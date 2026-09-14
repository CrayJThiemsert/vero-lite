"""No render may land in the checkout's own ``.claude/state/`` while the suite runs (s297).

🔴 **Measured, not hypothesised.** ``tools/goal_template.py`` writes each real
(non-dry-run) render's check scripts and evidence directory under ``.claude/state/``.
``tests/tools/test_goal_template_lifecycle.py`` drives it through a subprocess, which no
``monkeypatch`` reaches, so every run of that file added four directories to the
checkout's ``goal-checks/`` and ``goal-evidence/``: **36 → 40**, while
``test_goal_template_shell_quoting.py`` — which patches both roots in-process — held
**36 → 36**. Of the 36 directories found in s297, **34** belonged to no goal record.
Nothing reddened, because the directories are gitignored; that silence is why this file
exists. It is the s295 ``GIT_*`` incident's class: a test mutating the real checkout.

Two halves, and the tests cover each: the renderer honours ``CLAUDE_GOAL_STATE_DIR``
(``resolve_state_dir``, pure), and ``tests/conftest.py`` sets it at import to a temp
directory outside the checkout. The scenario case drives the REAL renderer CLI into the
REAL goal-file reader the Stop gate uses (``_goal_state.load_goal``) and asks where the
files that goal names actually are — not where the code intends them to be.

Probes: ``tests/batteries/s297-goal-state-isolation.json``.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / ".claude" / "hooks"))

from _goal_state import KIND_CHECK, load_goal  # noqa: E402 — sys.path bootstrap above

_REAL_STATE = _ROOT / ".claude" / "state"
_GID = re.compile(r"goal-checks/(\d{8}T\d{6}-[0-9a-f]{8})/")
_CMD_PREFIX = "wsl.exe --exec bash "


# --- the pure half: resolve_state_dir -------------------------------------------


def test_the_override_re_roots_the_state_dir(tmp_path: Path) -> None:
    from tools.goal_template import resolve_state_dir

    elsewhere = tmp_path / "elsewhere"
    got = resolve_state_dir({"CLAUDE_GOAL_STATE_DIR": str(elsewhere)}, _ROOT)
    assert got == elsewhere, f"got={got} want={elsewhere}"


def test_no_override_means_the_checkouts_state_dir() -> None:
    from tools.goal_template import resolve_state_dir

    got = resolve_state_dir({}, _ROOT)
    assert got == _REAL_STATE, f"got={got} want={_REAL_STATE}"


def test_an_empty_override_is_no_override() -> None:
    """``Path("")`` is the working directory: an empty value treated as a path would
    scatter goal state wherever the process happened to start."""
    from tools.goal_template import resolve_state_dir

    got = resolve_state_dir({"CLAUDE_GOAL_STATE_DIR": ""}, _ROOT)
    assert got == _REAL_STATE, f"got={got} want={_REAL_STATE}"


# --- the structural half: tests/conftest.py -------------------------------------


def test_the_suite_points_the_renderer_outside_the_checkout() -> None:
    """The guard is only structural if nobody has to remember it — so check it is on.

    The third assertion is the drift guard between two copies of one name:
    ``tests/conftest.py`` cannot import the renderer to read ``STATE_DIR_ENV`` (the
    import would resolve the roots before the variable is set), so it spells the name.
    """
    from tools import goal_template

    value = os.environ.get("CLAUDE_GOAL_STATE_DIR")
    module_dir = goal_template.STATE_DIR
    assert value, f"CLAUDE_GOAL_STATE_DIR={value!r}: tests/conftest.py must set it at import"
    assert not Path(value).resolve().is_relative_to(_ROOT), f"override={value} root={_ROOT}"
    assert module_dir == Path(value), f"module STATE_DIR={module_dir} env={value}"


# --- the scenario: real CLI -> real goal file -> the gate's real reader ----------


def test_a_real_render_names_scripts_that_exist_and_none_in_the_checkout(
    tmp_path: Path,
) -> None:
    """Render a goal for real, load it the way the Stop gate does, and follow its paths.

    The assertions are ordered so each can be witnessed alone: a probe that moves the
    scripts back into the checkout reddens A2 with A1 green; one that writes them
    nowhere the goal names reddens A3 with A2 green; the evidence pair likewise.
    A2 and A4 are negative claims, and A3 and A5 are their positive controls — an
    absence in the checkout means something only once the files are shown to exist.
    """
    override = Path(os.environ.get("CLAUDE_GOAL_STATE_DIR") or "<unset>")
    log = tmp_path / "log.jsonl"
    log.write_text('{"transport":"ok"}\n', encoding="utf-8")
    goal_file = tmp_path / "goal.json"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.goal_template",
            "T-COUNT",
            "--file",
            str(log),
            "--field",
            "transport",
            "--expect",
            "ok",
            "--goal-file",
            str(goal_file),
            "--history-root",
            str(tmp_path / "goal-history"),
        ],
        capture_output=True,
        text=True,
        cwd=str(_ROOT),
        env={**os.environ, "PYTHONPATH": str(_ROOT)},
        check=False,
    )
    goal = load_goal(goal_file)
    cmds = [c.cmd or "" for c in goal.criteria if c.kind == KIND_CHECK] if goal else []
    gids = sorted({g for cmd in cmds for g in _GID.findall(cmd)})
    scripts = [Path(cmd.removeprefix(_CMD_PREFIX)) for cmd in cmds]
    gid = gids[0] if gids else "<none>"
    real_checks = _REAL_STATE / "goal-checks" / gid
    real_evidence = _REAL_STATE / "goal-evidence" / gid
    override_evidence = override / "goal-evidence" / gid
    placed = [(str(p), p.is_file(), p.is_relative_to(override)) for p in scripts]
    print(
        f"exit={proc.returncode} checks={len(cmds)} gids={gids} override={override} "
        f"real_checks_dir={real_checks.exists()} real_evidence_dir={real_evidence.exists()}"
    )

    assert len(gids) == 1, f"A1: gids={gids} exit={proc.returncode} tail={proc.stdout[-300:]!r}"
    assert not real_checks.exists(), f"A2: scripts written into the checkout: {real_checks}"
    assert placed and all(ok and inside for _, ok, inside in placed), f"A3: {placed}"
    assert not real_evidence.exists(), f"A4: evidence dir made in the checkout: {real_evidence}"
    assert (
        override_evidence.is_dir()
    ), f"A5: no evidence dir under the override: {override_evidence}"
