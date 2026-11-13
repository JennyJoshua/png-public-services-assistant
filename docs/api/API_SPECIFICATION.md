# API Specification — Initial Contract

The API is versioned under `/api/v1`. This is a proposed contract for implementation; request and response schemas must be formalized in code and tested.

## 1. Conventions
- All application endpoints, including later-phase endpoints, use the `/api/v1` prefix.
- JSON for ordinary requests/responses.
- UTF-8 text.
- UTC ISO-8601 timestamps.
- Stable machine-readable error codes.
- Request ID returned in responses.
- Explicit pagination and bounded request sizes.
- No secrets or privileged provider credentials in client requests.

## 2. Phase 1 endpoints

### GET /api/v1/health
Returns service health and version metadata. Do not expose secrets, environment variables, or internal infrastructure details.

### POST /api/v1/chat/sessions
Creates a short-lived anonymous or authenticated chat session. Return an opaque session identifier and expiry. Do not require account creation for basic public questions.

### POST /api/v1/chat/sessions/{session_id}/messages
Request:
```json
{
  "message": "What documents are needed for ...?",
  "language": "en"
}
```
Response:
```json
{
  "request_id": "opaque-id",
  "answer": "Evidence-grounded response...",
  "citations": [
    {
      "title": "Source title",
      "institution": "Publishing institution",
      "url": "https://example.gov.pg/source",
      "publication_date": null,
      "last_checked_at": "2026-01-01T00:00:00Z"
    }
  ],
  "warnings": [],
  "created_at": "2026-01-01T00:00:00Z"
}
```
The example URL and dates are placeholders, not real source data. Actual citations must be generated from retrieved source records.

### GET /api/v1/chat/sessions/{session_id}/messages
Returns only messages the caller is authorized to access, with pagination and retention rules applied.

## 3. Later-phase endpoint families
- `POST /api/v1/documents/uploads`: request a bounded, private upload; validate file type and size.
- `POST /api/v1/documents/extract`: create an extraction job and return job ID/status.
- `GET /api/v1/jobs/{job_id}`: retrieve authorized processing status.
- `POST /api/v1/documents/generate`: create a document draft from user instructions and approved inputs.
- `GET /api/v1/documents/{document_id}/preview`: provide a safe preview.
- `POST /api/v1/documents/{document_id}/approve-export`: export only after explicit user approval.
- `POST /api/v1/forms/analyze`: identify form structure and fields.
- `POST /api/v1/forms/{form_id}/populate`: populate only confirmed user-provided values.
- `GET /api/v1/documents/{document_id}/download`: authorize a short-lived download.

These routes are roadmap items and must not be represented as implemented until delivered and tested.

## 4. Error model
Use a consistent structure:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request could not be processed.",
    "request_id": "opaque-id"
  }
}
```
Do not return stack traces, provider secrets, raw database errors, or private filesystem paths.

## 5. Security requirements
- Validate session ownership and access on every request.
- Apply rate limits and request/body size limits.
- Validate uploaded file content, not just filename extensions.
- Use CSRF protections where cookie-based authentication is used.
- Restrict CORS to configured origins.
- Avoid logging full private documents or sensitive user messages by default.
- Return safe, generic errors for unauthorized resources.
- Require explicit confirmation for document export and any future consequential action.

## 6. API acceptance
OpenAPI documentation must match implemented schemas. Add tests for valid requests, malformed input, expired sessions, unauthorized access, provider failures, citation integrity, and rate limits.
