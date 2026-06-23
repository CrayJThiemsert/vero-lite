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

SD-1 = (c) Hybrid (Cray-adjudicated, session 73), phased. THIS module is **Phase 1
= the deterministic floor (mechanism (a))**: it always runs, is fully offline, and
is the acceptance gate. **Phase 2** adds an ADVISORY local-LLM-judge cross-check
(gated on the ADR-0022 amendment) that **never overrides the surfaced action** —
the deterministic floor decides *which* action is surfaced; the judge only sets
confidence + trace. The ``verification_mode`` is therefore ``"(a)-only"`` in Phase 1
(the scaffold the Phase-2 hybrid/degradation disclosure plugs into).

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

from services.engine.actions import ReasoningStep
from services.engine.llm.structured import LlmJudgment
from services.engine.registry import registry

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
