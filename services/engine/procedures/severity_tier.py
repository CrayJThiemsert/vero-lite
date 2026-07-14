"""The deterministic ``severity_tier`` resolution (ADR-0025 D2/D3; ADR-0031 D3 gate-kind
seam; PLAN-0074 Step 3).

The RUN-side enforcement of the author-time
:class:`~services.engine.procedures.spec.SeverityLadder` (the typed AT-2 NON-MONEY authority
content): given the :class:`~services.engine.procedures.spec.ExcursionSeverity` a
``severity_tier``-bearing step consumes, resolve the required severity tier via the ladder's
half-open total-cover ORDINAL band, resolve that tier's ``approver_role`` to the acting
:class:`Person`, and **fail CLOSED** — raise :class:`SeverityTierError`, never silently guess —
when the entity carries no resolvable severity.

The non-money analog of :func:`~services.engine.procedures.doa_tier.resolve_doa_tier`: the
authority quantity is a CLOSED ORDINAL (``ExcursionSeverity``), ranked by ``SEVERITY_BY_RANK``,
never money — a ``severity_tier`` gate authorises on patient-safety / regulatory severity, so
``DoaLadder`` (money-typed) cannot represent it (PLAN-0074 SD-1).

Pure + deterministic: no LLM, no DB, no network — the offline tests are the gate (CLAUDE.md §8).
The verdict is STRUCTURED + stable-keyed (the render contract): which tier resolved, the
required approver role, the excursion severity, the tier's half-open ordinal band, whether the
step is SoD-constrained, and the resolved approver's ``person_id`` — so a read-only render can
surface the governance moment ("a CRITICAL excursion → qp_release") without parsing prose. The
LLM only summarises (advisory, elsewhere); it NEVER decides the tier (governed ≠ generated,
ADR-0019 IN-3). Render / route / block only — no external write (ADR-0007 LOCKED #3).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.engine.procedures.orchestrator import ProcedureError
from services.engine.procedures.spec import (
    SEVERITY_BY_RANK,
    ExcursionSeverity,
    Person,
    PersonId,
    RoleId,
    SeverityLadder,
)


class SeverityTierError(ProcedureError):
    """A ``severity_tier`` step failed CLOSED (PLAN-0074 Step 3).

    Raised when the input entity carries no resolvable ``ExcursionSeverity`` — a severity tier
    cannot be routed without a severity. Failing closed blocks the tier routing **before** any
    approve/execute — no governed verdict is emitted (render / route / block only)."""


@dataclass(frozen=True)
class SeverityBand:
    """The resolved tier's half-open ``[min, max)`` ORDINAL band. ``max`` is ``None`` for the
    unbounded top tier — so the render can show the severity ceiling the excursion crossed."""

    min: ExcursionSeverity
    max: ExcursionSeverity | None


@dataclass(frozen=True)
class SeverityTierVerdict:
    """The structured, stable-keyed ``severity_tier`` outcome (the render contract — mirroring
    :class:`~services.engine.procedures.doa_tier.DoaTierVerdict`, but severity-keyed not
    money-keyed, PLAN-0074).

    ``resolved_tier_id`` is the tier's stable handle — its ``approver_role``. ``required_role``
    is the role that must approve at this tier (== ``approver_role``). ``resolved_approver_id``
    is the ``person_id`` that role resolves to via the vertical principals (``None`` if no
    declared :class:`Person` holds it — the fail-closed-on-unresolved-approver is the SoD
    run-check's job at the gate, not this resolution). The render joins audit → control →
    principal on these keys."""

    resolved_tier_id: str
    required_role: RoleId
    severity: ExcursionSeverity
    band: SeverityBand
    sod_required: bool
    resolved_approver_id: PersonId | None

    def to_audit(self) -> dict[str, Any]:
        """JSON-safe projection for the step audit / output_set (JSONB) — the ordinal severity
        renders as its string value; all fields are already JSON-native (no ``Decimal``)."""
        return {
            "resolved_tier_id": self.resolved_tier_id,
            "required_role": self.required_role,
            "severity": self.severity.value,
            "band": {
                "min": self.band.min.value,
                "max": None if self.band.max is None else self.band.max.value,
            },
            "sod_required": self.sod_required,
            "resolved_approver_id": self.resolved_approver_id,
        }


def resolve_severity_tier(
    ladder: SeverityLadder,
    *,
    severity: ExcursionSeverity,
    principals: list[Person],
    sod_required: bool,
) -> SeverityTierVerdict:
    """Resolve the severity tier for ``severity`` over ``ladder`` (PLAN-0074 Step 3).

    ``ladder.tiers`` is validated ascending by ordinal floor with the first floor at the lowest
    severity (total cover from ``NEGLIGIBLE``) and strictly increasing, so every
    ``ExcursionSeverity`` maps to exactly one half-open band ``[min_i, min_{i+1})`` (top tier
    unbounded). The required tier is the rightmost whose ``min_severity`` rank <= the excursion's
    rank; its ``approver_role`` resolves to the acting :class:`Person` (the first by ``person_id``
    holding that role).

    Does NOT raise when the role resolves to no Person — the absent / unrecognised severity
    fail-closed is the caller's entity reader, before this resolution.

    ⚠ ENFORCEMENT SCOPE (s131 review finding — read before trusting the tier). This resolves +
    AUDITS which tier a severity routes to (``resolved_tier_id`` / ``required_role`` /
    ``resolved_approver_id``), but NO current gate path enforces that the acting approver holds the
    resolved ``required_role``: the live SoD run-check (``principal_sod.check_principal_sod``) only
    verifies the approver holds the procedure's generic SoD role (``approve: approver``) and is
    distinct from the requester — it never reads this ladder. So a lower-tier approver can today
    resolve a gate this ladder routed to a higher tier. This is a KNOWN, pre-existing gap shared
    with ``doa_tier`` (whose identical docstring was the source of this over-claim); closing it —
    requiring ``principal.roles ∋ required_role`` (or ``person_id == resolved_approver_id``) at
    ``resolve_gated_step``, and failing closed on ``resolved_approver_id is None`` — is a follow-on
    that touches the shipped procurement path, tracked for the gate-seam PLAN. Until then the ladder
    is an audit-grade ROUTING record, not yet an enforced authority control."""
    sev_rank = SEVERITY_BY_RANK.index(severity)
    tier_idx = max(
        (
            i
            for i, t in enumerate(ladder.tiers)
            if SEVERITY_BY_RANK.index(t.min_severity) <= sev_rank
        ),
        default=-1,
    )
    if tier_idx < 0:  # unreachable for a valid ladder (total cover from NEGLIGIBLE) — fail closed
        raise SeverityTierError(
            f"severity_tier: severity '{severity.value}' resolves to no tier — a SeverityLadder "
            f"totally covers from the lowest severity (PLAN-0074); fail closed"
        )
    tier = ladder.tiers[tier_idx]
    band_max = ladder.tiers[tier_idx + 1].min_severity if tier_idx + 1 < len(ladder.tiers) else None
    role = tier.approver_role
    holders = sorted(p.person_id for p in principals if role in p.roles)
    return SeverityTierVerdict(
        resolved_tier_id=role,
        required_role=role,
        severity=severity,
        band=SeverityBand(min=tier.min_severity, max=band_max),
        sod_required=sod_required,
        resolved_approver_id=holders[0] if holders else None,
    )
