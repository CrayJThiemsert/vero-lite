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

from decimal import Decimal
from typing import Any, get_args

import pytest
from pydantic import BaseModel

from services.engine.procedures.archetypes.template import REGISTRY, instantiate
from services.engine.procedures.draft import (
    AGENT_GOVERNANCE_FIELDS,
    PROCEDURE_GOVERNANCE_FIELDS,
    STEP_GOVERNANCE_FIELDS,
    AgentDraft,
    ProcedureDraft,
    StepDraft,
    derive_governance_todo,
    lift_to_procedure,
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
    ComplianceCriterion,
    ComplianceGate,
    ComplianceRule,
    DecisionCondition,
    DoaLadder,
    DoaTier,
    EmergencyWaiverPolicy,
    ExceptionPolicy,
    GateKind,
    Procedure,
    RelaxableConstraint,
    ScoredCriterion,
    ScoredRule,
    SoDConstraint,
    SourcePolicy,
    Step,
    StepFacet,
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


# --- ADR-0025 Step 1 (D4): AT-2 content is H — recursive draft-disjointness + facet-unreach ---

_AT2_CONTENT_TYPES: frozenset[type[BaseModel]] = frozenset(
    {
        DoaTier,
        DoaLadder,
        EmergencyWaiverPolicy,
        ScoredCriterion,
        ScoredRule,
        ComplianceRule,
        ComplianceGate,
        SoDConstraint,
    }
)


def _annotation_types(annotation: Any) -> list[type]:
    """Every concrete type named in a type annotation, walked recursively through
    list/set/frozenset/Optional/Union/Annotated args."""
    out: list[type] = [annotation] if isinstance(annotation, type) else []
    for arg in get_args(annotation):
        out.extend(_annotation_types(arg))
    return out


def _reachable_models(root: type[BaseModel]) -> set[type[BaseModel]]:
    """Every BaseModel subclass reachable from ``root``'s fields, recursively (excludes
    ``root`` itself)."""
    seen: set[type[BaseModel]] = set()
    stack: list[type] = [root]
    while stack:
        current = stack.pop()
        if not (isinstance(current, type) and issubclass(current, BaseModel)) or current in seen:
            continue
        seen.add(current)
        for field in current.model_fields.values():
            stack.extend(_annotation_types(field.annotation))
    seen.discard(root)
    return seen


@pytest.mark.parametrize("draft_type", [StepDraft, ProcedureDraft, AgentDraft])
def test_no_at2_content_reachable_from_any_draft_type(draft_type: type[BaseModel]) -> None:
    """D4 recursive disjointness: no AT-2 governance-content type (nor any union variant) is
    reachable from any draft type's fields — a generated AT-2 value is a TYPE ERROR at the
    boundary. Adding one to a draft type later fails CI (the guardrail cannot silently
    erode)."""
    assert _AT2_CONTENT_TYPES.isdisjoint(_reachable_models(draft_type))


def test_no_at2_content_reachable_from_step_facet() -> None:
    """D4 / D2-A4: the non-authoritative StepFacet cannot embed AT-2 content — it may only
    carry the gate_kind (point-at), never a ladder. Keeps the authoritative content on the
    typed Step field, never in the facet."""
    assert _AT2_CONTENT_TYPES.isdisjoint(_reachable_models(StepFacet))


def test_step_reaches_at2_content_positive_control() -> None:
    """Positive control: the AUTHORITATIVE Step DOES reach the AT-2 union (so the
    disjointness assertions above are meaningful, not vacuous)."""
    assert not _AT2_CONTENT_TYPES.isdisjoint(_reachable_models(Step))


def test_new_governance_fields_registered_as_human_authored() -> None:
    """AC-4: governance_content (Step) + separation_of_duties (Procedure) are in the H set."""
    assert "governance_content" in STEP_GOVERNANCE_FIELDS
    assert "separation_of_duties" in PROCEDURE_GOVERNANCE_FIELDS


def test_lift_injects_at2_content_absent() -> None:
    """AC-4: the lift leaves governance_content / separation_of_duties ABSENT (H stubs) — a
    draft cannot carry them, so a lifted skeleton has neither."""
    step = lift_to_step(StepDraft(step_id="approve", name="Approve", kind=StepKind.ACTION))
    assert step.governance_content is None
    proc = lift_to_procedure(
        ProcedureDraft(
            procedure_id="p",
            title="P",
            steps=[StepDraft(step_id="approve", name="Approve", kind=StepKind.ACTION)],
        ),
        run_by="agent",
    )
    assert proc.separation_of_duties == []


# --- ADR-0025 Step 2 (D5): the AT-2-aware run-gate (governance_content + SoD) -----
#
# derive_governance_todo now owes governance_content on an AT-2 gate kind; _is_filled checks
# the D4 correspondence (variant kind == gate_kind); validate_governance_complete refuses a
# hollow AT-2 (missing content) and a doa_tier procedure with no SoD. The principal-level SoD
# is the deferred A2 run check (OQ-A=A1) — these assert the author-time STRUCTURAL gate.


def _dc_step(
    step_id: str,
    kind: StepKind,
    gate_kind: GateKind,
    *,
    handler: str | None = None,
    governance_content: DoaLadder | ScoredRule | ComplianceGate | None = None,
) -> Step:
    """A step carrying a facet ``gate_kind`` (the discriminator the gate reads)."""
    return Step(
        step_id=step_id,
        name=step_id,
        kind=kind,
        handler=handler,
        governance_content=governance_content,
        facet=StepFacet(decision_condition=DecisionCondition(gate_kind=gate_kind)),
    )


def _ladder() -> DoaLadder:
    return DoaLadder(
        currency="THB",
        tiers=[DoaTier(min_amount=Decimal("0"), approver_role="dept_head")],
        emergency_waiver=EmergencyWaiverPolicy(
            relaxes=[RelaxableConstraint.THREE_BID], escalate_to="director"
        ),
    )


def _scored() -> ScoredRule:
    return ScoredRule(
        criteria=[ScoredCriterion(name="price", weight=Decimal("1"))],
        default_source=SourcePolicy.ON_CONTRACT,
        exception_policy=ExceptionPolicy.RFQ_AVL_LOGGED,
    )


# AC-7 — derive_governance_todo owes governance_content on each AT-2 gate kind


def test_governance_todo_scored_rule_action_owes_content() -> None:
    step = _dc_step("source", StepKind.ACTION, GateKind.SCORED_RULE, handler="emergency_source")
    assert "governance_content" in derive_governance_todo(step)


def test_governance_todo_rule_gate_evaluate_owes_content() -> None:
    step = _dc_step("compliance", StepKind.EVALUATE, GateKind.RULE_GATE)
    assert derive_governance_todo(step) == ["governance_content"]


def test_governance_todo_doa_tier_action_owes_content() -> None:
    step = _dc_step("approve", StepKind.ACTION, GateKind.DOA_TIER, handler="request_approval")
    assert "governance_content" in derive_governance_todo(step)


def test_governance_todo_none_gate_action_owes_no_at2_content() -> None:
    """An AT-1-family action (gate_kind none) is unchanged — no governance_content owed."""
    step = _dc_step("issue", StepKind.ACTION, GateKind.NONE, handler="issue_po")
    assert "governance_content" not in derive_governance_todo(step)


# AC-7 — _is_filled enforces the D4 variant<->gate_kind correspondence


def test_doa_tier_with_matching_ladder_is_filled() -> None:
    step = _dc_step(
        "approve",
        StepKind.ACTION,
        GateKind.DOA_TIER,
        handler="request_approval",
        governance_content=_ladder(),
    )
    assert "governance_content" not in unfilled_governance(step)


def test_doa_tier_with_wrong_variant_is_unfilled() -> None:
    """D4 correspondence: a ScoredRule on a doa_tier step is present but mismatched -> unfilled."""
    step = _dc_step(
        "approve",
        StepKind.ACTION,
        GateKind.DOA_TIER,
        handler="request_approval",
        governance_content=_scored(),
    )
    assert "governance_content" in unfilled_governance(step)


def test_at2_step_missing_content_is_unfilled() -> None:
    step = _dc_step("compliance", StepKind.EVALUATE, GateKind.RULE_GATE)
    assert unfilled_governance(step) == ["governance_content"]


# AC-9 — the negative hollow-but-complete regression (the D5 ratification gate)

_SOD = [SoDConstraint(distinct_steps=frozenset({"intake", "approve"}))]


def _doa_procedure(
    *, content: DoaLadder | ScoredRule | ComplianceGate | None, sod: list[SoDConstraint]
) -> Procedure:
    return Procedure(
        procedure_id="p",
        title="P",
        run_by="a",
        steps=[
            Step(step_id="intake", name="Intake", kind=StepKind.QUERY),
            _dc_step(
                "approve",
                StepKind.ACTION,
                GateKind.DOA_TIER,
                handler="request_approval",
                governance_content=content,
            ),
        ],
        separation_of_duties=sod,
    )


def test_hollow_at2_missing_content_is_refused() -> None:
    """AC-9 / D8 fixture 1: a doa_tier step with handler+autonomy filled but governance_content
    ABSENT is refused — the live blindness defect, now closed (pre-committed pass/fail)."""
    proc = _doa_procedure(content=None, sod=_SOD)
    with pytest.raises(ProcedureError, match="governance_content"):
        validate_governance_complete(proc)


def test_doa_procedure_missing_sod_is_refused() -> None:
    """AC-9: a doa_tier-bearing procedure with no separation_of_duties is refused (D5)."""
    proc = _doa_procedure(content=_ladder(), sod=[])
    with pytest.raises(ProcedureError, match="separation_of_duties"):
        validate_governance_complete(proc)


def test_wrong_variant_at2_is_refused() -> None:
    """AC-9: a present-but-mismatched variant (ScoredRule on a doa_tier step) is refused."""
    proc = _doa_procedure(content=_scored(), sod=_SOD)
    with pytest.raises(ProcedureError, match="governance_content"):
        validate_governance_complete(proc)


def test_fully_authored_at2_passes_the_gate() -> None:
    """The second state: matching content on the doa_tier step + a SoD constraint passes."""
    proc = _doa_procedure(content=_ladder(), sod=_SOD)
    validate_governance_complete(proc)  # no raise


def test_compliance_criterion_import_is_used() -> None:
    """A rule_gate evaluate owes a ComplianceGate; a matching one fills it."""
    gate = ComplianceGate(rules=[ComplianceRule(criterion=ComplianceCriterion.AVL, spec="on AVL")])
    step = _dc_step("compliance", StepKind.EVALUATE, GateKind.RULE_GATE, governance_content=gate)
    assert "governance_content" not in unfilled_governance(step)
