"""Deterministic offline capture of fleet's View G governance moment (PLAN-0098 D-C).

Runs the **real shipped engine functions** over the ladder, principals and SoD constraint
loaded from the vertical's own ``procedures.yaml`` — never a re-typed copy. That is the
point rather than a stylistic preference: the same never-restate rule
``economic_impact.py:42-45`` already applies to the ฿30,000 threshold, and AC-2's parity
tripwire asserts the response's band floors equal the spec's, so a builder that hardcodes
a rung goes RED the moment the YAML moves.

* :func:`~services.engine.procedures.doa_tier.resolve_doa_tier` — ฿ → the half-open DOA
  band → the approver role → the resolved :class:`Person`. The hero's ฿48,000 clears the
  ฿30,001 rung → ``เจ้าของกิจการ``; the contrast's ฿15,000 lands mid-ladder →
  ``ผจก.เดินรถ``. Two different repairs resolving to two different authorities off one
  ladder is what shows the gate is data-driven rather than always-the-top.
* :func:`~services.engine.procedures.principal_sod.check_principal_sod` — the fail-closed
  run-check: ต้อม filed the claim (``intake``), so ต้อม must not be the authority who
  approves it. That constraint is the partner's own กฎเหล็ก, stated unprompted.
* :class:`~services.engine.actions.GovernedDecision` / :class:`ControlRef` — the typed
  audit-to-control ties on the shipped join keys.

Plus one beat procurement's audit does not have: the ``three_quote`` rule-gate verdict.
Its ``basis`` is READ off the event rather than recomputed — ``sourcing.py:79-82`` states
why in its own words ("stamped on the row so the month-end export can answer 'why did
this pass?' *without re-running the logic* … against a threshold that may since have
moved"), and the events carry no vendor counts to recompute from, so recomputing would
mean inventing the inputs. The stamp IS the real function's output, recorded when the
inputs existed.

NO LLM, NO MS-S1, NO DB — pure and deterministic. All figures are demo-grade.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from services.engine.actions import ControlRef, GovernedDecision
from services.engine.procedures.doa_tier import DoaTierVerdict, resolve_doa_tier
from services.engine.procedures.principal_sod import PrincipalSoDVerdict, check_principal_sod
from services.engine.procedures.spec import (
    ComplianceGate,
    DoaLadder,
    Person,
    Procedure,
    SoDConstraint,
    VerticalProcedures,
    load_procedures,
)
from verticals.fleet_maintenance.data_adapter import FleetMaintenanceSyntheticAdapter

_VERTICAL = "fleet_maintenance"
_CURRENCY = "THB"
_PROCEDURE_ID = "governed_repair_approval"
_APPROVE_STEP = "approve"
_GATE_STEP = "quote_gate"
_INTAKE_STEP = "intake"

#: The two repairs the moment contrasts. Both are real rows in the synthetic feed:
#: ฿48,000 clears the ฿30,000 comparison threshold and earned its three_quote pass by
#: actually collecting three quotes; ฿15,000 sits under it and passes because the rule
#: never applied. Same signal, two different reasons — which is the beat.
_HERO_EVENT_ID = "event-reading-02"
_CONTRAST_EVENT_ID = "event-reading-05"


def _procedure(spec: VerticalProcedures) -> Procedure:
    """The governed repair procedure, or a loud failure if the spec stopped shipping it."""
    for procedure in spec.procedures:
        if procedure.procedure_id == _PROCEDURE_ID:
            return procedure
    raise LookupError(
        f"{_PROCEDURE_ID!r} is not in {_VERTICAL}'s procedures.yaml "
        f"(found {[p.procedure_id for p in spec.procedures]}). View G captures THAT "
        "procedure's gate; falling back to another one would render a different demo."
    )


def _governance_content(procedure: Procedure, step_id: str, expected: type[Any]) -> Any:
    """One step's ``governance_content``, type-checked against what the capture needs."""
    for step in procedure.steps:
        if step.step_id != step_id:
            continue
        content = step.governance_content
        if not isinstance(content, expected):
            raise TypeError(
                f"step {step_id!r} carries {type(content).__name__} governance_content, "
                f"expected {expected.__name__}. The capture reads the authored spec "
                "rather than restating it, so a shape change must surface here."
            )
        return content
    raise LookupError(f"{_PROCEDURE_ID!r} has no step {step_id!r}")


def _sod_constraint(procedure: Procedure) -> SoDConstraint:
    """The procedure's SoD constraint — the partner's own requester≠approver rule."""
    if not procedure.separation_of_duties:
        raise LookupError(
            f"{_PROCEDURE_ID!r} declares no separation_of_duties. A doa_tier gate REQUIRES "
            "one (ADR-0025 D2/D5); capturing the moment without it would show a governance "
            "beat the spec does not actually have."
        )
    return procedure.separation_of_duties[0]


def _requester_id(spec: VerticalProcedures) -> str:
    """The principal who files the claim — read from the spec's declared roles."""
    for person in spec.principals:
        if "requester" in person.roles:
            return person.person_id
    raise LookupError(
        f"no principal in {_VERTICAL}'s spec carries the 'requester' role, so the SoD "
        "check has no intake principal to resolve. Read from the spec deliberately: "
        "hardcoding an id here is how a renamed principal silently stops being checked."
    )


def _sod_projection(
    verdict: PrincipalSoDVerdict,
    constraint: SoDConstraint,
    *,
    requester_id: str,
    approver_id: str | None,
    by_id: dict[str, Person],
) -> dict[str, Any]:
    """Render-friendly projection of the SoD verdict — who asked, who approved, held?"""

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
        "constraint_id": constraint.constraint_id,
        "requester": _who(requester_id),
        "approver": _who(approver_id),
        "violations": [
            {"kind": str(v.kind), "detail": v.detail, "steps": list(v.steps)}
            for v in verdict.violations
        ],
    }


def _three_quote_block(event: dict[str, Any], gate: ComplianceGate) -> dict[str, Any]:
    """The fleet-only rule-gate card: the signal, the stamped basis, and the authored rule.

    ``basis`` is read, not recomputed — see the module docstring. ``spec`` comes from the
    authored ``ComplianceGate`` so the card shows the partner's rule in the partner's own
    words rather than a paraphrase that can drift from the YAML.
    """
    compliance = event.get("compliance") or {}
    rule = next((r for r in gate.rules if r.criterion == "three_quote"), None)
    return {
        "criterion": "three_quote",
        "signal": bool(compliance.get("three_quote")),
        "basis": str(event.get("three_quote_basis")) if event.get("three_quote_basis") else None,
        "spec": rule.spec if rule else None,
        "blocks_po": rule.blocks_po if rule else None,
    }


def _audit_for_event(
    event: dict[str, Any],
    *,
    ladder: DoaLadder,
    gate: ComplianceGate,
    procedure: Procedure,
    constraint: SoDConstraint,
    principals: list[Person],
    principal_aliases: list[Any],
    by_id: dict[str, Person],
    requester_id: str,
) -> dict[str, Any]:
    """Capture the gate audit for one repair, exactly as the shipped engine emits it."""
    amount = Decimal(str(event["measured_value"]))
    verdict: DoaTierVerdict = resolve_doa_tier(
        ladder,
        amount=amount,
        currency=_CURRENCY,
        principals=principals,
        sod_required=True,
    )
    approver_id = verdict.resolved_approver_id

    sod_verdict = check_principal_sod(
        procedure,
        principals=principals,
        principal_aliases=principal_aliases,
        step_principals={_INTAKE_STEP: requester_id, _APPROVE_STEP: approver_id},
    )

    governed_decision: list[dict[str, Any]] = []
    if approver_id is not None:
        governed_decision.append(
            GovernedDecision(
                control_ref=ControlRef(kind="doa_tier", id=verdict.resolved_tier_id),
                principal_id=approver_id,
            ).model_dump()
        )
        if sod_verdict.governed:
            governed_decision.append(
                GovernedDecision(
                    control_ref=ControlRef(kind="sod", id=constraint.constraint_id),
                    principal_id=approver_id,
                ).model_dump()
            )

    return {
        "event_id": event["event_id"],
        "truck_id": event["truck_id"],
        "case_id": event["case_id"],
        "site_id": event.get("site_id"),
        "severity": event.get("severity"),
        "amount": {"value": str(amount), "currency": _CURRENCY},
        "doa_tier": [verdict.to_audit()],
        "governed_kind": "doa_tier",
        "governed_decision": governed_decision,
        "sod": _sod_projection(
            sod_verdict,
            constraint,
            requester_id=requester_id,
            approver_id=approver_id,
            by_id=by_id,
        ),
        "three_quote": _three_quote_block(event, gate),
    }


async def _events_by_id(
    adapter: FleetMaintenanceSyntheticAdapter,
) -> dict[str, dict[str, Any]]:
    return {e["event_id"]: dict(e) for e in await adapter.fetch_objects("OperationalEvent")}


async def build_fleet_governance_audit(
    adapter: FleetMaintenanceSyntheticAdapter | None = None,
) -> dict[str, Any]:
    """Capture fleet's hero + contrast gate audits from the real engine, offline.

    ``source: offline-fixture`` marks this the deterministic arm. Fleet ships no live
    arm in v1 (PLAN-0098 out of scope); the router returns a typed 400 for ``live=true``
    rather than serving this capture under a label it has not earned.
    """
    adapter = adapter or FleetMaintenanceSyntheticAdapter()
    spec = load_procedures(_VERTICAL)
    procedure = _procedure(spec)
    ladder: DoaLadder = _governance_content(procedure, _APPROVE_STEP, DoaLadder)
    gate: ComplianceGate = _governance_content(procedure, _GATE_STEP, ComplianceGate)
    constraint = _sod_constraint(procedure)
    principals = list(spec.principals)
    by_id = {p.person_id: p for p in principals}
    requester_id = _requester_id(spec)

    events = await _events_by_id(adapter)
    missing = [e for e in (_HERO_EVENT_ID, _CONTRAST_EVENT_ID) if e not in events]
    if missing:
        raise LookupError(
            f"pinned View G events not in the fleet synthetic dataset: {missing}. The "
            "moment contrasts two SPECIFIC repairs (฿48,000 over the threshold vs ฿15,000 "
            "under it); substituting whatever is available would change what the demo "
            "demonstrates."
        )

    def capture(event_id: str) -> dict[str, Any]:
        return _audit_for_event(
            events[event_id],
            ladder=ladder,
            gate=gate,
            procedure=procedure,
            constraint=constraint,
            principals=principals,
            principal_aliases=list(spec.principal_aliases),
            by_id=by_id,
            requester_id=requester_id,
        )

    return {
        "provisional": True,
        "source": "offline-fixture",
        "hero": capture(_HERO_EVENT_ID),
        "contrast": capture(_CONTRAST_EVENT_ID),
    }
