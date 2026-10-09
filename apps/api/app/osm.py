"""Small, cached Overpass queries for nearby OpenStreetMap feature counts."""
import asyncio
import time

import httpx

from app.config import settings

_cache: dict[tuple[float, float, int], tuple[float, dict[str, int]]] = {}
_lock = asyncio.Lock()
_last_request_at = 0.0

FEATURES = {
    "roads": '[highway]',
    "buildings": '[building]',
    "amenities": '[amenity]',
    "water features": '["natural"="water"]',
}


async def nearby_feature_counts(lat: float, lon: float) -> dict[str, int]:
    """Count mapped OSM elements by category inside the configured radius."""
    global _last_request_at
    radius = settings.overpass_radius_m
    key = (round(lat, 4), round(lon, 4), radius)
    now = time.monotonic()
    cached = _cache.get(key)
    if cached and now - cached[0] < settings.overpass_cache_ttl_s:
        return cached[1]

    async with _lock:
        now = time.monotonic()
        cached = _cache.get(key)
        if cached and now - cached[0] < settings.overpass_cache_ttl_s:
            return cached[1]
        wait = 1.0 - (now - _last_request_at)
        if wait > 0:
            await asyncio.sleep(wait)

        statements = []
        for selector in FEATURES.values():
            statements.append(
                f"nwr(around:{radius},{lat:.6f},{lon:.6f}){selector};\nout count;"
            )
        query = f"[out:json][timeout:20];\n" + "\n".join(statements)
        async with httpx.AsyncClient(timeout=settings.overpass_timeout_s) as client:
            response = await client.post(settings.overpass_api_url, data={"data": query})
            _last_request_at = time.monotonic()
            response.raise_for_status()
        elements = response.json().get("elements", [])
        count_rows = [row for row in elements if row.get("type") == "count"]
        if len(count_rows) != len(FEATURES):
            raise ValueError("Overpass returned an unexpected count response")

        counts = {
            label: int(row.get("tags", {}).get("total", 0))
            for label, row in zip(FEATURES, count_rows)
        }
        if len(_cache) >= 2048:
            _cache.pop(next(iter(_cache)))
        _cache[key] = (time.monotonic(), counts)
        return counts
