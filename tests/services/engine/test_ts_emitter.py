"""Tests for the TypeScript emitter (light path — no tsc compile)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.engine.code_generator import emit_typescript


def _doc() -> dict[str, Any]:
    return {
        "version": 0,
        "namespace": "test",
        "object_types": {
            "Asset": {
                "primary_key": "asset_id",
                "properties": {
                    "asset_id": {"type": "string", "required": True},
                    "name": {"type": "string"},
                    "status": {"type": "enum", "values": ["active", "retired"]},
                    "capacity_kw": {"type": "float"},
                    "meta": {"type": "json"},
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


def test_ts_emitter_exists_and_interface_count(tmp_path: Path) -> None:
    out = tmp_path / "types.ts"
    emit_typescript(_doc(), out)
    text = out.read_text()
    assert text
    assert text.count("export interface ") == 2


def test_ts_emitter_field_shapes(tmp_path: Path) -> None:
    out = tmp_path / "types.ts"
    emit_typescript(_doc(), out)
    text = out.read_text()
    assert "asset_id: string;" in text
    assert "name?: string;" in text
    assert "status?: 'active' | 'retired';" in text
    assert "capacity_kw?: number;" in text
    assert "meta?: Record<string, unknown>;" in text
    assert "site_id: string;" in text


def test_ts_emitter_braces_match(tmp_path: Path) -> None:
    out = tmp_path / "types.ts"
    emit_typescript(_doc(), out)
    text = out.read_text()
    assert text.count("{") == text.count("}")
    assert text.count("export interface ") == text.count("{")
