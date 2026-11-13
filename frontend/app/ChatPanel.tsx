"use client";

import { FormEvent, useEffect, useState } from "react";
import { checkApiHealth, getApiBaseUrl } from "../lib/api";

type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
};

type ConnectionState = "checking" | "connected" | "unavailable" | "not-configured";

const suggestions = [
  "How do I apply for a National ID?",
  "Where can I find information about business registration?",
  "What public services are available in my province?"
];

export default function ChatPanel() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
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

  function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = question.trim();
    if (!value) return;

    setMessages((current) => [
      ...current,
      { id: Date.now(), role: "user", content: value },
      {
        id: Date.now() + 1,
        role: "assistant",
        content:
          "The chat interface is connected to the application shell, but evidence retrieval and a verified answer provider are not available yet. I cannot responsibly answer this question until those components are connected."
      }
    ]);
    setQuestion("");
  }

  const connectionLabel: Record<ConnectionState, string> = {
    checking: "Checking API",
    connected: "API connected",
    unavailable: "API unavailable",
    "not-configured": "API not configured"
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
          <p>For example, you can ask about an application, a government office, or a public service.</p>
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
              <span className="message-role">{message.role === "user" ? "You" : "Assistant"}</span>
              <p>{message.content}</p>
            </article>
          ))}
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
          maxLength={2000}
        />
        <div className="composer-bottom">
          <span>Do not include passwords or sensitive personal information.</span>
          <button className="send-button" type="submit" disabled={!question.trim()}>
            Send <span aria-hidden="true">→</span>
          </button>
        </div>
      </form>
      <p className="prototype-notice">
        Prototype only: verified public-source retrieval and answer generation are not yet connected.
      </p>
    </section>
  );
}
