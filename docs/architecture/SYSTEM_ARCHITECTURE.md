# System Architecture

## 1. Architectural direction
Use a modular monolith initially. Keep the browser client, API, data persistence, retrieval, and provider adapters clearly separated. Avoid microservices until measured scale or operational boundaries justify them.

## 2. Logical components

### Frontend
- Next.js, React, TypeScript, and Tailwind are candidate technologies.
- Responsive PWA-oriented experience with accessible chat, source references, upload states, document preview, and export controls.
- Keep secrets and privileged operations out of browser code.
- Communicate with the backend through versioned API contracts.

### Backend
- Python with FastAPI is the current candidate.
- Modules: chat orchestration, retrieval/RAG, source registry, model-provider adapters, document processing, OCR, forms, PDF/export, identity/access, and audit.
- Phase 1 implements only the chat, retrieval, source, provider, and foundational security slices.

### Data and storage
- PostgreSQL for application records and metadata.
- Supabase PostgreSQL and private object storage are candidates, not yet irrevocably selected.
- Vector search may begin with a small local FAISS index or use PostgreSQL/pgvector when deployment and operations are validated.
- Public indexed source content must be separated from private user uploads and generated documents.

### External integrations
- Web search/retrieval and official public websites.
- Replaceable LLM, embedding, reranking, OCR, and document parsing adapters.
- No integration may introduce an unapproved paid dependency.

## 3. Request flow
1. Browser sends a question to the API.
2. API validates input, applies rate limits, and creates request context.
3. Retrieval searches the approved source registry and permitted live sources.
4. Results are normalized into passages, ranked using topic-independent BM25 relevance with a general preference for approved official government sources, and expanded with nearby same-page context so related list items and explanations are retained.
5. The model adapter receives the question and bounded evidence context.
6. Answer validation checks citation references and required uncertainty language.
7. API returns answer, citations, source dates, and warnings.
8. Telemetry records operational metadata without unnecessarily storing sensitive content.

## 4. RAG and source governance
Each source record should include institution/publisher, title, canonical URL, source type, publication date if known, retrieved-at time, last-checked time, language, content hash, status, and reliability notes. Store document/chunk provenance so each retrieved passage can be traced to its source. Prefer official government sources; use secondary sources only with clear labeling. Detect and surface conflicting or outdated material rather than silently choosing one.

Live retrieval and indexed content should share a normalized evidence interface. A source being reachable does not automatically make it authoritative. Respect site terms, robots rules, copyright, and reasonable request rates.

## 5. Provider abstraction
Define interfaces for:
- Chat completion/generation.
- Embedding.
- Optional reranking.
- OCR.
- Document parsing.
- Object storage.

Adapters must expose capability, limits, model/version, licence, and operational health metadata. The application must be able to change providers without rewriting product workflows.

## 6. Suggested repository layout
```text
frontend/
  app/ components/ features/ services/ public/
backend/
  app/
    api/ core/ models/ services/
    modules/
      chat/ rag/ sources/ documents/ ocr/ forms/ pdf/
  tests/
infrastructure/
  database/ deployment/ monitoring/
docs/
  architecture/ requirements/ security/ api/ handovers/
scripts/
.github/
```

## 7. Deployment direction
Candidate split: frontend on a static/web host, API on an application host, PostgreSQL and private file storage on a managed or self-hosted service. Netlify, Render, and Supabase are candidates only. Validate current free-tier limits, sleep/cold-start behavior, storage, bandwidth, build limits, data region, backup, and acceptable-use terms before choosing. Free hosting is not assumed to support local model inference or OCR workloads.

## 8. Operational concerns
- Health/readiness endpoints and structured logs.
- Request IDs and provider timeout/retry policies.
- Background processing for large files in later phases.
- Database migrations and backup/restore testing.
- Resource ceilings for uploads, OCR, and model inference.
- Monitoring for broken sources, stale content, latency, errors, and unexpected cost.
- Document a rollback path for every deployment.

## 9. Architecture decision gates
Before implementation, verify framework compatibility, deployment feasibility, supported Python/Node versions, licensing, data protection, and actual free-tier limits. Any paid service, material change of scope, or production deployment requires explicit user approval.
