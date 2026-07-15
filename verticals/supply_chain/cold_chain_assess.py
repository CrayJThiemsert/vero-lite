"""The cold-chain excursion SEVERITY derivation + action-stamp (PLAN-0074 Step 4, SD-2).

The ``severity_tier`` gate (the 4th AT-2 kind, PLAN-0074 Steps 1-3) authorises on a NON-MONEY
quantity: the :class:`~services.engine.procedures.spec.ExcursionSeverity` of a cold-chain breach.
Its run-side resolver reads that severity off the input entity and fails CLOSED without it
(``governance_step._severity``) — so SOMETHING must put it there. This module is that something:
the **action-stamp** (PLAN-0074 SD-2), scoped to the ``supply_chain`` vertical.

**Why an action-stamp and not a transform step.** The severity is DERIVED from intake scalars
(the excursion's magnitude x duration vs the cargo's stability budget), and the engine has no
transform/derived-field grammar — that seam is ADR-0031 D3 **row-1**, explicitly deferred (a
grammar ships in its OWN plan, never inlined here; PLAN-0074 Out of Scope). SD-2's ruling: for
v1, stamp the derived quantity from the ``assess`` action, mirroring the shipped ``scored_rule``
branch's own amount-stamp (``governance_step._scored_rule`` emits the selected quote's spend onto
the threaded entity so the downstream ``doa_tier`` resolves). This is the non-money analog.

**Recorded finding (PLAN-0074 -> the follow-on transform PLAN).** Building it CONFIRMS ADR-0031
D3 row-1 case-2 is armed: a real signature needed derived-field intake, and the derivation lives
in vertical CODE (the ladder below) rather than in the declaration. The ladder is the exact datum
a transform grammar would declare as data. It is vertical-scoped + provisional until that PLAN.

Pure + deterministic: no LLM, no DB, no network (the offline tests are the gate, CLAUDE.md §8).
Money never enters: the authority quantity is the severity ordinal. The LLM only drafts the
advisory prose in the base executor — it NEVER derives the severity (governed != generated).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

from services.engine.procedures.governance_step import EXCURSION_SEVERITY_FIELD
from services.engine.procedures.orchestrator import (
    ProcedureError,
    RunContext,
    StepExecutor,
    StepOutcome,
)
from services.engine.procedures.spec import ExcursionSeverity, Step

MAGNITUDE_FIELD = "excursion_magnitude_c"
"""Degrees Celsius the reading breached the cargo's ``temp_ceiling`` by (the excursion's height)."""

DURATION_FIELD = "excursion_duration_h"
"""Hours the breach persisted (the excursion's width)."""

BUDGET_FIELD = "stability_budget_ch"
"""The cargo's remaining stability budget in degree-hours (C*h) — the MKT-style dose the batch can
absorb before its shelf life is compromised. Per-cargo (a vaccine's budget is not a reagent's)."""

SEVERITY_FIELD = EXCURSION_SEVERITY_FIELD
"""The stamped authority quantity the ``severity_tier`` gate resolves (``_severity``).

NOT the bare ``severity``: the cold-chain ``OperationalEvent`` rows this intake threads ALREADY
carry one (``info`` | ``warning`` | ``critical`` — the alert-triage vocabulary), which overlaps
:class:`ExcursionSeverity` at ``critical``. Stamping into a distinct field keeps the two
vocabularies from ever being confused for one another (PLAN-0074 Step-4 run-path finding — see
``governance_step.EXCURSION_SEVERITY_FIELD``)."""

# The vertical-authored dose->severity ladder (PROVISIONAL, instance-scoped). Each tuple is an
# INCLUSIVE CEILING on the dose ratio: the excursion's DOSE (magnitude x duration, in C*h) as a
# FRACTION of the cargo's stability budget, matched by `ratio <= ceiling` (ascending). A breach
# consuming <=1/4 of the budget is negligible; <=1/2 minor; <=the whole budget (ratio <= 1.0)
# major; and ABOVE the budget (ratio > 1.0, the unbounded top band) critical — the batch has spent
# more than its stability budget and is presumed compromised. Total-cover: every non-negative ratio
# maps to exactly one severity (the ordinal analog of the SeverityLadder's own invariant). THIS IS
# THE DATUM A TRANSFORM GRAMMAR WOULD DECLARE (ADR-0031 D3 row-1) — it lives in code today, and
# that is the finding, not an oversight.
_DOSE_LADDER: tuple[tuple[Decimal, ExcursionSeverity], ...] = (
    (Decimal("0.25"), ExcursionSeverity.NEGLIGIBLE),
    (Decimal("0.50"), ExcursionSeverity.MINOR),
    (Decimal("1.00"), ExcursionSeverity.MAJOR),
)
_TOP_SEVERITY = ExcursionSeverity.CRITICAL
"""The unbounded top band: a dose ABOVE the last ladder floor (the budget is spent) is critical."""


def derivation_hash() -> str:
    """A canonical sha256 over the severity-DERIVATION constants — :data:`_DOSE_LADDER` AND
    :data:`_TOP_SEVERITY` (PLAN-0075 AC-13, the ratified SD-5 provenance fold-in).

    Threaded into the ``supply_chain`` run's governance snapshot (the engine pulls it by vertical
    through the registry hook — ``registry.derivation_hash`` — never importing this module), so a
    mid-flight (run-start ↔ resolve) derivation edit fails CLOSED at the governance pin and the run
    record answers "which derivation governed THIS run". **Serialises the constants THEMSELVES**,
    never a hand-maintained ``derivation_version`` string a deploy can forget to bump.

    Both constants are hashed on purpose: a ladder-tuple-only hash would leave the unbounded
    ``_TOP_SEVERITY`` critical band un-covered — an edit that re-pointed the top band would slip a
    tuple-only pin (the drafter finding, AC-13). Deterministic + stable across processes (ordered
    tuple, ``Decimal`` -> exact ``str``, enum -> ``.value``; ``sort_keys`` on the wrapper dict; no
    set, no float, no clock — the same discipline the ``governance_pin`` canonicalisation states).

    PROVENANCE-ONLY: this buys mid-flight tamper-evidence + audit provenance; it does NOT close the
    new-run re-routing threat (a fresh run on already-changed code pins the changed derivation
    without complaint) — F-PIN stays open (SD-5 tracked follow-on)."""
    payload = {
        "dose_ladder": [[str(ceiling), severity.value] for ceiling, severity in _DOSE_LADDER],
        "top_severity": _TOP_SEVERITY.value,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ColdChainAssessError(ProcedureError):
    """The severity derivation failed CLOSED (PLAN-0074 Step 4).

    Raised when the entity carries no usable excursion scalars (absent / non-numeric magnitude,
    duration, or stability budget; a non-positive budget). Failing closed blocks the assess step
    BEFORE the downstream ``severity_tier`` gate — a disposition is never routed to an approver on
    a severity the engine had to guess. (The gate's own reader fails closed too, ``_severity`` —
    two independent closed doors, mirroring the doa_tier ``_spend`` contract.)"""


def _positive_decimal(entity: Mapping[str, Any], key: str) -> Decimal:
    """Read an EXACT, strictly-positive ``Decimal`` scalar off the entity, failing CLOSED on an
    absent / non-numeric / non-positive value (a zero-or-negative stability budget would make the
    dose ratio undefined or nonsensical, not merely wrong)."""
    if key not in entity:
        raise ColdChainAssessError(
            f"cold_chain assess: input entity carries no '{key}' — the excursion severity cannot "
            "be derived (fail closed; the intake contract enriches the batch with its excursion "
            "scalars, PLAN-0074 Step 4)"
        )
    try:
        value = Decimal(str(entity[key]))
        # NaN / +-Infinity are "numeric" to Decimal and slip a bare `> 0` test (Inf budget -> a
        # near-zero dose ratio -> the LOWEST tier: a fail-DANGEROUS routing, not a closed door). A
        # severity that routes a human authority must be a finite, strictly-positive real.
        if not value.is_finite() or value <= 0:
            raise ColdChainAssessError(
                f"cold_chain assess: entity '{key}' must be a finite, strictly-positive number, "
                f"got {value} — a non-finite / non-positive excursion scalar cannot ground a "
                "severity (fail closed)"
            )
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ColdChainAssessError(
            f"cold_chain assess: entity '{key}' ({entity[key]!r}) is not a valid finite Decimal "
            "— fail closed"
        ) from exc
    return value


@dataclass(frozen=True)
class SeverityDerivation:
    """The structured, stable-keyed derivation outcome (the render / audit contract): the dose the
    excursion delivered, the cargo's budget, their ratio, and the severity it lands in — so a
    read-only render can show WHY a batch is CRITICAL without re-deriving the math."""

    magnitude_c: Decimal
    duration_h: Decimal
    dose_ch: Decimal
    budget_ch: Decimal
    ratio: Decimal
    severity: ExcursionSeverity

    def to_audit(self) -> dict[str, Any]:
        """JSON-safe projection for the step audit / output_set (JSONB) — ``Decimal`` -> ``str``
        (project memory: a raw ``Decimal`` fails the JSONB column on a persisted run)."""
        return {
            "magnitude_c": str(self.magnitude_c),
            "duration_h": str(self.duration_h),
            "dose_ch": str(self.dose_ch),
            "budget_ch": str(self.budget_ch),
            "ratio": str(self.ratio),
            "severity": self.severity.value,
        }


def derive_excursion_severity(entity: Mapping[str, Any]) -> SeverityDerivation:
    """Derive the :class:`ExcursionSeverity` of one excursion, DETERMINISTICALLY (same inputs ->
    same severity; no LLM, no clock, no randomness).

    dose = magnitude x duration (C*h above the cargo's ceiling); ratio = dose / stability budget;
    the ratio lands in exactly one band of :data:`_DOSE_LADDER` (total cover, unbounded top).
    Fails CLOSED (:class:`ColdChainAssessError`) on absent / non-numeric / non-positive scalars."""
    if not isinstance(entity, Mapping):
        raise ColdChainAssessError(
            f"cold_chain assess: entity {entity!r} is not a mapping — cannot read its excursion "
            "scalars (fail closed)"
        )
    magnitude = _positive_decimal(entity, MAGNITUDE_FIELD)
    duration = _positive_decimal(entity, DURATION_FIELD)
    budget = _positive_decimal(entity, BUDGET_FIELD)
    dose = magnitude * duration
    ratio = dose / budget
    severity = next(
        (sev for ceiling, sev in _DOSE_LADDER if ratio <= ceiling),
        _TOP_SEVERITY,
    )
    return SeverityDerivation(
        magnitude_c=magnitude,
        duration_h=duration,
        dose_ch=dose,
        budget_ch=budget,
        ratio=ratio,
        severity=severity,
    )


@dataclass(frozen=True)
class ColdChainAssessExecutor:
    """The ``assess``-step action-stamp wrapper (PLAN-0074 Step 4, SD-2) — a supply_chain-scoped
    delegating executor, the same extend-not-replace shape as
    :class:`~services.engine.procedures.governance_step.GovernanceActionExecutor` and
    :class:`~services.engine.procedures.env_band_step.EnvBandEvaluateExecutor` (LOCKED #5: the
    orchestrator's ``StepKind``-keyed contract is untouched).

    For a step named in ``stamp_steps`` it derives each entity's severity and STAMPS it (plus the
    derivation's audit projection and the criticality the scored rule amplifies) onto the entity
    BEFORE delegating to ``inner`` — which is the shipped governance wrapper, so ``assess``'s own
    ``scored_rule`` gate still runs untouched and its enriched output carries the stamp forward to
    the ``approve`` ``severity_tier`` gate. Every other step delegates straight through, so the
    vertical's existing (AT-3) sweep is byte-identical.

    Render / route only — no external write (ADR-0007 LOCKED #3)."""

    inner: StepExecutor
    stamp_steps: frozenset[str] = field(default_factory=frozenset)

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        if step.step_id not in self.stamp_steps:
            return await self.inner.execute(step, input_set, ctx)

        derivations = [derive_excursion_severity(entity) for entity in input_set]
        stamped: list[Any] = [
            {
                **entity,
                SEVERITY_FIELD: d.severity.value,
                "severity_derivation": d.to_audit(),
                # the scored rule's `criticality` criterion amplifier (0..1): a batch that has
                # burned more of its stability budget is more urgent, so the SAME authored rule
                # prefers the fast disposition lane for a critical excursion and the cheap one for
                # a negligible drift (governance_step._event_criticality clamps to [0, 1]).
                "criticality": str(min(Decimal(1), d.ratio)),
            }
            for entity, d in zip(input_set, derivations, strict=True)
        ]
        outcome = await self.inner.execute(step, stamped, ctx)
        trace = list(outcome.reasoning_trace) + [
            {
                "kind": "severity_derived",
                "severity": d.severity.value,
                "summary": (
                    f"excursion dose {d.dose_ch} C*h (magnitude {d.magnitude_c} C x duration "
                    f"{d.duration_h} h) against a {d.budget_ch} C*h stability budget -> "
                    f"severity '{d.severity.value}'"
                ),
            }
            for d in derivations
        ]
        audit = {
            **(outcome.audit or {}),
            "severity_derivation": [d.to_audit() for d in derivations],
        }
        return StepOutcome(output=outcome.output, reasoning_trace=trace, audit=audit)
