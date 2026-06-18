"""Governed entity resolution for the LLM recommendation path (ADR-0022 member (a)).

PLAN-0030. Before the governed ``RecommendedAction`` (ADR-007 D2) trusts the
model-emitted ``affected_entities``, resolve each ``EntityRef.primary_key``
against the vertical's **declared object universe** (the ratified fork **F1 =
1-b**: a ``DataAdapter`` lookup keyed through the registry). A **resolving** PK is
kept with its canonical declared key; a **non-resolving** PK **falls back to the
deterministic event subject anchor** (**F1 = 1-c / F2 = 2-c** -- the
``recommender._rule_recommend`` ``:265`` ground truth) and a resolution-outcome
``ReasoningStep`` records the outcome, so a model-invented identity is **never
silently certified** (the PDPA-forward invariant, CLAUDE.md section 8). It is the
same "classify, don't synthesize" move ADR-0021 made for measurement *kind*, now
applied to entity *identity* -- the model selects against a declared set; code
composes the governed identity.

Scope: the **reactive recommend LLM path** (``recommender._compose_llm_record``)
only. Member (b) verify+reshape (ADR-0022 D2(b)) and the procedure-engine path
(``procedures/action_step.py``) are **forward-declared, NOT built here**.

D-6 (PLAN-0027 / PLAN-0028, BINDING). This is product-path-only governance. The
normalizer below is a **fresh product-side copy** of the Cray-ratified key
calibration standard -- it deliberately does **not** import, and must not be
imported by, the benchmark grader's ``normalize_primary_key`` (``benchmarks/``),
so the arm-(c) naive-RAG baseline stays a clean, ungoverned control. (No
``benchmarks`` import appears in this module -- asserted by a test.)
"""

from __future__ import annotations

from typing import Any

from services.api.config import settings
from services.engine.actions import EntityRef, ReasoningStep
from services.engine.data_adapter import DataAdapter
from services.engine.ontology_meta import load_ontology_meta
from services.engine.registry import registry

# --- recover-only key normalization (product-side; NOT a benchmark import -- D-6) ---
#
# The Cray-ratified KEY-comparison fold (B-6 2026-06-12 + PLAN-0029 2026-06-17):
# fold the Unicode hyphen/dash family AND the whitespace-as-separator family to
# ASCII '-'. Codepoints are listed explicitly (not as literal glyphs) so the set
# is unambiguous. This is a FRESH product-side copy of that standard, NOT an
# import of the benchmark grader's normalize_primary_key (D-6).
_KEY_SEPARATOR_CODEPOINTS = (
    0x2010,  # HYPHEN
    0x2011,  # NON-BREAKING HYPHEN (e.g. 'asset-E07' emitted with U+2011)
    0x2012,  # FIGURE DASH
    0x2013,  # EN DASH
    0x2014,  # EM DASH
    0x2015,  # HORIZONTAL BAR
    0x2212,  # MINUS SIGN
    0x0020,  # SPACE
    0x00A0,  # NO-BREAK SPACE
    0x2007,  # FIGURE SPACE
    0x202F,  # NARROW NO-BREAK SPACE (e.g. 'pond-A116' emitted with U+202F)
    0x2060,  # WORD JOINER
)
_KEY_SEPARATOR_FOLD = {cp: "-" for cp in _KEY_SEPARATOR_CODEPOINTS}


def normalize_entity_key(key: str) -> str:
    """Recover-only normalization of a primary key for COMPARISON (never invent).

    Casefold + fold the Unicode separator-glyph family (hyphen/dash + space/narrow/
    no-break whitespace) to ASCII ``-``. A separator-glyph variant is a representation
    artifact, not an identity difference (ADR-0022 / PLAN-0029 calibration standard);
    a genuinely different key still fails to match. This is **not** a format
    constraint (ADR-0022 Alternative 3) -- only resolution against the declared *set*
    decides identity. Applied to BOTH sides of the comparison.
    """
    return key.translate(_KEY_SEPARATOR_FOLD).casefold()


def event_subject_ref(event: dict[str, Any]) -> EntityRef:
    """The deterministic event-grounded subject ``EntityRef`` -- the universal-correct
    identity anchor (ADR-010 IN-4 / PLAN-0006 section 6.6; ``recommender._rule_recommend``
    ``:265``).

    Shared by the deterministic fail-safe (``_rule_recommend``) and the LLM-path
    resolution fall-back (:func:`resolve_affected_entities`) so the two paths
    converge on ONE source and cannot drift (ADR-0022 F1=1-c / F2=2-c; PLAN-0030
    SD-2 -- Cray-approved). Behavior-identical to the prior inline ``EntityRef``
    construction: a refactor-only extraction, the deterministic fail-safe is not
    regressed.
    """
    return EntityRef(
        object_type=settings.oct_recommend_entity_type,
        primary_key=str(event.get(settings.oct_recommend_entity_id_field, "unknown")),
    )


def _primary_key_fields(vertical: str) -> dict[str, str]:
    """Map each ontology object-type name to its ``primary_key`` field name.

    Loaded once per :func:`resolve_affected_entities` call (the ontology is the
    source of truth for which raw-dict key holds an instance's primary key).
    """
    meta = load_ontology_meta(vertical)
    fields: dict[str, str] = {}
    for object_type in meta.object_types:
        if object_type.primary_key is not None:
            fields[object_type.name] = object_type.primary_key
    return fields


async def _declared_universe(
    adapter: DataAdapter, object_type: str, pk_field: str | None
) -> dict[str, str]:
    """Return ``{normalized_key: canonical_key}`` for the declared instances of
    ``object_type`` (the 1-b lookup). Empty when the object type has no declared
    ``primary_key`` field -- every PK of that type then falls back."""
    if pk_field is None:
        return {}
    universe: dict[str, str] = {}
    for raw in await adapter.fetch_objects(object_type):
        value = raw.get(pk_field)
        if value is None:
            continue
        canonical = str(value)
        universe[normalize_entity_key(canonical)] = canonical
    return universe


def _resolution_step(
    index: int,
    emitted: EntityRef,
    *,
    outcome: str,
    resolved_key: str | None = None,
    fallback: EntityRef | None = None,
) -> ReasoningStep:
    """A minimal, machine-readable resolution-outcome trace step (SD-1: trace-only,
    Cray-approved -- the ADR-007 D2 ``EntityRef`` envelope is left untouched). Lands
    in ``reasoning_trace``; ``AuditMetadata`` is NOT designed here (D-3)."""
    detail: dict[str, Any] = {
        "emitted_object_type": emitted.object_type,
        "emitted_primary_key": emitted.primary_key,
        "outcome": outcome,
    }
    if outcome == "resolved":
        detail["resolved_primary_key"] = resolved_key
        summary = (
            f"Resolved affected_entities[{index}] '{emitted.primary_key}' to declared "
            f"{emitted.object_type} '{resolved_key}'"
        )
    else:
        assert fallback is not None  # always provided on the fall-back branch
        detail["fallback_object_type"] = fallback.object_type
        detail["fallback_primary_key"] = fallback.primary_key
        summary = (
            f"affected_entities[{index}] '{emitted.primary_key}' did not resolve against the "
            f"declared {emitted.object_type} universe; fell back to the deterministic event "
            f"subject {fallback.object_type} '{fallback.primary_key}'"
        )
    return ReasoningStep(
        step_id=f"entity-resolution-{index}",
        kind="entity_resolution",
        summary=summary,
        detail=detail,
    )


async def resolve_affected_entities(
    event: dict[str, Any],
    vertical: str,
    entities: list[EntityRef],
) -> tuple[list[EntityRef], list[ReasoningStep]]:
    """Resolve model-emitted ``entities`` against the vertical's declared universe.

    Returns ``(resolved_entities, trace_steps)``. For each emitted ``EntityRef``:

    * **resolving** PK -> kept with the **canonical** declared key (outcome
      ``"resolved"``);
    * **non-resolving** PK -> replaced by the deterministic event subject anchor
      (:func:`event_subject_ref`, the ``:265`` ground truth; outcome ``"fallback"``);

    with each outcome appended as a ``ReasoningStep(kind="entity_resolution")``. A
    model-invented PK is **never** carried into the governed record (PDPA-forward).

    The adapter lookup is **deduped + memoised per object type** within this single
    call to bound the recommend-time read cost (the ADR-0022 Fork-1 latency flag).
    Any lookup error (e.g. no adapter registered, adapter raises) **propagates** so
    ``recommend()`` falls through to the deterministic fail-safe (ADR-010 IN-4) -- it
    is not swallowed here.
    """
    adapter = registry.get_adapter(vertical)
    pk_fields = _primary_key_fields(vertical)
    universe_cache: dict[str, dict[str, str]] = {}

    resolved: list[EntityRef] = []
    steps: list[ReasoningStep] = []
    for index, emitted in enumerate(entities):
        object_type = emitted.object_type
        if object_type not in universe_cache:
            universe_cache[object_type] = await _declared_universe(
                adapter, object_type, pk_fields.get(object_type)
            )
        canonical = universe_cache[object_type].get(normalize_entity_key(emitted.primary_key))
        if canonical is not None:
            resolved.append(emitted.model_copy(update={"primary_key": canonical}))
            steps.append(
                _resolution_step(index, emitted, outcome="resolved", resolved_key=canonical)
            )
        else:
            anchor = event_subject_ref(event)
            resolved.append(anchor)
            steps.append(_resolution_step(index, emitted, outcome="fallback", fallback=anchor))
    return resolved, steps
