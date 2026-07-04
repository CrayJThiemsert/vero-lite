"""PLAN-0051 — the classify reason-then-structure A/B driver (shared pure logic).

A pure-logic module (no ``test_`` prefix → not collected). Both the OFFLINE A/B harness
(``test_reason_then_structure_classify``, Step 2) and the Cray-gated LIVE twin metric
(``test_reason_then_structure_classify_live``, Step 5) import :func:`classify_ab_route`, so
the A/B routing is defined ONCE and the offline gate exercises the EXACT logic the live run
uses — the offline oracle stays the gate; live is confirming evidence (CLAUDE.md §8).

The route goes through the PRODUCTION ``classify_narrative`` with the given ``arm``. The arm
changes only the classify prompt/schema (Step 1); the deterministic abstain-guard
(``_archetype_disagreement`` + the closed-label check) is production code, so the route is
byte-identical across arms by construction (LOCKED-3) — the A/B isolates the reasoning-order
lever, never the guard.
"""

from __future__ import annotations

from services.engine.llm.structured import ChatClient
from services.engine.procedures.generator.pipeline import (
    ClassifyArm,
    ProposedMatch,
    classify_narrative,
)


async def classify_ab_route(
    client: ChatClient, narrative: str, *, vertical: str, arm: ClassifyArm
) -> tuple[str, str]:
    """Route one narrative through ``classify_narrative`` for ``arm``; return ``(route, path)``.

    ``route`` is the matched ``archetype_id`` or ``"abstain"`` — the value scored against the
    fixture's pre-committed ``expected``. ``path`` records HOW the outcome arose (``"matched"``
    or the ``Abstained.reason`` — ``no_archetype_match`` / ``archetype_disagreement`` /
    ``classify_unparseable`` / ``llm_unreachable``) so a silent label→guard-backstop shift is
    visible in the twin-metric diagnostics (mirrors PLAN-0041's live ``_route``)."""
    outcome = await classify_narrative(client, narrative=narrative, vertical=vertical, arm=arm)
    if isinstance(outcome, ProposedMatch):
        return outcome.template.archetype_id, "matched"
    return "abstain", outcome.reason
