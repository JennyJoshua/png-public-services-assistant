"""Adapters connecting approved-source retrieval to provider-neutral evidence.

No network requests or new provider calls occur here. The existing allowlisted
fetcher remains responsible for fetching; this module validates and records its
results without promoting source governance status.
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Sequence
from urllib.parse import urlsplit

from app.retrieval_contracts import (
    EvidencePassage,
    FetchedDocument,
    RetrievalContractError,
    SourceRecord,
    SourceStatus,
    is_eligible_for_answer,
)
from app.source_registry import SOURCES


_SOURCES_BY_URL = {source.url: source for source in SOURCES}


def _timestamp(value: str) -> datetime:
    """Parse an ISO timestamp and require an explicit timezone."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Retrieval timestamp must include a timezone.")
    return parsed


def _optional_timestamp(value: str | None) -> datetime | None:
    return _timestamp(value) if value else None


def page_to_fetched_document(page: dict) -> FetchedDocument:
    """Convert a fetched page only when its exact URL is registered and approved."""
    source_url = str(page["url"])
    registered = _SOURCES_BY_URL.get(source_url)
    if registered is None:
        raise RetrievalContractError(
            "Fetched page URL is not in the approved source registry."
        )

    final_url = str(page.get("final_url") or source_url)
    source_host = (urlsplit(source_url).hostname or "").lower()
    final_host = (urlsplit(final_url).hostname or "").lower()
    if (not source_host or not final_host or urlsplit(final_url).scheme.lower() != "https"
            or (
                final_host != source_host
                and not (source_host.endswith(".gov.pg") and final_host.endswith(".gov.pg"))
            )):
        raise RetrievalContractError(
            "Fetched page must remain on its registered source host."
        )

    retrieved_at = _timestamp(str(page["last_checked_at"]))
    text = str(page["text"])
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

    # Being on the curated fetch allowlist is not the same as having completed
    # source verification. Preserve the registry's status and all unknown facts.
    source = SourceRecord(
        institution=registered.institution,
        title=registered.title,
        url=registered.url,
        status=SourceStatus(registered.status),
        authority_tier=registered.authority_tier,
        document_type=registered.document_type,
        jurisdiction=registered.jurisdiction,
        language=registered.language,
        publication_date=registered.publication_date,
        effective_date=registered.effective_date,
        last_fetched_at=retrieved_at,
        last_reviewed_at=_optional_timestamp(registered.last_reviewed_at),
        content_hash=content_hash,
    )
    return FetchedDocument(
        source=source,
        canonical_url=registered.url,
        final_url=final_url,
        title=str(page.get("title") or registered.title),
        content_type=str(page.get("content_type") or "text/html"),
        text=text,
        retrieved_at=retrieved_at,
        publication_date=page.get("publication_date") or registered.publication_date,
        provider="approved-source-registry",
    )


def build_evidence_records(
    documents: Sequence[FetchedDocument],
    ranked_passages: Sequence[dict],
) -> list[EvidencePassage]:
    """Attach stable evidence IDs and provenance to ranked passages."""
    by_url = {document.canonical_url: document for document in documents}
    records: list[EvidencePassage] = []
    for passage in ranked_passages:
        source_data = passage["source"]
        url = str(source_data["url"])
        document = by_url.get(url)
        if document is None:
            raise RetrievalContractError(
                "Ranked passage does not map to a fetched document."
            )
        records.append(EvidencePassage(
            source=document.source,
            document_id=document.document_id,
            document_url=document.canonical_url,
            document_content_hash=document.content_hash,
            passage_index=int(passage["passage_index"]),
            section_path=tuple(passage.get("section_path", ())),
            text=str(passage["text"]),
            retrieved_at=document.retrieved_at,
            publication_date=document.publication_date,
        ))
    return records


def filter_eligible_source_pages(pages: Sequence[dict]) -> tuple[list[dict], list[FetchedDocument]]:
    """Keep only pages whose registered source is active and classified for answer use.

    Fetch success and allowlist membership do not confer authority. Unknown,
    pending, broken, superseded, or unclassified sources fail closed.
    """
    eligible_pages: list[dict] = []
    eligible_documents: list[FetchedDocument] = []
    for page in pages:
        document = page_to_fetched_document(page)
        if not is_eligible_for_answer(document.source):
            continue
        eligible_pages.append(page)
        eligible_documents.append(document)
    return eligible_pages, eligible_documents
