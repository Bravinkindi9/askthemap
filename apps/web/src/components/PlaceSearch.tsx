"use client";

import { useState } from "react";
import type { PlaceResult, SelectedPoint } from "@/types";
import { searchPlaces } from "@/lib/api";

interface PlaceSearchProps {
  onPlaceSelected: (point: SelectedPoint) => void;
}

export default function PlaceSearch({ onPlaceSelected }: PlaceSearchProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PlaceResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = query.trim();
    if (trimmed.length < 2 || loading) return;

    setLoading(true);
    setError(null);
    try {
      setResults(await searchPlaces(trimmed));
    } catch (err) {
      setResults([]);
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  function choosePlace(place: PlaceResult) {
    onPlaceSelected({
      lat: place.latitude,
      lon: place.longitude,
      label: place.name || place.display_name,
    });
    setResults([]);
    setQuery(place.name || place.display_name);
  }

  return (
    <div className="place-search">
      <form onSubmit={handleSubmit} className="place-search-form">
        <input
          className="place-search-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search a place"
          aria-label="Search a place"
        />
        <button className="place-search-button" type="submit" disabled={loading}>
          {loading ? "..." : "Search"}
        </button>
      </form>

      {error && <div className="place-search-error">{error}</div>}

      {results.length > 0 && (
        <div className="place-search-results">
          {results.map((place) => (
            <button
              key={`${place.latitude}-${place.longitude}-${place.display_name}`}
              type="button"
              className="place-search-result"
              onClick={() => choosePlace(place)}
            >
              <span>{place.name}</span>
              <small>{place.display_name}</small>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
