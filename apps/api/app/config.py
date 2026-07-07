from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    cors_origins: list[str] = ["http://localhost:3000"]
    max_cloud_cover: int = 30
    image_size_px: int = 512
    stac_api_url: str = "https://planetarycomputer.microsoft.com/api/stac/v1"

    # Per-stage timeouts (seconds) for external services. Each is enforced both
    # at the underlying HTTP/GDAL client level and as an asyncio.wait_for backstop
    # in the query pipeline, since cancelling an in-flight thread-bridged call is
    # not otherwise possible. The library-level timeout is per HTTP request, while
    # a single stage can involve several requests (e.g. STAC catalog open + search,
    # or GDAL's metadata read + windowed range read), so these are set with headroom
    # above a single request's cost, not equal to it. Measured against real Planetary
    # Computer / Azure Blob latency during development: STAC search ~11s, windowed
    # COG read ~37s on a typical residential connection.
    stac_timeout_s: float = 20.0
    image_fetch_timeout_s: float = 45.0
    vlm_timeout_s: float = 30.0

    model_config = {"env_file": ".env", "env_prefix": "ATM_"}


settings = Settings()
