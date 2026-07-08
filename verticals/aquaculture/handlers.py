"""Aquaculture vertical action handlers (PLAN-0016 new-vertical scaffold;
PLAN-0019 Part B hardening).

Every handler is a **no-op receipt** today: it records the action and returns a
receipt without performing real I/O. Real aerator / water-exchange I/O lands with
the design partner.

Beyond the retained ``echo`` no-op, the vertical now registers the ontology
``RecommendedAction.action_type`` vocabulary (aquaculture_v0:
``start_emergency_aerator`` / ``dispatch_technician`` / ``increase_water_exchange``
/ ``escalate``) as **distinctly-named** no-op stubs, so the LLM's
``suggested_handler`` is a real multiple-choice (the registry enum the model picks
from) — the PLAN-0019 Part B benchmark-hardening lever (β + α). The deterministic
procedure path still fixes the executed handler via ``step.handler`` (ADR-016).
"""

from __future__ import annotations

from typing import Any

from services.engine.actions import RecommendedAction
from services.engine.registry import Handler, registry

ACTION_TYPES: tuple[str, ...] = (
    "start_emergency_aerator",
    "dispatch_technician",
    "increase_water_exchange",
    "escalate",
)
"""The aquaculture ontology ``RecommendedAction.action_type`` enum — the real
action vocabulary, registered as no-op stubs alongside ``echo``."""

ACTION_DESCRIPTIONS: dict[str, str] = {
    "echo": "Diagnostic no-op — record the action without performing anything.",
    "start_emergency_aerator": (
        "Start emergency aeration to raise dissolved oxygen when a pond crashes "
        "below the safe threshold — the urgent path."
    ),
    "dispatch_technician": (
        "Send a technician to the pond/site to inspect or intervene on the ground."
    ),
    "increase_water_exchange": (
        "Increase the water-exchange rate to improve water quality — a slower "
        "corrective measure than emergency aeration."
    ),
    "escalate": (
        "Raise the event to a higher tier of human ownership when no automated "
        "action is appropriate."
    ),
}
"""Per-handler when-to-pick descriptions surfaced to the reactive judgment prompt
(PLAN-0060). Keyed by ``echo`` + every :data:`ACTION_TYPES` entry."""


async def echo_handler(action: RecommendedAction) -> dict[str, Any]:
    """No-op handler: echo the action back as an execution receipt."""
    return {
        "handler": "echo",
        "executed": True,
        "action_id": action.id,
        "vertical": action.vertical,
        "payload": action.handler_payload,
    }


def _stub_action_handler(name: str) -> Handler:
    """Build a named no-op action handler — the named-action equivalent of
    :func:`echo_handler` (records + receipts, no real I/O). Pending the design
    partner's real aerator/water-exchange integration."""

    async def handler(action: RecommendedAction) -> dict[str, Any]:
        return {
            "handler": name,
            "executed": True,
            "stub": True,
            "action_id": action.id,
            "vertical": action.vertical,
            "payload": action.handler_payload,
        }

    handler.__name__ = f"{name}_handler"
    return handler


def register_aquaculture_handlers() -> None:
    """Register the aquaculture vertical's action handlers on the registry — the
    retained ``echo`` no-op plus the ontology action-type vocabulary as no-op
    stubs (PLAN-0019 Part B)."""
    registry.register_handler(
        "aquaculture", "echo", echo_handler, description=ACTION_DESCRIPTIONS["echo"]
    )
    for action_type in ACTION_TYPES:
        registry.register_handler(
            "aquaculture",
            action_type,
            _stub_action_handler(action_type),
            description=ACTION_DESCRIPTIONS[action_type],
        )
