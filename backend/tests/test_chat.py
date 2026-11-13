from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_chat_returns_retrieved_evidence_and_citations(monkeypatch) -> None:
    async def fake_retrieve_answer(question: str) -> dict:
        assert question == "How do I register a business?"
        return {
            "answer": "The agency administers business registration. [1]",
            "citations": [{
                "title": "Business Registration",
                "institution": "Example Agency",
                "url": "https://example.gov.pg/business",
                "publication_date": None,
                "last_checked_at": "2026-11-13T00:00:00+00:00",
            }],
            "evidence": [{"text": "The agency administers business registration.", "citation_index": 1}],
            "warnings": [],
        }

    monkeypatch.setattr("app.main.retrieve_answer", fake_retrieve_answer)
    response = client.post("/api/v1/chat", json={"question": "  How do I register a business?  "})

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"].endswith("[1]")
    assert payload["citations"][0]["url"] == "https://example.gov.pg/business"
    assert payload["evidence"][0]["citation_index"] == 1
    assert payload["request_id"]


def test_chat_rejects_empty_or_oversized_questions() -> None:
    assert client.post("/api/v1/chat", json={"question": ""}).status_code == 422
    assert client.post("/api/v1/chat", json={"question": "x" * 1001}).status_code == 422
