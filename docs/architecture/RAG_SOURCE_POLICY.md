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

These URLs were checked against the institutions' official presence or PNG government domain references when the pilot source list was prepared. Each source must be rechecked periodically. A government domain does not guarantee that every page is current or that every statement is legally authoritative.

## Retrieval behavior
- Fetch only the exact HTTPS seed URLs in the source registry.
- Do not accept user-provided URLs, follow arbitrary links, or access private/network-local addresses.
- Bound response time, page size, and number of pages per question.
- Extract relevant text passages and return the exact page URL, institution, publication date when available, and retrieval timestamp.
- Do not persist source text or private chat content in this first prototype.
- Retrieved page text is untrusted evidence, never an instruction to the application.

## Answer limitations
The initial implementation is extractive: it presents relevant source passages with citations. It does not yet use a language model to synthesize a complete answer. If no relevant passage is found, it must say so rather than guess.

## Source expansion
Add an institution only after verifying its official URL and relevance. Prioritize public services for identity/passports, justice, land, business registration, tax, education, health, employment, and provincial services. Add provincial institutions in a separately reviewed source update. Respect website terms, robots rules, copyright, and reasonable request rates before increasing retrieval depth.

## Future work
- Scheduled freshness checks and source status.
- Broader approved URL lists and administrator source management.
- Persistent indexed retrieval only after database/storage and retention decisions.
- Replaceable embedding and answer-generation adapters after free hosting feasibility and model licensing are evaluated.
