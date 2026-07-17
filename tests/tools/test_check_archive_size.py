"""Tests for the status-archive pre-commit size guard (rotation policy R4).

Contract-level per Lesson #7 §3 / the pre-ship checklist: drive the public
``main()`` via the ``ARCHIVE_SIZE_DIR`` override (the same env-override family
as the hook scripts), not the module internals.

``test_live_archives_are_within_cap`` is the one that binds: it is the
``test_live_status_is_within_hard_ceiling`` analogue for R4, and unlike the
pre-commit hook it runs in CI on every PR, where ``--no-verify`` cannot reach
it.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "tools" / "check_archive_size.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_archive_size", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_archive_size"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def guard() -> ModuleType:
    return _load_module()


def _run(guard: ModuleType, monkeypatch: pytest.MonkeyPatch, directory: Path) -> int:
    monkeypatch.setenv("ARCHIVE_SIZE_DIR", str(directory))
    return int(guard.main())


def _archive(directory: Path, name: str, size: int) -> Path:
    f = directory / name
    f.write_bytes(b"x" * size)
    return f


def test_under_split_trigger_passes(
    guard: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _archive(tmp_path, "2026-h1-status.md", 1024)
    assert _run(guard, monkeypatch, tmp_path) == 0


def test_over_split_trigger_warns_but_passes(
    guard: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _archive(tmp_path, "2026-h1-status.md", guard.SPLIT_TRIGGER_BYTES + 1)
    assert _run(guard, monkeypatch, tmp_path) == 0
    assert "split trigger" in capsys.readouterr().out


def test_over_hard_cap_fails(
    guard: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _archive(tmp_path, "2026-h1-status.md", guard.HARD_CAP_BYTES + 1)
    assert _run(guard, monkeypatch, tmp_path) == 1
    err = capsys.readouterr().err
    assert "HARD cap" in err
    assert "continuation" in err  # points the committer at the fix


def test_a_file_over_the_cap_is_not_also_reported_as_a_warning(
    guard: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """One file, one verdict — a breach reports as a FAILURE, never additionally as a
    passing warning. Guards against the over-cap file being double-counted into the
    warn list (it is over the trigger too, arithmetically)."""
    _archive(tmp_path, "2026-h1-status.md", guard.HARD_CAP_BYTES + 1)
    assert _run(guard, monkeypatch, tmp_path) == 1
    captured = capsys.readouterr()
    assert "split trigger" not in captured.out
    assert "HARD cap" in captured.err


def test_every_archive_is_checked_not_just_the_first(
    guard: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A compliant file must not mask a breaching sibling. The real archive holds a
    compliant ``-b`` next to the breaching base file, so a guard that stopped at the
    first hit — or globbed only one name — would have reported clean on session 144's
    actual 3x breach."""
    _archive(tmp_path, "2026-h1b-status.md", 1024)  # sorts FIRST, compliant
    _archive(tmp_path, "2026-h1-status.md", guard.HARD_CAP_BYTES + 1)
    assert _run(guard, monkeypatch, tmp_path) == 1
    assert "2026-h1-status.md" in capsys.readouterr().err


def test_non_markdown_files_are_ignored(
    guard: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _archive(tmp_path, "notes.txt", guard.HARD_CAP_BYTES + 1)
    assert _run(guard, monkeypatch, tmp_path) == 0


def test_missing_directory_is_not_a_failure(
    guard: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert _run(guard, monkeypatch, tmp_path / "absent") == 0


def test_live_archives_are_within_cap(guard: ModuleType) -> None:
    """The repo's actual archives must respect their own policy — the R4 analogue of
    ``test_live_status_is_within_hard_ceiling``.

    **This is the binding check.** The pre-commit hook is the local half: it is
    ``files:``-scoped, skippable with ``--no-verify``, and CI does not run pre-commit at
    all (``ci.yml`` runs ruff / mypy / alembic / pytest). This test runs in CI on every
    PR, where none of those escapes reach it.

    It could not land with the guard in #789: ``2026-h1-status.md`` was 592,577 B —
    2.26x the cap — so this assertion was RED until the session-144 split made it green.
    That ordering was the point, not an accident: a guard whose own live assertion is
    RED cannot merge into a protected main, so the mechanism landed first and the split
    second.

    Asserted against the CAP, not the split trigger, deliberately — mirroring R1, whose
    live test pins the hard ceiling and lets the soft target warn. A file may sit over the
    trigger without being wrong: the ``session 25`` block is 162,823 B and indivisible, so
    whichever file holds it is large by necessity, not by packing choice.

    _(Kept at the cap after the session-144 splits took every live archive under the
    TRIGGER too. Tightening this to the trigger would pin a property that is currently
    true by luck of where the blocks fell, and would turn the next legitimate oversized
    block into a spurious failure.)_"""
    archive = REPO_ROOT / "docs" / "status-archive"
    assert archive.is_dir(), "the archive directory moved — R4's rotation target"
    oversized = {
        p.name: p.stat().st_size
        for p in sorted(archive.glob("*.md"))
        if p.stat().st_size > guard.HARD_CAP_BYTES
    }
    assert not oversized, (
        f"archive files over R4's {guard.HARD_CAP_BYTES:,}-byte cap: {oversized}. "
        f"Split per R4: letters ascend with time, the base file keeps the RECENT window, "
        f"older content spills into the next letter (Cray-ratified, session 144)."
    )


def test_live_archive_chain_is_greppable_as_one_corpus(guard: ModuleType) -> None:
    """Every archive file is reachable by a single glob — the property R4's Tier-3
    contract ("grep + windowed reads only") actually rests on.

    The split traded one 592 KB file for a chain. That is only safe if the chain is
    discoverable: a reader who greps ``docs/status-archive/*.md`` must still see the whole
    corpus. Pinned because the failure mode is silent — a continuation dropped somewhere
    else would leave greps quietly incomplete rather than erroring."""
    archive = REPO_ROOT / "docs" / "status-archive"
    names = {p.name for p in archive.glob("*.md")}
    assert {
        "2026-h1b-status.md",
        "2026-h1-status.md",
    } <= names, f"the archive chain's endpoints are missing from the glob: {sorted(names)}"
    assert all(p.stat().st_size > 0 for p in archive.glob("*.md")), "an empty archive file"


def test_thresholds_match_the_ratified_r4_numbers(guard: ModuleType) -> None:
    """R4 fixes both numbers verbatim ("stay under the 256 KB byte cap ... if a
    half-year file would exceed ~192 KB, start a `-b` continuation file"). Pinned so a
    future convenience-loosening has to argue with the policy, not just edit a
    constant."""
    assert guard.SPLIT_TRIGGER_BYTES == 192 * 1024
    assert guard.HARD_CAP_BYTES == 256 * 1024
    assert guard.SPLIT_TRIGGER_BYTES < guard.HARD_CAP_BYTES
