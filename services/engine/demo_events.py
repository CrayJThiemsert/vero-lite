"""Per-process live OperationalEvent view for the OCT demo (PLAN-0015 D1/D2).

Each synthetic vertical adapter serves its OperationalEvents through this
module instead of calling ``synthetic.operational_events()`` directly, so the
demo can layer two **per-process, reset-every-run** effects over the otherwise
deterministic base data:

* **D1 — real-time anchoring** (gated by ``settings.oct_demo_time_anchor``,
  default off). On first access the whole event list is shifted so the breach
  event (the latest reading crossing ``settings.oct_recommend_threshold``) lands
  at the capture time (``prime()`` / first ``events()`` call ~= server start),
  with the original relative spacing preserved. With the flag **off** the base
  datetimes are served unchanged, so ``synthetic.py`` stays deterministic and
  tests are unaffected (D5).

* **D2 — recovery on execute.** The recovery reading is no longer pre-baked into
  the base events; ``inject_recovery()`` appends it when the operator executes
  the decision (``occurred_at`` = real execute time), so the timeline only
  resolves *after* the human acts.

State is keyed by vertical name (one active vertical per process). It is
module-global and therefore process-wide; tests call :func:`reset` between cases
(mirroring ``reset_action_store``) to keep cases isolated.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from services.api.config import settings

Event = dict[str, Any]
EventSource = Callable[[], list[Event]]

# Per-vertical live event list (mutable, per-process). Absent until first built.
_live: dict[str, list[Event]] = {}

_RECOVERY_EVENT_ID = "event-recovery-01"


def _breach_event(events: list[Event]) -> Event | None:
    """Return the breach event used as the anchor reference (PLAN-0015 D1).

    The breach is the recommender trigger — a ``reading`` whose
    ``measured_value`` is at or above the active vertical's
    ``settings.oct_recommend_threshold`` — generalised across verticals (energy
    over-temp 96.5 °C, supply_chain cold-chain 14.6 °C both qualify). When
    several cross, the latest one (the climax) is chosen. ``None`` when no event
    crosses (no incident to anchor on).
    """
    threshold = settings.oct_recommend_threshold
    crossing = [
        e
        for e in events
        if e.get("event_type") == "reading"
        and isinstance(e.get("measured_value"), int | float)
        and e["measured_value"] >= threshold
        and isinstance(e.get("occurred_at"), datetime)
    ]
    if not crossing:
        return None
    return max(crossing, key=lambda e: e["occurred_at"])


def _anchor(events: list[Event], now: datetime) -> list[Event]:
    """Shift every event's ``occurred_at`` so the breach lands at ``now`` (D1).

    Relative spacing is preserved (a single ``delta`` applied to all events).
    No-op when there is no breach to anchor on.
    """
    breach = _breach_event(events)
    if breach is None:
        return events
    delta = now - breach["occurred_at"]
    for event in events:
        occurred = event.get("occurred_at")
        if isinstance(occurred, datetime):
            event["occurred_at"] = occurred + delta
    return events


def events(vertical: str, base_source: EventSource) -> list[Event]:
    """Return the per-process live OperationalEvent list for ``vertical``.

    Built once from ``base_source()`` (a shallow copy of each event so the
    module never mutates the synthetic constants), anchoring it at build time
    when ``settings.oct_demo_time_anchor`` is on. Subsequent calls return the
    same mutable list, so a recovery appended by :func:`inject_recovery`
    persists for the rest of the process run.
    """
    cached = _live.get(vertical)
    if cached is not None:
        return cached
    built = [dict(event) for event in base_source()]
    if settings.oct_demo_time_anchor:
        built = _anchor(built, datetime.now(UTC))
    _live[vertical] = built
    return built


def inject_recovery(
    vertical: str,
    *,
    breach_event_id: str | None = None,
    occurred_at: datetime,
) -> Event | None:
    """Append the recovery reading as the effect of Execute (PLAN-0015 D2).

    The recovery inherits the breach event's location/asset/unit (so it lands on
    the affected asset's per-site timeline for any vertical), overriding the
    severity to ``info``, the value to ``settings.oct_recovery_value``, the
    description to ``settings.oct_recovery_description`` and ``occurred_at`` to
    the real execute time. Idempotent: a prior recovery is replaced, never
    duplicated. Returns the injected event, or ``None`` when the live view has
    not been built yet (nothing to resolve).
    """
    live = _live.get(vertical)
    if live is None:
        return None
    breach: Event | None = None
    if breach_event_id is not None:
        breach = next((e for e in live if e.get("event_id") == breach_event_id), None)
    if breach is None:
        breach = _breach_event(live)
    recovery: Event = dict(breach) if breach is not None else {}
    recovery.update(
        {
            "event_id": _RECOVERY_EVENT_ID,
            "event_type": "reading",
            "severity": "info",
            "measured_value": settings.oct_recovery_value,
            "description": settings.oct_recovery_description,
            "occurred_at": occurred_at,
        }
    )
    live[:] = [e for e in live if e.get("event_id") != _RECOVERY_EVENT_ID]
    live.append(recovery)
    return recovery


def reset(vertical: str | None = None) -> None:
    """Clear the live event view (tests; mirrors ``reset_action_store``).

    ``vertical=None`` clears every vertical; a name clears just that one.
    """
    if vertical is None:
        _live.clear()
    else:
        _live.pop(vertical, None)
