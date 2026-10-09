import type {
  ChatRequest,
  ChatResponse,
  ChatTurn,
  LocationContext,
  PlaceResult,
  QueryRequest,
  QueryResponse,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function queryLocation(req: QueryRequest): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function searchPlaces(query: string): Promise<PlaceResult[]> {
  const params = new URLSearchParams({ q: query });
  const res = await fetch(`${API_BASE}/api/places/search?${params.toString()}`);

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Search failed" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

/** Reverse geocode a coordinate to a human-readable place name.
 *  Returns null for ocean / polar areas or if the request fails.
 *  Never throws — failure is silently degraded. */
export async function reverseGeocode(
  lat: number,
  lon: number
): Promise<PlaceResult | null> {
  try {
    const params = new URLSearchParams({ lat: String(lat), lon: String(lon) });
    const res = await fetch(`${API_BASE}/api/places/reverse?${params.toString()}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/** Send a chat message with location context and conversation history. */
export async function sendChatMessage(req: {
  location: LocationContext;
  question: string;
  history: ChatTurn[];
}): Promise<ChatResponse> {
  const body: ChatRequest = {
    location: req.location,
    question: req.question,
    history: req.history,
  };

  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}
