import type { ImageMetadata } from "@/types";

interface SatelliteImagePreviewProps {
  imageBase64: string;
  metadata: ImageMetadata;
}

export default function SatelliteImagePreview({
  imageBase64,
  metadata,
}: SatelliteImagePreviewProps) {
  return (
    <div className="image-preview">
      {/* eslint-disable-next-line @next/next/no-img-element -- locally generated base64 tile, not a remote/optimizable image */}
      <img
        src={`data:image/png;base64,${imageBase64}`}
        alt="Satellite tile analyzed for this location"
        className="image-preview-img"
      />
      <div className="image-meta">
        <span>Image date: {new Date(metadata.datetime).toLocaleDateString()}</span>
        {metadata.platform && <span>Satellite: {metadata.platform}</span>}
        {metadata.resolution_m != null && (
          <span>Resolution: {metadata.resolution_m}m/pixel</span>
        )}
        {metadata.cloud_cover != null && (
          <span>Cloud cover: {metadata.cloud_cover.toFixed(1)}%</span>
        )}
        <span>Source: {metadata.collection}</span>
      </div>
    </div>
  );
}
