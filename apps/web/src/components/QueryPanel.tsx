"use client";

import { useState } from "react";
import AnswerDisplay from "./AnswerDisplay";
import type { SelectedPoint, QueryResponse } from "@/types";

interface QueryPanelProps {
  selectedPoint: SelectedPoint | null;
  loading: boolean;
  result: QueryResponse | null;
  error: string | null;
  onSubmit: (question: string) => void;
}

export default function QueryPanel({
  selectedPoint,
  loading,
  result,
  error,
  onSubmit,
}: QueryPanelProps) {
  const [question, setQuestion] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (question.trim() && selectedPoint && !loading) {
      onSubmit(question.trim());
    }
  }

  return (
    <div className="side-panel">
      <div className="panel-header">
        <h1>AskTheMap</h1>
        <p>Click a point on the map, then ask a question</p>
      </div>

      <div className="panel-body">
        {!selectedPoint ? (
          <div className="empty-state">
            Click anywhere on the map to select a location and start asking
            questions about it.
          </div>
        ) : (
          <>
            <div className="coordinates">
              Location:{" "}
              <span>
                {selectedPoint.lat.toFixed(4)}, {selectedPoint.lon.toFixed(4)}
              </span>
            </div>

            <form onSubmit={handleSubmit}>
              <textarea
                className="question-input"
                placeholder="What do you want to know about this location?"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={loading}
              />
              <button
                type="submit"
                className="submit-btn"
                disabled={!question.trim() || loading}
                style={{ marginTop: 12 }}
              >
                {loading ? "Analyzing..." : "Ask"}
              </button>
            </form>

            {loading && (
              <div className="loading-indicator">
                <div className="spinner" />
                Searching satellite imagery and analyzing...
              </div>
            )}

            {error && <div className="error-msg">{error}</div>}

            {result && <AnswerDisplay result={result} />}
          </>
        )}
      </div>
    </div>
  );
}
