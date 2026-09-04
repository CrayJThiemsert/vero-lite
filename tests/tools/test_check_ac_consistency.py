"""Tests for the AC-ledger consistency guard (``tools/check_ac_consistency.py``).

The attribution cases are not invented — each is a shape that occurs verbatim in
`docs/STATUS.md` and that a simpler matcher gets wrong:

* ``Phase B's AC-7 + AC-8 CLOSED`` — a forward scan from ``AC-7`` drops ``AC-8``.
* ``PLAN-0107 AC-11 CLOSED and PLAN-0111 drafted`` — a line-scoped "any PLAN
  mentioned" rule accuses PLAN-0111 of a criterion it does not have.
* two ``CLOSED`` claims on one line — an unbounded lookback merges them.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "tools" / "check_ac_consistency.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_ac_consistency", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def guard() -> ModuleType:
    return _load_module()


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _plan(*acs: tuple[int, str]) -> str:
    """A minimal PLAN body: ``(number, "x" or " ")`` per criterion."""
    return "**Status:** Draft\n\n" + "".join(
        f"- [{flag}] **AC-{n} [check] — a criterion.** Body.\n" for n, flag in acs
    )


# --------------------------------------------------------------------------
# Check 1 — duplicate AC labels
# --------------------------------------------------------------------------


def test_a_duplicate_label_in_an_active_plan_is_found(guard: ModuleType, tmp_path: Path) -> None:
    """The real PLAN-0108 shape: six items, five labels."""
    _write(tmp_path, "docs/plans/0108-x.md", _plan((1, " "), (2, " "), (5, " "), (5, " ")))
    dupes = guard.find_duplicate_labels(tmp_path)
    assert [(d.plan, d.label, d.count) for d in dupes] == [("0108-x.md", 5, 2)]


def test_distinct_labels_are_clean(guard: ModuleType, tmp_path: Path) -> None:
    _write(tmp_path, "docs/plans/0107-x.md", _plan((1, "x"), (2, " "), (3, " ")))
    assert guard.find_duplicate_labels(tmp_path) == []


def test_an_archived_plans_duplicate_is_out_of_scope(guard: ModuleType, tmp_path: Path) -> None:
    """Archived PLANs are frozen records — one really does carry a duplicate.

    `docs/plans/done/0042-at2-managerial-build.md` has a duplicate AC-13. The
    guard exists to stop NEW collisions, not to reopen closed ones, and the
    exclusion is deliberate rather than accidental.
    """
    _write(tmp_path, "docs/plans/done/0042-x.md", _plan((13, "x"), (13, "x")))
    assert guard.find_duplicate_labels(tmp_path) == []
    assert [p.name for p in guard.active_plans(tmp_path)] == []


# --------------------------------------------------------------------------
# Check 2 — STATUS closure claims vs PLAN checkboxes
# --------------------------------------------------------------------------


def test_a_closure_claimed_in_status_but_unticked_is_found(
    guard: ModuleType, tmp_path: Path
) -> None:
    """The real s240 defect: STATUS said CLOSED, the PLAN still said `- [ ]`."""
    _write(tmp_path, "docs/plans/0107-x.md", _plan((11, " ")))
    _write(tmp_path, "docs/STATUS.md", "- **PLAN-0107 — ✅ AC-11 CLOSED s240.**\n")

    found = guard.find_status_mismatches(tmp_path)
    assert len(found) == 1
    assert (found[0].plan, found[0].ac, found[0].status_line) == ("0107", 11, 1)
    assert "still has it as" in found[0].reason


def test_a_ticked_checkbox_agrees(guard: ModuleType, tmp_path: Path) -> None:
    _write(tmp_path, "docs/plans/0107-x.md", _plan((11, "x")))
    _write(tmp_path, "docs/STATUS.md", "- **PLAN-0107 — ✅ AC-11 CLOSED s240.**\n")
    assert guard.find_status_mismatches(tmp_path) == []


def test_two_acs_closed_by_one_claim_are_both_checked(guard: ModuleType, tmp_path: Path) -> None:
    """`AC-7 + AC-8 CLOSED` — the shape a forward scan silently halves."""
    _write(tmp_path, "docs/plans/0107-x.md", _plan((7, "x"), (8, " ")))
    _write(tmp_path, "docs/STATUS.md", "- **PLAN-0107 — Phase B's AC-7 + AC-8 CLOSED s236.**\n")

    found = guard.find_status_mismatches(tmp_path)
    assert [f.ac for f in found] == [8], "AC-8 must be reached, and AC-7 must not be accused"


def test_the_nearest_preceding_plan_governs(guard: ModuleType, tmp_path: Path) -> None:
    """`PLAN-0107 AC-11 CLOSED and PLAN-0111 drafted` — a real STATUS line."""
    _write(tmp_path, "docs/plans/0107-x.md", _plan((11, " ")))
    _write(tmp_path, "docs/plans/0111-x.md", _plan((1, " ")))
    _write(
        tmp_path,
        "docs/STATUS.md",
        "| **s240 — PLAN-0107 AC-11 CLOSED and PLAN-0111 drafted with six SDs.** |\n",
    )

    found = guard.find_status_mismatches(tmp_path)
    assert [f.plan for f in found] == ["0107"], "PLAN-0111 must not be accused"


def test_two_claims_on_one_line_do_not_bleed(guard: ModuleType, tmp_path: Path) -> None:
    """The lookback stops at the previous CLOSED, so AC-7 is not re-reported."""
    _write(tmp_path, "docs/plans/0107-x.md", _plan((7, "x"), (11, " ")))
    _write(
        tmp_path,
        "docs/STATUS.md",
        "- **PLAN-0107 — AC-7 CLOSED s236 (#1206 `7a37c6d`, #1207) and ✅ AC-11 CLOSED s240.**\n",
    )

    found = guard.find_status_mismatches(tmp_path)
    assert [f.ac for f in found] == [11]


# --------------------------------------------------------------------------
# Ambiguity fails LOUD — a check that quietly narrows to nothing is worse
# --------------------------------------------------------------------------


def test_an_unattributable_claim_is_reported_not_skipped(guard: ModuleType, tmp_path: Path) -> None:
    _write(tmp_path, "docs/STATUS.md", "- the AC-4 work is CLOSED now.\n")
    found = guard.find_status_mismatches(tmp_path)
    assert len(found) == 1
    assert found[0].plan == "?"
    assert "names no PLAN" in found[0].reason


def test_a_claim_naming_a_missing_plan_is_reported(guard: ModuleType, tmp_path: Path) -> None:
    _write(tmp_path, "docs/STATUS.md", "- **PLAN-0999 — AC-1 CLOSED.**\n")
    found = guard.find_status_mismatches(tmp_path)
    assert len(found) == 1 and "no file in docs/plans/" in found[0].reason


def test_a_claim_naming_an_ac_the_plan_lacks_is_reported(guard: ModuleType, tmp_path: Path) -> None:
    _write(tmp_path, "docs/plans/0107-x.md", _plan((1, "x")))
    _write(tmp_path, "docs/STATUS.md", "- **PLAN-0107 — AC-99 CLOSED.**\n")
    found = guard.find_status_mismatches(tmp_path)
    assert len(found) == 1 and "declares no AC-99" in found[0].reason


# --------------------------------------------------------------------------
# Documented blind spots — asserted so they stay deliberate
# --------------------------------------------------------------------------


def test_a_phase_level_claim_names_no_ac_and_is_invisible(
    guard: ModuleType, tmp_path: Path
) -> None:
    """`Phase A CLOSED 6/6` — three of these exist and none can be checked.

    Recorded as a test so the blind spot is a decision on the record rather than
    something a later reader mistakes for coverage.
    """
    _write(tmp_path, "docs/plans/0107-x.md", _plan((1, " ")))
    _write(tmp_path, "docs/STATUS.md", "- **PLAN-0107 — ✅ Phase A CLOSED 6/6 s236.**\n")
    assert guard.find_status_mismatches(tmp_path) == []


def test_a_claim_against_an_archived_plan_is_still_checked(
    guard: ModuleType, tmp_path: Path
) -> None:
    """Check 2 reads `done/` too — STATUS cites archived PLANs routinely."""
    _write(tmp_path, "docs/plans/done/0100-x.md", _plan((4, " ")))
    _write(tmp_path, "docs/STATUS.md", "- **PLAN-0100 — AC-4 CLOSED s216.**\n")
    found = guard.find_status_mismatches(tmp_path)
    assert [(f.plan, f.ac) for f in found] == [("0100", 4)]


def test_a_missing_status_file_is_not_fatal(guard: ModuleType, tmp_path: Path) -> None:
    assert guard.find_status_mismatches(tmp_path) == []


# --------------------------------------------------------------------------
# The live repo
# --------------------------------------------------------------------------


def test_the_live_repo_ledger_agrees(guard: ModuleType) -> None:
    """The guard's real assertion, against the tree it ships in.

    Non-vacuity is established in the PR, not here, and each half separately:
    Check 1 reddened on the **live** duplicate AC-5 in PLAN-0108 — a defect
    found in the wild, not planted — and Check 2 reddened with four reports
    (one per claiming STATUS site) when AC-11 was unticked in PLAN-0107,
    replaying the real session-240 state. The two mutations redden disjoint
    things: a duplicate label in one PLAN, a ledger disagreement about another.
    """
    dupes = guard.find_duplicate_labels(REPO_ROOT)
    mismatches = guard.find_status_mismatches(REPO_ROOT)

    assert dupes == [], f"duplicate AC labels: {[(d.plan, d.label) for d in dupes]}"
    assert (
        mismatches == []
    ), f"ledger disagreements: {[(m.plan, m.ac, m.status_line) for m in mismatches]}"
    assert guard.active_plans(REPO_ROOT), "no active PLANs — this would pass vacuously"


# --------------------------------------------------------------------------
# Check 3 — a ticked AC's artifact must be inside some battery's denominator
#
# The failure this closes, measured s278: four batteries each reported
# ``PROBE-COVERAGE: COMPLETE`` while two ACs' artifacts appeared in no battery's
# ``claim_sources`` at all, and one AC's declared probe had never run. Both ACs
# were ticked on that reading. A coverage report is scoped to its own denominator,
# which is not the obligation set the ledger rests on.
# --------------------------------------------------------------------------

_BINDS = "A green is not evidence: no AC box is ticked before its probe reports WITNESSED."


def _plan_with_batteries(pattern: str, *acs: tuple[int, str, str]) -> str:
    """``(number, flag, artifact-token)`` per criterion; artifact ``""`` writes none."""
    body = "**Status:** Draft\n" + f"**Batteries:** `{pattern}`\n\n" + _BINDS + "\n\n"
    for n, flag, art in acs:
        art_clause = f" *Artifact:* `{art}`." if art else ""
        body += f"- [{flag}] **AC-{n} [check] — a criterion.**{art_clause} Body.\n"
    return body


def _battery(root: Path, name: str, *sources: str) -> None:
    _write(
        root,
        f"tests/batteries/{name}",
        '{"claim_sources": '
        + str(list(sources)).replace("'", '"')
        + ', "probes": [], "exemptions": {}}',
    )


def test_a_ticked_ac_whose_artifact_is_in_no_battery_is_found(
    guard: ModuleType, tmp_path: Path
) -> None:
    """🔴 The s278 shape: AC-7 and AC-8 ticked while their modules were in no denominator."""
    _write(
        tmp_path,
        "docs/plans/0120-x.md",
        _plan_with_batteries(
            "tests/batteries/*.json", (1, "x", "tests/a/test_uncovered.py::test_it")
        ),
    )
    _battery(tmp_path, "b.json", "tests/a/test_something_else.py")
    gaps = guard.find_battery_gaps(tmp_path)
    assert [(g.ac, "test_uncovered.py" in g.reason) for g in gaps] == [(1, True)]


def test_a_ticked_ac_whose_artifact_is_covered_is_clean(guard: ModuleType, tmp_path: Path) -> None:
    """🟢 The positive control. Without it, a checker that always fired would pass above."""
    _write(
        tmp_path,
        "docs/plans/0120-x.md",
        _plan_with_batteries(
            "tests/batteries/*.json", (1, "x", "tests/a/test_covered.py::test_it")
        ),
    )
    _battery(tmp_path, "b.json", "tests/a/test_covered.py")
    assert guard.find_battery_gaps(tmp_path) == []


def test_a_bare_filename_artifact_matches_a_full_path_claim_source(
    guard: ModuleType, tmp_path: Path
) -> None:
    """🟢 Measured false positive, s278. PLANs write some artifacts as bare filenames and
    some as full paths; a raw string comparison accused four correct ACs on PLAN-0120."""
    _write(
        tmp_path,
        "docs/plans/0120-x.md",
        _plan_with_batteries("tests/batteries/*.json", (1, "x", "test_covered.py::test_it")),
    )
    _battery(tmp_path, "b.json", "tests/deep/nested/test_covered.py")
    assert guard.find_battery_gaps(tmp_path) == []


def test_a_plan_that_binds_ticks_to_probes_but_names_no_battery_is_found(
    guard: ModuleType, tmp_path: Path
) -> None:
    """🔴 The silent-exemption door: omit the header line and every tick goes unchecked."""
    _write(
        tmp_path,
        "docs/plans/0120-x.md",
        "**Status:** Draft\n\n" + _BINDS + "\n\n- [x] **AC-1 [check] — a criterion.** Body.\n",
    )
    gaps = guard.find_battery_gaps(tmp_path)
    assert len(gaps) == 1 and gaps[0].ac is None and "names no batteries" in gaps[0].reason


def test_an_unstarted_plan_with_no_ticks_is_not_accused(guard: ModuleType, tmp_path: Path) -> None:
    """🟢 Measured false positive, s278: unscoped, this fired on PLAN-0121 at 0 of 8 ticked.
    The check exists to catch an unjustified tick, not a plan nobody has started."""
    _write(
        tmp_path,
        "docs/plans/0121-x.md",
        "**Status:** Draft\n\n" + _BINDS + "\n\n- [ ] **AC-1 [check] — a criterion.** Body.\n",
    )
    assert guard.find_battery_gaps(tmp_path) == []


def test_a_batteries_glob_matching_nothing_is_an_error_not_a_skip(
    guard: ModuleType, tmp_path: Path
) -> None:
    """🔴 The vacuity door. A check that quietly passes when its evidence is absent is
    precisely the failure it exists to prevent, so an empty match must FAIL."""
    _write(
        tmp_path,
        "docs/plans/0120-x.md",
        _plan_with_batteries(
            "tests/batteries/nope-*.json", (1, "x", "tests/a/test_it.py::test_it")
        ),
    )
    gaps = guard.find_battery_gaps(tmp_path)
    assert len(gaps) == 1 and gaps[0].ac is None and "matches no files" in gaps[0].reason


def test_an_ac_with_no_test_artifact_is_not_a_gap(guard: ModuleType, tmp_path: Path) -> None:
    """🟢 PLAN-0120's AC-10 runs commands and names no test module. Not every AC has one."""
    _write(
        tmp_path,
        "docs/plans/0120-x.md",
        _plan_with_batteries("tests/batteries/*.json", (1, "x", "")),
    )
    _battery(tmp_path, "b.json", "tests/a/test_something.py")
    assert guard.find_battery_gaps(tmp_path) == []


def test_the_live_repo_has_no_battery_gaps(guard: ModuleType) -> None:
    """The guard must agree with the tree it ships in."""
    assert guard.find_battery_gaps(REPO_ROOT) == []
