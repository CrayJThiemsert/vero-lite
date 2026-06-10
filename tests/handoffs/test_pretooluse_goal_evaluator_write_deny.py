"""Tests for ``.claude/hooks/pretooluse_goal_evaluator_write_deny.py``.

Matrix row **adversarial-3** (PLAN-0021): the SD-1 narrowed-Write boundary.
This hook enforces the `goal-evaluator` subagent write-path allowlist —
the H2 single-file pattern of `pretooluse_status_scribe_write_deny.py`,
narrowed to `.claude/state/goal.json`.

Boundaries asserted here:

* The allowlist is exactly `.claude/state/goal.json` — the sibling state
  files (`stop-chain.json`, `loop-counter.json`), `docs/STATUS.md` (which the
  *status-scribe* hook allows), plan/ADR files, code, and out-of-repo paths
  are all **denied**.
* Per ADR-013 D2 the hook is **fail-CLOSED**: malformed JSON, missing
  `tool_input`, or a non-string `file_path` all deny the call.
* Cross-platform normalization: Windows-UNC, drive-letter, and POSIX inputs
  resolve identically (the shared `/vero-lite/` marker idiom).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / ".claude" / "hooks" / "pretooluse_goal_evaluator_write_deny.py"

Payload = dict[str, Any]
Parsed = dict[str, Any] | None

ALLOWED = ".claude/state/goal.json"


def _run(payload: Payload | str) -> tuple[int, Parsed]:
    env = os.environ.copy()
    stdin = payload if isinstance(payload, str) else json.dumps(payload)
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    out = result.stdout.strip()
    parsed = json.loads(out) if out else None
    return result.returncode, parsed


def _is_deny(parsed: Parsed) -> bool:
    if not parsed:
        return False
    decision = parsed.get("hookSpecificOutput", {}).get("permissionDecision")
    return bool(decision == "deny")


def _write(file_path: Any) -> Payload:
    return {"tool_name": "Write", "tool_input": {"file_path": file_path, "content": "x"}}


def _edit(file_path: Any) -> Payload:
    return {
        "tool_name": "Edit",
        "tool_input": {"file_path": file_path, "old_string": "a", "new_string": "b"},
    }


# --- allow: exactly the goal file, any path spelling ---


def test_write_goal_json_relative_allowed() -> None:
    rc, parsed = _run(_write(ALLOWED))
    assert rc == 0
    assert parsed is None  # pass-through: no decision emitted


def test_edit_goal_json_relative_allowed() -> None:
    rc, parsed = _run(_edit(ALLOWED))
    assert rc == 0
    assert parsed is None


def test_write_goal_json_absolute_posix_allowed() -> None:
    rc, parsed = _run(_write(str(REPO_ROOT / ".claude" / "state" / "goal.json")))
    assert rc == 0
    assert parsed is None


def test_write_goal_json_windows_unc_allowed() -> None:
    unc = (
        "\\\\wsl.localhost\\ubuntu-24.04\\home\\crayj\\work\\vero-lite"
        "\\.claude\\state\\goal.json"
    )
    rc, parsed = _run(_write(unc))
    assert rc == 0
    assert parsed is None


# --- deny: everything else (adversarial-3 families) ---


def test_sibling_state_files_denied() -> None:
    for sibling in (".claude/state/stop-chain.json", ".claude/state/loop-counter.json"):
        rc, parsed = _run(_write(sibling))
        assert rc == 0
        assert _is_deny(parsed), f"{sibling} must be denied"


def test_status_md_denied_here() -> None:
    """The status-scribe hook allows docs/STATUS.md; THIS hook must not."""
    rc, parsed = _run(_write("docs/STATUS.md"))
    assert rc == 0
    assert _is_deny(parsed)


def test_plan_and_code_paths_denied() -> None:
    for target in (
        "docs/plans/0021-axis-b-verification-loop-build.md",
        "docs/adr/0018-axis-b-verification-loop.md",
        ".claude/hooks/_goal_gate.py",
        "services/api/main.py",
    ):
        rc, parsed = _run(_write(target))
        assert rc == 0
        assert _is_deny(parsed), f"{target} must be denied"


def test_out_of_repo_path_denied() -> None:
    rc, parsed = _run(_write("/tmp/goal.json"))  # noqa: S108 — adversarial fixture path
    assert rc == 0
    assert _is_deny(parsed)


def test_goal_json_name_elsewhere_denied() -> None:
    """A file merely NAMED goal.json outside .claude/state/ is not the goal."""
    rc, parsed = _run(_write("docs/goal.json"))
    assert rc == 0
    assert _is_deny(parsed)


def test_edit_denied_outside_allowlist() -> None:
    rc, parsed = _run(_edit("docs/lessons/0023-status-md-rotation.md"))
    assert rc == 0
    assert _is_deny(parsed)


# --- fail-closed families ---


def test_malformed_json_denies() -> None:
    rc, parsed = _run("{not json")
    assert rc == 0
    assert _is_deny(parsed)


def test_missing_tool_input_denies() -> None:
    rc, parsed = _run({"tool_name": "Write"})
    assert rc == 0
    assert _is_deny(parsed)


def test_non_dict_tool_input_denies() -> None:
    rc, parsed = _run({"tool_name": "Write", "tool_input": "goal.json"})
    assert rc == 0
    assert _is_deny(parsed)


def test_missing_file_path_denies() -> None:
    rc, parsed = _run({"tool_name": "Edit", "tool_input": {"old_string": "a"}})
    assert rc == 0
    assert _is_deny(parsed)


def test_non_string_file_path_denies() -> None:
    rc, parsed = _run({"tool_name": "Write", "tool_input": {"file_path": 42}})
    assert rc == 0
    assert _is_deny(parsed)


def test_empty_file_path_denies() -> None:
    rc, parsed = _run(_write(""))
    assert rc == 0
    assert _is_deny(parsed)


# --- non-watched tools pass through (matcher is the selector) ---


def test_non_watched_tool_passes_through() -> None:
    rc, parsed = _run({"tool_name": "Read", "tool_input": {"file_path": "docs/STATUS.md"}})
    assert rc == 0
    assert parsed is None


def test_deny_reason_names_the_boundary() -> None:
    _, parsed = _run(_write("docs/STATUS.md"))
    assert parsed is not None
    reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
    assert "goal-evaluator" in reason
    assert "goal.json" in reason
