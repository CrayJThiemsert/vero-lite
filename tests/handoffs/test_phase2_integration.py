"""End-to-end integration tests for PLAN-0008 Phase 2 (Step 7).

Validates the **wiring** between Phase 2 components — counter state,
PreToolUse gate, PostToolUse observer, Stop continuation, and the Sonnet
classifier — by driving real subprocess invocations of the hook scripts
with a local mock HTTP server standing in for the Anthropic Messages
API. Unit-level behavior is already covered exhaustively by the per-hook
test files; this file only asserts the cross-hook contracts.

Coverage map (cross-hook contracts only):

- **Stop continuation ↔ Sonnet classifier**: classifier ``proceed`` →
  Stop emits ``block`` decision returning agent to loop; ``pause`` →
  Stop exits clean (no block); fail-closed when env+file resolution
  fails.
- **PostToolUse observer → state file → PreToolUse loop-detect**:
  observer increments L1/L4; PreToolUse reads the same state and denies
  at threshold 6.
- **PostToolUse observer L2/L3 inline Telegram fire on threshold**:
  pytest-fail / traceback accumulation triggers ping at exactly the
  6th observation.
- **Stop turn-boundary reset ↔ observer turn_touched marker**: L1
  counters whose file_path is in ``turn_touched`` survive Stop; those
  not in it are zeroed.
- **Stop chain-cap ↔ stop-chain.json state**: at cap, Stop emits no
  block + Telegram ``cap reached`` + resets chain (OQ-E option b).
- **Stop ``stop_hook_active`` re-entry guard**: no state mutation, no
  classifier call (verified by mock server receiving zero requests).

The mock Sonnet server runs on 127.0.0.1 on an ephemeral port; tests
override ``$CLAUDE_SONNET_API_URL`` to point at it. Every test isolates
both the state file (via ``$CLAUDE_LOOP_COUNTER_PATH``) and the
classifier key-file fallback (via ``$CLAUDE_ANTHROPIC_KEY_FILE``) so
no developer's real ``~/.claude/.anthropic_api_key`` can leak the
classifier into a live API call.
"""

from __future__ import annotations

import http.server
import json
import os
import socketserver
import subprocess
import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, ClassVar

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from _loop_counter import (  # noqa: E402  — sys.path manipulation above
    ActionRecord,
    LoopType,
    get_count,
    increment,
    load_counter,
    new_counter,
    save_counter,
)

PRE_LOOP_HOOK = HOOKS_DIR / "pretooluse_loop_detect.py"
POST_OBSERVER_HOOK = HOOKS_DIR / "posttooluse_progress_observer.py"
STOP_HOOK = HOOKS_DIR / "stop_continuation.py"

STUB_TELEGRAM = """#!/usr/bin/env bash
cat > "$TELEGRAM_STUB_CAPTURE"
"""

Payload = dict[str, Any]


# --- Mock Sonnet HTTP server ---


class _MockSonnetHandler(http.server.BaseHTTPRequestHandler):
    """Returns the configured canned response; logs each request."""

    canned_response: ClassVar[dict[str, Any]] = {
        "decision": "pause",
        "matched_rows": [],
        "reason": "default mock",
    }
    request_log: ClassVar[list[dict[str, Any]]] = []

    def do_POST(self) -> None:  # noqa: N802 — http.server contract
        length = int(self.headers.get("Content-Length", "0"))
        body_bytes = self.rfile.read(length) if length else b""
        try:
            body = json.loads(body_bytes.decode("utf-8")) if body_bytes else None
        except json.JSONDecodeError:
            body = None
        self.__class__.request_log.append({"headers": dict(self.headers), "body": body})
        wire = {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(self.__class__.canned_response),
                }
            ]
        }
        encoded = json.dumps(wire).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: Any) -> None:
        # Silence default per-request stderr noise.
        return


@contextmanager
def _mock_sonnet_server(
    canned: dict[str, Any],
) -> Iterator[tuple[str, list[dict[str, Any]]]]:
    """Start an ephemeral HTTP server returning ``canned`` as a Sonnet
    Messages-API wire response. Yields ``(url, request_log)``.
    """
    log: list[dict[str, Any]] = []
    handler_cls = type(
        "BoundHandler",
        (_MockSonnetHandler,),
        {"canned_response": canned, "request_log": log},
    )
    # Bind to port 0 to get an OS-assigned ephemeral port.
    with socketserver.TCPServer(("127.0.0.1", 0), handler_cls) as server:
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield (f"http://127.0.0.1:{port}/v1/messages", log)
        finally:
            server.shutdown()


# --- Common subprocess + env fixtures ---


@pytest.fixture
def stub_env(tmp_path: Path) -> dict[str, str]:
    """Isolated env for one integration scenario.

    Provides: state file, chain file, telegram stub + capture, classifier
    fallback file pointed at a nonexistent path (so the fail-closed path
    is the default; tests that want classifier dispatch set
    ``ANTHROPIC_API_KEY`` and ``CLAUDE_SONNET_API_URL`` themselves).
    Registry is the real ``.claude/autonomy-triggers.md`` so the
    classifier system prompt is realistic.
    """
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
    env.pop("ANTHROPIC_API_KEY", None)
    env["CLAUDE_ANTHROPIC_KEY_FILE"] = str(tmp_path / "nope.anthropic_api_key")
    return env


def _run(hook: Path, payload: Payload, env: dict[str, str]) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, str(hook)],
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


def _write_payload(file_path: str, *, post: bool = False) -> Payload:
    base = {
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": "x"},
    }
    if post:
        base["tool_response"] = {}
    return base


def _bash_payload(command: str, *, exit_code: int = 0, post: bool = False) -> Payload:
    base: Payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }
    if post:
        base["tool_response"] = {"exit_code": exit_code, "stdout": "", "stderr": ""}
    return base


# --- A. Stop ↔ classifier wiring ---


def test_stop_proceed_emits_block_decision(stub_env: dict[str, str]) -> None:
    """E2E: mock Sonnet returns `proceed` → Stop hook emits `block`
    decision returning the agent to the loop, with the classifier's
    reason propagated.
    """
    stub_env["ANTHROPIC_API_KEY"] = "sk-int-fake-key"  # pragma: allowlist secret
    canned = {
        "decision": "proceed",
        "matched_rows": [],
        "reason": "tests pass, safe to continue",
    }
    with _mock_sonnet_server(canned) as (url, log):
        stub_env["CLAUDE_SONNET_API_URL"] = url
        rc, out = _run(STOP_HOOK, {"hook_event_name": "Stop"}, stub_env)
    assert rc == 0
    parsed = json.loads(out)
    assert parsed["decision"] == "block"
    assert "tests pass" in parsed["reason"]
    assert parsed["hookSpecificOutput"]["hookEventName"] == "Stop"
    assert len(log) == 1, "expected exactly one Sonnet call"


def test_stop_pause_emits_no_block(stub_env: dict[str, str]) -> None:
    """E2E: mock Sonnet returns `pause` with matched_rows → Stop emits
    no stdout (exit 0; the stop fires normally) and resets chain depth.
    """
    stub_env["ANTHROPIC_API_KEY"] = "sk-int-fake-key"  # pragma: allowlist secret
    # Pre-seed chain depth so we can verify it resets on pause.
    _chain(stub_env).write_text(
        json.dumps({"depth": 3, "last_proceed_ts": ""}),
        encoding="utf-8",
    )
    canned = {
        "decision": "pause",
        "matched_rows": ["G1"],
        "reason": "about to mutate accepted ADR",
    }
    with _mock_sonnet_server(canned) as (url, log):
        stub_env["CLAUDE_SONNET_API_URL"] = url
        rc, out = _run(STOP_HOOK, {"hook_event_name": "Stop"}, stub_env)
    assert rc == 0
    assert out == "", "pause must emit no decision (no block)"
    assert len(log) == 1
    chain = json.loads(_chain(stub_env).read_text(encoding="utf-8"))
    assert chain["depth"] == 0, "pause must reset chain"


def test_stop_classifier_fail_closed_when_key_missing(
    stub_env: dict[str, str],
) -> None:
    """E2E: no API key (env empty + file missing) → classifier returns
    fail-closed pause → Stop emits no block. No mock server needed
    (classifier never reaches the network).
    """
    # stub_env already pops ANTHROPIC_API_KEY and points the file at
    # a nonexistent path.
    _chain(stub_env).write_text(
        json.dumps({"depth": 2, "last_proceed_ts": ""}),
        encoding="utf-8",
    )
    rc, out = _run(STOP_HOOK, {"hook_event_name": "Stop"}, stub_env)
    assert rc == 0
    assert out == ""
    chain = json.loads(_chain(stub_env).read_text(encoding="utf-8"))
    assert chain["depth"] == 0


def test_stop_hook_active_short_circuits_no_classifier_call(
    stub_env: dict[str, str],
) -> None:
    """E2E: `stop_hook_active=True` → hook exits immediately. The mock
    server must receive zero requests (proves the re-entry guard fires
    before classifier dispatch).
    """
    stub_env["ANTHROPIC_API_KEY"] = "sk-int-fake-key"  # pragma: allowlist secret
    with _mock_sonnet_server(
        {"decision": "proceed", "matched_rows": [], "reason": "should not fire"}
    ) as (url, log):
        stub_env["CLAUDE_SONNET_API_URL"] = url
        rc, out = _run(
            STOP_HOOK,
            {"hook_event_name": "Stop", "stop_hook_active": True},
            stub_env,
        )
    assert rc == 0
    assert out == ""
    assert len(log) == 0, "re-entry guard must prevent classifier call"


# --- B. Chain-cap ---


def test_stop_chain_cap_fires_telegram_and_no_block(
    stub_env: dict[str, str],
) -> None:
    """E2E: pre-seed chain depth at cap; Stop fires → Telegram captures
    cap_reached payload + chain resets + no block decision.
    """
    stub_env["ANTHROPIC_API_KEY"] = "sk-int-fake-key"  # pragma: allowlist secret
    stub_env["CLAUDE_CODE_STOP_HOOK_BLOCK_CAP"] = "8"
    _chain(stub_env).write_text(
        json.dumps({"depth": 8, "last_proceed_ts": ""}),
        encoding="utf-8",
    )
    # Mock server present but should NOT be called (cap check is before
    # classifier dispatch).
    with _mock_sonnet_server({"decision": "proceed", "matched_rows": [], "reason": "x"}) as (
        url,
        log,
    ):
        stub_env["CLAUDE_SONNET_API_URL"] = url
        rc, out = _run(STOP_HOOK, {"hook_event_name": "Stop"}, stub_env)
    assert rc == 0
    assert out == ""
    assert len(log) == 0, "cap-hit must short-circuit before classifier"
    captured = json.loads(_capture(stub_env).read_text(encoding="utf-8"))
    assert captured["event"] == "stop_continuation_cap_reached"
    assert captured["depth"] == 8
    assert captured["cap"] == 8
    chain = json.loads(_chain(stub_env).read_text(encoding="utf-8"))
    assert chain["depth"] == 0


# --- C. Observer ↔ state file ↔ PreToolUse loop-detect ---


def test_l1_observer_increments_then_pretooluse_denies_at_threshold(
    stub_env: dict[str, str],
    tmp_path: Path,
) -> None:
    """E2E: PostToolUse observer increments L1 across 6 invocations
    on the same file; the 7th attempt's PreToolUse loop-detect sees
    count=6 and denies + fires Telegram with the Cray-E.4 payload.
    """
    file_path = str(tmp_path / "integration-target.py")
    for _ in range(6):
        rc = _run(
            POST_OBSERVER_HOOK,
            _write_payload(file_path, post=True),
            stub_env,
        )[0]
        assert rc == 0
    # State now has L1 counter at 6 for this target.
    counter = load_counter(_state(stub_env))
    assert get_count(counter, LoopType.FILE_EDIT, file_path) == 6, "observer should have reached 6"

    # Next attempt's PreToolUse gate must deny.
    rc, out = _run(PRE_LOOP_HOOK, _write_payload(file_path), stub_env)
    assert rc == 0
    parsed = json.loads(out)
    decision = parsed.get("hookSpecificOutput", {}).get("permissionDecision")
    assert decision == "deny", "L1 at 6 must deny on next PreToolUse"
    captured = json.loads(_capture(stub_env).read_text(encoding="utf-8"))
    assert captured["loop_type"] == "L1"
    assert captured["target"].endswith("integration-target.py")
    assert len(captured["last_6_actions"]) == 6


def test_l4_observer_increments_on_failure_then_pretooluse_denies(
    stub_env: dict[str, str],
) -> None:
    """E2E: 6 failed `pytest tests/x.py` Bash calls → L4 counter at 6
    → PreToolUse denies on the 7th attempt of the same tokenized
    command pattern.
    """
    command = "pytest tests/integration_dummy.py"
    for _ in range(6):
        rc = _run(
            POST_OBSERVER_HOOK,
            _bash_payload(command, exit_code=1, post=True),
            stub_env,
        )[0]
        assert rc == 0
    rc, out = _run(PRE_LOOP_HOOK, _bash_payload(command), stub_env)
    assert rc == 0
    parsed = json.loads(out)
    assert (
        parsed.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
    ), "L4 at 6 must deny on next PreToolUse"
    captured = json.loads(_capture(stub_env).read_text(encoding="utf-8"))
    assert captured["loop_type"] == "L4"


def test_l4_observer_resets_on_success(stub_env: dict[str, str]) -> None:
    """E2E: 5 failed Bash calls bring L4 to 5; a single success on the
    same command pattern resets the L4 counter to 0; PreToolUse allows.
    """
    command = "pytest tests/integration_dummy.py"
    for _ in range(5):
        _run(POST_OBSERVER_HOOK, _bash_payload(command, exit_code=1, post=True), stub_env)
    _run(POST_OBSERVER_HOOK, _bash_payload(command, exit_code=0, post=True), stub_env)
    counter = load_counter(_state(stub_env))
    assert get_count(counter, LoopType.BASH_PATTERN, command) == 0, "success must reset L4"

    rc, out = _run(PRE_LOOP_HOOK, _bash_payload(command), stub_env)
    assert rc == 0
    # Allow path: no decision emitted.
    assert out == ""


# --- D. Observer L2/L3 inline Telegram fire ---


def test_l2_inline_telegram_fires_on_threshold(
    stub_env: dict[str, str],
) -> None:
    """E2E: 6 ``Bash`` invocations whose tool_response carries pytest
    FAILED output for the same nodeid → on the 6th, the observer fires
    Telegram inline with L2 payload.
    """
    nodeid = "tests/handoffs/test_dummy.py::test_failing"
    pytest_output = f"FAILED {nodeid} - AssertionError: boom\n1 failed in 0.05s"
    payload: Payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "pytest tests/handoffs/test_dummy.py"},
        "tool_response": {
            "exit_code": 1,
            "stdout": pytest_output,
            "stderr": "",
        },
    }
    for _ in range(6):
        rc = _run(POST_OBSERVER_HOOK, payload, stub_env)[0]
        assert rc == 0
    captured = json.loads(_capture(stub_env).read_text(encoding="utf-8"))
    assert captured["loop_type"] == "L2"
    assert nodeid in captured["target"]


def test_l2_resets_on_pass_for_same_nodeid(
    stub_env: dict[str, str],
) -> None:
    """E2E (Step 8 / AC-3 reset semantic): L2 counter accumulates to 3
    on failures for a nodeid, then a single PASSED observation for the
    same nodeid zeroes the counter. Demonstrates observer's
    extract_passed_nodeids → reset flow per PLAN §Step 3.
    """
    nodeid = "tests/handoffs/test_dummy.py::test_flaky"
    fail_payload: Payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "pytest tests/handoffs/test_dummy.py"},
        "tool_response": {
            "exit_code": 1,
            "stdout": f"FAILED {nodeid} - AssertionError: still red\n1 failed",
            "stderr": "",
        },
    }
    pass_payload: Payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "pytest tests/handoffs/test_dummy.py"},
        "tool_response": {
            "exit_code": 0,
            "stdout": f"{nodeid} PASSED [100%]\n1 passed",
            "stderr": "",
        },
    }
    for _ in range(3):
        _run(POST_OBSERVER_HOOK, fail_payload, stub_env)
    counter = load_counter(_state(stub_env))
    assert (
        get_count(counter, LoopType.TEST_FAIL, nodeid) == 3
    ), "L2 should have accumulated to 3 before reset"

    _run(POST_OBSERVER_HOOK, pass_payload, stub_env)
    counter = load_counter(_state(stub_env))
    assert (
        get_count(counter, LoopType.TEST_FAIL, nodeid) == 0
    ), "PASSED observation must zero L2 counter for that nodeid"


def test_l3_inline_telegram_fires_on_traceback_signature_threshold(
    stub_env: dict[str, str],
) -> None:
    """E2E (Step 8 / AC-3 trigger): 6 Bash invocations each containing
    a Python traceback whose last line is the same exception signature
    → observer hashes the signature, increments L3 counter, and at the
    6th fires Telegram inline with the L3 payload.

    L3 auto-reset is **deferred** per PLAN-0008 §Step 4 closeout
    ("signature absent from next 2 tool outputs" needs multi-tool
    observation — held for PLAN-0009+).
    """
    traceback_text = (
        "Traceback (most recent call last):\n"
        '  File "x.py", line 10, in <module>\n'
        "    func()\n"
        "AssertionError: signature should be stable across attempts"
    )
    payload: Payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "python x.py"},
        "tool_response": {
            "exit_code": 1,
            "stdout": "",
            "stderr": traceback_text,
        },
    }
    for _ in range(6):
        rc = _run(POST_OBSERVER_HOOK, payload, stub_env)[0]
        assert rc == 0
    captured = json.loads(_capture(stub_env).read_text(encoding="utf-8"))
    assert captured["loop_type"] == "L3"
    # Target is the hashed signature; assert it is non-empty + the
    # last_6_actions ring buffer is full.
    assert captured["target"]
    assert len(captured["last_6_actions"]) == 6


# --- E. Stop turn-boundary reset ↔ observer turn_touched ---


def test_l1_counter_survives_when_target_in_turn_touched(
    stub_env: dict[str, str],
    tmp_path: Path,
) -> None:
    """E2E: observer records turn_touched on Write/Edit; Stop hook then
    sees the L1 counter's target IS in turn_touched and does NOT reset.
    """
    file_path = str(tmp_path / "touched-this-turn.py")
    # Three observer calls increment L1 + record turn_touched.
    for _ in range(3):
        _run(POST_OBSERVER_HOOK, _write_payload(file_path, post=True), stub_env)
    # Fail-closed classifier (no API key) so Stop just runs turn-reset + exits.
    rc, _ = _run(STOP_HOOK, {"hook_event_name": "Stop"}, stub_env)
    assert rc == 0
    counter = load_counter(_state(stub_env))
    assert (
        get_count(counter, LoopType.FILE_EDIT, file_path) == 3
    ), "in-turn target must NOT be reset"
    # And turn_touched is cleared so the NEXT turn-boundary will reset.
    assert counter.turn_touched == []


def test_l1_counter_resets_when_target_not_in_turn_touched(
    stub_env: dict[str, str], tmp_path: Path
) -> None:
    """E2E: pre-seed an L1 counter for a file that was NOT touched in
    the current turn (empty turn_touched). Stop hook resets it to 0.
    """
    file_path = str(tmp_path / "stale-file.py")
    seed = new_counter("s")
    increment(
        seed,
        LoopType.FILE_EDIT,
        file_path,
        ActionRecord("2026-05-24", "Edit", file_path),
    )
    increment(
        seed,
        LoopType.FILE_EDIT,
        file_path,
        ActionRecord("2026-05-24", "Edit", file_path),
    )
    # turn_touched left empty — last turn ended, this is a fresh turn.
    save_counter(seed, _state(stub_env))

    rc, _ = _run(STOP_HOOK, {"hook_event_name": "Stop"}, stub_env)
    assert rc == 0
    counter = load_counter(_state(stub_env))
    assert (
        get_count(counter, LoopType.FILE_EDIT, file_path) == 0
    ), "untouched-last-turn L1 must reset"


def test_stop_hook_active_does_not_reset_l1_counters(
    stub_env: dict[str, str],
    tmp_path: Path,
) -> None:
    """E2E: re-entry guard short-circuit must not touch state — even
    counters that would normally be reset (target not in turn_touched)
    survive when stop_hook_active=True.
    """
    file_path = str(tmp_path / "preserved-on-reentry.py")
    seed = new_counter("s")
    increment(
        seed,
        LoopType.FILE_EDIT,
        file_path,
        ActionRecord("2026-05-24", "Edit", file_path),
    )
    save_counter(seed, _state(stub_env))
    rc, _ = _run(
        STOP_HOOK,
        {"hook_event_name": "Stop", "stop_hook_active": True},
        stub_env,
    )
    assert rc == 0
    counter = load_counter(_state(stub_env))
    assert (
        get_count(counter, LoopType.FILE_EDIT, file_path) == 1
    ), "re-entry guard must short-circuit before turn-reset"


# --- F. Stop ↔ chain depth full cycle ---


def test_stop_proceed_increments_chain_depth(stub_env: dict[str, str]) -> None:
    """E2E: classifier returns proceed → chain depth goes from 0 to 1
    in the persisted state file.
    """
    stub_env["ANTHROPIC_API_KEY"] = "sk-int-fake-key"  # pragma: allowlist secret
    with _mock_sonnet_server({"decision": "proceed", "matched_rows": [], "reason": "go"}) as (
        url,
        _log,
    ):
        stub_env["CLAUDE_SONNET_API_URL"] = url
        rc, _ = _run(STOP_HOOK, {"hook_event_name": "Stop"}, stub_env)
    assert rc == 0
    chain = json.loads(_chain(stub_env).read_text(encoding="utf-8"))
    assert chain["depth"] == 1
    assert chain["last_proceed_ts"] != ""


def test_stop_proceed_then_pause_resets_chain(stub_env: dict[str, str]) -> None:
    """E2E: 2 proceeds then a pause — chain goes 0→1→2→0 across three
    consecutive Stop invocations.
    """
    stub_env["ANTHROPIC_API_KEY"] = "sk-int-fake-key"  # pragma: allowlist secret
    proceed_canned = {
        "decision": "proceed",
        "matched_rows": [],
        "reason": "step 1 ok",
    }
    with _mock_sonnet_server(proceed_canned) as (url, _log):
        stub_env["CLAUDE_SONNET_API_URL"] = url
        for expected_depth in (1, 2):
            _run(STOP_HOOK, {"hook_event_name": "Stop"}, stub_env)
            chain = json.loads(_chain(stub_env).read_text(encoding="utf-8"))
            assert chain["depth"] == expected_depth

    pause_canned = {
        "decision": "pause",
        "matched_rows": ["G1"],
        "reason": "stop and yield",
    }
    with _mock_sonnet_server(pause_canned) as (url, _log):
        stub_env["CLAUDE_SONNET_API_URL"] = url
        _run(STOP_HOOK, {"hook_event_name": "Stop"}, stub_env)
    chain = json.loads(_chain(stub_env).read_text(encoding="utf-8"))
    assert chain["depth"] == 0


# --- G. Phase 1 + C4 regression cross-reference (AC-4 discoverability) ---


def test_phase1_regression_test_files_present() -> None:
    """AC-4 cross-reference (no duplication). The Phase 1 + C4 bypass-
    immunity matrices live in their own test files; this assertion just
    ensures they exist so Step 8 live AC has a discoverable starting
    point.
    """
    expected = [
        "tests/handoffs/test_pretooluse_git_deny.py",
        "tests/handoffs/test_posttooluse_validate_handoff.py",
        "tests/handoffs/test_pretooluse_research_path_deny.py",
    ]
    missing = [p for p in expected if not (REPO_ROOT / p).is_file()]
    assert not missing, (
        f"Phase 1 regression test files missing: {missing}. AC-4 cannot "
        "be re-run without them — restore from main or revisit PLAN-0007."
    )
