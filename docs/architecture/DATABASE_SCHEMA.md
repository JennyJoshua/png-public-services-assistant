# Database Schema — Initial Proposal

This document describes logical entities, not a committed migration. Refine the schema after Phase 1 implementation details and security review are known.

## 1. Design rules
- Use stable UUID primary keys.
- Store timestamps in UTC.
- Keep public knowledge, private conversations, uploads, generated files, and administration data logically separated.
- Apply least-privilege access and row-level security where supported.
- Never trust client-supplied role or ownership fields.
- Keep source provenance on every indexed chunk.

## 2. Phase 1 entities

### source_records
- id (UUID, PK)
- institution_name
- title
- canonical_url (unique where appropriate)
- source_type (official, institutional, secondary, other)
- language_code
- publication_date (nullable)
- retrieved_at
- last_checked_at (nullable)
- content_hash
- status (active, stale, unavailable, withdrawn, review_required)
- reliability_notes (nullable)
- created_at, updated_at

### source_documents
- id (UUID, PK)
- source_id (FK source_records)
- media_type
- storage_key or extracted_text reference
- document_version
- extracted_at
- processing_status
- created_at

### source_chunks
- id (UUID, PK)
- source_document_id (FK source_documents)
- chunk_index
- text_content
- page_or_section (nullable)
- token_count (nullable)
- embedding reference/vector (implementation-dependent)
- created_at

### chat_sessions
- id (UUID, PK)
- user_id (nullable for anonymous sessions)
- anonymous_session_key_hash (nullable)
- created_at, updated_at
- expires_at (nullable)

### chat_messages
- id (UUID, PK)
- session_id (FK chat_sessions)
- role (user, assistant, system)
- content
- created_at
- request_id (nullable)

### answer_citations
- id (UUID, PK)
- message_id (FK chat_messages)
- source_id (FK source_records)
- source_chunk_id (nullable FK source_chunks)
- cited_url
- quoted_or_paraphrased_span (optional; minimize retained text)
- created_at

## 3. Later-phase entities
- user_files: owner/session, private storage key, original filename, validated media type, byte size, checksum, scan status, retention deadline, processing status.
- document_jobs: request, source file/template, job status, provider/version, error classification, timestamps.
- generated_documents: owner/session, private storage key, media type, version, approval status, expiry.
- form_templates and form_fields: template provenance, version, page geometry, field type, confidence and mapping rules.
- form_field_values: field reference, user-provided value, confirmation status, source (user input/OCR/derived), confidence.
- audit_events: actor, action, resource type/id, timestamp, request ID, minimal metadata.

## 4. Privacy and access model
- Anonymous public chat should use short-lived, unguessable session identifiers and conservative retention.
- Authenticated user records must be scoped to the authenticated principal.
- Private file metadata and storage objects must enforce ownership on every operation.
- Public source content must never be placed in a user's private namespace and vice versa.
- Admin permissions must be explicit and separate from ordinary user roles.
- Server-side service credentials must never be exposed to the client.

## 5. Indexing and deletion
Index records must retain source IDs and document versions. When a source is withdrawn or replaced, mark affected chunks inactive and re-index. Deleting a private file must also remove derived temporary artifacts and associated embeddings where applicable, subject to documented retention and backup policies.

## 6. Implementation gates
Before creating migrations: choose identity/session strategy, hosting, vector storage, retention periods, backup policy, and exact RLS policies. Test both allowed and denied access paths. This proposal is not authorization to collect unnecessary personal information.
