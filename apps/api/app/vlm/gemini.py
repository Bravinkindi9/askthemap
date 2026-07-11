import asyncio
import io

from google import genai
from google.genai import types
from PIL import Image

from app.config import settings
from .base import BaseVLM
from .prompts import build_analyst_prompt
from .schemas import AnalysisResult


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
        prompt = build_analyst_prompt(lat, lon, question)

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
