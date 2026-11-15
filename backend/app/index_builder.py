"""Build a deterministic, source-backed index from the exact approved PNG seed URLs.

This module is an offline artifact builder only. It does not change live retrieval.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from app.index_artifact import build_index_artifact, document_id_for_url, source_id_for_url
from app.source_registry import SOURCES

USER_AGENT = "PNGPublicServicesAssistant/0.4 (+https://github.com/JennyJoshua/png-public-services-assistant)"
MAX_PAGE_BYTES = 1_500_000
MAX_PAGE_TEXT_CHARS = 24_000
MAX_PASSAGE_CHARS = 1_400
MAX_REDIRECTS = 4
MAX_CONCURRENCY = 3
MIN_EXTRACTED_CHARS = 80
REDIRECT_STATUSES = {301, 302, 303, 307, 308}


class IndexBuildError(ValueError):
    """Raised when a representative source index cannot be built safely."""


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _normalise_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _split_passage(text: str) -> list[str]:
    if len(text) <= MAX_PASSAGE_CHARS:
        return [text]
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    output: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > MAX_PASSAGE_CHARS:
            if current:
                output.append(current)
                current = ""
            output.extend(
                sentence[i:i + MAX_PASSAGE_CHARS].strip()
                for i in range(0, len(sentence), MAX_PASSAGE_CHARS)
                if sentence[i:i + MAX_PASSAGE_CHARS].strip()
            )
        elif current and len(current) + len(sentence) + 1 > MAX_PASSAGE_CHARS:
            output.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        output.append(current)
    return output


def extract_passages(html: str) -> tuple[str | None, list[tuple[tuple[str, ...], str]]]:
    """Extract ordered content blocks with heading context and table labels."""
    soup = BeautifulSoup(html, "html.parser")
    page_title = _normalise_text(soup.title.get_text(" ", strip=True)) if soup.title else None
    for element in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript", "svg"]):
        element.decompose()

    main = soup.find("main") or soup.find("article") or soup.body or soup
    headings: list[tuple[int, str]] = []
    passages: list[tuple[tuple[str, ...], str]] = []
    seen: set[tuple[tuple[str, ...], str]] = set()

    for element in main.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "dt", "dd", "tr"]):
        if element.name == "p" and element.find_parent("li"):
            continue
        if element.name and re.fullmatch(r"h[1-6]", element.name):
            level = int(element.name[1])
            heading = _normalise_text(element.get_text(" ", strip=True))
            if heading:
                headings = [(depth, value) for depth, value in headings if depth < level]
                headings.append((level, heading))
            continue

        if element.name == "tr":
            cells = element.find_all(["th", "td"], recursive=False)
            if not cells or all(cell.name == "th" for cell in cells):
                continue
            table = element.find_parent("table")
            header = table.find("tr") if table else None
            header_cells = header.find_all(["th", "td"], recursive=False) if header else []
            labels = [_normalise_text(cell.get_text(" ", strip=True)) for cell in header_cells]
            values = [_normalise_text(cell.get_text(" ", strip=True)) for cell in cells]
            text = " | ".join(
                f"{label}: {value}" for label, value in zip(labels, values)
            ) if labels and len(labels) == len(values) else " | ".join(values)
        else:
            text = _normalise_text(element.get_text(" ", strip=True))

        if not text:
            continue
        section_path = tuple(value for _, value in headings)
        for chunk in _split_passage(text):
            item = (section_path, chunk)
            if item not in seen:
                passages.append(item)
                seen.add(item)

    if not passages:
        fallback = _normalise_text(main.get_text(" ", strip=True))
        for chunk in _split_passage(fallback):
            if chunk:
                passages.append(((), chunk))

    bounded: list[tuple[tuple[str, ...], str]] = []
    remaining = MAX_PAGE_TEXT_CHARS
    for section_path, text in passages:
        if remaining <= 0:
            break
        clipped = text[:remaining].strip()
        if clipped:
            bounded.append((section_path, clipped))
            remaining -= len(clipped)
    return page_title, bounded


async def _get_same_host(
    client: httpx.AsyncClient, url: str, expected_host: str, *, max_bytes: int
) -> httpx.Response:
    """Follow bounded HTTPS redirects and stream no more than max_bytes."""
    current = url
    for _ in range(MAX_REDIRECTS + 1):
        parsed = urlparse(current)
        if parsed.scheme != "https" or (parsed.hostname or "").lower() != expected_host:
            raise IndexBuildError("redirect left the approved HTTPS source host")
        async with client.stream("GET", current, follow_redirects=False) as streamed:
            if streamed.status_code in REDIRECT_STATUSES:
                location = streamed.headers.get("location")
                if not location:
                    raise IndexBuildError("redirect response did not include a location")
                current = urljoin(current, location)
                continue

            body = bytearray()
            async for chunk in streamed.aiter_bytes():
                if len(body) + len(chunk) > max_bytes:
                    raise IndexBuildError("response exceeded configured byte limit")
                body.extend(chunk)
            return httpx.Response(
                status_code=streamed.status_code,
                headers=streamed.headers,
                content=bytes(body),
                request=streamed.request,
            )
    raise IndexBuildError("source exceeded the redirect limit")


async def _robots_allowed(
    client: httpx.AsyncClient, url: str, robots_cache: dict[str, RobotFileParser | None | bool],
    robots_lock: asyncio.Lock,
) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    origin = f"https://{host}"
    async with robots_lock:
        if origin not in robots_cache:
            parser = RobotFileParser()
            try:
                response = await _get_same_host(client, f"{origin}/robots.txt", host, max_bytes=256_000)
                if response.status_code == 404:
                    robots_cache[origin] = None
                elif response.status_code == 200:
                    parser.parse(response.text.splitlines())
                    robots_cache[origin] = parser
                else:
                    # Fail closed if the site's robots policy cannot be checked.
                    robots_cache[origin] = False  # type: ignore[assignment]
            except (httpx.HTTPError, IndexBuildError, ValueError):
                robots_cache[origin] = False  # type: ignore[assignment]
        policy = robots_cache[origin]
    if policy is False:
        return False
    return policy is None or policy.can_fetch(USER_AGENT, url)


async def _fetch_one(
    client: httpx.AsyncClient, source: Any,
    robots_cache: dict[str, RobotFileParser | None | bool], robots_lock: asyncio.Lock,
    semaphore: asyncio.Semaphore,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    checked_at = datetime.now(timezone.utc).isoformat()
    audit: dict[str, Any] = {
        "source_url": source.url,
        "institution": source.institution,
        "registry_title": source.title,
        "checked_at": checked_at,
        "status": "failed",
        "reason": None,
        "final_url": None,
        "http_status": None,
        "response_bytes": 0,
        "passage_count": 0,
        "extracted_text_sha256": None,
    }
    async with semaphore:
        try:
            if not await _robots_allowed(client, source.url, robots_cache, robots_lock):
                audit["reason"] = "robots_policy_disallowed_or_unavailable"
                return [], audit

            expected_host = (urlparse(source.url).hostname or "").lower()
            response = await _get_same_host(client, source.url, expected_host, max_bytes=MAX_PAGE_BYTES)
            audit["final_url"] = str(response.url)
            audit["http_status"] = response.status_code
            audit["response_bytes"] = len(response.content)

            if response.status_code != 200:
                audit["reason"] = f"http_status_{response.status_code}"
                return [], audit
            if "text/html" not in response.headers.get("content-type", "").lower():
                audit["reason"] = "response_not_html"
                return [], audit
            if len(response.content) > MAX_PAGE_BYTES:
                audit["reason"] = "response_exceeds_size_limit"
                return [], audit
            if not await _robots_allowed(client, str(response.url), robots_cache, robots_lock):
                audit["reason"] = "robots_policy_disallowed_redirect_target"
                return [], audit

            page_title, passages = extract_passages(response.text)
            extracted = "\n".join(text for _, text in passages)
            if len(extracted) < MIN_EXTRACTED_CHARS:
                audit["reason"] = "insufficient_extractable_text"
                return [], audit

            title = page_title or source.title
            source_id = source_id_for_url(source.url)
            document_id = document_id_for_url(source.url)
            records: list[dict[str, Any]] = []
            for position, (section_path, passage_text) in enumerate(passages):
                content_hash = _sha256(passage_text.encode("utf-8"))
                passage_id = "pas_" + _sha256(
                    f"{document_id}\0{position}\0{content_hash}".encode("utf-8")
                )[:24]
                records.append({
                    "source_id": source_id,
                    "document_id": document_id,
                    "passage_id": passage_id,
                    "source_url": source.url,
                    "institution": source.institution,
                    "title": title,
                    "section_path": list(section_path),
                    "position": position,
                    "text": passage_text,
                    "content_hash": content_hash,
                })

            audit.update({
                "status": "indexed",
                "reason": None,
                "passage_count": len(records),
                "extracted_text_sha256": _sha256(extracted.encode("utf-8")),
            })
            return records, audit
        except (httpx.HTTPError, IndexBuildError, ValueError, UnicodeError) as exc:
            audit["reason"] = type(exc).__name__ + ": " + str(exc)[:180]
            return [], audit


async def build_representative_index(
    *, index_version: str, sources: tuple[Any, ...] = SOURCES
) -> tuple[bytes, dict[str, Any]]:
    """Fetch the curated seed set and return artifact bytes plus a non-content audit manifest."""
    if not isinstance(index_version, str) or not index_version.strip():
        raise IndexBuildError("index_version must be a non-empty string")

    timeout = httpx.Timeout(12.0, connect=5.0)
    limits = httpx.Limits(max_connections=MAX_CONCURRENCY, max_keepalive_connections=MAX_CONCURRENCY)
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html"}
    robots_cache: dict[str, RobotFileParser | None | bool] = {}
    robots_lock = asyncio.Lock()
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

    async with httpx.AsyncClient(timeout=timeout, limits=limits, headers=headers) as client:
        results = await asyncio.gather(*(
            _fetch_one(client, source, robots_cache, robots_lock, semaphore)
            for source in sources
        ))

    records = [record for source_records, _ in results for record in source_records]
    audit = [entry for _, entry in results]
    if not records:
        raise IndexBuildError("no approved source produced enough usable content; no artifact was written")

    generated_at = datetime.now(timezone.utc).isoformat()
    artifact = build_index_artifact(
        records, index_version=index_version, generated_at=generated_at
    )
    manifest = {
        "manifest_schema_version": 1,
        "index_version": index_version,
        "generated_at": generated_at,
        "registry_source_count": len(sources),
        "indexed_source_count": sum(item["status"] == "indexed" for item in audit),
        "failed_source_count": sum(item["status"] != "indexed" for item in audit),
        "record_count": len(records),
        "artifact_sha256": _sha256(artifact),
        "sources": audit,
        "notice": (
            "Audit metadata only. This manifest does not certify legal authority, "
            "content freshness, copyright permission, or completeness."
        ),
    }
    return artifact, manifest


def write_build_outputs(
    artifact: bytes, manifest: dict[str, Any], output_path: str | Path,
    manifest_path: str | Path,
) -> None:
    """Write each output through a temporary file before replacing its destination."""
    output = Path(output_path)
    audit = Path(manifest_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    audit.parent.mkdir(parents=True, exist_ok=True)
    output_tmp = output.with_suffix(output.suffix + ".tmp")
    audit_tmp = audit.with_suffix(audit.suffix + ".tmp")
    output_tmp.write_bytes(artifact)
    audit_tmp.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    output_tmp.replace(output)
    audit_tmp.replace(audit)
