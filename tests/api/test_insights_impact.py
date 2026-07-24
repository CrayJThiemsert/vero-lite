"""AC-4 — ``GET /insights/impact``, the A2 ฿ ROI rollup (PLAN-0088 Step 2).

Seeds the AC-2 corpus factory into the disposable ``<db>_test`` and asserts the
endpoint reports exactly what the factory computed independently, with the two
structural properties the ADR-0030 / S7 disciplines demand:

* per-currency sums only, with **no** cross-currency total representable, and
* a malformed ฿ figure is skipped and *counted*, never raised.

Skips gracefully when Postgres is unreachable.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from decimal import Decimal

import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.config import settings
from services.api.main import app
from services.api.models.insights import ImpactReport
from services.db.base import Base
from services.db.session import get_session
from tests.db_support import create_test_engine
from tests.support.run_corpus_factory import Corpus, build_corpus

_SEED = 99
_N_RUNS = 60


@dataclass
class _Client:
    http: AsyncClient
    corpus: Corpus


@pytest.fixture
async def insights_client() -> AsyncIterator[_Client]:
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


async def test_impact_report_shape_and_vertical_stamp(insights_client: _Client) -> None:
    resp = await insights_client.http.get("/insights/impact")
    assert resp.status_code == 200
    body = resp.json()
    assert body["provisional"] is True
    assert body["vertical"] == settings.oct_vertical  # S7 deployment stamp
    assert body["buckets"], "the seeded corpus carries ฿ facets"
    assert body["narrative"]
    # The response validates against the declared model (no extra/missing fields).
    ImpactReport.model_validate(body)


async def test_buckets_match_the_corpus_exactly(insights_client: _Client) -> None:
    """AC-4 grouping: currency x procedure x facet kind x day, exact figures."""
    body = (await insights_client.http.get("/insights/impact")).json()
    got = {
        (b["currency"], b["procedure_id"], b["facet_kind"], b["period"]): b for b in body["buckets"]
    }
    assert set(got) == set(insights_client.corpus.benefit)
    for key, expected in insights_client.corpus.benefit.items():
        bucket = got[key]
        assert bucket["run_count"] == len(expected["run_ids"])
        assert bucket["facet_count"] == expected["facet_count"]
        assert bucket["figures_missing"] == expected["facet_count"] - expected["valued"]
        assert Decimal(str(bucket["net_benefit_sum"])) == Decimal(expected["sum"])


async def test_currencies_land_in_separate_buckets_with_no_combined_total(
    insights_client: _Client,
) -> None:
    """S7: the wrong sum is unrepresentable, not merely discouraged."""
    body = (await insights_client.http.get("/insights/impact")).json()
    currencies = {b["currency"] for b in body["buckets"]}
    assert {"THB", "USD"} <= currencies, "the corpus seeds a non-THB sub-subset"
    # Each bucket is single-currency by construction, and the REPORT carries no
    # cross-currency total field at all.
    assert not [k for k in body if "total" in k and k != "figures_missing_total"]
    assert "net_benefit_total" not in body
    assert "net_benefit_sum" not in body  # sums live only inside a currency bucket


async def test_malformed_figure_is_counted_never_raised(insights_client: _Client) -> None:
    """ADR-0030 never-raise: an unreadable ฿ figure is disclosed, not fatal."""
    resp = await insights_client.http.get("/insights/impact")
    assert resp.status_code == 200
    body = resp.json()
    expected_missing = sum(
        b["facet_count"] - b["valued"] for b in insights_client.corpus.benefit.values()
    )
    assert expected_missing > 0, "the corpus must seed malformed facets for this to mean anything"
    assert body["figures_missing_total"] == expected_missing


async def test_assumptions_are_the_disclosed_union(insights_client: _Client) -> None:
    """ADR-0030 D3: an aggregate discloses no less than its parts."""
    body = (await insights_client.http.get("/insights/impact")).json()
    assert body["assumptions"] == insights_client.corpus.assumptions
    assert body["assumptions"], "the corpus must actually carry assumptions"


async def test_empty_corpus_reports_cleanly() -> None:
    """No ฿ facets anywhere -> an empty, still-well-formed provisional report."""
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
            body = (await http.get("/insights/impact")).json()
        assert body["buckets"] == []
        assert body["figures_missing_total"] == 0
        assert body["provisional"] is True
        assert body["narrative"]
    finally:
        app.dependency_overrides.clear()
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
        await eng.dispose()
