import base64
import io

import httpx
from PIL import Image

from app.config import settings
from .base import BaseVLM
from .prompts import build_analyst_prompt
from .schemas import AnalysisResult, Confidence

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Hand-written rather than derived from AnalysisResult.model_json_schema(): the
# Pydantic-generated schema uses $defs/$ref for the Confidence enum and leaves
# caveats/supporting_evidence optional, which strict JSON-schema response modes
# on third-party models handle inconsistently. This flat, fully-required form is
# the safer wire format; Pydantic still does the real validation on the way back.
_RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "detail": {"type": "string"},
        "confidence": {"type": "string", "enum": [c.value for c in Confidence]},
        "caveats": {"type": "array", "items": {"type": "string"}},
        "supporting_evidence": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "detail", "confidence", "caveats", "supporting_evidence"],
    "additionalProperties": False,
}

# Open models are less consistent about honoring response_format than Gemini's
# native schema mode, so the shape is also reinforced directly in the prompt.
_JSON_SHAPE_HINT = (
    "\n\nRespond with ONLY a single JSON object, no markdown formatting, no code "
    'fences, matching this exact shape: {"summary": "...", "detail": "...", '
    '"confidence": "low"|"medium"|"high", "caveats": ["..."], "supporting_evidence": ["..."]}'
)


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if not text.startswith("```"):
        return text
    lines = text.split("\n")[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


class OpenRouterVLM(BaseVLM):
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model

    async def ask(
        self,
        image: Image.Image,
        question: str,
        lat: float,
        lon: float,
    ) -> AnalysisResult:
        prompt = build_analyst_prompt(lat, lon, question) + _JSON_SHAPE_HINT

        buf = io.BytesIO()
        image.save(buf, format="PNG")
        image_b64 = base64.b64encode(buf.getvalue()).decode("ascii")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                        },
                    ],
                }
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "AnalysisResult",
                    "strict": True,
                    "schema": _RESPONSE_JSON_SCHEMA,
                },
            },
        }

        async with httpx.AsyncClient(timeout=settings.vlm_timeout_s) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "X-Title": "AskTheMap",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        return AnalysisResult.model_validate_json(_strip_code_fence(content))
