"use client";

import { useEffect } from "react";
import L from "leaflet";
import { MapContainer, TileLayer, Marker, useMap, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { MapAction, SelectedPoint } from "@/types";

/* Fix Leaflet default marker icon paths broken by bundlers.
   Icons are served from public/leaflet/ — no external CDN dependency. */
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "/leaflet/marker-icon-2x.png",
  iconUrl: "/leaflet/marker-icon.png",
  shadowUrl: "/leaflet/marker-shadow.png",
});

interface MapProps {
  selectedPoint: SelectedPoint | null;
  onPointSelected: (point: SelectedPoint) => void;
  onMapReady?: (executeAction: (action: MapAction) => void) => void;
}

function ClickHandler({
  onPointSelected,
}: {
  onPointSelected: (point: SelectedPoint) => void;
}) {
  useMapEvents({
    click(e) {
      onPointSelected({ lat: e.latlng.lat, lon: e.latlng.lng });
    },
  });
  return null;
}

function Recenter({ selectedPoint }: { selectedPoint: SelectedPoint | null }) {
  const map = useMap();

  useEffect(() => {
    if (selectedPoint) {
      map.flyTo([selectedPoint.lat, selectedPoint.lon], Math.max(map.getZoom(), 12), {
        duration: 0.8,
      });
    }
  }, [map, selectedPoint]);

  return null;
}

/** Exposes a map action executor to the parent via onMapReady callback. */
function MapActionExecutor({
  onMapReady,
}: {
  onMapReady?: (fn: (action: MapAction) => void) => void;
}) {
  const map = useMap();

  useEffect(() => {
    if (!onMapReady) return;
    onMapReady((action: MapAction) => {
      if (action.type === "zoom_to" || action.type === "pan_to") {
        const zoom = action.zoom ?? map.getZoom();
        map.flyTo([action.lat, action.lon], zoom, { duration: 1.0 });
      }
    });
  }, [map, onMapReady]);

  return null;
}

export default function MapView({ selectedPoint, onPointSelected, onMapReady }: MapProps) {
  return (
    <MapContainer
      center={[0, 20]}
      zoom={3}
      style={{ width: "100%", height: "100%" }}
      zoomControl={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <ClickHandler onPointSelected={onPointSelected} />
      <Recenter selectedPoint={selectedPoint} />
      <MapActionExecutor onMapReady={onMapReady} />
      {selectedPoint && (
        <Marker position={[selectedPoint.lat, selectedPoint.lon]} />
      )}
    </MapContainer>
  );
}
