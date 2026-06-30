"""Action-step adapter + the external gated-action gate driver
(ADR-016 D2/D3; PLAN-0019 Part A, Step A-ε / AC A-7).

The REAL ``action`` :class:`StepExecutor`. Per affected entity in the step's
input set it builds an **ADR-007 D2 ``RecommendedAction`` envelope** (the existing
``services/engine/actions.py`` class, UNCHANGED) — reasoning via the shipped
two-call LLM path (``generate_judgment``, mockable through the ``ChatClient``
Protocol) — wraps it in an ``ActionRecord`` and routes it through the **shipped**
``approve()`` -> ``execute()`` gate (``services/engine/recommender.py``)
**verbatim**. ``suggested_handler`` is the procedure author's declared
``step.handler`` (the allowlist-checked, deterministic blast-radius bound), not
the model's guess.

Gated-action lifecycle — **Option 2 (external gate), decided 2026-06-08**:

* On run, a ``gated`` action only **proposes** (each ``ActionRecord`` stays
  ``proposed``); the orchestrator suspends the run at ``waiting_human``. The real
  ``approve()`` -> ``execute()`` runs **later, via the EXTERNAL gate**
  (:func:`resolve_gated_step`, the same ``recommender`` functions the shipped
  action-loop router drives) — NOT inside the executor and NOT inside
  ``resume_run``, which stays a pure control-plane continuation.
* :func:`resolve_gated_step` reconstructs the proposals, applies the human's
  approve/reject decision per action (approve -> execute -> executed + receipt;
  **reject -> recorded but NOT executed**), **rewrites the suspended step's
  ``output_set`` to the executed effects**, appends the decisions to the step's
  reasoning trace, and persists — leaving the run ``waiting_human`` so a plain
  ``resume_run`` then threads the resolved output forward and continues.

**Reject = continue + record** (Phase-1 default, grounded in Palantir's
staged-Action model: Palantir has no run primitive, so a rejected proposal is a
local "not applied" disposition, not a run failure; a rejected action is recorded
in the trace and the run continues to its next step — the per-step
``on_reject: halt`` policy is a deferred future extension).

An ``auto`` action (no human gate) **approves + executes inline** and threads the
executed effects straight to the next step.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from services.api.config import settings
from services.engine.actions import ControlRef, EntityRef, GovernedDecision, RecommendedAction
from services.engine.llm.client import OllamaClient
from services.engine.llm.structured import ChatClient, JudgmentResult, generate_judgment
from services.engine.llm.trace import build_llm_audit_metadata, build_llm_reasoning_trace
from services.engine.procedures.orchestrator import (
    ProcedureError,
    RunContext,
    StepOutcome,
)
from services.engine.procedures.persistence import load_run
from services.engine.procedures.principal_sod import (
    PrincipalSoDVerdict,
    check_principal_sod,
)
from services.engine.procedures.runs import PipelineRun, StepResult, StepResultStatus
from services.engine.procedures.spec import (
    Autonomy,
    Person,
    PrincipalAlias,
    Procedure,
    Step,
)
from services.engine.recommender import (
    ActionRecord,
    approve,
    reject,
)
from services.engine.recommender import (
    execute as gate_execute,
)

APPROVE = "approve"
REJECT = "reject"


class PrincipalSoDError(ProcedureError):
    """A SoD-constrained gate failed the LIVE principal-SoD run-check (ADR-0026 D4;
    PLAN-0044 A1b Step 1) — the run is BLOCKED.

    Raising this aborts the gate resolution **before** any approve/execute runs: no
    handler fires, no PO is issued, no "governed" verdict is emitted — the fail-closed
    run enforcement that the structural author-time ``SoDConstraint`` could only assert
    over *steps*, not *humans* (the Alternative-5 collapse ADR-0025 rejected). It carries
    the structured :class:`PrincipalSoDVerdict` so a caller / read-only render can surface
    WHICH constraint + principals collapsed (the hero-demo governance moment, ask #1)."""

    def __init__(self, verdict: PrincipalSoDVerdict, *, run_id: str, step_id: str) -> None:
        self.verdict = verdict
        detail = "; ".join(v.detail for v in verdict.violations) or "no detail"
        super().__init__(
            f"run '{run_id}': step '{step_id}' BLOCKED by the principal-SoD run-check "
            f"({len(verdict.violations)} violation(s)): {detail}"
        )


ClientFactory = Callable[[str], ChatClient]
"""``llm_model`` name -> a ``ChatClient`` for that model. Injected so offline
tests pass a fake; the default builds the local Ollama client (ADR-001)."""


def _default_client_factory(model: str) -> ChatClient:
    """Build the local Ollama client bound to the running ``Agent``'s model.

    Per-``Agent`` model binding (ADR-016 OQ-1): the client's model comes from
    ``ctx.agent.llm_model`` (default ``gpt-oss:20b``, ADR-001), not the reactive
    loop's ``settings.recommender_model``.
    """
    return OllamaClient(
        base_url=settings.ollama_host,
        model=model,
        timeout=settings.llm_request_timeout_s,
    )


def _loop_entity_ref(event: Mapping[str, Any]) -> EntityRef:
    """The single, deterministically-scoped entity this action-step loop iteration
    is processing — sourced from the loop ``event``, NOT the model's
    ``affected_entities`` guess (which, under multi-entity input, over-names SAFE
    sibling entities — the PLAN-0019 Part B aquaculture over-naming finding). Mirrors
    the ``step.handler`` override: one envelope field sourced deterministically while
    the ADR-007 D2 ``RecommendedAction`` envelope CLASS stays unchanged.

    HEDGE (PLAN-0020 Phase 1, entity-key fork): assumes the event carries the
    faithful ontology-projected keys ``object_type`` + ``primary_key`` (the shape
    ``benchmarks/procedure_baseline/harness.scenario_to_event`` emits). The defensive
    ``.get(..., fallback)`` chain mirrors ``recommender._rule_recommend`` so a
    minimal/stub event degrades gracefully rather than raising. If the Tier-2
    real-data event standardises on different entity keys, revisit this getter.
    """
    return EntityRef(
        object_type=str(event.get("object_type", "unknown")),
        primary_key=str(event.get("primary_key", event.get("event_id", "unknown"))),
    )


def _compose_action(
    event: Mapping[str, Any],
    vertical: str,
    result: JudgmentResult,
    *,
    handler: str,
) -> RecommendedAction:
    """Compose the ADR-007 D2 envelope from an LLM judgment, mirroring
    ``recommender._compose_llm_record`` — EXCEPT two fields are sourced
    deterministically, not from the model's guess: ``suggested_handler`` is the
    procedure author's declared ``step.handler`` (allowlist-bounded), and
    ``affected_entities`` is the single loop ``event`` entity (PLAN-0020 Phase 1 —
    the model over-names safe sibling entities under multi-entity input; the executed
    handler already fires per-deterministic-entity, so this closes the envelope's
    over-naming metadata/UX leak). The model owns the remaining judgment fields; the
    harness owns id / vertical / created_at / audit + the hybrid trace.
    """
    judgment = result.judgment
    event_id = str(event.get("event_id", "unknown"))
    return RecommendedAction(
        id=f"action-{event_id}",
        title=judgment.title,
        description=judgment.description,
        vertical=vertical,
        reasoning_trace=build_llm_reasoning_trace(event, vertical, result),
        confidence=judgment.confidence,
        affected_entities=[_loop_entity_ref(event)],
        suggested_handler=handler,
        handler_payload=judgment.handler_payload,
        audit_metadata=build_llm_audit_metadata(result.model),
        created_at=datetime.now(UTC),
    )


def _entry(record: ActionRecord, receipt: dict[str, Any] | None) -> dict[str, Any]:
    """Serialise one ActionRecord + optional handler receipt for the step artifact
    (JSONB ``output_set``). ``action`` round-trips via ``RecommendedAction.model_validate``."""
    return {
        "action_id": record.action.id,
        "status": record.status.value,
        "action": record.action.model_dump(mode="json"),
        "receipt": receipt,
    }


@dataclass(frozen=True)
class ActionStepExecutor:
    """The real ``action`` StepExecutor (AC A-7). See module docstring."""

    client_factory: ClientFactory = _default_client_factory
    retry_budget: int = 3

    async def execute(self, step: Step, input_set: list[Any], ctx: RunContext) -> StepOutcome:
        """Build + route one RecommendedAction per entity in ``input_set``.

        ``auto`` actions are approved + executed inline; ``gated`` actions are
        only proposed (the orchestrator suspends; the human's approve/execute runs
        later via :func:`resolve_gated_step`).
        """
        if step.handler is None:
            raise ProcedureError(
                f"action step '{step.step_id}' has no handler — an action step must "
                "declare a registered handler to propose a RecommendedAction"
            )
        client = self.client_factory(ctx.agent.llm_model)
        auto = step.autonomy is Autonomy.AUTO
        output: list[Any] = []
        trace: list[dict[str, Any]] = []
        for entity in input_set:
            event = dict(entity) if isinstance(entity, Mapping) else {"value": entity}
            judgment = await generate_judgment(
                client, event, ctx.vertical, retry_budget=self.retry_budget, goal=ctx.goal
            )
            action = _compose_action(event, ctx.vertical, judgment, handler=step.handler)
            record = ActionRecord(action=action)
            if auto:
                approve(record)
                receipt = await gate_execute(record)
                output.append(_entry(record, receipt))
                trace.append(
                    {
                        "kind": "action_executed",
                        "action_id": action.id,
                        "summary": f"auto action: executed handler '{action.suggested_handler}'",
                    }
                )
            else:
                output.append(_entry(record, None))
                trace.append(
                    {
                        "kind": "action_proposed",
                        "action_id": action.id,
                        "summary": (
                            f"gated action: proposed handler '{action.suggested_handler}' "
                            "for human approval"
                        ),
                    }
                )
        audit = {
            "actor": ctx.agent.agent_id,
            "actor_kind": "engine",
            "autonomy": step.autonomy.value if step.autonomy is not None else None,
            "action_count": len(output),
        }
        return StepOutcome(output=output, reasoning_trace=trace, audit=audit)


def _enforce_principal_sod(
    run: PipelineRun,
    step_id: str,
    principal: Person | None,
    procedure: Procedure | None,
    principals: list[Person] | None,
    principal_aliases: list[PrincipalAlias] | None,
) -> None:
    """Run the LIVE fail-closed principal-SoD run-check for a gate resolution (ADR-0026
    D4; PLAN-0044 A1b Step 1). A no-op unless the run carried a SoD constraint AND this
    step is one of the constrained steps.

    ``run.step_principals is not None`` is the durable "this run carried SoD" signal the
    orchestrator persisted (the requester half). On such a run the check is NOT skippable:
    omitting ``procedure`` / ``principals`` raises rather than silently bypassing (AC-2).
    When this step is constrained it assembles the full ``step_principals`` (the persisted
    REQUESTER half + this gate's APPROVER from the ``principal`` arg — the typed Person
    seam, never ``trigger_context``, OQ-2) and invokes the pure check, raising
    :class:`PrincipalSoDError` (BLOCK — no approve/execute) on any violation.
    """
    sod_run = run.step_principals is not None
    if sod_run and (procedure is None or principals is None):
        raise ProcedureError(
            f"run '{run.run_id}': step '{step_id}' resolves a gate on a SoD-constrained run "
            "but no procedure/principals were supplied — the principal-SoD run-check cannot "
            "be skipped (ADR-0026 D4; PLAN-0044 A1b Step 1)"
        )
    if procedure is None or not any(
        step_id in sod.distinct_steps for sod in procedure.separation_of_duties
    ):
        return
    step_principals: dict[str, str | None] = {
        **(run.step_principals or {}),
        step_id: principal.person_id if principal is not None else None,
    }
    verdict = check_principal_sod(
        procedure,
        principals=principals or [],
        principal_aliases=principal_aliases or [],
        step_principals=step_principals,
    )
    if not verdict.governed:
        raise PrincipalSoDError(verdict, run_id=run.run_id, step_id=step_id)


def _sod_governed_decisions(
    step_id: str,
    principal: Person | None,
    procedure: Procedure | None,
) -> list[dict[str, Any]]:
    """The OQ-5 audit-to-control ties for a GOVERNED SoD gate (ADR-0026 D6; PLAN-0044 A1b Step 6,
    AC-8). Called only AFTER the live principal-SoD check passed (no violation): for each SoD
    constraint covering this step, tie the gate to its control (the stable ``constraint_id``, D2)
    + the approving principal's ``person_id``. Empty when the step is unconstrained or no
    principal was supplied (no resolved principal to name). Engine side-effect — typed, minimal,
    not free prose (it does not pre-empt the ADR-011 framework)."""
    if procedure is None or principal is None:
        return []
    return [
        GovernedDecision(
            control_ref=ControlRef(kind="sod", id=sod.constraint_id),
            principal_id=principal.person_id,
        ).model_dump(mode="json")
        for sod in procedure.separation_of_duties
        if step_id in sod.distinct_steps
    ]


def _record_governed_decision(
    target: StepResult,
    step_id: str,
    principal: Person | None,
    procedure: Procedure | None,
) -> None:
    """Record the OQ-5 SoD audit-to-control tie on a GOVERNED gate's resolved step (A1b Step 6,
    AC-8) — merged into the step audit, never overwriting it. A no-op for a non-SoD / principal-
    less gate (nothing to tie)."""
    governed = _sod_governed_decisions(step_id, principal, procedure)
    if governed:
        target.audit = {**(target.audit or {}), "governed_decision": governed}


async def resolve_gated_step(
    session: AsyncSession,
    run_id: str,
    step_id: str,
    decisions: Mapping[str, str],
    principal: Person | None = None,
    *,
    procedure: Procedure | None = None,
    principals: list[Person] | None = None,
    principal_aliases: list[PrincipalAlias] | None = None,
) -> StepResult:
    """Apply a human's approve/reject decisions to a suspended gated action
    (Option 2 — the EXTERNAL gate driver; the shipped ``recommender`` gate,
    verbatim).

    ``principal`` is the resolved HUMAN who approved THIS gate (ADR-0026 D3, OQ-2
    — the *load-bearing* identity, beside the ambient ``RunContext.principal``).
    It is the typed seam the principal-SoD run-check resolves against, and when
    supplied it is recorded on the step's reasoning trace (the approving-principal
    record).

    **The LIVE fail-closed principal-SoD run-check (ADR-0026 D4; PLAN-0044 A1b
    Step 1).** When the run carried a separation-of-duties constraint (the orchestrator
    recorded a ``step_principals`` map on the run) and this step is one of the
    constrained steps, the gate assembles the full ``step_principals`` (the persisted
    REQUESTER half + this step's APPROVER from the ``principal`` arg) and invokes
    :func:`~services.engine.procedures.principal_sod.check_principal_sod`
    **unconditionally**, **failing CLOSED** — raising :class:`PrincipalSoDError`
    BEFORE any approve/execute, so no handler fires and no governed verdict is emitted —
    on any violation (an unresolvable/missing principal, a role mismatch, or two
    constrained steps collapsing to one human). It is **not skippable**: on a run that
    recorded ``step_principals``, omitting ``procedure`` / ``principals`` raises rather
    than silently bypassing the check. ``procedure`` + ``principals`` + ``principal_aliases``
    are the resolution context (the procedure's SoD constraints + the vertical's authored
    ``Person`` set + declared alias groups); the caller supplies them (consistent with
    :func:`resume_run`). A run with no SoD constraint leaves them unused (the check is
    inert), keeping every non-SoD caller unchanged.

    ``decisions`` maps each proposed ``action_id`` to ``"approve"`` or
    ``"reject"`` (every proposal needs an explicit decision — no silent default on
    a consequential write). For each proposal it reconstructs the ``ActionRecord``
    from the persisted artifact and:

    * ``approve`` -> ``approve()`` + ``execute()`` (the handler runs) -> the
      executed effect (with receipt) joins the rewritten ``output_set``;
    * ``reject`` -> ``reject()`` (the handler does NOT run) -> recorded in
      ``decisions`` + the step trace, but NOT threaded forward (reject = continue
      + record).

    Rewrites the suspended step's ``output_set`` to the executed effects, appends
    the per-action decisions to its reasoning trace, and persists — leaving the
    run ``waiting_human`` so a subsequent :func:`resume_run` threads the resolved
    output forward and continues. Returns the updated ``StepResult``.

    Raises :class:`ProcedureError` if the run/step is absent, the step is not
    awaiting a human decision, it carries no proposals, a proposal has no (or an
    unknown) decision, or a SoD-constrained run is resolved without the procedure /
    principals context (non-skippable). Raises :class:`PrincipalSoDError` when the
    live SoD run-check fails closed (the structured verdict is on the exception).
    """
    loaded = await load_run(session, run_id)
    if loaded is None:
        raise ProcedureError(f"run '{run_id}' not found")
    target = next((s for s in loaded.step_results if s.step_id == step_id), None)
    if target is None:
        raise ProcedureError(f"run '{run_id}': step '{step_id}' is not in the run")
    if target.status != StepResultStatus.WAITING_HUMAN.value:
        raise ProcedureError(
            f"run '{run_id}': step '{step_id}' is not awaiting a human decision "
            f"(status '{target.status}', expected waiting_human)"
        )
    proposals: list[dict[str, Any]] = (target.artifact or {}).get("output_set", [])
    if not proposals:
        raise ProcedureError(f"run '{run_id}': step '{step_id}' has no proposed actions to resolve")

    # The LIVE fail-closed principal-SoD run-check (ADR-0026 D4; A1b Step 1) — runs
    # BEFORE any approve/execute so a violation blocks the gate (no PO, no governed
    # verdict). Non-skippable on a SoD run; inert otherwise (see the helper).
    _enforce_principal_sod(loaded.run, step_id, principal, procedure, principals, principal_aliases)

    executed_effects: list[dict[str, Any]] = []
    decided: list[dict[str, Any]] = []
    trace_adds: list[dict[str, Any]] = []
    for proposal in proposals:
        action = RecommendedAction.model_validate(proposal["action"])
        decision = decisions.get(action.id)
        if decision is None:
            raise ProcedureError(
                f"run '{run_id}': no decision for proposed action '{action.id}' "
                "(every gated action needs an explicit approve/reject)"
            )
        record = ActionRecord(action=action)
        if decision == APPROVE:
            approve(record)
            receipt = await gate_execute(record)
            effect = _entry(record, receipt)
            executed_effects.append(effect)
            decided.append(effect)
            trace_adds.append(
                {
                    "kind": "action_executed",
                    "action_id": action.id,
                    "summary": f"human-approved; executed handler '{action.suggested_handler}'",
                }
            )
        elif decision == REJECT:
            reject(record)
            decided.append(_entry(record, None))
            trace_adds.append(
                {
                    "kind": "action_rejected",
                    "action_id": action.id,
                    "summary": (
                        f"human-rejected handler '{action.suggested_handler}'; not executed "
                        "(run continues — a reject is a recorded decision, not a failure)"
                    ),
                }
            )
        else:
            raise ProcedureError(
                f"run '{run_id}': unknown decision '{decision}' for action '{action.id}' "
                "(expected 'approve' or 'reject')"
            )

    if principal is not None:
        trace_adds.append(
            {
                "kind": "gate_principal_recorded",
                "principal_id": principal.person_id,
                "summary": (
                    f"gate resolved by principal '{principal.person_id}' — the approving human "
                    "recorded for the principal-SoD run-check (ADR-0026 D3, OQ-2)"
                ),
            }
        )
    # The OQ-5 audit-to-control side-effect (A1b Step 6, AC-8): the live SoD check governed this
    # gate (it did not raise above), so tie the gate to its SoD control + the approving principal.
    # Engine-emitted — recorded whether the human approved or rejected the proposals (it records
    # WHO governed the gate, not the per-action outcome). Inert for a non-SoD / principal-less gate.
    _record_governed_decision(target, step_id, principal, procedure)
    target.artifact = {"output_set": executed_effects, "decisions": decided}
    target.reasoning_trace = list(target.reasoning_trace or []) + trace_adds
    await session.merge(target)
    await session.commit()
    return target
