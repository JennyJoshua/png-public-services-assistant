# Hybrid answer and model-provider policy

## Intended behaviour

The assistant uses a hybrid approach:

- For PNG public-service, government, legal, eligibility, fee, deadline, and procedural questions, it retrieves the approved source set first. The model must ground official claims in those passages, cite the supplied reference numbers, and say when the sources do not verify a requirement.
- When useful, the model may add a separately labelled general-background explanation. That background must not be represented as an official PNG requirement.
- For ordinary non-government questions, the model may answer from general knowledge. It must not imply that the answer was checked against PNG government sources.
- If the question is ambiguous, the assistant asks a concise clarifying question.

## Initial provider: Groq

Groq is the approved initial model provider, using its OpenAI-compatible chat-completions API. Initial defaults:

- API base URL: `https://api.groq.com/openai/v1`
- Model: `openai/gpt-oss-20b`
- Required secret: `MODEL_API_KEY`

The endpoint and model can be overridden with `MODEL_API_BASE_URL` and `MODEL_NAME` when a different compatible provider is approved. The API key is always server-side. Do not put it in frontend variables, source code, GitHub, or chat messages.

Use only the provider's free tier unless the owner explicitly approves otherwise. Free-tier access and rate limits are controlled by Groq and may change. Do not upgrade to a paid tier or add a payment method.

Groq states that inference requests are not retained by default, but may be temporarily logged for reliability troubleshooting or abuse monitoring for up to 30 days unless Zero Data Retention is enabled. Data storage is in the United States. Users should not submit passwords, highly sensitive personal data, or confidential documents to the chat.

## Provider boundary

The backend contains an optional OpenAI-compatible chat-completions adapter. The frontend never receives the provider key. Without `MODEL_API_KEY`, the application stays in extractive retrieval mode and explains that model responses are not yet enabled.

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

The Groq adapter is implemented but requires the owner to create an API key and add it as the private `MODEL_API_KEY` environment variable on the backend hosting service. The application can continue serving retrieved source excerpts in the meantime.
