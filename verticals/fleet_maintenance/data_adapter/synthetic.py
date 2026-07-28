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
  100,000`` — is GUESS — รอแก้. The dirtied narrative carries the routine-PM THREAD
  ("ปกติพวกผ้าเบรก ไส้กรอง...", "เปลี่ยนไส้กรองน้ำมันเครื่องตามระยะ") but NO km figures at all,
  so every due point below is a fixture choice the design partner re-feeds.
* truck-03 is a GUESS — รอแก้ in full (plate, class, odometer, last service). It exists so the
  calm-path sweep reads THREE trucks rather than two (PLAN-0089 SD-3's Cray-ratified sub-choice)
  — one due, two not — instead of a 2-row demo where half the fleet is always flagged.

NOTE the deliberate non-overlap, unchanged by PLAN-0096 Step 1: the calm path flags truck-02; the
AT-2 hero flags truck-01 (฿48,000 → owner) and truck-03 (฿15,000 → fleet manager). The two
procedures still watch different trucks for different reasons, so the demo shows a fleet with both
a routine and an emergency story in flight — not one truck carrying everything.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


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
            "truck_class": "six_wheeler",
            "odometer_km": 412_580.0,
            "minor_repair_ceiling_thb": 5001.0,  # partner Q8
            # last service 400,000 (GUESS — รอแก้) + the 100,000 km interval (M-5 Q1).
            # 412,580 < 500,000 -> NOT due: the hero's breakdown truck is not also PM-flagged.
            "next_service_due_km": 500_000.0,
            "status": "roadside_breakdown",
            "site_id": "depot-01",
        },
        {
            "truck_id": "truck-02",
            "plate": "70-5678 กรุงเทพมหานคร",
            "truck_class": "tractor_head",
            "odometer_km": 688_140.0,
            "minor_repair_ceiling_thb": 5001.0,  # partner Q8
            # last service 585,000 (GUESS — รอแก้) + the 100,000 km interval (M-5 Q1).
            # 688,140 >= 685,000 -> DUE, 3,140 km overdue. The high-mileage tractor head running
            # past its interval is the calm path's whole story.
            "next_service_due_km": 685_000.0,
            "status": "in_service",
            "site_id": "depot-01",
        },
        {
            # PLAN-0089 SD-3 sub-choice (Cray-ratified): the third truck, so the calm-path sweep
            # reads three and flags one. GUESS — รอแก้ in full; no narrative source.
            "truck_id": "truck-03",
            "plate": "82-9012 กรุงเทพมหานคร",
            "truck_class": "six_wheeler",
            "odometer_km": 254_300.0,
            "minor_repair_ceiling_thb": 5001.0,  # partner Q8
            # last service 200,000 (GUESS — รอแก้) + the 100,000 km interval.
            # 254,300 < 300,000 -> NOT due, 45,700 km of headroom.
            "next_service_due_km": 300_000.0,
            "status": "in_service",
            "site_id": "depot-01",
        },
    ]


def operational_events() -> list[dict[str, Any]]:
    """Return the synthetic OperationalEvent records (routine quotes + the two breaching quotes).

    The ฿48,000 breakdown is the timeline's FINAL beat so real-time anchoring (PLAN-0015 D1) leaves
    nothing in the future. ``intake`` reads the LATEST event per truck, so truck-01 is judged on
    that breakdown (→ owner tier), truck-03 on its ฿15,000 gearbox quote (→ fleet-manager tier,
    the PLAN-0096 Step 1 mid-ladder row) and truck-02 on its routine ฿1,800 service (verdict
    ``ok``). Two breaches, two different tiers: the demo shows the ladder ROUTING, which a
    single-breach fixture cannot.
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


OBJECT_SOURCES = {
    "Depot": depot_records,
    "Truck": truck_records,
}
