"""PLAN-0119 Step 3 part 2 — the call-shape derivation and the budget rule (AC-4).

Its own module, deliberately. A battery's coverage denominator is every claim in
each file its ``claim_sources`` names, so folding these into an existing test
module would put this AC's claims into a denominator it does not own and make
``GAPS: 0`` unreachable for both.

Every failing assertion here prints the values it measured rather than a bare
verdict (CLAUDE.md Sec 8): the printed number is what makes a disagreement one
step to diagnose instead of a hunt.

Note on shape: cases are written as separate functions rather than
``pytest.mark.parametrize``. A parametrised node fails as N test cases at once,
which the probe-battery driver cannot attribute to a single claim and classifies
MISFIRE. Where several spellings support ONE claim, they are folded into one
assertion instead.
"""

from __future__ import annotations

import pytest

from services.engine.llm.capacity import (
    _MODEL_CAPACITY,
    UnlistedModelError,
    capacity_for,
    derive_call_shape,
    fits_in_timeout,
)

# The three figures PLAN-0118 measured, in tokens/s, derived from the known-1024
# truncated calls. Repeated here as an independent expectation rather than read
# out of the table under test -- a test that reads its expectation from its
# subject agrees with itself by construction.
PLAN_0118_DECODE_RATES = {
    "gpt-oss:20b": 48.3,
    "qwen3.8:27b-mtp-q4_K_M": 19.5,
    "qwen3.8:27b-mtp-q8_0": 18.5,
}


# --------------------------------------------------------------------------
# derive_call_shape -- the chokepoint's shape derivation
# --------------------------------------------------------------------------


def test_a_response_format_makes_the_call_a_structuring_pass() -> None:
    shape = derive_call_shape(think=None, response_format={"type": "object"})
    assert shape == "structuring", f"expected 'structuring', got {shape!r}"


def test_think_without_a_response_format_makes_it_a_reasoning_pass() -> None:
    shape = derive_call_shape(think=True, response_format=None)
    assert shape == "reasoning", f"expected 'reasoning', got {shape!r}"


def test_neither_argument_makes_it_a_plain_generation() -> None:
    shape = derive_call_shape(think=None, response_format=None)
    assert shape == "plain", f"expected 'plain', got {shape!r}"


def test_a_response_format_wins_when_both_arguments_are_set() -> None:
    """Pattern B call 2 is a structuring call even if the caller left ``think`` on.

    Deciding the other way would classify the schema-constrained call as
    reasoning whenever ``think`` was not explicitly cleared, which is precisely
    the pair the taxonomy exists to keep apart.
    """
    shape = derive_call_shape(think=True, response_format={"type": "object"})
    assert shape == "structuring", f"a response_format must dominate a set think; got {shape!r}"


def test_think_false_counts_as_set_because_it_does_not_stop_the_reasoning() -> None:
    """Ollama #18044: ``think: false`` disables the thinking PARSER, not the
    thinking GENERATION -- ``eval_count`` is unchanged. A call that passes it is
    still paying for a reasoning pass, so reading it as "no reasoning" would
    under-budget exactly the calls that most need the room.

    Both falsey spellings are folded into ONE assertion: they support a single
    claim -- "falsey but present is still present" -- and one mutation must be
    able to redden it. The contrast case (an ABSENT ``think`` reading as
    ``plain``) is asserted separately above, so this test would still redden if
    the check were relaxed to a truthiness test.
    """
    shapes = (
        derive_call_shape(think=False, response_format=None),
        derive_call_shape(think="", response_format=None),
    )
    assert shapes == ("reasoning", "reasoning"), (
        f"a falsey-but-present think must read as SET (reasoning), because "
        f"think=False does not stop the generation; got {shapes!r}"
    )


# --------------------------------------------------------------------------
# capacity_for -- SD-2's refuse-at-construction, at its source
# --------------------------------------------------------------------------


def test_a_listed_model_returns_its_measured_capacity() -> None:
    cap = capacity_for("gpt-oss:20b")
    assert (
        cap.decode_tokens_per_s == 48.3
    ), f"gpt-oss:20b decode rate drifted: {cap.decode_tokens_per_s}"


def test_an_unlisted_model_is_refused_rather_than_defaulted() -> None:
    with pytest.raises(UnlistedModelError) as excinfo:
        capacity_for("llama3:70b")
    assert "llama3:70b" in str(
        excinfo.value
    ), f"the refusal must name the model it refused; got: {excinfo.value}"


def test_the_refusal_names_the_models_that_would_have_been_accepted() -> None:
    """A refusal that does not say what WAS acceptable sends the reader to the
    source to find out, which is the one thing an error message exists to save.
    """
    with pytest.raises(UnlistedModelError) as excinfo:
        capacity_for("llama3:70b")
    message = str(excinfo.value)
    missing = [model for model in PLAN_0118_DECODE_RATES if model not in message]
    assert not missing, f"refusal omitted listed models: {missing}; message was: {message}"


def test_the_measured_decode_rates_are_the_plan_0118_figures() -> None:
    """Pins the three rates so a silent edit reddens here rather than in an arm.

    Every model is checked in ONE assertion: they support the single claim "the
    table still holds what PLAN-0118 measured".
    """
    actual = {model: cap.decode_tokens_per_s for model, cap in _MODEL_CAPACITY.items()}
    assert actual == PLAN_0118_DECODE_RATES, (
        f"decode rates drifted from PLAN-0118: expected {PLAN_0118_DECODE_RATES}, " f"got {actual}"
    )


def test_load_prefill_and_context_are_unmeasured_for_every_listed_model() -> None:
    """The three terms Step 4b fills in are ``None``, meaning never measured.

    🔴 This is a NEGATIVE assertion -- "these are all None" is satisfied by an
    EMPTY table -- so it carries its own positive control: the table must first
    be non-empty and hold the models we expect. Without that control a mutation
    emptying ``_MODEL_CAPACITY`` would pass this test green.
    """
    assert set(_MODEL_CAPACITY) == set(PLAN_0118_DECODE_RATES), (
        f"positive control failed -- the table is not the expected set: "
        f"{sorted(_MODEL_CAPACITY)}"
    )
    measured = {
        model: (cap.load_s, cap.prefill_tokens_per_s, cap.safe_context_tokens)
        for model, cap in _MODEL_CAPACITY.items()
        if cap.load_s is not None
        or cap.prefill_tokens_per_s is not None
        or cap.safe_context_tokens is not None
    }
    assert not measured, (
        f"a term claims to be measured before Step 4b ran: {measured}. "
        f"If Step 4b HAS run, this test is the place that records it."
    )


# --------------------------------------------------------------------------
# fits_in_timeout -- AC-4's rule
# --------------------------------------------------------------------------


def test_qwen_at_2048_does_not_fit_a_120s_timeout_once_load_is_paid() -> None:
    """AC-4's named failing case.

    🔴 The failure is carried ENTIRELY by the load term. Decode alone is
    2048 / 19.5 = 105.0 s against a 120 s timeout, leaving **15.0 s** of
    headroom -- so at ``load = prefill = 0`` this case FITS and the criterion
    would close on nothing. PLAN-0118 measured qwen-q4's warm at ~24 s, which is
    what overruns the headroom here.
    """
    verdict = fits_in_timeout(
        cap_tokens=2048,
        decode_tokens_per_s=19.5,
        load_s=24.0,
        prefill_s=0.0,
        timeout_s=120.0,
    )
    assert not verdict.fits, (
        f"qwen at 2048 must not fit a 120s timeout: decode={verdict.decode_s:.1f}s "
        f"load={verdict.load_s:.1f}s prefill={verdict.prefill_s:.1f}s "
        f"projected={verdict.projected_s:.1f}s timeout={verdict.timeout_s:.1f}s"
    )


def test_the_qwen_case_fits_when_load_and_prefill_are_zero() -> None:
    """The other half of the case above, and the reason it is worth stating.

    This is what makes the failing case a real test of the RULE rather than of
    the decode rate: the same cap and the same model flip to fitting the moment
    the unmeasured terms are treated as zero. Anyone tempted to zero them should
    have to redden this test to do it.
    """
    verdict = fits_in_timeout(
        cap_tokens=2048,
        decode_tokens_per_s=19.5,
        load_s=0.0,
        prefill_s=0.0,
        timeout_s=120.0,
    )
    assert verdict.fits, (
        f"with zero overhead qwen at 2048 projects {verdict.projected_s:.1f}s "
        f"against a {verdict.timeout_s:.1f}s timeout and must fit"
    )


def test_gpt_oss_at_4096_fits_the_same_timeout() -> None:
    """AC-4's passing case: the arm Step 6 is aiming at."""
    verdict = fits_in_timeout(
        cap_tokens=4096,
        decode_tokens_per_s=48.3,
        load_s=5.5,
        prefill_s=0.0,
        timeout_s=120.0,
    )
    assert verdict.fits, (
        f"gpt-oss at 4096 must fit a 120s timeout: decode={verdict.decode_s:.1f}s "
        f"projected={verdict.projected_s:.1f}s timeout={verdict.timeout_s:.1f}s"
    )


def test_a_projection_landing_exactly_on_the_deadline_does_not_fit() -> None:
    """Strict ``<``: the timeout ABORTS and discards every token produced, so a
    projection landing on the deadline is a total loss, not a near miss.
    """
    verdict = fits_in_timeout(
        cap_tokens=1200,
        decode_tokens_per_s=10.0,
        load_s=0.0,
        prefill_s=0.0,
        timeout_s=120.0,
    )
    assert not verdict.fits, (
        f"projected={verdict.projected_s!r} against timeout={verdict.timeout_s!r} "
        f"must NOT fit -- equality is a total loss"
    )


def test_the_verdict_carries_every_term_it_used() -> None:
    """CLAUDE.md Sec 8: a report prints the values it measured, never a bare
    verdict. A caller that can only log ``fits`` throws away the evidence the
    call just produced.
    """
    verdict = fits_in_timeout(
        cap_tokens=1024,
        decode_tokens_per_s=48.3,
        load_s=1.0,
        prefill_s=2.0,
        timeout_s=120.0,
    )
    terms = (verdict.decode_s, verdict.load_s, verdict.prefill_s, verdict.timeout_s)
    assert terms == (
        1024 / 48.3,
        1.0,
        2.0,
        120.0,
    ), f"the verdict dropped or altered a term it was given: {terms!r}"


def test_a_non_positive_decode_rate_is_refused_rather_than_answered() -> None:
    """A zero rate divides by zero and a negative one makes a LARGER cap look
    cheaper. Both are corrupt inputs; the caller needs to hear about it rather
    than receive a plausible number.
    """
    with pytest.raises(ValueError, match="must be positive"):
        fits_in_timeout(
            cap_tokens=1024,
            decode_tokens_per_s=0.0,
            load_s=0.0,
            prefill_s=0.0,
            timeout_s=120.0,
        )
