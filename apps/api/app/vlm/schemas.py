from enum import Enum

from pydantic import BaseModel, Field


class Confidence(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class AnalysisResult(BaseModel):
    summary: str = Field(..., description="A one or two sentence direct answer to the question.")
    detail: str = Field(..., description="A fuller explanation of what supports the summary.")
    confidence: Confidence
    caveats: list[str] = Field(
        default_factory=list,
        description="Known limitations affecting how much this analysis should be trusted "
        "(e.g. cloud cover, image resolution, image age).",
    )
    supporting_evidence: list[str] = Field(
        default_factory=list,
        description="Specific visual observations from the image that support the summary.",
    )
