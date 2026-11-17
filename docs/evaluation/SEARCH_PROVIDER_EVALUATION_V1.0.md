# Search Provider Evaluation Dataset v1.0

**Purpose:** Compare candidate search providers using the same Papua New Guinea/Pacific public-service queries and human-reviewed result judgments.  
**Status:** Evaluation framework only. No provider has been selected or connected.  
**Privacy:** Queries must be generic public-information searches. Never include personal identifiers, case details, contact information, health/financial data or conversation history.

## Evaluation procedure

1. Use the same query set, location assumptions, result limit and test window for each provider.
2. Capture each provider's raw results without modifying the rank order.
3. Record the provider's latency and quota/credit usage using the provider's own unit. Do not compare unlike quota units as if they were equivalent.
4. Independently fetch each result URL using the approved test process and record whether it succeeds, is blocked, errors or has not been checked.
5. Human reviewers assign:
   - **Relevance:** 0 = irrelevant/incorrect jurisdiction; 1 = partially relevant; 2 = directly relevant to the query.
   - **Source class:** A = approved authoritative primary source; B = recognised institution; C = general web; D = unverified/unsafe. A result must not receive A merely because its domain looks official.
6. Run the scoring tool. Review per-query results as well as provider averages; do not select a provider from one aggregate score alone.

## Required query set

| ID | Query |
|---|---|
| Q01 | Papua New Guinea Gulf Province provincial administration public services official |
| Q02 | Gulf Provincial Administration Papua New Guinea government departments services |
| Q03 | Papua New Guinea public service offices Gulf Province district services |
| Q04 | Papua New Guinea national identity registration official requirements PNGCIR |
| Q05 | Papua New Guinea passport application official requirements Department of Foreign Affairs |
| Q06 | Papua New Guinea business registration official IPA process |
| Q07 | Papua New Guinea tax registration official IRC taxpayer services |
| Q08 | Papua New Guinea education services Gulf Province official schools administration |
| Q09 | Papua New Guinea health services Gulf Province official hospital health authority |
| Q10 | Papua New Guinea land services official Land Commission process |
| Q11 | Papua New Guinea government public service fees application deadlines official source |
| Q12 | Papua New Guinea provincial government public service directory official |

## Dataset schema

One JSON file per provider:

- `schema_version`: must be `1.0`.
- `provider`: provider name.
- `evaluated_at`: ISO-8601 timestamp.
- `queries`: one entry per query with `query_id`, exact `query`, `latency_ms`, `usage_units` and ranked `results`.
- Each result has `rank`, `title`, HTTPS `url`, human-assigned `relevance` (0–2), human-assigned `source_class` (A–D or null), and `fetch_status` (`success`, `blocked`, `error`, `not_checked`).

Example result record:

```json
{
  "rank": 1,
  "title": "Example official service page",
  "url": "https://example.gov.pg/service",
  "relevance": 2,
  "source_class": "A",
  "fetch_status": "success"
}
```

Do not copy this illustrative URL into an actual evaluation.

## Metrics

The offline scorer reports:
- Precision@5 and Precision@10: fraction of the fixed top-k slots with relevance grade 1 or 2 (missing results count as non-relevant).
- nDCG@5 and nDCG@10: rank-sensitive relevance quality using grades 0–2.
- Mean count of class-A sources in the top 10.
- Mean number of successfully fetched URLs in the top 10.
- Mean query latency and total provider usage units when supplied.

The scorer does not decide relevance, source authority, legal correctness or suitability. Those remain human-reviewed decisions. A class-A count is a source-coverage indicator, not proof that a page is relevant or authoritative for every claim.

## Running the scorer

From the backend directory:

```bash
python -m app.search_evaluation tavily-results.json langsearch-results.json
```

The command is offline and makes no external requests. Keep raw result datasets and reviewer judgments in the project's approved repository location; do not store API keys or personal data in them.

## Provider selection gate

A candidate is eligible only after its terms, privacy, quotas, downstream page-fetch permissions and no-card free-tier conditions are reviewed. The query benchmark must demonstrate useful PNG/Pacific coverage, working URLs and acceptable latency. If no candidate passes, retain approved-source-only retrieval.
