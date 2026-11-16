# PNG Public Services Assistant

A mobile-first assistant designed to help people in Papua New Guinea find trustworthy public-service information, understand procedures and forms, and prepare documents.

## Controlling technical baseline

The project-owner-approved **Simplified Hybrid RAG Architecture and Delivery Plan v1.1** is the active technical baseline, merged through PR #41 (merge commit `eb363795fc74822913c11c8227041fb95919329a`). It supersedes v1.0 for future work. The original v1.0 documents remain available as historical design records.

- [Simplified Hybrid RAG Architecture and Delivery Plan v1.1](docs/architecture/SIMPLIFIED_HYBRID_RAG_ARCHITECTURE_V1.1.md)
- [Simplified Hybrid RAG Implementation Backlog v1.1](docs/architecture/SIMPLIFIED_HYBRID_RAG_IMPLEMENTATION_BACKLOG_V1.1.md)
- [Historical Bounded Adaptive RAG Technical Architecture v1.0](docs/architecture/BOUNDED_ADAPTIVE_RAG_TECHNICAL_SPEC.md)
- [Historical v1.0 Architecture Decision and Delivery Roadmap](docs/architecture/BOUNDED_ADAPTIVE_RAG_DECISION.md)
- [Historical v1.0 Implementation Backlog](docs/architecture/BOUNDED_ADAPTIVE_RAG_IMPLEMENTATION_BACKLOG.md)

The seven existing GitHub batch issues remain the delivery tracker. Their active scope and acceptance criteria are being reconciled to v1.1 without creating duplicate issues.

## Engineering delivery standard

The owner-adopted [Joshua AI Software Delivery System (JASDS) v1.0](docs/engineering/AI_ASSISTED_CONTINUOUS_DELIVERY.md) defines the portfolio delivery standard currently being piloted in this repository. It governs workflow and quality practices only; it does not change the approved RAG architecture, backlog or project-owner approval gates.

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
- Prioritise approved authoritative sources; permit bounded general-web discovery only when approved evidence is insufficient, with source classes and explicit uncertainty. No unrestricted crawling or arbitrary user-supplied source URLs.
- No model training or fine-tuning, and no persistent conversation history.
- Do not assume Render's local filesystem is durable.
- Do not claim retrieval or answer-quality improvements without evaluation evidence.

## Current implementation

The repository contains a Next.js/TypeScript frontend and a Python/FastAPI backend. The current live retrieval implementation fetches the fixed approved URL registry, extracts pages and ranks passages with BM25 before sending bounded evidence to the configured Groq model. General internet search, source classification, evidence sufficiency and claim-level citation verification are not yet implemented.

The approved-source ingestion and versioned-index foundations have been added:
- General lexical retrieval, vocabulary aliases, context expansion, and improved preservation of headings, lists, and table labels.
- A strict versioned index-artifact schema and loader.
- An offline builder restricted to exact URLs in the curated source registry.
- A manually triggered, ephemeral GitHub Actions audit that validates an index artifact and removes generated source content after the run.

The latest controlled audit indexed 4 of 15 registered pages and produced 163 passages. This is a partial technical result, not proof of full source coverage, source authority, legal reuse permission, answer quality, or production index integration. See [the audit run](https://github.com/JennyJoshua/png-public-services-assistant/actions/runs/43690260410).

## Delivery status

Implementation is governed by the seven existing GitHub batch issues, reconciled to the approved [Simplified Hybrid RAG Backlog v1.1](docs/architecture/SIMPLIFIED_HYBRID_RAG_IMPLEMENTATION_BACKLOG_V1.1.md).

Recent merged implementation PRs:
- PR #23 — general-purpose retrieval foundation.
- PR #24 — strict versioned index-artifact foundation.
- PR #25 — representative approved-source index builder.
- PR #26 — controlled ephemeral source-index audit workflow.
- PR #27 — source-index audit CLI import-path correction.

Important outstanding work includes evaluating compliant free search providers for PNG/Pacific relevance, building a provider-neutral evidence interface, adding bounded general-web discovery, source classification, evidence sufficiency and citation verification, then completing security, reliability and evaluation. Full production index delivery is optional and must be justified by measured value.

Passing CI or a successful artifact audit does not constitute release readiness or deployment approval.

## Hosting and provider constraints

The existing hosting direction is Render, with the current free-service constraints respected. GitHub is the only permanent application knowledge/artifact store initially. Render Free filesystem changes are ephemeral; runtime behaviour must not depend on mutable files surviving restart, redeploy or spin-down. Optional read-only index artifacts may be packaged with deployments only where justified and validated.

**Approved pilot AI-provider constraint:** retain the existing free Groq-hosted LLM arrangement. Keep Groq credentials server-side, verify the configured model's availability and rate limits, and handle provider failures safely. Do not introduce a paid OpenAI API dependency, paid Groq tier, paid fallback provider, or other recurring AI cost without explicit owner approval. The exact configured model identifier must be confirmed from non-secret configuration before it is documented as fact. No paid plan or service is authorised by this README.

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
