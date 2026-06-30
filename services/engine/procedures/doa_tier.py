"""The deterministic ``doa_tier`` resolution (ADR-0025 D2/D3; ADR-0026 D5 / OQ-4;
PLAN-0044 A1b Step 3).

The RUN-side enforcement of the author-time :class:`~services.engine.procedures.spec.DoaLadder`
(the typed AT-2 delegation-of-authority content): given the ``Decimal`` spend on the entity a
``doa_tier``-bearing step consumes, resolve the required DOA tier via the ladder's half-open
total-cover band, resolve that tier's ``approver_role`` to the acting :class:`Person`, and **fail
CLOSED** — raise :class:`DoaTierError`, never silently convert — on a currency mismatch between the
entity and the ladder (OQ-4). Money is :class:`~decimal.Decimal`, never ``float`` (no binary-float
rounding on an authority threshold).

Pure + deterministic: no LLM, no DB, no network — the offline tests are the gate (CLAUDE.md §8).
The verdict is **STRUCTURED + stable-keyed** (the hero-demo render contract): which tier resolved,
the required approver role, the spend + its currency, the tier's half-open band, whether the step is
SoD-constrained, and the resolved approver's ``person_id`` — so a read-only render can surface the
governance moment ("฿288,000 crosses ฿50,000 → ผจก.จัดซื้อ") without parsing prose. The LLM only
summarises the justification (advisory, elsewhere); it NEVER decides the tier (governed ≠ generated,
ADR-0019 IN-3). Render / route / block only — NO PO is issued (ADR-0007 LOCKED #3).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from services.engine.procedures.orchestrator import ProcedureError
from services.engine.procedures.spec import DoaLadder, Person, PersonId, RoleId


class DoaTierError(ProcedureError):
    """A ``doa_tier`` step failed CLOSED (ADR-0026 D5 / OQ-4; PLAN-0044 A1b Step 3).

    Raised on a currency mismatch between the spend entity and the DOA ladder (no silent
    conversion) or a non-resolvable spend (a negative / missing amount). Failing closed here
    blocks the tier routing **before** any approve/execute — no PO is issued, no governed
    verdict is emitted (render / route / block only, LOCKED #3)."""


@dataclass(frozen=True)
class TierAmount:
    """The spend that drove the tier resolution — ``Decimal`` value + its ISO currency
    (never a formatted string; the render formats the human/Thai label itself)."""

    value: Decimal
    currency: str


@dataclass(frozen=True)
class TierBand:
    """The resolved tier's half-open ``[min, max)`` band (ADR-0025 D3). ``max`` is ``None``
    for the unbounded top tier — so the render can show the ceiling the spend crossed."""

    min: Decimal
    max: Decimal | None


@dataclass(frozen=True)
class DoaTierVerdict:
    """The structured, stable-keyed ``doa_tier`` outcome (the hero render contract, ask (a)).

    ``resolved_tier_id`` is the tier's stable handle — its ``approver_role`` (PLAN-0044 SD-1
    decision D1: a DOA tier's stable identity in a ladder is its distinct approver role; the
    band distinguishes tiers numerically). ``required_role`` is the role that must approve at
    this tier (== ``approver_role``). ``resolved_approver_id`` is the ``person_id`` that role
    resolves to via the vertical principals (``None`` if no declared :class:`Person` holds it —
    the fail-closed-on-unresolved-approver is the SoD run-check's job at the gate, A1b Step 1,
    not this resolution). The render joins audit → control → principal on these keys."""

    resolved_tier_id: str
    required_role: RoleId
    amount: TierAmount
    band: TierBand
    sod_required: bool
    resolved_approver_id: PersonId | None

    def to_audit(self) -> dict[str, Any]:
        """JSON-safe projection for the step audit / output_set (JSONB) — ``Decimal`` -> ``str``
        so the persisted artifact is serialisable while the authoritative values stay exact."""
        return {
            "resolved_tier_id": self.resolved_tier_id,
            "required_role": self.required_role,
            "amount": {"value": str(self.amount.value), "currency": self.amount.currency},
            "band": {
                "min": str(self.band.min),
                "max": None if self.band.max is None else str(self.band.max),
            },
            "sod_required": self.sod_required,
            "resolved_approver_id": self.resolved_approver_id,
        }


def resolve_doa_tier(
    ladder: DoaLadder,
    *,
    amount: Decimal,
    currency: str,
    principals: list[Person],
    sod_required: bool,
) -> DoaTierVerdict:
    """Resolve the DOA tier for ``amount`` over ``ladder``, failing CLOSED on a currency
    mismatch (ADR-0026 D5 / OQ-4; PLAN-0044 A1b Step 3).

    ``ladder.tiers`` is validated ascending by floor with the first floor at 0 and strictly
    increasing (total cover from zero spend), so every ``amount >= 0`` maps to exactly one
    half-open band ``[min_i, min_{i+1})`` (top tier unbounded). The required tier is the
    rightmost whose ``min_amount <= amount``; its ``approver_role`` resolves to the acting
    :class:`Person` (the first by ``person_id`` holding that role — procurement binds one
    Person per tier role). The spend is :class:`~decimal.Decimal`, never ``float``.

    Raises :class:`DoaTierError` (fail closed — no silent conversion) when ``currency`` differs
    from the ladder's single ``currency``, or when ``amount`` is below the ladder's zero floor
    (a negative / invalid spend). Does NOT raise when the role resolves to no Person — that is
    the SoD run-check's fail-closed surface at the gate (A1b Step 1), kept distinct here."""
    if currency != ladder.currency:
        raise DoaTierError(
            f"doa_tier: spend currency '{currency}' does not match the DOA ladder currency "
            f"'{ladder.currency}' — failing closed, no silent conversion (ADR-0026 OQ-4)"
        )
    tier_idx = max(
        (i for i, t in enumerate(ladder.tiers) if t.min_amount <= amount),
        default=-1,
    )
    if tier_idx < 0:
        raise DoaTierError(
            f"doa_tier: spend {amount} is below the ladder's zero floor — a DOA ladder totally "
            f"covers spend >= 0 (ADR-0025 D3); a negative/invalid amount fails closed"
        )
    tier = ladder.tiers[tier_idx]
    band_max = ladder.tiers[tier_idx + 1].min_amount if tier_idx + 1 < len(ladder.tiers) else None
    role = tier.approver_role
    holders = sorted(p.person_id for p in principals if role in p.roles)
    return DoaTierVerdict(
        resolved_tier_id=role,
        required_role=role,
        amount=TierAmount(value=amount, currency=currency),
        band=TierBand(min=tier.min_amount, max=band_max),
        sod_required=sod_required,
        resolved_approver_id=holders[0] if holders else None,
    )
