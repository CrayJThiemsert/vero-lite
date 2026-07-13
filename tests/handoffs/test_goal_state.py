"""Tests for ``.claude/hooks/_goal_state.py`` (PLAN-0021 Step 1, AC-1).

Covers (matrix rows: concurrency [state half] + AC-1 tolerance families):

- Schema round-trip (Goal <-> JSON, criteria kinds, evaluations trail)
- Tolerant parse: missing / empty / malformed file, non-dict root, missing
  goal statement, invalid status, junk criteria entries, unknown fields
  ignored — all -> ``None`` / skipped, never a raise (AC-1)
- Atomic write (tmpfile + ``os.replace``; no partial-write window; mid-replace
  readers see old-or-new — VX-3)
- ``CLAUDE_GOAL_PATH`` env override honored by ``goal_path``/``load_goal``/
  ``save_goal``
- ``record_evaluation`` append-only trail
"""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path
from typing import Any

import pytest

HOOKS_DIR = Path(__file__).resolve().parents[2] / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from _goal_state import (  # noqa: E402  — sys.path manipulation above
    DEFAULT_GOAL_PATH,
    SCHEMA_VERSION,
    STATUS_ACTIVE,
    STATUS_BLOCKED_PENDING_HUMAN,
    STATUS_PASSED,
    Amendment,
    Criterion,
    Evaluation,
    Goal,
    goal_path,
    load_goal,
    new_goal,
    record_amendment,
    record_evaluation,
    save_goal,
)


def _sample_goal() -> Goal:
    return new_goal(
        goal_text="ship the widget",
        criteria=[
            Criterion(id="C1", kind="check", cmd="pytest -q", desc="suite green", timeout_s=300),
            Criterion(id="C2", kind="judge", desc="ADR resolves every OQ"),
        ],
        source="docs/plans/0099-widget.md#acceptance-criteria",
        session=51,
    )


class TestRoundTrip:
    def test_goal_round_trips_through_json(self, tmp_path: Path) -> None:
        goal = _sample_goal()
        record_evaluation(
            goal,
            Evaluation(
                ts="2026-06-10T04:00:00+0000",
                fingerprint="fp-1",
                deterministic={"C1": "pass"},
                judged={
                    "C2": {"verdict": "FAIL", "reason": "OQ-3 unresolved", "confidence": "medium"}
                },
                evaluator="goal-evaluator",
            ),
        )
        p = tmp_path / "goal.json"
        save_goal(goal, p)
        loaded = load_goal(p)
        assert loaded is not None
        assert loaded.goal == "ship the widget"
        assert loaded.status == STATUS_ACTIVE
        assert loaded.source.endswith("#acceptance-criteria")
        assert loaded.session == 51
        assert [c.id for c in loaded.criteria] == ["C1", "C2"]
        assert loaded.check_criteria()[0].cmd == "pytest -q"
        assert loaded.check_criteria()[0].timeout_s == 300
        assert loaded.judge_criteria()[0].id == "C2"
        last = loaded.last_evaluation()
        assert last is not None
        assert last.deterministic == {"C1": "pass"}
        assert last.judged["C2"]["verdict"] == "FAIL"
        assert last.evaluator == "goal-evaluator"

    def test_judge_criterion_serializes_without_cmd_fields(self) -> None:
        goal = _sample_goal()
        data = goal.to_json()
        judge_row = next(c for c in data["criteria"] if c["kind"] == "judge")
        assert "cmd" not in judge_row
        assert "timeout_s" not in judge_row


class TestToleranceFamilies:
    """AC-1: missing / empty / malformed -> no active goal, never a raise."""

    def test_missing_file_returns_none(self, tmp_path: Path) -> None:
        assert load_goal(tmp_path / "absent.json") is None

    def test_empty_file_returns_none(self, tmp_path: Path) -> None:
        p = tmp_path / "goal.json"
        p.write_text("", encoding="utf-8")
        assert load_goal(p) is None

    @pytest.mark.parametrize(
        "raw",
        [
            "{not json",
            "[]",
            '"a string"',
            "42",
            "null",
        ],
        ids=["malformed", "list-root", "string-root", "int-root", "null-root"],
    )
    def test_non_goal_documents_return_none(self, tmp_path: Path, raw: str) -> None:
        p = tmp_path / "goal.json"
        p.write_text(raw, encoding="utf-8")
        assert load_goal(p) is None

    @pytest.mark.parametrize(
        "doc",
        [
            {"status": "active"},  # no goal statement
            {"goal": "", "status": "active"},  # empty goal
            {"goal": "   ", "status": "active"},  # whitespace goal
            {"goal": "x", "status": "bogus"},  # invalid status
            {"goal": "x"},  # missing status
        ],
        ids=["no-goal", "empty-goal", "ws-goal", "bad-status", "no-status"],
    )
    def test_invalid_goal_documents_return_none(self, tmp_path: Path, doc: dict[str, Any]) -> None:
        p = tmp_path / "goal.json"
        p.write_text(json.dumps(doc), encoding="utf-8")
        assert load_goal(p) is None

    def test_junk_criteria_entries_are_skipped_not_fatal(self, tmp_path: Path) -> None:
        doc = {
            "goal": "x",
            "status": "active",
            "criteria": [
                {"id": "C1", "kind": "check", "cmd": "true", "timeout_s": 5},
                {"kind": "check", "cmd": "true"},  # missing id
                {"id": "C3", "kind": "bogus"},  # invalid kind
                "not-a-dict",
                {"id": "C4", "kind": "judge", "desc": "ok"},
            ],
        }
        p = tmp_path / "goal.json"
        p.write_text(json.dumps(doc), encoding="utf-8")
        loaded = load_goal(p)
        assert loaded is not None
        assert [c.id for c in loaded.criteria] == ["C1", "C4"]

    def test_unknown_fields_ignored(self, tmp_path: Path) -> None:
        doc = {
            "goal": "x",
            "status": "passed",
            "mystery": {"nested": True},
            "criteria": [],
        }
        p = tmp_path / "goal.json"
        p.write_text(json.dumps(doc), encoding="utf-8")
        loaded = load_goal(p)
        assert loaded is not None
        assert loaded.status == STATUS_PASSED

    def test_bool_session_and_timeout_rejected(self, tmp_path: Path) -> None:
        doc = {
            "goal": "x",
            "status": "active",
            "session": True,
            "criteria": [{"id": "C1", "kind": "check", "cmd": "true", "timeout_s": True}],
        }
        p = tmp_path / "goal.json"
        p.write_text(json.dumps(doc), encoding="utf-8")
        loaded = load_goal(p)
        assert loaded is not None
        assert loaded.session == 0
        assert loaded.criteria[0].timeout_s is None


class TestAtomicity:
    def test_save_leaves_no_tmp_residue_and_is_loadable(self, tmp_path: Path) -> None:
        p = tmp_path / "goal.json"
        save_goal(_sample_goal(), p)
        assert load_goal(p) is not None
        residue = [f for f in tmp_path.iterdir() if f.name != "goal.json"]
        assert residue == []

    def test_concurrent_writers_never_corrupt(self, tmp_path: Path) -> None:
        """VX-3 stress row (state half): racing writers; readers always see a
        complete document (old-or-new, never partial)."""
        p = tmp_path / "goal.json"
        save_goal(_sample_goal(), p)
        errors: list[str] = []

        def writer(n: int) -> None:
            g = _sample_goal()
            g.goal = f"goal-{n}"
            for _ in range(20):
                save_goal(g, p)

        def reader() -> None:
            for _ in range(100):
                loaded = load_goal(p)
                # None would mean a partial/corrupt read of an existing file
                if loaded is None:
                    errors.append("reader saw corrupt/partial goal.json")
                    return

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(4)]
        threads.append(threading.Thread(target=reader))
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []
        final = load_goal(p)
        assert final is not None
        assert final.goal.startswith("goal-")


class TestEnvOverride:
    def test_goal_path_honors_env(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        override = tmp_path / "elsewhere" / "goal.json"
        monkeypatch.setenv("CLAUDE_GOAL_PATH", str(override))
        assert goal_path() == override
        save_goal(_sample_goal(), None)  # None -> resolves via goal_path()
        assert override.exists()
        loaded = load_goal(None)
        assert loaded is not None and loaded.goal == "ship the widget"

    def test_default_path_without_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("CLAUDE_GOAL_PATH", raising=False)
        assert goal_path() == DEFAULT_GOAL_PATH


class TestAppendOnlyTrail:
    def test_record_evaluation_appends_and_preserves(self, tmp_path: Path) -> None:
        goal = _sample_goal()
        for i in range(3):
            record_evaluation(goal, Evaluation(ts=f"t{i}", fingerprint=f"fp{i}"))
        assert [e.ts for e in goal.evaluations] == ["t0", "t1", "t2"]
        p = tmp_path / "goal.json"
        save_goal(goal, p)
        loaded = load_goal(p)
        assert loaded is not None
        assert [e.fingerprint for e in loaded.evaluations] == ["fp0", "fp1", "fp2"]


# ---------------------------------------------------------------------------
# PLAN-0069 PR1 — v2 schema (enforce + amendments[] + blocked-pending-human)
# ---------------------------------------------------------------------------


def _v2_goal_with_amendment() -> Goal:
    """A v2 goal carrying enforce=True and one amendment — the ratification
    log's minimal non-empty shape."""
    goal = new_goal(
        goal_text="ship the widget",
        criteria=[Criterion(id="C1", kind="check", cmd="pytest -q", desc="suite", timeout_s=60)],
        source="docs/plans/0099-widget.md#ac",
        session=124,
        enforce=True,
    )
    record_amendment(
        goal,
        Amendment(
            ts="2026-07-13T14:00:00+0000",
            event="ask_user_question:merge-720",
            summary="redirected to the enforce build",
            prev_goal="ship the widget",
            new_goal="ship the enforcing gate",
            fingerprint="fp-ratify-1",
        ),
    )
    return goal


class TestV2Schema:
    def test_new_goal_defaults_to_v2_warn(self) -> None:
        """A freshly declared goal is schema_version 2 and enforce=False
        (default = warn-only v1 behavior, L-1)."""
        goal = new_goal(goal_text="x", criteria=[])
        assert goal.schema_version == SCHEMA_VERSION == 2
        assert goal.enforce is False
        assert goal.amendments == []

    def test_enforce_and_amendments_are_first_class_fields(self, tmp_path: Path) -> None:
        """AC-1 (build hazard i — silent-strip): enforce + amendments survive
        the gate's OWN rewrite path (load -> mutate -> save). The module drops
        UNKNOWN fields on rewrite, so this holds only because they are real
        Goal dataclass fields."""
        p = tmp_path / "goal.json"
        save_goal(_v2_goal_with_amendment(), p)
        loaded = load_goal(p)
        assert loaded is not None
        assert loaded.enforce is True
        assert len(loaded.amendments) == 1
        # the gate's rewrite path: append an evaluation, re-save
        record_evaluation(loaded, Evaluation(ts="t1", fingerprint="fp1", amendments_seen=1))
        save_goal(loaded, p)
        rewritten = load_goal(p)
        assert rewritten is not None
        assert rewritten.enforce is True
        assert [a.fingerprint for a in rewritten.amendments] == ["fp-ratify-1"]
        assert rewritten.amendments[0].event == "ask_user_question:merge-720"
        assert rewritten.amendments[0].new_goal == "ship the enforcing gate"
        # the raw bytes carry them too (defensive against a to_json gap)
        raw = json.loads(p.read_text(encoding="utf-8"))
        assert raw["enforce"] is True
        assert raw["amendments"][0]["fingerprint"] == "fp-ratify-1"

    def test_v1_file_parses_with_v2_defaults(self, tmp_path: Path) -> None:
        """AC-4a: a v1 file (schema_version 1, no enforce, no amendments) reads
        with enforce=False, amendments=[], full v1 semantics; schema_version is
        passed through (not force-upgraded)."""
        doc = {
            "schema_version": 1,
            "goal": "legacy goal",
            "status": "active",
            "criteria": [{"id": "C1", "kind": "check", "cmd": "true"}],
            "evaluations": [{"ts": "t0", "fingerprint": "fp0"}],
        }
        p = tmp_path / "goal.json"
        p.write_text(json.dumps(doc), encoding="utf-8")
        loaded = load_goal(p)
        assert loaded is not None
        assert loaded.enforce is False
        assert loaded.amendments == []
        assert loaded.schema_version == 1  # passthrough
        assert loaded.goal == "legacy goal"
        assert [c.id for c in loaded.criteria] == ["C1"]
        # a v1 evaluation with no v2 instrumentation defaults cleanly
        assert loaded.evaluations[0].amendments_seen == 0
        assert loaded.evaluations[0].divergence is None

    def test_amendments_seen_and_divergence_round_trip(self, tmp_path: Path) -> None:
        """SD-D + V2-D2 instrumentation survives round-trip; divergence is
        omitted from the bytes when None (kept optional)."""
        goal = new_goal(goal_text="x", criteria=[])
        record_evaluation(
            goal,
            Evaluation(
                ts="t1",
                fingerprint="fp1",
                amendments_seen=2,
                divergence={"verdict": "DIVERGENT", "reason": "off-anchor"},
            ),
        )
        p = tmp_path / "goal.json"
        save_goal(goal, p)
        loaded = load_goal(p)
        assert loaded is not None
        ev = loaded.evaluations[0]
        assert ev.amendments_seen == 2
        assert ev.divergence == {"verdict": "DIVERGENT", "reason": "off-anchor"}
        raw = json.loads(p.read_text(encoding="utf-8"))
        assert "divergence" in raw["evaluations"][0]
        # an evaluation with no divergence does not emit the key
        goal2 = new_goal(goal_text="y", criteria=[])
        record_evaluation(goal2, Evaluation(ts="t2", fingerprint="fp2"))
        p2 = tmp_path / "goal2.json"
        save_goal(goal2, p2)
        raw2 = json.loads(p2.read_text(encoding="utf-8"))
        assert "divergence" not in raw2["evaluations"][0]
        assert raw2["evaluations"][0]["amendments_seen"] == 0

    def test_junk_amendment_entries_skipped(self, tmp_path: Path) -> None:
        """Tolerant amendments parse — non-dict and ts-less entries skipped,
        never fatal (mirrors junk-criteria)."""
        doc = {
            "goal": "x",
            "status": "active",
            "amendments": [
                {"ts": "t1", "event": "typed", "summary": "ok"},
                {"event": "typed"},  # no ts -> skipped
                "not-a-dict",
                {"ts": "", "summary": "empty ts"},  # empty ts -> skipped
                {"ts": "t2"},
            ],
        }
        p = tmp_path / "goal.json"
        p.write_text(json.dumps(doc), encoding="utf-8")
        loaded = load_goal(p)
        assert loaded is not None
        assert [a.ts for a in loaded.amendments] == ["t1", "t2"]


class TestBlockedPendingHumanStatus:
    def test_blocked_pending_human_parses_as_real_goal(self, tmp_path: Path) -> None:
        """AC-2 (build hazard ii): blocked-pending-human is a VALID status — the
        file loads as a real goal (not None), so the gate can stand down on it
        without the goal ever transitioning to passed."""
        doc = {
            "schema_version": 2,
            "goal": "paused work",
            "status": STATUS_BLOCKED_PENDING_HUMAN,
            "enforce": True,
        }
        p = tmp_path / "goal.json"
        p.write_text(json.dumps(doc), encoding="utf-8")
        loaded = load_goal(p)
        assert loaded is not None
        assert loaded.status == STATUS_BLOCKED_PENDING_HUMAN
        assert loaded.status != STATUS_PASSED

    def test_blocked_status_round_trips(self, tmp_path: Path) -> None:
        goal = new_goal(goal_text="x", criteria=[], enforce=True)
        goal.status = STATUS_BLOCKED_PENDING_HUMAN
        p = tmp_path / "goal.json"
        save_goal(goal, p)
        loaded = load_goal(p)
        assert loaded is not None and loaded.status == STATUS_BLOCKED_PENDING_HUMAN


# a FROZEN replica of v1's status contract (``_goal_state.py:225-227`` pre-PLAN-0069):
# the v1 code no longer exists at HEAD, so the reader-skew direction (a v2 file
# read by a v1 reader) is pinned against this fixture (AC-4b; Code R2 confirmed
# the frozen-fixture approach is the right evidence for a deleted-code contract).
_V1_VALID_STATUSES = frozenset({"active", "passed", "released-unevaluated"})


def _v1_status_ok(doc: dict[str, Any]) -> bool:
    """Mirror of v1 ``Goal.from_json``'s status gate: a status outside the v1
    set makes v1 return ``None`` (stand-down)."""
    status = doc.get("status")
    return isinstance(status, str) and status in _V1_VALID_STATUSES


class TestV1ReaderSkew:
    def test_blocked_status_absent_from_v1_contract(self) -> None:
        """AC-4b: the new status is unknown to the frozen v1 contract."""
        assert STATUS_BLOCKED_PENDING_HUMAN not in _V1_VALID_STATUSES

    def test_v1_reader_stands_down_on_v2_blocked_file(self) -> None:
        """AC-4b (fail-safe skew direction): a v2 blocked-pending-human file,
        read by v1 rules, is rejected -> None -> the gate stands down. It never
        blocks and never marks passed (ADR-0018 Reversibility)."""
        v2_blocked = {"goal": "paused", "status": STATUS_BLOCKED_PENDING_HUMAN, "enforce": True}
        assert _v1_status_ok(v2_blocked) is False
        # an ordinary active goal is accepted by both readers
        assert _v1_status_ok({"goal": "x", "status": "active"}) is True

    def test_v2_reader_rejects_status_unknown_to_v2(self, tmp_path: Path) -> None:
        """AC-4c: the stand-down contract survives the NEXT skew — a status
        unknown to v2 still yields None (never a raise, never a false active)."""
        doc = {"goal": "x", "status": "some-future-status-v3"}
        p = tmp_path / "goal.json"
        p.write_text(json.dumps(doc), encoding="utf-8")
        assert load_goal(p) is None


class TestAmendmentsAppendOnly:
    def test_record_amendment_appends_and_preserves(self, tmp_path: Path) -> None:
        goal = new_goal(goal_text="x", criteria=[])
        for i in range(3):
            record_amendment(goal, Amendment(ts=f"t{i}", fingerprint=f"fp{i}", event="typed"))
        assert [a.ts for a in goal.amendments] == ["t0", "t1", "t2"]
        p = tmp_path / "goal.json"
        save_goal(goal, p)
        loaded = load_goal(p)
        assert loaded is not None
        assert [a.fingerprint for a in loaded.amendments] == ["fp0", "fp1", "fp2"]

    def test_amendment_never_dropped_by_a_gate_rewrite(self, tmp_path: Path) -> None:
        """AC-8: interleave an appended amendment with a gate evaluation rewrite;
        the amendment is never dropped (composes with AC-1)."""
        p = tmp_path / "goal.json"
        goal = new_goal(goal_text="x", criteria=[], enforce=True)
        record_amendment(goal, Amendment(ts="t-amend", fingerprint="fp-amend", event="typed"))
        save_goal(goal, p)
        # the gate reloads and appends an evaluation (its rewrite path)
        g2 = load_goal(p)
        assert g2 is not None
        record_evaluation(g2, Evaluation(ts="t-eval", fingerprint="fp-eval", amendments_seen=1))
        save_goal(g2, p)
        final = load_goal(p)
        assert final is not None
        assert [a.ts for a in final.amendments] == ["t-amend"]
        assert [e.ts for e in final.evaluations] == ["t-eval"]
        assert final.evaluations[0].amendments_seen == 1
