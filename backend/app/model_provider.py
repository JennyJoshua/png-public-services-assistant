"""Optional OpenAI-compatible chat-model adapter.

Groq is the initial provider. The endpoint and model have safe defaults, while
the key is always supplied as a private server-side secret. Other compatible
providers can be selected later by overriding the endpoint and model.
"""
import os

import httpx

from app.system_prompt import SYSTEM_PROMPT

MAX_HISTORY_MESSAGES = 8
MAX_EVIDENCE_CHARS = 7000
MAX_ANSWER_CHARS = 12000
DEFAULT_MODEL_API_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL_NAME = "openai/gpt-oss-20b"


class ModelProviderError(RuntimeError):
    """Raised when a configured model provider cannot return a usable answer."""


def _provider_settings() -> tuple[str, str, str]:
    return (
        os.getenv("MODEL_API_BASE_URL", DEFAULT_MODEL_API_BASE_URL).strip().rstrip("/"),
        os.getenv("MODEL_API_KEY", "").strip(),
        os.getenv("MODEL_NAME", DEFAULT_MODEL_NAME).strip(),
    )


def model_is_configured() -> bool:
    base_url, api_key, model = _provider_settings()
    return bool(base_url and api_key and model)


def _build_messages(
    question: str,
    evidence: list[dict],
    history: list[dict] | None = None,
) -> list[dict[str, str]]:
    evidence_parts: list[str] = []
    remaining = MAX_EVIDENCE_CHARS
    for index, item in enumerate(evidence, start=1):
        text = str(item.get("text", ""))[:1800]
        citation_number = item.get("citation_index", index)
        block = f"[{citation_number}] {text}"
        if len(block) > remaining:
            break
        evidence_parts.append(block)
        remaining -= len(block)

    evidence_text = "\n\n".join(evidence_parts) or "No relevant approved-source passages were found."
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in (history or [])[-MAX_HISTORY_MESSAGES:]:
        role = item.get("role")
        content = str(item.get("content", "")).strip()
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content[:3000]})
    messages.append({
        "role": "user",
        "content": (
            f"Question: {question.strip()}\n\n"
            f"Approved-source excerpts (use only if relevant):\n{evidence_text}"
        ),
    })
    return messages


async def generate_answer(
    question: str,
    evidence: list[dict],
    history: list[dict] | None = None,
) -> str | None:
    """Generate an answer when a compatible provider has been configured."""
    base_url, api_key, model = _provider_settings()
    if not api_key:
        return None
    if not base_url.startswith("https://"):
        raise ModelProviderError("The model provider URL must use HTTPS.")

    payload = {
        "model": model,
        "messages": _build_messages(question, evidence, history),
        "temperature": 0.1,
        "max_tokens": 900,
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=8.0)) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ModelProviderError("The configured model provider did not return a valid response.") from exc

    try:
        answer = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ModelProviderError("The model provider response had an unexpected format.") from exc
    if not isinstance(answer, str) or not answer.strip():
        raise ModelProviderError("The model provider returned an empty answer.")
    return answer.strip()[:MAX_ANSWER_CHARS]
