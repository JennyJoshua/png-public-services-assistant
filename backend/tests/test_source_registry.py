from dataclasses import FrozenInstanceError
from urllib.parse import urlparse

import pytest

from app.source_registry import SOURCES, Source


def test_registry_has_unique_exact_https_seed_urls():
    urls = [source.url for source in SOURCES]
    assert len(urls) == 15
    assert len(urls) == len(set(urls))
    assert all(urlparse(url).scheme == "https" for url in urls)


def test_new_sources_default_to_pending_review_and_unknown_metadata():
    source = Source("Example PNG agency", "Example page", "https://example.gov.pg/page")
    assert source.status == "pending_review"
    for field in (
        "authority_tier",
        "document_type",
        "jurisdiction",
        "language",
        "publication_date",
        "effective_date",
        "last_fetched_at",
        "last_reviewed_at",
        "content_hash",
    ):
        assert getattr(source, field) is None


def test_existing_registry_does_not_invent_governance_metadata():
    for source in SOURCES:
        assert source.status == "pending_review"
        assert source.authority_tier is None
        assert source.document_type is None
        assert source.jurisdiction is None
        assert source.language is None
        assert source.publication_date is None
        assert source.effective_date is None
        assert source.last_fetched_at is None
        assert source.last_reviewed_at is None
        assert source.content_hash is None


def test_source_records_are_immutable():
    source = SOURCES[0]
    with pytest.raises(FrozenInstanceError):
        source.status = "active"


@pytest.mark.parametrize("status", ["active", "superseded", "broken", "pending_review"])
def test_source_status_values_are_documented(status):
    source = Source("Example PNG agency", "Example page", "https://example.gov.pg/page", status=status)
    assert source.status == status
