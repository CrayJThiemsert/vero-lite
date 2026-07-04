"""PLAN-0051 — the nl_query reason-then-structure A/B driver (shared pure logic).

A pure-logic module (no ``test_`` prefix → not collected). Both the OFFLINE A/B harness
(``test_reason_then_structure_nl_query``, Step 4) and the Cray-gated LIVE A/B
(``test_reason_then_structure_nl_query_live``, Step 5) import :func:`translate_ab_query`, so
the A/B routing is defined ONCE and the offline gate exercises the EXACT logic the live run
uses — the offline oracle stays the gate; live is confirming evidence (CLAUDE.md §8).

The translate goes through the PRODUCTION ``_translate`` with the given ``arm`` and returns the
RAW ``StructuredQuery`` — the translate output BEFORE the Phase-B rewrite seam
(``_infer_group_by`` / ``_coherence_rewrite``), which is exactly what the SD-1 metric scores:
the seam repairs the aggregate-superlative drop AFTER translate, so scoring the raw output
isolates the reasoning-order lever instead of letting the seam mask (or credit) it.
"""

from __future__ import annotations

from services.engine.llm.structured import ChatClient
from services.engine.nl_query import StructuredQuery, TranslateArm, _translate
from services.engine.ontology_meta import load_ontology_meta


async def translate_ab_query(
    client: ChatClient,
    question: str,
    *,
    vertical: str,
    arm: TranslateArm,
    retry_budget: int = 3,
) -> StructuredQuery:
    """Translate one question through the production ``_translate`` for ``arm``; return the RAW
    ``StructuredQuery`` (pre-Phase-B-seam) that the SD-1 metric scores. Loads the vertical's
    ontology metadata + builds the object-type index the same way ``answer_question`` does."""
    meta = load_ontology_meta(vertical)
    type_index = {t.name: t for t in meta.object_types}
    return await _translate(
        client, question, vertical, meta, type_index, retry_budget=retry_budget, arm=arm
    )
