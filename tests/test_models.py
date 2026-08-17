import pytest
from pydantic import ValidationError

from app.models import ImageMetadata, PlaceResult, QueryRequest, QueryResponse
from app.vlm.schemas import AnalysisResult, Confidence


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


def test_analysis_result_defaults():
    analysis = AnalysisResult(summary="Urban area", detail="Dense buildings visible.", confidence=Confidence.high)
    assert analysis.caveats == []
    assert analysis.supporting_evidence == []


def test_query_response():
    resp = QueryResponse(
        lat=-1.9403,
        lon=29.8739,
        question="What is here?",
        analysis=AnalysisResult(
            summary="Urban area",
            detail="Dense buildings and roads visible across the frame.",
            confidence=Confidence.high,
            caveats=["Image is several months old."],
            supporting_evidence=["Grid-like street pattern", "Rooftop clusters"],
        ),
        image_metadata=ImageMetadata(
            item_id="S2A_TEST_ITEM",
            datetime="2026-06-12T08:00:00Z",
            cloud_cover=15.0,
            collection="sentinel-2-l2a",
            source="Microsoft Planetary Computer",
            platform="Sentinel-2B",
            instrument="msi",
            resolution_m=10.0,
        ),
        image_base64="iVBORw0KGgo=",
    )
    assert resp.analysis.summary == "Urban area"
    assert resp.analysis.confidence == Confidence.high
    assert resp.image_metadata.cloud_cover == 15.0
    assert resp.image_metadata.platform == "Sentinel-2B"
    assert resp.image_metadata.source == "Microsoft Planetary Computer"
    assert resp.image_base64 == "iVBORw0KGgo="


def test_query_response_requires_image_metadata():
    with pytest.raises(ValidationError):
        QueryResponse(
            lat=0,
            lon=0,
            question="test",
            analysis=AnalysisResult(summary="s", detail="d", confidence=Confidence.low),
            image_base64="",
        )


def test_place_result_valid():
    result = PlaceResult(
        name="Kigali",
        display_name="Kigali, Rwanda",
        latitude=-1.9441,
        longitude=30.0619,
        type="city",
        bounding_box=[-2.1, -1.8, 29.9, 30.2],
    )
    assert result.name == "Kigali"
