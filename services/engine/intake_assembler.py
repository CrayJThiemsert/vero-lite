"""Deterministic partner-input-package -> canonical OCT ontology YAML (PLAN-0017).

The live co-creation intake **face** (PLAN-0017) turns a free-text domain
description into a :class:`IntakePackage` (drafted by the MS-S1 LLM — see
``services/engine/llm/intake.py`` — or a prebaked default, or manual entry),
the operator reviews/edits it behind the mandatory gate, and the confirmed
package is assembled **here** into the OCT-shaped ontology YAML that
``vero-lite new-vertical`` (PLAN-0016 ``scaffold.py``) requires at
``verticals/<ns>/ontology/<ns>_v0.yaml``.

**Why constrained slots, not free YAML (ADR-0015 D5 / PLAN-0017 OQ-4 hybrid).**
The LLM never emits a whole ontology — it fills bounded *domain slots*
(the Asset-/Site-role names + their domain properties/enums, the metric +
threshold/direction, the action vocabulary, the problem/decision/recovery
texts). This module assembles the fixed six-type OCT skeleton (the five
ADR-008 D1 base types + the D4 ``AlertEventLink`` join) around those slots,
**guaranteeing** the three invariants ``scaffold.detect_roles`` depends on:

1. exactly **one** geo-bearing object type — the Site-role (``lat`` + ``lng``);
2. ``OperationalEvent`` carries **exactly one** ref to the Site-role and one to
   the Asset-role;
3. the event's Asset-ref field name **equals the Asset-role primary key field**
   (so ``OCT_RECOMMEND_ENTITY_ID_FIELD`` resolves on the event).

The assembled YAML is structurally identical to ``aquaculture_v0.yaml`` (the
known-valid template), so it passes the L1+L2 validator
(``ontology_validator``) by construction; the caller still runs
``vero-lite validate`` before the gate renders (PLAN-0017 Step 2) as the
backstop.
"""

from __future__ import annotations

import io
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator
from ruamel.yaml import YAML

# --------------------------------------------------------------------------- #
# Naming helpers (mirror code_generator._snake — kept local to avoid importing
# a private symbol; the regexes are identical).
# --------------------------------------------------------------------------- #

_CAMEL_BOUNDARY = re.compile(r"(.)([A-Z][a-z]+)")
_LOWER_UPPER = re.compile(r"([a-z0-9])([A-Z])")
_NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_TYPE_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
_PROP_RE = re.compile(r"^[a-z][a-z0-9_]*$")
# enum / action values are embedded verbatim into generated Pydantic Literals
# and SQL CHECK clauses (code_generator) — forbid the quote/backslash chars that
# would break that generated code. Spaces / dashes / slashes are fine.
_ENUM_VALUE_RE = re.compile(r"^[^\"'\\]+$")

# The Asset-role property names this module owns structurally; an LLM-/operator-
# supplied domain property colliding with one (or with the geo fields) is dropped
# so the skeleton invariants always hold.
_GEO_FIELDS = ("lat", "lng")

# Fixed OCT vocabulary for the non-domain skeleton (matches aquaculture_v0).
_EVENT_TYPES = ["reading", "transition", "alarm"]
_SEVERITIES = ["info", "warn", "error", "critical"]
_ALERT_URGENCY = ["low", "medium", "high", "critical"]
_ALERT_STATUS = ["open", "acknowledged", "resolved"]
_ACTION_STATUS = ["proposed", "approved", "rejected", "executed"]


def _snake(name: str) -> str:
    """``SolarArray`` -> ``solar_array`` (mirrors code_generator._snake)."""
    interim = _CAMEL_BOUNDARY.sub(r"\1_\2", name)
    return _LOWER_UPPER.sub(r"\1_\2", interim).lower()


# --------------------------------------------------------------------------- #
# The partner-input package (the gate-editable contract)
# --------------------------------------------------------------------------- #

# Domain properties are descriptive attributes only — refs/json are structural
# and owned by the assembler, so they are excluded from the editable surface.
DomainPropertyType = Literal["string", "int", "float", "bool", "enum", "timestamp", "date"]
PackageSource = Literal["ms_s1_live", "prebaked_default", "manual_entry"]


class PropertySpec(BaseModel):
    """One domain attribute on the Asset-/Site-role (scalar or enum)."""

    name: str = Field(description="snake_case property name (^[a-z][a-z0-9_]*$)")
    type: DomainPropertyType = Field(description="property scalar/enum type")
    values: list[str] = Field(
        default_factory=list, description="enum members; required + non-empty when type is enum"
    )
    required: bool = Field(default=False, description="whether the property is required")

    @field_validator("name")
    @classmethod
    def _check_name(cls, v: str) -> str:
        if not _PROP_RE.match(v):
            raise ValueError(f"property name {v!r} must be snake_case (^[a-z][a-z0-9_]*$)")
        return v

    @model_validator(mode="after")
    def _check_enum_values(self) -> PropertySpec:
        if self.type == "enum":
            if not self.values:
                raise ValueError(f"enum property {self.name!r} requires a non-empty 'values' list")
            for value in self.values:
                if not value.strip() or not _ENUM_VALUE_RE.match(value):
                    raise ValueError(
                        f"enum value {value!r} on {self.name!r} is empty or contains a "
                        "quote/backslash (would break generated code)"
                    )
        return self


class RoleSpec(BaseModel):
    """A domain object role — its PascalCase type name + its domain properties.

    The primary key / title / geo / ref fields are NOT supplied here; the
    assembler injects them structurally (see module docstring).
    """

    type_name: str = Field(description="PascalCase object type name, e.g. 'Pond'")
    properties: list[PropertySpec] = Field(
        default_factory=list, description="domain attribute properties (scalars/enums)"
    )

    @field_validator("type_name")
    @classmethod
    def _check_type_name(cls, v: str) -> str:
        if not _TYPE_RE.match(v):
            raise ValueError(f"type_name {v!r} must be PascalCase (^[A-Z][A-Za-z0-9]*$)")
        # Reserved skeleton type names cannot be reused for a domain role.
        if v in {"OperationalEvent", "Alert", "RecommendedAction", "AlertEventLink"}:
            raise ValueError(f"type_name {v!r} is a reserved OCT skeleton type")
        return v


class MetricSpec(BaseModel):
    """The breaching metric — drives the threshold->action config + synthetic breach."""

    label: str = Field(description="short anomaly label (OCT_RECOMMEND_LABEL)")
    unit: str = Field(default="", description="measurement unit, e.g. 'mg/L' (blank allowed)")
    threshold: float = Field(description="OCT_RECOMMEND_THRESHOLD — the breach threshold value")
    direction: Literal["above", "below"] = Field(
        description="breach direction: 'above' (overrun) or 'below' (crash)"
    )

    @field_validator("label")
    @classmethod
    def _check_label(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("metric label must be non-empty")
        return v


class IntakePackage(BaseModel):
    """The partner-input package: the gate-editable, assembler-consumable contract.

    Produced by MS-S1 extraction (``source='ms_s1_live'``), loaded from a
    prebaked default (``'prebaked_default'``), or hand-entered in the gate
    (``'manual_entry'``). ``source`` + ``confidence`` are package metadata, NOT
    serialized into the ontology YAML (the L1 schema forbids extra top-level
    keys) — they surface in the gate + the generated README so the operator
    always knows which dataset is in play (PLAN-0017 AC-4 non-silent state).
    """

    namespace: str = Field(description="vertical namespace slug; also the directory name")
    domain_label: str = Field(description="human-readable domain description")
    asset_role: RoleSpec = Field(description="the managed operational unit (recommender entity)")
    site_role: RoleSpec = Field(description="the geo-bearing location grouping assets")
    metric: MetricSpec = Field(description="the breaching metric + threshold/direction")
    action_types: list[str] = Field(
        min_length=1, description="RecommendedAction.action_type enum members (>=1)"
    )
    problem: str = Field(default="", description="problem statement (for the README / env)")
    decision: str = Field(default="", description="corrective action description (README / env)")
    recovery_value: float = Field(description="OCT_RECOVERY_VALUE — safe reading after the action")
    recovery_description: str = Field(default="", description="OCT_RECOVERY_DESCRIPTION text")
    source: PackageSource = Field(
        default="manual_entry", description="package provenance; surfaced in the gate + README"
    )
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="coarse extraction confidence; advisory only"
    )

    @field_validator("namespace")
    @classmethod
    def _check_namespace(cls, v: str) -> str:
        if not _NAMESPACE_RE.match(v):
            raise ValueError(f"namespace {v!r} must be lowercase snake_case (^[a-z][a-z0-9_]*$)")
        return v

    @field_validator("action_types")
    @classmethod
    def _check_action_types(cls, v: list[str]) -> list[str]:
        cleaned = [a.strip() for a in v if a.strip()]
        if not cleaned:
            raise ValueError("action_types must contain at least one non-empty action")
        for action in cleaned:
            if not _ENUM_VALUE_RE.match(action):
                raise ValueError(
                    f"action_type {action!r} has a quote/backslash (breaks generated code)"
                )
        return cleaned

    @model_validator(mode="after")
    def _check_roles_distinct(self) -> IntakePackage:
        if self.asset_role.type_name == self.site_role.type_name:
            raise ValueError(
                f"asset_role and site_role share the type name {self.asset_role.type_name!r}; "
                "they must be distinct object types"
            )
        return self


class PackageAssemblyError(Exception):
    """Raised when a package cannot be assembled into a valid OCT ontology."""


# --------------------------------------------------------------------------- #
# Assembly
# --------------------------------------------------------------------------- #


def _prop(
    ptype: str,
    *,
    required: bool = False,
    values: list[str] | None = None,
    target: str | None = None,
) -> dict[str, Any]:
    """Build one ontology property dict with only the L1-allowed keys."""
    out: dict[str, Any] = {"type": ptype}
    if values is not None:
        out["values"] = list(values)
    if target is not None:
        out["target"] = target
    if required:
        out["required"] = True
    return out


def _domain_props(role: RoleSpec, reserved: set[str]) -> dict[str, dict[str, Any]]:
    """Render a role's domain properties, dropping any that collide with the
    structurally-reserved field names (so the skeleton invariants always hold)."""
    out: dict[str, dict[str, Any]] = {}
    for p in role.properties:
        if p.name in reserved or p.name in _GEO_FIELDS or p.name in out:
            continue
        enum_values = p.values if p.type == "enum" else None
        out[p.name] = _prop(p.type, required=p.required, values=enum_values)
    return out


def assemble_ontology(package: IntakePackage) -> dict[str, Any]:
    """Assemble the canonical six-type OCT ontology dict from a package.

    Pure + deterministic. The result is structurally identical to
    ``aquaculture_v0.yaml`` with the domain slots substituted, so it passes the
    L1+L2 validator by construction (see module docstring for the invariants).
    """
    asset = package.asset_role.type_name
    site = package.site_role.type_name
    asset_snake = _snake(asset)
    site_snake = _snake(site)
    asset_pk = f"{asset_snake}_id"
    site_pk = f"{site_snake}_id"
    target_asset_ref = f"target_{asset_snake}_id"

    # Asset-role: pk + name + domain props + the (single) ref to the Site-role.
    asset_props: dict[str, dict[str, Any]] = {
        asset_pk: _prop("string", required=True),
        "name": _prop("string", required=True),
    }
    asset_props.update(_domain_props(package.asset_role, {asset_pk, "name", site_pk}))
    asset_props[site_pk] = _prop("ref", target=site, required=True)

    # Site-role: pk + name + domain props + the geo pair (the ONLY geo type).
    site_props: dict[str, dict[str, Any]] = {
        site_pk: _prop("string", required=True),
        "name": _prop("string", required=True),
    }
    site_props.update(_domain_props(package.site_role, {site_pk, "name"}))
    site_props["lat"] = _prop("float")
    site_props["lng"] = _prop("float")

    # OperationalEvent: the event's Asset-ref field name == the Asset pk field
    # (so OCT_RECOMMEND_ENTITY_ID_FIELD resolves), one Site-ref, event_type
    # carries 'reading', severity first/last = baseline/breach.
    event_props = {
        "event_id": _prop("string", required=True),
        "event_type": _prop("enum", values=_EVENT_TYPES),
        "severity": _prop("enum", values=_SEVERITIES),
        "measured_value": _prop("float"),
        "unit": _prop("string"),
        "description": _prop("string"),
        "occurred_at": _prop("timestamp", required=True),
        asset_pk: _prop("ref", target=asset),
        site_pk: _prop("ref", target=site),
    }

    alert_props = {
        "alert_id": _prop("string", required=True),
        "title": _prop("string", required=True),
        "urgency": _prop("enum", values=_ALERT_URGENCY),
        "status": _prop("enum", values=_ALERT_STATUS),
        "opened_at": _prop("timestamp", required=True),
        "resolved_at": _prop("timestamp"),
        "reasoning": _prop("string"),
    }

    action_props = {
        "action_id": _prop("string", required=True),
        "action_type": _prop("enum", values=package.action_types),
        "confidence_score": _prop("float"),
        "status": _prop("enum", values=_ACTION_STATUS),
        "parameters": _prop("json"),
        "alert_id": _prop("ref", target="Alert", required=True),
        target_asset_ref: _prop("ref", target=asset),
    }

    link_props = {
        "link_id": _prop("string", required=True),
        "created_at": _prop("timestamp", required=True),
        "alert_id": _prop("ref", target="Alert", required=True),
        "event_id": _prop("ref", target="OperationalEvent", required=True),
    }

    object_types: dict[str, Any] = {
        asset: {
            "primary_key": asset_pk,
            "title_key": "name",
            "description": f"A {asset} — the managed operational unit ({package.domain_label}).",
            "properties": asset_props,
        },
        site: {
            "primary_key": site_pk,
            "title_key": "name",
            "description": f"A {site} — a geo-located location grouping one or more {asset}s.",
            "properties": site_props,
        },
        "OperationalEvent": {
            "primary_key": "event_id",
            "description": f"Time-stamped signal concerning a {asset} or {site}.",
            "properties": event_props,
        },
        "Alert": {
            "primary_key": "alert_id",
            "title_key": "title",
            "description": "An actionable notification derived from one or more OperationalEvents.",
            "properties": alert_props,
        },
        "RecommendedAction": {
            "primary_key": "action_id",
            "description": "An AI-proposed action awaiting human approval (ADR-007 D2 envelope).",
            "properties": action_props,
        },
        "AlertEventLink": {
            "primary_key": "link_id",
            "description": "Join linking an Alert to its OperationalEvent(s) (ADR-008 D4).",
            "properties": link_props,
        },
    }

    link_types = {
        f"{asset_snake}_hosted_at_{site_snake}": {
            "from": asset,
            "to": site,
            "cardinality": "many_to_one",
            "foreign_key": f"{asset}.{site_pk} -> {site}.{site_pk}",
            "description": f"Each {asset} is hosted at exactly one {site}.",
        },
        f"event_emitted_by_{asset_snake}": {
            "from": "OperationalEvent",
            "to": asset,
            "cardinality": "many_to_one",
            "foreign_key": f"OperationalEvent.{asset_pk} -> {asset}.{asset_pk}",
        },
        f"event_occurred_at_{site_snake}": {
            "from": "OperationalEvent",
            "to": site,
            "cardinality": "many_to_one",
            "foreign_key": f"OperationalEvent.{site_pk} -> {site}.{site_pk}",
        },
        "action_addresses_alert": {
            "from": "RecommendedAction",
            "to": "Alert",
            "cardinality": "many_to_one",
            "foreign_key": "RecommendedAction.alert_id -> Alert.alert_id",
        },
        f"action_target_{asset_snake}": {
            "from": "RecommendedAction",
            "to": asset,
            "cardinality": "many_to_one",
            "foreign_key": f"RecommendedAction.{target_asset_ref} -> {asset}.{asset_pk}",
        },
        "alert_event_link_to_alert": {
            "from": "AlertEventLink",
            "to": "Alert",
            "cardinality": "many_to_one",
            "foreign_key": "AlertEventLink.alert_id -> Alert.alert_id",
        },
        "alert_event_link_to_event": {
            "from": "AlertEventLink",
            "to": "OperationalEvent",
            "cardinality": "many_to_one",
            "foreign_key": "AlertEventLink.event_id -> OperationalEvent.event_id",
        },
    }

    return {
        "version": 0,
        "namespace": package.namespace,
        "object_types": object_types,
        "link_types": link_types,
    }


def dump_yaml(doc: dict[str, Any]) -> str:
    """Serialize an assembled ontology dict to a YAML string (block style)."""
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.indent(mapping=2, sequence=4, offset=2)
    buf = io.StringIO()
    yaml.dump(doc, buf)
    return buf.getvalue()


def assemble_yaml(package: IntakePackage) -> str:
    """Assemble + serialize a package to its OCT ontology YAML string."""
    return dump_yaml(assemble_ontology(package))
