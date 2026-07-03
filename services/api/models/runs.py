"""Request/response models for the procedure run + gate-resolve endpoints.

PLAN-0047 Step 2 (AC-2 / AC-3). The request models carry ONLY
caller-legitimate fields — never a principal: the caller identity is
resolved server-side from the bearer key by the authn dependency, and the
run endpoint OVERWRITES any client-supplied ``triggered_by`` (AC-2).
"""

from __future__ import annotations

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
