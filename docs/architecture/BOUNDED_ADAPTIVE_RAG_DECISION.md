# Bounded Adaptive RAG — Historical Architecture Decision and Delivery Roadmap

**Status:** Historical; superseded where it conflicts with the owner-approved Simplified Hybrid RAG Architecture v1.1.  
**Current controlling baseline:** [Simplified Hybrid RAG Architecture and Delivery Plan v1.1](./SIMPLIFIED_HYBRID_RAG_ARCHITECTURE_V1.1.md)  
**v1.1 approval and adoption:** Project owner selected Option B — Simplified hybrid; PR #41 merged the v1.1 architecture on 16 November 2026.

> This document records the earlier v1.0 bounded-adaptive design and its historical decisions. It is retained for traceability. New work must follow v1.1 where the two documents differ.

## Historical v1.0 decision

Adopt bounded adaptive RAG. The model may interpret, reformulate and answer; application code controls approved-source access, retrieval, retry limits, evidence verification, citation integrity, resource budgets and abstention.

The online request lifecycle was: input guard → structured question plan → first retrieval → evidence-sufficiency gate → at most one additional retrieval → evidence assembly → answer generation → deterministic verification → response composition or safe fallback.

No unbounded agent/tool loop, model training, unrestricted crawling, arbitrary URL ingestion or persistent conversation storage was in scope.

## Historical architecture decisions

### Sources and index
- Use a curated exact-URL source registry.
- Represent authority tier, document type, jurisdiction, language, dates, fetch/review state and content hash as source metadata.
- Preserve document structure: headings, list groups, table headers/rows, section paths and document order.
- Use stable document and passage IDs.
- Build a reproducible, versioned index offline where practical.
- Do not assume the Render filesystem is durable.

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
- Surface conflicting or stale sources; abstain or provide only supported parts when evidence is insufficient.
- Use a controlled source-linked/extractive fallback when generation or verification fails.

### Operational controls
- Keep the then-current Render/Groq arrangement as default.
- Measure tokens, latency, memory, index size and concurrency before fixing budgets.
- Bound requests, history, evidence, retries and model calls.
- Keep secrets server-side and minimise logging.
- Treat retrieved text as untrusted data and test prompt-injection resistance.

## Historical validation gates

1. Storage: demonstrate artifact loading, startup, memory, replacement and rollback.
2. Retrieval: pass structure-aware extraction and general regression tests, including NID procedure ordering and IPA checklist fixtures.
3. Adaptive: prove the retry limit cannot exceed one additional retrieval.
4. Evidence: test claim-to-passage mapping, citation integrity, high-risk facts, conflicts and abstention.
5. Operational: test provider failures, quotas, privacy, prompt injection and bounded resource use.
6. Release: publish reproducible test results, limitations and measured resource use.

## Historical delivery phases

- Phase 0 — Baseline and validation.
- Phase 1 — General retrieval foundation.
- Phase 2 — Source ingestion and index.
- Phase 3 — Bounded adaptation.
- Phase 4 — Verification.
- Phase 5 — Operational readiness.

## Historical pull-request reconciliation

- PR #10 remains open and unmerged; its IPA-specific retrieval rule remains excluded.
- PR #11 remains open and unmerged as an intermediate branch; useful generalisation work was partly delivered through PR #23.
- PR #13 remains an open draft and was superseded by the approved baseline published through PR #14.
- PR #14 published the v1.0 specification, decision/roadmap and backlog.
- PR #22 remains open and unmerged as an earlier artifact prototype; its strict artifact foundation was superseded by PR #24.
- PRs #23–#27 are merged and provide general retrieval and optional index foundations.

## Data Analysis rule

Do not fabricate statistical or retrieval-performance conclusions. If a task genuinely requires the dedicated Data Analysis capability and it is unavailable, stop that analysis and prepare a ready-to-paste Claude handover. Ordinary code inspection, deterministic tests and qualitative architecture review may proceed without that capability.

## Approval boundaries

This historical document does not authorise production deployment, paid services, destructive actions, database migrations, material scope changes or merging existing pull requests. Apply the current project approval gates and the v1.1 baseline.
