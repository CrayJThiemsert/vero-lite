"""The trace-kind label registry is exactly the emitted trace vocabulary.

The reasoning-trace badge is the **attribution channel** — it tells a reader who or what
produced a step. Before PLAN-0080 it picked its colour by *substring sniff*
(``kind.includes('rule')``), which was dishonest in both directions: 14 of the 16
procedure-engine kinds fell through to an unattributed neutral badge, and
``scored_rule_selected`` / ``rule_gate_evaluated`` matched ``'rule'`` and rendered in the
recommender's ``rule_check`` colour — asserting an attribution that was simply wrong. The
typed path had rotted the same way: only the 3 original example kinds coloured correctly.

Prose inventories of a code vocabulary go stale silently, and this one did so twice: the
drafting dispatch hand-listed 9 kinds where 22 existed (PLAN-0080 F-3), and the PLAN then
asserted "the engine is the only emitter" — which a live probe against a real governed run
refuted, surfacing a 23rd kind (``query``) emitted from ``verticals/``. So the fix is not a
better list; it is this test. ``services/api/static/assets/trace-kinds.js`` is the one
registry, and adding an emission without adding a label turns this RED.

Scope + limits, stated honestly:

* This is an **AST** scan, not a regex scan. That is what lets the alias allowlist below
  stay genuinely EMPTY. A regex over ``kind="..."`` also catches (a) prose in comments —
  ``event_bridge.py`` explains a hash collision with ``vertical="a"+kind="bc"``, naming
  two kinds that do not exist; and (b) ``ControlRef(kind="sod")``
  (``action_step.py``), a real kwarg on a *different* Pydantic model. Neither is a trace
  kind, and seeding them into an allowlist would have made the allowlist a junk drawer
  that erodes the very thing this test protects.
* Any **other** callable taking a literal ``kind=`` kwarg is a hard FAILURE, not a silent
  skip — see ``_NON_TRACE_KIND_KWARG_OWNERS``. A new model with a ``kind`` field must be
  classified deliberately. Fail-closed is the point.
* A dict literal with a ``"kind"`` string key is treated as a trace emission **anywhere**
  under the scanned roots. If a ``detail=`` payload ever legitimately carries its own
  ``"kind"`` key, this goes RED and forces a conscious call. That is intended.
* A **dynamically built** kind (e.g. ``kind=f"read_{mode}"``) evades the scan entirely —
  none exist today (all 23 are literals). This is the accepted residual of SD-1 option
  (c) (``ReasoningStep.kind`` stays ``str``; the vocabulary is enforced at CI-time, not
  runtime). If dynamic kinds ever appear, SD-1 reopens.
* Trace-entry ``kind`` is **not** definition-side ``Step.kind``
  (``services/engine/procedures/spec.py``), which is a ``StrEnum`` written
  ``QUERY = "query"`` and IS hashed into the governance/config pin. The two merely share
  a name; this scan sees neither form of the enum.
"""

from __future__ import annotations

import ast
import json
from functools import lru_cache
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]

#: EVERY tree that emits a trace kind. ``verticals/`` is here because the PLAN-0080
#: draft asserted "the engine is the only emitter" and a live probe against a real
#: governed run refuted it: the per-vertical seed executors emit ``query``
#: (``verticals/procurement/hero_demo/run.py``, ``verticals/supply_chain/
#: procedures_factory.py``). Scanning only ``services/engine`` would leave a new
#: vertical's seed emitter uncovered — the exact rot this test exists to kill.
_SCANNED_ROOTS = (_REPO_ROOT / "services" / "engine", _REPO_ROOT / "verticals")
_REGISTRY_JS = _REPO_ROOT / "services" / "api" / "static" / "assets" / "trace-kinds.js"

_JSON_BEGIN = "/* TRACE_KINDS_JSON_BEGIN */"
_JSON_END = "/* TRACE_KINDS_JSON_END */"

#: The ONLY typed trace emitter.
_TRACE_STEP_CTOR = "ReasoningStep"

#: Callables that legitimately take a literal ``kind=`` kwarg that is NOT a reasoning-trace
#: kind. Listed explicitly so a NEW such callable fails loudly (via
#: test_every_kind_kwarg_owner_is_classified) instead of silently polluting the trace
#: vocabulary. ``ControlRef`` — a governed-decision control tie (ADR-0026 D6), kinds
#: 'sod'/'doa_tier'. ``EconomicImpact`` — the Box-4 impact facet (ADR-0030), a
#: per-vertical kind ('mortality_avoided', 'spoilage_avoided', 'avoided_outage',
#: 'expedite_tradeoff'). Both were surfaced by widening the scan to ``verticals/``.
_NON_TRACE_KIND_KWARG_OWNERS = frozenset({"ControlRef", "EconomicImpact"})

#: Registry entries deliberately not emitted by any scanned root (demo aliases).
#: EMPTY by construction: view-story's synthetic ``query``/``rule``/``llm`` kinds were
#: normalized to the canonical vocabulary (PLAN-0080 Step 3) rather than aliased, so the
#: map stays exactly the emitted vocabulary.
_ALIAS_ALLOWLIST: frozenset[str] = frozenset()

#: L-4: colour = mechanism, glyph = actor. Two axes, two channels.
_ACTORS = frozenset({"human", "llm", "engine"})
_MECHANISM_CLASSES = frozenset({"s-ok", "s-info", "s-warn", "s-crit", "s-neutral"})

#: A scan that matches nothing must not pass vacuously (the ``|| echo`` false-pass class).
#: 23 kinds exist today; the floor sits below that so adding or retiring one kind does not
#: require editing this number.
_SCAN_HEALTH_FLOOR = 20


@lru_cache(maxsize=1)
def _registry() -> dict[str, dict[str, str]]:
    """The kind -> {label, cls, actor} map, read from the JS asset's JSON block."""
    src = _REGISTRY_JS.read_text(encoding="utf-8")
    try:
        start = src.index(_JSON_BEGIN) + len(_JSON_BEGIN)
        end = src.index(_JSON_END)
    except ValueError as exc:  # pragma: no cover - only on a broken asset
        raise AssertionError(
            f"{_REGISTRY_JS.name} lost its {_JSON_BEGIN} / {_JSON_END} delimiters — the "
            "browser and this test read the SAME literal through them. Restore them."
        ) from exc
    return json.loads(src[start:end])


def _kwarg_owner(call: ast.Call) -> str | None:
    """``Foo(...)`` -> ``"Foo"``; ``mod.Foo(...)`` -> ``"Foo"``; else ``None``."""
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _scanned_sources() -> list[Path]:
    return sorted(p for root in _SCANNED_ROOTS for p in root.rglob("*.py"))


def _dict_kind_literal(node: ast.AST) -> str | None:
    """A ``{"kind": "<literal>"}`` dict -> the kind string (raw-dict emission form)."""
    if not isinstance(node, ast.Dict):
        return None
    for key, value in zip(node.keys, node.values, strict=False):
        if (
            isinstance(key, ast.Constant)
            and key.value == "kind"
            and isinstance(value, ast.Constant)
            and isinstance(value.value, str)
        ):
            return value.value
    return None


def _call_kind_kwarg(node: ast.AST) -> tuple[str, str] | None:
    """A call with a literal ``kind="..."`` -> ``(owner, kind)`` (typed emission form)."""
    if not isinstance(node, ast.Call):
        return None
    kw = next((k for k in node.keywords if k.arg == "kind"), None)
    if kw is None or not isinstance(kw.value, ast.Constant) or not isinstance(kw.value.value, str):
        return None
    return _kwarg_owner(node) or "<unknown>", kw.value.value


@lru_cache(maxsize=1)
def _scan_emitters() -> tuple[frozenset[str], tuple[str, ...]]:
    """Return ``(emitted_kinds, unclassified_kind_kwargs)`` over every scanned root."""
    kinds: set[str] = set()
    problems: list[str] = []
    for path in _scanned_sources():
        rel = path.relative_to(_REPO_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            dict_kind = _dict_kind_literal(node)
            if dict_kind is not None:
                kinds.add(dict_kind)
                continue
            call = _call_kind_kwarg(node)
            if call is None:
                continue
            owner, kind = call
            if owner == _TRACE_STEP_CTOR:
                kinds.add(kind)
            elif owner not in _NON_TRACE_KIND_KWARG_OWNERS:
                problems.append(f"{rel}:{node.lineno} — {owner}(kind={kind!r})")
    return frozenset(kinds), tuple(problems)


def test_scan_is_not_vacuous() -> None:
    """A refactor that breaks the scan must fail, not silently find nothing."""
    emitted, _ = _scan_emitters()
    roots = ", ".join(r.relative_to(_REPO_ROOT).as_posix() for r in _SCANNED_ROOTS)
    assert len(emitted) >= _SCAN_HEALTH_FLOOR, (
        f"only {len(emitted)} trace kinds found under {roots} (floor "
        f"{_SCAN_HEALTH_FLOOR}) — the scan is probably broken, not the emitters. A pass "
        f"here would be vacuous. Found: {sorted(emitted)}"
    )


def test_every_kind_kwarg_owner_is_classified() -> None:
    """A new callable taking ``kind="..."`` must be classified, not silently absorbed."""
    _, problems = _scan_emitters()
    assert not problems, (
        "a literal kind= kwarg appeared on a callable this guard does not know:\n  "
        + "\n  ".join(problems)
        + f"\n\nClassify it: if it emits a reasoning-trace step, it should be a "
        f"{_TRACE_STEP_CTOR}; if its `kind` is an unrelated vocabulary (as "
        f"ControlRef's 'sod' is), add it to _NON_TRACE_KIND_KWARG_OWNERS with a reason."
    )


def test_every_emitted_kind_has_a_label() -> None:
    """The anti-rot half: an engine kind with no label renders as a raw token."""
    emitted, _ = _scan_emitters()
    unlabelled = emitted - set(_registry())
    assert not unlabelled, (
        f"these engine-emitted trace kinds have no entry in {_REGISTRY_JS.name}: "
        f"{sorted(unlabelled)}\n\nThey would render as an unattributed raw token in the "
        "trace badge. Add each one a {label, cls, actor} row."
    )


def test_no_dead_registry_entries() -> None:
    """The other half: a labelled kind nothing emits is dead weight (or a typo)."""
    emitted, _ = _scan_emitters()
    dead = set(_registry()) - emitted - _ALIAS_ALLOWLIST
    assert not dead, (
        f"{_REGISTRY_JS.name} labels kinds the engine never emits: {sorted(dead)}\n\n"
        "Either the kind was retired (drop the row), the label has a typo, or it is a "
        "deliberate demo alias (add it to _ALIAS_ALLOWLIST with a reason)."
    )


def test_every_entry_declares_a_known_actor_and_mechanism() -> None:
    """L-4 tripwired: a kind cannot get a label but no attribution."""
    bad_actor = {
        kind: entry.get("actor")
        for kind, entry in _registry().items()
        if entry.get("actor") not in _ACTORS
    }
    assert not bad_actor, (
        f"every registry entry needs actor in {sorted(_ACTORS)} — the glyph channel is "
        f"driven by this facet, not by another substring sniff. Offenders: {bad_actor}"
    )
    bad_cls = {
        kind: entry.get("cls")
        for kind, entry in _registry().items()
        if entry.get("cls") not in _MECHANISM_CLASSES
    }
    assert not bad_cls, (
        f"every registry entry needs cls in {sorted(_MECHANISM_CLASSES)} — colour is the "
        f"MECHANISM channel (theme.css semantics), never the actor. Offenders: {bad_cls}"
    )
    missing_label = [k for k, e in _registry().items() if not str(e.get("label", "")).strip()]
    assert not missing_label, f"registry entries with no label: {missing_label}"
