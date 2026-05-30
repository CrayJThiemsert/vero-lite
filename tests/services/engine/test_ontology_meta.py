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
    assert props["asset_type"].enum == ["battery", "inverter", "meter", "transformer"]
    assert props["asset_id"].required is True
    assert props["capacity_kw"].enum is None  # non-enum property


def test_ref_target() -> None:
    meta = load_ontology_meta("energy")
    asset = next(t for t in meta.object_types if t.name == "Asset")
    site_id = next(p for p in asset.properties if p.name == "site_id")
    assert site_id.type == "ref"
    assert site_id.target == "Site"


def test_link_types() -> None:
    meta = load_ontology_meta("energy")
    assert any(link.from_type == "Asset" and link.to_type == "Site" for link in meta.link_types)
