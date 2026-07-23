# Lesson #0032 — Ambition scales with the oracle; exploration is gated, not planned

**Date:** 2026-07-23 (session 166)
**Class:** advisory (dispatch authoring / work-regime discipline)
**Trigger:** Cray shared a reported episode: GPT 5.6 Pro refuting the general
(non-planar) case of the Dinitz–Garg–Goemans single-source-unsplittable-flow
conjecture — open 30+ years — driven by **four short prompts**, with the planar-case
paper attached. Two-model analysis in s166 (Opus 4.8 first pass, Fable 5 adversarial
R2) extracted what transfers into vero-lite's workflow and what must not.

## The episode (as reported; structure verified from the prompts themselves)

The four prompts, paraphrased to their function:

| turn | prompt (compressed) | function |
|------|--------------------|----------|
| 1 | "Construct a counterexample… do a breakthrough… find a **structured** counterexample" + the planar-case paper | goal as a self-verifying OBJECT · refute-direction locked · ceiling set high · answer-shape constrained · context = one frontier artifact |
| 2 | "find a **complete unconditional** counterexample" | the unacceptable done-forms named (partial, conditional) |
| 3 | "Have a **clear strategy obtained from deeper understanding of the problem structure**" | anti-flailing: no retry without a structural diagnosis |
| 4 | "**it's enough of partial results.** let's finish…" | the partial-credit ratchet cut by a human with full context |

Three structural facts matter more than any wording:

1. **Zero domain content in all four prompts.** No graph theory anywhere — every
   sentence is control language (goal, standard, process, termination). The domain
   knowledge travels in the attachment.
2. **The goal at turn 4 is identical to turn 1.** Nothing was renegotiated
   downward; only process pressure rose. The operator held the goal for the model.
3. **The attachment is a near-miss, not a reference pile.** The planar proof is
   the thing that almost closes the question and cannot extend — a counterexample
   hunt starts exactly where that proof leans on planarity. Attaching it hints the
   method without stating the method.

## The lesson — two principles and a reframe

### 1. Ambition scales with the oracle

"You should do a breakthrough" is an explicit override of a model's trained
default (hedge, claim small, stay safe). It was SAFE to write **only because the
oracle was maximal**: a candidate counterexample is checked mechanically, free,
and unarguably. Port the coupling, not the sentence:

- Over strong-oracle work (tests + mypy + the offline gate cover it): write the
  accelerator clause — bold first attempt, the suite is the net.
- Over weak-oracle work (strategy, prose, governance judgment): the same words
  buy **confident wrongness** — nothing slaps the bold-but-wrong attempt down.
- Want more ambition on a weak-oracle task? **Strengthen the oracle first, then
  raise the ceiling** — never the reverse. (CLAUDE.md §8 says the same thing from
  the other side: "the offline oracle is the gate"; a live run is evidence.)

### 2. Two work regimes — the constitution covers one, this names the other

| regime | shape of work | discipline | codified |
|--------|--------------|------------|----------|
| **Execution** | costly / host-state / irreversible / multi-step | **plan-first**: read the result-producing code, stage a plan, pre-commit the pass/fail read, run once, verify | CLAUDE.md §11 · Lesson #0026 |
| **Exploration** | cheap, reversible search — research, design-space sweeps, counterexample hunts | **gate-at-checkpoints**: fix goal + ceiling + named not-done forms up front; let the run go long; review at checkpoints (the 4 moves); NEVER plan the search itself | this lesson |

Applying plan-first to exploration inverts its value: a detailed plan locks the
frame *before* the model has seen the problem's structure — the exact failure the
episode's turn 3 exists to prevent. The regimes also map onto the standing model
economy: exploration under gate-at-checkpoints is where a Fable-tier long deep
run belongs (one deep run + checkpoint reviews beats many shallow ones); plan-first
execution is Opus territory.

### 3. The reframe: copy the control loop, not the prompts

The artifact worth porting is the **operator's decision table** — given a return
of type X, respond with move Y — not any prompt's wording. Operationalized as the
**4-move follow-up vocabulary** (M1 dispatch · M2 reject-by-name · M3
strategy-before-retry · M4 terminate-the-ratchet) in the `code-operational-policy`
skill, alongside the three dispatch blocks (Frontier + anti-anchoring ·
oracle-scoped accelerator · REJECT-if list) and the pre-close counterexample step.

A deliberate scoping decision from the s166 R2, recorded so it is not re-litigated
casually: **M3 and M4 stay conversational — no hook, no detector.** A hook can
only verify that a strategy paragraph EXISTS (ritual compliance); a
partial-ratchet counter mechanizes a judgment that needs full context
(consecutive INSUFFICIENT-EVIDENCE has benign causes). Both are judgment-shaped
calls; per the house rule, a recoverable hazard is not promoted to machinery
until it has actually bitten ~3 times.

## What does NOT transfer

- **Survivorship bias, twice.** We see the one thread that worked, not the dead
  ones; and within the thread, each turn was hours of frontier-model compute
  against a free oracle. Copy structure, never wording-as-magic.
- **Error costs are asymmetric.** A wrong graph costs compute; a wrong merge
  costs downstream rework (the §6 reversal-cost frame). Our accelerator clause
  is therefore *scoped*, never global.
- **The judgment core is untouched.** Which noun is the Asset, whose ฿ ladder,
  what the waiver relaxes — no dispatch wording moves these; they stay human.

## How to apply

At the moment of need, the `code-operational-policy` skill carries the blocks
verbatim (§ "Dispatch quality — hold the goal, arm the oracle"). Adoption is
deliberately Rule-of-Three: **record every catch** — a REJECT-if line that
bounced a fake-done, a Frontier sentence that produced a delete-the-seam design,
a counterexample step that exposed a vacuous AC. At ~3 real catches, promote the
block from skill how-to into the dispatch template / conventions; until then it
stays cheap prose.

> **Tripwire (greppable):** if you are writing "be ambitious" / "do a
> breakthrough" into a dispatch whose oracle is an R2 prose review — **stop**.
> Strengthen the oracle first, or delete the clause. Ambition without an oracle
> is confidence, not quality.

Related: Lesson #0026 (interpret-before-run — the execution regime's spine),
Lesson #0030 (verify the fact-pack before dispatching — what Frontier does NOT
replace: facts must still be true; Frontier stops true facts from becoming a
cage), Lesson #0031 (the dispatcher owns the seam — same caller-side duty, write
axis), ADR-0018 (the goal-evaluator's refute-not-bless mandate — the standing
in-repo instance of the refute direction), `.claude/skills/code-operational-policy/`
(the operational blocks this lesson backs).
