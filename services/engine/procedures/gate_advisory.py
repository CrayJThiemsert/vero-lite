"""PLAN-0085 Step 1 — the advisory gate recommendation builder (AI-Transition Rung 1).

At a ``doa_tier`` approval gate the run parks ``waiting_human`` and a person decides.
This module builds ONE advisory :class:`~services.engine.actions.ReasoningStep`-shaped
trace entry answering the approver's real question — *why did this land on MY desk?* —
from the gate's own deterministic verdicts (amount vs the ladder band, the resolved
tier/approver, SoD, the escalate-never-skip waiver posture). The entry is SHOWN, never
routes (PLAN-0085 L-B; ADR-0019:50-57): it writes to ``reasoning_trace`` only — never
to ``audit``, never to the output set — and the gate resolves exactly as it would
without it (the AC-4 fence).

**Arms (SD-2 = (b), stub-first).** The default arm (``client_factory=None``) builds
deterministic grounded reasons from the verdicts — no network, no MS-S1, demo-safe
under the ADR-0032 D1(3) offline discipline. A live arm exists behind the same seam
(:data:`ClientFactory`, the ``ActionStepExecutor(client_factory=...)`` shape): when a
factory is supplied, the builder additionally asks the client for a short narrative,
carried as ``detail.narrative`` — the deterministic reasons are ALWAYS present, so the
grounding never depends on the model. ``detail.model`` discloses the producing arm
(``"deterministic"``, or the live :class:`ChatResult.model`) — the record never
overstates which arm ran (SD-5 honesty mitigation).

**Never-raise (ADR-0030 D5).** :meth:`GateAdvisoryBuilder.build` catches everything
and returns ``[]`` — an advisory must never fail, park, or divert the run (the
``build_economic_steps`` contract, economic_impact.py). The orchestrator is untouched.

No numeric confidence is surfaced anywhere in the entry (PLAN-0085 L-C; the s74 trust
shape, PLAN-0035:591-602, executed by PR #823).
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from services.engine.llm.structured import ChatClient
from services.engine.procedures.doa_tier import DoaTierVerdict
from services.engine.procedures.orchestrator import RunContext
from services.engine.procedures.spec import DoaLadder, Step

logger = logging.getLogger(__name__)

ClientFactory = Callable[[str], ChatClient]
"""The ``ActionStepExecutor(client_factory=...)`` seam shape (action_step.py:146) —
redeclared here (like advisory_stub.py) to avoid importing the executor module."""

ADVISORY_TRACE_KIND = "advisory_recommendation"
"""The trace ``kind`` (SD-5): registered in trace-kinds.js with actor ``llm`` +
label "Advisory recommendation (shown, never routes)"; the set-equality tripwire
(tests/api/test_trace_kind_labels.py) pins it."""

_DETERMINISTIC_ARM = "deterministic"
"""``detail.model`` value for the default no-client arm (SD-2 disclosure)."""


def _band_text(verdict: DoaTierVerdict) -> str:
    """The half-open authority band as human text — ``฿min-฿max`` or ``฿min and above``."""
    lo = f"{verdict.band.min} {verdict.amount.currency}"
    if verdict.band.max is None:
        return f"{lo} and above"
    return f"{lo} up to {verdict.band.max} {verdict.amount.currency}"


def _reasons(ladder: DoaLadder, verdicts: list[DoaTierVerdict], entity: Any) -> list[str]:
    """Grounded, deterministic reasons — every line derives from a gate verdict or the
    authored ladder, never from model output (governed ≠ generated)."""
    v = verdicts[0]
    reasons = [
        (
            f"Spend {v.amount.value} {v.amount.currency} lands in tier "
            f"'{v.resolved_tier_id}' (band {_band_text(v)}), so approver role "
            f"'{v.required_role}' must sign"
            + (
                f" — resolved to '{v.resolved_approver_id}'."
                if v.resolved_approver_id is not None
                else "; tier-authority enforces at the gate."
            )
        )
    ]
    if v.sod_required:
        reasons.append(
            "Separation of duties binds this gate: the requester cannot approve "
            "their own requisition."
        )
    reasons.append(
        "Emergency handling can only escalate the approver above the band — the "
        "gate is never skipped (the ladder's waiver posture)."
    )
    if isinstance(entity, Mapping):
        quote_id = entity.get("selected_quote_id")
        supplier_id = entity.get("selected_supplier_id")
        if quote_id is not None and supplier_id is not None:
            reasons.append(
                f"Spend basis: selected quote '{quote_id}' from supplier "
                f"'{supplier_id}' (scored-rule selection upstream of this gate)."
            )
    if len(verdicts) > 1:
        reasons.append(
            f"{len(verdicts)} candidates reached this gate; the reasons above "
            "describe the first — every candidate's verdict rides the step audit."
        )
    return reasons


@dataclass(frozen=True)
class GateAdvisoryBuilder:
    """Builds the one advisory trace entry for a ``doa_tier`` gate (PLAN-0085 SD-1(b)).

    Supplied per vertical via the ``GovernanceActionExecutor(advisory_builder=...)``
    constructor argument — verticals that do not supply it stay byte-identical.
    """

    client_factory: ClientFactory | None = None
    model: str = "advisory"
    """Model name handed to the live arm's factory; unused on the deterministic arm."""

    async def build(
        self,
        *,
        step: Step,
        ladder: DoaLadder,
        verdicts: list[DoaTierVerdict],
        input_set: list[Any],
        ctx: RunContext,
    ) -> list[dict[str, Any]]:
        """0..1 advisory trace entries. NEVER raises — any failure logs a warning and
        returns ``[]`` (ADR-0030 D5: the advisory must never harm the run)."""
        try:
            return [await self._entry(step, ladder, verdicts, input_set)]
        except Exception:  # the never-raise contract IS the feature (ADR-0030 D5)
            logger.warning(
                "gate advisory failed for step %r — omitting the advisory entry "
                "(never-raise, ADR-0030 D5)",
                getattr(step, "step_id", "?"),
                exc_info=True,
            )
            return []

    async def _entry(
        self, step: Step, ladder: DoaLadder, verdicts: list[DoaTierVerdict], input_set: list[Any]
    ) -> dict[str, Any]:
        if not verdicts:
            raise ValueError("gate advisory needs at least one doa_tier verdict")
        v = verdicts[0]
        entity = input_set[0] if input_set else None
        reasons = _reasons(ladder, verdicts, entity)
        detail: dict[str, Any] = {
            "model": _DETERMINISTIC_ARM,
            "reasons": reasons,
            "tier": v.resolved_tier_id,
            "approver_role": v.required_role,
            "resolved_approver_id": v.resolved_approver_id,
            "sod_required": v.sod_required,
        }
        if self.client_factory is not None:
            # The live arm (opt-in, §8-gated at the wiring site — never the demo path):
            # the narrative SUPPLEMENTS the deterministic reasons, never replaces them.
            client = self.client_factory(self.model)
            result = await client.chat(
                [
                    {
                        "role": "system",
                        "content": (
                            "You brief a human approver in 2 short sentences. Explain "
                            "why this requisition needs THEIR level of authority, from "
                            "the facts given. No numbers you were not given, no "
                            "confidence scores, no recommendation to approve or reject."
                        ),
                    },
                    {"role": "user", "content": " ".join(reasons)},
                ]
            )
            detail["model"] = result.model
            detail["narrative"] = result.content
        return {
            # The literal (not the constant) is deliberate: the PLAN-0080 AC-3 tripwire
            # discovers emitted kinds by AST-scanning for {"kind": "<literal>"} dicts.
            "kind": "advisory_recommendation",
            "summary": (
                f"Advisory (shown, never routes): why this gate — spend "
                f"{v.amount.value} {v.amount.currency} requires '{v.required_role}'."
            ),
            "detail": detail,
        }
