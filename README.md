# PNG Public Services Assistant

A mobile-first assistant designed to help people in Papua New Guinea find trustworthy public-service information, understand forms, and prepare documents.

## Product direction

The application provides a conversational interface for:
- Evidence-grounded answers about PNG public services, procedures, eligibility, required documents, and responsible institutions.
- General-knowledge answers for ordinary questions, clearly separated from official PNG guidance.
- Source links and dates so users can check information themselves.
- Later: document generation from user-approved samples, preview, and DOCX/PDF export.

## Principles

- Mobile-first, including practical use on Android devices.
- No forced registration just to ask a public information question.
- Free/open-source-first; no mandatory paid AI API dependency.
- Replaceable AI, retrieval, OCR, and storage providers.
- Clear distinction between verified facts, general guidance, and unknown information.
- Privacy and security by design; private uploads are not public knowledge sources.
- Users review and approve generated documents. The assistant does not submit forms, sign, certify, or make declarations on a user's behalf.

## Planned architecture

The initial direction is a modular monolith with a Next.js/TypeScript frontend and a Python/FastAPI backend. Retrieval fetches a curated set of public PNG sources. An optional OpenAI-compatible model adapter composes conversational answers using bounded conversation history. Model credentials are server-side only.

Specific provider and model choices remain subject to compatibility, licensing, resource, and free-tier evaluation. No paid service is approved by this README.

## Delivery phases

1. Public-information chat, source management, retrieval, citations, model integration, and foundational security.
2. Document upload, extraction, generation from approved samples, preview, and DOCX/PDF export.
3. OCR and form understanding.
4. Assisted form completion, validation, preview, and export/printing.
5. Quality, security, performance, accessibility, and controlled release.

See the engineering specifications in `docs/` for requirements, architecture, API contracts, security, and the Phase 1 plan.

## Status

The first source-retrieval slice is in draft PR #4. The hybrid model adapter and bounded conversation history are being developed in a follow-on feature branch. The model adapter is not active until a provider is selected and private credentials are configured. No merge or production deployment is implied by these development branches.

## License

To be selected and confirmed before public code reuse or distribution.
