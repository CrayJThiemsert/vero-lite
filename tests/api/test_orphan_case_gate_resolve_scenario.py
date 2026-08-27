"""Resolving a gate whose repair case has been ERASED — the live demo's real shape.

**Why this exists.** Session 257 measured the published fleet system and found a run
parked at `approve`, resolvable by any visitor, whose repair case no longer exists
(`docs/logs/2026-08-27-s257-fleet-walk-residue-readonly-probe.md`). The open question
was whether a visitor clicking that gate hits a 500 on a dangling case reference.

Reading the code said no: `services/api/routers/runs.py` and
`services/engine/procedures/action_step.py` carry zero references to
`RepairCase` / `repair_case` / `case_id`, and the whole `services/engine/` tree
(74 modules) has none either — against a control where the same grep finds five
modules under `services/db/` and four under `services/api/`. But a grep proves what
the code *says*, not what the system *does*, and CLAUDE.md §8 is explicit that a
scenario test must drive the real producer into the real consumer rather than agree
with the author's reading. This module is that test, and it is also the guard: if
anyone later teaches the resolve path to dereference the case, this reddens instead
of a visitor finding out.

**Nothing is stubbed on either side of the seam.** Producer: the real HTTP capture
surface (`POST /api/cases` + quotes + accepted-quote) and the real shipped procedure
fired through the real run endpoint. Erasure: the real DSR seam
`repair_case_retention.delete_case` — the same call the retention sweep uses, not a
hand-rolled `DELETE`. Consumer: the real `resolve_gated_step` driver.

**The positive control is load-bearing, not decoration.** The claim is that a
deletion changes nothing, and "nothing changed" is a negative — so the identical
round WITHOUT the deletion runs beside it. If both fail, the harness is broken and
neither result means anything; only control-green-with-claim-green establishes that
the erasure is what was survived.

**`gate_hooks.failures()` is asserted in every test here** for the reason the sibling
module records: the link hook is fail-soft by design, and session 191 measured it
swallowing an exception so completely that the test asserting the resulting absence
stayed green. Without this assertion, "the resolve succeeded" would be satisfied by a
resolve that exploded quietly inside the hook.

DB-backed — SKIPS when Postgres is unreachable, and a skip is never satisfaction.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.config import settings
from services.db import repair_case_retention
from services.db.repair_case import RepairCase
from services.engine import demo_events
from services.engine.procedures import gate_hooks
from services.engine.procedures.action_step import resolve_gated_step
from services.engine.procedures.persistence import load_run
from services.engine.procedures.spec import load_procedures
from verticals.fleet_maintenance import case_projection

_VERTICAL = "fleet_maintenance"
_HERO = "governed_repair_approval"
_GATE_STEP = "approve"
_OWNER = "appr-owner"
_MECHANIC = "req-mechanic-tom"

_RAW_KEY = "test-key-req-mechanic-tom"
_DIGEST = hashlib.sha256(_RAW_KEY.encode("utf-8")).hexdigest()
_HEADERS = {"Authorization": f"Bearer {_RAW_KEY}"}


@pytest.fixture(autouse=True)
def _clean() -> Iterator[None]:
    case_projection.reset()
    demo_events.reset(_VERTICAL)
    gate_hooks.clear_on_resolved()
    yield
    case_projection.reset()
    demo_events.reset(_VERTICAL)
    gate_hooks.clear_on_resolved()


@pytest.fixture
async def fleet_active(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.engine.discovery import discover_and_register
    from verticals.fleet_maintenance.procedures_factory import (
        register_fleet_maintenance_procedure_executors,
    )

    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    monkeypatch.setattr(settings, "oct_vertical", _VERTICAL)
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", {_DIGEST: _MECHANIC})


def _person(person_id: str) -> Any:
    spec = load_procedures(_VERTICAL)
    return next(p for p in spec.principals if p.person_id == person_id)


async def _accepted_case(client: AsyncClient) -> str:
    """A real breakdown case with three garages compared and one agreed."""
    opened = await client.post(
        "/api/cases",
        json={
            "truck_id": "truck-01",
            "work_type": "breakdown",
            "description": "เพลาขาดกลางทาง — เคสสำหรับทดสอบว่าลบเคสแล้ว gate ยังกดได้",
        },
        headers=_HEADERS,
    )
    assert opened.status_code == 201, opened.text
    case_id: str = opened.json()["case_id"]
    chosen = ""
    for vendor, amount in (
        ("ส.เจริญยนต์", "58000.00"),
        ("อู่ริมทางปากช่อง", "62000.00"),
        ("อู่ช่างเล็ก", "59500.00"),
    ):
        quoted = await client.post(
            f"/api/cases/{case_id}/quotes",
            data={"vendor": vendor, "amount_thb": amount},
            headers=_HEADERS,
        )
        assert quoted.status_code == 201, quoted.text
        if vendor == "อู่ริมทางปากช่อง":
            chosen = quoted.json()["quote_id"]
    accepted = await client.post(
        f"/api/cases/{case_id}/accepted-quote",
        json={"quote_id": chosen, "reason": "เจ้าเดียวที่มีของพร้อมเปลี่ยนวันนี้"},
        headers=_HEADERS,
    )
    assert accepted.status_code == 201, accepted.text
    return case_id


async def _fire(client: AsyncClient) -> dict[str, Any]:
    fired = await client.post(f"/procedures/{_HERO}/run", json={}, headers=_HEADERS)
    assert fired.status_code == 200, fired.text
    body: dict[str, Any] = fired.json()
    assert body["triggered_by"] == _MECHANIC
    return body


def _decide(body: dict[str, Any], case_id: str, verdict: str) -> dict[str, str]:
    """Decide every proposal — the gate refuses a partial resolution."""
    ours = next(str(p["action_id"]) for p in body["proposals"] if case_id in str(p["action_id"]))
    return {
        str(p["action_id"]): (verdict if str(p["action_id"]) == ours else "reject")
        for p in body["proposals"]
    }


async def _resolve(session: AsyncSession, run_id: str, decisions: dict[str, str]) -> Any:
    """The real driver, with the SoD inputs the hero's constraint demands."""
    spec = load_procedures(_VERTICAL)
    procedure = next(p for p in spec.procedures if p.procedure_id == _HERO)
    return await resolve_gated_step(
        session,
        run_id,
        _GATE_STEP,
        decisions,
        _person(_OWNER),
        procedure=procedure,
        principals=list(spec.principals),
    )


async def _case_rows(session: AsyncSession, case_id: str) -> list[str]:
    rows = await session.execute(sa.select(RepairCase.case_id).where(RepairCase.case_id == case_id))
    return list(rows.scalars())


async def test_the_gate_still_resolves_after_its_case_is_erased(
    client_with_db: AsyncClient,
    db_session: AsyncSession,
    fleet_active: None,
    tmp_path: Path,
) -> None:
    """THE CLAIM. Erase the case out from under a parked run; the gate still resolves.

    This is the published system's exact state as measured s257: a run at `approve`
    whose case is gone, reachable by any visitor through the ingress allowlist. If
    this test ever reddens, that visitor gets a 500 instead of a decision.
    """
    case_id = await _accepted_case(client_with_db)
    body = await _fire(client_with_db)
    run_id = body["run_id"]
    decisions = _decide(body, case_id, "approve")

    # --- the erasure, through the real DSR seam -------------------------------
    await repair_case_retention.delete_case(db_session, case_id, photo_root=tmp_path)
    assert await _case_rows(db_session, case_id) == [], (
        "precondition: the case must actually be gone, or this test proves nothing — "
        "it would be the control running twice under a different name"
    )

    # --- the consumer, on a dangling reference --------------------------------
    await _resolve(db_session, run_id, decisions)

    loaded = await load_run(db_session, run_id)
    assert loaded is not None, "the run must survive its case"
    gate = next(s for s in loaded.step_results if s.step_id == _GATE_STEP)
    assert gate.status != "waiting_human", (
        f"the {_GATE_STEP} step must have actually advanced — a resolve that left it "
        "parked would satisfy 'no exception' while doing nothing"
    )
    assert gate_hooks.failures() == [], (
        "the link hook is FAIL-SOFT: without this, an exception swallowed inside it "
        "would let 'the resolve succeeded' pass over a resolve that broke"
    )


async def test_control_the_same_round_with_the_case_intact(
    client_with_db: AsyncClient,
    db_session: AsyncSession,
    fleet_active: None,
) -> None:
    """POSITIVE CONTROL for the test above — deliberately identical but for the erasure.

    The claim under test is a negative ("deleting the case changes nothing"), and a
    negative is only evidence when the same shape is shown to produce a positive.
    If this control ever fails, the test above proves nothing regardless of its own
    result: the harness, not the deletion, is what was measured.
    """
    case_id = await _accepted_case(client_with_db)
    body = await _fire(client_with_db)
    run_id = body["run_id"]

    assert await _case_rows(db_session, case_id) == [case_id], "control: the case is present"

    await _resolve(db_session, run_id, _decide(body, case_id, "approve"))

    loaded = await load_run(db_session, run_id)
    assert loaded is not None
    gate = next(s for s in loaded.step_results if s.step_id == _GATE_STEP)
    assert gate.status != "waiting_human"
    assert gate_hooks.failures() == []
