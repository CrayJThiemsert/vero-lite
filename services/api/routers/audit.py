"""Audit-chain verification surface (PLAN-0063) — the trust-dossier read view.

One read-only endpoint exposing the shipped ``verify_chain``
(``services/db/audit_log.py``) as a typed integrity report. It is object ③ of
the value thesis — the auditor's tamper-evidence — which had no product surface
before this: the UI already claimed the audit trail is "tamper-evident" without
ever letting a user see it verified.

* **SD-2(d) split visibility.** The verification VERDICT is served to any caller
  (consistent with the read-only monitor GETs, ``routers/runs.py``); the verbatim
  break strings, which enumerate exactly where the chain was cut, require a
  credential (``get_optional_principal``).
* **SD-4.** v1 accepts the O(n) whole-chain walk. A bounded / checkpointed verify
  is deferred — it would need trusted anchor storage ≈ external anchoring, which
  is the ADR-011 boundary this surface must NOT cross. A bounded walk cannot be
  honest anyway: a suffix proves nothing about the prefix it chains from.
* **Read-only by construction:** only SELECTs — no mutation, no LLM, no executor.
  ``audit_log.py`` and its DDL are untouched; this is a projection, not a schema
  change, and NOT the ADR-011 audit framework (no retention/export/anchoring).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

import sqlalchemy as sa
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services.api.auth import AuthContext, get_optional_principal
from services.api.config import settings
from services.api.models.audit import ChainVerificationReport
from services.db.audit_log import GENESIS_HASH, AuditLog, verify_chain
from services.db.session import get_session

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/verify", response_model=ChainVerificationReport)
async def verify_audit_chain(
    session: Annotated[AsyncSession, Depends(get_session)],
    auth: Annotated[AuthContext, Depends(get_optional_principal)],
) -> ChainVerificationReport:
    """Walk the whole ``audit_log`` hash chain and report its integrity.

    O(n) in the table size — ``verify_chain`` loads every row and recomputes each
    hash. Fine at pilot scale; a bounded verify is a documented follow-up (SD-4).
    The verdict is always computed from the real full walk; SD-2(d) only governs
    whether the verbatim ``breaks`` detail is disclosed to THIS caller.
    """
    breaks = await verify_chain(session)
    rows_verified = (
        await session.execute(sa.select(sa.func.count()).select_from(AuditLog))
    ).scalar_one()
    head_hash = (
        await session.execute(
            sa.select(AuditLog.row_hash).order_by(AuditLog.audit_id.desc()).limit(1)
        )
    ).scalar_one_or_none()

    # SD-2(d): disclose the break detail to a credentialed caller, or when authn
    # is disabled (the deployment explicitly opted out of the credential fence).
    reveal_breaks = (not settings.api_auth_enabled) or (auth.person_id is not None)
    return ChainVerificationReport(
        intact=not breaks,
        breaks=breaks if reveal_breaks else None,
        rows_verified=rows_verified,
        head_hash=head_hash,
        genesis_hash=GENESIS_HASH,
        verified_at=datetime.now(UTC),
    )
