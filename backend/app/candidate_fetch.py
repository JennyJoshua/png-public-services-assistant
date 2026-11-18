"""Bounded, policy-aware retrieval of untrusted web discovery candidates.

Candidate pages are never added to the approved source registry or answer cache.
"""
from __future__ import annotations

import asyncio
import ipaddress
import socket
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

USER_AGENT = "PNGPublicServicesAssistant/1.0 (+https://github.com/JennyJoshua/png-public-services-assistant)"
MAX_CANDIDATES = 5
MAX_CONCURRENCY = 2
MAX_REDIRECTS = 3
MAX_DOWNLOAD_BYTES = 1_000_000
MAX_ROBOTS_BYTES = 256_000
MAX_TEXT_CHARS = 12_000
REQUEST_TIMEOUT = httpx.Timeout(8.0, connect=4.0)
REDIRECT_CODES = {301, 302, 303, 307, 308}
ACCEPTED_CONTENT_TYPES = {"text/html", "application/xhtml+xml"}


class CandidateFetchError(ValueError):
    """Candidate URL or response failed a retrieval safety/policy check."""


def _normalise_candidate_url(url: str) -> str:
    if not isinstance(url, str) or not url.strip():
        raise CandidateFetchError("Candidate URL is missing.")
    parsed = urlsplit(url.strip())
    if (
        parsed.scheme.lower() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or parsed.port not in (None, 443)
    ):
        raise CandidateFetchError("Candidate URL must be a clean HTTPS URL on the standard port.")
    host = parsed.hostname.rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith((".localhost", ".local", ".internal")):
        raise CandidateFetchError("Candidate hostname is not publicly routable.")
    try:
        literal_ip = ipaddress.ip_address(host)
    except ValueError:
        literal_ip = None
    if literal_ip is not None and not literal_ip.is_global:
        raise CandidateFetchError("Candidate IP address is not globally routable.")
    return parsed._replace(fragment="").geturl()


async def _resolve_public_host(host: str, port: int = 443) -> None:
    """Reject DNS answers containing private, local, reserved or non-global IPs."""
    try:
        records = await asyncio.to_thread(
            socket.getaddrinfo, host, port, type=socket.SOCK_STREAM
        )
    except OSError as exc:
        raise CandidateFetchError("Candidate hostname could not be resolved.") from exc
    addresses = {record[4][0].split("%", 1)[0] for record in records}
    if not addresses:
        raise CandidateFetchError("Candidate hostname has no address records.")
    for address in addresses:
        try:
            parsed = ipaddress.ip_address(address)
        except ValueError as exc:
            raise CandidateFetchError("Candidate DNS returned an invalid address.") from exc
        if not parsed.is_global:
            raise CandidateFetchError("Candidate DNS resolved to a non-public IP address.")


async def _check_robots(client: httpx.AsyncClient, page_url: str) -> None:
    parsed = urlsplit(page_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    await _resolve_public_host(parsed.hostname or "")
    try:
        async with client.stream("GET", robots_url, follow_redirects=False) as response:
            if response.status_code == 404:
                return
            if response.status_code != 200:
                raise CandidateFetchError("Robots policy could not be confirmed; candidate fetch blocked.")
            raw = bytearray()
            async for chunk in response.aiter_bytes():
                raw.extend(chunk)
                if len(raw) > MAX_ROBOTS_BYTES:
                    raise CandidateFetchError("Robots policy file exceeds the safety limit; candidate fetch blocked.")
    except httpx.HTTPError as exc:
        raise CandidateFetchError("Robots policy could not be checked; candidate fetch blocked.") from exc
    parser = RobotFileParser()
    parser.set_url(robots_url)
    parser.parse(bytes(raw).decode("utf-8", errors="replace").splitlines())
    if not parser.can_fetch(USER_AGENT, page_url):
        raise CandidateFetchError("Candidate page is disallowed by robots.txt.")
async def _fetch_one_candidate(client: httpx.AsyncClient, candidate: dict) -> dict:
    try:
        original_url = _normalise_candidate_url(candidate.get("url", ""))
        current_url = original_url
        robots_checked: set[str] = set()
        for redirect_count in range(MAX_REDIRECTS + 1):
            parsed = urlsplit(current_url)
            host = parsed.hostname or ""
            await _resolve_public_host(host)
            origin = f"{parsed.scheme}://{parsed.netloc}"
            if origin not in robots_checked:
                await _check_robots(client, current_url)
                robots_checked.add(origin)
            async with client.stream(
                "GET",
                current_url,
                follow_redirects=False,
                headers={"Accept": "text/html,application/xhtml+xml"},
            ) as response:
                if response.status_code in REDIRECT_CODES:
                    if redirect_count >= MAX_REDIRECTS:
                        raise CandidateFetchError("Candidate exceeded the redirect limit.")
                    location = response.headers.get("location")
                    if not location:
                        raise CandidateFetchError("Candidate redirect has no location.")
                    next_url = _normalise_candidate_url(urljoin(current_url, location))
                    current_url = next_url
                    continue
                if response.status_code != 200:
                    raise CandidateFetchError(f"Candidate returned HTTP {response.status_code}.")
                content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                if content_type not in ACCEPTED_CONTENT_TYPES:
                    raise CandidateFetchError("Candidate content type is not supported HTML.")
                content_length = response.headers.get("content-length")
                if content_length:
                    try:
                        if int(content_length) > MAX_DOWNLOAD_BYTES:
                            raise CandidateFetchError("Candidate exceeds the download-size limit.")
                    except ValueError as exc:
                        raise CandidateFetchError("Candidate has an invalid content-length header.") from exc
                raw = bytearray()
                async for chunk in response.aiter_bytes():
                    raw.extend(chunk)
                    if len(raw) > MAX_DOWNLOAD_BYTES:
                        raise CandidateFetchError("Candidate exceeds the download-size limit.")
            text, page_title = _extract_candidate_html(bytes(raw))
            if len(text) < 80:
                raise CandidateFetchError("Candidate page contains insufficient extractable text.")
            return {
                "title": page_title or str(candidate.get("title") or "Untitled candidate")[:200],
                "url": original_url,
                "final_url": current_url,
                "domain": host,
                "provider": str(candidate.get("provider") or "unspecified")[:80],
                "rank": candidate.get("rank"),
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "content_type": content_type,
                "text": text,
                "status": "candidate_unreviewed",
                "evidence_class": None,
                "approved": False,
            }
        raise CandidateFetchError("Candidate redirect limit reached.")
    except (CandidateFetchError, httpx.HTTPError, ValueError) as exc:
        return {
            "url": str(candidate.get("url", ""))[:500],
            "status": "unavailable",
            "approved": False,
            "evidence_class": None,
            "error": str(exc)[:240],
        }

