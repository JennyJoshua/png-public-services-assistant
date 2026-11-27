# Automated Source Refresh Runner

## Schedule

`.github/workflows/automated-source-registry-refresh.yml` runs daily at 03:00 Papua New Guinea time (17:00 UTC) and can also be started manually from GitHub Actions.

The workflow requires the repository secret `SUPABASE_DATABASE_URL`. If it is absent, the job records a notice and safely skips the database operation.

## What the runner does

1. Reads due source records from the private Supabase registry, limited to the exact URLs in `backend/sources.txt`.
2. Fetches at most three sources concurrently using the existing bounded page fetcher.
3. Computes and checks the SHA-256 hash of extracted text.
4. Runs the deterministic source-assessment engine.
5. Stores new content as a separate immutable version; it never overwrites a previous version.
6. Records the assessment decision, hard-gate results, refresh outcome, and retryable exception.
7. Preserves the active-version pointer when a candidate is held, excluded, or fails to fetch.
8. Retries due sources on the next scheduled run.

The run records a GitHub Actions run ID and URL for traceability. The workflow uses read-only GitHub repository permissions; its only write target is the private Supabase database through the server-side PostgreSQL connection.

## Deliberately conservative activation gates

This first runner does **not** claim that fetching an official-looking page proves it is current or conflict-free.

The verification layer now adds deterministic temporal checks:

- extracts explicit publication/issue and modified dates from page text, HTML metadata, and HTTP Last-Modified headers;
- checks whether the most recent explicit date is within a conservative five-year freshness window;
- flags future-dated content;
- detects explicit supersession, withdrawal, repeal, revocation, draft, and amendment/conflict markers; and
- records the evidence and reasons in the immutable assessment audit input.

A recent date is only a freshness signal. It does not prove that an Act, regulation, fee schedule, or policy remains legally in force.

The cross-document verifier accepts only HTTPS comparator documents on the exact configured authority hosts. It records the exact comparator URLs, detects explicit supersession/conflict markers, and compares repeated labelled numeric values (for example, a stated fee or age threshold). An empty comparator set is never reported as a completed conflict check.

The runner does **not yet fetch controlling/corroborating instruments**. Therefore it continues to set `conflict_check_completed = false` and `controlling_instrument_verified = false`. Class A sources remain held even when their page dates pass. Class C material is additionally blocked from activation if it contains high-impact claims; it is intended for context only. No source is promoted merely because a temporal signal passes.

This is deliberate: the next integration stage must add an exact, reviewed instrument map per authority/topic, safely fetch those instruments, and feed their actual content into the cross-document verifier before the runner can set the conflict gate to complete.

No human approval is required for routine refresh runs. The next implementation stage is the automated verification layer that can establish currentness, detect supersession/conflicts, and verify high-impact requirements against controlling official instruments and corroborating competent sources.

## Failure and rollback behaviour

- Fetch failure: keep the previous active version, record an exception, retry later.
- Assessment hold: retain the candidate as held, keep the previous active version, retry later.
- Assessment exclusion: reject the candidate; do not replace an existing active version.
- Successful activation (only when all required gates eventually pass): accept the new immutable version and move the active pointer in the same database transaction.
- Database failure: the run fails; live retrieval independently fails closed and does not fall back to memory.

## Required secret setup

Add a server-side Supabase PostgreSQL **Session pooler** URI as the GitHub Actions repository secret `SUPABASE_DATABASE_URL`. Use the same secret name for the Render backend when database-backed live retrieval is enabled. Never place the URI in source files, workflow YAML, logs, or frontend variables.

See [Supabase Runtime Connection](SUPABASE_RUNTIME_CONNECTION.md) for the connection details and secret-handling rules.

## Current operational boundary

The workflow and runner are code-only until the repository secret is configured. The runner has not been executed against production data, no source has been activated by this batch, and no Render deployment has been performed.
