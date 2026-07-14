"""PLAN-0072 — hero-demo real run resolution (beat 3 genuinely resolves the DOA gate).

The offline integration test is the GATE (CLAUDE.md §8). Drives the demo's beat-3
resolution end-to-end over the PRODUCTION auth'd route (SD-A(b)):

    POST /demo/hero/event            (parks a real run at the DOA gate)
    GET  /runs/{run_id}              (read the pending proposals, read-only)
    POST /runs/{run_id}/gate/resolve (Bearer <appr-pm> — the real resolve+resume)

then asserts the GENUINELY-persisted truth (fresh DB read), never a client literal.
Covers AC-1..AC-5. Auth is armed explicitly per test (tests/conftest.py disables it
suite-wide); oct_vertical=procurement so the real spec principals (appr-pm, req-planner)
resolve server-side from the bearer key — identity is never client-chosen.

DB-backed (disposable ``<db>_test``, skips without Postgres); MS-S1-free — the shipped
``advisory_stub_factory`` is deterministic (the governed decision is the rule, not an LLM).
"""

from __future__ import annotations

import hashlib
from collections.abc import AsyncIterator, Callable
from typing import Any

import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from services.api.config import settings
from services.api.main import app
from services.db.audit_log import AuditLog
from services.db.base import Base
from services.db.session import get_session
from services.engine.procedures.persistence import load_run
from services.engine.procedures.runs import PipelineRun, PipelineRunStatus
from tests.db_support import create_test_engine

_GATED_STEP = "approve"
_SOD_CONSTRAINT_ID = "approve+intake"

# Per-test bearer keys (generated in-test; no raw key or digest is committed — CLAUDE.md §8).
_APPR_KEY = "test-key-appr-pm"
_REQ_KEY = "test-key-req-planner"
_APPR_DIGEST = hashlib.sha256(_APPR_KEY.encode("utf-8")).hexdigest()
_REQ_DIGEST = hashlib.sha256(_REQ_KEY.encode("utf-8")).hexdigest()
_APPR_HEADERS = {"Authorization": f"Bearer {_APPR_KEY}"}
_REQ_HEADERS = {"Authorization": f"Bearer {_REQ_KEY}"}


@pytest.fixture
async def hero_engine() -> AsyncIterator[AsyncEngine]:
    """A disposable procurement test engine (never the dev/demo DB)."""
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


@pytest.fixture
def read_session(hero_engine: AsyncEngine) -> Callable[[], AsyncSession]:
    """A sessionmaker to read PERSISTED rows independently of the request session."""
    return async_sessionmaker(hero_engine, expire_on_commit=False)


@pytest.fixture
async def hero_client(
    hero_engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[AsyncClient]:
    """The app bound to the procurement test DB, auth ON, appr-pm + req-planner keys.

    Registers what the API lifespan registers (``discover_and_register`` + the procurement
    executor factory) — the lifespan does not run under ``ASGITransport``. ``oct_vertical`` is
    procurement so ``get_current_principal`` resolves the real authored Persons (appr-pm,
    req-planner) from the bearer key server-side (services/api/auth.py).
    """
    from services.engine.discovery import discover_and_register
    from verticals.procurement.hero_demo.run import register_procurement_procedure_executors

    monkeypatch.setattr(settings, "oct_vertical", "procurement")
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", {_APPR_DIGEST: "appr-pm", _REQ_DIGEST: "req-planner"})

    discover_and_register()
    await register_procurement_procedure_executors()

    maker = async_sessionmaker(hero_engine, expire_on_commit=False)

    async def _override_session() -> AsyncIterator[AsyncSession]:
        async with maker() as session:
            yield session

    app.dependency_overrides[get_session] = _override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


# --------------------------------------------------------------------------- #
# Helpers — drive the real demo/resolve path over HTTP.
# --------------------------------------------------------------------------- #


async def _fire_event(http: AsyncClient) -> str:
    """POST the event opener → the parked run's run_id (Step 3: additive on hero.run_id)."""
    resp = await http.post("/demo/hero/event")
    assert resp.status_code == 200, resp.text
    run_id = resp.json()["hero"]["run_id"]
    assert run_id, "the event opener must expose the parked run_id (AC / Step 3)"
    return run_id


async def _decisions_for(
    http: AsyncClient, run_id: str, decision: str
) -> tuple[str, dict[str, str]]:
    """Read the parked gate's proposals (read-only) and build the decision map."""
    resp = await http.get(f"/runs/{run_id}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    step_id = body["suspended_step"]
    assert step_id == _GATED_STEP
    decisions = {p["action_id"]: decision for p in body["proposals"]}
    assert decisions, "the DOA gate produced no decidable proposals"
    return step_id, decisions


async def _resolve(
    http: AsyncClient, run_id: str, decision: str, headers: dict[str, str] | None
) -> Any:
    step_id, decisions = await _decisions_for(http, run_id, decision)
    return await http.post(
        f"/runs/{run_id}/gate/resolve",
        json={"step_id": step_id, "decisions": decisions},
        headers=headers,
    )


# --------------------------------------------------------------------------- #
# AC-1..AC-5
# --------------------------------------------------------------------------- #


async def test_authenticated_approve_resolves_to_completed(
    hero_client: AsyncClient, read_session: Callable[[], AsyncSession]
) -> None:
    """AC-1 — authenticated appr-pm approves the parked gate → the run genuinely resumes to
    COMPLETED (persisted), and the response reports the real status + resolved run_id."""
    run_id = await _fire_event(hero_client)
    resp = await _resolve(hero_client, run_id, "approve", _APPR_HEADERS)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["run_id"] == run_id
    assert body["run_status"] == PipelineRunStatus.COMPLETED.value

    async with read_session() as s:  # fresh DB read — persisted truth, not the response
        run = await s.get(PipelineRun, run_id)
        assert run is not None and run.status == PipelineRunStatus.COMPLETED.value


async def test_sod_tie_persisted_at_resolution(
    hero_client: AsyncClient, read_session: Callable[[], AsyncSession]
) -> None:
    """AC-2 — the SoD audit-to-control tie is written AT resolution by resolve_gated_step onto
    the persisted approve step's governed_decision (the REAL tie, not the parked preview)."""
    run_id = await _fire_event(hero_client)
    assert (await _resolve(hero_client, run_id, "approve", _APPR_HEADERS)).status_code == 200

    async with read_session() as s:
        loaded = await load_run(s, run_id)
        assert loaded is not None
        approve = next(sr for sr in loaded.step_results if sr.step_id == _GATED_STEP)
        governed = (approve.audit or {}).get("governed_decision", [])
        ties = [d for d in governed if d.get("control_ref", {}).get("kind") == "sod"]
        assert ties, f"no SoD control tie on the resolved gate: {governed}"
        tie = ties[-1]
        assert tie["control_ref"]["id"] == _SOD_CONSTRAINT_ID
        assert tie["principal_id"] == "appr-pm"


async def test_wrong_approver_fails_closed_and_unauthenticated_401(
    hero_client: AsyncClient, read_session: Callable[[], AsyncSession]
) -> None:
    """AC-3 — identity is server-resolved from the bearer key, never client-chosen: an
    UNAUTHENTICATED resolve → 401; the requester (req-planner) approving → SoD violation 403
    with the structured verdict; the run STAYS parked and a gate_refused audit row is written."""
    run_id = await _fire_event(hero_client)
    step_id, decisions = await _decisions_for(hero_client, run_id, "approve")
    payload = {"step_id": step_id, "decisions": decisions}

    unauth = await hero_client.post(f"/runs/{run_id}/gate/resolve", json=payload)
    assert unauth.status_code == 401, unauth.text

    wrong = await hero_client.post(
        f"/runs/{run_id}/gate/resolve", json=payload, headers=_REQ_HEADERS
    )
    assert wrong.status_code == 403, wrong.text
    assert "verdict" in wrong.json()["detail"]

    async with read_session() as s:
        run = await s.get(PipelineRun, run_id)
        assert run is not None and run.status == PipelineRunStatus.WAITING_HUMAN.value
        refused = await s.execute(
            sa.select(AuditLog).where(AuditLog.action == "gate_refused", AuditLog.run_id == run_id)
        )
        assert list(refused.scalars().all()), "the SoD refusal must be durably audited"


async def test_authenticated_reject_records_and_completes_with_no_effect(
    hero_client: AsyncClient, read_session: Callable[[], AsyncSession]
) -> None:
    """AC-4 — reject = continue + record (shipped semantics, NOT a rejected terminal): the
    handler never fires (empty output_set), action_rejected lands on the trace, and the run
    resumes to COMPLETED with no executed effect. This arm ALSO answers OQ-4 (whether the demo
    procedure's downstream steps tolerate an empty executed-effect set)."""
    run_id = await _fire_event(hero_client)
    resp = await _resolve(hero_client, run_id, "reject", _APPR_HEADERS)
    assert resp.status_code == 200, resp.text
    assert resp.json()["run_status"] == PipelineRunStatus.COMPLETED.value

    async with read_session() as s:
        loaded = await load_run(s, run_id)
        assert loaded is not None
        approve = next(sr for sr in loaded.step_results if sr.step_id == _GATED_STEP)
        assert (approve.artifact or {}).get("output_set") == []  # nothing executed
        trace = approve.reasoning_trace or []
        assert any(t.get("kind") == "action_rejected" for t in trace), trace
        run = await s.get(PipelineRun, run_id)
        assert run is not None and run.status == PipelineRunStatus.COMPLETED.value


async def test_event_run_source_trace_carries_economic_facet(
    hero_client: AsyncClient, read_session: Callable[[], AsyncSession]
) -> None:
    """PLAN-0073 AC-2 (SD-1a) — fire-for-real: the event-fired governed run genuinely carries the
    advisory ``economic_impact`` facet on the PERSISTED ``source`` action's reasoning trace (it
    rides the real hero run, not a render-side fabrication). The facet reaches the action step
    because the enriched intake seed threads ``event_type`` through intake → judge → source."""
    run_id = await _fire_event(hero_client)
    async with read_session() as s:
        loaded = await load_run(s, run_id)
        assert loaded is not None
        # The governed `source` step is GovernanceActionExecutor._scored_rule: it REPLACES the base
        # action envelopes with enriched entities and lifts the advisory economic_impact facet onto
        # the STEP reasoning trace (PLAN-0073 SD-1a), where it durably persists.
        source = next(sr for sr in loaded.step_results if sr.step_id == "source")
        kinds = [t.get("kind") for t in (source.reasoning_trace or [])]
        assert "economic_impact" in kinds, kinds
        econ = next(t for t in source.reasoning_trace if t.get("kind") == "economic_impact")
        assert econ["detail"]["kind"] == "expedite_tradeoff"
        assert econ["detail"]["provisional"] is True


async def test_replay_refires_a_fresh_run_after_a_decision(
    hero_client: AsyncClient, read_session: Callable[[], AsyncSession]
) -> None:
    """AC-5 (SD-C) — replay is generation-aware: while a run is parked a repeat POST returns the
    SAME parked run; after a decision (approve OR reject → both COMPLETED) a repeat POST returns
    a FRESH parked run (new run_id), and the decided run is retained as audit history."""
    first = await _fire_event(hero_client)
    # While parked, a repeat returns the SAME parked run (today's ALREADY_FIRED behavior).
    assert await _fire_event(hero_client) == first

    assert (await _resolve(hero_client, first, "approve", _APPR_HEADERS)).status_code == 200

    second = await _fire_event(hero_client)
    assert second != first, "after a decision, replay must fire a FRESH parked run"

    async with read_session() as s:
        first_run = await s.get(PipelineRun, first)
        second_run = await s.get(PipelineRun, second)
        assert first_run is not None and first_run.status == PipelineRunStatus.COMPLETED.value
        assert second_run is not None and second_run.status == PipelineRunStatus.WAITING_HUMAN.value
