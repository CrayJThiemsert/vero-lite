"""Accepting a quote fires a governed run — the visitor's case reaches Tab H.

**PLAN-0112 Step 3 / AC-2 + AC-3.** The §8-binding scenario: the REAL Tab I HTTP
intake flow (``POST /api/cases`` → ``/quotes`` → ``/accepted-quote``) drives the REAL
server-side firing seam on realistic simulated data — a breaching THB amount against
a real seeded ``Truck`` ceiling — and the run is read back through the REAL Tab H
surface (``GET /runs``). Nothing on either side of the seam is stubbed.

**The run existing is NOT the claim; the run being ABOUT the visitor's case is.**
The hero's ``intake`` is a fleet-wide population scan (G-6), so a run can fire, park,
and present a perfectly healthy gate that concerns some other truck entirely — with
the visitor's own case absent from every proposal and no error raised anywhere.
Session 244 measured exactly that shape when the case projection had not caught up
(a run whose single proposal resolved to ``case-demo-truck03-gearbox``). So every
test here asserts the visitor's ``case_id`` is among the proposals, not merely that
the count moved. A suite that only counted runs would stay green through that defect.

**SD-2(b) as Cray ruled it, both directions.** Re-accepting the SAME quote is not a
material change and must NOT mint a second run; accepting a DIFFERENT quote must.
That is why ``entity_ids`` carries the quote's identity (G-14) and never
``accepted_id``, which ``accept_quote`` regenerates on every call.

**The demo seed's parked run must not swallow the visitor's.** Fleet's published
profile pins ``OCT_DEMO_SEED_OPERATE=true``, which parks a ``governed_repair_approval``
run at boot; the bridge's SD-P4 backpressure would otherwise skip every visitor
acceptance on that deployment with no error and no visible trace.

DB-backed — SKIPS when Postgres is unreachable, and a skip is never satisfaction.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.config import settings
from services.engine import demo_events
from services.engine.procedures import gate_hooks
from verticals.fleet_maintenance import case_projection

_VERTICAL = "fleet_maintenance"
_HERO = "governed_repair_approval"

#: ต้อม — the one fleet persona holding the SoD ``requester`` role, and therefore the
#: only valid ``event_trigger.owning_person_id`` (G-8). Firing keyed as him is what
#: leaves the run approvable by a distinct human.
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
    """Register exactly what the API lifespan registers, and make fleet active.

    The executor-factory registration is not optional: the seam resolves executors
    through the registry, and without it ``load_event_resolver`` returns ``None`` and
    the seam becomes a silent no-op — which would make every count assertion below
    pass for the wrong reason.
    """
    from services.engine.discovery import discover_and_register
    from verticals.fleet_maintenance.procedures_factory import (
        register_fleet_maintenance_procedure_executors,
    )

    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    monkeypatch.setattr(settings, "oct_vertical", _VERTICAL)
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", {_DIGEST: _MECHANIC})


async def _open_case_with_quotes(client: AsyncClient) -> tuple[str, list[str]]:
    """A real ฿62,000 axle breakdown with three garages compared — over truck-01's ceiling."""
    opened = await client.post(
        "/api/cases",
        json={
            "truck_id": "truck-01",
            "work_type": "breakdown",
            "description": "เพลาขาดกลางทางแถวปากช่อง",
        },
        headers=_HEADERS,
    )
    assert opened.status_code == 201, opened.text
    case_id: str = opened.json()["case_id"]
    quote_ids: list[str] = []
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
        quote_ids.append(quoted.json()["quote_id"])
    return case_id, quote_ids


async def _accept(client: AsyncClient, case_id: str, quote_id: str) -> None:
    accepted = await client.post(
        f"/api/cases/{case_id}/accepted-quote",
        json={"quote_id": quote_id, "reason": "เจ้าเดียวที่มีเพลาพร้อมเปลี่ยนวันนี้"},
        headers=_HEADERS,
    )
    assert accepted.status_code == 201, accepted.text


async def _hero_runs(client: AsyncClient) -> list[dict[str, Any]]:
    """The runs Tab H itself would paint, filtered to the hero procedure."""
    listed = await client.get("/runs", headers=_HEADERS)
    assert listed.status_code == 200, listed.text
    return [r for r in listed.json()["runs"] if r["procedure_id"] == _HERO]


async def _proposal_case_ids(client: AsyncClient, run_id: str) -> list[str]:
    got = await client.get(f"/runs/{run_id}", headers=_HEADERS)
    assert got.status_code == 200, got.text
    return [str(p["action_id"]) for p in got.json()["proposals"]]


async def _assert_run_is_about(client: AsyncClient, run_id: str, case_id: str) -> None:
    """The load-bearing half: this run's gate concerns the visitor's OWN case.

    Asserted separately from the count because the two fail independently — a run
    that fires on a stale projection moves the count and proposes another truck.
    """
    proposals = await _proposal_case_ids(client, run_id)
    assert any(case_id in pid for pid in proposals), (
        f"run {run_id} fired but proposes {proposals} — the visitor's case {case_id} "
        "is not among them. The seam must run AFTER _refresh_case_events, or the run "
        "gates on whatever the stale projection still held."
    )


async def test_accepting_a_quote_fires_a_governed_run_about_that_case(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """AC-3: the whole promise, end to end through the real surfaces."""
    before = len(await _hero_runs(client_with_db))
    case_id, quotes = await _open_case_with_quotes(client_with_db)

    assert len(await _hero_runs(client_with_db)) == before, (
        "opening a case and keying quotes must fire NOTHING — a case with no accepted "
        "quote projects no governable event at all (G-4)"
    )

    await _accept(client_with_db, case_id, quotes[1])

    runs = await _hero_runs(client_with_db)
    assert len(runs) == before + 1, "exactly one governed run per governable acceptance"
    assert runs[0]["status"] == "waiting_human", "the run parks for a human (G-12)"
    await _assert_run_is_about(client_with_db, runs[0]["run_id"], case_id)


async def test_re_accepting_the_same_quote_does_not_mint_a_second_run(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """AC-2(i) — SD-2(b): the same quote re-accepted is not a material change.

    This is the assertion that fails if the key is ever moved to ``accepted_id``:
    ``accept_quote`` mints a fresh ``accepted-{uuid4}`` per call, so a double-click
    would mint a second run.
    """
    case_id, quotes = await _open_case_with_quotes(client_with_db)
    await _accept(client_with_db, case_id, quotes[1])
    after_first = len(await _hero_runs(client_with_db))

    await _accept(client_with_db, case_id, quotes[1])

    assert len(await _hero_runs(client_with_db)) == after_first, (
        "re-accepting the SAME quote minted a second run — entity_ids must carry the "
        "quote's identity, never the per-call accepted_id (G-14)"
    )


async def test_accepting_a_different_quote_mints_one_more_run(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """AC-2(ii) — SD-2(b) as ruled: a materially different acceptance re-fires.

    Load-bearing beyond the key: the first run is parked ``waiting_human`` by the time
    this fires, so this also pins that the bridge's SD-P4 backpressure is opted out of
    for this seam. With the default it returns SKIPPED_IN_FLIGHT and the count stays 1.
    """
    case_id, quotes = await _open_case_with_quotes(client_with_db)
    await _accept(client_with_db, case_id, quotes[1])
    after_first = len(await _hero_runs(client_with_db))

    await _accept(client_with_db, case_id, quotes[2])

    runs = await _hero_runs(client_with_db)
    assert len(runs) == after_first + 1, (
        "accepting a DIFFERENT quote must mint a new run (SD-2(b)); if this reads "
        "equal, either the key lost the quote id or SD-P4 skipped the fire"
    )
    for run in runs:
        await _assert_run_is_about(client_with_db, run["run_id"], case_id)


async def test_the_seeded_demo_run_does_not_swallow_a_visitor_acceptance(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """The published-profile shape: a parked demo run must not block the visitor.

    ``OCT_DEMO_SEED_OPERATE=true`` on fleet's published profile
    (``deploy/published/oct-fleet-maintenance/published.env``), and the seed parks a
    ``governed_repair_approval`` run at ``waiting_human`` by construction — the seed
    RAISES if it does not. Under the bridge's stock SD-P4 backpressure that parked run
    makes every visitor acceptance a silent ``SKIPPED_IN_FLIGHT``, which is the whole
    promise of this PLAN failing with nothing to see.
    """
    from verticals.fleet_maintenance.operate_seed import (
        seed_demo_repair_case,
        seed_repair_gate_waiting_human_run,
    )

    await seed_demo_repair_case(db_session)
    await case_projection.refresh(db_session)
    seeded = await seed_repair_gate_waiting_human_run(db_session)
    assert seeded.run.status == "waiting_human", "the premise: a parked run is in the way"
    before = len(await _hero_runs(client_with_db))

    case_id, quotes = await _open_case_with_quotes(client_with_db)
    await _accept(client_with_db, case_id, quotes[1])

    runs = await _hero_runs(client_with_db)
    assert len(runs) == before + 1, (
        "the visitor's acceptance fired nothing while the seeded demo run was parked — "
        "SD-P4 backpressure swallowed it (PLAN-0112 Step 3, skip_if_in_flight=False)"
    )
    fired = next(r for r in runs if r["run_id"] != seeded.run.run_id)
    await _assert_run_is_about(client_with_db, fired["run_id"], case_id)
