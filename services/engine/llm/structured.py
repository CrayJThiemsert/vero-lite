"""Structured-output generation for the LLM reasoning hook (PLAN-0006 Step 3).

Runs the two-call Pattern B exchange (SD-2) and returns a validated,
semantically-checked :class:`LlmJudgment` — or raises
:class:`StructuredOutputError` when the bounded retry budget (SD-1,
default 3 = 1 initial + 2 retries) is exhausted, which the Step 5
fail-safe (ADR-010 IN-4) catches.

SC-1 disposition (PLAN-0006 §8 surfaced catch — resolved by Code here)
----------------------------------------------------------------------
PLAN-0006 §6.3 says call 2 emits ``format =
RecommendedAction.model_json_schema()``; §6.5 assigns ``id``,
``vertical``, ``created_at``, ``requires_approval``,
``audit_metadata.actor_kind`` and the harness-emitted trace steps to the
HARNESS, not the model. A literal §6.3 reading forces the model to invent
engine-owned truth (an action id, a timestamp), which is error-prone and
semantically wrong. **Resolution:** constrained generation targets the
reduced :class:`LlmJudgment` sub-schema — the fields that are genuine
model judgment — and the harness composes the full ADR-007 D2
``RecommendedAction`` envelope around it (Step 5 / Step 4). The ADR-007
D2 envelope class is **unchanged** (PLAN-0006 §6.1 hard constraint) —
only the JSON Schema handed to Ollama ``format`` differs.

Structured-output mechanism: raw Ollama ``format`` plus a hand-rolled
validate-and-retry loop — no new dependency (PLAN-0006 SD-4).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel, Field, ValidationError

from services.engine.actions import EntityRef
from services.engine.llm.client import ChatResult
from services.engine.llm.prompt import build_reasoning_messages, build_structuring_messages
from services.engine.registry import RegistryError, registry


class ChatClient(Protocol):
    """The subset of :class:`~services.engine.llm.client.OllamaClient` that
    structured generation depends on — an injection seam for offline tests.
    """

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = ...,
        response_format: dict[str, Any] | None = ...,
        temperature: float = ...,
    ) -> ChatResult: ...


class LlmJudgment(BaseModel):
    """The reduced "LLM-judgment" sub-schema fed to Ollama ``format`` (SC-1).

    Holds ONLY the fields that are genuine model judgment. The harness
    composes the full ADR-007 D2 ``RecommendedAction`` envelope around it
    (Step 5), owning ``id``/``vertical``/``created_at``/
    ``requires_approval``/``audit_metadata`` and the harness-emitted trace
    steps.
    """

    title: str = Field(..., min_length=1, description="Short imperative action title")
    description: str = Field(..., min_length=1, description="What to do and why")
    rationale: str = Field(
        ...,
        min_length=1,
        description="Concise model-asserted rationale — becomes the llm_inference trace step",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model-asserted confidence in [0,1] — advisory only (ADR-010 IN-3)",
    )
    affected_entities: list[EntityRef] = Field(
        ...,
        min_length=1,
        description="Ontology entities the action targets (at least one)",
    )
    suggested_handler: str = Field(
        ..., min_length=1, description="Name of a handler registered for the vertical"
    )
    handler_payload: dict[str, Any] = Field(
        default_factory=dict, description="Input payload passed to the handler on execute"
    )


_JUDGMENT_SCHEMA: dict[str, Any] = LlmJudgment.model_json_schema()
"""The JSON Schema handed to Ollama ``format`` for constrained generation."""


class StructuredOutputError(RuntimeError):
    """Raised when structured generation fails after the full retry budget.

    The Step 5 fail-safe (PLAN-0006 §6.6 / ADR-010 IN-4) catches this to
    fall back to the deterministic rule path — it never escapes the loop.
    """


@dataclass(frozen=True)
class JudgmentResult:
    """The outcome of a successful Pattern B exchange.

    ``thinking`` and ``draft`` are call-1 output, carried so Step 4 can
    assemble the hybrid reasoning trace; ``attempts`` is the number of
    call-2 attempts the retry loop consumed.
    """

    judgment: LlmJudgment
    thinking: str | None
    draft: str
    model: str
    attempts: int


async def generate_judgment(
    client: ChatClient,
    event: Mapping[str, Any],
    vertical: str,
    *,
    retry_budget: int = 3,
) -> JudgmentResult:
    """Run the two-call Pattern B exchange and return a validated judgment.

    Call 1 reasons (``think=True``); call 2 emits the constrained envelope
    against :data:`_JUDGMENT_SCHEMA`. Per the CHECKPOINT-0 contract, call
    2 OMITS ``think`` (never ``think=False`` with ``format`` — Ollama
    #15260). A parse / schema / semantic failure feeds the error back as
    labelled-untrusted retry context (PLAN-0006 §6.4 / IN-2 corollary)
    for up to ``retry_budget`` total attempts.

    Raises :class:`StructuredOutputError` when the budget is exhausted.
    Transport failures surface as ``OllamaError`` from ``client.chat`` and
    are intentionally NOT retried here — they go straight to the Step 5
    fail-safe.
    """
    budget = max(1, retry_budget)
    reasoning = await client.chat(build_reasoning_messages(event, vertical), think=True)

    feedback: str | None = None
    last_error = "no attempt was made"
    for attempt in range(1, budget + 1):
        messages = build_structuring_messages(
            event, vertical, reasoning.content, retry_feedback=feedback
        )
        # call 2: omit `think` (CHECKPOINT-0 contract — never think=False + format)
        result = await client.chat(messages, response_format=_JUDGMENT_SCHEMA)
        judgment, error = _parse_and_check(result.content, vertical)
        if judgment is not None:
            return JudgmentResult(
                judgment=judgment,
                thinking=reasoning.thinking,
                draft=reasoning.content,
                model=result.model,
                attempts=attempt,
            )
        last_error = error
        feedback = error

    raise StructuredOutputError(f"structured output failed after {budget} attempt(s): {last_error}")


def _parse_and_check(content: str, vertical: str) -> tuple[LlmJudgment | None, str]:
    """Parse + schema-validate + semantically check one call-2 response.

    Returns ``(judgment, "")`` on success, or ``(None, error)`` where
    ``error`` is the retry-feedback string.
    """
    try:
        raw: Any = json.loads(content)
    except json.JSONDecodeError as exc:
        return None, f"output was not valid JSON: {exc}"

    try:
        judgment = LlmJudgment.model_validate(raw)
    except ValidationError as exc:
        return None, f"output did not satisfy the schema: {exc}"

    semantic = _semantic_errors(judgment, vertical)
    if semantic:
        return None, "; ".join(semantic)
    return judgment, ""


def _semantic_errors(judgment: LlmJudgment, vertical: str) -> list[str]:
    """Checks beyond schema validity (PLAN-0006 §6.4 — "syntax != semantics").

    ``confidence`` range is already enforced by the Pydantic model.
    """
    errors: list[str] = []

    try:
        registry.get_handler(vertical, judgment.suggested_handler)
    except RegistryError:
        errors.append(
            f"suggested_handler '{judgment.suggested_handler}' is not a "
            f"registered handler for vertical '{vertical}'"
        )

    for index, entity in enumerate(judgment.affected_entities):
        if not entity.primary_key.strip():
            errors.append(f"affected_entities[{index}].primary_key is empty")

    return errors
