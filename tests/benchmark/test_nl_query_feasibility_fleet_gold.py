"""Grade the FLEET gold's supplier band against the real engine (session 266).

CLAUDE.md §8: *an expected-value set is not an oracle of the system until the
system's own output is scored against it.* Until this module existed, every
`gold_fleet.yaml` case was checked only for internal self-consistency — gold
compared to gold, which reddens on a malformed file and CANNOT redden on a wrong
value. The three supplier cases (`fl-20`/`fl-21`/`fl-22`, authored s266 against
the seed PLAN-0117 landed) are graded here by the REAL engine on the REAL fleet
adapter, with only the model transport stubbed.

**Registered gap, deliberately not closed here.** `fl-01`..`fl-10` are the
control and ceiling bands; they are graded by the LIVE MS-S1 benchmark run, not
offline, and this module does not pretend otherwise. `test_the_supplier_band_is_
exactly_the_engine_graded_set` is what keeps that boundary honest: a fourth
supplier case cannot be added without landing here.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from benchmarks.nl_query_feasibility.harness import GOLD_PATH, load_gold, score_case
from services.engine.nl_query import answer_question
from tests.support.nl_query_transport_stub import TranslateOnlyStub
from verticals.fleet_maintenance.data_adapter import register_fleet_maintenance_adapter

FLEET_GOLD = GOLD_PATH.parent / "gold_fleet.yaml"

#: Case id -> the StructuredQuery the translate stage must stand in for.
#:
#: These are NOT read from gold. Gold states what the ANSWER should be; this
#: states how the question is posed to the engine. Deriving one from the other
#: would make the comparison circular — the whole point is that two independently
#: authored statements have to agree.
_HAND_AUTHORED_TRANSLATIONS: dict[str, dict[str, Any]] = {
    "fl-20": {
        "object_type": "Vendor",
        "operation": "list",
        # A bool filter is compared as a STRING; a JSON boolean fails validation.
        "filters": [{"property": "is_contracted", "op": "eq", "value": "true"}],
    },
    "fl-21": {
        "object_type": "Vendor",
        "operation": "max",
        "aggregate_property": "comeback_count",
        "group_by": "vendor_id",
    },
    "fl-22": {
        "object_type": "Vendor",
        "operation": "min",
        "aggregate_property": "avg_turnaround_days",
        "group_by": "vendor_id",
    },
}


@pytest.fixture
def fleet_adapter() -> Iterator[None]:
    register_fleet_maintenance_adapter()
    yield


#: The control + ceiling bands, fixed before s266. These are graded by the LIVE
#: MS-S1 benchmark run, not offline — a written, reviewable admission rather than
#: a silent omission. Anything in gold outside this set and outside the
#: translation table above is UNGRADED, which the partition test below refuses.
_GRADED_LIVE_NOT_HERE = {
    "fl-01",
    "fl-02",
    "fl-03",
    "fl-04",
    "fl-05",
    "fl-06",
    "fl-07",
    "fl-08",
    "fl-09",
    "fl-10",
}


def test_no_gold_case_is_left_ungraded_by_both_lanes() -> None:
    """No case may sit outside BOTH the translation table and the live-band admission.

    The load-bearing half of this module's coverage claim. Without it the
    parametrized test below would silently grade whatever happens to be in the
    table — a fourth supplier case would arrive ungraded with everything green.
    """
    _vertical, cases = load_gold(FLEET_GOLD)
    all_ids = {str(c["id"]) for c in cases}
    ungraded = sorted(all_ids - _GRADED_LIVE_NOT_HERE - set(_HAND_AUTHORED_TRANSLATIONS))
    assert not ungraded, (
        f"gold cases graded by neither lane: {ungraded} — translate them here or "
        "add them to the live-band admission with a reason"
    )
    # Two-sided: an id in a lane that gold no longer carries is equally a defect,
    # because the admission would then excuse a gap that does not exist.
    unknown = sorted((_GRADED_LIVE_NOT_HERE | set(_HAND_AUTHORED_TRANSLATIONS)) - all_ids)
    assert not unknown, f"lanes name cases gold does not carry: {unknown}"
    # Non-vacuity: an empty gold set would satisfy both checks above.
    assert len(all_ids) == 13


@pytest.mark.parametrize("case_id", sorted(_HAND_AUTHORED_TRANSLATIONS))
async def test_the_fleet_gold_agrees_with_what_the_real_engine_produces(
    case_id: str, fleet_adapter: None
) -> None:
    """Grade one gold case against the ENGINE rather than against itself.

    A mismatch here is a SURFACED FINDING, never a reason to edit gold. Which side
    drifted — the gold value or the engine — is the finding's subject, not this
    test's to decide.
    """
    _vertical, cases = load_gold(FLEET_GOLD)
    case = next(c for c in cases if c["id"] == case_id)

    client = TranslateOnlyStub(_HAND_AUTHORED_TRANSLATIONS[case_id])
    ans = await answer_question(case["text"], "fleet_maintenance", client=client)

    # Non-vacuity, BEFORE the grade: score_case reads expected_count /
    # expected_ids / expected_aggregate, so a case carrying none of them would be
    # graded on nothing at all and pass.
    assert (
        case.get("expected_count") is not None
        or case.get("expected_ids")
        or case.get("expected_aggregate")
    ), f"{case_id} carries no deterministic expectation for score_case to grade"
    assert (
        ans.grounded is case["expected_grounded"]
    ), f"{case_id}: engine grounded={ans.grounded}, gold expects {case['expected_grounded']}"

    assert score_case(case, ans) == "correct", (
        f"{case_id} SURFACED FINDING — gold and the real engine disagree. "
        f"gold count={case.get('expected_count')} aggregate={case.get('expected_aggregate')}; "
        f"engine count={ans.result_count} "
        f"aggregate={None if ans.aggregate is None else ans.aggregate.value} "
        f"groups={None if ans.aggregate is None else dict(ans.aggregate.groups)}. "
        "Do NOT edit gold to make this pass — raise it with Cray."
    )


async def test_an_absent_history_fact_stays_out_of_the_groups(fleet_adapter: None) -> None:
    """The absent-is-not-zero property, asserted on the ENGINE's own output.

    `vendor-03` carries no `comeback_count`. It must be missing from the grouped
    result entirely, not present as a 0 — a 0 would make a garage nobody has kept
    records for look like a garage with a spotless record.
    """
    ans = await answer_question(
        "Which vendor has the most comebacks?",
        "fleet_maintenance",
        client=TranslateOnlyStub(_HAND_AUTHORED_TRANSLATIONS["fl-21"]),
    )
    assert ans.aggregate is not None, "positive control: there must be an aggregate to inspect"
    groups = dict(ans.aggregate.groups)
    # Positive control for the absence claim: the two carrying vendors ARE there,
    # so an empty grouping cannot satisfy this test.
    assert {"vendor-01", "vendor-02"} <= set(groups)
    assert "vendor-03" not in groups
