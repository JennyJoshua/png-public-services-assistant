"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  checkApiHealth,
  getApiBaseUrl,
  sendChatMessage,
  type Citation,
  type ChatHistoryMessage,
} from "../lib/api";

type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  warnings?: string[];
  answerMode?: "model" | "extractive";
};

type ConnectionState = "checking" | "connected" | "unavailable" | "not-configured";

const suggestions = [
  "How do I apply for a National ID?",
  "Where can I find information about business registration?",
  "What public services are available in my province?",
];

export default function ChatPanel() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [connectionState, setConnectionState] = useState<ConnectionState>(
    getApiBaseUrl() ? "checking" : "not-configured"
  );

  useEffect(() => {
    if (!getApiBaseUrl()) return;

    const controller = new AbortController();
    checkApiHealth(controller.signal)
      .then(() => setConnectionState("connected"))
      .catch(() => {
        if (!controller.signal.aborted) setConnectionState("unavailable");
      });

    return () => controller.abort();
  }, []);

  async function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = question.trim();
    if (!value || isSending) return;

    const history: ChatHistoryMessage[] = messages.map(({ role, content }) => ({
      role,
      content,
    }));
    setMessages((current) => [
      ...current,
      { id: Date.now(), role: "user", content: value },
    ]);
    setQuestion("");
    setIsSending(true);

    try {
      const result = await sendChatMessage(value, history);
      setMessages((current) => [
        ...current,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: result.answer,
          citations: result.citations,
          warnings: result.warnings,
          answerMode: result.answer_mode,
        },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: error instanceof Error
            ? error.message
            : "The service is temporarily unavailable. Please try again.",
        },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  const connectionLabel: Record<ConnectionState, string> = {
    checking: "Checking API",
    connected: "API connected",
    unavailable: "API unavailable",
    "not-configured": "API not configured",
  };

  return (
    <section className="chat-card" aria-label="Public services question assistant">
      <div className="chat-heading">
        <div>
          <h2>Ask a question</h2>
          <p>Use plain language. You do not need an account.</p>
        </div>
        <span className={`status-dot status-${connectionState}`}>
          <span /> {connectionLabel[connectionState]}
        </span>
      </div>

      {messages.length === 0 ? (
        <div className="welcome-panel">
          <div className="welcome-icon" aria-hidden="true">?</div>
          <h3>What would you like to know?</h3>
          <p>Ask about a PNG public service, an application, a government office, or a general topic.</p>
          <div className="suggestions">
            {suggestions.map((item) => (
              <button
                className="suggestion"
                key={item}
                type="button"
                onClick={() => setQuestion(item)}
              >
                {item}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="conversation" aria-live="polite">
          {messages.map((message) => (
            <article className={`message message-${message.role}`} key={message.id}>
              <span className="message-role">
                {message.role === "user" ? "You" : "Assistant"}
                {message.answerMode && (
                  <span className="answer-mode">
                    {message.answerMode === "model" ? " · AI response" : " · Source excerpts"}
                  </span>
                )}
              </span>
              <p className="message-content">{message.content}</p>
              {message.citations && message.citations.length > 0 && (
                <div className="message-citations">
                  <strong>Sources</strong>
                  <ol>
                    {message.citations.map((citation, index) => (
                      <li key={citation.url}>
                        <a href={citation.url} target="_blank" rel="noreferrer">
                          {citation.institution}: {citation.title}
                        </a>
                        <small>
                          {citation.publication_date
                            ? `Published: ${citation.publication_date} · `
                            : ""}
                          Checked: {new Date(citation.last_checked_at).toLocaleDateString()}
                          {" · "}Reference [{index + 1}]
                        </small>
                      </li>
                    ))}
                  </ol>
                </div>
              )}
              {message.warnings?.map((warning) => (
                <p className="message-warning" key={warning}>{warning}</p>
              ))}
            </article>
          ))}
          {isSending && (
            <article className="message message-assistant" aria-live="polite">
              <span className="message-role">Assistant</span>
              <p>Checking relevant sources and preparing your answer…</p>
            </article>
          )}
        </div>
      )}

      <form className="composer" onSubmit={submitQuestion}>
        <label className="sr-only" htmlFor="question">Your question</label>
        <textarea
          id="question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Type your question here..."
          rows={2}
          maxLength={1000}
          disabled={isSending}
        />
        <div className="composer-bottom">
          <span>Do not include passwords or sensitive personal information.</span>
          <button className="send-button" type="submit" disabled={!question.trim() || isSending}>
            {isSending ? "Thinking…" : "Send"} <span aria-hidden="true">→</span>
          </button>
        </div>
      </form>
      <p className="prototype-notice">
        PNG public-service answers should be checked against the cited agency sources.
        General background is not an official government determination.
      </p>
    </section>
  );
}
