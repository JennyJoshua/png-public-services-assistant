# Bounded Adaptive RAG — Architecture Decision and Delivery Roadmap

**Status:** Reconciled to approved Technical Architecture and Interface Specification v1.0  
**Controlling baseline:** [BOUNDED_ADAPTIVE_RAG_TECHNICAL_SPEC.md](./BOUNDED_ADAPTIVE_RAG_TECHNICAL_SPEC.md)  
**Approval:** Project owner approved v1.0 on 15 November 2026.

## Decision

Adopt bounded adaptive RAG. The model may interpret, reformulate and answer; application code controls approved-source access, retrieval, retry limits, evidence verification, citation integrity, resource budgets and abstention.

The online request lifecycle is: input guard → structured question plan → first retrieval → evidence-sufficiency gate → at most one additional retrieval → evidence assembly → answer generation → deterministic verification → response composition or safe fallback.

No unbounded agent/tool loop, model training, unrestricted crawling, arbitrary URL ingestion or persistent conversation storage is in scope.

## Architecture decisions

### Sources and index
- Use a curated exact-URL source registry.
- Represent authority tier, document type, jurisdiction, language, dates, fetch/review state and content hash as source metadata.
- Preserve document structure: headings, list groups, table headers/rows, section paths and document order.
- Use stable document and passage IDs.
- Build a reproducible, versioned index offline where practical.
- Load the index read-only at runtime only after validating Render storage, memory, startup, replacement and rollback behaviour. Do not assume the Render filesystem is durable.

### Retrieval
- Keep retrieval strategies modular and general-purpose.
- Preserve parent-section context; do not discard short meaningful checklist items.
- Do not implement agency- or topic-specific ranking rules.
- Calibrate relevance/sufficiency thresholds against a reviewed evaluation set.
- Permit at most one bounded reformulation/decomposition and second retrieval.
- Defer dense retrieval, embeddings and reranking until evaluation demonstrates a need and hosting tests establish feasibility.

### Evidence and answers
- Map each material official claim to supplied passage IDs.
- Validate citation IDs and evidence support independently of the model.
- Treat fees, amounts, dates, deadlines, form codes, agency names and eligibility conditions as high-risk facts.
- Do not mistake the presence of a number in a passage for proof that it is attached to the correct condition.
- Surface conflicting or stale sources; abstain or provide only supported parts when evidence is insufficient.
- Use a controlled source-linked/extractive fallback when generation or verification fails.

### Operational controls
- Keep current Render/Groq arrangement as default.
- Measure tokens, latency, memory, index size and concurrency before fixing budgets.
- Bound requests, history, evidence, retries and model calls.
- Keep secrets server-side and minimise logging.
- Treat retrieved text as untrusted data and test prompt-injection resistance.

## Validation gates

1. **Storage gate:** demonstrate index artifact loading, startup, memory, replacement and rollback on the actual Render service.
2. **Retrieval gate:** pass structure-aware extraction and general regression tests, including NID procedure ordering and IPA checklist fixtures.
3. **Adaptive gate:** prove the retry limit cannot exceed one additional retrieval.
4. **Evidence gate:** test claim-to-passage mapping, citation integrity, high-risk facts, conflicts and abstention.
5. **Operational gate:** test provider failures, quotas, privacy, prompt injection and bounded resource use.
6. **Release gate:** publish reproducible test results, limitations and measured resource use; obtain explicit owner approval before merge/deployment.

## Delivery phases

- **Phase 0 — Baseline and validation:** publish the approved specification; reconcile this roadmap; validate Render index delivery; define evaluation data and technical budgets only after measurement.
- **Phase 1 — General retrieval foundation:** stable structures, structure-aware extraction, modular retrieval, regression fixtures.
- **Phase 2 — Source ingestion and index:** source metadata, offline build, versioned index, change detection and review.
- **Phase 3 — Bounded adaptation:** question planning, sufficiency gate and one controlled second retrieval.
- **Phase 4 — Verification:** claim-to-passage mapping, high-risk fact checks, abstention and fallback.
- **Phase 5 — Operational readiness:** quotas, monitoring, privacy, human-reviewed evaluation and release decision.

## Existing pull requests

- PR #11 is intermediate work. Retain the central system prompt and generalisation direction, but correct retrieval ordering, short-passage handling, ranking and evidence selection before merge.
- PR #10's IPA-specific retrieval rule is excluded. Preserve useful official IPA checklist examples as general evaluation fixtures.
- Neither PR is approved for merge by this roadmap.

## Data Analysis rule

Do not fabricate statistical or retrieval-performance conclusions. If a task genuinely requires the dedicated Data Analysis capability and it is unavailable, stop that analysis and prepare a ready-to-paste Claude handover. Ordinary code inspection, deterministic tests and qualitative architecture review may proceed without that capability.

## Approval boundaries

This document and the approved technical specification do not authorise production deployment, paid services, destructive actions, database migrations, material scope changes or merging existing pull requests. Those require explicit owner approval.
