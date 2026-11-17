from datetime import datetime, timezone

import pytest

from app.retrieval_contracts import (
    RetrievalContractError,
    SourceStatus,
)
from app.retrieval_pipeline import build_evidence_records, page_to_fetched_document


NOW = "2026-11-16T07:00:00+00:00"
URL = "https://pngcir.gov.pg/nid-registration-information"
TEXT = "Applicants must lodge the completed form at the registry office."


def page(**overrides):
    value = {
        "institution": "Untrusted page institution",
        "title": "NID registration information",
        "url": URL,
        "final_url": URL,
        "content_type": "text/html; charset=utf-8",
        "publication_date": None,
        "last_checked_at": NOW,
        "text": TEXT,
    }
    value.update(overrides)
    return value


def test_adapter_preserves_registry_status_and_unknown_governance_metadata():
    document = page_to_fetched_document(page())
    source = document.source

    assert source.status is SourceStatus.PENDING_REVIEW
    assert source.source_class is None
    assert source.authority_tier is None
    assert source.document_type is None
    assert source.jurisdiction is None
    assert source.language is None
    assert source.publication_date is None
    assert source.effective_date is None
    assert source.last_reviewed_at is None
    assert source.institution == "PNGCIR"
    assert source.title == "NID registration procedure and witness rules"
    assert source.last_fetched_at == datetime(
        2026, 11, 16, 7, 0, tzinfo=timezone.utc
    )
    assert source.content_hash == document.content_hash
    assert document.final_url == URL
    assert document.content_type.startswith("text/html")


def test_adapter_rejects_timestamp_without_timezone():
    with pytest.raises(ValueError, match="timezone"):
        page_to_fetched_document(
            page(last_checked_at="2026-11-16T07:00:00")
        )


def test_adapter_rejects_url_not_exactly_in_approved_registry():
    with pytest.raises(RetrievalContractError, match="approved source registry"):
        page_to_fetched_document(
            page(url="https://pngcir.gov.pg/unregistered-page/")
        )


def test_adapter_rejects_redirect_to_another_host():
    with pytest.raises(RetrievalContractError, match="registered source host"):
        page_to_fetched_document(
            page(final_url="https://unrelated.example/collect")
        )


def test_ranked_passages_receive_stable_provenance_and_registry_status():
    fetched_page = page()
    document = page_to_fetched_document(fetched_page)
    ranked = [{
        "source": fetched_page,
        "text": TEXT,
        "passage_index": 0,
        "section_path": ("NID registration", "Applying"),
        "score": 2.1,
    }]

    records = build_evidence_records([document], ranked)

    assert len(records) == 1
    record = records[0]
    assert record.source.status is SourceStatus.PENDING_REVIEW
    assert record.source.source_class is None
    assert record.document_id == document.document_id
    assert record.document_content_hash == document.content_hash
    assert record.document_url == document.canonical_url
    assert record.section_path == ("NID registration", "Applying")
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


def test_ranked_passage_without_matching_fetched_document_fails_closed():
    document = page_to_fetched_document(page())
    with pytest.raises(RetrievalContractError, match="does not map"):
        build_evidence_records([document], [{
            "source": {"url": "https://unregistered.example/page"},
            "text": "Unregistered content",
            "passage_index": 0,
        }])


def test_page_publication_date_is_kept_as_document_metadata_only():
    document = page_to_fetched_document(
        page(publication_date="2024-06-15")
    )
    assert document.publication_date == "2024-06-15"
    assert document.source.publication_date is None
    assert document.source.last_reviewed_at is None
