"""PLAN-0113 Step 1 (the ADR-016 Amendment 2026-08-23): the ``scope_by`` /
``when_absent`` grammar's schema + load gate + H-governance classification (AC-1).

Step 1 lands the DECLARATION and consumes nothing: no executor reads ``scope_by``
yet, and ``query_step.py`` still contains zero references to ``trigger_context``.
The wire is Step 2. Everything asserted here is therefore about what the spec
ACCEPTS, what it REFUSES at load, and what the governance pin RECORDS.

**The load-bearing assertion in this module is the absence one.** ADR-0034 D6 /
SB-6 require the two scope keys to be dropped from the governance snapshot when a
step declares no scope. A key that serialized always — even as ``null`` — would
move every one of the six verticals' config hashes at once, and every in-flight
run would refuse at resume (``governance_pin`` fails CLOSED on a mismatch, by
design). ``reads``/``join``/``project`` pin the always-present way; ``transform``
pins the only-when-supplied way; this grammar follows ``transform``.

Because "the key is absent" is satisfied by an empty dict, the absence is asserted
as an EXACT key-set equality against the pre-scope shape rather than as a bare
``not in`` — the equality reddens both when a scope key leaks in and when an
existing pinned key silently disappears.

Offline + deterministic (CLAUDE.md §8): pure model construction + sha256. No DB,
no adapter, no network, no YAML I/O.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from services.engine.procedures.draft import (
    STEP_GOVERNANCE_FIELDS,
    StepDraft,
    lift_to_step,
)
from services.engine.procedures.governance_pin import (
    build_governance_snapshot,
    compute_governance_hash,
)
from services.engine.procedures.spec import (
    Procedure,
    ScopeBySpec,
    Step,
    StepInput,
    StepKind,
    WhenAbsent,
)

# --------------------------------------------------------------------------- #
# Fixtures — pure dicts, so every case reads as the YAML an author would write
# --------------------------------------------------------------------------- #

_SCOPE = {"field": "case_id", "from": "trigger.entity_ids"}


def _scoped_input(**overrides: object) -> dict[str, object]:
    """A well-formed scoped read, overridable per case."""
    base: dict[str, object] = {
        "reads": ["OperationalEvent"],
        "scope_by": dict(_SCOPE),
        "when_absent": "sweep",
    }
    base.update(overrides)
    return base


def _proc(input_: StepInput, *, kind: StepKind = StepKind.QUERY) -> Procedure:
    return Procedure(
        procedure_id="p",
        title="P",
        goal="g",
        run_by="a",
        steps=[Step(step_id="q", name="Q", kind=kind, input=input_)],
    )


def _step_pin(input_: StepInput) -> dict[str, object]:
    pin: dict[str, object] = build_governance_snapshot(_proc(input_))["steps"][0]
    return pin


# --------------------------------------------------------------------------- #
# SB-1/SB-2 schema — the shape the YAML may declare
# --------------------------------------------------------------------------- #


def test_a_well_formed_scoped_query_step_constructs() -> None:
    """The positive control for every refusal below.

    Without it, a model that rejected EVERYTHING would pass all four refusal tests
    while the grammar was unusable."""
    input_ = StepInput.model_validate(_scoped_input())
    assert input_.scope_by == ScopeBySpec(field="case_id", from_source="trigger.entity_ids")
    assert input_.when_absent is WhenAbsent.SWEEP


def test_from_is_closed_to_the_single_v1_source() -> None:
    """SB-1: ``from`` is a closed Literal in v1. A second source is a future
    amendment under the catalog-growth convention, not something a vertical may
    invent at its own authoring site."""
    with pytest.raises(ValidationError):
        StepInput.model_validate(
            _scoped_input(scope_by={"field": "case_id", "from": "trigger.actor_id"})
        )


def test_from_is_required_not_defaulted() -> None:
    """A single-member Literal could have been defaulted. It is not: writing it at
    each site is what makes every run-time-valued read greppable."""
    with pytest.raises(ValidationError):
        StepInput.model_validate(_scoped_input(scope_by={"field": "case_id"}))


def test_scope_by_forbids_unknown_keys() -> None:
    """``extra="forbid"``, like every sibling in the read grammar — the property
    that makes the dynamic surface explicitly enumerable."""
    with pytest.raises(ValidationError):
        StepInput.model_validate(
            _scoped_input(
                scope_by={"field": "case_id", "from": "trigger.entity_ids", "default": "all"}
            )
        )


@pytest.mark.parametrize("member", ["sweep", "refuse"])
def test_when_absent_accepts_both_ratified_members(member: str) -> None:
    """OQ-1: the vocabulary is closed at exactly two — and BOTH must work, or the
    closed-vocabulary test below would pass on a one-member enum."""
    assert StepInput.model_validate(_scoped_input(when_absent=member)).when_absent is WhenAbsent(
        member
    )


def test_when_absent_vocabulary_is_closed() -> None:
    """OQ-1: a third posture (e.g. warn-then-sweep) is a future amendment. A warn
    variant is provenance's job, not a third policy."""
    with pytest.raises(ValidationError):
        StepInput.model_validate(_scoped_input(when_absent="warn"))


# --------------------------------------------------------------------------- #
# SB-3 load-gate posture — three refusals, each witnessable on its own
# --------------------------------------------------------------------------- #


def test_scope_by_without_reads_refuses_at_load() -> None:
    """SB-3: scope narrows the BASE READ's rows, so a step that declares no read has
    nothing to scope."""
    with pytest.raises(ValidationError, match="scope_by requires a declared reads list"):
        StepInput.model_validate(_scoped_input(reads=None))


def test_scope_by_without_when_absent_refuses_at_load() -> None:
    """SD-1 (RULED, Cray-typed s249): required-explicit. A silent default is exactly
    the fail-open/fail-closed ambiguity the per-step policy exists to remove — and the
    project has already retired one fail-open default at this same load gate."""
    with pytest.raises(ValidationError, match="scope_by requires an explicit when_absent"):
        StepInput.model_validate({"reads": ["OperationalEvent"], "scope_by": dict(_SCOPE)})


def test_when_absent_without_scope_by_refuses_at_load() -> None:
    """The sibling refusal: an absent-scope policy governing no scoped read is inert
    spec surface that READS as though it does something. Mirrors
    ``project.order_by``'s latest_per requirement."""
    with pytest.raises(ValidationError, match="when_absent is only meaningful with scope_by"):
        StepInput.model_validate({"reads": ["OperationalEvent"], "when_absent": "sweep"})


@pytest.mark.parametrize(
    "kind",
    [k for k in StepKind if k is not StepKind.QUERY],
    ids=lambda k: k.value,
)
def test_scope_by_on_a_non_query_step_refuses_at_load(kind: StepKind) -> None:
    """SB-3: the third refusal needs the STEP's kind, so it lives on ``Step`` rather
    than ``StepInput`` — mirroring how ``transform`` is bound to a transform step. The
    input itself is well-formed here; only its host is wrong.

    Parametrized over EVERY non-query kind rather than one representative, and derived
    from ``StepKind`` rather than listed, for two reasons. ``action`` is the case that
    actually bites: ``Step._validate_step`` returns EARLY for an action step, so a
    scope check written below that return would pass a hand-picked ``evaluate`` case and
    silently let every action step through. And deriving the list means a sixth
    ``StepKind`` added later is covered here on the day it ships, instead of quietly
    escaping the gate."""
    scoped = StepInput.model_validate(_scoped_input())
    with pytest.raises(ValidationError, match="scope_by applies to query steps only"):
        Step(step_id="s", name="S", kind=kind, input=scoped)


def test_a_scoped_query_step_is_accepted_by_the_same_constructor() -> None:
    """Positive control for the refusal above: the identical input on a QUERY step
    constructs. Without it, a Step model that rejected every scoped input would pass
    the non-query test for the wrong reason."""
    scoped = StepInput.model_validate(_scoped_input())
    step = Step(step_id="q", name="Q", kind=StepKind.QUERY, input=scoped)
    assert step.input is not None and step.input.scope_by is not None


# --------------------------------------------------------------------------- #
# SB-5 / SD-2 — H-governance: the generator may never emit it
# --------------------------------------------------------------------------- #


def test_scope_fields_are_h_governed() -> None:
    assert {"scope_by", "when_absent"} <= STEP_GOVERNANCE_FIELDS


def test_lift_strips_the_scope_grammar_from_a_draft() -> None:
    """A generated skeleton may never decide which population reaches its own gate —
    the same rule that strips ``reads``/``join``/``project``.

    Deliberately COUPLED with the round-trip test below, and the coupling is declared
    in the probe battery rather than resolved by deleting one of them. Both rest on the
    same two lines of ``_strip_read_binding``, so no mutation can redden one and leave
    the other green — which means a probe targeting the strip legitimately reddens both,
    and the battery names both in advance. The alternative (drop the second test so the
    probe shows a single red) would have made the battery pass by shrinking the measured
    population, and "delete the collateral test" is a general-purpose way to make ANY
    battery pass."""
    draft = StepDraft(
        step_id="q",
        name="Q",
        kind=StepKind.QUERY,
        input=StepInput.model_validate(_scoped_input()),
    )
    step = lift_to_step(draft)
    assert step.input is not None
    assert (step.input.scope_by, step.input.when_absent) == (None, None)


def test_lift_yields_a_skeleton_that_survives_a_load_round_trip() -> None:
    """The D6 draft-loadable promise, at the altitude where the strip's REASON bites.

    ``model_copy(update=...)`` does NOT re-run validators (pydantic v2, by design —
    measured, not assumed), so a lift that dropped only ``scope_by`` would hand back,
    silently and without raising, a ``StepInput`` carrying a dangling ``when_absent``.
    Nothing would complain until that skeleton was round-tripped through
    ``load_procedures``, far from the cause. Asserting the round trip is what turns the
    joint strip from a style choice into a checked promise.

    See the coupling note on the test above: these two are one property at two
    altitudes, and the battery declares that rather than deleting either."""
    draft = StepDraft(
        step_id="q",
        name="Q",
        kind=StepKind.QUERY,
        input=StepInput.model_validate(_scoped_input()),
    )
    lifted = lift_to_step(draft).input
    assert lifted is not None
    # The round trip IS the assertion: an invalid intermediate raises here.
    StepInput.model_validate(lifted.model_dump(by_alias=True, exclude_none=True))


# --------------------------------------------------------------------------- #
# SB-6 — only-when-supplied pinning (the hash-stability half)
# --------------------------------------------------------------------------- #

_PRE_SCOPE_STEP_PIN_KEYS = frozenset(
    {"step_id", "kind", "autonomy", "handler", "governance_content", "reads", "join", "project"}
)
"""The step-level pinned surface as it stood BEFORE this grammar existed.

Written out rather than derived, so that adding a pinned key without deciding its
only-when-supplied posture fails HERE, at a test that says what the decision is."""


def test_an_unscoped_step_pins_exactly_the_pre_scope_key_set() -> None:
    """SB-6 / ADR-0034 D6 — the assertion the whole module exists for.

    A step that declares no scope must pin byte-identically to before this grammar
    landed. Asserted as exact set equality rather than ``"scope_by" not in pin``
    because a bare absence check passes on an empty dict; the equality also reddens
    if an existing pinned key silently vanishes."""
    assert set(_step_pin(StepInput.model_validate({"reads": ["OperationalEvent"]}))) == (
        _PRE_SCOPE_STEP_PIN_KEYS
    )


def test_a_scoped_step_pins_the_two_scope_keys_and_nothing_else() -> None:
    """The other side of the same equality — without this, the test above would pass
    on an implementation that never pinned scope at all."""
    assert set(_step_pin(StepInput.model_validate(_scoped_input()))) == (
        _PRE_SCOPE_STEP_PIN_KEYS | {"scope_by", "when_absent"}
    )


def test_the_pinned_scope_records_the_authored_field_and_source() -> None:
    """Pinned ``by_alias`` so ``from`` pins as authored, matching the join pin's
    treatment of ``with``."""
    pin = _step_pin(StepInput.model_validate(_scoped_input()))
    assert pin["scope_by"] == {"field": "case_id", "from": "trigger.entity_ids"}
    assert pin["when_absent"] == "sweep"


def test_a_scope_edit_changes_the_governance_hash() -> None:
    """The fail-closed teeth: scope decides WHICH ROWS reach a gate, so a mid-flight
    scope edit must trip the same pin mismatch a ladder edit does."""
    unscoped = compute_governance_hash(
        build_governance_snapshot(_proc(StepInput.model_validate({"reads": ["OperationalEvent"]})))
    )
    scoped = compute_governance_hash(
        build_governance_snapshot(_proc(StepInput.model_validate(_scoped_input())))
    )
    assert unscoped != scoped


def test_flipping_when_absent_alone_changes_the_governance_hash() -> None:
    """``when_absent`` is pinned as governance in its own right, not as decoration:
    sweep-vs-refuse is the difference between a run that read the fleet and a run that
    refused, and an approver's decision was made under one of them."""
    sweep = compute_governance_hash(
        build_governance_snapshot(_proc(StepInput.model_validate(_scoped_input())))
    )
    refuse = compute_governance_hash(
        build_governance_snapshot(
            _proc(StepInput.model_validate(_scoped_input(when_absent="refuse")))
        )
    )
    assert sweep != refuse


# --------------------------------------------------------------------------- #
# The Step 1 -> Step 2 boundary, INVERTED rather than deleted
# --------------------------------------------------------------------------- #


def test_the_executor_now_consumes_the_grammar_step_2_landed() -> None:
    """Step 1 shipped this assertion the other way round, and Step 2 flipped it.

    While Step 1 stood alone the load-bearing claim was *"the executor cannot see a
    trigger"* — ``query_step.py`` contained zero references to ``trigger_context``,
    which is what made "grammar only, consuming nothing" a checked property instead
    of a promise. Step 2's entire job is to build that wire, so this test was
    **guaranteed** to redden here.

    It is INVERTED rather than deleted. The boundary is still worth asserting; only
    its direction changed. Deleting it would have removed the one place that says
    which side of the Step 1 / Step 2 line the executor sits on, and a later reader
    would have no way to tell the wire was ever deliberately absent.

    Asserted against the ARTIFACT (the executor module's source), never against this
    test's own idea of it. The last assertion is the positive control: without it a
    typo'd path would make every claim above vacuous on an empty string."""
    from pathlib import Path

    source = Path("services/engine/procedures/query_step.py").read_text(encoding="utf-8")
    assert "trigger_context" in source
    assert "scope_field" in source
    # Positive control: the file was really read and really is the query executor.
    assert "matches_where" in source
