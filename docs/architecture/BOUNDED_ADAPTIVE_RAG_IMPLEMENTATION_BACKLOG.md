# Implementation Backlog — Bounded Adaptive RAG v1.0

**Baseline:** Approved [Technical Architecture and Interface Specification v1.0](../architecture/BOUNDED_ADAPTIVE_RAG_TECHNICAL_SPEC.md)  
**Status:** Proposed traceable delivery plan. Each batch is tracked by a GitHub Issue.

## Batch 0 — Baseline and technical validation
1. Publish and cross-link the approved architecture specification and reconciled roadmap.
2. Validate Render Free index storage, startup, memory, replacement and rollback.
3. Establish a source-backed evaluation-set structure and identify measurable resource budgets.

**Exit gate:** documented storage/delivery decision and reviewed baseline documentation. No production behaviour changed.

## Batch 1 — General retrieval foundation
1. Define stable source, document and passage records.
2. Preserve list groups, headings, table headers/rows and document order.
3. Correct NID procedure-order regression and short-passage loss.
4. Modularise general retrieval; remove topic-specific ranking branches.
5. Convert NID and IPA cases into source-passage-based evaluation fixtures.

**Exit gate:** general regression suite passes without agency-specific retrieval rules.

## Batch 2 — Source ingestion and versioned index
1. Add governed source metadata and source lifecycle states.
2. Implement exact-URL offline fetch and structure-aware extraction.
3. Build reproducible versioned index artifact.
4. Validate read-only runtime loading and rollback.
5. Detect broken, changed, stale and superseded sources for review.

**Exit gate:** retrieval uses a validated index rather than fetching every source for every question.

## Batch 3 — Bounded adaptive retrieval
1. Implement validated QuestionPlan.
2. Implement evidence-sufficiency gate.
3. Add one optional reformulation/decomposition and second retrieval.
4. Enforce maximum retry and resource budgets.
5. Test ambiguous, compound and terminology-mismatch questions.

**Exit gate:** no path can trigger more than one additional retrieval.

## Batch 4 — Evidence verification and safe answers
1. Implement stable claim-to-passage citation mapping.
2. Validate citation IDs and passage membership.
3. Add high-risk fact checks for amounts, dates, deadlines, form codes, agencies and conditions.
4. Handle conflicting, stale, incomplete and absent evidence.
5. Implement controlled regeneration once and extractive/source-linked fallback.

**Exit gate:** unsupported official claims are rejected, qualified or omitted in the reviewed test set.

## Batch 5 — Operational reliability and privacy
1. Enforce bounded API inputs, history, evidence, model calls and execution.
2. Handle provider timeouts, quota limits, cold starts and outages.
3. Minimise technical logs and avoid persistent conversation content.
4. Test prompt-injection resistance for user and retrieved content.
5. Validate monitoring and safe fallback.

**Exit gate:** operational failure modes are controlled and documented.

## Batch 6 — Evaluation and release readiness
1. Run backend, frontend, retrieval, ingestion, verifier and integration tests.
2. Conduct human-reviewed answer evaluation, including conditional and multi-agency questions.
3. Measure latency, memory, tokens and index size on actual hosting.
4. Document limitations, coverage gaps and unresolved risks.
5. Prepare a release decision report and obtain explicit approval.

**Exit gate:** reproducible evidence supports release readiness; CI success alone is not deployment approval.

## Cross-cutting acceptance rules
- No model training/fine-tuning, paid infrastructure, unrestricted crawling or arbitrary source URLs.
- No topic-specific retrieval code for individual agencies.
- New subject coverage should primarily be added through approved sources and evaluation fixtures.
- No synthetic evaluation results represented as production performance.
- No merges, production deployments, paid services, destructive actions or database migrations without explicit owner approval.


## GitHub tracking issues

- [Batch 0 — Baseline and Render index validation](https://github.com/JennyJoshua/png-public-services-assistant/issues/15)
- [Batch 1 — General retrieval foundation](https://github.com/JennyJoshua/png-public-services-assistant/issues/16)
- [Batch 2 — Governed source ingestion and versioned index](https://github.com/JennyJoshua/png-public-services-assistant/issues/17)
- [Batch 3 — Bounded adaptive retrieval](https://github.com/JennyJoshua/png-public-services-assistant/issues/18)
- [Batch 4 — Evidence verification and safe answers](https://github.com/JennyJoshua/png-public-services-assistant/issues/19)
- [Batch 5 — Operational reliability, privacy and security](https://github.com/JennyJoshua/png-public-services-assistant/issues/20)
- [Batch 6 — Evaluation and release readiness](https://github.com/JennyJoshua/png-public-services-assistant/issues/21)

The issues are planning and tracking records. They do not independently authorise merges, deployments, paid services, destructive actions or database migrations.
