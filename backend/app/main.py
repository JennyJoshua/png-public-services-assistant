import asyncio
import hmac
import logging
import os
import time
import uuid
from collections import defaultdict, deque
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.rag import retrieve_answer
from app.source_content import get_sources_status, refresh_loop, refresh_sources
from app.source_store import (
    close_source_store,
    database_source_store_enabled,
    fetch_active_source_pages,
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="PNG Public Services Assistant API",
    version="0.4.0",
    description="PNG public-service answers grounded in configured official sources.",
    docs_url="/api/docs",
    redoc_url=None,
)

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

RATE_LIMIT_REQUESTS = 30
RATE_LIMIT_WINDOW_SECONDS = 60
_rate_buckets: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def chat_rate_limit(request: Request, call_next):
    if request.url.path == "/api/v1/chat":
        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        bucket = _rate_buckets[client_ip]
        while bucket and now - bucket[0] >= RATE_LIMIT_WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please wait a minute and try again."},
                headers={"Retry-After": str(RATE_LIMIT_WINDOW_SECONDS)},
            )
        bucket.append(now)
        # Bound memory if many different client IPs visit the service.
        if len(_rate_buckets) > 5000:
            stale = [key for key, values in _rate_buckets.items() if not values or now - values[-1] >= RATE_LIMIT_WINDOW_SECONDS]
            for key in stale:
                _rate_buckets.pop(key, None)
    return await call_next(request)


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=3000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    history: list[ConversationMessage] = Field(default_factory=list, max_length=8)


@app.on_event("startup")
async def start_source_refresh() -> None:
    """Use durable approved versions when configured; otherwise warm the legacy cache."""
    if database_source_store_enabled():
        try:
            pages = await fetch_active_source_pages()
            logger.info("Durable source store ready; %s active evidence pages available.", len(pages))
        except Exception:
            # Keep the API available but fail closed: retrieval returns no evidence.
            logger.exception("Durable source store unavailable at startup; retrieval will fail closed.")
        return

    try:
        await refresh_sources()
    except Exception:
        # A source outage must never prevent the API from starting.
        logger.exception("Initial source refresh failed; starting API with the available cache.")
    app.state.source_refresh_task = asyncio.create_task(refresh_loop())


@app.on_event("shutdown")
async def stop_source_refresh() -> None:
    task = getattr(app.state, "source_refresh_task", None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    await close_source_store()


@app.get("/api/v1/health", tags=["system"])
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "png-public-services-assistant-api",
        "version": "0.4.0",
    }


@app.get("/sources-status", tags=["admin"])
async def sources_status(request: Request) -> dict:
    configured_token = os.getenv("SOURCES_STATUS_TOKEN", "").strip()
    if not configured_token:
        raise HTTPException(status_code=503, detail="Source status endpoint is disabled until SOURCES_STATUS_TOKEN is configured.")
    supplied = request.headers.get("authorization", "")
    expected = f"Bearer {configured_token}"
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="A valid bearer token is required.")
    return get_sources_status()


@app.post("/api/v1/chat", tags=["chat"])
async def chat(request: ChatRequest) -> dict:
    result = await retrieve_answer(
        request.question.strip(),
        [message.model_dump() for message in request.history],
    )
    return {"request_id": str(uuid.uuid4()), **result}
