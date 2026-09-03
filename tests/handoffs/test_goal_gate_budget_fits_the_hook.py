"""🔴 s275 — the goal gate's check budget must fit inside the Stop hook's own timeout.

`.claude/settings.json` gives the Stop hook a `timeout` (seconds); `_goal_gate.py`
gives its deterministic `check` criteria a separate `DEFAULT_CHECK_BUDGET_S`. The
two live in different files, in different languages, and cannot import each other —
the same shape as `BATTERY_LOCK_STALE_AFTER_S` in
`test_goal_gate_battery_lock.py::test_the_two_sides_agree_on_the_staleness_bound`,
and duplicated constants drift.

Measured s275: the budget was **600 s** inside a **180 s** hook. Unreachable by
3.3x, and not merely cosmetic:

* `stop_continuation.main()` runs this gate FIRST and the Sonnet classifier plus
  the chain-cap fail-safe AFTER, so a gate that spent even half of 600 s would
  starve them.
* When the harness kills the hook, the criterion's **WSL-side pytest child is
  orphaned** — still holding the per-checkout test database with no owner to
  release it. That is the resource whose contention fabricated nine failures in
  s275 (and corrupted runs in s228 and s253 before it).

So the relationship is load-bearing, not tidy-mindedness, and this file is the
only thing that would ever notice it drifting back.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SETTINGS = REPO_ROOT / ".claude" / "settings.json"
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

import _goal_gate  # noqa: E402  — sys.path manipulation above

#: Seconds reserved for everything the Stop hook does AFTER the gate: the Sonnet
#: classifier's API call, the Telegram notification, and the auto-handoff.
REQUIRED_MARGIN_S = 45


def _stop_hook_timeout_s() -> int | None:
    """The declared timeout of the Stop entry that runs ``stop_continuation.py``."""
    data: dict[str, Any] = json.loads(SETTINGS.read_text(encoding="utf-8"))
    for entry in (data.get("hooks") or {}).get("Stop") or []:
        for hook in entry.get("hooks") or []:
            if not isinstance(hook, dict):
                continue
            if "stop_continuation.py" in str(hook.get("command", "")):
                timeout = hook.get("timeout")
                return timeout if isinstance(timeout, int) else None
    return None


def test_the_stop_hook_declares_a_timeout_we_can_read() -> None:
    """Positive control, and it is not ceremony.

    Every assertion below is of the form "the budget is under X". If the parse
    silently returned ``None`` — a renamed script, a restructured settings file —
    those assertions would be skipped or trivially satisfied and this whole module
    would go green while measuring nothing.
    """
    timeout = _stop_hook_timeout_s()
    assert timeout is not None, (
        "no Stop hook entry running stop_continuation.py declares an integer timeout — "
        "the pin below cannot be evaluated, so treat this as RED, not as absence of a rule"
    )
    assert timeout > 0, f"Stop hook timeout is {timeout}, which cannot bound anything"


def test_the_check_budget_fits_inside_the_stop_hook_timeout() -> None:
    """The pin itself. Prints the values it measured, per CLAUDE.md §8."""
    timeout = _stop_hook_timeout_s()
    assert timeout is not None  # guarded by the control above
    budget = _goal_gate.DEFAULT_CHECK_BUDGET_S

    assert budget + REQUIRED_MARGIN_S <= timeout, (
        f"goal-gate check budget does not fit the Stop hook: "
        f"budget={budget}s margin={REQUIRED_MARGIN_S}s timeout={timeout}s "
        f"(budget+margin={budget + REQUIRED_MARGIN_S} > {timeout}). "
        "Either lower DEFAULT_CHECK_BUDGET_S in .claude/hooks/_goal_gate.py or raise "
        "the Stop hook's timeout in .claude/settings.json — but raising it means every "
        "Stop can block for that long, so lowering the budget is usually right."
    )


def test_the_budget_is_not_trivially_small() -> None:
    """The other direction, because the assertion above is satisfiable by setting the
    budget to 1 — which would make every check TIMEOUT, and a timeout is *unresolved*,
    never a pass (ADR-0018 VX-2). That failure mode is silent: the gate would report
    "checks not green" forever and read as a working gate.
    """
    assert _goal_gate.DEFAULT_CHECK_BUDGET_S >= 60, (
        f"DEFAULT_CHECK_BUDGET_S is {_goal_gate.DEFAULT_CHECK_BUDGET_S}s — too small for "
        "a real check (a scoped pytest selection or a full mypy run), so every criterion "
        "would time out and the gate would be permanently unresolved"
    )
