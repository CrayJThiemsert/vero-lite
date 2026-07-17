"""Tests for the STATUS.md line-number citation guard (rotation policy R7).

Contract-level per Lesson #7 §3 / the pre-ship checklist: drive the public
``find_violations`` / ``main()`` surface, not module internals.

These tests deliberately do **not** require a working ``git`` in the checkout.
``find_violations`` takes the file list as a parameter precisely so the pattern
+ allowlist logic is testable without enumeration, and the one test that does
need enumeration (`test_live_repo_obeys_r7`) skips explicitly rather than
silently passing.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "tools" / "check_status_citations.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_status_citations", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_status_citations"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def guard() -> ModuleType:
    return _load_module()


def _write(root: Path, rel: str, text: str) -> Path:
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return Path(rel)


# --- the pattern: what R7 forbids -------------------------------------------


def test_line_citation_is_found(guard: ModuleType, tmp_path: Path) -> None:
    rel = _write(tmp_path, "docs/adr/0029-x.md", "see `docs/STATUS.md:132` for it\n")
    violations = guard.find_violations(tmp_path, [rel])
    assert len(violations) == 1
    assert violations[0][0] == "docs/adr/0029-x.md"
    assert violations[0][1] == 1


def test_range_citation_is_found(guard: ModuleType, tmp_path: Path) -> None:
    """`STATUS.md:264-286` (PLAN-0079's real shape) must be caught too."""
    rel = _write(tmp_path, "docs/plans/0079-x.md", "edits): `docs/STATUS.md:264-286`\n")
    assert len(guard.find_violations(tmp_path, [rel])) == 1


def test_citation_without_path_prefix_is_found(guard: ModuleType, tmp_path: Path) -> None:
    """PLAN-0063:234's real shape — bare `STATUS.md:276,292`, no `docs/`."""
    rel = _write(tmp_path, "docs/plans/done/0063-x.md", "(`STATUS.md:276,292`). A Step\n")
    assert len(guard.find_violations(tmp_path, [rel])) == 1


def test_reports_every_violating_line(guard: ModuleType, tmp_path: Path) -> None:
    rel = _write(tmp_path, "docs/adr/0029-x.md", "`STATUS.md:1`\nclean\n`STATUS.md:2`\n")
    assert [v[1] for v in guard.find_violations(tmp_path, [rel])] == [1, 3]


# --- the prescribed alternatives must PASS (else the rule is unusable) -------


def test_section_name_citation_is_allowed(guard: ModuleType, tmp_path: Path) -> None:
    """R7's own prescribed replacement must not trip the guard it prescribes."""
    rel = _write(tmp_path, "docs/adr/0029-x.md", 'see `docs/STATUS.md` §"Active TODOs"\n')
    assert guard.find_violations(tmp_path, [rel]) == []


def test_bare_status_reference_is_allowed(guard: ModuleType, tmp_path: Path) -> None:
    rel = _write(tmp_path, "docs/adr/0029-x.md", "current state: `docs/STATUS.md`\n")
    assert guard.find_violations(tmp_path, [rel]) == []


def test_other_files_line_refs_are_untouched(guard: ModuleType, tmp_path: Path) -> None:
    """R7 is about STATUS only — a code line-ref stays a good citation."""
    rel = _write(tmp_path, "docs/adr/0029-x.md", "`services/db/audit_log.py:17-18`\n")
    assert guard.find_violations(tmp_path, [rel]) == []


# --- the allowlist ----------------------------------------------------------


@pytest.mark.parametrize(
    "rel",
    ["docs/STATUS.md", "docs/runbooks/memory-architecture.md"],
)
def test_allowlisted_files_are_exempt(guard: ModuleType, tmp_path: Path, rel: str) -> None:
    path = _write(tmp_path, rel, "narrative about `docs/STATUS.md:132` history\n")
    assert guard.find_violations(tmp_path, [path]) == []


def test_status_archive_is_exempt(guard: ModuleType, tmp_path: Path) -> None:
    """R4 makes this mandatory: archives are move-only, never rewritten."""
    rel = _write(tmp_path, "docs/status-archive/2026-h1-status.md", "`STATUS.md:262`\n")
    assert guard.find_violations(tmp_path, [rel]) == []


def test_done_plans_are_not_exempt(guard: ModuleType, tmp_path: Path) -> None:
    """Deliberate: exempting `done/` would let a PLAN launder a violation by
    being archived. An archived PLAN is still a tracked artifact a reader
    follows."""
    rel = _write(tmp_path, "docs/plans/done/0063-x.md", "`docs/STATUS.md:276`\n")
    assert len(guard.find_violations(tmp_path, [rel])) == 1


def test_guards_own_machinery_is_exempt(guard: ModuleType) -> None:
    """The guard and its tests must spell the pattern to match/test it.

    Caught by the guard itself at commit time: staging made these two files
    tracked, so `git ls-files` picked them up and the guard reported its own
    fixtures as violations. Exempt for the same reason the runbook is — they
    define the rule rather than cite STATUS.
    """
    assert guard.is_allowlisted("tools/check_status_citations.py")
    assert guard.is_allowlisted("tests/tools/test_check_status_citations.py")
    # ...but nothing else under tools/ or tests/ gets a free pass.
    assert not guard.is_allowlisted("tools/check_status_size.py")
    assert not guard.is_allowlisted("tests/tools/test_check_status_size.py")


def test_allowlist_is_exact_not_substring(guard: ModuleType) -> None:
    assert guard.is_allowlisted("docs/STATUS.md")
    assert not guard.is_allowlisted("docs/STATUS.md.bak")
    assert not guard.is_allowlisted("docs/plans/STATUS.md")
    assert guard.is_allowlisted("docs/status-archive/2026-h1-status.md")
    assert not guard.is_allowlisted("docs/status-archive-notes.md")


# --- fail-closed: the regression test for the bug this guard shipped with ----


def test_enumeration_failure_fails_closed(
    guard: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A non-git tree must exit 1, never 0.

    Regression: the first cut swallowed `git ls-files` failure into an empty
    file list, so the guard reported a CLEAN tree while 10 known violations sat
    on disk (this worktree's UNC gitdir is unresolvable from WSL). "Nothing to
    check" and "I failed to look" must never collapse to the same answer.
    """
    monkeypatch.setenv("STATUS_CITATION_ROOT", str(tmp_path))
    assert guard.main() == 1
    err = capsys.readouterr().err
    assert "cannot enumerate" in err
    assert "Failing closed" in err


def test_unreadable_file_is_skipped_not_fatal(guard: ModuleType, tmp_path: Path) -> None:
    rel = tmp_path / "docs" / "img.png"
    rel.parent.mkdir(parents=True, exist_ok=True)
    rel.write_bytes(b"\x89PNG\r\n\x1a\n\xff\xfe")
    assert guard.find_violations(tmp_path, [Path("docs/img.png")]) == []


def test_absent_file_is_skipped_not_fatal(guard: ModuleType, tmp_path: Path) -> None:
    """A staged-but-deleted path is enumerated by git yet absent on disk."""
    assert guard.find_violations(tmp_path, [Path("docs/gone.md")]) == []


# --- the live invariant -----------------------------------------------------


def test_live_repo_obeys_r7(guard: ModuleType) -> None:
    """The repo itself must carry no line-number citations of STATUS.

    Skips (loudly) where `git ls-files` cannot run — this worktree's `.git`
    points at a UNC gitdir WSL git cannot resolve. It runs for real in a normal
    checkout (CI, main tree), which is where it matters.
    """
    try:
        files = guard.tracked_files(REPO_ROOT)
    except guard.EnumerationError as exc:
        pytest.skip(f"git enumeration unavailable here: {exc}")
    violations = guard.find_violations(REPO_ROOT, files)
    assert violations == [], "R7 violations: " + "; ".join(f"{p}:{n}" for p, n, _ in violations)
