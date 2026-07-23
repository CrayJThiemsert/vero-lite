"""Wire-writer — the four registration points a scaffolded vertical needs (Step 5).

Oracles AC-6 and AC-10. A vertical that emits perfectly and is not wired is
invisible: the API serves no procedures for it and the scheduler daemon raises
``RegistryError`` at startup. The four points are

1. ``services/api/main.py`` — the registrar entry (lazy-import convention).
2. ``services/engine/cli.py`` — the MIRROR entry. ``services/engine/`` must not
   import ``services/api/``, so the map is duplicated deliberately and pinned
   EQUAL by ``tests/services/engine/test_cli_registrars.py``.
3. ``services/api/routers/procedures.py`` — the ``PROCEDURE_ARCHETYPES`` label,
   classified from the emitted gate content rather than guessed.
4. ``tests/api/test_procedures_endpoint.py`` — the census ``_EXPECTED`` entry and
   the ``assert total == N`` pin.

**Every transform is a pure ``str -> str``** and every writer takes an explicit
root. The tool code-mods files that also exist in this repo, so a CWD-relative
write would edit the running checkout instead of the scratch tree.

**AC-10 / SD-4 — counted prose is DISPOSED, not recounted.** The ratified option
is "stop counted prose; load-bearing counts become executable assertions". The
narrative tallies around the census are therefore replaced with a pointer to the
assertion rather than incremented: a prose count that must be hand-maintained
goes stale silently (it already had — ``fleet_maintenance ships two`` while
``_EXPECTED`` shipped three, a narrative summing to 12 against
``assert total == 13``), whereas the assertion cannot.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any


class WireError(RuntimeError):
    """Raised when an anchor is missing or an entry already exists.

    Fail loudly rather than appending blindly: a wire-writer that silently
    produced a duplicate entry would corrupt a shipped map.
    """


def classify_archetype(procedures_doc: dict[str, Any]) -> str:
    """The archetype label, derived from the emitted GATE CONTENT (row 8).

    Not guessed and not passed in: the label is a function of which gates the
    spine actually carries, so a spine that changes shape cannot keep a stale
    label. An authority gate (``doa_tier`` / ``severity_tier``) makes it AT-2 —
    that is the managerial signature; a lone band with a single gated action is
    AT-3; anything else falls back to AT-1.
    """
    gate_kinds = {
        step.get("facet", {}).get("decision_condition", {}).get("gate_kind", "none")
        for procedure in procedures_doc.get("procedures", {}).values()
        for step in procedure.get("steps", [])
    }
    if {"doa_tier", "severity_tier"} & gate_kinds:
        return "AT-2"
    if "rule_gate" in gate_kinds:
        return "AT-2"
    if "in_file_band" in gate_kinds or "env_band" in gate_kinds:
        return "AT-3"
    return "AT-1"


def _require(source: str, anchor: str, what: str) -> None:
    if anchor not in source:
        raise WireError(f"{what}: anchor not found — refusing to guess where to write")


def add_registrar_entry(source: str, namespace: str, *, mirror: bool) -> str:
    """Add the vertical to a ``_PROCEDURE_EXECUTOR_REGISTRARS`` map.

    ``mirror=True`` emits the ``services/engine/cli.py`` tuple form
    ``(module, attr)``; ``mirror=False`` emits the ``services/api/main.py``
    callable form. The two shapes differ because the CLI resolves lazily by name
    while the API holds the registrar directly.
    """
    anchor = "_PROCEDURE_EXECUTOR_REGISTRARS"
    _require(source, anchor, "registrar map")
    if f'"{namespace}"' in source.split(anchor, 1)[1][:2000]:
        raise WireError(f"registrar map already contains {namespace!r}")

    module = f"verticals.{namespace}.procedures_factory"
    attr = f"register_{namespace}_procedure_executors"
    entry = (
        f'    "{namespace}": (\n        "{module}",\n        "{attr}",\n    ),\n'
        if mirror
        else f'    "{namespace}": _{namespace}_registrar,\n'
    )
    # Insert before the map's closing brace — the first `\n}` after the anchor.
    head, tail = source.split(anchor, 1)
    close = tail.index("\n}")
    return head + anchor + tail[:close] + "\n" + entry.rstrip("\n") + tail[close:]


def add_procedure_archetype(source: str, vertical: str, procedure_id: str, archetype: str) -> str:
    """Add the ``(vertical, procedure_id) -> archetype`` label entry."""
    anchor = "PROCEDURE_ARCHETYPES: dict[tuple[str, str], str] = {"
    _require(source, anchor, "PROCEDURE_ARCHETYPES")
    key = f'("{vertical}", "{procedure_id}")'
    if key in source:
        raise WireError(f"PROCEDURE_ARCHETYPES already contains {key}")
    entry = f'    {key}: "{archetype}",\n'
    return source.replace(anchor + "\n", anchor + "\n" + entry, 1)


def add_census_entry(source: str, vertical: str, procedure_id: str, archetype: str) -> str:
    """Add the vertical's census block (or extend it) in ``_EXPECTED``."""
    anchor = "_EXPECTED: dict[str, dict[str, str]] = {"
    _require(source, anchor, "_EXPECTED")
    if f'"{procedure_id}"' in source:
        raise WireError(f"_EXPECTED already contains {procedure_id!r}")
    entry = f'    "{vertical}": {{"{procedure_id}": "{archetype}"}},\n'
    return source.replace(anchor + "\n", anchor + "\n" + entry, 1)


_TOTAL = re.compile(r"assert total == (\d+)")


def bump_total(source: str, by: int = 1) -> str:
    """Increment the executable census pin — the count SD-4 keeps.

    This one is load-bearing precisely because it is executable: unlike the
    prose tallies, it cannot drift without a test going red.
    """
    match = _TOTAL.search(source)
    if match is None:
        raise WireError("assert total == N: pin not found")
    bumped = f"assert total == {int(match.group(1)) + by}"
    return source[: match.start()] + bumped + source[match.end() :]


# `\s+` between the vertical and the verb, not a single space: these tallies live
# in wrapped docstrings, so the two halves are routinely split across a line
# break ("supply_chain\nships two"). A single-space pattern silently missed
# exactly the stale one this rule exists to catch.
_COUNTED_PROSE = re.compile(
    r"(?P<vertical>\w+)(?P<gap>\s+)ships (?:one|two|three|four|five|six|seven|eight|nine|ten)\b"
)

_NUMBER_WORD = (
    r"one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
    r"fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty"
)

# The SECOND counted shape, and the reason AC-10's fourth site was untouched: the
# per-vertical tally pattern above scores ZERO on "All six PROCEDURE-SHIPPING
# verticals register a factory" (services/api/main.py) and on "across six verticals"
# — those count the COLLECTION, not each member. Adding main.py to the targets dict
# without this would have been a no-op that looked like a fix.
_COUNTED_COLLECTION = re.compile(
    rf"\b(?:{_NUMBER_WORD})\s+(?P<rest>(?:[A-Za-z-]+\s+)?verticals?\b)",
    re.IGNORECASE,
)

# Any spelled cardinal still adjacent to the census nouns AFTER disposition. Used to
# REPORT, never to rewrite — see `residual_counted_prose`.
_RESIDUAL_COUNT = re.compile(
    rf"\b(?:{_NUMBER_WORD})\s+(?:[A-Za-z-]+\s+)?(?:verticals?|procedures?)\b",
    re.IGNORECASE,
)

DISPOSITION_NOTE = (
    "per-vertical counts are deliberately NOT written in prose (PLAN-0091 SD-4): "
    "the executable `assert total ==` pin below is the count of record, because a "
    "hand-maintained narrative tally goes stale silently and an assertion cannot"
)


def dispose_counted_prose(source: str) -> tuple[str, int]:
    """Replace hand-maintained narrative tallies with non-counting prose (SD-4, AC-10).

    Returns ``(new_source, replacements)``. The prose is never re-counted — that is
    the whole ruling: a count a human must maintain in prose is exactly the thing
    that had already gone stale on disk.

    Two shapes, because the counted prose in the wired files comes in two:

    * a **per-member** tally — ``supply_chain ships two`` — rewritten to
      ``supply_chain ships its own procedures``;
    * a **collection** count — ``All six PROCEDURE-SHIPPING verticals`` — where the
      cardinal is simply deleted, leaving ``All PROCEDURE-SHIPPING verticals``. Deleting
      is the whole transform on purpose: anything cleverer has to rewrite the
      surrounding grammar, and a wire-writer that reflows English in shipped files is
      one bad match away from mangling a docstring.
    """
    replaced = 0

    def _sub_member(match: re.Match[str]) -> str:
        nonlocal replaced
        replaced += 1
        return f"{match.group('vertical')}{match.group('gap')}ships its own procedures"

    def _sub_collection(match: re.Match[str]) -> str:
        nonlocal replaced
        replaced += 1
        return match.group("rest")

    out = _COUNTED_PROSE.sub(_sub_member, source)
    out = _COUNTED_COLLECTION.sub(_sub_collection, out)
    return out, replaced


def residual_counted_prose(source: str) -> list[str]:
    """Counted prose the disposer will NOT rewrite, reported for a human to settle.

    Some counted prose is not a regular shape. ``test_procedures_endpoint.py``'s census
    comment carries four interlocking counts in one free-form narrative ("thirteen
    procedures … the twelve prior (fact-pack #1's five + …)"), and each one encodes
    real provenance — which PLAN contributed which procedure. A regex that rewrote it
    would either mangle the grammar or delete the provenance, and deleting a shipped
    file's history to satisfy a tally rule is a worse outcome than the stale tally.

    So this reports instead of rewriting, which is the same stance the tool takes at a
    governance tripwire: detect, hand a human the specifics, never clear it yourself.
    """
    return sorted({match.group(0) for match in _RESIDUAL_COUNT.finditer(source)})


def write_wires(
    namespace: str,
    procedure_id: str,
    procedures_doc: dict[str, Any],
    root: Path,
) -> dict[str, str]:
    """Apply all four wires under ``root`` and return ``{path: new_source}``.

    ``root`` is explicit — the tool edits files that also exist in this repo, so
    inheriting the CWD would code-mod the running checkout.
    """
    archetype = classify_archetype(procedures_doc)
    targets: dict[str, Callable[[str], str]] = {
        # AC-10's fourth counted site lives in this file's registrar docstring
        # ("All six PROCEDURE-SHIPPING verticals register a factory"), so the
        # disposition runs here too — it is a collection count, which is why the
        # per-member pattern alone scored zero on it.
        "services/api/main.py": lambda s: dispose_counted_prose(
            add_registrar_entry(s, namespace, mirror=False)
        )[0],
        "services/engine/cli.py": lambda s: add_registrar_entry(s, namespace, mirror=True),
        "services/api/routers/procedures.py": lambda s: add_procedure_archetype(
            s, namespace, procedure_id, archetype
        ),
        "tests/api/test_procedures_endpoint.py": lambda s: dispose_counted_prose(
            bump_total(add_census_entry(s, namespace, procedure_id, archetype))
        )[0],
    }

    written: dict[str, str] = {}
    for rel, transform in targets.items():
        path = root / rel
        if not path.is_file():
            raise WireError(f"{rel}: not present under {root} — stage it before wiring")
        new_source = transform(path.read_text(encoding="utf-8"))
        path.write_text(new_source, encoding="utf-8")
        written[rel] = new_source
    return written
