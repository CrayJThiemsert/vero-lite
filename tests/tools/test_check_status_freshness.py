"""``tools/check_status_freshness.py`` — the exit-code contract, witnessed RED.

The guard has two hard assertions (``head_commit`` resolves on the baseline; a staged
STATUS carries drift 0) and one visibility promise (otherwise drift is printed, never
gated). Each is pinned here against a throwaway git repository built per test, so the
RED witness does not depend on the real tree's state — the real tree is exercised by
``test_guards_hold_on_the_real_tree.py`` (the guard *accepts* it) and by AC-19 below
(it reads ``mode=print`` there).

Every case prints the values it measured in its assertion message, so a failure
names what broke instead of starting a hunt (Lesson #0043).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GUARD = REPO_ROOT / "tools" / "check_status_freshness.py"
PRECOMMIT_CONFIG = REPO_ROOT / ".pre-commit-config.yaml"
TOKEN = "STATUS-FRESHNESS:"

_GIT_IDENTITY = ["-c", "user.name=t", "-c", "user.email=t@example.invalid"]


def _git(root: Path, *args: str, env: dict[str, str] | None = None) -> str:
    proc = subprocess.run(
        ["git", *_GIT_IDENTITY, *args],  # noqa: S607  ("git" via PATH — the house idiom)
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    return proc.stdout.strip()


def _commit(root: Path, subject: str, name: str = "f.txt") -> str:
    """One substantive commit; returns its short sha."""
    marker = root / name
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


def _run(root: Path, env: dict[str, str] | None = None) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(GUARD), str(root)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        env=env,
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


# --- PLAN-0125 Step 0 (SD-1 = c, Cray typed s299): drift gates only a STAGED STATUS -------
#
# Every reading below is the guard's own printed line, parsed back — never an import of
# the behaviour under test, never a mocked git.


def _parse(out: str) -> dict[str, str]:
    """The ``key=value`` fields of the guard's FIRST ``STATUS-FRESHNESS:`` line."""
    for line in out.splitlines():
        if line.startswith(TOKEN):
            return dict(tok.split("=", 1) for tok in line[len(TOKEN) :].split() if "=" in tok)
    return {}


#: A gate run's two lines. The second carries its own ``drift=`` so a parser that read
#: the wrong line would return a different value, not the same one by coincidence.
_KNOWN_OUTPUT = (
    f"{TOKEN} head=abc1234 newest=def5678 drift=2 fresh=False staged=True mode=gate "
    "baseline_lag=n/a\n"
    f"{TOKEN} docs/STATUS.md is STAGED with drift=9 — point head_commit at main's tip — exit 1\n"
)


def test_the_line_parser_reads_a_known_output() -> None:
    """Instrument control (Lesson #0056): every AC-17 / AC-19 reading goes through ``_parse``."""
    got = _parse(_KNOWN_OUTPUT)
    assert got == {
        "head": "abc1234",
        "newest": "def5678",
        "drift": "2",
        "fresh": "False",
        "staged": "True",
        "mode": "gate",
        "baseline_lag": "n/a",
    }, f"got={got!r}"


def _history(tmp_path: Path) -> Path:
    """AC-17's repository, fixed before any run.

    STATUS names the first commit. After it land a ``docs(status):`` reconcile, then two
    substantive commits (one on a side branch), then the merge commit bringing the side
    branch in. The range holds four commits and the substantive drift is **2**, so a
    reading of 2 can only come from the count that skips merges and reconciles.
    """
    root, first = _repo(tmp_path)
    _write_status(root, first)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "docs(status): reconcile at the first commit")
    _git(root, "checkout", "-q", "-b", "side")
    _commit(root, "feat: second", name="side.txt")
    _git(root, "checkout", "-q", "main")
    _commit(root, "fix: third")
    _git(root, "merge", "-q", "--no-ff", "-m", "Merge branch 'side'", "side")
    return root


def _touch_status(root: Path, note: str) -> None:
    status = root / "docs" / "STATUS.md"
    status.write_text(status.read_text() + note + "\n")


def test_a_staged_status_with_drift_gates(tmp_path: Path) -> None:
    """AC-17 (A): STATUS edited and staged while ``main`` is 2 substantive commits ahead."""
    root = _history(tmp_path)
    _touch_status(root, "a TODO-row edit")
    _git(root, "add", "docs/STATUS.md")
    rc, out = _run(root)
    got = _parse(out)
    assert (got.get("staged"), got.get("mode"), rc) == ("True", "gate", 1), (
        f"A: staged={got.get('staged')} mode={got.get('mode')} rc={rc} "
        f"drift={got.get('drift')} out={out!r}"
    )
    assert (
        got.get("drift") == "2"
    ), f"A: drift={got.get('drift')} (substantive, expected 2) out={out!r}"


def test_a_staged_status_pointing_at_the_tip_passes(tmp_path: Path) -> None:
    """AC-17 (B): the control that the gate is not "STATUS staged => red"."""
    root = _history(tmp_path)
    _write_status(root, _git(root, "rev-parse", "--short", "main"))
    _git(root, "add", "docs/STATUS.md")
    rc, out = _run(root)
    got = _parse(out)
    assert (got.get("staged"), got.get("mode"), rc) == ("True", "gate", 0), (
        f"B: staged={got.get('staged')} mode={got.get('mode')} rc={rc} "
        f"drift={got.get('drift')} out={out!r}"
    )


def test_another_staged_file_only_prints_drift(tmp_path: Path) -> None:
    """AC-17 (C): a non-STATUS commit at drift 2 — drift alone never gates."""
    root = _history(tmp_path)
    (root / "other.txt").write_text("unrelated\n")
    _git(root, "add", "other.txt")
    rc, out = _run(root)
    got = _parse(out)
    assert (got.get("staged"), got.get("mode"), rc) == ("False", "print", 0), (
        f"C: staged={got.get('staged')} mode={got.get('mode')} rc={rc} "
        f"drift={got.get('drift')} out={out!r}"
    )


def test_nothing_staged_is_the_all_files_shape(tmp_path: Path) -> None:
    """AC-17 (D): an empty staged set — the ``--all-files`` / CI shape."""
    root = _history(tmp_path)
    rc, out = _run(root)
    got = _parse(out)
    assert (got.get("staged"), got.get("mode"), rc) == ("False", "print", 0), (
        f"D: staged={got.get('staged')} mode={got.get('mode')} rc={rc} "
        f"drift={got.get('drift')} out={out!r}"
    )
    assert (
        got.get("baseline_lag") == "n/a"
    ), f"D: baseline_lag={got.get('baseline_lag')} (no remote, expected n/a) out={out!r}"


def test_a_partial_commit_index_is_the_set_that_is_read(tmp_path: Path) -> None:
    """AC-17 (E): ``git commit -a`` / ``-- <paths>`` hand hooks a TEMPORARY index.

    STATUS is edited in the working tree and staged only into that temporary index; the
    default index never sees it. ``tests/conftest.py`` strips every inherited ``GIT_*``,
    so the variable is set explicitly on this one child and cannot reach it by accident.
    """
    root = _history(tmp_path)
    _touch_status(root, "a partial-commit edit")
    env = {**os.environ, "GIT_INDEX_FILE": str(root / ".git" / "step0-partial-index")}
    _git(root, "read-tree", "HEAD", env=env)
    _git(root, "add", "docs/STATUS.md", env=env)
    rc, out = _run(root, env=env)
    got = _parse(out)
    control_rc, control_out = _run(root)
    control = _parse(control_out)
    assert got.get("staged") == "True", (
        f"E: staged={got.get('staged')} mode={got.get('mode')} rc={rc} "
        f"(control, no GIT_INDEX_FILE: staged={control.get('staged')} rc={control_rc}) "
        f"out={out!r}"
    )


# AC-18: the two pointer texts carry the ruling, not the question.
_OLD_POINTER = "PLAN-0125 SD-1, Cray's to rule"
_NEW_POINTER = "PLAN-0125 SD-1 = c, Cray, typed, s299"


def _count(path: Path, needle: str) -> int:
    return sum(line.count(needle) for line in path.read_text(encoding="utf-8").splitlines())


def test_the_guard_docstring_carries_the_ruling() -> None:
    old, new = _count(GUARD, _OLD_POINTER), _count(GUARD, _NEW_POINTER)
    assert old == 0, f"guard: old post={old} new post={new}"
    assert new == 1, f"guard: old post={old} new post={new}"


def test_the_precommit_comment_carries_the_ruling() -> None:
    old, new = _count(PRECOMMIT_CONFIG, _OLD_POINTER), _count(PRECOMMIT_CONFIG, _NEW_POINTER)
    assert old == 0, f"yaml: old post={old} new post={new}"
    assert new == 1, f"yaml: old post={old} new post={new}"


def test_the_real_tree_reads_print_mode_on_a_clean_index() -> None:
    """AC-19: the guard over this checkout, as pre-commit runs it on a non-STATUS commit.

    ``drift`` and ``baseline_lag`` are printed, never pinned — they move with ``main``.
    Two visible skips, neither a pass: STATUS staged in the real index (not the shape
    this reads), and a checkout without a local ``main`` (CI's shallow clone).
    """
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],  # noqa: S607
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    if "docs/STATUS.md" in staged:
        pytest.skip("docs/STATUS.md is staged in the real index — AC-19 reads a clean index")
    rc, out = _run(REPO_ROOT)
    if "UNAVAILABLE" in out:
        pytest.skip(f"no local baseline in this checkout — skipped, NOT a pass: {out.strip()!r}")
    got = _parse(out)
    assert got.get("mode") == "print", f"real: mode={got.get('mode')} rc={rc} out={out!r}"
    assert rc == 0, f"real: mode={got.get('mode')} rc={rc} out={out!r}"
