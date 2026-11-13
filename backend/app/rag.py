"""Live retrieval over curated PNG sources, with an optional grounded model layer."""
import asyncio
import math
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
MAX_SNIPPETS = 12
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
    """Normalize common abbreviations and equivalent public-service terms."""
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
    business_terms = {"business", "businesses", "company", "companies", "incorporation", "incorporate", "registering"}
    if tokens & business_terms:
        tokens.update({"business", "businesses", "name", "company", "companies", "registration", "register", "registering", "incorporation", "incorporate", "ipa"})
    return tokens


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
    """Rank relevant passages with BM25 and add nearby context from the same page.

    Context expansion is deliberately topic-independent: a matching heading or
    paragraph can bring along adjacent checklist items, table rows, and
    explanations that would otherwise be lost when a page is split into blocks.
    """
    query_tokens = _query_tokens(question)
    if not query_tokens:
        return []

    documents: list[dict] = []
    document_frequency: dict[str, int] = {}
    total_length = 0

    for page_index, page in enumerate(pages):
        title_tokens = _tokens(str(page.get("title", "")))
        for passage_index, passage in enumerate(_passage_blocks(page.get("text", ""))):
            if len(passage) < 25:
                continue
            tokens = re.findall(r"[a-z0-9]{2,}", passage.lower())
            frequencies: dict[str, int] = {}
            for token in tokens:
                if token not in STOP_WORDS:
                    frequencies[token] = frequencies.get(token, 0) + 1
            if not frequencies:
                continue
            documents.append({
                "page_index": page_index,
                "passage_index": passage_index,
                "text": passage,
                "tokens": frequencies,
                "length": sum(frequencies.values()),
                "title_tokens": title_tokens,
                "source": page,
            })
            total_length += sum(frequencies.values())
            for token in set(frequencies):
                document_frequency[token] = document_frequency.get(token, 0) + 1

    if not documents:
        return []

    # BM25 gives longer passages a length-normalized relevance score and
    # down-weights terms that occur in almost every passage.
    average_length = total_length / len(documents)
    k1 = 1.5
    b = 0.75
    ranked: list[dict] = []
    for document in documents:
        score = 0.0
        for token in query_tokens:
            frequency = document["tokens"].get(token, 0)
            if not frequency:
                continue
            doc_frequency = document_frequency.get(token, 0)
            inverse_frequency = math.log(
                1 + (len(documents) - doc_frequency + 0.5) / (doc_frequency + 0.5)
            )
            denominator = frequency + k1 * (
                1 - b + b * document["length"] / max(average_length, 1)
            )
            score += inverse_frequency * (frequency * (k1 + 1)) / denominator
        title_overlap = query_tokens & document["title_tokens"]
        score += 1.5 * len(title_overlap)
        source_host = (urlparse(str(document["source"].get("url", ""))).hostname or "").lower()
        if source_host.endswith(".gov.pg"):
            score += 2.0
        if score > 0:
            ranked.append({**document, "score": score})

    if not ranked:
        return []

    ranked.sort(key=lambda item: item["score"], reverse=True)

    # Expand the strongest matches with nearby passages from the same source
    # page. This preserves the surrounding context of multi-line instructions
    # and lists without writing a rule for each public-service topic.
    selected_scores: dict[tuple[int, int], float] = {}
    document_lookup = {
        (item["page_index"], item["passage_index"]): item for item in documents
    }
    for seed in ranked[:3]:
        page_index = seed["page_index"]
        center = seed["passage_index"]
        for offset in range(-6, 7):
            position = center + offset
            key = (page_index, position)
            neighbour = document_lookup.get(key)
            if neighbour is None:
                continue
            contextual_score = seed["score"] / (1 + abs(offset) * 0.35)
            selected_scores[key] = max(selected_scores.get(key, 0), contextual_score)

    selected = []
    for key, score in sorted(
        selected_scores.items(), key=lambda item: item[1], reverse=True
    ):
        item = document_lookup[key]
        selected.append({
            "score": score,
            "text": item["text"],
            "source": item["source"],
        })
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
