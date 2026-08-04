"""The task-chain SLA rules, cased on the partner's OWN narrative (PLAN-0096 Step 6 / AC-7).

Every case here is a sentence from round-2 answer A1 turned into an assertion. The
staleness rule is the only thing in Step 6 a human never sees until it misfires:
nobody notices a nudge that did not fire, and everybody notices the ones that fire
wrongly — after which they mute the channel, which is the partner's own stated fear
("ผมไม่อยากให้ทุกอย่างเด้งเข้ากลุ่มเดียว เดี๋ยวคนปิดแจ้งเตือนหมด") and the end of
the pilot's single outbound surface.

Pure + in-memory on purpose: these pin the RULE. The wiring — real API writes, a
real database, the real notify seam — is proven separately in
``tests/api/test_task_chain_scenario.py`` (CLAUDE.md §8), because a rule suite and
a wiring suite fail for different reasons and a suite that mixes them tells you
which only by accident.

Measured, not asserted: with the router mutated to write a status string the chain
does not recognise, all 17 cases here stayed GREEN and 5 of the 8 scenario cases
went RED. That is the seam class §8 exists for, and the reason both suites exist.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from services.db.repair_case import WORK_TYPE_BREAKDOWN, WORK_TYPE_PM
from services.db.repair_case_task import (
    TASK_STATUS_DONE,
    TASK_STATUS_PENDING,
    TASK_STATUS_SKIPPED,
    RepairCaseTaskEvent,
)
from verticals.fleet_maintenance.task_chain import (
    TASK_CHAIN,
    chain_state,
    item_spec,
    sla_for,
    stale_items,
)

_T0 = datetime(2026, 7, 29, 8, 0, tzinfo=UTC)

_counter = iter(range(1, 10_000))


def _flip(
    item_key: str,
    status: str,
    *,
    at: datetime,
    actor: str = "person-may",
    variant: str | None = None,
    seq: int | None = None,
) -> RepairCaseTaskEvent:
    """One flip row. ``seq`` defaults to CREATION order — the reduction key.

    These objects are never persisted, so the database cannot assign ``seq`` and the
    builder must. Defaulting it to creation order is what the cases below already
    meant: every one lists its flips in the order they happened, and the same-instant
    ties (four events at ``_T0`` is a normal shape here) already resolved by the
    ascending ``ev-NNNN`` counter, so this reproduces their existing answers exactly
    rather than re-interpreting them.

    Pass ``seq`` explicitly to express an insertion order that DISAGREES with ``at`` —
    the wall-clock-stepped-backwards case (migration ``0025``).
    """
    ordinal = next(_counter)
    return RepairCaseTaskEvent(
        event_id=f"ev-{ordinal:04d}",
        case_id="case-test",
        item_key=item_key,
        status=status,
        actor=actor,
        at=at,
        variant=variant,
        seq=ordinal if seq is None else seq,
    )


def _keys(items: list) -> set[str]:
    return {item.key for item in items}


# --------------------------------------------------------------------------- #
# The chain itself matches what the partner described
# --------------------------------------------------------------------------- #


def test_the_chain_is_the_partner_s_eight_steps_four_of_them_mandatory() -> None:
    """A1's table, structurally. Guards against a later edit quietly dropping a
    step or promoting a conditional one — the item set is a partner-confirmed
    fact, not a developer preference."""
    assert [spec.key for spec in TASK_CHAIN] == [
        "notify_garage",
        "arrange_tow",
        "arrange_cargo_transfer",
        "order_parts",
        "wait_parts",
        "start_repair",
        "test_drive",
        "close_case",
    ]
    assert {spec.key for spec in TASK_CHAIN if spec.mandatory} == {
        "notify_garage",
        "start_repair",
        "test_drive",
        "close_case",
    }


# --------------------------------------------------------------------------- #
# SLA resolution — A1's two context variants
# --------------------------------------------------------------------------- #


def test_notify_garage_is_half_an_hour_on_a_breakdown_but_a_day_on_pm() -> None:
    """A1: "30 นาที (รถเสียกลางทาง), 1 วัน (PM)".

    The most consequential threshold in the chain: a truck stopped on the road is
    losing money by the minute, while a PM booking that takes a day is normal. One
    shared timeout would have to pick one, and either choice is wrong half the time.
    """
    spec = item_spec("notify_garage")
    assert sla_for(spec, work_type=WORK_TYPE_BREAKDOWN, variant=None) == timedelta(minutes=30)
    assert sla_for(spec, work_type=WORK_TYPE_PM, variant=None) == timedelta(days=1)


def test_a_major_part_buys_five_days_of_waiting_instead_of_two() -> None:
    """A1: "2 วัน (ของทั่วไป), 5 วัน (อะไหล่ใหญ่)" — the flip-time variant wins."""
    spec = item_spec("wait_parts")
    assert sla_for(spec, work_type=WORK_TYPE_BREAKDOWN, variant=None) == timedelta(days=2)
    assert sla_for(spec, work_type=WORK_TYPE_BREAKDOWN, variant="major_part") == timedelta(days=5)


def test_the_variant_outranks_the_work_type() -> None:
    """Only the flipping human knows a part is a big one; only the case knows it is
    PM. When both speak, the more specific fact wins — otherwise a PM case ordering
    an engine part would silently inherit the PM relaxation on the wrong item."""
    spec = item_spec("wait_parts")
    assert sla_for(spec, work_type=WORK_TYPE_PM, variant="major_part") == timedelta(days=5)


# --------------------------------------------------------------------------- #
# The anchor rule (Cray, typed — prerequisite-complete)
# --------------------------------------------------------------------------- #


def test_start_repair_is_not_stale_while_the_parts_are_legitimately_still_coming() -> None:
    """THE case the anchor rule exists for. A1 prices เริ่มซ่อม at "1 วันหลังของครบ".

    A major part is 5 days out and the case is on day 4: the repair has not started,
    and that is correct, not late. An activation-anchored clock would have been
    nudging เมย์ since day 2 about a truck nobody can work on yet.
    """
    events = [
        _flip("notify_garage", TASK_STATUS_DONE, at=_T0),
        _flip("order_parts", TASK_STATUS_DONE, at=_T0),
        _flip("wait_parts", TASK_STATUS_PENDING, at=_T0, variant="major_part"),
        _flip("start_repair", TASK_STATUS_PENDING, at=_T0),
    ]
    stale = stale_items(events, work_type=WORK_TYPE_BREAKDOWN, now=_T0 + timedelta(days=4))
    assert "start_repair" not in _keys(stale), (
        "the repair cannot start until the parts land — nudging about it is noise, "
        "and noise is how the one channel gets muted"
    )
    assert "wait_parts" not in _keys(stale), "day 4 of a 5-day major-part wait is fine"


def test_the_wait_itself_goes_stale_once_its_own_five_days_run_out() -> None:
    """Day 6 of a 5-day wait: nobody has chased the supplier. THIS is the nudge."""
    events = [
        _flip("order_parts", TASK_STATUS_DONE, at=_T0),
        _flip("wait_parts", TASK_STATUS_PENDING, at=_T0, variant="major_part"),
    ]
    stale = stale_items(events, work_type=WORK_TYPE_BREAKDOWN, now=_T0 + timedelta(days=6))
    assert "wait_parts" in _keys(stale)


def test_start_repair_goes_stale_a_day_after_the_parts_actually_arrive() -> None:
    """The other half of "1 วันหลังของครบ" — the clock DOES start, at parts-complete.

    Parts land on day 5; on day 6.5 the repair still has not begun. Anchoring to
    case-open would have burned this nudge days ago, on a case that was behaving.
    """
    parts_in = _T0 + timedelta(days=5)
    events = [
        _flip("notify_garage", TASK_STATUS_DONE, at=_T0),
        _flip("order_parts", TASK_STATUS_DONE, at=_T0),
        _flip("wait_parts", TASK_STATUS_PENDING, at=_T0, variant="major_part"),
        _flip("wait_parts", TASK_STATUS_DONE, at=parts_in),
        _flip("start_repair", TASK_STATUS_PENDING, at=_T0),
    ]
    assert "start_repair" not in _keys(
        stale_items(events, work_type=WORK_TYPE_BREAKDOWN, now=parts_in + timedelta(hours=12))
    )
    stale = stale_items(
        events, work_type=WORK_TYPE_BREAKDOWN, now=parts_in + timedelta(days=1, hours=12)
    )
    assert "start_repair" in _keys(stale)


def test_a_case_that_never_ordered_parts_anchors_on_the_garage_call() -> None:
    """A1: "บางเคสเปลี่ยนแบต เปลี่ยนยาง จบในหน้างาน" — no parts step ever exists.

    The prerequisite is ABSENT, not pending. If absence were treated as
    "not settled", เริ่มซ่อม would have no clock at all and could sit forever
    without a nudge — the failure nobody would ever observe.
    """
    events = [
        _flip("notify_garage", TASK_STATUS_DONE, at=_T0),
        _flip("start_repair", TASK_STATUS_PENDING, at=_T0),
    ]
    stale = stale_items(events, work_type=WORK_TYPE_BREAKDOWN, now=_T0 + timedelta(days=2))
    assert "start_repair" in _keys(stale)


def test_a_skipped_prerequisite_counts_as_settled() -> None:
    """A1: "บางเคสซ่อมที่อู่เลย ไม่ต้องรถยก". Skipped is a human's answer, not a gap —
    it must release the next step's clock exactly as ``done`` does."""
    events = [
        _flip("notify_garage", TASK_STATUS_DONE, at=_T0),
        _flip("order_parts", TASK_STATUS_SKIPPED, at=_T0),
        _flip("start_repair", TASK_STATUS_PENDING, at=_T0),
    ]
    stale = stale_items(events, work_type=WORK_TYPE_BREAKDOWN, now=_T0 + timedelta(days=2))
    assert "start_repair" in _keys(stale)


def test_an_item_added_after_its_prerequisite_finished_is_not_born_overdue() -> None:
    """เมย์ adds ทดลองวิ่ง two days after the repair finished — measured from when it
    ENTERED the chain, not from a completion that predates it. Without the
    ``max(..., activated_at)`` guard the item would arrive already stale and fire a
    nudge for a task nobody had been given yet."""
    repair_done = _T0
    added_late = _T0 + timedelta(days=2)
    events = [
        _flip("start_repair", TASK_STATUS_DONE, at=repair_done),
        _flip("test_drive", TASK_STATUS_PENDING, at=added_late),
    ]
    assert "test_drive" not in _keys(
        stale_items(events, work_type=WORK_TYPE_BREAKDOWN, now=added_late + timedelta(hours=12))
    )
    assert "test_drive" in _keys(
        stale_items(
            events, work_type=WORK_TYPE_BREAKDOWN, now=added_late + timedelta(days=1, hours=1)
        )
    )


# --------------------------------------------------------------------------- #
# What must never be nudged about
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("settled", [TASK_STATUS_DONE, TASK_STATUS_SKIPPED])
def test_a_settled_item_never_goes_stale_however_long_ago_it_was(settled: str) -> None:
    """The muting failure, direct: an item a human already answered must never
    produce another nudge — not on day 30, not ever."""
    events = [_flip("notify_garage", settled, at=_T0)]
    assert stale_items(events, work_type=WORK_TYPE_BREAKDOWN, now=_T0 + timedelta(days=30)) == []


def test_an_item_the_case_never_activated_is_not_stale() -> None:
    """A PM case with all four conditional items absent is a NORMAL complete case
    (A1: "PM ส่วนใหญ่ข้ามรถยกและรถถ่ายของทั้งหมด") — a conditional step nobody added
    must not be reported as outstanding work."""
    events = [_flip("notify_garage", TASK_STATUS_DONE, at=_T0)]
    stale = stale_items(events, work_type=WORK_TYPE_PM, now=_T0 + timedelta(days=10))
    assert _keys(stale).isdisjoint({"arrange_tow", "arrange_cargo_transfer", "order_parts"})


def test_an_item_exactly_at_its_deadline_is_not_yet_stale() -> None:
    """Boundary: "ถ้าค้างเกิน 30 นาที" means past it. At exactly 30 minutes the
    30-minute allowance has been used, not exceeded."""
    events = [_flip("notify_garage", TASK_STATUS_PENDING, at=_T0)]
    assert stale_items(events, work_type=WORK_TYPE_BREAKDOWN, now=_T0 + timedelta(minutes=30)) == []
    assert _keys(
        stale_items(events, work_type=WORK_TYPE_BREAKDOWN, now=_T0 + timedelta(minutes=31))
    ) == {"notify_garage"}


# --------------------------------------------------------------------------- #
# The reducer
# --------------------------------------------------------------------------- #


def test_the_latest_flip_wins_and_the_first_one_records_when_it_started() -> None:
    """Append-only means state is a reduction, and both ends of the trail matter:
    the latest flip is the status, the first is when the clock started."""
    events = [
        _flip("notify_garage", TASK_STATUS_PENDING, at=_T0, actor="person-may"),
        _flip(
            "notify_garage", TASK_STATUS_DONE, at=_T0 + timedelta(minutes=10), actor="person-tom"
        ),
    ]
    state = chain_state(events)["notify_garage"]
    assert state.status == TASK_STATUS_DONE
    assert state.actor == "person-tom"
    assert state.activated_at == _T0


def test_the_reduction_does_not_depend_on_the_order_rows_come_back_in() -> None:
    """A database returns rows in whatever order it likes. If the reducer needed
    them sorted, the chain would report different state depending on the query
    plan — the kind of bug that reproduces only in production."""
    first = _flip("notify_garage", TASK_STATUS_PENDING, at=_T0)
    second = _flip("notify_garage", TASK_STATUS_DONE, at=_T0 + timedelta(minutes=10))
    assert chain_state([second, first]) == chain_state([first, second])


def test_the_reduction_follows_insertion_order_when_the_clock_disagrees() -> None:
    """The rule half of migration ``0025``: ``seq`` decides, ``at`` only reports.

    เมย์ marks the garage call done, and the wall clock happens to step backwards
    (measured on this box at 20 times per 300 s, every step >= 400 ms) so the DONE
    row carries an EARLIER stamp than the PENDING row it supersedes. Sorting on
    ``at`` returns the pending row as though it were her latest word.

    The wiring half — real HTTP writes, real sweep, a real nudge that does or does
    not fire — is ``tests/api/test_task_chain_scenario.py``. This case pins the rule
    on its own so a regression names the reducer rather than the router.
    """
    activated = _flip("notify_garage", TASK_STATUS_PENDING, at=_T0, actor="person-may", seq=1)
    finished = _flip(
        "notify_garage",
        TASK_STATUS_DONE,
        at=_T0 - timedelta(milliseconds=500),
        actor="person-tom",
        seq=2,
    )

    state = chain_state([activated, finished])["notify_garage"]
    assert state.status == TASK_STATUS_DONE, "the later INSERT is current, whatever the clock says"
    assert state.actor == "person-tom"
    assert (
        stale_items(
            [activated, finished], work_type=WORK_TYPE_BREAKDOWN, now=_T0 + timedelta(days=30)
        )
        == []
    ), "and a step reduced to done is never nudged about again"


def test_a_flip_row_without_a_seq_is_refused_rather_than_ordered_on_the_clock() -> None:
    """No silent fallback to ``at`` — that would be the defect wearing a seatbelt.

    ``seq`` is NOT NULL since ``0025``, so a row arriving without one was never
    persisted. Quietly reverting such a row to wall-clock ordering would put a nudge
    decision back on the lying key with nothing downstream able to tell.
    """
    # Built directly rather than through ``_flip``, which always assigns one.
    unpersisted = RepairCaseTaskEvent(
        event_id="ev-no-seq",
        case_id="case-test",
        item_key="notify_garage",
        status=TASK_STATUS_PENDING,
        actor="person-may",
        at=_T0,
    )
    assert unpersisted.seq is None, "the premise: an unflushed row has no database-assigned seq"
    with pytest.raises(ValueError, match="seq"):
        chain_state([unpersisted])


def test_a_variant_set_once_survives_later_flips_that_do_not_repeat_it() -> None:
    """เมย์ marks the part as major when she orders it; the flip that later says it
    arrived carries no variant. The 5-day allowance must not silently revert to 2
    days in between — the case would go stale on a schedule nobody agreed to."""
    events = [
        _flip("wait_parts", TASK_STATUS_PENDING, at=_T0, variant="major_part"),
        _flip("wait_parts", TASK_STATUS_PENDING, at=_T0 + timedelta(days=1)),
    ]
    assert chain_state(events)["wait_parts"].variant == "major_part"
    assert stale_items(events, work_type=WORK_TYPE_BREAKDOWN, now=_T0 + timedelta(days=3)) == []
