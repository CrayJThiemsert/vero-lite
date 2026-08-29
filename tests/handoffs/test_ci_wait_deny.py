"""The deny predicate for hand-rolled CI waits.

Both directions are pinned, and the SILENT direction is the load-bearing one. A gate
that blocks legitimate work gets disabled, and a disabled gate takes its diagnosis
with it — so every shape the gate must let through is enumerated here as explicitly
as the shapes it must stop.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

_HOOK = Path(__file__).resolve().parents[2] / ".claude" / "hooks" / "pretooluse_ci_wait_deny.py"

_spec = importlib.util.spec_from_file_location("ci_wait_deny", _HOOK)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
is_hand_rolled_ci_wait = _mod.is_hand_rolled_ci_wait


#: Every one of these is a real shape written during the 2026-08-29 incident.
DENIED = [
    "for i in $(seq 1 30); do gh pr checks 1312 > /tmp/c.txt; sleep 45; done",
    'until [ "$(gh api repos/o/r/actions/runs/123 --jq .status)" = "completed" ]; '
    "do sleep 40; done",
    "while true; do s=$(gh pr checks 1312); sleep 45; done",
    "while true; do gh run list --commit abc123 --json status; sleep 30; done",
]

#: The gate must be silent on all of these or it is obstruction.
ALLOWED = [
    # One-shot queries — the whole point is that these stay easy.
    "gh pr checks 1312",
    "gh run list --commit abc123 --json databaseId,status",
    "gh pr view 1312 --json state,mergedAt",
    # The prescribed route itself. If the gate denied its own remedy there would be
    # no way to comply at all.
    "uv run python -m tools.ci.wait_for_ci wait --sha e9e5f72",
    "uv run python -m tools.ci.wait_for_ci status --sha e9e5f72",
    # A loop with a sleep that polls something the tool does NOT cover. Denying this
    # would block work with no replacement available — 2 of the 9 waits measured in
    # the corpus were exactly this shape (a local benchmark dump).
    "until [ -f /tmp/run.done ]; do sleep 10; done",
    "while ! curl -sf http://192.168.1.133:11434/api/tags; do sleep 5; done",
    # A loop over PRs that calls gh but never sleeps — ordinary batch work.
    "for n in 1310 1311 1312; do gh pr view $n --json state; done",
    # A sleep with a gh call but no loop.
    "sleep 30; gh pr checks 1312",
]


@pytest.mark.parametrize("command", DENIED)
def test_hand_rolled_ci_waits_are_denied(command: str) -> None:
    assert is_hand_rolled_ci_wait(command), f"gate missed a hand-rolled CI wait: {command!r}"


@pytest.mark.parametrize("command", ALLOWED)
def test_legitimate_shapes_are_not_denied(command: str) -> None:
    """The direction that decides whether this gate survives contact with real work."""
    assert not is_hand_rolled_ci_wait(command), f"gate blocks legitimate work: {command!r}"


def test_all_three_conjuncts_are_required() -> None:
    """Loop AND sleep AND a CI poll. Dropping any one must stop the deny.

    Pinned because the tempting simplification — deny any loop containing `gh` — is
    what turns a 0.74% gate into one that blocks ordinary batch work and gets removed.
    """
    full = "while true; do gh run list --commit abc --json status; sleep 30; done"
    assert is_hand_rolled_ci_wait(full)
    assert not is_hand_rolled_ci_wait(full.replace("sleep 30; ", ""))
    assert not is_hand_rolled_ci_wait(
        full.replace("gh run list --commit abc --json status", "true")
    )
    assert not is_hand_rolled_ci_wait("gh run list --commit abc --json status; sleep 30")


def _run_hook(payload: dict) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(_HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout


def test_hook_denies_end_to_end_and_names_the_route() -> None:
    """A deny that does not say what to do instead gets worked around, not followed."""
    rc, out = _run_hook(
        {
            "tool_name": "Bash",
            "tool_input": {"command": "while true; do gh pr checks 1; sleep 30; done"},
        }
    )
    assert rc == 0
    decision = json.loads(out)["hookSpecificOutput"]
    assert decision["permissionDecision"] == "deny"
    assert "tools.ci.wait_for_ci" in decision["permissionDecisionReason"]


def test_hook_covers_the_monitor_tool_not_just_bash() -> None:
    """A Bash-only gate is bypassed by the harness's own wait primitive.

    Not hypothetical: the agent reached for `Monitor` mid-incident, and that call had
    zero hook coverage of any kind.
    """
    rc, out = _run_hook(
        {
            "tool_name": "Monitor",
            "tool_input": {"command": "while true; do gh pr checks 1; sleep 30; done"},
        }
    )
    assert rc == 0
    # Asserted BEFORE parsing, because "the gate said nothing" and "the gate said the
    # wrong thing" are different failures and only one of them is about the decision.
    # Parsing an empty string first would raise JSONDecodeError — a crash, which under
    # the witnessed-RED rule credits no claim at all.
    assert out.strip(), (
        "the gate produced no decision for a Monitor call, so Monitor is uncovered — "
        "and Monitor is the harness's own wait primitive, i.e. the natural way to "
        "write the very loop this gate exists to stop"
    )
    assert json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_hook_is_silent_for_unrelated_tools() -> None:
    rc, out = _run_hook(
        {
            "tool_name": "Write",
            "tool_input": {"command": "while true; do gh pr checks 1; sleep 30; done"},
        }
    )
    assert rc == 0
    assert out.strip() == ""


def test_hook_fails_open_on_unreadable_input() -> None:
    """A gate that cannot read its input must not block work."""
    proc = subprocess.run(
        [sys.executable, str(_HOOK)],
        input="not json at all",
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""
