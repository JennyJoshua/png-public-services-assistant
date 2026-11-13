from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="PNG Public Services Assistant API",
    version="0.1.0",
    description="Phase 1 API foundation. Public-service answers are not connected yet.",
    docs_url="/api/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/api/v1/health", tags=["system"])
async def health() -> dict[str, str]:
    """Return basic application health without exposing infrastructure details."""
    return {"status": "ok", "service": "png-public-services-assistant-api", "version": "0.1.0"}
