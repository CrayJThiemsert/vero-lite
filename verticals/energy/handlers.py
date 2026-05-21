"""Energy vertical action handlers (PLAN-0005 §6.5).

Phase 2 ships a single no-op echo handler: it records the action and
returns a receipt without performing real I/O. Real handlers (grid
control, technician dispatch) land with the design partner.
"""

from __future__ import annotations

from typing import Any

from services.engine.actions import RecommendedAction
from services.engine.registry import registry


async def echo_handler(action: RecommendedAction) -> dict[str, Any]:
    """No-op handler: echo the action back as an execution receipt."""
    return {
        "handler": "echo",
        "executed": True,
        "action_id": action.id,
        "vertical": action.vertical,
        "payload": action.handler_payload,
    }


def register_energy_handlers() -> None:
    """Register the energy vertical's action handlers on the registry."""
    registry.register_handler("energy", "echo", echo_handler)
