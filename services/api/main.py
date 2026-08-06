"""FastAPI entry point for vero-lite."""

import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse, HTMLResponse, Response
from starlette.types import Scope

from services.api.config import settings
from services.api.models.health import HealthResponse
from services.api.routers.actions import router as actions_router
from services.api.routers.admin import router as admin_router
from services.api.routers.audit import router as audit_router
from services.api.routers.cases import router as cases_router
from services.api.routers.demo import router as demo_router
from services.api.routers.exports import router as exports_router
from services.api.routers.insights import router as insights_router
from services.api.routers.intake import router as intake_router
from services.api.routers.pm import router as pm_router
from services.api.routers.procedure_draft import router as procedure_draft_router
from services.api.routers.procedures import router as procedures_router
from services.api.routers.query import router as query_router
from services.api.routers.runs import router as runs_router
from services.api.routers.whoami import router as whoami_router
from services.db.session import async_session
from services.engine.discovery import discover_and_register
from services.engine.registry import registry
from services.notify.line import describe_arm_state as describe_line_arm_state
from services.notify.telegram import describe_arm_state

# uvicorn configures its "uvicorn.error" logger (the startup banner) at INFO with
# a console handler, while leaving the root logger at WARNING — so a plain
# app-module INFO log is dropped from the server console. Boot diagnostics go
# through this logger so they appear alongside the uvicorn startup lines.
_boot_logger = logging.getLogger("uvicorn.error")

_STATIC_DIR = Path(__file__).parent / "static"


# --- Content-Security-Policy for the served OCT demo UI (defense-in-depth) ---
# PLAN-0054's operate UI (View H) keeps the operator's pilot API key in
# sessionStorage (the SD-A login-form auth surface). That security review
# returned "secure-for-pilot" with a SINGLE defense-in-depth gap: no CSP. This
# header is that safety net -- it caps what a *future* html:/innerHTML XSS
# regression could reach, turning "exfiltrate the sessionStorage credential to
# an attacker origin" into a contained bug (script execution + network egress
# are pinned to same-origin).
#
# Intentionally minimal: default-src 'self' plus only the relaxations the
# current assets actually need (verified against services/api/static):
#   * script-src 'self'         -- every script is an external assets/*.js; no
#                                  inline <script>, no eval / new Function, no
#                                  inline on*= handlers (all grep-verified).
#   * style-src 'unsafe-inline'  -- the UI injects <style> elements at runtime
#                                  (e.g. view-monitor.js injectStyles) and uses
#                                  many inline style= attributes; a nonce is
#                                  heavier for no real gain on a same-origin
#                                  static bundle.
#   * img-src 'self' data:       -- favicon.svg + defensive room for inline
#                                  data: images (data: cannot execute script).
#   * font-src 'self'            -- IBM Plex woff2 bundled under assets/fonts/.
#   * connect-src 'self'         -- every fetch() targets a relative same-origin
#                                  API path.
# object-src / base-uri / frame-ancestors harden with no functional cost.
# Scoped to the static mount (a StaticFiles subclass, NOT a global middleware)
# so it never lands on the JSON API or FastAPI's /docs & /redoc -- whose
# Swagger/ReDoc UIs load from a CDN + inline scripts and would break under a
# blanket 'self' policy.
_OCT_CSP = "; ".join(
    (
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data:",
        "font-src 'self'",
        "connect-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "frame-ancestors 'none'",
    )
)


# --- The UI-profile boot injection (PLAN-0100 Step 2) ---
# The published profile must be knowable BEFORE the first paint: ``app.js`` calls
# ``buildTabs()`` before ``initMeta()``, so a profile arriving over ``/meta``
# would land after the header was already built — and any fetch-based mechanism
# has to answer "what if the fetch fails?", whose only safe answer on a public
# deployment is the restrictive profile, which would then strip the console for a
# developer whose backend merely hiccuped. Serving the value inside the document
# removes the question rather than answering it.
#
# It rides a ``<meta>`` tag and NOT an inline ``<script>`` because ``_OCT_CSP``
# pins ``script-src 'self'``: an inline script would be silently blocked, leaving
# the value undefined and the UI defaulting to the FULL console — the exact
# exposure AC-1 exists to prevent. A meta tag executes nothing, so the CSP has no
# opinion about it and the header keeps its "no inline script" invariant.
_UI_PROFILE_META_DEV = '<meta name="ui-profile" content="dev" />'


def _ui_profile_meta(profile: str) -> str:
    return f'<meta name="ui-profile" content="{profile}" />'


class _StaticFilesWithCSP(StaticFiles):
    """StaticFiles that stamps a CSP on every served file and profiles the index.

    Overriding ``get_response`` covers the ``html=True`` index lookup, the
    ``assets/`` bundle, and 404s alike, scoping the header to the UI mount so it
    never lands on the JSON API or the /docs pages.
    """

    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        if isinstance(response, FileResponse) and str(response.path).endswith("index.html"):
            response = self._profiled_index(response)
        response.headers["Content-Security-Policy"] = _OCT_CSP
        return response

    def _profiled_index(self, response: FileResponse) -> Response:
        """Rewrite the index's profile tag, or hand back the file untouched.

        The dev profile takes the fast path deliberately: it is the default, and
        not rewriting it keeps ``FileResponse``'s ETag/Last-Modified handling for
        every existing flow.
        """
        if settings.ui_profile == "dev":
            return response
        html = Path(response.path).read_text(encoding="utf-8")
        if _UI_PROFILE_META_DEV not in html:
            # Fail loud rather than serve a published page still marked "dev".
            # Silence here is the failure mode that matters: the page would look
            # perfectly normal while carrying the wrong profile.
            raise RuntimeError(
                "index.html no longer contains the ui-profile anchor "
                f"{_UI_PROFILE_META_DEV!r} — the PLAN-0100 boot injection cannot "
                "be applied. Restore the tag or update _UI_PROFILE_META_DEV."
            )
        profiled = HTMLResponse(
            html.replace(_UI_PROFILE_META_DEV, _ui_profile_meta(settings.ui_profile))
        )
        # The body no longer matches the file on disk, so the file's validators
        # would be wrong; without them the browser stops issuing conditional
        # requests for the index, which is also what keeps a profile change from
        # being served out of a stale cache.
        profiled.headers["Cache-Control"] = "no-store"
        return profiled


async def _register_aquaculture_executors() -> None:
    from verticals.aquaculture.procedures_factory import (
        register_aquaculture_procedure_executors,
    )

    await register_aquaculture_procedure_executors()


async def _register_energy_executors() -> None:
    from verticals.energy.procedures_factory import register_energy_procedure_executors

    await register_energy_procedure_executors()


async def _register_procurement_executors() -> None:
    from verticals.procurement.hero_demo.run import register_procurement_procedure_executors

    await register_procurement_procedure_executors()


async def _register_supply_chain_executors() -> None:
    from verticals.supply_chain.procedures_factory import (
        register_supply_chain_procedure_executors,
    )

    await register_supply_chain_procedure_executors()


async def _register_building_materials_executors() -> None:
    from verticals.building_materials.procedures_factory import (
        register_building_materials_procedure_executors,
    )

    await register_building_materials_procedure_executors()


async def _register_fleet_maintenance_executors() -> None:
    from verticals.fleet_maintenance.procedures_factory import (
        register_fleet_maintenance_procedure_executors,
    )

    await register_fleet_maintenance_procedure_executors()


_PROCEDURE_EXECUTOR_REGISTRARS: dict[str, Callable[[], Awaitable[None]]] = {
    "aquaculture": _register_aquaculture_executors,
    "energy": _register_energy_executors,
    "procurement": _register_procurement_executors,
    "supply_chain": _register_supply_chain_executors,
    "building_materials": _register_building_materials_executors,
    "fleet_maintenance": _register_fleet_maintenance_executors,
}
"""Per-vertical procedure-executor factory registration (PLAN-0062 AC-5). Imports stay
LAZY inside each registrar so booting one vertical never imports another's harness.
All six PROCEDURE-SHIPPING verticals register a factory (building_materials joined at
PLAN-0081 — the governed-credit hero; fleet_maintenance at PLAN-0086 — the governed
repair-spend hero, the first vertical shipping the gate advisory ON from day one);
the remaining spec-less Tier-1 mirror (vet_clinic — no ``procedures.yaml``) registers
none."""


def _is_environment_absent(exc: Exception) -> bool:
    """Is this boot-load failure "no database here", or "this code is wrong"?

    The policy seam for the two fail-soft projection loads below. Both keep booting
    either way — PLAN-0095's DB-less demo depends on it — but they must not keep
    REPORTING both the same way, which is the hole that let PLAN-0096 Step 8/9 sit dead
    for a whole release: an ``UnboundLocalError`` landed in the same handler as an
    unreachable Postgres and logged the same reassuring "serving fixture values" line.

    Return ``True`` for the expected, environmental causes (an operator running the demo
    with no database is not a defect). Return ``False`` for anything that means the code
    itself is broken — those get ERROR + a traceback + a ``BUG:``-prefixed status reason,
    so ``health_check`` and the boot log both say so.

    TODO(Cray): write the policy. The stub below is deliberately the CURRENT behaviour
    (absorb everything as environmental), so the tree stays green until you replace it —
    which also means the distinction is inert until then. Things worth deciding:

      * ``OSError`` / ``ConnectionRefusedError`` — the raw "nothing is listening" case.
      * ``sqlalchemy.exc.SQLAlchemyError`` — note asyncpg connect failures arrive
        WRAPPED as ``InterfaceError``/``OperationalError`` (both ``DBAPIError``), so
        catching ``OSError`` alone will miss them.
      * ``sqlalchemy.exc.ProgrammingError`` is also a ``SQLAlchemyError`` but usually
        means "schema not migrated" — environmental or defect? Your call.
      * ``NameError`` (incl. ``UnboundLocalError``), ``AttributeError``, ``TypeError``
        are the family that must return ``False`` — that is the regression this exists
        to make loud.

    Add the ``sqlalchemy.exc`` import at module scope when you fill this in.
    """
    return True


def _absorb_boot_load_failure(
    record_unavailable: Callable[[str], None],
    exc: Exception,
    *,
    what: str,
    degraded: str,
) -> None:
    """Log + record a boot-time projection load failure, telling the two causes apart.

    Fail-soft either way, never with the same message. An absent database is expected,
    so it warns and says what the operator now sees instead; a programming error keeps
    the process alive while making itself impossible to mistake for one.
    """
    if _is_environment_absent(exc):
        record_unavailable(str(exc))
        _boot_logger.warning("%s NOT loaded (%s) — %s", what, exc, degraded)
        return
    record_unavailable(f"BUG: {exc!r}")
    _boot_logger.error(
        "%s NOT loaded — a PROGRAMMING error, not an unreachable database; %s",
        what,
        degraded,
        exc_info=True,
    )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Auto-discover + register all verticals at startup (import-scan over
    ``verticals/*`` — ADR-0023 / PLAN-0032; the ADR-006 D3 L1→L2 plugin-maturity move,
    no hand-wired registry map). The OCT_VERTICAL-selected vertical is warmed for the
    real-time anchor.
    """
    discover_and_register()
    vertical = settings.oct_vertical
    known = registry.verticals()
    if vertical not in known:
        raise RuntimeError(
            f"OCT_VERTICAL={vertical!r} is not a discovered vertical; "
            f"known: {', '.join(known) or '(none)'}"
        )
    # PLAN-0015 D1: warm the per-process live OperationalEvent view so the
    # real-time anchor base = server start (the breach is anchored to "now").
    # Reads raw object dicts only (no LLM call), so it is safe even when MS-S1 is
    # warming; a no-op beyond a fixed-datetime copy when OCT_DEMO_TIME_ANCHOR off.
    await registry.get_adapter(vertical).fetch_objects("OperationalEvent")
    # PLAN-0054 Step 6b / PLAN-0062 Step 1: register the ACTIVE vertical's deterministic
    # procedure-executor factory. The gate-resolve endpoint resumes a run via
    # registry.get_procedure_executors(vertical), which 409s until a factory is
    # registered -- discover_and_register (OQ-6) registers adapters + handlers only.
    # Explicit + active-vertical-scoped (NOT import-scan); deterministic (no MS-S1).
    registrar = _PROCEDURE_EXECUTOR_REGISTRARS.get(vertical)
    if registrar is not None:
        await registrar()
    if vertical == "procurement":
        # PLAN-0054 Step 6c: seed ONE waiting_human run so the Control-leg operate
        # demo (View H) has a real gate to act on. Env-gated (demo only), idempotent
        # (a fixed run_id, skipped if present), and FAIL-SOFT (a seed error logs +
        # never blocks the demo boot — the Monitor just shows no run).
        if settings.oct_demo_seed_operate:
            # These stay lazy (vertical-specific harnesses). ``async_session`` must NOT
            # join them: Python binds locals at COMPILE time, so a local import here
            # would make the name function-local for the whole of ``lifespan`` — and the
            # fleet block below, which does not run under this branch, would then raise
            # UnboundLocalError straight into its fail-soft handler and silently skip
            # both projection refreshes. It is imported at module scope for that reason.
            from services.engine.procedures.persistence import load_run
            from verticals.procurement.hero_demo.run import seed_operate_waiting_human_run

            try:
                async with async_session() as _seed_session:
                    if await load_run(_seed_session, "run-operate-demo") is None:
                        _seeded = await seed_operate_waiting_human_run(_seed_session)
                        _boot_logger.info(
                            "operate-demo seed: run 'run-operate-demo' seeded (status=%s)",
                            _seeded.run.status,
                        )
                    else:
                        _boot_logger.info(
                            "operate-demo seed: run 'run-operate-demo' already present — skip"
                        )
            except Exception as exc:  # fail-soft — a seed error must never block the demo boot
                _boot_logger.warning("operate-demo seed skipped (error): %s", exc)
    # PLAN-0096 Step 9 / AC-10: load the confirmed-PM view once at boot, so a restart
    # does not silently revert every truck an operator has already confirmed to its
    # fixture value. Fail-SOFT and LOUD: the DB-less demo (PLAN-0095) must still boot,
    # so an unreachable database logs and records the reason on the view rather than
    # aborting startup — the view then reports itself unloaded instead of pretending
    # nobody has confirmed anything.
    if "fleet_maintenance" in known:
        from verticals.fleet_maintenance import pm_projection

        try:
            async with async_session() as _pm_session:
                _pm_loaded = await pm_projection.refresh(_pm_session)
            _boot_logger.info(
                "fleet PM overrides loaded: %d truck(s) carry confirmed values", len(_pm_loaded)
            )
        except Exception as exc:  # fail-soft — a PM read must never block the demo boot
            _absorb_boot_load_failure(
                pm_projection.record_unavailable,
                exc,
                what="fleet PM overrides",
                degraded="trucks serve fixture values until a confirm refreshes the view",
            )

        # PLAN-0096 Step 8 (build-order item 2): load the real repair cases onto the
        # event stream once at boot, so a restart does not silently drop every case an
        # operator has already accepted a quote for back to the pure fixture. Same
        # fail-SOFT-and-LOUD contract as the PM view above, for the same reason: the
        # DB-less demo (PLAN-0095) must still boot, and an unloaded view must SAY it is
        # unloaded rather than look like a fleet with no live cases.
        from verticals.fleet_maintenance import case_projection

        try:
            async with async_session() as _case_session:
                _cases_loaded = await case_projection.refresh(_case_session)
            _boot_logger.info(
                "fleet live cases loaded: %d case(s) with an accepted quote reach the gate",
                len(_cases_loaded),
            )
        except Exception as exc:  # fail-soft — a case read must never block the demo boot
            _absorb_boot_load_failure(
                case_projection.record_unavailable,
                exc,
                what="fleet live cases",
                degraded=(
                    "the event stream serves the synthetic fixture only until a case "
                    "write refreshes the view"
                ),
            )
    # One-shot boot diagnostic: makes a mis-armed PLAN-0014 notifier (e.g. the
    # enable flag left off — otherwise a silent per-call no-op) visible at startup.
    _boot_logger.info(
        "verticals discovered: %s; active=%r; PLAN-0014 Telegram notify: %s; "
        "PLAN-0096 LINE notify: %s",
        ", ".join(known),
        vertical,
        describe_arm_state(),
        describe_line_arm_state(),
    )
    yield


app = FastAPI(
    title="vero-lite",
    description="Palantir-lite data platform — vertical ontology engine",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(actions_router)
app.include_router(query_router)
app.include_router(admin_router)
app.include_router(audit_router)
app.include_router(cases_router)
app.include_router(pm_router)
app.include_router(intake_router)
app.include_router(procedures_router)
app.include_router(procedure_draft_router)
app.include_router(demo_router)
app.include_router(runs_router)
app.include_router(whoami_router)
app.include_router(insights_router)
app.include_router(exports_router)


@app.get("/health", response_model=HealthResponse, tags=["infrastructure"])
async def health() -> HealthResponse:
    """Liveness probe endpoint."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(UTC),
        version="0.1.0",
    )


# Serve the Claude-Design OCT demo UI (PLAN-0013 Step 5, OQ-4: one process, one
# URL, same-origin, no CORS). Mounted LAST so the API routes above take
# precedence; this catch-all serves index.html at "/" and the assets/ bundle.
# The UI fetches the relative API paths (/meta, /objects, /recommendations,
# /query) which resolve to the routers above.
app.mount("/", _StaticFilesWithCSP(directory=_STATIC_DIR, html=True), name="ui")
