"""PLAN-0062 Step 1 (PR1b) — the energy production factory + the full-procedure run (AC-2, AC-5).
Judge re-themed to a per-feeder over-current band by PLAN-0070.

The half of AC-2 the parity module could not reach: the migrated ``read_readings``
grammar feeding ``judge`` **in situ**, through the executors the API actually
registers, all the way to the gated ``restart_breaches`` suspension. Offline and
host-state-free (SD-6): the QUERY step reads the synthetic adapter, the EVALUATE step
is deterministic per-row band math, and the ACTION step's advisory prose is stubbed — no
MS-S1 call anywhere (CLAUDE.md §8).

Why this test is the one that catches the real gap: a shape-only fixture never runs the
judge; this drives the real per-feeder band (``threshold_field: rated_current_a``) over the
FK-parent join. The energy factory still wires the ``EnvBandEvaluateExecutor`` wrapper
(PLAN-0070 SD-5a), whose guard delegates a ``threshold_field`` judge straight through (#709).
"""

from __future__ import annotations

import pytest

from services.api.config import settings
from services.engine.discovery import discover_and_register
from services.engine.procedures.env_band_step import EnvBandEvaluateExecutor
from services.engine.procedures.evaluate_step import EvaluateStepExecutor
from services.engine.procedures.orchestrator import run_procedure
from services.engine.procedures.query_step import QueryStepExecutor
from services.engine.procedures.runs import PipelineRunStatus
from services.engine.procedures.spec import StepKind, load_procedures
from services.engine.registry import ExecutorFactory, RegistryError, registry
from verticals.energy.procedures_factory import register_energy_procedure_executors

_VERTICAL = "energy"
_PROCEDURE_ID = "substation_health_sweep"
_OVERLOADED_FEEDER = "asset-meter-01"  # 84 A latest vs its OWN 80 A rating → breach


@pytest.fixture
async def energy_factory(monkeypatch: pytest.MonkeyPatch) -> ExecutorFactory:
    """The registered energy factory over a pinned band + a fixed (un-anchored) clock —
    the same registration path ``services/api/main.py`` runs at startup."""
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    monkeypatch.setattr(settings, "oct_recommend_threshold", 90.0)
    monkeypatch.setattr(settings, "oct_recommend_direction", "above")
    discover_and_register()  # adapters + handlers only (OQ-6) — no executor factory
    await register_energy_procedure_executors()
    return registry.get_procedure_executors(_VERTICAL)


async def test_registration_is_required_then_idempotent() -> None:
    """``discover_and_register`` alone leaves the vertical without a factory (the 409
    the resolve endpoint raises); registering twice is a no-op, never a RegistryError."""
    discover_and_register()
    with pytest.raises(RegistryError, match="no procedure-executor factory"):
        registry.get_procedure_executors(_VERTICAL)

    await register_energy_procedure_executors()
    await register_energy_procedure_executors()  # idempotent

    assert registry.get_procedure_executors(_VERTICAL) is not None


async def test_factory_binds_the_three_step_kinds_energy_needs(
    energy_factory: ExecutorFactory,
) -> None:
    """AC-5: the QUERY executor carries the REAL ontology meta (so the declared
    latest-per-group grammar executes on the production path, not just in tests), the
    EVALUATE executor is the env-band wrapper over the SHIPPED base, and each call
    builds a fresh executor map (the registry Step-2 no-leak contract)."""
    executors = energy_factory()

    # PLAN-0078 Step 1: TRANSFORM joins the exact key set (shared fieldless executor, all 4
    # factories, pure-additive — inert until a procedure declares a transform).
    assert set(executors) == {
        StepKind.QUERY,
        StepKind.EVALUATE,
        StepKind.ACTION,
        StepKind.TRANSFORM,
    }
    query = executors[StepKind.QUERY]
    assert isinstance(query, QueryStepExecutor)
    assert query.meta is not None
    assert "OperationalEvent" in query.object_type_names

    evaluate = executors[StepKind.EVALUATE]
    assert isinstance(evaluate, EnvBandEvaluateExecutor)
    assert isinstance(evaluate.base, EvaluateStepExecutor)

    assert energy_factory()[StepKind.QUERY] is not query, "executors must be built per request"


async def test_full_procedure_run_suspends_at_the_gated_restart(
    energy_factory: ExecutorFactory,
) -> None:
    """AC-2 (the full-run half): read_readings -> judge -> restart_breaches over the REAL
    energy YAML + ontology + synthetic adapter. The run suspends at ``waiting_human`` —
    the gated restart is PROPOSED, never executed."""
    spec = load_procedures(_VERTICAL)
    procedure = next(p for p in spec.procedures if p.procedure_id == _PROCEDURE_ID)
    agent = next(a for a in spec.agents if a.agent_id == procedure.run_by)

    result = await run_procedure(
        procedure, agent, energy_factory(), vertical=_VERTICAL, run_id="energy-pr1b-e2e"
    )

    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    by_step = {step.step_id: step for step in result.step_results}
    assert set(by_step) == {"read_readings", "judge", "restart_breaches"}

    # the migrated grammar fed the judge in situ: one latest CURRENT reading per feeder, judged
    readings = by_step["read_readings"].artifact["output_set"]
    assert readings, "the declared current-narrowed read produced no rows"
    assert all(row["event_type"] == "reading" for row in readings)

    judged = by_step["judge"].artifact["output_set"]
    assert {row["asset_id"] for row in judged} == {row["asset_id"] for row in readings}
    breaches = [row for row in judged if row["verdict"] == "breach"]
    assert [row["asset_id"] for row in breaches] == [_OVERLOADED_FEEDER]

    # PLAN-0070: the verdict is the per-feeder (in_file) band, NOT the blanket env threshold —
    # the migrated judge records its threshold_field and carries no band_source="env" stamp.
    assert by_step["judge"].audit.get("threshold_field") == "rated_current_a"
    assert by_step["judge"].audit.get("band_source") != "env"

    # the gated action fanned out over the breach subset ONLY, and proposed (not executed)
    actions = by_step["restart_breaches"].artifact["output_set"]
    assert len(actions) == 1
    assert actions[0]["status"] == "proposed"
    assert actions[0]["action"]["suggested_handler"] == "restart"
