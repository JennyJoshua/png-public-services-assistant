# Source content change detection and review gate

**Status:** Implemented in the in-memory source fetcher; no automatic source activation or candidate promotion.

## Behaviour

- Each successful fetch computes a SHA-256 hash of the extracted text.
- The first usable fetch establishes the in-memory baseline for that running service instance.
- If a later fetch has a different hash, the current cached copy is retained for retrieval and the changed copy is held separately as a pending candidate.
- The source status reports the baseline hash, candidate hash, change-detection timestamp, `content_changed` and `review_required`.
- Subsequent refreshes cannot clear an outstanding review gate automatically, including when the old content reappears.
- Failed fetches continue to preserve the last good cached copy.

## Boundaries and limitations

This is an in-memory safety gate, not a durable version store. A Render restart loses the cache and pending candidate, as it does today. It does not prove whether a change is material, identify publication/effective dates, compare semantic meaning, or provide a human approval UI. It does not activate sources or classify authority. The existing registry status and A/B/C/D evidence rules remain separate.

A later durable change-review workflow must persist candidate versions and reviewer decisions before this gate can be used as a long-term audit record. Until then, source changes must not be silently treated as reviewed or officially current.

## Tests

Mocked HTTP tests verify that changed content is detected, the previous good copy remains in use, candidate hashes are reported, and a pending review gate cannot be cleared by an automatic refresh.
