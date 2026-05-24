"""Tests for ``.claude/hooks/stop_continuation.py`` (PLAN-0008 Step 4).

Covers:

- Re-entry guard: ``stop_hook_active=True`` short-circuits
- Turn-boundary L1 reset: counters NOT in ``turn_touched`` are reset;
  counters IN ``turn_touched`` survive; ``turn_touched`` is cleared
- Chain-cap fail-safe (OQ-E option b): cap-hit emits no block + pings
  Telegram with ``cap_reached`` payload + resets chain
- Classifier stub: defaults to ``pause`` → no block, chain reset
- Malformed input fail-open
- State paths honor env-var overrides (testability)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / ".claude" / "hooks" / "stop_continuation.py"
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from _loop_counter import (  # noqa: E402  — sys.path manipulation above
    ActionRecord,
    LoopType,
    counter_key,
    increment,
    load_counter,
    new_counter,
    record_turn_touched,
    save_counter,
)

STUB_TELEGRAM = """#!/usr/bin/env bash
cat > "$TELEGRAM_STUB_CAPTURE"
"""


@pytest.fixture
def stub_env(tmp_path: Path) -> dict[str, str]:
    state_path = tmp_path / "loop-counter.json"
    chain_path = tmp_path / "stop-chain.json"
    stub_script = tmp_path / "telegram_stub.sh"
    capture_file = tmp_path / "telegram_capture.json"
    stub_script.write_text(STUB_TELEGRAM, encoding="utf-8")
    stub_script.chmod(0o755)
    env = os.environ.copy()
    env["CLAUDE_LOOP_COUNTER_PATH"] = str(state_path)
    env["CLAUDE_STOP_CHAIN_PATH"] = str(chain_path)
    env["CLAUDE_TELEGRAM_SCRIPT"] = str(stub_script)
    env["TELEGRAM_STUB_CAPTURE"] = str(capture_file)
    env.pop("TELEGRAM_BOT_TOKEN", None)
    env.pop("TELEGRAM_CHAT_ID", None)
    env.pop("CLAUDE_CODE_STOP_HOOK_BLOCK_CAP", None)
    return env


def _run(payload: dict[str, Any], env: dict[str, str]) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=15,
    )
    return result.returncode, result.stdout.strip()


def _state(env: dict[str, str]) -> Path:
    return Path(env["CLAUDE_LOOP_COUNTER_PATH"])


def _chain(env: dict[str, str]) -> Path:
    return Path(env["CLAUDE_STOP_CHAIN_PATH"])


def _capture(env: dict[str, str]) -> Path:
    return Path(env["TELEGRAM_STUB_CAPTURE"])


def _seed_chain(env: dict[str, str], depth: int) -> None:
    p = _chain(env)
    p.write_text(json.dumps({"depth": depth, "last_proceed_ts": ""}), encoding="utf-8")


# --- Re-entry guard ---


def test_reentry_guard_short_circuits(stub_env: dict[str, str]) -> None:
    """When the harness reports stop_hook_active=True, the hook MUST NOT
    run reset / classifier / Telegram — just exit clean.
    """
    # Pre-seed an L1 counter NOT in turn_touched — would normally be reset.
    seed = new_counter("s")
    increment(seed, LoopType.FILE_EDIT, "x.py", ActionRecord("t", "Edit", "x.py"))
    save_counter(seed, _state(stub_env))
    _seed_chain(stub_env, depth=100)  # would normally hit cap

    rc, out = _run({"stop_hook_active": True, "hook_event_name": "Stop"}, stub_env)
    assert rc == 0
    assert out == ""

    # Counter unchanged, chain unchanged, no Telegram
    c = load_counter(_state(stub_env))
    assert counter_key(LoopType.FILE_EDIT, "x.py") in c.counters
    chain = json.loads(_chain(stub_env).read_text(encoding="utf-8"))
    assert chain["depth"] == 100
    assert not _capture(stub_env).exists()


# --- Turn-boundary L1 reset ---


def test_l1_counter_not_in_turn_touched_is_reset(stub_env: dict[str, str]) -> None:
    """An L1 counter for a file NOT touched this turn → reset on Stop."""
    seed = new_counter("s")
    increment(seed, LoopType.FILE_EDIT, "x.py", ActionRecord("t", "Edit", "x.py"))
    increment(seed, LoopType.FILE_EDIT, "x.py", ActionRecord("t", "Edit", "x.py"))
    # NOTE: turn_touched intentionally empty — x.py was edited but not
    # recorded as touched (simulates a fresh turn with no edits).
    save_counter(seed, _state(stub_env))

    _run({"hook_event_name": "Stop"}, stub_env)

    c = load_counter(_state(stub_env))
    assert counter_key(LoopType.FILE_EDIT, "x.py") not in c.counters


def test_l1_counter_in_turn_touched_survives(stub_env: dict[str, str]) -> None:
    """An L1 counter for a file touched this turn must NOT be reset."""
    seed = new_counter("s")
    increment(seed, LoopType.FILE_EDIT, "docs/STATUS.md", ActionRecord("t", "Edit", "x"))
    record_turn_touched(seed, "docs/STATUS.md")
    save_counter(seed, _state(stub_env))

    _run({"hook_event_name": "Stop"}, stub_env)

    c = load_counter(_state(stub_env))
    assert counter_key(LoopType.FILE_EDIT, "docs/STATUS.md") in c.counters


def test_turn_touched_cleared_after_stop(stub_env: dict[str, str]) -> None:
    """After Stop, turn_touched is empty so the next turn starts fresh."""
    seed = new_counter("s")
    record_turn_touched(seed, "x.py")
    record_turn_touched(seed, "y.py")
    save_counter(seed, _state(stub_env))

    _run({"hook_event_name": "Stop"}, stub_env)

    c = load_counter(_state(stub_env))
    assert c.turn_touched == []


def test_mixed_touched_and_untouched_l1_reset_correctly(stub_env: dict[str, str]) -> None:
    """Selective reset — touched survives, untouched is reset."""
    seed = new_counter("s")
    increment(seed, LoopType.FILE_EDIT, "a.py", ActionRecord("t", "Edit", "a"))
    increment(seed, LoopType.FILE_EDIT, "b.py", ActionRecord("t", "Edit", "b"))
    increment(seed, LoopType.FILE_EDIT, "c.py", ActionRecord("t", "Edit", "c"))
    record_turn_touched(seed, "a.py")
    record_turn_touched(seed, "c.py")
    save_counter(seed, _state(stub_env))

    _run({"hook_event_name": "Stop"}, stub_env)

    c = load_counter(_state(stub_env))
    keys = set(c.counters.keys())
    assert counter_key(LoopType.FILE_EDIT, "a.py") in keys
    assert counter_key(LoopType.FILE_EDIT, "b.py") not in keys
    assert counter_key(LoopType.FILE_EDIT, "c.py") in keys


def test_non_l1_counters_untouched_by_reset(stub_env: dict[str, str]) -> None:
    """L2/L3/L4 counters must NOT be reset by Stop hook (Step 4 scope = L1 only)."""
    seed = new_counter("s")
    increment(seed, LoopType.TEST_FAIL, "tests/foo.py::test_bar", ActionRecord("t", "Bash", "x"))
    increment(seed, LoopType.BASH_PATTERN, "pytest <arg>", ActionRecord("t", "Bash", "x"))
    increment(seed, LoopType.ERROR_SIGNATURE, "RuntimeError: foo", ActionRecord("t", "Bash", "x"))
    save_counter(seed, _state(stub_env))

    _run({"hook_event_name": "Stop"}, stub_env)

    c = load_counter(_state(stub_env))
    assert counter_key(LoopType.TEST_FAIL, "tests/foo.py::test_bar") in c.counters
    assert counter_key(LoopType.BASH_PATTERN, "pytest <arg>") in c.counters
    assert counter_key(LoopType.ERROR_SIGNATURE, "RuntimeError: foo") in c.counters


def test_reset_runs_even_with_empty_state(stub_env: dict[str, str]) -> None:
    """No state file = no-op reset; hook still completes cleanly."""
    rc, _ = _run({"hook_event_name": "Stop"}, stub_env)
    assert rc == 0


# --- Chain-cap fail-safe (OQ-E option b) ---


def test_cap_hit_pings_telegram_and_does_not_block(stub_env: dict[str, str]) -> None:
    """At cap: no block emitted, Telegram pinged with cap_reached payload."""
    _seed_chain(stub_env, depth=8)  # default cap = 8
    rc, out = _run({"hook_event_name": "Stop"}, stub_env)
    assert rc == 0
    assert out == ""  # no block

    cap = _capture(stub_env)
    assert cap.exists(), "Telegram cap-reached payload not written"
    payload = json.loads(cap.read_text(encoding="utf-8"))
    assert payload["event"] == "stop_continuation_cap_reached"
    assert payload["depth"] == 8
    assert payload["cap"] == 8


def test_cap_hit_resets_chain(stub_env: dict[str, str]) -> None:
    _seed_chain(stub_env, depth=8)
    _run({"hook_event_name": "Stop"}, stub_env)
    chain = json.loads(_chain(stub_env).read_text(encoding="utf-8"))
    assert chain["depth"] == 0


def test_cap_respects_env_override(stub_env: dict[str, str]) -> None:
    """Custom CLAUDE_CODE_STOP_HOOK_BLOCK_CAP value is honored."""
    stub_env["CLAUDE_CODE_STOP_HOOK_BLOCK_CAP"] = "3"
    _seed_chain(stub_env, depth=3)
    rc, out = _run({"hook_event_name": "Stop"}, stub_env)
    assert rc == 0
    assert out == ""
    assert _capture(stub_env).exists()


def test_cap_env_invalid_falls_back_to_default(stub_env: dict[str, str]) -> None:
    """Garbage env value falls back to DEFAULT_CAP=8."""
    stub_env["CLAUDE_CODE_STOP_HOOK_BLOCK_CAP"] = "not-an-int"
    _seed_chain(stub_env, depth=7)
    _run({"hook_event_name": "Stop"}, stub_env)
    # 7 < default 8 → no cap-hit, no Telegram
    assert not _capture(stub_env).exists()


# --- Classifier stub (defaults to pause) ---


def test_classifier_stub_pauses_no_block(stub_env: dict[str, str]) -> None:
    """Under cap, classifier stub returns pause → no block emitted."""
    _seed_chain(stub_env, depth=2)
    rc, out = _run({"hook_event_name": "Stop"}, stub_env)
    assert rc == 0
    assert out == ""


def test_pause_resets_chain(stub_env: dict[str, str]) -> None:
    """On pause: chain resets so next session starts fresh."""
    _seed_chain(stub_env, depth=2)
    _run({"hook_event_name": "Stop"}, stub_env)
    chain = json.loads(_chain(stub_env).read_text(encoding="utf-8"))
    assert chain["depth"] == 0


# --- Malformed input ---


def test_malformed_json_fails_open(stub_env: dict[str, str]) -> None:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json",
        capture_output=True,
        text=True,
        env=stub_env,
        check=False,
        timeout=15,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_missing_hook_event_name_no_crash(stub_env: dict[str, str]) -> None:
    """Hook should run even without explicit hook_event_name field."""
    rc, _ = _run({}, stub_env)
    assert rc == 0


# --- Chain state persistence ---


def test_chain_state_atomic_no_leftover_tmp(stub_env: dict[str, str], tmp_path: Path) -> None:
    _seed_chain(stub_env, depth=8)
    _run({"hook_event_name": "Stop"}, stub_env)
    leftovers = list(tmp_path.glob("*.tmp"))
    assert leftovers == []


def test_chain_state_recovers_from_malformed(stub_env: dict[str, str]) -> None:
    """A garbage chain file is treated as fresh, not raised."""
    _chain(stub_env).write_text("{garbage", encoding="utf-8")
    rc, _ = _run({"hook_event_name": "Stop"}, stub_env)
    assert rc == 0
    chain = json.loads(_chain(stub_env).read_text(encoding="utf-8"))
    assert chain["depth"] == 0


def test_chain_state_recovers_from_empty(stub_env: dict[str, str]) -> None:
    _chain(stub_env).write_text("", encoding="utf-8")
    rc, _ = _run({"hook_event_name": "Stop"}, stub_env)
    assert rc == 0
