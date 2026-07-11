"""PLAN-0063 Step 3 — the audit-chain verification endpoint (GET /audit/verify).

DB-backed (skips without Postgres). Proves the read-only trust-dossier contract:

* AC-1 an intact chain verifies over HTTP (intact / rows_verified / head_hash /
  genesis_hash);
* AC-2 an in-place mutation is reported verbatim (the library "mutated" string);
* AC-3 a prev_hash linkage break is reported verbatim (a NEW induction exemplar —
  the library suite only exercised the mutation shape);
* AC-4 an empty chain is honest (intact, 0 rows, null head);
* AC-5 the response model is closed (extra="forbid") with a description on every
  field;
* AC-6 the SD-2(d) split-visibility auth posture — anonymous sees the verdict but
  breaks are withheld (null), a valid credential reveals them, and a presented-
  but-invalid credential still 401s (never silently downgraded).

The fixture installs the frozen migration-0007 block trigger on the create_all
schema (mirroring tests/services/db/test_audit_log.py) so the break-induction
cases exercise the REAL disable-trigger tamper path.
"""

from __future__ import annotations

import hashlib
from collections.abc import AsyncIterator
from typing import Any

import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

import services.api.auth as auth_module
from services.api.config import settings
from services.api.main import app
from services.api.models.audit import ChainVerificationReport
from services.db.audit_log import (
    AUDIT_BLOCK_FUNCTION_SQL,
    AUDIT_BLOCK_TRIGGER_SQL,
    GENESIS_HASH,
    append_audit,
)
from services.db.base import Base
from services.db.session import get_session
from tests.db_support import create_test_engine

_RAW_KEY = "auditor-secret-key"
_DIGEST = hashlib.sha256(_RAW_KEY.encode("utf-8")).hexdigest()
_VERIFY = "/audit/verify"


@pytest.fixture
async def audit_env() -> AsyncIterator[tuple[AsyncClient, AsyncEngine]]:
    """An httpx client whose get_session is bound to a per-test engine that
    carries the audit block trigger, plus that engine so a test can seed rows
    with append_audit and induce tampering directly."""
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(sa.text(AUDIT_BLOCK_FUNCTION_SQL))
        await conn.execute(sa.text(AUDIT_BLOCK_TRIGGER_SQL))
    maker = async_sessionmaker(eng, expire_on_commit=False)

    async def _override_session() -> AsyncIterator[Any]:
        async with maker() as session:
            yield session

    app.dependency_overrides[get_session] = _override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http, eng
    app.dependency_overrides.clear()
    async with eng.begin() as conn:
        await conn.execute(sa.text("DROP TRIGGER IF EXISTS audit_log_no_mutation ON audit_log"))
        await conn.execute(sa.text("DROP FUNCTION IF EXISTS audit_log_block_mutation()"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


async def _append(engine: AsyncEngine, action: str, **kwargs: Any) -> None:
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        await append_audit(session, action=action, **kwargs)
        await session.commit()


async def _head_row_hash(engine: AsyncEngine) -> str | None:
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        return (
            await session.execute(
                sa.text("SELECT row_hash FROM audit_log ORDER BY audit_id DESC LIMIT 1")
            )
        ).scalar_one_or_none()


# --- AC-1 / AC-4: the verdict over an intact and an empty chain ---------------


async def test_intact_chain_verifies_over_http(
    audit_env: tuple[AsyncClient, AsyncEngine], monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-1: a freshly appended, untampered chain reports intact with the full
    verdict. Runs under the global authn-off default, so breaks are disclosed."""
    monkeypatch.setattr(settings, "api_auth_enabled", False)
    client, eng = audit_env
    await _append(eng, "run_started", run_id="ax-1")
    await _append(eng, "gate_decision", run_id="ax-1", step_id="approve")
    await _append(eng, "handler_receipt", run_id="ax-1", payload={"receipt": {"ok": True}})

    resp = await client.get(_VERIFY)
    assert resp.status_code == 200
    body = resp.json()
    assert body["intact"] is True
    assert body["breaks"] == []
    assert body["rows_verified"] == 3
    assert body["head_hash"] == await _head_row_hash(eng)
    assert body["genesis_hash"] == GENESIS_HASH
    assert body["verified_at"]


async def test_empty_chain_is_honest(
    audit_env: tuple[AsyncClient, AsyncEngine], monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-4: an empty audit_log verifies intact with zero rows and a null head."""
    monkeypatch.setattr(settings, "api_auth_enabled", False)
    client, _eng = audit_env

    resp = await client.get(_VERIFY)
    assert resp.status_code == 200
    body = resp.json()
    assert body["intact"] is True
    assert body["breaks"] == []
    assert body["rows_verified"] == 0
    assert body["head_hash"] is None
    assert body["genesis_hash"] == GENESIS_HASH


# --- AC-2 / AC-3: break shapes reported verbatim ------------------------------


async def test_in_place_mutation_reported_verbatim(
    audit_env: tuple[AsyncClient, AsyncEngine], monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-2: disable the trigger, mutate a row in place, re-enable — the endpoint
    reports intact=false and the library 'row content mutated' string verbatim."""
    monkeypatch.setattr(settings, "api_auth_enabled", False)
    client, eng = audit_env
    await _append(eng, "run_started", run_id="ax-2")
    await _append(eng, "gate_decision", run_id="ax-2", step_id="approve")

    async with eng.begin() as conn:
        await conn.execute(sa.text("ALTER TABLE audit_log DISABLE TRIGGER audit_log_no_mutation"))
        await conn.execute(
            sa.text("UPDATE audit_log SET action = 'forged' WHERE action = 'gate_decision'")
        )
        await conn.execute(sa.text("ALTER TABLE audit_log ENABLE TRIGGER audit_log_no_mutation"))

    resp = await client.get(_VERIFY)
    assert resp.status_code == 200
    body = resp.json()
    assert body["intact"] is False
    assert body["breaks"], "the mutated row must surface a break"
    assert any("row content mutated" in b for b in body["breaks"])


async def test_linkage_break_reported_verbatim(
    audit_env: tuple[AsyncClient, AsyncEngine], monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3: rewrite a row's prev_hash under a disabled trigger — a NEW induction
    exemplar (the library suite only exercised the mutation shape). The endpoint
    reports intact=false and the 'prev_hash linkage broken' string verbatim."""
    monkeypatch.setattr(settings, "api_auth_enabled", False)
    client, eng = audit_env
    await _append(eng, "run_started", run_id="ax-3")
    await _append(eng, "gate_decision", run_id="ax-3", step_id="approve")
    await _append(eng, "handler_receipt", run_id="ax-3")

    async with eng.begin() as conn:
        await conn.execute(sa.text("ALTER TABLE audit_log DISABLE TRIGGER audit_log_no_mutation"))
        # sever the linkage of the middle row without touching its own content,
        # so the break is a prev_hash mismatch, not a recomputed-hash mismatch.
        await conn.execute(
            sa.text(
                "UPDATE audit_log SET prev_hash = :g WHERE action = 'gate_decision'"
            ).bindparams(g="f" * 64)
        )
        await conn.execute(sa.text("ALTER TABLE audit_log ENABLE TRIGGER audit_log_no_mutation"))

    resp = await client.get(_VERIFY)
    assert resp.status_code == 200
    body = resp.json()
    assert body["intact"] is False
    assert any("prev_hash linkage broken" in b for b in body["breaks"])


# --- AC-6: SD-2(d) split-visibility auth posture ------------------------------


async def test_anonymous_gets_verdict_but_breaks_withheld(
    audit_env: tuple[AsyncClient, AsyncEngine], monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-6 / SD-2(d): with authn ON and no credential, a tampered chain still
    reports the verdict (intact=false, rows_verified) but withholds the break
    detail (breaks=null, never []). null != [] is the whole point."""
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", {_DIGEST: "auditor-1"})
    client, eng = audit_env
    await _append(eng, "run_started", run_id="ax-4")
    await _append(eng, "gate_decision", run_id="ax-4", step_id="approve")

    async with eng.begin() as conn:
        await conn.execute(sa.text("ALTER TABLE audit_log DISABLE TRIGGER audit_log_no_mutation"))
        await conn.execute(
            sa.text("UPDATE audit_log SET action = 'forged' WHERE action = 'gate_decision'")
        )
        await conn.execute(sa.text("ALTER TABLE audit_log ENABLE TRIGGER audit_log_no_mutation"))

    resp = await client.get(_VERIFY)  # no Authorization header
    assert resp.status_code == 200
    body = resp.json()
    assert body["intact"] is False
    assert body["rows_verified"] == 2
    assert body["breaks"] is None, "an anonymous caller must not see the break detail"


async def test_valid_credential_reveals_breaks(
    audit_env: tuple[AsyncClient, AsyncEngine], monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-6: with authn ON and a valid credential, the same tampered chain
    discloses the verbatim break strings."""
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", {_DIGEST: "auditor-1"})
    # keep the posture vertical-independent: empty index => person_id present,
    # person None (the auth.py `if index:` false branch) => breaks revealed.
    monkeypatch.setattr(auth_module, "_principal_index", lambda vertical: {})
    client, eng = audit_env
    await _append(eng, "run_started", run_id="ax-5")
    await _append(eng, "gate_decision", run_id="ax-5", step_id="approve")

    async with eng.begin() as conn:
        await conn.execute(sa.text("ALTER TABLE audit_log DISABLE TRIGGER audit_log_no_mutation"))
        await conn.execute(
            sa.text("UPDATE audit_log SET action = 'forged' WHERE action = 'gate_decision'")
        )
        await conn.execute(sa.text("ALTER TABLE audit_log ENABLE TRIGGER audit_log_no_mutation"))

    resp = await client.get(_VERIFY, headers={"Authorization": f"Bearer {_RAW_KEY}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["intact"] is False
    assert body["breaks"] is not None
    assert any("row content mutated" in b for b in body["breaks"])


async def test_presented_but_invalid_credential_401s(
    audit_env: tuple[AsyncClient, AsyncEngine], monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-6: a bad key is NOT silently downgraded to the anonymous view — it
    401s loudly, so a misconfigured auditor is caught."""
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", {_DIGEST: "auditor-1"})
    client, _eng = audit_env

    resp = await client.get(_VERIFY, headers={"Authorization": "Bearer wrong-key"})
    assert resp.status_code == 401


# --- AC-5: response-model discipline (no DB needed) ---------------------------


def test_response_model_is_closed_and_described() -> None:
    """AC-5: extra keys are rejected and every field carries a description."""
    with pytest.raises(ValueError):
        ChainVerificationReport.model_validate(
            {
                "intact": True,
                "breaks": [],
                "rows_verified": 0,
                "head_hash": None,
                "genesis_hash": GENESIS_HASH,
                "verified_at": "2026-07-11T00:00:00Z",
                "unexpected": 1,
            }
        )
    for name, field in ChainVerificationReport.model_fields.items():
        assert field.description, f"field {name!r} must carry a Field(description=...)"
