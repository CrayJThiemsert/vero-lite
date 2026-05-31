"""Application configuration via environment variables."""

from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


def _derive_test_database_url(database_url: str) -> str:
    """Derive a sibling ``<db>_test`` URL from the main database URL.

    Only the database name changes — same driver / host / port /
    credentials — so the test DB lands on the same Postgres server the dev
    DB uses (ADR-003 port hygiene) while never pointing at the dev DB
    itself. The disposable test suite owns ``<db>_test`` exclusively, so its
    create_all / drop_all teardown can never wipe the dev/demo schema (see
    project memory ``project_test_suite_drops_demo_db``).
    """
    url = make_url(database_url)
    base_name = url.database or "vero_lite"
    # render_as_string(hide_password=False): str(URL) masks the password as
    # "***", which would corrupt the connection string for the test engine.
    return url.set(database=f"{base_name}_test").render_as_string(hide_password=False)


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
    test_database_url: str = Field(
        default="",
        description=(
            "Disposable database the test suite owns exclusively. Left blank "
            "it is derived as <db>_test from database_url; set TEST_DATABASE_URL "
            "to override. Must never equal database_url — the suite drops its "
            "schema on teardown (project memory project_test_suite_drops_demo_db)."
        ),
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

    # OCT demo — active vertical + recommender policy (PLAN-0013 AC-template).
    # Only ONE vertical runs per process, so the policy is a flat set of
    # env-driven settings, NOT a per-vertical map or framework (Rule-of-Three:
    # a data-driven 2nd instance, not premature abstraction — CLAUDE.md §1).
    # Every default reproduces the energy vertical exactly, so swapping
    # OCT_VERTICAL (+ a few OCT_RECOMMEND_* values) is the only change needed to
    # re-skin the demo onto a different ontology with zero UI-code change.
    oct_vertical: str = Field(
        default="energy",
        description=(
            "Active OCT vertical — the adapter + handlers registered on startup "
            "and the vertical the routers serve (e.g. 'energy' | 'supply_chain')"
        ),
    )
    oct_recommend_threshold: float = Field(
        default=90.0,
        description=(
            "measured_value at or above which a 'reading' event escalates to a "
            "RecommendedAction (energy over-temp = 90 °C; a cold-chain breach is "
            "lower). Supersedes the energy-only OVERTEMP_THRESHOLD_CELSIUS at runtime."
        ),
    )
    oct_recommend_entity_type: str = Field(
        default="Asset",
        description=(
            "Ontology object_type the deterministic fail-safe rule names as the "
            "affected entity (energy 'Asset'; supply_chain e.g. 'Shipment')"
        ),
    )
    oct_recommend_entity_id_field: str = Field(
        default="asset_id",
        description=(
            "Event field holding the affected entity's primary key, read by the "
            "fail-safe rule (energy 'asset_id'; supply_chain e.g. 'shipment_id')"
        ),
    )
    oct_recommend_label: str = Field(
        default="over-temperature",
        description=(
            "Short anomaly label used in the deterministic fail-safe rule's "
            "title/description (energy 'over-temperature'; supply_chain e.g. "
            "'cold-chain temperature breach')"
        ),
    )

    # App
    log_level: str = Field(default="INFO", description="Python logging level")
    environment: str = Field(default="development", description="Deployment environment name")

    @model_validator(mode="after")
    def _fill_test_database_url(self) -> Self:
        """Default test_database_url to the derived ``<db>_test`` when blank."""
        if not self.test_database_url:
            self.test_database_url = _derive_test_database_url(self.database_url)
        return self


settings = Settings()
