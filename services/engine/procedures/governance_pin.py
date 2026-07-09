"""Per-run governance-config pinning (PLAN-0047 Step 6, AC-8).

At run start the RESOLVED governance configuration — the SoD constraints
(+ their step→required-role maps) and every step's governance surface
(kind / autonomy / handler / typed AT-2 ``governance_content``) — is
snapshotted onto the ``PipelineRun`` row together with its canonical
sha256. ``resume_run`` / ``resolve_gated_step`` recompute the hash from
the caller-supplied procedure and FAIL CLOSED on a mismatch: a mid-flight
DOA-ladder / SoD / rule edit can never silently govern an old run, and
the audit question "which ladder governed THIS run?" is answered by the
run record itself.

Determinism note: set-typed spec fields (``distinct_steps``) are sorted
explicitly — Python's per-process str-hash randomisation would otherwise
make the same config hash differently across process restarts. The AT-2
``governance_content`` types carry no set-typed fields (verified against
the spec), so their ``model_dump`` + sorted-key JSON is stable.

NOT pinned in v1 (disclosed): the vertical-level ``principals`` /
``principal_aliases`` sets — the SoD run-check resolves those live by
design (a personnel change must apply immediately); the pinned surface is
the RULE configuration, not the people directory.

Pinned since PLAN-0048 SD-5(b): each step's declared ``input.reads``
(sorted) — the moment ``reads`` became execution-bound (the Q4 generic
executor dispatches exactly what is declared), a mid-flight ``reads`` edit
changes what a resumed run READS, so it must trip the same fail-closed
pin as a ladder edit. Disclosed format consequence: runs pinned BEFORE
this field existed refuse at resume (the PLAN-0047 sanctioned
cancel-and-restart path).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from services.engine.procedures.spec import Procedure


def build_governance_snapshot(procedure: Procedure) -> dict[str, Any]:
    """The canonical, JSON-safe projection of a procedure's governance config."""
    return {
        "procedure_id": procedure.procedure_id,
        "separation_of_duties": [
            {
                "distinct_steps": sorted(sod.distinct_steps),
                "required_roles": dict(sorted(sod.required_roles.items())),
            }
            for sod in procedure.separation_of_duties
        ],
        "steps": [
            {
                "step_id": step.step_id,
                "kind": step.kind.value,
                "autonomy": step.autonomy.value if step.autonomy is not None else None,
                "handler": step.handler,
                "governance_content": (
                    step.governance_content.model_dump(mode="json")
                    if step.governance_content is not None
                    else None
                ),
                # PLAN-0048 SD-5(b): the declared read surface is governance the
                # moment it is execution-bound — pinned sorted, like distinct_steps.
                "reads": (
                    sorted(step.input.reads)
                    if step.input is not None and step.input.reads
                    else None
                ),
                # PLAN-0061 Step 2 (Q4): the join/projection grammar changes what a
                # resumed run reads + how rows merge — pinned canonically (JSON mode,
                # by_alias so `with` pins as authored); a mid-flight edit fails
                # CLOSED at resume, same as a ladder edit.
                "join": (
                    [j.model_dump(mode="json", by_alias=True) for j in step.input.join]
                    if step.input is not None and step.input.join
                    else None
                ),
                "project": (
                    step.input.project.model_dump(mode="json")
                    if step.input is not None and step.input.project is not None
                    else None
                ),
            }
            for step in procedure.steps
        ],
    }


def compute_governance_hash(snapshot: dict[str, Any]) -> str:
    """sha256 over the canonical (sorted-key, compact) JSON of a snapshot."""
    canonical = json.dumps(
        snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def governance_pin_for(procedure: Procedure) -> tuple[dict[str, Any], str]:
    """Convenience: ``(snapshot, hash)`` for pinning at run start."""
    snapshot = build_governance_snapshot(procedure)
    return snapshot, compute_governance_hash(snapshot)
