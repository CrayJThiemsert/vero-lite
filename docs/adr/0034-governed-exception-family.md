# ADR-0034: The governed exception family — three exception mechanisms (escalate-never-skip waiver · evidence-alternative · deferred ratification), grounded in four real customer instances; SoD and compliance stay non-waivable by type

**Status:** Accepted — ratified by Cray 2026-07-28 (session 185, typed AskUserQuestion pick after Code R2); OQ-1 / OQ-2 / OQ-3 resolved per their in-file recommendations in the same pick
**Amendment log:** 2026-07-29 — **RATIFIED (Cray, typed pick, session 187)**: **D3(3)'s precondition clause + the two D3(3)/D3(4) status-transition sentences ONLY** — the shipped mechanism is obligation/audit-based, not status-based. Full reasoning in §"D3 Amendment (2026-07-29)" (in place, after D3(6)). The ADR Status **stays Accepted**.
**Date:** 2026-07-28
**Deciders:** Jirachai Thiemsert (Cray) — ratifies. The ADR-first route and the Phase-1 = Lean-KPI-first scope are already LOCKED (Cray, typed AskUserQuestion picks, 2026-07-28, session 184); this ADR decides the *mechanism design* those picks routed here.
**Related:** ADR-0025 (D2 typed AT-2 content home; **D3 bypass-unrepresentable** — this ADR EXTENDS the D3 waiver without weakening any unrepresentability; D4 prose-lint; D7 outcome amendment / PLAN-0087 criterion vocabulary), ADR-0026 (D4 live fail-closed run-checks the ratify path REUSES), ADR-0032 (D1 demo→pilot wedge + 1-KPI charter this family serves), ADR-016 (run/persistence layer being extended, not replaced), ADR-007 (approve→execute write gate, untouched), ADR-009 D1/D2 (Cowork drafts ungated; only Code commits), ADR-012 D4.3 (author≠reviewer), PLAN-0075 (SD-6(a): no authority tie names a principal who has not acted — the provisional path's honesty rule), PLAN-0086/0089/0090 (the fleet vertical), **PLAN-0096** (the consuming PLAN, drafted alongside). Substrate (verified on disk at `main`=`7b84fa2`): `services/engine/procedures/spec.py`, `runs.py`, `action_step.py`, `rule_gate.py`, `governance_step.py`, `verticals/fleet_maintenance/procedures.yaml`.

> **Drafting provenance.** Drafted (uncommitted) by Cowork per the session-184 dispatch
> (`.claude/handoffs/session-184/2026-07-28-1704-code-cowork-fleet-pilot-adr0034-plan0096-dispatch.md`) —
> mechanical G2 routing per CLAUDE.md §6, NOT a quality judgment. Code R2-reviews + commits via a
> `docs/*` PR after Cray ratifies (ADR-009 D2). Cowork does not git.
>
> **Author≠reviewer disclosure (ADR-012 D4.3).** Originators = the design partner (18 discovery
> answers, 2026-07-28), Cray (the two typed scoping picks), and Code (the s184 dispatch's engine
> fact-pack + the E-4 tier-deferral reframing). Drafter = Cowork (cloud session; engine facts
> re-verified via the read-only bridge against `7b84fa2`; the gitignored research files were read
> as chat attachments). **No adversarial panel was run on this draft** — the independent checks are
> Cray at ratification + Code R2 at commit. ADR number 0034 taken from the dispatch fact-pack;
> Code re-verifies the next-free number at commit time.

---

## Context

### Why now

The fleet vertical's design partner (Thai trucking operator; ADR-0032 D1 wedge partner — fit-filter
PASSED, Q18) answered all 18 discovery questions and asked for the demoed flow to be completed for
real-use evaluation. Four of those answers describe **exceptions to his own rules** — and his rules
are already the product (the governed AT-2 spine). The four instances (Rule of Three satisfied, with
one honestly marked a hypothesis):

| # | Instance | Partner evidence | Status |
|---|---|---|---|
| E-2 | **Roadside emergency** — "เคาะก่อน ทำเอกสารทีหลัง" (owner decides by phone; the record catches up); **no ฿ cap in his head** — the control is that accounting starts asking within ~a week ("ไม่เกินอาทิตย์ บัญชีจะเริ่มถามแล้ว") | Q9, Q11 | confirmed; partially built (waiver exists; window does not) |
| E-3 | **Sole-source** — a rare part with one vendor: written justification instead of three quotes | Q10 | confirmed; unbuilt |
| E-4 | **Short-staff (Songkran)** — ต้อม opened his own case, วิรัช confirmed by phone, the owner learned after; requester ≠ approver **held** | Q14 | confirmed; unbuilt |
| — | **Seasonal** rule-flexing (pre-New-Year/Songkran) | analyst-voice addendum only | **hypothesis — named, parked** (Q14's confirmed story partially corroborates and may make this a *trigger* of E-4, not a mechanism) |

### The frontier

The engine has exactly ONE exception mechanism family today: `EmergencyWaiverPolicy`
(escalate-never-skip; closed `relaxes` set that cannot name compliance or SoD — `spec.py:917-922`,
`942-967`) plus the additive `ExceptionPolicy` logged-exception labels (`spec.py:904-914`). Nothing
models **decide-first-record-catches-up**: every governed run suspends at `waiting_human`
(`runs.py:47-59`) until the human decides, and a gate resolution is terminal
(`resolve_gated_step` flips `WAITING_HUMAN → RESOLVED`, `action_step.py::resolve_gated_step`;
PLAN-0047 Step 3). The partner's two highest-value exceptions (E-2, E-4) are exactly this missing
shape.

### Engine facts this design is built against (all verified at `7b84fa2`)

- `RelaxableConstraint` = closed `{THREE_BID, SOLE_SOURCE}`; docstring: cannot name compliance/SoD
  (`spec.py:917-922`). `EmergencyWaiverPolicy` fields: `relaxes` (min 1) / `escalate_to` /
  `requires_justification: Literal[True]` / free-text `justification`; `extra="forbid"`; **no cap
  field, no window field** (`spec.py:942-967`).
- `ExceptionPolicy` is consumed in exactly ONE place: `ScoredRule.exception_policy`
  (`spec.py:1028`); the executor reads it as a label (`source_path` stamp). **The fleet hero has no
  `scored_rule` step** (gate sequence: none · in_file_band · none · rule_gate · doa_tier · none —
  `verticals/fleet_maintenance/procedures.yaml`), so an `ExceptionPolicy` member for E-3 would have
  no consumer in this flow.
- `rule_gate` is pass/fail on a supplied per-criterion signal map, fail-CLOSED on an absent map, and
  has **no waive path and no threshold field** (`rule_gate.py::evaluate_compliance`;
  `ComplianceRule`, `spec.py:1031-1052`). The signal is an intake-enrichment convention — "the ฿
  half … lives in whatever feed computes `compliance.three_quote`" is already written into the fleet
  YAML as a recorded gap.
- Gate resolution runs, in order: RF-1 identified-human guard → governance-pin check
  (`assert_governance_pin`; pin = `PipelineRun.governance_snapshot/_hash`, `runs.py:83-90`) → live
  principal-SoD check → live tier-authority check → two-phase decide/commit-then-execute
  (`action_step.py::resolve_gated_step`). The `governed_decision` audit-to-control tie is emitted at
  GATE time, only after the checks pass, naming who ACTUALLY acted (PLAN-0075 SD-6(a)).
- Run/step statuses are Text columns; step audit is JSONB (`runs.py`) — an additive status member
  and an additive audit block need **no DB migration**.

## Decision

Introduce a **governed exception family**: a closed taxonomy of THREE exception mechanisms, each
logged, each leaving SoD and compliance non-waivable, plus ONE new run-lifecycle primitive
(**deferred ratification**) that two of the four instances share. Build the primitive once in
Phase 1 (E-2); add the second authored entry point (E-4) in Phase 2.

### LOCKED (from the dispatch — restated, not re-litigated)

1. ADR-first route (Cray, typed pick). The four instances above ground the design; seasonal stays a
   named, parked hypothesis.
2. **SoD and compliance stay non-waivable by type** — an explicit non-goal below; the ADR-0025 D3
   unrepresentability is preserved verbatim (`RelaxableConstraint` still cannot name them;
   `blocks_po` stays `Literal[True]`).
3. E-4 is **tier-deferral**, not an SoD relaxation. Cowork examined the invited refutation and
   **accepts the framing**: in Q14 the requester (ต้อม) and the provisional approver (วิรัช) were
   distinct humans — what flexed was the *authority tier acting first*, never requester≠approver.
   D5 grounds the mechanism accordingly.

### D1 — The taxonomy: three mechanisms, four instances, one non-goal

A governed exception is never "the rule stops applying." It is one of exactly three shapes:

1. **Escalate-never-skip waiver** *(exists — ADR-0025 D3, unchanged)*: a closed sourcing constraint
   is relaxed, authority strictly escalates, a justification is forced. Instance: E-2's
   quote-relaxation half (`relaxes: [three_bid]`, `escalate_to: เจ้าของกิจการ` — already authored).
2. **Evidence-alternative** *(new category, ZERO new schema — D4)*: the human-authored rule itself
   names more than one evidence path that satisfies an UNCHANGED pass/fail criterion; taking the
   non-default path is logged with its basis. Instance: E-3 (three quotes on file **or** a logged
   sole-source justification). The gate still blocks when no path is satisfied.
3. **Deferred ratification** *(new primitive — D2/D3)*: the decision precedes its firsthand governed
   record; a typed window bounds the catch-up; the run-state makes
   pending / ratified / overdue / refused observable; the `governed_decision` tie is emitted only at
   ratification. Instances: E-2's window half (Phase 1) and E-4 tier-deferral (Phase 2). Seasonal,
   if the partner confirms it, is expected to be a *trigger condition* on E-4's entry point — not a
   fourth mechanism.

**Non-goal, stated as the dispatch requires:** nothing in this family makes SoD or compliance
waivable in any representable form. `RelaxableConstraint` is not extended; no field of any new model
names an SoD constraint or a compliance criterion; a deferred ratification defers WHO has confirmed
firsthand — never WHETHER the quote gate ran, and never requester≠approver (both the provisional
approver and the ratifier are SoD-checked against the requester, D3).

**Elimination proposals** (invited by the dispatch's frontier clause): (a) the hypothesized
emergency **฿ cap field is eliminated**, not deferred — Q11 refuted it ("no cap in the owner's
head"; the window IS the control); it must not reappear as a "safe default". (b) **E-3 as engine
work is eliminated** — it is an evidence path in the feed + the authored rule prose, not a schema
change (D4). (c) A **generic exception-policy registry/object is eliminated for now** — with the
run-lifecycle shared (D2) the remaining per-mechanism surface is one small authored field each;
abstracting further from N=2 confirmed windowed instances repeats the ADR-0025 Rule-of-Three
tension with less justification than ADR-0025 had.

### D2 — Deferred ratification is ONE run-lifecycle primitive with PER-MECHANISM authored entry points

The dispatch's "one primitive or two?" — answer: **one primitive, two doors.**

- **The primitive** (built once, Phase 1): the provisional-resolution → ratification → observability
  run-state machinery of D3. It is mechanism-agnostic: nothing in it knows "emergency" from
  "short-staff".
- **Door 1 — E-2 (Phase 1):** one new OPTIONAL field on the existing waiver:

  ```python
  class EmergencyWaiverPolicy(BaseModel):
      ...existing fields unchanged...
      ratification_window_days: int | None = Field(
          default=None, ge=1,
          description="when set, a waiver-invoked gate resolution may be recorded "
          "provisionally (decide-first) and MUST be ratified firsthand by the "
          "escalate_to authority within this many days; absent = today's behavior "
          "(no provisional path representable). Only-when-supplied (D6).",
      )
  ```

  The **ratifier is `escalate_to` by construction** — the waiver already escalates to that
  authority, and in the partner's practice the phone-decider and the paperwork-signer are the same
  person (Q9: the owner). No new role field (OQ-1 surfaces the alternative). Fleet authors
  `ratification_window_days: 7` (Q11's "ไม่เกินอาทิตย์").
- **Door 2 — E-4 (Phase 2, shape defined now, NOT built):** a ladder-scoped policy, sketched:

  ```python
  class TierDeferralPolicy(BaseModel):   # Phase 2 — final shape decided at its PLAN
      model_config = ConfigDict(extra="forbid")
      max_tiers_below: Literal[1] = 1    # Q14 shows exactly one-tier-down; wider is unobserved
      ratification_window_days: int      # ge=1
  # DoaLadder.tier_deferral: TierDeferralPolicy | None = None   (only-when-supplied)
  ```

  Its ratifier is the **ladder-resolved tier role** by construction (the authority the spend
  actually demanded). The provisional actor must hold an approver tier (never the requester), one
  tier below the resolved tier at most. Build is calendar-gated: the next holiday crunch is
  New Year; PLAN-0096 lists it Out of Scope.

Why not a shared `RatificationPolicy` sub-model on both doors: the two doors share one `int` field
name and nothing else (Door 1's ratifier is `escalate_to`; Door 2's is resolved-per-spend). A shared
config model would be abstraction at N=2 with divergent halves — the shared thing is the RUN-STATE,
and D3 builds exactly that once.

### D3 — Run-lifecycle semantics: the named enforcement path

*(This D exists so the window is never "prose/YAML only" — the PLAN-0094 AC-1 defect class named in
the dispatch. Every branch below is a named code path with an observable state.)*

1. **New step status member:** `StepResultStatus.RESOLVED_PROVISIONAL = "resolved_provisional"`
   (`runs.py` — additive; the column is Text, existing rows unaffected, **no migration**).
2. **Provisional resolution** — a new branch in `action_step.py::resolve_gated_step`, entered ONLY
   when (a) the suspended step's authored ladder waiver carries `ratification_window_days` AND
   (b) the caller explicitly invokes the waiver with the run-time logged justification the waiver
   already forces (`requires_justification`). A non-waiver resolution, or a waiver without the
   window authored, cannot reach this branch — today's path stays byte-identical (the
   only-when-supplied principle applied to *behavior*).
   - The RF-1 identified-human guard still holds: the **recorder** (the principal filing the
     provisional decision — roadside reality: ต้อม or เมย์) must be an identified declared
     principal.
   - The decision is recorded as an **attestation**: the attested approver is the `escalate_to`
     role-holder (the owner who "เคาะ" by phone), resolved to a `person_id` fail-CLOSED — an
     unresolvable attested authority refuses the provisional path.
   - The **live SoD check binds to the attested approver** (attested ≠ requester, alias-collapse
     rejected — the existing `check_principal_sod` seam); the tier-authority check validates the
     ATTESTED approver holds the resolved tier (for E-2 the escalated tier). Fail-closed as today.
   - Effects execute (the repair proceeds — decide-first is the point) via the existing two-phase
     commit; the step lands `RESOLVED_PROVISIONAL`, persisting on the step audit (JSONB):
     `ratification: {due_at, ratify_by_role, attested_approver_id, recorded_by, justification_ref}`
     with `due_at = decided_at + window_days`.
   - **NO `governed_decision` tie is emitted** — PLAN-0075 SD-6(a)'s rule ("no authority tie names a
     principal who has not acted") applied honestly: the attested authority has not acted
     *in-system*. The attestation record is the routing-honest interim.
3. **Ratification** — a new sibling gate driver `ratify_gated_step(session, run_id, step_id,
   principal, ...)`: **the precondition is the OBLIGATION, not the step status** — an outstanding
   ratification obligation, `pending` or `overdue` per D3(6)'s pure `ratification_state()`
   (`RatificationView.is_outstanding`) *(clause amended 2026-07-29 — Cray, typed pick,
   session 187; see §"D3 Amendment (2026-07-29)". As originally accepted this clause read
   `status == RESOLVED_PROVISIONAL`)*. The obligation condition is a **strict superset** of the
   original — a step at `RESOLVED_PROVISIONAL` always carries an outstanding obligation — and it
   preserves the original clause's stated intent verbatim (idempotent BY STATE, mirroring
   PLAN-0047 Step 3): a second ratification finds the obligation no longer outstanding and is
   refused. An `overdue` obligation is **still ratifiable** — overdue is urgency, not expiry; the
   signature is owed either way, and refusing it late would strand the case in the one state
   nobody can clear — which is what makes D3(6)'s completed-run promise real. RF-1; the ratifier
   must hold `ratify_by_role` — enforced by REUSING
   `check_tier_authority` with the ratifier as acting principal (ADR-0026 D4 (iv)); live SoD check
   (ratifier ≠ requester). On pass: `ratified_at` + `ratified_by` persisted, and the
   `governed_decision` tie is emitted NOW, naming the ratifier — the record has caught up. The
   status flip is **conditional**: only a step still parked at `RESOLVED_PROVISIONAL` flips
   `RESOLVED_PROVISIONAL → RESOLVED`; a step the run has already advanced past stays `complete` —
   walking it back would re-enter it into `_UNRESUMED_STATUSES`, making a finished step look like
   the one the run is suspended at (`suspended_step_result` would resume it a second time or
   refuse the run as inconsistent). The obligation lives on the audit block, so the status does
   not need to carry it (D3(6)) *(transition sentence amended 2026-07-29 — same s187 ruling;
   `action_step.py:1165-1172`; see §"D3 Amendment (2026-07-29)". As originally accepted the transition was
   stated unconditionally)*. A refusal is durably audited (`gate_refused`) before the error
   propagates, mirroring the existing SoD/tier refusal audits.
4. **Ratification refused** (the owner declines to ratify): recorded as a terminal
   `ratification: {refused_at, refused_by}` disposition riding the audit block — with the same
   conditional status flip as D3(3): only a step still parked at `RESOLVED_PROVISIONAL` flips to
   `RESOLVED`; a step the run has already advanced past stays `complete` with the refusal on the
   audit *(sentence amended 2026-07-29 — same s187 ruling; the flip sits after the ratify/refuse
   fork, `action_step.py:1151-1154`, `:1165-1172`, so it governs both dispositions; see
   §"D3 Amendment (2026-07-29)". As originally accepted the flip was stated unconditionally)*;
   nothing
   un-executes (the money is spent; the honest record is a named, exported exception —
   fail-VISIBLE, not fail-closed, because closed is impossible after the fact). Surfacing beyond
   the export is OQ-2.
5. **Resume:** `resume_run` advances a gate from `RESOLVED_PROVISIONAL` exactly as from `RESOLVED`
   (act-now semantics; the fulfill step proceeds). One named orchestrator change.
6. **Overdue is COMPUTED, never stored:** a pure function
   `ratification_state(step_result, now) -> pending | ratified | overdue | refused` (deterministic,
   `now` injected — offline-testable) consumed by the render, the month-end export, and the LINE
   reminder nudge. There is **no actor-less state writer** at window expiry: an automatic flip
   would be a state mutation no principal performed, breaking the audit model. `PipelineRunStatus`
   is untouched — a run may complete while ratification is pending; the obligation rides the step
   audit and stays queryable on completed runs.

### D3 Amendment (2026-07-29): obligation-based ratification precondition + conditional status flip

> **Status of this amendment:** **RATIFIED (Cray, typed pick, session 187).** The ADR's overall
> Status **stays Accepted**. **Scope: D3(3)'s precondition clause + the two D3(3)/D3(4)
> status-transition sentences ONLY** — one amendment entry, both halves the same ruling's
> consequence: the shipped mechanism is obligation/audit-based where the original text described a
> status-based model. Amended **in place** (the ADR-0016 D2-Amendment in-place precedent; the
> header log line per ADR-0022).

**(a) Precondition:** the ratification precondition is **the OBLIGATION, not the step status** (an
outstanding obligation, `pending` or `overdue` per D3(6)'s `ratification_state()`), replacing the
literal `status == RESOLVED_PROVISIONAL`. Read literally, the original clause contradicted D3(6)
in the only flow the window exists for: `resume_run` flips every resolved step to `complete` as it
advances (`services/engine/procedures/persistence.py`), and in the fleet hero the step after
`approve` is itself gated — so the run always resumes past `approve` within minutes against a
seven-day authored window, making the owner's signature impossible in exactly the case D3(6)
promises stays ratifiable. Found by BUILDING the mechanism (PLAN-0096 Step 5), not by review — the
shipped code (`action_step.py::ratify_gated_step`: `ratification_state(...).is_outstanding`) and
its discriminating guard test
(`tests/services/db/test_ratification_matrix.py::test_the_obligation_survives_resume_and_is_ratifiable_afterwards`)
predate this text catching up.

**(b) Transition:** both sentences stated `RESOLVED_PROVISIONAL → RESOLVED` unconditionally; the
shipped flip is **conditional** — only a step still parked at `RESOLVED_PROVISIONAL` flips, for
ratification AND refusal alike (the flip sits after the disposition fork:
`action_step.py:1151-1154`, `:1165-1172`); a step the run has already advanced past stays
`complete`, because walking it back would re-enter `_UNRESUMED_STATUSES` and make a finished step
look like the one the run is suspended at (`suspended_step_result` would resume it a second time
or refuse the run as inconsistent) — the obligation rides the audit block, so the status need not
carry it (D3(6)). An oracle-backed design decision (a non-vacuity probe recorded in the
session-187 close report: restoring the unconditional flip reddens exactly one test), surfaced by
Code R2 answering the residual flagged in half (a)'s drafting.

The tie-emission rule, the refusal's nothing-un-executes / fail-VISIBLE semantics,
D3(1)/(2)/(5)/(6), the taxonomy, and the Alternatives are untouched. *Amendment text drafted
in-harness by `plan-drafter` (ADR-013 D1); Code R2-reviews + commits via a `docs/*` PR
(ADR-009 D2) — drafter ≠ ratifier, separation intact.*

### D4 — E-3 routing: an evidence-alternative on the UNCHANGED quote gate (zero engine diff)

The dispatch's fork was "additive `ExceptionPolicy` value vs a waiver-variant relaxing `THREE_BID`
with a sole-source trigger". Judged against how the gate actually consumes these — **both rejected,
third path taken**:

- **Not `ExceptionPolicy`:** its only consumer is `ScoredRule.exception_policy` (`spec.py:1028`),
  and the fleet hero has no `scored_rule` step — the member would be a dead label in this flow.
  (The docstring's "growth here is safe" holds; safe ≠ consumed.)
- **Not a waiver-variant:** `DoaLadder` carries exactly one REQUIRED `emergency_waiver`
  (`spec.py:983`) whose semantics force escalation + emergency framing. Q10's sole-source practice
  is a *standing* procedure with **no escalation** — routing it through the waiver would misstate
  the partner's own rule (every rare-part repair would escalate to the owner).
- **Taken — the evidence-alternative:** the `three_quote` criterion stays pass/fail and the gate
  stays untouched. The human-authored rule names its evidence paths; the signal-computing feed (the
  Phase-1 quote evidence pack) computes `compliance.three_quote` as: *under-threshold* OR *≥3 quotes
  on file* OR *sole-source justification logged*, and stamps a `three_quote_basis` field
  (`under_threshold | three_quotes | sole_source_justified`) onto the row so the basis rides the
  entity into the step audit and the month-end export (OQ-3). This is the gate's DESIGNED
  consumption shape — the signal map is an intake-enrichment convention (`rule_gate.py`, "intake
  enriches the requisition…"), and the fleet YAML itself already recorded that the ฿ half "lives in
  whatever feed computes `compliance.three_quote`". The rule's authored `spec` prose is rewritten to
  name both paths — with **no ฿ token** (ADR-0025 D4 prose-lint; the threshold is typed config in
  the feed, D6/PLAN). A case satisfying NO path is blocked, exactly as today; an absent signal map
  fails CLOSED (`RuleGateError`).

**Consequence:** E-3 is additive-trivial ⇒ per the dispatch's own condition it **lands in
PLAN-0096 Phase 1** (Steps 3–4 there).

### D5 — E-4 tier-deferral: grounding, shape, and the Phase-2 gate

Q14's record: requester ต้อม ≠ provisional approver วิรัช; the flexed dimension was that วิรัช
acted below the spend's resolved tier, with the owner ratifying after. Therefore E-4 is a
**tier-authority timing exception**, mechanically: the provisional branch of D3 with entry
condition = the ladder's authored `tier_deferral` (D2 Door 2) instead of the waiver, attested/acting
approver = a declared approver at most `max_tiers_below` under the resolved tier, ratifier = the
resolved tier's role-holder. SoD is enforced at BOTH moments, unchanged — which is exactly why this
is not, and must never become, an SoD relaxation. Phase 2 (calendar-gated: New Year); its PLAN
inherits D3's machinery and adds only the schema field + the entry condition + the matrix tests.

### D6 — Binding discipline for every field this family adds

- **Only-when-supplied, enforced by oracle:** any new governance/schema field defaults to
  absent-and-unserialized so an unauthored config is BYTE-IDENTICAL before/after the schema change —
  the governance pin (`PipelineRun.governance_hash`, `runs.py:83-90`) hashes the resolved config,
  and an always-serialized `None` would silently change EVERY vertical's hash (the measured failure
  class the dispatch names). The acceptance oracle: resolved-config hash equality for all five
  non-fleet verticals across the diff (PLAN-0096 AC-2/AC-6).
- **The window is typed data, never prose:** `ratification_window_days` is a typed field;
  the ADR-0025 D4 prose-lint surface is unchanged (no ฿ amount, weight, or role token in any
  YAML free-text — including the rewritten E-3 rule `spec`).
- **Mid-flight edits fail closed as today:** authoring the window bumps the fleet governance hash;
  in-flight runs keep their pin (`assert_governance_pin` at resolve/resume, unchanged).

## Consequences

### Positive

- The partner's two live exception practices (roadside decide-first; sole-source) become
  **governed, logged, and exportable** instead of un-modelled — directly serving the 1-KPI charter
  (*every repair baht traceable: who approved, bought from whom, why* — Q16), where an unratified
  or sole-source case is a NAMED exception on the month-end export, not a hole.
- The decide-first shape is built ONCE and E-4 becomes a small Phase-2 delta (field + entry
  condition), not a second machine.
- Zero engine diff for E-3; no DB migration for E-2's run-state; today's non-waiver path stays
  byte-identical (behavioral only-when-supplied).

### Negative / risks

- **A provisional record is secondhand by construction** (the attested phone decision). The
  mitigations are structural — attested-approver fail-closed resolution, SoD at both moments,
  no `governed_decision` until ratify, overdue/refused always visible — but a lie at the recording
  seam ("owner said yes" when he did not) is caught at ratification, not before. That is the
  partner's own current practice made visible, not a new hole; it must be presented honestly.
- The taxonomy is extracted at N=2 confirmed windowed instances (E-2 confirmed + E-4 confirmed but
  unbuilt). Mitigated ADR-0025-style: instance-scoped fields, the generic registry eliminated
  (D1), Phase-2 build gated on the calendar-real second instance.
- A run can COMPLETE with ratification pending/overdue — deliberate (act-now), but any consumer
  that equates `COMPLETED` with "fully governed" must learn `ratification_state` (the export and
  render do; named in PLAN-0096).

### Neutral

- Extends ADR-0025 D3 and ADR-0026 D4; supersedes nothing. ADR merged before the implementation PR
  (CLAUDE.md §8). The seasonal hypothesis stays parked with a named owner question for the next
  partner visit.

## Open Questions (for Cray)

- **OQ-1 — E-2's ratifier: by construction (= `escalate_to`) or an explicit `ratified_by` field?**
  Recommendation: **by construction** — Q9/Q11 show the phone-decider and the paperwork-signer are
  the same authority, and a second role field is an unobserved degree of freedom. Add the field
  only if a real instance splits them.
- **OQ-2 — ratification refusal: export-flag only, or also an active surface (LINE alert to
  owner/accounting)?** Recommendation: **export flag + the existing overdue LINE reminder**;
  nothing auto-reverses. Escalation policy on refusal is partner conversation, not schema.
- **OQ-3 — where the E-3 basis lives:** row field `three_quote_basis` stamped by the evidence feed
  (recommended — rides existing audit paths, zero schema), vs a typed audit block. Recommendation:
  **row field**; revisit only if a second vertical needs a shared shape.

## Alternatives Considered

### Alternative 1: One generic exception-policy object/registry (all four instances, one model)
- Pros: one authoring surface; taxonomy as schema.
- Cons: abstraction at N≤2 per mechanism; divergent ratifier semantics (fixed role vs
  resolved-per-spend) forced into one shape; repeats the ADR-0025 Rule-of-Three tension without its
  forcing defect.
- Why rejected: the shared thing is the run-state (D3), built once; the authored surfaces stay
  per-mechanism minimal (D2).

### Alternative 2: Suspend-until-ratified (no provisional execution)
- Pros: strictly fail-closed; no secondhand record.
- Cons: contradicts the observed practice this exists to govern (Q9 "เคาะก่อน ทำเอกสารทีหลัง" —
  the truck is on the hard shoulder; the repair will not wait for the record).
- Why rejected: it models the rule the partner does NOT follow; the honest system records reality
  and makes the catch-up bounded + visible.

### Alternative 3: Auto-flip state at window expiry (stored `overdue`, or auto-fail)
- Pros: overdue is queryable without a clock argument.
- Cons: an actor-less state mutation (no principal performed it) breaking the audit model;
  auto-FAIL is worse — the money is spent, so "failed" would falsify what happened.
- Why rejected: D3.6 computes state purely from the persisted record + `now`; fail-visible.

### Alternative 4: Route E-3 through the emergency waiver (`relaxes: [sole_source]` exists already)
- Pros: zero new concepts; `SOLE_SOURCE` is a `RelaxableConstraint` member today (`spec.py:922`).
- Cons: forces escalation + emergency framing onto a standing no-escalation practice (Q10);
  `DoaLadder` has one waiver slot, so overloading it entangles the two exceptions' semantics.
- Why rejected: D4's evidence-alternative matches the gate's designed consumption and the
  partner's actual rule.

### Alternative 5: A ฿ cap field on the waiver
- Refuted by the partner directly (Q11) — not deferred, eliminated (D1). Recording this so the
  hypothesis does not silently return as a "safe default".

### Alternative 6: A new `PipelineRunStatus` (e.g. `ratification_pending`)
- Pros: run-level visibility for free.
- Cons: freezes a cross-cutting obligation into a lifecycle enum; collides with `COMPLETED`
  semantics; migration surface for zero information not derivable from step audit.
- Why rejected: computed `ratification_state` (D3.6) + export/render consumption.

## References

- Dispatch: `.claude/handoffs/session-184/2026-07-28-1704-code-cowork-fleet-pilot-adr0034-plan0096-dispatch.md`
- Partner grounding (gitignored, read as attachments):
  `docs/research/private/2026-07-28-fleet-partner-answers-analysis.md` (READ-FIRST answer→decision
  mapping; Q9/Q10/Q11/Q14/Q16 anchors) · `2026-07-28-fleet-partner-discovery-instrument.md`
- ADR-0025 (`docs/adr/0025-at2-managerial-layer.md`) — D2/D3/D4 the substrate + the
  unrepresentability this ADR preserves; ADR-0026 D4 (live run-checks reused); ADR-0032 D1
  (1-KPI charter); PLAN-0075 SD-6(a) (tie-at-act-time honesty); PLAN-0047 Step 3 (gate state
  machine mirrored by `ratify_gated_step`)
- Code (verified at `7b84fa2`): `spec.py:904-914, 917-922, 925-1001, 1028, 1031-1060, 1263-1269` ·
  `runs.py:36-59, 83-90` · `action_step.py::resolve_gated_step` (RF-1 / pin / SoD / tier-authority /
  two-phase) · `rule_gate.py::evaluate_compliance` (fail-closed signal consumption) ·
  `governance_step.py` (SD-6(a) comments; `_rule_gate` tagging) ·
  `verticals/fleet_maintenance/procedures.yaml` (gate sequence; the recorded "฿ half lives in the
  feed" note)
- CLAUDE.md §6 (governance artifact flow), §8 (offline oracle is the gate)

## Implementation Notes

PLAN-0096 (drafted alongside) owns Phase 1: the D2 Door-1 field, the full D3 machinery with its
case-coverage matrix, the D4 evidence path, and the D6 hash-equality oracle. Phase 2 (its own
PLAN, pre-New-Year): D2 Door 2 / D5. Status flips Proposed → Accepted on Cray's ratification; Code
commits via PR (ADR-009 D2). AI-assisted (Cowork drafter); no `Co-Authored-By` (CLAUDE.md §7).
