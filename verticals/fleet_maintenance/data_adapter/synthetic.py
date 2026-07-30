"""Synthetic dataset for the fleet_maintenance vertical (PLAN-0086 timed manual scaffold).

Hand-written from the building_materials fixtures (NOT ``vero-lite new-vertical``). Deterministic,
no external I/O. Shapes match ``fleet_maintenance_v0.yaml``.

Provenance — every value below is either a DIRTY-narrative sentence, a logged simulated-customer
answer, or (since PLAN-0096 Step 1) a REAL design-partner answer. Never invented:

* ``minor_repair_ceiling_thb = 5001`` — design partner **Q8** ("ต้อม ~5,000; some tractor heads
  stretch a bit"). ABOVE ฿5,000 the repair stops being the head mechanic's call and enters the
  governed ladder; the band breaches at/above the ceiling, so his inclusive "up to 5,000" is
  authored as 5001. The per-truck stretch values are a NAMED partner intake question — until he
  gives them, every truck carries the default rather than a number this file made up.
* the breach quote ``48000`` — narrative "เพลาขาดแถวๆ ปากช่อง ... ค่าซ่อมอีก ไม่รู้กี่หมื่น"
  (tens of thousands, unspecified). 48,000 sits inside the customer's own "หมื่นๆ" range. Under the
  partner's REAL ladder (Q9) it clears ฿30,000 and now routes to the OWNER — no longer the
  mid-ladder case it was against the simulated ฿50,000 rung.
* the breach quote ``15000`` — PLAN-0096 Step 1's deliberate MID-LADDER row, so the demo still
  shows tiering rather than always-the-top (the building_materials ฿550,000 precedent). A fixture
  choice, not a partner figure: it exists to exercise the ฿5,001-30,000 วิรัช rung, which the
  ฿48,000 case vacated. Kept honest by being the ONLY invented ฿ figure here, and by being the
  first thing the partner will be asked to replace with a real repair he remembers.
* the two below-ceiling quotes ``3200`` / ``1800`` — narrative "ปกติพวกผ้าเบรก ไส้กรอง ผมซื้อเจ๊หงส์
  กับ ส.เจริญยนต์ เป็นหลัก" (routine consumables, the calm path that never needs a governed run).
* ปากช่อง / กระเบื้องของห้าง / ศูนย์กระจายสินค้าโคราช / สี่โมงเย็น — narrative, verbatim beats.
* the hero truck's PLATE is a GUESS — รอแก้: the customer explicitly could not recall it
  ("หกล้อทะเบียนจำไม่ได้ละ"). Home-yard coordinates are likewise a GUESS (the narrative gives
  ROUTES — แหลมฉบัง / อีสาน — never a base location).

PLAN-0089 (the AT-3 PM calm path) adds ``next_service_due_km`` per truck and a THIRD truck.
Provenance splits cleanly, and the split is the point:

* the 100,000 km service INTERVAL is a logged customer answer ("เข้าศูนย์ทุกแสนกิโลฯ" — the
  PLAN-0089 M-5 Q1 intake round, one fixed interval across every truck class).
* each truck's LAST-SERVICE odometer — from which ``next_service_due_km = last_service +
  100,000`` — is a **DEMO SEED**. The dirtied narrative carries the routine-PM THREAD
  ("ปกติพวกผ้าเบรก ไส้กรอง...", "เปลี่ยนไส้กรองน้ำมันเครื่องตามระยะ") but NO km figures at all.
  Since PLAN-0096 Step 9 these numbers are no longer marked ``รอแก้``, and the change is not
  cosmetic: they are no longer waiting to be corrected IN THIS FILE. The real values arrive
  through the import + human-confirm path (``pm_import.py`` → ``pm_projection.py``, AC-10;
  runbook ``docs/runbooks/fleet-pm-onboarding.md``), which OVERLAYS whatever is confirmed on
  top of the seeds below. Editing them here would be the wrong correction surface.
* truck-03 is a DEMO SEED in full (plate, class, odometer, last service) — no narrative source.
  It exists so the calm-path sweep reads THREE trucks rather than two (PLAN-0089 SD-3's
  Cray-ratified sub-choice) — one due, two not — instead of a 2-row demo where half the fleet
  is always flagged.

PLAN-0096 Step 2 adds ``case_id`` to the two BREACHING quotes only. Two things about that:

* the routine below-ceiling quotes carry none, on purpose — a ฿1,800 filter change is not a
  "case", it is the calm path, and stamping a case id on it would inflate the traceability KPI
  with rows nobody ever opened a case for;
* these are DEMO case ids. Real cases live in Postgres (``repair_case``, written by the
  ``/api/cases`` router at minute 1, before any quote exists). The synthetic ids exist so the
  offline suite can prove the end-to-end link — case id present on the event -> carried by
  intake -> still on the row the DOA gate routes — without needing a database. Step 3 wires the
  real case -> quote -> event path; until then, do not read these ids as rows that exist.

NOTE the deliberate non-overlap, unchanged by PLAN-0096 Step 1: the calm path flags truck-02; the
AT-2 hero flags truck-01 (฿48,000 → owner) and truck-03 (฿15,000 → fleet manager). The two
procedures still watch different trucks for different reasons, so the demo shows a fleet with both
a routine and an emergency story in flight — not one truck carrying everything.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from verticals.fleet_maintenance import case_projection, pm_projection
from verticals.fleet_maintenance.sourcing import compliance_signal_map, compute_three_quote


def _sourcing_signal(
    amount_thb: int, *, distinct_vendors: int, sole_source: bool
) -> dict[str, Any]:
    """The computed sourcing fields for one demo breach row (PLAN-0096 Step 4).

    Runs the REAL ``compute_three_quote`` rather than hard-coding
    ``{"three_quote": true}``. That matters: the fixture and the live case feed now
    share ONE implementation of the rule, so a demo row can never quietly disagree
    with what production would decide about the same numbers. Hard-coding the map
    here would have re-created the fail-open default this step exists to retire,
    just relocated one file away.
    """
    result = compute_three_quote(
        amount_thb=Decimal(amount_thb),
        distinct_vendor_count=distinct_vendors,
        has_sole_source_justification=sole_source,
    )
    _, basis = result
    return {"compliance": compliance_signal_map(result), "three_quote_basis": basis}


def depot_records() -> list[dict[str, Any]]:
    """Return the synthetic Depot records (geo-bearing — lights View A / the map)."""
    return [
        {
            "depot_id": "depot-01",
            "name": "ลานจอดสำนักงานใหญ่ (บางพลี)",
            "depot_type": "home_yard",
            # GUESS — รอแก้: the narrative names routes (แหลมฉบัง / อีสาน), never the yard.
            "lat": 13.5990,
            "lng": 100.7500,
        },
        {
            "depot_id": "depot-02",
            "name": "อู่คู่สัญญา ปากช่อง",
            "depot_type": "partner_garage",
            # ปากช่อง — the narrative's own breakdown location.
            "lat": 14.7100,
            "lng": 101.4160,
        },
    ]


def truck_records() -> list[dict[str, Any]]:
    """Return the synthetic Truck records (the monitored assets).

    ``next_service_due_km`` is ABSOLUTE (``last_service + 100,000``), never an interval — the
    AT-3 judge compares the projected ``measured_value`` against it directly and the projection
    grammar is a fields-only rename with no arithmetic. Exactly ONE truck is due (truck-02), so
    the calm path has a breach set and a healthy contrast set.
    """
    return [
        {
            "truck_id": "truck-01",
            # GUESS — รอแก้ ("หกล้อทะเบียนจำไม่ได้ละ").
            "plate": "80-1234 กรุงเทพมหานคร",
            "accounting_code": "T-001",  # DEMO SEED — รหัสรถ, not the partner's real code.
            "truck_class": "six_wheeler",
            "odometer_km": 412_580.0,
            "minor_repair_ceiling_thb": 5001.0,  # partner Q8
            # last service 400,000 (DEMO SEED) + the 100,000 km interval (M-5 Q1).
            # 412,580 < 500,000 -> NOT due: the hero's breakdown truck is not also PM-flagged.
            "next_service_due_km": 500_000.0,
            "status": "roadside_breakdown",
            "site_id": "depot-01",
        },
        {
            "truck_id": "truck-02",
            "plate": "70-5678 กรุงเทพมหานคร",
            "accounting_code": "T-002",  # DEMO SEED — รหัสรถ.
            "truck_class": "tractor_head",
            "odometer_km": 688_140.0,
            "minor_repair_ceiling_thb": 5001.0,  # partner Q8
            # last service 585,000 (DEMO SEED) + the 100,000 km interval (M-5 Q1).
            # 688,140 >= 685,000 -> DUE, 3,140 km overdue. The high-mileage tractor head running
            # past its interval is the calm path's whole story.
            "next_service_due_km": 685_000.0,
            "status": "in_service",
            "site_id": "depot-01",
        },
        {
            # PLAN-0089 SD-3 sub-choice (Cray-ratified): the third truck, so the calm-path sweep
            # reads three and flags one. DEMO SEED in full; no narrative source.
            "truck_id": "truck-03",
            "plate": "82-9012 กรุงเทพมหานคร",
            # NO accounting_code ON PURPOSE — a truck can be in service before accounting
            # opens it in Express. This is the row that keeps AC-9's KPI non-vacuous: an
            # export drawn only from coded trucks reports 100% traceable whatever happens.
            "truck_class": "six_wheeler",
            "odometer_km": 254_300.0,
            "minor_repair_ceiling_thb": 5001.0,  # partner Q8
            # last service 200,000 (DEMO SEED) + the 100,000 km interval.
            # 254,300 < 300,000 -> NOT due, 45,700 km of headroom.
            "next_service_due_km": 300_000.0,
            "status": "in_service",
            "site_id": "depot-01",
        },
    ]


def operational_events() -> list[dict[str, Any]]:
    """The OperationalEvent stream: the synthetic fixture with REAL cases layered on.

    PLAN-0096 Step 8 (build-order item 2). Until this overlay existed a real repair
    case never reached a governed run at all — เมย์ could open a case, key quotes and
    accept one, and the procedure that routes spend would never see it.

    **A real case OUTRANKS the fixture, and that is the intended behaviour** (Cray,
    typed s191). ``intake`` reads the LATEST event per truck, and a case accepted
    today is later than any fixture beat, so once a real case exists on truck-01 the
    demo's ฿48,000 hero row stops being what the gate judges. The alternative —
    parking real cases on trucks the demo does not use — would have hidden the
    collision in the fixture until two real cases landed on one truck.

    **Why the overlay hangs here rather than on the adapter.** Same reason
    :func:`truck_view` gives: ``data_adapter/__init__.py`` carries the PLAN-0086 AC-7
    row 4 measurement claim (it is STRUCTURALLY EQUAL to what the scaffolder emits,
    and ``test_golden_e2e`` holds it there). Attaching a fleet-specific seam to it
    would retract a measurement. The object SOURCE is the right home.
    """
    return case_projection.apply(_fixture_events(), truck_records())


def _fixture_events() -> list[dict[str, Any]]:
    """The synthetic OperationalEvent records (routine quotes + the two breaching quotes).

    The ฿48,000 breakdown is the FIXTURE's final beat so real-time anchoring (PLAN-0015 D1) leaves
    nothing in the future. With no real case on file, ``intake`` judges truck-01 on that breakdown
    (→ owner tier), truck-03 on its ฿15,000 gearbox quote (→ fleet-manager tier, the PLAN-0096
    Step 1 mid-ladder row) and truck-02 on its routine ฿1,800 service (verdict ``ok``). Two
    breaches, two different tiers: the demo shows the ladder ROUTING, which a single-breach
    fixture cannot. A real accepted case supersedes whichever of these shares its truck.
    """
    return [
        {
            "event_id": "event-reading-01",
            "event_type": "reading",
            "severity": "info",
            "measured_value": 3200.0,
            "unit": "THB",
            "description": (
                "เปลี่ยนผ้าเบรกหน้า ใบเสนอราคา 3,200 บาท (ร้านประจำ) — ต่ำกว่าเพดาน 5,000 บาท "
                "ช่างใหญ่เคาะเองได้ ไม่ต้องเข้าสายอนุมัติ."
            ),
            "occurred_at": datetime(2026, 7, 1, 2, 0, tzinfo=UTC),
            "truck_id": "truck-01",
            "site_id": "depot-01",
        },
        {
            # PLAN-0089: truck-03's routine below-ceiling service quote. Superseded as truck-03's
            # LATEST reading by the PLAN-0096 ฿15,000 gearbox quote below, so this row now plays
            # the same part the other routine quotes do: history the demo can scroll back through.
            "event_id": "event-reading-04",
            "event_type": "reading",
            "severity": "info",
            "measured_value": 2400.0,
            "unit": "THB",
            "description": (
                "เปลี่ยนผ้าเบรกหลัง ใบเสนอราคา 2,400 บาท (ร้านประจำ) — ต่ำกว่าเพดาน 5,000 บาท "
                "ช่างใหญ่เคาะเองได้."
            ),
            "occurred_at": datetime(2026, 7, 2, 8, 15, tzinfo=UTC),
            "truck_id": "truck-03",
            "site_id": "depot-01",
        },
        {
            "event_id": "event-reading-03",
            "event_type": "reading",
            "severity": "info",
            "measured_value": 1800.0,
            "unit": "THB",
            "description": (
                "เปลี่ยนไส้กรองน้ำมันเครื่องตามระยะ ใบเสนอราคา 1,800 บาท (ร้านประจำ) — "
                "ต่ำกว่าเพดาน 5,000 บาท."
            ),
            "occurred_at": datetime(2026, 7, 3, 3, 30, tzinfo=UTC),
            "truck_id": "truck-02",
            "site_id": "depot-01",
        },
        {
            # PLAN-0096 Step 1 — the MID-LADDER breach. Under the partner's real Q9 ladder the
            # ฿48,000 case moved up to the owner's tier, which would have left the demo showing
            # only ever the top rung. This ฿15,000 gearbox quote lands in [5,001, 30,001) and
            # routes to วิรัช, so the ladder is visibly a LADDER. The ฿ figure is the one
            # deliberately-invented number in this file (see the module docstring) — a shape the
            # partner is meant to correct, not a claim about his fleet.
            "event_id": "event-reading-05",
            "event_type": "reading",
            "severity": "warn",
            "measured_value": 15000.0,
            "unit": "THB",
            # PLAN-0096 Step 2 (AC-3): the case เมย์ opened when ต้อม phoned in the
            # noise, BEFORE any quote existed. See the module docstring on why the
            # demo carries case ids at all.
            "case_id": "case-demo-truck03-gearbox",
            # PLAN-0096 Step 4: ฿15,000 sits UNDER the ฿30,000 comparison threshold,
            # so the sourcing rule never applies — one quote is enough and the basis
            # says why. The contrast with truck-01 below is the demo's whole point.
            **_sourcing_signal(15_000, distinct_vendors=1, sole_source=False),
            "description": (
                "เกียร์มีเสียงดังผิดปกติ อู่ประจำเสนอราคาซ่อม 15,000 บาท — เกินเพดาน 5,000 บาท "
                "ต้องเข้าสายอนุมัติ ระดับ ผจก.เดินรถ."
            ),
            "occurred_at": datetime(2026, 7, 4, 6, 45, tzinfo=UTC),
            "truck_id": "truck-03",
            "site_id": "depot-01",
        },
        {
            "event_id": "event-reading-02",
            "event_type": "reading",
            "severity": "critical",
            "measured_value": 48000.0,
            "unit": "THB",
            # PLAN-0096 Step 2 (AC-3): opened from the roadside at minute 1, well
            # before the อู่ quoted 48,000 — which is the entire point of the case.
            "case_id": "case-demo-truck01-axle",
            # PLAN-0096 Step 4: ฿48,000 is OVER the threshold, so the rule applies —
            # and เมย์ collected three separate quotes while the truck sat at the
            # partner garage. The row passes on `three_quotes`, honestly earned,
            # where the retired fail-open default used to pass it on nothing at all.
            **_sourcing_signal(48_000, distinct_vendors=3, sole_source=False),
            "description": (
                "เพลาขาดกลางทางแถวปากช่อง รถจอดข้างทางพร้อมกระเบื้องเต็มคันของห้าง "
                "ต้องถึงศูนย์กระจายสินค้าโคราชก่อนสี่โมงเย็น — อู่เสนอราคาซ่อม 48,000 บาท "
                "เกินเพดาน 5,000 บาท ต้องเข้าสายอนุมัติ."
            ),
            "occurred_at": datetime(2026, 7, 5, 4, 15, tzinfo=UTC),
            "truck_id": "truck-01",
            "site_id": "depot-02",
        },
    ]


def truck_view() -> list[dict[str, Any]]:
    """The Truck records as the ontology serves them: seeds with confirmed PM values on top.

    PLAN-0096 Step 9 / AC-10. ``truck_records`` above stays the pure fixture — it is what
    the fleet looks like before anyone has confirmed anything — and this is the one place the
    two are combined, so a reader can see the whole of the overlay in three lines.

    **Why the overlay hangs here rather than on the adapter.** The obvious home was
    ``data_adapter/__init__.py``, next to the ``demo_events`` wrapper it mirrors. But that
    file carries a measurement claim: PLAN-0086 AC-7 row 4 records that this hand-written
    adapter is STRUCTURALLY EQUAL to what the Tier-1 scaffolder emits, and
    ``test_row_4_adapter_is_structurally_equal_to_the_donor`` holds it to that. Adding a
    fleet-specific seam there would have retracted a measurement — and the alternative,
    teaching the scaffolder to emit a PM overlay, would hand every future vertical a
    workaround for a problem only this one has (its objects come from a fixture rather than
    a real system). Attaching it to the object SOURCE keeps both facts true.
    """
    return pm_projection.apply(truck_records())


def vendor_records() -> list[dict[str, Any]]:
    """Return the synthetic Vendor records — the garages the fleet buys repairs from.

    The registry the month-end export resolves a typed vendor name against (AC-9 columns
    5 and 6). Names are matched EXACTLY — trimmed, case-insensitively — the same rule
    ``services/db/evidence_pack.py`` applies and for the same stated reason: fuzzy matching
    would merge vendors the operator meant to keep apart.

    ``accounting_code`` is DEMO SEED, not the partner's real Express codes — those arrive
    with his vendor master (~20-30 coded vendors), and inventing plausible-looking ones here
    would put fake accounting keys in a public repository.

    **vendor-03 deliberately has no code.** A garage can legitimately be used before
    accounting opens it in Express — the partner marked the column "รหัสผู้ขาย (ถ้ามี)"
    himself — so this row is what proves AC-9's KPI is not vacuous: an export built only
    from coded vendors would report 100% traceable no matter what.
    """
    return [
        {
            "vendor_id": "vendor-01",
            # The partner's own contracted garage, named in the narrative.
            "name": "อู่คู่สัญญา ปากช่อง",
            "accounting_code": "V-001",  # DEMO SEED
        },
        {
            "vendor_id": "vendor-02",
            # Named in the quote-provenance comment at the top of this module.
            "name": "ส.เจริญยนต์",
            "accounting_code": "V-002",  # DEMO SEED
        },
        {
            "vendor_id": "vendor-03",
            "name": "เจ๊หงส์",
            # No accounting_code ON PURPOSE — see the docstring. Used but not yet opened
            # in Express, which is a real state the export has to report honestly.
        },
    ]


OBJECT_SOURCES = {
    "Depot": depot_records,
    "Truck": truck_view,
    "Vendor": vendor_records,
}
