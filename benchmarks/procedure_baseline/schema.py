"""Dataset item models for the procedure-baseline benchmark (PLAN-0019 B-β).

The human-authored ground-truth schema (SD-B2 coverage). One :class:`Dataset`
per vertical YAML file; each :class:`BenchmarkItem` carries a self-contained
:class:`Scenario` (the synthetic reading + its threshold, so the deterministic
disposition is computable without the DB/orchestrator) and an :class:`Expected`
ground-truth key the grader scores the LLM proposal against.

The two halves are graded differently (SD-B1):

* ``Scenario.{measured_value, threshold, direction, watch_margin}`` drive the
  **deterministic** breach/watch/ok disposition (``crosses_threshold`` — the
  ~100% sanity check, reported separately).
* ``Expected.{affected_primary_key, action_keywords}`` are the **β headline**
  scoring fields (the entity + action class the model owns in the procedure path);
  ``valid_handlers`` is the **α probe** (reactive-path handler-selection, reported
  on its own lane — see :mod:`benchmarks.procedure_baseline.grader`);
  ``payload_contains`` is **advisory**. The three lanes never contaminate each
  other (PLAN-0019 Part B hardening, Cray-ratified 2026-06-09).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Direction = Literal["below", "above"]
"""Breach direction, mirroring ``crosses_threshold``: ``below`` = ``measured <=
threshold`` (an aquaculture DO crash); ``above`` = ``measured >= threshold`` (an
energy / cold-chain over-temperature). Default ``above`` matches the engine's
fail-safe for an unset/garbled direction."""


class Disposition(StrEnum):
    """The three-way verdict a ``judge`` (``evaluate``) step assigns. ``breach``
    is the only disposition that fires an ``action`` (and thus the only one whose
    LLM proposal is graded); ``watch`` routes to a human task; ``ok`` is a no-op.
    """

    BREACH = "breach"
    WATCH = "watch"
    OK = "ok"


class Scenario(BaseModel):
    """One synthetic reading + the threshold context needed to classify it.

    Self-contained (carries its own ``threshold`` / ``direction`` /
    ``watch_margin``) so the deterministic disposition is computable per item
    without the DB or the orchestrator — the harness bypasses both to isolate the
    LLM variable (handoff §3).
    """

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(..., min_length=1)
    entity_type: str = Field(
        ..., min_length=1, description="Ontology object_type, e.g. Pond / Asset / Shipment"
    )
    primary_key: str = Field(
        ..., min_length=1, description="The affected entity's PK (ground truth)"
    )
    measured_value: float
    unit: str = Field(..., min_length=1)
    threshold: float
    direction: Direction = "above"
    watch_margin: float | None = Field(
        default=None,
        ge=0.0,
        description="Width of the watch band just inside the safe side of the breach floor; "
        "None collapses the watch band (everything not-breach is ok).",
    )
    context: dict[str, Any] = Field(
        default_factory=dict, description="Extra event fields fed to the model verbatim"
    )


class Expected(BaseModel):
    """The ground-truth key the grader scores against.

    ``disposition`` + ``action_expected`` are the deterministic sanity fields
    (must agree with :func:`grader.classify_disposition`); the remaining fields
    are the LLM-graded checks, each scored only when present (an item grades on
    exactly the fields it declares). A breach item must declare at least one
    **headline scoring** field (``affected_primary_key`` and/or ``action_keywords``)
    — the α ``valid_handlers`` probe alone does not make a breach item gradable.
    """

    model_config = ConfigDict(extra="forbid")

    disposition: Disposition
    action_expected: bool = Field(
        ..., description="True iff a breach (the engine proposes an action only on breach)"
    )
    affected_primary_key: str | None = Field(
        default=None,
        description="β HEADLINE: a proposed affected_entities[*].primary_key must match",
    )
    valid_handlers: list[str] | None = Field(
        default=None,
        description="α PROBE (not a headline gate): suggested_handler must be one of these — "
        "the correct ontology action_type(s) for the breach, e.g. [restart] / "
        "[start_emergency_aerator] / [hold]",
    )
    payload_contains: dict[str, Any] | None = Field(
        default=None,
        description="ADVISORY: handler_payload must contain each key/value (subset match)",
    )
    action_keywords: list[str] | None = Field(
        default=None,
        description="β HEADLINE 'action class': >=1 keyword must appear in "
        "title/description/rationale",
    )


class BenchmarkItem(BaseModel):
    """One graded scenario."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    scenario: Scenario
    expected: Expected


class Dataset(BaseModel):
    """One vertical's authored dataset file."""

    model_config = ConfigDict(extra="forbid")

    vertical: str = Field(..., min_length=1)
    procedure: str = Field(..., min_length=1, description="The procedure_id this dataset exercises")
    reading_parameter: str = Field(
        ...,
        min_length=1,
        description="The domain parameter the reading measures (e.g. dissolved_oxygen / "
        "temperature). Fed into the event so the model knows the domain — faithful to what "
        "a real ontology-projected event carries (B-β calibration, Cray-ratified 2026-06-08).",
    )
    threshold_note: str | None = Field(
        default=None, description="Provenance of the threshold/direction (grounding for review)"
    )
    items: list[BenchmarkItem] = Field(..., min_length=1)
