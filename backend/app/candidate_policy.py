"""Risk-based policy for discovered candidate pages.

Configured source hosts are the trust boundary. Pages on those exact hosts may
enter automated processing; unfamiliar hosts are held for exception review.
This policy does not fetch, persist, publish, or alter live answer evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlsplit

from app.source_registry import SOURCES

CandidateAction = Literal["auto_process", "human_review", "exclude"]


@dataclass(frozen=True)
class CandidatePolicyResult:
    action: CandidateAction
    source_class: str | None
    trusted_host: str | None
    reason: str


def configured_trusted_hosts() -> frozenset[str]:
    """Return exact hosts represented by the curated source registry.

    Exact host matching is intentional: trusting one *.gov.pg host must not
    implicitly trust every other government or third-party subdomain.
    """
    return frozenset(
        (urlsplit(source.url).hostname or "").lower()
        for source in SOURCES
        if urlsplit(source.url).hostname
    )


def _candidate_hosts(candidate: dict) -> tuple[str, ...] | None:
    """Validate the candidate's original/canonical and final HTTPS destinations."""
    original = candidate.get("canonical_url") or candidate.get("url")
    final = candidate.get("final_url") or original
    values = (original, final)
    hosts: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            return None
        parsed = urlsplit(value.strip())
        try:
            port = parsed.port
        except ValueError:
            return None
        if (
            parsed.scheme.lower() != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
            or port not in (None, 443)
        ):
            return None
        hosts.append(parsed.hostname.rstrip(".").lower())
    return tuple(hosts)


def evaluate_candidate_policy(
    candidate: dict,
    *,
    trusted_hosts: frozenset[str] | set[str] | None = None,
) -> CandidatePolicyResult:
    """Choose automated processing, exception review, or exclusion.

    A successfully fetched candidate from an exact configured source host is
    eligible for automated processing as Class A. A new host, or a redirect
    involving an untrusted host, requires exception review. Invalid URLs,
    failed fetches and malformed candidate states are excluded.
    """
    if not isinstance(candidate, dict):
        return CandidatePolicyResult("exclude", None, None, "Candidate must be a mapping.")
    if candidate.get("status") != "candidate_unreviewed":
        return CandidatePolicyResult("exclude", None, None, "Candidate fetch did not complete successfully.")
    if candidate.get("approved") is not False or candidate.get("evidence_class") is not None:
        return CandidatePolicyResult("exclude", None, None, "Candidate must remain unapproved and unclassified before policy evaluation.")

    hosts = _candidate_hosts(candidate)
    if hosts is None:
        return CandidatePolicyResult("exclude", None, None, "Candidate must have valid clean HTTPS original and final URLs.")

    allowed = frozenset(host.lower().rstrip(".") for host in (trusted_hosts if trusted_hosts is not None else configured_trusted_hosts()))
    if not allowed:
        return CandidatePolicyResult("exclude", None, None, "No trusted source hosts are configured.")

    if all(host in allowed for host in hosts):
        return CandidatePolicyResult(
            "auto_process",
            "A",
            hosts[-1],
            "Original and final URLs are on exact hosts already present in the curated source registry.",
        )

    return CandidatePolicyResult(
        "human_review",
        None,
        None,
        "A new or untrusted host was discovered; verify the institution and domain before adding it to the trusted host registry.",
    )
