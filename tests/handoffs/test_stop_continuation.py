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
# Stub that writes $1 (argv message) to $TELEGRAM_STUB_CAPTURE.
# Matches real telegram.sh contract — message via argv, never stdin
# (see Lesson #14 / session-15 Path C step 3 fix).
set -eu
printf '%s' "$1" > "$TELEGRAM_STUB_CAPTURE"
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
    # Defang Step 5 classifier so tests are deterministic — fail-closed
    # pause kicks in without ANTHROPIC_API_KEY (no real API call). Step 5b
    # added a ~/.claude/.anthropic_api_key fallback; point the override at
    # a nonexistent path so a developer's real key file cannot leak the
    # classifier into a live API call here.
    env.pop("ANTHROPIC_API_KEY", None)
    env["CLAUDE_ANTHROPIC_KEY_FILE"] = str(tmp_path / "nope.anthropic_api_key")
    # PLAN-0021 M2 hermeticity: point the goal gate at a per-test (absent)
    # goal file so a developer's live .claude/state/goal.json can never leak
    # into these cases. Absent file = no active goal = the gate falls through
    # — semantically identical to the pre-gate behavior for every prior case.
    env["CLAUDE_GOAL_PATH"] = str(tmp_path / "goal.json")
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
    body = cap.read_text(encoding="utf-8")
    # Human-readable body (per Lesson #14): argv message, not JSON-on-stdin.
    assert "stop_continuation_cap_reached" in body
    assert "depth=8" in body
    assert "cap=8" in body


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


# ---------------------------------------------------------------------------
# PLAN-0009 Step 5c-1: auto-handoff dispatch arm
#
# These tests are in-process (not subprocess) because the dispatch arm
# requires mocking the Sonnet classifier's return value — the existing
# subprocess pattern defangs the classifier by removing the API key, which
# is the right pattern for non-dispatch tests but cannot exercise the
# dispatch decision path. We import stop_continuation + _sonnet_classifier
# directly and monkey-patch classify() to return canned verdicts.
# ---------------------------------------------------------------------------


import importlib  # noqa: E402  — placed after subprocess-test section deliberately
import io  # noqa: E402

import _sonnet_classifier as _sc  # noqa: E402  — sys.path was set above
import stop_continuation as _stop  # noqa: E402


@pytest.fixture
def inproc_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, Path]:
    """In-process fixture: redirect state paths via env, neutralize Telegram,
    reset stop_continuation module-level state. Returns paths for assertion.
    """
    state_path = tmp_path / "loop-counter.json"
    chain_path = tmp_path / "stop-chain.json"
    # Point telegram at a nonexistent script so _ping_telegram is a no-op
    # (it short-circuits on missing script per _ping_telegram impl).
    telegram_script = tmp_path / "nonexistent-telegram.sh"
    monkeypatch.setenv("CLAUDE_LOOP_COUNTER_PATH", str(state_path))
    monkeypatch.setenv("CLAUDE_STOP_CHAIN_PATH", str(chain_path))
    monkeypatch.setenv("CLAUDE_TELEGRAM_SCRIPT", str(telegram_script))
    monkeypatch.delenv("CLAUDE_CODE_STOP_HOOK_BLOCK_CAP", raising=False)
    # Reload the hook to refresh any module-level cached paths/cap (defensive —
    # current impl reads via _state_path()/_chain_path()/_cap() helpers, which
    # query env at call time, but reload guarantees test isolation).
    importlib.reload(_stop)
    return {
        "state": state_path,
        "chain": chain_path,
        "telegram": telegram_script,
    }


def _patch_classify(monkeypatch: pytest.MonkeyPatch, verdict: dict[str, Any]) -> None:
    """Monkey-patch the classifier to return the canned verdict."""
    monkeypatch.setattr(_sc, "classify", lambda payload: verdict)


def _run_inproc(monkeypatch: pytest.MonkeyPatch, payload: dict[str, Any]) -> tuple[int, str]:
    """Invoke stop_continuation.main() in-process with stdin/stdout patched."""
    stdin = io.StringIO(json.dumps(payload))
    stdout = io.StringIO()
    monkeypatch.setattr("sys.stdin", stdin)
    monkeypatch.setattr("sys.stdout", stdout)
    rc = _stop.main()
    return rc, stdout.getvalue().strip()


def _dispatch_verdict(
    *,
    subagent: str = "plan-drafter",
    artifact_kind: str = "plan",
    task_summary: str = "Draft PLAN-0011 for cross-machine coordination spike",
    matched_rows: list[str] | None = None,
    reason: str = "governance drafting need; agreed plan needs structuring",
) -> dict[str, Any]:
    return {
        "decision": "dispatch",
        "matched_rows": matched_rows if matched_rows is not None else ["D2"],
        "reason": reason,
        "dispatch": {
            "subagent": subagent,
            "artifact_kind": artifact_kind,
            "task_summary": task_summary,
        },
    }


# --- Happy: dispatch emits block with instruction ---


def test_dispatch_plan_emits_block_with_instruction(
    monkeypatch: pytest.MonkeyPatch, inproc_env: dict[str, Path]
) -> None:
    _patch_classify(monkeypatch, _dispatch_verdict())
    rc, out = _run_inproc(monkeypatch, {"hook_event_name": "Stop"})
    assert rc == 0
    parsed = json.loads(out)
    assert parsed["decision"] == "block"
    assert parsed["hookSpecificOutput"]["hookEventName"] == "Stop"
    reason = parsed["reason"]
    # Instruction header references the auto-handoff system + spec
    assert "AUTO-HANDOFF DISPATCH" in reason
    assert "PLAN-0009 Step 5c" in reason
    # Cited classifier match + reason
    assert "D2" in reason
    assert "agreed plan needs structuring" in reason
    # Routing detail
    assert "plan-drafter" in reason
    assert "artifact_kind: plan" in reason
    assert "PLAN-0011" in reason  # task_summary surfaced
    # Pre-spawn discipline (Step 4 §4)
    assert "docs/plans" in reason  # artifact dir resolved correctly
    assert "target_number" in reason or "NNNN" in reason
    # Budget reminder (Step 4 §5)
    assert "OUTPUT BUDGET REMINDER" in reason
    assert "≤ 1k tokens" in reason
    assert "disclosure stamp" in reason
    # Commit boundary reminder
    assert "G5" in reason or "composed" in reason or "cannot commit" in reason
    assert "PR" in reason
    # Override clause
    assert "Override" in reason or "override" in reason
    assert "misroute" in reason or "spurious" in reason


def test_dispatch_adr_routes_to_docs_adr(
    monkeypatch: pytest.MonkeyPatch, inproc_env: dict[str, Path]
) -> None:
    _patch_classify(
        monkeypatch,
        _dispatch_verdict(
            artifact_kind="adr",
            matched_rows=["D1"],
            task_summary="Draft ADR-0015 for cross-tab transport decision",
        ),
    )
    rc, out = _run_inproc(monkeypatch, {"hook_event_name": "Stop"})
    assert rc == 0
    parsed = json.loads(out)
    reason = parsed["reason"]
    assert "artifact_kind: adr" in reason
    assert "docs/adr" in reason
    assert "D1" in reason
    assert "ADR-0015" in reason


# --- Chain-cap interaction: dispatch counts as proceed ---


def test_dispatch_increments_chain_depth(
    monkeypatch: pytest.MonkeyPatch, inproc_env: dict[str, Path]
) -> None:
    # Seed chain at depth 3
    inproc_env["chain"].write_text(
        json.dumps({"depth": 3, "last_proceed_ts": ""}), encoding="utf-8"
    )
    _patch_classify(monkeypatch, _dispatch_verdict())
    _run_inproc(monkeypatch, {"hook_event_name": "Stop"})
    chain = json.loads(inproc_env["chain"].read_text(encoding="utf-8"))
    assert chain["depth"] == 4
    assert chain["last_proceed_ts"]  # timestamp recorded


def test_dispatch_respects_chain_cap(
    monkeypatch: pytest.MonkeyPatch, inproc_env: dict[str, Path]
) -> None:
    """At cap-hit, classifier is never consulted — cap-fail-safe wins."""
    inproc_env["chain"].write_text(
        json.dumps({"depth": 8, "last_proceed_ts": ""}), encoding="utf-8"
    )
    classifier_called = {"n": 0}

    def spying_classify(payload: dict[str, Any]) -> dict[str, Any]:
        classifier_called["n"] += 1
        return _dispatch_verdict()

    monkeypatch.setattr(_sc, "classify", spying_classify)
    rc, out = _run_inproc(monkeypatch, {"hook_event_name": "Stop"})
    assert rc == 0
    assert out == ""  # cap-hit emits no block (lets stop fire)
    assert classifier_called["n"] == 0
    chain = json.loads(inproc_env["chain"].read_text(encoding="utf-8"))
    assert chain["depth"] == 0  # cap-hit resets


# --- Fail-closed: malformed dispatch metadata ---


def test_dispatch_with_missing_dispatch_field_demotes_to_pause(
    monkeypatch: pytest.MonkeyPatch, inproc_env: dict[str, Path]
) -> None:
    """Defensive: if a malformed dispatch verdict reaches the hook (classifier
    bug bypassing its own validation), the hook demotes to pause locally.
    """
    bad_verdict = {
        "decision": "dispatch",
        "matched_rows": ["D1"],
        "reason": "broken",
        # dispatch field missing entirely
    }
    _patch_classify(monkeypatch, bad_verdict)
    rc, out = _run_inproc(monkeypatch, {"hook_event_name": "Stop"})
    assert rc == 0
    assert out == ""  # demoted to pause behavior


def test_dispatch_with_non_dict_dispatch_field_demotes_to_pause(
    monkeypatch: pytest.MonkeyPatch, inproc_env: dict[str, Path]
) -> None:
    bad_verdict = {
        "decision": "dispatch",
        "matched_rows": ["D1"],
        "reason": "broken",
        "dispatch": "this should be an object",
    }
    _patch_classify(monkeypatch, bad_verdict)
    rc, out = _run_inproc(monkeypatch, {"hook_event_name": "Stop"})
    assert rc == 0
    assert out == ""


def test_dispatch_demoted_to_pause_resets_chain(
    monkeypatch: pytest.MonkeyPatch, inproc_env: dict[str, Path]
) -> None:
    """Demoted-dispatch behaves like pause: chain reset, no chain increment."""
    inproc_env["chain"].write_text(
        json.dumps({"depth": 4, "last_proceed_ts": ""}), encoding="utf-8"
    )
    bad_verdict = {
        "decision": "dispatch",
        "matched_rows": [],
        "reason": "broken",
    }
    _patch_classify(monkeypatch, bad_verdict)
    _run_inproc(monkeypatch, {"hook_event_name": "Stop"})
    chain = json.loads(inproc_env["chain"].read_text(encoding="utf-8"))
    assert chain["depth"] == 0


# --- Pre-existing behaviors unchanged by dispatch arm ---


def test_proceed_verdict_still_emits_block_with_reason(
    monkeypatch: pytest.MonkeyPatch, inproc_env: dict[str, Path]
) -> None:
    """Regression guard: the proceed arm still works after Step 5c-1 wiring."""
    proceed_verdict = {
        "decision": "proceed",
        "matched_rows": [],
        "reason": "tests pass, safe to continue",
    }
    _patch_classify(monkeypatch, proceed_verdict)
    rc, out = _run_inproc(monkeypatch, {"hook_event_name": "Stop"})
    assert rc == 0
    parsed = json.loads(out)
    assert parsed["decision"] == "block"
    assert parsed["reason"] == "tests pass, safe to continue"


def test_pause_verdict_still_emits_nothing(
    monkeypatch: pytest.MonkeyPatch, inproc_env: dict[str, Path]
) -> None:
    pause_verdict = {
        "decision": "pause",
        "matched_rows": ["G1"],
        "reason": "about to edit accepted ADR",
    }
    _patch_classify(monkeypatch, pause_verdict)
    rc, out = _run_inproc(monkeypatch, {"hook_event_name": "Stop"})
    assert rc == 0
    assert out == ""


def test_unknown_verdict_treated_as_pause(
    monkeypatch: pytest.MonkeyPatch, inproc_env: dict[str, Path]
) -> None:
    """Defense in depth: unknown decision values are treated as pause
    (fail-closed). The classifier should never emit these, but a future
    contract drift must not silently miss-fire as a proceed/dispatch.
    """
    weird_verdict = {
        "decision": "maybe-later",
        "matched_rows": [],
        "reason": "x",
    }
    _patch_classify(monkeypatch, weird_verdict)
    rc, out = _run_inproc(monkeypatch, {"hook_event_name": "Stop"})
    assert rc == 0
    assert out == ""


# --- Adversarial: dispatch with empty matched_rows still works ---


def test_dispatch_with_empty_matched_rows_still_dispatches(
    monkeypatch: pytest.MonkeyPatch, inproc_env: dict[str, Path]
) -> None:
    """Classifier emits dispatch without citing a D-row (unlikely but allowed
    by contract since reason is the citation fallback). Hook still emits the
    block with the matched_rows section showing (none cited).
    """
    _patch_classify(monkeypatch, _dispatch_verdict(matched_rows=[]))
    rc, out = _run_inproc(monkeypatch, {"hook_event_name": "Stop"})
    assert rc == 0
    parsed = json.loads(out)
    assert parsed["decision"] == "block"
    assert "(none cited)" in parsed["reason"]


# --- Re-entry guard still applies to dispatch arm ---


def test_dispatch_skipped_under_reentry_guard(
    monkeypatch: pytest.MonkeyPatch, inproc_env: dict[str, Path]
) -> None:
    """When stop_hook_active=True, even a dispatch verdict is not produced
    (classifier is never consulted; nothing is emitted).
    """
    classifier_called = {"n": 0}

    def spying_classify(payload: dict[str, Any]) -> dict[str, Any]:
        classifier_called["n"] += 1
        return _dispatch_verdict()

    monkeypatch.setattr(_sc, "classify", spying_classify)
    rc, out = _run_inproc(
        monkeypatch,
        {"hook_event_name": "Stop", "stop_hook_active": True},
    )
    assert rc == 0
    assert out == ""
    assert classifier_called["n"] == 0


# --- Instruction template structure sanity ---


def test_dispatch_instruction_includes_step4_references(
    monkeypatch: pytest.MonkeyPatch, inproc_env: dict[str, Path]
) -> None:
    """Instruction cites Step 4 sections so the main agent can cross-reference."""
    _patch_classify(monkeypatch, _dispatch_verdict())
    _, out = _run_inproc(monkeypatch, {"hook_event_name": "Stop"})
    reason = json.loads(out)["reason"]
    assert "Step 4 §1" in reason  # routing
    assert "Step 4 §4" in reason  # pre-spawn discipline
    assert "Step 4 §3" in reason  # post-spawn discipline


def test_dispatch_instruction_includes_scoped_context_discipline(
    monkeypatch: pytest.MonkeyPatch, inproc_env: dict[str, Path]
) -> None:
    """Instruction tells the agent not to inline file contents (Step 4 §2)."""
    _patch_classify(monkeypatch, _dispatch_verdict())
    _, out = _run_inproc(monkeypatch, {"hook_event_name": "Stop"})
    reason = json.loads(out)["reason"]
    assert "scoped_context" in reason
    assert "do NOT inline" in reason or "do not inline" in reason.lower()


# ---------------------------------------------------------------------------
# PLAN-0011 / Lesson #15 §5 — AC-4 mock-input assertion
#
# Most dispatch-arm tests above short-circuit at ``classify()`` to keep them
# deterministic. That pattern is correct for dispatch decision-mapping tests
# but cannot catch the Lesson #15 bug class (rendered user_message starved
# of transcript content). This test threads through the REAL classify() path
# with ``_call_api`` mocked to capture the rendered prompt, then asserts the
# prompt contains a verbatim fragment of the fixture transcript's user turn
# + assistant turn — the canary that proves _build_user_message is wiring
# transcript_path into the prompt, not just dropping it.
# ---------------------------------------------------------------------------


def test_classifier_user_message_includes_transcript_excerpt(
    monkeypatch: pytest.MonkeyPatch,
    inproc_env: dict[str, Path],
    tmp_path: Path,
) -> None:
    """AC-4 prevention — Stop event with a real transcript_path produces
    a user_message that surfaces the fixture's recent turns. If this
    test fails, the Lesson #15 starvation bug has regressed."""
    transcript = tmp_path / "ac4-stop-transcript.jsonl"
    transcript.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "type": "user",
                        "message": {
                            "role": "user",
                            "content": "AC4-STOP-FIXTURE-USER please draft ADR-0099",
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "AC4-STOP-FIXTURE-ASSISTANT acknowledged, drafting now",
                                }
                            ],
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    registry = tmp_path / "autonomy-triggers.md"
    registry.write_text(
        "# fixture registry\n\n| # | Trigger | Phase 2 |\n"
        "|---|---------|---------|\n| G1 | example | pause |\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CLAUDE_AUTONOMY_REGISTRY_PATH", str(registry))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake-key")
    monkeypatch.setenv("CLAUDE_CLASSIFIER_FORCE_DIRECT", "1")  # never bridge in tests

    captured: dict[str, str] = {}

    def fake_call_api(api_key: str, system_prompt: str, user_message: str) -> str:
        captured["user_message"] = user_message
        captured["system_prompt"] = system_prompt
        return json.dumps({"decision": "pause", "matched_rows": ["G1"], "reason": "fixture pause"})

    monkeypatch.setattr(_sc, "_call_api", fake_call_api)

    payload = {
        "hook_event_name": "Stop",
        "transcript_path": str(transcript),
        "session_id": "ac4-stop",
    }
    rc, _out = _run_inproc(monkeypatch, payload)
    assert rc == 0

    user_message = captured["user_message"]
    # Header proves the new section is emitted
    assert "## Recent conversation excerpt" in user_message
    # Verbatim fixture fragments prove _summarize_transcript ran with payload's path
    assert "AC4-STOP-FIXTURE-USER" in user_message
    assert "AC4-STOP-FIXTURE-ASSISTANT" in user_message
    # The "(no transcript available)" fallback must NOT have fired
    assert _sc.TRANSCRIPT_UNAVAILABLE not in user_message
    # Raw JSON payload still present (back-compat with PreToolUse callers)
    assert "## Raw payload" in user_message
    assert '"hook_event_name": "Stop"' in user_message


# ---------------------------------------------------------------------------
# PLAN-0021 M2 — goal-gate integration rows (ADR-0018 D4; additive only).
# The pre-existing cases above are UNCHANGED (AC-2): with no goal.json the
# gate falls through and the hook is byte-for-byte its pre-gate self.
# ---------------------------------------------------------------------------

GOAL_CHECK_OK = f'"{sys.executable}" -c "import sys; sys.exit(0)"'


def _seed_goal(env: dict[str, str], criteria: list[dict[str, Any]]) -> Path:
    goal_file = Path(env["CLAUDE_GOAL_PATH"])
    goal_file.parent.mkdir(parents=True, exist_ok=True)
    goal_file.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "goal": "m2 integration goal",
                "session": 51,
                "created": "2026-06-10T04:00:00+0000",
                "status": "active",
                "criteria": criteria,
                "evaluations": [],
            }
        ),
        encoding="utf-8",
    )
    return goal_file


def test_goalless_gate_is_byte_for_byte_todays_behavior(stub_env: dict[str, str]) -> None:
    """AC-2 (the load-bearing non-interference row): with the gate present but
    no goal file, the classifier-pause flow emits EXACTLY the pre-gate
    contract — empty stdout, exit 0, chain reset."""
    assert not Path(stub_env["CLAUDE_GOAL_PATH"]).exists()
    rc, out = _run({"hook_event_name": "Stop"}, stub_env)
    assert (rc, out) == (0, "")
    chain = json.loads(_chain(stub_env).read_text(encoding="utf-8"))
    assert chain["depth"] == 0


def test_gate_dispatch_emits_block_and_counts_toward_chain(stub_env: dict[str, str]) -> None:
    """Matrix dispatch row (e2e): active goal, green check + unresolved judge
    -> the hook prints the GOAL-GATE DISPATCH block and depth++ (the same
    chain-cap the classifier uses)."""
    _seed_goal(
        stub_env,
        [
            {"id": "C1", "kind": "check", "cmd": GOAL_CHECK_OK, "timeout_s": 30},
            {"id": "J1", "kind": "judge", "desc": "judged residue"},
        ],
    )
    rc, out = _run({"hook_event_name": "Stop"}, stub_env)
    assert rc == 0
    block = json.loads(out)
    assert block["decision"] == "block"
    assert "GOAL-GATE DISPATCH" in block["reason"]
    assert "goal-evaluator" in block["reason"]
    chain = json.loads(_chain(stub_env).read_text(encoding="utf-8"))
    assert chain["depth"] == 1


def test_cap_fires_before_gate_with_active_goal(stub_env: dict[str, str]) -> None:
    """boundary-2 row: at cap depth the chain-cap releases BEFORE the gate can
    dispatch — the cap stays the single loop bound (ADR-0018 D4)."""
    _seed_goal(
        stub_env,
        [
            {"id": "C1", "kind": "check", "cmd": GOAL_CHECK_OK, "timeout_s": 30},
            {"id": "J1", "kind": "judge", "desc": "judged residue"},
        ],
    )
    _seed_chain(stub_env, depth=8)
    rc, out = _run({"hook_event_name": "Stop"}, stub_env)
    assert (rc, out) == (0, "")  # cap released; no gate block
    chain = json.loads(_chain(stub_env).read_text(encoding="utf-8"))
    assert chain["depth"] == 0  # cap reset
    capture = _capture(stub_env)
    assert capture.exists()
    assert "cap" in capture.read_text(encoding="utf-8")


def test_fail_open_e2e_unanswered_dispatch_releases(stub_env: dict[str, str]) -> None:
    """fail-open row (e2e): Stop #1 dispatches; nothing answers (no evaluator
    in a subprocess test) and no work changes; Stop #2 releases the goal
    unevaluated and the stop FIRES (empty stdout) — never a wedge.

    NOTE: relies on the repo work-fingerprint being stable across the two
    runs (this test writes only under tmp_path, never inside the repo)."""
    goal_file = _seed_goal(
        stub_env,
        [
            {"id": "C1", "kind": "check", "cmd": GOAL_CHECK_OK, "timeout_s": 30},
            {"id": "J1", "kind": "judge", "desc": "judged residue"},
        ],
    )
    rc1, out1 = _run({"hook_event_name": "Stop"}, stub_env)
    assert rc1 == 0
    assert "GOAL-GATE DISPATCH" in json.loads(out1)["reason"]
    rc2, out2 = _run({"hook_event_name": "Stop"}, stub_env)
    assert (rc2, out2) == (0, "")  # the stop fires — fail-open, no wedge
    goal_doc = json.loads(goal_file.read_text(encoding="utf-8"))
    assert goal_doc["status"] == "released-unevaluated"
    capture = _capture(stub_env)
    assert capture.exists()
    assert "WITHOUT evaluation" in capture.read_text(encoding="utf-8")


def test_passed_goal_stands_down_classifier_flow_unchanged(stub_env: dict[str, str]) -> None:
    """happy-1 row (e2e, check-only): all checks green -> goal passes, then
    the classifier pause flow proceeds unchanged (empty stdout, exit 0)."""
    goal_file = _seed_goal(
        stub_env,
        [{"id": "C1", "kind": "check", "cmd": GOAL_CHECK_OK, "timeout_s": 30}],
    )
    rc, out = _run({"hook_event_name": "Stop"}, stub_env)
    assert (rc, out) == (0, "")
    goal_doc = json.loads(goal_file.read_text(encoding="utf-8"))
    assert goal_doc["status"] == "passed"
    capture = _capture(stub_env)
    assert capture.exists()
    assert "goal_gate_passed" in capture.read_text(encoding="utf-8")
