# Lesson #0027 — Verification is hygiene, not a verdict: REFUTE the claim, don't INDICT the decision

**Date:** 2026-06-26 (session 79)
**Class:** advisory (cross-tier decision/verification discipline)
**Trigger:** Cray's s79 "Interesting Context" on decision quality — decisions are
**time-local optimal** (best given what was known then), **path-dependent** ("this
choice was possible because of the previous"), and **adding a check ≠ the first
choice was wrong." The binding one-liner landed as CLAUDE.md §6 "Verification is
hygiene, not a verdict" (PR
[#438](https://github.com/CrayJThiemsert/vero-lite/pull/438), commit `709a947`).
This lesson carries the rationale the binding rule is deliberately too short to
hold — and the one worked distinction that keeps the rule from being abused.

## The lesson

The §6 rule frees a **passing, evidence-backed re-check** from blame-framing
(`confirmed — prior intact`) so a routine verification stops *reading as distrust*
of solid prior work. The whole rule rests on one distinction that is easy to state
and easy to abuse:

> **REFUTE a claim. Do not INDICT a decision.**

- A **claim** is a proposition about the world — "nl-08 returns the right answer on
  the structured lens", "the merge landed", "the gate denies this Edit". Claims are
  **refuted with fresh evidence, always, no exceptions.** This is unchanged by §6.
- A **decision** is a choice made under bounded information — "we ratified
  `measured_kind` option (b)", "we routed this to Cowork", "we pinned `gpt-oss:20b`".
  A decision was **best given what was known then**; a later re-check that confirms
  it is *hygiene*, and one that supersedes it is *evolution* — neither is a verdict
  that the original was an error.

The blame-relief applies to **decisions only**. Verifying a **claim** stays fully
adversarial.

## Why — the under-scrutiny drift this is built to resist

A verification culture that is deliberately adversarial (the `goal-evaluator`
REFUTES, never blesses — ADR-0018 D3; "a green result against the wrong thing is
worse than a red one" — Lesson #0026) has a real cost: every extra check starts to
*read* as "we don't trust the prior", which erodes confidence in work that is
actually fine and tempts over-correction (rewriting a memory whose reasoning was
sound for its moment). §6 removes that blame-framing — but a blame-relief rule, if
loosened, becomes an **under-scrutiny excuse**: *"it's just hygiene, the prior is
fine, skip it."* That was Cray's stated #1 concern, and the rule is worded to make
it structurally hard:

- The label `confirmed — prior intact` is **double-gated** — it requires *both* a
  pass/fail criterion fixed **before** the run (Lesson #0026) **and** a fresh
  on-disk artifact. You cannot write it from memory; no artifact ⇒ no label.
- Absent evidence is **`INSUFFICIENT-EVIDENCE`, not a pass** (the ADR-0018 D3
  verdict, reused verbatim).
- The rule governs the **label on a finished check**, never the **decision to run
  one** (the §6 tripwire). Using it as a reason *not to check* is misuse by
  definition.

## The most abusable seam — claim relabelled as decision (worked example)

The one residual hinge (flagged by Cowork's adversarial read): because blame-relief
attaches to a *decision* and a *claim* stays adversarial, an agent under pressure
could **relabel an unverified claim as a settled decision** to borrow the hygiene
framing and dodge refutation. Hold the line with a concrete pair:

- **CLAIM — stays adversarial.** "The structured lens still answers nl-08/nl-11
  correctly." This is a proposition about current behaviour. It is **not** settled
  by "we decided this works in session 62"; it is settled by **re-running and
  reading the fresh artifact** (and if you did not re-run, the honest verdict is
  `INSUFFICIENT-EVIDENCE`, not `confirmed`). You may not launder it into "a prior
  decision" to skip the run.
- **DECISION — blame-relieved + weigh reversal cost.** "We ratified
  `measured_kind` option (b)" (ADR-0021). Reopening it is legitimate, but the
  default framing is *"(b) was best given what we knew at ratification"*, not *"(b)
  was a mistake"* — and the real cost of reversing is **everything built on it**
  (PR #329's enum + bindings, the NL-query closure #332), not just editing one ADR.
  That is the **path-dependency** principle: a choice is the accumulation of the
  choices that made it reachable.

Test to apply at the seam: *"Am I asserting something about the world right now
(claim → verify it) or treating a past choice as settled (decision → weigh
reversal cost)?"* If you are using "it's a settled decision" to avoid producing
evidence, you have crossed from decision into claim and the blame-relief does not
apply.

## How to apply

- **A passing re-check →** record `confirmed — prior intact`, not "the prior was
  unverified/risky until now." A re-verify is hygiene; it strengthens, it does not
  accuse. (Distinguish from `superseded by new info` and `was an error` below.)
- **A recalled artifact that no longer matches current code →** classify it:
  `superseded by new info` (evolution — update the pointer, **keep the reasoning
  lineage**) **vs** `was an error` (fix + note *why* it was wrong when written).
  Never flatten both into "stale" — the handling differs.
- **Before reopening a settled decision →** name what depends on it (reversal-cost
  / blast radius), and default to "best given what was known then" unless new
  evidence genuinely supersedes it.
- **Never** let the hygiene framing shorten, soften, or skip a check, or stand in
  for a claim you did not verify. The label is earned by evidence, not asserted.

## Why a lesson (not just the §6 rule)

The binding rule belongs in CLAUDE.md and must stay short (ADR-0017 D5: binding
rule → CLAUDE.md short, rationale → a lesson). But the claim↔decision distinction
is subtle in prose and is the rule's one abusable seam — so the *demonstration*
(the worked pair above) lives here, where it can be read at length, rather than
bloating the constitution. This is the same split the project already uses for the
plan-first discipline (Lesson #0026 ↔ §11 pointer).

Related: CLAUDE.md §6 "Verification is hygiene, not a verdict" (the binding rule
this backs) + its §11 pointer; ADR-0018 D3 (the `goal-evaluator`'s refute-not-bless
mandate + the `INSUFFICIENT-EVIDENCE` verdict — the canonical fully-adversarial
*claim* check); [[0026-interpret-before-run-pre-commit-outcome-meaning]] (pre-commit
what each outcome will MEAN — the pass/fail-before-the-run half of the gate);
[[0025-llm-judge-verdict-must-bind-to-its-own-reasoning]] (sibling — a verdict must
bind to its evidence, the same epistemic spine). Private Tier-0 companion:
`feedback-verify-not-indictment` (the Code-only nudge that landed first).

*AI-assisted (Claude Code, session 79); no `Co-Authored-By` per CLAUDE.md §7.*
