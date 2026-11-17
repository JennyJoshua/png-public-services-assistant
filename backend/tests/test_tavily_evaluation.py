import json
from pathlib import Path

import httpx
import pytest

from app.tavily_evaluation import (
    evaluate_queries,
    load_query_fixture,
    request_payload,
)

QUERY = {
    "id": "Q01",
    "country": "papua new guinea",
    "query": "Papua New Guinea National ID registration official requirements",
    "reference_urls": ["https://pngcir.gov.pg/nid-registration-information/"],
}


def test_request_payload_uses_bounded_search_and_disables_answer_and_raw_content():
    payload = request_payload(QUERY)

    assert payload["search_depth"] == "basic"
    assert payload["max_results"] == 5
    assert payload["country"] == "papua new guinea"
    assert payload["topic"] == "general"
    assert payload["include_answer"] is False
    assert payload["include_raw_content"] is False
    assert payload["include_usage"] is True


def test_evaluation_normalises_results_and_never_emits_api_key():
    secret = "tvly-test-secret"

    def handler(request):
        assert request.headers["Authorization"] == f"Bearer {secret}"
        body = json.loads(request.content)
        assert body["query"] == QUERY["query"]
        return httpx.Response(200, json={
            "results": [{
                "title": "NID Registration",
                "url": "https://pngcir.gov.pg/nid-registration-information/",
                "content": "Official registration information.",
                "score": 0.92,
                "published_date": "2026-01-01",
                "id": "provider-id",
                "raw_content": "must not be retained",
            }],
            "answer": "must not be retained",
            "usage": {"credits": 1},
            "response_time": "0.42",
            "request_id": "request-123",
        })

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        report = evaluate_queries(secret, [QUERY], client=client)

    serialised = json.dumps(report)
    assert secret not in serialised
    assert "must not be retained" not in serialised
    assert report["successful_queries"] == 1
    assert report["total_credits_used"] == 1
    assert report["results"][0]["results"][0]["domain"] == "pngcir.gov.pg"
    assert report["results"][0]["results"][0]["excluded"] is False


def test_evaluation_excludes_non_https_result_urls():
    def handler(request):
        return httpx.Response(200, json={
            "results": [
                {"title": "Unsafe", "url": "http://example.com/page", "content": "x"},
                {"title": "Credentials", "url": "https://user:pass@example.com/page", "content": "y"},
            ],
            "usage": {"credits": 1},
        })

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        report = evaluate_queries("secret", [QUERY], client=client)

    results = report["results"][0]["results"]
    assert len(results) == 2
    assert all(item["excluded"] for item in results)
    assert all("url" not in item for item in results)


def test_http_error_is_recorded_without_provider_body_or_secret():
    secret = "tvly-test-secret"

    def handler(request):
        return httpx.Response(401, text=f"Unauthorized {secret}")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        report = evaluate_queries(secret, [QUERY], client=client)

    serialised = json.dumps(report)
    assert report["results"][0]["error"] == "http_401"
    assert secret not in serialised
    assert "Unauthorized" not in serialised


def test_missing_key_and_empty_query_list_fail_closed():
    with pytest.raises(ValueError, match="TAVILY_API_KEY"):
        evaluate_queries("", [QUERY])
    with pytest.raises(ValueError, match="At least one"):
        evaluate_queries("secret", [])


def test_query_fixture_has_ten_synthetic_queries():
    fixture_path = Path(__file__).resolve().parents[1] / "evaluation" / "tavily_png_pacific_queries.json"
    fixture = load_query_fixture(str(fixture_path))
    assert len(fixture) == 10
    assert {item["id"] for item in fixture} == {f"Q{i:02d}" for i in range(1, 11)}
    assert all("Papua New Guinea" in item["query"] or item["country"] != "papua new guinea" for item in fixture)
