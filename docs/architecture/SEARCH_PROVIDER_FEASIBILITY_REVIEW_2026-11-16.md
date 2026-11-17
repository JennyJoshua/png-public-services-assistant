# Search Provider Feasibility Review — 16 November 2026

**Project:** PNG Public Services Assistant  
**Architecture:** Simplified Hybrid RAG v1.1  
**Status:** Initial desk review only — no provider selected, account connected, API key created or runtime integration authorised  
**Decision rule:** Prefer a compliant free tier that requires no payment card, supports a server-side API integration, provides traceable URLs and can be evaluated on Papua New Guinea/Pacific queries.

## Executive finding

There are plausible no-card free search APIs, but the desk review is not enough to select one for production. The most promising candidates for a controlled technical evaluation are **Tavily Basic Search** and **LangSearch Web Search**. Their terms/privacy conditions need further review, and their relevance for Papua New Guinea and Pacific government sources must be measured with a fixed query set before selection.

No provider is selected by this report. Until that evaluation is completed, the application must retain its current approved-source-only behaviour.

## Candidate comparison

| Provider | Published free access (checked 16 Nov 2026) | Important limitations / terms findings | Initial disposition |
|---|---|---|---|
| Tavily | Researcher: 1,000 API credits/month; no credit card required. Basic search uses 1 credit; advanced search uses 2. Credits reset monthly and requests stop when exhausted. | Platform terms allow API integration with customer applications but also describe use as for the customer's internal business purposes. Terms permit broad processing/sharing of customer input with affiliates/vendors to provide/improve services; sensitive data categories are expressly restricted. Clarify public-facing application rights and avoid sending personal/sensitive data. | **Candidate for controlled evaluation**, subject to terms clarification and query minimisation. |
| LangSearch | Free Web Search plan; daily token allowance; titles, URLs, snippets, full webpage text, domain/date filters and up to 50 results/request. New accounts start at 5 requests/second. Query and returned content consume the shared daily token allowance. | Privacy policy says queries, API requests and usage patterns are collected, but does not clearly state retention periods or detailed processor/subprocessor arrangements. Terms are brief, revocable and allow service changes/discontinuation. No service-level commitment is published for the free plan. | **Candidate for controlled evaluation**, using generic non-personal queries only; privacy and continuity risks remain. |
| Exa | Free tier advertises $10 monthly credits plus onboarding credit; no payment method required. | Current terms restrict downloading, copying, distributing, transmitting, displaying, reproducing or publishing information obtained through the Services except limited browser caching. That wording creates a material compatibility concern for an application that sends retrieved page text to its own LLM and displays source evidence. | **Do not select** unless Exa provides written permission/clarification for this RAG use. |
| Firecrawl | Free tier: 1,000 credits/month, no card; Search costs 2 credits per 10 results, with extra page-scrape credits when full page content is requested. Free Search rate limit is 10 requests/minute. | Terms prohibit commercial use except where expressly authorised, and specifically prohibit using the service to determine eligibility for a government license. This is a poor fit for a public-service assistant that may discuss licensing eligibility. Zero-data-retention is an Enterprise feature, not the free tier. | **Do not select** without written authorisation and confirmation that intended use is permitted. |
| Brave Search API | $5 free credits/month, priced at $5/1,000 requests. | No standalone free plan; access to the monthly credit without a prepaid balance requires a credit card at signup. | **Not preferred** for this no-card pilot. Reconsider only if the owner elects to provide a suitable payment card and approves account setup. |
| Serper | 2,500 free queries advertised; no credit card required. | Public offer does not clearly state whether the free queries recur or expire. Serper describes its service as a Google SERP API; a sufficiently clear terms/privacy review for this specific downstream RAG use was not completed in this desk review. | **Hold** pending full terms, privacy and free-credit expiry review. |
| Google Custom Search JSON API | Existing customers have a published 100 free queries/day quota. | Closed to new customers; Google states existing customers must transition by 1 January 2027. Not a viable new integration. | **Exclude** for a new account. |
| DuckDuckGo Instant Answer API | No-key access is available for instant-answer data. | It is not a general ranked web-search API equivalent to the required discovery layer. | **Not suitable as the primary general-web search provider.** |
| Mojeek Search API | Published PAYG pricing from £2/1,000 requests. | A bank card is required to open an account even to claim the free test credit. | **Not preferred** for the no-card pilot. |
| Self-hosted SearXNG | Open-source and no API subscription charge. | Requires operating another service and relies on the availability/terms of configured upstream search engines. Public instances are not a dependable production dependency. | **Fallback research option**, not the first pilot choice. |

## Source links

- Tavily [pricing](https://www.tavily.com/pricing), [platform terms](https://www.tavily.com/terms), [API documentation](https://docs.tavily.com/documentation/api-reference/endpoint/search)
- LangSearch [pricing and limits](https://langsearch.com/pricing), [privacy policy](https://langsearch.com/privacy-policy), [terms](https://langsearch.com/terms-of-service), [developer documentation](https://docs.langsearch.com/)
- Exa [pricing](https://exa.ai/pricing), [terms of service](https://exa.ai/assets/Exa_Labs_Terms_of_Service.pdf)
- Firecrawl [pricing](https://www.firecrawl.dev/pricing), [terms of service](https://www.firecrawl.dev/terms-of-service), [zero-data-retention description](https://www.firecrawl.dev/blog/zero-data-retention)
- Brave [Search API pricing](https://api-dashboard.search.brave.com/documentation/pricing), [free-credit requirements](https://api-dashboard.search.brave.com/documentation/resources/help-feedback)
- Serper [official pricing/free query offer](https://serper.dev/)
- Google [Custom Search JSON API availability notice](https://developers.google.com/custom-search/v1/overview)
- Mojeek [Search API pricing and account requirements](https://www.mojeek.com/services/search/web-search-api/)

## Required next evaluation

Before selecting a provider, run the same fixed query set through each eligible provider and record raw result URLs, titles, snippets/page content, ranks, latency, errors and token/credit usage.

Suggested evaluation queries:
1. `Papua New Guinea Gulf Province provincial administration public services official`
2. `Gulf Provincial Administration Papua New Guinea government departments services`
3. `Papua New Guinea public service offices Gulf Province district services`
4. `Papua New Guinea national identity registration official requirements PNGCIR`
5. `Papua New Guinea passport application official requirements Department of Foreign Affairs`
6. `Papua New Guinea business registration official IPA process`
7. `Papua New Guinea tax registration official IRC taxpayer services`
8. `Papua New Guinea education services Gulf Province official schools administration`
9. `Papua New Guinea health services Gulf Province official hospital health authority`
10. `Papua New Guinea land services official Land Commission process`
11. `Papua New Guinea government public service fees application deadlines official source`
12. `Papua New Guinea provincial government public service directory official`

Score each provider on:
- Relevant PNG/Pacific results in the top 5 and top 10.
- Official PNG government/agency coverage and correct jurisdiction.
- Precision (irrelevant or misleading results in the top 10).
- Result freshness and publication-date availability.
- Working URLs and page fetch success.
- Citation/provenance completeness.
- Median and worst-case latency over repeated runs.
- API stability, rate limits and quota consumption.
- Terms/privacy compatibility with a public-facing RAG application.

A search result from a provider is not proof that its content is authoritative. Every page must still be fetched/validated, source-classified and independently checked before use in an official answer.

## Privacy and safety constraints for any provider

- Never send NID numbers, passport numbers, addresses, phone numbers, email addresses, health details, financial details, passwords, credentials or other sensitive personal information to a search provider.
- Convert user questions to minimal, generic search queries that preserve the public-service topic and jurisdiction but remove identifying or sensitive details.
- Keep provider credentials server-side; never expose them to the browser.
- Do not send conversation history to the search provider.
- Do not use the provider's own generated-answer endpoint as a substitute for the approved Groq model and application-side evidence verification.
- Enforce a hard free-quota cap and fail closed when the quota is exhausted. No auto-upgrade, auto-reload, paid overage or silent provider switch.
- Keep a provider-neutral adapter so the project can disable or replace a provider without changing the rest of the RAG engine.

## Current decision

**No search provider is selected.** Tavily and LangSearch are the leading candidates for a non-sensitive, controlled comparison, not approved production dependencies. If their terms/privacy or PNG/Pacific relevance do not pass review, keep approved-source-only retrieval until another compliant provider is found.
