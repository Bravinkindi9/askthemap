from app.config import settings
from .base import BaseVLM
from .gemini import GeminiVLM
from .openrouter import OpenRouterVLM


def get_vlm() -> BaseVLM:
    if settings.vlm_provider == "openrouter":
        return OpenRouterVLM()
    if settings.vlm_provider == "gemini":
        return GeminiVLM()
    raise ValueError(f"Unsupported VLM provider '{settings.vlm_provider}'. Use 'gemini' or 'openrouter'.")
