# PNG Public Services Assistant
## Bounded Adaptive RAG Technical Architecture and Interface Specification v1.0

**Status:** Approved project baseline  
**Approval:** Project owner approval recorded in the project conversation on 15 November 2026  
**Repository:** `JennyJoshua/png-public-services-assistant`  
**Scope:** Architecture and internal interface baseline; not authorisation to merge, deploy, purchase services, or perform database migrations.

## 1. Purpose

Define a reliable, extensible retrieval-augmented generation architecture for answering Papua New Guinea public-service questions using approved information sources and an existing inference model. New subject areas should generally be supported by adding and maintaining source data, not by writing a new application rule for every topic or anticipated question.

## 2. Product requirements and constraints

The assistant should support diverse PNG public-service questions, including identity and civil registration, business registration, tax, education, health, land, justice, government agencies, forms, fees, eligibility and procedures.

It must:
- Answer in clear, accessible language and cite the official sources used.
- Never invent official requirements, fees, deadlines, eligibility, forms, procedures or agency positions.
- Distinguish verified PNG official information from general background.
- Identify missing, insufficient, stale or conflicting evidence and abstain where necessary.
- Handle unfamiliar questions through general question understanding and retrieval, not a growing set of topic-specific code branches.
- Use existing models through inference; no model training or fine-tuning.
- Use only curated, exact, approved source URLs; no unrestricted crawling or arbitrary user-supplied URLs.
- Avoid persistent conversation storage and retain only bounded context required for a response.
- Prefer free services and the existing Render/Groq deployment unless the owner explicitly approves a change.

## 3. Target architecture

### 3.1 Online request lifecycle

1. **Input guard:** validate request size, role/history shape, scope and abuse limits.
2. **Question understanding:** produce a structured question plan, including intent, sub-questions, ambiguity and likely information needs.
3. **First retrieval:** search the approved, versioned corpus using modular retrieval strategies and source metadata.
4. **Evidence sufficiency gate:** assess whether the retrieved evidence appears sufficient and relevant for the question.
5. **Bounded adaptive retrieval:** if evidence is weak or the question is compound, permit at most one additional reformulation/decomposition and retrieval attempt.
6. **Evidence assembly:** select and budget relevant passages while retaining section, source and authority context.
7. **Answer generation:** generate a structured answer whose material official claims map to passage identifiers.
8. **Verification:** validate citation identity and evidence support for high-risk facts and claims.
9. **Response composition:** provide citations, uncertainty, source dates and appropriate abstention or fallback language.
10. **Operational recording:** record only necessary technical metrics; do not retain unnecessary user conversation content.

The model may assist with question interpretation, reformulation and answer drafting. Deterministic application code controls source access, retrieval limits, validation, citation integrity, resource budgets and abstention.

### 3.2 Main components

- **API and input guard:** maintains the existing chat API contract where practical and validates bounded input.
- **Question planner:** converts user wording into a validated, general-purpose plan.
- **Source registry:** authoritative metadata for approved source URLs.
- **Ingestion and extraction:** fetches only registered sources and preserves headings, lists, tables and document structure.
- **Versioned index:** stores stable document and passage records and can be built reproducibly.
- **Retrieval engine:** exposes replaceable lexical, terminology, hybrid and later optional semantic strategies.
- **Adaptive controller:** decides whether one further retrieval attempt is justified and enforces the hard retry limit.
- **Evidence verifier:** checks claim-to-passage relationships and high-risk facts independently of the model.
- **Answer composer:** renders citations, source dates, uncertainty and fallbacks.
- **Monitoring/evaluation:** records operational metrics and runs reproducible tests.

## 4. Internal interface contracts

These are logical contracts. Exact Python types and module locations are implementation decisions, subject to review and compatibility testing.

### 4.1 QuestionPlan

Expected fields:
- `normalized_question`: string
- `intent`: concise intent label or controlled value
- `sub_questions`: list of independently answerable information needs
- `query_variants`: optional list of general reformulations
- `ambiguities`: list of unresolved details
- `requires_clarification`: boolean
- `scope`: in-scope, out-of-scope or uncertain
- `language`: detected or requested language when known

The plan must be schema-validated. It must not contain executable instructions or authorise access outside the approved source registry.

### 4.2 SourceRecord

Expected fields:
- `source_id`, `institution`, `title`, `url`
- `authority_tier` and `document_type`
- `jurisdiction` and `language`
- `publication_date` and `effective_date`, when available
- `last_fetched_at` and `last_reviewed_at`
- `content_hash`
- `status`: active, superseded, broken or pending review

Missing dates must remain unknown; they must not be inferred.

### 4.3 DocumentRecord and PassageRecord

A document record links to one approved source and one fetched content version. A passage record contains:
- Stable `passage_id` and `document_id`
- Text and passage type
- Section heading/path and document order
- Parent/child relationship where applicable
- Source metadata reference and content version/hash

Checklist items must retain their heading and related context. Table rows must retain their column headings. Short but meaningful headings, labels and list items must not be discarded solely because of character length.

### 4.4 EvidenceHit and RetrievalResult

Each evidence hit should include:
- Passage and document identifiers
- Text and section context
- Source identity, authority tier and relevant dates
- Retrieval strategy and score metadata
- Document order and parent-section relationship

The retrieval result should include the selected hits, query variants used, strategy metadata, index version, and bounded diagnostics needed for evaluation. Raw internal scoring details need not be exposed to public users.

### 4.5 VerificationResult

Expected fields:
- `passed`: boolean
- `valid_citation_ids` and `invalid_citation_ids`
- `unsupported_claims`: claim references and reasons
- `high_risk_fact_findings`: fees, amounts, dates, form codes, deadlines, agency names and conditions
- `recommended_action`: accept, clarify, abstain, regenerate_once or extractive_fallback

A match of a number or phrase somewhere in a source is not sufficient proof that the answer attached it to the correct condition or meaning.

### 4.6 Chat response

Preserve existing frontend compatibility where practical. The response should support:
- Answer text
- Citations with source title, institution, URL and available date metadata
- Evidence status or warning
- Clarifying question where required
- Explicit indication when information is incomplete or not verified

Any contract change must include frontend/API compatibility tests.

## 5. Source governance and ingestion

1. Only exact URLs explicitly included in the approved registry may be fetched.
2. Source authority is represented as metadata, not inferred solely from a hostname.
3. Ingestion preserves headings, list groups, table headers and rows, and document order.
4. Each build records content hashes and source-fetch metadata.
5. Changed, broken, superseded or potentially conflicting sources are flagged for review.
6. A source change that may affect official fees, requirements, eligibility or procedures must not silently become trusted current guidance without the defined review policy.
7. Source coverage gaps must be visible; a homepage alone is not proof that all procedural guidance for an agency is covered.

## 6. Retrieval and adaptive behaviour

- Start with a general-purpose retrieval pass over the approved corpus.
- Retrieval strategies must be modular and replaceable.
- Preserve section and document context when expanding a selected passage.
- Do not use topic-specific ranking branches for NID, IPA or any other agency.
- A weak first pass may trigger at most one additional retrieval attempt.
- Query rewriting and decomposition must remain bounded and schema-validated.
- Retrieval confidence thresholds must be calibrated against a reviewed evaluation set, not guessed.
- Dense retrieval, embeddings and reranking are optional later techniques; introduce them only when evaluation demonstrates a need and resource validation supports them.

## 7. Evidence verification and response policy

- Every material official claim should map to one or more passage IDs.
- Every citation must refer to a passage actually supplied to the answer-generation step.
- High-risk facts require stronger checks than simple substring presence.
- Eligibility and conditional rules must preserve the source's conditions; the assistant must not manufacture a definitive eligibility decision when the source does not establish one.
- Conflicting official sources must be surfaced with their source identities and dates rather than silently reconciled.
- If evidence is insufficient, answer only the supported parts and state what remains unverified.
- If generation or verification fails, use a controlled extractive/source-linked fallback or abstain.
- Retrieved content is untrusted data, never instructions that can override system policy.

## 8. Hosting, security, privacy and resource constraints

- Existing Render hosting and Groq inference remain the default.
- Secrets remain in provider-managed environment variables; never commit or expose API keys.
- No assumption may be made that Render's local filesystem is durable across restarts or deployments.
- Prefer a reproducible, versioned index artifact loaded read-only at runtime, subject to storage, startup, memory and rollback validation.
- Heavy ingestion and optional embedding work should be offline where feasible.
- Enforce bounded request, history, evidence, model-call and execution budgets.
- Measure actual token use, latency, memory, index size and concurrency before fixing operational thresholds.
- Handle provider timeouts, rate limits, cold starts and outages.
- Do not persist conversations. Any operational logging must be minimised and privacy-reviewed.
- Protect against prompt injection in both user inputs and retrieved source content.

## 9. Technical validation and acceptance

Before implementation is considered complete, validate:
- Existing API and frontend compatibility.
- Stable document/passage identifiers and correct source relationships.
- Correct extraction of headings, lists and table rows with context.
- No loss of short meaningful checklist items.
- National ID procedure order regression is fixed.
- General retrieval tests include NID, IPA and uncovered/ambiguous questions without topic-specific code.
- Adaptive retrieval performs no more than one second attempt.
- Invalid citations and unsupported high-risk claims are rejected or handled safely.
- Conflicting, stale, missing and insufficient evidence produce clear responses.
- Prompt-injection content cannot override system policy.
- Index loading, startup, memory, latency, rollback and provider failure behaviour are tested on the actual hosting arrangement.
- Quantitative quality claims are based on a defined dataset and reproducible analysis; no synthetic probe is presented as real-world performance.

## 10. Delivery batches

1. **Baseline and technical validation:** publish this specification, reconcile roadmap, validate index storage and delivery.
2. **General retrieval foundation:** stable data structures, structure-aware extraction, general ranking, regression suite.
3. **Source ingestion and versioned index:** governed metadata, offline ingestion, packaging, change monitoring.
4. **Bounded adaptive retrieval:** question planning, evidence gate, one controlled second attempt.
5. **Evidence verification and safe answers:** claim-to-passage mapping, high-risk fact checks, abstention and fallback.
6. **Operational reliability and release readiness:** quotas, privacy, monitoring, evaluation, human review and explicit release approval.

## 11. Approval gates and non-goals

This baseline does not authorise:
- Merging any open pull request.
- Deploying to production.
- Paid services, upgrades or new billing commitments.
- Destructive actions or database migrations.
- Material changes to product scope, hosting or privacy policy.

Explicit owner approval is required for those actions. Routine implementation within an approved batch may proceed on a branch and through reviewable pull requests.

Non-goals: model training/fine-tuning, unrestricted crawling, arbitrary URL ingestion, persistent conversation storage, an unbounded agent loop, an immediate graph database, and unmeasured claims of retrieval superiority.
