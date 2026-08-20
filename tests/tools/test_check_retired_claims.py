"""Tests for the retired-claim propagation guard (``tools/check_retired_claims.py``).

The two shapes that matter are not hypothetical — both are replays of the
session-241 incident the guard exists to close: a claim corrected in one file
that kept living in a **sibling script** for two months, and a second claim
corrected at the top of a file that kept living in that **same file's footer**
165 lines below. A guard that catches only the cross-file shape would have
found one of the two.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "tools" / "check_retired_claims.py"

#: Long enough to clear ``_MIN_RETIRED_LEN`` and distinctive enough that a match
#: cannot be coincidental.
CLAIM = "ms-s1-max has no WSL DNS entry"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_retired_claims", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def guard() -> ModuleType:
    return _load_module()


def _write(root: Path, rel: str, text: str) -> str:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return rel


def _marker(claim: str = CLAIM) -> str:
    return f'<!-- retired: "{claim}" -->\n'


# --------------------------------------------------------------------------
# The two real shapes
# --------------------------------------------------------------------------


def test_a_survivor_in_another_file_is_found(guard: ModuleType, tmp_path: Path) -> None:
    """The warm.sh shape: corrected in SKILL.md, still asserted in a sibling."""
    decl = _write(tmp_path, "skills/SKILL.md", f"corrected here.\n{_marker()}")
    stale = _write(tmp_path, "skills/warm.sh", f"# IP — {CLAIM}. Run with bash.\n")

    markers, problems = guard.collect_markers(tmp_path, [decl, stale])
    survivors = guard.find_survivors(tmp_path, [decl, stale], markers)

    assert problems == []
    assert [(s.path, s.line) for s in survivors] == [("skills/warm.sh", 1)]
    assert survivors[0].declared_at == "skills/SKILL.md:2"


def test_a_distant_survivor_in_the_same_file_is_found(guard: ModuleType, tmp_path: Path) -> None:
    """The footer shape, in the SAME file — the half a cross-file-only guard misses."""
    body = f"corrected at the top.\n{_marker()}" + "filler\n" * 40 + f"footer still says {CLAIM}.\n"
    rel = _write(tmp_path, "skills/SKILL.md", body)

    markers, _ = guard.collect_markers(tmp_path, [rel])
    survivors = guard.find_survivors(tmp_path, [rel], markers)

    assert len(survivors) == 1
    assert survivors[0].line == 43


# --------------------------------------------------------------------------
# What must NOT be flagged
# --------------------------------------------------------------------------


def test_the_correction_narrative_beside_the_marker_is_exempt(
    guard: ModuleType, tmp_path: Path
) -> None:
    """A correction almost always quotes the claim it is retiring."""
    rel = _write(
        tmp_path,
        "skills/SKILL.md",
        f"This section used to assert that {CLAIM}. Measured, it resolves.\n{_marker()}",
    )
    markers, _ = guard.collect_markers(tmp_path, [rel])
    assert guard.find_survivors(tmp_path, [rel], markers) == []


def test_the_marker_line_itself_is_never_a_survivor(guard: ModuleType, tmp_path: Path) -> None:
    """Two markers for one claim, far apart — neither may report the other."""
    body = _marker() + "filler\n" * 60 + _marker()
    rel = _write(tmp_path, "skills/SKILL.md", body)
    markers, _ = guard.collect_markers(tmp_path, [rel])
    assert len(markers) == 2
    assert guard.find_survivors(tmp_path, [rel], markers) == []


def test_an_unrelated_file_without_the_claim_is_clean(guard: ModuleType, tmp_path: Path) -> None:
    decl = _write(tmp_path, "skills/SKILL.md", _marker())
    other = _write(tmp_path, "docs/other.md", "reach MS-S1 by IP; the hostname resolves.\n")
    markers, _ = guard.collect_markers(tmp_path, [decl, other])
    assert guard.find_survivors(tmp_path, [decl, other], markers) == []


def test_no_markers_means_no_survivors(guard: ModuleType, tmp_path: Path) -> None:
    """The empty case is legitimate, and must not be mistaken for enforcement."""
    rel = _write(tmp_path, "docs/other.md", f"{CLAIM}\n")
    markers, problems = guard.collect_markers(tmp_path, [rel])
    assert markers == [] and problems == []
    assert guard.find_survivors(tmp_path, [rel], markers) == []


# --------------------------------------------------------------------------
# Scope: archives preserve superseded text on purpose
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rel",
    [
        "docs/status-archive/2026-h1-status.md",
        "docs/plans/done/0100-x.md",
    ],
)
def test_archives_are_neither_searched_nor_trusted_to_declare(
    guard: ModuleType, tmp_path: Path, rel: str
) -> None:
    decl = _write(tmp_path, "skills/SKILL.md", _marker())
    archived = _write(tmp_path, rel, f"the s171 note said {CLAIM}\n{_marker()}")

    markers, _ = guard.collect_markers(tmp_path, [decl, archived])
    survivors = guard.find_survivors(tmp_path, [decl, archived], markers)

    assert [m.path for m in markers] == ["skills/SKILL.md"], "an archive declares nothing"
    assert survivors == [], "an archive preserves superseded text by design"
    assert guard.is_scannable(rel) is False


def test_a_non_text_file_is_out_of_scope(guard: ModuleType) -> None:
    assert guard.is_scannable("docs/design/logo.png") is False
    assert guard.is_scannable("docs/runbooks/x.md") is True
    assert guard.is_scannable("tools/x.py") is True


# --------------------------------------------------------------------------
# Unusable markers fail loudly rather than matching half the repo
# --------------------------------------------------------------------------


def test_a_too_short_claim_is_refused_not_ignored(guard: ModuleType, tmp_path: Path) -> None:
    rel = _write(tmp_path, "skills/SKILL.md", '<!-- retired: "no DNS" -->\n')
    markers, problems = guard.collect_markers(tmp_path, [rel])
    assert markers == []
    assert len(problems) == 1
    assert "minimum is" in problems[0] and "skills/SKILL.md:1" in problems[0]


def test_own_machinery_markers_are_illustrations_not_declarations(
    guard: ModuleType,
) -> None:
    """The tool, its test and the convention doc show examples, not declarations.

    Without this, the marker in this file's own ``_marker()`` helper — and the
    examples in the tool's docstring — would retire a sample claim repo-wide.
    """
    assert "tools/check_retired_claims.py" in guard._OWN_MACHINERY
    assert "tests/tools/test_check_retired_claims.py" in guard._OWN_MACHINERY
    assert "docs/conventions/retired-claims.md" in guard._OWN_MACHINERY

    markers, problems = guard.collect_markers(REPO_ROOT, sorted(guard._OWN_MACHINERY))
    assert markers, "the docs really do carry examples; this would pass vacuously otherwise"
    assert all(m.local_only for m in markers)
    assert problems == [], "a placeholder like `<text>` must not trip the length floor"


def test_an_illustration_retires_nothing_for_other_files(guard: ModuleType, tmp_path: Path) -> None:
    """A doc example must not put a claim under search repo-wide."""
    doc = _write(tmp_path, "docs/conventions/retired-claims.md", _marker())
    elsewhere = _write(tmp_path, "docs/other.md", f"still says {CLAIM}\n")

    markers, _ = guard.collect_markers(tmp_path, [doc, elsewhere])
    assert [m.local_only for m in markers] == [True]
    assert guard.find_survivors(tmp_path, [doc, elsewhere], markers) == []


def test_an_illustration_still_exempts_its_own_neighbourhood(
    guard: ModuleType, tmp_path: Path
) -> None:
    """The bug that blocked this guard's own first commit.

    The convention doc could not declare, so it could not build an exempt window
    either — and its worked example was reported as a survivor of the very claim
    it was documenting.
    """
    real = _write(tmp_path, "skills/SKILL.md", _marker())
    doc = _write(
        tmp_path,
        "docs/conventions/retired-claims.md",
        f"worked example: {CLAIM}\n{_marker()}",
    )

    markers, _ = guard.collect_markers(tmp_path, [real, doc])
    assert guard.find_survivors(tmp_path, [real, doc], markers) == []


def test_own_machinery_is_still_searched_for_survivors(guard: ModuleType, tmp_path: Path) -> None:
    """Exempting a file from DECLARING must not exempt it from being SEARCHED."""
    decl = _write(tmp_path, "skills/SKILL.md", _marker())
    tool = _write(tmp_path, "tools/check_retired_claims.py", f"# stale: {CLAIM}\n")

    markers, _ = guard.collect_markers(tmp_path, [decl, tool])
    survivors = guard.find_survivors(tmp_path, [decl, tool], markers)

    assert [s.path for s in survivors] == ["tools/check_retired_claims.py"]


# --------------------------------------------------------------------------
# Robustness
# --------------------------------------------------------------------------


def test_an_absent_file_is_skipped_not_fatal(guard: ModuleType, tmp_path: Path) -> None:
    markers, problems = guard.collect_markers(tmp_path, ["docs/gone.md"])
    assert markers == [] and problems == []
    assert guard.find_survivors(tmp_path, ["docs/gone.md"], []) == []


def test_two_claims_report_independently(guard: ModuleType, tmp_path: Path) -> None:
    """Disjoint claims must not collapse into one another's report."""
    second = "the active PLAN/handoff is where the gate lives"
    decl = _write(tmp_path, "skills/SKILL.md", _marker() + _marker(second))
    a = _write(tmp_path, "skills/warm.sh", f"# {CLAIM}\n")
    b = _write(tmp_path, "docs/footer.md", f"see {second}\n")

    markers, _ = guard.collect_markers(tmp_path, [decl, a, b])
    survivors = guard.find_survivors(tmp_path, [decl, a, b], markers)

    assert {(s.path, s.text) for s in survivors} == {
        ("skills/warm.sh", CLAIM),
        ("docs/footer.md", second),
    }


# --------------------------------------------------------------------------
# The live repo
# --------------------------------------------------------------------------


def test_the_live_repo_has_no_surviving_retired_claim(guard: ModuleType) -> None:
    """The guard's real assertion, run against the tree it ships in.

    Non-vacuity is established in the PR rather than here: replaying the real
    pre-fix ``warm.sh`` reddened this with ``warm.sh:11``, and re-injecting the
    real pre-fix footer reddened it with ``SKILL.md:212`` — two mutations, two
    disjoint reports.
    """
    files = guard._tracked_files(REPO_ROOT)
    markers, problems = guard.collect_markers(REPO_ROOT, files)
    survivors = guard.find_survivors(REPO_ROOT, files, markers)

    assert problems == [], f"unusable markers: {problems}"
    assert survivors == [], f"retired claims still live: {[(s.path, s.line) for s in survivors]}"
    assert markers, "no markers found — this assertion would pass vacuously"
