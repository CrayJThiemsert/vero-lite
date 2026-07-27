"""Loop-counter state primitives for .claude/hooks/ (PLAN-0008 Step 1).

State file: ``.claude/state/loop-counter.json`` (gitignored, per-session).
Read by Step 2 (``pretooluse_loop_detect.py``); written by Step 3
(``posttooluse_progress_observer.py``). The decision logic and hook
entrypoints land in Steps 2-5; this module ships only the schema,
atomic I/O, normalization, and counter ops.

Schema::

    {
      "session_id": str,
      "started_at": ISO-8601 str,
      "counters": {
        "<loop_type>:<target_normalized>": {
          "count": int,
          "last_6_actions": [
            {"ts": ISO-8601, "tool": str, "target": str, "result": str}
          ],
          "last_updated": ISO-8601,
          "warned_at": ISO-8601 | ""
        }
      }
    }

Loop types map 1:1 to the L1-L4 rows in ``.claude/autonomy-triggers.md``
(Cray E.4 / ADR-013):

- L1 — same file edited repeatedly. **Warn-first since PLAN-0094 P2:** the
  path-class bar (:func:`l1_threshold_for` — 6 code / 15 doc) now WARNS and
  allows; the deny moves out to :func:`l1_deny_threshold_for`
  (+ :data:`L1_GRACE_BUDGET`). ``warned_at`` dedupes the warn to once per entry.
- L2 — same test fails >= 6 times consecutively
- L3 — same error signature seen >= 6 times
- L4 — same bash command pattern fails >= 6 times

Reset semantics are observability-driven (the *signal* gathering lives
in Step 3); this module exposes ``reset()`` so the observer can clear a
counter once the signal arrives.

Session-ID source (OQ-A, Cray-approved 2026-05-24):
``$CLAUDE_SESSION_ID`` -> ``pid-<PID>`` -> ``uuid-<UUID>`` fallback. Callers
that hold a hook payload should pass ``session_id=payload["session_id"]``
to :func:`load_counter` instead of relying on that chain — the harness puts a
real session id on every hook payload, and the ``pid-<PID>`` fallback is the
PID of the short-lived hook subprocess (different on every invocation), so it
can never be compared meaningfully.

**State lifetime (2026-07-25, Cray-approved per-diff).** The state file used
to be effectively immortal: :func:`load_counter` minted a fresh counter only
when the file was missing or corrupt, and the recorded ``session_id`` was
never compared against the live session. Observed consequence — one file held
194 counters spanning 2026-06-23 .. 2026-07-25, including a past-threshold L2
entry last touched 2026-07-06 that would re-alert on its next failure weeks
later (L2/L3 re-fire on *every* observation past threshold). Two independent
guards now bound the lifetime:

1. **Session boundary** — a recorded ``session_id`` that differs from the
   caller-supplied one re-mints the counter (:func:`load_counter`).
2. **Age-out** — entries whose ``last_updated`` is older than
   :data:`COUNTER_MAX_AGE_HOURS` are dropped on load
   (:func:`prune_stale_entries`). Age-out needs no session identity at all,
   so it also covers the case the session check cannot see: ``.claude/state/``
   is gitignored, so creating a git worktree *copies* the state file, carrying
   another session's counters into a fresh tree.

Stdlib-only (no Pydantic) — hooks run as subprocesses and must start
fast without third-party deps.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_DIR = REPO_ROOT / ".claude" / "state"
DEFAULT_COUNTER_PATH = STATE_DIR / "loop-counter.json"

LOOP_TRIGGER_THRESHOLD = 6  # Cray E.4 — >= 6 attempts triggers pause + Telegram (code-path base)
MAX_RECENT_ACTIONS = 6  # last_6_actions ring-buffer size

# L1 path-class threshold (Cray E.4 refinement, 2026-06-08). Prose / docs
# authoring (markdown, ``docs/``) legitimately needs many small sequential edits
# to ONE file within a single turn — multi-section PLAN / ADR / STATUS / lessons
# authoring is the WORK, not a directionless loop. So doc targets get a higher
# bar than the code-path base, kept FINITE so a genuinely stuck doc-edit loop
# still trips. Code paths keep the base 6: the edit -> test -> fail -> edit
# thrash the guard targets does not exist for prose, and L2/L3/L4 (test-fail /
# error-signature / bash-pattern) cover the code feedback loop more directly.
# See docs/lessons/0021-l1-loop-detect-subagent-and-doc-threshold.md + ADR-013 / Cray E.4.
L1_DOC_THRESHOLD = 15

# L1 grace budget (PLAN-0094 P2 / OQ-1 — Cray-ratified `G = 3`, 2026-07-25).
# The path-class threshold T is now the WARN bar, not the deny bar: crossing it
# pings Telegram and hands the agent an advisory reason, but allows the edit.
# The deny wall moves to T + G. Rationale for warn-first: ADR-013 row E.4's
# stated consequence was "pause + Telegram alert" all along, so the hard
# first-trip deny exceeded its own mandate — this moves L1 back TOWARD the
# Accepted ADR rather than away from it. `G` prices how much rope a
# false-positive costs before it walls, which is why it was Cray's call.
# NOTE: this widens only L1. L4's deny bar is untouched (its unit is already
# failure-based and it has no recorded false-fire series).
L1_GRACE_BUDGET = 3

# Age-out window for counter entries (2026-07-25, Cray-approved per-diff).
# An entry whose ``last_updated`` is older than this is dropped on load.
#
# Why 6 hours. Age-out keys on ``last_updated``, which every ``increment``
# refreshes — so a loop that is still running NEVER ages out, whatever this
# value is. The only thing the window trades off is how long a *dormant* loop
# stays remembered. 6 h is (a) comfortably longer than the slowest plausible
# time-to-threshold, so no live signal is truncated: 6 attempts against a
# ~15-minute DB / benchmark cycle is ~1.5 h; and (b) well under a day, so
# nothing survives an overnight gap or bleeds into the next day's session.
# Override per-process with ``CLAUDE_LOOP_COUNTER_MAX_AGE_HOURS`` (read from
# the hook's own env, never from ``tool_input`` — same bypass-immunity
# property as ``CLAUDE_LOOP_COUNTER_PATH``).
COUNTER_MAX_AGE_HOURS = 6.0


class LoopType(str, Enum):
    """L1-L4 loop-detection rows from ``.claude/autonomy-triggers.md``.

    Values match the registry row IDs so Step 2/3 hooks + Step 5
    classifier share one vocabulary.
    """

    FILE_EDIT = "L1"
    TEST_FAIL = "L2"
    ERROR_SIGNATURE = "L3"
    BASH_PATTERN = "L4"


@dataclass
class ActionRecord:
    """One entry in a counter's ``last_6_actions`` ring buffer."""

    ts: str
    tool: str
    target: str
    result: str = ""

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> ActionRecord:
        return cls(
            ts=str(data.get("ts", "")),
            tool=str(data.get("tool", "")),
            target=str(data.get("target", "")),
            result=str(data.get("result", "")),
        )


@dataclass
class CounterEntry:
    """A single ``(loop_type, target)`` counter."""

    count: int = 0
    last_6_actions: list[ActionRecord] = field(default_factory=list)
    last_updated: str = ""
    warned_at: str = ""
    """ISO stamp of the L1 warn ping for this entry, or ``""`` if not yet warned.

    ADDITIVE (PLAN-0094 P2): an older reader ignores the key, and an older state
    file simply reads back ``""`` — which means "not yet warned", so the first
    increment after an upgrade warns once and then dedupes. Its only job is that
    dedupe: the warn fires on CROSSING the bar, and without a stamp every
    subsequent grace-zone edit would re-ping Cray.
    """

    def to_json(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "last_6_actions": [a.to_json() for a in self.last_6_actions],
            "last_updated": self.last_updated,
            "warned_at": self.warned_at,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> CounterEntry:
        actions_raw = data.get("last_6_actions") or []
        actions: list[ActionRecord] = []
        if isinstance(actions_raw, list):
            for a in actions_raw:
                if isinstance(a, dict):
                    actions.append(ActionRecord.from_json(a))
        return cls(
            count=int(data.get("count", 0)),
            last_6_actions=actions[-MAX_RECENT_ACTIONS:],
            last_updated=str(data.get("last_updated", "")),
            warned_at=str(data.get("warned_at", "")),
        )


@dataclass
class LoopCounter:
    """Top-level state document (``.claude/state/loop-counter.json``).

    ``turn_touched`` tracks normalized file paths Written/Edited in the
    **current turn** (between two ``Stop`` events). Step 4's
    ``stop_continuation.py`` consumes this on every ``Stop`` event to
    reset L1 counters whose targets were NOT touched this turn — i.e.,
    the "target untouched on next turn-boundary marker" rule from PLAN
    §Step 1 / §Step 3. List rather than set so JSON round-trip is
    trivial; deduplication happens on append.
    """

    session_id: str
    started_at: str
    counters: dict[str, CounterEntry] = field(default_factory=dict)
    turn_touched: list[str] = field(default_factory=list)
    subagent_touched: dict[str, list[str]] = field(default_factory=dict)
    awaiting_ack: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "counters": {k: v.to_json() for k, v in self.counters.items()},
            "turn_touched": list(self.turn_touched),
            "subagent_touched": {k: list(v) for k, v in self.subagent_touched.items()},
            "awaiting_ack": list(self.awaiting_ack),
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> LoopCounter:
        counters_raw = data.get("counters") or {}
        counters: dict[str, CounterEntry] = {}
        if isinstance(counters_raw, dict):
            for k, v in counters_raw.items():
                if isinstance(v, dict):
                    counters[str(k)] = CounterEntry.from_json(v)
        touched_raw = data.get("turn_touched") or []
        touched: list[str] = []
        if isinstance(touched_raw, list):
            touched = [str(t) for t in touched_raw if isinstance(t, str)]
        # Additive (PLAN-0094 D1): absent in state written before Step 1, so a
        # missing key must read as "no subagent edits recorded", never raise —
        # old and new readers interoperate over the same file.
        sub_raw = data.get("subagent_touched") or {}
        subagent: dict[str, list[str]] = {}
        if isinstance(sub_raw, dict):
            for agent_id, targets in sub_raw.items():
                if isinstance(targets, list):
                    subagent[str(agent_id)] = [t for t in targets if isinstance(t, str)]
        # Additive (PLAN-0094 D5), same tolerance contract as the field above.
        # This one must ALSO survive the round-trip: every Stop rewrites the
        # whole document via ``to_json``, so a field the writer forgets is a
        # field the marker silently loses on the next turn boundary.
        ack_raw = data.get("awaiting_ack") or []
        awaiting: list[str] = []
        if isinstance(ack_raw, list):
            awaiting = [str(t) for t in ack_raw if isinstance(t, str)]
        return cls(
            session_id=str(data.get("session_id", "")),
            started_at=str(data.get("started_at", "")),
            counters=counters,
            turn_touched=touched,
            subagent_touched=subagent,
            awaiting_ack=awaiting,
        )


def counter_key(loop_type: LoopType, target_normalized: str) -> str:
    return f"{loop_type.value}:{target_normalized}"


def normalize_file_path(path_str: str) -> str:
    """L1 — file-path normalization. Reuses the C4 hook idiom.

    Returns a project-relative POSIX path. Falls back to the
    slash-normalized input if the path can't be resolved relative to the
    repo (e.g., truly external file). Backslash -> slash happens BEFORE
    any ``pathlib`` op so Windows / UNC inputs parse correctly regardless
    of host.
    """
    if not path_str:
        return ""
    normalized = path_str.replace("\\", "/")
    marker = "/vero-lite/"
    idx = normalized.rfind(marker)
    if idx >= 0:
        return normalized[idx + len(marker) :]
    p = Path(normalized)
    if p.is_absolute():
        try:
            return p.resolve().relative_to(REPO_ROOT).as_posix()
        except (ValueError, OSError):
            return normalized
    return p.as_posix()


def normalize_pytest_nodeid(nodeid: str) -> str:
    """L2 — pytest nodeid normalization.

    Strips the trailing ``[param]`` suffix so a parametrized test that
    fails 6 different ways collapses to the same counter (it is still
    "the same test in trouble"). Preserves ``::`` separators.
    """
    if not nodeid:
        return ""
    return re.sub(r"\[[^\]]*\]$", "", nodeid.strip())


_VOLATILE_ERR_PATTERNS: tuple[tuple[str, str], ...] = (
    (
        r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?",
        "<ts>",
    ),
    (r"0x[0-9a-fA-F]{6,}", "<addr>"),
    (r"/tmp/[^\s:]+", "<tmp>"),  # noqa: S108 — regex pattern matching tmp-path strings in error text, not a file op
    (r"C:\\Users\\[^\\]+\\AppData\\Local\\Temp\\[^\s:]+", "<tmp>"),
    (r"\bpid=\d+\b", "pid=<pid>"),
    (
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
        "<uuid>",
    ),
)


def normalize_error_signature(first_line: str) -> str:
    """L3 — error-signature normalization.

    Caller extracts the first non-volatile line of the traceback; this
    function strips volatile bits (timestamps, hex addresses, temp paths,
    PIDs, UUIDs) so two occurrences of the same error collapse to the
    same string.
    """
    if not first_line:
        return ""
    out = first_line.strip()
    for pat, repl in _VOLATILE_ERR_PATTERNS:
        out = re.sub(pat, repl, out)
    return re.sub(r"\s+", " ", out)


_BASH_ARG_PATTERN = re.compile(
    r"""
    (
        "[^"]*"                         |  # double-quoted arg
        '[^']*'                         |  # single-quoted arg
        --?[a-zA-Z][\w-]*=\S+           |  # --flag=value
        \./\S+                          |  # ./path
        /\S+                            |  # /abs/path
        \S*/\S+                         |  # any token containing /
        \d+                                # bare integer
    )
    """,
    re.VERBOSE,
)


def tokenize_bash_command(cmd: str) -> str:
    """L4 — bash command tokenization.

    Replaces likely-variant arguments with ``<arg>`` so
    ``pytest tests/foo.py`` and ``pytest tests/bar.py`` collapse to the
    same pattern. Preserves bare flag names without values (``-v``,
    ``--strict``).
    """
    if not cmd:
        return ""
    tokenized = _BASH_ARG_PATTERN.sub("<arg>", cmd.strip())
    tokenized = re.sub(r"(?:<arg>\s*){2,}", "<arg> ", tokenized).strip()
    return re.sub(r"\s+", " ", tokenized)


def resolve_session_id() -> str:
    """Session-ID source (OQ-A, Cray 2026-05-24).

    ``$CLAUDE_SESSION_ID`` (if the harness exposes one) -> ``pid-<PID>``
    -> ``uuid-<UUID>`` fallback. UUID fallback mints a fresh ID per call
    and is essentially unreachable in practice (``os.getpid`` always
    returns a non-zero int on POSIX + Windows).
    """
    env = os.environ.get("CLAUDE_SESSION_ID")
    if env:
        return env
    pid = os.getpid()
    if pid:
        return f"pid-{pid}"
    return f"uuid-{uuid.uuid4()}"


def main_session_id(payload: dict[str, Any]) -> str | None:
    """Session id to compare on load, or ``None`` for a subagent invocation.

    Returns ``None`` when the payload carries a non-empty ``agent_id`` — the
    signal that the hook fired inside a subagent, the same key
    ``pretooluse_git_deny`` / ``pretooluse_classifier_dispatch`` use (G5 /
    PLAN-0034 prong 2; populated live on subagent payloads).

    Why suppress rather than compare: a subagent shares its parent's
    ``session_id``, so a comparison is *expected* to match and would be a
    no-op — but if a future harness version scoped the id per subagent
    instead, every subagent Write would re-mint and wipe the main agent's
    live L1 budget mid-turn. Returning ``None`` makes that impossible
    structurally rather than relying on the id staying shared. Age-out still
    applies on these loads; only the session check is skipped.
    """
    agent_id = payload.get("agent_id")
    if isinstance(agent_id, str) and agent_id.strip():
        return None
    session_id = payload.get("session_id")
    if isinstance(session_id, str) and session_id.strip():
        return session_id.strip()
    return None


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S%z")


def new_counter(session_id: str | None = None) -> LoopCounter:
    return LoopCounter(
        session_id=session_id or resolve_session_id(),
        started_at=_now_iso(),
        counters={},
    )


def _max_age_hours() -> float:
    """Age-out window in hours; ``CLAUDE_LOOP_COUNTER_MAX_AGE_HOURS`` override.

    A malformed or non-positive override falls back to the default rather
    than disabling the guard — a typo must not silently restore the
    immortal-state behaviour this replaces.
    """
    raw = os.environ.get("CLAUDE_LOOP_COUNTER_MAX_AGE_HOURS")
    if not raw:
        return COUNTER_MAX_AGE_HOURS
    try:
        hours = float(raw)
    except ValueError:
        return COUNTER_MAX_AGE_HOURS
    return hours if hours > 0 else COUNTER_MAX_AGE_HOURS


def _parse_iso(ts: str) -> datetime | None:
    """Parse a ``_now_iso`` stamp; ``None`` when absent or unparseable.

    A naive stamp is read as UTC so comparisons never raise on mixed
    awareness. ``None`` is the fail-SAFE answer: callers keep the entry
    rather than dropping it (an entry built directly, without going
    through :func:`increment`, has ``last_updated == ""``).
    """
    if not ts or not ts.strip():
        return None
    try:
        parsed = datetime.fromisoformat(ts.strip())
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def prune_stale_entries(
    counter: LoopCounter,
    max_age_hours: float | None = None,
    now: datetime | None = None,
) -> list[str]:
    """Drop counter entries older than ``max_age_hours``; return dropped keys.

    "Older" means ``last_updated`` — which :func:`increment` refreshes on
    every observation — so an actively-running loop is never pruned. An
    entry with a missing or unparseable ``last_updated`` is KEPT (fail-safe:
    an unreadable stamp must not licence dropping a live signal).
    """
    window = _max_age_hours() if max_age_hours is None else max_age_hours
    cutoff = (now or datetime.now(UTC)) - timedelta(hours=window)
    dropped: list[str] = []
    for key in list(counter.counters):
        stamped = _parse_iso(counter.counters[key].last_updated)
        if stamped is not None and stamped < cutoff:
            del counter.counters[key]
            dropped.append(key)
    return dropped


def load_counter(path: Path | None = None, session_id: str | None = None) -> LoopCounter:
    """Load LoopCounter from disk; mint a fresh one on missing/malformed.

    Never raises. A corrupted state file is treated as missing and
    silently replaced on the next save — Phase 2 state is per-session
    and reset on observable progress anyway, so the cost of losing a
    counter is bounded.

    ``session_id`` — pass ``payload["session_id"]`` from the hook payload.
    When it differs from the ``session_id`` recorded in the file, the file
    belongs to a previous session and a fresh counter is minted. Omitting it
    keeps the previous behaviour (load whatever is on disk) *except* that
    age-out still applies. Callers must NOT pass a subagent's id here: see
    the ``agent_id`` note at each call site — a subagent shares its parent's
    ``session_id``, and re-minting on a subagent's invocation would wipe the
    main agent's live L1 budget.
    """
    p = path or DEFAULT_COUNTER_PATH
    if not p.exists():
        return new_counter(session_id)
    try:
        raw = p.read_text(encoding="utf-8")
        if not raw.strip():
            return new_counter(session_id)
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return new_counter(session_id)
    if not isinstance(data, dict):
        return new_counter(session_id)
    counter = LoopCounter.from_json(data)
    # Session boundary. Both ids must be non-empty to compare — an empty
    # recorded id carries no session information, so it cannot be judged
    # foreign; that case is left to age-out. A file recording the old
    # ``pid-<PID>`` fallback DOES mismatch and is re-minted, once: the mint is
    # then persisted with the real id, so later loads in the same session match.
    if session_id and counter.session_id and counter.session_id != session_id:
        return new_counter(session_id)
    prune_stale_entries(counter)
    return counter


def save_counter(counter: LoopCounter, path: Path | None = None) -> None:
    """Atomic write via tmpfile + ``os.replace``.

    Tmpfile is created in the same directory as the target so
    ``os.replace`` is atomic on a single filesystem. Concurrent
    invocations each write their own tmpfile and the last ``os.replace``
    wins; readers either see the old or the new content, never a partial
    write. Caller re-reads before mutation if strict ordering matters.
    """
    p = path or DEFAULT_COUNTER_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(counter.to_json(), indent=2, sort_keys=True)
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


def increment(
    counter: LoopCounter,
    loop_type: LoopType,
    target_normalized: str,
    action: ActionRecord | None = None,
) -> CounterEntry:
    """Increment ``(loop_type, target)``; append the action to the ring."""
    key = counter_key(loop_type, target_normalized)
    entry = counter.counters.get(key) or CounterEntry()
    entry.count += 1
    if action is not None:
        entry.last_6_actions.append(action)
        if len(entry.last_6_actions) > MAX_RECENT_ACTIONS:
            entry.last_6_actions = entry.last_6_actions[-MAX_RECENT_ACTIONS:]
    entry.last_updated = _now_iso()
    counter.counters[key] = entry
    return entry


def reset(
    counter: LoopCounter,
    loop_type: LoopType,
    target_normalized: str,
) -> None:
    """Reset ``(loop_type, target)`` to zero.

    Removes the entry entirely so the state file does not grow
    unboundedly with reset counters across a long session.
    """
    key = counter_key(loop_type, target_normalized)
    counter.counters.pop(key, None)


def get_count(
    counter: LoopCounter,
    loop_type: LoopType,
    target_normalized: str,
) -> int:
    key = counter_key(loop_type, target_normalized)
    entry = counter.counters.get(key)
    return entry.count if entry else 0


def has_triggered(
    counter: LoopCounter,
    loop_type: LoopType,
    target_normalized: str,
    threshold: int = LOOP_TRIGGER_THRESHOLD,
) -> bool:
    """True iff the counter has reached the Cray-E.4 trigger threshold."""
    return get_count(counter, loop_type, target_normalized) >= threshold


def is_doc_target(target_normalized: str) -> bool:
    """True for prose / documentation L1 targets (markdown or under ``docs/``).

    These get the higher :data:`L1_DOC_THRESHOLD` because multi-section
    governance authoring (PLAN / ADR / STATUS / lessons / handoffs) legitimately
    makes many small sequential edits to one file within a single turn — that is
    the work, not a directionless loop.
    """
    t = target_normalized.lower()
    return t.endswith(".md") or t.startswith("docs/")


def l1_threshold_for(target_normalized: str) -> int:
    """L1 trigger threshold by path class.

    :func:`is_doc_target` -> :data:`L1_DOC_THRESHOLD`; all other (code) targets
    -> :data:`LOOP_TRIGGER_THRESHOLD` (the code-thrash base, unchanged).
    """
    return L1_DOC_THRESHOLD if is_doc_target(target_normalized) else LOOP_TRIGGER_THRESHOLD


def l1_deny_threshold_for(target_normalized: str) -> int:
    """The L1 bar at which the gate actually DENIES: warn bar + grace budget.

    Kept as its own function rather than an inline ``+ L1_GRACE_BUDGET`` at the
    gate, so the warn bar (:func:`l1_threshold_for`, observer-side) and the deny
    bar (here, gate-side) cannot silently drift apart across two hook processes.
    """
    return l1_threshold_for(target_normalized) + L1_GRACE_BUDGET


def mark_warned(counter: LoopCounter, loop_type: LoopType, target_normalized: str) -> bool:
    """Stamp ``warned_at`` for this entry if unstamped; return whether we stamped.

    The return value IS the dedupe: the caller warns only when this returns True,
    so the ping fires on the crossing edit and never again for the same entry.
    A reset (turn boundary / commit / ``SubagentStop``) drops the entry entirely,
    which clears the stamp with it — so a genuinely new loop warns again.
    """
    entry = counter.counters.get(counter_key(loop_type, target_normalized))
    if entry is None or entry.warned_at:
        return False
    entry.warned_at = _now_iso()
    return True


def reset_l1_for_targets(counter: LoopCounter, targets: list[str]) -> list[str]:
    """Reset the L1 counter for each given normalized target; return those cleared.

    Used at the ``SubagentStop`` completion boundary so a subagent's edits do not
    consume the main agent's L1 budget for the same file — symmetric with the
    commit-boundary (:func:`reset` on commit) and Stop turn-boundary
    (:func:`reset_untouched_l1`) resets. The caller supplies the *completing
    agent's own* recorded targets (:func:`take_subagent_touched`), never
    ``turn_touched`` — see PLAN-0094 D1 for why turn scope was a self-unlock path.
    """
    cleared: list[str] = []
    for target in targets:
        key = counter_key(LoopType.FILE_EDIT, target)
        if key in counter.counters:
            del counter.counters[key]
            cleared.append(target)
    return cleared


def record_turn_touched(counter: LoopCounter, target_normalized: str) -> None:
    """Mark a file as touched in the current turn (PostToolUse Write/Edit).

    Deduplicated — the same file touched multiple times within a turn is
    recorded once. The ``Stop`` hook (Step 4) reads this list to decide
    which L1 counters survive vs reset at the turn boundary.
    """
    if not target_normalized:
        return
    if target_normalized not in counter.turn_touched:
        counter.turn_touched.append(target_normalized)


def record_subagent_touched(counter: LoopCounter, agent_id: str, target_normalized: str) -> None:
    """Attribute a Write/Edit to the subagent that performed it (PLAN-0094 D1).

    Keyed per ``agent_id`` so two subagents running in parallel cannot clear each
    other's entries at completion. Deduplicated per key, like
    :func:`record_turn_touched`.
    """
    if not agent_id or not target_normalized:
        return
    targets = counter.subagent_touched.setdefault(agent_id, [])
    if target_normalized not in targets:
        targets.append(target_normalized)


def take_subagent_touched(counter: LoopCounter, agent_id: str | None) -> list[str]:
    """Pop and return the targets recorded for a completing subagent.

    ``agent_id`` empty/``None`` is the fail-safe case: the harness did not
    populate the field, so every recorded subagent entry is drained. That
    over-clears, but only ever across targets a subagent actually touched —
    strictly bounded, and preferable to leaving a finished drafter's budget
    wedged (PLAN-0094 D1). The main agent's own targets are never in this dict,
    so they cannot be laundered through a spawn.
    """
    if agent_id:
        return counter.subagent_touched.pop(agent_id, [])
    drained: list[str] = []
    for targets in counter.subagent_touched.values():
        for target in targets:
            if target not in drained:
                drained.append(target)
    counter.subagent_touched.clear()
    return drained


def reset_untouched_l1(counter: LoopCounter) -> list[str]:
    """Reset L1 counters whose targets are NOT in ``turn_touched``.

    Called on every ``Stop`` event by Step 4. Returns the list of
    targets that were reset (for logging / Telegram debug). Implements
    the "target file untouched on the next turn-boundary marker" reset
    semantic from PLAN §Step 1.
    """
    reset_targets: list[str] = []
    touched = set(counter.turn_touched)
    l1_prefix = f"{LoopType.FILE_EDIT.value}:"
    # Snapshot keys before mutation
    for key in list(counter.counters):
        if not key.startswith(l1_prefix):
            continue
        target = key[len(l1_prefix) :]
        if target not in touched:
            del counter.counters[key]
            reset_targets.append(target)
    return reset_targets


def record_awaiting_ack(counter: LoopCounter, target_normalized: str) -> None:
    """Arm the acknowledged-pause exit for a target the L1 gate just denied.

    Written ONLY by the deny branch of ``pretooluse_loop_detect`` and cleared
    ONLY by a ``Stop`` that actually fires — no agent-side action touches it, so
    this is not a sanctioned version of the forbidden ``loop-counter.json``
    hand-edit (Lesson #0021 §4); that prohibition stands verbatim. Deduplicated,
    because the deny re-fires on every retry and the marker is a set, not a log.
    """
    if not target_normalized:
        return
    if target_normalized not in counter.awaiting_ack:
        counter.awaiting_ack.append(target_normalized)


def take_awaiting_ack(counter: LoopCounter) -> list[str]:
    """Pop and return every armed target. Called at a fired ``Stop``.

    The guarantee this buys is "the turn ended and Cray regained the prompt",
    not "Cray typed an ack token" — a fired stop by construction returns the
    prompt to Cray, and the agent cannot mint one. The stronger form (parsing an
    ack out of the user's message) was declined for v1: it reads conversation
    content, which is injectable, and the weaker form already beats every
    recorded incident, where Cray was present and typing but no working state
    transition existed at all.
    """
    taken = list(counter.awaiting_ack)
    counter.awaiting_ack = []
    return taken


def clear_turn_touched(counter: LoopCounter) -> None:
    """Empty the turn-touched list. Called by Step 4 after L1 reset
    so the next turn starts with a clean slate.
    """
    counter.turn_touched = []
