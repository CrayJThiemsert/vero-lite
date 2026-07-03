"""PLAN-0048 Step 1 — the compile seam: ``plan_read`` + ``ReadRefusal`` +
``readable_object_types`` (AC-1..AC-3).

ORACLE-FIRST DISCIPLINE (AC-2 / Lesson #0026, mirroring PLAN-0046 AC-5 and the
house block above the read-gate tests in ``test_orchestrator.py``): the pass/fail
matrix below is COMMITTED BEFORE any test or implementation code exists, so the
refusal contract cannot be quietly bent to whatever the implementation happens
to do. The tests in this module must implement EXACTLY this matrix; deviations
are surfaced, never silently absorbed.
"""

# ---------------------------------------------------------------------------
# PRE-COMMITTED PASS/FAIL MATRIX (PLAN-0048 AC-1/AC-2/AC-3; SD-1..SD-5 ratified
# as-recommended 2026-07-04 — single-read only, scope fixed).
# Fixture registry: object_type_names = {Pond, Reading}; step_id = "read".
#
# COMPILE (returns ReadPlan; AC-1):
#   COMPILE-1  reads=["Pond"], allowlist=["Pond"]          -> ReadPlan(step_id="read",
#              object_type="Pond", where={})   (in ontology ∩ allowlist)
#   COMPILE-2  reads=["Pond"], where={"verdict": "breach"} -> ReadPlan.where ==
#              {"verdict": "breach"}            (the where mapping is carried)
#   COMPILE-3  reads=["Pond"], allowlist=[]                -> compiles (LOCKED-5 /
#              OQ-6: empty object_types = UNCONSTRAINED, mirrors the load gate)
#
# REFUSE (raises ReadRefusal with STRUCTURED fields — refusal_kind + step_id
# (+ object_type where applicable); AC-2, the five ratified shapes):
#   REFUSE-1   reads=["Ghost"] (∉ ontology)                -> unknown_object_type,
#              object_type="Ghost", step_id="read"
#   REFUSE-2   reads=["Pond"], allowlist=["Reading"]       -> outside_allowlist,
#              object_type="Pond", step_id="read"
#   REFUSE-3   reads=["Pond", "Reading"] (len > 1)         -> unsupported_read_shape
#              (SD-1 ratified: single-read only; joins await a join grammar)
#   REFUSE-4   reads=["Pond"] + from="prior"               -> unsupported_read_shape
#              (two competing input sources = ambiguous; where would double-apply)
#   REFUSE-5   reads absent + from absent (entry-point)    -> unbound_query
#              (a silent [] here is exactly the must-1-banned empty masquerade)
#
# GUARDS beyond the ratified minimum (AC-1 totality — plan_read never returns
# garbage for ANY Step shape; labeled as guards, not matrix rows):
#   GUARD-1    reads absent + from="prior"                 -> unsupported_read_shape
#              (no DECLARED read to compile; SD-1 locates identity pass-through
#              in the Step-2 executor, which does not consult plan_read for it)
#   GUARD-2    step.kind != QUERY                          -> unsupported_read_shape
#              (the compile seam is a query-step contract; library callers get a
#              typed refusal, not a nonsense plan)
#
# INSPECT (readable_object_types; D-N3):
#   INSPECT-1  allowlist=[]                 -> the whole ontology set (LOCKED-5)
#   INSPECT-2  allowlist=["Pond"]           -> {"Pond"}   (ontology ∩ allowlist)
#   INSPECT-3  allowlist=["Pond", "Ghost"]  -> {"Pond"}   (unknown types drop out)
#
# TRIPWIRE (AC-3 — one bound, zero drift): the same fixture matrix driven
# through BOTH the load gate (validate_read_bindings) and plan_read must yield
# IDENTICAL accept/refuse decisions for the bound shapes:
#   in-ontology + in-allowlist -> both accept
#   unknown object_type        -> both refuse (gate: ProcedureError "does not
#                                 exist in the vertical's ontology"; seam:
#                                 unknown_object_type)
#   outside non-empty allowlist-> both refuse (gate: "is outside agent";
#                                 seam: outside_allowlist)
#   empty allowlist            -> both accept (unconstrained)
# The gate's ProcedureError messages stay BYTE-IDENTICAL to the pre-refactor
# wording (the PLAN-0046 tests in test_orchestrator.py are untouched and green).
# ---------------------------------------------------------------------------

import pytest

from services.engine.procedures.orchestrator import (
    ProcedureError,
    validate_read_bindings,
)
from services.engine.procedures.query_step import (
    ReadRefusal,
    ReadRefusalKind,
    plan_read,
    readable_object_types,
)
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    Procedure,
    Step,
    StepInput,
    StepKind,
    Trigger,
)

_REGISTRY = frozenset({"Pond", "Reading"})


def _agent(object_types: list[str] | None = None) -> Agent:
    return Agent(
        agent_id="a1",
        name="Agent One",
        autonomy_ceiling=Autonomy.GATED,
        allowed=AgentAllowed(step_kinds=[], action_handlers=[], object_types=object_types or []),
    )


def _query_step(
    *,
    reads: list[str] | None = None,
    where: dict[str, str] | None = None,
    from_step: str | None = None,
    input_absent: bool = False,
) -> Step:
    step_input = None if input_absent else StepInput(reads=reads, where=where, from_step=from_step)
    return Step(step_id="read", name="Read", kind=StepKind.QUERY, input=step_input)


def _refusal(step: Step, agent: Agent) -> ReadRefusal:
    with pytest.raises(ReadRefusal) as excinfo:
        plan_read(step, agent, _REGISTRY)
    return excinfo.value


# --- COMPILE (AC-1) ---------------------------------------------------------


def test_plan_read_compiles_in_coverage_single_read() -> None:
    """COMPILE-1: reads ∈ ontology ∩ allowlist -> ReadPlan with an empty where."""
    plan = plan_read(_query_step(reads=["Pond"]), _agent(object_types=["Pond"]), _REGISTRY)
    assert plan.step_id == "read"
    assert plan.object_type == "Pond"
    assert dict(plan.where) == {}


def test_plan_read_carries_where() -> None:
    """COMPILE-2: the OQ-4 post-fetch where mapping is carried on the plan."""
    plan = plan_read(
        _query_step(reads=["Pond"], where={"verdict": "breach"}),
        _agent(object_types=["Pond"]),
        _REGISTRY,
    )
    assert dict(plan.where) == {"verdict": "breach"}


def test_plan_read_empty_allowlist_is_unconstrained() -> None:
    """COMPILE-3 / LOCKED-5: empty object_types = UNCONSTRAINED, mirrors the load gate."""
    plan = plan_read(_query_step(reads=["Pond"]), _agent(), _REGISTRY)
    assert plan.object_type == "Pond"


# --- REFUSE (AC-2 — the five ratified shapes; structured fields asserted) ----


def test_plan_read_refuses_unknown_object_type() -> None:
    """REFUSE-1: reads names an object_type the ontology does not have."""
    refusal = _refusal(_query_step(reads=["Ghost"]), _agent(object_types=["Ghost"]))
    assert refusal.refusal_kind is ReadRefusalKind.UNKNOWN_OBJECT_TYPE
    assert refusal.object_type == "Ghost"
    assert refusal.step_id == "read"


def test_plan_read_refuses_outside_allowlist() -> None:
    """REFUSE-2: in-ontology but outside the agent's non-empty allowlist."""
    refusal = _refusal(_query_step(reads=["Pond"]), _agent(object_types=["Reading"]))
    assert refusal.refusal_kind is ReadRefusalKind.OUTSIDE_ALLOWLIST
    assert refusal.object_type == "Pond"
    assert refusal.step_id == "read"


def test_plan_read_refuses_multi_read() -> None:
    """REFUSE-3 / SD-1: single-read only — a multi-read refuses, never invents a join."""
    refusal = _refusal(
        _query_step(reads=["Pond", "Reading"]), _agent(object_types=["Pond", "Reading"])
    )
    assert refusal.refusal_kind is ReadRefusalKind.UNSUPPORTED_READ_SHAPE
    assert refusal.step_id == "read"


def test_plan_read_refuses_reads_plus_from_step() -> None:
    """REFUSE-4: reads + from are two competing input sources — ambiguous, refuse."""
    refusal = _refusal(
        _query_step(reads=["Pond"], from_step="prior"), _agent(object_types=["Pond"])
    )
    assert refusal.refusal_kind is ReadRefusalKind.UNSUPPORTED_READ_SHAPE
    assert refusal.step_id == "read"


def test_plan_read_refuses_unbound_entry_point() -> None:
    """REFUSE-5: reads absent + from absent = unbound entry-point query — the
    silent-[] shape must 1 bans. Both input=None and an empty StepInput refuse."""
    for step in (_query_step(input_absent=True), _query_step()):
        refusal = _refusal(step, _agent())
        assert refusal.refusal_kind is ReadRefusalKind.UNBOUND_QUERY
        assert refusal.step_id == "read"
        assert refusal.object_type is None


# --- GUARDS (AC-1 totality — beyond the ratified minimum, labeled) -----------


def test_plan_read_refuses_undeclared_read_with_from_step() -> None:
    """GUARD-1: reads absent + from present = no DECLARED read to compile;
    identity pass-through is the Step-2 executor's case (SD-1), not a plan."""
    refusal = _refusal(_query_step(from_step="prior"), _agent())
    assert refusal.refusal_kind is ReadRefusalKind.UNSUPPORTED_READ_SHAPE
    assert refusal.step_id == "read"


def test_plan_read_refuses_non_query_step() -> None:
    """GUARD-2: the compile seam is a query-step contract — other kinds refuse typed."""
    step = Step(step_id="judge", name="J", kind=StepKind.EVALUATE, input=StepInput(reads=["Pond"]))
    with pytest.raises(ReadRefusal) as excinfo:
        plan_read(step, _agent(), _REGISTRY)
    assert excinfo.value.refusal_kind is ReadRefusalKind.UNSUPPORTED_READ_SHAPE
    assert excinfo.value.step_id == "judge"


def test_read_refusal_message_names_kind_and_step() -> None:
    """The human-readable message carries the structured story too (audit-friendly)."""
    refusal = _refusal(_query_step(reads=["Ghost"]), _agent())
    assert "unknown_object_type" in str(refusal)
    assert "'read'" in str(refusal)
    assert "'Ghost'" in str(refusal)


# --- INSPECT (D-N3) ----------------------------------------------------------


def test_readable_object_types_empty_allowlist_is_whole_ontology() -> None:
    """INSPECT-1 / LOCKED-5: empty allowlist = unconstrained -> the whole ontology."""
    assert readable_object_types(_agent(), _REGISTRY) == _REGISTRY


def test_readable_object_types_intersection() -> None:
    """INSPECT-2: non-empty allowlist -> ontology ∩ allowlist."""
    assert readable_object_types(_agent(object_types=["Pond"]), _REGISTRY) == frozenset({"Pond"})


def test_readable_object_types_drops_unknown_allowlist_entries() -> None:
    """INSPECT-3: allowlisted-but-unknown types drop out — coverage ⊆ ontology."""
    assert readable_object_types(_agent(object_types=["Pond", "Ghost"]), _REGISTRY) == frozenset(
        {"Pond"}
    )


# --- TRIPWIRE (AC-3 — one bound, zero drift) ---------------------------------


def _gate_accepts(reads: list[str], agent: Agent) -> bool:
    proc = Procedure(
        procedure_id="p1",
        title="P",
        run_by="a1",
        trigger=Trigger.MANUAL,
        steps=[
            Step(step_id="read", name="Read", kind=StepKind.QUERY, input=StepInput(reads=reads))
        ],
    )
    try:
        validate_read_bindings(proc, agent, _REGISTRY)
    except ProcedureError:
        return False
    return True


def _seam_accepts(reads: list[str], agent: Agent) -> bool:
    try:
        plan_read(_query_step(reads=reads), agent, _REGISTRY)
    except ReadRefusal:
        return False
    return True


def test_tripwire_gate_and_seam_share_one_bound() -> None:
    """AC-3: the SAME fixture matrix through the load gate and the compile seam
    yields IDENTICAL accept/refuse decisions for every single-read bound shape
    (the shared read_bound_violation predicate cannot drift)."""
    matrix: list[tuple[list[str], Agent, bool]] = [
        (["Pond"], _agent(object_types=["Pond"]), True),  # in ontology ∩ allowlist
        (["Ghost"], _agent(object_types=["Ghost"]), False),  # unknown object_type
        (["Pond"], _agent(object_types=["Reading"]), False),  # outside allowlist
        (["Pond"], _agent(), True),  # empty allowlist = unconstrained
        (["Reading"], _agent(object_types=["Pond", "Reading"]), True),
    ]
    for reads, agent, expected in matrix:
        gate = _gate_accepts(reads, agent)
        seam = _seam_accepts(reads, agent)
        assert (
            gate == seam == expected
        ), f"bound drift on reads={reads}: gate={gate} seam={seam} expected={expected}"
