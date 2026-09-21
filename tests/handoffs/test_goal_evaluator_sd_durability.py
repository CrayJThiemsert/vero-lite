"""A surfaced decision the ``goal-evaluator`` raises must survive the goal gate's rewrite.

The failure this pins, measured s316 (``docs/logs/2026-09-21-s316-goal-gate-seven-rounds.md``):
round 6 raised SD-2 in its final message only. The final message is read once by the
caller; the next round reads only ``goal.json``, and ``_goal_state.Evaluation`` had no
field the evaluator was told to put an SD in. Round 7 could not see SD-2 and said so.

The repair is a prompt rule (``.claude/agents/goal-evaluator.md``: SDs go in the entry's
``detail``), so the durability it promises is a property of TWO things this file drives
together: the gate's real rewrite path (``run_goal_gate`` -> ``save_goal``) and the schema
the prompt tells the evaluator to write.
"""

from __future__ import annotations

import dataclasses
import json
import re
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

import _goal_gate  # noqa: E402  — sys.path manipulation above
from _goal_gate import EVALUATOR_NAME, run_goal_gate  # noqa: E402
from _goal_state import Criterion, Evaluation, new_goal, record_evaluation, save_goal  # noqa: E402

AGENT_FILE = REPO_ROOT / ".claude" / "agents" / "goal-evaluator.md"

#: Shaped like s316's real SD-2, which is the one that was lost.
SD_TEXT = (
    "SD-2: does J2's 'both documents' mean two files or two changed bodies of text? "
    "— (a) two files (b) two changed bodies"
)


@pytest.fixture
def goal_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """An isolated goal path, no Telegram, a pinned fingerprint, an isolated battery lock."""
    path = tmp_path / "goal.json"
    monkeypatch.setenv("CLAUDE_GOAL_PATH", str(path))
    monkeypatch.delenv("CLAUDE_GOAL_CHECK_BUDGET_S", raising=False)
    monkeypatch.setenv("CLAUDE_PROBE_BATTERY_LOCK", str(tmp_path / "no-such-battery.lock"))
    monkeypatch.setattr(_goal_gate, "_ping_telegram", lambda *_a: None)
    monkeypatch.setattr(_goal_gate, "work_fingerprint", lambda: "fp-A")
    return path


def _seed_an_evaluator_round(path: Path) -> None:
    """Write goal.json as the evaluator leaves it: one FAIL round at the current fingerprint,
    its SD in ``detail`` AND, beside it, under a key the schema does not name.

    The second copy is written raw, the way the evaluator's own ``Edit`` would put it there —
    ``Evaluation`` cannot carry an unknown key, which is the point.
    """
    goal = new_goal(
        "g",
        [
            Criterion(
                id="C1",
                kind="check",
                cmd=f'"{sys.executable}" -c "import sys; sys.exit(0)"',
                desc="always green",
                timeout_s=30,
            ),
            Criterion(id="J1", kind="judge", desc="the doc resolves every OQ"),
        ],
    )
    record_evaluation(
        goal,
        Evaluation(
            ts="(evaluator: no clock)",
            fingerprint="fp-A",
            judged={"J1": {"verdict": "FAIL", "reason": "OQ-3 unresolved"}},
            evaluator=EVALUATOR_NAME,
            detail=SD_TEXT,
        ),
    )
    save_goal(goal, path)
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    raw["evaluations"][0]["surfaced"] = [SD_TEXT]
    path.write_text(json.dumps(raw, indent=2), encoding="utf-8")


def test_an_sd_in_detail_survives_the_gates_rewrite_and_an_invented_key_does_not(
    goal_file: Path,
) -> None:
    """🔴 The scenario: the real gate fires once over an evaluator round and rewrites the file.

    Three reads, each printed on failure: the rewrite happened (the entry count grew — without
    it, both halves below would pass on an untouched file); ``detail`` kept the SD; the
    invented key, holding the same SD, was stripped — the s316 loss, reproduced, which is the
    reason the prompt names ``detail`` and forbids inventing a key.
    """
    _seed_an_evaluator_round(goal_file)
    before = json.loads(goal_file.read_text(encoding="utf-8"))["evaluations"]
    # The positive control for the absence asserted last: the key IS there before the gate
    # runs, so "absent after" cannot be satisfied by a seed that never wrote it.
    assert "surfaced" in before[0], f"seed keys: {sorted(before[0])}"

    assert run_goal_gate({}) is None  # FAIL at an unchanged fingerprint: warn, no re-dispatch

    after = json.loads(goal_file.read_text(encoding="utf-8"))["evaluations"]
    pre, post = len(before), len(after)
    assert post > pre, f"the gate did not rewrite: pre={pre} post={post}"
    assert (
        after[0].get("detail") == SD_TEXT
    ), f"detail after the rewrite: {after[0].get('detail')!r}"
    assert "surfaced" not in after[0], f"keys after the rewrite: {sorted(after[0])}"


def _schema_block(text: str) -> str:
    """The ```json block of the evaluator's step 4 — the entry it is told to append."""
    match = re.search(r"```json\n(.*?)\n\s*```", text, re.S)
    assert match, "no ```json schema block in the goal-evaluator prompt"
    return match.group(1)


def test_every_key_the_prompt_tells_the_evaluator_to_write_survives_a_rewrite() -> None:
    """🔴 The prompt and the schema, read together. A top-level key the prompt names that
    ``Evaluation`` does not carry is a field the evaluator writes and the next ``save_goal``
    deletes — exactly how an SD evaporated in s316, so the two must never drift apart."""
    block = _schema_block(AGENT_FILE.read_text(encoding="utf-8"))
    # Top-level keys sit at the block's own indent; nested ones (verdict, reason…) sit deeper.
    indent = min(len(m.group(1)) for m in re.finditer(r'^( +)"\w+":', block, re.M))
    prompt_keys = set(re.findall(rf'^ {{{indent}}}"(\w+)":', block, re.M))
    schema_keys = {f.name for f in dataclasses.fields(Evaluation)}
    assert (
        prompt_keys - schema_keys == set()
    ), f"prompt names keys a rewrite strips: {sorted(prompt_keys - schema_keys)}"
    assert (
        "detail" in prompt_keys
    ), f"the prompt's entry schema has no detail: {sorted(prompt_keys)}"


def test_the_prompt_routes_surfaced_decisions_into_detail() -> None:
    """🔴 The rule itself, in the only input surface the evaluator reads (CLAUDE.md §4: a rule
    meant to bind an automated judge lives in that judge's input). Both places an SD is
    mentioned must send it to ``detail``: the step that writes the entry, and the output
    template's SD section, which is where the s316 SD was written instead."""
    text = AGENT_FILE.read_text(encoding="utf-8")
    sd_section = text.split("## Surfaced decisions", 1)[1].split("\n## ", 1)[0]
    assert "`detail`" in sd_section, f"SD section: {sd_section.strip()!r}"
    assert "Surfaced decisions go into `detail`" in text
