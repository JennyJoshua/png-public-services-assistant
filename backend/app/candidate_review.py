"""Explicit human-review gate for discovered web candidates.

This module is a pure policy boundary: it does not persist decisions, mutate the
configured source registry, fetch URLs, or connect candidates to live retrieval.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from app.retrieval_contracts import (
    SourceClass,
    SourceRecord,
    SourceStatus,
    transition_source_status,
)


ReviewDecision = Literal["approve", "reject"]
APPROVABLE_CLASSES = frozenset({
    SourceClass.APPROVED_AUTHORITATIVE,
    SourceClass.RECOGNISED_INSTITUTIONAL,
    SourceClass.GENERAL_WEB,
})


class CandidateReviewError(ValueError):
    """Raised when a candidate review does not satisfy governance requirements."""


@dataclass(frozen=True)
class CandidateReview:
    candidate_id: str
    decision: ReviewDecision
    reviewer: str
    reviewed_at: datetime
    source: SourceRecord | None
    reason: str | None = None


def review_candidate(
    candidate: dict,
    *,
    decision: ReviewDecision,
    reviewer: str,
    reviewed_at: datetime,
    source_class: SourceClass | None = None,
    institution: str | None = None,
    reason: str | None = None,
) -> CandidateReview:
    """Record an explicit review decision; approval requires class and institution.

    Rejected candidates never produce a SourceRecord. Approved candidates are
    activated only through the existing human-timestamp lifecycle transition.
    Class D cannot be approved. No decision is persisted or automatically applied.
    """
    if not isinstance(candidate, dict):
        raise CandidateReviewError("Candidate must be a mapping.")
    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise CandidateReviewError("Candidate ID is required.")
    if candidate.get("status") != "candidate_unreviewed":
        raise CandidateReviewError("Only unreviewed candidates may enter this review gate.")
    if candidate.get("approved") is not False or candidate.get("evidence_class") is not None:
        raise CandidateReviewError("Candidate must remain unapproved and unclassified before review.")
    if decision not in {"approve", "reject"}:
        raise CandidateReviewError("Review decision must be approve or reject.")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise CandidateReviewError("A named human reviewer is required.")
    if not isinstance(reviewed_at, datetime) or reviewed_at.tzinfo is None:
        raise CandidateReviewError("A timezone-aware review timestamp is required.")

    if decision == "reject":
        return CandidateReview(
            candidate_id=candidate_id,
            decision="reject",
            reviewer=reviewer.strip(),
            reviewed_at=reviewed_at,
            source=None,
            reason=(reason or "Rejected during human review.")[:500],
        )

    if source_class not in APPROVABLE_CLASSES:
        raise CandidateReviewError("Approval requires an explicit A, B or C evidence class; class D is excluded.")
    if not isinstance(institution, str) or not institution.strip():
        raise CandidateReviewError("Institution or publisher must be identified by the reviewer.")
    title = candidate.get("title")
    url = candidate.get("canonical_url") or candidate.get("url")
    if not isinstance(title, str) or not title.strip():
        raise CandidateReviewError("Candidate title is required for approval.")
    if not isinstance(url, str) or not url.strip():
        raise CandidateReviewError("Candidate HTTPS URL is required for approval.")

    pending = SourceRecord(
        institution=institution.strip(),
        title=title.strip()[:200],
        url=url.strip(),
        source_class=source_class,
        status=SourceStatus.PENDING_REVIEW,
        authority_tier=None,
        document_type=None,
        jurisdiction=None,
        language=None,
        publication_date=candidate.get("publication_date"),
    )
    active = transition_source_status(
        pending,
        SourceStatus.ACTIVE,
        reviewed_at=reviewed_at,
    )
    return CandidateReview(
        candidate_id=candidate_id,
        decision="approve",
        reviewer=reviewer.strip(),
        reviewed_at=reviewed_at,
        source=active,
        reason=(reason or "Approved by human review.")[:500],
    )
