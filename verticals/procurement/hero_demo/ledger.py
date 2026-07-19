"""The hero-demo ฿-impact ledger (PLAN-0045 Step 3 / B1).

Computes the Profit-Formula beat — *"governed sourcing turned a ~฿9.8M line-stop into a ~฿1.65M
decision"* — from the C1 dataset columns, Decimal-exact (never ``float`` on money):

* **baseline** = wait for the on-AVL **preferred** supplier (Fastenal, 14-day): downtime
  (``downtime_cost_per_hour_thb`` x lead-days x productive-hours/day) + on-contract part cost
  (``quoted_unit_price_thb`` x qty);
* **governed** = the off-AVL **emergency** decision the demo dramatizes (RapidMRO, 2-day): downtime
  over the short lead + the emergency part cost (the hero PO total);
* **expedite premium** = governed part cost - baseline part cost (฿52,500, the price of speed);
* **avoided downtime** / **net benefit** = the baseline - governed deltas (~฿8.1M).

⚠ **ALL FIGURES DEMO-GRADE / PROVISIONAL** (dossier §10) — the render + the API stamp them so.
``productive_hours_per_day`` is a stated modelling assumption (the CSVs carry cost/hour + lead-days,
not a shift calendar); everything else is a dataset column.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from verticals.procurement.data_adapter.fastenal_csv import FastenalCsvAdapter

_CURRENCY = "THB"
_HERO_PO = "PO-2026-0412"
# Demo modelling assumption (NOT a CSV column): productive hours lost per calendar day of downtime.
_PRODUCTIVE_HOURS_PER_DAY = Decimal(8)


def _sole(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    hits = [row for row in rows if row[key] == value]
    if len(hits) != 1:
        raise ValueError(f"expected exactly one {key}=={value!r}, got {len(hits)}")
    return hits[0]


async def build_hero_impact_ledger(adapter: FastenalCsvAdapter | None = None) -> dict[str, Any]:
    """Compute the baseline → governed ฿-impact ledger for the hero PO, from dataset columns.

    Decimal-exact; deterministic; no LLM / no MS-S1. Every ฿ value is a :class:`~decimal.Decimal`
    (the API serialises them to strings). The baseline path is the on-AVL **preferred** supplier
    for the hero part; the governed path is the hero PO's off-AVL supplier.
    """
    adapter = adapter or FastenalCsvAdapter()
    hero_po = _sole(await adapter.fetch_objects("PurchaseOrder"), "po_id", _HERO_PO)
    part_id: str = hero_po["part_no"]  # PLAN-0083: canonical (was part_id)
    qty: int = hero_po["qty"]
    governed_supplier: str = hero_po["supplier_id"]
    governed_part_cost: Decimal = hero_po["total_thb"]  # SD-4b DEFER: ฿-column stays raw

    # PLAN-0083 (c1 / SD-1 + SD-4a): the adapter serves the canonical type `Equipment` keyed by
    # `equipment_id`; the hero PO carries the canonical `equipment_id` (was `asset_id`).
    asset = _sole(await adapter.fetch_objects("Equipment"), "equipment_id", hero_po["equipment_id"])
    downtime_per_hour: Decimal = asset["downtime_cost_per_hour_thb"]

    links = await adapter.fetch_links("part_suppliable_by_supplier", from_pk=part_id)
    baseline_link = next(link for link in links if link["preferred"])
    governed_link = next(link for link in links if link["to_id"] == governed_supplier)

    baseline_lead: int = baseline_link["lead_time_days"]
    governed_lead: int = governed_link["lead_time_days"]
    baseline_part_cost: Decimal = baseline_link["quoted_unit_price_thb"] * qty

    baseline_downtime = downtime_per_hour * baseline_lead * _PRODUCTIVE_HOURS_PER_DAY
    governed_downtime = downtime_per_hour * governed_lead * _PRODUCTIVE_HOURS_PER_DAY
    baseline_exposure = baseline_downtime + baseline_part_cost
    governed_exposure = governed_downtime + governed_part_cost

    return {
        "provisional": True,
        "currency": _CURRENCY,
        "asset_id": asset["equipment_id"],  # PLAN-0083: ledger output key stays; read canonical
        "part_id": part_id,
        "qty": qty,
        "productive_hours_per_day": _PRODUCTIVE_HOURS_PER_DAY,
        "baseline": {
            "path": "on-AVL wait (preferred supplier)",
            "supplier_id": baseline_link["to_id"],
            "lead_time_days": baseline_lead,
            "downtime_thb": baseline_downtime,
            "part_cost_thb": baseline_part_cost,
            "exposure_thb": baseline_exposure,
        },
        "governed": {
            "path": "off-AVL emergency (governed)",
            "supplier_id": governed_supplier,
            "lead_time_days": governed_lead,
            "downtime_thb": governed_downtime,
            "part_cost_thb": governed_part_cost,
            "exposure_thb": governed_exposure,
        },
        "expedite_premium_thb": governed_part_cost - baseline_part_cost,
        "avoided_downtime_thb": baseline_downtime - governed_downtime,
        "net_benefit_thb": baseline_exposure - governed_exposure,
    }
