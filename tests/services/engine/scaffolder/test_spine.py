"""PLAN-0091 Step 4 — the AT-2 spine template + the procedures emitter (oracle AC-5).

The first test in this module is the **SD-5 tripwire**, and it is the reason the
rest of the step is safe: the AT-2 template must never enter the shared
``REGISTRY``. If it did, ``generator/pipeline.py`` would start routing an "AT-2"
classification as a hit instead of an abstain, silently growing the API classify
surface that Step 4's design note promises stays byte-unchanged.

If that test ever needs editing, the answer is **not** to edit it. Stop and
re-open SD-5.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from services.engine.procedures.archetypes.template import REGISTRY
from services.engine.procedures.draft import derive_governance_todo
from services.engine.procedures.spec import load_procedures
from services.engine.scaffolder.intake import IntakeAnswer, IntakeRecord
from services.engine.scaffolder.ontology import emit_ontology
from services.engine.scaffolder.spine import (
    AT2_SPINE,
    ProseLintError,
    SpineAgreementError,
    emit_procedures,
    gate_signature,
)

_FULL = {
    "ontology.asset_noun": "Truck",
    "ontology.site_noun": "Depot",
    "ontology.band_property": "minor_repair_ceiling_thb",
    "ontology.action_types": "approve_repair_spend, escalate",
    "governance.rule_gate.criteria": "three_quote",
    "governance.approve.currency": "THB",
    "governance.approve.tiers": "0:head_mechanic, 5000:fleet_manager, 50000:owner",
    "governance.approve.waiver.relaxes": "three_bid",
    "governance.approve.waiver.ratifier": "owner",
    "governance.approve.sod.requester": "head_mechanic",
    "band.judge.direction": "above",
}


def _record(drop: tuple[str, ...] = ()) -> IntakeRecord:
    return IntakeRecord(
        namespace="fleet_demo",
        answers=[IntakeAnswer(slot_id=k, value=v) for k, v in _FULL.items() if k not in drop],
    )


def _emit(record: IntakeRecord | None = None) -> dict:
    rec = record or _record()
    return emit_procedures(rec, emit_ontology(rec))


# --- the SD-5 tripwire ------------------------------------------------------


def test_at2_template_is_scaffolder_owned_and_never_registered() -> None:
    """SD-5 (a), Cray-ratified: the AT-2 template NEVER enters the shared REGISTRY.

    This is what keeps `generator/pipeline.py`'s classify path byte-unchanged —
    it builds its catalog from `REGISTRY.values()` and routes by label through
    the same dict, so a registered AT-2 turns an abstain into a hit.

    **If this fails, do not "fix" it by registering.** Stop and re-open SD-5.
    """
    assert AT2_SPINE.archetype_id == "AT-2"
    assert AT2_SPINE.archetype_id not in REGISTRY
    assert set(REGISTRY) == {"AT-1", "AT-1b", "AT-3"}
    assert AT2_SPINE not in REGISTRY.values()


# --- the spine shape --------------------------------------------------------


def test_spine_is_row_11s_fixed_sequence() -> None:
    assert [slot.step_id for slot in AT2_SPINE.slots] == [
        "intake",
        "judge",
        "reshape",
        "rule_gate",
        "approve",
        "fulfill",
    ]
    assert AT2_SPINE.terminal_slot == "fulfill"


def test_emitted_spine_agrees_with_the_template_signature() -> None:
    """ADR-0024 D4 agreement, asserted rather than assumed."""
    doc = _emit()
    steps = next(iter(doc["procedures"].values()))["steps"]
    emitted = tuple((s["step_id"], s["facet"]["decision_condition"]["gate_kind"]) for s in steps)
    assert emitted == gate_signature()


def test_a_contradicting_gate_kind_is_a_hard_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-vacuity for the agreement check: break the signature, get a raise.

    Without this, `test_emitted_spine_agrees_...` would pass trivially for any
    emitter that derived both sides from the same source.
    """
    import services.engine.scaffolder.spine as spine_mod

    monkeypatch.setattr(
        spine_mod, "gate_signature", lambda template=AT2_SPINE: (("intake", "doa_tier"),)
    )
    with pytest.raises(SpineAgreementError):
        _emit()


# --- governance values: confirmed intake only -------------------------------


def test_governance_values_trace_to_confirmed_intake() -> None:
    steps = next(iter(_emit()["procedures"].values()))["steps"]
    approve = next(s for s in steps if s["step_id"] == "approve")
    ladder = approve["governance_content"]
    assert ladder["currency"] == "THB"
    assert [t["min_amount"] for t in ladder["tiers"]] == ["0", "5000", "50000"]
    assert ladder["emergency_waiver"]["escalate_to"] == "owner"


def test_an_unanswered_ladder_is_absent_not_invented() -> None:
    """The stub form: absent field, so the review gate still lists the obligation.

    A half-authored authority ladder that LOADS is more dangerous than one the
    gate refuses — it looks governed and routes on invented tiers.
    """
    doc = _emit(_record(drop=("governance.approve.tiers",)))
    approve = next(
        s for s in next(iter(doc["procedures"].values()))["steps"] if s["step_id"] == "approve"
    )
    assert "governance_content" not in approve


def test_the_shipped_deriver_still_lists_the_unfilled_obligation() -> None:
    """The stub is only meaningful if the review gate re-derives it — check that.

    Uses the shipped `derive_governance_todo` on the spine's own approve shape,
    so this asserts against the real obligation source, not a local restatement.
    """
    from services.engine.scaffolder.intake import spine_steps

    approve = next(s for s in spine_steps() if s.step_id == "approve")
    assert "governance_content" in derive_governance_todo(approve)


def test_separation_of_duties_is_emitted_for_the_doa_gate() -> None:
    """ADR-0025 D5: a doa_tier gate REQUIRES SoD."""
    procedure = next(iter(_emit()["procedures"].values()))
    assert procedure["separation_of_duties"] == [
        {
            "distinct_steps": ["intake", "approve"],
            "required_roles": {"intake": "requester", "approve": "approver"},
        }
    ]


def test_sod_is_absent_when_the_requester_is_unanswered() -> None:
    doc = _emit(_record(drop=("governance.approve.sod.requester",)))
    assert "separation_of_duties" not in next(iter(doc["procedures"].values()))


# --- the vertical declares its own vocabulary (PLAN-0087, zero engine diff) --


def test_vertical_declares_its_own_compliance_criteria() -> None:
    doc = _emit()
    assert doc["compliance_criteria"] == ["three_quote"]
    rule_gate = next(
        s for s in next(iter(doc["procedures"].values()))["steps"] if s["step_id"] == "rule_gate"
    )
    assert [r["criterion"] for r in rule_gate["governance_content"]["rules"]] == ["three_quote"]


# --- prose lint runs BEFORE writing -----------------------------------------


def test_prose_lint_refuses_a_smuggled_governance_value() -> None:
    """AC-5's "lint pre-paid": a D4 leak is a refusal to emit, not a later parse round-trip.

    A role token in the goal prose is an ungoverned second copy of a governed
    value — the exact class ADR-0025 D4 exists to stop.
    """
    record = _record()
    record.answers.append(
        IntakeAnswer(slot_id="ontology.asset_noun", value="Truck approved by owner"),
    )
    with pytest.raises(ProseLintError):
        emit_procedures(record, emit_ontology(_record()))


# --- the round trip ---------------------------------------------------------


@pytest.fixture
def _chdir_tmp(tmp_path: Path) -> Iterator[Path]:
    old = Path.cwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(old)


def test_emitted_procedures_round_trip_load_procedures(_chdir_tmp: Path) -> None:
    """AC-5's round-trip: the shipped loader accepts what the emitter wrote.

    `load_procedures` is INVOKED, so this asserts against the real spec loader —
    including its AT-2 free-text validation — rather than this test's idea of a
    valid procedure document.
    """
    record = _record()
    doc = emit_procedures(record, emit_ontology(record))
    path = _chdir_tmp / "verticals" / record.namespace / "procedures.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        YAML().dump(doc, stream)

    spec = load_procedures(record.namespace)
    assert [p.procedure_id for p in spec.procedures] == ["governed_truck_approval"]
    procedure = spec.procedures[0]
    assert [s.step_id for s in procedure.steps] == [
        "intake",
        "judge",
        "reshape",
        "rule_gate",
        "approve",
        "fulfill",
    ]
    assert procedure.terminal == "fulfill"
