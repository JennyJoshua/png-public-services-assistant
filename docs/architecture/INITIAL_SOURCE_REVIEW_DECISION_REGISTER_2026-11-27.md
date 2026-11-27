# Initial Source Review and Activation Decision Register
**Prepared:** 2026-11-27  
**Purpose:** Convert the 18-source assessment into an actionable, evidence-linked human review batch.

> This is a proposal, not a completed human review. No source is activated, no status is changed, and no source classification is written into the runtime registry by this document.

## 1. Proposed first review batch

The following exact official endpoints are the strongest candidates for an initial human review. If the reviewer confirms the page's issuing authority, scope, content, and currentness, the proposed classification is **A — Approved authoritative** for the limited subject stated.

| Source | Exact URL to review | Proposed class | Scope and review notes |
|---|---|---:|---|
| PNGCIR registration information | https://pngcir.gov.pg/nid-registration-information/ | A | Birth registration and NID registration information. Page explicitly says biometric/fingerprint capture must occur in person; verify all listed requirements and current forms before approval. |
| RPNGC ePolice clearance | https://rpngc.gov.pg/advice-services/epolice-clearance/ | A | Official online clearance workflow. Confirm payment channel, fingerprint capture, lodgement steps and availability before approval. |
| RPNGC police clearance | https://rpngc.gov.pg/advice-services/police-clearance/ | A | Official clearance types and requirements. Fees, lodgement schedules and processing times are volatile and must be rechecked before being stated as current. |
| IPA prescribed forms | https://www.ipa.gov.pg/public/prescribedforms.aspx | A | Official Registry Services form catalogue. Approve for identifying forms and published fees only; every form/fee change is high impact. |
| Education 2026 Government Free Education Policy | https://education.gov.pg/admin/images/products/03_02_26%20_N_MPS_on%20GFEP_202695.pdf | A | Ministerial Policy Statement 01/2026, signed 27 January 2026. Scope must be limited to the 2026 policy; do not infer later-year policy from it. |
| PNG Customs importer/exporter registration | https://www.customs.gov.pg/trade/tin_reg | A | Current page found at this path, not the configured `/ict/tin_reg` path. Review the exact page and confirm its Form G26 and IRC TIN requirements. Replace the old configured URL only through a separate, explicit registry change. |

These pages were discoverable on 2026-11-27 from the official agency sites. Discovery and search indexing do not replace the reviewer's inspection of the exact live page.

## 2. Hold from activation pending reconciliation or verification

| Existing configured source(s) | Proposed disposition | Reason / required action |
|---|---|---|
| Four ICA passport/visa entries | Do not activate; replace with current ICSA endpoints after URL-by-URL review | Current passport guidance and visa fee information are now published by ICSA. Suggested current pages include https://icsa.gov.pg/passports/apply-for-or-renew-a-passport and https://icsa.gov.pg/visas/visa-fees. The old ICA paths must not be assumed equivalent. Add appropriate ICSA FAQ/forms/visa pages only after confirming their exact purpose and canonical URL. |
| RTA driver licensing | Hold; A candidate only after legal/currentness review | Official RTA page states it has overall responsibility for driver licensing and fees from 1 June 2018, while service delivery is handled by MVIL and some provincial governments. It also contains pre-2018 references. Review exact rules and scope; answer must distinguish regulator requirements from local service delivery. URL: https://www.rta.gov.pg/licences-approvals/driver-licensing/ |
| IRC TIN registration | Hold | Configured endpoint still needs direct endpoint and content validation. Confirm current registration procedure with IRC. |
| IRC tax forms | Hold | Confirm page availability and the current version/date of each form before activation. |
| IRC TIN4I PDF (2021 path) | Hold | Current validity of this dated form is unconfirmed. Do not present it as the current form without IRC confirmation. |
| Education tuition-fee subsidy page | Keep pending/broken as operationally appropriate; do not activate | Configured page was previously observed returning not found. Locate a current official replacement before use. |
| Customs old `/ict/tin_reg` URL | Do not activate as a separate source | Current page is at `/trade/tin_reg`. Confirm redirect/canonical behaviour and make a controlled registry URL replacement; do not keep both as independent authorities without reason. |

## 3. Supporting and supplementary sources

| Source | Proposed class | Permitted use if later approved |
|---|---:|---|
| PNGCIR institutional home/about/contact page | B | Agency identity and contact context, not detailed registration requirements. |
| IPA December 2022 transitional registry PDF | B | Historical transition context only; not current procedure without corroboration. |
| DICT digital-government progress article | C | Supplementary programme context only; never service eligibility, legal requirements, fees or application instructions. |

## 4. Mandatory review checklist for each proposed activation

A reviewer must record all of the following before an A/B/C classification and activation are applied:

1. Exact URL and final/canonical URL were opened successfully.
2. Issuing agency and its authority over the subject are clear.
3. Page is about the stated service and jurisdiction.
4. Content is sufficiently current for the claims it will support; publication/effective date is recorded where available.
5. Any referenced law, regulation, form, policy or fee schedule is identified, and stale or conflicting material is flagged.
6. The source's maximum permitted evidence role (A primary, B supporting, C supplementary) is justified.
7. Reviewer identity/role and timezone-aware review timestamp are recorded.
8. The source is activated only after the review record is complete.

A domain match, successful fetch, search result, or this proposal is not a review record.

## 5. Global change-risk rules

Even for an active A source, changes to fees, eligibility, legal rules, application requirements, forms, deadlines, dates, numeric thresholds, service availability, payment channels or contact/lodgement channels must be held for human review. Routine low-risk editorial changes may be eligible for automatic acceptance only after persistent version history, reliable diff classification and rollback are implemented. Uncertain changes must escalate.

## 6. Evidence checked during preparation

- PNGCIR registration information: https://pngcir.gov.pg/nid-registration-information/
- RPNGC ePolice clearance: https://rpngc.gov.pg/advice-services/epolice-clearance/
- RPNGC police clearance: https://rpngc.gov.pg/advice-services/police-clearance/
- IPA prescribed forms: https://www.ipa.gov.pg/public/prescribedforms.aspx
- Education 2026 policy: https://education.gov.pg/admin/images/products/03_02_26%20_N_MPS_on%20GFEP_202695.pdf
- Customs importer/exporter registration: https://www.customs.gov.pg/trade/tin_reg
- RTA driver licensing: https://www.rta.gov.pg/licences-approvals/driver-licensing/
- Current ICSA passport guidance: https://icsa.gov.pg/passports/apply-for-or-renew-a-passport
- Current ICSA visa fees: https://icsa.gov.pg/visas/visa-fees

## 7. Next implementation gate

After the reviewer confirms or edits the proposed first batch, implement the reviewed metadata in the source registry and retrieval adapter as one tested change. The implementation must carry source class, status, review timestamp and relevant provenance into `SourceRecord`; activation must remain impossible without a timezone-aware review timestamp. Keep all other sources pending until separately reviewed.
