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
