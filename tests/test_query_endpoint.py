import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.vlm.schemas import AnalysisResult, Confidence

client = TestClient(app)

VALID_REQUEST = {"lat": -1.9403, "lon": 29.8739, "question": "What is here?"}

SEARCH_RESULT = {
    "datetime": "2026-06-12T08:00:00Z",
    "cloud_cover": 10.0,
    "collection": "sentinel-2-l2a",
    "asset_href": "https://example.com/image.tif",
    "platform": "Sentinel-2B",
    "instrument": "msi",
    "resolution_m": 10.0,
}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("app.routers.query.search_imagery", new_callable=AsyncMock)
def test_query_no_imagery(mock_search):
    mock_search.return_value = None
    response = client.post("/api/query", json=VALID_REQUEST)
    assert response.status_code == 404


@patch("app.routers.query.settings")
@patch("app.routers.query.get_vlm")
@patch("app.routers.query.fetch_image", new_callable=AsyncMock)
@patch("app.routers.query.search_imagery", new_callable=AsyncMock)
def test_query_success(mock_search, mock_fetch, mock_get_vlm, mock_settings):
    mock_settings.gemini_api_key = "test-key"
    mock_settings.max_cloud_cover = 30
    mock_settings.stac_api_url = "https://planetarycomputer.microsoft.com/api/stac/v1"
    mock_settings.image_size_px = 512
    mock_settings.stac_timeout_s = 10.0
    mock_settings.image_fetch_timeout_s = 15.0
    mock_settings.vlm_timeout_s = 20.0
    mock_search.return_value = SEARCH_RESULT
    mock_fetch.return_value = Image.new("RGB", (512, 512))

    mock_vlm = MagicMock()
    mock_vlm.ask = AsyncMock(
        return_value=AnalysisResult(
            summary="This is an urban area.",
            detail="Dense grid of streets and rooftops fills the frame.",
            confidence=Confidence.high,
            caveats=["Image is from a single overpass; conditions may have changed."],
            supporting_evidence=["Grid-like street pattern", "Rooftop clusters"],
        )
    )
    mock_get_vlm.return_value = mock_vlm

    response = client.post("/api/query", json=VALID_REQUEST)
    assert response.status_code == 200
    data = response.json()
    assert data["analysis"]["summary"] == "This is an urban area."
    assert data["analysis"]["confidence"] == "high"
    assert data["lat"] == -1.9403
    assert data["image_metadata"]["collection"] == "sentinel-2-l2a"
    assert data["image_metadata"]["platform"] == "Sentinel-2B"
    assert len(data["image_base64"]) > 0


@patch("app.routers.query.settings")
@patch("app.routers.query.search_imagery", new_callable=AsyncMock)
def test_query_stac_timeout_returns_friendly_error(mock_search, mock_settings):
    mock_settings.max_cloud_cover = 30
    mock_settings.stac_api_url = "https://planetarycomputer.microsoft.com/api/stac/v1"
    mock_settings.stac_timeout_s = 10.0
    mock_search.side_effect = asyncio.TimeoutError()

    response = client.post("/api/query", json=VALID_REQUEST)
    assert response.status_code == 504
    assert "too long" in response.json()["detail"].lower()


@patch("app.routers.query.settings")
@patch("app.routers.query.search_imagery", new_callable=AsyncMock)
def test_query_stac_failure_does_not_leak_exception_detail(mock_search, mock_settings):
    mock_settings.max_cloud_cover = 30
    mock_settings.stac_api_url = "https://planetarycomputer.microsoft.com/api/stac/v1"
    mock_settings.stac_timeout_s = 10.0
    mock_search.side_effect = RuntimeError("upstream credentials rejected: secret-token-123")

    response = client.post("/api/query", json=VALID_REQUEST)
    assert response.status_code == 502
    detail = response.json()["detail"]
    assert "secret-token-123" not in detail
    assert "try again" in detail.lower()


@patch("app.routers.query.settings")
@patch("app.routers.query.fetch_image", new_callable=AsyncMock)
@patch("app.routers.query.search_imagery", new_callable=AsyncMock)
def test_query_image_fetch_failure_returns_friendly_error(mock_search, mock_fetch, mock_settings):
    mock_settings.max_cloud_cover = 30
    mock_settings.stac_api_url = "https://planetarycomputer.microsoft.com/api/stac/v1"
    mock_settings.stac_timeout_s = 10.0
    mock_settings.image_size_px = 512
    mock_settings.image_fetch_timeout_s = 15.0
    mock_search.return_value = SEARCH_RESULT
    mock_fetch.side_effect = RuntimeError("GDAL: curl error 28")

    response = client.post("/api/query", json=VALID_REQUEST)
    assert response.status_code == 502
    detail = response.json()["detail"]
    assert "curl" not in detail.lower()
    assert "download" in detail.lower()


@patch("app.routers.query.settings")
@patch("app.routers.query.get_vlm")
@patch("app.routers.query.fetch_image", new_callable=AsyncMock)
@patch("app.routers.query.search_imagery", new_callable=AsyncMock)
def test_query_vlm_failure_returns_friendly_error(mock_search, mock_fetch, mock_get_vlm, mock_settings):
    mock_settings.gemini_api_key = "test-key"
    mock_settings.max_cloud_cover = 30
    mock_settings.stac_api_url = "https://planetarycomputer.microsoft.com/api/stac/v1"
    mock_settings.stac_timeout_s = 10.0
    mock_settings.image_size_px = 512
    mock_settings.image_fetch_timeout_s = 15.0
    mock_settings.vlm_timeout_s = 20.0
    mock_search.return_value = SEARCH_RESULT
    mock_fetch.return_value = Image.new("RGB", (512, 512))

    mock_vlm = MagicMock()
    mock_vlm.ask = AsyncMock(side_effect=RuntimeError("Gemini API key abc123 invalid"))
    mock_get_vlm.return_value = mock_vlm

    response = client.post("/api/query", json=VALID_REQUEST)
    assert response.status_code == 502
    detail = response.json()["detail"]
    assert "abc123" not in detail
    assert "analysis failed" in detail.lower()


@patch("app.routers.query.settings")
@patch("app.routers.query.fetch_image", new_callable=AsyncMock)
@patch("app.routers.query.search_imagery", new_callable=AsyncMock)
def test_query_missing_api_key(mock_search, mock_fetch, mock_settings):
    mock_settings.gemini_api_key = ""
    mock_settings.max_cloud_cover = 30
    mock_settings.stac_api_url = "https://planetarycomputer.microsoft.com/api/stac/v1"
    mock_settings.stac_timeout_s = 10.0
    mock_settings.image_size_px = 512
    mock_settings.image_fetch_timeout_s = 15.0
    mock_search.return_value = SEARCH_RESULT
    mock_fetch.return_value = Image.new("RGB", (512, 512))

    response = client.post("/api/query", json=VALID_REQUEST)
    assert response.status_code == 503
