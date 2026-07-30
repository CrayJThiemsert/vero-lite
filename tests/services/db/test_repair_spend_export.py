"""Row-building for the month-end export (PLAN-0096 Step 8 item 5, AC-9).

These tests cover how one Express entry is ASSEMBLED — which month it falls in,
which human lands in ผู้อนุมัติ, and whether escaped money shows up at all. The KPI
itself and its non-vacuity oracle are a separate concern and live separately; a row
that is assembled wrong makes every number computed from it wrong too, so this is
the layer that has to be right first.

**The approver assertions are the load-bearing ones.** ``audit_log.actor_person_id``
is the obvious column and it is the WRONG one — on a provisional resolve it holds
ต้อม, the mechanic who keyed the record on the hard shoulder, not เฮีย who authorised
the spend. Printing the recorder in an accounting document's ผู้อนุมัติ column is a
wrong value that passes every type check and every completeness count, which is the
single most likely way this build ships a plausible-looking false document. So each
approver test seeds the recorder and the approver as DIFFERENT people and asserts the
recorder is not what comes out.

DB-backed — SKIPS when Postgres is unreachable, and a skip is never satisfaction.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import fields
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from services.db.audit_log import append_audit
from services.db.base import Base
from services.db.repair_case import RepairCase
from services.db.repair_case_closeout import RepairCaseCloseout, RepairCaseOrderNumber
from services.db.repair_case_run_link import (
    LINK_OUTCOME_APPROVED,
    LINK_OUTCOME_PROVISIONAL,
    LINK_OUTCOME_REJECTED,
    RepairCaseRunLink,
)
from services.db.repair_spend_export import (
    AUDIT_QUESTIONS,
    EXPORT_COLUMNS,
    ExportRow,
    audit_answers,
    is_fully_traceable,
    load_monthly_export,
    month_bounds,
)
from services.engine.procedures.ratification import RATIFICATION_KEY
from services.engine.procedures.runs import PipelineRun, StepResult
from tests.db_support import create_test_engine

BKK = ZoneInfo("Asia/Bangkok")

#: เฮีย — the owner who authorises the spend. The answer every approver test wants.
_APPROVER = "appr-owner"
#: ต้อม — the mechanic who KEYS the record. Seeded as `actor_person_id` on every audit
#: row below precisely so a reader that reached for that column fails these tests.
_RECORDER = "req-mechanic-tom"

#: A vendor WITH an Express code, and one deliberately without. `เจ๊หงส์` is used but
#: not yet opened in accounting — the fixture that keeps AC-9's KPI honest.
_CODED_VENDOR = "อู่คู่สัญญา ปากช่อง"
_UNCODED_VENDOR = "เจ๊หงส์"


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    eng = await create_test_engine()
    yield eng
    await eng.dispose()


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        yield session
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version CASCADE"))


async def _seed_case(
    session: AsyncSession,
    *,
    case_id: str,
    truck_id: str = "truck-01",
    description: str | None = "เปลี่ยนเพลาหลัง",
    work_type: str = "breakdown",
) -> None:
    session.add(
        RepairCase(
            case_id=case_id,
            truck_id=truck_id,
            opened_by=_RECORDER,
            opened_at=datetime(2026, 7, 10, 9, 0, tzinfo=UTC),
            description=description,
            status="open",
            work_type=work_type,
            photos=[],
        )
    )
    await session.flush()


async def _seed_closeout(
    session: AsyncSession,
    *,
    case_id: str,
    entered_at: datetime,
    vendor: str = _CODED_VENDOR,
    tax_invoice_no: str | None = "INV-2026-0042",
    tax_invoice_date: date | None = date(2026, 7, 28),
    closeout_id: str | None = None,
    seq: int | None = 7,
) -> None:
    """Seed a close-out, and the case's repair-order number unless ``seq`` is None.

    ``seq`` is per-case rather than fixed: `repair_case_order_number` carries UNIQUE
    on both `repair_order_no` and `(year, seq)`, so a multi-row month needs distinct
    numbers or the fixture fails on the constraint rather than on the assertion.
    """
    order_no = f"RC-2026-{seq:04d}" if seq is not None else None
    session.add(
        RepairCaseCloseout(
            closeout_id=closeout_id or f"co-{case_id}",
            case_id=case_id,
            vendor=vendor,
            tax_invoice_no=tax_invoice_no,
            tax_invoice_date=tax_invoice_date,
            amount_pre_vat_thb=Decimal("57943.93"),
            vat_thb=Decimal("4056.07"),
            total_thb=Decimal("62000.00"),
            entered_by=_RECORDER,
            entered_at=entered_at,
        )
    )
    if order_no is not None and await session.get(RepairCaseOrderNumber, case_id) is None:
        session.add(
            RepairCaseOrderNumber(
                case_id=case_id,
                repair_order_no=order_no,
                year=2026,
                seq=seq,
                allocated_at=entered_at,
            )
        )
    await session.flush()


async def _seed_governed_run(
    session: AsyncSession,
    *,
    case_id: str,
    run_id: str,
    decided_at: datetime,
    audit: dict[str, Any] | None,
    outcome: str = LINK_OUTCOME_APPROVED,
    step_id: str = "approve",
) -> None:
    """A gate decision, exactly as the engine records one.

    ``actor_person_id`` is the RECORDER on purpose — see the module docstring.
    """
    if await session.get(PipelineRun, run_id) is None:
        session.add(
            PipelineRun(
                run_id=run_id,
                procedure_id="governed_repair_approval",
                agent_id="fleet-agent",
                status="completed",
                started_at=decided_at,
                updated_at=decided_at,
            )
        )
        await session.flush()
    session.add(
        StepResult(
            step_result_id=f"sr-{run_id}-{step_id}",
            run_id=run_id,
            step_id=step_id,
            status="resolved",
            artifact={"output_set": [], "decisions": []},
            reasoning_trace=[],
            audit=audit,
            created_at=decided_at,
        )
    )
    session.add(
        RepairCaseRunLink(
            link_id=f"lnk-{run_id}-{case_id}-{outcome}",
            case_id=case_id,
            run_id=run_id,
            step_id=step_id,
            outcome=outcome,
            linked_at=decided_at,
        )
    )
    await session.flush()
    audit_row = await append_audit(
        session,
        action="gate_decision",
        actor_person_id=_RECORDER,
        run_id=run_id,
        step_id=step_id,
        payload={"actor_kind": "human"},
    )
    # `append_audit` stamps `occurred_at` from the wall clock; the export reads that
    # column as the approval instant, so the fixture must place it in the month under
    # test rather than at "whenever the suite ran".
    audit_row.occurred_at = decided_at
    await session.flush()


def _doa_tie(principal_id: str) -> dict[str, Any]:
    """The audit block an ordinary governed approval carries.

    The `sod` tie is included because the real one is — `_record_governed_decision`
    concatenates the SoD ties ahead of the authority ties, so a single-tie fixture
    would not be the shape the engine actually writes.

    **Both ties carry the SAME principal, and that is measured, not assumed**
    (`action_step.py` — every tie is built from `principal.person_id`). So the
    `doa_tier` filter in the reader picks the right CONTROL, not a different human,
    and no probe can redden it without fabricating a state the engine cannot emit.
    It is defensive against a future emission that ties a second person, and it is
    NOT covered by an oracle today — named here rather than implied by a fixture
    where the principals differ, which would prove a contract nothing produces.
    """
    return {
        "governed_decision": [
            {
                "control_ref": {"kind": "sod", "id": "requester_ne_approver"},
                "principal_id": principal_id,
            },
            {"control_ref": {"kind": "doa_tier", "id": "owner"}, "principal_id": principal_id},
        ]
    }


def _ratification_block(
    *,
    attested: str,
    due_at: datetime,
    ratified_by: str | None = None,
    refused_by: str | None = None,
) -> dict[str, Any]:
    block: dict[str, Any] = {
        RATIFICATION_KEY: {
            "due_at": due_at.isoformat(),
            "ratify_by_role": "owner",
            "attested_approver_id": attested,
            "recorded_by": _RECORDER,
            "justification_ref": "a" * 64,
        }
    }
    if ratified_by is not None:
        block[RATIFICATION_KEY]["ratified_by"] = ratified_by
        block[RATIFICATION_KEY]["ratified_at"] = due_at.isoformat()
    if refused_by is not None:
        block[RATIFICATION_KEY]["refused_by"] = refused_by
        block[RATIFICATION_KEY]["refused_at"] = due_at.isoformat()
    return block


# --------------------------------------------------------------------------- #
# The month boundary
# --------------------------------------------------------------------------- #


def test_month_bounds_are_thai_calendar_instants() -> None:
    """July 2026 runs 30 June 17:00Z → 31 July 17:00Z, not midnight to midnight UTC."""
    start, end = month_bounds(2026, 7)
    assert start == datetime(2026, 6, 30, 17, 0, tzinfo=UTC)
    assert end == datetime(2026, 7, 31, 17, 0, tzinfo=UTC)


def test_month_bounds_roll_the_year_at_december() -> None:
    start, end = month_bounds(2026, 12)
    assert start == datetime(2026, 11, 30, 17, 0, tzinfo=UTC)
    assert end == datetime(2026, 12, 31, 17, 0, tzinfo=UTC)


async def test_approval_just_after_thai_midnight_files_in_the_new_month(
    db_session: AsyncSession,
) -> None:
    """01:00 on 1 August Bangkok is an AUGUST row, though it is 31 July in UTC.

    This is the wrong-month failure `tax_invoice_date` exists to prevent, arriving
    through the other door: the row looks completely filled in either way, so nothing
    downstream can flag it. A UTC-bounded query files it in July.
    """
    decided_at = datetime(2026, 8, 1, 1, 0, tzinfo=BKK)
    assert decided_at.astimezone(UTC).month == 7  # the trap, made explicit

    await _seed_case(db_session, case_id="case-boundary")
    await _seed_closeout(
        db_session, case_id="case-boundary", entered_at=datetime(2026, 8, 2, 3, 0, tzinfo=UTC)
    )
    await _seed_governed_run(
        db_session,
        case_id="case-boundary",
        run_id="run-boundary",
        decided_at=decided_at,
        audit=_doa_tie(_APPROVER),
    )

    july = await load_monthly_export(db_session, year=2026, month=7, now=decided_at)
    august = await load_monthly_export(db_session, year=2026, month=8, now=decided_at)

    assert [r.case_id for r in july.rows] == []
    assert [r.case_id for r in august.rows] == ["case-boundary"]
    assert august.rows[0].approval_date == date(2026, 8, 1)


# --------------------------------------------------------------------------- #
# ผู้อนุมัติ — the column most likely to name the wrong human
# --------------------------------------------------------------------------- #


async def test_approver_is_the_doa_tier_principal_not_the_audit_actor(
    db_session: AsyncSession,
) -> None:
    """เฮีย authorised; ต้อม is on `audit_log.actor_person_id`. The column says เฮีย."""
    decided_at = datetime(2026, 7, 15, 10, 0, tzinfo=BKK)
    await _seed_case(db_session, case_id="case-governed")
    await _seed_closeout(
        db_session, case_id="case-governed", entered_at=datetime(2026, 7, 20, 3, 0, tzinfo=UTC)
    )
    await _seed_governed_run(
        db_session,
        case_id="case-governed",
        run_id="run-governed",
        decided_at=decided_at,
        audit=_doa_tie(_APPROVER),
    )

    export = await load_monthly_export(db_session, year=2026, month=7, now=decided_at)

    (row,) = export.rows
    assert row.approver == _APPROVER
    assert row.approver != _RECORDER


async def test_provisional_row_reads_the_attested_approver(db_session: AsyncSession) -> None:
    """A provisional resolve emits NO `governed_decision` — the obligation block is
    the only record of who authorised, and the recorder must not stand in for them."""
    decided_at = datetime(2026, 7, 15, 22, 30, tzinfo=BKK)
    await _seed_case(db_session, case_id="case-provisional")
    await _seed_closeout(
        db_session, case_id="case-provisional", entered_at=datetime(2026, 7, 21, 3, 0, tzinfo=UTC)
    )
    await _seed_governed_run(
        db_session,
        case_id="case-provisional",
        run_id="run-provisional",
        decided_at=decided_at,
        outcome=LINK_OUTCOME_PROVISIONAL,
        audit=_ratification_block(
            attested=_APPROVER, due_at=datetime(2026, 7, 22, 15, 30, tzinfo=UTC)
        ),
    )

    export = await load_monthly_export(db_session, year=2026, month=7, now=decided_at)

    (row,) = export.rows
    assert row.approver == _APPROVER
    assert row.exception_label == "pending"
    assert row.justification_ref == "a" * 64


async def test_overdue_ratification_is_labelled_from_the_report_clock(
    db_session: AsyncSession,
) -> None:
    """`now` is a parameter: re-running last month's export must not relabel it today."""
    decided_at = datetime(2026, 7, 15, 22, 30, tzinfo=BKK)
    due_at = datetime(2026, 7, 22, 15, 30, tzinfo=UTC)
    await _seed_case(db_session, case_id="case-overdue")
    await _seed_governed_run(
        db_session,
        case_id="case-overdue",
        run_id="run-overdue",
        decided_at=decided_at,
        outcome=LINK_OUTCOME_PROVISIONAL,
        audit=_ratification_block(attested=_APPROVER, due_at=due_at),
    )

    at_report_time = await load_monthly_export(
        db_session, year=2026, month=7, now=datetime(2026, 7, 20, 0, 0, tzinfo=UTC)
    )
    later = await load_monthly_export(
        db_session, year=2026, month=7, now=datetime(2026, 8, 30, 0, 0, tzinfo=UTC)
    )

    assert at_report_time.rows[0].exception_label == "pending"
    assert later.rows[0].exception_label == "overdue"
    assert later.outstanding_ratifications == later.rows


async def test_refused_ratification_leaves_the_approver_blank(db_session: AsyncSession) -> None:
    """A refusal is checked FIRST (Cray, typed s192).

    The authorisation was withdrawn, so there is no approver to print. Letting the
    attested name survive a refusal would put a signature in an accounting document
    for spend the signatory declined to stand behind.
    """
    decided_at = datetime(2026, 7, 15, 22, 30, tzinfo=BKK)
    await _seed_case(db_session, case_id="case-refused")
    await _seed_closeout(
        db_session, case_id="case-refused", entered_at=datetime(2026, 7, 25, 3, 0, tzinfo=UTC)
    )
    await _seed_governed_run(
        db_session,
        case_id="case-refused",
        run_id="run-refused",
        decided_at=decided_at,
        outcome=LINK_OUTCOME_PROVISIONAL,
        audit=_ratification_block(
            attested=_APPROVER,
            due_at=datetime(2026, 7, 22, 15, 30, tzinfo=UTC),
            refused_by=_APPROVER,
        ),
    )

    export = await load_monthly_export(db_session, year=2026, month=7, now=decided_at)

    (row,) = export.rows
    assert row.approver is None
    assert row.exception_label == "refused"
    assert is_fully_traceable(row) is False


async def test_rejected_case_names_nobody_as_approver(db_session: AsyncSession) -> None:
    """A rejected proposal was not approved, whatever else the step's audit carries."""
    decided_at = datetime(2026, 7, 16, 11, 0, tzinfo=BKK)
    await _seed_case(db_session, case_id="case-rejected")
    await _seed_governed_run(
        db_session,
        case_id="case-rejected",
        run_id="run-rejected",
        decided_at=decided_at,
        outcome=LINK_OUTCOME_REJECTED,
        audit=_doa_tie(_APPROVER),
    )

    export = await load_monthly_export(db_session, year=2026, month=7, now=decided_at)

    (row,) = export.rows
    assert row.outcome == LINK_OUTCOME_REJECTED
    assert row.approver is None
    assert is_fully_traceable(row) is False


# --------------------------------------------------------------------------- #
# Ungoverned spend — the row that must not be invisible
# --------------------------------------------------------------------------- #


async def test_ungoverned_closeout_is_a_row_not_an_absence(db_session: AsyncSession) -> None:
    """Money spent with no governed run is the escaped money — it gets a row."""
    await _seed_case(db_session, case_id="case-escaped")
    await _seed_closeout(
        db_session, case_id="case-escaped", entered_at=datetime(2026, 7, 18, 4, 0, tzinfo=UTC)
    )

    export = await load_monthly_export(
        db_session, year=2026, month=7, now=datetime(2026, 7, 31, 0, 0, tzinfo=UTC)
    )

    (row,) = export.rows
    assert row.governed is False
    assert row.run_id is None
    assert row.approver is None
    assert row.approval_date is None
    assert row.total_thb == Decimal("62000.00")
    assert export.ungoverned_rows == export.rows
    assert is_fully_traceable(row) is False


async def test_ungoverned_row_with_no_invoice_date_still_appears(
    db_session: AsyncSession,
) -> None:
    """Filed by `entered_at`, so a missing วันที่เอกสาร cannot erase the row.

    `tax_invoice_date` is nullable. Filing ungoverned rows by it would drop exactly
    the least-documented spend out of every month's export — restoring the blindness
    this source exists to end, while the KPI kept reporting a healthy number.
    """
    await _seed_case(db_session, case_id="case-no-invoice")
    await _seed_closeout(
        db_session,
        case_id="case-no-invoice",
        entered_at=datetime(2026, 7, 19, 4, 0, tzinfo=UTC),
        tax_invoice_no=None,
        tax_invoice_date=None,
    )

    export = await load_monthly_export(
        db_session, year=2026, month=7, now=datetime(2026, 7, 31, 0, 0, tzinfo=UTC)
    )

    (row,) = export.rows
    assert row.case_id == "case-no-invoice"
    assert row.document_date is None
    assert row.tax_invoice_no is None


# --------------------------------------------------------------------------- #
# Column mapping
# --------------------------------------------------------------------------- #


async def test_governed_and_documented_row_fills_every_express_column(
    db_session: AsyncSession,
) -> None:
    """The happy path: all 15 columns present except ศูนย์ต้นทุน, which ships empty."""
    decided_at = datetime(2026, 7, 15, 10, 0, tzinfo=BKK)
    await _seed_case(db_session, case_id="case-complete", truck_id="truck-01")
    await _seed_closeout(
        db_session, case_id="case-complete", entered_at=datetime(2026, 7, 20, 3, 0, tzinfo=UTC)
    )
    await _seed_governed_run(
        db_session,
        case_id="case-complete",
        run_id="run-complete",
        decided_at=decided_at,
        audit=_doa_tie(_APPROVER),
    )

    export = await load_monthly_export(db_session, year=2026, month=7, now=decided_at)

    (row,) = export.rows
    assert row.document_date == date(2026, 7, 28)
    assert row.approval_date == date(2026, 7, 15)
    assert row.repair_order_no == "RC-2026-0007"
    assert row.tax_invoice_no == "INV-2026-0042"
    assert row.vendor == _CODED_VENDOR
    assert row.vendor_code == "V-001"
    assert row.plate == "80-1234 กรุงเทพมหานคร"
    assert row.truck_code == "T-001"
    assert row.work_type == "breakdown"
    assert row.description == "เปลี่ยนเพลาหลัง"
    assert row.amount_pre_vat_thb == Decimal("57943.93")
    assert row.vat_thb == Decimal("4056.07")
    assert row.total_thb == Decimal("62000.00")
    assert row.approver == _APPROVER
    assert row.cost_center is None
    assert is_fully_traceable(row) is True


async def test_vendor_without_an_express_code_leaves_the_code_blank(
    db_session: AsyncSession,
) -> None:
    """เจ๊หงส์ is used but not yet opened in Express — reported honestly, not guessed."""
    decided_at = datetime(2026, 7, 15, 10, 0, tzinfo=BKK)
    await _seed_case(db_session, case_id="case-uncoded-vendor")
    await _seed_closeout(
        db_session,
        case_id="case-uncoded-vendor",
        entered_at=datetime(2026, 7, 20, 3, 0, tzinfo=UTC),
        vendor=f"  {_UNCODED_VENDOR} ",  # trimmed + case-folded matching, per the registry
    )
    await _seed_governed_run(
        db_session,
        case_id="case-uncoded-vendor",
        run_id="run-uncoded-vendor",
        decided_at=decided_at,
        audit=_doa_tie(_APPROVER),
    )

    export = await load_monthly_export(db_session, year=2026, month=7, now=decided_at)

    (row,) = export.rows
    assert row.vendor_code is None
    assert is_fully_traceable(row) is False


async def test_truck_without_an_accounting_code_leaves_the_vehicle_code_blank(
    db_session: AsyncSession,
) -> None:
    """truck-03 is in service before accounting opened it — the second honest blank."""
    decided_at = datetime(2026, 7, 15, 10, 0, tzinfo=BKK)
    await _seed_case(db_session, case_id="case-uncoded-truck", truck_id="truck-03")
    await _seed_closeout(
        db_session, case_id="case-uncoded-truck", entered_at=datetime(2026, 7, 20, 3, 0, tzinfo=UTC)
    )
    await _seed_governed_run(
        db_session,
        case_id="case-uncoded-truck",
        run_id="run-uncoded-truck",
        decided_at=decided_at,
        audit=_doa_tie(_APPROVER),
    )

    export = await load_monthly_export(db_session, year=2026, month=7, now=decided_at)

    (row,) = export.rows
    assert row.plate == "82-9012 กรุงเทพมหานคร"
    assert row.truck_code is None
    assert is_fully_traceable(row) is False


async def test_latest_closeout_wins_over_the_corrected_one(db_session: AsyncSession) -> None:
    """Append-only: a correction is a new row, and the export reads the newest.

    A mistyped invoice number that the export kept showing would make the correction
    path pointless — เมย์ re-keys the paperwork and the month-end file still carries
    the wrong number onto the accountant's desk.
    """
    await _seed_case(db_session, case_id="case-corrected")
    await _seed_closeout(
        db_session,
        case_id="case-corrected",
        entered_at=datetime(2026, 7, 18, 4, 0, tzinfo=UTC),
        tax_invoice_no="INV-TYPO",
        closeout_id="co-first",
    )
    await _seed_closeout(
        db_session,
        case_id="case-corrected",
        entered_at=datetime(2026, 7, 19, 4, 0, tzinfo=UTC),
        tax_invoice_no="INV-2026-0099",
        closeout_id="co-second",
    )

    export = await load_monthly_export(
        db_session, year=2026, month=7, now=datetime(2026, 7, 31, 0, 0, tzinfo=UTC)
    )

    (row,) = export.rows
    assert row.tax_invoice_no == "INV-2026-0099"


# --------------------------------------------------------------------------- #
# The KPI — AC-9's payoff number, and its non-vacuity bar
# --------------------------------------------------------------------------- #


async def _seed_complete_row(
    session: AsyncSession, *, case_id: str, seq: int, run_id: str, decided_at: datetime
) -> None:
    """A row that answers every audit question — the 100% baseline."""
    await _seed_case(session, case_id=case_id, truck_id="truck-01")
    await _seed_closeout(
        session,
        case_id=case_id,
        entered_at=datetime(2026, 7, 20, 3, 0, tzinfo=UTC),
        seq=seq,
    )
    await _seed_governed_run(
        session,
        case_id=case_id,
        run_id=run_id,
        decided_at=decided_at,
        audit=_doa_tie(_APPROVER),
    )


async def test_a_month_of_complete_rows_scores_one_hundred(db_session: AsyncSession) -> None:
    """The baseline the non-vacuity bar is measured against.

    Without this, a KPI stuck at 0% would satisfy "an incomplete row drops it below
    100%" trivially, and the bar would prove nothing.
    """
    decided_at = datetime(2026, 7, 15, 10, 0, tzinfo=BKK)
    await _seed_complete_row(
        db_session, case_id="case-a", seq=1, run_id="run-a", decided_at=decided_at
    )
    await _seed_complete_row(
        db_session, case_id="case-b", seq=2, run_id="run-b", decided_at=decided_at
    )

    export = await load_monthly_export(db_session, year=2026, month=7, now=decided_at)

    assert len(export.rows) == 2
    assert export.traceability_pct == 100.0


async def test_one_incomplete_row_drops_the_kpi_below_one_hundred(
    db_session: AsyncSession,
) -> None:
    """**AC-9's non-vacuity bar.** If this does not hold, the metric is vacuous.

    The incomplete row is not invented for the test: `เจ๊หงส์` is a real fixture
    vendor deliberately shipped with no `accounting_code`, because a garage can be
    used before accounting opens it in Express. An export built only from coded
    vendors would report 100% traceable no matter what happened.
    """
    decided_at = datetime(2026, 7, 15, 10, 0, tzinfo=BKK)
    await _seed_complete_row(
        db_session, case_id="case-complete", seq=1, run_id="run-complete", decided_at=decided_at
    )
    # Identical in every respect except the one missing Express code.
    await _seed_case(db_session, case_id="case-incomplete", truck_id="truck-01")
    await _seed_closeout(
        db_session,
        case_id="case-incomplete",
        entered_at=datetime(2026, 7, 20, 3, 0, tzinfo=UTC),
        vendor=_UNCODED_VENDOR,
        seq=2,
    )
    await _seed_governed_run(
        db_session,
        case_id="case-incomplete",
        run_id="run-incomplete",
        decided_at=decided_at,
        audit=_doa_tie(_APPROVER),
    )

    export = await load_monthly_export(db_session, year=2026, month=7, now=decided_at)

    assert len(export.rows) == 2
    assert export.traceable_row_count == 1
    assert export.traceability_pct == 50.0
    assert export.traceability_pct < 100.0


async def test_escaped_money_drops_the_kpi_and_shows_in_baht(
    db_session: AsyncSession,
) -> None:
    """Ungoverned spend is the KPI's whole reason for existing.

    The baht figure is asserted alongside the count because they answer different
    questions — a count-only cover lets one expensive escape hide behind many cheap
    governed rows.
    """
    decided_at = datetime(2026, 7, 15, 10, 0, tzinfo=BKK)
    await _seed_complete_row(
        db_session, case_id="case-governed", seq=1, run_id="run-governed", decided_at=decided_at
    )
    await _seed_case(db_session, case_id="case-escaped")
    await _seed_closeout(
        db_session,
        case_id="case-escaped",
        entered_at=datetime(2026, 7, 18, 4, 0, tzinfo=UTC),
        seq=2,
    )

    cover = (
        await load_monthly_export(db_session, year=2026, month=7, now=decided_at)
    ).cover_summary()

    assert cover.row_count == 2
    assert cover.traceability_pct == 50.0
    assert cover.ungoverned_row_count == 1
    assert cover.ungoverned_thb == Decimal("62000.00")
    assert cover.total_thb == Decimal("124000.00")


async def test_empty_month_reports_none_not_a_perfect_score(db_session: AsyncSession) -> None:
    """A month nobody spent in has no traceability to report."""
    cover = (
        await load_monthly_export(
            db_session, year=2026, month=3, now=datetime(2026, 7, 31, tzinfo=UTC)
        )
    ).cover_summary()

    assert cover.row_count == 0
    assert cover.traceability_pct is None
    assert cover.audit_answer_pct is None


async def test_audit_proxy_moves_where_the_all_or_nothing_kpi_cannot(
    db_session: AsyncSession,
) -> None:
    """The companion number exists to show partial progress.

    A case that went from "nothing recorded" to "everything but the invoice" is real
    improvement the headline KPI cannot express — it is 0% either way. If the proxy
    could not separate them it would be redundant with the KPI and worth deleting.
    """
    decided_at = datetime(2026, 7, 15, 10, 0, tzinfo=BKK)
    # Governed and approved, but no paperwork keyed at all: 3 of 5 questions answered.
    await _seed_case(db_session, case_id="case-partial")
    await _seed_governed_run(
        db_session,
        case_id="case-partial",
        run_id="run-partial",
        decided_at=decided_at,
        audit=_doa_tie(_APPROVER),
    )

    export = await load_monthly_export(db_session, year=2026, month=7, now=decided_at)

    (row,) = export.rows
    assert audit_answers(row) == (True, True, True, False, True)
    cover = export.cover_summary()
    assert cover.traceability_pct == 0.0
    assert cover.audit_answer_pct == pytest.approx(80.0)


def _complete_row(**overrides: Any) -> ExportRow:
    """A hand-built row that answers everything — the base for predicate unit tests."""
    base: dict[str, Any] = {
        "document_date": date(2026, 7, 28),
        "approval_date": date(2026, 7, 15),
        "repair_order_no": "RC-2026-0007",
        "tax_invoice_no": "INV-2026-0042",
        "vendor": _CODED_VENDOR,
        "vendor_code": "V-001",
        "plate": "80-1234 กรุงเทพมหานคร",
        "truck_code": "T-001",
        "work_type": "breakdown",
        "description": "เปลี่ยนเพลาหลัง",
        "amount_pre_vat_thb": Decimal("57943.93"),
        "vat_thb": Decimal("4056.07"),
        "total_thb": Decimal("62000.00"),
        "approver": _APPROVER,
        "cost_center": None,
        "case_id": "case-x",
        "governed": True,
        "run_id": "run-x",
        "outcome": LINK_OUTCOME_APPROVED,
        "exception_label": None,
        "justification_ref": None,
    }
    return ExportRow(**{**base, **overrides})


def test_complete_row_is_traceable() -> None:
    """The predicate's own baseline — without it the two guards below prove nothing."""
    assert is_fully_traceable(_complete_row()) is True


def test_predicate_refuses_an_ungoverned_row_even_when_fully_documented() -> None:
    """The `governed` guard holds on its OWN contract, not on a caller's care.

    `load_monthly_export` never builds this row — it nulls the approver whenever
    there is no decision, so the guard is currently unreachable through that path and
    a probe deleting it stays green. That is precisely why the predicate is tested
    directly: it is public and pure, its contract must hold for any row handed to it,
    and if `_build_row` ever starts carrying an approver on an ungoverned row this is
    what stops escaped money being scored as traceable.
    """
    assert is_fully_traceable(_complete_row(governed=False, run_id=None)) is False


def test_predicate_refuses_a_rejected_row_even_when_an_approver_is_present() -> None:
    """Same reasoning for the outcome guard: a rejected proposal was not approved.

    A row carrying both a rejection and an approver is contradictory, and the
    predicate resolves it the way Cray typed the ordering — the refusal wins.
    """
    assert is_fully_traceable(_complete_row(outcome=LINK_OUTCOME_REJECTED)) is False
    assert is_fully_traceable(_complete_row(outcome="refused")) is False


def test_predicate_does_not_require_vat_or_cost_center() -> None:
    """Both omissions are deliberate and both would be bugs if reversed.

    A garage that is not VAT-registered has no VAT line, and ศูนย์ต้นทุน ships
    unfilled pending a partner answer — requiring either would score honest rows as
    untraceable, and requiring `cost_center` would pin the KPI at 0% forever.
    """
    assert is_fully_traceable(_complete_row(vat_thb=None)) is True
    assert is_fully_traceable(_complete_row(cost_center=None)) is True


def test_audit_questions_and_answers_stay_the_same_length() -> None:
    """The proxy's denominator is `len(AUDIT_QUESTIONS)`; a mismatch would skew it."""
    blank = ExportRow(
        *(None,) * 15,
        case_id="c",
        governed=False,
        run_id=None,
        outcome=None,
        exception_label=None,
        justification_ref=None,
    )
    assert len(audit_answers(blank)) == len(AUDIT_QUESTIONS) == 5


#: The Express half of `ExportRow`, positionally aligned with `EXPORT_COLUMNS`.
#: Written out rather than sliced from the dataclass so the assertion below compares
#: two INDEPENDENT statements of the mapping — a test that derived this list from the
#: same object it checks would agree with itself no matter what either side became.
_EXPRESS_FIELDS = (
    "document_date",
    "approval_date",
    "repair_order_no",
    "tax_invoice_no",
    "vendor",
    "vendor_code",
    "plate",
    "truck_code",
    "work_type",
    "description",
    "amount_pre_vat_thb",
    "vat_thb",
    "total_thb",
    "approver",
    "cost_center",
)


def test_express_columns_and_row_fields_stay_positionally_aligned() -> None:
    """The 15 headers and the 15 Express fields cannot drift apart.

    `ExportRow` carries provenance fields AFTER the Express ones, and the CSV writer
    will render `EXPORT_COLUMNS` against those first fields positionally. Adding a
    column on one side only would otherwise shift every value one cell left in an
    accounting document — a corruption that no type check and no completeness count
    can see, because every cell is still populated.
    """
    names = [f.name for f in fields(ExportRow)]
    assert len(EXPORT_COLUMNS) == len(_EXPRESS_FIELDS) == 15
    assert names[:15] == list(_EXPRESS_FIELDS)
    # The boundary itself: the 16th field starts provenance, not Express.
    assert names[15] == "case_id"
