import type { Confidence, QueryResponse } from "@/types";
import SatelliteImagePreview from "./SatelliteImagePreview";

interface AnalysisPanelProps {
  result: QueryResponse;
}

const CONFIDENCE_LABEL: Record<Confidence, string> = {
  low: "Low confidence",
  medium: "Medium confidence",
  high: "High confidence",
};

export default function AnalysisPanel({ result }: AnalysisPanelProps) {
  const { analysis } = result;

  return (
    <div className="analysis-panel">
      <SatelliteImagePreview
        imageBase64={result.image_base64}
        metadata={result.image_metadata}
      />

      <div className="analysis-section">
        <div className="analysis-header">
          <h3>Analysis</h3>
          <span className={`confidence-badge confidence-${analysis.confidence}`}>
            {CONFIDENCE_LABEL[analysis.confidence]}
          </span>
        </div>

        <p className="analysis-summary">{analysis.summary}</p>

        <details className="analysis-detail">
          <summary>Detailed explanation</summary>
          <p>{analysis.detail}</p>
        </details>

        {analysis.supporting_evidence.length > 0 && (
          <div className="evidence-block">
            <h4>Supporting evidence</h4>
            <ul>
              {analysis.supporting_evidence.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>
        )}

        {analysis.caveats.length > 0 && (
          <div className="caveats-block">
            <h4>Caveats</h4>
            <ul>
              {analysis.caveats.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
