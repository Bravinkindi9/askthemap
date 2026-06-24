# geo

Geospatial module for AskTheMap. Handles satellite imagery search and retrieval from Microsoft Planetary Computer.

## Modules

- `stac_search.py` — searches the STAC catalog for Sentinel-2 L2A imagery at a given coordinate
- `image_retrieval.py` — downloads a windowed tile from a Cloud-Optimized GeoTIFF and returns it as a PIL Image

## Usage

```python
from geo import search_imagery, fetch_image

result = await search_imagery(lat=-1.9403, lon=29.8739)
image = await fetch_image(result["asset_href"], lat=-1.9403, lon=29.8739)
```

This module is imported by `apps/api` via sys.path — it is not a standalone pip package.
