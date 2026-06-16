"""Offline tests for B-γ arm (b) — raw text-to-SQL (PLAN-0027 AC-2).

Pure, no network: the per-scenario DB builds from the breach ``Scenario`` (its
breached entity + distractor siblings), a correct discovery SELECT scores
entity-ID PASS, a non-SELECT is refused, a generation error is invalid, and the
action-class is recorded as structurally N/A (the D-3 finding).
"""

from __future__ import annotations

import json
from typing import Any

from benchmarks.procedure_baseline.schema import Scenario, SiblingReading
from benchmarks.procedure_comparison.text_to_sql_arm import (
    ACTION_CLASS_NA,
    build_scenario_db,
    entity_in_result,
    run_item_b,
)
from services.engine.llm.client import ChatResult


def _scenario(**overrides: Any) -> Scenario:
    base: dict[str, Any] = {
        "event_id": "energy-evt-h01",
        "entity_type": "Asset",
        "primary_key": "asset-E101",
        "measured_value": 98.0,
        "unit": "celsius",
        "threshold": 90.0,
        "direction": "above",
        "watch_margin": 5.0,
        "distractors": [
            SiblingReading(primary_key="asset-E102", measured_value=88.0),
            SiblingReading(primary_key="asset-E103", measured_value=86.5),
        ],
    }
    base.update(overrides)
    return Scenario.model_validate(base)


class _SqlClient:
    """Returns one canned ``{"sql": ...}`` (or raw non-JSON) for the generate call."""

    def __init__(self, content: str) -> None:
        self._content = content
        self.calls: list[dict[str, Any]] = []

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        self.calls.append({"has_format": response_format is not None})
        return ChatResult(content=self._content, thinking=None, model="mock", raw={})


def _sql(sql: str) -> str:
    return json.dumps({"sql": sql})


def _scalar(conn: Any, sql: str) -> Any:
    return conn.execute(sql).fetchone()[0]


def test_build_scenario_db_has_breach_and_distractors() -> None:
    conn = build_scenario_db(_scenario())
    assert _scalar(conn, "SELECT COUNT(*) FROM asset") == 3  # breach + 2 distractors
    assert _scalar(conn, "SELECT COUNT(*) FROM operational_event") == 3
    # the breach reading is present and is the only one >= the ceiling
    assert (
        _scalar(conn, "SELECT asset_id FROM operational_event WHERE measured_value >= 90")
        == "asset-E101"
    )


def test_build_scenario_db_simple_item_has_one_asset() -> None:
    conn = build_scenario_db(_scenario(distractors=[]))
    assert _scalar(conn, "SELECT COUNT(*) FROM asset") == 1


def test_entity_in_result_value_token_match() -> None:
    scenario = _scenario()
    assert entity_in_result(scenario, [("asset-E101", 98.0)])
    assert not entity_in_result(scenario, [("asset-E102", 88.0)])
    assert not entity_in_result(scenario, [])


async def test_correct_discovery_select_scores_entity_correct() -> None:
    client = _SqlClient(_sql("SELECT asset_id FROM operational_event WHERE measured_value >= 90"))

    result = await run_item_b("energy-h01", _scenario(), client, "temperature")

    assert result.outcome == "correct"
    assert result.entity_correct is True
    assert result.action_class == ACTION_CLASS_NA  # D-3: SQL cannot propose an action
    assert result.error == ""
    assert len(client.calls) == 1
    assert client.calls[0]["has_format"] is True  # generate_sql constrains {"sql": ...}


async def test_select_returning_only_distractor_scores_wrong() -> None:
    client = _SqlClient(_sql("SELECT asset_id FROM operational_event WHERE measured_value < 90"))

    result = await run_item_b("energy-h01", _scenario(), client, "temperature")

    assert result.outcome == "wrong"
    assert result.entity_correct is False


async def test_non_select_is_refused_and_invalid() -> None:
    client = _SqlClient(_sql("DELETE FROM asset"))

    result = await run_item_b("energy-h01", _scenario(), client, "temperature")

    assert result.outcome == "invalid"
    assert result.entity_correct is False
    assert "refused" in result.error


async def test_sqlite_error_is_invalid() -> None:
    client = _SqlClient(_sql("SELECT * FROM no_such_table"))

    result = await run_item_b("energy-h01", _scenario(), client, "temperature")

    assert result.outcome == "invalid"
    assert "error" in result.error.lower()


async def test_generation_error_is_invalid() -> None:
    client = _SqlClient("this is not json")  # generate_sql -> non-JSON reply

    result = await run_item_b("energy-h01", _scenario(), client, "temperature")

    assert result.outcome == "invalid"
    assert result.entity_correct is False
    assert result.error != ""
