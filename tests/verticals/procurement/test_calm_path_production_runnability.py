"""PLAN-0065 (SD-4, AC-2) — the calm-path ``low_stock_reorder_round`` runs END-TO-END on
the PRODUCTION factory.

Before this PLAN the production chain CRASHED at ``judge_stock``: post-PLAN-0064 the
declared ``read_stock`` routes to the shipped ``QueryStepExecutor`` over the
registry-registered ``ProcurementSyntheticAdapter`` and returns raw ``Part`` rows carrying
``stock_qty`` — but the shipped ``EvaluateStepExecutor`` reads ``measured_value`` and fails
loudly on entities without one. The ``read_stock`` rename-projection
(``stock_qty -> measured_value``) closes exactly that gap.

The existing event-based calm-path test (``test_procurement_vertical.py``) feeds test-local
``OperationalEvent`` rows that already carry ``measured_value``, so it never exercised the
``Part``-row production path — this test does, through the REAL factory executors and the
REAL ``run_procedure``.

In-memory, offline, no DB, no MS-S1 (the synthetic adapter is deterministic; L-1 no LLM).
"""

from __future__ import annotations

from services.engine.discovery import discover_and_register
from services.engine.procedures.orchestrator import run_procedure
from services.engine.procedures.runs import PipelineRunStatus
from services.engine.procedures.spec import load_procedures
from services.engine.registry import registry
from verticals.procurement.hero_demo.run import register_procurement_procedure_executors

_VERTICAL = "procurement"
_PROC_ID = "low_stock_reorder_round"


async def test_calm_path_runs_end_to_end_on_the_production_factory() -> None:
    """AC-2: the declared ``read_stock`` projection lets the shipped judge band the
    registered adapter's Part rows; the chain runs read -> judge -> reorder and SUSPENDS at
    the gated ``reorder`` (a machine never reorders — RF-3)."""
    discover_and_register()
    await register_procurement_procedure_executors()
    executors = registry.get_procedure_executors(_VERTICAL)()

    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == _PROC_ID)
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)

    result = await run_procedure(
        proc, agent, executors, vertical=_VERTICAL, run_id="proc-calm-prod"
    )

    # The chain runs to the gated reorder and SUSPENDS (no auto-reorder past the gate).
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    assert result.step_results[-1].step_id == "reorder"

    # read_stock served the registry-registered adapter's THREE Part rows (PLAN-0066 SD-4b
    # added the flip part), projected: stock_qty RENAMED to measured_value (moved, not
    # duplicated); reorder_point kept.
    read_sr = next(sr for sr in result.step_results if sr.step_id == "read_stock")
    assert read_sr.artifact is not None
    rows = read_sr.artifact["output_set"]
    assert len(rows) == 3
    assert all("measured_value" in r and "stock_qty" not in r for r in rows)
    assert all("reorder_point" in r for r in rows)
    assert sorted(float(r["measured_value"]) for r in rows) == [0.0, 40.0, 150.0]

    # judge_stock derived BOTH verdicts from measured_value vs the fixed 100.0 band:
    # spindle 0 <= 100 breach, filter 40 <= 100 breach (fact 9).
    judge_sr = next(sr for sr in result.step_results if sr.step_id == "judge_stock")
    assert judge_sr.artifact is not None
    verdicts = {e["part_no"]: e["verdict"] for e in judge_sr.artifact["output_set"]}
    # spindle 0 and filter 40 breach their own reorder points (1 / 100); the high-turnover
    # v-belt (150) breaches ITS 200 point — all three low vs their per-part band (SD-4b).
    assert verdicts == {
        "part-spindle-01": "breach",
        "part-filter-02": "breach",
        "part-vbelt-03": "breach",
    }
    assert judge_sr.audit is not None and judge_sr.audit.get("deterministic") is True


async def test_calm_path_per_part_band_flips_the_high_reorder_part() -> None:
    """PLAN-0066 AC-6 (SD-4b): the flip seed part ``part-vbelt-03`` (stock 150,
    reorder_point 200) is ``ok`` under a blanket-100 scalar but ``breach`` under per-part
    banding — the demo-visible win (a blanket threshold MISSES a genuinely-low high-reorder
    part). RED-verified: against the unedited ``threshold: 100.0`` YAML this assertion FAILS
    (the part judges ``ok``); the ``threshold_field: reorder_point`` migration makes it pass."""
    discover_and_register()
    await register_procurement_procedure_executors()
    executors = registry.get_procedure_executors(_VERTICAL)()

    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == _PROC_ID)
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)

    result = await run_procedure(
        proc, agent, executors, vertical=_VERTICAL, run_id="proc-calm-flip"
    )

    judge_sr = next(sr for sr in result.step_results if sr.step_id == "judge_stock")
    assert judge_sr.artifact is not None
    verdicts = {e["part_no"]: e["verdict"] for e in judge_sr.artifact["output_set"]}
    assert verdicts["part-vbelt-03"] == "breach"  # 150 <= 200 (per-part), NOT <= 100 (scalar)
