"""AC-8 (PLAN-0044 A1b Step 6) — the typed, queryable governed_decision audit-to-control field.

Offline + LLM-free (CLAUDE.md §8). Covers the typed shape (SD-3=(a)), the stable SoD
``constraint_id`` derivation (D2), and the ``doa_tier`` engine side-effect emission. The SoD-gate
emission (the DB-backed ``resolve_gated_step`` path) is exercised in
``tests/services/db/test_procurement_sod_gate.py``.

Pre-committed pass/fail reads: PLAN-0044 AC-8 — fixed before this test was authored.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from services.engine.actions import AuditMetadata, ControlRef, GovernedDecision
from services.engine.procedures.governance_step import GovernanceActionExecutor
from services.engine.procedures.orchestrator import RunContext, StepOutcome
from services.engine.procedures.spec import Person, SoDConstraint, Step, load_procedures

# --------------------------------------------------------------------------- #
# The typed shape (SD-3=(a)) — minimal, not free prose / Any / dict-blob
# --------------------------------------------------------------------------- #


def test_governed_decision_is_typed_and_minimal() -> None:
    gd = GovernedDecision(
        control_ref=ControlRef(kind="doa_tier", id="ผอ."), principal_id="appr-director"
    )
    assert gd.control_ref.kind == "doa_tier"
    assert gd.control_ref.id == "ผอ."
    assert gd.principal_id == "appr-director"
    # minimal — extra fields are forbidden (does NOT expand toward the ADR-011 framework)
    with pytest.raises(ValidationError):
        GovernedDecision(
            control_ref=ControlRef(kind="sod", id="x"),
            principal_id="p",
            attestation="nope",  # type: ignore[call-arg]
        )
    # the control family is a closed set (doa_tier | sod)
    with pytest.raises(ValidationError):
        ControlRef(kind="rule_gate", id="x")  # type: ignore[arg-type]


def test_audit_metadata_governed_decision_defaults_none() -> None:
    am = AuditMetadata(actor="agent", actor_kind="engine")
    assert am.governed_decision is None
    am2 = AuditMetadata(
        actor="agent",
        actor_kind="engine",
        governed_decision=GovernedDecision(
            control_ref=ControlRef(kind="sod", id="approve+intake"), principal_id="appr-buyer"
        ),
    )
    assert am2.governed_decision is not None
    assert am2.governed_decision.control_ref.id == "approve+intake"


def test_sod_constraint_id_is_sorted_distinct_steps() -> None:
    """D2: the stable SoD control id is the sorted '+'-joined distinct_steps — derived identically
    wherever a control_ref names it, so audit -> control joins exactly (no new schema field)."""
    c = SoDConstraint(
        distinct_steps=frozenset({"approve", "intake"}),
        required_roles={"intake": "requester", "approve": "approver"},
    )
    assert c.constraint_id == "approve+intake"


# --------------------------------------------------------------------------- #
# AC-8 — the doa_tier engine side-effect emission
# --------------------------------------------------------------------------- #


class _RecordingBase:
    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(output=list(input_set), audit={"actor": "agent", "actor_kind": "engine"})


def _approve_ctx() -> tuple[Step, RunContext]:
    spec = load_procedures("procurement")
    proc = next(p for p in spec.procedures if p.procedure_id == "emergency_sourcing_round")
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    approve = next(s for s in proc.steps if s.step_id == "approve")
    return approve, RunContext(agent=agent, vertical="procurement")


def _principals() -> list[Person]:
    return [
        Person(person_id="appr-director", name="ผอ.", roles=frozenset({"approver", "ผอ."})),
    ]


async def test_doa_tier_emits_governed_decision_tied_to_control_and_principal() -> None:
    """The doa_tier route emits a typed governed_decision into the step audit: control_ref
    {kind:'doa_tier', id: the verdict's resolved_tier_id} + principal_id: the resolved approver
    (a canonical Person PK). This is the field the hero render joins on."""
    approve, ctx = _approve_ctx()
    wrapper = GovernanceActionExecutor(
        base=_RecordingBase(), principals=_principals(), sod_steps=frozenset({"intake", "approve"})
    )
    outcome = await wrapper.execute(
        approve, [{"po_id": "po-1", "amount": "2150000", "currency": "THB"}], ctx
    )
    assert outcome.audit is not None
    assert outcome.audit["governed_decision"] == [
        {"control_ref": {"kind": "doa_tier", "id": "ผอ."}, "principal_id": "appr-director"}
    ]


async def test_doa_tier_emits_no_tie_without_a_resolved_approver() -> None:
    """A tier whose approver_role resolves to no declared Person emits no tie (no principal to
    name — the unresolved-approver case fails closed at the SoD gate, Step 1, not here)."""
    approve, ctx = _approve_ctx()
    wrapper = GovernanceActionExecutor(
        base=_RecordingBase(), principals=[], sod_steps=frozenset({"intake", "approve"})
    )
    outcome = await wrapper.execute(
        approve, [{"po_id": "po-1", "amount": "2150000", "currency": "THB"}], ctx
    )
    assert outcome.audit is not None
    assert outcome.audit["governed_decision"] == []
