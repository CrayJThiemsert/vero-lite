"""The (d') truncation policy: withhold the SCORE, never the data.

Driven through the real ``_main`` rather than through a extracted predicate. The
failure this guards against is ordering — a summary printed before truncation is
computed is a summary that cannot be unprinted — and a unit test on a boolean
helper would stay green through exactly that regression. Only the model call
itself is stubbed; the print, dump, and exit paths are the real ones.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import pytest

from benchmarks.procedure_baseline import run_benchmark
from benchmarks.procedure_baseline.grader import HandlerTier
from benchmarks.procedure_baseline.harness import ItemResult
from benchmarks.procedure_baseline.schema import (
    BenchmarkItem,
    Dataset,
    Disposition,
    Expected,
    Scenario,
)
from services.engine.llm.client import CallMetrics

#: A SCORE line, matched by shape: a label, then the metric, then a NUMBER.
#: Asserting on the score's own text rather than on a flag is the point — the
#: policy's promise is that this does not reach the screen, and only reading the
#: screen can check that.
#:
#: Deliberately not the bare words "β headline". The run's trailing NOTE explains
#: the columns with "NOTE: β headline = LLM action-proposal correctness …", so a
#: substring match reports a leak on every run, withheld or not. The legend
#: carries no number; requiring a digit (or the explicit "n/a") after the metric
#: is what separates a printed score from a description of one.
_SCORE_LINE = re.compile(r"^\S+: β headline (?:\d|n/a)", re.MULTILINE)


def _item() -> BenchmarkItem:
    return BenchmarkItem(
        id="t-1",
        description="DO 2.1 — breach",
        scenario=Scenario(
            event_id="evt-1",
            entity_type="Pond",
            primary_key="pond-A1",
            measured_value=2.1,
            unit="mg/L",
            threshold=4.0,
            direction="below",
        ),
        expected=Expected.model_validate(
            {"disposition": "breach", "action_expected": True, "affected_primary_key": "pond-A1"}
        ),
    )


def _dataset() -> Dataset:
    return Dataset(
        vertical="aquaculture",
        procedure="morning_pond_health_round",
        reading_parameter="dissolved_oxygen",
        items=[_item()],
    )


def _result(*, truncated: bool) -> ItemResult:
    calls = (
        CallMetrics(
            role="reasoning",
            done_reason="length" if truncated else "stop",
            eval_count=1024,
            prompt_eval_count=90,
            content_chars=10,
            thinking_chars=None,
        ),
    )
    return ItemResult(
        item_id="t-1",
        vertical="aquaculture",
        disposition_expected=Disposition.BREACH,
        disposition_actual=Disposition.BREACH,
        disposition_correct=True,
        graded=True,
        proposal_correct=True,
        grade=None,
        probe_tier=HandlerTier.CANONICAL,
        judgment_latency_s=1.0,
        calls=calls,
    )


async def _run(monkeypatch: pytest.MonkeyPatch, argv: list[str], results: list[ItemResult]) -> None:
    monkeypatch.setattr(sys, "argv", ["run_benchmark", *argv])
    args = run_benchmark._parse_args()
    monkeypatch.setattr(run_benchmark, "load_all", lambda _dir: [_dataset()])
    monkeypatch.setattr(run_benchmark, "_register_all_handlers", lambda _v: None)

    async def _fake_run_dataset(_dataset: Dataset, **_kwargs: Any) -> list[ItemResult]:
        return results

    monkeypatch.setattr(run_benchmark, "run_dataset", _fake_run_dataset)
    await run_benchmark._main(args)


async def test_a_truncated_run_withholds_the_score(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The score must not reach the screen, and the run must not exit clean.

    A clipped reasoning pass still produces a well-formed judgment, so this item
    would otherwise have been averaged into β as an ordinary pass.
    """
    with pytest.raises(SystemExit) as exc:
        await _run(monkeypatch, [], [_result(truncated=True)])

    assert exc.value.code == 3, "a withheld run exited 0/None, so a script reads it as clean"
    out = capsys.readouterr().out
    assert "SCORES WITHHELD" in out
    assert _SCORE_LINE.search(out) is None, (
        "a β score line was printed anyway — the truncation check is running AFTER "
        "the summary, which is the one ordering this policy exists to prevent"
    )


async def test_the_data_survives_a_withheld_run(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """Scores are withheld; measurements are not. The dump is the valuable part."""
    dump = tmp_path / "dump.jsonl"
    with pytest.raises(SystemExit):
        await _run(monkeypatch, ["--dump-json", str(dump)], [_result(truncated=True)])

    assert dump.exists(), "the withheld run wrote no dump, so the measurement was thrown away"
    assert dump.read_text(encoding="utf-8").strip(), "the dump is empty"
    assert _SCORE_LINE.search(capsys.readouterr().out) is None


async def test_allow_truncation_prints_the_score_anyway(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The demand run's escape hatch — and the positive control for the test above.

    Identical wiring, identical truncated result: the only difference is the flag.
    Without this, "the score was absent" would be satisfied by a run that never
    prints a score at all.
    """
    await _run(monkeypatch, ["--allow-truncation"], [_result(truncated=True)])

    out = capsys.readouterr().out
    assert _SCORE_LINE.search(out) is not None, "--allow-truncation did not restore the score"
    assert "SCORES WITHHELD" not in out


async def test_a_clean_run_is_unaffected(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The second positive control: nothing truncated, so nothing is withheld."""
    await _run(monkeypatch, [], [_result(truncated=False)])

    out = capsys.readouterr().out
    assert _SCORE_LINE.search(out) is not None
    assert "SCORES WITHHELD" not in out
    assert "TRUNCATION: 0 of 1 calls hit the cap." in out
