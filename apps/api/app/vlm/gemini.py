import asyncio
import io

from google import genai
from google.genai import types
from PIL import Image

from app.config import settings
from .base import BaseVLM
from .schemas import AnalysisResult

SYSTEM_PROMPT = (
    "You are a geospatial analyst examining satellite imagery. "
    "The image is a Sentinel-2 satellite view centered at "
    "latitude {lat:.4f}, longitude {lon:.4f}. "
    "Analyze what you observe in the image and answer the user's question. "
    "Be specific about visible features: land cover, vegetation, urban areas, "
    "water bodies, infrastructure, terrain. "
    "Set confidence to 'low' if the image is unclear, too coarse, or the question "
    "cannot be reliably answered from a single satellite snapshot; use 'high' only "
    "when the relevant features are clearly visible. "
    "List any caveats that affect how much the answer should be trusted "
    "(e.g. cloud cover, resolution limits, image age). "
    "List the specific visual details that support your summary as supporting evidence. "
    "If you cannot determine something from the image, say so clearly rather than guessing."
)


class GeminiVLM(BaseVLM):
    def __init__(self):
        self.client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(timeout=int(settings.vlm_timeout_s * 1000)),
        )

    async def ask(
        self,
        image: Image.Image,
        question: str,
        lat: float,
        lon: float,
    ) -> AnalysisResult:
        prompt = SYSTEM_PROMPT.format(lat=lat, lon=lon) + f"\n\nQuestion: {question}"

        buf = io.BytesIO()
        image.save(buf, format="PNG")
        image_part = types.Part.from_bytes(data=buf.getvalue(), mime_type="image/png")

        def _call() -> AnalysisResult:
            response = self.client.models.generate_content(
                model=settings.gemini_model,
                contents=[prompt, image_part],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AnalysisResult,
                ),
            )
            if response.parsed is None:
                raise ValueError("Gemini did not return a parseable structured response")
            return response.parsed

        return await asyncio.to_thread(_call)
