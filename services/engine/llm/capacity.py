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

from dataclasses import dataclass
from typing import Any, Literal

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
    """What has been measured about one model's serving behaviour.

    ``decode_tokens_per_s`` is measured and real (PLAN-0118, derived from the
    known-1024 truncated calls). The remaining three are ``None`` until Step 4b
    runs, and ``None`` here means exactly "never measured" -- never "zero".
    A zero would be a measurement that never happened wearing the shape of one
    that did, which is the same trap ``call_metrics`` avoids field by field.
    """

    decode_tokens_per_s: float
    load_s: float | None = None
    prefill_tokens_per_s: float | None = None
    safe_context_tokens: int | None = None


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
    "gpt-oss:20b": ModelCapacity(decode_tokens_per_s=48.3),
    "qwen3.8:27b-mtp-q4_K_M": ModelCapacity(decode_tokens_per_s=19.5),
    "qwen3.8:27b-mtp-q8_0": ModelCapacity(decode_tokens_per_s=18.5),
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
