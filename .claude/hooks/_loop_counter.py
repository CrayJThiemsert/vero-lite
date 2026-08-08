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

- L1 — same file edited repeatedly. **RETIRED by PLAN-0102**, and no
  :class:`LoopType` member remains for it. It keyed on the same *file*; the
  three below key on the same *problem*, which is what ADR-013 E.4 actually
  ratified. Across its entire live history it recorded zero true positives
  while hard-walling legitimate construction sequences.
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

# PLAN-0102 removed three L1 tuning constants that stood here —
# ``MAX_CONTENT_HASHES`` (the per-turn oscillation-digest cap),
# ``L1_DOC_THRESHOLD`` (the 15-edit prose bar) and ``L1_GRACE_BUDGET`` (the
# Cray-ratified G = 3 rope between warn and wall). All three tuned a guard that
# no longer exists. They are named here rather than merely deleted because each
# was a Cray-ratified number, and a future reader finding the L1 history in
# ``docs/lessons/0021-*`` should be able to tell that the values were retired
# WITH the guard rather than lost.

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
    """L2-L4 loop-detection rows from ``.claude/autonomy-triggers.md``.

    Values match the registry row IDs so Step 2/3 hooks + Step 5
    classifier share one vocabulary.

    ``FILE_EDIT = "L1"`` was removed by PLAN-0102. **Nothing reconstructs a
    :class:`LoopType` from a stored key** — :meth:`LoopCounter.from_json` keeps
    counter keys as plain strings and :func:`prune_stale_entries` iterates them
    as strings — so a state file still carrying ``L1:`` entries loads without
    raising; the keys are simply never matched again, and age-out drops them.
    That property is what PLAN-0102 AC-5 asserts behaviourally, because a
    ``LoopType("L1")`` on any load path would raise ``ValueError`` at hook start.
    """

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


def _digest_tally(raw: Any) -> dict[str, int]:
    """Coerce a persisted digest->count map, dropping anything malformed.

    Tolerant by contract (PLAN-0094 D4): these fields are ADDITIVE, so a state
    file written before Step 4 has no key at all and must read back as an empty
    map rather than raise. A non-int or non-str member is dropped rather than
    coerced -- a corrupt tally must not be able to manufacture an increment.
    """
    if not isinstance(raw, dict):
        return {}
    out: dict[str, int] = {}
    for k, v in raw.items():
        if isinstance(k, str) and isinstance(v, int) and not isinstance(v, bool) and v > 0:
            out[k] = v
    return out


@dataclass
class CounterEntry:
    """A single ``(loop_type, target)`` counter."""

    count: int = 0
    last_6_actions: list[ActionRecord] = field(default_factory=list)
    last_updated: str = ""
    warned_at: str = ""
    """ISO stamp of the L1 warn ping. **INERT since PLAN-0102 — nothing writes it.**

    Retained deliberately under this file's "excise behaviour, tolerate schema"
    rule: the field is additive by contract, so leaving it costs nothing, while
    removing it would enlarge the diff in the layer L2/L3/L4 still depend on for
    exactly zero behaviour change. It reads back ``""`` on every entry.
    """

    attempted_edits: dict[str, int] = field(default_factory=dict)
    """``sha1(old_string) -> times applied``. **INERT since PLAN-0102.**

    Was L1's non-progress tally (PLAN-0094 D4 b) — a dict rather than a set so
    it could carry the N in ``repeat xN``. Retained on the same
    tolerate-schema grounds as :attr:`warned_at`; nothing writes it and nothing
    clears it, because the turn-scoped clear was itself an L1 reset path.
    """

    content_hashes: dict[str, int] = field(default_factory=dict)
    """``sha1(file content after the write) -> times seen``. **INERT since PLAN-0102.**

    Was L1's oscillation signal (PLAN-0094 D4 c): a digest seen twice meant the
    file had returned to a state it already held that turn. Its eviction cap
    retired with it — there is no writer left to bound.
    """

    def to_json(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "last_6_actions": [a.to_json() for a in self.last_6_actions],
            "last_updated": self.last_updated,
            "warned_at": self.warned_at,
            # Both MUST round-trip: every Stop rewrites the whole document via
            # this method, so a field the writer forgets is a field the reader
            # silently loses at the next turn boundary (the AC-9 finding).
            "attempted_edits": dict(self.attempted_edits),
            "content_hashes": dict(self.content_hashes),
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
            attempted_edits=_digest_tally(data.get("attempted_edits")),
            content_hashes=_digest_tally(data.get("content_hashes")),
        )


@dataclass
class LoopCounter:
    """Top-level state document (``.claude/state/loop-counter.json``).

    **PLAN-0102 removed three top-level fields with L1** — ``turn_touched``
    (paths Written/Edited this turn, read by the Stop hook's turn-boundary
    reset), ``subagent_touched`` (per-``agent_id`` attribution for the
    SubagentStop reset, PLAN-0094 D1) and ``awaiting_ack`` (the
    acknowledged-pause marker, PLAN-0094 D5). Every one of them existed to feed
    an L1 reset path, and a hooks-wide reference sweep found no consumer
    outside those paths — so they are eliminated rather than kept "in case".

    A state file written before the retirement still carries all three keys.
    :meth:`from_json` reads through ``data.get`` and simply never looks at
    them, so an old file loads clean and the keys drop out on the next save
    (PLAN-0102 AC-5).
    """

    session_id: str
    started_at: str
    counters: dict[str, CounterEntry] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "counters": {k: v.to_json() for k, v in self.counters.items()},
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> LoopCounter:
        counters_raw = data.get("counters") or {}
        counters: dict[str, CounterEntry] = {}
        if isinstance(counters_raw, dict):
            for k, v in counters_raw.items():
                if isinstance(v, dict):
                    counters[str(k)] = CounterEntry.from_json(v)
        # ``turn_touched`` / ``subagent_touched`` / ``awaiting_ack`` were read
        # here until PLAN-0102. They are now simply not looked at: a
        # pre-retirement state file still carrying them loads clean and sheds
        # them on the next save. Reading through ``data.get`` throughout is what
        # makes that true without a migration (AC-5).
        return cls(
            session_id=str(data.get("session_id", "")),
            started_at=str(data.get("started_at", "")),
            counters=counters,
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
    return _record(counter, loop_type, target_normalized, action, bump=True)


def observe(
    counter: LoopCounter,
    loop_type: LoopType,
    target_normalized: str,
    action: ActionRecord | None = None,
) -> CounterEntry:
    """Record an action WITHOUT incrementing the count (PLAN-0094 D4).

    The record-only sibling of :func:`increment`, which couples the two. L1's
    unit is now *non-progress*, so a distinct forward edit must still land in
    the evidence ring and refresh ``last_updated`` -- it just must not score.
    Splitting the two is what lets "six distinct forward edits leave count == 0"
    (AC-7) coexist with an evidence trail that still shows all six.

    Refreshing ``last_updated`` is deliberate: an actively-edited target must
    not age out from under the guard just because its edits are all forward.
    """
    return _record(counter, loop_type, target_normalized, action, bump=False)


def _record(
    counter: LoopCounter,
    loop_type: LoopType,
    target_normalized: str,
    action: ActionRecord | None,
    *,
    bump: bool,
) -> CounterEntry:
    """Shared body of :func:`increment` / :func:`observe`.

    One implementation on purpose: if the ring-buffer or timestamp handling
    drifted between the counting and non-counting paths, the evidence for a
    trip would differ from the evidence for the edits that led to it.
    """
    key = counter_key(loop_type, target_normalized)
    entry = counter.counters.get(key) or CounterEntry()
    if bump:
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
