"""Tests for the R8 pre-archive PLAN reference guard.

The load-bearing property is NOT "flags a dead path" -- it is **"flags a MOVED
path and nothing else"**. Measured on the real tree at s183, a naive
"path does not resolve" predicate flags 89 files (mostly placeholders like
``NNNN-name.md`` and never-written forward references) and is unusable as a
fail-closed gate, while the moved-only predicate flags 29 files, every one a
real dead pointer. The discriminator tests below are what keep that true.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tools.check_plan_archive_refs import (
    EnumerationError,
    find_violations,
    has_moved,
    is_exempt,
    tracked_files,
)

MOVED = "0094-loop-detect-non-progress-and-reset-paths.md"
LIVE = "0076-at2-followon-tracking-gate-seam-and-derivation-pin.md"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A tree with one ARCHIVED plan (done/ only) and one LIVE plan."""
    plans = tmp_path / "docs" / "plans"
    (plans / "done").mkdir(parents=True)
    (plans / "done" / MOVED).write_text("archived\n", encoding="utf-8")
    (plans / LIVE).write_text("live\n", encoding="utf-8")
    return tmp_path


def _write(root: Path, rel: str, body: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


# --- the core positive -----------------------------------------------------


def test_citation_of_a_moved_plan_is_a_violation(repo: Path) -> None:
    _write(repo, "docs/lessons/0033-x.md", f"See `docs/plans/{MOVED}` for detail.\n")
    found = find_violations(repo, [Path("docs/lessons/0033-x.md")])
    assert len(found) == 1
    rel, lineno, slug, _line = found[0]
    assert (rel, lineno, slug) == ("docs/lessons/0033-x.md", 1, MOVED)


# --- the discriminators: what must NOT trip --------------------------------


def test_placeholder_never_trips(repo: Path) -> None:
    """`NNNN-name.md` has no twin under done/, so it cannot be a moved path.

    This is the single property that makes the guard usable: a "must resolve"
    rule would flag every template, doc example and test fixture in the repo.
    """
    _write(
        repo,
        "docs/conventions/x.md",
        "Draft at `docs/plans/NNNN-name.md`, see also `docs/plans/NNNN-*.md`.\n",
    )
    assert find_violations(repo, [Path("docs/conventions/x.md")]) == []


def test_live_plan_path_never_trips(repo: Path) -> None:
    _write(repo, "docs/lessons/0033-x.md", f"See `docs/plans/{LIVE}`.\n")
    assert find_violations(repo, [Path("docs/lessons/0033-x.md")]) == []


def test_never_written_forward_reference_never_trips(repo: Path) -> None:
    """A path that never existed anywhere is a forward reference, not rot."""
    _write(repo, "docs/lessons/0033-x.md", "Planned: `docs/plans/0199-never-written.md`.\n")
    assert find_violations(repo, [Path("docs/lessons/0033-x.md")]) == []


def test_fenced_code_block_is_skipped(repo: Path) -> None:
    """A path inside a fence is DATA, not navigation.

    Real case: a lesson quoting the literal L1 counter key
    ``counter["counters"].pop("L1:docs/plans/0010-...md")``. Rewriting that to
    `done/` would falsify the historical record instead of repairing a link.
    """
    body = f'Prose is scanned.\n\n```python\ncounter.pop("L1:docs/plans/{MOVED}")\n```\n'
    _write(repo, "docs/lessons/0012-x.md", body)
    assert find_violations(repo, [Path("docs/lessons/0012-x.md")]) == []


def test_prose_after_a_closed_fence_is_scanned_again(repo: Path) -> None:
    """The fence toggle must not swallow the rest of the file."""
    body = f"```\ninside\n```\n\nSee `docs/plans/{MOVED}`.\n"
    _write(repo, "docs/lessons/0012-x.md", body)
    assert len(find_violations(repo, [Path("docs/lessons/0012-x.md")])) == 1


def test_tilde_fence_is_also_skipped(repo: Path) -> None:
    body = f"~~~\nSee docs/plans/{MOVED}\n~~~\n"
    _write(repo, "docs/lessons/0012-x.md", body)
    assert find_violations(repo, [Path("docs/lessons/0012-x.md")]) == []


# --- exemptions ------------------------------------------------------------


@pytest.mark.parametrize(
    "rel",
    [
        "tests/handoffs/test_x.py",
        "docs/plans/done/0009-x.md",
        "docs/status-archive/2026-h1-status.md",
        "docs/adr/0018-x.md",
    ],
)
def test_exempt_paths_are_not_scanned(repo: Path, rel: str) -> None:
    _write(repo, rel, f"See `docs/plans/{MOVED}`.\n")
    assert is_exempt(rel)
    assert find_violations(repo, [Path(rel)]) == []


def test_non_exempt_sibling_of_an_exempt_prefix_is_scanned(repo: Path) -> None:
    """`docs/plans/<active>.md` is scanned; only `docs/plans/done/` is exempt."""
    assert not is_exempt("docs/plans/0076-active.md")
    _write(repo, "docs/plans/0076-active.md", f"See `docs/plans/{MOVED}`.\n")
    assert len(find_violations(repo, [Path("docs/plans/0076-active.md")])) == 1


# --- predicate unit --------------------------------------------------------


def test_has_moved_requires_both_halves(repo: Path) -> None:
    assert has_moved(repo, MOVED) is True
    # live: present in plans/, so not moved even though done/ is a real dir
    assert has_moved(repo, LIVE) is False
    # absent from both
    assert has_moved(repo, "0199-never-written.md") is False
    # present in BOTH (mid-archival, or a duplicate) is NOT a dead pointer
    (repo / "docs" / "plans" / MOVED).write_text("also here\n", encoding="utf-8")
    assert has_moved(repo, MOVED) is False


# --- fail-closed enumeration ----------------------------------------------


def test_enumeration_failure_is_fatal_not_empty(tmp_path: Path) -> None:
    """A guard that cannot enumerate must NOT report a clean tree.

    Mirrors the R7 guard: "no files found" is indistinguishable from "the scan
    silently failed", which is the fail-OPEN shape these guards exist to prevent.
    """
    with pytest.raises(EnumerationError):
        tracked_files(tmp_path)  # not a git repo


def test_tracked_files_lists_a_real_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)  # noqa: S607
    (tmp_path / "a.md").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.md"], cwd=tmp_path, check=True)  # noqa: S607
    assert Path("a.md") in tracked_files(tmp_path)


# --- non-vacuity of the repo's own clean state -----------------------------


def test_the_real_repo_is_clean() -> None:
    """The guard must be GREEN on the tree it ships with.

    Deliberately an assertion, not a smoke test: R8 landed together with the
    17-file remediation, so a regression here means either a new dead pointer
    was authored or the remediation was reverted.
    """
    root = Path(__file__).resolve().parents[2]
    violations = find_violations(root, tracked_files(root))
    assert violations == [], f"{len(violations)} pre-archive PLAN reference(s): {violations[:5]}"
