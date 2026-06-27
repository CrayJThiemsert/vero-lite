"""Procedure-draft intake routes (PLAN-0040 Phase B, Step B3 / AC-B5; LOCKED-9 / D9).

The PLAN-0017 intake face reused for the archetype-first procedure generator:

``POST /procedures/draft/classify``    — MS-S1-local narrative → a PROPOSED archetype
                                         (no skeleton yet — LOCKED-5), or abstain / a
                                         non-silent degraded state (D9).
``POST /procedures/draft/build``       — a human-CONFIRMED archetype → the governed
                                         SKELETON behind the gate (the gate-render
                                         envelope), or abstain / degraded.
``POST /procedures/draft/instantiate`` — the deterministic, ZERO-LLM fallback: a
                                         manually-picked archetype → the same envelope
                                         from the template alone (D9 graceful degradation;
                                         no MS-S1 dependency).

**The human-confirm boundary is on the server (LOCKED-5).** classify ↔ build is split like
``intake.py``'s extract ↔ generate: ``build`` runs ONLY on an explicit ``confirmed=true``
archetype, and there is no classify→build server path that bypasses the confirm. The
matched archetype is rebuilt from the closed :data:`REGISTRY` (the human picked it), never
re-classified — confidence never routes (ADR-010 IN-3).

**Residency (CLAUDE.md §8 / ADR-001).** The two LLM calls run the MS-S1-local pinned
``gpt-oss:20b`` — a structuring (``format``) model, NEVER a Qwen3.x (which silently drops
the schema constraint under ``format``, Ollama #15260). The model is therefore pinned here,
NOT inherited from ``settings.recommender_model`` (which an operator may retarget). A
non-local backend or an unreachable MS-S1 degrades to a clear non-silent state and the
operator falls back to manual archetype-pick (``instantiate``) — a silently-wrong skeleton
is never produced (abstain-never-force-fit, D5).

Output is a ``load_procedures``-valid SKELETON behind the gate: every governance value is
an unfilled stub, so ``validate_governance_complete`` refuses to run it (D6). No run, no
write-back into ``verticals/*/procedures.yaml``, no auto-commit (LOCKED-10) — the route
returns the draft envelope; it never persists it.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from services.api.config import settings
from services.api.models.procedure_draft import (
    ArchetypeChoice,
    BuildRequest,
    BuildResponse,
    ClassifyRequest,
    ClassifyResponse,
    DraftAgentView,
    DraftEnvelope,
    DraftProcedureView,
    DraftVerticalView,
    InstantiateRequest,
    InstantiateResponse,
    ProposedMatchView,
)
from services.engine.llm.client import OllamaClient
from services.engine.procedures.archetypes.template import REGISTRY
from services.engine.procedures.archetypes.template import instantiate as instantiate_template
from services.engine.procedures.draft import GovernanceStub
from services.engine.procedures.generator import (
    Abstained,
    GeneratedSkeleton,
    ProposedMatch,
    build_governance_todo,
    build_skeleton,
    classify_narrative,
)
from services.engine.procedures.generator.schemas import Classification
from services.engine.procedures.prose_lint import prose_lint
from services.engine.procedures.spec import Autonomy, BandSource, Procedure, parse_procedures
from services.engine.registry import registry

logger = logging.getLogger(__name__)

router = APIRouter(tags=["procedures"])

_GENERATOR_MODEL = "gpt-oss:20b"
"""ADR-001 structuring pin — a ``format`` model, never qwen3.x (Ollama #15260). Pinned
here, NOT read from ``settings.recommender_model`` (an operator may retarget that)."""

_PLACEHOLDER_AGENT_NAME = "<author: name + bind this agent>"


class LocalBackendUnavailableError(RuntimeError):
    """The MS-S1-local backend is not configured — the generator never uses the hosted
    API (CLAUDE.md §8 / D9)."""


def _chat_client() -> OllamaClient:
    """Build the MS-S1-local Ollama client for the generator's two structuring calls.

    PINNED to ``gpt-oss:20b`` (see :data:`_GENERATOR_MODEL`). Raises
    :class:`LocalBackendUnavailableError` when the backend is not local — extraction NEVER falls
    through to the hosted API. Monkeypatched in tests (the offline seam)."""
    if settings.llm_backend != "local":
        raise LocalBackendUnavailableError(f"llm_backend={settings.llm_backend!r} is not 'local'")
    return OllamaClient(
        base_url=settings.ollama_host,
        model=_GENERATOR_MODEL,
        timeout=settings.llm_request_timeout_s,
    )


def _catalog() -> list[ArchetypeChoice]:
    """The closed v1 archetype catalog (the AT-1 family) — the manual-pick fallback set."""
    return [ArchetypeChoice(archetype_id=t.archetype_id, title=t.title) for t in REGISTRY.values()]


def _governance_options(vertical: str) -> dict[str, list[str]]:
    """The LEGAL authoring domains (the allowlist a human picks from — never a value, D4).

    ``handler`` = the target vertical's registered action handlers; falls back to the
    all-vertical union when the target has none registered yet (a fresh vertical the human
    will wire). ``direction`` / ``autonomy`` are the closed runtime enums."""
    handlers = registry.handler_names(vertical) or registry.all_handler_names()
    return {
        "direction": ["above", "below"],
        "autonomy": [a.value for a in Autonomy],
        "handler": sorted(set(handlers)),
    }


def _band_source(value: str) -> BandSource:
    return BandSource.ENV if value == "env" else BandSource.IN_FILE


_UNREACHABLE_DETAIL = "the local model server is unreachable — pick an archetype manually"


def _abstain_detail(reason: str, detail: str | None) -> str | None:
    """Sanitise a degraded detail before it crosses the HTTP boundary: an
    ``llm_unreachable`` detail embeds the MS-S1 host/port (``OllamaUnreachableError``) —
    return a generic message instead of echoing the internal address to the caller."""
    if reason == "llm_unreachable":
        return _UNREACHABLE_DETAIL
    return detail


def _safe_rationale(rationale: str) -> str:
    """Lint the classify rationale (advisory LLM prose) before returning it. The S5 build
    prose is linted, but the classify rationale renders right beside the confirm decision —
    a value smuggled here is the same leak-class-1 anchor a human would copy into the field
    they author (governed ≠ generated). On any violation, blank it (advisory — safe to drop;
    it is recorded in provenance, not authoritative)."""
    if rationale and prose_lint(rationale, handlers=frozenset(registry.all_handler_names())):
        return ""
    return rationale


def _envelope(
    *,
    vertical: str,
    namespace: str | None,
    version: int | None,
    archetype_id: str,
    agent_id: str,
    agent_name: str,
    procedure: Procedure,
    governance_todo: dict[str, list[GovernanceStub]],
) -> DraftEnvelope:
    """Assemble the gate-render envelope from a lifted ``Procedure`` + its worklist.

    Reuses the read-mode :class:`DraftProcedureView` (subclass of ``ProcedureView``) so the
    typed step/facet decomposition is byte-identical to ``GET /procedures``; the placeholder
    agent's H bindings are emitted ABSENT (the agent-side stubs the human authors)."""
    proc_view = DraftProcedureView.model_validate(
        {**procedure.model_dump(), "archetype": archetype_id, "governance_todo": governance_todo}
    )
    vertical_view = DraftVerticalView(
        vertical=vertical,
        namespace=namespace,
        version=version,
        agents=[DraftAgentView(agent_id=agent_id, name=agent_name)],
        procedures=[proc_view],
    )
    return DraftEnvelope(
        verticals=[vertical_view], governance_options=_governance_options(vertical)
    )


def _skeleton_envelope(skeleton: GeneratedSkeleton) -> DraftEnvelope:
    doc: dict[str, Any] = skeleton.document
    agents = doc.get("agents", {})
    agent_name = agents.get(skeleton.agent_id, {}).get("name", _PLACEHOLDER_AGENT_NAME)
    return _envelope(
        vertical=skeleton.vertical,
        namespace=doc.get("namespace", skeleton.vertical),
        version=doc.get("version", 0),
        archetype_id=skeleton.archetype_id,
        agent_id=skeleton.agent_id,
        agent_name=agent_name,
        procedure=skeleton.procedure,
        governance_todo=skeleton.governance_todo,
    )


def _instantiate_envelope(
    *, archetype_id: str, vertical: str, title: str, band_source: BandSource
) -> DraftEnvelope:
    """The deterministic, zero-LLM skeleton (the D9 manual-pick fallback): instantiate the
    template, round-trip ``parse_procedures`` (the same shape the live path emits), and
    derive the worklist via :func:`build_governance_todo` (one source of truth — no drift
    from the pipeline)."""
    template = REGISTRY[archetype_id]
    document = instantiate_template(
        template,
        procedure_id="generated_procedure",
        title=title or template.title,
        vertical=vertical,
        band_source=band_source,
    )
    spec = parse_procedures(document, vertical=vertical)
    procedure = spec.procedures[0]
    return _envelope(
        vertical=vertical,
        namespace=spec.namespace,
        version=spec.version,
        archetype_id=archetype_id,
        agent_id=procedure.run_by,
        agent_name=_PLACEHOLDER_AGENT_NAME,
        procedure=procedure,
        governance_todo=build_governance_todo(procedure),
    )


# --------------------------------------------------------------------------- #
# routes
# --------------------------------------------------------------------------- #


@router.post("/procedures/draft/classify", response_model=ClassifyResponse)
async def draft_classify(req: ClassifyRequest) -> ClassifyResponse:
    """Classify a free-text narrative to a PROPOSED archetype (no skeleton yet, LOCKED-5).

    A no-archetype-match / AT-2-class narrative ⇒ ``abstain`` (route to hand-author); a
    non-local backend or an unreachable MS-S1 ⇒ ``degraded`` (pick an archetype manually).
    The manual-pick ``catalog`` is always returned (the D9 fallback)."""
    try:
        client = _chat_client()
    except LocalBackendUnavailableError as exc:
        return ClassifyResponse(
            state="degraded", reason="backend_not_local", detail=str(exc), catalog=_catalog()
        )

    outcome = await classify_narrative(client, narrative=req.narrative, vertical=req.vertical)
    if isinstance(outcome, Abstained):
        # an unreachable LLM is recoverable by manual pick (degraded); a real no-match is a
        # hand-author route (abstain) — distinct states so the UI offers the right next step.
        state = "degraded" if outcome.reason == "llm_unreachable" else "abstain"
        return ClassifyResponse(
            state=state,
            reason=outcome.reason,
            detail=_abstain_detail(outcome.reason, outcome.detail),
            catalog=_catalog(),
        )

    return ClassifyResponse(
        state="match",
        match=ProposedMatchView(
            archetype_id=outcome.template.archetype_id,
            title=outcome.template.title,
            confidence=outcome.classification.confidence,
            rationale=_safe_rationale(outcome.classification.rationale),
        ),
        catalog=_catalog(),
    )


@router.post("/procedures/draft/build", response_model=BuildResponse)
async def draft_build(req: BuildRequest) -> BuildResponse:
    """Build the governed skeleton for a human-CONFIRMED archetype (the confirm boundary).

    Refuses an unconfirmed request (422 — no bypass, LOCKED-5) and an unknown archetype
    (422). The match is rebuilt from the closed :data:`REGISTRY` (the human picked it), not
    re-classified. Abstains (e.g. the model never produces clean prose) and an unreachable
    MS-S1 surface as ``abstain`` / ``degraded`` — never a half-stripped draft (D3/D5)."""
    if not req.confirmed:
        raise HTTPException(
            status_code=422, detail="build requires explicit human confirmation (confirmed=true)"
        )
    if req.archetype_id not in REGISTRY:
        raise HTTPException(status_code=422, detail=f"unknown archetype '{req.archetype_id}'")

    try:
        client = _chat_client()
    except LocalBackendUnavailableError as exc:
        return BuildResponse(state="degraded", reason="backend_not_local", detail=str(exc))

    match = ProposedMatch(
        classification=Classification(archetype_id=req.archetype_id),
        template=REGISTRY[req.archetype_id],
    )
    outcome = await build_skeleton(
        client,
        narrative=req.narrative,
        match=match,
        vertical=req.vertical,
        band_source=_band_source(req.band_source),
    )
    if isinstance(outcome, Abstained):
        state = "degraded" if outcome.reason == "llm_unreachable" else "abstain"
        return BuildResponse(
            state=state,
            reason=outcome.reason,
            detail=_abstain_detail(outcome.reason, outcome.detail),
        )

    return BuildResponse(
        state="ok", draft=_skeleton_envelope(outcome), prose_attempts=outcome.prose_attempts
    )


@router.post("/procedures/draft/instantiate", response_model=InstantiateResponse)
async def draft_instantiate(req: InstantiateRequest) -> InstantiateResponse:
    """The deterministic, zero-LLM fallback (D9): a manually-picked archetype → the same
    gate-render envelope from the template alone (no MS-S1 call). Refuses an unknown
    archetype (422)."""
    if req.archetype_id not in REGISTRY:
        raise HTTPException(status_code=422, detail=f"unknown archetype '{req.archetype_id}'")
    envelope = _instantiate_envelope(
        archetype_id=req.archetype_id,
        vertical=req.vertical,
        title=req.title,
        band_source=_band_source(req.band_source),
    )
    return InstantiateResponse(state="ok", draft=envelope)
