"""AC-3 scenario test — the real producer flows into the real consumer, offline.

CLAUDE.md §8 (binding): every build ships a scenario test that drives the **real
producer into the real consumer on realistic simulated data**. Here that is:

    gold.yaml (a REAL case)
        -> the SHIPPED extract_package (services/engine/llm/intake.py:155)
           -- real prompt assembly, real retry loop, real validation, real
              `source` stamping
        -> the REAL score_case (benchmarks/intake_extraction/harness.py)

**Where the canned transport sits, and why that is not stubbing the seam under
test.** The seam under test is the benchmark plumbing: gold -> extraction ->
scorer. The canned transport is attached at the *designed* ``ChatClient``
Protocol seam (``intake.py:39-50``), which exists precisely so extraction can be
driven offline — it is the transport **beyond** the plumbing, not one side of it.
Nothing between the gold case and the scored outcome is replaced.

**What this module claims:** the instrument is live end to end.
**What it CANNOT claim, stated:** anything whatever about any model. The
transport is canned here *by design*; model claims close only under AC-6's live
run. A pass here is evidence about the plumbing and nothing else.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from benchmarks.intake_extraction.harness import (
    CaseFailure,
    load_gold,
    score_case,
    scored_cases,
)
from benchmarks.intake_extraction.run_benchmark import (
    RecordingChatClient,
    case_artifact,
    confidence_was_omitted,
    run_benchmark,
    run_case,
)
from services.engine.llm.client import ChatResult, OllamaUnreachableError

# --------------------------------------------------------------------------- canned transport


class CannedTransport:
    """A ``ChatClient`` that replays pre-set message bodies instead of calling a box.

    Attached at ``intake.py``'s own injection seam. When the scripted contents run
    out it repeats the last one, so a single valid body can serve a whole-gold-set
    run without the script having to enumerate every case.
    """

    def __init__(
        self,
        contents: list[str],
        *,
        model: str = "canned-model",
        raises: Exception | None = None,
        envelopes: list[dict[str, Any]] | None = None,
        thinkings: list[str | None] | None = None,
    ) -> None:
        self._contents = contents
        self._model = model
        self._raises = raises
        # `envelopes` is the Ollama response envelope `ChatResult.raw` carries — the
        # generation accounting (`done_reason`, `eval_count`, the ns durations) the
        # recorder reads via `call_metrics`. Default `{}` keeps every pre-existing
        # test on the optional-tolerant path, which is itself the behaviour a live
        # server with an older envelope would produce.
        self._envelopes = envelopes
        self._thinkings = thinkings
        self.calls = 0

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        think: bool | str | None = None,
        response_format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> ChatResult:
        self.calls += 1
        if self._raises is not None:
            raise self._raises
        index = min(self.calls - 1, len(self._contents) - 1)

        def _pick(seq: list[Any] | None, default: Any) -> Any:
            if seq is None:
                return default
            return seq[min(self.calls - 1, len(seq) - 1)]

        return ChatResult(
            content=self._contents[index],
            thinking=_pick(self._thinkings, None),
            model=self._model,
            raw=_pick(self._envelopes, {}),
        )


# --------------------------------------------------------------------------- fixtures


def _package_json(
    *, direction: str, threshold: float, recovery: float, confidence: float | None = 0.9
) -> str:
    """A schema-valid IntakePackage body, band-compliant, for the boiler case.

    Band-compliant on purpose (asset 2-5 properties, site 1-3, action_types 2-4)
    so ``band_compliance`` is a clean ``correct`` in the baseline and any change
    to it is attributable to the mutation under test rather than to the fixture.
    """
    package: dict[str, Any] = {
        "namespace": "biomass_boiler",
        "domain_label": "Rice-husk-fired steam boilers supplying process steam",
        "asset_role": {
            "type_name": "Boiler",
            "properties": [
                {"name": "fuel_type", "type": "string", "values": [], "required": False},
                {"name": "rated_pressure_bar", "type": "float", "values": [], "required": False},
            ],
        },
        "site_role": {
            "type_name": "BoilerHouse",
            "properties": [
                {"name": "bay_count", "type": "int", "values": [], "required": False},
            ],
        },
        "metric": {
            "label": "steam drum pressure",
            "unit": "bar",
            "threshold": threshold,
            "direction": direction,
        },
        "action_types": ["cut_husk_feed", "vent_to_atmosphere"],
        "recovery_value": recovery,
    }
    if confidence is not None:
        package["confidence"] = confidence
    return json.dumps(package)


@pytest.fixture
def gold() -> dict[str, Any]:
    return load_gold()


@pytest.fixture
def boiler_case(gold: dict[str, Any]) -> dict[str, Any]:
    """`bo-01` — a REAL gold case, not a fixture invented for this test."""
    for case in scored_cases(gold):
        if case["id"] == "bo-01":
            return case
    raise AssertionError("gold.yaml no longer carries bo-01; update this scenario test")


def _matching_body(case: dict[str, Any]) -> str:
    expected = case["expected"]
    return _package_json(
        direction=expected["metric_direction"],
        threshold=float(expected["metric_threshold"]),
        recovery=float(expected["recovery_value"]),
    )


# --------------------------------------------------------------------------- AC-3


@pytest.mark.asyncio
async def test_gold_flows_through_the_shipped_seam_into_the_real_scorer(
    boiler_case: dict[str, Any],
) -> None:
    """The end-to-end pass read, fixed before the run: a canned package that matches
    gold scores ``correct`` on the direction axis, and the diagnostics carry the
    attempt count produced by the REAL retry loop."""
    client = RecordingChatClient(CannedTransport([_matching_body(boiler_case)]))

    outcome = await run_case(boiler_case, client)
    scored = score_case(boiler_case, outcome.result, confidence_omitted=outcome.confidence_omitted)

    assert scored.axes["metric_direction"] == "correct"
    assert scored.axes["metric_threshold"] == "correct"
    assert scored.axes["recovery_value"] == "correct"
    assert scored.attempts == 1


@pytest.mark.asyncio
async def test_the_shipped_source_stamp_survives_the_round_trip(
    boiler_case: dict[str, Any],
) -> None:
    """`source` is stamped by the real ``extract_package`` (intake.py:186), not by the
    canned body — which is exactly why the scorer refuses to score it."""
    client = RecordingChatClient(CannedTransport([_matching_body(boiler_case)]))

    outcome = await run_case(boiler_case, client)

    assert not isinstance(outcome.result, CaseFailure)
    assert outcome.result.package.source == "ms_s1_live"


@pytest.mark.asyncio
async def test_flipping_the_canned_direction_flips_the_scored_outcome(
    boiler_case: dict[str, Any],
) -> None:
    """The mutation reaches the code and names the output it changes: with every
    other field untouched, inverting only ``direction`` moves that one axis to
    ``wrong`` while the numeric axes stay ``correct``."""
    expected = boiler_case["expected"]
    flipped = "below" if expected["metric_direction"] == "above" else "above"
    body = _package_json(
        direction=flipped,
        threshold=float(expected["metric_threshold"]),
        recovery=float(expected["recovery_value"]),
    )
    client = RecordingChatClient(CannedTransport([body]))

    outcome = await run_case(boiler_case, client)
    scored = score_case(boiler_case, outcome.result)

    assert scored.axes["metric_direction"] == "wrong"
    assert scored.axes["metric_threshold"] == "correct"
    assert scored.axes["recovery_value"] == "correct"


@pytest.mark.asyncio
async def test_the_real_validation_retry_loop_is_driven(boiler_case: dict[str, Any]) -> None:
    """Invalid-then-valid must cost TWO attempts. This reddens if the runner ever
    stops driving ``extract_package``'s own retry loop and starts calling the
    transport once itself."""
    client = RecordingChatClient(
        CannedTransport(["{not valid json at all", _matching_body(boiler_case)])
    )

    outcome = await run_case(boiler_case, client)
    scored = score_case(boiler_case, outcome.result)

    assert scored.attempts == 2
    assert scored.axes["metric_direction"] == "correct"
    assert len(outcome.attempts) == 2


# --------------------------------------------------------------------------- AC-4


@pytest.mark.asyncio
async def test_transport_error_and_validation_exhaustion_stay_distinct(
    boiler_case: dict[str, Any],
) -> None:
    """🔴 The SD-5 correctness constraint. The two failures must not collapse: one
    scores ``wrong`` and stays in the denominator, the other scores ``unscored`` and
    leaves it. A single broad ``except RuntimeError`` in the runner would merge them
    (both derive from it) and this assertion is what catches that."""
    transport_client = RecordingChatClient(
        CannedTransport([], raises=OllamaUnreachableError("box is down"))
    )
    transport_outcome = await run_case(boiler_case, transport_client)

    exhausted_client = RecordingChatClient(CannedTransport(["{still not json"]))
    exhausted_outcome = await run_case(boiler_case, exhausted_client)

    assert isinstance(transport_outcome.result, CaseFailure)
    assert transport_outcome.result.kind == "transport_error"
    assert isinstance(exhausted_outcome.result, CaseFailure)
    assert exhausted_outcome.result.kind == "validation_exhausted"

    transport_scored = score_case(boiler_case, transport_outcome.result)
    exhausted_scored = score_case(boiler_case, exhausted_outcome.result)
    assert transport_scored.axes["metric_direction"] == "unscored"
    assert exhausted_scored.axes["metric_direction"] == "wrong"


@pytest.mark.asyncio
async def test_the_artifact_carries_every_raw_attempt(boiler_case: dict[str, Any]) -> None:
    """Artifact completeness — the property that makes a scoring dispute
    re-adjudicable without a re-run. Reddens if the raw-attempt capture is cut."""
    client = RecordingChatClient(CannedTransport(["{not json", _matching_body(boiler_case)]))

    outcome = await run_case(boiler_case, client)
    scored = score_case(boiler_case, outcome.result)
    record = case_artifact(boiler_case, outcome, scored=scored)

    assert record["attempt_count"] == 2
    assert len(record["attempts"]) == 2
    assert record["attempts"][0]["content"] == "{not json"
    assert record["attempts"][1]["content"] is not None
    assert record["package"] is not None
    assert record["description"] == boiler_case["description"]


@pytest.mark.asyncio
async def test_the_transport_failure_artifact_records_the_error_not_a_body(
    boiler_case: dict[str, Any],
) -> None:
    """A transport failure has no body to record, so the attempt carries ``error``
    and a null ``content`` — the artifact distinguishes 'the model emitted this and
    it was rejected' from 'there was no answer at all'."""
    client = RecordingChatClient(CannedTransport([], raises=OllamaUnreachableError("box is down")))

    outcome = await run_case(boiler_case, client)
    record = case_artifact(boiler_case, outcome)

    assert record["package"] is None
    assert record["failure"]["kind"] == "transport_error"
    assert record["attempts"][0]["content"] is None
    assert "OllamaUnreachableError" in record["attempts"][0]["error"]


def test_confidence_omission_is_read_from_the_raw_attempt_only() -> None:
    """The diagnostic exists only because the raw body is kept: once a package is
    built, ``default=1.0`` makes an omitting model indistinguishable from a
    confident one. Absence of parseable JSON reports ``None``, never ``True`` —
    absence of evidence is not evidence of omission."""
    from benchmarks.intake_extraction.run_benchmark import AttemptRecord

    with_conf = AttemptRecord(
        index=1,
        content=_package_json(direction="above", threshold=1.0, recovery=2.0, confidence=0.4),
        model="m",
    )
    without_conf = AttemptRecord(
        index=1,
        content=_package_json(direction="above", threshold=1.0, recovery=2.0, confidence=None),
        model="m",
    )
    unparseable = AttemptRecord(index=1, content="{not json", model="m")

    assert confidence_was_omitted([with_conf]) is False
    assert confidence_was_omitted([without_conf]) is True
    assert confidence_was_omitted([unparseable]) is None
    assert confidence_was_omitted([]) is None


@pytest.mark.asyncio
async def test_the_runner_produces_the_live_shape_offline(gold: dict[str, Any]) -> None:
    """AC-4's offline verification: with a canned transport the runner produces the
    same artifact shape and the same summary the live run will — one artifact per
    case across BOTH bands, and every scored axis summarised."""
    expected_first = scored_cases(gold)[0]["expected"]
    body = _package_json(
        direction=expected_first["metric_direction"],
        threshold=float(expected_first["metric_threshold"]),
        recovery=float(expected_first["recovery_value"]),
    )
    client = RecordingChatClient(CannedTransport([body]))

    run = await run_benchmark(gold, client)

    n_cases = len(gold["cases"])
    assert len(run.artifacts) == n_cases
    assert {a["case_id"] for a in run.artifacts} == {str(c["id"]) for c in gold["cases"]}
    assert [s.axis for s in run.summaries] == [
        "metric_direction",
        "metric_threshold",
        "recovery_value",
        "band_compliance",
    ]
    assert run.injection is not None
    # inj-03 declares counts_in_fraction: false and must never enter the fraction.
    assert "inj-03" in run.injection_excluded


@pytest.mark.asyncio
async def test_every_summary_keeps_both_excluded_counts_visible(gold: dict[str, Any]) -> None:
    """A number that left the denominator has to stay visible or the denominator
    lies — so every axis reports both exclusion counts, on every run."""
    client = RecordingChatClient(CannedTransport([], raises=OllamaUnreachableError("box is down")))

    run = await run_benchmark(gold, client)

    n_scored = len(scored_cases(gold))
    for summary in run.summaries:
        assert summary.unscored_transport == n_scored
        assert summary.wrong_validation_exhausted == 0
        assert summary.overall.total == 0


# ------------------------------------------- generation accounting (s273 follow-on)
#
# These exist because the s273 live run could not explain its own headline result:
# 11 of 20 attempts returned an EMPTY body and nothing on disk could separate "the
# model ran into the num_predict cap while reasoning" from "the model chose to emit
# nothing". `ChatResult.raw` carried the answer the whole time and the recorder
# dropped it. Every assertion below is about a field that discriminates those two.

#: A realistic Ollama envelope for a call that hit the cap: `done_reason == "length"`,
#: a large `eval_count` (the model generated plenty) beside an EMPTY body.
_ENVELOPE_TRUNCATED: dict[str, Any] = {
    "done_reason": "length",
    "eval_count": 1024,
    "prompt_eval_count": 412,
    "total_duration": 31_400_000_000,
    "eval_duration": 30_100_000_000,
}
#: The contrasting envelope: the model ended on its own, having generated little.
_ENVELOPE_STOP: dict[str, Any] = {
    "done_reason": "stop",
    "eval_count": 260,
    "prompt_eval_count": 412,
    "total_duration": 8_200_000_000,
    "eval_duration": 7_400_000_000,
}


@pytest.mark.asyncio
async def test_the_recorder_captures_the_generation_accounting(
    boiler_case: dict[str, Any],
) -> None:
    """Every counter the envelope carries reaches the attempt record."""
    client = RecordingChatClient(
        CannedTransport([_matching_body(boiler_case)], envelopes=[_ENVELOPE_STOP])
    )

    await run_case(boiler_case, client)

    attempt = client.attempts[0]
    assert attempt.done_reason == "stop"
    assert attempt.eval_count == 260
    assert attempt.prompt_eval_count == 412
    assert attempt.total_duration_ns == 8_200_000_000
    assert attempt.eval_duration_ns == 7_400_000_000


@pytest.mark.asyncio
async def test_an_empty_body_at_the_cap_is_distinguishable_from_a_deliberate_stop() -> None:
    """THE discriminator the s273 run lacked.

    Both attempts below deliver an empty body — indistinguishable in the s273
    artifacts. Under the envelope they are not the same event at all: one generated
    1024 tokens and was cut, the other generated 260 and stopped itself.
    """
    client = RecordingChatClient(
        CannedTransport(
            ["", ""],
            envelopes=[_ENVELOPE_TRUNCATED, _ENVELOPE_STOP],
        )
    )

    await client.chat([{"role": "user", "content": "x"}])
    await client.chat([{"role": "user", "content": "x"}])

    cut, stopped = client.attempts
    assert cut.content == stopped.content == ""
    assert cut.truncated is True
    assert stopped.truncated is False
    assert cut.eval_count == 1024
    assert stopped.eval_count == 260


@pytest.mark.asyncio
async def test_thinking_chars_records_how_much_of_the_generation_was_reasoning() -> None:
    """`gpt-oss:20b` reasons unconditionally (s261), and reasoning shares the one
    `num_predict` budget on this single-call path — so the reasoning size is the
    quantity the cap hypothesis is about."""
    client = RecordingChatClient(
        CannedTransport([""], envelopes=[_ENVELOPE_TRUNCATED], thinkings=["r" * 3105])
    )

    await client.chat([{"role": "user", "content": "x"}])

    assert client.attempts[0].thinking_chars == 3105


@pytest.mark.asyncio
async def test_a_transport_failure_records_no_accounting() -> None:
    """There is no envelope when the call never returned — every counter stays
    None. A zero here would be a measurement that never happened wearing the shape
    of one that did."""
    client = RecordingChatClient(CannedTransport([], raises=OllamaUnreachableError("box is down")))

    with pytest.raises(OllamaUnreachableError):
        await client.chat([{"role": "user", "content": "x"}])

    attempt = client.attempts[0]
    assert attempt.error is not None
    assert attempt.done_reason is None
    assert attempt.eval_count is None
    assert attempt.total_duration_ns is None
    assert attempt.truncated is False


@pytest.mark.asyncio
async def test_an_envelope_without_counters_degrades_to_none_rather_than_raising() -> None:
    """Ollama versions differ in what they put in the envelope. A missing counter
    must read as absent, never crash a run over a field nothing scores."""
    client = RecordingChatClient(CannedTransport([""], envelopes=[{}]))

    await client.chat([{"role": "user", "content": "x"}])

    attempt = client.attempts[0]
    assert attempt.done_reason is None
    assert attempt.eval_count is None
    assert attempt.total_duration_ns is None


@pytest.mark.asyncio
async def test_the_artifact_carries_the_accounting_for_every_attempt(
    boiler_case: dict[str, Any],
) -> None:
    """The whole point is re-adjudication without a re-run, so the counters have to
    survive into the per-case file — not just live on the in-memory record."""
    client = RecordingChatClient(
        CannedTransport(
            ["{not json", _matching_body(boiler_case)],
            envelopes=[_ENVELOPE_TRUNCATED, _ENVELOPE_STOP],
        )
    )

    outcome = await run_case(boiler_case, client)
    record = case_artifact(boiler_case, outcome)

    assert [a["done_reason"] for a in record["attempts"]] == ["length", "stop"]
    assert [a["truncated"] for a in record["attempts"]] == [True, False]
    assert [a["eval_count"] for a in record["attempts"]] == [1024, 260]
    assert [a["total_duration_ns"] for a in record["attempts"]] == [
        31_400_000_000,
        8_200_000_000,
    ]
    # `content_chars` beside `eval_count` is what makes an empty body legible:
    # plenty generated, none of it content.
    assert record["attempts"][0]["content_chars"] == len("{not json")
