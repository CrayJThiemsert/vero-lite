"""Gated live-API smoke test for ``_sonnet_classifier.classify`` over a
real ``Stop`` payload with a transcript fixture matching the Smoke 2 D1
trigger (PLAN-0011 §Step 4, AC-5).

**Skipped by default.** Run locally with:

    RUN_LIVE_CLASSIFIER_TESTS=1 uv run --extra dev pytest \\
        tests/handoffs/test_classifier_live_smoke.py -v

The test verifies the Lesson #15 fix end-to-end: with the transcript
excerpt now included in the user message, Sonnet should match D1
(governance-drafting auto-handoff) and return ``decision == "dispatch"``
on a Stop event that follows a Cray-driven ADR-drafting request. Before
PLAN-0011, the same input produced ``decision: proceed`` because the
classifier saw only metadata, not the conversation context.

Requires:

- ``$ANTHROPIC_API_KEY`` in env, OR ``~/.claude/.anthropic_api_key`` file
- The real registry at ``.claude/autonomy-triggers.md`` (not patched).

Cost note: one live Sonnet call per invocation (~5s, sub-cent). Skip in
CI; opt-in only.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"
sys.path.insert(0, str(HOOKS_DIR))

import _sonnet_classifier as sc  # noqa: E402

LIVE_GATE = pytest.mark.skipif(
    os.environ.get("RUN_LIVE_CLASSIFIER_TESTS") != "1",
    reason=(
        "live API smoke; set RUN_LIVE_CLASSIFIER_TESTS=1 to enable "
        "(opt-in to avoid CI billing + non-deterministic CI failures)"
    ),
)


@LIVE_GATE
def test_d1_stop_dispatch_live() -> None:
    """Live AC: a Stop event whose transcript shows Cray ratifying an
    ADR-drafting request followed by the agent's ack-only turn should
    trigger the D1 auto-handoff arm (``decision: dispatch``,
    ``matched_rows`` includes ``"D1"``).

    Asserts the post-PLAN-0011 behavior: classifier sees the
    conversation excerpt and routes to dispatch instead of defaulting
    to proceed (the Lesson #15 starvation finding).
    """
    fixture = FIXTURES_DIR / "transcript_smoke_d1.jsonl"
    assert fixture.exists(), f"missing fixture: {fixture}"

    payload = {
        "hook_event_name": "Stop",
        "transcript_path": str(fixture),
        "session_id": "live-smoke-d1",
    }
    result = sc.classify(payload)

    # Contract guards first
    assert isinstance(result, dict)
    assert result["decision"] in {"proceed", "pause", "dispatch"}
    assert isinstance(result.get("matched_rows"), list)

    # AC: decision is dispatch + cites D1
    decision = result["decision"]
    matched = result.get("matched_rows", [])
    reason = result.get("reason", "")
    assert decision == "dispatch", (
        f"expected dispatch, got {decision!r}; matched_rows={matched}; " f"reason={reason!r}"
    )
    assert "D1" in matched, f"expected D1 in matched_rows, got {matched}; reason={reason!r}"

    # Dispatch metadata sanity
    dispatch = result.get("dispatch")
    assert isinstance(dispatch, dict), f"dispatch metadata missing: {result}"
    assert dispatch.get("subagent") == "plan-drafter"
    assert dispatch.get("artifact_kind") == "adr"
    assert isinstance(dispatch.get("task_summary"), str)
    assert dispatch["task_summary"].strip(), "task_summary empty"


def test_d1_fixture_renders_into_user_message() -> None:
    """Companion AC-1 verification (no API call). Asserts the rendered
    user_message that the live test would send contains the fixture's
    user turn + assistant turn, so a failure of
    ``test_d1_stop_dispatch_live`` cannot be blamed on the prompt
    being empty. Always runs (no live gate).
    """
    fixture = FIXTURES_DIR / "transcript_smoke_d1.jsonl"
    assert fixture.exists()
    payload = {
        "hook_event_name": "Stop",
        "transcript_path": str(fixture),
        "session_id": "live-smoke-d1",
    }
    rendered = sc._build_user_message(payload)
    assert "## Recent conversation excerpt" in rendered
    assert "ADR-0014" in rendered  # from user turn
    assert "cross-tab MCP transport" in rendered  # from user turn
    assert "draft ADR-0014" in rendered  # from assistant ack
    # JSON dump still present
    assert "## Raw payload" in rendered
    assert '"hook_event_name": "Stop"' in rendered
    # Sanity: the noise fallback didn't fire
    assert sc.TRANSCRIPT_UNAVAILABLE not in rendered
    assert sc.TRANSCRIPT_UNREADABLE not in rendered


if __name__ == "__main__":  # pragma: no cover — manual invocation aid
    # Quick local sanity: `python tests/handoffs/test_classifier_live_smoke.py`
    # prints what would be sent to Sonnet.
    fixture = FIXTURES_DIR / "transcript_smoke_d1.jsonl"
    payload = {
        "hook_event_name": "Stop",
        "transcript_path": str(fixture),
        "session_id": "live-smoke-d1",
    }
    rendered = sc._build_user_message(payload)
    print(rendered)
    if os.environ.get("RUN_LIVE_CLASSIFIER_TESTS") == "1":
        print("\n=== LIVE CLASSIFIER RESULT ===\n")
        print(json.dumps(sc.classify(payload), indent=2, ensure_ascii=False))
