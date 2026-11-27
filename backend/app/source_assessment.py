"""Deterministic, explainable assessment of registered PNG public-service sources.

This module does not fetch URLs and does not trust model confidence. It evaluates
fetch and provenance facts supplied by a controlled assessment runner. Unknown
authority, unresolved conflicts, and missing high-impact corroboration fail closed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from urllib.parse import urlsplit

from app.retrieval_contracts import SourceClass


class AssessmentAction(str, Enum):
    ACTIVATE = "activate"
    HOLD = "hold"
    EXCLUDE = "exclude"


@dataclass(frozen=True)
class AuthorityProfile:
    institution: str
    hosts: frozenset[str]
    topic_terms: tuple[str, ...]
    maximum_class: SourceClass
    current_authority: bool = True


# Exact hosts only. A .gov.pg suffix or search-provider result is never sufficient.
AUTHORITY_PROFILES: tuple[AuthorityProfile, ...] = (
    AuthorityProfile("PNGCIR", frozenset({"pngcir.gov.pg", "www.pngcir.gov.pg"}),
                     ("birth", "nid", "national identity", "civil registry"), SourceClass.APPROVED_AUTHORITATIVE),
    AuthorityProfile("RPNGC", frozenset({"rpngc.gov.pg", "www.rpngc.gov.pg"}),
                     ("police", "clearance", "epolice"), SourceClass.APPROVED_AUTHORITATIVE),
    AuthorityProfile("RTA", frozenset({"rta.gov.pg", "www.rta.gov.pg"}),
                     ("driver", "licence", "license", "vehicle", "road transport"), SourceClass.APPROVED_AUTHORITATIVE),
    AuthorityProfile("IPA", frozenset({"ipa.gov.pg", "www.ipa.gov.pg"}),
                     ("business", "company", "incorporation", "registry", "forms"), SourceClass.APPROVED_AUTHORITATIVE),
    AuthorityProfile("IRC", frozenset({"irc.gov.pg", "www.irc.gov.pg", "static.irc.gov.pg"}),
                     ("tax", "tin", "taxpayer", "revenue", "tax forms"), SourceClass.APPROVED_AUTHORITATIVE),
    AuthorityProfile("Education", frozenset({"education.gov.pg", "www.education.gov.pg"}),
                     ("education", "school", "tuition", "fee", "curriculum"), SourceClass.APPROVED_AUTHORITATIVE),
    AuthorityProfile("Customs", frozenset({"customs.gov.pg", "www.customs.gov.pg"}),
                     ("customs", "import", "export", "trade", "importer", "exporter"), SourceClass.APPROVED_AUTHORITATIVE),
    AuthorityProfile("DICT", frozenset({"ict.gov.pg", "www.ict.gov.pg"}),
                     ("digital government", "government portal", "digital service", "ict"),
                     SourceClass.GENERAL_WEB),
    # ICA is retained as a legacy identity pending verification of its successor authority.
    AuthorityProfile("ICA", frozenset({"ica.gov.pg", "www.ica.gov.pg"}),
                     ("passport", "visa", "citizenship", "migration"),
                     SourceClass.UNVERIFIED_UNSAFE, current_authority=False),
)

_PROFILE_BY_HOST = {
    host: profile for profile in AUTHORITY_PROFILES for host in profile.hosts
}

_HIGH_IMPACT = re.compile(
    r"\b(fee|fees|price|cost|eligibility|eligible|deadline|due date|"
    r"effective date|commencement|penalty|fine|threshold|must submit|"
    r"required document|application requirement|payment|lodgement|lodge at|"
    r"valid for|expires|expiry|visa condition|legal requirement)\b",
    re.IGNORECASE,
)
_ERROR_MARKERS = (
    "404 not found", "page not found", "access denied", "service unavailable",
    "temporarily unavailable", "enable javascript to continue",
)


@dataclass(frozen=True)
class AssessmentInput:
    registered_url: str
    final_url: str
    registered_institution: str
    registered_topic: str
    page_title: str
    content_type: str
    text: str
    fetched_at: datetime
    fetch_succeeded: bool = True
    currentness_verified: bool = False
    scope_statement: str | None = None
    controlling_instrument_verified: bool = False
    corroborating_official_sources: tuple[str, ...] = ()
    unresolved_conflict: bool = False
    superseded: bool = False


@dataclass(frozen=True)
class AssessmentDecision:
    action: AssessmentAction
    source_class: SourceClass
    confidence: float
    hard_gates: dict[str, bool]
    reasons: tuple[str, ...]
    authority_profile: str | None
    policy_version: str = "source-assessment-v1"


def _host(url: str) -> str | None:
    parsed = urlsplit(url)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        return None
    if parsed.username or parsed.password or parsed.fragment:
        return None
    return parsed.hostname.lower()


def _topic_matches(topic: str, profile: AuthorityProfile) -> bool:
    normalized = topic.lower()
    return any(term in normalized for term in profile.topic_terms)


def assess_source(candidate: AssessmentInput) -> AssessmentDecision:
    """Return a deterministic decision; confidence never overrides a failed gate."""
    registered_host = _host(candidate.registered_url)
    final_host = _host(candidate.final_url)
    profile = _PROFILE_BY_HOST.get(registered_host or "")
    authority_verified = bool(
        profile
        and profile.current_authority
        and candidate.registered_institution.casefold() == profile.institution.casefold()
    )
    topic_verified = bool(profile and _topic_matches(candidate.registered_topic, profile))
    final_url_verified = bool(
        registered_host and final_host and profile
        and final_host in profile.hosts
    )
    content_type = candidate.content_type.lower().split(";", 1)[0].strip()
    supported_content = content_type in {"text/html", "application/xhtml+xml", "application/pdf"}
    clean_text = " ".join(candidate.text.split())
    usable_content = (
        candidate.fetch_succeeded
        and supported_content
        and len(clean_text) >= 200
        and not any(marker in clean_text.lower() for marker in _ERROR_MARKERS)
        and bool(candidate.page_title.strip())
    )
    timestamp_valid = (
        candidate.fetched_at.tzinfo is not None
        and candidate.fetched_at.utcoffset() is not None
    )
    scope_verified = bool(candidate.scope_statement and len(candidate.scope_statement.strip()) >= 20)
    no_conflict = not candidate.unresolved_conflict and not candidate.superseded
    high_impact = bool(_HIGH_IMPACT.search(clean_text))
    high_impact_verified = (
        not high_impact
        or (
            candidate.controlling_instrument_verified
            and len(candidate.corroborating_official_sources) >= 1
        )
    )

    gates = {
        "registered_https_url": registered_host is not None,
        "final_url_verified": final_url_verified,
        "competent_authority_verified": authority_verified,
        "topic_authority_verified": topic_verified,
        "fetch_and_content_valid": usable_content,
        "timezone_aware_fetch_timestamp": timestamp_valid,
        "explicit_scope": scope_verified,
        "no_unresolved_conflict_or_supersession": no_conflict,
        "currentness_verified": candidate.currentness_verified,
        "high_impact_requirements_verified": high_impact_verified,
    }
    passed = sum(gates.values())
    confidence = round(passed / len(gates), 2)

    reasons = [name for name, passed_gate in gates.items() if not passed_gate]
    if not profile or not authority_verified or not topic_verified:
        action = AssessmentAction.HOLD
        source_class = SourceClass.UNVERIFIED_UNSAFE
    elif not usable_content or not timestamp_valid or not final_url_verified:
        action = AssessmentAction.EXCLUDE
        source_class = SourceClass.UNVERIFIED_UNSAFE
    elif not no_conflict or not scope_verified:
        action = AssessmentAction.HOLD
        source_class = SourceClass.UNVERIFIED_UNSAFE
    elif profile.maximum_class is SourceClass.APPROVED_AUTHORITATIVE:
        if candidate.currentness_verified and high_impact_verified:
            action = AssessmentAction.ACTIVATE
            source_class = SourceClass.APPROVED_AUTHORITATIVE
        else:
            action = AssessmentAction.HOLD
            source_class = SourceClass.UNVERIFIED_UNSAFE
    elif profile.maximum_class in {
        SourceClass.RECOGNISED_INSTITUTIONAL, SourceClass.GENERAL_WEB
    }:
        # B/C sources can be activated only for their restricted contextual role.
        action = AssessmentAction.ACTIVATE
        source_class = profile.maximum_class
    else:
        action = AssessmentAction.HOLD
        source_class = SourceClass.UNVERIFIED_UNSAFE

    if action is AssessmentAction.ACTIVATE:
        reasons.append("all_required_gates_passed_for_restricted_evidence_role")
    elif not reasons:
        reasons.append("policy_did_not_authorize_activation")

    return AssessmentDecision(
        action=action,
        source_class=source_class,
        confidence=confidence,
        hard_gates=gates,
        reasons=tuple(reasons),
        authority_profile=profile.institution if profile else None,
    )
