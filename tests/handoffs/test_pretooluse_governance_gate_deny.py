"""Tests for ``.claude/hooks/pretooluse_governance_gate_deny.py``.

The deterministic G1 + G2 gate. Every status shape asserted here was measured
against the 35 committed ADRs on 2026-08-02 (session 201) — the emphasis
variant and the template's option-menu are real files, not imagined edge cases.

Two kinds of test live here on purpose:

* **Synthetic** (``tmp_path``) — pin the decision logic without depending on
  today's repo contents.
* **Currency tripwire** (real ``docs/adr/``) — pin that the parser still
  understands the files it actually guards. A synthetic-only suite would stay
  green while a new ADR shape silently slipped past the gate.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

import pretooluse_governance_gate_deny as gate  # noqa: E402


def _payload(path: str, *, tool: str = "Edit", **extra: object) -> dict[str, object]:
    return {"tool_name": tool, "tool_input": {"file_path": path}, **extra}


def _write(root: Path, rel: str, body: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


# --- status parsing: every shape measured across the committed ADRs ---------


@pytest.mark.parametrize(
    "line",
    [
        "**Status:** Accepted",
        "**Status:** **Accepted**",  # ADR-0035
        "**Status:** Accepted — ratified by Cray 2026-07-28 (session 185)",
        "**Status:** Accepted *(Cray-ratified 2026-06-11)*",
        "**Status:** Accepted (ratified 2026-06-09 via PR #236)",
        "**Status:**   Accepted  ",
    ],
)
def test_status_is_accepted_true_for_every_measured_shape(line: str) -> None:
    assert gate.status_is_accepted(f"# ADR\n\n{line}\n\n## Context\n")


@pytest.mark.parametrize(
    "line",
    [
        "**Status:** Withdrawn",  # ADR-0014
        "**Status:** Proposed",
        "**Status:** Superseded by ADR-0035",
        # 0000-template.md lists the options. A substring test says "Accepted"
        # here — the pipe is what distinguishes a menu from a decision.
        "**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-XXXX",
    ],
)
def test_status_is_accepted_false(line: str) -> None:
    assert not gate.status_is_accepted(f"# ADR\n\n{line}\n\n## Context\n")


def test_status_missing_is_not_accepted() -> None:
    assert not gate.status_is_accepted("# ADR\n\nNo status line at all.\n")


# --- G1 ---------------------------------------------------------------------


def test_g1_denies_edit_of_accepted_adr(tmp_path: Path) -> None:
    _write(tmp_path, "docs/adr/0002-network-topology.md", "# ADR\n\n**Status:** Accepted\n")
    reason = gate.evaluate(_payload("docs/adr/0002-network-topology.md"), repo_root=tmp_path)
    assert reason is not None
    assert "G1" in reason
    assert "retrying will not change this answer" in reason


def test_g1_silent_on_withdrawn_adr(tmp_path: Path) -> None:
    """ADR-0014 is real. The classifier cited G1 against it on 1/3 runs; the
    gate must not, because the file plainly says Withdrawn."""
    _write(tmp_path, "docs/adr/0014-WITHDRAWN.md", "# ADR\n\n**Status:** Withdrawn\n")
    assert gate.evaluate(_payload("docs/adr/0014-WITHDRAWN.md"), repo_root=tmp_path) is None


def test_g1_silent_on_template_menu(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "docs/adr/0000-template.md",
        "# ADR\n\n**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-XXXX\n",
    )
    assert gate.evaluate(_payload("docs/adr/0000-template.md"), repo_root=tmp_path) is None


def test_g1_silent_on_ordinary_source_file(tmp_path: Path) -> None:
    """The measured baseline false positive: the classifier cited G1 against
    ``services/api/routers/insights.py`` while returning proceed."""
    _write(tmp_path, "services/api/routers/insights.py", "x = 1\n")
    assert gate.evaluate(_payload("services/api/routers/insights.py"), repo_root=tmp_path) is None


def test_g1_fires_through_a_windows_path(tmp_path: Path) -> None:
    _write(tmp_path, "docs/adr/0002-network-topology.md", "# ADR\n\n**Status:** Accepted\n")
    win = (
        r"\\wsl.localhost\ubuntu-24.04\home\crayj\work"
        r"\vero-lite\docs\adr\0002-network-topology.md"
    )
    reason = gate.evaluate(_payload(win), repo_root=tmp_path)
    assert reason is not None and "G1" in reason


def test_g1_silent_when_file_unreadable(tmp_path: Path) -> None:
    """A path that looks like an ADR but is a directory: the gate has nothing
    to say rather than guessing."""
    (tmp_path / "docs/adr/0099-weird.md").mkdir(parents=True)
    assert gate.evaluate(_payload("docs/adr/0099-weird.md"), repo_root=tmp_path) is None


# --- G2 ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "rel", ["docs/plans/0100-portal-exposure.md", "docs/adr/0036-something-new.md"]
)
def test_g2_denies_new_numbered_artifact(tmp_path: Path, rel: str) -> None:
    reason = gate.evaluate(_payload(rel, tool="Write"), repo_root=tmp_path)
    assert reason is not None
    assert "G2" in reason
    assert "plan-drafter" in reason


def test_g2_silent_for_existing_plan(tmp_path: Path) -> None:
    """Editing an existing PLAN does not consume a number. (Whether it should
    pause for other reasons is a different row's business.)"""
    _write(tmp_path, "docs/plans/0099-live.md", "# PLAN\n\n**Status:** Draft\n")
    assert gate.evaluate(_payload("docs/plans/0099-live.md"), repo_root=tmp_path) is None


def test_g2_silent_for_done_archive_path(tmp_path: Path) -> None:
    """``docs/plans/done/NNNN-*.md`` is an archive location, not a fresh
    number — the regex forbids a nested directory for exactly this reason."""
    assert (
        gate.evaluate(_payload("docs/plans/done/0042-old.md", tool="Write"), repo_root=tmp_path)
        is None
    )


def test_g2_silent_for_unnumbered_doc(tmp_path: Path) -> None:
    assert gate.evaluate(_payload("docs/plans/README.md", tool="Write"), repo_root=tmp_path) is None


# --- exemption + protocol ---------------------------------------------------


def test_plan_drafter_subagent_is_exempt(tmp_path: Path) -> None:
    _write(tmp_path, "docs/adr/0002-network-topology.md", "# ADR\n\n**Status:** Accepted\n")
    payload = _payload(
        "docs/adr/0002-network-topology.md", agent_id="sub-1", agent_type="plan-drafter"
    )
    assert gate.evaluate(payload, repo_root=tmp_path) is None


def test_other_subagent_does_not_inherit_the_exemption(tmp_path: Path) -> None:
    _write(tmp_path, "docs/adr/0002-network-topology.md", "# ADR\n\n**Status:** Accepted\n")
    payload = _payload(
        "docs/adr/0002-network-topology.md", agent_id="sub-2", agent_type="general-purpose"
    )
    reason = gate.evaluate(payload, repo_root=tmp_path)
    assert reason is not None and "G1" in reason


def test_main_agent_without_agent_id_is_not_exempt(tmp_path: Path) -> None:
    """``agent_type`` alone must not grant the exemption — a main-agent payload
    that happened to carry the string would otherwise walk through."""
    _write(tmp_path, "docs/adr/0002-network-topology.md", "# ADR\n\n**Status:** Accepted\n")
    payload = _payload("docs/adr/0002-network-topology.md", agent_type="plan-drafter")
    reason = gate.evaluate(payload, repo_root=tmp_path)
    assert reason is not None and "G1" in reason


@pytest.mark.parametrize("tool", ["Read", "Bash", "Grep", "NotebookEdit"])
def test_silent_for_non_write_tools(tmp_path: Path, tool: str) -> None:
    _write(tmp_path, "docs/adr/0002-network-topology.md", "# ADR\n\n**Status:** Accepted\n")
    assert (
        gate.evaluate(_payload("docs/adr/0002-network-topology.md", tool=tool), repo_root=tmp_path)
        is None
    )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"tool_name": "Edit"},
        {"tool_name": "Edit", "tool_input": None},
        {"tool_name": "Edit", "tool_input": {}},
        {"tool_name": "Edit", "tool_input": {"file_path": 42}},
        {"tool_name": "Edit", "tool_input": {"file_path": ""}},
    ],
)
def test_malformed_payloads_fail_open(payload: dict[str, object], tmp_path: Path) -> None:
    assert gate.evaluate(payload, repo_root=tmp_path) is None


# --- currency tripwire against the real repo --------------------------------


def _committed_adrs() -> list[Path]:
    return sorted((REPO_ROOT / "docs" / "adr").glob("*.md"))


def test_every_committed_adr_exposes_a_parseable_status_line() -> None:
    """The gate's precondition. If a new ADR lands without a ``**Status:**``
    line — or with a shape this parser cannot see — G1 silently stops guarding
    that file. Fail here rather than in production."""
    missing = [
        p.name
        for p in _committed_adrs()
        if gate.STATUS_LINE.search(p.read_text(encoding="utf-8")) is None
    ]
    assert not missing, f"ADRs with no parseable **Status:** line: {missing}"


def test_the_known_non_accepted_adrs_are_exactly_the_template_and_the_withdrawn_one() -> None:
    """Pins the discrimination that no prompt size could buy. If a genuinely
    Proposed ADR lands this reddens — update the expectation deliberately; that
    is the point, not an inconvenience."""
    not_accepted = {
        p.name
        for p in _committed_adrs()
        if not gate.status_is_accepted(p.read_text(encoding="utf-8"))
    }
    assert not_accepted == {"0000-template.md", "0014-WITHDRAWN.md"}


def test_the_real_accepted_adrs_are_actually_gated() -> None:
    """End-to-end against real files: an Accepted ADR in the live tree denies,
    the withdrawn one does not."""
    assert gate.evaluate(_payload("docs/adr/0035-hosting-and-exposure-model.md")) is not None
    assert gate.evaluate(_payload("docs/adr/0014-WITHDRAWN.md")) is None
