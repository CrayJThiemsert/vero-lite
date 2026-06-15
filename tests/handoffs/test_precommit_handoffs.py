"""Tests for tools/handoffs/precommit_handoffs.py (PLAN-004 Phase B hook).

The hook validates only the latest ``session-NN`` directory (no legacy
drag) and regenerates that session's ``INDEX.md``. Loaded by file path via
importlib, mirroring the other ``tools/handoffs`` test modules.
"""

from __future__ import annotations

import importlib.util
import sys
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


_load("_schema")
pc = _load("precommit_handoffs")


_VALID = """---
from: code-session-35
to: code-session-36
actor: code
session: 35
batch: demo
phase: kickoff
status: READY
created: 2026-06-04T01:00:00+07:00
title: demo handoff
---

body
"""

_MALFORMED = """---
from: code-session-35
actor: code
title: missing required fields (to/session/batch/phase/status/created)
---

body
"""


def _session(root: Path, name: str) -> Path:
    d = root / name
    d.mkdir(parents=True)
    return d


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def test_no_session_dir_is_noop(tmp_path: Path) -> None:
    """Missing root or no session-NN dir → exit 0 (nothing to check)."""
    assert pc.main([str(tmp_path / "missing")]) == 0
    assert pc.main([str(tmp_path)]) == 0  # empty root, no session dirs


def test_valid_latest_session_exit_0_and_writes_index(tmp_path: Path) -> None:
    """A clean latest session passes and gets its INDEX.md regenerated."""
    d = _session(tmp_path, "session-35")
    _write(d / "2026-06-04-0100-code-a.md", _VALID)
    assert pc.main([str(tmp_path)]) == 0
    assert (d / "INDEX.md").exists()


def test_malformed_latest_session_exit_1(tmp_path: Path) -> None:
    """An error-severity finding in the latest session fails the commit."""
    d = _session(tmp_path, "session-35")
    _write(d / "2026-06-04-0100-code-bad.md", _MALFORMED)
    assert pc.main([str(tmp_path)]) == 1


def test_only_latest_session_validated_no_legacy_drag(tmp_path: Path) -> None:
    """A malformed handoff in an OLDER session does not block (latest only)."""
    old = _session(tmp_path, "session-9")
    _write(old / "2026-05-01-0100-code-bad.md", _MALFORMED)
    new = _session(tmp_path, "session-10")  # numerically newer than session-9
    _write(new / "2026-06-04-0100-code-ok.md", _VALID)
    assert pc.main([str(tmp_path)]) == 0


def test_generated_index_not_itself_flagged(tmp_path: Path) -> None:
    """A pre-existing INDEX.md (no frontmatter) is not a violation."""
    d = _session(tmp_path, "session-35")
    _write(d / "2026-06-04-0100-code-a.md", _VALID)
    assert pc.main([str(tmp_path)]) == 0  # creates INDEX.md
    assert (d / "INDEX.md").exists()
    assert pc.main([str(tmp_path)]) == 0  # second run still clean (INDEX skipped)


def test_raw_transcript_does_not_block(tmp_path: Path) -> None:
    """A raw ``*-transcript.md`` render (no frontmatter) in the latest session
    does not fail the commit — it is not a frontmatter-bearing handoff. Without
    the session_md_files exemption this would be a missing-frontmatter error."""
    d = _session(tmp_path, "session-60")
    _write(d / "2026-06-15-1353-code-a-handoff.md", _VALID)
    _write(
        d / "2026-06-15-1353-code-a-transcript.md",
        "# Transcript — session `abc`\n\n- Source: x\n\n---\n\nbody\n",
    )
    assert pc.main([str(tmp_path)]) == 0
    assert (d / "INDEX.md").exists()
