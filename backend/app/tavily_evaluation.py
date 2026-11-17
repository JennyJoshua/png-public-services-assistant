"""Non-production Tavily search evaluation; never used by the live chat path.

Only synthetic public-service queries from the checked-in fixture are sent.
The API key is read from the environment and is never written to output.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Sequence
from urllib.parse import urlsplit

import httpx

TAVILY_SEARCH_URL = "https://api.tavily.com/search"
SEARCH_DEPTH = "basic"
MAX_RESULTS = 5
REQUEST_TIMEOUT_SECONDS = 20.0


def request_payload(query: dict[str, Any]) -> dict[str, Any]:
    """Build a bounded search-only request; disable generated answers/raw pages."""
    payload = {
        "query": str(query["query"]),
        "search_depth": SEARCH_DEPTH,
        "max_results": MAX_RESULTS,
        "topic": "general",
        "language": "en",
        "include_published_date": True,
        "include_answer": False,
        "include_raw_content": False,
        "include_favicon": False,
        "include_usage": True,
        "safe_search": True,
    }
    if query.get("country"):
        payload["country"] = str(query["country"])
    return payload


def _safe_result(item: Any, rank: int) -> dict[str, Any]:
    if not isinstance(item, dict):
        return {"rank": rank, "excluded": True, "exclusion_reason": "malformed_result"}
    raw_url = item.get("url")
    parsed = urlsplit(str(raw_url or ""))
    if (
        parsed.scheme.lower() != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        return {"rank": rank, "excluded": True, "exclusion_reason": "non_https_or_invalid_url"}

    return {
        "rank": rank,
        "title": str(item.get("title") or "")[:300],
        "url": str(raw_url),
        "domain": (parsed.hostname or "").lower(),
        "snippet": str(item.get("content") or "")[:800],
        "published_date": item.get("published_date"),
        "provider_score": item.get("score") if isinstance(item.get("score"), (int, float)) else None,
        "provider_result_id": str(item.get("id"))[:100] if item.get("id") is not None else None,
        "excluded": False,
    }


def evaluate_queries(
    api_key: str,
    queries: Sequence[dict[str, Any]],
    *,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Run the fixed synthetic suite sequentially, with no automatic retries."""
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("TAVILY_API_KEY is required.")
    if not queries:
        raise ValueError("At least one synthetic query is required.")

    owns_client = client is None
    session = client or httpx.Client(
        timeout=httpx.Timeout(REQUEST_TIMEOUT_SECONDS, connect=5.0),
        follow_redirects=False,
    )
    started_at = datetime.now(timezone.utc).isoformat()
    records: list[dict[str, Any]] = []

    try:
        for query in queries:
            record: dict[str, Any] = {
                "query_id": str(query["id"]),
                "query": str(query["query"]),
                "country_boost": str(query["country"]) if query.get("country") else None,
                "reference_urls": list(query.get("reference_urls", [])),
                "request_parameters": {
                    "search_depth": SEARCH_DEPTH,
                    "max_results": MAX_RESULTS,
                    "topic": "general",
                    "language": "en",
                    "include_answer": False,
                    "include_raw_content": False,
                    "include_published_date": True,
                    "include_usage": True,
                    "safe_search": True,
                },
            }
            before = time.monotonic()
            try:
                response = session.post(
                    TAVILY_SEARCH_URL,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=request_payload(query),
                )
            except httpx.TimeoutException:
                record.update({"error": "timeout", "http_status": None})
            except httpx.HTTPError:
                record.update({"error": "transport_error", "http_status": None})
            else:
                record["http_status"] = response.status_code
                if response.status_code != 200:
                    # Do not persist provider error bodies or request headers.
                    record["error"] = f"http_{response.status_code}"
                else:
                    try:
                        payload = response.json()
                    except (ValueError, json.JSONDecodeError):
                        payload = None
                    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
                        record["error"] = "malformed_response"
                    else:
                        results = payload["results"][:MAX_RESULTS]
                        record["results"] = [
                            _safe_result(item, rank)
                            for rank, item in enumerate(results, start=1)
                        ]
                        usage = payload.get("usage")
                        credits = usage.get("credits") if isinstance(usage, dict) else None
                        record["credits_used"] = credits if isinstance(credits, int) else None
                        try:
                            record["provider_response_time_seconds"] = float(payload.get("response_time"))
                        except (TypeError, ValueError):
                            record["provider_response_time_seconds"] = None
                        record["request_id"] = str(payload.get("request_id") or "")[:120] or None
            record["elapsed_seconds"] = round(time.monotonic() - before, 3)
            records.append(record)
    finally:
        if owns_client:
            session.close()

    total_credits = sum(
        item.get("credits_used", 0) or 0 for item in records
        if isinstance(item.get("credits_used", 0), int)
    )
    return {
        "provider": "tavily",
        "endpoint": TAVILY_SEARCH_URL,
        "started_at": started_at,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "query_count": len(records),
        "successful_queries": sum(1 for item in records if "error" not in item),
        "failed_queries": sum(1 for item in records if "error" in item),
        "total_credits_used": total_credits,
        "results": records,
        "limitations": [
            "Synthetic queries only; no real user prompts, history or private documents are sent.",
            "Search results are unscored until a human reviewer checks them against the reference set.",
            "Provider country selection is a ranking boost, not a guarantee or strict jurisdiction filter.",
            "No page fetching, source promotion, shared caching or live application integration occurs.",
        ],
    }


def load_query_fixture(path: str) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, list) or not value:
        raise ValueError("Search evaluation fixture must be a non-empty JSON list.")
    required = {"id", "query", "reference_urls"}
    for item in value:
        if not isinstance(item, dict) or not required.issubset(item):
            raise ValueError("Each query fixture must include id, country, query and reference_urls.")
        if not str(item["query"]).strip() or (item.get("country") is not None and not str(item["country"]).strip()):
            raise ValueError("Query must not be empty and country must be non-empty when supplied.")
        if not isinstance(item["reference_urls"], list):
            raise ValueError("reference_urls must be a list.")
    return value
