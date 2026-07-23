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

from services.engine.procedures.spec import StepKind
from services.engine.scaffolder.intake import (
    IntakeRecord,
    SlotKind,
    required_slots,
    spine_steps,
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

    # Read off the emitted ontology rather than re-deriving from the record, so the
    # two files cannot disagree. They previously could: `name` and `status: active`
    # were hardcoded here, and an operator-chosen title_key (the donor's `plate`) or
    # status vocabulary would have produced synthetic rows missing the ontology's own
    # REQUIRED title column.
    asset_title = str(ontology_doc["object_types"][asset]["title_key"])
    site_title = str(ontology_doc["object_types"][site]["title_key"])
    asset_status = str(ontology_doc["object_types"][asset]["properties"]["status"]["values"][0])

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
    return [{{"{site_pk}": "site-1", "{site_title}": "TODO — the customer's own site name"}}]


def {_key_fn(asset)}() -> list[dict[str, Any]]:
    """The demo {asset} rows — each carrying its OWN per-entity band."""
    return [
        {{
            "{asset_pk}": f"asset-{{i}}",
            "{asset_title}": f"TODO-{asset_title}-{{i}}",
            "{band_property}": _BAND_VALUE,
            "status": "{asset_status}",
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


_FACTORY_SLOTS: dict[StepKind, str] = {
    StepKind.QUERY: """            StepKind.QUERY: QueryStepExecutor(
                adapter=adapter, object_type_names=object_type_names, meta=meta
            ),""",
    StepKind.EVALUATE: """            StepKind.EVALUATE: GovernanceEvaluateExecutor(
                base=EvaluateStepExecutor()  # in_file threshold_field band — no env wrapper
            ),""",
    StepKind.ACTION: """            StepKind.ACTION: GovernanceActionExecutor(
                base=ActionStepExecutor(client_factory=advisory_stub_factory),
                principals=principals,
                sod_steps=sod_steps,
                # Trace-only, never-raise gate advisory (ADR-0030 D5) — the fleet donor's
                # one structural addition over the building_materials template.
                advisory_builder=GateAdvisoryBuilder(),
            ),""",
    StepKind.TRANSFORM: """            StepKind.TRANSFORM: TransformStepExecutor(),""",
}
"""The executor body per :class:`StepKind`, copied from the shipped donor factories.

Only the kinds the spine actually uses are emitted (see :func:`factory_step_kinds`),
which is what "StepKind slots computed from the spine" means: a spine that grew or
lost a kind changes the emitted factory, rather than the factory silently pinning a
shape the spine no longer has."""

_FACTORY_SLOT_ORDER: tuple[StepKind, ...] = (
    StepKind.QUERY,
    StepKind.EVALUATE,
    StepKind.ACTION,
    StepKind.TRANSFORM,
)
"""Emission order — fixed, so the output is deterministic regardless of spine order."""


def factory_step_kinds() -> list[StepKind]:
    """The StepKind slots the emitted factory must map, DERIVED from the row-11 spine.

    Derived rather than hardcoded for the same reason the donor derives ``sod_steps``
    from the spec: a hardcoded copy is a second source of truth that drifts silently.
    An unmapped StepKind is not a lint error — it is a run that dies at dispatch.
    """
    kinds = {step.kind for step in spine_steps()}
    return [kind for kind in _FACTORY_SLOT_ORDER if kind in kinds]


def emit_procedures_factory(ns: str) -> str:
    """Row 7/9 — the procedure-executor factory the wire-writer registers.

    Without this file the scaffolded package is **not loadable**: ``wire.py`` writes a
    registrar entry pointing at ``verticals.<ns>.procedures_factory``, so the emitted
    package referenced a module that was never written. ``discover_and_register``
    registers adapters and handlers only (OQ-6), so the HTTP run/resume surface 409s
    until a vertical registers a factory explicitly — this is that registration.
    """
    slots = "\n".join(_FACTORY_SLOTS[kind] for kind in factory_step_kinds())
    return f'''"""The deterministic ``{ns}`` procedure-executor factory (scaffolded — PLAN-0091).

``discover_and_register`` registers adapters + handlers only (OQ-6), so the HTTP
run/resume surface 409s ("no procedure-executor factory") until a vertical registers
one explicitly. This is that registration for ``{ns}``, wired active-vertical-scoped
at API startup (``services/api/main.py``).

Every slot is a wrapper that governs the step it owns and falls through untouched for
the rest. ``sod_steps`` is DERIVED from the spec's own ``separation_of_duties``
constraints, not hardcoded — a renamed step cannot silently drop the ``sod_required``
flag. Deterministic and host-state-free end to end (CLAUDE.md §8): synthetic adapter,
pure band math, pure AT-2 resolution, stubbed advisory prose. Idempotent: a no-op when
a ``{ns}`` factory is already registered.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from services.engine.ontology_meta import load_ontology_meta
from services.engine.procedures.action_step import ActionStepExecutor
from services.engine.procedures.advisory_stub import advisory_stub_factory
from services.engine.procedures.evaluate_step import EvaluateStepExecutor
from services.engine.procedures.gate_advisory import GateAdvisoryBuilder
from services.engine.procedures.governance_step import (
    GovernanceActionExecutor,
    GovernanceEvaluateExecutor,
)
from services.engine.procedures.orchestrator import StepExecutor
from services.engine.procedures.query_step import QueryStepExecutor
from services.engine.procedures.spec import Person, StepKind, load_procedures
from services.engine.procedures.transform_step import TransformStepExecutor
from services.engine.registry import RegistryError, registry

_VERTICAL = "{ns}"


def _sod_steps(procedures: Any) -> frozenset[str]:
    """Every SoD-constrained step across the vertical's procedures — DERIVED, never
    hardcoded (the ``sod_required`` flag cannot drift when a step is renamed)."""
    return frozenset(
        step_id
        for procedure in procedures
        for constraint in procedure.separation_of_duties
        for step_id in constraint.distinct_steps
    )


async def {registrar_name(ns, "procedure_executors")}() -> None:
    """Register the deterministic ``{ns}`` procedure-executor factory.

    See module docstring."""
    try:
        registry.get_procedure_executors(_VERTICAL)
        return  # already registered — idempotent
    except RegistryError:
        pass

    # The registry's adapter, not a fresh construction: the lifespan warms it
    # (``fetch_objects("OperationalEvent")``) so the demo time-anchor is process-stable.
    adapter = registry.get_adapter(_VERTICAL)
    meta = load_ontology_meta(_VERTICAL)
    object_type_names = frozenset(object_type.name for object_type in meta.object_types)

    spec = load_procedures(_VERTICAL)
    principals: list[Person] = list(spec.principals)
    sod_steps = _sod_steps(spec.procedures)

    def factory() -> Mapping[StepKind, StepExecutor]:
        # Built fresh per run/resume request (the registry Step-2 contract — a stateful
        # executor must never leak across requests); adapter + meta + principals are
        # immutable read-only data captured once at registration.
        return {{
{slots}
        }}

    registry.register_procedure_executors(_VERTICAL, factory)
'''


def emit_package(record: IntakeRecord, ontology_doc: dict[str, Any]) -> dict[str, str]:
    """The full emitted file set, keyed by path relative to ``verticals/<ns>/``."""
    ns = record.namespace
    return {
        "__init__.py": f'"""{ns} vertical (scaffolded — PLAN-0091)."""\n',
        "handlers.py": emit_handlers(record, ontology_doc),
        "procedures_factory.py": emit_procedures_factory(ns),
        "data_adapter/__init__.py": _emit_adapter(ns),
        "data_adapter/synthetic.py": emit_synthetic(record, ontology_doc),
        "README.md": emit_readme(record),
    }


def class_prefix(namespace: str) -> str:
    """``fleet_maintenance`` -> ``FleetMaintenance`` — the adapter class-name convention.

    Kept beside :func:`registrar_name` for the same reason: the emitted class name
    and the emitted registrar body must not be able to disagree.
    """
    return "".join(part.capitalize() for part in namespace.split("_"))


def _emit_adapter(ns: str) -> str:
    """Row 4 — the adapter. Structurally identical across verticals by design.

    **This is the row the ledger claims byte-equality for**, so it is emitted as a
    literal namespace-swap of the shipped donor rather than a simplified lookalike.
    That is not cosmetic: the earlier short form diverged from the
    :class:`~services.engine.data_adapter.DataAdapter` protocol on every method
    (``fetch_objects`` without ``filter_expr``/``limit``, ``stream_events`` without
    ``event_type``/``since``, no ``fetch_links``, no ``health_check``) and its
    registrar called ``registry.register_adapter`` with **two** arguments against a
    one-argument signature — so the scaffolded vertical raised ``TypeError`` the
    moment anything imported and called it. No test caught that, because the package
    tests only ``ast.parse`` the emitted text; they never execute it.
    """
    prefix = class_prefix(ns)
    return f'''"""{ns} vertical — synthetic DataAdapter (scaffolded — PLAN-0091).

Structurally identical to every shipped vertical's adapter; only the object
sources differ, which is the "swap the ontology + adapter" claim made concrete.

``{registrar_name(ns, "adapter")}`` registers an instance on the process-wide
registry (OQ-6: explicit registration).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from services.engine import demo_events
from services.engine.registry import registry
from verticals.{ns}.data_adapter import synthetic

_VERTICAL = "{ns}"


def _operational_events() -> list[dict[str, Any]]:
    """The per-process live OperationalEvent view (PLAN-0015 D1/D2)."""
    return demo_events.events(_VERTICAL, synthetic.operational_events)


_OBJECT_SOURCES = {{
    **synthetic.OBJECT_SOURCES,
    "OperationalEvent": _operational_events,
}}


class {prefix}SyntheticAdapter:
    """Deterministic synthetic DataAdapter for the {ns} vertical.

    Conforms structurally to ``services.engine.data_adapter.DataAdapter``.
    No external I/O — every call returns the synthetic dataset, so demos
    and tests are reproducible.
    """

    vertical_name = "{ns}"

    async def fetch_objects(
        self,
        object_type: str,
        filter_expr: str | None = None,
        limit: int = 1000,  # structural: the protocol's default page size
    ) -> list[dict[str, Any]]:
        """Return synthetic object dicts for ``object_type`` (unknown -> empty)."""
        source = _OBJECT_SOURCES.get(object_type)
        if source is None:
            return []
        return source()[:limit]

    async def fetch_links(
        self,
        link_type: str,
        from_pk: str | None = None,
        to_pk: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return link dicts for ``link_type`` (Phase 2 synthetic: none)."""
        return []

    async def stream_events(
        self,
        event_type: str,
        since: datetime | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield synthetic OperationalEvent dicts of ``event_type``."""
        for event in _operational_events():
            if event["event_type"] != event_type:
                continue
            if since is not None and event["occurred_at"] < since:
                continue
            yield event

    async def health_check(self) -> dict[str, Any]:
        """Report adapter status and the synthetic record counts."""
        return {{
            "status": "ok",
            "vertical": self.vertical_name,
            "synthetic": True,
            "object_counts": {{name: len(src()) for name, src in _OBJECT_SOURCES.items()}},
        }}


def {registrar_name(ns, "adapter")}() -> {prefix}SyntheticAdapter:
    """Register a fresh {prefix}SyntheticAdapter on the process-wide registry."""
    adapter = {prefix}SyntheticAdapter()
    registry.register_adapter(adapter)
    return adapter
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
