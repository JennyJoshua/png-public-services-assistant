"""Configured official-source list for the simplified Phase 1 fetcher."""
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

SourceStatus = Literal["active", "superseded", "broken", "pending_review"]
VALID_SOURCE_STATUSES = frozenset({"active", "superseded", "broken", "pending_review"})
ALLOWED_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending_review": frozenset({"active", "broken"}),
    "active": frozenset({"pending_review", "broken", "superseded"}),
    "broken": frozenset({"pending_review"}),
    "superseded": frozenset({"pending_review"}),
}


@dataclass(frozen=True)
class Source:
    institution: str
    title: str
    url: str
    authority_tier: str | None = None
    document_type: str | None = None
    jurisdiction: str | None = None
    language: str | None = None
    publication_date: str | None = None
    effective_date: str | None = None
    last_fetched_at: str | None = None
    last_reviewed_at: str | None = None
    content_hash: str | None = None
    status: SourceStatus = "pending_review"

    def __post_init__(self) -> None:
        if self.status not in VALID_SOURCE_STATUSES:
            raise ValueError(f"unsupported source status: {self.status!r}")


def transition_source_status(
    source: Source, new_status: SourceStatus, *, reviewed_at: str | None = None
) -> Source:
    if new_status not in VALID_SOURCE_STATUSES:
        raise ValueError(f"unsupported source status: {new_status!r}")
    if new_status == source.status:
        return source
    if new_status not in ALLOWED_STATUS_TRANSITIONS[source.status]:
        raise ValueError(
            f"source status transition not allowed: {source.status} -> {new_status}"
        )
    if new_status == "active":
        if not isinstance(reviewed_at, str) or not reviewed_at.strip():
            raise ValueError("reviewed_at is required before a source can become active")
        return replace(source, status=new_status, last_reviewed_at=reviewed_at.strip())
    return replace(source, status=new_status)


def load_sources(path: str | Path | None = None) -> tuple[Source, ...]:
    """Load exact HTTPS source entries from sources.txt; comments and blanks are ignored."""
    config_path = Path(path) if path else Path(__file__).resolve().parents[1] / "sources.txt"
    if not config_path.is_file():
        raise RuntimeError(f"Required source configuration is missing: {config_path}")
    sources: list[Source] = []
    seen: set[str] = set()
    for line_number, raw_line in enumerate(config_path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 3 or not all(parts):
            raise ValueError(f"sources.txt line {line_number} must be URL | agency | topic")
        url, agency, topic = parts
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
            raise ValueError(f"sources.txt line {line_number} must contain a clean HTTPS URL")
        if url in seen:
            raise ValueError(f"sources.txt line {line_number} duplicates URL: {url}")
        seen.add(url)
        sources.append(Source(institution=agency, title=topic, url=url))
    if not sources:
        raise ValueError("sources.txt contains no source entries")
    return tuple(sources)


SOURCES: tuple[Source, ...] = load_sources()
