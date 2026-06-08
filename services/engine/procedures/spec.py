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
  ``human_task`` is inherently human.
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
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from ruamel.yaml import YAML


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


class Step(BaseModel):
    """One step of a Procedure (ADR-016 D2)."""

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
    input: str | None = Field(
        default=None, description="prior-step output reference + optional filter predicate"
    )
    output: str | None = Field(default=None, description="produced object set / artifact name")
    handler: str | None = Field(
        default=None,
        description="registered action-handler to invoke; action steps only (allowlist-checked).",
    )

    @model_validator(mode="after")
    def _validate_step(self) -> Self:
        """Enforce the D3 step invariants: ``autonomy`` and ``handler`` are axes of
        ``action`` steps only.

        ``action`` defaults to ``gated`` (safe-by-default). A non-action step must
        not carry either — ``query`` / ``evaluate`` always run auto, ``human_task``
        is inherently human, and none of them invoke an action handler.
        """
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
