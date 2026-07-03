"""PLAN-0048 Step 3 — AC-12: the HTTP/registry composition, proven offline.

A test-registered ``ExecutorFactory`` wiring the generic ``QueryStepExecutor``
(adapter via ``registry.get_adapter`` — the SD-4 composition recipe) drives the
REAL ``POST /procedures/{id}/run`` endpoint through suspend; the same spec with
NO factory registered still 409s. The fixture spec (a reads-declaring
procedure) is monkeypatched in — no shipped ``procedures.yaml`` migrates
(SD-3), so the real energy spec stays byte-unchanged.

This module is the documented composition recipe the SD-4 follow-up PLAN
starts from: real production factories do exactly ``_factory`` below, plus the
ACTION executor's client wiring (the LLM-surface decision SD-4 defers).
"""

import hashlib
from typing import Any

import pytest
from httpx import AsyncClient

from services.api.config import settings
from services.api.routers import runs as runs_router
from services.engine.ontology_meta import load_ontology_meta
from services.engine.procedures.orchestrator import RunContext, StepExecutor, StepOutcome
from services.engine.procedures.query_step import QueryStepExecutor
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    Procedure,
    Step,
    StepInput,
    StepKind,
    Trigger,
    VerticalProcedures,
)
from services.engine.registry import registry

RAW_KEY = "test-key-op-somchai"
DIGEST = hashlib.sha256(RAW_KEY.encode("utf-8")).hexdigest()
HEADERS = {"Authorization": f"Bearer {RAW_KEY}"}


@pytest.fixture
def runs_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", {DIGEST: "op-somchai"})


class _GatedAction:
    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(output=[{"action": "restart"}])


def _fixture_spec() -> VerticalProcedures:
    """A reads-declaring energy procedure — fixture-only (SD-3: no shipped
    procedures.yaml migrates onto ``reads``)."""
    return VerticalProcedures(
        vertical="energy",
        agents=[
            Agent(
                agent_id="grid_agent",
                name="Grid Agent",
                autonomy_ceiling=Autonomy.GATED,
                allowed=AgentAllowed(
                    step_kinds=[],
                    action_handlers=["restart"],
                    object_types=["OperationalEvent"],
                ),
            )
        ],
        procedures=[
            Procedure(
                procedure_id="read_bound_sweep",
                title="Read-bound Sweep",
                run_by="grid_agent",
                trigger=Trigger.MANUAL,
                steps=[
                    Step(
                        step_id="read",
                        name="Read events",
                        kind=StepKind.QUERY,
                        input=StepInput(reads=["OperationalEvent"]),
                    ),
                    Step(
                        step_id="act",
                        name="Restart",
                        kind=StepKind.ACTION,
                        handler="restart",
                    ),
                ],
            )
        ],
    )


@pytest.fixture
def read_bound_spec(monkeypatch: pytest.MonkeyPatch) -> None:
    """Route the active vertical's spec resolution to the fixture spec."""
    spec = _fixture_spec()
    monkeypatch.setattr(runs_router, "load_procedures", lambda vertical: spec)


def _register_read_factory() -> None:
    """The SD-4 composition recipe: the generic query executor wired from the
    registry's own adapter registration — nothing hand-rolled per procedure."""
    ontology_names = frozenset(m.name for m in load_ontology_meta("energy").object_types)

    def factory() -> dict[StepKind, StepExecutor]:
        return {
            StepKind.QUERY: QueryStepExecutor(
                adapter=registry.get_adapter("energy"),
                object_type_names=ontology_names,
            ),
            StepKind.ACTION: _GatedAction(),
        }

    registry.register_procedure_executors("energy", factory)


async def test_generic_query_executor_drives_real_endpoint_to_suspend(
    client_with_db: AsyncClient, runs_auth: None, read_bound_spec: None
) -> None:
    """AC-12: the composed factory (generic executor + registry adapter) runs the
    reads-declaring procedure through the REAL endpoint to the gate suspend."""
    _register_read_factory()
    response = await client_with_db.post(
        "/procedures/read_bound_sweep/run", json={}, headers=HEADERS
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "waiting_human"
    assert body["suspended_step"] == "act"


async def test_unwired_vertical_still_409s(
    client_with_db: AsyncClient, runs_auth: None, read_bound_spec: None
) -> None:
    """AC-12 (negative): the same spec with NO registered factory refuses 409 —
    the ADR-0023 explicit-registration contract is unchanged."""
    response = await client_with_db.post(
        "/procedures/read_bound_sweep/run", json={}, headers=HEADERS
    )
    assert response.status_code == 409
