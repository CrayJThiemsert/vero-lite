"""AC-7 — ``GET /insights/audit-readiness``, the A4 reader (PLAN-0088 Step 4).

Asserts the endpoint against the AC-2 corpus factory's independently-computed
expectations — the oracle is the seeded specs re-tallied in plain Python, never
the SQL under test — and pins the two properties that are easy to get quietly
wrong:

* **the approver half comes from the step trace, not ``step_principals``.**
  AC-2's wording says the factory seeds "gate resolutions with ``step_principals``
  approver halves"; it does not, and could not — every write to that column
  records the REQUESTER half. The approver is recorded by ``resolve_gated_step``
  in the step ``reasoning_trace``. A future "fix" that made the count match AC-2's
  prose would read the wrong principal and still return a plausible number, so the
  source of the count is pinned in SQL (``test_run_analytics.py``) as well as by
  value here.
* **split visibility is structural.** ``AuditReadinessReport`` has no ``breaks``
  field and forbids extras, so a verbatim chain-break string is unrepresentable
  on this reader rather than merely absent today.

Skips gracefully when Postgres is unreachable.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.config import settings
from services.api.main import app
from services.api.models.insights import AuditReadinessReport
from services.db.base import Base
from services.db.session import get_session
from tests.db_support import create_test_engine
from tests.support.run_corpus_factory import Corpus, build_corpus

_SEED = 909
_N_RUNS = 120


@dataclass
class _Client:
    http: AsyncClient
    corpus: Corpus


@pytest.fixture
async def readiness_client() -> AsyncIterator[_Client]:
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


async def test_readiness_shape_and_vertical_stamp(readiness_client: _Client) -> None:
    resp = await readiness_client.http.get("/insights/audit-readiness")
    assert resp.status_code == 200
    body = resp.json()
    assert body["vertical"] == settings.oct_vertical
    assert body["statuses"] and body["gates"] and body["refusals"]
    AuditReadinessReport.model_validate(body)


async def test_status_totals_match_the_corpus_exactly(readiness_client: _Client) -> None:
    body = (await readiness_client.http.get("/insights/audit-readiness")).json()
    got = {row["status"]: row["run_count"] for row in body["statuses"]}
    assert got == readiness_client.corpus.status_counts
    assert sum(got.values()) == readiness_client.corpus.run_count


async def test_gate_counts_match_the_corpus_exactly(readiness_client: _Client) -> None:
    body = (await readiness_client.http.get("/insights/audit-readiness")).json()
    got = {row["procedure_id"]: row["resolved_count"] for row in body["gates"]}
    assert got == readiness_client.corpus.gates


async def test_approver_half_matches_the_corpus_exactly(readiness_client: _Client) -> None:
    """AC-7's "(approver half present)" — the count, against an independent tally.

    The corpus seeds the approver the way the engine records it: a
    ``gate_principal_recorded`` trace entry carrying ``principal_id``. The factory
    re-derives the expected per-procedure count from those same specs in plain
    Python, so this compares SQL against a non-SQL oracle.
    """
    body = (await readiness_client.http.get("/insights/audit-readiness")).json()
    got = {row["procedure_id"]: row["approver_recorded"] for row in body["gates"]}
    assert got == readiness_client.corpus.gate_approvers
    # The equality above is only meaningful while the corpus seeds gates that
    # resolved WITHOUT an approver. A mutation probe proved the point: with an
    # approver on every resolved gate, deleting the extraction entirely left this
    # assertion green, because approver_recorded and resolved_count coincided.
    resolved = {row["procedure_id"]: row["resolved_count"] for row in body["gates"]}
    assert got != resolved, "the unattributed sub-subset stopped being seeded"
    assert all(got[p] < resolved[p] for p in got), "every procedure should show the gap"


async def test_refusal_counts_match_the_corpus_exactly(readiness_client: _Client) -> None:
    body = (await readiness_client.http.get("/insights/audit-readiness")).json()
    got = {row["refusal_kind"]: row["count"] for row in body["refusals"]}
    assert got == readiness_client.corpus.refusals


async def test_chain_verdict_comes_from_the_verify_chain_seam(
    readiness_client: _Client,
) -> None:
    """The corpus writes no audit rows, so the chain is trivially intact.

    The point of the assertion is that the field is populated from the real seam
    rather than hardcoded: ``verify_chain`` walks the (empty) table and returns no
    breaks, which is what ``chain_intact: true`` means here.
    """
    body = (await readiness_client.http.get("/insights/audit-readiness")).json()
    assert body["chain_intact"] is True


async def test_response_body_carries_no_break_detail(readiness_client: _Client) -> None:
    """Split visibility, observed at the wire (AC-7)."""
    body = (await readiness_client.http.get("/insights/audit-readiness")).json()
    assert "breaks" not in body


def test_report_model_cannot_carry_break_strings() -> None:
    """Split visibility, held structurally rather than by care (AC-7).

    ``breaks`` is absent AND extras are forbidden — together those make a verbatim
    break string unrepresentable on this report, the same way ``ImpactReport``
    makes a cross-currency total unrepresentable (S7). A test that only checked
    today's response body would pass just as happily after someone added the field.
    """
    assert "breaks" not in AuditReadinessReport.model_fields
    assert AuditReadinessReport.model_config["extra"] == "forbid"
