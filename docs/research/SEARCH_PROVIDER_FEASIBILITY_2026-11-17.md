# Search Provider Feasibility Review — 17 November 2026

**Project:** PNG Public Services Assistant  
**Architecture:** Owner-approved Simplified Hybrid RAG v1.1  
**Purpose:** Assess provider feasibility for bounded general-web discovery. This is a desk review, not an integration approval or a live API quality test.

## Executive result

**Tavily is the strongest candidate for a controlled free-tier technical pilot, but it is not yet approved as the production search provider.** Its current free Researcher plan advertises 1,000 API credits per month without a credit card; basic search costs one credit; and its API supports Papua New Guinea as a country-ranking boost. Tavily also expressly permits customer-facing and commercial application use on the free plan.

Two blockers remain before provider selection:
1. The project has not run an authenticated Tavily API test against a fixed PNG/Pacific evaluation set. Country boosting is not evidence of good local result quality.
2. Privacy and shared-cache terms need to be handled deliberately. Search queries must be stripped of personal details before leaving the backend. Tavily's privacy policy says query data may be used to improve responses and may be shared with third-party search-index providers in limited circumstances. Tavily's current help guidance also says cross-customer reuse of cached results should be confirmed with its support team.

Therefore, **do not integrate or configure Tavily in production yet**. Keep approved-source-only retrieval as the operating boundary until the free-tier test and privacy/cache decisions are complete. No provider credential, account, paid service, or Render setting is created or changed by this review.

## Provider comparison

| Provider | Free access and quota | PNG/Pacific support | Terms and operational fit | Result |
|---|---|---|---|---|
| Tavily Search API | 1,000 credits/month on Researcher free plan; no credit card required. Basic/fast/ultra-fast search costs 1 credit; advanced costs 2. | API supports a `country` ranking boost and explicitly lists Papua New Guinea. It can also boost English-language results. | Explicitly permits customer-facing and commercial applications on the free plan. API key must remain server-side. Search result metadata/snippets can be stored, but shared caching across multiple customers should first be confirmed with Tavily. Query data handling requires minimisation. | **Best pilot candidate; not production-approved.** |
| Brave Search API | No standalone free plan. Current pricing gives $5 monthly credits, but accessing the credit without prepayment requires a credit card at signup. Listed search price is $5 per 1,000 requests. | Independent web index; no PNG-specific result-quality evidence reviewed. | Terms restrict storing/caching search results beyond transient operational storage, prohibit model training/benchmarking with results, and impose end-user contractual obligations. This is a poor fit for reusable evidence caching and the current privacy/operational model. | Not selected for the free-first pilot. |
| Google Custom Search JSON API | Official documentation says 100 free queries/day, but the API is closed to new customers and existing customers must transition by 1 January 2027. | Existing Programmable Search offerings have domain restrictions for new engines; not a dependable new full-web API path. | Not available for a new integration under the project's current circumstances and near-term retirement timeline. | Not viable for a new project integration. |

## Tavily findings

### Cost and quotas
- Researcher plan: free, 1,000 API credits/month, no credit card required.
- Basic, fast and ultra-fast search: 1 credit per request.
- Advanced search: 2 credits per request.
- Credits reset on the first day of each month.
- Requests stop when the free credits are exhausted unless the account is upgraded.

Implication: at the basic-search rate, the headline allowance is up to 1,000 search requests/month before any additional credit-consuming endpoints. This is a quota ceiling, not a usage forecast or a guarantee of uninterrupted service.

### PNG and Pacific relevance
The Search API's `country` parameter boosts results from a selected country and explicitly includes `papua new guinea` in its supported values. It also supports language boosting, domain inclusion/exclusion and a maximum of 20 results.

This is technically useful for PNG queries, but does **not** prove that the index returns the best PNG government, provincial, district or Pacific sources. The project must test actual result relevance before adopting the provider.

### Permitted application use and output handling
Tavily's help centre expressly says its free Researcher plan may be used in customer-facing applications and commercial products. API keys must be kept server-side; direct end-user access to the API is prohibited; and the API itself must not be resold.

Tavily's November 2026 help guidance says result metadata, snippets and API output may be stored and cached. However:
- Original webpage content remains subject to the publisher's copyright and website terms.
- Tavily asks customers to contact support before sharing cached results across multiple customers of their own.
- Generated answers have additional presentation/use conditions and should not be treated as human-written.

The app should therefore keep Tavily result metadata distinct from retrieved source content, preserve publisher URLs, and not assume that permission to store search output grants permission to republish full third-party webpages.

### Privacy
Tavily's privacy policy says query data is collected and used to retrieve content; portions may be used to improve future responses; and queries may be shared with third-party search-index providers in limited cases. It advises users not to include personal information in queries if they do not want it shared with such providers.

Required project safeguards before any integration:
- Generate search queries from the minimum necessary public-service topic and jurisdiction.
- Remove names, phone numbers, email addresses, NID/passport numbers, addresses, uploaded-document text and other user-specific details before provider submission.
- Never send conversation history, private uploads, credentials or complete chat transcripts to a search provider.
- Keep the API key in a backend-only environment variable.
- Do not log raw provider queries if they could contain personal data.
- Document the provider and its query-data handling in the app's privacy notice before production use.

## Required PNG/Pacific provider test

Before a final selection, run the same fixed query set through the candidate provider and the existing approved-source retrieval path. Record exact request parameters, time, returned URLs, titles, snippets, result order, response time, credit usage, and errors. Do not use an LLM to score the provider.

Suggested query set:
1. Papua New Guinea National Identification registration process and required documents.
2. PNG business registration requirements and IPA forms.
3. Papua New Guinea TIN registration for an individual and small business.
4. PNG passport application requirements and official forms.
5. PNG police clearance application process.
6. PNG driver licence application and renewal requirements.
7. Gulf Province government and provincial public-service information.
8. PNG public service information from official agency domains.
9. Fiji public-service procedure (Pacific comparison/control).
10. Solomon Islands public-service procedure (Pacific comparison/control).

For each query, score top-5 results against a manually reviewed reference list:
- official/primary PNG source found;
- correct agency and jurisdiction;
- relevant procedure or document found;
- result is accessible and fetchable under site rules;
- date/effective-date information available or explicitly unknown;
- irrelevant, duplicate or non-authoritative results.

Report precision@5 and recall@5 only after the reference list is established and independently reviewed. Do not infer provider quality from a handful of web searches or from country-boost support alone.

## Recommended decision

1. Retain approved-source-first retrieval.
2. Keep Tavily as the first candidate for a free-tier, non-production API pilot.
3. Do not create an account, add an API key, alter Render configuration, or deploy the integration as part of this desk review.
4. Before a production provider decision, complete the fixed PNG/Pacific result-quality test and document query minimisation, privacy notice and cross-customer cache handling.
5. If the candidate fails quality, terms, privacy or free-quota requirements, remain in approved-source-only mode. Do not silently substitute another provider or incur a paid cost.

## Primary references

- Tavily pricing: https://www.tavily.com/pricing
- Tavily Search API reference (credit cost, country parameter, result limits): https://docs.tavily.com/documentation/api-reference/endpoint/search
- Tavily permitted use in customer-facing/commercial apps: https://help.tavily.com/articles/5880393096-permitted-use-customer-applications
- Tavily storing, caching and retaining output: https://help.tavily.com/articles/1612400809-storing-caching-retaining-output
- Tavily privacy policy: https://www.tavily.com/privacy
- Brave Search API pricing: https://api-dashboard.search.brave.com/documentation/pricing
- Brave Search API terms: https://api-dashboard.search.brave.com/documentation/resources/terms-of-service
- Google Custom Search JSON API status and transition notice: https://developers.google.com/custom-search/v1/overview
- Google Custom Search API terms: https://developers.google.com/custom-search/terms

**Review limitation:** This assessment is based on publicly available provider documentation accessed on 17 November 2026. Provider pricing, quotas, terms and privacy policies can change. It does not establish legal advice, an executed provider contract, or actual PNG/Pacific search quality.
