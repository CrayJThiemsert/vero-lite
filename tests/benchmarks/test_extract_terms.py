"""Planted-defect tests for the Step 4b term extractor.

`extract_terms.py` is an INSTRUMENT, not a `tools/check_*.py` guard, so
`tests/tools/test_guards_hold_on_the_real_tree.py` does not cover it by name
pattern (COMPANION s288 §3 point 5). Every claim it prints therefore needs its own
planted defect here, and every negative assertion its own positive control — "the
control line is absent" is satisfied by an empty output.

The claims under test:

* an attempt missing a duration field is COUNTED, never silently dropped;
* the >= 6-of-11 floor actually refuses;
* the PLAN-0118 control can FAIL — a control that cannot fail certifies nothing;
* an empty arm is refused rather than averaged.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from benchmarks.intake_extraction.extract_terms import MIN_CASES, report_arm

NS = 1_000_000_000


def _attempt(
    index: int = 0,
    *,
    out_tok: int = 400,
    decode_s: float = 8.7,
    drop: str | None = None,
    model: str = "gpt-oss:20b",
) -> dict[str, object]:
    """One attempt. `drop` plants the defect: that duration field goes None."""
    att: dict[str, object] = {
        "index": index,
        "model": model,
        "total_duration_ns": int((decode_s + 0.3) * NS),
        "load_duration_ns": int(0.004 * NS),
        "prompt_eval_duration_ns": int(0.3 * NS),
        "eval_duration_ns": int(decode_s * NS),
        "eval_count": out_tok,
        "prompt_eval_count": 900,
        "done_reason": "stop",
        "truncated": False,
    }
    if drop is not None:
        att[drop] = None
    return att


def _arm(
    tmp_path: pathlib.Path,
    n_cases: int,
    *,
    out_tok: int = 400,
    decode_s: float = 8.7,
    drop_on_last: str | None = None,
    model: str = "gpt-oss:20b",
) -> str:
    d = tmp_path / "arm"
    d.mkdir(exist_ok=True)
    for i in range(n_cases):
        drop = drop_on_last if i == n_cases - 1 else None
        (d / f"case-{i:02d}.json").write_text(
            json.dumps(
                {
                    "case_id": f"c{i:02d}",
                    "model": model,
                    "attempts": [
                        _attempt(0, out_tok=out_tok, decode_s=decode_s, drop=drop, model=model)
                    ],
                }
            ),
            encoding="utf-8",
        )
    return str(d)


def test_a_missing_duration_field_is_counted_not_dropped(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The defect: one attempt loses `eval_duration_ns`.

    It must appear in `missing`, the accounting line must still read OK, and the
    usable count must drop by exactly one. Positive control below proves the same
    fixture reads 0 missing when nothing is planted.
    """
    rc = report_arm(_arm(tmp_path, 11, drop_on_last="eval_duration_ns"))
    out = capsys.readouterr().out
    assert "missing a duration field: 1" in out, out
    assert "usable: 10" in out, out
    assert "10 + 1 missing = 11  vs attempts seen 11  OK" in out, out
    assert rc == 0  # 10 cases still clears the floor


def test_positive_control_same_fixture_reads_zero_missing(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Without the planted defect the SAME assertion reads 0 — so the test above
    detects the defect rather than a constant."""
    report_arm(_arm(tmp_path, 11))
    out = capsys.readouterr().out
    assert "missing a duration field: 0" in out, out
    assert "usable: 11" in out, out
    assert "11 + 0 missing = 11  vs attempts seen 11  OK" in out, out


def test_the_case_floor_actually_refuses(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Below the pre-committed floor the arm is INSUFFICIENT-EVIDENCE, exit 1."""
    rc = report_arm(_arm(tmp_path, MIN_CASES - 1))
    out = capsys.readouterr().out
    assert "STEP4B-ARM: INSUFFICIENT-EVIDENCE" in out, out
    assert rc == 1


def test_the_floor_passes_exactly_at_the_boundary(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Positive control for the floor: one more case flips it to USABLE, so the
    refusal above is the floor firing and not a fixture that can never pass."""
    rc = report_arm(_arm(tmp_path, MIN_CASES))
    out = capsys.readouterr().out
    assert "STEP4B-ARM: USABLE" in out, out
    assert rc == 0


def test_the_plan_0118_control_can_fail(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The defect: an implausible decode rate.

    4096 tokens at ~4600 tok/s predicts ~0.9 s against a published ~85 s, so the
    control must say OUT OF BAND. This is the assertion that makes every in-band
    reading elsewhere mean something.
    """
    report_arm(_arm(tmp_path, 11, out_tok=40_000, decode_s=8.7))
    out = capsys.readouterr().out
    assert "OUT OF BAND" in out, out


def test_the_plan_0118_control_passes_on_a_plausible_rate(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Positive control: ~46 tok/s predicts ~89 s, inside the 60-110 s band.

    Without this, `OUT OF BAND` appearing above could just mean the control always
    fires — a negative assertion with no positive control is vacuous.
    """
    report_arm(_arm(tmp_path, 11, out_tok=400, decode_s=8.7))
    out = capsys.readouterr().out
    assert "OUT OF BAND" not in out, out
    assert "published band 60-110 s   OK" in out, out


def test_a_model_with_no_published_figure_gets_no_verdict(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The s289 defect, planted: qwen's ~19 tok/s legitimately predicts ~215 s, and
    the gpt-oss band would call that OUT OF BAND.

    The band is a gpt-oss figure. Asserting it against a model it does not describe
    is not a control — so an unpublished model must get the prediction printed and
    NO verdict. Both halves are asserted: the disclaimer present AND the false
    accusation absent.
    """
    report_arm(_arm(tmp_path, 11, out_tok=400, decode_s=21.0, model="qwen3.8:27b-mtp-q4_K_M"))
    out = capsys.readouterr().out
    assert "NO PUBLISHED FIGURE for qwen3.8:27b-mtp-q4_K_M — not a control" in out, out
    assert "OUT OF BAND" not in out, out


def test_positive_control_the_same_rate_under_gpt_oss_does_get_a_verdict(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Positive control for the test above: the identical slow rate, relabelled
    `gpt-oss:20b`, DOES draw a verdict — and OUT OF BAND at that.

    Without this, "no verdict" could mean the control had simply stopped running for
    everyone. It proves the suppression is scoped to the model, not global.
    """
    report_arm(_arm(tmp_path, 11, out_tok=400, decode_s=21.0, model="gpt-oss:20b"))
    out = capsys.readouterr().out
    assert "NO PUBLISHED FIGURE" not in out, out
    assert "OUT OF BAND" in out, out


def test_a_mixed_model_arm_is_refused_rather_than_averaged(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Two model tags in one arm have no single published figure to check against."""
    d = tmp_path / "mixed"
    d.mkdir()
    for i, m in enumerate(["gpt-oss:20b"] * 6 + ["qwen3.8:27b-mtp-q4_K_M"] * 5):
        (d / f"case-{i:02d}.json").write_text(
            json.dumps({"case_id": f"c{i:02d}", "model": m, "attempts": [_attempt(0, model=m)]}),
            encoding="utf-8",
        )
    report_arm(str(d))
    out = capsys.readouterr().out
    assert "2 model tags in one arm — REFUSED" in out, out


def test_an_empty_arm_is_refused_not_averaged(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    d = tmp_path / "empty"
    d.mkdir()
    rc = report_arm(str(d))
    assert "REFUSED" in capsys.readouterr().out
    assert rc == 2


def test_an_arm_where_every_attempt_is_defective_is_refused(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A zero needs a positive control: files exist and attempts exist, but none
    carries all four fields, so there is nothing to average and the tool must say so
    rather than divide by zero."""
    d = tmp_path / "alldrop"
    d.mkdir()
    for i in range(11):
        (d / f"case-{i:02d}.json").write_text(
            json.dumps(
                {"case_id": f"c{i:02d}", "attempts": [_attempt(0, drop="load_duration_ns")]}
            ),
            encoding="utf-8",
        )
    rc = report_arm(str(d))
    out = capsys.readouterr().out
    assert "REFUSED" in out, out
    assert "11 attempts, none carrying all four" in out, out
    assert rc == 2
