# Automation-first candidate source policy

**Status:** Implemented as an isolated, tested policy helper. It is not yet connected to candidate fetching, persistent source management, or answer selection.

## Operating decision

**Automation by default; human review by exception.** Routine pages discovered on an exact host represented in the curated seed-source configuration may enter automated processing. New or uncertain hosts are held for one-time verification. Invalid or unsafe candidates are excluded.

## Trust boundary

- Hostnames are derived from the exact URLs in `backend/sources.txt`.
- This is a configured seed-source allowlist for automated processing, not proof that every page on those hosts is reviewed, active, or authoritative.
- Matching is exact. Trusting `ica.gov.pg` does not implicitly trust `new.ica.gov.pg`, every `*.gov.pg` host, or a third-party host.
- Both the candidate's original/canonical URL and final redirect URL must be clean HTTPS URLs on configured hosts for automatic processing.
- A candidate that redirects to an unfamiliar host requires exception review.
- **No evidence class or approval is assigned by this policy.** Evidence classification, approval status and eligibility for authoritative answers remain separate controls.

## Outcomes

| Outcome | Meaning |
|---|---|
| `auto_process` | Exact configured seed host; eligible for automated processing |
| `human_review` | New or unconfigured host; verify the institution and domain before adding trust |
| `exclude` | Failed fetch, invalid URL, unsafe URL, or invalid candidate state |

## Safeguards and limitations

- Search-provider ranking, titles and snippets never establish authority.
- A general `.gov.pg` suffix is not sufficient to establish trust.
- Candidate fetching remains bounded and subject to HTTPS, robots.txt, size, timeout and redirect controls.
- The policy helper does not persist decisions, add hosts to the registry, fetch content, or change live answer selection.
- Existing source-content change detection still holds changed content separately for review. Automating low-risk content updates and escalating significant changes is a separate integration task.
- Candidate fetching still has the documented DNS preflight limitation; it is not a final SSRF boundary for arbitrary unauthenticated URLs.

## Tests

Unit tests cover exact configured-host matching, automated eligibility without evidence classification, exception review for new domains and untrusted redirects, exact subdomain boundaries, unsafe URL rejection, and invalid candidate states.
