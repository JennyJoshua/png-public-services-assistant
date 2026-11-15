# PNG Public Services Assistant

A mobile-first assistant designed to help people in Papua New Guinea find trustworthy public-service information, understand procedures and forms, and prepare documents.

## Controlling technical baseline

The project-owner-approved **Bounded Adaptive RAG Technical Architecture and Interface Specification v1.0** is the controlling technical baseline for implementation.

- [Technical Architecture and Interface Specification v1.0](docs/architecture/BOUNDED_ADAPTIVE_RAG_TECHNICAL_SPEC.md)
- [Bounded Adaptive RAG Architecture Decision and Delivery Roadmap](docs/architecture/BOUNDED_ADAPTIVE_RAG_DECISION.md)
- [Bounded Adaptive RAG Implementation Backlog v1.0](docs/architecture/BOUNDED_ADAPTIVE_RAG_IMPLEMENTATION_BACKLOG.md)

Implementation proposals and pull requests must be reconciled against these documents. Proposed implementation choices do not override the approved baseline unless the project owner explicitly approves a material change.

## Product direction

The application provides a conversational interface for:
- Evidence-grounded answers about PNG public services, procedures, eligibility, required documents, and responsible institutions.
- General-knowledge answers for ordinary questions, clearly distinguished from official PNG guidance.
- Source links and dates so users can check information themselves.
- Later, document generation from user-approved samples, preview, and DOCX/PDF export.

## Principles

- Mobile-first, including practical use on Android devices.
- No forced registration just to ask a public information question.
- Free/open-source-first, with no mandatory paid AI API dependency.
- Replaceable AI, retrieval, OCR, and storage providers.
- Clear distinction between verified facts, general guidance, and unknown information.
- Privacy and security by design; private uploads are not public knowledge sources.
- Users review and approve generated documents. The assistant does not submit forms, sign, certify, or make declarations on a user's behalf.
- Approved exact-URL sources only; no unrestricted crawling or arbitrary user-supplied source URLs.
- No model training or fine-tuning, and no persistent conversation history.
- Do not assume Render's local filesystem is durable.
- Do not claim retrieval or answer-quality improvements without evaluation evidence.

## Current implementation

The repository contains a Next.js/TypeScript frontend and a Python/FastAPI backend. The current live retrieval implementation still follows the earlier page-fetch-and-rank path; it has **not yet been connected to the versioned index artifact** required by the approved architecture.

The approved-source ingestion and versioned-index foundations have been added:
- General lexical retrieval, vocabulary aliases, context expansion, and improved preservation of headings, lists, and table labels.
- A strict versioned index-artifact schema and loader.
- An offline builder restricted to exact URLs in the curated source registry.
- A manually triggered, ephemeral GitHub Actions audit that validates an index artifact and removes generated source content after the run.

The latest controlled audit indexed 4 of 15 registered pages and produced 163 passages. This is a partial technical result, not proof of full source coverage, source authority, legal reuse permission, answer quality, or production index integration. See [the audit run](https://github.com/JennyJoshua/png-public-services-assistant/actions/runs/43690260410).

## Delivery status

Implementation is governed by the seven batches in the approved [Implementation Backlog v1.0](docs/architecture/BOUNDED_ADAPTIVE_RAG_IMPLEMENTATION_BACKLOG.md). Its detailed work items and acceptance criteria are authoritative.

Recent merged implementation PRs:
- PR #23 — general-purpose retrieval foundation.
- PR #24 — strict versioned index-artifact foundation.
- PR #25 — representative approved-source index builder.
- PR #26 — controlled ephemeral source-index audit workflow.
- PR #27 — source-index audit CLI import-path correction.

Important outstanding work includes completing Render artifact-delivery validation, establishing the reviewed retrieval evaluation set, enriching governed source metadata, integrating the versioned index into online retrieval, implementing source-change monitoring, and completing Batches 3–6.

Passing CI or a successful artifact audit does not constitute release readiness or deployment approval.

## Hosting and provider constraints

The existing hosting direction is Render, with the current free-service constraints respected. Free-service filesystem changes are ephemeral; the authoritative index must not depend on mutable runtime files or an assumed persistent disk. The approved architecture requires measured startup, memory, packaging, replacement, and rollback validation before relying on deployed index artifacts.

The existing Groq arrangement remains the preferred model-provider direction within the approved free-service constraint. Secrets remain server-side. No paid plan or service is authorised by this README.

## Approval gates

Explicit project-owner approval is required before:
- Merging implementation pull requests.
- Production deployments or production behaviour/configuration changes.
- Paid services or upgrades.
- Destructive actions or database migrations.
- Material scope or architecture changes.

Technical investigation, documentation, and implementation may proceed within the approved baseline and existing permissions, but every implementation PR must be reviewed before merge.

## Document generation

Document generation remains deferred until approved sample documents and the relevant implementation scope are ready.

## License

To be selected and confirmed before public code reuse or distribution.
