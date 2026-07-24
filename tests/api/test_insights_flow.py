"""AC-6 — ``GET /insights/flow``, the A3 bottleneck / cycle-time report (PLAN-0088 Step 3).

Asserts the endpoint against the AC-2 corpus factory's independently-computed
expectations, and pins the two things that are easy to get quietly wrong:

* **spans are clamped at >= 0** — this box's wall clock steps backwards, and the
  corpus seeds a backward-clock subset intersected with ``waiting_human`` so the
  clamp is exercised rather than assumed; and
* **the backward rows are COUNTED, not swallowed** — ``negative_clock_spans`` is
  asserted non-zero, so a regression that silently dropped the anomaly (or averaged
  it in) fails here.

Skips gracefully when Postgres is unreachable.
"""

from __future__ import annotations

import statistics
from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.config import settings
from services.api.main import app
from services.api.models.insights import FlowReport
from services.db.base import Base
from services.db.session import get_session
from tests.db_support import create_test_engine
from tests.support.run_corpus_factory import Corpus, build_corpus

_SEED = 4242
_N_RUNS = 120


@dataclass
class _Client:
    http: AsyncClient
    corpus: Corpus


@pytest.fixture
async def flow_client() -> AsyncIterator[_Client]:
    corpus = build_corpus(seed=_SEED, n_runs=_N_RUNS)
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(eng, expire_on_commit=False)
    async with maker() as seed_session:
        seed_session.add_all(corpus.rows)
        await seed_session.commit()

    async def _override_session() -> AsyncIterator[AsyncSession]:
        async with maker() as session:
            yield session

    app.dependency_overrides[get_session] = _override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield _Client(http=http, corpus=corpus)
    app.dependency_overrides.clear()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


async def test_flow_report_shape_and_vertical_stamp(flow_client: _Client) -> None:
    resp = await flow_client.http.get("/insights/flow")
    assert resp.status_code == 200
    body = resp.json()
    assert body["vertical"] == settings.oct_vertical
    assert body["steps"] and body["dwell"]
    FlowReport.model_validate(body)


async def test_step_latency_matches_the_corpus_exactly(flow_client: _Client) -> None:
    body = (await flow_client.http.get("/insights/flow")).json()
    got = {(s["procedure_id"], s["step_id"]): s for s in body["steps"]}
    assert set(got) == set(flow_client.corpus.durations)
    for key, samples in flow_client.corpus.durations.items():
        step = got[key]
        assert step["sample_count"] == len(samples)
        assert step["max_ms"] == max(samples)
        assert step["avg_ms"] == pytest.approx(statistics.mean(samples))


async def test_steps_are_ordered_slowest_first(flow_client: _Client) -> None:
    """A bottleneck report that makes the reader sort it has not reported the bottleneck."""
    body = (await flow_client.http.get("/insights/flow")).json()
    maxima = [s["max_ms"] for s in body["steps"]]
    assert maxima == sorted(maxima, reverse=True)


async def test_dwell_matches_the_corpus_exactly(flow_client: _Client) -> None:
    body = (await flow_client.http.get("/insights/flow")).json()
    got = {d["procedure_id"]: d for d in body["dwell"]}
    assert set(got) == set(flow_client.corpus.dwell)
    for procedure_id, expected in flow_client.corpus.dwell.items():
        bucket = got[procedure_id]
        assert bucket["run_count"] == expected["run_count"]
        assert bucket["negative_clock_spans"] == expected["negatives"]
        assert bucket["max_span_seconds"] == pytest.approx(max(expected["spans"]))
        assert bucket["avg_span_seconds"] == pytest.approx(statistics.mean(expected["spans"]))


async def test_backward_clock_spans_are_clamped_and_counted(flow_client: _Client) -> None:
    """The anomaly is surfaced, never silently absorbed (S4 / AC-6).

    **Which assertion actually holds the clamp — measured, not assumed.** A mutation
    run that deleted the ``GREATEST(span, 0)`` from ``waiting_dwell_stats`` reddened
    ``test_dwell_matches_the_corpus_exactly`` (avg 249.67 against an expected 250.0)
    and left THIS test green: a handful of -2 s rows among many +300 s ones keeps the
    mean positive, so the ``>= 0`` assertions below are a cheap sanity floor, **not**
    the guard. The exact-value comparison against the corpus is the guard. Kept here
    anyway because it is the one assertion that still fires if a bucket ever goes
    wholly negative — but do not mistake it for the load-bearing one.
    """
    body = (await flow_client.http.get("/insights/flow")).json()
    expected_negatives = sum(d["negatives"] for d in flow_client.corpus.dwell.values())
    assert (
        expected_negatives > 0
    ), "the corpus must seed backward-clock waiting_human runs, or this test proves nothing"
    # The counting half IS decisive here: break the counter and this line fails.
    assert body["negative_clock_spans"] == expected_negatives
    assert all(d["avg_span_seconds"] >= 0 for d in body["dwell"])
    assert all(d["max_span_seconds"] >= 0 for d in body["dwell"])


async def test_dwell_covers_only_waiting_human_runs(flow_client: _Client) -> None:
    """Scope check: the spans describe suspended runs, not every run."""
    body = (await flow_client.http.get("/insights/flow")).json()
    reported = sum(d["run_count"] for d in body["dwell"])
    waiting = flow_client.corpus.status_counts["waiting_human"]
    assert reported == waiting
    assert reported < flow_client.corpus.run_count, "not every run is suspended"


async def test_empty_corpus_reports_cleanly() -> None:
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(eng, expire_on_commit=False)

    async def _override_session() -> AsyncIterator[AsyncSession]:
        async with maker() as session:
            yield session

    app.dependency_overrides[get_session] = _override_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as http:
            body = (await http.get("/insights/flow")).json()
        assert body["steps"] == []
        assert body["dwell"] == []
        assert body["negative_clock_spans"] == 0
    finally:
        app.dependency_overrides.clear()
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
        await eng.dispose()
