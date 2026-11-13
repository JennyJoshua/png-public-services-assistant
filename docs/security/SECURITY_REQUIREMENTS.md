# Security and Privacy Requirements

## 1. Principles
- Privacy by default and data minimization.
- Least privilege for users, administrators, services, and integrations.
- Public knowledge and private user content remain separate.
- Secure defaults, auditable changes, and explicit user approval for consequential outputs.
- No private upload is used for model training or shared retrieval without informed, explicit consent and a separately reviewed lawful basis.

## 2. Identity and sessions
- Public information chat should not require registration.
- Use unguessable, short-lived anonymous session credentials; store hashes where practical.
- Authenticated access, if introduced, must derive identity and permissions from trusted server-side authentication, never client-editable metadata.
- Check ownership on every read, write, preview, and download.
- Protect cookies, sessions, and tokens; expire and revoke them appropriately.

## 3. Authorization and database
- Deny by default.
- Enforce row-level security where supported and test policies using multiple user identities.
- Keep privileged service credentials server-side.
- Separate administrative source management from public access.
- Do not rely on frontend route hiding as authorization.

## 4. Upload and document safety
- Allowlist supported file formats and enforce strict size/page limits.
- Inspect actual file signatures and parse defensively; do not trust extensions or MIME headers alone.
- Reject malformed, encrypted, oversized, or unsupported files with clear guidance.
- Malware scanning is desirable where feasible; do not claim scanning if it is not implemented.
- Store files privately, use random object keys, and issue short-lived authorized download links.
- Isolate parsing/OCR workloads and enforce CPU, memory, and time limits.
- Prevent path traversal, archive bombs, unsafe macros, and server-side request forgery through document links.
- Apply retention and deletion policies to originals, previews, extracted text, temporary files, and derived indexes.

## 5. Application security
- HTTPS in production.
- Validate and normalize all input.
- Rate-limit chat, upload, extraction, and expensive operations.
- Restrict CORS and protect cookie-based flows against CSRF.
- Use secure headers and dependency scanning.
- Keep secrets out of source control, logs, client bundles, and error messages.
- Protect against prompt injection in retrieved pages and uploaded documents: treat content as untrusted evidence, never as system instructions.
- Do not allow retrieved content to trigger tools or external actions without a separately authorized workflow.

## 6. Privacy and retention
- Publish a clear privacy notice before collecting personal or document data.
- Collect only what is necessary for the requested task.
- Define retention periods before launch; provide a practical deletion route.
- Avoid storing full conversation or document content in operational logs.
- Explain any third-party processing and data-location implications.
- Do not use private content for training by default.
- Ensure backups and derived artifacts are covered by retention/deletion policy.

## 7. AI-specific safeguards
- Display source references and dates.
- Label uncertainty and conflicting evidence.
- Never invent missing form values.
- Distinguish extracted OCR text from verified user-confirmed data.
- Require user review before export.
- Never submit forms, sign, certify, or make declarations for users.
- Do not present generated content as official advice or an agency decision.

## 8. Operations and incident response
- Maintain dependency and deployment records.
- Monitor authentication failures, unusual traffic, provider errors, and resource exhaustion.
- Keep minimal audit events for administrative changes and sensitive document actions.
- Define incident triage, containment, notification, recovery, and credential rotation procedures before public release.
- Test backup restoration and deployment rollback.

## 9. Release gates
Before public release, review threat model, access policies, upload pipeline, retention/deletion, privacy notice, dependency vulnerabilities, rate limits, and incident procedure. Any unresolved critical/high-risk issue blocks release.
