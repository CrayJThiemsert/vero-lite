"""Package emitter — rows 1/3/4/5 + the synthetic skeleton + the README (Step 3, AC-4).

What makes this step more than templating is the **no-fabricated-numbers**
property. A scaffolder that invents plausible demo numbers produces a package
that looks finished and is quietly wrong: the operator cannot tell a customer
answer from the tool's guess, and neither can the next reader. So every numeric
literal the emitter writes into ``synthetic.py`` must either

* carry a ``# from intake: <slot_id>`` trace back to a confirmed answer, or
* carry the ``# GUESS — รอแก้`` marker,

and :func:`untraced_numerics` is the scanner that makes "must not fabricate;
ask" **falsifiable** rather than aspirational — it is what the AC-4 test runs.

The README follows the same discipline in prose: the mechanical parts (env
block, the step walk-through) are generated, and the human parts (the problem
statement, and the **"stated but NOT enforced" register** fed by the intake
queue's schemaless sub-slots) are emitted as explicit stubs. An unanswered
customer fact appears as a visible gap, never as silence.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from services.engine.scaffolder.intake import (
    IntakeRecord,
    SlotKind,
    required_slots,
)

GUESS_MARKER = "# GUESS — รอแก้"
TRACE_PREFIX = "# from intake:"
STRUCTURAL_MARKER = "# structural:"
"""For a numeric literal that is NOT a data value (a loop index, an offset).
Accepted by the scanner but still visible in review — the contract is "every
number is accounted for", which is stronger than "every number I classified as
data is accounted for", and it leaves no judgement call inside the scanner."""

_ACCEPTED = (TRACE_PREFIX, GUESS_MARKER, STRUCTURAL_MARKER)


def untraced_numerics(source: str) -> list[str]:
    """Lines carrying a numeric literal with no trace, guess, or structural marker.

    The AC-4 oracle. Numeric literals are found via the **AST**, not a regex:
    a regex over source lines also matches digits inside strings, docstrings and
    identifiers (``"site-1"``, ``PLAN-0091``, ``field_2``), which would make the
    scanner noisy enough that a real offender hides in the noise. The AST sees
    exactly the numbers the emitter actually wrote as numbers.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:  # a broken emission is a louder failure elsewhere
        return ["<unparseable>"]

    lines = source.splitlines()
    offenders: list[str] = []
    seen: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or isinstance(node.value, bool):
            continue
        if not isinstance(node.value, int | float):
            continue
        lineno = node.lineno
        if lineno in seen:
            continue
        seen.add(lineno)
        raw = lines[lineno - 1]
        if any(marker in raw for marker in _ACCEPTED):
            continue
        offenders.append(raw.strip())
    return offenders


def _fixture_value(record: IntakeRecord, slot_id: str, fallback: str) -> tuple[str, str]:
    """Return ``(value, annotation)`` for a fixture slot.

    A confirmed answer is traced to its slot; anything else falls back to a
    placeholder that is MARKED, so the distinction between "the customer said
    six" and "the tool needed a number" survives into the emitted file.
    """
    value = record.confirmed_value(slot_id)
    if value is None:
        return fallback, f"  {GUESS_MARKER} ({slot_id} unanswered)"
    answer = record.answered()[slot_id]
    if answer.guess:
        return value, f"  {GUESS_MARKER} ({slot_id}, operator-marked)"
    return value, f"  {TRACE_PREFIX} {slot_id}"


def registrar_name(namespace: str, suffix: str) -> str:
    """The registrar-name convention the wire-writer and the daemon both expect.

    Kept here as one function so Step 5's registrar maps and this package's
    emitted function names cannot disagree — a mismatch would register nothing
    and surface only as a runtime RegistryError.
    """
    return f"register_{namespace}_{suffix}"


def emit_handlers(record: IntakeRecord, ontology_doc: dict[str, Any]) -> str:
    """Row 3 — ``handlers.py``. ``ACTION_TYPES`` IS the ontology enum, by construction."""
    ns = record.namespace
    action_types = ontology_doc["object_types"]["RecommendedAction"]["properties"]["action_type"][
        "values"
    ]
    entries = "\n".join(f'    "{name}",' for name in action_types)
    descriptions = "\n".join(
        f'    "{name}": "TODO — describe when the operator should pick {name}.",'
        for name in action_types
    )
    return f'''"""{ns} vertical action handlers (scaffolded — PLAN-0091).

Every handler is a **no-op receipt**: it records the action and returns a receipt
without performing real I/O. Real integration lands with the design partner.

``ACTION_TYPES`` mirrors the ontology ``RecommendedAction.action_type`` enum —
the enum IS the LLM's proposal menu, so the two must never drift.
"""

from __future__ import annotations

from typing import Any

from services.engine.actions import RecommendedAction
from services.engine.registry import Handler, registry

ACTION_TYPES: tuple[str, ...] = (
{entries}
)
"""The {ns} ontology ``RecommendedAction.action_type`` enum, registered as no-op stubs."""

ACTION_DESCRIPTIONS: dict[str, str] = {{
    "echo": "Diagnostic no-op — record the action without performing anything.",
{descriptions}
}}
"""Per-handler when-to-pick descriptions surfaced to the reactive judgment prompt."""


async def echo_handler(action: RecommendedAction) -> dict[str, Any]:
    """No-op handler: echo the action back as an execution receipt."""
    return {{
        "handler": "echo",
        "executed": True,
        "action_id": action.id,
        "vertical": action.vertical,
        "payload": action.handler_payload,
    }}


def _stub_action_handler(name: str) -> Handler:
    """Build a named no-op action handler — the named-action equivalent of echo."""

    async def handler(action: RecommendedAction) -> dict[str, Any]:
        return {{
            "handler": name,
            "executed": True,
            "stub": True,
            "action_id": action.id,
            "vertical": action.vertical,
            "payload": action.handler_payload,
        }}

    handler.__name__ = f"{{name}}_handler"
    return handler


def {registrar_name(ns, "handlers")}() -> None:
    """Register ``echo`` + every :data:`ACTION_TYPES` entry on the process registry."""
    registry.register_handler("{ns}", "echo", echo_handler)
    for name in ACTION_TYPES:
        registry.register_handler("{ns}", name, _stub_action_handler(name))
'''


def emit_synthetic(record: IntakeRecord, ontology_doc: dict[str, Any]) -> str:
    """Row 6 — the ``synthetic.py`` skeleton. Every number traced or marked."""
    ns = record.namespace
    asset = next(
        name
        for name, spec in ontology_doc["object_types"].items()
        if "site_id" in spec.get("properties", {}) and name != "OperationalEvent"
    )
    site = ontology_doc["object_types"][asset]["properties"]["site_id"]["target"]
    band_property = str(record.confirmed_value("ontology.band_property"))
    asset_pk = ontology_doc["object_types"][asset]["primary_key"]
    site_pk = ontology_doc["object_types"][site]["primary_key"]

    count, count_note = _fixture_value(record, "fixture.asset_count", "3")
    band, band_note = _fixture_value(record, "fixture.band_value", "20000")
    breach, breach_note = _fixture_value(record, "fixture.breach_value", "48000")
    normal, normal_note = _fixture_value(record, "fixture.normal_value", "1200")

    return f'''"""{ns} synthetic dataset (scaffolded — PLAN-0091).

Deterministic demo data. **Every numeric literal below is either traced to a
confirmed intake answer ({TRACE_PREFIX} ...) or marked {GUESS_MARKER}** — the
scaffolder does not invent numbers, because an invented number is
indistinguishable from a customer answer once it is on disk.

Events are emitted latest-per-asset: the newest event per {asset} is the one the
judge reads, so the ordering here is load-bearing, not cosmetic.
"""

from __future__ import annotations

from typing import Any

_ASSET_COUNT = {count}{count_note}
_BAND_VALUE = {band}{band_note}
_BREACH_VALUE = {breach}{breach_note}
_NORMAL_VALUE = {normal}{normal_note}


def {_key_fn(site)}() -> list[dict[str, Any]]:
    """The demo {site} rows."""
    return [{{"{site_pk}": "site-1", "name": "TODO — the customer's own site name"}}]


def {_key_fn(asset)}() -> list[dict[str, Any]]:
    """The demo {asset} rows — each carrying its OWN per-entity band."""
    return [
        {{
            "{asset_pk}": f"asset-{{i}}",
            "name": f"TODO-name-{{i}}",
            "{band_property}": _BAND_VALUE,
            "status": "active",
            "site_id": "site-1",
        }}
        for i in range(_ASSET_COUNT)
    ]


def operational_events() -> list[dict[str, Any]]:
    """Latest-per-asset event rows: one breaching, the rest normal."""
    rows: list[dict[str, Any]] = []
    for i in range(_ASSET_COUNT):
        breaching = i == 0  {STRUCTURAL_MARKER} the first asset carries the demo breach
        rows.append(
            {{
                "event_id": f"evt-{{i}}",
                "event_type": "reading",
                "severity": "warn" if breaching else "info",
                "measured_value": _BREACH_VALUE if breaching else _NORMAL_VALUE,
                "unit": "TODO — the customer's unit",
                "description": "TODO — describe the reading in the customer's words",
                "occurred_at": "TODO — set by the demo-event anchor",
                "{_key(asset)}_id": f"asset-{{i}}",
                "site_id": "site-1",
            }}
        )
    return rows


OBJECT_SOURCES = {{
    "{site}": {_key_fn(site)},
    "{asset}": {_key_fn(asset)},
    "OperationalEvent": operational_events,
}}
'''


def emit_readme(record: IntakeRecord) -> str:
    """Row 14 — the README: mechanical parts generated, human parts visibly stubbed."""
    ns = record.namespace
    checklist = required_slots()
    answered = record.answered()

    register_lines: list[str] = []
    for slot in checklist:
        if slot.kind is not SlotKind.UNMODELLED:
            continue
        answer = answered.get(slot.slot_id)
        if answer is not None and answer.confirmed:
            register_lines.append(
                f"- **{slot.slot_id}** — the customer stated `{answer.value}`. "
                f"**No schema field exists for it**, so nothing enforces it. "
                f"({slot.question})"
            )
        else:
            register_lines.append(
                f"- **{slot.slot_id}** — not answered, and there is no schema field for it "
                f"either. ({slot.question})"
            )
    register = "\n".join(register_lines) or "- (none)"

    open_slots = [
        slot.slot_id
        for slot in checklist
        if slot.slot_id not in answered or not answered[slot.slot_id].confirmed
    ]
    open_block = "\n".join(f"- {sid}" for sid in open_slots) or "- (none)"

    return f"""# {ns}

> Scaffolded by `vero-lite scaffold` (PLAN-0091). Sections marked **TODO** are
> human work the tool deliberately did not guess.

## Problem statement

TODO — the customer's problem in their own words.

## Stated but NOT enforced

These are facts the customer gave us that the typed models have **no field
for**. They are recorded here precisely because nothing in the running system
will check them — a reader who assumes "if it is not in the YAML the customer
never said it" would be wrong.

{register}

## Still open

{open_block}

## Environment

```
OCT_VERTICAL={ns}
```

## The governed walk-through

1. `intake` — read the latest event per asset.
2. `judge` — compare each asset against its OWN per-entity band.
3. `reshape` — derive the governed spend from the breach.
4. `rule_gate` — the customer's own compliance rule.
5. `approve` — the tiered authority ladder (human gate; separation of duties).
6. `fulfill` — the approved write.
"""


def _key(noun: str) -> str:
    out: list[str] = []
    for i, ch in enumerate(noun):
        if ch.isupper() and i > 0:
            out.append("_")
        out.append(ch.lower())
    return "".join(out)


def _key_fn(noun: str) -> str:
    """The synthetic source-function name for an object noun (``Depot`` -> ``depots``)."""
    return f"{_key(noun)}s"


def emit_package(record: IntakeRecord, ontology_doc: dict[str, Any]) -> dict[str, str]:
    """The full emitted file set, keyed by path relative to ``verticals/<ns>/``."""
    ns = record.namespace
    return {
        "__init__.py": f'"""{ns} vertical (scaffolded — PLAN-0091)."""\n',
        "handlers.py": emit_handlers(record, ontology_doc),
        "data_adapter/__init__.py": _emit_adapter(ns),
        "data_adapter/synthetic.py": emit_synthetic(record, ontology_doc),
        "README.md": emit_readme(record),
    }


def _emit_adapter(ns: str) -> str:
    """Row 4 — the adapter. Structurally identical across verticals by design."""
    return f'''"""{ns} vertical — synthetic DataAdapter (scaffolded — PLAN-0091).

Structurally identical to every shipped vertical's adapter; only the object
sources differ, which is the "swap the ontology + adapter" claim made concrete.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from services.engine import demo_events
from services.engine.registry import registry
from verticals.{ns}.data_adapter import synthetic

_VERTICAL = "{ns}"


def _operational_events() -> list[dict[str, Any]]:
    return demo_events.events(_VERTICAL, synthetic.operational_events)


_OBJECT_SOURCES = {{
    **synthetic.OBJECT_SOURCES,
    "OperationalEvent": _operational_events,
}}


class SyntheticAdapter:
    """Deterministic synthetic DataAdapter — no external I/O."""

    vertical_name = _VERTICAL

    async def fetch_objects(self, object_type: str) -> list[dict[str, Any]]:
        source = _OBJECT_SOURCES.get(object_type)
        return list(source()) if source else []

    async def stream_events(self) -> AsyncIterator[dict[str, Any]]:
        for event in _operational_events():
            yield event


def {registrar_name(ns, "adapter")}() -> None:
    """Register the adapter on the process-wide registry (OQ-6: explicit)."""
    registry.register_adapter(_VERTICAL, SyntheticAdapter())
'''


def write_package(record: IntakeRecord, ontology_doc: dict[str, Any], root: Path) -> list[Path]:
    """Write the package under ``root/verticals/<ns>/`` and return the paths written."""
    base = root / "verticals" / record.namespace
    written: list[Path] = []
    for rel, content in emit_package(record, ontology_doc).items():
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written
