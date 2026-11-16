# Simplified Hybrid RAG Implementation Backlog v1.1

**Baseline:** [Simplified Hybrid RAG Architecture and Delivery Plan v1.1](SIMPLIFIED_HYBRID_RAG_ARCHITECTURE_V1.1.md)  
**Status:** Active delivery plan. The seven existing GitHub issues remain the tracking structure; no duplicate batch issues are to be created.  
**Supersedes:** Bounded Adaptive RAG Implementation Backlog v1.0 for future work. The v1.0 file is retained as a historical record.

## Delivery strategy

Use approved sources first, then bounded general-web discovery when approved evidence is insufficient. Retrieve and classify evidence before sending it to the existing free Groq model. Keep search-provider choice replaceable. Optional indexed knowledge is permitted where it provides measurable value; full production index integration is not a prerequisite.

### Batch 0 — Reconcile baseline, source policy and provider feasibility (Issue #15)
1. Publish v1.1 as the active architecture and reconcile README/backlog/issue references.
2. Retain the non-production Render probe evidence and clearly document what it proves and does not prove.
3. Assess free or no-cost search-provider candidates: terms, quotas, geographic/Papua New Guinea and Pacific result quality, downstream page-fetch permission, privacy, reliability and latency.
4. Select a provider only if a suitable compliant free option is evidenced. Otherwise record approved-source-only mode as the current implementation boundary.
5. Define source classes, source-policy rules and a source-backed evaluation-fixture format.
6. Keep the existing Groq free-tier arrangement; no paid fallback or silent model switch.

**Exit gate:** architecture and issue tracking reconciled; documented provider decision (provider selected with evidence, or no suitable free provider); source policy and evaluation-fixture approach defined. No production runtime change.

### Batch 1 — Modular retrieval and provider-neutral evidence foundation (Issue #16)
1. Define common source, search-result, fetched-document and evidence records with stable provenance.
2. Define a provider-neutral search interface and deterministic fake/test provider.
3. Separate approved-source retrieval, general search, page fetching, extraction, ranking and context assembly.
4. Preserve meaningful headings, lists, short checklist items, tables, order and source identity.
5. Reuse and protect NID/IPA regressions; add unsupported/missing-evidence fixtures (including provincial service-count questions).
6. Keep ranking topic-independent and deterministic tests independent of live search/model calls.

**Exit gate:** modular contracts and deterministic tests pass; no live provider dependency required to test core retrieval.

### Batch 2 — Governed web discovery and optional knowledge ingestion (Issue #17)
1. Complete source metadata and lifecycle policy; unknown metadata remains explicitly unknown.
2. Integrate only the provider selected and approved through Batch 0; normalise results.
3. Search approved sources first; invoke general discovery only when the sufficiency policy says it is needed.
4. Fetch a bounded set of candidate pages with HTTPS, DNS/IP, redirect, timeout, byte, content-type and concurrency controls.
5. Respect robots, terms, rate limits and access restrictions; do not bypass login, paywalls or anti-bot controls.
6. Classify provenance A/B/C/D and keep unreviewed general results separate from approved official sources.
7. Retain optional reproducible GitHub-stored indexing only for material where it adds measurable value; do not require hosted vector DB or persistent Render disk.

**Exit gate:** source provenance and provider limits are inspectable; untrusted results cannot become approved sources automatically; retrieval is bounded and tested.

### Batch 3 — Question planning and evidence sufficiency (Issue #18)
1. Add a validated, provider-neutral retrieval plan for intent, jurisdiction, query and sub-questions.
2. Implement evidence sufficiency based on directness, relevance, authority, freshness and consistency.
3. Allow at most one bounded additional search/retrieval pass.
4. Deduplicate evidence and enforce request, time, page, byte, evidence and model budgets.
5. Test ambiguous, compound, terminology-mismatch and follow-up questions.

**Exit gate:** one-retry maximum is enforced in code/tests; no unbounded agent/tool loop; thresholds are calibrated from reviewed fixtures.

### Batch 4 — Evidence verification and safe answers (Issue #19)
1. Preserve stable evidence IDs and map material claims to supplied passages.
2. Validate citation identity, URL and source class.
3. Apply stronger verification to fees, dates, deadlines, legal requirements, eligibility, form codes, agency responsibilities, counts and service availability.
4. Surface conflicts, stale evidence and missing conditions.
5. Permit at most one controlled correction; otherwise abstain or provide a source-linked partial answer.
6. Clearly distinguish official evidence from institutional and general-web material.

**Exit gate:** unsupported material claims and invalid citations are rejected or qualified in the reviewed evaluation set.

### Batch 5 — Security, privacy and operational reliability (Issue #20)
1. Enforce SSRF protections, DNS/IP and redirect validation, safe content handling and prompt-injection resistance.
2. Bound input, history, concurrency, network requests, execution time, evidence and model tokens.
3. Handle search-provider and Groq timeouts, rate limits, quotas, outages and malformed responses.
4. Keep secrets server-side and minimise logs; do not persist conversation content.
5. Handle Render cold starts and optional artifact load failures safely.
6. Add privacy-preserving operational metrics for latency, errors, source freshness and provider usage.

**Exit gate:** failure modes are controlled and security/privacy behaviour is tested and documented.

### Batch 6 — Evaluation and release readiness (Issue #21)
1. Run frontend, backend, retrieval, provider, extraction, verification and integration suites.
2. Evaluate approved-source, general-web, missing-answer, conflict, stale, ambiguous, high-impact and adversarial cases.
3. Human-review correctness, evidence support, authority classification, citation precision and abstention.
4. Measure actual latency, requests, bytes, model tokens, provider quotas, Render memory/CPU and any optional index size.
5. Document coverage gaps, limitations, unresolved risks and rollback.
6. Produce a release-readiness report. Release/production deployment remains subject to the applicable approval gate.

**Exit gate:** reproducible evidence supports release readiness; CI success alone is not release or deployment approval.

## Cross-cutting constraints
- Existing free Groq inference only; no paid provider, paid fallback or silent model/provider switch.
- No paid search/scraping, database, vector store, storage or hosting without explicit owner approval.
- No unrestricted crawling, arbitrary user URLs, prohibited SERP scraping, paywall/login bypass or anti-bot evasion.
- No topic-specific retrieval branches; add subject coverage through source policy and evaluation fixtures.
- General web content never becomes authoritative merely because it was retrieved.
- GitHub is the only permanent application knowledge/artifact store initially; Render Free filesystem is ephemeral.
- Keep project collections and policies isolated; no cross-project retrieval or private-data sharing.
- Preserve existing tests and historical issue/PR evidence.
- Production deployments, destructive changes, hosted migrations and material scope changes remain gated.

## Existing GitHub tracking issues
- [#15 — Batch 0: baseline, source policy and provider feasibility](https://github.com/JennyJoshua/png-public-services-assistant/issues/15)
- [#16 — Batch 1: modular retrieval foundation](https://github.com/JennyJoshua/png-public-services-assistant/issues/16)
- [#17 — Batch 2: governed web discovery and optional ingestion](https://github.com/JennyJoshua/png-public-services-assistant/issues/17)
- [#18 — Batch 3: question planning and evidence sufficiency](https://github.com/JennyJoshua/png-public-services-assistant/issues/18)
- [#19 — Batch 4: evidence verification and safe answers](https://github.com/JennyJoshua/png-public-services-assistant/issues/19)
- [#20 — Batch 5: security, privacy and reliability](https://github.com/JennyJoshua/png-public-services-assistant/issues/20)
- [#21 — Batch 6: evaluation and release readiness](https://github.com/JennyJoshua/png-public-services-assistant/issues/21)
