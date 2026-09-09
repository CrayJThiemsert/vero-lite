"""The aggregate paths' two silent drops are REFUSED at the validator — (a), RULED s288.

``_aggregate_duration`` and ``_aggregate_benefit`` each dropped two things without
saying so:

1. a ``started_week`` FILTER — ``_keep`` reads ``procedure_id``/``status`` only, so
   the aggregate answered across EVERY week (found s228);
2. any ``group_by`` — both sites build ``AggregateResult(...)`` with no ``groups``,
   so *"average duration per procedure"* returned ONE ungrouped number (found s232).

Cray ruled disposition **(a) refuse** (typed, s288), matching the s228 ruling on the
``count`` case: a silently wrong number is strictly worse than a refusal. The guard
is ``_validate_aggregate_dimensions`` — a SIBLING of ``_validate_week_dimension``,
not a widening of it, because that guard's message describes ``week_rollup``, which
no aggregate operation reaches.

This module is purpose-built so a probe battery can own its claims with a denominator
it can actually cover (``tests/batteries/s288-run-query-aggregate-refusal.json``). The
two SCENARIO tests that demonstrate the harm on the real seeded corpus live in
``test_run_query.py`` beside their ``count`` sibling and the fixture they need.

No database: every assertion here is over the pure validator.
"""

from __future__ import annotations

import pytest

from services.engine import run_query as rq
from services.engine.nl_query import QueryFilter, StructuredQuery


def test_the_week_guard_is_scoped_to_count_while_the_sibling_guard_refuses_the_aggregate() -> None:
    """Pins the count guard's scope — and, since s288, the boundary that MOVED.

    ``execute_run_query`` routes only ``count`` to ``_count``, and that guard's refusal
    explains itself in terms of ``week_rollup``, which no other operation touches. So
    an aggregate carrying the same filter shape is still NOT refused *by this guard*.

    🔴 **The predecessor of this test claimed more than it measured.** It lived in
    ``test_run_query.py`` and promised, in its docstring, *"if a future change repairs
    or refuses it, this test SHOULD fail"* — but its only assertion called
    ``_validate_week_dimension`` directly. The s288 repair went in as a sibling guard,
    so the behaviour every caller sees changed while that test stayed green. An oracle
    bound to one helper cannot see a change in what callers actually get. The second
    assertion below is the one that would have caught it.
    """
    aggregate = StructuredQuery(
        object_type=rq.RUN_CORPUS_TYPE,
        operation="avg",
        aggregate_property="duration_ms_total",
        filters=[
            QueryFilter(property="started_week", op="eq", value="2026-W01"),
            QueryFilter(property="procedure_id", op="eq", value="p1"),
        ],
    )
    # Half 1 — unchanged by s288: the count-scoped guard still says nothing here.
    assert rq._validate_week_dimension(aggregate) == []
    # Half 2 — the behaviour a caller sees. Silent before s288, refused after.
    errors = rq.validate_run_query(aggregate)
    assert errors, "the aggregate week-filter drop must be refused at the validator"
    assert any("started_week" in e for e in errors)


@pytest.mark.parametrize("operation", ["max", "min", "avg", "sum"])
@pytest.mark.parametrize("aggregate_property", ["duration_ms_total", "net_benefit_thb"])
def test_an_aggregate_carrying_a_week_filter_is_refused(
    operation: str, aggregate_property: str
) -> None:
    """Drop (1), across BOTH aggregate routes and all four operations.

    ``execute_run_query`` routes on ``aggregate_property``: ``net_benefit_thb`` to
    ``_aggregate_benefit``, everything else to ``_aggregate_duration``. Both read
    ``procedure_id``/``status`` only, so a week filter vanished at either. Their
    docstrings require the two sites to be fixed together, so both are parametrized
    rather than one standing in for the other.
    """
    query = StructuredQuery(
        object_type=rq.RUN_CORPUS_TYPE,
        operation=operation,
        aggregate_property=aggregate_property,
        filters=[QueryFilter(property="started_week", op="eq", value="2026-W01")],
    )
    errors = rq.validate_run_query(query)
    assert errors, f"{operation} over {aggregate_property} + week filter must be refused"
    joined = " ".join(errors)
    assert "started_week" in joined
    # Corrective, like every other refusal here: it must say what to ask instead.
    assert "without" in joined.lower()


@pytest.mark.parametrize("group_by", ["procedure_id", "status", "started_week"])
def test_an_aggregate_carrying_group_by_is_refused_for_every_dimension(group_by: str) -> None:
    """Drop (2). The refusal is not per-dimension — NO dimension survives.

    Both aggregate paths build ``AggregateResult(...)`` without a ``groups`` argument,
    so the grouping is lost before it could be dimension-specific. All three
    ``DIMENSIONS`` are parametrized because a guard that special-cased one
    (``started_week``, which drop (1) also names) would leave the other two silently
    answering a grouped question with a single number.
    """
    query = StructuredQuery(
        object_type=rq.RUN_CORPUS_TYPE,
        operation="avg",
        aggregate_property="duration_ms_total",
        group_by=group_by,
    )
    errors = rq.validate_run_query(query)
    assert errors, f"an aggregate grouped by {group_by!r} must be refused, not answered"
    # ⚠️ Scoped to the REFUSAL CLAUSE — everything before the first colon — and this
    # took two corrections to get right, both times because the instrument was wrong
    # and the message was fine. The refusal ends with a suggestion, "...or for a
    # 'count' grouped by 'procedure_id'/'status', which the corpus does serve", so:
    #   `group_by in e`                  passes on the suggestion alone (2 of 3 dims)
    #   `f"grouped by {group_by!r}" in e` ALSO passes on it — the suggestion contains
    #                                     that exact substring for procedure_id
    # Only the position distinguishes "the refusal named what you asked for" from
    # "the suggestion happened to mention it". A probe aimed at [procedure_id] is
    # what exposed both; it stayed GREEN under a mutation that de-named the clause.
    heads = [e.split(":", 1)[0] for e in errors]
    assert any(f"grouped by {group_by!r}" in h for h in heads), (
        "the refusal clause must name the dimension that was asked for, not merely "
        f"mention it in the suggestion that follows: {errors}"
    )


def test_an_empty_week_value_on_an_aggregate_is_still_refused() -> None:
    """The same ``is not None``-vs-truthiness hole the ``count`` guard documents.

    ``_wanted`` returns ``""`` for a filter carrying an empty value: falsy, but NOT
    None. The aggregate fold ignores that filter exactly as it ignores a populated
    one, so a truthiness-based guard would stay silent on the shape that still reaches
    the drop — and no test using ``"2026-W01"`` would ever reveal it.
    """
    query = StructuredQuery(
        object_type=rq.RUN_CORPUS_TYPE,
        operation="avg",
        aggregate_property="duration_ms_total",
        filters=[QueryFilter(property="started_week", op="eq", value="")],
    )
    assert rq.validate_run_query(query), (
        "an empty started_week value is falsy but not None, and the aggregate fold "
        "ignores it just the same — the guard must not miss it"
    )


@pytest.mark.parametrize(
    ("operation", "aggregate_property", "group_by", "filters"),
    [
        # Aggregates the corpus genuinely serves: _keep reads both dimensions.
        ("avg", "duration_ms_total", None, [("procedure_id", "p1")]),
        ("sum", "duration_ms_total", None, [("status", "completed")]),
        ("max", "net_benefit_thb", None, [("procedure_id", "p1")]),
        ("avg", "duration_ms_total", None, []),
        # count is a DIFFERENT operation and keeps every shape it had.
        ("count", None, "procedure_id", []),
        ("count", None, "status", [("procedure_id", "p1")]),
        ("count", None, "started_week", []),
    ],
)
def test_the_aggregate_guard_does_not_over_refuse(
    operation: str,
    aggregate_property: str | None,
    group_by: str | None,
    filters: list[tuple[str, str]],
) -> None:
    """Non-vacuity in the expensive direction — a guard that refuses everything passes
    every test above.

    Two families. The aggregate shapes are ones ``_keep`` serves correctly, so refusing
    them would trade a silent wrong answer for a wrong refusal. The ``count`` shapes are
    the leak test: this guard keys on ``operation in _AGGREGATE_OPS`` and ``count`` is
    not in that set — including ``count`` + ``group_by='started_week'``, which AC-5
    requires to answer with real per-week buckets.
    """
    query = StructuredQuery(
        object_type=rq.RUN_CORPUS_TYPE,
        operation=operation,
        aggregate_property=aggregate_property,
        group_by=group_by,
        filters=[QueryFilter(property=p, op="eq", value=v) for p, v in filters],
    )
    assert rq.validate_run_query(query) == []
