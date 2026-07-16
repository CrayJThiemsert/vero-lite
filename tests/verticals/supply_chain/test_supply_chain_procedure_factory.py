"""PLAN-0062 Step 2 (PR2) — the supply_chain production factory + full-procedure run (AC-3, AC-5).

The energy PR1b test, re-pointed at the cold chain. What it proves beyond a copy: the
shared engine executors (QueryStepExecutor / EnvBandEvaluateExecutor / advisory stub) are
genuinely **vertical-agnostic** — a second vertical binds them with no engine change. The
``judge`` migrated env_band -> per-cargo ``threshold_field: temp_ceiling`` (PLAN-0067,
ADR-016 FKP), so it now delegates THROUGH the still-registered EnvBandEvaluateExecutor.

Offline and host-state-free (SD-6): synthetic adapter, deterministic band math, stubbed
advisory prose — no MS-S1 call anywhere (CLAUDE.md §8).
"""

from __future__ import annotations

import pytest

from services.api.config import settings
from services.engine.discovery import discover_and_register
from services.engine.procedures.action_step import ActionStepExecutor
from services.engine.procedures.env_band_step import EnvBandEvaluateExecutor
from services.engine.procedures.evaluate_step import EvaluateStepExecutor
from services.engine.procedures.governance_step import (
    GovernanceActionExecutor,
    GovernanceEvaluateExecutor,
)
from services.engine.procedures.orchestrator import run_procedure
from services.engine.procedures.query_router import QueryStepRouter
from services.engine.procedures.query_step import QueryStepExecutor
from services.engine.procedures.runs import PipelineRunStatus
from services.engine.procedures.spec import StepKind, load_procedures
from services.engine.registry import ExecutorFactory, RegistryError, registry
from verticals.supply_chain.cold_chain_assess import ColdChainAssessExecutor
from verticals.supply_chain.procedures_factory import register_supply_chain_procedure_executors

_VERTICAL = "supply_chain"
_PROCEDURE_ID = "cold_chain_excursion_sweep"
_INCIDENT_SHIPMENT = "shipment-pharma-01"
_COLD_CHAIN_CEILING = 8.0


@pytest.fixture
async def supply_chain_factory(monkeypatch: pytest.MonkeyPatch) -> ExecutorFactory:
    """The registered supply_chain factory over the COLD-CHAIN band (8 °C, above) and a
    fixed clock — the same registration path ``services/api/main.py`` runs at startup."""
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    monkeypatch.setattr(settings, "oct_recommend_threshold", _COLD_CHAIN_CEILING)
    monkeypatch.setattr(settings, "oct_recommend_direction", "above")
    discover_and_register()  # adapters + handlers only (OQ-6) — no executor factory
    await register_supply_chain_procedure_executors()
    return registry.get_procedure_executors(_VERTICAL)


async def test_registration_is_required_then_idempotent() -> None:
    """``discover_and_register`` alone leaves the vertical without a factory (the 409 the
    resolve endpoint raises); registering twice is a no-op, never a RegistryError."""
    discover_and_register()
    with pytest.raises(RegistryError, match="no procedure-executor factory"):
        registry.get_procedure_executors(_VERTICAL)

    await register_supply_chain_procedure_executors()
    await register_supply_chain_procedure_executors()  # idempotent

    assert registry.get_procedure_executors(_VERTICAL) is not None


async def test_factory_reuses_the_shared_engine_executors(
    supply_chain_factory: ExecutorFactory,
) -> None:
    """AC-5: the shared engine executors are still what does the work — now reached THROUGH the
    AT-2 wrappers the second procedure needs (PLAN-0074 Step 4). Each slot is a delegating wrapper
    over the SAME shipped executor the vertical bound before (no per-vertical band class, no
    per-vertical query executor), so the AT-3 sweep's path is unchanged — proven behaviourally by
    ``test_full_procedure_run_suspends_at_the_gated_hold`` below, which is untouched.

    Each call still builds a fresh map (the registry Step-2 no-leak contract)."""
    executors = supply_chain_factory()

    # PLAN-0078 Step 1: TRANSFORM joins the exact key set (shared fieldless executor, all 4
    # factories, pure-additive — inert until the PR-2 intake flip declares one).
    assert set(executors) == {
        StepKind.QUERY,
        StepKind.EVALUATE,
        StepKind.ACTION,
        StepKind.TRANSFORM,
    }

    # QUERY: routed per step (PLAN-0064 declaration-presence). The sweep's `read_temps` DECLARES
    # reads -> the shipped QueryStepExecutor over the REAL ontology meta (as before); the
    # disposition's undeclared `intake` takes the seed leg.
    query = executors[StepKind.QUERY]
    assert isinstance(query, QueryStepRouter)
    declared = query.declared
    assert isinstance(declared, QueryStepExecutor)
    assert declared.meta is not None
    assert "Shipment" in declared.object_type_names

    # EVALUATE: the rule_gate dispatcher over the SAME EnvBandEvaluateExecutor energy binds, over
    # the SAME shipped band executor — the sweep's banded `judge` falls through both wrappers.
    evaluate = executors[StepKind.EVALUATE]
    assert isinstance(evaluate, GovernanceEvaluateExecutor)
    assert isinstance(evaluate.base, EnvBandEvaluateExecutor)
    assert isinstance(evaluate.base.base, EvaluateStepExecutor)

    # ACTION: the vertical's severity stamp (assess only) over the shipped AT-2 governance wrapper
    # over the shipped ActionStepExecutor — the sweep's `hold_breaches` reaches the base untouched.
    action = executors[StepKind.ACTION]
    assert isinstance(action, ColdChainAssessExecutor)
    assert action.stamp_steps == frozenset({"assess"})
    assert isinstance(action.inner, GovernanceActionExecutor)
    assert isinstance(action.inner.base, ActionStepExecutor)
    # SoD steps are DERIVED from the spec's own constraints, never hardcoded (no rename drift)
    assert action.inner.sod_steps == frozenset({"intake", "approve"})
    assert [p.person_id for p in action.inner.principals] == [
        "req-coldchain",
        "appr-qa",
        "appr-qam",
        "appr-qp",
        "appr-qdir",
    ]

    assert supply_chain_factory()[StepKind.QUERY] is not query, "executors are per-request"


async def test_full_procedure_run_suspends_at_the_gated_hold(
    supply_chain_factory: ExecutorFactory,
) -> None:
    """AC-3 (the full-run half): read_temps -> judge -> hold_breaches over the REAL
    supply_chain YAML + ontology + synthetic adapter. The run suspends at
    ``waiting_human`` — the gated hold is PROPOSED, never executed."""
    spec = load_procedures(_VERTICAL)
    procedure = next(p for p in spec.procedures if p.procedure_id == _PROCEDURE_ID)
    agent = next(a for a in spec.agents if a.agent_id == procedure.run_by)

    result = await run_procedure(
        procedure, agent, supply_chain_factory(), vertical=_VERTICAL, run_id="sc-pr2-e2e"
    )

    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    by_step = {step.step_id: step for step in result.step_results}
    assert set(by_step) == {"read_temps", "judge", "hold_breaches"}

    # the migrated grammar fed the judge in situ; the door-open alarm never reached it
    readings = by_step["read_temps"].artifact["output_set"]
    assert readings, "the declared latest-per-group read produced no rows"
    assert all(row["event_type"] == "reading" for row in readings)
    assert all("measured_value" in row for row in readings), "an alarm row would break the judge"

    judged = by_step["judge"].artifact["output_set"]
    breaches = [row for row in judged if row["verdict"] == "breach"]
    # PLAN-0067 (SD-2b): per-cargo banding makes the frozen shipment breach too — it warmed
    # to -11.8 °C, above its OWN -15 °C ceiling (a blanket 8 °C would clear it) — so the hold
    # set grew 1 -> 2. pharma still breaches (14.6 °C above its 8 °C ceiling).
    assert {row["shipment_id"] for row in breaches} == {
        "shipment-pharma-01",
        "shipment-frozen-01",
    }

    # PLAN-0067: the judge migrated env_band -> threshold_field (in_file per-entity), so it
    # delegates THROUGH EnvBandEvaluateExecutor untouched — no env band_source, no scalar band.
    judge_audit = by_step["judge"].audit
    assert "band_source" not in judge_audit
    assert judge_audit["threshold_field"] == "temp_ceiling"
    assert judge_audit["threshold"] is None

    # the gated action fanned out over the breach subset (both breaches), and proposed only
    actions = by_step["hold_breaches"].artifact["output_set"]
    assert len(actions) == 2
    assert actions[0]["status"] == "proposed"
    assert actions[0]["action"]["suggested_handler"] == "hold"
