"""Seed ONE persisted ``waiting_human`` repair-approval run for fleet's operate demo.

PLAN-0103 Step 7, under SD-5's ruling (a) (Cray, typed, s218): **seed one at boot AND
keep the visitor path.** Fleet's published set lands on Tab A but publishes Tab H
(Monitor), and until a visitor files a case at Tab I that Monitor opens EMPTY — the
first paint of the system whose whole pitch is "watch a decision get governed" showed
nothing being governed. This closes that, without removing the visitor path: the seed
supplies the first paint, the visitor still gets to watch their *own* case enter the
loop (AC-8's second clause).

**Why this is not a copy of procurement's seeder, and the difference is the point.**
``verticals.procurement.hero_demo.run.seed_operate_waiting_human_run`` must hand-build
an intake seed dict, because procurement's ``intake`` step declares no ``reads`` — its
QUERY slot is a hand-written ``_SeedQuery`` holding a cardinality-changing nest the v1
grammar cannot express. Fleet's ``intake`` **declares** ``input.reads`` + ``join`` +
``project`` (latest ``OperationalEvent`` per ``Truck`` with that truck's own
``minor_repair_ceiling_thb`` joined on), so it runs through the shipped
:class:`~services.engine.procedures.query_step.QueryStepExecutor` over the registry's
adapter. There is therefore **no seed to write here at all** — and no seam where a
hand-built fixture could disagree with what the procedure actually reads in production.
A declared procedure earns a shorter seeder, and it earns it without trading away the
truth of the data.

Contract, mirroring procurement's block by intent rather than by copy:

* **env-gated** — the caller checks ``settings.oct_demo_seed_operate``; this module is
  a plain coroutine and gates nothing itself;
* **idempotent** — a fixed ``run_id``; the caller skips when ``load_run`` already finds
  it, so a restart never piles up demo runs;
* **fail-soft at the call site** — a seed error must log and never block the demo boot;
  the Monitor then simply shows no run, which is the pre-Step-7 behaviour;
* **the SAME executors that resolve the gate** — taken from the registry rather than
  constructed here, so the run that parks and the resume that clears it cannot drift
  apart. The factory is registered immediately before this runs in the API lifespan.

The requester half of the SoD map (``{intake: req-mechanic-tom}``) is recorded on the
run by passing ``principal``, so a DISTINCT approver keeps SoD **governed** when the
gate is resolved — which is exactly the refused-then-granted moment fleet's card copy
promises a visitor.

Deterministic and host-state-free: the synthetic adapter, pure band math, pure AT-2
resolution, and the stubbed advisory prose the factory already wires (CLAUDE.md §8).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from services.db.repair_case import (
    CASE_STATUS_CLOSED,
    CASE_STATUS_OPEN,
    WORK_TYPE_BREAKDOWN,
    RepairCase,
)
from services.db.repair_case_closeout import (
    RepairCaseCloseout,
    allocate_repair_order_no,
)
from services.db.repair_case_evidence import (
    LOWEST_AT_ACCEPTANCE_RECORDED,
    RepairCaseAcceptedQuote,
    RepairCaseQuote,
)
from services.engine.procedures.action_step import resolve_gated_step
from services.engine.procedures.orchestrator import ProcedureError, RunResult
from services.engine.procedures.persistence import run_procedure_persisted
from services.engine.procedures.runs import StepResultStatus
from services.engine.procedures.spec import load_procedures
from services.engine.registry import registry
from verticals.fleet_maintenance import case_projection
from verticals.fleet_maintenance.run_link import case_id_of

_VERTICAL = "fleet_maintenance"
_PROCEDURE_ID = "governed_repair_approval"
_APPROVE_STEP = "approve"

#: The demo case the seeded run is ABOUT. Fixed like ``DEMO_RUN_ID`` and for the same
#: reason — idempotency — and separate from it because the two are seeded by different
#: mechanisms and can be skipped independently.
DEMO_CASE_ID = "case-fleet-operate-demo"

#: Every synthetic truck carries ``minor_repair_ceiling_thb = 5001`` (partner Q8), and
#: the sourcing-hygiene rule_gate demands three competing quotes above ฿30,000. The
#: seeded repair is priced ABOVE BOTH so the run exercises the whole spine rather than
#: the easy half: the per-truck ceiling breach routes it to the DOA ladder, and the
#: three distinct vendors satisfy the sourcing gate instead of tripping it.
_DEMO_QUOTES: tuple[tuple[str, str, str], ...] = (
    ("quote-fleet-demo-1", "อู่คู่สัญญา ปากช่อง", "38000.00"),
    ("quote-fleet-demo-2", "อู่เพื่อนช่าง สีคิ้ว", "42500.00"),
    ("quote-fleet-demo-3", "ศูนย์บริการโคราช", "45000.00"),
)

#: The already-settled repair the month-end KPI opens on. Its own case, run and
#: quotes: it must be a SECOND case, because a settled repair and a pending one are
#: different rows of the report and one case cannot be both.
DEMO_HISTORY_CASE_ID = "case-fleet-demo-history"
DEMO_HISTORY_RUN_ID = "run-fleet-demo-history"

#: Priced above the ฿30,000 sourcing threshold for the same reason as the live case,
#: and at a different figure so the two rows are never confused on the report.
_HISTORY_QUOTES: tuple[tuple[str, str, str], ...] = (
    ("quote-fleet-hist-1", "อู่คู่สัญญา ปากช่อง", "31500.00"),
    ("quote-fleet-hist-2", "อู่เพื่อนช่าง สีคิ้ว", "34000.00"),
    ("quote-fleet-hist-3", "ศูนย์บริการโคราช", "36800.00"),
)

#: VAT 7% on the accepted figure — the invoice as an accountant would key it.
_HISTORY_PRE_VAT = Decimal("31500.00")
_HISTORY_VAT = Decimal("2205.00")
_HISTORY_TOTAL = Decimal("33705.00")

#: The head mechanic — fleet's authored requester (``procedures.yaml`` principals).
#: He holds no approver role, which is what makes the seeded gate refusable by him
#: and grantable by the fleet manager or the owner.
_REQUESTER_ID = "req-mechanic-tom"

#: เฮีย, the owner — the tier a repair of this size routes to under the real ladder.
#: The history case is approved BY him so its link row carries a real approver, which
#: is one of the six audit questions the KPI scores.
_APPROVER_ID = "appr-owner"

#: The fixed demo run id. A constant, not a parameter default that callers vary:
#: idempotency is the whole point, and two ids would mean two demo runs.
DEMO_RUN_ID = "run-fleet-operate-demo"


async def _run_repair_round(session: AsyncSession, *, run_id: str) -> RunResult:
    """Fire one real ``governed_repair_approval`` round and persist it.

    Shared by both seeds on purpose: the settled history case and the live parked one
    must be produced by the SAME path, or the report's opening figure and the figure a
    visitor's approval adds would come from two different code paths that could drift.
    """
    spec = load_procedures(_VERTICAL)
    procedure = next(p for p in spec.procedures if p.procedure_id == _PROCEDURE_ID)
    agent = next(a for a in spec.agents if a.agent_id == procedure.run_by)
    requester = next(p for p in spec.principals if p.person_id == _REQUESTER_ID)

    # The registry's factory, not a local construction (see module docstring): the API
    # lifespan registers it one statement earlier, and every test that drives this must
    # do the same. A missing factory raises loudly here rather than silently seeding a
    # run the resolve endpoint would then 409 on.
    executors = registry.get_procedure_executors(_VERTICAL)()

    return await run_procedure_persisted(
        session,
        procedure,
        agent,
        executors,
        vertical=_VERTICAL,
        run_id=run_id,
        trigger_context={
            "source": "operate-demo-seed",
            "triggered_by": requester.person_id,
            # NOTE: no ``subject`` ref, unlike procurement's seed. Procurement can name
            # its asset because it hand-builds the intake seed; fleet's breaching truck
            # is chosen by the declared query DURING the run, so it is not knowable
            # before it. The Monitor row simply carries no subject — ``_resolve_subject``
            # already handles that — and inventing one here would mean asserting an
            # asset the run had not yet picked.
        },
        principal=requester,
    )


async def seed_demo_repair_case(session: AsyncSession, *, case_id: str = DEMO_CASE_ID) -> bool:
    """Seed the accepted repair case the demo run is ABOUT. True if it wrote one.

    🔴 **Why this exists — and the reason is NOT that the old seed named no case.**
    It did: ``synthetic.py`` attaches a ``case_id`` to its two breaching quotes
    (``:48``, ``:269``, ``:290``), so resolving the pre-fix gate genuinely wrote link
    rows. The defect was what those rows became on the report. Those ids *"exist only
    in the fixture"* (``repair_case_run_link``'s own docstring), so ``_build_row``
    looked up the case, the close-out and the order number and got **None for all
    three** — producing a month-end row with no description, no vendor, no plate, no
    amounts and no sourcing basis. A hollow shell that scores against the KPI.

    With a REAL accepted case on the stream, the SAME declared query picks it up and
    the row the approval produces is **substantive**: real vendor, real quotes, real
    accepted figure, real sourcing basis — the thing an accountant could actually key.
    The visitor's approval is still what creates it, which is the causal link the demo
    is selling; what changed is that the row it creates now says something.

    **What is seeded is INPUT, never OUTPUT.** This writes a case, its quotes and its
    acceptance — the things a human would have entered — and stops. The ฿ figure, the
    link row and every KPI cell are computed by the real engine from a real gate
    resolution. Inserting export rows directly would have been quicker and would have
    made the tab's own *"fully traceable"* claim a lie by construction.

    Idempotent on ``case_id``; the caller is fail-soft.
    """
    existing = await session.get(RepairCase, case_id)
    if existing is not None:
        return False

    now = datetime.now(UTC)
    session.add(
        RepairCase(
            case_id=case_id,
            # 🔴 truck-02, and the choice is load-bearing rather than arbitrary. The
            # declared query projects the LATEST OperationalEvent **per truck**, so a
            # live case DISPLACES whatever the fixture had for that truck. truck-01
            # carries the demo's flagship ฿48,000 axle breach (the row that passes
            # sourcing on `three_quotes`) and truck-03 the ฿15,000 `under_threshold`
            # one — seeding onto either silently deletes a governance example the demo
            # is built to show. Measured: on truck-01 this replaced the ฿48,000 row and
            # reddened `test_the_shipped_demo_passes_the_gate_on_its_own_evidence`,
            # which pins those two bases by equality.
            truck_id="truck-02",
            opened_by=_REQUESTER_ID,
            opened_at=now,
            description=(
                "เพลาขาดกลางทางแถวปากช่อง รถจอดข้างทางพร้อมของเต็มคัน " "อู่ประเมินต้องเปลี่ยนเพลาชุดใหญ่"
            ),
            status=CASE_STATUS_OPEN,
            work_type=WORK_TYPE_BREAKDOWN,
            photos=[],
        )
    )
    for quote_id, vendor, amount in _DEMO_QUOTES:
        session.add(
            RepairCaseQuote(
                quote_id=quote_id,
                case_id=case_id,
                vendor=vendor,
                amount_thb=Decimal(amount),
                entered_by=_REQUESTER_ID,
                entered_at=now,
            )
        )

    # FLUSH before the acceptance: ``repair_case_accepted_quote`` carries a COMPOSITE
    # foreign key to ``repair_case_quote`` on ``(tenant_id, case_id, quote_id)``, and
    # the unit of work is free to order the accepted row ahead of the quotes it points
    # at. Measured: without this, the insert fails ForeignKeyViolation on a quote the
    # same transaction is about to create. Same composite-FK edge PLAN-0105 hit from
    # the deletion side.
    await session.flush()

    chosen_id, _, chosen_amount = _DEMO_QUOTES[0]
    lowest = min(Decimal(amount) for _, _, amount in _DEMO_QUOTES)
    if Decimal(chosen_amount) != lowest:
        # Not defensive noise: the row below records `reason=None`, which is only
        # honest while the accepted quote IS the cheapest. Reordering `_DEMO_QUOTES`
        # would silently turn the seed into a non-lowest acceptance with no
        # justification — the exact state `accept_quote` returns 422 for.
        raise ProcedureError(
            f"fleet demo case {case_id!r}: the accepted quote {chosen_id!r} at "
            f"{chosen_amount} is not the lowest on file ({lowest}) — a non-lowest "
            "acceptance owes a reason, so the seed would write a row the API refuses"
        )
    session.add(
        RepairCaseAcceptedQuote(
            accepted_id=f"accepted-{uuid.uuid4().hex[:12]}",
            case_id=case_id,
            quote_id=chosen_id,
            # The CHEAPEST of the three is accepted, so no reason is owed and the row
            # is an ordinary approval. Accepting a dearer one would have demanded a
            # justification and labelled the KPI row an exception — a louder demo, but
            # one that misrepresents the ordinary path as the common case.
            reason=None,
            accepted_by=_REQUESTER_ID,
            accepted_at=now,
            lowest_amount_at_acceptance_thb=lowest,
            # ``recorded``, NOT ``reconstructed`` — and the distinction is a ruled one
            # (PLAN-0099 D1 §Provenance, Cray's SD-2). ``reconstructed`` means
            # specifically *"migration 0023 derived this afterwards from the quote
            # rows"*, which is not what happened here: this figure is computed at the
            # instant of its own acceptance, exactly as the write path does it. Marking
            # it reconstructed would be a false provenance claim, not a cautious one.
            lowest_at_acceptance_basis=LOWEST_AT_ACCEPTANCE_RECORDED,
        )
    )
    await session.commit()
    return True


async def seed_settled_history_case(session: AsyncSession) -> bool:
    """Seed ONE already-settled repair so the month-end KPI opens on a real figure.

    🔴 **Why this is necessary rather than decorative, and the measurement behind it.**
    The ฿ column comes from a CLOSE-OUT (`repair_spend_export._build_row`: ``total_thb
    = closeout.total_thb if closeout else None``), and on the published surface a
    close-out **cannot be created by anyone**: there is no close-out UI anywhere in
    ``services/api/static/``, and ``/api/cases/{id}/closeout`` is **not on the
    system's ingress allowlist**. Neither is ``/accepted-quote``. So no visitor-created
    case can reach the gate, and no amount of visitor activity can ever put money on
    the report. Without this seed the KPI is **structurally ฿0 forever** — not empty
    until someone acts, but empty by construction.

    **It is still not a fabricated number.** This drives the same path a real repair
    takes — case, quotes, acceptance, a REAL run through the shipped procedure, a REAL
    gate resolution by the owner, then the invoice — and lets the reader compute the
    figure. The one thing written directly is the close-out itself, which is what the
    accountant keys from the paper invoice; nothing writes a link row or an export row.

    **Closed at the end, deliberately.** ``governed_case_facts`` selects OPEN cases,
    and its docstring gives the reason this one must not stay open: *"the work is done
    and the paperwork is keyed, so re-presenting one to the gate would ask for
    authority over spend that has already happened."* Leaving it open would also put a
    settled repair in front of the visitor as if it still needed a decision. ⚠️ This is
    the first code path in the repo that closes a case; PLAN-0105 SD-3 noted that none
    existed, and a retention exemption keyed on OPEN would now behave differently.

    Idempotent on the case id; the caller is fail-soft.
    """
    if await session.get(RepairCase, DEMO_HISTORY_CASE_ID) is not None:
        return False

    now = datetime.now(UTC)
    session.add(
        RepairCase(
            case_id=DEMO_HISTORY_CASE_ID,
            # Also truck-02, and safe for the same reason the live case is: it is
            # CLOSED before the live round fires, so it leaves the event stream and
            # never competes for the truck's latest-event slot.
            truck_id="truck-02",
            opened_by=_REQUESTER_ID,
            opened_at=now,
            description="ปั๊มลมเบรกรั่ว เปลี่ยนชุดปั๊มลมพร้อมสายลม ซ่อมเสร็จและรับรถแล้ว",
            status=CASE_STATUS_OPEN,
            work_type=WORK_TYPE_BREAKDOWN,
            photos=[],
        )
    )
    for quote_id, vendor, amount in _HISTORY_QUOTES:
        session.add(
            RepairCaseQuote(
                quote_id=quote_id,
                case_id=DEMO_HISTORY_CASE_ID,
                vendor=vendor,
                amount_thb=Decimal(amount),
                entered_by=_REQUESTER_ID,
                entered_at=now,
            )
        )
    # Same composite-FK flush as the live case above, for the same measured reason.
    await session.flush()

    chosen_id, chosen_vendor, chosen_amount = _HISTORY_QUOTES[0]
    lowest = min(Decimal(amount) for _, _, amount in _HISTORY_QUOTES)
    if Decimal(chosen_amount) != lowest:
        raise ProcedureError(
            f"fleet history case: accepted quote {chosen_id!r} at {chosen_amount} is not "
            f"the lowest ({lowest}) — the row below records no reason and would be a "
            "non-lowest acceptance the API refuses"
        )
    session.add(
        RepairCaseAcceptedQuote(
            accepted_id=f"accepted-{uuid.uuid4().hex[:12]}",
            case_id=DEMO_HISTORY_CASE_ID,
            quote_id=chosen_id,
            reason=None,
            accepted_by=_REQUESTER_ID,
            accepted_at=now,
            lowest_amount_at_acceptance_thb=lowest,
            lowest_at_acceptance_basis=LOWEST_AT_ACCEPTANCE_RECORDED,
        )
    )
    await session.commit()

    # The REAL round + the REAL gate driver — this is what makes the row `governed`
    # and gives it an approver. Writing a RepairCaseRunLink here instead would put a
    # traceable-looking row on the report that no decision ever produced.
    await case_projection.refresh(session)
    run = await _run_repair_round(session, run_id=DEMO_HISTORY_RUN_ID)
    approve_step = next((s for s in run.step_results if s.step_id == _APPROVE_STEP), None)
    # ``output_set`` is the PARKED gate's proposal list — the same key
    # ``resolve_gated_step`` itself reads (``action_step.py:766``). ``decisions`` is the
    # post-resolution shape and is empty here; reading it would silently decide nothing.
    pending = list((approve_step.artifact or {}).get("output_set") or []) if approve_step else []
    ours = [p for p in pending if case_id_of(p) == DEMO_HISTORY_CASE_ID]
    if not ours:
        raise ProcedureError(
            f"fleet history case: the seeded round proposed nothing about "
            f"{DEMO_HISTORY_CASE_ID!r} — it would close with no approver and land on "
            "the report as ungoverned spend, which is the opposite of the point"
        )

    # EVERY proposal must get a verdict: the gate refuses a partial resolution,
    # because silence about a proposed spend is what an audit trail must not contain.
    # The fixture breaches riding along in the same round are rejected — they are not
    # this repair, and approving them would invent spend nobody authorised.
    decisions = {
        str(p["action_id"]): ("approve" if case_id_of(p) == DEMO_HISTORY_CASE_ID else "reject")
        for p in pending
        if "action_id" in p
    }
    spec = load_procedures(_VERTICAL)
    procedure = next(p for p in spec.procedures if p.procedure_id == _PROCEDURE_ID)
    approver = next(p for p in spec.principals if p.person_id == _APPROVER_ID)
    await resolve_gated_step(
        session,
        DEMO_HISTORY_RUN_ID,
        _APPROVE_STEP,
        decisions,
        approver,
        procedure=procedure,
        principals=list(spec.principals),
    )

    # The repair-order number, allocated the SAME way ``key_closeout`` allocates it
    # (`routers/cases.py:818`) rather than invented here — it is gap-free within a
    # year by construction, so a hand-written string would either collide with a real
    # allocation or open a hole an auditor would ask about. It is also one of the
    # eleven columns ``is_fully_traceable`` requires: without it the opening figure
    # would render as spend that scores against its own KPI.
    await allocate_repair_order_no(session, case_id=DEMO_HISTORY_CASE_ID, year=now.year, now=now)
    session.add(
        RepairCaseCloseout(
            closeout_id=f"closeout-{uuid.uuid4().hex[:12]}",
            case_id=DEMO_HISTORY_CASE_ID,
            vendor=chosen_vendor,
            tax_invoice_no="INV-2026-0815",
            tax_invoice_date=now.date(),
            amount_pre_vat_thb=_HISTORY_PRE_VAT,
            vat_thb=_HISTORY_VAT,
            total_thb=_HISTORY_TOTAL,
            entered_by=_REQUESTER_ID,
            entered_at=now,
        )
    )
    settled = await session.get(RepairCase, DEMO_HISTORY_CASE_ID)
    if settled is not None:
        settled.status = CASE_STATUS_CLOSED
    await session.commit()
    await case_projection.refresh(session)
    return True


async def seed_repair_gate_waiting_human_run(
    session: AsyncSession,
    *,
    run_id: str = DEMO_RUN_ID,
) -> RunResult:
    """Run ``governed_repair_approval`` to its ``approve`` gate and persist it parked.

    Returns the persisted :class:`RunResult` — reachable by ``GET /runs/{run_id}`` and
    counted by ``GET /runs``'s ``waiting_human_count``, which is what Tab H reads.

    Raises :class:`ProcedureError` if the run does **not** park at ``waiting_human``.
    That is deliberate and is not defensive noise: a run that completed instead of
    parking would leave the Monitor with nothing to act on while every status line
    still said "seeded", which is precisely the silent-success shape this PLAN keeps
    catching. The caller wraps this fail-soft, so the loud failure lands in the boot
    log rather than in a visitor's browser.
    """
    # 🔴 ORDER IS LOAD-BEARING, and it is the reverse of ``lifespan``'s own.
    # The case must be on the event stream BEFORE the query step runs, or the
    # proposal carries no ``case_id`` and resolving the gate writes no link — the
    # exact ฿0 seam this seeds against. ``lifespan`` refreshes ``case_projection``
    # AFTER calling this function (it has other reasons to), so relying on that
    # refresh would seed a run built one boot too early. The precondition therefore
    # lives here, with the thing whose correctness depends on it.
    await seed_demo_repair_case(session)
    await case_projection.refresh(session)

    result = await _run_repair_round(session, run_id=run_id)

    approve = next((s for s in result.step_results if s.step_id == _APPROVE_STEP), None)
    if approve is None or approve.status != StepResultStatus.WAITING_HUMAN.value:
        raise ProcedureError(
            f"fleet operate-demo seed {run_id!r}: the {_APPROVE_STEP!r} gate did not park at "
            f"waiting_human (status {approve.status if approve else None!r}) — Tab H would "
            "open empty while the boot log reported a seeded run"
        )
    return result
