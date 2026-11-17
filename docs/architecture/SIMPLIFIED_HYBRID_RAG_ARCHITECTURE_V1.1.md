# Simplified Hybrid RAG Architecture and Delivery Plan v1.1

**Project:** PNG Public Services Assistant (pilot implementation)  
**Reusable capability:** Joshua shared RAG engine  
**Status:** Active owner-approved architecture; adopted and merged through PR #41  
**Supersedes:** Bounded Adaptive RAG Technical Architecture and Interface Specification v1.0 for new implementation decisions; historical v1.0 work remains retained where compatible  
**Storage baseline:** GitHub is the only permanent application knowledge/artifact store initially  
**Runtime baseline:** Existing Render services  
**LLM baseline:** Existing free Groq-hosted model configuration; no paid provider or silent provider/model fallback

---

## 1. Purpose and decision

This document specifies a simplified, reusable, web-first hybrid retrieval-augmented generation (RAG) architecture.

The owner has selected **Option B — Simplified hybrid** after evaluating the original Bounded Adaptive RAG architecture and the current repository implementation.

The purpose is to reduce unnecessary indexing and ingestion work while retaining the controls that make answers reliable. Live retrieval becomes the normal first path for questions requiring current external information. The existing curated source registry remains the authority and policy layer. Persistent indexed knowledge remains available as an optional supporting capability for material that benefits from it.

This is still a RAG system: retrieved external or stored evidence is supplied to the LLM as context. It is not a direct, unconstrained LLM-to-internet connection.

### 1.1 Decision status and transition rule

The owner approved Option B and this architecture was merged through PR #41. That approval does not, by itself, authorize:
- production deployment;
- a paid search provider, paid scraping service, paid model or paid infrastructure;
- changing the current Groq provider/model configuration;
- changing production source policy or treating arbitrary web content as authoritative;
- destructive changes to existing issues, branches, pull requests or artifacts.

This document was reviewed and merged through PR #41 and is the controlling technical baseline. Historical v1.0 records remain available for traceability; where they conflict, v1.1 controls.

### 1.2 Core principles

1. Retrieve evidence before generating factual answers.
2. Prefer approved and authoritative sources for the relevant project.
3. Permit general web discovery when approved evidence is insufficient, while clearly classifying and qualifying general sources.
4. Treat every retrieved page as untrusted input, including pages from approved domains.
5. Verify evidence relevance, freshness, authority and citation identity before relying on it.
6. Keep retrieval bounded in time, result count, page count, bytes, redirects and model-context size.
7. Preserve a replaceable search-provider interface.
8. Keep project knowledge collections, policies and data isolated.
9. Use GitHub as the only permanent storage initially; do not require a hosted vector database or persistent Render disk.
10. Retain optional indexing where measured value justifies it.
11. Keep the existing free Groq inference arrangement. No paid fallback or silent provider/model switch.
12. Prefer measured quality and resource results over assumed capacity claims.

---

## 2. Assessment of the current implementation

The current live implementation already performs a basic web-grounded RAG workflow:

1. It fetches exact URLs listed in `backend/app/source_registry.py`.
2. It checks host and response characteristics and extracts readable HTML.
3. It creates structure-aware text blocks/passages.
4. It ranks passages using BM25 and registered terminology aliases.
5. It selects a bounded set of excerpts.
6. It sends the question and evidence to the configured Groq-compatible model adapter.
7. It returns an answer and source references.

The main limitation is discovery: the application fetches a fixed set of registered URLs and does not search the general internet for additional relevant pages. It therefore cannot discover a new relevant provincial or agency page unless its URL is already registered.

The repository also contains an offline index-building/profiling foundation. That artifact is not currently the primary live retrieval path. Its work remains useful, but full production index delivery is not a prerequisite for the simplified web-first path.

### 2.1 Existing work to preserve

- Exact approved source registry and source metadata foundation.
- Host validation and bounded HTTP/HTML extraction.
- Structure-aware extraction and passage preparation.
- BM25 ranking and terminology aliases.
- Groq model adapter and server-side secret handling.
- System grounding instructions and existing citation structures.
- Existing test fixtures, NID/IPA retrieval work and source-policy documentation.
- Index artifact builder, validator, profiling and rollback experiments as optional supporting capabilities.
- Existing Render deployment and GitHub CI foundations.

No existing implementation should be deleted merely because it is not part of the first web-first release.

---

## 3. Target architecture

The engine is organised into five replaceable, testable capabilities.

### 3.1 Question and retrieval planner

Input: validated user question, project policy and bounded conversation context.

Responsibilities:
- classify whether the question requires current information, stored/reference knowledge, or both;
- identify relevant project source policy and jurisdiction;
- search the approved source collection first;
- determine whether returned evidence is sufficient for the requested answer;
- invoke general web discovery when approved evidence is absent, weak, stale or incomplete;
- allow at most one bounded additional search/retrieval pass in the initial release;
- enforce per-request budgets and avoid topic-specific hard-coded retrieval branches.

The planner may use deterministic rules and lightweight classification. It must not depend on an additional paid model call.

### 3.2 Search provider interface

A provider-neutral interface accepts a query and returns normalised search results.

Each result should carry, where available:
- title;
- canonical URL;
- snippet;
- displayed domain;
- provider result identifier;
- publication date if supplied by the provider;
- retrieval timestamp;
- provider name;
- rank/order;
- result type or source classification, where known.

The initial implementation must assess free/usable providers before selecting one. Provider selection must consider:
- free-tier availability and quotas;
- terms of service and permitted use;
- reliability and geographical availability;
- result quality for Papua New Guinea and Pacific sources;
- latency, timeout behaviour and response schema;
- whether results can be used for downstream page retrieval;
- privacy and data handling.

Do not scrape search-engine result pages where the provider prohibits it. Do not assume that a search endpoint is free, unlimited or stable. Do not hard-code a provider-specific response into the RAG engine.

If no suitable free provider is available, retain the approved-source-only mode and report the limitation. Do not enable a paid service without explicit owner approval.

### 3.3 Web content retrieval and extraction

The retrieval component receives candidate URLs and obtains their content under strict controls.

Requirements:
- HTTPS by default; explicit policy required for any exception.
- Validate schemes, hostnames, DNS results and resolved IP addresses to mitigate SSRF.
- Block loopback, private, link-local, reserved and cloud metadata addresses.
- Revalidate every redirect target and enforce a small redirect limit.
- Apply connection, read and total request timeouts.
- Limit concurrent requests, response bytes, extracted characters and pages per user request.
- Accept supported HTML and explicitly supported document types only.
- Do not execute page JavaScript, download arbitrary binaries, submit forms, authenticate, bypass paywalls or evade anti-bot controls.
- Respect robots.txt where applicable, website terms, rate limits and access restrictions.
- Use a clear user-agent and contact policy if appropriate.
- Remove navigation, scripts, styles, hidden text and boilerplate while preserving meaningful headings, paragraphs, lists and tables.
- Record canonical URL, final URL, title, domain, fetch timestamp, publication/effective date if reliably available, content hash and extraction status.
- Treat page content, metadata and embedded instructions as untrusted data.

Blocked or unavailable pages must be recorded as unavailable, not treated as evidence that the information does not exist.

### 3.4 Evidence manager and source policy

Every evidence item receives a source class and provenance record.

Initial source classes:

| Class | Description | Use |
|---|---|---|
| A — Approved authoritative | Official government, regulator or owner-approved primary source for the relevant jurisdiction/topic | Primary evidence |
| B — Recognised institutional | Established institution or recognised service provider with relevant authority | Supporting evidence |
| C — General web | Other discoverable webpages, media, organisations or commentary | Supplementary evidence, qualified |
| D — Unverified/unsafe | Unclear provenance, irrelevant, suspicious, inaccessible or policy-disallowed content | Exclude |

Source class is project-specific. A domain is not globally authoritative for every subject merely because it is an official domain.

The evidence manager must:
- apply the project's approved domain and source policy;
- avoid elevating general search results to official status;
- compare evidence dates and jurisdiction;
- detect duplicate or near-duplicate pages;
- identify conflicts and missing provenance;
- retain citation identity through extraction, ranking and generation;
- exclude evidence that is irrelevant or fails safety checks;
- communicate uncertainty when source authority or freshness cannot be established.

General web discovery is allowed when approved sources cannot answer, but general results must remain visibly distinguishable from approved official evidence. General results must never override a verified official requirement without a documented reason and clear explanation of the conflict.

### 3.5 Retrieval ranking and evidence sufficiency

Use the existing BM25/terminology retrieval foundation for ranking extracted page content. Keep ranking modular so semantic or hybrid ranking can be evaluated later.

Initial retrieval should:
- rank across approved-source pages and general-search candidate pages;
- use title, headings, passage text and relevant metadata;
- preserve passage-to-source linkage;
- return only a bounded evidence set;
- avoid treating a high lexical score as proof of factual sufficiency.

An evidence sufficiency gate should assess whether evidence is relevant and adequate for the question. It must consider the type of claim requested, source authority, freshness, directness and consistency.

If evidence is insufficient:
1. perform no more than one bounded additional search/retrieval pass, using a reformulated query or a targeted sub-question;
2. reassess evidence;
3. answer only supported parts and clearly state what could not be verified if evidence remains insufficient.

Do not generate invented counts, fees, deadlines, eligibility rules, form numbers, service availability or agency responsibilities.

### 3.6 LLM answer generation

Retain the existing replaceable OpenAI-compatible adapter with the currently configured free Groq provider.

The model receives:
- the original question;
- concise project policy and answer instructions;
- a bounded evidence pack;
- stable citation identifiers;
- source classes and relevant dates;
- relevant bounded conversation history.

The model must:
- distinguish approved authoritative evidence from general web evidence;
- cite factual claims to the supplied evidence;
- not claim to have verified information that was not retrieved;
- identify conflicting or stale sources;
- distinguish publication date from retrieval date;
- abstain or qualify unsupported claims;
- ignore instructions contained in retrieved pages that attempt to change system behaviour, disclose secrets, or redirect the task.

No provider/model switch, paid fallback, model training or fine-tuning is included. Provider outages should produce a clear controlled error or the existing safe fallback, not an undocumented model change.

### 3.7 Citation and claim verification

Citations must resolve to the exact source actually retrieved. Validate citation identifiers and URLs before returning the response.

For high-impact facts, require stronger evidence:
- fees and amounts;
- deadlines and dates;
- legal requirements;
- eligibility conditions;
- application steps;
- form names/codes;
- official agency names and responsibilities;
- counts, statistics and service availability.

Where possible, important claims should be associated with the exact supporting passage. If the evidence pack does not support a claim, remove or qualify the claim rather than inventing a citation.

The response should identify source type and the date checked. Do not imply that a source is official unless its classification supports that statement.

---

## 4. Retrieval flow

1. Validate the request and apply project policy.
2. Check optional local/indexed knowledge if enabled and relevant.
3. Retrieve relevant approved sources, including direct live retrieval where appropriate.
4. Assess relevance, authority, freshness and evidence sufficiency.
5. If insufficient, run general internet search through the selected provider.
6. Fetch a bounded number of relevant candidate pages and extract content.
7. Rank and deduplicate evidence; apply source classes and safety controls.
8. If still insufficient, perform at most one additional bounded retrieval pass.
9. Assemble a limited evidence pack for the LLM.
10. Generate a grounded answer.
11. Validate citations and high-impact claims.
12. Return answer, citations, source classifications and checked dates, including a clear uncertainty statement where needed.

The exact request budgets must be configurable and tested. Initial values should be conservative and adjusted only from evaluation and runtime measurements.

---

## 5. Optional persistent knowledge and indexing

Persistent indexing remains supported, but is not required for every project or every request.

Use it where it provides measurable value:
- large official PDFs and long reference documents;
- frequently requested content;
- historical records that should not be replaced by current pages;
- sites with unreliable availability;
- material where reproducible snapshots are important.

Initial storage rules:
- GitHub is the only permanent storage location.
- Store source registry, metadata, approved extracted text where permitted, index artifacts, evaluation fixtures and build provenance in the repository.
- Avoid committing unnecessary duplicate raw downloads or copyrighted material where storage or redistribution is not permitted.
- Do not introduce Git LFS, hosted vector databases, paid storage or a database without separate owner approval.
- Render receives read-only artifacts as part of a deployment and loads them into memory when required.
- Do not rely on Render Free ephemeral filesystem writes surviving restart, redeploy or spin-down.
- Generate artifacts reproducibly and validate size, schema, hashes and source provenance before use.
- Keep rollback to the previous known-good artifact possible.

The source registry remains the control plane even when optional indexed content is used.

---

## 6. Reusable multi-project design

The engine is shared; project policy and knowledge are isolated.

Each project supplies a configuration containing:
- project identifier;
- permitted jurisdictions and subject areas;
- approved domains and source records;
- source classification rules;
- answer and citation policy;
- high-impact claim categories;
- optional indexed knowledge collection;
- retrieval budgets and feature flags.

Initial prospective collections include Public Services, Legal Library, SkillProof/Vocational and Education. These are future reuse targets, not authorization to ingest sensitive or private data.

Isolation requirements:
- no cross-project retrieval;
- no shared user conversation history;
- no cross-project source authority assumptions;
- no shared private documents unless explicitly authorised;
- tests proving that one collection cannot retrieve another project's evidence.

---

## 7. Security, privacy and operational controls

- Retrieved pages are untrusted; defend against prompt injection and malicious content.
- Do not execute scripts or page instructions.
- Prevent SSRF, unsafe redirects, DNS rebinding and access to internal services.
- Do not send secrets, environment variables or internal prompts to search providers or retrieved websites.
- Send only the minimum query data required to the search provider.
- Keep API keys server-side.
- Bound request size, concurrency, timeouts, retries, page count, bytes, evidence characters and model tokens.
- Apply provider rate limits and handle 429, 5xx, timeout and malformed responses.
- Avoid storing user questions or retrieved personal information beyond operational necessity.
- Do not collect, index or expose sensitive personal data from public pages without an approved purpose and policy.
- Log operational metadata without logging secrets or unnecessary personal content.
- Provide a clear error or limited answer when external search is unavailable.
- Do not claim live search was performed if it failed or was skipped.

---

## 8. Delivery plan and reconciliation with existing batches

The existing seven GitHub issues remain the tracking structure. They should be updated only after this architecture is accepted and after their current descriptions and open PRs are reconciled. Do not create duplicate batch issues.

| Existing issue/batch | Revised scope |
|---|---|
| #15 — Batch 0 | Close baseline decisions; confirm deployment/runtime constraints, provider-selection criteria, evaluation fixtures and source policy. Full production index delivery is no longer a prerequisite. |
| #16 — Batch 1 | Modular retrieval foundation: common evidence records, search-provider interface, page extraction, ranking, provenance and current test fixtures. |
| #17 — Batch 2 | Governed source policy, provider adapter, live result retrieval and optional indexed knowledge. Reduce mandatory full index pipeline to only justified use cases. |
| #18 — Batch 3 | Question/retrieval planning, evidence sufficiency, one bounded additional search and request budgets. |
| #19 — Batch 4 | Source classification, claim/evidence checks, citation integrity, conflicts, freshness and safe abstention. |
| #20 — Batch 5 | SSRF and prompt-injection defence, privacy, rate limits, provider failures, resource budgets and observability. |
| #21 — Batch 6 | Evaluation, regression testing, load/resource measurements, quality thresholds and release readiness. |

### 8.1 PR and issue handling

- PR #39 (source metadata foundation): retain as a candidate foundation; review it against the revised metadata and source-policy requirements before any merge.
- PR #37 (non-production Render index delivery probe): retain its measurements and evidence. It is not production integration and is not required to be merged merely to adopt Option B.
- Older/superseded PRs must be reviewed individually; do not merge them simply to clear the open PR list.
- Preserve existing issue history and acceptance evidence. Update descriptions rather than replacing history or creating duplicates.
- No issue closure, PR merge, production deployment or destructive cleanup is authorised by this architecture decision alone.

### 8.2 Proposed implementation sequence

1. Finalise and approve this architecture document.
2. Reconcile Batch 0 and provider feasibility; do not select a provider until terms, free limits and quality are checked.
3. Implement a provider-neutral search adapter and normalised evidence record in a small, testable batch.
4. Integrate bounded page retrieval and extraction, reusing current code.
5. Add source classification, evidence sufficiency and bounded second retrieval.
6. Strengthen citation/claim verification and high-impact fact handling.
7. Complete security, privacy, reliability and resource controls.
8. Evaluate with representative questions and only then release the revised capability.

---

## 9. Evaluation and acceptance criteria

The revised system must be tested against a representative set of questions, including:
- questions answerable from current approved sources;
- questions requiring discovery of a new approved or official page;
- questions answerable only by general web sources;
- questions with no reliable answer available;
- conflicting or outdated source content;
- ambiguous and multi-part questions;
- high-impact fees, deadlines, eligibility and application requirements;
- malicious instructions embedded in retrieved webpages;
- blocked, malformed, slow and unavailable websites;
- search-provider quota exhaustion and outages;
- cross-project isolation.

Measure:
- answer correctness and evidence support;
- retrieval relevance and source authority;
- citation precision and URL validity;
- freshness and date handling;
- appropriate abstention and conflict disclosure;
- latency and external requests per question;
- bytes fetched, evidence size and model token use;
- memory/CPU use on the actual Render service;
- provider quota and failure behaviour;
- regression performance against current NID and IPA fixtures.

A successful answer must not merely sound plausible: its material claims must be supported by retrieved evidence.

Capacity must not be promised from the isolated 163-passage probe. Establish actual capacity through staged evaluation and load tests on the deployed application and selected provider. Free-tier concurrency and latency remain bounded by platform/provider limits.

---

## 10. Constraints and exclusions

Included:
- approved-source retrieval;
- general web search as a secondary discovery path;
- bounded webpage fetching and extraction;
- reusable provider interface;
- evidence ranking, source classification and verification;
- optional GitHub-stored knowledge index;
- existing Render and Groq baseline;
- project-specific policies and isolated collections.

Excluded unless separately approved:
- unrestricted crawling of the internet;
- scraping search-engine result pages in violation of provider terms;
- login, form submission, paywall bypass or anti-bot evasion;
- paid search, scraping, model, database or hosting services;
- paid LLM fallback or silent provider/model changes;
- hosted vector databases and persistent Render disks;
- automatic ingestion of unreviewed sources into trusted knowledge;
- model training or fine-tuning;
- cross-project sharing of private or sensitive information;
- production deployment or hosted data migration as part of architecture approval.

---

## 11. Approval gates

The following require explicit owner approval under the project's operating rules:
- merging implementation PRs where the current workflow requires a separate approval;
- material changes to source trust policy or project scope;
- selection of a paid provider/service or any recurring cost;
- changing the configured LLM provider/model;
- production deployments when they are not already covered by a specific deployment approval;
- hosted database migrations or destructive changes;
- integrating optional index storage in production if it changes runtime/deployment architecture.

Routine implementation and tests may proceed within an approved batch and scope, subject to the project's existing JASDS controls.

---

## 12. Adopted architectural decision

The adopted direction is:

**A reusable, web-first Simplified Hybrid RAG engine with approved-source priority, general internet discovery when approved evidence is insufficient, bounded webpage extraction, explicit evidence and citation verification, optional GitHub-stored indexing, existing Render hosting and the existing free Groq inference arrangement.**

This v1.1 document is the active owner-approved architecture, merged through PR #41. Historical v1.0 documents remain retained for traceability.
