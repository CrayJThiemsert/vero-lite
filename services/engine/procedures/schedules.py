"""Persisted schedule state for ``schedule``-triggered procedures (ADR-0028 SD-P5;
PLAN-0055 Step 2).

A small DEDICATED table — one row per scheduled procedure — chosen over deriving the fire
clock from ``PipelineRun`` history (SD-P5: derive-from-history is fragile + races). The
long-lived scheduler daemon (PLAN-0055 Phase B) recovers its schedule set from this table
on restart (AC-7) and stamps ``last_fired`` / ``next_fire`` as it fires. Purely additive:
it touches neither the ADR-008 ontology nor the ``pipeline_runs`` run-record layer.

Shares the project ``Base`` (``services/db/base.py``) so the Alembic metadata + the test
``create_all`` see it; ``alembic/env.py`` imports this module to register the table on
``Base.metadata``.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from services.db.base import Base


class ScheduleState(Base):
    """The persisted clock of one ``schedule``-triggered procedure (ADR-0028 SD-P5).

    ``last_fired`` / ``next_fire`` are nullable: a freshly-registered schedule has no fire
    history, and its ``next_fire`` is computed by the croniter helper (PLAN-0055 Step 3)
    before the first tick — Step 2 only lands the surface. ``(vertical, procedure_id)`` is
    unique: a ``procedure_id`` is unique only WITHIN a vertical (spec cross-refs), so the
    natural identity of a schedule is the pair, not the id alone.
    """

    __tablename__ = "schedule_states"
    __table_args__ = (
        UniqueConstraint("vertical", "procedure_id", name="uq_schedule_states_vertical_procedure"),
    )

    schedule_id: Mapped[str] = mapped_column(Text, primary_key=True)
    vertical: Mapped[str] = mapped_column(Text, nullable=False)
    procedure_id: Mapped[str] = mapped_column(Text, nullable=False)
    cron: Mapped[str] = mapped_column(Text, nullable=False)
    timezone: Mapped[str] = mapped_column(Text, nullable=False)
    last_fired: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_fire: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
