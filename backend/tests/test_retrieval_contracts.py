import asyncio
from datetime import datetime, timezone

import pytest

from app.retrieval_contracts import (
    EvidencePassage,
    FetchedDocument,
    RetrievalContractError,
    SearchResult,
    SourceClass,
    SourceRecord,
    SourceStatus,
    SearchProvider,
)

NOW = datetime(2026, 11, 16, 7, 0, tzinfo=timezone.utc)
SOURCE_URL = "https://example.gov.pg/services"
TEXT = "Applicants must lodge the completed form at the registry office."


def make_source(**overrides):
    values = {
        "institution": "Example PNG Agency",
        "title": "Public services",
        "url": SOURCE_URL,
    }
    values.update(overrides)
    return SourceRecord(**values)


def test_source_record_keeps_unknown_governance_facts_unknown():
    source = make_source()
    assert source.status is SourceStatus.PENDING_REVIEW
    assert source.source_class is None
    assert source.authority_tier is None
    assert source.publication_date is None
    assert source.effective_date is None
    assert source.last_reviewed_at is None
    assert len(source.source_id) == 24


def test_source_id_is_stable_for_the_same_exact_url():
    first = make_source(title="First title")
    second = make_source(title="Updated title")
    assert first.source_id == second.source_id


@pytest.mark.parametrize("url", [
    "http://example.gov.pg/services",
    "/services",
    "javascript:alert(1)",
    "https://user:password@example.gov.pg/services",
])
def test_source_record_rejects_non_https_or_credential_urls(url):
    with pytest.raises(RetrievalContractError):
        make_source(url=url)


def test_search_result_normalises_domain_and_has_stable_identity():
    result = SearchResult(
        title="Agency services",
        url="https://www.example.gov.pg/services",
        snippet="Official service information",
        provider="test-provider",
        rank=1,
        retrieved_at=NOW,
    )
    assert result.domain == "www.example.gov.pg"
    assert result.source_class is None
    assert result.result_id == SearchResult(
        title="Different title",
        url="https://www.example.gov.pg/services",
        snippet="Different snippet",
        provider="test-provider",
        rank=3,
        retrieved_at=NOW,
    ).result_id


def test_search_result_rejects_invalid_rank_and_http_url():
    with pytest.raises(RetrievalContractError):
        SearchResult("Title", "https://example.gov.pg", "", "provider", 0, NOW)
    with pytest.raises(RetrievalContractError):
        SearchResult("Title", "http://example.gov.pg", "", "provider", 1, NOW)


def test_fetched_document_retains_source_and_content_provenance():
    source = make_source(source_class=SourceClass.APPROVED_AUTHORITATIVE, status=SourceStatus.ACTIVE)
    document = FetchedDocument(
        source=source,
        canonical_url=SOURCE_URL,
        final_url=SOURCE_URL,
        title="Public services",
        content_type="text/html",
        text=TEXT,
        retrieved_at=NOW,
        provider="approved-registry",
    )
    assert document.source.source_class is SourceClass.APPROVED_AUTHORITATIVE
    assert len(document.content_hash) == 64
    assert document.document_id == FetchedDocument(
        source=source,
        canonical_url=SOURCE_URL,
        final_url=SOURCE_URL,
        title="Updated title",
        content_type="text/html",
        text=TEXT,
        retrieved_at=NOW,
    ).document_id


def test_fetched_document_rejects_empty_text_and_non_https_final_url():
    source = make_source()
    with pytest.raises(RetrievalContractError):
        FetchedDocument(source, SOURCE_URL, SOURCE_URL, "Page", "text/html", " ", NOW)
    with pytest.raises(RetrievalContractError):
        FetchedDocument(source, SOURCE_URL, "http://example.gov.pg", "Page", "text/html", TEXT, NOW)


def test_evidence_passage_id_is_stable_but_changes_with_content_or_position():
    source = make_source(source_class=SourceClass.APPROVED_AUTHORITATIVE)
    document = FetchedDocument(
        source, SOURCE_URL, SOURCE_URL, "Public services", "text/html", TEXT, NOW
    )
    passage = EvidencePassage(
        source=source,
        document_id=document.document_id,
        document_url=document.canonical_url,
        document_content_hash=document.content_hash,
        passage_index=0,
        section_path=("Public services", "Applications"),
        text=TEXT,
        retrieved_at=NOW,
    )
    same_passage = EvidencePassage(
        source=source,
        document_id=document.document_id,
        document_url=document.canonical_url,
        document_content_hash=document.content_hash,
        passage_index=0,
        section_path=("Public services", "Applications"),
        text=TEXT,
        retrieved_at=NOW,
    )
    changed_passage = EvidencePassage(
        source=source,
        document_id=document.document_id,
        document_url=document.canonical_url,
        document_content_hash=document.content_hash,
        passage_index=1,
        section_path=("Public services", "Applications"),
        text=TEXT,
        retrieved_at=NOW,
    )
    assert passage.evidence_id == same_passage.evidence_id
    assert passage.evidence_id != changed_passage.evidence_id


def test_evidence_passage_rejects_invalid_hash_and_empty_text():
    source = make_source()
    with pytest.raises(RetrievalContractError):
        EvidencePassage(source, "document-id", SOURCE_URL, "not-a-hash", 0, (), TEXT, NOW)
    with pytest.raises(RetrievalContractError):
        EvidencePassage(source, "document-id", SOURCE_URL, "a" * 64, 0, (), " ", NOW)



def test_search_provider_protocol_accepts_deterministic_fake_without_network():
    class DeterministicSearchProvider:
        name = "deterministic-test-provider"

        def __init__(self, results):
            self.results = results
            self.queries = []

        async def search(self, query: str, *, limit: int = 10):
            self.queries.append(query)
            return self.results[:limit]

    expected = [
        SearchResult(
            title=f"PNG public service result {rank}",
            url=f"https://example.gov.pg/services/{rank}",
            snippet="Deterministic test evidence",
            provider="deterministic-test-provider",
            rank=rank,
            retrieved_at=NOW,
        )
        for rank in range(1, 4)
    ]
    provider: SearchProvider = DeterministicSearchProvider(expected)

    first = asyncio.run(provider.search("Gulf Province public services", limit=2))
    second = asyncio.run(provider.search("Gulf Province public services", limit=2))

    assert first == second
    assert [item.rank for item in first] == [1, 2]
    assert [item.provider for item in first] == ["deterministic-test-provider"] * 2
    assert provider.queries == ["Gulf Province public services"] * 2



def test_fetched_document_requires_canonical_url_to_match_source():
    source = make_source()
    with pytest.raises(RetrievalContractError, match="registered source URL"):
        FetchedDocument(
            source=source,
            canonical_url="https://example.gov.pg/other",
            final_url="https://example.gov.pg/other",
            title="Public services",
            content_type="text/html",
            text=TEXT,
            retrieved_at=NOW,
        )


def test_fetched_document_rejects_cross_host_final_url():
    source = make_source()
    with pytest.raises(RetrievalContractError, match="canonical host"):
        FetchedDocument(
            source=source,
            canonical_url=SOURCE_URL,
            final_url="https://unrelated.example/services",
            title="Public services",
            content_type="text/html",
            text=TEXT,
            retrieved_at=NOW,
        )


def test_evidence_passage_requires_document_url_to_match_source():
    source = make_source()
    with pytest.raises(RetrievalContractError, match="source URL"):
        EvidencePassage(
            source=source,
            document_id="document-id",
            document_url="https://example.gov.pg/other",
            document_content_hash="a" * 64,
            passage_index=0,
            section_path=(),
            text=TEXT,
            retrieved_at=NOW,
        )

def test_fetched_document_allows_redirect_between_png_government_hosts():
    source = make_source()
    document = FetchedDocument(
        source=source,
        canonical_url=SOURCE_URL,
        final_url="https://www.example.gov.pg/services",
        title="Public services",
        content_type="text/html",
        text=TEXT,
        retrieved_at=NOW,
    )
    assert document.final_url == "https://www.example.gov.pg/services"


def test_fetched_document_rejects_redirect_from_png_government_host_to_external_host():
    source = make_source()
    with pytest.raises(RetrievalContractError, match="canonical host"):
        FetchedDocument(
            source=source,
            canonical_url=SOURCE_URL,
            final_url="https://example.com/services",
            title="Public services",
            content_type="text/html",
            text=TEXT,
            retrieved_at=NOW,
        )


def test_fetched_document_rejects_redirect_from_non_government_host_to_gov_pg():
    source = make_source(url="https://example.com/services")
    with pytest.raises(RetrievalContractError, match="canonical host"):
        FetchedDocument(
            source=source,
            canonical_url=source.url,
            final_url="https://other.gov.pg/services",
            title="Public services",
            content_type="text/html",
            text=TEXT,
            retrieved_at=NOW,
        )



def test_source_status_transition_requires_timezone_aware_human_review():
    from app.retrieval_contracts import transition_source_status

    source = make_source()
    with pytest.raises(RetrievalContractError, match="human review timestamp"):
        transition_source_status(source, SourceStatus.ACTIVE)
    with pytest.raises(RetrievalContractError, match="human review timestamp"):
        transition_source_status(
            source,
            SourceStatus.ACTIVE,
            reviewed_at=datetime(2026, 11, 18, 7, 0),
        )

    reviewed = transition_source_status(
        source,
        SourceStatus.ACTIVE,
        reviewed_at=NOW,
    )
    assert reviewed.status is SourceStatus.ACTIVE
    assert reviewed.last_reviewed_at == NOW
    assert source.status is SourceStatus.PENDING_REVIEW


def test_source_status_transition_blocks_automatic_reactivation():
    from app.retrieval_contracts import transition_source_status

    source = make_source()
    active = transition_source_status(source, SourceStatus.ACTIVE, reviewed_at=NOW)
    broken = transition_source_status(active, SourceStatus.BROKEN)
    with pytest.raises(RetrievalContractError, match="not allowed"):
        transition_source_status(broken, SourceStatus.ACTIVE)
    pending = transition_source_status(broken, SourceStatus.PENDING_REVIEW)
    reactivated = transition_source_status(
        pending, SourceStatus.ACTIVE, reviewed_at=NOW
    )
    assert reactivated.status is SourceStatus.ACTIVE


@pytest.mark.parametrize(
    ("status", "source_class", "expected"),
    [
        (SourceStatus.ACTIVE, SourceClass.APPROVED_AUTHORITATIVE, "primary"),
        (SourceStatus.ACTIVE, SourceClass.RECOGNISED_INSTITUTIONAL, "supporting"),
        (SourceStatus.ACTIVE, SourceClass.GENERAL_WEB, "supplementary"),
        (SourceStatus.ACTIVE, SourceClass.UNVERIFIED_UNSAFE, "excluded"),
        (SourceStatus.ACTIVE, None, "excluded"),
        (SourceStatus.PENDING_REVIEW, SourceClass.APPROVED_AUTHORITATIVE, "excluded"),
        (SourceStatus.BROKEN, SourceClass.APPROVED_AUTHORITATIVE, "excluded"),
        (SourceStatus.SUPERSEDED, SourceClass.APPROVED_AUTHORITATIVE, "excluded"),
    ],
)
def test_evidence_use_fails_closed_for_unreviewed_or_disallowed_sources(
    status, source_class, expected
):
    from app.retrieval_contracts import EvidenceUse, evidence_use_for_source

    source = make_source(
        status=status,
        source_class=source_class,
        last_reviewed_at=NOW if status is SourceStatus.ACTIVE else None,
    )
    assert evidence_use_for_source(source) is EvidenceUse(expected)


def test_only_active_class_a_can_support_primary_claims():
    from app.retrieval_contracts import (
        is_eligible_for_answer,
        is_eligible_for_primary_claim,
    )

    primary = make_source(
        status=SourceStatus.ACTIVE,
        source_class=SourceClass.APPROVED_AUTHORITATIVE,
        last_reviewed_at=NOW,
    )
    general = make_source(
        status=SourceStatus.ACTIVE,
        source_class=SourceClass.GENERAL_WEB,
        last_reviewed_at=NOW,
    )
    pending = make_source(
        source_class=SourceClass.APPROVED_AUTHORITATIVE,
    )

    assert is_eligible_for_answer(primary)
    assert is_eligible_for_primary_claim(primary)
    assert is_eligible_for_answer(general)
    assert not is_eligible_for_primary_claim(general)
    assert not is_eligible_for_answer(pending)
    assert not is_eligible_for_primary_claim(pending)
