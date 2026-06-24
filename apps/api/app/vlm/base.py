from abc import ABC, abstractmethod

from PIL import Image


class BaseVLM(ABC):
    @abstractmethod
    async def ask(
        self,
        image: Image.Image,
        question: str,
        lat: float,
        lon: float,
    ) -> str: ...
