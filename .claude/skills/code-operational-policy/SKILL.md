---
name: code-operational-policy
description: Tier 2 (Code) tactical operating policy for vero-lite — when to turn git worktree mode ON vs OFF, how to render a transcript handoff to Chat/Cowork, the dispatch-quality discipline (Frontier + oracle-scoped accelerator + REJECT-if blocks, the 4-move follow-up vocabulary, the pre-close counterexample step), and the plan-first discipline for costly / host-state / irreversible / multi-step execution (read the result-producing code first, stage a plan, pre-commit the pass/fail read, run once, verify; + the Axis-B /goal habit for verification tasks). Also carries the instrument-vs-subject test for when a check and a claim disagree, and the pre-committed assertion battery for any two-file move (rotation / archive append / rehome). Use when deciding worktree isolation, handing off a transcript, authoring a Cowork / plan-drafter / subagent dispatch, following up on a subagent's partial return, closing an acceptance criterion, judging a ruff/lint gate, interpreting test failures in a Windows worktree, planning a host-state run / live benchmark / multi-step verification, OR whenever a guard/test/assertion fails and you are about to decide whether the check or the artifact is wrong, or about to move content between two files. Other tiers do not need this.
---

# Tier 2 (Code) operational policy

Tactical policy specific to Tier 2 (Code) execution. This is procedure, not a
constitutional rule — it loads on demand. The constitutional pointer lives in
`CLAUDE.md` §11.

## Worktree mode

Default policy per Lesson #3:

| Scenario | Worktree | Rationale |
|----------|----------|-----------|
| Single-task work (ADR draft, doc edit, single commit) | **OFF** | Avoid Family B traps (sandbox ownership cascade); zero isolation benefit |
| Parallel work (multiple branches in flight, risky refactor) | **ON** | Isolation worth the lifecycle cost; apply Lesson #3 prevention checklist |
| Buildable code that should fail-isolated in CI | **ON** | PR boundary clarity; explicit pre-flight required |

Apply the [Lesson #3 prevention checklist](../../../docs/lessons/0003-code-tab-worktree-lifecycle-traps.md#prevention-checklist)
before any worktree-on session.

⚠️ **A Windows worktree has a non-zero environmental-RED floor** — `pytest
tests/` there fails a handful of tests for pure environment reasons, and the
count **drifts upward as new tests land** (it went 6 → 7 without anyone being
wrong). Never carry a remembered count forward; attribute REDs **by cause**,
and use a **WSL-native** checkout when you need a true CI-scope gate. Method +
the current cause list:
[Lesson #0042](../../../docs/lessons/0042-a-remembered-baseline-is-not-evidence.md).

## Transcript handoff

When the Code tab judges that a reply or span of work should be handed to Chat
or Cowork for follow-up, render the full raw transcript via
`tools/handoffs/render_transcript.py` into `.claude/handoffs/session-NN/`
(gitignored working note) and **always state the export file path in the reply**.

Procedure + options: [`docs/runbooks/transcript-handoff.md`](../../../docs/runbooks/transcript-handoff.md).

## Dispatch quality — hold the goal, arm the oracle

Discipline for authoring a Cowork / `plan-drafter` / subagent dispatch, and for
the follow-up turns when the return comes back partial. Rationale + provenance
(the 4-prompt conjecture-refutation episode + the s166 two-model analysis):
Lesson #0032. How-to, not binding rules.

### Three blocks a substantive dispatch should carry

1. **§ Frontier — one paragraph, near the top.** State the edge of the known:
   "the furthest solved point is ___; what nobody has cracked is ___." Close it
   with the anti-anchoring sentence, verbatim: **"You are permitted to propose
   that an item in this fact-pack should be ELIMINATED, not automated or
   preserved."** A fact-pack of N manual seams silently anchors a drafter into
   automating all N; the escape hatch must be granted explicitly. (Worked
   precedent: the s164 scaffolder dispatch's "the seam no longer exists — do
   not design around it".)
2. **Accelerator clause — scoped by oracle strength.** Over the parts covered
   by a strong offline oracle (tests + mypy + the offline gate): "Attempt the
   structurally bold solution first; the suite is the safety net." Models
   default to hedged, incremental designs; this is the explicit override — and
   it is ONLY safe where a wrong bold attempt is caught free. Never attach it
   to weak-oracle parts (strategy, prose, governance judgment): ambition
   without an oracle buys confident wrongness.
3. **REJECT-if list — inside the return contract.** "The caller will REJECT
   the return if: …" + the fake-done forms named for THIS task. Standing
   entries: an AC satisfied by mocking the thing under test · TODO / `pass`
   stubs in delivered code · a check that passes because it was skipped · a
   "works in principle" claim with no `file:line` grounding. Naming the forms
   up front moves the catch from the caller's R2 into the drafter's self-check
   — one round-trip cheaper.

### The 4-move follow-up vocabulary (the return came back partial)

Invariant: **the goal stays constant; only process pressure rises.** Silently
accepting a narrower result IS renegotiating the goal — if the goal genuinely
changed, that is a typed Cray ratification (`/goal amend`), never drift.

- **M1 — the dispatch itself**: goal + ceiling + shape + Frontier (above).
- **M2 — reject by name**: restate the goal VERBATIM, then name the partial
  form returned — "this is a conditional result; the goal is an unconditional
  X." Named rejection beats "please improve".
- **M3 — strategy before retry**: "State the structural reason the last
  attempt failed, and derive the new strategy from it. Do not re-run a variant
  of the same approach." (Deliberately a conversational move, NOT a hook — a
  hook can only verify a strategy paragraph EXISTS, which invites ritual
  compliance.)
- **M4 — terminate the partial ratchet**: "Enough partial results — finish
  complete, or declare blocked and name the specific blocker." A human call
  made with full context; deliberately NOT a counter or detector.

### The counterexample step — before closing an AC

Before marking an AC done, spend one line testing the ORACLE, not the code:
"Construct a test that passes today AND would still pass if <the AC's
behavior> were silently broken." A mutation counts only if it changes behavior
the AC claims to protect — comments, formatting, and dead code do not. If such
a test is constructible, the AC's oracle is vacuous: fix the test before
closing. Same family as the non-vacuity probe — you must SEE the RED.

⚠️ **And then READ it.** Seeing the RED proves the guard is live; it does not
prove the failure names what broke. Two guards in consecutive PRs reddened
correctly and illegibly — one crashed on `RuntimeError: no running event loop`
before reaching its own assertion, the other printed
`{'repair_case...e_task_event'}` on **both** sides of a truncated set comparison.
A guard whose RED nobody can act on is deleted by the next person who trips it.
The two smells, the fix, and why the fix must carry its reason in the docstring:
[`Lesson #0043`](../../../docs/lessons/0043-a-probes-red-must-name-what-broke.md).

## Plan-first for costly / host-state / irreversible / multi-step work

For a task that is **host-state** (warm/run a model on MS-S1, touch global
config — ASK Cray first, CLAUDE.md §8), **irreversible / outward-facing** (a
live run that burns a one-shot authorization, a push/merge), **costly** (a long
benchmark, a paid API run), or **multi-step** (≥ ~3 dependent stages), do NOT
execute blind. Trivial, reversible, single-step work — just do it; this does not
apply. The discipline keeps the run trustworthy *and* cheap (it avoids wasted
host-state runs and false reads):

1. **Read the code that PRODUCES the result before you run it.** For an
   eval/benchmark/verification, read the harness + the scoring + the engine path
   the run exercises. You must be able to say, *before* the run, what each
   outcome will MEAN — pass / known-acceptable-miss (out of scope) / real failure
   — or you cannot tell a regression from noise afterward. This is the
   single highest-leverage step (interpret-before-run, Lesson #0026): it prevents
   both false alarms (an out-of-scope miss read as a regression) and false
   confidence (a lucky or off-route pass read as a validation).
2. **State a staged plan + pre-commit the pass/fail read.** A short stage table
   (cheapest checks first, host-state/irreversible last) + the explicit
   acceptance criteria you will judge against. Checkpoint here if the work is
   governance- or host-state-gated; otherwise proceed.
3. **Run the cheapest gate first.** Offline / mocked gate before any host-state
   or paid run — if the offline gate is red, never spend the live run.
4. **Run once.** Minimize host-state / paid runs (the ASK-Cray host-state gate).
   No iterating on the live target.
5. **Verify with the right tool, against the pre-committed criteria.** Read the
   evidence artifact with the **Read tool** (never piped `cat`/`wc` — it silently
   misreports; verify-relayed / verify-pin lessons). Judge against step 2's
   criteria and report misses honestly: out-of-scope/known vs regression.

### 🔴 When a check and a claim disagree — the instrument-vs-subject test

Measured s241, five times in one session, and **the armchair answer was wrong in
BOTH directions**: three times the check was right and the claim wrong, twice the
opposite. Nothing but reading the artifact separated them, so do not decide by
which is cheaper to change.

Read the flagged line itself — not a summary of it — then ask in order:

1. **Is the check reporting a real property of the artifact?** A new guard
   blocked its own first commit; the guard was right and its *rules* were the
   defect (a file exempted from *declaring* could not exempt its own examples
   either).
2. **If the check is right, does the fix change the artifact or the rule?**
   ⚠️ **Narrowing a matcher until it stops matching is editing the artifact to
   satisfy the instrument.** Legitimate only when the reach was wrong on its own
   terms — never because the report was inconvenient.
3. **If the check is wrong, is it wrong about the artifact or about itself?**
   Three failed assertions in one session were wrong about *themselves* — a
   comment counted as data, a case-sensitive needle, a needle straddling `**`
   emphasis. Fix the needle; changing the file to match a bad needle is step 2's
   error in disguise.

**Pre-commit the assertion; do not verify after.** All three self-inflicted
misfires above cost nothing because the assertion ran **before** the write. The
one incident caught only afterwards had already put a false claim into a tracked
file. For any two-file move (a rotation, an archive append, a rehome):

> pin each slice by its expected **first AND last** text · assert no
> neighbour-bleed · assert it is not already in the target · then check
> **presence-in-target and absence-from-source SEPARATELY** — never infer one
> from the other.

That battery aborted a rotation this session with **both files untouched**.

⚠️ **A subagent's report is a claim about the tree, not the tree.** One reported
removing two notes that were still there; an archive note written from that
report asserted something false. Diff or grep the artifact before repeating what
a report says it did.

Full incident set:
[`docs/lessons/0046-when-a-check-and-a-claim-disagree-go-to-the-artifact.md`](../../../docs/lessons/0046-when-a-check-and-a-claim-disagree-go-to-the-artifact.md).
For the aggregate-before-synthesis half, see the `fan-out-dispatch` skill.

#### The prior depends on the instrument's age — and it is not 50/50

s241's "wrong in both directions" was measured on **shipped guards** that had been
running against the repo. s269 measured a different population: **instruments written
minutes earlier for this one check** — a byte-delta criterion, a verification regex,
two merge-verification tokens, a positive control. There the score was **7 disagreements,
7 times the instrument was wrong, 0 times the artifact.**

> **A guard that has been running is a real hypothesis. A script you just wrote is a
> draft.** Read the artifact either way, but when the instrument is fresh, read *it*
> first — you will usually be reading your own bug.

#### Two mechanics that make the disagreement cheap (or prevent it)

**1 — an instrument passes a control on known content before you trust its first
reading.** The silent failures are the expensive ones: an uncontrolled instrument does
not fail loudly, it fails *confidently*. s269's regex reported one number in a
description that holds three (a trailing lookahead rejected any number ending a
sentence) and that figure was on its way into an acceptance criterion. The repair opens
with the control:

```python
FIXTURE = "Clean bags sit around 0.6. By 2.4 the fan stalls; back at 1.0. 240 sites."
EXPECT  = ["0.6", "2.4", "1.0", "240"]
if NUM.findall(FIXTURE) != EXPECT:
    raise SystemExit("instrument failed its own control - no figure below is trustworthy")
```

A control pays twice: it catches your bug, **and** it makes a later agreement with an
independent figure mean something. Once controlled, that regex reproduced a prior
session's `4 of 8` exactly — which is what established the *earlier* instrument had
been right all along.

**2 — print the values, never a bare verdict.** Every s269 disagreement was diagnosed
in one follow-up probe because the report already showed the number:

```
[A5] the ledger IOU is gone (both ledgers): pre=2 post=2 -> FAIL
```

`pre=2` *is* the diagnosis — the phrase was in a retained neighbour the runbook forbids
rewriting. A bare `FAIL` starts a hunt. **A verification report that prints only
PASS/FAIL is withholding the evidence it just collected.**

⚠️ **Also from s269 — count the variety before coding against one instance.** Two of the
seven were a single example generalised to a set (one ledger rotation read as the
pattern for all; one injection case read as the shape of a three-shape band). Such code
works *perfectly* on the example you read. `grep -c` the field and list its distinct
values before writing the branch.

Full incident set + the four-class taxonomy:
[`docs/lessons/0056-suspect-the-instrument-before-the-artifact.md`](../../../docs/lessons/0056-suspect-the-instrument-before-the-artifact.md).


### Judge a lint gate on the tracked tree, not on your checkout

`ruff` is a **gate**, so the thing under judgement must be the tree CI will see.
Your checkout is not that tree. Extract HEAD and run the gate inside it:

```bash
rm -rf /tmp/gatetree && mkdir -p /tmp/gatetree
git archive HEAD | tar -x -C /tmp/gatetree
cd /tmp/gatetree && ruff check .
```

Two independent reasons a bare `ruff check .` in your checkout misreports —
**both measured in the main checkout at `71b8f6b`, session 230**, where it
found 2 errors while the extracted HEAD tree (1027 files) was `All checks
passed!`:

- **Untracked files get linted.** `.claude/benchmark-results/` is untracked but
  present, and contributed an `S108` that **is not in the repo**.
- **Uncommitted work gets linted — including someone else's.** The second error
  (`E501`) came from an in-flight edit belonging to a *concurrent session* on
  another branch. Neither error was attributable to HEAD, and neither would
  appear in CI.

⚠️ **You cannot fix this by naming paths instead.** `ruff check <paths>`
*bypasses* `exclude`, so narrowing the argument silently changes which rules
apply and diverges from CI, which runs a bare `ruff check .`. Extracting the
tree is what makes a bare, `exclude`-faithful invocation possible.

### Use the Axis-B `/goal` loop for verification tasks

When the task has explicit acceptance criteria (a verification, a multi-criteria
eval, an AC-N re-verify), declare them up front with **`/goal`** (writes
`.claude/state/goal.json`; ADR-0018 / PLAN-0021). The Stop-hook goal gate then
checks every turn and can dispatch the `goal-evaluator` to adversarially
**REFUTE** — not bless — each `judge` criterion from on-disk evidence. This moves
step 2's pass/fail read from post-hoc prose into machinery and adds a skeptical
second perspective for free. Warn-only v1 (never blocks) → pure upside.

## CI does not type-check `tools/` or `benchmarks/`

`.github/workflows` runs `mypy --strict services/ verticals/`. Those two trees are
the whole scope. **`tools/`, `benchmarks/` and `tests/` are never type-checked by
CI**, and the pre-commit mypy hook skips them too — so a green PR says nothing
about them.

Measured session 262, twice in one session and in two different trees: a decorator
that had silently stopped satisfying the Protocol it wraps (after the Protocol was
widened in an earlier PR, with CI green throughout), and two `list[dict]`
type-argument errors in a shipped tool. Both surfaced only because mypy was run at
the package by hand while the file was open for an unrelated reason.

**So: when you touch `tools/` or `benchmarks/`, run it yourself.**

```bash
wsl bash -lc 'cd ~/work/vero-lite && source .venv/bin/activate && mypy --strict <path>'
```

Treat a pre-existing error you find there as in scope for the change you are
already making — a module cannot be kept clean going forward if it starts dirty,
and the next person will not be looking either.

## References

- `CLAUDE.md` §11 (constitutional pointer), §8 (host-state ASK-Cray gate)
- Lesson #3 (worktree lifecycle traps + prevention checklist)
- Lesson #0026 (interpret-before-run: pre-commit what each outcome means)
- Lesson #0032 (ambition scales with the oracle; hold the goal; the two work regimes)
- ADR-0018 / PLAN-0021 (Axis-B `/goal` verification loop); the `goal` skill
- `docs/runbooks/transcript-handoff.md`; the `ms-s1-ollama` skill (host-state mechanics)
