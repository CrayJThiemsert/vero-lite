"""PLAN-0056 Step 6 (ADR-0029 SD-1/SD-4; SD-P3 ship-dark) — the recommender-loop wiring.

Proves AC-11: with ``event_bridge_enabled`` OFF (default) the recommender loop is byte-behavior
identical (the resolver is never loaded, nothing fires); with it ON, an actionable recommendation
whose ``suggested_handler`` maps to an ``event``-trigger procedure is FED INTO the governed engine
(a real PipelineRun). Also covers the mapping derivation (``event_kind = suggested_handler``,
``entity_ids`` = affected-entity PKs, ``detected_at`` = ``created_at``) and the graceful no-fire
paths (non-event vertical, no executor factory, unmapped kind — the last is the Step-7 LOUD hook).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.api.routers import actions
from services.db.base import Base
from services.engine.actions import AuditMetadata, EntityRef, RecommendedAction
from services.engine.procedures.event_bridge import EventFireResult
from services.engine.procedures.orchestrator import RunContext, StepExecutor, StepOutcome
from services.engine.procedures.runs import PipelineRun, PipelineRunStatus
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    EventTrigger,
    Person,
    Procedure,
    ServicePrincipal,
    Step,
    StepKind,
    Trigger,
    VerticalProcedures,
)
from services.engine.recommender import ActionRecord
from tests.db_support import create_test_engine

SP_ID = "svc-buyer"
PROC_ID = "event_emergency_sourcing_round"
KIND = "asset_failure"
DETECTED = datetime(2026, 7, 7, 6, 0, tzinfo=UTC)


# --- synthetic vertical (mirrors tests/services/db/test_event_bridge_fire.py) -----------------


class _Exec:
    def __init__(self, output: list[Any]) -> None:
        self.output = output

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(output=self.output, reasoning_trace=[{"summary": step.step_id}])


def _executors() -> dict[StepKind, StepExecutor]:
    return {StepKind.QUERY: _Exec([{"asset": "pump-7"}]), StepKind.ACTION: _Exec([{"po": 1}])}


def _event_spec() -> VerticalProcedures:
    return VerticalProcedures(
        vertical="procurement",
        agents=[
            Agent(
                agent_id="buyer_agent",
                name="Buyer Agent",
                autonomy_ceiling=Autonomy.AUTO,
                allowed=AgentAllowed(action_handlers=["echo"]),
                service_principal_ids=[SP_ID],
            )
        ],
        service_principals=[ServicePrincipal(service_principal_id=SP_ID, name="Buyer Bot")],
        principals=[Person(person_id="req-planner", name="Req Planner", roles=frozenset({"req"}))],
        procedures=[
            Procedure(
                procedure_id=PROC_ID,
                title="Event Emergency Sourcing",
                run_by="buyer_agent",
                trigger=Trigger.EVENT,
                event_trigger=EventTrigger(event_kind=KIND, owning_person_id="req-planner"),
                steps=[
                    Step(step_id="read", name="Read", kind=StepKind.QUERY),
                    Step(
                        step_id="source",
                        name="Source",
                        kind=StepKind.ACTION,
                        autonomy=Autonomy.AUTO,
                        handler="echo",
                    ),
                ],
            )
        ],
    )


def _manual_spec() -> VerticalProcedures:
    """A vertical with NO event-trigger procedure — the bridge is a clean no-op here."""
    return VerticalProcedures(
        vertical="energy",
        agents=[
            Agent(
                agent_id="a",
                name="A",
                autonomy_ceiling=Autonomy.AUTO,
                allowed=AgentAllowed(action_handlers=["echo"]),
            )
        ],
        procedures=[
            Procedure(
                procedure_id="manual_only",
                title="Manual",
                run_by="a",
                trigger=Trigger.MANUAL,
                steps=[Step(step_id="s", name="S", kind=StepKind.ACTION, handler="echo")],
            )
        ],
    )


def _record(
    *, handler: str = KIND, entity_pk: str = "pump-7", action_id: str = "action-e1"
) -> ActionRecord:
    action = RecommendedAction(
        id=action_id,
        title="Overtemp on pump-7",
        description="d",
        vertical="procurement",
        reasoning_trace=[],
        confidence=0.8,
        affected_entities=[EntityRef(object_type="pump", primary_key=entity_pk)],
        suggested_handler=handler,
        audit_metadata=AuditMetadata(actor="engine", actor_kind="engine"),
        created_at=DETECTED,
    )
    return ActionRecord(action=action)


class _FakeAdapter:
    def __init__(self, events: list[dict[str, Any]]) -> None:
        self._events = events

    async def stream_events(self, kind: str) -> AsyncIterator[dict[str, Any]]:
        for e in self._events:
            yield e

    async def fetch_objects(self, object_type: str) -> list[dict[str, Any]]:
        return []


# --- DB fixtures (mirror the Step-5 fire test) ------------------------------------------------


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


@pytest.fixture(autouse=True)
def _clear_store() -> AsyncIterator[None]:
    actions.reset_action_store()
    yield
    actions.reset_action_store()


# --- _load_event_bridge -----------------------------------------------------------------------


async def test_load_event_bridge_non_event_vertical_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(actions, "load_procedures", lambda v: _manual_spec())
    assert await actions._load_event_bridge("energy") is None


async def test_load_event_bridge_missing_yaml_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(v: str) -> VerticalProcedures:
        raise FileNotFoundError(v)

    monkeypatch.setattr(actions, "load_procedures", _boom)
    assert await actions._load_event_bridge("nope") is None


async def test_load_event_bridge_no_factory_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.engine.registry import RegistryError

    monkeypatch.setattr(actions, "load_procedures", lambda v: _event_spec())
    monkeypatch.setattr(
        actions.registry,
        "get_procedure_executors",
        lambda v: (_ for _ in ()).throw(RegistryError("none")),
    )
    assert await actions._load_event_bridge("procurement") is None


async def test_load_event_bridge_event_vertical_returns_resolver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(actions, "load_procedures", lambda v: _event_spec())
    monkeypatch.setattr(actions.registry, "get_procedure_executors", lambda v: _executors)
    resolve = await actions._load_event_bridge("procurement")
    assert resolve is not None
    req = resolve(event_kind=KIND, entity_ids=["pump-7"], detected_at=DETECTED)
    assert req.procedure.procedure_id == PROC_ID


# --- _fire_event_for_record -------------------------------------------------------------------


async def test_fire_event_for_record_unmapped_kind_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # An actionable recommendation whose suggested_handler maps to no event procedure — the
    # resolver raises EventBridgeError, which Step 6 swallows (Step 7 makes it LOUD). No DB needed:
    # the raise precedes the session open.
    monkeypatch.setattr(actions, "load_procedures", lambda v: _event_spec())
    monkeypatch.setattr(actions.registry, "get_procedure_executors", lambda v: _executors)
    resolve = await actions._load_event_bridge("procurement")
    assert resolve is not None
    assert await actions._fire_event_for_record(resolve, _record(handler="not_a_kind")) is None


async def test_fire_event_for_record_maps_and_fires(
    db_engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    # AC-11 (flag-on) + the mapping: event_kind = suggested_handler, entity_ids = affected PKs,
    # detected_at = created_at. A real governed PipelineRun is created; its trigger_context proves
    # the derived mapping.
    monkeypatch.setattr(
        actions, "async_session", async_sessionmaker(db_engine, expire_on_commit=False)
    )
    monkeypatch.setattr(actions, "load_procedures", lambda v: _event_spec())
    monkeypatch.setattr(actions.registry, "get_procedure_executors", lambda v: _executors)
    resolve = await actions._load_event_bridge("procurement")
    assert resolve is not None
    outcome = await actions._fire_event_for_record(resolve, _record())
    assert outcome is not None
    assert outcome.result is EventFireResult.FIRED

    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as s:
        run = await s.get(PipelineRun, outcome.run_id)
        assert run is not None
        assert run.procedure_id == PROC_ID
        assert run.status == PipelineRunStatus.COMPLETED.value
        tc = run.trigger_context
        assert tc is not None
        assert tc["event_kind"] == KIND  # == suggested_handler
        assert tc["entity_ids"] == ["pump-7"]  # == affected-entity primary keys
        assert tc["detected_at"] == DETECTED.isoformat()  # == created_at


# --- _populate_store flag gating (AC-11: both states) -----------------------------------------


async def test_populate_store_flag_off_never_touches_bridge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Flag OFF (default) = zero behavior change: the resolver is never loaded, the fire branch is
    # never reached, and the ActionRecord store is populated exactly as before.
    calls: list[str] = []
    monkeypatch.setattr(actions.settings, "event_bridge_enabled", False)
    monkeypatch.setattr(actions.settings, "oct_vertical", "procurement")
    monkeypatch.setattr(actions.registry, "get_adapter", lambda v: _FakeAdapter([{"e": 1}]))

    async def _fake_recommend(event: dict[str, Any], vertical: str) -> ActionRecord:
        return _record()

    async def _spy_load(vertical: str) -> None:
        calls.append("load")
        return None

    monkeypatch.setattr(actions, "recommend", _fake_recommend)
    monkeypatch.setattr(actions, "_load_event_bridge", _spy_load)
    await actions._populate_store()
    assert calls == []  # bridge never consulted when the flag is off
    assert "action-e1" in actions._action_store  # existing path intact


async def test_populate_store_flag_on_fires_per_actionable_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Flag ON: the resolver is loaded once and each actionable record is fed to the fire helper.
    fired: list[str] = []
    monkeypatch.setattr(actions.settings, "event_bridge_enabled", True)
    monkeypatch.setattr(actions.settings, "oct_vertical", "procurement")
    monkeypatch.setattr(actions.registry, "get_adapter", lambda v: _FakeAdapter([{"e": 1}]))

    async def _fake_recommend(event: dict[str, Any], vertical: str) -> ActionRecord:
        return _record()

    sentinel = object()

    async def _fake_load(vertical: str) -> object:
        return sentinel

    async def _spy_fire(resolve: object, record: ActionRecord) -> None:
        assert resolve is sentinel
        fired.append(record.action.id)
        return None

    monkeypatch.setattr(actions, "recommend", _fake_recommend)
    monkeypatch.setattr(actions, "_load_event_bridge", _fake_load)
    monkeypatch.setattr(actions, "_fire_event_for_record", _spy_fire)
    await actions._populate_store()
    assert fired == ["action-e1"]  # fed into the bridge once
    assert "action-e1" in actions._action_store  # AND still stored (never replaced)


async def test_populate_store_flag_on_non_event_vertical_no_fire(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Flag ON but the vertical maps no event procedure: _load_event_bridge returns None, so the
    # fire helper is never reached — a clean no-op, not a failure.
    fired: list[str] = []
    monkeypatch.setattr(actions.settings, "event_bridge_enabled", True)
    monkeypatch.setattr(actions.settings, "oct_vertical", "energy")
    monkeypatch.setattr(actions.registry, "get_adapter", lambda v: _FakeAdapter([{"e": 1}]))
    monkeypatch.setattr(actions, "load_procedures", lambda v: _manual_spec())

    async def _fake_recommend(event: dict[str, Any], vertical: str) -> ActionRecord:
        return _record()

    async def _spy_fire(resolve: object, record: ActionRecord) -> None:
        fired.append(record.action.id)
        return None

    monkeypatch.setattr(actions, "recommend", _fake_recommend)
    monkeypatch.setattr(actions, "_fire_event_for_record", _spy_fire)
    await actions._populate_store()
    assert fired == []  # non-event vertical => no fire
    assert "action-e1" in actions._action_store
