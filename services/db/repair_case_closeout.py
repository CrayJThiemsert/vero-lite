"""The close-out record — what ปิดงาน / เก็บเอกสาร produces (PLAN-0096 Step 8).

This is what the month-end Express export is built from. Everything upstream — the
case, the quote pack, the sourcing signal, the gate, the task chain — answers *"was
this repair governed?"*. These tables answer the question accounting actually asks:
*"what did it cost, on which tax invoice, and which repair order was it?"*

**Two tables, not one, because they are two different facts** — the same split the
quote pack makes for the same reason:

* :class:`RepairCaseOrderNumber` — *this case is repair order ``RC-2026-0007``.*
  Exactly one per case, allocated once, never rewritten.
* :class:`RepairCaseCloseout` — *เมย์ keyed this paperwork at this moment.*
  Append-only, MANY per case: a correction is a new row and the export reads the
  latest, so a mistyped invoice number cannot be quietly erased.

Conflating them was the first shape tried, and it does not survive the append-only
rule. If the number lives on the keying row, then a correction either invents a
SECOND number for one repair, or the ``UNIQUE`` constraint that stops two repairs
sharing a number also forbids the correction path. Splitting them lets both
invariants hold at the database level at once: one number per case (primary key),
no number shared by two cases (unique), and unlimited corrections.

Per Cray's typed Decision B (s189), the money-and-paper fields are keyed at the
``close_case`` task-chain item (``verticals/fleet_maintenance/task_chain.py``):
``tax_invoice_no`` plus all three amounts, **none derived**. Back-computing VAT at
7% was explicitly rejected: not every vendor in this fleet is VAT-registered, so a
computed 7% would silently invent tax on the ones that are not, and the export
would disagree with the paper it exists to reconcile against.

**Money is Numeric, never float** — the rule the quote pack states. A binary float
in a column accounting reconciles is a rounding report waiting to happen.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from services.db.base import Base

#: Width of the running part of ``RC-<year>-<NNNN>``. Fixed-width zero padding is
#: what makes the series sort correctly as text anywhere it is displayed; the
#: allocator below refuses to exceed it rather than silently widening, because a
#: ``RC-2026-10000`` appearing mid-series would sort before ``RC-2026-0002``.
ORDER_NO_WIDTH = 4
ORDER_NO_PREFIX = "RC"


class RepairCaseOrderNumber(Base):
    """The human-readable repair-order number for one case — Cray's Decision A.

    It exists because ``repair_case.case_id`` is a UUID (``case-{uuid4hex[:12]}``)
    that no accounting department can key an Express document against, and AC-9's
    Express column 3 (เลขที่ใบแจ้งซ่อม) needs something a human reads off paper and
    types into a different system.

    ``case_id`` is the primary key, which is the whole point: a case cannot end up
    with two repair-order numbers, and the constraint says so rather than a comment
    asking future code to be careful.

    ``year`` and ``seq`` are stored as integers rather than parsed back out of the
    formatted string. The allocator needs ``MAX(seq)`` for a year, and deriving that
    by string-slicing a text column would make the numbering depend on the display
    format holding still forever.
    """

    __tablename__ = "repair_case_order_number"
    __table_args__ = (
        sa.UniqueConstraint("repair_order_no", name="uq_repair_case_order_number_no"),
        sa.UniqueConstraint("year", "seq", name="uq_repair_case_order_number_year_seq"),
    )

    case_id: Mapped[str] = mapped_column(
        sa.Text, sa.ForeignKey("repair_case.case_id"), primary_key=True
    )
    repair_order_no: Mapped[str] = mapped_column(sa.Text, nullable=False)
    year: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    seq: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    allocated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)


class RepairCaseCloseout(Base):
    """One close-out keying for one repair case. Append-only; latest row wins.

    ``vat_thb`` is NULLABLE on purpose: a vendor who charges no VAT has no VAT line,
    which is a different fact from a VAT line of zero. The export has to be able to
    tell those apart, because one of them means "not VAT-registered" and the other
    means "VAT-registered and this repair was exempt".
    """

    __tablename__ = "repair_case_closeout"
    __table_args__ = (
        sa.Index("idx_repair_case_closeout_case_id", "case_id"),
        sa.UniqueConstraint("seq", name="uq_repair_case_closeout_seq"),
    )

    closeout_id: Mapped[str] = mapped_column(sa.Text, primary_key=True)
    case_id: Mapped[str] = mapped_column(
        sa.Text, sa.ForeignKey("repair_case.case_id"), nullable=False
    )
    #: The garage that actually did the work — AC-9's ผู้ขาย / อู่, and the key the
    #: authored รหัสผู้ขาย mapping resolves. It is keyed here rather than derived
    #: from the quote pack because the pack records who QUOTED, not who was used:
    #: matching a quote to the invoice by amount would be a guess (quotes are
    #: pre-VAT, the invoice total is not, and an approved higher quote breaks the
    #: match outright). เมย์ reads it off the same piece of paper as the invoice
    #: number, so keying it costs nothing and inventing it costs correctness.
    vendor: Mapped[str] = mapped_column(sa.Text, nullable=False)
    tax_invoice_no: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    #: วันที่เอกสาร — AC-9 column 1, the date PRINTED ON the vendor's tax invoice
    #: (Cray, typed s192). A `Date`, not a `DateTime`: the paper carries a calendar
    #: date and no time, so a timestamp would store a precision the document does
    #: not have, and month-end would then be keyed on an invented hour.
    #:
    #: Deliberately NOT `entered_at`. เมย์ may key a 28 July invoice on 3 August, and
    #: an export that reported the keying day as the document date would put the row
    #: in the wrong accounting month while looking perfectly filled in — the failure
    #: mode a KPI counting completeness cannot see, because nothing is missing.
    #:
    #: Nullable, like `tax_invoice_no` and for the same reason: a repair can close
    #: before the invoice arrives, and the export reports that as an incomplete row
    #: rather than refusing the close-out.
    tax_invoice_date: Mapped[date | None] = mapped_column(sa.Date, nullable=True)
    amount_pre_vat_thb: Mapped[Decimal] = mapped_column(sa.Numeric(14, 2), nullable=False)
    #: NULL means "this vendor charges no VAT" — NOT ``Decimal("0.00")``.
    vat_thb: Mapped[Decimal | None] = mapped_column(sa.Numeric(14, 2), nullable=True)
    total_thb: Mapped[Decimal] = mapped_column(sa.Numeric(14, 2), nullable=False)
    entered_by: Mapped[str] = mapped_column(sa.Text, nullable=False)
    entered_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    #: Insertion order, assigned by the database (PLAN-0099 D2 / SD-3(a)). The
    #: correction path is what makes this load-bearing: เมย์ re-keys a mistyped
    #: invoice, a second row lands, and the month-end ฿ figure accounting reconciles
    #: against is whichever row ``latest_closeout`` calls current. Keyed on
    #: ``entered_at``, a backward clock step between the two writes hands the export
    #: the row เมย์ just corrected — and the export looks perfectly filled in doing
    #: it, which is the failure a completeness KPI structurally cannot see.
    seq: Mapped[int] = mapped_column(sa.BigInteger, sa.Identity(always=False), nullable=False)


async def latest_closeout(session: AsyncSession, case_id: str) -> RepairCaseCloseout | None:
    """The newest close-out keying for a case, or None.

    Newest wins because the table is append-only: a correction is a new row, and
    every consumer — the case endpoint, the month-end export — must agree on which
    row is current. One query in one place is how they stay agreed.

    **Newest means last-INSERTED** (PLAN-0099 D2 / SD-3(a)), for the reason
    :func:`services.db.evidence_pack.latest_accepted_quote` states about its own pick.
    Keyed on ``entered_at`` this was one backward clock step away from handing the
    month-end ฿ figure the row เมย์ had just corrected — and the export would have
    looked perfectly filled in doing it, which is the failure a completeness KPI
    structurally cannot see. ``seq`` is UNIQUE, so no tiebreak is needed: identical
    data yields one row, and the endpoint and the export cannot disagree about which.
    """
    return (
        (
            await session.execute(
                sa.select(RepairCaseCloseout)
                .where(RepairCaseCloseout.case_id == case_id)
                .order_by(RepairCaseCloseout.seq.desc())
                .limit(1)
            )
        )
        .scalars()
        .first()
    )


class OrderNumberExhaustedError(RuntimeError):
    """A year ran past ``RC-<year>-9999``.

    Raised rather than widening the format, because a wider number would sort wrong
    against every number already issued that year. A fleet of a few dozen trucks
    will not reach this; if it ever does, that is a decision about the format, not
    something the allocator should make silently at 03:00.
    """


def format_repair_order_no(year: int, seq: int) -> str:
    """``RC-2026-0007`` — Decision A's format, in one place.

    One function so the display form and the parsed ``(year, seq)`` columns cannot
    drift apart: everything that renders a repair-order number comes through here.
    """
    if seq < 1 or seq > 10**ORDER_NO_WIDTH - 1:
        raise OrderNumberExhaustedError(f"seq {seq} does not fit {ORDER_NO_WIDTH} digits")
    return f"{ORDER_NO_PREFIX}-{year}-{seq:0{ORDER_NO_WIDTH}d}"


async def allocate_repair_order_no(
    session: AsyncSession, *, case_id: str, year: int, now: datetime
) -> RepairCaseOrderNumber:
    """Return this case's repair-order number, allocating one on first close-out.

    **Idempotent by case.** A case that already has a number gets it back unchanged,
    which is what makes the append-only correction path work: เมย์ re-keys the
    paperwork, a second close-out row lands, and the repair keeps the number that is
    already written on the paper in the folder.

    **Gap-free within a year, by construction.** The next number is ``MAX(seq) + 1``
    over the numbers actually issued, and a number is only issued when a case really
    closes. A case that is opened and abandoned never consumes one, and a rolled-back
    transaction leaves no hole — which is the property an auditor asking "why does
    the series skip from 0006 to 0008?" actually cares about.

    **Fails closed under a race.** Two concurrent closes can compute the same
    ``MAX(seq) + 1``; a unique constraint rejects the loser, whose transaction rolls
    back and retries. This is deliberately not a lock: at this fleet's volume
    contention is effectively zero, and a wrong-but-unique number is a far worse
    failure than a retry.

    Two constraints stand behind that, and the loser dies on
    ``uq_repair_case_order_number_no`` rather than on ``(year, seq)`` — they are checked
    in declaration order and the formatted-number index is declared first. Either is a
    correct fail-closed; naming the wrong one only misleads whoever next reads a
    production error. Measured s195 by ``tests/services/db/test_concurrent_writer_races.py``,
    which also records that the loser BLOCKS on the winner's uncommitted key before it
    fails, so a caller sees latency and then an error, never a duplicate.
    """
    existing = await session.get(RepairCaseOrderNumber, case_id)
    if existing is not None:
        return existing

    highest = (
        await session.execute(
            sa.select(sa.func.max(RepairCaseOrderNumber.seq)).where(
                RepairCaseOrderNumber.year == year
            )
        )
    ).scalar()
    seq = (highest or 0) + 1

    allocated = RepairCaseOrderNumber(
        case_id=case_id,
        repair_order_no=format_repair_order_no(year, seq),
        year=year,
        seq=seq,
        allocated_at=now,
    )
    session.add(allocated)
    await session.flush()
    return allocated
