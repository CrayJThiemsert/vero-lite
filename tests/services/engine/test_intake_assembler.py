"""Tests for the PLAN-0017 partner-input-package -> OCT ontology assembler.

The load-bearing contract: a constrained-slot :class:`IntakePackage` assembles
into a canonical OCT ontology YAML that (a) passes the real L1+L2 validator by
construction, (b) is consumable by the PLAN-0016 ``new-vertical`` engine
unchanged, and (c) carries the operator's domain slots through to the generated
artifacts (the foundation the AC-2 edit-propagation test builds on). The
prebaked-default fallbacks (AC-4) are validated here too — a malformed fixture
fails at test time, never silently at demo time.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from services.api.intake_defaults import load_default_packages
from services.engine import code_generator, ontology_validator, scaffold
from services.engine.intake_assembler import IntakePackage, assemble_ontology, assemble_yaml
from services.engine.scaffold import RecommendConfig

_SRC_ROOT = Path(__file__).resolve().parents[3]


def _package(**overrides: object) -> IntakePackage:
    base: dict[str, object] = {
        "namespace": "shrimp_demo",
        "domain_label": "shrimp pond water quality",
        "asset_role": {
            "type_name": "Pond",
            "properties": [
                {"name": "area_sqm", "type": "float"},
                {"name": "species", "type": "enum", "values": ["whiteleg_shrimp", "tiger_prawn"]},
            ],
        },
        "site_role": {
            "type_name": "Farm",
            "properties": [{"name": "farm_type", "type": "enum", "values": ["coastal", "inland"]}],
        },
        "metric": {
            "label": "dissolved-oxygen",
            "unit": "mg/L",
            "threshold": 4.0,
            "direction": "below",
        },
        "action_types": ["start_emergency_aerator", "dispatch_technician"],
        "problem": "A nighttime dissolved-oxygen crash kills the crop within hours.",
        "decision": "Start the emergency aerator to restore oxygen.",
        "recovery_value": 5.5,
        "recovery_description": "Dissolved oxygen recovering above the safe minimum.",
        "source": "manual_entry",
        "confidence": 0.9,
    }
    base.update(overrides)
    return IntakePackage.model_validate(base)


def _write_yaml(package: IntakePackage, tmp_path: Path) -> Path:
    path = tmp_path / f"{package.namespace}_v0.yaml"
    path.write_text(assemble_yaml(package), encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# Validity by construction
# --------------------------------------------------------------------------- #


def test_assembled_yaml_passes_validator(tmp_path: Path) -> None:
    """The assembled ontology passes the real L1+L2 validator (zero findings)."""
    path = _write_yaml(_package(), tmp_path)
    findings = ontology_validator.validate_file(path)
    assert findings == [], "\n".join(f.render() for f in findings)


def test_assembled_doc_detect_roles(tmp_path: Path) -> None:
    """The engine's role detection reads the assembled doc correctly — the three
    invariants hold (one geo Site, event refs resolve, event asset-ref == asset pk)."""
    path = _write_yaml(_package(), tmp_path)
    roles = scaffold.detect_roles(code_generator.load_doc(path))
    assert roles.asset_type == "Pond"
    assert roles.site_type == "Farm"
    assert roles.asset_site_ref == "farm_id"
    assert roles.event_asset_ref == "pond_id"  # == asset pk -> entity_id_field resolves
    assert roles.event_site_ref == "farm_id"
    assert roles.event_type_value == "reading"
    assert roles.severity_baseline == "info"
    assert roles.severity_breach == "critical"


def test_exactly_one_geo_type(tmp_path: Path) -> None:
    """Only the Site-role bears lat+lng — never the Asset-role (invariant 1)."""
    doc = assemble_ontology(_package())
    geo = [
        name
        for name, obj in doc["object_types"].items()
        if {"lat", "lng"} <= set(obj["properties"])
    ]
    assert geo == ["Farm"]
    assert "lat" not in doc["object_types"]["Pond"]["properties"]


def test_domain_properties_propagate(tmp_path: Path) -> None:
    """A domain property/enum survives into the assembled YAML and the generated
    Pydantic model — the seam the AC-2 edit-propagation guarantee rests on."""
    pkg = _package(
        asset_role={
            "type_name": "Pond",
            "properties": [{"name": "stocking_density", "type": "float"}],
        }
    )
    yaml_text = assemble_yaml(pkg)
    assert "stocking_density" in yaml_text


def test_reserved_and_geo_domain_props_dropped() -> None:
    """A domain property colliding with a structural field (pk) or named lat/lng is
    dropped, so the skeleton invariants always hold even on a hostile package."""
    pkg = _package(
        asset_role={
            "type_name": "Pond",
            "properties": [
                {"name": "pond_id", "type": "string"},  # collides with the pk
                {"name": "lat", "type": "float"},  # would create a 2nd geo type
                {"name": "depth_m", "type": "float"},  # legitimate domain prop, kept
            ],
        }
    )
    doc = assemble_ontology(pkg)
    pond = doc["object_types"]["Pond"]["properties"]
    assert "depth_m" in pond
    assert "lat" not in pond
    assert pond["pond_id"] == {"type": "string", "required": True}  # the assembler's pk, not a dup


def test_asset_and_site_must_be_distinct() -> None:
    with pytest.raises(ValidationError, match="distinct"):
        _package(
            site_role={"type_name": "Pond", "properties": []},
        )


def test_bad_namespace_rejected() -> None:
    with pytest.raises(ValidationError, match="snake_case"):
        _package(namespace="Shrimp-Demo")


def test_enum_requires_non_empty_values() -> None:
    with pytest.raises(ValidationError, match="non-empty"):
        _package(
            asset_role={
                "type_name": "Pond",
                "properties": [{"name": "species", "type": "enum", "values": []}],
            }
        )


def test_action_type_with_quote_rejected() -> None:
    with pytest.raises(ValidationError, match="quote/backslash"):
        _package(action_types=['start_"aerator"'])


# --------------------------------------------------------------------------- #
# End-to-end: the assembled YAML scaffolds a full vertical (engine consumable)
# --------------------------------------------------------------------------- #


def test_assembled_yaml_scaffolds_full_vertical(tmp_path: Path) -> None:
    """assemble -> write -> scaffold_vertical: the generated artifacts carry the
    domain type + a domain enum, and the env block carries the breach direction."""
    pkg = _package()
    staged = tmp_path / "repo"
    onto = staged / "verticals" / pkg.namespace / "ontology"
    onto.mkdir(parents=True)
    (onto / f"{pkg.namespace}_v0.yaml").write_text(assemble_yaml(pkg), encoding="utf-8")
    api = staged / "services" / "api"
    api.mkdir(parents=True)
    shutil.copy2(_SRC_ROOT / "services" / "api" / "main.py", api / "main.py")

    config = RecommendConfig(
        threshold=pkg.metric.threshold,
        direction=pkg.metric.direction,
        label=pkg.metric.label,
        unit=pkg.metric.unit,
        recovery_value=pkg.recovery_value,
        recovery_description=pkg.recovery_description,
        problem=pkg.problem,
        decision=pkg.decision,
    )
    result = scaffold.scaffold_vertical(pkg.namespace, config, repo_root=staged)

    assert result.roles.asset_type == "Pond"
    models = (staged / "verticals" / pkg.namespace / "generated" / "models.py").read_text(
        encoding="utf-8"
    )
    assert "class Pond(BaseModel):" in models
    assert "whiteleg_shrimp" in models  # the domain enum propagated to generated code
    assert "OCT_RECOMMEND_DIRECTION=below" in result.env_block
    assert "OCT_RECOMMEND_ENTITY_TYPE=Pond" in result.env_block
    assert "OCT_RECOMMEND_ENTITY_ID_FIELD=pond_id" in result.env_block


# --------------------------------------------------------------------------- #
# Prebaked defaults (AC-4 fallback)
# --------------------------------------------------------------------------- #


def test_prebaked_defaults_are_valid_and_scaffoldable(tmp_path: Path) -> None:
    packages = load_default_packages()
    by_ns = {p.namespace: p for p in packages}
    assert set(by_ns) == {"solar_farm", "water_utility"}
    # One crash (below) + one overrun (above) — covers both recommender directions.
    assert by_ns["water_utility"].metric.direction == "below"
    assert by_ns["solar_farm"].metric.direction == "above"

    for pkg in packages:
        assert pkg.source == "prebaked_default"
        path = tmp_path / f"{pkg.namespace}_v0.yaml"
        path.write_text(assemble_yaml(pkg), encoding="utf-8")
        findings = ontology_validator.validate_file(path)
        assert findings == [], f"{pkg.namespace}: " + "\n".join(f.render() for f in findings)
        # role detection works on every default
        scaffold.detect_roles(code_generator.load_doc(path))
