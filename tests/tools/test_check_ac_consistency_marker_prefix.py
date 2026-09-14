"""AC lines that carry a status marker before their label (``tools/check_ac_consistency.py``).

🔴 **The blind spot these close, measured s298.** Archiving PLAN-0123 (13 ACs) dropped
the guard's count by **9**, not 13. Four of its AC lines put a status marker between
the checkbox and the bold label::

    - [ ] 🔴 **MEASURED s293 — FAILED on clause 2: …** **AC-9 [check-replay] — …

and the matcher anchored ``**AC-N`` directly after the box, so those four lines were
invisible to every check at once: a ``- [x]`` on one was never verified against its
battery (Check 3), a second AC wearing its label was never counted (Check 1), and a
STATUS closure claim about it was answered with "declares no AC-N" (Check 2).

**Every planted line below is a shape that really occurs.** Counted s298 across all
125 PLAN files in ``docs/plans/`` and ``docs/plans/done/`` — 1002 checkbox lines
carrying an AC token — the prefix between the box and ``**AC-N`` took exactly five
forms: none (976), a symbol plus a bold marker (PLAN-0123 AC-9..AC-12), two such
markers stacked (PLAN-0123 AC-12 at its closeout), an italic tick-note
(``done/0010``, ``done/0012``) and a strikethrough opener (``done/0049``).

Kept in its own module rather than appended to ``test_check_ac_consistency.py``: two
committed batteries take that module as their whole ``claim_sources`` denominator, and
new claims there would reopen both batteries' coverage without anyone touching them.
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


_BINDS = "A green is not evidence: no AC box is ticked before its probe reports WITNESSED."


def _plan_with_batteries(*lines: str) -> str:
    return (
        "**Status:** Draft\n**Batteries:** `tests/batteries/*.json`\n\n"
        + _BINDS
        + "\n\n"
        + "".join(f"{line}\n" for line in lines)
    )


def _battery(root: Path, *sources: str) -> None:
    listed = ", ".join(f'"{s}"' for s in sources)
    _write(
        root,
        "tests/batteries/b.json",
        f'{{"claim_sources": [{listed}], "probes": [], "exemptions": {{}}}}',
    )


def _marked_ac(artifact: str) -> str:
    """PLAN-0123 AC-9's real shape, ticked: a 🔴 marker, then the label, then its artifact."""
    return (
        "- [x] 🔴 **MEASURED s293 — FAILED on clause 2: `p=27.1 %` against the 5 % ceiling.** "
        "**AC-9 [check-replay] — the detector meets the kill criterion.** "
        f"*Artifact:* `{artifact}`."
    )


#: One line per measured prefix shape, plus the unprefixed shape as a reference point.
_MEASURED_SHAPES = (
    "- [ ] 🔴 **MEASURED s293 — FAILED on clause 2: `p=27.1 %` against the 5 % ceiling.** "
    "**AC-9 [check-replay] — the detector meets the kill criterion.** Body.\n"
    "- [ ] ⚖️ **RULED s298 — Cray, typed: `AC-12 = B`. Closed NOT MET.** 🔴 **READ s297 — "
    "the numeric half is NOT MET.** **AC-12 [live-ledger, judgment] — reached for.** Body.\n"
    "- [x] *(ticked 2026-07-11 s118 close — `tools/vero_bridge/server.py` is live: the "
    "`mcp__vero-bridge__*` tool surface answers)* **AC-2 — the bridge serves.** Body.\n"
    "- [ ] ~~**AC-5 — a struck criterion.**~~ Superseded.\n"
    "- [x] **AC-7 [check] — the unprefixed shape, unchanged.** Body.\n"
)


# --------------------------------------------------------------------------
# The parser itself
# --------------------------------------------------------------------------


def test_every_measured_marker_shape_is_parsed_with_its_own_box_state(guard: ModuleType) -> None:
    """🟢 The positive control every absence assertion below leans on.

    The box state is read from the checkbox and nowhere else. The marker is prose for a
    human — MEASURED, STRUCK, UNREACHABLE, READ, RULED, ticked — an open vocabulary no
    parser should try to interpret, and in all ten measured marker lines the author had
    already kept the box consistent with it.

    The ⚖️ marker quotes `AC-12` inside itself and the tick-note carries a `*` inside a
    code span; both are real, and both would derail a naive span matcher.
    """
    assert guard._AC_BOX.findall(_MEASURED_SHAPES) == [
        (" ", "9"),
        (" ", "12"),
        ("x", "2"),
        (" ", "5"),
        ("x", "7"),
    ]


def test_an_ac_referenced_in_prose_does_not_become_an_ac(guard: ModuleType) -> None:
    """🔴 NEGATIVE CONTROL: widening the matcher must not reach into prose.

    The first line is PLAN-0123 AC-10's shape: its own marker names AC-9 and AC-10, and
    its body names AC-11 — only AC-10 is an AC. The second line is a Step checkbox that
    bold-references an AC; a prefix rule of "anything, then **AC-N" makes it a phantom
    AC-4, which in an active PLAN would collide with the real one.

    Asserted as the exact list, not as absences: "AC-9 is not in the list" is satisfied
    by an empty list, so the one AC that IS there is what makes the absence mean anything.
    """
    text = (
        "- [ ] 🔴 **STRUCK s293 — its precondition AC-9 failed, and AC-10 is struck.** "
        "**AC-10 [check] — contingent on AC-9.** AC-11 runs after it.\n"
        "- [x] Step 3 — closes **AC-4** once AC-5 lands.\n"
    )
    assert guard._ac_labels(text) == [10]


def test_a_bold_ac_right_after_the_label_is_not_mistaken_for_the_label(
    guard: ModuleType,
) -> None:
    """🔴 A marker may not itself be an AC label.

    Without that exclusion a bold label can be consumed as a "marker", and whatever bold
    AC follows it on the line is read as the label instead — silently renumbering the AC.
    """
    text = "- [x] **AC-2 — a criterion.** **AC-3 is its sibling, named after it.**\n"
    assert guard._ac_labels(text) == [2]


# --------------------------------------------------------------------------
# The three checks, each of which was blind to a marker-prefixed AC
# --------------------------------------------------------------------------


def test_a_marker_prefixed_ticked_ac_whose_artifact_is_in_no_battery_is_found(
    guard: ModuleType, tmp_path: Path
) -> None:
    """🔴 THE s298 DEFECT (Check 3): a tick behind a marker was never verified.

    Before the fix this reported nothing at all — the guard printed `clean` over a ticked
    AC whose artifact no battery had ever probed. Two parsers had to learn the shape: the
    matcher, and the line lookup that fetched the AC's artifact clause, which matched
    `- [x] **AC-N ` literally and so skipped the line even once the matcher found it.
    """
    _write(
        tmp_path,
        "docs/plans/0123-x.md",
        _plan_with_batteries(_marked_ac("tests/a/test_uncovered.py::test_it")),
    )
    _battery(tmp_path, "tests/a/test_something_else.py")
    gaps = guard.find_battery_gaps(tmp_path)
    assert [(g.ac, "test_uncovered.py" in g.reason) for g in gaps] == [(9, True)]


def test_a_marker_prefixed_ticked_ac_whose_artifact_is_covered_is_clean(
    guard: ModuleType, tmp_path: Path
) -> None:
    """🟢 POSITIVE CONTROL for the defect above: without it, a check that fired on every
    marker-prefixed tick would pass there too."""
    _write(
        tmp_path,
        "docs/plans/0123-x.md",
        _plan_with_batteries(_marked_ac("tests/a/test_covered.py::test_it")),
    )
    _battery(tmp_path, "tests/a/test_covered.py")
    assert guard.find_battery_gaps(tmp_path) == []


def test_a_duplicate_label_hidden_behind_a_marker_is_found(
    guard: ModuleType, tmp_path: Path
) -> None:
    """🔴 Check 1: the second AC-9 wears a marker, and used to go uncounted."""
    _write(
        tmp_path,
        "docs/plans/0123-x.md",
        "**Status:** Draft\n\n"
        "- [ ] **AC-9 [check] — the first criterion.** Body.\n"
        "- [ ] 🔴 **MEASURED s293 — FAILED.** **AC-9 [check] — a second one.** Body.\n",
    )
    dupes = guard.find_duplicate_labels(tmp_path)
    assert [(d.plan, d.label, d.count) for d in dupes] == [("0123-x.md", 9, 2)]


def test_a_status_closure_of_an_unticked_marker_prefixed_ac_names_the_real_disagreement(
    guard: ModuleType, tmp_path: Path
) -> None:
    """🔴 Check 2: the claim was already refused, but for the WRONG reason.

    It read "PLAN-0123 declares no AC-9" — pointing the reader at a missing criterion that
    is sitting in the file — instead of the true finding, that STATUS and the checkbox
    disagree about a criterion that exists.
    """
    _write(
        tmp_path,
        "docs/plans/0123-x.md",
        "- [ ] 🔴 **MEASURED s293 — FAILED.** **AC-9 [check] — a criterion.** Body.\n",
    )
    _write(tmp_path, "docs/STATUS.md", "- **PLAN-0123 — ✅ AC-9 CLOSED s298.**\n")
    found = guard.find_status_mismatches(tmp_path)
    assert [(m.ac, "still has it as" in m.reason) for m in found] == [(9, True)]


# --------------------------------------------------------------------------
# Check 4 — an AC line the matcher cannot read fails LOUD
#
# The marker grammar is a closed list of the shapes measured at s298. The next new
# marker would otherwise reopen this exact blind spot, silently, the way this one was
# found: by a count that came out 4 short. So the guard refuses an active PLAN's AC
# line it cannot parse instead of quietly narrowing around it.
# --------------------------------------------------------------------------


def test_an_ac_line_behind_an_unrecognised_marker_is_reported(
    guard: ModuleType, tmp_path: Path
) -> None:
    """🔴 A plain-prose prefix is not a recognised marker, so the AC cannot be read."""
    _write(
        tmp_path,
        "docs/plans/0124-x.md",
        "**Status:** Draft\n\n- [x] Ruled by Cray: **AC-3 [check] — a criterion.** Body.\n",
    )
    found = guard.find_unparsed_ac_lines(tmp_path)
    assert [(u.plan, u.line) for u in found] == [("0124-x.md", 3)]


def test_no_measured_shape_is_reported_as_unparsed(guard: ModuleType, tmp_path: Path) -> None:
    """🟢 POSITIVE CONTROL for Check 4: every real shape is readable, so none is refused."""
    _write(tmp_path, "docs/plans/0123-x.md", "**Status:** Draft\n\n" + _MEASURED_SHAPES)
    assert guard.find_unparsed_ac_lines(tmp_path) == []


def test_the_live_repo_has_no_unparsed_ac_lines(guard: ModuleType) -> None:
    """The guard must agree with the tree it ships in."""
    assert guard.find_unparsed_ac_lines(REPO_ROOT) == []
