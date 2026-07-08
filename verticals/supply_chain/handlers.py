"""Supply-chain vertical action handlers (PLAN-0005 §6.5; PLAN-0019 Part B
hardening).

Every handler is a **no-op receipt** today: it records the action and returns a
receipt without performing real I/O. Real carrier / cold-chain I/O (reroute,
expedite, hold, inspect) lands with the design partner. Mirrors the energy
vertical's handler shape — only the registered vertical + vocabulary differ.

Beyond the retained ``echo`` no-op, the vertical now registers the ontology
``RecommendedAction.action_type`` vocabulary (supply_chain_v0: ``reroute`` /
``expedite`` / ``hold`` / ``inspect`` / ``escalate``) as **distinctly-named**
no-op stubs, so the LLM's ``suggested_handler`` is a real multiple-choice (the
registry enum the model picks from) — the PLAN-0019 Part B benchmark-hardening
lever (β + α). The deterministic procedure path still fixes the executed handler
via ``step.handler`` (ADR-016).
"""

from __future__ import annotations

from typing import Any

from services.engine.actions import RecommendedAction
from services.engine.registry import Handler, registry

ACTION_TYPES: tuple[str, ...] = ("reroute", "expedite", "hold", "inspect", "escalate")
"""The supply_chain ontology ``RecommendedAction.action_type`` enum — the real
action vocabulary, registered as no-op stubs alongside ``echo``."""

ACTION_DESCRIPTIONS: dict[str, str] = {
    "echo": "Diagnostic no-op — record the action without performing anything.",
    "reroute": (
        "Divert the shipment to an alternate route or carrier to avoid a delay or disruption."
    ),
    "expedite": (
        "Speed up an in-flight shipment (upgrade service level) to recover a slipping delivery."
    ),
    "hold": (
        "Halt the shipment in place pending a decision — e.g. a suspected cold-chain "
        "or quality breach."
    ),
    "inspect": "Trigger a physical or documentary inspection of the shipment before it proceeds.",
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
    partner's real carrier/cold-chain integration."""

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


def register_supply_chain_handlers() -> None:
    """Register the supply_chain vertical's action handlers on the registry — the
    retained ``echo`` no-op plus the ontology action-type vocabulary as no-op
    stubs (PLAN-0019 Part B)."""
    registry.register_handler(
        "supply_chain", "echo", echo_handler, description=ACTION_DESCRIPTIONS["echo"]
    )
    for action_type in ACTION_TYPES:
        registry.register_handler(
            "supply_chain",
            action_type,
            _stub_action_handler(action_type),
            description=ACTION_DESCRIPTIONS[action_type],
        )
