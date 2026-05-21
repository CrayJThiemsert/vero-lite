"""Response models for the action-loop API (PLAN-0005 §6.7)."""

from typing import Any

from pydantic import BaseModel, Field


class ObjectListResponse(BaseModel):
    """A page of raw objects from a vertical DataAdapter."""

    object_type: str = Field(..., description="The ontology object type listed")
    count: int = Field(..., description="Number of objects returned")
    objects: list[dict[str, Any]] = Field(..., description="Raw object dicts from the adapter")


class RecommendationResponse(BaseModel):
    """A single RecommendedAction and its lifecycle status."""

    action_id: str = Field(..., description="Unique action identifier")
    title: str = Field(..., description="Short action title")
    description: str = Field(..., description="Why the action was recommended")
    vertical: str = Field(..., description="Originating vertical name")
    status: str = Field(..., description="Lifecycle status: proposed/approved/rejected/executed")
    confidence: float = Field(..., description="Recommender confidence in [0.0, 1.0]")
    requires_approval: bool = Field(..., description="Whether the action needs approval")
    suggested_handler: str = Field(..., description="Registered handler name for execution")


class RecommendationListResponse(BaseModel):
    """A list of current RecommendedActions."""

    count: int = Field(..., description="Number of recommendations")
    recommendations: list[RecommendationResponse] = Field(..., description="The recommendations")


class ExecuteResponse(BaseModel):
    """The outcome of executing an approved action."""

    action_id: str = Field(..., description="The executed action identifier")
    status: str = Field(..., description="Lifecycle status after execution")
    handler_receipt: dict[str, Any] = Field(..., description="Receipt returned by the handler")
