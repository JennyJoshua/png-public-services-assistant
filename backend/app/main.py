import os
import uuid
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.rag import retrieve_answer

app = FastAPI(
    title="PNG Public Services Assistant API",
    version="0.3.0",
    description="Source-grounded chat with an optional replaceable language-model provider.",
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


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=3000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    history: list[ConversationMessage] = Field(default_factory=list, max_length=8)


@app.get("/api/v1/health", tags=["system"])
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "png-public-services-assistant-api",
        "version": "0.3.0",
    }


@app.post("/api/v1/chat", tags=["chat"])
async def chat(request: ChatRequest) -> dict:
    result = await retrieve_answer(
        request.question.strip(),
        [message.model_dump() for message in request.history],
    )
    return {"request_id": str(uuid.uuid4()), **result}
