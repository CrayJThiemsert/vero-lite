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
* ``Expected.{affected_primary_key, action_keywords}`` (+ the PR2 precision add-ons
  ``forbidden_primary_keys`` / ``forbidden_keywords``) are the **β headline** scoring
  fields (the entity + action class the model owns in the procedure path);
  ``canonical_handler`` + ``acceptable_handlers`` drive the **tiered α probe**
  (reactive-path handler-selection classified canonical / acceptable /
  forbidden-or-other — PLAN-0022 Step 1, replacing the flat ``valid_handlers``;
  see :mod:`benchmarks.procedure_baseline.grader`); ``payload_contains`` is
  **advisory**. The three lanes never contaminate each other (PLAN-0019 Part B
  hardening, Cray-ratified 2026-06-09).
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
    LLM proposal is graded); ``watch`` routes to human review (a bare
    ``human_task`` today; a ``gated`` proposal per ADR-0019 once PLAN-0022
    Phase 2 lands); ``ok`` is a no-op. Same values as the engine's
    ``services.engine.procedures.verdict.Verdict`` — the band math is delegated
    there (the PLAN-0022 single shared definition).
    """

    BREACH = "breach"
    WATCH = "watch"
    OK = "ok"


class SiblingReading(BaseModel):
    """A non-breaching sibling entity's reading, injected into the event as a
    **distractor** — the model must identify the breached ``primary_key`` and must
    NOT name this one as affected (PLAN-0019 Part B PR2 multi-entity hardening). The
    ``unit`` / ``parameter`` are inherited from the parent :class:`Scenario` (same
    domain); only the identity + value differ.
    """

    model_config = ConfigDict(extra="forbid")

    primary_key: str = Field(..., min_length=1, description="The decoy entity's PK")
    measured_value: float = Field(..., description="A safe-side (non-breaching) reading")


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
    distractors: list[SiblingReading] = Field(
        default_factory=list,
        description="Non-breaching sibling readings injected into the event as decoys (PR2 "
        "multi-entity hardening); the model must pick the breached primary_key, not these.",
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
    — the α handler-tier probe alone does not make a breach item gradable. The
    ``forbidden_*`` fields are β-headline **precision** add-ons (PR2 hardening): they
    sharpen the entity + action-class checks on multi-entity / near-miss scenarios.
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
    forbidden_primary_keys: list[str] | None = Field(
        default=None,
        description="β HEADLINE precision (PR2): NONE of these distractor PKs may appear in the "
        "model's affected_entities — the multi-entity decoy-discrimination check",
    )
    canonical_handler: str | None = Field(
        default=None,
        description="α PROBE tier 1 (not a headline gate): the single correct ontology "
        "action_type for the breach, e.g. start_emergency_aerator / restart / hold "
        "(PLAN-0022 Step 1, replacing the flat valid_handlers)",
    )
    acceptable_handlers: list[str] | None = Field(
        default=None,
        description="α PROBE tier 2: benign defensible alternative handlers — not wrong, "
        "just not canonical (e.g. inspect for a cold-chain excursion, "
        "increase_water_exchange for a DO crash — the PLAN-0020 REPORT-verified benign "
        "divergences). forbidden stays expressed by forbidden_keywords (SD-4=a)",
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
    forbidden_keywords: list[str] | None = Field(
        default=None,
        description="β HEADLINE precision (PR2): the near-miss action verb(s) must NOT appear in "
        "the proposal TITLE — the model must not recommend the decoy action",
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
