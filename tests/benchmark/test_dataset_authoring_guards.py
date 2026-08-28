"""Authoring guards that must hold for EVERY vertical — including the one that
does not exist yet.

Split out of ``test_loader.py`` rather than added to it, so a probe battery's
coverage denominator is exactly these claims. In a shared module the denominator
is every claim the module holds, so a battery over these guards could never report
complete coverage and the report would say GAPS for reasons unrelated to them.

What they defend, both measured:

* A dataset supplied ``temperature`` readings while the procedure whose goal it
  threads into the *trusted* system instruction had been re-themed to feeder
  current six weeks earlier. The challenger model noticed the contradiction,
  refused the pinned action on scope grounds, and was graded WRONG for it — so
  the benchmark rewarded the model that ignored its directive.
* The benchmark registered verticals from a hand-written list of four. A vertical
  missing from it does not error; it gets an EMPTY ``suggested_handler`` enum,
  which removes the schema constraint and lets the model emit any string at all.
"""

from __future__ import annotations

from benchmarks.procedure_baseline.consistency import (
    goal_coverage,
    missing_handler_verticals,
    parameter_tokens,
)
from benchmarks.procedure_baseline.loader import load_all
from services.engine.discovery import discover_and_register
from services.engine.procedures.spec import load_procedures
from services.engine.registry import registry


def test_every_dataset_goal_names_the_quantity_its_events_carry() -> None:
    """The directive must be about the quantity the events carry — or the dataset
    must say IN WRITING why not.

    This guard cannot make an author's goal correct; it makes a mismatch
    impossible to ship *silently*.
    """
    for dataset in load_all():
        spec = load_procedures(dataset.vertical)
        procedure = next(
            (proc for proc in spec.procedures if proc.procedure_id == dataset.procedure), None
        )
        assert procedure is not None, (
            f"{dataset.vertical}: dataset names procedure '{dataset.procedure}', "
            f"which its procedures.yaml does not define"
        )
        coverage = goal_coverage(dataset.reading_parameter, procedure.goal)
        if coverage.covered:
            assert not dataset.goal_parameter_exemption, (
                f"{dataset.vertical}: declares a goal_parameter_exemption but the goal DOES "
                f"name its parameter — remove the stale exemption ({coverage.describe()})"
            )
            continue
        assert dataset.goal_parameter_exemption, (
            f"{dataset.vertical}: {coverage.describe()}. Either re-theme the dataset (or the "
            f"procedure) so they agree, or declare goal_parameter_exemption saying WHY the "
            f"numbers this file produces should not be read as model capability."
        )


def test_the_goal_parameter_rule_discriminates_in_both_directions() -> None:
    """Positive control for the guard above.

    Every shipped dataset now either passes that rule or declares an exemption, so
    the guard is green across the whole corpus — and a green that cannot redden is
    not evidence. This pins the rule against the REAL shipped goal, in both
    directions, so a widening that quietly makes it always-true fails here.
    """
    spec = load_procedures("energy")
    goal = next(
        proc for proc in spec.procedures if proc.procedure_id == "substation_health_sweep"
    ).goal

    # The real, declared mismatch: the goal is about current, the fixture measures heat.
    assert not goal_coverage("temperature", goal).covered
    # ...and the same rule matches when the quantity IS the one the goal names.
    assert goal_coverage("current", goal).covered
    # The length floor drops unit/currency codes without a hand-maintained stop-list
    # that would need editing for every new vertical's units.
    assert parameter_tokens("repair_quote_thb") == ("repair", "quote")


def test_handler_registration_is_a_rule_not_a_roster() -> None:
    """Every dataset's vertical resolves handlers WITHOUT being named by hand.

    Discovery is called DIRECTLY rather than through ``_register_all_handlers``,
    which fails closed on the same condition: routed through it, this assertion
    could only ever be reached on the happy path, so no mutation could witness it
    reddening — it would raise first, and a crash is not a witnessed red.
    """
    discover_and_register()
    for dataset in load_all():
        assert registry.handler_names(
            dataset.vertical
        ), f"{dataset.vertical}: auto-discovery registered no handlers"


def test_missing_handler_verticals_names_the_empty_ones() -> None:
    """Positive control for the assertion above.

    "No vertical is missing handlers" is satisfied by an empty vertical list and by
    an empty registry — the exact shape of the failure being guarded. A first draft
    of this check reported a clean bill of health for all four datasets while the
    registry was empty, because registration had silently failed.
    """
    assert missing_handler_verticals(["a", "b"], {"a": ["x"], "b": []}) == ["b"]
    assert missing_handler_verticals(["a", "b"], {"a": ["x"]}) == ["b"]
    assert missing_handler_verticals(["a"], {"a": ["x"]}) == []
