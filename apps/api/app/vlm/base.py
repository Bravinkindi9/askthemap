from abc import ABC, abstractmethod

from PIL import Image

from .schemas import AnalysisResult


class BaseVLM(ABC):
    @abstractmethod
    async def ask(
        self,
        image: Image.Image,
        question: str,
        lat: float,
        lon: float,
    ) -> AnalysisResult: ...
