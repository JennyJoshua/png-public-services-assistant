"""Risk-based policy for discovered candidate pages.

Configured seed hosts are a discovery boundary, not proof that every page is
authoritative evidence. Matching pages may enter automated processing, while
evidence classification and approval remain separate decisions.
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
    """Return exact hosts represented in the curated seed-source configuration.

    These hosts are trusted for automated candidate processing only. This
    function does not assert that each page is reviewed, active, or Class A.
    Exact matching prevents implicit trust of sibling or child subdomains.
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
    hosts: list[str] = []
    for value in (original, final):
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

    Successful candidates whose original and final URLs use exact configured
    seed hosts are eligible for automated processing. No evidence class or
    approval is assigned. New hosts and untrusted redirects require exception
    review; malformed, unsafe, or failed candidates are excluded.
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

    allowed = frozenset(
        host.lower().rstrip(".")
        for host in (trusted_hosts if trusted_hosts is not None else configured_trusted_hosts())
    )
    if not allowed:
        return CandidatePolicyResult("exclude", None, None, "No configured seed-source hosts are available.")

    if all(host in allowed for host in hosts):
        return CandidatePolicyResult(
            "auto_process",
            None,
            hosts[-1],
            "Original and final URLs match exact configured seed-source hosts; evidence classification remains separate.",
        )

    return CandidatePolicyResult(
        "human_review",
        None,
        None,
        "A new or unconfigured host was discovered; verify the institution and domain before adding it to the trusted seed-source configuration.",
    )
