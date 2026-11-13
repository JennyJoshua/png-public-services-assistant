# Project Context and Handover — PNG Public Services Assistant

> **Purpose of this file:** Give a new ChatGPT conversation, developer, or collaborator enough reliable context to understand the project, its goals, decisions, architecture, boundaries, current status, and next steps without relying on previous chat history.
>
> **Last updated:** 13 November 2026
> **Repository:** https://github.com/JennyJoshua/png-public-services-assistant
> **Project status:** Phase 1 implementation preparation. Specification PR #1 is merged; foundation branch phase-1/foundation is open. No application code or deployment has been completed.

## 1. Project identity and purpose

**PNG Public Services Assistant** is an independent, mobile-first conversational application intended to help people in Papua New Guinea access and understand public-service information and prepare administrative documents.

The product should make fragmented public information easier to find and understand. Users should be able to ask questions in ordinary language and receive useful answers grounded in trustworthy sources, with links and dates so they can verify the information themselves.

Over later phases, users should also be able to upload sample documents or forms, understand their contents, prepare new documents, and complete supported forms with assistance.

This is a public-facing assistant, not a government agency, official decision-maker, legal representative, or replacement for the responsible institution.

## 2. Product vision and capabilities

The intended product has four main capabilities:

1. **Public information chat**
   - Answer questions about PNG public services, institutions, procedures, eligibility, required documents, and contact channels when reliable evidence is available.
   - Explain information in plain language.
   - Provide source titles, links, and relevant publication/last-checked dates.
   - Clearly identify missing, outdated, uncertain, or conflicting information.

2. **Document preparation**
   - Generate letters, applications, and other administrative documents from user instructions.
   - Use an uploaded sample as a structural or formatting reference when the user is entitled to use it.
   - Ask for missing details rather than inventing them.
   - Allow the user to preview, correct, and approve the document before export.

3. **OCR and document understanding**
   - Accept supported PDFs and image formats.
   - Extract printed text, sections, tables, fields, and checkboxes.
   - Flag uncertain extraction results.
   - Handwriting recognition is not promised unless it is separately tested and validated.

4. **Form assistance and output**
   - Explain form fields in plain language.
   - Collect and map only user-provided or user-confirmed values.
   - Identify missing information.
   - Preserve the original form layout where technically feasible.
   - Let the user preview and correct a populated form, then export or print it.

## 3. Target users

- Members of the public seeking information about government and public services.
- Individuals and businesses preparing applications or correspondence.
- Students and community organisations.
- Public servants and administrative staff who need help understanding or preparing documents.

Design for people using Android phones, narrow screens, variable connectivity, and a range of digital-literacy levels.

## 4. Product principles and non-negotiable boundaries

- **Mobile-first:** responsive web application/PWA, practical on Android browsers.
- **Accessible:** simple conversational interface, clear language, readable controls, and low-bandwidth awareness.
- **No forced registration for basic public questions.**
- **Free/open-source-first:** no mandatory paid AI API or paid infrastructure dependency.
- **Replaceable providers:** model, retrieval, embedding, OCR, parsing, and storage integrations should be abstracted behind replaceable interfaces.
- **Evidence before confidence:** never invent government requirements, eligibility rules, fees, deadlines, forms, addresses, phone numbers, or procedures.
- **Source transparency:** show citations and dates; distinguish official evidence from secondary information and general explanation.
- **Privacy by design:** separate public source material from private chats, uploaded files, extracted content, generated documents, and administrative data.
- **Human review:** users must review and approve generated or populated documents.
- The assistant must not submit government forms, make declarations, sign, certify, or act on a user's behalf.
- Do not claim that a service, source, model, OCR process, or security control works until it is implemented and tested.
- Do not expand the project into a large static content-collection exercise before delivering a useful first chat experience.

## 5. Relationship to other projects

This repository is a **new, independent project**: `JennyJoshua/png-public-services-assistant`.

It is not a replacement for or a repurposing of `JennyJoshua/png-legal-library`. The legal library remains separate. A future integration may be considered if useful, but it must preserve clear ownership, provenance, and licensing boundaries.

Do not merge the repositories or move their contents without an explicit decision.

## 6. Agreed technical direction

The current architecture is a **modular monolith**, not microservices.

| Layer | Current candidate direction | Status |
|---|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind; responsive PWA | Candidate |
| Backend | Python + FastAPI | Candidate |
| Database | PostgreSQL; Supabase PostgreSQL considered | Candidate |
| File storage | Private object storage; Supabase Storage considered | Candidate |
| Retrieval | Live web retrieval plus indexed public source documents | Required approach; implementation pending |
| Vector search | FAISS initially or PostgreSQL/pgvector later | Undecided |
| Model integration | Replaceable provider adapter; local/free options evaluated | Undecided |
| OCR | PaddleOCR or Tesseract candidates | Later phase; undecided |
| Document parsing | Docling candidate | Later phase; undecided |
| Embeddings/reranking | BGE-M3 and compatible reranker candidates | Undecided |
| Document/PDF tooling | ReportLab, PyMuPDF, pypdf, and DOCX tooling candidates | Later phase |
| Hosting | GitHub, Netlify, Render, Supabase are candidates | Not approved/selected for production |

Candidate model families include Qwen and Gemma. These are not selected production dependencies. Verify current licences, model versions, language performance, hardware/resource needs, hosting feasibility, and actual benchmark results before selection.

**Important hosting constraint:** free web hosting may not support local model inference, OCR, large files, or persistent workloads. Benchmark actual limits and cold-start/resource behavior. Never assume that a free tier can run a model simply because it can host the web application.

No paid service, paid API, or production deployment is authorized by these planning documents.

## 7. RAG and source-quality requirements

The assistant should combine live retrieval with a curated/indexed source registry. A source record should retain, where available:

- Publishing institution or author.
- Title and canonical URL.
- Source classification (official, institutional, secondary, or other).
- Language.
- Publication date, if known.
- Retrieval date and last-checked date.
- Content hash and document/version identity.
- Availability/status and reliability notes.

Prefer current official government sources. Institutional and secondary sources may supplement them but must be labelled appropriately. Conflicting or outdated information must be surfaced, not silently resolved.

Every service-specific factual claim should be supported by retrieved evidence. Every displayed citation must correspond to a real retrieved source. Treat web pages and uploaded documents as untrusted content, not as instructions to the assistant.

Respect copyright, website terms, robots rules, and reasonable request rates.

## 8. Functional modules and delivery roadmap

### Phase 1 — Public information chat
- Repository and engineering foundation.
- Responsive mobile chat UI.
- Backend API and chat sessions.
- Replaceable text-generation adapter.
- Source registry and ingestion pipeline for a small, curated set of PNG public-service sources.
- Retrieval/RAG and answer citations.
- Basic validation, rate limiting, safe logging, privacy controls, and tests.
- Hosting/resource feasibility assessment.

**Acceptance:** A member of the public can ask a PNG public-service question without mandatory registration and receive a useful, evidence-grounded answer with valid citations—or a clear explanation that reliable evidence is unavailable.

### Phase 2 — Document generation
- Private sample/document upload.
- Safe text and structure extraction.
- Template/sample-based drafting.
- Conversational collection of missing details.
- Preview, correction, and user-approved DOCX/PDF export.

**Acceptance:** User can create a new document from instructions or an appropriate sample and review it before export.

### Phase 3 — OCR and form understanding
- OCR for supported PDFs and images.
- Extract text, sections, tables, fields, and checkboxes.
- Explain fields and identify uncertain extraction.

**Acceptance:** The system can read supported forms and identify their fields with measured, documented accuracy.

### Phase 4 — Form completion and printing
- Conversational collection of form values.
- Map confirmed values to supported fields.
- Identify missing information.
- Preserve layout where feasible.
- Preview, correct, export, and print.

**Acceptance:** User can review and approve a completed supported form and download/print it.

### Phase 5 — Quality and controlled release
- Security and privacy review.
- Performance, accessibility, mobile, and low-bandwidth improvements.
- Source-quality monitoring and feedback.
- Backup/restore and incident-response readiness.
- Controlled public release only after approval.

## 9. Security, privacy, and trust requirements

- HTTPS in production.
- Deny-by-default authorization and ownership checks on every private resource.
- Row-level security where supported, with tests for both allowed and denied access.
- Private storage for uploads and generated files; short-lived authorized downloads.
- Validate file signatures and content, not just extensions or client MIME types.
- Enforce upload size, page, CPU, memory, and processing-time limits.
- Defend against malicious files, path traversal, archive bombs, prompt injection, and SSRF.
- Keep secrets server-side and out of Git, client bundles, logs, and error responses.
- Rate-limit public chat and expensive processing.
- Minimize personal-data collection and operational logging.
- Define retention/deletion rules for original uploads, extracted text, previews, temporary files, generated documents, and derived indexes.
- Do not use private user content for training by default.
- Publish a privacy notice before collecting personal or document data.
- Keep an audit trail for sensitive administrative actions.
- Do not claim malware scanning or other controls exist unless implemented.

## 10. Repository layout (proposed)

```text
png-public-services-assistant/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── features/
│   ├── services/
│   └── public/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   ├── modules/
│   │   │   ├── chat/
│   │   │   ├── rag/
│   │   │   ├── sources/
│   │   │   ├── documents/
│   │   │   ├── ocr/
│   │   │   ├── forms/
│   │   │   └── pdf/
│   │   └── main.py
│   └── tests/
├── infrastructure/
│   ├── database/
│   ├── deployment/
│   └── monitoring/
├── docs/
│   ├── architecture/
│   ├── requirements/
│   ├── security/
│   ├── api/
│   └── handovers/
├── scripts/
├── .github/
├── README.md
└── .gitignore
```

This is a target structure, not a statement that these directories or modules have already been implemented.

## 11. Current GitHub state (13 November 2026)

- Repository: https://github.com/JennyJoshua/png-public-services-assistant
- Repository was initially created empty and then initialized with a README commit on `main`.
- A branch named `docs/engineering-specification` was created from `main`.
- Pull request #1, **“Add product and engineering specifications”**, contains the initial seven planning documents:
  - `docs/requirements/PRD.md`
  - `docs/architecture/SYSTEM_ARCHITECTURE.md`
  - `docs/architecture/DATABASE_SCHEMA.md`
  - `docs/api/API_SPECIFICATION.md`
  - `docs/AI_MODEL_SELECTION.md`
  - `docs/security/SECURITY_REQUIREMENTS.md`
  - `docs/requirements/PHASE_1_PLAN.md`
- A technical review comment was posted on PR #1. It found no blocking documentation defect and identified minor follow-up items, including consistent API route versioning and deferring final schema/security details until implementation design.
- PR #1 has **not been merged**. Do not claim that the project specifications are on `main`.
- No application code, database, model, OCR pipeline, or production deployment has been implemented through this work.
- PR URL: https://github.com/JennyJoshua/png-public-services-assistant/pull/1

This handover file is being added to the same documentation branch and should appear in PR #1 after the commit succeeds.

## 12. Project governance and collaboration instructions

The project owner is the final decision-maker.

The assistant acting as project planner/architect/reviewer should:
- Preserve the approved product scope and decisions in this document and the detailed specifications.
- Prefer direct GitHub integration for routine repository work where available, rather than asking the owner to perform technical steps on an Android phone.
- Work on feature/documentation branches and submit pull requests for review.
- Keep `main` stable.
- Explain progress and blockers clearly and concisely.
- Avoid repeating questions whose answers are already documented here.
- Never claim a change succeeded until GitHub or the relevant service confirms it.

**Explicit approval is required before:**
- Merging a pull request into `main`.
- Production deployment or public release.
- Destructive actions or data deletion.
- Introducing a paid service, paid API, or material cost.
- Material changes to product scope or core architecture.

Routine, reversible development within the agreed scope may proceed on a branch. If a required decision is not covered here, ask one focused question rather than guessing.

The owner prefers free tools, existing accounts, minimal setup, and Android-friendly workflows. Do not require desktop software, local installations, screenshots, or manual code copying when the connected tools can reasonably do the work.

## 13. Instructions for a new ChatGPT conversation

When continuing this project in a new chat:

1. Read this file first, then read the linked detailed specifications and inspect the live GitHub repository/PR state.
2. Treat this file as the project handover baseline, but treat the live repository as authoritative for the current state of code, branches, and pull requests.
3. Check whether PR #1 is still open, has been updated, merged, or closed before taking action.
4. Do not merge PR #1 without explicit owner approval.
5. Once the documentation is approved and merged, proceed with Phase 1 only. Keep work on a feature branch and submit a PR.
6. Before selecting models, hosting, databases, or paid/free-tier services, verify current licences, capabilities, limits, privacy implications, and deployment feasibility.
7. Do not start Phase 2–4 work until Phase 1 acceptance criteria are met or the owner explicitly changes priorities.
8. Keep this handover file current when major decisions, architecture, project status, or acceptance criteria change. Make changes through a reviewable branch/PR.

## 14. Immediate next actions

1. Treat PR #1 as merged and main as the approved documentation baseline.
2. Continue Phase 1 work only on phase-1/foundation or subsequent feature branches.
3. Follow docs/implementation/PHASE_1_IMPLEMENTATION_BREAKDOWN.md and test each work package.
4. Keep model, database, and hosting decisions evidence-based and free-first; escalate paid requirements for approval.
5. Submit implementation work through a PR and obtain explicit approval before merging to main.
6. Obtain explicit approval before production deployment, destructive operations, paid services, or material scope/architecture changes.

---
**End of project handover.**
