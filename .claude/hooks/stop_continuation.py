#!/usr/bin/env python3
"""Stop hook — turn-boundary L1 reset + chain-cap fail-safe + auto-handoff
dispatch (PLAN-0008 Step 4 + PLAN-0009 Step 5c-1).

Fires on every ``Stop`` event. Three responsibilities:

1. **Turn-boundary reset (priority).** Reads ``turn_touched`` from the
   loop-counter state file (recorded by Step 3's
   ``posttooluse_progress_observer.py`` on each Write/Edit) and resets
   L1 counters whose targets were NOT touched this turn. Implements
   the "target untouched on the next turn-boundary marker" rule from
   PLAN §Step 1 / §Step 3. **Closes the 🔴 L1 reset gap** surfaced in
   the L1/L4 asymmetry ELI-CTO (Cray's iterative STATUS-editing
   workflow would otherwise false-positive at 6 edits per session).
2. **Chain-cap fail-safe (PLAN §Step 4).** Tracks consecutive
   ``proceed`` decisions in ``.claude/state/stop-chain.json``
   against ``$CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`` (default 8). On cap-hit:
   emits no block (lets the stop fire), pings Telegram with
   ``"cap reached"`` per OQ-E option (b), and resets the chain.
   Re-entry guarded by the harness ``stop_hook_active`` flag.
   (``dispatch`` no longer counts toward the cap — see 3; the goal-gate
   V1 directive still does.)
3. **Dispatch suggestion (PLAN-0009 Step 5c-1, DEMOTED by PLAN-0092).**
   When the classifier returns ``decision == "dispatch"`` (governance-
   drafting need matching a D-row in the registry), the hook emits
   **nothing**: the stop fires with pause semantics (chain **reset**) and
   the classifier's routing — subagent, artifact_kind, task_summary,
   matched D-rows, reason — is delivered to Cray as a single Telegram
   ping. It is a **suggestion, never an order**; Cray routes it.
   Malformed metadata stays silent (no ping, no directive).
   *Was:* a ``block`` directive instructing the main agent to spawn
   ``plan-drafter``. Demoted after 14 recorded misfires / 0 recorded
   valid fires across ~2 months live (PLAN-0092; Cray-ratified 2026-07-23).

The Sonnet pause/proceed/dispatch classifier is invoked via
``_sonnet_classifier.classify`` (PLAN §Step 5 + PLAN-0009 Step 5c-1).
The classifier reads ``.claude/autonomy-triggers.md`` verbatim, calls
the Anthropic Messages API (stdlib urllib), parses JSON, and is
fail-closed: any infrastructure failure returns ``pause``. The hook
flow here therefore never mis-proceeds because of an API outage, and
never mis-dispatches on malformed dispatch metadata (the classifier
demotes a bad dispatch to ``pause`` before returning).

State file paths and Telegram script honor the env-var overrides
shared with Step 2/3 for testability
(``CLAUDE_LOOP_COUNTER_PATH``, ``CLAUDE_TELEGRAM_SCRIPT``,
``CLAUDE_STOP_CHAIN_PATH``, ``CLAUDE_CODE_STOP_HOOK_BLOCK_CAP``).
"""

from __future__ import annotations

import json
import os
import re
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
from _wsl_bridge import bash_argv, env_with_wslenv_passthrough  # noqa: E402

DEFAULT_TELEGRAM_SCRIPT = REPO_ROOT / "tools" / "notify" / "telegram.sh"
DEFAULT_CHAIN_PATH = STATE_DIR / "stop-chain.json"
DEFAULT_CAP = 8
TELEGRAM_TIMEOUT_SEC = 5

_FORWARDED_ENV = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")


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


def _format_cap_message(payload: dict[str, Any]) -> str:
    """Build the human-readable Telegram body from the cap-reached payload."""
    event = str(payload.get("event") or "stop_continuation_event")
    depth = payload.get("depth", "?")
    cap = payload.get("cap", "?")
    ts = str(payload.get("ts") or "")
    reason = str(payload.get("reason") or "").strip()
    return f"[vero-lite/{event}] depth={depth} / cap={cap}\n" f"ts: {ts}\n" f"{reason}"


def _format_dispatch_suggestion(payload: dict[str, Any]) -> str:
    """Build the Telegram body for an A' dispatch suggestion (PLAN-0092 SD-A).

    Deliberately NOT the cap shape: ``depth=``/``cap=`` are meaningless for a
    suggestion and would bury the five routing fields Cray reads on a phone.
    The wording is advisory on purpose — this channel must never read as an
    instruction to spawn.
    """
    rows = payload.get("matched_rows") or []
    matched = ", ".join(str(r) for r in rows) if rows else "(none cited)"
    return (
        f"[vero-lite/{payload.get('event')}] classifier suggestion — not an order\n"
        f"ts: {payload.get('ts', '')}\n"
        f"subagent: {payload.get('subagent', '')}\n"
        f"artifact_kind: {payload.get('artifact_kind', '')}\n"
        f"task_summary: {payload.get('task_summary', '')}\n"
        f"matched_rows: {matched}\n"
        f"reason: {str(payload.get('reason') or '').strip()}\n"
        "Route it yourself if it is right; ignoring it is the default (PLAN-0092)."
    )


def _format_message(payload: dict[str, Any]) -> str:
    """Dispatch to the formatter for this payload's event kind."""
    if payload.get("event") == "stop_dispatch_suggestion":
        return _format_dispatch_suggestion(payload)
    return _format_cap_message(payload)


def _ping_telegram(message: dict[str, Any]) -> None:
    """Best-effort Telegram ping. Never raises; the hook flow continues.

    Cross-platform invocation + WSLENV passthrough delegated to
    :mod:`_wsl_bridge` (Pattern A). The formatted message is delivered as a
    single argv element (per ``telegram.sh`` contract — argv, never stdin).
    """
    script = _telegram_script()
    if not script.exists():
        return
    body = _format_message(message)
    cmd = bash_argv(script, body)
    env = env_with_wslenv_passthrough(_FORWARDED_ENV)

    try:
        # S603: cmd elements come from hook-controlled script path
        # (constant or env-override) + the formatted message; no shell
        # interpolation.
        subprocess.run(  # noqa: S603
            cmd,
            env=env,
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


def _classify(payload: dict[str, Any]) -> dict[str, Any]:
    """Dispatch to the Sonnet classifier with fail-closed pause.

    Imports lazily so a missing ``_sonnet_classifier`` module (unlikely
    in production, but defensive) does not break the hook flow. Any
    transport or schema error inside ``classify()`` is already
    converted to a pause by the helper — this wrapper adds a final
    catch-all so the Stop hook can never raise into the harness.
    """
    try:
        from _sonnet_classifier import classify  # local import: tolerant to absence
    except ImportError as exc:
        return {
            "decision": "pause",
            "matched_rows": [],
            "reason": f"classifier helper unavailable: {exc}",
        }
    try:
        return classify(payload)
    except Exception as exc:  # final safety net; helper should already fail-closed
        return {
            "decision": "pause",
            "matched_rows": [],
            "reason": f"classifier raised unexpectedly: {exc}",
        }


def _run_goal_gate(payload: dict[str, Any]) -> dict[str, Any] | None:
    """PLAN-0021 / ADR-0018 D4 goal gate — lazy-import wrapper.

    Mirrors :func:`_classify`'s tolerance posture: a missing ``_goal_gate``
    module or any unexpected raise inside it degrades to ``None`` (fall
    through to the classifier flow unchanged) so the Stop hook can never
    break on the verification layer. With no active ``goal.json`` the gate
    itself returns ``None`` immediately (AC-2 — goal-less sessions are
    byte-for-byte unchanged).
    """
    try:
        from _goal_gate import run_goal_gate  # local import: tolerant to absence
    except ImportError:
        return None
    try:
        return run_goal_gate(payload)
    except Exception as exc:  # never raise into the harness (D4 posture)
        print(f"stop_continuation: goal gate raised unexpectedly: {exc}", file=sys.stderr)
        return None


def _proceed_block(reason: str) -> dict[str, Any]:
    """`decision: block` on Stop = continuation loop (per Anthropic
    stop-hook docs: blocking returns the agent to the loop).
    """
    return {
        "decision": "block",
        "reason": reason,
        "hookSpecificOutput": {"hookEventName": "Stop"},
    }


# Meta-continuation vocabulary: words that describe the ACT of continuing
# rather than WHAT to do. A reason built entirely from these names no next
# action. Deliberately narrow — every genuine action verb (merge, commit,
# run, write, fix, read, reconcile, ...) is absent, so it stays a FLOOR and
# never becomes a specificity judge. See _reason_is_contentless.
_META_REASON_TOKENS = frozenset(
    {
        # continuation verbs
        "continue",
        "continues",
        "continuing",
        "proceed",
        "proceeds",
        "proceeding",
        "resume",
        "resumes",
        "resuming",
        "keep",
        "keeps",
        "keeping",
        "go",
        "goes",
        "going",
        "carry",
        "carrying",
        "start",
        "starting",
        "begin",
        "beginning",
        # generic work nouns
        "work",
        "works",
        "working",
        "task",
        "tasks",
        "step",
        "steps",
        "item",
        "items",
        "action",
        "actions",
        "thing",
        "things",
        "job",
        "jobs",
        "piece",
        "pieces",
        "part",
        "parts",
        "bit",
        "bits",
        # sequence / position
        "next",
        "following",
        "remaining",
        "further",
        "more",
        "rest",
        "ahead",
        "forward",
        "onward",
        "then",
        "now",
        "first",
        "second",
        "last",
        "again",
        "another",
        "other",
        "others",
        # generic completion
        "finish",
        "finishes",
        "finishing",
        "complete",
        "completes",
        "completing",
        "completion",
        "done",
        "wrap",
        "wrapping",
        # modality / filler / function words
        "a",
        "an",
        "the",
        "to",
        "with",
        "on",
        "in",
        "of",
        "for",
        "and",
        "or",
        "at",
        "by",
        "from",
        "as",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "it",
        "its",
        "this",
        "that",
        "these",
        "those",
        "there",
        "here",
        "up",
        "out",
        "i",
        "we",
        "you",
        "agent",
        "session",
        "turn",
        "do",
        "does",
        "doing",
        "should",
        "must",
        "can",
        "could",
        "will",
        "would",
        "shall",
        "may",
        "might",
        "need",
        "needs",
        "needed",
        "let",
        "lets",
        "us",
        "please",
        "still",
        "yet",
        "just",
        "simply",
        "current",
        "currently",
        "ongoing",
        "pending",
        "open",
        "active",
        "normal",
        "normally",
        "ready",
        "safe",
        "ok",
        "okay",
    }
)


def _reason_is_contentless(reason: str) -> bool:
    """True when ``reason`` names no concrete next action.

    The Stop hook passes a ``proceed`` reason back to the agent VERBATIM
    as its continuation instruction (:func:`_proceed_block`), and the
    classifier prompt requires a proceed reason to NAME the next action.
    Nothing enforced that. A model that wants ``proceed`` but has no
    action to name can satisfy the JSON schema with a placeholder —
    session 160 observed the reason ``"Continue to the next work step"``
    on a turn whose only real next step was Cray's decision, and the
    agent read it as an order to invent work. #843 does not cover this
    shape: that paragraph forbids NAMING a Cray-reserved step, and a
    contentless reason names nothing at all.

    The demotion is free of judgement calls because **a contentless
    reason is worthless even when ``proceed`` is correct** — the reason
    IS the instruction, so an instruction that says nothing cannot be
    the right output either way. This is therefore a FLOOR, not a
    specificity judge: it rejects only reasons built entirely from
    meta-continuation vocabulary, never a weak-but-substantive one
    (``"Continue running the test and mypy suite on the merged commit"``
    — the OTHER session-159 directive — keeps ``run``/``test``/``mypy``/
    ``commit`` and passes).

    Non-ASCII reasons pass: ``\\w`` is Unicode-aware, so Thai or any
    other script yields tokens outside the ASCII meta set.
    """
    tokens = re.findall(r"\w+", reason.lower())
    return not any(token not in _META_REASON_TOKENS for token in tokens)


def _dispatch_suggestion_payload(
    dispatch: dict[str, Any],
    matched_rows: list[str],
    classifier_reason: str,
) -> dict[str, Any]:
    """Build the suggestion payload Cray receives instead of a spawn order.

    PLAN-0092 (A'): the classifier's routing judgment is preserved verbatim —
    subagent, artifact_kind, task_summary, the matched D-rows and the reason —
    but it is delivered as advice on a side channel, not as a continuation
    instruction the agent must adversarially decline. Cray routes it.
    """
    return {
        "event": "stop_dispatch_suggestion",
        "ts": _now_iso(),
        "subagent": str(dispatch.get("subagent", "")),
        "artifact_kind": str(dispatch.get("artifact_kind", "")),
        "task_summary": str(dispatch.get("task_summary", "")),
        "matched_rows": matched_rows,
        "reason": classifier_reason,
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

    # Goal gate (PLAN-0021 / ADR-0018 D4) — after chain-cap, before the
    # classifier. A dispatch directive counts toward the same chain-cap as
    # classifier proceeds/dispatches (the cap stays the single loop bound);
    # None = no active goal / warn-only outcome -> classifier flow unchanged.
    gate_directive = _run_goal_gate(payload)
    if gate_directive is not None:
        chain["depth"] += 1
        chain["last_proceed_ts"] = _now_iso()
        _save_chain(chain)
        print(json.dumps(gate_directive))
        return 0

    # Classifier dispatch (real Sonnet via _sonnet_classifier, fail-closed pause).
    decision = _classify(payload)
    verdict = decision.get("decision")

    if verdict == "proceed":
        # Contentless-reason floor (session 160). The reason is emitted
        # VERBATIM as the agent's continuation instruction, so one that
        # names no action is demoted to pause — see _reason_is_contentless.
        # A missing `reason` key lands here too: the old "continue" default
        # was itself contentless.
        reason = str(decision.get("reason") or "")
        if _reason_is_contentless(reason):
            print(
                "stop_continuation: demoted a contentless proceed reason to " f"pause: {reason!r}",
                file=sys.stderr,
            )
            _reset_chain()
            return 0
        chain["depth"] += 1
        chain["last_proceed_ts"] = _now_iso()
        _save_chain(chain)
        print(json.dumps(_proceed_block(reason)))
        return 0

    if verdict == "dispatch":
        # PLAN-0092 (A'): a dispatch is a SUGGESTION, not an order. The arm
        # emits no directive — the stop fires normally (pause semantics, chain
        # RESET) and the classifier's routing goes to Cray as one Telegram
        # ping. Rationale: 14 recorded misfires / 0 recorded valid fires, in
        # four shapes across two failure families — the classifier can see
        # neither disk state nor in-flight work (no model upgrade fixes that),
        # and mention-as-intent is a prompt-rule race lost since PLAN-0034.
        # A misfired suggestion costs one ping; a misfired order cost a turn
        # of adversarial declining. This also honors the arm's own stated
        # preference that spurious dispatches are worse than spurious pauses.
        #
        # Malformed metadata stays SILENT (no ping): there is no coherent
        # routing to suggest, so the demotion must not trade a spurious order
        # for spurious noise.
        dispatch_meta = decision.get("dispatch")
        if not isinstance(dispatch_meta, dict):
            _reset_chain()
            return 0
        matched_rows_raw = decision.get("matched_rows") or []
        matched_rows = [str(r) for r in matched_rows_raw if isinstance(matched_rows_raw, list)]
        _ping_telegram(
            _dispatch_suggestion_payload(
                dispatch_meta,
                matched_rows,
                str(decision.get("reason", "")),
            )
        )
        _reset_chain()
        return 0

    # "pause" (or any unrecognized verdict, fail-closed) → no block; reset the
    # chain so the next session starts fresh.
    _reset_chain()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
