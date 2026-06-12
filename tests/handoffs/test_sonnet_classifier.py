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

import io
import json
import os
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
    assert "REGISTRY START" in body["messages"][0]["content"]


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
    silently regresses out of the prompt."""
    prompt = sc._build_system_prompt("registry text here")
    assert "CONCRETE remaining work" in prompt
    assert "Decision and reason" in prompt and "AGREE" in prompt
    assert "NATURAL stop" in prompt
    # The conservative bias stays intact alongside the new rule.
    assert "spurious pauses are preferred over spurious proceeds" in prompt


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
