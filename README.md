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

The initial implementation uses a Next.js/TypeScript frontend and a Python/FastAPI backend. Retrieval fetches a small curated set of public PNG sources. An optional OpenAI-compatible model adapter composes conversational answers using bounded conversation history. Model credentials are server-side only.

The approved initial provider is Groq's free tier, using the OpenAI-compatible endpoint and the `openai/gpt-oss-20b` model. No paid plan or payment method is approved.

## Delivery phases

1. Public-information chat, source retrieval, citations, model integration, and foundational security.
2. Document upload, extraction, generation from approved samples, preview, and DOCX/PDF export.
3. OCR and form understanding.
4. Assisted form completion, validation, preview, and export/printing.
5. Quality, security, performance, accessibility, and controlled release.

See the engineering specifications in `docs/` for requirements, architecture, API contracts, security, source policy, and model-provider policy.

## Status

The source-retrieval and hybrid-model implementation is in draft PR #5. CI has passed for the latest feature-branch commit, including frontend typecheck, lint, production build, and backend tests. The Groq API key has been added as a private Render backend environment variable using Save Only; it will take effect after an approved deployment. PR #5 has not been merged, and production deployment has not been authorized.

Document generation remains deferred until the owner uploads approved sample documents.

## License

To be selected and confirmed before public code reuse or distribution.
