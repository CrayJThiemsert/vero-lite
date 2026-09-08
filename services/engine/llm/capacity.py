"""Per-model serving capacity and the budget rule that reads it.

PLAN-0119 Step 3 part 2. This module holds the three things the chokepoint in
:mod:`services.engine.llm.client` needs but should not itself define:

1. **The call shape**, derived from what is already visible at the chokepoint —
   a ``response_format`` present means a structuring pass, ``think`` set with no
   ``response_format`` means a reasoning pass. Pattern B's two calls are told
   apart without any new argument reaching ``chat()``.
2. **The per-model capacity table**, keyed on the model string a client is bound
   to. It records what has been *measured* about a model's serving behaviour.
3. **The budget rule** ``cap / decode_rate + load + prefill < timeout`` (AC-4),
   as a pure function over its terms.

Why a separate module rather than more of ``client.py``: the rule is arithmetic
over measurements and has no business holding an HTTP client's state, and a
battery's coverage denominator is every claim in each file it names — giving
this AC's tests their own module is what keeps ``GAPS: 0`` reachable for them.

⚠️ **The terms are not all measured, and that is load-bearing, not incidental.**
``decode_tokens_per_s`` came from PLAN-0118 and is real. ``load`` and ``prefill``
only became *recordable* in PLAN-0119 Step 2 and have never been run; the
effective ``num_ctx`` on the box (OQ-7) has never been measured at all. Step 4b
is what fills them in, under its own CLAUDE.md Sec 8 go. Until then the honest
statement about those terms is "unknown", and how the rule behaves in the
presence of an unknown term is a posture decision recorded below.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import ceil
from typing import Any, Generic, Literal, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Term(Generic[T]):
    """One capacity number, carrying where it came from.

    🔴 **The provenance is the point, not decoration.** A provisional number that
    looks like a measured one is the failure this type exists to make
    impossible: a placeholder silently hardens into a fact, and every decision
    downstream inherits a confidence nobody ever earned. CLAUDE.md Sec 6 states
    the general rule -- an inherited premise a decision rests on is a claim, not
    context, and must be marked ``asserted-not-verified`` where the decision is
    recorded. This is that marking, in the type system.

    ``measured`` False means the value is a stand-in chosen to be pessimistic:
    it may make the budget rule refuse a cap that would in fact have fitted, and
    that direction is deliberate. It must never make the rule ACCEPT a cap it
    could not otherwise justify.

    ``replaced_by`` names the step that will supply the real number, so a reader
    who wants to know when this stops being a guess does not have to search.
    """

    value: T
    measured: bool
    source: str
    replaced_by: str | None = None


#: Which of the three shapes a single chat call takes, derived at the chokepoint.
#:
#: Distinct from :data:`~services.engine.llm.client.CallRole`, which tags METRICS
#: after the fact for the two Pattern B calls. This one is derived BEFORE the call
#: from the arguments themselves, because it is what a budget has to be chosen
#: from -- a reasoning pass and a structuring pass on the same model differ in
#: demand by an order of magnitude.
CallShape = Literal["structuring", "reasoning", "plain"]


def derive_call_shape(
    *,
    think: bool | str | None,
    response_format: dict[str, Any] | None,
) -> CallShape:
    """Classify one chat call from the two arguments the chokepoint can already see.

    The rule is PLAN-0119 Step 3's, verbatim: a ``response_format`` present means
    a structuring pass; ``think`` set with no ``response_format`` means a
    reasoning pass. Everything else is a plain generation.

    ``response_format`` wins when both are set. That ordering is deliberate and
    it matches the CHECKPOINT-0 contract in ``client.chat``: a constrained call
    is a structuring call whatever it was allowed to think along the way, because
    the schema is what bounds its output. Deciding the other way would classify
    Pattern B's *second* call as reasoning whenever a caller left ``think`` on.

    ``think=False`` counts as SET, not as absent. Ollama issue #18044 measured
    that ``think: false`` disables the thinking *parser*, not the thinking
    *generation* -- ``eval_count`` is unchanged -- so a call that passes it is
    still paying for a reasoning pass and must not be budgeted as if it were not.
    Reading it as "no reasoning" would under-budget exactly the calls that most
    need the room.
    """
    if response_format is not None:
        return "structuring"
    if think is not None:
        return "reasoning"
    return "plain"


@dataclass(frozen=True)
class ModelCapacity:
    """One model's serving capacity, term by term, each carrying its provenance.

    Exactly one term is measured today -- ``decode_tokens_per_s``, from PLAN-0118,
    derived from the known-1024 truncated calls. The other three are provisional
    and Step 4b replaces them.

    Every term is a :class:`Term` rather than a bare number, uniformly, so that
    "is this measured?" is answered the same way for all of them. A design where
    only the doubtful ones were wrapped would make the wrapper itself the signal
    -- and the day a fourth term arrived, the person adding it would have to
    already know the convention to get it right.
    """

    decode_tokens_per_s: Term[float]
    load_s: Term[float]
    prefill_s: Term[float]
    safe_context_tokens: Term[int]

    @property
    def fully_measured(self) -> bool:
        """True only when no term is still standing in for a measurement."""
        return all(
            term.measured
            for term in (
                self.decode_tokens_per_s,
                self.load_s,
                self.prefill_s,
                self.safe_context_tokens,
            )
        )


def _provisional_load(seconds: float) -> Term[float]:
    """A model's load time, standing in until Step 4b measures it.

    The stand-in is PLAN-0118's observed WARM time for that model. It is the only
    load-shaped number on disk, and it is pessimistic in the right direction: a
    warm pays the full weight load, so a call arriving at an already-resident
    model is charged for something it will not actually pay.
    """
    return Term(
        value=seconds,
        measured=False,
        source="PLAN-0118 observed warm time (the only load-shaped figure on disk)",
        replaced_by="PLAN-0119 Step 4b (load_duration_ns, recordable since Step 2)",
    )


def _unmeasured_prefill() -> Term[float]:
    """Prefill time, with NO stand-in value -- deliberately zero.

    🔴 A tempting stand-in exists and is FORBIDDEN. PLAN-0118 measured a
    ``total_duration - eval_duration`` residual of 10.4-54.4 s that "contains
    prefill and grammar-compilation time", and subtracting the warm time from it
    would yield a prefill-shaped number. That is the contested OQ-1 residual, and
    PLAN-0119's Out of Scope forbids it in as many words: nothing in this PLAN
    may be built on that reconstruction. The decomposition is also visibly
    unstable -- it puts q8's prefill BELOW q4's, which is the wrong order.

    So this term contributes nothing to the projection and says so. The safety
    margin before Step 4b comes entirely from the load term, which does have an
    anchor. Inventing a number here to look thorough would be exactly the
    placeholder-hardening failure :class:`Term` exists to prevent -- and it would
    be worse than a zero, because a zero cannot be mistaken for evidence.
    """
    return Term(
        value=0.0,
        measured=False,
        source=(
            "no measurement exists; deriving one from the OQ-1 residual is "
            "forbidden by PLAN-0119 Out of Scope"
        ),
        replaced_by="PLAN-0119 Step 4b (prompt_eval_duration_ns, recordable since Step 2)",
    )


def _unmeasured_context() -> Term[int]:
    """The effective runtime context window -- OQ-7, never measured.

    4096 is the pessimistic reading, and pessimistic here means SMALL: a smaller
    assumed window makes AC-5 send an explicit ``num_ctx`` sooner, which is the
    safe direction. The box reports a model ``context_length`` of 32768, but
    Ollama's RUNTIME ``num_ctx`` default is a separate thing and is what actually
    binds. Assuming the larger number is what would let a prompt be silently
    truncated instead of the output -- a strictly worse failure, because
    ``done_reason`` cannot see it.
    """
    return Term(
        value=4096,
        measured=False,
        source=(
            "pessimistic assumption of Ollama's runtime num_ctx default; the "
            "model's reported context_length of 32768 is a DIFFERENT number"
        ),
        replaced_by="PLAN-0119 Step 4b / OQ-7",
    )


def _measured_decode(rate: float) -> Term[float]:
    """A model's decode rate -- the one term that is genuinely measured."""
    return Term(
        value=rate,
        measured=True,
        source="PLAN-0118, derived from the known-1024 truncated calls",
    )


#: Serving capacity per model. The key is the exact model string a client binds.
#:
#: Only the three models PLAN-0119 names are listed, because they are the three
#: PLAN-0118 measured. An unlisted model refuses at construction (SD-2 = (b)):
#: serving a model nobody has measured is not a smaller version of serving a
#: measured one, it is serving with the budget rule switched off.
_MODEL_CAPACITY: dict[str, ModelCapacity] = {
    # The only model any published system actually runs today: `recommender_model`
    # defaults to it, `procedure_draft._GENERATOR_MODEL` pins it, and no
    # published.env overrides either (verified by grep at s287).
    "gpt-oss:20b": ModelCapacity(
        decode_tokens_per_s=_measured_decode(48.3),
        load_s=_provisional_load(5.5),
        prefill_s=_unmeasured_prefill(),
        safe_context_tokens=_unmeasured_context(),
    ),
    "qwen3.8:27b-mtp-q4_K_M": ModelCapacity(
        decode_tokens_per_s=_measured_decode(19.5),
        load_s=_provisional_load(24.0),
        prefill_s=_unmeasured_prefill(),
        safe_context_tokens=_unmeasured_context(),
    ),
    "qwen3.8:27b-mtp-q8_0": ModelCapacity(
        decode_tokens_per_s=_measured_decode(18.5),
        load_s=_provisional_load(46.0),
        prefill_s=_unmeasured_prefill(),
        safe_context_tokens=_unmeasured_context(),
    ),
}


class UnlistedModelError(ValueError):
    """Raised when a client is constructed for a model with no measured capacity.

    SD-2 = (b), ruled s274: the refusal happens app-side, at construction, rather
    than at the first call. A model reaches the capacity table by being measured,
    so this error is a statement that a measurement is missing -- and the fix is
    to run Step 4b for that model, never to widen the table by hand.
    """


def capacity_for(model: str) -> ModelCapacity:
    """Return the measured capacity for ``model``, or refuse.

    Raises :class:`UnlistedModelError` when the model has no entry. The message
    names the listed set, because the failure a reader hits in practice is a
    typo or a newly pulled tag, and a refusal that does not say what WAS
    acceptable sends them to the source to find out.
    """
    try:
        return _MODEL_CAPACITY[model]
    except KeyError:
        listed = ", ".join(sorted(_MODEL_CAPACITY))
        raise UnlistedModelError(
            f"model {model!r} has no measured serving capacity; "
            f"listed models are: {listed}. A model is added to the table by "
            f"measuring it (PLAN-0119 Step 4b), not by hand."
        ) from None


@dataclass(frozen=True)
class BudgetVerdict:
    """The result of evaluating AC-4's budget rule, with the terms it used.

    Every term is carried, not just the boolean. CLAUDE.md Sec 8: a verification
    report prints the values it measured -- ``pre=1 post=2``, never a bare
    PASS/FAIL -- because the printed value is what makes a disagreement one step
    to diagnose instead of a hunt. A caller logging only ``fits`` throws away the
    evidence the call just produced.

    ``terms_measured`` is False when any term came from something other than a
    measurement of this model. It exists so that no consumer can act on this
    verdict without being able to see that it rests on an unmeasured term.
    """

    fits: bool
    projected_s: float
    decode_s: float
    load_s: float
    prefill_s: float
    timeout_s: float
    terms_measured: bool


def fits_in_timeout(
    *,
    cap_tokens: int,
    decode_tokens_per_s: float,
    load_s: float,
    prefill_s: float,
    timeout_s: float,
) -> BudgetVerdict:
    """Evaluate ``cap / decode_rate + load + prefill < timeout`` (AC-4).

    Pure arithmetic over its five terms -- it reads no table, no settings and no
    clock, so it is the same function whatever posture the caller takes toward an
    unmeasured term. That separation is the point: the *rule* is not in dispute,
    only what to feed it when a term is unknown.

    ``terms_measured`` is left True here and narrowed by the caller, which is the
    only party that knows where its terms came from.

    Why strict ``<``: the timeout ABORTS and discards every token already
    produced (``config.py`` says so in as many words), so a projection landing
    exactly on the deadline is a total loss, not a near miss.

    Raises ``ValueError`` on a non-positive decode rate. A zero rate would divide
    by zero and a negative one would make a larger cap look cheaper -- both are
    corrupt inputs, and the caller that produced one needs to hear about it
    rather than receive a plausible number.
    """
    if decode_tokens_per_s <= 0:
        raise ValueError(
            f"decode_tokens_per_s must be positive, got {decode_tokens_per_s!r}; "
            "a non-positive rate cannot bound a generation time"
        )
    decode_s = cap_tokens / decode_tokens_per_s
    projected_s = decode_s + load_s + prefill_s
    return BudgetVerdict(
        fits=projected_s < timeout_s,
        projected_s=projected_s,
        decode_s=decode_s,
        load_s=load_s,
        prefill_s=prefill_s,
        timeout_s=timeout_s,
        terms_measured=True,
    )


def evaluate_budget(*, model: str, cap_tokens: int, timeout_s: float) -> BudgetVerdict:
    """Apply AC-4's rule to a model, reading its terms from the capacity table.

    The seam between this and :func:`fits_in_timeout` is where the posture lives:
    the rule is pure arithmetic and does not know whether its inputs are real,
    while this function does and says so on the way out. ``terms_measured`` is
    narrowed to the model's own ``fully_measured``, so no caller can act on a
    verdict without being able to see that it rests on a stand-in.

    Raises :class:`UnlistedModelError` for a model with no capacity entry.
    """
    capacity = capacity_for(model)
    verdict = fits_in_timeout(
        cap_tokens=cap_tokens,
        decode_tokens_per_s=capacity.decode_tokens_per_s.value,
        load_s=capacity.load_s.value,
        prefill_s=capacity.prefill_s.value,
        timeout_s=timeout_s,
    )
    return replace(verdict, terms_measured=capacity.fully_measured)


def largest_fitting_cap(*, model: str, timeout_s: float) -> int:
    """The biggest ``num_predict`` whose projection still lands inside the timeout.

    This is what the clamp bounds a class's request DOWN to. It is exact, not a
    search: the largest integer strictly below ``budget * rate`` is
    ``ceil(budget * rate) - 1``, and strictness is what keeps a projection landing
    exactly on the deadline out of the answer -- the timeout aborts and discards
    every token produced, so equality is a total loss.

    Returns 0 when the load and prefill terms alone already exceed the timeout.
    A zero cap is not servable, and a caller receiving one should refuse rather
    than send it; it means the model cannot answer at all within the deadline,
    which is a configuration fault rather than a budgeting one.

    Raises :class:`UnlistedModelError` for a model with no capacity entry.
    """
    capacity = capacity_for(model)
    budget_s = timeout_s - capacity.load_s.value - capacity.prefill_s.value
    if budget_s <= 0:
        return 0
    return max(0, ceil(budget_s * capacity.decode_tokens_per_s.value) - 1)


#: Characters per generated token, measured across PLAN-0118's arms as
#: ``content_chars / eval_count`` = 2.71-3.47. The LOW end is used deliberately:
#: fewer characters per token means MORE tokens estimated for the same text, which
#: over-states the prompt. For a context-headroom check, over-stating the prompt is
#: the safe error -- it sends an explicit ``num_ctx`` sooner than strictly needed,
#: where under-stating it lets the prompt be silently truncated.
#:
#: ⚠️ It is a ratio measured on GENERATED content, applied here to PROMPT text.
#: Nothing on disk measures the prompt-side ratio; this is the closest anchor that
#: exists, and it is used only to decide whether to send a bound, never to report a
#: token count as a measurement.
_CHARS_PER_TOKEN = 2.71


def estimate_prompt_tokens(messages: list[dict[str, str]]) -> int:
    """Estimate the prompt's token count from the characters actually being sent.

    Counts every value in every message, not just ``content``: a role, a name or
    any other field the caller included is serialised onto the wire and occupies
    context too. Rounds UP, so a short prompt never estimates as zero tokens.
    """
    characters = sum(len(value) for message in messages for value in message.values())
    return ceil(characters / _CHARS_PER_TOKEN)


def needs_explicit_context(
    *, prompt_tokens: int, cap_tokens: int, safe_context_tokens: int
) -> bool:
    """True when prompt + cap could breach the context window (AC-5's trigger).

    Below this line the server's own default is adequate and sending ``num_ctx``
    would only add a knob to reason about. Above it, NOT sending one moves the
    failure somewhere invisible: the prompt gets truncated rather than the
    output, and ``done_reason`` -- the truncation oracle this whole PLAN rests on
    -- reports nothing at all, because from the server's point of view nothing
    was cut short.
    """
    return prompt_tokens + cap_tokens > safe_context_tokens


def required_context_tokens(*, prompt_tokens: int, cap_tokens: int) -> int:
    """The ``num_ctx`` to send so that prompt + generation both fit.

    Guarantees ``prompt_tokens + cap_tokens <= result`` -- that is AC-5's whole
    claim, and it is what the test asserts. The 10% margin absorbs the estimate's
    error (``estimate_prompt_tokens`` approximates from characters), and the
    round up to a 512-token boundary keeps the value tidy without ever rounding
    DOWN, which would silently undo the guarantee.
    """
    needed = ceil((prompt_tokens + cap_tokens) * 1.1)
    return ceil(needed / 512) * 512
