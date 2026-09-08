"""PLAN-0119 Step 3 part 2 — the capacity clamp and ``num_ctx``, read off the wire.

Its own module (battery denominators; see ``test_capacity.py``'s header).

``test_capacity.py`` proves the ARITHMETIC in isolation. This module proves the
WIRING: that the chokepoint actually consults the rule and that what it decided
reaches the request body. Both are needed and neither substitutes for the other —
a correct rule that nothing calls is worth nothing, and a called rule that
computes the wrong number is worse.

Like AC-3's seam test, the double sits at the TRANSPORT, the lowest possible
interception point. Anything higher — a fake ``chat``, a patched
``_request_json`` — would test the code above it, and these are claims about the
bytes that leave the process.

⚠️ **No assertion here is a conjunction.** ``assert x is not None and x.y == z``
is two claims wearing one assert: a mutation reddens it without saying which half
failed, and the probe driver cannot attribute the result to a claim. Every
"is not None" precondition is therefore funnelled through :func:`_budget_of`,
where it is ONE claim that can be exempted with a reason, rather than repeated in
a dozen asserts that each become an unprobeable half.

What these tests CANNOT claim, stated plainly: anything about a model or a real
server. The transport is a double; no number here was produced by MS-S1. They
test that the client sends what the rule says, not that the rule's provisional
terms are right — those are provisional precisely because nobody has measured
them.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from services.engine.llm.capacity import (
    UnlistedModelError,
    capacity_for,
    estimate_prompt_tokens,
)
from services.engine.llm.client import (
    _WORKLOAD_NUM_PREDICT,
    AppliedBudget,
    ChatResult,
    OllamaClient,
)

_SHIPPED_MODEL = "gpt-oss:20b"


class _WireRecorder:
    """A transport double that keeps every request body it was handed."""

    def __init__(self) -> None:
        self.bodies: list[dict[str, Any]] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.bodies.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "model": _SHIPPED_MODEL,
                "message": {"role": "assistant", "content": "ok"},
                "done": True,
                "done_reason": "stop",
            },
        )

    @property
    def options(self) -> dict[str, Any]:
        """The ``options`` block of the single request recorded.

        The length check is a PRECONDITION of every wire assertion in this
        module, not a claim about the clamp: it records that exactly one request
        was observed, which is the condition under which "the wire carries X"
        means anything at all.
        """
        assert len(self.bodies) == 1, f"expected exactly one call, got {len(self.bodies)}"
        options = self.bodies[0]["options"]
        return dict(options)


def _budget_of(result: ChatResult) -> AppliedBudget:
    """The budget record the chokepoint attached, or fail loudly.

    A PRECONDITION funnel, deliberately. Without it every test below would carry
    its own ``result.budget is not None`` — either as a conjunction (unprobeable)
    or as a separate claim repeated a dozen times (a denominator full of noise
    that says nothing about the clamp). Here it is one claim, and a mutation that
    stopped the chokepoint attaching a record reddens every test at once, which
    is the honest signal for a failure of that size.
    """
    assert result.budget is not None, "the chokepoint must attach a budget record"
    return result.budget


def _client(recorder: _WireRecorder, *, timeout: float = 120.0) -> OllamaClient:
    return OllamaClient(
        workload="S",
        base_url="http://ollama.test",
        model=_SHIPPED_MODEL,
        timeout=timeout,
        transport=httpx.MockTransport(recorder),
    )


def _short_message() -> list[dict[str, str]]:
    return [{"role": "user", "content": "summarise this boiler reading"}]


def _long_message() -> list[dict[str, str]]:
    """A prompt long enough that prompt + the shipped 1024 cap breaches 4096.

    ~12,650 characters at the measured 2.71 chars/token is ~4,668 tokens, so
    4,668 + 1,024 = 5,692 against an assumed 4,096 window.
    """
    return [{"role": "user", "content": "boiler telemetry line. " * 550}]


# --------------------------------------------------------------------------
# The clamp
# --------------------------------------------------------------------------


async def test_the_shipped_configuration_does_not_clamp() -> None:
    """🔴 The regression floor for this whole change.

    Today's shipped cap on today's shipped model against today's timeout must
    reach the wire untouched. If this reddens, the seam has made the CURRENT
    behaviour unservable — a defect in the seam, not a discovery about budgets.
    It is also the positive control for the clamp test below: without it, a
    clamp stuck permanently on would look correct there.
    """
    recorder = _WireRecorder()
    result = await _client(recorder).chat(_short_message())

    assert recorder.options["num_predict"] == _WORKLOAD_NUM_PREDICT["S"], (
        f"the shipped cap must reach the wire unchanged; "
        f"wire={recorder.options['num_predict']} expected={_WORKLOAD_NUM_PREDICT['S']}"
    )
    assert not _budget_of(
        result
    ).clamped, f"the shipped configuration must not clamp; budget={_budget_of(result)}"


async def test_a_timeout_too_short_for_the_class_clamps_the_cap_on_the_wire() -> None:
    """The clamp fires, and what it computed is what is sent.

    A 20 s timeout cannot serve 1024 tokens on this model: 1024 / 48.3 = 21.2 s
    of decode plus a 5.5 s load term. The largest cap that still fits strictly
    inside 20 s is 700 — ``ceil((20.0 - 5.5) * 48.3) - 1``.
    """
    recorder = _WireRecorder()
    budget = _budget_of(await _client(recorder, timeout=20.0).chat(_short_message()))

    assert recorder.options["num_predict"] == budget.applied_num_predict, (
        f"the wire must carry what the clamp decided; "
        f"wire={recorder.options['num_predict']} decided={budget.applied_num_predict}"
    )
    assert budget.applied_num_predict == 700, (
        f"expected the exact largest fitting cap 700, got "
        f"{budget.applied_num_predict} (requested {budget.requested_num_predict})"
    )


async def test_the_clamp_never_hands_a_class_more_than_it_asked_for() -> None:
    """A generous timeout must not inflate a budget somebody chose on purpose.

    The clamp is a bound, not a negotiation: with an hour of headroom the model
    could decode far more than 1024 tokens, and the wire must still carry 1024.
    """
    recorder = _WireRecorder()
    await _client(recorder, timeout=3600.0).chat(_short_message())

    assert recorder.options["num_predict"] == _WORKLOAD_NUM_PREDICT["S"], (
        f"a generous timeout must not raise the cap; " f"wire={recorder.options['num_predict']}"
    )


async def test_a_clamp_that_fires_is_disclosed_with_the_numbers_it_used() -> None:
    """SD-8 = (b). A silent clamp is the failure this disclosure exists to prevent.

    The reason string must carry the arithmetic, not just the fact — a reviewer
    who sees a short judgment needs to be able to tell that its author was given
    less room than its class asks for, and why.
    """
    recorder = _WireRecorder()
    budget = _budget_of(await _client(recorder, timeout=20.0).chat(_short_message()))

    reason = budget.reason or ""
    missing = [token for token in ("1024", "700", "20.0", "clamped") if token not in reason]
    assert not missing, f"the disclosure omitted {missing}; reason was: {reason!r}"


async def test_a_clamped_call_says_its_terms_are_not_all_measured() -> None:
    """The provenance survives the trip to the disclosure.

    Before Step 4b every clamp rests on a provisional load term, and the
    disclosure has to say so — otherwise a reader takes a stand-in for a
    measurement at exactly the moment the number is being used to take room away.
    """
    recorder = _WireRecorder()
    budget = _budget_of(await _client(recorder, timeout=20.0).chat(_short_message()))

    assert "terms not all measured" in (
        budget.reason or ""
    ), f"a clamp on provisional terms must disclose that; reason was: {budget.reason!r}"


# --------------------------------------------------------------------------
# AC-5 -- num_ctx on the wire
# --------------------------------------------------------------------------


async def test_the_shipped_cap_with_an_ordinary_prompt_sends_no_num_ctx() -> None:
    """Positive control for the test below, and the reason AC-5 is dormant today.

    An ordinary prompt plus the 1024 cap sits well inside the assumed window, so
    no bound is needed and adding one would only be a knob to reason about. If
    ``num_ctx`` appeared here, the test below would prove nothing.
    """
    recorder = _WireRecorder()
    await _client(recorder).chat(_short_message())

    assert (
        "num_ctx" not in recorder.options
    ), f"no bound should be sent for an ordinary prompt; options={recorder.options}"


async def test_a_prompt_that_breaches_the_window_puts_num_ctx_on_the_wire() -> None:
    """AC-5. Without this the PROMPT is truncated rather than the output — and
    ``done_reason``, the truncation oracle this PLAN rests on, reports nothing,
    because from the server's side nothing was cut short.
    """
    recorder = _WireRecorder()
    budget = _budget_of(await _client(recorder).chat(_long_message()))

    assert recorder.options.get("num_ctx") == budget.num_ctx, (
        f"the wire must carry the window the chokepoint decided; "
        f"wire={recorder.options.get('num_ctx')} decided={budget.num_ctx}"
    )


async def test_the_window_sent_holds_the_whole_prompt_and_the_whole_cap() -> None:
    """AC-5's actual claim: prompt + cap <= context.

    Asserted against the estimate the client itself uses, so a change to the
    estimator cannot quietly decouple the two.
    """
    recorder = _WireRecorder()
    budget = _budget_of(await _client(recorder).chat(_long_message()))

    prompt_tokens = estimate_prompt_tokens(_long_message())
    needed = prompt_tokens + budget.applied_num_predict
    assert (budget.num_ctx or 0) >= needed, (
        f"num_ctx={budget.num_ctx} is smaller than prompt({prompt_tokens}) "
        f"+ cap({budget.applied_num_predict}) = {needed}"
    )


async def test_a_sent_num_ctx_is_never_smaller_than_the_assumed_window() -> None:
    """🔴 The property that replaced a dead guard.

    ``_resolve_budget`` first floored ``num_ctx`` at the model's assumed safe
    window, to be sure a provisional 4096 could never SHRINK a real 32768. That
    floor was then proved unreachable — the bound is only sent when
    ``prompt + cap > safe_context``, and the bound is at least ``prompt + cap`` —
    so it was removed rather than shipped as defensive code that cannot fire.

    This test is what keeps the property true after the guard is gone.
    """
    recorder = _WireRecorder()
    budget = _budget_of(await _client(recorder).chat(_long_message()))

    assumed = capacity_for(_SHIPPED_MODEL).safe_context_tokens.value
    assert (budget.num_ctx or 0) >= assumed, (
        f"num_ctx={budget.num_ctx} would SHRINK the assumed window {assumed} — "
        f"the provisional value must never cost real headroom"
    )


# --------------------------------------------------------------------------
# The shape derivation reaches the record
# --------------------------------------------------------------------------


async def test_the_disclosed_shape_tracks_the_arguments_of_the_call() -> None:
    """The chokepoint's derivation is recorded, not just computed.

    All three shapes are folded into ONE assertion: they support the single claim
    "the shape on the record is the shape of the call". Kept out of
    ``parametrize`` on purpose — a parametrised node fails as N cases, which the
    probe driver classifies MISFIRE.
    """
    shapes = []
    for kwargs in ({"response_format": {"type": "object"}}, {"think": True}, {}):
        recorder = _WireRecorder()
        result = await _client(recorder).chat(_short_message(), **kwargs)  # type: ignore[arg-type]
        shapes.append(_budget_of(result).shape)

    assert shapes == ["structuring", "reasoning", "plain"], f"got {shapes}"


async def test_an_unlisted_model_cannot_even_be_constructed() -> None:
    """SD-2, at the seam a caller actually touches."""
    with pytest.raises(UnlistedModelError):
        OllamaClient(workload="S", base_url="http://ollama.test", model="llama3:70b")
