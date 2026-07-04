"""Tests for the R1 semantic context-pack emitter (PLAN-0049 Step 4).

The 7th emitter compiles a vertical's ontology YAML into a compact markdown
context pack for NL-query / anomaly grounding. Deterministic, pure-Python, and
degrades gracefully in the absence of the carved-out R2 enrichment fields
(SD-1). The token budget (32K char tripwire) is asserted here — the emitter
itself does not enforce it (deterministic emit only).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.engine.code_generator import (
    CONTEXT_PACK_CHAR_BUDGET,
    emit_context_pack,
    generate_all,
    load_doc,
)

_ENERGY_YAML = Path("verticals/energy/ontology/energy_v0.yaml")


def _full_doc() -> dict[str, Any]:
    return {
        "version": 2,
        "namespace": "demo",
        "object_types": {
            "Widget": {
                "primary_key": "widget_id",
                "title_key": "label",
                "description": "A demo widget.",
                "properties": {
                    "widget_id": {"type": "string", "required": True},
                    "label": {"type": "string"},
                    "kind": {"type": "enum", "values": ["a", "b"]},
                    "site_id": {"type": "ref", "target": "Site"},
                },
                "quantity_bindings": [{"kind": "temperature", "unit": "celsius"}],
            },
            "Site": {"primary_key": "site_id", "properties": {"site_id": {"type": "string"}}},
        },
        "link_types": {
            "widget_at_site": {
                "from": "Widget",
                "to": "Site",
                "cardinality": "many_to_one",
                "foreign_key": "Widget.site_id -> Site.site_id",
            }
        },
    }


def _bare_doc() -> dict[str, Any]:
    """A minimal ontology with NO enum, NO quantity_bindings, NO links — the
    R2-degrade / empty-relationship path."""
    return {
        "version": 0,
        "namespace": "bare",
        "object_types": {
            "Thing": {
                "primary_key": "thing_id",
                "properties": {"thing_id": {"type": "string", "required": True}},
            }
        },
    }


def test_context_pack_has_all_sections(tmp_path: Path) -> None:
    out = emit_context_pack(_full_doc(), tmp_path / "pack.md")
    text = out.read_text(encoding="utf-8")
    assert "# Semantic context pack — demo" in text
    assert "Ontology revision 2" in text  # the version field surfaces
    assert "## Object types" in text
    assert "### Widget — A demo widget." in text
    assert "primary key `widget_id`; title `label`" in text.lower()
    # closed enum set + ref target rendered
    assert "closed set: {a, b}" in text
    assert "`site_id` (ref) -> Site" in text
    # measured-quantity conventions + relationships
    assert "## Measured quantities (conventions)" in text
    assert "Widget: temperature→celsius" in text
    assert "## Relationships" in text
    assert "Widget —many_to_one→ Site" in text


def test_closed_set_refusal_framing(tmp_path: Path) -> None:
    """The pack states enum sets are CLOSED (refuse-not-guess) — the coverage
    posture the semantic-foundation research (P3) requires."""
    out = emit_context_pack(_full_doc(), tmp_path / "pack.md")
    text = out.read_text(encoding="utf-8")
    assert "CLOSED" in text
    assert "refuse" in text.lower()


def test_r2_degrade_and_empty_relationships(tmp_path: Path) -> None:
    """SD-1 carve-out: with no quantity_bindings / no links / no enrichment, the
    emitter still produces a valid pack — the measured + relationships sections
    are omitted, and the R2 note records the degrade."""
    out = emit_context_pack(_bare_doc(), tmp_path / "pack.md")
    text = out.read_text(encoding="utf-8")
    assert "### Thing" in text
    assert "## Measured quantities" not in text  # no quantity_bindings -> omitted
    assert "## Relationships" not in text  # no link_types -> omitted
    assert "not yet populated" in text  # the R2-degrade note always present


def test_context_pack_is_deterministic(tmp_path: Path) -> None:
    a = emit_context_pack(_full_doc(), tmp_path / "a.md").read_text(encoding="utf-8")
    b = emit_context_pack(_full_doc(), tmp_path / "b.md").read_text(encoding="utf-8")
    assert a == b


def test_real_energy_pack_within_token_budget(tmp_path: Path) -> None:
    """The real energy ontology's pack stays well under the 32K char tripwire
    (target ~4KB) — the per-vertical budget the semantic-foundation research
    flags before multi-vertical growth."""
    out = emit_context_pack(load_doc(_ENERGY_YAML), tmp_path / "energy.md")
    size = len(out.read_text(encoding="utf-8"))
    assert 0 < size < CONTEXT_PACK_CHAR_BUDGET
    assert size < 8_000  # comfortably within the ~4KB target for a 6-type ontology


def test_generate_all_includes_context_pack(tmp_path: Path) -> None:
    """The orchestrator wires the 7th emitter: generate_all returns the
    context_pack key alongside the other six."""
    outdir = tmp_path / "demo" / "generated"
    outputs = generate_all(_ENERGY_YAML, outdir)
    assert "context_pack" in outputs
    assert outputs["context_pack"].name == "context_pack.md"
    assert outputs["context_pack"].read_text(encoding="utf-8").startswith("# Semantic context pack")
