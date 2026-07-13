"""Goal-state primitives for the Axis-B verification loop (PLAN-0021 Step 1;
PLAN-0069 PR1 = the v2 schema — enforce flag + amendments[] log + the
blocked-pending-human status).

State file: ``.claude/state/goal.json`` (gitignored, per-session goal). Read +
written by ``_goal_gate.py`` (PLAN-0021 Step 2) at every ``Stop`` event;
written by the ``goal-evaluator`` subagent (verdict append — its ``Write`` is
hook-narrowed to exactly this file per ADR-0018 SD-1) and by the ``/goal``
command via the main agent. This module ships only the schema, tolerant
parsing, and atomic I/O; the gate's decision logic lands in Step 2.

Schema (ADR-0018 §Minimal-prototype spec 1; §V2 Amendment)::

    {
      "schema_version": 2,
      "goal": "one-sentence goal statement",
      "source": "docs/plans/0011-xxx.md#acceptance-criteria",   // optional
      "session": 51,
      "created": "2026-06-10T02:12:00+07:00",
      "status": "active",          // active | passed | released-unevaluated | blocked-pending-human
      "enforce": false,            // V2: per-goal opt-in enforcement (default false = warn-only v1)
      "criteria": [
        {"id": "C1", "kind": "check", "cmd": "pytest -q",
         "desc": "test suite green", "timeout_s": 300},
        {"id": "C3", "kind": "judge",
         "desc": "the drafted ADR resolves OQ-1..OQ-7 with decisions"}
      ],
      "evaluations": [             // append-only verdict trail
        {"ts": "...", "fingerprint": "<work-state marker>",
         "deterministic": {"C1": "pass"},
         "judged": {"C3": {"verdict": "FAIL", "reason": "...",
                            "confidence": "medium"}},
         "evaluator": "goal-evaluator",
         "amendments_seen": 0}     // V2: len(amendments) when written (SD-D freshness anchor)
      ],
      "amendments": [              // V2: append-only ratification log (typed Cray sign-off ONLY)
        {"ts": "...", "event": "ask_user_question:<label>",
         "summary": "redirected to X", "prev_goal": "...", "new_goal": "...",
         "fingerprint": "<work-state marker at ratification>"}
      ]
    }

Tolerance contract (AC-1): a **missing, empty, or malformed** ``goal.json`` is
*no active goal* — ``load_goal()`` returns ``None`` and never raises. Unknown
fields are ignored on parse and dropped on rewrite — which is exactly why the
v2 ``enforce`` / ``amendments`` fields are FIRST-CLASS dataclass fields
(PLAN-0069 AC-1 build hazard i): an unknown field on disk would be silently
stripped by the gate's next ``save_goal`` rewrite. The goal file is a
**derived projection** of its ``source`` contract (ADR-0017 D3/D6 discipline);
on divergence the PLAN wins.

Stdlib-only (no Pydantic) — hooks run as subprocesses and must start fast.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from _loop_counter import STATE_DIR

DEFAULT_GOAL_PATH = STATE_DIR / "goal.json"

SCHEMA_VERSION = 2

STATUS_ACTIVE = "active"
STATUS_PASSED = "passed"
STATUS_RELEASED_UNEVALUATED = "released-unevaluated"
# V2 (ADR-0018 V2 / L-4 / SD-4): evidence-missing under enforce, or a re-Stop
# still failing, parks the goal here — a human must clear / re-declare / ratify.
# NEVER a silent pass and NEVER released-unevaluated. A v1 reader that predates
# this status rejects it at ``Goal.from_json`` -> ``None`` -> stands down (the
# fail-safe skew direction, PLAN-0069 AC-4b).
STATUS_BLOCKED_PENDING_HUMAN = "blocked-pending-human"
VALID_STATUSES = frozenset(
    {
        STATUS_ACTIVE,
        STATUS_PASSED,
        STATUS_RELEASED_UNEVALUATED,
        STATUS_BLOCKED_PENDING_HUMAN,
    }
)

KIND_CHECK = "check"
KIND_JUDGE = "judge"
VALID_KINDS = frozenset({KIND_CHECK, KIND_JUDGE})


def _parse_criteria(raw: Any) -> list[Criterion]:
    """Tolerant criteria-list parse — junk entries skipped, never fatal."""
    criteria: list[Criterion] = []
    if isinstance(raw, list):
        for c in raw:
            if isinstance(c, dict):
                parsed = Criterion.from_json(c)
                if parsed is not None:
                    criteria.append(parsed)
    return criteria


def _parse_evaluations(raw: Any) -> list[Evaluation]:
    """Tolerant evaluations-trail parse — non-dict entries skipped."""
    evaluations: list[Evaluation] = []
    if isinstance(raw, list):
        for e in raw:
            if isinstance(e, dict):
                evaluations.append(Evaluation.from_json(e))
    return evaluations


def _parse_amendments(raw: Any) -> list[Amendment]:
    """Tolerant amendments-log parse — junk entries skipped, never fatal
    (mirrors ``_parse_criteria``). The surviving count is load-bearing: the
    SD-D positional freshness rule compares ``len(amendments)`` against an
    evaluation's recorded ``amendments_seen`` (clock-free, because the WSL
    wall clock is non-monotonic and wall-clock ordering is barred).
    """
    amendments: list[Amendment] = []
    if isinstance(raw, list):
        for a in raw:
            if isinstance(a, dict):
                parsed = Amendment.from_json(a)
                if parsed is not None:
                    amendments.append(parsed)
    return amendments


def goal_path() -> Path:
    """Resolve the goal file path. ``$CLAUDE_GOAL_PATH`` overrides for tests
    (the ``CLAUDE_*`` override family pattern shared with the Step 2/3/4 hooks).
    """
    override = os.environ.get("CLAUDE_GOAL_PATH")
    return Path(override) if override else DEFAULT_GOAL_PATH


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S%z")


@dataclass
class Criterion:
    """One acceptance criterion — ``check`` (exit-code answerable, has ``cmd``
    + ``timeout_s``) or ``judge`` (LLM residue, ``desc`` only). The D1 split
    rule: *if you can write it as a command whose exit code answers it, you
    must.* Validation is the gate's job (Step 2); parsing stays tolerant.
    """

    id: str
    kind: str
    desc: str = ""
    cmd: str = ""
    timeout_s: int | None = None

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {"id": self.id, "kind": self.kind, "desc": self.desc}
        if self.kind == KIND_CHECK:
            out["cmd"] = self.cmd
            if self.timeout_s is not None:
                out["timeout_s"] = self.timeout_s
        return out

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Criterion | None:
        """Tolerant parse; ``None`` for an entry that cannot be a criterion
        (missing/invalid ``id`` or ``kind``) — the caller skips it.
        """
        crit_id = data.get("id")
        kind = data.get("kind")
        if not isinstance(crit_id, str) or not crit_id:
            return None
        if not isinstance(kind, str) or kind not in VALID_KINDS:
            return None
        timeout_raw = data.get("timeout_s")
        timeout_s: int | None = None
        if isinstance(timeout_raw, int) and not isinstance(timeout_raw, bool) and timeout_raw > 0:
            timeout_s = timeout_raw
        return cls(
            id=crit_id,
            kind=kind,
            desc=str(data.get("desc", "")),
            cmd=str(data.get("cmd", "")),
            timeout_s=timeout_s,
        )


@dataclass
class Evaluation:
    """One entry in the append-only ``evaluations[]`` verdict trail.

    V2 (ADR-0018 V2) adds two optional instrumentation fields: ``amendments_seen``
    (``len(amendments)`` at the moment this verdict was written — the SD-D
    positional freshness anchor, clock-free because the WSL wall clock is
    non-monotonic) and ``divergence`` (the evaluator's V2-D2 anchor-alignment
    verdict — ``{"verdict": "ALIGNED"|"DIVERGENT", "reason": ...}``). Both
    default empty, so a v1 evaluation round-trips unchanged in meaning.
    """

    ts: str
    fingerprint: str = ""
    deterministic: dict[str, str] = field(default_factory=dict)
    judged: dict[str, dict[str, str]] = field(default_factory=dict)
    evaluator: str = ""
    amendments_seen: int = 0
    divergence: dict[str, str] | None = None

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "ts": self.ts,
            "fingerprint": self.fingerprint,
            "deterministic": dict(self.deterministic),
            "judged": {k: dict(v) for k, v in self.judged.items()},
            "evaluator": self.evaluator,
            "amendments_seen": self.amendments_seen,
        }
        if self.divergence is not None:
            out["divergence"] = dict(self.divergence)
        return out

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Evaluation:
        det_raw = data.get("deterministic") or {}
        deterministic: dict[str, str] = {}
        if isinstance(det_raw, dict):
            deterministic = {str(k): str(v) for k, v in det_raw.items()}
        judged_raw = data.get("judged") or {}
        judged: dict[str, dict[str, str]] = {}
        if isinstance(judged_raw, dict):
            for k, v in judged_raw.items():
                if isinstance(v, dict):
                    judged[str(k)] = {str(vk): str(vv) for vk, vv in v.items()}
        seen_raw = data.get("amendments_seen")
        amendments_seen = (
            seen_raw if isinstance(seen_raw, int) and not isinstance(seen_raw, bool) else 0
        )
        div_raw = data.get("divergence")
        divergence: dict[str, str] | None = None
        if isinstance(div_raw, dict):
            divergence = {str(k): str(v) for k, v in div_raw.items()}
        return cls(
            ts=str(data.get("ts", "")),
            fingerprint=str(data.get("fingerprint", "")),
            deterministic=deterministic,
            judged=judged,
            evaluator=str(data.get("evaluator", "")),
            amendments_seen=amendments_seen,
            divergence=divergence,
        )


@dataclass
class Amendment:
    """One entry in the append-only ``amendments[]`` ratification log (ADR-0018
    V2 SD-2 / L-2). A **typed Cray sign-off** that redirected the goal — the
    only thing that turns a divergence from *drift* (flagged/blocked) into
    *redirect* (passes). A Stop-hook "proceed", a Code inference, or a subagent
    suggestion NEVER appends here — that gap is the whole point of the log.
    """

    ts: str
    event: str = ""  # "typed" | "ask_user_question:<label>"
    summary: str = ""
    prev_goal: str = ""
    new_goal: str = ""
    fingerprint: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "ts": self.ts,
            "event": self.event,
            "summary": self.summary,
            "prev_goal": self.prev_goal,
            "new_goal": self.new_goal,
            "fingerprint": self.fingerprint,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Amendment | None:
        """Tolerant parse; ``None`` for an entry that cannot be an amendment
        (missing/empty ``ts``) — the caller skips it (like ``Criterion``).
        """
        ts = data.get("ts")
        if not isinstance(ts, str) or not ts:
            return None
        return cls(
            ts=ts,
            event=str(data.get("event", "")),
            summary=str(data.get("summary", "")),
            prev_goal=str(data.get("prev_goal", "")),
            new_goal=str(data.get("new_goal", "")),
            fingerprint=str(data.get("fingerprint", "")),
        )


@dataclass
class Goal:
    """Top-level goal document (``.claude/state/goal.json``)."""

    goal: str
    status: str = STATUS_ACTIVE
    source: str = ""
    session: int = 0
    created: str = ""
    schema_version: int = SCHEMA_VERSION
    enforce: bool = False
    criteria: list[Criterion] = field(default_factory=list)
    evaluations: list[Evaluation] = field(default_factory=list)
    amendments: list[Amendment] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "schema_version": self.schema_version,
            "goal": self.goal,
            "session": self.session,
            "created": self.created,
            "status": self.status,
            "enforce": self.enforce,
            "criteria": [c.to_json() for c in self.criteria],
            "evaluations": [e.to_json() for e in self.evaluations],
            "amendments": [a.to_json() for a in self.amendments],
        }
        if self.source:
            out["source"] = self.source
        return out

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Goal | None:
        """Tolerant parse; ``None`` when the document cannot be a goal
        (missing/empty ``goal`` statement or invalid ``status``) — the caller
        treats ``None`` as *no active goal* (AC-1). A v1 file (no ``enforce``,
        no ``amendments``) parses with ``enforce=False`` + ``amendments=[]``
        and full v1 semantics (PLAN-0069 AC-4a).
        """
        goal_text = data.get("goal")
        if not isinstance(goal_text, str) or not goal_text.strip():
            return None
        status = data.get("status")
        if not isinstance(status, str) or status not in VALID_STATUSES:
            return None
        session_raw = data.get("session")
        session = 0
        if isinstance(session_raw, int) and not isinstance(session_raw, bool):
            session = session_raw
        enforce_raw = data.get("enforce")
        enforce = enforce_raw if isinstance(enforce_raw, bool) else False
        return cls(
            goal=goal_text,
            status=status,
            source=str(data.get("source", "")),
            session=session,
            created=str(data.get("created", "")),
            schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
            enforce=enforce,
            criteria=_parse_criteria(data.get("criteria")),
            evaluations=_parse_evaluations(data.get("evaluations")),
            amendments=_parse_amendments(data.get("amendments")),
        )

    def check_criteria(self) -> list[Criterion]:
        return [c for c in self.criteria if c.kind == KIND_CHECK]

    def judge_criteria(self) -> list[Criterion]:
        return [c for c in self.criteria if c.kind == KIND_JUDGE]

    def last_evaluation(self) -> Evaluation | None:
        return self.evaluations[-1] if self.evaluations else None


def load_goal(path: Path | None = None) -> Goal | None:
    """Load the goal document; ``None`` = no active goal.

    Never raises (AC-1): a missing, empty, or malformed file — including
    non-dict JSON, invalid status, or a missing goal statement — is treated
    as *no active goal* with at most one stderr note from the caller. The
    gate falls through to today's classifier flow in that case.
    """
    p = path or goal_path()
    if not p.exists():
        return None
    try:
        raw = p.read_text(encoding="utf-8")
        if not raw.strip():
            return None
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    return Goal.from_json(data)


def save_goal(goal: Goal, path: Path | None = None) -> None:
    """Atomic write via tmpfile + ``os.replace`` (the ``_save_chain`` /
    ``save_counter`` pattern): tmpfile in the target directory so the replace
    is atomic on one filesystem; readers see old-or-new, never partial;
    last-writer-wins (VX-3 — the gate and the evaluator write at different
    points of the Stop cycle, so no simultaneous same-file writers exist by
    construction).
    """
    p = path or goal_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(goal.to_json(), indent=2, sort_keys=True)
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


def new_goal(
    goal_text: str,
    criteria: list[Criterion],
    source: str = "",
    session: int = 0,
    enforce: bool = False,
) -> Goal:
    return Goal(
        goal=goal_text,
        status=STATUS_ACTIVE,
        source=source,
        session=session,
        created=_now_iso(),
        enforce=enforce,
        criteria=criteria,
    )


def record_evaluation(goal: Goal, evaluation: Evaluation) -> None:
    """Append to the ``evaluations[]`` trail (append-only — never rewrites or
    drops prior entries; the trail is the durable evidence ADR-0018 D7 cites).
    """
    goal.evaluations.append(evaluation)


def record_amendment(goal: Goal, amendment: Amendment) -> None:
    """Append to the ``amendments[]`` ratification log (append-only, V2 SD-2 /
    L-2). Only a typed Cray sign-off reaches here — the caller (the ``/goal``
    main-agent path) is responsible for that gate; this function is the pure
    append primitive, symmetric with ``record_evaluation``.
    """
    goal.amendments.append(amendment)
