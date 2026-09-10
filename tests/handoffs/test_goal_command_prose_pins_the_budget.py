"""PLAN-0123 AC-2 — the ``/goal`` command prose states the real budget, pinned to the constant.

🔴 **The drift this pins, measured s291.** ``.claude/commands/goal.md`` tells the agent
*"the total deterministic budget at Stop is 600 s"*. The gate's constant is
``DEFAULT_CHECK_BUDGET_S = 120`` (``_goal_gate.py``), changed at s275 because 600 s
was unreachable inside the Stop hook's 180 s timeout — and the s275 fix pinned the
constant to ``settings.json`` (``test_goal_gate_budget_fits_the_hook.py``) but never to
the prose that tells an agent how big a budget it may declare. So for ~16 sessions the
command an agent reads at declaration time overstated the budget by 5x, and nothing
could notice.

This is the same shape as that precedent test: two statements of one fact in two
files that cannot import each other, held together by a test that reads both. The
number is parsed from the sentence itself, so a rewording that drops the sentence is
INSUFFICIENT (A2 reddens) rather than a vacuous pass — a prose file with no budget
sentence must not read as "in agreement".

Ordering is deliberate: A2 (the sentence exists) is asserted BEFORE A1 (its number
matches), so probe P2b — delete the sentence — reddens exactly A2 and never reaches A1.
The parser passes a control on known text before its first real reading (Lesson #0056).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GOAL_MD = REPO_ROOT / ".claude" / "commands" / "goal.md"
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

import _goal_gate  # noqa: E402  — sys.path manipulation above

#: The one sentence the command uses to state the budget. Anchored on its wording, not
#: on a bare number, so an unrelated "600" elsewhere in the file can never satisfy it.
SENTENCE_RE = re.compile(r"total deterministic budget at Stop is\s+(\d+)\s*s\b")

#: Control: a fixture the parser must read correctly before any real reading is trusted.
_CONTROL_TEXT = "Scope each cmd — the total deterministic budget at Stop is 42 s (env); a skip"
_CONTROL_EXPECT = 42


def parse_budget_sentence(text: str) -> int | None:
    """The integer N in "total deterministic budget at Stop is N s", or None if absent."""
    match = SENTENCE_RE.search(text)
    return int(match.group(1)) if match else None


def test_the_parser_passes_its_own_control() -> None:
    """An uncontrolled instrument fails confidently, not loudly (Lesson #0056)."""
    got = parse_budget_sentence(_CONTROL_TEXT)
    print(f"control_expect={_CONTROL_EXPECT} control_got={got}")
    assert got == _CONTROL_EXPECT, f"control_got={got}"
    assert parse_budget_sentence("no such sentence here") is None


def test_the_prose_budget_is_pinned_to_the_constant() -> None:
    text = GOAL_MD.read_text(encoding="utf-8")
    prose = parse_budget_sentence(text)
    constant = _goal_gate.DEFAULT_CHECK_BUDGET_S
    sentence_found = prose is not None
    print(f"prose={prose} constant={constant} sentence_found={sentence_found}")

    # A2 — the sentence must exist; its absence is INSUFFICIENT, never a pass.
    assert sentence_found, f"sentence_found={sentence_found} — goal.md no longer states a budget"
    # A1 — and its number must be the constant the gate actually enforces.
    assert prose == constant, f"prose={prose} constant={constant}"
