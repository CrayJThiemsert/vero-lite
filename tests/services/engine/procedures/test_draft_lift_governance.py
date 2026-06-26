"""PLAN-0040 Phase A (Step A2) — restricted draft type + lift + the governance run-gate.

Offline gate (zero-LLM, no DB) for ADR-0024 D3 mechanism 1 + D6 / OQ-1:

* **AC-A4** structural disjointness — the draft types carry NO governance field
  (adding one later fails CI; the guardrail cannot silently erode).
* **AC-A3** lift — ``lift_to_step`` injects governance values as ABSENT stubs
  (OQ-C C1: ``None`` / safe default, never an in-field sentinel) and stays
  ``load_procedures``-valid.
* **AC-A7** ``derive_governance_todo`` — the obligation worklist from ``(gate_kind, kind)``.
* **AC-A6** ``validate_governance_complete`` — refuses a stub skeleton, accepts a
  complete one; invoked by ``validate_runnable``.
* the **two-state property** (D6): an instantiated skeleton LOADS but fails the
  run-gate; authoring the stubs makes it pass.
"""

from __future__ import annotations

import pytest

from services.engine.procedures.archetypes.template import REGISTRY, instantiate
from services.engine.procedures.draft import (
    AGENT_GOVERNANCE_FIELDS,
    PROCEDURE_GOVERNANCE_FIELDS,
    STEP_GOVERNANCE_FIELDS,
    AgentDraft,
    ProcedureDraft,
    StepDraft,
    derive_governance_todo,
    lift_to_step,
    unfilled_governance,
)
from services.engine.procedures.orchestrator import (
    ProcedureError,
    validate_governance_complete,
    validate_runnable,
)
from services.engine.procedures.spec import (
    Autonomy,
    BandSource,
    GateKind,
    Step,
    StepKind,
    VerticalProcedures,
    load_procedures,
    parse_procedures,
)

REAL_VERTICALS = ["energy", "supply_chain", "aquaculture", "procurement"]


# --- AC-A4 structural disjointness ----------------------------------------------


def test_step_draft_has_no_governance_field() -> None:
    """AC-A4: a leak is a TYPE ERROR — StepDraft shares no field with the H set.
    Adding `threshold` (etc.) to the draft later fails CI."""
    assert STEP_GOVERNANCE_FIELDS.isdisjoint(set(StepDraft.model_fields))


def test_procedure_and_agent_drafts_have_no_governance_field() -> None:
    """AC-A4 analogues: ProcedureDraft has no run_by; AgentDraft has no
    llm_model/autonomy_ceiling/allowed."""
    assert PROCEDURE_GOVERNANCE_FIELDS.isdisjoint(set(ProcedureDraft.model_fields))
    assert AGENT_GOVERNANCE_FIELDS.isdisjoint(set(AgentDraft.model_fields))


# --- AC-A3 lift injects absent stubs --------------------------------------------


def test_lift_judge_draft_injects_absent_band() -> None:
    """A judge StepDraft lifts to a load_procedures-valid Step with the band kind
    preserved (G) but every band VALUE absent (H stub, OQ-C C1)."""
    draft = StepDraft(
        step_id="judge",
        name="Judge",
        kind=StepKind.EVALUATE,
        gate_kind=GateKind.IN_FILE_BAND,
        band_source=BandSource.IN_FILE,
    )
    step = lift_to_step(draft)
    assert step.kind is StepKind.EVALUATE
    assert (step.threshold, step.direction, step.watch_margin) == (None, None, None)
    assert step.facet is not None and step.facet.decision_condition is not None
    assert step.facet.decision_condition.gate_kind is GateKind.IN_FILE_BAND
    assert step.facet.decision_condition.env_var is None


def test_lift_action_draft_injects_absent_handler_safe_autonomy() -> None:
    """An action StepDraft lifts with handler ABSENT (H stub) and autonomy at the
    safe default (gated) — the draft cannot carry either."""
    draft = StepDraft(step_id="act", name="Act", kind=StepKind.ACTION, gate_kind=GateKind.NONE)
    step = lift_to_step(draft)
    assert step.kind is StepKind.ACTION
    assert step.handler is None
    assert step.tiers is None
    assert step.autonomy is Autonomy.GATED  # safe-by-default; a confirm obligation


# --- AC-A7 governance_todo derivation -------------------------------------------


def _step(kind: StepKind, gate_kind: GateKind, band_source: BandSource | None = None) -> Step:
    return lift_to_step(
        StepDraft(step_id="s", name="S", kind=kind, gate_kind=gate_kind, band_source=band_source)
    )


def test_governance_todo_in_file_band_owes_threshold_direction() -> None:
    step = _step(StepKind.EVALUATE, GateKind.IN_FILE_BAND, BandSource.IN_FILE)
    assert derive_governance_todo(step) == ["threshold", "direction"]


def test_governance_todo_env_band_owes_env_var() -> None:
    step = _step(StepKind.EVALUATE, GateKind.ENV_BAND, BandSource.ENV)
    assert derive_governance_todo(step) == ["env_var"]


def test_governance_todo_action_owes_handler() -> None:
    step = _step(StepKind.ACTION, GateKind.NONE)
    assert "handler" in derive_governance_todo(step)


def test_governance_todo_query_owes_nothing() -> None:
    step = _step(StepKind.QUERY, GateKind.NONE)
    assert derive_governance_todo(step) == []


# --- AC-A6 validate_governance_complete + the two-state property -----------------


def _skeleton(
    archetype_id: str, band_source: BandSource = BandSource.IN_FILE
) -> VerticalProcedures:
    doc = instantiate(REGISTRY[archetype_id], procedure_id="p", title="P", band_source=band_source)
    return parse_procedures(doc, vertical="draft")


@pytest.mark.parametrize("archetype_id", ["AT-1", "AT-1b", "AT-3"])
def test_skeleton_loads_but_fails_governance_complete(archetype_id: str) -> None:
    """The two-state property (D6): the instantiated skeleton LOADS (we already have a
    VerticalProcedures) but validate_governance_complete RAISES — it is draft-loadable,
    not run-loadable."""
    spec = _skeleton(archetype_id)
    with pytest.raises(ProcedureError, match="unfilled governance stub"):
        validate_governance_complete(spec.procedures[0])


@pytest.mark.parametrize("archetype_id", ["AT-1", "AT-1b", "AT-3"])
def test_authoring_the_stubs_makes_it_run_loadable(archetype_id: str) -> None:
    """Author the H stubs (threshold/direction on the judge; a handler on each action)
    and the skeleton passes validate_governance_complete — the second state."""
    proc = _skeleton(archetype_id).procedures[0]
    authored_steps = []
    for s in proc.steps:
        if s.kind is StepKind.EVALUATE:
            authored_steps.append(s.model_copy(update={"threshold": 1.0, "direction": "below"}))
        elif s.kind is StepKind.ACTION:
            authored_steps.append(s.model_copy(update={"handler": "echo"}))
        else:
            authored_steps.append(s)
    authored = proc.model_copy(update={"steps": authored_steps})
    validate_governance_complete(authored)  # no raise
    assert all(not unfilled_governance(s) for s in authored.steps)


def test_validate_runnable_now_rejects_a_stub_skeleton() -> None:
    """validate_runnable invokes validate_governance_complete (OQ-1): a stub skeleton
    that previously slipped through (handler=None) now raises before any run."""
    spec = _skeleton("AT-1")
    proc = spec.procedures[0]
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    with pytest.raises(ProcedureError):
        validate_runnable(proc, agent)


# --- no-regression: every shipped vertical is governance-complete ----------------


@pytest.mark.parametrize("vertical", REAL_VERTICALS)
def test_shipped_verticals_pass_governance_complete(vertical: str) -> None:
    """Every hand-authored, shipped procedure is already governance-complete — the new
    gate adds nothing to authored specs (no-regression)."""
    spec = load_procedures(vertical)
    for proc in spec.procedures:
        validate_governance_complete(proc)  # no raise
        assert all(not unfilled_governance(s) for s in proc.steps)
