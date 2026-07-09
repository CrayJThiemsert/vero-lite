"""The deterministic, vertical-agnostic advisory-LLM stub (PLAN-0062 Step 1, OQ-1).

An ``action`` step composes its ADR-007 D2 ``RecommendedAction`` envelope from an LLM
*judgment* (:func:`~services.engine.llm.structured.generate_judgment`) — but the two
envelope fields that carry governance weight are sourced **deterministically**, never
from the model: ``suggested_handler`` is the procedure author's ``step.handler`` and
``affected_entities`` is the loop entity
(:func:`~services.engine.procedures.action_step._compose_action` /
``_loop_entity_ref``). Only the advisory prose is the model's.

That is what makes stubbing honest here: the governed decision is untouched (governed
≠ generated, ADR-0019 IN-3) while a production executor factory stays offline and
**host-state-free** (PLAN-0062 SD-6; CLAUDE.md §8). The real ``OllamaClient`` remains
the ``ActionStepExecutor`` default for callers that want live prose.

**Vertical-agnostic by construction.** The structured call's ``response_format`` is
:func:`~services.engine.llm.structured._judgment_schema`, whose ``suggested_handler``
property is enum-constrained to ``registry.handler_names(vertical)``. Naming the first
enum member is therefore the one choice guaranteed to satisfy ``structured``'s
registered-handler semantic check for *any* vertical — and it never reaches the
envelope, which takes ``step.handler``. No per-vertical parameter, so PR2/PR3 reuse
this unchanged.

The procurement hero harness keeps its own older, PO-shaped stub
(``verticals/procurement/hero_demo/run.py``) — byte-unchanged per PLAN-0062 AC-6.
"""

from __future__ import annotations

import json
from typing import Any

from services.engine.llm.client import ChatResult
from services.engine.llm.structured import ChatClient

_ADVISORY_PROSE = "advisory draft — LLM prose stubbed; the governed decision is the rule"

_FALLBACK_HANDLER = "echo"
"""Used only when the vertical registered no handlers, so the schema carries no enum.
The semantic check then rejects it — a loud failure, which is correct: an action step
over a handler-less vertical is unrunnable."""


def _stub_judgment(response_format: dict[str, Any]) -> str:
    """A schema-valid :class:`~services.engine.llm.structured.LlmJudgment` payload.

    ``affected_entities`` is a placeholder: ``_compose_action`` replaces it with the
    loop entity, so its content is never observable. ``confidence`` is advisory only
    (ADR-010 IN-3 — it routes nothing).
    """
    handler_enum = (
        response_format.get("properties", {}).get("suggested_handler", {}).get("enum") or []
    )
    return json.dumps(
        {
            "title": "Advisory proposal (stubbed)",
            "description": "A governed proposal awaiting the human gate; prose stubbed offline.",
            "rationale": _ADVISORY_PROSE,
            "confidence": 0.5,
            "affected_entities": [{"object_type": "unknown", "primary_key": "unknown"}],
            "suggested_handler": handler_enum[0] if handler_enum else _FALLBACK_HANDLER,
            "handler_payload": {},
        }
    )


class AdvisoryStubClient:
    """A deterministic ``ChatClient``: structured calls get a schema-valid judgment,
    unstructured (reasoning) calls get fixed prose. No network, no MS-S1."""

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        if response_format is not None:
            return ChatResult(
                content=_stub_judgment(response_format), thinking=None, model="stub", raw={}
            )
        return ChatResult(content=_ADVISORY_PROSE, thinking=None, model="stub", raw={})


def advisory_stub_factory(_model: str) -> ChatClient:
    """A ``ClientFactory`` (the ``ActionStepExecutor(client_factory=...)`` seam) yielding
    the deterministic stub, ignoring the agent's declared model."""
    return AdvisoryStubClient()
