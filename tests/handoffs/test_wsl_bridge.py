"""Tests for .claude/hooks/_wsl_bridge.py — the rule-of-three extraction shared
by notification_telegram, subagentstop_notify, and _sonnet_classifier.

Covers:

* Pattern A — POSIX bash script invocation: ``is_windows_with_wsl``,
  ``wsl_path``, ``env_with_wslenv_passthrough``, ``bash_argv``.
* Pattern B — outbound HTTPS POST via WSL Python: ``should_use_wsl_https_bridge``,
  ``http_post_via_wsl_bridge``.

The Pattern-B HTTPS bridge is exercised end-to-end via a fake ``subprocess.run``
that returns canned JSON responses, mirroring what ``wsl.exe --exec python3``
would emit. No real subprocess + no real network.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import urllib.error
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / ".claude" / "hooks" / "_wsl_bridge.py"


def _load_bridge() -> Any:
    """Load _wsl_bridge.py as a module without polluting sys.modules."""
    spec = importlib.util.spec_from_file_location("_wsl_bridge_under_test", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- Pattern A: bash script invocation --------------------------------------


def test_is_windows_with_wsl_returns_false_on_linux(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.platform", "linux")
    bridge = _load_bridge()
    assert bridge.is_windows_with_wsl() is False


def test_is_windows_with_wsl_returns_false_when_wsl_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.platform", "win32")
    bridge = _load_bridge()
    monkeypatch.setattr(bridge.shutil, "which", lambda _name: None)
    assert bridge.is_windows_with_wsl() is False


def test_is_windows_with_wsl_returns_true_on_windows_with_wsl(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.platform", "win32")
    bridge = _load_bridge()
    monkeypatch.setattr(bridge.shutil, "which", lambda _name: "C:/Windows/System32/wsl.exe")
    assert bridge.is_windows_with_wsl() is True


def test_wsl_path_translates_unc() -> None:
    bridge = _load_bridge()
    unc = Path(r"\\wsl.localhost\ubuntu-24.04\home\crayj\work\vero-lite")
    assert bridge.wsl_path(unc) == "/home/crayj/work/vero-lite"


def test_wsl_path_translates_wsl_dollar_unc() -> None:
    bridge = _load_bridge()
    unc = r"\\wsl$\ubuntu-24.04\home\crayj\foo"
    # \\wsl$ — the index search hits ``wsl$`` (lowercased match), so the
    # distro segment is parts[idx+1] and the leading slash precedes whatever
    # comes after the distro. parts == ['', '', 'wsl$', 'ubuntu-24.04', 'home', 'crayj', 'foo']
    # idx = 2 (the 'wsl$' segment), so result = '/' + 'ubuntu-24.04/home/crayj/foo'
    assert bridge.wsl_path(unc) == "/ubuntu-24.04/home/crayj/foo"


def test_wsl_path_passes_through_posix() -> None:
    bridge = _load_bridge()
    assert bridge.wsl_path(Path("/home/crayj/work/vero-lite")) == "/home/crayj/work/vero-lite"


def test_wsl_path_non_wsl_windows_path_falls_back_to_slash_conversion() -> None:
    bridge = _load_bridge()
    # A plain Windows path (not under \\wsl.localhost) — backslash converted
    # to forward slash, no semantic translation (best-effort fallback).
    assert bridge.wsl_path(r"C:\Users\crayj\foo") == "C:/Users/crayj/foo"


def test_env_with_wslenv_passthrough_no_op_on_linux(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.platform", "linux")
    bridge = _load_bridge()
    base = {"FOO": "1", "WSLENV": "EXISTING/u"}
    result = bridge.env_with_wslenv_passthrough(("BAR", "BAZ"), base_env=base)
    # base passed through; no WSLENV mutation on Linux.
    assert result["FOO"] == "1"
    assert result["WSLENV"] == "EXISTING/u"


def test_env_with_wslenv_passthrough_adds_keys_on_windows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.platform", "win32")
    bridge = _load_bridge()
    base = {"WSLENV": ""}
    result = bridge.env_with_wslenv_passthrough(("FOO", "BAR"), base_env=base)
    assert result["WSLENV"] == "FOO/u:BAR/u"


def test_env_with_wslenv_passthrough_preserves_existing_and_dedupes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.platform", "win32")
    bridge = _load_bridge()
    base = {"WSLENV": "EXISTING/u"}
    result = bridge.env_with_wslenv_passthrough(("EXISTING", "NEW"), base_env=base)
    # EXISTING is already in WSLENV → not duplicated; NEW gets appended.
    assert result["WSLENV"] == "EXISTING/u:NEW/u"


def test_bash_argv_linux_branch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("sys.platform", "linux")
    bridge = _load_bridge()
    script = tmp_path / "foo.sh"
    cmd = bridge.bash_argv(script, "arg1", "arg2")
    assert cmd == ["bash", str(script), "arg1", "arg2"]


def test_bash_argv_windows_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.platform", "win32")
    bridge = _load_bridge()
    monkeypatch.setattr(bridge.shutil, "which", lambda _name: "C:/Windows/System32/wsl.exe")
    cmd = bridge.bash_argv(
        Path(r"\\wsl.localhost\ubuntu-24.04\home\crayj\work\vero-lite\tools\notify\telegram.sh"),
        "message",
    )
    assert cmd == [
        "wsl.exe",
        "--exec",
        "bash",
        "/home/crayj/work/vero-lite/tools/notify/telegram.sh",
        "message",
    ]


def test_bash_argv_windows_without_wsl_falls_back_to_bash(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("sys.platform", "win32")
    bridge = _load_bridge()
    monkeypatch.setattr(bridge.shutil, "which", lambda _name: None)
    script = tmp_path / "foo.sh"
    cmd = bridge.bash_argv(script, "arg")
    # No wsl.exe → bash_argv falls back to local bash invocation.
    assert cmd == ["bash", str(script), "arg"]


# --- Pattern B: HTTPS bridge -------------------------------------------------


def test_should_use_wsl_https_bridge_false_on_linux(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.delenv("CLAUDE_CLASSIFIER_FORCE_DIRECT", raising=False)
    bridge = _load_bridge()
    assert bridge.should_use_wsl_https_bridge() is False


def test_should_use_wsl_https_bridge_false_when_opt_out_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.platform", "win32")
    bridge = _load_bridge()
    monkeypatch.setattr(bridge.shutil, "which", lambda _name: "C:/wsl.exe")
    monkeypatch.setenv("CLAUDE_CLASSIFIER_FORCE_DIRECT", "1")
    assert bridge.should_use_wsl_https_bridge() is False


def test_should_use_wsl_https_bridge_true_on_windows_no_opt_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.platform", "win32")
    bridge = _load_bridge()
    monkeypatch.setattr(bridge.shutil, "which", lambda _name: "C:/wsl.exe")
    monkeypatch.delenv("CLAUDE_CLASSIFIER_FORCE_DIRECT", raising=False)
    assert bridge.should_use_wsl_https_bridge() is True


def test_should_use_wsl_https_bridge_custom_opt_out_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("sys.platform", "win32")
    bridge = _load_bridge()
    monkeypatch.setattr(bridge.shutil, "which", lambda _name: "C:/wsl.exe")
    monkeypatch.setenv("MY_CUSTOM_OPT_OUT", "yes")
    monkeypatch.delenv("CLAUDE_CLASSIFIER_FORCE_DIRECT", raising=False)
    assert bridge.should_use_wsl_https_bridge(opt_out_env="MY_CUSTOM_OPT_OUT") is False


def _fake_run_returning(stdout: str, returncode: int = 0, stderr: str = "") -> Any:
    """Return a callable matching subprocess.run signature that yields a canned
    CompletedProcess. Used by the Pattern-B tests below."""

    def _run(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=_args[0] if _args else [],
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )

    return _run


def test_http_post_via_wsl_bridge_success(monkeypatch: pytest.MonkeyPatch) -> None:
    bridge = _load_bridge()
    canned = json.dumps({"ok": True, "status": 200, "body": '{"result": "ok"}'})
    monkeypatch.setattr(bridge.subprocess, "run", _fake_run_returning(canned))
    result = bridge.http_post_via_wsl_bridge(
        url="https://api.anthropic.com/v1/messages",
        body=b'{"x":1}',
        headers={"content-type": "application/json"},
        timeout=10,
    )
    assert result == '{"result": "ok"}'


def test_http_post_via_wsl_bridge_http_error_reraises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bridge = _load_bridge()
    canned = json.dumps({"ok": False, "kind": "HTTPError", "status": 429, "body": "rate limited"})
    monkeypatch.setattr(bridge.subprocess, "run", _fake_run_returning(canned))
    with pytest.raises(urllib.error.HTTPError) as exc:
        bridge.http_post_via_wsl_bridge(
            url="https://api.anthropic.com/v1/messages",
            body=b"{}",
            headers={},
            timeout=10,
        )
    assert exc.value.code == 429


def test_http_post_via_wsl_bridge_url_error_on_bridge_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bridge = _load_bridge()
    canned = json.dumps({"ok": False, "kind": "URLError", "reason": "name resolution"})
    monkeypatch.setattr(bridge.subprocess, "run", _fake_run_returning(canned))
    with pytest.raises(urllib.error.URLError) as exc:
        bridge.http_post_via_wsl_bridge(
            url="https://api.anthropic.com/v1/messages",
            body=b"{}",
            headers={},
            timeout=10,
        )
    assert "URLError" in str(exc.value)
    assert "name resolution" in str(exc.value)


def test_http_post_via_wsl_bridge_subprocess_nonzero_rc(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bridge = _load_bridge()
    monkeypatch.setattr(
        bridge.subprocess,
        "run",
        _fake_run_returning(stdout="", returncode=2, stderr="wsl: distro not found"),
    )
    with pytest.raises(urllib.error.URLError) as exc:
        bridge.http_post_via_wsl_bridge(
            url="https://api.anthropic.com/v1/messages",
            body=b"{}",
            headers={},
            timeout=10,
        )
    assert "subprocess failed" in str(exc.value)
    assert "distro not found" in str(exc.value)


def test_http_post_via_wsl_bridge_missing_wsl_exe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bridge = _load_bridge()

    def _raise(*_args: Any, **_kwargs: Any) -> Any:
        raise FileNotFoundError(2, "No such file", "wsl.exe")

    monkeypatch.setattr(bridge.subprocess, "run", _raise)
    with pytest.raises(urllib.error.URLError) as exc:
        bridge.http_post_via_wsl_bridge(
            url="https://api.anthropic.com/v1/messages",
            body=b"{}",
            headers={},
            timeout=10,
        )
    assert "wsl.exe not found" in str(exc.value)


def test_http_post_via_wsl_bridge_subprocess_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bridge = _load_bridge()

    def _raise(*_args: Any, **_kwargs: Any) -> Any:
        raise subprocess.TimeoutExpired(cmd="wsl.exe", timeout=15)

    monkeypatch.setattr(bridge.subprocess, "run", _raise)
    with pytest.raises(urllib.error.URLError) as exc:
        bridge.http_post_via_wsl_bridge(
            url="https://api.anthropic.com/v1/messages",
            body=b"{}",
            headers={},
            timeout=10,
        )
    assert "timed out" in str(exc.value)


def test_http_post_via_wsl_bridge_non_json_stdout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bridge = _load_bridge()
    monkeypatch.setattr(bridge.subprocess, "run", _fake_run_returning(stdout="not valid json"))
    with pytest.raises(urllib.error.URLError) as exc:
        bridge.http_post_via_wsl_bridge(
            url="https://api.anthropic.com/v1/messages",
            body=b"{}",
            headers={},
            timeout=10,
        )
    assert "non-JSON stdout" in str(exc.value)
