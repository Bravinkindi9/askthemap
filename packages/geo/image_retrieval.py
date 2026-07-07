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
    timeout_s: float = 15.0,
) -> Image.Image:
    gdal_timeout = str(int(timeout_s))
    with rasterio.Env(GDAL_HTTP_TIMEOUT=gdal_timeout, GDAL_HTTP_CONNECTTIMEOUT=gdal_timeout):
        with rasterio.open(asset_href) as src:
            xs, ys = transform("EPSG:4326", src.crs, [lon], [lat])
            col, row = ~src.transform * (xs[0], ys[0])
            col, row = int(col), int(row)

            half = size_px // 2
            width = min(size_px, src.width)
            height = min(size_px, src.height)
            col_off = max(0, min(col - half, src.width - width))
            row_off = max(0, min(row - half, src.height - height))

            window = rasterio.windows.Window(
                col_off=col_off,
                row_off=row_off,
                width=width,
                height=height,
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
    timeout_s: float = 15.0,
) -> Image.Image:
    return await asyncio.to_thread(_fetch_sync, asset_href, lat, lon, size_px, timeout_s)
