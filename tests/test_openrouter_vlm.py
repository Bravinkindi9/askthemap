from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image
from pydantic import ValidationError

from app.vlm.openrouter import OpenRouterVLM, _strip_code_fence
from app.vlm.schemas import Confidence


def _client_returning(content: str):
    """Build a mocked httpx.AsyncClient context manager returning the given
    chat-completion message content."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"choices": [{"message": {"content": content}}]}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    mock_client_cls = MagicMock()
    mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
    return mock_client_cls, mock_client


def test_strip_code_fence_removes_markdown_wrapper():
    wrapped = '```json\n{"a": 1}\n```'
    assert _strip_code_fence(wrapped) == '{"a": 1}'


def test_strip_code_fence_leaves_plain_json_untouched():
    plain = '{"a": 1}'
    assert _strip_code_fence(plain) == plain


@pytest.mark.asyncio
@patch("app.vlm.openrouter.settings")
async def test_ask_parses_clean_json_response(mock_settings):
    mock_settings.openrouter_api_key = "test-key"
    mock_settings.openrouter_model = "qwen/qwen2.5-vl-7b-instruct:free"
    mock_settings.vlm_timeout_s = 30.0

    content = (
        '{"summary": "Urban area", "detail": "Dense buildings and roads.", '
        '"confidence": "medium", "caveats": ["single overpass"], '
        '"supporting_evidence": ["grid street pattern"]}'
    )
    mock_client_cls, mock_client = _client_returning(content)

    with patch("app.vlm.openrouter.httpx.AsyncClient", mock_client_cls):
        vlm = OpenRouterVLM()
        result = await vlm.ask(
            image=Image.new("RGB", (10, 10)), question="What is here?", lat=1.0, lon=2.0
        )

    assert result.summary == "Urban area"
    assert result.confidence == Confidence.medium
    assert result.caveats == ["single overpass"]

    call_kwargs = mock_client.post.call_args.kwargs
    assert call_kwargs["headers"]["Authorization"] == "Bearer test-key"
    assert call_kwargs["json"]["model"] == "qwen/qwen2.5-vl-7b-instruct:free"
    content_blocks = call_kwargs["json"]["messages"][0]["content"]
    assert content_blocks[0]["type"] == "text"
    assert content_blocks[1]["type"] == "image_url"
    assert content_blocks[1]["image_url"]["url"].startswith("data:image/png;base64,")


@pytest.mark.asyncio
@patch("app.vlm.openrouter.settings")
async def test_ask_parses_code_fence_wrapped_response(mock_settings):
    mock_settings.openrouter_api_key = "test-key"
    mock_settings.openrouter_model = "qwen/qwen2.5-vl-7b-instruct:free"
    mock_settings.vlm_timeout_s = 30.0

    content = (
        "```json\n"
        '{"summary": "Farmland", "detail": "Regular field boundaries.", '
        '"confidence": "high", "caveats": [], "supporting_evidence": []}\n'
        "```"
    )
    mock_client_cls, _ = _client_returning(content)

    with patch("app.vlm.openrouter.httpx.AsyncClient", mock_client_cls):
        vlm = OpenRouterVLM()
        result = await vlm.ask(
            image=Image.new("RGB", (10, 10)), question="What is here?", lat=1.0, lon=2.0
        )

    assert result.summary == "Farmland"
    assert result.confidence == Confidence.high


@pytest.mark.asyncio
@patch("app.vlm.openrouter.settings")
async def test_ask_raises_on_malformed_response(mock_settings):
    mock_settings.openrouter_api_key = "test-key"
    mock_settings.openrouter_model = "qwen/qwen2.5-vl-7b-instruct:free"
    mock_settings.vlm_timeout_s = 30.0

    mock_client_cls, _ = _client_returning("The image shows a city. Confidence: high.")

    with patch("app.vlm.openrouter.httpx.AsyncClient", mock_client_cls):
        vlm = OpenRouterVLM()
        with pytest.raises((ValidationError, ValueError)):
            await vlm.ask(
                image=Image.new("RGB", (10, 10)), question="What is here?", lat=1.0, lon=2.0
            )
