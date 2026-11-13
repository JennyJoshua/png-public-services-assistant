# Phase 1 Implementation Breakdown

**Status:** Prepared on phase-1/foundation; implementation has not yet begun.
**Baseline:** Specification PR #1 merged to main on 13 November 2026.
**Scope:** Phase 1 public-information chat only.

## 1. Delivery objective

Deliver a usable Android-friendly web chat that answers a deliberately limited set of Papua New Guinea public-service questions from traceable public evidence. If the system cannot retrieve sufficient reliable evidence, it must say so rather than improvise.

Phase 1 excludes document generation, user uploads, OCR, form filling, account registration, and production release.

## 2. Implementation principles

- Keep main stable; all work is on this feature branch and later through a reviewable PR.
- Do not add a paid API, paid hosting, or paid dependency.
- Do not select a model merely because a free demo or temporary quota exists.
- Do not claim AI answers are live until a provider has been evaluated and connected.
- Keep public source material separate from private conversation/session data.
- Use a small curated source set and a reviewed benchmark; do not attempt national coverage.
- Prefer the smallest working vertical slice over building every planned module at once.

## 3. Proposed repository layout

    frontend/
      app/
      components/
      lib/
    backend/
      app/
        api/v1/
        core/
        modules/chat/
        modules/sources/
        modules/retrieval/
        providers/
      tests/
    data/
      sources/
    docs/
      implementation/
    .github/workflows/

The layout is a target. Add modules only when the corresponding work package needs them.

## 4. Work packages and gates

### WP0 — Engineering baseline
- Add frontend and backend project manifests, pinned/locked dependencies, environment examples, formatting and lint configuration.
- Add GitHub Actions for frontend checks and backend tests.
- Add safe defaults, .gitignore, and setup documentation.
- No credentials or secrets in GitHub.
- Acceptance: clean CI checks; no real secrets; documented reproducible project commands.

### WP1 — Chat interface and API skeleton
- Build a narrow-screen-first chat interface with accessible message composer, loading, empty, error, retry, and citation presentation.
- Implement GET /api/v1/health and typed chat request/response schemas.
- Use a clearly labelled development stub only until a real evidence-grounded provider path is approved.
- Acceptance: mobile layout works; API validation and health tests pass; stub cannot be mistaken for a verified government answer.

### WP2 — Source registry and ingestion
- Define source records: publisher, title, canonical URL, source class, language, publication date, retrieved-at, last-checked, content hash, status, and provenance.
- Start with a small set of official PNG sources that are reachable and have clear reuse/terms information.
- Ingest only permitted content; store source URL and document/version identity with each extracted chunk.
- Acceptance: each chunk traces to a source record and version; stale, unavailable, and conflicting records can be represented.

### WP3 — Retrieval and evidence validation
- Implement a provider-neutral evidence interface and a simple retrieval baseline suitable for the small initial corpus.
- Rank official sources above secondary material while retaining conflicting evidence.
- Validate that citations refer only to retrieved source IDs and that source dates are exposed.
- Treat retrieved page content as untrusted data, not instructions.
- Acceptance: benchmark tests cover direct answer, conflicting sources, stale source, no evidence, prompt injection, and invalid citation cases.

### WP4 — Model feasibility and provider adapter
- Evaluate local/free inference options against the reviewed PNG question benchmark and actual deployment resource ceilings.
- Record exact model revision, licence, language quality, memory/CPU/GPU needs, latency, limits, privacy terms, and fallback behavior.
- Keep the chat provider behind an interface; do not couple retrieval or UI to one model.
- Acceptance: a model is selected only if it meets quality and resource criteria without an unapproved paid dependency. Otherwise ship the retrieval/answer workflow only as a clearly labelled prototype and report the blocker.

### WP5 — Anonymous sessions and persistence decision
- Finalize session ownership, expiry, retention, and storage only after the minimum data model and threat model are specified.
- Do not store full chat content in operational logs.
- Evaluate whether persistence is necessary for the initial public chat experience; do not add a database merely to satisfy an abstract architecture diagram.
- If persistence is selected, verify free-tier pause, storage, backup, region, and deletion behavior before use.
- Acceptance: session isolation and expiry tests pass; retention and deletion behavior are documented.

### WP6 — Security, quality, and operational checks
- Add bounded input validation, rate limiting, safe errors, request IDs, restrictive CORS, dependency checks, and security tests.
- Add tests for session isolation, provider timeout/malformed response, and citation integrity.
- Ensure no upload/OCR endpoint is exposed in Phase 1.
- Acceptance: no unresolved critical/high security finding; functional and mobile checks pass.

### WP7 — Hosting feasibility (not deployment)
- Assess static frontend hosting, API hosting, persistence, cold starts, outbound traffic, region, quotas, build minutes, and data handling.
- A free plan is for testing/prototyping only where provider terms say so; it is not automatically suitable for a public service.
- Render free web services sleep after 15 minutes idle and may take about a minute to wake; local filesystem is ephemeral. Render free Postgres expires after 30 days and has no backups.
- Supabase Free includes a 500 MB database and 1 GB file storage; free projects can pause after a week of inactivity and do not include automatic backups.
- Netlify Free currently uses a monthly credit allowance. Confirm current credit consumption before relying on it for public traffic.
- Acceptance: written recommendation, limitations, rollback plan, and owner approval before any production deployment.

## 5. Current technical evaluation (13 November 2026)

| Area | Candidate | Current assessment |
|---|---|---|
| Frontend | Next.js 16.x, React, TypeScript | Next.js 16 is Active LTS. Current Next.js installation guidance requires Node.js 20.9+. Pin an actively supported Node LTS compatible with the selected framework. |
| Backend | FastAPI, Python | FastAPI supports Python 3.10+. Pin a supported Python minor version and exact dependency lock after CI validation. |
| Frontend hosting | Netlify Free or another static/web host | Netlify advertises a $0 Free tier with a 300-credit monthly limit; consumption and current limits must be monitored. |
| API hosting | Render Free for prototype only | Free services sleep after 15 minutes idle, wake slowly, and have ephemeral filesystems. Not recommended as a public-service production target. |
| Database | Supabase Free candidate | 500 MB DB, 1 GB storage; projects pause after inactivity and no automatic backups are included on Free. Suitable for experiments only until retention/availability requirements are resolved. |
| Model | Local/free model candidates | No production model selected. Public hosted free inference cannot be assumed stable or private; local inference may exceed free hosting resources. |
| Retrieval | Small local corpus and provider-neutral retriever | Start simple; vector database is not justified until corpus size and retrieval evaluation require it. |

### Current decision

Proceed with the codebase foundation and UI/API skeleton, but keep hosting, database persistence, and production model choices open. The public-facing service cannot be described as a functioning AI assistant until a viable model/inference path has passed the benchmark.

## 6. Suggested implementation sequence

1. WP0 engineering baseline.
2. WP1 chat UI and API skeleton.
3. WP2 source registry and a tiny permitted source corpus.
4. WP3 retrieval and citation validation.
5. WP4 model benchmark and provider decision.
6. WP5 session/persistence decision and implementation.
7. WP6 security and quality hardening.
8. WP7 hosting recommendation and deployment gate.

Each work package should be tested before proceeding. The completed Phase 1 work is submitted as a PR; merging to main remains an owner approval gate.

## 7. Sources checked for current platform limits

- Next.js support policy: https://nextjs.org/support-policy
- Next.js installation requirements: https://nextjs.org/learn/react-foundations/installation
- FastAPI requirements and documentation: https://fastapi.tiangolo.com/
- Render free service limits: https://render.com/docs/free
- Render free service behavior: https://render.com/docs/faq
- Netlify pricing: https://www.netlify.com/pricing/
- Supabase pricing: https://supabase.com/pricing
- Supabase billing and free-tier quotas: https://supabase.com/docs/guides/platform/billing-on-supabase

Platform terms and quotas change; re-check before deployment or reliance on a free allowance.
