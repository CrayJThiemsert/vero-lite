"""PLAN-0081 — the building_materials governed-credit HERO, the 3rd AT-2 signature, end to end and
offline.

The 3rd governance-heavy ``request->approve->fulfill`` instance (ADR-0025 D7). It REUSES the money
``doa_tier`` ladder unchanged (THB and all) — no new gate kind, no new authority quantity — and
grows only the criterion vocabulary (``ComplianceCriterion += {kyc, overdue_ar, blacklist}``, the
axis the N=2 finding established as per-instance forever; the D7 re-evaluation is recorded at
``test_at2_signature_retrigger.py``). What these tests prove:

* **AC-1** — the 3-part spine ships all three legs: a per-entity exposure band, a hard
  credit-compliance ``rule_gate`` upstream of the authority gate, and a ``doa_tier`` gated action
  with an SoD constraint binding requester != approver;
* **AC-2** — the reshape seam (measured_value -> flat amount/currency) resolves the DOA tier: an
  in-memory run over the synthetic data reaches ``approve`` with ``amount`` byte-derived from the
  breach ``measured_value`` and SUSPENDS ``waiting_human`` (no ``DoaTierError``, no ``fulfill``);
* **AC-4** — the executor factory is registered (the 409-at-resolve failure mode is covered);
* **AC-5** — SoD + tier authority are enforced: the sales requester cannot approve (SoD), the tier's
  own approver resolves, and a SENIOR approves downward via cumulative roles (PLAN-0075 Policy B);
* **AC-9** — every authored number carries a GUESS marking; the whole path is deterministic-offline.

Offline + host-state-free (CLAUDE.md §8): synthetic adapter, pure band math, pure AT-2 resolution,
stubbed advisory prose — no MS-S1 call, no DB.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from services.api.config import settings
from services.engine.discovery import discover_and_register
from services.engine.procedures.doa_tier import resolve_doa_tier
from services.engine.procedures.orchestrator import run_procedure
from services.engine.procedures.principal_sod import check_principal_sod
from services.engine.procedures.runs import PipelineRunStatus, StepResult
from services.engine.procedures.spec import (
    DoaLadder,
    Procedure,
    VerticalProcedures,
    load_procedures,
)
from services.engine.procedures.tier_authority import (
    TierAuthorityViolationKind,
    check_tier_authority,
)
from services.engine.registry import ExecutorFactory, RegistryError, registry
from verticals.building_materials.procedures_factory import (
    register_building_materials_procedure_executors,
)

_VERTICAL = "building_materials"
_PROCEDURE_ID = "governed_credit_release"
# The shipped synthetic breach: exposure 550,000 THB vs the account's 500,000 limit — mid-ladder.
_BREACH_EXPOSURE = Decimal("550000")


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


@pytest.fixture
async def building_materials_factory(monkeypatch: pytest.MonkeyPatch) -> ExecutorFactory:
    """The registered building_materials factory — the same registration path
    ``services/api/main.py`` runs at startup. ``discover_and_register`` registers the adapter +
    handlers (OQ-6); the factory is the explicit active-vertical registration."""
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    discover_and_register()
    await register_building_materials_procedure_executors()
    return registry.get_procedure_executors(_VERTICAL)


# --------------------------------------------------------------------------- #
# AC-1 — the 3-part spine ships (all three, or the PR does not merge)
# --------------------------------------------------------------------------- #


def test_spine_composition_ships_all_three_legs() -> None:
    """AC-1: ``load_procedures`` returns the hero whose steps carry (a) an ``evaluate`` band with
    ``threshold_field: credit_limit_thb`` / ``direction: above``; (b) a ``rule_gate`` compliance
    step UPSTREAM of (c) a ``doa_tier`` gated action plus an SoD constraint binding
    requester != approver. A ladder-only form (missing the rule_gate) is the hollow-governance
    shape PLAN-0079 forbids."""
    proc = _hero(load_procedures(_VERTICAL))

    # (a) the per-entity exposure band
    judge = next(s for s in proc.steps if s.step_id == "judge")
    assert judge.threshold_field == "credit_limit_thb"
    assert judge.direction == "above"

    # (b) rule_gate upstream of (c) doa_tier — read off the TYPED governance_content, in step order
    gate_kinds = tuple(
        s.governance_content.kind for s in proc.steps if s.governance_content is not None
    )
    assert gate_kinds == ("rule_gate", "doa_tier")

    # (c) the SoD constraint binds requester != approver on distinct steps
    assert proc.separation_of_duties, "a doa_tier gate REQUIRES an SoD constraint (ADR-0025 D5)"
    [sod] = proc.separation_of_duties
    assert sod.distinct_steps == frozenset({"intake", "approve"})
    assert sod.required_roles == {"intake": "requester", "approve": "approver"}


# --------------------------------------------------------------------------- #
# AC-2 — the reshape seam resolves the DOA tier (the L-2 seam, first-class)
# --------------------------------------------------------------------------- #


async def test_run_suspends_at_the_doa_tier_gate_with_reshaped_spend(
    building_materials_factory: ExecutorFactory,
) -> None:
    """AC-2: intake -> judge -> reshape -> credit_gate -> approve, over the REAL building_materials
    YAML + ontology + synthetic adapter. The run SUSPENDS at ``approve`` (waiting_human): the
    release is proposed to the human credit authority the exposure demands, and ``fulfill`` never
    runs. The ``amount`` the DOA tier routes on is byte-derived from the breach ``measured_value``
    (no ``DoaTierError``)."""
    spec = load_procedures(_VERTICAL)
    proc = _hero(spec)
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)

    result = await run_procedure(
        proc, agent, building_materials_factory(), vertical=_VERTICAL, run_id="bm-at2-e2e"
    )

    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    by_step = {step.step_id: step for step in result.step_results}
    # the gated `approve` suspended the run — `fulfill` (the release write) never executed.
    assert set(by_step) == {"intake", "judge", "reshape", "credit_gate", "approve"}
    assert "fulfill" not in by_step
    # the run RECORDED the SoD requester half — the live principal-SoD check is armed for real.
    assert result.run.step_principals is not None

    # --- reshape: the exposure became a flat governed spend, byte-derived from measured_value ---
    reshaped = _output_set(by_step["reshape"])[0]
    assert Decimal(reshaped["amount"]) == _BREACH_EXPOSURE  # 550,000, Decimal-exact via the coerce
    assert reshaped["currency"] == "THB"
    assert reshaped["compliance"] == {"kyc": True, "overdue_ar": True, "blacklist": True}

    # --- credit_gate: the account cleared every credit-compliance criterion ---
    gate_audit = _audit(by_step["credit_gate"])
    assert gate_audit["governed_kind"] == "rule_gate"
    [compliance] = gate_audit["rule_gate"]
    assert compliance["compliant"] is True
    assert {r["criterion"] for r in compliance["results"]} == {"kyc", "overdue_ar", "blacklist"}

    # --- approve: the money doa_tier routed the FULL exposure to the mid-ladder authority ---
    approve_audit = _audit(by_step["approve"])
    assert approve_audit["governed_kind"] == "doa_tier"
    [verdict] = approve_audit["doa_tier"]
    assert verdict["required_role"] == "ผจก.ควบคุมเครดิต"  # [250k,1M) — tiering, not always-the-top
    assert verdict["resolved_approver_id"] == "appr-credit-manager"
    assert verdict["sod_required"] is True  # `approve` is SoD-constrained vs `intake` (derived)
    assert Decimal(verdict["amount"]["value"]) == _BREACH_EXPOSURE
    assert verdict["amount"]["currency"] == "THB"

    # the gated action PROPOSED only — nothing was executed (ADR-0007 approve->execute, LOCKED #3)
    proposals = _output_set(by_step["approve"])
    assert all(p["status"] == "proposed" for p in proposals)
    assert all(p["action"]["suggested_handler"] == "escalate" for p in proposals)


# --------------------------------------------------------------------------- #
# AC-4 — the executor factory is wired (coordination point i)
# --------------------------------------------------------------------------- #


async def test_factory_registration_covers_the_409_at_resolve(
    building_materials_factory: ExecutorFactory,
) -> None:
    """AC-4 (the PLAN-0062 AC-5 pattern): after the registrar runs,
    ``registry.get_procedure_executors('building_materials')`` succeeds and yields the four
    StepKind executors — the 409-at-gate-resolve failure mode (a fired run with no factory) is
    covered."""
    executors = building_materials_factory()
    assert {kind.name for kind in executors} == {"QUERY", "EVALUATE", "ACTION", "TRANSFORM"}


def test_unregistered_vertical_409s_at_resolve() -> None:
    """The contract the registrar exists to satisfy: with no factory registered (the autouse
    ``_reset_registry`` wipes it before this test, and this test never registers one), resolving the
    procedure executors raises the ``RegistryError`` the gate-resolve endpoint surfaces as a 409."""
    with pytest.raises(RegistryError):
        registry.get_procedure_executors(_VERTICAL)


# --------------------------------------------------------------------------- #
# AC-5 — SoD + tier authority are demonstrably enforced
# --------------------------------------------------------------------------- #


def _persisted_verdict(proc: Procedure, spec: VerticalProcedures) -> dict[str, Any]:
    """The doa_tier verdict the run persists for the shipped 550k breach — resolved off the SHIPPED
    ladder + roster so the test tracks the YAML, never a hand-copied constant."""
    verdict = resolve_doa_tier(
        _ladder(proc),
        amount=_BREACH_EXPOSURE,
        currency="THB",
        principals=list(spec.principals),
        sod_required=True,
    )
    return verdict.to_audit()


def test_tier_the_own_approver_resolves() -> None:
    """AC-5(ii): the native-tier approver for the 550k exposure (appr-credit-manager, holding
    ผจก.ควบคุมเครดิต) PASSES the tier-authority gate."""
    spec = load_procedures(_VERTICAL)
    proc = _hero(spec)
    manager = next(p for p in spec.principals if p.person_id == "appr-credit-manager")
    verdict = check_tier_authority(
        principal=manager,
        step_id="approve",
        governance_content=_ladder(proc),
        persisted_verdicts=[_persisted_verdict(proc, spec)],
        declared_principals=list(spec.principals),
    )
    assert verdict.governed is True


def test_junior_credit_officer_is_refused_upward() -> None:
    """AC-5: the junior (appr-credit-officer, holds only จนท.เครดิต — the [0,250k) tier) is REFUSED
    at the 550k gate the ladder routed to ผจก.ควบคุมเครดิต. A lower tier cannot resolve a higher
    gate."""
    spec = load_procedures(_VERTICAL)
    proc = _hero(spec)
    officer = next(p for p in spec.principals if p.person_id == "appr-credit-officer")
    verdict = check_tier_authority(
        principal=officer,
        step_id="approve",
        governance_content=_ladder(proc),
        persisted_verdicts=[_persisted_verdict(proc, spec)],
        declared_principals=list(spec.principals),
    )
    assert verdict.governed is False
    assert [v.kind for v in verdict.violations] == [TierAuthorityViolationKind.TIER_ROLE_MISMATCH]
    assert verdict.violations[0].required_role == "ผจก.ควบคุมเครดิต"


def test_senior_finance_director_approves_downward() -> None:
    """AC-5(iii) — PLAN-0075 Policy B: the SENIOR (appr-finance-director) holds ผจก.ควบคุมเครดิต
    cumulatively, so they PASS the 550k gate — 'senior can approve downward'. This is the behaviour
    the cumulative role authoring in the roster exists to grant."""
    spec = load_procedures(_VERTICAL)
    proc = _hero(spec)
    director = next(p for p in spec.principals if p.person_id == "appr-finance-director")
    verdict = check_tier_authority(
        principal=director,
        step_id="approve",
        governance_content=_ladder(proc),
        persisted_verdicts=[_persisted_verdict(proc, spec)],
        declared_principals=list(spec.principals),
    )
    assert verdict.governed is True


def test_sod_requester_cannot_be_the_approver() -> None:
    """AC-5(i): SoD (ADR-0026 D4) — the sales principal who requested the release (``intake``)
    cannot also approve it. A run where both SoD steps resolve to the SAME human fails CLOSED
    (the two-into-one collapse); a distinct approver passes."""
    spec = load_procedures(_VERTICAL)
    proc = _hero(spec)
    principals = list(spec.principals)

    # collapse: the sales requester acts on BOTH intake and approve -> fail closed
    collapsed = check_principal_sod(
        proc,
        principals=principals,
        principal_aliases=[],
        step_principals={"intake": "req-sales", "approve": "req-sales"},
    )
    assert collapsed.governed is False

    # distinct humans (sales requests, credit-control approves) -> passes
    distinct = check_principal_sod(
        proc,
        principals=principals,
        principal_aliases=[],
        step_principals={"intake": "req-sales", "approve": "appr-credit-manager"},
    )
    assert distinct.governed is True


# --------------------------------------------------------------------------- #
# AC-9 — demo discipline (ADR-0032 D1): every authored number is GUESS-marked
# --------------------------------------------------------------------------- #


def test_authored_values_are_guess_marked() -> None:
    """AC-9: the ladder tiers, the compliance criteria signals, and the principal roster carry a
    'GUESS — รอแก้' marking in the YAML comments (the partner's 'correct me' surface, ADR-0032 D1
    guess-then-react). Grep-level: the marker appears, and it is not a lone stray."""
    yaml_text = Path("verticals/building_materials/procedures.yaml").read_text(encoding="utf-8")
    assert "GUESS" in yaml_text
    # the three authored surfaces the PLAN names (roster / ladder / criteria) each sit near a GUESS
    # marker — a spot-check that the discipline is applied, not a single decorative token.
    assert yaml_text.count("GUESS") >= 3
    assert "รอแก้" in yaml_text
