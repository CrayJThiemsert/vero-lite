"""`tools/tally.py` must refuse a breakdown that does not account for its own input.

🔴 **The regression pin is ``test_a_value_appearing_inside_another_field_is_not_counted``.**
That is the s288 defect verbatim: the classifier log's transport breakdown was built
with ``grep -c -i timeout``, which counts every line containing that word ANYWHERE —
including inside a ``reason`` string — mixed in the same table with a proper field
match for ``ok``. The four buckets summed to 139 against 140 lines, and a fourth
value (``retry``) was never counted at all because a hand-written breakdown
enumerates only the values its author already knows about.

Every other case here is one way a breakdown can stop describing its input while
still looking tidy: a record that will not parse, a record with no such field, and
a value set that has moved since the author last looked.
"""

from __future__ import annotations

import json
from pathlib import Path

from tools.tally import main, render, tally_jsonl


def _log(tmp_path: Path, records: list[dict[str, object]], *, raw: str = "") -> Path:
    path = tmp_path / "log.jsonl"
    body = "".join(json.dumps(r) + "\n" for r in records) + raw
    path.write_text(body, encoding="utf-8")
    return path


# --- the happy path, and its non-vacuity --------------------------------------


def test_a_complete_breakdown_is_exhaustive_and_counts_correctly(tmp_path: Path) -> None:
    """Non-vacuity for every refusal below: a tool that refuses everything passes them."""
    path = _log(
        tmp_path,
        [{"transport": "ok"}, {"transport": "timeout"}, {"transport": "timeout"}],
    )
    result = tally_jsonl(path, "transport")

    # One assertion over the whole accounting rather than four, so a failure prints
    # every measured value side by side with what was expected — the shape §8 asks
    # for (`pre=… post=…`, never a bare verdict).
    assert (result.records, result.counted, result.unparseable, result.missing_field) == (
        3,
        3,
        0,
        0,
    )
    assert result.counts == {"timeout": 2, "ok": 1}
    assert result.exhaustive
    # More than one bucket, and no bucket holds the total: a collapse-to-one-value
    # breakdown would satisfy a sum check while describing nothing.
    assert len(result.counts) > 1
    assert max(result.counts.values()) < result.records


def test_a_value_appearing_inside_another_field_is_not_counted(tmp_path: Path) -> None:
    """🔴 The s288 defect, verbatim: substring counting vs field counting.

    ``reason`` carries the word ``timeout`` while ``transport`` says ``ok``. A
    ``grep -c -i timeout`` reads 2 here; the field is the only thing that reads 1.
    """
    path = _log(
        tmp_path,
        [
            {"transport": "timeout", "reason": "the model did not answer"},
            {"transport": "ok", "reason": "recovered after a timeout on the first try"},
        ],
    )
    result = tally_jsonl(path, "transport")

    assert result.counts == {"timeout": 1, "ok": 1}, (
        "a value was counted from a different field's free text — this is the s288 "
        f"breakdown defect, back: {result.counts}"
    )
    assert result.exhaustive


# --- each way a breakdown stops describing its input ---------------------------


def test_a_record_missing_the_field_is_counted_not_skipped(tmp_path: Path) -> None:
    """A skipped record shrinks the denominator with it, so the sum still looks tidy."""
    path = _log(tmp_path, [{"transport": "ok"}, {"decision": "pause"}])
    result = tally_jsonl(path, "transport")

    assert (result.records, result.counted, result.missing_field) == (2, 1, 1)
    assert not result.exhaustive


def test_an_unparseable_line_is_counted_not_skipped(tmp_path: Path) -> None:
    """Same failure from the other side: a line that never became a record."""
    path = _log(tmp_path, [{"transport": "ok"}], raw="{not json\n")
    result = tally_jsonl(path, "transport")

    assert (result.records, result.counted, result.unparseable) == (2, 1, 1)
    assert not result.exhaustive


def test_the_report_prints_the_values_it_measured(tmp_path: Path) -> None:
    """§8: a verification report prints `pre=…  post=…`, never a bare verdict.

    A refusal that does not say WHICH records went unaccounted for cannot be acted
    on — the reader is told the breakdown is wrong and not where to look.
    """
    path = _log(tmp_path, [{"transport": "ok"}, {"decision": "pause"}])
    report, ok = render(tally_jsonl(path, "transport"), None)

    assert not ok
    assert "sum 1 != records 2" in report
    assert "missing key 1" in report


# --- --expect: the falsifier, written down before the reading ------------------


def test_an_expected_value_set_that_matches_is_accepted(tmp_path: Path) -> None:
    """Non-vacuity for the two refusals below."""
    path = _log(tmp_path, [{"transport": "ok"}, {"transport": "timeout"}])
    _, ok = render(tally_jsonl(path, "transport"), {"ok", "timeout"})
    assert ok


def test_a_value_the_author_did_not_enumerate_is_refused(tmp_path: Path) -> None:
    """The s288 miss: `retry` existed in the log and appeared in no hand-written bucket."""
    path = _log(
        tmp_path,
        [{"transport": "ok"}, {"transport": "timeout"}, {"transport": "retry"}],
    )
    report, ok = render(tally_jsonl(path, "transport"), {"ok", "timeout"})

    assert not ok
    assert "unexpected: ['retry']" in report


def test_an_expected_value_that_has_vanished_is_refused(tmp_path: Path) -> None:
    """The other direction: the population moved since the author last looked."""
    path = _log(tmp_path, [{"transport": "ok"}])
    report, ok = render(tally_jsonl(path, "transport"), {"ok", "timeout"})

    assert not ok
    assert "absent: ['timeout']" in report


# --- the CLI contract ----------------------------------------------------------


def test_the_cli_exits_non_zero_on_a_breakdown_that_cannot_be_quoted(tmp_path: Path) -> None:
    """The exit code is what stops an incomplete breakdown being quoted by a script."""
    path = _log(tmp_path, [{"transport": "ok"}, {"decision": "pause"}])
    assert main([str(path), "--field", "transport"]) == 1


def test_the_cli_exits_zero_on_a_complete_breakdown(tmp_path: Path) -> None:
    """Non-vacuity for the exit code: it is not always 1."""
    path = _log(tmp_path, [{"transport": "ok"}, {"transport": "timeout"}])
    assert main([str(path), "--field", "transport"]) == 0


def test_a_missing_file_is_a_usage_error_not_an_empty_tally(tmp_path: Path) -> None:
    """An unreadable file must not read as 'zero records, exhaustive'."""
    assert main([str(tmp_path / "nope.jsonl"), "--field", "transport"]) == 2
