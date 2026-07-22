"""FleetMaintenance vertical action handlers (PLAN-0086 — the timed manual scaffold).

Every handler is a **no-op receipt** today: it records the action and returns a receipt without
performing real I/O. Real garage / parts-ledger I/O (the approved repair spend, the
replacement-truck dispatch, the tow) lands with the design partner. Mirrors the building_materials
vertical's handler shape — only the registered vertical + vocabulary differ.

Beyond the retained ``echo`` no-op, the vertical registers the ontology
``RecommendedAction.action_type`` vocabulary (fleet_maintenance_v0: ``approve_repair_spend`` /
``dispatch_replacement_truck`` / ``tow_to_partner_garage`` / ``escalate``) as **distinctly-named**
no-op stubs, so the LLM's ``suggested_handler`` is a real multiple-choice (the registry enum the
model picks from). The deterministic procedure path still fixes the executed handler via
``step.handler`` (ADR-016): the governed-repair hero's ``approve`` step fixes ``escalate`` (route to
the DOA authority) and its ``fulfill`` step fixes ``approve_repair_spend`` (the approved write).
"""

from __future__ import annotations

from typing import Any

from services.engine.actions import RecommendedAction
from services.engine.registry import Handler, registry

ACTION_TYPES: tuple[str, ...] = (
    "approve_repair_spend",
    "dispatch_replacement_truck",
    "tow_to_partner_garage",
    "escalate",
    "schedule_pm_service",
)
"""The fleet_maintenance ontology ``RecommendedAction.action_type`` enum — the real action
vocabulary, registered as no-op stubs alongside ``echo``."""

ACTION_DESCRIPTIONS: dict[str, str] = {
    "echo": "Diagnostic no-op — record the action without performing anything.",
    "approve_repair_spend": (
        "Approve the quoted repair spend for the truck after the governed authority decision — "
        "the approved terminal write."
    ),
    "dispatch_replacement_truck": (
        "Hire / dispatch a replacement vehicle to transfer the load so the delivery window is "
        "still met while the broken-down truck is off the road."
    ),
    "tow_to_partner_garage": (
        "Tow the disabled truck to a partner garage instead of authorising a roadside repair."
    ),
    "escalate": (
        "Route the repair-spend decision to a higher tier of human authority (the DOA ladder) "
        "when the quote demands it."
    ),
    "schedule_pm_service": (
        "Book the truck in for its routine interval service after a single human go/no-go — the "
        "calm-path terminal write. Routine maintenance, NOT a breakdown response: no DOA ladder, "
        "no emergency waiver."
    ),
}
"""Per-handler when-to-pick descriptions surfaced to the reactive judgment prompt (PLAN-0060).
Keyed by ``echo`` + every :data:`ACTION_TYPES` entry."""


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
    """Build a named no-op action handler — the named-action equivalent of :func:`echo_handler`
    (records + receipts, no real I/O). Pending the design partner's real garage/ERP integration."""

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


def register_fleet_maintenance_handlers() -> None:
    """Register the fleet_maintenance vertical's action handlers on the registry — the retained
    ``echo`` no-op plus the ontology action-type vocabulary as no-op stubs."""
    registry.register_handler(
        "fleet_maintenance", "echo", echo_handler, description=ACTION_DESCRIPTIONS["echo"]
    )
    for action_type in ACTION_TYPES:
        registry.register_handler(
            "fleet_maintenance",
            action_type,
            _stub_action_handler(action_type),
            description=ACTION_DESCRIPTIONS[action_type],
        )
