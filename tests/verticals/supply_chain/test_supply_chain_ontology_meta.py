"""Ontology-metadata projection for the supply_chain vertical (PLAN-0013 AC-template).

Asserts the UI-facing ``/meta`` projection the ontology-driven UI consumes —
proving the second vertical exposes the same shape (geo type, status enums,
ref targets, link types) the generic UI binds to, with no UI change.
"""

from __future__ import annotations

from services.engine.ontology_meta import load_ontology_meta


def test_object_types_present() -> None:
    meta = load_ontology_meta("supply_chain")
    assert meta.vertical == "supply_chain"
    assert meta.namespace == "supply_chain"
    names = {t.name for t in meta.object_types}
    assert {"Shipment", "Facility", "OperationalEvent", "Alert", "RecommendedAction"} <= names


def test_title_and_primary_key() -> None:
    meta = load_ontology_meta("supply_chain")
    shipment = next(t for t in meta.object_types if t.name == "Shipment")
    assert shipment.primary_key == "shipment_id"
    assert shipment.title_key == "reference"
    facility = next(t for t in meta.object_types if t.name == "Facility")
    assert facility.primary_key == "facility_id"
    assert facility.title_key == "name"


def test_enums_and_required() -> None:
    meta = load_ontology_meta("supply_chain")
    shipment = next(t for t in meta.object_types if t.name == "Shipment")
    props = {p.name: p for p in shipment.properties}
    assert props["cargo_type"].enum == ["pharma", "produce", "frozen", "biologic"]
    assert props["status"].enum == ["in_transit", "at_facility", "delayed", "held", "delivered"]
    assert props["shipment_id"].required is True
    assert props["payload_kg"].enum is None  # non-enum property


def test_facility_is_geo_bearing() -> None:
    """AC-template: the map's geoTypes heuristic needs a type with lat + lng."""
    meta = load_ontology_meta("supply_chain")
    facility = next(t for t in meta.object_types if t.name == "Facility")
    prop_types = {p.name: p.type for p in facility.properties}
    assert prop_types.get("lat") == "float"
    assert prop_types.get("lng") == "float"


def test_ref_target() -> None:
    meta = load_ontology_meta("supply_chain")
    shipment = next(t for t in meta.object_types if t.name == "Shipment")
    facility_id = next(p for p in shipment.properties if p.name == "facility_id")
    assert facility_id.type == "ref"
    assert facility_id.target == "Facility"


def test_link_types() -> None:
    meta = load_ontology_meta("supply_chain")
    assert any(
        link.from_type == "Shipment" and link.to_type == "Facility" for link in meta.link_types
    )
