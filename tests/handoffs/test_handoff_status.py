"""Tests for tools/handoffs/handoff_status.py (CLI reader)."""

from __future__ import annotations

import importlib.util
import io
import json
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


_load("_schema")
hs = _load("handoff_status")


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


def _session(tmp_path: Path) -> Path:
    d = tmp_path / "session-10"
    d.mkdir()
    return d


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_empty_session_zero_counts(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """An empty session dir summarizes to zero totals."""
    _session(tmp_path)
    assert hs.main(["10", "--root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "Total handoffs: 0" in out


def test_counts_by_phase_and_status(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Two files are counted by phase and status."""
    d = _session(tmp_path)
    _write(d / "2026-05-19-0200-chat-a.md", _VALID)
    _write(
        d / "2026-05-19-0300-code-b.md",
        _VALID.replace("actor: chat", "actor: code")
        .replace("phase: dispatch", "phase: closeout")
        .replace("status: READY", "status: DONE"),
    )
    assert hs.main(["session-10", "--root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "Total handoffs: 2" in out
    assert "dispatch=1" in out
    assert "closeout=1" in out
    assert "DONE=1" in out


def test_pause_redispatch_chain_detected(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Three files in one batch with a PAUSED step form a chain, linked
    via references_predecessor_handoffs."""
    d = _session(tmp_path)
    _write(
        d / "2026-05-19-0100-chat-x.md",
        _VALID.replace("status: READY", "status: PAUSED").replace(
            "created: 2026-05-19T02:00:00+07:00", "created: 2026-05-19T01:00:00+07:00"
        ),
    )
    _write(
        d / "2026-05-19-0200-chat-x.md",
        _VALID.replace("status: READY", "status: PAUSED")
        + "references_predecessor_handoffs:\n  - 2026-05-19-0100-chat-x.md\n",
    )
    _write(
        d / "2026-05-19-0300-chat-x.md",
        _VALID.replace("status: READY", "status: DONE").replace(
            "created: 2026-05-19T02:00:00+07:00", "created: 2026-05-19T03:00:00+07:00"
        )
        + "references_predecessor_handoffs:\n  - 2026-05-19-0200-chat-x.md\n",
    )
    assert hs.main(["10", "--root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "Pause-and-redispatch chains: 1" in out
    assert "PAUSED → PAUSED → DONE" in out


def test_json_mode_parseable(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """--json emits valid JSON with the expected keys."""
    d = _session(tmp_path)
    _write(d / "2026-05-19-0200-chat-a.md", _VALID)
    assert hs.main(["10", "--root", str(tmp_path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert isinstance(payload, list)
    assert payload[0]["total"] == 1
    assert payload[0]["session"] == "session-10"


def test_no_selector_exit_2(capsys: pytest.CaptureFixture[str]) -> None:
    """Neither a session selector nor --all is an invocation error."""
    assert hs.main([]) == 2
    assert "error:" in capsys.readouterr().err


# --- PLAN-004 Phase B: --index and --watch ---


def test_index_flag_writes_index_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """--index writes INDEX.md listing the session's handoffs."""
    d = _session(tmp_path)
    _write(d / "2026-05-19-0200-chat-a.md", _VALID)
    assert hs.main(["10", "--root", str(tmp_path), "--index"]) == 0
    index = d / "INDEX.md"
    assert index.exists()
    assert "2026-05-19-0200-chat-a.md" in index.read_text(encoding="utf-8")
    assert "wrote" in capsys.readouterr().out


def test_index_flag_idempotent(tmp_path: Path) -> None:
    """Two --index runs over an unchanged session produce identical bytes."""
    d = _session(tmp_path)
    _write(d / "2026-05-19-0200-chat-a.md", _VALID)
    assert hs.main(["10", "--root", str(tmp_path), "--index"]) == 0
    first = (d / "INDEX.md").read_text(encoding="utf-8")
    assert hs.main(["10", "--root", str(tmp_path), "--index"]) == 0
    assert (d / "INDEX.md").read_text(encoding="utf-8") == first


def test_index_excluded_from_counts(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """After INDEX.md exists, the summary still counts only real handoffs."""
    d = _session(tmp_path)
    _write(d / "2026-05-19-0200-chat-a.md", _VALID)
    hs.main(["10", "--root", str(tmp_path), "--index"])
    capsys.readouterr()  # drain the --index output
    assert hs.main(["10", "--root", str(tmp_path)]) == 0
    assert "Total handoffs: 1" in capsys.readouterr().out


def test_index_missing_session_dir_exit_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--index against a non-existent session dir is an invocation error."""
    assert hs.main(["99", "--root", str(tmp_path), "--index"]) == 2
    assert "error:" in capsys.readouterr().err


def test_watch_runs_bounded_ticks(tmp_path: Path) -> None:
    """run_watch renders `ticks` frames with an injected sleep (no hang)."""
    d = _session(tmp_path)
    _write(d / "2026-05-19-0200-chat-a.md", _VALID)
    args = hs.build_arg_parser().parse_args(
        ["10", "--root", str(tmp_path), "--watch", "--interval", "0.01"]
    )
    sleeps: list[float] = []
    buf = io.StringIO()
    assert hs.run_watch(args, ticks=3, sleep_fn=sleeps.append, out=buf) == 0
    assert buf.getvalue().count("Total handoffs: 1") == 3
    assert len(sleeps) == 2  # 3 frames → 2 inter-frame sleeps
