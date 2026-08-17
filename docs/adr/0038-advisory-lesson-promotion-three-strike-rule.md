# ADR-0038: The three-strike promotion rule — when an advisory lesson class becomes binding, what "binding" takes per class, and the demotion path that keeps this from being a ratchet

**Status:** Proposed
**Date:** 2026-08-17 (session-235 census; Cray's two typed rulings the same day)
**Deciders:** Jirachai Thiemsert (Cray) — ruled the threshold and the scope
(typed, 2026-08-17; recorded as R1/R2 below, not re-argued). Everything else in
this ADR is a draft position that binds only at Cray's ratification.
**Related:** CLAUDE.md §1 (precedence — lessons are advisory, "promote to ADR if
it must bind"; that clause is the door this ADR walks through), §4 (knowledge
placement + the keep-`CLAUDE.md`-short instruction D2 exists to honour), §6
(verification hygiene), §8 (the scenario-test rule — the control group: a
binding mechanical rule this repo actually obeys); ADR-0017 (D5/D6 knowledge
routing); ADR-0018 (the goal gate + `goal-evaluator` — D3's substrate); ADR-009
D1/D2 + ADR-012 D4.3 + ADR-013 D1 (drafting route + disclosure); **PLAN-0108**
(consumer — its Related-ADRs line names this ADR as the companion that "MUST
land first", `docs/plans/0108-ac-authoring-and-preclose-convention-hardening.md:6`;
referenced here, never restructured); **PLAN-0107** (independent of this ADR in
both directions — deliberately not coupled, per `0108:7`); PLAN-0099 (C3's
substantive fix, already ratified); lessons #0024, #0030, #0033–#0037,
#0039–#0045.

> **Drafting provenance (ADR-012 D4.3 / ADR-013 D1).** Drafted by the in-harness
> `plan-drafter` subagent from a Code-authored dispatch carrying Cray's two
> typed rulings (2026-08-17) and the session-235 census. The rulings are Cray's;
> the per-class enforcement determinations (D2), the `measure` proposal (D3),
> the watch-list posture (D4) and the staging/demotion design (D5) are drafter
> positions for ratification. Every `file:line` cited below was opened with
> Read/Grep on 2026-08-17 in this drafting session, except three facts
> explicitly marked *census-attributed* at their sites. Independent review:
> Code (R2) at PR; ratification: Cray. Author≠reviewer separation: **INTACT**.
> Uncommitted draft — Code commits per ADR-009 D2.

## Context

### The asymmetry this ADR exists to close

This repo obeys rules that are **binding and mechanical** to an unusual
standard: the session-235 audit of CLAUDE.md §8's scenario-test rule found zero
violations across all 17 scenario/e2e files (census-attributed; not re-derived
here). The same repo carries **26 lessons marked advisory** (verified this
session: a grep over `docs/lessons/` for the advisory class marker returns
exactly 26 files, 2026-08-17), and five recurring failure classes among them
have each fired three or more distinct times — one of them six.

Advisory placement is not a mild version of binding. It is a position from
which a rule **cannot act**, and this repo has measured that twice:

- Lesson #0024 — the host-state rule was written in at least three places;
  none of them was the stop-classifier's single input document, and **all four
  evaluated models, including the production classifier, answered `proceed`**
  against it (`docs/lessons/0024-rules-must-live-where-the-enforcer-looks.md:26-38`).
- Lesson #0039 §1 — the same rule was written down three times, in the
  author's own words, inches from the code that violated it; all three
  violations shipped and were caught only by running the thing
  (`docs/lessons/0039-a-self-authored-guard-inherits-the-authors-blind-spot.md:28-42`).

So the open problem was never "write better lessons". It is the rule by which
a lesson **stops being advice** — and paying honestly for what that costs.

### Cray's typed rulings — DECIDED, recorded, not re-opened

- **R1 (2026-08-17, typed): the three-strike rule is ruled IN.** An advisory
  lesson class promotes to binding when it has fired **three or more distinct
  times**. This ADR states it (D1), defines its terms precisely enough that two
  independent counters agree, and applies it once.
- **R2 (2026-08-17, typed): scope is ruled.** Only classes meeting the
  threshold **today** promote. Not all 26 lessons. No general "lessons are now
  binding" sweep.

The threshold number and the scope are not argued anywhere below.

### The census — measured 2026-08-17, every firing read at source

Counting rules used (these become D1's normative text): a **firing** is one
distinct real-world incident that actually occurred and cost something; one
incident cited in five files is ONE firing; a hypothetical is ZERO; the
lesson's existence is not a firing.

| Class | Predicate (one sentence) | Firings | Existing enforcement |
|---|---|---|---|
| **C1** | A green came from an oracle that could not have gone RED over the defect (vacuous / structurally blind) | **6** | **none** |
| **C2** | An inherited premise was treated as context rather than a claim to re-measure | **4** | none mechanical (one actor's prompt only — see D2-C2) |
| **C3** | A wall-clock or otherwise non-monotonic key sat on a correctness path | **4** | partial: a static guard exists and is scope-blind on three axes |
| **C4** | A rule or decision was recorded outside the surface its consumer scans | **3** (thin) | half-covered by CLAUDE.md §4's placement bright line |
| **C5** | A rendered-layout defect that no source-text oracle can see | **4** | none — the source-text proxies self-declare blindness |

**C1's six**, each verified at the cited lines this session:
s205 — a search string recovered from a doc's quote rather than the emitter
never existed in any transcript, turning ≥56 real deny events into a `0` that
stood 19 days (`docs/lessons/0035-negative-measurement-needs-a-positive-control.md:29-62`);
s206 — an ordering site escaped all three of a guard's axes at once —
outside `services/`, a Python `sorted()`, a column named `at`
(`docs/lessons/0037-a-scans-blind-spot-is-the-intersection-of-its-axes.md:48-62`);
s214 — a hazard set with no braces left a guard green over the exact
`--format={{…}}` command that failed on the PowerShell host
(`docs/lessons/0039-…:44-69`); s222 — a presence assertion no probe had shown
could fail, and a delta count that passed while its subject was severed
(`docs/lessons/0040-a-probe-proves-one-direction-only.md:41-64`); s232 — a
committed-file guard blind to the untracked new file: 4107 green locally, CI
red on the same tree (`docs/lessons/0044-a-committed-file-guard-is-blind-to-the-new-file.md:13-28`,
PR #1179); s233 — a liveness probe inside the SSH session returned `200` for a
process the session's own teardown had already condemned
(`docs/lessons/0045-a-probe-that-shares-fate-with-its-subject-cannot-fail.md:17-40`).

**C2's four:** s130 — "OQ-8 is unbuilt / a precondition" inherited as a given;
ADR-0025 had already decided AND built it (`docs/lessons/0030-…:5-17`); s205 —
the search wording inherited from a doc's transcription instead of the emitter
(`docs/lessons/0035-…:44-62`); s224 — SD-8's factual premise was false when
authored, and a true adjacent observation laundered it forward
(`docs/lessons/0041-a-decision-slots-premise-is-a-claim-not-context.md:5-49`);
s229 — a remembered baseline of 6 known failures met a measured 7
(`docs/lessons/0042-a-remembered-baseline-is-not-evidence.md:32-57`).

**C3's four:** the accepted-quote read-model flake — 20 backward clock steps in
528M samples, ≈0.9%/run (`docs/plans/done/0099-wall-clock-root-fix-store-at-write-and-sequence.md:38-68`);
`latest_accepted_quote` feeding the DOA gate the superseded acceptance —
the audit trail inverting its own meaning (`…0099-…:69-81`); PR #1034's
uuid4 tiebreak measured 50.5% newest-first over 20,000 reps — a coin flip
wearing the costume of a fix (`docs/lessons/0036-a-tiebreak-buys-repeatability-not-order.md:35-53`);
PR #1035's task chain, where both directions were live failures — a finished
step nudged forever, a reopened one silently un-chased (`docs/lessons/0036-…:55-69`).

**C4's three (thin):** the classifier incident above (`0024:17-38`); the
hosting-ADR gate whose definition lived in an archived PLAN, whose
do-not-pick-up lived in a gitignored handoff, and whose visible surface
contradicted both (`docs/lessons/0034-deliberate-gate-outside-the-scanned-surface.md:22-52`);
the rule-as-comment triple from `0039:28-42`.

**C5's four:** `.hero-sub` applied but defined in no stylesheet — one unwrapped
line measured 1121px inside a 980px column, console clean
(`tests/api/test_css_class_contract.py:3-7`); s197 — the nav bar 443px past the
viewport, scrollWidth 1825 vs clientWidth 1382
(`tests/api/test_static_ui.py:67-79`); s234 — Tab I's 305px vertical clip
shipped live (PR #1190, merged to `main` at `28bc043`, branch
`fix/tab-i-case-view-scroll`; the 305px figure and commit `4b0fdda` are
census-attributed — the PR's existence was verified against the branch log,
the number was not re-derived); PR #1179's disclosure shipped with no CSS and
painted as stray text — what eleven green tests could not find, because this
repo has no rendering oracle in CI (`docs/lessons/0044-…:65-75`).

**Excluded by construction:** lesson #0027 is already binding via CLAUDE.md §6
and is not a promotion candidate. The two classes at exactly 2 firings go to
D4, not to promotion (R2).

## D1 — the promotion rule (states R1, defines its terms, applies once)

**The rule (R1, Cray, typed):** an advisory lesson class promotes to binding
when it has fired **three or more distinct times**.

**Definitions — written so two independent counters get the same number:**

1. **Class** = a failure predicate: one sentence that assigns any incident IN
   or OUT (the census table's second column is the format). A class is **not**
   a lesson file — C1 spans six lessons, and one lesson can evidence two
   classes (#0035 evidences C1 via the un-reddenable zero and C2 via the
   transcribed premise). The predicate is written down where the tally lives
   (D4); counting against an unwritten predicate is not counting.
2. **Firing** = one distinct real-world incident that actually occurred and
   cost something (rework, a wrong number standing, a shipped defect, a wrong
   decision nearly made), and that satisfies the predicate. One incident cited
   in N files is ONE firing. A hypothetical is ZERO. The lesson's existence is
   not a firing. **Distinct incident required; distinct mechanism NOT** — the
   recurrence of one mechanism is precisely the signal.
3. **Distinct incident** = a distinct defect-occurrence, not a distinct
   session. One session can contribute several firings when several
   independent defects each satisfy the predicate (s231 contributes two to the
   #0043 watch-list entry); one defect rediscovered N times is one firing.
4. **Cross-class counting**: deduplication is per class. One incident may
   count once in each of several classes when it factually satisfies each
   predicate (s205 fires C1 and C2). This is the reading the census's own
   arithmetic uses; it is surfaced as SD-1 for explicit ratification because
   the alternative (an incident counts in exactly one class) produces
   different tallies and must not be left to the counter's taste.
5. **Who counts, and when**: at lesson-write time. The writer of the lesson
   recording a class's Nth distinct incident states the running tally — with
   the incident list, not just the number — in that lesson's header, checked
   against D4's standing watch-list. The tally is reviewed at that lesson's PR
   like any other measured claim. There is **no standing census** (D4
   eliminates it; the 2026-08-17 census is the baseline).
6. **What crossing 3 does**: the class **promotes**. Concretely: (i) its rule
   acquires binding force under §1 precedence — recorded by an amendment pass
   to this ADR naming the class, its predicate, its firing list, and its D2
   enforcement form, which Cray reviews at that PR; (ii) the D2-form
   enforcement work becomes **owed**, with a named owner. Leaving a ≥3 class
   advisory requires an explicit typed Cray waiver recorded at the same site.
   Promotion is an obligation, not an option; the waiver exists so the
   obligation is dischargeable honestly rather than silently ignored.

**Applied once (R2's scope):** C1–C5 promote under this ADR at ratification.
Nothing else does.

## D2 — what "binding" takes, per class

Four enforcement forms exist, and the determination is per class — this is the
decision that keeps `CLAUDE.md` short, which §4 explicitly asks for:

- **(a)** a new binding rule whose home is `CLAUDE.md` (content described
  here; **wording deliberately not drafted** — Cowork drafts constitutional
  text by convention, ADR-009 D1);
- **(b)** widening an existing enforcer;
- **(c)** a mechanical gate that makes stating the rule unnecessary;
- **(d)** an entry in an existing binding surface.

**What binding force means before an enforcer lands — stated honestly.**
Lesson #0039 §1 measured that a written rule with no enforcer was broken three
times by its own author. Promotion does not repeal that. What it buys, before
the enforcer exists, is exactly two things: (i) **citable-in-review blocking
status** — a reviewer, a gate agent, or the `goal-evaluator` can block on the
rule without relitigating "it's only advisory"; (ii) **recurrence
reclassification** — a post-promotion incident of a promoted class is a
**defect against this ADR** (fix + a note on why the enforcer missed it, per
§6's classification discipline), not fresh lesson material. Anything more is
the enforcer's job, which is why each class below names one.

### C1 — a green from an oracle that could not have gone RED · 6 firings · form (a)+(d); (c) refused

**The binding rule (binds via this ADR):** a load-bearing green — an
AC-closing test, a guard, a measurement supporting a decision — is not
evidence until its assertion has been **witnessed RED**: a mutation of the
subject shown to redden it, in the direction the assertion claims (an added
payload cannot vouch for a presence assertion, nor a removal for an absence
one — `0040:41-55`), with a positive control for any zero/absence result
(`0035:10-22`).

**Form:** (a) — the rule needs a constitutional bullet, because it must bind
every session including ones where no skill triggers; its content is the
sentence above, its home is §8's quality-constraints vicinity, and its
**wording is left to the Cowork-drafted follow-up** (OQ-2). Plus (d) — the
operational how-to (which mutation, which direction, restore-from-tmp
mechanics) belongs on the pre-close authoring surface PLAN-0108 is already
hardening, per §4's bright line: the rule in the constitution, the how-to in
the task-triggered surface.

**(c) is refused, with reasoning:** a mechanical vacuity-detector is itself an
oracle an author supplies, and #0039's whole finding is that a self-authored
guard inherits the author's blind spot — the guard written *for* the
metacharacter failure mode was green over the exact command that failed
(`0039:44-69`). A vacuity gate would be the most C1-prone artifact in the
repo. The enforcement here is a discipline with review teeth, not a hook.

### C2 — an inherited premise treated as context · 4 firings · form (a)+(d)

**The binding rule (binds via this ADR):** an inherited load-bearing premise —
a fact-pack line, an SD-slot premise, a STATUS shorthand, a remembered
baseline — is a **claim**: before a decision consumes it, either re-measure it
against the live surface or mark it *asserted-not-verified* at the point where
the decision is recorded. Negative and precondition claims ("X is unbuilt /
absent / deferred") get the strictest treatment — `0030:5-17` shows a
load-bearing rejection nearly built on one.

**Form:** (a) — described for the §6 verification-hygiene vicinity (wording to
the follow-up, OQ-2). Plus (d) — the only enforcement that exists today is
**one actor's prompt** (the `plan-drafter`'s verify-inherited-claims clause);
promotion widens the same discipline to every decision surface, most
concretely: an SD slot's premise line carries a measured-on date and an
evidence pointer, so the premise is visibly a claim with provenance rather
than ambient context (`0041:11-30` is the mechanism this closes). Which PLAN
carries that authoring-surface change is OQ-3 — **not** PLAN-0108, which is
referenced as committed and is not restructured here.

### C3 — a non-monotonic key on a correctness path · 4 firings · form (b); no new constitutional text

The substantive rule is already ratified: PLAN-0099 established store-at-write
`seq` for correctness-path ordering, and the repo carries a static guard. What
the four firings and lesson #0037 measure is that the guard is scope-blind on
**three independent axes** — directory (`services/` only), call shape
(`order_by(...)` only; a Python `sorted()` is invisible), and a nine-name
hand-picked vocabulary, a limit the guard states about itself
(`tests/services/db/test_run_analytics_ordering_guard.py:30-33`) — and that
the escaped site escaped **all three at once** (`0037:48-62`).

**Form:** (b) — widen the existing enforcer, argued **per-axis** because
#0037's corollary is that widening one axis catches nothing caught by another:
directory scope beyond `services/` (at minimum `verticals/`); call shape to
cover Python `sorted()` keyed on model attributes; and the vocabulary roster
replaced by **discovery** (timestamp columns enumerated from ORM metadata
rather than a hand list) — the "rule, not roster" repair pattern that
`0044:48-58` showed is strictly better independent of any incident. No new
`CLAUDE.md` text: the rule exists; the enforcer was narrow. Owner: OQ-4.

### C4 — a rule recorded outside the surface its consumer scans · 3 firings (thin) · form (d); no new enforcer

§4's knowledge-placement bright line already binds placement *by reader*. The
three firings add two clauses it does not yet state: (i) a rule intended to
bind an **automated judge or enforcer** must be placed in that enforcer's
actual input surface — writing it anywhere else is writing it nowhere, for
that consumer (`0024:30-38`); (ii) a gate/tripwire definition and its
do-not-act instruction must live on a **scanned, tracked** surface — never
only an archived PLAN or a gitignored handoff (`0034:35-49`).

**Form:** (d) — extend the existing §4 routing rule with those two clauses
(described; wording to the follow-up, OQ-2) and mirror them in the
memory-architecture runbook. No new enforcer: this rule's consumer is the
human or agent doing the placing, and its natural check is review. The count
is the thinnest of the five (3, flagged thin by the census) — it promotes
because R1 says so, but its cost is near-zero, which D5 uses.

### C5 — a rendered-layout defect no source-text oracle can see · 4 firings · form (c) via D3 once ratified; interim rule binds now

The census's enforcement read is exact: the proxies self-declare blindness —
the CSS-class contract states it is "a **name-existence** guard, not a
rendering test … rendering is verified in the browser preview — evidence, not
the gate" (`tests/api/test_css_class_contract.py:19-24`), and there is no JS
runtime in CI to build a rendering oracle on (`0044:70-75`).

**Interim binding rule (binds via this ADR):** a perception-level claim —
renders, legible, fits the viewport, *reads as* a notice — is never closed by
a source-text oracle alone. Its closing evidence is a recorded measurement
(geometry numbers, per the s197/s202 pattern) or a recorded human visual pass
naming what was looked at. The source-text proxies remain as cheap tripwires;
they stop being allowed to *close* perception claims.

**Full form:** (c) — the proposed `measure` criterion bucket (D3), which gives
such claims a satisfiable, auditable home in the goal machinery. C5's
enforcement completes only if D3 is ratified; the interim rule does not wait.

## D3 — the `measure` criterion bucket · PROPOSED — Cray's to ratify; nothing in this section is decided

**The gap, verified:** `/goal` splits criteria into `check` — a command's exit
status decides it (`.claude/commands/goal.md:31-40`) — and `judge` — the
Read-only `goal-evaluator` judges from repo-local disk evidence
(`.claude/agents/goal-evaluator.md:17-26`, `:70-77`). A rendered-layout claim
fits neither: no runtime exists for `check`, and no repo-local artifact exists
for `judge`. Today such a claim is either dropped or written as a criterion
that is permanently INSUFFICIENT-EVIDENCE — which the repo's own rule (a goal
criterion must stay satisfiable) calls defective.

**Proposal:** a third kind, `measure`, satisfied only by a **committed
measurement artifact produced out-of-band** (browser geometry eval, live
probe) that carries, at minimum: the metric name, value and units; the exact
procedure run (re-runnable by a future session); the commit SHA of the surface
measured; who took it and when; and the pass predicate **fixed before the
number was taken** (the §8 / Lesson #0026 pre-committed-read discipline). The
`goal-evaluator` then judges a `measure` criterion from that artifact on disk
— unchanged Read-only, no new capability.

**What makes the artifact trustworthy — structural, not promissory:** it must
land in the **same PR** as the claim it closes (or be explicitly marked
*reconstructed*, surfacing its provenance); it must name a procedure, not just
a number; and the procedure must carry a **positive control** — shown
detecting a known-bad state at least once — because a geometry sweep that has
never seen an overflow is a C1-shaped zero (`0035:10-22`). An artifact missing
any of these is INSUFFICIENT-EVIDENCE, never PASS.

**The laundering failure mode, named:** `measure` becomes the channel through
which an **unmeasured claim enters the record wearing measurement's costume**
— in two shapes: a number nobody took, written from memory or belief
(`0042:32-57` is that shape with a test count), and a **stale re-cite** — a
real, honest measurement re-cited against a tree it was never taken on. The
same-PR freshness rule and the against-SHA field exist for the second; the
positive-control and re-runnable-procedure requirements exist for the first;
and C2's premise-is-a-claim rule applies to every `measure` artifact anyone
inherits. If those defenses are dropped in ratification, the bucket should be
rejected outright — a laundering channel is worse than the dropped-criterion
status quo, because it manufactures false confidence at the exact point the
repo looks for evidence.

**Open ratification parameters (Cray's):** the kind's name; the artifact's
home (a dedicated `docs/evidence/`-style location vs a plan-local evidence
block); whether the positive control is per-procedure or per-instance; and
the evaluator-payload wiring. PLAN-0108 consumes whichever bucket set is
ratified (`0108:58-60`) and is not blocked on any particular answer.

## D4 — the watch-list is standing; the census is not (one elimination)

**Decision (draft):** the two classes at exactly two firings are named here as
a **standing watch-list**, so the next distinct incident promotes by D1's
lesson-write-time mechanism without any census:

- **W-1 — a probe's RED must name what broke** (#0043; s231 ×2: a guard
  reddening as `RuntimeError: no running event loop` before reaching its
  assertion, `docs/lessons/0043-a-probes-red-must-name-what-broke.md:24-45`;
  and a second same-session case, census-attributed).
- **W-2 — a cheap parameter change where the measured unit is wrong** (#0033's
  6→15 threshold raise that left the guard blind to the exact failure mode it
  existed to catch, `docs/lessons/0033-raising-the-threshold-is-not-fixing-the-unit.md:23-35`;
  and the uuid4 tiebreak of `0036:46-53`).

**The elimination:** this ADR proposes that the **standing full census be
eliminated as a practice** — not automated, not scheduled, gone. The
2026-08-17 census is the baseline; from here the tally is event-driven at
lesson-write time (D1.5), carried by the writer who is already holding the
incident. A periodic census is itself a C4-shaped artifact: a deliberate sweep
whose definition would live outside the surface where lessons are written, and
which decays exactly the way the census's own C4 exemplars did. Two entries
of bookkeeping in this ADR is the entire carrying cost.

## D5 — the cost, honestly: staging, demotion, sunset

**Do all five promote immediately?** Yes — R1 leaves no residue on that point:
all five qualify today, so all five rules bind at ratification. But
**rule-binding and enforcement-building are different costs**, and only the
first happens at once. The owed enforcement work is staged by value-per-cost:

1. **C4** — a text extension to an existing surface; near-free; first.
2. **C3** — a bounded widening of an existing guard; second.
3. **C1 + C2** — the census's own read: no enforcer at all and the
   highest-value promotions. Their constitutional bullets ride the OQ-2
   follow-up; their authoring-surface mechanics ride PLAN-0108's surfaces
   (C1) and OQ-3 (C2). Until then they bind as review-citable rules — the
   two-thing honest minimum stated in D2's preamble.
4. **C5** — the interim rule binds now; the full form waits on D3's
   ratification, deliberately, because a half-specified `measure` bucket is
   the laundering channel D3 names.

**Demotion — the path that keeps this from being a ratchet.** A rule that can
only ever be added is a ratchet, and this ADR is being written because
ratchets-that-cannot-act are the failure mode under study; a ratchet that
cannot release is merely the same defect facing the other way. Proposed
(SD-2, Cray's to ratify): **demotion runs on the same currency as promotion**
— three distinct incidents in which a promoted rule or its enforcer itself
caused measured net cost (false-fire, deadlock, legitimate work wrongly
blocked) open a **demotion item** that must be brought to Cray, with the same
tally discipline D1 demands. Demotion itself is a typed Cray ruling, never
automatic — the asymmetry is deliberate, because demotion removes protection
while promotion adds obligation, and the two are not symmetric in blast
radius. The repo has lived the cost side already: the L1 loop-detect history —
four false-fires in five sessions, three deadlocks, two Cray-authorised shell
escapes (`0033:5-12`) — is precisely the evidence shape a demotion item would
carry.

**Sunset:** each D2 entry names, at promotion or in its amendment pass, the
condition under which its enforcement becomes obsolete (for C5: a real
rendering oracle in CI would retire both the proxies' closing-evidence
restriction and most of `measure`'s reason to exist; for C3's vocabulary axis:
discovery landing retires the roster). An enforcement whose obsolescence
condition has fired is removed by the same amendment mechanism, without a
demotion tally — obsolete is not the same as net-negative.

## Consequences

### Positive
- Five failure classes with 21 verified firings between them stop being
  advice; recurrence becomes a defect with an owner instead of a new lesson.
- `CLAUDE.md` stays short: two described bullets and one clause extension are
  the entire constitutional footprint; C3 adds none; C5's machinery lives in
  the goal harness.
- The promotion mechanism becomes self-executing at lesson-write time — no
  census to schedule, no census to go stale.

### Negative
- Two rules (C1, C2) bind before their enforcers exist — the exact condition
  #0039 §1 measured as weak. Mitigated only by review-citability and
  recurrence-reclassification, and stated as such, not oversold.
- Witnessed-RED discipline (C1) has a real per-test cost; it is the price of
  the six firings, but it is a price.
- `measure` (D3), if ratified carelessly, is a laundering channel; the
  defenses are load-bearing, so ratification must be all-or-nothing on them.

### Neutral
- The watch-list adds two entries of standing bookkeeping to this ADR.
- Lesson files of promoted classes gain a one-line pointer ("binding per
  ADR-0038") at their next natural edit; no mass-edit is owed.

## Alternatives considered

### Promote all 26 advisory lessons
Ruled out by R2, and rightly: most advisory lessons record environment quirks
and one-time recoveries with no recurrence signal; binding them all would be
the general sweep R2 forbids and would bury the five real signals in noise.

### Leave everything advisory; rely on lessons being read
The census is the refutation: five classes re-fired 3–6 times each *after*
being written down. #0024 and #0039 measure the mechanism — placement without
an enforcer, and rules inches from the violation.

### Mechanically gate everything promoted
Refused per class where refused (C1: a vacuity gate is itself C1-prone; C4:
the consumer is the placer). A gate is the strongest form where it fits (C3,
C5-via-D3) and a liability where its own oracle would be blind.

### A standing periodic census
Eliminated (D4): it is a C4-shaped artifact that decays; event-driven
tallying at lesson-write time puts the count where the counter already is.

## Surfaced decisions (for Cray at ratification)

- **SD-1 — cross-class counting.** Draft position: dedup per class; one
  incident may fire multiple classes it factually satisfies (D1.4 — the
  census's own arithmetic). Alternative: exactly-one-class per incident,
  which changes C2's tally from 4 to 3 (s205 counted once). This sets every
  future tally, so the counting text must be Cray-ratified, not
  drafter-chosen.
- **SD-2 — demotion mechanics.** Draft position: three cost-incidents open a
  demotion item; demotion is a typed ruling, never automatic (D5).
  Alternative: symmetric auto-demotion at 3 — rejected in draft for blast
  radius, surfaced because the asymmetry is a values call, not a technical
  one.
- **SD-3 — D3 in its entirety** (bucket name, artifact home, positive-control
  granularity, evaluator wiring) — proposed, never decided here.

## Open questions

- **OQ-1:** D3 ratification (SD-3's parameter list). Blocks C5's full form
  and one input to PLAN-0108's template port; blocks nothing else.
- **OQ-2:** the Cowork-drafted constitutional wording for C1's bullet, C2's
  sentence, and C4's two-clause extension (this ADR describes content and
  placement only; ADR-009 D1 governs the drafting route).
- **OQ-3:** which PLAN carries C2's SD-slot premise-stamp authoring
  convention. Explicitly **not** PLAN-0108 by this ADR's hand — that PLAN is
  committed and referenced as-is.
- **OQ-4:** owner and PLAN for C3's per-axis guard widening.

## References

- Census exemplars: `docs/lessons/0030`, `0033`, `0034`, `0035`, `0036`,
  `0037`, `0039`, `0040`, `0041`, `0042`, `0043`, `0044`, `0045` (full
  filenames at their citations above);
  `docs/plans/done/0099-wall-clock-root-fix-store-at-write-and-sequence.md`
- Enforcement surfaces read: `tests/services/db/test_run_analytics_ordering_guard.py`,
  `tests/api/test_css_class_contract.py`, `tests/api/test_static_ui.py`,
  `.claude/commands/goal.md`, `.claude/agents/goal-evaluator.md`
- Consumer: `docs/plans/0108-ac-authoring-and-preclose-convention-hardening.md`
- Governance frame: CLAUDE.md §1/§4/§6/§8; ADR-0017; ADR-0018; ADR-009 /
  ADR-012 / ADR-013
