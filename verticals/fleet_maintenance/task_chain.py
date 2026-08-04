"""The authored task-chain config — the partner's REAL 8 steps (PLAN-0096 Step 6 / AC-7).

Transcribed from the partner's round-2 answer A1 (2026-07-29,
``docs/research/private/2026-07-29-fleet-partner-intake-round2_reply.md``): the
post-approval chain is 8 steps — 4 that happen on every case and 4 that a human
adds only when the case needs them — each with its OWN "ถ้าค้างเกิน" threshold.
A single timeout for the whole chain was never what he described: a tow truck
that has not moved in an hour is an emergency, a parts order sitting 4 days may
be normal.

**Authored config, not a template UI** (Cray, typed, 2026-07-29): the partner's
dev-suggestion of a partner-editable template system is declined for Phase 1 —
one vertical, one partner, one chain (ADR-006 Rule of Three). Renaming a step or
changing a threshold is an edit to THIS file with provenance, exactly like the
DOA ladder in ``procedures.yaml``.

**What lives where.** The event table (``services/db/repair_case_task.py``)
stores what happened; this module says what it means — which keys exist, which
are mandatory, what each step's SLA is, and what a stale item is. The staleness
sweep and the API both read the chain through :func:`chain_state` /
:func:`stale_items`, so there is exactly one place where "ค้าง" is defined.

SLA resolution order for one item: the flip's ``variant`` (only the flipping
human knows it is a big part) → the case's ``work_type`` (only the case knows it
is PM) → the item's default. Every value below is the partner's own number from
A1's table; none is invented here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from services.db.repair_case_task import (
    TASK_STATUS_DONE,
    TASK_STATUS_PENDING,
    TASK_STATUS_SKIPPED,
    RepairCaseTaskEvent,
)

#: SLA-map keys that are NOT variants: resolution falls through them in order.
_SLA_DEFAULT = "default"


@dataclass(frozen=True)
class TaskItemSpec:
    """One checklist step, as the partner described it.

    ``sla`` maps a context key to that context's "ถ้าค้างเกิน" threshold —
    ``"default"`` plus optional overrides keyed by work_type (``"pm"``) or by a
    flip-supplied variant (``"major_part"``). ``after`` names the steps whose
    completion this step's clock waits for (A1: เริ่มซ่อม is stale "1 วันหลัง
    ของครบ" — a day after the parts are IN, not a day after approval).
    """

    key: str
    label_th: str
    mandatory: bool
    sla: dict[str, timedelta] = field(default_factory=dict)
    after: tuple[str, ...] = ()


#: The chain, in the partner's own order and words (A1's table, verbatim labels).
TASK_CHAIN: tuple[TaskItemSpec, ...] = (
    TaskItemSpec(
        key="notify_garage",
        label_th="แจ้งอู่ / ยืนยันอู่ที่จะซ่อม",
        mandatory=True,
        # A1: 30 นาที (รถเสียกลางทาง), 1 วัน (PM). Accident is not separately
        # priced in his table; it takes the urgent default, not the PM relaxation.
        sla={_SLA_DEFAULT: timedelta(minutes=30), "pm": timedelta(days=1)},
    ),
    TaskItemSpec(
        key="arrange_tow",
        label_th="จัดหารถยก",
        mandatory=False,  # A1: เฉพาะรถวิ่งต่อไม่ได้
        sla={_SLA_DEFAULT: timedelta(hours=1)},
    ),
    TaskItemSpec(
        key="arrange_cargo_transfer",
        label_th="จัดหารถถ่ายของ",
        mandatory=False,  # A1: เฉพาะรถมีสินค้าค้าง
        sla={_SLA_DEFAULT: timedelta(hours=1)},
    ),
    TaskItemSpec(
        key="order_parts",
        label_th="สั่งอะไหล่",
        mandatory=False,  # A1: เฉพาะไม่มีของในสต๊อก
        sla={_SLA_DEFAULT: timedelta(days=1)},
    ),
    TaskItemSpec(
        key="wait_parts",
        label_th="รออะไหล่",
        mandatory=False,  # A1: เฉพาะสั่งของ
        sla={_SLA_DEFAULT: timedelta(days=2), "major_part": timedelta(days=5)},
        after=("order_parts",),
    ),
    TaskItemSpec(
        key="start_repair",
        label_th="เริ่มซ่อม",
        mandatory=True,
        # A1: "1 วันหลังของครบ" — the clock is relative to parts-complete.
        sla={_SLA_DEFAULT: timedelta(days=1)},
        after=("wait_parts", "order_parts", "notify_garage"),
    ),
    TaskItemSpec(
        key="test_drive",
        label_th="ทดลองวิ่ง / ตรวจรับ",
        mandatory=True,
        sla={_SLA_DEFAULT: timedelta(days=1)},
        after=("start_repair",),
    ),
    TaskItemSpec(
        key="close_case",
        label_th="ปิดงาน / เก็บเอกสาร",
        mandatory=True,
        sla={_SLA_DEFAULT: timedelta(days=7)},
        after=("test_drive",),
    ),
)

_BY_KEY: dict[str, TaskItemSpec] = {spec.key: spec for spec in TASK_CHAIN}


def item_spec(key: str) -> TaskItemSpec:
    """The spec for one item key, or KeyError for a key the chain never defined."""
    return _BY_KEY[key]


@dataclass(frozen=True)
class ChainItemState:
    """One item's current state, reduced from its append-only flip rows."""

    key: str
    status: str
    #: When the item entered the chain (its first ``pending`` row).
    activated_at: datetime
    #: When the LATEST flip happened — the "last movement" the staleness clock reads.
    last_flip_at: datetime
    #: Latest non-null variant any flip supplied (e.g. ``major_part``).
    variant: str | None
    actor: str


def _insertion_order(event: RepairCaseTaskEvent) -> int:
    """The reduction key: ``seq``, never the wall clock.

    Raises rather than falling back to ``at`` when ``seq`` is missing. A fallback
    would be the defect wearing a seatbelt: it would restore wall-clock ordering on
    exactly the rows whose provenance we could not confirm, and do it silently — the
    reduced status looks the same either way, and nothing downstream could tell that
    a nudge decision had been made on the lying key. ``seq`` is NOT NULL in the
    schema, so a row reaching here without one was never persisted (a hand-built
    ORM object in a test), and that is a defect in the caller worth a loud failure.
    """
    if event.seq is None:
        raise ValueError(
            f"task event {event.event_id!r} has no seq — 'current status' is reduced on "
            "database insertion order, and a row without one cannot be placed in it. "
            "A persisted row always has seq (NOT NULL since migration 0025); a "
            "hand-built RepairCaseTaskEvent must assign one explicitly."
        )
    return event.seq


def chain_state(events: list[RepairCaseTaskEvent]) -> dict[str, ChainItemState]:
    """Reduce flip rows to per-item current state. Pure; order-insensitive input.

    **"Latest" is database insertion order (``seq``), never ``at``.** ``at`` is a
    Python ``datetime.now(UTC)`` stamp, and this box's clock was measured stepping
    BACKWARDS 20 times per 300 s, every step >= 400 ms (PLAN-0099). Reducing on it
    meant a backward step between two flips of the SAME item made the SUPERSEDED
    flip win — and because this feeds ``stale_items``, the consequence is an
    operational one in both directions: a finished step nudged about forever
    (the muting failure this module exists to avoid), or a reopened step that
    silently stops being chased. The old ``event_id`` tiebreak protected neither:
    ``at`` led the sort, so on an inversion it was never consulted, and it is a
    ``uuid4`` anyway. See migration ``0025``.

    ``at`` is still what the chain REPORTS — ``activated_at`` and ``last_flip_at``
    are the human-facing instants and the SLA arithmetic's inputs. Re-keying fixes
    WHICH row is current; it does not claim the stored instants are exact. Under a
    backward step ``activated_at`` (the first-inserted row's stamp) can sit a few
    hundred milliseconds after ``last_flip_at``, which is the clock being wrong
    about when, against thresholds measured in half-hours and days.
    """
    state: dict[str, ChainItemState] = {}
    for event in sorted(events, key=_insertion_order):
        prior = state.get(event.item_key)
        activated_at = prior.activated_at if prior else event.at
        variant = event.variant if event.variant is not None else (prior.variant if prior else None)
        state[event.item_key] = ChainItemState(
            key=event.item_key,
            status=event.status,
            activated_at=activated_at,
            last_flip_at=event.at,
            variant=variant,
            actor=event.actor,
        )
    return state


def sla_for(spec: TaskItemSpec, *, work_type: str, variant: str | None) -> timedelta:
    """The threshold for one item in one context — variant wins, then work_type."""
    if variant is not None and variant in spec.sla:
        return spec.sla[variant]
    if work_type in spec.sla:
        return spec.sla[work_type]
    return spec.sla[_SLA_DEFAULT]


def _anchor_for(
    spec: TaskItemSpec, item: ChainItemState, state: dict[str, ChainItemState]
) -> datetime | None:
    """When this item's SLA clock starts, or ``None`` if it is not running yet.

    The rule (Cray, typed, 2026-07-29 — "prerequisite-complete", of three options
    weighed): a step with prerequisites starts its clock when the prerequisites
    THIS CASE ACTUALLY HAS are all settled; until then the clock does not run and
    the item cannot be stale.

    Why not simply the item's own activation: A1 prices เริ่มซ่อม at "1 วันหลัง
    ของครบ" — a day after the parts are IN. Anchoring to activation would make
    every repair waiting out a legitimate 5-day major-part order look stale on day
    two, and the resulting nudges are exactly what the partner warned about
    ("ผมไม่อยากให้ทุกอย่างเด้งเข้ากลุ่มเดียว เดี๋ยวคนปิดแจ้งเตือนหมด"). The pilot
    has ONE outbound channel; a nudge people learn to ignore costs more than a
    missed one.

    ``after`` is a superset listing every plausible predecessor, and only the ones
    present in THIS case count — a case that never ordered parts has no
    ``order_parts`` row, so เริ่มซ่อม anchors on แจ้งอู่ instead. That is what
    makes one chain serve both a PM (which skips รถยก/รถถ่ายของ/parts entirely)
    and a roadside breakdown. An item with no prerequisite present at all falls
    back to its own activation rather than never running: a mandatory step must
    not become un-nudgeable just because its predecessors were skipped.

    ``max(..., activated_at)`` because an item added to the chain AFTER its
    prerequisite finished must be measured from when it entered, not from a
    completion that predates it — otherwise it is born already overdue.
    """
    if not spec.after:
        return item.activated_at

    present = [state[key] for key in spec.after if key in state]
    if not present:
        return item.activated_at
    if any(p.status == TASK_STATUS_PENDING for p in present):
        return None
    return max(max(p.last_flip_at for p in present), item.activated_at)


@dataclass(frozen=True)
class StaleItem:
    """One item over its threshold — what the LINE nudge is built from."""

    key: str
    label_th: str
    stale_since: datetime
    overdue_by: timedelta


def stale_items(
    events: list[RepairCaseTaskEvent], *, work_type: str, now: datetime
) -> list[StaleItem]:
    """Every currently-pending item whose SLA clock has run out, chain order.

    Only ``pending`` items can be stale: ``done`` and ``skipped`` are humans
    having already reported reality, and nudging about those teaches people to
    mute the channel (the failure the notify module's docstring names).
    """
    state = chain_state(events)
    out: list[StaleItem] = []
    for spec in TASK_CHAIN:
        item = state.get(spec.key)
        if item is None or item.status != TASK_STATUS_PENDING:
            continue
        anchor = _anchor_for(spec, item, state)
        if anchor is None:
            continue
        threshold = sla_for(spec, work_type=work_type, variant=item.variant)
        deadline = anchor + threshold
        if now > deadline:
            out.append(
                StaleItem(
                    key=spec.key,
                    label_th=spec.label_th,
                    stale_since=deadline,
                    overdue_by=now - deadline,
                )
            )
    return out


__all__ = [
    "TASK_CHAIN",
    "ChainItemState",
    "StaleItem",
    "TaskItemSpec",
    "chain_state",
    "item_spec",
    "sla_for",
    "stale_items",
    "TASK_STATUS_DONE",
    "TASK_STATUS_PENDING",
    "TASK_STATUS_SKIPPED",
]
