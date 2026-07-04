"""Ontology metadata projection for the ``GET /meta`` endpoint (PLAN-0013 Step 1b).

Loads a vertical's **source** ontology YAML and projects it into a small,
UI-friendly metadata shape the ontology-driven demo UI consumes — object types
(with ``primary_key`` + ``title_key`` + properties + enums) and link types.

Vertical-agnostic: swapping the ontology swaps the metadata with **no UI
change** (PLAN-0013 AC-template). Loaded from the YAML source of truth rather
than the generated ``schema.json`` — the latter is JSON-Schema-per-type and
carries property types + enums but **not** ``title_key`` / ``primary_key`` /
link metadata, which a generic UI needs to render titles + relationships.

ADR-0027 R2 (PLAN-0050) adds the four OPTIONAL semantic-enrichment constructs to
this projection (``synonyms``, ``sample_values``, ``verified_queries``, and
quantity-binding ``grain`` / ``join_path``); an ontology declaring none of them
projects every new attribute to its empty/None default (the D2 invariant).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from ruamel.yaml import YAML


class Synonyms(BaseModel):
    """ADR-0027 R2 (SD-2): lang-keyed alternate names for NL matching.

    The th/en separation is the moat (F9). Each language is an optional list
    (absent projects to an empty list). Attachable at object-type and property
    level (SD-1).
    """

    th: list[str] = Field(default_factory=list, description="Thai alternate names")
    en: list[str] = Field(default_factory=list, description="English alternate names")


class VerifiedQuery(BaseModel):
    """ADR-0027 R2 (SD-4): a curated known-good NL question -> trusted answer pair."""

    question: str = Field(..., description="The natural-language question")
    answer: str = Field(..., description="The trusted natural-language answer / grounded fact")


class PropertyMeta(BaseModel):
    """One property of an object type."""

    name: str
    type: str
    required: bool = False
    enum: list[str] | None = Field(default=None, description="Allowed values when type == 'enum'")
    target: str | None = Field(
        default=None, description="Referenced object_type when type == 'ref'"
    )
    synonyms: Synonyms | None = Field(
        default=None, description="ADR-0027 R2 (SD-1/SD-2): th/en alternate names for this property"
    )
    sample_values: list[str] = Field(
        default_factory=list,
        description="ADR-0027 R2 (SD-3): closed filtering set when populated",
    )


class QuantityBinding(BaseModel):
    """ADR-0021 construct (b): one declared quantity-kind ⟂ unit binding."""

    kind: str = Field(..., description="A measured_kind enum value")
    unit: str = Field(..., description="The coherent unit bound to this kind")
    grain: str | None = Field(
        default=None, description="ADR-0027 R2 (SD-5): optional aggregation grain for this kind"
    )
    join_path: str | None = Field(
        default=None, description="ADR-0027 R2 (SD-5): optional join-path semantics for this kind"
    )


class ObjectTypeMeta(BaseModel):
    """One ontology object type and its display + property metadata."""

    name: str
    primary_key: str | None = None
    title_key: str | None = Field(
        default=None, description="Property to render as the display title"
    )
    description: str | None = None
    properties: list[PropertyMeta]
    quantity_bindings: list[QuantityBinding] = Field(
        default_factory=list,
        description="ADR-0021: declared quantity-kind -> unit bindings for this type",
    )
    synonyms: Synonyms | None = Field(
        default=None, description="ADR-0027 R2 (SD-1/SD-2): th/en alternate names for this type"
    )
    verified_queries: list[VerifiedQuery] = Field(
        default_factory=list,
        description="ADR-0027 R2 (SD-B): curated known-good NL question/answer pairs",
    )


class LinkTypeMeta(BaseModel):
    """One relationship between two object types."""

    name: str
    from_type: str = Field(..., description="Source object_type")
    to_type: str = Field(..., description="Target object_type")
    cardinality: str | None = None


class OntologyMeta(BaseModel):
    """The UI-facing projection of a vertical's ontology."""

    vertical: str
    namespace: str | None = None
    version: int | None = None
    object_types: list[ObjectTypeMeta]
    link_types: list[LinkTypeMeta]


def ontology_path(vertical: str) -> Path:
    """Path to a vertical's source ontology YAML (matches the engine CLI)."""
    return Path("verticals") / vertical / "ontology" / f"{vertical}_v0.yaml"


def _synonyms(raw: Any) -> Synonyms | None:
    """Project a raw ``{th, en}`` mapping into :class:`Synonyms` (None when absent/empty)."""
    if not isinstance(raw, dict):
        return None
    th = [str(v) for v in (raw.get("th") or [])]
    en = [str(v) for v in (raw.get("en") or [])]
    if not th and not en:
        return None
    return Synonyms(th=th, en=en)


def _property_meta(name: str, raw: dict[str, Any]) -> PropertyMeta:
    ptype = str(raw.get("type", "string"))
    enum: list[str] | None = None
    if ptype == "enum":
        values = raw.get("values")
        if isinstance(values, list):
            enum = [str(v) for v in values]
    target = raw.get("target") if ptype == "ref" else None
    sample_values = [str(v) for v in (raw.get("sample_values") or [])]
    return PropertyMeta(
        name=name,
        type=ptype,
        required=bool(raw.get("required", False)),
        enum=enum,
        target=str(target) if target is not None else None,
        synonyms=_synonyms(raw.get("synonyms")),
        sample_values=sample_values,
    )


def load_ontology_meta(vertical: str) -> OntologyMeta:
    """Load + project a vertical's ontology YAML into :class:`OntologyMeta`."""
    yaml = YAML(typ="safe")
    with ontology_path(vertical).open(encoding="utf-8") as fh:
        doc: dict[str, Any] = yaml.load(fh)

    object_types: list[ObjectTypeMeta] = []
    for name, raw in (doc.get("object_types") or {}).items():
        obj = raw or {}
        props_raw = obj.get("properties") or {}
        properties = [_property_meta(str(pn), pd or {}) for pn, pd in props_raw.items()]
        bindings = [
            QuantityBinding(
                kind=str(b.get("kind", "")),
                unit=str(b.get("unit", "")),
                grain=str(b["grain"]) if b.get("grain") is not None else None,
                join_path=str(b["join_path"]) if b.get("join_path") is not None else None,
            )
            for b in (obj.get("quantity_bindings") or [])
            if isinstance(b, dict)
        ]
        verified_queries = [
            VerifiedQuery(question=str(q.get("question", "")), answer=str(q.get("answer", "")))
            for q in (obj.get("verified_queries") or [])
            if isinstance(q, dict)
        ]
        object_types.append(
            ObjectTypeMeta(
                name=str(name),
                primary_key=obj.get("primary_key"),
                title_key=obj.get("title_key"),
                description=obj.get("description"),
                properties=properties,
                quantity_bindings=bindings,
                synonyms=_synonyms(obj.get("synonyms")),
                verified_queries=verified_queries,
            )
        )

    link_types: list[LinkTypeMeta] = []
    for name, raw in (doc.get("link_types") or {}).items():
        link = raw or {}
        link_types.append(
            LinkTypeMeta(
                name=str(name),
                from_type=str(link.get("from", "")),
                to_type=str(link.get("to", "")),
                cardinality=link.get("cardinality"),
            )
        )

    return OntologyMeta(
        vertical=vertical,
        namespace=doc.get("namespace"),
        version=doc.get("version"),
        object_types=object_types,
        link_types=link_types,
    )
