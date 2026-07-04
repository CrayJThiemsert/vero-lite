"""Unit tests for the ontology-metadata loader (PLAN-0013 Step 1b).

Loads the real energy ontology YAML and asserts the UI-facing projection
(object types, title_key/primary_key, enums, ref targets, link types).
"""

from __future__ import annotations

from pathlib import Path

import pytest

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


# ---------- ADR-0027 R2 / PLAN-0050 Step 2: semantic-enrichment projection (AC-2) ----------

_ENRICHED_ONTOLOGY = """\
version: 1
namespace: enr
object_types:
  Asset:
    primary_key: asset_id
    synonyms:
      th: [sinsap]
      en: [asset, equipment]
    verified_queries:
      - question: How many active assets?
        answer: Count Asset rows where status is active.
    properties:
      asset_id:
        type: string
      status:
        type: enum
        values: [active, retired]
        synonyms:
          en: [state]
        sample_values: [active, retired]
  OperationalEvent:
    primary_key: event_id
    properties:
      event_id:
        type: string
      measured_kind:
        type: enum
        values: [temperature]
    quantity_bindings:
      - kind: temperature
        unit: celsius
        grain: hourly
        join_path: OperationalEvent.asset_id -> Asset.asset_id
"""


def test_enrichment_projection_from_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ADR-0027 R2 (PLAN-0050 Step 2, AC-2): the loader projects the four
    enrichment constructs — typed ``Synonyms`` / ``VerifiedQuery`` (SD-D),
    ``sample_values``, and quantity-binding ``grain`` / ``join_path`` — from an
    enriched ontology YAML."""
    path = tmp_path / "enr_v0.yaml"
    path.write_text(_ENRICHED_ONTOLOGY, encoding="utf-8")
    monkeypatch.setattr("services.engine.ontology_meta.ontology_path", lambda v: path)

    meta = load_ontology_meta("enr")
    asset = next(t for t in meta.object_types if t.name == "Asset")
    # object-type synonyms (typed model, SD-D)
    assert asset.synonyms is not None
    assert asset.synonyms.th == ["sinsap"]
    assert asset.synonyms.en == ["asset", "equipment"]
    # object-type verified_queries (SD-B)
    assert len(asset.verified_queries) == 1
    assert asset.verified_queries[0].question == "How many active assets?"
    assert asset.verified_queries[0].answer.startswith("Count Asset")
    # property synonyms + sample_values (an absent lang projects to [])
    status = next(p for p in asset.properties if p.name == "status")
    assert status.synonyms is not None
    assert status.synonyms.en == ["state"]
    assert status.synonyms.th == []
    assert status.sample_values == ["active", "retired"]
    # quantity-binding grain / join_path (SD-5)
    event = next(t for t in meta.object_types if t.name == "OperationalEvent")
    binding = next(b for b in event.quantity_bindings if b.kind == "temperature")
    assert binding.grain == "hourly"
    assert binding.join_path == "OperationalEvent.asset_id -> Asset.asset_id"


def test_unenriched_ontology_projects_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-2 / D2 backward-compat: an ontology declaring NONE of the four
    enrichment constructs projects every new attribute to its empty/None default.
    Uses a bare fixture so the assertion stays valid as real verticals are
    enriched (energy was the example until PLAN-0050 Step 5 backfilled it)."""
    body = """\
version: 0
namespace: bare
object_types:
  Thing:
    primary_key: thing_id
    properties:
      thing_id:
        type: string
      measured_kind:
        type: enum
        values: [temperature]
    quantity_bindings:
      - kind: temperature
        unit: celsius
"""
    path = tmp_path / "bare_v0.yaml"
    path.write_text(body, encoding="utf-8")
    monkeypatch.setattr("services.engine.ontology_meta.ontology_path", lambda v: path)
    meta = load_ontology_meta("bare")
    for t in meta.object_types:
        assert t.synonyms is None
        assert t.verified_queries == []
        for p in t.properties:
            assert p.synonyms is None
            assert p.sample_values == []
        for b in t.quantity_bindings:
            assert b.grain is None
            assert b.join_path is None
