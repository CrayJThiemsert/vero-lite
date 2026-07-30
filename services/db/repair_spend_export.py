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

import csv
import io
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
    LINK_OUTCOME_APPROVED,
    LINK_OUTCOME_PROVISIONAL,
    LINK_OUTCOME_RATIFIED,
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
    #: Why this spend passed the sourcing rule — the basis the gate ACTUALLY SAW,
    #: read from the link row rather than recomputed (alembic ``0022``; Cray, typed
    #: s193). None for an ungoverned row, which never had a sourcing decision made
    #: on it at all — an absence the proxy reports rather than papers over.
    three_quote_basis: str | None


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

    @property
    def total_thb(self) -> Decimal:
        return sum((row.total_thb or Decimal(0) for row in self.rows), Decimal(0))

    @property
    def ungoverned_thb(self) -> Decimal:
        """The baht that never passed a governed run.

        Reported in money as well as in row count because they answer different
        questions: ten ฿800 rows and one ฿90,000 row are the same count and very
        different problems, and a count-only cover lets the expensive one hide.
        """
        return sum((row.total_thb or Decimal(0) for row in self.ungoverned_rows), Decimal(0))

    def cover_summary(self) -> CoverSummary:
        """The cover page — AC-9's KPI plus the audit-answer proxy."""
        answered = sum(sum(audit_answers(row)) for row in self.rows)
        askable = len(self.rows) * len(AUDIT_QUESTIONS)
        return CoverSummary(
            year=self.year,
            month=self.month,
            row_count=len(self.rows),
            traceable_row_count=self.traceable_row_count,
            traceability_pct=self.traceability_pct,
            audit_answer_pct=(100.0 * answered / askable) if askable else None,
            ungoverned_row_count=len(self.ungoverned_rows),
            ungoverned_thb=self.ungoverned_thb,
            total_thb=self.total_thb,
            outstanding_ratification_count=len(self.outstanding_ratifications),
        )


@dataclass(frozen=True)
class CoverSummary:
    """The two numbers AC-9 puts on the cover, plus the context they need to be read.

    ``traceability_pct`` is the headline: a row either answers the audit question end
    to end or it does not. ``audit_answer_pct`` is the softer companion — of all the
    questions we could ask of this month, what share have an answer — and it exists
    because the headline is all-or-nothing: a month that went from "nothing recorded"
    to "everything but the invoice number" shows no movement on the KPI at all, and a
    partner improving their process deserves to see that it moved.
    """

    year: int
    month: int
    row_count: int
    traceable_row_count: int
    traceability_pct: float | None
    audit_answer_pct: float | None
    ungoverned_row_count: int
    ungoverned_thb: Decimal
    total_thb: Decimal
    outstanding_ratification_count: int


#: The questions an auditor asks of one line of repair spend. Named as data so the
#: proxy's denominator is inspectable rather than a magic number inside a division.
#:
#: The sourcing question was ABSENT until alembic ``0022``, and the reason it could
#: not be asked is worth keeping: the basis existed only inside the persisted event
#: dict, so answering it meant either walking JSONB reasoning traces or recomputing
#: — and `compute_three_quote` forbids recomputation in its own docstring. Cray typed
#: option (ก) at s193: persist it at decision time. The question is now askable
#: because the answer is recorded, not because the reader got cleverer.
AUDIT_QUESTIONS = (
    "who approved it",
    "when was it approved",
    "which governed run decided it",
    "what paper backs it",
    "why was it an exception",
    "why did it pass sourcing",
)


def audit_answers(row: ExportRow) -> tuple[bool, ...]:
    """Which of :data:`AUDIT_QUESTIONS` this row can answer, in order.

    The exception question is answered when there is nothing to explain: a case with
    no ratification obligation is not missing a justification, and scoring it as
    unanswered would penalise every ordinary approval for the existence of the
    emergency path.

    The sourcing question is NOT given that treatment. An ungoverned row has no basis
    because no gate ever judged its sourcing, and that is exactly the gap the report
    exists to surface — scoring it "not applicable" would let escaped money improve
    the proxy by virtue of having escaped.
    """
    return (
        row.approver is not None,
        row.approval_date is not None,
        row.run_id is not None,
        row.tax_invoice_no is not None and row.document_date is not None,
        row.exception_label is None or row.justification_ref is not None,
        row.three_quote_basis is not None,
    )


#: The link outcomes that mean spend was AUTHORISED. A case in one of these states
#: belongs in the month even before its paperwork lands — Cray's decision 3 requires
#: exactly that: approved 15 July, closed 3 August, filed as a JULY row with blank
#: invoice fields.
APPROVING_LINK_OUTCOMES = (
    LINK_OUTCOME_APPROVED,
    LINK_OUTCOME_PROVISIONAL,
    LINK_OUTCOME_RATIFIED,
)


def is_reportable(row: ExportRow) -> bool:
    """Whether this decision belongs in a file accounting keys as SPEND.

    Surfaced by the end-to-end scenario, not by any unit test: the hero round decides
    the demo fixture cases alongside the real one, and rejecting them produced link
    rows with no approver, no invoice and no amounts. Those were landing in the export
    as zero-baht Express entries — lines an accountant would have to key into a ledger
    to record that nothing happened.

    The rule that follows, stated once:

    * **Money exists → always a row**, governed or not. A close-out is real spend, and
      a REJECTED case that still has one is the worst case in the whole report — the
      repair the approver declined and somebody paid for anyway. It must never be
      filtered out by the same rule that removes noise.
    * **No money, but spend was authorised → a row.** The invoice has not arrived yet;
      the blank fields are the honest report and the KPI counts them against us.
    * **No money and no authorisation → not a row.** A rejected proposal that was
      never paid is a governance record, not a line of spend. It is fully visible in
      the audit trail and in ``repair_case_run_link``; putting it in an accounting
      export would mean keying a ฿0 entry to record that nothing happened.
    """
    if row.total_thb is not None:
        return True
    return row.outcome in APPROVING_LINK_OUTCOMES


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


#: Excel on Windows reads a BOM-less UTF-8 file as the system codepage, which turns
#: every Thai column header and every vendor name into mojibake. เมย์ opens this file
#: by double-clicking it, so the BOM is not a nicety — without it the export is
#: unreadable to the one person who has to key it, while being perfectly valid UTF-8
#: to every tool that would be used to check it.
CSV_ENCODING = "utf-8-sig"


def _cell(value: object) -> str:
    """One CSV cell. ``None`` renders as empty — the honest blank the KPI counts.

    ``Decimal`` is rendered by ``str`` and never by ``float``: the column is money
    that accounting reconciles against paper, and a binary float would introduce a
    rounding difference in the only place it is guaranteed to be noticed.
    """
    if value is None:
        return ""
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def to_csv(export: MonthlyExport) -> str:
    """Render the month as Express-keyable CSV — the 15 columns, nothing else.

    **The cover summary is deliberately NOT prepended.** A preamble above the header
    row is what makes a file human-friendly and machine-hostile: Express keys from
    this, and any importer would have to be told how many lines to skip — a number
    that silently becomes wrong the first time the cover grows a line. The cover is
    served as its own JSON resource instead, so the file stays exactly what it claims
    to be and the numbers stay machine-readable rather than parsed back out of prose.

    Dates render ISO. The partner's own paperwork is Thai-formatted, but this file is
    keyed into another system rather than read as a document, and ISO is the one
    format no locale reinterprets — `03/07/2026` is two different days depending on
    who opens it.
    """
    buffer = io.StringIO()
    # QUOTE_MINIMAL with the default dialect: `รายการซ่อม` is free text a mechanic
    # typed and will contain commas, and an unquoted comma there would shift every
    # later cell one column left for that row only — a corruption that looks like
    # data rather than like an error.
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(EXPORT_COLUMNS)
    for row in export.rows:
        writer.writerow(
            [
                _cell(row.document_date),
                _cell(row.approval_date),
                _cell(row.repair_order_no),
                _cell(row.tax_invoice_no),
                _cell(row.vendor),
                _cell(row.vendor_code),
                _cell(row.plate),
                _cell(row.truck_code),
                _cell(row.work_type),
                _cell(row.description),
                _cell(row.amount_pre_vat_thb),
                _cell(row.vat_thb),
                _cell(row.total_thb),
                _cell(row.approver),
                _cell(row.cost_center),
            ]
        )
    return buffer.getvalue()


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
            RepairCaseRunLink.three_quote_basis,
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
    for case_id, run_id, step_id, outcome, basis, _linked_at, occurred_at in (
        await session.execute(governed_stmt)
    ).all():
        # Ascending `linked_at` means the last write wins: a ratification lands after
        # its provisional row and is the case's current position, which is exactly
        # what the export should show.
        governed_by_case[case_id] = {
            "run_id": run_id,
            "step_id": step_id,
            "outcome": outcome,
            "three_quote_basis": basis,
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
        if is_reportable(row):
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
        three_quote_basis=decision["three_quote_basis"] if decision is not None else None,
    )
