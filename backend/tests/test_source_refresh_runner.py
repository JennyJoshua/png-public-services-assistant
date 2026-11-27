from datetime import datetime, timezone

import pytest

from app.source_assessment import AssessmentAction
from app.source_refresh_runner import (
    _build_assessment,
    _parse_timestamp,
    _scope_statement,
)
from app.source_registry import SOURCES


def page(**overrides):
    value = {
        "title": "Official service page",
        "final_url": SOURCES[4].url,
        "content_type": "text/html; charset=utf-8",
        "last_checked_at": "2026-11-27T07:00:00+00:00",
        "text": (
            "This official service page explains the purpose and scope of the "
            "public service for applicants in Papua New Guinea. It provides "
            "general information about the registry and its service."
        ),
        "content_hash": "a" * 64,
    }
    value.update(overrides)
    return value


def test_scope_statement_is_derived_from_registered_metadata():
    statement = _scope_statement("PNGCIR", "National identity registration")
    assert "PNGCIR" in statement
    assert "National identity registration" in statement
    assert len(statement) >= 20


def test_class_a_candidate_is_held_until_currentness_and_instrument_checks_pass():
    source = next(item for item in SOURCES if item.institution == "PNGCIR")
    candidate_page = page(final_url=source.url)

    decision, audit = _build_assessment(source, candidate_page)

    assert decision.action is AssessmentAction.HOLD
    assert decision.hard_gates["class_a_currentness_verified"] is False
    assert decision.hard_gates["class_a_high_impact_requirements_verified"] is False
    assert decision.hard_gates["no_unresolved_conflict_or_supersession"] is False
    assert audit["currentness_verified"] is False
    assert audit["controlling_instrument_verified"] is False
    assert audit["conflict_check_completed"] is False


def test_supplementary_source_is_not_activated_before_conflict_check():
    source = next(item for item in SOURCES if item.institution == "DICT")
    candidate_page = page(
        final_url=source.url,
        text=(
            "The digital government programme explains institutional progress "
            "and the development of public digital services in Papua New Guinea. "
            "This article describes the programme and its implementation."
        ),
    )

    decision, _ = _build_assessment(source, candidate_page)

    assert decision.action is AssessmentAction.HOLD
    assert decision.authority_profile == "DICT"
    assert decision.hard_gates["no_unresolved_conflict_or_supersession"] is False


def test_refresh_timestamp_must_include_timezone():
    with pytest.raises(ValueError, match="timezone"):
        _parse_timestamp("2026-11-27T07:00:00")
    assert _parse_timestamp("2026-11-27T07:00:00+00:00").tzinfo == timezone.utc
