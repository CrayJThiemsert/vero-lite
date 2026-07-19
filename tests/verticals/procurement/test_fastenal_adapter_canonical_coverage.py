"""PLAN-0083 (c1) — the canonical-source-mapping coverage tripwire (AC-2).

Pins that the ``FastenalCsvAdapter`` emits the CANONICAL ontology vocabulary for every served
procurement type, so a future CSV-column add or a dropped/typo'd rename cannot SILENTLY re-drift
the declared-vs-runtime seam back open. Four checks + a non-vacuity probe:

  (i)   per-type emitted-key SET-EQUALITY against the pinned canonical sets below (a new column or
        a changed rename shifts a set -> RED);
  (ii)  every declared REQUIRED ontology property of each declared type is present in the rows;
  (iii) every ``_COLUMN_RENAMES`` target is a real declared ontology property name (typo guard);
  (iv)  the served object-type keys are canonical (Equipment, never raw Asset — SD-1);
plus a permanent doctored-fixture probe proving the denylist check goes RED on a raw-keyed row.

Deterministic, offline (CLAUDE.md §8 — the offline oracle is the gate; no DB, no MS-S1).
**SD-4b DEFER:** the ฿-columns (``total_thb`` / ``min_thb`` / ``max_thb``) are pinned RAW below —
deliberately not renamed (the governed amount is re-derived, never read from the PO), so a future
rename must consciously update these pins.
"""

from __future__ import annotations

import pytest

from services.engine.ontology_meta import load_ontology_meta
from verticals.procurement.data_adapter.fastenal_csv import (
    _COLUMN_RENAMES,
    _OBJECT_FILES,
    FastenalCsvAdapter,
)

_VERTICAL = "procurement"

# The pinned CANONICAL emitted-key set per served type (raw CSV header + _COLUMN_RENAMES applied).
# SD-4b DEFER: total_thb (PurchaseOrder) + min_thb / max_thb (ApprovalTier) are pinned RAW here.
_CANONICAL_KEYS: dict[str, set[str]] = {
    "Equipment": {
        "equipment_id",
        "name",
        "equipment_type",
        "line_code",
        "site_id",
        "status",
        "downtime_cost_per_hour_thb",
        "criticality",
    },
    "Part": {
        "part_no",
        "name",
        "category",
        "unit",
        "on_contract_unit_price_thb",
        "emergency_expedite_unit_price_thb",
        "criticality",
    },
    "Supplier": {"supplier_id", "name", "avl_status", "region", "on_contract"},
    "PurchaseOrder": {
        "po_id",
        "part_no",
        "supplier_id",
        "equipment_id",
        "qty",
        "unit_price_thb",
        "total_thb",
        "order_type",
        "is_off_avl_override",
        "required_tier_id",
        "requester_role",
        "approver_role",
        "status",
    },
    "ApprovalTier": {"tier_id", "tier_name", "min_thb", "max_thb", "approver_role", "sod_required"},
    "Person": {"person_id", "name", "roles"},
    "OperationalEvent": {
        "event_id",
        "event_type",
        "severity",
        "measured_value",
        "unit",
        "description",
        "occurred_at",
        "equipment_id",
        "site_id",
    },
    "Quotation": {
        "quote_id",
        "part_no",
        "supplier_id",
        "price",
        "currency",
        "lead_time",
        "warranty",
        "on_contract",
    },
}

# The raw Fastenal names the adapter renames away — none may reappear in an emitted object row
# (the core anti-re-drift denylist; dropping a _COLUMN_RENAMES entry brings one back -> RED).
_RENAMED_AWAY_RAW: frozenset[str] = frozenset(
    raw for renames in _COLUMN_RENAMES.values() for raw in renames
)

# Required ontology properties per DECLARED procurement type. Person is shared/promoted (PLAN-0082)
# and NOT declared in procurement_v0.yaml, so it is covered by the set-equality pin only.
_REQUIRED_BY_TYPE: dict[str, set[str]] = {
    "Equipment": {"equipment_id", "name", "site_id"},
    "Part": {"part_no", "name"},
    "Supplier": {"supplier_id", "name"},
    "PurchaseOrder": {"po_id", "part_no", "supplier_id"},
    "ApprovalTier": {"tier_id"},
    "OperationalEvent": {"event_id", "occurred_at"},
}


async def _emitted_keys(object_type: str) -> set[str]:
    """The emitted-key set of ``object_type``'s rows (asserts non-empty + homogeneous)."""
    rows = await FastenalCsvAdapter().fetch_objects(object_type)
    assert rows, f"{object_type} must emit rows"
    keys = set(rows[0].keys())
    assert all(set(row.keys()) == keys for row in rows), f"{object_type} rows must be homogeneous"
    return keys


def _declared_property_names() -> set[str]:
    meta = load_ontology_meta(_VERTICAL)
    return {prop.name for obj_type in meta.object_types for prop in obj_type.properties}


@pytest.mark.parametrize("object_type", sorted(_CANONICAL_KEYS))
async def test_emitted_keys_match_the_pinned_canonical_set(object_type: str) -> None:
    """(i) SET-EQUALITY: the adapter emits exactly the pinned canonical key set for each type."""
    assert await _emitted_keys(object_type) == _CANONICAL_KEYS[object_type]


async def test_no_renamed_away_raw_name_is_emitted() -> None:
    """(i) non-vacuity core: no renamed-away raw Fastenal name appears in any emitted object row."""
    for object_type in _OBJECT_FILES:
        leaked = await _emitted_keys(object_type) & _RENAMED_AWAY_RAW
        assert not leaked, f"{object_type} leaked raw name(s) {leaked} — a rename was dropped"


@pytest.mark.parametrize("object_type", sorted(_REQUIRED_BY_TYPE))
async def test_declared_required_properties_are_present(object_type: str) -> None:
    """(ii) every declared REQUIRED ontology property is present in the emitted rows."""
    missing = _REQUIRED_BY_TYPE[object_type] - await _emitted_keys(object_type)
    assert not missing, f"{object_type} is missing required declared prop(s) {missing}"


def test_every_rename_target_is_a_declared_ontology_property() -> None:
    """(iii) typo guard: each ``_COLUMN_RENAMES`` target is a real declared ontology property name.

    Validated against the UNION of all declared names (SD-4a: ``PurchaseOrder.asset_id`` maps to
    ``equipment_id`` — the canonical Equipment-ref vocabulary declared on Equipment /
    OperationalEvent, not on PurchaseOrder itself), so a typo'd target still fails while the SD-4a
    reuse is allowed.
    """
    declared = _declared_property_names()
    targets = {tgt for renames in _COLUMN_RENAMES.values() for tgt in renames.values()}
    unknown = targets - declared
    assert not unknown, f"rename target(s) not a declared ontology property: {unknown}"


def test_type_keys_are_canonical() -> None:
    """(iv) SD-1: the served object-type keys are canonical — Equipment, never the raw Asset."""
    assert "Equipment" in _OBJECT_FILES
    assert "Asset" not in _OBJECT_FILES


def test_sd4b_deferred_baht_columns_stay_raw() -> None:
    """SD-4b DEFER pin: the ฿-columns are deliberately NOT renamed (re-derived, never read from the
    PO). This pins the decision so a future rename must consciously update the canonical pins."""
    assert "total_thb" in _CANONICAL_KEYS["PurchaseOrder"]
    assert {"min_thb", "max_thb"} <= _CANONICAL_KEYS["ApprovalTier"]
    all_targets = {tgt for renames in _COLUMN_RENAMES.values() for tgt in renames}
    assert not ({"total_thb", "min_thb", "max_thb"} & all_targets), "฿-columns must stay raw"


def _leaks_raw(rows: list[dict[str, object]]) -> set[str]:
    """The coverage check under test: the renamed-away raw names present across ``rows``."""
    return {key for row in rows for key in row} & _RENAMED_AWAY_RAW


def test_probe_denylist_check_is_non_vacuous() -> None:
    """A doctored fixture proving the denylist check WOULD fire: a raw-keyed row leaks, a
    canonical-keyed row does not (keeps the ``no-raw-name-emitted`` test honest)."""
    doctored_raw = [{"asset_id": "AST-X", "part_id": "PRT-X", "name": "n"}]
    assert _leaks_raw(doctored_raw) == {"asset_id", "part_id"}  # RED path proven
    canonical = [{"equipment_id": "AST-X", "part_no": "PRT-X", "name": "n"}]
    assert _leaks_raw(canonical) == set()  # GREEN path
