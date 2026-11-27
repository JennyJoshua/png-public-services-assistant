# Supabase Runtime Connection

## Purpose

FastAPI can read approved, immutable source versions from the dedicated Supabase PostgreSQL project. It does not use the public Data API or a browser-visible key.

## Runtime selection

- `SUPABASE_DATABASE_URL`: server-only PostgreSQL connection URI.
- `SOURCE_STORE_MODE=database`: explicitly select durable database-backed retrieval.
- If the database mode is selected but the URI is missing or the database is unavailable, retrieval returns no evidence. It does not fall back to the in-memory cache.
- If database mode is not selected, the legacy in-memory path remains available for development compatibility.

## Connection type

Use the Supabase Dashboard **Connect → Session pooler** connection URI for the persistent Render FastAPI service, particularly if the hosting environment uses IPv4-only outbound networking. Supabase documents direct database connections as IPv6 by default on Free projects, while the shared session pooler supports IPv4. The application requires TLS with `sslmode=require`.

Do not use a transaction-pooler URI for this persistent connection. Do not enable the paid IPv4 add-on or a paid dedicated pooler for this project.

## Required secret handling

The connection URI contains the database password. Store it only as a secret:

- Render backend environment variable: `SUPABASE_DATABASE_URL`
- GitHub Actions repository secret (for the later scheduled refresh workflow): `SUPABASE_DATABASE_URL`

Set `SOURCE_STORE_MODE=database` in the Render backend environment only when the database URI has been installed and verified.

Never commit the URI, password, service-role key, or any other credential to GitHub. Do not use a `NEXT_PUBLIC_*` variable. The frontend does not need database credentials.

## Runtime query rules

The backend reads only rows where:

- registry status is `active`;
- classification is one of `approved_authoritative`, `recognised_institutional`, or `general_web`;
- the registry's active-version pointer references the fetched version; and
- version state is `accepted`.

Pending, unclassified, held, excluded, superseded, and candidate-only versions are never returned as live evidence.

If the database connection or query fails, the application returns no source pages. It never substitutes the old in-memory cache in database mode.

## Current operational state

- Supabase schema and all 18 pending source records are present.
- No source is active or classified.
- The FastAPI integration is implemented but not yet merged.
- The Render secret and mode flag have not been configured.
- No production deployment has been performed.

## Operator setup after merge

1. Open the Supabase project and choose **Connect**.
2. Select **Session pooler** and copy the PostgreSQL URI.
3. Put the database password into the URI locally; do not paste it into ChatGPT or a GitHub file.
4. Add that URI as the Render backend secret `SUPABASE_DATABASE_URL`.
5. Set `SOURCE_STORE_MODE=database`.
6. Add the same URI as a GitHub Actions repository secret named `SUPABASE_DATABASE_URL` when the scheduled refresh workflow is introduced.
7. Deploy manually only after the code and secrets are ready; verify the health endpoint and source-status endpoint before relying on the new path.

The user retains control of the Render deployment. No deployment is performed by this implementation.
