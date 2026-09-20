from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.6-luna"
    database_url: str = "postgresql://bitelog:bitelog@localhost:5432/bitelog"
    redis_url: str = "redis://localhost:6379/0"

    # Optional S3-compatible storage settings. Python 3.9-compatible typing.
    s3_endpoint_url: Optional[str] = None
    s3_region: str = "us-east-1"
    s3_bucket: str = "bitelog-meals"
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""

    max_inline_image_bytes: int = 6_000_000


@lru_cache
def get_settings() -> Settings:
    return Settings()
