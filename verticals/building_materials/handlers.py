"""BuildingMaterials vertical action handlers (PLAN-0016 scaffold; PLAN-0081 governed-credit hero).

Every handler is a **no-op receipt** today: it records the action and returns a receipt without
performing real I/O. Real ERP / credit-ledger I/O (the credit override, the order hold, the
prepayment demand) lands with the design partner. Mirrors the supply_chain vertical's handler shape
— only the registered vertical + vocabulary differ.

Beyond the retained ``echo`` no-op, the vertical registers the ontology
``RecommendedAction.action_type`` vocabulary (building_materials_v0: ``approve_credit_override`` /
``hold_order`` / ``require_prepayment`` / ``escalate``) as **distinctly-named** no-op stubs, so the
LLM's ``suggested_handler`` is a real multiple-choice (the registry enum the model picks from). The
deterministic procedure path still fixes the executed handler via ``step.handler`` (ADR-016): the
governed-credit hero's ``approve`` step fixes ``escalate`` (route to the DOA authority) and its
``fulfill`` step fixes ``approve_credit_override`` (the approved release write).
"""

from __future__ import annotations

from typing import Any

from services.engine.actions import RecommendedAction
from services.engine.registry import Handler, registry

ACTION_TYPES: tuple[str, ...] = (
    "approve_credit_override",
    "hold_order",
    "require_prepayment",
    "escalate",
)
"""The building_materials ontology ``RecommendedAction.action_type`` enum — the real action
vocabulary, registered as no-op stubs alongside ``echo``."""

ACTION_DESCRIPTIONS: dict[str, str] = {
    "echo": "Diagnostic no-op — record the action without performing anything.",
    "approve_credit_override": (
        "Approve the credit release / override the account's limit for this order after the "
        "governed authority decision — the approved terminal write."
    ),
    "hold_order": (
        "Hold the order in place pending the credit decision — the exposure breaches the "
        "account's approved limit."
    ),
    "require_prepayment": (
        "Require prepayment / cash terms before releasing the order instead of extending credit."
    ),
    "escalate": (
        "Route the credit decision to a higher tier of human authority (the DOA ladder) when the "
        "exposure demands it."
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
    (records + receipts, no real I/O). Pending the design partner's real ERP/credit integration."""

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


def register_building_materials_handlers() -> None:
    """Register the building_materials vertical's action handlers on the registry — the retained
    ``echo`` no-op plus the ontology action-type vocabulary as no-op stubs (PLAN-0019 Part B)."""
    registry.register_handler(
        "building_materials", "echo", echo_handler, description=ACTION_DESCRIPTIONS["echo"]
    )
    for action_type in ACTION_TYPES:
        registry.register_handler(
            "building_materials",
            action_type,
            _stub_action_handler(action_type),
            description=ACTION_DESCRIPTIONS[action_type],
        )
