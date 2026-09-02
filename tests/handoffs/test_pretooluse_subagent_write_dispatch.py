"""Tests for ``.claude/hooks/pretooluse_subagent_write_dispatch.py``.

Session 272 measured that agent-frontmatter ``hooks:`` never run in this
harness while settings-level hooks do — and carry ``agent_id`` + ``agent_type``
in the payload (Lesson #0057, "Resolution, part 2"). The dispatcher is the
settings-level route to the three UNCHANGED guard scripts. Asserted here:

* identity routing — the main agent and non-guarded subagents pass through;
  each of the three guarded ``agent_type`` values reaches ITS guard, and the
  real guard script runs (its own deny reason comes back, not a copy);
* the guard's decision is forwarded verbatim (byte-equal to a direct run);
* fail-closed where identity is known (missing / crashing guard → deny);
* the documented pass-through on malformed stdin;
* the SCENARIO (CLAUDE.md §8): the real ``settings.json`` registration is read
  as data and the command it names is executed from the repo root with the
  payload shape the harness produced in s272 — real registration → real
  dispatcher → real guard, nothing stubbed on either side of the seam.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
HOOK = HOOKS_DIR / "pretooluse_subagent_write_dispatch.py"
SETTINGS = REPO_ROOT / ".claude" / "settings.json"
DISPATCHER_NAME = "pretooluse_subagent_write_dispatch.py"

GOAL_JSON = ".claude/state/goal.json"
FORBIDDEN_STATE_FILE = ".claude/state/s271-deny-probe.txt"

Payload = dict[str, Any]
Parsed = dict[str, Any] | None

# Payload fields recorded from the live harness in session 272 (the git-deny
# probe): ``agent_id`` equals the Agent tool's returned agentId and
# ``agent_type`` equals the ``subagent_type`` the parent spawned. The main
# agent's payload carries NEITHER field.
HARNESS_FIELDS: Payload = {
    "session_id": "aed2f679-2f96-45ab-92f4-15e5f0aea901",
    "transcript_path": "C:/Users/crayj/.claude/projects/x/aed2f679.jsonl",
    "cwd": "//wsl.localhost/ubuntu-24.04/home/crayj/work/vero-lite",
    "permission_mode": "auto",
    "hook_event_name": "PreToolUse",
}
RECORDED_AGENT_ID = "a9ea7bd029e309f43"


def _run(
    payload: Payload | str, hook: Path = HOOK, cwd: Path | None = None
) -> tuple[int, Parsed, str]:
    stdin = payload if isinstance(payload, str) else json.dumps(payload)
    result = subprocess.run(
        [sys.executable, str(hook)],
        input=stdin,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
        check=False,
        cwd=cwd,
    )
    out = result.stdout.strip()
    parsed = json.loads(out) if out else None
    return result.returncode, parsed, result.stdout


def _decision(parsed: Parsed) -> str | None:
    if not parsed:
        return None
    value = parsed.get("hookSpecificOutput", {}).get("permissionDecision")
    return str(value) if value is not None else None


def _reason(parsed: Parsed) -> str:
    assert parsed is not None
    return str(parsed["hookSpecificOutput"]["permissionDecisionReason"])


def _payload(
    tool: str, file_path: str, *, agent: str | None = None, agent_id: str | None = RECORDED_AGENT_ID
) -> Payload:
    tool_input: dict[str, Any] = {"file_path": file_path}
    if tool == "Write":
        tool_input["content"] = "x"
    elif tool == "Edit":
        tool_input.update({"old_string": "a", "new_string": "b"})
    payload: Payload = {**HARNESS_FIELDS, "tool_name": tool, "tool_input": tool_input}
    if agent is not None:
        payload["agent_type"] = agent
        if agent_id is not None:
            payload["agent_id"] = agent_id
    return payload


def _write(file_path: str, *, agent: str | None = None) -> Payload:
    return _payload("Write", file_path, agent=agent)


def _edit(file_path: str, *, agent: str | None = None) -> Payload:
    return _payload("Edit", file_path, agent=agent)


# --- pass-through: the main agent and everyone the dispatcher does not guard ---


def test_main_agent_passes_through_everywhere() -> None:
    """No ``agent_type`` = the main Code agent: every allowlist stays off it."""
    for path in (GOAL_JSON, "docs/STATUS.md", "services/api/main.py", "docs/plans/0001-x.md"):
        rc, parsed, stdout = _run(_write(path))
        assert rc == 0
        assert parsed is None, f"main agent was answered for {path}: {parsed}"
        assert stdout == ""


def test_unguarded_subagents_pass_through() -> None:
    for agent in ("general-purpose", "claude", "explore-research", "Explore"):
        rc, parsed, _ = _run(_write("services/api/main.py", agent=agent))
        assert rc == 0
        assert parsed is None, f"{agent} is not a guarded agent yet got {parsed}"


def test_non_watched_tool_passes_through() -> None:
    rc, parsed, _ = _run(_payload("Read", "services/api/main.py", agent="goal-evaluator"))
    assert rc == 0
    assert parsed is None


# --- routing: each guarded agent reaches ITS guard, and the real guard answers ---


def test_goal_evaluator_write_outside_goal_json_is_denied_with_the_sd1_reason() -> None:
    rc, parsed, _ = _run(_write(FORBIDDEN_STATE_FILE, agent="goal-evaluator"))
    assert rc == 0
    assert _decision(parsed) == "deny"
    reason = _reason(parsed)
    assert "SD-1 narrowed Write" in reason, reason
    assert FORBIDDEN_STATE_FILE in reason, reason


def test_goal_evaluator_write_to_goal_json_is_allowed() -> None:
    rc, parsed, stdout = _run(_write(GOAL_JSON, agent="goal-evaluator"))
    assert rc == 0
    assert parsed is None, parsed
    assert stdout == ""


def test_goal_evaluator_edit_is_routed_too() -> None:
    rc, parsed, _ = _run(_edit("docs/STATUS.md", agent="goal-evaluator"))
    assert rc == 0
    assert _decision(parsed) == "deny"
    assert "SD-1 narrowed Write" in _reason(parsed)


def test_status_scribe_write_to_status_is_allowed() -> None:
    rc, parsed, _ = _run(_write("docs/STATUS.md", agent="status-scribe"))
    assert rc == 0
    assert parsed is None, parsed


def test_status_scribe_write_elsewhere_is_denied_by_its_own_guard() -> None:
    rc, parsed, _ = _run(_write(GOAL_JSON, agent="status-scribe"))
    assert rc == 0
    assert _decision(parsed) == "deny"
    assert "status-scribe (H2-derived)" in _reason(parsed), _reason(parsed)


def test_plan_drafter_write_under_plans_is_allowed() -> None:
    rc, parsed, _ = _run(_write("docs/plans/0999-probe.md", agent="plan-drafter"))
    assert rc == 0
    assert parsed is None, parsed


def test_plan_drafter_write_to_code_is_denied_by_its_own_guard() -> None:
    rc, parsed, _ = _run(_write("services/api/main.py", agent="plan-drafter"))
    assert rc == 0
    assert _decision(parsed) == "deny"
    assert "PLAN-0009 Step 1b §5 (H2)" in _reason(parsed), _reason(parsed)


def test_agent_type_is_whitespace_stripped() -> None:
    rc, parsed, _ = _run(_write(FORBIDDEN_STATE_FILE, agent="  goal-evaluator "))
    assert rc == 0
    assert _decision(parsed) == "deny"


def test_guard_stdout_is_forwarded_verbatim() -> None:
    """The dispatcher adds nothing and rewrites nothing: byte-equal to a direct run."""
    payload = _write(FORBIDDEN_STATE_FILE, agent="goal-evaluator")
    _, _, via_dispatch = _run(payload)
    _, _, direct = _run(payload, hook=HOOKS_DIR / "pretooluse_goal_evaluator_write_deny.py")
    assert via_dispatch == direct
    assert via_dispatch.strip(), "the direct run produced no deny — the control is broken"


# --- fail-closed where identity is known ---


def _dispatcher_in_scratch(tmp_path: Path) -> Path:
    """A copy of the dispatcher whose sibling guard scripts do not exist."""
    scratch = tmp_path / "hooks"
    scratch.mkdir()
    return Path(shutil.copy(HOOK, scratch / DISPATCHER_NAME))


def test_missing_guard_script_denies_fail_closed(tmp_path: Path) -> None:
    hook = _dispatcher_in_scratch(tmp_path)
    rc, parsed, _ = _run(_write(GOAL_JSON, agent="goal-evaluator"), hook=hook)
    assert rc == 0
    assert _decision(parsed) == "deny"
    reason = _reason(parsed)
    assert "is missing" in reason, reason
    assert "Fail-closed" in reason, reason


def test_crashing_guard_denies_fail_closed(tmp_path: Path) -> None:
    hook = _dispatcher_in_scratch(tmp_path)
    fake_guard = hook.parent / "pretooluse_goal_evaluator_write_deny.py"
    fake_guard.write_text("import sys\nsys.exit(3)\n", encoding="utf-8")
    rc, parsed, _ = _run(_write(GOAL_JSON, agent="goal-evaluator"), hook=hook)
    assert rc == 0
    assert _decision(parsed) == "deny"
    assert "exited 3" in _reason(parsed), _reason(parsed)


def test_missing_guard_does_not_touch_the_main_agent(tmp_path: Path) -> None:
    """Fail-closed is scoped to a KNOWN guarded identity; the main agent is untouched."""
    hook = _dispatcher_in_scratch(tmp_path)
    rc, parsed, _ = _run(_write(GOAL_JSON), hook=hook)
    assert rc == 0
    assert parsed is None


# --- documented pass-through on input the harness would never produce ---


def test_malformed_stdin_passes_through_by_design() -> None:
    """The harness serialises this payload, not the agent — an agent cannot reach
    a bypass here, and a deny would block every actor's Write/Edit on a glitch."""
    rc, parsed, stdout = _run("{not json")
    assert rc == 0
    assert parsed is None
    assert stdout == ""


def test_non_object_payload_passes_through() -> None:
    rc, parsed, _ = _run("[1, 2, 3]")
    assert rc == 0
    assert parsed is None


# --- SCENARIO (CLAUDE.md §8): the real registration drives the real guard ---


def _registered_dispatch_argv() -> tuple[str, list[str]]:
    """The matcher + argv that ``settings.json`` actually registers for the dispatcher."""
    data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    entries = data["hooks"]["PreToolUse"]
    hits: list[tuple[str, str]] = []
    for entry in entries:
        for hook in entry.get("hooks") or []:
            command = hook.get("command", "")
            if DISPATCHER_NAME in command:
                hits.append((str(entry.get("matcher")), command))
    assert len(hits) == 1, f"expected exactly one dispatcher registration, got {hits}"
    matcher, command = hits[0]
    argv = shlex.split(command)
    assert argv[0] == "python", command
    # The harness resolves ``python`` on PATH; the pinned interpreter stands in
    # for it here. The script path is used exactly as registered (relative), so
    # the repo-root cwd the registration relies on is part of what is exercised.
    return matcher, [sys.executable, *argv[1:]]


def _run_registered(payload: Payload) -> tuple[int, Parsed]:
    _, argv = _registered_dispatch_argv()
    result = subprocess.run(
        argv,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=os.environ.copy(),
        check=False,
        cwd=REPO_ROOT,
    )
    out = result.stdout.strip()
    return result.returncode, (json.loads(out) if out else None)


def test_scenario_registration_covers_write_and_edit() -> None:
    matcher, _ = _registered_dispatch_argv()
    assert {"Write", "Edit"} <= set(matcher.split("|")), matcher


def test_scenario_registered_command_denies_goal_evaluator_outside_goal_json() -> None:
    """Real registration → real dispatcher → real guard, with the s272 harness payload."""
    rc, parsed = _run_registered(_write(FORBIDDEN_STATE_FILE, agent="goal-evaluator"))
    assert rc == 0
    assert _decision(parsed) == "deny"
    assert "SD-1 narrowed Write" in _reason(parsed), _reason(parsed)


def test_scenario_registered_command_allows_goal_evaluator_verdict_write() -> None:
    """The regression a settings-level guard could introduce: a FALSE deny on the
    evaluator's one legitimate write. Positive control for the deny above."""
    rc, parsed = _run_registered(_write(GOAL_JSON, agent="goal-evaluator"))
    assert rc == 0
    assert parsed is None, parsed


def test_scenario_registered_command_leaves_the_main_agent_alone() -> None:
    rc, parsed = _run_registered(_write(FORBIDDEN_STATE_FILE))
    assert rc == 0
    assert parsed is None, parsed


def test_scenario_registered_command_routes_every_guarded_agent() -> None:
    expectations = {
        "status-scribe": ("docs/STATUS.md", "services/api/main.py", "status-scribe (H2-derived)"),
        "plan-drafter": ("docs/adr/0999-probe.md", "docs/STATUS.md", "PLAN-0009 Step 1b §5 (H2)"),
        "goal-evaluator": (GOAL_JSON, "docs/plans/0999-probe.md", "SD-1 narrowed Write"),
    }
    for agent, (allowed, forbidden, token) in expectations.items():
        _, allowed_parsed = _run_registered(_write(allowed, agent=agent))
        assert allowed_parsed is None, f"{agent}: false deny on {allowed}: {allowed_parsed}"
        _, denied_parsed = _run_registered(_write(forbidden, agent=agent))
        assert _decision(denied_parsed) == "deny", f"{agent}: {forbidden} was not denied"
        assert token in _reason(denied_parsed), f"{agent}: wrong guard answered"
