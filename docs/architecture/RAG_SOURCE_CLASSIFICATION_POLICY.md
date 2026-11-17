# RAG Source Classification and Evidence Governance Policy

**Project:** PNG Public Services Assistant  
**Architecture:** Simplified Hybrid RAG v1.1  
**Status:** Batch 0 policy baseline  
**Applies to:** Search results, fetched webpages, registered sources, extracted documents and evidence passages

## 1. Purpose

This policy defines how the assistant classifies source authority without confusing a domain allowlist, a successful fetch, or a source lifecycle state with proof that a particular claim is authoritative.

Classification is specific to the subject, jurisdiction, institution and page. A government domain is not automatically authoritative for every topic. Retrieved content is untrusted input and must never be allowed to change application instructions.

## 2. Four source classes

| Class | Name | Criteria | Permitted use |
|---|---|---|---|
| A | Approved authoritative | Exact page is verified as a primary source for the relevant service, jurisdiction and claim; institution's authority is established; page identity and content are reviewed; source is permitted for the intended retrieval/use. | Primary evidence for claims within the source's remit, subject to freshness and claim-level checks. |
| B | Recognised institutional | Identifiable and reputable institution with relevant expertise or operational role, but not the primary government authority for the claim. | Supporting evidence; do not present as the government's definitive requirement. |
| C | General web | Other identifiable public webpages, news, commentary, directories, private providers or third-party explanations. | Discovery leads and supplementary context only; clearly label as non-official and do not use alone for high-impact official requirements. |
| D | Unverified or unsafe | Provenance cannot be established; page is irrelevant, deceptive, malicious, inaccessible, policy-disallowed, or fails technical/security checks. | Exclude from evidence and answer generation. Retain only minimal diagnostic metadata where safe. |

## 3. Classification rules

1. Classify the exact page and its relevant subject, not just its domain.
2. A `.gov.pg` domain is a useful provenance signal, not sufficient proof that every page is current, complete or authoritative.
3. An official agency page may be Class A for a service within that agency's legal/administrative remit and not Class A for another agency's service.
4. A search provider's country ranking, domain label, snippet or AI summary is not authority verification.
5. A result discovered through general web search starts unverified for this project. It may be assessed and assigned A, B, C or D after review.
6. Class A requires a human-reviewed source record with institution, exact URL, topic/remit, jurisdiction, document type, review timestamp and any known effective/publication date. Unknown values remain unknown.
7. Source class and source lifecycle status are separate fields. For example, `pending_review` is not Class A; `active` means the source record passed the project's review workflow, but does not make every claim on the page current or legally controlling.
8. A successful HTTP response, extraction, indexing operation, matching domain, or inclusion in a curated URL registry never promotes a source automatically.
9. Conflicting sources must remain separately identified. Do not silently choose a newer-looking page or prefer a general source over a primary source.
10. A material change to an A-class page triggers review before relying on the changed content for current official requirements.
11. Publication date, effective date, last-reviewed date and retrieval timestamp are distinct. Never substitute one for another.
12. Respect source terms, robots policies, copyright, rate limits, access controls and applicable law. Do not bypass logins, paywalls or anti-bot controls.

## 4. Source lifecycle is independent of class

The existing lifecycle states remain:

- `pending_review`: not yet reviewed for activation; no A-class trust may be inferred.
- `active`: reviewed and eligible for the configured use, subject to page-level evidence checks.
- `broken`: unavailable or failing technical checks; absence of a fetch is not proof that information does not exist.
- `superseded`: replaced by a newer source or version; preserve traceability and do not treat as current.

A source must return to `pending_review` before reactivation from `broken` or `superseded`. Activation requires an explicit review timestamp. Source records are immutable; a transition creates a new record.

## 5. Current registry interpretation

The current `backend/sources.txt` list is a curated URL fetch allowlist, not a completed source-approval register. Registry metadata currently defaults to `pending_review`; the repository's existing retrieval path has not yet implemented a complete class/status-aware evidence gate.

Consequently:
- Do not describe all fetched registry excerpts as fully verified or universally approved.
- Do not treat all 15 registered URLs as Class A.
- Do not infer that all URLs have passed source-use/rights, content-freshness or subject-remit review.
- Preserve the current allowlist and existing answer behaviour until a separately tested implementation enforces the classification policy.
- A follow-up implementation must expose source class/status in evidence and citations and prevent pending, broken, superseded or Class D evidence from being represented as verified official guidance.

## 6. Search discovery defaults

- New general-web results are Class C at most until source review; if provenance or safety is unclear, classify D and exclude.
- A result from a known official agency domain is only a candidate for A. Verify the exact page, remit, jurisdiction and content before assigning A.
- Search snippets are discovery metadata, not sufficient evidence for fees, dates, eligibility, legal obligations, deadlines, application steps or other high-impact claims.
- Fetch a bounded candidate page only after URL, DNS/IP, redirect, HTTPS, content-type, timeout, byte and concurrency checks pass.
- A blocked page is marked unavailable; do not assume its content or use an unverified snippet as a substitute.

## 7. Privacy and search-query minimisation

Before sending a query to an external search provider:
- Reduce it to the minimum public-service topic and jurisdiction needed to find sources.
- Do not send the full conversation, conversation history, names, phone numbers, email addresses, residential addresses, NID/passport numbers, bank details, account identifiers, private uploads or full document text.
- Remove user-specific values and personal circumstances. Search for the general process, not the individual's case.
- If a safe generalised query cannot be formed, skip external search and use the approved-source path or explain the limitation.
- Keep provider credentials server-side. Never expose API keys to the browser or user.
- Avoid logging raw user queries or private search inputs.
- Disclose external search-provider processing in the product privacy notice before production use.

Tavily's published privacy policy states that query data and uploaded documents are collected for retrieval, portions of query data may be used to improve future responses, and query data may be shared with third-party search-index providers in limited situations. This makes query minimisation a mandatory control, not an optional enhancement.

## 8. Citation and answer presentation

For each cited item, preserve:
- source title and exact canonical URL;
- institution or publisher;
- source class and lifecycle status;
- jurisdiction and topic/remit when known;
- provider and rank for general-search discoveries;
- retrieval timestamp;
- publication/effective date only when reliably available;
- content hash or stable document/evidence identifier where supported.

The answer must distinguish official requirements from general context. Class B/C evidence must not be described as official government instructions. If sources conflict, are stale, or do not directly support a high-impact claim, disclose the conflict or abstain.

## 9. Change control

Changes to source trust rules, automatic promotion, source allowlists or production evidence behaviour are material policy changes. They require a documented issue/PR, tests and the project's normal approval gates. This document does not authorise production deployment, paid services, or automatic promotion of discovered sources.
