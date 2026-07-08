"""GET /whoami tests (PLAN-0058) — the auth-validating echo read.

Mirrors ``tests/api/test_api_auth.py``'s ``auth_on`` fixture: the suite runs
authn OFF by default (``tests/conftest.py``); each auth-on test flips it back
per-test with a provisioned digest → person. Six deterministic cases cover the
ratified SD-1 shape + the SD-2 fail-closed mirror + the AC-3 dev-escape. All
offline; no MS-S1, no DB.
"""

from __future__ import annotations

import hashlib

import pytest
from httpx import AsyncClient

import services.api.auth as auth_module
from services.api.config import settings
from services.engine.procedures.spec import Person

RAW_KEY = "test-key-op-somchai"
DIGEST = hashlib.sha256(RAW_KEY.encode("utf-8")).hexdigest()
HEADERS = {"Authorization": f"Bearer {RAW_KEY}"}

_PERSON = Person(person_id="op-somchai", name="Somchai P.", roles=frozenset({"approver"}))


@pytest.fixture
def auth_on(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enable authn with one provisioned key → person 'op-somchai'."""
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", {DIGEST: "op-somchai"})


async def test_whoami_valid_key_resolves_display_name(
    client: AsyncClient, auth_on: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-1: a principals-shipping vertical echoes person_id + the resolved name."""
    monkeypatch.setattr(auth_module, "_principal_index", lambda vertical: {"op-somchai": _PERSON})
    resp = await client.get("/whoami", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json() == {
        "person_id": "op-somchai",
        "display_name": "Somchai P.",
        "auth_enabled": True,
    }


async def test_whoami_valid_key_no_principals_vertical(
    client: AsyncClient, auth_on: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-1: a no-principals vertical echoes person_id with display_name null."""
    monkeypatch.setattr(auth_module, "_principal_index", lambda vertical: {})
    resp = await client.get("/whoami", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json() == {
        "person_id": "op-somchai",
        "display_name": None,
        "auth_enabled": True,
    }


async def test_whoami_missing_header_is_401(client: AsyncClient, auth_on: None) -> None:
    """AC-2 fail-closed: no Authorization header → 401 (the reject-at-login signal)."""
    assert (await client.get("/whoami")).status_code == 401


async def test_whoami_unknown_key_is_401(client: AsyncClient, auth_on: None) -> None:
    """AC-2 fail-closed: an unprovisioned key → 401."""
    resp = await client.get("/whoami", headers={"Authorization": "Bearer not-a-provisioned-key"})
    assert resp.status_code == 401


async def test_whoami_unmapped_person_is_403(
    client: AsyncClient, auth_on: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-2 fail-closed: a principals-shipping vertical rejects an unmapped subject → 403."""
    monkeypatch.setattr(auth_module, "_principal_index", lambda vertical: {"someone-else": _PERSON})
    resp = await client.get("/whoami", headers=HEADERS)
    assert resp.status_code == 403


async def test_whoami_auth_disabled_is_open(client: AsyncClient) -> None:
    """AC-3 dev-escape: authn off (suite default) → 200, person_id null, auth_enabled false."""
    resp = await client.get("/whoami")
    assert resp.status_code == 200
    assert resp.json() == {
        "person_id": None,
        "display_name": None,
        "auth_enabled": False,
    }
