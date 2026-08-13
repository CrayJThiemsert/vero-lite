---
name: decision-lookup
description: Answer "have we already decided this?" before re-deciding, and record a decision CHANGE without erasing the original. Searches every decision-bearing surface in the repo — critically including docs/plans/done/ and docs/status-archive/, where two thirds of the ruling-bearing files live and where ordinary work never looks. Use when about to open a question that feels previously settled, when a PLAN/ADR slot seems to need a ruling that may already exist, when Cray says "เคยตัดสินไปแล้วหรือยัง / เรื่องนี้เคยคุยกันไหม / did we decide this", when writing a Surfaced-decisions slot, or when about to reverse, retire or supersede an earlier ruling. It has NO store of its own — it reads the canonicals.
---

# decision-lookup — has this already been decided?

A task-triggered procedure (Tier 2.6). It owns **no state**: every answer is
computed from the tracked canonicals, so it cannot drift out of sync with them
(ADR-0017 D6 — derived artifacts carry no independent precedence).

It exists because **recording is not retrieval.** vero-lite records decisions
well; what it lacks is a way to *ask* whether something was already settled.

## The measured problem this solves (session 226)

`git grep -l RULED -- docs/` returns **15 files. Ten of them are archives** —
six under `docs/plans/done/`, four under `docs/status-archive/`. STATUS keeps
only the **last ten** Recent-Decisions rows, so every older ruling rotates into
Tier 3 (archeology) by design. Nothing is lost; nothing is *findable* either,
because normal work opens neither directory.

**Therefore: a lookup that does not search the archives answers the wrong
question.** That is the single most important rule in this skill.

## Step 1 — Search, archives included

Run via `wsl bash -lc`, redirecting to a file (never pipe into `head`/`tail` —
the truncator's exit status masks failures, Lesson #0007). Search **all** of
`docs/`, which already includes `plans/done/` and `status-archive/`.

Grounded patterns — measured hit counts, so you know what each buys:

| Tier | Pattern | Hits / files | Use for |
|---|---|---|---|
| **High signal** | `RULED (Cray` | 30 / 6 | Cray's explicit typed rulings |
| High signal | `Cray, typed` | 127 / 30 | the same rulings phrased inline |
| High signal | `ACCEPTED (Cray` · `DECIDED` | 3+7 | acceptances of a residual risk |
| Structural | `LOCKED-` | 451 / 66 | PLAN-level locked premises |
| Broad | `Cray-ratified` | 280 / 74 | widen only if the tight patterns miss |

Prefer the tight patterns first. `ratified` alone is **1343 hits / 163 files** —
too broad to be an answer; use it only to confirm a negative.

⚠️ `git grep` eats a pattern starting with `-`; always use `-e`.

### 🔴 Step 1b — Co-occurrence is NOT aboutness (measured; skip this and the skill lies)

The obvious method — grep the **topic**, then look for `RULED` / `Cray, typed`
on the same lines — **produces false positives**, and a false "already decided"
is far worse than a miss: it closes a question that is genuinely open.

Measured while dog-fooding this skill (s226). Question: *may Code edit files in
`docs/plans/done/`?* — a question asked three sessions running and **never
answered**. Grepping `plans/done` returned **408** hits; several carried
`RULED` / `Cray, typed` on the same line, so the naive method reported
**"FOUND a ruling"**. Every one of those rulings was about something else
entirely — the autonomy fork, PLAN-0088's SD-9, PLAN-0095's draft status. They
merely mentioned the path. **The correct verdict was NOT DECIDED.**

Therefore:

1. **Read the ruling's own sentence**, never its line's co-occurrence. Ask: *is
   this ruling ABOUT my question, or does it just mention the same noun?*
2. **A topic pattern returning hundreds of hits is not a search, it is a
   directory listing.** Narrow it — quote the decision as it would have been
   phrased, not the object it concerns (`"no portal repo"`, not `portal`).
3. **Report the count you had to read.** If you narrowed from 408 to 6, say so;
   it tells the reader how much of the space you actually covered.
4. When the honest answer is *nothing here is about this*, that is a **confident
   negative** and it is the finding — it licenses opening the question.

## Step 2 — Classify each hit into exactly one of four states

This is the step that separates *forgetting* from *legitimately changing your
mind*, which is the whole reason the skill exists.

| State | Markers to look for | What it means |
|---|---|---|
| **DECIDED — live** | a ruling with no later marker pointing at it | Do not re-open. Cite it and proceed. |
| **DECIDED — then superseded** | `superseded by new info` (75 hits / 30 files) · `SUPERSEDED` · `RETIRED` · `CANCELLED` · `DISCHARGED` | The original was **right when made**; circumstances moved. **Keep the lineage** — cite both. |
| **DECIDED — was wrong** | `was an error` (94 hits / 29 files) · `Corrected s<NN>` | Never true. Cite the correction, and the reason it was missed. |
| **NOT decided** | `NOT RULED` · `Cray's call` (103 hits) · an unruled `SD-`/`OQ-` slot | Genuinely open. Surface it; do not assume. |

🔴 **Never flatten the middle two into "stale".** They carry different lessons
and get different handling (CLAUDE.md §6; Lesson #0027). A superseded decision is
the system working; an erroneous one is a defect with a cause worth naming.

## Step 3 — Report

Answer in this shape, briefly:

- **Verdict:** decided-live / decided-superseded / decided-wrong / not-decided.
- **Where:** `file:line` for every hit, and say plainly when a hit is in an
  **archive** — that tells the reader why they had not seen it.
- **When + by whom:** the session stamp (`s2NN`) and whether it was Cray-typed.
- **If not decided:** say so explicitly. A confident negative is a finding, and
  it is what licenses opening the question.

## Step 4 — Changing a decision (the other half — do not skip)

A ruling may absolutely be reversed; Cray's requirements legitimately move. What
must not happen is a **silent overwrite**, because that is indistinguishable
from having forgotten.

Before proposing a reversal:

1. **Weigh the reversal cost, not the edit cost.** Ask what has been *built on
   top of* the decision, not what it costs to change that one paragraph
   (CLAUDE.md §6). A one-line ADR edit can invalidate a shipped PLAN.
2. **Classify honestly:** is this `superseded by new info` (conditions changed —
   the original stays correct in its context) or `was an error` (it was never
   right)? Say which, and why.
3. **Record the supersession as a pointer, never an erasure.** Correct **in
   place** so a reader who stops at the old text is stopped *by* it, and keep the
   original visible in the correction — the house style used throughout this repo
   is an inline `_[Corrected s<NN>, <classification>: <what it used to say and
   why it changed>]_`.
4. **A reversal of a Cray-typed ruling needs a Cray-typed reversal.** Code never
   retires one on inference — a Stop-hook "proceed" is the harness, not Cray.

## Worked example — the two shapes, both measured s226

**DECIDED.** *"Is a portal repo being created?"* → narrow pattern `"no portal repo"`
→ `docs/adr/0035-hosting-and-exposure-model.md:53` and `:848`: *"Cray ruled
(typed, s221): **no portal repo will be created**"*. Verdict **decided-live**,
cited, closed. Note for the reader: 17 of the 68 broader hits sat in archives —
which is why this had been re-asked before.

**NOT DECIDED.** *"May Code edit files in `docs/plans/done/`?"* → 408 raw hits,
several with `RULED` on the same line, **none of them about this question**.
Verdict **not-decided** — and it stays open, asked three sessions running. The
naive method would have closed it wrongly.

## Anti-patterns

- **Reporting "decided" from co-occurrence** — a `RULED` on the same line as your
  topic noun. This is the failure mode that motivated Step 1b; it is the one that
  does real damage, because it closes a live question.
- Searching only `docs/adr/` + `docs/plans/` and reporting "not decided". Two
  thirds of the ruling-bearing files are archives; that answer is unsound.
- Reporting a hit without saying whether anything later supersedes it — a live
  quote of a reversed decision is worse than no answer.
- Treating a gitignored handoff as a home. Handoffs are working notes; if a
  ruling's only hit is in `.claude/handoffs/`, it is **unhomed** — say so and
  rehome it into a tracked artifact (that is the s223 loss and the s226 one-pager
  near-miss).
- Adding a decisions store. This skill reads canonicals **by design**; a second
  copy would drift and become a third place to forget things.

## References

- `CLAUDE.md` §6 ("Verification is hygiene, not a verdict" — the claim-vs-decision
  split, and the reversal-cost rule), §1 (precedence when sources conflict).
- [`docs/lessons/0027-verify-not-indictment-refute-claim-not-decision.md`](../../../docs/lessons/0027-verify-not-indictment-refute-claim-not-decision.md)
  — the worked example.
- [`docs/runbooks/memory-architecture.md`](../../../docs/runbooks/memory-architecture.md)
  — R2/R4 rotation (why rulings reach the archives) and the R2 carve-out (rehome
  before trimming); ADR-0017 D5 knowledge placement.
- `stream-status` (state, not decisions) · `next-work-analyst` (ranking, not
  decisions) — this skill answers a third question and defers to those two.
