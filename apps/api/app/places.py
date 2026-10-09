import asyncio
import time

import httpx

from app.config import settings
from app.models import PlaceResult

_cache: dict[str, tuple[float, list[PlaceResult]]] = {}
_reverse_cache: dict[str, tuple[float, PlaceResult | None]] = {}
_last_request_at = 0.0
_lock = asyncio.Lock()


def _normalize_place(raw: dict) -> PlaceResult:
    bounding_box = None
    if raw.get("boundingbox"):
        bounding_box = [float(value) for value in raw["boundingbox"]]

    name = raw.get("name") or raw.get("display_name", "").split(",", 1)[0]
    place_type = raw.get("type") or raw.get("class") or "place"
    return PlaceResult(
        name=name,
        display_name=raw["display_name"],
        latitude=float(raw["lat"]),
        longitude=float(raw["lon"]),
        type=place_type,
        bounding_box=bounding_box,
    )


async def search_place(query: str) -> list[PlaceResult]:
    if settings.place_search_provider != "nominatim":
        raise ValueError(f"Unsupported place search provider '{settings.place_search_provider}'.")

    normalized_query = " ".join(query.strip().split())
    if not normalized_query:
        return []

    cached = _cache.get(normalized_query.lower())
    now = time.monotonic()
    if cached and now - cached[0] <= settings.place_search_cache_ttl_s:
        return cached[1]

    global _last_request_at
    async with _lock:
        wait_s = settings.place_search_min_interval_s - (time.monotonic() - _last_request_at)
        if wait_s > 0:
            await asyncio.sleep(wait_s)

        params = {
            "q": normalized_query,
            "format": "jsonv2",
            "limit": 5,
            "addressdetails": 0,
        }
        headers = {
            "User-Agent": settings.place_search_user_agent,
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=settings.place_search_timeout_s) as client:
            response = await client.get(settings.place_search_url, params=params, headers=headers)
            response.raise_for_status()
        _last_request_at = time.monotonic()

    results = [_normalize_place(item) for item in response.json()]
    _cache[normalized_query.lower()] = (time.monotonic(), results)
    return results


async def reverse_geocode(lat: float, lon: float) -> PlaceResult | None:
    """Return a place name for a coordinate, or None for open ocean / polar areas.

    Uses the same Nominatim rate-limit lock as search_place to respect the
    1 req/s ToS. Cache key is rounded to 4 d.p. (~11m grid) for useful hits.
    """
    if settings.place_search_provider != "nominatim":
        raise ValueError(f"Unsupported place search provider '{settings.place_search_provider}'.")

    # Round to 4 decimal places for cache key (~11m precision)
    cache_key = f"{round(lat, 4)},{round(lon, 4)}"
    cached = _reverse_cache.get(cache_key)
    now = time.monotonic()
    if cached and now - cached[0] <= settings.place_search_cache_ttl_s:
        return cached[1]

    global _last_request_at
    async with _lock:
        wait_s = settings.place_search_min_interval_s - (time.monotonic() - _last_request_at)
        if wait_s > 0:
            await asyncio.sleep(wait_s)

        base_url = settings.place_search_url.replace("/search", "/reverse")
        params = {
            "lat": lat,
            "lon": lon,
            "format": "jsonv2",
            "zoom": 10,          # city/town granularity
            "addressdetails": 0,
        }
        headers = {
            "User-Agent": settings.place_search_user_agent,
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=settings.place_search_timeout_s) as client:
            response = await client.get(base_url, params=params, headers=headers)
            response.raise_for_status()
        _last_request_at = time.monotonic()

    data = response.json()
    # Nominatim returns {"error": "Unable to geocode"} for ocean / no result
    if "error" in data or "display_name" not in data:
        result = None
    else:
        result = _normalize_place(data)

    _reverse_cache[cache_key] = (time.monotonic(), result)
    return result
