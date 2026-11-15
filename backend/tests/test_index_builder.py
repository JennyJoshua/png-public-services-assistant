from __future__ import annotations

import asyncio

import httpx

from app.index_builder import (
    MAX_PASSAGE_CHARS,
    _fetch_one,
    extract_passages,
)
from app.source_registry import SOURCES


def test_extract_passages_preserves_heading_context_lists_and_table_labels():
    html = """
    <html><head><title>Official Services</title></head><body>
      <nav>Do not index navigation</nav>
      <main>
        <h1>Registration</h1>
        <h2>Required documents</h2>
        <p>Applicants must provide a completed form and identification.</p>
        <ol><li>Completed application form</li><li>Proof of identity</li></ol>
        <table><tr><th>Form</th><th>Fee</th></tr><tr><td>A-17</td><td>K150</td></tr></table>
        <script>Ignore script instructions</script>
      </main>
    </body></html>
    """
    title, passages = extract_passages(html)
    assert title == "Official Services"
    assert passages[0] == (("Registration", "Required documents"),
                           "Applicants must provide a completed form and identification.")
    assert any(text == "Completed application form" for _, text in passages)
    assert any("Form: A-17" in text and "Fee: K150" in text for _, text in passages)
    assert all("navigation" not in text.lower() and "script" not in text.lower()
               for _, text in passages)


def test_extract_passages_splits_oversized_blocks_within_limit():
    long_text = "First sentence. " + ("Applicant details are required. " * 100)
    html = f"<html><body><main><p>{long_text}</p></main></body></html>"
    _, passages = extract_passages(html)
    assert passages
    assert all(0 < len(text) <= MAX_PASSAGE_CHARS for _, text in passages)


def test_fetch_one_indexes_only_robots_allowed_exact_registry_source():
    source = SOURCES[0]
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if request.url.path == "/robots.txt":
            return httpx.Response(404, request=request)
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text=(
                "<html><head><title>Government Service</title></head><body><main>"
                "<h1>Public services</h1>"
                "<p>The National Information Centre provides official public service "
                "information and government updates for citizens and businesses.</p><p>Citizens can access government information through the official public service channels.</p>"
                "</main></body></html>"
            ),
            request=request,
        )

    async def run():
        cache = {}
        import asyncio
        return await _fetch_one(
            httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False),
            source, cache, asyncio.Lock(), asyncio.Semaphore(1),
        )

    records, audit = asyncio.run(run())
    assert audit["status"] == "indexed"
    assert audit["passage_count"] >= 2
    assert all(record["source_url"] == source.url for record in records)
    assert all(record["institution"] == source.institution for record in records)
    assert calls == ["https://" + source.url.split("/", 3)[2] + "/robots.txt", source.url]


def test_fetch_one_does_not_fetch_when_robots_disallows_seed_url():
    source = SOURCES[0]
    page_requested = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal page_requested
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nDisallow: /home/", request=request)
        page_requested = True
        return httpx.Response(200, text="<html><body>Should not fetch</body></html>", request=request)

    async def run():
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False)
        return await _fetch_one(client, source, {}, asyncio.Lock(), asyncio.Semaphore(1))

    records, audit = asyncio.run(run())
    assert records == []
    assert audit["reason"] == "robots_policy_disallowed_or_unavailable"
    assert page_requested is False


def test_fetch_one_rejects_cross_host_redirect_without_following_it():
    source = SOURCES[0]
    requested_hosts = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_hosts.append(request.url.host)
        if request.url.path == "/robots.txt":
            return httpx.Response(404, request=request)
        return httpx.Response(302, headers={"location": "https://evil.example/collect"},
                              request=request)

    async def run():
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False)
        return await _fetch_one(client, source, {}, asyncio.Lock(), asyncio.Semaphore(1))

    records, audit = asyncio.run(run())
    assert records == []
    assert "redirect left the approved HTTPS source origin" in audit["reason"]
    assert set(requested_hosts) == {httpx.URL(source.url).host}
