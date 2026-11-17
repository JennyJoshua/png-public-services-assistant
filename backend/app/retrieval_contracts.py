"""Provider-neutral retrieval contracts for the Simplified Hybrid RAG engine.

These records are deliberately independent of any search vendor or network client.
They describe provenance and evidence; they do not themselves assert that a source
is authoritative or that a retrieved claim is true.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
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
