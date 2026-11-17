"""Bounded HTML/PDF fetching with an in-memory cache and per-source status."""
from __future__ import annotations

import asyncio
import io
import logging
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader

from app.source_registry import SOURCES

logger = logging.getLogger(__name__)

REFRESH_SECONDS = 24 * 60 * 60
MAX_DOWNLOAD_BYTES = 5_000_000
MAX_TEXT_CHARS = 24_000
MAX_PDF_PAGES = 80
MAX_CONTEXT_CHARS = 14_000
MAX_CONTEXT_PAGES = 6
USER_AGENT = "PNGPublicServicesAssistant/1.0 (+https://github.com/JennyJoshua/png-public-services-assistant)"

_CACHE: dict[str, dict] = {}
_STATUS: dict[str, dict] = {
    source.url: {
        "url": source.url,
        "agency": source.institution,
        "topic": source.title,
        "last_attempt_at": None,
        "last_success_at": None,
        "http_status": None,
        "final_url": None,
        "fetch_succeeded": False,
        "usable_text": False,
        "text_chars": 0,
        "cached": False,
        "error": "Not fetched yet",
    }
    for source in SOURCES
}
_LAST_REFRESH: datetime | None = None
_REFRESH_LOCK = asyncio.Lock()


def _clean_text(value: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in value.splitlines()]
    return "\n".join(line for line in lines if line)[:MAX_TEXT_CHARS]


def _extract_html(raw: bytes) -> tuple[str, str]:
    soup = BeautifulSoup(raw, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    for element in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript", "svg"]):
        element.decompose()
    main = soup.find("main") or soup.find("article") or soup.body or soup
    blocks: list[str] = []
    for element in main.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "dt", "dd", "tr"]):
        if element.name == "p" and element.find_parent("li"):
            continue
        if element.name == "tr":
            cells = element.find_all(["th", "td"], recursive=False)
            if not cells or all(cell.name == "th" for cell in cells):
                continue
            table = element.find_parent("table")
            header = table.find("tr") if table else None
            headings = [cell.get_text(" ", strip=True) for cell in header.find_all(["th", "td"], recursive=False)] if header else []
            values = [cell.get_text(" ", strip=True) for cell in cells]
            text = " | ".join(f"{heading}: {value}" for heading, value in zip(headings, values)) if headings and len(headings) == len(values) else " | ".join(values)
        else:
            text = element.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()
        if text and (not blocks or text != blocks[-1]):
            blocks.append(text)
        if sum(len(item) + 1 for item in blocks) >= MAX_TEXT_CHARS:
            break
    if not blocks:
        blocks = [main.get_text(" ", strip=True)]
    return _clean_text("\n".join(blocks)), title


def _extract_pdf(raw: bytes) -> tuple[str, str]:
    reader = PdfReader(io.BytesIO(raw), strict=False)
    pages: list[str] = []
    for page in reader.pages[:MAX_PDF_PAGES]:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text)
        if sum(len(item) for item in pages) >= MAX_TEXT_CHARS:
            break
    return _clean_text("\n".join(pages)), "PDF document"


def _redirect_is_allowed(original_url: str, final_url: str) -> bool:
    original = urlparse(original_url)
    final = urlparse(final_url)
    original_host = (original.hostname or "").lower()
    final_host = (final.hostname or "").lower()
    return (
        final.scheme == "https"
        and bool(final_host)
        and (final_host == original_host or final_host.endswith(".gov.pg"))
        and (original_host.endswith(".gov.pg") or final_host == original_host)
    )


async def _fetch_one(client: httpx.AsyncClient, source) -> tuple[dict | None, dict]:
    attempted_at = datetime.now(timezone.utc).isoformat()
    status = dict(_STATUS[source.url])
    status.update({"last_attempt_at": attempted_at, "fetch_succeeded": False, "usable_text": False, "text_chars": 0, "error": None})
    try:
        response = await client.get(source.url)
        status["http_status"] = response.status_code
        status["final_url"] = str(response.url)
        if response.status_code != 200:
            raise ValueError(f"HTTP {response.status_code}")
        status["fetch_succeeded"] = True
        if not _redirect_is_allowed(source.url, str(response.url)):
            raise ValueError("Redirect destination is outside the approved HTTPS government domain")
        if len(response.content) > MAX_DOWNLOAD_BYTES:
            raise ValueError("Download exceeded the 5 MB source limit")
        content_type = response.headers.get("content-type", "").lower()
        is_pdf = "application/pdf" in content_type or urlparse(str(response.url)).path.lower().endswith(".pdf")
        if is_pdf:
            text, title = _extract_pdf(response.content)
        elif "text/html" in content_type or "application/xhtml" in content_type:
            text, title = _extract_html(response.content)
        else:
            raise ValueError(f"Unsupported content type: {content_type or 'missing'}")
        if len(text) < 40:
            raise ValueError("Page fetched but no usable text could be extracted")
        fetched_at = datetime.now(timezone.utc).isoformat()
        page = {
            "institution": source.institution,
            "agency": source.institution,
            "title": title or source.title,
            "topic": source.title,
            "url": source.url,
            "final_url": str(response.url),
            "content_type": content_type,
            "publication_date": None,
            "last_checked_at": fetched_at,
            "text": text,
        }
        status.update({
            "last_success_at": fetched_at,
            "fetch_succeeded": True,
            "usable_text": True,
            "text_chars": len(text),
            "cached": True,
            "error": None,
        })
        return page, status
    except Exception as exc:
        status.update({
            "usable_text": False,
            "text_chars": 0,
            "cached": source.url in _CACHE,
            "error": str(exc)[:240],
        })
        logger.warning("Source fetch failed for %s: %s", source.url, exc)
        return None, status


async def refresh_sources(*, force: bool = True) -> dict:
    """Fetch all configured URLs; retain the previous good copy when refresh fails."""
    global _LAST_REFRESH
    async with _REFRESH_LOCK:
        now = datetime.now(timezone.utc)
        if not force and _LAST_REFRESH and now - _LAST_REFRESH < timedelta(seconds=REFRESH_SECONDS):
            return {"refreshed": False, "reason": "cache is still fresh"}
        timeout = httpx.Timeout(12.0, connect=5.0)
        headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.5"}
        async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True, max_redirects=5) as client:
            results = await asyncio.gather(*(_fetch_one(client, source) for source in SOURCES))
        successes = 0
        for source, (page, status) in zip(SOURCES, results):
            if page is not None:
                _CACHE[source.url] = page
                successes += 1
            status["cached"] = source.url in _CACHE
            _STATUS[source.url] = status
        _LAST_REFRESH = now
        return {"refreshed": True, "sources": len(SOURCES), "successful": successes, "cached": len(_CACHE)}


async def get_source_pages() -> list[dict]:
    if _LAST_REFRESH is None:
        await refresh_sources()
    elif datetime.now(timezone.utc) - _LAST_REFRESH >= timedelta(seconds=REFRESH_SECONDS):
        await refresh_sources(force=False)
    return list(_CACHE.values())


async def refresh_loop() -> None:
    """Best-effort periodic refresh; startup refresh also runs after Render wake-up."""
    while True:
        await asyncio.sleep(REFRESH_SECONDS)
        await refresh_sources(force=True)


def get_sources_status() -> dict:
    return {
        "last_refresh_at": _LAST_REFRESH.isoformat() if _LAST_REFRESH else None,
        "refresh_interval_hours": 24,
        "cache_storage": "memory_only",
        "sources": [dict(_STATUS[source.url]) for source in SOURCES],
    }


def assemble_sources_block(pages: list[dict], selected_urls: list[str]) -> str:
    """Build the prompt's labelled SOURCES block, bounded to relevant cached pages."""
    by_url = {page["url"]: page for page in pages}
    chunks: list[str] = []
    remaining = MAX_CONTEXT_CHARS
    for url in selected_urls:
        page = by_url.get(url)
        if not page or remaining <= 0 or len(chunks) >= MAX_CONTEXT_PAGES:
            continue
        fetched = str(page.get("last_checked_at", ""))[:10] or "unknown"
        header = f"PAGE: {url} | AGENCY: {page.get('agency', page.get('institution', 'Unknown'))} | FETCHED: {fetched}"
        block = f"{header}\n{page.get('text', '')}"
        if len(block) > remaining:
            if remaining <= len(header) + 80:
                break
            block = f"{header}\n{page.get('text', '')[:remaining - len(header) - 1]}"
        chunks.append(block)
        remaining -= len(block) + 2
    return "\n\n".join(chunks) or "No relevant source text was successfully fetched for this question."
