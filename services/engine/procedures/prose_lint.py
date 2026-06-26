"""Deterministic prose-lint for generated advisory prose (ADR-0024 D3 mechanism 2;
PLAN-0040 Phase A, Step A3).

The restricted draft type (D3 mechanism 1, ``draft.py``) makes a *typed* governance
leak a type error — but ``extra="forbid"`` gives **false assurance** against
**prose-smuggling**: a threshold / amount / handler-name laundered into generated
``goal`` / ``description`` / ``facet.*`` prose looks non-authoritative but is the
exact anchor a human then copies into the field they "author" (leak class 1). This
lint closes that hole: it rejects numeric values, currency, percentages, registered
handler-names, and selection/approval verbs appearing in generated prose.

Conservative by design — a SAFETY net, so it over-flags rather than under-flags (a
flagged false positive is reviewed by a human; an unflagged value is dangerous). It
runs over every generated prose string at pipeline stage S6 (Phase B); here it is a
pure, offline-testable function. It is NOT run over hand-authored specs — a shipped
``facet.governance`` note may legitimately say "HUMAN approves", which this would
flag; that is fine, because the lint's scope is *generated* prose only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# A decimal value (a threshold / band): 4.0, 0.8, 100.0. Guarded so version-ish
# strings (v0.1) and ADR-007 do not match.
_DECIMAL = re.compile(r"(?<![\w.])\d+\.\d+")
# A standalone multi-digit integer (an amount / reorder point): 100, 50. The
# lookarounds exclude identifiers (ADR-007, PLAN-0022, gpt-oss:20b, 5-facet).
_INTEGER = re.compile(r"(?<![\w.\-])\d{2,}(?![\w.\-])")
# Currency-prefixed amounts: ฿50, $1,000.00, €250.
_CURRENCY = re.compile(r"[$€£¥฿]\s?\d[\d,]*(?:\.\d+)?")
# Magnitude-suffixed amounts: 50k, 1.5M.
_AMOUNT_SUFFIX = re.compile(r"(?<![\w])\d+(?:\.\d+)?\s?[kKmM](?![\w])")
# Percentages: 80%, 12.5 %.
_PERCENT = re.compile(r"(?<![\w])\d+(?:\.\d+)?\s?%")
# Selection / approval verbs — the LLM may only draft/summarise; selecting or
# approving is a decision a rule or a human owns (governed ≠ generated). Matched as
# whole words so "approver" / "selection" (descriptive nouns) do not trip.
_DECISION_VERB = re.compile(
    r"\b(?:select|selects|selecting|choose|chooses|choosing|pick|picks|"
    r"approve|approves|approving|authori[sz]e|authori[sz]es|authori[sz]ed)\b",
    re.IGNORECASE,
)
# "set ... threshold" — the canonical "the LLM never sets a threshold" phrasing.
_SET_THRESHOLD = re.compile(r"\bset(?:s|ting)?\b[^.]{0,40}\bthreshold\b", re.IGNORECASE)


@dataclass(frozen=True)
class Violation:
    """One prose-lint finding: the leak class, the offending substring, and why."""

    kind: str
    match: str
    message: str


def prose_lint(text: str, *, handlers: frozenset[str] = frozenset()) -> list[Violation]:
    """Return the governance-smuggling violations in ``text`` (empty ⇒ clean).

    ``handlers`` is the known registered-handler vocabulary (from the agent
    allowlists / handler registry); a handler NAME in generated prose is a binding
    a human must author, not advisory text. Pure + deterministic — no I/O."""
    out: list[Violation] = []
    for m in _CURRENCY.finditer(text):
        out.append(Violation("currency", m.group(), "a currency amount is a human-authored value"))
    for m in _AMOUNT_SUFFIX.finditer(text):
        out.append(Violation("amount", m.group(), "a magnitude amount is a human-authored value"))
    for m in _PERCENT.finditer(text):
        out.append(Violation("percent", m.group(), "a percentage is a human-authored value"))
    for m in _DECIMAL.finditer(text):
        out.append(
            Violation("numeric", m.group(), "a decimal value (a threshold/band) is human-authored")
        )
    for m in _INTEGER.finditer(text):
        out.append(Violation("numeric", m.group(), "a numeric value is human-authored"))
    for handler in sorted(handlers):
        if re.search(rf"\b{re.escape(handler)}\b", text):
            out.append(
                Violation(
                    "handler",
                    handler,
                    f"the registered handler name '{handler}' is a human-authored binding",
                )
            )
    for m in _SET_THRESHOLD.finditer(text):
        out.append(
            Violation(
                "decision_verb", m.group(), "the LLM never SETS a threshold (bands are authored)"
            )
        )
    for m in _DECISION_VERB.finditer(text):
        out.append(
            Violation(
                "decision_verb",
                m.group(),
                "a selection/approval verb implies the LLM decides — it may only draft/summarise",
            )
        )
    return out
