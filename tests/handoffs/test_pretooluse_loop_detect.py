"""Tests for ``.claude/hooks/pretooluse_loop_detect.py`` (PLAN-0008 Step 2).

Covers:

**PLAN-0102 retired L1**, so Bash -> L4 is the only mapping left and this
module lost its whole path-class dimension. The Write/Edit tests that remain
assert the OPPOSITE of what they used to: that no amount of recorded L1 state
can produce a deny.

- Tool/target mapping: Bash -> L4; Write/Edit/Read/Glob/etc -> no-op
- Allow path: count below threshold, no counter for target, fresh state
  file, missing state file
- Deny path: L4 at the flat threshold of 6 (its unit is failure-based, so it
  never had the false-fire series that bought L1 a warn stage and a grace
  budget)
- Telegram stub captures the Cray-E.4 payload `{loop_type, target,
  last_6_actions}` when deny fires
- Malformed input (bad JSON, missing tool_name, missing tool_input,
  non-dict tool_input)
- Path normalization parity with the C4 hook (Windows-UNC / backslash)
- Bash tokenization (same command pattern with different args collapses)
- Env-var overrides for state path + telegram script (testability)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeGuard

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / ".claude" / "hooks" / "pretooluse_loop_detect.py"
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from _loop_counter import (  # noqa: E402  — sys.path manipulation above
    LOOP_TRIGGER_THRESHOLD,
    MAX_RECENT_ACTIONS,
    ActionRecord,
    LoopType,
    increment,
    new_counter,
    save_counter,
)

Payload = dict[str, Any]
Parsed = dict[str, Any] | None

# PLAN-0102 retired L1, so the path-class split (CODE_TARGET / DOC_TARGET and
# their grace-adjusted deny bars) went with it — there is no per-path threshold
# left to express. L4 is the one gated surface and its bar is flat.
L4_COMMAND = "pytest tests/foo.py"
L4_TARGET = "pytest <arg>"  # the tokenized form L4 keys on

# Above every bar L1 ever used (6/15 warn, 9/18 deny). Seeded on an ``L1:`` key,
# it is what makes "Write/Edit is not gated" a claim about the MAPPING rather
# than about a small number.
_ABOVE_EVERY_HISTORICAL_L1_BAR = 20

# Hand-written state fixtures must carry a FRESH stamp. ``prune_stale_entries``
# drops anything older than COUNTER_MAX_AGE_HOURS (6.0) on load, so a hardcoded
# past date would make every "not gated" assertion below pass because the entry
# had been pruned — the classic vacuous green, and one the assertion could not
# distinguish from the retirement actually working.
_RECENT_STAMP = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S%z")

STUB_TELEGRAM = """#!/usr/bin/env bash
# Stub that writes $1 (argv message) to $TELEGRAM_STUB_CAPTURE.
# Matches real telegram.sh contract — message via argv, never stdin
# (see Lesson #14 / session-15 Path C step 3 fix).
set -eu
printf '%s' "$1" > "$TELEGRAM_STUB_CAPTURE"
"""


@pytest.fixture
def stub_env(tmp_path: Path) -> dict[str, str]:
    """Seed env: state path + telegram stub + capture file path."""
    state_path = tmp_path / "loop-counter.json"
    stub_script = tmp_path / "telegram_stub.sh"
    capture_file = tmp_path / "telegram_capture.json"
    stub_script.write_text(STUB_TELEGRAM, encoding="utf-8")
    stub_script.chmod(0o755)
    env = os.environ.copy()
    env["CLAUDE_LOOP_COUNTER_PATH"] = str(state_path)
    env["CLAUDE_TELEGRAM_SCRIPT"] = str(stub_script)
    env["TELEGRAM_STUB_CAPTURE"] = str(capture_file)
    # Defang the real Telegram env so even if the stub leaks, no live call
    env.pop("TELEGRAM_BOT_TOKEN", None)
    env.pop("TELEGRAM_CHAT_ID", None)
    return env


def _run(payload: Payload, env: dict[str, str]) -> tuple[int, Parsed]:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=15,
    )
    out = result.stdout.strip()
    parsed = json.loads(out) if out else None
    return result.returncode, parsed


def _is_deny(parsed: Parsed) -> TypeGuard[dict[str, Any]]:
    if not parsed:
        return False
    decision = parsed.get("hookSpecificOutput", {}).get("permissionDecision")
    return bool(decision == "deny")


def _write(file_path: str) -> Payload:
    return {"tool_name": "Write", "tool_input": {"file_path": file_path, "content": "x"}}


def _edit(file_path: str) -> Payload:
    return {
        "tool_name": "Edit",
        "tool_input": {"file_path": file_path, "old_string": "a", "new_string": "b"},
    }


def _bash(command: str) -> Payload:
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def _seed_counter(state_path: Path, loop_type: LoopType, target: str, count: int) -> None:
    c = new_counter("test-session")
    for i in range(count):
        increment(c, loop_type, target, ActionRecord(ts=f"t{i}", tool="Edit", target=target))
    save_counter(c, state_path)


def _state_path_from(env: dict[str, str]) -> Path:
    return Path(env["CLAUDE_LOOP_COUNTER_PATH"])


# --- Allow path ---


def test_allow_when_no_state_file(stub_env: dict[str, str]) -> None:
    rc, out = _run(_bash(L4_COMMAND), stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_allow_when_no_counter_for_target(stub_env: dict[str, str]) -> None:
    _seed_counter(_state_path_from(stub_env), LoopType.BASH_PATTERN, "git <arg>", 10)
    rc, out = _run(_bash(L4_COMMAND), stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_allow_when_count_below_threshold(stub_env: dict[str, str]) -> None:
    _seed_counter(
        _state_path_from(stub_env), LoopType.BASH_PATTERN, L4_TARGET, LOOP_TRIGGER_THRESHOLD - 1
    )
    rc, out = _run(_bash(L4_COMMAND), stub_env)
    assert rc == 0
    assert not _is_deny(out)


# --- PLAN-0102: Write/Edit no longer map to any loop type -------------------


def _seed_l1_directly(env: dict[str, str], target: str) -> None:
    """Write an ``L1:`` counter entry straight to disk, past the module API.

    Deliberately not built through ``_seed_counter``: ``LoopType.FILE_EDIT`` no
    longer exists, so the only way to stage the state a retired guard would have
    read is to write the persisted shape by hand. That is also the more honest
    fixture — it stages what a REAL pre-retirement state file looks like rather
    than what today's API can express.
    """
    path = _state_path_from(env)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "session_id": "seeded",
                "started_at": _RECENT_STAMP,
                "counters": {
                    f"L1:{target}": {
                        "count": _ABOVE_EVERY_HISTORICAL_L1_BAR,
                        "last_6_actions": [],
                        # Recent, or age-out would drop the entry and the test
                        # would pass for the wrong reason.
                        "last_updated": _RECENT_STAMP,
                        "warned_at": "",
                    }
                },
            }
        ),
        encoding="utf-8",
    )


def test_write_is_never_gated_however_much_l1_state_exists(
    stub_env: dict[str, str],
) -> None:
    """A Write against a target carrying 20 recorded hits is ALLOWED.

    20 is above every bar L1 ever used — 6/15 warn, 9/18 deny — so this is a
    claim about the MAPPING being gone, not about the number being small.

    RED when: a ``Write``/``Edit`` -> loop-type branch is reintroduced in
    ``_resolve_target``. Read it beside ``test_deny_l4_at_threshold``, which is
    the live positive control: without that pair, this test passes identically
    over a hook that has stopped denying anything at all.
    """
    _seed_l1_directly(stub_env, "services/api/main.py")
    rc, out = _run(_write("services/api/main.py"), stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_edit_is_never_gated_however_much_l1_state_exists(
    stub_env: dict[str, str],
) -> None:
    """Same for ``Edit`` — the retired branch mapped both tools to one counter.

    ``docs/STATUS.md`` on purpose: under the retired path-class split this was
    the DOC class, and it is the real file whose authoring the guard walled.
    """
    _seed_l1_directly(stub_env, "docs/STATUS.md")
    rc, out = _run(_edit("docs/STATUS.md"), stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_a_legacy_l1_state_file_does_not_crash_the_gate(stub_env: dict[str, str]) -> None:
    """AC-5: pre-retirement state must load, not raise.

    Gitignored state files predating the excision exist in every worktree and
    on both machines. An ``L1:``-prefixed key, ``turn_touched``,
    ``subagent_touched`` and ``awaiting_ack`` must all read back harmlessly —
    RED when any load path reconstructs ``LoopType("L1")``, which raises
    ``ValueError`` before the hook does anything.
    """
    path = _state_path_from(stub_env)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "session_id": "legacy",
                "started_at": _RECENT_STAMP,
                "counters": {
                    "L1:services/api/main.py": {
                        "count": 30,
                        "last_6_actions": [],
                        "last_updated": _RECENT_STAMP,
                        "warned_at": _RECENT_STAMP,
                        "attempted_edits": {"deadbeef": 4},
                        "content_hashes": {"cafebabe": 2},
                    }
                },
                "turn_touched": ["services/api/main.py"],
                "subagent_touched": {"agent-A": ["services/api/main.py"]},
                "awaiting_ack": ["services/api/main.py"],
            }
        ),
        encoding="utf-8",
    )
    rc, out = _run(_write("services/api/main.py"), stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_allow_for_non_matching_tool_read(stub_env: dict[str, str]) -> None:
    rc, out = _run({"tool_name": "Read", "tool_input": {"file_path": "x.py"}}, stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_allow_for_non_matching_tool_glob(stub_env: dict[str, str]) -> None:
    rc, out = _run({"tool_name": "Glob", "tool_input": {"pattern": "**/*.py"}}, stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_allow_when_command_missing(stub_env: dict[str, str]) -> None:
    rc, out = _run({"tool_name": "Bash", "tool_input": {}}, stub_env)
    assert rc == 0
    assert not _is_deny(out)


# --- Deny path: L4 (Bash) ---


def test_deny_l4_at_threshold(stub_env: dict[str, str]) -> None:
    target = "pytest <arg>"  # tokenized form
    _seed_counter(_state_path_from(stub_env), LoopType.BASH_PATTERN, target, 6)
    rc, out = _run(_bash("pytest tests/foo.py"), stub_env)
    assert rc == 0
    assert _is_deny(out)
    assert "L4" in out["hookSpecificOutput"]["permissionDecisionReason"]


def test_deny_l4_collapses_variant_args(stub_env: dict[str, str]) -> None:
    """Different paths collapse to the same `pytest <arg>` token."""
    target = "pytest <arg>"
    _seed_counter(_state_path_from(stub_env), LoopType.BASH_PATTERN, target, 6)
    rc1, out1 = _run(_bash("pytest tests/foo.py"), stub_env)
    rc2, out2 = _run(_bash("pytest tests/bar.py"), stub_env)
    assert _is_deny(out1) and _is_deny(out2)


def test_allow_l4_distinct_command_pattern(stub_env: dict[str, str]) -> None:
    """Counter for pytest must NOT trip a different command (e.g., git)."""
    _seed_counter(_state_path_from(stub_env), LoopType.BASH_PATTERN, "pytest <arg>", 10)
    rc, out = _run(_bash("git status"), stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_l4_uses_base_threshold_for_doc_like_command(stub_env: dict[str, str]) -> None:
    """L4 (Bash) is path-class-agnostic: a command that happens to mention a .md
    path still uses the base threshold 6 (path-class applies to L1 file edits only).
    """
    target = "cat <arg>"
    _seed_counter(_state_path_from(stub_env), LoopType.BASH_PATTERN, target, 6)
    rc, out = _run(_bash("cat docs/STATUS.md"), stub_env)
    assert rc == 0
    assert _is_deny(out)


# --- Telegram payload contract (Cray E.4) ---


def test_deny_fires_telegram_with_payload(stub_env: dict[str, str], tmp_path: Path) -> None:
    state_path = _state_path_from(stub_env)
    c = new_counter("test-session")
    for i in range(LOOP_TRIGGER_THRESHOLD):
        increment(
            c,
            LoopType.BASH_PATTERN,
            L4_TARGET,
            ActionRecord(ts=f"t{i}", tool="Bash", target=L4_TARGET, result=f"attempt-{i}"),
        )
    save_counter(c, state_path)

    rc, out = _run(_bash(L4_COMMAND), stub_env)
    assert rc == 0
    assert _is_deny(out)

    capture = Path(stub_env["TELEGRAM_STUB_CAPTURE"])
    assert capture.exists(), "stub telegram script was not invoked"
    body = capture.read_text(encoding="utf-8")
    # Human-readable body (per Lesson #14): argv message, not JSON-on-stdin.
    assert "L4" in body
    assert L4_TARGET in body
    assert f"attempt-{LOOP_TRIGGER_THRESHOLD - 1}" in body  # newest action present
    # The ring window is the LAST MAX_RECENT_ACTIONS, not the first six.
    for i in range(LOOP_TRIGGER_THRESHOLD - MAX_RECENT_ACTIONS, LOOP_TRIGGER_THRESHOLD):
        assert f"t{i}" in body


def test_deny_still_fires_when_telegram_script_missing(stub_env: dict[str, str]) -> None:
    """Telegram outage must NOT block the gate — deny still emitted."""
    stub_env["CLAUDE_TELEGRAM_SCRIPT"] = "/nonexistent/path/telegram.sh"
    _seed_counter(
        _state_path_from(stub_env), LoopType.BASH_PATTERN, L4_TARGET, LOOP_TRIGGER_THRESHOLD
    )
    rc, out = _run(_bash(L4_COMMAND), stub_env)
    assert rc == 0
    assert _is_deny(out)


# --- Malformed input (fail-open per hook protocol) ---


def test_malformed_json_fails_open(stub_env: dict[str, str]) -> None:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json at all",
        capture_output=True,
        text=True,
        env=stub_env,
        check=False,
        timeout=15,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_missing_tool_name(stub_env: dict[str, str]) -> None:
    rc, out = _run({"tool_input": {"file_path": "x.py"}}, stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_non_dict_tool_input(stub_env: dict[str, str]) -> None:
    rc, out = _run({"tool_name": "Write", "tool_input": "not-a-dict"}, stub_env)
    assert rc == 0
    assert not _is_deny(out)


# --- L2/L3 NOT enforced at PreToolUse (Step 3 responsibility) ---


def test_l2_counter_does_not_gate_bash(stub_env: dict[str, str]) -> None:
    """L2 (test_fail) is keyed by pytest nodeid — PreToolUse cannot predict
    which test the bash command will fail. Step 3 fires L2 Telegram pings
    directly; Step 2 must not also deny on L2-state existing.
    """
    _seed_counter(
        _state_path_from(stub_env),
        LoopType.TEST_FAIL,
        "tests/handoffs/test_foo.py::test_bar",
        10,
    )
    rc, out = _run(_bash("pytest tests/handoffs/test_foo.py"), stub_env)
    assert rc == 0
    assert not _is_deny(out)


def test_l3_counter_does_not_gate_bash(stub_env: dict[str, str]) -> None:
    _seed_counter(
        _state_path_from(stub_env),
        LoopType.ERROR_SIGNATURE,
        "RuntimeError: foo missing",
        10,
    )
    rc, out = _run(_bash("python script.py"), stub_env)
    assert rc == 0
    assert not _is_deny(out)


# --- Reason message contract ---


def test_deny_reason_includes_target_and_count_and_registry_pointer(
    stub_env: dict[str, str],
) -> None:
    _seed_counter(_state_path_from(stub_env), LoopType.BASH_PATTERN, L4_TARGET, 10)
    _, out = _run(_bash(L4_COMMAND), stub_env)
    assert _is_deny(out)
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert L4_TARGET in reason
    assert "10" in reason
    assert ".claude/autonomy-triggers.md" in reason
    assert "Cray E.4" in reason or "threshold" in reason


def test_deny_reason_names_only_reset_paths_that_exist(stub_env: dict[str, str]) -> None:
    """The message must not advertise a reset the agent cannot reach.

    PLAN-0094 P2 set this rule after a message described the reset in terms of
    the ``Agent`` tool returning — dead code for seven weeks while three
    documents called it live. PLAN-0102 pointed the same rule the other way:
    the message used to list three reset paths (an untouched turn boundary, a
    ``git commit`` containing the target, a subagent's own ``SubagentStop``),
    and ALL THREE were L1 paths deleted with L1. Only L4 reaches this message
    now, and L4's real reset is a successful run of the same command pattern.

    RED when: the pre-retirement wording is restored, or a fourth path is
    invented — either way the agent is told to do something that cannot clear
    its counter.
    """
    _seed_counter(_state_path_from(stub_env), LoopType.BASH_PATTERN, L4_TARGET, 10)
    _, out = _run(_bash(L4_COMMAND), stub_env)
    assert _is_deny(out)
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    for dead_path in ("turn boundary", "SubagentStop", "git commit"):
        assert dead_path not in reason, (
            f"the L4 deny message still names {dead_path!r} as a reset path. "
            "That was an L1 path and it no longer exists, so this tells the "
            "agent to do something that cannot clear the counter."
        )
    assert "SUCCEEDS" in reason, "the message must name L4's actual reset"


# --- ADR-013 D2 bypass-immunity regression guard (Step 6 Phase 1.5) ---


def test_bypass_permissions_still_denies_at_threshold(stub_env: dict[str, str]) -> None:
    """ADR-013 D2 binding: ``PreToolUse deny`` is deterministic and bypass-immune.

    Adding ``permission_mode: bypassPermissions`` to the payload must not
    short-circuit the L4 loop-detect deny once the counter is at threshold.
    Cheap insurance against a future hook implementation that accidentally
    short-circuits on bypass. Uncovered until session-14 Step 6 Phase 1.5
    closeout. (Was asserted on L1 until PLAN-0102; L4 is now the only gated
    surface, so it inherits the guarantee.)
    """
    _seed_counter(
        _state_path_from(stub_env), LoopType.BASH_PATTERN, L4_TARGET, LOOP_TRIGGER_THRESHOLD
    )
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": L4_COMMAND},
        "permission_mode": "bypassPermissions",
    }
    rc, out = _run(payload, stub_env)
    assert rc == 0
    assert _is_deny(out)
