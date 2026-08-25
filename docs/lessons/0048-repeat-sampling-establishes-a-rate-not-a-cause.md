# Lesson 0048: Repeat-sampling establishes a rate; measuring the mechanism establishes a cause

**Status:** Advisory (ADR-0038 D1 — this lesson promotes nothing; it names
a method so the method stops being unciteable)
**Source:** PLAN-0099 (`docs/plans/done/0099-wall-clock-root-fix-store-at-write-and-sequence.md`),
promoted to a durable surface by PLAN-0115 (Cray ruling 3, s253)

## The gap this closes

PLAN-0099 root-caused this repo's hardest intermittent, and its *method* was
cited nowhere durable: a grep for `forced reproduction|reproduce
deterministically|frozen clock|deterministic reproduction` across CLAUDE.md,
lessons, ADRs, conventions, runbooks and skills returned zero matches
(positive control: the same pattern matches inside PLAN-0099 itself, `:38`,
`:58` — measured 2026-08-25). The repo cites 0099 for its coverage ledger
and its store-at-write rule (lessons #0036/#0037, ADR-0038 C3) — never for
how it *attributed* the flake.

## The method — four moves, in 0099's own record

1. **Measure the mechanism directly, at scale.** Not the flaky test — the
   clock under it: 300 s tight loop, 528M samples, 20 backward steps, all
   ≥ 400 ms (`0099:40-42`).
2. **Compute the predicted rate and match it to the observed one.**
   P(flake) ≈ step-rate × exposure-window ≈ 0.9%/execution — matching the
   observed 1-in-3 full-suite failure (`0099:43-47`). A mechanism whose
   arithmetic reproduces the observed rate is attribution; a hunch that
   survives N reruns is not.
3. **Rule out alternatives by construction, not by sampling.** Postgres
   `now()` excluded by showing no `server_default` exists on any timestamp
   column — a structural fact, worth infinite reruns (`0099:48-55`).
4. **Force deterministic reproduction.** Three ways — exact tie, −5 ms
   inversion, frozen clock through the real HTTP path (`0099:56-60`). A
   defect you can summon on demand needs no statistics at all.

Where 0099 compared with/without a change, it ran **once per side** and
concluded by reasoning over the mechanism (`0099:61-68` — the `<`
experiment). That is the point: repetition was never what carried the
conclusion.

## The distinction, stated once

**Repeat-sampling establishes a RATE** — how often, with what variance;
indispensable when the rate itself is the claim. **Measuring the mechanism
and forcing deterministic reproduction establishes a CAUSE.** A rule of the
form "n ≥ 2 observations on both sides" (considered and cut in PLAN-0115)
would tax every comparison with repetition while buying no attribution —
the repo's best-attributed defect used n=1 per side.

## Adjacent tally — recorded, not promoted (ADR-0038 D1.5 discipline)

The cost-estimation class ("a pre-run estimate missed by ≥ 4×, root cause
knowable in advance") stands at **two** distinct firings:
`docs/logs/2026-07-05-plan0051-live-ab-results.md:40` (~4×, ~2 h vs ~30 min,
root-caused to per-call latency) and s253's ~10× miss on the probe-battery
session (session-attributed). Two < three: no rule is minted; this tally
exists so the third firing can promote without archaeology.

## W-1's tally — CROSSED THREE and promoted (the s254 binding condition)

Recorded here because Cray's s254 ruling on PLAN-0115 SD-4 requires this
tally to live in a **tracked file**, not in a PR body: a promotion
obligation recorded somewhere `git grep` cannot reach is a debt with no
invoice. The canonical record is **ADR-0038 D2-C6**; this is the pointer
that makes it findable from the lesson surface.

**W-1 — "a probe's RED must name what broke"** (#0043) reached **three**
distinct firings and **promoted → ADR-0038 C6** (amendment pass 2026-08-25,
s254):

1. **s231** — a probe reddening as `RuntimeError: no running event loop`
   before reaching its assertion, recorded as passing evidence
   (`docs/lessons/0043-a-probes-red-must-name-what-broke.md:24-49`).
2. **s231** — the FK-children set comparison whose RED truncated both sides
   to the same string: assertion correct, output unusable (`0043:52-75`).
   Carried census-attributed on the watch-list; verified at source in the
   s254 amendment pass.
3. **s253** — a `/tmp` battery driver keyed on `returncode == 0` with output
   discarded, crediting an `AttributeError` and a pre-assert `KeyError` as
   WITNESSED; published 13/13, corrected in-PR.

Note the shape of firing 2, because it is what widened C6's predicate: the
assertion fired **correctly at its own site** and crediting it was right —
the defect was output no reader could act on. A crediting-only predicate
counts two and never triggers. Hence C6's second conjunct (legibility) is
arithmetically load-bearing, not a garnish.
