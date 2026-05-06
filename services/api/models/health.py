"""Health check response model."""

from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response from /health endpoint."""

    status: str = Field(..., description="Service status (ok / degraded / down)")
    timestamp: datetime = Field(..., description="Server time at response (UTC)")
    version: str = Field(..., description="Application version")
