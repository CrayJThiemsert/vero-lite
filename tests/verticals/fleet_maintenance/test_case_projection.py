"""The live-case projection's own edges (PLAN-0096 Step 8, build-order item 2).

The end-to-end behaviour is proven by ``tests/api/test_case_event_path_scenario.py``
against the real routes and the real procedure. What is left here is the handful of
paths that scenario cannot reach cheaply — a case pointing at a truck that is not in
the fleet, and the fingerprint that decides whether to drop ``demo_events``' cache.

Both are DIAGNOSTIC paths, which is exactly why they are tested. An unexercised
"we noticed something went wrong" branch is the confidently-empty failure in a new
place: it reports nothing, and nobody finds out until the number it should have
explained is already in front of the partner.

Pure — no database, no clock.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from services.db.case_events import CaseFacts
from verticals.fleet_maintenance import case_projection
from verticals.fleet_maintenance.case_events import build_event, event_id_for

_NOW = datetime(2026, 7, 30, 4, 0, tzinfo=UTC)

_TRUCKS = [
    {"truck_id": "truck-01", "site_id": "depot-01", "minor_repair_ceiling_thb": 5001.0},
    {"truck_id": "truck-02", "site_id": "depot-01", "minor_repair_ceiling_thb": 5001.0},
]


def _facts(case_id: str = "case-a", truck_id: str = "truck-01", amount: str = "62000.00"):
    return CaseFacts(
        case_id=case_id,
        truck_id=truck_id,
        work_type="breakdown",
        description="เพลาขาดกลางทาง",
        opened_at=_NOW,
        accepted_amount_thb=Decimal(amount),
        accepted_vendor="อู่ริมทางปากช่อง",
        accepted_at=_NOW,
        accepted_reason="เจ้าเดียวที่มีอะไหล่",
        distinct_vendor_count=3,
        has_sole_source_justification=False,
    )


@pytest.fixture(autouse=True)
def _clean() -> None:
    case_projection.reset()


def test_a_case_on_an_unknown_truck_is_skipped_and_named() -> None:
    """Silently dropping it would be the worst of the three options.

    The ``event_for_truck`` join would drop such a row anyway, so emitting it buys
    nothing; raising would take down every other case's projection for one bad
    reference. Skipping and reporting is the only choice that leaves someone able to
    answer "where did my case go".
    """
    case_projection._facts.extend([_facts(), _facts("case-ghost", truck_id="truck-99")])

    events = case_projection.apply([], _TRUCKS)

    assert [e["case_id"] for e in events] == ["case-a"]
    assert case_projection.status()["trucks_not_found"] == ["truck-99"]


def test_apply_appends_and_never_mutates_its_inputs() -> None:
    """The fixture list is a module-level constant upstream; mutating it would leak
    a real case into every later read in the process."""
    case_projection._facts.append(_facts())
    fixture = [{"event_id": "event-reading-01", "truck_id": "truck-02"}]
    trucks = [dict(t) for t in _TRUCKS]

    events = case_projection.apply(fixture, trucks)

    assert len(events) == 2
    assert fixture == [{"event_id": "event-reading-01", "truck_id": "truck-02"}]
    assert trucks == _TRUCKS


def test_the_event_id_is_derived_from_the_case_so_a_reload_is_not_a_new_event() -> None:
    """A random id per build would defeat the fingerprint AND duplicate the case on
    the timeline every refresh."""
    facts = _facts()
    first = build_event(facts, site_id="depot-01", ceiling_thb=5001.0)
    second = build_event(facts, site_id="depot-01", ceiling_thb=5001.0)

    assert first == second
    assert first["event_id"] == event_id_for("case-a")


def test_the_reason_for_not_taking_the_cheapest_reaches_the_timeline() -> None:
    """The audit question is answered where a human is already looking.

    The export will carry it too, but a reason visible only in a month-end file is a
    reason nobody reads while the decision can still be questioned."""
    event = build_event(_facts(), site_id="depot-01", ceiling_thb=5001.0)

    assert "เจ้าเดียวที่มีอะไหล่" in event["description"]
    assert "เกินเพดาน" in event["description"]


def test_a_case_below_its_trucks_ceiling_reads_as_settleable() -> None:
    """The head mechanic settles it; the line should say so rather than alarm."""
    event = build_event(_facts(amount="3200.00"), site_id="depot-01", ceiling_thb=5001.0)

    assert event["severity"] == "info"
    assert "ช่างใหญ่เคาะเองได้" in event["description"]
    assert event["three_quote_basis"] == "under_threshold"
