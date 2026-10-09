from typing import Literal

from pydantic import BaseModel, Field

from app.vlm.schemas import AnalysisResult


class QueryRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    question: str = Field(..., min_length=1, max_length=1000)


class ImageMetadata(BaseModel):
    item_id: str
    datetime: str
    cloud_cover: float | None = None
    collection: str
    source: str
    platform: str | None = None
    instrument: str | None = None
    resolution_m: float | None = None


class QueryResponse(BaseModel):
    lat: float
    lon: float
    question: str
    analysis: AnalysisResult
    image_metadata: ImageMetadata
    image_base64: str = Field(..., description="PNG-encoded satellite tile that was analyzed, base64 without a data: prefix.")


class PlaceResult(BaseModel):
    name: str
    display_name: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    type: str
    bounding_box: list[float] | None = Field(
        default=None,
        description="Optional [south, north, west, east] bounds when provided by the search provider.",
    )


# ---------------------------------------------------------------------------
# Conversational map models (Phase 1)
# ---------------------------------------------------------------------------

class LocationContext(BaseModel):
    """The user's active map state sent with every chat request."""
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    label: str | None = Field(
        default=None,
        description="Human-readable place name, e.g. 'Kigali, Rwanda'. "
                    "Populated by reverse geocoding after a map click.",
    )
    zoom: int | None = Field(default=None, ge=1, le=20)


class ChatTurn(BaseModel):
    """One turn in the conversation. Content is always plain text — images
    are never stored in history to avoid payload bloat."""
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    location: LocationContext
    question: str = Field(..., min_length=1, max_length=1000)
    history: list[ChatTurn] = Field(
        default_factory=list,
        max_length=12,
        description="Last N conversation turns, oldest first. "
                    "Frontend is responsible for truncation.",
    )


class MapAction(BaseModel):
    """A structured, allow-listed action the frontend may execute after
    receiving a response. The frontend validates the type before acting."""
    type: Literal["zoom_to", "pan_to"]
    lat: float
    lon: float
    zoom: int | None = None


class ChatResponse(BaseModel):
    reply: str = Field(..., description="The assistant's conversational reply.")
    sources: list[str] = Field(
        default_factory=list,
        description="Data sources used to generate this answer, e.g. ['OpenStreetMap', 'Sentinel-2'].",
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Deterministic measurements or observations returned with this answer.",
    )
    image_metadata: ImageMetadata | None = Field(
        default=None,
        description="Present only when satellite imagery was retrieved and analyzed.",
    )
    image_base64: str | None = Field(
        default=None,
        description="PNG satellite tile, base64-encoded, no data: prefix. "
                    "Present only when image_metadata is also present.",
    )
    map_action: MapAction | None = Field(
        default=None,
        description="Optional map action for the frontend to execute.",
    )
