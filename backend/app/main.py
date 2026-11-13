import os
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.rag import retrieve_answer

app = FastAPI(
    title="PNG Public Services Assistant API",
    version="0.2.0",
    description="Live retrieval over a curated set of PNG public-service sources.",
    docs_url="/api/docs",
    redoc_url=None,
)

# Set CORS_ORIGINS to a comma-separated list of trusted frontend origins in deployment.
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


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


@app.get("/api/v1/health", tags=["system"])
async def health() -> dict[str, str]:
    """Return basic application health without exposing infrastructure details."""
    return {
        "status": "ok",
        "service": "png-public-services-assistant-api",
        "version": "0.2.0",
    }


@app.post("/api/v1/chat", tags=["chat"])
async def chat(request: ChatRequest) -> dict:
    """Retrieve relevant passages from the curated public source set."""
    result = await retrieve_answer(request.question.strip())
    return {
        "request_id": str(uuid.uuid4()),
        **result,
    }
