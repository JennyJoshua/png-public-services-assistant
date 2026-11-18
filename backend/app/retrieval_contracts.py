"""Provider-neutral retrieval contracts for the Simplified Hybrid RAG engine.

These records are deliberately independent of any search vendor or network client.
They describe provenance and evidence; they do not themselves assert that a source
is authoritative or that a retrieved claim is true.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum
from typing import Protocol, Sequence
from urllib.parse import urlsplit


class SourceClass(str, Enum):
    """Project-policy classification assigned after source evaluation."""

    APPROVED_AUTHORITATIVE = "A"
    RECOGNISED_INSTITUTIONAL = "B"
    GENERAL_WEB = "C"
    UNVERIFIED_UNSAFE = "D"


class SourceStatus(str, Enum):
    """Lifecycle state for a source record."""

    ACTIVE = "active"
    PENDING_REVIEW = "pending_review"
    SUPERSEDED = "superseded"
    BROKEN = "broken"


class RetrievalContractError(ValueError):
    """Raised when a retrieval record violates its basic data contract."""


def _require_https_url(value: str, field_name: str) -> str:
    url = value.strip()
    parsed = urlsplit(url)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise RetrievalContractError(f"{field_name} must be an absolute HTTPS URL.")
    if parsed.username or parsed.password:
        raise RetrievalContractError(f"{field_name} must not contain URL credentials.")
    return url


def _stable_digest(*parts: str) -> str:
    material = "\n".join(parts).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


@dataclass(frozen=True)
class SourceRecord:
    """A source's identity and governance metadata; unknown facts stay null."""

    institution: str
    title: str
    url: str
    source_class: SourceClass | None = None
    status: SourceStatus = SourceStatus.PENDING_REVIEW
    authority_tier: str | None = None
    document_type: str | None = None
    jurisdiction: str | None = None
    language: str | None = None
    publication_date: str | None = None
    effective_date: str | None = None
    last_fetched_at: datetime | None = None
    last_reviewed_at: datetime | None = None
    content_hash: str | None = None

    def __post_init__(self) -> None:
        if not self.institution.strip():
            raise RetrievalContractError("Source institution must not be empty.")
        if not self.title.strip():
            raise RetrievalContractError("Source title must not be empty.")
        object.__setattr__(self, "url", _require_https_url(self.url, "Source URL"))

    @property
    def source_id(self) -> str:
        """Stable identifier derived from the exact registered source URL."""
        return _stable_digest("source", self.url)[:24]


@dataclass(frozen=True)
class SearchResult:
    """One normalised result returned by any provider adapter."""

    title: str
    url: str
    snippet: str
    provider: str
    rank: int
    retrieved_at: datetime
    domain: str | None = None
    provider_result_id: str | None = None
    publication_date: str | None = None
    source_class: SourceClass | None = None

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise RetrievalContractError("Search-result provider must not be empty.")
        if self.rank < 1:
            raise RetrievalContractError("Search-result rank must be at least 1.")
        object.__setattr__(self, "url", _require_https_url(self.url, "Search-result URL"))
        if self.domain is None:
            object.__setattr__(self, "domain", (urlsplit(self.url).hostname or "").lower())

    @property
    def result_id(self) -> str:
        """Stable identifier for the same provider result and canonical URL."""
        return _stable_digest("result", self.provider, self.url)[:24]


@dataclass(frozen=True)
class FetchedDocument:
    """A successfully fetched and extracted web document with provenance."""

    source: SourceRecord
    canonical_url: str
    final_url: str
    title: str
    content_type: str
    text: str
    retrieved_at: datetime
    publication_date: str | None = None
    provider: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "canonical_url", _require_https_url(self.canonical_url, "Canonical URL")
        )
        object.__setattr__(self, "final_url", _require_https_url(self.final_url, "Final URL"))
        canonical = urlsplit(self.canonical_url)
        final = urlsplit(self.final_url)
        if self.canonical_url != self.source.url:
            raise RetrievalContractError("Canonical URL must match the registered source URL.")
        canonical_host = (canonical.hostname or "").lower()
        final_host = (final.hostname or "").lower()
        same_host = canonical_host == final_host
        approved_png_government_redirect = (
            canonical_host.endswith(".gov.pg") and final_host.endswith(".gov.pg")
        )
        if not (same_host or approved_png_government_redirect):
            raise RetrievalContractError(
                "Final URL must remain on the canonical host or another .gov.pg host."
            )
        if self.retrieved_at.tzinfo is None:
            raise RetrievalContractError("Document retrieval timestamp must include a timezone.")
        if not self.title.strip():
            raise RetrievalContractError("Fetched-document title must not be empty.")
        if not self.content_type.strip():
            raise RetrievalContractError("Fetched-document content type must not be empty.")
        if not self.text.strip():
            raise RetrievalContractError("Fetched-document text must not be empty.")

    @property
    def content_hash(self) -> str:
        """SHA-256 of the extracted text, for reproducibility and change detection."""
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()

    @property
    def document_id(self) -> str:
        """Stable identifier for the same canonical URL and extracted content."""
        return _stable_digest("document", self.canonical_url, self.content_hash)[:24]


@dataclass(frozen=True)
class EvidencePassage:
    """A passage with a stable link back to the exact fetched document."""

    source: SourceRecord
    document_id: str
    document_url: str
    document_content_hash: str
    passage_index: int
    section_path: tuple[str, ...]
    text: str
    retrieved_at: datetime
    publication_date: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "document_url", _require_https_url(self.document_url, "Evidence document URL")
        )
        if self.document_url != self.source.url:
            raise RetrievalContractError("Evidence document URL must match its source URL.")
        if not self.document_id.strip():
            raise RetrievalContractError("Evidence document ID must not be empty.")
        if self.retrieved_at.tzinfo is None:
            raise RetrievalContractError("Evidence retrieval timestamp must include a timezone.")
        if not re.fullmatch(r"[0-9a-f]{64}", self.document_content_hash):
            raise RetrievalContractError("Evidence document content hash must be a SHA-256 hex digest.")
        if self.passage_index < 0:
            raise RetrievalContractError("Evidence passage index must not be negative.")
        if not self.text.strip():
            raise RetrievalContractError("Evidence passage text must not be empty.")

    @property
    def evidence_id(self) -> str:
        """Stable ID tied to document version, passage order and passage content."""
        return _stable_digest(
            "evidence",
            self.document_id,
            self.document_content_hash,
            str(self.passage_index),
            self.text,
        )[:24]


class SearchProvider(Protocol):
    """Replaceable async interface implemented by a search-provider adapter."""

    name: str

    async def search(self, query: str, *, limit: int = 10) -> Sequence[SearchResult]:
        """Return normalised search results; implementations enforce provider limits."""
        ...



ALLOWED_SOURCE_STATUS_TRANSITIONS: dict[SourceStatus, frozenset[SourceStatus]] = {
    SourceStatus.PENDING_REVIEW: frozenset({SourceStatus.ACTIVE, SourceStatus.BROKEN}),
    SourceStatus.ACTIVE: frozenset({
        SourceStatus.PENDING_REVIEW,
        SourceStatus.BROKEN,
        SourceStatus.SUPERSEDED,
    }),
    SourceStatus.BROKEN: frozenset({SourceStatus.PENDING_REVIEW}),
    SourceStatus.SUPERSEDED: frozenset({SourceStatus.PENDING_REVIEW}),
}


class EvidenceUse(str, Enum):
    """Maximum permitted use of evidence under the source governance policy."""

    PRIMARY = "primary"
    SUPPORTING = "supporting"
    SUPPLEMENTARY = "supplementary"
    EXCLUDED = "excluded"


def transition_source_status(
    source: SourceRecord,
    new_status: SourceStatus,
    *,
    reviewed_at: datetime | None = None,
) -> SourceRecord:
    """Return a new source record after a permitted lifecycle transition.

    Activation requires a timezone-aware human-review timestamp. Fetch success,
    indexing and domain matching must never activate a source automatically.
    """
    if not isinstance(new_status, SourceStatus):
        raise RetrievalContractError("New source status must be a SourceStatus value.")
    if new_status is source.status:
        return source
    if new_status not in ALLOWED_SOURCE_STATUS_TRANSITIONS[source.status]:
        raise RetrievalContractError(
            f"Source status transition not allowed: {source.status.value} -> {new_status.value}."
        )
    if new_status is SourceStatus.ACTIVE:
        if reviewed_at is None or reviewed_at.tzinfo is None:
            raise RetrievalContractError(
                "A timezone-aware human review timestamp is required before activation."
            )
        return replace(source, status=new_status, last_reviewed_at=reviewed_at)
    return replace(source, status=new_status)


def evidence_use_for_source(source: SourceRecord) -> EvidenceUse:
    """Return the maximum evidence role; unknown or inactive sources fail closed.

    Class A may support primary claims. Class B is supporting evidence only.
    Class C is supplementary context and must not be presented as official
    requirements. Class D, unclassified, pending, broken and superseded sources
    are excluded from answer evidence.
    """
    if source.status is not SourceStatus.ACTIVE:
        return EvidenceUse.EXCLUDED
    if source.source_class is SourceClass.APPROVED_AUTHORITATIVE:
        return EvidenceUse.PRIMARY
    if source.source_class is SourceClass.RECOGNISED_INSTITUTIONAL:
        return EvidenceUse.SUPPORTING
    if source.source_class is SourceClass.GENERAL_WEB:
        return EvidenceUse.SUPPLEMENTARY
    return EvidenceUse.EXCLUDED


def is_eligible_for_answer(source: SourceRecord) -> bool:
    """Whether a source can be included in answer evidence at all."""
    return evidence_use_for_source(source) is not EvidenceUse.EXCLUDED


def is_eligible_for_primary_claim(source: SourceRecord) -> bool:
    """Only active Class A evidence may support a primary-authority claim."""
    return evidence_use_for_source(source) is EvidenceUse.PRIMARY
