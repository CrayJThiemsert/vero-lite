"""Tests for ``validate_handoff_frontmatter`` — PLAN-0012 Step 2b (tool 2/4).

This tool runs the committed handoff-frontmatter schema
(``tools/handoffs/_schema.py``) in-process so Cowork can validate handoffs it
authors without Code brokering the run (Lesson #8 K-1). It introduces no new
``ErrorCode`` — validation findings are a *successful* result
(``ok=True, valid=<bool>, errors=[...]``); only a non-str ``content`` is a
transport-level ``MALFORMED_FRAME``.

Coverage:

- **Adapter** (``tools.vero_bridge._handoff_validate``): valid body →
  ``(True, [])``; missing-required / invalid-enum / missing-fence / empty →
  ``valid=False`` with findings; the wire shape of each finding; the
  warning-surfacing nuance (a warning appears only alongside an error,
  mirroring ``parse_frontmatter``).
- **Server handler** (``_handle_validate_handoff_frontmatter``): the
  transport-success-vs-content-validity distinction (invalid handoff is
  ``ok=True, valid=False`` and is audited ``outcome="ok"``), envelope
  fail-closed, non-str payload rejection, and audit side-effects.
- **AC-7 parity**: Chat vs Cowork yield an identical response.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.vero_bridge import _audit_log
from tools.vero_bridge._audit_log import reset_counter_for_test
from tools.vero_bridge._handoff_validate import validate_frontmatter_content
from tools.vero_bridge.server import _handle_validate_handoff_frontmatter

_VALID_HANDOFF = """---
from: code-session-25
to: cowork-session-25
actor: code
session: 25
batch: step2b-validate
phase: handoff
status: READY
created: 2026-05-29T16:00:00+07:00
title: validate handoff frontmatter sample
---

body text
"""


@pytest.fixture(autouse=True)
def _reset_counter() -> None:
    reset_counter_for_test()


@pytest.fixture
def audit_log_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the audit log writer to a per-test temp path."""
    path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(_audit_log, "DEFAULT_LOG_PATH", path)
    return path


def _read_audit_lines(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


# ---------------------------------------------------------------------------
# Adapter — validate_frontmatter_content
# ---------------------------------------------------------------------------


def test_valid_frontmatter_is_valid_with_no_findings() -> None:
    valid, errors = validate_frontmatter_content(_VALID_HANDOFF)
    assert valid is True
    assert errors == []


def test_missing_required_field_is_invalid() -> None:
    text = _VALID_HANDOFF.replace("session: 25\n", "")
    valid, errors = validate_frontmatter_content(text)
    assert valid is False
    assert any(e["field"] == "session" for e in errors)


def test_invalid_enum_value_is_invalid() -> None:
    text = _VALID_HANDOFF.replace("actor: code", "actor: robot")
    valid, errors = validate_frontmatter_content(text)
    assert valid is False
    assert any(e["field"] == "actor" and "invalid actor" in e["message"] for e in errors)


def test_missing_frontmatter_block_is_invalid() -> None:
    valid, errors = validate_frontmatter_content("no frontmatter fence here\n")
    assert valid is False
    assert errors[0]["field"] == "<frontmatter>"


def test_empty_content_is_invalid_not_malformed() -> None:
    """Empty content is a valid *input* — it simply has no frontmatter, so
    the validator reports valid=False (not a transport malformation)."""
    valid, errors = validate_frontmatter_content("")
    assert valid is False
    assert errors[0]["field"] == "<frontmatter>"


def test_findings_have_exact_wire_shape() -> None:
    _valid, errors = validate_frontmatter_content("no fence\n")
    assert errors
    for finding in errors:
        assert set(finding) == {"field", "value", "message", "severity"}
        assert finding["severity"] in {"error", "warning"}


def test_mixed_error_and_warning_surfaces_warning_severity() -> None:
    """When a block has a blocking error, advisory findings (e.g. an unknown
    field) are surfaced alongside it — so the ``warning`` severity appears."""
    text = _VALID_HANDOFF.replace("session: 25\n", "mystery_field: 1\n")
    valid, errors = validate_frontmatter_content(text)
    assert valid is False  # session now missing → error
    severities = {e["severity"] for e in errors}
    assert "error" in severities
    assert "warning" in severities  # unknown 'mystery_field' is advisory
    assert any(e["field"] == "mystery_field" and e["severity"] == "warning" for e in errors)


def test_warning_only_block_is_valid_with_no_findings() -> None:
    """Nuance mirroring parse_frontmatter: a block whose only issue is a
    warning parses cleanly → valid=True, no findings (the warning is hidden
    unless an error is also present)."""
    text = _VALID_HANDOFF.replace(
        "title: validate handoff frontmatter sample\n",
        "title: validate handoff frontmatter sample\nmystery_field: 1\n",
    )
    valid, errors = validate_frontmatter_content(text)
    assert valid is True
    assert errors == []


# ---------------------------------------------------------------------------
# Server handler — happy + content-validity distinction
# ---------------------------------------------------------------------------


def test_handler_valid_returns_ok_true_valid_true(audit_log_path: Path) -> None:
    response = _handle_validate_handoff_frontmatter(
        version=1, claimed_tag="cowork", content=_VALID_HANDOFF
    )
    assert response == {"ok": True, "valid": True, "errors": []}


def test_handler_response_shape(audit_log_path: Path) -> None:
    response = _handle_validate_handoff_frontmatter(
        version=1, claimed_tag="cowork", content=_VALID_HANDOFF
    )
    assert set(response) == {"ok", "valid", "errors"}


def test_handler_invalid_content_is_ok_true_valid_false(audit_log_path: Path) -> None:
    """The key distinction: an invalid handoff is a *successful* call
    (ok=True) that reports valid=False — not a transport error."""
    text = _VALID_HANDOFF.replace("status: READY", "status: BOGUS")
    response = _handle_validate_handoff_frontmatter(version=1, claimed_tag="cowork", content=text)
    assert response["ok"] is True
    assert response["valid"] is False
    assert any(e["field"] == "status" for e in response["errors"])


def test_handler_invalid_content_audits_outcome_ok(audit_log_path: Path) -> None:
    """An invalid *handoff* is still a transport success — the audit outcome
    is "ok" (the tool ran), not "error"."""
    _handle_validate_handoff_frontmatter(version=1, claimed_tag="cowork", content="no fence\n")
    records = _read_audit_lines(audit_log_path)
    assert len(records) == 1
    assert records[0]["tool_name"] == "validate_handoff_frontmatter"
    assert records[0]["outcome"] == "ok"
    assert records[0]["error_code"] is None


def test_handler_happy_logs_claimed_tag_verbatim(audit_log_path: Path) -> None:
    _handle_validate_handoff_frontmatter(version=1, claimed_tag="cowork", content=_VALID_HANDOFF)
    records = _read_audit_lines(audit_log_path)
    assert records[0]["claimed_tag"] == "cowork"
    assert records[0]["outcome"] == "ok"


# ---------------------------------------------------------------------------
# Server handler — fail-closed (envelope + payload)
# ---------------------------------------------------------------------------


def test_handler_version_mismatch_returns_error(audit_log_path: Path) -> None:
    response = _handle_validate_handoff_frontmatter(
        version=99, claimed_tag="cowork", content=_VALID_HANDOFF
    )
    assert response["ok"] is False
    assert response["error_code"] == "version-mismatch"
    records = _read_audit_lines(audit_log_path)
    assert records[0]["outcome"] == "error"
    assert records[0]["error_code"] == "version-mismatch"


def test_handler_empty_claimed_tag_returns_malformed_frame(audit_log_path: Path) -> None:
    response = _handle_validate_handoff_frontmatter(
        version=1, claimed_tag="", content=_VALID_HANDOFF
    )
    assert response["ok"] is False
    assert response["error_code"] == "malformed-frame"


def test_handler_non_str_content_returns_malformed_frame(audit_log_path: Path) -> None:
    """A non-str ``content`` is the only payload-level malformation."""
    response = _handle_validate_handoff_frontmatter(
        version=1,
        claimed_tag="cowork",
        content=123,  # type: ignore[arg-type]
    )
    assert response["ok"] is False
    assert response["error_code"] == "malformed-frame"
    records = _read_audit_lines(audit_log_path)
    assert records[0]["outcome"] == "error"
    assert records[0]["error_code"] == "malformed-frame"


# ---------------------------------------------------------------------------
# AC-7 cross-client parity
# ---------------------------------------------------------------------------


def test_ac7_parity_across_clients(audit_log_path: Path) -> None:
    """Same content from the Chat path vs the Cowork path → identical
    response (no per-tab branch). Only the audit-only claimed_tag differs."""
    chat = _handle_validate_handoff_frontmatter(
        version=1, claimed_tag="chat", content=_VALID_HANDOFF
    )
    cowork = _handle_validate_handoff_frontmatter(
        version=1, claimed_tag="cowork", content=_VALID_HANDOFF
    )
    assert chat == cowork
    records = _read_audit_lines(audit_log_path)
    assert [r["claimed_tag"] for r in records] == ["chat", "cowork"]
