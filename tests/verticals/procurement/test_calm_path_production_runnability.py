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

    # read_stock served the registry-registered adapter's Part rows — since PLAN-0084
    # SD-F the registered adapter is the FastenalCsvAdapter (FIVE parts, canonical
    # part_no) — projected: stock_qty RENAMED to measured_value (moved, not
    # duplicated); reorder_point kept.
    read_sr = next(sr for sr in result.step_results if sr.step_id == "read_stock")
    assert read_sr.artifact is not None
    rows = read_sr.artifact["output_set"]
    assert len(rows) == 5
    assert all("measured_value" in r and "stock_qty" not in r for r in rows)
    assert all("reorder_point" in r for r in rows)
    assert sorted(float(r["measured_value"]) for r in rows) == [0.0, 2.0, 8.0, 60.0, 150.0]

    # judge_stock bands each part vs ITS OWN reorder_point (threshold_field, SD-4b):
    # spindle 0<=1 breach (the hero out-of-stock spare) · belt 150<=160 breach (the
    # >100 flip case) · seal-kit 8<=12 breach (the calm low-stock consumable) ·
    # servo 2>1 ok · collet 60>20 ok.
    judge_sr = next(sr for sr in result.step_results if sr.step_id == "judge_stock")
    assert judge_sr.artifact is not None
    verdicts = {e["part_no"]: e["verdict"] for e in judge_sr.artifact["output_set"]}
    assert verdicts == {
        "PRT-SPN-700": "breach",
        "PRT-BLT-110": "breach",
        "PRT-HYD-450": "breach",
        "PRT-SVO-220": "ok",
        "PRT-CTR-880": "ok",
    }
    assert judge_sr.audit is not None and judge_sr.audit.get("deterministic") is True


async def test_calm_path_per_part_band_flips_the_high_reorder_part() -> None:
    """PLAN-0066 AC-6 (SD-4b): the flip part — now the Fastenal ``PRT-BLT-110`` (stock
    150, reorder_point 160, mirroring the retired synthetic ``part-vbelt-03`` 150/200) —
    is ``ok`` under a blanket-100 scalar but ``breach`` under per-part banding — the
    demo-visible win (a blanket threshold MISSES a genuinely-low high-reorder part).
    The original RED-proof ran against the synthetic row (PLAN-0066); the semantics are
    preserved verbatim in the Fastenal fixture (PLAN-0084 SD-F primary-adapter swap)."""
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
    assert verdicts["PRT-BLT-110"] == "breach"  # 150 <= 160 (per-part), NOT <= 100 (scalar)
