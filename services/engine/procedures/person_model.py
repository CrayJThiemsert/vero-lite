"""Generated Pydantic models from ontology YAML — do not edit by hand."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Person(BaseModel):
    model_config = ConfigDict(extra="forbid")
    person_id: str
    name: str
    roles: frozenset[str] = Field(min_length=1)
