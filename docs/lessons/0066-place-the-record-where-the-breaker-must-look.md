# Lesson #0066 — place the record where the breaker must look

**Session:** 316 (2026-09-21), measured against `main` at `bf919c01` · **Status:** advisory
(§1 precedence — promote to ADR if it must bind).
**Class:** the placement half of `CLAUDE.md` §4's routing rule, and a companion to
[#0065](0065-the-tracked-surface-rule-stops-at-gates-the-losses-did-not.md) — where #0065
measured what a **missing** tracked surface costs, this one measures that *tracked* is not
the property that matters. **Supervised by something the breaker must run** is.

---

## The test

> **Name the person who would make this sentence false. Then check whether they are forced
> to see it.**

A record they will not encounter is not a record; it is a hope. The question is never "did
we write it down" — it is "whose hands are on the thing this describes, and does the
sentence sit in their path".

## The measurement

`tag --reflow` shipped in PLAN-0128 Step 3 with a complete battery. Asking *"is this flag
recorded?"* of five surfaces gives five different answers — and only one of them is
supervised.

| Surface | Names the flag? | Who breaks it | Forced to see it? |
|---|:-:|---|---|
| The refusal message, `tools/probe_battery/_tag.py:358` | ✅ | anyone editing that string | 🟢 **yes** — *The one that is supervised, and why* |
| CLI `--help`, `tools/probe_battery/__main__.py:204` | ✅ | anyone editing the parser | 🔴 no — prose, no guard |
| `tests/batteries/README.md:30,57` | ✅ | anyone editing that README | 🔴 no — prose, no guard |
| `tools/probe_battery/README.md` | ❌ **0 hits before this change** | — | 🔴 the gap this session closed |
| `docs/plans/done/0128-*.md` (106,521 B) | ✅ | anyone | 🔴 **never, by design** |

Three of those readings are worth their own line.

### The one that is supervised, and why

Probe **`P5-a-vanished-anchor-is-not-reported`** in
`tests/batteries/s288-battery-definition-lint.json` witnesses the claim
`test_an_anchor_that_no_longer_resolves_is_found|"occurs 0 times" in details|#0`. Probe
**R6** in `tests/batteries/plan-0128-pr3-tag-reflow.json` anchors on the literal text
`Re-run with --reflow to let` inside `_tag.py`, and witnesses
`test_without_reflow_the_refusal_warns_against_exploding_by_hand|"--reflow" in printed|#0`.

`check_battery_definitions.py` runs **`always_run: true`** at pre-commit, and its config
comment states the reason outright: *"both deaths were authored by editing the code a
battery points AT, never the battery file."* So rewording that refusal strands R6's anchor
and the commit reddens.

And R6 is not alone. **All fourteen** of that battery's probes anchor inside `_tag.py`, and
three of them sit on refusal *prose* rather than on control flow: R6 on
`Re-run with --reflow to let` (`:358`), **R7** on
`refuses every one of them as an unaddressable key.` (`:361`), and **R10** on
`clean already, so that any formatting change afterwards is ` (`:367`) — a substring of the
*second*, format-clean refusal. Reword any of the three and the same `always_run` lint
reddens. **Those three anchors are the supervised copies; the other surfaces listed under
*The measurement* are not.**

> ⚠️ This section first closed with *"That is the **only** `--reflow` sentence in the repo
> that cannot rot quietly."* It was refuted by the battery this section cites — R10
> alone disproves it. A uniqueness claim is a negative claim wearing a positive sentence,
> and *A claim about where a record lives is still a claim* applies to it in full.
> The correction is kept here rather than smoothed away, because *what* was wrong is the
> point.

### The one that is unsupervised forever

`tools/check_ac_consistency.py:383-384` is explicit:

> `"""Active PLANs only — ``docs/plans/*.md``, never ``done/``."""`

Archiving a PLAN ends its mechanical supervision. A sentence written into an archived PLAN
is beyond every guard's reach from the moment the `git mv` lands — which makes an archived
PLAN the **worst** available home for anything that must stay true, and a perfectly good
home for the reasoning lineage that only has to stay *readable*.

### The surface that is silent about its own silence

`tools/README.md` says what the whole pre-commit group does not do, and quotes
`check_ac_consistency.py`'s docstring for the sharpest form of it:

> Every one of these verifies a *lexical shape* [...] **None opens a cited target and asks
> whether the sentence about it is true.**
>
> — *"They compare two statements of the same fact; **a wrong fact stated consistently
> passes.**"*

Measured this session: **twelve** pre-commit hooks invoke a `tools/` script, and **not one
of the thirteen `tools/` paths named in `.pre-commit-config.yaml` reads a README** — all
thirteen return 0, against a positive control (`tools/README.md` itself) returning 1.

⚠️ **That denominator took three instruments to get right, and the third one is the
lesson.** The first cut used `grep -rln README tools/*.py`, which cannot see
`tools/handoffs/` or `tools/vero_bridge/`. The second, `grep -o 'tools/[^ ]*\.py'` over
`.pre-commit-config.yaml`, returned **fourteen** — because `tests/tools/test_guards_hold_on_the_real_tree.py`,
named in a *comment* at L97, contains `tools/` as a substring. Anchoring the pattern to a
word boundary does **not** separate them: `tests/tools/` has a word boundary before `tools`
too. What separated them was asking the filesystem — and the same loop had been running
`grep -c README` against that phantom path and **scoring its 0 alongside the real ones**. A
negative reading taken over a set you have not confirmed exists is not a weak reading; it
is a vacuous one, and it reports success in the same voice as a real one.

Several of these guards do read prose files — `check_status_citations.py`,
`check_plan_archive_refs.py` and `check_measure_staleness.py` all run over `docs/`. What
none of them checks is whether a *sentence* is true; each verifies a lexical shape, a
resolvable path, or two artifacts agreeing with each other. That is not an argument against
prose — it is the reason prose must never be the *only* home for something load-bearing.

## The corollary that saved work this session

Before building a proof that "editing the refusal trips a guard", the catalogue was
checked — and **P5 already witnessed it**, at s288, with 17 probes. A hand-rolled re-proof
would have been one more instrument wrong about something the artifact had right.

> **Before building an instrument, ask what already witnesses this.** `tools/README.md`
> exists for exactly that question: *"listed so you don't rebuild one."*

## A claim about where a record lives is still a claim

The s315 closing handoff recorded that `--reflow`'s format-clean precondition was
*"Recorded ONLY here"* — meaning the gitignored handoff itself. Re-derived this session, it
has **four** tracked homes: `_tag.py:367` (the refusal text), `__main__.py:209` (the CLI
help), `tests/batteries/plan-0128-pr3-tag-reflow.json:86` (a probe's `why`), and
`tests/tools/test_probe_battery_tag_reflow.py:91` (a test docstring). The handoff was
written from memory about what was tracked, and a "this exists nowhere else" line is a
**negative claim** — the shape `CLAUDE.md` §6 already singles out for the strictest
re-measurement. Classify: `was an error`, not `superseded`.

## The same rule, applied to a consumer that is not a human

The Axis-B goal gate reads a `check` criterion's `cmd` and runs it **argv-without-shell,
from the Windows side, with `cwd=REPO_ROOT`** (`.claude/hooks/_goal_gate.py:404-447`, the
`cwd=str(REPO_ROOT)` at `:433`). A goal declared this session with `.venv/bin/python` and
`/usr/bin/test` in its commands scored **`error` on four of five criteria** — not `fail`:
the binaries could not be executed at all, while a PATH-resolvable `grep` in the same goal
ran fine and returned a correct `fail`. The archived record is
`.claude/state/goal-history/goal-s316-replaced-windows-boundary-20260921T0920.json`; the
working shape, already present in two archived goals from 2026-09-11, is
`wsl.exe --exec bash <absolute linux path>.sh`.

**`error` and `fail` are different readings and the distinction is the diagnosis.** A
criterion that cannot run is an unsupervised criterion wearing a guard's uniform — the same
defect as a doc nobody reads, in a surface that looks mechanical.

### One more rule, and where this page's own record lives

**A positional cross-reference — "two paragraphs above", "see below" — is a claim about the
document's own layout, and every edit falsifies some of them silently. Cite by name.**

This page was drafted under a session goal whose `judge` criteria were fixed before it was
written, and the `goal-evaluator` refuted claims in it before it merged. The evaluator
appends its verdicts to the session goal file — its write is hook-narrowed to that one file
(`.claude/hooks/pretooluse_goal_evaluator_write_deny.py`) — but that file sits under the
gitignored `.claude/state/`: per-machine, and rotated when a goal closes. By this page's own
test that is an expiring home.

The tracked record is
[`docs/logs/2026-09-21-s316-goal-gate-seven-rounds.md`](../logs/2026-09-21-s316-goal-gate-seven-rounds.md):
the seven rounds that judged PR #1545, each bound to the commit it judged by recomputing the
gate's own fingerprint. Its scope is closed — a closed round does not change — so it can
stay true where a running summary could not. **Read that record; this page does not restate
it.**

## What this does not settle

PLAN-0128's closeout left open whether `tag --reflow` should get a **retroactive AC** or a
note that it rode in under Step 3 on its battery. **Cray ruled that question, not this
lesson:** no retroactive AC — the flag rode in under Step 3, and
`tests/batteries/plan-0128-pr3-tag-reflow.json` is its record. The ruling is written into
the archived PLAN itself, on its `**Batteries:**` line. This lesson records where the flag's
*mechanism* is supervised and where it is not; it argues neither side of the AC question.

## How to apply it

1. For any sentence you are about to write down, name who would make it false.
2. Check whether that person's own workflow surfaces it — a test they run, a guard that
   fires on their commit, a comment adjacent to the line they are editing.
3. If nothing does, either move the sentence to a surface that does, or accept — **in
   writing** — that it is a convenience with a safe failure mode. A README entry whose
   worst case is "you hit the correct refusal one step later" is fine. A rule whose worst
   case is silent divergence is not.
4. An archived PLAN, a gitignored handoff, and a `docs/STATUS.md` row scheduled for
   rotation are all **expiring** homes. Reasoning lineage may live there; a live rule may
   not.
5. **Cross-reference by name, never by offset.** "Two paragraphs above" is a claim about
   layout that the next edit falsifies without reddening anything — three of this page's
   own defects were that shape. A section title, a probe name, a symbol name: each is a
   handle the breaker also has to touch.
