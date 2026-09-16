"""The fact-pack contract lives in each writer's own prompt (PLAN-0125 §4, Step 3, AC-13).

CLAUDE.md §4's placement rule is the reason these assertions exist at all: *"a rule meant
to bind an automated judge or enforcer … must live in that enforcer's own input surface;
written anywhere else it is, for that consumer, not written."* The three writers below are
those consumers, and their input surface is the agent prompt file — so the only way to
know the contract binds them is to read the sentence out of the file.

Each needle is asserted **once**, in its own test, because one mutation witnesses only one
assertion (CLAUDE.md §8). The probes are ``P-13.1`` … ``P-13.4`` in
``tests/batteries/plan-0125-step3.json``; each deletes one sentence and only that needle's
reading reddens.

Every reading is taken over **whitespace-normalized** text. A prompt file is hand-wrapped
prose that a later edit will re-wrap, and a needle pinned to one line would then fail for a
reason that has nothing to do with the contract — a false red that teaches the next author
to weaken the assertion (Lesson #0056: repair a check by deriving the right expectation,
never by relaxing the one that just failed). Normalizing asks the question that is actually
being asked: does the sentence exist, in any wrapping?
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS = REPO_ROOT / ".claude" / "agents"

SCRIBE = AGENTS / "status-scribe.md"
DRAFTER = AGENTS / "plan-drafter.md"
RESEARCH = AGENTS / "explore-research.md"

#: §4.2 — the two payload fields arrive as blocks the scribe cannot type.
SCRIBE_CONTRACT = "--recipe status-reconcile"
#: §6 E4 / SD-9 = a — the rule that stops the `Window = …` literal regrowing after the
#: next reconcile deletes it. No rule ever prescribed the literal (G46), so only its
#: absence from the prior header would have stopped the scribe — and that is not a rule.
SCRIBE_SD9 = "the entries present are the window"
#: §4.1 — the closed set of four grounding marks.
DRAFTER_LEGEND = "An execution fact with no block is never ✔"
#: §4.3 / SD-6 = b — this agent has no way to run the emitter, so any block it wrote
#: would be model-typed prose wearing a measurement's fields.
RESEARCH_NO_BLOCK = "You never emit a `measure` block"

#: The instrument control. Every test below reads it too: a counter that cannot return 0
#: for an absent sentence cannot vouch for the 1 it returns for a present one.
ABSENT = "no-such-contract-sentence-ever-written"


def _normalized(path: Path) -> str:
    """The file's text with every run of whitespace collapsed to one space."""
    return " ".join(path.read_text(encoding="utf-8").split())


def test_the_scribe_prompt_names_the_recipe_its_payload_arrives_from() -> None:
    """AC-13 scribe(contract) — `head_commit` / `recent_commits` as `measure/v1` blocks."""
    text = _normalized(SCRIBE)
    got = (text.count(SCRIBE_CONTRACT), text.count(ABSENT))
    assert got == (1, 0), (
        f"AC-13 scribe(contract): (post, control)={got!r} expected (1, 0) — "
        f"needle={SCRIBE_CONTRACT!r} in {SCRIBE}"
    )


def test_the_scribe_prompt_carries_the_sd9_ledger_rule() -> None:
    """AC-13 scribe(SD-9) — the ledgers declare no `Window = …`."""
    text = _normalized(SCRIBE)
    got = (text.count(SCRIBE_SD9), text.count(ABSENT))
    assert got == (1, 0), (
        f"AC-13 scribe(SD-9): (post, control)={got!r} expected (1, 0) — "
        f"needle={SCRIBE_SD9!r} in {SCRIBE}"
    )


def test_the_drafter_prompt_carries_the_four_mark_legend() -> None:
    """AC-13 drafter — the closed set of four marks, and the rule that closes it."""
    text = _normalized(DRAFTER)
    got = (text.count(DRAFTER_LEGEND), text.count(ABSENT))
    assert got == (1, 0), (
        f"AC-13 drafter: (post, control)={got!r} expected (1, 0) — "
        f"needle={DRAFTER_LEGEND!r} in {DRAFTER}"
    )


def test_the_research_prompt_refuses_to_emit_a_block() -> None:
    """AC-13 research — SD-6 = (b): cite `file:line`, never a model-typed block."""
    text = _normalized(RESEARCH)
    got = (text.count(RESEARCH_NO_BLOCK), text.count(ABSENT))
    assert got == (1, 0), (
        f"AC-13 research: (post, control)={got!r} expected (1, 0) — "
        f"needle={RESEARCH_NO_BLOCK!r} in {RESEARCH}"
    )
