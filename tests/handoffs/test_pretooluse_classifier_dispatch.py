"""Tests for ``.claude/hooks/pretooluse_classifier_dispatch.py``
(PLAN-0009 Step 5c-2 — PreToolUse classifier dispatch for G1/G2).

Two test surfaces:

1. **Pre-filter (deterministic, no classifier needed)** — verifies the
   ``_detect_signature`` cheap-check correctly identifies G1 (Edit on
   existing accepted ADR/PLAN) vs G2 (Write of fresh
   ``docs/(adr|plans)/NNNN-*.md``) vs no-match (allow without classifier
   call). Pure unit tests; no mocking required.

2. **Decision mapping (in-process with mocked classifier)** — verifies
   the hook maps proceed/pause/dispatch to the right
   allow/deny/deny-with-redirect output. Mocks ``_sonnet_classifier.classify``
   directly; pattern matches the Step 5c-1 in-process tests in
   ``test_stop_continuation.py``.

3. **End-to-end (subprocess with defanged classifier)** — invokes the
   real hook as a subprocess with the classifier defanged (no API key
   + missing key file → fail-closed pause). Verifies wire output is
   well-formed JSON deny + that the classifier dispatch only fires on
   pre-filter hits.
"""

from __future__ import annotations

import importlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK = REPO_ROOT / ".claude" / "hooks" / "pretooluse_classifier_dispatch.py"
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

import _sonnet_classifier as _sc  # noqa: E402  — sys.path manipulation above
import pretooluse_classifier_dispatch as _hook  # noqa: E402

# ---------------------------------------------------------------------------
# Pre-filter unit tests (no classifier needed)
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Build a tiny fake repo with docs/{adr,plans}/ and ADR fixtures.

    Patches the hook's REPO_ROOT so disk reads land in tmp_path. Returns
    the repo root so tests can write more fixtures.
    """
    (tmp_path / "docs" / "adr").mkdir(parents=True)
    (tmp_path / "docs" / "plans").mkdir(parents=True)

    # Accepted ADR (G1 fixture)
    (tmp_path / "docs" / "adr" / "0009-accepted.md").write_text(
        "# ADR-0009: Test\n\n**Status:** Accepted\n**Date:** 2026-05-25\n\nBody.\n",
        encoding="utf-8",
    )
    # Proposed ADR (G1 negative fixture)
    (tmp_path / "docs" / "adr" / "0010-proposed.md").write_text(
        "# ADR-0010: Test\n\n**Status:** Proposed\n\nBody.\n",
        encoding="utf-8",
    )
    # Draft PLAN (G1 negative fixture)
    (tmp_path / "docs" / "plans" / "0009-draft.md").write_text(
        "# PLAN-0009\n\n**Status:** Draft\n\nBody.\n",
        encoding="utf-8",
    )
    # Accepted PLAN (G1 fixture)
    (tmp_path / "docs" / "plans" / "0007-accepted.md").write_text(
        "# PLAN-0007\n\nStatus: Accepted\n\nBody.\n",
        encoding="utf-8",
    )

    # Repoint REPO_ROOT and the loop-counter helper's REPO_ROOT inside the
    # hook module. The hook resolves relative paths against REPO_ROOT.
    monkeypatch.setattr(_hook, "REPO_ROOT", tmp_path)
    # Reload so any module-level constants that depend on REPO_ROOT refresh.
    # (Currently none in this hook, but defensive.)
    return tmp_path


# --- G1 detection (Edit on accepted ADR/PLAN) ---


def test_g1_match_edit_accepted_adr(fake_repo: Path) -> None:
    assert _hook._detect_signature("Edit", "docs/adr/0009-accepted.md") == "G1"


def test_g1_match_edit_accepted_plan(fake_repo: Path) -> None:
    assert _hook._detect_signature("Edit", "docs/plans/0007-accepted.md") == "G1"


def test_g1_negative_edit_proposed_adr(fake_repo: Path) -> None:
    """Edit on a Proposed ADR is fine — classifier never invoked."""
    assert _hook._detect_signature("Edit", "docs/adr/0010-proposed.md") is None


def test_g1_negative_edit_draft_plan(fake_repo: Path) -> None:
    assert _hook._detect_signature("Edit", "docs/plans/0009-draft.md") is None


def test_g1_negative_edit_nonexistent_file(fake_repo: Path) -> None:
    """Edit on a file that doesn't exist — the Edit tool itself would fail;
    we just skip the gate (no signature).
    """
    assert _hook._detect_signature("Edit", "docs/adr/9999-ghost.md") is None


def test_g1_status_field_case_insensitive(fake_repo: Path, tmp_path: Path) -> None:
    """Status: Accepted matches regardless of case variations + leading ws."""
    (tmp_path / "docs" / "adr" / "0011-lowercase.md").write_text(
        "# ADR-0011\n\n  status: ACCEPTED  \n\nBody.\n", encoding="utf-8"
    )
    assert _hook._detect_signature("Edit", "docs/adr/0011-lowercase.md") == "G1"


def test_g1_negative_status_within_body(fake_repo: Path, tmp_path: Path) -> None:
    """A reference to 'Status: Accepted' deep in the body (past scan window)
    is not picked up — only the header area defines the ADR's status.
    """
    body = "\n".join(["filler"] * 30) + "\n\nStatus: Accepted\n"
    (tmp_path / "docs" / "adr" / "0012-deep.md").write_text(body, encoding="utf-8")
    assert _hook._detect_signature("Edit", "docs/adr/0012-deep.md") is None


# --- G2 detection (Write of fresh NNNN-*.md) ---


def test_g2_match_write_new_adr(fake_repo: Path) -> None:
    """Write to a not-yet-existing docs/adr/NNNN-*.md → G2 (number consumption)."""
    assert _hook._detect_signature("Write", "docs/adr/0014-new-feature.md") == "G2"


def test_g2_match_write_new_plan(fake_repo: Path) -> None:
    assert _hook._detect_signature("Write", "docs/plans/0011-new-plan.md") == "G2"


def test_g2_negative_write_overwriting_proposed_adr(fake_repo: Path) -> None:
    """Write overwriting an existing non-accepted ADR — not G2 (already
    consumed) and not G1 (not accepted). No signature.
    """
    assert _hook._detect_signature("Write", "docs/adr/0010-proposed.md") is None


def test_g2_negative_write_overwriting_accepted_adr_becomes_g1(
    fake_repo: Path,
) -> None:
    """Edge case: Write overwriting an ACCEPTED ADR. Number is already
    consumed (not G2), but the action is a mutation of an accepted ADR (G1).
    The hook reports G1 — defense-in-depth even though the conventional path
    for editing existing files is Edit, not Write.
    """
    assert _hook._detect_signature("Write", "docs/adr/0009-accepted.md") == "G1"


# --- Path pattern pre-filter ---


def test_skip_non_governance_path(fake_repo: Path) -> None:
    """Files outside docs/{adr,plans}/ → no signature."""
    assert _hook._detect_signature("Edit", "docs/STATUS.md") is None
    assert _hook._detect_signature("Edit", "services/api/main.py") is None
    assert _hook._detect_signature("Edit", "README.md") is None


def test_skip_governance_path_without_nnnn(fake_repo: Path) -> None:
    """docs/adr/template.md, docs/plans/notes.md → no NNNN, no match."""
    assert _hook._detect_signature("Write", "docs/adr/template.md") is None
    assert _hook._detect_signature("Write", "docs/plans/notes.md") is None


def test_skip_governance_path_wrong_extension(fake_repo: Path) -> None:
    """Only .md is gated; .txt / .yaml etc. are skipped."""
    assert _hook._detect_signature("Write", "docs/adr/0011-foo.txt") is None
    assert _hook._detect_signature("Write", "docs/plans/0011-foo.yaml") is None


def test_skip_non_write_edit_tool(fake_repo: Path) -> None:
    """Tools other than Write/Edit → no signature."""
    # _detect_signature only gates Write/Edit; main() also gates by tool_name.
    assert _hook._detect_signature("Read", "docs/adr/0009-accepted.md") is None
    assert _hook._detect_signature("Bash", "docs/adr/0009-accepted.md") is None


# --- Absolute path resolution ---


def test_absolute_path_resolved(fake_repo: Path) -> None:
    """An absolute path to the accepted ADR is detected as G1 too."""
    abs_path = str(fake_repo / "docs" / "adr" / "0009-accepted.md")
    assert _hook._detect_signature("Edit", abs_path) == "G1"


# ---------------------------------------------------------------------------
# Decision mapping (in-process with mocked classifier)
# ---------------------------------------------------------------------------


@pytest.fixture
def inproc(monkeypatch: pytest.MonkeyPatch, fake_repo: Path) -> dict[str, Any]:
    """In-process invocation harness for the hook. Returns helpers."""
    # Reload hook module so any monkey-patched REPO_ROOT sticks
    importlib.reload(_hook)
    monkeypatch.setattr(_hook, "REPO_ROOT", fake_repo)
    return {"repo": fake_repo}


def _patch_classify(monkeypatch: pytest.MonkeyPatch, verdict: dict[str, Any]) -> None:
    monkeypatch.setattr(_sc, "classify", lambda payload: verdict)


def _run_inproc(monkeypatch: pytest.MonkeyPatch, payload: dict[str, Any]) -> tuple[int, str]:
    stdin = io.StringIO(json.dumps(payload))
    stdout = io.StringIO()
    monkeypatch.setattr("sys.stdin", stdin)
    monkeypatch.setattr("sys.stdout", stdout)
    rc = _hook.main()
    return rc, stdout.getvalue().strip()


def _g1_payload(file_path: str = "docs/adr/0009-accepted.md") -> dict[str, Any]:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": file_path, "old_string": "x", "new_string": "y"},
    }


def _g2_payload(file_path: str = "docs/plans/0011-new.md") -> dict[str, Any]:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": "# PLAN-0011\n"},
    }


# --- proceed → allow ---


def test_proceed_allows_g1_edit(monkeypatch: pytest.MonkeyPatch, inproc: dict[str, Any]) -> None:
    """Classifier overruled the pre-filter (legitimate context) → allow."""
    _patch_classify(
        monkeypatch,
        {
            "decision": "proceed",
            "matched_rows": [],
            "reason": "chore typo fix, Cray pre-approved",
        },
    )
    rc, out = _run_inproc(monkeypatch, _g1_payload())
    assert rc == 0
    assert out == ""  # no output = allow


def test_proceed_allows_g2_write(monkeypatch: pytest.MonkeyPatch, inproc: dict[str, Any]) -> None:
    _patch_classify(
        monkeypatch,
        {"decision": "proceed", "matched_rows": [], "reason": "ok"},
    )
    rc, out = _run_inproc(monkeypatch, _g2_payload())
    assert rc == 0
    assert out == ""


# --- pause → deny ---


def test_pause_denies_g1(monkeypatch: pytest.MonkeyPatch, inproc: dict[str, Any]) -> None:
    _patch_classify(
        monkeypatch,
        {
            "decision": "pause",
            "matched_rows": ["G1"],
            "reason": "about to mutate accepted ADR-0009",
        },
    )
    rc, out = _run_inproc(monkeypatch, _g1_payload())
    assert rc == 0
    parsed = json.loads(out)
    assert parsed["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert parsed["hookSpecificOutput"]["permissionDecision"] == "deny"
    reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
    assert "G1" in reason
    assert "accepted ADR" in reason or "mutate" in reason
    assert "autonomy-triggers.md" in reason


def test_pause_denies_g2(monkeypatch: pytest.MonkeyPatch, inproc: dict[str, Any]) -> None:
    _patch_classify(
        monkeypatch,
        {
            "decision": "pause",
            "matched_rows": ["G2"],
            "reason": "consuming fresh PLAN number without ratification",
        },
    )
    rc, out = _run_inproc(monkeypatch, _g2_payload())
    assert rc == 0
    parsed = json.loads(out)
    assert parsed["hookSpecificOutput"]["permissionDecision"] == "deny"
    reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
    assert "G2" in reason


# --- dispatch → deny with spawn-redirect ---


def test_dispatch_denies_with_spawn_redirect(
    monkeypatch: pytest.MonkeyPatch, inproc: dict[str, Any]
) -> None:
    _patch_classify(
        monkeypatch,
        {
            "decision": "dispatch",
            "matched_rows": ["G2", "D2"],
            "reason": "drafting a new PLAN should be subagent task",
            "dispatch": {
                "subagent": "plan-drafter",
                "artifact_kind": "plan",
                "task_summary": "Draft PLAN-0011 for cross-machine coordination",
            },
        },
    )
    rc, out = _run_inproc(monkeypatch, _g2_payload())
    assert rc == 0
    parsed = json.loads(out)
    assert parsed["hookSpecificOutput"]["permissionDecision"] == "deny"
    reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
    assert "AUTO-HANDOFF DISPATCH" in reason
    assert "plan-drafter" in reason
    assert "PLAN-0011" in reason
    assert "docs/plans" in reason
    assert "do NOT proceed" in reason or "do not proceed" in reason.lower()
    assert "Step 4 §1 R4" in reason
    assert "Override" in reason or "override" in reason


def test_dispatch_adr_redirects_to_docs_adr(
    monkeypatch: pytest.MonkeyPatch, inproc: dict[str, Any]
) -> None:
    _patch_classify(
        monkeypatch,
        {
            "decision": "dispatch",
            "matched_rows": ["G2"],
            "reason": "drafting ADR via subagent",
            "dispatch": {
                "subagent": "plan-drafter",
                "artifact_kind": "adr",
                "task_summary": "Draft ADR-0015 for transport bus",
            },
        },
    )
    rc, out = _run_inproc(monkeypatch, _g2_payload(file_path="docs/adr/0015-bus.md"))
    assert rc == 0
    parsed = json.loads(out)
    reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
    assert "docs/adr" in reason
    assert "ADR-0015" in reason
    assert "artifact_kind=adr" in reason


def test_dispatch_malformed_metadata_demotes_to_pause_deny(
    monkeypatch: pytest.MonkeyPatch, inproc: dict[str, Any]
) -> None:
    """Defense in depth: if a dispatch verdict reaches the hook without
    valid metadata (classifier helper regression), demote to a pause-style
    deny so the action still gets blocked.
    """
    _patch_classify(
        monkeypatch,
        {
            "decision": "dispatch",
            "matched_rows": ["G1"],
            "reason": "broken",
            # dispatch field intentionally missing
        },
    )
    rc, out = _run_inproc(monkeypatch, _g1_payload())
    assert rc == 0
    parsed = json.loads(out)
    assert parsed["hookSpecificOutput"]["permissionDecision"] == "deny"
    reason = parsed["hookSpecificOutput"]["permissionDecisionReason"]
    # Pause-style reason cites G1, not the spawn redirect
    assert "G1" in reason
    assert "always-pause" in reason
    assert "AUTO-HANDOFF" not in reason  # not the dispatch-style reason


def test_dispatch_non_dict_metadata_demotes_to_pause_deny(
    monkeypatch: pytest.MonkeyPatch, inproc: dict[str, Any]
) -> None:
    _patch_classify(
        monkeypatch,
        {
            "decision": "dispatch",
            "matched_rows": ["G1"],
            "reason": "broken",
            "dispatch": "not a dict",
        },
    )
    rc, out = _run_inproc(monkeypatch, _g1_payload())
    parsed = json.loads(out)
    assert parsed["hookSpecificOutput"]["permissionDecision"] == "deny"


# --- Unknown verdict → fail-closed deny ---


def test_unknown_verdict_denies(monkeypatch: pytest.MonkeyPatch, inproc: dict[str, Any]) -> None:
    """Defense in depth: a verdict outside proceed/pause/dispatch is treated
    as pause (deny). Should never happen — classifier validates — but the
    fail-closed bias matters.
    """
    _patch_classify(
        monkeypatch,
        {"decision": "maybe-later", "matched_rows": [], "reason": "x"},
    )
    rc, out = _run_inproc(monkeypatch, _g1_payload())
    parsed = json.loads(out)
    assert parsed["hookSpecificOutput"]["permissionDecision"] == "deny"


# --- Pre-filter miss skips classifier entirely ---


def test_pre_filter_miss_skips_classifier(
    monkeypatch: pytest.MonkeyPatch, inproc: dict[str, Any]
) -> None:
    """Edit on a non-governance file → classifier never invoked, allow."""
    classifier_called = {"n": 0}

    def spying_classify(payload: dict[str, Any]) -> dict[str, Any]:
        classifier_called["n"] += 1
        return {"decision": "pause", "matched_rows": [], "reason": "x"}

    monkeypatch.setattr(_sc, "classify", spying_classify)
    rc, out = _run_inproc(
        monkeypatch,
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "services/api/main.py"},
        },
    )
    assert rc == 0
    assert out == ""
    assert classifier_called["n"] == 0


def test_pre_filter_miss_on_proposed_adr_skips_classifier(
    monkeypatch: pytest.MonkeyPatch, inproc: dict[str, Any]
) -> None:
    """Edit on a Proposed ADR is not G1 → no classifier call, allow."""
    classifier_called = {"n": 0}

    def spying_classify(payload: dict[str, Any]) -> dict[str, Any]:
        classifier_called["n"] += 1
        return {"decision": "pause", "matched_rows": [], "reason": "x"}

    monkeypatch.setattr(_sc, "classify", spying_classify)
    rc, out = _run_inproc(monkeypatch, _g1_payload("docs/adr/0010-proposed.md"))
    assert rc == 0
    assert out == ""
    assert classifier_called["n"] == 0


# --- Augmented payload sanity ---


def test_classifier_receives_pretool_signature(
    monkeypatch: pytest.MonkeyPatch, inproc: dict[str, Any]
) -> None:
    """Hook augments the payload with pretool_signature before classify()."""
    captured: dict[str, Any] = {}

    def capturing_classify(payload: dict[str, Any]) -> dict[str, Any]:
        captured.update(payload)
        return {"decision": "pause", "matched_rows": [], "reason": "x"}

    monkeypatch.setattr(_sc, "classify", capturing_classify)
    _run_inproc(monkeypatch, _g1_payload())
    assert "pretool_signature" in captured
    sig = captured["pretool_signature"]
    assert sig["matched_row"] == "G1"
    assert "0009-accepted.md" in sig["file_path"]
    assert sig["hook_source"] == "pretooluse_classifier_dispatch"


# --- Malformed input fail-open (matches Phase 1/2 pattern) ---


def test_malformed_json_fails_open(monkeypatch: pytest.MonkeyPatch, inproc: dict[str, Any]) -> None:
    """Hook should not crash on malformed JSON — exit 0 silently."""
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    monkeypatch.setattr("sys.stdout", io.StringIO())
    rc = _hook.main()
    assert rc == 0


def test_missing_tool_input_fails_open(
    monkeypatch: pytest.MonkeyPatch, inproc: dict[str, Any]
) -> None:
    rc, out = _run_inproc(monkeypatch, {"hook_event_name": "PreToolUse", "tool_name": "Edit"})
    assert rc == 0
    assert out == ""


# ---------------------------------------------------------------------------
# End-to-end subprocess tests (real classifier, defanged via no API key)
# ---------------------------------------------------------------------------


@pytest.fixture
def subprocess_env(tmp_path: Path) -> dict[str, str]:
    """Build a subprocess env that defangs the classifier to fail-closed pause."""
    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)
    env["CLAUDE_ANTHROPIC_KEY_FILE"] = str(tmp_path / "nope.anthropic_api_key")
    # Use the real registry so the classifier helper has SOMETHING to load
    # before it discovers no API key — even though it fails-closed earlier.
    return env


def _run_subprocess(payload: dict[str, Any], env: dict[str, str]) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=15,
    )
    return result.returncode, result.stdout.strip()


def test_subprocess_skip_on_non_governance_path(
    subprocess_env: dict[str, str],
) -> None:
    """Real subprocess; non-governance Edit → allow (no output)."""
    rc, out = _run_subprocess(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "README.md"},
        },
        subprocess_env,
    )
    assert rc == 0
    assert out == ""


def test_subprocess_g1_with_defanged_classifier_denies(
    subprocess_env: dict[str, str],
) -> None:
    """Real subprocess; G1 hit + defanged classifier (fail-closed pause) →
    deny. Uses the live repo's actual accepted ADRs as fixture data.
    """
    # Find a real accepted ADR in the live repo
    accepted_adr: Path | None = None
    for adr in (REPO_ROOT / "docs" / "adr").glob("*.md"):
        content = adr.read_text(encoding="utf-8")
        if "Status: Accepted" in content or "**Status:** Accepted" in content:
            accepted_adr = adr
            break
    if accepted_adr is None:
        pytest.skip("no accepted ADR in repo to use as fixture")

    rel = accepted_adr.relative_to(REPO_ROOT).as_posix()
    rc, out = _run_subprocess(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": rel,
                "old_string": "x",
                "new_string": "y",
            },
        },
        subprocess_env,
    )
    assert rc == 0
    parsed = json.loads(out)
    assert parsed["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "G1" in parsed["hookSpecificOutput"]["permissionDecisionReason"]


def test_subprocess_g2_with_defanged_classifier_denies(
    subprocess_env: dict[str, str],
) -> None:
    """Real subprocess; G2 hit (new PLAN number) + defanged classifier → deny."""
    rc, out = _run_subprocess(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "docs/plans/9999-fresh-number.md",
                "content": "# PLAN-9999\n",
            },
        },
        subprocess_env,
    )
    assert rc == 0
    parsed = json.loads(out)
    assert parsed["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "G2" in parsed["hookSpecificOutput"]["permissionDecisionReason"]


def test_subprocess_bash_tool_not_gated(
    subprocess_env: dict[str, str],
) -> None:
    """Bash tool → hook skips entirely (matcher is Write|Edit upstream too,
    but hook should be defensive)."""
    rc, out = _run_subprocess(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
        },
        subprocess_env,
    )
    assert rc == 0
    assert out == ""
