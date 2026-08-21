"""``POST /procedures/{id}/run`` fails closed without an authenticated human.

**PLAN-0112 AC-1 — the asymmetry this closes, and why it had to close first.**
``run_procedure_endpoint`` is the ONLY producer of a ``PipelineRun``, and it was the
only one of the three run-surface doors that did not fail closed: ``gate/resolve``
and ``cancel`` both 403 on a ``None`` principal, while firing a governed run — the
act that *creates* the thing those two guard — accepted an unauthenticated caller
and recorded ``triggered_by: null``. PLAN-0110's G10.6 found the asymmetry and
demanded any visitor-reachable firing path close it **in the same change**; PLAN-0112
hard-orders it FIRST, before a firing seam exists to widen the hole.

**Where the guard sits is part of the claim.** It runs before spec loading and before
any DB write, so a principal-less request costs nothing and — the assertion below —
can never leave a row behind. A 403 that still persisted a ``running`` row would
satisfy a status-code-only test and violate the point.

**The 403 is reachable only with authn OFF, and that is not a gap.** With
``api_auth_enabled`` on, a missing or bad credential is rejected as a 401 by
``get_current_principal`` before this endpoint body runs; ``person_id`` is ``None``
only on the authn-off deployment escape. That is exactly the hole the sibling guards
were written for (PLAN-0053), and this test mirrors their shape deliberately.

DB-backed — SKIPS when Postgres is unreachable, and a skip is never satisfaction.
"""

from __future__ import annotations

import hashlib

import pytest
import sqlalchemy as sa
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.config import settings
from services.engine.procedures.runs import PipelineRun

_VERTICAL = "fleet_maintenance"
_HERO = "governed_repair_approval"

#: ต้อม — the one fleet persona holding the SoD ``requester`` role, so a run fired as
#: him resolves its requester and stays approvable by a distinct human. A declared
#: fleet principal, so the bearer resolves against the real spec with no
#: ``_principal_index`` monkeypatch (the ``test_run_link_scenario.py`` precedent).
_MECHANIC = "req-mechanic-tom"
_RAW_KEY = "test-key-req-mechanic-tom"
_DIGEST = hashlib.sha256(_RAW_KEY.encode("utf-8")).hexdigest()
_HEADERS = {"Authorization": f"Bearer {_RAW_KEY}"}


@pytest.fixture
async def fleet_registered(monkeypatch: pytest.MonkeyPatch) -> None:
    """Register EXACTLY what the API lifespan registers, and make fleet active.

    The executor-factory registration is not optional: a firing seam that resolves
    executors through the registry 409s until it has run (PLAN-0112 G-10), which
    would make a 403 assertion below pass for the wrong reason.
    """
    from services.engine.discovery import discover_and_register
    from verticals.fleet_maintenance.procedures_factory import (
        register_fleet_maintenance_procedure_executors,
    )

    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    monkeypatch.setattr(settings, "oct_vertical", _VERTICAL)


async def _run_rows(session: AsyncSession) -> int:
    return int(
        (await session.execute(sa.select(sa.func.count()).select_from(PipelineRun))).scalar_one()
    )


async def test_firing_without_a_principal_is_refused_and_writes_nothing(
    client_with_db: AsyncClient,
    db_session: AsyncSession,
    fleet_registered: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-1: no accountable human -> 403 citing RF-1, and ZERO new ``pipeline_runs``.

    Both halves are asserted because either alone is satisfiable by a broken guard:
    a 403 raised *after* ``run_procedure_persisted`` would leave a durable row (the
    write-ahead driver commits the ``running`` row before step 1), and a row count
    that never moved would also hold if the request had failed for some unrelated
    reason. Together they pin the guard's placement, not just its verdict.
    """
    monkeypatch.setattr(settings, "api_auth_enabled", False)

    before = await _run_rows(db_session)
    response = await client_with_db.post(f"/procedures/{_HERO}/run", json={})

    assert response.status_code == 403, response.text
    detail = response.json()["detail"]
    assert "ADR-016 S2" in detail and "RF-1" in detail, detail
    assert "authenticated human" in detail, detail

    assert await _run_rows(db_session) == before, (
        "a refused firing left a pipeline_runs row behind — the guard must run "
        "BEFORE run_procedure_persisted's write-ahead insert, not after"
    )


async def test_a_keyed_persona_still_fires_and_parks_at_the_gate(
    client_with_db: AsyncClient,
    db_session: AsyncSession,
    fleet_registered: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-1's other half: the guard refuses the anonymous caller WITHOUT closing the
    door on the legitimate one.

    Without this, a guard that rejected every caller — ``raise`` with no condition —
    would pass the refusal test above and silently break the product. It is the
    positive control for that assertion, not a duplicate of the sibling suites.
    """
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", {_DIGEST: _MECHANIC})

    before = await _run_rows(db_session)
    response = await client_with_db.post(f"/procedures/{_HERO}/run", json={}, headers=_HEADERS)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "waiting_human", body
    assert body["triggered_by"] == _MECHANIC, body
    assert await _run_rows(db_session) == before + 1
