"use client";

import { useEffect, useRef, useState } from "react";
import type { Message, SelectedPoint } from "@/types";

interface ChatPanelProps {
  selectedPoint: SelectedPoint | null;
  messages: Message[];
  loading: boolean;
  error: string | null;
  onSubmit: (question: string) => void;
}

export default function ChatPanel({
  selectedPoint,
  messages,
  loading,
  error,
  onSubmit,
}: ChatPanelProps) {
  const [question, setQuestion] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Clear question input when location changes
  useEffect(() => {
    setQuestion("");
    textareaRef.current?.focus();
  }, [selectedPoint?.lat, selectedPoint?.lon]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || !selectedPoint || loading) return;
    onSubmit(trimmed);
    setQuestion("");
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Submit on Enter (without Shift)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as React.FormEvent);
    }
  }

  return (
    <div className="side-panel">
      <div className="panel-header">
        <h1>Askio</h1>
        <p>
          {selectedPoint
            ? selectedPoint.label
              ? selectedPoint.label
              : `${selectedPoint.lat.toFixed(4)}, ${selectedPoint.lon.toFixed(4)}`
            : "Click the map to select a location"}
        </p>
      </div>

      <div className="chat-thread" role="log" aria-live="polite">
        {!selectedPoint ? (
          <div className="empty-state">
            Click anywhere on the map to select a location, then ask a question.
          </div>
        ) : messages.length === 0 && !loading ? (
          <div className="empty-state">
            Ask anything about{" "}
            {selectedPoint.label || "this location"}.
          </div>
        ) : (
          <>
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`chat-message chat-message--${msg.role}`}
              >
                {msg.role === "user" ? (
                  <div className="chat-bubble chat-bubble--user">
                    {msg.content}
                  </div>
                ) : (
                  <div className="chat-bubble chat-bubble--assistant">
                    <p className="chat-reply">{msg.content}</p>

                    {msg.role === "assistant" && msg.response.sources.length > 0 && (
                      <div className="chat-sources">
                        {msg.response.sources.map((src, si) => (
                          <span key={si} className="source-tag">{src}</span>
                        ))}
                      </div>
                    )}

                    {msg.role === "assistant" && msg.response.evidence.length > 0 && (
                      <ul className="chat-evidence" aria-label="Evidence">
                        {msg.response.evidence.map((item, ei) => (
                          <li key={ei}>{item}</li>
                        ))}
                      </ul>
                    )}

                    {msg.role === "assistant" && msg.response.image_base64 && (
                      <details className="satellite-disclosure">
                        <summary>View analyzed satellite image</summary>
                        <div className="satellite-image-wrap">
                          <img
                            src={`data:image/png;base64,${msg.response.image_base64}`}
                            alt="Sentinel-2 satellite tile"
                            className="satellite-image"
                          />
                          {msg.response.image_metadata && (
                            <div className="image-meta">
                              <span>
                                {msg.response.image_metadata.collection} ·{" "}
                                {msg.response.image_metadata.datetime.slice(0, 10)}
                              </span>
                              {msg.response.image_metadata.cloud_cover != null && (
                                <span>
                                  Cloud cover: {msg.response.image_metadata.cloud_cover.toFixed(0)}%
                                </span>
                              )}
                              <span>Source: {msg.response.image_metadata.source}</span>
                            </div>
                          )}
                        </div>
                      </details>
                    )}
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="chat-message chat-message--assistant">
                <div className="chat-bubble chat-bubble--assistant chat-bubble--loading">
                  <div className="loading-indicator">
                    <div className="spinner" />
                    <span>Thinking...</span>
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div className="error-msg" role="alert">
                {error}
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <form onSubmit={handleSubmit} className="chat-form">
          <textarea
            ref={textareaRef}
            className="question-input"
            placeholder={
              selectedPoint
                ? "Ask a question about this location… (Enter to send)"
                : "Select a location first"
            }
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={!selectedPoint || loading}
            rows={2}
          />
          <button
            type="submit"
            className="submit-btn"
            disabled={!question.trim() || !selectedPoint || loading}
          >
            {loading ? "…" : "Ask"}
          </button>
        </form>
      </div>
    </div>
  );
}
