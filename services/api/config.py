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

    # API authentication (PLAN-0047 Step 1, SD-1 = (a) static per-person API keys)
    api_auth_enabled: bool = Field(
        default=True,
        description=(
            "Require a bearer API key on every state-changing route (approve/"
            "execute, /warm, /sleep, /intake/generate, and the PLAN-0047 run/"
            "gate-resolve endpoints). Fail-closed default; set false only on a "
            "local dev/demo box that deliberately wants the pre-authn behavior."
        ),
    )
    api_keys: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "SHA-256 hex digest of a raw bearer API key -> the person_id it "
            "authenticates. Digests only — raw keys are never stored. Provision "
            'via the API_KEYS env var as JSON, e.g. {"<sha256-hex>": "appr-x"} '
            "(.env.example documents a key-generation one-liner)."
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
    verification_judge_enabled: bool = Field(
        default=False,
        description=(
            "PLAN-0035 Phase 2 / ADR-0022 amendment — enable the ADVISORY local-LLM "
            "action-verification judge (member (b)). When False (default), recommend() "
            "runs the deterministic floor alone (verification_mode '(a)-only'), "
            "byte-identical to Phase 1. When True, the advisory judge adds a confidence + "
            "agreement signal and a 'hybrid' trace; it NEVER overrides the surfaced action "
            "(constraint ②) and degrades to '(a)-only' disclosed when MS-S1 is unreachable "
            "(constraint ④). Default off because a live judge run is host-state — "
            "Cray-gated (CLAUDE.md §8); the offline acceptance gate fakes the judge."
        ),
    )
    event_bridge_enabled: bool = Field(
        default=False,
        description=(
            "PLAN-0056 Phase B / ADR-0029 — enable the event-trigger bridge (SD-P3 ship-dark). "
            "When False (default), an actionable recommendation follows only the existing "
            "ActionRecord approve/execute path — byte-identical to before the bridge shipped. "
            "When True, an actionable recommendation whose suggested_handler maps to an "
            "event-trigger procedure in the active vertical is ALSO FED INTO the governed engine "
            "in-process (ADR-0029 SD-1/SD-4) — a real governed PipelineRun that parks at any gate. "
            "Default off because it changes the recommender's action semantics for the deployment "
            "(a blast-radius / rollout-posture call); the ActionRecord path is untouched when off."
        ),
    )
    handler_catalog_enabled: bool = Field(
        default=True,
        description=(
            "PLAN-0060 — surface per-handler descriptions (an 'Available actions' catalog) into "
            "the REACTIVE recommender judgment prompt so the model distinguishes handlers by "
            "meaning (e.g. emergency_source vs reorder) instead of bare name. When True, the "
            "vertical's registry.handler_catalog rides in the trusted system instruction of every "
            "reasoning/structuring call; the suggested_handler enum is unchanged either way. When "
            "False, the reactive prompt is byte-identical to before — names only (AC-4). "
            "Default flipped to True after the PLAN-0060 AC-7 live re-validate PASSED (2026-07-09, "
            "docs/logs/2026-07-09-reactive-handler-catalog-live-revalidate.md): the real MS-S1 "
            "gpt-oss:20b picked emergency_source with the catalog on vs reorder off, for the "
            "session-114 CNC line-down event. The GOVERNED procedure path is untouched (out of "
            "scope) — it threads no catalog."
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
    oct_demo_seed_operate: bool = Field(
        default=False,
        description=(
            "When True (env OCT_DEMO_SEED_OPERATE) AND the active vertical is "
            "procurement, seed ONE waiting_human 'emergency_sourcing_round' run at "
            "startup so the Control-leg operate demo (View H) has a real gate to "
            "act on (PLAN-0054 Step 6). Idempotent (a fixed demo run_id, skipped if "
            "present) + fail-soft (a seed error logs, never blocks boot). Off by "
            "default so no non-demo startup writes to the DB."
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
