import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.models import PlaceResult
from app.places import reverse_geocode, search_place

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/places/search", response_model=list[PlaceResult])
async def search_places(q: str = Query(..., min_length=2, max_length=120)):
    try:
        return await search_place(q)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception:
        logger.exception("Place search failed")
        raise HTTPException(status_code=502, detail="Place search failed. Please try again.")


@router.get("/api/places/reverse", response_model=PlaceResult | None)
async def reverse_geocode_point(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    """Return a human-readable place name for a coordinate.
    Returns null (JSON) when no result exists (ocean, polar areas).
    """
    try:
        result = await reverse_geocode(lat, lon)
        if result is None:
            return JSONResponse(content=None, status_code=200)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception:
        logger.exception("Reverse geocode failed for lat=%s lon=%s", lat, lon)
        # Best-effort — return null rather than erroring, the frontend degrades gracefully
        return JSONResponse(content=None, status_code=200)
