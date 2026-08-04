"""The task-chain, driven END TO END on a realistic case (PLAN-0096 Step 6 / AC-7).

**This is the CLAUDE.md §8 scenario test for Step 6.** The rule suite
(``tests/verticals/fleet_maintenance/test_task_chain.py``) proves the SLA rules
behave — it feeds ``RepairCaseTaskEvent`` objects the test author constructed, so
it agrees with itself by construction. What it cannot prove is that the rows the
API actually WRITES are rows the sweep can READ, or that the label the nudge
carries is the one the partner would recognise.

So every case below drives the real producer into the real consumer: the real
FastAPI routes write real rows into a real Postgres, the real sweep reads them
back, the real ``services.notify.line`` seam builds and pushes the real message.
The ONLY fakes are the two CLAUDE.md §8 permits — an injected transport (so the
suite opens no socket, AC-11) and an injected clock (so a five-day parts wait does
not take five days).

The narrative is the partner's own, from round-2 answer A1: a tractor head breaks
down on the road, the garage is called, a major part is ordered, and the repair
cannot start until it lands. Each assertion is a thing that would go wrong in his
yard, not a thing that would go wrong in a unit test.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.config import settings
from services.api.routers import cases as cases_router
from services.db.task_chain_sweep import sweep_stale_tasks
from services.notify.line import reset_cooldown
from tests.clock_support import Clock

#: Distinct from any other role id in the suite, so a nudge landing in the wrong
#: inbox cannot pass by coincidence.
_OPERATOR_ID = "Uoperator_taskchain_0000000000000"

_T0 = datetime(2026, 7, 29, 8, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _photo_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "repair-case-photos"
    monkeypatch.setattr(settings, "repair_case_photo_dir", str(target))
    return target


@pytest.fixture(autouse=True)
def _armed_line(monkeypatch: pytest.MonkeyPatch) -> None:
    """Arm LINE with an operator recipient — task-chain nudges go to เมย์ (A3)."""
    monkeypatch.setattr(settings, "line_notify_enabled", True)
    monkeypatch.setattr(settings, "line_channel_access_token", "test-token")
    monkeypatch.setattr(settings, "line_recipients", json.dumps({"operator": _OPERATOR_ID}))
    monkeypatch.setattr(settings, "line_notify_cooldown_s", 0)
    reset_cooldown()


class _Recorder:
    """Captures what would have gone over the wire."""

    def __init__(self) -> None:
        self.pushes: list[dict[str, Any]] = []

    def transport(self) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            self.pushes.append(json.loads(request.content))
            return httpx.Response(200, json={})

        return httpx.MockTransport(handler)

    @property
    def texts(self) -> list[str]:
        return [push["messages"][0]["text"] for push in self.pushes]


async def _open_breakdown_case(client: AsyncClient, truck_id: str = "truck-07") -> str:
    response = await client.post(
        "/api/cases",
        json={
            "truck_id": truck_id,
            "description": "เพลาขาดแถวปากช่อง วิ่งต่อไม่ได้",
            "work_type": "breakdown",
        },
    )
    assert response.status_code == 201, response.text
    return str(response.json()["case_id"])


async def _flip(
    client: AsyncClient, case_id: str, item_key: str, status: str, **extra: Any
) -> dict:
    response = await client.post(
        f"/api/cases/{case_id}/tasks",
        json={"item_key": item_key, "status": status, **extra},
    )
    assert response.status_code == 201, response.text
    return dict(response.json())


# --------------------------------------------------------------------------- #


async def test_the_chain_the_api_writes_is_the_chain_the_sweep_reads(
    client_with_db: AsyncClient, db_session: AsyncSession
) -> None:
    """The seam this module exists for: API-written rows drive a real nudge.

    เมย์ opens a roadside case and activates the garage call. Nobody confirms a
    garage. Forty minutes later — past the 30-minute breakdown SLA — the sweep must
    find it and push a nudge naming the truck and the step IN THE PARTNER'S OWN
    WORDS.

    If the router wrote a status string the chain config does not recognise, or the
    sweep queried a column the router does not fill, every rule-suite test would
    still pass and this pushes nothing. That is the exact shape of the seam bug the
    §8 rule exists to catch.
    """
    case_id = await _open_breakdown_case(client_with_db)
    await _flip(client_with_db, case_id, "notify_garage", "pending")

    recorder = _Recorder()
    report = await sweep_stale_tasks(
        db_session, now=datetime.now(UTC) + timedelta(minutes=40), transport=recorder.transport()
    )

    assert report.stale_found == 1, "the 30-minute breakdown SLA has passed"
    assert report.nudged == 1
    assert len(recorder.texts) == 1
    body = recorder.texts[0]
    assert "แจ้งอู่" in body, "the nudge must name the step the way the partner does"
    assert "truck-07" in body
    assert case_id in body
    assert recorder.pushes[0]["to"] == _OPERATOR_ID, "task-chain nudges go to เมย์ (A3)"


async def test_a_pm_case_gets_a_day_where_a_breakdown_gets_half_an_hour(
    client_with_db: AsyncClient, db_session: AsyncSession
) -> None:
    """A1's context variant, end to end — and the one most likely to be lost in wiring.

    Two cases, identical except ``work_type``. At the 40-minute mark the breakdown is
    overdue and the PM is not. If ``work_type`` failed to reach the SLA lookup — the
    column not written, not read, or defaulted somewhere in between — both would fire
    and เมย์ would start muting a channel that cries wolf on routine servicing.
    """
    breakdown_id = await _open_breakdown_case(client_with_db, truck_id="truck-11")
    pm_response = await client_with_db.post(
        "/api/cases", json={"truck_id": "truck-12", "work_type": "pm"}
    )
    assert pm_response.status_code == 201, pm_response.text
    pm_id = str(pm_response.json()["case_id"])

    await _flip(client_with_db, breakdown_id, "notify_garage", "pending")
    await _flip(client_with_db, pm_id, "notify_garage", "pending")

    recorder = _Recorder()
    await sweep_stale_tasks(
        db_session, now=datetime.now(UTC) + timedelta(minutes=40), transport=recorder.transport()
    )

    assert len(recorder.pushes) == 1, "only the breakdown is late at 40 minutes"
    assert "truck-11" in recorder.texts[0]
    assert all("truck-12" not in text for text in recorder.texts), (
        "a PM booking has a day to be confirmed — nudging at 40 minutes is how the "
        "channel gets muted"
    )


async def test_a_truck_waiting_on_a_real_major_part_is_never_nudged_about_starting(
    client_with_db: AsyncClient, db_session: AsyncSession
) -> None:
    """The partner's own workflow, played out through the API on the real clock rules.

    Garage confirmed, a major part ordered, the wait flagged ``major_part`` — A1 gives
    that five days. On day four the repair has not started, and NOTHING should be
    nudged: the parts wait is inside its allowance, and the repair is waiting on the
    parts.

    This is the case that fails loudly if the anchor rule regresses to "count from
    when the item was added", and it fails through the real API rather than through
    hand-built rows — so it also covers ``variant`` surviving the round trip into
    Postgres and back out into the SLA lookup.
    """
    case_id = await _open_breakdown_case(client_with_db, truck_id="truck-21")
    await _flip(client_with_db, case_id, "notify_garage", "done")
    await _flip(client_with_db, case_id, "order_parts", "done")
    await _flip(client_with_db, case_id, "wait_parts", "pending", variant="major_part")
    chain = await _flip(client_with_db, case_id, "start_repair", "pending")

    assert chain["stale_item_keys"] == [], "nothing is late on the day the work is logged"

    recorder = _Recorder()
    report = await sweep_stale_tasks(
        db_session, now=datetime.now(UTC) + timedelta(days=4), transport=recorder.transport()
    )

    assert report.stale_found == 0, (
        "day 4 of an authorised 5-day major-part wait is normal — and the repair "
        "cannot start before the part lands"
    )
    assert recorder.pushes == []


async def test_once_the_part_lands_the_repair_starts_its_own_clock(
    client_with_db: AsyncClient, db_session: AsyncSession
) -> None:
    """The other half of A1's "1 วันหลังของครบ", end to end.

    Same case, but the part has arrived. Now — and only now — เริ่มซ่อม is on the
    clock, and a day and a half later it is late. This is the nudge that has real
    operational value: a truck sitting in a yard with its parts on the shelf.
    """
    case_id = await _open_breakdown_case(client_with_db, truck_id="truck-22")
    await _flip(client_with_db, case_id, "notify_garage", "done")
    await _flip(client_with_db, case_id, "order_parts", "done")
    await _flip(client_with_db, case_id, "wait_parts", "pending", variant="major_part")
    await _flip(client_with_db, case_id, "start_repair", "pending")
    await _flip(client_with_db, case_id, "wait_parts", "done")

    recorder = _Recorder()
    report = await sweep_stale_tasks(
        db_session,
        now=datetime.now(UTC) + timedelta(days=1, hours=12),
        transport=recorder.transport(),
    )

    assert report.stale_found == 1
    assert "เริ่มซ่อม" in recorder.texts[0]
    assert "truck-22" in recorder.texts[0]


async def test_the_screen_and_the_nudge_never_disagree(
    client_with_db: AsyncClient, db_session: AsyncSession
) -> None:
    """What เมย์ sees after tapping the nudge must be what the nudge said.

    A person who receives "งานค้าง" and opens a screen showing nothing outstanding
    stops trusting the channel within a week. Both paths go through ``stale_items``,
    and this proves they still do — the GET's own staleness flags and the sweep's
    findings are compared on the same case at the same moment.
    """
    case_id = await _open_breakdown_case(client_with_db, truck_id="truck-31")
    await _flip(client_with_db, case_id, "notify_garage", "pending")
    await _flip(client_with_db, case_id, "arrange_tow", "pending")

    # ONE instant for both paths. Comparing a sweep at T+2h against a screen at "now"
    # would compare two different questions and prove nothing about agreement.
    moment = datetime.now(UTC) + timedelta(hours=2)

    recorder = _Recorder()
    await sweep_stale_tasks(db_session, now=moment, transport=recorder.transport())
    nudged_labels = {text.split("ขั้นตอน")[-1].split("\n")[0].strip(' "') for text in recorder.texts}

    response = await client_with_db.get(
        f"/api/cases/{case_id}/tasks", params={"as_of": moment.isoformat()}
    )
    assert response.status_code == 200, response.text
    chain = response.json()
    screen_labels = {item["label_th"] for item in chain["items"] if item["is_stale"]}

    assert (
        nudged_labels == screen_labels
    ), "the phone screen and the push must be computed from one definition of 'ค้าง'"
    assert len(screen_labels) == 2, "both the garage call and the tow are past their SLA at 2h"


async def test_a_completed_item_stops_producing_nudges_for_good(
    client_with_db: AsyncClient, db_session: AsyncSession
) -> None:
    """เมย์ answers the nudge — and the channel goes quiet about it forever.

    Written through the API precisely because the append-only design makes this
    non-obvious: the ``pending`` row is still in the table after the ``done`` row is
    written, so a sweep that read rows instead of reduced STATE would keep nudging
    about work that is finished. Thirty days out, it stays silent.
    """
    case_id = await _open_breakdown_case(client_with_db, truck_id="truck-41")
    await _flip(client_with_db, case_id, "notify_garage", "pending")
    await _flip(client_with_db, case_id, "notify_garage", "done")

    recorder = _Recorder()
    report = await sweep_stale_tasks(
        db_session, now=datetime.now(UTC) + timedelta(days=30), transport=recorder.transport()
    )

    assert report.stale_found == 0
    assert recorder.pushes == []


async def test_the_append_only_trail_keeps_every_flip_and_its_actor(
    client_with_db: AsyncClient, db_session: AsyncSession
) -> None:
    """AC-7's "actor + timestamp per flip", proved against what the API stored.

    A correction does not overwrite: เมย์ marks the tow done, then re-opens it because
    the truck is still on the road. Both rows survive, the chain reports the LATEST,
    and the trail can still show a human that the first answer was given and revised.
    """
    case_id = await _open_breakdown_case(client_with_db, truck_id="truck-51")
    await _flip(client_with_db, case_id, "arrange_tow", "pending", actor="person-may")
    await _flip(client_with_db, case_id, "arrange_tow", "done", actor="person-may")
    chain = await _flip(client_with_db, case_id, "arrange_tow", "pending", actor="person-tom")

    tow = next(item for item in chain["items"] if item["item_key"] == "arrange_tow")
    assert tow["status"] == "pending"
    assert tow["actor"] == "person-tom", "the latest flip names who last touched it"

    from sqlalchemy import select

    from services.db.repair_case_task import RepairCaseTaskEvent

    rows = list(
        (
            await db_session.execute(
                select(RepairCaseTaskEvent).where(RepairCaseTaskEvent.case_id == case_id)
            )
        ).scalars()
    )
    assert len(rows) == 3, "an append-only trail keeps the correction AND what it corrected"
    assert {row.actor for row in rows} == {"person-may", "person-tom"}


# --------------------------------------------------------------------------- #
# The wall clock stepping backwards between two flips of the SAME item
#
# PLAN-0099 measured this box's ``datetime.now(UTC)`` stepping BACKWARDS 20 times
# per 300 s, every step >= 400 ms. ``chain_state`` reduced flip rows to "current
# state" by sorting on that clock, so a backward step between two flips of one
# item made the SUPERSEDED flip win. The ``event_id`` tiebreak never rescued it:
# ``at`` is the leading key, so on an inversion the tiebreak is not even consulted
# — and ``event_id`` is ``uuid4``-derived anyway, so on an exact tie it is a coin
# flip rather than a tiebreak.
#
# Both cases below FORCE the inversion rather than wait for it (PLAN-0099 D5): at
# ~0.9 % per vulnerable window a happy-path test passes 99.1 % of the time and
# proves nothing. Both drive the real HTTP writer into the real sweep.
# --------------------------------------------------------------------------- #


async def test_a_finished_step_is_not_nudged_when_the_clock_stepped_back(
    client_with_db: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """เมย์ confirms the garage — and the clock lies about when she did it.

    The garage call is activated, then confirmed done a moment later while the wall
    clock happens to step backwards. Reducing "current state" on that clock puts the
    ``pending`` row last and the chain reports work that is FINISHED as outstanding
    — so the sweep nudges เมย์ about a step she already completed, forever, every
    time it runs. That is the partner's stated pilot-killer
    ("เดี๋ยวคนปิดแจ้งเตือนหมด") reached by arithmetic rather than by a wrong rule.

    RED before the fix: ``stale_found == 1`` and a push naming แจ้งอู่.
    """
    clock = Clock(_T0)
    monkeypatch.setattr(cases_router, "datetime", clock.datetime_class())

    case_id = await _open_breakdown_case(client_with_db, truck_id="truck-71")
    await _flip(client_with_db, case_id, "notify_garage", "pending")
    clock.back(milliseconds=500)
    chain = await _flip(client_with_db, case_id, "notify_garage", "done")

    assert clock.calls > 0, (
        "the clock was never consulted — the patch missed the module that stamps "
        "``at``, and every assertion below would pass without forcing anything"
    )
    garage = next(item for item in chain["items"] if item["item_key"] == "notify_garage")
    assert garage["status"] == "done", (
        "the LAST flip เมย์ made is the current state; a backward clock step is the "
        "clock being wrong about when, never the operator being wrong about what"
    )

    recorder = _Recorder()
    report = await sweep_stale_tasks(
        db_session, now=_T0 + timedelta(minutes=40), transport=recorder.transport()
    )
    assert report.stale_found == 0, "a completed step is not outstanding work"
    assert recorder.pushes == [], "nudging about finished work is how the channel gets muted"


async def test_a_reopened_step_is_still_chased_when_the_clock_stepped_back(
    client_with_db: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The same inversion the other way round — and this one fails SILENTLY.

    เมย์ marks the tow done, then reopens it because the truck is still on the road
    (the correction flow ``test_the_append_only_trail_keeps_every_flip_and_its_actor``
    already covers on a well-behaved clock). With the clock stepping back between the
    two flips, the reduced state reports ``done`` and the truck simply stops being
    chased — no nudge, no error, nothing on any screen to notice.

    Worth pinning separately from its sibling: the over-nudge case announces itself
    to a human within a day, this one is only ever discovered by a truck sitting in a
    yard that nobody is asking about.

    RED before the fix: ``stale_found == 0`` and no push.
    """
    clock = Clock(_T0)
    monkeypatch.setattr(cases_router, "datetime", clock.datetime_class())

    case_id = await _open_breakdown_case(client_with_db, truck_id="truck-72")
    await _flip(client_with_db, case_id, "arrange_tow", "done", actor="person-may")
    clock.back(milliseconds=500)
    chain = await _flip(client_with_db, case_id, "arrange_tow", "pending", actor="person-tom")

    assert clock.calls > 0, "the clock was never consulted — the patch missed the stamping module"
    tow = next(item for item in chain["items"] if item["item_key"] == "arrange_tow")
    assert tow["status"] == "pending", "the reopen is the operator's latest word on the tow"
    assert tow["actor"] == "person-tom", "and it names who reopened it, not who closed it"

    recorder = _Recorder()
    report = await sweep_stale_tasks(
        db_session, now=_T0 + timedelta(hours=2), transport=recorder.transport()
    )
    assert report.stale_found == 1, "a reopened tow is outstanding work past its 1-hour SLA"
    assert "จัดหารถยก" in recorder.texts[0]
    assert "truck-72" in recorder.texts[0]


async def test_an_unknown_checklist_item_is_refused(client_with_db: AsyncClient) -> None:
    """The chain is authored config, not free text.

    A typo'd or invented key must not create a row the config cannot price — it would
    sit in the table forever, invisible to every SLA and to every nudge.
    """
    case_id = await _open_breakdown_case(client_with_db, truck_id="truck-61")
    response = await client_with_db.post(
        f"/api/cases/{case_id}/tasks",
        json={"item_key": "wash_the_truck", "status": "pending"},
    )
    assert response.status_code == 422
    assert "wash_the_truck" in response.text
