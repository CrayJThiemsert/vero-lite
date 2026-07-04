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


# ---------- ADR-0027 R2 / PLAN-0050 Step 7: the emitter POPULATES enrichment (AC-7) ----------


def _enriched_doc() -> dict[str, Any]:
    """A doc carrying all four ADR-0027 enrichment constructs — the AC-7 populate path."""
    return {
        "version": 1,
        "namespace": "enr",
        "object_types": {
            "Asset": {
                "primary_key": "asset_id",
                "title_key": "name",
                "description": "An asset.",
                "synonyms": {"th": ["สินทรัพย์"], "en": ["asset", "equipment"]},
                "verified_queries": [
                    {"question": "How many active assets?", "answer": "Count active Assets."}
                ],
                "properties": {
                    "asset_id": {"type": "string", "required": True},
                    "status": {
                        "type": "enum",
                        "values": ["active", "retired"],
                        "synonyms": {"en": ["state"]},
                        "sample_values": ["active", "retired"],
                    },
                },
                "quantity_bindings": [
                    {
                        "kind": "temperature",
                        "unit": "celsius",
                        "grain": "hourly",
                        "join_path": "Asset.asset_id -> Site.site_id",
                    }
                ],
            },
            "Site": {"primary_key": "site_id", "properties": {"site_id": {"type": "string"}}},
        },
    }


def test_ac7_emitter_populates_enrichment(tmp_path: Path) -> None:
    """AC-7 (PLAN-0050 Step 7): with the four ADR-0027 constructs present, the emitter
    POPULATES them inline — object + property synonyms, sample values, verified queries,
    and metric grain / join_path — and the 'not yet populated' degrade note does NOT fire."""
    out = emit_context_pack(_enriched_doc(), tmp_path / "enr.md")
    text = out.read_text(encoding="utf-8")
    # object-level synonyms (th/en moat) + verified queries
    assert "Synonyms — th: สินทรัพย์; en: asset, equipment." in text
    assert "Verified queries:" in text
    assert "Q: How many active assets? -> A: Count active Assets." in text
    # property-level synonyms + sample values (closed set)
    assert "aka en: state" in text
    assert "sample values: {active, retired}" in text
    # metric grain + join_path rendered on the measure line
    assert "temperature→celsius @hourly via Asset.asset_id -> Site.site_id" in text
    # the degrade note is GONE for an enriched doc (the conditional's populate branch)
    assert "not yet populated" not in text
    assert "is populated inline above" in text


def test_ac7_bare_doc_still_degrades(tmp_path: Path) -> None:
    """AC-7 pair: a doc declaring NONE of the four constructs still emits the
    'not yet populated' degrade note (the conditional's else branch — both paths held)."""
    out = emit_context_pack(_bare_doc(), tmp_path / "bare.md")
    text = out.read_text(encoding="utf-8")
    assert "not yet populated" in text
    assert "is populated inline above" not in text
