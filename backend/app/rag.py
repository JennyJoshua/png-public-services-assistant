"""Live retrieval over curated PNG sources, with an optional grounded model layer."""
import asyncio
import math
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.model_provider import ModelProviderError, generate_answer, model_is_configured
from app.retrieval_pipeline import build_evidence_records, page_to_fetched_document
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


VOCABULARY_ALIASES = {
    "nid": {"national", "identity", "id", "card"},
    "national": {"nid", "identity"},
    "identity": {"nid", "national", "card"},
    "card": {"nid", "identity"},
    "business": {"businesses", "company", "companies"},
    "businesses": {"business", "company", "companies"},
    "company": {"business", "businesses", "companies"},
    "companies": {"business", "businesses", "company"},
    "incorporation": {"company", "business"},
    "incorporate": {"company", "business"},
}


def _query_tokens(question: str) -> set[str]:
    """Expand reusable vocabulary aliases without branching on question topics."""
    tokens = _tokens(question)
    for token in tuple(tokens):
        tokens.update(VOCABULARY_ALIASES.get(token, set()))
    return tokens


def _page_structure(html: str) -> tuple[list[dict], str | None]:
    """Extract ordered content blocks and their active heading hierarchy."""
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else None
    for element in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript", "svg"]):
        element.decompose()

    main = soup.find("main") or soup.find("article") or soup.body or soup
    blocks: list[dict] = []
    headings: list[str | None] = [None] * 6

    for element in main.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "dt", "dd", "tr"]):
        if element.name == "p" and element.find_parent("li"):
            continue
        if element.name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            value = re.sub(r"\s+", " ", element.get_text(" ", strip=True)).strip()
            level = int(element.name[1])
            headings[level - 1] = value or None
            for index in range(level, 6):
                headings[index] = None
            section_path = tuple(item for item in headings if item)
        else:
            section_path = tuple(item for item in headings if item)
            if element.name == "tr":
                cells = element.find_all(["th", "td"], recursive=False)
                if not cells or all(cell.name == "th" for cell in cells):
                    continue
                table = element.find_parent("table")
                header_row = table.find("tr") if table else None
                headers = (
                    [re.sub(r"\s+", " ", cell.get_text(" ", strip=True)).strip()
                     for cell in header_row.find_all(["th", "td"], recursive=False)]
                    if header_row else []
                )
                values = [re.sub(r"\s+", " ", cell.get_text(" ", strip=True)).strip() for cell in cells]
                value = " | ".join(
                    f"{header}: {cell}" for header, cell in zip(headers, values)
                ) if headers and len(headers) == len(values) else " | ".join(values)
            else:
                value = re.sub(r"\s+", " ", element.get_text(" ", strip=True)).strip()

        if value and (not blocks or value != blocks[-1]["text"]):
            blocks.append({"text": value, "section_path": section_path})

    if not blocks:
        value = re.sub(r"\s+", " ", main.get_text(" ", strip=True)).strip()
        if value:
            blocks.append({"text": value, "section_path": ()})

    # Bound extracted text without losing block order or heading provenance.
    bounded: list[dict] = []
    remaining = MAX_TEXT_CHARS
    for block in blocks:
        if remaining <= 0:
            break
        value = block["text"][:remaining]
        if value:
            bounded.append({**block, "text": value})
            remaining -= len(value) + 1
    return bounded, title


def _page_text(html: str) -> tuple[str, str | None]:
    """Compatibility wrapper returning the historic newline-delimited text."""
    blocks, title = _page_structure(html)
    return "\n".join(block["text"] for block in blocks), title


def _split_passage_block(block: str) -> list[str]:
    """Split exceptionally long blocks while retaining sentence boundaries."""
    if len(block) <= MAX_PASSAGE_CHARS:
        return [block]
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", block)
    passages: list[str] = []
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


def _structured_passages(page: dict) -> list[dict]:
    """Return ordered passage text with its section path, when extraction has it."""
    blocks = page.get("blocks")
    if not isinstance(blocks, list):
        return [
            {"text": text, "section_path": ()}
            for text in _passage_blocks(str(page.get("text", "")))
        ]

    passages: list[dict] = []
    for block in blocks:
        text = str(block.get("text", "")).strip()
        section_path = tuple(str(item) for item in block.get("section_path", ()))
        if not text:
            continue
        for passage in _split_passage_block(text):
            passages.append({"text": passage, "section_path": section_path})
    return passages

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
        content_blocks, page_title = _page_structure(html)
        text = "\n".join(block["text"] for block in content_blocks)
        if len(text) < 80:
            return None
        return {
            "institution": source.institution,
            "title": page_title or source.title,
            "url": source.url,
            "final_url": str(response.url),
            "content_type": response.headers.get("content-type", ""),
            "publication_date": _published_date(html),
            "last_checked_at": datetime.now(timezone.utc).isoformat(),
            "text": text,
            "blocks": content_blocks,
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
        for passage_index, passage_record in enumerate(_structured_passages(page)):
            passage = passage_record["text"]
            if len(passage) < 2:
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
                "section_path": passage_record["section_path"],
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

    # Rank source pages by their strongest match, but preserve passage order
    # within each page. This keeps procedural steps and table context in order.
    page_scores: dict[int, float] = {}
    for (page_index, _), score in selected_scores.items():
        page_scores[page_index] = max(page_scores.get(page_index, 0.0), score)

    selected = []
    for page_index in sorted(page_scores, key=page_scores.get, reverse=True):
        page_items = sorted(
            (
                (passage_index, score)
                for (candidate_page, passage_index), score in selected_scores.items()
                if candidate_page == page_index
            ),
            key=lambda item: item[0],
        )
        for passage_index, score in page_items:
            item = document_lookup[(page_index, passage_index)]
            selected.append({
                "score": score,
                "text": item["text"],
                "passage_index": item["passage_index"],
                "section_path": item["section_path"],
                "source": item["source"],
            })
            if len(selected) >= MAX_SNIPPETS:
                return selected

    return selected


async def retrieve_answer(question: str, history: list[dict] | None = None) -> dict:
    """Fetch approved evidence, then optionally ask a model to compose the response."""
    timeout = httpx.Timeout(7.0, connect=4.0)
    headers = {"User-Agent": "PNGPublicServicesAssistant/0.3", "Accept": "text/html"}
    async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
        pages = await asyncio.gather(*(_fetch_source(client, source) for source in SOURCES))

    available_pages = [page for page in pages if page]
    fetched_documents = [page_to_fetched_document(page) for page in available_pages]
    passages = _rank_passages(question, available_pages)
    evidence_records = build_evidence_records(fetched_documents, passages)

    citations: list[dict] = []
    citation_indexes: dict[str, int] = {}
    evidence: list[dict] = []
    for passage in evidence_records:
        source = passage.source
        url = source.url
        if url not in citation_indexes:
            citation_indexes[url] = len(citations) + 1
            citations.append({
                "title": source.title,
                "institution": source.institution,
                "url": url,
                "publication_date": passage.publication_date,
                "last_checked_at": source.last_fetched_at.isoformat() if source.last_fetched_at else None,
            })
        evidence.append({"text": passage.text, "citation_index": citation_indexes[url]})

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

    if not evidence_records:
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
