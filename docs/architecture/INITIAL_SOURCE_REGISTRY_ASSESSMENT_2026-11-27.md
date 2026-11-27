# Initial Source Registry Assessment

**Assessment date:** 2026-11-27  
**Scope:** The 18 URLs currently configured in `backend/sources.txt`  
**Purpose:** Establish an evidence-based starting point for source governance and automated refresh.  
**Important:** This is an assessment proposal, not a source approval, legal validation, or registry status change. No source is activated by this document.

## 1. Current repository state

The source registry constructs every entry with the default `pending_review` status. The registry entries do not currently carry source class, authority tier, document type, jurisdiction, language, publication date, effective date, or review timestamp. This is appropriate as a fail-closed default until an initial assessment is recorded.

The existing retrieval contracts define:
- **A — Approved authoritative:** may support primary claims.
- **B — Recognised institutional:** supporting evidence only.
- **C — General web:** supplementary context only; not official requirements.
- **D — Unverified/unsafe:** excluded.

A class recommendation below does not itself activate a source. Initial activation still requires a human review record with a timezone-aware timestamp.

## 2. Source-by-source assessment

| # | Configured source | Assessment evidence / concern | Provisional class recommendation | Initial disposition |
|---:|---|---|---|---|
| 1 | ICA — passport application | Legacy configured ICA path. Current public passport guidance is now surfaced under the Immigration and Citizenship Services Authority (ICSA) domain; old ICA content and current authority continuity need reconciliation. | A candidate, pending authority continuity check | Keep pending; replace/confirm canonical URL before activation |
| 2 | ICA — passport FAQ | Same legacy authority/path concern; FAQ may contain operational details that can become stale. | A candidate, pending verification | Keep pending |
| 3 | ICA — passport application forms | Official-form endpoint is potentially authoritative, but form version and current issuing authority need verification. | A candidate, pending verification | Keep pending |
| 4 | ICA — visa and migration service fees | Fees are high-impact and time-sensitive; legacy path requires confirmation against current ICSA/eVisa information. | A candidate, pending verification | Keep pending; fee changes always high-risk |
| 5 | PNGCIR — NID registration information | Official PNG Civil and Identity Registry page; currently describes in-person identity capture and registration requirements. | A | Keep pending until initial reviewer confirms page and agency details |
| 6 | PNGCIR — registry home/about and contacts | Official registry domain, but primarily institutional/contact context rather than a specific service rule. | B | Keep pending |
| 7 | RPNGC — ePolice clearance | Official Royal Papua New Guinea Constabulary page with current online process details, including geographic availability and fingerprint steps. | A | Keep pending until initial reviewer confirms scope and currency |
| 8 | RPNGC — police clearance types and requirements | Official RPNGC page describing certificate types, requirements, fees and lodgement. High-impact fee/process content. | A | Keep pending; future changes to fees/requirements escalate |
| 9 | RTA — driver licensing | Official regulator page, but includes historical legal references and states service delivery is handled by MVIL/provincial governments. Current legislation and operational details need validation. | A candidate | Keep pending; legal/currentness review required |
| 10 | IPA — prescribed forms | Official PNG Registry Services page listing prescribed forms and fees. Strong primary-source candidate for registry forms and fees. | A | Keep pending until form/fee content is reviewed |
| 11 | IPA — 2022 transitional online registry PDF | Official institutional publication, but dated December 2022 and likely historical/transitional rather than current operational instructions. | B candidate for historical context | Keep pending; do not use as current procedure without corroboration |
| 12 | IRC — TIN registration | Official IRC URL is explicitly marked “VERIFY it loads” in source configuration. Endpoint availability and current procedure have not been confirmed in this assessment. | A candidate | Keep pending; verify endpoint and current instructions |
| 13 | IRC — tax forms | Official IRC URL is explicitly marked “VERIFY it loads”; forms may change and version dates matter. | A candidate | Keep pending; verify endpoint and form versions |
| 14 | IRC — small business TIN4I PDF | Official-looking static IRC PDF hosted on the IRC domain, dated 2021 by its path. Current validity of the form is unconfirmed. | A candidate if confirmed current; otherwise historical | Keep pending; confirm current form version |
| 15 | Education — 2026 Government Free Education Policy PDF | Official Ministry of Education Ministerial Policy Statement 01/2026, signed/dated 27 January 2026. The document states the 2026 policy and is primary policy evidence for that year. | A | Keep pending until reviewer confirms document authenticity and scope |
| 16 | Education — Government Tuition Fee Subsidy report page | Configured page currently returns a Page Not Found result. | Not classifiable until resolved | Keep pending in registry; mark fetch issue and locate replacement page |
| 17 | Customs — importer/exporter TIN registration | Official PNG Customs page exists at a different current path (`/trade/tin_reg`) and contains detailed registration requirements. Configured `/ict/tin_reg` path needs redirect/canonical URL validation. | A | Keep pending; update canonical URL only after repository-level redirect check |
| 18 | DICT — digital government progress article | Official DICT article, dated 28 August 2025, describing digital-government programme progress. It is an institutional news/context source, not the authoritative source for individual service requirements. | C | Keep pending; supplementary context only |

## 3. Evidence consulted

The following official/public pages were discoverable during this assessment:

- PNGCIR registration information: https://pngcir.gov.pg/nid-registration-information/
- RPNGC online police clearance: https://rpngc.gov.pg/advice-services/epolice-clearance/
- RPNGC police clearance: https://rpngc.gov.pg/advice-services/police-clearance/
- RTA driver licensing: https://www.rta.gov.pg/licences-approvals/driver-licensing/
- IPA prescribed forms: https://www.ipa.gov.pg/public/prescribedforms.aspx
- Education 2026 policy PDF: https://education.gov.pg/admin/images/products/03_02_26%20_N_MPS_on%20GFEP_202695.pdf
- Education tuition-fee subsidy page (currently not found): https://www.education.gov.pg/Government-Tuition-Fee-Subsidy-Report/
- Customs importer/exporter registration: https://www.customs.gov.pg/trade/tin_reg
- DICT digital government article: https://www.ict.gov.pg/a-digital-leap-for-png-dict-secretary-explains-progress-in-digital-government-journey/
- Current ICSA passport guidance: https://icsa.gov.pg/passports/apply-for-or-renew-a-passport

Search discovery is not a substitute for a direct fetch, legal review, or verification of the exact configured URL. The recommendations are therefore deliberately provisional.

## 4. Initial decisions and unresolved work

1. **Do not activate any source solely from this assessment.** All 18 remain `pending_review` until a reviewer confirms the exact page, issuing authority, relevance, currentness, and source class.
2. Resolve the ICA-to-ICSA transition and update the four passport/visa URLs only after direct validation of the new official endpoints.
3. Confirm whether the RTA page's referenced legislation and service-delivery arrangements remain current.
4. Replace the missing Education subsidy page with a verified official page, or remove it from the active refresh list after an explicit registry decision.
5. Verify the IRC pages and confirm whether the 2021 TIN4I PDF remains current.
6. Confirm the Customs redirect and use the canonical URL only after checking the exact redirect chain.
7. Treat fees, eligibility, legal rules, application requirements, forms, deadlines, and service availability as high-impact content. Changes to these fields must be held for review, even for an active Class A source.
8. Do not treat host trust or a successful fetch as evidence approval.

## 5. Recommended initial review order

Prioritise service pages that directly inform citizens' requirements:
1. PNGCIR NID/birth registration.
2. RPNGC police clearance and ePolice clearance.
3. Education 2026 Free Education Policy.
4. IPA prescribed forms.
5. RTA driver licensing.
6. IRC TIN registration and forms.
7. Customs importer/exporter registration.
8. ICSA passport/visa pages after canonical-source reconciliation.
9. DICT article as supplementary context only.

## 6. What this assessment does not do

- It does not change `backend/sources.txt` or source-registry metadata.
- It does not activate or approve any source.
- It does not change live RAG retrieval or answer selection.
- It does not accept changed content automatically.
- It does not fetch arbitrary URLs or broaden the fetch allowlist.
- It does not claim that the legal status of any rule, fee, form, or policy has been independently validated.

The next implementation step is to connect source governance to the live retrieval path and ensure only active, classified sources can supply answer evidence. Routine refresh automation should follow only after the initial source activation decisions and persistent change-history design are in place.
