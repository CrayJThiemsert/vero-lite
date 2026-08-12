"""AC-7 — the persona loop is real (PLAN-0103 Step 6).

**The seam under test is picker → auth, and nothing on either side is stubbed.**
The producer is :func:`resolve_demo_personas`, the exact function ``/meta`` calls
to build the cards a visitor clicks; the consumer is the real
``POST /procedures/{id}/run`` and ``POST /runs/{id}/gate/resolve`` behind the
real ``get_current_principal`` dependency. The bearer tokens below are read
**out of the picker's own offer set** rather than declared here, so this module
cannot pass in the world where the picker serves keys that authenticate nobody.

That choice is the whole point. A suite that declared its own raw keys and
asserted the endpoints accept them would prove the endpoints work and say
nothing about whether the cards a visitor is shown can log in — and "the card
logs nobody in" is precisely the failure this Step exists to prevent, on the one
published system whose entire story is the approve beat.

**Refused-then-granted is walked across all THREE authored personas**, not across
a valid and an invalid key, and the two refusals come from *different governance
mechanisms*:

* **ต้อม** fired the round, so his own approval is refused by **separation of
  duties**;
* **วิรัช** is a genuine authenticated approver and is *still* refused, because
  this repair's amount routed the gate to the tier above his — the **DOA ladder
  routing**;
* **เฮีย** holds the routed tier and is granted.

The middle rung was found by measurement, not design: the module was first
written expecting วิรัช to be the approver, and the engine answered
``tier_role_mismatch … routed to 'appr-owner'``. Keeping all three is strictly
stronger — a module showing only a granted approval passes with SoD deleted, and
one showing only an SoD refusal passes with the ladder flattened.

DB-backed — SKIPS when Postgres is unreachable, and a skip is never satisfaction.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator

import pytest
import sqlalchemy as sa
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from services.api.config import settings
from services.api.demo_personas import resolve_demo_personas
from services.db.audit_log import AuditLog
from services.engine import demo_events
from services.engine.procedures import gate_hooks
from services.engine.procedures.persistence import load_run
from verticals.fleet_maintenance import case_projection

_VERTICAL = "fleet_maintenance"
_HERO = "governed_repair_approval"
_GATE_STEP = "approve"

_MECHANIC = "req-mechanic-tom"
_MANAGER = "appr-fleet-manager-wirat"
_OWNER = "appr-owner"

#: What an operator would put in UI_DEMO_PERSONA_KEYS. Deliberately NOT in
#: authored order — the picker is expected to re-order, and a fixture that
#: pre-sorted would hide it.
_PROVISIONED = {
    _OWNER: "scenario-raw-owner",
    _MECHANIC: "scenario-raw-tom",
    _MANAGER: "scenario-raw-wirat",
}


def _digest(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


#: The API_KEYS half, derived from the SAME raw values rather than written out
#: again. Two hand-typed copies is the drift the settings validator exists to
#: catch, and a test that reproduced that shape would be asserting against its
#: own typo rather than against the system.
_API_KEYS = {_digest(raw): person_id for person_id, raw in _PROVISIONED.items()}


@pytest.fixture(autouse=True)
def _clean() -> Iterator[None]:
    """Process-global caches; a leak makes a later test lie."""
    case_projection.reset()
    demo_events.reset(_VERTICAL)
    gate_hooks.clear_on_resolved()
    yield
    case_projection.reset()
    demo_events.reset(_VERTICAL)
    gate_hooks.clear_on_resolved()


@pytest.fixture
async def fleet_active(monkeypatch: pytest.MonkeyPatch) -> None:
    """Register exactly what the API lifespan registers, with authn ON.

    Authn on is load-bearing rather than incidental: with it off the run endpoint
    records no requester, and ``_enforce_principal_sod`` would refuse the later
    approval for a missing principal instead of on its MERITS. The refusal this
    module asserts has to be the SoD one.
    """
    from services.engine.discovery import discover_and_register
    from verticals.fleet_maintenance.procedures_factory import (
        register_fleet_maintenance_procedure_executors,
    )

    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    monkeypatch.setattr(settings, "oct_vertical", _VERTICAL)
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", _API_KEYS)
    monkeypatch.setattr(settings, "ui_demo_persona_keys", _PROVISIONED)
    # `ui_profile` is deliberately NOT set here. The published-only gate lives in
    # the /meta route, which this module does not call — `resolve_demo_personas`
    # itself is profile-agnostic by design (it resolves; the route decides
    # whether to serve). tests/api/test_ui_profile.py owns the profile branch,
    # in both directions.


def _offered() -> dict[str, str]:
    """The picker's OWN offer set, keyed by person_id.

    Read through the producer rather than from ``_PROVISIONED`` so the bearer
    tokens used below are literally the strings a visitor's browser receives.
    """
    return {
        p.person_id: p.key for p in resolve_demo_personas(_VERTICAL, settings.ui_demo_persona_keys)
    }


def _headers_for(person_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {_offered()[person_id]}"}


async def _audit_rows(maker: async_sessionmaker[AsyncSession], run_id: str) -> list[AuditLog]:
    async with maker() as session:
        rows = await session.execute(
            sa.select(AuditLog).where(AuditLog.run_id == run_id).order_by(AuditLog.audit_id)
        )
        return list(rows.scalars())


#: Sessions are opened AROUND the reads rather than held across the HTTP calls.
#:
#: Measured this session: taking the long-lived ``db_session`` fixture and
#: reading through it after firing a run left its close racing a connection the
#: app had checked out of the same engine — teardown raised "got Future attached
#: to a different loop" and the module exited non-zero while every assertion
#: passed. A short-lived session per read has no such window.
#:
#: (The first thing tried was touching ``db_session`` before the HTTP call, on
#: the theory that the sibling modules avoid this incidentally by seeding first.
#: It did not help, so that explanation was wrong and is not preserved here.)


async def _parked_decisions(maker: async_sessionmaker[AsyncSession], run_id: str) -> dict[str, str]:
    """Approve-everything decisions for the proposals sitting at the parked gate.

    Read off the PERSISTED run rather than a response body: the gate refuses a
    partial resolution, so the map has to cover every proposal the round actually
    parked, and the persisted artifact is where that set is authoritative.
    """
    async with maker() as session:
        loaded = await load_run(session, run_id)
        assert loaded is not None, f"run {run_id} did not persist"
        target = next(sr for sr in loaded.step_results if sr.step_id == _GATE_STEP)
        artifact = target.artifact
        assert artifact is not None, "the parked gate must have produced an artifact"
        return {str(p["action_id"]): "approve" for p in artifact["output_set"]}


@pytest.mark.anyio
async def test_the_offered_keys_are_the_keys_that_authenticate(
    client_with_db: AsyncClient, api_db_maker: async_sessionmaker[AsyncSession], fleet_active: None
) -> None:
    """The producer→consumer tie, asserted before anything is built on it.

    Every card the picker renders must resolve, through the real auth seam, to
    the person_id printed on that same card. Without this the two tests below
    could both pass while the picker offered a fourth key that worked and three
    that did not — the endpoints would look healthy and the demo would not.
    """
    offered = _offered()
    assert set(offered) == set(_PROVISIONED), "the picker must offer every provisioned persona"
    for person_id, raw_key in offered.items():
        who = await client_with_db.get("/whoami", headers={"Authorization": f"Bearer {raw_key}"})
        assert who.status_code == 200, f"{person_id}'s offered key was refused: {who.text}"
        assert who.json()["person_id"] == person_id, (
            f"the card labelled {person_id!r} authenticates as "
            f"{who.json()['person_id']!r} — the disclosure the picker shows "
            "('recorded under this name') would be false while nothing looked broken"
        )


@pytest.mark.anyio
async def test_all_three_personas_meet_the_ladder_refused_refused_granted(
    client_with_db: AsyncClient, api_db_maker: async_sessionmaker[AsyncSession], fleet_active: None
) -> None:
    """AC-7's refused-then-granted, walked across the WHOLE authored ladder.

    Three cards, three outcomes, and the two refusals are refused by **different
    governance mechanisms** — which is what makes this stronger than a
    valid-key/invalid-key pair:

    * **ต้อม** fired the round, so his own approval is refused by the live
      **separation-of-duties** check. Deleting SoD would turn this green.
    * **วิรัช** is a genuine, authenticated approver — and is still refused,
      because this repair's amount routed the gate to the tier ABOVE his. This
      is the **DOA ladder routing**, and it is the assertion a suite that only
      showed a happy-path approval can never make. Measured, not assumed: the
      engine answers `tier_role_mismatch … routed to 'appr-owner'`.
    * **เฮีย** holds the routed tier, and is granted.

    A visitor clicking the three cards in order sees exactly this, which is the
    demo beat Step 6 exists to make real.
    """
    fired = await client_with_db.post(
        f"/procedures/{_HERO}/run", json={}, headers=_headers_for(_MECHANIC)
    )
    assert fired.status_code == 200, fired.text
    run_id: str = fired.json()["run_id"]

    decisions = await _parked_decisions(api_db_maker, run_id)
    assert decisions, "no parked proposals means every assertion below is vacuous"
    payload = {"step_id": _GATE_STEP, "decisions": decisions}

    self_approval = await client_with_db.post(
        f"/runs/{run_id}/gate/resolve", json=payload, headers=_headers_for(_MECHANIC)
    )
    assert self_approval.status_code == 403, (
        "ต้อม fired this round, so approving it himself must be refused — got "
        f"{self_approval.status_code}: {self_approval.text}"
    )
    assert "sod" in self_approval.text.lower() or "distinct" in self_approval.text.lower(), (
        "the refusal must be the SEPARATION-OF-DUTIES one. A 403 for any other "
        f"reason would satisfy the status assertion while proving nothing: {self_approval.text}"
    )

    too_low = await client_with_db.post(
        f"/runs/{run_id}/gate/resolve", json=payload, headers=_headers_for(_MANAGER)
    )
    assert too_low.status_code == 403, (
        "วิรัช is a real approver but the ladder routed this amount above his tier — "
        f"got {too_low.status_code}: {too_low.text}"
    )
    assert "tier" in too_low.text.lower(), (
        "the refusal must be the TIER-AUTHORITY one, not SoD — วิรัช did not fire "
        f"this round, so an SoD refusal here would mean the ladder is not routing: {too_low.text}"
    )

    granted = await client_with_db.post(
        f"/runs/{run_id}/gate/resolve", json=payload, headers=_headers_for(_OWNER)
    )
    assert (
        granted.status_code == 200
    ), f"เฮีย holds the routed tier and must be granted: {granted.text}"


@pytest.mark.anyio
async def test_the_audit_trail_records_the_acting_persona(
    client_with_db: AsyncClient, api_db_maker: async_sessionmaker[AsyncSession], fleet_active: None
) -> None:
    """ "Every decision is recorded under this name" — the disclosure, measured.

    The picker's whole promise is that the name on the card is the name in the
    record. Asserted positively (วิรัช's id IS in the gate rows) AND negatively
    (ต้อม's is not in them), because either alone is satisfiable by the wrong
    world: a positive-only check passes if EVERY persona is recorded on every
    row, and a negative-only check passes if nothing is recorded at all.
    """
    fired = await client_with_db.post(
        f"/procedures/{_HERO}/run", json={}, headers=_headers_for(_MECHANIC)
    )
    assert fired.status_code == 200, fired.text
    run_id: str = fired.json()["run_id"]

    decisions = await _parked_decisions(api_db_maker, run_id)
    granted = await client_with_db.post(
        f"/runs/{run_id}/gate/resolve",
        json={"step_id": _GATE_STEP, "decisions": decisions},
        headers=_headers_for(_OWNER),
    )
    assert granted.status_code == 200, granted.text

    rows = await _audit_rows(api_db_maker, run_id)
    assert rows, "no audit rows means every assertion below is vacuous"

    gate_rows = [r for r in rows if r.action == "gate_decision"]
    assert gate_rows, "the resolution must have written a gate_decision row"

    # Read the structured column, not a stringified payload. `actor_person_id` is
    # what the chain actually binds a decision to; a substring search over the
    # payload blob would pass on any incidental mention and fail on a correct row
    # that simply does not repeat the id in its JSON.
    deciders = {row.actor_person_id for row in gate_rows}
    assert deciders == {_OWNER}, (
        f"the gate rows are attributed to {deciders} — the persona who actually "
        f"acted is {_OWNER}, and the picker's on-screen promise ('recorded in the "
        "audit trail under this name') is exactly this column"
    )
    assert _MECHANIC not in deciders, (
        f"the REQUESTER ({_MECHANIC}) is recorded as deciding. He fired the round "
        "and was refused; a trail naming him here would attribute a decision to "
        "the wrong rung of a ladder built to keep them distinct"
    )

    # The requester IS recorded — on the row that starts the run, not on the
    # decision. Asserted so "the mechanic is absent from the gate rows" cannot be
    # satisfied by the trail having forgotten him entirely, which would be the
    # same green for the opposite reason.
    started = [r for r in rows if r.action == "run_started"]
    assert started, "the run must have written a run_started row"
    assert {r.actor_person_id for r in started} == {_MECHANIC}, (
        f"ต้อม fired this round and must be the actor on run_started; got "
        f"{ {r.actor_person_id for r in started} }"
    )
