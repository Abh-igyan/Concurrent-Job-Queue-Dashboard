from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="CJQD_")

    app_name: str = "Concurrent Job Queue Dashboard"
    environment: str = "development"
    log_level: str = "INFO"

    worker_count: int = 4
    queue_capacity: int = 128
    enqueue_timeout_seconds: float = 2.0
    retry_delay_seconds: float = 1.0
    default_max_retries: int = 2
    metrics_interval_seconds: float = 1.0
    history_limit: int = 256

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
