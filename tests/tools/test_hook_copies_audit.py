"""Tests for the AC-10 hook-copies audit (PLAN-0122, SD-6 audit-only).

Every case is SYNTHETIC, and that is deliberate rather than convenient. The real
finding this tool records — 19 worktrees on 8 distinct versions of
``stop_continuation.py`` — exists only on the dev machine; CI checks out a fresh
clone with zero worktrees. An assertion against the real tree would therefore
pass locally, redden in CI, and be reporting the environment rather than the
tool. What is asserted here is that the tool READS EACH COPY; what it finds is an
operational report, not a build verdict.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.hook_copies_audit import SUBJECTS, audit, collect

CLASSIFIER = "_sonnet_classifier.py"
STOP_HOOK = "stop_continuation.py"


def _hooks(root: Path, name: str, body: str) -> None:
    """Write a full hook set into `root` (the main tree) or a named worktree."""
    base = root if name == "main" else root / ".claude" / "worktrees" / name
    hooks = base / ".claude" / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    for subject in SUBJECTS:
        (hooks / subject).write_text(f"# {subject}\n{body}\n", encoding="utf-8")


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """A repo root whose main tree carries the shipped bytes."""
    _hooks(tmp_path, "main", "SHIPPED")
    return tmp_path


# --- enumeration -----------------------------------------------------------


def test_a_tree_with_no_worktrees_reports_only_the_main_copy(tree: Path) -> None:
    """Zero worktrees is a legitimate state — a fresh clone, and CI."""
    report = audit(tree)
    assert report.worktrees == 0
    assert report.distinct == {CLASSIFIER: 1, STOP_HOOK: 1}
    assert report.stale == []
    assert report.main_readable is True


def test_a_directory_without_hooks_is_not_a_checkout(tree: Path) -> None:
    """Noise under .claude/worktrees/ must not inflate the count."""
    (tree / ".claude" / "worktrees" / "scratch").mkdir(parents=True)
    assert audit(tree).worktrees == 0


def test_a_matching_worktree_adds_a_copy_but_no_new_hash(tree: Path) -> None:
    _hooks(tree, "twin", "SHIPPED")
    report = audit(tree)
    assert report.worktrees == 1
    assert report.distinct == {CLASSIFIER: 1, STOP_HOOK: 1}
    assert report.stale == []


# --- P10a: the positive control that the tool reads each copy --------------


def test_one_changed_byte_increments_the_hash_count(tree: Path) -> None:
    """P10a. A worktree differing by ONE byte must move the count.

    This is the whole load-bearing claim: the tool hashes CONTENT, it does not
    count directories. Under a directory-counting implementation every
    assertion here still passes except this one.
    """
    _hooks(tree, "twin", "SHIPPED")
    stale_hook = tree / ".claude" / "worktrees" / "twin" / ".claude" / "hooks" / STOP_HOOK
    stale_hook.write_text(stale_hook.read_text(encoding="utf-8") + "#", encoding="utf-8")

    report = audit(tree)
    assert report.worktrees == 1
    assert report.distinct[STOP_HOOK] == 2
    # The classifier was NOT touched, so its count must stay at 1 — otherwise
    # the tool is keying on the directory rather than on each subject file.
    assert report.distinct[CLASSIFIER] == 1
    assert report.stale == ["twin"]


def test_every_worktree_is_read_not_just_the_first(tree: Path) -> None:
    """Three worktrees on three different versions must yield four hashes."""
    for name, body in (("a", "V1"), ("b", "V2"), ("c", "V3")):
        _hooks(tree, name, body)
    report = audit(tree)
    assert report.worktrees == 3
    assert report.distinct == {CLASSIFIER: 4, STOP_HOOK: 4}  # 3 + main
    assert report.stale == ["a", "b", "c"]


def test_a_worktree_missing_a_subject_is_reported_stale_not_dropped(
    tree: Path,
) -> None:
    """A worktree predating a hook is a real state, not an absence to skip."""
    _hooks(tree, "old", "SHIPPED")
    (tree / ".claude" / "worktrees" / "old" / ".claude" / "hooks" / CLASSIFIER).unlink()
    report = audit(tree)
    assert report.worktrees == 1
    assert report.stale == ["old"]
    assert report.distinct[CLASSIFIER] == 2  # the shipped hash, plus None


# --- the vacuity control ---------------------------------------------------


def test_an_unreadable_main_copy_fails_closed(tmp_path: Path) -> None:
    """The control that discriminates, chosen because zero worktrees does not.

    An enumerator that cannot find the one copy guaranteed to exist is broken,
    not looking at a clean tree.
    """
    report = audit(tmp_path)
    assert report.main_readable is False


def test_collect_names_the_main_tree_and_each_worktree(tree: Path) -> None:
    _hooks(tree, "zeta", "V1")
    _hooks(tree, "alpha", "V2")
    main, worktrees = collect(tree)
    assert main.name == "main"
    # Sorted, so a report diffed between runs does not churn on directory order.
    assert [c.name for c in worktrees] == ["alpha", "zeta"]
