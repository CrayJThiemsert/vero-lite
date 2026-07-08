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
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field, ValidationError

from services.engine.actions import EntityRef
from services.engine.llm.client import ChatResult
from services.engine.llm.prompt import build_reasoning_messages, build_structuring_messages
from services.engine.registry import RegistryError, registry

ReasoningMode = Literal["full", "think_off", "skip"]
"""PLAN-0020 think-trim lever (AC-1a) — controls the call-1 reasoning pass, the
dominant per-call latency cost.

* ``full`` — the shipped two-call path: call 1 reasons (``think=True``), call 2
  structures from that draft. **Default — byte-identical to the shipped behaviour.**
* ``think_off`` — keeps the two-call shape but call 1 runs with ``think=False``
  (a plain draft, no extended reasoning trace). Moderate latency cut. (Call 1 has
  no ``format``, so the Ollama #15260 ``think=False``+``format`` hazard does not
  apply here — only call 2 carries ``format``, and it never sets ``think``.)
* ``skip`` — omits call 1 entirely; call 2 structures from the event alone
  (single call). Largest latency cut, largest accuracy risk.

The accuracy/latency deltas per mode are measured on the procedure path under
PLAN-0020 R2 (host-state); this lever only makes the pass selectable. The
reactive and procedure product paths pass ``full`` (unchanged)."""


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


def _judgment_schema(handler_names: list[str]) -> dict[str, Any]:
    """Build the JSON Schema handed to Ollama ``format``.

    When the vertical has registered handlers, ``suggested_handler`` is
    constrained to that enum, so constrained generation cannot emit an
    unresolvable handler. A PLAN-0006 Step-7 live capture confirmed that a
    free-string handler field lets the model invent plausible-but-wrong
    handler names (e.g. ``"operator"``); the enum closes that. The
    semantic check in ``_parse_and_check`` remains the backstop (and the
    only guard when no handler is registered yet).
    """
    schema: dict[str, Any] = LlmJudgment.model_json_schema()
    if handler_names:
        schema["properties"]["suggested_handler"]["enum"] = list(handler_names)
    return schema


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
    goal: str | None = None,
    reasoning_mode: ReasoningMode = "full",
    include_handler_catalog: bool = False,
) -> JudgmentResult:
    """Run the Pattern B exchange and return a validated judgment.

    Call 1 reasons (``think=True``); call 2 emits the constrained envelope
    against the :class:`LlmJudgment` schema, with ``suggested_handler``
    enum-constrained to the vertical's registered handlers. Per the
    CHECKPOINT-0 contract, call 2 OMITS ``think`` (never ``think=False``
    with ``format`` — Ollama #15260). A parse / schema / semantic failure
    feeds the error back as
    labelled-untrusted retry context (PLAN-0006 §6.4 / IN-2 corollary)
    for up to ``retry_budget`` total attempts.

    ``goal`` (ADR-016 D5; PLAN-0019 A-8) is the running ``Procedure``'s trusted
    directive, threaded into the system instruction of BOTH calls; it is ``None``
    on the reactive Pipeline-v0 path (system prompt unchanged).

    ``reasoning_mode`` (PLAN-0020 AC-1a think-trim lever, default ``"full"``)
    selects the call-1 reasoning pass: ``full`` = call 1 ``think=True`` (shipped);
    ``think_off`` = call 1 ``think=False``; ``skip`` = no call 1 (call 2 structures
    from the event alone). On ``skip`` the returned ``draft`` is ``""`` and
    ``thinking`` is ``None`` (no reasoning output existed). See :data:`ReasoningMode`.

    ``include_handler_catalog`` (PLAN-0060, default ``False``) fetches the vertical's
    ``registry.handler_catalog`` and threads it into the trusted system instruction of
    every call (both Pattern-B calls and the ``skip`` single call, via the
    ``build_structuring_messages`` → ``build_reasoning_messages`` composition) so the
    model distinguishes handlers by description, not bare name. ``False`` → the prompt
    is byte-identical to before; the ``suggested_handler`` enum is unchanged either way.

    Raises :class:`StructuredOutputError` when the budget is exhausted.
    Transport failures surface as ``OllamaError`` from ``client.chat`` and
    are intentionally NOT retried here — they go straight to the Step 5
    fail-safe.
    """
    budget = max(1, retry_budget)
    schema = _judgment_schema(registry.handler_names(vertical))
    # PLAN-0060: the "Available actions" catalog rides beside the enum fetch; None
    # (flag off) leaves every prompt builder byte-identical to before.
    catalog = registry.handler_catalog(vertical) if include_handler_catalog else None

    # PLAN-0020 think-trim lever: `skip` omits call 1; `full`/`think_off` run it
    # with think on/off. `draft`/`thinking` feed the hybrid trace (empty on skip).
    draft: str | None
    thinking: str | None
    if reasoning_mode == "skip":
        draft = None
        thinking = None
    else:
        reasoning = await client.chat(
            build_reasoning_messages(event, vertical, goal, catalog),
            think=(reasoning_mode == "full"),
        )
        draft = reasoning.content
        thinking = reasoning.thinking

    feedback: str | None = None
    last_error = "no attempt was made"
    for attempt in range(1, budget + 1):
        messages = build_structuring_messages(
            event, vertical, draft, retry_feedback=feedback, goal=goal, catalog=catalog
        )
        # call 2: omit `think` (CHECKPOINT-0 contract — never think=False + format)
        result = await client.chat(messages, response_format=schema)
        judgment, error = _parse_and_check(result.content, vertical)
        if judgment is not None:
            return JudgmentResult(
                judgment=judgment,
                thinking=thinking,
                draft=draft if draft is not None else "",
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
