"""PLAN-0061 Step 4 (AC-6, persisted half): a declared join runs through
``run_procedure_persisted`` — the joined output set lands JSONB-safe (the fake
adapter deliberately ships raw ``datetime`` values: without the ``_json_safe``
boundary the JSONB write would raise — the procurement Decimal/datetime seed
lesson) and the pinned ``join``/``project`` fields round-trip into the stored
governance hash. Deterministic, offline, no LLM, disposable test DB.
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
    Step,
    StepInput,
    StepKind,
)
from tests.db_support import create_test_engine

_QUOTE_RENAMES = {
    "currency": "quote_currency",
    "part_no": "quote_part_no",
    "supplier_id": "quote_supplier_id",
}


class _FakeAdapter:
    vertical_name = "procurement"

    async def fetch_objects(self, object_type: str) -> list[dict[str, Any]]:
        if object_type == "PurchaseOrder":
            return [
                {
                    "po_id": "po-spindle-01",
                    "part_no": "part-spindle-01",
                    "supplier_id": "sup-rfq-01",
                    "quote_id": "quote-spindle-rfq",
                    "amount": 2150000.0,
                    "currency": "THB",
                    # a RAW datetime — JSONB refuses it without _json_safe
                    "created_at": datetime(2026, 6, 30, 9, 15, tzinfo=UTC),
                }
            ]
        if object_type == "Quotation":
            return [
                {
                    "quote_id": "quote-spindle-rfq",
                    "part_no": "part-spindle-01",
                    "supplier_id": "sup-rfq-01",
                    "price": 2150000.0,
                    "currency": "THB",
                    "quoted_at": datetime(2026, 6, 29, 14, 0, tzinfo=UTC),
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
    return Procedure(
        procedure_id="join-persisted-round",
        title="Join persisted round",
        goal="Persist a declared-join output set.",
        run_by="fixture_agent",
        steps=[
            Step(
                step_id="read_joined",
                name="Declared join",
                kind=StepKind.QUERY,
                input=StepInput.model_validate(
                    {
                        "reads": ["PurchaseOrder", "Quotation"],
                        "join": [{"with": "Quotation", "link": "po_from_quotation"}],
                        "project": {"fields": _QUOTE_RENAMES},
                    }
                ),
            )
        ],
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


async def test_declared_join_persists_jsonb_safe_and_pins(db_engine: AsyncEngine) -> None:
    meta = load_ontology_meta("procurement")
    executors = {
        StepKind.QUERY: QueryStepExecutor(
            adapter=_FakeAdapter(),  # type: ignore[arg-type]  # duck-typed: fetch_objects only
            object_type_names=frozenset(t.name for t in meta.object_types),
            meta=meta,
        )
    }
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        result = await run_procedure_persisted(
            session,
            _procedure(),
            _agent(),
            executors,
            vertical="procurement",
            run_id="join-persisted-1",
        )
    # the run completed and the JSONB write accepted the datetime-carrying rows
    assert result.run.status == PipelineRunStatus.COMPLETED.value
    artifact = result.step_results[-1].artifact
    assert artifact is not None
    row = artifact["output_set"][0]
    assert row["po_id"] == "po-spindle-01"
    assert row["price"] == 2150000.0  # enriched from the quote
    assert isinstance(row["created_at"], str)  # _json_safe coerced the datetime
    assert row["quote_part_no"] == "part-spindle-01"  # the side's collision renamed
    # the pinned join/project fields round-trip: the stored hash equals a fresh
    # recompute over the same declared config (join/project feed the pin).
    assert result.run.governance_hash is not None
    assert result.run.governance_hash == compute_governance_hash(
        build_governance_snapshot(_procedure())
    )
