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
    estimate_prompt_tokens,
    evaluate_budget,
    fits_in_timeout,
    needs_explicit_context,
    required_context_tokens,
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
        cap.decode_tokens_per_s.value == 48.3
    ), f"gpt-oss:20b decode rate drifted: {cap.decode_tokens_per_s.value}"


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
    actual = {model: cap.decode_tokens_per_s.value for model, cap in _MODEL_CAPACITY.items()}
    assert actual == PLAN_0118_DECODE_RATES, (
        f"decode rates drifted from PLAN-0118: expected {PLAN_0118_DECODE_RATES}, " f"got {actual}"
    )


def test_only_the_decode_rate_is_measured_and_the_other_three_are_not() -> None:
    """The provenance split, asserted in BOTH directions.

    🔴 Half of this is a NEGATIVE assertion -- "load, prefill and context are not
    measured" is satisfied vacuously by an EMPTY table -- so it carries its own
    positive control twice over: the table's membership is pinned first, and the
    decode rate must come back as measured. Without those, a mutation emptying
    ``_MODEL_CAPACITY`` or flipping every term to unmeasured would pass green.

    🔴 **This test is the tripwire for Step 4b.** When the live run supplies real
    load / prefill / context numbers, this reddens -- which is the point. It is
    not an obstacle to that landing; it is the thing that stops the numbers
    landing SILENTLY, with nobody updating the places that reason about whether
    the budget rule can be trusted yet.
    """
    assert set(_MODEL_CAPACITY) == set(PLAN_0118_DECODE_RATES), (
        f"positive control failed -- the table is not the expected set: "
        f"{sorted(_MODEL_CAPACITY)}"
    )

    unmeasured_decode = [
        m for m, c in _MODEL_CAPACITY.items() if not c.decode_tokens_per_s.measured
    ]
    assert not unmeasured_decode, (
        f"positive control failed -- the decode rate IS measured and must say so; "
        f"models claiming otherwise: {unmeasured_decode}"
    )

    wrongly_measured = {
        model: [
            name
            for name, term in (
                ("load_s", cap.load_s),
                ("prefill_s", cap.prefill_s),
                ("safe_context_tokens", cap.safe_context_tokens),
            )
            if term.measured
        ]
        for model, cap in _MODEL_CAPACITY.items()
        if cap.load_s.measured or cap.prefill_s.measured or cap.safe_context_tokens.measured
    }
    assert not wrongly_measured, (
        f"a term claims to be MEASURED before Step 4b ran: {wrongly_measured}. "
        f"If Step 4b HAS run, this test is the place that records it -- update it "
        f"deliberately rather than deleting it."
    )


def test_every_provisional_term_names_the_step_that_replaces_it() -> None:
    """A stand-in whose replacement is unnamed is a stand-in nobody will retire.

    Carries a positive control: provisional terms must actually EXIST for this to
    mean anything, so the count is asserted non-zero before the property is
    checked on them.
    """
    provisional = [
        (model, name, term)
        for model, cap in _MODEL_CAPACITY.items()
        for name, term in (
            ("load_s", cap.load_s),
            ("prefill_s", cap.prefill_s),
            ("safe_context_tokens", cap.safe_context_tokens),
        )
        if not term.measured
    ]
    assert len(provisional) == 9, (
        f"positive control failed -- expected 9 provisional terms "
        f"(3 models x 3 terms), found {len(provisional)}"
    )
    unnamed = [(m, n) for m, n, t in provisional if not t.replaced_by or not t.source]
    assert not unnamed, f"provisional terms with no source or no replaced_by: {unnamed}"


def test_no_model_reports_itself_fully_measured_before_step_4b() -> None:
    claiming = [model for model, cap in _MODEL_CAPACITY.items() if cap.fully_measured]
    assert not claiming, (
        f"models claiming full measurement before Step 4b ran: {claiming}. "
        f"fully_measured gates whether a budget verdict can be trusted."
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


# --------------------------------------------------------------------------
# evaluate_budget -- the rule applied through the table, carrying provenance
# --------------------------------------------------------------------------


def test_a_verdict_built_from_provisional_terms_says_it_is_not_measured() -> None:
    """The whole point of the posture: a caller cannot act on this verdict
    without being able to see that it rests on a stand-in.
    """
    verdict = evaluate_budget(model="gpt-oss:20b", cap_tokens=1024, timeout_s=120.0)
    assert not verdict.terms_measured, (
        f"before Step 4b no verdict may claim measured terms; "
        f"projected={verdict.projected_s:.1f}s load={verdict.load_s:.1f}s"
    )


def test_the_shipped_1024_cap_fits_on_the_model_every_system_actually_runs() -> None:
    """A regression floor: today's shipped configuration must project as fitting.

    If this reddens, the seam has made the CURRENT behaviour unservable -- which
    would be a defect in the seam, not a discovery about the budget.
    """
    verdict = evaluate_budget(model="gpt-oss:20b", cap_tokens=1024, timeout_s=120.0)
    assert verdict.fits, (
        f"the shipped cap must fit: decode={verdict.decode_s:.1f}s "
        f"load={verdict.load_s:.1f}s prefill={verdict.prefill_s:.1f}s "
        f"projected={verdict.projected_s:.1f}s timeout={verdict.timeout_s:.1f}s"
    )


def test_qwen_at_2048_is_refused_through_the_table_not_only_by_hand() -> None:
    """AC-4's named failing case, reached the way production would reach it.

    The by-hand version above proves the RULE; this proves the rule plus the
    TABLE, which is what a caller actually gets. The provisional load term is
    what carries the refusal -- see the by-hand pair for why that matters.
    """
    verdict = evaluate_budget(model="qwen3.8:27b-mtp-q4_K_M", cap_tokens=2048, timeout_s=120.0)
    assert not verdict.fits, (
        f"qwen-q4 at 2048 must be refused: decode={verdict.decode_s:.1f}s "
        f"load={verdict.load_s:.1f}s prefill={verdict.prefill_s:.1f}s "
        f"projected={verdict.projected_s:.1f}s timeout={verdict.timeout_s:.1f}s"
    )


def test_evaluating_a_budget_for_an_unlisted_model_refuses() -> None:
    with pytest.raises(UnlistedModelError):
        evaluate_budget(model="llama3:70b", cap_tokens=1024, timeout_s=120.0)


# --------------------------------------------------------------------------
# AC-5 -- num_ctx and the context headroom
# --------------------------------------------------------------------------


def test_the_prompt_estimate_counts_every_field_not_only_content() -> None:
    """A role, a name, or any other field a caller included is serialised onto
    the wire and occupies context too. Counting only ``content`` would
    under-state the prompt, which is the unsafe direction.
    """
    with_role_only = estimate_prompt_tokens([{"role": "user", "content": "hello"}])
    with_extra_field = estimate_prompt_tokens(
        [{"role": "user", "content": "hello", "name": "a-much-longer-value"}]
    )
    assert with_extra_field > with_role_only, (
        f"an extra serialised field must raise the estimate: "
        f"{with_role_only} -> {with_extra_field}"
    )


def test_a_short_prompt_never_estimates_as_zero_tokens() -> None:
    """Rounding UP matters: a zero-token prompt would make the headroom check
    believe the whole context is available for generation.
    """
    estimate = estimate_prompt_tokens([{"role": "u", "content": "x"}])
    assert estimate >= 1, f"estimate rounded down to {estimate}"


def test_a_1024_cap_against_a_4096_window_does_not_need_an_explicit_context() -> None:
    """Today's shipped configuration, and the reason AC-5 is not already firing:
    741 + 1024 is well inside 4096. This is the positive control for the test
    below -- without it, a ``needs_explicit_context`` stuck at True would look
    correct.
    """
    assert not needs_explicit_context(
        prompt_tokens=741, cap_tokens=1024, safe_context_tokens=4096
    ), "the shipped cap must not require an explicit num_ctx"


def test_a_4096_cap_against_the_same_window_does_need_one() -> None:
    """Step 6's arm, and exactly the breach PLAN-0119 warns about: a 741-token
    prompt plus a 4096 cap does not fit a 4096 window, and NOT sending
    ``num_ctx`` truncates the PROMPT -- a failure ``done_reason`` cannot see.
    """
    assert needs_explicit_context(
        prompt_tokens=741, cap_tokens=4096, safe_context_tokens=4096
    ), "a 741-token prompt plus a 4096 cap breaches a 4096 window"


def test_the_context_sent_always_holds_the_prompt_plus_the_whole_cap() -> None:
    """AC-5's claim, asserted over a spread of shapes in ONE assertion.

    🔴 The spread IS the positive control. A constant implementation -- one
    returning 4096 whatever it was asked -- passes any single small case and
    fails here on the large prompt, which is the case it must not be allowed to
    pass by luck.
    """
    cases = [(741, 1024), (741, 4096), (8000, 4096), (1, 1), (32000, 8192)]
    breaches = [
        (prompt, cap, required_context_tokens(prompt_tokens=prompt, cap_tokens=cap))
        for prompt, cap in cases
        if prompt + cap > required_context_tokens(prompt_tokens=prompt, cap_tokens=cap)
    ]
    assert not breaches, f"num_ctx smaller than prompt + cap for (prompt, cap, ctx): {breaches}"
