"""Sonnet pause/proceed classifier helper (PLAN-0008 Step 5).

Called by ``.claude/hooks/stop_continuation.py`` (Step 4) on every
``Stop`` event under the chain cap. Decides whether the agent should
*proceed* (keep iterating without Cray) or *pause* (yield to Cray).

Reads ``.claude/autonomy-triggers.md`` verbatim as the decision
registry, calls the Anthropic Messages API with Sonnet 4.6 (pin per
PLAN-0008 OQ-B), parses a JSON response, and returns
``{decision, matched_rows, reason}``.

**Stdlib-only by design.** PLAN §Step 5 noted the Anthropic SDK as
"preferred for structured output via format constraint", but
``urllib.request`` + JSON-in-text + retry-once achieves the same
guarantee without a new Python dep, matching the Phase 1 hooks
idiom (everything under ``.claude/hooks/`` is import-free apart from
stdlib + sibling hook modules). Avoids the C2 (new external dep)
registry trigger for the very classifier that exists to enforce
the registry — chicken-and-egg sidestepped.

**Fail-closed pause.** Every error path (API unreachable, malformed
JSON after retry, missing ``$ANTHROPIC_API_KEY``, missing registry
file, response not matching the schema) returns
``{"decision": "pause", "reason": "..."}``. The hook flow in
``stop_continuation.py`` thus *never* mis-proceeds past a real
gate because of an infrastructure failure.

**Conservative-by-default prompt.** The system prompt instructs the
classifier to default to ``pause`` unless the next action is
obviously low-risk progress. Cray's stated preference (ELI-CTO
discussion) is spurious pauses over spurious proceeds.

**Auth (Step 5b — config-file fallback).** Resolution chain:

1. ``$ANTHROPIC_API_KEY`` env (truthy after strip)
2. ``~/.claude/.anthropic_api_key`` (first non-empty line, whitespace
   stripped; chmod 600 enforced on POSIX). Override the path via
   ``$CLAUDE_ANTHROPIC_KEY_FILE``.
3. → fail-closed pause.

The file fallback exists because **Claude Desktop launches the
``claude.exe`` CLI with ``ANTHROPIC_API_KEY=""``** (empty, not unset)
for OAuth-subscription / API-key billing isolation. WSLENV propagation
cannot defeat this — User-scope env is overwritten by Desktop before
the CLI spawn. Any hook invoked from inside a Claude Code session
inherits the empty value. The Telegram-token pattern from PLAN-0007 /
ADR-013 D5 is unaffected (Desktop strips only Anthropic-auth vars).
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent
DEFAULT_REGISTRY = REPO_ROOT / ".claude" / "autonomy-triggers.md"
DEFAULT_KEY_FILE = Path.home() / ".claude" / ".anthropic_api_key"

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MAX_TOKENS = 1024
API_TIMEOUT_SEC = 20  # Sonnet typical < 5s; padding for cold-start / queue
KEY_FILE_PERM_MASK = 0o077  # any group/other bit set = unsafe (POSIX)

# Decision contract — single source of truth, used by tests too.
DECISION_PROCEED = "proceed"
DECISION_PAUSE = "pause"


def _registry_path() -> Path:
    override = os.environ.get("CLAUDE_AUTONOMY_REGISTRY_PATH")
    return Path(override) if override else DEFAULT_REGISTRY


def _key_file_path() -> Path:
    override = os.environ.get("CLAUDE_ANTHROPIC_KEY_FILE")
    return Path(override) if override else DEFAULT_KEY_FILE


def _resolve_api_key() -> tuple[str | None, str]:
    """Resolve the Anthropic API key from env or the fallback key file.

    Returns ``(key, source_or_reason)``. On success ``key`` is the
    resolved token and ``source_or_reason`` is a short tag (``"env"``
    or ``"file:<path>"``). On failure ``key`` is ``None`` and
    ``source_or_reason`` is the fail-closed reason string.

    Chain (Step 5b):

    1. ``$ANTHROPIC_API_KEY`` env if truthy after strip — wins
    2. ``~/.claude/.anthropic_api_key`` (override via
       ``$CLAUDE_ANTHROPIC_KEY_FILE``). On POSIX the file must be
       chmod 600 (no group/other bits) or the read is refused.
       First non-empty line, whitespace stripped, is the key.
    3. neither → ``(None, "...")``.

    See the module docstring for the Claude Desktop env-strip rationale.
    """
    env_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if env_key:
        return env_key, "env"

    path = _key_file_path()
    if not path.exists():
        return None, f"ANTHROPIC_API_KEY not set; key file missing at {path}"

    if os.name == "posix":
        try:
            mode = path.stat().st_mode
        except OSError as exc:
            return None, f"key file {path} stat failed: {exc}"
        if mode & KEY_FILE_PERM_MASK:
            return None, (
                f"key file {path} has unsafe permissions "
                f"(mode={oct(mode & 0o777)}; require chmod 600)"
            )

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"key file {path} unreadable: {exc}"

    for line in content.splitlines():
        candidate = line.strip()
        if candidate:
            return candidate, f"file:{path}"
    return None, f"key file {path} is empty"


def _api_url() -> str:
    return os.environ.get("CLAUDE_SONNET_API_URL") or DEFAULT_API_URL


def _model() -> str:
    return os.environ.get("CLAUDE_SONNET_MODEL") or DEFAULT_MODEL


def _pause(reason: str, matched: list[str] | None = None) -> dict[str, Any]:
    return {
        "decision": DECISION_PAUSE,
        "matched_rows": matched or [],
        "reason": reason,
    }


def _load_registry() -> str | None:
    p = _registry_path()
    if not p.exists():
        return None
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return None
    return text if text.strip() else None


def _build_system_prompt(registry: str, *, strict: bool = False) -> str:
    base = (
        "You are the Phase 2 autonomy classifier for vero-lite Claude "
        "Code sessions.\n\n"
        "Your job: given the agent's recent activity (in the user "
        "message), decide whether the agent should\n"
        "  (a) PROCEED — keep iterating without Cray's input, or\n"
        "  (b) PAUSE  — yield to Cray and wait for human review.\n\n"
        "Decision criteria are in this registry. Read it literally; "
        "scan the agent's recent activity against the rows. If the "
        "next likely action matches an always-pause row, return PAUSE "
        "and cite the row ID.\n\n"
        "--- REGISTRY START ---\n"
        f"{registry}\n"
        "--- REGISTRY END ---\n\n"
        "Default to PAUSE unless the next action is obviously low-risk "
        "progress (e.g., committing tests that just passed, running a "
        "known-safe read-only command). Conservative bias is "
        "intentional: spurious pauses are preferred over spurious "
        "proceeds.\n\n"
        "Respond with ONLY a JSON object matching this schema:\n"
        '  {"decision": "proceed" | "pause", "matched_rows": '
        '[<row IDs like "G1", "L3">], "reason": "<one short sentence>"}\n'
    )
    if strict:
        base += (
            "\nIMPORTANT: Respond with the raw JSON object ONLY. No "
            "markdown fences, no prose before or after, no comments.\n"
        )
    return base


def _build_user_message(payload: dict[str, Any]) -> str:
    """Render the Stop event payload as the classifier's user message.

    The Stop event payload shape from Claude Code is not formally
    specced; we just JSON-dump whatever came in so the classifier sees
    the same context the harness has. A future Step 6 refinement can
    add structured "recent N actions" summary here.
    """
    safe = json.dumps(payload, indent=2, sort_keys=True, default=str)
    return (
        "The agent has just emitted a Stop event. The raw event "
        "payload follows. Decide whether to PROCEED (continue the "
        "agent loop) or PAUSE (yield to Cray).\n\n"
        f"```\n{safe}\n```"
    )


def _call_api(
    api_key: str,
    system_prompt: str,
    user_message: str,
) -> str:
    """POST to Anthropic Messages API; return the assistant text content.

    Raises ``urllib.error.URLError`` on network/HTTP failure,
    ``TimeoutError`` on timeout, ``ValueError`` on malformed wire
    response. Caller handles these as fail-closed pause.
    """
    body = json.dumps(
        {
            "model": _model(),
            "max_tokens": DEFAULT_MAX_TOKENS,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
        }
    ).encode("utf-8")
    # S310: the URL is a fixed Anthropic Messages endpoint (or an
    # explicit test override via $CLAUDE_SONNET_API_URL) — not user-
    # controlled, and the scheme is locked to https by the constant.
    req = urllib.request.Request(  # noqa: S310
        _api_url(),
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": DEFAULT_ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=API_TIMEOUT_SEC) as resp:  # noqa: S310
        wire = json.loads(resp.read().decode("utf-8"))
    content = wire.get("content")
    if not isinstance(content, list) or not content:
        raise ValueError("Anthropic response missing 'content' list")
    first = content[0]
    if not isinstance(first, dict) or first.get("type") != "text":
        raise ValueError("Anthropic response first content block not text")
    text = first.get("text", "")
    if not isinstance(text, str):
        raise ValueError("Anthropic response text not a string")
    return text


_JSON_OBJECT_RE = re.compile(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", re.DOTALL)


def _parse_response(text: str) -> dict[str, Any]:
    """Parse the classifier's text reply into the decision dict.

    First try whole-text JSON parse; if that fails, search for the
    first balanced JSON object (model may wrap in markdown despite
    instructions). Raises ``ValueError`` on no-parse or
    schema-violation; caller catches and triggers retry or fail-closed.
    """
    stripped = text.strip()
    raw: Any
    try:
        raw = json.loads(stripped)
    except json.JSONDecodeError:
        match = _JSON_OBJECT_RE.search(stripped)
        if match is None:
            raise ValueError("no JSON object in classifier response") from None
        raw = json.loads(match.group(0))

    if not isinstance(raw, dict):
        raise ValueError("classifier response not a JSON object")
    decision = raw.get("decision")
    if decision not in (DECISION_PROCEED, DECISION_PAUSE):
        raise ValueError(f"invalid decision value: {decision!r}")
    matched = raw.get("matched_rows") or []
    if not isinstance(matched, list):
        raise ValueError("matched_rows not a list")
    reason = raw.get("reason") or ""
    if not isinstance(reason, str):
        raise ValueError("reason not a string")
    return {
        "decision": decision,
        "matched_rows": [str(r) for r in matched],
        "reason": reason,
    }


def classify(payload: dict[str, Any]) -> dict[str, Any]:
    """Public entry point. Always returns a dict matching the contract.

    Fail-closed: any error → pause with explanatory reason.
    """
    api_key, source_or_reason = _resolve_api_key()
    if not api_key:
        return _pause(source_or_reason)

    registry = _load_registry()
    if registry is None:
        return _pause("autonomy registry missing or empty")

    user_message = _build_user_message(payload)

    # First attempt — normal prompt.
    try:
        text = _call_api(api_key, _build_system_prompt(registry), user_message)
    except (urllib.error.URLError, TimeoutError) as exc:
        return _pause(f"API unreachable: {exc}")
    except ValueError as exc:
        return _pause(f"API response malformed: {exc}")
    except Exception as exc:  # defensive: never raise into the hook flow
        return _pause(f"classifier transport error: {exc}")

    try:
        return _parse_response(text)
    except ValueError:
        pass  # fall through to retry

    # Retry once with stricter prompt.
    try:
        text2 = _call_api(
            api_key,
            _build_system_prompt(registry, strict=True),
            user_message,
        )
    except (urllib.error.URLError, TimeoutError) as exc:
        return _pause(f"retry unreachable: {exc}")
    except Exception as exc:
        return _pause(f"retry transport error: {exc}")

    try:
        return _parse_response(text2)
    except ValueError as exc:
        return _pause(f"classifier response unparseable after retry: {exc}")
