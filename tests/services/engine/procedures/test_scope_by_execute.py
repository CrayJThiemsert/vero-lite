"""PLAN-0113 Step 2 — the ``trigger_context`` -> ``query_step`` wire (AC-2).

Step 1 landed the grammar consuming nothing. This is the wire: a scoped BASE read
narrows to the run's firing entity, resolved from ``ctx.trigger_context["entity_ids"]``
at execute time.

**The assertion this module exists for is the ORDERING one.** SB-4 pins scope
post-``where``, pre-join, **pre-``latest_per``**, and that is semantics rather than
sequencing taste:

* applied BEFORE ``latest_per`` -> "the firing case's own latest reading" -> 1 row ->
  the visitor's gate proposes exactly their case;
* applied AFTER ``latest_per`` -> "the fleet's latest reading, iff that row happens to
  belong to the firing case" -> usually 0 rows -> the gate proposes NOTHING.

A test that only checks "the scoped output contains the right case" passes under BOTH
orders whenever the firing case happens to own the fleet-wide latest row. So the fixture
here is built so the two orders give DIFFERENT answers: the firing case's latest reading
is deliberately NOT the newest row in the store.

Offline + deterministic (CLAUDE.md §8): a counting fake adapter, no DB, no network.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

import pytest

from services.engine.ontology_meta import (
    JoinKeyMeta,
    LinkTypeMeta,
    ObjectTypeMeta,
    OntologyMeta,
    PropertyMeta,
)
from services.engine.procedures.orchestrator import RunContext, _failure_trace_entry
from services.engine.procedures.query_step import (
    QueryStepExecutor,
    ReadRefusal,
    ReadRefusalKind,
    matches_scope,
    scope_ids,
)
from services.engine.procedures.spec import (
    Agent,
    AgentAllowed,
    Autonomy,
    Step,
    StepInput,
    StepKind,
)

# --------------------------------------------------------------------------- #
# Fixture world — an event stream keyed by case, plus the ontology the join path
# resolves `latest_per` against.
# --------------------------------------------------------------------------- #

_VISITOR_CASE = "case-visitor"
_OTHER_CASE = "case-other"

#: The ordering fixture. `case-visitor`'s own latest reading is `ev-2` (12:00), but the
#: FLEET-wide latest is `ev-4` (14:00), which belongs to `case-other`. So:
#:   scope-then-latest_per  -> [ev-2]   (the visitor's own latest)  <- SB-4's pinned order
#:   latest_per-then-scope  -> []       (ev-4 is not the visitor's) <- the wrong order
#: The two answers differ, which is what makes the ordering assertion real.
_EVENT_ROWS: list[dict[str, Any]] = [
    {"event_id": "ev-1", "case_id": _VISITOR_CASE, "asset_id": "truck-01", "occurred_at": "10:00"},
    {"event_id": "ev-2", "case_id": _VISITOR_CASE, "asset_id": "truck-01", "occurred_at": "12:00"},
    {"event_id": "ev-3", "case_id": _OTHER_CASE, "asset_id": "truck-01", "occurred_at": "11:00"},
    {"event_id": "ev-4", "case_id": _OTHER_CASE, "asset_id": "truck-01", "occurred_at": "14:00"},
    # A ROUTINE event with no case at all — the shape fleet's real fixtures carry, and
    # the reason a scoped intake returns the firing case's rows alone.
    {"event_id": "ev-5", "asset_id": "truck-01", "occurred_at": "13:00"},
]

_META = OntologyMeta(
    vertical="fixture",
    object_types=[
        ObjectTypeMeta(
            name="OperationalEvent",
            primary_key="event_id",
            properties=[
                PropertyMeta(name=n, type="string")
                for n in ("event_id", "case_id", "asset_id", "occurred_at")
            ],
        ),
        ObjectTypeMeta(
            name="Asset",
            primary_key="asset_id",
            properties=[PropertyMeta(name=n, type="string") for n in ("asset_id", "plate")],
        ),
    ],
    link_types=[
        LinkTypeMeta(
            name="event_emitted_by_asset",
            from_type="OperationalEvent",
            to_type="Asset",
            foreign_key=JoinKeyMeta(from_property="asset_id", to_property="asset_id"),
        )
    ],
)
_ONTOLOGY = frozenset(t.name for t in _META.object_types)


class _CountingAdapter:
    """Protocol-complete counting fake — records every ``fetch_objects`` dispatch."""

    vertical_name = "fixture"

    def __init__(self, store: dict[str, list[dict[str, Any]]]) -> None:
        self._store = store
        self.calls: list[tuple[str, str | None]] = []

    async def fetch_objects(
        self, object_type: str, filter_expr: str | None = None, limit: int = 1000
    ) -> list[dict[str, Any]]:
        self.calls.append((object_type, filter_expr))
        return [dict(row) for row in self._store.get(object_type, [])]

    async def fetch_links(
        self, link_type: str, from_pk: str | None = None, to_pk: str | None = None
    ) -> list[dict[str, Any]]:
        return []

    def stream_events(
        self, event_type: str, since: datetime | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        raise NotImplementedError("not part of the v1 read surface (LOCKED-2)")


def _agent() -> Agent:
    return Agent(
        agent_id="a1",
        name="Agent One",
        autonomy_ceiling=Autonomy.GATED,
        allowed=AgentAllowed(),  # empty = unconstrained reads (OQ-6)
    )


def _ctx(entity_ids: Any = ..., *, no_trigger: bool = False) -> RunContext:
    """``entity_ids=...`` omits the key entirely; ``no_trigger`` omits the context."""
    if no_trigger:
        return RunContext(agent=_agent(), vertical="fixture")
    trigger: dict[str, Any] = {"source": "test", "trigger": "event"}
    if entity_ids is not ...:
        trigger["entity_ids"] = entity_ids
    return RunContext(agent=_agent(), vertical="fixture", trigger_context=trigger)


def _step(
    *,
    scope: bool,
    when_absent: str | None = "sweep",
    project: bool = False,
    field: str = "case_id",
) -> Step:
    payload: dict[str, Any] = {"reads": ["OperationalEvent"]}
    if project:
        payload["reads"] = ["OperationalEvent", "Asset"]
        payload["join"] = [{"with": "Asset", "link": "event_emitted_by_asset"}]
        payload["project"] = {"latest_per": "event_emitted_by_asset", "order_by": "occurred_at"}
    if scope:
        payload["scope_by"] = {"field": field, "from": "trigger.entity_ids"}
        payload["when_absent"] = when_absent
    return Step(
        step_id="intake",
        name="Intake",
        kind=StepKind.QUERY,
        input=StepInput.model_validate(payload),
    )


def _executor() -> QueryStepExecutor:
    store = {"OperationalEvent": _EVENT_ROWS, "Asset": [{"asset_id": "truck-01", "plate": "AA"}]}
    return QueryStepExecutor(
        adapter=_CountingAdapter(store),  # type: ignore[arg-type]
        object_type_names=_ONTOLOGY,
        meta=_META,
    )


def _ids(outcome: Any) -> list[str]:
    return [row["event_id"] for row in outcome.output]


def _scope_entries(outcome: Any) -> list[dict[str, Any]]:
    return [e for e in outcome.reasoning_trace if e.get("kind") == "scope_provenance"]


# --------------------------------------------------------------------------- #
# SB-1 match semantics — asserted DIRECTLY on the predicate, isolated from the
# shared fixture.
#
# These exist because the executor-level cases below all read one fixture that
# contains `ev-5` (no `case_id`), so a mutation to the field-missing branch ripples
# through every one of them and no probe can isolate a single behaviour. Given their
# own one-row inputs, each sub-behaviour of `matches_scope` gets a home that a
# targeted mutation can redden alone.
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("row", "expected", "why"),
    [
        ({"case_id": "c1"}, True, "a string value in the id list matches"),
        ({"case_id": "c9"}, False, "a string value outside the list does not"),
        ({"other": "c1"}, False, "a row missing the scope field never matches"),
        ({"case_id": None}, False, "a null value is not a string"),
        ({"case_id": 1}, False, "a non-string value never matches, even if 1 were in ids"),
        ("not-a-mapping", False, "a non-mapping row never matches (the matches_where posture)"),
        ([], False, "a non-mapping sequence never matches either"),
    ],
    ids=["in-list", "out-of-list", "missing-field", "null", "non-string", "string-row", "list-row"],
)
def test_matches_scope_semantics(row: Any, expected: bool, why: str) -> None:
    assert matches_scope(row, "case_id", ["c1", "c2"]) is expected, why


# --------------------------------------------------------------------------- #
# AC-2 (i) — scope present and matching
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_matching_scope_keeps_only_the_firing_cases_rows() -> None:
    outcome = await _executor().execute(_step(scope=True), [], _ctx([_VISITOR_CASE]))
    assert _ids(outcome) == ["ev-1", "ev-2"]


@pytest.mark.asyncio
async def test_a_row_without_the_scope_field_never_matches() -> None:
    """``ev-5`` is a ROUTINE event carrying no ``case_id`` — the shape fleet's real
    fixtures carry. It must fall out, mirroring ``matches_where``'s non-mapping
    posture, or a scoped intake would still drag unrelated readings to the gate."""
    outcome = await _executor().execute(_step(scope=True), [], _ctx([_VISITOR_CASE]))
    assert "ev-5" not in _ids(outcome)


@pytest.mark.asyncio
async def test_the_trigger_id_list_may_carry_ids_that_match_nothing() -> None:
    """Fleet stamps ``[case_id, quote_id]``. The quote id matches no ``case_id`` value
    and must be harmless, not an error — SB-1 says membership, not equality-of-list."""
    outcome = await _executor().execute(_step(scope=True), [], _ctx([_VISITOR_CASE, "quote-999"]))
    assert _ids(outcome) == ["ev-1", "ev-2"]


# --------------------------------------------------------------------------- #
# AC-2 (ii) — scope present, nothing matches (with its positive control)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_a_scope_matching_no_row_yields_zero_rows() -> None:
    outcome = await _executor().execute(_step(scope=True), [], _ctx(["case-nobody"]))
    assert _ids(outcome) == []


@pytest.mark.asyncio
async def test_positive_control_the_same_fixture_with_a_real_id_yields_rows() -> None:
    """Without this, the zero above is satisfied by an executor that returns nothing
    for every input — the empty-result vacuity CLAUDE.md §8 names explicitly."""
    outcome = await _executor().execute(_step(scope=True), [], _ctx([_VISITOR_CASE]))
    assert len(outcome.output) > 0


@pytest.mark.asyncio
async def test_zero_matches_is_a_completed_step_not_a_refusal() -> None:
    """Refusal != no-data (the PLAN-0048 D-N1 distinction, carried). A scope that
    APPLIES and keeps nothing is an empty result; only an ABSENT scope can refuse."""
    outcome = await _executor().execute(_step(scope=True), [], _ctx(["case-nobody"]))
    assert outcome.output == [] and _scope_entries(outcome)[0]["applied"] is True


# --------------------------------------------------------------------------- #
# AC-2 (iii) — absent + sweep is byte-identical in OUTPUT to an unscoped run
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("kwargs", "why"),
    [
        ({"entity_ids": ...}, "missing key"),
        ({"entity_ids": None}, "non-list"),
        ({"entity_ids": []}, "empty list"),
        ({"no_trigger": True}, "no trigger context at all"),
    ],
    ids=["missing-key", "non-list", "empty-list", "no-context"],
)
@pytest.mark.asyncio
async def test_absent_with_sweep_matches_the_unscoped_run_exactly(
    kwargs: dict[str, Any], why: str
) -> None:
    """Equality against the ACTUAL unscoped run of the same fixture — not a length
    check, which would pass on a same-size but differently-ordered result.

    The four cases are the amendment's enumerated absent shapes plus the
    no-trigger-context-at-all case that a `manual` run presents."""
    swept = await _executor().execute(_step(scope=True, when_absent="sweep"), [], _ctx(**kwargs))
    unscoped = await _executor().execute(_step(scope=False), [], _ctx([_VISITOR_CASE]))
    assert swept.output == unscoped.output


@pytest.mark.asyncio
async def test_a_sweep_is_recorded_rather_than_silent() -> None:
    """The trace is not the output. OQ-3 makes the counted entry contractual, so
    "the gate saw the whole fleet" must be visible rather than inferred."""
    outcome = await _executor().execute(_step(scope=True, when_absent="sweep"), [], _ctx([]))
    entry = _scope_entries(outcome)[0]
    assert (entry["applied"], entry["post_scope_count"]) == (False, len(_EVENT_ROWS))


@pytest.mark.asyncio
async def test_a_step_declaring_no_scope_records_no_scope_entry() -> None:
    """A procedure that never adopted the grammar keeps a byte-identical TRACE too,
    not merely a byte-identical output."""
    outcome = await _executor().execute(_step(scope=False), [], _ctx([_VISITOR_CASE]))
    assert _scope_entries(outcome) == []


# --------------------------------------------------------------------------- #
# AC-2 (iv) — absent + refuse is a TYPED refusal, never a silent []
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_absent_with_refuse_raises_a_typed_refusal() -> None:
    with pytest.raises(ReadRefusal) as caught:
        await _executor().execute(_step(scope=True, when_absent="refuse"), [], _ctx([]))
    assert caught.value.refusal_kind is ReadRefusalKind.SCOPE_UNRESOLVED


@pytest.mark.asyncio
async def test_the_refusal_names_the_count_it_declined_to_hand_over() -> None:
    """OQ-3: never a silent narrowing. A refusal that named no number would leave
    "how much did the gate not see" unanswerable from the record.

    Asserted as a full phrase, not as ``str(count) in detail`` — a bare one-digit
    substring passes on any wrong count that happens to contain the digit, which is
    an oracle that cannot fail for the reason it claims to test."""
    with pytest.raises(ReadRefusal) as caught:
        await _executor().execute(_step(scope=True, when_absent="refuse"), [], _ctx([]))
    assert f"{len(_EVENT_ROWS)} unscoped rows" in caught.value.detail


@pytest.mark.asyncio
async def test_the_refusals_count_reaches_the_reasoning_trace() -> None:
    """OQ-3 closes through the PLAN-0048 wiring, and that route is asserted here.

    ``apply_scope`` appends nothing to ``provenance`` on the refusal path — it raises,
    and the raise discards the outcome. The count survives because
    ``orchestrator._failure_trace_entry`` turns a ``ReadRefusal`` into a structured
    ``read_refused`` entry carrying the message. Without this test, "every refusal
    records a counted entry" would rest on an inference about code in a different
    module rather than on a measurement."""
    with pytest.raises(ReadRefusal) as caught:
        await _executor().execute(_step(scope=True, when_absent="refuse"), [], _ctx([]))
    entry = _failure_trace_entry(caught.value)
    assert entry["kind"] == "read_refused"
    assert entry["refusal_kind"] == ReadRefusalKind.SCOPE_UNRESOLVED.value
    assert f"{len(_EVENT_ROWS)} unscoped rows" in entry["summary"]


def test_the_new_refusal_kind_is_additive() -> None:
    """The PLAN-0061 ``JOIN_SHAPE_VIOLATION`` precedent: existing members untouched."""
    assert {
        "unknown_object_type",
        "outside_allowlist",
        "unsupported_read_shape",
        "unbound_query",
        "join_shape_violation",
    } < {member.value for member in ReadRefusalKind}


# --------------------------------------------------------------------------- #
# SB-4 — THE ATTACHMENT POINT, on a fixture where the two orders DISAGREE
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_scope_applies_before_latest_per_so_the_gate_sees_the_firing_case() -> None:
    """The load-bearing ordering assertion.

    ``ev-2`` is the visitor's own latest reading; ``ev-4`` is the FLEET's latest and
    belongs to another case. Scoping first yields ``ev-2``. Scoping after ``latest_per``
    would yield ``[]`` — the visitor's gate would propose nothing at all."""
    outcome = await _executor().execute(_step(scope=True, project=True), [], _ctx([_VISITOR_CASE]))
    assert _ids(outcome) == ["ev-2"]


@pytest.mark.asyncio
async def test_the_ordering_fixture_really_does_separate_the_two_orders() -> None:
    """The control that makes the assertion above meaningful.

    If the fleet-wide latest row happened to BE the visitor's, both orders would agree
    and the test above would pass with the scope applied in the wrong place. This pins
    the premise: unscoped + latest_per selects ``ev-4``, which is NOT the visitor's."""
    unscoped = await _executor().execute(_step(scope=False, project=True), [], _ctx([]))
    assert _ids(unscoped) == ["ev-4"]
    assert _EVENT_ROWS[3]["case_id"] != _VISITOR_CASE


@pytest.mark.asyncio
async def test_the_join_path_records_its_scope_with_counts() -> None:
    """The counts are the BASE read's, taken at the attachment point: all 5 fetched
    events survive the (absent) base ``where``, and 2 survive the scope. They are
    deliberately NOT the step's final output size — ``latest_per`` reduces those 2 to
    1 further down the pipeline, and a provenance entry that reported the END state
    would say nothing about what the scope itself did."""
    outcome = await _executor().execute(_step(scope=True, project=True), [], _ctx([_VISITOR_CASE]))
    entry = _scope_entries(outcome)[0]
    assert (entry["pre_scope_count"], entry["post_scope_count"]) == (len(_EVENT_ROWS), 2)
    assert len(outcome.output) == 1  # latest_per, downstream of the counts above


# --------------------------------------------------------------------------- #
# `scope_ids` — the absent/present boundary, stated directly
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (..., None),
        (None, None),
        ([], None),
        ("case-1", None),
        ([_VISITOR_CASE], [_VISITOR_CASE]),
        ([_VISITOR_CASE, "q1"], [_VISITOR_CASE, "q1"]),
    ],
    ids=["missing", "none", "empty", "string-not-list", "one-id", "two-ids"],
)
def test_scope_ids_absent_shapes(value: Any, expected: list[str] | None) -> None:
    assert scope_ids(_ctx(value)) == expected


def test_a_list_of_non_strings_is_present_not_absent() -> None:
    """A deliberate reading of the ratified text, recorded because it is a fork.

    SB-2 enumerates exactly three absent shapes — missing key, non-list, empty list —
    and a non-empty list of non-strings is none of them. So the scope APPLIES, nothing
    matches, and the step yields zero rows. The alternative reading (treat it as absent)
    would SWEEP under ``when_absent: sweep``, handing a gate every case in the vertical
    on the strength of an upstream type bug — the fail-open outcome the per-step policy
    exists to remove."""
    assert scope_ids(_ctx([1, 2])) == []


@pytest.mark.asyncio
async def test_a_non_string_id_list_yields_zero_rows_not_a_sweep() -> None:
    """The behavioural half of the decision above — the assertion that would flip if
    someone later re-read a non-string list as absent."""
    outcome = await _executor().execute(_step(scope=True, when_absent="sweep"), [], _ctx([1, 2]))
    assert outcome.output == []
