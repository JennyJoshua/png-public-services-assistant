# Bounded Adaptive RAG — Architecture Decision and Delivery Roadmap

**Status:** Accepted architectural direction; implementation roadmap  
**Date:** 2026-11-14  
**Applies to:** PNG Public Services Assistant  
**Decision owner:** Product owner

## 1. Decision

Adopt **bounded adaptive retrieval-augmented generation (RAG)** as the target architecture.

The assistant must handle a broad and changing range of PNG public-service questions without requiring developers to write a separate query rule, workflow, or canned answer for every subject. New subject coverage should normally be achieved by adding and maintaining approved information sources and improving general retrieval, not by adding topic-specific branches to application code.

The system remains inference-based. Model training and fine-tuning are not part of this plan.

## 2. Target request lifecycle

1. **Validate and understand the request.** Validate size and shape, then use the configured model to interpret the user's intent, entities, constraints, likely terminology, and information need. Do not let model-generated interpretations bypass source policy.
2. **Retrieve from the approved knowledge collection.** Search a persistent, provenance-preserving index built only from exact, reviewed HTTPS source URLs. Do not accept arbitrary user URLs or unrestricted crawling.
3. **Assess retrieval sufficiency.** Use measurable retrieval signals and, where appropriate, model-assisted relevance assessment. A model's confidence alone is not proof of evidence sufficiency.
4. **Perform at most one bounded additional retrieval.** If the first retrieval is weak and a useful alternative query or search strategy is available, make one additional retrieval attempt. Enforce strict time, token, passage, and request budgets.
5. **Generate a grounded answer.** Provide the question, bounded evidence passages, source metadata, and permanent system instructions to the model. Keep official PNG claims distinct from general background.
6. **Verify evidence and citations.** Check that citation identifiers exist, cited passages are actually supplied, and important claims have traceable supporting evidence. Apply additional checks to high-impact facts such as fees, dates, amounts, legal provisions, eligibility, required documents, and procedural steps.
7. **Answer or abstain.** Answer only to the extent supported. Clearly state what could not be verified, identify conflicts or freshness concerns, and direct users to the responsible agency when the approved evidence supports doing so.

The application must preserve a deterministic extractive fallback if the model provider is unavailable. The fallback must not pretend to have generated a verified synthesis.

## 3. Core architecture principles

- **General-purpose behaviour:** no per-topic query routing or handcrafted answer rules as the default solution.
- **Approved sources only:** every indexed item must originate from the curated source registry and an exact approved URL.
- **Traceable evidence:** preserve institution, canonical URL, page title, source type, retrieval time, content hash, and passage/document provenance.
- **Authority is explicit metadata:** do not treat a `.gov.pg` hostname alone as proof that every page is authoritative or current.
- **Freshness is visible:** track publication/effective dates when available, last-checked time, and review status. Do not confuse retrieval time with publication date.
- **Bounded model use:** cap retrieval attempts, evidence size, history, output size, timeouts, and provider calls.
- **No conversation persistence by default:** do not add conversation storage as a side effect of building the knowledge index.
- **Privacy separation:** public indexed sources must remain separate from any future private user uploads.
- **Replaceable providers:** keep chat, embedding, reranking, and storage behind interfaces. Do not add paid services without explicit owner approval.
- **No unsupported certainty:** abstention is a valid result, not a failure to be hidden.

## 4. Knowledge ingestion and persistent index

Separate source ingestion from the live question-answering request.

### Ingestion pipeline

1. Read the curated source registry.
2. Fetch only approved exact URLs, subject to reasonable time, size, and frequency limits.
3. Record fetch outcome, HTTP status, retrieval timestamp, content hash, and source metadata.
4. Extract structured content while preserving headings, paragraphs, list items, definition lists, and tables with their headers and row relationships.
5. Normalize content into documents and passages without discarding short but meaningful checklist items.
6. Attach provenance and source authority/freshness metadata to every document and passage.
7. Build or update the searchable index atomically; failed ingestion must not silently replace a known-good index with an incomplete one.
8. Report broken URLs, empty extraction, changed content, stale sources, and conflicting material.

### Persistence decision gate

The index must survive ordinary API requests and must not require fetching every website for every question. Before selecting the storage implementation, verify the actual free-tier deployment constraints and persistence guarantees.

Render's ordinary free service filesystem must not be assumed durable across restarts, redeploys, or instance replacement. Do not claim that an in-memory cache or ephemeral local file is a durable persistent index.

Evaluate the lowest-complexity options first:
- a versioned, build-generated index artifact shipped with the application, if source size and update workflow permit;
- an already-approved persistent database/storage service, if one is available and its free-tier limits and retention implications are verified;
- another no-cost option only after its durability, limits, backup/export, and operational constraints are documented.

Do not introduce a new database, paid service, account, or provider without a separate decision and approval. Keep the index format portable so the storage implementation can change without rewriting retrieval logic.

## 5. Retrieval strategy

Start with a measured, replaceable retrieval interface rather than hard-coding one algorithm.

Candidate retrieval stages:
- lexical retrieval (BM25 or equivalent);
- general query normalization and model-assisted query rewriting;
- semantic retrieval/embeddings where evaluation demonstrates a material benefit;
- optional reranking where justified by measured quality and resource limits;
- context expansion that preserves nearby checklist, table, and explanatory structure.

Do not assume BM25 alone is sufficient, and do not assume vector search is necessary before testing. Compare candidate approaches on the same reviewed evaluation set. Vocabulary aliases should be maintained as reusable data/configuration where possible, not as a growing list of topic-specific code branches.

The initial adaptive loop is limited to one additional retrieval attempt. Any future increase requires evidence that it improves answer quality enough to justify latency and provider usage.

## 6. Evidence and answer verification

Verification must go beyond checking whether a number, date, agency name, or form code appears somewhere in a cited page.

Minimum requirements:
- citation IDs in the answer must map to evidence actually supplied to the model;
- cited source URLs and metadata must be drawn from the approved registry/index;
- critical factual claims must have explicit supporting passage references;
- unsupported critical facts must be removed, qualified, or marked unverified;
- conflicting source statements must be surfaced rather than silently reconciled;
- source freshness and authority must inform qualification, not be used as automatic truth guarantees;
- the system must not invent a source, requirement, or official determination.

Begin with deterministic structural checks and a small set of high-impact claim checks. Evaluate whether a separate verifier model is affordable and reliable before adding one; do not assume another model call is free or infallible.

## 7. Source metadata model

At minimum, plan for:
- stable source ID;
- institution/publisher;
- canonical exact URL;
- page title;
- source type (law/regulation, official procedure, official form/fee schedule, agency overview, explanatory guidance, other);
- authority tier and rationale;
- jurisdiction and service area, when known;
- language;
- publication/effective date, when available;
- first-seen and last-checked timestamps;
- content hash and ingestion status;
- review status and reviewer/review date;
- supersedes/superseded-by or conflict notes, when known.

A source's metadata must not imply legal authority that has not been established. Unknown fields remain unknown.

## 8. Delivery phases and acceptance criteria

### Phase 0 — Architecture and baseline
- Document the accepted request lifecycle, boundaries, source governance, and provider limits.
- Inventory current code, source registry, deployment constraints, and existing tests.
- Establish a baseline evaluation set with diverse, human-reviewed PNG public-service questions.
- Record current response latency, retrieval quality, evidence size, and provider token usage where those measurements are available.

**Acceptance:** architecture and interfaces are documented; baseline tests can be rerun; no production behaviour changes.

### Phase 1 — General foundation
- Keep the permanent system prompt in one tested module.
- Define typed interfaces for source records, documents, passages, retrieval results, and evidence bundles.
- Define source authority/freshness metadata and provenance requirements.
- Remove topic-specific retrieval boosts from the target design.
- Preserve short meaningful passages and structured document relationships.
- Define operational budgets and a no-model fallback.

**Acceptance:** general-purpose tests cover different public-service domains and phrasings; no individual topic requires its own ranking branch; existing supported NID and IPA cases remain represented as ordinary evaluation cases.

### Phase 2 — Ingestion and durable index
- Implement ingestion as a separate operation from chat requests.
- Build a versioned index from the exact approved source registry.
- Select persistence only after confirming Render/free-tier durability and any existing approved storage option.
- Support atomic index replacement, failure reporting, and source freshness checks.

**Acceptance:** normal chat requests query the built index without downloading every source page; index provenance is inspectable; a failed refresh does not destroy the last known-good index.

### Phase 3 — Bounded adaptive retrieval
- Add model-assisted request understanding and controlled query rewriting.
- Add a measurable retrieval sufficiency decision.
- Permit no more than one additional retrieval attempt.
- Compare lexical and semantic retrieval candidates on the same evaluation set before selecting or combining them.

**Acceptance:** unfamiliar phrasings retrieve relevant evidence across multiple domains; retrieval attempts and resource use are bounded and observable.

### Phase 4 — Grounded generation and verification
- Generate answers only from bounded evidence for official PNG claims.
- Validate citations and high-impact factual claims against supplied passages.
- Surface conflicts, stale evidence, and missing official details.
- Preserve extractive fallback behaviour.

**Acceptance:** unsupported official claims are rejected or qualified in the evaluation suite; every displayed citation resolves to supplied approved evidence.

### Phase 5 — Evaluation, optimisation, and source operations
- Run a broad, human-reviewed evaluation suite across identity, business, tax, education, health, justice, land, provincial services, and general questions.
- Measure answer correctness, retrieval recall/relevance, citation support, abstention quality, latency, token usage, and failure rates.
- Establish a practical source-review and update cadence.
- Expand exact URLs through separately reviewed source changes.

**Acceptance:** release decisions are based on recorded evaluation results and resource measurements, not anecdotal demonstrations alone.

## 9. Evaluation and Data Analysis handoff rule

Some future work may require genuine dataset analysis, such as comparing retrieval algorithms over a large query set, calculating domain-level metrics, analysing token/latency distributions, or processing evaluation spreadsheets.

If ChatGPT cannot invoke the appropriate Data Analysis capability when such a task is required:
1. Stop that analysis task. Do not simulate the analysis with ordinary reasoning or present estimates as measured results.
2. Tell the owner exactly what analysis is blocked and what input data is needed.
3. Prepare a complete, ready-to-paste handover for Claude, including the objective, files/data, required calculations, methodology, outputs, validation checks, and constraints.
4. Wait for the owner to paste Claude's results back.
5. Resume only after reviewing the returned results and identifying assumptions, calculations, limitations, and reproducibility.

This rule does not block ordinary architecture discussion, code inspection, or deterministic tests that do not require Data Analysis. It applies whenever the work genuinely depends on the Data Analysis capability or equivalent execution-based dataset analysis.

## 10. Existing pull requests

- PR #11 is an intermediate generalisation step, not the complete target architecture. Reconcile or replace it with the phased design; do not merge it merely because its current CI passes.
- PR #10's IPA-specific retrieval branch is not part of the target design. Preserve its useful official IPA examples as general evaluation fixtures; do not merge the topic-specific rule as written.
- Previously merged and deployed work remains intact.
- No merge, production deployment, destructive action, paid service, or material scope change is authorised by this document.

## 11. Explicit non-goals for this delivery

- Model training or fine-tuning.
- Unrestricted web crawling or user-supplied URL fetching.
- A custom rule or workflow for every agency/topic.
- Conversation-history database or user profiling.
- A knowledge graph, multi-agent system, or unbounded autonomous agent loop.
- Mandatory paid vector database, embedding API, reranker, or model.
- Python spreadsheet/data-analysis execution inside the public chat application. That remains a separate optional product capability and is not part of core RAG.

## 12. Approval gates

Seek explicit owner approval before:
- merging any pull request into `main`;
- deploying to production;
- adding paid services or payment methods;
- introducing a new external service/account or material data-retention change;
- destructive data/index operations;
- material changes to product scope or privacy posture.

Routine isolated development and testing may proceed within the accepted scope, with concise reporting and no bypass of these gates.
