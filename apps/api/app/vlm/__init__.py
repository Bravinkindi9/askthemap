from app.config import settings
from .base import BaseVLM
from .gemini import GeminiVLM
from .openrouter import OpenRouterVLM


def get_vlm() -> BaseVLM:
    if settings.vlm_provider == "openrouter":
        return OpenRouterVLM()
    return GeminiVLM()
