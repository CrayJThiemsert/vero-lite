"""NL operational-query API router (PLAN-0013 Step 2, OCT feature 2).

Exposes ``POST /query`` — a plain-language question is translated to a
bounded structured query over the ontology, executed against real
``/objects`` data, and phrased back grounded in the records read. The
engine (``services/engine/nl_query.py``) owns the translate→execute→phrase
flow; this router maps its :class:`NlAnswer` to the API response model.
"""

from fastapi import APIRouter

from services.api.config import settings
from services.api.models.query import NlQueryRequest, NlQueryResponse
from services.engine.llm import prompt_log
from services.engine.nl_query import PHRASED_BY_DETERMINISTIC, NlAnswer, answer_question

router = APIRouter(tags=["nl-query"])


def arm_of(phrased_by: str | None) -> str:
    """Which arm authored the text, as the prompt log records it (D6).

    ``phrased_by`` carries the MODEL NAME when the LLM authored and the sentinel
    when the template did, so the log's coarse ``arm`` is derived rather than
    stored twice — the two can never disagree.
    """
    return "deterministic" if phrased_by in (None, PHRASED_BY_DETERMINISTIC) else "llm"


def _to_response(answer: NlAnswer) -> NlQueryResponse:
    return NlQueryResponse(
        question=answer.question,
        answer=answer.answer,
        grounded=answer.grounded,
        structured_query=answer.query,
        source_object_type=answer.source_object_type,
        source_object_ids=answer.source_object_ids,
        source_objects=answer.source_objects,
        result_count=answer.result_count,
        # PLAN-0093 AC-2/AC-5: `outcome` and the arm pair were computed by the
        # engine and then dropped here — a consumer could not tell a template-
        # phrased answer from a model-phrased one over the same records.
        outcome=answer.outcome,
        phrased_by=answer.phrased_by,
        phrase_disclosure=answer.phrase_disclosure,
    )


@router.post("/query", response_model=NlQueryResponse)
async def nl_query(request: NlQueryRequest) -> NlQueryResponse:
    """Answer a plain-language operational question, grounded in ontology data."""
    answer = await answer_question(request.question, settings.oct_vertical)
    # PLAN-0100 Step 7 — recorded AFTER the answer so `outcome` and `arm` describe
    # what actually happened, including a degrade to the deterministic arm. No-op
    # unless PROMPT_LOG_ENABLED, and never raises (see prompt_log.record).
    prompt_log.record(
        route="/query",
        vertical=settings.oct_vertical,
        text=request.question,
        # The model this route ACTUALLY routes to. It used to record
        # `ollama_default_model` (gemma4:26b, the ADR-001 baseline), which nothing
        # on this path reads: nl_query builds its client from
        # `recommender_model`. PLAN-0100 Step 11 caught the two disagreeing in one
        # row — the log said gemma4:26b while the same response reported
        # `phrased_by: "gpt-oss:20b"` (D-2). A wrong name is worse than a blank
        # one here, because gemma4:26b IS present on the box, so an auditor
        # reading the log has no reason to doubt it.
        model=settings.recommender_model,
        outcome=answer.outcome or "unknown",
        arm=arm_of(answer.phrased_by),
    )
    return _to_response(answer)
