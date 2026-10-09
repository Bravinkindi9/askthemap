"""Gemini text-only LLM implementation."""
import asyncio
import logging

from google import genai
from google.genai import types

from app.config import settings
from app.llm.base import BaseTextLLM

logger = logging.getLogger(__name__)


class GeminiTextLLM(BaseTextLLM):
    async def answer(self, prompt: str) -> str:
        def _call() -> str:
            client = genai.Client(api_key=settings.gemini_api_key)
            response = client.models.generate_content(
                model=settings.text_model_gemini,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    http_options=types.HttpOptions(
                        timeout=int(settings.vlm_timeout_s * 1000)
                    ),
                ),
            )
            return response.text or ""

        return await asyncio.to_thread(_call)
