"""The operate seed → governed approval → month-end ฿, end to end.

🔴 **The defect was not "no link was written" — that framing was checked and is
false.** ``synthetic.py`` attaches a ``case_id`` to its two breaching quotes
(``:48``, ``:269``, ``:290``), so the pre-fix seeded gate did resolve into real link
rows. What went wrong is what those rows *became*: those ids **exist only in the
fixture**, so the export's ``_build_row`` resolved case, close-out and order number
to ``None`` and emitted a hollow row — no description, vendor, plate, amounts or
sourcing basis — which scores against the KPI it appears on.

Two things follow, and this module pins both. A seeded run about a REAL case makes
the approval produce a **substantive** row. And the ฿ column can only ever come from
a close-out, which **nothing on the published surface can create** — no close-out UI
exists, and ``/closeout`` is not on the ingress allowlist — so without a settled case
the money column is zero by construction.

⚠️ **This basis named TWO excluded routes until PLAN-0112 Step 5; now it names one.**
``/accepted-quote`` **is** on the published allowlist as of Step 5 (SD-3(a), Cray typed
s243), so a published visitor can now drive a case to the GATE. The conclusion above is
unaffected: an approval is not an invoice, and the ฿ column needs the close-out that
``/closeout`` still guards. A governed visitor case lands in the export as an approved
row with a blank ฿ — which is what ``assert ours.total_thb is None`` below already pins.

Nothing is stubbed on either side. The producer is the real shipped seed
(``seed_repair_gate_waiting_human_run``, the same coroutine ``lifespan`` calls); the
consumer is the real ``resolve_gated_step`` driver firing the real registered hook,
and then the real month-end reader. A test that called ``link_resolved_cases``
directly would prove the writer works and say nothing about whether the seeded run
ever reaches it — and "the seeded run never reaches it" is the entire defect.

**The ฿ figure is asserted as computed, never as seeded.** The seed writes INPUT
only — a case, its quotes, its acceptance. Every number below is produced by the
engine from a real gate resolution; if a future change starts inserting export rows
directly, these assertions keep passing while the tab's *"fully traceable"* claim
becomes false, so ``test_the_seed_writes_no_export_rows_of_its_own`` pins that too.

DB-backed — SKIPS when Postgres is unreachable, and a skip is never satisfaction.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal

import pytest
import sqlalchemy as sa
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.config import settings
from services.db.repair_case import CASE_STATUS_CLOSED, RepairCase
from services.db.repair_case_run_link import RepairCaseRunLink
from services.db.repair_spend_export import (
    AUDIT_QUESTIONS,
    audit_answers,
    is_fully_traceable,
    load_monthly_export,
)
from services.engine import demo_events
from services.engine.procedures import gate_hooks
from services.engine.procedures.action_step import resolve_gated_step
from services.engine.procedures.spec import load_procedures
from verticals.fleet_maintenance import case_projection
from verticals.fleet_maintenance.operate_seed import (
    DEMO_CASE_ID,
    DEMO_HISTORY_CASE_ID,
    DEMO_RUN_ID,
    seed_repair_gate_waiting_human_run,
)
from verticals.fleet_maintenance.run_link import case_id_of

_VERTICAL = "fleet_maintenance"
_HERO = "governed_repair_approval"
_GATE_STEP = "approve"
_OWNER = "appr-owner"
_MECHANIC = "req-mechanic-tom"

_RAW_KEY = "test-key-req-mechanic-tom"
_DIGEST = hashlib.sha256(_RAW_KEY.encode("utf-8")).hexdigest()


@pytest.fixture(autouse=True)
def _clean() -> Iterator[None]:
    case_projection.reset()
    demo_events.reset(_VERTICAL)
    gate_hooks.clear_on_resolved()
    yield
    case_projection.reset()
    demo_events.reset(_VERTICAL)
    gate_hooks.clear_on_resolved()


@pytest.fixture
async def fleet_active(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.engine.discovery import discover_and_register
    from verticals.fleet_maintenance.procedures_factory import (
        register_fleet_maintenance_procedure_executors,
    )

    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    monkeypatch.setattr(settings, "oct_vertical", _VERTICAL)
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_keys", {_DIGEST: _MECHANIC})


def _person(person_id: str):
    spec = load_procedures(_VERTICAL)
    return next(p for p in spec.principals if p.person_id == person_id)


async def _resolve(session: AsyncSession, run_id: str, decisions: dict[str, str]):
    """Resolve the gate through the real driver, with the SoD inputs it demands."""
    spec = load_procedures(_VERTICAL)
    procedure = next(p for p in spec.procedures if p.procedure_id == _HERO)
    return await resolve_gated_step(
        session,
        run_id,
        _GATE_STEP,
        decisions,
        _person(_OWNER),
        procedure=procedure,
        principals=list(spec.principals),
    )


def _proposals(run) -> list[dict]:
    """The parked gate's proposal list, read the way the resolver reads it.

    ``output_set``, not ``decisions``: the latter is the post-resolution shape and is
    empty on a parked gate, so a test reading it would assert over nothing and pass.
    """
    approve = next(s for s in run.step_results if s.step_id == _GATE_STEP)
    return list((approve.artifact or {}).get("output_set") or [])


async def test_the_seeded_run_is_about_a_real_case(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """The seeded gate names the REAL case, not only the fixture's phantom ids.

    ⚠️ Deliberately asserts membership of ``DEMO_CASE_ID`` rather than "some case is
    named" — the weaker form passes on the pre-fix seed, because the synthetic
    breaching quotes already carry ``case-demo-truck01-axle`` and
    ``case-demo-truck03-gearbox``. Those are ids with no row behind them; asserting
    only that the gate names *a* case would be vacuous against the defect.
    """
    run = await seed_repair_gate_waiting_human_run(db_session, run_id=DEMO_RUN_ID)

    named = [case_id_of(p) for p in _proposals(run)]
    assert DEMO_CASE_ID in named, (
        f"the seeded gate names {named!r} — the real case is absent, so the approval "
        "would produce a row with no vendor, plate, amounts or sourcing basis"
    )


async def test_approving_the_seeded_gate_puts_a_substantive_row_on_the_report(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """Approve the seeded moment → a governed, SUBSTANTIVE row reaches the report.

    The approval is what creates the row — that causal link is the product. What it
    creates is now a row that says something: real approver, real run, real accepted
    figure and sourcing basis, where the pre-fix seed produced a shell.

    ⚠️ The ฿ column is asserted BLANK here, and that is not a gap in the test. Money
    arrives only with an invoice; the settled-history test covers the ฿ figure.
    """
    run = await seed_repair_gate_waiting_human_run(db_session, run_id=DEMO_RUN_ID)
    pending = _proposals(run)
    assert pending, "the seeded gate parked with no decidable proposal"
    # EVERY proposal needs a verdict — the gate refuses a partial resolution. Ours is
    # approved; the fixture breaches riding along are rejected.
    decisions = {
        str(p["action_id"]): ("approve" if case_id_of(p) == DEMO_CASE_ID else "reject")
        for p in pending
        if "action_id" in p
    }

    now = datetime.now(UTC)
    before = await load_monthly_export(db_session, year=now.year, month=now.month, now=now)
    assert before.total_thb == 0, (
        "this month already carries spend before the approval — the assertion below "
        "would pass on someone else's row and prove nothing"
    )

    await _resolve(db_session, DEMO_RUN_ID, decisions)
    assert (
        not gate_hooks.failures()
    ), f"the link hook is fail-soft, so it can swallow its own error: {gate_hooks.failures()!r}"

    linked = (
        (
            await db_session.execute(
                sa.select(RepairCaseRunLink).where(RepairCaseRunLink.case_id == DEMO_CASE_ID)
            )
        )
        .scalars()
        .all()
    )
    assert linked, "the gate resolved but no case↔run link was written"
    assert {row.run_id for row in linked} == {DEMO_RUN_ID}

    after = await load_monthly_export(db_session, year=now.year, month=now.month, now=now)
    ours = next((row for row in after.rows if row.case_id == DEMO_CASE_ID), None)
    assert ours is not None, "the gate resolved but the case never reached the report"

    # GOVERNED, with a real approver and a real approval date — the half the approval
    # produces. This is what was structurally unreachable before: the row exists
    # BECAUSE a human decided, not because anything was seeded.
    assert ours.governed is True
    assert ours.run_id == DEMO_RUN_ID
    assert ours.approver, "a governed row with no approver answers none of the audit questions"

    # 🔴 And the ฿ column is still EMPTY, deliberately. `total_thb` comes only from a
    # close-out (`_build_row`), i.e. from the invoice, which has not arrived. The
    # export's own rule is "no money, but spend was authorised → a row … the blank
    # fields are the honest report and the KPI counts them against us". Asserting the
    # blank is what stops a future change from quietly filling it from the accepted
    # quote, which would report money as spent before anyone was billed.
    assert ours.total_thb is None


async def test_the_settled_history_case_opens_the_kpi_on_a_real_figure(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """The month-end tab opens on ฿ that the reader computed from a real decision.

    Why this must exist at all, measured: on the published surface **nothing can ever
    produce a close-out** — there is no close-out UI in ``services/api/static/``, and
    ``/closeout`` is not on the ingress allowlist. So without a settled case the ฿
    column is structurally zero forever, and the tab whose entire subject is money would
    open empty on every visit for all time.

    ⚠️ ``/accepted-quote`` used to be named here as a second excluded route. It was
    admitted by PLAN-0112 Step 5 (SD-3(a)), so that half is gone — a visitor CAN now
    drive a case to the gate. It buys them an approval, not an invoice, so this test's
    subject is untouched: the money still arrives only through a close-out.

    The figure is still not fabricated: a real round, a real gate resolution by the
    owner, then the invoice. What is asserted is the reader's output, not the seed's
    input.
    """
    from verticals.fleet_maintenance.operate_seed import (
        DEMO_HISTORY_RUN_ID,
        seed_settled_history_case,
    )

    assert await seed_settled_history_case(db_session) is True

    now = datetime.now(UTC)
    export = await load_monthly_export(db_session, year=now.year, month=now.month, now=now)
    row = next((r for r in export.rows if r.case_id == DEMO_HISTORY_CASE_ID), None)
    assert row is not None, "the settled case never reached the month-end report"

    assert export.total_thb > 0, "the month-end tab still opens on ฿0"
    assert row.total_thb == Decimal("33705.00")
    # Governed by a REAL resolution — not an inserted link.
    assert row.governed is True
    assert row.run_id == DEMO_HISTORY_RUN_ID
    assert row.approver, "the settled row must name who approved it"
    # It is the traceable kind: this is the number the KPI headline is made of.
    unanswered = [q for q, ok in zip(AUDIT_QUESTIONS, audit_answers(row), strict=True) if not ok]
    assert is_fully_traceable(row), (
        "the opening figure is not fully traceable — the tab would open on a number "
        f"that scores against itself. Unanswered audit questions: {unanswered}"
    )


async def test_the_settled_case_is_closed_so_it_leaves_the_gate(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """A settled repair must not still be sitting in front of the visitor.

    ``governed_case_facts`` selects OPEN cases and says why a closed one is excluded:
    *"the work is done and the paperwork is keyed, so re-presenting one to the gate
    would ask for authority over spend that has already happened."* If this regressed,
    the demo would show a decided-and-paid repair as if it still needed approving, and
    the live round would carry two proposals where the story wants one.
    """
    from services.db.repair_case import RepairCase
    from verticals.fleet_maintenance.operate_seed import (
        seed_settled_history_case,
    )

    await seed_settled_history_case(db_session)

    settled = await db_session.get(RepairCase, DEMO_HISTORY_CASE_ID)
    assert settled is not None
    assert settled.status == CASE_STATUS_CLOSED

    run = await seed_repair_gate_waiting_human_run(db_session, run_id=DEMO_RUN_ID)
    named = {case_id_of(p) for p in _proposals(run)}
    assert DEMO_HISTORY_CASE_ID not in named, (
        "the settled repair is still being proposed for approval — a visitor would be "
        "asked to authorise spend that has already been invoiced and paid"
    )
    assert DEMO_CASE_ID in named


async def test_the_settled_repair_does_not_sit_in_the_visitors_approval_queue(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """The settled repair's OWN run must leave ``waiting_human``, not just its case.

    🔴 **The sibling above states this intent and cannot see it.** Its docstring says a
    regression would "show a decided-and-paid repair as if it still needed approving" —
    and that regression WAS live on the deployed system on 2026-08-18 while that test
    was green. It asserts the CASE is ``CLOSED`` (true) and that the case is absent
    from the NEXT run's proposals (true, ``governed_case_facts`` selects OPEN cases).
    The defect lives in neither field: ``seed_settled_history_case`` called
    ``resolve_gated_step`` without ``resume_run``, so the APPROVE step read ``resolved``
    while the RUN stayed ``waiting_human`` at 5/6 — and Tab H's queue counts RUNS, not
    cases. Measured on live: "2 WAITING ON YOU" where the story wants one.

    The money was never wrong (the close-out landed; the month-end cover read
    ฿33,705.00 over one row), which is why every offline oracle stayed green. This is
    an instrument that exists, aimed one field to the left of the damage.

    Nothing is stubbed: the producer is the real shipped ``seed_settled_history_case``
    (the same coroutine ``lifespan`` calls) and the reader below is the real run store.

    DB-backed — SKIPS when Postgres is unreachable, and a skip is never satisfaction.
    """
    from services.engine.procedures.persistence import load_run
    from services.engine.procedures.runs import PipelineRunStatus
    from verticals.fleet_maintenance.operate_seed import (
        DEMO_HISTORY_RUN_ID,
        seed_settled_history_case,
    )

    await seed_settled_history_case(db_session)
    await seed_repair_gate_waiting_human_run(db_session, run_id=DEMO_RUN_ID)

    history = await load_run(db_session, DEMO_HISTORY_RUN_ID)
    live = await load_run(db_session, DEMO_RUN_ID)
    assert history is not None and live is not None

    # The queue Tab H renders is a set of RUNS in ``waiting_human`` — read here from
    # the same store the Monitor reads, not recomputed.
    waiting = set()
    for run_id, loaded in ((DEMO_RUN_ID, live), (DEMO_HISTORY_RUN_ID, history)):
        if loaded.run.status == PipelineRunStatus.WAITING_HUMAN.value:
            waiting.add(run_id)

    # 🔴 THE POSITIVE HALF, and it is not decoration. The claim below is an ABSENCE,
    # and an absence passes for free the moment the reader goes blind: if the seed
    # ever wrote no runs at all, ``waiting`` would be empty and "the settled repair is
    # not in it" would be TRUE on a completely broken demo. This line is the known
    # positive the instrument must still find (CLAUDE.md §8: a zero or absence needs a
    # positive control that finds a known one). If it reddens, the test is untrustworthy
    # — not the system.
    assert DEMO_RUN_ID in waiting, (
        "the LIVE repair is not waiting on a human, so this test cannot tell "
        "'the settled repair correctly left the queue' from 'the queue reader is "
        "blind' — fix this before reading the assertion below"
    )

    # The claim. Stated as MEMBERSHIP, deliberately, not as set equality against
    # {DEMO_RUN_ID}: equality would couple this test to how many scenarios happen to
    # be seeded, so a legitimate third seed would redden it for a reason that has
    # nothing to do with settled repairs. Identity survives that; counts do not.
    assert DEMO_HISTORY_RUN_ID not in waiting, (
        f"the settled repair {DEMO_HISTORY_CASE_ID!r} is sitting in the visitor's "
        f"approval queue: its run {DEMO_HISTORY_RUN_ID!r} is {history.run.status!r} "
        f"even though the work is done, the invoice is keyed and the case is CLOSED "
        f"— a visitor is being asked to authorise spend that has already happened. "
        f"The '{_GATE_STEP}' step resolving is NOT enough: the seed must also resume "
        f"the run, which is what the HTTP path does in the same call "
        f"(routers/runs.py:19-21)"
    )


async def test_the_seed_writes_no_export_rows_of_its_own(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """Seeding alone must move NOTHING on the KPI — only a decision may.

    This is the honesty pin. Seeding input is legitimate; seeding output would make
    the tab's *"fully traceable"* claim true by assertion rather than by evidence,
    and a reader could not tell the difference from the number alone.
    """
    await seed_repair_gate_waiting_human_run(db_session, run_id=DEMO_RUN_ID)

    now = datetime.now(UTC)
    export = await load_monthly_export(db_session, year=now.year, month=now.month, now=now)
    assert export.total_thb == 0
    assert export.rows == ()


async def test_seeding_twice_writes_one_case(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """Idempotent on the case, matching the run's own contract.

    A restart must not pile up demo cases; two would put a second proposal in front
    of the visitor and double the KPI for a fleet that had one breakdown.
    """
    from verticals.fleet_maintenance.operate_seed import seed_demo_repair_case

    assert await seed_demo_repair_case(db_session) is True
    assert await seed_demo_repair_case(db_session) is False

    count = await db_session.scalar(
        sa.select(sa.func.count()).select_from(RepairCase).where(RepairCase.case_id == DEMO_CASE_ID)
    )
    assert count == 1
