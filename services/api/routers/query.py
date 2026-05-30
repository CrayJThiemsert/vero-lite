"""NL operational-query API router (PLAN-0013 Step 2, OCT feature 2).

Exposes ``POST /query`` — a plain-language question is translated to a
bounded structured query over the ontology, executed against real
``/objects`` data, and phrased back grounded in the records read. The
engine (``services/engine/nl_query.py``) owns the translate→execute→phrase
flow; this router maps its :class:`NlAnswer` to the API response model.
"""

from fastapi import APIRouter

from services.api.models.query import NlQueryRequest, NlQueryResponse
from services.engine.nl_query import NlAnswer, answer_question

router = APIRouter(tags=["nl-query"])

_VERTICAL = "energy"


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
    )


@router.post("/query", response_model=NlQueryResponse)
async def nl_query(request: NlQueryRequest) -> NlQueryResponse:
    """Answer a plain-language operational question, grounded in ontology data."""
    answer = await answer_question(request.question, _VERTICAL)
    return _to_response(answer)
