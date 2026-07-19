"""PLAN-0045 Step 1 / C1 — the CSV-backed FastenalCsvAdapter (hero-demo dataset).

Offline + deterministic (CLAUDE.md §8 — the offline oracle is the gate). Covers:

* protocol conformance to the ``@runtime_checkable`` ``DataAdapter`` (AC-1),
* the round-trip of the canonical demo rows — the hero PO ``PO-2026-0412`` (฿288,000,
  qty 3, off-AVL override) resolving to ``TIER-CTRL`` / ``CONTROLLER``, and the contrast
  PO ``PO-2026-0411`` (฿99,000 → ``TIER-MGR``) (AC-1),
* Decimal-safe THB parsing (never ``float`` on a ฿ authority threshold),
* the 2 explicit link files + the 4 inline-FK links synthesised from
  ``purchase_order.csv`` (dataset §"ingestion mapping"),
* the empty event stream (v1 CSV snapshot),
* explicit registration that does not auto-clobber the synthetic adapter, and
* the **zero-core-edit** guard (AC-2): the adapter is a pure ``verticals/`` plugin —
  it never imports ``services.engine.procedures`` / ``services.db`` core.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from services.engine.data_adapter import DataAdapter
from services.engine.registry import registry
from verticals.procurement.data_adapter.fastenal_csv import (
    FastenalCsvAdapter,
    register_fastenal_csv_adapter,
)

_ADAPTER_SRC = Path("verticals/procurement/data_adapter/fastenal_csv.py")


def _by_pk(rows: list[dict[str, object]], key: str, value: str) -> dict[str, object]:
    """Return the single row whose ``key`` == ``value`` (asserts exactly one)."""
    matches = [row for row in rows if row[key] == value]
    assert len(matches) == 1, f"expected exactly one {key}=={value!r}, got {len(matches)}"
    return matches[0]


# --------------------------------------------------------------------------- #
# Protocol conformance + basic surface
# --------------------------------------------------------------------------- #


def test_adapter_conforms_to_protocol() -> None:
    assert isinstance(FastenalCsvAdapter(), DataAdapter)


async def test_health_check_reports_ok() -> None:
    result = await FastenalCsvAdapter().health_check()
    assert result["status"] == "ok"
    assert result["vertical"] == "procurement"
    assert result["csv_backed"] is True
    assert result["object_counts"]["PurchaseOrder"] == 4


async def test_fetch_objects_serves_the_five_types_plus_person() -> None:
    adapter = FastenalCsvAdapter()
    for object_type in ("Equipment", "Part", "Supplier", "PurchaseOrder", "ApprovalTier", "Person"):
        objects = await adapter.fetch_objects(object_type)
        assert objects, f"{object_type} should be non-empty"
        assert all(isinstance(obj, dict) for obj in objects)


async def test_fetch_objects_unknown_type_is_empty() -> None:
    assert await FastenalCsvAdapter().fetch_objects("Nonexistent") == []


async def test_fetch_objects_respects_limit() -> None:
    objects = await FastenalCsvAdapter().fetch_objects("Equipment", limit=2)
    assert len(objects) == 2


# --------------------------------------------------------------------------- #
# AC-1 — the canonical hero rows round-trip
# --------------------------------------------------------------------------- #


async def test_hero_purchase_order_round_trips() -> None:
    adapter = FastenalCsvAdapter()
    pos = await adapter.fetch_objects("PurchaseOrder")
    hero = _by_pk(pos, "po_id", "PO-2026-0412")
    assert hero["total_thb"] == 288000
    assert hero["qty"] == 3
    assert hero["required_tier_id"] == "TIER-CTRL"
    assert hero["is_off_avl_override"] is True
    assert hero["requester_role"] == "MAINT_PLANNER"
    assert hero["approver_role"] == "CONTROLLER"


async def test_hero_asset_and_part_present() -> None:
    adapter = FastenalCsvAdapter()
    assets = await adapter.fetch_objects("Equipment")
    down = _by_pk(assets, "equipment_id", "AST-CNC-014")
    assert down["status"] == "DOWN"
    assert down["downtime_cost_per_hour_thb"] == 85000
    parts = await adapter.fetch_objects("Part")
    _by_pk(parts, "part_no", "PRT-SPN-700")


async def test_controller_tier_band_round_trips() -> None:
    tiers = await FastenalCsvAdapter().fetch_objects("ApprovalTier")
    ctrl = _by_pk(tiers, "tier_id", "TIER-CTRL")
    assert ctrl["min_thb"] == 200001
    assert ctrl["max_thb"] == 1000000
    assert ctrl["approver_role"] == "CONTROLLER"
    assert ctrl["sod_required"] is True


async def test_contrast_po_stays_at_manager_tier() -> None:
    """AC-7 fixture: the ฿99,000 emergency PO is authored TIER-MGR — no Controller escalation."""
    pos = await FastenalCsvAdapter().fetch_objects("PurchaseOrder")
    contrast = _by_pk(pos, "po_id", "PO-2026-0411")
    assert contrast["required_tier_id"] == "TIER-MGR"
    assert contrast["total_thb"] == 99000


async def test_person_roles_parse_pipe_separated() -> None:
    people = await FastenalCsvAdapter().fetch_objects("Person")
    planner = _by_pk(people, "person_id", "req-maint-planner")
    assert planner["roles"] == ["requester", "MAINT_PLANNER"]
    controller = _by_pk(people, "person_id", "appr-controller")
    assert controller["roles"] == ["approver", "CONTROLLER"]


# --------------------------------------------------------------------------- #
# Decimal-safe THB (never float on a ฿ authority threshold)
# --------------------------------------------------------------------------- #


async def test_money_columns_are_decimal() -> None:
    adapter = FastenalCsvAdapter()
    hero = _by_pk(await adapter.fetch_objects("PurchaseOrder"), "po_id", "PO-2026-0412")
    assert isinstance(hero["total_thb"], Decimal)
    assert isinstance(hero["unit_price_thb"], Decimal)
    ctrl = _by_pk(await adapter.fetch_objects("ApprovalTier"), "tier_id", "TIER-CTRL")
    assert isinstance(ctrl["min_thb"], Decimal)
    assert isinstance(ctrl["max_thb"], Decimal)


# --------------------------------------------------------------------------- #
# OperationalEvent + Quotation (the C-full run inputs)
# --------------------------------------------------------------------------- #


async def test_operational_event_failure_present() -> None:
    events = await FastenalCsvAdapter().fetch_objects("OperationalEvent")
    fail = _by_pk(events, "event_id", "EVT-CNC-014-FAIL")
    assert fail["event_type"] == "failure"
    assert fail["equipment_id"] == "AST-CNC-014"  # PLAN-0083: canonical (was asset_id)
    assert isinstance(fail["measured_value"], float)
    assert fail["measured_value"] == 0.92


async def test_quotation_offavl_is_the_hero_price() -> None:
    quotes = await FastenalCsvAdapter().fetch_objects("Quotation")
    rapid = _by_pk(quotes, "quote_id", "QT-SPN-RAPIDMRO")
    assert rapid["supplier_id"] == "SUP-RAPIDMRO"
    assert rapid["price"] == Decimal("96000")  # PLAN-0083: canonical (was price_thb)
    assert isinstance(rapid["price"], Decimal)
    assert rapid["lead_time"] == 2  # PLAN-0083: canonical (was lead_time_days)
    assert rapid["on_contract"] is False


# --------------------------------------------------------------------------- #
# fetch_links — 2 explicit files + 4 inline-FK from purchase_order.csv
# --------------------------------------------------------------------------- #


async def test_explicit_asset_uses_part_link() -> None:
    links = await FastenalCsvAdapter().fetch_links("asset_uses_part", from_pk="AST-CNC-014")
    to_ids = {link["to_id"] for link in links}
    assert {"PRT-SPN-700", "PRT-CTR-880"} <= to_ids
    spindle = _by_pk(
        [link for link in links if link["to_id"] == "PRT-SPN-700"], "to_id", "PRT-SPN-700"
    )
    assert spindle["qty_per_asset"] == 2


async def test_explicit_part_suppliable_by_supplier_link_is_decimal() -> None:
    links = await FastenalCsvAdapter().fetch_links(
        "part_suppliable_by_supplier", from_pk="PRT-SPN-700", to_pk="SUP-RAPIDMRO"
    )
    assert len(links) == 1
    offavl = links[0]
    assert offavl["lead_time_days"] == 2
    assert offavl["quoted_unit_price_thb"] == Decimal("96000")
    assert isinstance(offavl["quoted_unit_price_thb"], Decimal)
    assert offavl["preferred"] is False


async def test_four_inline_fk_links_from_purchase_order() -> None:
    adapter = FastenalCsvAdapter()
    expected = {
        "po_references_part": "PRT-SPN-700",
        "po_sourced_from_supplier": "SUP-RAPIDMRO",
        "po_for_asset": "AST-CNC-014",
        "po_requires_tier": "TIER-CTRL",
    }
    for link_type, to_id in expected.items():
        links = await adapter.fetch_links(link_type, from_pk="PO-2026-0412")
        assert len(links) == 1, f"{link_type} should yield exactly the hero PO row"
        assert links[0]["to_id"] == to_id
        assert links[0]["from_id"] == "PO-2026-0412"


async def test_fetch_links_unknown_type_is_empty() -> None:
    assert await FastenalCsvAdapter().fetch_links("nonexistent_link") == []


async def test_stream_events_is_empty_in_v1() -> None:
    adapter = FastenalCsvAdapter()
    events = [event async for event in adapter.stream_events("failure")]
    assert events == []


# --------------------------------------------------------------------------- #
# Registration (explicit; does not auto-clobber the synthetic adapter)
# --------------------------------------------------------------------------- #


def test_register_fastenal_csv_adapter_registers_on_registry() -> None:
    register_fastenal_csv_adapter()
    assert isinstance(registry.get_adapter("procurement"), FastenalCsvAdapter)


# --------------------------------------------------------------------------- #
# AC-2 — zero-core-edit: the adapter is a pure verticals/ plugin
# --------------------------------------------------------------------------- #


def test_adapter_does_not_import_engine_core() -> None:
    """AC-2 proxy: the CSV adapter is a data-layer plugin — it never reaches into the engine
    core (``services.engine.procedures`` / ``services.db``). Its only ``services`` dependency is
    the sanctioned registry seam. (The git-diff zero-core-edit check runs at the offline gate.)"""
    source = _ADAPTER_SRC.read_text(encoding="utf-8")
    assert "services.engine.procedures" not in source
    assert "services.db" not in source
    assert "from services.engine.registry import registry" in source
