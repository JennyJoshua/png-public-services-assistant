from app.rag import _page_text, _rank_passages
from app.source_registry import SOURCES


def test_page_text_removes_navigation_and_scripts() -> None:
    html = """
    <html><head><title>Agency page</title></head><body>
      <nav>Navigation noise</nav>
      <main><p>The agency provides business registration services to applicants.</p></main>
      <script>ignore this script content</script>
    </body></html>
    """
    text, title = _page_text(html)
    assert title == "Agency page"
    assert "business registration" in text
    assert "Navigation noise" not in text
    assert "ignore this script" not in text


def test_rank_passages_returns_relevant_source_excerpt() -> None:
    pages = [{
        "institution": "Example Agency",
        "title": "Business Registration",
        "url": "https://example.gov.pg/business",
        "publication_date": None,
        "last_checked_at": "2026-11-13T00:00:00+00:00",
        "text": (
            "The Companies Office administers business registration and maintains "
            "the national register of companies and business names. "
            "The weather is usually warm during the wet season."
        ),
    }]
    results = _rank_passages("How does business registration work?", pages)
    assert results
    assert "business registration" in results[0]["text"].lower()
    assert results[0]["source"]["institution"] == "Example Agency"


def test_rank_passages_returns_empty_when_no_query_overlap() -> None:
    pages = [{
        "institution": "Example Agency",
        "title": "Page",
        "url": "https://example.gov.pg/",
        "publication_date": None,
        "last_checked_at": "2026-11-13T00:00:00+00:00",
        "text": "The department publishes annual statistics about rainfall patterns.",
    }]
    assert _rank_passages("How can I renew a passport?", pages) == []


def test_pngcir_is_an_explicit_curated_source_set() -> None:
    pngcir_urls = {source.url for source in SOURCES if source.institution == "Papua New Guinea Civil and Identity Registry"}
    assert pngcir_urls == {
        "https://pngcir.gov.pg/",
        "https://pngcir.gov.pg/nid-registration-information/",
        "https://pngcir.gov.pg/downloads/",
        "https://pngcir.gov.pg/png-civil-identity-registry-fees/",
        "https://pngcir.gov.pg/contact/",
    }


def test_national_id_question_ranks_official_registration_instructions() -> None:
    pages = [{
        "institution": "Papua New Guinea Civil and Identity Registry",
        "title": "NID Registration Information",
        "url": "https://pngcir.gov.pg/nid-registration-information/",
        "publication_date": None,
        "last_checked_at": "2026-11-13T00:00:00+00:00",
        "text": (
            "Full online registration is not possible because every citizen must provide "
            "fingerprint and ID capture in person. "
            "Normal registration: Download the Registration Form, fill in the details "
            "and lodge it at your nearest Civil and Identity Registry Office. "
            "National Identity Card Information is for applicants 18 years and above only."
        ),
    }]
    results = _rank_passages("How do I apply for a National ID?", pages)
    assert results
    assert results[0]["source"]["institution"] == "Papua New Guinea Civil and Identity Registry"
    assert any("lodge it at your nearest Civil and Identity Registry Office" in item["text"] for item in results)
