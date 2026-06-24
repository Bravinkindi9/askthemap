"use client";

import { useEffect } from "react";
import L from "leaflet";
import { MapContainer, TileLayer, Marker, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { SelectedPoint } from "@/types";

/* Fix Leaflet's default marker icon paths broken by bundlers */
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

interface MapProps {
  selectedPoint: SelectedPoint | null;
  onPointSelected: (point: SelectedPoint) => void;
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

export default function MapView({ selectedPoint, onPointSelected }: MapProps) {
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
      {selectedPoint && (
        <Marker position={[selectedPoint.lat, selectedPoint.lon]} />
      )}
    </MapContainer>
  );
}
