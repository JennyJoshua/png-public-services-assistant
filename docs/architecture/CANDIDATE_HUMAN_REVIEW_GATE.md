# Human review gate for discovered candidates

**Status:** Implemented as a pure, tested governance boundary. Not persisted and not connected to live chat or the configured source registry.

## Review rules

- Only a candidate with status `candidate_unreviewed`, `approved=false`, and no evidence class may enter the review function.
- A human reviewer identity and timezone-aware review timestamp are mandatory.
- Rejection produces a review record with no source record.
- Approval requires the reviewer to identify the institution/publisher and explicitly assign class A, B or C.
- Class D is never approvable. A general-web source may be assigned class C only; it cannot be represented as PNG government authority by domain appearance alone.
- Approved source records are activated through the existing lifecycle transition, which stamps the human review time.
- Unknown authority tier, document type, jurisdiction and language remain null. The function does not infer them from the URL or page content.

## Deliberate boundary

`review_candidate` is a pure function. It does not persist an audit record, mutate `sources.txt`, add a source to the live registry, fetch content, write the answer cache, or change answer selection. A returned approved `SourceRecord` is a review result, not automatic publication or deployment.

Before a production workflow, a separate durable store and reviewer interface must preserve the decision, reviewer, timestamp, rationale, source metadata and content version. Integration with live retrieval must then enforce eligibility at evidence selection and citation rendering.

## Tests

Mocked/unit tests verify the unreviewed-only entry gate, explicit reviewer and timestamp, class A/B/C approval, class D rejection, class C general-web treatment, rejection without source activation, unknown metadata preservation and HTTPS validation.
