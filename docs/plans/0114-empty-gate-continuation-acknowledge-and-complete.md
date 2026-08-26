# PLAN-0114: Empty-gate continuation — acknowledge-and-complete through the product surface

**Status:** Draft
**Owner:** Claude Code
**Created:** 2026-08-24
**Related ADRs:** ADR-016 (D4 — **unchanged**; the reading is recorded in §Mechanism), ADR-0019 (watch → gated escalation — unchanged), ADR-007 (proposal envelope — untouched), ADR-0026 (D6 — the echo-only auto-downstream-of-a-gate guarantee, load-bearing for SD-3)
**Related PLANs:** PLAN-0113 (SD-3, the origin), PLAN-0022 (human_task parity — the plain-resume continuation contract), PLAN-0047 (the gate state machine), PLAN-0054 (cancel — the governed run-level write this PLAN mirrors)

> **Drafting provenance (ADR-012 D4.3).** Drafted (uncommitted) by the in-harness
> `plan-drafter` subagent from the s252 Code dispatch
> (`.claude/handoffs/session-252/2026-08-24-2230-code-plan-drafter-empty-gate-continuation-dispatch.md`),
> fact pack re-verified against the tree on disk. Outline originator: Code (s252).
> Independent reviewer: Cray at PR merge. Separation: INTACT.
>
> **Post-draft amendment (Code, s253, pre-Step-1).** Three edits, each grounded in a
> measurement of the live tree at `c49872a`, none changing the ruling, the taken
> mechanism, the scope, or any SD outcome:
>
> 1. **AC-2(a)'s RED-witness recipe** — `resume_run` carries a second, pre-existing
>    guard the draft did not account for, so the drafted probe could not have witnessed
>    what it claimed. The repair went to the **instrument**, never to the criterion.
> 2. **One SD-3 sentence** — *"the ONLY thing keeping it from becoming a resolve
>    bypass"* is measurably too strong; the seam is defense-in-depth.
> 3. **Guard 3's key** — `actor_person_id`, not a resolved `Person`. Keying on the
>    `Person` would permanently refuse 3 of the 18 gated steps, contradicting the
>    LOCKED SD-3; where mechanism prose and a LOCKED SD disagree, the SD wins.
>
> Author≠reviewer: Code authored this amendment; Cray reviews it at PR merge.

## The ruling this PLAN executes (LOCKED — do not re-open)

**PLAN-0113 SD-3 is RULED (b) (Cray, typed, s252, 2026-08-24):** a run whose gate carries
nothing decidable must reach **`completed`**, not sit unresolvable. Cray's stated reason
(*"เราชอบ 'เหตุผล 1'"*) is the **artifact argument**: a sub-ceiling case genuinely has
nothing to approve, so a completed run recording *"checked — ฿4,500 is inside the head
mechanic's own authority"* is a more valuable governance artifact than a stuck one.

Three boundary conditions on the ruling (from the dispatch, binding here):

- **The OUTCOME is ruled; the MECHANISM is not.** The mechanism priced under SD-3's
  option (b) at the time — "engine change to the gate shape" — is **not** what ships:
  grounding showed the engine already sanctions completion (below); the gap is
  reachability. The mechanism is this PLAN's design, ratified with the PLAN.
- **The trace-entry idea is NOT ratified.** Cray endorsed reason 1, not a trace entry.
  What the completed run records is SD-2 below.
- **`POST /runs/{id}/cancel` is not the answer.** It works on exactly a `waiting_human`
  run but records *abandonment* for a case that was checked and cleared — the misleading
  artifact the ruling rejects.

## Context — verified facts (all anchors re-checked s252 on the drafting tree)

- **The semantic:** ADR-0016 D4 (`docs/adr/0016-governed-procedure-engine.md:2463-2465`,
  Status Accepted `:3`): *"A `gated` or `human_task` step suspends the run at
  `status = waiting_human` … and the run resumes when the human acts."*
- **The implementation:** `_suspends` (`services/engine/procedures/orchestrator.py:632-644`)
  is purely structural — `HUMAN_TASK`, or `ACTION` + `Autonomy.GATED`. It never inspects
  the input or output set. **This PLAN does not touch it.**
- **The engine already sanctions completion.** `_has_decidable_proposals`
  (`services/engine/procedures/persistence.py:277-287`) defines the no-decision suspend,
  and `resume_run` (`:349`; the no-decision branch `:436-458`) completes such a run on a
  plain resume — "the documented plain-resume continuation contract" (PLAN-0022 parity).
  Two shipped tests lock this: `tests/services/db/test_gate_state_machine.py:260-282`
  (`test_empty_proposal_suspend_keeps_plain_resume` — parks, then plain resume →
  `COMPLETED`) and `tests/services/engine/procedures/test_watch_gated_routing.py:187-211`
  (`test_empty_watch_set_still_suspends_with_no_proposals`). **Both must stay green,
  unchanged.**
- **The real gap is reachability.** `resume_run`'s only non-test production call site is
  `services/api/routers/runs.py:551`, **inside** `POST /runs/{run_id}/gate/resolve`
  (`:461`) — which calls `resolve_gated_step` first, and that raises `"has no proposed
  actions to resolve"` on an empty `output_set`
  (`services/engine/procedures/action_step.py:830-832`) → HTTP 409, before `resume_run`
  is ever reached. Routes on runs today: `GET /runs` (`:273`), `GET /runs/{run_id}`
  (`:356`), `POST /procedures/{procedure_id}/run` (`:393`), `/gate/resolve` (`:461`),
  `/cancel` (`:577`). There is no plain-continuation route. So the engine's own
  sanctioned exit is **unreachable from the product surface**.
- **The concrete case:** under PLAN-0113 scoping, a **sub-ceiling** fleet acceptance
  (฿4,500 vs the ฿5,001 ceiling) runs `intake` (1 row) → `judge` (`ok`) → `reshape`
  (`where: {verdict: breach}`, 0 rows) → `quote_gate` → `approve` parks with an empty
  `output_set`. Measured s252. Asserted today by the deliberate tripwire
  `test_an_empty_gate_cannot_be_resolved_so_the_run_is_a_dead_end`
  (`tests/api/test_case_acceptance_fires_governed_run_scenario.py:415-449`), which names
  SD-3 and expects to be re-authored by this PLAN. Its sibling
  `test_a_sub_ceiling_acceptance_reaches_the_gate_with_no_proposals` (`:385-412`)
  asserts the empty proposal list and **must survive unchanged** (the gate still parks).
- **The surface this fires on:** **18** `autonomy: gated` steps across all 6 verticals
  (fleet 4, procurement 6, supply_chain 3, building_materials 2, aquaculture 2,
  energy 1; `grep -rn "autonomy: gated" verticals/` — 19 hits incl. one comment in
  `verticals/fleet_maintenance/operate_seed.py:643`). Grounded negative: `kind:
  human_task` has **0** uses in `verticals/` — D4's other suspending kind is currently
  theoretical, but the mechanism below covers it by construction (a non-proposal
  artifact is the same no-decision suspend).
- **Audit substrate:** `services/db/audit_log.py` treats `action` as an opaque string
  (no enumeration; verified `:134,193,202,247`) — a new audit action rides the
  tamper-evident chain without touching `GET /audit/verify`.

## Goal

Make a run parked at a gate with **no decidable proposals** reachable to **`completed`**
through the product surface: a new governed, RF-1-guarded, **fail-closed**
acknowledge-and-continue seam — a persistence chokepoint plus
`POST /runs/{run_id}/continue` — that exposes the engine's *existing* plain-resume
continuation contract, records an explicit *"checked — nothing to approve"*
acknowledgment naming the accountable human at both audit levels, and changes **nothing**
about `_suspends`, `resolve_gated_step`, the resolve route, or ADR-0016 D4. The parked
run stays loud; a human explicitly closes it; the completed run is the artifact Cray's
ruling values.

## Mechanism (decided under the dispatch's L-2 mandate; pricing recorded)

Three shapes were priced (dispatch S-1):

| Shape | Priced | Verdict |
|---|---|---|
| **(i) New route** `POST /runs/{id}/continue` → `resume_run` when nothing is decidable | Accountable human still acts (RF-1, mirrors cancel/resolve); the parked run stays **visible** until acknowledged; zero change to resolve semantics; smallest blast radius over the 18 gated steps (non-empty gates are 409-refused, fail-closed) | **TAKEN** |
| (ii) `/gate/resolve` falls through to continuation instead of 409-ing when nothing is decidable | Keeps RF-1, but overloads "resolve" with a non-decision, silently changes an existing route's contract (today's 409 is load-bearing for clients and for the tripwire's discriminator), and entangles the SoD/tier resolve machinery with a case that has no decision to govern | rejected |
| (iii) Auto-continue at suspension time (never parks) | Fastest for the visitor, but reddens both shipped parity tests, contradicts PLAN-0022 / ADR-0019 ratified behaviour (→ the dispatch's R-2 routing), removes the human act ADR-0016 D4 promises, and is maximally exposed to the loudness hazard below | rejected |

**The loudness answer (dispatch S-2), stated in writing.**
`_has_decidable_proposals` cannot distinguish *"correctly nothing to approve"* from
*"a broken executor produced nothing"* — both are an empty `output_set` — and this PLAN
does **not** claim to distinguish them in-engine. The design's answer is posture, not
detection: the run **still parks, loudly and visibly** (nothing auto-completes), and the
discriminator is the **accountable human**, who acknowledges with the run's per-step
evidence in front of them — the run detail (`GET /runs/{run_id}`, `runs.py:356-390`)
already surfaces every step's status and audit, so *"intake 1 → judge ok → reshape 0"*
(correctly empty) reads differently from *"intake 0"* (a read that broke). A broken
executor therefore still produces a parked run a human must look at; what changes is
only that the human gains an honest exit besides `cancel`. Shape (iii) was rejected
precisely because it forfeits this. This is why R-3 does not hold.

**Why no ADR (dispatch S-3), stated plainly.** ADR-0016 D4 stays true verbatim under
shape (i): the gated step still **suspends** at `waiting_human`, and the run still
**resumes when the human acts** — the act is an acknowledgment instead of an approval,
exactly the plain-resume continuation the engine has documented since PLAN-0022/0047.
`_suspends` is untouched; both parity tests stay green. **STOP-tripwire:** if
implementation discovers it must modify `_suspends`, redden either parity test, or
change what D4 asserts, **stop and re-route** — that is an ADR-0016 amendment, which
must merge before the implementation PR (CLAUDE.md §8), i.e. the dispatch's R-2
condition materializing late.

**The seam, concretely** (contract, not line-by-line implementation):

1. **Persistence chokepoint** — a new function in
   `services/engine/procedures/persistence.py` (suggested name
   `continue_no_decision_run`), the library-level twin of `cancel_run` (`:491-518`) /
   `resolve_gated_step`:
   - loads the run; refuses unless `status = waiting_human` (`ProcedureError`);
   - finds the suspended step (`suspended_step_result` — exactly-one enforced);
   - **fail-closed guard 1:** `_has_decidable_proposals(artifact)` true → refuse:
     *"this gate holds decidable proposals — resolve it through resolve_gated_step"*.
     The continue seam is **never** a resolve bypass;
   - **fail-closed guard 2:** `artifact is None` (the escalated-failure suspend,
     `on_failure = escalate_to_human`) → refuse. That is a *retry* surface, not an
     acknowledgment — out of scope here, recorded as OQ-1;
   - **fail-closed guard 3 (RF-1, library level):** the accountable human is missing →
     refuse, so a direct caller / scheduler cannot acknowledge with no accountable
     human. (`resume_run` itself keeps its `principal: Person | None` signature — the
     shipped parity tests call it bare and must stay green; the RF-1 floor lives in the
     NEW chokepoint, which is the only surface this PLAN exposes.)
     🔴 **Keyed on `actor_person_id: str | None`, NOT on a resolved `Person`
     (Code, s253, pre-Step-1 — measured).** The draft said *"`principal is None` →
     `GateApproverError`, mirroring `resolve_gated_step`'s posture"*. Measured:
     `AuthContext` (`services/api/auth.py:37-46`) documents that `person_id` is `None`
     **only** when authn is disabled, while `person` is `None` when authn is disabled
     **OR when the active vertical ships no authored principal set**. Only **4 of 6**
     verticals ship a `principals:` block (`fleet_maintenance`, `building_materials`,
     `supply_chain`, `procurement`; **not** `aquaculture`, **not** `energy` — control:
     all 6 ship a `procedures.yaml`, so the 4 is not a missing-file artifact). Keying
     guard 3 on the `Person` would therefore refuse `/continue` **permanently** on the
     **3 of 18** gated steps in those two verticals (aquaculture 2, energy 1) even for a
     correctly authenticated human — a guard that can never pass is a defect, not a
     floor, and it contradicts SD-3's ruled *"any authenticated human"*. Where this
     mechanism prose and the LOCKED SD-3 disagree, **the SD wins** (CLAUDE.md §1
     precedence): SD-3 ruled the **cancel posture**, and `cancel_run`
     (`persistence.py:491-506`) already states the reason in its own docstring —
     *"cancel has no SoD check, so it needs the id, not the resolved `Person`"*. So the
     chokepoint mirrors `cancel_run`'s `actor_person_id` attribution and the `/cancel`
     route's RF-1 403 (`runs.py:592-599`), not `resolve_gated_step`'s `Person`
     resolution. `auth.person` is still threaded into `resume_run` when it resolves, so
     PLAN-0053 AC-3's non-null `run_resumed` actor (test-enforced,
     `tests/services/db/test_procedure_action_gate.py:241-291`) is preserved wherever it
     can hold; attribution never depends on it, because the SD-2
     `run_continued_no_decision` row always carries the id.
     ⚠️ **Step 2 landmine, recorded:** the new audit action may need a row in the
     per-action payload-schema registry at
     `tests/api/test_visitor_case_to_monitor_scenario.py:174`, whose sibling at `:460`
     asserts an **exact** action set — the same shape as the house "a new trace kind
     needs its UI label" pairing. Check before assuming it is inert;
   - takes a caller-supplied `step_id` and refuses on mismatch with the actually
     suspended step — the acknowledging human names what they believe they are
     acknowledging (cheap guard against acting on a run that moved between read and
     POST; the optimistic-lock version covers concurrent writers as today);
   - **records the acknowledgment** (shape per SD-2), then delegates to `resume_run`
     with the principal threaded — one commit posture, mirroring the
     `run_resumed`/`run_cancelled` idiom. Implementation note: a step's `audit` dict is
     a JSON column — mirror `resolve_gated_step`'s `governed_decision` write idiom
     (reassign / flag-modified, never bare in-place mutation).
2. **HTTP route** — `POST /runs/{run_id}/continue` in `services/api/routers/runs.py`,
   body `{"step_id": …}`, response `ContinueRunResponse` (`run_id`, `continued_step`,
   `run_status`, `steps` — mirrors `GateResolveResponse`). Error mapping mirrors the
   siblings: 403 no authenticated human (RF-1, mirrors cancel `:592-599`), 404 unknown
   run, 409 `ProcedureError` / `StaleDataError` (concurrent writer loses cleanly).
   <br>**Shipped with one field more than this list (Code, s256):** `suspended_step`,
   which `GateResolveResponse` — the mirror this line names — already carries. A
   continuation is not a completion: the run parks again whenever the next step is also
   gated, and a response that could not say so would report a continued run as finished.
   Under **SD-4** it is load-bearing rather than cosmetic — it is the field the UI's walk
   reads to find the next gate.
   <br>🔴 Also shipped: the endpoint's `except NoDecisionApproverError` arm must precede
   its `except ProcedureError` arm, because the former **subclasses** the latter and an
   arm placed second silently degrades the RF-1 403 to a 409.
3. **UI affordance** — ⚠️ **amended by SD-4 (Cray, typed, s256): option (B), one button
   that walks the empty gates.** The paragraph below is the text as drafted (option A,
   one button per gate); it is retained verbatim per the PLAN-0111 convention and is
   superseded by SD-4 for Step 3. The reason the question was re-put is recorded there:
   AC-1's one-POST premise was **measured false** in Step 2.
   <br>🔴 **Two factual corrections, measured at the tree (Code, s256, Step 3).**
   **(1) The tab labels are swapped.** `app.js:12-20` registers **H = Monitor
   (`view-monitor.js`)** and **G = Governance Moment (`view-hero.js`)**; the draft calls
   view-hero "the Tab H surface". The dead end was observed on the **Monitor**, and that
   is where the affordance ships. **(2) `view-hero.js` is OUT OF SCOPE, and this is a
   scope cut, not an omission.** Its Act panel (`renderActPanel`) is reached from
   `render()` **only** on the procurement path and **only** when `mode === 'event'` —
   `renderFleet()` (`:580-614`) never calls it. That panel drives the scripted
   `/demo/hero/event` beat-3 run, whose gate carries a proposal **by construction**; an
   acknowledge affordance there would be an affordance nothing can reach. `api.js`
   therefore gains **no** `continueRun` helper — a comment records the refusal in place,
   mirroring how that module already refuses an unused export download helper.
   <br>The two operate surfaces that POST `gate/resolve` today
   (`services/api/static/assets/view-hero.js:286`-area — the Tab H surface the dead-end
   was observed on — and `services/api/static/assets/view-monitor.js:133`): when a
   `waiting_human` run's `proposals` list is empty, render an explicit
   **"Acknowledge — nothing to approve"** action posting `/continue` (beside the
   existing Cancel), through the same auth seam (`auth.js`). Per-file `?v=` cache-bust
   counters bumped.

## Acceptance Criteria

Probe discipline per CLAUDE.md §8: every load-bearing green below is witnessed RED by a
mutation of what the assertion is about, one probe per assertion; the battery's own
coverage may be computed with `tools/probe_coverage.py` (shipped s252, lesson #0047 §6).

> 🔴 **AC-1's "one POST" premise was MEASURED FALSE (Code, s256, Step 2).** The hero
> spine is `request -> approve -> fulfill` and **`fulfill` is `autonomy: gated` too**;
> `_suspends` (`orchestrator.py:632-644`) never inspects the input set, so acknowledging
> `approve` parks the run again at `fulfill` rather than completing it. The sub-ceiling
> run reaches `completed` after **TWO** acknowledgments — the same G-12 shape
> `test_the_full_walk_both_gates_the_link_row_and_the_case_surface` already records for
> the resolve path, which the draft did not carry across to the continue path. The
> **outcome** AC-1 asserts (`completed`, reachable through the product surface) is
> unchanged and is met; only the *arity* was wrong. The shipped test asserts the measured
> walk as a list (`acknowledged == [_APPROVE, _FULFILL]`) so the count cannot drift
> silently. This is what re-opened the Step 3 UI question — see **SD-4**.

- [x] **AC-1 — the empty-gate run completes through the product surface.**
  *(CLOSED s256 — Step 2. The sub-ceiling run reaches `completed` through the product
  surface, asserted by `test_the_empty_gate_is_acknowledged_and_the_run_reaches_completed`,
  and verified LIVE in the preview on the fleet published profile. **Arity corrected:** TWO
  acknowledgments, measured, asserted as a list so the count cannot drift.)*
  Scenario test
  (real producer → real consumer, realistic data): the sub-ceiling fleet acceptance
  parks at `approve` with `proposals == []` (the existing helper
  `_fire_sub_ceiling_with_a_breaching_control` — its breaching control run is the
  positive control that the same fixtures CAN produce a proposal), then an
  authenticated human POSTs `/runs/{id}/continue` → **200**, `run_status = completed`,
  and `GET /runs/{id}` shows the run completed with the `judge` step's `ok` verdict
  still on the record. The current tripwire
  `test_an_empty_gate_cannot_be_resolved_so_the_run_is_a_dead_end` reddens loudly at
  this step **by design** and is re-authored (Step 2) — that is its documented purpose.
- [x] **AC-2 — the seam is fail-closed, with a positive control.**
  *(CLOSED s256 — Step 2. Five HTTP arms shipped (a/b/c/d + the route's own 404).
  Battery through `tools/probe_battery/`: 4 WITNESSED at their own declared assertion, plus
  one declared-GREEN isolation control. 🔴 (a) **and (b)** assert the detail string rather
  than the status code — the PLAN warned of the one-code-two-causes shape for (a) only, and
  it repeats at (b): RF-1 is guarded twice and BOTH layers answer 403, so `== 403` stays
  green with either guard deleted.)*
  Battery, one probe
  per assertion:
  (a) 🔴 a gate **with** decidable proposals is refused on `/continue` — asserted on the
  **detail string naming the chokepoint's own mechanism** (`"this gate holds decidable
  proposals"`), **not** on the bare 409. **Measured correction (Code, s253, pre-Step-1):**
  the status code is not a discriminator here — `resume_run` already carries a *second*
  guard (`persistence.py:447-452`: `_has_decidable_proposals` true **and** `status not in
  _ADVANCING_STATUSES = {RESOLVED, RESOLVED_PROVISIONAL}` → `ProcedureError` *"suspended
  with undecided proposals"*), which `runs.py:561` also maps to **409**. A `/continue`
  that skipped chokepoint guard 1 would therefore still answer 409 and a status-code
  assertion would stay **green** — the s252 failure-#1 shape (one code, two causes,
  discriminating neither). RED witness: scratch-disable the chokepoint's
  `_has_decidable_proposals` guard → the observable detail flips to `resume_run`'s
  *"suspended with undecided proposals"* → (a) reddens **on that assertion**, while AC-1
  stays green, isolating the probe;
  (b) unauthenticated / authn-off → **403** (RF-1);
  (c) a non-`waiting_human` run → **409**;
  (d) a `step_id` naming a step other than the suspended one → **409**;
  (e) an escalated-failure suspend (`artifact is None`) → **409** (OQ-1 stays a
  recorded gap, not a silent hole).
- [x] **AC-3 — the completed run is the artifact the ruling values.**
  *(CLOSED s256 — writes in Step 1, **retrieval proven LIVE** in Step 3. The real
  tamper-evident chain carries `run_continued_no_decision` on `approve` AND on `fulfill`,
  each naming the acting human with `actor_kind: human`; both step `audit` dicts carry the
  acknowledgment block, readable through `GET /runs/{run_id}`. `GET /audit/verify` returned
  `intact: true` over 50 rows — the new action rides the chain without breaking it.)*
  After AC-1's
  continue: the tamper-evident audit chain carries the new run-level acknowledgment row
  (SD-2 shape) naming the actor and the acknowledged step with `proposal_count: 0`,
  **and** the gate step's own `audit` dict carries the acknowledgment block, retrieved
  through the existing surfaces — `GET /runs/{run_id}` per-step audit and the monitor's
  "Show audit" toggle (`view-monitor.js:378-389`), plus `run_resumed` from
  `resume_run` as today. `GET /audit/verify` still verifies. RED witness: drop the
  audit write → the presence assertion reddens. (A reader of the completed run must be
  able to reconstruct *"checked — nothing to approve, acknowledged by X"*, not merely
  *"completed"*.)
- [x] **AC-4 — blast radius bounded, with a positive control (the PLAN-0113 AC-4
  precedent).**
  *(CLOSED s256 — Step 4. `orchestrator.py` and `action_step.py` **byte-identical** vs
  `origin/main` (empty diffs), the empty-gate raise present verbatim, suite 4460 → 4466 with
  0 failed. Positive control through the driver: **both** parity tests witnessed RED under a
  `_suspends` mutation, tree restored byte-identical. 🔴 The watch half **MISFIRED first** —
  re-addressed from the CODE, not the outcome: that module's suspend guard lives in
  `_run_to_escalation:148`, which runs before the test body, so the body's own assert is
  structurally unreachable under this mutation.)*
  `_suspends` and `resolve_gated_step` are byte-identical (empty
  `git diff` on `orchestrator.py`; `action_step.py`'s empty-gate raise untouched); the
  two parity tests (`test_gate_state_machine.py:260-282`,
  `test_watch_gated_routing.py:187-211`) and the sibling
  `test_a_sub_ceiling_acceptance_reaches_the_gate_with_no_proposals` pass **unchanged**;
  `/gate/resolve` on an empty gate still answers 409 `"no proposed actions to resolve"`
  (asserted in the re-authored test — continue is a new exit, not a changed resolve);
  full suite green vs the Step 0 baseline. 🔴 Positive control (a green suite proves
  nothing about "unchanged" without it): scratch-mutate `_suspends` to consult the
  output set → the watch parity test reddens; restore (restore from the scratch copy,
  verify byte-identical).
- [x] **AC-5 — the dead-end is closed where it was observed.**
  *(CLOSED s256 — Step 3, per SD-4(B). Verified in the preview against a seeded
  sub-ceiling run: ONE click settled it, the panel read "Acknowledged — nothing to approve.
  Run completed. (2 empty gates)". Positive control on the same surface: a gate holding
  three real proposals renders Submit and **not** the acknowledge button. 🔴 **Scope cut,
  not an omission:** `view-hero.js` is Tab **G**, its Act panel is procurement-only and its
  gate carries a proposal by construction — an affordance there would be unreachable.
  🔴 Also closed a **live-only** gap the offline suite could not see: the published ingress
  allowlist is default-deny, so the button would have 404'd at the Cloudflare edge.)*
  Both operate surfaces
  render the acknowledge affordance exactly when a `waiting_human` run has zero
  proposals, wired to `/continue`; `?v=` bumped per touched file; verified in the
  preview against a seeded sub-ceiling run. **Per SD-4 the affordance is ONE button that
  walks the empty gates**, so the preview check is: one click settles the fleet hero, the
  walk **halts** at a gate carrying a real proposal (positive control — the breaching
  control run must still show the ordinary resolve affordance, never the acknowledge
  one), and the audit trail still carries **one acknowledgment row per gate walked**.
- [x] **AC-6 — the record trail is consistent.**
  *(CLOSED s256 — Step 5. 🔴 **OQ-2 resolved at the artifact, and it said DO NOT
  WRITE:** PR #1280 **did** land the ruling — `done/0113-…md` carries the RULED (b)
  marker — so this was a reconcile, not a re-write. What was genuinely missing was
  any mention of PLAN-0114 at all (`grep 0114` returned zero hits); that pointer is
  now added, additively, and carries the two things a reader would otherwise inherit
  wrong: the mechanism is NOT the `_suspends` change SD-3 priced, and the ruling's
  own arity was off by one. The stale docstring was refreshed in Step 2. STATUS
  reconciled to s256, with the session-252 block rotated out under R2/R6 and
  verified **by content** — byte-identical to `git show HEAD:docs/STATUS.md` — not
  by presence.)*
  PLAN-0113 SD-3 carries the RULED (b)
  marker + a pointer to this PLAN (additive, ruled history untouched verbatim — the
  PLAN-0111 convention; **check first**: the dispatch says PR #1280 recorded the
  ruling, but on the drafting tree `0113-…md:431` still reads "SD-3 — OPEN" — reconcile
  rather than double-write). The stale docstring in
  `test_a_visitor_fired_run_is_never_a_dead_end`
  (`test_case_acceptance_fires_governed_run_scenario.py:570-573`, "OPEN as PLAN-0113
  SD-3") is refreshed. STATUS.md In-Flight updated.

## Out of Scope

- ❌ **Changing `_suspends` / the gate shape** (`orchestrator.py:632-644`) — the
  STOP-tripwire in §Mechanism. Any need to touch it re-routes this work through an
  ADR-0016 amendment first.
- ❌ **Auto-continue at suspension** (shape (iii)) — rejected on the loudness hazard;
  re-opening it is a Cray decision, not an implementation drift.
- ❌ **The escalated-failure suspend** (`artifact is None`) — today it is equally
  API-dead-ended (resolve 409s on its empty `output_set`; only cancel exits), but its
  honest exit is a *retry*, a different semantic. Recorded as OQ-1; `/continue` refuses
  it (AC-2e).
- ❌ **In-engine discrimination of "correctly empty" vs "executor broke"** — delegated
  to the acknowledging human by design (§Mechanism, the loudness answer).
- ❌ **An ADR-0016 amendment** — not needed under the taken mechanism (§Mechanism).
- ❌ **Trace-entry emission for the continuation** — not ratified (LOCKED L-3); SD-2's
  recommended record shape uses the audit substrate instead. If Cray rules a trace
  entry into SD-2, note a new trace kind needs its UI label + cache-bust (house
  convention).

## Steps

### Step 0 — Baseline

Full `pytest tests/`, `mypy --strict services/ verticals/`, bare `ruff check .`,
`ruff format --check .`; record exact counts. The offline gate must match CI scope — no
path-scoped shortcuts.

### Step 1 — The persistence chokepoint (AC-2 guards, AC-3 record)

`continue_no_decision_run` in `persistence.py` per §Mechanism: the three fail-closed
guards + `step_id` match + the SD-2 acknowledgment writes + delegate to `resume_run`
(principal threaded). DB-level tests: the guards' battery (each refusal one probe), the
happy path to `COMPLETED`, the audit rows/block present, `StaleDataError` on a
concurrent writer. The two shipped parity tests are the *unchanged-green* half of AC-4
from this step onward.

### Step 2 — The HTTP route + scenario re-author (AC-1, AC-2, AC-4's resolve half)

`POST /runs/{run_id}/continue` + `ContinueRunResponse` + error mapping per §Mechanism.
Re-author the tripwire: `test_an_empty_gate_cannot_be_resolved_so_the_run_is_a_dead_end`
becomes the closure's own scenario — (1) `/gate/resolve` on the empty gate **still**
409s `"no proposed actions to resolve"` (resolve unchanged — the discriminating detail
string, not the bare status code, per its current caution), (2) `/continue` as the
authenticated human → completed (AC-1), (3) `/continue` on the breaching control run →
409 (AC-2a). The sibling no-proposals test survives byte-identical.

### Step 3 — UI affordance (AC-5)

Per §Mechanism item 3 **as amended by SD-4** — one button that walks the empty gates,
bounded, halting at the first gate carrying a real proposal. Verify against a seeded
sub-ceiling run in the preview (the fleet hero walks **two** gates, so the check is that
one click settles the run and the audit trail still carries **two** acknowledgment rows);
`?v=` bumps per file.

### Step 4 — Regression gate (AC-4)

Full suite vs Step 0 baseline; byte-diff checks on `orchestrator.py` /
`action_step.py`'s raise; the scratch positive control on `_suspends` (mutate → watch
parity test reddens → restore byte-identical). Optionally run
`tools/probe_coverage.py` over the new battery and name any never-reddened claim with
its reason (lesson #0047 §6).

### Step 5 — Records (AC-6)

PLAN-0113 SD-3 RULED marker + pointer (additive; reconcile with PR #1280 first — see
AC-6), the stale docstring refresh, STATUS.md. Then PR per CLAUDE.md §7; this PLAN
`git mv` to `done/` at closeout.

## Surfaced decisions

- **SD-1 — DECIDED by this draft (under the dispatch's L-2 "design the mechanism freely"
  mandate): shape (i), the new route + chokepoint.** Pricing recorded in §Mechanism;
  ratified by Cray with this PLAN. Re-opening (ii)/(iii) after ratification is a new
  dispatch, not an implementation choice.
- **SD-2 — RULED (Cray, typed, s252, 2026-08-24): the recommendation, dual audit.**
  Cray's words: *"เอาตามที่แนะนำ: audit สองชั้น"*. **LOCKED for Step 1 and AC-3.** Both
  levels are required — a chain row alone fails L-1's artifact test (the reader learns
  "completed", not "checked"), and a step-`audit` block alone is not tamper-evident.
  🔴 The **no-trace-entry** half is ruled too: it follows from taking the recommendation
  as posed, and L-3 already forbade pre-deciding a trace entry. If a trace entry is ever
  wanted, it is a NEW surfaced decision — and it would need a `trace-kinds.js` registry
  row plus a per-file `?v=` bump (house convention; the AST guard enforces the pairing
  bidirectionally).
  <br>_The option text as posed is retained verbatim below (the PLAN-0111 convention)._
  <br>**Recommendation: dual audit, no trace entry** — (1) a run-level audit action
  `run_continued_no_decision` (payload: `step_id`, `proposal_count: 0`,
  `actor_kind: "human"`, actor id) on the tamper-evident chain, beside the existing
  `run_resumed`; (2) an acknowledgment block (e.g. `no_decision_continuation`:
  acknowledged-by + timestamp) in the gate step's own `audit` dict, because that dict
  already has a retrieval surface (run detail + the monitor's "Show audit" toggle) —
  recording is not retrieval, and this shape needs zero new read machinery.
  *Alternatives:* a trace entry (L-3 explicitly unratified; needs a UI label +
  cache-bust); a `governed_decision` record (dishonest — no decision was exercised);
  the bare `run_resumed` row alone (fails L-1 — the reader learns "completed", not
  "checked"). Why Cray: this is the artifact the ruling was *about*.
- **SD-3 — RULED (Cray, typed, s252, 2026-08-24): the recommendation, the RF-1 floor.**
  Cray's words: *"เอาตามที่แนะนำ: คนที่ authenticate แล้วคนไหนก็ได้"*. **LOCKED for Step 1
  and AC-2(b).** `/continue` requires an authenticated human and **nothing more** — no
  tier resolution, no SoD check. The rejected alternative (restrict to the gate's
  resolver population) is retained verbatim below and is NOT to be reintroduced as an
  implementation detail.
  🔴 **The guard this ruling makes load-bearing:** with the approver population no longer
  gating `/continue`, fail-closed guard 1 (`_has_decidable_proposals` true → refuse) is
  what keeps it from becoming a resolve bypass. AC-2(a) is therefore not one assertion
  among five — it is the security boundary of the whole seam, and its witnessed-RED probe
  is mandatory.
  <br>**Corrected on measurement (Code, s253, pre-Step-1).** This was drafted as *"the
  ONLY thing keeping it from becoming a resolve bypass"*; measured against the tree that
  is too strong. `resume_run` already carries an independent second layer refusing a
  decidable, unresolved gate (`persistence.py:447-452`), so the seam is defense-in-depth,
  not single-guarded. The correction **lowers the residual risk and raises the probe
  bar**: because both layers answer 409, AC-2(a) witnesses nothing unless it asserts the
  chokepoint's own detail string — see AC-2(a). Guard 2 (`artifact is None` — `resume_run`
  would *retry*, a different observable) and guard 3 (RF-1 — `resume_run` takes
  `principal: Person | None` and the shipped parity tests call it bare) have **no** second
  layer and remain genuinely single-guarded. The SD-3 ruling itself is unchanged.
  <br>_The option text as posed is retained verbatim below (the PLAN-0111 convention)._
  <br>**Recommendation: any authenticated
  human (RF-1 floor) — the cancel posture (PLAN-0054), not the resolve posture.**
  Reasoning: no decision is exercised, no proposal is approved, and nothing operational
  can execute from an empty set on the continuation (auto steps downstream of a gate
  are restricted to the verified no-op `echo` receipt — ADR-0026 D6,
  `orchestrator.py:647-654`), so demanding the resolver population's tier/SoD machinery
  would be governance theater on a non-decision — while the RF-1 floor keeps the
  acknowledgment attributable. *Alternative:* restrict `/continue` to the gate's
  resolver population (tier-resolved approver) — more conservative, defensible if Cray
  wants "the same person who could have approved confirms there was nothing to
  approve"; costs approver-resolution machinery on a non-decision and changes nothing
  operationally. Why Cray: it sets who is accountable for the "checked" claim in the
  artifact.

- **SD-4 — RULED (Cray, typed, s256, 2026-08-26): option (B), one button that walks the
  empty gates.** **LOCKED for Step 3 and AC-5.** Supersedes §Mechanism item 3's drafted
  option (A) (one affordance per gate), whose text is retained verbatim there.
  <br>**Why this was put to Cray rather than executed as drafted.** Step 3's shape rested
  on AC-1's premise that one POST completes the run. Step 2 **measured that premise
  false** (see the AC-1 note above): the hero case takes two acknowledgments. A decision
  taken under a premise that has since been measured false is a decision worth re-putting,
  so the three shapes were priced and Cray ruled.
  <br>**What (B) means concretely, and what it does NOT change.** The UI renders **one**
  "Acknowledge — nothing to approve" action. On click it POSTs `/continue`, and while the
  response reports `run_status = waiting_human` **and** the newly suspended step also
  carries **zero** proposals, it POSTs again for that step — a **bounded** loop, and it
  **stops** the moment a gate carries a real proposal, falling back to the ordinary
  resolve affordance rather than clicking on. **The API, the chokepoint and the audit
  trail are untouched:** every gate still gets its own `run_continued_no_decision` chain
  row and its own step-`audit` block, because the loop is a client of the same endpoint.
  Only the number of human clicks changes.
  <br>🔴 **The cost Cray accepted, recorded so it is not rediscovered as a defect.** The
  artifact's *"checked — nothing to approve"* claim is weaker for the second and later
  gates: the human looked at the first gate's evidence, not the last one's. The loudness
  answer (§Mechanism) is therefore thinner under (B) than under (A) — though strictly
  stronger than the rejected shape (iii), because a human still initiates the walk on a
  run that **parked and was displayed**, and the walk halts at the first gate with
  anything to decide.
  <br>_The options as posed are retained (the PLAN-0111 convention)._
  <br>**(A) one affordance per gate** — as drafted; faithful to SD-3's per-gate human act,
  at two clicks and two "checked" rows for one sub-ceiling case; the second click is
  semantically odd (`fulfill` is "the mechanical write of the approved decision" and there
  is no approved decision to write). **(B) one button, UI walks the empty gates —
  TAKEN.** **(C) the chokepoint walks them server-side** — rejected as drifting into
  shape (iii), which this PLAN refused on the loudness hazard; re-opening it is a Cray
  decision, not an implementation choice.

## Open questions — record, do not resolve here

- **OQ-1 — the escalated-failure suspend is also API-dead-ended.** A step failing with
  `on_failure = escalate_to_human` parks `waiting_human` with `artifact = None`;
  `/gate/resolve` 409s on it (empty `output_set` at `action_step.py:830-832`) and only
  `/cancel` exits — yet `resume_run:436-441` already sanctions a *retry* for exactly
  this case. Same reachability gap, different semantic (retry, not acknowledge).
  Deliberately excluded from `/continue` (AC-2e); needs its own small PLAN if/when a
  vertical exercises it.
- **OQ-2 — dispatch L-1 vs the drafting tree.** The dispatch records the SD-3 ruling as
  written to PLAN-0113 via PR #1280; on the tree this draft was authored against,
  `0113-…md:431` still reads "SD-3 — OPEN". Presumably #1280 is unmerged or landed the
  record elsewhere — Step 5 reconciles instead of double-writing. Flagged so the
  reviewer checks rather than inherits.

## Verification

- Step 0 vs Step 4 full-suite comparison at CI scope (pytest / mypy --strict / bare
  ruff) — no path-scoped shortcuts.
- The AC-1..AC-3 battery with one probe per load-bearing assertion, each RED witnessed
  in the direction claimed (§8 discipline); the AC-2a probe doubles as the isolation
  control (AC-1 stays green under it).
- AC-4's scratch positive control proves the "unchanged" tests can redden.
- The two shipped parity tests + the sibling no-proposals test green **unchanged** —
  the mechanical proof that R-2 never materialized.
- Optional: `tools/probe_coverage.py` over the new battery; any never-reddened claim
  named with its reason.
- Preview check of AC-5 against a seeded sub-ceiling run (both surfaces, `?v=` bumped).
