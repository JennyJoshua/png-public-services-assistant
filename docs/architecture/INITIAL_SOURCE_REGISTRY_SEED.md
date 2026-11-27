# Initial Source Registry Seed

The migration `20261127000500_seed_initial_pending_source_registry.sql` inserts the exact 18 URLs from `backend/sources.txt` into the dedicated Supabase private source registry.

## Safety defaults

Every seeded row is inserted with:

- `status = pending_review`
- `source_class = unverified_unsafe`
- `active_version_id = NULL`

The migration does not fetch pages, infer authority, approve evidence, or change live retrieval. It is idempotent for an existing registered URL and does not overwrite an existing record's governance state.

## Initial database verification

Verified after applying the migration:

| Measure | Count |
|---|---:|
| Total source records | 18 |
| Pending review | 18 |
| Active | 0 |
| Classified | 0 |
| Active version pointers | 0 |

## Known special cases retained in status reasons

- Four legacy ICA pages remain pending until the current successor authority and current guidance are verified.
- IPA's 2022 transitional notice and IRC's 2021 TIN4I form are historical documents and must not be treated as current procedure without corroboration.
- Education's tuition-fee subsidy URL was previously reported unavailable and remains eligible for retry.
- Customs' configured URL requires canonical-path validation.
- DICT's article is institutional progress context, not authoritative service requirements.

## Next stage

The next batch adds a controlled assessment/refresh runner and persists fetched snapshots and deterministic decisions. A source remains ineligible for live retrieval until the runner's hard gates produce an activation decision and a known-good version is committed as active.
