"""PLAN-0096 Step 9 / AC-10 — the PM import parser and the confirmed-PM projection.

The half of AC-10 that needs no database. Its companion,
``tests/api/test_pm_import_endpoint.py``, proves the measured-then-confirmed gate
against a real Postgres round-trip; this module proves the two pure pieces underneath
it, so a Postgres outage skips the storage tests without hiding the fail-closed
parsing that keeps a mangled export out of the fleet.

The parser's contract has an asymmetry worth stating, because it is a design decision
and not an oversight: **a mangled file fails whole, a mismatched row fails alone.**
Structure and type faults abort the entire parse — half-importing a fleet leaves it in
a state nobody can reason about — while a plate the fleet does not recognise is an
ordinary onboarding event that must not take twenty good rows down with it.
"""

from __future__ import annotations

import pytest

from verticals.fleet_maintenance import pm_projection
from verticals.fleet_maintenance.data_adapter import synthetic
from verticals.fleet_maintenance.pm_import import (
    SERVICE_INTERVAL_KM,
    PmImportError,
    next_service_due_from,
    parse_pm_csv,
)

_PLATE_01 = "80-1234 กรุงเทพมหานคร"
_PLATE_02 = "70-5678 กรุงเทพมหานคร"


@pytest.fixture(autouse=True)
def _clean_projection() -> None:
    """The projection is process-global (the ``demo_events`` shape), so cases reset it."""
    pm_projection.reset()


# --------------------------------------------------------------------------- #
# The Wialon export half — current odometer
# --------------------------------------------------------------------------- #


def test_a_wialon_odometer_export_becomes_proposals() -> None:
    """AC-10 happy: plate + odometer in, typed proposals out, in file order."""
    csv_text = f"plate,odometer_km\n{_PLATE_01},412580\n{_PLATE_02},688140\n"

    proposals = parse_pm_csv(csv_text)

    assert [p.plate for p in proposals] == [_PLATE_01, _PLATE_02]
    assert [p.odometer_km for p in proposals] == [412580.0, 688140.0]
    # Row 1 is the header, so เมย์'s first data row is 2 — the number she sees in the
    # spreadsheet, not a zero-based index into a list she cannot.
    assert [p.row_number for p in proposals] == [2, 3]
    assert all(
        p.next_service_due_km is None for p in proposals
    ), "an odometer-only export says nothing about when a service falls due"


def test_real_export_noise_is_tolerated_not_refused() -> None:
    """A BOM, padded headers, mixed case and thousands separators all parse.

    None of these is the partner's fault or his choice — they are what a spreadsheet
    export contains. Refusing them would be a governance control that only ever fires
    on honest files, and the first thing it would teach เมย์ is to stop importing."""
    csv_text = f'﻿ Plate , ODOMETER_KM \n{_PLATE_01}," 412,580 "\n'

    [proposal] = parse_pm_csv(csv_text)

    assert proposal.plate == _PLATE_01
    assert proposal.odometer_km == 412580.0


# --------------------------------------------------------------------------- #
# The paper-PM-folder half — last service, and the arithmetic done at load
# --------------------------------------------------------------------------- #


def test_last_service_is_turned_into_an_absolute_due_point_at_load() -> None:
    """AC-10: ``next_service_due_km`` is computed here, once, and stored absolute.

    The ontology's own comment promises this, and the reason is structural rather than
    stylistic: the projection grammar downstream is a fields-only rename with no
    arithmetic, so there is nowhere else it COULD be computed. If this stopped
    happening at load, every truck's due point would silently become its last-service
    odometer — i.e. every truck would read as overdue by 100,000 km."""
    csv_text = f"plate,last_service_odometer_km\n{_PLATE_02},585000\n"

    [proposal] = parse_pm_csv(csv_text)

    assert proposal.last_service_odometer_km == 585000.0
    assert proposal.next_service_due_km == 685000.0
    assert proposal.next_service_due_km == 585000.0 + SERVICE_INTERVAL_KM
    assert next_service_due_from(585000.0) == 685000.0


def test_one_file_may_carry_both_figures() -> None:
    """Onboarding may hand over one sheet with both columns; nothing forbids it."""
    csv_text = f"plate,odometer_km,last_service_odometer_km\n{_PLATE_02},688140,585000\n"

    [proposal] = parse_pm_csv(csv_text)

    assert proposal.odometer_km == 688140.0
    assert proposal.next_service_due_km == 685000.0


def test_an_empty_cell_means_silence_not_zero() -> None:
    """A blank odometer column on a last-service sheet leaves the field unset.

    Coercing it to 0.0 would be catastrophic and quiet: a truck whose odometer read
    zero would never again reach any due point."""
    csv_text = f"plate,odometer_km,last_service_odometer_km\n{_PLATE_02},,585000\n"

    [proposal] = parse_pm_csv(csv_text)

    assert proposal.odometer_km is None
    assert proposal.last_service_odometer_km == 585000.0


# --------------------------------------------------------------------------- #
# FAIL CLOSED — the mangled-file half of AC-10
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("csv_text", "expected"),
    [
        pytest.param("", "empty", id="empty-file"),
        pytest.param("plate\n80-1234\n", "carries none of", id="no-value-column"),
        pytest.param("odometer_km\n412580\n", "no 'plate' column", id="no-plate-column"),
        pytest.param("plate,odometer_km\n", "no data rows", id="header-only"),
        pytest.param("plate,odometer_km\n   ,412580\n", "is blank", id="blank-plate"),
        pytest.param(
            "plate,odometer_km\n80-1234,four hundred\n", "is not a number", id="non-numeric"
        ),
        pytest.param("plate,odometer_km\n80-1234,-5\n", "is negative", id="negative"),
        pytest.param(
            "plate,odometer_km,last_service_odometer_km\n80-1234,,\n",
            "carries no value",
            id="row-says-nothing",
        ),
        pytest.param(
            "plate,odometer_km\n80-1234,1\n80-1234,2\n", "already appeared", id="duplicate-plate"
        ),
    ],
)
def test_a_mangled_file_proposes_nothing(csv_text: str, expected: str) -> None:
    """AC-10 fail-closed: every one of these refuses the WHOLE file.

    The duplicate-plate case is the least obvious and the most important. Two readings
    for one truck are not a formatting problem — they make the confirm step ambiguous
    about which number a human just agreed to, and there is no safe way to guess."""
    with pytest.raises(PmImportError, match=expected):
        parse_pm_csv(csv_text)


def test_the_failing_row_is_named() -> None:
    """เมย์ is told which line to look at. 'Invalid file' on a thirty-truck sheet is
    an instruction to give up."""
    csv_text = f"plate,odometer_km\n{_PLATE_01},412580\n{_PLATE_02},oops\n"

    with pytest.raises(PmImportError, match="row 3"):
        parse_pm_csv(csv_text)


# --------------------------------------------------------------------------- #
# The projection — where a confirmed value becomes something the ontology sees
# --------------------------------------------------------------------------- #


def test_with_nothing_confirmed_the_fleet_is_byte_identical() -> None:
    """The only-when-supplied shape, applied to behaviour: before anyone confirms
    anything, the Truck view is exactly what it was before this feature existed."""
    baseline = synthetic.truck_records()

    assert pm_projection.apply(baseline) == baseline


def test_a_confirmed_value_replaces_only_that_truck_and_only_that_field() -> None:
    """The overlay is surgical. A confirmed odometer must not disturb the truck's
    authority band, its status, or any other truck — an import has no business moving
    ``minor_repair_ceiling_thb``, which is a governance number the partner answered."""
    pm_projection._overrides["truck-01"] = {"odometer_km": 505_000.0}
    baseline = {t["truck_id"]: t for t in synthetic.truck_records()}

    applied = {t["truck_id"]: t for t in pm_projection.apply(synthetic.truck_records())}

    assert applied["truck-01"]["odometer_km"] == 505_000.0
    assert (
        applied["truck-01"]["minor_repair_ceiling_thb"]
        == (baseline["truck-01"]["minor_repair_ceiling_thb"])
    )
    assert applied["truck-01"]["status"] == baseline["truck-01"]["status"]
    assert applied["truck-02"] == baseline["truck-02"]
    assert applied["truck-03"] == baseline["truck-03"]


def test_the_overlay_does_not_mutate_the_fixture() -> None:
    """The synthetic source hands out module-level records. Mutating them in place
    would let one request's confirmed override leak into every later read in the
    process — including the offline suite's other cases."""
    pm_projection._overrides["truck-01"] = {"odometer_km": 999_999.0}

    pm_projection.apply(synthetic.truck_records())

    assert synthetic.truck_records()[0]["odometer_km"] == 412_580.0


def test_status_distinguishes_nothing_confirmed_from_could_not_read() -> None:
    """On an evidence surface those are different answers, and a view that reported
    them identically would be the reassuring-empty-state lie in a new place."""
    assert pm_projection.status() == {
        "loaded": False,
        "trucks_with_confirmed_values": 0,
        "last_error": None,
    }

    pm_projection.record_unavailable("connection refused")

    assert pm_projection.status()["last_error"] == "connection refused"
    assert pm_projection.status()["loaded"] is False
