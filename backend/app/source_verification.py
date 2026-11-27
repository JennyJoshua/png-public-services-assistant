"""Deterministic temporal and cross-document verification primitives.

These checks produce evidence signals, not legal conclusions. A recent page date
cannot prove that a law or policy remains in force. High-impact claims still
require a fetched controlling instrument and a corroborating competent source.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Iterable
from urllib.parse import urlsplit


_DATE_PATTERNS = (
    re.compile(r"\b(?:published|issued|effective|commenced|last updated|updated)\s*(?:on|:)?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{4}-\d{2}-\d{2})", re.I),
    re.compile(r"\b(?:published|issued|effective|commenced|last updated|updated)\s*(?:on|:)?\s*([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})", re.I),
)
_SUPERSESSION_MARKERS = (
    "superseded", "repealed", "revoked", "rescinded", "withdrawn",
    "replaced by", "no longer in force", "ceased to apply", "obsolete",
    "archived for historical reference", "draft for consultation",
)
_CONFLICT_MARKERS = (
    "inconsistent with", "conflicts with", "contrary to", "different from",
    "subject to amendment", "pending amendment",
)
_LABELLED_VALUES = re.compile(
    r"(?P<label>minimum age|age requirement|application deadline|deadline|"
    r"valid for|validity|fee|fees|price|cost|threshold)\s*"
    r"(?:is|of|:|=)?\s*(?P<value>(?:k\s*)?\d+(?:[.,]\d+)?"
    r"(?:\s*(?:days?|months?|years?))?)",
    re.I,
)
_LEGAL_CITATION = re.compile(
    r"(?P<title>[A-Z][A-Za-z0-9&'()/,\-\s]{3,100}?\b(?:Act|Regulation|Rules))"
    r"\s+(?P<year>(?:19|20)\d{2})",
    re.I,
)
_HIGH_IMPACT_MARKERS = re.compile(
    r"\b(fee|fees|price|cost|eligibility|eligible|deadline|due date|"
    r"effective date|commencement|penalty|fine|threshold|must submit|"
    r"required document|application requirement|payment|lodgement|lodge at|"
    r"valid for|expires|expiry|visa condition|legal requirement)\b",
    re.I,
)


@dataclass(frozen=True)
class TemporalVerification:
    publication_date: date | None
    modified_date: date | None
    currentness_signal: bool
    superseded: bool
    explicit_conflict_signal: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class CrossDocumentVerification:
    completed: bool
    unresolved_conflict: bool
    compared_urls: tuple[str, ...]
    conflicts: tuple[str, ...]
    reason: str


def _parse_date(value: str) -> date | None:
    raw_value = value.strip()
    try:
        return parsedate_to_datetime(raw_value).date()
    except (TypeError, ValueError, OverflowError):
        pass
    value = raw_value.replace(",", "")
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%B %d %Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def extract_document_dates(text: str, metadata: dict[str, str] | None = None) -> tuple[date | None, date | None]:
    """Extract explicit publication/issue and modification dates only."""
    metadata = {str(k).lower(): str(v) for k, v in (metadata or {}).items()}
    published = None
    modified = None
    for key in ("article:published_time", "datepublished", "date_published", "publication_date", "dc.date"):
        if metadata.get(key):
            published = _parse_date(metadata[key][:10]) or _parse_date(metadata[key])
            if published:
                break
    for key in ("article:modified_time", "datemodified", "date_modified", "last-modified", "modified"):
        if metadata.get(key):
            modified = _parse_date(metadata[key][:10]) or _parse_date(metadata[key])
            if modified:
                break
    for pattern in _DATE_PATTERNS:
        for match in pattern.finditer(text[:50000]):
            label = match.group(0).lower()
            parsed = _parse_date(match.group(1))
            if not parsed:
                continue
            if any(term in label for term in ("updated", "modified")):
                modified = modified or parsed
            else:
                published = published or parsed
    return published, modified


def verify_temporal_signals(
    text: str,
    *,
    fetched_at: datetime,
    metadata: dict[str, str] | None = None,
    max_age_days: int = 1825,
) -> TemporalVerification:
    """Check date freshness and explicit withdrawal/supersession signals.

    This is a conservative metadata/content check. It is not proof that an
    instrument remains legally in force; that requires separate instrument
    verification and corroboration.
    """
    if fetched_at.tzinfo is None or fetched_at.utcoffset() is None:
        raise ValueError("fetched_at must be timezone-aware")
    published, modified = extract_document_dates(text, metadata)
    effective_date = modified or published
    reasons: list[str] = []
    if effective_date is None:
        reasons.append("no_explicit_publication_or_modified_date")
        currentness = False
    else:
        age = (fetched_at.astimezone(timezone.utc).date() - effective_date).days
        if age < -2:
            reasons.append("document_date_is_in_the_future")
            currentness = False
        elif age > max_age_days:
            reasons.append("document_date_exceeds_freshness_window")
            currentness = False
        else:
            currentness = True
            reasons.append("explicit_document_date_within_freshness_window")

    normalized = " ".join(text.lower().split())
    superseded = any(marker in normalized for marker in _SUPERSESSION_MARKERS)
    explicit_conflict = any(marker in normalized for marker in _CONFLICT_MARKERS)
    if superseded:
        reasons.append("explicit_supersession_or_withdrawal_marker")
    if explicit_conflict:
        reasons.append("explicit_conflict_or_amendment_marker")
    return TemporalVerification(
        publication_date=published,
        modified_date=modified,
        currentness_signal=currentness and not superseded,
        superseded=superseded,
        explicit_conflict_signal=explicit_conflict,
        reasons=tuple(reasons),
    )


def _extract_legal_references(text: str) -> dict[str, set[str]]:
    """Extract named PNG legal instruments and their cited years."""
    references: dict[str, set[str]] = {}
    for match in _LEGAL_CITATION.finditer(text):
        title = re.sub(r"[^a-z0-9]+", " ", match.group("title").lower()).strip()
        if title:
            references.setdefault(title, set()).add(match.group("year"))
    return references


def verify_cross_document_consistency(
    primary_url: str,
    primary_text: str,
    corroborating_documents: Iterable[tuple[str, str]],
    *,
    expected_hosts: frozenset[str],
) -> CrossDocumentVerification:
    """Compare a primary document with explicitly fetched official documents.

    URLs are accepted only when HTTPS and on an exact configured host. An empty
    corroboration set is never reported as a completed conflict check.
    """
    parsed = urlsplit(primary_url)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in expected_hosts:
        return CrossDocumentVerification(False, True, (), ("primary_host_not_authorised",), "primary source host is not authorised")

    documents: list[tuple[str, str]] = []
    for url, text in corroborating_documents:
        candidate = urlsplit(url)
        host = (candidate.hostname or "").lower()
        if candidate.scheme != "https" or host not in expected_hosts or not text.strip():
            continue
        documents.append((url, " ".join(text.lower().split())))

    if not documents:
        return CrossDocumentVerification(
            False, False, (), (), "no corroborating official document was fetched"
        )

    primary = " ".join(primary_text.lower().split())
    # Detect explicit contradictions/withdrawal notices and compare repeated
    # labelled numeric claims only where both documents state the same field.
    conflicts: list[str] = []
    if any(marker in primary for marker in _SUPERSESSION_MARKERS):
        conflicts.append("primary_document_contains_supersession_marker")
    if any(marker in primary for marker in _CONFLICT_MARKERS):
        conflicts.append("primary_document_contains_conflict_marker")
    all_legal_references: list[tuple[str, dict[str, set[str]]]] = [
        ("primary", _extract_legal_references(primary))
    ]
    all_legal_references.extend(
        (url, _extract_legal_references(other)) for url, other in documents
    )
    for index, (left_url, left_refs) in enumerate(all_legal_references):
        for right_url, right_refs in all_legal_references[index + 1:]:
            for title in left_refs.keys() & right_refs.keys():
                years = left_refs[title] | right_refs[title]
                if len(years) > 1:
                    conflicts.append(
                        f"legal_instrument_year_mismatch:{title}:{','.join(sorted(years))}"
                    )

    primary_values = {
        match.group("label").lower(): match.group("value").replace(" ", "")
        for match in _LABELLED_VALUES.finditer(primary)
    }
    for url, other in documents:
        if any(marker in other for marker in _SUPERSESSION_MARKERS):
            conflicts.append(f"corroborating_document_supersession:{url}")
        if any(marker in other for marker in _CONFLICT_MARKERS):
            conflicts.append(f"corroborating_document_conflict_marker:{url}")
        other_values = {
            match.group("label").lower(): match.group("value").replace(" ", "")
            for match in _LABELLED_VALUES.finditer(other)
        }
        for label in primary_values.keys() & other_values.keys():
            if primary_values[label] != other_values[label]:
                conflicts.append(f"labelled_value_mismatch:{label}:{url}")
    return CrossDocumentVerification(
        completed=True,
        unresolved_conflict=bool(conflicts),
        compared_urls=tuple(url for url, _ in documents),
        conflicts=tuple(conflicts),
        reason="official corroborating documents fetched and deterministic conflict markers compared",
    )


def contains_high_impact_claims(text: str) -> bool:
    return bool(_HIGH_IMPACT_MARKERS.search(text))
