"""Offline oracle for the fail-closed principal-SoD run-check (ADR-0026 D4; PLAN-0043 A1a
Step 5/6). Zero-LLM, no DB, no network — the offline tests ARE the gate (CLAUDE.md §8). Each
test's pass/fail read is the PLAN's pre-committed AC (AC-5 happy / AC-6 alias-collapse / AC-7
unresolvable-role / AC-9 fail-closed-default) — fixed before these tests were authored.
"""

from __future__ import annotations

from services.engine.procedures.orchestrator import RunContext
from services.engine.procedures.principal_sod import (
    PrincipalSoDVerdict,
    SoDViolationKind,
    check_principal_sod,
)
from services.engine.procedures.spec import (
    Agent,
    Person,
    PrincipalAlias,
    Procedure,
    SoDConstraint,
    Step,
    StepKind,
)


def _proc(
    required_roles: dict[str, str], *, steps: tuple[str, str] = ("intake", "approve")
) -> Procedure:
    """A 2-step procedure with a SoDConstraint over both steps + the given required_roles."""
    return Procedure(
        procedure_id="p",
        title="P",
        run_by="agent",
        steps=[
            Step(step_id=steps[0], name=steps[0].title(), kind=StepKind.QUERY),
            Step(step_id=steps[1], name=steps[1].title(), kind=StepKind.ACTION),
        ],
        separation_of_duties=[
            SoDConstraint(distinct_steps=frozenset(steps), required_roles=required_roles)
        ],
    )


_FULL_ROLES = {"intake": "requester", "approve": "approver"}


def _check(
    proc: Procedure,
    *,
    principals: list[Person],
    step_principals: dict[str, str | None],
    aliases: list[PrincipalAlias] | None = None,
) -> PrincipalSoDVerdict:
    return check_principal_sod(
        proc,
        principals=principals,
        principal_aliases=aliases or [],
        step_principals=step_principals,
    )


# --- AC-5: happy path -> governed ------------------------------------------------


def test_two_distinct_principals_are_governed() -> None:
    """AC-5: two SoD-constrained steps performed by two DISTINCT humans (distinct PKs, no
    shared alias), each holding the step's required role -> governed, no violation."""
    verdict = _check(
        _proc(_FULL_ROLES),
        principals=[
            Person(person_id="alice", name="Alice", roles=frozenset({"requester"})),
            Person(person_id="bob", name="Bob", roles=frozenset({"approver"})),
        ],
        step_principals={"intake": "alice", "approve": "bob"},
    )
    assert verdict.governed is True
    assert verdict.violations == ()


def test_procedure_without_sod_is_vacuously_governed() -> None:
    """No SoDConstraint -> nothing to enforce -> governed."""
    proc = Procedure(
        procedure_id="p",
        title="P",
        run_by="agent",
        steps=[Step(step_id="s", name="S", kind=StepKind.QUERY)],
    )
    verdict = _check(proc, principals=[], step_principals={})
    assert verdict.governed is True


# --- AC-6: alias-collapse fails closed (both OQ-3 triggers) ----------------------


def test_pk_match_collapse_fails_closed() -> None:
    """AC-6 (OQ-3 trigger 1 = bare PK match): two structurally-distinct steps performed by the
    SAME person_id -> fail closed, no governed verdict."""
    verdict = _check(
        _proc(_FULL_ROLES),
        principals=[
            Person(person_id="alice", name="Alice", roles=frozenset({"requester", "approver"})),
        ],
        step_principals={"intake": "alice", "approve": "alice"},
    )
    assert verdict.governed is False
    assert any(v.kind is SoDViolationKind.PRINCIPAL_COLLAPSE for v in verdict.violations)


def test_shared_alias_link_collapse_fails_closed() -> None:
    """AC-6 (OQ-3 trigger 2 = declared alias-set overlap, SD-2=(b)): two DIFFERENT person_ids
    that share a PrincipalAlias link are one human -> fail closed."""
    verdict = _check(
        _proc(_FULL_ROLES),
        principals=[
            Person(person_id="alice", name="Alice", roles=frozenset({"requester"})),
            Person(person_id="alice_oncall", name="Alice (on-call)", roles=frozenset({"approver"})),
        ],
        aliases=[PrincipalAlias(alias_id="g1", members=frozenset({"alice", "alice_oncall"}))],
        step_principals={"intake": "alice", "approve": "alice_oncall"},
    )
    assert verdict.governed is False
    collapse = [v for v in verdict.violations if v.kind is SoDViolationKind.PRINCIPAL_COLLAPSE]
    assert collapse and set(collapse[0].principals) == {"alice", "alice_oncall"}


def test_transitive_alias_link_collapse_fails_closed() -> None:
    """The alias union is transitive: alice~mid, mid~zed => alice and zed are one human."""
    verdict = _check(
        _proc(_FULL_ROLES),
        principals=[
            Person(person_id="alice", name="Alice", roles=frozenset({"requester"})),
            Person(person_id="zed", name="Zed", roles=frozenset({"approver"})),
        ],
        aliases=[
            PrincipalAlias(alias_id="g1", members=frozenset({"alice", "mid"})),
            PrincipalAlias(alias_id="g2", members=frozenset({"mid", "zed"})),
        ],
        step_principals={"intake": "alice", "approve": "zed"},
    )
    assert verdict.governed is False
    assert any(v.kind is SoDViolationKind.PRINCIPAL_COLLAPSE for v in verdict.violations)


def test_distinct_principals_not_sharing_alias_stay_governed() -> None:
    """An alias group that does NOT join the two acting principals must not false-collapse a
    legitimately distinct pair (availability: too-strict is a bug too)."""
    verdict = _check(
        _proc(_FULL_ROLES),
        principals=[
            Person(person_id="alice", name="Alice", roles=frozenset({"requester"})),
            Person(person_id="bob", name="Bob", roles=frozenset({"approver"})),
        ],
        aliases=[PrincipalAlias(alias_id="g1", members=frozenset({"alice", "alice_oncall"}))],
        step_principals={"intake": "alice", "approve": "bob"},
    )
    assert verdict.governed is True


# --- AC-7: unresolvable role / principal fails closed ----------------------------


def test_missing_required_role_fails_closed() -> None:
    """AC-7: a constrained step with no required_role is unresolvable -> fail closed."""
    verdict = _check(
        _proc({"intake": "requester"}),  # 'approve' has no required_role
        principals=[
            Person(person_id="alice", name="Alice", roles=frozenset({"requester"})),
            Person(person_id="bob", name="Bob", roles=frozenset({"approver"})),
        ],
        step_principals={"intake": "alice", "approve": "bob"},
    )
    assert verdict.governed is False
    assert any(v.kind is SoDViolationKind.UNRESOLVED_ROLE for v in verdict.violations)


def test_no_principal_for_constrained_step_fails_closed() -> None:
    """AC-7 / AC-9: a constrained step with no resolved principal (None / absent) fails
    closed — the fail-closed DEFAULT, never a silent pass."""
    verdict = _check(
        _proc(_FULL_ROLES),
        principals=[Person(person_id="alice", name="Alice", roles=frozenset({"requester"}))],
        step_principals={"intake": "alice", "approve": None},
    )
    assert verdict.governed is False
    assert any(v.kind is SoDViolationKind.UNRESOLVED_PRINCIPAL for v in verdict.violations)


def test_absent_principal_key_fails_closed() -> None:
    """AC-9: omitting a constrained step from step_principals cannot bypass the check — an
    absent key is treated as None and fails closed (no bypass-by-omission)."""
    verdict = _check(
        _proc(_FULL_ROLES),
        principals=[Person(person_id="alice", name="Alice", roles=frozenset({"requester"}))],
        step_principals={"intake": "alice"},  # 'approve' omitted entirely
    )
    assert verdict.governed is False
    assert any(v.kind is SoDViolationKind.UNRESOLVED_PRINCIPAL for v in verdict.violations)


def test_unknown_principal_fails_closed() -> None:
    """A person_id that is not a declared Person fails closed (cannot resolve identity)."""
    verdict = _check(
        _proc(_FULL_ROLES),
        principals=[Person(person_id="alice", name="Alice", roles=frozenset({"requester"}))],
        step_principals={"intake": "alice", "approve": "ghost"},
    )
    assert verdict.governed is False
    assert any(v.kind is SoDViolationKind.UNKNOWN_PRINCIPAL for v in verdict.violations)


def test_role_mismatch_fails_closed() -> None:
    """A principal who does not hold the step's required role fails closed (the binding is
    load-bearing, not decorative)."""
    verdict = _check(
        _proc(_FULL_ROLES),
        principals=[
            Person(person_id="alice", name="Alice", roles=frozenset({"requester"})),
            Person(person_id="carol", name="Carol", roles=frozenset({"requester"})),  # not approver
        ],
        step_principals={"intake": "alice", "approve": "carol"},
    )
    assert verdict.governed is False
    assert any(v.kind is SoDViolationKind.ROLE_MISMATCH for v in verdict.violations)


# --- the structured verdict (hero-demo convergence ask) --------------------------


def test_verdict_is_structured_not_a_bare_bool() -> None:
    """The fail-closed verdict carries WHICH constraint fired + WHICH principals collapsed, so
    a read-only render can surface the governance moment (not a bare boolean)."""
    verdict = _check(
        _proc(_FULL_ROLES),
        principals=[
            Person(person_id="alice", name="Alice", roles=frozenset({"requester", "approver"})),
        ],
        step_principals={"intake": "alice", "approve": "alice"},
    )
    assert verdict.governed is False
    (violation,) = verdict.violations
    assert violation.kind is SoDViolationKind.PRINCIPAL_COLLAPSE
    assert violation.constraint_steps == frozenset({"intake", "approve"})
    assert set(violation.principals) == {"alice"}
    assert "same human" in violation.detail


# --- AC-4: the RunContext.principal seam (OQ-2 ambient resolution) ----------------


def test_run_context_carries_optional_principal() -> None:
    """AC-4: RunContext gains a typed Person | None principal seam (OQ-2, the ambient
    resolution; the load-bearing identity is the explicit principal arg on
    resolve_gated_step). It defaults None so every existing caller is unchanged."""
    agent = Agent(agent_id="a", name="A")
    assert RunContext(agent=agent, vertical="v").principal is None
    alice = Person(person_id="alice", name="Alice", roles=frozenset({"requester"}))
    ctx = RunContext(agent=agent, vertical="v", principal=alice)
    assert ctx.principal is alice
