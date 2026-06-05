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
    llm_status_timeout_s: float = Field(
        default=3.0,
        gt=0.0,
        description=(
            "Short, dedicated timeout for the read-only GET /llm/status residency "
            "probe (PLAN-0018 AC-5) — decoupled from llm_request_timeout_s so a "
            "slow/half-down MS-S1 degrades the poll fast instead of hanging for a "
            "generation-length window per poll"
        ),
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
    oct_recommend_direction: str = Field(
        default="above",
        description=(
            "Direction a 'reading' must breach oct_recommend_threshold to escalate: "
            "'above' (measured >= threshold — energy over-temp, the default) or "
            "'below' (measured <= threshold — e.g. an aquaculture dissolved-oxygen "
            "crash). Read by the recommender trigger, the fail-safe rule, and the "
            "demo-anchor breach selector (PLAN-0016 Step 0). Default 'above' "
            "preserves the energy + supply_chain verticals exactly."
        ),
    )

    # OCT live-time demo loop (PLAN-0015). The anchor flag is OFF by default so
    # synthetic.py stays deterministic for tests (D5); the demo box sets
    # OCT_DEMO_TIME_ANCHOR=true so each uvicorn run anchors the incident to real
    # time (breach ~= server start). The recovery value/description are the
    # safe-range reading injected as the effect of Execute (D2) — energy
    # defaults; a second vertical overrides them via env (PLAN-0013 AC-template).
    oct_demo_time_anchor: bool = Field(
        default=False,
        description=(
            "When True (env OCT_DEMO_TIME_ANCHOR), shift the active vertical's "
            "OperationalEvent timestamps each server run so the breach ~= server "
            "start, preserving relative spacing (PLAN-0015 D1). Default off keeps "
            "the fixed synthetic datetimes so tests stay deterministic (D5)."
        ),
    )
    oct_recovery_value: float = Field(
        default=58.0,
        description=(
            "Safe-range measured_value for the recovery reading injected as the "
            "effect of Execute (PLAN-0015 D2; env OCT_RECOVERY_VALUE). Energy "
            "58 °C; a cold-chain vertical sets e.g. 4.0."
        ),
    )
    oct_recovery_description: str = Field(
        default="Battery Bank A temperature returning to the safe range.",
        description=(
            "Description on the injected recovery reading (PLAN-0015 D2; env "
            "OCT_RECOVERY_DESCRIPTION). Energy default; overridden per vertical."
        ),
    )

    # Telegram notify + LLM warm control (PLAN-0014). The notifier pings the
    # operator when an OCT local-LLM call fails because MS-S1 is unreachable;
    # the /warm + /sleep routes load/unload the model. Tokens come from env
    # ONLY (CLAUDE.md §8) and the notifier no-ops gracefully when unset or the
    # flag is off. Reuses the existing harness bot/chat (ADR-013 D5).
    telegram_bot_token: str = Field(
        default="",
        description=(
            "Telegram bot API token (env TELEGRAM_BOT_TOKEN) — reuses the existing "
            "harness bot; from env only, never committed (CLAUDE.md §8)"
        ),
    )
    telegram_chat_id: str = Field(
        default="",
        description="Telegram destination chat id (env TELEGRAM_CHAT_ID) — reuses the harness chat",
    )
    telegram_notify_enabled: bool = Field(
        default=False,
        description=(
            "Master switch for the MS-S1-unreachable Telegram ping "
            "(env TELEGRAM_NOTIFY_ENABLED); default off so dev sessions get no pings"
        ),
    )
    telegram_notify_cooldown_s: float = Field(
        default=600.0,
        gt=0.0,
        description=(
            "Minimum seconds between MS-S1-unreachable pings — debounces UI polling "
            "(env TELEGRAM_NOTIFY_COOLDOWN_S)"
        ),
    )
    ollama_keep_alive: str = Field(
        default="30m",
        description=(
            "How long a warmed model stays resident in MS-S1 VRAM (Ollama keep_alive; "
            "env OLLAMA_KEEP_ALIVE) — also used by the /warm route + the ping's warm one-liner"
        ),
    )
    oct_public_base_url: str = Field(
        default="",
        description=(
            "Externally reachable base URL of the demo box (env OCT_PUBLIC_BASE_URL); "
            "when set, the Telegram ping appends a tap-link to {base}/warm"
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
