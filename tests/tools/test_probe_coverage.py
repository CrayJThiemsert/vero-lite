"""`tools/probe_coverage.py` — the fourth clause of a probe battery's pass rule.

Every test here carries exactly ONE claim (lesson #0047 §6: a `pytest.raises` counts as
a claim), so a mutation of the tool can only ever hide behind one assertion at a time.

🔴 **These read the tool's real output on real source text.** A test that asserted
against a hand-built `Claim` list would be checking the fixture rather than the AST
walk — the vacuity this tool exists to detect, reproduced inside its own suite.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.probe_coverage import (
    VERDICT_COMPLETE,
    VERDICT_GAPS,
    Claim,
    enumerate_claims,
    render_report,
)

_MODULE = '''
"""A docstring that says assert foo == bar and must NOT be counted."""

import pytest


def helper(x):
    assert x > 0
    return x


def test_one():
    # assert this comment is not a claim
    assert helper(1) == 1


def test_raises():
    with pytest.raises(ValueError):
        raise ValueError("boom")


def test_conjunction():
    assert helper(1) == 1 and helper(2) == 2
'''


@pytest.fixture
def module(tmp_path: Path) -> Path:
    path = tmp_path / "test_sample.py"
    path.write_text(_MODULE, encoding="utf-8")
    return path


def _key(claim: Claim) -> str:
    return f"{claim.owner}|{claim.source}"


def test_prose_in_a_docstring_is_not_counted_as_a_claim(module: Path) -> None:
    """The regex trap #0047 §6 names: `assert ` matches prose, the AST does not."""
    assert not any("must NOT be counted" in c.source for c in enumerate_claims(module))


def test_a_comment_mentioning_assert_is_not_counted_as_a_claim(module: Path) -> None:
    assert not any("this comment" in c.source for c in enumerate_claims(module))


def test_every_assert_statement_is_counted(module: Path) -> None:
    """3 asserts + 1 `pytest.raises` = 4 claims; the count IS the denominator, so it is
    asserted exactly rather than as a lower bound — an over-count from prose or a
    comment is the failure mode this whole module exists to rule out."""
    assert len(enumerate_claims(module)) == 4


def test_pytest_raises_is_counted_as_a_claim(module: Path) -> None:
    assert any(c.kind == "raises" for c in enumerate_claims(module))


def test_a_claim_is_attributed_to_its_enclosing_function(module: Path) -> None:
    """The helper's assert belongs to `helper`, not to the test that calls it."""
    owners = {c.source: c.owner for c in enumerate_claims(module)}
    assert owners["x > 0"] == "helper"


def test_a_conjunction_is_flagged_rather_than_split(module: Path) -> None:
    """One mutation can witness only one operand, so the honest report says so."""
    assert [c.multi for c in enumerate_claims(module)].count(True) == 1


def test_an_unparsable_module_raises_instead_of_reporting_zero_claims(tmp_path: Path) -> None:
    """A silent zero would read as "nothing to cover" — the false green, exactly."""
    broken = tmp_path / "test_broken.py"
    broken.write_text("def f(:\n", encoding="utf-8")
    with pytest.raises(SyntaxError):
        enumerate_claims(broken)


def test_a_claim_neither_reddened_nor_exempted_is_reported_as_a_gap(module: Path) -> None:
    """The s251 shape: the battery would otherwise have printed PASS."""
    _, complete = render_report(enumerate_claims(module), {}, {}, key_of=_key)
    assert complete is False


def test_the_gap_verdict_token_is_printed(module: Path) -> None:
    report, _ = render_report(enumerate_claims(module), {}, {}, key_of=_key)
    assert VERDICT_GAPS in report


def test_every_gap_is_named_not_merely_counted(module: Path) -> None:
    """#0047's actual requirement: the report must say **WHICH** claims were never
    probed. A count alone is the silence the lesson is about."""
    claims = enumerate_claims(module)
    report, _ = render_report(claims, {}, {}, key_of=_key)
    tail = report.split("GAPS: neither reddened nor exempted")[1]
    assert all(c.source in tail for c in claims)


def test_a_fully_covered_module_is_complete(module: Path) -> None:
    claims = enumerate_claims(module)
    reddened = {_key(c): "P1" for c in claims}
    _, complete = render_report(claims, reddened, {}, key_of=_key)
    assert complete is True


def test_the_complete_verdict_token_is_printed(module: Path) -> None:
    claims = enumerate_claims(module)
    report, _ = render_report(claims, {_key(c): "P1" for c in claims}, {}, key_of=_key)
    assert VERDICT_COMPLETE in report


def test_an_exemption_closes_a_gap(module: Path) -> None:
    claims = enumerate_claims(module)
    _, complete = render_report(claims, {}, {_key(c): "unreachable" for c in claims}, key_of=_key)
    assert complete is True


def test_an_exemptions_reason_is_printed_where_a_reviewer_meets_it(module: Path) -> None:
    """A reason hidden behind a count is a reason nobody reads (#0047 §3)."""
    claims = enumerate_claims(module)
    report, _ = render_report(claims, {}, {_key(c): "BECAUSE-XYZZY" for c in claims}, key_of=_key)
    assert report.count("BECAUSE-XYZZY") == len(claims)


def test_a_stale_key_fails_the_verdict(module: Path) -> None:
    """Addressing an assertion that no longer exists is how the check rots into
    agreement with itself — it must fail, not be ignored."""
    claims = enumerate_claims(module)
    reddened = {_key(c): "P1" for c in claims} | {"gone|no such claim": "P9"}
    _, complete = render_report(claims, reddened, {}, key_of=_key)
    assert complete is False


def test_a_stale_key_is_named_in_the_report(module: Path) -> None:
    claims = enumerate_claims(module)
    reddened = {_key(c): "P1" for c in claims} | {"gone|no such claim": "P9"}
    report, _ = render_report(claims, reddened, {}, key_of=_key)
    assert "gone|no such claim" in report


def test_reddening_wins_over_an_exemption_for_the_same_claim(module: Path) -> None:
    """A claim a probe actually witnessed is never reported as merely exempted —
    otherwise a blanket exemption could quietly bury real coverage."""
    claims = enumerate_claims(module)
    keys = {_key(c) for c in claims}
    report, _ = render_report(
        claims, {k: "P1" for k in keys}, {k: "unreachable" for k in keys}, key_of=_key
    )
    assert "exempted: 0" in report


_REPEATED = """
def test_repeats():
    row = load()
    assert row is not None
    mutate(row)
    assert row is not None
"""


def test_two_identical_asserts_in_one_owner_get_distinct_stable_keys(tmp_path: Path) -> None:
    """🔴 `owner|source` alone COLLIDES, and a colliding key is a coverage lie: the pair
    would report as covered when only the first was ever witnessed."""
    path = tmp_path / "test_repeat.py"
    path.write_text(_REPEATED, encoding="utf-8")
    assert len({c.stable_key for c in enumerate_claims(path)}) == 2


def test_a_witnessed_repeat_does_not_cover_its_twin(tmp_path: Path) -> None:
    """The consequence, asserted directly: reddening one occurrence leaves the other a
    GAP rather than silently closing it."""
    path = tmp_path / "test_repeat.py"
    path.write_text(_REPEATED, encoding="utf-8")
    claims = enumerate_claims(path)
    first = min(claims, key=lambda c: c.lineno)
    _, complete = render_report(claims, {first.stable_key: "P1"}, {}, key_of=lambda c: c.stable_key)
    assert complete is False


def test_the_default_key_is_the_claim_id(module: Path) -> None:
    """Callers that pass no `key_of` address claims by their line-numbered id."""
    claims = enumerate_claims(module)
    _, complete = render_report(claims, {c.claim_id: "P1" for c in claims}, {})
    assert complete is True
