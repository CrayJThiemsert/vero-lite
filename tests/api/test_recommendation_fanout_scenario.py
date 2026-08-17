"""One judgment per EVENT, not one judgment per BATCH (PLAN-0107 AC-8, ② data reach).

**What was invisible before this.** The offline LLM stub returned a single canned
object for every event in a streamed batch — same title, same confidence, same
``affected_entities`` — as its own docstring admitted. Under that stub a whole class
of defect produces byte-identical output and cannot be reddened by any assertion:

* a fan-out that maps every event to the FIRST event's judgment,
* a fan-out that reuses one record and overwrites it,
* a resolver that loses the event→judgment correspondence entirely.

Every one of those is a **correctness** failure on the surface a visitor reads —
"escalate the excursion on X" attached to Y — and every one of them was green. The
stub is now a factory deriving its judgment from the triggering event, which is what
makes the mapping assertable at all. This module is the assertion.

🔴 **Why fleet_maintenance and not energy — measured, not preferred.** The claim is
about "a streamed batch of ≥ 2 events". Counting what each vertical's synthetic
stream actually trips through ``_is_recommendation_trigger``: **energy 1** of 11,
**aquaculture 0** of 7, **supply_chain 0** of 4, **procurement 0** (it streams
nothing at all), **building_materials 2** of 2, **fleet_maintenance 5** of 5. On
energy this module's distinctness assertions would pass **vacuously** — and did, on
the first run, until the anti-vacuity test below refused them. Energy's synthetic
events are LOCKED (PLAN-0107 AC-10: ``gold.yaml`` hard-couples to them), so the
batch has to come from a vertical that already reaches the state rather than from
an edit that manufactures it.

Nothing is stubbed on either side of the seam under test. The producer is the REAL
adapter stream plus the REAL ``recommend()`` path; the consumer is the REAL
``GET /recommendations`` over HTTP. Only the model TRANSPORT is offline, which is the
one thing CLAUDE.md §8 permits — a live model would make this test host-state.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from services.api.config import settings
from services.engine.recommender import _is_recommendation_trigger
from services.engine.registry import registry

_VERTICAL = "fleet_maintenance"


@pytest.fixture
async def fleet_fanout(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> AsyncClient:
    """Register EXACTLY what the API lifespan registers, and make fleet active.

    ``discover_and_register`` is the pair the real process uses; registering the
    adapter by hand would mask the class of bug where a vertical is reachable in
    tests and 409s in production.
    """
    from services.engine.discovery import discover_and_register

    discover_and_register()
    monkeypatch.setattr(settings, "oct_vertical", _VERTICAL)
    return client


async def _triggering_events() -> list[dict]:
    """The events the fan-out will actually judge, through the REAL adapter."""
    adapter = registry.get_adapter(_VERTICAL)
    return [e async for e in adapter.stream_events("reading") if _is_recommendation_trigger(e)]


async def _recommendations(client: AsyncClient) -> list[dict]:
    response = await client.get("/recommendations")
    assert response.status_code == 200, response.text
    items: list[dict] = response.json()["recommendations"]
    return items


async def test_the_batch_really_carries_more_than_one_triggering_event(
    fleet_fanout: AsyncClient,
) -> None:
    """Anti-vacuity: "distinct judgments" is unfalsifiable on a one-event batch.

    Every assertion below compares judgments to each other, so a batch that tripped
    exactly one recommendation would make them all pass while proving nothing. This
    test is not decoration — it is the one that caught exactly that on the first run
    of this module, against energy.
    """
    items = await _recommendations(fleet_fanout)
    assert len(items) >= 2, (
        f"the fan-out produced {len(items)} recommendation(s). With fewer than two "
        "there is nothing to compare, so every distinctness assertion in this module "
        "would be vacuously true."
    )


async def test_each_event_gets_its_own_judgment_not_the_first_events(
    fleet_fanout: AsyncClient,
) -> None:
    """The load-bearing claim: judgments are DISTINCT across a streamed batch."""
    items = await _recommendations(fleet_fanout)
    titles = [item["title"] for item in items]
    assert len(set(titles)) == len(titles), (
        f"{len(titles)} recommendations collapsed to {len(set(titles))} distinct "
        f"title(s): {titles}. Every event received the same judgment — the shape a "
        "fan-out bug produces, and the shape the old canned stub could not reveal."
    )


async def test_every_triggering_event_is_represented_exactly_once(
    fleet_fanout: AsyncClient,
) -> None:
    """Distinctness alone is not correspondence — the mapping itself is asserted.

    A fan-out could hand out distinct judgments and still attach them to the wrong
    events (an off-by-one over the stream), or judge one event twice and drop
    another. This pins the judgment set against the triggering-event set by the only
    key both sides carry over HTTP: the ``event_id`` the stub puts in the title.
    """
    events = await _triggering_events()
    expected = {str(event["event_id"]) for event in events}
    assert expected, "the adapter tripped no recommendation — nothing to correspond to"

    items = await _recommendations(fleet_fanout)
    claimed = [
        next((eid for eid in expected if f"[{eid}]" in item["title"]), None) for item in items
    ]
    unattributed = [
        item["action_id"] for item, eid in zip(items, claimed, strict=True) if eid is None
    ]
    assert not unattributed, (
        f"{len(unattributed)} recommendation(s) name no triggering event in their title: "
        f"{unattributed}. The judgment cannot be traced back to the event it is about."
    )
    assert sorted(filter(None, claimed)) == sorted(expected), (
        f"the fan-out judged {sorted(filter(None, claimed))} but the stream tripped "
        f"{sorted(expected)} — an event was judged twice, or dropped."
    )


async def test_each_judgment_names_the_entity_of_its_own_event(
    fleet_fanout: AsyncClient,
) -> None:
    """The prose and the structured entities must agree, per record.

    A record that mixed one event's prose with another's entities would pass both
    the distinctness and the correspondence test above while still being wrong on
    screen. This is the cross-check.
    """
    items = await _recommendations(fleet_fanout)
    for item in items:
        entities = [entity["primary_key"] for entity in item["affected_entities"]]
        assert entities, f"recommendation {item['action_id']} names no affected entity"
        assert any(key in item["title"] for key in entities), (
            f"recommendation {item['action_id']!r} has title {item['title']!r} but "
            f"affected entities {entities} — prose and entities disagree, which is "
            "what a crossed event→judgment mapping looks like."
        )
