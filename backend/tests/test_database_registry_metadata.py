from app.retrieval_contracts import (
    EvidenceUse,
    SourceClass,
    SourceStatus,
    evidence_use_for_source,
)
from app.retrieval_pipeline import page_to_fetched_document


URL = "https://pngcir.gov.pg/nid-registration-information"
TOPIC = "Online birth and NID registration, witness rules"


def database_page(**overrides):
    page = {
        "institution": "PNGCIR",
        "agency": "PNGCIR",
        "title": "National Identity Registration",
        "topic": TOPIC,
        "url": URL,
        "final_url": URL,
        "content_type": "text/html; charset=utf-8",
        "publication_date": None,
        "last_checked_at": "2026-11-27T07:00:00+00:00",
        "text": "Official National Identity Registration information for applicants.",
        "_registry_source_class": "approved_authoritative",
        "_registry_status": "active",
    }
    page.update(overrides)
    return page


def test_database_registry_metadata_enables_only_approved_active_authority():
    document = page_to_fetched_document(database_page())

    assert document.source.status is SourceStatus.ACTIVE
    assert document.source.source_class is SourceClass.APPROVED_AUTHORITATIVE
    assert evidence_use_for_source(document.source) is EvidenceUse.PRIMARY


def test_database_pending_source_remains_excluded_even_if_classified():
    document = page_to_fetched_document(
        database_page(_registry_status="pending_review")
    )

    assert evidence_use_for_source(document.source) is EvidenceUse.EXCLUDED


def test_database_active_but_unverified_source_remains_excluded():
    document = page_to_fetched_document(
        database_page(_registry_source_class="unverified_unsafe")
    )

    assert document.source.status is SourceStatus.ACTIVE
    assert document.source.source_class is SourceClass.UNVERIFIED_UNSAFE
    assert evidence_use_for_source(document.source) is EvidenceUse.EXCLUDED


def test_database_metadata_cannot_override_configured_institution():
    from app.retrieval_contracts import RetrievalContractError
    import pytest

    with pytest.raises(RetrievalContractError, match="institution"):
        page_to_fetched_document(database_page(institution="Untrusted Agency"))


def test_database_metadata_cannot_override_configured_topic():
    from app.retrieval_contracts import RetrievalContractError
    import pytest

    with pytest.raises(RetrievalContractError, match="topic"):
        page_to_fetched_document(database_page(topic="Different topic"))


def test_database_source_content_hash_must_match_immutable_version_record():
    import pytest
    from app.retrieval_contracts import RetrievalContractError

    with pytest.raises(RetrievalContractError, match="recorded source-version hash"):
        page_to_fetched_document(database_page(content_hash="0" * 64))
