import logging

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import ImageMetadata, QueryRequest, QueryResponse
from app.vlm import get_vlm
from geo import fetch_image, search_imagery

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/api/query", response_model=QueryResponse)
async def ask_about_location(req: QueryRequest):
    result = await search_imagery(
        lat=req.lat,
        lon=req.lon,
        max_cloud_cover=settings.max_cloud_cover,
        stac_api_url=settings.stac_api_url,
    )
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No recent satellite imagery found for this location.",
        )

    image = await fetch_image(
        asset_href=result["asset_href"],
        lat=req.lat,
        lon=req.lon,
        size_px=settings.image_size_px,
    )

    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=503,
            detail="VLM API key not configured. Set ATM_GEMINI_API_KEY.",
        )

    try:
        vlm = get_vlm()
        answer = await vlm.ask(
            image=image,
            question=req.question,
            lat=req.lat,
            lon=req.lon,
        )
    except Exception as exc:
        logger.exception("VLM call failed")
        raise HTTPException(status_code=502, detail=f"AI model error: {exc}")

    return QueryResponse(
        answer=answer,
        lat=req.lat,
        lon=req.lon,
        question=req.question,
        image_metadata=ImageMetadata(
            datetime=result["datetime"],
            cloud_cover=result.get("cloud_cover"),
            collection=result["collection"],
            asset_href=result["asset_href"],
        ),
    )
