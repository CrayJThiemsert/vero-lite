"""Deterministic per-arm NL question renderers for the B-γ comparison (PLAN-0027 SD-2).

SD-2 (Cray-ratified 2026-06-16): a deterministic **per-arm template** that draws
the ``Scenario`` fields verbatim into a plain operator question. The two baseline
arms consume different modalities, so the template is rendered per arm — both
drawing the SAME scenario fields, neither leaking anything beyond what the
matching arm-(a) input carries, so the comparison stays apples-to-apples on the
D-1 graded sub-task:

* arm (b) raw text-to-SQL — a *discovery* question that deliberately does NOT
  name the breached entity's primary key; the model must write SQL to FIND it in
  the per-scenario DB (``text_to_sql_arm.build_scenario_db``).
* arm (c) lean RAG — an *event-style* question that states the readings (the
  breached entity first, then any distractor siblings — mirroring the event arm
  (a) consumes via ``scenario_to_event``: the primary reading, then
  ``other_readings``), since RAG has no DB to query and must reason over the
  question text + the retrieved corpus.

The joint SD-1↔SD-2 binding lives in the corpus authoring; here the renderers
just guarantee the question shares surface vocabulary (the entity-type word, the
reading parameter, the threshold/direction) with that corpus.
"""

from __future__ import annotations

from benchmarks.procedure_baseline.schema import Scenario

_UNIT_PHRASE = {"celsius": "°C", "hz": "Hz"}


def _fmt_number(value: float) -> str:
    """Render a float without a trailing ``.0`` (90.0 -> "90", 96.5 -> "96.5")."""
    return str(int(value)) if value.is_integer() else str(value)


def _unit_phrase(unit: str) -> str:
    return _UNIT_PHRASE.get(unit.lower(), unit)


def _edge(direction: str) -> str:
    return "at or above" if direction == "above" else "at or below"


def _threshold_noun(direction: str) -> str:
    """The threshold's noun, **derived from the breach direction** (not a per-vertical
    hardcode): an ``above`` breach crosses a *ceiling*, a ``below`` breach a *floor*.
    Data-driven so a new vertical needs no template change — energy/supply_chain are
    ``above`` (→ "ceiling", byte-identical to the pre-data-driven renderer); aquaculture
    is ``below`` (→ "floor", the R-OQ1-3 template-neutrality fix)."""
    return "ceiling" if direction == "above" else "floor"


def render_sql_question(scenario: Scenario, reading_parameter: str) -> str:
    """Arm (b) discovery question — the model must FIND the breached entity via SQL.

    Draws entity_type / reading_parameter / threshold / direction / unit from the
    scenario; deliberately omits the primary key and the breach value (those live
    in the per-scenario DB the SQL queries).
    """
    entity = scenario.entity_type.lower()
    return (
        f"Which {entity} has a {reading_parameter} reading {_edge(scenario.direction)} "
        f"the {_fmt_number(scenario.threshold)} {_unit_phrase(scenario.unit)} "
        f"{_threshold_noun(scenario.direction)}? "
        f"Return the affected {entity}."
    )


def render_rag_question(scenario: Scenario, reading_parameter: str) -> str:
    """Arm (c) event-style question — states the readings (breached entity first,
    then distractor siblings, mirroring ``scenario_to_event``) and asks for the
    affected entity AND the recommended action.
    """
    entity = scenario.entity_type.lower()
    unit = _unit_phrase(scenario.unit)
    noun = _threshold_noun(scenario.direction)
    readings: list[tuple[str, float]] = [(scenario.primary_key, scenario.measured_value)]
    readings += [(decoy.primary_key, decoy.measured_value) for decoy in scenario.distractors]
    reading_list = "; ".join(f"{pk} = {_fmt_number(value)} {unit}" for pk, value in readings)
    return (
        f"{entity.capitalize()} {reading_parameter} readings — {reading_list}. The "
        f"{reading_parameter} {noun} is {_fmt_number(scenario.threshold)} {unit} (a "
        f"breach is a reading {_edge(scenario.direction)} the {noun}). Which {entity} "
        f"has a {reading_parameter} breach, and what should we do about it?"
    )


__all__ = ["render_rag_question", "render_sql_question"]
