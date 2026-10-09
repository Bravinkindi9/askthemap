"""OpenRouter text-only LLM implementation."""
import logging

import httpx

from app.config import settings
from app.llm.base import BaseTextLLM

logger = logging.getLogger(__name__)


class OpenRouterTextLLM(BaseTextLLM):
    async def answer(self, prompt: str) -> str:
        payload = {
            "model": settings.text_model_openrouter,
            "messages": [{"role": "user", "content": prompt}],
        }
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://askio.app",
            "X-Title": "Askio",
        }
        async with httpx.AsyncClient(timeout=settings.vlm_timeout_s) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"] or ""
