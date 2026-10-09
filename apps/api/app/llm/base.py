"""Abstract base for text-only LLM providers used by the chat endpoint."""
from abc import ABC, abstractmethod


class BaseTextLLM(ABC):
    @abstractmethod
    async def answer(self, prompt: str) -> str:
        """Send a text prompt and return the model's plain-text reply."""
