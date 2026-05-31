"""Supply-chain vertical action handlers (PLAN-0005 §6.5).

Phase 2 ships a single no-op echo handler: it records the action and
returns a receipt without performing real I/O. Real handlers (carrier
dispatch, reroute, cold-chain hold) land with the design partner. Mirrors
the energy vertical's handler shape — only the registered vertical differs.
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


def register_supply_chain_handlers() -> None:
    """Register the supply_chain vertical's action handlers on the registry."""
    registry.register_handler("supply_chain", "echo", echo_handler)
