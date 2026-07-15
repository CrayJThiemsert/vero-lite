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

This module ships the **ACTION** wrapper (:class:`GovernanceActionExecutor`) with the ``doa_tier``
branch (Step 3) and the ``scored_rule`` branch (Step 5, also ACTION-step content), and the
**EVALUATE** wrapper (:class:`GovernanceEvaluateExecutor`) with the ``rule_gate`` branch (Step 4 —
the compliance gate is EVALUATE-step content). Render / route / select / block only — the wrapper
resolves + annotates, for ``scored_rule`` it EMITS the selected quote's spend onto the threaded
entity so the downstream ``doa_tier`` resolves (PLAN-0044 A1b Step 5, the section-3 baht-threading
fix), and for ``rule_gate`` it tags each candidate ``compliant`` so the downstream ``approve``
fan-out (``where: {compliant: true}``) drops a non-compliant candidate (Step 4); the shipped
ADR-0007 approve->execute gate stays the only external write path (LOCKED #3).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, cast

from services.engine.procedures.doa_tier import DoaTierError, resolve_doa_tier
from services.engine.procedures.orchestrator import RunContext, StepExecutor, StepOutcome
from services.engine.procedures.rule_gate import evaluate_compliance
from services.engine.procedures.scored_rule import ScoredRuleError, select_scored_supplier
from services.engine.procedures.severity_tier import SeverityTierError, resolve_severity_tier
from services.engine.procedures.spec import (
    ComplianceGate,
    DoaLadder,
    ExcursionSeverity,
    Person,
    ScoredRule,
    SeverityLadder,
    Step,
)


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


EXCURSION_SEVERITY_FIELD = "excursion_severity"
"""The entity field a ``severity_tier`` gate reads its authority quantity from (PLAN-0074).

DELIBERATELY NOT the bare ``severity`` (the Step-4 run-path finding, the second coordination point
static analysis missed): the shipped ontologies ALREADY carry an ``OperationalEvent.severity``
(``info`` | ``warning`` | ``critical`` — an alert-triage vocabulary), whose value space OVERLAPS
:class:`ExcursionSeverity` at ``critical``. A gate reading a bare ``severity`` would therefore
resolve an event-triage string as a stability-budget-derived excursion severity and silently route
the TOP approval tier — failing DANGEROUS (a plausible wrong authority), not closed. A distinct
field name makes that collision unrepresentable: an un-stamped entity carries no
``excursion_severity`` at all, so the gate fails closed (below), which is the invariant."""


def _severity(entity: Any) -> ExcursionSeverity:
    """Read the :class:`ExcursionSeverity` off a ``severity_tier`` step's input entity
    (PLAN-0074 Step 3 — the non-money analog of :func:`_spend`).

    Fails CLOSED (:class:`SeverityTierError`) if the entity carries no
    :data:`EXCURSION_SEVERITY_FIELD` or an unrecognised value — a severity tier cannot be routed
    without a resolvable severity. The severity is the authority quantity the upstream ``assess``
    step stamps onto the entity (the non-money analog of the ``scored_rule`` amount-stamp)."""
    if not isinstance(entity, Mapping) or EXCURSION_SEVERITY_FIELD not in entity:
        raise SeverityTierError(
            f"severity_tier: input entity carries no '{EXCURSION_SEVERITY_FIELD}' — cannot resolve "
            "a severity tier (fail closed; render/route/block only). NOTE: the ontology's own "
            "OperationalEvent.severity is a DIFFERENT vocabulary and is never read here"
        )
    try:
        return ExcursionSeverity(str(entity[EXCURSION_SEVERITY_FIELD]))
    except ValueError as exc:
        raise SeverityTierError(
            f"severity_tier: input entity {EXCURSION_SEVERITY_FIELD} "
            f"'{entity[EXCURSION_SEVERITY_FIELD]}' is not a recognised ExcursionSeverity "
            "(fail closed)"
        ) from exc


def _candidate_quotes(entity: Any) -> list[Any]:
    """The candidate quotes the ``scored_rule`` ``source`` step scores -- carried on the input
    entity (intake enriches the requisition with them, data-access = (a), Cray-confirmed s91).
    Fails CLOSED if absent / not a list (a supplier cannot be selected without candidates)."""
    if not isinstance(entity, Mapping) or "candidate_quotes" not in entity:
        raise ScoredRuleError(
            "scored_rule: input entity carries no 'candidate_quotes' -- the source step needs the "
            "part's candidate quotes to score (intake enriches the requisition with them, "
            "PLAN-0044 A1b Step 5 data-access = (a)); fail closed"
        )
    quotes = entity["candidate_quotes"]
    if not isinstance(quotes, list):
        raise ScoredRuleError(
            f"scored_rule: 'candidate_quotes' must be a list, got {type(quotes).__name__} "
            "-- fail closed"
        )
    return quotes


def _quantity(entity: Any) -> Decimal:
    """The requested quantity that scales the winning unit price to the PO spend (PLAN-0044 A1b
    Step 5). Defaults to 1 (a single-unit order) when the requisition carries none. ``Decimal``,
    never ``float`` -- the spend routes an authority tier."""
    raw = entity.get("qty", entity.get("quantity", 1)) if isinstance(entity, Mapping) else 1
    try:
        return Decimal(str(raw))
    except InvalidOperation as exc:
        raise ScoredRuleError(
            f"scored_rule: entity qty '{raw}' is not a valid Decimal quantity -- fail closed"
        ) from exc


def _event_criticality(entity: Any) -> Decimal:
    """The event criticality (0..1) that amplifies the ``criticality`` criterion's weight (see
    ``scored_rule`` module docstring). Read from an explicit ``criticality`` field; else the
    ontology-projected ``measured_value`` when the reading IS a criticality (``unit ==
    'criticality'``, the operational-event convention); else a neutral 0.5 (no amplification bias).
    Clamped to [0, 1]."""
    if isinstance(entity, Mapping) and "criticality" in entity:
        raw: Any = entity["criticality"]
    elif (
        isinstance(entity, Mapping)
        and str(entity.get("unit", "")).lower() == "criticality"
        and "measured_value" in entity
    ):
        raw = entity["measured_value"]
    else:
        raw = "0.5"
    try:
        value = Decimal(str(raw))
    except InvalidOperation as exc:
        raise ScoredRuleError(
            f"scored_rule: entity criticality '{raw}' is not a valid Decimal -- fail closed"
        ) from exc
    return min(Decimal(1), max(Decimal(0), value))


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
        if isinstance(gc, ScoredRule):
            return await self._scored_rule(step, gc, input_set, ctx)
        if isinstance(gc, SeverityLadder):
            return await self._severity_tier(step, gc, input_set, ctx)
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
                        else ", no native-tier approver — tier-authority enforces at the gate)"
                    )
                ),
            }
            for v in verdicts
        ]
        # PLAN-0075 SD-6(a): the principal-naming ``governed_decision`` tie is NO LONGER emitted at
        # run time — a suspended run must carry NO authority tie naming a principal who has not yet
        # acted (the run-time ``doa_tier`` verdict list below is the honest ROUTING record). The
        # actor-named tie is emitted at GATE time, after the tier-authority check passes
        # (``_record_governed_decision`` -> ``_authority_governed_decisions`` in action_step).
        audit = {
            **(base_outcome.audit or {}),
            "governed_kind": "doa_tier",
            "doa_tier": [v.to_audit() for v in verdicts],
        }
        return StepOutcome(output=base_outcome.output, reasoning_trace=trace, audit=audit)

    async def _severity_tier(
        self, step: Step, ladder: SeverityLadder, input_set: list[Any], ctx: RunContext
    ) -> StepOutcome:
        """Resolve the severity tier per input entity (deterministic, fail-closed on an absent /
        unrecognised severity), then delegate to the base executor for the gated proposal — the
        orchestrator suspends the ``gated`` action at ``waiting_human``. The structured verdicts
        ride the step audit (the render reads them); the LLM only drafts (base, advisory) — it
        never decides the tier (governed != generated). Render / route / block only — the
        non-money analog of :meth:`_doa_tier` (PLAN-0074 Step 3)."""
        sod_required = step.step_id in self.sod_steps
        verdicts = [
            resolve_severity_tier(
                ladder,
                severity=severity,
                principals=self.principals,
                sod_required=sod_required,
            )
            for severity in (_severity(entity) for entity in input_set)
        ]
        base_outcome = await self.base.execute(step, input_set, ctx)
        trace = list(base_outcome.reasoning_trace) + [
            {
                "kind": "severity_tier_resolved",
                "resolved_tier_id": v.resolved_tier_id,
                "required_role": v.required_role,
                "resolved_approver_id": v.resolved_approver_id,
                "summary": (
                    f"severity '{v.severity.value}' -> tier '{v.resolved_tier_id}' "
                    f"(approver_role '{v.required_role}'"
                    + (
                        f", resolved to '{v.resolved_approver_id}')"
                        if v.resolved_approver_id is not None
                        else ", no native-tier approver — tier-authority enforces at the gate)"
                    )
                ),
            }
            for v in verdicts
        ]
        # PLAN-0075 SD-6(a): no run-time principal-naming tie (see _doa_tier) — the actor-named
        # ``governed_decision`` is emitted at GATE time after the tier-authority check passes.
        audit = {
            **(base_outcome.audit or {}),
            "governed_kind": "severity_tier",
            "severity_tier": [v.to_audit() for v in verdicts],
        }
        return StepOutcome(output=base_outcome.output, reasoning_trace=trace, audit=audit)

    async def _scored_rule(
        self, step: Step, rule: ScoredRule, input_set: list[Any], ctx: RunContext
    ) -> StepOutcome:
        """Deterministically select the supplier per entity's candidate quotes and EMIT the
        selected spend (``unit_price x qty``) + currency onto the threaded entity, so the downstream
        approve doa_tier resolves (PLAN-0044 A1b Step 5 -- the section-3 baht-threading fix).

        Unlike :meth:`_doa_tier` (which KEEPS the base envelopes), this REPLACES the output with the
        enriched selected entities -- the whole point of the finding: the shipped ``action``
        executor returns action envelopes, DROPPING the input entity's spend, so the approve
        doa_tier would fail closed with no amount. The base executor still runs (its advisory LLM
        judgment + the auto sourcing action + its audit); the LLM NEVER selects (governed !=
        generated, ADR-0019 IN-3). Render / route / select only -- no PO is issued (LOCKED #3)."""
        verdicts = [
            select_scored_supplier(
                rule,
                _candidate_quotes(entity),
                qty=_quantity(entity),
                event_criticality=_event_criticality(entity),
            )
            for entity in input_set
        ]
        base_outcome = await self.base.execute(step, input_set, ctx)
        # PLAN-0073 (SD-1a): the base ActionStepExecutor builds the advisory Box-4 economic_impact
        # facet into each RecommendedAction's reasoning_trace (ADR-0030 / PLAN-0071). This method
        # REPLACES base_outcome.output below (dropping those action envelopes to thread the selected
        # spend forward), which would discard the facet — so lift it onto the STEP trace here, where
        # it persists on the governed run. Advisory + never-raise: an empty list when no producer is
        # registered or the event does not ground a ฿ figure (it never changes the action).
        economic_steps: list[dict[str, Any]] = [
            cast("dict[str, Any]", trace_step)
            for entry in base_outcome.output
            if isinstance(entry, Mapping)
            for trace_step in (entry.get("action") or {}).get("reasoning_trace", [])
            if isinstance(trace_step, Mapping) and trace_step.get("kind") == "economic_impact"
        ]
        enriched: list[Any] = [
            {
                **(entity if isinstance(entity, Mapping) else {"value": entity}),
                "amount": str(v.amount),
                "currency": v.currency,
                "selected_quote_id": v.selected_quote_id,
                "selected_supplier_id": v.selected_supplier_id,
                "source_path": v.source_path,
                "override_required": v.override_required,
            }
            for entity, v in zip(input_set, verdicts, strict=True)
        ]
        trace = (
            list(base_outcome.reasoning_trace)
            + economic_steps
            + [
                {
                    "kind": "scored_rule_selected",
                    "selected_supplier_id": v.selected_supplier_id,
                    "selected_quote_id": v.selected_quote_id,
                    "amount": str(v.amount),
                    "currency": v.currency,
                    "summary": (
                        f"scored {len(v.ranked)} quotes -> '{v.selected_supplier_id}' "
                        f"(quote '{v.selected_quote_id}', {v.amount} {v.currency}"
                        + (
                            ", off-contract exception -- logged justification required)"
                            if v.override_required
                            else ", on-contract default)"
                        )
                    ),
                }
                for v in verdicts
            ]
        )
        audit = {
            **(base_outcome.audit or {}),
            "governed_kind": "scored_rule",
            "scored_rule": [v.to_audit() for v in verdicts],
        }
        return StepOutcome(output=enriched, reasoning_trace=trace, audit=audit)


@dataclass(frozen=True)
class GovernanceEvaluateExecutor:
    """SD-1=(a) dispatching wrapper for the ``evaluate`` StepKind (PLAN-0044 A1b Step 4).

    Branches on ``step.governance_content`` and delegates the ``rule_gate`` (compliance) content to
    the deterministic :func:`~services.engine.procedures.rule_gate.evaluate_compliance`; a non-AT-2
    evaluate step (the banded ``judge`` — no / non-``rule_gate`` governance content) delegates
    straight to the wrapped ``base`` (the shipped deterministic
    :class:`~services.engine.procedures.evaluate_step.EvaluateStepExecutor`, which reads the
    authored band). The orchestrator's ``StepKind``-keyed contract is untouched (extend not replace,
    LOCKED #5), mirroring :class:`GovernanceActionExecutor`.

    The ``rule_gate`` branch does NOT call the base: the base ``EvaluateStepExecutor`` REQUIRES an
    authored numeric ``threshold`` and a band-less compliance step would fail it — compliance is a
    RULE gate, not a numeric band. The gate is the pure :func:`evaluate_compliance` (no LLM — the
    LLM never evaluates the rule, governed ≠ generated, ADR-0019 IN-3). Block / render only.
    """

    base: StepExecutor

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        gc = step.governance_content
        if isinstance(gc, ComplianceGate):
            return await self._rule_gate(step, gc, input_set, ctx)
        return await self.base.execute(step, input_set, ctx)

    async def _rule_gate(
        self, step: Step, gate: ComplianceGate, input_set: list[Any], ctx: RunContext
    ) -> StepOutcome:
        """Evaluate the compliance gate per candidate and TAG each ``compliant`` (blocking the PO on
        any failed criterion — the non-compliant candidate is dropped by the downstream ``approve``
        ``where: {compliant: true}`` fan-out). Deterministic + fail-closed (see
        :func:`evaluate_compliance`); no base call (compliance has no numeric band), no LLM. The
        per-criterion results ride the step audit (the hero render reads them); no PO is issued
        (render / block only, LOCKED #3)."""
        verdicts = [evaluate_compliance(gate, candidate) for candidate in input_set]
        output: list[Any] = [
            {
                **(candidate if isinstance(candidate, Mapping) else {"value": candidate}),
                "compliant": v.compliant,
                "failed_criteria": list(v.failed_criteria),
            }
            for candidate, v in zip(input_set, verdicts, strict=True)
        ]
        blocked = sum(1 for v in verdicts if not v.compliant)
        trace = [
            {
                "kind": "rule_gate_evaluated",
                "summary": (
                    f"evaluated {len(gate.rules)} compliance rule(s) over {len(verdicts)} "
                    f"candidate(s): {blocked} blocked (any failed criterion blocks the PO — "
                    "non-waivable)"
                ),
            }
        ]
        audit = {
            "actor": ctx.agent.agent_id,
            "actor_kind": "engine",
            "deterministic": True,
            "governed_kind": "rule_gate",
            "rule_gate": [v.to_audit() for v in verdicts],
        }
        return StepOutcome(output=output, reasoning_trace=trace, audit=audit)
