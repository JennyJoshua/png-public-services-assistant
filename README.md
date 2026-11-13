# PNG Public Services Assistant

A mobile-first assistant designed to help people in Papua New Guinea find trustworthy public-service information, understand forms, and prepare documents.

## Product direction

The application will provide:
- Evidence-grounded answers about PNG public services, procedures, eligibility, required documents, and responsible institutions.
- Source links and dates so users can check information themselves.
- Conversational help understanding forms and preparing documents.
- Document preview and user approval before export.
- OCR and form-filling capabilities introduced in later phases.

## Principles

- Mobile-first, including practical use on Android devices.
- No forced registration just to ask a public information question.
- Free/open-source-first; no mandatory paid AI API dependency.
- Replaceable AI, retrieval, OCR, and storage providers.
- Clear distinction between verified facts, general guidance, and unknown information.
- Privacy and security by design; private uploads are not public knowledge sources.
- Users review and approve generated documents. The assistant does not submit forms, sign, certify, or make declarations on a user's behalf.

## Planned architecture

The initial direction is a modular monolith with a Next.js/TypeScript frontend, a Python/FastAPI backend, and PostgreSQL. Retrieval will combine carefully sourced public information with indexed documents. Model, embedding, OCR, and storage integrations will sit behind replaceable adapters.

Specific technologies and hosting choices remain subject to compatibility, licensing, resource, and free-tier evaluation. No paid service is approved by this README.

## Delivery phases

1. Public-information chat, source management, retrieval, citations, and foundational security.
2. Document upload, extraction, generation, preview, and DOCX/PDF export.
3. OCR and form understanding.
4. Assisted form completion, validation, preview, and export/printing.
5. Quality, security, performance, accessibility, and controlled release.

See the engineering specifications in `docs/` for requirements, architecture, API contracts, security, and the Phase 1 plan.

## Status

Planning and specification stage. No production deployment or paid service is authorized.

## License

To be selected and confirmed before public code reuse or distribution.
