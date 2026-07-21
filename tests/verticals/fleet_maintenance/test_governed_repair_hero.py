"""PLAN-0086 — the fleet_maintenance governed-repair HERO, end to end and offline.

The 6th vertical, hand-written under the timed-scaffold measurement. NOT a 4th AT-2 signature: the
money ``doa_tier`` ladder is REUSED unchanged (THB and all) and the criterion vocabulary grows by
one instance-scoped member (``ComplianceCriterion += {three_quote}``) — exactly the per-instance
axis the N=2 finding established and PLAN-0081 re-confirmed at N=3 (ADR-0025 D7).

What is genuinely NEW here is PLAN-0086 L-B: this is the FIRST vertical whose factory ships the
PLAN-0085 gate advisory ON by default, so the parked gate is readable on day one. The fence tests
below hold that advisory to the ADR-0030 D5 shown-never-routes contract with advisory-ON as the
DEFAULT arm (the inverse of the PLAN-0085 fences, which had procurement opt in).

What these tests prove:

* **AC-1** — the 3-part spine ships all three legs: a per-truck repair-ceiling band, a hard
  sourcing-hygiene ``rule_gate`` upstream of the authority gate, and a ``doa_tier`` gated action
  with an SoD constraint binding requester != approver;
* **AC-2** — an in-memory run over the synthetic data reaches ``approve`` with ``amount``
  byte-derived from the breaching quote, SUSPENDS ``waiting_human``, and carries the grounded
  advisory in the persisted approve-step trace (no confidence key anywhere);
* **AC-3** — narrative fidelity: every ฿ value and role in the shipped YAML matches the customer's
  logged answers, asserted against the YAML itself so prose drift cannot pass;
* **AC-5** — the advisory fence: present by default, audit byte-identical vs a ``builder=None``
  arm, and a raising builder cannot fail / park / divert the run.

Offline + host-state-free (CLAUDE.md §8): synthetic adapter, pure band math, pure AT-2 resolution,
stubbed advisory prose, deterministic gate advisory — no MS-S1 call, no DB.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from services.api.config import settings
from services.engine.discovery import discover_and_register
from services.engine.ontology_meta import load_ontology_meta
from services.engine.procedures.action_step import ActionStepExecutor
from services.engine.procedures.advisory_stub import advisory_stub_factory
from services.engine.procedures.evaluate_step import EvaluateStepExecutor
from services.engine.procedures.gate_advisory import GateAdvisoryBuilder
from services.engine.procedures.governance_step import (
    GovernanceActionExecutor,
    GovernanceEvaluateExecutor,
)
from services.engine.procedures.orchestrator import StepExecutor, run_procedure
from services.engine.procedures.principal_sod import check_principal_sod
from services.engine.procedures.query_step import QueryStepExecutor
from services.engine.procedures.runs import PipelineRunStatus, StepResult
from services.engine.procedures.spec import (
    DoaLadder,
    Procedure,
    StepKind,
    VerticalProcedures,
    load_procedures,
)
from services.engine.procedures.tier_authority import check_tier_authority
from services.engine.procedures.transform_step import TransformStepExecutor
from services.engine.registry import ExecutorFactory, RegistryError, registry
from verticals.fleet_maintenance.procedures_factory import (
    register_fleet_maintenance_procedure_executors,
)

_VERTICAL = "fleet_maintenance"
_PROCEDURE_ID = "governed_repair_approval"
# The shipped synthetic breach: a ฿48,000 axle repair vs the truck's ฿5,000 ceiling — MID-ladder,
# so the demo shows tiering rather than always-the-top.
_BREACH_QUOTE = Decimal("48000.0")
# The customer's ladder, verbatim from question-log Q1 ("ต้อมเคาะได้ถึง 5 พัน วิรัชถึง 5 หมื่น เกินนั้นผมเอง").
_LADDER_ANSWER = (
    (Decimal("0"), "ช่างใหญ่"),
    (Decimal("5000"), "ผจก.เดินรถ"),
    (Decimal("50000"), "เจ้าของกิจการ"),
)


def _hero(spec: VerticalProcedures) -> Procedure:
    return next(p for p in spec.procedures if p.procedure_id == _PROCEDURE_ID)


def _ladder(proc: Procedure) -> DoaLadder:
    ladder = next(s.governance_content for s in proc.steps if s.step_id == "approve")
    assert isinstance(ladder, DoaLadder)
    return ladder


def _audit(step_result: StepResult) -> dict[str, Any]:
    audit = step_result.audit
    assert audit is not None, f"step '{step_result.step_id}' emitted no audit"
    return audit


def _output_set(step_result: StepResult) -> list[Any]:
    artifact = step_result.artifact
    assert artifact is not None, f"step '{step_result.step_id}' produced no artifact"
    rows = artifact["output_set"]
    assert isinstance(rows, list)
    return rows


def _trace_dicts(step_result: StepResult) -> list[dict[str, Any]]:
    return [t if isinstance(t, dict) else t.model_dump() for t in step_result.reasoning_trace]


@pytest.fixture
async def fleet_factory(monkeypatch: pytest.MonkeyPatch) -> ExecutorFactory:
    """The registered fleet_maintenance factory — the same registration path
    ``services/api/main.py`` runs at startup."""
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    return registry.get_procedure_executors(_VERTICAL)


async def _run(factory: ExecutorFactory, run_id: str) -> dict[str, StepResult]:
    spec = load_procedures(_VERTICAL)
    proc = _hero(spec)
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    result = await run_procedure(proc, agent, factory(), vertical=_VERTICAL, run_id=run_id)
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    return {step.step_id: step for step in result.step_results}


# --------------------------------------------------------------------------- #
# AC-1 — the 3-part spine ships (all three, or the PR does not merge)
# --------------------------------------------------------------------------- #


def test_spine_composition_ships_all_three_legs() -> None:
    """AC-1: the hero's steps carry (a) a per-truck ``evaluate`` band on
    ``minor_repair_ceiling_thb`` / ``direction: above``; (b) a ``rule_gate`` sourcing step UPSTREAM
    of (c) a ``doa_tier`` gated action plus an SoD constraint binding requester != approver. A
    ladder-only form (missing the rule_gate) is the hollow-governance shape PLAN-0079 forbids."""
    proc = _hero(load_procedures(_VERTICAL))

    judge = next(s for s in proc.steps if s.step_id == "judge")
    assert judge.threshold_field == "minor_repair_ceiling_thb"
    assert judge.direction == "above"

    gate_kinds = tuple(
        s.governance_content.kind for s in proc.steps if s.governance_content is not None
    )
    assert gate_kinds == ("rule_gate", "doa_tier")

    assert proc.separation_of_duties, "a doa_tier gate REQUIRES an SoD constraint (ADR-0025 D5)"
    [sod] = proc.separation_of_duties
    assert sod.distinct_steps == frozenset({"intake", "approve"})
    assert sod.required_roles == {"intake": "requester", "approve": "approver"}


# --------------------------------------------------------------------------- #
# AC-3 — narrative fidelity: the shipped ฿ and roles ARE the customer's answers
# --------------------------------------------------------------------------- #


def test_shipped_ladder_matches_the_customer_answer() -> None:
    """AC-3: the ladder in the shipped YAML is the customer's Q1 answer, tier for tier. This is the
    spot-auditable half of narrative fidelity — a later edit that 'tidies' a threshold silently
    breaks it, which is exactly the drift PLAN-0086 exists to prevent."""
    ladder = _ladder(_hero(load_procedures(_VERTICAL)))
    assert tuple((t.min_amount, t.approver_role) for t in ladder.tiers) == _LADDER_ANSWER
    assert ladder.currency == "THB"


def test_emergency_waiver_relaxes_the_constraint_the_customer_described() -> None:
    """AC-3: the customer volunteered the roadside bypass ("ซ่อมไปก่อน ซื้อร้านข้างทางไปเลย"). The
    only constraint that bypass actually breaks is the three-quote comparison, so the waiver relaxes
    ``three_bid`` and escalates to the owner — who is who the driver phones in the narrative. It
    never skips the gate."""
    waiver = _ladder(_hero(load_procedures(_VERTICAL))).emergency_waiver
    assert waiver is not None, "a DoaLadder REQUIRES an emergency_waiver (ADR-0025 D3)"
    assert [r.value for r in waiver.relaxes] == ["three_bid"]
    assert waiver.escalate_to == "เจ้าของกิจการ"
    assert waiver.requires_justification is True


def test_requester_holds_no_approver_role() -> None:
    """AC-3: the customer's own กฎเหล็ก ("คนทำเรื่องเบิกห้ามเป็นคนอนุมัติเอง") is structural, not
    just a comment: the head mechanic who files carries ``requester`` and NOTHING else, while the
    fleet manager carries ``ช่างใหญ่`` cumulatively so he can approve DOWN into the mechanic's own
    tier — the mechanism behind the customer's Q3 answer 'ต้อมตั้งเรื่อง วิรัชเคาะแทน'."""
    spec = load_procedures(_VERTICAL)
    mechanic = next(p for p in spec.principals if p.person_id == "req-mechanic-tom")
    manager = next(p for p in spec.principals if p.person_id == "appr-fleet-manager-wirat")
    assert set(mechanic.roles) == {"requester"}
    assert "approver" in manager.roles and "ช่างใหญ่" in manager.roles


def test_narrative_provenance_block_is_present() -> None:
    """AC-3: the YAML carries the provenance header mapping every authored ฿/role/rule back to a
    narrative sentence or a logged customer answer. Unlike the other verticals' 'GUESS — รอแก้'
    marking, these numbers are NOT guesses — they came from the customer — so the discipline this
    vertical must carry is TRACEABILITY, and the header is where it lives."""
    yaml_text = Path("verticals/fleet_maintenance/procedures.yaml").read_text(encoding="utf-8")
    assert "NARRATIVE PROVENANCE" in yaml_text
    for marker in ("Q1", "Q3", "Q4"):
        assert marker in yaml_text, f"provenance header lost its {marker} citation"


# --------------------------------------------------------------------------- #
# AC-2 — the run parks at the gate with the advisory already in the trace
# --------------------------------------------------------------------------- #


async def test_run_suspends_at_the_doa_tier_gate_with_reshaped_spend(
    fleet_factory: ExecutorFactory,
) -> None:
    """AC-2: intake -> judge -> reshape -> quote_gate -> approve, over the REAL fleet_maintenance
    YAML + ontology + synthetic adapter. The run SUSPENDS at ``approve`` (waiting_human) and
    ``fulfill`` never runs. The ``amount`` the DOA tier routes on is byte-derived from the breaching
    quote, and the ฿48,000 lands MID-ladder (the fleet manager), not at the owner."""
    by_step = await _run(fleet_factory, "fleet-at2-e2e")

    assert set(by_step) == {"intake", "judge", "reshape", "quote_gate", "approve"}
    assert "fulfill" not in by_step

    reshaped = _output_set(by_step["reshape"])[0]
    assert Decimal(reshaped["amount"]) == _BREACH_QUOTE
    assert reshaped["currency"] == "THB"
    assert reshaped["compliance"] == {"three_quote": True}

    gate_audit = _audit(by_step["quote_gate"])
    assert gate_audit["governed_kind"] == "rule_gate"
    [compliance] = gate_audit["rule_gate"]
    assert compliance["compliant"] is True
    assert {r["criterion"] for r in compliance["results"]} == {"three_quote"}

    approve_audit = _audit(by_step["approve"])
    assert approve_audit["governed_kind"] == "doa_tier"
    [verdict] = approve_audit["doa_tier"]
    assert verdict["required_role"] == "ผจก.เดินรถ"  # [5k,50k) — tiering, not always-the-top
    assert verdict["resolved_approver_id"] == "appr-fleet-manager-wirat"
    assert verdict["sod_required"] is True
    assert Decimal(verdict["amount"]["value"]) == _BREACH_QUOTE
    assert verdict["amount"]["currency"] == "THB"

    proposals = _output_set(by_step["approve"])
    assert all(p["status"] == "proposed" for p in proposals)
    assert all(p["action"]["suggested_handler"] == "escalate" for p in proposals)


async def test_advisory_is_present_and_grounded_by_default(
    fleet_factory: ExecutorFactory,
) -> None:
    """AC-2 / L-B: the parked approve step carries the advisory ALREADY — this vertical ships it ON.
    The reasons are grounded in the run's own data (the actual ฿ figure, the actual resolved
    approver), the arm is disclosed as ``deterministic``, and NO confidence key appears anywhere in
    the trace (PLAN-0085 AC-8 — a fabricated confidence number is worse than none)."""
    by_step = await _run(fleet_factory, "fleet-advisory")
    trace = _trace_dicts(by_step["approve"])

    kinds = [t.get("kind") for t in trace]
    assert "advisory_recommendation" in kinds
    # the advisory is APPENDED — the governed records come first, so it can never be mistaken
    # for the routing decision itself.
    assert kinds.index("doa_tier_resolved") < kinds.index("advisory_recommendation")

    advisory = next(t for t in trace if t.get("kind") == "advisory_recommendation")
    detail = advisory["detail"]
    assert detail["model"] == "deterministic"
    assert detail["resolved_approver_id"] == "appr-fleet-manager-wirat"
    assert detail["tier"] == "ผจก.เดินรถ"
    # grounded, not generic: the run's own figure appears in the prose
    assert any("48000" in reason for reason in detail["reasons"])
    assert "confidence" not in str(trace)


# --------------------------------------------------------------------------- #
# AC-5 — the advisory fence, with advisory-ON as the DEFAULT arm
# --------------------------------------------------------------------------- #


def _executors(advisory_builder: Any) -> dict[StepKind, StepExecutor]:
    """The fleet executor map with an INJECTED advisory builder — the A/B arm the fence needs.
    Mirrors ``procedures_factory.factory()`` exactly except for the injected builder."""
    spec = load_procedures(_VERTICAL)
    meta = load_ontology_meta(_VERTICAL)
    sod_steps = frozenset(
        step_id
        for procedure in spec.procedures
        for constraint in procedure.separation_of_duties
        for step_id in constraint.distinct_steps
    )
    return {
        StepKind.QUERY: QueryStepExecutor(
            adapter=registry.get_adapter(_VERTICAL),
            object_type_names=frozenset(o.name for o in meta.object_types),
            meta=meta,
        ),
        StepKind.EVALUATE: GovernanceEvaluateExecutor(base=EvaluateStepExecutor()),
        StepKind.ACTION: GovernanceActionExecutor(
            base=ActionStepExecutor(client_factory=advisory_stub_factory),
            principals=list(spec.principals),
            sod_steps=sod_steps,
            advisory_builder=advisory_builder,
        ),
        StepKind.TRANSFORM: TransformStepExecutor(),
    }


async def test_audit_is_byte_identical_without_the_advisory(
    fleet_factory: ExecutorFactory,
) -> None:
    """AC-5: the advisory is SHOWN, it never ROUTES. Running the same procedure with the builder
    removed produces a byte-identical approve-step audit block — the advisory lives in the trace
    only, so no downstream consumer of the governed record can be influenced by it."""
    with_advisory = await _run(fleet_factory, "fleet-fence-on")
    without = await _run(lambda: _executors(None), "fleet-fence-off")

    assert _audit(without["approve"]) == _audit(with_advisory["approve"])
    # and the difference is confined to the trace
    assert "advisory_recommendation" in [
        t.get("kind") for t in _trace_dicts(with_advisory["approve"])
    ]
    assert "advisory_recommendation" not in [
        t.get("kind") for t in _trace_dicts(without["approve"])
    ]


async def test_a_raising_advisory_builder_cannot_break_the_run(
    fleet_factory: ExecutorFactory,
) -> None:
    """AC-5 / ADR-0030 D5 (never-raise): an advisory whose construction explodes must not fail the
    run, must not divert it, and must not change where it parks. The gate is governance; the
    advisory is commentary — commentary is never load-bearing.

    NOTE on where the guarantee lives (a PLAN-0086 finding, recorded in the seam ledger): the
    never-raise contract is implemented INSIDE ``GateAdvisoryBuilder.build``, which catches
    everything (``gate_advisory.py``). The call site in ``governance_step.py`` awaits the builder
    WITHOUT its own guard. So the guarantee covers the shipped builder and its subclasses — it does
    NOT make an arbitrary foreign builder object safe. This test therefore injects the failure the
    way PLAN-0085 does (subclass, break ``_entry``), which is the contract that actually exists."""

    class _Exploding(GateAdvisoryBuilder):
        """Test double: entry construction ALWAYS raises — ``build`` must swallow it."""

        async def _entry(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
            raise RuntimeError("forced advisory failure (AC-5)")

    by_step = await _run(lambda: _executors(_Exploding()), "fleet-fence-raise")

    assert set(by_step) == {"intake", "judge", "reshape", "quote_gate", "approve"}
    [verdict] = _audit(by_step["approve"])["doa_tier"]
    assert verdict["resolved_approver_id"] == "appr-fleet-manager-wirat"
    assert "advisory_recommendation" not in [
        t.get("kind") for t in _trace_dicts(by_step["approve"])
    ]


# --------------------------------------------------------------------------- #
# factory wiring + SoD / tier authority
# --------------------------------------------------------------------------- #


async def test_factory_registration_covers_the_409_at_resolve(
    fleet_factory: ExecutorFactory,
) -> None:
    """The PLAN-0062 AC-5 pattern: after the registrar runs, the four StepKind executors resolve —
    the 409-at-gate-resolve failure mode (a fired run with no factory) is covered."""
    executors = fleet_factory()
    assert {kind.name for kind in executors} == {"QUERY", "EVALUATE", "ACTION", "TRANSFORM"}


def test_unregistered_vertical_409s_at_resolve() -> None:
    """With no factory registered (the autouse ``_reset_registry`` wipes it), resolving raises the
    ``RegistryError`` the gate-resolve endpoint surfaces as a 409."""
    with pytest.raises(RegistryError):
        registry.get_procedure_executors(_VERTICAL)


def _persisted_verdict(proc: Procedure, spec: VerticalProcedures) -> dict[str, Any]:
    from services.engine.procedures.doa_tier import resolve_doa_tier

    return resolve_doa_tier(
        _ladder(proc),
        amount=_BREACH_QUOTE,
        currency="THB",
        principals=list(spec.principals),
        sod_required=True,
    ).to_audit()


def test_fleet_manager_resolves_his_native_tier() -> None:
    """The ฿48,000 quote routes to ผจก.เดินรถ, and วิรัช holds it — he PASSES the tier gate."""
    spec = load_procedures(_VERTICAL)
    proc = _hero(spec)
    manager = next(p for p in spec.principals if p.person_id == "appr-fleet-manager-wirat")
    verdict = check_tier_authority(
        principal=manager,
        step_id="approve",
        governance_content=_ladder(proc),
        persisted_verdicts=[_persisted_verdict(proc, spec)],
        declared_principals=list(spec.principals),
    )
    assert verdict.governed is True


def test_owner_approves_downward() -> None:
    """PLAN-0075 Policy B: the owner holds ผจก.เดินรถ cumulatively, so he PASSES the ฿48,000 gate —
    'senior can approve downward'. The customer said it plainly: หนักๆ ต้องมาถึงผม, but he can
    obviously sign for less."""
    spec = load_procedures(_VERTICAL)
    proc = _hero(spec)
    owner = next(p for p in spec.principals if p.person_id == "appr-owner")
    verdict = check_tier_authority(
        principal=owner,
        step_id="approve",
        governance_content=_ladder(proc),
        persisted_verdicts=[_persisted_verdict(proc, spec)],
        declared_principals=list(spec.principals),
    )
    assert verdict.governed is True


def test_sod_requester_cannot_be_the_approver() -> None:
    """The customer's กฎเหล็ก, enforced: a run where the mechanic occupies BOTH SoD steps fails
    CLOSED (the two-into-one collapse); mechanic-requests / manager-approves passes. This is the
    rule he adopted after being defrauded — it is the one rule he asked for by name."""
    spec = load_procedures(_VERTICAL)
    proc = _hero(spec)
    principals = list(spec.principals)

    collapsed = check_principal_sod(
        proc,
        principals=principals,
        principal_aliases=[],
        step_principals={"intake": "req-mechanic-tom", "approve": "req-mechanic-tom"},
    )
    assert collapsed.governed is False

    distinct = check_principal_sod(
        proc,
        principals=principals,
        principal_aliases=[],
        step_principals={"intake": "req-mechanic-tom", "approve": "appr-fleet-manager-wirat"},
    )
    assert distinct.governed is True
