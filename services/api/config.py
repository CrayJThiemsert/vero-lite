"""Application configuration via environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://vero:vero@localhost:5432/vero_lite",
        description="PostgreSQL connection string (asyncpg driver)",
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string for Celery broker + cache",
    )

    # LLM
    ollama_host: str = Field(
        default="http://ms-s1-max:11434",
        description="Ollama API endpoint (use http://localhost:11434 for local dev)",
    )
    ollama_default_model: str = Field(
        default="gemma4:26b",
        description="Default LLM model — see ADR-001 (digest 5571076f3d70)",
    )

    # LLM reasoning hook (PLAN-0006 / ADR-010)
    llm_backend: str = Field(
        default="local",
        description=(
            "Reasoning-hook backend selector — 'local' (Ollama on MS-S1 MAX, "
            "ADR-010 D1 default) or 'hosted' (Claude API fallback, seam-only / "
            "stubbed per PLAN-0006 SD-5)"
        ),
    )
    recommender_model: str = Field(
        default="gpt-oss:20b",
        description=(
            "Model for the recommender LLM path — pinned by PLAN-0006 "
            "CHECKPOINT-0 (ADR-010 IN-1 verification, Ollama 0.24.0); "
            "supersedes the ADR-001 gemma4:26b baseline for this path "
            "(see ADR-001 amendment)"
        ),
    )
    llm_retry_budget: int = Field(
        default=3,
        ge=1,
        description=(
            "Total structured-output attempts on the LLM path — 1 initial "
            "plus retries (PLAN-0006 SD-1; default 3)"
        ),
    )
    llm_request_timeout_s: float = Field(
        default=120.0,
        gt=0.0,
        description="Per-request timeout for a single Ollama chat call, in seconds",
    )

    # App
    log_level: str = Field(default="INFO", description="Python logging level")
    environment: str = Field(default="development", description="Deployment environment name")


settings = Settings()
