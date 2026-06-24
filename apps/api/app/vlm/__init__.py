from .base import BaseVLM
from .gemini import GeminiVLM


def get_vlm() -> BaseVLM:
    return GeminiVLM()
