"""Append-only, hash-chained audit log (PLAN-0047 Step 5, SD-3 = yes-minimal).

The MINIMAL append-only audit slice ratified under SD-3: an ``audit_log``
table written at every governance-relevant transition (run start, gate
decision, handler receipt, resume, SoD refusal), protected by

* a **block trigger** (migration ``0007``) that raises on UPDATE/DELETE —
  binding even for the compose-default owner credential the dev box uses;
* an **INSERT-only DB role** (``vero_audit_writer``, provisioned by the
  migration for the pilot cutover; the app's own credential is item-6
  remainder);
* a **per-row hash chain**: ``row_hash = sha256(canonical(prev_hash + row
  fields))`` with a UNIQUE index on ``prev_hash`` — the chain is linear by
  construction, and :func:`verify_chain` detects any in-place mutation or
  splice even by an actor strong enough to drop the trigger.

The full audit *framework* (retention, export, external anchoring, PDPA
surface) stays ADR-011, gated on real partner data.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from services.db.base import Base

GENESIS_HASH = "0" * 64
"""``prev_hash`` of the first row — the chain anchor."""

# Frozen copies of this DDL live in alembic/versions/0007_audit_log.py (a
# migration must never change after it ships); these constants exist so the
# create_all-based test fixtures can install the SAME guard.
AUDIT_BLOCK_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION audit_log_block_mutation() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'audit_log is append-only (PLAN-0047 Step 5) — % blocked', TG_OP;
END;
$$ LANGUAGE plpgsql;
"""
AUDIT_BLOCK_TRIGGER_SQL = """
CREATE TRIGGER audit_log_no_mutation
BEFORE UPDATE OR DELETE ON audit_log
FOR EACH ROW EXECUTE FUNCTION audit_log_block_mutation();
"""


class AuditLog(Base):
    """One governance-relevant transition, hash-chained to its predecessor.

    Hand-authored engine-governance table (like ``pipeline_runs`` /
    ``action_identity``) — never part of the generated ontology schema, so
    the YAML→ORM parity suite is untouched.
    """

    __tablename__ = "audit_log"
    __table_args__ = (
        # The chain is LINEAR by construction: two writers extending the same
        # predecessor cannot both commit (the rare loser retries/raises).
        sa.UniqueConstraint("prev_hash", name="uq_audit_log_prev_hash"),
        sa.Index("idx_audit_log_run_id", "run_id"),
    )

    audit_id: Mapped[int] = mapped_column(sa.BigInteger, sa.Identity(), primary_key=True)
    occurred_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    actor_person_id: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    action: Mapped[str] = mapped_column(sa.Text, nullable=False)
    run_id: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    step_id: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    prev_hash: Mapped[str] = mapped_column(sa.Text, nullable=False)
    row_hash: Mapped[str] = mapped_column(sa.Text, nullable=False)


def compute_row_hash(
    *,
    prev_hash: str,
    occurred_at: datetime,
    actor_person_id: str | None,
    action: str,
    run_id: str | None,
    step_id: str | None,
    payload: dict[str, Any] | None,
) -> str:
    """The canonical row hash: sha256 over a sorted-key JSON of every audited
    field + the predecessor's hash. ``occurred_at`` is normalised to UTC at
    microsecond precision (timestamptz round-trips it losslessly), so the
    verifier recomputes byte-identically from the stored row."""
    canonical = json.dumps(
        {
            "prev_hash": prev_hash,
            "occurred_at": occurred_at.astimezone(UTC).isoformat(timespec="microseconds"),
            "actor_person_id": actor_person_id,
            "action": action,
            "run_id": run_id,
            "step_id": step_id,
            "payload": payload,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


async def append_audit(
    session: AsyncSession,
    *,
    action: str,
    actor_person_id: str | None = None,
    run_id: str | None = None,
    step_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> AuditLog:
    """Append one chained audit row to the CURRENT session transaction.

    The caller owns the commit — so a governance transition and its audit row
    land in the SAME transaction (the Step-4 decision-before-effect ordering
    extends to the audit trail). The chain head is read ``FOR UPDATE``, which
    serialises concurrent appenders; the residual genesis race (empty table —
    nothing to lock) is closed by the UNIQUE(prev_hash) constraint.
    """
    head = (
        await session.execute(
            sa.select(AuditLog.row_hash)
            .order_by(AuditLog.audit_id.desc())
            .limit(1)
            .with_for_update()
        )
    ).scalar_one_or_none()
    prev_hash = head if head is not None else GENESIS_HASH
    occurred_at = datetime.now(UTC)
    row = AuditLog(
        occurred_at=occurred_at,
        actor_person_id=actor_person_id,
        action=action,
        run_id=run_id,
        step_id=step_id,
        payload=payload,
        prev_hash=prev_hash,
        row_hash=compute_row_hash(
            prev_hash=prev_hash,
            occurred_at=occurred_at,
            actor_person_id=actor_person_id,
            action=action,
            run_id=run_id,
            step_id=step_id,
            payload=payload,
        ),
    )
    session.add(row)
    return row


async def verify_chain(session: AsyncSession) -> list[str]:
    """Walk the whole chain; return a list of human-readable breaks (empty =
    intact). Detects in-place mutation (recomputed ``row_hash`` mismatch) and
    splice/reorder (``prev_hash`` linkage break) — the tamper-evidence that
    holds even against an actor strong enough to drop the block trigger."""
    rows = (await session.execute(sa.select(AuditLog).order_by(AuditLog.audit_id))).scalars().all()
    breaks: list[str] = []
    expected_prev = GENESIS_HASH
    for row in rows:
        if row.prev_hash != expected_prev:
            breaks.append(
                f"audit_id={row.audit_id}: prev_hash linkage broken "
                f"(expected {expected_prev[:12]}…, stored {row.prev_hash[:12]}…)"
            )
        recomputed = compute_row_hash(
            prev_hash=row.prev_hash,
            occurred_at=row.occurred_at,
            actor_person_id=row.actor_person_id,
            action=row.action,
            run_id=row.run_id,
            step_id=row.step_id,
            payload=row.payload,
        )
        if recomputed != row.row_hash:
            breaks.append(
                f"audit_id={row.audit_id}: row content mutated "
                f"(stored hash {row.row_hash[:12]}…, recomputed {recomputed[:12]}…)"
            )
        expected_prev = row.row_hash
    return breaks
