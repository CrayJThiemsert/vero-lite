"""PLAN-0051 Step 4 — nl_query reason-then-structure arm plumbing + offline driver (AC-4).

The structural gate (CLAUDE.md §8, zero host-state): the three A/B arms — ``baseline`` /
``field_order_flip`` / ``two_pass`` — are wired into ``_translate`` correctly:

* each selects the right schema/call-shape; the two-pass constrained call OMITS ``think``
  (CHECKPOINT-0 / Ollama #15260);
* the ``field_order_flip`` leading advisory ``reasoning`` field is STRIPPED before execute
  (StructuredQuery ignores it) — advisory only (SD-2);
* the production semantic validator (``_validate_query``) still gates EVERY arm, and the driver
  returns the RAW ``_translate`` output — the Phase-B rewrite seam is not invoked, so the SD-1
  metric scores the raw output (never the seam-repaired result);
* the shipped default is ``baseline`` (byte-identical, R1).

The A/B *accuracy* measurement is the separate live twin metric (Step 5, behind a Cray
host-state go); THIS proves only the plumbing, through a stub ``ChatClient`` — no MS-S1 call.
"""

from __future__ import annotations

import json

import pytest

from services.engine.llm.client import ChatResult
from services.engine.nl_query import (
    QueryTranslationError,
    StructuredQuery,
    TranslateArm,
    _query_schema,
    _query_schema_reasoning_first,
    _translate,
)
from services.engine.ontology_meta import load_ontology_meta
from tests.services.engine.nl_query_ab_fixtures import FIXTURES, score_query
from tests.services.engine.reason_then_structure_nl_query_ab import translate_ab_query

VERTICAL = "energy"
_ARMS: list[TranslateArm] = ["baseline", "field_order_flip", "two_pass"]


class _StubQueryClient:
    """Replays canned query JSON in call order, recording each call's ``{think, has_format,
    response_format}``. CHECKPOINT-0 assertion baked in (never ``think=False`` + ``format``)."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self._index = 0
        self.calls: list[dict[str, object]] = []

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, object] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        assert not (
            think is False and response_format is not None
        ), "think=False + format (Ollama #15260)"
        self.calls.append(
            {
                "think": think,
                "has_format": response_format is not None,
                "response_format": response_format,
            }
        )
        if self._index >= len(self._responses):
            raise AssertionError("_StubQueryClient: no more recorded responses")
        content = self._responses[self._index]
        self._index += 1
        return ChatResult(content=content, thinking=None, model="gpt-oss:20b-recorded", raw={})


def _canned(
    gold: StructuredQuery, arm: TranslateArm, *, drop: dict[str, object] | None = None
) -> str:
    """The canned constrained-call response for ``gold``. ``field_order_flip`` prepends a leading
    advisory ``reasoning`` key (which the parser must strip); ``drop`` overrides fields to mimic
    a model that under-specifies (e.g. dropping ``group_by`` on a superlative)."""
    data: dict[str, object] = json.loads(gold.model_dump_json())
    if drop is not None:
        data.update(drop)
    if arm == "field_order_flip":
        data = {"reasoning": "the question implies this query", **data}
    return json.dumps(data)


def _responses_for(
    arm: TranslateArm, gold: StructuredQuery, *, drop: dict[str, object] | None = None
) -> list[str]:
    """two_pass consumes a free-form reasoning response first; the single-call arms don't."""
    canned = _canned(gold, arm, drop=drop)
    return ["free-form reasoning prose", canned] if arm == "two_pass" else [canned]


# --- AC-4(a): the field-order-flip schema emits a leading advisory reasoning field ----------


def test_field_order_flip_schema_puts_reasoning_first() -> None:
    """AC-4(a) / SD-2: the field_order_flip schema emits a leading ``reasoning`` string BEFORE
    ``object_type`` (the decision), both required; ``object_type`` stays enum-pinned. The
    baseline schema has NO reasoning field and leads with object_type."""
    type_names = [t.name for t in load_ontology_meta(VERTICAL).object_types]
    flipped = _query_schema_reasoning_first(type_names)
    assert next(iter(flipped["properties"])) == "reasoning"
    assert flipped["required"][:2] == ["reasoning", "object_type"]
    assert flipped["properties"]["object_type"]["enum"] == type_names

    base = _query_schema(type_names)
    assert "reasoning" not in base["properties"]
    assert next(iter(base["properties"])) == "object_type"


async def test_field_order_flip_strips_the_advisory_reasoning_field() -> None:
    """AC-4 / SD-2 (R3): the leading ``reasoning`` field is dropped before execute — a response
    carrying it parses to a StructuredQuery byte-identical to the gold (StructuredQuery has no
    ``reasoning`` field; the grounding receipt is unchanged from baseline)."""
    gold = FIXTURES[0].gold
    client = _StubQueryClient(_responses_for("field_order_flip", gold))
    query = await translate_ab_query(client, "q", vertical=VERTICAL, arm="field_order_flip")
    assert query == gold
    assert not hasattr(query, "reasoning")


# --- AC-4(b): two_pass reasons (formatless) THEN structures (omitting think) -----------------


async def test_two_pass_reasons_then_structures() -> None:
    """AC-4(b): the two_pass arm issues a free-form reasoning call (no ``format``, ``think=True``)
    BEFORE the constrained call, and the constrained call OMITS ``think`` (CHECKPOINT-0)."""
    client = _StubQueryClient(_responses_for("two_pass", FIXTURES[0].gold))
    await translate_ab_query(client, "q", vertical=VERTICAL, arm="two_pass")
    assert len(client.calls) == 2
    assert client.calls[0]["has_format"] is False
    assert client.calls[0]["think"] is True
    assert client.calls[1]["has_format"] is True
    assert client.calls[1]["think"] is None


async def test_single_call_arms_make_one_constrained_call() -> None:
    """AC-4(b) contrast: baseline + field_order_flip each make exactly ONE constrained call
    (``format`` on, ``think`` omitted) — no reasoning pass."""
    for arm in ("baseline", "field_order_flip"):
        client = _StubQueryClient(_responses_for(arm, FIXTURES[0].gold))
        await translate_ab_query(client, "q", vertical=VERTICAL, arm=arm)
        assert len(client.calls) == 1, arm
        assert client.calls[0]["has_format"] is True, arm
        assert client.calls[0]["think"] is None, arm


# --- AC-4: every arm round-trips a perfect canned query; the driver returns RAW translate -----


@pytest.mark.parametrize("arm", _ARMS)
async def test_every_arm_round_trips_gold_to_score_one(arm: TranslateArm) -> None:
    """AC-4: drive all 27 fixtures through the shared driver for each arm, feeding a canned
    response equal to the gold. The parsed query scores a perfect 1.0 in EVERY arm — the arm
    plumbing does not corrupt the parse, and the field_order_flip reasoning field is stripped.
    (Canned responses, so this is the DRIVER, not an accuracy measurement — the live lift is
    Step 5.)"""
    for fx in FIXTURES:
        client = _StubQueryClient(_responses_for(arm, fx.gold))
        query = await translate_ab_query(client, fx.question, vertical=VERTICAL, arm=arm)
        assert score_query(fx.gold, query) == pytest.approx(1.0), f"{fx.fixture_id} [{arm}]"


async def test_driver_returns_raw_translate_not_seam_repaired() -> None:
    """SD-1: the driver returns the RAW ``_translate`` output — the Phase-B seam is NOT invoked,
    so a model that DROPS ``group_by`` on a superlative (the documented failure) comes back with
    ``group_by=None`` and scores below 1.0. Scoring the raw output is what isolates the lever."""
    hard = next(f for f in FIXTURES if f.hard_class)
    client = _StubQueryClient(_responses_for("baseline", hard.gold, drop={"group_by": None}))
    query = await translate_ab_query(client, hard.question, vertical=VERTICAL, arm="baseline")
    assert query.group_by is None  # RAW — the seam did not run in the driver
    assert score_query(hard.gold, query) < 1.0


# --- AC-4: the production validator gates EVERY arm (unchanged) ------------------------------


@pytest.mark.parametrize("arm", _ARMS)
async def test_validator_gates_every_arm(arm: TranslateArm) -> None:
    """AC-4: ``_validate_query`` still gates every arm — a query naming an unknown object_type
    is rejected on each attempt and, with the budget exhausted, raises QueryTranslationError.
    The arm moves only the prompt/schema, never the semantic gate."""
    bad = json.dumps({"object_type": "NotARealType", "operation": "list"})
    responses = ["reasoning prose", bad] if arm == "two_pass" else [bad]
    client = _StubQueryClient(responses)
    with pytest.raises(QueryTranslationError):
        await translate_ab_query(client, "q", vertical=VERTICAL, arm=arm, retry_budget=1)


# --- AC-4 / R1: the shipped default is baseline ---------------------------------------------


async def test_translate_default_arm_is_baseline() -> None:
    """AC-4 / R1: ``_translate`` called WITHOUT an arm makes exactly one constrained call with
    the baseline schema (no leading reasoning field, object_type first) — byte-identical to the
    shipped path, so ``answer_question`` is unaffected."""
    meta = load_ontology_meta(VERTICAL)
    type_index = {t.name: t for t in meta.object_types}
    gold = FIXTURES[0].gold
    client = _StubQueryClient([json.dumps(json.loads(gold.model_dump_json()))])
    await _translate(client, "q", VERTICAL, meta, type_index, retry_budget=1)
    assert len(client.calls) == 1
    assert client.calls[0]["has_format"] is True
    assert client.calls[0]["think"] is None
    schema = client.calls[0]["response_format"]
    assert isinstance(schema, dict)
    assert "reasoning" not in schema["properties"]
    assert next(iter(schema["properties"])) == "object_type"
