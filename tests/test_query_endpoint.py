from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("app.routers.query.search_imagery", new_callable=AsyncMock)
def test_query_no_imagery(mock_search):
    mock_search.return_value = None
    response = client.post(
        "/api/query",
        json={"lat": 0, "lon": 0, "question": "What is here?"},
    )
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
    mock_search.return_value = {
        "datetime": "2026-06-12T08:00:00Z",
        "cloud_cover": 10.0,
        "collection": "sentinel-2-l2a",
        "asset_href": "https://example.com/image.tif",
    }
    mock_fetch.return_value = Image.new("RGB", (512, 512))

    mock_vlm = MagicMock()
    mock_vlm.ask = AsyncMock(return_value="This is an urban area.")
    mock_get_vlm.return_value = mock_vlm

    response = client.post(
        "/api/query",
        json={"lat": -1.9403, "lon": 29.8739, "question": "What is here?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "This is an urban area."
    assert data["lat"] == -1.9403
    assert data["image_metadata"]["collection"] == "sentinel-2-l2a"
