"""Offline scoring for manually reviewed web-search provider results.

This module makes no network requests and does not assign relevance or source
authority. Those judgements must be supplied by a human reviewer.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean
from typing import Any
from urllib.parse import urlsplit

VALID_SOURCE_CLASSES = {"A", "B", "C", "D"}
VALID_FETCH_STATUSES = {"success", "blocked", "error", "not_checked"}
SUPPORTED_SCHEMA_VERSION = "1.0"


def _validate_result(result: dict[str, Any], query_id: str) -> None:
    if not isinstance(result, dict):
        raise ValueError(f"{query_id}: each result must be an object.")
    url = result.get("url")
    parsed = urlsplit(url) if isinstance(url, str) else None
    if not parsed or parsed.scheme.lower() != "https" or not parsed.hostname:
        raise ValueError(f"{query_id}: result URL must be an absolute HTTPS URL.")
    if parsed.username or parsed.password:
        raise ValueError(f"{query_id}: result URL must not contain credentials.")
    if not isinstance(result.get("title"), str) or not result["title"].strip():
        raise ValueError(f"{query_id}: result title is required.")
    rank = result.get("rank")
    if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
        raise ValueError(f"{query_id}: result rank must be a positive integer.")
    relevance = result.get("relevance")
    if not isinstance(relevance, int) or isinstance(relevance, bool) or relevance not in (0, 1, 2):
        raise ValueError(f"{query_id}: human relevance grade must be 0, 1 or 2.")
    source_class = result.get("source_class")
    if source_class is not None and (
        not isinstance(source_class, str) or source_class not in VALID_SOURCE_CLASSES
    ):
        raise ValueError(f"{query_id}: source_class must be A, B, C, D or null.")
    fetch_status = result.get("fetch_status", "not_checked")
    if not isinstance(fetch_status, str) or fetch_status not in VALID_FETCH_STATUSES:
        raise ValueError(f"{query_id}: unsupported fetch_status.")


def _dcg(grades: list[int]) -> float:
    return sum((2**grade - 1) / math.log2(index + 2) for index, grade in enumerate(grades))


def _precision(grades: list[int], cutoff: int) -> float:
    return sum(grade >= 1 for grade in grades[:cutoff]) / cutoff


def _ndcg(grades: list[int], cutoff: int) -> float:
    actual = _dcg(grades[:cutoff])
    ideal = _dcg(sorted(grades, reverse=True)[:cutoff])
    return actual / ideal if ideal else 0.0


def score_query(query: dict[str, Any]) -> dict[str, Any]:
    """Score one query using explicit human relevance and provenance labels."""
    if not isinstance(query, dict):
        raise ValueError("Each query must be an object.")
    query_id = query.get("query_id")
    if not isinstance(query_id, str) or not query_id.strip():
        raise ValueError("query_id is required.")
    if not isinstance(query.get("query"), str) or not query["query"].strip():
        raise ValueError(f"{query_id}: query text is required.")
    results = query.get("results")
    if not isinstance(results, list):
        raise ValueError(f"{query_id}: results must be a list.")

    seen_ranks: set[int] = set()
    for result in results:
        _validate_result(result, query_id)
        if result["rank"] in seen_ranks:
            raise ValueError(f"{query_id}: result ranks must be unique.")
        seen_ranks.add(result["rank"])

    ordered = sorted(results, key=lambda item: item["rank"])
    grades = [item["relevance"] for item in ordered]
    official_a = sum(item.get("source_class") == "A" for item in ordered[:10])
    fetch_success = sum(item.get("fetch_status", "not_checked") == "success" for item in ordered[:10])

    latency = query.get("latency_ms")
    if latency is not None and (
        not isinstance(latency, (int, float)) or isinstance(latency, bool)
        or not math.isfinite(latency) or latency < 0
    ):
        raise ValueError(f"{query_id}: latency_ms must be a non-negative number or null.")
    usage = query.get("usage_units")
    if usage is not None and (
        not isinstance(usage, (int, float)) or isinstance(usage, bool)
        or not math.isfinite(usage) or usage < 0
    ):
        raise ValueError(f"{query_id}: usage_units must be a non-negative number or null.")

    return {
        "query_id": query_id,
        "result_count": len(ordered),
        "precision_at_5": _precision(grades, 5),
        "precision_at_10": _precision(grades, 10),
        "ndcg_at_5": _ndcg(grades, 5),
        "ndcg_at_10": _ndcg(grades, 10),
        "class_a_count_at_10": official_a,
        "fetch_success_count_at_10": fetch_success,
        "latency_ms": latency,
        "usage_units": usage,
    }


def score_provider(dataset: dict[str, Any]) -> dict[str, Any]:
    """Validate and aggregate one provider's reviewed query-result dataset."""
    if not isinstance(dataset, dict) or dataset.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        raise ValueError(f"Dataset schema_version must be {SUPPORTED_SCHEMA_VERSION}.")
    provider = dataset.get("provider")
    if not isinstance(provider, str) or not provider.strip():
        raise ValueError("provider is required.")
    queries = dataset.get("queries")
    if not isinstance(queries, list) or not queries:
        raise ValueError("At least one query is required.")

    query_ids = [query.get("query_id") for query in queries if isinstance(query, dict)]
    if (
        len(query_ids) != len(queries)
        or any(not isinstance(query_id, str) or not query_id.strip() for query_id in query_ids)
        or len(set(query_ids)) != len(query_ids)
    ):
        raise ValueError("Query records must have unique query_id values.")
    scored = [score_query(query) for query in queries]
    metric_names = (
        "precision_at_5",
        "precision_at_10",
        "ndcg_at_5",
        "ndcg_at_10",
        "class_a_count_at_10",
        "fetch_success_count_at_10",
    )
    summary = {
        metric: mean(item[metric] for item in scored)
        for metric in metric_names
    }
    latencies = [item["latency_ms"] for item in scored if item["latency_ms"] is not None]
    usage = [item["usage_units"] for item in scored if item["usage_units"] is not None]
    summary.update({
        "provider": provider,
        "evaluated_at": dataset.get("evaluated_at"),
        "query_count": len(scored),
        "total_results": sum(item["result_count"] for item in scored),
        "mean_latency_ms": mean(latencies) if latencies else None,
        "total_usage_units": sum(usage) if usage else None,
        "per_query": scored,
    })
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Score human-reviewed search provider result JSON.")
    parser.add_argument("datasets", nargs="+", help="One or more provider result JSON files.")
    args = parser.parse_args()
    reports = []
    for filename in args.datasets:
        dataset = json.loads(Path(filename).read_text(encoding="utf-8"))
        reports.append(score_provider(dataset))
    print(json.dumps(reports, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
