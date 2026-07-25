"""AC-9b — the ONE live translate+phrase run against local MS-S1 (host-state).

**Not a CI gate. Evidence, not a check** (PLAN-0088 §Verification). It is opted
into TWICE and runs under neither condition by accident:

* ``VERO_LIVE_MS_S1=1`` in the environment — absent, the test skips, so a plain
  ``pytest tests/`` (CI or local) never reaches the network;
* ``@pytest.mark.host_state`` — which releases the ``_no_outbound_network``
  conftest guard for this test alone.

Running it is a **host-state action** and needs explicit Cray approval every
time (CLAUDE.md §8). The marker is not that approval; it only makes the run
possible once approval exists.

    VERO_LIVE_MS_S1=1 pytest tests/api/test_insights_query_live.py -s

Local model only. Run records carry ``person_id`` (PII / PDPA), so the remote
Anthropic API is never used on run data — and by construction it cannot be: the
offline suite proves neither prompt is ever handed a run record
(``test_no_run_record_reaches_either_prompt``).

**The pass/fail read is fixed here, before the run**, so a live result cannot be
graded after the fact into whatever it happened to produce:

* **PASS** — the translate stage returns a query passing ``validate_run_query``
  without exhausting its retry budget; execution matches > 0 runs; the phrased
  answer contains the exact figure the executor computed; ``grounded`` is true.
* **FAIL** — any figure in the answer the executor did not produce, or
  ``grounded`` true on a zero match.
* **INSUFFICIENT-EVIDENCE** — MS-S1 unreachable or the model absent. That is a
  skip, never a pass.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.main import app
from services.api.models.insights import RunQueryAnswer
from services.db.base import Base
from services.db.session import get_session
from tests.db_support import create_test_engine
from tests.support.run_corpus_factory import Corpus, build_corpus

pytestmark = [
    pytest.mark.host_state,
    pytest.mark.skipif(
        os.environ.get("VERO_LIVE_MS_S1") != "1",
        reason="host-state: set VERO_LIVE_MS_S1=1 and get Cray's go (CLAUDE.md §8)",
    ),
]

_SEED = 909
_N_RUNS = 120


@dataclass
class _Live:
    http: AsyncClient
    corpus: Corpus


@pytest.fixture
async def live_client() -> AsyncIterator[_Live]:
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
    async with AsyncClient(transport=transport, base_url="http://test", timeout=180.0) as http:
        yield _Live(http=http, corpus=corpus)
    app.dependency_overrides.clear()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


async def test_live_translate_and_phrase_over_the_run_corpus(live_client: _Live) -> None:
    """One live run: a plain question in, a grounded sentence out.

    The question is deliberately ordinary and does not name a property, an
    operation or a filter value — a question phrased in the schema's own
    vocabulary would test the prompt's echo, not its translation.
    """
    question = "How many governed runs have we recorded so far?"
    resp = await live_client.http.post("/insights/query", json={"question": question})
    assert resp.status_code == 200
    body = resp.json()
    answer = RunQueryAnswer.model_validate(body)

    print("\n--- AC-9b live evidence (MS-S1, gpt-oss:20b) ---")
    print(f"question:         {question}")
    print(f"structured_query: {answer.structured_query}")
    print(f"matched:          {answer.matched}")
    print(f"grounded:         {answer.grounded}")
    print(f"answer:           {answer.answer}")
    print("--- end evidence ---")

    # PASS criteria, exactly as fixed in the module docstring.
    assert answer.structured_query is not None, "translate produced no query"
    assert answer.structured_query["object_type"] == "pipeline_run"
    assert answer.validation_errors in (None, []), answer.validation_errors
    assert answer.matched > 0, "the corpus is seeded; a zero match means the query missed"
    assert answer.grounded is True
    assert answer.matched == live_client.corpus.run_count, (
        "an unfiltered count must equal the seeded corpus size — the executor's figure, "
        "not the model's"
    )
    # The grounding assertion: the model must report the executor's number.
    assert str(answer.matched) in answer.answer, (
        f"the phrased answer does not contain the computed figure {answer.matched}: "
        f"{answer.answer!r}"
    )
