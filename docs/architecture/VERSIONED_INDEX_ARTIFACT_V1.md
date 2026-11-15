# Versioned index artifact contract (schema v1)

## Status and scope

This is a validated artifact contract and read-only loader. It is not connected to
`retrieve_answer`, does not replace live source fetching, and does not change
production hosting configuration. A synthetic fixture is used only to test the
format; it is not evidence of source coverage or retrieval quality.

## Envelope

The UTF-8 JSON root object has exactly these fields:

| Field | Type | Rule |
|---|---|---|
| `schema_version` | integer | Strict integer (booleans rejected); currently `1` |
| `index_version` | string | Non-empty release identifier |
| `generated_at` | string | ISO-8601 timestamp with explicit timezone |
| `record_count` | integer | Non-negative strict integer equal to records length |
| `records_sha256` | string | Lowercase 64-character SHA-256 of canonical records JSON |
| `records` | array | Ordered passage records |

Canonical JSON uses UTF-8, sorted object keys, compact separators, Unicode
preservation, and rejects non-finite numeric values. The loader rejects duplicate
JSON keys and non-standard constants.

## Passage record

Every record has exactly: `source_id`, `document_id`, `passage_id`,
`source_url`, `institution`, `title`, `section_path`, `position`,
`text`, and `content_hash`.

- `source_url` must exactly match one HTTPS seed URL in
  `backend/app/source_registry.py`. Redirect destinations are not registry
  entries and are not accepted as artifact source URLs.
- `source_id` is `src_` plus the first 16 lowercase hex characters of
  SHA-256(source URL).
- `document_id` is `doc_` plus the first 16 lowercase hex characters of
  SHA-256(source ID, NUL, source URL).
- `institution` must match the registry entry.
- `passage_id` is globally unique; `position` is a non-negative strict integer
  unique within its document.
- `section_path` is an ordered array of non-empty strings.
- `content_hash` is SHA-256 of the exact UTF-8 passage text.

The stable source/document identifiers are deterministic for an exact registered
seed URL. If a source URL changes, it is treated as a new identity and requires
an explicit registry change and a new index version.

## Trust boundaries and deferred work

The digest detects accidental or unsophisticated content corruption; it is not a
digital signature and does not prove publisher authenticity. Registry membership
proves only that a URL is approved for fetching by this application, not that
the content is authoritative, current, or legally correct.

Before generating a real corpus index, the project still needs:
1. a reviewed source registry snapshot/version and source approval workflow;
2. a deterministic source-to-document ingestion and passage-generation pipeline;
3. representative corpus-size, startup-time, memory and packaging measurements;
4. Render filesystem/restart/rollback validation under the actual deployment;
5. retrieval quality and citation regression evaluation against approved source material.

No live retrieval integration or production rollout is included in this batch.
