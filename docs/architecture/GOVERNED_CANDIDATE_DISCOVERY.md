# Governed candidate discovery orchestration

**Status:** Implemented as a provider-neutral, non-production orchestration helper.

## Flow

1. Accept provider-normalised candidate metadata from a caller.
2. Pass candidates to the existing bounded fetcher (maximum five candidates, two concurrent fetches).
3. Evaluate each fetched result using the exact configured seed-host policy.
4. Attach one of three outcomes: auto_process, human_review, or exclude.

## Important boundary

- Search-provider ranking, title and snippet are provenance only.
- auto_process means eligible for subsequent automated processing; it does not mean source approval.
- The orchestration helper never assigns A/B/C/D, never sets approved=true, never activates a source, and never inserts candidate text into the live answer cache.
- New or unconfigured hosts and redirects require exception review.
- Failed or unsafe fetches are excluded.
- No provider is selected or called here. A future provider adapter can supply normalised results without changing the fetch/policy boundary.
- No candidate persistence or public API endpoint is added in this batch.

## Validation

Tests verify automatic processing for a configured host, exception review for a new host, exclusion of failed fetches, and preservation of the unapproved/unclassified quarantine state.