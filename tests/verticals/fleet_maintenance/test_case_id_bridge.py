"""PLAN-0096 Step 2 / AC-3 — the case_id bridge, end to end and offline.

AC-3 has two halves. The API half (open a case from a phone, attach a photo,
persist it) is DB-backed and lives in ``tests/api/test_cases_endpoint.py``, where it
SKIPS without Postgres. This module is the other half — **the link survives the
run** — and it is deliberately DB-free so it can never skip: it is the assertion
that actually earns the KPI.

Why that framing matters. The partner's charter (Q16) is *"ตอบได้ทุกบาทว่า เงินซ่อม
ก้อนนี้ ใครอนุมัติ ซื้อจากใคร ทำไมซื้อ"*. Answering per baht means walking from an
approved spend BACK to the case that opened at minute 1 — the photo, the person, the
timestamp from before anyone had a number. If ``case_id`` is dropped anywhere between
the event and the gate, that walk breaks and the KPI is unanswerable no matter how
good the case UI is. So the thing under test is not "the field exists", it is
"the field is still on the row the DOA gate routed".

Offline + host-state-free (CLAUDE.md §8): synthetic adapter, real query/transform/
governance executors, stubbed advisory prose — no DB, no MS-S1, no network.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from services.api.config import settings
from services.engine.discovery import discover_and_register
from services.engine.procedures.orchestrator import run_procedure
from services.engine.procedures.runs import PipelineRunStatus, StepResult
from services.engine.procedures.spec import load_procedures
from services.engine.registry import ExecutorFactory, registry
from verticals.fleet_maintenance.data_adapter.synthetic import operational_events
from verticals.fleet_maintenance.procedures_factory import (
    register_fleet_maintenance_procedure_executors,
)

_VERTICAL = "fleet_maintenance"
_PROCEDURE_ID = "governed_repair_approval"

#: The two breaching quotes and the demo cases they belong to.
_BREACH_CASES = {
    Decimal("48000.0"): "case-demo-truck01-axle",
    Decimal("15000.0"): "case-demo-truck03-gearbox",
}


@pytest.fixture
async def fleet_factory(monkeypatch: pytest.MonkeyPatch) -> ExecutorFactory:
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    return registry.get_procedure_executors(_VERTICAL)


async def _run(factory: ExecutorFactory, run_id: str) -> dict[str, StepResult]:
    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == _PROCEDURE_ID)
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    result = await run_procedure(proc, agent, factory(), vertical=_VERTICAL, run_id=run_id)
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    return {step.step_id: step for step in result.step_results}


def _rows(step_result: StepResult) -> list[dict[str, Any]]:
    artifact = step_result.artifact
    assert artifact is not None, f"step '{step_result.step_id}' produced no artifact"
    return list(artifact["output_set"])


def test_only_the_breaching_quotes_carry_a_case_id() -> None:
    """The fixture links cases to breakdowns, NOT to routine consumables.

    A ฿1,800 filter change is the calm path, not a case anyone opened. Stamping a
    case id on it would be the easy way to make the traceability KPI look better
    than the operation actually is — every row 'traceable' because every row was
    handed an id by a fixture. This test is what stops that being a quiet edit."""
    by_value = {e["measured_value"]: e for e in operational_events()}
    for value, event in by_value.items():
        expected = _BREACH_CASES.get(Decimal(str(value)))
        assert event.get("case_id") == expected, f"{value}: {event.get('case_id')!r}"


async def test_case_id_survives_intake_reshape_and_the_doa_gate(
    fleet_factory: ExecutorFactory,
) -> None:
    """AC-3's load-bearing half: the id is still on the row the gate routed.

    Walked step by step rather than only checked at the end, because each hop drops
    fields for a different reason and a single end-assertion would not say WHICH hop
    lost it: ``intake`` projects/renames, ``judge`` tags a verdict, ``reshape`` runs
    declared transform ops, and ``approve`` resolves the tier. The id has to survive
    all four to be worth anything to the audit question.

    The fourth hop turned out to work differently from the first three, which is
    recorded inline below rather than smoothed over — the engine keeps the action
    envelope free of vertical fields on purpose, so the case link reaches the gate
    through the grounding trace and the amount-joinable reshape artifact instead."""
    by_step = await _run(fleet_factory, "fleet-case-bridge")

    intake_cases = {r.get("case_id") for r in _rows(by_step["intake"]) if r.get("case_id")}
    assert intake_cases == set(_BREACH_CASES.values())

    # the breach subset keeps its ids through the verdict tagging...
    judged = {r["case_id"] for r in _rows(by_step["judge"]) if r.get("verdict") == "breach"}
    assert judged == set(_BREACH_CASES.values())

    # ...and through the declared transform that builds the governed spend, which is
    # the hop most likely to drop it: a transform that rebuilt rows from its declared
    # ops instead of enriching them would silently lose every un-named field.
    reshaped = {Decimal(r["amount"]): r.get("case_id") for r in _rows(by_step["reshape"])}
    assert reshaped == _BREACH_CASES

    # The gate hop, and it works differently — a finding worth stating because Step 8's
    # export depends on it. A proposal is an ACTION ENVELOPE
    # (action_id / status / action / receipt), not an entity row, so it deliberately
    # carries no vertical fields at the top level. The link rides two other ways, and
    # both are what the month-end export will actually join on:
    #   (a) the reshape artifact above, joinable to the gate audit by amount;
    #   (b) the proposal's own grounding trace, which names the source event.
    # Asserting (b) here rather than demanding a top-level field keeps the engine
    # vertical-agnostic instead of teaching it about `case_id`.
    verdict_amounts = {
        Decimal(v["amount"]["value"]) for v in (by_step["approve"].audit or {})["doa_tier"]
    }
    assert verdict_amounts == set(_BREACH_CASES), "the gate must route both breaches"
    assert {reshaped[a] for a in verdict_amounts} == set(_BREACH_CASES.values())

    grounded = set()
    for proposal in _rows(by_step["approve"]):
        for trace in proposal["action"]["reasoning_trace"]:
            event = (trace.get("detail") or {}).get("event") or {}
            if event.get("case_id"):
                grounded.add(event["case_id"])
    assert grounded == set(_BREACH_CASES.values())


async def test_a_case_id_is_never_invented_for_a_row_that_had_none(
    fleet_factory: ExecutorFactory,
) -> None:
    """The negative that keeps the positive honest.

    A bridge that defaulted a missing ``case_id`` — to the truck id, to a generated
    value, to empty string — would make every assertion above pass while destroying
    the only thing the field is for. An un-cased row must reach the gate visibly
    un-cased, so the KPI can count it as untraceable instead of quietly clean."""
    by_step = await _run(fleet_factory, "fleet-case-bridge-negative")

    # truck-02's routine ฿1,800 reading reaches intake and carries NO case id.
    uncased = [r for r in _rows(by_step["intake"]) if r["truck_id"] == "truck-02"]
    assert uncased, "truck-02's routine reading must still reach intake"
    assert all("case_id" not in r or r["case_id"] is None for r in uncased)
