"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import QueryPanel from "@/components/QueryPanel";
import type { SelectedPoint, QueryResponse } from "@/types";
import { queryLocation } from "@/lib/api";

const MapView = dynamic(() => import("@/components/Map"), { ssr: false });

export default function Home() {
  const [selectedPoint, setSelectedPoint] = useState<SelectedPoint | null>(
    null
  );
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(question: string) {
    if (!selectedPoint) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await queryLocation({
        lat: selectedPoint.lat,
        lon: selectedPoint.lon,
        question,
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  function handlePointSelected(point: SelectedPoint) {
    setSelectedPoint(point);
    setResult(null);
    setError(null);
  }

  return (
    <div className="app-container">
      <div className="map-container">
        <MapView
          selectedPoint={selectedPoint}
          onPointSelected={handlePointSelected}
        />
      </div>
      <QueryPanel
        selectedPoint={selectedPoint}
        loading={loading}
        result={result}
        error={error}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
