"""Run the isolated synthetic Tavily search benchmark."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx

from app.tavily_evaluation import evaluate_queries, load_query_fixture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--queries",
        default="backend/evaluation/tavily_png_pacific_queries.json",
    )
    parser.add_argument(
        "--output",
        default="artifacts/tavily-search-evaluation.json",
    )
    args = parser.parse_args()

    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        print("TAVILY_API_KEY is not configured as a repository Actions secret.", file=sys.stderr)
        return 2

    try:
        queries = load_query_fixture(args.queries)
        report = evaluate_queries(api_key, queries)
    except (OSError, ValueError, httpx.HTTPError) as exc:
        # Never print exception details that might contain request configuration.
        print(f"Evaluation could not start: {type(exc).__name__}", file=sys.stderr)
        return 2

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        "Tavily synthetic evaluation completed: "
        f"{report['successful_queries']}/{report['query_count']} queries succeeded; "
        f"{report['total_credits_used']} credits reported."
    )
    for item in report["results"]:
        print(
            f"{item['query_id']}: "
            f"{len(item.get('results', []))} results; "
            f"{item.get('error', 'ok')}"
        )
    return 1 if report["failed_queries"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
