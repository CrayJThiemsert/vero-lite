"""Hand-authored identity projection for the reactive action loop (PLAN-0047 Step 1).

Deliberately SEPARATE from the generated energy ORM
(``services/db/models.py``): the YAML→ORM parity suite pins generated
tables to the ontology exactly, so caller identity — engine governance
state, not vertical ontology — lives in its own table, like the
``pipeline_runs`` family (``services/engine/procedures/runs.py``).
"""

from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from services.db.base import Base


class ActionIdentity(Base):
    """Who approved / executed a reactive-loop action (AC-1 identity recording).

    One merge-idempotent row per executed action; ``approved_by`` /
    ``executed_by`` are the server-resolved ``person_id``s from the authn
    dependency (never client-supplied), nullable because a deployment may
    run with authn disabled (``api_auth_enabled=false``).
    """

    __tablename__ = "action_identity"

    action_id: Mapped[str] = mapped_column(sa.Text, primary_key=True)
    approved_by: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    executed_by: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
