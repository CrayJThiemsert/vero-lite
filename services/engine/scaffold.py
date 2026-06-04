"""vero-lite ``new-vertical`` scaffolding engine (PLAN-0016).

Stitches the BUILD steps around the existing AUTO generator
(``code_generator.generate_all``) to turn a *partner-input package* — an
OCT-shaped ontology YAML plus a threshold→action config — into a runnable,
fully-skinned vertical: a deterministic synthetic adapter, the templated
boilerplate (adapter ``__init__``, ``handlers`` echo stub, package init,
README), and the registration code-mod in ``services/api/main.py``.

The synthetic dataset this emits is a **minimal, deterministic draft for
human review** (ADR-0015 D5): one site, one asset, a baseline reading and
the configured breach. PLAN-0016 Step 2 layers LLM enrichment on top; the
human review/edit gate (PLAN-0017) stays mandatory either way.

**Role detection.** The command reads the ontology to find the Site-role
(the object type bearing ``lat`` + ``lng``), the ``OperationalEvent`` stream,
and the Asset-role (the other ref target on ``OperationalEvent``) — so a
domain-renamed ontology (``Pond``/``Farm`` rather than ``Asset``/``Site``)
scaffolds correctly (proven by ``supply_chain`` = ``Shipment``/``Facility``).
The threshold *direction* (``above``/``below``) drives the breach value so a
below-threshold crash (e.g. an aquaculture dissolved-oxygen crash) fires the
recommender (PLAN-0016 Step 0).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from services.engine import code_generator, ontology_validator

# Fixed, deterministic synthetic timestamps (no randomness — reproducible
# demos/tests). The breach is the latest beat so real-time anchoring
# (PLAN-0015 D1) leaves nothing dangling in the future.
_BASELINE_AT = datetime(2026, 6, 1, 1, 30, tzinfo=UTC)
_BREACH_AT = datetime(2026, 6, 1, 2, 0, tzinfo=UTC)
_INSTALL_DATE = date(2026, 1, 15)

_NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_VALID_DIRECTIONS = ("above", "below")


class ScaffoldError(Exception):
    """A scaffolding precondition was not met (bad namespace, non-OCT ontology,
    existing files without ``--force``). Carries an operator-facing message."""


@dataclass(frozen=True)
class RecommendConfig:
    """The threshold→action config the operator supplies (becomes the env block
    + drives the synthetic breach). ``entity_type``/``entity_id_field`` are
    *derived* from the ontology (the Asset-role), not supplied here."""

    threshold: float
    direction: str
    label: str
    unit: str
    recovery_value: float
    recovery_description: str
    problem: str = ""
    decision: str = ""

    def validate(self) -> None:
        if self.direction not in _VALID_DIRECTIONS:
            raise ScaffoldError(
                f"direction {self.direction!r} invalid; expected one of {_VALID_DIRECTIONS}"
            )


@dataclass(frozen=True)
class VerticalRoles:
    """The OCT roles detected from the ontology (see module docstring)."""

    namespace: str
    site_type: str
    asset_type: str
    asset_site_ref: str  # FK field on the Asset-role pointing at the Site-role
    event_asset_ref: str  # FK field on OperationalEvent pointing at the Asset-role
    event_site_ref: str  # FK field on OperationalEvent pointing at the Site-role
    event_type_value: str  # the 'reading' member of OperationalEvent.event_type
    severity_baseline: str  # first severity enum value (e.g. 'info')
    severity_breach: str  # last severity enum value (e.g. 'critical')


@dataclass(frozen=True)
class ScaffoldResult:
    """What ``scaffold_vertical`` produced — paths written + the generated
    artifacts + the env block, for the CLI to print as a run checklist."""

    namespace: str
    roles: VerticalRoles
    written: list[Path] = field(default_factory=list)
    generated: dict[str, Path] = field(default_factory=dict)
    env_block: str = ""
    registered: bool = False


# --------------------------------------------------------------------------- #
# Role detection
# --------------------------------------------------------------------------- #


def _object_types(doc: dict[str, Any]) -> dict[str, Any]:
    types = doc.get("object_types")
    if not isinstance(types, dict):
        raise ScaffoldError("ontology has no 'object_types' mapping")
    return types


def _props(obj_def: dict[str, Any]) -> dict[str, Any]:
    props = obj_def.get("properties")
    return props if isinstance(props, dict) else {}


def _refs(obj_def: dict[str, Any]) -> dict[str, str]:
    """Map each ``type: ref`` property name → its ``target`` object type."""
    out: dict[str, str] = {}
    for name, spec in _props(obj_def).items():
        if isinstance(spec, dict) and spec.get("type") == "ref":
            target = spec.get("target")
            if isinstance(target, str):
                out[name] = target
    return out


def detect_roles(doc: dict[str, Any]) -> VerticalRoles:
    """Infer the Site/Asset/OperationalEvent roles from an OCT-shaped ontology.

    Raises :class:`ScaffoldError` with operator guidance when the ontology is
    not OCT-shaped (no geo-bearing Site, missing OperationalEvent, or the event
    does not carry exactly one Site ref + one Asset ref).
    """
    namespace = doc.get("namespace")
    if not isinstance(namespace, str) or not namespace:
        raise ScaffoldError("ontology has no 'namespace'")
    object_types = _object_types(doc)

    # Site-role = the object type bearing both lat + lng float properties.
    site_candidates = [
        name
        for name, obj in object_types.items()
        if isinstance(obj, dict) and {"lat", "lng"} <= set(_props(obj))
    ]
    if len(site_candidates) != 1:
        raise ScaffoldError(
            "expected exactly one geo-bearing Site-role object type (with 'lat' "
            f"and 'lng' properties); found {site_candidates or 'none'}"
        )
    site_type = site_candidates[0]

    if "OperationalEvent" not in object_types:
        raise ScaffoldError("ontology has no 'OperationalEvent' object type")
    event_def = object_types["OperationalEvent"]
    event_refs = _refs(event_def)
    site_event_refs = [f for f, t in event_refs.items() if t == site_type]
    asset_event_refs = [f for f, t in event_refs.items() if t != site_type]
    if len(site_event_refs) != 1 or len(asset_event_refs) != 1:
        raise ScaffoldError(
            "OperationalEvent must carry exactly one ref to the Site-role and one "
            f"ref to the Asset-role; found site refs {site_event_refs}, "
            f"other refs {asset_event_refs}"
        )
    event_site_ref = site_event_refs[0]
    event_asset_ref = asset_event_refs[0]
    asset_type = event_refs[event_asset_ref]

    # The Asset-role's FK to the Site-role (e.g. Asset.site_id -> Site).
    asset_refs = _refs(object_types[asset_type])
    asset_site_refs = [f for f, t in asset_refs.items() if t == site_type]
    if len(asset_site_refs) != 1:
        raise ScaffoldError(
            f"the Asset-role {asset_type!r} must carry exactly one ref to the "
            f"Site-role {site_type!r}; found {asset_site_refs}"
        )
    asset_site_ref = asset_site_refs[0]

    event_type_value = _pick_event_type(event_def)
    sev_lo, sev_hi = _pick_severities(event_def)
    return VerticalRoles(
        namespace=namespace,
        site_type=site_type,
        asset_type=asset_type,
        asset_site_ref=asset_site_ref,
        event_asset_ref=event_asset_ref,
        event_site_ref=event_site_ref,
        event_type_value=event_type_value,
        severity_baseline=sev_lo,
        severity_breach=sev_hi,
    )


def _enum_values(obj_def: dict[str, Any], prop: str) -> list[str]:
    spec = _props(obj_def).get(prop)
    if isinstance(spec, dict) and spec.get("type") == "enum":
        values = spec.get("values")
        if isinstance(values, list):
            return [str(v) for v in values]
    return []


def _pick_event_type(event_def: dict[str, Any]) -> str:
    values = _enum_values(event_def, "event_type")
    if not values:
        return "reading"
    return "reading" if "reading" in values else values[0]


def _pick_severities(event_def: dict[str, Any]) -> tuple[str, str]:
    values = _enum_values(event_def, "severity")
    if not values:
        return "info", "critical"
    return values[0], values[-1]


# --------------------------------------------------------------------------- #
# Deterministic record synthesis
# --------------------------------------------------------------------------- #


_SKIP = object()
_GEO_DEFAULTS = {"lat": 13.75, "lng": 100.50}


def _synth_prop_value(
    prop: str,
    spec: dict[str, Any],
    *,
    pk: Any,
    title_key: Any,
    type_name: str,
    pk_value: str,
    ref_values: dict[str, str],
) -> Any:
    """The synthetic value for one property, or ``_SKIP`` to omit it (unresolved
    refs and non-required scalars are omitted from the minimal record)."""
    if prop in ref_values:
        return ref_values[prop]
    if prop == pk:
        return pk_value
    if prop == title_key:
        return f"{type_name} 01"
    if prop in _GEO_DEFAULTS:
        return _GEO_DEFAULTS[prop]
    ptype = spec.get("type")
    if ptype == "enum":
        values = spec.get("values") or []
        return str(values[0]) if values else _SKIP
    if ptype == "ref":
        return _SKIP
    return _placeholder(ptype, prop) if spec.get("required") else _SKIP


def _synth_object(
    obj_def: dict[str, Any],
    type_name: str,
    pk_value: str,
    ref_values: dict[str, str],
) -> dict[str, Any]:
    """Build one minimal, ontology-valid record: PK + title + enums + geo +
    the supplied refs + placeholders for any other *required* scalar."""
    pk = obj_def.get("primary_key")
    title_key = obj_def.get("title_key")
    rec: dict[str, Any] = {}
    for prop, spec in _props(obj_def).items():
        if not isinstance(spec, dict):
            continue
        value = _synth_prop_value(
            prop,
            spec,
            pk=pk,
            title_key=title_key,
            type_name=type_name,
            pk_value=pk_value,
            ref_values=ref_values,
        )
        if value is not _SKIP:
            rec[prop] = value
    return rec


def _placeholder(ptype: Any, prop: str) -> Any:
    if ptype == "string":
        return f"{prop}-01"
    if ptype == "float":
        return 0.0
    if ptype == "int":
        return 0
    if ptype == "bool":
        return False
    if ptype == "timestamp":
        return _BASELINE_AT
    if ptype == "date":
        return _INSTALL_DATE
    if ptype == "json":
        return {}
    return ""


def _breach_value(threshold: float, direction: str) -> float:
    """A measured_value clearly on the breaching side of ``threshold``."""
    return round(threshold * (1.1 if direction == "above" else 0.8), 4)


def _safe_value(threshold: float, direction: str) -> float:
    """A measured_value clearly on the safe side of ``threshold``."""
    return round(threshold * (0.5 if direction == "above" else 1.5), 4)


def _synth_events(
    roles: VerticalRoles, config: RecommendConfig, asset_pk: str, site_pk: str
) -> list[dict[str, Any]]:
    refs = {roles.event_asset_ref: asset_pk, roles.event_site_ref: site_pk}
    baseline = {
        "event_id": "event-reading-01",
        "event_type": roles.event_type_value,
        "severity": roles.severity_baseline,
        "measured_value": _safe_value(config.threshold, config.direction),
        "unit": config.unit,
        "description": f"{roles.asset_type} 01 {config.label} nominal.",
        "occurred_at": _BASELINE_AT,
        **refs,
    }
    verb = "rose above" if config.direction == "above" else "fell below"
    breach = {
        "event_id": "event-reading-02",
        "event_type": roles.event_type_value,
        "severity": roles.severity_breach,
        "measured_value": _breach_value(config.threshold, config.direction),
        "unit": config.unit,
        "description": (
            f"{roles.asset_type} 01 {config.label} {verb} the "
            f"{config.threshold:g} {config.unit} threshold."
        ),
        "occurred_at": _BREACH_AT,
        **refs,
    }
    return [baseline, breach]


# --------------------------------------------------------------------------- #
# Source rendering
# --------------------------------------------------------------------------- #


def _py_literal(value: Any) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, datetime):
        return (
            f"datetime({value.year}, {value.month}, {value.day}, "
            f"{value.hour}, {value.minute}, tzinfo=UTC)"
        )
    if isinstance(value, date):
        return f"date({value.year}, {value.month}, {value.day})"
    if isinstance(value, dict):
        return "{}" if not value else repr(value)
    return repr(value)


def _render_fn(name: str, docstring: str, records: list[dict[str, Any]]) -> str:
    lines = [f"def {name}() -> list[dict[str, Any]]:", f'    """{docstring}"""', "    return ["]
    for rec in records:
        lines.append("        {")
        for key, value in rec.items():
            lines.append(f"            {key!r}: {_py_literal(value)},")
        lines.append("        },")
    lines.append("    ]")
    return "\n".join(lines)


def pascal(namespace: str) -> str:
    """``supply_chain`` -> ``SupplyChain`` (matches the existing adapter class names)."""
    return "".join(part.capitalize() for part in namespace.split("_"))


def render_synthetic(
    roles: VerticalRoles,
    config: RecommendConfig,
    site_def: dict[str, Any],
    asset_def: dict[str, Any],
) -> str:
    site_pk = f"{roles.site_type.lower()}-01"
    asset_pk = f"{roles.asset_type.lower()}-01"

    site_rec = _synth_object(site_def, roles.site_type, site_pk, {})
    asset_rec = _synth_object(
        asset_def, roles.asset_type, asset_pk, {roles.asset_site_ref: site_pk}
    )
    events = _synth_events(roles, config, asset_pk, site_pk)

    site_fn = f"{roles.site_type.lower()}_records"
    asset_fn = f"{roles.asset_type.lower()}_records"

    body = "\n\n\n".join(
        [
            _render_fn(
                site_fn,
                f"Return the synthetic {roles.site_type} records (geo-bearing).",
                [site_rec],
            ),
            _render_fn(asset_fn, f"Return the synthetic {roles.asset_type} records.", [asset_rec]),
            _render_fn(
                "operational_events",
                "Return the synthetic OperationalEvent records (baseline + breach).",
                events,
            ),
        ]
    )

    rendered = body  # used to decide which datetime symbols to import
    date_import = ", date" if "date(" in rendered else ""
    # Note: ``date(`` never matches inside ``datetime(`` (distinct prefixes).

    return (
        f'"""Deterministic synthetic dataset for the {roles.namespace} vertical '
        "(PLAN-0016 scaffold).\n\n"
        "Generated by ``vero-lite new-vertical``. No external I/O and no "
        "randomness — every\ncall returns the same data, so demos and tests are "
        "reproducible. Shapes match\n"
        f"``verticals/{roles.namespace}/ontology/{roles.namespace}_v0.yaml``.\n\n"
        "⚠ DRAFT FOR HUMAN REVIEW (ADR-0015 D5): these records are a minimal, "
        "auto-\ngenerated starting point — review + enrich them (domain-plausible "
        "names, a\nfuller timeline) before the demo. The breach event is the "
        "timeline's final\nbeat so real-time anchoring (PLAN-0015 D1) leaves "
        'nothing in the future.\n"""\n\n'
        "from __future__ import annotations\n\n"
        f"from datetime import UTC{date_import}, datetime\n"
        "from typing import Any\n\n\n"
        f"{body}\n\n\n"
        "OBJECT_SOURCES = {\n"
        f"    {roles.site_type!r}: {site_fn},\n"
        f"    {roles.asset_type!r}: {asset_fn},\n"
        "}\n"
    )


def render_adapter_init(roles: VerticalRoles) -> str:
    ns = roles.namespace
    cls = f"{pascal(ns)}SyntheticAdapter"
    return (
        f'"""{pascal(ns)} vertical — synthetic DataAdapter (PLAN-0016 new-vertical scaffold).\n\n'
        f"Generated by ``vero-lite new-vertical``. Structurally identical to the\n"
        "energy/supply_chain adapters; only the object sources differ (proof that a\n"
        'new vertical is "swap the ontology + adapter"). Serves the synthetic dataset\n'
        "in ``synthetic.py`` as raw object dicts and streams OperationalEvent dicts —\n"
        "including one breach the recommender escalates.\n\n"
        f"``register_{ns}_adapter`` registers an instance on the process-wide registry\n"
        '(OQ-6: explicit registration).\n"""\n\n'
        "from __future__ import annotations\n\n"
        "from collections.abc import AsyncIterator\n"
        "from datetime import datetime\n"
        "from typing import Any\n\n"
        "from services.engine import demo_events\n"
        "from services.engine.registry import registry\n"
        f"from verticals.{ns}.data_adapter import synthetic\n\n"
        f'_VERTICAL = "{ns}"\n\n\n'
        "def _operational_events() -> list[dict[str, Any]]:\n"
        '    """The per-process live OperationalEvent view (PLAN-0015 D1/D2).\n\n'
        "    Routes synthetic events through ``demo_events`` so real-time anchoring and\n"
        "    the execute-time recovery reading apply; with the anchor flag off and no\n"
        '    execution it equals ``synthetic.operational_events()`` (deterministic).\n    """\n'
        "    return demo_events.events(_VERTICAL, synthetic.operational_events)\n\n\n"
        "_OBJECT_SOURCES: dict[str, Any] = {\n"
        "    **synthetic.OBJECT_SOURCES,\n"
        '    "OperationalEvent": _operational_events,\n'
        "}\n\n\n"
        f"class {cls}:\n"
        f'    """Deterministic synthetic DataAdapter for the {ns} vertical.\n\n'
        "    Conforms structurally to ``services.engine.data_adapter.DataAdapter``.\n"
        "    No external I/O — every call returns the synthetic dataset, so demos\n"
        '    and tests are reproducible.\n    """\n\n'
        f'    vertical_name = "{ns}"\n\n'
        "    async def fetch_objects(\n"
        "        self,\n"
        "        object_type: str,\n"
        "        filter_expr: str | None = None,\n"
        "        limit: int = 1000,\n"
        "    ) -> list[dict[str, Any]]:\n"
        '        """Return synthetic object dicts for ``object_type`` (unknown -> empty)."""\n'
        "        source = _OBJECT_SOURCES.get(object_type)\n"
        "        if source is None:\n"
        "            return []\n"
        "        return source()[:limit]\n\n"
        "    async def fetch_links(\n"
        "        self,\n"
        "        link_type: str,\n"
        "        from_pk: str | None = None,\n"
        "        to_pk: str | None = None,\n"
        "    ) -> list[dict[str, Any]]:\n"
        '        """Return link dicts for ``link_type`` (Phase 2 synthetic: none)."""\n'
        "        return []\n\n"
        "    async def stream_events(\n"
        "        self,\n"
        "        event_type: str,\n"
        "        since: datetime | None = None,\n"
        "    ) -> AsyncIterator[dict[str, Any]]:\n"
        '        """Yield synthetic OperationalEvent dicts of ``event_type``."""\n'
        "        for event in _operational_events():\n"
        '            if event["event_type"] != event_type:\n'
        "                continue\n"
        '            if since is not None and event["occurred_at"] < since:\n'
        "                continue\n"
        "            yield event\n\n"
        "    async def health_check(self) -> dict[str, Any]:\n"
        '        """Report adapter status and the synthetic record counts."""\n'
        "        return {\n"
        '            "status": "ok",\n'
        '            "vertical": self.vertical_name,\n'
        '            "synthetic": True,\n'
        '            "object_counts": '
        "{name: len(src()) for name, src in _OBJECT_SOURCES.items()},\n"
        "        }\n\n\n"
        f"def register_{ns}_adapter() -> {cls}:\n"
        f'    """Register a fresh {cls} on the process-wide registry."""\n'
        f"    adapter = {cls}()\n"
        "    registry.register_adapter(adapter)\n"
        "    return adapter\n"
    )


def render_handlers(namespace: str) -> str:
    ns = namespace
    return (
        f'"""{pascal(ns)} vertical action handlers (PLAN-0016 new-vertical scaffold).\n\n'
        "Phase 2 ships a single no-op echo handler: it records the action and\n"
        "returns a receipt without performing real I/O. Real handlers land with\n"
        'the design partner.\n"""\n\n'
        "from __future__ import annotations\n\n"
        "from typing import Any\n\n"
        "from services.engine.actions import RecommendedAction\n"
        "from services.engine.registry import registry\n\n\n"
        "async def echo_handler(action: RecommendedAction) -> dict[str, Any]:\n"
        '    """No-op handler: echo the action back as an execution receipt."""\n'
        "    return {\n"
        '        "handler": "echo",\n'
        '        "executed": True,\n'
        '        "action_id": action.id,\n'
        '        "vertical": action.vertical,\n'
        '        "payload": action.handler_payload,\n'
        "    }\n\n\n"
        f"def register_{ns}_handlers() -> None:\n"
        f'    """Register the {ns} vertical\'s action handlers on the registry."""\n'
        f'    registry.register_handler("{ns}", "echo", echo_handler)\n'
    )


def render_package_init(namespace: str) -> str:
    return (
        f'"""{pascal(namespace)} vertical — generated by ``vero-lite new-vertical`` '
        '(PLAN-0016)."""\n'
    )


def render_env_block(roles: VerticalRoles, config: RecommendConfig, asset_pk_field: str) -> str:
    return "\n".join(
        [
            f"OCT_VERTICAL={roles.namespace}",
            f"OCT_RECOMMEND_THRESHOLD={config.threshold:g}",
            f"OCT_RECOMMEND_DIRECTION={config.direction}",
            f"OCT_RECOMMEND_ENTITY_TYPE={roles.asset_type}",
            f"OCT_RECOMMEND_ENTITY_ID_FIELD={asset_pk_field}",
            f'OCT_RECOMMEND_LABEL="{config.label}"',
            f"OCT_RECOVERY_VALUE={config.recovery_value:g}",
            f'OCT_RECOVERY_DESCRIPTION="{config.recovery_description}"',
        ]
    )


def render_readme(roles: VerticalRoles, config: RecommendConfig, env_block: str) -> str:
    ns = roles.namespace
    problem = config.problem or "_(describe the operation's problem statement here)_"
    decision = config.decision or "_(describe the corrective action here)_"
    return (
        f"# `{ns}/` — {pascal(ns)} vertical (PLAN-0016 Mirror demo)\n\n"
        "**Status:** Generated by `vero-lite new-vertical` — synthetic Tier-1 Mirror "
        "demo (ADR-0015 D1).\n"
        f"**Asset-role:** `{roles.asset_type}` · **Site-role:** `{roles.site_type}` "
        f"· **Breach direction:** `{config.direction}` threshold "
        f"`{config.threshold:g}{(' ' + config.unit) if config.unit else ''}`\n\n"
        "> ⚠ The synthetic dataset in `data_adapter/synthetic.py` is an "
        "auto-generated **draft for human review** (ADR-0015 D5). Review + enrich the "
        "records before any demo.\n\n"
        "## Problem\n\n"
        f"{problem}\n\n"
        "## Decision / action\n\n"
        f"{decision}\n\n"
        "## Run this vertical\n\n"
        "Set the env block (paste into your local `.env`) and boot `uvicorn`:\n\n"
        "```dotenv\n"
        f"{env_block}\n"
        "```\n"
    )


# --------------------------------------------------------------------------- #
# Registration code-mod (services/api/main.py)
# --------------------------------------------------------------------------- #

_REGISTRARS_DECL = "_VERTICAL_REGISTRARS"


def register_in_main(main_text: str, namespace: str) -> str:
    """Idempotently add the vertical's imports + a ``_VERTICAL_REGISTRARS`` row.

    Pure text transform (returns the new file text). A no-op when the vertical
    is already registered, so re-running ``new-vertical`` is safe.
    """
    ns = namespace
    adapter_import = f"from verticals.{ns}.data_adapter import register_{ns}_adapter"
    handlers_import = f"from verticals.{ns}.handlers import register_{ns}_handlers"
    row = f'    "{ns}": (register_{ns}_adapter, register_{ns}_handlers),'

    if adapter_import in main_text and row in main_text:
        return main_text

    lines = main_text.splitlines()

    # 1. Insert the two imports after the last ``from verticals.`` import.
    last_vertical_import = max(
        (i for i, ln in enumerate(lines) if ln.startswith("from verticals.")), default=-1
    )
    if last_vertical_import < 0:
        raise ScaffoldError("could not find the 'from verticals.' import block in main.py")
    inserts = [ln for ln in (adapter_import, handlers_import) if ln not in lines]
    for offset, ln in enumerate(inserts, start=1):
        lines.insert(last_vertical_import + offset, ln)

    # 2. Insert the registrar row before the dict's closing brace.
    decl_idx = next((i for i, ln in enumerate(lines) if ln.startswith(_REGISTRARS_DECL)), None)
    if decl_idx is None:
        raise ScaffoldError(f"could not find {_REGISTRARS_DECL} in main.py")
    close_idx = next((i for i in range(decl_idx, len(lines)) if lines[i] == "}"), None)
    if close_idx is None:
        raise ScaffoldError(f"could not find the closing brace of {_REGISTRARS_DECL}")
    if row not in lines:
        lines.insert(close_idx, row)

    return "\n".join(lines) + ("\n" if main_text.endswith("\n") else "")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #


def _ontology_path(repo_root: Path, namespace: str) -> Path:
    return repo_root / "verticals" / namespace / "ontology" / f"{namespace}_v0.yaml"


def _scaffold_targets(repo_root: Path, namespace: str) -> dict[str, Path]:
    base = repo_root / "verticals" / namespace
    return {
        "package_init": base / "__init__.py",
        "adapter_init": base / "data_adapter" / "__init__.py",
        "synthetic": base / "data_adapter" / "synthetic.py",
        "handlers": base / "handlers.py",
        "readme": base / "README.md",
    }


def scaffold_vertical(
    namespace: str,
    config: RecommendConfig,
    *,
    repo_root: Path | None = None,
    force: bool = False,
) -> ScaffoldResult:
    """Scaffold ``verticals/<namespace>/`` from its ontology + ``config``.

    Preconditions: a valid OCT-shaped ontology at
    ``verticals/<namespace>/ontology/<namespace>_v0.yaml``. Refuses to clobber
    existing scaffold files unless ``force``. Returns a :class:`ScaffoldResult`.
    """
    root = repo_root or Path.cwd()
    config.validate()
    if not _NAMESPACE_RE.match(namespace):
        raise ScaffoldError(
            f"namespace {namespace!r} invalid; expected lowercase snake_case " "(^[a-z][a-z0-9_]*$)"
        )

    yaml_path = _ontology_path(root, namespace)
    if not yaml_path.is_file():
        raise ScaffoldError(
            f"ontology not found at {yaml_path} — author the ontology first "
            "(the partner-input package), then run new-vertical"
        )

    targets = _scaffold_targets(root, namespace)
    existing = [p for p in targets.values() if p.exists()]
    if existing and not force:
        names = ", ".join(str(p.relative_to(root)) for p in existing)
        raise ScaffoldError(
            f"refusing to clobber existing scaffold files: {names} (use --force to overwrite)"
        )

    # Validate + generate (AUTO, unchanged) — bail before writing if the
    # ontology is broken (operator never sees a half-scaffolded vertical).
    if ontology_validator.main([str(yaml_path)]) != 0:
        raise ScaffoldError(f"ontology validation failed for {yaml_path}")

    doc = code_generator.load_doc(yaml_path)
    roles = detect_roles(doc)
    if roles.namespace != namespace:
        raise ScaffoldError(
            f"ontology namespace {roles.namespace!r} != target vertical {namespace!r}; "
            "they must match (verticals/<ns>/ontology/<ns>_v0.yaml with namespace: <ns>)"
        )
    object_types = _object_types(doc)
    site_def = object_types[roles.site_type]
    asset_def = object_types[roles.asset_type]
    asset_pk_field = str(asset_def.get("primary_key", "asset_id"))

    generated_dir = root / "verticals" / namespace / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    generated = code_generator.generate_all(yaml_path, generated_dir)

    env_block = render_env_block(roles, config, asset_pk_field)
    files = {
        targets["package_init"]: render_package_init(namespace),
        targets["adapter_init"]: render_adapter_init(roles),
        targets["synthetic"]: render_synthetic(roles, config, site_def, asset_def),
        targets["handlers"]: render_handlers(namespace),
        targets["readme"]: render_readme(roles, config, env_block),
    }
    written: list[Path] = []
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(path)

    registered = False
    main_path = root / "services" / "api" / "main.py"
    if main_path.is_file():
        original = main_path.read_text(encoding="utf-8")
        new_text = register_in_main(original, namespace)
        if new_text != original:
            main_path.write_text(new_text, encoding="utf-8")
        registered = True

    return ScaffoldResult(
        namespace=namespace,
        roles=roles,
        written=written,
        generated=generated,
        env_block=env_block,
        registered=registered,
    )
