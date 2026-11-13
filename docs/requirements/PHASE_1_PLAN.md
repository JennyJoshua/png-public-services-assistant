# Phase 1 Implementation Plan — Public Information Chat

## 1. Objective
Deliver a usable mobile-first chat application that answers a limited set of PNG public-service questions using traceable public evidence. Phase 1 does not include document generation, OCR, or form filling.

## 2. Scope
Included:
- Repository and engineering foundations.
- Responsive chat UI.
- Backend API and health endpoint.
- Replaceable text-generation adapter.
- Source registry and ingestion path for a small curated source set.
- Retrieval and answer citations.
- Anonymous session approach.
- Basic rate limiting, validation, logging, and tests.
- Deployment feasibility assessment.

Excluded:
- Paid model/API services.
- Production deployment without approval.
- Full national coverage or unsupported claims of completeness.
- User document uploads, OCR, form filling, and generated-document exports.
- Automated submission to government agencies.

## 3. Work packages

### P1 — Foundation
- Establish frontend/backend project structure and supported runtime versions.
- Add environment-variable examples without secrets.
- Configure formatting, linting, type checks, and tests.
- Add CI checks and secure dependency practices.
Acceptance: clean install/build/test instructions; CI validates the baseline; no secrets committed.

### P2 — Chat experience
- Build responsive conversation interface with accessible controls.
- Add loading, empty, error, retry, and citation states.
- Support narrow Android screens and low-bandwidth behavior.
Acceptance: a user can ask a question, read the response, open citations, and recover from an API failure on a mobile viewport.

### P3 — API and sessions
- Implement health and chat-session/message endpoints.
- Validate request sizes and input.
- Implement short-lived anonymous sessions and ownership checks.
Acceptance: API contract tests cover valid, invalid, expired, and unauthorized requests.

### P4 — Source registry
- Define source metadata and ingestion workflow.
- Start with a small set of high-value official PNG public-service sources that can be verified.
- Extract and chunk documents with provenance.
- Track publication, retrieval, and last-checked dates.
Acceptance: every indexed chunk traces to a source and document version; stale/unavailable sources can be marked.

### P5 — Retrieval and answer generation
- Implement retrieval over approved sources and a normalized evidence interface.
- Add provider adapter and configurable fallback behavior.
- Require citations for service-specific factual claims.
- Handle missing, stale, and contradictory evidence safely.
Acceptance: benchmark questions return grounded answers with valid citations or clearly abstain; fabricated citations fail tests.

### P6 — Security and observability
- Add rate limits, safe errors, structured request IDs, secret handling, and access tests.
- Ensure private session content is not exposed across sessions.
- Record operational metrics without unnecessary sensitive content.
Acceptance: authorization and abuse-control tests pass; no critical/high security issue remains open.

### P7 — Deployment feasibility and review
- Evaluate current free-tier limits, runtime support, data region, cold starts, persistence, and resource needs.
- Do not deploy publicly until the user approves the proposed target and release.
Acceptance: documented deployment recommendation and rollback plan; explicit approval obtained before production deployment.

## 4. Initial test matrix
- Official source directly answers the question.
- Multiple sources agree.
- Official and secondary sources conflict.
- Source is stale or withdrawn.
- No evidence exists.
- Prompt injection appears in retrieved content.
- Citation URL is invalid or not among retrieved sources.
- Anonymous session expires.
- Session ID is guessed or accessed by another client.
- Provider times out or returns malformed output.
- Mobile layout, keyboard navigation, and network interruption.

## 5. Phase 1 completion criteria
- Public user can ask a question without mandatory registration.
- Answer is understandable and grounded in retrieved PNG public-service evidence.
- Citations identify actual retrieved sources and relevant dates.
- Missing or conflicting evidence is clearly communicated.
- Mobile experience is usable.
- Tests cover critical functional and security paths.
- No paid dependency or production deployment has been introduced without approval.

## 6. Execution controls
Work may proceed routinely on a feature branch. Stop and seek approval for material scope changes, paid services, production deployments, destructive operations, or merging to main. Report blockers with the exact decision needed; do not ask the user to perform technical steps that can be completed through the available GitHub integration.
