"""Governed action verify+reshape — the deterministic floor (ADR-0022 member (b), PLAN-0035).

PLAN-0035. Before the governed ``RecommendedAction`` (ADR-007 D2) trusts the
model's **prose** to express the corrective action, verify that the proposal's
prose expresses the action named by the model's own structured
``suggested_handler`` (the enum-bound declared contract, ``llm/structured.py:111-125``).
On an inconsistency the governed record authoritatively carries the action
**surfaced from the structured handler** (never fabricated) via an
``action_verification`` ``ReasoningStep``, so a downstream consumer trusts the
**structured action, not model prose**. It is the same "classify, don't synthesize"
move member (a) made for entity *identity* (ADR-0021 lineage), applied to the
action *expression*.

SD-1 = (c) Hybrid (Cray-adjudicated, session 73), phased; the ADR-0022 amendment
is RATIFIED (2026-06-23), so **both** phases live here now:

* **Phase 1 — the deterministic floor (mechanism (a))** — :func:`verify_action_expression`.
  It always runs, is fully offline, and IS the acceptance gate (constraint ①). The
  ``verification_mode`` it stamps is ``"(a)-only"``.
* **Phase 2 — the ADVISORY local-LLM-judge** — :func:`augment_with_advisory_judge`
  (+ :func:`judge_action_expression`). A semantic cross-check that *adds confidence +
  a trace* and **NEVER overrides the surfaced action** (constraint ②): the floor decides
  *which* action is surfaced; the judge cannot rescue/flip it. The floor↔judge
  agreement is computed **deterministically** — no 3rd LLM (constraint ③). When the
  judge is unavailable the engine runs in ``"(a)-only"`` mode, **disclosed** in the
  trace, reusing the IN-4 / ``OllamaUnreachableError`` degradation seam (constraint ④).
  The judge is advisory, so its failure is **caught here and never harms the
  load-bearing floor result**; only the floor's errors propagate to ``recommend()``'s
  IN-4 fail-safe (AC-7). The live judge runs on the **MS-S1 local Ollama** (ADR-002 pin)
  and is gated behind ``settings.verification_judge_enabled`` (default off — a live run
  is Cray-gated host-state, CLAUDE.md §8); the offline gate **fakes the judge** (the
  ``tests/services/engine/`` fake-``ChatClient`` pattern).

The floor is a **conservative literal check**: derive the action's head token from
the (snake_case) handler name — the ontology ``RecommendedAction.action_type``
vocabulary, e.g. ``start_emergency_aerator`` -> ``aerator`` — and check the prose
expresses it. Morphological / synonym / paraphrase variants are Phase-2's LLM-judge
job, NOT the floor's; a floor false-negative only emits a redundant (harmless)
reshape, because the surfaced action always comes from the structured handler and is
**never invented** (the PDPA-forward anti-hallucination invariant, CLAUDE.md §8).

Scope: the reactive recommend LLM path (``recommender._compose_llm_record``) only.
The procedure-engine step-to-step seam is forward-declared, NOT built here (SD-2).

D-6 (PLAN-0027 / PLAN-0028, BINDING). Product-path-only governance: this module
does **not** import, and must not be imported by, the benchmark grader
(``benchmarks/``) — asserted by a test — so the arm-(c) naive-RAG baseline stays a
clean, ungoverned control.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from services.engine.actions import ReasoningStep
from services.engine.llm.client import OllamaError, OllamaUnreachableError
from services.engine.llm.prompt import render_untrusted_block
from services.engine.llm.structured import ChatClient, LlmJudgment
from services.engine.registry import registry

logger = logging.getLogger(__name__)

VERIFICATION_MODE_DETERMINISTIC = "(a)-only"
"""Phase-1 ``verification_mode``: only the deterministic floor ran (no LLM-judge).
Phase 2 sets ``"hybrid"`` when the advisory judge concurs, or falls back to this
value with a disclosure when the judge is unavailable (the IN-4 / ``OllamaUnreachable``
degradation path)."""

_NO_OP_HANDLER = "echo"
"""The no-op round-summary terminal (``verticals/*/handlers.py``) — not an
operational corrective action, so verification is skipped for it."""

_MIN_TOKEN_LEN = 3
"""Drop connector tokens shorter than this when deriving the action vocabulary."""


def _action_tokens(handler: str) -> list[str]:
    """The distinctive (snake_case) tokens of a handler's action_type, casefolded.

    ``start_emergency_aerator`` -> ``["start", "emergency", "aerator"]``. Recorded in
    the trace detail for auditability. Recover-only: derived from the declared handler
    name, never invented.
    """
    return [tok for tok in handler.casefold().split("_") if len(tok) >= _MIN_TOKEN_LEN]


def _action_head_token(handler: str) -> str | None:
    """The most-identifying token of the action_type — the head of the snake_case
    name (``start_emergency_aerator`` -> ``aerator``; ``escalate`` -> ``escalate``).

    Returns ``None`` for a handler with no usable token (defensive; the caller then
    skips rather than reshape what it cannot ground).
    """
    tokens = _action_tokens(handler)
    return tokens[-1] if tokens else None


def _proposal_prose(judgment: LlmJudgment) -> str:
    """The model-authored prose the corrective action could be expressed in
    (title + description + rationale), casefolded for a literal match. The structured
    ``suggested_handler`` is the declared contract; the prose is what may omit it."""
    return "\n".join((judgment.title, judgment.description, judgment.rationale)).casefold()


def _verification_step(
    handler: str,
    *,
    outcome: str,
    summary: str,
    detail_extra: dict[str, object] | None = None,
) -> ReasoningStep:
    """A minimal, machine-readable action-verification trace step (SD-3: trace-only
    in Phase 1 — the ADR-007 D2 ``RecommendedAction`` envelope is left untouched;
    ``AuditMetadata`` is NOT designed here, D-3 / ADR-011)."""
    detail: dict[str, object] = {
        "suggested_handler": handler,
        "outcome": outcome,
        "verification_mode": VERIFICATION_MODE_DETERMINISTIC,
    }
    if detail_extra is not None:
        detail.update(detail_extra)
    return ReasoningStep(
        step_id="action-verification-0",
        kind="action_verification",
        summary=summary,
        detail=detail,
    )


def verify_action_expression(judgment: LlmJudgment, vertical: str) -> list[ReasoningStep]:
    """Verify the proposal prose expresses the action its structured handler names;
    on an inconsistency, reshape (authoritatively surface the structured action) + trace.

    Returns a single-element ``[ReasoningStep(kind="action_verification")]`` recording the
    outcome (``"consistent"`` | ``"reshaped"`` | ``"skipped"``). The action is **always**
    the model's own ``suggested_handler`` — member (b) verifies/reshapes the *expression*
    of the action, it does **not** change *which* action the model selected (AC-5: a wrong
    handler stays wrong; member (b) is not an action-selection improver).

    * ``echo`` / empty / a handler not registered for the vertical -> **skipped** (no
      operational action to ground; never fabricate).
    * prose expresses the handler's action -> **consistent** (no reshape; trace only).
    * prose omits it -> **reshaped**: the governed record authoritatively carries the
      action surfaced from the structured handler (the 5 §B-3 prose-omission cases).

    Deterministic and offline (Phase 1 floor). Any error propagates to ``recommend()``'s
    fail-safe (ADR-010 IN-4) — it is not swallowed here.
    """
    handler = judgment.suggested_handler.strip()
    if not handler or handler == _NO_OP_HANDLER:
        reason = "no-op terminal handler" if handler == _NO_OP_HANDLER else "empty handler"
        return [
            _verification_step(
                handler,
                outcome="skipped",
                summary=f"Action verification skipped: {reason} (no operational action to verify).",
                detail_extra={"reason": reason},
            )
        ]
    if handler not in registry.handler_names(vertical):
        return [
            _verification_step(
                handler,
                outcome="skipped",
                summary=(
                    f"Action verification skipped: handler '{handler}' is not registered for "
                    f"vertical '{vertical}' (cannot ground the action; never fabricate)."
                ),
                detail_extra={"reason": "handler not registered for the vertical"},
            )
        ]

    head = _action_head_token(handler)
    prose = _proposal_prose(judgment)
    if head is not None and head in prose:
        return [
            _verification_step(
                handler,
                outcome="consistent",
                summary=(
                    f"Proposal prose expresses the corrective action '{handler}' named by the "
                    f"structured handler (consistent)."
                ),
                detail_extra={"matched_token": head},
            )
        ]
    return [
        _verification_step(
            handler,
            outcome="reshaped",
            summary=(
                f"Proposal prose did not express the corrective action '{handler}' named by the "
                f"structured handler; reshaped the governed record to authoritatively carry "
                f"'{handler}' (surfaced from the structured handler, not fabricated)."
            ),
            detail_extra={
                "surfaced_action": handler,
                "expected_action_tokens": _action_tokens(handler),
            },
        )
    ]


# --- Phase 2: the advisory local-LLM-judge (ADR-0022 amendment, RATIFIED 2026-06-23) ---

VERIFICATION_MODE_HYBRID = "hybrid"
"""Phase-2 ``verification_mode``: the advisory local-LLM-judge ran alongside the
deterministic floor. The floor still decides the surfaced action (constraint ②); the
judge contributes a confidence + agreement signal only — it never overrides."""


class ActionJudgeError(RuntimeError):
    """The advisory judge ran but produced no usable verdict (bad JSON / failed schema).

    Caught by :func:`augment_with_advisory_judge`, which then degrades gracefully to
    ``"(a)-only"`` mode; it never propagates into ``recommend()`` (the judge is advisory
    and must not harm the load-bearing floor result — constraint ②)."""


class ActionJudgeVerdict(BaseModel):
    """The advisory judge's semantic-equivalence verdict — the reduced sub-schema handed
    to Ollama ``format``. It judges EXPRESSION only: never whether the action is correct,
    and never which action is surfaced (constraint ②)."""

    expresses_action: bool = Field(
        ...,
        description="Does the proposal prose semantically express the named corrective action?",
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="The judge's confidence in [0,1] — advisory only"
    )
    rationale: str = Field(
        ..., min_length=1, description="One-sentence justification of the verdict"
    )


@dataclass(frozen=True)
class JudgeResult:
    """A parsed advisory verdict plus the model that produced it (recorded in the trace)."""

    verdict: ActionJudgeVerdict
    model: str


def _build_judge_messages(judgment: LlmJudgment, handler: str) -> list[dict[str, str]]:
    """Build the focused semantic-equivalence chat for the advisory judge.

    ``handler`` is a trusted, enum-bound internal identifier (a registered handler name),
    so it is safe inside the system instruction — exactly as ``vertical`` is in
    ``prompt.build_system_instruction``. The model-authored prose is wrapped in the
    delimiter-forgery-proof UNTRUSTED block (``prompt.render_untrusted_block``) because it
    may carry text that originated from operator-supplied event data.
    """
    system = (
        "You are a verification judge for an operational control tower. You are given a "
        "recommended-action proposal's prose and the name of the corrective action its "
        "structured handler already selected. Decide ONLY whether the prose semantically "
        "EXPRESSES that corrective action — i.e. a human reading the prose would understand "
        f"that '{handler}' (or an equivalent phrasing) is what to do. You judge EXPRESSION "
        "only: you do NOT decide whether the action is correct, and you NEVER change it. "
        "Respond with a single JSON object conforming to the provided schema."
    )
    prose = render_untrusted_block(
        "recommendation prose",
        f"title: {judgment.title}\ndescription: {judgment.description}\n"
        f"rationale: {judgment.rationale}",
    )
    user = (
        f"Corrective action named by the structured handler: '{handler}'.\n\n"
        f"{prose}\n\n"
        "Does the prose above express this corrective action? Output only the JSON verdict."
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


async def judge_action_expression(
    judgment: LlmJudgment, handler: str, *, judge_client: ChatClient
) -> JudgeResult:
    """Run the ADVISORY local-LLM-judge: does the prose express the action ``handler`` names?

    One constrained (``response_format``) chat call against the injected ``judge_client``
    (the MS-S1 ``OllamaClient`` in production; a fake in offline tests). Per the
    CHECKPOINT-0 caller contract, ``think`` is OMITTED (never ``think=False`` + ``format``).
    Transport failures surface as ``OllamaError`` / ``OllamaUnreachableError`` from
    ``judge_client.chat``; a parse / schema failure raises :class:`ActionJudgeError`. The
    caller (:func:`augment_with_advisory_judge`) catches all of these and degrades gracefully.
    """
    schema = ActionJudgeVerdict.model_json_schema()
    result = await judge_client.chat(
        _build_judge_messages(judgment, handler), response_format=schema
    )
    try:
        raw: Any = json.loads(result.content)
        verdict = ActionJudgeVerdict.model_validate(raw)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ActionJudgeError(f"advisory judge verdict was not usable: {exc}") from exc
    return JudgeResult(verdict=verdict, model=result.model)


def _floor_says_expressed(floor_outcome: object) -> bool:
    """Map the floor's outcome to its prose-expresses-the-action verdict, for the
    deterministic agreement: ``consistent`` -> prose expresses it; ``reshaped`` -> prose
    omits it (so the floor reshaped)."""
    return floor_outcome == "consistent"


def _hybrid_step(
    floor_step: ReasoningStep, floor_detail: dict[str, Any], judge: JudgeResult
) -> ReasoningStep:
    """Augment the floor's trace step with the advisory verdict + the DETERMINISTIC
    floor↔judge agreement (constraint ③). The floor's ``outcome`` and the surfaced action
    are LEFT UNCHANGED — the judge never overrides them (constraint ②); it only flips
    ``verification_mode`` to ``"hybrid"`` and records a confidence signal."""
    agree = _floor_says_expressed(floor_detail.get("outcome")) == judge.verdict.expresses_action
    detail: dict[str, Any] = {
        **floor_detail,
        "verification_mode": VERIFICATION_MODE_HYBRID,
        "judge": {
            "model": judge.model,
            "expresses_action": judge.verdict.expresses_action,
            "confidence": judge.verdict.confidence,
            "rationale": judge.verdict.rationale,
        },
        "judge_agreement": agree,
        "confidence_signal": "high" if agree else "low",
    }
    note = (
        f" Advisory judge {'agreed' if agree else 'disagreed'} "
        f"(confidence {detail['confidence_signal']}); the surfaced action is unchanged."
    )
    return floor_step.model_copy(update={"detail": detail, "summary": floor_step.summary + note})


def _degraded_step(
    floor_step: ReasoningStep, floor_detail: dict[str, Any], *, status: str, error: str
) -> ReasoningStep:
    """Disclose advisory-judge degradation in the trace, keeping ``verification_mode`` at
    ``"(a)-only"`` (constraint ④ — disclosed, not silent). The floor's outcome + surfaced
    action stand; the judge contributed nothing this run."""
    detail: dict[str, Any] = {
        **floor_detail,
        "verification_mode": VERIFICATION_MODE_DETERMINISTIC,
        "judge_status": status,
        "judge_disclosure": f"advisory judge {status}; ran in (a)-only mode: {error}"[:300],
    }
    note = f" Advisory judge {status}; ran in (a)-only mode (disclosed)."
    return floor_step.model_copy(update={"detail": detail, "summary": floor_step.summary + note})


async def _notify_unreachable_best_effort() -> None:
    """Reuse the IN-4 ``OllamaUnreachableError`` notification (PLAN-0014) when the advisory
    judge finds MS-S1 unreachable. Best-effort — never raises (the advisory path must not
    harm the floor result)."""
    try:
        from services.notify.telegram import notify_llm_unreachable

        await notify_llm_unreachable()
    except Exception:  # pragma: no cover - notify is itself best-effort / never-raises
        logger.debug("notify_llm_unreachable failed (best-effort)", exc_info=True)


async def augment_with_advisory_judge(
    floor_steps: list[ReasoningStep],
    judgment: LlmJudgment,
    *,
    judge_client: ChatClient | None,
) -> list[ReasoningStep]:
    """Phase 2: layer the ADVISORY local-LLM-judge on top of the deterministic floor.

    The judge is ADVISORY (constraint ②) — it NEVER changes the floor's ``outcome`` or the
    surfaced action; it only adds confidence + a DETERMINISTIC agreement signal (constraint
    ③) and flips ``verification_mode`` to ``"hybrid"``. The judge is skipped when:

    * ``judge_client is None`` (the ``verification_judge_enabled`` lever is off, or no client
      was supplied) -> the floor's ``"(a)-only"`` steps are returned byte-unchanged; or
    * the floor ``"skipped"`` (echo / unregistered handler) -> nothing to semantically judge.

    On judge unavailability the engine runs in ``"(a)-only"`` mode, **disclosed** in the
    trace (constraint ④), reusing the ``OllamaUnreachableError`` seam. This function
    **never raises** — an advisory component must not break the load-bearing floor result;
    only the floor (run by the caller, before this) propagates errors to the ``recommend()``
    IN-4 fail-safe (AC-7).
    """
    if judge_client is None:
        return floor_steps
    floor_step = floor_steps[0]
    floor_detail = floor_step.detail or {}
    if floor_detail.get("outcome") == "skipped":
        return floor_steps
    handler = str(floor_detail.get("suggested_handler", "")).strip()
    try:
        judge = await judge_action_expression(judgment, handler, judge_client=judge_client)
    except OllamaUnreachableError as exc:
        await _notify_unreachable_best_effort()
        return [_degraded_step(floor_step, floor_detail, status="unreachable", error=str(exc))]
    except (OllamaError, ActionJudgeError) as exc:
        return [_degraded_step(floor_step, floor_detail, status="error", error=str(exc))]
    except Exception as exc:  # advisory must never harm the floor result (constraint ②)
        logger.warning(
            "advisory action-verification judge raised unexpectedly; degrading to (a)-only: %s",
            exc,
            exc_info=True,
        )
        return [_degraded_step(floor_step, floor_detail, status="error", error=str(exc))]
    return [_hybrid_step(floor_step, floor_detail, judge)]
