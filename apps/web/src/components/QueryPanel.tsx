"use client";

import { useEffect, useState } from "react";
import AnalysisPanel from "./AnalysisPanel";
import type { SelectedPoint, QueryResponse } from "@/types";

const LOADING_STAGES = [
  "Searching satellite imagery...",
  "Retrieving satellite tile...",
  "Running AI analysis...",
  "Preparing results...",
];

const STAGE_INTERVAL_MS = 1800;

/**
 * The backend responds with a single JSON payload, not a progress stream, so
 * this can't reflect the server's actual stage. It cycles through plausible
 * stages but caps at the last one and never advances past it until the real
 * response arrives -- it can undersell progress, never oversell it.
 */
function useLoadingStage(loading: boolean): string {
  const [stageIndex, setStageIndex] = useState(0);

  useEffect(() => {
    if (!loading) {
      setStageIndex(0);
      return;
    }
    const interval = setInterval(() => {
      setStageIndex((i) => Math.min(i + 1, LOADING_STAGES.length - 1));
    }, STAGE_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [loading]);

  return LOADING_STAGES[stageIndex];
}

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
  const loadingStage = useLoadingStage(loading);

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
                {loadingStage}
              </div>
            )}

            {error && <div className="error-msg">{error}</div>}

            {result && <AnalysisPanel result={result} />}
          </>
        )}
      </div>
    </div>
  );
}
