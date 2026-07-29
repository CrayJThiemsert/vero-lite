"""Fleet pilot SCENARIO tests — does the thing actually do its job? (PLAN-0096)

Cray, session 187: a passing unit test proves the SEAM works. It does not prove the
system does what it was built to do. These cases exist to close that gap, and they are
deliberately written as *situations a person would recognise* rather than as assertions
about functions.

The situation here is the one Step 9 was built for:

    เมย์ exports the odometer file on Monday. Truck 80-1234 has quietly run past
    its service interval since the last export. Does the PM sweep actually start
    flagging it — and does it stay silent until she agrees the number is right?

Every earlier Step 9 test stopped at the adapter: "the confirmed value appears in the
Truck records". That is one layer short of the claim the PLAN makes ("this step is what
makes the calm path real"), because nothing had ever run the calm path afterwards. If
the projection and the judge disagreed about a field name, a unit, or a comparison
direction, every existing test would still have been green and the sweep would have
silently kept ignoring the truck.

So this drives the REAL chain end to end: CSV upload -> proposal -> human confirm ->
projection -> adapter -> the production `pm_service_round` procedure -> the judge's
per-truck verdict.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import AsyncClient

from services.engine.discovery import discover_and_register
from services.engine.procedures.orchestrator import run_procedure
from services.engine.procedures.runs import PipelineRunStatus
from services.engine.procedures.spec import load_procedures
from services.engine.registry import registry
from verticals.fleet_maintenance import pm_projection
from verticals.fleet_maintenance.procedures_factory import (
    register_fleet_maintenance_procedure_executors,
)

_VERTICAL = "fleet_maintenance"
_CALM_PATH = "pm_service_round"
_PLATE_01 = "80-1234 กรุงเทพมหานคร"

#: truck-01's shipped state: 412,580 km against a 500,000 km due point — comfortably
#: NOT due, and the hero's breakdown truck, so it is the one truck whose PM status
#: nothing else in the fixture set is already changing.
_DUE_POINT_01 = 500_000.0
#: A reading past that due point. Realistic rather than dramatic: ~92,000 km of running
#: between exports is a few months for a truck on the แหลมฉบัง/อีสาน runs.
_READING_PAST_DUE = 505_120.0


@pytest.fixture(autouse=True)
async def _fleet_ready(client_with_db: AsyncClient) -> AsyncIterator[None]:
    """Register the fleet vertical FULLY, and keep the PM view clean between cases.

    Two ordering details that a shorter fixture gets wrong, both learned by watching it
    fail:

    * it registers through ``discover_and_register`` rather than calling the adapter
      registrar directly, because the calm path's gated action needs the vertical's
      **handlers** too — an adapter-only registration runs the read and the judge fine
      and then fails the action step, which reads as "the procedure is broken";
    * it declares ``client_with_db`` as a dependency purely for ORDERING. That fixture
      registers energy directly (not via discovery, so not idempotently), and an
      autouse fixture running before it would register energy first and make it raise.
    """
    discover_and_register()
    await register_fleet_maintenance_procedure_executors()
    pm_projection.reset()
    yield
    pm_projection.reset()


async def _run_calm_path(run_id: str) -> dict[str, str]:
    """Run the PRODUCTION ``pm_service_round`` once; return {truck_id: verdict}."""
    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == _CALM_PATH)
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    executors = registry.get_procedure_executors(_VERTICAL)()

    result = await run_procedure(proc, agent, executors, vertical=_VERTICAL, run_id=run_id)
    assert result.run.status == PipelineRunStatus.WAITING_HUMAN.value
    judge = next(sr for sr in result.step_results if sr.step_id == "judge_service_due")
    assert judge.artifact is not None
    return {row["truck_id"]: row["verdict"] for row in judge.artifact["output_set"]}


async def _proposals_at_the_gate(run_id: str) -> int:
    """How many trucks the calm path actually proposes booking a service for."""
    spec = load_procedures(_VERTICAL)
    proc = next(p for p in spec.procedures if p.procedure_id == _CALM_PATH)
    agent = next(a for a in spec.agents if a.agent_id == proc.run_by)
    executors = registry.get_procedure_executors(_VERTICAL)()

    result = await run_procedure(proc, agent, executors, vertical=_VERTICAL, run_id=run_id)
    gate = next(sr for sr in result.step_results if sr.step_id == "schedule_service")
    assert gate.artifact is not None
    return len(gate.artifact["output_set"])


async def _upload(client: AsyncClient, csv_text: str) -> dict[str, Any]:
    response = await client.post(
        "/api/pm/imports",
        files={"file": ("wialon-export.csv", csv_text.encode("utf-8"), "text/csv")},
    )
    assert response.status_code == 201, response.text
    return response.json()


# --------------------------------------------------------------------------- #


async def test_a_confirmed_odometer_makes_the_pm_sweep_flag_a_truck_it_was_ignoring(
    client_with_db: AsyncClient,
) -> None:
    """THE scenario Step 9 exists for, run end to end on the production procedure.

    Three measurements in one story, and the middle one is the governance:

    1. **Before.** The sweep reads truck-01 at 412,580 km and calls it ``ok`` — one
       truck due in the whole fleet.
    2. **After the import, before the confirm.** เมย์ has uploaded Monday's export
       showing 505,120 km. The sweep STILL calls truck-01 ``ok``. Nothing a machine
       said has changed what the fleet looks like.
    3. **After she confirms.** The sweep now calls truck-01 ``breach`` and proposes
       booking it in — two trucks due.

    Step (3) is what no previous test covered: the confirmed number does not merely
    appear in a record, it changes a per-truck governance verdict computed by the real
    judge against the real band. A field-name or unit mismatch between the projection
    and the judge would leave (1) and (2) passing and silently break (3) — the truck
    would run past its interval and nothing would say so.
    """
    before = await _run_calm_path("scenario-pm-before")
    assert before["truck-01"] == "ok"
    assert sum(1 for v in before.values() if v == "breach") == 1, "only truck-02 is due"

    batch = await _upload(
        client_with_db, f"plate,odometer_km\n{_PLATE_01},{_READING_PAST_DUE:.0f}\n"
    )
    row = batch["rows"][0]
    assert row["status"] == "proposed"

    during = await _run_calm_path("scenario-pm-proposed")
    assert during["truck-01"] == "ok", (
        "an unconfirmed machine reading must not change a governance verdict — this is "
        "Q4's whole point, and it is the assertion an integration would quietly break"
    )

    decided = await client_with_db.post(
        f"/api/pm/imports/{batch['batch_id']}/decisions",
        json={"decisions": [{"import_row_id": row["import_row_id"], "confirm": True}]},
    )
    assert decided.status_code == 200, decided.text

    after = await _run_calm_path("scenario-pm-after")
    assert after["truck-01"] == "breach", (
        "the confirmed reading is past the truck's due point, so the real judge must "
        "flag it — anything less means Step 9 built a screen, not a behaviour"
    )
    assert after["truck-02"] == "breach", "the truck that was already due stays due"
    assert after["truck-03"] == "ok", "a truck nobody imported anything for is untouched"
    assert (
        await _proposals_at_the_gate("scenario-pm-gate") == 2
    ), "the human gate now offers TWO services to book, not one"


async def test_a_declined_reading_leaves_the_sweep_exactly_where_it_was(
    client_with_db: AsyncClient,
) -> None:
    """The other half of the same story: เมย์ looks at 505,120 and knows it is wrong
    (the GPS drifted, or that is a different truck's figure), so she declines it.

    The sweep must be byte-identical to a fleet where the file was never uploaded.
    A decline that still moved the number would be worse than no import at all — she
    would have been asked to review something her review could not stop."""
    baseline = await _run_calm_path("scenario-decline-before")

    batch = await _upload(
        client_with_db, f"plate,odometer_km\n{_PLATE_01},{_READING_PAST_DUE:.0f}\n"
    )
    await client_with_db.post(
        f"/api/pm/imports/{batch['batch_id']}/decisions",
        json={
            "decisions": [{"import_row_id": batch["rows"][0]["import_row_id"], "confirm": False}]
        },
    )

    after = await _run_calm_path("scenario-decline-after")

    assert after == baseline


async def test_a_corrected_reading_moves_the_verdict_back(
    client_with_db: AsyncClient,
) -> None:
    """The correction path, which is the reason latest-confirmed-wins exists.

    เมย์ confirms 505,120 on Monday, then discovers on Tuesday it belonged to another
    truck and the real figure is 430,000. She confirms the correction. The sweep must
    stop flagging truck-01.

    A 'highest reading wins' rule — tempting, since an odometer only goes up — would
    pass every unit test and make this impossible: the wrong number would be pinned
    forever and her correction would silently do nothing."""
    first = await _upload(
        client_with_db, f"plate,odometer_km\n{_PLATE_01},{_READING_PAST_DUE:.0f}\n"
    )
    await client_with_db.post(
        f"/api/pm/imports/{first['batch_id']}/decisions",
        json={"decisions": [{"import_row_id": first["rows"][0]["import_row_id"], "confirm": True}]},
    )
    assert (await _run_calm_path("scenario-fix-wrong"))["truck-01"] == "breach"

    corrected = await _upload(client_with_db, f"plate,odometer_km\n{_PLATE_01},430000\n")
    await client_with_db.post(
        f"/api/pm/imports/{corrected['batch_id']}/decisions",
        json={
            "decisions": [{"import_row_id": corrected["rows"][0]["import_row_id"], "confirm": True}]
        },
    )

    after = await _run_calm_path("scenario-fix-right")

    assert after["truck-01"] == "ok", "the correction must actually take effect"
    assert 430_000.0 < _DUE_POINT_01, "sanity: the corrected reading really is below the band"


async def test_the_onboarding_load_gives_a_truck_a_due_point_it_can_be_judged_against(
    client_with_db: AsyncClient,
) -> None:
    """The other half of Step 9: the paper PM folder, and the number it produces.

    เมย์ reads truck-01's last interval service off the folder — 300,000 km — and types
    it in. The import computes the due point at load: 300,000 + the 100,000 km interval
    = 400,000. The truck's odometer is 412,580, so once she confirms, the sweep must
    flag it.

    The figures are chosen so the verdict DISCRIMINATES. Against the shipped fixture due
    point of 500,000 the truck reads ``ok``; against the loaded 400,000 it reads
    ``breach``. Nothing about the odometer moved — only which due point the judge is
    comparing against — so a pass here can only mean the loaded number is the one in
    force.

    _(An earlier draft used 350,000 -> 450,000 and asserted ``breach``. 412,580 is
    BELOW 450,000, so the code was right and the test was wrong. Running the real
    procedure is what said so — which is the entire argument for this file existing.)_
    """
    batch = await _upload(client_with_db, f"plate,last_service_odometer_km\n{_PLATE_01},300000\n")
    row = batch["rows"][0]
    assert row["next_service_due_km"] == 400_000.0, "computed at load, absolute"

    before = await _run_calm_path("scenario-onboard-before")
    assert before["truck-01"] == "ok", "against the shipped 500,000 due point"

    await client_with_db.post(
        f"/api/pm/imports/{batch['batch_id']}/decisions",
        json={"decisions": [{"import_row_id": row["import_row_id"], "confirm": True}]},
    )

    after = await _run_calm_path("scenario-onboard-after")

    assert after["truck-01"] == "breach", (
        "412,580 km is past the 400,000 km due point loaded from the paper folder — the "
        "judge must use the loaded number, not the fixture's 500,000"
    )
