"""The archetype-first procedure generator pipeline (ADR-0024 D1; PLAN-0040 Phase B,
Steps B1/B2).

Deterministic-code-DOMINANT orchestration of the seven stages with **two** narrow LLM
calls per successful run — 1 classify + 1 prose (LOCKED-1 / D1); a repair retry adds
further prose calls, never a second classify:

* **S0 normalize** — trim the narrative.
* **S1 classify** *(LLM)* — :func:`classify_narrative` selects one archetype from the
  closed catalog enum + emits per-step ``gate_kind`` (``schemas.Classification``).
* **S2 abstain-gate** — deterministic on the LABEL (LOCKED-5): an ``abstain`` /
  off-catalog label, or a per-step gate that disagrees with the archetype oracle (OQ-3 /
  AC-A8), routes to hand-author. **Confidence NEVER routes** (ADR-010 IN-3) — it is
  recorded in provenance only. The matched archetype is **human-confirmed before any
  skeleton is built**: :func:`build_skeleton` only runs on a :class:`ProposedMatch`, and
  the only path to one is through the ``confirm`` callback in :func:`generate`.
* **S3 instantiate** — select the template from the registry (code synthesizes structure;
  the LLM never invents an archetype or a gate_kind).
* **S4 stub-stamp** — fold the advisory prose into a restricted ``ProcedureDraft`` (which
  structurally cannot carry a governance value, D3 mech 1) and ``lift_to_procedure`` it,
  injecting every governance field as an ABSENT stub (OQ-C C1).
* **S5 prose** *(LLM)* — draft advisory prose (``schemas.ProseResponse``), then run
  ``prose_lint`` over every generated string (D3 mech 2).
* **S6 assemble** — serialise to a ``procedures.yaml``-shaped document + round-trip
  ``parse_procedures`` (the ``load_procedures`` core; cross-ref clean, D6). A capped
  validate→repair-retry loop feeds the exact lint / assembly error back to the prose
  call; on exhaustion it **abstains** (never ships a value).

The output is a ``load_procedures``-valid SKELETON behind the gate: it loads, but every
governance value is an unfilled stub, so ``validate_runnable`` /
``validate_governance_complete`` refuses to run it (the D6 two-state property). No run, no
write-back, no auto-commit (LOCKED-10). The two LLM calls are STRUCTURING calls (Ollama
``format``) so ``think`` is omitted — never ``think=False`` with ``format`` (ADR-001).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, ValidationError

from services.engine.llm.client import OllamaError
from services.engine.llm.structured import ChatClient
from services.engine.procedures.archetypes.template import REGISTRY, ArchetypeTemplate, StepSlot
from services.engine.procedures.draft import (
    GovernanceStub,
    ProcedureDraft,
    StepDraft,
    derive_governance_todo,
    lift_to_procedure,
)
from services.engine.procedures.generator.prompts import (
    build_classify_messages,
    build_classify_reasoning_messages,
    build_classify_structuring_messages,
    build_prose_messages,
)
from services.engine.procedures.generator.schemas import (
    ABSTAIN,
    Classification,
    ProseResponse,
    classification_schema,
    classification_schema_reasoning_first,
    prose_schema,
)
from services.engine.procedures.prose_lint import Violation, prose_lint
from services.engine.procedures.spec import (
    Autonomy,
    BandSource,
    GateKind,
    Procedure,
    StepInput,
    StepKind,
    parse_procedures,
)
from services.engine.registry import registry

_BAND_KINDS = (GateKind.ENV_BAND, GateKind.IN_FILE_BAND)
_AT2_ONLY_KINDS = frozenset(
    {GateKind.SCORED_RULE, GateKind.RULE_GATE, GateKind.DOA_TIER, GateKind.SEVERITY_TIER}
)

ClassifyArm = Literal["baseline", "field_order_flip", "two_pass"]
"""PLAN-0051 reason-then-structure A/B arm selector for the classify call (EXPERIMENTAL).

* ``baseline`` — the shipped single constrained call (``build_classify_messages`` +
  ``classification_schema``). **Default — byte-identical to the shipped behaviour.**
* ``field_order_flip`` — the SAME single call, but the schema emits ``rationale`` (reasoning)
  BEFORE ``archetype_id`` (decision) — the research brief's within-schema variant.
* ``two_pass`` — a free-form reasoning call (no ``format``, ``think=True``) BEFORE the
  constrained call (which OMITS ``think`` — CHECKPOINT-0 / Ollama #15260), mirroring the
  recommender's Pattern B (:func:`services.engine.llm.structured.generate_judgment`).

Only the A/B harness passes a non-``baseline`` arm; the shipped call sites pass nothing. The
abstain-gate (:func:`_archetype_disagreement` + the closed-label check) and the closed-enum
route are byte-identical across all three arms — the arm moves ONLY the classify prompt/schema,
never the deterministic guard (LOCKED-3)."""

_GOVERNANCE_REASONS = {
    "threshold": "the breach floor/ceiling is a deterministic band a human authors (D3)",
    "direction": "the breach direction pairs with the human-authored threshold (D3)",
    "env_var": "the env var carrying the band is a deployment binding a human authors (D3)",
    "handler": "the action handler is a blast-radius binding a human authors (D3)",
    "autonomy": "confirm the action's autonomy posture (safe-default gated; D3)",
}


# --- outcome types --------------------------------------------------------------


@dataclass(frozen=True)
class Abstained:
    """The generator declined to emit a skeleton — route to hand-author (LOCKED-5/7).

    ``reason`` is a machine code (``no_archetype_match`` / ``archetype_disagreement`` /
    ``not_confirmed`` / ``unclean_draft`` / ``classify_unparseable``); ``detail`` is the
    human-readable why."""

    reason: str
    detail: str


@dataclass(frozen=True)
class ProposedMatch:
    """The classify result awaiting human confirmation (S1/S2). No skeleton exists yet —
    :func:`build_skeleton` only runs once this is confirmed (LOCKED-5)."""

    classification: Classification
    template: ArchetypeTemplate


@dataclass(frozen=True)
class GeneratedSkeleton:
    """A ``load_procedures``-valid draft behind the gate (LOCKED-10). It loads but is NOT
    run-loadable: every governance value is an unfilled stub, captured in
    ``governance_todo`` for the gate's "YOU must author" zone (D6/D8)."""

    archetype_id: str
    vertical: str
    agent_id: str
    procedure: Procedure
    document: dict[str, Any]
    governance_todo: dict[str, list[GovernanceStub]] = field(default_factory=dict)
    classification: Classification | None = None
    prose_attempts: int = 0


_M = TypeVar("_M", bound=BaseModel)


def _parse(content: str, model_cls: type[_M]) -> _M | None:
    """Parse + schema-validate one structured response; ``None`` on any failure."""
    try:
        raw: Any = json.loads(content)
    except json.JSONDecodeError:
        return None
    try:
        return model_cls.model_validate(raw)
    except ValidationError:
        return None


def _normalize(narrative: str) -> str:
    """S0 — collapse incidental whitespace; the narrative stays untrusted downstream."""
    return " ".join(narrative.split())


# --- S1 classify + S2 abstain-gate ----------------------------------------------


def _gate_class(gate_kind: GateKind) -> str:
    """Compare gates at the band CLASS level — the template's judge defaults to
    ``in_file_band`` but instantiates to whichever band_source is chosen, so a model
    ``env_band`` still agrees with an ``in_file_band`` template judge."""
    return "band" if gate_kind in _BAND_KINDS else gate_kind.value


def _archetype_disagreement(
    classification: Classification, template: ArchetypeTemplate
) -> str | None:
    """OQ-3 / AC-A8 cross-check: the model's per-step gates must agree with the archetype
    oracle, and NO AT-2-only kind may appear. Returns the disagreement detail, or ``None``
    when the per-step classification agrees (or is absent — the label is the primary
    driver, so an empty/extra step list is not itself a disagreement)."""
    expected = {slot.step_id: _gate_class(slot.gate_kind) for slot in template.slots}
    for step_gate in classification.step_gates:
        if step_gate.gate_kind in _AT2_ONLY_KINDS:
            return (
                f"step '{step_gate.step_id}' implies an out-of-scope gate "
                f"'{step_gate.gate_kind.value}' (AT-2 only) — abstain, never down-classify"
            )
        want = expected.get(step_gate.step_id)
        if want is None:
            continue  # an id the template lacks; structure comes from the template
        if _gate_class(step_gate.gate_kind) != want:
            return (
                f"step '{step_gate.step_id}': narrative implies gate '{step_gate.gate_kind.value}' "
                f"but archetype '{template.archetype_id}' expects '{want}' — abstain (AC-A8/D4)"
            )
    return None


async def classify_narrative(
    client: ChatClient, *, narrative: str, vertical: str, arm: ClassifyArm = "baseline"
) -> ProposedMatch | Abstained:
    """S0-S2: classify the narrative to a catalogued archetype, or abstain.

    The route is a deterministic function of the closed-enum LABEL + the per-step
    cross-check (LOCKED-5) — ``classification.confidence`` is advisory and appears in NO
    branch here. Returns a :class:`ProposedMatch` (awaiting human confirm) or an
    :class:`Abstained`.

    ``arm`` (PLAN-0051 reason-then-structure A/B, default ``"baseline"``) selects the classify
    prompt/schema variant WITHOUT changing the route: ``baseline`` = the shipped single
    constrained call; ``field_order_flip`` = the same call with a reasoning-first schema;
    ``two_pass`` = a free-form reasoning call before the constrained call. Everything from the
    ``_parse`` below down — the abstain-guard + the closed-enum route — is byte-identical across
    arms (see :data:`ClassifyArm`)."""
    text = _normalize(narrative)
    if not text:
        return Abstained("empty_narrative", "no narrative text to classify — nothing to generate")
    catalog = [(t.archetype_id, t.title, t.description) for t in REGISTRY.values()]
    schema = (
        classification_schema_reasoning_first()
        if arm == "field_order_flip"
        else classification_schema()
    )
    # the classify STRUCTURING call passes `format` → omit think (Ollama #15260 contract,
    # ADR-001). two_pass runs a free-form reasoning call (no format, think=True) FIRST — the
    # hazard needs `format`, so it applies only to the constrained call below.
    try:
        if arm == "two_pass":
            reasoning = await client.chat(
                build_classify_reasoning_messages(text, vertical=vertical, catalog=catalog),
                think=True,
            )
            messages = build_classify_structuring_messages(
                text, vertical=vertical, catalog=catalog, draft=reasoning.content
            )
        else:
            messages = build_classify_messages(text, vertical=vertical, catalog=catalog)
        result = await client.chat(messages, response_format=schema)
    except OllamaError as exc:
        # a transport failure (most likely a cold/unreachable MS-S1) is NOT retried here —
        # it abstains gracefully, symmetric with the recommender / nl_query fail-safes.
        return Abstained("llm_unreachable", f"the classify call could not reach the LLM: {exc}")
    classification = _parse(result.content, Classification)
    if classification is None:
        return Abstained("classify_unparseable", "the classification response was not valid")
    if classification.archetype_id == ABSTAIN or classification.archetype_id not in REGISTRY:
        return Abstained(
            "no_archetype_match",
            f"classified '{classification.archetype_id}' — no catalogued archetype fits",
        )
    template = REGISTRY[classification.archetype_id]
    # OQ-3 (both granularities): the per-step gate_kinds are CHECKED when present — an
    # AT2-only kind (security-meaningful), or a gate contradicting the archetype on a
    # step_id the template names, abstains (:func:`_archetype_disagreement`). The
    # whole-procedure LABEL is the primary driver and the template guarantees the generated
    # skeleton's gate signature (AC-A8 is tested on the templates), so the cross-check never
    # REQUIRES the model to echo the template's internal step_ids: a classification that
    # uses its own step naming (as the live model does) or omits the per-step gates still
    # proceeds on the label. (A mandate to name the template's exact judge step_id broke the
    # live path — every real classification failed it — caught by the PR-B2 live run.)
    disagreement = _archetype_disagreement(classification, template)
    if disagreement is not None:
        return Abstained("archetype_disagreement", disagreement)
    return ProposedMatch(classification=classification, template=template)


# --- S3 instantiate + S4 stub-stamp ---------------------------------------------


def _slot_gate(slot: StepSlot, band_source: BandSource) -> tuple[GateKind, BandSource | None]:
    """Resolve a slot's emitted (gate_kind, band_source) — mirrors
    ``archetypes.template._decision_condition``: a band judge resolves to the chosen
    band_source; every other slot keeps its (``none``) gate with no band_source."""
    if slot.gate_kind in _BAND_KINDS:
        if band_source is BandSource.ENV:
            return GateKind.ENV_BAND, BandSource.ENV
        return GateKind.IN_FILE_BAND, BandSource.IN_FILE
    return slot.gate_kind, None


def _slot_input(slot: StepSlot) -> StepInput | None:
    if slot.input is None:
        return None
    where = dict(slot.input.where) if slot.input.where else None
    return StepInput(from_step=slot.input.from_step, where=where)


def _slot_llm_assist(slot: StepSlot) -> str | None:
    if slot.llm_assist is None:
        return None
    return f"{slot.llm_assist.role} the {slot.llm_assist.of} (advisory)"


def _build_procedure_draft(
    template: ArchetypeTemplate,
    prose: ProseResponse,
    *,
    band_source: BandSource,
    procedure_id: str,
    title: str,
) -> ProcedureDraft:
    """Fold the advisory prose into a restricted :class:`ProcedureDraft`. Structure
    (kind / gate_kind / input / autonomy posture) comes from the TEMPLATE (code
    synthesizes, D1); only the prose (description + notes) is LLM-sourced — and the draft
    type has no governance field, so a value cannot ride it (D3 mech 1)."""
    prose_by_id = {p.step_id: p for p in prose.steps}
    # The live model often does NOT echo the template's exact step_ids in its prose (it
    # renames freely — the same behaviour the classify cross-check already tolerates,
    # PR-B2). When the prose step COUNT matches the template, fall back to POSITIONAL
    # pairing (the model returns its steps in the asked order) so the advisory descriptions
    # LAND instead of silently dropping to "" — structure + governance still come ONLY from
    # the template, and the prose strings are linted regardless (D3). Found via the AC-B5
    # live run: a matched narrative built a stub-correct skeleton with EMPTY descriptions.
    by_position = prose.steps if len(prose.steps) == len(template.slots) else None
    steps: list[StepDraft] = []
    for index, slot in enumerate(template.slots):
        gate_kind, band = _slot_gate(slot, band_source)
        text = prose_by_id.get(slot.step_id)
        if text is None and by_position is not None:
            text = by_position[index]
        steps.append(
            StepDraft(
                step_id=slot.step_id,
                name=slot.name,
                kind=slot.kind,
                gate_kind=gate_kind,
                band_source=band,
                input=_slot_input(slot),
                llm_assist=_slot_llm_assist(slot),
                description=text.description if text is not None else "",
                input_note=text.input_note if text is not None else None,
                output_note=text.output_note if text is not None else None,
                governance_note=text.governance_note if text is not None else None,
            )
        )
    return ProcedureDraft(
        procedure_id=procedure_id,
        title=title,
        goal="",  # OQ-B (B2): goal generation defers to Phase C's elevated-scrutiny zone
        steps=steps,
        terminal=template.terminal_slot,
    )


def _slot_autonomies(template: ArchetypeTemplate) -> dict[str, Autonomy]:
    return {slot.step_id: slot.autonomy for slot in template.slots if slot.autonomy is not None}


# --- S5 prose-lint + S6 assemble ------------------------------------------------


def _generated_strings(draft: ProcedureDraft) -> list[str]:
    """Every LLM-sourced prose string in the draft — the ``prose_lint`` surface (the
    template-rendered ``llm_assist`` is included for completeness; it is clean by
    construction)."""
    out: list[str] = [draft.title]
    for step in draft.steps:
        out.extend(
            text
            for text in (
                step.description,
                step.input_note,
                step.output_note,
                step.governance_note,
                step.llm_assist,
            )
            if text
        )
    return [text for text in out if text]


def _lint_draft(draft: ProcedureDraft, handlers: frozenset[str]) -> list[Violation]:
    violations: list[Violation] = []
    for text in _generated_strings(draft):
        violations.extend(prose_lint(text, handlers=handlers))
    return violations


def _violation_feedback(violations: list[Violation]) -> str:
    parts = [f"{v.kind} '{v.match}': {v.message}" for v in violations[:6]]
    return "the prose carried governance values that must be removed — " + "; ".join(parts)


def _to_document(
    procedure: Procedure, *, agent_id: str, agent_name: str, vertical: str, version: int = 0
) -> dict[str, Any]:
    """Serialise the lifted typed ``Procedure`` + a placeholder agent into a
    ``procedures.yaml``-shaped mapping (house style: maps keyed by id). The agent is a
    placeholder the human binds — ``run_by`` resolves so the skeleton loads, but
    ``allowed`` is empty (a blast-radius bound the human authors)."""
    proc_dump = procedure.model_dump(by_alias=True, exclude_none=True, mode="json")
    procedure_id = proc_dump.pop("procedure_id")
    return {
        "namespace": vertical,
        "version": version,
        "agents": {agent_id: {"name": agent_name}},
        "procedures": {procedure_id: proc_dump},
    }


def _step_expectation(step_kind: StepKind, gate_kind: GateKind) -> str:
    if step_kind is StepKind.EVALUATE and gate_kind is GateKind.IN_FILE_BAND:
        return "judge expects an in_file band — author threshold + direction"
    if step_kind is StepKind.EVALUATE and gate_kind is GateKind.ENV_BAND:
        return "judge expects an env band — author the env var binding"
    if step_kind is StepKind.ACTION:
        return "action expects a registered handler binding + an autonomy confirm"
    return "no gate expected"


def build_governance_todo(procedure: Procedure) -> dict[str, list[GovernanceStub]]:
    """The "YOU must author" worklist (OQ-C / AC-A7), keyed by step_id. Derived from
    ``derive_governance_todo`` (the same re-derivation ``validate_governance_complete``
    re-checks — never a trusted stored copy).

    Public so the deterministic, zero-LLM instantiate path (the D9 manual-pick fallback,
    ``POST /procedures/draft/instantiate``) builds the SAME worklist from a template-only
    skeleton — one source of truth for the reasons/expectations, no drift from this
    pipeline (the gate-fixture's verbatim copy is the only other mirror)."""
    todo: dict[str, list[GovernanceStub]] = {}
    for step in procedure.steps:
        fields = derive_governance_todo(step)
        if not fields:
            continue
        gate_kind = GateKind.NONE
        if step.facet is not None and step.facet.decision_condition is not None:
            gate_kind = step.facet.decision_condition.gate_kind
        expectation = _step_expectation(step.kind, gate_kind)
        todo[step.step_id] = [
            GovernanceStub(
                field=name,
                reason=_GOVERNANCE_REASONS.get(name, "a human-authored governance value (D3)"),
                archetype_expectation=expectation,
            )
            for name in fields
        ]
    return todo


async def build_skeleton(
    client: ChatClient,
    *,
    narrative: str,
    match: ProposedMatch,
    vertical: str,
    agent_id: str = "author_agent",
    agent_name: str = "<author: name + bind this agent>",
    band_source: BandSource = BandSource.IN_FILE,
    procedure_id: str = "generated_procedure",
    retry_budget: int = 3,
    handlers: frozenset[str] | None = None,
) -> GeneratedSkeleton | Abstained:
    """S3-S6: build the governed skeleton for a CONFIRMED archetype match.

    Reachable only with a :class:`ProposedMatch` (the human-confirm boundary, LOCKED-5).
    The S5 prose call + S6 prose-lint / assembly run under a capped validate→repair-retry
    loop: a lint or assembly failure feeds the exact error back to the prose call; on
    budget exhaustion the generator **abstains** (never ships a value, D3). ``handlers``
    defaults to the vertical's registered handler vocabulary (for the handler-name lint).
    """
    text = _normalize(narrative)
    template = match.template
    # default the handler-name lint vocabulary to the ALL-vertical registered union (a
    # handler registered in another vertical, or invented, is still a binding the model
    # must not echo); the snake_case structural catch in prose_lint covers the rest.
    lint_handlers = handlers if handlers is not None else frozenset(registry.all_handler_names())
    autonomies = _slot_autonomies(template)
    feedback: str | None = None
    last_detail = "no attempt was made"

    for attempt in range(1, max(1, retry_budget) + 1):
        try:
            result = await client.chat(
                build_prose_messages(
                    text, vertical=vertical, template=template, retry_feedback=feedback
                ),
                response_format=prose_schema(),
            )
        except OllamaError as exc:
            # transport failure is not retried — abstain gracefully (cold/unreachable MS-S1)
            return Abstained("llm_unreachable", f"the prose call could not reach the LLM: {exc}")
        prose = _parse(result.content, ProseResponse)
        if prose is None:
            last_detail = "the prose response was not valid JSON for the schema"
            feedback = last_detail
            continue

        draft = _build_procedure_draft(
            template,
            prose,
            band_source=band_source,
            procedure_id=procedure_id,
            title=prose.title or template.title,
        )

        violations = _lint_draft(draft, lint_handlers)  # S6: reject smuggled values
        if violations:
            feedback = _violation_feedback(violations)
            last_detail = feedback
            continue

        try:  # S6: lift (stubs injected) + round-trip parse_procedures (cross-ref clean)
            procedure = lift_to_procedure(draft, run_by=agent_id, autonomies=autonomies)
            document = _to_document(
                procedure, agent_id=agent_id, agent_name=agent_name, vertical=vertical
            )
            parse_procedures(document, vertical=vertical)
        except (ValidationError, ValueError) as exc:
            feedback = f"the assembled skeleton failed schema validation: {exc}"
            last_detail = feedback
            continue

        return GeneratedSkeleton(
            archetype_id=template.archetype_id,
            vertical=vertical,
            agent_id=agent_id,
            procedure=procedure,
            document=document,
            governance_todo=build_governance_todo(procedure),
            classification=match.classification,
            prose_attempts=attempt,
        )

    return Abstained(
        "unclean_draft",
        f"could not produce a clean draft after {max(1, retry_budget)} attempt(s): {last_detail}",
    )


# --- S0-S6 end to end (the human-confirm boundary made explicit) ----------------


async def generate(
    client: ChatClient,
    *,
    narrative: str,
    vertical: str,
    confirm: Callable[[ProposedMatch], bool],
    agent_id: str = "author_agent",
    agent_name: str = "<author: name + bind this agent>",
    band_source: BandSource = BandSource.IN_FILE,
    procedure_id: str = "generated_procedure",
    retry_budget: int = 3,
    handlers: frozenset[str] | None = None,
) -> GeneratedSkeleton | Abstained:
    """The full S0-S6 path with the human-confirm boundary made explicit (LOCKED-5).

    Classifies, then calls ``confirm`` with the :class:`ProposedMatch`; the skeleton is
    built ONLY if ``confirm`` returns ``True`` (the human accepted the proposed archetype).
    A declined match abstains — no skeleton is ever built without confirmation."""
    match = await classify_narrative(client, narrative=narrative, vertical=vertical)
    if isinstance(match, Abstained):
        return match
    if not confirm(match):
        return Abstained(
            "not_confirmed",
            f"the proposed archetype '{match.template.archetype_id}' was not human-confirmed",
        )
    return await build_skeleton(
        client,
        narrative=narrative,
        match=match,
        vertical=vertical,
        agent_id=agent_id,
        agent_name=agent_name,
        band_source=band_source,
        procedure_id=procedure_id,
        retry_budget=retry_budget,
        handlers=handlers,
    )
