import asyncio
import io

from google import genai
from PIL import Image

from app.config import settings
from .base import BaseVLM

SYSTEM_PROMPT = (
    "You are a geospatial analyst examining satellite imagery. "
    "The image is a Sentinel-2 satellite view centered at "
    "latitude {lat:.4f}, longitude {lon:.4f}. "
    "Analyze what you observe in the image and answer the user's question. "
    "Be specific about visible features: land cover, vegetation, urban areas, "
    "water bodies, infrastructure, terrain. "
    "If you cannot determine something from the image, say so clearly."
)


class GeminiVLM(BaseVLM):
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)

    async def ask(
        self,
        image: Image.Image,
        question: str,
        lat: float,
        lon: float,
    ) -> str:
        prompt = SYSTEM_PROMPT.format(lat=lat, lon=lon) + f"\n\nQuestion: {question}"

        buf = io.BytesIO()
        image.save(buf, format="PNG")
        image_bytes = buf.getvalue()

        image_part = genai.types.Part.from_bytes(data=image_bytes, mime_type="image/png")

        def _call():
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[prompt, image_part],
            )
            return response.text

        return await asyncio.to_thread(_call)
