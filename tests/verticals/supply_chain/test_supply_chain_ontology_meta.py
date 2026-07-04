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
    # supply-chain-v1 (PLAN-0049 Step 2, G11): `returned` status added.
    assert props["status"].enum == [
        "in_transit",
        "at_facility",
        "delayed",
        "held",
        "delivered",
        "returned",
    ]
    assert props["shipment_id"].required is True
    assert props["payload_kg"].enum is None  # non-enum property


def test_v1_equipment_entity_and_link() -> None:
    """supply-chain-v1 (PLAN-0049 Step 2, G1): a first-class Equipment entity +
    the shipment_uses_equipment link home the previously-homeless reefer fleet."""
    meta = load_ontology_meta("supply_chain")
    equipment = next((t for t in meta.object_types if t.name == "Equipment"), None)
    assert equipment is not None
    props = {p.name: p for p in equipment.properties}
    assert props["equipment_type"].enum == ["reefer_truck", "reefer_container", "data_logger"]
    shipment = next(t for t in meta.object_types if t.name == "Shipment")
    assert any(p.name == "equipment_id" and p.target == "Equipment" for p in shipment.properties)
    assert any(
        link.from_type == "Shipment" and link.to_type == "Equipment" for link in meta.link_types
    )


def test_v1_metric_kinds_and_bindings() -> None:
    """supply-chain-v1 (PLAN-0049 Step 2, G2): OperationalEvent gains temperature
    and battery measured_kinds, each bound one-to-one to its unit (ADR-0021)."""
    meta = load_ontology_meta("supply_chain")
    event = next(t for t in meta.object_types if t.name == "OperationalEvent")
    kinds = {p.name: p for p in event.properties}["measured_kind"].enum
    assert kinds == ["temperature", "battery"]
    bindings = {b.kind: b.unit for b in event.quantity_bindings}
    assert bindings == {"temperature": "celsius", "battery": "percent"}


def test_v1_action_enum_gaps() -> None:
    """supply-chain-v1 (PLAN-0049 Step 2, G11): release/return/adjust_setpoint."""
    meta = load_ontology_meta("supply_chain")
    action = next(t for t in meta.object_types if t.name == "RecommendedAction")
    action_type = {p.name: p for p in action.properties}["action_type"].enum
    assert action_type == [
        "reroute",
        "expedite",
        "hold",
        "inspect",
        "escalate",
        "release",
        "return",
        "adjust_setpoint",
    ]


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
