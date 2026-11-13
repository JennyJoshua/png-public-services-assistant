# Product Requirements Document

## 1. Product summary
PNG Public Services Assistant is a mobile-first conversational web application that helps people in Papua New Guinea understand public services and prepare documents. It starts with a focused, evidence-grounded information assistant; document and form workflows follow in later phases.

## 2. Problem and opportunity
Information about public services can be distributed across agency websites, notices, PDFs, and forms. People may struggle to locate current requirements, interpret official language, or prepare correctly formatted documents. The product provides a simpler conversational entry point while preserving links to original sources and clearly communicating uncertainty.

## 3. Users
- Members of the public seeking services or procedures.
- Individuals and businesses preparing applications or correspondence.
- Students and community organisations seeking reliable public information.
- Public servants and administrative staff using document-preparation assistance.

The product must not assume every user has a modern device, fast connection, or technical expertise.

## 4. Product goals
1. Answer common PNG public-service questions with traceable evidence.
2. Explain procedures, eligibility, required documents, and responsible institutions when supported by sources.
3. Make uncertainty, conflicting sources, and stale information visible.
4. Later, help users understand forms and prepare editable/exportable documents.
5. Keep the experience usable on Android phones and low-bandwidth connections.
6. Avoid mandatory paid AI APIs and keep core providers replaceable.

## 5. Non-goals and boundaries
- Not a government agency, legal representative, or authoritative decision-maker.
- Does not guarantee eligibility, approvals, fees, processing times, or outcomes.
- Does not submit forms, make declarations, sign, certify, or transact on a user's behalf.
- Does not invent missing information or silently alter source documents.
- Phase 1 does not attempt comprehensive coverage of every PNG service.
- No paid infrastructure or model dependency without explicit approval.

## 6. Core user journeys

### 6.1 Ask a public-service question (Phase 1)
1. User opens the app without being forced to register.
2. User asks a question in ordinary language.
3. System retrieves relevant public sources and evaluates their authority and freshness.
4. Assistant answers with citations, dates, and caveats.
5. User can open the source and ask a follow-up.

### 6.2 Generate a document (Phase 2)
1. User describes the document or uploads a sample they are entitled to use.
2. System extracts structure and identifies details that need replacement.
3. Assistant asks only for missing information.
4. User reviews a preview and corrects it.
5. User approves export to supported formats.

### 6.3 Understand and complete a form (Phases 3–4)
1. User uploads a supported form.
2. System extracts text, fields, tables, and checkboxes; uncertain OCR is flagged.
3. Assistant explains fields and collects information.
4. System maps only user-provided or explicitly confirmed values.
5. User reviews the populated form and approves export/printing.

## 7. Functional requirements
- FR-01: Responsive, mobile-first chat interface.
- FR-02: Public questions can be asked without mandatory account creation.
- FR-03: Answers distinguish supported facts, general guidance, and unknowns.
- FR-04: Answers show source title, institution/publisher, URL, and relevant dates where available.
- FR-05: Retrieval ranks official sources above institutional and general sources, while surfacing conflicts.
- FR-06: Source records retain retrieval and last-checked timestamps.
- FR-07: The system declines to invent fees, eligibility rules, requirements, contacts, or deadlines.
- FR-08: Later phases support controlled uploads, extraction, document generation, OCR, form mapping, preview, and export.
- FR-09: Users can correct generated content before export.
- FR-10: Private uploads and conversations are isolated from public knowledge sources.
- FR-11: The application exposes clear errors and retry guidance without leaking secrets.
- FR-12: Admin-only source-management capabilities are access-controlled and auditable.

## 8. Quality requirements
- Usable on common Android browsers and narrow screens.
- Progressive enhancement and restrained page weight for low-bandwidth environments.
- Accessible labels, keyboard operation, readable contrast, and clear focus states.
- Secure transport and private-by-default user files.
- Automated tests for retrieval, permissions, file validation, and critical workflows.
- Observable failures, source freshness, latency, and resource consumption.
- Graceful handling when AI providers or source websites are unavailable.

## 9. Trust and safety
Every answer must avoid presenting generated text as an official government determination. High-impact claims should be supported by authoritative sources. When sources are missing, stale, contradictory, or ambiguous, the assistant must say so and direct users to the responsible institution where possible. Users retain responsibility for final review and submission.

## 10. Success measures
Phase 1: answer usefulness, citation coverage, source authority/freshness, successful follow-up rate, latency, failure rate, and mobile usability. Later phases add extraction accuracy, field-mapping accuracy, correction rate, and successful user-approved exports. Do not optimize for answer volume at the expense of correctness.

## 11. Release approach
Deliver in small phases with acceptance tests. Begin with a limited, curated set of PNG public-service topics and expand based on source quality and user feedback. Public release requires security, privacy, performance, and content-quality review.
