"""Automated, fail-closed source refresh and assessment runner.

This runner fetches only the code-configured seed URLs, stores immutable versions,
records deterministic decisions, and never replaces an active version unless the
source-assessment hard gates return an activation decision.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlsplit

import httpx
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.source_assessment import AssessmentInput, AssessmentAction, assess_source
from app.source_content import USER_AGENT, _fetch_one
from app.source_registry import SOURCES
from app.source_store import SourceStoreError, get_source_pool

logger = logging.getLogger(__name__)

REFRESH_INTERVAL = timedelta(hours=24)
RETRY_INTERVAL = timedelta(hours=24)
MAX_FETCH_CONCURRENCY = 3

_DB_CLASS_BY_DECISION = {
    "A": "approved_authoritative",
    "B": "recognised_institutional",
    "C": "general_web",
    "D": "unverified_unsafe",
}

_DUE_SOURCES_SQL = """
select
    s.id as source_id,
    s.source_key,
    s.registered_url,
    s.institution,
    s.topic,
    s.source_class,
    s.status,
    s.active_version_id,
    v.content_sha256 as active_content_sha256
from private.source_registry as s
left join private.source_versions as v
  on v.id = s.active_version_id
where s.registered_url = any(%s)
  and s.status <> 'superseded'
  and (s.next_refresh_at is null or s.next_refresh_at <= now())
order by s.institution, s.topic, s.registered_url
"""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Fetched timestamp must include a timezone.")
    return parsed


def _scope_statement(institution: str, topic: str) -> str:
    """Describe the configured topic; this is scope metadata, not authority proof."""
    return (
        f"{institution} information about {topic} for Papua New Guinea "
        "public-service users."
    )


def _build_assessment(source: Any, page: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    fetched_at = _parse_timestamp(str(page["last_checked_at"]))
    scope = _scope_statement(source.institution, source.title)
    assessment_input = AssessmentInput(
        registered_url=source.url,
        final_url=str(page["final_url"]),
        registered_institution=source.institution,
        registered_topic=source.title,
        page_title=str(page.get("title") or source.title),
        content_type=str(page.get("content_type") or ""),
        text=str(page.get("text") or ""),
        fetched_at=fetched_at,
        fetch_succeeded=True,
        # Currentness and controlling-instrument evidence are intentionally
        # false until the automated official-instrument verification stage exists.
        currentness_verified=False,
        scope_statement=scope,
        controlling_instrument_verified=False,
        corroborating_official_sources=(),
        conflict_check_completed=False,
        unresolved_conflict=False,
        superseded=False,
    )
    audit_input = {
        "registered_url": source.url,
        "final_url": str(page["final_url"]),
        "registered_institution": source.institution,
        "registered_topic": source.title,
        "page_title": str(page.get("title") or source.title),
        "content_type": str(page.get("content_type") or ""),
        "content_sha256": str(page["content_hash"]),
        "fetched_at": fetched_at.isoformat(),
        "currentness_verified": False,
        "scope_statement": scope,
        "controlling_instrument_verified": False,
        "corroborating_official_sources": [],
        "conflict_check_completed": False,
        "unresolved_conflict": False,
        "superseded": False,
    }
    return assess_source(assessment_input), audit_input


async def _start_run(
    pool: Any, trigger_type: str, workflow_run_id: str | None, workflow_run_url: str | None
) -> Any:
    async with pool.connection(timeout=10) as connection:
        async with connection.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(
                """
                insert into private.source_refresh_runs
                    (trigger_type, workflow_run_id, workflow_run_url, status)
                values (%s, %s, %s, 'running')
                returning id
                """,
                (trigger_type, workflow_run_id, workflow_run_url),
            )
            row = await cursor.fetchone()
            return row["id"]


async def _load_due_sources(pool: Any) -> list[dict[str, Any]]:
    urls = [source.url for source in SOURCES]
    async with pool.connection(timeout=10) as connection:
        async with connection.cursor(row_factory=dict_row) as cursor:
            await cursor.execute(_DUE_SOURCES_SQL, (urls,))
            return await cursor.fetchall()


async def _upsert_exception(
    cursor: Any,
    *,
    source_id: Any,
    version_id: Any | None,
    run_id: Any,
    category: str,
    details: dict[str, Any],
    now: datetime,
) -> None:
    await cursor.execute(
        """
        select id, attempt_count
        from private.source_exceptions
        where source_id = %s
          and category = %s
          and status in ('open', 'retrying')
        order by first_seen_at desc
        limit 1
        for update
        """,
        (source_id, category),
    )
    existing = await cursor.fetchone()
    if existing:
        await cursor.execute(
            """
            update private.source_exceptions
            set version_id = %s,
                refresh_run_id = %s,
                status = 'retrying',
                attempt_count = attempt_count + 1,
                next_retry_at = %s,
                details = %s,
                last_seen_at = %s
            where id = %s
            """,
            (version_id, run_id, now + RETRY_INTERVAL, Jsonb(details), now, existing["id"]),
        )
    else:
        await cursor.execute(
            """
            insert into private.source_exceptions
                (source_id, version_id, refresh_run_id, category, severity,
                 status, attempt_count, next_retry_at, details, first_seen_at, last_seen_at)
            values (%s, %s, %s, %s, 'warning', 'retrying', 1, %s, %s, %s, %s)
            """,
            (
                source_id, version_id, run_id, category, now + RETRY_INTERVAL,
                Jsonb(details), now, now,
            ),
        )


async def _resolve_exceptions(cursor: Any, source_id: Any, now: datetime) -> None:
    await cursor.execute(
        """
        update private.source_exceptions
        set status = 'resolved', resolved_at = %s, last_seen_at = %s
        where source_id = %s and status in ('open', 'retrying')
        """,
        (now, now, source_id),
    )


async def _record_fetch_failure(
    pool: Any,
    *,
    source_row: dict[str, Any],
    run_id: Any,
    status: dict[str, Any],
) -> None:
    now = _utc_now()
    source_id = source_row["source_id"]
    error = str(status.get("error") or "source fetch failed")[:240]
    async with pool.connection(timeout=10) as connection:
        async with connection.transaction():
            async with connection.cursor(row_factory=dict_row) as cursor:
                await cursor.execute(
                    """
                    update private.source_registry
                    set last_attempt_at = %s, next_refresh_at = %s, updated_at = %s
                    where id = %s
                    """,
                    (now, now + RETRY_INTERVAL, now, source_id),
                )
                await cursor.execute(
                    """
                    insert into private.source_refresh_results
                        (refresh_run_id, source_id, outcome, http_status,
                         final_url, error_code, error_message)
                    values (%s, %s, 'fetch_failed', %s, %s, 'fetch_failed', %s)
                    """,
                    (
                        run_id, source_id, status.get("http_status"),
                        status.get("final_url"), error,
                    ),
                )
                await _upsert_exception(
                    cursor,
                    source_id=source_id,
                    version_id=None,
                    run_id=run_id,
                    category="fetch_failed",
                    details={"error": error, "http_status": status.get("http_status")},
                    now=now,
                )


async def _persist_assessment(
    pool: Any,
    *,
    source_row: dict[str, Any],
    source: Any,
    page: dict[str, Any],
    run_id: Any,
    decision: Any,
    audit_input: dict[str, Any],
) -> str:
    now = _utc_now()
    source_id = source_row["source_id"]
    content_hash = str(page["content_hash"])
    action = decision.action.value
    decision_class = _DB_CLASS_BY_DECISION[decision.source_class.value]
    fetched_at = _parse_timestamp(str(page["last_checked_at"]))

    async with pool.connection(timeout=10) as connection:
        async with connection.transaction():
            async with connection.cursor(row_factory=dict_row) as cursor:
                await cursor.execute(
                    """
                    select id, status, source_class, active_version_id
                    from private.source_registry
                    where id = %s
                    for update
                    """,
                    (source_id,),
                )
                current = await cursor.fetchone()
                if current is None:
                    raise SourceStoreError("A registered source disappeared during assessment.")

                active_version_id = current["active_version_id"]
                if source_row.get("active_content_sha256") == content_hash and active_version_id:
                    version_id = active_version_id
                    outcome = "unchanged"
                else:
                    await cursor.execute(
                        """
                        select id, version_state
                        from private.source_versions
                        where source_id = %s and content_sha256 = %s
                        """,
                        (source_id, content_hash),
                    )
                    existing_version = await cursor.fetchone()
                    if existing_version:
                        version_id = existing_version["id"]
                    else:
                        await cursor.execute(
                            """
                            select coalesce(max(version_number), 0) + 1 as next_version
                            from private.source_versions
                            where source_id = %s
                            """,
                            (source_id,),
                        )
                        next_version = (await cursor.fetchone())["next_version"]
                        await cursor.execute(
                            """
                            insert into private.source_versions
                                (source_id, version_number, content_sha256, page_title,
                                 final_url, content_type, publication_date, fetched_at,
                                 text_char_count, extracted_text, version_state, metadata)
                            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                    'candidate', %s)
                            returning id
                            """,
                            (
                                source_id,
                                next_version,
                                content_hash,
                                str(page.get("title") or source.title),
                                str(page["final_url"]),
                                str(page.get("content_type") or "application/octet-stream"),
                                None,
                                fetched_at,
                                len(str(page.get("text") or "")),
                                str(page.get("text") or ""),
                                Jsonb({
                                    "source_key": source_row["source_key"],
                                    "registered_url": source.url,
                                    "fetcher": "source_content._fetch_one",
                                }),
                            ),
                        )
                        version_id = (await cursor.fetchone())["id"]

                    if action == AssessmentAction.ACTIVATE.value:
                        if active_version_id and active_version_id != version_id:
                            await cursor.execute(
                                """
                                update private.source_versions
                                set version_state = 'superseded'
                                where id = %s and version_state = 'accepted'
                                """,
                                (active_version_id,),
                            )
                        await cursor.execute(
                            "update private.source_versions set version_state = 'accepted' where id = %s",
                            (version_id,),
                        )
                        await cursor.execute(
                            """
                            update private.source_registry
                            set status = 'active',
                                source_class = %s,
                                active_version_id = %s,
                                status_reason = 'Automated source assessment passed all required policy gates.',
                                last_attempt_at = %s,
                                last_success_at = %s,
                                next_refresh_at = %s,
                                updated_at = %s
                            where id = %s
                            """,
                            (
                                decision_class, version_id, now, fetched_at,
                                now + REFRESH_INTERVAL, now, source_id,
                            ),
                        )
                        outcome = "activated"
                        await _resolve_exceptions(cursor, source_id, now)
                    elif action == AssessmentAction.HOLD.value:
                        await cursor.execute(
                            """
                            update private.source_versions
                            set version_state = 'held'
                            where id = %s and version_state in ('candidate', 'held')
                            """,
                            (version_id,),
                        )
                        await cursor.execute(
                            """
                            update private.source_registry
                            set status_reason = %s,
                                last_attempt_at = %s,
                                last_success_at = %s,
                                next_refresh_at = %s,
                                updated_at = %s
                            where id = %s
                            """,
                            (
                                "; ".join(decision.reasons)[:500], now, fetched_at,
                                now + RETRY_INTERVAL, now, source_id,
                            ),
                        )
                        outcome = "held"
                        if source_row.get("active_content_sha256") != content_hash:
                            await _upsert_exception(
                                cursor,
                                source_id=source_id,
                                version_id=version_id,
                                run_id=run_id,
                                category="assessment_hold",
                                details={
                                    "reasons": list(decision.reasons),
                                    "hard_gates": decision.hard_gates,
                                    "policy_version": decision.policy_version,
                                },
                                now=now,
                            )
                    else:
                        await cursor.execute(
                            """
                            update private.source_versions
                            set version_state = 'rejected'
                            where id = %s and version_state in ('candidate', 'held')
                            """,
                            (version_id,),
                        )
                        await cursor.execute(
                            """
                            update private.source_registry
                            set status = case when active_version_id is null then 'excluded' else status end,
                                source_class = case when active_version_id is null then 'unverified_unsafe' else source_class end,
                                status_reason = %s,
                                last_attempt_at = %s,
                                last_success_at = %s,
                                next_refresh_at = %s,
                                updated_at = %s
                            where id = %s
                            """,
                            (
                                "; ".join(decision.reasons)[:500], now, fetched_at,
                                now + RETRY_INTERVAL, now, source_id,
                            ),
                        )
                        outcome = "excluded"
                        await _upsert_exception(
                            cursor,
                            source_id=source_id,
                            version_id=version_id,
                            run_id=run_id,
                            category="assessment_excluded",
                            details={
                                "reasons": list(decision.reasons),
                                "hard_gates": decision.hard_gates,
                                "policy_version": decision.policy_version,
                            },
                            now=now,
                        )

                await cursor.execute(
                    """
                    insert into private.source_assessment_decisions
                        (source_id, version_id, refresh_run_id, policy_version,
                         action, source_class, confidence, hard_gates, reasons,
                         assessment_input)
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        source_id, version_id, run_id, decision.policy_version,
                        action, decision_class, decision.confidence,
                        Jsonb(decision.hard_gates), Jsonb(list(decision.reasons)),
                        Jsonb(audit_input),
                    ),
                )
                if outcome == "unchanged":
                    await cursor.execute(
                        """
                        update private.source_registry
                        set last_attempt_at = %s, last_success_at = %s,
                            next_refresh_at = %s, updated_at = %s
                        where id = %s
                        """,
                        (now, fetched_at, now + REFRESH_INTERVAL, now, source_id),
                    )
                    await _resolve_exceptions(cursor, source_id, now)

                await cursor.execute(
                    """
                    insert into private.source_refresh_results
                        (refresh_run_id, source_id, version_id, outcome, http_status, final_url)
                    values (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        run_id, source_id, version_id, outcome,
                        200, str(page["final_url"]),
                    ),
                )
                return outcome


async def _finish_run(
    pool: Any,
    run_id: Any,
    *,
    counts: dict[str, int],
    failed: bool = False,
) -> None:
    finished = _utc_now()
    status = "failed" if failed else (
        "partial" if counts["failure_count"] or counts["held_count"] or counts["excluded_count"]
        else "completed"
    )
    async with pool.connection(timeout=10) as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                """
                update private.source_refresh_runs
                set status = %s, finished_at = %s,
                    source_count = %s, fetched_count = %s,
                    activated_count = %s, held_count = %s,
                    excluded_count = %s, failure_count = %s,
                    summary = %s
                where id = %s
                """,
                (
                    status, finished, counts["source_count"], counts["fetched_count"],
                    counts["activated_count"], counts["held_count"],
                    counts["excluded_count"], counts["failure_count"],
                    Jsonb(counts), run_id,
                ),
            )


async def run_source_refresh(
    *,
    trigger_type: str = "scheduled",
    workflow_run_id: str | None = None,
    workflow_run_url: str | None = None,
) -> dict[str, Any]:
    """Fetch due configured sources and persist versions, decisions and outcomes."""
    if trigger_type not in {"scheduled", "manual", "startup", "retry"}:
        raise ValueError("Unsupported source refresh trigger type.")

    pool = await get_source_pool()
    run_id = await _start_run(pool, trigger_type, workflow_run_id, workflow_run_url)
    counts = {
        "source_count": 0,
        "fetched_count": 0,
        "activated_count": 0,
        "held_count": 0,
        "excluded_count": 0,
        "failure_count": 0,
        "unchanged_count": 0,
    }

    try:
        due_rows = await _load_due_sources(pool)
        counts["source_count"] = len(due_rows)
        sources_by_url = {source.url: source for source in SOURCES}
        due: list[tuple[dict[str, Any], Any]] = []
        for row in due_rows:
            source = sources_by_url.get(row["registered_url"])
            if source is None:
                continue
            if row["institution"] != source.institution or row["topic"] != source.title:
                logger.error("Registry identity mismatch for %s; skipping.", row["registered_url"])
                counts["failure_count"] += 1
                continue
            due.append((row, source))

        timeout = httpx.Timeout(12.0, connect=5.0)
        limits = httpx.Limits(
            max_connections=MAX_FETCH_CONCURRENCY,
            max_keepalive_connections=MAX_FETCH_CONCURRENCY,
        )
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.5",
        }
        semaphore = asyncio.Semaphore(MAX_FETCH_CONCURRENCY)
        async with httpx.AsyncClient(
            timeout=timeout, limits=limits, headers=headers,
            follow_redirects=True, max_redirects=5,
        ) as client:
            async def fetch_one(source: Any):
                async with semaphore:
                    return await _fetch_one(client, source)

            fetched = await asyncio.gather(
                *(fetch_one(source) for _, source in due)
            )

        for (source_row, source), (page, fetch_status) in zip(due, fetched):
            if page is None:
                counts["failure_count"] += 1
                await _record_fetch_failure(
                    pool, source_row=source_row, run_id=run_id, status=fetch_status
                )
                continue

            counts["fetched_count"] += 1
            decision, audit_input = _build_assessment(source, page)
            outcome = await _persist_assessment(
                pool,
                source_row=source_row,
                source=source,
                page=page,
                run_id=run_id,
                decision=decision,
                audit_input=audit_input,
            )
            if outcome == "activated":
                counts["activated_count"] += 1
            elif outcome == "held":
                counts["held_count"] += 1
            elif outcome == "excluded":
                counts["excluded_count"] += 1
            else:
                counts["unchanged_count"] += 1

        await _finish_run(pool, run_id, counts=counts)
        return {"run_id": str(run_id), "status": "partial" if (
            counts["failure_count"] or counts["held_count"] or counts["excluded_count"]
        ) else "completed", **counts}
    except Exception:
        logger.exception("Source refresh run failed.")
        try:
            await _finish_run(pool, run_id, counts=counts, failed=True)
        except Exception:
            logger.exception("Could not persist failed refresh-run status.")
        raise


async def _main() -> None:
    event = os.getenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    trigger_type = "scheduled" if event == "schedule" else "manual"
    run_id = os.getenv("GITHUB_RUN_ID")
    repository = os.getenv("GITHUB_REPOSITORY")
    server = os.getenv("GITHUB_SERVER_URL", "https://github.com")
    run_url = f"{server}/{repository}/actions/runs/{run_id}" if run_id and repository else None
    summary = await run_source_refresh(
        trigger_type=trigger_type,
        workflow_run_id=run_id,
        workflow_run_url=run_url,
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_main())
