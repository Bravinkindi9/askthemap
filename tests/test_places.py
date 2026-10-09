from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import PlaceResult
from app.places import _normalize_place

client = TestClient(app)


def test_normalize_place():
    result = _normalize_place(
        {
            "name": "Kigali",
            "display_name": "Kigali, Rwanda",
            "lat": "-1.9441",
            "lon": "30.0619",
            "type": "city",
            "boundingbox": ["-2.1", "-1.8", "29.9", "30.2"],
        }
    )
    assert result == PlaceResult(
        name="Kigali",
        display_name="Kigali, Rwanda",
        latitude=-1.9441,
        longitude=30.0619,
        type="city",
        bounding_box=[-2.1, -1.8, 29.9, 30.2],
    )


@patch("app.routers.places.search_place", new_callable=AsyncMock)
def test_place_search_endpoint(mock_search):
    mock_search.return_value = [
        PlaceResult(
            name="Kigali",
            display_name="Kigali, Rwanda",
            latitude=-1.9441,
            longitude=30.0619,
            type="city",
            bounding_box=None,
        )
    ]

    response = client.get("/api/places/search?q=Kigali")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["name"] == "Kigali"
    assert data[0]["latitude"] == -1.9441


@patch("app.places.settings")
@patch("app.places.httpx.AsyncClient")
@pytest.mark.anyio
async def test_search_place_uses_identifying_user_agent(mock_client_cls, mock_settings):
    from app.places import _cache, search_place

    _cache.clear()
    mock_settings.place_search_provider = "nominatim"
    mock_settings.place_search_url = "https://nominatim.openstreetmap.org/search"
    mock_settings.place_search_user_agent = "AskioTest/0.1"
    mock_settings.place_search_timeout_s = 8.0
    mock_settings.place_search_min_interval_s = 0.0
    mock_settings.place_search_cache_ttl_s = 86400.0

    response = MagicMock()
    response.json.return_value = [
        {
            "name": "Kigali",
            "display_name": "Kigali, Rwanda",
            "lat": "-1.9441",
            "lon": "30.0619",
            "type": "city",
        }
    ]
    response.raise_for_status.return_value = None
    client_instance = AsyncMock()
    client_instance.get.return_value = response
    mock_client_cls.return_value.__aenter__.return_value = client_instance

    await search_place("Kigali")

    _, kwargs = client_instance.get.call_args
    assert kwargs["headers"]["User-Agent"] == "AskioTest/0.1"
    assert kwargs["params"]["format"] == "jsonv2"
    assert kwargs["params"]["limit"] == 5
