"""Deterministic synthetic dataset for the procurement vertical (PLAN-0036 Step 5).

Scaffolded by ``vero-lite new-vertical`` (PLAN-0016) then **human-authored** into
the demo timeline below (ADR-0015 D5). No external I/O and no randomness — every
call returns the same data, so demos and tests are reproducible. All identifiers
are **abstract** (a generic EEC auto-parts operator); **no design-partner brand
names** appear here (wording discipline, L-7).

Shapes match ``verticals/procurement/ontology/procurement_v0.yaml`` — adapter dict
keys are ontology property names (the engine does zero field translation).

The dataset tells two stories on one governed engine:

* **HERO (emergency sourcing).** A critical CNC machining center (``equip-cnc-07``)
  fails at an EEC plant. Its spare spindle servo drive (``part-spindle-01``) is out
  of stock; the contracted OEM's lead time (21d) is too slow for a line-down, so
  the scored sourcing rule takes a faster off-contract RFQ supplier (5d) — which
  trips the **AVL exception + emergency waiver + the top DOA tier (ผอ., > ฿2M)**.
  A third quote is **blocked by a failed compliance criterion** (the supplier's
  certificate is expired) — the per-criterion gate biting, not theater.
* **CALM-PATH (low-stock reorder).** A coolant-filter cartridge (``part-filter-02``)
  drops to 40 units, at/below its 100-unit reorder point — a routine, single-tier
  (หน.จัดซื้อ, ≤ ฿50k) reorder, the familiar MRO contrast.

GOVERNED ≠ GENERATED (L-3): the LLM only drafts/summarises. Selection is the
scored rule (the RFQ supplier wins on criticality + lead time, recorded here);
the thresholds are authored (procedures.yaml); approval is the human gate.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

CNC_FAILURE_CRITICALITY = 0.92
"""The breaching criticality reading on equip-cnc-07 — above the 0.8 band
(procedures.yaml judge: threshold 0.8 / above) so the CNC failure escalates to
the emergency-sourcing path while nominal equipment stays silent."""

HERO_PO_AMOUNT_THB = 2_150_000.0
"""The selected RFQ quote / hero PO value — above the ฿2M tier-3 ceiling, so it
escalates to the ผอ. (Director) DOA tier under the emergency waiver."""

CALM_PO_AMOUNT_THB = 45_000.0
"""The calm-path reorder PO value — within the ฿50k tier-1 (หน.จัดซื้อ) band."""

FILTER_STOCK_QTY = 40
FILTER_REORDER_POINT = 100
"""The calm-path part is at 40 units, at/below its 100-unit reorder point
(procedures.yaml judge_stock: threshold 100 / below)."""

HIGHTURN_STOCK_QTY = 150
HIGHTURN_REORDER_POINT = 200
"""PLAN-0066 SD-4(b): the demo-visible per-part FLIP. A high-turnover part carried at
150 units. A blanket 100-unit reorder threshold clears it (150 > 100 -> ok), but its
OWN 200-unit reorder point flags it (150 <= 200 -> breach). Per-part banding
(judge_stock: threshold_field reorder_point, ADR-016 TF-1) catches the low-stock
high-reorder part the blanket band silently misses."""


def plant_records() -> list[dict[str, Any]]:
    """Return the synthetic Plant records (geo-bearing — map-plottable). Abstract
    EEC locations (Rayong / Chonburi); no brand names."""
    return [
        {
            "plant_id": "plant-eec-01",
            "name": "EEC Assembly Plant 1",
            "plant_type": "assembly",
            "lat": 12.68,
            "lng": 101.15,
        },
        {
            "plant_id": "plant-eec-02",
            "name": "EEC Machining Plant 2",
            "plant_type": "machining",
            "lat": 13.36,
            "lng": 100.98,
        },
    ]


def equipment_records() -> list[dict[str, Any]]:
    """Return the synthetic Equipment records. ``equip-cnc-07`` is the hero — a
    critical CNC machining center in the failed state."""
    return [
        {
            "equipment_id": "equip-cnc-07",
            "name": "CNC Machining Center #7",
            "equipment_type": "cnc_machine",
            "criticality": "critical",
            "status": "failed",
            "site_id": "plant-eec-01",
        },
        {
            "equipment_id": "equip-press-03",
            "name": "Stamping Press #3",
            "equipment_type": "stamping_press",
            "criticality": "high",
            "status": "operational",
            "site_id": "plant-eec-01",
        },
        {
            "equipment_id": "equip-robot-02",
            "name": "Welding Robot Arm #2",
            "equipment_type": "robot_arm",
            "criticality": "medium",
            "status": "operational",
            "site_id": "plant-eec-02",
        },
        {
            "equipment_id": "equip-conveyor-05",
            "name": "Line Conveyor #5",
            "equipment_type": "conveyor",
            "criticality": "low",
            "status": "operational",
            "site_id": "plant-eec-02",
        },
    ]


def operational_events() -> list[dict[str, Any]]:
    """Return the synthetic OperationalEvent records, in chronological order.

    Nominal baselines, a low-stock signal (the calm-path beat), and — as the
    timeline's **final beat** — the CNC criticality failure (measured_value 0.92
    >= the 0.8 judge band) that drives the emergency-sourcing hero. The failure is
    the latest event so real-time anchoring (PLAN-0015 D1) leaves nothing in the
    future. ``measured_value`` carries the criticality score for failure/reading
    events and the on-hand stock count for the low_stock event (each procedure
    reads its own event subset)."""
    return [
        {
            "event_id": "event-cnc-07-baseline",
            "event_type": "reading",
            "severity": "info",
            "measured_value": 0.30,
            "unit": "criticality",
            "description": "CNC Machining Center #7 operating nominally.",
            "occurred_at": datetime(2026, 6, 1, 6, 0, tzinfo=UTC),
            "equipment_id": "equip-cnc-07",
            "site_id": "plant-eec-01",
        },
        {
            "event_id": "event-press-03-baseline",
            "event_type": "reading",
            "severity": "info",
            "measured_value": 0.45,
            "unit": "criticality",
            "description": "Stamping Press #3 operating nominally.",
            "occurred_at": datetime(2026, 6, 1, 6, 10, tzinfo=UTC),
            "equipment_id": "equip-press-03",
            "site_id": "plant-eec-01",
        },
        {
            "event_id": "event-filter-02-low-stock",
            "event_type": "low_stock",
            "severity": "warn",
            "measured_value": float(FILTER_STOCK_QTY),
            "unit": "units",
            "description": "Coolant filter cartridge stock fell to 40 units (reorder point 100).",
            "occurred_at": datetime(2026, 6, 1, 8, 30, tzinfo=UTC),
            "equipment_id": "equip-conveyor-05",
            "site_id": "plant-eec-02",
        },
        {
            "event_id": "event-cnc-07-failure",
            "event_type": "failure",
            "severity": "critical",
            "measured_value": CNC_FAILURE_CRITICALITY,
            "unit": "criticality",
            "description": (
                "CNC Machining Center #7 spindle drive failed — line down, spare out of stock."
            ),
            "occurred_at": datetime(2026, 6, 1, 9, 15, tzinfo=UTC),
            "equipment_id": "equip-cnc-07",
            "site_id": "plant-eec-01",
        },
    ]


def part_records() -> list[dict[str, Any]]:
    """Return the synthetic Part records — the hero spare (out of stock) and the
    calm-path low-stock consumable."""
    return [
        {
            "part_no": "part-spindle-01",
            "name": "CNC Spindle Servo Drive",
            "on_contract": True,
            "preferred_supplier": "sup-contract-01",
            "stock_qty": 0,
            "reorder_point": 1,
            "lead_time": 21,
            "fits_equipment_id": "equip-cnc-07",
        },
        {
            "part_no": "part-filter-02",
            "name": "Coolant Filter Cartridge",
            "on_contract": True,
            "preferred_supplier": "sup-contract-02",
            "stock_qty": FILTER_STOCK_QTY,
            "reorder_point": FILTER_REORDER_POINT,
            "lead_time": 7,
            "fits_equipment_id": "equip-conveyor-05",
        },
        {
            # PLAN-0066 SD-4(b): the per-part flip part — a high-turnover consumable whose
            # high reorder_point (200) a blanket-100 threshold wrongly clears. `ok` under
            # scalar-100, `breach` under per-part banding (threshold_field: reorder_point).
            "part_no": "part-vbelt-03",
            "name": "Drive V-Belt (high-turnover)",
            "on_contract": True,
            "preferred_supplier": "sup-contract-02",
            "stock_qty": HIGHTURN_STOCK_QTY,
            "reorder_point": HIGHTURN_REORDER_POINT,
            "lead_time": 5,
            "fits_equipment_id": "equip-conveyor-05",
        },
    ]


def supplier_records() -> list[dict[str, Any]]:
    """Return the synthetic Supplier records. The contracted OEM is the default
    (single-source, slow); the RFQ supplier is the AVL exception (faster); the alt
    supplier FAILS the cert criterion (per-criterion compliance blocks it)."""
    return [
        {
            "supplier_id": "sup-contract-01",
            "name": "Contracted OEM Spares Co.",
            "avl_status": "approved",
            "tax_id": "0105540000111",
            "cert_status": "valid",
            "sanctions_flag": False,
            "single_source_flag": True,
        },
        {
            "supplier_id": "sup-rfq-01",
            "name": "Regional Industrial Supply",
            "avl_status": "pending",
            "tax_id": "0205550000222",
            "cert_status": "valid",
            "sanctions_flag": False,
            "single_source_flag": False,
        },
        {
            "supplier_id": "sup-rfq-02",
            "name": "Allied Parts Trading",
            "avl_status": "approved",
            "tax_id": "0305560000333",
            "cert_status": "expired",
            "sanctions_flag": False,
            "single_source_flag": False,
        },
        {
            "supplier_id": "sup-contract-02",
            "name": "MRO Consumables Ltd.",
            "avl_status": "approved",
            "tax_id": "0405570000444",
            "cert_status": "valid",
            "sanctions_flag": False,
            "single_source_flag": False,
        },
    ]


def quotation_records() -> list[dict[str, Any]]:
    """Return the synthetic Quotation records. Spindle quotes: the on-contract OEM
    (slow), the selected RFQ supplier (fast, higher ฿ — the scored-rule winner),
    and the cert-blocked alternative. Plus the calm-path filter quote."""
    return [
        {
            "quote_id": "quote-spindle-contract",
            "part_no": "part-spindle-01",
            "supplier_id": "sup-contract-01",
            "price": 1_850_000.0,
            "currency": "THB",
            "lead_time": 21,
            "warranty": "12 months",
            "on_contract": True,
        },
        {
            "quote_id": "quote-spindle-rfq",
            "part_no": "part-spindle-01",
            "supplier_id": "sup-rfq-01",
            "price": HERO_PO_AMOUNT_THB,
            "currency": "THB",
            "lead_time": 5,
            "warranty": "6 months",
            "on_contract": False,
        },
        {
            "quote_id": "quote-spindle-alt",
            "part_no": "part-spindle-01",
            "supplier_id": "sup-rfq-02",
            "price": 1_950_000.0,
            "currency": "THB",
            "lead_time": 9,
            "warranty": "6 months",
            "on_contract": False,
        },
        {
            "quote_id": "quote-filter-contract",
            "part_no": "part-filter-02",
            "supplier_id": "sup-contract-02",
            "price": CALM_PO_AMOUNT_THB,
            "currency": "THB",
            "lead_time": 7,
            "warranty": "3 months",
            "on_contract": True,
        },
    ]


def purchase_order_records() -> list[dict[str, Any]]:
    """Return the synthetic PurchaseOrder records — the hero PO (waiver applied,
    SoD chain, forced justification) and the calm-path reorder PO."""
    return [
        {
            "po_id": "po-spindle-01",
            "part_no": "part-spindle-01",
            "supplier_id": "sup-rfq-01",
            "quote_id": "quote-spindle-rfq",
            "amount": HERO_PO_AMOUNT_THB,
            "currency": "THB",
            "status": "pending_approval",
            "approver_chain": [
                {"role": "requester", "name": "maintenance-eng-01"},
                {"role": "head_purchasing", "name": "หน.จัดซื้อ"},
                {"role": "plant_manager", "name": "ผจก.โรงงาน"},
                {"role": "director", "name": "ผอ."},
            ],
            "waiver_applied": True,
            "justification": (
                "Critical line-down on CNC #7; on-contract OEM lead time 21d vs RFQ 5d. "
                "Emergency waiver: 3-bid/sole-source relaxed, AVL exception logged for "
                "sup-rfq-01 (AVL pending), approver escalated to ผอ. (> ฿2M)."
            ),
        },
        {
            "po_id": "po-filter-02",
            "part_no": "part-filter-02",
            "supplier_id": "sup-contract-02",
            "quote_id": "quote-filter-contract",
            "amount": CALM_PO_AMOUNT_THB,
            "currency": "THB",
            "status": "pending_approval",
            "approver_chain": [
                {"role": "requester", "name": "store-keeper-02"},
                {"role": "head_purchasing", "name": "หน.จัดซื้อ"},
            ],
            "waiver_applied": False,
            "justification": (
                "Routine low-stock reorder on contract (stock 40 <= reorder point 100)."
            ),
        },
    ]


def compliance_rule_records() -> list[dict[str, Any]]:
    """Return the per-criterion compliance rules the compliance step evaluates
    (AVL · tax · cert · sanctions · single_source). Any failed criterion blocks
    the PO."""
    return [
        {
            "rule_id": "rule-avl",
            "name": "Approved Vendor List",
            "type": "avl",
            "predicate": "supplier.avl_status == approved (or a logged emergency AVL exception)",
        },
        {
            "rule_id": "rule-tax",
            "name": "Tax registration",
            "type": "tax",
            "predicate": "supplier.tax_id present and valid",
        },
        {
            "rule_id": "rule-cert",
            "name": "Certification valid",
            "type": "cert",
            "predicate": "supplier.cert_status == valid",
        },
        {
            "rule_id": "rule-sanctions",
            "name": "Sanctions screening",
            "type": "sanctions",
            "predicate": "supplier.sanctions_flag == false",
        },
        {
            "rule_id": "rule-single-source",
            "name": "Single-source justified",
            "type": "single_source",
            "predicate": "single-source documented and justified",
        },
    ]


def approval_tier_records() -> list[dict[str, Any]]:
    """Return the Delegation-of-Authority ladder (฿ ceiling + the authorised role
    per tier). The hero PO (฿2.15M > ฿2M) escalates to ผอ.; the calm PO (฿45k)
    sits in tier-1 (หน.จัดซื้อ)."""
    return [
        {
            "tier_id": "tier-1",
            "tier": 1,
            "max_amount": 50_000.0,
            "approver_role": "หน.จัดซื้อ",
        },
        {
            "tier_id": "tier-2",
            "tier": 2,
            "max_amount": 500_000.0,
            "approver_role": "ผจก.จัดซื้อ",
        },
        {
            "tier_id": "tier-3",
            "tier": 3,
            "max_amount": 2_000_000.0,
            "approver_role": "ผจก.โรงงาน",
        },
        {
            "tier_id": "tier-4",
            "tier": 4,
            "max_amount": 1_000_000_000.0,  # no ceiling — the > ฿2M tier
            "approver_role": "ผอ.",
        },
    ]


OBJECT_SOURCES = {
    "Plant": plant_records,
    "Equipment": equipment_records,
    "Part": part_records,
    "Supplier": supplier_records,
    "Quotation": quotation_records,
    "PurchaseOrder": purchase_order_records,
    "ComplianceRule": compliance_rule_records,
    "ApprovalTier": approval_tier_records,
}
