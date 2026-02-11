"""Core configuration for the Economy Tracker backend."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Database
    database_url: str = "postgresql://tracker_user:change_this_password@postgres:5432/economy_tracker"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "economy_tracker"
    postgres_user: str = "tracker_user"
    postgres_password: str = "change_this_password"

    # Redis
    redis_url: str = "redis://redis:6379/0"
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: Optional[str] = None

    # API Keys
    fred_api_key: Optional[str] = None
    world_bank_api_base: str = "https://api.worldbank.org/v2"
    oecd_api_base: str = "https://sdmx.oecd.org/public/rest/data"

    # Backend
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_reload: bool = True
    log_level: str = "info"

    # Feature Flags
    enable_llm_insights: bool = False
    enable_timescaledb: bool = True
    demo_mode: bool = False

    # Ingestion
    ingestion_schedule: str = "0 6 * * *"

    # Cache TTL
    cache_ttl_indicators: int = 3600
    cache_ttl_observations: int = 1800
    cache_ttl_insights: int = 900

    # Rate Limiting
    fred_rate_limit_calls: int = 120
    fred_rate_limit_period: int = 60
    world_bank_rate_limit_calls: int = 100
    world_bank_rate_limit_period: int = 60
    oecd_rate_limit_calls: int = 100
    oecd_rate_limit_period: int = 60

    # Retry Configuration
    max_retry_attempts: int = 3
    retry_backoff_factor: int = 2
    retry_initial_delay: int = 1


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
