"""Application configuration via environment variables."""

import hashlib
from typing import Literal, Self

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


#: PLAN-0103 Step 2 — the ten-tab census, server side, as KEYS ONLY.
#:
#: ``app.js``'s ``ALL_VIEWS`` stays the rendering census and stays authoritative
#: for what a tab IS: its label, its icon, and the module that mounts it are JS
#: closures with no Python representation. What lives here is only the key set,
#: because ``ui_published_views`` is parsed here and validation must happen where
#: the value is parsed — a boot refusal is worth nothing if it fires after the
#: browser has already rendered.
#:
#: That makes this a SECOND copy of a list, which is a drift hazard and is
#: therefore given a tripwire rather than a comment: a guard test parses
#: ``ALL_VIEWS`` out of ``app.js`` and asserts set-equality with this tuple, so
#: adding an eleventh tab in the browser without adding it here reddens on the
#: commit that creates the gap.
ALL_VIEW_KEYS: tuple[str, ...] = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J")


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
    # PLAN-0103 Step 6 (SD-4 ruling (b); credential path RULED (a), Cray typed
    # s224) — the persona picker's RAW demo keys, person_id -> raw key.
    #
    # 🔴 READ THIS BEFORE COPYING THE PATTERN. Every other credential in this
    # file is a digest or a pass-through the server keeps to itself. These are
    # raw keys, and on the published profile they are DELIBERATELY SERVED TO THE
    # BROWSER over /meta so a visitor can pick a persona without being handed a
    # secret to type. The consequence is intended, not overlooked: anyone can
    # read them out of the page and call the API directly as any persona — the
    # same power the picker already grants them through the UI. That is
    # acceptable ONLY because these authenticate three SYNTHETIC demo principals
    # on a synthetic dataset. A key that authenticates anything real must never
    # be put here.
    #
    # Still never in git (AC-6): provisioned host-env-local through the compose
    # bare pass-through, exactly like the database credentials.
    #
    # Empty default = the feature is OFF, which is the correct posture for every
    # system except fleet — procurement takes no personas (SD-3/SD-4) and energy
    # stays keyless.
    ui_demo_persona_keys: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "person_id -> RAW demo API key for the published persona picker. "
            "Served to the browser on the published profile by design (PLAN-0103 "
            "Step 6, credential option (a)); synthetic demo principals ONLY. "
            'Provision via UI_DEMO_PERSONA_KEYS as JSON, e.g. {"appr-owner": '
            '"<raw>"}. Empty = no picker. Every raw key here must digest to an '
            "API_KEYS entry naming the SAME person_id — validated at boot"
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

    # The tenant key (ADR-0035 D7 / PLAN-0101 Step 1). A CUSTOMER ORGANISATION —
    # not a deployment (two deployments for one customer keep one key) and not a
    # vertical instance (that is oct_vertical above; conflating them breaks the
    # moment one customer runs two verticals). Process-wide exactly like
    # oct_vertical, which is what keeps ADR-0035's L4 "light": per-request tenancy
    # would collide with the process-scoped vertical (auth.py:82) and the
    # hand-wired executor factories (main.py:103-156).
    # It is a plain settings field and is NOT part of the governance pin — it must
    # never reach the resolved-procedures hash (guarded by
    # tests/services/engine/procedures/test_tenant_key_not_in_governance_pin.py).
    tenant_id: str = Field(
        default="default",
        description=(
            "Customer-organisation slug stamped onto every persisted row "
            "(ADR-0035 D7). Defaults to 'default' so existing dev/test flows are "
            "untouched; the public demo deployment sets TENANT_ID=demo"
        ),
    )
    # PLAN-0100 Step 2 — which UI surface this process serves. "published" is the
    # public demo profile, which renders no control whose backend that deployment
    # excludes (AC-1); "dev" is today's full console and stays the default so
    # every existing flow is untouched (AC-2).
    #
    # Typed as a Literal, not a plain str, DELIBERATELY: an unrecognised value
    # must fail the process at boot rather than fall back. A silent fallback here
    # resolves the wrong way round — a typo'd UI_PROFILE on the PUBLIC deployment
    # would serve the full dev console, which is the exact exposure this PLAN
    # exists to prevent. A loud boot failure is recoverable; a quiet leak is not.
    ui_profile: Literal["dev", "published"] = Field(
        default="dev",
        description=(
            "Which UI surface to serve: 'dev' (full console, the default) or "
            "'published' (public demo — excluded-backend controls not rendered). "
            "Served to the browser two ways: injected into index.html as a "
            "<meta name='ui-profile'> tag so it is readable BEFORE the first "
            "paint, and carried on /meta as the API-visible contract"
        ),
    )
    # PLAN-0103 Step 2 — which tabs the PUBLISHED profile renders, per system.
    #
    # This replaces app.js's PUBLISHED_EXCLUDED_VIEWS, which was a client-side
    # constant naming the FIVE tabs energy drops. That shape encoded N=1: a
    # second published system with a different tab set had nowhere to say so
    # except a per-vertical branch in the browser. The set is now DECLARED by
    # the server it belongs to, per compose project.
    #
    # Stated POSITIVELY (which tabs to show) rather than as exclusions, because
    # the exclusion form only has meaning relative to a full census, and the
    # census is the one thing that legitimately differs from nobody's system to
    # nobody's system — it is fixed. A positive list also makes ORDER declarable,
    # which the exclusion form could not express, and order is load-bearing: the
    # first key is the system's default landing tab. That matters concretely —
    # procurement's Tab A is structurally blank (its adapter's stream_events is
    # an empty iterator by design), so procurement must land on G, not A.
    #
    # A comma string rather than a JSON list: this value is hand-edited per
    # system in a committed published.env, and A,B,C,D,F reads at a glance where
    # ["A","B","C","D","F"] does not. Parsed by published_view_keys.
    #
    # Ignored entirely on the dev profile, which always renders the full census.
    ui_published_views: str = Field(
        default="A,B,C,D,F",
        description=(
            "Ordered, comma-separated view keys the 'published' UI profile "
            "renders; the FIRST key is that system's default landing tab. "
            "Default is system #1 (energy)'s set, so an existing published "
            "deployment needs no env change. Validated at boot against the "
            "ten-tab census — an unknown key fails the process. Ignored on the "
            "dev profile, which renders every tab"
        ),
    )
    # PLAN-0100 Step 6 (ADR-0035 D5(3)) — process-wide concurrent LLM requests.
    # 0 disables the cap; the published deployment pins 1.
    #
    # DEFAULT READING, stated so it can be corrected: the PLAN's pinned-values
    # table gives this row a single value (1) without naming a dev default, while
    # its sibling PROMPT_LOG_ENABLED row spells out "true on published, default
    # false". Read here the same way — a published resource posture, not a global
    # behaviour change — so dev and CI are untouched, matching Step 7's explicit
    # "default-off" rule. If Cray meant 1 everywhere, this default is the one line
    # to change.
    llm_max_inflight: int = Field(
        default=0,
        ge=0,
        description=(
            "Maximum concurrent LLM requests process-wide; 0 = unlimited. Over "
            "the cap a request FAILS FAST to the deterministic arm with the "
            "PLAN-0093 disclosure rather than queueing — a visitor waiting "
            "behind someone else's generation experiences a hang, which is what "
            "the cap exists to prevent. Published demo pins 1"
        ),
    )
    # PLAN-0100 Step 7 (ADR-0035 D6). Default-OFF so dev and CI never write a
    # byte; the published deployment sets true + the named-volume path.
    prompt_log_enabled: bool = Field(
        default=False,
        description=(
            "Append what visitors typed to a rolling 90-day JSONL log "
            "(published demo only). The row schema is CLOSED — no IP, no "
            "headers, no gate identity (ADR-0035 D6, ratified OQ-2)"
        ),
    )
    prompt_log_dir: str = Field(
        default="/var/log/vero/prompt-log",
        description=(
            "Directory for the prompt log's per-day JSONL files; the published "
            "compose mounts the named volume 'prompt-log' here"
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
    case_retention_enabled: bool = Field(
        default=False,
        description=(
            "When True (env CASE_RETENTION_ENABLED) AND the active vertical is "
            "fleet_maintenance, sweep visitor-opened repair cases older than "
            "CASE_RETENTION_DAYS at startup and every CASE_RETENTION_SWEEP_HOURS "
            "thereafter (PLAN-0105 LOCKED-3: an in-app task, never a host "
            "scheduler). Off by default because this DELETES data: no dev, CI, or "
            "pilot deployment may lose an operator's cases to an engine default — "
            "only fleet's published profile opts in, where the 90-day promise is "
            "the RoPA's."
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

    # Repair-case capture (PLAN-0096 Step 2). Photo BYTES live on disk, not in
    # Postgres: a phone photo is ~1-5 MB and nothing queries inside it, so the DB
    # row keeps only the metadata. The directory is created on first write.
    repair_case_photo_dir: str = Field(
        default="var/repair-case-photos",
        description=(
            "Directory for repair-case photo uploads (env REPAIR_CASE_PHOTO_DIR). "
            "Relative paths resolve from the repo root. Local disk only — PLAN-0096 "
            "AC-11 forbids any live external call, object storage included."
        ),
    )
    repair_case_photo_max_bytes: int = Field(
        default=12 * 1024 * 1024,
        description=(
            "Per-photo upload ceiling in bytes (env REPAIR_CASE_PHOTO_MAX_BYTES). "
            "12 MB clears a modern phone photo with headroom; an over-size upload is "
            "refused with 413 rather than truncated."
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
    # --- LINE Official Account push (PLAN-0096 Step 7 / AC-8) -------------------
    # The ONE new outbound channel of the fleet pilot, and a DIFFERENT audience from
    # the Telegram notifier above: Telegram goes to our own harness chat (hence its
    # strict no-PII body), LINE goes to the operator's own people about the
    # operator's own trucks. Secrets from env ONLY (CLAUDE.md §8).
    line_channel_access_token: str = Field(
        default="",
        description=(
            "LINE Messaging API channel access token for the Official Account "
            "(env LINE_CHANNEL_ACCESS_TOKEN) — from env only, never committed. LINE "
            "Notify was discontinued 2025-03-31; this is the OA push API."
        ),
    )
    line_notify_enabled: bool = Field(
        default=False,
        description=(
            "Master switch for LINE push (env LINE_NOTIFY_ENABLED); default off so no "
            "dev session or offline test can reach a real recipient"
        ),
    )
    line_recipients: str = Field(
        default="",
        description=(
            "JSON object mapping a recipient ROLE to its LINE destination id "
            '(env LINE_RECIPIENTS), e.g. {"owner":"U…","operator":"U…","accounting":"U…"}. '
            "Whether these are individual users or one shared group is the partner's "
            "call and a named intake question; the seam takes either, since the push "
            "API's `to` field accepts both."
        ),
    )
    line_notify_cooldown_s: float = Field(
        default=300.0,
        gt=0.0,
        description=(
            "Minimum seconds between pushes of the SAME event kind to the SAME recipient "
            "(env LINE_NOTIFY_COOLDOWN_S) — a reminder that repeats every sweep is how a "
            "notification channel gets muted"
        ),
    )
    ollama_keep_alive: str = Field(
        default="30m",
        description=(
            "How long a warmed model stays resident in MS-S1 VRAM (Ollama keep_alive; "
            "env OLLAMA_KEEP_ALIVE) — the /warm route, the ping's warm one-liner, AND "
            "every /api/chat call. The chat path was added 2026-08-08: before it, chat "
            "calls sent no keep_alive at all and silently inherited Ollama's 5-minute "
            "default, so a warm here could be undone by ordinary traffic. PLAN-0100 "
            "Step 11 measured the cost on the published demo — a ~22 s cold load "
            "against a 25 s request timeout, so the first visitor after a quiet spell "
            "waited the whole timeout and then got a degraded, ungrounded answer. "
            "Deliberately ONE knob rather than a separate chat setting: two values "
            "that have to agree are a bug waiting for the day they do not."
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

    @property
    def published_view_keys(self) -> tuple[str, ...]:
        """``ui_published_views`` parsed into ordered view keys.

        A property rather than a stored field so there is exactly ONE parse, in
        one place: a second field holding the parsed form could be mutated to
        disagree with the string the validator checked, and the two carriers
        (the injected meta tag and ``/meta``) both read this.
        """
        parts = (part.strip().upper() for part in self.ui_published_views.split(","))
        return tuple(part for part in parts if part)

    @model_validator(mode="after")
    def _validate_published_views(self) -> Self:
        """Refuse to boot on a published view set the browser could not render.

        The same asymmetry ``ui_profile``'s ``Literal`` encodes, one level down:
        this value is typed by hand into a per-system ``published.env``, and every
        way of getting it wrong resolves toward a PUBLIC surface that is broken or
        over-exposed. A loud boot failure is recoverable; a demo that silently
        renders the wrong tabs in front of a design partner is not.

        Validated on every profile, not just ``published``. A dev process ignores
        the value when rendering, but a typo that only fails on the box nobody
        runs locally is exactly the bug class PLAN-0100 kept hitting.
        """
        keys = self.published_view_keys
        unknown = [key for key in keys if key not in ALL_VIEW_KEYS]
        if unknown:
            raise ValueError(
                f"UI_PUBLISHED_VIEWS names view keys that do not exist: {unknown}. "
                f"The census is {list(ALL_VIEW_KEYS)} (services/api/static/assets/app.js "
                "ALL_VIEWS). A published deployment must not boot with a tab set it "
                "cannot render."
            )
        if not keys:
            raise ValueError(
                "UI_PUBLISHED_VIEWS is empty, so this deployment would publish no "
                "console at all. app.js refuses to render such a page and says so "
                "on screen, but that refusal is the BACKSTOP — it fires in a "
                "visitor's browser, while this one fires in the operator's terminal "
                "at deploy time, before anyone sees the box."
            )
        duplicates = sorted({key for key in keys if keys.count(key) > 1})
        if duplicates:
            raise ValueError(
                f"UI_PUBLISHED_VIEWS repeats view keys: {duplicates}. The browser "
                "would silently collapse them, so a repeat is always a typo, and a "
                "typo in this value is a typo about what the public sees."
            )
        return self

    @model_validator(mode="after")
    def _validate_demo_persona_keys(self) -> Self:
        """Refuse to boot on a persona picker that would offer a login it cannot honour.

        Both halves of the pairing live in this file, so the whole check is
        offline: ``ui_demo_persona_keys`` holds ``person_id -> raw key`` and
        ``api_keys`` holds ``sha256(raw key) -> person_id``. They are typed into
        a deployment by hand, from two different places, and every way of
        mistyping either one produces the SAME visible symptom — a visitor picks
        a persona and is refused. On a public demo whose entire story is the
        approve beat, that reads as the product being broken, and it reads that
        way to the one audience the system exists for.

        Deliberately not deferred to the first login: the failure would then fire
        in a visitor's browser rather than in the operator's terminal at deploy
        time. Same asymmetry ``_validate_published_views`` encodes one field up.

        NOT checked here: that each ``person_id`` is authored in the active
        vertical's principals. That needs the vertical's YAML, which this module
        deliberately does not read — it happens at boot in ``main.py``'s
        lifespan helper, where ``load_procedures`` is already in hand.
        """
        if not self.ui_demo_persona_keys:
            return self
        if not self.api_keys:
            raise ValueError(
                "UI_DEMO_PERSONA_KEYS is provisioned but API_KEYS is empty, so "
                "every persona the picker offers would be refused at login. The "
                "picker is not a second credential source — it is a front end "
                "onto API_KEYS, and both are provisioned together or neither is."
            )
        for person_id, raw_key in self.ui_demo_persona_keys.items():
            if not raw_key:
                raise ValueError(
                    f"UI_DEMO_PERSONA_KEYS has an empty key for {person_id!r}. An "
                    "empty value is the shape an unset host-env pass-through takes, "
                    "so this is more likely a provisioning miss than a typo."
                )
            digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
            mapped = self.api_keys.get(digest)
            if mapped is None:
                raise ValueError(
                    f"UI_DEMO_PERSONA_KEYS[{person_id!r}] holds a raw key whose "
                    "SHA-256 digest is absent from API_KEYS, so the picker would "
                    "offer that persona and the login would 401. Regenerate the "
                    "pair together — the digest of the raw key IS the API_KEYS "
                    "entry, never a separately-chosen value."
                )
            if mapped != person_id:
                raise ValueError(
                    f"UI_DEMO_PERSONA_KEYS[{person_id!r}] holds the raw key that "
                    f"API_KEYS maps to {mapped!r}. The picker would then label the "
                    "card with one persona while the audit trail recorded the "
                    "other — the exact confusion the on-screen disclosure promises "
                    "cannot happen (SD-4(b)). A crossed pair is worse than a "
                    "missing one, because nothing downstream looks wrong."
                )
        return self

    @model_validator(mode="after")
    def _fill_test_database_url(self) -> Self:
        """Default test_database_url to the derived ``<db>_test`` when blank."""
        if not self.test_database_url:
            self.test_database_url = _derive_test_database_url(self.database_url)
        return self


settings = Settings()
