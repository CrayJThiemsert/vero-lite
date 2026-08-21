# PLAN-0112: A Visitor's Case Fires a Governed Run — Tab I → Tab H

**Status:** Draft
**Owner:** both — Code executes; Cray rules the SDs before any build past Step 1
**Created:** 2026-08-21
**Related ADRs:** ADR-016 (S2 service principals / RF-1), ADR-0026 (principal SoD), ADR-0029 (event bridge, deterministic run ids), ADR-0035 (published-exposure rulings)
**Provenance:** Cray REVERSED PLAN-0110 SD-E (typed, s242, 2026-08-21 — recorded in
`docs/STATUS.md` §Active TODOs, first entry). SD-E's ruling **(d) build nothing** stands as
history in `docs/plans/done/0110-fleet-demo-run-markers-filter-and-deploy-reset.md`
(§SD-E, `:733-823`) and is **not edited by this PLAN**; its named follow-on **(b)
server-side firing** is hereby commissioned. Everything SD-E priced for (b) —
`done/0110:761-777` — is inherited here by citation, never restated.

## Goal

A repair case a visitor opens at Tab I ("Open a Case") becomes a governed `PipelineRun`
that appears in Tab H (Monitor)'s runs list — delivering the demo's own promise that a
visitor "watches their own case enter the loop" (`operate_seed.py:11-19`, the AC-8
clause 2 that PLAN-0110 measured unreachable and re-scoped). The tunnel exclusion of
`POST /procedures/{id}/run` and its written basis stand untouched — the run is fired
server-side, the only shape SD-E found that keeps the strongest ingress posture.

## Grounded measurements (all re-verified on `main` @ `e4eaf78`, 2026-08-21)

Everything below was read from the code this session. Two dispatch facts earned
**refinements** (G-4, G-6) and one **new finding** surfaced (G-5); the three-part break
itself is confirmed as stated.

- **G-1 — the three-part break holds.** (1) `open_case`
  (`services/api/routers/cases.py:183-219`) writes the `RepairCase`, commits, returns —
  fires nothing; unauthenticated intake falls back to `_UNATTRIBUTED` (`:206`).
  (2) `run_procedure_endpoint` (`services/api/routers/runs.py:370-419`) is the only
  producer of a `PipelineRun` (persist at `:397` via `run_procedure_persisted`), and the
  published ingress excludes it by design (`deploy/published/oct-fleet-maintenance/
  cloudflared/config.yml:110-112`, named again in the deny-by-default comment `:199-204`).
  (3) The parked seeded gate cannot adopt a later case — PLAN-0110 G10(3)
  (`done/0110:164-169`); so the visitor's run must be a **new** run.
- **G-2 — the auth asymmetry is still open (Step 1's premise INTACT).**
  `run_procedure_endpoint`'s complete body (`runs.py:370-419`) carries **no**
  `auth.person_id is None` refusal — it sets
  `trigger_context["triggered_by"] = auth.person_id` (`:391`) and passes
  `principal=auth.person` (`:405`) even when both are `None`. Both sibling doors fail
  closed: `resolve_gate_endpoint` — `if auth.person_id is None: raise HTTPException(403,
  "a gated step requires an authenticated human approver (ADR-016 S2 RF-1)…")`
  (`runs.py:444-451`) — and `cancel_run_endpoint` (`:553-560`). PLAN-0110 G10.6
  (`done/0110:196-205`) demanded any firing path close this **in the same change**.
- **G-3 — downstream of a fired run, the chain works.** `link_resolved_cases`
  (`verticals/fleet_maintenance/run_link.py:143-193`, armed by
  `register_fleet_run_link_hook` `:196-198`) writes `RepairCaseRunLink` per decided case
  on gate resolution; Tab H lists via `list_runs` (`runs.py:273-330`), fetched by
  `services/api/static/assets/view-monitor.js:164-178` (`getJSON('/runs')` at `:168`).
- **G-4 — REFINEMENT: "firing on case creation" literally cannot govern the case.**
  The procedure's intake reads the **projected event stream**, and a case enters that
  stream only when it is OPEN **with an accepted quote**: `governed_case_facts`
  (`services/db/case_events.py:68-99`) skips any case whose evidence pack has no
  accepted amount/vendor/time; `build_event` derives `measured_value` from
  `facts.accepted_amount_thb` and stamps the `case_id` onto the event
  (`verticals/fleet_maintenance/case_events.py:85-98`); the projection is refreshed at
  exactly three router sites — add-quote (`cases.py:497`), add-justification (`:530`),
  and **accept-quote** (`:715`, endpoint `POST /api/cases/{case_id}/accepted-quote`,
  `:639-640`). A just-opened case projects **nothing**; the **governable moment is
  quote acceptance**, not case creation. SD-E's option name was shorthand; the build
  must hang on the accept seam (SD-2).
- **G-5 — NEW FINDING: a second excluded door.** The published allowlist admits
  `^/api/cases$`, `/photos`, `/evidence`, `/quotes` (`config.yml:176-187`) and
  **deliberately does not admit accepted-quote**: "The cases router exposes more (tasks,
  justifications, accepted-quote, closeout, GET /{id}); under default-deny an
  unexercised route earns no row" (`config.yml:173-175`). So on the published profile a
  visitor can open a case and key quotes but **cannot reach the governable moment at
  all** — the promise fails one seam earlier than PLAN-0110 measured. Delivering it to
  a published visitor requires admitting `POST /api/cases/{id}/accepted-quote` (an
  ADR-0035-shaped ingress decision that reddens `tests/deploy/
  test_published_profiles.py`'s set-equality guard, per the `done/0110:748-751` rider
  precedent) **plus** a UI control that drives it — or re-scoping who accepts (SD-3).
- **G-6 — REFINEMENT: the intake is a population scan, not a case lookup.** The intake
  step reads the latest `reading` event **per Truck across the fleet**
  (`verticals/fleet_maintenance/procedures.yaml:146-166`), so a fired run proposes
  **every currently-breaching OPEN case** — including the two seeded demo cases, which
  stay OPEN with accepted quotes by seed design. A visitor-fired run therefore carries
  a multi-case gate: their case *plus* re-proposals of the demo pair (and any other
  visitor's pending governable case). Approving it re-approves spends the seeded run
  already parks on, and resolution writes link rows onto demo cases from a visitor run
  (the reset clears demo link rows on both keys — `services/db/demo_run_reset.py:208-214`
  — so hygiene survives, but the governance semantics need a ruling: SD-4).
- **G-7 — a `None`-principal firing mints a permanently unapprovable run (measured, not
  assumed).** Fleet's `governed_repair_approval` carries SoD (`procedures.yaml:354-363`,
  `intake: requester`), so `_record_requester_principals` returns a **non-None** map with
  `intake → None` when no principal fired the run
  (`services/engine/procedures/orchestrator.py:839-849`). Every subsequent resolve then
  fails closed: `check_principal_sod` raises `UNRESOLVED_PRINCIPAL` on a `None` pid for
  a constrained step (`services/engine/procedures/principal_sod.py:150-161`), surfacing
  as a 403 via `_enforce_principal_sod` (`services/engine/procedures/
  action_step.py:435-457`). **Correction to PLAN-0110's framing:** this is *not* "the
  G10(6) hole by another door" (nothing goes ungoverned) — it is worse in a different
  way: the run fires, parks, appears in Tab H, and **can never be resolved by anyone**.
- **G-8 — the persona role asymmetry narrows option (a) more than SD-E knew.** Only
  `req-mechanic-tom` holds the SoD `requester` role; `appr-fleet-manager-wirat` and
  `appr-owner` hold approver/authority-tier roles only (`procedures.yaml:102-111`).
  The PLAN-0075 cumulative roles are **authority-tier** roles, not the SoD requester
  role (`procedures.yaml:91-96`). Firing "as the authenticated persona" therefore
  dead-ends for an approver-keyed visitor too — `ROLE_MISMATCH`, fail-closed
  (`principal_sod.py:176-188`) — not just for the anonymous one. Under option (a) the
  promise holds for exactly **one** persona.
- **G-9 — the S1/S2 precedent is real and its shape is on disk.** A headless run fires
  as its agent's service principal with a declared **owning person recorded as the SoD
  requester at fire time**: `spec.py:1834-1836` (schedule), `event_bridge.py:91-107` +
  `:156-167` + `principal=request.owning_person` at `:317` (event), scheduler mirror at
  `scheduler.py:69-77`/`:274`. The event bridge also gives a **deterministic event-keyed
  run id** (ADR-0029 SD-2, `event_bridge.py:95`) — idempotency by construction. The
  bridge is invoked today only from `actions.py:177-186` behind `event_bridge_enabled`
  (`services/api/config.py:191`), so a case-accept invocation is **new wiring under any
  option** — the precedent supplies the actor shape, not the call path.
- **G-10 — runtime wiring hazards: confirmed, and bounded.** `discover_and_register()`
  registers **adapters + handlers only** (`services/api/main.py:485`, `:499-503`);
  procedure-executor factories are registered per **active vertical** at lifespan via
  `_PROCEDURE_EXECUTOR_REGISTRARS` (`main.py:335`, `:504-506`), and fleet's factory is
  deterministic — no MS-S1 call on the firing path (`:503`; so server-side firing adds
  DB-bounded latency, no LLM dependency). A firing seam resolving executors via
  `registry.get_procedure_executors` 409s until that registration runs
  (`runs.py:116-120`) — on the live fleet app this is satisfied post-lifespan; the 409
  hazard is real for **test fixtures**, which must register the factory (or boot the
  lifespan) before driving the seam.
- **G-11 — reset interplay: better than the rider feared, one live gap.** AC-4's
  "exactly two" assertion is **already id-scoped**
  (`tests/api/test_fleet_demo_reset_scenario.py:344-346` filters on `DEMO_RUN_IDS`), and
  `read_demo_state` reads only the two fixed demo ids (`demo_run_reset.py:179-205`) — a
  visitor run cannot confuse pristine/consumed detection. What no test yet proves:
  the reset **coexisting** with a visitor-fired run (the visitor run and its link rows
  must survive; AC-7 below). Visitor runs surviving every reset means they
  **accumulate across deploys with no lifecycle owner** — exactly the question SD-E said
  the follow-on must own, not silently inherit (`done/0110:808-811`; SD-7 below). G4's
  tripwire is pre-armed for this PLAN by name: trigger (ii) at `done/0110:92-99`.
- **G-12 — two gates, not one.** `governed_repair_approval` parks at `approve`, and
  resolving it parks again at the gated terminal `fulfill` (`done/0110:106-112`,
  measured there at `operate_seed.py:518-525`). A visitor-fired run needs **two**
  resolves to complete; Tab H shows it `waiting_human` after the first.

## Acceptance Criteria

> Numbered pass reads are fixed now against the **recommended** SD shapes and marked
> **[contingent]** where a different ruling re-fixes them — the PLAN-0111 discipline:
> rulings land first, pass reads are re-fixed against the ruled options **before**
> execution, and the run confirms them, never rewrites them. Every probe names its
> mutation and the direction the named assertion must redden. Environment marking:
> **[offline/DB]** = pytest against the dev Postgres (port 5442, main checkout —
> deterministic, no LLM); **[offline/no-DB]** = pure pytest; **[published]** = live
> evidence only, never the gate (§8 host-state rules apply).

- [ ] **AC-1 — the run endpoint fails closed on a missing principal (unconditional;
  Step 1; lands before any firing path exists).** `run_procedure_endpoint` refuses with
  403 when `auth.person_id is None`, mirroring `runs.py:444-451` verbatim in mechanism
  (independent of the `api_auth_enabled` toggle), before spec loading or any DB write.
  Pass read: a new test drives `POST /procedures/governed_repair_approval/run` with no
  resolved principal → **403**, detail citing ADR-016 S2 RF-1, and **zero** new
  `pipeline_runs` rows; a keyed-persona request still runs (parks `waiting_human`).
  Non-vacuity probe: comment out the new guard in a scratch copy → the 403 assertion
  reddens to a 200 **and** the zero-rows assertion reddens to 1 — both directions
  witnessed. **[offline/DB]**
- [ ] **AC-2 — the governable moment fires exactly one new run, idempotently
  [contingent on SD-1/SD-2/SD-5].** After a case crosses its governable moment
  (accepted quote whose amount breaches the truck's ceiling — G-4), exactly **one** new
  `PipelineRun` exists attributable to that case-event; repeating the trigger action
  (re-accept, projection re-refresh) creates **no second run**. Pass read: scenario
  drives open → quote → accept over HTTP; `GET /runs` gains exactly one run beyond the
  baseline; drive accept again → still exactly one. A **sub-ceiling** acceptance fires
  per the SD-2 ruling's stated behaviour (recommended: fires and completes with no
  gate — the loop *did* judge it; assert the ruled read). Non-vacuity probe: drop the
  idempotency key (deterministic run id / existence check) in a scratch copy → the
  exactly-one assertion reddens to 2 on the repeated accept. **[offline/DB]**
- [ ] **AC-3 — the binding scenario test: real producer into real consumer (CLAUDE.md
  §8).** Producer, concretely: the **Tab I HTTP intake flow** — `POST /api/cases` →
  `POST /api/cases/{id}/quotes` → `POST /api/cases/{id}/accepted-quote`
  (`cases.py:183`, `:450`, `:639`) driving the real server-side firing seam on realistic
  simulated data (a breaching THB amount against a real seeded `Truck` ceiling).
  Consumer, concretely: `GET /runs` (`list_runs`, `runs.py:273`) showing the new run;
  then `POST /runs/{id}/gate/resolve` as a keyed approver through **both** gates
  (G-12); then the real `link_resolved_cases` hook having written the
  `RepairCaseRunLink` row and the case list/evidence surfaces showing the outcome. The
  test must contain **no** `POST /procedures/{id}/run` call — the line
  `tests/api/test_visitor_case_to_monitor_scenario.py:371` exists because intake fires
  nothing (PLAN-0110 G10(1)); this test is that file's counterpart with the explicit
  fire **removed and the promise still delivered**. Neither side of the seam is
  stubbed. Pass read: all listed assertions green in one test run. Non-vacuity probe:
  disable the firing seam (scratch-revert the hook call at the accept path) → the
  "run exists in `GET /runs`" assertion reddens from 1 to 0 — the exact break the
  feature closes, re-witnessed. **[offline/DB]**
- [ ] **AC-4 — no reachable intake path mints a dead-end run [contingent on SD-1].**
  Whatever SD-1 rules, the invariant holds: every run a visitor-reachable path can
  fire has a gate the declared approvers can actually resolve. Pass read (recommended
  shape, SD-1(b)): every fired run's SoD requester is the declared owning person
  holding `requester`; a resolve by `appr-fleet-manager-wirat` succeeds. Pass read
  (shape (a)): an unkeyed or non-`requester`-keyed intake fires **nothing** (case
  writes succeed; run count unchanged) and the fired-run path exists only for the
  `requester`-role persona. Non-vacuity probe: force the seam's principal/owning-person
  to `None` in a scratch copy and fire → assert the resolve attempt 403s with
  `UNRESOLVED_PRINCIPAL` (G-7) — witnessing the dead-end the invariant excludes, in
  the direction (approvable → unapprovable) it guards. **[offline/DB]**
- [ ] **AC-5 — the demo copy claims exactly what the ruled shape delivers [contingent
  on SD-1/SD-3].** The sentences PLAN-0110 Step 6 re-scoped (`deploy/published/
  oct-fleet-maintenance/card-copy.md:26-27` TH / `:58-59` EN, per `done/0110:174-180`)
  are re-instated **only to the extent the ruled build makes true** — e.g. under
  SD-3(b) the promise text stays scoped to where acceptance is reachable. Pass read:
  each re-instated claim maps to a green AC-3 assertion; no sentence promises a surface
  the allowlist does not serve. Non-vacuity: this AC's reads are RED today by
  construction — the current copy deliberately does *not* make the promise
  (PLAN-0110 AC-10 re-scoped it), so any re-instatement flips them. **[offline/no-DB]**
  (grep-based) plus **[published]** eyes-on at Step 7.
- [ ] **AC-6 — the RoPA rider: intake's write-side effects are described where the
  compliance record lives.** `docs/compliance/ropa-change-statement-fleet.md` (and the
  Tab-I description surface PLAN-0110 called "the RoPA / AC-11 description",
  `done/0110:767-768`) gains the line that quote acceptance now also fires a governed
  procedure run (a `pipeline_runs` + `step_results` write naming the case via its
  event). Pass read: a grep for the new sentence(s) finds exactly the added lines;
  the PLAN-0109 caution applies — **no true sentence is deleted** to make room (the
  s241 finding against `docs/plans/0109-fleet-repair-cases-queryable-from-ask.md`
  §AC-11, whose ordered deletion of a still-true compliance sentence was the defect;
  s241 record: `docs/STATUS.md` §Active TODOs). Non-vacuity: the grep is RED today
  (0 matches — verified: no compliance text mentions run-firing on the accept path).
  **[offline/no-DB]**
- [ ] **AC-7 — the reset and the population bound survive contact [rider 3].**
  (i) A new reset-coexistence scenario: with one visitor-fired run parked and one of
  its link rows written, `reset_demo_runs` deletes only demo-scoped artifacts; the
  visitor run, its step results, and its link rows **survive**; `read_demo_state`
  still reads `PRISTINE` after re-boot (G-11). Non-vacuity probe: widen the reset's
  run-id scoping to all fleet runs in a scratch copy → the survival assertion reddens
  (visitor run gone). (ii) G4's population-bound paragraph and the AC-4/AC-5 framing
  in `done/0110` are rewritten **via an additive `§Post-archival amendment`** (the
  PLAN-0100/0102 convention) executing the tripwire's own instruction
  (`done/0110:92-99` — "rewrite this paragraph then; never delete the tripwire"),
  stating the new bound ("exactly two runs bearing the fixed demo ids among N visitor
  runs") and citing this PLAN. The ruled history above it is not touched. Pass read:
  the amendment section exists, the tripwire text survives verbatim, and
  `test_fleet_demo_reset_scenario.py`'s id-scoped assertions are cited as the code
  half. **[offline/DB]** for (i); doc-read for (ii).
- [ ] **AC-8 — the reopened cap/filtering question is answered, not dodged [contingent
  on SD-6].** Whichever SD-6 rules: (b)-recommended — `GET /runs` gains a bounded
  newest-N default with the client filter unchanged; pass read = a test seeds N+1 runs
  and reads N back, plus the two demo runs always present within bound; non-vacuity =
  lift the bound in scratch → the count assertion reddens. If (a)-unbounded is ruled:
  the pass read becomes the recorded acceptance note + a rewritten tripwire condition
  in AC-7(ii)'s amendment, and no endpoint change ships. **[offline/DB]**
- [ ] **AC-9 — full gates + the ingress guard moves only as ruled.** `uv run --extra dev
  pytest tests/ -q 2>&1`, `uv run mypy services/ 2>&1`, bare `ruff check . 2>&1` — all
  green (offline gate matches CI scope). `tests/deploy/test_published_profiles.py`:
  under SD-3(b)/no-ingress-change the expected route table is **byte-identical** —
  the strongest posture preserved is itself asserted; under SD-3(a) the accepted-quote
  row is added to the expected table **in the same PR with its written basis** (the
  file's P12 convention, `done/0110:748-751`). `POST /procedures/{id}/run` stays
  excluded under **every** ruling — any diff touching its exclusion or comments
  (`config.yml:110-112`, `:199-204`) fails this AC. **[offline/DB]**

## Out of Scope

- ❌ **Admitting `POST /procedures/{id}/run` to the tunnel allowlist** (SD-E option (a))
  — under every SD ruling here. Its exclusion, comments, and the `done/0110:757-760`
  open question stay untouched; this PLAN's whole shape exists to avoid that door.
- ❌ **Engine/orchestrator generalisation** — no query-grammar parameterization, no
  trigger-context-driven `where`, no generic subject-stamping (PLAN-0110 kept the
  engine untouched twice, `done/0110:377-379`) — unless Cray explicitly rules SD-4(b),
  which would **re-scope this PLAN**, not silently grow it.
- ❌ **`deploy/published/deploy.py`** — still energy-only by typed s219 decision
  (PLAN-0110 G11); nothing here attaches to it.
- ❌ **Retention-sweep semantics** — PLAN-0105 SD-4 RETAIN and the id-reuse divergence
  granted in PLAN-0110 SD-D stand unchanged; AC-7 touches the demo reset only.
- ❌ **Editing ruled history in `done/0110`** — only the additive `§Post-archival
  amendment` of AC-7(ii); the SD-E block, rulings, and G-findings stay verbatim.
- ❌ **PLAN-0111's closeout/credit-note work** — a closed case leaving
  `governed_case_facts` (`case_events.py:71-73`) is the only seam shared; no coupling.
- ❌ **Other verticals** — no procurement/energy firing path; fleet only.

## Steps

### Step 1: Close the auth asymmetry (AC-1) — before any firing path exists
The non-negotiable ordering (PLAN-0110 G10.6; STATUS names it the prerequisite).
Mirror `runs.py:444-451`'s refusal at the top of `run_procedure_endpoint`, independent
of the authn toggle, with its own test. Ships as its own PR — a weaker door must not
exist beside stronger ones for even one commit on which a firing path lands.

### Step 2: Cray rules SD-1 … SD-7; pass reads re-fixed
No build past Step 1 until the SDs below are ruled. Contingent ACs (2, 4, 5, 8) are
re-fixed against the ruled options in this file, with the ruling stamped per SD
(the PLAN-0110/0111 convention), before Step 3 begins.

### Step 3: Build the firing seam (AC-2)
Per SD-1/SD-2/SD-5 rulings: hook the governable moment (`cases.py:715`, after
`_refresh_case_events`) to fire `governed_repair_approval` with the ruled actor shape
and an idempotency key (deterministic per case-event id if SD-5 takes the bridge-shaped
id, `event_bridge.py:95` precedent). Executor resolution goes through
`registry.get_procedure_executors` (G-10) — test fixtures must register fleet's factory
first, and the seam's failure mode is ruled in SD-2 (recommended: fail-soft on the case
write, loud in the log + trace, mirroring the boot seed's posture at `main.py:508-511`
— the case row must never be lost to a firing error).

### Step 4: The scenario test + dead-end guard (AC-3, AC-4)
The §8-binding scenario lands with the seam in the same PR, plus the AC-4 invariant
tests. Non-vacuity probes witnessed RED from scratch copies before the green is
claimed (probes restore from the scratchpad, never from git).

### Step 5: The published surface (AC-5, AC-6) — per SD-3
If SD-3(a): the `^/api/cases/[^/]+/accepted-quote$` ingress row + the Tab I accept
control + the `test_published_profiles.py` expected-table change with written basis +
copy re-instatement. If SD-3(b): copy scoped to the reachable surface; no ingress
change. Either way the RoPA rider (AC-6) lands here.

### Step 6: Population-bound follow-through (AC-7, AC-8) — per SD-6/SD-7
The reset-coexistence scenario, the `done/0110` post-archival amendment, the cap (or
its recorded acceptance), and the visitor-run lifecycle disposition SD-7 rules.

### Step 7: Full gates + live evidence (AC-9)
Offline gates first (the gate). Then, under an explicit typed Cray go (§8 host-state;
every fleet redeploy is by-hand per PLAN-0110 G11): one live walk of the visitor flow
on the published system — open, quote, accept (per SD-3's ruling), watch the run
appear in Tab H, resolve both gates as personas, verify the link row and the reset
coexistence. Evidence, never the gate.

## Surfaced Decisions

> Per the commission: options laid out neutrally, grounded in measurements;
> recommendations are labelled **recommendation** and rule nothing. Cray rules each.

### SD-1 — who is the accountable requester for a visitor-fired run? (the commissioned decision)

The question PLAN-0110 left open (`done/0110:768-775`), now measured (G-7, G-8, G-9):

- **(a) Fire as the authenticated persona; fire nothing otherwise.** Fail-closed:
  intake by an unkeyed visitor or by a persona not holding `requester` fires no run
  (their case writes succeed unchanged). Measured narrowing (G-8): the promise then
  holds for **exactly one persona** (`req-mechanic-tom`) — the demo copy must say so
  (AC-5). Cleanest attribution: the run's requester is the human who actually accepted
  the quote. Cost: most visitors never see their own run; two of three demo personas
  cannot trigger the feature they came to see.
- **(b) Fire headless via the S1/S2 shape: the agent's service principal, with a
  declared owning person recorded as the SoD requester** (`spec.py:1834-1836`,
  `event_bridge.py:317` — G-9). Every governable case fires uniformly, keyed or not;
  the SoD requester is the standing `requester`-role Person (e.g. `req-mechanic-tom`
  as the declared "ผู้ตั้งเรื่องเบิก" — which is the customer's own narrative: ต้อม
  files, management decides, `procedures.yaml:91-96`); the *visitor's* identity stays
  where it already truthfully lives — `opened_by`/`accepted_by` on the case rows and
  the trigger context — and the `run_started` audit says `actor_kind: "service"`, as
  the scheduled path already does (`procedures.yaml:73-74`). Cost: the run's requester
  is a role-holder, not the specific visitor; the disclosure/copy must not imply
  otherwise.
- **(c) Fire with no principal.** Measured consequence on the record (G-7): the run
  fires, parks, appears in Tab H — and **no one can ever resolve it**
  (`UNRESOLVED_PRINCIPAL`, fail-closed 403, every attempt). Nothing goes ungoverned
  (correcting PLAN-0110's "hole by another door" fear), but each anonymous case mints
  a permanent `waiting_human` dead-end in the Monitor.

**Recommendation (labelled, rules nothing):** (b) — it is the only option that delivers
the promise to every visitor without minting dead-ends, and its actor shape is the
repo's own precedent, not an invention. **Why Cray:** this decides who may cause a
governed run to exist on a public surface and whose name the record carries — the
ADR-016/ADR-0035 class of ruling, and the exact question SD-E reserved.

### SD-2 — the firing moment and its idempotency/failure semantics

Measured (G-4): case-open cannot fire anything real; the governable moment is
quote-acceptance. Remaining choices: **(a)** fire on accept only, once per case
(deterministic id; a re-accept re-fires only if the prior run for that case-event is
absent), fail-soft on the case write (loud log + trace; the accept must not be lost to
a firing error — the boot seed's posture, `main.py:508-511`); **(b)** re-fire on every
projection-material change (re-accept at a new amount → a new run; honest but noisy —
each re-fire adds a parked run someone must resolve or cancel); **(c)** fire-on-open
as literally commissioned — measured to govern nothing (G-4) and recorded here so the
reversal's option-name is not silently redefined: delivering *the promise* requires
the accept seam. **Recommendation:** (a). **Why Cray:** (a) vs (b) trades audit
completeness against Monitor noise — a demo-narrative call, and the option-name
correction ((c)→accept-seam) should be ratified explicitly since Cray's commission
used SD-E's wording.

### SD-3 — the second excluded door: how a published visitor reaches the governable moment

New finding (G-5): `POST /api/cases/{id}/accepted-quote` is deliberately off the
published allowlist, and Tab I ships no accept control — the promise currently fails
before any firing seam is reached. **(a)** Admit the route + ship the Tab I accept
interaction: full promise for published visitors; costs an ingress-allowlist change
(ADR-0035-shaped, guard table changes with written basis, `done/0110:748-751`
precedent) and puts a spend-accepting write on the public surface (bounded by the
same app-auth posture as the other admitted case writes — `accepted_by` falls back to
`_UNATTRIBUTED` at `cases.py:704`, the same intake-attribution question SD-1 governs).
**(b)** Keep it excluded: the firing seam still ships and is real on the dev console
and for any keyed flow that reaches accept; the published copy scopes the promise to
"your case enters the queue; the governed round you watch is driven from the console"
— an honest partial delivery, close to what PLAN-0110's re-scope already says.
**Recommendation:** (a), because the commission is "delivered rather than re-scoped"
and (b) re-scopes; but (a) is precisely a published-exposure ruling this PLAN may not
make. **Why Cray:** it reverses a named default-deny row — the decision class
PLAN-0100/0103/ADR-0035 reserved for typed rulings.

### SD-4 — the population-scan gate: whose cases does a visitor-fired run propose?

Measured (G-6): a fired run proposes every currently-breaching OPEN case — the
visitor's *and* the demo pair's *and* other visitors'. **(a)** Accept the multi-case
gate: it is what the declared procedure means ("read the fleet, govern what breaches");
the approver decides per proposal; the copy explains that the round sweeps the fleet.
Costs: re-approval surface over already-parked demo spends; visitor-run link rows land
on demo cases (hygiene held by the reset's both-key deletion, `demo_run_reset.py:
208-214`, but the audit narrative needs a line). **(b)** Scope the run to the firing
case — requires engine work (grammar parameterization) or per-case procedure
authoring; both are the Out-of-Scope engine line unless Cray re-scopes the PLAN.
**(c)** Have the seed close/fulfil the demo cases so they stop re-proposing — changes
the seeded demo's own story (the parked gate IS the beat) — recorded for completeness,
priced as self-defeating. **Recommendation:** (a) with the copy line and an AC-3
assertion that the visitor's proposal is decidable independently of the others (the
gate's per-proposal `decisions` map already supports it, `resolve_gate_endpoint`
`req.decisions`). **Why Cray:** it decides what a governed round *means* in the demo
narrative — product voice, not code.

### SD-5 — mechanism: imperative call vs declared event trigger

**(a)** Imperative: the accept path calls `run_procedure_persisted` directly with the
ruled actor shape — smallest diff, hand-rolled idempotency, wiring lives in the router.
**(b)** Declared: give `governed_repair_approval` an `event_trigger` and fire through
the shipped bridge — deterministic event-keyed run id (idempotency by construction,
ADR-0029 SD-2), owning-person shape built in (G-9), and the vertical's behaviour stays
*declared* (the spine's own thesis, CLAUDE.md §3); costs: the YAML's `trigger: manual`
comment (`procedures.yaml:144`, "L-1: only manual runs in Phase 1") changes meaning as
a declared decision, and the bridge needs a new invocation seam from the accept path
either way (G-9 — today only `actions.py` calls it, behind `event_bridge_enabled`).
**Recommendation:** (b) if SD-1 = (b) (the shapes compose; the idempotency is free);
(a) if SD-1 = (a) (the bridge's service-principal actor contradicts firing as the
persona). **Why Cray:** with SD-1 it fixes which precedent (manual-door vs
S1/S2-headless) this surface extends — an architecture-lineage call.

### SD-6 — the dissolved population bound: cap and server-side filtering

The two `done/0110:375-383` Out-of-Scope items reopen the moment a visitor can mint
runs (G4 tripwire trigger (ii), pre-armed). **(a)** Accept unbounded at pilot scale:
each run costs a visitor a full open→quote→accept walk, so growth is slow;
rewrite the tripwire's condition in the AC-7 amendment; ship nothing. **(b)** A
bounded newest-N default on `GET /runs` (client filter unchanged, demo runs asserted
within bound) — the minimal cap. **(c)** Server-side status filtering + pagination —
the complete answer, priced as overbuild before any measured need. **Recommendation:**
(b). **Why Cray:** G4 records the cap as Cray's own reopened question by name.

### SD-7 — visitor-run lifecycle: who owns the runs that now accumulate?

Measured (G-11): visitor runs survive every reset by design and accumulate across
deploys. SD-E: "a decision someone must own — in the follow-on PLAN, not silently
here" (`done/0110:808-811`). **(a)** Retain: governed runs are audit substance; the
`audit_log` is never deleted anyway (PLAN-0110 G8) and deleting runs while keeping
their audit rows makes the chain's subjects dangle; Monitor growth is SD-6's problem.
**(b)** Reset-time sweep of non-demo fleet runs: a pristine Monitor each deploy;
reverses the reset's deliberate protect-visitor-runs scoping (AC-5 of `done/0110`) and
deletes governed history. **(c)** Cancel-only: an operator cancels stale
`waiting_human` visitor runs via the existing endpoint (`runs.py:538-560`) — governed,
manual, and honest, but an operator chore. **Recommendation:** (a) + (c) as posture
(retain; cancel manually when a parked run has served its purpose), revisit at pilot.
**Why Cray:** retention of governed records on a public demo is a compliance-adjacent
posture call (PDPA framing in §8), not an implementation detail.

## Verification

1. **Offline (the gate):** the AC-9 full gates plus, per AC, its own named test —
   each contingent pass read re-fixed at Step 2 before execution, each non-vacuity
   probe SEEN red from a scratch copy (restored from the scratchpad, never from git)
   before its green is claimed. DB-backed tests run from the main checkout against the
   dev Postgres (5442).
2. **Ordering is part of the pass:** AC-1's PR merges before any PR containing a firing
   seam; a PR that lands both in one diff fails review by this line.
3. **Live (evidence, not the gate):** Step 7 under an explicit typed Cray go — §8
   host-state rules; every fleet redeploy is the by-hand path (PLAN-0110 G11).
4. **Rulings:** no SD is ruled at drafting time. This PLAN stays `Draft`; each ruling
   is stamped in place per SD (`RULED (Cray, typed, date, session): …`) the moment it
   lands, and the contingent ACs are re-fixed in the same edit (drafter dispatch —
   `docs/plans/` stays G2-gated for Code).
