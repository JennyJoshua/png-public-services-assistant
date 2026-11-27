from datetime import datetime, timezone

from app.source_verification import (
    contains_high_impact_claims,
    extract_document_dates,
    verify_cross_document_consistency,
    verify_temporal_signals,
)

NOW = datetime(2026, 11, 27, 0, 0, tzinfo=timezone.utc)


def test_extracts_explicit_publication_and_modified_dates():
    published, modified = extract_document_dates(
        "Published on 12/02/2026. Last updated: 2026-10-15.",
    )
    assert published.isoformat() == "2026-02-12"
    assert modified.isoformat() == "2026-10-15"


def test_http_last_modified_header_is_parsed_as_freshness_metadata():
    published, modified = extract_document_dates(
        "",
        {"last-modified": "Fri, 27 Nov 2026 00:00:00 GMT"},
    )
    assert published is None
    assert modified.isoformat() == "2026-11-27"


def test_missing_date_does_not_claim_currentness():
    result = verify_temporal_signals("A public service page without a date.", fetched_at=NOW)
    assert result.currentness_signal is False
    assert "no_explicit_publication_or_modified_date" in result.reasons


def test_stale_or_future_dated_content_fails_currentness():
    stale = verify_temporal_signals("Published on 01/01/2018.", fetched_at=NOW)
    future = verify_temporal_signals("Published on 01/01/2028.", fetched_at=NOW)
    assert stale.currentness_signal is False
    assert future.currentness_signal is False


def test_supersession_and_conflict_markers_are_detected():
    result = verify_temporal_signals(
        "Last updated: 2026-10-01. This policy has been superseded and replaced by a new policy.",
        fetched_at=NOW,
    )
    assert result.currentness_signal is False
    assert result.superseded is True


def test_cross_document_check_is_not_complete_without_official_comparator():
    result = verify_cross_document_consistency(
        "https://pngcir.gov.pg/service",
        "Published on 2026-10-01. Service information.",
        (),
        expected_hosts=frozenset({"pngcir.gov.pg"}),
    )
    assert result.completed is False
    assert result.unresolved_conflict is False


def test_cross_document_check_rejects_unapproved_hosts():
    result = verify_cross_document_consistency(
        "https://pngcir.gov.pg/service",
        "Service information.",
        (("https://example.com/page", "Service information."),),
        expected_hosts=frozenset({"pngcir.gov.pg"}),
    )
    assert result.completed is False


def test_cross_document_check_records_exact_official_comparator():
    url = "https://pngcir.gov.pg/current-instrument"
    result = verify_cross_document_consistency(
        "https://pngcir.gov.pg/service",
        "Service information.",
        ((url, "The current instrument governs this service."),),
        expected_hosts=frozenset({"pngcir.gov.pg"}),
    )
    assert result.completed is True
    assert result.unresolved_conflict is False
    assert result.compared_urls == (url,)


def test_cross_document_check_detects_labelled_fee_mismatch():
    result = verify_cross_document_consistency(
        "https://pngcir.gov.pg/service",
        "The application fee is K10.",
        (("https://pngcir.gov.pg/current-instrument", "The application fee is K20."),),
        expected_hosts=frozenset({"pngcir.gov.pg"}),
    )
    assert result.completed is True
    assert result.unresolved_conflict is True
    assert any(item.startswith("labelled_value_mismatch:fee:") for item in result.conflicts)


def test_legal_instrument_year_mismatch_is_a_conflict():
    result = verify_cross_document_consistency(
        "https://rta.gov.pg/licences-approvals/driver-licensing/",
        "Driver licensing fees are prescribed by the Road Traffic (Fees and Charges) Regulation 2017.",
        (
            (
                "https://rta.gov.pg/pdfs/resources/legislation/rules/RTR_LicensingOfDrivers2017.pdf",
                "This Rule refers to the Road Traffic (Fees and Charges) Regulation 2015.",
            ),
            (
                "https://www.rta.gov.pg/licences-approvals/schedule-of-fees-from-1-june-2018/",
                "Road Traffic (Fees and Charges) Regulation 2017 - Schedule 1.",
            ),
        ),
        expected_hosts=frozenset({"rta.gov.pg", "www.rta.gov.pg"}),
    )
    assert result.completed is True
    assert result.unresolved_conflict is True
    assert any(item.startswith("legal_instrument_year_mismatch:") for item in result.conflicts)


def test_high_impact_claim_detector():
    assert contains_high_impact_claims("Applicants must pay a fee of K10.")
    assert not contains_high_impact_claims("This page describes the agency's history.")
