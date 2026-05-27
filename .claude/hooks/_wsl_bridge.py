"""Cross-platform WSL bridge helpers for hooks running on Windows.

Rule-of-three extraction (PLAN-0009 deferred follow-up): three hooks
(``notification_telegram``, ``subagentstop_notify``, ``_sonnet_classifier``)
all reach across the Windows-Python → WSL boundary via ``subprocess.run([
"wsl.exe", "--exec", ...])`` for two distinct reasons:

* **Pattern A — POSIX bash script invocation.** A ``tools/notify/telegram.sh``-
  style shell script needs to run, but Claude Code's hook spawn mechanism on
  Windows invokes ``python`` directly (Windows Python). The hook re-shells
  through ``wsl.exe --exec bash`` so ``bash`` is the WSL bash, with the
  script path translated from the Windows UNC mount to the POSIX path the
  WSL filesystem already has. ``WSLENV`` is augmented so chosen env vars
  (``TELEGRAM_BOT_TOKEN``, ``TELEGRAM_CHAT_ID``, etc.) cross the boundary.

* **Pattern B — outbound HTTPS POST.** The Windows Python CA bundle fails
  chain validation against ``api.anthropic.com`` with
  ``SSL: CERTIFICATE_VERIFY_FAILED — Basic Constraints of CA cert not marked
  critical (_ssl.c:1028)`` (Lesson #14 sibling — bug #4 of root-cause family).
  Mitigation: ``wsl.exe --exec python3 -c <inline script>`` re-issues the
  POST under WSL Python whose CA chain works. The bridge contract is
  pure-stdin/stdout JSON; the inline script is constant so there's no
  injection surface.

Why bridge inside Python (vs settings.json ``wsl --exec`` routing — the PR
#48 attempt): Claude Code's hook spawn mechanism on Windows funnels through
``cmd /c``, which doesn't survive UNC ``cwd`` + stdin piping to ``wsl.exe``
(proven by the post-PR-48 smoke regression). Spawning ``wsl.exe`` from
Windows Python via ``subprocess.run`` gives full control over stdin/stdout
byte forwarding.
"""

from __future__ import annotations

import email.message
import json
import os
import shutil
import subprocess
import sys
import urllib.error
from pathlib import Path

__all__ = (
    "is_windows_with_wsl",
    "wsl_path",
    "env_with_wslenv_passthrough",
    "bash_argv",
    "should_use_wsl_https_bridge",
    "http_post_via_wsl_bridge",
)


# --- Pattern A: POSIX bash script invocation ---------------------------------


def is_windows_with_wsl() -> bool:
    """True iff ``sys.platform == "win32"`` AND ``wsl.exe`` is on PATH.

    Single source of truth for the platform gate that wraps every WSL-bridge
    call site. Encapsulates both checks so callers can branch on one boolean
    rather than reproducing the two-condition pattern.
    """
    return sys.platform == "win32" and shutil.which("wsl.exe") is not None


def wsl_path(win_path: Path | str) -> str:
    r"""Translate a Windows path under ``\\wsl.localhost\<distro>\...`` to POSIX.

    Used to convert a Windows-side path to a form the WSL bash inside
    ``wsl.exe --exec`` can resolve directly via the native WSL filesystem
    (the same file is already at ``/home/<user>/...`` inside WSL).

    Pass-through cases:

    * A POSIX path (e.g. ``/home/crayj/...``) is returned unchanged.
    * A Windows path that doesn't start with ``\\wsl.localhost`` or
      ``\\wsl$`` is converted backslash → forward-slash (best-effort —
      it's an unusual case in this codebase and the caller likely
      won't have a working bridge anyway).
    """
    s = str(win_path)
    if not s.lower().startswith("\\\\wsl"):
        return s.replace("\\", "/")
    parts = s.split("\\")
    try:
        idx = next(i for i, p in enumerate(parts) if p.startswith("ubuntu") or p.lower() == "wsl$")
    except StopIteration:
        return s.replace("\\", "/")
    return "/" + "/".join(parts[idx + 1 :])


def env_with_wslenv_passthrough(
    keys: tuple[str, ...],
    base_env: dict[str, str] | None = None,
) -> dict[str, str]:
    """Return a copy of ``base_env`` (default: ``os.environ``) with ``WSLENV``
    augmented to forward the named env vars across the ``wsl.exe`` boundary.

    Each key is added as ``<key>/u`` so WSL converts it to a Unix-style env
    var inside the bridged subprocess. Keys already present in ``WSLENV``
    are not duplicated. No-op on non-Windows hosts (``WSLENV`` is a
    Windows-side mechanism with no Linux equivalent).
    """
    env: dict[str, str] = dict(os.environ) if base_env is None else base_env.copy()
    if sys.platform == "win32":
        wslenv = env.get("WSLENV", "")
        existing = {item.split("/", 1)[0] for item in wslenv.split(":") if item}
        additions = [f"{k}/u" for k in keys if k not in existing]
        if additions:
            env["WSLENV"] = ":".join(filter(None, [wslenv, *additions]))
    return env


def bash_argv(script: Path | str, *args: str) -> list[str]:
    """Return argv to run ``bash <script> <args...>`` portably.

    On Windows with ``wsl.exe`` available::

        ["wsl.exe", "--exec", "bash", wsl_path(script), *args]

    Elsewhere (Linux/macOS or where ``wsl.exe`` is missing)::

        ["bash", str(script), *args]

    Callers can rely on the same argv shape and pass it straight to
    ``subprocess.run``; only the prefix changes. Pair with
    :func:`env_with_wslenv_passthrough` if env vars need to cross the
    boundary.
    """
    if is_windows_with_wsl():
        return ["wsl.exe", "--exec", "bash", wsl_path(script), *args]
    return ["bash", str(script), *args]


# --- Pattern B: outbound HTTPS POST via WSL Python ---------------------------

# Inline python3 script executed by ``wsl.exe --exec python3 -c <this>``.
# Reads a JSON ``{url, body, headers, timeout}`` spec from stdin and writes a
# JSON response to stdout. Constant source — no injection surface.
_WSL_HTTPS_BRIDGE_SCRIPT = r"""
import sys, json, urllib.request, urllib.error
try:
    spec = json.loads(sys.stdin.read())
    req = urllib.request.Request(
        spec["url"],
        data=spec["body"].encode("utf-8"),
        headers=spec["headers"],
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=spec["timeout"]) as resp:
            sys.stdout.write(json.dumps({
                "ok": True,
                "status": resp.status,
                "body": resp.read().decode("utf-8"),
            }))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8")
        except Exception:
            pass
        sys.stdout.write(json.dumps({
            "ok": False, "kind": "HTTPError",
            "status": e.code, "body": body,
        }))
    except urllib.error.URLError as e:
        sys.stdout.write(json.dumps({
            "ok": False, "kind": "URLError",
            "reason": str(e.reason),
        }))
    except TimeoutError as e:
        sys.stdout.write(json.dumps({
            "ok": False, "kind": "TimeoutError",
            "reason": str(e),
        }))
except Exception as e:
    sys.stdout.write(json.dumps({
        "ok": False, "kind": "BridgeError",
        "reason": f"{type(e).__name__}: {e}",
    }))
"""


def should_use_wsl_https_bridge(
    opt_out_env: str = "CLAUDE_CLASSIFIER_FORCE_DIRECT",
) -> bool:
    """True iff :func:`is_windows_with_wsl` AND ``$opt_out_env`` is unset/empty.

    The opt-out env name is parameterized so independent HTTPS callers can
    opt out independently (the classifier uses
    ``CLAUDE_CLASSIFIER_FORCE_DIRECT``; other future callers can pick their
    own flag). The opt-out exists for tests + Linux CI where the direct
    ``urllib`` path already works.
    """
    if os.environ.get(opt_out_env, "").strip():
        return False
    return is_windows_with_wsl()


def http_post_via_wsl_bridge(
    url: str,
    body: bytes,
    headers: dict[str, str],
    timeout: int,
) -> str:
    """Bridge an HTTPS POST through ``wsl.exe python3``; return body text.

    Raises ``urllib.error.URLError`` / ``urllib.error.HTTPError`` on
    failure so callers don't need to know the transport — the same
    exception types a direct ``urllib`` call would surface.
    """
    spec = {
        "url": url,
        "body": body.decode("utf-8"),
        "headers": dict(headers),
        "timeout": timeout,
    }
    spec_json = json.dumps(spec)
    try:
        # S603/S607: wsl.exe is a hook-controlled invocation; argv is
        # constant ``["wsl.exe", "--exec", "python3", "-c", <constant
        # bridge script>]`` — no shell, no user-controlled args.
        result = subprocess.run(  # noqa: S603
            ["wsl.exe", "--exec", "python3", "-c", _WSL_HTTPS_BRIDGE_SCRIPT],  # noqa: S607
            input=spec_json,
            text=True,
            capture_output=True,
            timeout=timeout + 5,
            check=False,
        )
    except FileNotFoundError as exc:
        raise urllib.error.URLError(f"wsl.exe not found: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise urllib.error.URLError(
            f"wsl bridge subprocess timed out after {timeout + 5}s: {exc}"
        ) from exc

    if result.returncode != 0:
        raise urllib.error.URLError(
            f"wsl bridge subprocess failed "
            f"(rc={result.returncode}, stderr={result.stderr[:200]!r})"
        )

    try:
        response = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise urllib.error.URLError(
            f"wsl bridge returned non-JSON stdout: {result.stdout[:200]!r}"
        ) from exc

    if not isinstance(response, dict):
        raise urllib.error.URLError(f"wsl bridge returned non-dict JSON: {result.stdout[:200]!r}")

    if response.get("ok"):
        body_text = response.get("body", "")
        if not isinstance(body_text, str):
            raise urllib.error.URLError("wsl bridge response body not a string")
        return body_text

    kind = response.get("kind", "unknown")
    if kind == "HTTPError":
        status = response.get("status", 500)
        err_body = response.get("body", "")
        raise urllib.error.HTTPError(
            url,
            int(status) if isinstance(status, int) else 500,
            f"HTTP {status}: {err_body[:200]}",
            email.message.Message(),
            None,
        )
    reason = response.get("reason", "(no reason given)")
    raise urllib.error.URLError(f"wsl bridge {kind}: {reason}")
