"""PLAN-0077 Phase C (AC-6, persisted half): a declared transform runs through
``run_procedure_persisted`` — the enriched output set lands JSONB-safe (the derived
``Decimal`` magnitude coerces to its exact string, and the fake adapter deliberately ships a
raw ``datetime`` the ``_json_safe`` boundary must coerce — the procurement Decimal/datetime
seed lesson) and the pinned ``transform`` declaration round-trips into the stored governance
hash. Deterministic, offline, no LLM, disposable test DB.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.db.base import Base
from services.engine.ontology_meta import load_ontology_meta
from services.engine.procedures.governance_pin import (
    build_governance_snapshot,
    compute_governance_hash,
)
from services.engine.procedures.persistence import run_procedure_persisted
from services.engine.procedures.query_step import QueryStepExecutor
from services.engine.procedures.runs import PipelineRunStatus
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    Procedure,
    StepKind,
)
from services.engine.procedures.transform_step import TransformStepExecutor
from tests.db_support import create_test_engine

_OPS = [
    {
        "derive": {
            "target": "excursion_magnitude_c",
            "expr": {"op": "sub", "args": [{"field": "reading_c"}, {"field": "temp_ceiling"}]},
        }
    },
    {"default": {"target": "excursion_duration_h", "value": 9}},
    {"default": {"target": "stability_budget_ch", "value": 24}},
    {"coerce": {"target": "excursion_magnitude_c", "to": "string"}},
]


class _FakeAdapter:
    vertical_name = "supply_chain"

    async def fetch_objects(self, object_type: str) -> list[dict[str, Any]]:
        if object_type == "OperationalEvent":
            return [
                {
                    "event_id": "evt-1",
                    "reading_c": "12",
                    "temp_ceiling": "8",
                    # a RAW datetime — JSONB refuses it without _json_safe
                    "detected_at": datetime(2026, 6, 30, 9, 15, tzinfo=UTC),
                }
            ]
        return []


def _agent() -> Agent:
    return Agent(
        agent_id="fixture_agent",
        name="Fixture Agent",
        autonomy_ceiling=Autonomy.GATED,
        allowed=AgentAllowed(),
    )


def _procedure() -> Procedure:
    return Procedure.model_validate(
        {
            "procedure_id": "transform-persisted-round",
            "title": "Transform persisted round",
            "goal": "Persist a declared-transform output set.",
            "run_by": "fixture_agent",
            "steps": [
                {
                    "step_id": "read",
                    "name": "Read",
                    "kind": "query",
                    "input": {"reads": ["OperationalEvent"]},
                },
                {
                    "step_id": "enrich",
                    "name": "Enrich",
                    "kind": "transform",
                    "input": {"from": "read"},
                    "transform": {"ops": _OPS},
                },
            ],
        }
    )


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


async def test_declared_transform_persists_jsonb_safe_and_pins(db_engine: AsyncEngine) -> None:
    meta = load_ontology_meta("supply_chain")
    executors = {
        StepKind.QUERY: QueryStepExecutor(
            adapter=_FakeAdapter(),  # type: ignore[arg-type]  # duck-typed: fetch_objects only
            object_type_names=frozenset(t.name for t in meta.object_types),
            meta=meta,
        ),
        StepKind.TRANSFORM: TransformStepExecutor(),
    }
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        result = await run_procedure_persisted(
            session,
            _procedure(),
            _agent(),
            executors,
            vertical="supply_chain",
            run_id="transform-persisted-1",
        )
    # the run completed and the JSONB write accepted the derived + datetime-carrying rows
    assert result.run.status == PipelineRunStatus.COMPLETED.value
    row = result.step_results[-1].artifact["output_set"][0]  # type: ignore[index]
    assert row["excursion_magnitude_c"] == "4"  # 12 - 8, exact, coerced to string
    assert row["excursion_duration_h"] == 9  # defaulted
    assert isinstance(row["detected_at"], str)  # _json_safe coerced the datetime
    # the pinned transform declaration round-trips: the stored hash equals a fresh recompute
    # over the same declared config (the transform declaration feeds the pin).
    assert result.run.governance_hash is not None
    assert result.run.governance_hash == compute_governance_hash(
        build_governance_snapshot(_procedure())
    )
