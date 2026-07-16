"""FastAPI entry point for vero-lite."""

import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.types import Scope

from services.api.config import settings
from services.api.models.health import HealthResponse
from services.api.routers.actions import router as actions_router
from services.api.routers.admin import router as admin_router
from services.api.routers.audit import router as audit_router
from services.api.routers.demo import router as demo_router
from services.api.routers.intake import router as intake_router
from services.api.routers.procedure_draft import router as procedure_draft_router
from services.api.routers.procedures import router as procedures_router
from services.api.routers.query import router as query_router
from services.api.routers.runs import router as runs_router
from services.api.routers.whoami import router as whoami_router
from services.engine.discovery import discover_and_register
from services.engine.registry import registry
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


class _StaticFilesWithCSP(StaticFiles):
    """StaticFiles that stamps a Content-Security-Policy on every served file.

    Overriding ``get_response`` covers the ``html=True`` index lookup, the
    ``assets/`` bundle, and 404s alike, scoping the header to the UI mount so it
    never lands on the JSON API or the /docs pages.
    """

    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        response.headers["Content-Security-Policy"] = _OCT_CSP
        return response


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


_PROCEDURE_EXECUTOR_REGISTRARS: dict[str, Callable[[], Awaitable[None]]] = {
    "aquaculture": _register_aquaculture_executors,
    "energy": _register_energy_executors,
    "procurement": _register_procurement_executors,
    "supply_chain": _register_supply_chain_executors,
}
"""Per-vertical procedure-executor factory registration (PLAN-0062 AC-5). Imports stay
LAZY inside each registrar so booting one vertical never imports another's harness.
All four PROCEDURE-SHIPPING verticals register a factory; the spec-less Tier-1 mirrors
(building_materials, vet_clinic — no ``procedures.yaml``) register none."""


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
            from services.db.session import async_session
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
    # One-shot boot diagnostic: makes a mis-armed PLAN-0014 notifier (e.g. the
    # enable flag left off — otherwise a silent per-call no-op) visible at startup.
    _boot_logger.info(
        "verticals discovered: %s; active=%r; PLAN-0014 Telegram notify: %s",
        ", ".join(known),
        vertical,
        describe_arm_state(),
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
app.include_router(intake_router)
app.include_router(procedures_router)
app.include_router(procedure_draft_router)
app.include_router(demo_router)
app.include_router(runs_router)
app.include_router(whoami_router)


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
