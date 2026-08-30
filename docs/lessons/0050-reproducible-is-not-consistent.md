# Lesson 0050: Reproducible is not consistent, and only one of them can be engineered by rerunning

**Status:** Advisory (names a distinction and records the measurement behind it;
the metric it defines ships as `benchmarks/procedure_baseline/tier_consistency.py`)
**Source:** Session 262 — stage 2a/2b of the fleet demand runs

## The distinction

**Reproducibility** — run the same item twice, is the answer the same? A property
of the **instrument**.

**Consistency** — do items the governing rule treats as the *same case* get the
same **class** of answer? A property of the **judgment**, and the one a user has
to be able to trust.

They are independent, and a model can be perfect on the first while failing the
second. This one is.

## What was measured

`fleet` × `qwen/full`, twice, `LLM_MAX_OUTPUT_TOKENS=16384`, nothing truncated:

- **Reproducibility: 20/20.** Reasoning drafts identical character for character,
  rationales identical, handlers identical, every `eval_count` identical — while
  judgment latency differed on 17 of 20, which is what proves two genuine runs
  rather than one file read twice.
- **Consistency: 9/14.** Ten breach items sit in the same DOA authority band
  (฿5,001–30,000), where the rule has already decided the amount is irrelevant.
  They drew four different classes of answer: `escalate` ×5, `echo` ×2 (one on a
  **฿22,800** repair — a no-op), `dispatch_replacement_truck` ×2,
  `tow_to_partner_garage` ×1 (a forbidden handler). **No pattern by amount** —
  ฿30,000 escalates while ฿22,800 does not.

The band above (≥฿30,001) was **4/4**. So the divergence is not uniform noise; it
is concentrated where the stakes are mid-range.

## Why the difference matters more than the numbers

**Rerunning cannot fix an inconsistency.** Because the model is bit-exactly
reproducible, it returns the *same* unpatterned set of answers every time. Repeats
buy nothing. The instinct to "run it again and see" — which is the right instinct
against flakiness — is exactly wrong here, and the reproducibility measurement is
what tells you so.

A grader can also hide it. β scored this run at 85.7% and the handler probe at
78.6%, because both ask *was this item right*. Consistency asks *did one rule
produce one answer*, and it is the harshest of the three precisely because it is
closest to what an operator experiences.

## Consistency has to be structural, not hoped-for

Today it depends on the model reasoning its way to the same place twice, from
prose. Two measured facts say that is the wrong place to put the weight.

**1. The governance is not in the constraint.** Call 2 builds its handler enum as
`_judgment_schema(registry.handler_names(vertical))` — **every** handler the
vertical registers, **independent of the band**. `fleet-004` could answer `echo`
on ฿22,800 *because the schema allowed it*; the DOA ladder exists only in the
prompt, which is a thing the model may or may not honour. Narrowing the enum by
band would make that class of answer **inexpressible** rather than merely
discouraged.

⚠️ With a trade-off worth stating: narrow it in the benchmark too and you lose the
signal that the model *would have* answered wrongly. Narrow in production, keep
the wide enum where you are measuring.

**2. The inputs a real decision needs are not in the ontology.** Measured across
all 20 fleet items, `scenario.context` carries `plate`, `truck_class`, `symptom`,
`drivable` (20/20), `quotes_obtained` (14/20 — a **count**, not the quotes),
`load_aboard` (3/20), `delivery_window_hours` (2/20). There is **no supplier
identity, no delivery history, no quality record, and no per-quote price**. So the
ordinary procurement judgement — *the cheapest quote is not chosen because that
supplier delivers late* — is not something the model is getting wrong. It is
**currently inexpressible**, and no amount of prompt work reaches it.

Put together: the route to consistency is to move the decision into a declared,
ordered structure and shrink the model's job to **supplying each criterion's
input**, which is the part it is reliable at. The reason then generates from the
rule — *"not the cheapest, because on-time rate 0.6 < 0.9 and reliability outranks
price"* — which is auditable, and auditable is what trust is made of.

## The metric, and the ruling that defines it

Group breach items by the **governing rule's own structure** (for fleet, the DOA
ladder), then score against each band's canonical handler.

🔴 **Cray's ruling, 2026-08-30 (typed): the STRICT reading.** A handler the grader
tiers as *acceptable* is still a **different class of answer**.
`dispatch_replacement_truck` does not agree with `escalate`, because the question
is *who has authority to approve this spend* and dispatching a truck answers a
different one — however sensible it is as a parallel action. Strict gives 9/14
where lenient gives 11/14, and the gap is the judgement.

The definition lives in `tier_consistency.py` rather than only here, because a
definition that has to be re-derived is one that will be re-derived differently.

## The rule

**Before treating a rerun as evidence, ask which property you are testing.** If
the instrument is reproducible, repeats measure nothing about the judgment —
and a model that always gives the same scattered answers is not more trustworthy
than one that scatters differently each time. It is only easier to study.
