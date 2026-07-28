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
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from services.api.config import settings
from services.db.audit_log import append_audit
from services.engine.actions import (
    ControlRef,
    EntityRef,
    GovernedDecision,
    ReasoningStep,
    RecommendedAction,
)
from services.engine.economic_impact import build_economic_steps
from services.engine.llm.client import OllamaClient
from services.engine.llm.structured import ChatClient, JudgmentResult, generate_judgment
from services.engine.llm.trace import build_llm_audit_metadata, build_llm_reasoning_trace
from services.engine.procedures.orchestrator import (
    ProcedureError,
    RunContext,
    StepOutcome,
)
from services.engine.procedures.persistence import assert_governance_pin, load_run
from services.engine.procedures.principal_sod import (
    PrincipalSoDVerdict,
    check_principal_sod,
)
from services.engine.procedures.ratification import (
    RATIFICATION_KEY,
    due_at_from,
    ratification_state,
)
from services.engine.procedures.runs import PipelineRun, StepResult, StepResultStatus
from services.engine.procedures.spec import (
    Autonomy,
    DoaLadder,
    EmergencyWaiverPolicy,
    Person,
    PrincipalAlias,
    Procedure,
    Step,
)
from services.engine.procedures.tier_authority import (
    TierAuthorityVerdict,
    check_tier_authority,
    native_approver,
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


class GateApproverError(ProcedureError):
    """A gated step's resolve was attempted with NO identified human approver (ADR-016 S2 RF-1,
    PLAN-0053 AC-1) — BLOCKED. The LIBRARY-level fail-closed guard behind the HTTP RF-1 403: a
    gate resolution is a consequential approval point, so an unidentified approver is refused
    independent of ``settings.api_auth_enabled`` and of any SoD constraint (the SoD run-check is
    inert on a non-SoD step). A service actor cannot reach this seam by construction (``principal``
    is ``Person | None``; RF-3)."""


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


class TierAuthorityError(ProcedureError):
    """A gated AT-2 authority step failed the LIVE tier-authority run-check (ADR-0026 D4 (iv);
    PLAN-0075) — the run is BLOCKED.

    Raising this aborts the gate resolution **before** any approve/execute runs: the acting
    approver did not hold the ladder-resolved tier role of one or more persisted authority
    verdicts (a lower-tier approver cannot resolve a gate routed to a higher tier), or the step
    declared authority content but persisted no verdict (the plain-executor bypass), or the actor
    is undeclared. ADDITIVE beside :class:`PrincipalSoDError` (LOCKED #2 — the SoD check runs
    first and is never weakened). Carries the structured :class:`TierAuthorityVerdict` so a caller
    / read-only render can surface WHICH tier role the approver lacked."""

    def __init__(self, verdict: TierAuthorityVerdict, *, run_id: str, step_id: str) -> None:
        self.verdict = verdict
        detail = "; ".join(v.detail for v in verdict.violations) or "no detail"
        super().__init__(
            f"run '{run_id}': step '{step_id}' BLOCKED by the tier-authority run-check "
            f"({len(verdict.violations)} violation(s)): {detail}"
        )


class RatificationError(ProcedureError):
    """A deferred-ratification path failed CLOSED (ADR-0034 D3; PLAN-0096 Step 5).

    Raised when a provisional (decide-first) resolution is attempted where the ADR does not
    make one representable — a gate with no authored ``ratification_window_days``, a
    non-waiver gate, an empty run-time justification, or an ``escalate_to`` authority that
    resolves to nobody — and when a ratification is attempted against a step that carries no
    outstanding obligation (never provisional, or already ratified / refused).

    Failing closed here is the point: every one of those cases is a request to record a
    decision the record cannot honestly stand behind, and the alternative to refusing is a
    trail that names an authority who did not act (PLAN-0075 SD-6(a))."""


@dataclass(frozen=True)
class WaiverInvocation:
    """The caller's EXPLICIT invocation of an authored emergency waiver (ADR-0034 D3(2)).

    Its presence is the second half of the provisional path's entry condition — the first
    being an authored ``ratification_window_days``. Both are required, and neither is
    inferred: a gate is never silently resolved provisionally because it *could* be. The
    ordinary path stays byte-identical for every caller that does not pass one of these
    (the only-when-supplied principle applied to behaviour, ADR-0034 D3(2)).

    ``justification`` is the run-time logged reason the waiver already forces
    (``requires_justification`` is ``Literal[True]``) — the roadside "ทำไมถึงเคาะไปก่อน".
    It is stored in the durable audit chain, and the ratification block points at that row
    by its tamper-evident ``row_hash``, so the obligation and its stated reason cannot drift
    apart.
    """

    justification: str

    def __post_init__(self) -> None:
        if not self.justification.strip():
            raise RatificationError(
                "a waiver invocation requires a non-empty run-time justification — the "
                "authored waiver forces one (requires_justification is Literal[True], "
                "ADR-0025 D3); recording a decide-first resolution with no stated reason "
                "would defeat the only control the partner actually relies on (ADR-0034 D3)"
            )


RatificationDecision = Literal["ratify", "refuse"]
"""What the ``ratify_by_role`` authority did when the record caught up with the decision.

Both are TERMINAL human acts and both are honest outcomes — a refusal is not an error path.
Nothing un-executes on a refusal (the money is spent); it becomes a named, exported exception
(ADR-0034 D3(4) — fail-VISIBLE, because fail-closed is impossible after the fact)."""


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
    economic_steps: list[ReasoningStep],
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
    ``economic_steps`` is the advisory, trace-carried Box-4 economic-impact facet
    (ADR-0030 / PLAN-0071), appended LAST — it never changes the action.
    """
    judgment = result.judgment
    event_id = str(event.get("event_id", "unknown"))
    return RecommendedAction(
        id=f"action-{event_id}",
        title=judgment.title,
        description=judgment.description,
        vertical=vertical,
        reasoning_trace=build_llm_reasoning_trace(event, vertical, result) + economic_steps,
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


def _decide_proposals(
    run_id: str,
    proposals: list[dict[str, Any]],
    decisions: Mapping[str, str],
) -> tuple[list[tuple[ActionRecord, str]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Phase 1 of the gate (PLAN-0047 Step 4): validate + apply every decision
    IN MEMORY — no handler fires here. Returns ``(dispositions, pending_entries,
    trace_adds)`` in proposal order: approved records serialise as
    ``pending_execution`` (the durable intent the caller commits before any
    effect), rejects serialise final + carry their trace entry."""
    dispositions: list[tuple[ActionRecord, str]] = []
    pending_entries: list[dict[str, Any]] = []
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
            pending_entries.append({**_entry(record, None), "status": "pending_execution"})
        elif decision == REJECT:
            reject(record)
            pending_entries.append(_entry(record, None))
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
        dispositions.append((record, decision))
    return dispositions, pending_entries, trace_adds


@dataclass(frozen=True)
class ActionStepExecutor:
    """The real ``action`` StepExecutor (AC A-7). See module docstring."""

    client_factory: ClientFactory = _default_client_factory
    # PLAN-0093 AC-6: ``None`` means "read settings.llm_retry_budget at use time".
    # This was a hardcoded 3 that no factory overrode, so LLM_RETRY_BUDGET was
    # honoured on every reactive path and silently inert on the governed one —
    # the disclosed configuration was not the operative one. An explicit
    # constructor value still wins (the nl_query.answer_question idiom).
    retry_budget: int | None = None

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
        budget = self.retry_budget if self.retry_budget is not None else settings.llm_retry_budget
        auto = step.autonomy is Autonomy.AUTO
        output: list[Any] = []
        trace: list[dict[str, Any]] = []
        for entity in input_set:
            event = dict(entity) if isinstance(entity, Mapping) else {"value": entity}
            judgment = await generate_judgment(
                client, event, ctx.vertical, retry_budget=budget, goal=ctx.goal
            )
            # ADR-0030 / PLAN-0071: the advisory economic-impact facet on the governed
            # action path — the FIRST appended advisory step on this composition; the
            # helper never raises (ADR-0030 D5), so it cannot break the run.
            economic_steps = await build_economic_steps(event, ctx.vertical)
            action = _compose_action(
                event, ctx.vertical, judgment, handler=step.handler, economic_steps=economic_steps
            )
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


def _enforce_tier_authority(
    target: StepResult,
    run_id: str,
    step_id: str,
    principal: Person,
    procedure: Procedure | None,
    principals: list[Person] | None,
) -> None:
    """Run the LIVE fail-closed tier-authority run-check for a gate resolution (ADR-0026 D4 (iv);
    PLAN-0075) — ADDITIVE beside :func:`_enforce_principal_sod`, and run AFTER it (SoD stays the
    primary check, LOCKED #2). Reads the step's PERSISTED authority verdicts
    (``target.audit["doa_tier" | "severity_tier"]``, written by the governance executor at run
    time) plus the gated step's declared ``governance_content`` (when the caller supplied the
    procedure), and raises :class:`TierAuthorityError` (BLOCK — no approve/execute) unless the
    acting principal holds the resolved tier role of EVERY verdict. Inert on a non-authority gate
    (no persisted verdict and no declared authority content)."""
    audit = target.audit or {}
    persisted = audit.get("doa_tier") or audit.get("severity_tier") or []
    content = None
    if procedure is not None:
        step = next((s for s in procedure.steps if s.step_id == step_id), None)
        content = step.governance_content if step is not None else None
    verdict = check_tier_authority(
        principal=principal,
        step_id=step_id,
        governance_content=content,
        persisted_verdicts=persisted,
        declared_principals=principals or [],
    )
    if not verdict.governed:
        raise TierAuthorityError(verdict, run_id=run_id, step_id=step_id)


async def _enforce_tier_authority_with_refusal_audit(
    session: AsyncSession,
    run_id: str,
    target: StepResult,
    step_id: str,
    principal: Person,
    procedure: Procedure | None,
    principals: list[Person] | None,
    audit_actor: Person | None = None,
) -> None:
    """Run the live tier-authority check; on a violation, durably audit the refusal (mirroring
    the SoD refusal, PLAN-0047 Step 5) BEFORE the ``TierAuthorityError`` propagates.

    ``audit_actor`` (default: ``principal``) is who the refusal row names — see
    :func:`_enforce_sod_with_refusal_audit` for why the two diverge on the provisional path."""
    actor = audit_actor if audit_actor is not None else principal
    try:
        _enforce_tier_authority(target, run_id, step_id, principal, procedure, principals)
    except TierAuthorityError as exc:
        await append_audit(
            session,
            action="gate_refused",
            actor_person_id=actor.person_id,
            run_id=run_id,
            step_id=step_id,
            payload={
                "kind": "tier_authority",
                "violations": [v.detail for v in exc.verdict.violations],
            },
        )
        await session.commit()
        raise


def _authority_governed_decisions(
    target: StepResult, principal: Person | None
) -> list[dict[str, Any]]:
    """The GATE-TIME authority audit-to-control tie (PLAN-0075 SD-6(a)): after the tier-authority
    check has passed, tie each resolved authority tier to its control + the ACTING principal — so
    the persisted ``governed_decision`` names who ACTUALLY acted, never the run-time routed-to
    approver (which stays a trace-level routing record). Empty for a principal-less gate or a step
    with no persisted authority verdict."""
    if principal is None:
        return []
    audit = target.audit or {}
    return [
        GovernedDecision(
            control_ref=ControlRef(kind=kind, id=verdict["resolved_tier_id"]),
            principal_id=principal.person_id,
        ).model_dump(mode="json")
        for kind in ("doa_tier", "severity_tier")
        for verdict in audit.get(kind, [])
    ]


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
    """Record the OQ-5 audit-to-control ties on a GOVERNED gate's resolved step (A1b Step 6, AC-8;
    PLAN-0075 SD-6a) — merged into the step audit, never overwriting it. Combines the SoD tie (the
    approving principal ↔ the SoD control) with the AUTHORITY ties (the acting principal ↔ each
    resolved doa_tier / severity_tier control) — both naming who ACTUALLY acted, emitted only after
    the SoD + tier-authority checks passed. A no-op for a non-SoD, non-authority, or principal-less
    gate (nothing to tie)."""
    governed = _sod_governed_decisions(
        step_id, principal, procedure
    ) + _authority_governed_decisions(target, principal)
    if governed:
        target.audit = {**(target.audit or {}), "governed_decision": governed}


def _authored_waiver(procedure: Procedure | None, step_id: str) -> EmergencyWaiverPolicy | None:
    """The emergency waiver authored on this gated step's DOA ladder, if any (ADR-0034 D2 Door 1).

    ``None`` when the caller supplied no procedure, when the step is not a DOA-ladder gate, or
    when the step is unknown. A procedure-less resolution therefore cannot reach the provisional
    path at all — which is the correct fail-closed reading: the window is authored config, and a
    caller who did not bring the config cannot prove one exists."""
    if procedure is None:
        return None
    step = next((s for s in procedure.steps if s.step_id == step_id), None)
    content = step.governance_content if step is not None else None
    return content.emergency_waiver if isinstance(content, DoaLadder) else None


def _resolve_attested_approver(
    waiver: EmergencyWaiverPolicy,
    principals: list[Person] | None,
    *,
    run_id: str,
    step_id: str,
) -> Person:
    """Resolve the waiver's ``escalate_to`` role to the Person being attested to, failing CLOSED.

    This is the honesty seam of the whole provisional path. The record is about to say "this
    authority approved by phone", so the authority must be a REAL declared principal — if
    ``escalate_to`` names a role nobody holds, there is no one the attestation could be about,
    and the only truthful response is to refuse the decide-first path (ADR-0034 D3(2)).

    Uses the same NATIVE-tier resolution the ladder routing uses
    (:func:`~services.engine.procedures.tier_authority.native_approver`), so the attested
    approver is the person for whom that authority is their own — not a senior who merely holds
    the role cumulatively. ``higher_roles`` is empty by construction: ``escalate_to`` is the
    authority the waiver escalates TO, so there is no tier above it to exclude."""
    attested_id = native_approver(
        waiver.escalate_to, higher_roles=frozenset(), principals=principals or []
    )
    person = next((p for p in (principals or []) if p.person_id == attested_id), None)
    if person is None:
        raise RatificationError(
            f"run '{run_id}': step '{step_id}' cannot be resolved provisionally — the waiver's "
            f"escalate_to authority '{waiver.escalate_to}' resolves to no declared Person, so "
            "there is nobody the attestation could name (fail closed; ADR-0034 D3(2))"
        )
    return person


async def _enforce_sod_with_refusal_audit(
    session: AsyncSession,
    run: PipelineRun,
    run_id: str,
    step_id: str,
    principal: Person | None,
    procedure: Procedure | None,
    principals: list[Person] | None,
    principal_aliases: list[PrincipalAlias] | None,
    audit_actor: Person | None = None,
) -> None:
    """Run the live principal-SoD check; on a violation, durably audit the
    refusal (PLAN-0047 Step 5) BEFORE the ``PrincipalSoDError`` propagates.

    ``principal`` is the identity being CHECKED; ``audit_actor`` (default: the same person) is
    who the refusal row names as having acted. They diverge on the provisional path, where the
    checked identity is the ATTESTED approver but the human who actually filed the record is the
    recorder — and an audit row must name the person who acted in-system (PLAN-0075 SD-6(a))."""
    actor = audit_actor if audit_actor is not None else principal
    try:
        _enforce_principal_sod(run, step_id, principal, procedure, principals, principal_aliases)
    except PrincipalSoDError as exc:
        await append_audit(
            session,
            action="gate_refused",
            actor_person_id=actor.person_id if actor is not None else None,
            run_id=run_id,
            step_id=step_id,
            payload={"violations": [v.detail for v in exc.verdict.violations]},
        )
        await session.commit()
        raise


async def resolve_gated_step(  # noqa: C901 — load-bearing gate driver: precondition guards (incl. RF-1) + SoD + governance pin + 2-phase decide/execute
    session: AsyncSession,
    run_id: str,
    step_id: str,
    decisions: Mapping[str, str],
    principal: Person | None = None,
    *,
    procedure: Procedure | None = None,
    principals: list[Person] | None = None,
    principal_aliases: list[PrincipalAlias] | None = None,
    waiver_invocation: WaiverInvocation | None = None,
) -> StepResult:
    """Apply a human's approve/reject decisions to a suspended gated action
    (Option 2 — the EXTERNAL gate driver; the shipped ``recommender`` gate,
    verbatim).

    **The provisional (decide-first) path** (ADR-0034 D3(2); PLAN-0096 Step 5). Passing a
    :class:`WaiverInvocation` records the resolution as an ATTESTATION rather than a firsthand
    approval: the authority approved out-of-band (the partner's roadside "เคาะก่อน ทำเอกสาร
    ทีหลัง") and the record catches up within the authored window. It is reachable ONLY when
    both halves of the entry condition hold — the step's authored ladder waiver carries
    ``ratification_window_days`` AND the caller explicitly invoked it — so a caller that passes
    no invocation runs the pre-existing path byte-for-byte.

    What changes on that path, and what deliberately does not:

    * ``principal`` becomes the **recorder** (the human filing the record — ต้อม on the hard
      shoulder, or เมย์ at the desk), still RF-1-guarded. The **attested approver** is the
      waiver's ``escalate_to`` role-holder, resolved fail-CLOSED.
    * The live SoD and tier-authority checks bind to the **attested approver**, not the
      recorder — so requester≠approver and the tier requirement hold exactly as they would
      have if the authority had clicked the button themselves. Neither is weakened; that is
      the whole reason this is a *deferred ratification* and not an SoD relaxation.
    * Effects execute (the truck gets fixed — deferring that is what this exists to avoid).
    * The step lands ``RESOLVED_PROVISIONAL`` carrying a ``ratification`` audit block, and
      **no** ``governed_decision`` tie is emitted: the attested authority has not acted
      in-system, and a tie naming them would be a lie the audit model has no way to catch
      (PLAN-0075 SD-6(a)). The tie is emitted at :func:`ratify_gated_step`, naming whoever
      actually signs.

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

    # RF-1 LIBRARY guard (ADR-016 S2, PLAN-0053 AC-1) — the fail-closed check the Phase-A HTTP
    # endpoint (runs.py:337) shipped ONLY at the HTTP surface. A gated step is a consequential
    # human-approval point: resolving one with NO identified approver is never permitted,
    # INDEPENDENT of settings.api_auth_enabled and of whether the step carries a SoD constraint
    # (the SoD run-check below is inert on a non-SoD step). This closes the scheduler / direct-
    # caller bypass. RF-3: `principal` is typed Person | None, so a service actor cannot reach
    # this approver seam by construction.
    if principal is None:
        raise GateApproverError(
            f"run '{run_id}': step '{step_id}' is a gated step — resolving it requires an "
            "identified human approver (ADR-016 S2 RF-1); none was supplied"
        )

    # PLAN-0047 Step 6 (AC-8): a mid-flight governance edit fails closed at the
    # gate too — verified whenever the caller supplies the procedure (the HTTP
    # surface always does; a procedure-less legacy call on a non-SoD run has no
    # config to compare, and resume re-checks the pin regardless).
    if procedure is not None:
        assert_governance_pin(loaded.run, procedure, context="gate resolution")

    # ---- The ADR-0034 D3(2) provisional entry condition -----------------------
    # BOTH halves must hold, and the failure is LOUD rather than a silent fallback to the
    # ordinary path: a caller who asked to record a decide-first resolution on a gate that
    # cannot represent one has a wiring bug, and quietly recording a FIRSTHAND approval
    # instead would put an authority's name on a decision they never made in-system.
    waiver = _authored_waiver(procedure, step_id)
    attested: Person | None = None
    window_days: int | None = None
    if waiver_invocation is not None:
        if waiver is None:
            raise RatificationError(
                f"run '{run_id}': step '{step_id}' is not a DOA-ladder gate with an authored "
                "emergency waiver — the provisional (decide-first) path is unreachable here "
                "(ADR-0034 D3(2)); resolve it firsthand or supply the procedure"
            )
        if waiver.ratification_window_days is None:
            raise RatificationError(
                f"run '{run_id}': step '{step_id}' waiver authors no ratification_window_days — "
                "without an authored window there is no bound on the catch-up, so the "
                "provisional path is not representable (ADR-0034 D2 Door 1 / D3(2))"
            )
        window_days = waiver.ratification_window_days
        attested = _resolve_attested_approver(waiver, principals, run_id=run_id, step_id=step_id)

    # WHO the governance checks below are about. On the ordinary path that is the acting
    # approver; on the provisional path it is the ATTESTED approver — the checks must hold
    # against the authority the record claims decided, never against the clerk who typed it.
    gate_actor = attested if attested is not None else principal

    # The LIVE fail-closed principal-SoD run-check (ADR-0026 D4; A1b Step 1) — runs
    # BEFORE any approve/execute so a violation blocks the gate (no PO, no governed
    # verdict). Non-skippable on a SoD run; inert otherwise. PLAN-0047 Step 5: a
    # refusal is itself audited durably before the exception propagates.
    await _enforce_sod_with_refusal_audit(
        session,
        loaded.run,
        run_id,
        step_id,
        gate_actor,
        procedure,
        principals,
        principal_aliases,
        audit_actor=principal,
    )

    # The LIVE fail-closed tier-authority run-check (ADR-0026 D4 (iv); PLAN-0075) — ADDITIVE beside
    # the SoD check and run AFTER it (SoD stays primary, LOCKED #2). It verifies the acting approver
    # holds the ladder-resolved tier role of every persisted authority verdict, BLOCKING the gate
    # (no approve/execute, no PO) otherwise — the guarantee ADR-0026 D5 stated but no run path
    # delivered. Inert on a non-authority gate; a refusal is durably audited before the error.
    await _enforce_tier_authority_with_refusal_audit(
        session,
        run_id,
        target,
        step_id,
        gate_actor,
        procedure,
        principals,
        audit_actor=principal,
    )

    # ---- Phase 1 (PLAN-0047 Step 4, AC-6): decide + COMMIT the intent -------
    # Every decision is validated and applied in memory, then the decisions +
    # the governed_decision audit tie + the gate-principal trace are COMMITTED
    # BEFORE any handler effect fires. A crash/raise after this commit leaves:
    # the step still waiting_human, the ORIGINAL proposals intact (the resolve
    # is retryable), the decisions durably recorded as pending_execution, and
    # NO phantom executed effect. The pending -> executed shape is the seam a
    # real transactional outbox slots into later (in-process handlers today).
    dispositions, pending_entries, trace_adds = _decide_proposals(run_id, proposals, decisions)

    if attested is not None:
        # A DIFFERENT trace kind from the firsthand one, deliberately. The analytics read
        # (`run_analytics`) counts `gate_principal_recorded` as "an approver was recorded on
        # this gate" — and on a provisional resolution no approver has acted in-system yet.
        # Emitting the firsthand kind would inflate that count with gates whose authority
        # never signed, which is precisely the hole the ratification window exists to expose.
        trace_adds.append(
            {
                "kind": "gate_provisionally_recorded",
                "principal_id": principal.person_id,
                "attested_approver_id": attested.person_id,
                "summary": (
                    f"gate recorded PROVISIONALLY by '{principal.person_id}' attesting that "
                    f"'{attested.person_id}' approved out-of-band — effects execute now; the "
                    "firsthand ratification is owed within the authored window (ADR-0034 D3)"
                ),
            }
        )
    else:
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
    #
    # WITHHELD on the provisional path (ADR-0034 D3(2)): the tie's contract is that it names who
    # ACTUALLY acted (PLAN-0075 SD-6(a)). Naming the attested approver would assert an in-system
    # act that did not happen; naming the recorder would assert an authority they do not hold.
    # There is no honest tie to emit yet, so none is — `ratify_gated_step` emits it later.
    if attested is None:
        _record_governed_decision(target, step_id, principal, procedure)
    target.artifact = {"output_set": proposals, "decisions": pending_entries}
    target.reasoning_trace = list(target.reasoning_trace or []) + trace_adds
    # The run row is touched HERE so its optimistic-lock version bumps AT the
    # decision commit — a concurrent resolver loses (StaleDataError) BEFORE its
    # handlers fire, not after (true exactly-once under concurrency).
    decided_at = datetime.now(UTC)
    loaded.run.updated_at = decided_at
    await session.merge(loaded.run)
    await session.merge(target)
    # PLAN-0047 Step 5: the gate decision is audited in the SAME transaction
    # as the durable intent (decision + audit land together, before any effect).
    decision_payload: dict[str, Any] = {"decisions": dict(decisions), "actor_kind": "human"}
    if attested is not None and waiver is not None and waiver_invocation is not None:
        decision_payload |= {
            "kind": "provisional",
            "justification": waiver_invocation.justification,
            "attested_approver_id": attested.person_id,
            "recorded_by": principal.person_id,
            "ratify_by_role": waiver.escalate_to,
            "ratification_window_days": waiver.ratification_window_days,
        }
    decision_row = await append_audit(
        session,
        action="gate_decision",
        actor_person_id=principal.person_id,
        run_id=run_id,
        step_id=step_id,
        payload=decision_payload,
    )
    await session.commit()  # the decision is durable BEFORE any effect (AC-6)

    # ---- Phase 2: execute the approved effects, then commit the receipts ----
    executed_effects: list[dict[str, Any]] = []
    effects_by_id: dict[str, dict[str, Any]] = {}
    exec_trace: list[dict[str, Any]] = []
    for record, decision in dispositions:
        if decision != APPROVE:
            continue
        receipt = await gate_execute(record)
        effect = _entry(record, receipt)
        executed_effects.append(effect)
        effects_by_id[record.action.id] = effect
        exec_trace.append(
            {
                "kind": "action_executed",
                "action_id": record.action.id,
                "summary": (
                    f"human-approved; executed handler '{record.action.suggested_handler}'"
                ),
            }
        )
    # Final artifact in proposal order — byte-shape identical to the pre-Step-4
    # contract: executed effects thread forward; rejects are recorded, not threaded.
    decided = [
        effects_by_id[record.action.id] if decision == APPROVE else _entry(record, None)
        for record, decision in dispositions
    ]
    target.artifact = {"output_set": executed_effects, "decisions": decided}
    target.reasoning_trace = list(target.reasoning_trace or []) + exec_trace
    # PLAN-0047 Step 3 — the gate state machine: a decided gate flips to RESOLVED,
    # so a second resolve fails the waiting_human precondition above (idempotent
    # BY STATE — the handler cannot refire) and resume_run advances the gate from
    # this status, never from artifact presence. The RUN row is touched so its
    # optimistic-lock version bumps — a concurrent resolver loses at commit
    # (StaleDataError) instead of silently double-writing.
    #
    # ADR-0034 D3(2): a provisional resolution lands RESOLVED_PROVISIONAL instead, carrying the
    # obligation on the step audit. `due_at` is computed through the ONE shared helper the
    # reports also use, so the deadline the driver writes and the deadline a month-end export
    # recomputes can never disagree by a day.
    if attested is not None and waiver is not None and window_days is not None:
        target.status = StepResultStatus.RESOLVED_PROVISIONAL.value
        target.audit = {
            **(target.audit or {}),
            RATIFICATION_KEY: {
                "due_at": due_at_from(decided_at, window_days).isoformat(),
                "ratify_by_role": waiver.escalate_to,
                "attested_approver_id": attested.person_id,
                "recorded_by": principal.person_id,
                # The tamper-evident handle of the audit row holding the run-time justification.
                # A content hash rather than a row id on purpose: if that row is ever edited, the
                # ref stops resolving AND `verify_chain` breaks — the reason cannot be quietly
                # rewritten after the fact while the obligation still points at it.
                "justification_ref": decision_row.row_hash,
            },
        }
    else:
        target.status = StepResultStatus.RESOLVED.value
    loaded.run.updated_at = datetime.now(UTC)
    await session.merge(loaded.run)
    await session.merge(target)
    # PLAN-0047 Step 5: every executed effect's receipt is audited in the same
    # commit that records it on the step artifact.
    for effect in executed_effects:
        await append_audit(
            session,
            action="handler_receipt",
            actor_person_id=principal.person_id if principal is not None else None,
            run_id=run_id,
            step_id=step_id,
            payload={
                "action_id": effect["action_id"],
                "receipt": effect["receipt"],
                "actor_kind": "human",
            },
        )
    await session.commit()
    return target


def _ratification_verdicts(view_role: str | None, attested_id: str | None) -> list[dict[str, Any]]:
    """The synthetic authority verdict that makes the ratifier's requirement checkable by the
    EXISTING tier-authority predicate (ADR-0034 D3(3): "enforced by REUSING
    ``check_tier_authority``").

    ``check_tier_authority`` asks one question — does this principal hold the ``required_role``
    of every verdict? — so expressing "the ratifier must hold ``ratify_by_role``" as a verdict
    reuses that predicate, its structured violation kinds, and its declared-principal check
    verbatim, instead of growing a second, subtly-different authority rule that could drift.

    Only the ratifier's own requirement is asserted here, NOT the ladder's persisted verdicts.
    That is deliberate: ``ratify_by_role`` is the ESCALATED authority, which under cumulative
    role authoring already dominates the tier — but under a vertical that authors roles
    non-cumulatively, also demanding the tier role would block the very authority the waiver
    escalates to. The ADR names one requirement; this asserts exactly it."""
    return [{"required_role": view_role, "resolved_approver_id": attested_id}]


async def ratify_gated_step(  # noqa: C901 — the sibling gate driver: obligation precondition + RF-1 + pin + SoD + tier-authority + the ratify/refuse fork, each a named ADR-0034 D3 branch
    session: AsyncSession,
    run_id: str,
    step_id: str,
    principal: Person | None = None,
    *,
    decision: RatificationDecision = "ratify",
    procedure: Procedure | None = None,
    principals: list[Person] | None = None,
    principal_aliases: list[PrincipalAlias] | None = None,
    now: datetime | None = None,
    note: str = "",
) -> StepResult:
    """The record catching up: the ``ratify_by_role`` authority signs (or declines to sign) a
    step that was resolved provisionally (ADR-0034 D3(3)/D3(4); PLAN-0096 Step 5).

    The sibling of :func:`resolve_gated_step`, running the same live checks against the human
    who is acting NOW — RF-1, the governance pin, principal-SoD, and tier-authority — and, on a
    ratification, emitting the ``governed_decision`` tie that was deliberately withheld at
    provisional time. That tie names the RATIFIER, because the ratifier is who actually acted
    (PLAN-0075 SD-6(a)). The trail therefore never claims a firsthand approval before one exists,
    and gains one the moment it does.

    **The precondition is the OBLIGATION, not the step status** (Cray, typed pick, session 187).
    ADR-0034 D3(3) writes the precondition as ``status == RESOLVED_PROVISIONAL``, but D3(6) of the
    same ADR requires that ratification stay possible on a COMPLETED run — and ``resume_run``
    flips every resolved step to ``complete`` as it advances (``persistence.py``). In the fleet
    hero the gate after ``approve`` is itself gated, so the run ALWAYS resumes past ``approve``
    within minutes, while the authored window is seven days. Read literally, D3(3) would make the
    owner's signature impossible in exactly the flow the window exists for. So the precondition is
    an outstanding ratification obligation — ``pending`` or ``overdue`` per
    :func:`~services.engine.procedures.ratification.ratification_state`. That is a superset of
    D3(3)'s condition (a step at ``RESOLVED_PROVISIONAL`` always carries one) and it preserves
    D3(3)'s stated intent verbatim: idempotency BY STATE, since a second ratification finds the
    obligation no longer outstanding and is refused.

    An **overdue** obligation is still ratifiable. Overdue is urgency, not expiry — the signature
    is owed either way, and refusing it late would strand the case in the one state nobody can
    clear (ADR-0034 D3(6); ``RatificationView.is_outstanding``).

    ``decision="refuse"`` records the honest opposite (D3(4)): the authority declines to stand
    behind the decision. **Nothing un-executes** — the money is spent, so a fail-closed response
    is not available after the fact — and **no tie is emitted**, because a refusal is precisely
    the assertion that this authority did NOT govern the spend. The case becomes a named
    exception on the month-end export.

    ``now`` is injected (never an ambient clock) so the overdue boundary is testable offline.
    Raises :class:`RatificationError` when no outstanding obligation exists,
    :class:`GateApproverError` when no identified human is supplied (RF-1),
    :class:`PrincipalSoDError` / :class:`TierAuthorityError` when the acting ratifier fails a
    live check — each durably audited before the error propagates.
    """
    loaded = await load_run(session, run_id)
    if loaded is None:
        raise ProcedureError(f"run '{run_id}' not found")
    target = next((s for s in loaded.step_results if s.step_id == step_id), None)
    if target is None:
        raise ProcedureError(f"run '{run_id}': step '{step_id}' is not in the run")

    moment = now if now is not None else datetime.now(UTC)
    view = ratification_state(target.audit, moment)
    if not view.is_outstanding:
        raise RatificationError(
            f"run '{run_id}': step '{step_id}' carries no outstanding ratification obligation "
            f"(state '{view.state}') — only a provisionally-resolved step awaiting its firsthand "
            "signature can be ratified or refused, and a second attempt on one already settled "
            "is refused BY STATE (ADR-0034 D3(3))"
        )

    # RF-1 (ADR-016 S2, PLAN-0053 AC-1) — ratifying is the consequential human act the whole
    # provisional path was deferring; it can never happen without an identified human.
    if principal is None:
        raise GateApproverError(
            f"run '{run_id}': step '{step_id}' ratification requires an identified human "
            "(ADR-016 S2 RF-1); none was supplied"
        )

    if procedure is not None:
        assert_governance_pin(loaded.run, procedure, context="gate ratification")

    # SoD first (LOCKED #2 — it stays the primary check), then tier-authority: the ratifier must
    # be distinct from the requester and hold the escalated authority the waiver named. Both are
    # the SAME checks the firsthand path runs, which is what makes deferring the signature a
    # timing exception rather than a governance one.
    await _enforce_sod_with_refusal_audit(
        session,
        loaded.run,
        run_id,
        step_id,
        principal,
        procedure,
        principals,
        principal_aliases,
    )
    try:
        verdict = check_tier_authority(
            principal=principal,
            step_id=step_id,
            governance_content=None,
            persisted_verdicts=_ratification_verdicts(
                view.ratify_by_role, view.attested_approver_id
            ),
            declared_principals=principals or [],
        )
        if not verdict.governed:
            raise TierAuthorityError(verdict, run_id=run_id, step_id=step_id)
    except TierAuthorityError as exc:
        await append_audit(
            session,
            action="gate_refused",
            actor_person_id=principal.person_id,
            run_id=run_id,
            step_id=step_id,
            payload={
                "kind": "ratification_authority",
                "violations": [v.detail for v in exc.verdict.violations],
            },
        )
        await session.commit()
        raise

    settled_at = datetime.now(UTC)
    block = dict((target.audit or {}).get(RATIFICATION_KEY) or {})
    if decision == "refuse":
        block |= {"refused_at": settled_at.isoformat(), "refused_by": principal.person_id}
    else:
        block |= {"ratified_at": settled_at.isoformat(), "ratified_by": principal.person_id}
    if note.strip():
        block["note"] = note
    target.audit = {**(target.audit or {}), RATIFICATION_KEY: block}

    # The tie the provisional resolution withheld — emitted ONLY on a ratification, naming the
    # ratifier. A refusal emits none: it is the statement that this authority does not stand
    # behind the spend, and a tie would record the opposite.
    if decision == "ratify":
        _record_governed_decision(target, step_id, principal, procedure)

    # Only a step still parked at RESOLVED_PROVISIONAL flips to RESOLVED. A step the run has
    # already advanced past is `complete`, and moving it BACK to `resolved` would re-enter it
    # into `_UNRESUMED_STATUSES` — making a finished step look like the one the run is suspended
    # at, which `suspended_step_result` would then either resume a second time or refuse as an
    # inconsistent run. The obligation lives on the audit block, so the status does not need to
    # carry it (ADR-0034 D3(6)).
    if target.status == StepResultStatus.RESOLVED_PROVISIONAL.value:
        target.status = StepResultStatus.RESOLVED.value

    # Touch the run so the optimistic lock bumps — a ratify racing a concurrent resolve/resume
    # loses cleanly with StaleDataError rather than silently double-writing (PLAN-0047 Step 3).
    loaded.run.updated_at = settled_at
    await session.merge(loaded.run)
    await session.merge(target)
    await append_audit(
        session,
        action="gate_ratified" if decision == "ratify" else "ratification_refused",
        actor_person_id=principal.person_id,
        run_id=run_id,
        step_id=step_id,
        payload={
            "actor_kind": "human",
            "attested_approver_id": view.attested_approver_id,
            "recorded_by": view.recorded_by,
            "ratify_by_role": view.ratify_by_role,
            "due_at": view.due_at.isoformat() if view.due_at is not None else None,
            "was_overdue": view.state == "overdue",
            "justification_ref": (target.audit or {})
            .get(RATIFICATION_KEY, {})
            .get("justification_ref"),
            "note": note or None,
        },
    )
    await session.commit()
    return target
