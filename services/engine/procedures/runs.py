"""PipelineRun / StepResult run records (ADR-016 D2; PLAN-0019 Part A, SD-A1).

The durable, additive run-time RECORD layer the orchestrator writes as it runs a
``Procedure``. It does NOT touch the ADR-007 ``RecommendedAction`` envelope nor
the ADR-008 ontology — these are new ``pipeline_runs`` / ``step_results`` tables
(SD-A1: JSONB for the set-valued artifact + the per-step trace / audit; BIGINT
``duration_ms`` per the PLAN-0005 integer-column convention).

Persistence is the lever for ADR-016 D4 durable / resumable runs: a ``gated`` or
``human_task`` step suspends the run at ``waiting_human`` and a later (possibly
fresh-process) resume reads the persisted run. Every ``StepResult`` carries the
per-step telemetry seam (``duration_ms`` + ``reasoning_trace`` + ``audit``) the
PLAN-0019 Part B benchmark consumes (AC A-9) — required regardless of step kind.

These ORM models share the project ``Base`` (``services/db/base.py``) so the
Alembic metadata + the test ``create_all`` see them; ``alembic/env.py`` imports
this module to register the tables on ``Base.metadata``.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from services.db.base import Base


class PipelineRunStatus(StrEnum):
    """Run lifecycle (ADR-016 D2). The explicit enum is a legibility addition
    over Palantir's effect-level-only model — it feeds the Phase-3 OCT monitor."""

    RUNNING = "running"
    WAITING_HUMAN = "waiting_human"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepResultStatus(StrEnum):
    """Per-step lifecycle (ADR-016 D2)."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    WAITING_HUMAN = "waiting_human"
    # PLAN-0047 Step 3: the gate state machine — resolve_gated_step flips a
    # decided proposal gate waiting_human -> RESOLVED (so a second resolve fails
    # at the waiting_human precondition, idempotent BY STATE), and resume_run
    # advances a decidable gate ONLY from RESOLVED (never on artifact presence).
    RESOLVED = "resolved"
    FAILED = "failed"


class PipelineRun(Base):
    """A run of a Procedure — the additive run-time record (ADR-016 D2)."""

    __tablename__ = "pipeline_runs"

    run_id: Mapped[str] = mapped_column(Text, primary_key=True)
    procedure_id: Mapped[str] = mapped_column(Text, nullable=False)
    agent_id: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_context: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # The run-level per-step principal map the SoD run-check resolves against
    # (ADR-0026 D4 / PLAN-0044 A1b Step 1, SD-2=(a)): {step_id -> person_id | None}
    # for each SoD-constrained step the run completed (the REQUESTER half, recorded
    # from the TYPED ``RunContext.principal`` ambient resolution — never the untyped
    # ``trigger_context`` blob, OQ-2). The APPROVER half is added at gate-resolution
    # time (``resolve_gated_step``). ``None`` / absent = no SoD-constrained step ran
    # (every non-SoD procedure leaves it empty, so the live check stays inert for them).
    step_principals: Mapped[dict[str, str | None] | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # PLAN-0047 Step 6 (AC-8): the resolved governance config pinned at run
    # start — snapshot for human/audit inspection, hash for the fail-closed
    # pin-mismatch check on resume/resolve. Nullable: pre-0008 rows carry no
    # pin and skip the check (backward compat).
    governance_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    governance_hash: Mapped[str | None] = mapped_column(Text)
    # PLAN-0047 Step 3: optimistic concurrency — SQLAlchemy bumps + checks this
    # on every UPDATE (version_id_col), so concurrent resolve/resume writers lose
    # cleanly (StaleDataError) instead of silently double-writing run state.
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )

    # SQLAlchemy's DeclarativeBase types __mapper_args__ as an instance-level
    # attribute, so ClassVar (RUF012's suggested fix) would break mypy --strict.
    __mapper_args__ = {"version_id_col": version}  # noqa: RUF012


class StepResult(Base):
    """One step's result within a PipelineRun, incl. the telemetry seam (AC A-9)."""

    __tablename__ = "step_results"
    __table_args__ = (Index("idx_step_results_run_id", "run_id"),)

    step_result_id: Mapped[str] = mapped_column(Text, primary_key=True)
    run_id: Mapped[str] = mapped_column(Text, ForeignKey("pipeline_runs.run_id"), nullable=False)
    step_id: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(BigInteger)
    artifact: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    reasoning_trace: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    audit: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
