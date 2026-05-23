"""Tests for .claude/hooks/posttooluse_validate_handoff.py (PLAN-0007 AC-3)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / ".claude" / "hooks" / "posttooluse_validate_handoff.py"

Payload = dict[str, Any]
Parsed = dict[str, Any] | None

VALID_FRONTMATTER = """\
---
from: code-session-10
to: cray-session-10
actor: code
session: 10
batch: test-validator-hook
suffix: closeout
phase: closeout
status: DONE
created: 2026-05-23T20:00:00+07:00
title: Test handoff for hook validator
---

# Test handoff for hook validator

Body content.
"""

INVALID_FRONTMATTER_BAD_ENUM = """\
---
from: code-session-10
to: cray-session-10
actor: code
session: 10
batch: test-validator-hook
suffix: closeout
phase: nonsense
status: DONE
created: 2026-05-23T20:00:00+07:00
title: Bad enum
---

Body.
"""

INVALID_FRONTMATTER_MISSING_FIELD = """\
---
from: code-session-10
to: cray-session-10
actor: code
session: 10
batch: test-validator-hook
phase: closeout
status: DONE
created: 2026-05-23T20:00:00+07:00
---

Missing title.
"""


@pytest.fixture
def handoff_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".claude" / "handoffs" / "session-99"
    d.mkdir(parents=True)
    return d


def _run(payload: Payload) -> tuple[int, Parsed, str]:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=os.environ.copy(),
        check=False,
    )
    out = result.stdout.strip()
    parsed = json.loads(out) if out else None
    return result.returncode, parsed, result.stderr


def _write_payload(file_path: Path) -> Payload:
    return {
        "tool_name": "Write",
        "tool_input": {"file_path": str(file_path), "content": "ignored"},
    }


def test_valid_handoff_passes(handoff_dir: Path) -> None:
    f = handoff_dir / "2026-05-23-2000-code-test-valid.md"
    f.write_text(VALID_FRONTMATTER)
    rc, out, err = _run(_write_payload(f))
    assert rc == 0
    assert out is None, f"expected no block decision; got {out} (stderr={err})"


def test_invalid_enum_blocks(handoff_dir: Path) -> None:
    f = handoff_dir / "2026-05-23-2001-code-test-bad-enum.md"
    f.write_text(INVALID_FRONTMATTER_BAD_ENUM)
    rc, out, err = _run(_write_payload(f))
    assert rc == 0
    assert out is not None
    assert out.get("decision") == "block"
    assert "validate_handoff" in out.get("reason", "")


def test_missing_field_blocks(handoff_dir: Path) -> None:
    f = handoff_dir / "2026-05-23-2002-code-test-missing.md"
    f.write_text(INVALID_FRONTMATTER_MISSING_FIELD)
    rc, out, err = _run(_write_payload(f))
    assert rc == 0
    assert out is not None
    assert out.get("decision") == "block"


def test_non_handoff_path_skipped(tmp_path: Path) -> None:
    # Edit on a non-handoff file must not invoke the validator.
    f = tmp_path / "elsewhere.md"
    f.write_text("body")
    payload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(f), "old_string": "a", "new_string": "b"},
    }
    rc, out, _ = _run(payload)
    assert rc == 0
    assert out is None


def test_non_write_edit_tool_skipped(handoff_dir: Path) -> None:
    f = handoff_dir / "2026-05-23-2003-code-test.md"
    f.write_text(INVALID_FRONTMATTER_BAD_ENUM)
    payload = {"tool_name": "Read", "tool_input": {"file_path": str(f)}}
    rc, out, _ = _run(payload)
    assert rc == 0
    assert out is None


def test_malformed_stdin_does_not_block() -> None:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_edit_tool_on_invalid_handoff_blocks(handoff_dir: Path) -> None:
    f = handoff_dir / "2026-05-23-2004-code-test-edit.md"
    f.write_text(INVALID_FRONTMATTER_BAD_ENUM)
    payload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(f), "old_string": "x", "new_string": "y"},
    }
    rc, out, _ = _run(payload)
    assert rc == 0
    assert out is not None
    assert out.get("decision") == "block"
