"""PLAN-0052 Phase-3 OCT monitor (v1) — GET /runs list + GET /runs/{run_id} detail.

Read-only endpoint tests over seeded PipelineRun / StepResult rows. Binds to the
disposable ``<db>_test`` (never the dev/demo DB) via ``create_test_engine`` and
skips gracefully when Postgres is unreachable — mirrors
``tests/api/conftest.py::client_with_db``, but seeds runs first so the read
projections have something to return.

Covers AC-1 (list shape + waiting_human count + trigger/step-progress
projection), AC-2 (detail per-step trace/audit + 404), AC-3 (read-only by
construction), AC-7 (the waiting_human gate + proposals exposed read-only).
"""

from __future__ import annotations

import inspect
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.main import app
from services.api.routers import runs as runs_router
from services.db.base import Base
from services.db.session import get_session
from services.engine.procedures.runs import (
    PipelineRun,
    PipelineRunStatus,
    StepResult,
    StepResultStatus,
)
from tests.db_support import create_test_engine

_T0 = datetime(2026, 7, 5, 6, 0, tzinfo=UTC)
_T1 = _T0 + timedelta(hours=1)  # the waiting run starts later -> sorts first (newest-first)

_PROPOSAL_ARTIFACT = {
    "output_set": [
        {
            "action": {
                "id": "act-1",
                "title": "Start aerator on pond-3",
                "suggested_handler": "start_emergency_aerator",
            }
        }
    ]
}


def _seed_rows() -> list[PipelineRun | StepResult]:
    return [
        PipelineRun(
            run_id="run-mon-done",
            procedure_id="morning_round",
            agent_id="pond_agent",
            trigger_context={"triggered_by": "person-alice"},
            status=PipelineRunStatus.COMPLETED.value,
            started_at=_T0,
            updated_at=_T0 + timedelta(minutes=5),
        ),
        PipelineRun(
            run_id="run-mon-wait",
            procedure_id="morning_round",
            agent_id="pond_agent",
            trigger_context={"triggered_by": "person-bob"},
            status=PipelineRunStatus.WAITING_HUMAN.value,
            started_at=_T1,
            updated_at=_T1 + timedelta(minutes=2),
        ),
        StepResult(
            step_result_id="sr-done-1",
            run_id="run-mon-done",
            step_id="read_do",
            status=StepResultStatus.COMPLETE.value,
            duration_ms=12,
            reasoning_trace=[{"step_id": "read_do", "kind": "query", "summary": "read DO"}],
            audit={"actor": "engine", "actor_kind": "engine"},
            artifact={"output_set": [{"pond": "pond-3", "do": 3.2}]},
            created_at=_T0,
        ),
        StepResult(
            step_result_id="sr-done-2",
            run_id="run-mon-done",
            step_id="summary",
            status=StepResultStatus.COMPLETE.value,
            duration_ms=3,
            audit={"actor_kind": "engine"},
            created_at=_T0 + timedelta(minutes=1),
        ),
        StepResult(
            step_result_id="sr-wait-1",
            run_id="run-mon-wait",
            step_id="read_do",
            status=StepResultStatus.COMPLETE.value,
            duration_ms=9,
            reasoning_trace=[{"step_id": "read_do", "kind": "query"}],
            audit={"actor_kind": "engine"},
            created_at=_T1,
        ),
        StepResult(
            step_result_id="sr-wait-2",
            run_id="run-mon-wait",
            step_id="propose_aerator",
            status=StepResultStatus.WAITING_HUMAN.value,
            duration_ms=40,
            reasoning_trace=[
                {"step_id": "propose_aerator", "kind": "action", "summary": "propose"}
            ],
            audit={"actor_kind": "engine"},
            artifact=_PROPOSAL_ARTIFACT,
            created_at=_T1 + timedelta(minutes=1),
        ),
    ]


@pytest.fixture
async def monitor_client() -> AsyncIterator[AsyncClient]:
    """An httpx client bound to the app with a seeded, disposable test DB."""
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(eng, expire_on_commit=False)
    async with maker() as session:
        session.add_all(_seed_rows())
        await session.commit()

    async def _override_session() -> AsyncIterator[AsyncSession]:
        async with maker() as session:
            yield session

    app.dependency_overrides[get_session] = _override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


async def test_list_runs_newest_first_with_projection(monitor_client: AsyncClient) -> None:
    """AC-1: the list projects status/trigger/actor/step-progress, newest-first,
    and reports the waiting_human ('waiting on me') count."""
    resp = await monitor_client.get("/runs")
    assert resp.status_code == 200
    body = resp.json()
    assert body["waiting_human_count"] == 1
    runs = body["runs"]
    assert [r["run_id"] for r in runs] == ["run-mon-wait", "run-mon-done"]  # newest-first

    wait = runs[0]
    assert wait["status"] == "waiting_human"
    assert wait["trigger"] == "manual"  # unstamped trigger_context -> 'manual'
    assert wait["triggered_by"] == "person-bob"
    assert wait["steps_recorded"] == 2
    assert wait["steps_waiting"] == 1

    done = runs[1]
    assert done["status"] == "completed"
    assert done["triggered_by"] == "person-alice"
    assert done["steps_recorded"] == 2
    assert done["steps_waiting"] == 0


async def test_run_detail_trace_audit_and_gate(monitor_client: AsyncClient) -> None:
    """AC-2 + AC-7: detail round-trips per-step trace/audit/duration and exposes
    the waiting_human gate + its pending proposals READ-ONLY."""
    resp = await monitor_client.get("/runs/run-mon-wait")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "waiting_human"
    assert body["suspended_step"] == "propose_aerator"

    # AC-7: the gate's proposals are surfaced read-only (the Control-leg hook).
    assert [p["action_id"] for p in body["proposals"]] == ["act-1"]
    assert body["proposals"][0]["suggested_handler"] == "start_emergency_aerator"

    # AC-2: per-step trace/audit/duration round-trip in run order.
    steps = body["steps"]
    assert [s["step_id"] for s in steps] == ["read_do", "propose_aerator"]
    last = steps[-1]
    assert last["duration_ms"] == 40
    assert last["audit"] == {"actor_kind": "engine"}
    assert last["reasoning_trace"][0]["kind"] == "action"


async def test_run_detail_unknown_id_404(monitor_client: AsyncClient) -> None:
    """AC-2: an unknown run id is a 404, not a 500."""
    resp = await monitor_client.get("/runs/run-does-not-exist")
    assert resp.status_code == 404


def test_read_endpoints_perform_no_mutation() -> None:
    """AC-3: read-only by construction — the handlers call no writer/executor."""
    src = inspect.getsource(runs_router.list_runs) + inspect.getsource(runs_router.get_run)
    for forbidden in (".commit(", ".merge(", "resolve_gated_step", "resume_run", "run_procedure"):
        assert forbidden not in src, f"read endpoint must not reference {forbidden}"
