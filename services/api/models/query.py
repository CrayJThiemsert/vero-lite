"""Request + response models for the NL-query API (PLAN-0013 Step 2).

The response surfaces the answer **plus its grounding receipt** — the
structured query the engine ran and the source object ids it read — so
the AC-nlquery "grounded, no canned answers" claim is verifiable from the
payload alone.
"""

from typing import Any

from pydantic import BaseModel, Field

from services.engine.nl_query import QueryOutcome, StructuredQuery


class NlQueryRequest(BaseModel):
    """An operator's plain-language operational question."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Plain-language question about the operational data",
    )


class NlQueryResponse(BaseModel):
    """A grounded NL answer and the evidence that backs it."""

    question: str = Field(..., description="The question that was asked")
    answer: str = Field(..., description="Natural-language answer, grounded in ontology data")
    grounded: bool = Field(
        ...,
        description="True iff the answer is backed by ≥1 source object (else a no-data answer)",
    )
    structured_query: StructuredQuery | None = Field(
        default=None,
        description="The structured query the engine ran (None if translation failed)",
    )
    source_object_type: str | None = Field(
        default=None, description="The ontology object type the answer was drawn from"
    )
    source_object_ids: list[str] = Field(
        default_factory=list,
        description="Primary keys of the source objects that grounded the answer",
    )
    source_objects: list[dict[str, Any]] = Field(
        default_factory=list, description="The source object records the answer was drawn from"
    )
    result_count: int = Field(
        default=0, description="How many objects matched the structured query"
    )
    outcome: QueryOutcome = Field(
        ...,
        description=(
            "Terminal state of the query: 'answered' | 'no_data' | 'clarify'. Distinct from "
            "`grounded` so a clarification request is never conflated with 'no records'"
        ),
    )
    phrased_by: str = Field(
        ...,
        description=(
            "Which arm authored `answer`: the live model's name, or 'deterministic' when a "
            "template did. Always present — arm identity is not conditional (PLAN-0093 AC-5)"
        ),
    )
    phrase_disclosure: str | None = Field(
        default=None,
        description=(
            "Set only when the LLM arm was attempted and did NOT author the answer (transport "
            "failure or empty response). None on a non-degraded path — this marks a DEGRADE, "
            "not determinism itself"
        ),
    )
