import type { QueryResponse } from "@/types";

interface AnswerDisplayProps {
  result: QueryResponse;
}

export default function AnswerDisplay({ result }: AnswerDisplayProps) {
  const meta = result.image_metadata;

  return (
    <div className="answer-section">
      <h3>Answer</h3>
      <div className="answer-text">{result.answer}</div>

      {meta && (
        <div className="image-meta">
          <span>
            Image date: {new Date(meta.datetime).toLocaleDateString()}
          </span>
          {meta.cloud_cover !== null && (
            <span>Cloud cover: {meta.cloud_cover.toFixed(1)}%</span>
          )}
          <span>Source: {meta.collection}</span>
        </div>
      )}
    </div>
  );
}
