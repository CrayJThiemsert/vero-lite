#!/usr/bin/env python3
"""Stop hook — chain-cap fail-safe + auto-handoff dispatch
(PLAN-0008 Step 4 + PLAN-0009 Step 5c-1).

Fires on every ``Stop`` event. Two responsibilities:

**PLAN-0102 removed a third.** This hook used to own both of L1's Stop-side
reset paths — the turn-boundary reset (``turn_touched`` → clear L1 counters for
targets untouched this turn) and the acknowledged-pause exit (PLAN-0094 D5).
Both retired with L1 itself, and they had to go **together**: the excision that
deleted ``reset_l1_for_targets`` while leaving the acknowledged-pause exit
importing it would have raised ``ImportError`` at module load — before any arm
below runs, and caught by no ``try``/``except`` — taking the chain-cap
fail-safe, the classifier and the auto-handoff down with it. That is why the
retirement is asserted behaviourally (PLAN-0102 AC-11 a) rather than by
inspection, and why this hook now imports exactly one name from
``_loop_counter``.

1. **Chain-cap fail-safe (PLAN §Step 4).** Tracks consecutive
   ``proceed`` decisions in ``.claude/state/stop-chain.json``
   against ``$CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`` (default 8). On cap-hit:
   emits no block (lets the stop fire), pings Telegram with
   ``"cap reached"`` per OQ-E option (b), and resets the chain.
   Re-entry guarded by the harness ``stop_hook_active`` flag.
   (``dispatch`` no longer counts toward the cap — see 2; the goal-gate
   V1 directive still does.)
2. **Dispatch suggestion (PLAN-0009 Step 5c-1, DEMOTED by PLAN-0092).**
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
The classifier reads ``.claude/autonomy-triggers.md`` verbatim, for every
event including the ``Stop`` this hook raises. PLAN-0122 Step 2 briefly
answered ``Stop`` with ``_sonnet_classifier.STOP_SYSTEM_PROMPT`` (the
measured SLIM5 prompt); Step 3's held-out validation refuted it — 28/30
with 2 unsafe proceeds against the registry prompt's 29/30 with 0 — and
session 281 reverted that routing on Cray's call. The classifier calls
the Anthropic Messages API (stdlib urllib), parses JSON, and is
fail-closed: any infrastructure failure returns ``pause``. The hook
flow here therefore never mis-proceeds because of an API outage, and
never mis-dispatches on malformed dispatch metadata (the classifier
demotes a bad dispatch to ``pause`` before returning).

State file paths and Telegram script honor the env-var overrides
shared with Step 2/3 for testability
(``CLAUDE_TELEGRAM_SCRIPT``, ``CLAUDE_STOP_CHAIN_PATH``,
``CLAUDE_CODE_STOP_HOOK_BLOCK_CAP``). ``CLAUDE_LOOP_COUNTER_PATH`` is
deliberately NOT in that list any more: this hook stopped touching the loop
counter with PLAN-0102, so honoring the override would be a claim it cannot
back.
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

# ``STATE_DIR`` only — this hook no longer reads or writes the loop counter at
# all (PLAN-0102 retired both of its L1 subsystems). It borrows the constant
# solely to locate its OWN state file, ``stop-chain.json``, in the same dir.
from _loop_counter import STATE_DIR  # noqa: E402  — sys.path manipulation above
from _wsl_bridge import bash_argv, env_with_wslenv_passthrough  # noqa: E402

DEFAULT_TELEGRAM_SCRIPT = REPO_ROOT / "tools" / "notify" / "telegram.sh"
DEFAULT_CHAIN_PATH = STATE_DIR / "stop-chain.json"
DEFAULT_CAP = 8
TELEGRAM_TIMEOUT_SEC = 5

_FORWARDED_ENV = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")


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


#: Path and env override are PLAN-0122 §4.3's, verbatim. They shipped wrong at
#: first (`stop-decisions.jsonl` / `CLAUDE_STOP_DECISION_LOG`), built from
#: AC-8's pass read without reading §4.3, which specifies both — and AC-12
#: would have looked for a file that did not exist.
DEFAULT_DECISION_LOG_PATH = STATE_DIR / "stop-classifier-log.jsonl"


def _decision_log_path() -> Path:
    return Path(os.environ.get("CLAUDE_STOP_CLASSIFIER_LOG") or DEFAULT_DECISION_LOG_PATH)


def _log_decision(
    decision: dict[str, Any],
    emitted: str,
    event: str,
) -> None:
    """Append ONE line per classifier verdict (PLAN-0122 SD-4 / AC-8).

    Today the hook writes a depth counter and nothing else, so the arm Cray
    chose to keep has no production instrument at all: the 117-fire ledger
    existed only because blocked stops reach the transcript, on ~30-day
    retention. Without this, the next review of the arm would again have no
    counted evidence — the exact gap that left the proceed arm unadjudicated
    by PLAN-0092.

    `emitted` is what the agent actually received, which is NOT recoverable
    from `decision` alone: a `proceed` verdict emits a block OR is demoted to
    silence by the contentless floor, and a `dispatch` emits a Telegram
    suggestion OR nothing when its metadata is malformed.

    `transport` separates a pause the MODEL decided from one manufactured
    after a failure — see the `TRANSPORT_*` constants in `_sonnet_classifier`,
    which record the one remaining deviation from §4.3's enum (`not_attempted`).
    Scoring those together would make AC-12's defect rate a measurement of the
    network. The second deviation — an HTTP error labelled `timeout` — was
    retired at s290 by the §4.3 amendment that gave it `http_error`; this
    function copies the field opaquely, so the new value needed no change here.

    Never raises: an observability write must not be able to break the Stop
    path it observes.
    """
    try:
        path = _decision_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        # Field set and order are §4.3's, exactly: ts, event, decision,
        # emitted, reason, matched_rows, latency_s, transport, prompt_sha8.
        line = json.dumps(
            {
                "ts": _now_iso(),
                "event": event,
                "decision": str(decision.get("decision") or ""),
                "emitted": emitted,
                "reason": str(decision.get("reason") or ""),
                "matched_rows": [str(r) for r in (decision.get("matched_rows") or [])],
                "latency_s": decision.get("latency_s"),
                "transport": str(decision.get("transport") or ""),
                "prompt_sha8": str(decision.get("prompt_sha8") or ""),
            },
            ensure_ascii=False,
        )
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception as exc:  # observability must never break the arm it observes
        print(f"stop_continuation: decision log write failed: {exc}", file=sys.stderr)


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
        # `not_attempted` mirrors the helper's own `_pause` default: no request
        # ever left the box, so labelling this `timeout` would assert a network
        # event that never happened. SD-4's log must not score either of these
        # wrapper pauses as a correct model pause.
        return {
            "decision": "pause",
            "matched_rows": [],
            "reason": f"classifier helper unavailable: {exc}",
            "transport": "not_attempted",
        }
    try:
        return classify(payload)
    except Exception as exc:  # final safety net; helper should already fail-closed
        return {
            "decision": "pause",
            "matched_rows": [],
            "reason": f"classifier raised unexpectedly: {exc}",
            "transport": "not_attempted",
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

    # §4.3's `event` field. Defaults to "Stop" rather than "<unknown>": this is
    # the Stop hook, so an absent key means the harness omitted it, not that
    # some other event arrived.
    event = str(payload.get("hook_event_name") or payload.get("event") or "Stop")

    # An L1 turn-boundary reset used to run here, ahead of everything else.
    # PLAN-0102 retired it with L1; the chain-cap is now the first arm, and it
    # touches no loop-counter state at all.
    #
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
            _log_decision(decision, "demoted", event)
            _reset_chain()
            return 0
        chain["depth"] += 1
        chain["last_proceed_ts"] = _now_iso()
        _save_chain(chain)
        _log_decision(decision, "block", event)
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
            # Malformed metadata stays silent, so `emitted` is "none" — the
            # verdict was `dispatch` but the agent and Cray received nothing.
            _log_decision(decision, "none", event)
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
        _log_decision(decision, "suggestion", event)
        _reset_chain()
        return 0

    # "pause" (or any unrecognized verdict, fail-closed) → no block; reset the
    # chain so the next session starts fresh.
    _log_decision(decision, "none", event)
    _reset_chain()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
