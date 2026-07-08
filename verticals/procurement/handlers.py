"""Procurement vertical action handlers (PLAN-0016 new-vertical scaffold;
PLAN-0036 Step 4 hardening).

Every handler is a **no-op receipt** today: it records the action and returns a
receipt without performing real I/O. Real ERP / email / CMMS integration lands
with the design partner (§ Out of Scope).

Beyond the retained ``echo`` no-op, the vertical registers the ontology
``RecommendedAction.action_type`` vocabulary (procurement_v0:
``emergency_source`` / ``reorder`` / ``request_approval`` / ``issue_po`` /
``escalate``) as **distinctly-named** no-op stubs, so the procedure engine's
action steps resolve a real registered handler (the ``procedures.yaml`` agent
allowlist invokes ``emergency_source`` / ``request_approval`` / ``issue_po`` /
``reorder`` / ``echo``). The deterministic procedure path fixes the executed
handler via ``step.handler`` (ADR-016); the LLM never selects it
(governed ≠ generated, L-3).
"""

from __future__ import annotations

from typing import Any

from services.engine.actions import RecommendedAction
from services.engine.registry import Handler, registry

ACTION_TYPES: tuple[str, ...] = (
    "emergency_source",
    "reorder",
    "request_approval",
    "issue_po",
    "escalate",
)
"""The procurement ontology ``RecommendedAction.action_type`` enum — the real
action vocabulary, registered as no-op stubs alongside ``echo``."""

ACTION_DESCRIPTIONS: dict[str, str] = {
    "echo": "Diagnostic no-op — record the action without performing anything.",
    "emergency_source": (
        "Urgent off-cycle sourcing for a critical failure or line-down, where the "
        "normal reorder lead time is unacceptable — the hero/emergency path."
    ),
    "reorder": (
        "Routine on-contract restock at the normal lead time — the calm path when "
        "stock is low but there is no line-down urgency."
    ),
    "request_approval": (
        "Route the proposed buy to a human approver before anything executes "
        "(spend or policy gate)."
    ),
    "issue_po": "Raise a purchase order against an existing contract for an already-approved buy.",
    "escalate": (
        "Raise the event to a higher tier of human ownership when no automated "
        "action is appropriate."
    ),
}
"""Per-handler when-to-pick descriptions surfaced to the reactive judgment prompt
(PLAN-0060). Keyed by ``echo`` + every :data:`ACTION_TYPES` entry. The
``emergency_source`` vs ``reorder`` pair is the load-bearing distinction the
session-114 live smoke found the model getting wrong from bare names alone."""


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
    partner's real ERP / email / CMMS integration."""

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


def register_procurement_handlers() -> None:
    """Register the procurement vertical's action handlers on the registry — the
    retained ``echo`` no-op plus the ontology action-type vocabulary as no-op
    stubs (PLAN-0036 Step 4)."""
    registry.register_handler(
        "procurement", "echo", echo_handler, description=ACTION_DESCRIPTIONS["echo"]
    )
    for action_type in ACTION_TYPES:
        registry.register_handler(
            "procurement",
            action_type,
            _stub_action_handler(action_type),
            description=ACTION_DESCRIPTIONS[action_type],
        )
