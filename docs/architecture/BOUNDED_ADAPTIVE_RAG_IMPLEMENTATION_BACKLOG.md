# Implementation Backlog — Bounded Adaptive RAG v1.0 (Historical)

**Status:** Historical backlog; superseded for new work by the owner-approved [Simplified Hybrid RAG Architecture and Delivery Plan v1.1](./SIMPLIFIED_HYBRID_RAG_ARCHITECTURE_V1.1.md).  
**Purpose:** Preserve the original seven-batch v1.0 plan and its traceability. The active v1.1 scope is tracked in the GitHub issues listed below.

> Do not use this historical backlog to require full production index integration where v1.1 makes indexing optional. Where a v1.0 item conflicts with v1.1, follow v1.1.

## Historical v1.0 batches

### Batch 0 — Baseline and technical validation
1. Publish and cross-link the approved architecture specification and reconciled roadmap.
2. Validate Render Free index storage, startup, memory, replacement and rollback.
3. Establish a source-backed evaluation-set structure and identify measurable resource budgets.

### Batch 1 — General retrieval foundation
1. Define stable source, document and passage records.
2. Preserve list groups, headings, table headers/rows and document order.
3. Correct NID procedure-order regression and short-passage loss.
4. Modularise general retrieval; remove topic-specific ranking branches.
5. Convert NID and IPA cases into source-passage-based evaluation fixtures.

### Batch 2 — Source ingestion and versioned index
1. Add governed source metadata and source lifecycle states.
2. Implement exact-URL offline fetch and structure-aware extraction.
3. Build reproducible versioned index artifact.
4. Validate read-only runtime loading and rollback.
5. Detect broken, changed, stale and superseded sources for review.

### Batch 3 — Bounded adaptive retrieval
1. Implement validated QuestionPlan.
2. Implement evidence-sufficiency gate.
3. Add one optional reformulation/decomposition and second retrieval.
4. Enforce maximum retry and resource budgets.
5. Test ambiguous, compound and terminology-mismatch questions.

### Batch 4 — Evidence verification and safe answers
1. Implement stable claim-to-passage citation mapping.
2. Validate citation IDs and passage membership.
3. Add high-risk fact checks for amounts, dates, deadlines, form codes, agencies and conditions.
4. Handle conflicting, stale, incomplete and absent evidence.
5. Implement controlled regeneration once and extractive/source-linked fallback.

### Batch 5 — Operational reliability and privacy
1. Enforce bounded API inputs, history, evidence, model calls and execution.
2. Handle provider timeouts, quota limits, cold starts and outages.
3. Minimise technical logs and avoid persistent conversation content.
4. Test prompt-injection resistance for user and retrieved content.
5. Validate monitoring and safe fallback.

### Batch 6 — Evaluation and release readiness
1. Run backend, frontend, retrieval, ingestion, verifier and integration tests.
2. Conduct human-reviewed answer evaluation, including conditional and multi-agency questions.
3. Measure latency, memory, tokens and index size on actual hosting.
4. Document limitations, coverage gaps and unresolved risks.
5. Prepare a release decision report and obtain explicit approval.

## Active v1.1 GitHub tracking issues

The owner-approved v1.1 plan changes the delivery emphasis to governed, web-first hybrid retrieval. The active work is tracked in these issues:

- [Batch 0 — Reconcile baseline, source policy and search-provider feasibility](https://github.com/JennyJoshua/png-public-services-assistant/issues/15)
- [Batch 1 — General retrieval foundation](https://github.com/JennyJoshua/png-public-services-assistant/issues/16)
- [Batch 2 — Governed web discovery and optional knowledge ingestion](https://github.com/JennyJoshua/png-public-services-assistant/issues/17)
- [Batch 3 — Retrieval planning and evidence sufficiency](https://github.com/JennyJoshua/png-public-services-assistant/issues/18)
- [Batch 4 — Evidence verification and safe answers](https://github.com/JennyJoshua/png-public-services-assistant/issues/19)
- [Batch 5 — Operational reliability, privacy and security](https://github.com/JennyJoshua/png-public-services-assistant/issues/20)
- [Batch 6 — Evaluation and release readiness](https://github.com/JennyJoshua/png-public-services-assistant/issues/21)

## Cross-cutting v1.1 acceptance rules

- Search approved sources first; general discovery is bounded and used only when approved evidence is insufficient.
- Keep evidence provenance and source class visible; general web content must never be silently promoted to official status.
- Respect source terms, robots policies, rate limits and access restrictions; no paywall bypass or anti-bot evasion.
- Keep provider interfaces replaceable and use only a suitable compliant free provider unless the owner explicitly approves a cost.
- Enforce SSRF, redirect, DNS/IP, timeout, content-type, byte, concurrency, page and model-token controls.
- Do not silently switch LLM providers or models.
- Retain optional indexing only where measured value justifies it; no hosted vector database or persistent Render disk is required.
- No synthetic evaluation results represented as production performance.
- Production deployments, paid services, destructive actions, database migrations and material scope changes remain subject to explicit owner approval.

These issues are planning and tracking records; the current v1.1 architecture and the owner approval gates govern delivery.
