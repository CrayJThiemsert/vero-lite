"""Procurement vertical — CSV-backed DataAdapter for the hero-demo (PLAN-0045 Step 1 / C1).

A **real** ``DataAdapter`` (ADR-007 D1) alongside the synthetic one, serving the canonical
Fastenal hero-demo dataset (``verticals/procurement/data/hero/*.csv``) as raw object + link
dicts. It exists to make the "Foundry-analog" beat of the hero demo tangible — *legacy CSV
export → ontology objects the governance run consumes* — proving a new data source is "just an
adapter", not an engine rebuild (the ADR-007 protocol is already generic).

Design (PLAN-0045 SD / dossier §9):

* **Zero ``services/`` core edit** (AC-2 / ADR-0023 CQ-1): this is a per-vertical adapter under
  ``verticals/``; registration is the explicit conventional ``register_fastenal_csv_adapter``.
  It is **NOT** the vertical's discovery entry point — ``discover_and_register`` only invokes
  ``register_procurement_adapter`` (the synthetic adapter) for the ``procurement`` namespace, so
  this CSV adapter never auto-clobbers it. The hero-demo path instantiates it explicitly.
* **Decimal-safe THB** (AC-1): every money column is parsed to :class:`~decimal.Decimal` (never
  ``float``) so the DOA-tier resolution + the ฿-impact ledger stay exact on an authority
  threshold (mirrors the ``doa_tier`` executor's Decimal discipline, ADR-0026).
* **Canonical ontology vocabulary** (AC-1; PLAN-0083 c1): ``fetch_objects`` serves the canonical
  OCT type + property names the ontology declares (``Equipment`` / ``Part`` / ``Supplier`` /
  ``PurchaseOrder`` / ``ApprovalTier`` / ``Person``), translating the raw Fastenal CSV column
  names via ``_COLUMN_RENAMES`` — the adapter is the per-vertical source-diversity-absorbing
  layer (ADR-016: "the mapping layer absorbs source diversity; connectors-in-the-procedure OUT").
  ``fetch_links`` returns the 2 explicit link files **plus** the 4 inline-FK links synthesised
  from ``purchase_order.csv`` (dataset §"ingestion mapping"), addressing raw CSV columns
  positionally — the link paths stay raw (SD-2).
* **No event stream** (v1): ``stream_events`` is an empty async iterator — the CSV demo dataset
  is a static snapshot.

⚠ **ALL NUMBERS ARE DEMO-GRADE / PROVISIONAL** — plausible-but-impressive estimates for a
stakeholder demo, **NOT** real Fastenal data (dossier §10; the ledger + render label them so).
"""

from __future__ import annotations

import csv
from collections.abc import AsyncIterator, Callable
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from services.engine.registry import registry

_VERTICAL = "procurement"
_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "hero"

# --------------------------------------------------------------------------- #
# Per-column coercions — money -> Decimal (exact), never float on a ฿ threshold
# --------------------------------------------------------------------------- #

_Coerce = Callable[[str], Any]


def _dec(value: str) -> Decimal:
    """A THB money column -> exact ``Decimal`` (no binary-float rounding)."""
    return Decimal(value)


def _int(value: str) -> int:
    return int(value)


def _float(value: str) -> float:
    """A non-money numeric column (e.g. a criticality reading) -> ``float``."""
    return float(value)


def _bool(value: str) -> bool:
    """A CSV boolean cell (``true`` / ``false``) -> ``bool``."""
    return value.strip().lower() == "true"


def _roles(value: str) -> list[str]:
    """A ``|``-separated principal-roles cell -> ``list[str]`` (comma is the CSV delimiter)."""
    return [role for role in value.split("|") if role]


# object_type -> (csv filename, {column: coercion}); unlisted columns stay ``str``.
_OBJECT_FILES: dict[str, tuple[str, dict[str, _Coerce]]] = {
    # Plant: the geo-bearing map anchor (PLAN-0084 SD-F — this adapter is now the
    # PRIMARY procurement adapter, so it must serve the map's geo type; its plant_id
    # matches the asset/event rows' site refs, canonical `site_id` post-rename).
    "Plant": ("plant.csv", {"lat": _float, "lng": _float}),
    "Equipment": ("asset.csv", {"downtime_cost_per_hour_thb": _dec}),
    "Part": (
        "part.csv",
        # stock_qty/reorder_point: the calm-path low-stock fields (PLAN-0084 SD-F —
        # the declared read_stock -> judge_stock chain now runs over THIS adapter).
        {
            "on_contract_unit_price_thb": _dec,
            "emergency_expedite_unit_price_thb": _dec,
            "stock_qty": _int,
            "reorder_point": _int,
        },
    ),
    "Supplier": ("supplier.csv", {"on_contract": _bool}),
    "PurchaseOrder": (
        "purchase_order.csv",
        {"qty": _int, "unit_price_thb": _dec, "total_thb": _dec, "is_off_avl_override": _bool},
    ),
    "ApprovalTier": (
        "approval_tier.csv",
        {"min_thb": _dec, "max_thb": _dec, "sod_required": _bool},
    ),
    "Person": ("person.csv", {"roles": _roles}),
    "OperationalEvent": ("operational_event.csv", {"measured_value": _float}),
    "Quotation": (
        "quotation.csv",
        {"price_thb": _dec, "lead_time_days": _int, "on_contract": _bool},
    ),
}

# object_type -> {raw CSV column -> canonical ontology property}. PLAN-0083 (c1): the adapter is
# the per-vertical source-diversity-absorbing layer (ADR-016 — "the mapping layer absorbs source
# diversity; connectors-in-the-procedure OUT"), so it translates the raw Fastenal CSV column names
# to the canonical OCT names the ontology deliberately adopted (procurement_v0.yaml:25 — "mirror
# aquaculture, Asset->Equipment, Site->Plant"). Applied on the ``fetch_objects`` path ONLY (SD-2 =
# (b)); the coercion keys above stay raw (they are applied first, keyed to the CSV) and the link
# paths address raw CSV columns positionally, so both are unaffected. The ฿-columns (``total_thb`` /
# ``max_thb`` / ``min_thb``) are DELIBERATELY not renamed (SD-4b DEFER): the governed amount is
# re-derived, never read from the PO, so renaming them buys no generic-join value and would churn
# the box-4 provenance surface — they are pinned raw in the canonical-coverage tripwire.
_COLUMN_RENAMES: dict[str, dict[str, str]] = {
    "Equipment": {"asset_id": "equipment_id", "asset_type": "equipment_type", "site": "site_id"},
    "Part": {"part_id": "part_no"},
    "PurchaseOrder": {"part_id": "part_no", "asset_id": "equipment_id"},  # SD-4a
    "OperationalEvent": {"asset_id": "equipment_id", "site": "site_id"},
    "Quotation": {"part_id": "part_no", "price_thb": "price", "lead_time_days": "lead_time"},
}

# Explicit link files: link_type -> (filename, from_col, to_col, {prop_col: coercion}).
_EXPLICIT_LINKS: dict[str, tuple[str, str, str, dict[str, _Coerce]]] = {
    "asset_uses_part": ("link_asset_uses_part.csv", "asset_id", "part_id", {"qty_per_asset": _int}),
    "part_suppliable_by_supplier": (
        "link_part_suppliable_by_supplier.csv",
        "part_id",
        "supplier_id",
        {"lead_time_days": _int, "quoted_unit_price_thb": _dec, "preferred": _bool},
    ),
}

# Inline-FK links synthesised from purchase_order.csv: link_type -> the FK column (to_id).
# from_id is always the po_id (dataset §"ingestion mapping").
_PO_INLINE_LINKS: dict[str, str] = {
    "po_references_part": "part_id",
    "po_sourced_from_supplier": "supplier_id",
    "po_for_asset": "asset_id",
    "po_requires_tier": "required_tier_id",
}


def _read_rows(filename: str, coercions: dict[str, _Coerce]) -> list[dict[str, Any]]:
    """Read ``data/hero/<filename>`` and coerce the mapped columns (unlisted -> ``str``)."""
    path = _DATA_DIR / filename
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows: list[dict[str, Any]] = []
        for raw in reader:
            row: dict[str, Any] = {}
            for column, cell in raw.items():
                coerce = coercions.get(column)
                row[column] = coerce(cell) if coerce is not None else cell
            rows.append(row)
        return rows


class FastenalCsvAdapter:
    """A CSV-backed :class:`~services.engine.data_adapter.DataAdapter` for the procurement
    hero demo (PLAN-0045 C1). Conforms structurally to the ``@runtime_checkable`` protocol;
    deterministic + no external I/O beyond reading the committed demo CSVs."""

    vertical_name = _VERTICAL

    async def fetch_objects(
        self,
        object_type: str,
        filter_expr: str | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Return the demo object dicts for ``object_type`` (unknown -> empty).

        ``filter_expr`` is accepted for protocol conformance but not applied (the demo
        dataset is small + read whole); ``limit`` caps the returned rows.
        """
        spec = _OBJECT_FILES.get(object_type)
        if spec is None:
            return []
        filename, coercions = spec
        rows = _read_rows(filename, coercions)[:limit]
        renames = _COLUMN_RENAMES.get(object_type)
        if renames:
            rows = [{renames.get(col, col): val for col, val in row.items()} for row in rows]
        return rows

    async def fetch_links(
        self,
        link_type: str,
        from_pk: str | None = None,
        to_pk: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return relationship dicts (``from_id`` / ``to_id`` / props) for ``link_type``.

        The 2 explicit link files plus the 4 inline-FK links synthesised from
        ``purchase_order.csv`` (``po_references_part`` / ``po_sourced_from_supplier`` /
        ``po_for_asset`` / ``po_requires_tier``). ``from_pk`` / ``to_pk`` filter the endpoints
        when supplied; an unknown ``link_type`` returns empty.
        """
        links = self._explicit_links(link_type)
        if links is None:
            links = self._po_inline_links(link_type)
        if links is None:
            return []
        if from_pk is not None:
            links = [link for link in links if link["from_id"] == from_pk]
        if to_pk is not None:
            links = [link for link in links if link["to_id"] == to_pk]
        return links

    def _explicit_links(self, link_type: str) -> list[dict[str, Any]] | None:
        spec = _EXPLICIT_LINKS.get(link_type)
        if spec is None:
            return None
        filename, from_col, to_col, prop_coercions = spec
        rows = _read_rows(filename, prop_coercions)
        links: list[dict[str, Any]] = []
        for row in rows:
            link = {"from_id": row[from_col], "to_id": row[to_col]}
            if "link_id" in row:
                link["link_id"] = row["link_id"]
            for prop in prop_coercions:
                link[prop] = row[prop]
            links.append(link)
        return links

    def _po_inline_links(self, link_type: str) -> list[dict[str, Any]] | None:
        to_col = _PO_INLINE_LINKS.get(link_type)
        if to_col is None:
            return None
        rows = _read_rows("purchase_order.csv", {})
        return [{"from_id": row["po_id"], "to_id": row[to_col]} for row in rows]

    async def stream_events(
        self,
        event_type: str,
        since: datetime | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """The CSV demo dataset ships no OperationalEvent stream (v1) — an empty async iterator."""
        empty: list[dict[str, Any]] = []
        for event in empty:
            yield event

    async def health_check(self) -> dict[str, Any]:
        """Report adapter status + the demo record counts (per object type)."""
        return {
            "status": "ok",
            "vertical": self.vertical_name,
            "csv_backed": True,
            "data_dir": str(_DATA_DIR),
            "object_counts": {
                name: len(_read_rows(filename, coercions))
                for name, (filename, coercions) in _OBJECT_FILES.items()
            },
        }


def register_fastenal_csv_adapter() -> FastenalCsvAdapter:
    """Register a fresh :class:`FastenalCsvAdapter` on the process-wide registry.

    Explicit registration (ADR-0023 / CQ-1) — NOT the ``procurement`` discovery entry point
    (that is ``register_procurement_adapter``), so this never auto-clobbers the synthetic
    adapter. Raises ``RegistryError`` if a ``procurement`` adapter is already registered
    (register the CSV adapter on a fresh / reset registry — e.g. the hero-demo path or a test).
    """
    adapter = FastenalCsvAdapter()
    registry.register_adapter(adapter)
    return adapter
