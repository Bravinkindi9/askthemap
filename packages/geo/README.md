# geo

Geospatial module for AskTheMap. Handles satellite imagery search and retrieval from Microsoft Planetary Computer.

## Modules

- `stac_search.py` — searches the STAC catalog for Sentinel-2 L2A imagery at a
  given coordinate, returning acquisition metadata (datetime, cloud cover,
  platform, instrument, resolution) alongside the asset href
- `image_retrieval.py` — downloads a windowed tile from a Cloud-Optimized GeoTIFF
  and returns it as a PIL Image. The crop window is clamped to the raster's
  bounds on every side, so points near a tile edge still return a full-size,
  undistorted crop instead of a silently truncated one.

Both functions accept a `timeout_s` parameter enforced at the underlying
HTTP/GDAL client level (not just at the asyncio layer by the caller), since a
blocking network call bridged via `asyncio.to_thread` can't otherwise be
cancelled once it's started.

## Usage

```python
from geo import search_imagery, fetch_image

result = await search_imagery(lat=-1.9403, lon=29.8739, timeout_s=20.0)
image = await fetch_image(result["asset_href"], lat=-1.9403, lon=29.8739, timeout_s=45.0)
```

This module is imported by `apps/api` via sys.path — it is not a standalone pip package.
