#!/usr/bin/env python3
"""Stop hook — turn-boundary L1 reset + chain-cap fail-safe (PLAN-0008 Step 4).

Fires on every ``Stop`` event. Two responsibilities:

1. **Turn-boundary reset (priority).** Reads ``turn_touched`` from the
   loop-counter state file (recorded by Step 3's
   ``posttooluse_progress_observer.py`` on each Write/Edit) and resets
   L1 counters whose targets were NOT touched this turn. Implements
   the "target untouched on the next turn-boundary marker" rule from
   PLAN §Step 1 / §Step 3. **Closes the 🔴 L1 reset gap** surfaced in
   the L1/L4 asymmetry ELI-CTO (Cray's iterative STATUS-editing
   workflow would otherwise false-positive at 6 edits per session).
2. **Chain-cap fail-safe (PLAN §Step 4).** Tracks consecutive
   ``proceed`` decisions in ``.claude/state/stop-chain.json`` against
   ``$CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`` (default 8). On cap-hit:
   emits no block (lets the stop fire), pings Telegram with
   ``"cap reached"`` per OQ-E option (b), and resets the chain.
   Re-entry guarded by the harness ``stop_hook_active`` flag.

The Sonnet pause/proceed classifier (PLAN §Step 5) is dispatched
via a **stub** that returns ``"pause"`` by default — until Step 5
lands the classifier helper, the conservative default keeps the
agent in human-supervised mode. When Step 5 lands, replace
``_classifier_stub`` with the real Sonnet call without changing
this hook's flow.

State file paths and Telegram script honor the env-var overrides
shared with Step 2/3 for testability
(``CLAUDE_LOOP_COUNTER_PATH``, ``CLAUDE_TELEGRAM_SCRIPT``,
``CLAUDE_STOP_CHAIN_PATH``, ``CLAUDE_CODE_STOP_HOOK_BLOCK_CAP``).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from _loop_counter import (  # noqa: E402  — sys.path manipulation above
    DEFAULT_COUNTER_PATH,
    STATE_DIR,
    clear_turn_touched,
    load_counter,
    reset_untouched_l1,
    save_counter,
)

DEFAULT_TELEGRAM_SCRIPT = REPO_ROOT / "tools" / "notify" / "telegram.sh"
DEFAULT_CHAIN_PATH = STATE_DIR / "stop-chain.json"
DEFAULT_CAP = 8
TELEGRAM_TIMEOUT_SEC = 5


def _state_path() -> Path:
    override = os.environ.get("CLAUDE_LOOP_COUNTER_PATH")
    return Path(override) if override else DEFAULT_COUNTER_PATH


def _chain_path() -> Path:
    override = os.environ.get("CLAUDE_STOP_CHAIN_PATH")
    return Path(override) if override else DEFAULT_CHAIN_PATH


def _telegram_script() -> Path:
    override = os.environ.get("CLAUDE_TELEGRAM_SCRIPT")
    return Path(override) if override else DEFAULT_TELEGRAM_SCRIPT


def _cap() -> int:
    raw = os.environ.get("CLAUDE_CODE_STOP_HOOK_BLOCK_CAP")
    if not raw:
        return DEFAULT_CAP
    try:
        v = int(raw)
        return v if v > 0 else DEFAULT_CAP
    except ValueError:
        return DEFAULT_CAP


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S%z")


def _load_chain() -> dict[str, Any]:
    p = _chain_path()
    if not p.exists():
        return {"depth": 0, "last_proceed_ts": ""}
    try:
        data = json.loads(p.read_text(encoding="utf-8") or "{}")
    except (OSError, json.JSONDecodeError):
        return {"depth": 0, "last_proceed_ts": ""}
    if not isinstance(data, dict):
        return {"depth": 0, "last_proceed_ts": ""}
    depth = data.get("depth", 0)
    return {
        "depth": depth if isinstance(depth, int) else 0,
        "last_proceed_ts": str(data.get("last_proceed_ts", "")),
    }


def _save_chain(data: dict[str, Any]) -> None:
    p = _chain_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, sort_keys=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(p.parent),
        delete=False,
        prefix=p.name + ".",
        suffix=".tmp",
    ) as tmp:
        tmp.write(payload)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, p)


def _reset_chain() -> None:
    _save_chain({"depth": 0, "last_proceed_ts": ""})


def _ping_telegram(message: dict[str, Any]) -> None:
    """Best-effort Telegram ping. Never raises; the hook flow continues."""
    script = _telegram_script()
    if not script.exists():
        return
    try:
        # S603/S607 carry the Phase 1 idiom justification.
        subprocess.run(  # noqa: S603
            ["bash", str(script)],  # noqa: S607
            input=json.dumps(message),
            text=True,
            capture_output=True,
            check=False,
            timeout=TELEGRAM_TIMEOUT_SEC,
        )
    except (subprocess.TimeoutExpired, OSError):
        pass


def _apply_turn_boundary_reset() -> list[str]:
    """Read state, reset untouched L1 counters, clear turn_touched.

    Returns the list of L1 targets that were reset (informational —
    Step 4 does not fire Telegram for reset events; they are by
    definition healthy progress signals).
    """
    counter = load_counter(_state_path())
    reset_targets = reset_untouched_l1(counter)
    clear_turn_touched(counter)
    save_counter(counter, _state_path())
    return reset_targets


def _classifier_stub() -> dict[str, str]:
    """Sonnet pause/proceed classifier — STUBBED.

    Step 5 (`sonnet_classifier.py`) will replace this with the real
    Sonnet call that reads `.claude/autonomy-triggers.md`. Until then,
    the conservative default is **pause** so the agent yields to Cray
    at every stop — preserving the pre-Phase-2 human-supervised
    cadence while the deterministic L1 reset benefit lands.
    """
    return {
        "decision": "pause",
        "reason": (
            "Sonnet classifier not yet wired (Step 5 pending). "
            "Defaulting to pause — agent yields to Cray. Step 4 L1 "
            "reset has already run."
        ),
    }


def _proceed_block(reason: str) -> dict[str, Any]:
    """`decision: block` on Stop = continuation loop (per Anthropic
    stop-hook docs: blocking returns the agent to the loop).
    """
    return {
        "decision": "block",
        "reason": reason,
        "hookSpecificOutput": {"hookEventName": "Stop"},
    }


def _cap_reached_payload(depth: int, cap: int) -> dict[str, Any]:
    return {
        "event": "stop_continuation_cap_reached",
        "depth": depth,
        "cap": cap,
        "ts": _now_iso(),
        "reason": (
            f"Stop hook chain depth {depth} reached cap {cap}. "
            "Releasing agent to Cray (no block). Chain counter reset."
        ),
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # fail-open

    # Re-entry guard: if the harness reports we are already inside a
    # stop-hook chain, do not re-enter (no reset, no classifier dispatch,
    # no chain increment). Let the stop fire normally.
    if payload.get("stop_hook_active") is True:
        return 0

    # Always run the turn-boundary reset first — it is independent of the
    # chain-cap / classifier flow and is the load-bearing Step 4 benefit.
    try:
        _apply_turn_boundary_reset()
    except Exception as exc:  # observer must not block on internal errors
        print(f"stop_continuation: turn-boundary reset failed: {exc}", file=sys.stderr)

    # Chain-cap fail-safe (OQ-E option b).
    cap = _cap()
    chain = _load_chain()
    if chain["depth"] >= cap:
        _ping_telegram(_cap_reached_payload(chain["depth"], cap))
        _reset_chain()
        return 0  # do not block; let Cray see the stop event

    # Classifier dispatch (stub for now — Step 5 replaces).
    decision = _classifier_stub()
    if decision.get("decision") == "proceed":
        chain["depth"] += 1
        chain["last_proceed_ts"] = _now_iso()
        _save_chain(chain)
        print(json.dumps(_proceed_block(decision.get("reason", "continue"))))
        return 0

    # "pause" → no block; reset the chain so the next session starts fresh.
    _reset_chain()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
