"use client";

import { useCallback, useRef, useState } from "react";
import dynamic from "next/dynamic";
import PlaceSearch from "@/components/PlaceSearch";
import ChatPanel from "@/components/ChatPanel";
import { reverseGeocode, sendChatMessage } from "@/lib/api";
import type { ChatTurn, LocationContext, MapAction, Message, SelectedPoint } from "@/types";

const MapView = dynamic(() => import("@/components/Map"), { ssr: false });

/** Build the history array to send to the API: last 12 ChatTurn entries. */
function buildHistory(messages: Message[]): ChatTurn[] {
  const turns: ChatTurn[] = [];
  for (const msg of messages) {
    turns.push({ role: msg.role, content: msg.content });
  }
  return turns.slice(-12);
}

export default function Home() {
  const [selectedPoint, setSelectedPoint] = useState<SelectedPoint | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Map action ref — MapView exposes a callback so we can flyTo programmatically
  const mapActionRef = useRef<((action: MapAction) => void) | null>(null);

  /** Called when user submits a question. */
  const handleSubmit = useCallback(
    async (question: string) => {
      if (!selectedPoint || loading) return;

      const userMessage: Message = { role: "user", content: question };
      setMessages((prev) => [...prev, userMessage]);
      setLoading(true);
      setError(null);

      const location: LocationContext = {
        lat: selectedPoint.lat,
        lon: selectedPoint.lon,
        label: selectedPoint.label,
      };

      try {
        const response = await sendChatMessage({
          location,
          question,
          history: buildHistory([...messages, userMessage]).slice(0, -1), // history excludes the new user turn
        });

        const assistantMessage: Message = {
          role: "assistant",
          content: response.reply,
          response,
        };
        setMessages((prev) => [...prev, assistantMessage]);

        // Execute allow-listed map action if present
        if (response.map_action && mapActionRef.current) {
          const allowed = new Set(["zoom_to", "pan_to"]);
          if (allowed.has(response.map_action.type)) {
            mapActionRef.current(response.map_action);
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Something went wrong");
      } finally {
        setLoading(false);
      }
    },
    [selectedPoint, loading, messages]
  );

  /** Called when user clicks the map or selects a place result. */
  const handlePointSelected = useCallback((point: SelectedPoint) => {
    setSelectedPoint(point);
    setMessages([]);
    setError(null);

    // Fire-and-forget reverse geocode — update label when it resolves
    reverseGeocode(point.lat, point.lon).then((place) => {
      if (place) {
        setSelectedPoint((prev) =>
          prev && prev.lat === point.lat && prev.lon === point.lon
            ? { ...prev, label: place.display_name }
            : prev
        );
      }
    });
  }, []);

  /** Called by MapView to give us a handle to execute map actions. */
  const handleMapReady = useCallback((fn: (action: MapAction) => void) => {
    mapActionRef.current = fn;
  }, []);

  return (
    <div className="app-container">
      <div className="map-container">
        <PlaceSearch onPlaceSelected={handlePointSelected} />
        <MapView
          selectedPoint={selectedPoint}
          onPointSelected={handlePointSelected}
          onMapReady={handleMapReady}
        />
      </div>
      <ChatPanel
        selectedPoint={selectedPoint}
        messages={messages}
        loading={loading}
        error={error}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
