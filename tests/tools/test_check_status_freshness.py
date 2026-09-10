"""``tools/check_status_freshness.py`` — the exit-code contract, witnessed RED.

The guard has exactly one hard assertion (``head_commit`` resolves on the baseline)
and one visibility promise (drift is printed, never gated). Each is pinned here
against a throwaway git repository built per test, so the RED witness does not
depend on the real tree's state — the real tree is exercised separately by
``test_guards_hold_on_the_real_tree.py``, which asserts only that the guard *accepts*
it.

Every case prints the values it measured in its assertion message, so a failure
names what broke instead of starting a hunt (Lesson #0043).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GUARD = REPO_ROOT / "tools" / "check_status_freshness.py"
TOKEN = "STATUS-FRESHNESS:"

_GIT_IDENTITY = ["-c", "user.name=t", "-c", "user.email=t@example.invalid"]


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *_GIT_IDENTITY, *args],  # noqa: S607  ("git" via PATH — the house idiom)
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _commit(root: Path, subject: str) -> str:
    """One substantive commit; returns its short sha."""
    marker = root / "f.txt"
    marker.write_text(marker.read_text() + subject + "\n" if marker.exists() else subject + "\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", subject)
    return _git(root, "rev-parse", "--short", "HEAD")


def _write_status(root: Path, head_commit: str | None) -> None:
    status = root / "docs" / "STATUS.md"
    status.parent.mkdir(parents=True, exist_ok=True)
    if head_commit is None:
        status.write_text("---\nsession: 1\n---\n\n# no head_commit here\n")
    else:
        status.write_text(f"---\nhead_commit: {head_commit}\nsession: 1\n---\n\n# x\n")


def _repo(tmp_path: Path, branch: str = "main") -> tuple[Path, str]:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "checkout", "-q", "-b", branch)
    sha = _commit(root, "feat: first")
    return root, sha


def _run(root: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(GUARD), str(root)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout + proc.stderr


def test_fresh_pointer_exits_zero_and_prints_zero_drift(tmp_path: Path) -> None:
    root, sha = _repo(tmp_path)
    _write_status(root, sha)
    rc, out = _run(root)
    assert rc == 0, f"rc={rc} out={out!r}"
    assert TOKEN in out and "drift=0" in out and "fresh=True" in out, f"out={out!r}"


def test_drift_is_printed_not_gated(tmp_path: Path) -> None:
    """The visibility promise: a stale-but-valid pointer is exit 0 with the number shown."""
    root, sha = _repo(tmp_path)
    _write_status(root, sha)
    _commit(root, "feat: second")
    _commit(root, "fix: third")
    rc, out = _run(root)
    assert rc == 0, f"rc={rc} out={out!r}"
    assert "drift=2" in out and "fresh=False" in out, f"out={out!r}"


def test_reconcile_commits_do_not_count_as_drift(tmp_path: Path) -> None:
    """A ``docs(status):`` commit is the reconcile itself; it must not inflate drift."""
    root, sha = _repo(tmp_path)
    _write_status(root, sha)
    _commit(root, "docs(status): reconcile")
    rc, out = _run(root)
    assert rc == 0 and "drift=0" in out, f"rc={rc} out={out!r}"


def test_unresolvable_head_commit_exits_one(tmp_path: Path) -> None:
    """🔴 The RED witness for the one hard assertion.

    Same fixture shape as the fresh case; only the sha is corrupted. This is the
    mutation that must flip 0 -> 1, and the message must name the sha.
    """
    root, _sha = _repo(tmp_path)
    _write_status(root, "0000000")
    rc, out = _run(root)
    assert rc == 1, f"rc={rc} out={out!r}"
    assert "0000000" in out and "does NOT resolve" in out, f"out={out!r}"


def test_missing_head_commit_exits_one(tmp_path: Path) -> None:
    root, _sha = _repo(tmp_path)
    _write_status(root, None)
    rc, out = _run(root)
    assert rc == 1, f"rc={rc} out={out!r}"
    assert "MISSING" in out, f"out={out!r}"


def test_missing_status_file_exits_one(tmp_path: Path) -> None:
    root, _sha = _repo(tmp_path)
    rc, out = _run(root)
    assert rc == 1, f"rc={rc} out={out!r}"


def test_baseline_unavailable_is_a_visible_skip(tmp_path: Path) -> None:
    """No ``main`` branch: exit 0 but the skip is PRINTED, so it cannot read as a pass."""
    root, sha = _repo(tmp_path, branch="trunk")
    _write_status(root, sha)
    rc, out = _run(root)
    assert rc == 0, f"rc={rc} out={out!r}"
    assert "UNAVAILABLE" in out and "NOT a pass" in out, f"out={out!r}"


@pytest.mark.parametrize("bad", ["", "   ", "not-a-sha-at-all"])
def test_degenerate_head_commit_values_exit_one(tmp_path: Path, bad: str) -> None:
    root, _sha = _repo(tmp_path)
    _write_status(root, bad)
    rc, out = _run(root)
    assert rc == 1, f"bad={bad!r} rc={rc} out={out!r}"
