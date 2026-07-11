"""Response model for the audit-chain verification surface (PLAN-0063 Step 1).

The read-only trust-dossier contract — object ③ of the value thesis (the
auditor's tamper-evidence), which had no product surface before this. A pure
projection over the shipped ``verify_chain`` (``services/db/audit_log.py``): no
schema change, no framework. The ADR-011 audit framework (retention, export,
external anchoring, PDPA) stays gated on real partner data — nothing here.

**SD-2(d) split visibility.** The verification VERDICT (``intact`` /
``rows_verified`` / ``head_hash`` / ``genesis_hash`` / ``verified_at``) is served
to any caller; the verbatim ``breaks`` strings — which name an ``audit_id`` and
hash prefixes, i.e. exactly where the chain was cut — are withheld from an
anonymous caller (rendered ``null``) and served only to a credentialed one.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChainVerificationReport(BaseModel):
    """The hash-chain integrity verdict over the whole ``audit_log`` table."""

    model_config = ConfigDict(extra="forbid")

    intact: bool = Field(
        description=(
            "true when the whole chain verifies with zero breaks; always computed from the "
            "real full-chain walk, even for an anonymous caller whose break detail is withheld"
        )
    )
    breaks: list[str] | None = Field(
        description=(
            "the verbatim per-break strings from verify_chain (each names an audit_id and "
            "12-char hash prefixes) for a credentialed caller; null = withheld from an anonymous "
            "caller (SD-2(d)), which is NOT the same as [] (the chain verified intact)"
        )
    )
    rows_verified: int = Field(
        description="number of audit_log rows walked by the verifier (0 on an empty chain)"
    )
    head_hash: str | None = Field(
        description="the newest row's stored row_hash (the chain head); null on an empty chain"
    )
    genesis_hash: str = Field(
        description="the chain anchor — the prev_hash of the first row (64 zero characters)"
    )
    verified_at: datetime = Field(description="the UTC instant this verification walk ran")
