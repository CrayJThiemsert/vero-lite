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
from pathlib import Path

import pytest
from pydantic import ValidationError

from services.engine.procedures.draft import VERTICAL_GOVERNANCE_FIELDS
from services.engine.procedures.rule_gate import COMPLIANCE_FIELD, evaluate_compliance
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
    load_procedures_file,
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


# --- AC-1: the proof pair — the engine-edit-per-vertical pressure is GONE ---------
#
# The three tests below are the PLAN's acceptance proof, not extra coverage. AC-1's
# pre-committed read is: a fixture vertical carrying a criterion that appears NOWHERE in
# `services/` (i) loads through the real `load_procedures_file` and gates through the real
# `evaluate_compliance`, (ii) its undeclared twin is refused at load, and (iii) a repo grep
# for that criterion matches only this module. Together they say: shipping a brand-new gate
# vocabulary required zero engine diff. Under the retired `ComplianceCriterion` enum, the
# fixture below was simply unloadable without editing `spec.py`.

_NOVEL_CRITERION = "zzz_fixture_only_sourcing_check"
"""Deliberately not a plausible real criterion: it must never be added to a shipped vertical,
because :func:`test_novel_criterion_is_confined_to_this_module` asserts it appears nowhere
else in the repo. That assertion is what makes the other two tests mean "no engine diff"
rather than merely "a criterion works"."""

_FIXTURE_YAML = """\
namespace: fixturevert
version: 0

agents:
  fixture_agent:
    name: Fixture Agent
    allowed:
      step_kinds: [query, evaluate]

compliance_criteria: [{criteria}]

procedures:
  fixture_gate_check:
    title: Fixture Gate Check
    goal: >-
      Evaluate a candidate against a vocabulary this vertical declared for itself.
    run_by: fixture_agent
    trigger: manual
    steps:
      - step_id: intake
        name: Intake
        kind: query
      - step_id: gate
        name: Gate
        kind: evaluate
        governance_content:
          kind: rule_gate
          rules:
            - criterion: {criterion}
              spec: "the fixture predicate — non-authoritative display text"
        facet:
          decision_condition: {{ gate_kind: rule_gate }}
"""


def _write_fixture(tmp_path: Path, *, declared: str) -> Path:
    path = tmp_path / "procedures.yaml"
    path.write_text(
        _FIXTURE_YAML.format(criteria=declared, criterion=_NOVEL_CRITERION), encoding="utf-8"
    )
    return path


def test_novel_criterion_loads_and_gates_with_zero_engine_diff(tmp_path: Path) -> None:
    """AC-1(i). The full real path: `load_procedures_file` parses a vertical whose gate names a
    criterion the engine has never heard of, and `evaluate_compliance` then gates on it —
    passing on an explicit truthy signal, BLOCKING on a false one and on an ABSENT one (an
    unverifiable blocking criterion can never be waved through; ADR-0025 D3 fail-closed)."""
    spec = load_procedures_file(
        _write_fixture(tmp_path, declared=_NOVEL_CRITERION), vertical="fixturevert"
    )
    gate = spec.procedures[0].steps[1].governance_content
    assert isinstance(gate, ComplianceGate)
    assert [r.criterion for r in gate.rules] == [_NOVEL_CRITERION]

    passing = evaluate_compliance(gate, {COMPLIANCE_FIELD: {_NOVEL_CRITERION: True}})
    assert passing.compliant and passing.failed_criteria == []

    failing = evaluate_compliance(gate, {COMPLIANCE_FIELD: {_NOVEL_CRITERION: False}})
    assert not failing.compliant and failing.failed_criteria == [_NOVEL_CRITERION]

    absent = evaluate_compliance(gate, {COMPLIANCE_FIELD: {}})
    assert not absent.compliant and absent.failed_criteria == [_NOVEL_CRITERION]


def test_novel_criterion_undeclared_twin_is_refused_at_load(tmp_path: Path) -> None:
    """AC-1(ii). The SAME fixture, declaring a different id — so the gate's criterion is
    well-formed but undeclared. Refused at load, with a message that names the vertical, the
    offender and the declared set. This is what keeps the vocabulary closed: the vertical may
    choose its own words, but it may not use one it never wrote down."""
    with pytest.raises(ValidationError) as exc:
        load_procedures_file(
            _write_fixture(tmp_path, declared="something_else"), vertical="fixturevert"
        )
    msg = str(exc.value)
    assert _NOVEL_CRITERION in msg
    assert "something_else" in msg


def test_novel_criterion_is_confined_to_this_module() -> None:
    """AC-1(iii) — the static guard that gives the two tests above their meaning. If this
    fixture criterion ever appears in `services/` or in a shipped vertical, then the "zero
    engine diff" claim above is no longer being proven by anything, and this test says so
    before the claim quietly rots. Mirrors the `test_load_run_ordering_guard.py` pattern."""
    root = Path(__file__).resolve().parents[4]
    hits = sorted(
        p.relative_to(root).as_posix()
        for d in ("services", "tests", "verticals")
        for p in (root / d).rglob("*")
        if p.is_file()
        and p.suffix in {".py", ".yaml", ".yml"}
        and _NOVEL_CRITERION in p.read_text(encoding="utf-8", errors="ignore")
    )
    assert hits == [Path(__file__).resolve().relative_to(root).as_posix()], (
        f"the AC-1 fixture criterion leaked outside this module: {hits}. It must exist ONLY "
        "here — its absence from services/ is what proves a new vertical's vocabulary needs "
        "no engine edit."
    )
