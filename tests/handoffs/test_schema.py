"""Tests for tools/handoffs/_schema.py.

The schema module lives under ``tools/`` (a non-package scripts
directory), so it is loaded by file path via importlib rather than a
normal import.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime
from pathlib import Path
from types import ModuleType

_TOOLS = Path(__file__).resolve().parents[2] / "tools" / "handoffs"


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, _TOOLS / f"{name}.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sch = _load("_schema")


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
references_commits:
  - b81817b
  - 96bf51b
---

body text
"""


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_parse_happy_path(tmp_path: Path) -> None:
    """A well-formed file parses into a typed Frontmatter."""
    p = _write(tmp_path / "2026-05-19-0200-chat-demo.md", _VALID)
    fm = sch.parse_frontmatter(p)
    assert isinstance(fm, sch.Frontmatter)
    assert fm.actor is sch.Actor.CHAT
    assert fm.phase is sch.Phase.DISPATCH
    assert fm.status is sch.Status.READY
    assert fm.session == 10
    assert fm.from_ == "claude-chat-session-10"
    assert fm.references_commits == ("b81817b", "96bf51b")
    assert fm.suffix is None


def test_parse_missing_required_field(tmp_path: Path) -> None:
    """Dropping a required field yields a ValidationError list."""
    text = _VALID.replace("session: 10\n", "")
    p = _write(tmp_path / "2026-05-19-0200-chat-demo.md", text)
    result = sch.parse_frontmatter(p)
    assert isinstance(result, list)
    assert any(e.field == "session" and e.is_error() for e in result)


def test_parse_invalid_enum_value(tmp_path: Path) -> None:
    """An out-of-enum actor value is reported as an error."""
    text = _VALID.replace("actor: chat", "actor: robot")
    p = _write(tmp_path / "2026-05-19-0200-chat-demo.md", text)
    result = sch.parse_frontmatter(p)
    assert isinstance(result, list)
    assert any(e.field == "actor" and "invalid actor" in e.message for e in result)


def test_missing_frontmatter_block(tmp_path: Path) -> None:
    """A file with no '---' fence reports a single structural error."""
    p = _write(tmp_path / "2026-05-19-0200-chat-demo.md", "no frontmatter here\n")
    result = sch.parse_frontmatter(p)
    assert isinstance(result, list)
    assert result[0].field == "<frontmatter>"


def test_validate_filename_prefix_match(tmp_path: Path) -> None:
    """A filename whose actor token matches the actor passes."""
    p = tmp_path / "2026-05-19-0200-chat-demo.md"
    assert sch.validate_filename_prefix(p, sch.Actor.CHAT) is None


def test_validate_filename_prefix_mismatch(tmp_path: Path) -> None:
    """A chat- filename with actor: code is flagged."""
    p = tmp_path / "2026-05-19-0200-chat-demo.md"
    err = sch.validate_filename_prefix(p, sch.Actor.CODE)
    assert err is not None
    assert err.field == "filename"
    assert err.is_error()


def test_iso8601_requires_timezone(tmp_path: Path) -> None:
    """created without a timezone offset is rejected; with one it
    parses to a tz-aware datetime."""
    naive = _VALID.replace("2026-05-19T02:00:00+07:00", "2026-05-19T02:00:00")
    p = _write(tmp_path / "2026-05-19-0200-chat-demo.md", naive)
    result = sch.parse_frontmatter(p)
    assert isinstance(result, list)
    assert any(e.field == "created" for e in result)

    ok = sch.parse_frontmatter(_write(tmp_path / "2026-05-19-0200-chat-ok.md", _VALID))
    assert isinstance(ok, sch.Frontmatter)
    assert isinstance(ok.created, datetime)
    assert ok.created.tzinfo is not None


def test_unknown_field_is_warning(tmp_path: Path) -> None:
    """An unrecognized field is a warning, not an error (forward-compat)."""
    text = _VALID.replace("title: demo handoff\n", "title: demo handoff\nmystery: 1\n")
    p = _write(tmp_path / "2026-05-19-0200-chat-demo.md", text)
    fm = sch.parse_frontmatter(p)
    assert isinstance(fm, sch.Frontmatter)  # warning does not block parsing
    findings = sch.validate_file(p)
    # validate_file re-parses cleanly; the warning surfaces via parse only
    assert findings == [] or all(not f.is_error() for f in findings)


def test_detect_chain_via_summary(tmp_path: Path) -> None:
    """A batch with PAUSED→PAUSED→DONE is reported as a chain."""
    base = _VALID
    f1 = _write(
        tmp_path / "2026-05-19-0100-chat-x.md",
        base.replace("status: READY", "status: PAUSED").replace(
            "created: 2026-05-19T02:00:00+07:00", "created: 2026-05-19T01:00:00+07:00"
        ),
    )
    f2 = _write(
        tmp_path / "2026-05-19-0200-chat-x.md",
        base.replace("status: READY", "status: PAUSED"),
    )
    f3 = _write(
        tmp_path / "2026-05-19-0300-chat-x.md",
        base.replace("status: READY", "status: DONE").replace(
            "created: 2026-05-19T02:00:00+07:00", "created: 2026-05-19T03:00:00+07:00"
        ),
    )
    summary = sch.summarize_paths([f3, f1, f2], "session-10")
    assert summary.total == 3
    assert summary.chains
    assert "PAUSED → PAUSED → DONE" in summary.chains[0]
