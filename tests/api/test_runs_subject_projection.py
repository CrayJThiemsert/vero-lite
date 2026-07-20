"""PLAN-0084 Steps 2 + 4b — the ``subject`` projection on the runs read model (AC-2).

The map↔monitor linkage field: ``RunSummaryView.subject`` / ``RunDetailView.subject``,
projected from the persisted ``trigger_context``. Covered here:

* the SEED path — an explicit ``trigger_context["subject"]`` stamp projects verbatim;
* legacy / unstamped runs (already persisted in demo DBs) project ``None``;
* MALFORMED stamps (non-dict, missing keys, non-str, empty-str) project ``None``
  fail-soft — the list renders, never 500s;
* the EVENT path (Step 4b) — an event-fired run carries engine-stamped
  ``entity_ids`` and no ``subject`` key: exactly ONE id resolving to a known
  ontology object projects that subject; a legacy pre-re-pin id (``CNC-Line-07``)
  resolves to nothing and projects ``None``; >1 resolvable id is ambiguous → ``None``.

The event cases pin the resolve through ``_SUBJECT_PK_INDEX`` (the lazily-cached
pk→object_type index) by seeding the cache directly — the index build itself is
adapter-backed and per-vertical; isolating it here keeps the tests deterministic
and DB-only (no vertical adapter dependency). The cache is snapshot/restored per
test so no state leaks (the goal-path-isolation lesson).

DB-backed (skips without Postgres); MS-S1-free; read-only endpoints.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, timedelta

import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.config import settings
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

_T0 = datetime(2026, 7, 20, 6, 0, tzinfo=UTC)


def _run(run_id: str, minutes: int, trigger_context: dict | None) -> PipelineRun:
    return PipelineRun(
        run_id=run_id,
        procedure_id="morning_round",
        agent_id="pond_agent",
        trigger_context=trigger_context,
        status=PipelineRunStatus.WAITING_HUMAN.value,
        started_at=_T0 + timedelta(minutes=minutes),
        updated_at=_T0 + timedelta(minutes=minutes + 1),
    )


def _seed_rows() -> list[PipelineRun | StepResult]:
    # A FUNCTION returning FRESH ORM instances per fixture instantiation (the monitor-
    # harness pattern) — module-level instances become detached-persistent after the
    # first test's engine is dropped and silently fail to re-INSERT.
    return [
        # newest-first order on GET /runs = reverse of `minutes`
        _run(
            "run-subj-stamped",
            50,
            {
                "source": "operate-demo-seed",
                "triggered_by": "req-planner",
                "subject": {"object_type": "Equipment", "primary_key": "AST-CNC-014"},
            },
        ),
        _run("run-subj-legacy", 40, {"triggered_by": "person-bob"}),
        _run("run-subj-malformed-nondict", 30, {"subject": "AST-CNC-014"}),
        _run("run-subj-malformed-keys", 20, {"subject": {"object_type": "Equipment"}}),
        _run(
            "run-subj-event-resolvable",
            10,
            {"trigger": "event", "entity_ids": ["AST-CNC-014"], "event_kind": "emergency_source"},
        ),
        _run(
            "run-subj-event-legacy-id",
            5,
            {"trigger": "event", "entity_ids": ["CNC-Line-07"], "event_kind": "emergency_source"},
        ),
        _run(
            "run-subj-event-ambiguous",
            0,
            {"trigger": "event", "entity_ids": ["AST-CNC-014", "AST-CNC-009"]},
        ),
    ] + [
        # GET /runs/{id} routes through load_run, which needs >=1 step row — give the three
        # detail-tested runs a minimal recorded step each (the monitor-harness pattern).
        StepResult(
            step_result_id=f"sr-{rid}",
            run_id=rid,
            step_id="intake",
            status=StepResultStatus.WAITING_HUMAN.value,
            duration_ms=1,
            reasoning_trace=[],
            audit={"actor_kind": "engine"},
            created_at=_T0,
        )
        for rid in ("run-subj-stamped", "run-subj-event-resolvable", "run-subj-legacy")
    ]


@pytest.fixture
def pk_index() -> Iterator[None]:
    """Seed the resolve cache with a known index for the ACTIVE vertical; restore after."""
    snapshot = dict(runs_router._SUBJECT_PK_INDEX)
    runs_router._SUBJECT_PK_INDEX.clear()
    runs_router._SUBJECT_PK_INDEX[settings.oct_vertical] = {
        "AST-CNC-014": "Equipment",
        "AST-CNC-009": "Equipment",
    }
    yield
    runs_router._SUBJECT_PK_INDEX.clear()
    runs_router._SUBJECT_PK_INDEX.update(snapshot)


@pytest.fixture
async def subject_client() -> AsyncIterator[AsyncClient]:
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


async def test_subject_projection_on_list(subject_client: AsyncClient, pk_index: None) -> None:
    """AC-2 — one GET /runs covers every projection case; the list NEVER 500s on
    malformed stamps."""
    resp = await subject_client.get("/runs")
    assert resp.status_code == 200
    subjects = {r["run_id"]: r["subject"] for r in resp.json()["runs"]}
    assert subjects["run-subj-stamped"] == {
        "object_type": "Equipment",
        "primary_key": "AST-CNC-014",
    }
    assert subjects["run-subj-legacy"] is None
    assert subjects["run-subj-malformed-nondict"] is None
    assert subjects["run-subj-malformed-keys"] is None
    # Step 4b: exactly-one resolvable entity id -> projected subject
    assert subjects["run-subj-event-resolvable"] == {
        "object_type": "Equipment",
        "primary_key": "AST-CNC-014",
    }
    # a legacy pre-re-pin id resolves to nothing -> None (never an error)
    assert subjects["run-subj-event-legacy-id"] is None
    # >1 resolvable id is ambiguous -> None (resolution must be exact)
    assert subjects["run-subj-event-ambiguous"] is None


async def test_subject_projection_on_detail(subject_client: AsyncClient, pk_index: None) -> None:
    """AC-2 — the detail view carries the same projection (SD-A: list AND detail)."""
    stamped = await subject_client.get("/runs/run-subj-stamped")
    assert stamped.status_code == 200
    assert stamped.json()["subject"] == {
        "object_type": "Equipment",
        "primary_key": "AST-CNC-014",
    }
    event = await subject_client.get("/runs/run-subj-event-resolvable")
    assert event.status_code == 200
    assert event.json()["subject"] == {
        "object_type": "Equipment",
        "primary_key": "AST-CNC-014",
    }
    legacy = await subject_client.get("/runs/run-subj-legacy")
    assert legacy.status_code == 200
    assert legacy.json()["subject"] is None


def test_subject_of_fail_soft_unit_cases() -> None:
    """The fail-soft matrix, unit-level (no DB): every malformed shape -> None."""
    f = runs_router._subject_of
    assert f(None) is None
    assert f({}) is None
    assert f({"subject": None}) is None
    assert f({"subject": "Equipment|X"}) is None
    assert f({"subject": {}}) is None
    assert f({"subject": {"object_type": "Equipment"}}) is None
    assert f({"subject": {"primary_key": "X"}}) is None
    assert f({"subject": {"object_type": "", "primary_key": "X"}}) is None
    assert f({"subject": {"object_type": "Equipment", "primary_key": ""}}) is None
    assert f({"subject": {"object_type": 7, "primary_key": "X"}}) is None
    ok = f({"subject": {"object_type": "Equipment", "primary_key": "AST-1"}})
    assert ok is not None and (ok.object_type, ok.primary_key) == ("Equipment", "AST-1")
