import pytest
from pydantic import ValidationError

from app.models import QueryRequest, QueryResponse, ImageMetadata


def test_query_request_valid():
    req = QueryRequest(lat=-1.9403, lon=29.8739, question="What is here?")
    assert req.lat == -1.9403
    assert req.lon == 29.8739


def test_query_request_lat_out_of_range():
    with pytest.raises(ValidationError):
        QueryRequest(lat=91, lon=0, question="test")


def test_query_request_lon_out_of_range():
    with pytest.raises(ValidationError):
        QueryRequest(lat=0, lon=181, question="test")


def test_query_request_empty_question():
    with pytest.raises(ValidationError):
        QueryRequest(lat=0, lon=0, question="")


def test_query_response():
    resp = QueryResponse(
        answer="Urban area",
        lat=-1.9403,
        lon=29.8739,
        question="What is here?",
        image_metadata=ImageMetadata(
            datetime="2026-06-12T08:00:00Z",
            cloud_cover=15.0,
            collection="sentinel-2-l2a",
            asset_href="https://example.com/image.tif",
        ),
    )
    assert resp.answer == "Urban area"
    assert resp.image_metadata.cloud_cover == 15.0


def test_query_response_no_metadata():
    resp = QueryResponse(
        answer="Unknown",
        lat=0,
        lon=0,
        question="test",
        image_metadata=None,
    )
    assert resp.image_metadata is None
