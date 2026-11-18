# Automation-first candidate source policy

**Status:** The risk policy is implemented and is now applied to results returned by the bounded candidate-fetch function. It remains separate from persistent source management and live answer selection.

## Operating decision

**Automation by default; human review by exception.** Routine pages discovered on an exact host represented in the curated seed-source configuration receive an `auto_process` discovery-policy outcome. New or uncertain hosts receive `human_review`. Invalid or unsafe candidates are excluded.

## Trust boundary

- Hostnames are derived from the exact URLs in `backend/sources.txt`.
- This is a configured seed-source allowlist for automated processing, not proof that every page on those hosts is reviewed, active, or authoritative.
- Matching is exact. Trusting `ica.gov.pg` does not implicitly trust `new.ica.gov.pg`, every `*.gov.pg` host, or a third-party host.
- Both the candidate's original/canonical URL and final redirect URL must be clean HTTPS URLs on configured hosts for automatic processing.
- A candidate that redirects to an unfamiliar host receives an exception-review outcome.
- **No evidence class or approval is assigned by this policy.** Evidence classification, approval status and eligibility for authoritative answers remain separate controls.

## Candidate-fetch integration

Each result from `fetch_candidate_pages` now includes:
- `discovery_policy_action`: `auto_process`, `human_review`, or `exclude`
- `discovery_policy_reason`: an explanatory policy reason
- `configured_seed_host`: the matched exact host, when applicable

The policy is evaluated after bounded fetching and provenance capture. Failed fetches are excluded. The result remains `candidate_unreviewed`, `approved=false`, and `evidence_class=null`; an `auto_process` outcome is not source approval and does not make the page answer evidence.

## Safeguards and limitations

- Search-provider ranking, titles and snippets never establish authority.
- A general `.gov.pg` suffix is not sufficient to establish trust.
- Candidate fetching remains bounded and subject to HTTPS, robots.txt, size, timeout and redirect controls.
- This integration does not persist candidate records, add hosts to the registry, or change live retrieval or answer selection.
- Existing source-content change detection still holds changed content separately for review. Automating low-risk changes and escalating significant changes is a separate task.
- Candidate fetching still has the documented DNS preflight limitation; it is not a final SSRF boundary for arbitrary unauthenticated URLs.

## Tests

Unit tests cover exact configured-host matching, automated eligibility without evidence classification, exception review for new domains and untrusted redirects, exact subdomain boundaries, unsafe URL rejection, invalid candidate states, and application of the policy to fetched results without approval or evidence promotion.
