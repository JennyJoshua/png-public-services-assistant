# AI and Document Model Selection

## 1. Selection policy
No model is selected as a production dependency by this document. The project is free/open-source-first and must not require a paid AI API. Evaluate current model availability, licence, actual hosting requirements, language support, quality, and operational limits before adoption.

## 2. Required provider interfaces
- Text generation/chat.
- Embeddings.
- Optional reranking.
- OCR.
- Document parsing/layout extraction.

Provider adapters must allow replacement without changing user-facing workflows. Record model name, exact version/revision, licence, configuration, and evaluation date.

## 3. Candidate families to evaluate
- Qwen model family.
- Gemma model family.
- BGE-M3 embeddings and a compatible BGE reranker.
- PaddleOCR and Tesseract OCR.
- Docling for document parsing and layout extraction.

These are candidates only. Confirm the current model card, licence terms, redistribution/commercial-use restrictions, language coverage, hardware needs, and deployment compatibility at evaluation time.

## 4. Evaluation criteria
1. Accuracy on representative PNG public-service questions.
2. Ability to follow evidence-only instructions and abstain when evidence is missing.
3. Quality of citations and resistance to fabricated sources.
4. English and relevant PNG language performance, measured rather than assumed.
5. Context length and document/table handling.
6. Latency, memory, CPU/GPU needs, and concurrency.
7. Licence and acceptable-use restrictions.
8. Deployability within approved free resources.
9. Model and dependency maintenance status.
10. Data handling and privacy implications.

## 5. Evaluation dataset
Create a small, reviewed benchmark from public and permitted documents. Include:
- Questions with clear official answers.
- Questions with incomplete or conflicting evidence.
- Outdated notices and changed procedures.
- Questions for which no reliable answer is available.
- Tables, scanned pages, and common administrative terminology.
- English and selected local-language examples only where competent reviewers can assess them.

Do not include private user uploads or personal information in shared evaluation datasets without informed consent and a lawful basis.

## 6. Grounding rules
The model must answer from retrieved evidence for service-specific factual claims. Each citation must map to a retrieved source. It must not fabricate fees, forms, deadlines, phone numbers, eligibility, or procedures. If evidence is insufficient, state what is unknown and suggest contacting the responsible institution.

## 7. Hosting reality
Free web application hosting may not provide sufficient RAM, GPU, execution time, or persistent storage for local inference and OCR. Benchmark on the actual target environment. Consider separating inference from the web/API deployment only after cost, privacy, and reliability are understood. Any paid inference or hosting requires explicit user approval.

## 8. Decision record template
For every selected model, record: use case, exact model/revision, licence URL and review date, benchmark results, hardware/runtime, latency, known limitations, data policy, hosting plan, fallback provider, and approval status.
