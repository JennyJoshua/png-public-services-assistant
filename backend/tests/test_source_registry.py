from dataclasses import FrozenInstanceError
from urllib.parse import urlparse

import pytest

from app.source_registry import (
    ALLOWED_STATUS_TRANSITIONS,
    SOURCES,
    Source,
    transition_source_status,
)


def test_registry_has_unique_exact_https_seed_urls():
    urls = [source.url for source in SOURCES]
    assert len(urls) == 15
    assert len(urls) == len(set(urls))
    assert all(urlparse(url).scheme == "https" for url in urls)


def test_new_sources_default_to_pending_review_and_unknown_metadata():
    source = Source("Example PNG agency", "Example page", "https://example.gov.pg/page")
    assert source.status == "pending_review"
    for field in (
        "authority_tier", "document_type", "jurisdiction", "language",
        "publication_date", "effective_date", "last_fetched_at",
        "last_reviewed_at", "content_hash",
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
    with pytest.raises(FrozenInstanceError):
        SOURCES[0].status = "active"


@pytest.mark.parametrize("status", ["active", "superseded", "broken", "pending_review"])
def test_source_status_values_are_supported(status):
    source = Source("Example PNG agency", "Example page", "https://example.gov.pg/page", status=status)
    assert source.status == status


def test_invalid_status_is_rejected_at_runtime():
    with pytest.raises(ValueError, match="unsupported source status"):
        Source("Example", "Page", "https://example.gov.pg/page", status="trusted")


def test_lifecycle_transition_policy_is_explicit():
    assert ALLOWED_STATUS_TRANSITIONS == {
        "pending_review": frozenset({"active", "broken"}),
        "active": frozenset({"pending_review", "broken", "superseded"}),
        "broken": frozenset({"pending_review"}),
        "superseded": frozenset({"pending_review"}),
    }


def test_pending_source_requires_review_timestamp_before_activation():
    source = SOURCES[0]
    with pytest.raises(ValueError, match="reviewed_at is required"):
        transition_source_status(source, "active")


def test_source_can_be_activated_after_explicit_review():
    source = SOURCES[0]
    reviewed = transition_source_status(
        source, "active", reviewed_at="2026-11-17T10:00:00+10:00"
    )
    assert reviewed.status == "active"
    assert reviewed.last_reviewed_at == "2026-11-17T10:00:00+10:00"
    assert source.status == "pending_review"


@pytest.mark.parametrize(
    ("initial", "target"),
    [
        ("pending_review", "superseded"),
        ("broken", "active"),
        ("superseded", "active"),
        ("broken", "superseded"),
    ],
)
def test_disallowed_lifecycle_transitions_are_rejected(initial, target):
    source = Source(
        "Example", "Page", "https://example.gov.pg/page", status=initial
    )
    with pytest.raises(ValueError, match="transition not allowed"):
        transition_source_status(source, target, reviewed_at="2026-11-17T10:00:00+10:00")


def test_broken_source_must_return_to_review_before_activation():
    source = Source("Example", "Page", "https://example.gov.pg/page", status="broken")
    reviewed = transition_source_status(source, "pending_review")
    active = transition_source_status(
        reviewed, "active", reviewed_at="2026-11-17T10:00:00+10:00"
    )
    assert active.status == "active"


def test_same_status_transition_is_idempotent():
    source = SOURCES[0]
    assert transition_source_status(source, "pending_review") is source
