"""FastAPI entry point for vero-lite."""

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from services.api.config import settings
from services.api.models.health import HealthResponse
from services.api.routers.actions import router as actions_router
from services.api.routers.admin import router as admin_router
from services.api.routers.query import router as query_router
from verticals.energy.data_adapter import register_energy_adapter
from verticals.energy.handlers import register_energy_handlers
from verticals.supply_chain.data_adapter import register_supply_chain_adapter
from verticals.supply_chain.handlers import register_supply_chain_handlers

_STATIC_DIR = Path(__file__).parent / "static"

# Explicit vertical registry (OQ-6: no import-scan discovery). Each entry
# registers that vertical's adapter + handlers; lifespan wires up the one
# named by OCT_VERTICAL. Adding a vertical = swap the ontology + adapter and
# add a row here — no engine or UI change (PLAN-0013 AC-template).
_VERTICAL_REGISTRARS: dict[str, tuple[Callable[[], object], Callable[[], None]]] = {
    "energy": (register_energy_adapter, register_energy_handlers),
    "supply_chain": (register_supply_chain_adapter, register_supply_chain_handlers),
}


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Register the OCT_VERTICAL-selected vertical (adapter + handlers) on startup."""
    vertical = settings.oct_vertical
    registrars = _VERTICAL_REGISTRARS.get(vertical)
    if registrars is None:
        known = ", ".join(sorted(_VERTICAL_REGISTRARS)) or "(none)"
        raise RuntimeError(
            f"OCT_VERTICAL={vertical!r} is not a registered vertical; known: {known}"
        )
    register_adapter, register_handlers = registrars
    register_adapter()
    register_handlers()
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
