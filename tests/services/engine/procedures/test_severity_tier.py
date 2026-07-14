"""PLAN-0074 Step 3 — the deterministic ``severity_tier`` executor (the 4th AT-2 gate kind).

Offline + LLM-free (CLAUDE.md §8 — the offline oracle is the gate). Three surfaces:

* the pure :func:`resolve_severity_tier` — ORDINAL tier routing over the half-open severity
  band, the resolved approver :class:`Person`, the structured verdict, and the fail-closed
  reader (the non-money analog of ``resolve_doa_tier``);
* the :class:`GovernanceActionExecutor` dispatch — a ``severity_tier`` action resolves +
  annotates and delegates to the base for the gated proposal; render / route / block only;
* AC-7 (coordination point 7) — the SeverityLadder run-pin is deterministic (list-typed, no
  set fields), preserving the ``governance_pin.py`` invariant for the new content model.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from services.engine.procedures.governance_pin import (
    build_governance_snapshot,
    compute_governance_hash,
)
from services.engine.procedures.governance_step import GovernanceActionExecutor
from services.engine.procedures.orchestrator import RunContext, StepOutcome
from services.engine.procedures.severity_tier import (
    SeverityTierError,
    resolve_severity_tier,
)
from services.engine.procedures.spec import (
    Agent,
    DecisionCondition,
    ExcursionSeverity,
    GateKind,
    Person,
    Procedure,
    SeverityLadder,
    SeverityTier,
    SoDConstraint,
    Step,
    StepFacet,
    StepKind,
)

# --------------------------------------------------------------------------- #
# Fixtures — a GDP cold-chain disposition severity ladder + its approvers
# --------------------------------------------------------------------------- #


def _ladder() -> SeverityLadder:
    """A GDP disposition ladder: NEGLIGIBLE → qa_officer, MAJOR → qa_manager,
    CRITICAL → qp_release (the non-money analog of the procurement DOA ladder)."""
    return SeverityLadder(
        tiers=[
            SeverityTier(min_severity=ExcursionSeverity.NEGLIGIBLE, approver_role="qa_officer"),
            SeverityTier(min_severity=ExcursionSeverity.MAJOR, approver_role="qa_manager"),
            SeverityTier(min_severity=ExcursionSeverity.CRITICAL, approver_role="qp_release"),
        ],
    )


def _principals() -> list[Person]:
    return [
        Person(person_id="qa-1", name="QA Officer", roles=frozenset({"qa_officer"})),
        Person(person_id="qa-mgr", name="QA Manager", roles=frozenset({"qa_manager"})),
        Person(person_id="qp-1", name="Qualified Person", roles=frozenset({"qp_release"})),
    ]


# --------------------------------------------------------------------------- #
# Ordinal tier routing over the half-open severity band
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("severity", "role", "band_min", "band_max"),
    [
        # NEGLIGIBLE and MINOR both fall in tier-0's band [NEGLIGIBLE, MAJOR)
        (
            ExcursionSeverity.NEGLIGIBLE,
            "qa_officer",
            ExcursionSeverity.NEGLIGIBLE,
            ExcursionSeverity.MAJOR,
        ),
        (
            ExcursionSeverity.MINOR,
            "qa_officer",
            ExcursionSeverity.NEGLIGIBLE,
            ExcursionSeverity.MAJOR,
        ),
        # MAJOR is the INCLUSIVE floor of tier-1 (half-open) → qa_manager
        (
            ExcursionSeverity.MAJOR,
            "qa_manager",
            ExcursionSeverity.MAJOR,
            ExcursionSeverity.CRITICAL,
        ),
        # CRITICAL is the top tier — unbounded
        (ExcursionSeverity.CRITICAL, "qp_release", ExcursionSeverity.CRITICAL, None),
    ],
)
def test_tier_routing_is_deterministic_half_open_ordinal(
    severity: ExcursionSeverity,
    role: str,
    band_min: ExcursionSeverity,
    band_max: ExcursionSeverity | None,
) -> None:
    v = resolve_severity_tier(
        _ladder(), severity=severity, principals=_principals(), sod_required=True
    )
    assert v.required_role == role
    assert v.resolved_tier_id == role  # the tier's stable handle is its approver_role
    assert v.band.min is band_min
    assert v.band.max is band_max


def test_severity_is_the_ordinal_not_money() -> None:
    """The authority quantity is a closed ordinal ExcursionSeverity — the whole point of the
    gate-kind seam (PLAN-0074 SD-1). The verdict carries no amount/currency."""
    v = resolve_severity_tier(
        _ladder(), severity=ExcursionSeverity.CRITICAL, principals=_principals(), sod_required=True
    )
    assert v.severity is ExcursionSeverity.CRITICAL
    assert not hasattr(v, "amount")


def test_resolves_the_approver_person_for_the_tier() -> None:
    v = resolve_severity_tier(
        _ladder(), severity=ExcursionSeverity.MAJOR, principals=_principals(), sod_required=True
    )
    assert v.resolved_approver_id == "qa-mgr"  # holds 'qa_manager'
    top = resolve_severity_tier(
        _ladder(), severity=ExcursionSeverity.CRITICAL, principals=_principals(), sod_required=True
    )
    assert top.resolved_approver_id == "qp-1"  # holds 'qp_release'


def test_unresolved_approver_is_none_not_a_raise() -> None:
    """No declared Person holds the tier role → resolved_approver_id is None (the fail-closed on
    an unresolvable approver is the SoD run-check's job at the gate — kept distinct here)."""
    v = resolve_severity_tier(
        _ladder(), severity=ExcursionSeverity.MAJOR, principals=[], sod_required=True
    )
    assert v.resolved_approver_id is None


def test_sod_required_is_passed_through() -> None:
    yes = resolve_severity_tier(
        _ladder(),
        severity=ExcursionSeverity.NEGLIGIBLE,
        principals=_principals(),
        sod_required=True,
    )
    no = resolve_severity_tier(
        _ladder(),
        severity=ExcursionSeverity.NEGLIGIBLE,
        principals=_principals(),
        sod_required=False,
    )
    assert yes.sod_required is True and no.sod_required is False


def test_verdict_to_audit_is_json_safe() -> None:
    """The audit projection is JSON-native (the ordinal renders as its string value)."""
    v = resolve_severity_tier(
        _ladder(), severity=ExcursionSeverity.CRITICAL, principals=_principals(), sod_required=True
    )
    audit = v.to_audit()
    assert audit["resolved_tier_id"] == "qp_release"
    assert audit["severity"] == "critical"
    assert audit["band"] == {"min": "critical", "max": None}
    assert audit["resolved_approver_id"] == "qp-1"
    assert audit["sod_required"] is True
    json.dumps(audit)  # must not raise


# --------------------------------------------------------------------------- #
# The GovernanceActionExecutor dispatch
# --------------------------------------------------------------------------- #


class _RecordingBase:
    """A fake base ACTION executor: pass-through proposal, records that it was delegated to
    (no LLM, no approve()/execute() — render/route/block only)."""

    def __init__(self) -> None:
        self.calls = 0

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        self.calls += 1
        return StepOutcome(
            output=list(input_set),
            reasoning_trace=[{"kind": "rule", "summary": f"propose {step.handler}"}],
            audit={"actor": "agent", "actor_kind": "engine"},
        )


def _severity_step() -> Step:
    return Step(
        step_id="approve",
        name="Approve disposition",
        kind=StepKind.ACTION,
        handler="request_approval",
        governance_content=_ladder(),
        facet=StepFacet(decision_condition=DecisionCondition(gate_kind=GateKind.SEVERITY_TIER)),
    )


def _ctx() -> RunContext:
    return RunContext(agent=Agent(agent_id="a", name="A"), vertical="supply_chain")


async def test_wrapper_dispatches_severity_tier_and_delegates_to_base() -> None:
    base = _RecordingBase()
    wrapper = GovernanceActionExecutor(
        base=base, principals=_principals(), sod_steps=frozenset({"intake", "approve"})
    )
    entities = [{"batch_id": "b-1", "severity": "critical"}]
    outcome = await wrapper.execute(_severity_step(), entities, _ctx())
    assert base.calls == 1  # delegated to base for the proposal
    assert outcome.output == entities
    assert outcome.audit is not None
    assert outcome.audit["governed_kind"] == "severity_tier"
    [verdict] = outcome.audit["severity_tier"]
    assert verdict["resolved_tier_id"] == "qp_release"
    assert verdict["resolved_approver_id"] == "qp-1"
    assert verdict["sod_required"] is True  # 'approve' is a SoD-constrained step
    assert any(t["kind"] == "severity_tier_resolved" for t in outcome.reasoning_trace)


async def test_wrapper_missing_severity_fails_closed_before_base() -> None:
    """An entity carrying no severity fails closed in the wrapper BEFORE the base proposal —
    no proposal is built (render/route/block only)."""
    base = _RecordingBase()
    wrapper = GovernanceActionExecutor(
        base=base, principals=_principals(), sod_steps=frozenset({"approve"})
    )
    with pytest.raises(SeverityTierError, match="no 'severity'"):
        await wrapper.execute(_severity_step(), [{"batch_id": "b-1"}], _ctx())
    assert base.calls == 0


async def test_wrapper_unrecognised_severity_fails_closed() -> None:
    base = _RecordingBase()
    wrapper = GovernanceActionExecutor(
        base=base, principals=_principals(), sod_steps=frozenset({"approve"})
    )
    with pytest.raises(SeverityTierError, match="not a recognised"):
        await wrapper.execute(
            _severity_step(), [{"batch_id": "b-1", "severity": "apocalyptic"}], _ctx()
        )
    assert base.calls == 0


# --------------------------------------------------------------------------- #
# AC-7 — the run-pin determinism invariant (coordination point 7)
# --------------------------------------------------------------------------- #


def test_severity_ladder_governance_pin_is_deterministic() -> None:
    """AC-7 (⚠ coordination point 7): SeverityLadder is list-typed (no set-typed fields), so its
    build_governance_snapshot + compute_governance_hash is STABLE across calls — preserving the
    governance_pin run-pin determinism invariant for the 4th content model (a set field would
    silently break cross-process hash stability)."""
    proc = Procedure(
        procedure_id="p",
        title="P",
        run_by="a",
        steps=[Step(step_id="intake", name="Intake", kind=StepKind.QUERY), _severity_step()],
        separation_of_duties=[SoDConstraint(distinct_steps=frozenset({"intake", "approve"}))],
    )
    snap = build_governance_snapshot(proc)
    assert compute_governance_hash(snap) == compute_governance_hash(build_governance_snapshot(proc))
    [step_snap] = [s for s in snap["steps"] if s["step_id"] == "approve"]
    assert step_snap["governance_content"]["kind"] == "severity_tier"
    assert isinstance(step_snap["governance_content"]["tiers"], list)  # list-typed, not a set
