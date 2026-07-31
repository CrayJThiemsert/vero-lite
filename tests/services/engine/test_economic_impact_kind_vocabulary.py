"""``EconomicImpact.kind``'s documented vocabulary equals what producers emit.

`kind` is a free `str` by ratified design — ADR-0030 D3 leaves it unconstrained so a
new vertical can name its own semantics without an engine change. The cost of that
freedom is that the only description of the vocabulary is a Field docstring, and a
docstring cannot notice when a fifth producer ships a fifth label.

That is not hypothetical. PR #994 (session 195) added fleet_maintenance's
``overpay_avoided`` and the description kept listing four kinds for the whole of
session 195 — a wrong statement in the one place a reader goes to learn the
vocabulary, sitting in the field's own OpenAPI description. Nothing failed, because
nothing was checking.

So the description is pinned to the producers by SET EQUALITY, both directions:

* a producer emits a kind the description omits → RED (the #994 case);
* the description names a kind no producer emits → RED (a retired vertical leaves
  a label behind, and the vocabulary starts describing a world that ended).

Scope + limits, stated honestly:

* This is a **static source scan**, not a runtime check. It reads the `kind="..."`
  literal each producer passes, which is how every producer shipped to date names
  its kind — a producer computing its kind at runtime would be invisible here, and
  ``test_every_producer_names_its_kind_with_a_literal`` is what stops that from
  happening silently rather than pretending it cannot.
* It says nothing about whether a kind is a *good* label. Only that the engine's
  description and the verticals' behaviour agree on which labels exist.
"""

from __future__ import annotations

import re
from pathlib import Path

from services.engine.economic_impact import EconomicImpact

_REPO_ROOT = Path(__file__).resolve().parents[3]
_VERTICALS = _REPO_ROOT / "verticals"

#: ``kind="overpay_avoided"`` inside a vertical's economic-impact producer.
_KIND_LITERAL = re.compile(r'\bkind\s*=\s*"([a-z][a-z0-9_]*)"')


def _producer_modules() -> list[Path]:
    """Every vertical's `economic_impact.py`, by glob — a new vertical needs no edit."""
    return sorted(_VERTICALS.glob("*/economic_impact.py"))


def _emitted_kinds() -> dict[str, str]:
    """``{kind: the vertical that emits it}``."""
    emitted: dict[str, str] = {}
    for module in _producer_modules():
        for kind in _KIND_LITERAL.findall(module.read_text(encoding="utf-8")):
            emitted[kind] = module.parent.name
    return emitted


def _documented_kinds() -> set[str]:
    """The kinds named in `EconomicImpact.kind`'s Field description."""
    description = EconomicImpact.model_fields["kind"].description or ""
    return set(re.findall(r"\b([a-z][a-z0-9_]*_[a-z0-9_]+)\b", description))


def test_the_scan_finds_every_shipped_producer() -> None:
    """A glob that matches nothing would make the equality below vacuous."""
    modules = _producer_modules()
    verticals = sorted(m.parent.name for m in modules)
    assert len(modules) >= 5, (
        f"only {len(modules)} economic_impact.py modules found under verticals/ "
        f"({verticals}) — five shipped as of PR #994. The glob is broken, not the repo."
    )
    assert "fleet_maintenance" in verticals, (
        "fleet_maintenance's producer (PR #994) was not found — the scan is not reading "
        "the tree it thinks it is."
    )


def test_every_producer_names_its_kind_with_a_literal() -> None:
    """Each producer module must contain at least one `kind="..."` literal.

    This is the assumption the whole module rests on. A producer that computes its
    kind at runtime is invisible to a source scan, and the honest response is to go
    RED here — which forces a decision — rather than to keep passing while silently
    covering one vertical less.
    """
    silent = [
        module.parent.name
        for module in _producer_modules()
        if not _KIND_LITERAL.search(module.read_text(encoding="utf-8"))
    ]
    assert not silent, (
        f'economic-impact producers with no literal `kind="..."`: {silent}\n\n'
        "This module scans source for that literal, so those verticals are not covered "
        "by the vocabulary check below. Either keep the literal, or replace this scan "
        "with a runtime check — do not leave it passing while covering less."
    )


def test_the_documented_kind_vocabulary_equals_what_producers_emit() -> None:
    """Set equality, both directions — the #994 drift is the motivating case."""
    emitted = _emitted_kinds()
    documented = _documented_kinds()

    undocumented = set(emitted) - documented
    assert not undocumented, (
        "producers emit `kind` values EconomicImpact.kind's description never mentions: "
        + ", ".join(f"{kind} ({emitted[kind]})" for kind in sorted(undocumented))
        + "\n\nThat description is the only written definition of the vocabulary and it "
        "ships in the OpenAPI schema. Add the label there in the same change that adds "
        "the producer — this is exactly the drift PR #994 introduced."
    )
    retired = documented - set(emitted)
    assert not retired, (
        f"the description names kinds no producer emits: {sorted(retired)}\n\n"
        "Either a producer was removed and its label left behind, or the label is a "
        "typo. Both make the documented vocabulary describe a world that does not exist."
    )
