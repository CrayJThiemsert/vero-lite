"""AC-1 — the cross-run substrate over a seeded 250-run corpus (PLAN-0088 Step 1).

Seeds the AC-2 corpus factory into the disposable ``<db>_test`` and asserts each
``run_analytics`` primitive returns exactly the values the factory computed
independently (``Corpus.expected_*``, plain Python over the same seeded specs —
never the substrate's own SQL). Skips gracefully when Postgres is unreachable.

The load-bearing property is not the corpus size but the **statement-capture**
test: it proves the aggregation is pushed into SQL (``GROUP BY``, O(groups) rows),
so an accidental O(runs) materialize-then-count-in-Python regression fails here.
"""

from __future__ import annotations

import statistics
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

import pytest
import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.db import run_analytics as ra
from services.db.base import Base
from services.engine.procedures.runs import PipelineRun
from tests.db_support import create_test_engine
from tests.support.run_corpus_factory import Corpus, build_corpus

_SEED = 1234
_N_RUNS = 250


@dataclass
class _Seeded:
    session: AsyncSession
    corpus: Corpus
    statements: list[str]


@pytest.fixture
async def seeded() -> AsyncIterator[_Seeded]:
    corpus = build_corpus(seed=_SEED, n_runs=_N_RUNS)
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(eng, expire_on_commit=False)
    async with maker() as seed_session:
        seed_session.add_all(corpus.rows)
        await seed_session.commit()

    statements: list[str] = []

    def _capture(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(eng.sync_engine, "after_cursor_execute", _capture)
    async with maker() as session:
        yield _Seeded(session=session, corpus=corpus, statements=statements)
    event.remove(eng.sync_engine, "after_cursor_execute", _capture)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


async def test_corpus_meets_the_ac1_floor(seeded: _Seeded) -> None:
    """The seeded corpus is >= 250 runs / >= 1,250 step rows (AC-1 floor)."""
    assert seeded.corpus.run_count >= 250
    assert seeded.corpus.step_row_count >= 1250


async def test_status_rollup_exact(seeded: _Seeded) -> None:
    rows = await ra.status_rollup(seeded.session)
    assert {r.status: r.run_count for r in rows} == seeded.corpus.status_counts


async def test_procedure_rollup_exact(seeded: _Seeded) -> None:
    rows = await ra.procedure_rollup(seeded.session)
    assert {r.procedure_id: r.run_count for r in rows} == seeded.corpus.procedure_counts


async def test_period_rollup_exact_and_day_bucketed(seeded: _Seeded) -> None:
    rows = await ra.period_rollup(seeded.session)
    assert {r.period: r.run_count for r in rows} == seeded.corpus.period_counts
    # Every bucket key is a bare ISO date (day granularity), never a timestamp.
    assert all(len(r.period) == len("2026-06-01") for r in rows)


async def test_duration_stats_exact(seeded: _Seeded) -> None:
    rows = await ra.duration_stats(seeded.session)
    got = {(r.procedure_id, r.step_id): r for r in rows}
    assert set(got) == set(seeded.corpus.durations)
    for key, samples in seeded.corpus.durations.items():
        stat = got[key]
        assert stat.sample_count == len(samples)
        assert stat.max_ms == max(samples)
        assert stat.avg_ms == pytest.approx(statistics.mean(samples))


async def test_benefit_rollup_exact_and_per_currency(seeded: _Seeded) -> None:
    rows = await ra.benefit_rollup(seeded.session)
    got = {(r.currency, r.procedure_id): r for r in rows}
    assert set(got) == set(seeded.corpus.benefit)
    for key, expected in seeded.corpus.benefit.items():
        bucket = got[key]
        assert bucket.facet_count == expected["facet_count"]
        assert bucket.figures_missing == expected["facet_count"] - expected["valued"]
        assert bucket.net_benefit_thb_sum == Decimal(expected["sum"])
        if expected["valued"]:
            assert float(bucket.net_benefit_thb_avg) == pytest.approx(
                float(expected["sum"]) / expected["valued"]
            )
        assert bucket.provisional is True


async def test_currency_buckets_never_combine(seeded: _Seeded) -> None:
    """S7: THB and USD land in separate buckets — no cross-currency total exists."""
    rows = await ra.benefit_rollup(seeded.session)
    currencies = {r.currency for r in rows}
    assert {"THB", "USD"} <= currencies
    # The report row carries no cross-currency total field at all (structurally unrepresentable).
    assert not hasattr(rows[0], "net_benefit_thb_total")


async def test_refusal_counts_exact(seeded: _Seeded) -> None:
    rows = await ra.refusal_counts(seeded.session)
    assert {r.refusal_kind: r.count for r in rows} == seeded.corpus.refusals


async def test_gate_counts_exact(seeded: _Seeded) -> None:
    rows = await ra.gate_counts(seeded.session)
    assert {r.procedure_id: r.resolved_count for r in rows} == seeded.corpus.gates


async def test_aggregation_is_pushed_to_sql_not_python(seeded: _Seeded) -> None:
    """The statement-capture proof: every primitive aggregates in SQL (GROUP BY),
    returning O(groups) rows — never O(runs). An in-Python `SELECT *`-then-count
    regression would emit no GROUP BY and would fail here."""
    primitives = (
        ra.status_rollup,
        ra.procedure_rollup,
        ra.period_rollup,
        ra.duration_stats,
        ra.benefit_rollup,
        ra.refusal_counts,
        ra.gate_counts,
    )
    for primitive in primitives:
        seeded.statements.clear()
        result = await primitive(seeded.session)
        selects = [s for s in seeded.statements if s.lstrip().upper().startswith("SELECT")]
        assert len(selects) == 1, f"{primitive.__name__} emitted {len(selects)} SELECTs, expected 1"
        assert "GROUP BY" in selects[0].upper(), (
            f"{primitive.__name__} did not push aggregation into SQL (no GROUP BY) — "
            "an O(runs) in-Python count would look like this"
        )
        # O(groups): the corpus has 250 runs; a correct rollup returns far fewer rows.
        assert len(result) < 50, (
            f"{primitive.__name__} returned {len(result)} rows over a 250-run corpus — "
            "that is O(runs), not O(groups)"
        )


async def test_substrate_exposes_no_listing_primitive() -> None:
    """SD-8 (a): the substrate ships aggregate primitives only — no run listing."""
    assert not hasattr(ra, "list_runs_page")
    public = {name for name in vars(ra) if not name.startswith("_")}
    listing_like = {n for n in public if "list" in n.lower() or "page" in n.lower()}
    assert not listing_like, f"unexpected listing-shaped names in the substrate: {listing_like}"


async def test_empty_db_yields_empty_rollups() -> None:
    """No runs -> every primitive returns an empty list, never raises (never-raise)."""
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(eng, expire_on_commit=False)
    try:
        async with maker() as session:
            assert await ra.status_rollup(session) == []
            assert await ra.benefit_rollup(session) == []
            assert await ra.refusal_counts(session) == []
            # a run with no step rows never trips the jsonb lateral
            session.add(
                PipelineRun(
                    run_id="lonely",
                    procedure_id="p",
                    agent_id="a",
                    status="completed",
                    started_at=datetime(2026, 6, 1, tzinfo=UTC),
                    updated_at=datetime(2026, 6, 1, tzinfo=UTC),
                )
            )
            await session.commit()
            assert await ra.benefit_rollup(session) == []
    finally:
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
        await eng.dispose()
