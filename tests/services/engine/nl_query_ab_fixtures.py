"""PLAN-0051 Step 3 — the labelled nl_query A/B corpus + the pre-committed scoring metric.

Pure data + pure logic (no ``test_`` prefix → not collected). Both the OFFLINE A/B driver
(``test_reason_then_structure_nl_query``, Step 4) and the Cray-gated LIVE A/B
(``test_reason_then_structure_nl_query_live``, Step 5) import ``FIXTURES`` + ``score_query``
from here, so the corpus + metric are defined ONCE and pre-committed BEFORE any live run
(CLAUDE.md §8 / Lesson #0026 — the offline oracle is the gate; live is confirming evidence).

Corpus (SD-1, ratified): ~27 hand-authored questions over the **energy** ontology, each with a
gold :class:`StructuredQuery` that PASSES the production ``_validate_query`` at build time (a
gold that fails the semantic validator is a corpus bug — asserted in
``test_nl_query_ab_fixtures``). Categories span ``list`` + conjunctive filter, ``count``, each
aggregate op (max/min/avg/sum), an explicit aggregate ``group_by``, a cross-type ``resolve``
(name→id), and the known-hard **aggregate-superlative** class ("which X is most Y") that the
model tends to under-specify by DROPPING ``group_by`` + ``measured_kind``
(``project_nl_query_aggregate_framing_drops_filter``).

Scoring (SD-1, ratified): a **field-weighted partial structural match on the RAW ``_translate``
output**, NOT execution-equivalence and NOT strict all-or-nothing. It is scored on the raw
translate the model *should* produce — the Phase-B deterministic seam
(``_infer_group_by`` / ``_coherence_rewrite``) runs AFTER ``_translate`` and already repairs
the aggregate-superlative drop, so scoring the raw output isolates the reasoning-order lever
instead of letting the seam mask (or credit) it. ``limit`` is intentionally NOT scored (benign
differences, SD-1).
"""

from __future__ import annotations

from dataclasses import dataclass

from services.engine.nl_query import NameResolve, QueryFilter, StructuredQuery


@dataclass(frozen=True)
class NlQueryFixture:
    """One labelled NL question + its pre-committed gold :class:`StructuredQuery`.

    ``gold`` is the raw translate the model SHOULD emit (it passes ``_validate_query``).
    ``category`` buckets the corpus; ``hard_class`` marks the aggregate-superlative subset
    whose discriminating fields (``group_by`` + ``measured_kind``) the model tends to drop."""

    fixture_id: str
    category: str
    question: str
    gold: StructuredQuery
    hard_class: bool = False


def _f(prop: str, op: str, value: str) -> QueryFilter:
    return QueryFilter(property=prop, op=op, value=value)


# --- list + conjunctive filter -------------------------------------------------------------
_LIST: tuple[NlQueryFixture, ...] = (
    NlQueryFixture(
        "list-assets-maintenance",
        "list_filter",
        "List all assets that are currently in maintenance.",
        StructuredQuery(
            object_type="Asset", operation="list", filters=[_f("status", "eq", "maintenance")]
        ),
    ),
    NlQueryFixture(
        "list-battery-assets",
        "list_filter",
        "Show the battery assets.",
        StructuredQuery(
            object_type="Asset", operation="list", filters=[_f("asset_type", "eq", "battery")]
        ),
    ),
    NlQueryFixture(
        "list-open-alerts",
        "list_filter",
        "Which alerts are still open?",
        StructuredQuery(
            object_type="Alert", operation="list", filters=[_f("status", "eq", "open")]
        ),
    ),
    NlQueryFixture(
        "list-critical-events",
        "list_filter",
        "List the critical operational events.",
        StructuredQuery(
            object_type="OperationalEvent",
            operation="list",
            filters=[_f("severity", "eq", "critical")],
        ),
    ),
    NlQueryFixture(
        "list-substations",
        "list_filter",
        "Show the substations.",
        StructuredQuery(
            object_type="Site", operation="list", filters=[_f("site_type", "eq", "substation")]
        ),
    ),
    NlQueryFixture(
        "list-high-capacity-assets",
        "list_filter",
        "List assets with capacity over 100 kW.",
        StructuredQuery(
            object_type="Asset", operation="list", filters=[_f("capacity_kw", "gt", "100")]
        ),
    ),
    NlQueryFixture(
        "list-proposed-actions",
        "list_filter",
        "Which recommended actions are still proposed?",
        StructuredQuery(
            object_type="RecommendedAction",
            operation="list",
            filters=[_f("status", "eq", "proposed")],
        ),
    ),
    NlQueryFixture(
        "list-high-open-alerts",
        "list_filter",
        "List the high-urgency alerts that are still open.",
        StructuredQuery(
            object_type="Alert",
            operation="list",
            filters=[_f("urgency", "eq", "high"), _f("status", "eq", "open")],
        ),
    ),
)

# --- count -------------------------------------------------------------------------------
_COUNT: tuple[NlQueryFixture, ...] = (
    NlQueryFixture(
        "count-active-assets",
        "count",
        "How many active assets are there?",
        StructuredQuery(
            object_type="Asset", operation="count", filters=[_f("status", "eq", "active")]
        ),
    ),
    NlQueryFixture(
        "count-feeders",
        "count",
        "How many feeders do we have?",
        StructuredQuery(
            object_type="Asset", operation="count", filters=[_f("asset_type", "eq", "feeder")]
        ),
    ),
    NlQueryFixture(
        "count-resolved-alerts",
        "count",
        "Count the resolved alerts.",
        StructuredQuery(
            object_type="Alert", operation="count", filters=[_f("status", "eq", "resolved")]
        ),
    ),
    NlQueryFixture(
        "count-alarm-events",
        "count",
        "How many operational events were alarms?",
        StructuredQuery(
            object_type="OperationalEvent",
            operation="count",
            filters=[_f("event_type", "eq", "alarm")],
        ),
    ),
)

# --- aggregate (max/min/avg/sum), no grouping --------------------------------------------
_AGGREGATE: tuple[NlQueryFixture, ...] = (
    NlQueryFixture(
        "agg-avg-capacity",
        "aggregate",
        "What is the average capacity of our assets?",
        StructuredQuery(object_type="Asset", operation="avg", aggregate_property="capacity_kw"),
    ),
    NlQueryFixture(
        "agg-total-capacity",
        "aggregate",
        "What is the total installed capacity across all assets?",
        StructuredQuery(object_type="Asset", operation="sum", aggregate_property="capacity_kw"),
    ),
    NlQueryFixture(
        "agg-min-capacity",
        "aggregate",
        "What is the smallest asset capacity we have?",
        StructuredQuery(object_type="Asset", operation="min", aggregate_property="capacity_kw"),
    ),
    NlQueryFixture(
        "agg-avg-confidence",
        "aggregate",
        "What is the average confidence score of the recommended actions?",
        StructuredQuery(
            object_type="RecommendedAction", operation="avg", aggregate_property="confidence_score"
        ),
    ),
    NlQueryFixture(
        "agg-max-feeder-current",
        "aggregate",
        "What is the maximum rated current among the feeders?",
        StructuredQuery(
            object_type="Asset",
            operation="max",
            aggregate_property="rated_current_a",
            filters=[_f("asset_type", "eq", "feeder")],
        ),
    ),
    NlQueryFixture(
        "agg-max-temperature-reading",
        "aggregate",
        "What is the highest temperature reading recorded?",
        StructuredQuery(
            object_type="OperationalEvent",
            operation="max",
            aggregate_property="measured_value",
            measured_kind="temperature",
        ),
    ),
)

# --- aggregate + explicit group_by -------------------------------------------------------
_GROUP: tuple[NlQueryFixture, ...] = (
    NlQueryFixture(
        "group-avg-value-by-kind",
        "aggregate_group",
        "What is the average measured value for each measured kind?",
        StructuredQuery(
            object_type="OperationalEvent",
            operation="avg",
            aggregate_property="measured_value",
            group_by="measured_kind",
        ),
    ),
    NlQueryFixture(
        "group-total-capacity-by-type",
        "aggregate_group",
        "What is the total capacity broken down by asset type?",
        StructuredQuery(
            object_type="Asset",
            operation="sum",
            aggregate_property="capacity_kw",
            group_by="asset_type",
        ),
    ),
    NlQueryFixture(
        "group-avg-capacity-by-site",
        "aggregate_group",
        "What is the average asset capacity at each site?",
        StructuredQuery(
            object_type="Asset",
            operation="avg",
            aggregate_property="capacity_kw",
            group_by="site_id",
        ),
    ),
)

# --- cross-type resolve (name -> id join) ------------------------------------------------
_RESOLVE: tuple[NlQueryFixture, ...] = (
    NlQueryFixture(
        "resolve-events-for-asset",
        "resolve",
        "List the operational events for the asset named 'Battery Bank A'.",
        StructuredQuery(
            object_type="OperationalEvent",
            operation="list",
            resolve=NameResolve(
                name="Battery Bank A", target_type="Asset", filter_property="asset_id"
            ),
        ),
    ),
    NlQueryFixture(
        "resolve-count-events-at-site",
        "resolve",
        "How many events occurred at the site named 'North Substation'?",
        StructuredQuery(
            object_type="OperationalEvent",
            operation="count",
            resolve=NameResolve(
                name="North Substation", target_type="Site", filter_property="site_id"
            ),
        ),
    ),
    NlQueryFixture(
        "resolve-assets-at-site",
        "resolve",
        "Show the assets hosted at the site named 'Central Depot'.",
        StructuredQuery(
            object_type="Asset",
            operation="list",
            resolve=NameResolve(
                name="Central Depot", target_type="Site", filter_property="site_id"
            ),
        ),
    ),
)

# --- the KNOWN-HARD aggregate-superlative class ("which X is most Y") ----------------------
# The model tends to DROP group_by + measured_kind here (the documented translate gap); the gold
# carries BOTH — the field-order-flip / two-pass lever is meant to help the model retain them.
_HARD: tuple[NlQueryFixture, ...] = (
    NlQueryFixture(
        "hard-which-asset-hottest",
        "hard_superlative",
        "Which asset has the highest temperature reading?",
        StructuredQuery(
            object_type="OperationalEvent",
            operation="max",
            aggregate_property="measured_value",
            group_by="asset_id",
            measured_kind="temperature",
        ),
        hard_class=True,
    ),
    NlQueryFixture(
        "hard-which-asset-most-current",
        "hard_superlative",
        "Which asset is drawing the most current?",
        StructuredQuery(
            object_type="OperationalEvent",
            operation="max",
            aggregate_property="measured_value",
            group_by="asset_id",
            measured_kind="current",
        ),
        hard_class=True,
    ),
    NlQueryFixture(
        "hard-which-site-highest-voltage",
        "hard_superlative",
        "Which site has the highest average voltage?",
        StructuredQuery(
            object_type="OperationalEvent",
            operation="avg",
            aggregate_property="measured_value",
            group_by="site_id",
            measured_kind="voltage",
        ),
        hard_class=True,
    ),
)

FIXTURES: tuple[NlQueryFixture, ...] = (*_LIST, *_COUNT, *_AGGREGATE, *_GROUP, *_RESOLVE, *_HARD)
"""The full nl_query A/B corpus: 8 list+filter · 4 count · 6 aggregate · 3 aggregate+group_by
· 3 resolve · 3 hard aggregate-superlative = 27 questions over the energy ontology."""

CATEGORIES: frozenset[str] = frozenset(f.category for f in FIXTURES)


# --- the scoring metric (SD-1) — field-weighted partial match on the RAW translate output --

_FIELD_WEIGHTS: dict[str, float] = {
    "object_type": 3.0,  # the type queried — heaviest; a wrong type is a wrong answer
    "operation": 3.0,  # list/count/max/min/avg/sum — heaviest
    "filters": 2.0,  # the question-implied conjunctive filters (Jaccard over property/op/value)
    "aggregate_property": 2.0,  # the numeric property aggregated
    "group_by": 2.0,  # the hard-class discriminator #1 (dropped on 'which X is most Y')
    "measured_kind": 1.0,  # the hard-class discriminator #2 (unit-coherence classification)
    "resolve": 2.0,  # the cross-type name->id join
}  # NB: `limit` is intentionally excluded (benign differences, SD-1)

_TOTAL_WEIGHT: float = sum(_FIELD_WEIGHTS.values())  # 15.0


def _filter_keys(filters: list[QueryFilter]) -> set[tuple[str, str, str]]:
    return {(flt.property, flt.op, flt.value) for flt in filters}


def _filters_similarity(gold: list[QueryFilter], pred: list[QueryFilter]) -> float:
    """Jaccard over (property, op, value) — penalises BOTH a dropped filter and a spurious one."""
    g, p = _filter_keys(gold), _filter_keys(pred)
    if not g and not p:
        return 1.0
    if not g or not p:
        return 0.0
    return len(g & p) / len(g | p)


def _resolve_match(gold: NameResolve | None, pred: NameResolve | None) -> float:
    if gold is None and pred is None:
        return 1.0
    if gold is None or pred is None:
        return 0.0
    return float(
        gold.name == pred.name
        and gold.target_type == pred.target_type
        and gold.filter_property == pred.filter_property
    )


def score_query(gold: StructuredQuery, pred: StructuredQuery) -> float:
    """Field-weighted partial structural match in [0, 1] of ``pred`` (the RAW ``_translate``
    output) against ``gold``. 1.0 = identical on every scored field; each scalar field scores
    None-aware equality (so over-specifying a field the gold leaves ``None`` is penalised), and
    ``filters`` scores a Jaccard similarity. ``limit`` is not scored (SD-1)."""
    got = 0.0
    got += _FIELD_WEIGHTS["object_type"] * float(gold.object_type == pred.object_type)
    got += _FIELD_WEIGHTS["operation"] * float(gold.operation == pred.operation)
    got += _FIELD_WEIGHTS["filters"] * _filters_similarity(gold.filters, pred.filters)
    got += _FIELD_WEIGHTS["aggregate_property"] * float(
        gold.aggregate_property == pred.aggregate_property
    )
    got += _FIELD_WEIGHTS["group_by"] * float(gold.group_by == pred.group_by)
    got += _FIELD_WEIGHTS["measured_kind"] * float(gold.measured_kind == pred.measured_kind)
    got += _FIELD_WEIGHTS["resolve"] * _resolve_match(gold.resolve, pred.resolve)
    return got / _TOTAL_WEIGHT


# --- SD-4 pre-committed pass/fail read (fixed BEFORE any live run — §8 / Lesson #0026) ------
# These thresholds are the acceptance bar the Cray-gated live A/B (Step 5) reads. They are
# recorded HERE, before any live run, and are NEVER adjusted after the run.

REGRESSION_FLOOR_TOLERANCE: float = 0.05
"""A variant arm PASSES the regression floor iff its mean ``score_query`` over the whole corpus
is >= the baseline arm's mean minus this tolerance (no material overall regression)."""

HARD_CLASS_WIN_MIN_DELTA: float = 0.05
"""A variant arm WINS the hard aggregate-superlative subset iff its mean ``score_query`` on the
``hard_class`` fixtures exceeds baseline's by at least this margin — the reasoning-order lever's
whole purpose is retaining ``group_by`` + ``measured_kind`` on 'which X is most Y'. A margin
(not delta>0) guards against reading noise on a small hand-authored set."""

LIVE_MIN_REPS: int = 3
"""N >= 3 reps in the live A/B; report the WORST rep, never the best (the small hand-authored
corpus + non-deterministic live model — read as 'X -> Y on this corpus', never a rate)."""
