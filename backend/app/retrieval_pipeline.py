"""Adapters connecting the legacy approved-source fetch/rank path to v1.1 records.

The adapter intentionally performs no network requests. Fetching and URL safety
remain owned by the existing approved-source fetcher until the governed fetch
component is implemented and tested in a later batch.
"""
from __future__ import annotations

from datetime import datetime
from typing import Sequence
from urllib.parse import urlsplit

from app.retrieval_contracts import (
    EvidencePassage,
    FetchedDocument,
    RetrievalContractError,
    SourceClass,
    SourceRecord,
    SourceStatus,
)


def _timestamp(value: str) -> datetime:
    """Parse the retrieval timestamp produced by the approved-source fetcher."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Retrieval timestamp must include a timezone.")
    return parsed


def page_to_fetched_document(page: dict) -> FetchedDocument:
    """Convert one successfully fetched allowlisted page into a provenance record."""
    source_url = str(page["url"])
    final_url = str(page.get("final_url") or source_url)
    source_host = (urlsplit(source_url).hostname or "").lower()
    final_host = (urlsplit(final_url).hostname or "").lower()
    if not source_host or final_host != source_host:
        raise RetrievalContractError("Fetched page must remain on its registered source host.")
    retrieved_at = _timestamp(str(page["last_checked_at"]))
    source = SourceRecord(
        institution=str(page["institution"]),
        title=str(page["title"]),
        url=source_url,
        source_class=SourceClass.APPROVED_AUTHORITATIVE,
        status=SourceStatus.ACTIVE,
        jurisdiction="Papua New Guinea",
        publication_date=page.get("publication_date"),
        last_fetched_at=retrieved_at,
    )
    return FetchedDocument(
        source=source,
        canonical_url=source_url,
        final_url=final_url,
        title=str(page["title"]),
        content_type=str(page.get("content_type") or "text/html"),
        text=str(page["text"]),
        retrieved_at=retrieved_at,
        publication_date=page.get("publication_date"),
        provider="approved-source-registry",
    )


def build_evidence_records(
    documents: Sequence[FetchedDocument],
    ranked_passages: Sequence[dict],
) -> list[EvidencePassage]:
    """Attach stable evidence IDs and provenance to the ranked passage sequence."""
    by_url = {document.canonical_url: document for document in documents}
    records: list[EvidencePassage] = []
    for passage in ranked_passages:
        source_data = passage["source"]
        url = str(source_data["url"])
        document = by_url.get(url)
        if document is None:
            raise ValueError("Ranked passage does not map to a fetched document.")
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
