# Supabase Source Registry Storage

## Purpose

This project uses a dedicated Supabase PostgreSQL project as the durable store for PNG public-service source governance. It is separate from the application's other Supabase projects.

Project reference: `gccuzypgzpjxsmacuvlp`  
Region: Sydney (`ap-southeast-2`)

## Data model

All operational tables are in the non-public `private` schema:

- `source_registry`: one record per exact configured source URL, its authority classification, lifecycle status, active known-good version pointer, and refresh schedule.
- `source_versions`: immutable fetched-content snapshots, SHA-256 hashes, provenance, and extracted text. A later source change creates a new version rather than overwriting the accepted copy.
- `source_assessment_decisions`: append-only assessment outcomes, policy version, hard-gate results, reasons, and assessment input snapshot.
- `source_refresh_runs`: one record per scheduled/manual/retry refresh run and its aggregate result.
- `source_refresh_results`: per-source result for each run.
- `source_exceptions`: retryable fetch, assessment, and verification exceptions.

## Security

- The schema is not part of the public API schema.
- RLS is enabled on all six tables.
- `anon` and `authenticated` have no table privileges.
- The server-side `service_role` is the only application role granted access.
- The service-role key must never be placed in frontend code or a `NEXT_PUBLIC_*` variable.
- Source text is stored only in this private database; it is not committed to GitHub.
- The version guard prevents updates to version content/provenance and prevents version deletion. Lifecycle state may change as a result of recorded decisions.

## Governance invariants

1. Fetching a page does not activate it.
2. Only the deterministic source-assessment policy may produce an activation decision.
3. A candidate version does not replace the active known-good version until the required gates pass.
4. Held or failed candidates do not displace the active version.
5. Assessment decisions and refresh outcomes remain auditable.
6. Source content is untrusted evidence, never executable instructions.

## Current implementation boundary

The database schema and migration history are created. The existing FastAPI runtime still uses its in-memory source cache, and the GitHub source audit workflow is still manual. The next implementation batch must:

1. Seed the exact 18 configured URLs as `pending_review` records without activating any source.
2. Add a server-only database repository and configuration.
3. Connect the controlled assessment runner to persist fetched candidate versions and decisions.
4. Add scheduled GitHub Actions refresh/assessment with secrets supplied through repository secrets.
5. Switch live retrieval to read only the active known-good versions from this registry.
6. Test fail-closed behaviour, retries, version preservation, and rollback.

No production deployment is part of this change.
