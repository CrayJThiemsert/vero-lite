"""FastAPI entry point for vero-lite."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from services.api.config import settings
from services.api.models.health import HealthResponse
from services.api.routers.actions import router as actions_router
from services.api.routers.admin import router as admin_router
from services.api.routers.demo import router as demo_router
from services.api.routers.intake import router as intake_router
from services.api.routers.procedure_draft import router as procedure_draft_router
from services.api.routers.procedures import router as procedures_router
from services.api.routers.query import router as query_router
from services.api.routers.runs import router as runs_router
from services.engine.discovery import discover_and_register
from services.engine.registry import registry
from services.notify.telegram import describe_arm_state

# uvicorn configures its "uvicorn.error" logger (the startup banner) at INFO with
# a console handler, while leaving the root logger at WARNING — so a plain
# app-module INFO log is dropped from the server console. Boot diagnostics go
# through this logger so they appear alongside the uvicorn startup lines.
_boot_logger = logging.getLogger("uvicorn.error")

_STATIC_DIR = Path(__file__).parent / "static"


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
    # PLAN-0054 Step 6b: register the deterministic procurement procedure-executor
    # factory for the Control-leg operate demo. The gate-resolve endpoint resumes a
    # run via registry.get_procedure_executors(vertical), which 409s until a factory
    # is registered -- discover_and_register (OQ-6) registers adapters + handlers only.
    # Explicit + active-vertical-scoped (NOT import-scan); deterministic (no MS-S1).
    if vertical == "procurement":
        from verticals.procurement.hero_demo.run import (
            register_procurement_procedure_executors,
        )

        await register_procurement_procedure_executors()
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
app.include_router(intake_router)
app.include_router(procedures_router)
app.include_router(procedure_draft_router)
app.include_router(demo_router)
app.include_router(runs_router)


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
app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="ui")
