"""Procedure / Step / Agent SPEC models + loader (ADR-016 D2; PLAN-0019 Part A).

The per-vertical SPEC layer the Procedure engine runs — authored in
``verticals/<name>/procedures.yaml`` alongside (but separate from) the ADR-008
ontology YAML. The six-``object_types`` ontology is untouched: procedures and
agents are a distinct spec layer (ADR-016 D2 / D6).

The shapes are the ADR-016 D2 contract:

* ``Procedure`` — a ``goal`` (a runtime LLM directive, D5), the ``Agent`` that
  runs it (``run_by``), a ``trigger``, and a LINEAR, set-valued list of ``Step``s.
* ``Step`` — its ``kind`` of work and, for ``action`` steps ONLY, an ``autonomy``
  (default ``gated``; D3 safe-by-default). ``query`` / ``evaluate`` never gate;
  ``human_task`` is inherently human. An ``evaluate`` step MAY author its
  deterministic band (``threshold`` / ``direction`` / ``watch_margin``) and an
  ``action`` step MAY declare a handler-tier taxonomy (``tiers``) — all optional,
  added by PLAN-0022 Step 3 (SD-5=a); absent fields preserve today's behaviour
  byte-for-byte (AC-9).
* ``Agent`` — the actor: a bound local LLM model (default ``gpt-oss:20b``,
  ADR-001), an ``autonomy_ceiling``, and an ``allowed`` allowlist that bounds
  blast radius (D3).

Only ``trigger: manual`` is RUNNABLE in Phase 1 (PLAN-0019 L-1); a ``schedule``
spec still *loads* (the orchestrator refuses to run it — deferred to a PLAN-0010
reuse). The loader validates shape + cross-references (``run_by`` resolves to a
defined agent; ids are unique) so a malformed spec fails loudly at load, not
mid-run. The YAML house style mirrors the ontology loader
(``services/engine/ontology_meta.py``): ``agents`` / ``procedures`` are maps
keyed by id.
"""

from __future__ import annotations

from collections.abc import Iterator
from decimal import Decimal
from enum import StrEnum
from itertools import pairwise
from pathlib import Path
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from ruamel.yaml import YAML

from services.engine.procedures.prose_lint import governance_prose_lint

ThresholdDirection = Literal["below", "above"]
"""Breach direction for an ``evaluate`` step's authored threshold, mirroring
``recommender.crosses_threshold``: ``below`` = ``measured <= threshold`` (an
aquaculture DO crash); ``above`` = ``measured >= threshold`` (an energy /
cold-chain over-temperature). PLAN-0022 Step 3 (SD-5=a)."""


class StepKind(StrEnum):
    """The type of work a step performs (ADR-016 D2)."""

    QUERY = "query"
    EVALUATE = "evaluate"
    ACTION = "action"
    HUMAN_TASK = "human_task"


class Autonomy(StrEnum):
    """Autonomy level — an axis of ``action`` steps ONLY (ADR-016 D3)."""

    AUTO = "auto"
    GATED = "gated"


class OnFailure(StrEnum):
    """What a failed step does to the run (ADR-016 D4 fail-and-divert)."""

    FAIL = "fail"
    ESCALATE_TO_HUMAN = "escalate_to_human"


class Trigger(StrEnum):
    """How a procedure run starts. Only ``manual`` is runnable in Phase 1 (L-1)."""

    MANUAL = "manual"
    SCHEDULE = "schedule"


class BandSource(StrEnum):
    """How an ``evaluate`` step's deterministic band is authored (ADR-016 D2-A3).

    ``env`` = the band comes from the runtime env (``OCT_RECOMMEND_THRESHOLD`` +
    direction) with NO in-file ``threshold`` field (energy / supply_chain);
    ``in_file`` = the band is authored on the ``Step`` itself
    (``threshold`` / ``direction`` / ``watch_margin``; aquaculture / procurement).
    """

    ENV = "env"
    IN_FILE = "in_file"


class GateKind(StrEnum):
    """The kind of deterministic decision a step's ``decision_condition`` gates on —
    exactly the six kinds observed across the N=4 instrumented verticals (ADR-016
    D2-A3; no speculative future kinds, Rule-of-Three). A 5th vertical with a new
    shape extends this enum additively (amendment OQ-A1)."""

    ENV_BAND = "env_band"
    IN_FILE_BAND = "in_file_band"
    RULE_GATE = "rule_gate"
    SCORED_RULE = "scored_rule"
    DOA_TIER = "doa_tier"
    NONE = "none"


class StepInput(BaseModel):
    """A step's input source (ADR-016 D4; PLAN-0019 A-ζ-prep named-input).

    ``from`` names the prior step whose output set feeds this step (default = the
    immediately preceding step). ``where`` is a field-equality filter that narrows
    that set — an entity is kept iff ``entity[field] == value`` for **every** pair,
    so the set-valued breach/watch/ok fan-out is just ``where: {verdict: breach}``
    on the evaluate step's output. A non-mapping entity never matches a ``where``
    (it has no fields). Linear-only: ``from`` must name an EARLIER step
    (forward / unknown references are rejected at pre-flight by ``validate_runnable``).
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    from_step: str | None = Field(
        default=None,
        alias="from",
        description="step_id whose output feeds this step; default = the immediately prior step",
    )
    where: dict[str, Any] | None = Field(
        default=None,
        description="field-equality filter: keep entities where entity[field] == value (all pairs)",
    )


class StepTiers(BaseModel):
    """Canonical / acceptable / forbidden handler tiers for an ``action`` step
    (PLAN-0022 Step 3; SD-5=a).

    Mirrors the benchmark grader's tier taxonomy (PLAN-0022 Step 1) so product
    config and benchmark ground truth share one source of truth: ``canonical``
    is the single correct handler for the step's situation; ``acceptable`` are
    benign defensible alternatives; ``forbidden`` are handlers that must never
    be the recommendation. This is a TAXONOMY declaration, not an execution
    allowlist — what an agent may actually invoke stays bounded by
    ``Agent.allowed.action_handlers`` (ADR-016 D3, unchanged per ADR-0019).
    """

    model_config = ConfigDict(extra="forbid")

    canonical: str | None = Field(
        default=None, description="the single correct handler for this step's situation"
    )
    acceptable: list[str] = Field(
        default_factory=list, description="benign defensible alternative handlers"
    )
    forbidden: list[str] = Field(
        default_factory=list, description="handlers that must never be the recommendation"
    )


class DecisionCondition(BaseModel):
    """The discriminated decision-condition facet of a ``Step`` (ADR-016 D2-A3).

    ``gate_kind`` names HOW the step decides (one of the six observed kinds).
    ``band_source`` is set iff ``gate_kind`` is a band kind (``env_band`` /
    ``in_file_band``); ``env_var`` names the env band's source only when
    ``band_source == env``. An ``in_file_band`` POINTS AT the existing typed
    ``threshold`` / ``direction`` / ``watch_margin`` on the ``Step`` — it does NOT
    re-store those values (single source of truth, no drift; D2-A2/A3).
    """

    model_config = ConfigDict(extra="forbid")

    gate_kind: GateKind
    band_source: BandSource | None = Field(
        default=None,
        description="present iff gate_kind in {env_band, in_file_band} (D2-A3)",
    )
    env_var: str | None = Field(
        default=None,
        description="the env var carrying the band; only with band_source == env",
    )
    note: str | None = Field(default=None, description="optional human prose")

    @model_validator(mode="after")
    def _validate_band_source(self) -> Self:
        """band_source set iff gate_kind is a band kind; env_var only with env (D2-A3)."""
        is_band = self.gate_kind in (GateKind.ENV_BAND, GateKind.IN_FILE_BAND)
        if is_band != (self.band_source is not None):
            raise ValueError(
                f"decision_condition: band_source must be set iff gate_kind is a band "
                f"kind (env_band/in_file_band); got gate_kind '{self.gate_kind.value}', "
                f"band_source {self.band_source!r} — ADR-016 D2-A3"
            )
        if self.env_var is not None and self.band_source is not BandSource.ENV:
            raise ValueError(
                f"decision_condition: env_var applies only with band_source == env; "
                f"got band_source {self.band_source!r} — ADR-016 D2-A3"
            )
        return self


class StepFacet(BaseModel):
    """Descriptive 5-facet metadata for a ``Step`` (ADR-016 D2 Amendment 2026-06-25).

    NON-AUTHORITATIVE for runtime — the engine reads but does NOT consume it
    (D2-A2/A4). The Hybrid shape (D2-A2): the net-new machine-readable signal
    (``decision_condition`` + ``llm_assist``) is typed; the three facets the
    ``Step`` already types are kept as optional non-authoritative ``str`` notes so
    the catalog's uniform 5-facet reading is preserved without re-owning structured
    values (the typed ``Step`` fields stay source of truth). Note ``StepFacet.input``
    is a prose ``str`` note — distinct from ``Step.input: StepInput``; the type
    difference is intentional.
    """

    model_config = ConfigDict(extra="forbid")

    decision_condition: DecisionCondition | None = None
    llm_assist: str | None = Field(
        default=None,
        description="what (if anything) the LLM drafts/summarises — advisory only; "
        "the net-new facet not modelled elsewhere today (D2-A2).",
    )
    input: str | None = Field(default=None, description="non-authoritative note (D2-A2)")
    output: str | None = Field(default=None, description="non-authoritative note (D2-A2)")
    governance: str | None = Field(default=None, description="non-authoritative note (D2-A2)")


# --- AT-2 governance content (ADR-0025 D2/D3 — the managerial layer) -------------
#
# The typed, HUMAN-AUTHORED, AUTHORITATIVE home for the AT-2 (managerial) archetype's
# governance content: a tiered delegation-of-authority (DOA) ladder, a scored selection
# rule, a per-criterion compliance gate, and procedure-level separation-of-duties (SoD).
# These are the source of truth (like ``Step.threshold``), POINTED AT by ``gate_kind``
# (D2-A3) — never carried in the non-authoritative ``facet`` (D2-A4). Every value is
# human-authored (D4: registered in ``draft.GOVERNANCE_FIELDS``, never declared on a draft
# type) — never model-emitted.
#
# Bypass is made UNREPRESENTABLE, not defaulted-false (D3): there is no field that skips a
# gate, lowers a tier, or waives compliance/SoD — the closed ``RelaxableConstraint`` enum
# cannot name compliance/SoD, ``ComplianceRule.blocks_po`` is ``Literal[True]``, the waiver
# always requires a justification, and the DOA ladder is a total, strictly-monotonic cover.
# The AMOUNT- / PRINCIPAL- / ROLE-RANK-dependent SEMANTIC checks (the resolved-tier strict
# escalation of the waiver; requester-principal != approver-principal) are RUN-time
# enforcement on the deferred A2 path (ADR-0025 D6 / OQ-A=A1, ratified s85; AC-13-ALT) —
# author time enforces only the structural invariants below (no principal/role-rank model
# exists in the engine yet).
#
# Rule-of-Three caveat (ADR-0025 D2 / LOCKED-2): AT-2 is N=1
# (``procurement.emergency_sourcing_round``). These models are scoped tightly to that one
# observed signature and are PROVISIONAL-UNTIL-N>=2; genericizing them is gated on the D7
# CI re-trigger. v1 boundary (OQ-A=A1): author + render only — they render read-only.

RoleId = str
"""A human approval-role identifier (e.g. ``dept_head``) — a human-authored binding."""

StepId = str
"""A reference to a ``Step.step_id`` within the same procedure."""

PersonId = str
"""A canonical principal-identity key (e.g. ``alice``) — the resolved-principal identity
SoD compares at run time (ADR-0026 D1). A bare ``person_id`` match is the first of the two
OQ-3=(c) alias-collapse triggers. Human-authored."""


class ComplianceCriterion(StrEnum):
    """The per-criterion compliance checks an AT-2 ``rule_gate`` evaluates (ADR-0025 D2),
    scoped to the observed procurement signature (provisional-until-N>=2)."""

    AVL = "avl"
    TAX = "tax"
    CERT = "cert"
    SANCTIONS = "sanctions"
    SINGLE_SOURCE = "single_source"


class SourcePolicy(StrEnum):
    """The default supplier-selection policy for an AT-2 ``scored_rule`` (ADR-0025 D2)."""

    ON_CONTRACT = "on_contract"
    OFF_CONTRACT = "off_contract"


class ExceptionPolicy(StrEnum):
    """The logged-exception policy when the default source cannot be used (ADR-0025 D2)."""

    RFQ_AVL_LOGGED = "rfq_avl_logged"


class RelaxableConstraint(StrEnum):
    """The sourcing constraints an emergency waiver MAY relax (ADR-0025 D3) — a CLOSED set
    that CANNOT name compliance or separation-of-duties (those are non-waivable by type)."""

    THREE_BID = "three_bid"
    SOLE_SOURCE = "sole_source"


class DoaTier(BaseModel):
    """One tier of a delegation-of-authority ladder: a spend within this tier's half-open
    band ``[min_amount, next_min)`` routes to ``approver_role`` (ADR-0025 D2). Money is
    ``Decimal``, never ``float`` (no binary-float rounding on an authority threshold)."""

    model_config = ConfigDict(extra="forbid")

    min_amount: Decimal = Field(ge=0, description="inclusive spend floor of this tier (Decimal)")
    approver_role: RoleId = Field(description="role authorised to approve within this tier")
    note: str = Field(
        default="",
        description="optional human note for this tier — NON-AUTHORITATIVE free-text (never a "
        "gate input; scoped-prose-lint-guarded so a ฿-amount/role token cannot be smuggled in, "
        "ADR-0025 D4). The authoritative tier is min_amount + approver_role.",
    )


class EmergencyWaiverPolicy(BaseModel):
    """An emergency waiver that ESCALATES the approver and forces a logged justification but
    NEVER skips a gate (ADR-0025 D3). Bypass is unrepresentable: no field removes a gate,
    lowers a tier, or waives compliance/SoD — ``relaxes`` is a closed enum that cannot name
    them, and ``requires_justification`` is ``Literal[True]``. (The resolved-tier strict
    escalation of ``escalate_to`` is a RUN-time A2 check — it needs the spend->tier
    resolution + a role-rank model that does not exist yet; OQ-A=A1.)"""

    model_config = ConfigDict(extra="forbid")

    relaxes: list[RelaxableConstraint] = Field(
        min_length=1,
        description="the sourcing constraints this waiver relaxes (closed; never compliance/SoD)",
    )
    escalate_to: RoleId = Field(description="the higher authority approval escalates to")
    requires_justification: Literal[True] = Field(
        default=True,
        description="a waiver ALWAYS forces a logged justification (unrepresentable to omit)",
    )
    justification: str = Field(
        default="",
        description="optional human-authored standing rationale for this waiver — "
        "NON-AUTHORITATIVE free-text (the per-invocation run-time logged justification is "
        "separate; this is the authored rationale, scoped-prose-lint-guarded so a "
        "฿-amount/weight/role token cannot be smuggled in, ADR-0025 D4 / D-129).",
    )


class DoaLadder(BaseModel):
    """A tiered delegation-of-authority ladder (the ``doa_tier`` content, ADR-0025 D2/D3).

    Total + unambiguous by construction: a single ``currency`` (one field — multiple
    currencies are unrepresentable, D3); ``tiers`` non-empty with the first floor at 0 and
    strictly-increasing floors, so every spend >= 0 maps to exactly one half-open band
    ``[min_i, min_{i+1})`` (top tier unbounded)."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["doa_tier"] = "doa_tier"
    currency: str = Field(min_length=1, description="ISO currency for every tier (single, D3)")
    tiers: list[DoaTier] = Field(min_length=1, description="the DOA tiers, ascending by floor")
    emergency_waiver: EmergencyWaiverPolicy = Field(description="the escalate-never-skip waiver")

    @model_validator(mode="after")
    def _validate_ladder(self) -> Self:
        """Total-cover, strictly-monotonic ladder (D3): first floor 0, no equal/overlapping
        floors. Single currency is structural (one field). The resolved-tier strict
        escalation is an A2 run check (needs a role-rank model)."""
        floors = [t.min_amount for t in self.tiers]
        if floors[0] != 0:
            raise ValueError(
                f"DoaLadder: the first tier's min_amount must be 0 (total cover from zero "
                f"spend); got {floors[0]} — ADR-0025 D3"
            )
        if any(nxt <= cur for cur, nxt in pairwise(floors)):
            raise ValueError(
                f"DoaLadder: tier min_amount must be STRICTLY increasing (no overlap / equal "
                f"thresholds); got {floors} — ADR-0025 D3"
            )
        return self


class ScoredCriterion(BaseModel):
    """One weighted criterion of a scored selection rule (ADR-0025 D2)."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, description="the criterion name (human prose label)")
    weight: Decimal = Field(description="the criterion's weight in the scored selection (Decimal)")
    note: str = Field(
        default="",
        description="optional human note for this criterion — NON-AUTHORITATIVE free-text "
        "(never a gate input; scoped-prose-lint-guarded so a weight/amount cannot be smuggled "
        "in, ADR-0025 D4). The authoritative values are name + weight.",
    )


class ScoredRule(BaseModel):
    """The deterministic, human-authored supplier-selection rule (the ``scored_rule``
    content, ADR-0025 D2). The LLM only summarises quotes — selection is this rule."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["scored_rule"] = "scored_rule"
    criteria: list[ScoredCriterion] = Field(min_length=1, description="the weighted criteria (>=1)")
    default_source: SourcePolicy = Field(description="the default supplier-selection policy")
    exception_policy: ExceptionPolicy = Field(description="the logged-exception policy")


class ComplianceRule(BaseModel):
    """One per-criterion compliance rule that ALWAYS blocks the PO on failure (ADR-0025
    D2/D3). ``blocks_po`` is ``Literal[True]`` — a non-blocking 'compliance' rule is
    unrepresentable (it would not be a gate)."""

    model_config = ConfigDict(extra="forbid")

    criterion: ComplianceCriterion = Field(description="the compliance criterion checked")
    spec: str = Field(
        min_length=1,
        description="the human-authored predicate for this criterion (rendered read-only in "
        "v1; evaluated on the deferred A2 run path)",
    )
    blocks_po: Literal[True] = Field(
        default=True, description="a compliance rule ALWAYS blocks the PO on failure (D3)"
    )


class ComplianceGate(BaseModel):
    """A per-criterion compliance gate (the ``rule_gate`` content, ADR-0025 D2)."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["rule_gate"] = "rule_gate"
    rules: list[ComplianceRule] = Field(min_length=1, description="the per-criterion rules (>=1)")


AT2Governance = Annotated[DoaLadder | ScoredRule | ComplianceGate, Field(discriminator="kind")]
"""The discriminated AT-2 governance-content union, keyed to a step's ``gate_kind`` via the
``kind`` literal (ADR-0025 D2). One field, not four bare ``Optional``s — a leaked variant
is one test, not four (Alternative 3 rejected)."""


class SoDConstraint(BaseModel):
    """A separation-of-duties constraint: the named steps MUST be performed by distinct
    principals (ADR-0025 D2). Author time enforces the STRUCTURAL form (>=2 distinct steps,
    each resolving to a real step — see ``Procedure``) plus the step->required-role map's own
    integrity (no role named for a step outside this constraint); the resolved-PRINCIPAL
    distinctness (fail-closed on alias-collapse) is the run check ADR-0026 D4 adds — it
    resolves each constrained step's ``required_role`` to a ``Person`` and fails closed if any
    is unresolvable or two collapse to one human."""

    model_config = ConfigDict(extra="forbid")

    distinct_steps: frozenset[StepId] = Field(
        min_length=2, description="step_ids that must be performed by distinct principals (>=2)"
    )
    required_roles: dict[StepId, RoleId] = Field(
        default_factory=dict,
        description="step->required-role map (ADR-0026 D2; OQ-1=(a), SD-1=(b)): the RoleId each "
        "constrained step requires, so the run-check resolves step -> required_role -> Person. "
        "Human-author-only (H). Keys must be among distinct_steps; a constrained step left "
        "unmapped is unresolvable -> the run-check fails closed (ADR-0026 D4).",
    )

    @model_validator(mode="after")
    def _validate_required_roles(self) -> Self:
        """A ``required_roles`` key may only name a step this constraint covers — a role bound
        to a step outside ``distinct_steps`` is an authoring error (ADR-0026 D2). (Coverage of
        every constrained step is NOT forced here: a partial/empty map keeps author-time load
        backward-compatible; an unmapped constrained step fails closed at run time, D4.)"""
        dangling = sorted(self.required_roles.keys() - self.distinct_steps)
        if dangling:
            raise ValueError(
                f"SoDConstraint: required_roles names step_id(s) {dangling} not in "
                f"distinct_steps {sorted(self.distinct_steps)} — ADR-0026 D2"
            )
        return self


class Step(BaseModel):
    """One step of a Procedure (ADR-016 D2; threshold/tier config per PLAN-0022 Step 3)."""

    model_config = ConfigDict(extra="forbid")

    step_id: str
    name: str
    description: str = ""
    kind: StepKind
    autonomy: Autonomy | None = Field(
        default=None,
        description="action steps ONLY; default gated. Must be unset for non-action kinds (D3).",
    )
    on_failure: OnFailure = OnFailure.FAIL
    input: StepInput | None = Field(
        default=None,
        description="input source: a named prior step + optional field-equality filter (D4)",
    )
    output: str | None = Field(default=None, description="produced object set / artifact name")
    handler: str | None = Field(
        default=None,
        description="registered action-handler to invoke; action steps only (allowlist-checked).",
    )
    threshold: float | None = Field(
        default=None,
        description="authored breach floor/ceiling; evaluate steps only (PLAN-0022 Step 3). "
        "Optional — absent keeps the step's band NL-only as today (AC-9).",
    )
    direction: ThresholdDirection | None = Field(
        default=None,
        description="breach direction for `threshold` (crosses_threshold semantics); "
        "evaluate steps only, requires threshold.",
    )
    watch_margin: float | None = Field(
        default=None,
        ge=0.0,
        description="width of the ambiguity band just inside the safe side of the breach "
        "floor — the escalate-to-human zone (ADR-0019). Evaluate steps only, requires "
        "threshold. Absent collapses the watch band (preserves today's behaviour, AC-9).",
    )
    tiers: StepTiers | None = Field(
        default=None,
        description="canonical/acceptable/forbidden handler-tier taxonomy; action steps "
        "only (PLAN-0022 Step 3, SD-5=a). A taxonomy mirror, not an execution allowlist.",
    )
    facet: StepFacet | None = Field(
        default=None,
        description="descriptive 5-facet metadata; optional; non-authoritative for runtime "
        "(ADR-016 D2 Amendment 2026-06-25 / D2-A2). The engine reads but does not consume it.",
    )
    governance_content: AT2Governance | None = Field(
        default=None,
        description="AUTHORITATIVE AT-2 governance content (DOA ladder / scored rule / "
        "compliance gate), discriminated by `kind` to match this step's gate_kind (ADR-0025 "
        "D2). Human-author-only (never on a draft type, D4); the gate_kind POINTS AT it — it "
        "is never stored in the non-authoritative facet (D2-A4).",
    )

    @model_validator(mode="after")
    def _validate_step(self) -> Self:
        """Enforce the per-kind field invariants: ``autonomy`` / ``handler`` / ``tiers``
        are axes of ``action`` steps only (ADR-016 D3; PLAN-0022 SD-5=a), and the
        authored band (``threshold`` / ``direction`` / ``watch_margin``) belongs to
        ``evaluate`` steps only (PLAN-0022 Step 3).

        ``action`` defaults to ``gated`` (safe-by-default). ``query`` / ``evaluate``
        always run auto; ``human_task`` is inherently human. ``direction`` and
        ``watch_margin`` are meaningless without a ``threshold`` to band around, so
        a margin-without-floor spec fails loudly at load, not mid-run.
        """
        if self.kind is not StepKind.EVALUATE:
            for field_name in ("threshold", "direction", "watch_margin"):
                if getattr(self, field_name) is not None:
                    raise ValueError(
                        f"step '{self.step_id}': {field_name} applies to evaluate steps only "
                        f"(kind '{self.kind.value}' must not set it) — PLAN-0022 Step 3"
                    )
        elif (self.direction is not None or self.watch_margin is not None) and (
            self.threshold is None
        ):
            raise ValueError(
                f"step '{self.step_id}': direction/watch_margin require a threshold "
                f"to band around — PLAN-0022 Step 3"
            )
        if self.kind is StepKind.ACTION:
            if self.autonomy is None:
                self.autonomy = Autonomy.GATED
            return self
        if self.autonomy is not None:
            raise ValueError(
                f"step '{self.step_id}': autonomy applies to action steps only "
                f"(kind '{self.kind.value}' must not set autonomy) — ADR-016 D3"
            )
        if self.handler is not None:
            raise ValueError(
                f"step '{self.step_id}': handler applies to action steps only "
                f"(kind '{self.kind.value}' must not set handler) — ADR-016 D3"
            )
        if self.tiers is not None:
            raise ValueError(
                f"step '{self.step_id}': tiers applies to action steps only "
                f"(kind '{self.kind.value}' must not set tiers) — PLAN-0022 SD-5"
            )
        return self


class AgentAllowed(BaseModel):
    """The allowlist that bounds an Agent's blast radius (ADR-016 D3)."""

    model_config = ConfigDict(extra="forbid")

    step_kinds: list[StepKind] = Field(default_factory=list)
    action_handlers: list[str] = Field(
        default_factory=list, description="registered handler names this agent may invoke"
    )


class PrincipalAlias(BaseModel):
    """A human-authored declaration that several principal-identity keys denote the SAME
    human (the OQ-3=(c) declared alias chain; ADR-0026 D4, SD-2=(b) — a separate first-class
    LINK object, NOT a flat alias-set on ``Person``). Two principals collapse (and the SoD
    run-check fails closed) when they share a ``PrincipalAlias`` link — i.e. both ``person_id``s
    are in one alias's ``members``. The link-object shape (over a flat set) is the more
    extensible path: it folds into the OQ-6 N>=2 shared-identity re-trigger later.
    Human-author-only (H, ADR-0024 D3) — never model-emitted."""

    model_config = ConfigDict(extra="forbid")

    alias_id: str = Field(description="identifier of this declared alias group")
    members: frozenset[PersonId] = Field(
        min_length=2,
        description="the person_ids this alias declares to be the SAME human (>=2) — the second "
        "OQ-3 collapse trigger, beside a bare person_id (PK) match",
    )


class Person(BaseModel):
    """A first-class, human-authored principal identity — the resolvable human who holds
    approval role(s) (ADR-0026 D1/D2). Lives in the procedures spec layer beside ``Agent`` (the
    MACHINE actor that *runs* a procedure), following ADR-0008 ontology-grammar conventions; it
    supersedes the procurement role-label near-misses (``ApprovalTier.approver_role`` /
    ``PurchaseOrder.approver_chain``) — those point at a ``Person``, they do not re-store the
    identity. Human-author-only (H, ADR-0024 D3) — a principal is never model-emitted."""

    model_config = ConfigDict(extra="forbid")

    person_id: PersonId = Field(
        description="canonical identity key (PK) — the resolved-principal identity SoD compares "
        "(ADR-0026 D1); a bare PK match is the first OQ-3 collapse trigger"
    )
    name: str = Field(description="the human's name (display)")
    roles: frozenset[RoleId] = Field(
        min_length=1,
        description="the approval role(s) this principal holds (>=1) — the role->principal "
        "binding the step->required-role map resolves against (ADR-0026 D2; OQ-1=(a))",
    )


class Agent(BaseModel):
    """The actor that RUNS a Procedure (ADR-016 D2)."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str
    name: str
    llm_model: str = Field(
        default="gpt-oss:20b", description="bound local Ollama model (ADR-001 Amendment 1)"
    )
    autonomy_ceiling: Autonomy = Field(
        default=Autonomy.GATED, description="max autonomy any step under this agent may exercise"
    )
    allowed: AgentAllowed = Field(default_factory=AgentAllowed)


def _at2_role_vocab(steps: list[Step]) -> frozenset[str]:
    """The typed approver-role vocabulary of an AT-2 procedure (every DOA tier's
    ``approver_role`` plus each waiver's ``escalate_to``) — the tokens that must live in the
    typed field, never in free-text (ADR-0025 D4 / PLAN-0042 Step 3)."""
    roles: set[str] = set()
    for step in steps:
        gc = step.governance_content
        if isinstance(gc, DoaLadder):
            roles.update(t.approver_role for t in gc.tiers)
            roles.add(gc.emergency_waiver.escalate_to)
    return frozenset(roles)


def _at2_free_text_surfaces(goal: str, steps: list[Step]) -> Iterator[tuple[str, str]]:
    """Yield ``(text, where)`` for every NON-AUTHORITATIVE AT-2 free-text surface the load
    gate scans: the goal, each governance-bearing step's description, the tier / criterion
    notes, and the waiver justification (ADR-0025 D4). NOT the typed authoritative fields and
    NOT a ``ComplianceRule.spec`` predicate (which legitimately holds comparison values)."""
    yield goal, "goal"
    for step in steps:
        gc = step.governance_content
        if gc is None:
            continue
        yield step.description, f"step '{step.step_id}' description"
        if isinstance(gc, DoaLadder):
            for tier in gc.tiers:
                yield tier.note, f"step '{step.step_id}' tier '{tier.approver_role}' note"
            yield gc.emergency_waiver.justification, f"step '{step.step_id}' waiver justification"
        elif isinstance(gc, ScoredRule):
            for crit in gc.criteria:
                yield crit.note, f"step '{step.step_id}' criterion '{crit.name}' note"


class Procedure(BaseModel):
    """A governed, multi-step operating procedure (ADR-016 D2)."""

    model_config = ConfigDict(extra="forbid")

    procedure_id: str
    title: str
    goal: str = Field(
        default="",
        description="freeform NL directive injected into the LLM system prompt at run time (D5)",
    )
    run_by: str = Field(..., description="agent_id of the Agent that runs this procedure")
    trigger: Trigger = Trigger.MANUAL
    steps: list[Step] = Field(..., min_length=1)
    terminal: str | None = Field(default=None, description="final step_id / produced artifact")
    separation_of_duties: list[SoDConstraint] = Field(
        default_factory=list,
        description="separation-of-duties constraints: each names >=2 steps that must be "
        "performed by distinct principals (ADR-0025 D2). Human-author-only (D4).",
    )

    @model_validator(mode="after")
    def _unique_step_ids(self) -> Self:
        ids = [s.step_id for s in self.steps]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            raise ValueError(f"procedure '{self.procedure_id}': duplicate step_id(s) {dupes}")
        return self

    @model_validator(mode="after")
    def _validate_separation_of_duties(self) -> Self:
        """Each SoD constraint must reference real steps of THIS procedure (ADR-0025 D2). The
        >=2-distinct-steps invariant is enforced structurally by ``SoDConstraint`` itself;
        this catches dangling step_id references (a typo'd SoD is an authoring error, not a
        silent no-op)."""
        known = {s.step_id for s in self.steps}
        for sod in self.separation_of_duties:
            dangling = sorted(sod.distinct_steps - known)
            if dangling:
                raise ValueError(
                    f"procedure '{self.procedure_id}': separation_of_duties references unknown "
                    f"step_id(s) {dangling} (known: {sorted(known)}) — ADR-0025 D2"
                )
        return self

    @model_validator(mode="after")
    def _validate_at2_free_text(self) -> Self:
        """Block load if a ฿-amount / weight / approver-role token is smuggled into an AT-2
        procedure's NON-AUTHORITATIVE free-text (the scoped prose-lint, ADR-0025 D4 /
        PLAN-0042 Step 3 / OQ-D). Runs ONLY for procedures carrying AT-2 governance content.
        Surfaces + role vocabulary: :func:`_at2_free_text_surfaces` / :func:`_at2_role_vocab`.
        The scoped variant omits the decision-verb / approval-phrase classes and the broad
        identifier catch, so a hand-authored note may legitimately say 'HUMAN approves' /
        'blocks the PO' or name a registered handler (finding 6)."""
        if all(s.governance_content is None for s in self.steps):
            return self
        roles = _at2_role_vocab(self.steps)
        for text, where in _at2_free_text_surfaces(self.goal, self.steps):
            found = governance_prose_lint(text, roles=roles) if text else []
            if found:
                v = found[0]
                raise ValueError(
                    f"procedure '{self.procedure_id}': AT-2 free-text {where} smuggles a "
                    f"governance value ({v.kind}: {v.match!r}) — author it in the typed field, "
                    f"not prose ({v.message}) — ADR-0025 D4"
                )
        return self


class VerticalProcedures(BaseModel):
    """A vertical's full ``procedures.yaml`` — its Agents, Procedures, and (ADR-0026 D1/D4) the
    human Principals + declared alias groups SoD resolves against."""

    model_config = ConfigDict(extra="forbid")

    vertical: str
    namespace: str | None = None
    version: int | None = None
    agents: list[Agent]
    procedures: list[Procedure]
    principals: list[Person] = Field(
        default_factory=list,
        description="the human principals the SoD run-check resolves against (ADR-0026 D1) — "
        "human-author-only (H, ADR-0024 D3), never generated",
    )
    principal_aliases: list[PrincipalAlias] = Field(
        default_factory=list,
        description="declared alias groups, the second OQ-3=(c) collapse trigger (ADR-0026 D4, "
        "SD-2=(b)) — human-author-only (H), never generated",
    )

    @model_validator(mode="after")
    def _validate_principals(self) -> Self:
        """Principal identity integrity (ADR-0026 D1/D4): person_ids are unique, and every
        alias member resolves to a defined ``Person`` (a typo'd alias is an authoring error,
        not a silent collapse that never fires)."""
        ids = [p.person_id for p in self.principals]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            raise ValueError(f"vertical '{self.vertical}': duplicate person_id(s) {dupes}")
        known = set(ids)
        for alias in self.principal_aliases:
            dangling = sorted(alias.members - known)
            if dangling:
                raise ValueError(
                    f"vertical '{self.vertical}': principal_alias '{alias.alias_id}' references "
                    f"unknown person_id(s) {dangling} (known: {sorted(known)}) — ADR-0026 D4"
                )
        return self

    @model_validator(mode="after")
    def _cross_refs(self) -> Self:
        agent_ids = [a.agent_id for a in self.agents]
        dup_agents = sorted({a for a in agent_ids if agent_ids.count(a) > 1})
        if dup_agents:
            raise ValueError(f"duplicate agent_id(s) {dup_agents}")
        proc_ids = [p.procedure_id for p in self.procedures]
        dup_procs = sorted({p for p in proc_ids if proc_ids.count(p) > 1})
        if dup_procs:
            raise ValueError(f"duplicate procedure_id(s) {dup_procs}")
        known = set(agent_ids)
        for proc in self.procedures:
            if proc.run_by not in known:
                raise ValueError(
                    f"procedure '{proc.procedure_id}': run_by '{proc.run_by}' is not a "
                    f"defined agent (known: {sorted(known)})"
                )
        return self


def procedures_path(vertical: str) -> Path:
    """Path to a vertical's procedures spec YAML."""
    return Path("verticals") / vertical / "procedures.yaml"


def _parse_procedure(procedure_id: str, raw: dict[str, Any]) -> Procedure:
    """Build a Procedure from its raw mapping; ``steps`` is an ORDERED list (linear)."""
    data = {k: v for k, v in raw.items() if k != "steps"}
    steps = [Step(**(s or {})) for s in (raw.get("steps") or [])]
    return Procedure(procedure_id=procedure_id, steps=steps, **data)


def parse_procedures(doc: dict[str, Any], *, vertical: str) -> VerticalProcedures:
    """Project a raw ``procedures.yaml`` mapping into a validated VerticalProcedures.

    ``agents`` and ``procedures`` are maps keyed by id (house YAML style — cf.
    ``object_types`` in the ontology YAML); the key is folded in as the id.
    """
    agents = [
        Agent(agent_id=str(aid), **(raw or {})) for aid, raw in (doc.get("agents") or {}).items()
    ]
    procedures = [
        _parse_procedure(str(pid), raw or {}) for pid, raw in (doc.get("procedures") or {}).items()
    ]
    return VerticalProcedures(
        vertical=vertical,
        namespace=doc.get("namespace"),
        version=doc.get("version"),
        agents=agents,
        procedures=procedures,
    )


def load_procedures_file(path: Path, *, vertical: str) -> VerticalProcedures:
    """Load + validate a procedures spec from an explicit path."""
    yaml = YAML(typ="safe")
    with path.open(encoding="utf-8") as fh:
        doc: dict[str, Any] = yaml.load(fh)
    return parse_procedures(doc or {}, vertical=vertical)


def load_procedures(vertical: str) -> VerticalProcedures:
    """Load + validate a vertical's ``verticals/<name>/procedures.yaml``."""
    return load_procedures_file(procedures_path(vertical), vertical=vertical)
