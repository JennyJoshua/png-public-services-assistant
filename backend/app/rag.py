"""Live retrieval over curated PNG sources, with an optional grounded model layer."""
import asyncio
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.model_provider import ModelProviderError, generate_answer, model_is_configured
from app.source_registry import SOURCES

MAX_PAGE_BYTES = 1_500_000
MAX_TEXT_CHARS = 24_000
MAX_PASSAGE_CHARS = 1_400
MAX_SNIPPETS = 8
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does",
    "for", "from", "how", "i", "in", "is", "it", "me", "my", "of", "on",
    "or", "the", "to", "what", "when", "where", "which", "who", "with",
    "you", "your",
}


def _tokens(value: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-z0-9]{2,}", value.lower())
        if token not in STOP_WORDS
    }


def _query_tokens(question: str) -> set[str]:
    """Add narrow vocabulary bridges for common PNG public-service wording."""
    tokens = _tokens(question)
    # Treat common NID wording as one concept so abbreviated and expanded
    # questions retrieve the same official registration guidance.
    is_nid_wording = (
        "nid" in tokens
        or ("national" in tokens and ("id" in tokens or "identity" in tokens))
        or ("identity" in tokens and "card" in tokens)
    )
    if is_nid_wording:
        tokens.update({"nid", "national", "identity", "id", "card", "registration", "form"})
    # Normalize common business-registration wording for the IPA guidance.
    business_terms = {"business", "company", "incorporation", "incorporate", "registering", "registration", "registered"}
    if tokens & business_terms:
        tokens.update({"business", "businesses", "name", "company", "companies", "registration", "register", "registering", "incorporation", "incorporate", "ipa"})
    return tokens


def _is_nid_question(query_tokens: set[str]) -> bool:
    return (
        "nid" in query_tokens
        or ("national" in query_tokens and ("id" in query_tokens or "identity" in query_tokens))
        or ("identity" in query_tokens and "card" in query_tokens)
    )


def _is_business_registration_question(query_tokens: set[str]) -> bool:
    return bool(query_tokens & {"business", "businesses", "company", "companies", "incorporation", "incorporate"})


def _page_text(html: str) -> tuple[str, str | None]:
    """Extract semantic content blocks without flattening lists into page-wide prose."""
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else None
    for element in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript", "svg"]):
        element.decompose()

    main = soup.find("main") or soup.find("article") or soup.body or soup
    blocks: list[str] = []
    for element in main.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "dt", "dd", "tr"]):
        # A paragraph nested in a list item is already represented by its parent list item.
        if element.name == "p" and element.find_parent("li"):
            continue
        value = re.sub(r"\s+", " ", element.get_text(" ", strip=True)).strip()
        if value and (not blocks or value != blocks[-1]):
            blocks.append(value)

    # Some CMS pages use content divs without semantic paragraph tags.
    if not blocks:
        value = re.sub(r"\s+", " ", main.get_text(" ", strip=True)).strip()
        if value:
            blocks.append(value)
    return "\n".join(blocks)[:MAX_TEXT_CHARS], title


def _published_date(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    for key in ("article:published_time", "date", "DC.date", "pubdate"):
        tag = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
        if tag and tag.get("content"):
            return tag["content"][:80]
    time_tag = soup.find("time")
    return time_tag.get("datetime", "")[:80] or None if time_tag else None


async def _fetch_source(client: httpx.AsyncClient, source) -> dict | None:
    try:
        response = await client.get(source.url)
        final_host = (urlparse(str(response.url)).hostname or "").lower()
        approved_host = (urlparse(source.url).hostname or "").lower()
        if final_host != approved_host or response.status_code != 200:
            return None
        if "text/html" not in response.headers.get("content-type", "").lower():
            return None
        if len(response.content) > MAX_PAGE_BYTES:
            return None
        html = response.text
        text, page_title = _page_text(html)
        if len(text) < 80:
            return None
        return {
            "institution": source.institution,
            "title": page_title or source.title,
            "url": source.url,
            "publication_date": _published_date(html),
            "last_checked_at": datetime.now(timezone.utc).isoformat(),
            "text": text,
        }
    except (httpx.HTTPError, ValueError, UnicodeError):
        return None


def _passage_blocks(page_text: str) -> list[str]:
    """Keep headings, paragraphs and list items intact as individual passages."""
    passages: list[str] = []
    for block in page_text.splitlines():
        block = block.strip()
        if not block:
            continue
        if len(block) <= MAX_PASSAGE_CHARS:
            passages.append(block)
            continue
        # Split only exceptionally long blocks; retain sentence boundaries.
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", block)
        current = ""
        for sentence in sentences:
            if current and len(current) + len(sentence) + 1 > MAX_PASSAGE_CHARS:
                passages.append(current)
                current = sentence
            else:
                current = f"{current} {sentence}".strip()
        if current:
            passages.append(current)
    return passages


def _rank_passages(question: str, pages: list[dict]) -> list[dict]:
    query_tokens = _query_tokens(question)
    if not query_tokens:
        return []

    is_nid_question = _is_nid_question(query_tokens)
    is_business_question = _is_business_registration_question(query_tokens)
    ranked: list[dict] = []
    for page in pages:
        source_text = f"{page.get('title', '')} {page.get('url', '')}".lower()
        source_boost = 0
        if is_nid_question and "pngcir.gov.pg" in source_text:
            source_boost += 12
        if is_nid_question and ("nid-registration-information" in source_text or "registration information" in source_text):
            source_boost += 10
        if is_business_question and "ipa.gov.pg" in source_text:
            source_boost += 16
        if is_business_question and any(term in source_text for term in ("registerbusinessname", "businessregulations", "prescribedforms")):
            source_boost += 8

        for passage in _passage_blocks(page["text"]):
            if len(passage) < 35:
                continue
            passage_tokens = _tokens(passage)
            overlap = query_tokens & passage_tokens
            if not overlap:
                continue
            score = sum(3 if token in passage.lower() else 1 for token in overlap)
            score += source_boost
            # Prefer passages that explain an action, rather than generic mentions of an ID.
            if is_nid_question and any(term in passage.lower() for term in ("download", "lodge", "registration form", "fingerprint", "capture")):
                score += 5
            if is_business_question and any(term in passage.lower() for term in ("proposed business name", "owners", "principal place of business", "directors", "shareholders", "company constitution", "client account")):
                score += 6
            ranked.append({"score": score, "text": passage, "source": page})

    ranked.sort(key=lambda item: item["score"], reverse=True)
    selected: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for item in ranked:
        key = (item["source"]["url"], item["text"])
        if key in seen:
            continue
        seen.add(key)
        selected.append(item)
        if len(selected) >= MAX_SNIPPETS:
            break
    return selected


async def retrieve_answer(question: str, history: list[dict] | None = None) -> dict:
    """Fetch approved evidence, then optionally ask a model to compose the response."""
    timeout = httpx.Timeout(7.0, connect=4.0)
    headers = {"User-Agent": "PNGPublicServicesAssistant/0.3", "Accept": "text/html"}
    async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
        pages = await asyncio.gather(*(_fetch_source(client, source) for source in SOURCES))

    available_pages = [page for page in pages if page]
    passages = _rank_passages(question, available_pages)

    citations: list[dict] = []
    citation_indexes: dict[str, int] = {}
    evidence: list[dict] = []
    for passage in passages:
        source = passage["source"]
        url = source["url"]
        if url not in citation_indexes:
            citation_indexes[url] = len(citations) + 1
            citations.append({
                "title": source["title"],
                "institution": source["institution"],
                "url": url,
                "publication_date": source["publication_date"],
                "last_checked_at": source["last_checked_at"],
            })
        evidence.append({"text": passage["text"], "citation_index": citation_indexes[url]})

    warnings: list[str] = []
    try:
        answer = await generate_answer(question, evidence, history or [])
    except ModelProviderError:
        answer = None
        warnings.append(
            "The configured AI model is temporarily unavailable. The response below uses source excerpts instead."
        )

    if answer:
        return {
            "answer": answer,
            "answer_mode": "model",
            "citations": citations,
            "evidence": evidence,
            "warnings": warnings,
        }

    if not passages:
        fallback = (
            "I could not find a sufficiently relevant passage in the currently approved sources. "
            "I won't guess at official requirements. Please check the responsible agency's website "
            "or contact its office."
        )
    else:
        answer_lines = [
            "I found these relevant passages in the approved PNG public-service sources:"
        ]
        for item in evidence:
            answer_lines.append(f"- {item['text']} [{item['citation_index']}]")
        answer_lines.append(
            "These are source excerpts, not confirmation that every requirement is current or applies "
            "to your circumstances. Open the cited page and confirm important details with the institution."
        )
        fallback = "\n\n".join(answer_lines)

    if not model_is_configured():
        warnings.append(
            "AI-generated answers are not enabled yet. This response is limited to retrieved source excerpts."
        )
    return {
        "answer": fallback,
        "answer_mode": "extractive",
        "citations": citations,
        "evidence": evidence,
        "warnings": warnings,
    }
