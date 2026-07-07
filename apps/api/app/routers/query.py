import asyncio
import base64
import io
import logging
from typing import Awaitable, TypeVar

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import ImageMetadata, QueryRequest, QueryResponse
from app.vlm import get_vlm
from geo import fetch_image, search_imagery

router = APIRouter()
logger = logging.getLogger(__name__)

T = TypeVar("T")


async def _run_stage(
    awaitable: Awaitable[T],
    *,
    stage: str,
    timeout_s: float,
    timeout_detail: str,
    error_detail: str,
) -> T:
    """Run one pipeline stage with a bounded wait and a user-safe error message.

    The timeout here is a backstop, not the primary defense: cancelling a
    thread-bridged blocking call (rasterio/GDAL, requests) isn't possible from
    asyncio, so the real timeout enforcement happens in the underlying client
    (GDAL_HTTP_TIMEOUT, pystac_client's timeout, Gemini's http_options). This
    wrapper guarantees the user gets a response within a bounded time and never
    sees raw exception internals.
    """
    try:
        return await asyncio.wait_for(awaitable, timeout=timeout_s)
    except asyncio.TimeoutError:
        logger.warning("Stage '%s' timed out after %.1fs", stage, timeout_s)
        raise HTTPException(status_code=504, detail=timeout_detail)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Stage '%s' failed", stage)
        raise HTTPException(status_code=502, detail=error_detail)


@router.post("/api/query", response_model=QueryResponse)
async def ask_about_location(req: QueryRequest):
    result = await _run_stage(
        search_imagery(
            lat=req.lat,
            lon=req.lon,
            max_cloud_cover=settings.max_cloud_cover,
            stac_api_url=settings.stac_api_url,
            timeout_s=settings.stac_timeout_s,
        ),
        stage="stac_search",
        timeout_s=settings.stac_timeout_s,
        timeout_detail="Searching for satellite imagery took too long. Please try again.",
        error_detail="We couldn't search for satellite imagery right now. Please try again in a moment.",
    )
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No recent, sufficiently cloud-free satellite imagery is available for this "
            "location. Try a nearby point or check back later.",
        )

    image = await _run_stage(
        fetch_image(
            asset_href=result["asset_href"],
            lat=req.lat,
            lon=req.lon,
            size_px=settings.image_size_px,
            timeout_s=settings.image_fetch_timeout_s,
        ),
        stage="image_fetch",
        timeout_s=settings.image_fetch_timeout_s,
        timeout_detail="Downloading the satellite image took too long. Please try again.",
        error_detail="We found imagery for this location but couldn't download it. Please try again.",
    )

    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=503,
            detail="VLM API key not configured. Set ATM_GEMINI_API_KEY.",
        )

    vlm = get_vlm()
    analysis = await _run_stage(
        vlm.ask(image=image, question=req.question, lat=req.lat, lon=req.lon),
        stage="vlm_analysis",
        timeout_s=settings.vlm_timeout_s,
        timeout_detail="The AI analysis took too long. Please try again.",
        error_detail="The AI analysis failed. Please try again.",
    )

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    image_base64 = base64.b64encode(buf.getvalue()).decode("ascii")

    return QueryResponse(
        lat=req.lat,
        lon=req.lon,
        question=req.question,
        analysis=analysis,
        image_metadata=ImageMetadata(
            datetime=result["datetime"],
            cloud_cover=result.get("cloud_cover"),
            collection=result["collection"],
            asset_href=result["asset_href"],
            platform=result.get("platform"),
            instrument=result.get("instrument"),
            resolution_m=result.get("resolution_m"),
        ),
        image_base64=image_base64,
    )
