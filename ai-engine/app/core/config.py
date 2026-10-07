from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ProviderName = Literal[
    "rule_based",
    "local",
    "cloud",
]


class Settings(BaseSettings):
    """
    Runtime configuration for the CareerIQ AI Engine.

    Values can be supplied through environment
    variables or an optional local .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    ai_provider: ProviderName = "rule_based"

    ai_model: str = "rule-based-v1"

    ai_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
    )

    ai_max_retries: int = Field(
        default=2,
        ge=0,
        le=10,
    )

    ai_retry_backoff_seconds: float = Field(
        default=0.5,
        ge=0,
        le=60,
    )

    ai_fallback_enabled: bool = True

    ai_fallback_provider: ProviderName = "rule_based"

    ai_base_url: str = "http://localhost:11434"

    ai_request_path: str = "/api/chat"


@lru_cache
def get_settings() -> Settings:
    return Settings()
