"""Tests for the MCP tool-definition emitter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.engine.code_generator import emit_mcp


def _doc() -> dict[str, Any]:
    return {
        "version": 0,
        "namespace": "test",
        "object_types": {
            "Asset": {
                "primary_key": "asset_id",
                "properties": {"asset_id": {"type": "string", "required": True}},
            },
            "OperationalEvent": {
                "primary_key": "event_id",
                "properties": {"event_id": {"type": "string", "required": True}},
            },
        },
        "link_types": {},
    }


def test_mcp_emitter_shape_and_per_object_count(tmp_path: Path) -> None:
    out = tmp_path / "mcp_tools.json"
    emit_mcp(_doc(), out)
    tools = json.loads(out.read_text())
    assert isinstance(tools, list)
    for tool in tools:
        assert {"name", "description", "inputSchema"} <= set(tool.keys())
        assert isinstance(tool["inputSchema"], dict)
        assert tool["inputSchema"]["type"] == "object"
    names = [t["name"] for t in tools]
    for obj_name in ("asset", "operational_event"):
        assert f"list_{obj_name}" in names
        assert f"get_{obj_name}_by_id" in names
    assert len(tools) == 2 * 2


def test_mcp_emitter_get_by_id_input_schema(tmp_path: Path) -> None:
    out = tmp_path / "mcp_tools.json"
    emit_mcp(_doc(), out)
    tools = json.loads(out.read_text())
    get_asset = next(t for t in tools if t["name"] == "get_asset_by_id")
    schema = get_asset["inputSchema"]
    assert schema["properties"]["id"] == {"type": "string"}
    assert schema["required"] == ["id"]
