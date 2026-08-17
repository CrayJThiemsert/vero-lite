# PLAN-0108: AC-Authoring and Pre-Close Convention Hardening (Convention/Process)

**Status:** Draft
**Owner:** Claude Code (execution + commits; template/plan-doc drafting routes per the mechanical overlay — see Step 1's routing note)
**Created:** 2026-08-17
**Related ADRs:** **Companion ADR (unnumbered, not yet drafted) — MUST land first.** It carries the two behaviour-binding decisions this PLAN consumes but must not make (CLAUDE.md §1): the advisory-lesson→binding promotion, and whether a third `measure` criterion bucket joins `check`/`judge`/`evidence`. Also: ADR-0017 (knowledge placement — the rule-vs-skill bright line governs where each artifact below lands); ADR-009 D1/D2 (drafting/commit split for governance docs); ADR-0018 (the goal gate whose split rule is being ported).
**Sibling:** PLAN-0107 (implementation half — strong offline oracle). **No ordering constraint runs between 0107 and 0108 in either direction**: 0107 is landable while this PLAN awaits its ADR; this PLAN's probes against pre/post-0107 states use recorded facts, not the live tree.

> **Drafting provenance (ADR-012 D4.3).** Drafted by the in-harness `plan-drafter`
> subagent from the session-235 audit fact-pack + Cray's typed split ruling
> (2026-08-17). Independent reviewer: Cray at PR merge; committer: Code. Every
> `file:line` below was re-verified with Read/Grep on 2026-08-17; audit-level
> counts that were not re-derived are attributed to the session-235 fact-pack
> explicitly.

> **Rulings recorded (Cray, typed, 2026-08-17).** S1 RULED: the convention work
> is split into this PLAN, apart from PLAN-0107's implementation, **because the
> oracle here is weak**. **The scoped accelerator explicitly does NOT apply to
> this PLAN** — a convention that is wrong is obeyed for months before anyone
> notices, so bold-first is the wrong posture where no oracle catches a wrong
> bold attempt. Every step below is deliberate, worked against known exemplars,
> and reviewed; none is attempted "boldly first".

## Why this PLAN exists

The session-235 audit measured, over 54 ACs across 5 recent PLANs (0103, 0106,
0100, 0098, 0033 — fact-pack count): 22 deterministic, 21 judge-style, and 11
**vacuous** (20%) — ACs claiming a runtime verb whose closing evidence was a
source-text read. Three verified exemplars:
`docs/plans/done/0106-fleet-case-persistence-disclosure.md:149-155` (a
disclosure "renders on the published fleet system"; evidence: asset diff + a
guard test over source),
`docs/plans/done/0100-exposure-published-demo-surface.md:585-589` (the UI
"renders a persistent notice"; closed by a source-level tripwire), and
`docs/plans/done/0103-portal-landing-and-per-system-published-profiles.md:254-259`
(closed on committed files on disk). Meanwhile the authoring surface everyone
starts from — `docs/plans/0000-template.md:12-14` — is literally a bare
checkbox, its Verification section (`:25-27`) the prose prompt "How do we know
it worked?", while `/goal` already HAS an explicit split rule
(`.claude/commands/goal.md:31-40`: command-answerable → `check` with a required
`timeout_s`; residue → `judge`). A rendered claim fits **neither** existing
bucket — no runtime for `check`, and the `goal-evaluator` is Read-only with
repo-local evidence (`.claude/agents/goal-evaluator.md:17-26`, `:70-73`) —
which is exactly the gap the companion ADR's proposed `measure` bucket exists
to rule on. And the pre-close discipline in
`.claude/skills/code-operational-policy/SKILL.md:93-100` asks ONE
counterexample question (oracle vacuity) where the audit's law names THREE
independent failure conditions (instrument · reach · arming); the audit also
found the coverage question — "if every criterion passes, does the goal
hold?" — asked nowhere in the goal machinery (fact-pack grep over the four
goal files: one unrelated hit; not independently re-derived).

PLAN-0107 fixes instances. This PLAN fixes the authoring surface that keeps
producing them.

## Goal

Port the `/goal` criterion split rule (extended by whatever bucket set the
companion ADR ratifies) into the PLAN template; install a runtime-verb rule
and a fixture-boundary rule at the same authoring surface; and replace the
skill's single pre-close counterexample question with the audit's
three-condition set — so the next PLAN's ACs are born bucketed, runtime claims
are born with runtime-capable oracles or honest relabels, and the pre-close
habit interrogates instrument, reach and arming instead of oracle vacuity
alone.

## Acceptance Criteria

Buckets are declared honestly: text-presence claims are `check` (a guard test
reads the artifact — never its own constant); wording-quality claims are
`judge` with the reviewer and the pass/fail read named; recorded audits are
`evidence` and say so.

- [ ] **AC-1 [check] — the template teaches the split rule.**
  `docs/plans/0000-template.md`'s Acceptance Criteria section (today the bare
  `- [ ] ...` at `:12-14`) states the authoring rule: every AC declares
  `check` (command + timeout given) / `judge` (artifact + pass/fail read
  named) / `evidence` (explicitly not a gate) — **plus the third bucket if and
  as the companion ADR ratifies it, incorporated verbatim from the ADR, not
  decided here** — and the Verification section (today `:25-27`) additionally
  prompts the coverage question: "if every criterion passes, does the goal
  hold? Name what is NOT covered." A guard test
  `tests/tools/test_plan_template_contract.py` reads the template file and
  asserts the bucket tokens and the coverage prompt are present (token-light
  on purpose — presence is checkable; quality is AC-2/AC-3's judge work).
  Command: `uv run --no-sync pytest tests/tools/test_plan_template_contract.py -q`.
- [ ] **AC-2 [judge] — the runtime-verb rule discriminates.** The template
  carries the rule: *an AC claiming a runtime verb (renders / serves / boots /
  streams / persists) whose evidence is a source-text read is mislabelled —
  re-bucket it, re-word it to the claim the evidence actually supports, or
  attach a runtime-capable oracle.* Judge: **Cray at PR merge**, reading the
  worked appendix in the PR body which applies the drafted rule to four
  verified exemplars. Pass/fail read: the rule as worded must FLAG all three
  vacuous exemplars (`0106:149-155`, `0100:585-589`, `0103:254-259`) and must
  NOT flag `0100:293-305` (AC-3's pinned-viewport geometry criterion — a
  rendered claim with a real runtime instrument and a recorded non-vacuity
  probe, `0100:369-375`). A rule that flags all four is a stopped clock and
  fails this AC.
- [ ] **AC-3 [judge] — the fixture-boundary rule is installed and grounded.**
  The template (with the how-to worked examples in the skill, per ADR-0017 D5
  routing) carries the rule: *a fixture feeding a bounded consumer must cross
  at least one boundary the consumer declares — pagination, truncation, batch
  size, DoA tier, rate limit.* Judge: **Cray at PR merge**. Pass/fail read:
  the rule text names those five boundary kinds and cites the two measured
  counterexamples that motivated it — the 2-case live seed
  (`verticals/fleet_maintenance/operate_seed.py:201,:315`, pre-0107) against
  the UI's own `limit=20` (`services/api/static/assets/view-case.js:71`), and
  the one-canned-judgment stub (`tests/api/conftest.py:29-39,:42-47`) feeding
  every streamed batch — and, applied to those recorded pre-0107 facts, flags
  both.
- [ ] **AC-4 [check + judge] — the pre-close question set is the audit's
  three conditions.** The skill section "The counterexample step — before
  closing an AC" (`.claude/skills/code-operational-policy/SKILL.md:93-100`)
  is replaced by the three-condition set — before closing an AC, answer all
  three: *① INSTRUMENT: can any oracle in this repo read the artifact this AC
  is about? ② REACH: does any fixture put the system in the state where the
  defect would show? ③ ARMING: does a required check's exit status — not a
  recorded artifact — turn RED if the answer to the AC's claim is no?* — while
  **retaining** the existing "READ the RED" legibility clause (`:102-107`)
  unchanged in force. `check` half: a guard test
  `tests/tools/test_skill_preclose_contract.py` reads `SKILL.md` and asserts
  the three condition tokens are present and the retained clause survives.
  Command: `uv run --no-sync pytest tests/tools/test_skill_preclose_contract.py -q`.
  `judge` half: Cray confirms the replacement wording subsumes the old
  vacuity question (condition ③ contains it) rather than dropping it.
- [ ] **AC-5 [evidence] — the retro-classification is recorded.** The 54
  audited ACs are re-classified under the final ratified bucket set and the
  table is recorded in the closing PR body. Recorded, **explicitly NOT a
  gate**: `done/` PLANs are archaeology and are not edited; the table exists
  to calibrate the new rules against real history and to hand the companion
  ADR's reviewer a measured base rate.

## Out of Scope

- ❌ **Deciding the `measure` bucket or promoting any advisory lesson to
  binding** — the companion ADR's decisions; this PLAN consumes them after
  ratification (LOCKED per the dispatch). If the ADR rejects the third bucket,
  AC-1 ships the two-plus-evidence set unchanged — the dependency is on the
  ADR *landing*, not on it landing a particular way.
- ❌ **Constitutional (`CLAUDE.md`) text** — including the §8 wording question
  (SD-1 below): flagged, never drafted here. Cowork drafts constitutional
  text by convention (ADR-009 D1); only Code commits it.
- ❌ **All of PLAN-0107's implementation** — instruments, fixtures, CI steps,
  gate arming. No step here touches code under `services/`, `verticals/`,
  `tests/api/`, or `.github/`.
- ❌ **An AC-linter / enforcement hook** (e.g. a PreToolUse or CI check that
  parses PLAN ACs for bucket declarations) — premature until the convention
  has survived a few PLANs' worth of use; a candidate follow-up, noted, not
  planned.
- ❌ **Retro-editing `done/` PLANs** to the new discipline — archaeology stays
  frozen; AC-5's table is the only retrospective artifact.

## Surfaced decisions (for Cray — proposed, not settled)

- **SD-1 (dispatch S3) — should CLAUDE.md §8's scenario-rule wording widen to
  reach the gold↔engine seam?** The concrete instance (nl-01…nl-12 checked
  only against themselves, `tests/benchmark/test_nl_query_feasibility_gold.py:68-89`)
  is closed mechanically by PLAN-0107 AC-10. Proposed: the *general* wording
  question rides the companion ADR discussion — it is constitutional text
  with the same author/committer split as the ADR's own subject matter, and
  deciding it per-benchmark forever means the next gold set re-opens it.
  Alternative: leave §8 as-is and treat each gold↔engine seam as
  benchmark-specific guard work. SURFACED in both cases; this PLAN drafts no
  wording either way.
- **SD-2 — does the fixture-boundary rule also become a lesson
  (`docs/lessons/`)?** Proposed: no — the template carries the
  at-authoring-time rule text, the skill carries the worked how-to (ADR-0017
  D5 routing: canonical reference vs task-triggered procedure), and a lesson
  would be a third copy of the same sentence with no independent trigger.
  Alternative: a short lesson pointing at both, for greppability. Cray
  decides.

## Steps

**The accelerator does not apply here** (ruled — recorded in the header).
Each step is worked against known exemplars before it is committed, and each
names its non-vacuity probe: for convention text, a probe is the drafted rule
applied to a KNOWN-bad and a KNOWN-good artifact, with the rule's flag output
— not a feeling — as the thing that changes. A rule that cannot mis-fire on
the known-good case has not been tested, only admired.

### Step 1: port the split rule + coverage prompt into the template

Draft the new Acceptance Criteria and Verification sections of
`docs/plans/0000-template.md` (bucket declarations per the ratified set;
coverage question in Verification). **Routing note (mechanical, not a quality
judgment):** a write to a doc under `docs/plans/` is G2-gated for Code, so the
text is drafted via the ungated drafter (`plan-drafter` / Cowork per ADR-009
D1) and Code commits the PR (ADR-009 D2). Write the
`tests/tools/test_plan_template_contract.py` guard (reads the artifact,
token-light).
**Probe:** run the guard against a pre-edit copy of the template → RED (the
tokens are genuinely absent today, `0000-template.md:12-14,:25-27`); against
the edited template → green. Output changed: the guard's verdict across the
edit. A guard that is green on the pre-edit template is testing its own
constant and is rejected.

### Step 2: the runtime-verb rule, calibrated on real exemplars

Draft the rule text; build the worked appendix applying it to the four
exemplars (three vacuous, one legitimately-runtime — the AC-2 set); iterate
the wording until it flags exactly the three and spares the fourth.
**Probe:** the appendix IS the probe, in both directions — the rule applied
to `0100:293-305` must come back clean, and applied to `0106:149-155` must
flag. Output changed: the appendix's per-exemplar flag column. Record the
final appendix in the PR body (feeds AC-2's judge read).

### Step 3: the fixture-boundary rule, grounded in the measured gaps

Draft the rule (five boundary kinds, per the ruling); cite the two recorded
pre-0107 counterexamples in the rule's motivation line; place the worked
how-to (how to find the consumer's declared bound: grep the consumer for its
`limit`/clamp/batch constants, then check the largest fixture against it) in
the `code-operational-policy` skill per ADR-0017 D5.
**Probe:** apply the rule to the recorded pre-0107 facts (2-case seed vs
`limit=20`; one canned judgment vs a streamed batch) → both flagged; apply it
to PLAN-0107's post-state as written in its AC-7/AC-8 (≥ 21 cases crossing
the limit; per-event judgments) → both pass. Output changed: the rule's flag
verdict across the 0107 boundary — computed from recorded facts, so no
execution-order dependency on 0107 exists.

### Step 4: replace the pre-close question with the three-condition set

Edit `SKILL.md:93-100` per AC-4, retaining `:102-107` verbatim; write the
`tests/tools/test_skill_preclose_contract.py` guard.
**Probe:** run the guard against a pre-edit copy of `SKILL.md` → RED (the
three tokens absent); post-edit → green; additionally delete the retained
"READ the RED" clause in a scratch copy → RED (the guard protects the
retention too, not only the addition). Output changed: the guard's verdict
under each mutation.

### Step 5: the retro-classification table

Re-classify the 54 audited ACs under the final bucket set; record the table +
the base rate in the closing PR body (AC-5, evidence).
**Probe:** none claimed — this is the PLAN's one evidence artifact and it is
labelled as such; a probe would be theatre. The table's honesty check is
AC-2/AC-3's calibration work, which already forced the rules to disagree with
at least one plausible classification.

## Verification

How we know it worked — stated with the weak oracle owned honestly:

1. **The deterministic slice:** both guard tests green
   (`test_plan_template_contract.py`, `test_skill_preclose_contract.py`), each
   having been SEEN red against the pre-edit artifacts (Step 1/Step 4 probes)
   — text presence is the part a command can settle, and only that part is
   claimed as `check`.
2. **The judged slice:** Cray's PR-merge reads for AC-2/AC-3/AC-4 against the
   named appendices — the pass/fail criteria were fixed above, before
   execution, per the plan-first discipline.
3. **The real oracle is retrospective and is named as such:** the next PLANs
   authored under the new template either arrive with bucketed,
   verb-honest, boundary-crossing ACs, or the review catches the template
   being ignored — this PLAN cannot prove its conventions correct at merge
   time, only calibrated (against the four exemplars and the measured 20%
   vacuity base rate) and present (the guards). That residual weakness is
   exactly why the accelerator was not applied here, and why the
   behaviour-binding half of this territory sits in the companion ADR where
   Cray ratifies it explicitly.
