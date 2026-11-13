# Hybrid answer and model-provider policy

## Intended behaviour

The assistant uses a hybrid approach:

- For PNG public-service, government, legal, eligibility, fee, deadline, and procedural questions, it retrieves the approved source set first. The model must ground official claims in those passages, cite the supplied reference numbers, and say when the sources do not verify a requirement.
- When useful, the model may add a separately labelled general-background explanation. That background must not be represented as an official PNG requirement.
- For ordinary non-government questions, the model may answer from general knowledge. It must not imply that the answer was checked against PNG government sources.
- If the question is ambiguous, the assistant asks a concise clarifying question.

## Provider boundary

The backend contains an optional OpenAI-compatible chat-completions adapter. The frontend never receives the provider key. The provider is configured only with server-side environment variables:

- `MODEL_API_BASE_URL`: HTTPS base URL ending at the provider API root (for example, a root that exposes `/chat/completions`).
- `MODEL_API_KEY`: private server-side secret.
- `MODEL_NAME`: model identifier supported by that provider.

No provider, model, API key, paid plan, or production change is approved by this document. Without all three settings, the application stays in extractive retrieval mode and explains that model responses are not yet enabled. Provider selection and credential setup are separate decisions.

## Conversation context

The API accepts a bounded recent history of user and assistant messages. It does not persist conversations. The client sends at most eight prior messages; the backend validates roles and truncates message content before forwarding it.

## Safety and quality

- Retrieved web content and conversation history are treated as untrusted data, not instructions.
- Official PNG claims require supporting approved-source evidence.
- The model must never invent source links, citation numbers, fees, forms, eligibility criteria, or deadlines.
- A missing or unavailable model provider must not break source retrieval.
- Model-generated answers are not legal advice or an official government determination.
- Provider keys remain server-side and must never be committed to Git.

## Current limitation

A provider-neutral adapter is implemented, but the live model is not active until a suitable provider is selected and its private credentials are configured. The application can continue serving retrieved source excerpts in the meantime.
