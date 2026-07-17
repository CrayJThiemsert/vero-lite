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


def test_thresholds_match_the_ratified_r4_numbers(guard: ModuleType) -> None:
    """R4 fixes both numbers verbatim ("stay under the 256 KB byte cap ... if a
    half-year file would exceed ~192 KB, start a `-b` continuation file"). Pinned so a
    future convenience-loosening has to argue with the policy, not just edit a
    constant."""
    assert guard.SPLIT_TRIGGER_BYTES == 192 * 1024
    assert guard.HARD_CAP_BYTES == 256 * 1024
    assert guard.SPLIT_TRIGGER_BYTES < guard.HARD_CAP_BYTES
