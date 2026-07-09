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
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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
    """How a procedure run starts. ``manual``, ``schedule`` and ``event`` are all
    runnable — ``schedule`` (clock-initiated) via ADR-0028 S1 / PLAN-0055, and
    ``event`` (an OCT anomaly/Alert) via ADR-0029 / PLAN-0056 (the event-trigger
    bridge). Each non-manual trigger's firing mechanism is built by its own PLAN."""

    MANUAL = "manual"
    SCHEDULE = "schedule"
    EVENT = "event"


class Schedule(BaseModel):
    """The fire-cadence descriptor of a ``schedule``-triggered ``Procedure`` (ADR-0028
    SD-P1; PLAN-0055 Step 2).

    Carries a cron expression + the IANA timezone the cron is evaluated in — a
    **per-schedule** tz string (not a global constant, SD-P1) so a non-TH vertical
    schedules in its own zone. Present **iff** the procedure's ``trigger`` is ``schedule``
    (enforced on :class:`Procedure`). The timezone is validated against the system tz
    database at load — a typo'd zone fails loudly at load, not at fire time (house style).
    The cron string is checked for non-blankness ONLY here; its **authoritative** parse is
    ``croniter`` in PLAN-0055 Step 3 (AC-10) — the dependency this step deliberately does
    not yet add. So a syntactically-malformed cron survives load and is caught by the
    Step-3 ``next_fire`` helper.
    """

    model_config = ConfigDict(extra="forbid")

    cron: str = Field(
        min_length=1,
        description="cron expression naming the fire cadence; parsed authoritatively by "
        "croniter (PLAN-0055 Step 3). Non-blank here — full parse-validation lands with the dep.",
    )
    timezone: str = Field(
        default="Asia/Bangkok",
        description="IANA tz name the cron is evaluated in (SD-P1; per-schedule, not global). "
        "Default Asia/Bangkok (the primary TH operator); a non-TH vertical sets its own zone.",
    )
    owning_person_id: str | None = Field(  # a PersonId (defined below); str avoids the fwd-ref
        default=None,
        description="the human Person a headless scheduled run acts ON BEHALF OF (SP-5; PLAN-0055 "
        "Step 8). A schedule fires as its agent's service principal (the actor); when the "
        "procedure carries a separation_of_duties requester role, this owning person is recorded "
        "as the run's requester so a distinct downstream human approver satisfies SoD "
        "(requester != approver). None = fully headless — valid only for a procedure with no SoD "
        "requester to resolve (a doa_tier procedure requires SoD, ADR-0025 D5, so it needs one). "
        "Cross-ref validated against the vertical's `principals` at load.",
    )

    @model_validator(mode="after")
    def _validate_schedule(self) -> Self:
        """Non-blank cron + a real IANA timezone (SD-P1). The tz is resolved against the
        system tz database so a bad zone is a loud load error, not a silent never-fire."""
        if not self.cron.strip():
            raise ValueError("schedule: cron must be a non-blank cron expression — ADR-0028 SD-P1")
        try:
            ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(
                f"schedule: timezone {self.timezone!r} is not a valid IANA time zone "
                "(e.g. 'Asia/Bangkok', 'UTC') — ADR-0028 SD-P1"
            ) from exc
        return self


class EventTrigger(BaseModel):
    """The event-binding descriptor of an ``event``-triggered ``Procedure`` (ADR-0029
    SD-3 / SD-P2; PLAN-0056 Step 2).

    Declares which detected OCT condition (an anomaly / ``Alert``) fires this procedure.
    Present **iff** the procedure's ``trigger`` is ``event`` (enforced on :class:`Procedure`),
    mirroring how :class:`Schedule` rides on a ``schedule`` procedure. The bridge derives the
    ``event_kind`` -> procedure index by scanning procedures with ``trigger == event`` (ADR-0029
    SD-3 — the mapping is authored in the vertical spec, not a code registry); a duplicate
    ``event_kind`` across event procedures is an authoring error caught at load (on
    :class:`VerticalProcedures`). The precise recommender field ``event_kind`` is matched against
    is pinned by the Step-4 resolver — the recommender's ``RecommendedAction`` has no
    ``action_type`` (its discriminators are ``suggested_handler`` / ``vertical``); Step 2 keeps
    ``event_kind`` a free authored string, unique per vertical.
    """

    model_config = ConfigDict(extra="forbid")

    event_kind: str = Field(
        min_length=1,
        description="the detected OCT condition kind this procedure responds to (ADR-0029 SD-3). "
        "Matched against the recommender's actionable detection by the Step-4 resolver; unique "
        "across a vertical's event-triggered procedures (cross-ref validated at load).",
    )
    owning_person_id: str | None = Field(  # a PersonId (defined below); str avoids the fwd-ref
        default=None,
        description="the human Person a headless event-fired run acts ON BEHALF OF (SP-5; mirrors "
        "`Schedule.owning_person_id`). An event run fires as its agent's service principal (the "
        "actor); when the procedure carries a separation_of_duties requester role, this owning "
        "person is recorded as the run's requester so a distinct downstream human approver "
        "satisfies SoD (requester != approver). None = fully headless — valid only for a procedure "
        "with no SoD requester to resolve (a doa_tier procedure requires SoD, ADR-0025 D5, so it "
        "needs one). Cross-ref validated against the vertical's `principals` at load.",
    )
    dedup_window_seconds: int = Field(
        default=3600,
        gt=0,
        description="the detection-window granularity (seconds) for the SD-2 dedup key (SD-P1). "
        "`detected_at` is truncated to this bucket by `event_bridge.event_key`, so a steady-state "
        "anomaly re-detected each poll collapses to ONE run while the same condition recurring in "
        "a LATER window fires a fresh run. Per-mapping (SD-P1) — a slow-moving asset anomaly wants "
        "a wide window, a transient one a narrow one. Default 1h.",
    )


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


class JoinOn(BaseModel):
    """An explicit equi-key override for one join (PLAN-0061 SD-1; ADR-016 Q4 SD-A).

    The per-step escape hatch for keys the ontology does not declare — warn-first
    at the load gate when no declared ``link_types`` relationship backs the pair
    (OQ-4 resolved: warn, never reject).
    """

    model_config = ConfigDict(extra="forbid")

    left: str = Field(..., description="join column on the base/accumulated side")
    right: str = Field(..., description="join column on the joined ('with') side")


class JoinSpec(BaseModel):
    """One declared join in a multi-read ``query`` step (PLAN-0061 SD-1; Q4 SD-A Hybrid).

    ``with`` names the declared read being joined in. Exactly ONE of the three
    join forms must be set: ``link`` (the ontology-declared default — keys resolve
    from the named link's typed ``foreign_key``, the governed path), ``on`` (an
    explicit equi-key override), or ``fuse`` (positional singleton fusion — both
    sides must be exactly one row post-narrowing; the procurement-intake shape the
    ontology cannot declare). ``where`` narrows the JOINED side post-fetch,
    pre-join, via the same single ``matches_where`` predicate (LOCKED-3).
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    with_read: str = Field(
        ...,
        alias="with",
        description="the declared read (an entry of input.reads) this join brings in",
    )
    link: str | None = Field(
        default=None,
        description="ontology link_types name — the declared-default join (keys from its "
        "typed foreign_key)",
    )
    on: JoinOn | None = Field(
        default=None, description="explicit equi-key override (warn-first when undeclared)"
    )
    fuse: bool | None = Field(
        default=None,
        description="positional singleton fusion — no relational key; both sides must be "
        "exactly one row",
    )
    where: dict[str, Any] | None = Field(
        default=None,
        description="field-equality filter narrowing the joined side post-fetch, pre-join",
    )

    @model_validator(mode="after")
    def _validate_exactly_one_form(self) -> Self:
        forms = [self.link is not None, self.on is not None, self.fuse is not None]
        if sum(forms) != 1:
            raise ValueError(
                f"join with '{self.with_read}': exactly one of link/on/fuse must be set "
                f"(got {sum(forms)}) — PLAN-0061 SD-1"
            )
        if self.fuse is False:
            raise ValueError(
                f"join with '{self.with_read}': fuse must be true when present (omit it "
                "for a keyed join)"
            )
        return self


class ProjectSpec(BaseModel):
    """A declared projection for a ``query`` step (PLAN-0061 SD-1; Q4 SD-B shape 1).

    ``latest_per`` names a declared ontology link: the group key is that link's
    typed ``foreign_key.from_property`` and the read keeps argmax(``order_by``)
    per group with the SD-5 deterministic primary-key tie-break. ``order_by`` is
    an explicit declared property of the grouped read (never a hard-coded field
    name). ``fields`` is an optional select/rename map — join + projection ONLY;
    arbitrary computation stays downstream (OQ-3 resolved).
    """

    model_config = ConfigDict(extra="forbid")

    latest_per: str | None = Field(
        default=None,
        description="ontology link_types name whose typed foreign_key.from_property is "
        "the group key (latest-per-group)",
    )
    order_by: str | None = Field(
        default=None,
        description="declared property of the grouped read that orders 'latest' (SD-5: "
        "explicit, never hard-coded)",
    )
    fields: dict[str, str] | None = Field(
        default=None,
        description="optional select/rename map {source_field: output_name}; omit to keep "
        "all fields",
    )

    @model_validator(mode="after")
    def _validate_latest_requires_order(self) -> Self:
        if self.latest_per is not None and self.order_by is None:
            raise ValueError(
                "project.latest_per requires an explicit project.order_by (PLAN-0061 SD-5)"
            )
        if self.latest_per is None and self.order_by is not None:
            raise ValueError("project.order_by is only meaningful with project.latest_per")
        if self.latest_per is None and not self.fields:
            raise ValueError("an empty project declares nothing — set latest_per and/or fields")
        return self


class StepInput(BaseModel):
    """A step's input source (ADR-016 D4; PLAN-0019 A-ζ-prep named-input).

    ``from`` names the prior step whose output set feeds this step (default = the
    immediately preceding step). ``where`` is a field-equality filter that narrows
    that set — an entity is kept iff ``entity[field] == value`` for **every** pair,
    so the set-valued breach/watch/ok fan-out is just ``where: {verdict: breach}``
    on the evaluate step's output. A non-mapping entity never matches a ``where``
    (it has no fields). Linear-only: ``from`` must name an EARLIER step
    (forward / unknown references are rejected at pre-flight by ``validate_runnable``).

    ``reads`` (ADR-016 Q3, 2026-07-01 amendment) is the typed **data-sourcing entry
    point** — the ontology object_type(s) a ``query`` step reads — distinct from and
    additive to the ``from`` intra-run thread. It is a declaration + a load-time
    consistency/scoping gate (``validate_read_bindings``): each named object_type
    must exist in the vertical's ontology AND, when the agent opts in with a
    non-empty ``allowed.object_types``, be inside that read allowlist.

    ``join`` / ``project`` (PLAN-0061; the ADR-016 Q4 amendment, Accepted
    2026-07-09) declare the multi-read join + projection grammar — the two v1
    shapes (equi-join enrichment + latest-per-group projection). Both are
    H-governed values the generator may never emit (stripped at lift, pinned in
    the governance snapshot); both require ``reads`` and are structurally
    validated by the extended ``validate_read_bindings`` load gate.
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
    reads: list[str] | None = Field(
        default=None,
        description="ontology object_types this query step reads (each must exist in the "
        "vertical's ObjectTypeMeta AND be in Agent.allowed.object_types) — ADR-016 Q3",
    )
    join: list[JoinSpec] | None = Field(
        default=None,
        description="declared joins bringing each non-base read into the base read "
        "(PLAN-0061 SD-1; requires reads)",
    )
    project: ProjectSpec | None = Field(
        default=None,
        description="declared projection (latest-per-group and/or field select/rename) — "
        "PLAN-0061 SD-1; requires reads",
    )

    @model_validator(mode="after")
    def _validate_join_project_shape(self) -> Self:
        """Schema-level Q4 invariants (ontology-dependent checks live in the load gate)."""
        if (self.join or self.project) and not self.reads:
            raise ValueError("join/project require a declared reads list (PLAN-0061 SD-1)")
        if self.join:
            base = self.reads[0] if self.reads else None
            seen: set[str] = set()
            for spec in self.join:
                if self.reads and spec.with_read not in self.reads:
                    raise ValueError(
                        f"join with '{spec.with_read}' is not a declared read {self.reads}"
                    )
                if spec.with_read == base:
                    raise ValueError(
                        f"join with '{spec.with_read}' names the base read (reads[0]) — "
                        "the base is joined TO, never brought in"
                    )
                if spec.with_read in seen:
                    raise ValueError(f"duplicate join for read '{spec.with_read}'")
                seen.add(spec.with_read)
        return self


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


ServicePrincipalId = str
"""A canonical service-principal identity key (e.g. ``svc-scheduler``) — the stable id of a
NON-HUMAN (service) actor for non-human triggers (ADR-016 S2 D2+D3; PLAN-0053 Phase B).
DISTINCT from ``PersonId``: a service id is NEVER a member of the SoD ``Person`` comparison
set (RF-3) and NEVER an approver (SP-1). Human-authored (never model-emitted)."""


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

    @property
    def constraint_id(self) -> str:
        """The stable id for this SoD constraint (PLAN-0044 A1b Step 6, SD-3 / D2): the sorted,
        ``+``-joined ``distinct_steps``. Derived identically wherever a ``control_ref`` names this
        constraint (the audit-to-control tie + a read-only render) so the join is EXACT, not
        fuzzy — and needs no new schema field (the ``distinct_steps`` ARE the constraint's
        identity)."""
        return "+".join(sorted(self.distinct_steps))


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
    object_types: list[str] = Field(
        default_factory=list,
        description="ontology object_types this agent may read (ADR-016 Q3 load-gate; "
        "empty = unconstrained, mirroring step_kinds — NOT action_handlers' fail-closed)",
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


class ServicePrincipal(BaseModel):
    """A first-class, human-authored NON-HUMAN (service) actor identity for non-human triggers
    (ADR-016 S2 D2+D3; PLAN-0053 Phase B). It fires / owns a run; it is NEVER an approver (SP-1)
    and NEVER substitutable for a ``Person`` in the SoD comparison set (RF-3) — deliberately a
    DISTINCT type with NO ``roles`` field so the approver seam cannot be reused. Least-privilege
    is unchanged (SP-6): the service actor's blast radius is the running ``Agent``'s
    ``allowed.{action_handlers, object_types}`` — this identity carries no scope primitive of its
    own. Human-author-only (H, ADR-0024 D3) — never model-emitted."""

    model_config = ConfigDict(extra="forbid")

    service_principal_id: ServicePrincipalId = Field(
        description="canonical service-identity key (PK) — the stable id an Agent references and "
        "the never-null audit actor a service-triggered run records (SP-4). NEVER compared as a "
        "``Person`` in SoD (RF-3)."
    )
    name: str = Field(description="the service actor's name (display)")


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
    service_principal_ids: list[str] = Field(
        default_factory=list,
        description="ids of registry ``ServicePrincipal``s this Agent may act as (SD-3, "
        "SP-2/SP-6) — cross-ref-validated on ``VerticalProcedures`` like ``run_by``. Default "
        "empty; the service actor's blast radius stays this Agent's ``allowed`` (no new scope "
        "primitive). Human-authored (H, ADR-0024 D3).",
    )


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
    schedule: Schedule | None = Field(
        default=None,
        description="fire cadence (cron + IANA tz) for a `schedule`-triggered procedure "
        "(ADR-0028 SD-P1). Present IFF trigger == schedule (validated below); a `manual` "
        "procedure must not carry one. Absent on every existing (manual) procedure.",
    )
    event_trigger: EventTrigger | None = Field(
        default=None,
        description="event-binding (event_kind + SP-5 owning person) for an `event`-triggered "
        "procedure (ADR-0029 SD-3 / SD-P2). Present IFF trigger == event (validated below); a "
        "non-event procedure must not carry one. Absent on every manual/schedule procedure.",
    )
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
    def _validate_schedule_descriptor(self) -> Self:
        """A ``schedule`` descriptor is present IFF the trigger is ``schedule`` (ADR-0028
        SD-P1; PLAN-0055 Step 2). A ``schedule``-triggered procedure needs a clock (cron + tz)
        to fire; a ``manual`` procedure carrying one is an authoring error — either way fail
        loudly at load, not at fire time (house style; mirrors the per-kind field invariants
        on ``Step``)."""
        is_schedule = self.trigger is Trigger.SCHEDULE
        if is_schedule and self.schedule is None:
            raise ValueError(
                f"procedure '{self.procedure_id}': trigger 'schedule' requires a `schedule` "
                "descriptor (cron + IANA tz) — ADR-0028 SD-P1 / PLAN-0055 Step 2"
            )
        if not is_schedule and self.schedule is not None:
            raise ValueError(
                f"procedure '{self.procedure_id}': a `schedule` descriptor applies to a "
                f"'schedule'-trigger procedure only (trigger is '{self.trigger.value}') — "
                "ADR-0028 SD-P1"
            )
        return self

    @model_validator(mode="after")
    def _validate_event_trigger_descriptor(self) -> Self:
        """An ``event_trigger`` descriptor is present IFF the trigger is ``event`` (ADR-0029
        SD-3 / SD-P2; PLAN-0056 Step 2). An ``event``-triggered procedure needs an ``event_kind``
        binding to fire; a non-event procedure carrying one is an authoring error — either way
        fail loudly at load, not at fire time (mirrors the schedule descriptor invariant)."""
        is_event = self.trigger is Trigger.EVENT
        if is_event and self.event_trigger is None:
            raise ValueError(
                f"procedure '{self.procedure_id}': trigger 'event' requires an `event_trigger` "
                "descriptor (event_kind) — ADR-0029 SD-3 / PLAN-0056 Step 2"
            )
        if not is_event and self.event_trigger is not None:
            raise ValueError(
                f"procedure '{self.procedure_id}': an `event_trigger` descriptor applies to an "
                f"'event'-trigger procedure only (trigger is '{self.trigger.value}') — "
                "ADR-0029 SD-3"
            )
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


def _check_event_cross_refs(procedures: list[Procedure], known_persons: set[str]) -> None:
    """PLAN-0056 Step 2 (ADR-0029 SD-3): validate the ``event_trigger`` cross-refs — the SP-5
    owning person resolves to a declared Person, and each ``event_kind`` maps to exactly one
    procedure (a duplicate is ambiguous). Extracted from ``VerticalProcedures._cross_refs`` to
    keep that validator's cyclomatic complexity bounded."""
    for proc in procedures:
        eref = proc.event_trigger.owning_person_id if proc.event_trigger is not None else None
        if eref is not None and eref not in known_persons:
            raise ValueError(
                f"procedure '{proc.procedure_id}': event_trigger.owning_person_id '{eref}' is "
                f"not a declared principal (known: {sorted(known_persons)}) — PLAN-0056 Step 2"
            )
    event_kinds = [p.event_trigger.event_kind for p in procedures if p.event_trigger is not None]
    dup_kinds = sorted({k for k in event_kinds if event_kinds.count(k) > 1})
    if dup_kinds:
        raise ValueError(
            f"duplicate event_trigger.event_kind(s) {dup_kinds} across event-triggered "
            "procedures — each event_kind maps to exactly one procedure (ADR-0029 SD-3 / "
            "PLAN-0056 Step 2)"
        )


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
    service_principals: list[ServicePrincipal] = Field(
        default_factory=list,
        description="the non-human service actors for non-human triggers (ADR-016 S2 / PLAN-0053 "
        "Phase B) — human-author-only (H, ADR-0024 D3), never generated. Absent => empty (every "
        "existing vertical unchanged).",
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
    def _validate_service_principals(self) -> Self:
        """Service-principal identity integrity (ADR-016 S2 / PLAN-0053 Phase B AC-6):
        ``service_principal_id``s are unique. The service id-space is disjoint from ``Person``
        by TYPE (RF-3), so no cross-space collision check is needed."""
        ids = [sp.service_principal_id for sp in self.service_principals]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            raise ValueError(
                f"vertical '{self.vertical}': duplicate service_principal_id(s) {dupes}"
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
        # ADR-016 S2 / PLAN-0053 SD-3 (AC-7): every Agent->service reference resolves to a
        # registry ServicePrincipal (mirrors the run_by cross-ref; a dangling ref is an
        # authoring error, not a silent no-op).
        known_services = {sp.service_principal_id for sp in self.service_principals}
        for agent in self.agents:
            dangling_sp = sorted(set(agent.service_principal_ids) - known_services)
            if dangling_sp:
                raise ValueError(
                    f"agent '{agent.agent_id}': service_principal_ids reference unknown "
                    f"service_principal_id(s) {dangling_sp} (known: {sorted(known_services)}) "
                    "— ADR-016 S2 / SD-3"
                )
        # PLAN-0055 Step 8: a schedule's owning_person_id (the SP-5 human a headless run acts ON
        # BEHALF OF, recorded as the SoD requester at fire time) must resolve to a declared Person
        # — a dangling ref is an authoring error, not a silent None-requester failing at the gate.
        known_persons = {p.person_id for p in self.principals}
        for proc in self.procedures:
            oref = proc.schedule.owning_person_id if proc.schedule is not None else None
            if oref is not None and oref not in known_persons:
                raise ValueError(
                    f"procedure '{proc.procedure_id}': schedule.owning_person_id '{oref}' is not "
                    f"a declared principal (known: {sorted(known_persons)}) — PLAN-0055 Step 8"
                )
        # PLAN-0056 Step 2 (ADR-0029 SD-3): event_trigger cross-refs (owning-person resolves +
        # unique event_kind) — extracted to a helper to keep this validator under the C901 bound.
        _check_event_cross_refs(self.procedures, known_persons)
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
        # Principals + declared alias groups are LIST-shaped (not id-keyed maps like
        # agents/procedures): the SoD run-check resolves against them (ADR-0026 D1/D4).
        # Pydantic coerces each raw dict into a Person / PrincipalAlias. Absent keys
        # default to empty — every non-SoD vertical loads unchanged.
        principals=doc.get("principals") or [],
        principal_aliases=doc.get("principal_aliases") or [],
        # Service principals are LIST-shaped (like principals): non-human actors for non-human
        # triggers (ADR-016 S2 / PLAN-0053 Phase B). Absent key => empty (every vertical unchanged).
        service_principals=doc.get("service_principals") or [],
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
