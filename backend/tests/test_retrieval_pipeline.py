from datetime import datetime, timezone

import pytest

from app.retrieval_contracts import SourceClass, SourceStatus
from app.retrieval_pipeline import build_evidence_records, page_to_fetched_document


NOW = "2026-11-16T07:00:00+00:00"


def page(**overrides):
    value = {
        "institution": "Papua New Guinea Civil and Identity Registry",
        "title": "NID registration information",
        "url": "https://pngcir.gov.pg/nid-registration-information/",
        "final_url": "https://pngcir.gov.pg/nid-registration-information/",
        "content_type": "text/html; charset=utf-8",
        "publication_date": None,
        "last_checked_at": NOW,
        "text": "Applicants must lodge the completed form at the registry office.",
    }
    value.update(overrides)
    return value


def test_page_adapter_marks_registered_source_and_retains_fetch_metadata():
    document = page_to_fetched_document(page())
    assert document.source.source_class is SourceClass.APPROVED_AUTHORITATIVE
    assert document.source.status is SourceStatus.ACTIVE
    assert document.source.jurisdiction == "Papua New Guinea"
    assert document.source.last_fetched_at == datetime(2026, 11, 16, 7, 0, tzinfo=timezone.utc)
    assert document.final_url.endswith("/nid-registration-information/")
    assert document.content_type.startswith("text/html")


def test_page_adapter_rejects_timestamp_without_timezone():
    with pytest.raises(ValueError, match="timezone"):
        page_to_fetched_document(page(last_checked_at="2026-11-16T07:00:00"))


def test_ranked_passages_receive_stable_provenance_records():
    document = page_to_fetched_document(page())
    ranked = [{
        "source": page(),
        "text": "Applicants must lodge the completed form at the registry office.",
        "passage_index": 0,
        "score": 2.1,
    }]
    records = build_evidence_records([document], ranked)
    assert len(records) == 1
    record = records[0]
    assert record.source.source_class is SourceClass.APPROVED_AUTHORITATIVE
    assert record.document_id == document.document_id
    assert record.document_content_hash == document.content_hash
    assert record.document_url == document.canonical_url
    assert record.evidence_id
    assert record.passage_index == 0


def test_evidence_id_changes_when_fetched_document_content_changes():
    first_page = page()
    second_page = page(text="Applicants must attend in person for identity capture.")
    first_doc = page_to_fetched_document(first_page)
    second_doc = page_to_fetched_document(second_page)
    first = build_evidence_records([first_doc], [{
        "source": first_page, "text": first_page["text"], "passage_index": 0,
    }])[0]
    second = build_evidence_records([second_doc], [{
        "source": second_page, "text": second_page["text"], "passage_index": 0,
    }])[0]
    assert first.evidence_id != second.evidence_id


def test_ranked_passage_without_matching_document_fails_closed():
    document = page_to_fetched_document(page())
    with pytest.raises(ValueError, match="does not map"):
        build_evidence_records([document], [{
            "source": {"url": "https://unregistered.example/page"},
            "text": "Unregistered content",
            "passage_index": 0,
        }])
