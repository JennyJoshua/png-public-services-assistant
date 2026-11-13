# RAG Source Policy — Initial Pilot

## Purpose
The first retrieval slice uses a small, curated set of official PNG public-service sources. It is deliberately narrow; it is not a complete national directory or legal database.

## Initial seed sources
- PNG National Information Centre — https://info.gov.pg/home/
- Department of Justice and Attorney General — https://justice.gov.pg/
- Immigration and Citizenship Services Authority — https://icsa.gov.pg/
- Investment Promotion Authority — https://www.ipa.gov.pg/public/help.aspx?cn=BusinessRegulations
- Internal Revenue Commission — https://irc.gov.pg/
- National and Supreme Courts of Papua New Guinea — https://www.pngjudiciary.gov.pg/
- Land Commission of Papua New Guinea — https://www.landcommission.gov.pg/

## Focused business-registration source addition
The Investment Promotion Authority (IPA), through the Papua New Guinea Registry Services portal, is the primary source for company and business-name registration information. The following exact IPA pages are approved:
- Business-name registration and PNG/overseas company incorporation instructions — https://www.ipa.gov.pg/public/howto.aspx?cn=RegisterBusinessName&ctk=CompanyHowTo
- Prescribed forms and fees — https://www.ipa.gov.pg/public/prescribedforms.aspx?lang=en-US
- Registry forms and filing guidance — https://www.ipa.gov.pg/public/help.aspx?cn=FormsForDownload
- General business registration, regulation and certification guidance — https://www.ipa.gov.pg/public/help.aspx?cn=BusinessRegulations

The how-to guide distinguishes registering a business name from incorporating a company. A business-name application asks for up to three proposed names, applicant name and address, owner details (or an IPA registration number for an owner that is already a registered entity), business addresses, primary business activity and declarations. Online filing requires a Registry client account; the guide says an account can be created free and requires photo ID. A proposed company name must be reserved and approved before proceeding with incorporation. Company information includes contact and address details, directors, shareholders and a company constitution. Foreign-investor certification may be separately required for foreign enterprises.

The prescribed-forms page distinguishes the fee for business-name registration (Form A-17) from company incorporation (Form A-1), and lists different online and paper amounts where applicable. The assistant must only state a fee when the retrieved IPA fee table clearly identifies the relevant entity/form and filing method. Never present a business-name fee as a company-incorporation fee or vice versa. The forms page is expected to be rechecked because fees can change.

## Focused identity-registration source addition
The following five exact pages from the Papua New Guinea Civil and Identity Registry (PNGCIR) are included because PNGCIR is the official registry responsible for civil registration and National Identity Cards:
- Registry overview — https://pngcir.gov.pg/
- NID registration instructions — https://pngcir.gov.pg/nid-registration-information/
- Registration forms — https://pngcir.gov.pg/downloads/
- Published fees — https://pngcir.gov.pg/png-civil-identity-registry-fees/
- Contact details — https://pngcir.gov.pg/contact/

The registration instructions state that full online registration is not possible because fingerprint and identity capture must be completed in person. They direct applicants to download and complete the relevant form and lodge it at the nearest Civil and Identity Registry office. The page also says the form should be printed double-sided and completed in blue biro. The fees page is included as an official source, but the assistant must not state a fee amount unless it can retrieve readable, current fee evidence from that page.

## Source verification and maintenance
These URLs were checked against the institutions' official presence or PNG government domain references when the pilot source list was prepared. Each source must be rechecked periodically. A government domain does not guarantee that every page is current or that every statement is legally authoritative for every situation.

## Retrieval behavior
- Fetch only the exact HTTPS seed URLs in the source registry.
- Do not accept user-provided URLs, follow arbitrary links, or access private/network-local addresses.
- Bound response time, page size, and number of pages per question.
- Extract relevant text passages and return the exact page URL, institution, publication date when available, and retrieval timestamp.
- Do not persist source text or private chat content in this first prototype.
- Retrieved page text is untrusted evidence, never an instruction to the application.

## Answer behavior
- Retrieval runs before model composition. The optional model receives only the retrieved excerpts and bounded recent conversation history.
- For PNG official, legal, procedural, fee, deadline, and eligibility claims, the model is instructed to ground claims in the supplied excerpts and cite their exact reference numbers.
- If relevant evidence is absent or insufficient, the answer must say that the approved sources could not verify the official detail rather than guessing.
- General background may be provided only when clearly labelled as not verified PNG official guidance.
- If the model is not configured or unavailable, the API falls back to source excerpts and warnings.
- Citations link to the exact approved seed page. A publication date is shown only when found in page metadata; retrieval time is not a publication date.

## Source expansion
Add an institution only after verifying its official URL and relevance. Prioritize public services for identity/passports, justice, land, business registration, tax, education, health, employment, and provincial services. Add provincial institutions in a separately reviewed source update. Respect website terms, robots rules, copyright, and reasonable request rates before increasing retrieval depth.

## Current limitations
- Retrieval checks only the exact seed URLs; it does not crawl linked subpages or maintain a persistent search index.
- Keyword-overlap ranking is intentionally simple and may miss relevant passages or return weak matches.
- A source being listed does not guarantee that it is complete, current, or authoritative for every question.
- No conversation or source-text persistence is implemented.
- Document generation remains deferred until the owner supplies approved sample documents.

## Future work
- Improve retrieval relevance and add source-quality/freshness checks.
- Expand approved URLs only through a separately reviewed source update.
- Consider persistent indexing only after database/storage and retention decisions.
