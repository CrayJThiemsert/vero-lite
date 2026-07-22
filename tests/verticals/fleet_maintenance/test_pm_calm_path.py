"""PLAN-0089 (AC-2 / AC-3) — the AT-3 PM calm path ``pm_service_round`` runs END-TO-END on
the PRODUCTION fleet_maintenance factory, and does so WITHOUT touching the AT-2 hero.

The calm path is the routine contrast to the vertical's governed-repair hero: one deterministic
per-truck km band, ONE human go/no-go, and nothing else — no ``doa_tier``, no SoD, no
``rule_gate``, no emergency waiver. That ABSENCE is the AT-3 signature, so the tests below assert
it directly rather than only asserting the happy path.

Mirrors ``tests/verticals/procurement/test_calm_path_production_runnability.py`` (the AT-3 donor)
through the REAL factory executors and the REAL ``run_procedure``.

In-memory, offline, no DB, no MS-S1 — the synthetic adapter is deterministic and no step carries
``llm_assist``.
"""

from __future__ import annotations

from services.engine.discovery import discover_and_register
from services.engine.procedures.orchestrator import run_procedure
from services.engine.procedures.runs import PipelineRunStatus
from services.engine.procedures.spec import load_procedures
from services.engine.registry import registry
from verticals.fleet_maintenance.procedures_factory import (
    register_fleet_maintenance_procedure_executors,
)

_VERTICAL = "fleet_maintenance"
_PROC_ID = "pm_service_round"
_HERO_ID = "governed_repair_approval"


async def _run(run_id: str):  # type: ignore[no-untyped-def]  # the orchestrator's result dataclass
    """Build the PRODUCTION factory and run the calm path once."""
    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    executors = registry.get_procedure_executors(_VERTICAL)()

    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == _PROC_ID)
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    return await run_procedure(proc, agent, executors, vertical=_VERTICAL, run_id=run_id)


async def test_pm_calm_path_runs_end_to_end_and_parks_at_the_gate() -> None:
    """AC-2: read -> judge -> schedule_service, suspending at the gated terminal.

    The rename-projection (``odometer_km -> measured_value``) is what lets the shipped
    ``EvaluateStepExecutor`` band raw ``Truck`` rows at all — it reads ``measured_value`` and
    fails loudly without one. The rename MOVES the field, so ``odometer_km`` is gone downstream
    while ``next_service_due_km`` (the band column) rides through untouched.
    """
    result = await _run("fleet-pm-calm-prod")

    # A machine never books the service past the gate — the run SUSPENDS for a human.
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    assert result.step_results[-1].step_id == "schedule_service"

    read_sr = next(sr for sr in result.step_results if sr.step_id == "read_odometer")
    assert read_sr.artifact is not None
    rows = read_sr.artifact["output_set"]
    # all THREE synthetic trucks are swept (PLAN-0089 SD-3's ratified third truck)
    assert len(rows) == 3
    # the rename MOVED odometer_km; the band column survived the fields-only projection
    assert all("measured_value" in r and "odometer_km" not in r for r in rows)
    assert all("next_service_due_km" in r for r in rows)
    assert sorted(float(r["measured_value"]) for r in rows) == [254_300.0, 412_580.0, 688_140.0]


async def test_pm_calm_path_bands_each_truck_against_its_own_due_point() -> None:
    """AC-2: per-truck banding via ``threshold_field``, direction ``above``.

    The inverted direction is the whole point of this instance — procurement's AT-3 breaches
    BELOW a reorder floor; a truck breaches ABOVE its service-due ceiling. Exactly ONE truck is
    due, so the breach set is a real subset rather than everything or nothing:

    * truck-01 412,580 < 500,000 -> ok   (the HERO's breakdown truck is NOT also PM-flagged)
    * truck-02 688,140 >= 685,000 -> breach (3,140 km overdue — the calm path's story)
    * truck-03 254,300 < 300,000 -> ok   (45,700 km of headroom)
    """
    result = await _run("fleet-pm-calm-band")

    judge_sr = next(sr for sr in result.step_results if sr.step_id == "judge_service_due")
    assert judge_sr.artifact is not None
    verdicts = {e["truck_id"]: e["verdict"] for e in judge_sr.artifact["output_set"]}
    assert verdicts == {"truck-01": "ok", "truck-02": "breach", "truck-03": "ok"}
    assert judge_sr.audit is not None and judge_sr.audit.get("deterministic") is True

    # the gated terminal proposes for ONLY the due subset (input.where.verdict: breach) —
    # ONE proposal, still `proposed`, fixed to the calm-path handler by the spec (ADR-016).
    gate_sr = next(sr for sr in result.step_results if sr.step_id == "schedule_service")
    assert gate_sr.artifact is not None
    proposals = gate_sr.artifact["output_set"]
    assert len(proposals) == 1
    assert all(p["status"] == "proposed" for p in proposals)
    assert all(p["action"]["suggested_handler"] == "schedule_pm_service" for p in proposals)


async def test_pm_calm_path_carries_no_at2_governance_artifacts() -> None:
    """AC-3: the AT-3 signature is an ABSENCE, asserted rather than assumed.

    The fleet factory constructs its ACTION slot with ``advisory_builder=GateAdvisoryBuilder()``
    (PLAN-0086 L-B — this vertical ships the gate advisory ON). That advisory is ``doa_tier``-only
    by construction, NOT merely never-raising: ``GovernanceActionExecutor.execute`` branches on
    ``step.governance_content`` and delegates straight to the base executor when there is none,
    and the builder is invoked only inside ``_doa_tier``
    (``services/engine/procedures/governance_step.py:183-191``, ``:235-238``). A calm-path gated
    action therefore never reaches the advisory at all.

    So the parked step must carry NO ``advisory_recommendation`` and NO ``doa_tier_resolved``
    trace entry, and NO ``governed_kind`` audit key. If a future change routes AT-3 through the
    governance path, this goes RED — which is the intent.
    """
    result = await _run("fleet-pm-calm-absence")

    gate_sr = next(sr for sr in result.step_results if sr.step_id == "schedule_service")
    trace_kinds = {entry.get("kind") for entry in (gate_sr.reasoning_trace or [])}
    assert "advisory_recommendation" not in trace_kinds
    assert "doa_tier_resolved" not in trace_kinds
    assert "governed_kind" not in (gate_sr.audit or {})

    # and the spec itself carries none of the AT-2 apparatus
    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == _PROC_ID)
    assert proc.separation_of_duties == []
    assert all(step.governance_content is None for step in proc.steps)


async def test_pm_calm_path_does_not_disturb_the_at2_hero() -> None:
    """AC-3: additivity — the second procedure leaves the first intact.

    Both procedures ride ONE per-StepKind executor mapping, so a calm-path change could in
    principle reach the hero. This pins the vertical's shape (exactly two procedures, one AT-2
    with its full apparatus and one AT-3 with none) so a regression is named, not inferred.
    """
    spec = load_procedures(_VERTICAL)
    assert {p.procedure_id for p in spec.procedures} == {_HERO_ID, _PROC_ID}

    hero = next(p for p in spec.procedures if p.procedure_id == _HERO_ID)
    # the hero keeps its AT-2 apparatus, untouched by the extension
    assert hero.separation_of_duties != []
    assert any(step.governance_content is not None for step in hero.steps)
    assert spec.compliance_criteria == ["three_quote"]
