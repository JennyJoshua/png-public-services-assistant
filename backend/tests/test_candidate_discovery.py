import asyncio

from app import candidate_discovery


def test_discovery_orchestration_attaches_policy_without_approval(monkeypatch):
    async def fake_fetch(candidates):
        assert len(candidates) == 2
        return [
            {
                "url": "https://ica.gov.pg/passport",
                "canonical_url": "https://ica.gov.pg/passport",
                "final_url": "https://ica.gov.pg/passport",
                "status": "candidate_unreviewed",
                "approved": False,
                "evidence_class": None,
                "text": "Public guidance text",
            },
            {
                "url": "https://new-agency.gov.pg/service",
                "canonical_url": "https://new-agency.gov.pg/service",
                "final_url": "https://new-agency.gov.pg/service",
                "status": "candidate_unreviewed",
                "approved": False,
                "evidence_class": None,
                "text": "Candidate text",
            },
        ]

    monkeypatch.setattr(candidate_discovery, "fetch_candidate_pages", fake_fetch)
    results = asyncio.run(candidate_discovery.discover_candidate_pages([
        {"url": "https://ica.gov.pg/passport"},
        {"url": "https://new-agency.gov.pg/service"},
    ]))

    assert results[0]["policy_action"] == "auto_process"
    assert results[1]["policy_action"] == "human_review"
    for result in results:
        assert result["approved"] is False
        assert result["evidence_class"] is None
        assert result["policy_source_class"] is None
        assert result["text"]


def test_discovery_orchestration_excludes_failed_fetches(monkeypatch):
    async def fake_fetch(candidates):
        return [{
            "url": "https://ica.gov.pg/unavailable",
            "status": "unavailable",
            "approved": False,
            "evidence_class": None,
            "error": "HTTP 503",
        }]

    monkeypatch.setattr(candidate_discovery, "fetch_candidate_pages", fake_fetch)
    results = asyncio.run(candidate_discovery.discover_candidate_pages([
        {"url": "https://ica.gov.pg/unavailable"}
    ]))

    assert results[0]["policy_action"] == "exclude"
    assert results[0]["approved"] is False
    assert results[0]["evidence_class"] is None