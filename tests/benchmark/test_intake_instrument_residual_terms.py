"""PLAN-0119 Step 2 (AC-2) — the benchmark instrument records what OQ-1 needs.

**The gap this closes.** OQ-1 asks whether the reasoning and content channels share
ONE ``num_predict`` budget or hold separate ones. The reconstruction
``total_duration - eval_duration`` implied ~1,089-1,292 tokens on delivering calls —
above the 1024 cap, which would mean separate budgets — while Ollama's own
post-generation splitter implies one shared budget. The reconstruction cannot settle
it, because that residual silently mixes three unrelated things: a cold model load,
prompt prefill, and grammar compilation. Recording load and prefill SEPARATELY is
what turns one unattributable number into terms that can be subtracted.

``load_duration_ns`` and ``prompt_eval_duration_ns`` were computed by ``CallMetrics``
(``client.py:191-192``) all along and dropped by this recorder. The raw ``thinking``
string is a *different* source — ``CallMetrics`` carries only ``thinking_chars``, an
``int``, and a count cannot say whether reasoning was cut mid-sentence — so it comes
off ``ChatResult.thinking``. Two sources, not one; PLAN-0119's first draft implied
one and was corrected at s274.

**What this module claims:** the instrument now CARRIES those terms, and the two new
runner flags reach the wire.
**What it CANNOT claim, stated:** anything whatever about any model. The transport is
canned here by design, so no number below is a measurement of anything on MS-S1.
OQ-1 closes on a live run, under its own CLAUDE.md §8 go — never here.

Why this is a module of its own rather than a section of
``test_intake_extraction_scenario.py``: a probe battery's coverage denominator is the
whole of each file it names, and the driver FAILS on an uncovered claim
(``passed = complete and not overlaps and ...``). Folding these tests into the
80-claim scenario module would make a clean ``GAPS: 0`` unreachable for this step's
battery. Measured while deciding: the pre-existing
``probe_battery_accounting.json`` already reports ``GAPS: 57`` against that module.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from benchmarks.intake_extraction.harness import load_gold, scored_cases
from benchmarks.intake_extraction.run_benchmark import (
    RecordingChatClient,
    _apply_num_predict,
    case_artifact,
    run_case,
)
from services.api.config import settings
from tests.benchmark.intake_canned import CannedTransport

# --------------------------------------------------------------------------- envelopes

#: A realistic Ollama envelope for a COLD call that hit the cap. The four duration
#: fields are chosen so the residual actually decomposes: 31.4 - 30.1 = 1.3 s of
#: non-decode time, of which 0.9 + 0.3 = 1.2 s is now attributed, leaving 0.1 s
#: unexplained rather than the whole 1.3 s. A fixture whose parts did not sum would
#: let a wrong implementation look right.
_ENVELOPE_COLD: dict[str, Any] = {
    "done_reason": "length",
    "eval_count": 1024,
    "prompt_eval_count": 412,
    "total_duration": 31_400_000_000,
    "eval_duration": 30_100_000_000,
    "load_duration": 900_000_000,
    "prompt_eval_duration": 300_000_000,
}
#: The same shape WARM — load drops ~80x while prefill is unchanged, because the
#: prompt is the same size. That invariance is what makes a collapsed load legible
#: as a collapse rather than as a changed prompt.
_ENVELOPE_WARM: dict[str, Any] = {
    "done_reason": "stop",
    "eval_count": 260,
    "prompt_eval_count": 412,
    "total_duration": 8_200_000_000,
    "eval_duration": 7_400_000_000,
    "load_duration": 11_000_000,
    "prompt_eval_duration": 300_000_000,
}


@pytest.fixture
def boiler_case() -> dict[str, Any]:
    """`bo-01` — a REAL gold case, not a fixture invented for this test."""
    for case in scored_cases(load_gold()):
        if case["id"] == "bo-01":
            return case
    raise AssertionError("gold.yaml no longer carries bo-01; update this module")


# --------------------------------------------------------------- the recorded terms


@pytest.mark.asyncio
async def test_the_recorder_captures_the_terms_that_decompose_the_residual() -> None:
    """Both new duration terms reach the record, and the subtraction they enable works.

    The arithmetic is asserted separately from the two fields because a recorder can
    carry all four durations and still make the residual meaningless — a mis-wired
    envelope key populates a plausible nanosecond count in the wrong slot, which no
    field-presence check can see.
    """
    client = RecordingChatClient(CannedTransport([""], envelopes=[_ENVELOPE_COLD]))

    await client.chat([{"role": "user", "content": "x"}])

    attempt = client.attempts[0]
    assert attempt.load_duration_ns == 900_000_000, "cold load must be its own term"
    assert attempt.prompt_eval_duration_ns == 300_000_000, "prefill must be its own term"

    residual = attempt.total_duration_ns - attempt.eval_duration_ns
    unattributed = residual - attempt.load_duration_ns - attempt.prompt_eval_duration_ns
    assert (residual, unattributed) == (1_300_000_000, 100_000_000), (
        f"the residual no longer decomposes: residual={residual} "
        f"load={attempt.load_duration_ns} prefill={attempt.prompt_eval_duration_ns} "
        f"unattributed={unattributed}"
    )


@pytest.mark.asyncio
async def test_a_cold_load_is_distinguishable_from_a_warm_one() -> None:
    """The discrimination ``load_duration_ns`` exists to make.

    A cold load can BE the reported tail on a small run, and before this nothing on
    disk would say so — the time landed in the same residual as prefill. Asserting
    the loads differ ~80x while prefill is IDENTICAL is what shows the recorder reads
    two distinct fields rather than one field twice.
    """
    client = RecordingChatClient(
        CannedTransport(["", ""], envelopes=[_ENVELOPE_COLD, _ENVELOPE_WARM])
    )

    await client.chat([{"role": "user", "content": "x"}])
    await client.chat([{"role": "user", "content": "x"}])

    loads = [a.load_duration_ns for a in client.attempts]
    prefills = [a.prompt_eval_duration_ns for a in client.attempts]
    assert (loads, prefills) == (
        [900_000_000, 11_000_000],
        [300_000_000, 300_000_000],
    ), f"loads={loads} prefills={prefills}"


@pytest.mark.asyncio
async def test_the_raw_thinking_string_is_recorded_not_only_its_length() -> None:
    """``thinking_chars`` is an int, and an int cannot show a cut mid-sentence.

    The count must survive BESIDE the string rather than be replaced by it — the two
    come from different records (``CallMetrics`` vs ``ChatResult``), and asserting
    both is what keeps that split from silently collapsing to one source.
    """
    reasoning = "the boiler threshold is 8.5 bar and the recovery value is"
    client = RecordingChatClient(
        CannedTransport([""], envelopes=[_ENVELOPE_COLD], thinkings=[reasoning])
    )

    await client.chat([{"role": "user", "content": "x"}])

    attempt = client.attempts[0]
    assert attempt.thinking == reasoning, "the raw reasoning text must survive"
    assert attempt.thinking_chars == len(reasoning), "the count must survive beside it"


@pytest.mark.asyncio
async def test_a_transport_failure_fabricates_no_residual_terms() -> None:
    """There is no envelope when the call never returned, so every new term stays
    ``None``. A zero here would be a measurement that never happened wearing the
    shape of one that did — and a zero load is a perfectly plausible WARM reading,
    which is exactly why it must not be invented."""
    client = RecordingChatClient(CannedTransport([""], raises=RuntimeError("box is down")))

    with pytest.raises(RuntimeError):
        await client.chat([{"role": "user", "content": "x"}])

    attempt = client.attempts[0]
    assert (attempt.load_duration_ns, attempt.prompt_eval_duration_ns, attempt.thinking) == (
        None,
        None,
        None,
    ), f"fabricated accounting on a failed call: {attempt}"


@pytest.mark.asyncio
async def test_an_envelope_without_the_new_counters_degrades_rather_than_raising() -> None:
    """Ollama versions differ in what they put in the envelope. An absent counter must
    read as absent, never crash a run over a field nothing scores — the older-server
    path is the one a live arm is most likely to meet unannounced."""
    client = RecordingChatClient(CannedTransport([""], envelopes=[{"done_reason": "stop"}]))

    await client.chat([{"role": "user", "content": "x"}])

    attempt = client.attempts[0]
    assert (attempt.done_reason, attempt.load_duration_ns, attempt.prompt_eval_duration_ns) == (
        "stop",
        None,
        None,
    ), f"absent counters did not degrade cleanly: {attempt}"


@pytest.mark.asyncio
async def test_the_artifact_carries_the_residual_terms_for_every_attempt(
    boiler_case: dict[str, Any],
) -> None:
    """The point is re-adjudication without a re-run, so the terms must reach the
    per-case file. An in-memory field nothing serialises answers OQ-1 for nobody.

    Both canned bodies are invalid on purpose: the case then exhausts validation and
    ``run_case`` records a ``CaseFailure``, which is the path that most needs its
    accounting kept — a failed case with no numbers cannot be re-read later.
    """
    client = RecordingChatClient(
        CannedTransport(
            ["{not json", "{still not json"],
            envelopes=[_ENVELOPE_COLD, _ENVELOPE_WARM],
            thinkings=["cut off here", None],
        )
    )

    outcome = await run_case(boiler_case, client, retry_budget=2)
    record = case_artifact(boiler_case, outcome)

    assert [a["load_duration_ns"] for a in record["attempts"]] == [900_000_000, 11_000_000]
    assert [a["prompt_eval_duration_ns"] for a in record["attempts"]] == [300_000_000, 300_000_000]
    assert [a["thinking"] for a in record["attempts"]] == ["cut off here", None]
    # `thinking` is the first free-text field in this record, so a dump check is not
    # idle: a value that cannot be serialised would fail at write time on a live run.
    assert json.loads(json.dumps(record))["attempts"][0]["thinking"] == "cut off here"


# ------------------------------------------------------------------ the runner flags


@pytest.mark.asyncio
async def test_the_think_override_reaches_the_wire_where_the_call_site_passed_nothing(
    boiler_case: dict[str, Any],
) -> None:
    """``--think`` must change what the MODEL is asked, not just what argparse parsed.

    Intake's shipped call passes no ``think`` at all, so without this lever the effort
    arm could only be run by editing the shipped prompt path — which would change the
    demand and confound the arm. Asserted on the transport's record of what ARRIVED,
    because the wire is the only place the claim is true or false.
    """
    transport = CannedTransport(["{not json"])
    client = RecordingChatClient(transport, think_override="low")

    await run_case(boiler_case, client, retry_budget=1)

    assert transport.thinks == [
        "low"
    ], f"the override did not reach the wire: transport saw {transport.thinks}"


@pytest.mark.asyncio
async def test_the_override_never_overrules_a_call_site_that_chose() -> None:
    """The negative half, and the one that makes the override safe to ship.

    Without it ``--think`` would silently rewrite a call site's own decision and a
    later arm would measure something other than what it declared. Its positive
    control is the test above: that override DOES reach the wire when the call site is
    silent, so this ``True`` is the call site winning rather than the lever being inert.
    """
    transport = CannedTransport([""])
    client = RecordingChatClient(transport, think_override="low")

    await client.chat([{"role": "user", "content": "x"}], think=True)

    assert transport.thinks == [
        True
    ], f"the override overruled an explicit call site: transport saw {transport.thinks}"


def test_think_false_is_refused_rather_than_quietly_supported() -> None:
    """``think: false`` disables the thinking PARSER, not the generation (Ollama
    #18044) — ``eval_count`` is unchanged — and pairing it with intake's
    ``response_format`` is exactly what the CHECKPOINT-0 contract (ADR-001) forbids.
    Accepting it would produce an arm that looks like an intervention, reads as a null
    result, and tested nothing.

    Every spelling is checked in ONE assertion rather than by parametrising: a
    parametrised node fails as five testcases at once, which a probe battery
    classifies MISFIRE ("more than one test failed") and cannot attribute.
    """
    refused = ["false", "False", "0", "no", "  FALSE  "]
    outcomes = []
    for value in refused:
        try:
            RecordingChatClient(CannedTransport([""]), think_override=value)
            outcomes.append((value, "ACCEPTED"))
        except ValueError as exc:
            outcomes.append((value, "not a lever" in str(exc)))
    assert outcomes == [(value, True) for value in refused], f"measured {outcomes}"


def test_num_predict_override_moves_what_the_chokepoint_actually_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``--num-predict`` has no seam to pass through until Step 3, so it moves the
    setting ``OllamaClient.chat`` reads at the chokepoint (``client.py:335``).

    Asserted against ``settings.llm_max_output_tokens`` itself rather than a literal,
    because that attribute IS what the client consults — a test against a constant
    would keep passing if the client were later repointed elsewhere. The default path
    is checked first and matters more: a run WITHOUT the flag must leave the shipped
    cap alone, or every baseline silently measures a different cap than production and
    the PLAN-0118 comparison Step 10 rests on is void.
    """
    monkeypatch.setattr(settings, "llm_max_output_tokens", 1024)

    unchanged = _apply_num_predict(None)
    assert (unchanged, settings.llm_max_output_tokens) == (1024, 1024), "None must not move it"

    applied = _apply_num_predict(4096)
    assert (applied, settings.llm_max_output_tokens) == (
        4096,
        4096,
    ), f"the chokepoint still reads {settings.llm_max_output_tokens}, not 4096"
