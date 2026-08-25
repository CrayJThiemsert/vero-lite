"""The LINE seam, fed by REAL engine output — not by hand-written dicts (PLAN-0096).

Cray, session 187: the Step 7 suite proves the notify seam behaves. It proves nothing
about whether the seam and the ENGINE agree, because every one of its cases feeds a
``_DETAIL`` dict the test author wrote. If the DOA ladder resolves an approver role
spelled one way and the recipient map is keyed another, all 24 of those tests stay
green and the pilot's first real approval request goes nowhere.

That is the failure this module exists to make impossible. Each case takes output the
engine ACTUALLY produced — a persisted ``doa_tier`` verdict, a persisted ratification
audit block — and drives the notify seam with it.

DB-backed for the provisional case (it needs a real gate resolution); the approval-
routing case runs in memory, because the ladder's verdict is on the step result before
anything is persisted.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.api.config import settings
from services.db.base import Base
from services.engine.discovery import discover_and_register
from services.engine.procedures.action_step import WaiverInvocation, resolve_gated_step
from services.engine.procedures.orchestrator import run_procedure
from services.engine.procedures.persistence import persist_run
from services.engine.procedures.ratification import RATIFICATION_KEY, ratification_state
from services.engine.procedures.runs import PipelineRunStatus, StepResultStatus
from services.engine.procedures.spec import Person, load_procedures
from services.engine.registry import ExecutorFactory, registry
from services.notify.line import LineEvent, build_message, notify, reset_cooldown
from tests.db_support import create_test_engine, drop_all_bounded
from verticals.fleet_maintenance.procedures_factory import (
    register_fleet_maintenance_procedure_executors,
)

_VERTICAL = "fleet_maintenance"
_HERO = "governed_repair_approval"
_GATE = "approve"
_MECHANIC = "req-mechanic-tom"

#: Distinct destinations per role, so a test that passed by everything landing in one
#: inbox is not possible.
_OWNER_TIER_ID = "Uowner_tier_00000000000000000000"
_MANAGER_TIER_ID = "Umanager_tier_0000000000000000000"
_OWNER_ID = "Uowner_person_000000000000000000"
_OPERATOR_ID = "Uoperator_00000000000000000000000"


@pytest.fixture(autouse=True)
def _armed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Arm LINE with a recipient map keyed by the vertical's OWN authored role names."""
    monkeypatch.setattr(settings, "line_notify_enabled", True)
    monkeypatch.setattr(settings, "line_channel_access_token", "test-token")
    monkeypatch.setattr(
        settings,
        "line_recipients",
        json.dumps(
            {
                "เจ้าของกิจการ": _OWNER_TIER_ID,
                "ผจก.เดินรถ": _MANAGER_TIER_ID,
                "owner": _OWNER_ID,
                "operator": _OPERATOR_ID,
            }
        ),
    )
    reset_cooldown()


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    eng = await create_test_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await drop_all_bounded(conn)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))
    await eng.dispose()


@pytest.fixture
async def fleet_factory(monkeypatch: pytest.MonkeyPatch) -> ExecutorFactory:
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    return registry.get_procedure_executors(_VERTICAL)


def _person(person_id: str) -> Person:
    return next(p for p in load_procedures(_VERTICAL).principals if p.person_id == person_id)


def _hero_bits() -> tuple[Any, Any]:
    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == _HERO)
    return proc, next(a for a in spec.agents if a.agent_id == proc.run_by)


class _Recorder:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def transport(self):  # type: ignore[no-untyped-def]  # httpx.MockTransport
        import httpx

        def handler(request: httpx.Request) -> httpx.Response:
            self.calls.append(json.loads(request.content))
            return httpx.Response(200, json={})

        return httpx.MockTransport(handler)


# --------------------------------------------------------------------------- #


async def test_the_role_the_ladder_resolves_is_a_role_the_notify_map_can_key_on(
    fleet_factory: ExecutorFactory,
) -> None:
    """The seam and the engine must share one vocabulary — proved, not assumed.

    The hero run carries TWO breaches that resolve to DIFFERENT rungs, so this is not a
    single-value coincidence: ฿48,000 resolves to ``เจ้าของกิจการ`` and ฿15,000 to
    ``ผจก.เดินรถ``. Both role strings come straight off the PERSISTED ``doa_tier``
    verdict the governance executor wrote — nothing here retypes them — and each must
    route to its own distinct destination.

    If the ladder ever renames a role, or the notify map is keyed on ``person_id``
    instead of role, or the audit key changes from ``required_role``, this fails. The
    Step 7 suite would not: it feeds a dict that agrees with itself by construction.
    """
    proc, agent = _hero_bits()
    result = await run_procedure(
        proc, agent, fleet_factory(), vertical=_VERTICAL, run_id="wiring-approval"
    )
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value

    gate = next(sr for sr in result.step_results if sr.step_id == _GATE)
    assert gate.audit is not None
    verdicts = gate.audit["doa_tier"]
    assert len(verdicts) == 2, "the two-rung run is what makes this discriminating"

    routed: dict[str, str] = {}
    for verdict in verdicts:
        role = verdict["required_role"]  # the engine's own spelling, not ours
        recorder = _Recorder()
        delivery = await notify(
            LineEvent.APPROVAL_NEEDED,
            {
                "truck": verdict.get("resolved_approver_id"),
                "amount_thb": float(verdict["amount"]["value"]),
                "approver_role": role,
            },
            resolved_approver=role,
            transport=recorder.transport(),
        )
        assert delivery.unmapped == (), (
            f"the ladder resolved role {role!r} but the notify map cannot key on it — "
            "the engine and the channel disagree about what a role is called"
        )
        assert delivery.sent_to == (role,)
        routed[role] = recorder.calls[0]["to"]

    assert routed == {
        "เจ้าของกิจการ": _OWNER_TIER_ID,
        "ผจก.เดินรถ": _MANAGER_TIER_ID,
    }, "each rung must reach its OWN approver — one shared inbox is the bottleneck again"


async def test_the_approval_push_carries_the_run_s_own_figures(
    fleet_factory: ExecutorFactory,
) -> None:
    """The body a person reads is built from what the run actually decided.

    ฿48,000 is the breach quote the synthetic feed produced and the ladder routed on;
    a body showing anything else would send the owner to approve a number nobody
    computed."""
    proc, agent = _hero_bits()
    result = await run_procedure(
        proc, agent, fleet_factory(), vertical=_VERTICAL, run_id="wiring-body"
    )
    gate = next(sr for sr in result.step_results if sr.step_id == _GATE)
    assert gate.audit is not None
    owner_verdict = next(v for v in gate.audit["doa_tier"] if v["required_role"] == "เจ้าของกิจการ")

    text = build_message(
        LineEvent.APPROVAL_NEEDED,
        {
            "truck": "80-1234 กรุงเทพมหานคร",
            "amount_thb": float(owner_verdict["amount"]["value"]),
            "approver_role": owner_verdict["required_role"],
        },
    )

    assert "฿48,000" in text
    assert "เจ้าของกิจการ" in text


async def test_a_real_provisional_resolution_drives_the_overdue_reminder(
    db_engine: AsyncEngine, fleet_factory: ExecutorFactory
) -> None:
    """The reminder is built from the obligation the ENGINE wrote, end to end.

    A real waiver-invoked resolution persists a ``ratification`` audit block. This case
    reads that block back, computes its state with an injected clock past the deadline,
    and builds the LINE body from those values — the same path the Step 6/8 producers
    will take.

    The failure it guards is quiet and expensive: if ``ratification_state`` reported
    ``pending`` past the deadline, or the block's ``due_at`` were stored in a shape the
    body cannot render, the owner would simply never be chased about an unsigned
    ฿48,000 repair. Nothing else in the suite would notice — the ratification matrix
    checks the state machine, the notify suite checks the channel, and neither one
    connects them.
    """
    proc, agent = _hero_bits()
    result = await run_procedure(
        proc,
        agent,
        fleet_factory(),
        vertical=_VERTICAL,
        run_id="wiring-overdue",
        principal=_person(_MECHANIC),
    )
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        await persist_run(session, result)
    gate = next(sr for sr in result.step_results if sr.step_id == _GATE)
    assert gate.artifact is not None
    action_ids = [str(p["action_id"]) for p in gate.artifact["output_set"]]

    async with maker() as session:
        target = await resolve_gated_step(
            session,
            "wiring-overdue",
            _GATE,
            dict.fromkeys(action_ids, "approve"),
            _person(_MECHANIC),
            procedure=proc,
            principals=list(load_procedures(_VERTICAL).principals),
            waiver_invocation=WaiverInvocation(
                justification="เพลาขาดที่ปากช่อง โทรหาเฮียแล้วเคาะให้ซ่อมเลย"
            ),
        )
    assert target.status == StepResultStatus.RESOLVED_PROVISIONAL.value

    block = target.audit[RATIFICATION_KEY]
    due_at = datetime.fromisoformat(block["due_at"])
    view = ratification_state(target.audit, due_at + timedelta(days=1))
    assert view.state == "overdue", "one day past the authored window"
    assert view.is_outstanding

    recorder = _Recorder()
    delivery = await notify(
        LineEvent.RATIFICATION_OVERDUE,
        {
            "truck": "80-1234 กรุงเทพมหานคร",
            "amount_thb": 48000,
            "due_at": due_at.date().isoformat(),
        },
        transport=recorder.transport(),
    )

    assert set(delivery.sent_to) == {"owner", "operator"}
    body = recorder.calls[0]["messages"][0]["text"]
    assert due_at.date().isoformat() in body, (
        "the reminder must quote the deadline the ENGINE computed, not one the " "notifier invented"
    )
    assert "฿48,000" in body
    assert "เลยกำหนดลงนาม" in body


async def test_a_ratified_obligation_stops_producing_reminders(
    db_engine: AsyncEngine, fleet_factory: ExecutorFactory
) -> None:
    """The other end of the same wire, and the one that decides whether the channel
    stays trusted.

    Once the owner signs, ``ratification_state`` must stop reporting the obligation as
    outstanding — because a reminder that keeps arriving after the thing is done is how
    people learn to ignore the channel entirely, and this pilot has exactly one
    outbound surface to spend."""
    proc, agent = _hero_bits()
    result = await run_procedure(
        proc,
        agent,
        fleet_factory(),
        vertical=_VERTICAL,
        run_id="wiring-ratified",
        principal=_person(_MECHANIC),
    )
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        await persist_run(session, result)
    gate = next(sr for sr in result.step_results if sr.step_id == _GATE)
    assert gate.artifact is not None
    action_ids = [str(p["action_id"]) for p in gate.artifact["output_set"]]

    async with maker() as session:
        provisional = await resolve_gated_step(
            session,
            "wiring-ratified",
            _GATE,
            dict.fromkeys(action_ids, "approve"),
            _person(_MECHANIC),
            procedure=proc,
            principals=list(load_procedures(_VERTICAL).principals),
            waiver_invocation=WaiverInvocation(justification="เฮียเคาะทางโทรศัพท์"),
        )
    assert ratification_state(provisional.audit, datetime.now(UTC)).is_outstanding

    from services.engine.procedures.action_step import ratify_gated_step

    async with maker() as session:
        ratified = await ratify_gated_step(
            session,
            "wiring-ratified",
            _GATE,
            _person("appr-owner"),
            procedure=proc,
            principals=list(load_procedures(_VERTICAL).principals),
        )

    view = ratification_state(ratified.audit, datetime.now(UTC) + timedelta(days=30))
    assert view.state == "ratified"
    assert not view.is_outstanding, (
        "a signed obligation must never look outstanding again, even long past the "
        "original deadline — otherwise the overdue sweep re-pushes it forever"
    )
