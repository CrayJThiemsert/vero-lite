"""Hand-authored task-chain event table (PLAN-0096 Step 6 / AC-7).

The post-approval checklist, stored as an append-only trail of status flips —
the same discipline as the quote pack (``repair_case_evidence.py``): current
state is the LATEST row per (case, item); a correction is a new row; nothing is
ever updated or deleted. AC-7 asks for "actor + timestamp per flip", and in this
shape the flips ARE the state rather than a log bolted onto mutable state.

**What a row means.** "Someone said this checklist item is now in this status."
A ``pending`` row is the item entering the chain (mandatory items when the chain
starts; a conditional item — รถยก, รถถ่ายของ — when a human decides this case
needs it, per A1: only trucks that cannot drive get a tow, only loaded trucks
get a cargo transfer). ``done`` and ``skipped`` are humans reporting reality.
There is no ``in_progress``: the partner's team tracks "ค้างอยู่ไหม", not
percent-complete, and a status nobody would flip is a status that lies.

**What this table does NOT know.** Which item keys exist, which are mandatory,
what the per-item SLAs are (A1's table: 30 minutes for แจ้งอู่ on a breakdown,
5 days for รออะไหล่ on a major part) — all of that is the fleet vertical's
authored config (``verticals/fleet_maintenance/task_chain.py``). The table
stores what happened; the config says what it means. A second vertical with a
different chain would reuse this table untouched — which is exactly why the
semantics must not live here (ADR-006 Rule of Three: no engine abstraction until
three verticals need one).

``variant`` is the flip-time context a threshold may depend on and only the
flipping human knows — today exactly one: ``major_part`` on the parts items
(A1: ordinary parts wait ~2 days, big ones ~5). Free-text ``note`` is for the
human's own words; nothing parses it.
"""

from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from services.db.base import Base
from services.db.tenant import TenantKeyMixin

#: The full status vocabulary. ``pending`` = entered the chain, ``done`` /
#: ``skipped`` = a human reported the outcome. Reopening a mis-flipped item is a
#: new ``pending`` row — visible, like every other correction here.
TASK_STATUS_PENDING = "pending"
TASK_STATUS_DONE = "done"
TASK_STATUS_SKIPPED = "skipped"
TASK_STATUSES = (TASK_STATUS_PENDING, TASK_STATUS_DONE, TASK_STATUS_SKIPPED)


class RepairCaseTaskEvent(TenantKeyMixin, Base):
    """One status flip of one checklist item on one repair case."""

    __tablename__ = "repair_case_task_event"
    __table_args__ = (
        sa.Index("idx_repair_case_task_event_case_id", "case_id"),
        # ``seq`` is the latest-wins key, declared UNIQUE so that "the current row
        # for this item" is a single-row answer by SCHEMA rather than by hope.
        # Identity is ``BY DEFAULT``, not ``ALWAYS``, because migration ``0025``
        # writes explicit values to backfill legacy rows in the old reader's order;
        # this constraint is what stops such a write landing on a value that exists.
        # Scoped ``(tenant_id, seq)`` per PLAN-0101 SD-3 — the counter is per-TABLE,
        # so no gap-free per-tenant monotonicity is implied. See services/db/tenant.py,
        # "What (tenant_id, seq) does NOT promise".
        sa.UniqueConstraint("tenant_id", "seq", name="uq_repair_case_task_event_seq"),
    )

    event_id: Mapped[str] = mapped_column(sa.Text, primary_key=True)
    case_id: Mapped[str] = mapped_column(
        sa.Text, sa.ForeignKey("repair_case.case_id"), nullable=False
    )
    item_key: Mapped[str] = mapped_column(sa.Text, nullable=False)
    status: Mapped[str] = mapped_column(sa.Text, nullable=False)
    actor: Mapped[str] = mapped_column(sa.Text, nullable=False)
    at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    variant: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    note: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    #: Insertion order, assigned by the database (PLAN-0099 D2 pattern; migration
    #: ``0025``). ``chain_state`` reduces these rows to "current status per item",
    #: and reading that off ``at`` means a backward clock step — measured on this box
    #: at 20 per 300 s, every one >= 400 ms — returns the SUPERSEDED flip as though
    #: it were the operator's latest word. The consequence is not cosmetic: the
    #: reduced status drives the staleness nudge, so a finished step gets chased
    #: forever, or a reopened one silently stops being chased. A same-instant tie is
    #: genuinely ambiguous on a clock; under a backward step the operator's intent is
    #: still recoverable, because it is insertion order — and this column is that.
    seq: Mapped[int] = mapped_column(sa.BigInteger, sa.Identity(always=False), nullable=False)
