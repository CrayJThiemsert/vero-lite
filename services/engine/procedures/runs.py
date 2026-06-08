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

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Text
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
    FAILED = "failed"


class PipelineRun(Base):
    """A run of a Procedure — the additive run-time record (ADR-016 D2)."""

    __tablename__ = "pipeline_runs"

    run_id: Mapped[str] = mapped_column(Text, primary_key=True)
    procedure_id: Mapped[str] = mapped_column(Text, nullable=False)
    agent_id: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_context: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


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
