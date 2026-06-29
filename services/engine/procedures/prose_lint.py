"""Deterministic prose-lint for generated advisory prose (ADR-0024 D3 mechanism 2;
PLAN-0040 Phase A, Step A3; hardened in Phase B PR-B1-fix after the security audit).

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

**Hardening (PR-B1 security audit + re-verify).** The text is **canonicalised before
scanning** (NFKC + zero-width strip) so display-equivalent obfuscations cannot evade the
digit patterns — a fullwidth-digit decimal folds to ASCII ``4.0``, a zero-width-split
number collapses. Coverage was widened to the bypass classes the audit found:
single-digit and hyphen-adjacent integers, scientific / hex forms, **spelled-out**
numbers ("four point zero", "fifty thousand"), a fuller approval-verb set, and any
``snake_case`` / ``UPPER_SNAKE`` / ``camelCase`` identifier (a handler / field / env-var
binding never appears in natural prose). Registered handler names are matched in any
separator spelling ("wire transfer" / "wire-transfer" / "wireTransfer"). Named residuals
(run-gate-backstopped — none can make a skeleton runnable): roman-numeral tiers,
non-English (e.g. Thai) spelled number-words, and ambiguous approval synonyms
(clear / confirm / validate) too false-positive-prone to denylist.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

# --- canonicalisation (run before every scan) -----------------------------------

# Zero-width / BOM codepoints that can split a number to evade the digit patterns
# (ZWSP, ZWNJ, ZWJ, word-joiner, BOM) — codepoints, not literals, so source stays ASCII.
_ZERO_WIDTH = dict.fromkeys((0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF), None)


def _canonicalize(text: str) -> str:
    """NFKC-fold compatibility forms (fullwidth digits / punctuation fold to ASCII — a
    fullwidth '4.0' becomes ``4.0`` and a fullwidth '$50k' becomes ``$50k``) and strip
    zero-width characters. ``\\d`` already matches Unicode digits, so once the separator is
    folded to ASCII, Thai / Arabic-Indic / Devanagari digit values are caught too."""
    return unicodedata.normalize("NFKC", text).translate(_ZERO_WIDTH)


# --- numeric values --------------------------------------------------------------

# A decimal value (a threshold / band): 4.0, 0.8, 100.0. Guarded so version-ish
# strings (v0.1) and ADR-007 do not match.
_DECIMAL = re.compile(r"(?<![\w.])\d+\.\d+")
# A bare integer (an amount / reorder point / a single-digit threshold like "above 4").
# The lookbehind excludes identifier prefixes (ADR-007, PLAN-0022, v0.1); the trailing
# \w guard excludes ids with a trailing letter/digit (gpt-oss:20b). Single digits ARE
# matched now (the audit showed "above 4" / "to 9" bypassed the old \d{2,}).
_INTEGER = re.compile(r"(?<![\w.\-])\d+(?![\w])")
# Scientific / hex numeric forms (4e0, 0x32) — low-prose-likelihood obfuscations.
_SCIENTIFIC = re.compile(r"(?<![\w.])\d+(?:\.\d+)?[eE][+-]?\d+(?![\w])")
_HEX = re.compile(r"(?<![\w])0[xX][0-9a-fA-F]+\b")
# Currency-prefixed amounts: ฿50, $1,000.00, €250.
_CURRENCY = re.compile(r"[$€£¥฿]\s?\d[\d,]*(?:\.\d+)?")
# Magnitude-suffixed amounts: 50k, 1.5M. (No 'b' suffix — it collides with ids like 20b.)
_AMOUNT_SUFFIX = re.compile(r"(?<![\w])\d+(?:\.\d+)?\s?[kKmM](?![\w])")
# Percentages: 80%, 12.5 %.
_PERCENT = re.compile(r"(?<![\w])\d+(?:\.\d+)?\s?%")

# --- spelled-out numbers (carry no digits) --------------------------------------

_ONES = r"zero|one|two|three|four|five|six|seven|eight|nine|ten"
_TEENS = r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen"
_TENS = r"twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety"
_SCALES = r"hundred|thousand|million|billion|trillion"
_NUMWORD = rf"{_ONES}|{_TEENS}|{_TENS}|{_SCALES}"
# Flag a specific-magnitude word (teens / tens / scale) on its own — a lone ones-word
# (one..ten) is too common in prose, so it only matters inside a "<word> point <word>"
# decimal or next to a scale word.
_NUMBER_WORD = re.compile(rf"\b(?:{_TEENS}|{_TENS}|{_SCALES})\b", re.IGNORECASE)
_PERCENT_WORD = re.compile(r"\b(?:percent|per\s?cent)\b", re.IGNORECASE)
_SPELLED_DECIMAL = re.compile(rf"\b(?:{_NUMWORD})\s+point\s+(?:{_NUMWORD})\b", re.IGNORECASE)

# --- identifiers ----------------------------------------------------------------

# A snake_case token (with an internal underscore) is a code identifier — a handler /
# field / env-var binding — never natural advisory prose. Case-INsensitive so an
# UPPER_SNAKE env var (OCT_RECOMMEND_THRESHOLD — the literal env-band binding) is caught,
# not just lower snake (wire_transfer). A camelCase token is the same kind of identifier
# in a different spelling (swiftPayout); both catch an invented handler the registry misses.
_SNAKE_CASE = re.compile(r"\b[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+\b")
_CAMEL_CASE = re.compile(r"\b[a-z]+[A-Z][A-Za-z0-9]*\b")

# --- decision verbs -------------------------------------------------------------

# Selection / approval verbs — the LLM may only draft/summarise; selecting, approving,
# or otherwise DECIDING is a rule's or a human's job (governed ≠ generated). Whole-word
# matched so descriptive nouns ("approver", "selection") do not trip. Expanded from the
# audit (the original set missed ratify / permit / grant / deny / reject / override / …).
_DECISION_VERB = re.compile(
    r"\b(?:select|selects|selecting|choose|chooses|choosing|pick|picks|picking|"
    r"approve|approves|approving|approved|authori[sz]e|authori[sz]es|authori[sz]ed|"
    r"ratif(?:y|ies|ied)|permit|permits|permitted|grant|grants|granted|"
    r"den(?:y|ies|ied)|reject|rejects|rejected|overrid(?:e|es|den|ing)|"
    r"waive|waives|waived|veto(?:es|ed)?|endors(?:e|es|ed|ing)|"
    r"accept|accepts|accepted|decline|declines|declined|disapprove|disapproves|disapproved|"
    r"sanction|sanctions|sanctioned)\b",
    re.IGNORECASE,
)
# Multi-word approval phrases the single-word set cannot express.
_DECISION_PHRASE = re.compile(r"\b(?:sign[\s-]?off|green[\s-]?light(?:s|ed|ing)?)\b", re.IGNORECASE)
# "set ... threshold" — the canonical "the LLM never sets a threshold" phrasing.
_SET_THRESHOLD = re.compile(r"\bset(?:s|ting)?\b[^.]{0,40}\bthreshold\b", re.IGNORECASE)


@dataclass(frozen=True)
class Violation:
    """One prose-lint finding: the leak class, the offending substring, and why."""

    kind: str
    match: str
    message: str


# A pattern, the leak class it flags, and the human-readable reason. The numeric/currency
# table is scanned first, then handlers (a special case needing the registry), then verbs.
_VALUE_SCANS: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (_CURRENCY, "currency", "a currency amount is a human-authored value"),
    (_AMOUNT_SUFFIX, "amount", "a magnitude amount is a human-authored value"),
    (_PERCENT, "percent", "a percentage is a human-authored value"),
    (_PERCENT_WORD, "percent", "a percentage is a human-authored value"),
    (_SPELLED_DECIMAL, "numeric", "a spelled-out decimal (a threshold/band) is human-authored"),
    (_DECIMAL, "numeric", "a decimal value (a threshold/band) is human-authored"),
    (_SCIENTIFIC, "numeric", "a scientific-notation value is human-authored"),
    (_HEX, "numeric", "a hex value is human-authored"),
    (_INTEGER, "numeric", "a numeric value is human-authored"),
    (_NUMBER_WORD, "numeric", "a spelled-out number is a human-authored value"),
)
_VERB_SCANS: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (_SET_THRESHOLD, "decision_verb", "the LLM never SETS a threshold (bands are authored)"),
    (_DECISION_PHRASE, "decision_verb", "an approval phrase implies the LLM decides"),
    (_DECISION_VERB, "decision_verb", "a selection/approval verb implies the LLM decides"),
)


def _scan(text: str, table: Iterable[tuple[re.Pattern[str], str, str]]) -> list[Violation]:
    return [
        Violation(kind, m.group(), message)
        for pattern, kind, message in table
        for m in pattern.finditer(text)
    ]


def _handler_violations(text: str, handlers: frozenset[str]) -> list[Violation]:
    """Registered-handler names — matched in ANY separator spelling (wire_transfer also
    catches 'wire transfer' / 'wire-transfer' / 'wireTransfer') — plus any snake_case /
    UPPER_SNAKE / camelCase identifier (the structural catch for an invented handler or
    env-var binding the registry misses)."""
    out: list[Violation] = []
    matched: set[str] = set()
    for handler in sorted(handlers):
        # a registered name may surface with the separators rewritten (or removed); match
        # all spellings so a known binding cannot be laundered past the exact-name check.
        flexible = re.escape(handler).replace("_", r"[_\- ]?")
        if re.search(rf"\b{flexible}\b", text, re.IGNORECASE) is not None:
            out.append(
                Violation(
                    "handler",
                    handler,
                    f"the registered handler name '{handler}' is a human-authored binding",
                )
            )
            matched.add(handler.lower())
    for pattern in (_SNAKE_CASE, _CAMEL_CASE):
        for m in pattern.finditer(text):
            token = m.group()
            if token.lower() in matched:
                continue
            matched.add(token.lower())
            out.append(
                Violation(
                    "handler",
                    token,
                    f"the identifier '{token}' (a handler/field binding) is human-authored",
                )
            )
    return out


def prose_lint(text: str, *, handlers: frozenset[str] = frozenset()) -> list[Violation]:
    """Return the governance-smuggling violations in ``text`` (empty ⇒ clean).

    ``handlers`` is the known registered-handler vocabulary (from the agent allowlists /
    handler registry); a handler NAME in generated prose is a binding a human must author,
    not advisory text. Pure + deterministic — no I/O. The text is canonicalised (NFKC +
    zero-width strip) before scanning so display-equivalent obfuscations cannot evade the
    patterns."""
    text = _canonicalize(text)
    return [
        *_scan(text, _VALUE_SCANS),
        *_handler_violations(text, handlers),
        *_scan(text, _VERB_SCANS),
    ]


# --- scoped variant for HAND-AUTHORED AT-2 governance free-text ------------------


def _role_violations(text: str, roles: frozenset[str]) -> list[Violation]:
    """An approver-ROLE token (an authoritative ``approver_role`` / ``escalate_to`` value)
    appearing in free-text is a leak — the role belongs in the typed DOA field, not prose
    (ADR-0025 D4). Exact-token containment, case-insensitive over the canonicalised text —
    robust for non-Latin role labels (e.g. Thai) where ``\\b`` is unreliable. ``text`` is
    already canonicalised by the caller; the role token is canonicalised here for symmetry."""
    folded = text.casefold()
    return [
        Violation(
            "role", role, f"the approver-role token '{role}' is a typed DOA value, never free-text"
        )
        for role in sorted(roles)
        if _canonicalize(role).casefold() in folded
    ]


def governance_prose_lint(text: str, *, roles: frozenset[str] = frozenset()) -> list[Violation]:
    """Scoped prose-lint for HAND-AUTHORED AT-2 governance free-text (PLAN-0042 Step 3 /
    ADR-0025 D4 / OQ-D) — empty ⇒ clean.

    Unlike :func:`prose_lint` (generated-prose-only — it deliberately over-flags, so it would
    block a hand-authored governance note that legitimately says 'HUMAN approves' / 'blocks the
    PO' or names a registered handler — finding 6), this variant runs the **value classes
    only** (``_VALUE_SCANS``: currency / magnitude / percent / decimal / numeric /
    spelled-number) plus an approver-**role**-token check, and OMITS the decision-verb /
    approval-phrase classes (``_VERB_SCANS``) and the broad snake/camel identifier catch.

    A ฿-amount / weight / approver-role token smuggled into AT-2 free-text (the waiver
    justification, a tier / criterion note, an AT-2-step description, the goal) is the exact
    anchor a human then copies into the typed field — so it **blocks load**; a decision verb or
    a registered handler name in a hand-authored note does **not**. Pure + deterministic; the
    text is canonicalised (NFKC + zero-width strip) before scanning."""
    text = _canonicalize(text)
    return [*_scan(text, _VALUE_SCANS), *_role_violations(text, roles)]
