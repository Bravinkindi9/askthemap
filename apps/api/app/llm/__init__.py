"""Text LLM factory — mirrors app/vlm/__init__.py pattern."""
from app.config import settings
from app.llm.base import BaseTextLLM


def get_text_llm() -> BaseTextLLM:
    if settings.vlm_provider == "openrouter":
        from app.llm.openrouter import OpenRouterTextLLM
        return OpenRouterTextLLM()
    from app.llm.gemini import GeminiTextLLM
    return GeminiTextLLM()
