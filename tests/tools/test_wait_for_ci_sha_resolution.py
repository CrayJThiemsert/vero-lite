"""Sha resolution for :mod:`tools.ci.wait_for_ci` — a separate concern from the verdict table.

The defect this closes, measured at session 262: ``gh run list --commit`` matches
the FULL 40-character sha only, so an abbreviation came back with zero runs and
was reported as ``NO-RUN`` — a verdict that says "CI has not run here", stated
about a commit where it had run and passed. Reproduced with a control on a second
sha, which is what showed it was the abbreviation and not the commit.

The direction was safe: this tool still could not report a green it had not
measured. But it made the tool unable to pass at all for the way shas are actually
pasted, and it did produce one wrong reading — a green PR read as unverified.

Kept out of ``test_wait_for_ci.py`` because that file is the verdict table: what
:func:`classify` decides given a set of runs. What a sha argument is allowed to be
before any of that happens is a different question with a different failure mode.
"""

from __future__ import annotations

import subprocess

import pytest

from tools.ci import wait_for_ci
from tools.ci.wait_for_ci import ShaResolutionError, resolve_sha


def _head_sha() -> str:
    """The full sha of HEAD, read from the repo under test.

    HEAD rather than any historical commit on purpose: CI checks out at depth 1,
    so a test that resolved an old sha would pass locally and fail there for a
    reason with nothing to do with what it is checking.
    """
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],  # noqa: S607
        cwd=wait_for_ci.REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def test_a_full_sha_is_returned_unchanged() -> None:
    """No resolution step at all, so nothing can substitute a different commit."""
    full = _head_sha()
    assert resolve_sha(full) == full


#: Abbreviation lengths that must all resolve. 7 is git's own default; 39 is one
#: short of a full sha and the top of the accepted band.
_ACCEPTED_LENGTHS = (7, 12, 20, 39)


def test_a_short_sha_of_any_accepted_length_resolves_to_the_full_one() -> None:
    """THE fix. An abbreviation used to reach the API unchanged and come back empty.

    A refusal is CAUGHT and recorded rather than allowed to propagate. Letting it
    raise would turn a narrowed accepted band into an uncaught exception — a crash,
    which says something broke without showing that this assertion is what carries
    the behaviour. Recorded, the same defect reddens this line and names the length
    that stopped working.
    """
    full = _head_sha()
    resolved: dict[int, str] = {}
    for length in _ACCEPTED_LENGTHS:
        try:
            resolved[length] = resolve_sha(full[:length])
        except ShaResolutionError as exc:
            resolved[length] = f"REFUSED: {exc}"

    assert resolved == dict.fromkeys(_ACCEPTED_LENGTHS, full)


def test_an_uppercase_sha_is_accepted() -> None:
    """git and GitHub both spell shas lowercase, but a pasted uppercase one names the
    same commit; refusing it would be pedantry rather than safety.

    Recorded rather than raised, for the reason given above.
    """
    full = _head_sha()
    try:
        got = resolve_sha(full.upper())
    except ShaResolutionError as exc:
        got = f"REFUSED: {exc}"

    assert got == full


#: Things that name a commit only at the moment you ask.
_MOVING_REFS = ("main", "HEAD", "origin/main", "v1.0", "")


def test_moving_refs_are_refused_rather_than_resolved() -> None:
    """A green is a claim about ONE commit.

    Resolving a branch or HEAD would answer with whatever it points at when asked,
    which is not necessarily the tree the caller was looking at — the exact reason
    ``--sha`` is required and never defaulted to HEAD.

    One assertion over the whole set rather than a parametrized case each. A
    mutation that un-refuses one of these un-refuses most of them, and a probe
    credits a claim only when exactly one assertion reddened; as separate cases the
    real defect was unwitnessable. The recorded list also names WHICH refs slipped
    through, which a bare ``pytest.raises`` cannot.
    """
    resolved_anyway: list[str] = []
    for ref in _MOVING_REFS:
        try:
            resolve_sha(ref)
        except ShaResolutionError:
            continue
        resolved_anyway.append(ref)

    assert resolved_anyway == [], (
        f"{resolved_anyway} resolved to a commit — a green pinned to whatever they "
        "point at when asked, which is not the commit the caller was looking at"
    )


def test_an_unknown_prefix_is_refused() -> None:
    """A hex prefix this clone has never seen cannot be the commit CI ran on."""
    with pytest.raises(ShaResolutionError):
        resolve_sha("dddddddd")


def test_main_reports_error_not_no_run_for_an_unusable_sha() -> None:
    """The defect, at the exit code a caller actually reads.

    ``NO-RUN`` (5) is a statement about CI. ``ERROR`` (2) is a statement about the
    argument. Returning the former for a sha the tool could not even use is how a
    green commit came to be read as unverified. This is the assertion that would
    have caught the original bug — the resolver did not exist to unit-test then.
    """
    assert wait_for_ci.main(["status", "--sha", "not-a-sha"]) == 2


def test_main_refuses_before_it_would_call_gh(monkeypatch: pytest.MonkeyPatch) -> None:
    """Resolution happens FIRST, so an unusable sha never reaches the network.

    Ordering is the fix, not just the refusal: it was precisely the API's empty
    answer for an unusable sha that got dressed up as a measured absence.

    The absence is RECORDED rather than raised. A stub that raises can only report
    this by crashing, and a crash says something broke — not that this assertion is
    the one holding the behaviour up. Checked before the return value, too, so the
    ordering claim is what reddens when ordering is what breaks.
    """
    called: list[str] = []
    monkeypatch.setattr(wait_for_ci, "_gh_runs", lambda sha: called.append(sha) or [])

    result = wait_for_ci.main(["status", "--sha", "zzzzzzz"])

    assert called == [], (
        f"gh was called with {called!r} for a sha that should have been refused — "
        "the empty answer it returns is exactly what used to be reported as NO-RUN"
    )
    assert result == 2
