"""Tests for tools/handoffs/validate_handoff.py (CLI)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

_TOOLS = Path(__file__).resolve().parents[2] / "tools" / "handoffs"


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, _TOOLS / f"{name}.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_load("_schema")  # register so the CLI's `from _schema import ...` resolves
vh = _load("validate_handoff")


_VALID = """---
from: claude-chat-session-10
to: claude-code-session-13
actor: chat
session: 10
batch: demo-batch
phase: dispatch
status: READY
created: 2026-05-19T02:00:00+07:00
title: demo handoff
---

body
"""


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_single_valid_file_exit_0(tmp_path: Path) -> None:
    """A schema-clean file makes the CLI exit 0."""
    p = _write(tmp_path / "2026-05-19-0200-chat-demo.md", _VALID)
    assert vh.main([str(p)]) == 0


def test_single_invalid_file_exit_1(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A file with a bad enum value makes the CLI exit 1 and print it."""
    p = _write(
        tmp_path / "2026-05-19-0200-chat-demo.md",
        _VALID.replace("phase: dispatch", "phase: wrong"),
    )
    assert vh.main([str(p)]) == 1
    assert "phase" in capsys.readouterr().out


def test_all_walks_directory(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """--all validates every file under --root and reports per file."""
    _write(tmp_path / "2026-05-19-0200-chat-ok.md", _VALID)
    _write(
        tmp_path / "2026-05-19-0300-chat-bad.md",
        _VALID.replace("actor: chat", "actor: nope"),
    )
    code = vh.main(["--all", "--root", str(tmp_path)])
    assert code == 1
    assert "2026-05-19-0300-chat-bad.md" in capsys.readouterr().out


def test_quiet_suppresses_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """--quiet keeps the exit-code contract but prints nothing."""
    p = _write(
        tmp_path / "2026-05-19-0200-chat-demo.md",
        _VALID.replace("status: READY", "status: BOGUS"),
    )
    assert vh.main([str(p), "--quiet"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_no_inputs_exit_2(capsys: pytest.CaptureFixture[str]) -> None:
    """No PATHs and no --all is an invocation error (exit 2)."""
    assert vh.main([]) == 2
    assert "error:" in capsys.readouterr().err
