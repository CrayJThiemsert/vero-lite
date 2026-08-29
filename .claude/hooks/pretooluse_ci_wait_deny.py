#!/usr/bin/env python3
"""PreToolUse hook — deny a hand-rolled CI wait, and name the tool that replaces it.

Session 261 wrote this loop four times in one hour and got four different wrong
answers, one of which could not terminate and had to be killed by hand. The rule
against it was already binding (``CLAUDE.md`` §8), already loaded every session, and
already hook-advised — and the loop was still re-derived, worse, each time. So the
thing being gated here is deliberately NOT the syntax.

**Why not gate the quoting.** The obvious predicate — an unescaped ``$`` inside a
``bash -c`` argument — fires on **16.6%** of all Bash commands (measured over 950
commands from five transcripts). Worse, it is trivially satisfiable in the wrong
direction: the cheapest way past it is to DELETE the ``echo "RC=$?"`` line, which
converts a fabricated exit code into no exit check at all. A gate whose cheapest
compliance path destroys the thing it protects is worse than no gate.

**Why this predicate.** It matches the profile every guard in this repo that stuck
shares: it is decidable from the command text alone, it fires on a **rare and
deliberate** act (0.74% of commands), it names an alternative route, and there is no
legitimate need for the denied act once that route exists. The quoting rule fails the
second and third of those, which is why it never bound.

Scoped to **CI** polling, not remote polling in general: a loop waiting on a local
file, an MS-S1 generation, or a container's health has no replacement here, and a
gate that denies work it cannot redirect is obstruction. Widen only when the tool
widens — and prototype the widened matcher before widening it.

Registered on ``Bash`` **and** ``Monitor``. A Bash-only gate is bypassed by the
harness's own sanctioned wait primitive, which is exactly what the agent reached for
mid-incident.
"""

from __future__ import annotations

import json
import re
import sys

#: A loop construct. `for` requires the `in` so an arithmetic `for((;;))` in some
#: unrelated one-liner does not read as a poll loop.
_LOOP_RE = re.compile(r"\b(?:while|until)\b|\bfor\b[^\n]*\bin\b")

#: The wait itself. Without a sleep it is not a poll loop, it is a one-shot query.
_SLEEP_RE = re.compile(r"\bsleep\s+\d")

#: CI specifically — the GitHub Actions surface the tool covers. NOT `curl`, and NOT
#: `gh` in general: `gh pr view` inside a loop over PR numbers is ordinary work.
_CI_POLL_RE = re.compile(r"\bgh\s+(?:run|pr)\s+(?:list|checks|view|watch)\b|actions/runs")

_ROUTE = (
    "uv run python -m tools.ci.wait_for_ci wait --sha <sha>\n"
    "    -> detached; writes a sentinel under .claude/state/ci_wait/\n"
    "uv run python -m tools.ci.wait_for_ci status --sha <sha>\n"
    "    -> one-shot; exit 0 ONLY on a conclusion measured at that sha"
)

_REASON = f"""This is a hand-rolled CI wait. Four of them were written in one hour on
2026-08-29 and all four were wrong — one reported green against a sha that had no run
at all (`gh run list -c <sha>` returns `[]` with exit status 0), and one froze its own
loop condition to a literal and had to be killed by hand.

Use the shipped tool instead:

{_ROUTE}

It refuses to infer a pass from silence: absence of runs is NO-RUN (exit 5), a
cancelled run is SUPERSEDED (exit 4), a deadline is TIMEOUT (exit 6), and exit 0 is
reserved for a conclusion actually measured at the sha you named.

If you are polling something the tool does not cover, do not inline the loop — put it
in a script file under `tools/`. A file has exactly one shell layer, which is what
makes the quoting hazard impossible rather than merely discouraged."""


def _emit_deny(reason: str) -> int:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    return 0


def is_hand_rolled_ci_wait(command: str) -> bool:
    """True for a loop that sleeps and polls GitHub Actions. All three are required."""
    return bool(
        _LOOP_RE.search(command) and _SLEEP_RE.search(command) and _CI_POLL_RE.search(command)
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # fail open — a gate that cannot read its input must not block work
    if not isinstance(payload, dict):
        return 0

    if payload.get("tool_name") not in {"Bash", "Monitor"}:
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    command = tool_input.get("command", "")
    if not isinstance(command, str) or not is_hand_rolled_ci_wait(command):
        return 0

    return _emit_deny(_REASON)


if __name__ == "__main__":
    raise SystemExit(main())
