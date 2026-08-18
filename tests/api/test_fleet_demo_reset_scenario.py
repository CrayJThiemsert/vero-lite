"""The fleet demo's whole lifecycle — seed, consume, reset, re-seed (PLAN-0110 Step 5).

The mandatory scenario test (CLAUDE.md §8). It drives the **real producer into the real
consumer on realistic data**, with no mocked seam on either side:

* the producer is ``services.api.main._seed_fleet_operate_demo`` — the ACTUAL boot
  block, not a replica of it. Its ordering, its ``load_run`` skip and its fail-soft
  wrapper are the ones that ship. A replica would agree with whatever this test's
  author believed the boot did, which is the one thing that must not be assumed here:
  the skip at ``main.py:307`` IS the defect under repair;
* the consumer is the real HTTP surface — persona-authenticated
  ``POST /runs/{id}/gate/resolve`` and ``POST /runs/{id}/cancel``, the two routes the
  published system's ingress allowlist actually exposes — read back through
  ``GET /runs``, which is what Tab H and Tab A read;
* the reset is the same entry point the deploy step invokes, in both its modes.

🔴 **Why all THREE consumed shapes are driven, and why two of them are not obvious.**
``governed_repair_approval`` is a ``request -> approve -> fulfill`` spine whose
TERMINAL step is itself ``autonomy: gated``. So resolving ``approve`` does not finish
the run — it parks it again at ``fulfill``, **still ``waiting_human``**. A test that
checked only ``run.status`` would see ``waiting_human`` before and after and conclude
nothing had happened, while the beat was in fact spent. That is not hypothetical: it
is the exact shape of the live defect PR #1209 fixed, and it is why
:func:`services.db.demo_run_reset.read_demo_state` asserts the SUSPENDED STEP and not
just the status. The three shapes are approve-then-fulfill (completed), approve-only
(parked at ``fulfill``), and cancel (cancelled).

**Measured side-effects, recorded rather than hidden.** Each rebuild consumes one
``allocate_repair_order_no`` allocation, so the report's RO number advances by one per
reset (gap-free by construction — ``operate_seed.py:571-577``), and each rebuild
appends one seed-round of audit rows. Honest allocation and honest audit; worth one
line in the demo narration, never suppressed.

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
from services.db.audit_log import AuditLog, verify_chain
from services.db.demo_run_reset import (
    DEMO_CASE_IDS,
    DEMO_RUN_IDS,
    STATE_CONSUMED,
    STATE_PRISTINE,
    VERDICT_PREFIX,
    read_demo_state,
    reset_demo_runs,
)
from services.db.repair_case import RepairCase
from services.engine import demo_events
from services.engine.procedures import gate_hooks
from services.engine.procedures.persistence import load_run
from services.engine.procedures.runs import PipelineRun, PipelineRunStatus, StepResultStatus
from services.engine.registry import registry
from verticals.fleet_maintenance import case_projection
from verticals.fleet_maintenance.operate_seed import (
    DEMO_HISTORY_RUN_ID,
    DEMO_RUN_ID,
)
from verticals.fleet_maintenance.run_link import case_id_of

_VERTICAL = "fleet_maintenance"
_APPROVE = "approve"
_FULFILL = "fulfill"

_MECHANIC = "req-mechanic-tom"
_OWNER = "appr-owner"
_MECHANIC_KEY = "test-key-req-mechanic-tom"
_OWNER_KEY = "test-key-appr-owner"
_HEADERS = {"Authorization": f"Bearer {_MECHANIC_KEY}"}
_OWNER_HEADERS = {"Authorization": f"Bearer {_OWNER_KEY}"}

#: A run id that is NOT one of the demo's. AC-5's decoy: the reset must be unable to
#: reach it, and "unable" has to be demonstrated rather than declared.
_DECOY_RUN_ID = "run-not-a-demo-run"
#: A case a visitor opened. Same protection, different table.
_DECOY_CASE_ID = "case-visitor-typed-this"


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
    """Register EXACTLY what the API lifespan registers, with authn ON, and point the
    boot seeder's session factory at the DISPOSABLE test database.

    That last part is the load-bearing one. ``_seed_fleet_operate_demo`` opens its own
    session from ``main.async_session``, which is bound to the DEV database at import
    time. Without this patch the boot block would seed the developer's demo DB while
    every assertion below read an empty test DB — a green suite proving nothing, on a
    polluted dev environment.
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
    """One boot of the REAL seed block, then re-read the caches it populated.

    ``_seed_fleet_operate_demo`` is fail-soft by design — a seed error logs and returns
    — so every caller here follows it with an assertion on the resulting STATE. A boot
    that silently seeded nothing must not read as a boot that worked.
    """
    await api_main._seed_fleet_operate_demo(_VERTICAL)
    await case_projection.refresh(session)


async def _runs(client: AsyncClient) -> dict[str, dict[str, Any]]:
    """``GET /runs``, the real route, keyed by run id.

    Never the response of the call that created a run: an endpoint returning the object
    it just wrote proves only that the endpoint returned it. Tab A and Tab H both read
    THIS payload, so this is where a ``subject`` claim has to be true.
    """
    response = await client.get("/runs", headers=_HEADERS)
    assert response.status_code == 200, response.text
    return {r["run_id"]: r for r in response.json()["runs"]}


async def _expected_truck(session: AsyncSession, run_id: str) -> str:
    """The truck, recomputed from the run's OWN approve-step proposal -> case row.

    Deliberately NOT read from ``operate_seed``'s ``truck-02`` constant. A test that
    asserted the constant would agree with the seed by construction and would pass
    just as happily against a hardcoded stamp — which is the single thing the
    derivation must not be.
    """
    loaded = await load_run(session, run_id)
    assert loaded is not None, f"{run_id} is not persisted"
    approve = next((s for s in loaded.step_results if s.step_id == _APPROVE), None)
    assert approve is not None, f"{run_id} has no {_APPROVE} step"

    trucks: set[str] = set()
    for proposal in (approve.artifact or {}).get("output_set") or []:
        case_id = case_id_of(proposal)
        if case_id is None:
            continue
        case = await session.get(RepairCase, case_id)
        if case is not None:
            trucks.add(case.truck_id)
    assert len(trucks) == 1, (
        f"{run_id}: exactly one proposal must resolve to a real repair case — got "
        f"{sorted(trucks)}. The other proposals name fixture-only case ids, which is "
        "what makes the case-table lookup the discriminator rather than a formality."
    )
    return trucks.pop()


async def _proposals_at(session: AsyncSession, run_id: str, step_id: str) -> dict[str, str]:
    """``{action_id: 'approve'}`` for every proposal parked at ``step_id``.

    EVERY proposal gets a verdict: the gate refuses a partial resolution, because
    silence about a proposed spend is what an audit trail must not contain.
    """
    loaded = await load_run(session, run_id)
    assert loaded is not None
    step = next((s for s in loaded.step_results if s.step_id == step_id), None)
    assert step is not None, f"{run_id} has no {step_id} step"
    return {
        str(p["action_id"]): "approve"
        for p in ((step.artifact or {}).get("output_set") or [])
        if "action_id" in p
    }


async def _resolve(client: AsyncClient, session: AsyncSession, run_id: str, step_id: str) -> str:
    """Resolve one gate through the REAL endpoint. Returns the resulting run status."""
    response = await client.post(
        f"/runs/{run_id}/gate/resolve",
        json={"step_id": step_id, "decisions": await _proposals_at(session, run_id, step_id)},
        headers=_OWNER_HEADERS,
    )
    assert response.status_code == 200, response.text
    status: str = response.json()["run_status"]
    return status


async def _consume(client: AsyncClient, session: AsyncSession, shape: str) -> None:
    """Play the beat to one of G5's three consumed shapes, all through real routes."""
    if shape == "cancelled":
        response = await client.post(f"/runs/{DEMO_RUN_ID}/cancel", headers=_OWNER_HEADERS)
        assert response.status_code == 200, response.text
        return
    await _resolve(client, session, DEMO_RUN_ID, _APPROVE)
    if shape == "parked_at_fulfill":
        return
    await _resolve(client, session, DEMO_RUN_ID, _FULFILL)


def _row_snapshot(row: Any) -> dict[str, Any]:
    """Every mapped column of one ORM row, for a field-by-field re-read comparison."""
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


async def _seed_decoys(session: AsyncSession) -> None:
    """One non-demo run and one visitor-opened case — the rows the reset must not reach."""
    now = (await session.execute(sa.select(sa.func.now()))).scalar_one()
    session.add(
        PipelineRun(
            run_id=_DECOY_RUN_ID,
            procedure_id="governed_repair_approval",
            agent_id="fleet-ops-agent",
            trigger_context={"source": "not-the-demo"},
            status=PipelineRunStatus.WAITING_HUMAN.value,
            started_at=now,
            updated_at=now,
        )
    )
    session.add(
        RepairCase(
            case_id=_DECOY_CASE_ID,
            truck_id="truck-04",
            opened_by=_MECHANIC,
            opened_at=now,
            description="ไฟเลี้ยวหลังซ้ายไม่ติด",
            status="open",
            work_type="breakdown",
            photos=[],
        )
    )
    await session.commit()


# --------------------------------------------------------------------------- #
# AC-1 — subject lands through the real seed -> /runs path
# --------------------------------------------------------------------------- #
async def test_the_seeded_runs_carry_the_subject_tab_a_keys_its_marker_on(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None, tmp_path: Path
) -> None:
    """Both demo runs project a ``subject`` through the real ``GET /runs`` response model.

    Measured live on 2026-08-18, BEFORE this PLAN: both fleet runs returned
    ``subject: null``, so ``view-map.js``'s double gate skipped them and Tab A rendered
    zero governed-run markers however the demo was narrated.

    The positive control is the second half and it is not decoration: a subject naming
    a truck the adapter does not serve would satisfy every shape assertion while
    leaving the map with **no node to attach the marker to** — a green that means the
    opposite of what it says.
    """
    await _boot(db_session)

    runs = await _runs(client_with_db)
    assert set(DEMO_RUN_IDS) <= set(runs), f"the boot seed produced {sorted(runs)}"

    adapter_pks = {
        obj["truck_id"] for obj in await registry.get_adapter(_VERTICAL).fetch_objects("Truck")
    }
    assert adapter_pks, "the adapter served no Trucks — the positive control is blind"

    for run_id in DEMO_RUN_IDS:
        expected = await _expected_truck(db_session, run_id)
        assert runs[run_id]["subject"] == {
            "object_type": "Truck",
            "primary_key": expected,
        }, f"{run_id} carries no usable subject: {runs[run_id]['subject']!r}"
        assert expected in adapter_pks, (
            f"{run_id}'s subject names {expected!r}, which the adapter does not serve — "
            "Tab A would have no node to hang the marker on"
        )


# --------------------------------------------------------------------------- #
# AC-4 / AC-11 — the reset restores the pristine pair, from every consumed shape
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("shape", ["completed", "parked_at_fulfill", "cancelled"])
async def test_the_reset_restores_the_pristine_pair_after_every_consumed_shape(
    client_with_db: AsyncClient,
    db_session: AsyncSession,
    fleet_active: None,
    tmp_path: Path,
    shape: str,
) -> None:
    """seed -> consume -> reset -> re-seed, with the token witnessed flipping both ways.

    ``parked_at_fulfill`` is the shape worth reading twice. After it the run is STILL
    ``waiting_human`` and still 2-of-2 in the Monitor's count — a status check alone
    calls that pristine. It is not: the ``approve`` gate is decided and the visitor's
    beat is gone.
    """
    await _boot(db_session)
    assert await read_demo_state(db_session) == STATE_PRISTINE, (
        "a fresh boot must produce the pristine pair — everything below measures a "
        "DELTA from it, so a wrong baseline would make the rest meaningless"
    )

    await _consume(client_with_db, db_session, shape)
    assert await read_demo_state(db_session) == STATE_CONSUMED, (
        f"the {shape!r} shape must be detectable as consumed — this is the assertion "
        "the live defect defeated, because it counted CASES where the screen counts RUNS"
    )

    report = await reset_demo_runs(db_session, photo_root=tmp_path, execute=True)
    assert report.executed and report.refused is None, report
    assert report.verdict_line == f"{VERDICT_PREFIX} {STATE_CONSUMED}"
    assert report.deleted["pipeline_runs"] == len(DEMO_RUN_IDS)

    await _boot(db_session)

    assert await read_demo_state(db_session) == STATE_PRISTINE
    runs = await _runs(client_with_db)
    demo = {rid: r for rid, r in runs.items() if rid in set(DEMO_RUN_IDS)}
    assert len(demo) == 2, f"exactly two demo runs must stand, got {sorted(demo)}"

    # Status is necessary and NOT sufficient — assert the suspended STEP as well.
    live = await load_run(db_session, DEMO_RUN_ID)
    assert live is not None
    assert live.run.status == PipelineRunStatus.WAITING_HUMAN.value
    waiting = [s for s in live.step_results if s.status == StepResultStatus.WAITING_HUMAN.value]
    assert [s.step_id for s in waiting] == [_APPROVE], (
        "the rebuilt live run must park at the APPROVE gate with its proposals still "
        f"undecided — parked at {[s.step_id for s in waiting]} instead"
    )
    assert (waiting[0].artifact or {}).get("output_set"), "the rebuilt gate proposes nothing"

    assert demo[DEMO_HISTORY_RUN_ID]["status"] == PipelineRunStatus.COMPLETED.value
    for run_id in DEMO_RUN_IDS:
        assert runs[run_id]["subject"] == {
            "object_type": "Truck",
            "primary_key": await _expected_truck(db_session, run_id),
        }


# --------------------------------------------------------------------------- #
# AC-5 — the reset is scoped to the fixed demo ids
# --------------------------------------------------------------------------- #
async def test_the_reset_cannot_reach_a_non_demo_run_or_a_visitor_case(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None, tmp_path: Path
) -> None:
    """A decoy run and a visitor case survive the reset field-for-field.

    The positive control matters more than the claim: an unchanged-row assertion is a
    NEGATIVE, and a comparison that can never detect a difference passes forever. So
    the same comparison is first shown detecting a deliberate mutation.
    """
    await _boot(db_session)
    await _seed_decoys(db_session)

    decoy_run = await db_session.get(PipelineRun, _DECOY_RUN_ID)
    decoy_case = await db_session.get(RepairCase, _DECOY_CASE_ID)
    assert decoy_run is not None and decoy_case is not None
    run_before, case_before = _row_snapshot(decoy_run), _row_snapshot(decoy_case)

    # Positive control FIRST: prove the reader can see a change at all.
    decoy_case.description = "mutated for the control"
    await db_session.commit()
    assert _row_snapshot(decoy_case) != case_before, (
        "the row comparison cannot detect a change — every 'survived untouched' "
        "assertion below would be vacuous"
    )
    decoy_case.description = case_before["description"]
    await db_session.commit()

    await reset_demo_runs(db_session, photo_root=tmp_path, execute=True)

    db_session.expire_all()
    after_run = await db_session.get(PipelineRun, _DECOY_RUN_ID)
    after_case = await db_session.get(RepairCase, _DECOY_CASE_ID)
    assert after_run is not None, "the reset deleted a run that is not one of the demo's"
    assert after_case is not None, "the reset deleted a visitor's case"
    assert _row_snapshot(after_run) == run_before
    assert _row_snapshot(after_case) == case_before

    # ...and it did do its own job, or "nothing changed" is trivially true.
    for run_id in DEMO_RUN_IDS:
        assert await load_run(db_session, run_id) is None
    for case_id in DEMO_CASE_IDS:
        assert await db_session.get(RepairCase, case_id) is None


# --------------------------------------------------------------------------- #
# AC-7 — the audit chain survives, and the checker is proven able to redden
# --------------------------------------------------------------------------- #
async def test_the_audit_chain_survives_the_reset_and_the_checker_can_still_redden(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None, tmp_path: Path
) -> None:
    """*The demo resets; the audit log remembers.*

    ``audit_log.run_id`` carries no ForeignKey and ``verify_chain`` walks only audit
    rows by ``audit_id``, so deleting a run leaves both the chain and the record of
    that run standing. Asserted as a MONOTONIC row count across the whole cycle —
    "equal before and after" would be satisfied by a delete plus an equal number of
    new rows.
    """

    async def _rows() -> int:
        return int(
            (
                await db_session.execute(sa.select(sa.func.count()).select_from(AuditLog))
            ).scalar_one()
        )

    await _boot(db_session)
    after_seed = await _rows()
    assert after_seed > 0, "the seed wrote no audit rows — the guard below is blind"
    assert await verify_chain(db_session) == []

    await _consume(client_with_db, db_session, "completed")
    after_consume = await _rows()
    assert after_consume >= after_seed

    await reset_demo_runs(db_session, photo_root=tmp_path, execute=True)
    after_reset = await _rows()
    assert after_reset >= after_consume, (
        f"the reset removed audit rows ({after_consume} -> {after_reset}) — the chain "
        "must outlive every demo generation"
    )
    assert await verify_chain(db_session) == []

    await _boot(db_session)
    assert await _rows() >= after_reset
    assert await verify_chain(db_session) == []

    # Positive control, LAST because it is destructive: an in-place mutation of one
    # audit row must make verify_chain report a break. Without this, "no breaks" would
    # also be the answer a checker that had silently stopped walking would give.
    victim = (
        await db_session.execute(sa.select(AuditLog).order_by(AuditLog.audit_id).limit(1))
    ).scalar_one()
    victim.action = f"{victim.action}-tampered"
    await db_session.commit()
    assert await verify_chain(db_session) != [], (
        "verify_chain reported an intact chain over a row that was just mutated — "
        "every 'chain intact' assertion above is vacuous"
    )


# --------------------------------------------------------------------------- #
# AC-8 — the reset fails closed
# --------------------------------------------------------------------------- #
async def test_plan_mode_deletes_nothing_and_execute_is_the_control(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None, tmp_path: Path
) -> None:
    """AC-8 read (1). Plan-by-default, with ``--execute`` as its own positive control:
    the "nothing happened" reading is only worth having once the same harness has been
    shown to detect "something happened"."""
    await _boot(db_session)
    await _consume(client_with_db, db_session, "completed")
    before = sorted((await _runs(client_with_db)).keys())

    planned = await reset_demo_runs(db_session, photo_root=tmp_path)
    assert planned.executed is False
    assert planned.deleted == {}
    assert planned.verdict_line == f"{VERDICT_PREFIX} {STATE_CONSUMED}"
    assert sorted((await _runs(client_with_db)).keys()) == before, "plan mode deleted rows"

    executed = await reset_demo_runs(db_session, photo_root=tmp_path, execute=True)
    assert executed.executed is True
    assert sorted((await _runs(client_with_db)).keys()) != before, (
        "--execute changed nothing either — the read above cannot tell the two modes "
        "apart, so its 'plan mode is safe' verdict means nothing"
    )


async def test_the_reset_refuses_when_the_deployment_serves_another_vertical(
    client_with_db: AsyncClient, db_session: AsyncSession, fleet_active: None, tmp_path: Path
) -> None:
    """AC-8 read (2). The fixed ids are fleet's; a hand-typed invocation on the wrong
    host is a realistic operator failure, so the guard refuses rather than deleting
    whatever happens to match."""
    await _boot(db_session)
    before = sorted((await _runs(client_with_db)).keys())

    report = await reset_demo_runs(
        db_session, photo_root=tmp_path, execute=True, vertical="procurement"
    )
    assert report.executed is False
    assert report.refused is not None and "procurement" in report.refused
    assert report.deleted == {}
    assert sorted((await _runs(client_with_db)).keys()) == before


def test_nothing_in_the_boot_path_invokes_the_reset() -> None:
    """AC-8 read (3) — SD-C's ruling, asserted against the code rather than trusted.

    Cray ruled the reset is a DEPLOY-time step, not a boot-time one, so that a
    container crash-restart can never wipe a visitor's half-played run. An import
    sneaking into the boot path would silently reverse that ruling, and the symptom
    would be a demo that mysteriously heals itself — which reads like good news.

    The positive control is required because this is an ABSENCE claim: the same reader
    is shown finding a reference that IS present, in this file.
    """
    repo_root = Path(__file__).resolve().parents[2]
    main_src = (repo_root / "services" / "api" / "main.py").read_text(encoding="utf-8")
    assert "demo_run_reset" not in main_src, (
        "services/api/main.py references the demo reset — SD-C ruled it a deploy-time "
        "step precisely so that a crash-restart cannot fire it"
    )
    assert "demo_run_reset" in Path(__file__).read_text(encoding="utf-8"), (
        "the reader found no reference in a file that certainly contains one — it is "
        "not actually reading anything"
    )
