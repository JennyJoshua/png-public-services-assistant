# Batch 2.3 — Representative source index builder

## Status

This batch adds a repeatable, local-only ingestion pipeline for the exact URLs in
`backend/app/source_registry.py`. It creates a real index only when the operator
runs the builder against the live approved sources. No live source text is
fabricated or checked into this repository.

## Scope and safeguards

- Fetches only exact seed URLs in the approved registry; it does not crawl links.
- Uses HTTPS and follows at most four redirects, only when every redirect remains
  on the original approved host.
- Checks each host's `robots.txt` before fetching. A robots policy that cannot be
  retrieved is treated as unavailable and fails closed; a 404 means no published
  robots file was found.
- Limits concurrency to three, request timeouts, response size, extracted page
  text, and passage length.
- Extracts heading paths, paragraphs, list items, definition lists, and table rows
  with table-header labels.
- Creates stable source/document/passage IDs and SHA-256 passage hashes compatible
  with the schema-v1 validator.
- Writes a separate audit manifest containing status, fetch timestamp, final URL,
  response size, passage count, and extracted-text hash. It does not duplicate
  source text in the manifest.
- Writes generated outputs locally and atomically. The live RAG endpoint remains
  unchanged and does not load this artifact.

## Run locally

From the `backend/` directory:

```bash
pip install -r requirements.txt
python scripts/build_index.py --index-version png-public-services-2026-11-v1
```

The default outputs are:

- `backend/data/public-services-index-v1.json`
- `backend/data/public-services-index-v1.manifest.json`

At least three source pages must be successfully indexed by default. To deliberately
accept fewer, use `--min-sources N`; never lower the threshold merely to conceal
source failures. The builder refuses to write outputs when the minimum is not met.

Validate the artifact using:

```bash
python -c "from app.index_artifact import load_index_artifact; print(len(load_index_artifact('data/public-services-index-v1.json').records))"
```

## Evidence and acceptance criteria

A generated manifest is required to report:
- how many registered pages were attempted and successfully indexed;
- which pages failed and why;
- when each page was checked;
- the final same-host URL, HTTP status, response bytes and passage count;
- artifact SHA-256 and per-passage hashes.

A source counts as indexed only when it returns HTTP 200 HTML, passes the host and
robots checks, and yields at least 80 characters of extractable content. These
checks establish technical retrievability, not legal authority, accuracy, freshness,
or permission to redistribute.

## Content rights and source authority

The index is intended for controlled retrieval and evaluation, not republishing
the source websites. Review each site's terms, copyright notices, and applicable
government reuse rules before storing or distributing a corpus. The builder does
not infer that a `.gov.pg` domain grants unrestricted reuse. The source owner
should separately approve durable storage and any public redistribution.

## Explicitly deferred

- No live retrieval integration or production switch.
- No Render configuration, deployment, persistent disk, database, or paid service.
- No automatic scheduled refresh or arbitrary-link crawling.
- No claims about real corpus size, source coverage, retrieval quality, startup
  time, memory, or Render filesystem durability until a real build and operational
  measurements have been run.
- No committing generated source-content artifacts to Git.
