"""Scenario — a supplier-evaluation question, end to end offline (PLAN-0117 AC-4).

CLAUDE.md §8, binding: a scenario test drives the **real producer into the real
consumer on realistic simulated data**. The only thing stubbed here is the model
*transport*; every stage that touches or shapes data is the shipped one:

    translate -> canned constrained-JSON (the transport stub — the established
                 offline pattern for this module)
    execute   -> the real filter path over the REAL registered fleet synthetic
                 adapter's `vendor_records()`
    phrase    -> the real deterministic template, reached by failing the phrase
                 transport

⚠️ **This makes NO claim that any live model emits these translations.** The
translate JSON is canned by design; whether a wider ontology vocabulary helps a
live model is measured on MS-S1 against `benchmarks/nl_query_feasibility/`
(PLAN-0117 SD-6) and is explicitly unmeasured here.

**Filter values are STRINGS, including for `bool`.** Measured while writing this
test: `{"property": "is_contracted", "op": "eq", "value": true}` (a JSON boolean)
fails translate validation and degrades to "I couldn't translate that question",
while `"true"` executes. That is the engine's contract, not a preference.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from services.engine.nl_query import answer_question
from tests.support.nl_query_transport_stub import TranslateOnlyStub
from verticals.fleet_maintenance.data_adapter import (
    register_fleet_maintenance_adapter,
    synthetic,
)

#: Hand-derived from `vendor_records()` and pinned as LITERALS on purpose.
#: Deriving the expectation from the same seed the engine reads would make this
#: test agree with itself — a seed edit would move both sides and redden nothing.
#: `test_the_pinned_expectations_still_match_the_seed` is the drift guard that
#: makes the pinning safe.
EXPECTED_APPROVED_IDS = {"vendor-01", "vendor-02"}
EXPECTED_CONTRACTED_ID = "vendor-01"
EXPECTED_CONTRACTED_NAME = "อู่คู่สัญญา ปากช่อง"


@pytest.fixture
def fleet_adapter() -> Iterator[None]:
    """Register the real fleet synthetic adapter for the duration of a test."""
    register_fleet_maintenance_adapter()
    yield


def _q(operation: str, prop: str, value: str) -> dict[str, Any]:
    return {
        "object_type": "Vendor",
        "operation": operation,
        "filters": [{"property": prop, "op": "eq", "value": value}],
    }


async def test_counting_approved_garages_runs_on_real_rows(fleet_adapter: None) -> None:
    """ "How many garages are cleared to receive work?" — the count band.

    The ids are the seed's own `vendor_id`s, which is what proves rows flowed
    through the adapter rather than a constant being echoed back.
    """
    ans = await answer_question(
        "อู่ไหนที่สถานะใช้งานได้บ้าง",
        "fleet_maintenance",
        client=TranslateOnlyStub(_q("count", "standing", "approved")),
    )
    assert ans.grounded is True
    assert ans.result_count == len(EXPECTED_APPROVED_IDS)
    assert set(ans.source_object_ids) == EXPECTED_APPROVED_IDS


async def test_looking_up_the_contracted_garage_names_it(fleet_adapter: None) -> None:
    """ "Which garage is our contracted one?" — `is_contracted`, the narrative's อู่คู่สัญญา.

    Asserts the phrased answer carries the vendor's `title_key` (`name`), so the
    phrase step really rendered the retrieved record.
    """
    ans = await answer_question(
        "อู่คู่สัญญาของเราคืออู่ไหน",
        "fleet_maintenance",
        client=TranslateOnlyStub(_q("list", "is_contracted", "true")),
    )
    assert ans.grounded is True
    assert set(ans.source_object_ids) == {EXPECTED_CONTRACTED_ID}
    assert EXPECTED_CONTRACTED_NAME in ans.answer


async def test_a_dormant_property_reaches_the_honest_no_records_answer(
    fleet_adapter: None,
) -> None:
    """The dormant band (SD-3a requirement (b)) — declared, unpopulated, honest.

    `sanctions_flag` is declared so the LLM can use it the day a value exists, and
    carries no value today. A question filtering on it must terminate in the
    deterministic no-records answer and must NOT invent a garage.

    📌 **Measured, and it differs from PLAN-0117 AC-4's prose.** The AC describes
    this outcome as "grounded-but-empty"; the engine actually returns
    `grounded=False` with `result_count=0` via the no-data path — the same shape
    the s265 fleet benchmark measured for `fl-10`. The operative requirement (the
    honest no-records answer, never a fabricated fact) holds; only the AC's
    parenthetical description of `grounded` does not. Asserted as measured.
    """
    ans = await answer_question(
        "มีอู่ไหนติดแบล็กลิสต์บ้าง",
        "fleet_maintenance",
        client=TranslateOnlyStub(_q("list", "sanctions_flag", "true")),
    )
    # Green control FIRST: translate still produced a query. Under a mutation that
    # seeds the dormant property, this stays green — so a redden below is the
    # no-records path losing its emptiness, not the question failing to translate.
    assert ans.query is not None
    assert ans.result_count == 0
    assert ans.grounded is False
    assert set(ans.source_object_ids) == set()
    # Positive control for the two absence claims above: an empty result set and
    # an empty id list are also what a crashed run produces. The deterministic
    # no-records TEXT is the thing only the real no-data path emits.
    assert "No Vendor records match that query." in ans.answer
    # And it invented nothing: no seeded garage name appears in the answer.
    assert not [r["name"] for r in synthetic.vendor_records() if r["name"] in ans.answer]


def test_the_pinned_expectations_still_match_the_seed() -> None:
    """The drift guard that makes pinning literals above safe.

    If the seed legitimately changes, this reddens and names what to update —
    rather than the scenario tests silently re-deriving and proving nothing.
    """
    rows = synthetic.vendor_records()
    assert rows, "no vendor rows — every expectation below would be vacuous"
    assert {r["vendor_id"] for r in rows if r.get("standing") == "approved"} == (
        EXPECTED_APPROVED_IDS
    )
    contracted = [r for r in rows if r.get("is_contracted") is True]
    assert [r["vendor_id"] for r in contracted] == [EXPECTED_CONTRACTED_ID]
    assert contracted[0]["name"] == EXPECTED_CONTRACTED_NAME
    # The filter must actually filter: a seed where every row matched would make
    # the scenario assertions pass without the WHERE clause doing anything.
    assert len(EXPECTED_APPROVED_IDS) < len(rows)
