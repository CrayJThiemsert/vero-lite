"""PLAN-0119 AC-3 — the budget seam exists and is exercised end to end.

CLAUDE.md §8 (binding): a scenario test drives the **real producer into the real
consumer on realistic simulated data**. Here that is:

    the SHIPPED extract_package (services/engine/llm/intake.py)
        -> the REAL OllamaClient, constructed for a workload class
           -- real body assembly, real chokepoint, real retry loop
        -> an httpx transport double that reads what reached THE WIRE

AC-3 says so explicitly: *"A test that stubs ``chat()`` itself does not satisfy
this: it would agree with itself by construction and could not see the wire."* So
nothing between the call site and the request body is replaced — the double sits at
the transport, below everything under test.

🔴 **Why these tests PATCH the budget table, and why the AC is vacuous without it.**
Step 3 ships every class at the same 1024, deliberately — it is a pure refactor, and
the experiment programme changes budgets one arm at a time afterwards. That makes the
obvious assertion worthless: *"the wire carries the class's budget"* is satisfied by a
client that ignores the class completely and hard-codes 1024, because every class's
budget IS 1024 today. Such a test would pass on a seam that does not exist.

So each test below gives two classes DIFFERENT budgets and checks the wire tracks the
one the client was constructed for. That is the only form of the assertion that can
fail if the seam is fake, and it is exactly the counterexample discipline: a test that
would still pass with the behaviour silently broken is not evidence.

What these tests CANNOT claim, stated: anything about a model. The transport is a
double by design; no number here was produced by MS-S1.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from services.engine.llm.client import (
    _WORKLOAD_NUM_PREDICT,
    OllamaAdminClient,
    OllamaClient,
    Workload,
)
from services.engine.llm.intake import IntakeExtractionError, extract_package

_DESCRIPTION = (
    "We run three rice-husk-fired steam boilers. Operators watch the steam drum "
    "pressure and cut the husk feed when it climbs past 8.5 bar."
)


class _WireRecorder:
    """An httpx transport double that keeps every request body it was handed.

    Deliberately the LOWEST possible interception point. Anything higher — a fake
    ``chat``, a patched ``_request_json`` — would be a test of the code above it,
    and AC-3 is a claim about the bytes that leave the process.
    """

    def __init__(self, *, body: str = "{not the package json}") -> None:
        self.requests: list[dict[str, Any]] = []
        self._body = body

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(json.loads(request.content.decode("utf-8")))
        return httpx.Response(
            200,
            json={
                "model": "gpt-oss:20b",
                "message": {"role": "assistant", "content": self._body},
                "done_reason": "stop",
            },
        )

    @property
    def num_predicts(self) -> list[int]:
        """``options.num_predict`` from every request, in order."""
        return [r["options"]["num_predict"] for r in self.requests]


def _client(workload: Workload, recorder: _WireRecorder) -> OllamaClient:
    return OllamaClient(
        workload=workload,
        base_url="http://ollama.test",
        model="gpt-oss:20b",
        transport=httpx.MockTransport(recorder),
    )


async def _drive_the_real_call_site(client: OllamaClient, *, retry_budget: int = 1) -> None:
    """Run the SHIPPED extraction call site against the double.

    The canned body is deliberately unparseable, so the real retry loop runs to
    exhaustion and raises. That outcome is irrelevant to AC-3 — the claim is about
    what reached the wire on the way — and an invalid body keeps this module free of
    a package fixture whose drift could redden a test about ``num_predict``.
    """
    with pytest.raises(IntakeExtractionError):
        await extract_package(client, _DESCRIPTION, retry_budget=retry_budget)


@pytest.mark.asyncio
async def test_the_wire_carries_the_budget_of_the_class_the_client_declared(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The seam's whole claim, made falsifiable.

    Two classes are given distinct budgets, and the SAME shipped call site is driven
    through a client of each. If the chokepoint ignored the class — read a global,
    hard-coded a number, took the first table entry — both runs would report the same
    value and this fails. With every class at its shipped 1024 the same assertion
    could not fail at all, which is why the table is patched.
    """
    monkeypatch.setitem(_WORKLOAD_NUM_PREDICT, "S", 1234)
    monkeypatch.setitem(_WORKLOAD_NUM_PREDICT, "J", 4321)

    structure = _WireRecorder()
    await _drive_the_real_call_site(_client("S", structure))

    judge = _WireRecorder()
    await _drive_the_real_call_site(_client("J", judge))

    assert (structure.num_predicts, judge.num_predicts) == ([1234], [4321]), (
        f"the wire did not track the declared class: S={structure.num_predicts} "
        f"J={judge.num_predicts}"
    )


@pytest.mark.asyncio
async def test_every_attempt_of_the_retry_loop_carries_the_class_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The budget must hold for the whole call site, not just its first attempt.

    The retry loop rebuilds messages between attempts, and a seam that resolved the
    budget once outside the loop — or that a retry path rebuilt from a default —
    would leak the shipped 1024 into attempts 2 and 3 while attempt 1 looked correct.
    Asserting the full list rather than ``[0]`` is what makes that visible.
    """
    monkeypatch.setitem(_WORKLOAD_NUM_PREDICT, "S", 777)
    recorder = _WireRecorder()

    await _drive_the_real_call_site(_client("S", recorder), retry_budget=3)

    assert recorder.num_predicts == [
        777,
        777,
        777,
    ], f"the retry loop did not hold the class budget: {recorder.num_predicts}"


@pytest.mark.asyncio
async def test_the_shipped_default_is_unchanged_by_this_refactor() -> None:
    """Step 3 is a PURE REFACTOR: the number on the wire must not have moved.

    Read WITHOUT patching, unlike every test above, because this is the one claim
    that is about the shipped values themselves. If a later arm raises a class's
    budget this test SHOULD redden — that is the arm being visible, and the arm's own
    pre-committed read is where the new number is ratified (PLAN-0119 Step 5-8).
    """
    recorder = _WireRecorder()

    await _drive_the_real_call_site(_client("S", recorder))

    assert recorder.num_predicts == [1024], (
        f"the shipped cap moved during a refactor that must not move it: "
        f"{recorder.num_predicts}"
    )


def test_the_housekeeping_client_cannot_reach_chat_at_all() -> None:
    """The (c) split's bonus guarantee, and the reason it is a type and not a rule.

    ``admin.py`` builds a client only to ``warm()`` and ``ps()``. Before the split it
    COULD have chatted — nothing stopped it but the absence of a call — and it would
    have had to declare a generation class it has no use for. Asserting the method is
    absent is what keeps the split from silently collapsing back into one class.
    """
    admin = OllamaAdminClient(base_url="http://ollama.test", model="gpt-oss:20b")

    assert not hasattr(admin, "chat"), "the housekeeping client grew a chat method"
    # Positive control: the capability it DOES have, so the assertion above cannot
    # pass merely because the object is broken or empty.
    assert hasattr(admin, "warm"), "the housekeeping client lost warm() — check the split"


def test_the_generating_client_is_still_a_housekeeping_client() -> None:
    """The split must not have cost the generating client its warm/ps/unload.

    ``benchmarks/*`` construct an ``OllamaClient`` and then ``warm()`` it, so the
    subclass relationship is load-bearing rather than cosmetic — this is the guard
    that would catch someone "tidying" the two classes apart.
    """
    client = OllamaClient(workload="S", base_url="http://ollama.test", model="gpt-oss:20b")

    assert isinstance(client, OllamaAdminClient), "the generating client lost its admin base"
    missing = [m for m in ("warm", "unload", "ps", "chat") if not hasattr(client, m)]
    assert not missing, f"the generating client is missing {missing}"


def test_the_class_a_client_was_built_for_is_readable() -> None:
    """The declared class is observable, not swallowed by the constructor.

    Without this the only evidence a client carries its class is the wire, which
    needs a transport; a disclosed clamp (SD-8) and the later arms both need to name
    the class in a trace, and a write-only constructor argument could not serve them.
    """
    assert _client("N", _WireRecorder()).workload == "N"
    assert _client("A", _WireRecorder()).workload == "A"
