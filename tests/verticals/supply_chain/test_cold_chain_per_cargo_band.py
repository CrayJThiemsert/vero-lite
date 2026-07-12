"""PLAN-0067 PR2 (ADR-016 FKP amendment 2026-07-12) — supply_chain
``cold_chain_excursion_sweep`` runs END-TO-END with per-cargo ``temp_ceiling``
banding on the PRODUCTION factory.

The migrated ``read_temps`` JOINS each latest reading to its Shipment's cargo band
(``event_concerns_shipment``), so ``temp_ceiling`` rides onto the judged rows (AC-5:
base OperationalEvent columns preserved, the Shipment band a strict addition). The
migrated ``judge`` bands each shipment's latest reading against its OWN
``threshold_field: temp_ceiling`` (in_file per-entity) instead of one blanket env
ceiling — so the frozen shipment WARMING to -11.8 °C (above its -15 °C frozen ceiling)
breaches, though a blanket 8 °C limit would clear it (the per-cargo demo win).

In-memory, offline, no DB, no MS-S1 (the synthetic adapter is deterministic; L-1 no LLM).
"""

from __future__ import annotations

from services.engine.discovery import discover_and_register
from services.engine.procedures.orchestrator import RunResult, run_procedure
from services.engine.procedures.runs import PipelineRunStatus
from services.engine.procedures.spec import load_procedures
from services.engine.registry import registry
from verticals.supply_chain.procedures_factory import (
    register_supply_chain_procedure_executors,
)

_VERTICAL = "supply_chain"
_PROC_ID = "cold_chain_excursion_sweep"


async def _run() -> RunResult:
    discover_and_register()
    await register_supply_chain_procedure_executors()
    executors = registry.get_procedure_executors(_VERTICAL)()

    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == _PROC_ID)
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    return await run_procedure(proc, agent, executors, vertical=_VERTICAL, run_id="sc-cold-band")


async def test_cold_chain_runs_end_to_end_with_per_cargo_band() -> None:
    """AC-6/AC-7: the migrated join read_temps + per-entity judge run read -> judge ->
    hold and SUSPEND at the gated ``hold_breaches`` (a machine never holds — the operator
    decides). AC-5: temp_ceiling (a joined Shipment column) rides onto the base reading
    rows, which keep their own ``measured_value``."""
    result = await _run()

    # The chain runs to the gated hold and SUSPENDS (no auto-hold past the gate).
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    assert result.step_results[-1].step_id == "hold_breaches"

    # AC-5: read_temps joined Shipment onto each latest reading — the base OperationalEvent
    # column (measured_value) is preserved AND the Shipment band (temp_ceiling) is added.
    read_sr = next(sr for sr in result.step_results if sr.step_id == "read_temps")
    assert read_sr.artifact is not None
    rows = read_sr.artifact["output_set"]
    assert {r["shipment_id"] for r in rows} == {"shipment-pharma-01", "shipment-frozen-01"}
    assert all("measured_value" in r and "temp_ceiling" in r for r in rows)
    ceilings = {r["shipment_id"]: r["temp_ceiling"] for r in rows}
    assert ceilings == {"shipment-pharma-01": 8.0, "shipment-frozen-01": -15.0}

    # AC-6: the judge bands each shipment vs ITS OWN temp_ceiling (in_file per-entity).
    judge_sr = next(sr for sr in result.step_results if sr.step_id == "judge")
    assert judge_sr.artifact is not None
    verdicts = {e["shipment_id"]: e["verdict"] for e in judge_sr.artifact["output_set"]}
    assert verdicts == {"shipment-pharma-01": "breach", "shipment-frozen-01": "breach"}
    assert judge_sr.audit is not None and judge_sr.audit.get("deterministic") is True
    # the migrated in_file judge must NOT claim env provenance (the PR1 env_band guard fix).
    assert "band_source" not in judge_sr.audit


async def test_per_cargo_band_flips_the_warming_frozen_shipment() -> None:
    """AC-6 (SD-2b): the frozen shipment WARMS to -11.8 °C — ``ok`` under a blanket 8 °C
    ceiling but ``breach`` under its OWN -15 °C frozen ceiling (the demo-visible win: a
    blanket limit MISSES a thawing frozen shipment). RED-verified: against the unedited
    env_band YAML this assertion FAILS (frozen judges ``ok``); the ``threshold_field:
    temp_ceiling`` migration makes it pass."""
    result = await _run()

    judge_sr = next(sr for sr in result.step_results if sr.step_id == "judge")
    assert judge_sr.artifact is not None
    verdicts = {e["shipment_id"]: e["verdict"] for e in judge_sr.artifact["output_set"]}
    # -11.8 > -15.0 (its own frozen ceiling) breaches; -11.8 is NOT > 8.0 (a blanket limit).
    assert verdicts["shipment-frozen-01"] == "breach"
