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
