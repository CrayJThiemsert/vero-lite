"""PLAN-0100 AC-7 — the global in-flight LLM cap fast-fails to the deterministic arm.

The published demo has one MS-S1 behind it and no queue. D5(3)'s cap exists so a
second visitor gets an honest deterministic answer immediately rather than
waiting behind someone else's generation — a wait is indistinguishable from a
hang at the ninety-second mark, and the demo's whole claim is that it degrades
visibly rather than silently.

Driven end to end: the real ASGI app, the real ``/query`` route, the real
``OllamaClient``, the real degrade path, against a **real local HTTP server**
speaking the Ollama chat contract with controllable latency (the upstream
stand-in — the one thing the AC preamble permits standing in).

Two independent witnesses, deliberately. The app reporting "I took the
deterministic arm" is the thing under test, so the stub also counts how many
requests were ever inside it at once: if the cap works, that number is 1. A test
that trusted only the app's self-report would pass on an app that reported
correctly and capped nothing.
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

import pytest
from httpx import AsyncClient

from services.api.config import settings
from services.api.routers.query import arm_of
from services.engine.llm import client as llm_client
from services.engine.ontology_meta import load_ontology_meta
from tests.support.ollama_stub import ollama_stub


def _translatable() -> str:
    """A stub reply the REAL translate stage accepts.

    Built from the live ontology rather than hardcoded, so the harness follows a
    vertical rename instead of going quietly ungrounded — a stub whose reply fails
    schema validation degrades EVERY request, which would make the capped test
    pass for entirely the wrong reason.
    """
    object_type = load_ontology_meta(settings.oct_vertical).object_types[0].name
    return json.dumps({"object_type": object_type, "operation": "count"})


#: Long enough that the second request provably arrives while the first is still
#: inside the upstream, short enough not to pad the suite.
_UPSTREAM_DELAY_S = 1.0

#: AC-7's pinned bound for the capped request.
_FAST_FAIL_BUDGET_S = 5.0

_QUESTIONS = (
    "which sites are over the temperature threshold right now?",
    "how many assets did we flag today?",
)


#: The engine's whole `outcome` vocabulary (`nl_query.py`). "unknown" is NOT in
#: it — that is the router's fallback when the engine dropped `outcome`, so a row
#: carrying it records that the pipeline lost the state rather than any state.
_OUTCOMES = frozenset({"answered", "no_data", "clarify"})


@pytest.fixture
def _local_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the app at the stand-in and cap it at one slot."""
    monkeypatch.setattr(settings, "llm_backend", "local")
    monkeypatch.setattr(settings, "llm_max_inflight", 1)


@pytest.fixture
def _prompt_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Enable the D6 prompt log into a temp dir — never the configured path.

    AC-7's second half. The cap must be visible in the OPERATOR's record, not
    only in the visitor's response: a degrade that is honest on the wire and
    absent from the log leaves the operator unable to tell a capped demo from a
    quiet one, which is the half D6 exists to provide.
    """
    target = tmp_path / "prompt-log"
    monkeypatch.setattr(settings, "prompt_log_enabled", True)
    monkeypatch.setattr(settings, "prompt_log_dir", str(target))
    return target


def _rows(directory: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted(directory.glob("prompt-*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _arm_of_response(response: dict[str, object]) -> str:
    """The arm the LOG would derive for this response, from the same signal.

    Deliberately routed through the shipped ``arm_of`` rather than reimplemented:
    a second copy of the derivation would agree with itself while disagreeing
    with the writer, which is the defect this assertion is meant to catch.
    """
    phrased_by = response.get("phrased_by")
    return arm_of(phrased_by if isinstance(phrased_by, str) else None)


async def _ask(http: AsyncClient, question: str) -> dict[str, object]:
    response = await http.post("/query", json={"question": question})
    assert response.status_code == 200, response.text
    return dict(response.json())


async def test_the_cap_lets_one_through_and_degrades_the_other(
    client: AsyncClient,
    _local_llm: None,
    _prompt_log: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two concurrent questions, one LLM slot: one is served, one degrades fast."""
    async with ollama_stub(delay=_UPSTREAM_DELAY_S, content=_translatable()) as stub:
        monkeypatch.setattr(settings, "ollama_host", stub.base_url)
        started = time.monotonic()
        first, second = await asyncio.gather(
            _ask(client, _QUESTIONS[0]),
            _ask(client, _QUESTIONS[1]),
        )
        elapsed = time.monotonic() - started

    # The stub's own witness: the cap kept the upstream to one at a time.
    assert (
        stub.max_concurrent == 1
    ), f"the upstream saw {stub.max_concurrent} concurrent calls — the cap did not hold"

    # Exactly one of the two carries a degrade disclosure. Which one is a race by
    # nature (whichever coroutine reaches the client first wins the slot), so the
    # assertion is on the PAIR, never on an ordering the event loop does not promise.
    disclosures = [r.get("phrase_disclosure") for r in (first, second)]
    degraded = [d for d in disclosures if d]
    assert len(degraded) == 1, f"expected exactly one degrade, got {disclosures!r}"
    assert "single LLM slot" in str(degraded[0]), (
        "the disclosure must say WHY it degraded — a generic degrade message would "
        f"leave the visitor unable to tell a cap from an outage: {degraded[0]!r}"
    )

    # Exactly one was AUTHORED by the LLM arm. Asserted through `phrased_by` —
    # the signal the prompt log itself derives `arm` from — and not through
    # `grounded`: grounded means the answer reached real records, which a
    # template-phrased answer over the same records also does. Using it as an arm
    # proxy would stay green if the degrade stopped changing the author at all.
    arms = [_arm_of_response(r) for r in (first, second)]
    assert arms.count("llm") == 1, f"expected exactly one LLM-phrased answer, got {arms}"

    # And exactly one reached the data — a separate claim from the one above,
    # kept because without it the pair would look identical to two failed
    # translations that happened to disclose differently.
    assert [r["grounded"] for r in (first, second)].count(True) == 1

    # Both still answered. The cap degrades; it never fails a request.
    assert first["answer"] and second["answer"]

    # A loose bound, not a bracket: the point is that the capped request did not
    # QUEUE behind the 1s upstream, and a tight assertion here would be the
    # wall-clock shape this repo has already been bitten by. AC-7's text was
    # amended to this bound (Cray, s208) rather than the test tightened to its
    # original "< 5 s on the capped request", which would have required timing a
    # coroutine whose completion order the event loop does not promise.
    assert elapsed < _UPSTREAM_DELAY_S + _FAST_FAIL_BUDGET_S

    # AC-7's second half — the cap is visible in the operator's D6 record too.
    # Recorded AFTER the answer, so `arm` describes what happened rather than
    # what was attempted.
    rows = _rows(_prompt_log)
    assert len(rows) == 2, f"expected one logged row per request, got {len(rows)}"
    assert sorted(str(r["arm"]) for r in rows) == ["deterministic", "llm"], (
        "the log must show exactly one degrade — reading the log is the only way "
        f"an operator can tell the cap fired at all: {[r['arm'] for r in rows]}"
    )
    outcomes = {str(r["outcome"]) for r in rows}
    assert outcomes <= _OUTCOMES, (
        f"outcome outside the engine's vocabulary {sorted(_OUTCOMES)}: {sorted(outcomes)} "
        "— 'unknown' here means the router's fallback fired and the pipeline "
        "dropped the state"
    )

    # The two witnesses tied together by the verbatim question. Asserting the
    # pair on each side separately would stay green if the writer swapped the
    # arms between the two rows, which is precisely a log that lies.
    arm_by_question = {str(r["text"]): str(r["arm"]) for r in rows}
    assert set(arm_by_question) == set(
        _QUESTIONS
    ), f"the log did not record both questions verbatim: {sorted(arm_by_question)}"
    for response, question in ((first, _QUESTIONS[0]), (second, _QUESTIONS[1])):
        assert arm_by_question[question] == _arm_of_response(response), (
            f"the row logged for {question!r} reports arm "
            f"{arm_by_question[question]!r} while its response reports "
            f"{_arm_of_response(response)!r} — the record contradicts the answer"
        )


async def test_without_the_cap_both_reach_the_upstream(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The positive control: same harness, cap off, and the degrade does NOT appear.

    Without this, the test above would pass just as happily against an app that
    degraded every request for some unrelated reason — the absence of a second
    upstream call would prove nothing.
    """
    monkeypatch.setattr(settings, "llm_backend", "local")
    monkeypatch.setattr(settings, "llm_max_inflight", 0)
    async with ollama_stub(delay=_UPSTREAM_DELAY_S, content=_translatable()) as stub:
        monkeypatch.setattr(settings, "ollama_host", stub.base_url)
        await asyncio.gather(_ask(client, _QUESTIONS[0]), _ask(client, _QUESTIONS[1]))

    assert stub.max_concurrent == 2, (
        "with the cap disabled both requests must overlap in the upstream — if they "
        "did not, the harness never produced the concurrency the capped test claims "
        f"to constrain (saw {stub.max_concurrent})"
    )


async def test_the_slot_is_released_after_each_call(
    client: AsyncClient, _local_llm: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A leaked slot would cap the process permanently after one request.

    The failure this guards is silent and cumulative: the demo would answer the
    first question on the LLM arm and every later one deterministically, which
    reads as "the model is cold" rather than as a bug.
    """
    async with ollama_stub(content=_translatable()) as stub:
        monkeypatch.setattr(settings, "ollama_host", stub.base_url)
        for question in _QUESTIONS:
            await _ask(client, question)

    assert llm_client._current_inflight() == 0, "an LLM slot was not released"
    assert (
        len(stub.calls) >= 2
    ), "the second sequential request never reached the upstream — the slot leaked"
