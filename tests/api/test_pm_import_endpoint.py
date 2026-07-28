"""PLAN-0096 Step 9 / AC-10 — the measured-then-confirmed PM import, DB-backed.

The assertion this module exists for is the one AC-10 is easiest to fake:

    **an imported reading changes nothing until a human confirms it, and then it
    changes the ontology.**

Both halves matter equally, and only together. A build that stored proposals and
never applied them would satisfy "unconfirmed rows never touch the ontology"
*vacuously* — confirmed ones would not touch it either — which is the same hollow
shape as the fail-open ``three_quote`` default PLAN-0096 Step 4 retired. So every
case below reads the **live fleet adapter** after acting, because that is what the
calm path's query step actually reads: not the API's own response about itself.

Its companion ``tests/verticals/fleet_maintenance/test_pm_import.py`` covers the pure
parser and projection with no database.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import AsyncClient

from services.engine.registry import RegistryError, registry
from verticals.fleet_maintenance import pm_projection
from verticals.fleet_maintenance.data_adapter import register_fleet_maintenance_adapter

_VERTICAL = "fleet_maintenance"
_PLATE_01 = "80-1234 กรุงเทพมหานคร"
_PLATE_02 = "70-5678 กรุงเทพมหานคร"
#: truck-01's fixture odometer — the value that must NOT move on an unconfirmed import.
_BASELINE_ODOMETER_01 = 412_580.0
#: truck-01's fixture due point. Confirming an odometer past it is what turns this
#: feature from a screen into a behaviour change for the calm path.
_BASELINE_DUE_01 = 500_000.0


@pytest.fixture(autouse=True)
async def _fleet_registered() -> AsyncIterator[None]:
    """Register the fleet adapter (the router resolves plates through it) and keep the
    process-global PM view clean between cases.

    Registers ONLY fleet rather than running the full discovery sweep: this module's
    client fixture already registers energy, and a second registration of the same
    vertical is a RegistryError by design."""
    try:
        registry.get_adapter(_VERTICAL)
    except RegistryError:
        register_fleet_maintenance_adapter()
    pm_projection.reset()
    yield
    pm_projection.reset()


async def _trucks() -> dict[str, dict[str, Any]]:
    """The fleet as the QUERY STEP sees it — through the registered adapter."""
    rows = await registry.get_adapter(_VERTICAL).fetch_objects("Truck")
    return {str(row["truck_id"]): row for row in rows}


async def _upload(client: AsyncClient, csv_text: str) -> dict[str, Any]:
    response = await client.post(
        "/api/pm/imports",
        files={"file": ("wialon.csv", csv_text.encode("utf-8"), "text/csv")},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _decide(
    client: AsyncClient, batch_id: str, row_id: str, *, confirm: bool
) -> dict[str, Any]:
    response = await client.post(
        f"/api/pm/imports/{batch_id}/decisions",
        json={"decisions": [{"import_row_id": row_id, "confirm": confirm}]},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _row_for(batch: dict[str, Any], plate: str) -> dict[str, Any]:
    return next(row for row in batch["rows"] if row["plate"] == plate)


# --------------------------------------------------------------------------- #
# The gate itself
# --------------------------------------------------------------------------- #


async def test_an_imported_reading_is_invisible_until_confirmed(
    client_with_db: AsyncClient,
) -> None:
    """AC-10, the load-bearing case: import proposes, and the fleet does not move.

    Q4 is why. The partner volunteered that his telematics figures are approximate, so
    an import that wrote straight through would make every truck's service-due date
    drift on its own — and เมย์ would have no way to answer "why is this one flagged?"

    **What this case does NOT prove on its own**, recorded because a probe measured it:
    deleting the ``status == confirmed`` filter from ``confirmed_truck_values`` leaves
    this test GREEN, because a bare upload never triggers a refresh, so the view is
    empty either way. The case that isolates the filter is
    :func:`test_rows_left_undecided_stay_invisible`, where a confirm on one row forces
    a refresh while another row is still proposed. Both are needed; neither is
    redundant.
    """
    batch = await _upload(client_with_db, f"plate,odometer_km\n{_PLATE_01},505000\n")

    assert batch["proposed_count"] == 1
    assert _row_for(batch, _PLATE_01)["status"] == "proposed"
    assert _row_for(batch, _PLATE_01)["truck_id"] == "truck-01"

    trucks = await _trucks()
    assert (
        trucks["truck-01"]["odometer_km"] == _BASELINE_ODOMETER_01
    ), "a PROPOSED reading must not reach the ontology"


async def test_confirming_moves_the_truck_and_only_that_truck(
    client_with_db: AsyncClient,
) -> None:
    """AC-10, the other half: once a human agrees, the calm path sees the new number.

    505,000 km is past truck-01's 500,000 due point, so this is not a cosmetic field
    update — it is the reading that would make the PM sweep flag a truck it was not
    flagging a moment ago. That is what 'this step makes the calm path real' means."""
    batch = await _upload(client_with_db, f"plate,odometer_km\n{_PLATE_01},505000\n")
    row = _row_for(batch, _PLATE_01)

    decided = await _decide(client_with_db, batch["batch_id"], row["import_row_id"], confirm=True)

    assert _row_for(decided, _PLATE_01)["status"] == "confirmed"
    trucks = await _trucks()
    assert trucks["truck-01"]["odometer_km"] == 505_000.0
    assert (
        trucks["truck-01"]["next_service_due_km"] == _BASELINE_DUE_01
    ), "an odometer confirm must not invent a new due point"
    assert trucks["truck-01"]["odometer_km"] > trucks["truck-01"]["next_service_due_km"], (
        "the confirmed reading now puts this truck past its service interval — the "
        "behaviour change the calm path exists to surface"
    )
    assert trucks["truck-02"]["odometer_km"] == 688_140.0, "other trucks are untouched"


async def test_declining_leaves_the_fleet_alone(client_with_db: AsyncClient) -> None:
    """A decline is recorded and applied to nothing — the reading was offered and
    refused, which is itself the answer to a later 'why did this not move?'"""
    batch = await _upload(client_with_db, f"plate,odometer_km\n{_PLATE_01},505000\n")
    row = _row_for(batch, _PLATE_01)

    decided = await _decide(client_with_db, batch["batch_id"], row["import_row_id"], confirm=False)

    assert _row_for(decided, _PLATE_01)["status"] == "rejected"
    assert _row_for(decided, _PLATE_01)["reason"] == "declined"
    assert _row_for(decided, _PLATE_01)["decided_by"] == "unattributed"
    trucks = await _trucks()
    assert trucks["truck-01"]["odometer_km"] == _BASELINE_ODOMETER_01


async def test_rows_left_undecided_stay_invisible(client_with_db: AsyncClient) -> None:
    """Confirming one row of a file does not implicitly accept the rest. 'Not yet
    reviewed' has to keep meaning 'not applied', or a partial review silently becomes
    a whole one."""
    batch = await _upload(
        client_with_db,
        f"plate,odometer_km\n{_PLATE_01},505000\n{_PLATE_02},700000\n",
    )

    await _decide(
        client_with_db, batch["batch_id"], _row_for(batch, _PLATE_01)["import_row_id"], confirm=True
    )

    trucks = await _trucks()
    assert trucks["truck-01"]["odometer_km"] == 505_000.0
    assert trucks["truck-02"]["odometer_km"] == 688_140.0, "the unreviewed row applied nothing"


# --------------------------------------------------------------------------- #
# The last-service half — the arithmetic that kills the GUESS
# --------------------------------------------------------------------------- #


async def test_a_confirmed_last_service_sets_an_absolute_due_point(
    client_with_db: AsyncClient,
) -> None:
    """AC-10: the paper PM folder loads through the SAME import path, and the due
    point it produces is absolute — computed once, at load."""
    batch = await _upload(client_with_db, f"plate,last_service_odometer_km\n{_PLATE_01},450000\n")
    row = _row_for(batch, _PLATE_01)
    assert row["next_service_due_km"] == 550_000.0, "computed at load, not at read"

    await _decide(client_with_db, batch["batch_id"], row["import_row_id"], confirm=True)

    trucks = await _trucks()
    assert trucks["truck-01"]["next_service_due_km"] == 550_000.0
    assert (
        trucks["truck-01"]["odometer_km"] == _BASELINE_ODOMETER_01
    ), "a last-service sheet carries no telematics reading and must not blank one"


async def test_the_latest_confirmation_wins(client_with_db: AsyncClient) -> None:
    """A correction has to be possible. If the first confirmed reading were sticky —
    the shape a 'highest odometer wins' rule would have — then confirming the right
    number after a wrong one would silently do nothing, which is the worst available
    behaviour for a correction surface."""
    first = await _upload(client_with_db, f"plate,odometer_km\n{_PLATE_01},999000\n")
    await _decide(
        client_with_db, first["batch_id"], _row_for(first, _PLATE_01)["import_row_id"], confirm=True
    )
    assert (await _trucks())["truck-01"]["odometer_km"] == 999_000.0

    second = await _upload(client_with_db, f"plate,odometer_km\n{_PLATE_01},505000\n")
    await _decide(
        client_with_db,
        second["batch_id"],
        _row_for(second, _PLATE_01)["import_row_id"],
        confirm=True,
    )

    assert (await _trucks())["truck-01"]["odometer_km"] == 505_000.0


# --------------------------------------------------------------------------- #
# FAIL CLOSED + adversarial
# --------------------------------------------------------------------------- #


async def test_a_mangled_upload_persists_nothing(client_with_db: AsyncClient) -> None:
    """AC-10: the whole file is refused, and no partial batch is left behind for
    someone to confirm later."""
    response = await client_with_db.post(
        "/api/pm/imports",
        files={"file": ("bad.csv", b"plate,odometer_km\n80-1234,four hundred\n", "text/csv")},
    )

    assert response.status_code == 422
    assert "is not a number" in response.text
    overrides = await client_with_db.get("/api/pm/overrides")
    assert overrides.json()["overrides"] == []


async def test_an_unknown_plate_is_rejected_without_failing_the_file(
    client_with_db: AsyncClient,
) -> None:
    """A retired or mistyped plate is an ordinary onboarding event, not a corrupt
    file. It is rejected on its own row — visibly, with a reason — while the good
    rows stay reviewable. Aborting a twenty-truck import over one plate would teach
    เมย์ to stop importing, which costs more than the row is worth."""
    batch = await _upload(
        client_with_db,
        f"plate,odometer_km\n{_PLATE_01},505000\nงง-0000 นครนายก,120000\n",
    )

    assert batch["rejected_count"] == 1
    assert batch["proposed_count"] == 1
    rejected = _row_for(batch, "งง-0000 นครนายก")
    assert rejected["status"] == "rejected"
    assert rejected["reason"] == "unknown_plate"
    assert rejected["truck_id"] is None


async def test_an_unknown_plate_row_cannot_be_confirmed_afterwards(
    client_with_db: AsyncClient,
) -> None:
    """The rejection is durable, not advisory: a second request cannot walk it back
    into a confirmation for a truck that does not exist."""
    batch = await _upload(client_with_db, "plate,odometer_km\nงง-0000 นครนายก,120000\n")
    row = _row_for(batch, "งง-0000 นครนายก")

    response = await client_with_db.post(
        f"/api/pm/imports/{batch['batch_id']}/decisions",
        json={"decisions": [{"import_row_id": row["import_row_id"], "confirm": True}]},
    )

    assert response.status_code == 409
    assert "already 'rejected'" in response.text


async def test_a_decided_row_is_not_re_decidable(client_with_db: AsyncClient) -> None:
    """Idempotent BY STATE, the same discipline the gate drivers use: a replayed
    request cannot flip a decline into a confirmation."""
    batch = await _upload(client_with_db, f"plate,odometer_km\n{_PLATE_01},505000\n")
    row_id = _row_for(batch, _PLATE_01)["import_row_id"]
    await _decide(client_with_db, batch["batch_id"], row_id, confirm=False)

    response = await client_with_db.post(
        f"/api/pm/imports/{batch['batch_id']}/decisions",
        json={"decisions": [{"import_row_id": row_id, "confirm": True}]},
    )

    assert response.status_code == 409
    trucks = await _trucks()
    assert trucks["truck-01"]["odometer_km"] == _BASELINE_ODOMETER_01


async def test_overrides_reports_only_what_was_accepted(client_with_db: AsyncClient) -> None:
    """'What did this file say' and 'what have we accepted' are different questions,
    and the second one is the one an audit asks."""
    batch = await _upload(
        client_with_db,
        f"plate,odometer_km\n{_PLATE_01},505000\n{_PLATE_02},700000\n",
    )
    assert (await client_with_db.get("/api/pm/overrides")).json()["overrides"] == []

    await _decide(
        client_with_db, batch["batch_id"], _row_for(batch, _PLATE_01)["import_row_id"], confirm=True
    )

    payload = (await client_with_db.get("/api/pm/overrides")).json()
    assert payload["overrides"] == [
        {"truck_id": "truck-01", "odometer_km": 505_000.0, "next_service_due_km": None}
    ]


async def test_the_batch_is_reviewable_after_upload(client_with_db: AsyncClient) -> None:
    """เมย์ reviews an import as the document it was, not as loose readings."""
    batch = await _upload(
        client_with_db,
        f"plate,odometer_km\n{_PLATE_01},505000\n{_PLATE_02},700000\n",
    )

    fetched = (await client_with_db.get(f"/api/pm/imports/{batch['batch_id']}")).json()

    assert [row["row_number"] for row in fetched["rows"]] == [2, 3]
    assert fetched["imported_by"] == "unattributed"


async def test_an_unknown_batch_is_404(client_with_db: AsyncClient) -> None:
    response = await client_with_db.get("/api/pm/imports/pmb-nope")
    assert response.status_code == 404
