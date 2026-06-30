"""The SD-1=(a) per-kind AT-2 governance dispatch (ADR-0026 D5; PLAN-0044 A1b, SD-1).

The AT-2 gate kinds (``doa_tier`` / ``scored_rule`` / ``rule_gate``) are NOT :class:`StepKind`s
— they are ``governance_content.kind`` discriminator values carried on the shipped ``action`` /
``evaluate`` steps. So a per-kind enforcement executor cannot register as a new ``StepKind`` (no
5th kind, PLAN-0044 Out-of-Scope). SD-1=(a): a **dispatching wrapper executor per StepKind** that
inspects ``step.governance_content`` and delegates to the right deterministic AT-2 enforcement,
falling through to the BASE executor for a non-AT-2 step — so the orchestrator's ``StepKind``-keyed
``executors`` map is untouched (extend not replace, LOCKED #5), mirroring the shipped test-harness
``_Evaluate`` dispatch. The enforcement itself stays a small pure function the wrapper calls
(:func:`~services.engine.procedures.doa_tier.resolve_doa_tier`).

This module ships the **ACTION** wrapper with the ``doa_tier`` branch (Step 3); the ``scored_rule``
branch (Step 5, also an ACTION-step content) and the EVALUATE wrapper's ``rule_gate`` branch
(Step 4) extend it. Render / route / block only — the wrapper resolves + annotates; the shipped
ADR-0007 approve->execute gate stays the only external write path (LOCKED #3).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

from services.engine.actions import ControlRef, GovernedDecision
from services.engine.procedures.doa_tier import DoaTierError, resolve_doa_tier
from services.engine.procedures.orchestrator import RunContext, StepExecutor, StepOutcome
from services.engine.procedures.spec import DoaLadder, Person, Step


def _spend(entity: Any) -> tuple[Decimal, str]:
    """Read the ``(Decimal, currency)`` spend off a ``doa_tier`` step's input entity (OQ-4).

    Fails CLOSED (:class:`DoaTierError`) if the entity carries no ``amount`` / ``currency`` — a
    DOA tier cannot be routed without a spend. ``Decimal(str(...))`` coerces a float/str amount
    to an EXACT ``Decimal`` (never binary ``float`` on an authority threshold)."""
    if not isinstance(entity, Mapping) or "amount" not in entity or "currency" not in entity:
        raise DoaTierError(
            "doa_tier: input entity carries no 'amount'/'currency' spend — cannot resolve a DOA "
            "tier (fail closed; render/route/block only)"
        )
    try:
        value = Decimal(str(entity["amount"]))
    except InvalidOperation as exc:
        raise DoaTierError(
            f"doa_tier: input entity amount '{entity['amount']}' is not a valid Decimal spend "
            "(fail closed)"
        ) from exc
    return value, str(entity["currency"])


@dataclass(frozen=True)
class GovernanceActionExecutor:
    """SD-1=(a) dispatching wrapper for the ``action`` StepKind (PLAN-0044 A1b Step 3).

    Branches on ``step.governance_content`` and delegates to the right deterministic AT-2
    enforcement; a non-AT-2 action (no / unrecognised governance content) delegates straight to
    the wrapped ``base`` :class:`~services.engine.procedures.action_step.ActionStepExecutor`.
    Constructed with the vertical ``principals`` (to resolve a tier's ``approver_role`` -> a
    :class:`Person`) and the procedure's SoD-constrained ``sod_steps`` (for the verdict's
    ``sod_required``) — the caller has the procedure, so the orchestrator contract is untouched.
    """

    base: StepExecutor
    principals: list[Person] = field(default_factory=list)
    sod_steps: frozenset[str] = field(default_factory=frozenset)

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        gc = step.governance_content
        if isinstance(gc, DoaLadder):
            return await self._doa_tier(step, gc, input_set, ctx)
        return await self.base.execute(step, input_set, ctx)

    async def _doa_tier(
        self, step: Step, ladder: DoaLadder, input_set: list[Any], ctx: RunContext
    ) -> StepOutcome:
        """Resolve the DOA tier per input entity (deterministic, fail-closed currency), then
        delegate to the base executor for the gated proposal — the orchestrator suspends the
        ``gated`` action at ``waiting_human``. The structured verdicts ride the step audit (the
        hero render reads them); the LLM only drafts the justification (base, advisory) — it
        never decides the tier (governed != generated). Render / route / block only."""
        sod_required = step.step_id in self.sod_steps
        verdicts = [
            resolve_doa_tier(
                ladder,
                amount=amount,
                currency=currency,
                principals=self.principals,
                sod_required=sod_required,
            )
            for amount, currency in (_spend(entity) for entity in input_set)
        ]
        base_outcome = await self.base.execute(step, input_set, ctx)
        trace = list(base_outcome.reasoning_trace) + [
            {
                "kind": "doa_tier_resolved",
                "resolved_tier_id": v.resolved_tier_id,
                "required_role": v.required_role,
                "resolved_approver_id": v.resolved_approver_id,
                "summary": (
                    f"spend {v.amount.value} {v.amount.currency} -> tier '{v.resolved_tier_id}' "
                    f"(approver_role '{v.required_role}'"
                    + (
                        f", resolved to '{v.resolved_approver_id}')"
                        if v.resolved_approver_id is not None
                        else ", no declared approver — SoD run-check fails closed at the gate)"
                    )
                ),
            }
            for v in verdicts
        ]
        # The OQ-5 audit-to-control side-effect (A1b Step 6, AC-8): tie each resolved tier route
        # to its control + the resolved approver. Engine-emitted (cannot be authored auto). A
        # tier whose role resolves to no Person emits no tie (no principal to name — that case
        # fails closed at the SoD gate, Step 1).
        governed_decisions = [
            GovernedDecision(
                control_ref=ControlRef(kind="doa_tier", id=v.resolved_tier_id),
                principal_id=v.resolved_approver_id,
            ).model_dump(mode="json")
            for v in verdicts
            if v.resolved_approver_id is not None
        ]
        audit = {
            **(base_outcome.audit or {}),
            "governed_kind": "doa_tier",
            "doa_tier": [v.to_audit() for v in verdicts],
            "governed_decision": governed_decisions,
        }
        return StepOutcome(output=base_outcome.output, reasoning_trace=trace, audit=audit)
