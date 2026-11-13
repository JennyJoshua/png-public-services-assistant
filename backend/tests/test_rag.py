from app.rag import _page_text, _rank_passages


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
