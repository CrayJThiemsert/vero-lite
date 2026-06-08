"""Loader + dataset-consistency unit tests (PLAN-0019 B-β) — pure, offline.

Beyond the loader mechanics, the consistency test is the authoring guard: every
seed item's declared ground truth must agree with the deterministic classifier
(so the dataset and the engine semantics never silently drift apart).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from benchmarks.procedure_baseline.grader import classify_disposition
from benchmarks.procedure_baseline.loader import DATASET_DIR, load_all, load_dataset
from benchmarks.procedure_baseline.schema import Disposition

_GRADED_FIELDS = ("affected_primary_key", "valid_handlers", "payload_contains", "action_keywords")


def test_load_all_returns_the_three_example_verticals() -> None:
    datasets = load_all()
    assert {dataset.vertical for dataset in datasets} == {"aquaculture", "energy", "supply_chain"}
    for dataset in datasets:
        assert dataset.items, f"{dataset.vertical}: dataset is empty"


def test_dataset_dir_is_the_packaged_dataset_folder() -> None:
    assert DATASET_DIR.is_dir()
    assert sorted(p.name for p in DATASET_DIR.glob("*.yaml")) == [
        "aquaculture.yaml",
        "energy.yaml",
        "supply_chain.yaml",
    ]


def test_every_item_is_self_consistent() -> None:
    """Each item's declared disposition matches the deterministic classifier;
    action_expected == (disposition is breach); breach items declare a graded field."""
    for dataset in load_all():
        for item in dataset.items:
            actual = classify_disposition(item.scenario)
            assert (
                actual is item.expected.disposition
            ), f"{item.id}: classifier says {actual}, dataset says {item.expected.disposition}"
            is_breach = item.expected.disposition is Disposition.BREACH
            assert (
                item.expected.action_expected is is_breach
            ), f"{item.id}: action_expected must equal (disposition is breach)"
            if is_breach:
                declared = [getattr(item.expected, field) for field in _GRADED_FIELDS]
                assert any(
                    value is not None for value in declared
                ), f"{item.id}: a breach item must declare at least one graded field"


def test_item_ids_are_globally_unique() -> None:
    ids = [item.id for dataset in load_all() for item in dataset.items]
    assert len(ids) == len(set(ids)), "duplicate item id across datasets"


def test_every_dataset_covers_all_three_dispositions() -> None:
    """SD-B2 coverage: each vertical exercises breach, watch, and ok."""
    for dataset in load_all():
        seen = {item.expected.disposition for item in dataset.items}
        assert seen == set(Disposition), f"{dataset.vertical}: missing {set(Disposition) - seen}"


def test_malformed_item_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("vertical: x\nprocedure: p\nitems:\n  - id: only-an-id\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_dataset(bad)


def test_unknown_field_is_rejected(tmp_path: Path) -> None:
    """extra='forbid' catches a typo'd key instead of silently dropping it."""
    bad = tmp_path / "extra.yaml"
    bad.write_text(
        "vertical: x\nprocedure: p\nitems:\n"
        "  - id: i1\n    description: d\n    surprise: oops\n"
        "    scenario: {event_id: e, entity_type: Pond, primary_key: p, "
        "measured_value: 1.0, unit: mg/L, threshold: 4.0, direction: below}\n"
        "    expected: {disposition: breach, action_expected: true, valid_handlers: [echo]}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError):
        load_dataset(bad)
