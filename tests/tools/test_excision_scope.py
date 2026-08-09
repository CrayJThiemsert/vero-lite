"""Tests for ``tools/excision_scope.py``.

The scenario case below is not a synthetic toy: it reproduces the **actual
three-module shape** that defeated PLAN-0102's scope review — a shared state
layer carrying a marker enum, a gate that reads it, and an observer whose
doomed function exclusively owns a small private subsystem. The names are the
real ones so a reader can line the fixture up against the incident.

The oracle is history, not invention: we know from the executed PLAN exactly
which symbols a backwards-only review missed, so the test asserts the tool
surfaces them — and, just as load-bearing, that it does NOT surface the
symbols a surviving caller keeps alive.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL = REPO_ROOT / "tools" / "excision_scope.py"
sys.path.insert(0, str(REPO_ROOT))

from tools.excision_scope import BLIND_SPOTS, collect, compute, render  # noqa: E402

# --- the fixture: the real PLAN-0102 shape, three modules -------------------

_COUNTER = '''
"""Shared state layer — serves the doomed guard AND the surviving ones."""
import os

MAX_CONTENT_HASHES = 32          # only note_content_hash reads it (doomed)
LOOP_TRIGGER_THRESHOLD = 6       # read by a SURVIVOR -> must live
L1_DOC_THRESHOLD = 15            # only l1_threshold_for reads it (doomed)
STATE_DIR = os.environ.get("STATE", "/tmp/state")   # module-level read -> lives


class LoopType:
    FILE_EDIT = "L1"
    BASH_PATTERN = "L4"


def is_doc_target(target):
    return target.endswith(".md")


def l1_threshold_for(target):
    return L1_DOC_THRESHOLD if is_doc_target(target) else LOOP_TRIGGER_THRESHOLD


def note_content_hash(entry, digest):
    while len(entry) > MAX_CONTENT_HASHES:
        entry.pop()
    return entry


def has_triggered(count, threshold=LOOP_TRIGGER_THRESHOLD):
    return count >= threshold


def normalize_file_path(p):
    return p.replace("\\\\", "/")
'''

_GATE = '''
"""PreToolUse gate — reads the marker; also serves the surviving loop type."""
from _counter import LoopType, has_triggered, l1_threshold_for, normalize_file_path


def _resolve_target(tool_name, tool_input):
    if tool_name in ("Write", "Edit"):
        return (LoopType.FILE_EDIT, normalize_file_path(tool_input["file_path"]))
    if tool_name == "Bash":
        return (LoopType.BASH_PATTERN, tool_input["command"])
    return None


def main(payload):
    match = _resolve_target(payload["tool_name"], payload["tool_input"])
    if match is None:
        return 0
    loop_type, target = match
    threshold = l1_threshold_for(target)
    return 1 if has_triggered(payload["count"], threshold) else 0
'''

# The observer is the incident: ``_apply_commit_reset`` exclusively owns
# ``_is_git_commit`` / ``_committed_files`` / ``_GIT`` / the ``shutil`` import,
# and NONE of those four carry an "L1" token in their name.
_OBSERVER = '''
"""PostToolUse observer — the commit-boundary reset lives on the Bash path."""
import re
import shutil

from _counter import LoopType, note_content_hash

_GIT = shutil.which("git") or "git"
_GIT_COMMIT_RE = re.compile(r"git commit")


def _is_git_commit(command):
    return bool(_GIT_COMMIT_RE.search(command))


def _committed_files(root):
    return [_GIT, root]


def _apply_commit_reset(counter, command):
    if not _is_git_commit(command):
        return False
    for path in _committed_files("."):
        counter.pop(path, None)
    return True


def _apply_l4(counter, command):
    """SURVIVES. Shares nothing with the commit reset."""
    counter[LoopType.BASH_PATTERN] = command
    return True


def _handle_write_or_edit(payload):
    return note_content_hash(payload["entry"], payload["digest"])


def main(payload):
    if payload["tool_name"] == "Bash":
        _apply_l4(payload["counter"], payload["command"])
        _apply_commit_reset(payload["counter"], payload["command"])
    else:
        _handle_write_or_edit(payload)
    return 0
'''


@pytest.fixture
def hooks_dir(tmp_path: Path) -> Path:
    d = tmp_path / "hooks"
    d.mkdir()
    (d / "_counter.py").write_text(_COUNTER, encoding="utf-8")
    (d / "gate.py").write_text(_GATE, encoding="utf-8")
    (d / "observer.py").write_text(_OBSERVER, encoding="utf-8")
    return d


# The set a BACKWARDS-only review produces: every site that touches the marker.
BACKWARDS_ONLY = [
    "LoopType.FILE_EDIT",
    "_resolve_target",
    "_apply_commit_reset",
    "_handle_write_or_edit",
    "l1_threshold_for",
    "note_content_hash",
]


def _orphan_names(result: dict[str, list[str]]) -> set[str]:
    """Bare symbol names out of the human-readable rows (``module::name  (...)``)."""
    return {row.split("  ")[0].split("::", 1)[1] for row in result["orphaned"]}


def test_scenario_it_finds_exactly_what_the_backwards_only_review_missed(
    hooks_dir: Path,
) -> None:
    """The real oracle: the three cascades PLAN-0102's Steps failed to name.

    Driving the real collector into the real fixpoint over three realistic
    modules — no stubbing on either side of the seam under test.
    """
    result = compute(collect([hooks_dir]), set(BACKWARDS_ONLY))
    found = _orphan_names(result)

    # (1) the commit-reset subsystem — four symbols, none named "L1"
    assert {
        "_is_git_commit",
        "_committed_files",
        "_GIT",
        "_GIT_COMMIT_RE",
    } <= found, f"missed the commit-reset cascade; found {sorted(found)}"
    # ...including the import ruff WOULD have caught, so the tool is a superset
    assert "shutil" in found

    # (2) constants reachable only from a doomed helper
    assert {"L1_DOC_THRESHOLD", "MAX_CONTENT_HASHES"} <= found

    # (3) the helper called only by a doomed helper
    assert "is_doc_target" in found


def test_it_does_not_orphan_symbols_a_survivor_still_uses(hooks_dir: Path) -> None:
    """The non-vacuity half: over-reporting would be worse than useless.

    ``LOOP_TRIGGER_THRESHOLD`` is read by ``has_triggered``, which the surviving
    gate calls; ``STATE_DIR`` is read at module level. Both must stay out of the
    orphan list — a tool that names everything is a tool nobody can act on.
    """
    result = compute(collect([hooks_dir]), set(BACKWARDS_ONLY))
    found = _orphan_names(result)

    for survivor in ("LOOP_TRIGGER_THRESHOLD", "has_triggered", "_apply_l4", "STATE_DIR"):
        assert survivor not in found, f"{survivor} has a surviving caller but was reported"


def test_module_level_use_keeps_a_symbol_alive(hooks_dir: Path) -> None:
    """A symbol read at import time can never be exclusively owned.

    ``_GIT`` is assigned at module level FROM ``shutil`` — but it is only READ
    inside ``_committed_files``, so it does orphan. ``STATE_DIR`` is read at
    module scope by nothing else and is never orphaned. This pins the
    distinction, which is the one that decides whether a constant is safe.
    """
    result = compute(collect([hooks_dir]), {"_committed_files"})
    found = _orphan_names(result)
    assert "_GIT" in found, "a constant read only by the deleted function must orphan"
    assert "STATE_DIR" not in found


def test_it_flags_a_named_symbol_that_still_has_a_surviving_caller(hooks_dir: Path) -> None:
    """Deleting `has_triggered` would break the gate — say so, do not stay quiet."""
    result = compute(collect([hooks_dir]), {"has_triggered"})
    assert result["still_used"], "deleting a live symbol produced no warning"
    assert any("has_triggered" in row for row in result["still_used"])


def test_an_empty_deletion_set_orphans_nothing(hooks_dir: Path) -> None:
    """Guard the guard: if this ever reports rows, the fixpoint is unsound."""
    result = compute(collect([hooks_dir]), set())
    assert result["orphaned"] == []


def test_the_report_declares_its_own_blind_spots(hooks_dir: Path) -> None:
    """The tool is not exempt from the lesson it exists to serve.

    ``docs/lessons/0039`` is about a predicate that reflects only what its
    author imagined. This tool's predicate is exactly that — a static reference
    graph — so presenting its output as complete would reproduce the failure it
    is meant to prevent. Every run must say so.

    RED when: someone trims the banner to make the output tidier.
    """
    text = render(compute(collect([hooks_dir]), set(BACKWARDS_ONLY)), set(BACKWARDS_ONLY))
    assert "NOT A VERDICT" in text
    for blind_spot in BLIND_SPOTS:
        assert blind_spot in text
    assert "getattr" in text


def test_same_name_in_two_modules_does_not_collapse(tmp_path: Path) -> None:
    """Two modules defining ``_state_path`` are two nodes, not one.

    **This is a regression test for a real miss, found the only way it could
    be.** The first version of the tool keyed symbols by bare name globally. The
    hooks tree defines ``_state_path`` three times; one copy kept a live caller,
    so the collapsed node read as alive and the tool reported nothing — missing
    the exact example its own docstring led with. A fixture would not have
    caught it; running the tool against the REAL pre-excision tree did.

    RED when: node identity stops being module-qualified, or ``_resolve`` stops
    preferring the local definition.
    """
    d = tmp_path / "hooks"
    d.mkdir()
    (d / "doomed.py").write_text(
        "DEFAULT = '/a'\n\n"
        "def _state_path():\n    return DEFAULT\n\n"
        "def _apply_reset():\n    return _state_path()\n",
        encoding="utf-8",
    )
    (d / "survivor.py").write_text(
        "DEFAULT = '/b'\n\n"
        "def _state_path():\n    return DEFAULT\n\n"
        "def _handle_bash():\n    return _state_path()\n",
        encoding="utf-8",
    )

    result = compute(collect([d]), {"_apply_reset"})
    rows = set(result["orphaned"])

    assert any(
        r.startswith("doomed::_state_path") for r in rows
    ), f"the doomed module's _state_path was not orphaned; got {sorted(rows)}"
    assert any(r.startswith("doomed::DEFAULT") for r in rows), "its constant should follow"
    assert not any(
        r.startswith("survivor::") for r in rows
    ), "the identically-named survivor was reported — nodes collapsed again"


def test_a_misspelled_symbol_is_reported_rather_than_silently_ignored(
    hooks_dir: Path,
) -> None:
    """A typo shrinks the answer to nothing and looks exactly like 'all clear'.

    Nothing orphans off a symbol that does not exist, so a silent no-match is
    the most dangerous output this tool could produce.
    """
    result = compute(collect([hooks_dir]), {"_apply_commit_rest"})  # missing 'e'
    assert result["unknown"] == ["_apply_commit_rest"]
    assert result["orphaned"] == []


def test_cli_runs_against_the_live_hooks_tree() -> None:
    """End-to-end through ``main()`` on the REAL repo, not a fixture.

    Uses a symbol that exists today; asserts only exit code and the banner, so
    it cannot rot when the hooks change.
    """
    result = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--root",
            str(REPO_ROOT / ".claude" / "hooks"),
            "--delete",
            "_apply_l4",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "NOT A VERDICT" in result.stdout


def test_cli_fails_loudly_on_a_missing_root() -> None:
    result = subprocess.run(
        [sys.executable, str(TOOL), "--root", "/nope/not/here", "--delete", "x"],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 2
    assert "no such path" in result.stderr
