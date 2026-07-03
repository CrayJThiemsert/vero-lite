"""AC-1 authn tests (PLAN-0047 Step 1) — the fail-closed API-key gate.

The legacy suites run with authn OFF (tests/conftest.py pins
``settings.api_auth_enabled = False``); every test here flips it ON
explicitly, so both AC-1 halves are exercised: unauthenticated → 401/403,
authenticated → success with the server-resolved identity recorded. The
route-coverage test is the enforceable form of the AC-1 "grep shows no
state-changing route without the dependency" read.
"""

from __future__ import annotations

import hashlib

import pytest
import sqlalchemy as sa
from fastapi.routing import APIRoute
from httpx import AsyncClient

import services.api.auth as auth_module
from services.api.config import settings
from services.api.main import app
from services.api.routers.actions import _action_store
from tests.db_support import create_test_engine

RAW_KEY = "test-key-op-somchai"
DIGEST = hashlib.sha256(RAW_KEY.encode("utf-8")).hexdigest()
HEADERS = {"Authorization": f"Bearer {RAW_KEY}"}


@pytest.fixture
def auth_on(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enable authn with one provisioned key → person 'op-somchai'."""
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", {DIGEST: "op-somchai"})


async def _first_action_id(client: AsyncClient) -> str:
    recs = (await client.get("/recommendations")).json()["recommendations"]
    return str(recs[0]["action_id"])


async def test_approve_without_key_is_401(client: AsyncClient, auth_on: None) -> None:
    """AC-1 fail-closed half: no Authorization header → 401, state unchanged."""
    action_id = await _first_action_id(client)
    response = await client.post(f"/recommendations/{action_id}/approve")
    assert response.status_code == 401
    assert _action_store[action_id].status.value == "proposed"


async def test_unknown_key_is_401(client: AsyncClient, auth_on: None) -> None:
    action_id = await _first_action_id(client)
    response = await client.post(
        f"/recommendations/{action_id}/approve",
        headers={"Authorization": "Bearer not-a-provisioned-key"},
    )
    assert response.status_code == 401


async def test_malformed_header_is_401(client: AsyncClient, auth_on: None) -> None:
    action_id = await _first_action_id(client)
    response = await client.post(
        f"/recommendations/{action_id}/approve",
        headers={"Authorization": "Basic dXNlcjpwYXNz"},
    )
    assert response.status_code == 401


async def test_valid_key_approves_and_records_identity(client: AsyncClient, auth_on: None) -> None:
    """AC-1 success half: authenticated approve succeeds; identity is the
    SERVER-resolved person_id from the key, never a client-supplied field."""
    action_id = await _first_action_id(client)
    response = await client.post(f"/recommendations/{action_id}/approve", headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert _action_store[action_id].approved_by == "op-somchai"


async def test_person_membership_403_when_unmapped(
    client: AsyncClient, auth_on: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A vertical that SHIPS principals fails closed on an unmapped subject."""
    monkeypatch.setattr(
        auth_module, "_principal_index", lambda vertical: {"someone-else": object()}
    )
    action_id = await _first_action_id(client)
    response = await client.post(f"/recommendations/{action_id}/approve", headers=HEADERS)
    assert response.status_code == 403


async def test_person_membership_resolves_when_mapped(
    client: AsyncClient, auth_on: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(auth_module, "_principal_index", lambda vertical: {"op-somchai": object()})
    action_id = await _first_action_id(client)
    response = await client.post(f"/recommendations/{action_id}/approve", headers=HEADERS)
    assert response.status_code == 200


async def test_warm_and_sleep_are_gated(client: AsyncClient, auth_on: None) -> None:
    """Host-state admin routes reject unauthenticated calls before any MS-S1 I/O."""
    assert (await client.get("/warm")).status_code == 401
    assert (await client.get("/sleep")).status_code == 401


async def test_intake_generate_is_gated(client: AsyncClient, auth_on: None) -> None:
    """/intake/generate WRITES the working tree → the dependency rejects first."""
    response = await client.post("/intake/generate", json={})
    assert response.status_code == 401


async def test_auth_disabled_preserves_legacy_behavior(client: AsyncClient) -> None:
    """With authn off (the suite-wide default) approve works with no header
    and records no identity — the pre-authn contract, unchanged."""
    action_id = await _first_action_id(client)
    response = await client.post(f"/recommendations/{action_id}/approve")
    assert response.status_code == 200
    assert _action_store[action_id].approved_by is None


async def test_execute_persists_identity_row(client_with_db: AsyncClient, auth_on: None) -> None:
    """AC-1 persisted half (Step-1 scope): the executed action's sidecar row
    carries the server-resolved approver/executor person_id."""
    action_id = await _first_action_id(client_with_db)
    assert (
        await client_with_db.post(f"/recommendations/{action_id}/approve", headers=HEADERS)
    ).status_code == 200
    assert (
        await client_with_db.post(f"/recommendations/{action_id}/execute", headers=HEADERS)
    ).status_code == 200

    eng = await create_test_engine()
    try:
        async with eng.connect() as conn:
            row = (
                await conn.execute(
                    sa.text(
                        "SELECT approved_by, executed_by FROM action_identity "
                        "WHERE action_id = :action_id"
                    ),
                    {"action_id": action_id},
                )
            ).one()
    finally:
        await eng.dispose()
    assert row.approved_by == "op-somchai"
    assert row.executed_by == "op-somchai"


def test_state_changing_routes_carry_authn() -> None:
    """The enforceable AC-1 coverage read: every state-changing route carries
    the authn dependency (path-suffix keyed so router prefixes cannot hide one)."""
    targets = {"/approve", "/execute", "/warm", "/sleep", "/intake/generate"}
    seen: set[str] = set()
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for suffix in targets:
            if route.path.endswith(suffix):
                deps = [dep.call for dep in route.dependant.dependencies]
                assert (
                    auth_module.get_current_principal in deps
                ), f"state-changing route '{route.path}' lacks get_current_principal"
                seen.add(suffix)
    assert seen == targets, f"expected every target route to exist; missing {targets - seen}"
