"""AC-4 — the ฿ facet survives the REAL persistence path (PLAN-0088 Step 2).

The corpus factory seeds ``StepResult`` rows directly, which proves the SQL but
NOT that the shape the orchestrator actually writes is the shape the substrate
reads. This test closes that gap: it runs a procedure whose executor emits a real
``EconomicImpact`` facet, persists it through ``persist_run``, and asserts
``benefit_rollup`` extracts back the exact ``Decimal`` that was emitted —
pinning the Decimal -> JSON string -> JSONB -> numeric-cast -> Decimal round trip.

A serialization change that turned money into a float would break here, and
nowhere else in the suite.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from decimal import Decimal
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.db.base import Base
from services.db.run_analytics import benefit_rollup
from services.engine.economic_impact import EconomicExposure, EconomicImpact
from services.engine.procedures.orchestrator import (
    RunContext,
    StepExecutor,
    StepOutcome,
    run_procedure,
)
from services.engine.procedures.persistence import persist_run
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    Procedure,
    Step,
    StepKind,
)
from tests.db_support import create_test_engine

_NET = Decimal("8150000")
_GOVERNED = Decimal("1650000")


class _ImpactExec:
    """An executor that emits one ``economic_impact`` facet on its reasoning trace."""

    def __init__(self, detail: dict[str, Any]) -> None:
        self.detail = detail

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(
            output=[{"read": "ok"}],
            reasoning_trace=[
                {
                    "step_id": "economic-impact-0",
                    "kind": "economic_impact",
                    "summary": "impact",
                    "detail": self.detail,
                }
            ],
        )


def _impact_detail(net: Decimal, currency: str = "THB") -> dict[str, Any]:
    impact = EconomicImpact(
        provisional=True,
        currency=currency,
        kind="avoided_outage",
        baseline=EconomicExposure(label="ungoverned", exposure_thb=_GOVERNED + net),
        governed=EconomicExposure(label="governed", exposure_thb=_GOVERNED),
        net_benefit_thb=net,
        assumptions=["round-trip fixture"],
    )
    return impact.model_dump(mode="json")


def _agent() -> Agent:
    return Agent(
        agent_id="pond_agent",
        name="Pond Agent",
        autonomy_ceiling=Autonomy.AUTO,
        allowed=AgentAllowed(action_handlers=["echo"]),
    )


def _procedure() -> Procedure:
    return Procedure(
        procedure_id="impact_round",
        title="Impact Round",
        goal="Emit a economic-impact facet and complete.",
        run_by="pond_agent",
        steps=[Step(step_id="read", name="Read", kind=StepKind.QUERY)],
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


async def _persist(engine: AsyncEngine, detail: dict[str, Any], run_id: str) -> None:
    executors: dict[StepKind, StepExecutor] = {StepKind.QUERY: _ImpactExec(detail)}
    result = await run_procedure(
        _procedure(), _agent(), executors, vertical="aquaculture", run_id=run_id
    )
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        await persist_run(session, result)


async def test_emitted_decimal_survives_the_real_persistence_path(
    db_engine: AsyncEngine,
) -> None:
    await _persist(db_engine, _impact_detail(_NET), "run-impact")
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as fresh:
        buckets = await benefit_rollup(fresh)

    assert len(buckets) == 1, "one facet -> one bucket"
    bucket = buckets[0]
    assert bucket.currency == "THB"
    assert bucket.procedure_id == "impact_round"
    assert bucket.facet_kind == "avoided_outage"
    assert bucket.facet_count == 1
    assert bucket.figures_missing == 0
    # The exact Decimal, not a float that happens to compare close.
    assert bucket.net_benefit_thb_sum == _NET
    assert isinstance(bucket.net_benefit_thb_sum, Decimal)


async def test_a_malformed_facet_through_the_real_path_is_counted_not_raised(
    db_engine: AsyncEngine,
) -> None:
    """ADR-0030 never-raise, asserted on the write path the orchestrator uses."""
    broken = {"currency": "THB", "kind": "avoided_outage", "net_benefit_thb": "not-a-number"}
    await _persist(db_engine, broken, "run-broken")
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as fresh:
        buckets = await benefit_rollup(fresh)

    assert len(buckets) == 1
    assert buckets[0].facet_count == 1
    assert buckets[0].figures_missing == 1
    assert buckets[0].net_benefit_thb_sum == Decimal(0)
