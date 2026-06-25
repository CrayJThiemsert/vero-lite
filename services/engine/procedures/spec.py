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

from enum import StrEnum
from pathlib import Path
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from ruamel.yaml import YAML

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

    @model_validator(mode="after")
    def _unique_step_ids(self) -> Self:
        ids = [s.step_id for s in self.steps]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            raise ValueError(f"procedure '{self.procedure_id}': duplicate step_id(s) {dupes}")
        return self


class VerticalProcedures(BaseModel):
    """A vertical's full ``procedures.yaml`` — its Agents and its Procedures."""

    model_config = ConfigDict(extra="forbid")

    vertical: str
    namespace: str | None = None
    version: int | None = None
    agents: list[Agent]
    procedures: list[Procedure]

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
