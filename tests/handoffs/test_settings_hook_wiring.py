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

**PLAN-0102 AC-4 inverted part of this module, and pinned BOTH directions.**
Retiring L1 eliminated three registrations that existed only to serve it: the
PreToolUse ``Write|Edit`` loop-detect gate, the PostToolUse ``Write|Edit``
observer, and the SubagentStop ``*`` observer. The assertions that used to
require them are now assertions that they stay gone — but each is paired with a
RETENTION assertion for the surface that survives on the same event. That
pairing is load-bearing: an absence-only test suite passes just as happily over
an emptied ``hooks`` block, which would silently disarm the L4 gate, the
L2/L3/L4 observer, the handoff validator and the plan-drafter notifier all at
once. Absence alone is not evidence; absence beside a live retention is.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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


# --- PLAN-0102 AC-4 (a): the three L1-only surfaces stay ELIMINATED ----------
#
# Read these three beside the retentions below, never alone. Each says "this
# route is gone"; the paired retention says "and the event still routes
# somewhere", which is what stops the pair passing over an emptied hooks block.


def test_subagentstop_no_longer_invokes_the_progress_observer() -> None:
    """The SubagentStop ``*`` -> observer registration was eliminated (PLAN-0102).

    PLAN-0094 AC-1 (i) pinned this route because the subagent L1 reset had
    shipped unreachable. The route is now gone on purpose: ``_handle_subagent_stop``
    was pure L1 and retired with it, so re-registering would spawn a Python
    process on every subagent completion to compute a guaranteed no-op.
    """
    entries = _entries_invoking("SubagentStop", OBSERVER)
    assert not entries, (
        "the progress observer is registered for SubagentStop again. Its handler "
        "was pure L1 and no longer exists, so this route can only cost a process "
        "per subagent. If this is intentional, retire this test with the "
        "reasoning, do not just delete the assertion."
    )


def test_posttooluse_write_edit_no_longer_invokes_the_progress_observer() -> None:
    """The PostToolUse ``Write|Edit`` -> observer registration was eliminated."""
    matchers = {str(entry.get("matcher")) for entry in _entries_invoking("PostToolUse", OBSERVER)}
    assert "Write|Edit" not in matchers, (
        "the progress observer is registered for PostToolUse Write|Edit again. "
        "``_handle_write_or_edit`` was pure L1 and no longer exists; the surviving "
        f"observer duty is the Bash path only. Got matchers {sorted(matchers)}"
    )


def test_pretooluse_write_edit_no_longer_invokes_the_loop_detect_gate() -> None:
    """The PreToolUse ``Write|Edit`` -> loop-detect registration was eliminated.

    This is the expensive one: ``_resolve_target`` mapped nothing but
    Write/Edit to ``FILE_EDIT``, so with L1 gone this registration would spawn a
    Python process on **every single Write and Edit in every session** to reach
    a guaranteed ``None``.
    """
    matchers = {
        str(entry.get("matcher"))
        for entry in _entries_invoking("PreToolUse", "pretooluse_loop_detect.py")
    }
    assert "Write|Edit" not in matchers, (
        "pretooluse_loop_detect is registered for PreToolUse Write|Edit again. "
        "With L1 retired it can only ever allow, at the cost of a process per "
        f"edit. Got matchers {sorted(matchers)}"
    )


# --- PLAN-0102 AC-4 (b) + PLAN-0094 AC-1 (iii): retentions -------------------


def test_pretooluse_loop_detect_gate_is_retained_for_bash() -> None:
    """L4 is the surviving gated surface — the deny wall must stay wired.

    Paired with ``test_pretooluse_write_edit_no_longer_invokes_the_loop_detect_gate``:
    together they say "exactly Bash", which neither says alone.
    """
    matchers = {
        str(entry.get("matcher"))
        for entry in _entries_invoking("PreToolUse", "pretooluse_loop_detect.py")
    }
    assert "Bash" in matchers, (
        f"pretooluse_loop_detect lost its PreToolUse Bash registration — the L4 "
        f"deny wall is now unreachable; got {sorted(matchers)}"
    )


def test_posttooluse_observer_is_retained_for_bash() -> None:
    """The Bash route feeds L2/L3/L4 and the shell-hygiene advisory."""
    matchers = {str(entry.get("matcher")) for entry in _entries_invoking("PostToolUse", OBSERVER)}
    assert "Bash" in matchers, (
        f"PostToolUse Bash no longer routes to the observer — L2, L3, L4 and the "
        f"shell-hygiene advisory all go dark at once; got {sorted(matchers)}"
    )


def test_posttooluse_write_edit_still_validates_handoffs() -> None:
    """Removing the observer from ``Write|Edit`` must not strip the whole matcher.

    The handoff validator shares that entry. This is the assertion that would
    have caught an over-broad excision — deleting the matcher object rather than
    the one hook inside it.
    """
    matchers = {
        str(entry.get("matcher"))
        for entry in _entries_invoking("PostToolUse", "posttooluse_validate_handoff.py")
    }
    assert "Write|Edit" in matchers, (
        f"the handoff validator lost its PostToolUse Write|Edit registration; got "
        f"{sorted(matchers)}"
    )


def test_preexisting_subagentstop_notifier_is_retained() -> None:
    """Removing the observer's SubagentStop entry must not displace the notifier."""
    matchers = {
        str(entry.get("matcher"))
        for entry in _entries_invoking("SubagentStop", "subagentstop_notify.py")
    }
    assert "plan-drafter" in matchers, (
        f"the plan-drafter SubagentStop notifier was removed or re-matched; got "
        f"{sorted(matchers)}"
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


def test_ci_wait_deny_covers_bash_and_monitor() -> None:
    """The CI-wait gate must reach BOTH command surfaces, not just Bash.

    `Monitor` is the harness's own sanctioned wait primitive, and it was the tool
    the agent reached for mid-incident on 2026-08-29 — a call that had zero hook
    coverage of any kind. A Bash-only registration is a gate with a documented
    bypass, and the bypass is the more natural way to write the denied thing.
    """
    matchers = {
        str(entry.get("matcher"))
        for entry in _entries_invoking("PreToolUse", "pretooluse_ci_wait_deny.py")
    }
    assert matchers, "the CI-wait deny lost its PreToolUse registration entirely"
    covered = {surface for m in matchers for surface in m.split("|")}
    assert {"Bash", "Monitor"} <= covered, (
        f"the CI-wait gate no longer covers both command surfaces; a Bash-only gate "
        f"is bypassed by Monitor, which is where the incident's own wait was written. "
        f"Got {sorted(matchers)}"
    )


def test_the_route_the_ci_wait_deny_names_still_exists() -> None:
    """Anti-rot: a deny that names a moved path is obstruction with no way to comply.

    This repo has measured that failure twice already (R8's plan-archive refs, and
    the s241 ``warm.sh`` case behind ``check_retired_claims.py``). The deny text is
    the contract, so the module it points at is asserted importable — not merely
    present as a string.
    """
    import importlib

    hook_src = (REPO_ROOT / ".claude" / "hooks" / "pretooluse_ci_wait_deny.py").read_text(
        encoding="utf-8"
    )
    assert "tools.ci.wait_for_ci" in hook_src, "the deny stopped naming a route at all"
    module = importlib.import_module("tools.ci.wait_for_ci")
    assert hasattr(module, "classify"), (
        "the route the deny names no longer exposes classify(); the gate now points "
        "somewhere that cannot answer the question it denies"
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
