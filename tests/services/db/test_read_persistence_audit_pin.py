"""PLAN-0048 Step 3 — AC-11 (write-ahead durability + the SD-5(a) audit row)
and AC-13 (the SD-5(b) ``reads`` pin, fail-closed at resume).

DB-backed (CI postgres; skips without it). The executor stays DB-free — the
persistence seam owns the ``read_refused`` audit append (same transaction as
the refusal StepResult's commit).
"""

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.db.base import Base
from services.engine.procedures.orchestrator import (
    ProcedureError,
    RunContext,
    StepExecutor,
    StepOutcome,
)
from services.engine.procedures.persistence import resume_run, run_procedure_persisted
from services.engine.procedures.query_step import QueryStepExecutor
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    OnFailure,
    Procedure,
    Step,
    StepInput,
    StepKind,
    Trigger,
)
from tests.db_support import create_test_engine

_EVENT_ROWS = [
    {"event_id": "e1", "measured_value": 95.0},
    {"event_id": "e2", "measured_value": 10.0},
]


class _FakeAdapter:
    vertical_name = "aquaculture"

    async def fetch_objects(
        self, object_type: str, filter_expr: str | None = None, limit: int = 1000
    ) -> list[dict[str, Any]]:
        return list(_EVENT_ROWS) if object_type == "OperationalEvent" else []

    async def fetch_links(
        self, link_type: str, from_pk: str | None = None, to_pk: str | None = None
    ) -> list[dict[str, Any]]:
        return []

    def stream_events(
        self, event_type: str, since: datetime | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        raise NotImplementedError


class _GatedAction:
    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(output=[{"action": "aerate"}])


def _agent(object_types: list[str] | None = None) -> Agent:
    return Agent(
        agent_id="pond_agent",
        name="Pond Agent",
        autonomy_ceiling=Autonomy.GATED,
        allowed=AgentAllowed(
            step_kinds=[],
            action_handlers=["start_aerator"],
            object_types=object_types or ["OperationalEvent", "Pond"],
        ),
    )


def _read_procedure(reads: list[str]) -> Procedure:
    """query (declared read) -> gated action; suspends at the gate."""
    return Procedure(
        procedure_id="read_bound_round",
        title="Read-bound Round",
        run_by="pond_agent",
        trigger=Trigger.MANUAL,
        steps=[
            Step(
                step_id="read",
                name="Read events",
                kind=StepKind.QUERY,
                input=StepInput(reads=reads),
            ),
            Step(
                step_id="act",
                name="Aerate",
                kind=StepKind.ACTION,
                handler="start_aerator",
            ),
        ],
    )


def _unbound_procedure() -> Procedure:
    """An entry-point query with NO reads — the generic executor refuses typed
    (unbound_query); reads-absent means the LOAD GATE SKIPS (no ontology I/O)."""
    return Procedure(
        procedure_id="unbound_round",
        title="Unbound Round",
        run_by="pond_agent",
        trigger=Trigger.MANUAL,
        steps=[
            Step(
                step_id="read",
                name="Read",
                kind=StepKind.QUERY,
                on_failure=OnFailure.ESCALATE_TO_HUMAN,
            ),
        ],
    )


def _executors() -> dict[StepKind, StepExecutor]:
    ontology_names = frozenset({"Pond", "Farm", "OperationalEvent"})
    return {
        StepKind.QUERY: QueryStepExecutor(adapter=_FakeAdapter(), object_type_names=ontology_names),
        StepKind.ACTION: _GatedAction(),
    }


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    """A fresh NullPool engine with the schema created; skips without Postgres."""
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


async def _audit_rows(engine: AsyncEngine, action: str) -> list[Any]:
    async with engine.connect() as conn:
        rows = await conn.execute(
            sa.text("SELECT run_id, step_id, payload FROM audit_log WHERE action = :action"),
            {"action": action},
        )
        return list(rows)


async def test_write_ahead_read_step_output_is_durable(db_engine: AsyncEngine) -> None:
    """AC-11 (happy half): the read step's fetched set lands durable via the
    write-ahead per-step commit; no read_refused audit row exists."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        result = await run_procedure_persisted(
            session,
            _read_procedure(["OperationalEvent"]),
            _agent(),
            _executors(),
            vertical="aquaculture",
            run_id="run-ac11a",
        )
    assert result.run.status == "waiting_human"
    async with db_engine.connect() as conn:
        artifact = (
            await conn.execute(
                sa.text(
                    "SELECT artifact FROM step_results "
                    "WHERE run_id = 'run-ac11a' AND step_id = 'read'"
                )
            )
        ).scalar_one()
    assert artifact == {"output_set": _EVENT_ROWS}
    assert await _audit_rows(db_engine, "read_refused") == []


async def test_write_ahead_refusal_is_durable_and_audited(db_engine: AsyncEngine) -> None:
    """AC-11 (refusal half, SD-5(a)): a typed refusal leaves BOTH a durable,
    queryable refusal StepResult AND a hash-chained read_refused audit row —
    appended by the persistence seam, in the same transaction."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        result = await run_procedure_persisted(
            session,
            _unbound_procedure(),
            _agent(),
            _executors(),
            vertical="aquaculture",
            run_id="run-ac11b",
        )
    assert result.run.status == "waiting_human"  # escalate_to_human routed it
    async with db_engine.connect() as conn:
        trace = (
            await conn.execute(
                sa.text(
                    "SELECT reasoning_trace FROM step_results "
                    "WHERE run_id = 'run-ac11b' AND step_id = 'read'"
                )
            )
        ).scalar_one()
    [entry] = trace
    assert entry["kind"] == "read_refused"
    assert entry["refusal_kind"] == "unbound_query"
    rows = await _audit_rows(db_engine, "read_refused")
    assert len(rows) == 1
    run_id, step_id, payload = rows[0]
    assert (run_id, step_id) == ("run-ac11b", "read")
    assert payload["refusal_kind"] == "unbound_query"
    assert payload["object_type"] is None


async def test_pin_carries_sorted_reads(db_engine: AsyncEngine) -> None:
    """AC-13 (pin content): the governance snapshot pins each step's declared
    reads, sorted."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        result = await run_procedure_persisted(
            session,
            _read_procedure(["OperationalEvent"]),
            _agent(),
            _executors(),
            vertical="aquaculture",
            run_id="run-ac13a",
        )
    snapshot = result.run.governance_snapshot
    assert snapshot is not None
    by_step = {entry["step_id"]: entry for entry in snapshot["steps"]}
    assert by_step["read"]["reads"] == ["OperationalEvent"]
    assert by_step["act"]["reads"] is None


async def test_mid_flight_reads_edit_fails_closed_at_resume(db_engine: AsyncEngine) -> None:
    """AC-13 (fail-closed): a mid-flight reads edit (OperationalEvent -> Pond —
    still load-gate-valid!) trips the standard pin-mismatch refusal at resume."""
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        await run_procedure_persisted(
            session,
            _read_procedure(["OperationalEvent"]),
            _agent(),
            _executors(),
            vertical="aquaculture",
            run_id="run-ac13b",
        )
    edited = _read_procedure(["Pond"])  # in ontology + allowlist — the gate accepts it
    async with maker() as fresh:
        with pytest.raises(ProcedureError, match="governance-config pin mismatch"):
            await resume_run(
                fresh,
                edited,
                _agent(),
                _executors(),
                "run-ac13b",
                vertical="aquaculture",
            )
