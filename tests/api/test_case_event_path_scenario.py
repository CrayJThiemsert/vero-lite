"""The case → event path, end to end (PLAN-0096 Step 8, build-order item 2).

**The scenario test CLAUDE.md §8 requires, and the one this build exists to make
possible.** Before it, a real repair case never reached a governed run: เมย์ could
open a case, key quotes and accept one, and the procedure that routes spend would
never see any of it. The only ``case_id`` that ever reached a run was a hardcoded
fixture, so every claim about "the gate governs real repairs" was true of the demo
and false of the product.

Nothing here is stubbed on either side of the seam under test. The producer is the
real HTTP capture surface (``POST /api/cases``, ``/quotes``, ``/accepted-quote``);
the consumer is the real registered adapter and the real shipped procedure, driven
through the real run endpoint. A version of this test that hand-built an event dict
and fed it to the adapter would agree with itself by construction and prove nothing
— which is exactly the failure mode the constitutional rule names.

Realistic data, not placeholders: a roadside axle failure on truck-01, three garages
quoting in the ranges the design partner described, and the dearer garage accepted
for a reason a human would actually give.

Every request here is keyed as ``req-mechanic-tom`` — ต้อม, the head mechanic. That
became load-bearing at PLAN-0112 AC-1, which closed ``POST /procedures/{id}/run``'s
RF-1 hole: firing a governed run now requires an authenticated human, so the module
arms authn and carries the bearer on every call. It also makes the scenario truer to
its own story — a mechanic filing and keying his own case, not an anonymous caller —
and no assertion here reads ``opened_by``/``accepted_by``, so nothing this module
proves changed with the identity.

DB-backed — SKIPS when Postgres is unreachable, and a skip is never satisfaction.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from decimal import Decimal

import pytest
from httpx import AsyncClient

from services.api.config import settings
from services.engine import demo_events
from services.engine.registry import registry
from verticals.fleet_maintenance import case_projection

_VERTICAL = "fleet_maintenance"
_HERO = "governed_repair_approval"
#: The fixture beat this scenario is meant to outrank — truck-01's ฿48,000 axle
#: breakdown, the demo's hero row until a real case exists on that truck.
_FIXTURE_HERO_EVENT = "event-reading-02"

#: PLAN-0112 AC-1 closed `POST /procedures/{id}/run`'s RF-1 hole, so firing the hero
#: now requires an authenticated human. Keyed as the head mechanic — the ONE persona
#: holding fleet's SoD `requester` role, so the run's requester resolves and a distinct
#: approver can still govern it. Mirrors `test_run_link_scenario.py`'s established shape.
_MECHANIC = "req-mechanic-tom"
_RAW_KEY = "test-key-req-mechanic-tom"
_DIGEST = hashlib.sha256(_RAW_KEY.encode("utf-8")).hexdigest()
_HEADERS = {"Authorization": f"Bearer {_RAW_KEY}"}


@pytest.fixture(autouse=True)
def _clean_projection() -> Iterator[None]:
    """Both caches are process-global; a leaked one would make a later test lie.

    ``case_projection.reset()`` also drops ``demo_events``' live list, so the next
    read rebuilds from whatever the projection then holds.
    """
    case_projection.reset()
    demo_events.reset(_VERTICAL)
    yield
    case_projection.reset()
    demo_events.reset(_VERTICAL)


@pytest.fixture
async def fleet_active(monkeypatch: pytest.MonkeyPatch) -> None:
    """Register EXACTLY what the API lifespan registers, and make fleet the active vertical.

    ``discover_and_register`` + the procedure-executor factory is the pair the real
    process uses; registering handlers by hand instead would mask the class of bug
    where a vertical is reachable in tests and 409s in production.
    """
    from services.engine.discovery import discover_and_register
    from verticals.fleet_maintenance.procedures_factory import (
        register_fleet_maintenance_procedure_executors,
    )

    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    monkeypatch.setattr(settings, "oct_vertical", _VERTICAL)
    # PLAN-0112 AC-1: the run endpoint now fails closed without a principal, so the
    # hero is fired as a real authenticated ต้อม. `req-mechanic-tom` is a declared
    # fleet principal, so the bearer resolves against the real spec with no
    # `_principal_index` monkeypatch (the `test_run_link_scenario.py` precedent).
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", {_DIGEST: _MECHANIC})


async def _open_axle_case(client: AsyncClient) -> str:
    response = await client.post(
        "/api/cases",
        headers=_HEADERS,
        json={
            "truck_id": "truck-01",
            "work_type": "breakdown",
            "description": "เพลาขาดกลางทางแถวปากช่อง รถจอดข้างทางพร้อมของเต็มคัน",
        },
    )
    assert response.status_code == 201, response.text
    case_id: str = response.json()["case_id"]
    return case_id


async def _quote(client: AsyncClient, case_id: str, vendor: str, amount: str) -> str:
    response = await client.post(
        f"/api/cases/{case_id}/quotes",
        data={"vendor": vendor, "amount_thb": amount},
        headers=_HEADERS,
    )
    assert response.status_code == 201, response.text
    quote_id: str = response.json()["quote_id"]
    return quote_id


async def _fleet_events() -> list[dict]:
    """Read the stream through the REAL registered adapter, as a query step would."""
    adapter = registry.get_adapter(_VERTICAL)
    return await adapter.fetch_objects("OperationalEvent")


async def test_a_real_accepted_case_reaches_the_gate_and_outranks_the_fixture(
    client_with_db: AsyncClient, fleet_active: None
) -> None:
    """The whole claim in one run: เมย์'s case becomes the row the ladder routes on.

    Three garages quote the axle job; the dearest is accepted because it is the only
    one with the part, with the reason recorded. ฿62,000 clears truck-01's ฿5,001
    ceiling, so ``judge`` calls it a breach, ``reshape`` derives the governed
    ``amount`` from it, and the run parks at the human gate — on OUR case, not on the
    fixture's ฿48,000 axle row, because ``intake`` reads the LATEST event per truck
    and a case accepted today is later than any fixture beat.

    That the hero narrative moves is the intended consequence (Cray, typed s191), not
    a regression: the alternative was parking real cases on trucks the demo does not
    use, which would have hidden the collision until two real cases landed together.
    """
    case_id = await _open_axle_case(client_with_db)
    await _quote(client_with_db, case_id, "ส.เจริญยนต์", "58000.00")
    dearest = await _quote(client_with_db, case_id, "อู่ริมทางปากช่อง", "62000.00")
    await _quote(client_with_db, case_id, "อู่ช่างเล็ก", "59500.00")

    accepted = await client_with_db.post(
        f"/api/cases/{case_id}/accepted-quote",
        headers=_HEADERS,
        json={
            "quote_id": dearest,
            "reason": "เจ้าเดียวที่มีเพลาพร้อมเปลี่ยนวันนี้ รออะไหล่อีก 5 วันไม่ได้",
        },
    )
    assert accepted.status_code == 201, accepted.text

    # --- the seam: the real adapter now serves the real case -------------------
    events = await _fleet_events()
    ours = [e for e in events if e.get("case_id") == case_id]
    assert len(ours) == 1, "the accepted case must appear exactly once on the stream"
    (event,) = ours
    assert event["measured_value"] == 62000.0, "the GOVERNED figure, not the cheapest quote"
    assert event["unit"] == "THB"
    assert event["event_type"] == "reading"
    # Three distinct garages above the ฿30,000 threshold: the sourcing rule is
    # satisfied as WRITTEN, computed by the same function the fixture calls.
    assert event["compliance"] == {"three_quote": True}
    assert event["three_quote_basis"] == "three_quotes"

    truck_01 = [e for e in events if e.get("truck_id") == "truck-01"]
    latest = max(truck_01, key=lambda e: e["occurred_at"])
    assert latest["case_id"] == case_id, (
        "a real accepted case must outrank the fixture beat on its own truck — "
        "intake reads the LATEST event per truck"
    )
    assert any(
        e["event_id"] == _FIXTURE_HERO_EVENT for e in events
    ), "the fixture row must still be ON the timeline as history — superseded, not deleted"

    # --- the consumer: the real shipped procedure, through the real endpoint ---
    fired = await client_with_db.post(f"/procedures/{_HERO}/run", json={}, headers=_HEADERS)
    assert fired.status_code == 200, fired.text
    body = fired.json()
    assert body["status"] == "waiting_human", "the run must park for a person, not self-approve"

    proposals = body["proposals"]
    assert proposals, "a breaching real case must produce a gated proposal"
    rendered = repr(proposals)
    assert case_id in rendered, (
        "the parked gate must be about the REAL case — if this fails the run reached "
        "the gate on the fixture row and the case → event path is still severed"
    )


async def test_a_case_below_the_ceiling_never_reaches_the_gate(
    client_with_db: AsyncClient, fleet_active: None
) -> None:
    """A case with no run is REAL, and must present as an absence rather than an error.

    Routine below-ceiling repairs are the majority of the partner's work: the head
    mechanic settles them himself and nothing should ask an owner to approve them.
    The month-end export has to count these against the KPI as missing rows, so the
    behaviour is pinned here rather than discovered later against a number that
    silently looked complete.
    """
    case_id = await _open_axle_case(client_with_db)
    quote_id = await _quote(client_with_db, case_id, "ร้านประจำ", "3200.00")
    accepted = await client_with_db.post(
        f"/api/cases/{case_id}/accepted-quote",
        json={"quote_id": quote_id},
        headers=_HEADERS,
    )
    assert accepted.status_code == 201, accepted.text

    events = await _fleet_events()
    (event,) = (e for e in events if e.get("case_id") == case_id)
    # It IS on the stream — the case happened, and the timeline should show it.
    assert event["measured_value"] == 3200.0
    assert event["severity"] == "info", "below its truck's ceiling is not a breakdown alarm"
    # ...and under the ฿30,000 comparison threshold the sourcing rule never applied.
    assert event["three_quote_basis"] == "under_threshold"

    fired = await client_with_db.post(f"/procedures/{_HERO}/run", json={}, headers=_HEADERS)
    assert fired.status_code == 200, fired.text
    rendered = repr(fired.json()["proposals"])
    assert case_id not in rendered, (
        "a below-ceiling repair must not reach the approval gate — the head mechanic "
        "settles it, and asking for an approval would be the hollow-compliance shape"
    )


async def test_nothing_changes_until_a_quote_is_accepted(
    client_with_db: AsyncClient, fleet_active: None
) -> None:
    """Quotes alone do not make a governed figure.

    This is the load-bearing negative. The DOA ladder routes on the accepted amount;
    a case with three quotes and no acceptance has no agreed number, and emitting one
    anyway would mean inventing it. Until เมย์ accepts, the stream must be exactly
    what it was before the case existed.

    **The health assertions are not decoration.** The router refreshes the projection
    fail-soft, so a refresh that CRASHED would leave the stream unchanged too — and an
    unchanged stream is exactly what this test asserts. Measured: a mutation that let
    unaccepted cases through raised inside the digest, the fail-soft handler swallowed
    it, and this test stayed green. Checking that the view is loaded and carries no
    error is what makes the absence a decision rather than a silent failure.
    """
    before = await _fleet_events()

    case_id = await _open_axle_case(client_with_db)
    await _quote(client_with_db, case_id, "ส.เจริญยนต์", "58000.00")
    await _quote(client_with_db, case_id, "อู่ช่างเล็ก", "59500.00")

    after = await _fleet_events()
    assert [e["event_id"] for e in after] == [e["event_id"] for e in before]
    assert not [e for e in after if e.get("case_id") == case_id]

    health = case_projection.status()
    assert health["cases_with_accepted_quote"] == 0
    assert health["loaded"] is True, "the view must have actually run, not merely stayed empty"
    assert health["last_error"] is None, (
        "the stream is unchanged because nothing was ACCEPTED — not because the refresh "
        "blew up and the fail-soft handler swallowed it"
    )
    assert health["trucks_not_found"] == []


async def test_switching_the_agreed_garage_moves_the_governed_figure(
    client_with_db: AsyncClient, fleet_active: None
) -> None:
    """A change of mind must reach the gate, or the ladder routes on a stale number.

    This is what the projection's fingerprinted cache-drop exists for: without it the
    ``demo_events`` live list would still hold the first acceptance and the gate would
    authorise ฿58,000 of spend the operator had already moved away from."""
    case_id = await _open_axle_case(client_with_db)
    cheaper = await _quote(client_with_db, case_id, "ส.เจริญยนต์", "58000.00")
    dearer = await _quote(client_with_db, case_id, "อู่ริมทางปากช่อง", "62000.00")

    first = await client_with_db.post(
        f"/api/cases/{case_id}/accepted-quote",
        json={"quote_id": cheaper},
        headers=_HEADERS,
    )
    assert first.status_code == 201, first.text
    (event,) = (e for e in await _fleet_events() if e.get("case_id") == case_id)
    assert event["measured_value"] == 58000.0

    switched = await client_with_db.post(
        f"/api/cases/{case_id}/accepted-quote",
        json={"quote_id": dearer, "reason": "เจ้าแรกถอนตัว ไม่มีเพลา"},
        headers=_HEADERS,
    )
    assert switched.status_code == 201, switched.text
    (event,) = (e for e in await _fleet_events() if e.get("case_id") == case_id)
    assert event["measured_value"] == 62000.0, (
        "the stream must follow the LATEST acceptance — a stale figure here would let "
        "the gate authorise spend the operator has already moved away from"
    )
    assert Decimal(str(event["measured_value"])) == Decimal("62000")
