"""AC-9 controls for the reading-shape replay (PLAN-0123 §4.5).

Three controls, run **before the first real reading is trusted**: the detector
still matches the three census commands it was written from (in-sample —
credits nothing, it only proves the detector is not dead); a fixture of twenty
benign commands fires zero; and a shape occurring twice in one session fires
once.

Two of these are the probe targets AC-9 names. P9a widens the grep clause to any
``grep`` — the benign fixture must redden, which it can only do because that
fixture deliberately contains a plain ``grep -n``. P9b drops the dedup — the
two-occurrence fixture must redden. A fixture without a bare grep would make P9a
vacuous, so :data:`BENIGN_COMMANDS` carries one on purpose.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.reading_shape_replay import (
    CONTROL_COMMANDS,
    reachable,
    reading_shapes,
    replay,
)

# A plain ``grep -n`` sits here deliberately: it is what makes probe P9a able to
# redden this fixture. Removing it would leave P9a witnessing nothing.
BENIGN_COMMANDS = [
    "git status --short",
    "ls -la docs/",
    "pytest -q tests/tools",
    "git log --oneline -1",
    'grep -n "def main" tools/absent.py',
    "ruff check .",
    "mypy --strict services/",
    "git diff --stat",
    "cat pyproject.toml",
    "python -m tools.goal_template list",
    "git rev-parse HEAD",
    "uv run --no-sync pytest -q",
    "git branch --show-current",
    "echo hello",
    "mkdir -p /tmp/scratch",
    "cp a.txt b.txt",
    "git add -A",
    "git commit -F /tmp/msg.txt",
    "gh pr list --state open",
    "python tools/check_battery_definitions.py",
]


def write_transcript(path: Path, commands: list[str], following: str = "ok") -> Path:
    """Synthesise a minimal transcript carrying *commands* as Bash tool_use."""
    with path.open("w", encoding="utf-8") as handle:
        for command in commands:
            record = {
                "type": "assistant",
                "isSidechain": False,
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "tool_use", "name": "Bash", "input": {"command": command}}
                    ],
                },
            }
            handle.write(json.dumps(record) + "\n")
            note = {
                "type": "assistant",
                "isSidechain": False,
                "message": {"role": "assistant", "content": [{"type": "text", "text": following}]},
            }
            handle.write(json.dumps(note) + "\n")
    return path


# --------------------------------------------------------------------------
# Control 1 — the positive control. In-sample by construction.
# --------------------------------------------------------------------------


def test_control_all_three_census_commands_are_reachable() -> None:
    per_command = {label: reading_shapes(cmd) for label, cmd in CONTROL_COMMANDS}
    print(f"reachable={reachable()}/3 per_command={per_command}")
    assert reachable() == 3, f"detector went dead on the census commands: {per_command}"


@pytest.mark.parametrize(("label", "command"), CONTROL_COMMANDS)
def test_each_census_command_matches_at_least_one_shape(label: str, command: str) -> None:
    shapes = reading_shapes(command)
    print(f"{label} shapes={shapes}")
    assert shapes, f"census command {label} matched no shape"


# --------------------------------------------------------------------------
# Control 2 — the negative control. Probe P9a reddens this.
# --------------------------------------------------------------------------


def test_benign_fixture_fires_zero(tmp_path: Path) -> None:
    path = write_transcript(tmp_path / "benign.jsonl", BENIGN_COMMANDS)
    result = replay({"benign": path})
    matched = {c: reading_shapes(c) for c in BENIGN_COMMANDS if reading_shapes(c)}
    print(
        f"corpus_calls={result.corpus_calls} raw_matches={result.raw_matches} "
        f"deduped_fires={len(result.fires)} matched={matched}"
    )
    assert result.corpus_calls == len(BENIGN_COMMANDS)
    assert result.raw_matches == 0, f"benign commands matched: {matched}"
    assert len(result.fires) == 0


def test_benign_fixture_contains_a_bare_grep_so_p9a_can_redden() -> None:
    """Positive control on the negative control: P9a needs something to widen onto."""
    bare = [c for c in BENIGN_COMMANDS if "grep" in c]
    print(f"bare_grep_commands={bare}")
    assert bare, "P9a would be vacuous — no bare grep in the benign fixture"


# --------------------------------------------------------------------------
# Control 3 — dedup. Probe P9b reddens this.
# --------------------------------------------------------------------------


def test_one_shape_twice_in_a_session_fires_once(tmp_path: Path) -> None:
    commands = ["wc -l docs/STATUS.md", "echo spacer", "wc -l CLAUDE.md"]
    path = write_transcript(tmp_path / "dedup.jsonl", commands)
    result = replay({"s000": path})
    print(
        f"corpus_calls={result.corpus_calls} raw_matches={result.raw_matches} "
        f"deduped_fires={len(result.fires)} shapes={[f.shape for f in result.fires]}"
    )
    assert result.corpus_calls == 3
    assert result.raw_matches == 2, "both wc -l calls must count toward the raw rate"
    assert len(result.fires) == 1, "once per session per shape"
    assert result.fires[0].shape == "wc_l"


def test_the_same_shape_in_a_different_session_fires_again(tmp_path: Path) -> None:
    """Dedup is per session, not global — otherwise F could never reach 21."""
    a = write_transcript(tmp_path / "a.jsonl", ["wc -l a.md"])
    b = write_transcript(tmp_path / "b.jsonl", ["wc -l b.md"])
    result = replay({"sA": a, "sB": b})
    print(f"deduped_fires={len(result.fires)} sessions={[f.session for f in result.fires]}")
    assert len(result.fires) == 2


# --------------------------------------------------------------------------
# The detector's own boundaries, so a widened clause is visible.
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ('grep -c -i "timeout" log.jsonl', ("grep_c",)),
        ("grep -rc pattern src/", ("grep_c",)),
        ("grep -L TODO src/*.py", ("grep_L",)),
        ('grep -n "def" x.py', ()),
        ("grep --color=always foo x.py", ()),
        ("wc -l < file.txt", ("wc_l",)),
        ("wc -c file.txt", ()),
        ("pgrep -af run_benchmark", ("pgrep",)),
        ("sed -n '1,20p' f | grep '^model:'", ("sed_n_grep",)),
        ("sed -n '1,20p' f", ()),
        ("cat f | head -20", ("pipe_head",)),
        ("cat f | tail -5", ("pipe_tail",)),
        ("head -20 f", ()),
    ],
)
def test_detector_boundaries(command: str, expected: tuple[str, ...]) -> None:
    got = reading_shapes(command)
    print(f"cmd={command!r} shapes={got} expected={expected}")
    assert got == expected
