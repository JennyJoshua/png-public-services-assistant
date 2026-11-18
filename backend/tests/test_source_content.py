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


def test_fetch_one_stops_when_download_exceeds_configured_byte_limit(monkeypatch):
    from app import source_content

    source = SOURCES[0]
    monkeypatch.setattr(source_content, "MAX_DOWNLOAD_BYTES", 100)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            request=request,
            headers={"content-type": "text/html"},
            content=b"<html><body>" + (b"x" * 300) + b"</body></html>",
        )

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await _fetch_one(client, source)

    page, status = asyncio.run(run())
    assert page is None
    assert status["fetch_succeeded"] is True
    assert status["usable_text"] is False
    assert "100 byte source limit" in status["error"]


def test_refresh_failure_preserves_last_good_in_memory_copy(monkeypatch):
    from app import source_content

    source = SOURCES[0]
    old_page = {
        "institution": source.institution,
        "agency": source.institution,
        "title": "Previously fetched page",
        "topic": source.title,
        "url": source.url,
        "final_url": source.url,
        "content_type": "text/html",
        "publication_date": None,
        "last_checked_at": "2026-11-16T00:00:00+00:00",
        "text": "Previously fetched official service text that remains usable.",
    }
    monkeypatch.setattr(source_content, "SOURCES", (source,))
    monkeypatch.setattr(source_content, "_LAST_REFRESH", None)
    monkeypatch.setitem(source_content._CACHE, source.url, old_page)
    monkeypatch.setitem(source_content._STATUS, source.url, {
        "url": source.url,
        "agency": source.institution,
        "topic": source.title,
        "last_attempt_at": None,
        "last_success_at": old_page["last_checked_at"],
        "http_status": 200,
        "final_url": source.url,
        "fetch_succeeded": True,
        "usable_text": True,
        "text_chars": len(old_page["text"]),
        "cached": True,
        "error": None,
    })
    original_client = httpx.AsyncClient

    def failing_client(*args, **kwargs):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, request=request)
        kwargs["transport"] = httpx.MockTransport(handler)
        return original_client(*args, **kwargs)

    monkeypatch.setattr(source_content.httpx, "AsyncClient", failing_client)
    result = asyncio.run(source_content.refresh_sources())
    status = source_content.get_sources_status()["sources"][0]

    assert result["successful"] == 0
    assert source_content._CACHE[source.url]["text"] == old_page["text"]
    assert status["cached"] is True
    assert status["fetch_succeeded"] is False
    assert status["last_success_at"] == old_page["last_checked_at"]
    assert status["error"] == "HTTP 503"

 
def test_html_extraction_rejects_javascript_only_application_shell():
    html = b"<html><body><main>You need to enable JavaScript to run this app.</main></body></html>"
    text, _ = _extract_html(html)
    assert text == ""



def test_refresh_detects_content_change_and_keeps_previous_good_copy(monkeypatch):
    from app import source_content

    source = SOURCES[0]
    old_text = "Previously fetched official service information that is still current."
    new_text = "Updated official service information requiring human review before use."
    old_page = {
        "institution": source.institution,
        "agency": source.institution,
        "title": "Old title",
        "topic": source.title,
        "url": source.url,
        "final_url": source.url,
        "content_type": "text/html",
        "publication_date": None,
        "last_checked_at": "2026-11-17T00:00:00+00:00",
        "text": old_text,
        "content_hash": __import__("hashlib").sha256(old_text.encode()).hexdigest(),
    }
    new_page = {**old_page, "title": "New title", "text": new_text,
                "content_hash": __import__("hashlib").sha256(new_text.encode()).hexdigest()}
    status = {"url": source.url, "review_required": False, "change_detected_at": None}
    monkeypatch.setattr(source_content, "SOURCES", (source,))
    monkeypatch.setattr(source_content, "_LAST_REFRESH", None)
    monkeypatch.setitem(source_content._CACHE, source.url, old_page)
    monkeypatch.setitem(source_content._STATUS, source.url, status)

    async def fake_fetch(client, item):
        return new_page, {"last_success_at": "2026-11-18T00:00:00+00:00",
                          "fetch_succeeded": True, "usable_text": True, "error": None}

    monkeypatch.setattr(source_content, "_fetch_one", fake_fetch)

    async def fake_client_context():
        pass

    class FakeClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            return False

    original_client = source_content.httpx.AsyncClient
    monkeypatch.setattr(source_content.httpx, "AsyncClient", lambda **kwargs: FakeClient())
    result = asyncio.run(source_content.refresh_sources())

    current_status = source_content.get_sources_status()["sources"][0]
    assert result["successful"] == 1
    assert source_content._CACHE[source.url]["text"] == old_text
    assert source_content._PENDING_CHANGES[source.url]["text"] == new_text
    assert current_status["review_required"] is True
    assert current_status["content_changed"] is True
    assert current_status["candidate_content_hash"] == new_page["content_hash"]
    monkeypatch.setattr(source_content.httpx, "AsyncClient", original_client)


def test_change_review_gate_is_not_cleared_by_same_old_content(monkeypatch):
    from app import source_content

    source = SOURCES[0]
    old_text = "Previously fetched official service information that is still current."
    old_hash = __import__("hashlib").sha256(old_text.encode()).hexdigest()
    old_page = {"url": source.url, "text": old_text, "content_hash": old_hash}
    monkeypatch.setattr(source_content, "SOURCES", (source,))
    monkeypatch.setitem(source_content._CACHE, source.url, old_page)
    monkeypatch.setitem(source_content._STATUS, source.url, {
        "url": source.url, "review_required": True,
        "candidate_content_hash": "a" * 64,
        "change_detected_at": "2026-11-18T00:00:00+00:00",
    })

    async def fake_fetch(client, item):
        return {**old_page, "last_checked_at": "2026-11-18T01:00:00+00:00"}, {
            "last_success_at": "2026-11-18T01:00:00+00:00",
            "fetch_succeeded": True, "usable_text": True, "error": None,
        }

    monkeypatch.setattr(source_content, "_fetch_one", fake_fetch)

    class FakeClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            return False

    monkeypatch.setattr(source_content.httpx, "AsyncClient", lambda **kwargs: FakeClient())
    asyncio.run(source_content.refresh_sources())
    current_status = source_content.get_sources_status()["sources"][0]
    assert current_status["review_required"] is True
    assert current_status["candidate_content_hash"] == "a" * 64
