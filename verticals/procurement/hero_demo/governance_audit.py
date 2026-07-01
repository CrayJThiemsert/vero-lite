"""Deterministic offline capture of the hero-demo GOVERNANCE MOMENT audit (PLAN-0045 Step 1b).

**SD-1 = Layered — this is the OFFLINE-fixture arm** (the CI gate + the demo fallback). It runs the
**real shipped A1b engine functions** over the Fastenal DOA ladder + principals loaded from the C1
CSV dataset, and captures the exact gate audit the governance-moment render binds to:

* :func:`~services.engine.procedures.doa_tier.resolve_doa_tier` — the ``doa_tier`` executor
  (ADR-0026): ฿ spend → the half-open DOA band → the required approver role → the resolved
  :class:`Person` (the hero ฿288,000 crosses the ฿200,000 Manager ceiling → ``CONTROLLER``);
* :func:`~services.engine.procedures.principal_sod.check_principal_sod` — the fail-closed SoD
  run-check (ADR-0026 D4): the requester (MAINT_PLANNER) and the approver (CONTROLLER) resolve to
  two DISTINCT principals → ``governed``;
* :class:`~services.engine.actions.GovernedDecision` / :class:`~services.engine.actions.ControlRef`
  — the typed audit-to-control tie (ADR-0026 D6), on the SHIPPED join keys
  (``control_ref.id == resolved_tier_id`` for ``doa_tier``; the sorted ``distinct_steps`` id for
  ``sod``; ``principal_id == Person.person_id``).

NO LLM, NO MS-S1, NO DB — pure + deterministic (the verdicts are deterministic by design; *governed
≠ generated*). The live MS-S1 runner (Step 4b) produces the SAME audit contract; this arm is what
the offline gate asserts and the demo falls back to. Binds to the SHIPPED shapes with **no reshape**
— ``resolved_tier_id`` is the approver **role** (``"CONTROLLER"``), never the CSV ``tier_id``.

All figures are DEMO-GRADE / PROVISIONAL (the C1 dataset).
"""

from __future__ import annotations

from typing import Any

from services.engine.actions import ControlRef, GovernedDecision
from services.engine.procedures.doa_tier import DoaTierVerdict, resolve_doa_tier
from services.engine.procedures.principal_sod import PrincipalSoDVerdict, check_principal_sod
from services.engine.procedures.spec import (
    DoaLadder,
    DoaTier,
    EmergencyWaiverPolicy,
    Person,
    Procedure,
    SoDConstraint,
    Step,
    StepKind,
)
from verticals.procurement.data_adapter.fastenal_csv import FastenalCsvAdapter

_CURRENCY = "THB"
_HERO_PO = "PO-2026-0412"
_CONTRAST_PO = "PO-2026-0411"
_REQUESTER_ID = "req-maint-planner"

# The hero procedure's SoD constraint (mirrors the shipped procurement procedure: the requester
# who intakes the request must not be the approver who clears the gate). ``constraint_id`` is the
# sorted '+'-joined distinct_steps ("approve+intake") — the exact SoD control id the engine emits.
_SOD = SoDConstraint(
    distinct_steps=frozenset({"intake", "approve"}),
    required_roles={"intake": "requester", "approve": "approver"},
)


def _hero_procedure() -> Procedure:
    """A minimal intake→approve procedure carrying the SoD constraint, so ``check_principal_sod``
    resolves the two constrained steps to distinct principals (the shipped run-check surface)."""
    return Procedure(
        procedure_id="fastenal_emergency_sourcing",
        title="Fastenal Emergency Sourcing (hero demo)",
        run_by="procurement_agent",
        steps=[
            Step(step_id="intake", name="Intake the maintenance request", kind=StepKind.QUERY),
            Step(
                step_id="approve", name="Tiered DOA approval", kind=StepKind.ACTION, handler="echo"
            ),
        ],
        separation_of_duties=[_SOD],
    )


async def _load_ladder(adapter: FastenalCsvAdapter) -> DoaLadder:
    """Build the DOA ladder from ``approval_tier.csv`` — the ฿ floors + approver roles, ascending
    (the ladder's half-open bands come from consecutive floors; top tier unbounded)."""
    rows = sorted(await adapter.fetch_objects("ApprovalTier"), key=lambda t: t["min_thb"])
    tiers = [DoaTier(min_amount=row["min_thb"], approver_role=row["approver_role"]) for row in rows]
    return DoaLadder(
        currency=_CURRENCY,
        tiers=tiers,
        # Off-AVL emergency = the waiver beat: relaxes three-bid, escalates authority, never skips a
        # gate. Authored for the demo (the CSV carries no waiver policy).
        emergency_waiver=EmergencyWaiverPolicy(relaxes=["three_bid"], escalate_to="CONTROLLER"),
    )


async def _load_principals(adapter: FastenalCsvAdapter) -> list[Person]:
    """Build the vertical principals from ``person.csv`` (the SoD / DOA-approver identities)."""
    return [
        Person(person_id=row["person_id"], name=row["name"], roles=frozenset(row["roles"]))
        for row in await adapter.fetch_objects("Person")
    ]


def _sod_projection(
    verdict: PrincipalSoDVerdict,
    *,
    requester_id: str,
    approver_id: str | None,
    by_id: dict[str, Person],
) -> dict[str, Any]:
    """A render-friendly projection of the SoD verdict (who requested vs who approved, and whether
    the distinct-principals constraint held) — the structured field the render binds, no reshape."""

    def _who(person_id: str | None) -> dict[str, Any] | None:
        if person_id is None:
            return None
        person = by_id.get(person_id)
        return {
            "person_id": person_id,
            "name": person.name if person else None,
            "roles": sorted(person.roles) if person else [],
        }

    return {
        "governed": verdict.governed,
        "constraint_id": _SOD.constraint_id,
        "requester": _who(requester_id),
        "approver": _who(approver_id),
        "violations": [
            {"kind": str(v.kind), "detail": v.detail, "steps": list(v.steps)}
            for v in verdict.violations
        ],
    }


async def _audit_for_po(
    po: dict[str, Any],
    *,
    ladder: DoaLadder,
    principals: list[Person],
    by_id: dict[str, Person],
) -> dict[str, Any]:
    """Capture the gate audit for one PO: the ``doa_tier`` verdict, the SoD verdict, and the typed
    ``governed_decision`` ties — exactly as the shipped engine emits them."""
    amount = po["total_thb"]
    verdict: DoaTierVerdict = resolve_doa_tier(
        ladder,
        amount=amount,
        currency=_CURRENCY,
        principals=principals,
        sod_required=True,
    )
    approver_id = verdict.resolved_approver_id

    step_principals: dict[str, str | None] = {"intake": _REQUESTER_ID, "approve": approver_id}
    sod_verdict = check_principal_sod(
        _hero_procedure(),
        principals=principals,
        principal_aliases=[],
        step_principals=step_principals,
    )

    governed_decision: list[dict[str, Any]] = []
    if approver_id is not None:
        # doa_tier route: control_ref.id == resolved_tier_id (the ROLE); principal = approver
        governed_decision.append(
            GovernedDecision(
                control_ref=ControlRef(kind="doa_tier", id=verdict.resolved_tier_id),
                principal_id=approver_id,
            ).model_dump()
        )
        if sod_verdict.governed:
            # sod route: control_ref.id == the sorted distinct_steps ("approve+intake")
            governed_decision.append(
                GovernedDecision(
                    control_ref=ControlRef(kind="sod", id=_SOD.constraint_id),
                    principal_id=approver_id,
                ).model_dump()
            )

    return {
        "po_id": po["po_id"],
        "part_id": po["part_id"],
        "supplier_id": po["supplier_id"],
        "asset_id": po["asset_id"],
        "order_type": po["order_type"],
        "is_off_avl_override": po["is_off_avl_override"],
        "amount": {"value": str(amount), "currency": _CURRENCY},
        # The CSV's human tier label (TIER-CTRL) — a DISPLAY handle only; the authoritative
        # governance value is doa_tier[].resolved_tier_id (the role), never this.
        "declared_tier_id": po["required_tier_id"],
        "doa_tier": [verdict.to_audit()],
        "governed_kind": "doa_tier",
        "governed_decision": governed_decision,
        "sod": _sod_projection(
            sod_verdict, requester_id=_REQUESTER_ID, approver_id=approver_id, by_id=by_id
        ),
    }


async def build_hero_governance_audit(adapter: FastenalCsvAdapter | None = None) -> dict[str, Any]:
    """Capture the hero + contrast gate audits from the real shipped engine (offline).

    Returns the audit contract the governance-moment render binds to: ``hero`` (PO-2026-0412,
    ฿288,000 off-AVL → CONTROLLER + SoD) and ``contrast`` (PO-2026-0411, ฿99,000 → MANAGER, no
    Controller escalation — proving the gate is data-driven, AC-7). ``source: offline-fixture``
    marks this as the deterministic capture (the live MS-S1 runner sets ``source: live-ms-s1``).
    """
    adapter = adapter or FastenalCsvAdapter()
    ladder = await _load_ladder(adapter)
    principals = await _load_principals(adapter)
    by_id = {p.person_id: p for p in principals}
    pos = {p["po_id"]: p for p in await adapter.fetch_objects("PurchaseOrder")}
    return {
        "provisional": True,
        "source": "offline-fixture",
        "hero": await _audit_for_po(
            pos[_HERO_PO], ladder=ladder, principals=principals, by_id=by_id
        ),
        "contrast": await _audit_for_po(
            pos[_CONTRAST_PO], ladder=ladder, principals=principals, by_id=by_id
        ),
    }
