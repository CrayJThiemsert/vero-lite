"""Tests for tools/handoffs/render_transcript.py.

The tool lives under ``tools/`` (a non-package scripts directory), so it
is loaded by file path via importlib rather than a normal import.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_TOOL_PATH = Path(__file__).resolve().parents[1] / "tools" / "handoffs" / "render_transcript.py"


def _load_module() -> ModuleType:
    """Load the render_transcript module from its file path."""
    spec = importlib.util.spec_from_file_location("render_transcript", _TOOL_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclasses + `from __future__ import
    # annotations` can resolve the module via sys.modules during class
    # creation.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rt = _load_module()


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> Path:
    """Write records as a JSONL file and return the path."""
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
        encoding="utf-8",
    )
    return path


def _sample_records() -> list[dict[str, Any]]:
    return [
        {"type": "queue-operation", "operation": "enqueue"},
        {
            "type": "user",
            "timestamp": "2026-05-16T00:00:00Z",
            "message": {"role": "user", "content": "hello จาก Cray"},
        },
        {
            "type": "assistant",
            "timestamp": "2026-05-16T00:00:01Z",
            "gitBranch": "main",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "thinking", "thinking": "secret reasoning", "signature": "x"},
                    {"type": "text", "text": "visible answer"},
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "Bash",
                        "input": {"command": "echo hi"},
                    },
                ],
            },
        },
        {
            "type": "user",
            "timestamp": "2026-05-16T00:00:02Z",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_1",
                        "content": "hi",
                        "is_error": False,
                    }
                ],
            },
        },
    ]


def test_encode_project_path() -> None:
    """Non-alphanumerics collapse to single dashes, lower-cased."""
    encoded = rt.encode_project_path(r"\\wsl.localhost\ubuntu-24.04\home\crayj\work\vero-lite")
    assert encoded == "--wsl-localhost-ubuntu-24-04-home-crayj-work-vero-lite"


def test_iter_records_skips_blank_and_bad(tmp_path: Path) -> None:
    """Blank lines and invalid JSON are skipped; dicts are yielded."""
    p = tmp_path / "s.jsonl"
    p.write_text('{"a":1}\n\nnot-json\n[1,2,3]\n{"b":2}\n', encoding="utf-8")
    rows = list(rt.iter_records(p))
    assert rows == [{"a": 1}, {"b": 2}]


def test_resolve_jsonl_explicit_path(tmp_path: Path) -> None:
    """An existing explicit path resolves to itself."""
    p = _write_jsonl(tmp_path / "abc.jsonl", [{"type": "user"}])
    assert rt.resolve_jsonl(str(p), None, latest=False) == p


def test_resolve_jsonl_by_session_id(tmp_path: Path) -> None:
    """A bare session id resolves under the project dir."""
    _write_jsonl(tmp_path / "sid.jsonl", [{"type": "user"}])
    assert rt.resolve_jsonl("sid", tmp_path, latest=False) == tmp_path / "sid.jsonl"


def test_resolve_jsonl_latest(tmp_path: Path) -> None:
    """--latest picks the most recently modified .jsonl."""
    old = _write_jsonl(tmp_path / "old.jsonl", [{"type": "user"}])
    new = _write_jsonl(tmp_path / "new.jsonl", [{"type": "user"}])
    os.utime(old, (1_000, 1_000))
    os.utime(new, (2_000, 2_000))
    assert rt.resolve_jsonl(None, tmp_path, latest=True) == new


def test_resolve_jsonl_errors(tmp_path: Path) -> None:
    """Unresolvable inputs raise clear errors."""
    with pytest.raises(FileNotFoundError):
        rt.resolve_jsonl("missing", tmp_path, latest=False)
    with pytest.raises(ValueError, match="project-dir"):
        rt.resolve_jsonl(None, None, latest=True)


def test_render_full(tmp_path: Path) -> None:
    """Full render includes thinking, text, tool_use and tool_result."""
    p = _write_jsonl(tmp_path / "s.jsonl", _sample_records())
    md = rt.render_transcript(p, rt.RenderOptions())
    assert "# Transcript" in md
    assert "hello จาก Cray" in md  # unicode preserved
    assert "[thinking]" in md
    assert "secret reasoning" in md
    assert "visible answer" in md
    assert "[tool_use]" in md
    assert "echo hi" in md
    assert "[tool_result]" in md
    # queue-operation is metadata noise and must not render a turn.
    assert "queue-operation" not in md.split("---", 1)[1]


def test_render_no_thinking_no_tools(tmp_path: Path) -> None:
    """Filters drop thinking and tool blocks."""
    p = _write_jsonl(tmp_path / "s.jsonl", _sample_records())
    md = rt.render_transcript(p, rt.RenderOptions(include_thinking=False, include_tools=False))
    assert "secret reasoning" not in md
    assert "[tool_use]" not in md
    assert "[tool_result]" not in md
    assert "visible answer" in md


def test_render_last_turns(tmp_path: Path) -> None:
    """--last keeps only the final N rendered turns."""
    p = _write_jsonl(tmp_path / "s.jsonl", _sample_records())
    md = rt.render_transcript(p, rt.RenderOptions(last_turns=1))
    assert "[tool_result]" in md
    assert "hello จาก Cray" not in md


def test_render_error_flag_and_truncation(tmp_path: Path) -> None:
    """tool_result error flag is shown; max_block_chars truncates."""
    records = [
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "t",
                        "content": "X" * 50,
                        "is_error": True,
                    }
                ],
            },
        }
    ]
    p = _write_jsonl(tmp_path / "s.jsonl", records)
    md = rt.render_transcript(p, rt.RenderOptions(max_block_chars=10))
    assert "[tool_result (error)]" in md
    assert "truncated 40 chars" in md


def test_tool_result_list_content(tmp_path: Path) -> None:
    """tool_result whose content is a list of blocks is flattened."""
    records = [
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "t",
                        "content": [
                            {"type": "text", "text": "line-A"},
                            {"type": "image"},
                        ],
                    }
                ],
            },
        }
    ]
    p = _write_jsonl(tmp_path / "s.jsonl", records)
    md = rt.render_transcript(p, rt.RenderOptions())
    assert "line-A" in md
    assert "[image]" in md


def test_main_writes_out_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """main() writes Markdown to --out and announces the path on stderr."""
    src = _write_jsonl(tmp_path / "s.jsonl", _sample_records())
    out = tmp_path / "nested" / "transcript.md"
    code = rt.main([str(src), "--out", str(out)])
    assert code == 0
    assert out.is_file()
    assert "# Transcript" in out.read_text(encoding="utf-8")
    err = capsys.readouterr().err
    assert "exported ->" in err
    assert str(out.resolve()) in err


def test_main_stdout(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """With no --out, Markdown goes to stdout."""
    src = _write_jsonl(tmp_path / "s.jsonl", _sample_records())
    code = rt.main([str(src)])
    assert code == 0
    captured = capsys.readouterr()
    assert "# Transcript" in captured.out


def test_main_bad_input_returns_2(capsys: pytest.CaptureFixture[str]) -> None:
    """Unresolvable input yields exit code 2 and a stderr message."""
    code = rt.main(["definitely-missing-session"])
    assert code == 2
    assert "error:" in capsys.readouterr().err
