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
          "last_updated": ISO-8601
        }
      }
    }

Loop types map 1:1 to the L1-L4 rows in ``.claude/autonomy-triggers.md``
(Cray E.4 / ADR-013):

- L1 — same file edited >= 6 times in one turn
- L2 — same test fails >= 6 times consecutively
- L3 — same error signature seen >= 6 times
- L4 — same bash command pattern fails >= 6 times

Reset semantics are observability-driven (the *signal* gathering lives
in Step 3); this module exposes ``reset()`` so the observer can clear a
counter once the signal arrives.

Session-ID source (OQ-A, Cray-approved 2026-05-24):
``$CLAUDE_SESSION_ID`` -> ``pid-<PID>`` -> ``uuid-<UUID>`` fallback.

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
from datetime import UTC, datetime
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

    def to_json(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "last_6_actions": [a.to_json() for a in self.last_6_actions],
            "last_updated": self.last_updated,
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

    def to_json(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "counters": {k: v.to_json() for k, v in self.counters.items()},
            "turn_touched": list(self.turn_touched),
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
        return cls(
            session_id=str(data.get("session_id", "")),
            started_at=str(data.get("started_at", "")),
            counters=counters,
            turn_touched=touched,
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


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S%z")


def new_counter(session_id: str | None = None) -> LoopCounter:
    return LoopCounter(
        session_id=session_id or resolve_session_id(),
        started_at=_now_iso(),
        counters={},
    )


def load_counter(path: Path | None = None) -> LoopCounter:
    """Load LoopCounter from disk; mint a fresh one on missing/malformed.

    Never raises. A corrupted state file is treated as missing and
    silently replaced on the next save — Phase 2 state is per-session
    and reset on observable progress anyway, so the cost of losing a
    counter is bounded.
    """
    p = path or DEFAULT_COUNTER_PATH
    if not p.exists():
        return new_counter()
    try:
        raw = p.read_text(encoding="utf-8")
        if not raw.strip():
            return new_counter()
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return new_counter()
    if not isinstance(data, dict):
        return new_counter()
    return LoopCounter.from_json(data)


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


def reset_l1_for_targets(counter: LoopCounter, targets: list[str]) -> list[str]:
    """Reset the L1 counter for each given normalized target; return those cleared.

    Used at the subagent (Agent/Task) completion boundary so a subagent's edits
    do not consume the main agent's L1 budget for the same file — symmetric with
    the commit-boundary (:func:`reset` on commit) and Stop turn-boundary
    (:func:`reset_untouched_l1`) resets.
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


def clear_turn_touched(counter: LoopCounter) -> None:
    """Empty the turn-touched list. Called by Step 4 after L1 reset
    so the next turn starts with a clean slate.
    """
    counter.turn_touched = []
