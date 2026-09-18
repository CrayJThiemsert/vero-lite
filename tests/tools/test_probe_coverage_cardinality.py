"""`Claim.stable_key`'s cardinality stamp — why a rank alone is not an address.

`occurrence` disambiguates two claims that share `(owner, source)`, and it does that
correctly. What it cannot do is survive one of them being deleted: it is a rank
**re-derived from the current source**, so deleting the first of two twins slides the
survivor into `#0` and the *deleted* claim's key silently addresses it. A battery goes
on crediting a claim nobody declared, and no rule over the current source can refuse
that — the fact which would (that the first assert used to exist) is no longer there.

Stamping the group's size beside the rank turns that deletion into a changed key, so
every address in the group stops resolving and `_validate` refuses before the first
mutation. Drift causes re-work, never inheritance.

Every test here carries exactly ONE claim, matching `test_probe_coverage.py`'s own
convention, so a mutation of the tool can only ever hide behind one assertion at a time.
These read the tool's real output on real source text; a hand-built `Claim` would be
checking the fixture rather than the stamping pass.
"""

from __future__ import annotations

from pathlib import Path

from tools.probe_coverage import enumerate_claims

#: Two claims sharing `(owner, source)` — the shape `PLAN-0115` AC-5 is built on, and
#: the one whose rank recycles. Identical to `test_probe_coverage.py::_REPEATED`.
_TWINS = """
def test_repeats():
    row = load()
    assert row is not None
    mutate(row)
    assert row is not None
"""

#: The same module after an ordinary one-line delete of the FIRST twin.
_TWINS_AFTER_DELETION = """
def test_repeats():
    mutate(row)
    assert row is not None
"""


def test_a_lone_claim_keys_exactly_as_it_did_before(tmp_path: Path) -> None:
    """Backward compatibility, asserted rather than assumed.

    A claim alone in its `(owner, source)` group takes no group suffix, so every
    committed address that was never at risk of recycling stays byte-identical. Without
    this the stamp would be a tree-wide migration instead of a targeted repair.
    """
    path = tmp_path / "test_lone.py"
    path.write_text("def test_lone():\n    assert a == 1\n", encoding="utf-8")
    (claim,) = enumerate_claims(path)
    assert claim.stable_key == "test_lone|a == 1|#0"


def test_repeated_claims_carry_their_group_size(tmp_path: Path) -> None:
    """Twins key by rank AND size, so the pair is addressable and the size is visible."""
    path = tmp_path / "test_repeat.py"
    path.write_text(_TWINS, encoding="utf-8")
    keys = sorted(c.stable_key for c in enumerate_claims(path))
    assert keys == ["test_repeats|row is not None|#0/2", "test_repeats|row is not None|#1/2"]


def test_the_deleted_twins_key_resolves_before_the_deletion(tmp_path: Path) -> None:
    """The positive control for the absence asserted below.

    "The old key no longer resolves" is a negative claim, and a negative claim is
    satisfied by an empty set — so the same key is shown PRESENT first, on the same
    fixture, before anything is deleted. Without this, the test below would pass against
    an enumerator that returned nothing at all.
    """
    path = tmp_path / "test_repeat.py"
    path.write_text(_TWINS, encoding="utf-8")
    assert "test_repeats|row is not None|#0/2" in {c.stable_key for c in enumerate_claims(path)}


def test_deleting_one_twin_kills_the_deleted_claims_key(tmp_path: Path) -> None:
    """The recycling defect, closed.

    Under a bare rank the survivor would inherit `#0` — the deleted claim's own address —
    and nothing would report it. With the size stamped, the survivor becomes a singleton
    and keys `#0`, so the deleted claim's `#0/2` addresses nothing and the driver refuses
    it. Positive control: `test_the_deleted_twins_key_resolves_before_the_deletion`.
    """
    path = tmp_path / "test_repeat.py"
    path.write_text(_TWINS_AFTER_DELETION, encoding="utf-8")
    assert "test_repeats|row is not None|#0/2" not in {c.stable_key for c in enumerate_claims(path)}
