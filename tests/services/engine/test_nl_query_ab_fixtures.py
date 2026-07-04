"""PLAN-0051 Step 3 — offline validators for the nl_query A/B corpus + scoring metric (AC-3).

Zero host-state (CLAUDE.md §8): asserts the hand-authored corpus is well-formed and every gold
:class:`StructuredQuery` PASSES the production ``_validate_query`` against the real energy
ontology (a gold that fails the semantic validator is a corpus bug, not a model finding), and
that the pre-committed ``score_query`` metric behaves as specified. No model call.
"""

from __future__ import annotations

import pytest

from services.engine.nl_query import QueryFilter, StructuredQuery, _validate_query
from services.engine.ontology_meta import ObjectTypeMeta, load_ontology_meta
from tests.services.engine.nl_query_ab_fixtures import (
    CATEGORIES,
    FIXTURES,
    HARD_CLASS_WIN_MIN_DELTA,
    LIVE_MIN_REPS,
    REGRESSION_FLOOR_TOLERANCE,
    score_query,
)


def _energy_type_index() -> dict[str, ObjectTypeMeta]:
    """The object-type index the production ``_validate_query`` checks a query against."""
    return {t.name: t for t in load_ontology_meta("energy").object_types}


# --- corpus shape (AC-3 / SD-1) ------------------------------------------------------------


def test_corpus_size_and_category_coverage() -> None:
    """AC-3: ~27 questions spanning every SD-1 category — list+filter, count, aggregate,
    aggregate+group_by, resolve, and the hard aggregate-superlative class."""
    assert len(FIXTURES) == 27
    assert CATEGORIES == {
        "list_filter",
        "count",
        "aggregate",
        "aggregate_group",
        "resolve",
        "hard_superlative",
    }
    # a meaningful count per bucket (not one token example)
    by_cat = {c: sum(1 for f in FIXTURES if f.category == c) for c in CATEGORIES}
    assert by_cat["list_filter"] == 8
    assert by_cat["count"] == 4
    assert by_cat["aggregate"] == 6
    assert by_cat["aggregate_group"] == 3
    assert by_cat["resolve"] == 3
    assert by_cat["hard_superlative"] == 3


def test_fixture_ids_unique_and_questions_nonempty() -> None:
    ids = [f.fixture_id for f in FIXTURES]
    assert len(ids) == len(set(ids))
    assert all(f.question.strip() for f in FIXTURES)


def test_hard_class_golds_carry_group_by_and_measured_kind() -> None:
    """SD-1: the hard aggregate-superlative golds carry BOTH discriminating fields — the exact
    pair the model tends to drop, and what the reasoning-order lever is meant to help retain."""
    hard = [f for f in FIXTURES if f.hard_class]
    assert len(hard) == 3
    for fx in hard:
        assert fx.category == "hard_superlative"
        assert fx.gold.group_by is not None, fx.fixture_id
        assert fx.gold.measured_kind is not None, fx.fixture_id
        assert fx.gold.operation in {"max", "min", "avg", "sum"}, fx.fixture_id


# --- every gold passes the PRODUCTION semantic validator (AC-3) -----------------------------


def test_every_gold_passes_the_production_validator() -> None:
    """AC-3 (the corpus-is-valid gate): each gold StructuredQuery passes the SAME
    ``_validate_query`` the translate loop enforces, against the real energy ontology. A gold
    that fails is a corpus bug — this keeps the A/B measuring the model, not a broken oracle."""
    type_index = _energy_type_index()
    for fx in FIXTURES:
        errors = _validate_query(fx.gold, type_index)
        assert errors == [], f"{fx.fixture_id}: gold is not a valid query — {errors}"


# --- the scoring metric (SD-1 / SD-4) -------------------------------------------------------


def test_score_of_gold_against_itself_is_one() -> None:
    """A gold scored against itself is a perfect 1.0 on every fixture (the metric's fixed point)."""
    for fx in FIXTURES:
        assert score_query(fx.gold, fx.gold) == pytest.approx(1.0), fx.fixture_id


def test_score_is_bounded_unit_interval() -> None:
    """The metric is bounded in [0, 1] even for a wholly-wrong prediction."""
    wrong = StructuredQuery(object_type="Site", operation="count")
    for fx in FIXTURES:
        s = score_query(fx.gold, wrong)
        assert 0.0 <= s <= 1.0, fx.fixture_id


def test_dropping_hard_class_fields_lowers_the_score_by_their_weight() -> None:
    """SD-1 discriminating power: a raw prediction that DROPS ``group_by`` + ``measured_kind`` on
    a hard-superlative gold (the documented model failure) scores exactly 12/15 = 0.8 — the
    group_by (2) + measured_kind (1) weight out of 15 — strictly below the gold's 1.0. This is
    the signal the field-order / two-pass lever is measured on."""
    hard = next(f for f in FIXTURES if f.hard_class)
    dropped = hard.gold.model_copy(update={"group_by": None, "measured_kind": None})
    assert score_query(hard.gold, dropped) == pytest.approx(12.0 / 15.0)
    assert score_query(hard.gold, dropped) < score_query(hard.gold, hard.gold)


def test_score_penalises_a_spurious_filter() -> None:
    """None-aware / set-based scoring penalises OVER-specification: adding a filter the gold
    lacks drops the filters-field Jaccard below 1.0, so the total score falls below 1.0."""
    simple = next(f for f in FIXTURES if f.category == "aggregate" and not f.gold.filters)
    extra = simple.gold.model_copy(
        update={"filters": [QueryFilter(property="status", op="eq", value="active")]}
    )
    assert score_query(simple.gold, extra) < 1.0


def test_precommitted_thresholds_are_sane() -> None:
    """SD-4: the pre-committed live-read constants exist and are in a sane range (recorded here
    BEFORE any live run; never adjusted after)."""
    assert 0.0 < REGRESSION_FLOOR_TOLERANCE < 0.5
    assert 0.0 < HARD_CLASS_WIN_MIN_DELTA < 0.5
    assert LIVE_MIN_REPS >= 3
