"""FastAPI entry point for vero-lite."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI

from services.api.models.health import HealthResponse
from services.api.routers.actions import router as actions_router
from verticals.energy.data_adapter import register_energy_adapter
from verticals.energy.handlers import register_energy_handlers


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Register the energy vertical (adapter + handlers) on startup."""
    register_energy_adapter()
    register_energy_handlers()
    yield


app = FastAPI(
    title="vero-lite",
    description="Palantir-lite data platform — vertical ontology engine",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(actions_router)


@app.get("/health", response_model=HealthResponse, tags=["infrastructure"])
async def health() -> HealthResponse:
    """Liveness probe endpoint."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(UTC),
        version="0.1.0",
    )
