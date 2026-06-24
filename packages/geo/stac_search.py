import asyncio
from datetime import datetime, timedelta, timezone

import planetary_computer
import pystac_client


def _search_sync(
    lat: float,
    lon: float,
    max_cloud_cover: int = 30,
    stac_api_url: str = "https://planetarycomputer.microsoft.com/api/stac/v1",
) -> dict | None:
    catalog = pystac_client.Client.open(
        stac_api_url,
        modifier=planetary_computer.sign_inplace,
    )

    now = datetime.now(timezone.utc)
    six_months_ago = now - timedelta(days=180)
    date_range = f"{six_months_ago.strftime('%Y-%m-%d')}/{now.strftime('%Y-%m-%d')}"

    search = catalog.search(
        collections=["sentinel-2-l2a"],
        intersects={"type": "Point", "coordinates": [lon, lat]},
        datetime=date_range,
        query={"eo:cloud_cover": {"lt": max_cloud_cover}},
        sortby=["-properties.datetime"],
        max_items=1,
    )

    items = list(search.items())
    if not items:
        return None

    item = items[0]
    visual_asset = item.assets.get("visual")
    if visual_asset is None:
        return None

    return {
        "datetime": item.properties.get("datetime", ""),
        "cloud_cover": item.properties.get("eo:cloud_cover"),
        "collection": "sentinel-2-l2a",
        "asset_href": visual_asset.href,
    }


async def search_imagery(
    lat: float,
    lon: float,
    max_cloud_cover: int = 30,
    stac_api_url: str = "https://planetarycomputer.microsoft.com/api/stac/v1",
) -> dict | None:
    return await asyncio.to_thread(
        _search_sync, lat, lon, max_cloud_cover, stac_api_url
    )
