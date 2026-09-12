"""The suite is structurally immune to an inherited ``GIT_DIR`` / ``GIT_WORK_TREE``.

Session 295 ``export``ed both in a shell that then ran ``pytest -q``. ``git`` stops
discovering a repository from ``cwd`` the moment ``GIT_DIR`` is set, so every fixture
that builds a throwaway repository wrote into the REAL one: the shared ``.git/config``
gained ``user.name=Test`` / ``user.email=test@example.com``, and a branch ``trunk``
appeared with ``HEAD`` moved onto it. ``tests/conftest.py`` now strips every inherited
``GIT_*`` at import; this file is the half that proves it.

The scenario case drives a real child ``pytest`` into the real git fixtures with both
variables set — pointed at a THROWAWAY repository, never the real one. The two nodes it
drives were measured writing under pollution in s296, one per dimension the snapshot
compares.

Every case prints the values it measured, so a failure names what broke instead of
starting a hunt (Lesson #0043).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import git_env_keys_to_strip

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Measured in s296, not guessed: the first node rewrites ``user.name`` / ``user.email``
#: in whatever repository ``GIT_DIR`` names, the second creates ``trunk`` there and moves
#: ``HEAD`` onto it. Between them they touch every field :func:`_snapshot` compares.
CHILD_NODES = (
    "tests/vero_bridge/test_lint_status.py::test_fresh_when_status_points_at_newest_substantive",
    "tests/tools/test_check_status_freshness.py"
    "::test_fresh_pointer_exits_zero_and_prints_zero_drift",
)

#: A child pytest imports the whole conftest tree; generous, but bounded so a regression
#: reddens instead of hanging the suite (the posture in test_db_guard_second_arriver.py).
CHILD_TIMEOUT_S = 300.0

#: This file's own absence assertion, used as a child payload below. In the parent it
#: cannot fail — nothing exported ``GIT_*`` here; spawned with both variables set, it can.
SELF_ABSENCE_NODE = (
    "tests/test_git_env_guard.py::test_this_process_has_no_inherited_git_variables_left"
)


def _git(repo: Path, *args: str) -> str:
    """Run git in ``repo``; ``check=True`` because this is setup, not a claim."""
    proc = subprocess.run(
        ["git", *args],  # noqa: S607  ("git" via PATH — the house idiom)
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


@pytest.fixture
def victim(tmp_path: Path) -> Path:
    """A throwaway repository standing where the real one stood in s295."""
    repo = tmp_path / "victim"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "victim-owner")
    _git(repo, "config", "user.email", "victim@example.invalid")
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "seed.txt")
    _git(repo, "commit", "-q", "-m", "victim seed")
    return repo


def _snapshot(repo: Path) -> dict[str, str]:
    """Exactly the three things the s295 incident changed on the real repository."""
    git_dir = repo / ".git"
    return {
        "config": (git_dir / "config").read_text(encoding="utf-8"),
        "HEAD": (git_dir / "HEAD").read_text(encoding="utf-8"),
        "refs": _git(repo, "for-each-ref", "--format=%(refname) %(objectname)"),
    }


def _run_child(
    victim: Path, nodes: tuple[str, ...] = CHILD_NODES
) -> subprocess.CompletedProcess[str]:
    """A real child pytest with both variables pointed at ``victim`` — the s295 shape."""
    env = dict(os.environ)
    env["GIT_DIR"] = str(victim / ".git")
    env["GIT_WORK_TREE"] = str(victim)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "pytest", *nodes, "-q", "-p", "no:cacheprovider"],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=CHILD_TIMEOUT_S,
        check=False,
    )


def test_a_polluted_child_leaves_the_victim_repository_byte_identical(victim: Path) -> None:
    """The claim: an inherited GIT_DIR reaches nothing the child shells out to."""
    before = _snapshot(victim)
    child = _run_child(victim)
    after = _snapshot(victim)

    assert after == before, (
        "an inherited GIT_DIR/GIT_WORK_TREE reached the child's git subprocesses "
        f"(child rc={child.returncode})\n"
        f"config: {before['config']!r}\n     -> {after['config']!r}\n"
        f"HEAD:   {before['HEAD']!r} -> {after['HEAD']!r}\n"
        f"refs:   {before['refs']!r} -> {after['refs']!r}"
    )


def test_the_polluted_child_still_passes(victim: Path) -> None:
    """The non-vacuity control for the case above.

    A child that died at import would also leave the victim untouched, and the
    byte-identical assertion would pass for the wrong reason. So the nodes have to
    actually run — and pass — with both variables set.
    """
    child = _run_child(victim)
    assert child.returncode == 0, (
        f"child rc={child.returncode}; the guard neutralised the variables only if the "
        f"nodes themselves still pass\n--- child stdout (tail) ---\n{child.stdout[-2000:]}"
    )


def test_a_polluted_child_process_has_no_git_variables_left(victim: Path) -> None:
    """The absence assertion, run where it is capable of failing.

    :func:`test_this_process_has_no_inherited_git_variables_left` passes trivially in
    THIS process — nothing exported ``GIT_*`` here, so it would stay green with the guard
    deleted. Spawned as a child with both variables set, the same node reddens unless the
    guard really strips them. That is the positive control which makes the absence mean
    something (CLAUDE.md §8: a negative assertion carries its own control or is vacuous).
    """
    child = _run_child(victim, (SELF_ABSENCE_NODE,))
    assert child.returncode == 0, (
        f"child rc={child.returncode} — the guard did not clean the child's environment"
        f"\n--- child stdout (tail) ---\n{child.stdout[-2000:]}"
    )


def test_the_snapshot_sees_a_config_change(victim: Path) -> None:
    """Positive control: an unchanged reading means nothing from a blind instrument."""
    before = _snapshot(victim)
    _git(victim, "config", "user.email", "mutated@example.invalid")
    after = _snapshot(victim)
    assert (
        after["config"] != before["config"]
    ), f"the snapshot cannot see a config write: {before['config']!r} == {after['config']!r}"


def test_the_snapshot_sees_a_new_ref(victim: Path) -> None:
    """The same control for the other dimension — s295 created a branch, not just config."""
    before = _snapshot(victim)
    _git(victim, "branch", "control-branch")
    after = _snapshot(victim)
    assert (
        after["refs"] != before["refs"]
    ), f"the snapshot cannot see a new ref: {before['refs']!r} == {after['refs']!r}"


def test_every_git_prefixed_name_is_stripped() -> None:
    env = {"GIT_DIR": "/x", "GIT_WORK_TREE": "/y", "GIT_CONFIG_COUNT": "1", "PATH": "/usr/bin"}
    assert git_env_keys_to_strip(env) == [
        "GIT_CONFIG_COUNT",
        "GIT_DIR",
        "GIT_WORK_TREE",
    ], f"stripped {git_env_keys_to_strip(env)} from {sorted(env)}"


def test_github_variables_are_not_git_variables() -> None:
    """CI's own environment must survive the sweep — ``GITHUB_`` is not ``GIT_``."""
    env = {"GITHUB_TOKEN": "t", "GITHUB_ACTIONS": "true", "GITHUB_SHA": "abc"}
    assert git_env_keys_to_strip(env) == [], f"stripped {git_env_keys_to_strip(env)}"


def test_the_keep_list_is_consulted() -> None:
    """The policy knob is real: a named variable survives, everything else does not."""
    env = {"GIT_DIR": "/x", "GIT_ASKPASS": "/p"}
    keep = {"GIT_ASKPASS"}
    assert git_env_keys_to_strip(env, keep=keep) == [
        "GIT_DIR"
    ], f"stripped {git_env_keys_to_strip(env, keep=keep)}"


def test_this_process_has_no_inherited_git_variables_left() -> None:
    """The guard ran at import — asserted on the live process, not on a copy.

    Registered plainly: run from a clean shell this CANNOT fail, so on its own it closes
    nothing. It earns its keep as the payload of
    :func:`test_a_polluted_child_process_has_no_git_variables_left`, which runs this very
    node in a child spawned with ``GIT_DIR`` and ``GIT_WORK_TREE`` set.
    """
    leftover = git_env_keys_to_strip(os.environ)
    assert leftover == [], f"conftest left {leftover} in the test process environment"
