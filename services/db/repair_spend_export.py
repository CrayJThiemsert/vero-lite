"""The month-end repair-spend export — AC-9's payoff moment (PLAN-0096 Step 8 item 5).

Everything upstream in this flow answers *"was this repair governed?"*. This module
answers the question that makes the answer worth money: **"show me the month, and
show me what escaped."**

**Two row sources, unioned — and the second one is the whole point.** A naive export
lists governed spend and reports 100% traceability by construction, because the rows
it cannot explain are the rows it never selected. Cray's typed decision (s192): a case
with a real payment that never passed a governed run is *the money that escaped*, and
it appears as a row that drags the KPI down. So:

* **Governed** — cases with a ``gate_decision`` in the month. The accounting month
  comes from the APPROVAL date, not the close-out date (Cray, typed): a case approved
  15 July and closed 3 August is a JULY row, with blank invoice fields until the
  paperwork lands.
* **Ungoverned** — cases whose close-out landed in the month with no governed run at
  all. Filed by ``entered_at``, the moment the spend became known to the system.
  Deliberately NOT ``tax_invoice_date``: that column is nullable, so an ungoverned
  repair with no invoice yet would have no month at all and would vanish from every
  export ever run — silently restoring the exact blindness this source exists to end.

**The month is bounded in Asia/Bangkok, not UTC.** ``occurred_at`` is stored as
timestamptz (UTC); the accounting month is a Thai calendar month. A gate decision at
2026-08-01 02:00 +07 is 2026-07-31 19:00 UTC, and a UTC-bounded query files it in July
— the same wrong-month failure ``tax_invoice_date`` exists to prevent, arriving through
the other door. The zone follows the engine's ratified default (ADR-0028 SD-P1).

**This module reports; it does not judge.** Rows carry their gate outcome and their
exception label rather than being filtered by them, for the reason
:mod:`services.db.evidence_pack` states about the quote pack: a reader with an opinion
is a reader that can be wrong in a way no caller can see. The single judgement in here
is :func:`is_fully_traceable`, which is the KPI's definition and is therefore stated
once, in the open, where it can be argued with.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from services.db.audit_log import AuditLog
from services.db.repair_case import RepairCase
from services.db.repair_case_closeout import (
    RepairCaseCloseout,
    RepairCaseOrderNumber,
    latest_closeout,
)
from services.db.repair_case_run_link import (
    LINK_OUTCOME_REFUSED,
    LINK_OUTCOME_REJECTED,
    RepairCaseRunLink,
)
from services.engine.procedures.ratification import RATIFICATION_KEY, ratification_state
from services.engine.procedures.runs import StepResult
from verticals.fleet_maintenance.data_adapter.synthetic import truck_records, vendor_records

#: The accounting calendar the month is bounded in. Follows the engine's ratified
#: default zone for the primary TH operator (ADR-0028 SD-P1).
EXPORT_TIMEZONE = "Asia/Bangkok"

#: The audit action a gate resolution writes — the row that carries the approval
#: date (``action_step.py``). Named here so the export and the gate cannot drift.
GATE_DECISION_ACTION = "gate_decision"

#: AC-9's 15 Express columns, in the order accounting keys them, transcribed from
#: the partner's A2 answer. This tuple is the single source of truth for column
#: order — the CSV writer renders it, and :class:`ExportRow` declares its fields in
#: the same sequence so the two cannot silently disagree.
EXPORT_COLUMNS = (
    "วันที่เอกสาร",
    "วันที่อนุมัติ",
    "เลขที่ใบแจ้งซ่อม",
    "เลขที่ใบกำกับภาษี",
    "ผู้ขาย / อู่",
    "รหัสผู้ขาย",
    "ทะเบียนรถ",
    "รหัสรถ",
    "ประเภทงาน",
    "รายการซ่อม",
    "จำนวนเงินก่อน VAT",
    "VAT",
    "จำนวนเงินรวม",
    "ผู้อนุมัติ",
    "ศูนย์ต้นทุน",
)


@dataclass(frozen=True)
class ExportRow:
    """One Express entry — one repair on one vehicle, never two trucks on a line.

    Every Express column is nullable here even where its source column is NOT NULL,
    because an ungoverned row genuinely has no approver and an unclosed row genuinely
    has no invoice. Rendering those as blanks is the honest report; the KPI is what
    turns a blank into a number somebody has to answer for.
    """

    # ---- the 15 Express columns, in EXPORT_COLUMNS order ------------------- #
    document_date: date | None
    approval_date: date | None
    repair_order_no: str | None
    tax_invoice_no: str | None
    vendor: str | None
    vendor_code: str | None
    plate: str | None
    truck_code: str | None
    work_type: str | None
    description: str | None
    amount_pre_vat_thb: Decimal | None
    #: NULL means "this vendor charges no VAT" — never back-computed at 7%, which
    #: Cray rejected twice, typed. A computed VAT would invent tax on the garages
    #: that are not registered, and the export would then disagree with the paper it
    #: exists to reconcile against.
    vat_thb: Decimal | None
    total_thb: Decimal | None
    approver: str | None
    #: ศูนย์ต้นทุน — ships EMPTY. Its granularity (per truck or per company) is an
    #: open partner intake question; the PLAN pre-authorises shipping the column
    #: unfilled rather than guessing a value accounting would have to unpick.
    cost_center: str | None

    # ---- provenance: the cover summary + the audit answer, not Express ----- #
    case_id: str
    #: False when no governed run ever decided this case — the escaped-money row.
    governed: bool
    run_id: str | None
    #: The gate's disposition for THIS case (``approved`` / ``rejected`` /
    #: ``provisional`` / ``ratified`` / ``refused``), or None when ungoverned.
    outcome: str | None
    #: The E-2 standing at report time — ``pending`` / ``overdue`` / ``ratified`` /
    #: ``refused``, or None when the case carries no ratification obligation.
    exception_label: str | None
    #: The tamper-evident handle of the audit row holding the run-time justification.
    justification_ref: str | None


@dataclass(frozen=True)
class MonthlyExport:
    """One accounting month of repair spend, plus the numbers on its cover.

    ``rows`` is ordered by approval date then case id — stable across runs, so two
    exports of the same month diff cleanly and an accountant can find a row again.
    """

    year: int
    month: int
    rows: tuple[ExportRow, ...]

    @property
    def traceable_row_count(self) -> int:
        return sum(1 for row in self.rows if is_fully_traceable(row))

    @property
    def traceability_pct(self) -> float | None:
        """AC-9's KPI: % of rows fully traceable.

        None for an empty month, NOT 100.0. A month with no spend has no
        traceability to report, and reporting a perfect score for it would put the
        best number the KPI can produce on the months nobody looked at.
        """
        if not self.rows:
            return None
        return 100.0 * self.traceable_row_count / len(self.rows)

    @property
    def ungoverned_rows(self) -> tuple[ExportRow, ...]:
        """The spend that never passed a governed run — the escaped money."""
        return tuple(row for row in self.rows if not row.governed)

    @property
    def outstanding_ratifications(self) -> tuple[ExportRow, ...]:
        """Rows where somebody still owes a signature — pending OR overdue."""
        return tuple(row for row in self.rows if row.exception_label in ("pending", "overdue"))


def is_fully_traceable(row: ExportRow) -> bool:
    """Whether one export row can answer the audit question end to end.

    This predicate IS the KPI's definition — AC-9's "% of rows fully traceable" is
    nothing more than how often this returns True. It is deliberately one function
    in the open rather than a condition inlined into the percentage, because the
    number is going in front of a partner and the thing it counts has to be
    arguable.

    **Cray's typed rule (s193): BOTH halves, not either.** A row counts only when it
    was governed AND its paperwork is complete. The two weaker rules were offered and
    declined, each because it hides the failure the other one catches: counting only
    governance would score a perfectly-approved repair with no invoice at 100%, and
    counting only paperwork would score escaped money as traceable the moment เมย์
    keyed a tidy invoice for it — the direct contradiction of why ungoverned rows are
    in this export at all.

    **Two columns are deliberately NOT required, and both would be bugs if they were.**
    ``vat_thb`` is NULL for a garage that is not VAT-registered, so requiring it would
    penalise the small garages for a tax status they do not have. ``cost_center``
    ships unfilled pending a partner answer, so requiring it would pin the KPI at 0%
    forever — vacuous in the opposite direction from the one AC-9 guards against, and
    just as useless.
    """
    if not row.governed or row.outcome in (LINK_OUTCOME_REJECTED, LINK_OUTCOME_REFUSED):
        return False
    if row.approver is None or row.approval_date is None:
        return False
    return all(
        value is not None
        for value in (
            row.document_date,
            row.tax_invoice_no,
            row.repair_order_no,
            row.vendor,
            row.vendor_code,
            row.plate,
            row.truck_code,
            row.work_type,
            row.description,
            row.amount_pre_vat_thb,
            row.total_thb,
        )
    )


def month_bounds(
    year: int, month: int, *, timezone: str = EXPORT_TIMEZONE
) -> tuple[datetime, datetime]:
    """The half-open UTC instants bounding one Thai accounting month.

    Half-open ``[start, end)`` on purpose: a closed upper bound either drops or
    double-counts a decision landing exactly on midnight, and month-end is precisely
    when a batch of approvals gets keyed.
    """
    zone = ZoneInfo(timezone)
    start_local = datetime(year, month, 1, tzinfo=zone)
    end_local = datetime(year + (month // 12), (month % 12) + 1, 1, tzinfo=zone)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)


def _approver_of(audit: Mapping[str, Any] | None, now: datetime) -> str | None:
    """Who authorised this spend — NOT ``audit_log.actor_person_id``.

    That column holds the RECORDER: on a provisional resolve it is ต้อม keying the
    record on the hard shoulder, not เฮีย who authorised it. Printing the recorder in
    an accounting document's ผู้อนุมัติ column would name the wrong human on paper
    that exists to say who approved the money — a wrong value that passes every
    check, which is worse than a blank one.

    **A refusal is checked FIRST, before any other state** (Cray, typed s192). A
    refused ratification means the authorisation was withdrawn: there is no approver,
    and letting a later state win would print a signature nobody gave.
    """
    if not audit:
        return None

    # The provisional path (ADR-0034 E-2) carries no `governed_decision` tie at first
    # resolve — deliberately, since naming the attested approver would assert an
    # in-system act that did not happen. The obligation block is the only record of
    # who authorised, so it is read first wherever it exists.
    if isinstance(audit.get(RATIFICATION_KEY), Mapping):
        view = ratification_state(audit, now)
        if view.state == "refused":
            return None
        return view.attested_approver_id

    # The ordinary governed path. `governed_decision` is a LIST, and the same list
    # carries `sod` and `severity_tier` ties with the SAME principal_id — filtering
    # on `doa_tier` picks the right CONTROL, not the right human, but reading the
    # list positionally would tie the answer to emission order.
    ties = audit.get("governed_decision")
    if isinstance(ties, list):
        for tie in ties:
            if not isinstance(tie, Mapping):
                continue
            ref = tie.get("control_ref")
            if isinstance(ref, Mapping) and ref.get("kind") == "doa_tier":
                principal_id = tie.get("principal_id")
                if isinstance(principal_id, str):
                    return principal_id
    return None


def _justification_ref_of(audit: Mapping[str, Any] | None) -> str | None:
    block = audit.get(RATIFICATION_KEY) if audit else None
    if isinstance(block, Mapping):
        ref = block.get("justification_ref")
        if isinstance(ref, str):
            return ref
    return None


def _vendor_code_index() -> dict[str, str]:
    """Vendor name → Express code, keyed on trimmed casefolded text.

    Names are matched EXACTLY once trimmed and case-folded — the rule the vendor
    registry states. Anything fuzzier would start MERGING garages the operator meant
    to keep apart, and a vendor code is what accounting posts against: a near-miss
    match posts one garage's repair to another garage's account.

    A vendor with no ``accounting_code`` is absent from this index rather than
    present-with-None. It is used but not yet opened in Express — a real state the
    export reports honestly as a blank column.
    """
    return {
        str(v["name"]).strip().casefold(): str(v["accounting_code"])
        for v in vendor_records()
        if v.get("accounting_code") and str(v.get("name", "")).strip()
    }


def _truck_index() -> dict[str, dict[str, Any]]:
    return {str(t["truck_id"]): t for t in truck_records()}


async def load_monthly_export(
    session: AsyncSession,
    *,
    year: int,
    month: int,
    now: datetime,
    timezone: str = EXPORT_TIMEZONE,
) -> MonthlyExport:
    """Read one accounting month of repair spend — governed rows and escaped rows.

    ``now`` is a parameter, not an ambient clock, for the reason
    :mod:`services.engine.procedures.ratification` states: overdue-ness is a function
    of the record and the clock, so an export re-run for last month must compute the
    exception labels that month's report showed, not today's.
    """
    start, end = month_bounds(year, month, timezone=timezone)

    # ---- source 1: cases a gate decided inside the month ------------------- #
    # The approval instant comes from the audit row, which is the only record of WHEN
    # the gate decided; `linked_at` is when the hook got around to writing the link.
    governed_stmt = (
        sa.select(
            RepairCaseRunLink.case_id,
            RepairCaseRunLink.run_id,
            RepairCaseRunLink.step_id,
            RepairCaseRunLink.outcome,
            RepairCaseRunLink.linked_at,
            AuditLog.occurred_at,
        )
        .join(
            AuditLog,
            sa.and_(
                AuditLog.run_id == RepairCaseRunLink.run_id,
                AuditLog.step_id == RepairCaseRunLink.step_id,
                AuditLog.action == GATE_DECISION_ACTION,
            ),
        )
        .where(AuditLog.occurred_at >= start, AuditLog.occurred_at < end)
        .order_by(RepairCaseRunLink.case_id, RepairCaseRunLink.linked_at)
    )
    governed_by_case: dict[str, dict[str, Any]] = {}
    for case_id, run_id, step_id, outcome, _linked_at, occurred_at in (
        await session.execute(governed_stmt)
    ).all():
        # Ascending `linked_at` means the last write wins: a ratification lands after
        # its provisional row and is the case's current position, which is exactly
        # what the export should show.
        governed_by_case[case_id] = {
            "run_id": run_id,
            "step_id": step_id,
            "outcome": outcome,
            "approved_at": occurred_at,
        }

    # ---- source 2: close-outs in the month with NO governed run at all ------ #
    linked_case_ids = set(
        (await session.execute(sa.select(RepairCaseRunLink.case_id).distinct())).scalars()
    )
    ungoverned_stmt = (
        sa.select(RepairCaseCloseout.case_id)
        .where(RepairCaseCloseout.entered_at >= start, RepairCaseCloseout.entered_at < end)
        .distinct()
    )
    ungoverned_case_ids = {
        case_id
        for case_id in (await session.execute(ungoverned_stmt)).scalars()
        if case_id not in linked_case_ids and case_id not in governed_by_case
    }

    vendor_codes = _vendor_code_index()
    trucks = _truck_index()
    rows: list[ExportRow] = []

    for case_id in sorted(set(governed_by_case) | ungoverned_case_ids):
        decision = governed_by_case.get(case_id)
        row = await _build_row(
            session,
            case_id=case_id,
            decision=decision,
            now=now,
            vendor_codes=vendor_codes,
            trucks=trucks,
        )
        rows.append(row)

    # Stable order: approval date, then case id. Rows without an approval date sort
    # last rather than raising — an ungoverned row has no approval instant and is
    # still a row somebody has to look at.
    rows.sort(key=lambda r: (r.approval_date is None, r.approval_date or date.min, r.case_id))
    return MonthlyExport(year=year, month=month, rows=tuple(rows))


async def _build_row(
    session: AsyncSession,
    *,
    case_id: str,
    decision: dict[str, Any] | None,
    now: datetime,
    vendor_codes: dict[str, str],
    trucks: dict[str, dict[str, Any]],
) -> ExportRow:
    """Assemble one Express entry from every source that has a fact about it.

    Every read here degrades to None rather than raising. The demo cases are the
    reason: they are real decisions about ids that were never inserted, so a case
    row genuinely may not exist for a link row that genuinely does — and an export
    that refused to render the demo would be showing the wrong product.
    """
    case = await session.get(RepairCase, case_id)
    closeout = await latest_closeout(session, case_id)
    order = await session.get(RepairCaseOrderNumber, case_id)

    audit: Mapping[str, Any] | None = None
    if decision is not None:
        step = (
            (
                await session.execute(
                    sa.select(StepResult).where(
                        StepResult.run_id == decision["run_id"],
                        StepResult.step_id == decision["step_id"],
                    )
                )
            )
            .scalars()
            .first()
        )
        audit = step.audit if step is not None else None

    truck = trucks.get(case.truck_id) if case is not None else None
    view = ratification_state(audit, now)
    outcome = decision["outcome"] if decision is not None else None
    # A rejected or refused decision has no approver to print, whatever else the
    # audit block carries — the same ordering Cray typed for the link outcome.
    approver = (
        None
        if outcome in (LINK_OUTCOME_REJECTED, LINK_OUTCOME_REFUSED)
        else _approver_of(audit, now)
    )
    approved_at: datetime | None = decision["approved_at"] if decision is not None else None

    return ExportRow(
        document_date=closeout.tax_invoice_date if closeout else None,
        approval_date=(
            approved_at.astimezone(ZoneInfo(EXPORT_TIMEZONE)).date() if approved_at else None
        ),
        repair_order_no=order.repair_order_no if order else None,
        tax_invoice_no=closeout.tax_invoice_no if closeout else None,
        vendor=closeout.vendor if closeout else None,
        vendor_code=(vendor_codes.get(closeout.vendor.strip().casefold()) if closeout else None),
        plate=str(truck["plate"]) if truck and truck.get("plate") else None,
        truck_code=(
            str(truck["accounting_code"]) if truck and truck.get("accounting_code") else None
        ),
        work_type=case.work_type if case else None,
        description=case.description if case else None,
        amount_pre_vat_thb=closeout.amount_pre_vat_thb if closeout else None,
        vat_thb=closeout.vat_thb if closeout else None,
        total_thb=closeout.total_thb if closeout else None,
        approver=approver,
        cost_center=None,
        case_id=case_id,
        governed=decision is not None,
        run_id=decision["run_id"] if decision is not None else None,
        outcome=outcome,
        exception_label=None if view.state == "none" else view.state,
        justification_ref=_justification_ref_of(audit),
    )
