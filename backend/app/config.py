from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    backend_port: int = 8000
    secret_key: str = "changeme"
    log_level: str = "INFO"

    database_url: str = "sqlite+aiosqlite:///./controlplane.db"
    sync_database_url: str = "sqlite:///./controlplane.db"
    redis_url: str = "redis://localhost:6379/0"

    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    enable_demo_mode: bool = True
    enable_websockets: bool = True
    enable_deep_checks: bool = True
    enable_llm_judge: bool = False

    default_latency_budget_ms: int = 700
    default_expected_cost_inr: float = 0.20

    pii_engine: str = "regex"

    # Risk thresholds
    risk_low_threshold: float = 0.25
    risk_medium_threshold: float = 0.50
    risk_high_threshold: float = 0.75

    # Cost thresholds
    cost_multiplier_medium: float = 2.0
    cost_multiplier_high: float = 4.0
    max_tool_calls_default: int = 5
    max_retries_default: int = 2


@lru_cache
def get_settings() -> Settings:
    return Settings()
