import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

from geo.image_retrieval import _fetch_sync

RASTER_SIZE = 50


def _make_test_raster(memfile: MemoryFile) -> None:
    transform = from_origin(west=0, north=RASTER_SIZE, xsize=1, ysize=1)
    with memfile.open(
        driver="GTiff",
        width=RASTER_SIZE,
        height=RASTER_SIZE,
        count=3,
        dtype="uint8",
        crs="EPSG:4326",
        transform=transform,
    ) as dataset:
        data = np.random.randint(0, 255, (3, RASTER_SIZE, RASTER_SIZE), dtype="uint8")
        dataset.write(data)


def test_fetch_sync_clamps_window_near_far_corner():
    """A point near the raster's far edge should still yield a full-size crop.

    Regression test: the crop window was only clamped against the raster's
    lower bound (col_off/row_off >= 0), not its upper bound, so points near
    the opposite edge produced a window that read past the raster extent and
    silently returned a smaller-than-requested image.
    """
    with MemoryFile() as memfile:
        _make_test_raster(memfile)
        # Near the bottom-right corner of the raster (col~49, row~49).
        img = _fetch_sync(memfile.name, lat=0.5, lon=49.5, size_px=20, timeout_s=5.0)
        assert img.size == (20, 20)


def test_fetch_sync_clamps_window_near_origin():
    with MemoryFile() as memfile:
        _make_test_raster(memfile)
        # Near the top-left corner of the raster (col~0, row~0).
        img = _fetch_sync(memfile.name, lat=49.5, lon=0.5, size_px=20, timeout_s=5.0)
        assert img.size == (20, 20)


def test_fetch_sync_center_point():
    with MemoryFile() as memfile:
        _make_test_raster(memfile)
        img = _fetch_sync(memfile.name, lat=25.0, lon=25.0, size_px=20, timeout_s=5.0)
        assert img.size == (20, 20)
