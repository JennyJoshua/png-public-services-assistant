# Source lifecycle and evidence-use runtime contract

**Status:** Implemented as a provider-neutral, tested contract; not yet wired into live answer selection.

## Purpose

Keep source authority and lifecycle as separate dimensions. A successful fetch, curated URL allowlist entry, matching government domain, extraction, or index operation does not activate a source or prove that its claims are authoritative.

## Lifecycle

| Status | Meaning | Permitted next states |
|---|---|---|
| `pending_review` | Not reviewed for activation | `active`, `broken` |
| `active` | Human-reviewed for its documented use | `pending_review`, `broken`, `superseded` |
| `broken` | Unavailable or failing technical checks | `pending_review` |
| `superseded` | Replaced by a newer source/version | `pending_review` |

Activation requires a timezone-aware human-review timestamp. Reactivation from `broken` or `superseded` must pass through `pending_review`. Transitions return a new immutable source record; they do not mutate the existing record.

## Evidence class and permitted use

| Class | Meaning | Maximum permitted use |
|---|---|---|
| A | Approved authoritative | Primary evidence for claims within the source's verified remit |
| B | Recognised institutional | Supporting evidence; do not describe as the primary authority |
| C | General web | Supplementary context only; do not present as official requirements |
| D | Unverified/unsafe | Excluded |

A source is eligible for answer evidence only when it is `active` and has a recognised class A, B or C. Only active class A can support a primary-authority claim. Class B and C must remain clearly distinguished. Class D and unclassified sources are excluded.

## Implemented helpers

In `backend/app/retrieval_contracts.py`:
- `transition_source_status(...)` validates lifecycle transitions and requires a human-review timestamp for activation.
- `evidence_use_for_source(...)` returns the maximum permitted evidence role.
- `is_eligible_for_answer(...)` excludes unreviewed, inactive, unclassified and class-D sources.
- `is_eligible_for_primary_claim(...)` permits only active class-A sources.

Unit tests cover the lifecycle transition graph, activation timestamp, reactivation gate, all evidence classes and inactive states.

## Important implementation boundary

This PR adds and tests the provider-neutral policy contract only. It does **not** connect these helpers to the current live retrieval pipeline, change the existing source allowlist, activate any of the 15 registry URLs, change prompts/citations, or alter production answer behaviour. Existing registry entries remain `pending_review` and their current runtime behaviour is unchanged until a separately tested integration is delivered and approved.

## Required follow-on

Before enabling this policy in live answer selection:
1. Add page/document-level reviewed metadata and evidence class without guessing unknown dates or authority.
2. Apply eligibility at the evidence-selection boundary, not merely in prompt wording.
3. Preserve class/status/provenance in citations and user-visible answer source labels.
4. Add regression tests proving pending, broken, superseded, unclassified and class-D evidence cannot support answers.
5. Verify existing user-facing answer behaviour and fallback paths before any production deployment.
