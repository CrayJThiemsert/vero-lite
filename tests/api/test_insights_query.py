"""AC-9 — ``POST /insights/query``, the A1 endpoint (PLAN-0088 Step 5).

Exercises translate -> validate -> execute -> phrase end to end **offline**, with
a schema-shaped stub translator and a stub phraser substituted at the module
seams. The stubs stand in for the AC-9b host-state stage; nothing here contacts
MS-S1 or any model.

The load-bearing assertion is not that the happy path answers — it is that the
three refusals stay honest, and in particular that **the phrase stage is never
invoked on an empty result**. The stub phraser records whether it ran, so a
regression that started describing zero matches would fail here rather than ship
a fluent sentence about nothing.

Skips gracefully when Postgres is unreachable.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field

import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.main import app
from services.api.models.insights import RunQueryAnswer
from services.db.base import Base
from services.db.session import get_session
from services.engine.llm.client import OllamaError
from services.engine.nl_query import QueryFilter, StructuredQuery
from tests.db_support import create_test_engine
from tests.support.run_corpus_factory import Corpus, build_corpus

_SEED = 313
_N_RUNS = 120
_ROUTER = "services.api.routers.insights"


@dataclass
class _Phraser:
    """Stub phrase stage that remembers whether it was called."""

    calls: list[str] = field(default_factory=list)

    async def __call__(self, question: str, query: StructuredQuery, result: object) -> str:
        self.calls.append(question)
        return f"stub answer for: {question}"


@dataclass
class _Client:
    http: AsyncClient
    corpus: Corpus
    phraser: _Phraser


@pytest.fixture
async def query_client(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[_Client]:
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

    phraser = _Phraser()
    monkeypatch.setattr(f"{_ROUTER}.phrase_run_answer", phraser)
    app.dependency_overrides[get_session] = _override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield _Client(http=http, corpus=corpus, phraser=phraser)
    app.dependency_overrides.clear()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


def _stub_translator(query: StructuredQuery) -> object:
    async def _translate(question: str) -> StructuredQuery:
        return query

    return _translate


async def test_end_to_end_count_is_grounded_in_the_corpus(
    query_client: _Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        f"{_ROUTER}.translate_run_question",
        _stub_translator(StructuredQuery(object_type="pipeline_run", operation="count")),
    )
    resp = await query_client.http.post("/insights/query", json={"question": "how many runs?"})
    assert resp.status_code == 200
    body = resp.json()
    RunQueryAnswer.model_validate(body)
    assert body["grounded"] is True
    assert body["matched"] == query_client.corpus.run_count
    # The grounding receipt travels with the answer.
    assert body["structured_query"]["object_type"] == "pipeline_run"
    assert query_client.phraser.calls == ["how many runs?"]


async def test_query_the_corpus_cannot_serve_returns_retry_shaped_errors(
    query_client: _Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SD-8 (a): no listing shape exists, and the refusal must be correctable."""
    monkeypatch.setattr(
        f"{_ROUTER}.translate_run_question",
        _stub_translator(StructuredQuery(object_type="pipeline_run", operation="list")),
    )
    body = (
        await query_client.http.post("/insights/query", json={"question": "list the runs"})
    ).json()
    assert body["grounded"] is False
    assert body["matched"] == 0
    assert body["validation_errors"]
    assert "count" in " ".join(body["validation_errors"])
    assert query_client.phraser.calls == [], "phrase must not run on a rejected query"


async def test_empty_result_short_circuits_without_invoking_the_phrase_stage(
    query_client: _Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The property AC-8 (iii) names, observed at the endpoint.

    A model asked to describe zero matches is exactly how a fabricated figure
    gets in, so the phrase stage is not merely unnecessary here — it is unsafe.
    """
    monkeypatch.setattr(
        f"{_ROUTER}.translate_run_question",
        _stub_translator(
            StructuredQuery(
                object_type="pipeline_run",
                operation="count",
                filters=[QueryFilter(property="procedure_id", op="eq", value="no-such-procedure")],
            )
        ),
    )
    body = (
        await query_client.http.post("/insights/query", json={"question": "runs of nothing?"})
    ).json()
    assert body["grounded"] is False
    assert body["matched"] == 0
    assert body["validation_errors"] == []
    assert query_client.phraser.calls == [], "phrase must not run on an empty result"


async def test_untranslatable_question_is_ungrounded_with_no_query(
    query_client: _Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unreachable model degrades to an honest ungrounded answer, never a 500.

    The failure is injected at the CHAT CLIENT, so the real translate stage runs —
    prompt, schema, retry loop and all — and the assertion is about how the handler
    treats its failure. ``OllamaError`` subclasses ``RuntimeError``, which is what
    the handler catches.

    _[Rewritten in the AC-9b build. The original installed no stub at all and
    relied on the seam being **unwired** (``NotImplementedError``), which made it a
    LIVE call the moment the seam was implemented — it ran ``gpt-oss:20b`` on MS-S1
    twice before that was noticed. A test whose premise is "the feature does not
    exist yet" expires silently the day it does. The `_no_live_model` conftest guard
    now makes that class of accident impossible; this test states its own
    precondition instead of inheriting one.]_
    """

    class _DeadClient:
        async def chat(self, *_args: object, **_kwargs: object) -> object:
            raise OllamaError("MS-S1 unreachable (injected)")

    monkeypatch.setattr(f"{_ROUTER}.nl_query._build_chat_client", lambda: _DeadClient())
    resp = await query_client.http.post("/insights/query", json={"question": "anything"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["grounded"] is False
    assert body["structured_query"] is None
    assert query_client.phraser.calls == []
