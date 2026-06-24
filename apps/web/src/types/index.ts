export interface SelectedPoint {
  lat: number;
  lon: number;
}

export interface QueryRequest {
  lat: number;
  lon: number;
  question: string;
}

export interface ImageMetadata {
  datetime: string;
  cloud_cover: number | null;
  collection: string;
  asset_href: string;
}

export interface QueryResponse {
  answer: string;
  lat: number;
  lon: number;
  question: string;
  image_metadata: ImageMetadata | null;
}
