"""PLAN-0047 Step 2 tests (AC-2 / AC-3) — run → suspend → resolve → resume over HTTP only.

Drives the energy ``substation_health_sweep`` (query → evaluate → gated
restart) end-to-end through the two new endpoints with stub executors
registered via ``registry.register_procedure_executors`` — no library
shortcut touches the run. AC-2: a spoofed ``triggered_by`` in the body is
OVERWRITTEN by the server-resolved identity on the persisted run.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import pytest
import sqlalchemy as sa
from httpx import AsyncClient

import services.api.auth as auth_module
from services.api.config import settings
from services.engine.llm.client import ChatResult
from services.engine.procedures.action_step import ActionStepExecutor
from services.engine.procedures.orchestrator import RunContext, StepExecutor, StepOutcome
from services.engine.procedures.spec import Person, Step, StepKind
from services.engine.registry import registry
from tests.db_support import create_test_engine

RAW_KEY = "test-key-op-somchai"
DIGEST = hashlib.sha256(RAW_KEY.encode("utf-8")).hexdigest()
HEADERS = {"Authorization": f"Bearer {RAW_KEY}"}

_PROCEDURE_ID = "substation_health_sweep"
_GATED_STEP = "restart_breaches"


@pytest.fixture
def runs_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    """Authn ON with one provisioned key → the 'op-somchai' Person.

    ADR-016 S2 RF-1 (PLAN-0053): resolving a gated step requires an *identified
    Person* approver — not merely an accountable ``person_id`` string — so the
    approver is provisioned here as a real ``Person`` (energy's gated
    ``restart_breaches`` carries no SoD constraint, so any role satisfies it).
    The ``_principal_index`` seam is monkeypatched (mirroring test_api_auth.py)
    rather than authoring a principal into the production energy vertical, which
    would arm vertical-wide membership enforcement — the OQ-6 N≥2 boundary the
    ``get_current_principal`` ``if index:`` branch guards (services/api/auth.py)."""
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", {DIGEST: "op-somchai"})
    approver = Person(
        person_id="op-somchai", name="Somchai (operator)", roles=frozenset({"operator"})
    )
    monkeypatch.setattr(auth_module, "_principal_index", lambda vertical: {"op-somchai": approver})


class _FakeChat:
    """Replays canned ChatResults (call-1 draft + call-2 judgment per entity)."""

    def __init__(self, results: list[ChatResult]) -> None:
        self._results = list(results)

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        return self._results.pop(0)


def _judgment_json() -> str:
    return json.dumps(
        {
            "title": "Restart asset a1 after over-temperature",
            "description": "Reading 95.0 exceeds the 90 ceiling.",
            "rationale": "Sustained over-temperature risks damage; restart.",
            "confidence": 0.9,
            "affected_entities": [{"object_type": "Asset", "primary_key": "a1"}],
            "suggested_handler": "restart",
            "handler_payload": {"asset_id": "a1"},
        }
    )


def _chat_results(entities: int) -> list[ChatResult]:
    out: list[ChatResult] = []
    for _ in range(entities):
        out.append(ChatResult(content="draft", thinking="t", model="gpt-oss:20b", raw={}))
        out.append(ChatResult(content=_judgment_json(), thinking=None, model="gpt-oss:20b", raw={}))
    return out


class _Query:
    """Fixed-output query executor — one over-threshold asset reading."""

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        return StepOutcome(
            output=[{"asset_id": "a1", "measured_value": 95.0}],
            reasoning_trace=[{"kind": "query", "summary": "read latest readings"}],
        )


class _Judge:
    """Deterministic evaluate executor — tags verdict vs the 90 ceiling."""

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        tagged = [
            {**entity, "verdict": "breach" if entity["measured_value"] >= 90 else "ok"}
            for entity in input_set
        ]
        return StepOutcome(
            output=tagged, reasoning_trace=[{"kind": "evaluate", "summary": "judged vs ceiling"}]
        )


def _register_energy_executors() -> None:
    def factory() -> dict[StepKind, StepExecutor]:
        return {
            StepKind.QUERY: _Query(),
            StepKind.EVALUATE: _Judge(),
            StepKind.ACTION: ActionStepExecutor(
                client_factory=lambda _model: _FakeChat(_chat_results(1))
            ),
        }

    registry.register_procedure_executors("energy", factory)


@pytest.fixture
async def wired_client(client_with_db: AsyncClient) -> AsyncClient:
    """The DB-backed client with energy's stub executor factory registered."""
    _register_energy_executors()
    return client_with_db


async def test_run_requires_auth(wired_client: AsyncClient, runs_auth: None) -> None:
    response = await wired_client.post(f"/procedures/{_PROCEDURE_ID}/run", json={})
    assert response.status_code == 401


async def test_http_only_run_suspend_resolve_resume(
    wired_client: AsyncClient, runs_auth: None
) -> None:
    """AC-3: the full loop over HTTP only — and AC-2 on the persisted record."""
    run_response = await wired_client.post(
        f"/procedures/{_PROCEDURE_ID}/run",
        json={"trigger_context": {"source": "test", "triggered_by": "spoofed-person"}},
        headers=HEADERS,
    )
    assert run_response.status_code == 200
    body = run_response.json()
    assert body["status"] == "waiting_human"
    assert body["suspended_step"] == _GATED_STEP
    assert body["triggered_by"] == "op-somchai"
    assert len(body["proposals"]) == 1
    run_id = body["run_id"]
    action_id = body["proposals"][0]["action_id"]

    # AC-2: the persisted run carries the SERVER-resolved identity — the
    # spoofed body value is overwritten, the caller-legitimate key survives.
    eng = await create_test_engine()
    try:
        async with eng.connect() as conn:
            trigger_context = (
                await conn.execute(
                    sa.text("SELECT trigger_context FROM pipeline_runs WHERE run_id = :run_id"),
                    {"run_id": run_id},
                )
            ).scalar_one()
    finally:
        await eng.dispose()
    assert trigger_context["triggered_by"] == "op-somchai"
    assert trigger_context["source"] == "test"

    resolve_response = await wired_client.post(
        f"/runs/{run_id}/gate/resolve",
        json={"step_id": _GATED_STEP, "decisions": {action_id: "approve"}},
        headers=HEADERS,
    )
    assert resolve_response.status_code == 200
    resolved = resolve_response.json()
    assert resolved["run_status"] == "completed"
    assert resolved["suspended_step"] is None
    assert {s["status"] for s in resolved["steps"]} == {"complete"}

    # Replay visibility pre-Step-3: a second resolve on the settled gate is a
    # clean conflict, not a silent re-execution.
    replay = await wired_client.post(
        f"/runs/{run_id}/gate/resolve",
        json={"step_id": _GATED_STEP, "decisions": {action_id: "approve"}},
        headers=HEADERS,
    )
    assert replay.status_code == 409


async def test_run_unknown_procedure_is_404(wired_client: AsyncClient, runs_auth: None) -> None:
    response = await wired_client.post(
        "/procedures/no-such-procedure/run", json={}, headers=HEADERS
    )
    assert response.status_code == 404


async def test_resolve_unknown_run_is_404(wired_client: AsyncClient, runs_auth: None) -> None:
    response = await wired_client.post(
        "/runs/run-nonexistent/gate/resolve",
        json={"step_id": _GATED_STEP, "decisions": {}},
        headers=HEADERS,
    )
    assert response.status_code == 404


async def test_unwired_vertical_is_409(client: AsyncClient, runs_auth: None) -> None:
    """A vertical with no registered executor factory refuses the run cleanly."""
    response = await client.post(f"/procedures/{_PROCEDURE_ID}/run", json={}, headers=HEADERS)
    assert response.status_code == 409
    assert "executor factory" in response.json()["detail"]


# --- PLAN-0053 Phase A: ADR-016 S2 RF-1 (broad gate-approver) + actor_kind ------


async def test_resolve_rejects_when_no_authenticated_approver(
    wired_client: AsyncClient, runs_auth: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-1 (ADR-016 S2 RF-1): with ``api_auth_enabled`` off there is NO
    accountable human approver, so gate-resolve fails closed (403) BEFORE any
    decision is applied — INDEPENDENT of the authn toggle. This closes the
    amendment's motivating hole: an authn-off resolve silently applying decisions
    with no human. The gate is left intact (``waiting_human``), retryable once a
    human authenticates.

    **Arrangement changed by PLAN-0112 AC-1**, which closed the run endpoint's own
    RF-1 hole: a parked run can no longer be minted with authn off, so the run is
    fired by a real keyed principal and authn is revoked only for the ACT. That is
    also the truthful shape — a run parked by a legitimate actor, then an
    unauthenticated caller trying to resolve it. Note what must NOT be done instead:
    leaving authn ON and omitting the header yields a **401 from the dependency**,
    which never reaches this 403 and would silently retire the RF-1 coverage."""
    run_response = await wired_client.post(
        f"/procedures/{_PROCEDURE_ID}/run", json={}, headers=HEADERS
    )
    assert run_response.status_code == 200
    body = run_response.json()
    assert body["status"] == "waiting_human"
    run_id = body["run_id"]
    action_id = body["proposals"][0]["action_id"]

    # ACT with no accountable human — the condition this test exists to cover.
    monkeypatch.setattr(settings, "api_auth_enabled", False)
    resolve_response = await wired_client.post(
        f"/runs/{run_id}/gate/resolve",
        json={"step_id": _GATED_STEP, "decisions": {action_id: "approve"}},
    )
    assert resolve_response.status_code == 403
    assert "authenticated human approver" in resolve_response.json()["detail"]

    # The rejected resolve did NOT mutate the gate — still waiting_human (retryable).
    detail = await wired_client.get(f"/runs/{run_id}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "waiting_human"


async def test_human_resolve_audit_records_actor_kind(
    wired_client: AsyncClient, runs_auth: None
) -> None:
    """AC-4 (ADR-016 S2 OQ-3, audit-only): a human-driven run-start + gate
    resolution stamp ``actor_kind='human'`` in the audit metadata (extending the
    existing ``'engine'`` convention), so the tamper-evident trail is filterable by
    actor class. The ``Person`` type carries no redundant ``kind`` field."""
    run_response = await wired_client.post(
        f"/procedures/{_PROCEDURE_ID}/run", json={}, headers=HEADERS
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["run_id"]
    action_id = run_response.json()["proposals"][0]["action_id"]

    resolve_response = await wired_client.post(
        f"/runs/{run_id}/gate/resolve",
        json={"step_id": _GATED_STEP, "decisions": {action_id: "approve"}},
        headers=HEADERS,
    )
    assert resolve_response.status_code == 200

    eng = await create_test_engine()
    try:
        async with eng.connect() as conn:
            rows = (
                await conn.execute(
                    sa.text(
                        "SELECT action, payload FROM audit_log "
                        "WHERE run_id = :run_id ORDER BY audit_id"
                    ),
                    {"run_id": run_id},
                )
            ).all()
    finally:
        await eng.dispose()

    kinds = {action: (payload or {}).get("actor_kind") for action, payload in rows}
    assert kinds["run_started"] == "human"
    assert kinds["gate_decision"] == "human"
    assert kinds["handler_receipt"] == "human"


# --- PLAN-0054 Control-leg v1: POST /runs/{id}/cancel (SD-B, waiting_human only) ---


async def test_cancel_waiting_human_run_records_audit(
    wired_client: AsyncClient, runs_auth: None
) -> None:
    """AC-5 (PLAN-0054 SD-B): an authenticated human cancels a `waiting_human` run
    → status `cancelled` + a `run_cancelled` audit row naming the canceller with
    `actor_kind:"human"`. The actor is the AUTHENTICATED id (non-null even though
    energy authors no `Person` set)."""
    run_response = await wired_client.post(
        f"/procedures/{_PROCEDURE_ID}/run", json={}, headers=HEADERS
    )
    assert run_response.json()["status"] == "waiting_human"
    run_id = run_response.json()["run_id"]

    cancel = await wired_client.post(f"/runs/{run_id}/cancel", headers=HEADERS)
    assert cancel.status_code == 200
    assert cancel.json()["run_status"] == "cancelled"
    # visible via the read endpoint
    assert (await wired_client.get(f"/runs/{run_id}")).json()["status"] == "cancelled"

    eng = await create_test_engine()
    try:
        async with eng.connect() as conn:
            row = (
                await conn.execute(
                    sa.text(
                        "SELECT actor_person_id, payload FROM audit_log "
                        "WHERE run_id = :run_id AND action = 'run_cancelled'"
                    ),
                    {"run_id": run_id},
                )
            ).one()
    finally:
        await eng.dispose()
    actor_person_id, payload = row
    assert actor_person_id == "op-somchai"
    assert payload["actor_kind"] == "human"


async def test_cancel_requires_authenticated_human(
    wired_client: AsyncClient, runs_auth: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-5 (RF-1): with `api_auth_enabled` off there is no accountable canceller →
    cancel fails closed (403) and the run is left untouched (`waiting_human`).

    Arrangement keyed for the same reason as the resolve guard above (PLAN-0112
    AC-1): the run endpoint now fails closed too, so the parked run is minted by a
    real principal and authn is revoked only for the cancel attempt."""
    run_id = (
        await wired_client.post(f"/procedures/{_PROCEDURE_ID}/run", json={}, headers=HEADERS)
    ).json()["run_id"]
    monkeypatch.setattr(settings, "api_auth_enabled", False)
    cancel = await wired_client.post(f"/runs/{run_id}/cancel")
    assert cancel.status_code == 403
    assert (await wired_client.get(f"/runs/{run_id}")).json()["status"] == "waiting_human"


async def test_cancel_non_waiting_human_is_409(wired_client: AsyncClient, runs_auth: None) -> None:
    """SD-B: only a `waiting_human` run is cancellable — a second cancel (the run is
    now `cancelled`) is a 409, not a silent re-cancel."""
    run_id = (
        await wired_client.post(f"/procedures/{_PROCEDURE_ID}/run", json={}, headers=HEADERS)
    ).json()["run_id"]
    assert (await wired_client.post(f"/runs/{run_id}/cancel", headers=HEADERS)).status_code == 200
    second = await wired_client.post(f"/runs/{run_id}/cancel", headers=HEADERS)
    assert second.status_code == 409
    assert "not cancellable" in second.json()["detail"]


# --- PLAN-0114 Step 2: POST /runs/{id}/continue (AC-2's HTTP half) ---
#
# Step 1's battery (tests/services/db/test_continue_no_decision_run.py) witnessed all
# five fail-closed guards at the LIBRARY level. What is untested until here is the
# ROUTE's own contract: that each library refusal is mapped to the right status code.
# That mapping is not free — `NoDecisionApproverError` subclasses `ProcedureError`, so
# an `except ProcedureError` arm placed first silently degrades the RF-1 403 to a 409.
#
# ⚠️ Honest scope note: the route checks RF-1 itself (before `load_run`, so an
# unauthenticated caller cannot probe which run ids exist), which makes the endpoint's
# `except NoDecisionApproverError` arm UNREACHABLE over HTTP — `auth.person_id` is
# non-None by the time the chokepoint is called. The arm is defence-in-depth for a
# future caller that reaches the chokepoint another way, and it is deliberately NOT
# claimed as covered here: no probe can redden it through this surface.


async def test_continue_refuses_a_gate_that_holds_decidable_proposals(
    wired_client: AsyncClient, runs_auth: None
) -> None:
    """AC-2(a) — the security boundary: /continue is never a resolve bypass.

    🔴 Asserted on the chokepoint's OWN detail string, not the bare 409. `resume_run`
    carries an independent second guard that refuses this exact case with a different
    message and the SAME status code (`persistence.py:447-452`), so `== 409` would
    stay green with the chokepoint's guard deleted — one code, two causes,
    discriminating neither. SD-3 admits any authenticated human, which is what makes
    this guard load-bearing rather than belt-and-braces.
    """
    run = await wired_client.post(f"/procedures/{_PROCEDURE_ID}/run", json={}, headers=HEADERS)
    run_id = run.json()["run_id"]
    assert len(run.json()["proposals"]) == 1, "precondition: this gate holds a REAL proposal"

    refused = await wired_client.post(
        f"/runs/{run_id}/continue", json={"step_id": _GATED_STEP}, headers=HEADERS
    )
    assert refused.status_code == 409
    assert "holds decidable proposals" in refused.json()["detail"], (
        f"the refusal must name the CHOKEPOINT's mechanism, not resume_run's; got "
        f"{refused.json()['detail']}"
    )
    assert (await wired_client.get(f"/runs/{run_id}")).json()[
        "status"
    ] == "waiting_human", "a refused acknowledgment must leave the run parked, not half-advanced"


async def test_continue_requires_an_authenticated_human(
    wired_client: AsyncClient, runs_auth: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-2(b) — RF-1: authn off means no accountable acknowledger → 403, run untouched.

    Arranged like the cancel guard above: the parked run is minted by a real principal
    and authn is revoked only for the acknowledgment attempt.

    🔴 The STATUS CODE alone does not discriminate here either, for the same reason
    AC-2(a) does not: RF-1 is guarded TWICE — once by this route (before ``load_run``,
    so an unauthenticated caller cannot probe which run ids exist) and once inside the
    chokepoint, which answers ``NoDecisionApproverError`` that this route also maps to
    403. Deleting EITHER guard leaves ``== 403`` green. The route's own detail string
    is what pins which layer answered, so it is asserted rather than the code.
    """
    run_id = (
        await wired_client.post(f"/procedures/{_PROCEDURE_ID}/run", json={}, headers=HEADERS)
    ).json()["run_id"]
    monkeypatch.setattr(settings, "api_auth_enabled", False)

    refused = await wired_client.post(f"/runs/{run_id}/continue", json={"step_id": _GATED_STEP})
    assert refused.status_code == 403
    assert "api_auth_enabled is off" in refused.json()["detail"], (
        "the ROUTE's guard must be what refuses — the chokepoint's twin says "
        f"'none was supplied' instead. Got {refused.json()['detail']}"
    )
    assert (await wired_client.get(f"/runs/{run_id}")).json()["status"] == "waiting_human"


async def test_continue_on_a_run_that_is_not_parked_is_409(
    wired_client: AsyncClient, runs_auth: None
) -> None:
    """AC-2(c) — a run with no gate to acknowledge. Cancelled here, because that is a
    settled state a human can actually reach from the same surface."""
    run_id = (
        await wired_client.post(f"/procedures/{_PROCEDURE_ID}/run", json={}, headers=HEADERS)
    ).json()["run_id"]
    assert (await wired_client.post(f"/runs/{run_id}/cancel", headers=HEADERS)).status_code == 200

    refused = await wired_client.post(
        f"/runs/{run_id}/continue", json={"step_id": _GATED_STEP}, headers=HEADERS
    )
    assert refused.status_code == 409
    assert "not parked at a gate" in refused.json()["detail"]


async def test_continue_naming_the_wrong_step_is_409(
    wired_client: AsyncClient, runs_auth: None
) -> None:
    """AC-2(d) — the acknowledging human names what they believe they are
    acknowledging; a mismatch means the run moved between the read and the POST, and
    the seam refuses rather than acknowledging whichever gate it happens to find."""
    run_id = (
        await wired_client.post(f"/procedures/{_PROCEDURE_ID}/run", json={}, headers=HEADERS)
    ).json()["run_id"]

    refused = await wired_client.post(
        f"/runs/{run_id}/continue", json={"step_id": "not_the_gate"}, headers=HEADERS
    )
    assert refused.status_code == 409
    assert "is not the step this run is suspended at" in refused.json()["detail"]


async def test_continue_on_an_unknown_run_is_404(
    wired_client: AsyncClient, runs_auth: None
) -> None:
    """The route's own 404 arm — distinct from the chokepoint's `not found`
    `ProcedureError`, which would otherwise surface as a 409."""
    refused = await wired_client.post(
        "/runs/no-such-run/continue", json={"step_id": _GATED_STEP}, headers=HEADERS
    )
    assert refused.status_code == 404


async def test_run_view_finds_the_suspended_step_when_the_gate_is_not_last(
    wired_client: AsyncClient, runs_auth: None
) -> None:
    """The read projection identifies the gate by STATUS, not by list position.

    Taking ``step_results[-1]`` would name a completed step and expose ITS (empty)
    output as the pending proposals, hiding the gate a human still has to decide.

    **This test was silently vacuous for one commit and the reason is worth keeping.**
    It used to backdate ``created_at`` and then assert its precondition against a raw
    ``ORDER BY created_at, step_result_id`` — a copy of what ``load_run`` did, not a
    call to it. When PLAN-0099 D3 re-keyed ``load_run`` on ``seq``, the precondition
    kept passing (the raw query really was scrambled) while the projection under test
    saw a perfectly ordered list, so the by-status rule was no longer being exercised
    at all. Nothing failed. That is the failure mode: an oracle whose fixture drifts
    away from the code path it is aiming at reports success either way.

    Both halves are fixed. The scramble is applied to ``seq``, which is what
    ``load_run`` actually reads, and the precondition is asserted on the list the
    ENDPOINT was handed rather than on a hand-rolled requery.
    """
    run_id = (
        await wired_client.post(f"/procedures/{_PROCEDURE_ID}/run", json={}, headers=HEADERS)
    ).json()["run_id"]

    # A second engine (no schema reset — the first was this test's fixture engine):
    # move the gated step to the FRONT of the run. A negative value rather than a swap
    # with the completed prefix: `seq` is UNIQUE and Postgres checks that per row.
    eng = await create_test_engine()
    try:
        async with eng.begin() as conn:
            await conn.execute(
                sa.text(
                    "UPDATE step_results SET seq = -1 "
                    "WHERE run_id = :run_id AND step_id = :step_id"
                ),
                {"run_id": run_id, "step_id": _GATED_STEP},
            )
    finally:
        await eng.dispose()

    ordered = [
        step["step_id"]
        for step in (await wired_client.get(f"/runs/{run_id}", headers=HEADERS)).json()["steps"]
    ]
    assert len(ordered) > 1, "the run must have a completed prefix for this to be meaningful"
    assert ordered[-1] != _GATED_STEP, (
        "precondition: the gate must not be last IN THE LIST THE ENDPOINT SEES — "
        "asserting this against a separate query is how this test went vacuous before"
    )

    detail = await wired_client.get(f"/runs/{run_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["status"] == "waiting_human"
    assert body["suspended_step"] == _GATED_STEP
    assert len(body["proposals"]) == 1, "the pending proposal is still exposed for decision"
