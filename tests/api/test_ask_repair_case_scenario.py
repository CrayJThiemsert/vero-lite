"""PLAN-0109 AC-8 + AC-9 — a case opened through the real intake route is answered from Ask.

CLAUDE.md §8 scenario test, binding: the **real producer into the real consumer on
realistic simulated data**.

* **Producer** — ``POST /api/cases`` and ``POST /api/cases/{id}/quotes`` on the real app,
  writing through the real session to the disposable test database: the same routes demo
  play uses on Tab I.
* **Consumer** — ``answer_question`` with the real fleet adapter registered against that
  same database: translate → validate → retrieve → match → phrase, all shipped code.
* **The one canned element** is the model TRANSPORT (``TranslateOnlyStub``, the PLAN-0104
  precedent): the translate call returns fixed JSON, and the phrase call fails so the
  engine's own deterministic sentence is what gets asserted.

⚠️ **No claim that the live model emits these translations** — that is AC-14's, and only a
Cray-gated live smoke can make it. In particular this module CANNOT see that object-level
synonyms never reach the translate prompt (measured s294: ``เคสซ่อม`` is absent from
``_describe_ontology``): the canned translation names ``RepairCase`` directly, so a live
model's ability to map the Thai word onto the type is outside what any assertion here tests.

**Why this lives in ``tests/api/`` and not in the PLAN's ``tests/verticals/fleet_maintenance/``.**
``client_with_db`` and ``api_db_maker`` are defined in ``tests/api/conftest.py``; a copy of
them would be a second definition of how a test binds to the disposable database.

DB-backed — SKIPS when Postgres is unreachable, and a skip is never satisfaction.
"""

from __future__ import annotations

from typing import Any

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from services.engine.nl_query import NlAnswer, answer_question
from services.engine.registry import registry
from tests.support.nl_query_transport_stub import TranslateOnlyStub
from verticals.fleet_maintenance.data_adapter.db_objects import FleetMaintenanceAdapter

_VERTICAL = "fleet_maintenance"
_COUNT_CASES: dict[str, Any] = {"object_type": "RepairCase", "operation": "count"}


def _register_against(maker: async_sessionmaker[AsyncSession]) -> None:
    registry.register_adapter(FleetMaintenanceAdapter(session_factory=maker))


async def _open_case(client: AsyncClient, truck_id: str, description: str) -> dict[str, Any]:
    response = await client.post(
        "/api/cases", json={"truck_id": truck_id, "description": description}
    )
    assert response.status_code == 201, response.text
    return dict(response.json())


async def _ask(question: str, query: dict[str, Any]) -> NlAnswer:
    return await answer_question(question, _VERTICAL, client=TranslateOnlyStub(query))


async def test_cases_opened_through_the_real_route_are_counted_from_ask(
    client_with_db: AsyncClient, api_db_maker: async_sessionmaker[AsyncSession]
) -> None:
    """Two cases in, a grounded count of two out — and a third case moves the read to three."""
    _register_against(api_db_maker)
    first = await _open_case(client_with_db, "truck-01", "เบรกไม่อยู่ ขาลงเขา")
    second = await _open_case(client_with_db, "truck-02", "ยางหลังแตก")

    answer = await _ask("มีเคสซ่อมกี่เคส", _COUNT_CASES)

    assert answer.grounded is True
    assert sorted(answer.source_object_ids) == sorted([first["case_id"], second["case_id"]])
    assert answer.answer == "2 RepairCase record(s) match that query."

    await _open_case(client_with_db, "truck-03", "แอร์ไม่เย็น")
    again = await _ask("มีเคสซ่อมกี่เคส", _COUNT_CASES)

    # The named changing output: the SAME question's answer moves because a row was added
    # through the route — the rows flowed; nothing here is a fixture.
    assert again.answer == "3 RepairCase record(s) match that query."


async def test_a_truck_filter_answers_about_that_trucks_case_only(
    client_with_db: AsyncClient, api_db_maker: async_sessionmaker[AsyncSession]
) -> None:
    """The ref the ontology declares is the key a question filters on."""
    _register_against(api_db_maker)
    await _open_case(client_with_db, "truck-01", "เบรกไม่อยู่")
    target = await _open_case(client_with_db, "truck-02", "ยางแตก")

    answer = await _ask(
        "truck-02 มีเคสซ่อมกี่เคส",
        {
            "object_type": "RepairCase",
            "operation": "count",
            "filters": [{"property": "truck_id", "op": "eq", "value": "truck-02"}],
        },
    )

    assert answer.source_object_ids == [target["case_id"]]


async def test_a_quote_reaches_ask_with_its_vendor_and_without_its_note(
    client_with_db: AsyncClient, api_db_maker: async_sessionmaker[AsyncSession]
) -> None:
    """SD-D through the real producer: ``vendor`` is ruled IN, ``note`` is ruled OUT."""
    _register_against(api_db_maker)
    case = await _open_case(client_with_db, "truck-01", "เบรกไม่อยู่")
    response = await client_with_db.post(
        f"/api/cases/{case['case_id']}/quotes",
        data={"vendor": "อู่ช่างเอก", "amount_thb": "12000.00", "note": "ลูกค้าประจำ ขอส่วนลด"},
    )
    assert response.status_code == 201, response.text
    # Positive control: the producer really stored a note, so its absence below is an
    # exclusion and not an empty field.
    assert response.json()["note"] == "ลูกค้าประจำ ขอส่วนลด"

    answer = await _ask(
        "ใบเสนอราคามีอะไรบ้าง", {"object_type": "RepairCaseQuote", "operation": "list"}
    )

    assert len(answer.source_objects) == 1
    record = answer.source_objects[0]
    assert record["vendor"] == "อู่ช่างเอก"
    assert "note" not in record


async def test_an_unreachable_database_degrades_to_the_honest_answer() -> None:
    """AC-9: no database, no invented count — the engine's own retrieval-failure answer."""
    engine = create_async_engine("postgresql+asyncpg://nobody@127.0.0.1:1/unreachable")
    try:
        _register_against(async_sessionmaker(engine))
        answer = await _ask("มีเคสซ่อมกี่เคส", _COUNT_CASES)
    finally:
        await engine.dispose()

    assert answer.grounded is False
    assert answer.answer == "I couldn't retrieve the operational data to answer that."
