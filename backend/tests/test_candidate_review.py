from datetime import datetime, timezone

import pytest

from app.candidate_review import CandidateReviewError, review_candidate
from app.retrieval_contracts import SourceClass, SourceStatus

NOW = datetime(2026, 11, 18, 8, 0, tzinfo=timezone.utc)


def candidate(**overrides):
    values = {
        "candidate_id": "candidate-123",
        "title": "Public service information",
        "url": "https://example.gov.pg/service",
        "canonical_url": "https://example.gov.pg/service",
        "status": "candidate_unreviewed",
        "approved": False,
        "evidence_class": None,
        "publication_date": None,
    }
    values.update(overrides)
    return values


def test_candidate_cannot_be_approved_without_explicit_human_review():
    with pytest.raises(CandidateReviewError, match="reviewer"):
        review_candidate(
            candidate(), decision="approve", reviewer=" ",
            reviewed_at=NOW, source_class=SourceClass.APPROVED_AUTHORITATIVE,
            institution="Example Agency",
        )


def test_approval_requires_explicit_class_and_institution_and_activates_with_review_stamp():
    result = review_candidate(
        candidate(),
        decision="approve",
        reviewer="source-reviewer",
        reviewed_at=NOW,
        source_class=SourceClass.APPROVED_AUTHORITATIVE,
        institution="Example PNG Agency",
    )
    assert result.decision == "approve"
    assert result.reviewer == "source-reviewer"
    assert result.reviewed_at == NOW
    assert result.source is not None
    assert result.source.status is SourceStatus.ACTIVE
    assert result.source.source_class is SourceClass.APPROVED_AUTHORITATIVE
    assert result.source.last_reviewed_at == NOW
    assert result.source.authority_tier is None
    assert result.source.jurisdiction is None


def test_class_d_cannot_be_approved():
    with pytest.raises(CandidateReviewError, match="A, B or C"):
        review_candidate(
            candidate(), decision="approve", reviewer="reviewer",
            reviewed_at=NOW, source_class=SourceClass.UNVERIFIED_UNSAFE,
            institution="Example",
        )


def test_general_web_can_only_be_approved_as_class_c():
    result = review_candidate(
        candidate(url="https://example.com/info", canonical_url="https://example.com/info"),
        decision="approve",
        reviewer="reviewer",
        reviewed_at=NOW,
        source_class=SourceClass.GENERAL_WEB,
        institution="Example publisher",
    )
    assert result.source.source_class is SourceClass.GENERAL_WEB


def test_rejection_never_creates_an_active_source():
    result = review_candidate(
        candidate(), decision="reject", reviewer="reviewer",
        reviewed_at=NOW, reason="Not relevant to PNG public services.",
    )
    assert result.decision == "reject"
    assert result.source is None
    assert result.reason == "Not relevant to PNG public services."


@pytest.mark.parametrize("invalid", [
    {"status": "unavailable", "approved": False, "evidence_class": None},
    {"status": "candidate_unreviewed", "approved": True, "evidence_class": None},
    {"status": "candidate_unreviewed", "approved": False, "evidence_class": "A"},
])
def test_only_pristine_unreviewed_candidates_enter_review_gate(invalid):
    with pytest.raises(CandidateReviewError):
        review_candidate(
            candidate(**invalid), decision="reject", reviewer="reviewer",
            reviewed_at=NOW,
        )


def test_review_timestamp_must_be_timezone_aware():
    with pytest.raises(CandidateReviewError, match="timezone-aware"):
        review_candidate(
            candidate(), decision="reject", reviewer="reviewer",
            reviewed_at=datetime(2026, 11, 18, 8, 0),
        )


def test_approval_rejects_non_https_candidate_urls():
    with pytest.raises(ValueError):
        review_candidate(
            candidate(url="http://example.gov.pg/service", canonical_url="http://example.gov.pg/service"),
            decision="approve",
            reviewer="reviewer",
            reviewed_at=NOW,
            source_class=SourceClass.APPROVED_AUTHORITATIVE,
            institution="Example Agency",
        )
