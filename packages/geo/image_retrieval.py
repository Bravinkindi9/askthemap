import asyncio

import numpy as np
import rasterio
from PIL import Image
from rasterio.warp import transform


def _fetch_sync(
    asset_href: str,
    lat: float,
    lon: float,
    size_px: int = 512,
) -> Image.Image:
    with rasterio.open(asset_href) as src:
        xs, ys = transform("EPSG:4326", src.crs, [lon], [lat])
        col, row = ~src.transform * (xs[0], ys[0])
        col, row = int(col), int(row)

        half = size_px // 2
        window = rasterio.windows.Window(
            col_off=max(0, col - half),
            row_off=max(0, row - half),
            width=size_px,
            height=size_px,
        )

        data = src.read([1, 2, 3], window=window)

    data = np.clip(data, 0, 3000)
    data = ((data / 3000) * 255).astype(np.uint8)

    img = Image.fromarray(np.transpose(data, (1, 2, 0)), mode="RGB")
    return img


async def fetch_image(
    asset_href: str,
    lat: float,
    lon: float,
    size_px: int = 512,
) -> Image.Image:
    return await asyncio.to_thread(_fetch_sync, asset_href, lat, lon, size_px)
