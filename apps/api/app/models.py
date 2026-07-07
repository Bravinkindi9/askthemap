from pydantic import BaseModel, Field

from app.vlm.schemas import AnalysisResult


class QueryRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    question: str = Field(..., min_length=1, max_length=1000)


class ImageMetadata(BaseModel):
    datetime: str
    cloud_cover: float | None = None
    collection: str
    asset_href: str
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
