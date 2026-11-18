import pytest

from app.candidate_policy import (
    configured_trusted_hosts,
    evaluate_candidate_policy,
)


def candidate(**overrides):
    values = {
        "url": "https://ica.gov.pg/passport/applying-for-a-png-passport",
        "canonical_url": "https://ica.gov.pg/passport/applying-for-a-png-passport",
        "final_url": "https://ica.gov.pg/passport/applying-for-a-png-passport",
        "status": "candidate_unreviewed",
        "approved": False,
        "evidence_class": None,
    }
    values.update(overrides)
    return values


def test_configured_trust_is_derived_from_exact_seed_hosts():
    hosts = configured_trusted_hosts()
    assert "ica.gov.pg" in hosts
    assert "www.ipa.gov.pg" in hosts
    assert "unlisted.gov.pg" not in hosts


def test_candidate_on_exact_configured_host_is_automatically_eligible():
    result = evaluate_candidate_policy(candidate())
    assert result.action == "auto_process"
    assert result.source_class == "A"
    assert result.trusted_host == "ica.gov.pg"


def test_new_government_host_requires_exception_review_not_automatic_trust():
    result = evaluate_candidate_policy(
        candidate(
            url="https://new-agency.gov.pg/service",
            canonical_url="https://new-agency.gov.pg/service",
            final_url="https://new-agency.gov.pg/service",
        )
    )
    assert result.action == "human_review"
    assert result.source_class is None


def test_untrusted_redirect_prevents_automatic_processing():
    result = evaluate_candidate_policy(
        candidate(final_url="https://third-party.example/service")
    )
    assert result.action == "human_review"
    assert result.source_class is None


def test_all_hosts_must_be_exactly_trusted():
    result = evaluate_candidate_policy(
        candidate(),
        trusted_hosts={"ica.gov.pg"},
    )
    assert result.action == "auto_process"

    subdomain = evaluate_candidate_policy(
        candidate(
            url="https://new.ica.gov.pg/service",
            canonical_url="https://new.ica.gov.pg/service",
            final_url="https://new.ica.gov.pg/service",
        ),
        trusted_hosts={"ica.gov.pg"},
    )
    assert subdomain.action == "human_review"


@pytest.mark.parametrize(
    "url",
    [
        "http://ica.gov.pg/service",
        "https://user:pass@ica.gov.pg/service",
        "https://ica.gov.pg:8443/service",
        "https://ica.gov.pg/service#fragment",
        "not-a-url",
    ],
)
def test_invalid_or_unsafe_urls_are_excluded(url):
    result = evaluate_candidate_policy(
        candidate(url=url, canonical_url=url, final_url=url)
    )
    assert result.action == "exclude"
    assert result.source_class is None


@pytest.mark.parametrize(
    "overrides",
    [
        {"status": "unavailable"},
        {"approved": True},
        {"evidence_class": "A"},
    ],
)
def test_only_successfully_fetched_unapproved_candidates_are_evaluated(overrides):
    result = evaluate_candidate_policy(candidate(**overrides))
    assert result.action == "exclude"
