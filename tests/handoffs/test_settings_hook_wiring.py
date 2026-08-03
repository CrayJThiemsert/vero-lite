"""Pins the hook REGISTRATIONS in ``.claude/settings.json`` (PLAN-0094 AC-1).

This module exists because of a specific failure: the subagent-completion L1
reset shipped 2026-06-08 with a handler, with green tests, and with **no event
registration that could ever invoke it**. ``_handle_agent_completion`` was gated
on ``tool_name in ("Task", "Agent")`` while ``settings.json`` registered
``PostToolUse`` for ``Write|Edit`` and ``Bash`` only. The tests passed because
they fed the handler synthetic payloads directly — nothing asserted that the
harness would ever produce one. Three documents then advertised the reset as
live for seven weeks, and at least one session (s172) followed that advice into
a dead end.

So these tests read `settings.json` **as data** and fail on a registration
removal *alone* — no hook-code mutation required. That is the whole point: a
handler with no route to it must not be able to pass.

**Scope note (PLAN-0094 AC-1 — CLOSED on (i) + (iii)).** AC-1 named three
assertions. Parts (i) and (iii) are pinned here and shipped with Step 1. Part
(ii) — a ``PostToolUseFailure`` entry, matcher ``Write|Edit``, invoking the same
observer — was **WITHDRAWN at s179 on measured evidence**, together with D4(a):
a *failed* ``Edit`` invokes **no hook at all** in this harness build — not
``PostToolUseFailure``, and not ``PostToolUse`` either. Measured twice, one
session apart: s173's live ``PostToolUse`` observer, and an s179 probe
registered on both events at once with a successful ``Write`` as the control
that makes "no dump" readable at all. No such registration is written, so there
is nothing here to pin.

It stays **unasserted rather than asserted-and-skipped**: a check that passes
because it was skipped is exactly the vacuous form this module was written to
kill. Withdrawing the criterion outright — rather than greening it by feeding a
synthetic payload straight into ``main()`` — is that same discipline applied one
level up: a test that passes while the live path stays dead is the defect above,
not a fix for it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SETTINGS = REPO_ROOT / ".claude" / "settings.json"

OBSERVER = "posttooluse_progress_observer.py"


def _load_hooks() -> dict[str, Any]:
    data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    hooks = data.get("hooks")
    assert isinstance(hooks, dict), "settings.json must carry a 'hooks' object"
    return hooks


def _commands(entry: dict[str, Any]) -> list[str]:
    """Every command string registered by one matcher entry."""
    out: list[str] = []
    for hook in entry.get("hooks") or []:
        if isinstance(hook, dict):
            command = hook.get("command")
            if isinstance(command, str):
                out.append(command)
    return out


def _entries_invoking(event: str, script: str) -> list[dict[str, Any]]:
    """Matcher entries under ``event`` whose hooks invoke ``script``."""
    entries = _load_hooks().get(event) or []
    if not isinstance(entries, list):
        return []
    return [
        entry
        for entry in entries
        if isinstance(entry, dict) and any(script in cmd for cmd in _commands(entry))
    ]


def test_settings_json_is_parseable() -> None:
    """Guard the guard: every assertion below is vacuous if this file is not JSON."""
    assert _load_hooks(), "settings.json parsed but declared no hooks"


# --- AC-1 (i): the SubagentStop route that Step 1 restores -------------------


def test_subagentstop_invokes_the_progress_observer() -> None:
    """The L1 subagent reset must have a route from the harness to the handler.

    Without this registration the handler is unreachable code — the exact
    2026-06-08 defect. Asserting the *registration* (not the handler) is what
    makes this test fail on removal alone.
    """
    assert _entries_invoking("SubagentStop", OBSERVER), (
        "no SubagentStop entry invokes the progress observer — the subagent L1 "
        "reset would be dead code again (PLAN-0094 D1)"
    )


def test_subagentstop_observer_entry_matches_every_subagent() -> None:
    """The reset must not be scoped to one agent type.

    The pre-existing SubagentStop entry is matcher ``plan-drafter`` (the Telegram
    notifier). Reusing that matcher would restore the reset for exactly one agent
    type and silently leave every other subagent's edits spending the main
    agent's budget.
    """
    matchers = {entry.get("matcher") for entry in _entries_invoking("SubagentStop", OBSERVER)}
    assert (
        "*" in matchers
    ), f"SubagentStop observer entry must use matcher '*', got {sorted(map(str, matchers))}"


def test_preexisting_subagentstop_notifier_is_retained() -> None:
    """Step 1 adds an entry; it must not displace the shipped notifier."""
    assert _entries_invoking(
        "SubagentStop", "subagentstop_notify.py"
    ), "the plan-drafter SubagentStop notifier was removed"


# --- AC-1 (iii): the registrations that already exist must survive -----------


@pytest.mark.parametrize("matcher", ["Write|Edit", "Bash"])
def test_posttooluse_observer_registrations_are_retained(matcher: str) -> None:
    """The two live PostToolUse routes into the observer are load-bearing.

    ``Write|Edit`` feeds L1; ``Bash`` feeds L2/L3/L4 and the commit reset.
    Losing either silently disables a whole loop class.
    """
    matchers = {entry.get("matcher") for entry in _entries_invoking("PostToolUse", OBSERVER)}
    assert matcher in matchers, (
        f"PostToolUse '{matcher}' no longer routes to the observer; got "
        f"{sorted(map(str, matchers))}"
    )


def test_pretooluse_loop_detect_gate_is_retained() -> None:
    """The deny gate must stay wired for both surfaces it walls."""
    matchers = {
        entry.get("matcher")
        for entry in _entries_invoking("PreToolUse", "pretooluse_loop_detect.py")
    }
    assert {"Bash", "Write|Edit"} <= {str(m) for m in matchers}, (
        f"pretooluse_loop_detect lost a PreToolUse registration; got "
        f"{sorted(map(str, matchers))}"
    )


def test_governance_gate_deny_is_registered_for_write_and_edit() -> None:
    """G1/G2 are enforced by a hook, so the REGISTRATION is the enforcement.

    The module docstring's failure mode applied to a gate rather than a
    handler: a deny hook that is never invoked denies nothing, and every test
    of its ``evaluate()`` would still pass. Pin the route.
    """
    matchers = {
        entry.get("matcher")
        for entry in _entries_invoking("PreToolUse", "pretooluse_governance_gate_deny.py")
    }
    assert "Write|Edit" in {str(m) for m in matchers}, (
        f"the deterministic G1/G2 gate lost its PreToolUse registration — "
        f"Accepted ADRs and fresh ADR/PLAN numbers are now ungated; got "
        f"{sorted(map(str, matchers))}"
    )


def test_classifier_dispatch_is_not_re_registered_on_pretooluse() -> None:
    """The classifier's PreToolUse arm was retired (session 202) — keep it out.

    ``pretooluse_classifier_dispatch.py`` detected exactly one thing: the
    G1/G2 signature. Once ``pretooluse_governance_gate_deny.py`` decided those
    two rows by reading the file, the arm became a redundant model call on
    every governance ``Write``/``Edit`` — and it was decided by
    ``gpt-oss:20b``, measured at self-consistency 0/4 at ``temperature 0`` with
    blank output on 3/12 runs.

    It was also **broader than its own spec**: it paused Accepted PLANs, which
    neither the registry's G1 row nor ``CLAUDE.md`` §6 ever claimed (both say
    ADR). See ``test_g1_does_not_fire_on_an_accepted_plan``.

    The script and its unit tests are deliberately kept on disk — this is an
    unwiring, not a deletion, so it is cheap to reverse. That is exactly why
    the registration needs a test: nothing else would notice it coming back,
    and re-wiring it would silently restore a non-deterministic model call to
    the governance hot path.
    """
    entries = _entries_invoking("PreToolUse", "pretooluse_classifier_dispatch.py")
    assert not entries, (
        "pretooluse_classifier_dispatch.py is registered on PreToolUse again. "
        "It is redundant with the deterministic G1/G2 gate and re-introduces a "
        "non-deterministic model call. If this is intentional, retire this test "
        "with the reasoning, do not just delete the assertion."
    )
