"""AC-6 (PLAN-0044 A1b Step 4) -- the deterministic ``rule_gate`` compliance executor.

Offline + LLM-free (CLAUDE.md #8 -- the offline oracle is the gate). Three surfaces:

* the pure :func:`evaluate_compliance` -- blocks on ANY failed criterion, is non-waivable
  (there is no pass-a-failed-rule path), coerces the string ``"false"`` signal correctly, is
  deterministic, and fails CLOSED (no signal map / a non-mapping candidate / an absent per-criterion
  signal);
* the SD-1=(a) :class:`GovernanceEvaluateExecutor` dispatch -- a ``rule_gate`` evaluate step tags
  each candidate ``compliant`` (so the downstream ``approve`` ``where: {compliant: true}`` fan-out
  drops a blocked candidate) and records the per-criterion audit, while a banded ``judge`` step
  (no ``rule_gate`` content) falls through to the shipped deterministic ``EvaluateStepExecutor``;
* a guard that the SHIPPED procurement ``compliance`` rule_gate (procedures.yaml) blocks a
  non-compliant candidate and passes a fully-compliant one.

The pre-committed pass/fail read is PLAN-0044 AC-6, fixed before this test was authored: a
``rule_gate``-bearing step blocks the PO on any failed ``ComplianceRule`` (candidate dropped from
the downstream ``compliant`` set); compliance is non-waivable by type; the LLM never evaluates the
rule.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from services.engine.procedures.evaluate_step import EvaluateStepExecutor
from services.engine.procedures.governance_step import GovernanceEvaluateExecutor
from services.engine.procedures.orchestrator import RunContext, StepOutcome
from services.engine.procedures.rule_gate import (
    RuleGateError,
    RuleResult,
    evaluate_compliance,
)
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    ComplianceCriterion,
    ComplianceGate,
    ComplianceRule,
    Step,
    StepKind,
    load_procedures,
)

# --------------------------------------------------------------------------- #
# Fixtures — the procurement per-criterion compliance gate + a candidate
# --------------------------------------------------------------------------- #


def _hero_gate() -> ComplianceGate:
    """The procurement ``compliance`` step's authored rule_gate (procedures.yaml): the five
    per-criterion rules, each blocking the PO on failure (blocks_po is Literal[True])."""
    return ComplianceGate(
        rules=[
            ComplianceRule(
                criterion=ComplianceCriterion.AVL, spec="supplier.avl_status == approved"
            ),
            ComplianceRule(criterion=ComplianceCriterion.TAX, spec="supplier.tax_id present"),
            ComplianceRule(
                criterion=ComplianceCriterion.CERT, spec="supplier.cert_status == valid"
            ),
            ComplianceRule(criterion=ComplianceCriterion.SANCTIONS, spec="not sanctioned"),
            ComplianceRule(
                criterion=ComplianceCriterion.SINGLE_SOURCE, spec="single-source justified"
            ),
        ]
    )


def _all_pass() -> dict[str, Any]:
    """A candidate carrying an all-pass per-criterion compliance signal map (data-access = (a))."""
    return {
        "primary_key": "PO-2026-0412",
        "supplier_id": "SUP-RAPIDMRO",
        "compliance": {
            "avl": True,
            "tax": True,
            "cert": True,
            "sanctions": True,
            "single_source": True,
        },
    }


# --------------------------------------------------------------------------- #
# The pure evaluate_compliance — block on any fail, non-waivable, fail closed
# --------------------------------------------------------------------------- #


def test_all_pass_is_compliant() -> None:
    """AC-6 — every criterion satisfied -> the candidate is compliant (the PO is not blocked)."""
    v = evaluate_compliance(_hero_gate(), _all_pass())
    assert v.compliant is True
    assert v.failed_criteria == []
    assert all(r.passed for r in v.results)
    assert [r.criterion for r in v.results] == ["avl", "tax", "cert", "sanctions", "single_source"]


def test_one_failed_criterion_blocks_the_po() -> None:
    """AC-6 — a single false criterion blocks the PO (compliant False, the criterion named)."""
    candidate = _all_pass()
    candidate["compliance"]["sanctions"] = False
    v = evaluate_compliance(_hero_gate(), candidate)
    assert v.compliant is False
    assert v.failed_criteria == ["sanctions"]


def test_multiple_failed_criteria_all_named() -> None:
    candidate = _all_pass()
    candidate["compliance"]["avl"] = False
    candidate["compliance"]["cert"] = False
    v = evaluate_compliance(_hero_gate(), candidate)
    assert v.compliant is False
    assert v.failed_criteria == ["avl", "cert"]  # authored order preserved


def test_absent_per_criterion_signal_fails_closed() -> None:
    """An unverifiable blocking criterion (its signal absent from the map) cannot pass -- it fails
    closed (blocks the candidate), never silently waved through."""
    candidate = _all_pass()
    del candidate["compliance"]["tax"]
    v = evaluate_compliance(_hero_gate(), candidate)
    assert v.compliant is False
    assert v.failed_criteria == ["tax"]


def test_string_false_signal_is_a_failure() -> None:
    """A CSV/JSON string ``"false"`` must FAIL the criterion (bool('false') is True in Python)."""
    candidate = _all_pass()
    candidate["compliance"]["cert"] = "false"
    v = evaluate_compliance(_hero_gate(), candidate)
    assert v.compliant is False
    assert v.failed_criteria == ["cert"]


def test_string_true_signal_passes() -> None:
    candidate = _all_pass()
    candidate["compliance"] = dict.fromkeys(
        ["avl", "tax", "cert", "sanctions", "single_source"], "true"
    )
    v = evaluate_compliance(_hero_gate(), candidate)
    assert v.compliant is True


def test_evaluation_is_deterministic() -> None:
    """AC-6 — same inputs -> same verdict, every run (no model signal)."""
    candidate = _all_pass()
    candidate["compliance"]["avl"] = False
    verdicts = [evaluate_compliance(_hero_gate(), candidate) for _ in range(5)]
    assert all(v.compliant == verdicts[0].compliant for v in verdicts)
    assert all(v.failed_criteria == verdicts[0].failed_criteria for v in verdicts)


def test_no_compliance_field_fails_closed() -> None:
    with pytest.raises(RuleGateError, match="no 'compliance' signal map"):
        evaluate_compliance(_hero_gate(), {"primary_key": "PO-1", "supplier_id": "SUP-X"})


def test_non_mapping_candidate_fails_closed() -> None:
    with pytest.raises(RuleGateError, match="not a mapping"):
        evaluate_compliance(_hero_gate(), "not-a-mapping")  # type: ignore[arg-type]


def test_non_mapping_compliance_signal_fails_closed() -> None:
    with pytest.raises(RuleGateError, match="must be a criterion->signal map"):
        evaluate_compliance(_hero_gate(), {"primary_key": "PO-1", "compliance": ["avl"]})


def test_verdict_to_audit_is_json_safe() -> None:
    candidate = _all_pass()
    candidate["compliance"]["tax"] = False
    audit = evaluate_compliance(_hero_gate(), candidate).to_audit()
    assert audit["compliant"] is False
    assert audit["failed_criteria"] == ["tax"]
    assert len(audit["results"]) == 5
    json.dumps(audit)  # must not raise


def test_rule_result_carries_the_spec_for_render() -> None:
    """The human-authored predicate rides through for the read-only render (non-authoritative)."""
    v = evaluate_compliance(_hero_gate(), _all_pass())
    avl = next(r for r in v.results if r.criterion == "avl")
    assert isinstance(avl, RuleResult)
    assert avl.spec == "supplier.avl_status == approved"


def test_shipped_procurement_compliance_gate_blocks_a_noncompliant_candidate() -> None:
    """AC-6 on the SHIPPED authored content: the procurement ``compliance`` rule_gate blocks a
    sanctioned candidate and passes a fully-compliant one -- so a rule edit that would weaken the
    gate is caught."""
    spec = load_procedures("procurement")
    proc = next(p for p in spec.procedures if p.procedure_id == "emergency_sourcing_round")
    compliance = next(s for s in proc.steps if s.step_id == "compliance")
    gate = compliance.governance_content
    assert isinstance(gate, ComplianceGate)  # the authored compliance content is a rule_gate
    assert all(r.blocks_po is True for r in gate.rules)  # non-waivable by type
    passing = evaluate_compliance(gate, _all_pass())
    assert passing.compliant is True
    blocked_candidate = _all_pass()
    blocked_candidate["compliance"]["sanctions"] = False
    assert evaluate_compliance(gate, blocked_candidate).compliant is False


# --------------------------------------------------------------------------- #
# The GovernanceEvaluateExecutor rule_gate dispatch
# --------------------------------------------------------------------------- #


class _RaisingBase:
    """A base EVALUATE executor that MUST NOT be called for a rule_gate step (compliance has no
    numeric band, so the base would raise). Records delegation to prove the dispatch skips it."""

    def __init__(self) -> None:
        self.calls = 0

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        self.calls += 1
        raise AssertionError("the base must not run for a rule_gate step")


def _ctx() -> RunContext:
    agent = Agent(
        agent_id="hero-agent",
        name="Hero Agent",
        autonomy_ceiling=Autonomy.AUTO,
        allowed=AgentAllowed(step_kinds=[StepKind.EVALUATE]),
    )
    return RunContext(agent=agent, vertical="procurement")


def _compliance_step() -> Step:
    return Step(
        step_id="compliance",
        name="Check per-criterion compliance",
        kind=StepKind.EVALUATE,
        governance_content=_hero_gate(),
    )


def _judge_step() -> Step:
    """A banded judge step (no rule_gate content) -- the dispatch must fall through to the base."""
    return Step(
        step_id="judge",
        name="Judge criticality",
        kind=StepKind.EVALUATE,
        threshold=0.8,
        direction="above",
        watch_margin=0.2,
    )


async def test_dispatch_tags_compliant_and_records_audit() -> None:
    """A rule_gate evaluate step tags each candidate ``compliant`` + audits the per-criterion
    results; the blocked candidate is tagged False (the fan-out drops it downstream)."""
    wrapper = GovernanceEvaluateExecutor(base=_RaisingBase())
    blocked = _all_pass()
    blocked["primary_key"] = "PO-BLOCKED"
    blocked["compliance"]["avl"] = False
    outcome = await wrapper.execute(_compliance_step(), [_all_pass(), blocked], _ctx())
    tags = {e["primary_key"]: e["compliant"] for e in outcome.output}
    assert tags == {"PO-2026-0412": True, "PO-BLOCKED": False}
    blocked_out = next(e for e in outcome.output if e["primary_key"] == "PO-BLOCKED")
    assert blocked_out["failed_criteria"] == ["avl"]
    assert outcome.audit is not None
    assert outcome.audit["governed_kind"] == "rule_gate"
    assert outcome.audit["deterministic"] is True
    assert len(outcome.audit["rule_gate"]) == 2
    assert any(t["kind"] == "rule_gate_evaluated" for t in outcome.reasoning_trace)


async def test_dispatch_does_not_call_base_for_rule_gate() -> None:
    """The rule_gate branch is self-contained -- the base EvaluateStepExecutor (which needs a
    numeric band) is never called."""
    base = _RaisingBase()
    wrapper = GovernanceEvaluateExecutor(base=base)
    await wrapper.execute(_compliance_step(), [_all_pass()], _ctx())
    assert base.calls == 0


async def test_dispatch_fails_closed_on_missing_signal() -> None:
    wrapper = GovernanceEvaluateExecutor(base=_RaisingBase())
    with pytest.raises(RuleGateError, match="signal map"):
        await wrapper.execute(_compliance_step(), [{"primary_key": "PO-1"}], _ctx())


async def test_banded_judge_falls_through_to_the_base() -> None:
    """A non-rule_gate evaluate step (the banded judge) delegates to the real deterministic
    EvaluateStepExecutor -- the wrapper does not intercept it."""
    wrapper = GovernanceEvaluateExecutor(base=EvaluateStepExecutor())
    entities = [
        {"event_id": "E1", "measured_value": 0.92},
        {"event_id": "E2", "measured_value": 0.1},
    ]
    outcome = await wrapper.execute(_judge_step(), entities, _ctx())
    verdicts = {e["event_id"]: e["verdict"] for e in outcome.output}
    assert verdicts == {"E1": "breach", "E2": "ok"}
    assert outcome.audit is not None
    assert "governed_kind" not in outcome.audit  # the base audit, not the rule_gate audit
