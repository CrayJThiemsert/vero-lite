"""Unit tests for the ontology-metadata loader (PLAN-0013 Step 1b).

Loads the real energy ontology YAML and asserts the UI-facing projection
(object types, title_key/primary_key, enums, ref targets, link types).
"""

from __future__ import annotations

from services.engine.ontology_meta import load_ontology_meta


def test_object_types_present() -> None:
    meta = load_ontology_meta("energy")
    assert meta.vertical == "energy"
    assert meta.namespace == "energy"
    names = {t.name for t in meta.object_types}
    assert {"Asset", "Site", "OperationalEvent", "Alert", "RecommendedAction"} <= names


def test_title_and_primary_key() -> None:
    meta = load_ontology_meta("energy")
    asset = next(t for t in meta.object_types if t.name == "Asset")
    assert asset.primary_key == "asset_id"
    assert asset.title_key == "name"


def test_enums_and_required() -> None:
    meta = load_ontology_meta("energy")
    asset = next(t for t in meta.object_types if t.name == "Asset")
    props = {p.name: p for p in asset.properties}
    # energy-v1 (PLAN-0049 Step 1, F9): distribution-utility asset types added.
    assert props["asset_type"].enum == [
        "battery",
        "inverter",
        "meter",
        "transformer",
        "feeder",
        "cap_bank",
        "gas_engine",
    ]
    assert props["asset_id"].required is True
    assert props["capacity_kw"].enum is None  # non-enum property
    assert props["rated_current_a"].enum is None  # non-enum float (SD-6)


def test_energy_v1_metric_kinds_and_bindings() -> None:
    """energy-v1 (PLAN-0049 Step 1, F9): OperationalEvent gains current/voltage
    measured_kinds, each bound one-to-one to its coherent unit (ADR-0021)."""
    meta = load_ontology_meta("energy")
    event = next(t for t in meta.object_types if t.name == "OperationalEvent")
    kinds = {p.name: p for p in event.properties}["measured_kind"].enum
    assert kinds == ["temperature", "frequency", "current", "voltage"]
    bindings = {b.kind: b.unit for b in event.quantity_bindings}
    assert bindings == {
        "temperature": "celsius",
        "frequency": "hz",
        "current": "ampere",
        "voltage": "kilovolt",
    }


def test_ref_target() -> None:
    meta = load_ontology_meta("energy")
    asset = next(t for t in meta.object_types if t.name == "Asset")
    site_id = next(p for p in asset.properties if p.name == "site_id")
    assert site_id.type == "ref"
    assert site_id.target == "Site"


def test_link_types() -> None:
    meta = load_ontology_meta("energy")
    assert any(link.from_type == "Asset" and link.to_type == "Site" for link in meta.link_types)
