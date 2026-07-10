"""PLAN-0062 Step 1 (PR1b) — the ``env_band`` evaluate executor (ADR-016 D2-A3).

Offline, pure-Python, no LLM: the executor binds the runtime env band onto a
band-less ``evaluate`` step and delegates the verdict math to the shipped
:class:`EvaluateStepExecutor`, so ``classify_verdict`` stays the single band
definition (PLAN-0062 L-5 "extend, never fork").

The pinned properties: an ``in_file`` band (authored ``threshold``) delegates
through **untouched** — settings are never consulted; a band-less step takes
``OCT_RECOMMEND_THRESHOLD`` / ``OCT_RECOMMEND_DIRECTION``; the step's own
``watch_margin`` survives the rebinding; the audit discloses the band's
provenance on top of the base's own audit; and — the ADR-016 **D2-A4** guard —
the decision is made from the typed ``Step``, never from ``facet``.
"""

from __future__ import annotations

from typing import Any

import pytest

from services.api.config import settings
from services.engine.procedures.env_band_step import (
    DIRECTION_ENV_VAR,
    THRESHOLD_ENV_VAR,
    EnvBandEvaluateExecutor,
)
from services.engine.procedures.evaluate_step import EvaluateStepExecutor
from services.engine.procedures.orchestrator import RunContext
from services.engine.procedures.spec import Agent, Step, StepKind


def _executor() -> EnvBandEvaluateExecutor:
    return EnvBandEvaluateExecutor(base=EvaluateStepExecutor())


def _step(**fields: Any) -> Step:
    return Step.model_validate(
        {"step_id": "judge", "name": "Judge", "kind": StepKind.EVALUATE.value, **fields}
    )


def _ctx() -> RunContext:
    return RunContext(agent=Agent(agent_id="grid_agent", name="Grid Agent"), vertical="energy")


def _asset(asset_id: str, value: Any) -> dict[str, Any]:
    return {"asset_id": asset_id, "event_id": f"e-{asset_id}", "measured_value": value}


@pytest.fixture
def env_band(monkeypatch: pytest.MonkeyPatch) -> None:
    """The energy default band: breach at/above 90.0."""
    monkeypatch.setattr(settings, "oct_recommend_threshold", 90.0)
    monkeypatch.setattr(settings, "oct_recommend_direction", "above")


@pytest.mark.usefixtures("env_band")
async def test_band_less_step_takes_the_env_band() -> None:
    """energy's ``judge`` authors no threshold — the band comes from the env, and the
    base's band math tags each asset. No watch_margin -> breach/ok only."""
    assets = [_asset("a1", 96.5), _asset("a2", 89.9)]

    outcome = await _executor().execute(_step(), assets, _ctx())

    assert [e["verdict"] for e in outcome.output] == ["breach", "ok"]


@pytest.mark.usefixtures("env_band")
async def test_env_direction_is_honoured(monkeypatch: pytest.MonkeyPatch) -> None:
    """A ``below`` env direction flips the breach edge (the cold-chain / DO shape)."""
    monkeypatch.setattr(settings, "oct_recommend_direction", "below")

    outcome = await _executor().execute(_step(), [_asset("a1", 12.0)], _ctx())

    assert outcome.output[0]["verdict"] == "breach"


@pytest.mark.usefixtures("env_band")
async def test_authored_threshold_delegates_untouched() -> None:
    """An ``in_file`` band wins: the step's own 4.0/below band decides, NOT the env's
    90.0/above — one registered executor can serve a vertical that mixes band sources."""
    step = _step(threshold=4.0, direction="below", watch_margin=1.0)

    outcome = await _executor().execute(step, [_asset("a1", 3.2), _asset("a2", 4.5)], _ctx())

    assert [e["verdict"] for e in outcome.output] == ["breach", "watch"]
    assert outcome.audit is not None
    assert "band_source" not in outcome.audit, "an in_file band must not claim env provenance"


def test_an_env_band_step_cannot_author_a_watch_margin_or_direction() -> None:
    """The invariant that makes an env band necessarily WATCH-LESS: ``Step``'s validator
    refuses ``direction``/``watch_margin`` without a ``threshold`` to band around
    (PLAN-0022 Step 3). So on the executor's binding branch both are always None, and
    the env band can only ever judge breach/ok — energy's declared two-verdict shape."""
    for bandless in ({"watch_margin": 5.0}, {"direction": "below"}):
        with pytest.raises(ValueError, match="require a threshold to band around"):
            _step(**bandless)


@pytest.mark.usefixtures("env_band")
async def test_env_band_collapses_the_watch_band() -> None:
    """No watch_margin counterpart in the environment -> every not-breach reading is ok."""
    outcome = await _executor().execute(_step(), [_asset("a1", 89.9)], _ctx())

    assert outcome.output[0]["verdict"] == "ok"


@pytest.mark.usefixtures("env_band")
async def test_audit_discloses_the_band_provenance_over_the_base_audit() -> None:
    """The run trail records that the numbers came from the environment, not the YAML —
    layered ON TOP of the base executor's own deterministic audit (never replacing it)."""
    outcome = await _executor().execute(_step(), [_asset("a1", 96.5)], _ctx())

    assert outcome.audit is not None
    assert outcome.audit["band_source"] == "env"
    assert outcome.audit["env_var"] == THRESHOLD_ENV_VAR
    assert outcome.audit["direction_env_var"] == DIRECTION_ENV_VAR
    # the base's keys survive
    assert outcome.audit["deterministic"] is True
    assert outcome.audit["threshold"] == 90.0
    assert outcome.audit["direction"] == "above"
    assert outcome.audit["actor_kind"] == "engine"


@pytest.mark.usefixtures("env_band")
async def test_facet_is_never_consulted() -> None:
    """ADR-016 D2-A4: ``facet`` is schema-only — engine-readable, never engine-consumed.
    A step whose facet declares an ``in_file_band`` while authoring NO threshold still
    takes the env band: the typed Step is the only input to the decision."""
    step = _step(
        threshold=None,
        facet={"decision_condition": {"gate_kind": "in_file_band", "band_source": "in_file"}},
    )

    outcome = await _executor().execute(step, [_asset("a1", 96.5)], _ctx())

    assert outcome.output[0]["verdict"] == "breach"
    assert outcome.audit is not None
    assert outcome.audit["band_source"] == "env"
