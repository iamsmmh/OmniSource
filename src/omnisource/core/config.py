"""Runtime configuration, sourced from the environment with safe defaults."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven settings (prefix ``OMNISOURCE_``)."""

    model_config = SettingsConfigDict(
        env_prefix="OMNISOURCE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "OmniSource"
    environment: str = "development"
    log_level: str = "INFO"

    # Engine
    provider_timeout: float = Field(
        default=3.0, gt=0, description="Per-provider deadline, seconds."
    )
    max_concurrency: int = Field(default=32, gt=0, description="Max parallel provider calls.")
    max_items: int = Field(default=100, gt=0, description="Cap on aggregated items returned.")

    # Cache
    redis_url: str = "redis://localhost:6379/0"
    cache_enabled: bool = True
    cache_ttl: int = Field(default=300, ge=0, description="Default cache TTL, seconds.")
    cache_namespace: str = "omnisource"

    # API
    host: str = "0.0.0.0"
    port: int = 8000


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""
    return Settings()
