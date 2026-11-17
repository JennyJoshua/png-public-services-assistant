# PNG and Pacific Search Provider Evaluation Protocol

**Project:** PNG Public Services Assistant  
**Architecture:** Simplified Hybrid RAG v1.1  
**Status:** Batch 0 evaluation design; no provider quality result has yet been measured  
**Candidate provider:** Tavily Search API (free Researcher plan)  
**Evaluation mode:** Manual, reproducible, non-production pilot using synthetic public-service queries

## 1. Purpose

This protocol defines how to test whether a search provider finds relevant and authoritative Papua New Guinea public-service sources, while checking Pacific coverage, provider limits, latency, errors and safe downstream page retrieval.

A provider's country parameter, marketing claims, result snippets or generic global benchmark do not prove PNG relevance. Do not select a production provider until the fixed query set has been run and its results reviewed.

## 2. Provider state and test prerequisites

Tavily is the leading candidate for a controlled pilot, not yet a production-approved provider.

Before a live API run:
1. Use a free account only; do not enable pay-as-you-go or enter a paid plan.
2. Set a monthly credit cap in the provider dashboard if supported.
3. Keep the API key in a server-side GitHub Actions secret or backend environment variable; never commit it or expose it to frontend code.
4. Do not use real user questions or personal data. Use only the synthetic queries below.
5. Do not send chat history, private documents, personal identifiers or uploaded document content.
6. Do not use shared cross-customer result caching until Tavily confirms that the intended use is covered by the selected plan.
7. Do not retain full page content from search results unless the publisher's rights and terms permit it. Preserve URLs and short metadata for evaluation.
8. Keep this pilot separate from the live application request path. No production deployment or user-facing search is authorised by this protocol.

Tavily's current free Researcher plan is documented as 1,000 credits/month without a credit card; basic search uses one credit and advanced search two. Free access is provided as-is without production support or warranties. Recheck current pricing, quotas and terms at execution time.

## 3. Fixed synthetic query set

Use the exact query text below for each run. Use Papua New Guinea as the country preference for PNG queries where the API supports it. Use the relevant country preference for Fiji and Solomon Islands controls. Do not add personal details.

| ID | Exact query | Jurisdiction | Reference sources to assess against | Purpose |
|---|---|---|---|---|
| Q01 | Papua New Guinea National ID registration process official requirements form and in-person fingerprint capture | PNG | https://pngcir.gov.pg/nid-registration-information/ ; https://pngcir.gov.pg/downloads/ | NID procedural retrieval and current source discovery |
| Q02 | Papua New Guinea business name registration company incorporation official IPA process forms fees | PNG | https://www.ipa.gov.pg/public/howto.aspx?cn=RegisterBusinessName&ctk=CompanyHowTo ; https://www.ipa.gov.pg/public/prescribedforms.aspx?lang=en-US | Distinguish business-name registration from company incorporation; high-impact fee/form retrieval |
| Q03 | Papua New Guinea individual taxpayer identification number TIN registration official IRC form proof of identity | PNG | https://irc.gov.pg/pages/know-your-taxes/tin-registration ; https://static.irc.gov.pg/2021/December/E6wskE-media-IRC-TIN4I-Registration.pdf | TIN source discovery and PDF handling |
| Q04 | Papua New Guinea passport application official Immigration and Citizenship Authority requirements forms | PNG | https://ica.gov.pg/passport/applying-for-a-png-passport ; https://ica.gov.pg/passport/application-forms | Passport authority and application requirements |
| Q05 | Papua New Guinea police clearance application official RPNGC online process requirements | PNG | https://rpngc.gov.pg/advice-services/epolice-clearance/ ; https://rpngc.gov.pg/advice-services/police-clearance/ | Police clearance and online/offline procedure |
| Q06 | Papua New Guinea driver licence application renewal official Road Transport Authority requirements | PNG | https://rta.gov.pg/licences-approvals/driver-licensing/ | Licensing and responsible-agency discovery |
| Q07 | Gulf Province Papua New Guinea provincial government public services districts administration contact information | PNG / Gulf Province | https://www.gulf.gov.pg/ ; https://www.gulf.gov.pg/contact-us/ | Provincial and remote-area discovery; test whether local sources are surfaced |
| Q08 | Papua New Guinea government public service information education free education policy official government sources | PNG | https://www.education.gov.pg/Government-Tuition-Fee-Subsidy-Report/ ; https://www.education.gov.pg/admin/images/products/03_02_26%20_N_MPS_on_GFEP_202695.pdf | Broader national source discovery and PDF coverage |
| Q09 | Fiji government online public services business registration official e-services portal | Fiji | https://www.fiji.gov.fj/ ; https://www.businessnow.gov.fj/e-service/ ; https://directory.digital.gov.fj/ | Pacific comparison/control; confirm the provider can honour jurisdiction |
| Q10 | Solomon Islands government public services portal official government services | Solomon Islands | https://solomons.gov.sb/ ; https://solomons.gov.sb/ministry-of-public-service/ | Pacific comparison/control; confirm jurisdiction and official gateway discovery |

Reference URLs are a starting reference list, not an assertion that every page is currently accessible, complete, current or suitable for every claim. A reviewer must open and verify each reference page before scoring a run. If a reference has moved, record the redirect and new canonical URL; do not silently replace the reference.

## 4. Run procedure

For each query:
1. Record UTC timestamp, provider/API version, endpoint, request parameters, country/language settings, search depth and requested result limit.
2. Record response time and provider credit usage.
3. Capture top-five results in provider rank order: title, URL, domain, snippet, publication date (if supplied), provider rank and any error/omission.
4. Do not treat a provider-generated answer as evidence. Score search results only.
5. Check whether each candidate URL is HTTPS, accessible, relevant, jurisdictionally correct and fetchable under site rules. Do not bypass blocked pages.
6. Classify each result under the project source-class policy (A/B/C/D), based on the exact page and topic, not just the domain.
7. Record duplicates, redirects, dead links, irrelevant results, stale pages and non-authoritative results.
8. Repeat the identical query once only if measuring repeatability; do not cherry-pick the better run.

Use the same fixed query set and scoring rules for every provider. Do not change query wording after seeing one provider's results.

## 5. Scoring

### Relevance
A result is relevant only when it materially helps answer the exact service query in the correct jurisdiction. A result about the same broad topic in another country is not relevant.

- Relevant@5 = number of relevant results in the top five.
- Precision@5 = relevant top-five results / 5. If fewer than five are returned, record both the raw count and the denominator actually returned; do not inflate the score.
- Recall@5 = number of manually verified reference sources found in top five / number of manually verified reference sources in the query's reference set.
- Report query-level scores and macro-average across queries. Keep PNG-only and Pacific-control results separate.
- Report Class A hit rate separately from general relevance; do not use Class C popularity to mask failure to find primary PNG sources.

### Quality and safety dimensions

For each query, report:
- correct jurisdiction;
- Class A primary-source discovery;
- Class B support-source discovery;
- relevance and duplication;
- source accessibility and permitted fetchability;
- date/effective-date visibility;
- HTTPS and redirect safety;
- response latency;
- credit consumption;
- errors, rate limits and quota behaviour;
- repeatability of result order and source set.

Do not invent a universal pass threshold after seeing results. Define thresholds before the live run using the project's answer-risk profile. A minimum pilot gate should require: no personal data sent; no policy-disallowed source fetched; correct country handling; stable normalized response; and at least one Class A result for each query where the verified reference set contains an accessible Class A source. Any query missing its primary reference must be reviewed before provider selection.

## 6. Privacy and retention controls

- Queries are synthetic and public-service oriented.
- No user names, contact details, NID/passport numbers, addresses, account data, personal case histories or private documents.
- No chat history or raw user prompt is sent.
- If a future user question contains personal data, derive a general topic-only query or skip external search.
- Do not log provider API keys, authorization headers, full request bodies or raw personal queries.
- Store only the minimum evaluation metadata needed to reproduce and review results.
- Do not share cached results across customers until the provider confirms permission.
- Update the product privacy notice before user-facing provider use.

Tavily's published privacy policy says query data may be used to improve future responses and may be shared with third-party search-index providers in limited circumstances. This risk is why the pilot uses synthetic queries only.

## 7. Decision record template

Record the following after execution:

- Provider, plan and API version:
- Test date/time (UTC):
- Country/language settings:
- Query count:
- Total credits used:
- Total errors / 429 / timeouts:
- Median and p95 latency:
- PNG macro Precision@5:
- PNG macro Recall@5:
- PNG Class A hit rate:
- Pacific-control Precision@5 / Recall@5:
- Broken or blocked reference pages:
- Query privacy/minimisation result:
- Terms/cache/use limitations:
- Decision: pilot passes / pilot fails / more evidence required:
- Unresolved risks and owner decisions:

No score or provider selection is complete until this record is populated from an actual run. Do not claim provider quality based on this protocol alone.

## 8. Primary provider references

- Tavily billing and free quota (updated 4 November 2026): https://help.tavily.com/articles/8298987937-billing-credits-usage-limits
- Tavily Search API: https://docs.tavily.com/documentation/api-reference/endpoint/search
- Tavily permitted use and customer applications (updated 2 November 2026): https://help.tavily.com/articles/5880393096-permitted-use-customer-applications
- Tavily storing, caching and retaining output (updated 2 November 2026): https://help.tavily.com/articles/1612400809-storing-caching-retaining-output
- Tavily privacy policy: https://www.tavily.com/privacy
- Tavily platform terms: https://www.tavily.com/terms

**Review limitation:** This document defines a reproducible test. It does not report live API results, establish legal advice, create a Tavily account, authorise a paid service, or approve production use.
