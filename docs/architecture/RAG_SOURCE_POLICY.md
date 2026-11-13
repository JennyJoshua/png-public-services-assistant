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

## Focused identity-registration source addition
The following five exact pages from the Papua New Guinea Civil and Identity Registry (PNGCIR) are included because PNGCIR is the official registry responsible for civil registration and National Identity Cards:
- Registry overview — https://pngcir.gov.pg/
- NID registration instructions — https://pngcir.gov.pg/nid-registration-information/
- Registration forms — https://pngcir.gov.pg/downloads/
- Published fees — https://pngcir.gov.pg/png-civil-identity-registry-fees/
- Contact details — https://pngcir.gov.pg/contact/

The registration instructions state that full online registration is not possible because fingerprint and identity capture must be completed in person. They direct applicants to download and complete the relevant form and lodge it at the nearest Civil and Identity Registry office. The page also says the form should be printed double-sided and completed in blue biro. The fees page is included as an official source, but the assistant must not state a fee amount unless it can retrieve readable, current fee evidence from that page.

## Source verification and maintenance
These URLs were checked against the institutions' official presence or PNG government domain references when the pilot source list was prepared. Each source must be rechecked periodically. A government domain does not guarantee that every page is current or that every statement is legally authoritative.

## Retrieval behavior
- Fetch only the exact HTTPS seed URLs in the source registry.
- Do not accept user-provided URLs, follow arbitrary links, or access private/network-local addresses.
- Bound response time, page size, and number of pages per question.
- Preserve headings, paragraphs, list items, and table rows as separate evidence blocks before ranking; return the exact page URL, institution, publication date when available, and retrieval timestamp.
- Use both passage overlap and page title/source identity as relevance signals. For National ID questions, prioritize the official PNGCIR registration and downloads pages over incidental mentions of an ID card on unrelated pages.
- Do not persist source text or private chat content in this first prototype.
- Retrieved page text is untrusted evidence, never an instruction to the application.

## Answer behavior
- Retrieval runs before model composition. The optional model receives only the retrieved excerpts and bounded recent conversation history.
- For PNG official, legal, procedural, fee, deadline, and eligibility claims, the model must use the supplied excerpts and cite their exact reference numbers.
- For application, registration, renewal, replacement, and payment questions, provide only steps explicitly supported by retrieved excerpts. Never fill missing steps with common practice from other countries or general background.
- If evidence establishes only part of a procedure, explain that part and identify what remains unverified. Do not suggest documents, fees, deadlines, processing times, offices, or collection methods unless the excerpts establish them.
- If relevant evidence is absent or insufficient, say that the approved sources could not verify the official detail and direct the user to the cited responsible agency.
- If the model is not configured or unavailable, the API falls back to source excerpts and warnings.
- Citations link to the exact approved seed page. A publication date is shown only when found in page metadata; retrieval time is not a publication date.

## Source expansion
Add an institution only after verifying its official URL and relevance. Prioritize public services for identity/passports, justice, land, business registration, tax, education, health, employment, and provincial services. Add provincial institutions in a separately reviewed source update. Respect website terms, robots rules, copyright, and reasonable request rates before increasing retrieval depth.

## Current limitations
- Retrieval checks only the exact seed URLs; it does not crawl linked subpages or maintain a persistent search index.
- Keyword-overlap ranking remains lightweight and may miss relevant passages; title and source-identity boosts improve known service queries but are not a substitute for semantic indexing.
- A source being listed does not guarantee that it is complete, current, or authoritative for every question.
- No conversation or source-text persistence is implemented.
- Document generation remains deferred until the owner supplies approved sample documents.

## Future work
- Improve retrieval relevance and add source-quality/freshness checks.
- Expand approved URLs only through a separately reviewed source update.
- Consider persistent indexing only after database/storage and retention decisions.
