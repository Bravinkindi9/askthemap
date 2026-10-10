from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Which BaseVLM/BaseTextLLM implementation to use. "gemini" or "openrouter".
    vlm_provider: str = "gemini"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    # Text-only model for geographic questions (same provider, same key)
    text_model_gemini: str = "gemini-2.5-flash"

    openrouter_api_key: str = ""
    openrouter_model: str = "qwen/qwen2.5-vl-7b-instruct:free"
    # Text-only model for geographic questions (free tier, better at instruction-following)
    text_model_openrouter: str = "qwen/qwen2.5-72b-instruct:free"

    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
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
    max_request_body_bytes: int = 8_192
    rate_limit_requests: int = 30
    rate_limit_window_s: float = 60.0
    query_concurrency_limit: int = 2

    place_search_provider: str = "nominatim"
    place_search_url: str = "https://nominatim.openstreetmap.org/search"
    place_search_user_agent: str = "AskioV1/0.1 (personal portfolio project)"
    place_search_timeout_s: float = 8.0
    place_search_min_interval_s: float = 1.0
    place_search_cache_ttl_s: float = 86400.0

    overpass_api_url: str = "https://overpass-api.de/api/interpreter"
    overpass_timeout_s: float = 25.0
    overpass_radius_m: int = 500
    overpass_cache_ttl_s: float = 900.0

    model_config = {"env_file": ".env", "env_prefix": "ATM_"}


settings = Settings()
