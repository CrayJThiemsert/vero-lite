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
