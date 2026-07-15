"""The fail-closed AT-2 tier-authority run-check (ADR-0026 D4, condition (iv); PLAN-0075).

The RUN-side complement to an AT-2 authority ladder (``DoaLadder`` / ``SeverityLadder``). The
ladder RESOLVES + audits which tier a spend / severity routes to; this module ENFORCES, at the
gate, that the acting approver actually **holds the ladder-resolved tier role** — the guarantee
ADR-0026 D5 always stated ("routes / suspends to the resolved approver for that tier") but no
run path delivered. It sits ADDITIVELY beside :func:`~services.engine.procedures.principal_sod`
(LOCKED #2 — never replacing or weakening it): the SoD check verifies the acting approver holds
the procedure's GENERIC step->role map (``approve: approver``) and is distinct from the requester;
this check verifies the acting approver holds the SPECIFIC, ladder-resolved tier role.

Fails **CLOSED** — emits NO governed verdict — when, on a gated step carrying AT-2 authority
content:

* the acting principal is unknown (not a declared :class:`Person`),
* the step declares authority content but carries NO persisted authority verdict at all (the
  plain-executor bypass: an executor binding that skips the governance wrapper would otherwise
  pass silently — PLAN-0075 AC-3), or
* the acting principal does not hold the ``required_role`` of one or more persisted verdicts
  (the ratified SD-1(a) predicate: exact ``required_role in principal.roles``, NO engine rank
  primitive — downward approval is authored as **cumulative role sets** in the vertical YAML,
  so a senior who holds the tier role passes; the multi-entity rule is SD-2(i): the principal
  must satisfy **EVERY** persisted verdict).

Render / route / **block** only — the ADR-0007 approve->execute gate stays the only external
write path. Pure + deterministic: no LLM, no DB, no network — the offline tests are the gate
(CLAUDE.md §8). The verdict is STRUCTURED (typed violation kinds, never a bare bool), so a
read-only render can surface WHY a gate was refused.

This module also owns :func:`native_approver` — the ROUTING-side companion the resolvers use to
name a tier's DESIGNATED approver (the person for whom that tier is their HIGHEST authority),
keeping the audit's routing record on the tier's own approver even when cumulative roles let a
senior also satisfy it. Routing (native) and enforcement (cumulative) are deliberately distinct.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from services.engine.procedures.spec import (
    AT2Governance,
    DoaLadder,
    Person,
    PersonId,
    RoleId,
    SeverityLadder,
    StepId,
)


def native_approver(
    role: RoleId,
    *,
    higher_roles: frozenset[RoleId],
    principals: Sequence[Person],
) -> PersonId | None:
    """The DESIGNATED approver for a tier whose approver role is ``role``: the sorted-first
    :class:`Person` who holds ``role`` but NONE of the tier's ``higher_roles`` — the person for
    whom this tier is their HIGHEST (native) authority.

    Under non-cumulative roles this is simply the sole holder. Under cumulative roles (a senior
    is authored to also hold ``role`` so they may approve downward — PLAN-0075 SD-1(a)), it
    EXCLUDES those seniors, keeping the audit's routing record on the tier's own approver while
    :func:`check_tier_authority` still ADMITS the seniors at enforcement. Routing and enforcement
    are deliberately distinct (Cray, s132 — native-tier routing). Falls back to the sorted-first
    holder of ``role`` when every holder also holds a higher role (a degenerate authoring, so no
    strictly-native holder exists), and ``None`` when nobody holds it (the fail-closed-on-no-
    approver is the gate's job, not this resolution)."""
    native = sorted(
        p.person_id for p in principals if role in p.roles and higher_roles.isdisjoint(p.roles)
    )
    if native:
        return native[0]
    holders = sorted(p.person_id for p in principals if role in p.roles)
    return holders[0] if holders else None


class TierAuthorityViolationKind(StrEnum):
    """Why the tier-authority run-check failed closed on a gated authority step."""

    UNKNOWN_PRINCIPAL = "unknown_principal"
    """The acting ``person_id`` is not a declared :class:`Person`."""
    VERDICT_MISSING = "verdict_missing"
    """The step declares AT-2 authority content but persisted NO authority verdict (the
    plain-executor bypass — PLAN-0075 AC-3)."""
    TIER_ROLE_MISMATCH = "tier_role_mismatch"
    """The acting principal does not hold the ``required_role`` of a persisted verdict."""


@dataclass(frozen=True)
class TierAuthorityViolation:
    """One fail-closed reason, structured for a read-only render (NOT a bare bool)."""

    kind: TierAuthorityViolationKind
    detail: str
    """Human-readable summary of what fired (for the governance render / the 403 body)."""
    step_id: StepId | None = None
    principal_id: PersonId | None = None
    required_role: RoleId | None = None
    resolved_approver_id: PersonId | None = None
    """The tier's routed-to (native) approver, when relevant — the honest routing record."""


@dataclass(frozen=True)
class TierAuthorityVerdict:
    """The run-check outcome. ``governed`` is True iff NO violation fired (fail-closed: any
    unknown principal / missing verdict / tier-role mismatch makes it False). ``violations``
    carries the structured why."""

    governed: bool
    violations: tuple[TierAuthorityViolation, ...] = field(default_factory=tuple)


def _is_authority_content(content: AT2Governance | None) -> bool:
    """An AT-2 *authority* gate is one that routes a human approver by a resolved tier — a
    ``DoaLadder`` (money) or ``SeverityLadder`` (ordinal severity). ``ScoredRule`` /
    ``ComplianceGate`` are AT-2 but not authority ladders (they select / gate; they do not route
    an approver tier)."""
    return isinstance(content, DoaLadder | SeverityLadder)


def check_tier_authority(
    *,
    principal: Person,
    step_id: StepId,
    governance_content: AT2Governance | None,
    persisted_verdicts: Sequence[Mapping[str, Any]],
    declared_principals: Sequence[Person],
) -> TierAuthorityVerdict:
    """Enforce that ``principal`` holds the ladder-resolved tier role of EVERY persisted authority
    verdict on a gated authority step, failing CLOSED otherwise (ADR-0026 D4 (iv); PLAN-0075).

    ``governance_content`` is the gated step's declared content — the check is INERT (vacuously
    governed) for a non-authority step, so a caller may invoke it unconditionally.
    ``persisted_verdicts`` is the ``to_audit()`` list the governance executor wrote at run time
    (``target.audit["doa_tier" | "severity_tier"]``); each entry carries ``required_role`` +
    ``resolved_approver_id``. ``declared_principals`` is the vertical's authored :class:`Person`
    set (to catch an undeclared acting principal independently of the SoD check, which is inert on
    a non-SoD authority gate). Pure; the gate (:func:`resolve_gated_step`) supplies the persisted
    verdicts + the acting principal.

    Fail-closed triggers (all applicable violations are reported, never short-circuited):
    (1) an authority step whose acting principal is not a declared Person -> ``UNKNOWN_PRINCIPAL``;
    (2) an authority step with no persisted verdict -> ``VERDICT_MISSING``;
    (3) any persisted verdict whose ``required_role`` the principal does not hold ->
    ``TIER_ROLE_MISMATCH`` (SD-1(a) exact match; SD-2(i) every verdict)."""
    # This IS an authority gate if the step declares authority content OR verdicts were persisted.
    # Keying on the persisted verdicts too means the check enforces even on a procedure-LESS gate
    # resolution (a legacy / non-SoD caller supplies no procedure — AC-4: "enforcement keys off the
    # persisted audit, works even procedure-less"); fail-closed, never inert while verdicts exist.
    content_is_authority = _is_authority_content(governance_content)
    if not content_is_authority and not persisted_verdicts:
        return TierAuthorityVerdict(governed=True)

    violations: list[TierAuthorityViolation] = []

    # Only assert declared-membership when a roster is supplied (an authority gate always carries
    # SoD, so the gate always passes the vertical principals; an empty roster = no roster to check
    # against, so skip rather than spuriously refuse — the per-verdict role check still applies).
    declared_ids = {p.person_id for p in declared_principals}
    if declared_ids and principal.person_id not in declared_ids:
        violations.append(
            TierAuthorityViolation(
                TierAuthorityViolationKind.UNKNOWN_PRINCIPAL,
                f"step '{step_id}' acting principal '{principal.person_id}' is not a declared "
                "Person — an authority gate cannot be resolved by an unknown principal",
                step_id=step_id,
                principal_id=principal.person_id,
            )
        )

    # VERDICT_MISSING fires only when the step DECLARES authority content but nothing persisted
    # (the plain-executor bypass); a procedure-less resolution with verdicts present skips it.
    if content_is_authority and not persisted_verdicts:
        violations.append(
            TierAuthorityViolation(
                TierAuthorityViolationKind.VERDICT_MISSING,
                f"step '{step_id}' declares AT-2 authority content but persisted no authority "
                "verdict — the tier the approver must hold cannot be established (fail closed; "
                "a governance-wrapper bypass would otherwise pass silently — PLAN-0075 AC-3)",
                step_id=step_id,
                principal_id=principal.person_id,
            )
        )

    for verdict in persisted_verdicts:
        required = verdict.get("required_role")
        if required is None or required not in principal.roles:
            violations.append(
                TierAuthorityViolation(
                    TierAuthorityViolationKind.TIER_ROLE_MISMATCH,
                    f"step '{step_id}' principal '{principal.person_id}' does not hold the "
                    f"ladder-resolved tier role '{required}' (routed to "
                    f"'{verdict.get('resolved_approver_id')}') — a lower-tier approver cannot "
                    "resolve a gate the ladder routed to a higher tier (ADR-0026 D4 (iv))",
                    step_id=step_id,
                    principal_id=principal.person_id,
                    required_role=required,
                    resolved_approver_id=verdict.get("resolved_approver_id"),
                )
            )

    return TierAuthorityVerdict(governed=not violations, violations=tuple(violations))
