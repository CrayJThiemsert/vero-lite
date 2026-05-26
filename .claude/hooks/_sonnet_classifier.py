"""Sonnet pause/proceed/dispatch classifier helper (PLAN-0008 Step 5 +
PLAN-0009 Step 5c-1).

Called by ``.claude/hooks/stop_continuation.py`` (Step 4) on every
``Stop`` event under the chain cap. Decides whether the agent should
*proceed* (keep iterating without Cray), *pause* (yield to Cray), or
*dispatch* (auto-handoff to a co-located subagent — PLAN-0009 Step 5c).

Reads ``.claude/autonomy-triggers.md`` verbatim as the decision
registry, calls the Anthropic Messages API with Sonnet 4.6 (pin per
PLAN-0008 OQ-B), parses a JSON response, and returns
``{decision, matched_rows, reason}`` (plus ``dispatch`` metadata when
decision == "dispatch").

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
DECISION_DISPATCH = "dispatch"  # PLAN-0009 Step 5c-1 — auto-handoff arm
_VALID_DECISIONS = frozenset({DECISION_PROCEED, DECISION_PAUSE, DECISION_DISPATCH})

# Dispatch metadata constraints — keep tight per Step 4 §1 R4 (governance
# drafting is the only auto-handoff use case in Phase 3; explore-research
# is a main-agent routing decision per Step 4 §1 R2/R5, not auto-handoff).
DISPATCH_ALLOWED_SUBAGENTS = frozenset({"plan-drafter"})
DISPATCH_ALLOWED_ARTIFACT_KINDS = frozenset({"adr", "plan"})
# Loose cap on task_summary length; classifier-emitted strings should be
# imperative one-liners per the system prompt, but we cap defensively so
# the dispatch instruction template stays bounded.
DISPATCH_TASK_SUMMARY_MAX_CHARS = 500


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
        "You are the Phase 2 + Phase 3 autonomy classifier for vero-lite "
        "Claude Code sessions.\n\n"
        "Your job: given the agent's recent activity (in the user "
        "message), decide whether the agent should\n"
        "  (a) PROCEED  — keep iterating without Cray's input,\n"
        "  (b) PAUSE    — yield to Cray and wait for human review, or\n"
        "  (c) DISPATCH — auto-handoff to a co-located subagent for a\n"
        "      governance-drafting task that the agent should NOT pause\n"
        "      for, because the work is bounded + structured + a Plan\n"
        "      subagent can produce a PR-ready draft without Cray paste.\n"
        "      (PLAN-0009 Step 5c-1; D-rows in the registry below.)\n\n"
        "Decision criteria are in this registry. Read it literally; "
        "scan the agent's recent activity against the rows. If the "
        "next likely action matches an always-pause row (G/C/H/L), "
        "return PAUSE and cite the row ID. If it matches an auto-handoff "
        "row (D-rows), return DISPATCH and cite the D-row + emit "
        "dispatch metadata.\n\n"
        "--- REGISTRY START ---\n"
        f"{registry}\n"
        "--- REGISTRY END ---\n\n"
        "Default to PAUSE unless the next action is obviously low-risk "
        "progress (e.g., committing tests that just passed, running a "
        "known-safe read-only command) OR clearly matches a D-row "
        "auto-handoff trigger. Conservative bias is intentional: "
        "spurious pauses are preferred over spurious proceeds. "
        "Spurious dispatches are worse than spurious pauses (they "
        "consume a subagent spawn) — when in doubt between PAUSE and "
        "DISPATCH, choose PAUSE.\n\n"
        "Respond with ONLY a JSON object matching this schema:\n"
        '  {"decision": "proceed" | "pause" | "dispatch",\n'
        '   "matched_rows": [<row IDs like "G1", "L3", "D1">],\n'
        '   "reason": "<one short sentence>",\n'
        '   "dispatch": {                       // REQUIRED iff decision == "dispatch"\n'
        '     "subagent": "plan-drafter",       // only allowed value today\n'
        '     "artifact_kind": "adr" | "plan",  // matches the D-row\n'
        '     "task_summary": "<imperative one-liner ≤ 200 chars>"\n'
        "   }}\n\n"
        "Omit the dispatch field when decision is proceed or pause. "
        "If you cannot supply valid dispatch metadata, fall back to "
        "PAUSE instead — the dispatch arm is fail-closed.\n"
    )
    if strict:
        base += (
            "\nIMPORTANT: Respond with the raw JSON object ONLY. No "
            "markdown fences, no prose before or after, no comments.\n"
        )
    return base


def _build_user_message(payload: dict[str, Any]) -> str:
    """Render the hook event payload as the classifier's user message.

    The classifier is called from both ``Stop`` (PLAN-0008 Step 4) and
    ``PreToolUse`` (PLAN-0009 Step 5c-2) hooks. The user message stays
    generic — the payload's ``hook_event_name`` / ``event`` field tells
    the model which event fired; the JSON dump includes everything else.
    A future refinement can add a structured "recent N actions" summary
    above the JSON dump.
    """
    safe = json.dumps(payload, indent=2, sort_keys=True, default=str)
    event_hint = payload.get("hook_event_name") or payload.get("event") or "<unknown>"
    return (
        f"The agent has just emitted a `{event_hint}` hook event. The raw "
        "event payload follows. Decide whether to PROCEED (continue / "
        "allow the action), PAUSE (yield to Cray and deny / wait for "
        "review), or DISPATCH (auto-handoff a governance-drafting task "
        "to a co-located subagent).\n\n"
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


def _validate_dispatch_metadata(raw_dispatch: Any) -> dict[str, str]:
    """Validate the ``dispatch`` field structure when decision == "dispatch".

    PLAN-0009 Step 5c-1 dispatch contract. Returns a normalized dict with
    the three required keys; raises ``ValueError`` on any schema violation
    so the caller can fail-closed to PAUSE per the design discipline
    ("spurious dispatches are worse than spurious pauses").
    """
    if not isinstance(raw_dispatch, dict):
        raise ValueError("dispatch field must be an object")

    subagent = raw_dispatch.get("subagent")
    if not isinstance(subagent, str) or subagent not in DISPATCH_ALLOWED_SUBAGENTS:
        raise ValueError(
            f"dispatch.subagent must be one of {sorted(DISPATCH_ALLOWED_SUBAGENTS)}; "
            f"got {subagent!r}"
        )

    artifact_kind = raw_dispatch.get("artifact_kind")
    if not isinstance(artifact_kind, str) or artifact_kind not in DISPATCH_ALLOWED_ARTIFACT_KINDS:
        raise ValueError(
            f"dispatch.artifact_kind must be one of "
            f"{sorted(DISPATCH_ALLOWED_ARTIFACT_KINDS)}; got {artifact_kind!r}"
        )

    task_summary = raw_dispatch.get("task_summary")
    if not isinstance(task_summary, str) or not task_summary.strip():
        raise ValueError("dispatch.task_summary must be a non-empty string")
    task_summary = task_summary.strip()
    if len(task_summary) > DISPATCH_TASK_SUMMARY_MAX_CHARS:
        raise ValueError(
            f"dispatch.task_summary exceeds {DISPATCH_TASK_SUMMARY_MAX_CHARS} chars "
            f"({len(task_summary)} given)"
        )

    return {
        "subagent": subagent,
        "artifact_kind": artifact_kind,
        "task_summary": task_summary,
    }


def _parse_response(text: str) -> dict[str, Any]:
    """Parse the classifier's text reply into the decision dict.

    First try whole-text JSON parse; if that fails, search for the
    first balanced JSON object (model may wrap in markdown despite
    instructions). Raises ``ValueError`` on no-parse or
    schema-violation; caller catches and triggers retry or fail-closed.

    PLAN-0009 Step 5c-1: also handles ``decision == "dispatch"`` with
    the required ``dispatch`` metadata sub-object; any dispatch schema
    violation raises ``ValueError`` so the caller fails closed to PAUSE.
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
    if decision not in _VALID_DECISIONS:
        raise ValueError(f"invalid decision value: {decision!r}")
    matched = raw.get("matched_rows") or []
    if not isinstance(matched, list):
        raise ValueError("matched_rows not a list")
    reason = raw.get("reason") or ""
    if not isinstance(reason, str):
        raise ValueError("reason not a string")

    result: dict[str, Any] = {
        "decision": decision,
        "matched_rows": [str(r) for r in matched],
        "reason": reason,
    }

    if decision == DECISION_DISPATCH:
        # Required iff decision == dispatch. Missing or malformed → ValueError →
        # caller's retry-then-pause flow (fail-closed).
        if "dispatch" not in raw:
            raise ValueError("decision=dispatch requires a 'dispatch' field")
        result["dispatch"] = _validate_dispatch_metadata(raw["dispatch"])

    return result


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
