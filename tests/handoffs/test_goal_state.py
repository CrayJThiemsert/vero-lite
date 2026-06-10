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
    STATUS_ACTIVE,
    STATUS_PASSED,
    Criterion,
    Evaluation,
    Goal,
    goal_path,
    load_goal,
    new_goal,
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
