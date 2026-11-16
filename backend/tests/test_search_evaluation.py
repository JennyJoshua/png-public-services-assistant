import pytest

from app.search_evaluation import score_provider, score_query


def result(rank, relevance, *, source_class=None, fetch_status="not_checked"):
    return {
        "rank": rank,
        "title": f"Search result {rank}",
        "url": f"https://example.gov.pg/result/{rank}",
        "relevance": relevance,
        "source_class": source_class,
        "fetch_status": fetch_status,
    }


def dataset(results):
    return {
        "schema_version": "1.0",
        "provider": "test-provider",
        "evaluated_at": "2026-11-16T17:00:00+10:00",
        "queries": [{
            "query_id": "Q01",
            "query": "Gulf Province public services official",
            "latency_ms": 120.5,
            "usage_units": 1,
            "results": results,
        }],
    }


def test_query_scoring_uses_rank_order_and_human_relevance_grades():
    scored = score_query({
        "query_id": "Q01",
        "query": "PNG public services",
        "latency_ms": 100,
        "usage_units": 1,
        "results": [
            result(2, 2, source_class="A", fetch_status="success"),
            result(1, 0, source_class="C", fetch_status="blocked"),
            result(3, 1, source_class="B", fetch_status="success"),
        ],
    })
    assert scored["precision_at_5"] == pytest.approx(0.4)
    assert scored["precision_at_10"] == pytest.approx(0.2)
    assert scored["class_a_count_at_10"] == 1
    assert scored["fetch_success_count_at_10"] == 2
    assert scored["ndcg_at_5"] < 1


def test_provider_summary_aggregates_queries_and_cost_units():
    data = dataset([
        result(1, 2, source_class="A", fetch_status="success"),
        result(2, 0, source_class="C", fetch_status="error"),
    ])
    data["queries"].append({
        "query_id": "Q02",
        "query": "PNG passport application official",
        "latency_ms": 220,
        "usage_units": 2,
        "results": [result(1, 1, source_class="A", fetch_status="success")],
    })
    report = score_provider(data)
    assert report["provider"] == "test-provider"
    assert report["query_count"] == 2
    assert report["total_results"] == 3
    assert report["mean_latency_ms"] == pytest.approx(170)
    assert report["total_usage_units"] == 3
    assert len(report["per_query"]) == 2


def test_empty_results_score_zero_without_crashing():
    scored = score_query({
        "query_id": "Q-empty",
        "query": "Gulf Province service directory",
        "results": [],
    })
    assert scored["precision_at_5"] == 0
    assert scored["ndcg_at_10"] == 0


@pytest.mark.parametrize("bad_url", [
    "http://example.gov.pg/page",
    "/relative/path",
    "https://user:pass@example.gov.pg/page",
])
def test_rejects_non_https_or_credential_result_urls(bad_url):
    with pytest.raises(ValueError, match="HTTPS URL"):
        score_query({
            "query_id": "Q01",
            "query": "PNG public services",
            "results": [{
                "rank": 1, "title": "Result", "url": bad_url,
                "relevance": 2,
            }],
        })


def test_rejects_unjudged_or_invalid_relevance():
    with pytest.raises(ValueError, match="relevance grade"):
        score_query({
            "query_id": "Q01",
            "query": "PNG public services",
            "results": [{
                "rank": 1, "title": "Result",
                "url": "https://example.gov.pg/page",
            }],
        })


def test_rejects_duplicate_ranks():
    with pytest.raises(ValueError, match="ranks must be unique"):
        score_query({
            "query_id": "Q01",
            "query": "PNG public services",
            "results": [result(1, 1), result(1, 2)],
        })



@pytest.mark.parametrize("field,value", [
    ("source_class", []),
    ("fetch_status", {}),
])
def test_rejects_malformed_source_class_and_fetch_status(field, value):
    item = result(1, 1)
    item[field] = value
    with pytest.raises(ValueError):
        score_query({
            "query_id": "Q01",
            "query": "PNG public services",
            "results": [item],
        })


def test_rejects_duplicate_query_ids_and_non_finite_measurements():
    data = dataset([result(1, 1)])
    data["queries"].append(dict(data["queries"][0]))
    with pytest.raises(ValueError, match="unique query_id"):
        score_provider(data)

    data = dataset([result(1, 1)])
    data["queries"][0]["latency_ms"] = float("nan")
    with pytest.raises(ValueError, match="latency_ms"):
        score_provider(data)
