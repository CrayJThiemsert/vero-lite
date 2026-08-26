# `sd-premortem` — four blinded replay runs, and an LLM rollup measured non-reproducible

**Date:** 2026-08-26
**Branch:** `docs/sd-premortem-replay-experiment`, cut from `main` = `f8aeba0`
**Event type:** experiment + measurement. **0 repo writes during the experiment itself**;
no host touched; the working tree was never mutated. Everything ran out of
`git archive` output in a scratch directory.

> **Session-number note.** A parallel session (`vero-lite-53`) was working the PLAN-0114
> line on the *same* worktree at the same time and also identifies as s256. This file
> deliberately omits a session number from its name to avoid asserting a numbering that is
> Cray's convention to set, not this session's. `docs/logs/` already carries eight files
> with no session number, so the shape is precedented.

## Verdict

**The hypothesis is dead as designed — and the autopsy names a better design.**

A read-only subagent, given drafted decision options and a codebase with every trace of the
outcome removed, **reconstructed a real ruling from scratch** — matching all four
control-flow sites the human measurement had named. The *measurement* half works.

The *judgment* half does not. **Run 4 repeated run 3's dispatch byte-for-byte against a
byte-identical tree and returned a different verdict on five of seven options** (§11). An
LLM cannot own the ALIVE / DEAD / NEEDS-EXECUTION rollup.

What survives is a three-layer split the four runs measured directly:

| layer | reproducible? | who should own it |
|---|---|---|
| **citations** — which line does what | ✅ stable in every run | the LLM; it is reliable here |
| **counts** | ⚠️ stable *only* if the match pattern is pinned | pin the pattern, or let a tool count |
| **rollup** — ALIVE / DEAD / NEEDS-EXECUTION | ❌ 5 of 7 differed on an identical prompt | **deterministic code, never the model** |

**Do not open a PLAN for `sd-premortem` as originally designed.** The buildable thing is
smaller: an agent that emits claims plus evidence, and code that computes the verdict.

---

## 1. What was being tested

Whether a `sd-premortem` agent is worth building: a subagent that measures each drafted
option of a Surfaced Decision against the live tree **before** Cray is asked to rule, so
that options which are already dead never reach the decision table.

The motivating evidence, measured over 2026-08-19 → 08-26 (base `origin/main`, see §7):

| | |
|---|---|
| commits | **71** (70 via PR) |
| by type | **52 docs · 13 feat · 2 test · 2 chore · 1 fix** |
| governance share | **73.2%** |
| ratio docs : feat | **4.0 : 1** |

and two specific incidents: PLAN-0115 SD-2, where **both drafted options died on
measurement** *after* dispatch and the ruling became a third thing neither draft proposed;
and PLAN-0114, which needed **three measured corrections before Step 1 was written**.

## 2. Method — the blinding, and why it was necessary

The replay surface is `git archive ce7c003` — the commit **before** `db98126`, which is the
squash that first landed PLAN-0115 *and already carried its rulings*. There is **no
committed version of the plan with unruled SDs**: `db98126` has a single parent, so the
pre-ruling draft is buried by the squash. The option text was therefore reconstructed by
hand from the retained record, stripped of every outcome line.

**This was the step that nearly voided the experiment.** `done/0115` keeps the options as a
record — directly beneath the line `Both fail on measurement`. Handing the agent that file
would have let it read the answer and report a clean PASS that measured nothing. The same
shape as lessons #0044 / #0045.

The mitigation is not the instruction (instructions are probabilistic) but a **separate
scored assertion**: every verdict must carry a `path:line` citation, and a citation outside
the replay root voids the report.

Replay surface contents, verified: `.claude/hooks/`, `.claude/settings.json`, `tests/`
(399 files), one archived plan. Leak greps for `0115`, `probe_battery`, `battery lock`,
`drop_all_bounded` all returned **0 files**.

## 3. Run 1 — pre-committed read, and the grade

Criteria fixed **before** dispatch:

| id | assertion | result | grade |
|---|---|---|---|
| P1 | SD-2(a) → `DEAD`/`NEEDS-EXECUTION` + citation | `NEEDS-EXECUTION` | ✅ PASS |
| P2 | SD-2(b) → `DEAD`/`NEEDS-EXECUTION` + citation | `DEAD as written` | ✅ PASS |
| P3 | SD-1(b) → `ALIVE` (positive control) | `NEEDS-EXECUTION` | ❌ **FAIL** |
| P4 | 0 citations outside the replay root | 34, all rooted | ✅ PASS |

**3 of 4.**

**P2 is the headline.** The agent independently found what the s254 measurement found:

| s254, measured by Cray + Code | run 1, blinded |
|---|---|
| `_last_decision_evaluation` filters only on `GATE_WARN_MARKER` — `_goal_gate.py:405-407` | `_goal_gate.py:406` |
| `work_changed` compares the wrong fingerprint — `:583` | `:583` |
| step-6 unanswered-dispatch check hidden — `:600` | `:600` |
| `_last_was_enforce_block` → a second block — `:411-419` | `:418` |

**4 of 4 sites.** It also produced two findings the s254 record does not contain: that no
lock primitive exists in the surface at all, so both SD-2 options are premortems on a
mechanism not yet in the tree (lesson #0041's shape, found unprompted); and that
`stand down` scopes to the gate, not the Stop hook.

That second finding was checked against the shipped tree and **holds**:
`stop_continuation.py:531` → a `None` gate return falls through to `:540 _classify(payload)`,
so the classifier still runs. The comment at `:530` records this as by design for `None`
generally; nothing records that the battery-lock case was considered specifically. Logged as
a question, not a defect.

## 4. Two defects found in the instrument — both authored by this session

**Defect A — the positive control was mis-chosen.** P3 equated *"the option Cray picked"*
with `ALIVE`. But the s254 record states SD-1's **effort was corrected from ~36 to 53 sites /
50 files, measured not estimated** — the option carried an unmeasured claim at draft time.
`NEEDS-EXECUTION` was the *correct* answer; the control was wrong.

**Defect B — a required output field was dropped from the design.** The design being tested
specified that `NEEDS-EXECUTION` must arrive **with a runnable probe spec**. The dispatch
did not ask for one. `NEEDS-EXECUTION` therefore cost the agent nothing, which is why it
appeared in **4 of 5** options.

## 5. Run 2 — the repair, and a regression

Repair shipped: every `NEEDS-EXECUTION` must carry `ACTION` / `PASS-FAIL` (fixed before
running) / `COST` (`cheap` | `medium` | `expensive`); if no probe can be written the verdict
is `UNVERIFIABLE-FROM-TREE` instead. The positive control was replaced with SD-3, whose
claims are all read-decidable.

| id | assertion | result | grade |
|---|---|---|---|
| P1′ | SD-2(a) stays `NEEDS-EXECUTION` (regression control) | **`ALIVE`** | ❌ **FAIL** |
| P2′ | SD-2(b) stays `DEAD` (regression control) | **`NEEDS-EXECUTION`** | ❌ **FAIL** |
| P3′ | SD-3 → `ALIVE` (repaired control) | SD-3(b) `ALIVE` | ✅ PASS |
| P4′ | 0 citations outside root | 61, all rooted | ✅ PASS |
| P5′ | every `NEEDS-EXECUTION` carries a probe spec | all 3 complete | ✅ PASS |
| M1 | *(measurement)* `NEEDS-EXECUTION` rate | **3/7 = 43%** (was 80%) | — |

**3 of 5, with both regression controls failing.**

**Repair B worked.** The rate fell 80% → 43%, and the agent used `UNVERIFIABLE-FROM-TREE`
twice where no probe was writable — the exact mechanism intended to stop the free hedge. One
probe it specified was run: `git check-ignore -v .claude/state/goal.json` → exit 0,
`.gitignore:69:.claude/state/`. **PASS**; the claim is verified and there is no live defect.
Cost, as advertised: about two seconds.

## 6. Diagnosis — two variables changed at once

The run-2 dispatch also added an instruction that was **not part of the design**:

> *distinguish a load-bearing claim from one that merely refutes a simplification in how the
> option was worded — a wording defect is not a dead option.*

That instruction caused both regressions, and the evidence is visible in the output:

| claim | run 1 | run 2 |
|---|---|---|
| SD-2(b) C3 (`_last_decision_evaluation`) | load-bearing → **`DEAD`** | same citations, tagged **load-bearing: no**, *"survives once corrected"* |
| SD-2(a) C5 (stderr visibility) | **`NEEDS-EXECUTION`** | *"load-bearing: no for the mechanism, yes for the stated purpose"* → rolled up **`ALIVE`** |

Ground truth decides it: s254 ruled **"neither (a) nor (b) as drafted"**. Cray killed both
**as drafted**. Run 1 matches; run 2 does not.

`vero-lite-53` supplied a same-day counterexample that settles the principle rather than the
tuning: in PLAN-0114, the draft called `view-hero.js` the Tab H surface, while `app.js`
registers **H = Monitor**, **G = Governance Moment**, and `renderActPanel` is unreachable
from the fleet path. A pure wording defect **killed the option** — it became a scope cut. So
the added instruction is wrong as a rule, not merely mis-calibrated.

**The correct next step is v3 = run 1 + the probe-spec requirement only.** No PLAN has been
opened.

`vero-lite-53` supplied a second case worth carrying: PLAN-0114 SD-4, where a premise was
measured false, the decision went back to Cray, and an option previously treated as settled
became live again. **A premortem verdict has a shelf life.** The design has no answer for
that yet.

## 7. A structural limit of the `git archive` replay method

**A git-derived replay tree cannot represent gitignored state.** SD-3's load-bearing claim
*"no local override"* depends on `.claude/settings.local.json`, which `.gitignore:65`
excludes — so it is in no archive at any SHA, and the claim would return a **false**
`NEEDS-EXECUTION`.

Handled by copying the live file in and **marking its provenance**: it is live host state,
not a snapshot. Its shape was verified first — a single `permissions` block, no `hooks`, no
`env` — matching what s254 recorded. The agent restated the caveat unprompted in its report.

Any future use of this method must enumerate the gitignored surfaces a decision depends on
before trusting a verdict about them.

## 8. Contamination ledger — the shared worktree

The experiment ran on a worktree shared with a parallel session working PLAN-0114. STATUS
read `0 open PRs, tree clean`; **it was stale**, and this session took it at face value and
did not run `git status` until late. Two standing rules already cover this and were not
applied: *STATUS `head_commit` lags main by convention* and *re-verify tree-facts before
finalizing*.

| claim | measured on | status |
|---|---|---|
| week statistics | **HEAD = the parallel feature branch** | ❌ **contaminated** |
| replay trees (both runs) | `git archive ce7c003` — object store | ✅ clean, immune by construction |
| `_goal_gate.py` / `stop_continuation.py` finding | working tree; `main` vs `HEAD` **IDENTICAL** | ✅ clean |
| `docs/STATUS.md` reads | `main` vs `HEAD` **IDENTICAL** | ✅ clean |
| `goal.json` gitignore probe | `.gitignore`, unmodified | ✅ clean |
| a `docs/plans/0114-*.md:225-235` quote | working tree, since modified (+12 lines at 217) | ⚠️ accurate when taken, **already stale** |

Corrected figures are the ones in §1: **71 commits, 52 docs / 13 feat**, against
`origin/main`. Reported earlier as 73 / 53 / 14. **The correction moves the numbers and not
the conclusion** — the governance share is 73.2% either way.

**One discrepancy is unexplained and is recorded as such.** The same `git log --since` query,
run twice in one session, returned 72 then 70 lines, and the sets differ: `docs(deploy)`
(`d912891`) is absent from the second, although `merge-base --is-ancestor` confirms it is on
`origin/main`. No explanation is asserted. A hypothesis with prior support — WSL2's wall
clock is non-monotonic, which would make a `--since=<date>` boundary non-deterministic
between runs — is offered as a hypothesis only.

The operational rule this yields: **force the base to `origin/main` for any statistic that
will be written down**, and take the measurement twice.

## 9. Rulings by Cray, typed, recorded at the moment they were made

1. **`NEEDS-EXECUTION` = BLOCKED.** A Surfaced Decision carrying an unmeasured
   load-bearing claim **does not reach Cray at all** until the measurement is performed. An
   `asserted-not-verified` stamp is not an escape hatch. The agent's input contract is
   fail-closed.
2. **Ruling 1 stands** after the 4-of-5 blocking rate was measured and reported. Repair the
   instrument and re-run rather than relaxing the rule.
3. **Record the event and the post-repair re-run, then escalate.** This file is that record.
4. **Run the repeat.** Asked whether to close on the stated limitation or spend one more run
   settling it, Cray chose the run. §11 is what that bought.

## 10. What is left

- **Unmodelled:** premortem verdicts expire when a premise changes (PLAN-0114 SD-4) —
  supplied as a same-day case by the parallel session.
- **Not opened, and should not be:** no PLAN, no ADR, no agent file for `sd-premortem` **as
  designed**. §11 supersedes the earlier "v3 is the next step" plan.
- **The buildable successor**, if Cray wants it: an agent emitting claims + citations with a
  pinned match pattern, and **code** computing the rollup from those claims. That is a
  different, smaller artifact and still needs a Cowork-drafted PLAN.

## 11. Run 4 — the same dispatch twice, and the result that ends the design

Runs 1–3 each carried a different dispatch, so none of their disagreements could be
attributed: instruction or model variance were indistinguishable. Run 4 removed that
ambiguity by changing **nothing** — the run-3 prompt byte-for-byte, against a replay tree
re-verified as identical (400 files, all four leak greps 0).

Pre-committed before dispatch: *if any of the three tracked verdicts differs from run 3,
variance dominates and the model cannot own the rollup.*

| option | run 3 | run 4 | |
|---|---|---|---|
| SD-3(a) | **DEAD** | **ALIVE** | ✗ |
| SD-3(b) | NEEDS-EXECUTION | **ALIVE** | ✗ |
| SD-2(a) | NEEDS-EXECUTION | NEEDS-EXECUTION | ✓ |
| SD-2(b) | **ALIVE** | **NEEDS-EXECUTION** | ✗ |
| SD-1(a) | NEEDS-EXECUTION | **ALIVE** | ✗ |
| SD-1(b) | NEEDS-EXECUTION | **ALIVE** | ✗ |
| SD-1(c) | NEEDS-EXECUTION | NEEDS-EXECUTION | ✓ |
| **tally** | ALIVE 1 · DEAD 1 · NE 5 | **ALIVE 4 · DEAD 0 · NE 3** | **5 of 7 differ** |

**The sharpest single case is SD-3(a).** Both runs derived the *same arithmetic* — the work
sitting outside the check budget is Ollama 75 s (`_sonnet_classifier.py:93`) + git 2×10 s
(`_goal_gate.py:199`) + Telegram 5 s (`:105`) ≈ 100 s, so a 179 s budget still totals ≈ 279 s
against a 180 s Stop timeout. Run 3 called that a refutation and returned **DEAD**. Run 4
called it *"MEASURED CONSEQUENCE (not a refutation)"* and returned **ALIVE**. Identical
evidence, identical numbers, opposite verdicts. Nothing was measured differently; the two
runs disagreed about whether the claim was load-bearing.

**A middle layer this session had missed.** Run 3 reported the migration surface as 64
occurrences / 53 files; run 4 reported 54 / 51. Neither is wrong — measured here directly,
bare `drop_all` gives **64 / 53** and `run_sync(Base.metadata.drop_all)` gives **54 / 51**.
**No run stated which pattern it used.** A count therefore looks like the same fact across
runs while silently answering a different question — worse than an unstable number, because
it does not announce itself. This is why the table in §Verdict has three rows, not two; the
earlier reading of this experiment ("claims stable, rollup unstable") was half right.

**What this costs and what it buys.** It cost one dispatch, roughly eight minutes, and no
repo writes. It bought the difference between *"the rollup might be prompt-tunable"* and
*"the rollup is not reproducible"* — which are different products. Runs 1–3 could not
distinguish them; only re-running an unchanged prompt could.
