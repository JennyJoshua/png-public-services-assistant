# PNG Public Services Assistant

A mobile-first assistant designed to help people in Papua New Guinea find trustworthy public-service information, understand procedures and forms, and prepare documents.

## Controlling technical baseline

The project-owner-approved **Simplified Hybrid RAG Architecture and Delivery Plan v1.1** is the active technical baseline. It was approved and merged through PR #41. The earlier Bounded Adaptive RAG v1.0 documents are retained as historical design and implementation records; they no longer control new implementation decisions where v1.1 differs.

- [Simplified Hybrid RAG Architecture and Delivery Plan v1.1](docs/architecture/SIMPLIFIED_HYBRID_RAG_ARCHITECTURE_V1.1.md)
- [Historical Bounded Adaptive RAG Technical Specification v1.0](docs/architecture/BOUNDED_ADAPTIVE_RAG_TECHNICAL_SPEC.md)
- [Historical Bounded Adaptive RAG Decision and Roadmap](docs/architecture/BOUNDED_ADAPTIVE_RAG_DECISION.md)
- [Historical Bounded Adaptive RAG Implementation Backlog v1.0](docs/architecture/BOUNDED_ADAPTIVE_RAG_IMPLEMENTATION_BACKLOG.md)
- [Source Policy](docs/architecture/RAG_SOURCE_POLICY.md)
- [Hybrid Model Policy](docs/architecture/HYBRID_MODEL_POLICY.md)
- [Search Provider Feasibility Review — 17 November 2026](docs/research/SEARCH_PROVIDER_FEASIBILITY_2026-11-17.md)

New implementation proposals must follow v1.1, the source policy, and the active GitHub batch issues. Historical v1.0 work remains useful where compatible and is not to be deleted merely because the architecture evolved.

## Engineering delivery standard

The owner-adopted [Joshua AI Software Delivery System (JASDS) v1.0](docs/engineering/AI_ASSISTED_CONTINUOUS_DELIVERY.md) defines the portfolio delivery standard being piloted in this repository. It governs workflow and quality practices; it does not override the RAG architecture or project-owner approval gates.

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
- Replaceable AI and retrieval providers.
- Clear distinction between verified official facts, recognised institutional evidence, general web guidance, and unknown information.
- Privacy and security by design; private uploads are not public knowledge sources.
- Users review and approve generated documents. The assistant does not submit forms, sign, certify, or make declarations on a user's behalf.
- Search approved sources first; use bounded general-web discovery only when approved evidence is absent, weak, stale, or incomplete.
- No unrestricted crawling, arbitrary user-supplied source URLs, model training/fine-tuning, or persistent conversation history.
- Treat retrieved content as untrusted input, including content from official domains.
- Do not assume Render's local filesystem is durable.
- Do not claim retrieval or answer-quality improvements without evaluation evidence.

## Current implementation

The repository contains a Next.js/TypeScript frontend and a Python/FastAPI backend. The live retrieval path currently fetches and ranks the curated exact-URL source registry. General web discovery and the full v1.1 hybrid retrieval flow are not yet complete.

The repository also contains supporting foundations from the earlier v1.0 work:
- General lexical retrieval, vocabulary aliases, context expansion, and structure-aware extraction.
- A strict versioned index-artifact schema and loader.
- An offline builder restricted to exact URLs in the curated source registry.
- A manually triggered, ephemeral GitHub Actions audit that validates an index artifact and removes generated source content after the run.

The latest recorded controlled audit indexed 4 of 15 registered pages and produced 163 passages. This is a partial technical result, not proof of full source coverage, source authority, legal reuse permission, answer quality, or production index integration. See [the audit run](https://github.com/JennyJoshua/png-public-services-assistant/actions/runs/43690260410).

## Delivery status

The active v1.1 delivery work is tracked in GitHub Issues:
- [Batch 0 — Reconcile baseline, source policy and search-provider feasibility](https://github.com/JennyJoshua/png-public-services-assistant/issues/15)
- [Batch 1 — General retrieval foundation](https://github.com/JennyJoshua/png-public-services-assistant/issues/16)
- [Batch 2 — Governed web discovery and optional knowledge ingestion](https://github.com/JennyJoshua/png-public-services-assistant/issues/17)
- [Batch 3 — Retrieval planning and evidence sufficiency](https://github.com/JennyJoshua/png-public-services-assistant/issues/18)
- [Batch 4 — Evidence verification and safe answers](https://github.com/JennyJoshua/png-public-services-assistant/issues/19)
- [Batch 5 — Operational reliability, privacy and security](https://github.com/JennyJoshua/png-public-services-assistant/issues/20)
- [Batch 6 — Evaluation and release readiness](https://github.com/JennyJoshua/png-public-services-assistant/issues/21)

Recent merged implementation PRs include PRs #23–#27 (general retrieval and index foundations), PR #41 (v1.1 architecture approval), and PR #51 (safe model-provider failure diagnostics). The v1.0 index foundations remain optional supporting capabilities; production index integration is not a prerequisite for the v1.1 web-first design.

Passing CI or a successful artifact audit does not constitute release readiness or production deployment approval.

## Hosting and provider constraints

Retain the existing Render services and free Groq-hosted LLM arrangement. Keep credentials server-side. Search-provider selection must be evidence-backed for free-tier availability, terms, quotas, reliability, latency, privacy, downstream page-fetch permissions, and PNG/Pacific result quality. If no suitable compliant free search provider is established, remain in approved-source-only mode and document the limitation. Do not introduce paid search, scraping, model, fallback provider, Groq tier, or infrastructure without explicit owner approval. Never silently switch providers or models.

## Approval gates

Explicit project-owner approval is required before:
- Production deployments or production-impacting hosting/configuration changes.
- Paid services, upgrades, or new recurring costs.
- Destructive actions or database migrations.
- Material scope or architecture changes.

Implementation PRs may proceed within the approved v1.1 scope and delivery workflow. Merge only when the owner has authorised the merge under the current project workflow. CI success is necessary but does not by itself authorise production deployment.

## Document generation

Document generation remains deferred until approved sample documents and the relevant implementation scope are ready.

## License

To be selected and confirmed before public code reuse or distribution.
