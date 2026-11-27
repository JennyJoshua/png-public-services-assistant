from datetime import datetime, timezone

import pytest

from app.retrieval_contracts import SourceClass
from app.source_assessment import (
    AssessmentAction,
    AssessmentInput,
    assess_source,
)

NOW = datetime(2026, 11, 27, 0, 0, tzinfo=timezone.utc)
TEXT = (
    "The National Identity Registration service provides information about "
    "registration procedures and the supporting documents applicants may need. "
    "Applicants can find further service information through the registry office. "
    "This page explains the purpose and scope of the public service."
)


def candidate(**changes):
    values = {
        "registered_url": "https://pngcir.gov.pg/nid-registration-information",
        "final_url": "https://pngcir.gov.pg/nid-registration-information",
        "registered_institution": "PNGCIR",
        "registered_topic": "Online birth and NID registration",
        "page_title": "National Identity Registration",
        "content_type": "text/html; charset=utf-8",
        "text": TEXT,
        "fetched_at": NOW,
        "currentness_verified": True,
        "scope_statement": "PNG national identity registration information for applicants.",
        "conflict_check_completed": True,
    }
    values.update(changes)
    return AssessmentInput(**values)


def test_strong_authoritative_source_can_be_automatically_activated():
    decision = assess_source(candidate())
    assert decision.action is AssessmentAction.ACTIVATE
    assert decision.source_class is SourceClass.APPROVED_AUTHORITATIVE
    assert decision.hard_gates["competent_authority_verified"]
    assert decision.hard_gates["topic_authority_verified"]
    assert decision.confidence == 1.0


def test_gov_pg_suffix_alone_does_not_establish_authority():
    decision = assess_source(candidate(
        registered_url="https://unlisted.gov.pg/nid",
        final_url="https://unlisted.gov.pg/nid",
    ))
    assert decision.action is AssessmentAction.HOLD
    assert not decision.hard_gates["competent_authority_verified"]


def test_registered_agency_must_match_exact_authority_profile():
    decision = assess_source(candidate(registered_institution="Another Department"))
    assert decision.action is AssessmentAction.HOLD
    assert not decision.hard_gates["competent_authority_verified"]


def test_redirect_must_remain_on_an_explicitly_mapped_host():
    decision = assess_source(candidate(final_url="https://external.example/page"))
    assert decision.action is AssessmentAction.EXCLUDE
    assert not decision.hard_gates["final_url_verified"]


def test_high_impact_requirements_need_controlling_instrument_and_corroboration():
    decision = assess_source(candidate(
        text=TEXT + " Applicants must pay a fee of K10 and lodge the form by the deadline."
    ))
    assert decision.action is AssessmentAction.HOLD
    assert not decision.hard_gates["class_a_high_impact_requirements_verified"]

    verified = assess_source(candidate(
        text=TEXT + " Applicants must pay a fee of K10 and lodge the form by the deadline.",
        controlling_instrument_verified=True,
        corroborating_official_sources=("https://pngcir.gov.pg/current-instrument",),
    ))
    assert verified.action is AssessmentAction.ACTIVATE


def test_missing_currentness_evidence_holds_class_a_source():
    decision = assess_source(candidate(currentness_verified=False))
    assert decision.action is AssessmentAction.HOLD
    assert not decision.hard_gates["class_a_currentness_verified"]


def test_unresolved_conflict_or_supersession_holds_source():
    conflict = assess_source(candidate(unresolved_conflict=True))
    superseded = assess_source(candidate(superseded=True))
    assert conflict.action is AssessmentAction.HOLD
    assert superseded.action is AssessmentAction.HOLD


def test_fetch_error_and_error_page_are_excluded():
    failed = assess_source(candidate(fetch_succeeded=False))
    error_page = assess_source(candidate(text="404 not found " + TEXT))
    assert failed.action is AssessmentAction.EXCLUDE
    assert error_page.action is AssessmentAction.EXCLUDE


def test_confidence_does_not_override_failed_hard_gate():
    decision = assess_source(candidate(currentness_verified=False))
    assert decision.confidence > 0.8
    assert decision.action is AssessmentAction.HOLD


def test_activation_requires_a_completed_conflict_check():
    decision = assess_source(candidate(conflict_check_completed=False))
    assert decision.action is AssessmentAction.HOLD
    assert not decision.hard_gates["no_unresolved_conflict_or_supersession"]


def test_legacy_ica_domain_is_not_treated_as_current_authority():
    decision = assess_source(candidate(
        registered_url="https://ica.gov.pg/passport/applying-for-a-png-passport",
        final_url="https://ica.gov.pg/passport/applying-for-a-png-passport",
        registered_institution="ICA",
        registered_topic="How to apply for a PNG passport",
    ))
    assert decision.action is AssessmentAction.HOLD
    assert decision.authority_profile == "ICA"


def test_official_news_domain_is_limited_to_supplementary_context():
    decision = assess_source(candidate(
        registered_url="https://ict.gov.pg/a-digital-leap",
        final_url="https://ict.gov.pg/a-digital-leap",
        registered_institution="DICT",
        registered_topic="e-Government portal progress",
        currentness_verified=False,
        scope_statement="Institutional progress reporting about digital government.",
    ))
    assert decision.action is AssessmentAction.ACTIVATE
    assert decision.source_class is SourceClass.GENERAL_WEB
