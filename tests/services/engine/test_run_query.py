"""AC-8 — A1 grounding parity over the run corpus (PLAN-0088 Step 5).

S5 claims ``nl_query``'s three provable-grounding properties are preserved *by
construction*. This module re-proves each one, and each test is written so that
it would fail if the property were lost rather than merely if the code changed:

1. unknown object type / property / non-numeric aggregate are rejected with
   validate-and-retry-shaped errors;
2. execute is deterministic and LLM-free — the chat client is monkeypatched to
   raise, and exact seeded values still come back;
3. an empty result short-circuits to the honest no-matching-records path.

Plus the two rules only this corpus has: ``operation='list'`` is rejected under
LOCKED SD-8 (a), and ``agent_id`` / ``trigger`` are absent from the v1 descriptor
per SD-9 (a2).

Skips gracefully when Postgres is unreachable.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.db.base import Base
from services.engine import run_query as rq
from services.engine.nl_query import QueryFilter, StructuredQuery
from tests.db_support import create_test_engine
from tests.support.run_corpus_factory import Corpus, build_corpus

_SEED = 77
_N_RUNS = 120


@dataclass
class _Seeded:
    session: AsyncSession
    corpus: Corpus


@pytest.fixture
async def seeded() -> AsyncIterator[_Seeded]:
    corpus = build_corpus(seed=_SEED, n_runs=_N_RUNS)
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(eng, expire_on_commit=False)
    async with maker() as session:
        session.add_all(corpus.rows)
        await session.commit()
        yield _Seeded(session=session, corpus=corpus)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


# --- property (1): semantic validation, validate-and-retry shaped -------------


def test_unknown_object_type_is_rejected() -> None:
    errors = rq.validate_run_query(StructuredQuery(object_type="Asset", operation="count"))
    assert errors
    # The message must NAME the valid types — that is what makes the error
    # correctable by a retry rather than merely a refusal.
    assert "pipeline_run" in errors[0]


def test_unknown_property_is_rejected_and_names_the_valid_ones() -> None:
    query = StructuredQuery(
        object_type=rq.RUN_CORPUS_TYPE,
        operation="count",
        filters=[QueryFilter(property="nonesuch", op="eq", value="x")],
    )
    errors = rq.validate_run_query(query)
    assert errors
    assert "nonesuch" in errors[0]
    assert "procedure_id" in errors[0]


def test_non_numeric_aggregate_property_is_rejected() -> None:
    query = StructuredQuery(
        object_type=rq.RUN_CORPUS_TYPE, operation="avg", aggregate_property="status"
    )
    assert rq.validate_run_query(query)


def test_eliminated_properties_are_not_in_the_v1_descriptor() -> None:
    """SD-9 (a2) struck ``agent_id`` and ``trigger``; absence is the enforcement."""
    props = {p.name for p in rq.run_corpus_meta()[rq.RUN_CORPUS_TYPE].properties}
    assert "agent_id" not in props
    assert "trigger" not in props
    assert props == {
        "procedure_id",
        "status",
        "started_week",
        "duration_ms_total",
        "net_benefit_thb",
    }


def test_list_operation_is_rejected_under_sd8() -> None:
    """No listing shape exists to serve, and the refusal must be *correctable*."""
    errors = rq.validate_run_query(
        StructuredQuery(object_type=rq.RUN_CORPUS_TYPE, operation="list")
    )
    assert errors
    joined = " ".join(errors)
    assert "list" in joined
    # Names what to use instead — a bare rejection would strand the retry loop.
    assert "count" in joined


def test_a_valid_query_produces_no_errors() -> None:
    """Non-vacuity for every rejection above: the validator is not refusing everything."""
    query = StructuredQuery(
        object_type=rq.RUN_CORPUS_TYPE,
        operation="count",
        filters=[QueryFilter(property="status", op="eq", value="completed")],
    )
    assert rq.validate_run_query(query) == []


@pytest.mark.parametrize(
    ("group_by", "blind_filter"),
    [
        (None, "procedure_id"),
        (None, "status"),
        ("started_week", "procedure_id"),
        ("started_week", "status"),
    ],
)
def test_a_weekly_query_carrying_a_dimension_the_rollup_lacks_is_refused(
    group_by: str | None, blind_filter: str
) -> None:
    """The four shapes where ``_count``'s week branch would DROP a filter in silence.

    Two of them reach the branch through a bare ``started_week`` FILTER with no
    ``group_by`` at all — the shape that made the defect reachable before PLAN-0104
    existed — which is why the guard cannot key on ``group_by`` alone.
    """
    filters = [] if group_by else [QueryFilter(property="started_week", op="eq", value="2026-W01")]
    filters.append(QueryFilter(property=blind_filter, op="eq", value="whatever"))
    query = StructuredQuery(
        object_type=rq.RUN_CORPUS_TYPE, operation="count", group_by=group_by, filters=filters
    )
    errors = rq.validate_run_query(query)
    assert errors, f"group_by={group_by!r} + {blind_filter} filter must be refused, not answered"
    joined = " ".join(errors)
    assert blind_filter in joined
    # Correctable, like the `list` rejection: it must say what to ask for instead.
    assert "without" in joined


@pytest.mark.parametrize(
    ("group_by", "filters"),
    [
        (None, [("started_week", "2026-W01")]),
        ("started_week", []),
        ("started_week", [("started_week", "2026-W01")]),
        (None, [("procedure_id", "p1")]),
        (None, [("status", "completed")]),
        ("status", [("procedure_id", "p1")]),
    ],
)
def test_the_week_guard_does_not_over_refuse(
    group_by: str | None, filters: list[tuple[str, str]]
) -> None:
    """Non-vacuity in the other direction — the expensive half to get wrong.

    Every shape here is served correctly today and must keep validating clean. The
    last one is the one a careless guard breaks: ``group_by='status'`` with a
    ``procedure_id`` filter routes to ``run_status_rollup``, which carries BOTH
    dimensions, so refusing it would trade a silent wrong answer for a wrong refusal.
    """
    query = StructuredQuery(
        object_type=rq.RUN_CORPUS_TYPE,
        operation="count",
        group_by=group_by,
        filters=[QueryFilter(property=p, op="eq", value=v) for p, v in filters],
    )
    assert rq.validate_run_query(query) == []


def test_the_week_branch_is_guarded_not_filtering() -> None:
    """Pins the coupling between the defect site and the fix, which are far apart.

    ``_count``'s week branch (``run_query.py``, the ``week_rollup`` path) applies the
    week filter and nothing else; it is correct ONLY because this refusal stops the
    dropped-filter shapes from reaching it. Deleting the guard restores a silently
    wrong answer at a line that itself looks unchanged, so the guarantee is asserted
    here rather than left to a comment.
    """
    reaches_the_branch = StructuredQuery(
        object_type=rq.RUN_CORPUS_TYPE,
        operation="count",
        filters=[
            QueryFilter(property="started_week", op="eq", value="2026-W01"),
            QueryFilter(property="procedure_id", op="eq", value="p1"),
        ],
    )
    assert rq.validate_run_query(reaches_the_branch), (
        "the week branch is unguarded: this query would reach week_rollup, which "
        "publishes no procedure_id dimension, and its filter would be silently dropped"
    )


def test_an_empty_week_value_still_reaches_the_branch_and_so_must_still_be_refused() -> None:
    """The guard tests ``is not None``, not truthiness — and the difference is a hole.

    ``_count``'s branch fires on ``_wanted(...) is not None``. An empty filter value
    makes ``_wanted`` return ``""``: falsy, but NOT None. A guard written with a
    truthiness test would therefore stay silent on exactly the shape that still
    reaches the dropping branch, and no test using a realistic week string like
    ``"2026-W01"`` would ever notice. This pins the two conditions together.
    """
    query = StructuredQuery(
        object_type=rq.RUN_CORPUS_TYPE,
        operation="count",
        filters=[
            QueryFilter(property="started_week", op="eq", value=""),
            QueryFilter(property="procedure_id", op="eq", value="p1"),
        ],
    )
    assert rq.validate_run_query(query), (
        "an empty started_week value is falsy but not None, so it still reaches "
        "_count's week branch — the guard must not miss it"
    )


# --- property (2): execute is deterministic and LLM-free ---------------------


async def test_count_matches_the_corpus_with_the_llm_client_disabled(
    seeded: _Seeded, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The execute path must not touch an LLM even when one is reachable.

    The chat-client builder is replaced with a raiser: if execution ever reached
    for a model, this test would error rather than quietly pass.
    """
    monkeypatch.setattr(
        "services.engine.nl_query._build_chat_client",
        lambda: (_ for _ in ()).throw(AssertionError("execute reached for an LLM")),
    )
    query = StructuredQuery(object_type=rq.RUN_CORPUS_TYPE, operation="count")
    result = await rq.execute_run_query(seeded.session, query)
    assert result.count == seeded.corpus.run_count


async def test_conjunctive_filter_matches_the_corpus_exactly(seeded: _Seeded) -> None:
    """The question Step 4.5 existed to make answerable, end to end."""
    (procedure_id, status), expected = next(iter(seeded.corpus.run_status_counts.items()))
    query = StructuredQuery(
        object_type=rq.RUN_CORPUS_TYPE,
        operation="count",
        filters=[
            QueryFilter(property="procedure_id", op="eq", value=procedure_id),
            QueryFilter(property="status", op="eq", value=status),
        ],
    )
    result = await rq.execute_run_query(seeded.session, query)
    assert result.count == expected
    # Non-vacuity: the filtered count must be strictly smaller than the total,
    # or the filter could be a no-op and this assertion would prove nothing.
    assert 0 < expected < seeded.corpus.run_count


async def test_duration_aggregate_matches_the_corpus_exactly(seeded: _Seeded) -> None:
    query = StructuredQuery(
        object_type=rq.RUN_CORPUS_TYPE, operation="max", aggregate_property="duration_ms_total"
    )
    result = await rq.execute_run_query(seeded.session, query)
    every_total = [t for totals in seeded.corpus.run_duration_totals.values() for t in totals]
    assert result.aggregate is not None
    assert result.aggregate.value == pytest.approx(max(every_total))


async def test_week_grouped_count_matches_the_corpus(seeded: _Seeded) -> None:
    week = next(iter(seeded.corpus.week_counts))
    query = StructuredQuery(
        object_type=rq.RUN_CORPUS_TYPE,
        operation="count",
        filters=[QueryFilter(property="started_week", op="eq", value=week)],
    )
    result = await rq.execute_run_query(seeded.session, query)
    assert result.count == seeded.corpus.week_counts[week]


# --- AC-5: a grouped count must never collapse to a single total (PLAN-0104) --


async def test_grouped_count_by_week_returns_per_week_figures_not_a_single_total(
    seeded: _Seeded,
) -> None:
    """AC-5, in the shape the AC names.

    Written to FAIL against the pre-PLAN-0104 ``_count``: that version summed the
    week rollup into ``week_total`` and returned it alone, so ``aggregate`` was
    None and the per-week figures were unrecoverable. Once the shared validator
    admits ``count`` + ``group_by``, that fold would answer "how many runs per
    week?" with one number — a silently wrong answer where the old refusal was at
    least honest.
    """
    query = StructuredQuery(
        object_type=rq.RUN_CORPUS_TYPE, operation="count", group_by="started_week"
    )
    result = await rq.execute_run_query(seeded.session, query)
    assert result.aggregate is not None
    assert result.aggregate.groups == {
        week: float(count) for week, count in seeded.corpus.week_counts.items()
    }
    assert result.matched == seeded.corpus.run_count


async def test_grouped_count_by_status_returns_one_figure_per_status(seeded: _Seeded) -> None:
    """The STRONG form of AC-5, and the one that can actually catch a fake grouping.

    The seeded corpus spans a single ISO week (``_N_DAYS = 5`` from a Monday
    base), so a per-week grouping has exactly one bucket — which cannot
    distinguish a real grouping from the total wrapped in one group. ``status``
    is genuinely multi-valued, so it can: a collapse-to-total would put the whole
    run count into a single bucket, and every assertion below would fail.
    """
    expected: dict[str, float] = {}
    for (_procedure_id, status), count in seeded.corpus.run_status_counts.items():
        expected[status] = expected.get(status, 0.0) + float(count)

    query = StructuredQuery(object_type=rq.RUN_CORPUS_TYPE, operation="count", group_by="status")
    result = await rq.execute_run_query(seeded.session, query)

    assert result.aggregate is not None
    assert result.aggregate.groups == expected
    assert result.matched == seeded.corpus.run_count
    # Non-vacuity: more than one bucket, no bucket holds the total, and the
    # buckets account for every run.
    assert len(expected) > 1
    assert max(result.aggregate.groups.values()) < float(seeded.corpus.run_count)
    assert sum(result.aggregate.groups.values()) == float(seeded.corpus.run_count)


async def test_ungrouped_count_over_the_run_corpus_carries_no_aggregate(seeded: _Seeded) -> None:
    """AC-3's run-corpus half: an ungrouped count keeps exactly its old shape —
    a plain ``count`` with no aggregate, phrased by the flat template."""
    query = StructuredQuery(object_type=rq.RUN_CORPUS_TYPE, operation="count")
    result = await rq.execute_run_query(seeded.session, query)
    assert result.count == seeded.corpus.run_count
    assert result.aggregate is None
    expected_text = f"{seeded.corpus.run_count} run(s) match that question."
    assert rq.fallback_run_answer(query, result) == expected_text


async def test_the_refused_weekly_combination_would_have_answered_the_whole_week(
    seeded: _Seeded,
) -> None:
    """Scenario: the harm the refusal prevents, demonstrated on the real corpus.

    Drives the real ``week_rollup`` SQL over seeded Postgres into the real ``_count``,
    with nothing stubbed. Two halves, and the second is what gives the first teeth:

    1. ``validate_run_query`` REFUSES *"how many runs of procedure X in week W?"*.
    2. Executed anyway — bypassing the validator exactly as a future edit deleting
       the guard would — ``_count`` returns the count of **every** run in that week,
       not procedure X's. The number is wrong, grounded-looking, and silent.

    The corpus seeds all runs into a single ISO week, so the wrong answer is the
    full corpus while the right one is one procedure's share. The assertion that
    those two differ is what stops this test from passing vacuously.
    """
    procedure = "emergency_sourcing"
    week = next(iter(seeded.corpus.week_counts))
    week_total = seeded.corpus.week_counts[week]
    procedure_total = seeded.corpus.procedure_counts[procedure]
    assert week_total != procedure_total, (
        "corpus makes this test vacuous: the week total and the procedure total "
        "coincide, so a dropped filter would be invisible"
    )

    dangerous = StructuredQuery(
        object_type=rq.RUN_CORPUS_TYPE,
        operation="count",
        filters=[
            QueryFilter(property="started_week", op="eq", value=week),
            QueryFilter(property="procedure_id", op="eq", value=procedure),
        ],
    )
    assert rq.validate_run_query(dangerous), "the combination must be refused before execution"

    # The teeth: what the refusal is protecting the caller from.
    executed = await rq._count(seeded.session, dangerous)
    assert executed.count == week_total
    assert executed.count != procedure_total


# --- property (3): empty result short-circuits honestly ----------------------


async def test_no_matching_records_returns_zero_matched_not_a_fabricated_figure(
    seeded: _Seeded,
) -> None:
    """A filter matching nothing must yield matched == 0 and NO aggregate value.

    The failure this guards against is an aggregate that quietly reports 0 (or
    the unfiltered figure) for an empty match — an answer that reads as grounded
    but is not.
    """
    query = StructuredQuery(
        object_type=rq.RUN_CORPUS_TYPE,
        operation="avg",
        aggregate_property="duration_ms_total",
        filters=[QueryFilter(property="procedure_id", op="eq", value="no-such-procedure")],
    )
    result = await rq.execute_run_query(seeded.session, query)
    assert result.matched == 0
    assert result.aggregate is None
