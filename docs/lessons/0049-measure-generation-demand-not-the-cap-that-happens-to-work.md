# Lesson 0049: Measure generation demand; never search for the cap that happens to work

**Status:** Advisory (this lesson promotes nothing; it names a method and records
a measurement so neither has to be re-derived)
**Source:** Session 261's `num_predict` finding, extended by session 262's
instrument work on `tools/`-adjacent benchmark plumbing

## What was measured

Session 261 shipped `llm_max_output_tokens` (default **1024**), sent as Ollama's
`num_predict`, so that a deadline breach would leave a short gradeable answer
instead of an aborted one. On the fleet decision dataset the default did the
opposite of its purpose. A single-variable A/B on `fleet-001`, everything else
held identical:

| | `num_predict=1024` | `num_predict=4096` |
|---|---|---|
| result | **UNSCORED** | **FAIL** |
| call-1 draft | **none** | **7,528 chars** |
| LLM calls | 4 (1 + three failed retries) | 2 |

The 1024 failure reproduced 2/2, so it is deterministic rather than model noise.
At 4096 the item — ฿5,001, exactly at the ceiling, `forbidden_keywords: ['tow']`
— drew a proposal of `tow_to_partner_garage`, a forbidden handler for a truck
that still drives. That is the single most decision-relevant behaviour the
session observed, and the shipped default hid it completely.

## The three outcomes a cap produces, only two of which are visible

| cap | what happens | how it reads |
|---|---|---|
| far too low | call 1 emits nothing; call 2 has nothing to structure | **loud** — no JSON, an unscored item |
| **slightly too low** | **call 1 is clipped mid-reasoning; call 2 structures the fragment into a well-formed envelope** | **a perfectly ordinary pass or fail** |
| adequate | call 1 ends on its own | trustworthy |

The middle row is the dangerous one, and it is dangerous *because* it is quiet.
An unscored item announces that the instrument could not measure. A judgment
resting on clipped reasoning enters the results looking healthy and gets counted.

## Why "find the minimum working value" selects exactly the wrong cap

A search over caps returns one pass/fail bit per run, where "pass" means output
that parsed. It therefore converges on the **smallest cap that still yields
parseable output** — which is the middle row above. The search procedure is not
merely imprecise; its objective function is aimed at the failure mode.

The fix is to change the quantity being measured. `eval_count` is the tokens the
model actually generated — its **demand**. Run once at a deliberately high
ceiling and the whole distribution of demand falls out, one number per call
rather than one bit per run, and the cap is then chosen above the observed
maximum with headroom. Demand is a property of the workload; the cap is a
decision about the workload. Measuring the former beats searching the latter.

## `done_reason` is the oracle, and it was already in the building

Ollama reports `done_reason="stop"` when the model ended on its own and
`"length"` when generation hit `num_predict`. `ChatResult.raw` has always
carried the whole response envelope — and every consumer dropped it. Verified
on the artifacts themselves: neither `benchmarks/model_compare/evidence/*.jsonl`
nor session 261's surviving `/tmp/runA-1024.jsonl` / `runB-4096.jsonl` contains
`done_reason` or `eval_count` anywhere. So the only signal any run ever wrote
down was a character count, and a character count cannot separate "finished and
brief" from "cut mid-sentence". That is why 261 could only tell the two apart by
running the same item twice at two caps and comparing.

⚠️ **`done_reason="length"` on `num_predict` exhaustion is asserted, not yet
measured on this server.** It is knowledge of Ollama's contract, and it must be
the first and cheapest gate of any run that relies on it — one call with
`num_predict=10` and a trivial prompt, which must come back `"length"`.

## A zero from an absent field is not a zero

If the server omits `done_reason`, every call scores "not truncated" and a
truncation count prints a reassuring **0** that actually means *not measured*.
Any report over this data must therefore count three things, never two:
truncated, clean, and **oracle absent**. The same shape as CLAUDE.md §8's rule
that no evidence yet is not a pass.

## One cap for everything is the same error one layer up

The chokepoint argument for a single application site is sound and survives:
eight call sites construct a client, and a bound passed at each of them is one
forgotten argument from being off. But a single **application site** is not a
single **value**. This repo's own matrix makes the point — `ReasoningMode` is
`full` / `think_off` / `skip`, and in `full` the reasoning lands in a separate
`thinking` channel while in `think_off` it is all inline content. Those cells
cannot plausibly share one demand figure, and the 7,528-char measurement above
came from `think_off` — *not* the shipped `full` path.

Stated generally: demand is a property of **(model × reasoning mode × workload)**,
and a config value that ignores any of those three dimensions is an instrument
that contaminates its subject.

---

## PORTABLE CORE

> *Everything above is vero-lite's instance. This section is the part that
> transfers, kept separate so extracting it later is a lift, not a rewrite. It is
> deliberately written without reference to this repo's file paths, verticals, or
> plan numbers. See the Active TODO in `docs/STATUS.md` for the standing
> intent — no second project exists yet, and per CLAUDE.md §1's Rule of Three
> the abstraction is not extracted until there is something to extract toward.*

**Before benchmarking or comparing LLMs, establish each model's generation
config first — it is a precondition of the comparison, not a tuning detail.**

1. **A global value shared across models is an instrument that contaminates the
   subject.** One number applied to every model reports the config's behaviour
   wearing the model's name.
2. **Measure demand, do not search supply.** Read the provider's generated-token
   counter at a high ceiling and take the distribution. Searching for the
   smallest cap that "works" converges on the cap that silently clips.
3. **"Could not measure" and "measured and wrong" are different kinds of fact.**
   Never let a pipeline collapse them into one column; the first indicts the
   instrument, the second the subject.
4. **Output that parses is not output that was complete.** A truncated reasoning
   pass still structures into a well-formed envelope. Use the provider's own
   stop-reason field — Ollama `done_reason`, OpenAI-compatible `finish_reason` —
   never an inferred length comparison.
5. **A missing stop-reason must never read as a clean run.** Count truncated,
   clean, and unmeasured separately, and say so out loud when the third is
   non-zero.
6. **If the harness does not already record the provider's response metadata,
   plumb it before the first live run.** It is usually received and discarded at
   some boundary, it costs nothing to carry, and no amount of later analysis can
   recover a field that was never written down.
7. **Demand varies by (model × mode × workload).** Any one config value is a
   claim about all three; check whether the claim is one you measured.
8. **Change one variable per run.** A prompt edit bundled into a demand
   measurement makes a lower token count unattributable — efficiency and
   suppressed reasoning look identical in the number.
