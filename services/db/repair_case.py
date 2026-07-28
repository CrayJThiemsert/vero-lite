"""Hand-authored repair-case table (PLAN-0096 Step 2 / AC-3).

Deliberately SEPARATE from the generated energy ORM (``services/db/models.py``):
the YAML→ORM parity suite pins generated tables to the ontology exactly, so this
table lives beside ``action_identity`` and the ``pipeline_runs`` family as a
hand-authored sidecar.

**Why it is named ``repair_case`` and not ``case``.** A case is the kind of noun
that *looks* vertical-agnostic — procurement and supply_chain could plausibly grow
one. Exactly one vertical needs it today, so ADR-006's Rule of Three says do not
abstract yet, and PLAN-0089's naming discipline says do not name a thing for a
generality that does not exist (the same reason the PM path is ``pm_service_round``
and not ``tire_*``). When a second and third vertical need cases, the extraction is
a rename with the shape already known. Naming it ``case`` today would claim a
generality nothing has tested.

**Why the partner needs it at all (Q1).** The data loss starts *after the first
phone call*: who took the case, which garage, when the price was agreed — today all
of it is trapped in individual phones. The case is what makes the run's evidence
chain start at minute 1 rather than at the moment a quote happens to be typed in,
and ``case_id`` riding the governed run's intake row is what links the two ends.

**Human-opened only (Q1, LOCKED).** There is no auto-detection path and none is
wanted; every row here was created by a person pressing a button.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from services.db.base import Base

#: The case lifecycle. Deliberately small: the partner's Q2 answer asked for
#: visible state + nudges, not workflow automation, and PLAN-0096 Step 6 grows the
#: post-approval task-chain on top of this rather than inside it.
CASE_STATUS_OPEN = "open"
CASE_STATUS_CLOSED = "closed"
CASE_STATUSES = (CASE_STATUS_OPEN, CASE_STATUS_CLOSED)


class RepairCase(Base):
    """One human-opened repair case for one truck.

    ``photos`` is JSONB rather than a child table: a photo is a small metadata
    record (id / filename / content type / size / relative stored path / uploaded
    time) whose BYTES live on disk, and nothing queries across photos. The same
    reasoning the run family uses for its JSONB audit blocks — a child table would
    buy joins nobody performs.

    ``opened_by`` is a ``person_id``-shaped string but carries no foreign key: the
    principal roster is resolved live from the procedures spec (the governance-pin
    module records the same reasoning — a personnel change must apply immediately),
    and น้องเมย์ opening a case from a phone must not fail closed because a roster
    row has not been synced.
    """

    __tablename__ = "repair_case"
    __table_args__ = (
        sa.Index("idx_repair_case_truck_id", "truck_id"),
        sa.Index("idx_repair_case_status", "status"),
    )

    case_id: Mapped[str] = mapped_column(sa.Text, primary_key=True)
    truck_id: Mapped[str] = mapped_column(sa.Text, nullable=False)
    opened_by: Mapped[str] = mapped_column(sa.Text, nullable=False)
    opened_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    #: Optional by design (AC-3): the truck pick is the ONLY required input, so a
    #: roadside case can be opened one-handed with a photo and nothing typed.
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    status: Mapped[str] = mapped_column(sa.Text, nullable=False, default=CASE_STATUS_OPEN)
    photos: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
