"""The fail-closed principal-SoD run-check (ADR-0026 D4; PLAN-0043 A1a Step 5).

The RUN-side complement to the author-time STRUCTURAL separation-of-duties
(:class:`~services.engine.procedures.spec.SoDConstraint`, enforced at load): given who
actually acted on each constrained step, this resolves them to :class:`Person`s and fails
**CLOSED** — emits NO "governed" verdict — when

* a constrained step has no ``required_role`` (the step->role map is incomplete),
* no principal resolved for a constrained step (nobody acted / not supplied),
* the acting principal is unknown (not a declared :class:`Person`),
* the acting principal does not hold the step's ``required_role`` (role mismatch), or
* two constrained steps collapse to ONE human — a ``person_id`` PK match **OR** a shared
  :class:`PrincipalAlias` link (OQ-3=(c), SD-2=(b)); alias links are unioned transitively.

It is the resolved-principal distinctness the author-time ``SoDConstraint`` could only assert
structurally (two *steps*, not two *humans*) — the Alternative-5 failure ADR-0025 rejected
role-label SoD to prevent. Render / route / block only — NO ERP I/O (ADR-0026 LOCKED #3); the
ADR-0007 approve->execute gate stays the only external write path. Pure + deterministic: no
LLM, no DB, no network — the offline tests are the gate (CLAUDE.md §8).

The verdict is **STRUCTURED** — each violation names which constraint fired, which step(s),
and which principal(s) collapsed / were unresolvable — never a bare boolean, so a later
read-only render can surface the governance moment (the hero-demo convergence ask).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from services.engine.procedures.spec import (
    Person,
    PersonId,
    PrincipalAlias,
    Procedure,
    RoleId,
    StepId,
)


class SoDViolationKind(StrEnum):
    """Why the principal-SoD run-check failed closed for one constrained step / pair."""

    UNRESOLVED_ROLE = "unresolved_role"
    """A constrained step has no ``required_role`` in the SoDConstraint map (incomplete)."""
    UNRESOLVED_PRINCIPAL = "unresolved_principal"
    """No principal was supplied for a constrained step (nobody resolved — fail closed)."""
    UNKNOWN_PRINCIPAL = "unknown_principal"
    """The acting ``person_id`` is not a declared :class:`Person`."""
    ROLE_MISMATCH = "role_mismatch"
    """The acting principal does not hold the step's ``required_role``."""
    PRINCIPAL_COLLAPSE = "principal_collapse"
    """Two constrained steps resolve to ONE human (PK match or a shared alias link)."""


@dataclass(frozen=True)
class SoDViolation:
    """One fail-closed reason, structured for a read-only render (NOT a bare bool)."""

    kind: SoDViolationKind
    constraint_steps: frozenset[StepId]
    """The ``SoDConstraint.distinct_steps`` whose check fired."""
    detail: str
    """Human-readable summary of which constraint / pair fired (for the governance render)."""
    steps: tuple[StepId, ...] = ()
    """The specific constrained step(s) involved."""
    principals: tuple[PersonId, ...] = ()
    """The person_id(s) involved — e.g. the collapsed pair, or the unknown/mismatched actor."""
    required_role: RoleId | None = None
    """The role expected at the step, when relevant."""


@dataclass(frozen=True)
class PrincipalSoDVerdict:
    """The run-check outcome. ``governed`` is True iff NO violation fired (fail-closed: any
    unresolved/mismatched/collapsed principal makes it False). ``violations`` carries the
    structured why."""

    governed: bool
    violations: tuple[SoDViolation, ...] = field(default_factory=tuple)


def _canonical_identity(aliases: list[PrincipalAlias]) -> dict[PersonId, PersonId]:
    """Union-find over declared alias groups: map every person_id named in any alias to a
    single canonical root, so transitively-linked identities (a aliases b, b aliases c) share
    a root. A person_id in no alias is its own identity (absent from the map). Two principals
    are the SAME human iff ``root(a) == root(b)`` (with a bare ``a == b`` covering the PK
    match for unaliased ids)."""
    parent: dict[PersonId, PersonId] = {}

    def find(x: PersonId) -> PersonId:
        parent.setdefault(x, x)
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:  # path-compress
            parent[x], x = root, parent[x]
        return root

    def union(a: PersonId, b: PersonId) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)  # deterministic root (lexicographically smallest)

    for alias in aliases:
        members = sorted(alias.members)
        for other in members[1:]:
            union(members[0], other)
    return {pid: find(pid) for pid in parent}


def _same_human(a: PersonId, b: PersonId, canonical: dict[PersonId, PersonId]) -> bool:
    """Two principals are one human iff their ids are equal (PK match) or share an alias root."""
    return a == b or canonical.get(a, a) == canonical.get(b, b)


def check_principal_sod(
    procedure: Procedure,
    *,
    principals: list[Person],
    principal_aliases: list[PrincipalAlias],
    step_principals: Mapping[StepId, PersonId | None],
) -> PrincipalSoDVerdict:
    """Resolve each SoD-constrained step to its acting :class:`Person` and fail CLOSED on an
    unresolvable role/principal, a role mismatch, or a two-into-one human collapse (ADR-0026
    D4). ``step_principals`` maps each constrained step to the ``person_id`` that acted on it
    (``None`` / absent = nobody resolved -> fail closed). Pure; the orchestrator / approval
    path supplies ``step_principals`` from the ``RunContext.principal`` + ``resolve_gated_step``
    principal seam (Step 4). A procedure with no ``separation_of_duties`` is vacuously governed
    (no constraint to enforce)."""
    by_id = {p.person_id: p for p in principals}
    canonical = _canonical_identity(principal_aliases)
    violations: list[SoDViolation] = []

    for sod in procedure.separation_of_duties:
        resolved: dict[StepId, PersonId] = {}
        for step_id in sorted(sod.distinct_steps):
            required = sod.required_roles.get(step_id)
            if required is None:
                violations.append(
                    SoDViolation(
                        SoDViolationKind.UNRESOLVED_ROLE,
                        sod.distinct_steps,
                        f"constrained step '{step_id}' has no required_role",
                        steps=(step_id,),
                    )
                )
                continue
            pid = step_principals.get(step_id)
            if pid is None:
                violations.append(
                    SoDViolation(
                        SoDViolationKind.UNRESOLVED_PRINCIPAL,
                        sod.distinct_steps,
                        f"no principal resolved for constrained step '{step_id}' (role "
                        f"'{required}')",
                        steps=(step_id,),
                        required_role=required,
                    )
                )
                continue
            person = by_id.get(pid)
            if person is None:
                violations.append(
                    SoDViolation(
                        SoDViolationKind.UNKNOWN_PRINCIPAL,
                        sod.distinct_steps,
                        f"step '{step_id}' principal '{pid}' is not a declared Person",
                        steps=(step_id,),
                        principals=(pid,),
                        required_role=required,
                    )
                )
                continue
            if required not in person.roles:
                violations.append(
                    SoDViolation(
                        SoDViolationKind.ROLE_MISMATCH,
                        sod.distinct_steps,
                        f"step '{step_id}' principal '{pid}' does not hold required role "
                        f"'{required}'",
                        steps=(step_id,),
                        principals=(pid,),
                        required_role=required,
                    )
                )
                continue
            resolved[step_id] = pid

        steps_sorted = sorted(resolved)
        for i in range(len(steps_sorted)):
            for j in range(i + 1, len(steps_sorted)):
                step_a, step_b = steps_sorted[i], steps_sorted[j]
                pid_a, pid_b = resolved[step_a], resolved[step_b]
                if _same_human(pid_a, pid_b, canonical):
                    violations.append(
                        SoDViolation(
                            SoDViolationKind.PRINCIPAL_COLLAPSE,
                            sod.distinct_steps,
                            f"steps '{step_a}' and '{step_b}' resolve to the same human "
                            f"('{pid_a}' / '{pid_b}')",
                            steps=(step_a, step_b),
                            principals=(pid_a, pid_b),
                        )
                    )

    return PrincipalSoDVerdict(governed=not violations, violations=tuple(violations))
