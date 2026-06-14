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


def test_parse_text_happy_path() -> None:
    """parse_frontmatter_text parses raw content (no file) into a typed
    Frontmatter — the in-process entry point used by the vero-bridge tool."""
    fm = sch.parse_frontmatter_text(_VALID)
    assert isinstance(fm, sch.Frontmatter)
    assert fm.actor is sch.Actor.CHAT
    assert fm.session == 10


def test_parse_text_missing_block() -> None:
    """No '---' fence → a single structural finding, same as the path API."""
    result = sch.parse_frontmatter_text("no frontmatter here\n")
    assert isinstance(result, list)
    assert result[0].field == "<frontmatter>"


def test_parse_text_matches_path_based(tmp_path: Path) -> None:
    """The content-based and path-based entry points agree on the typed
    result for identical content (parse_frontmatter delegates to the text
    form) — differing only in the recorded ``source``."""
    p = _write(tmp_path / "2026-05-19-0200-chat-demo.md", _VALID)
    from_path = sch.parse_frontmatter(p)
    from_text = sch.parse_frontmatter_text(_VALID)
    assert isinstance(from_path, sch.Frontmatter)
    assert isinstance(from_text, sch.Frontmatter)
    assert from_text.actor == from_path.actor
    assert from_text.session == from_path.session
    assert from_text.status == from_path.status
    assert from_text.created == from_path.created


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
    """An unrecognized field is a warning, not an error (forward-compat),
    and the warning is SURFACED — on the parsed Frontmatter and through
    validate_file — rather than silently swallowed on the otherwise-valid
    path (PLAN-004 Phase B warning-swallow bug)."""
    text = _VALID.replace("title: demo handoff\n", "title: demo handoff\nmystery: 1\n")
    p = _write(tmp_path / "2026-05-19-0200-chat-demo.md", text)
    fm = sch.parse_frontmatter(p)
    assert isinstance(fm, sch.Frontmatter)  # warning does not block parsing
    # the warning rides on the typed result instead of being discarded
    assert any(w.field == "mystery" and not w.is_error() for w in fm.warnings)
    findings = sch.validate_file(p)
    # ... and is reachable through validate_file (so the CLI can print it)
    assert any(f.field == "mystery" and not f.is_error() for f in findings)
    # but it stays advisory: the file is still valid (no error-severity finding)
    assert all(not f.is_error() for f in findings)


def test_unknown_field_warning_surfaces_via_text_api() -> None:
    """The content-based entry point (the vero-bridge
    validate_handoff_frontmatter tool) also carries the unknown-field warning
    on the Frontmatter — not just the path API."""
    text = _VALID.replace("title: demo handoff\n", "title: demo handoff\nmystery: 1\n")
    fm = sch.parse_frontmatter_text(text)
    assert isinstance(fm, sch.Frontmatter)
    assert any(w.field == "mystery" and not w.is_error() for w in fm.warnings)


def test_valid_file_has_no_spurious_warnings(tmp_path: Path) -> None:
    """A clean file carries an empty warnings tuple — the new field does not
    invent findings, so validate_file stays empty on a valid handoff."""
    p = _write(tmp_path / "2026-05-19-0200-chat-demo.md", _VALID)
    fm = sch.parse_frontmatter(p)
    assert isinstance(fm, sch.Frontmatter)
    assert fm.warnings == ()
    assert sch.validate_file(p) == []


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


def test_extensible_suffixes_registered() -> None:
    """C-2 resolution, option alpha (PLAN-004 D4 amendment, 2026-05-22):
    the dispatch / completion / consultation tokens resolve to Suffix
    enum members, closing the schema-vs-cowork-instruction divergence."""
    for token in ("dispatch", "completion", "consultation"):
        assert sch.Suffix(token).value == token


def test_completion_suffix_validates_clean(tmp_path: Path) -> None:
    """A handoff declaring `suffix: completion` with a matching filename
    token validates with zero findings: the case that surfaced C-2."""
    text = _VALID.replace(
        "title: demo handoff\n",
        "title: demo handoff\nsuffix: completion\n",
    )
    p = _write(tmp_path / "2026-05-22-1130-chat-demo-completion.md", text)
    fm = sch.parse_frontmatter(p)
    assert isinstance(fm, sch.Frontmatter)
    assert fm.suffix is sch.Suffix.COMPLETION
    assert sch.validate_file(p) == []


# --- PLAN-004 Phase B: session discovery + INDEX.md generation ---


def _session(tmp_path: Path, name: str) -> Path:
    d = tmp_path / name
    d.mkdir()
    return d


def test_latest_session_dir_numeric_not_lexicographic(tmp_path: Path) -> None:
    """session-10 beats session-9 (numeric sort, not string sort)."""
    _session(tmp_path, "session-9")
    _session(tmp_path, "session-10")
    _session(tmp_path, "session-2")
    latest = sch.latest_session_dir(tmp_path)
    assert latest is not None
    assert latest.name == "session-10"


def test_latest_session_dir_none_when_absent(tmp_path: Path) -> None:
    """No session-* dir (or a missing root) → None; non-session dirs ignored."""
    assert sch.latest_session_dir(tmp_path / "nope") is None
    (tmp_path / "archive").mkdir()
    assert sch.latest_session_dir(tmp_path) is None


def test_render_index_is_idempotent(tmp_path: Path) -> None:
    """Two renders over an unchanged dir are byte-identical (no timestamp)."""
    d = _session(tmp_path, "session-10")
    _write(d / "2026-05-19-0200-chat-demo.md", _VALID)
    assert sch.render_index(d) == sch.render_index(d)


def test_render_index_contains_row_and_header(tmp_path: Path) -> None:
    """The index has the session header, the count line, and a table row."""
    d = _session(tmp_path, "session-10")
    _write(d / "2026-05-19-0200-chat-demo.md", _VALID)
    text = sch.render_index(d)
    assert "# session-10 — handoff index" in text
    assert "Total:** 1" in text
    assert "2026-05-19-0200-chat-demo.md" in text
    assert "| chat | dispatch | READY |" in text


def test_write_index_excluded_from_subsequent_walks(tmp_path: Path) -> None:
    """A generated INDEX.md is not counted/parsed as a handoff afterwards."""
    d = _session(tmp_path, "session-10")
    _write(d / "2026-05-19-0200-chat-demo.md", _VALID)
    target = sch.write_index(d)
    assert target.name == sch.INDEX_FILENAME
    # session_md_files excludes it; the re-render still sees exactly 1 handoff
    assert [p.name for p in sch.session_md_files(d)] == ["2026-05-19-0200-chat-demo.md"]
    assert "Total:** 1" in sch.render_index(d)


def test_validate_directory_skips_index(tmp_path: Path) -> None:
    """validate_directory ignores INDEX.md (which has no frontmatter)."""
    d = _session(tmp_path, "session-10")
    _write(d / "2026-05-19-0200-chat-demo.md", _VALID)
    sch.write_index(d)
    names = {p.name for p in sch.validate_directory(tmp_path)}
    assert sch.INDEX_FILENAME not in names
    assert "2026-05-19-0200-chat-demo.md" in names
