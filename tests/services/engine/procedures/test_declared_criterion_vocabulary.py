"""PLAN-0087 Step 2 — the declared per-vertical `rule_gate` criterion vocabulary.

The criterion vocabulary used to live in engine code as the closed shared
``ComplianceCriterion`` enum, so every AT-2 vertical that shipped a ``rule_gate`` had to
edit the engine to name its own criteria. Four consecutive verticals did exactly that,
which is what cancelled the ADR-0025 D7 deferral at N=4 (PLAN-0086, Cray-ratified
2026-07-21). This module pins the replacement: a vertical DECLARES its vocabulary in its
own ``procedures.yaml``, and the engine validates membership at load.

**These tests are the mechanical half of the ADR-0031 moat-tripwire-4 answer.** Tripwire 4
forbids *"flipping a closed governed enum to accept free strings"* — so the design must be
demonstrably not-free-strings. Three of the four cases below are NEGATIVE: a prose-shaped
id is refused by TYPE, an undeclared id is refused by MEMBERSHIP, and a vertical that ships
a gate while declaring nothing is refused outright. The set is still closed; it closes per
vertical instead of in engine code.

Pure-offline (no DB, no LLM, no MS-S1 — CLAUDE.md §8).
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from services.engine.procedures.draft import VERTICAL_GOVERNANCE_FIELDS
from services.engine.procedures.spec import (
    Agent,
    ComplianceGate,
    ComplianceRule,
    DecisionCondition,
    DoaLadder,
    DoaTier,
    EmergencyWaiverPolicy,
    GateKind,
    Procedure,
    RelaxableConstraint,
    Step,
    StepFacet,
    StepKind,
    VerticalProcedures,
)

_AGENT = Agent(agent_id="ops", name="Ops")


def _rule_gate_step(criteria: list[str]) -> Step:
    """An `evaluate` step whose rule_gate names `criteria` — the surface under test."""
    return Step(
        step_id="compliance",
        name="compliance",
        kind=StepKind.EVALUATE,
        governance_content=ComplianceGate(
            rules=[ComplianceRule(criterion=c, spec="x") for c in criteria]
        ),
        facet=StepFacet(decision_condition=DecisionCondition(gate_kind=GateKind.RULE_GATE)),
    )


def _approve_step() -> Step:
    """A doa_tier approve step — present so the fixture is a realistic AT-2, not a fragment."""
    return Step(
        step_id="approve",
        name="approve",
        kind=StepKind.ACTION,
        handler="request_approval",
        governance_content=DoaLadder(
            currency="THB",
            tiers=[DoaTier(min_amount=Decimal("0"), approver_role="dept_head")],
            emergency_waiver=EmergencyWaiverPolicy(
                relaxes=[RelaxableConstraint.THREE_BID], escalate_to="director"
            ),
        ),
        facet=StepFacet(decision_condition=DecisionCondition(gate_kind=GateKind.DOA_TIER)),
    )


def _vertical(
    *, declared: list[str] | None = None, gate_criteria: list[str] | None = None
) -> VerticalProcedures:
    """Build a one-procedure vertical. `gate_criteria=None` ships NO rule_gate at all."""
    steps = [Step(step_id="intake", name="intake", kind=StepKind.QUERY)]
    if gate_criteria is not None:
        steps.append(_rule_gate_step(gate_criteria))
    steps.append(_approve_step())
    return VerticalProcedures(
        vertical="testvert",
        agents=[_AGENT],
        procedures=[
            Procedure(procedure_id="p", title="P", run_by="ops", steps=steps),
        ],
        compliance_criteria=declared or [],
    )


# --- the happy path: a vertical ships a gate on a vocabulary it declared -----------


def test_declared_vocabulary_loads_and_gates() -> None:
    """The whole point: a vertical names its own criteria with ZERO engine diff. `weird_local_check`
    exists nowhere in `services/` — under the old closed enum this spec was unloadable without an
    engine edit, which is the pressure PLAN-0087 discharges."""
    spec = _vertical(
        declared=["weird_local_check", "another_one"], gate_criteria=["weird_local_check"]
    )
    assert spec.compliance_criteria == ["weird_local_check", "another_one"]


def test_declared_but_unused_is_permitted() -> None:
    """A vocabulary may pre-declare — exactly as an unreferenced `Person` is permitted. Only the
    reverse direction (used-but-undeclared) is an authoring error."""
    spec = _vertical(declared=["used", "spare"], gate_criteria=["used"])
    assert "spare" in spec.compliance_criteria


def test_vertical_without_a_rule_gate_declares_nothing() -> None:
    """The only-when-supplied discipline: energy / aquaculture ship no rule_gate, so they author
    no vocabulary and stay byte-identical. An empty declaration is legal ONLY in this case."""
    spec = _vertical(declared=None, gate_criteria=None)
    assert spec.compliance_criteria == []


# --- the negative trio: why this is not a free-string opening ---------------------


def test_prose_shaped_criterion_is_refused_by_type() -> None:
    """Tripwire-4 leg 1 (TYPE). A criterion id is pattern-constrained, so a prose sentence, a
    ฿ amount, or a role token cannot be smuggled into the governed spine as a criterion —
    it is unrepresentable, not merely discouraged."""
    for bad in ["vendor must have three quotes", "THREE_QUOTE", "฿20,000", "has-dash", ""]:
        with pytest.raises(ValidationError):
            _vertical(declared=[bad], gate_criteria=[bad])


def test_undeclared_criterion_is_refused_by_membership() -> None:
    """Tripwire-4 leg 2 (MEMBERSHIP). A well-formed id the vertical never declared is an
    AUTHORING ERROR caught at load — the `_validate_principals` philosophy: never a silent
    collapse that never fires. The message must name the vertical, the offender, and the
    declared set, so the author can fix it without reading the engine."""
    with pytest.raises(ValidationError) as exc:
        _vertical(declared=["kyc"], gate_criteria=["kyc", "not_declared"])
    msg = str(exc.value)
    assert "testvert" in msg
    assert "not_declared" in msg
    assert "kyc" in msg


def test_rule_gate_with_no_declaration_is_refused() -> None:
    """Tripwire-4 leg 3. Shipping a gate while declaring nothing would leave the vocabulary
    implicitly open — refused outright, which is what makes the declaration MANDATORY exactly
    where it is used."""
    with pytest.raises(ValidationError) as exc:
        _vertical(declared=None, gate_criteria=["kyc"])
    assert "declares no compliance_criteria" in str(exc.value)


def test_duplicate_declarations_are_refused() -> None:
    """Mirrors `_validate_principals`'s duplicate-person_id rule: a repeated id is an authoring
    slip, and a vocabulary that silently dedups hides it."""
    with pytest.raises(ValidationError) as exc:
        _vertical(declared=["kyc", "kyc"], gate_criteria=["kyc"])
    assert "duplicate compliance_criteria" in str(exc.value)


# --- the H (never-generated) discipline ------------------------------------------


def test_compliance_criteria_is_a_human_authored_governance_field() -> None:
    """ADR-0024 D3 / ADR-0025 D4: a generator may never invent the vocabulary its own gate is
    judged against. There is no `VerticalProceduresDraft`, so — like the principal fields — the
    guard is the named H set rather than a per-draft field check."""
    assert "compliance_criteria" in VERTICAL_GOVERNANCE_FIELDS
