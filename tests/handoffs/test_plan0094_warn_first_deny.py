"""PLAN-0094 Step 3 (P2) — L1 warns on the first trip and denies on the second.

Closes **AC-4** (warn stage allows; deny moves out to ``T + G``), **AC-5** (the
warning is agent-visible and fires exactly once), and the third surface of
**AC-3** (the deny message stops advertising a reset path the main agent cannot
trigger).

Why the split exists at all: L1 counted *touches*, so six distinct edits
implementing one ratified plan step were indistinguishable from six retries of
one failing edit — and the guard hard-denied at the bar. ADR-013 row E.4's
stated consequence was "pause + Telegram alert" all along, so the first-trip
deny exceeded its own mandate. Warn-first moves L1 back toward the Accepted
ADR; the second-trip deny is hardening kept beyond it.

Run these in the **main tree** — five `tests/handoffs/` hook tests are known
false-RED inside a git worktree.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
GATE = HOOKS_DIR / "pretooluse_loop_detect.py"
OBSERVER = HOOKS_DIR / "posttooluse_progress_observer.py"

sys.path.insert(0, str(HOOKS_DIR))

from _loop_counter import (  # noqa: E402
    L1_GRACE_BUDGET,
    ActionRecord,
    LoopType,
    increment,
    l1_deny_threshold_for,
    l1_threshold_for,
    new_counter,
    note_attempted_edit,
    save_counter,
)

Payload = dict[str, Any]

CODE_TARGET = "services/api/main.py"
DOC_TARGET = "docs/STATUS.md"

# The ``old_string`` every ``_edit`` below carries, and its digest. Kept as one
# constant so ``_seed`` cannot drift out of sync with ``_edit`` — if they
# disagreed, the seeded state would stop making the crossing edit score and
# these tests would go green for the wrong reason.
_EDIT_OLD_STRING = "a"
_EDIT_OLD_STRING_SHA1 = hashlib.sha1(
    _EDIT_OLD_STRING.encode("utf-8"), usedforsecurity=False
).hexdigest()

STUB_TELEGRAM = """#!/usr/bin/env bash
# Appends $1 (argv message) to $TELEGRAM_STUB_CAPTURE, one record per line,
# so a test can count pings rather than only seeing the last one.
set -eu
printf '%s\\n---PING---\\n' "$1" >> "$TELEGRAM_STUB_CAPTURE"
"""


@pytest.fixture
def env(tmp_path: Path) -> dict[str, str]:
    state_path = tmp_path / "loop-counter.json"
    stub_script = tmp_path / "telegram_stub.sh"
    capture = tmp_path / "telegram_capture.txt"
    stub_script.write_text(STUB_TELEGRAM, encoding="utf-8")
    stub_script.chmod(0o755)
    e = os.environ.copy()
    e["CLAUDE_LOOP_COUNTER_PATH"] = str(state_path)
    e["CLAUDE_TELEGRAM_SCRIPT"] = str(stub_script)
    e["TELEGRAM_STUB_CAPTURE"] = str(capture)
    # Defang the real channel so even a stub leak cannot reach Telegram.
    e.pop("TELEGRAM_BOT_TOKEN", None)
    e.pop("TELEGRAM_CHAT_ID", None)
    return e


def _seed(env: dict[str, str], target: str, count: int) -> None:
    """Write a state file with ``count`` recorded L1 edits of ``target``.

    Also registers the digest of ``_edit``'s ``old_string`` in
    ``attempted_edits``, so the next ``_edit`` of this target reads as a
    re-applied edit and therefore SCORES. Since PLAN-0094 Step 4 (AC-7) L1
    counts non-progress rather than touches, so a seeded thrash scenario has to
    *look* like thrash in the state — a bare number no longer makes the
    following edit count, and without this the warn bar is never crossed.
    """
    counter = new_counter(session_id="test-session")
    for _ in range(count):
        increment(
            counter,
            LoopType.FILE_EDIT,
            target,
            ActionRecord(ts="2026-07-26T00:00:00+0000", tool="Edit", target=target),
        )
    note_attempted_edit(counter, LoopType.FILE_EDIT, target, _EDIT_OLD_STRING_SHA1)
    save_counter(counter, Path(env["CLAUDE_LOOP_COUNTER_PATH"]))


def _run(hook: Path, payload: Payload, env: dict[str, str]) -> tuple[str, str]:
    result = subprocess.run(
        [sys.executable, str(hook)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=15,
    )
    return result.stdout.strip(), result.stderr


def _edit(file_path: str) -> Payload:
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": file_path, "old_string": _EDIT_OLD_STRING, "new_string": "b"},
        "tool_response": {},
    }


def _is_deny(stdout: str) -> bool:
    if not stdout:
        return False
    parsed = json.loads(stdout)
    return parsed.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"


def _pings(env: dict[str, str]) -> list[str]:
    capture = Path(env["TELEGRAM_STUB_CAPTURE"])
    if not capture.exists():
        return []
    return [p for p in capture.read_text(encoding="utf-8").split("---PING---") if p.strip()]


# --------------------------------------------------------------------------- #
# AC-4 — the warn stage ALLOWS; the deny moves to T + G
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("target", [CODE_TARGET, DOC_TARGET])
def test_grace_zone_does_not_deny(target: str, env: dict[str, str]) -> None:
    """At the warn bar, and every count short of ``T + G``, the gate allows.

    This is the assertion that converts the s172 shape from a wall into a ping:
    seeded at exactly ``T`` (where the gate used to deny) the edit now proceeds.
    """
    warn_bar = l1_threshold_for(target)
    for count in range(warn_bar, l1_deny_threshold_for(target)):
        _seed(env, target, count)
        stdout, _ = _run(GATE, _edit(target), env)
        assert not _is_deny(stdout), f"{target}: denied at {count}, inside the grace zone"


@pytest.mark.parametrize("target", [CODE_TARGET, DOC_TARGET])
def test_deny_fires_at_the_grace_bar(target: str, env: dict[str, str]) -> None:
    """At ``T + G`` the wall returns, and the message names the real exits."""
    _seed(env, target, l1_deny_threshold_for(target))
    stdout, _ = _run(GATE, _edit(target), env)

    assert _is_deny(stdout), f"{target}: no deny at the grace bar"
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]
    assert "SubagentStop" in reason
    assert "git commit" in reason
    assert "turn boundary" in reason
    assert str(l1_deny_threshold_for(target)) in reason


def test_l4_deny_bar_is_untouched(env: dict[str, str]) -> None:
    """L4 keeps the flat base threshold — the grace budget widens L1 ONLY.

    Non-vacuity guard on the change's blast radius: an implementation that
    applied the grace budget in ``main()`` generally, rather than on the L1
    branch, would still pass every L1 test above and silently loosen L4.
    """
    counter = new_counter(session_id="test-session")
    command = "pytest tests/"
    for _ in range(6):
        increment(
            counter,
            LoopType.BASH_PATTERN,
            command,
            ActionRecord(ts="2026-07-26T00:00:00+0000", tool="Bash", target=command),
        )
    save_counter(counter, Path(env["CLAUDE_LOOP_COUNTER_PATH"]))

    stdout, _ = _run(
        GATE,
        {"tool_name": "Bash", "tool_input": {"command": command}},
        env,
    )
    assert _is_deny(stdout), "L4 stopped denying at its flat threshold of 6"


# --------------------------------------------------------------------------- #
# AC-5 — the warning is agent-visible and fires exactly once
# --------------------------------------------------------------------------- #


def test_crossing_the_warn_bar_emits_one_advisory_and_one_ping(env: dict[str, str]) -> None:
    """The edit that crosses ``T`` warns: agent-visible reason + one Telegram."""
    _seed(env, CODE_TARGET, l1_threshold_for(CODE_TARGET) - 1)
    stdout, _ = _run(OBSERVER, _edit(CODE_TARGET), env)

    assert stdout, "observer emitted nothing on the crossing edit"
    parsed = json.loads(stdout)
    assert parsed["decision"] == "block"
    assert CODE_TARGET in parsed["reason"]
    assert str(L1_GRACE_BUDGET) in parsed["reason"]

    pings = _pings(env)
    assert len(pings) == 1, f"expected exactly one Telegram warn, got {len(pings)}"
    assert "stage: warn" in pings[0]


def test_further_grace_zone_edits_are_silent(env: dict[str, str]) -> None:
    """Dedupe: only the CROSSING edit warns, never the rest of the grace zone.

    Without the ``warned_at`` stamp this would ping Cray on every edit between
    ``T`` and ``T + G`` — turning a warn into the nagging the deny replaced.
    """
    _seed(env, CODE_TARGET, l1_threshold_for(CODE_TARGET) - 1)
    first_stdout, _ = _run(OBSERVER, _edit(CODE_TARGET), env)
    assert first_stdout, "precondition: the crossing edit must warn"

    for _ in range(L1_GRACE_BUDGET):
        stdout, _ = _run(OBSERVER, _edit(CODE_TARGET), env)
        assert stdout == "", f"observer re-warned inside the grace zone: {stdout!r}"

    assert len(_pings(env)) == 1, "Telegram was pinged more than once for one entry"


def test_below_the_warn_bar_is_silent(env: dict[str, str]) -> None:
    """Non-vacuity: the observer is not simply printing on every edit."""
    _seed(env, CODE_TARGET, 1)
    stdout, _ = _run(OBSERVER, _edit(CODE_TARGET), env)

    assert stdout == "", f"observer warned below the bar: {stdout!r}"
    assert _pings(env) == []


def test_warned_at_is_persisted(env: dict[str, str]) -> None:
    """The dedupe stamp must survive the state write — it lives across processes.

    The warn fires in one hook invocation and must stay quiet in the NEXT one,
    a separate process, so an in-memory-only stamp would dedupe nothing.
    """
    _seed(env, CODE_TARGET, l1_threshold_for(CODE_TARGET) - 1)
    _run(OBSERVER, _edit(CODE_TARGET), env)

    state = json.loads(Path(env["CLAUDE_LOOP_COUNTER_PATH"]).read_text(encoding="utf-8"))
    entries = [v for k, v in state["counters"].items() if CODE_TARGET in k]
    assert entries, "no L1 entry written"
    assert entries[0]["warned_at"], "warned_at not persisted to the state file"


# --------------------------------------------------------------------------- #
# AC-3 (third surface) — the deny message stops advertising a dead path
# --------------------------------------------------------------------------- #


def test_deny_message_no_longer_claims_the_agent_tool_resets() -> None:
    """The AC-3 grep oracle, keyed on the anchor the old message contained.

    ``for a subagent's edits`` was chosen by PLAN-0094 precisely because it
    existed as ONE contiguous run on a single source line, whereas the adjacent
    prose "when the Agent tool returns" was split across an f-string boundary —
    an oracle keyed on the latter would have passed vacuously today and forever.
    """
    source = GATE.read_text(encoding="utf-8")
    assert "for a subagent's edits" not in source


def test_deny_message_does_not_advertise_the_unbuilt_stop_ack(env: dict[str, str]) -> None:
    """The P3 acknowledged-pause exit ships at Step 5 — it must not be named yet.

    Deliberate deviation from the Step 3 spec, which listed "the P3 stop-ack"
    among the exits to describe. Naming an exit that does not exist would
    recreate the exact defect AC-3 exists to close (three documents advertised
    the subagent reset as live while it was dead code for seven weeks). Step 5
    adds it to this message when the mechanism actually lands.
    """
    _seed(env, CODE_TARGET, l1_deny_threshold_for(CODE_TARGET))
    stdout, _ = _run(GATE, _edit(CODE_TARGET), env)
    reason = json.loads(stdout)["hookSpecificOutput"]["permissionDecisionReason"]

    assert "awaiting_ack" not in reason
    assert "stop-ack" not in reason
