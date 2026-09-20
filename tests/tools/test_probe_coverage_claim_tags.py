"""PLAN-0128 — claim tags in the enumerator.

A trailing tag comment on an assertion's ANCHOR line makes `@<id>` that claim's address,
so the address stops being derived from the text it names.

🔴 **This is its own module on purpose.** A probe battery's coverage denominator is every
claim in its `claim_sources`, so adding these claims to `test_probe_coverage.py` would
have put 20 unrelated pre-existing claims into this battery's denominator — and the only
way to a COMPLETE verdict would have been 20 junk exemptions, which the tool's own
docstring says "destroys the check faster than having none". Same reason, the other
direction: it also keeps these claims OUT of any battery that already scopes that module
exactly. Precedent: `test_probe_coverage_cardinality.py` (s311).

Every test here reads the tool's REAL output on real source text.

NOTE — no comment in this file spells the tag marker out. The enumerator reads every
COMMENT token, so a prose comment containing a live marker is parsed as a tag and refused
as malformed, taking the whole module's enumeration down with it. That strictness is
deliberate (a typo'd tag must be loud, never silently ignored) and it was measured here,
by an earlier draft of this file refusing itself. Spell the marker only inside a docstring
or a string literal — STRING tokens, invisible to the reader.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.probe_coverage import (
    VERDICT_GAPS,
    ClaimTagError,
    enumerate_claims,
    render_report,
)

_REPEATED = """
def test_repeats():
    row = load()
    assert row is not None
    mutate(row)
    assert row is not None
"""


_TAGGED_SIBLINGS = """
def test_x():
    result = go()
    assert result.error == "missing"  # claim: E1
    assert result.error == "missing" or retry
"""

_TAGGED_MULTILINE = """
import pytest


def test_x():
    assert f(
        a,
        b,
    ) == 1  # claim: E2
    with pytest.raises(
        ValueError,
    ):  # claim: E3
        boom()
"""

#: `_REPEATED` with the FIRST twin tagged and nothing else changed, so the untagged
#: original is a true control rather than a second hand-written fixture.
_TAGGED_TWIN = _REPEATED.replace(
    "assert row is not None", "assert row is not None  # claim: first", 1
)

_MIXED_TAGGED = """
def test_x():
    assert alpha == 1  # claim: X
    assert beta == 2
    assert gamma == 3
"""


def _write(tmp_path: Path, name: str, body: str) -> Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


def test_a_tagged_claim_is_keyed_by_its_tag(tmp_path: Path) -> None:
    """The tag becomes the key, and it does NOT become part of the text it sits beside.

    The second half is the one worth pinning: `source` is sliced from the assert's *test
    expression*, and a trailing comment falls outside that span. If it did not, tagging a
    claim would change the very text key it is meant to replace.
    """
    path = _write(tmp_path, "test_x.py", _TAGGED_SIBLINGS)
    tagged, sibling = enumerate_claims(path)

    assert (tagged.tag, tagged.stable_key) == ("E1", "@E1")  # claim: pr1/tag-is-the-key
    assert tagged.source == 'result.error == "missing"'  # claim: pr1/tag-not-in-source
    assert (sibling.tag, sibling.stable_key) == (
        None,
        'test_x|result.error == "missing" or retry|#0',
    )  # claim: pr1/sibling-keeps-text-key
    assert [c.claim_id for c in (tagged, sibling)] == [
        "test_x::test_x::L4",
        "test_x::test_x::L5",
    ]  # claim: pr1/claim-id-unchanged


def test_a_tag_on_the_anchor_line_of_a_multi_line_claim_is_attached_to_it(
    tmp_path: Path,
) -> None:
    """The anchor is the line that ENDS the logical line — `) == 1` for an exploded
    assert, `):` for an exploded `pytest.raises` header. Both are read from the same
    `tokenize` NEWLINE row the tag is read from, so what an author writes is what the
    enumerator looks at."""
    path = _write(tmp_path, "test_multi.py", _TAGGED_MULTILINE)
    claims = enumerate_claims(path)
    keys = {c.tag: c.stable_key for c in claims}
    sources = {c.tag: c.source for c in claims}

    # `.get` rather than `[...]`: a missing tag must redden THIS assertion, not raise a
    # KeyError, which the driver would classify CRASHED and refuse to credit.
    assert keys.get("E2") == "@E2"  # claim: pr1/multiline-assert-attaches
    assert keys.get("E3") == "@E3"  # claim: pr1/raises-header-attaches
    assert sources.get("E2") == "f( a, b, ) == 1"  # claim: pr1/multiline-no-leak
    assert sources.get("E3") == "pytest.raises( ValueError, )"  # claim: pr1/raises-no-leak


def test_tagging_one_twin_leaves_the_other_at_occurrence_1(tmp_path: Path) -> None:
    """🔴 Tagging a claim must never move a DIFFERENT claim's address.

    Occurrence and cardinality are stamped over every claim, tagged or not, so a tagged
    claim keeps its slot in its text group. Were the tagged twin dropped from the group,
    the survivor would slide from `#1/2` to `#0` — a silent re-point, which is the entire
    class of defect tags exist to remove.
    """
    path = _write(tmp_path, "test_repeat.py", _TAGGED_TWIN)
    keys = {c.stable_key for c in enumerate_claims(path)}

    assert keys == {
        "@first",
        "test_repeats|row is not None|#1/2",
    }  # claim: pr1/twin-keeps-its-slot

    control = _write(tmp_path, "test_repeat_untagged.py", _REPEATED)
    control_keys = {c.stable_key for c in enumerate_claims(control)}
    assert "test_repeats|row is not None|#0/2" in control_keys  # claim: pr1/twin-control


def test_gaps_are_named_across_tagged_and_untagged_claims(tmp_path: Path) -> None:
    """The denominator is every claim, tagged or not — tags are required only for what a
    battery ADDRESSES. A tagged claim credited by its tag leaves the untagged ones as
    gaps, exactly as two untagged ones would."""
    path = _write(tmp_path, "test_mixed.py", _MIXED_TAGGED)
    claims = enumerate_claims(path)
    key_of = lambda c: c.stable_key  # noqa: E731
    report, complete = render_report(claims, {"@X": "P1"}, {}, key_of=key_of)

    assert ("GAPS: 2" in report, VERDICT_GAPS in report, complete) == (
        True,
        True,
        False,
    )  # claim: pr1/gaps-count-untagged
    assert "@X" in report  # claim: pr1/covered-line-carries-tag

    beta = next(c for c in claims if "beta" in c.source)
    one_more, _ = render_report(claims, {"@X": "P1", beta.stable_key: "P2"}, {}, key_of=key_of)
    assert "GAPS: 1" in one_more  # claim: pr1/gaps-control


def test_a_duplicated_tag_is_refused(tmp_path: Path) -> None:
    """Two claims cannot share an id. G31: Jest and insta both reintroduced the
    silent-re-target defect on a duplicated explicit name, and neither validates for it."""
    path = _write(
        tmp_path,
        "test_dup.py",
        "\ndef test_x():\n    assert a == 1  # claim: D\n    assert b == 2  # claim: D\n",
    )
    with pytest.raises(
        ClaimTagError, match=r"duplicate claim id 'D' on lines 3 and 4"
    ):  # claim: pr1/duplicate-id-refused
        enumerate_claims(path)


@pytest.mark.parametrize(
    "body",
    [
        # the line-ABOVE form an earlier draft specified — refused, not silently ignored,
        # so nobody writes it from habit and loses the address
        "\ndef test_x():\n    # claim: E1\n    assert a == 1\n",
        # a comment-only line elsewhere in the owner
        "\ndef test_x():\n    assert a == 1\n    # claim: E1\n",
        # a code line that ends no claim
        "\ndef test_x():\n    x = 1  # claim: E1\n    assert a == 1\n",
    ],
    ids=["line-above", "comment-only", "non-claim-line"],
)
def test_an_unattached_tag_is_refused(tmp_path: Path, body: str) -> None:
    """A tag that addresses nothing must be loud. Silently ignoring it is how an author
    believes a claim is addressed when it is not."""
    path = _write(tmp_path, "test_unattached.py", body)
    with pytest.raises(ClaimTagError, match="unattached tag"):  # claim: pr1/unattached
        enumerate_claims(path)


def test_a_tag_on_an_interior_line_is_refused_because_it_would_leak_into_source(
    tmp_path: Path,
) -> None:
    """An interior line sits INSIDE the span `ast.get_source_segment` slices, so the tag
    would enter the very claim's `source` and change the text key it replaces. The
    message names the claim it sits inside, because "line 4" alone does not say which
    statement is wrong."""
    body = "\ndef test_x():\n    assert f(\n        a,  # claim: E3\n        b,\n    ) == 1\n"
    path = _write(tmp_path, "test_interior.py", body)
    with pytest.raises(
        ClaimTagError, match=r"interior line of the claim starting at line 3"
    ):  # claim: pr1/interior-refused
        enumerate_claims(path)


@pytest.mark.parametrize(
    "comment",
    ["# claim:", "# claim: a|b", "# claim: a b c", "# claim: a  # claim: b"],
    ids=["empty", "pipe", "spaces", "two-markers"],
)
def test_a_malformed_tag_id_is_refused(tmp_path: Path, comment: str) -> None:
    """`|` is refused because a text key contains one: an id that could look like a text
    key would make the two derivations ambiguous at the index."""
    path = _write(tmp_path, "test_malformed.py", f"\ndef test_x():\n    assert a == 1  {comment}\n")
    with pytest.raises(ClaimTagError):  # claim: pr1/malformed-id-refused
        enumerate_claims(path)


def test_a_claim_tag_inside_a_string_is_a_string_not_a_tag(tmp_path: Path) -> None:
    """Tags are read from `tokenize` COMMENT tokens, never from a regex over raw lines.

    A regex cannot tell a comment from the same characters inside a string literal, and
    the two fixtures below are the reason that matters: one would become a spurious tag,
    the other a spurious REFUSAL that takes the module down.
    """
    body = '\ndef test_x():\n    assert f() == "# claim: ok  # x"\n'
    literal = _write(tmp_path, "test_lit.py", body)
    assert [(c.tag, c.stable_key) for c in enumerate_claims(literal)] == [
        (None, 'test_x|f() == "# claim: ok # x"|#0')
    ]  # claim: pr1/string-literal-is-not-a-tag

    doc = _write(
        tmp_path,
        "test_doc.py",
        '"""A module docstring.\n\n# claim: doc\n"""\n\n\ndef test_x():\n    assert 1 == 1\n',
    )
    assert [c.tag for c in enumerate_claims(doc)] == [None]  # claim: pr1/docstring-is-not-a-tag
