from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app, rate_limit_buckets

client = TestClient(app)


def test_request_body_size_limit():
    with patch("app.main.settings") as mock_settings:
        mock_settings.max_request_body_bytes = 10
        mock_settings.rate_limit_window_s = 60.0
        mock_settings.rate_limit_requests = 100
        response = client.post(
            "/api/query",
            content=b'{"question":"this body is too large"}',
            headers={"content-type": "application/json"},
        )

    assert response.status_code == 413


def test_rate_limit_returns_429():
    rate_limit_buckets.clear()
    with patch("app.main.settings") as mock_settings:
        mock_settings.max_request_body_bytes = 8192
        mock_settings.rate_limit_window_s = 60.0
        mock_settings.rate_limit_requests = 1
        assert client.get("/health").status_code == 200
        response = client.get("/health")

    assert response.status_code == 429
