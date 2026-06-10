"""Tests for the STATUS.md pre-commit size guard (rotation policy R1).

Contract-level per Lesson #7 §3 / the pre-ship checklist: drive the public
``main()`` via the ``STATUS_SIZE_PATH`` override (the same env-override family
as the hook scripts), not the module internals.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "tools" / "check_status_size.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_status_size", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_status_size"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def guard() -> ModuleType:
    return _load_module()


def _run(guard: ModuleType, monkeypatch: pytest.MonkeyPatch, target: Path) -> int:
    monkeypatch.setenv("STATUS_SIZE_PATH", str(target))
    return int(guard.main())


def test_under_soft_target_passes(
    guard: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    f = tmp_path / "STATUS.md"
    f.write_bytes(b"x" * 1024)
    assert _run(guard, monkeypatch, f) == 0


def test_over_soft_target_warns_but_passes(
    guard: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    f = tmp_path / "STATUS.md"
    f.write_bytes(b"x" * (guard.SOFT_TARGET_BYTES + 1))
    assert _run(guard, monkeypatch, f) == 0
    out = capsys.readouterr().out
    assert "soft target" in out


def test_over_hard_ceiling_fails(
    guard: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    f = tmp_path / "STATUS.md"
    f.write_bytes(b"x" * (guard.HARD_CEILING_BYTES + 1))
    assert _run(guard, monkeypatch, f) == 1
    err = capsys.readouterr().err
    assert "HARD ceiling" in err
    assert "rotation" in err  # points the committer at the fix


def test_missing_file_is_not_a_failure(
    guard: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert _run(guard, monkeypatch, tmp_path / "absent.md") == 0


def test_live_status_is_within_hard_ceiling(guard: ModuleType) -> None:
    """The repo's actual STATUS.md must respect its own policy."""
    live = REPO_ROOT / "docs" / "STATUS.md"
    assert live.stat().st_size <= guard.HARD_CEILING_BYTES
