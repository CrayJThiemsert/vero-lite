"""Tests for the JSON Schema emitter in ``services.engine.code_generator``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from services.engine.code_generator import emit_jsonschema


def _doc() -> dict[str, Any]:
    return {
        "version": 0,
        "namespace": "test",
        "object_types": {
            "Asset": {
                "primary_key": "asset_id",
                "properties": {
                    "asset_id": {"type": "string", "required": True},
                    "capacity_kw": {"type": "float"},
                    "install_date": {"type": "date"},
                    "opened_at": {"type": "timestamp"},
                    "status": {"type": "enum", "values": ["active", "retired"]},
                    "meta": {"type": "json"},
                    "site_ref": {"type": "ref", "target": "Site"},
                },
            },
            "Site": {
                "primary_key": "site_id",
                "properties": {
                    "site_id": {"type": "string", "required": True},
                },
            },
        },
        "link_types": {},
    }


def test_jsonschema_emitter_json_load_and_meta_validates(tmp_path: Path) -> None:
    out = tmp_path / "schema.json"
    emit_jsonschema(_doc(), out)
    bundle = json.loads(out.read_text())
    assert set(bundle.keys()) == {"Asset", "Site"}
    for name, schema in bundle.items():
        Draft202012Validator.check_schema(schema)
        assert schema["type"] == "object"
        assert "properties" in schema
        assert schema["title"] == name


def test_jsonschema_emitter_per_property_shape(tmp_path: Path) -> None:
    out = tmp_path / "schema.json"
    emit_jsonschema(_doc(), out)
    bundle = json.loads(out.read_text())
    asset = bundle["Asset"]
    props = asset["properties"]
    assert props["capacity_kw"] == {"type": "number"}
    assert props["install_date"] == {"type": "string", "format": "date"}
    assert props["opened_at"] == {"type": "string", "format": "date-time"}
    assert props["status"] == {"type": "string", "enum": ["active", "retired"]}
    assert props["meta"] == {"type": "object"}
    assert props["site_ref"] == {"type": "string"}
    assert asset["required"] == ["asset_id"]
