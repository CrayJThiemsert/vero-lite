"""Ontology emitter + the invoked floor (PLAN-0091 Step 2, oracle AC-3).

Two halves, deliberately split by who decides:

* **Mechanical.** The 6-object OCT skeleton and all 7 link_types come from the
  grammar alone. Object roles, property shapes, foreign keys and cardinalities
  are fixed by ADR-008; nothing about them is a customer question, so nothing
  about them is asked.
* **Judgment.** The Asset noun, the Site noun, the per-entity band property and
  the ``RecommendedAction.action_type`` vocabulary come **only from confirmed
  intake**. :func:`emit_ontology` raises rather than defaulting: an ontology
  that guessed its own action vocabulary would be a governance value the LLM
  never had a write path to, arriving anyway through a default.

**The invoked floor.** :func:`run_floor` shells the emitted YAML through the
shipped ``validate`` + ``generate`` commands rather than re-implementing their
checks (ledger row 10: invoke, never re-implement). Those commands resolve paths
CWD-relative with no root override (``cli.py`` ``_yaml_path`` / ``_output_dir``,
kept as-is by ADR-0015 D2), so the floor runs under a ``chdir`` into the scratch
tree — the same shape as the shipped ``staged_repo`` test fixture.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from services.engine.scaffolder.intake import IntakeRecord

# ruamel, not PyYAML: it is what the shipped loaders already use
# (`ontology_validator.py`, `procedures/spec.py`), so the emitter writes with the
# same library that will read it back — and no new dependency (or stub) enters
# the tree for a file format the repo already handles.
_YAML = YAML()
_YAML.default_flow_style = False
_YAML.allow_unicode = True
_YAML.width = 100

# The judgment slots this emitter refuses to proceed without. Each is a customer
# vocabulary call: no default is safe, because a wrong default is indistinguishable
# from an answer in the emitted artifact.
REQUIRED_JUDGMENTS: tuple[str, ...] = (
    "ontology.asset_noun",
    "ontology.site_noun",
    "ontology.band_property",
    "ontology.action_types",
)


class OntologyEmissionError(RuntimeError):
    """Raised when emission is attempted with a judgment slot unconfirmed.

    Carries the open slot ids so the caller can print the queue rather than a
    bare failure — the AC-3 behaviour is "stop with the open queue printed", not
    "stop".
    """

    def __init__(self, open_slots: list[str]) -> None:
        self.open_slots = open_slots
        super().__init__("ontology emission needs confirmed intake for: " + ", ".join(open_slots))


def _key(noun: str) -> str:
    """The snake_case key stem for an object noun (``Truck`` -> ``truck``)."""
    out: list[str] = []
    for i, ch in enumerate(noun):
        if ch.isupper() and i > 0:
            out.append("_")
        out.append(ch.lower())
    return "".join(out)


def _split_list(value: str) -> list[str]:
    """Split an operator's comma/space separated answer into a clean list."""
    return [part.strip() for part in value.replace("\n", ",").split(",") if part.strip()]


def emit_ontology(record: IntakeRecord) -> dict[str, Any]:
    """Build the ontology document for ``record``.

    Raises :class:`OntologyEmissionError` if any judgment slot is unanswered or
    unconfirmed — the AC-3 "refuses to guess where the ledger says judgment
    lives" property, enforced here rather than at the CLI so every caller
    inherits it.
    """
    missing = [slot for slot in REQUIRED_JUDGMENTS if record.confirmed_value(slot) is None]
    if missing:
        raise OntologyEmissionError(missing)

    asset = str(record.confirmed_value("ontology.asset_noun"))
    site = str(record.confirmed_value("ontology.site_noun"))
    band_property = str(record.confirmed_value("ontology.band_property"))
    action_types = _split_list(str(record.confirmed_value("ontology.action_types")))

    a, s = _key(asset), _key(site)
    asset_pk, site_pk = f"{a}_id", f"{s}_id"

    object_types: dict[str, Any] = {
        asset: {
            "primary_key": asset_pk,
            "title_key": "name",
            "description": f"The managed operational unit (the monitored Asset) — {asset}.",
            "properties": {
                asset_pk: {"type": "string", "required": True},
                "name": {"type": "string", "required": True},
                band_property: {
                    "type": "float",
                    "description": (
                        "This entity's OWN per-entity band (ADR-016 FKP amendment) — the judge "
                        "compares each row against this field, not a shared scalar."
                    ),
                },
                "status": {"type": "enum", "values": ["active", "inactive"]},
                "site_id": {"type": "ref", "target": site, "required": True},
            },
        },
        site: {
            "primary_key": site_pk,
            "title_key": "name",
            "description": f"A location the {asset} belongs to or is routed to.",
            "properties": {
                site_pk: {"type": "string", "required": True},
                "name": {"type": "string", "required": True},
                "lat": {"type": "float"},
                "lng": {"type": "float"},
            },
        },
        "OperationalEvent": {
            "primary_key": "event_id",
            "description": f"Time-stamped signal concerning a {asset} at a {site}.",
            "properties": {
                "event_id": {"type": "string", "required": True},
                "event_type": {"type": "enum", "values": ["reading", "transition", "alarm"]},
                "severity": {"type": "enum", "values": ["info", "warn", "error", "critical"]},
                "measured_value": {"type": "float"},
                "unit": {"type": "string"},
                "description": {"type": "string"},
                "occurred_at": {"type": "timestamp", "required": True},
                f"{a}_id": {"type": "ref", "target": asset},
                "site_id": {"type": "ref", "target": site},
            },
        },
        "Alert": {
            "primary_key": "alert_id",
            "title_key": "title",
            "description": "An actionable notification derived from one or more OperationalEvents.",
            "properties": {
                "alert_id": {"type": "string", "required": True},
                "title": {"type": "string", "required": True},
                "urgency": {"type": "enum", "values": ["low", "medium", "high", "critical"]},
                "status": {"type": "enum", "values": ["open", "acknowledged", "resolved"]},
                "opened_at": {"type": "timestamp", "required": True},
                "resolved_at": {"type": "timestamp"},
                "reasoning": {"type": "string"},
            },
        },
        "RecommendedAction": {
            "primary_key": "action_id",
            "description": (
                "An AI-proposed decision awaiting human approval; mirrors the ADR-007 D2 "
                "runtime envelope."
            ),
            "properties": {
                "action_id": {"type": "string", "required": True},
                # The closed action vocabulary IS the LLM's proposal menu
                # (handlers.py) — which is exactly why it is operator-authored.
                "action_type": {"type": "enum", "values": action_types},
                "confidence_score": {"type": "float"},
                "status": {
                    "type": "enum",
                    "values": ["proposed", "approved", "rejected", "executed"],
                },
                "parameters": {"type": "json"},
                "alert_id": {"type": "ref", "target": "Alert", "required": True},
                f"target_{a}_id": {"type": "ref", "target": asset},
            },
        },
        "AlertEventLink": {
            "primary_key": "link_id",
            "description": (
                "Join object linking an Alert to the OperationalEvent(s) that triggered it "
                "(N:M via composition per ADR-008 D4)."
            ),
            "properties": {
                "link_id": {"type": "string", "required": True},
                "created_at": {"type": "timestamp", "required": True},
                "alert_id": {"type": "ref", "target": "Alert", "required": True},
                "event_id": {"type": "ref", "target": "OperationalEvent", "required": True},
            },
        },
    }

    link_types: dict[str, Any] = {
        f"{a}_at_{s}": {
            "from": asset,
            "to": site,
            "cardinality": "many_to_one",
            "foreign_key": f"{asset}.site_id -> {site}.{site_pk}",
        },
        f"event_for_{a}": {
            "from": "OperationalEvent",
            "to": asset,
            "cardinality": "many_to_one",
            "foreign_key": f"OperationalEvent.{a}_id -> {asset}.{asset_pk}",
        },
        f"event_at_{s}": {
            "from": "OperationalEvent",
            "to": site,
            "cardinality": "many_to_one",
            "foreign_key": f"OperationalEvent.site_id -> {site}.{site_pk}",
        },
        "action_addresses_alert": {
            "from": "RecommendedAction",
            "to": "Alert",
            "cardinality": "many_to_one",
            "foreign_key": "RecommendedAction.alert_id -> Alert.alert_id",
        },
        f"action_target_{a}": {
            "from": "RecommendedAction",
            "to": asset,
            "cardinality": "many_to_one",
            "foreign_key": f"RecommendedAction.target_{a}_id -> {asset}.{asset_pk}",
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
        "namespace": record.namespace,
        "object_types": object_types,
        "link_types": link_types,
    }


def write_ontology(record: IntakeRecord, root: Path) -> Path:
    """Write the emitted ontology under ``root`` and return its path.

    ``root`` is an explicit argument, never the CWD: the tool emits into a
    scratch tree, and a CWD-relative write would silently target the repo.
    """
    path = root / "verticals" / record.namespace / "ontology" / f"{record.namespace}_v0.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        _YAML.dump(emit_ontology(record), stream)
    return path


@contextmanager
def _chdir(target: Path) -> Iterator[None]:
    """Scoped chdir — the shipped `staged_repo` shape, restored in a finally."""
    old = Path.cwd()
    os.chdir(target)
    try:
        yield
    finally:
        os.chdir(old)


def run_floor(namespace: str, root: Path) -> int:
    """Invoke the shipped ``validate`` + ``generate`` floor against ``root``.

    Returns the exit code the floor produced: 0 means the emitted ontology
    passes the same L1+L2 validation and codegen every shipped vertical passes.
    The commands are INVOKED, never re-implemented — a re-implementation would
    drift from the floor it claims to represent, which is the whole point of
    row 10 of the ledger.
    """
    from services.engine import code_generator, ontology_validator

    with _chdir(root):
        yaml_path = f"verticals/{namespace}/ontology/{namespace}_v0.yaml"
        code = ontology_validator.main([yaml_path])
        if code != 0:
            return code
        code_generator.generate_all(Path(yaml_path), Path(f"verticals/{namespace}/generated"))
    return 0
