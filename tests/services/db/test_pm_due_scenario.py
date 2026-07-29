"""``pm_due`` driven by a REAL fired 06:00 round (PLAN-0096 AC-8, amended 2026-07-29).

**This is the CLAUDE.md §8 scenario test for the sixth LINE event.** Nothing here
hand-writes the due set: the real ``scheduled_pm_service_round`` fires through the
real scheduler, the real evaluate step bands each truck against its own
``next_service_due_km``, the run is persisted, and the producer reads the verdicts
back off that persisted run to build the real LINE push.

That is the point. A unit suite feeding the producer a ``{"plates": [...]}`` dict
would prove the message formats — and prove nothing about whether the set it names
is the set the engine actually found due, which is the only property that matters
when a mechanic reads it at 06:00 and drives to the yard.

Fakes are the two CLAUDE.md §8 permits: an injected transport (no socket, AC-11)
and the scheduler's injected clock.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx
import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from services.api.config import settings
from services.db.base import Base
from services.db.pm_due_notify import notify_pm_due_for_run
from services.engine.procedures.scheduler import FireResult, fire_due_schedules
from services.engine.procedures.scheduler_wiring import build_resolver, sync_schedule_states
from services.engine.procedures.schedules import ScheduleState
from services.engine.procedures.spec import load_procedures
from services.engine.registry import registry
from services.notify.line import reset_cooldown
from tests.db_support import create_test_engine

_VERTICAL = "fleet_maintenance"
_PROC_ID = "scheduled_pm_service_round"

_MECHANICS_ID = "Cmechanics_group_00000000000000000"
_OWNER_ID = "Uowner_pmdue_000000000000000000000"

BKK = ZoneInfo("Asia/Bangkok")
EPOCH = datetime(2026, 7, 1, 0, 0, tzinfo=UTC)
SLOT = datetime(2026, 7, 7, 6, 0, tzinfo=BKK)
NOW = datetime(2026, 7, 7, 6, 30, tzinfo=BKK)


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


@pytest.fixture
async def session(db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as s:
        yield s


@pytest.fixture
async def fleet_registered() -> AsyncIterator[None]:
    """Register exactly what the live daemon registers (PLAN-0090's lesson)."""
    from services.engine.discovery import discover_and_register
    from verticals.fleet_maintenance.procedures_factory import (
        register_fleet_maintenance_procedure_executors,
    )

    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    yield


@pytest.fixture(autouse=True)
def _armed_line(monkeypatch: pytest.MonkeyPatch) -> None:
    """Arm LINE with a mechanics group AND an owner, so a message reaching the wrong
    inbox is visible rather than indistinguishable."""
    monkeypatch.setattr(settings, "line_notify_enabled", True)
    monkeypatch.setattr(settings, "line_channel_access_token", "test-token")
    monkeypatch.setattr(
        settings,
        "line_recipients",
        json.dumps({"mechanics": _MECHANICS_ID, "owner": _OWNER_ID}),
    )
    monkeypatch.setattr(settings, "line_notify_cooldown_s", 0)
    reset_cooldown()


class _Recorder:
    def __init__(self) -> None:
        self.pushes: list[dict[str, Any]] = []

    def transport(self) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            self.pushes.append(json.loads(request.content))
            return httpx.Response(200, json={})

        return httpx.MockTransport(handler)


async def _fire_the_morning_round(session: AsyncSession) -> str:
    """Arm the 06:00 slot and fire it for real; return the run id."""
    spec = load_procedures(_VERTICAL)
    resolve = build_resolver(spec, registry.get_procedure_executors(_VERTICAL))
    rows = await sync_schedule_states(session, spec, now=EPOCH)
    state: ScheduleState = rows[0]
    state.next_fire = SLOT
    await session.commit()

    [outcome] = await fire_due_schedules(session, [state], now=NOW, resolve=resolve)
    assert outcome.result is FireResult.FIRED
    assert outcome.run_id
    return str(outcome.run_id)


# --------------------------------------------------------------------------- #


async def test_the_trucks_the_engine_banded_due_are_the_trucks_the_push_names(
    session: AsyncSession, fleet_registered: None
) -> None:
    """The seam: engine verdicts in, LINE message out, nothing retyped in between.

    The synthetic fleet has three trucks and exactly one is past its own service
    point, so this is discriminating in both directions — a producer that announced
    every truck, or none, fails.

    If the evaluate step ever renames its verdict, moves the plate off the row, or
    the producer reads the wrong step, the message goes out naming the wrong trucks
    (or no trucks) and every unit test still passes. That is the failure this exists
    to make impossible.
    """
    run_id = await _fire_the_morning_round(session)

    # The engine's own verdicts — read here only to state what the push MUST match,
    # never to build it.
    from services.engine.procedures.persistence import load_run

    loaded = await load_run(session, run_id)
    assert loaded is not None
    judge = next(sr for sr in loaded.step_results if sr.step_id == "judge_service_due")
    assert judge.artifact is not None
    due_rows = [r for r in judge.artifact["output_set"] if r["verdict"] == "breach"]
    assert len(due_rows) == 1, "the synthetic fleet has exactly one truck past its due point"

    recorder = _Recorder()
    delivery = await notify_pm_due_for_run(session, run_id, transport=recorder.transport())

    assert delivery is not None
    assert delivery.sent_to == ("mechanics",), "PM rounds go to กลุ่มช่าง (A3), nobody else"
    assert len(recorder.pushes) == 1, "one message for the whole round, not one per truck"
    push = recorder.pushes[0]
    assert push["to"] == _MECHANICS_ID
    body = push["messages"][0]["text"]

    expected_plate = due_rows[0].get("plate") or due_rows[0].get("truck_id")
    assert str(expected_plate) in body, (
        "the push must name the truck the ENGINE banded due — not one the producer "
        "re-derived from odometers on its own"
    )
    assert "ถึงกำหนดเข้าศูนย์ 1 คัน" in body


async def test_a_truck_the_engine_called_ok_is_never_announced(
    session: AsyncSession, fleet_registered: None
) -> None:
    """The other direction, and the more expensive mistake.

    Sending a mechanic to fetch a truck that is not due wastes a morning and teaches
    the group that the channel is wrong — after which the one that IS due gets
    ignored too. The message must name the due set exactly, not a superset.
    """
    run_id = await _fire_the_morning_round(session)

    from services.engine.procedures.persistence import load_run

    loaded = await load_run(session, run_id)
    assert loaded is not None
    judge = next(sr for sr in loaded.step_results if sr.step_id == "judge_service_due")
    assert judge.artifact is not None
    not_due = [r for r in judge.artifact["output_set"] if r["verdict"] != "breach"]
    assert not_due, "the fixture must contain trucks that are NOT due for this to discriminate"

    recorder = _Recorder()
    await notify_pm_due_for_run(session, run_id, transport=recorder.transport())
    body = recorder.pushes[0]["messages"][0]["text"]

    for row in not_due:
        plate = row.get("plate") or row.get("truck_id")
        assert str(plate) not in body, f"{plate} is not due — announcing it burns the channel"


async def test_a_round_with_nothing_due_says_nothing_at_all(
    session: AsyncSession, fleet_registered: None
) -> None:
    """Silence is the correct output on a quiet morning.

    A daily "0 trucks due" push is exactly the noise the partner warned about
    ("เดี๋ยวคนปิดแจ้งเตือนหมด"). Proven by driving a REAL run and then removing the
    due verdicts from what the producer reads, rather than by calling the producer
    with an empty list — the empty-list call would not prove the producer looks at
    the run at all.
    """
    run_id = await _fire_the_morning_round(session)

    from services.engine.procedures.persistence import load_run
    from services.engine.procedures.runs import StepResult

    loaded = await load_run(session, run_id)
    assert loaded is not None
    judge = next(sr for sr in loaded.step_results if sr.step_id == "judge_service_due")
    assert judge.artifact is not None
    cleared = {
        **judge.artifact,
        "output_set": [{**row, "verdict": "ok"} for row in judge.artifact["output_set"]],
    }
    await session.execute(
        sa.update(StepResult)
        .where(StepResult.run_id == run_id, StepResult.step_id == "judge_service_due")
        .values(artifact=cleared)
    )
    await session.commit()

    recorder = _Recorder()
    delivery = await notify_pm_due_for_run(session, run_id, transport=recorder.transport())

    assert delivery is None
    assert recorder.pushes == []


async def test_an_unknown_run_is_survivable(session: AsyncSession) -> None:
    """A notification is best-effort and must never raise into the caller — the run
    it is reacting to has already been recorded, and unwinding that to report a
    missing row would trade a real outcome for a cosmetic one."""
    recorder = _Recorder()
    assert (
        await notify_pm_due_for_run(session, "no-such-run", transport=recorder.transport()) is None
    )
    assert recorder.pushes == []
