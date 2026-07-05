"""Request/response models for the procedure run + gate-resolve endpoints.

PLAN-0047 Step 2 (AC-2 / AC-3). The request models carry ONLY
caller-legitimate fields — never a principal: the caller identity is
resolved server-side from the bearer key by the authn dependency, and the
run endpoint OVERWRITES any client-supplied ``triggered_by`` (AC-2).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class RunProcedureRequest(BaseModel):
    """Start a manual run of a shipped procedure (the active vertical's spec)."""

    trigger_context: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Caller-legitimate context recorded on the run (what fired it). The "
            "server OVERWRITES 'triggered_by' with the authenticated person_id — "
            "a client-supplied identity is never trusted (AC-2)."
        ),
    )


class StepResultView(BaseModel):
    """One executed step's status projection."""

    step_id: str = Field(description="The procedure step this result belongs to")
    status: str = Field(description="Step status: complete | waiting_human | failed")


class ProposalView(BaseModel):
    """One proposed action awaiting a human decision at a suspended gate."""

    action_id: str = Field(description="The proposal id — the key for the resolve decision map")
    title: str = Field(description="Human-readable proposal title")
    suggested_handler: str | None = Field(
        default=None, description="The handler that would execute on approve"
    )


class RunProcedureResponse(BaseModel):
    """The persisted outcome of a run request (suspends at the first gate)."""

    run_id: str = Field(description="Server-generated id of the persisted run")
    procedure_id: str = Field(description="The procedure that ran")
    status: str = Field(
        description="Run status: completed | waiting_human (suspended at a gate) | failed"
    )
    triggered_by: str | None = Field(
        default=None,
        description=(
            "The SERVER-resolved person_id recorded on the run's trigger context "
            "(null when authn is disabled)"
        ),
    )
    suspended_step: str | None = Field(
        default=None,
        description="The step awaiting a human when status is waiting_human; null otherwise",
    )
    proposals: list[ProposalView] = Field(
        default_factory=list,
        description=(
            "The suspended gate's proposed actions awaiting approve/reject — "
            "empty unless status is waiting_human"
        ),
    )
    steps: list[StepResultView] = Field(description="Every recorded step result, in run order")


# ---------------------------------------------------------------------------
# PLAN-0052 Phase-3 OCT monitor (v1 — read-only): list + detail read models.
# Additive read-only projections over the already-persisted PipelineRun /
# StepResult rows (no schema change). ``trigger`` / ``triggered_by`` are
# projected from the persisted ``trigger_context`` — a projection widening,
# forward-compat for the ``schedule`` trigger (ADR-016 S1) and a future
# service-principal actor (ADR-016 S2): the actor is displayed GENERICALLY
# (never assumed to be a ``Person``) so it renders without a rewrite.
# ---------------------------------------------------------------------------


class StepDetailView(BaseModel):
    """One executed step's full read projection for the run-detail view."""

    step_id: str = Field(description="The procedure step this result belongs to")
    status: str = Field(description="Step status: complete | waiting_human | failed | resolved")
    duration_ms: int | None = Field(default=None, description="Wall-clock duration of the step")
    artifact: dict[str, Any] | None = Field(
        default=None, description="The step's produced object set / output"
    )
    reasoning_trace: list[dict[str, Any]] | None = Field(
        default=None, description="Per-step reasoning trace (ADR-016 D2 legibility)"
    )
    audit: dict[str, Any] | None = Field(
        default=None, description="Per-step audit metadata (actor_kind, governed_decision, …)"
    )


class RunSummaryView(BaseModel):
    """One run's summary row for the monitor list (read-only projection)."""

    run_id: str = Field(description="The persisted run id")
    procedure_id: str = Field(description="The procedure that ran")
    agent_id: str = Field(description="The agent that ran it")
    status: str = Field(description="running | waiting_human | completed | failed | cancelled")
    trigger: str = Field(
        description="How the run was fired (from trigger_context; 'manual' when unstamped) — "
        "forward-compat for the 'schedule' trigger (ADR-016 S1)"
    )
    triggered_by: str | None = Field(
        default=None,
        description="The actor recorded on the run (a person_id today; a service-principal id "
        "post-ADR-016 S2) — displayed generically, never assumed to be a Person",
    )
    started_at: datetime = Field(description="When the run started")
    updated_at: datetime = Field(description="Last status transition")
    steps_recorded: int = Field(description="Number of step results recorded so far")
    steps_total: int | None = Field(
        default=None,
        description="Declared step count from the current spec, if the procedure still ships",
    )
    steps_waiting: int = Field(description="Recorded steps currently at waiting_human")


class RunsListResponse(BaseModel):
    """The monitor list payload — runs newest-first + a 'waiting on me' count."""

    runs: list[RunSummaryView] = Field(description="Runs, newest-first")
    waiting_human_count: int = Field(
        description="How many runs are suspended at waiting_human (the 'waiting on me' count)"
    )


class RunDetailView(BaseModel):
    """One run's full read projection for the monitor detail view (read-only).

    Exposes the ``waiting_human`` gate + its pending proposals READ-ONLY (AC-7)
    so a future Control increment (approve/reject/cancel from the UI) wires the
    existing gate-resolve endpoint to this display — an extension, not a
    rewrite (L4).
    """

    run_id: str = Field(description="The persisted run id")
    procedure_id: str = Field(description="The procedure that ran")
    agent_id: str = Field(description="The agent that ran it")
    status: str = Field(description="running | waiting_human | completed | failed | cancelled")
    trigger: str = Field(description="How the run was fired (see RunSummaryView.trigger)")
    triggered_by: str | None = Field(
        default=None, description="The actor recorded on the run (displayed generically)"
    )
    started_at: datetime = Field(description="When the run started")
    updated_at: datetime = Field(description="Last status transition")
    suspended_step: str | None = Field(
        default=None, description="The step awaiting a human when status is waiting_human"
    )
    proposals: list[ProposalView] = Field(
        default_factory=list,
        description="The suspended gate's proposals, exposed READ-ONLY (Control-leg hook, AC-7)",
    )
    steps: list[StepDetailView] = Field(description="Every recorded step, in run order")


class GateResolveRequest(BaseModel):
    """A human's approve/reject decisions for a suspended gated step."""

    step_id: str = Field(description="The suspended step being resolved")
    decisions: dict[str, Literal["approve", "reject"]] = Field(
        description=(
            "action_id -> approve | reject; EVERY proposal at the gate needs an "
            "explicit decision (no silent default). The deciding principal comes "
            "from the bearer key, never this body."
        )
    )


class GateResolveResponse(BaseModel):
    """The outcome of resolving a gate and resuming the run."""

    run_id: str = Field(description="The resolved run")
    resolved_step: str = Field(description="The gated step the decisions were applied to")
    run_status: str = Field(
        description=(
            "Run status AFTER the post-resolve resume: completed | waiting_human "
            "(suspended again at a later gate) | failed"
        )
    )
    suspended_step: str | None = Field(
        default=None,
        description="The next step awaiting a human when run_status is waiting_human",
    )
    steps: list[StepResultView] = Field(
        description="Every recorded step result after the resume, in run order"
    )
