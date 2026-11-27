"""Read the durable, active source versions from the private Supabase Postgres schema.

The service never falls back to the in-memory fetch cache when database mode is
selected: a database outage therefore produces no evidence rather than stale or
unreviewed content.
"""
from __future__ import annotations

import asyncio
import os
from datetime import date, datetime
from typing import Any

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

_POOL: AsyncConnectionPool | None = None
_POOL_LOCK = asyncio.Lock()

_ACTIVE_PAGES_SQL = """
select
    s.id as source_id,
    s.registered_url,
    s.institution,
    s.topic,
    s.source_class,
    s.status,
    v.id as version_id,
    v.page_title,
    v.final_url,
    v.content_type,
    v.publication_date,
    v.fetched_at,
    v.content_sha256,
    v.extracted_text
from private.source_registry as s
join private.source_versions as v
  on v.id = s.active_version_id
where s.status = 'active'
  and s.source_class in (
      'approved_authoritative',
      'recognised_institutional',
      'general_web'
  )
  and v.version_state = 'accepted'
order by s.institution, s.topic, s.registered_url
"""


class SourceStoreError(RuntimeError):
    """Raised when durable source storage is unavailable or misconfigured."""


def database_source_store_enabled() -> bool:
    """Use database mode when explicitly selected or when its URL is configured."""
    configured_url = os.getenv("SUPABASE_DATABASE_URL", "").strip()
    mode = os.getenv("SOURCE_STORE_MODE", "").strip().lower()
    if not mode:
        mode = "database" if configured_url else "memory"
    if mode not in {"database", "memory"}:
        raise SourceStoreError("SOURCE_STORE_MODE must be either 'database' or 'memory'.")
    return mode == "database"


def _database_url() -> str:
    value = os.getenv("SUPABASE_DATABASE_URL", "").strip()
    if not value:
        raise SourceStoreError(
            "Database source mode is enabled but SUPABASE_DATABASE_URL is not configured."
        )
    if not value.startswith(("postgres://", "postgresql://")):
        raise SourceStoreError("SUPABASE_DATABASE_URL must be a PostgreSQL connection URI.")
    return value


async def _get_pool() -> AsyncConnectionPool:
    global _POOL
    if _POOL is not None:
        return _POOL
    async with _POOL_LOCK:
        if _POOL is None:
            pool = AsyncConnectionPool(
                conninfo=_database_url(),
                min_size=1,
                max_size=3,
                timeout=10,
                open=False,
                kwargs={"sslmode": "require", "connect_timeout": 10},
                name="png-public-services-source-store",
            )
            try:
                await pool.open(wait=True)
            except Exception:
                await pool.close()
                raise
            _POOL = pool
    return _POOL


def _as_iso(value: date | datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def row_to_page(row: dict[str, Any]) -> dict[str, Any]:
    """Convert a database row to the existing retrieval page contract."""
    return {
        "institution": row["institution"],
        "agency": row["institution"],
        "title": row["page_title"],
        "topic": row["topic"],
        "url": row["registered_url"],
        "final_url": row["final_url"],
        "content_type": row["content_type"],
        "publication_date": _as_iso(row.get("publication_date")),
        "last_checked_at": _as_iso(row["fetched_at"]),
        "text": row["extracted_text"],
        "content_hash": row["content_sha256"],
        "_registry_source_id": str(row["source_id"]),
        "_registry_version_id": str(row["version_id"]),
        "_registry_source_class": row["source_class"],
        "_registry_status": row["status"],
    }


async def fetch_active_source_pages() -> list[dict[str, Any]]:
    """Return only accepted versions currently pointed to by active registry rows."""
    try:
        pool = await _get_pool()
        async with pool.connection(timeout=10) as connection:
            async with connection.cursor(row_factory=dict_row) as cursor:
                await cursor.execute(_ACTIVE_PAGES_SQL)
                rows = await cursor.fetchall()
        return [row_to_page(row) for row in rows]
    except SourceStoreError:
        raise
    except Exception as exc:
        raise SourceStoreError("Unable to read active source versions from Supabase.") from exc


async def close_source_store() -> None:
    """Close the process-local pool cleanly during application shutdown."""
    global _POOL
    async with _POOL_LOCK:
        pool, _POOL = _POOL, None
        if pool is not None:
            await pool.close()
