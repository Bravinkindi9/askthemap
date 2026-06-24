from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str = ""
    cors_origins: list[str] = ["http://localhost:3000"]
    max_cloud_cover: int = 30
    image_size_px: int = 512
    stac_api_url: str = "https://planetarycomputer.microsoft.com/api/stac/v1"

    model_config = {"env_file": ".env", "env_prefix": "ATM_"}


settings = Settings()
