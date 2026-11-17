import asyncio

import httpx

from app.source_content import (
    _extract_html,
    _fetch_one,
    _redirect_is_allowed,
    assemble_sources_block,
)
from app.source_registry import SOURCES


def test_html_extraction_removes_chrome_and_preserves_table_headers():
    html = b"""<html><head><title>Fees</title></head><body>
    <nav>Menu noise</nav><main><h1>Fees</h1>
    <p>Applicants may review the current fee schedule here.</p>
    <table><tr><th>Form</th><th>Fee</th></tr><tr><td>F-10</td><td>K50</td></tr></table>
    </main><footer>Footer noise</footer><script>bad script</script></body></html>"""
    text, title = _extract_html(html)
    assert title == "Fees"
    assert "Form: F-10" in text
    assert "Fee: K50" in text
    assert "Menu noise" not in text
    assert "Footer noise" not in text
    assert "bad script" not in text


def test_redirect_policy_allows_only_https_official_government_redirects():
    assert _redirect_is_allowed("https://ica.gov.pg/passport", "https://icsa.gov.pg/")
    assert _redirect_is_allowed("https://pngcir.gov.pg/", "https://pngcir.gov.pg/")
    assert not _redirect_is_allowed("https://ica.gov.pg/passport", "https://example.com/")
    assert not _redirect_is_allowed("https://ica.gov.pg/passport", "http://icsa.gov.pg/")


def test_source_context_has_url_agency_and_fetch_date_and_is_bounded():
    page = {
        "url": "https://example.gov.pg/service",
        "agency": "Example Agency",
        "last_checked_at": "2026-11-17T01:02:03+00:00",
        "text": "Official service information.",
    }
    block = assemble_sources_block([page], [page["url"]])
    assert "PAGE: https://example.gov.pg/service" in block
    assert "AGENCY: Example Agency" in block
    assert "FETCHED: 2026-11-17" in block
    assert "Official service information." in block


def test_fetch_one_returns_clean_html_and_status():
    source = SOURCES[0]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            request=request,
            headers={"content-type": "text/html; charset=utf-8"},
            content=(
                b"<html><head><title>Passport</title></head><body><main>"
                b"<h1>Passport application</h1><p>Applicants can read the official "
                b"passport application information and instructions on this page.</p>"
                b"</main></body></html>"
            ),
        )

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await _fetch_one(client, source)

    page, status = asyncio.run(run())
    assert page is not None
    assert page["institution"] == source.institution
    assert page["url"] == source.url
    assert "passport application information" in page["text"].lower()
    assert status["fetch_succeeded"] is True
    assert status["usable_text"] is True
    assert status["text_chars"] > 40


def test_fetch_one_reports_no_text_without_throwing():
    source = SOURCES[0]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, headers={"content-type": "text/html"}, text="<html><body>tiny</body></html>")

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await _fetch_one(client, source)

    page, status = asyncio.run(run())
    assert page is None
    assert status["fetch_succeeded"] is True
    assert status["usable_text"] is False
    assert "usable text" in status["error"]
