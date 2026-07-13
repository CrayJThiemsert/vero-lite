"""PLAN-0068 PR2 — aquaculture ``morning_pond_health_round`` runs END-TO-END with
per-species ``do_floor`` banding on the production factory.

The migrated ``read_do`` JOINS each latest reading to its Pond's band
(``event_emitted_by_pond``), so ``do_floor`` rides onto the judged rows (the base
OperationalEvent columns preserved, the Pond band a strict addition — the declared
``site_id`` collision renamed to ``pond_site_id``). The migrated ``judge`` bands each
pond's latest reading against its OWN ``threshold_field: do_floor`` (in_file
per-entity, ``direction: below`` floor + ``watch_margin: 1.0``) instead of one blanket
4 mg/L floor — so pond-11 (tiger_prawn) WARMING to 4.2 mg/L breaches its own 4.5 floor
though a blanket 4.0 limit would clear it to ``watch`` (the per-species demo win).

In-memory, offline, no DB, no MS-S1 (the synthetic adapter is deterministic; L-1 no LLM).
"""

from __future__ import annotations

from services.engine.discovery import discover_and_register
from services.engine.procedures.orchestrator import RunResult, run_procedure
from services.engine.procedures.runs import PipelineRunStatus
from services.engine.procedures.spec import load_procedures
from services.engine.registry import registry
from verticals.aquaculture.procedures_factory import register_aquaculture_procedure_executors

_VERTICAL = "aquaculture"
_PROC_ID = "morning_pond_health_round"


async def _run() -> RunResult:
    discover_and_register()
    await register_aquaculture_procedure_executors()
    executors = registry.get_procedure_executors(_VERTICAL)()

    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == _PROC_ID)
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    return await run_procedure(proc, agent, executors, vertical=_VERTICAL, run_id="aq-per-species")


async def test_morning_round_runs_end_to_end_with_per_species_floors() -> None:
    """AC-6/AC-7: the migrated join ``read_do`` + per-entity ``judge`` run
    read -> judge -> aerate and SUSPEND at the gated ``aerate`` (a machine never
    aerates — the operator decides). AC-5: ``do_floor`` (a joined Pond column) rides
    onto the base reading rows, which keep their own ``measured_value``."""
    result = await _run()

    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    assert result.step_results[-1].step_id == "aerate"

    read_sr = next(sr for sr in result.step_results if sr.step_id == "read_do")
    assert read_sr.artifact is not None
    rows = read_sr.artifact["output_set"]
    # ponds with readings: pond-07 (crash), pond-03 (nominal), pond-11 (flip). pond-05 is fallow.
    assert {r["pond_id"] for r in rows} == {"pond-07", "pond-03", "pond-11"}
    assert all("measured_value" in r and "do_floor" in r for r in rows)
    floors = {r["pond_id"]: r["do_floor"] for r in rows}
    assert floors == {"pond-07": 4.0, "pond-03": 4.0, "pond-11": 4.5}

    judge_sr = next(sr for sr in result.step_results if sr.step_id == "judge")
    assert judge_sr.artifact is not None
    verdicts = {e["pond_id"]: e["verdict"] for e in judge_sr.artifact["output_set"]}
    assert verdicts == {"pond-07": "breach", "pond-03": "ok", "pond-11": "breach"}
    # the migrated in_file judge names the per-entity column, never env provenance.
    assert judge_sr.audit is not None
    assert judge_sr.audit["threshold"] is None
    assert judge_sr.audit["threshold_field"] == "do_floor"
    assert "band_source" not in judge_sr.audit


async def test_per_species_floor_flips_the_warming_tiger_prawn_pond() -> None:
    """SD-3, the demo win (RED-verified). pond-11 (tiger_prawn) warms to 4.2 mg/L —
    only ``watch`` under a blanket 4.0 floor but ``breach`` under its OWN 4.5 floor:
    a blanket limit MISSES a genuinely-stressed sensitive-species pond. Against the
    unedited blanket-4.0 judge this assertion FAILS (pond-11 judges ``watch``, the
    breach set is {pond-07} only); the ``threshold_field: do_floor`` migration makes
    it pass (breach set grows to {pond-07, pond-11})."""
    result = await _run()

    judge_sr = next(sr for sr in result.step_results if sr.step_id == "judge")
    assert judge_sr.artifact is not None
    verdicts = {e["pond_id"]: e["verdict"] for e in judge_sr.artifact["output_set"]}
    # 4.2 <= 4.5 (its own floor) breaches; 4.2 is NOT <= 4.0 (a blanket limit -> watch).
    assert verdicts["pond-11"] == "breach"

    aerate_sr = next(sr for sr in result.step_results if sr.step_id == "aerate")
    assert aerate_sr.artifact is not None
    # the gated aerate fans out over the breach subset only: pond-07 crash + pond-11 flip.
    assert len(aerate_sr.artifact["output_set"]) == 2
