"""🔴 s276 — a bare ``uv run`` empties the shared ``.venv``, silently.

``uv run`` without ``--no-sync`` re-syncs the project environment **without** the
dev extra, uninstalling pytest / ruff / mypy / pre-commit to match the base
dependency set. The command that does it **succeeds**, so nothing reports the
damage; it surfaces later as an unrelated "command not found" or a lazily-imported
plugin's ``ImportError``.

Measured session 276: a specialist subagent did exactly this mid-session and left
``.venv/bin/`` holding a single ``python3`` symlink.

**Why a hook and not an agent-definition clause.** All four project agents
(`explore-research`, `goal-evaluator`, `plan-drafter`, `status-scribe`) *deny*
Bash, so the actor here is a built-in agent type whose definition is not in this
repo. The only surface that sees every actor's Bash call is a hook.

**Why advisory and not a deny.** ``scripts/bootstrap.sh`` uses the bare form
legitimately — a fresh clone has no venv to strip — so the deny rubric's "no
legitimate need once the alternative exists" conjunct fails
(`pretooluse_ci_wait_deny.py`), and this repo has measured what a gate with a
carve-out becomes.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

import posttooluse_progress_observer as observer  # noqa: E402


def test_a_bare_uv_run_is_flagged() -> None:
    """The guard. Prints the command it judged, never a bare boolean."""
    cmd = "uv run pytest -q"
    got = observer._venv_strip_warning(cmd)
    assert got is not None, f"bare `uv run` not flagged: {cmd!r}"
    assert "--no-sync" in got, "the advisory must name the fix, not just the fault"
    assert "uv sync --extra dev" in got, "it must also name the repair for an already-stripped venv"


def test_the_safe_form_is_silent() -> None:
    """🟢 POSITIVE CONTROL, and the load-bearing one.

    Without it, a predicate that fired unconditionally would satisfy the assertion
    above perfectly. This is what proves the flag is about the MISSING flag and not
    about the string ``uv run`` appearing at all.
    """
    assert observer._venv_strip_warning("uv run --no-sync pytest -q") is None


def test_neighbouring_uv_commands_are_silent() -> None:
    """🟢 The other half of the control: the predicate is not "any uv command".

    ``uv sync --extra dev`` is the documented repair and must never be flagged as
    the disease; ``uvx`` runs an ephemeral tool and touches no project venv.
    """
    for safe in ("uv sync --extra dev", "uvx ruff check .", "pytest -q", "python -m pytest"):
        assert observer._venv_strip_warning(safe) is None, f"false positive on {safe!r}"


def test_it_finds_the_bare_form_mid_command() -> None:
    """The real shape: a chained command, which is how every agent writes these."""
    got = observer._venv_strip_warning("cd ~/work/vero-lite && uv run python tools/x.py")
    assert got is not None


def test_both_advisories_can_be_emitted_together() -> None:
    """The join. The hook may print only ONE json object, so a command that trips
    both the shell-hygiene rule and this one must not lose either message —
    the failure mode that would otherwise silently drop whichever ran second."""
    cmd = "uv run pytest -q | head -n 5"
    hygiene = observer._shell_hygiene_warning(cmd)
    venv = observer._venv_strip_warning(cmd)
    assert hygiene is not None, "expected the pipe-to-truncator rule to fire too"
    assert venv is not None
    assert hygiene != venv, "the two advisories must be distinguishable"


def test_prose_that_merely_mentions_a_bare_uv_run_is_silent() -> None:
    """🔴 REGRESSION, measured s276 one minute after the advisory shipped.

    The unanchored predicate fired on this feature's own PR-creation command — a
    ``gh pr create --title "…name a bare uv run the moment it empties…"`` — because
    it matched the words inside a quoted argument, next token ``the``. An advisory
    that fires on *talking about* the hazard is one its reader learns to skip,
    which the sibling advisory's own docstring records happening at a 30.8%
    firing rate.

    So ``uv run`` must sit at a COMMAND position: start of string, after a
    separator, after a newline, or directly after an opening quote (the
    ``bash -lc "uv run …"`` shape). Reached by a space, in prose, it is not a
    command.
    """
    prose = [
        'gh pr create --title "name a bare uv run the moment it empties the venv"',
        "echo the rule is: never a bare uv run here",
        'git commit -m "fix: stop a bare uv run from stripping the venv"',
    ]
    for cmd in prose:
        assert observer._venv_strip_warning(cmd) is None, f"false positive on prose: {cmd!r}"


def test_the_command_position_shapes_all_still_fire() -> None:
    """🟢 The control for the anchoring above: tightening must not have made the
    guard blind. Each of these is a real shape an agent writes."""
    for cmd in (
        "uv run pytest -q",
        "cd ~/work/vero-lite && uv run python tools/x.py",
        'wsl bash -lc "uv run pytest"',
    ):
        assert observer._venv_strip_warning(cmd) is not None, f"missed a real command: {cmd!r}"
