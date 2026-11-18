import asyncio

import httpx
import pytest

from app import candidate_fetch


def test_candidate_url_requires_clean_https_and_standard_port():
    assert candidate_fetch._normalise_candidate_url("https://example.org/page") == "https://example.org/page"
    for url in (
        "http://example.org/page",
        "https://user:pass@example.org/page",
        "https://example.org:8443/page",
        "https://localhost/page",
        "https://127.0.0.1/page",
        "https://example.org/page#fragment",
    ):
        with pytest.raises(candidate_fetch.CandidateFetchError):
            candidate_fetch._normalise_candidate_url(url)


def test_candidate_dns_rejects_non_public_addresses(monkeypatch):
    def fake_getaddrinfo(host, port, type):
        return [(None, None, None, None, ("10.0.0.5", 443))]
    monkeypatch.setattr(candidate_fetch.socket, "getaddrinfo", fake_getaddrinfo)
    with pytest.raises(candidate_fetch.CandidateFetchError, match="non-public"):
        asyncio.run(candidate_fetch._resolve_public_host("example.org"))


def test_candidate_dns_accepts_public_addresses(monkeypatch):
    def fake_getaddrinfo(host, port, type):
        return [(None, None, None, None, ("93.184.216.34", 443))]
    monkeypatch.setattr(candidate_fetch.socket, "getaddrinfo", fake_getaddrinfo)
    asyncio.run(candidate_fetch._resolve_public_host("example.org"))


def test_candidate_html_extraction_removes_navigation_and_scripts():
    raw = b"""<html><head><title>Service Guide</title></head><body>
    <nav>Navigation noise</nav><main><h1>Service guide</h1>
    <p>Official information about how applicants can access this public service.</p>
    <p>Applicants should prepare their documents before visiting the service centre.</p>
    <script>malicious()</script></main><footer>Footer noise</footer></body></html>"""
    text, title = candidate_fetch._extract_candidate_html(raw)
    assert title == "Service Guide"
    assert "Official information" in text
    assert "Navigation noise" not in text
    assert "Footer noise" not in text
    assert "malicious()" not in text


def test_robots_policy_blocks_disallowed_candidate():
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, request=request, text="User-agent: *\nDisallow: /private")
        return httpx.Response(200, request=request, headers={"content-type": "text/html"}, text="<html></html>")

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            await candidate_fetch._check_robots(client, "https://example.org/private/page")

    async def public_dns(host, port=443):
        return None

    original = candidate_fetch._resolve_public_host
    candidate_fetch._resolve_public_host = public_dns
    try:
        with pytest.raises(candidate_fetch.CandidateFetchError, match="robots.txt"):
            asyncio.run(run())
    finally:
        candidate_fetch._resolve_public_host = original


def test_candidate_fetch_returns_unreviewed_metadata_and_never_approved(monkeypatch):
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404, request=request)
        body = ("<html><head><title>Public service</title></head><body><main>"
                "<h1>Public service</h1><p>" + ("Official service information for applicants. " * 8)
                + "</p></main></body></html>")
        return httpx.Response(200, request=request, headers={"content-type": "text/html"}, text=body)

    async def public_dns(host, port=443):
        return None

    monkeypatch.setattr(candidate_fetch, "_resolve_public_host", public_dns)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await candidate_fetch._fetch_one_candidate(
                client, {"url": "https://example.org/service", "provider": "test", "rank": 1}
            )

    result = asyncio.run(run())
    assert result["status"] == "candidate_unreviewed"
    assert result["approved"] is False
    assert result["evidence_class"] is None
    assert result["provider"] == "test"
    assert "Official service information" in result["text"]


def test_candidate_fetch_blocks_when_robots_cannot_be_checked(monkeypatch):
    def handler(request):
        return httpx.Response(503, request=request)

    async def public_dns(host, port=443):
        return None

    monkeypatch.setattr(candidate_fetch, "_resolve_public_host", public_dns)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await candidate_fetch._fetch_one_candidate(
                client, {"url": "https://example.org/service"}
            )

    result = asyncio.run(run())
    assert result["status"] == "unavailable"
    assert "Robots policy could not be confirmed" in result["error"]


def test_candidate_fetch_rejects_private_redirect(monkeypatch):
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404, request=request)
        return httpx.Response(302, request=request, headers={"location": "http://127.0.0.1/admin"})

    async def public_dns(host, port=443):
        return None

    monkeypatch.setattr(candidate_fetch, "_resolve_public_host", public_dns)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await candidate_fetch._fetch_one_candidate(
                client, {"url": "https://example.org/service"}
            )

    result = asyncio.run(run())
    assert result["status"] == "unavailable"
    assert "HTTPS" in result["error"]


def test_candidate_count_is_capped_at_five(monkeypatch):
    seen = []

    async def fake_fetch(client, candidate):
        seen.append(candidate)
        return {"url": candidate["url"], "status": "unavailable", "approved": False}

    monkeypatch.setattr(candidate_fetch, "_fetch_one_candidate", fake_fetch)

    async def run():
        return await candidate_fetch.fetch_candidate_pages(
            [{"url": f"https://example.org/{i}"} for i in range(8)]
        )

    result = asyncio.run(run())
    assert len(result) == 5
    assert len(seen) == 5


def test_candidate_fetch_preserves_provider_provenance_and_stable_identity(monkeypatch):
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404, request=request)
        body = ("<html><head><title>Fetched page title</title></head><body><main>"
                "<h1>Service guide</h1><p>" + ("Useful service information for applicants. " * 8)
                + "</p></main></body></html>")
        return httpx.Response(200, request=request, headers={"content-type": "text/html"}, text=body)

    async def public_dns(host, port=443):
        return None

    monkeypatch.setattr(candidate_fetch, "_resolve_public_host", public_dns)

    candidate = {
        "url": "https://example.org/service",
        "title": "Search provider title",
        "snippet": "Provider supplied summary",
        "provider": "example-search",
        "provider_result_id": "result-123",
        "rank": 2,
        "publication_date": "2026-10-01",
    }

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await candidate_fetch._fetch_one_candidate(client, candidate)

    first = asyncio.run(run())
    second = asyncio.run(run())
    assert first["candidate_id"] == second["candidate_id"]
    assert first["canonical_url"] == candidate["url"]
    assert first["final_url"] == candidate["url"]
    assert first["domain"] == "example.org"
    assert first["provider"] == "example-search"
    assert first["provider_result_id"] == "result-123"
    assert first["provider_title"] == "Search provider title"
    assert first["snippet"] == "Provider supplied summary"
    assert first["rank"] == 2
    assert first["publication_date"] == "2026-10-01"
    assert first["retrieved_at"]
    assert first["approved"] is False
    assert first["evidence_class"] is None


def test_candidate_fetch_does_not_trust_invalid_provider_rank(monkeypatch):
    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(404, request=request)
        body = ("<html><body><main><h1>Service guide</h1><p>"
                + ("Useful service information for applicants. " * 8)
                + "</p></main></body></html>")
        return httpx.Response(200, request=request, headers={"content-type": "text/html"}, text=body)

    async def public_dns(host, port=443):
        return None

    monkeypatch.setattr(candidate_fetch, "_resolve_public_host", public_dns)

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await candidate_fetch._fetch_one_candidate(
                client, {"url": "https://example.org/service", "rank": "first"}
            )

    result = asyncio.run(run())
    assert result["status"] == "candidate_unreviewed"
    assert result["rank"] is None
