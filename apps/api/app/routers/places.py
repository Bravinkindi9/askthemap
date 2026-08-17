import logging

from fastapi import APIRouter, HTTPException, Query

from app.models import PlaceResult
from app.places import search_place

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
