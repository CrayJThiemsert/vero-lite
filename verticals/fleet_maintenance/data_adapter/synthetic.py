"""Synthetic dataset for the fleet_maintenance vertical (PLAN-0086 timed manual scaffold).

Hand-written from the building_materials fixtures (NOT ``vero-lite new-vertical``). Deterministic,
no external I/O. Shapes match ``fleet_maintenance_v0.yaml``.

Narrative provenance (PLAN-0086 AC-3) — every value below is either a DIRTY-narrative sentence or a
logged customer answer, never invented:

* ``minor_repair_ceiling_thb = 5000`` — customer-question log **Q1** ("ต้อมเคาะได้ถึง 5 พัน"):
  at/above this the repair stops being the head mechanic's call and enters the governed ladder.
* the breach quote ``48000`` — narrative "เพลาขาดแถวๆ ปากช่อง ... ค่าซ่อมอีก ไม่รู้กี่หมื่น"
  (tens of thousands, unspecified). 48,000 sits inside the customer's own "หมื่นๆ" range AND lands
  mid-ladder in the fleet-manager tier [5k, 50k) — the demo shows TIERING, not always-the-top
  (the building_materials ฿550,000 precedent). The exact figure is a fixture choice inside a
  customer-stated range; the closeout records it as such.
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

NOTE the deliberate non-overlap: the calm path flags truck-02, the AT-2 hero flags truck-01. The
two procedures watch different trucks for different reasons, so the demo shows a fleet with both
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
            "minor_repair_ceiling_thb": 5000.0,  # Q1
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
            "minor_repair_ceiling_thb": 5000.0,  # Q1
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
            "minor_repair_ceiling_thb": 5000.0,
            # last service 200,000 (GUESS — รอแก้) + the 100,000 km interval.
            # 254,300 < 300,000 -> NOT due, 45,700 km of headroom.
            "next_service_due_km": 300_000.0,
            "status": "in_service",
            "site_id": "depot-01",
        },
    ]


def operational_events() -> list[dict[str, Any]]:
    """Return the synthetic OperationalEvent records (routine quotes + the breakdown breach).

    The breach is the timeline's FINAL beat so real-time anchoring (PLAN-0015 D1) leaves nothing
    in the future. ``intake`` reads the LATEST event per truck, so truck-01 is judged on the
    ฿48,000 breakdown and truck-02 on its routine ฿1,800 service (verdict ``ok``).
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
            # PLAN-0089: truck-03's routine below-ceiling service quote. Keeps the third truck
            # visible to the HERO's intake too (latest event per truck) as a plain `ok` row —
            # it grows the sweep's read set without touching the breach set (still truck-01 only).
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
