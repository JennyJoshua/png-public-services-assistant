# Bounded candidate-page fetching

**Status:** Implemented as an isolated, opt-in retrieval helper. Not connected to live chat, source approval, or the answer cache.

## Bounds and policy

- At most five candidate URLs are accepted per call; at most two page fetches run concurrently.
- Only clean HTTPS URLs on the standard port are accepted. Credentials, fragments, localhost, local hostnames, non-public IP literals and non-public DNS answers are rejected.
- Redirects are handled manually and each destination is revalidated; no more than three redirects are followed.
- `robots.txt` is checked before page retrieval. A disallow rule, robots fetch failure, or ambiguous robots response blocks retrieval.
- Only HTML/XHTML is accepted. The response is limited to 1 MB and extracted text to 12,000 characters.
- Requests use bounded timeouts, a project user-agent and `trust_env=False`.
- Extracted pages retain URL, final URL, domain, provider, rank and retrieval time.
- Every result is labelled `candidate_unreviewed`, has no evidence class and has `approved=false`. It is not added to the configured source registry or trusted cache.

## Important security limitation

DNS is checked immediately before each outbound request and every redirect hop. This is a preflight control, not connection-level DNS pinning; a DNS-rebinding race is therefore not fully eliminated. Do not expose this helper to arbitrary unauthenticated URLs or treat it as the final SSRF security boundary. A production integration must add connection-level address pinning (or an equivalent controlled egress proxy), provider terms/rate-limit checks, and a reviewed source-classification workflow.

## Deliberate exclusions

This helper does not crawl links, fetch PDFs, bypass logins/paywalls/anti-bot controls, change source lifecycle, promote content, classify A/B/C/D, or alter live answer selection. It fails closed when robots policy cannot be confirmed.

## Tests

Mocked tests cover URL validation, public/private DNS results, HTML extraction, robots denial/failure, redirect rejection, unreviewed metadata and the five-candidate cap.
