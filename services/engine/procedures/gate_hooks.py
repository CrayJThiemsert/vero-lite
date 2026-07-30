"""The post-resolution gate hook (PLAN-0096 Step 8, build-order item 3).

The engine has no seam on gate resolution: ``on_step_complete``
(``orchestrator.py``) is engine-internal, and ``_FIRED_HOOKS`` (``cli.py``) is
scheduler-daemon-only, so an API-process resolution reaches neither. This is the
smallest seam that closes that gap — one optional callback per vertical, fired
after a gate driver has durably committed its decision.

**Why the engine may not know what the hook writes.** A repair-case ↔ run link is
one operator's audit need. The engine's job is to say *"this step was resolved,
here is the durable result"*; deciding that this means a row in a fleet table is
the vertical's job (ADR-006). So the payload is the persisted
:class:`StepResult` and nothing narrower — every consumer extracts what it needs.

**Dispatch is by the vertical on the ACTION, not on the run.** ``PipelineRun``
carries no ``vertical`` column (verified s191: it has ``procedure_id`` and
``agent_id``, not a vertical), while every proposal in the resolved artifact does
carry ``action.vertical``. Reading it there is not a workaround — it is the only
authoritative per-decision answer, and it is already persisted.

**Fail-soft, but never silent.** A link row is an audit convenience; a human's
approval is not. If a hook raises, the resolution stands and the failure is
RECORDED where a test and a health check can see it. That last clause is the
whole design: session 191 measured a fail-soft handler swallowing an exception so
completely that the test asserting the resulting absence stayed green. A
swallowed error that nothing can observe turns every downstream oracle vacuous,
so :func:`failures` exists before any caller asks for it.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from services.engine.procedures.runs import StepResult

_logger = logging.getLogger(__name__)

#: ``(session, run_id, resolved_step) -> None``. The callback owns its own
#: transaction: it runs AFTER the gate driver has committed, so nothing it does —
#: including failing — can roll back the decision it is recording.
OnResolved = Callable[[AsyncSession, str, StepResult], Awaitable[None]]

_HOOKS: dict[str, OnResolved] = {}
_FAILURES: list[dict[str, str]] = []


def register_on_resolved(vertical: str, hook: OnResolved) -> None:
    """Register (or replace) the post-resolution hook for one vertical."""
    _HOOKS[vertical] = hook


def clear_on_resolved(vertical: str | None = None) -> None:
    """Drop hooks and recorded failures. Tests call this between cases."""
    if vertical is None:
        _HOOKS.clear()
    else:
        _HOOKS.pop(vertical, None)
    _FAILURES.clear()


def failures() -> list[dict[str, str]]:
    """Every hook failure recorded this process, oldest first.

    Read by tests and by health surfaces. An empty list after a resolution means
    the hook ran cleanly — which is a DIFFERENT fact from "the hook wrote nothing",
    and keeping them distinguishable is what stops a swallowed exception from
    passing as correct behaviour.
    """
    return [dict(entry) for entry in _FAILURES]


def decided_entries(target: StepResult) -> list[dict[str, Any]]:
    """Every action this step DECIDED, approved or not — the complete record.

    ``artifact["output_set"]`` is the wrong source for an audit consumer and the
    gate says so in its own words: *"executed effects thread forward; rejects are
    recorded, not threaded"* (``action_step.py``). ``output_set`` is the subset the
    NEXT step consumes, so a gate that rejected everything leaves it empty, and a
    hook reading it would conclude the resolution decided nothing — turning every
    rejection into a missing row rather than a recorded refusal.

    ``artifact["decisions"]`` is the full per-action list in proposal order, each
    entry carrying the FINAL status (``executed`` / ``rejected``), which is also the
    status a consumer actually wants. ``output_set`` remains the fallback for step
    artifacts that carry no ``decisions`` key at all — an ``auto`` action step never
    passed through a human gate, so it has proposals but no decision list.
    """
    artifact = target.artifact or {}
    entries = artifact.get("decisions")
    if not isinstance(entries, list) or not entries:
        entries = artifact.get("output_set") or []
    return [entry for entry in entries if isinstance(entry, dict)]


def vertical_of(target: StepResult) -> str | None:
    """The vertical this resolved step belongs to, read off its own decisions.

    Returns None when the step carries no decided action with a vertical — a step
    with nothing to dispatch on, which is a no-op rather than an error.
    """
    for entry in decided_entries(target):
        action = entry.get("action")
        if isinstance(action, dict):
            vertical = action.get("vertical")
            if isinstance(vertical, str) and vertical:
                return vertical
    return None


async def fire_on_resolved(session: AsyncSession, run_id: str, target: StepResult) -> None:
    """Fire the registered hook for this step's vertical, if there is one.

    Called by BOTH gate drivers — ``resolve_gated_step`` and
    ``ratify_gated_step``. Hooking only the first would silently drop every
    deferred-ratification decision (ADR-0034 E-2), which is precisely the class of
    gap this seam exists to close, so the second call site is a requirement rather
    than a nicety.
    """
    vertical = vertical_of(target)
    if vertical is None:
        return
    hook = _HOOKS.get(vertical)
    if hook is None:
        return
    try:
        await hook(session, run_id, target)
    except Exception as exc:  # fail-soft — the human's decision already committed
        entry: dict[str, Any] = {
            "vertical": vertical,
            "run_id": run_id,
            "step_id": target.step_id,
            "error": f"{type(exc).__name__}: {exc}",
        }
        _FAILURES.append({k: str(v) for k, v in entry.items()})
        _logger.warning(
            "on_resolved hook failed for vertical %s (run %s, step %s): %s",
            vertical,
            run_id,
            target.step_id,
            exc,
        )
