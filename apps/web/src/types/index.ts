export interface SelectedPoint {
  lat: number;
  lon: number;
  label?: string;
}

export interface QueryRequest {
  lat: number;
  lon: number;
  question: string;
}

export type Confidence = "low" | "medium" | "high";

export interface AnalysisResult {
  summary: string;
  detail: string;
  confidence: Confidence;
  caveats: string[];
  supporting_evidence: string[];
}

export interface ImageMetadata {
  item_id: string;
  datetime: string;
  cloud_cover: number | null;
  collection: string;
  source: string;
  platform: string | null;
  instrument: string | null;
  resolution_m: number | null;
}

export interface QueryResponse {
  lat: number;
  lon: number;
  question: string;
  analysis: AnalysisResult;
  image_metadata: ImageMetadata;
  image_base64: string;
}

export interface PlaceResult {
  name: string;
  display_name: string;
  latitude: number;
  longitude: number;
  type: string;
  bounding_box: number[] | null;
}
