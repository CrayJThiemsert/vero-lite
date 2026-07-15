"""AC-5 (PLAN-0044 A1b Step 3) — the deterministic ``doa_tier`` executor.

Offline + LLM-free (CLAUDE.md §8 — the offline oracle is the gate). Two surfaces:

* the pure :func:`resolve_doa_tier` — tier routing over the half-open DOA band, the resolved
  approver ``Person``, the structured verdict, ``Decimal`` (never ``float``) spend, and the
  fail-closed currency mismatch (OQ-4);
* the SD-1=(a) :class:`GovernanceActionExecutor` dispatch — a ``doa_tier`` action resolves +
  annotates and delegates to the base for the gated proposal; a non-AT-2 action delegates
  straight through; render / route / block only (no PO, no approve()/execute()).

The pre-committed pass/fail reads are in PLAN-0044 AC-5 — fixed before this test was authored.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from services.engine.procedures.doa_tier import (
    DoaTierError,
    resolve_doa_tier,
)
from services.engine.procedures.governance_step import GovernanceActionExecutor
from services.engine.procedures.orchestrator import RunContext, StepOutcome
from services.engine.procedures.spec import (
    DoaLadder,
    DoaTier,
    EmergencyWaiverPolicy,
    Person,
    Step,
    load_procedures,
)

# --------------------------------------------------------------------------- #
# Fixtures — the procurement-mirror DOA ladder + its approver principals
# --------------------------------------------------------------------------- #


def _ladder() -> DoaLadder:
    """The procurement DOA ladder (procedures.yaml): THB, floors 0 / 50k / 500k / 2M."""
    return DoaLadder(
        currency="THB",
        tiers=[
            DoaTier(min_amount=Decimal("0"), approver_role="หน.จัดซื้อ"),
            DoaTier(min_amount=Decimal("50000"), approver_role="ผจก.จัดซื้อ"),
            DoaTier(min_amount=Decimal("500000"), approver_role="ผจก.โรงงาน"),
            DoaTier(min_amount=Decimal("2000000"), approver_role="ผอ."),
        ],
        emergency_waiver=EmergencyWaiverPolicy(relaxes=["three_bid"], escalate_to="ผอ."),
    )


def _principals() -> list[Person]:
    return [
        Person(person_id="appr-buyer", name="หน.จัดซื้อ", roles=frozenset({"approver", "หน.จัดซื้อ"})),
        Person(person_id="appr-pm", name="ผจก.จัดซื้อ", roles=frozenset({"approver", "ผจก.จัดซื้อ"})),
        Person(
            person_id="appr-plant", name="ผจก.โรงงาน", roles=frozenset({"approver", "ผจก.โรงงาน"})
        ),
        Person(person_id="appr-director", name="ผอ.", roles=frozenset({"approver", "ผอ."})),
    ]


# --------------------------------------------------------------------------- #
# AC-5 — deterministic tier routing over the half-open band
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("amount", "role", "band_min", "band_max"),
    [
        ("0", "หน.จัดซื้อ", "0", "50000"),  # zero floor
        ("45000", "หน.จัดซื้อ", "0", "50000"),  # mid tier-0 (calm-path ฿45k)
        ("49999.99", "หน.จัดซื้อ", "0", "50000"),  # just below the next floor
        ("50000", "ผจก.จัดซื้อ", "50000", "500000"),  # boundary: min is INCLUSIVE (half-open)
        ("288000", "ผจก.จัดซื้อ", "50000", "500000"),
        ("500000", "ผจก.โรงงาน", "500000", "2000000"),
        ("2000000", "ผอ.", "2000000", None),  # top tier — unbounded
        ("2150000", "ผอ.", "2000000", None),  # the hero ฿2.15M
    ],
)
def test_tier_routing_is_deterministic_half_open(
    amount: str, role: str, band_min: str, band_max: str | None
) -> None:
    v = resolve_doa_tier(
        _ladder(),
        amount=Decimal(amount),
        currency="THB",
        principals=_principals(),
        sod_required=True,
    )
    assert v.required_role == role
    assert v.resolved_tier_id == role  # D1: the tier's stable handle is its approver_role
    assert v.band.min == Decimal(band_min)
    assert v.band.max == (None if band_max is None else Decimal(band_max))


def test_spend_is_decimal_not_float() -> None:
    v = resolve_doa_tier(
        _ladder(),
        amount=Decimal("2150000"),
        currency="THB",
        principals=_principals(),
        sod_required=True,
    )
    assert isinstance(v.amount.value, Decimal)
    assert v.amount.value == Decimal("2150000")
    assert v.amount.currency == "THB"
    assert isinstance(v.band.min, Decimal)


def test_resolves_the_approver_person_for_the_tier() -> None:
    """The tier's approver_role resolves to the declared Person holding it (route target)."""
    v = resolve_doa_tier(
        _ladder(),
        amount=Decimal("288000"),
        currency="THB",
        principals=_principals(),
        sod_required=True,
    )
    assert v.resolved_approver_id == "appr-pm"  # holds 'ผจก.จัดซื้อ'
    top = resolve_doa_tier(
        _ladder(),
        amount=Decimal("2150000"),
        currency="THB",
        principals=_principals(),
        sod_required=True,
    )
    assert top.resolved_approver_id == "appr-director"  # holds 'ผอ.'


def test_unresolved_approver_is_none_not_a_raise() -> None:
    """No declared Person is native to the tier role -> resolved_approver_id is None (the
    fail-closed on a wrong / absent approver is the tier-authority run-check's job at the gate —
    PLAN-0075: the acting approver must HOLD the resolved role — kept distinct here, NOT a
    doa_tier raise)."""
    v = resolve_doa_tier(
        _ladder(), amount=Decimal("288000"), currency="THB", principals=[], sod_required=True
    )
    assert v.resolved_approver_id is None


def test_sod_required_is_passed_through() -> None:
    yes = resolve_doa_tier(
        _ladder(), amount=Decimal("0"), currency="THB", principals=_principals(), sod_required=True
    )
    no = resolve_doa_tier(
        _ladder(), amount=Decimal("0"), currency="THB", principals=_principals(), sod_required=False
    )
    assert yes.sod_required is True and no.sod_required is False


# --------------------------------------------------------------------------- #
# AC-5 — fail closed (no silent conversion)
# --------------------------------------------------------------------------- #


def test_currency_mismatch_fails_closed() -> None:
    with pytest.raises(DoaTierError, match="does not match"):
        resolve_doa_tier(
            _ladder(),
            amount=Decimal("288000"),
            currency="USD",
            principals=_principals(),
            sod_required=True,
        )


def test_negative_spend_fails_closed() -> None:
    with pytest.raises(DoaTierError, match="below the ladder's zero floor"):
        resolve_doa_tier(
            _ladder(),
            amount=Decimal("-1"),
            currency="THB",
            principals=_principals(),
            sod_required=True,
        )


def test_verdict_to_audit_is_json_safe() -> None:
    """The audit projection serialises Decimal -> str so the persisted JSONB is safe."""
    v = resolve_doa_tier(
        _ladder(),
        amount=Decimal("2150000"),
        currency="THB",
        principals=_principals(),
        sod_required=True,
    )
    audit = v.to_audit()
    assert audit["resolved_tier_id"] == "ผอ."
    assert audit["amount"] == {"value": "2150000", "currency": "THB"}
    assert audit["band"] == {"min": "2000000", "max": None}
    assert audit["resolved_approver_id"] == "appr-director"
    assert audit["sod_required"] is True
    import json

    json.dumps(audit)  # must not raise (no Decimal leaks)


# --------------------------------------------------------------------------- #
# SD-1=(a) — the GovernanceActionExecutor dispatch
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


def _proc_ctx() -> tuple[Step, Step, RunContext]:
    spec = load_procedures("procurement")
    proc = next(p for p in spec.procedures if p.procedure_id == "emergency_sourcing_round")
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    approve = next(s for s in proc.steps if s.step_id == "approve")  # doa_tier content
    issue_po = next(s for s in proc.steps if s.step_id == "issue_po")  # no governance_content
    ctx = RunContext(agent=agent, vertical="procurement")
    return approve, issue_po, ctx


async def test_wrapper_dispatches_doa_tier_and_delegates_to_base() -> None:
    approve, _, ctx = _proc_ctx()
    base = _RecordingBase()
    wrapper = GovernanceActionExecutor(
        base=base, principals=_principals(), sod_steps=frozenset({"intake", "approve"})
    )
    entities = [{"po_id": "po-1", "amount": "2150000", "currency": "THB"}]
    outcome = await wrapper.execute(approve, entities, ctx)
    assert base.calls == 1  # delegated to base for the proposal
    assert outcome.output == entities  # the base's pass-through proposal
    assert outcome.audit is not None
    assert outcome.audit["governed_kind"] == "doa_tier"
    [verdict] = outcome.audit["doa_tier"]
    assert verdict["resolved_tier_id"] == "ผอ."
    assert verdict["resolved_approver_id"] == "appr-director"
    assert verdict["sod_required"] is True  # 'approve' is a SoD-constrained step
    assert any(t["kind"] == "doa_tier_resolved" for t in outcome.reasoning_trace)


async def test_wrapper_passes_non_at2_action_straight_to_base() -> None:
    _, issue_po, ctx = _proc_ctx()
    base = _RecordingBase()
    wrapper = GovernanceActionExecutor(base=base, principals=_principals())
    entities = [{"po_id": "po-1", "amount": "2150000", "currency": "THB"}]
    outcome = await wrapper.execute(issue_po, entities, ctx)
    assert base.calls == 1
    assert outcome.audit is not None
    assert "governed_kind" not in outcome.audit  # not an AT-2 step — no doa_tier annotation


async def test_wrapper_currency_mismatch_fails_closed_before_base() -> None:
    """A wrong-currency spend fails closed in the wrapper BEFORE the base proposal — no
    proposal is built (render/route/block only)."""
    approve, _, ctx = _proc_ctx()
    base = _RecordingBase()
    wrapper = GovernanceActionExecutor(
        base=base, principals=_principals(), sod_steps=frozenset({"approve"})
    )
    entities = [{"po_id": "po-1", "amount": "2150000", "currency": "USD"}]
    with pytest.raises(DoaTierError):
        await wrapper.execute(approve, entities, ctx)
    assert base.calls == 0  # failed closed before delegating


async def test_wrapper_missing_spend_fails_closed() -> None:
    approve, _, ctx = _proc_ctx()
    base = _RecordingBase()
    wrapper = GovernanceActionExecutor(
        base=base, principals=_principals(), sod_steps=frozenset({"approve"})
    )
    with pytest.raises(DoaTierError, match="no 'amount'"):
        await wrapper.execute(approve, [{"po_id": "po-1"}], ctx)
    assert base.calls == 0
