"""Tests for ``.claude/hooks/_sonnet_classifier.py`` (PLAN-0008 Step 5).

Covers:

- Schema contract: classify() returns {decision, matched_rows, reason}
- Fail-closed pause: missing API key, missing registry file, network
  error, HTTP error, timeout, malformed wire JSON, malformed text JSON
  after retry
- Successful proceed/pause parses
- JSON-in-markdown extraction (model wrapping in ```json fences)
- Retry-once with stricter prompt on first parse failure
- Env-var overrides honored (registry path, model, API URL)

The mocked transport intercepts ``urllib.request.urlopen`` at module
scope so the helper sees fake responses without hitting the network.

Live smoke test gated by ``RUN_LIVE_SONNET_TESTS=1`` env (skipped in
CI per OQ-G).
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import sys
import urllib.error
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

import _sonnet_classifier as sc  # noqa: E402  — sys.path manipulation above


@pytest.fixture(autouse=True)
def isolated_key_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Always isolate the key-file path so tests never see a real
    ``~/.claude/.anthropic_api_key`` that a developer may have populated
    for Step 5b operation. Tests that need a populated file write to the
    returned path (and chmod 600 on POSIX).
    """
    fake = tmp_path / ".anthropic_api_key"
    monkeypatch.setenv("CLAUDE_ANTHROPIC_KEY_FILE", str(fake))
    return fake


@pytest.fixture
def fake_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    p = tmp_path / "autonomy-triggers.md"
    p.write_text(
        "# Autonomy Triggers Registry (test fixture)\n\n"
        "| # | Trigger | Phase 1 | Phase 2 |\n"
        "|---|---------|---------|---------|\n"
        "| G1 | Mutate any ADR with Status: Accepted | Advisory | Classifier pause |\n"
        "| L1 | Same file edited >= 6 times | Manual | Enforced |\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CLAUDE_AUTONOMY_REGISTRY_PATH", str(p))
    return p


@pytest.fixture(autouse=True)
def force_sonnet_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin the legacy suite to the sonnet backend. These tests exercise the
    Anthropic-API transport + auth chain, which since Cray pick (b)
    (2026-06-12) is the ROLLBACK path — the default backend is local Ollama.
    The Ollama-backend section below overrides this env per-test."""
    monkeypatch.setenv("CLAUDE_CLASSIFIER_BACKEND", "sonnet")


@pytest.fixture
def with_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake-key")


def _write_key_file(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if os.name == "posix":
        os.chmod(path, 0o600)
    return path


def _make_response(text: str) -> MagicMock:
    """Build a context-manager mock that mimics urlopen's response."""
    wire = {"content": [{"type": "text", "text": text}]}
    raw = json.dumps(wire).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = raw
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = False
    return mock_resp


# --- Fail-closed pause paths ---


def test_pause_when_api_key_missing(monkeypatch: pytest.MonkeyPatch, fake_registry: Path) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"
    assert "ANTHROPIC_API_KEY" in result["reason"]
    assert result["matched_rows"] == []


def test_pause_when_registry_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, with_api_key: None
) -> None:
    monkeypatch.setenv("CLAUDE_AUTONOMY_REGISTRY_PATH", str(tmp_path / "nope.md"))
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"
    assert "registry" in result["reason"]


def test_pause_when_registry_empty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, with_api_key: None
) -> None:
    p = tmp_path / "empty.md"
    p.write_text("   \n\n", encoding="utf-8")
    monkeypatch.setenv("CLAUDE_AUTONOMY_REGISTRY_PATH", str(p))
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"


def test_pause_on_url_error(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    def boom(req: Any, timeout: int) -> Any:
        raise urllib.error.URLError("network down")

    monkeypatch.setattr(sc.urllib.request, "urlopen", boom)
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"
    assert "unreachable" in result["reason"]


def test_pause_on_http_error(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    def boom(req: Any, timeout: int) -> Any:
        raise urllib.error.HTTPError(
            url="https://api.anthropic.com",
            code=503,
            msg="Service Unavailable",
            hdrs=None,  # type: ignore[arg-type]
            fp=io.BytesIO(b""),
        )

    monkeypatch.setattr(sc.urllib.request, "urlopen", boom)
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"


def test_pause_on_timeout(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    def boom(req: Any, timeout: int) -> Any:
        raise TimeoutError("slow")

    monkeypatch.setattr(sc.urllib.request, "urlopen", boom)
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"


def test_pause_on_malformed_wire(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    """Wire response missing 'content' → fail-closed pause."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"unexpected": "shape"}'
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = False
    monkeypatch.setattr(sc.urllib.request, "urlopen", lambda req, timeout: mock_resp)
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"
    assert "malformed" in result["reason"] or "missing" in result["reason"]


# --- Successful parse paths ---


def test_successful_proceed(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    body = '{"decision": "proceed", "matched_rows": [], "reason": "tests pass, safe to commit"}'
    monkeypatch.setattr(sc.urllib.request, "urlopen", lambda req, timeout: _make_response(body))
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "proceed"
    assert result["matched_rows"] == []
    assert "tests pass" in result["reason"]


def test_successful_pause_with_matched_rows(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    body = (
        '{"decision": "pause", "matched_rows": ["G1", "L1"], '
        '"reason": "about to edit accepted ADR"}'
    )
    monkeypatch.setattr(sc.urllib.request, "urlopen", lambda req, timeout: _make_response(body))
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"
    assert result["matched_rows"] == ["G1", "L1"]


def test_extracts_json_from_markdown_fence(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    """Model wraps response in ```json fences despite instructions."""
    body = (
        "Sure, here's my analysis:\n\n"
        "```json\n"
        '{"decision": "pause", "matched_rows": ["G1"], "reason": "edit ADR detected"}\n'
        "```\n\n"
        "Let me know if you need more context."
    )
    monkeypatch.setattr(sc.urllib.request, "urlopen", lambda req, timeout: _make_response(body))
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"
    assert "G1" in result["matched_rows"]


# --- Retry-once path ---


def test_retry_once_on_first_parse_failure(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    """First call returns unparseable text; retry returns valid JSON."""
    call_count = {"n": 0}

    def fake_urlopen(req: Any, timeout: int) -> Any:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _make_response("this is not json at all")
        return _make_response('{"decision": "proceed", "matched_rows": [], "reason": "ok"}')

    monkeypatch.setattr(sc.urllib.request, "urlopen", fake_urlopen)
    result = sc.classify({"event": "Stop"})
    assert call_count["n"] == 2
    assert result["decision"] == "proceed"


def test_pause_when_retry_also_fails(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    monkeypatch.setattr(
        sc.urllib.request,
        "urlopen",
        lambda req, timeout: _make_response("still not json"),
    )
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"
    assert "unparseable" in result["reason"]


def test_pause_when_decision_value_invalid(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    """Model returns a decision outside the proceed/pause enum."""
    body = '{"decision": "maybe", "matched_rows": [], "reason": "unsure"}'
    monkeypatch.setattr(sc.urllib.request, "urlopen", lambda req, timeout: _make_response(body))
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"


# --- Env-var overrides ---


def test_model_override_honored(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(req: Any, timeout: int) -> Any:
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return _make_response('{"decision": "pause", "matched_rows": [], "reason": "x"}')

    monkeypatch.setenv("CLAUDE_SONNET_MODEL", "claude-sonnet-4-7")
    monkeypatch.setattr(sc.urllib.request, "urlopen", fake_urlopen)
    sc.classify({"event": "Stop"})
    assert captured["body"]["model"] == "claude-sonnet-4-7"


def test_api_url_override_honored(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    captured: dict[str, str] = {}

    def fake_urlopen(req: Any, timeout: int) -> Any:
        captured["url"] = req.full_url
        return _make_response('{"decision": "pause", "matched_rows": [], "reason": "x"}')

    monkeypatch.setenv("CLAUDE_SONNET_API_URL", "http://localhost:9999/test")
    monkeypatch.setattr(sc.urllib.request, "urlopen", fake_urlopen)
    sc.classify({"event": "Stop"})
    assert captured["url"] == "http://localhost:9999/test"


# --- Schema contract sanity ---


def test_result_always_has_required_keys(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path
) -> None:
    """Even in the absolute-failure path, the contract holds."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = sc.classify({"event": "Stop"})
    assert set(result.keys()) >= {"decision", "matched_rows", "reason"}
    assert isinstance(result["matched_rows"], list)
    assert isinstance(result["reason"], str)


# --- Ollama backend (the DEFAULT since Cray pick (b), 2026-06-12) ------------


def _make_ollama_response(text: str) -> MagicMock:
    """Context-manager mock mimicking urlopen against Ollama /api/chat."""
    wire = {"message": {"role": "assistant", "content": text}}
    raw = json.dumps(wire).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = raw
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = False
    return mock_resp


def test_default_backend_is_ollama_and_needs_no_api_key(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path
) -> None:
    """With the env unset the classifier goes to MS-S1 Ollama — no API key in
    the chain at all (the auth requirement is sonnet-backend-only), with the
    format-constrained, temperature-0, keep-alive request shape."""
    monkeypatch.delenv("CLAUDE_CLASSIFIER_BACKEND", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    seen: dict[str, Any] = {}

    def fake_urlopen(req: Any, timeout: float) -> MagicMock:
        seen["url"] = req.full_url
        seen["timeout"] = timeout
        seen["body"] = json.loads(req.data.decode("utf-8"))
        return _make_ollama_response('{"decision": "proceed", "matched_rows": [], "reason": "ok"}')

    monkeypatch.setattr(sc.urllib.request, "urlopen", fake_urlopen)
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "proceed"
    assert seen["url"] == "http://192.168.1.133:11434/api/chat"
    assert seen["timeout"] == sc.OLLAMA_TIMEOUT_SEC
    body = seen["body"]
    assert body["model"] == "gpt-oss:20b"
    assert body["stream"] is False
    assert body["options"] == {"temperature": 0}
    assert body["keep_alive"] == "10m"
    assert body["format"]["properties"]["decision"]["enum"] == [
        "proceed",
        "pause",
        "dispatch",
    ]
    assert body["messages"][0]["role"] == "system"
    # PLAN-0122 Step 3: the Stop arm embeds the registry AGAIN. Step 2 briefly
    # routed it to SLIM5; the held-out validation refuted that (SLIM5 2 unsafe
    # per 30 against FULL's 0) and session 281 reverted the routing on Cray's
    # call. The s56-era assertion is restored because it is true again — not
    # because the Step 2 version was wrong when it was written. The companion
    # negative is what makes this more than the original: it fails if SLIM5
    # comes back without AC-7 passing.
    assert "REGISTRY START" in body["messages"][0]["content"]
    assert body["messages"][0]["content"] != sc.STOP_SYSTEM_PROMPT


def test_pretooluse_still_embeds_the_registry_verbatim(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path
) -> None:
    """The PLAN-0122 prompt swap is Stop-only, and this is the other half of it.

    SLIM5's rule 4 — "This is a hook event, not a permission request. Do not
    answer whether an action is allowed" — is exactly WRONG for a PreToolUse
    call, where whether the action is allowed IS the question.
    ``pretooluse_classifier_dispatch.py`` shares this ``classify()``, so a swap
    that ignored the event would silently mis-instruct that arm (PLAN-0122
    §4.1, G11).
    """
    monkeypatch.delenv("CLAUDE_CLASSIFIER_BACKEND", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    seen: dict[str, Any] = {}

    def fake_urlopen(req: Any, timeout: float) -> MagicMock:
        seen["body"] = json.loads(req.data.decode("utf-8"))
        return _make_ollama_response('{"decision": "pause", "matched_rows": [], "reason": "ok"}')

    monkeypatch.setattr(sc.urllib.request, "urlopen", fake_urlopen)
    sc.classify({"hook_event_name": "PreToolUse"})

    system = seen["body"]["messages"][0]["content"]
    assert "REGISTRY START" in system
    assert system != sc.STOP_SYSTEM_PROMPT


def test_stop_arm_is_not_slim5_until_ac7_passes(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path
) -> None:
    """PLAN-0122 Step 3 — the guard on the reverted routing.

    Step 2 routed the Stop event to ``STOP_SYSTEM_PROMPT``. Step 3's held-out
    validation refuted it on 30 cases SLIM5 had never seen::

        SLIM5  28/30 correct, 2 unsafe   FULL  29/30 correct, 0 unsafe

    Both SLIM5 hard fails were the dangerous direction — proceed on a
    should-pause case, one of them a destructive database operation. AC-7's read
    was fixed before the run and failed two of its three conjuncts, and SD-1 (b)
    conditioned shipping on that read passing, so ``classify`` no longer passes
    the event and every arm gets the legacy prompt.

    This test exists so the revert cannot be quietly undone: it reddens the
    moment ``classify`` starts routing Stop to SLIM5 again. Re-enabling is a
    Cray decision that needs AC-7 to pass first. Deleting this test to make that
    change green is the failure it is written against.

    The constant and the ``event`` parameter are deliberately still here and
    still pinned by AC-4/AC-5/AC-6 — the measurement is evidence worth keeping,
    and the seam is where a future VALIDATED prompt would attach.
    """
    monkeypatch.delenv("CLAUDE_CLASSIFIER_BACKEND", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    seen: dict[str, Any] = {}

    def fake_urlopen(req: Any, timeout: float) -> MagicMock:
        seen["body"] = json.loads(req.data.decode("utf-8"))
        return _make_ollama_response('{"decision": "pause", "matched_rows": [], "reason": "ok"}')

    monkeypatch.setattr(sc.urllib.request, "urlopen", fake_urlopen)

    # both spellings of the event key the payload can carry
    for payload in ({"hook_event_name": "Stop"}, {"event": "Stop"}):
        seen.clear()
        sc.classify(payload)
        system = seen["body"]["messages"][0]["content"]
        assert system != sc.STOP_SYSTEM_PROMPT, f"SLIM5 is live on Stop for {payload}"
        assert "REGISTRY START" in system, f"Stop lost the registry prompt for {payload}"


def test_ollama_env_overrides_url_and_model(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path
) -> None:
    monkeypatch.delenv("CLAUDE_CLASSIFIER_BACKEND", raising=False)
    monkeypatch.setenv("CLAUDE_CLASSIFIER_OLLAMA_URL", "http://127.0.0.1:9999/")
    monkeypatch.setenv("CLAUDE_CLASSIFIER_OLLAMA_MODEL", "custom-model:1b")
    seen: dict[str, Any] = {}

    def fake_urlopen(req: Any, timeout: float) -> MagicMock:
        seen["url"] = req.full_url
        seen["body"] = json.loads(req.data.decode("utf-8"))
        return _make_ollama_response('{"decision": "pause", "matched_rows": [], "reason": "ok"}')

    monkeypatch.setattr(sc.urllib.request, "urlopen", fake_urlopen)
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"
    assert seen["url"] == "http://127.0.0.1:9999/api/chat"  # trailing slash stripped
    assert seen["body"]["model"] == "custom-model:1b"


def test_ollama_unreachable_fails_closed_to_pause(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path
) -> None:
    """An MS-S1 outage must pause, never proceed (backend-independent
    fail-closed contract)."""
    monkeypatch.delenv("CLAUDE_CLASSIFIER_BACKEND", raising=False)

    def boom(req: Any, timeout: float) -> MagicMock:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(sc.urllib.request, "urlopen", boom)
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"
    assert "unreachable" in result["reason"]


def test_ollama_malformed_envelope_fails_closed_to_pause(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path
) -> None:
    monkeypatch.delenv("CLAUDE_CLASSIFIER_BACKEND", raising=False)
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"no": "message"}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = False
    monkeypatch.setattr(sc.urllib.request, "urlopen", lambda req, timeout: mock_resp)
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"
    assert "malformed" in result["reason"]


def test_system_prompt_carries_the_completion_consistency_rule() -> None:
    """The session-56 calibration fix: the prompt must (a) define PROCEED as
    'has concrete remaining work' — not merely 'safe to continue' — and (b)
    forbid a PROCEED verdict whose reason describes completion / a natural
    stop. Without this rule the classifier was observed returning proceed
    with reasons like 'Session is cleanly complete... natural stop', burning
    a continuation turn on finished work. Contract test so the rule never
    silently regresses out of the prompt.

    PLAN-0122 Step 2 re-scope (G9): this pins the LEGACY builder — the prompt
    every NON-Stop event still receives, today PreToolUse. It calls
    ``_build_system_prompt`` without ``event``, which is the legacy branch by
    design. The Stop arm is pinned separately by the AC-4/AC-5 tests below."""
    prompt = sc._build_system_prompt("registry text here")
    assert "CONCRETE remaining work" in prompt
    assert "Decision and reason" in prompt and "AGREE" in prompt
    assert "NATURAL stop" in prompt
    # The conservative bias stays intact alongside the new rule.
    assert "spurious pauses are preferred over spurious proceeds" in prompt


def test_system_prompt_reserves_cray_only_actions_out_of_proceed() -> None:
    """The session-159 calibration fix: a step RESERVED FOR CRAY (merging a PR,
    ratifying a decision/SD, approving a draft, anything a PLAN's Owner line
    assigns to Cray) is a natural stop, never a PROCEED next action.

    Why this is worth a contract test rather than left to the completion rule
    above: ``stop_continuation._proceed_block`` passes this classifier's
    ``reason`` back to the main agent VERBATIM as the continuation instruction,
    so a reason naming a Cray-reserved step reads to the agent as an instruction
    to PERFORM it. On 2026-07-21 the classifier returned proceed with the reason
    "Merge PR #841" on a turn whose recent activity stated the agent was waiting
    on Cray's merge decision. The agent declined and asked Cray directly — but
    nothing deterministic would have caught it: ``pretooluse_git_deny``'s regex
    is anchored on ``git`` so ``gh pr merge`` never matches, and that gate
    permits the main Code agent in any case. The prompt is the only layer that
    can hold this line, so pin it.

    PLAN-0122 Step 2 re-scope (G9): this pins the LEGACY builder (non-Stop /
    PreToolUse). SLIM5 holds the same line through its STEP 1 row list and its
    REASON RULES, pinned by ``test_slim5_pins_*`` below."""
    prompt = sc._build_system_prompt("registry text here")
    assert "RESERVED FOR CRAY" in prompt
    assert "Merging a PR" in prompt
    # The pass-through mechanic is the REASON for the rule — if this sentence is
    # dropped the rule reads as arbitrary and is likely to be edited away.
    assert "VERBATIM" in prompt
    # The rule must resolve to PAUSE, not merely "be careful".
    assert "return PAUSE and never name it in a reason" in prompt


def test_system_prompt_describes_dispatch_as_a_suggestion_not_an_order() -> None:
    """SD-D, parked at PLAN-0092 and settled here: the prompt must not contradict
    the arm it feeds.

    A' demoted the Stop hook's ``dispatch`` verdict from an order to a suggestion —
    no directive, chain reset, one Telegram ping to Cray. The classifier itself was
    left byte-unchanged under that PLAN's R1 scope lock, so its preamble kept
    describing DISPATCH as an auto-handoff "the agent should NOT pause for" and
    justified conservatism with "they consume a subagent spawn". Post-A' the agent
    DOES pause and nothing is spawned.

    That mattered because ``.claude/autonomy-triggers.md`` is read VERBATIM into the
    same prompt, and the registry already described the no-directive behaviour
    correctly — so the model was being handed ordering framing in the preamble and
    suggestion framing in the embedded registry, in one call.

    PLAN-0122 Step 2 re-scope (G9): this pins the LEGACY builder (non-Stop /
    PreToolUse), which is still the arm that embeds the registry verbatim — so
    the contradiction this test guards against is still possible there, and
    still guarded. SLIM5's dispatch framing is pinned by
    ``test_slim5_pins_the_dispatch_metadata_shape``.
    """
    prompt = sc._build_system_prompt("registry text here")
    assert "ROUTING SUGGESTION" in prompt
    assert "not an\n      instruction to the agent" in prompt
    assert "PLAN-0092" in prompt
    # The false cost claim is gone, and its replacement is true.
    assert "consume a subagent spawn" not in prompt
    assert "one notification to Cray" in prompt
    # The conservative bias survives the rewording — 14 recorded misfires earned it.
    assert "When in doubt between PAUSE and DISPATCH, choose PAUSE" in prompt


def test_the_dispatch_decision_value_and_schema_are_unchanged() -> None:
    """The demotion is an interpretation change, not a protocol change.

    ``stop_continuation`` still branches on ``decision == "dispatch"`` and still
    formats the ping from the ``dispatch`` metadata block, so a reworded prompt that
    also renamed the verdict or dropped the metadata would silence the suggestion
    channel entirely — the failure this pins against.

    PLAN-0122 Step 2 re-scope (G9): this pins the LEGACY builder (non-Stop /
    PreToolUse). The Stop arm's copy of the same envelope is pinned by
    ``test_slim5_pins_the_dispatch_metadata_shape``; both consumers parse
    through the one ``_validate_dispatch_metadata``, so both need pinning.
    """
    prompt = sc._build_system_prompt("registry text here")
    assert '"decision": "proceed" | "pause" | "dispatch"' in prompt
    assert '"subagent": "plan-drafter"' in prompt
    assert '"artifact_kind": "adr" | "plan"' in prompt
    assert "the dispatch arm is fail-closed" in prompt


# --- Step 5b: config-file fallback (defeats Claude Desktop env-strip) ---


def test_resolves_key_from_file_when_env_empty(
    monkeypatch: pytest.MonkeyPatch,
    isolated_key_file: Path,
    fake_registry: Path,
) -> None:
    """Env var absent → reads ``~/.claude/.anthropic_api_key``."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _write_key_file(isolated_key_file, "sk-from-file-12345\n")

    captured: dict[str, str] = {}

    def fake_urlopen(req: Any, timeout: int) -> Any:
        captured["api_key"] = req.headers.get("X-api-key", "")
        return _make_response('{"decision": "proceed", "matched_rows": [], "reason": "ok"}')

    monkeypatch.setattr(sc.urllib.request, "urlopen", fake_urlopen)
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "proceed"
    assert captured["api_key"] == "sk-from-file-12345"  # pragma: allowlist secret


def test_resolves_key_from_file_when_env_is_empty_string(
    monkeypatch: pytest.MonkeyPatch,
    isolated_key_file: Path,
    fake_registry: Path,
) -> None:
    """Env var present but empty string (Claude Desktop strip pattern)
    → still falls back to file. This is the Step 5b motivating case.
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    _write_key_file(isolated_key_file, "sk-desktop-strip-defeated\n")

    captured: dict[str, str] = {}

    def fake_urlopen(req: Any, timeout: int) -> Any:
        captured["api_key"] = req.headers.get("X-api-key", "")
        return _make_response('{"decision": "proceed", "matched_rows": [], "reason": "ok"}')

    monkeypatch.setattr(sc.urllib.request, "urlopen", fake_urlopen)
    sc.classify({"event": "Stop"})
    assert captured["api_key"] == "sk-desktop-strip-defeated"  # pragma: allowlist secret


def test_env_key_wins_when_both_present(
    monkeypatch: pytest.MonkeyPatch,
    isolated_key_file: Path,
    fake_registry: Path,
    with_api_key: None,
) -> None:
    """Env-resolved key wins over file when both are set."""
    _write_key_file(isolated_key_file, "sk-from-file-loses\n")

    captured: dict[str, str] = {}

    def fake_urlopen(req: Any, timeout: int) -> Any:
        captured["api_key"] = req.headers.get("X-api-key", "")
        return _make_response('{"decision": "proceed", "matched_rows": [], "reason": "ok"}')

    monkeypatch.setattr(sc.urllib.request, "urlopen", fake_urlopen)
    sc.classify({"event": "Stop"})
    assert captured["api_key"] == "sk-test-fake-key"  # pragma: allowlist secret — env wins


def test_pause_when_env_empty_and_file_missing(
    monkeypatch: pytest.MonkeyPatch,
    isolated_key_file: Path,
    fake_registry: Path,
) -> None:
    """Both sources unavailable → fail-closed pause with explanatory reason."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # isolated_key_file points to a path inside tmp_path that we deliberately
    # do NOT create — the path exists in env but the file does not.
    assert not isolated_key_file.exists()
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"
    assert "ANTHROPIC_API_KEY" in result["reason"]
    assert "missing" in result["reason"]


def test_pause_when_file_is_empty(
    monkeypatch: pytest.MonkeyPatch,
    isolated_key_file: Path,
    fake_registry: Path,
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _write_key_file(isolated_key_file, "   \n\n\t\n")
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"
    assert "empty" in result["reason"]


def test_pause_when_file_has_unsafe_permissions_posix(
    monkeypatch: pytest.MonkeyPatch,
    isolated_key_file: Path,
    fake_registry: Path,
) -> None:
    """POSIX-only: file readable by group/other → refuse to use it."""
    if os.name != "posix":
        pytest.skip("POSIX permission check; skipped on non-POSIX")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    isolated_key_file.parent.mkdir(parents=True, exist_ok=True)
    isolated_key_file.write_text("sk-but-perms-wrong\n", encoding="utf-8")
    os.chmod(isolated_key_file, 0o644)  # group + other readable
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"
    assert "permissions" in result["reason"] or "chmod" in result["reason"]


def test_file_strips_whitespace_and_uses_first_nonempty_line(
    monkeypatch: pytest.MonkeyPatch,
    isolated_key_file: Path,
    fake_registry: Path,
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _write_key_file(isolated_key_file, "\n\n  sk-padded-with-whitespace  \nextra-line\n")

    captured: dict[str, str] = {}

    def fake_urlopen(req: Any, timeout: int) -> Any:
        captured["api_key"] = req.headers.get("X-api-key", "")
        return _make_response('{"decision": "proceed", "matched_rows": [], "reason": "ok"}')

    monkeypatch.setattr(sc.urllib.request, "urlopen", fake_urlopen)
    sc.classify({"event": "Stop"})
    assert captured["api_key"] == "sk-padded-with-whitespace"  # pragma: allowlist secret


def test_key_file_path_override_honored(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    fake_registry: Path,
) -> None:
    """``$CLAUDE_ANTHROPIC_KEY_FILE`` redirects the fallback file path."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    custom = tmp_path / "subdir" / "my-key-file"
    _write_key_file(custom, "sk-custom-path\n")
    monkeypatch.setenv("CLAUDE_ANTHROPIC_KEY_FILE", str(custom))

    captured: dict[str, str] = {}

    def fake_urlopen(req: Any, timeout: int) -> Any:
        captured["api_key"] = req.headers.get("X-api-key", "")
        return _make_response('{"decision": "proceed", "matched_rows": [], "reason": "ok"}')

    monkeypatch.setattr(sc.urllib.request, "urlopen", fake_urlopen)
    sc.classify({"event": "Stop"})
    assert captured["api_key"] == "sk-custom-path"  # pragma: allowlist secret


def test_resolve_api_key_unit_env_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    """Direct unit-test of the resolver (no network mocking needed)."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-env-direct")
    key, source = sc._resolve_api_key()
    assert key == "sk-env-direct"
    assert source == "env"


def test_resolve_api_key_unit_file_source_tag(
    monkeypatch: pytest.MonkeyPatch, isolated_key_file: Path
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _write_key_file(isolated_key_file, "sk-file-direct\n")
    key, source = sc._resolve_api_key()
    assert key == "sk-file-direct"
    assert source.startswith("file:")
    assert str(isolated_key_file) in source


# --- PLAN-0009 Step 5c-1: dispatch decision arm ---


def _dispatch_body(
    *,
    subagent: str = "plan-drafter",
    artifact_kind: str = "plan",
    task_summary: str = "Draft PLAN-0011 for cross-machine coordination spike",
    matched: list[str] | None = None,
    include_dispatch_field: bool = True,
    extra: dict[str, Any] | None = None,
) -> str:
    """Helper: build a dispatch-decision classifier response JSON body."""
    body: dict[str, Any] = {
        "decision": "dispatch",
        "matched_rows": matched if matched is not None else ["D2"],
        "reason": "governance drafting need; agreed plan needs structuring",
    }
    if include_dispatch_field:
        body["dispatch"] = {
            "subagent": subagent,
            "artifact_kind": artifact_kind,
            "task_summary": task_summary,
        }
    if extra is not None:
        body.update(extra)
    return json.dumps(body)


def test_successful_dispatch_with_valid_metadata(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    monkeypatch.setattr(
        sc.urllib.request,
        "urlopen",
        lambda req, timeout: _make_response(_dispatch_body()),
    )
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "dispatch"
    assert result["matched_rows"] == ["D2"]
    assert "dispatch" in result
    assert result["dispatch"]["subagent"] == "plan-drafter"
    assert result["dispatch"]["artifact_kind"] == "plan"
    assert "PLAN-0011" in result["dispatch"]["task_summary"]


def test_dispatch_artifact_kind_adr(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    monkeypatch.setattr(
        sc.urllib.request,
        "urlopen",
        lambda req, timeout: _make_response(_dispatch_body(artifact_kind="adr", matched=["D1"])),
    )
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "dispatch"
    assert result["dispatch"]["artifact_kind"] == "adr"
    assert result["matched_rows"] == ["D1"]


def test_dispatch_task_summary_at_max_length_passes(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    """Boundary: task_summary at exactly DISPATCH_TASK_SUMMARY_MAX_CHARS."""
    summary = "x" * sc.DISPATCH_TASK_SUMMARY_MAX_CHARS
    monkeypatch.setattr(
        sc.urllib.request,
        "urlopen",
        lambda req, timeout: _make_response(_dispatch_body(task_summary=summary)),
    )
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "dispatch"
    assert len(result["dispatch"]["task_summary"]) == sc.DISPATCH_TASK_SUMMARY_MAX_CHARS


def test_dispatch_task_summary_over_max_falls_to_pause(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    """Boundary fail: > DISPATCH_TASK_SUMMARY_MAX_CHARS → first parse fails →
    retry returns same body → unparseable → pause (fail-closed).
    """
    summary = "x" * (sc.DISPATCH_TASK_SUMMARY_MAX_CHARS + 1)
    monkeypatch.setattr(
        sc.urllib.request,
        "urlopen",
        lambda req, timeout: _make_response(_dispatch_body(task_summary=summary)),
    )
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"


def test_pause_when_dispatch_field_missing(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    """Fail-closed: decision=dispatch but no dispatch field → pause."""
    body = _dispatch_body(include_dispatch_field=False)
    monkeypatch.setattr(sc.urllib.request, "urlopen", lambda req, timeout: _make_response(body))
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"


def test_pause_when_dispatch_subagent_not_allowed(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    """Fail-closed: subagent != plan-drafter → pause (explore-research
    auto-handoff is NOT in scope for Step 5c-1; main agent routes manually
    per Step 4 §1 R2/R5).
    """
    monkeypatch.setattr(
        sc.urllib.request,
        "urlopen",
        lambda req, timeout: _make_response(_dispatch_body(subagent="explore-research")),
    )
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"


def test_pause_when_dispatch_subagent_unknown(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    """Fail-closed: subagent is a hallucinated name → pause."""
    monkeypatch.setattr(
        sc.urllib.request,
        "urlopen",
        lambda req, timeout: _make_response(_dispatch_body(subagent="random-agent")),
    )
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"


def test_pause_when_dispatch_artifact_kind_invalid(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    """Fail-closed: artifact_kind outside {adr, plan} → pause."""
    monkeypatch.setattr(
        sc.urllib.request,
        "urlopen",
        lambda req, timeout: _make_response(_dispatch_body(artifact_kind="lesson")),
    )
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"


def test_pause_when_dispatch_task_summary_empty(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    """Fail-closed: empty task_summary → pause."""
    monkeypatch.setattr(
        sc.urllib.request,
        "urlopen",
        lambda req, timeout: _make_response(_dispatch_body(task_summary="")),
    )
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"


def test_pause_when_dispatch_task_summary_whitespace_only(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    monkeypatch.setattr(
        sc.urllib.request,
        "urlopen",
        lambda req, timeout: _make_response(_dispatch_body(task_summary="   \t\n  ")),
    )
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"


def test_pause_when_dispatch_field_not_an_object(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    """Fail-closed: dispatch field is a string instead of an object → pause."""
    body = json.dumps(
        {
            "decision": "dispatch",
            "matched_rows": ["D1"],
            "reason": "x",
            "dispatch": "not an object",
        }
    )
    monkeypatch.setattr(sc.urllib.request, "urlopen", lambda req, timeout: _make_response(body))
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"


def test_pause_when_dispatch_subagent_not_a_string(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    body = json.dumps(
        {
            "decision": "dispatch",
            "matched_rows": ["D1"],
            "reason": "x",
            "dispatch": {
                "subagent": 42,
                "artifact_kind": "adr",
                "task_summary": "draft",
            },
        }
    )
    monkeypatch.setattr(sc.urllib.request, "urlopen", lambda req, timeout: _make_response(body))
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "pause"


def test_proceed_with_extra_dispatch_field_ignored(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    """Adversarial: classifier emits a dispatch field with decision=proceed.
    The dispatch field is silently ignored (NOT validated) — decision=proceed
    flows normally. Forgiving design: only validate dispatch metadata when
    decision == dispatch.
    """
    body = json.dumps(
        {
            "decision": "proceed",
            "matched_rows": [],
            "reason": "tests pass",
            "dispatch": {"subagent": "bogus", "artifact_kind": "x", "task_summary": ""},
        }
    )
    monkeypatch.setattr(sc.urllib.request, "urlopen", lambda req, timeout: _make_response(body))
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "proceed"
    assert "dispatch" not in result  # not surfaced for proceed/pause


def test_dispatch_extracts_from_markdown_fence(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    """Adversarial: model wraps dispatch JSON in ```json fences."""
    inner = _dispatch_body()
    body = f"Here is the dispatch decision:\n\n```json\n{inner}\n```\n\nDone."
    monkeypatch.setattr(sc.urllib.request, "urlopen", lambda req, timeout: _make_response(body))
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "dispatch"
    assert result["dispatch"]["subagent"] == "plan-drafter"


def test_dispatch_task_summary_stripped(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    """task_summary leading/trailing whitespace is stripped on validation."""
    monkeypatch.setattr(
        sc.urllib.request,
        "urlopen",
        lambda req, timeout: _make_response(
            _dispatch_body(task_summary="   Draft ADR-0015 for X   \n")
        ),
    )
    result = sc.classify({"event": "Stop"})
    assert result["decision"] == "dispatch"
    assert result["dispatch"]["task_summary"] == "Draft ADR-0015 for X"


def test_dispatch_retry_succeeds_after_first_malformed(
    monkeypatch: pytest.MonkeyPatch, fake_registry: Path, with_api_key: None
) -> None:
    """First response has invalid dispatch metadata → retry → valid → dispatch."""
    call_count = {"n": 0}

    def fake_urlopen(req: Any, timeout: int) -> Any:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _make_response(_dispatch_body(artifact_kind="invalid"))
        return _make_response(_dispatch_body())

    monkeypatch.setattr(sc.urllib.request, "urlopen", fake_urlopen)
    result = sc.classify({"event": "Stop"})
    assert call_count["n"] == 2
    assert result["decision"] == "dispatch"


# --- Decision contract sanity ---


def test_decision_dispatch_constant_exposed() -> None:
    """Constant available for import (tests + hook code rely on it)."""
    assert sc.DECISION_DISPATCH == "dispatch"
    assert sc.DECISION_DISPATCH in sc._VALID_DECISIONS
    assert sc.DECISION_PROCEED in sc._VALID_DECISIONS
    assert sc.DECISION_PAUSE in sc._VALID_DECISIONS


def test_dispatch_allowed_subagents_locked_to_plan_drafter() -> None:
    """Step 5c-1 scope: only plan-drafter. Adding new types is a deliberate
    contract extension (this test guards against accidental loosening).
    """
    assert sc.DISPATCH_ALLOWED_SUBAGENTS == frozenset({"plan-drafter"})


def test_dispatch_allowed_artifact_kinds_locked() -> None:
    assert sc.DISPATCH_ALLOWED_ARTIFACT_KINDS == frozenset({"adr", "plan"})


# --- PLAN-0011 / Lesson #15: transcript summarizer + _build_user_message excerpt ---


def _write_jsonl(path: Path, events: list[dict[str, Any]]) -> Path:
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    return path


def _user_event(text: str) -> dict[str, Any]:
    return {"type": "user", "message": {"role": "user", "content": text}}


def _assistant_text_event(text: str) -> dict[str, Any]:
    return {
        "type": "assistant",
        "message": {"role": "assistant", "content": [{"type": "text", "text": text}]},
    }


def _assistant_tool_use_event(name: str, inp: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "content": [{"type": "tool_use", "name": name, "input": inp}],
        },
    }


def test_summarize_transcript_missing_path() -> None:
    assert sc._summarize_transcript(None) == sc.TRANSCRIPT_UNAVAILABLE
    assert sc._summarize_transcript("") == sc.TRANSCRIPT_UNAVAILABLE


def test_summarize_transcript_nonexistent_path(tmp_path: Path) -> None:
    bogus = tmp_path / "does-not-exist.jsonl"
    assert sc._summarize_transcript(str(bogus)) == sc.TRANSCRIPT_UNAVAILABLE


def test_summarize_transcript_valid_fixture(tmp_path: Path) -> None:
    path = _write_jsonl(
        tmp_path / "t.jsonl",
        [
            {"type": "permission-mode", "sessionId": "x"},  # skipped
            _user_event("Please draft ADR-0099 about widget routing."),
            _assistant_text_event("On it. I'll start the draft now."),
            _assistant_tool_use_event("Read", {"file_path": "/foo/bar.md"}),
            {  # tool_result is referenced but body omitted
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [
                        {"type": "tool_result", "tool_use_id": "x", "content": "huge..."},
                    ],
                },
            },
            _assistant_text_event("Found the file. Drafting ADR-0099 now."),
        ],
    )
    excerpt = sc._summarize_transcript(str(path))
    assert "Please draft ADR-0099 about widget routing." in excerpt
    assert "I'll start the draft now." in excerpt
    assert "[tool: Read(" in excerpt
    assert "/foo/bar.md" in excerpt
    assert "[tool_result (omitted)]" in excerpt
    assert "huge..." not in excerpt  # full tool output must NOT leak in


def test_summarize_transcript_skips_thinking_blocks(tmp_path: Path) -> None:
    """``thinking`` blocks are private chain-of-thought; never surface them."""
    path = _write_jsonl(
        tmp_path / "t.jsonl",
        [
            _user_event("Question?"),
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "thinking", "thinking": "private deliberation"},
                        {"type": "text", "text": "Public answer."},
                    ],
                },
            },
        ],
    )
    excerpt = sc._summarize_transcript(str(path))
    assert "private deliberation" not in excerpt
    assert "Public answer." in excerpt


def test_summarize_transcript_skips_meta_event_types(tmp_path: Path) -> None:
    """``file-history-snapshot``, ``attachment``, ``ai-title`` etc. are noise."""
    path = _write_jsonl(
        tmp_path / "t.jsonl",
        [
            {"type": "file-history-snapshot", "messageId": "abc"},
            {"type": "attachment", "attachment": {"path": "/foo"}},
            {"type": "ai-title", "aiTitle": "session title"},
            _user_event("only this should appear"),
        ],
    )
    excerpt = sc._summarize_transcript(str(path))
    assert "only this should appear" in excerpt
    assert "file-history-snapshot" not in excerpt
    assert "session title" not in excerpt


def test_summarize_transcript_budget_cap(tmp_path: Path) -> None:
    long_chunk = "x" * 500
    events = [_user_event(f"turn {i}: {long_chunk}") for i in range(50)]
    path = _write_jsonl(tmp_path / "t.jsonl", events)
    excerpt = sc._summarize_transcript(str(path), max_turns=50, max_bytes=1024)
    assert excerpt.startswith(sc.TRANSCRIPT_ELIDED_PREFIX)
    # Allow some slack: prefix + truncation margin
    assert len(excerpt.encode("utf-8")) <= 1024 + len(sc.TRANSCRIPT_ELIDED_PREFIX) + 8


def test_summarize_transcript_malformed_lines(tmp_path: Path) -> None:
    path = tmp_path / "t.jsonl"
    valid_user = json.dumps(_user_event("valid turn"))
    valid_asst = json.dumps(_assistant_text_event("also valid"))
    path.write_text(
        "\n".join(
            [
                "{ this is not json",
                valid_user,
                "{{ also broken",
                valid_asst,
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    excerpt = sc._summarize_transcript(str(path))
    assert "valid turn" in excerpt
    assert "also valid" in excerpt
    # Malformed input must not poison the output
    assert "this is not json" not in excerpt


def test_summarize_transcript_max_turns_keeps_last_n(tmp_path: Path) -> None:
    events = [_user_event(f"turn-{i}") for i in range(10)]
    path = _write_jsonl(tmp_path / "t.jsonl", events)
    excerpt = sc._summarize_transcript(str(path), max_turns=3, max_bytes=8192)
    assert "turn-9" in excerpt
    assert "turn-8" in excerpt
    assert "turn-7" in excerpt
    assert "turn-6" not in excerpt
    assert "turn-0" not in excerpt


def test_summarize_transcript_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.jsonl"
    path.write_text("", encoding="utf-8")
    assert sc._summarize_transcript(str(path)) == sc.TRANSCRIPT_UNAVAILABLE


def test_summarize_transcript_only_meta_events(tmp_path: Path) -> None:
    path = _write_jsonl(
        tmp_path / "t.jsonl",
        [
            {"type": "permission-mode", "sessionId": "x"},
            {"type": "file-history-snapshot", "messageId": "y"},
        ],
    )
    # No user/assistant events → unavailable, not unreadable.
    assert sc._summarize_transcript(str(path)) == sc.TRANSCRIPT_UNAVAILABLE


def test_summarize_transcript_per_turn_cap(tmp_path: Path) -> None:
    big = "z" * 5000
    path = _write_jsonl(tmp_path / "t.jsonl", [_user_event(big)])
    excerpt = sc._summarize_transcript(str(path), max_bytes=8192)
    # Per-turn cap should clip well before max_bytes kicks in.
    assert len(excerpt) <= sc.TRANSCRIPT_PER_TURN_CHAR_CAP + 32
    assert excerpt.endswith("...")


def test_build_user_message_stop_includes_excerpt(tmp_path: Path) -> None:
    """AC-1: Stop payload with valid transcript_path → user message
    contains both the conversation excerpt AND the raw payload dump."""
    path = _write_jsonl(
        tmp_path / "t.jsonl",
        [
            _user_event("CRAY-FIXTURE-USER-TEXT please draft ADR"),
            _assistant_text_event("CRAY-FIXTURE-ASSISTANT-ACK on it now"),
        ],
    )
    payload = {
        "hook_event_name": "Stop",
        "transcript_path": str(path),
        "session_id": "abc-123",
    }
    msg = sc._build_user_message(payload)
    assert "## Recent conversation excerpt" in msg
    assert "CRAY-FIXTURE-USER-TEXT" in msg
    assert "CRAY-FIXTURE-ASSISTANT-ACK" in msg
    assert "## Raw payload" in msg
    assert '"hook_event_name": "Stop"' in msg
    assert '"session_id": "abc-123"' in msg


def test_build_user_message_pretooluse_preserves_tool_payload() -> None:
    """AC-2: PreToolUse payload (no transcript_path) — excerpt section
    shows ``(no transcript available)``, JSON dump still contains
    tool_name + tool_input semantic content (regression guard)."""
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Edit",
        "tool_input": {
            "file_path": "/repo/docs/adr/0001-accepted.md",
            "old_string": "Status: Accepted",
            "new_string": "Status: Proposed",
        },
    }
    msg = sc._build_user_message(payload)
    assert "## Recent conversation excerpt" in msg
    assert sc.TRANSCRIPT_UNAVAILABLE in msg
    assert "## Raw payload" in msg
    assert '"tool_name": "Edit"' in msg
    assert "0001-accepted.md" in msg
    assert "Status: Accepted" in msg


def test_build_user_message_stop_missing_transcript_path() -> None:
    """Stop event without transcript_path key still renders safely."""
    msg = sc._build_user_message({"hook_event_name": "Stop"})
    assert sc.TRANSCRIPT_UNAVAILABLE in msg
    assert "## Recent conversation excerpt" in msg


def test_build_user_message_stop_unreadable_transcript(tmp_path: Path) -> None:
    """Bad transcript path doesn't blow up _build_user_message."""
    msg = sc._build_user_message(
        {
            "hook_event_name": "Stop",
            "transcript_path": str(tmp_path / "nope.jsonl"),
        }
    )
    # Missing file → UNAVAILABLE (not UNREADABLE — UNREADABLE is for IO errors)
    assert sc.TRANSCRIPT_UNAVAILABLE in msg


# --- Live opt-in (skipped in CI, per OQ-G) ---


@pytest.mark.skipif(
    os.environ.get("RUN_LIVE_SONNET_TESTS") != "1",
    reason="live API call; set RUN_LIVE_SONNET_TESTS=1 to enable (OQ-G)",
)
def test_live_classifier_smoke() -> None:
    """Minimal live API call. Asserts only the JSON contract — not the
    semantic decision, since Sonnet's judgment is non-deterministic.
    """
    # Uses the real registry path + real $ANTHROPIC_API_KEY.
    payload = {"event": "Stop", "test_marker": "live-smoke"}
    result = sc.classify(payload)
    assert result["decision"] in ("proceed", "pause")
    assert isinstance(result["matched_rows"], list)
    assert isinstance(result["reason"], str)


# --- PLAN-0122 Step 2: the Stop-event prompt swap (AC-4, AC-5, AC-6) ---------
#
# Every test below reads the SHIPPED constant, never a copy declared here: a
# guard that asserts against its own constant is vacuous by construction. The
# subject is `sc.STOP_SYSTEM_PROMPT` as the interpreter built it.

_SLIM5_ARTIFACT = (
    Path(__file__).resolve().parents[2]
    / "benchmarks"
    / "stop_classifier"
    / "s280"
    / "SLIM5-PROMPT.txt"
)
_REGISTRY_ARTIFACT = Path(__file__).resolve().parents[2] / ".claude" / "autonomy-triggers.md"


def test_stop_prompt_is_the_measured_slim5(capsys: pytest.CaptureFixture[str]) -> None:
    """AC-4 — what ships on Stop is byte-identical to what was measured.

    SD-1 (a) and SD-7 (a) both turn on this: the 42/49 was measured against
    these exact bytes, so any drift silently trades a known number for an
    unknown one. The hash is the only assertion that can see a one-byte edit.
    Registry-independence is asserted separately because SLIM5 carries an
    inline row list — if the builder ever appended the registry again, the
    prompt would still contain every pinned sentence and only this would catch
    it.
    """
    measured = _SLIM5_ARTIFACT.read_text(encoding="utf-8")
    over_a = sc._build_system_prompt("REGISTRY-A", event="Stop")
    over_b = sc._build_system_prompt("REGISTRY-B" * 200, event="Stop")

    sha_live = hashlib.sha256(over_a.encode("utf-8")).hexdigest()
    sha_measured = hashlib.sha256(measured.encode("utf-8")).hexdigest()
    print(
        f"sha_live={sha_live} sha_measured={sha_measured} "
        f"chars={len(over_a)} registry_independent={over_a == over_b}"
    )

    # A1 — the registry argument changes nothing on the Stop arm.
    assert over_a == over_b
    # A2 — and those bytes are the measured ones.
    assert sha_live == sha_measured
    # A3 — the strict retry variant is base + the existing suffix, nothing else.
    strict = sc._build_system_prompt("REGISTRY-A", strict=True, event="Stop")
    assert strict == over_a + sc._STRICT_JSON_SUFFIX


def test_slim5_pins_the_not_forbidden_carveouts() -> None:
    """AC-5 (i) — the carve-outs that stop STEP 1 over-firing.

    Four of the s280 ledger's defective proceeds were the inverse: the arm
    cited a G/C row against an action the row does not cover. These sentences
    are what a one-sided rule was missing — a rule needs when it fires, when it
    must NOT fire, and what wins on conflict.
    """
    prompt = sc.STOP_SYSTEM_PROMPT
    assert "THESE ARE NOT FORBIDDEN. Do not cite a row against them:" in prompt
    assert "`git commit`, and `git push` of a FEATURE branch" in prompt
    assert "opening a PR with `gh pr create`." in prompt
    assert "printing or asserting on a DIAGNOSTIC MARKER string" in prompt


def test_slim5_pins_the_c6_waiver_exception() -> None:
    """AC-5 (ii) — the conflict clause, and its one exception.

    "An explicit Cray go means the row does not fire" is the conflict rule;
    C6 (a credential into a file) is the single row no go waives. Dropping the
    exception would let an in-excerpt "go" wave a credential through.
    """
    prompt = sc.STOP_SYSTEM_PROMPT
    assert "except C6, which no go waives" in prompt


def test_slim5_pins_the_reason_rules() -> None:
    """AC-5 (iii) — the four REASON RULES.

    These exist because ``stop_continuation._proceed_block`` passes ``reason``
    to the agent VERBATIM as its next instruction. Specimen #124 of the s280
    ledger fabricated Cray's authorization in a reason while a question was
    pending; rules 1-3 are what that violates, and rule 4 is the one that keeps
    the arm from answering a permission question it was never asked.
    """
    prompt = sc.STOP_SYSTEM_PROMPT
    assert "Decision and reason MUST agree" in prompt
    assert "APPEARS IN THE EXCERPT" in prompt
    assert "Never write in the first person" in prompt
    assert "This is a hook event, not a permission request" in prompt


def test_slim5_pins_the_last_turn_governs_step() -> None:
    """AC-5 (iv) — STEP 2 and, just as load-bearing, when it must NOT fire.

    The rule alone made the arm pause on every ordinary working turn, because
    a turn that reports finished work and then names the next step looks like a
    stop. Both halves are pinned: a copy of this prompt carrying only the first
    sentence is the failure this test exists to catch.
    """
    prompt = sc.STOP_SYSTEM_PROMPT
    assert "STEP 2 - THE LAST TURN GOVERNS" in prompt
    assert "THIS STEP DOES NOT FIRE on an ordinary working turn" in prompt


def test_slim5_pins_the_pause_bias() -> None:
    """AC-5 (v) — the tie-break, which is the whole safety argument.

    AC-3 measured always-proceed at 27 unsafe verdicts against SLIM5's zero.
    The bias sentence is why the arm lands on the safe side of a tie.
    """
    prompt = sc.STOP_SYSTEM_PROMPT
    assert "Default to PAUSE" in prompt
    assert "A spurious pause is cheaper than a spurious proceed" in prompt


def test_slim5_pins_the_dispatch_metadata_shape() -> None:
    """AC-5 (vi) — the dispatch envelope the consumer actually parses.

    ``_validate_dispatch_metadata`` requires all three fields and only accepts
    ``plan-drafter``; a prompt that stopped describing them would fail closed to
    pause and silence the suggestion channel without any error.
    """
    prompt = sc.STOP_SYSTEM_PROMPT
    assert '"subagent": "plan-drafter"' in prompt
    assert '"artifact_kind": "adr" or "plan"' in prompt
    assert '`subagent` is always the literal string "plan-drafter"' in prompt


def test_every_registry_gch_row_is_in_the_stop_prompt(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """AC-6 — the registry↔prompt drift guard (SD-7 (a)).

    SLIM5 stops embedding ``.claude/autonomy-triggers.md`` and carries an
    inline row list instead, so the two can now disagree silently. This reads
    BOTH artifacts — neither is a constant declared here — and fails when a
    registry row has no prompt line.

    ``C6`` and ``C7`` are prompt-only by ruling: SD-7 (a) ships the inline rows
    byte-identical and records that giving them real registry rows is a
    follow-up with its own blast radius. Pinning the exact prompt-only set is
    what keeps that debt visible instead of letting it become permanent.
    """
    registry = _REGISTRY_ARTIFACT.read_text(encoding="utf-8")
    prompt = sc.STOP_SYSTEM_PROMPT

    registry_rows = sorted(set(re.findall(r"^\| *([GCH]\d+) *\|", registry, re.M)))
    prompt_rows = sorted(set(re.findall(r"^\s+([GCH]\d+) - ", prompt, re.M)))
    missing = sorted(set(registry_rows) - set(prompt_rows))
    prompt_only = sorted(set(prompt_rows) - set(registry_rows))
    in_prompt = len(set(registry_rows) & set(prompt_rows))
    print(f"registry_rows={len(registry_rows)} in_prompt={in_prompt} prompt_only={prompt_only}")

    # The parser must actually find rows, or both assertions below are vacuous:
    # an empty registry satisfies "every row is in the prompt" for free.
    assert registry_rows, "registry parser found no G/C/H rows - instrument broken"
    assert prompt_rows, "prompt parser found no G/C/H rows - instrument broken"
    # A1 — no registry row has gone missing from the prompt.
    assert missing == []
    # A2 — and the prompt-only set is exactly the two SD-7 recorded.
    assert prompt_only == ["C6", "C7"]


# ---------------------------------------------------------------------------
# PLAN-0122 §4.3 — `transport`, `latency_s`, `prompt_sha8` on every verdict.
#
# The log in stop_continuation only COPIES these; whether the values are right
# is decided here, in _run_with_retry. `transport` is not a failure flag: it
# says how the call went, and `retry` means the model DID answer, second try.
# ---------------------------------------------------------------------------


_GOOD_BODY = '{"decision": "pause", "matched_rows": [], "reason": "needs Cray"}'


def _drive(monkeypatch: pytest.MonkeyPatch, *responses: object) -> dict[str, Any]:
    """Run _run_with_retry over a scripted transport.

    Each element is either a string (returned) or an exception (raised), one
    per attempt, in order.
    """
    calls = {"n": 0}

    def _transport(*, strict: bool) -> str:
        item = responses[calls["n"]]
        calls["n"] += 1
        if isinstance(item, BaseException):
            raise item
        return str(item)

    return sc._run_with_retry(_transport)


def test_a_first_attempt_that_parses_is_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    result = _drive(monkeypatch, _GOOD_BODY)
    print(f"transport={result.get('transport')}")
    assert result["transport"] == "ok"


def test_an_answer_that_needed_the_retry_is_retry_not_ok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The distinction §4.3 asks for: answered, but not first time.

    Under a naive implementation that sets `ok` on any successful parse, this
    is the only case that reddens.
    """
    result = _drive(monkeypatch, "not json at all", _GOOD_BODY)
    print(f"transport={result.get('transport')}")
    assert result["decision"] == "pause"
    assert result["transport"] == "retry"


def test_an_unreachable_server_is_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every attempt fails, so the verdict is the LAST failure's label.

    Scripted CLASSIFIER_MAX_ATTEMPTS deep: since s290 a transport failure is
    retried, so a one-deep script would exhaust the list rather than exercise
    the fail-closed path.
    """
    result = _drive(
        monkeypatch,
        *[urllib.error.URLError("timed out")] * sc.CLASSIFIER_MAX_ATTEMPTS,
    )
    print(f"transport={result.get('transport')} reason={result.get('reason')!r}")
    assert result["transport"] == "timeout"


def test_an_http_500_is_http_error_not_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """The §4.3 amendment (s290). This test previously pinned the OPPOSITE.

    It asserted `transport == "timeout"` and its docstring argued no information
    was lost, because `reason` carried the distinguishing text. Both were true.
    Neither helped: s289 tallied the log BY THIS FIELD, read `timeout 50.0%`, and
    concluded the blocker was elapsed time. The 62 500s were the largest single
    cause and were invisible in that aggregate. The name is changed with the
    assertion on purpose — a test called `..._lands_in_timeout` that asserts
    `http_error` is the same lossy label one level up.
    """
    exc = urllib.error.HTTPError(
        url="http://x/api/chat", code=500, msg="Internal Server Error", hdrs=None, fp=None
    )
    result = _drive(monkeypatch, *[exc] * sc.CLASSIFIER_MAX_ATTEMPTS)
    print(f"transport={result.get('transport')} reason={result.get('reason')!r}")
    assert result["transport"] == "http_error"
    assert "500" in result["reason"]


def test_an_http_error_and_a_socket_timeout_do_not_share_a_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The whole point of the amendment, asserted as a DIFFERENCE.

    Checking each label alone would pass under a mutation that made both values
    identical; only comparing them can redden that. `HTTPError` subclasses
    `URLError`, so the two arms are one `except` away from re-merging.
    """
    http = urllib.error.HTTPError(
        url="http://x/api/chat", code=500, msg="Internal Server Error", hdrs=None, fp=None
    )
    refused = _drive(monkeypatch, *[http] * sc.CLASSIFIER_MAX_ATTEMPTS)
    silent = _drive(monkeypatch, *[urllib.error.URLError("timed out")] * sc.CLASSIFIER_MAX_ATTEMPTS)
    print(f"answered-with-error={refused['transport']!r}  never-answered={silent['transport']!r}")
    assert refused["transport"] != silent["transport"]
    assert {refused["transport"], silent["transport"]} == {"http_error", "timeout"}


def test_an_unparseable_body_is_malformed_after_the_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _drive(monkeypatch, *["junk"] * sc.CLASSIFIER_MAX_ATTEMPTS)
    print(f"transport={result.get('transport')}")
    assert result["transport"] == "malformed"


def test_a_pause_built_before_any_request_is_not_attempted() -> None:
    """The fifth value, and why it is not `timeout`.

    A registry that is missing means nothing ever left the box. Labelling that
    a network event would put a fabricated cause into the file AC-12 reads.
    """
    result = sc._pause("autonomy registry missing or empty")
    print(f"transport={result.get('transport')}")
    assert result["transport"] == "not_attempted"


# ---------------------------------------------------------------------------
# s290 — the transport repair. The shipped code retried an UNPARSEABLE body but
# surrendered on the first `URLError`, so 62 HTTP 500s and 74 empty-`content`
# 200s each cost a Stop verdict on one try. Root cause is server-side and
# stochastic (gpt-oss emits harmony tool calls for undeclared tools; Ollama's
# parser then fails ~half as 500 and ~half as an empty 200), so re-asking is
# the repair. Budget = 3 attempts, Cray's typed call.
# ---------------------------------------------------------------------------


def test_a_transport_failure_is_retried_not_surrendered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """THE s290 regression test: two 500s then an answer must still answer.

    Under the shipped code this reddens — the first `URLError` returned a pause
    immediately and the good third body was never requested.
    """
    exc = urllib.error.HTTPError(
        url="http://x/api/chat", code=500, msg="Internal Server Error", hdrs=None, fp=None
    )
    result = _drive(monkeypatch, exc, exc, _GOOD_BODY)
    print(f"transport={result.get('transport')} decision={result.get('decision')}")
    assert result["decision"] == "pause"  # from _GOOD_BODY, not manufactured
    assert result["transport"] == "retry"
    assert result["reason"] == "needs Cray"  # the MODEL's reason, not a failure string


def test_a_socket_timeout_is_also_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    """The third arm. After s290 split HTTP errors out of `timeout`, the
    URLError arm is a separate `except` with its own `continue`, so its retry
    can be lost independently of the HTTP one and needs its own witness.
    """
    exc = urllib.error.URLError("timed out")
    result = _drive(monkeypatch, exc, exc, _GOOD_BODY)
    print(f"transport={result.get('transport')} reason={result.get('reason')!r}")
    assert result["transport"] == "retry"


def test_an_empty_ollama_envelope_is_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    """The 74-record bucket: `_call_ollama` raises ValueError on empty content.

    Separate probe from the 500 case above because the two take different
    `except` arms, and one mutation can only witness one of them.
    """
    empty = ValueError("Ollama envelope missing message.content")
    result = _drive(monkeypatch, empty, empty, _GOOD_BODY)
    print(f"transport={result.get('transport')} reason={result.get('reason')!r}")
    assert result["transport"] == "retry"
    assert result["reason"] == "needs Cray"


def test_the_attempt_budget_is_exactly_three() -> None:
    """Pin the count itself — a silent drift to 2 or 10 changes how long a Stop
    hook blocks Cray's turn, which is the thing he actually chose.
    """
    calls = {"n": 0}

    def _transport(*, strict: bool) -> str:
        calls["n"] += 1
        raise urllib.error.URLError("timed out")

    result = sc._run_with_retry(_transport)
    print(f"attempts={calls['n']} transport={result.get('transport')}")
    assert sc.CLASSIFIER_MAX_ATTEMPTS == 3
    assert calls["n"] == 3
    assert result["transport"] == "timeout"


def test_only_the_first_attempt_uses_the_normal_prompt() -> None:
    """Retries must use the STRICT prompt — the original single retry did, and
    that behaviour is why a retry can succeed where the first attempt failed.
    """
    seen: list[bool] = []

    def _transport(*, strict: bool) -> str:
        seen.append(strict)
        if len(seen) < 3:
            raise urllib.error.URLError("timed out")
        return _GOOD_BODY

    sc._run_with_retry(_transport)
    print(f"strict flags per attempt = {seen}")
    assert seen == [False, True, True]


def test_an_http_error_body_is_kept_in_the_reason() -> None:
    """`str(HTTPError)` drops the body, which is where Ollama says what broke.

    Positive control: the same reader is fed a body it MUST surface, so a later
    regression that silently stops reading cannot pass as "no body present".
    """
    import io

    body = b'{"error":"harmony parser: no reverse mapping for python"}'
    exc = urllib.error.HTTPError(
        url="http://x/api/chat",
        code=500,
        msg="Internal Server Error",
        hdrs=None,  # type: ignore[arg-type]
        fp=io.BytesIO(body),
    )
    detail = sc._http_error_detail(exc)
    print(f"detail={detail!r}")
    assert "500" in detail
    assert "harmony parser" in detail

    # and the no-body case must degrade to the bare string, not crash
    bare = urllib.error.HTTPError(
        url="http://x/api/chat", code=500, msg="Internal Server Error", hdrs=None, fp=None
    )
    detail_bare = sc._http_error_detail(bare)
    print(f"detail_bare={detail_bare!r}")
    assert "500" in detail_bare
