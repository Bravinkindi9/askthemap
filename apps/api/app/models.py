from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    question: str = Field(..., min_length=1, max_length=1000)


class ImageMetadata(BaseModel):
    datetime: str
    cloud_cover: float | None = None
    collection: str
    asset_href: str


class QueryResponse(BaseModel):
    answer: str
    lat: float
    lon: float
    question: str
    image_metadata: ImageMetadata | None = None
