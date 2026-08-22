"""AC-7(i) — the demo reset and a REAL visitor-fired run coexist. The bound is MEASURED.

The mandatory scenario test (CLAUDE.md §8): the real producer driven into the real
consumer on realistic data, with no mocked seam on either side.

* the producer is the **Step 3 accept seam** — ``POST /api/cases/{id}/accepted-quote``,
  the route the published profile exposes, which fires the governed run. Not a synthetic
  ``PipelineRun`` row: ``test_fleet_demo_reset_scenario.py``'s AC-5 decoy already covers
  hand-inserted rows, and a hand-inserted row cannot exercise the one thing this module
  is about — link rows written by the real ``on_resolved`` hook against real case ids;
* the consumer is ``services.db.demo_run_reset.reset_demo_runs``, the operator's own
  entry point, in execute mode;
* the re-boot is ``services.api.main._seed_fleet_operate_demo``, the ACTUAL boot block.

🔴 **AC-7(i)'s wording is narrower than the truth, and this module is where that was
measured.** The AC reads *"the visitor run, its step results, and its link rows
survive"*. Measured on a real visitor-fired run whose own case was ``case-c923c43a...``,
resolving its ``approve`` gate wrote **three** link rows::

    ['case-c923c43a814c', 'case-demo-truck03-gearbox', 'case-fleet-operate-demo']

Two facts compose to produce that, and neither is visible from the AC's text:

1. fleet's ``intake`` step is a **fleet-wide scan**, not a lookup of the accepted case
   (measured s243 — it is why AC-2's original pass read was false in the shipped demo).
   So every visitor-fired run gates on a proposal set that ALSO contains the seeded demo
   case, and the ``on_resolved`` hook writes one link row per proposed case, never one
   per run;
2. the reset clears link rows on BOTH keys — ``run_id IN DEMO_RUN_IDS`` **OR**
   ``case_id IN DEMO_CASE_IDS`` (``demo_run_reset._delete_run_side``).

Therefore **every** visitor-fired run loses its ``case-fleet-operate-demo`` link row to a
reset, whatever case the visitor accepted on. The surviving bound, asserted below, is:

* the visitor's **run** survives, field-for-field;
* its **step results** survive;
* its link rows for **non-demo cases** survive — including its own;
* its link rows for **demo cases** are deleted — **by design, not by defect**: the reset
  erases and re-seeds ``case-fleet-operate-demo``, so a surviving link would point at a
  DIFFERENT case that merely reuses the id (``_delete_run_side``'s docstring).

The audit chain is untouched by any of this — ``audit_log`` is outside the reset's
transaction entirely, so the approval itself remains provable after the link row goes.

DB-backed — SKIPS when Postgres is unreachable, and a skip is never satisfaction.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

import services.api.main as api_main
from services.api.config import settings
from services.db.demo_run_reset import (
    DEMO_CASE_IDS,
    DEMO_RUN_IDS,
    STATE_PRISTINE,
    read_demo_state,
    reset_demo_runs,
)
from services.db.repair_case import RepairCase
from services.db.repair_case_run_link import RepairCaseRunLink
from services.engine import demo_events
from services.engine.procedures import gate_hooks
from services.engine.procedures.persistence import load_run
from services.engine.procedures.runs import PipelineRun, PipelineRunStatus, StepResultStatus
from verticals.fleet_maintenance import case_projection
from verticals.fleet_maintenance.operate_seed import DEMO_CASE_ID

_VERTICAL = "fleet_maintenance"
_HERO = "governed_repair_approval"
_APPROVE = "approve"
_FULFILL = "fulfill"

_MECHANIC = "req-mechanic-tom"
_OWNER = "appr-owner"
_MECHANIC_KEY = "test-key-req-mechanic-tom"
_OWNER_KEY = "test-key-appr-owner"
_HEADERS = {"Authorization": f"Bearer {_MECHANIC_KEY}"}
_OWNER_HEADERS = {"Authorization": f"Bearer {_OWNER_KEY}"}


def _digest(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@pytest.fixture(autouse=True)
def _clean() -> Iterator[None]:
    """Both caches and the hook registry are process-global; a leak makes a later test lie."""
    case_projection.reset()
    demo_events.reset(_VERTICAL)
    gate_hooks.clear_on_resolved()
    yield
    case_projection.reset()
    demo_events.reset(_VERTICAL)
    gate_hooks.clear_on_resolved()


@pytest.fixture
async def fleet_active(
    monkeypatch: pytest.MonkeyPatch, api_db_maker: async_sessionmaker[AsyncSession]
) -> None:
    """Register EXACTLY what the API lifespan registers, authn ON, boot seeder pointed at
    the DISPOSABLE test database.

    ``register_fleet_maintenance_procedure_executors`` is what arms the ``on_resolved``
    link hook (``procedures_factory.py:84``). Without it every link-row assertion below
    would read an empty table and pass for the wrong reason.
    """
    from services.engine.discovery import discover_and_register
    from verticals.fleet_maintenance.procedures_factory import (
        register_fleet_maintenance_procedure_executors,
    )

    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    monkeypatch.setattr(settings, "oct_vertical", _VERTICAL)
    monkeypatch.setattr(settings, "oct_demo_seed_operate", True)
    monkeypatch.setattr(settings, "oct_demo_time_anchor", False)
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(
        settings,
        "api_keys",
        {_digest(_MECHANIC_KEY): _MECHANIC, _digest(_OWNER_KEY): _OWNER},
    )
    monkeypatch.setattr(api_main, "async_session", api_db_maker)


async def _boot(session: AsyncSession) -> None:
    """One boot of the REAL seed block, then re-read the caches it populated."""
    await api_main._seed_fleet_operate_demo(_VERTICAL)
    await case_projection.refresh(session)


def _row_snapshot(row: Any) -> dict[str, Any]:
    """Every mapped column of one ORM row, for a field-by-field re-read comparison."""
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


async def _hero_run_ids(client: AsyncClient) -> set[str]:
    """The hero-procedure run ids Tab H itself would paint, read through the real route."""
    listed = await client.get("/runs", headers=_HEADERS)
    assert listed.status_code == 200, listed.text
    return {r["run_id"] for r in listed.json()["runs"] if r["procedure_id"] == _HERO}


async def _quote(client: AsyncClient, case_id: str, vendor: str, amount: str) -> str:
    quoted = await client.post(
        f"/api/cases/{case_id}/quotes",
        data={"vendor": vendor, "amount_thb": amount},
        headers=_HEADERS,
    )
    assert quoted.status_code == 201, quoted.text
    quote_id: str = quoted.json()["quote_id"]
    return quote_id


async def _open_case_with_quotes(client: AsyncClient) -> tuple[str, list[str]]:
    """A real axle breakdown with three garages compared — the visitor's OWN case."""
    opened = await client.post(
        "/api/cases",
        json={
            "truck_id": "truck-01",
            "work_type": "breakdown",
            "description": "เพลาขาดกลางทางแถวปากช่อง",
        },
        headers=_HEADERS,
    )
    assert opened.status_code == 201, opened.text
    case_id: str = opened.json()["case_id"]
    quotes = [
        await _quote(client, case_id, "ส.เจริญยนต์", "58000.00"),
        await _quote(client, case_id, "อู่ริมทางปากช่อง", "62000.00"),
        await _quote(client, case_id, "อู่ช่างเล็ก", "59500.00"),
    ]
    return case_id, quotes


async def _accept(client: AsyncClient, case_id: str, quote_id: str) -> None:
    accepted = await client.post(
        f"/api/cases/{case_id}/accepted-quote",
        json={"quote_id": quote_id, "reason": "เจ้าเดียวที่มีเพลาพร้อมเปลี่ยนวันนี้"},
        headers=_HEADERS,
    )
    assert accepted.status_code == 201, accepted.text


async def _resolve_approve(client: AsyncClient, session: AsyncSession, run_id: str) -> str:
    """Resolve the ``approve`` gate through the REAL endpoint — this is what fires the
    ``on_resolved`` hook that writes the link rows. Returns the resulting run status."""
    loaded = await load_run(session, run_id)
    assert loaded is not None, f"{run_id} is not persisted"
    step = next((s for s in loaded.step_results if s.step_id == _APPROVE), None)
    assert step is not None, f"{run_id} has no {_APPROVE} step"
    decisions = {
        str(p["action_id"]): "approve"
        for p in ((step.artifact or {}).get("output_set") or [])
        if "action_id" in p
    }
    assert decisions, f"{run_id}'s {_APPROVE} gate proposed nothing to decide"
    response = await client.post(
        f"/runs/{run_id}/gate/resolve",
        json={"step_id": _APPROVE, "decisions": decisions},
        headers=_OWNER_HEADERS,
    )
    assert response.status_code == 200, response.text
    status: str = response.json()["run_status"]
    return status


async def _links_for(session: AsyncSession, *, run_id: str) -> list[RepairCaseRunLink]:
    """Every link row this run wrote, re-read from the database."""
    rows = await session.execute(
        sa.select(RepairCaseRunLink).where(RepairCaseRunLink.run_id == run_id)
    )
    return list(rows.scalars().all())


def _partition(links: list[RepairCaseRunLink]) -> tuple[list[str], list[str]]:
    """``(demo_scoped_link_ids, other_link_ids)`` — the split the reset actually makes."""
    demo = sorted(link.link_id for link in links if link.case_id in DEMO_CASE_IDS)
    other = sorted(link.link_id for link in links if link.case_id not in DEMO_CASE_IDS)
    return demo, other


async def _fire_visitor_run(client: AsyncClient, *, case_id: str, quote_id: str) -> str:
    """Accept a quote and return the run id the seam actually minted.

    The id is taken as the DIFFERENCE across ``GET /runs`` rather than from the accept
    response: an endpoint that returns the object it just wrote proves only that it
    returned it, and Tab H reads this payload.
    """
    before = await _hero_run_ids(client)
    await _accept(client, case_id, quote_id)
    after = await _hero_run_ids(client)
    minted = after - before
    assert len(minted) == 1, (
        f"accepting a quote on {case_id} minted {sorted(minted)} — exactly one governed "
        "run is the promise. Zero means the fire was swallowed (SD-P4 backpressure does "
        "it silently); more than one means the seam fired twice."
    )
    return minted.pop()


async def _park_with_link_rows(
    client: AsyncClient, session: AsyncSession, *, case_id: str, quote_id: str
) -> tuple[str, list[RepairCaseRunLink]]:
    """AC-7(i)'s precondition: a visitor-fired run PARKED, with link rows written.

    Both halves need the ``approve`` resolution. Before it the run is parked but the
    ``on_resolved`` hook has not fired, so there is nothing to protect; after it the run
    parks AGAIN at ``fulfill`` — ``governed_repair_approval``'s terminal step is itself
    gated — so it is still ``waiting_human``. That is the only state satisfying "parked
    AND linked", and it is reached entirely through the real routes.
    """
    run_id = await _fire_visitor_run(client, case_id=case_id, quote_id=quote_id)
    status = await _resolve_approve(client, session, run_id)
    assert status == PipelineRunStatus.WAITING_HUMAN.value, (
        f"{run_id} reports {status!r} after resolving {_APPROVE}; the precondition is a "
        "run still PARKED, which this spine gives because `fulfill` is gated too"
    )
    links = await _links_for(session, run_id=run_id)
    assert links, (
        f"resolving {run_id}'s gate wrote no link row — the on_resolved hook is not "
        "armed, and every survival/deletion assertion below would be vacuous"
    )
    return run_id, links


async def _assert_the_reset_did_its_own_job(session: AsyncSession) -> None:
    """Otherwise "the visitor's rows are untouched" is trivially true of a no-op."""
    for run_id in DEMO_RUN_IDS:
        assert await load_run(session, run_id) is None, f"{run_id} outlived the reset"
    for case_id in DEMO_CASE_IDS:
        assert await session.get(RepairCase, case_id) is None, f"{case_id} outlived the reset"


# --------------------------------------------------------------------------- #
# The structural fact AC-7(i)'s wording missed — asserted so it cannot regress
# --------------------------------------------------------------------------- #
async def test_a_visitor_fired_runs_gate_also_decides_the_seeded_demo_case(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None
) -> None:
    """Fleet's ``intake`` is a fleet-wide scan, so a visitor's run is never only theirs.

    This is the premise the survival bound rests on, so it is measured rather than
    assumed: if a future intake narrowed to the accepted case, the demo-scoped link row
    would stop being written and the deletion asserted in the next test would go vacuous
    — silently. This test reddens first in that case, naming the reason.
    """
    await _boot(db_session)
    case_id, quotes = await _open_case_with_quotes(client_with_db)
    _, links = await _park_with_link_rows(
        client_with_db, db_session, case_id=case_id, quote_id=quotes[1]
    )

    keyed_on = {link.case_id for link in links}
    assert case_id in keyed_on, (
        f"the visitor's own case {case_id} is not among {sorted(keyed_on)} — the run "
        "gated on a stale projection and decided somebody else's trucks"
    )
    assert DEMO_CASE_ID in keyed_on, (
        f"the seeded demo case is NOT among {sorted(keyed_on)}. If intake stopped "
        "sweeping fleet-wide this is good news, but AC-7(i)'s bound and the deletion "
        "test below both need rewriting — do not simply delete this assertion."
    )
    assert len(keyed_on) > 1, "a fleet-wide scan must decide more than the accepted case"


# --------------------------------------------------------------------------- #
# AC-7(i) — the measured survival bound, both directions
# --------------------------------------------------------------------------- #
async def test_the_reset_keeps_the_visitor_run_and_drops_only_its_demo_scoped_links(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None, tmp_path: Path
) -> None:
    """Run and step results survive whole; non-demo links survive; demo links go."""
    await _boot(db_session)
    case_id, quotes = await _open_case_with_quotes(client_with_db)
    run_id, links = await _park_with_link_rows(
        client_with_db, db_session, case_id=case_id, quote_id=quotes[1]
    )

    demo_before, other_before = _partition(links)
    # Both halves are positive controls for the two opposite assertions below: an
    # absence claim over an empty set and a survival claim over an empty set are each
    # satisfied by nothing at all.
    assert demo_before, (
        "no demo-scoped link row exists before the reset, so the deletion asserted "
        "below would be vacuous"
    )
    assert other_before, (
        "no non-demo link row exists before the reset, so the survival asserted below "
        "would be vacuous"
    )

    run_row = await db_session.get(PipelineRun, run_id)
    assert run_row is not None
    loaded_before = await load_run(db_session, run_id)
    assert loaded_before is not None
    steps_before = sorted(s.step_id for s in loaded_before.step_results)

    # Positive control for the field-for-field comparison itself: an unchanged-row
    # assertion is a NEGATIVE, and a comparison that cannot detect a difference passes
    # forever. It runs BEFORE the baseline snapshot is taken, deliberately:
    # ``pipeline_runs`` carries an optimistic-lock ``version`` that every commit bumps,
    # so the control's own mutate-and-restore moves it by two. Snapshotting first and
    # comparing after would fail on ``version`` alone and say nothing about the reset —
    # measured here, 5 -> 7, with all eleven other columns identical.
    control_probe = _row_snapshot(run_row)
    run_row.agent_id = "mutated-for-the-control"
    await db_session.commit()
    assert _row_snapshot(run_row) != control_probe, (
        "the row comparison cannot detect a change — every 'survived untouched' "
        "assertion below would be vacuous"
    )
    run_row.agent_id = control_probe["agent_id"]
    await db_session.commit()

    # The baseline is taken here, with the control's own writes already accounted for.
    db_session.expire_all()
    run_row = await db_session.get(PipelineRun, run_id)
    assert run_row is not None
    run_before = _row_snapshot(run_row)
    assert (
        run_before["agent_id"] == control_probe["agent_id"]
    ), "the control did not restore the field it mutated"

    await reset_demo_runs(db_session, photo_root=tmp_path, execute=True)
    db_session.expire_all()

    after_run = await db_session.get(PipelineRun, run_id)
    assert after_run is not None, "the reset deleted a visitor-FIRED governed run"
    assert _row_snapshot(after_run) == run_before

    loaded_after = await load_run(db_session, run_id)
    assert loaded_after is not None
    assert (
        sorted(s.step_id for s in loaded_after.step_results) == steps_before
    ), "the visitor's step results did not survive the reset"

    demo_after, other_after = _partition(await _links_for(db_session, run_id=run_id))
    assert other_after == other_before, (
        f"link rows keyed on non-demo cases must be out of the reset's reach: "
        f"{other_before} -> {other_after}"
    )
    assert demo_after == [], (
        f"link rows keyed on a demo case must NOT outlive the reset — after the re-seed "
        f"they would point at a different case reusing the id; survivors: {demo_after}"
    )

    await _assert_the_reset_did_its_own_job(db_session)

    await _boot(db_session)
    assert (
        await read_demo_state(db_session) == STATE_PRISTINE
    ), "after the reset and one re-boot the demo must read PRISTINE again (G-11)"


# --------------------------------------------------------------------------- #
# The same bound where the visitor accepted ON the demo case — session 245's live path
# --------------------------------------------------------------------------- #
async def test_a_run_fired_from_the_demo_case_itself_still_survives_the_reset(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None, tmp_path: Path
) -> None:
    """The path session 245 walked on the published system.

    Here the visitor's own case IS a demo case, so the reset reaches EVERY link row this
    run wrote about it. The run and its step results still survive: run-id scoping is
    what keeps a visitor's work out of reach, and it is unaffected by which case they
    decided.
    """
    await _boot(db_session)
    assert (
        await db_session.get(RepairCase, DEMO_CASE_ID) is not None
    ), "the demo case must be seeded before a visitor can quote it"

    quote_id = await _quote(client_with_db, DEMO_CASE_ID, "อู่ริมทางปากช่อง", "62000.00")
    run_id, links = await _park_with_link_rows(
        client_with_db, db_session, case_id=DEMO_CASE_ID, quote_id=quote_id
    )
    demo_before, _ = _partition(links)
    assert demo_before, "positive control: the run must have written a demo-scoped link row"

    run_row = await db_session.get(PipelineRun, run_id)
    assert run_row is not None
    run_before = _row_snapshot(run_row)

    await reset_demo_runs(db_session, photo_root=tmp_path, execute=True)
    db_session.expire_all()

    after_run = await db_session.get(PipelineRun, run_id)
    assert (
        after_run is not None
    ), "the reset deleted a visitor-fired run merely because it decided a demo case"
    assert _row_snapshot(after_run) == run_before

    demo_after, _ = _partition(await _links_for(db_session, run_id=run_id))
    assert demo_after == [], f"demo-scoped link rows outlived the reset: {demo_after}"

    await _assert_the_reset_did_its_own_job(db_session)
    await _boot(db_session)
    assert await read_demo_state(db_session) == STATE_PRISTINE, (
        "a visitor's run parked against the demo case must not stop the demo returning "
        "to PRISTINE after a reset and one re-boot (G-11)"
    )


# --------------------------------------------------------------------------- #
# Surviving as ROWS is weaker than surviving as WORK
# --------------------------------------------------------------------------- #
async def test_a_visitor_run_is_still_waiting_human_and_finishable_after_the_reset(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None, tmp_path: Path
) -> None:
    """A run that survives every row assertion and can no longer be finished has still
    lost the visitor's outstanding decision. Read back through the surface Tab H uses."""
    await _boot(db_session)
    case_id, quotes = await _open_case_with_quotes(client_with_db)
    run_id, _ = await _park_with_link_rows(
        client_with_db, db_session, case_id=case_id, quote_id=quotes[1]
    )

    await reset_demo_runs(db_session, photo_root=tmp_path, execute=True)
    db_session.expire_all()
    await _boot(db_session)

    listed = await client_with_db.get("/runs", headers=_HEADERS)
    assert listed.status_code == 200, listed.text
    painted = {r["run_id"]: r for r in listed.json()["runs"]}
    assert run_id in painted, "the visitor's run vanished from the surface Tab H reads"
    assert painted[run_id]["status"] == PipelineRunStatus.WAITING_HUMAN.value

    loaded = await load_run(db_session, run_id)
    assert loaded is not None
    waiting = [s for s in loaded.step_results if s.status == StepResultStatus.WAITING_HUMAN.value]
    assert len(waiting) == 1 and waiting[0].step_id == _FULFILL, (
        f"the visitor's outstanding decision is gone: waiting steps are "
        f"{[s.step_id for s in waiting]}, expected exactly ['{_FULFILL}']"
    )
