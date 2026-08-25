# PLAN-0112: A Visitor's Case Fires a Governed Run — Tab I → Tab H

**Status:** **COMPLETE 9/9** — closed session 246, 2026-08-22, on Cray's typed
ratification of AC-7(i)'s narrowing. All seven SDs ruled; Steps 1–7 executed; the
visitor flow is live on the published system (`docs/logs/2026-08-22-s246-plan0112-step7-fleet-deploy-and-live-walk.md`).
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
  _[Closed 2026-08-21 by Step 1 — PR #1246, merged `f52dbdc`: the refusal now
  exists at `runs.py:391-398`, before spec loading and any DB write; the sibling
  citations `:444-451` / `:553-560` above (fixed on `e4eaf78`) now resolve at
  `:460-466` / `:569-576` — pure line shift from the insertion. G10.6 is
  satisfied ahead of any firing path; evidence in AC-1's closing stamp.]_
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
- **G-13 — the accepted-quote exclusion is load-bearing PROSE at two further tracked
  sites (measured s243, on `docs/plan-0112-sd3-ruled` @ `b4ccd04` — postdates this
  section's header stamp).** Beyond the set-equality guard SD-3 already named
  (`tests/deploy/test_published_profiles.py:589-594`, `assert
  set(_ingress_paths(profile)) == expected`), two tracked sites carry the exclusion
  as a justifying claim — invisible to a call-graph review because neither *calls*
  the endpoint; each *asserts that it is unreachable*: (1)
  `verticals/fleet_maintenance/operate_seed.py:478-486` —
  `seed_settled_history_case`'s docstring, the reason the seed exists at all: no
  close-out UI anywhere in `services/api/static/`, "`/api/cases/{id}/closeout` is
  **not on the system's ingress allowlist**. Neither is `/accepted-quote`. So no
  visitor-created case can reach the gate, and no amount of visitor activity can
  ever put money on the report… the KPI is **structurally ฿0 forever**"; (2)
  `tests/api/test_operate_seed_spend_scenario.py:224-228` — the same claim inside
  `test_the_settled_history_case_opens_the_kpi_on_a_real_figure`'s docstring. The
  consequence under SD-3(a), split precisely — do not overstate it: the
  gate-reachability clause ("no visitor-created case can reach the gate") becomes
  **FALSE** and must be corrected in the same PR as the ingress row, or the repo
  carries a false statement a test's stated rationale rests on; the ฿-report clause
  ("no amount of visitor activity can ever put money on the report") stays **TRUE**,
  because `/closeout` remains excluded — the published config admits exactly four
  case rows (`config.yml:176`, `:180`, `:183`, `:186`) and `accepted` appears in
  that file only inside the exclusion comment (`:173-175`) — and the ฿ column comes
  from a close-out. **`seed_settled_history_case` remains necessary; only its reason
  sentence needs splitting** — nothing in this finding implies the seed becomes
  redundant.
- **G-14 — SD-2(b) and SD-5(b) do NOT compose on the bridge's stock key (measured
  s243, on `docs/plan-0112-sd2-4-5-6-7-ruled` @ `4913a80` — postdates this section's
  header stamp).** `event_key` hashes `(vertical, event_kind, sorted(entity_ids),
  detected_at // window_seconds)` (`services/engine/procedures/event_bridge.py:41-69`);
  the run id is `<procedure_id>@<key>` (`event_run_id`, `:72-76`); and `fire_event_run`
  returns `ALREADY_FIRED` without starting anything when that run id already exists
  (`:303-305`; existence check `_event_run_exists`, `:239-245`). **The accepted amount
  is not in the key** — a re-accept at a new amount within one dedup window would be
  deduped away, silently defeating SD-2(b) exactly as ruled. The constraint the build
  must carry: `entity_ids` must carry the accepted quote's identity, i.e.
  `[case_id, quote_id]` — the **same** quote re-accepted → same key → no new run
  (correct: not a material change); a **different** quote accepted → different key →
  a new run (precisely SD-2(b)). Two traps, both measured: (1) do **not** key on
  `accepted_id` — `accept_quote` mints a fresh `accepted-{uuid4}` on **every** call
  (`services/api/routers/cases.py:699-700`), so an accidental double-click of the
  same quote would mint two runs; (2) `dedup_window_seconds` defaults to 3600 (`gt=0`,
  `services/engine/procedures/spec.py:178-186`), and with a time bucket in the key a
  same-quote re-accept **after** the window would spuriously re-fire. This event is
  human-driven, not a polled steady-state detection, so the window must be authored
  wide enough that the bucket is effectively constant — reducing the key to
  `(vertical, event_kind, case_id, quote_id)`, which is SD-2(b) as ruled and nothing
  more. The window value is a deliberate build choice, for this reason (Step 3).
- **G-15 — SD-6's premise, measured (s243, same branch @ `4913a80`).** `list_runs`
  (`services/api/routers/runs.py:273-330`) issues
  `select(PipelineRun).order_by(PipelineRun.started_at.desc())` with **no `.limit()`**
  (`:295-299`) — the endpoint is unbounded today, returning every run ever on each
  Tab H load.

## Acceptance Criteria

> Numbered pass reads are fixed now against the **recommended** SD shapes and marked
> **[contingent]** where a different ruling re-fixes them — the PLAN-0111 discipline:
> rulings land first, pass reads are re-fixed against the ruled options **before**
> execution, and the run confirms them, never rewrites them. Every probe names its
> mutation and the direction the named assertion must redden. Environment marking:
> **[offline/DB]** = pytest against the dev Postgres (port 5442, main checkout —
> deterministic, no LLM); **[offline/no-DB]** = pure pytest; **[published]** = live
> evidence only, never the gate (§8 host-state rules apply).

- [x] **AC-1 — the run endpoint fails closed on a missing principal (unconditional;
  Step 1; lands before any firing path exists).** `run_procedure_endpoint` refuses with
  403 when `auth.person_id is None`, mirroring `runs.py:444-451` verbatim in mechanism
  (independent of the `api_auth_enabled` toggle), before spec loading or any DB write.
  Pass read: a new test drives `POST /procedures/governed_repair_approval/run` with no
  resolved principal → **403**, detail citing ADR-016 S2 RF-1, and **zero** new
  `pipeline_runs` rows; a keyed-persona request still runs (parks `waiting_human`).
  Non-vacuity probe: comment out the new guard in a scratch copy → the 403 assertion
  reddens to a 200 **and** the zero-rows assertion reddens to 1 — both directions
  witnessed. **[offline/DB]**
  > **CLOSED (Code, 2026-08-21) — PR #1246, merged `f52dbdc`** (4 files, +207/−18;
  > long form in the PR body + commit message — pointers only here). The guard:
  > `services/api/routers/runs.py:391-398` (rationale comment `:384-390`), at the
  > top of `run_procedure_endpoint`'s body — before `settings.oct_vertical` /
  > `_spec_for` (`:400-401`) and before `run_procedure_persisted` — mirroring the
  > resolve and cancel guards in mechanism (the resolve guard this AC cites as
  > `:444-451` on `e4eaf78` now sits at `:460-466`; pure line shift from this
  > insertion). The test: `tests/api/test_run_endpoint_principal_guard.py` — the
  > refusal (403 + RF-1 citation + zero new `pipeline_runs` rows) and its positive
  > control (a keyed `req-mechanic-tom` still fires and parks `waiting_human`).
  > **Non-vacuity witnessed RED in BOTH directions — via TWO probes on DIFFERENT
  > assertions, not one mutation** (the ⚠️ finding below): **P1** guard deleted →
  > `assert 200 == 403` reddened, the body printing `"triggered_by": null` — the
  > pre-fix defect itself; proves **presence**. **P2** guard relocated *after*
  > `run_procedure_persisted` → `assert 1 == 0` reddened with the placement
  > message *while the 403 assertion still passed* (ruling out an unrelated
  > break); proves **placement** — the AC's own "before spec loading or any DB
  > write" clause. Each probe restored byte-identical from `/tmp` (never from
  > git), sha256-verified. **Blast radius measured before AND after:** a
  > pre-change baseline over the nine driver files captured green (45 passed) so
  > any later red was attributable; four reddened, two kinds — two scenarios
  > firing unkeyed, and the SIBLING guards' own tests, whose *arrangement* (not
  > assertion) minted their parked run through the very door this change closes;
  > arming authn in the scenario fixture then reddened two further tests in that
  > module (the fixture governs every request there, not only the run POST).
  > Also landed: `test_runs_endpoints.py` sibling guard tests re-arranged + the
  > now-dead `runs_no_auth` fixture removed; `test_case_event_path_scenario.py`
  > keyed as `req-mechanic-tom`. **Full gate at CI scope:** `pytest tests/`
  > **4222 passed / 8 skipped** (4220 at session start — +2 exactly, so nothing
  > else moved) · bare `ruff check .` clean · `ruff format --check .` 648 files
  > already formatted (no file touched after the probes were witnessed) ·
  > `mypy --strict services/ verticals/` clean over 201 files.
  > ⚠️ **Finding for the probe batteries ahead (AC-2, AC-3, AC-4, AC-7, AC-8 —
  > specified in this same both-directions shape).** This AC's probe read asked
  > one mutation to redden two assertions ("the 403 assertion reddens to a 200
  > **and** the zero-rows assertion reddens to 1 — both directions witnessed") —
  > but both assertions live in ONE test, and pytest stops at the first failed
  > assert, so a single mutation can only ever witness ONE direction. Closing
  > honestly required two independent probes: deletion (presence) and
  > **relocation past the write** (placement). The placement half is the half
  > that evidences the AC's own ordering clause — a battery that only deletes
  > would have left that clause unevidenced while reporting success. For the ACs
  > above: where a pass read names two reddening assertions, plan one probe
  > **per assertion**, each naming its mutation and direction — and prefer
  > mutations under which the *other* assertion stays green, because that green
  > is what rules out "something unrelated broke."
- [x] **AC-2 — the governable moment fires runs per SD-2(b), idempotent per quote
  identity [SD-2 RULED (b) + SD-5 RULED (b), s243 — pass read re-fixed; the
  once-per-case read is retired; SD-1 RULED (b), s242 — see SD-1].** The accept seam
  fires through the declared event trigger (SD-5(b)) under the G-14 key constraint:
  `entity_ids = [case_id, quote_id]`, never `accepted_id`, with a deliberately wide
  `dedup_window_seconds` so the bucket is effectively constant (G-14). Pass read —
  **both directions asserted**: scenario drives open → quote → accept over HTTP;
  `GET /runs` gains exactly one run beyond baseline; (i) re-accept the **same**
  quote → still exactly one run (not a material change); (ii) accept a **different**
  quote on the same case → exactly one **more** run (SD-2(b) as ruled). Sub-ceiling
  clause, corrected per the SD-2 stamp: a sub-ceiling acceptance still fires (the
  loop *did* judge it), and in the shipped demo that run **gates anyway** — intake
  is a fleet-wide scan (G-6) and the seeded demo pair stays OPEN with breaching
  accepted quotes (G-12) — so assert instead that the run exists and that the
  visitor's sub-ceiling case appears in **none** of the gate's proposals (`reshape`
  consumes only the breach subset, `procedures.yaml:190-193`); "completes with no
  gate" holds only in a fleet with no other breaching truck and is asserted nowhere.
  Non-vacuity probes, re-fixed so each mutation reddens the named assertion in the
  direction it claims: drop `quote_id` from the key (`entity_ids = [case_id]`) in a
  scratch copy → assertion (ii) reddens (the different-quote accept dedups to
  `ALREADY_FIRED`; the count stays 1 where 2 is asserted); key on `accepted_id` in
  a scratch copy → assertion (i) reddens (the same-quote re-accept mints a second
  run; the count reads 2 where 1 is asserted). **[offline/DB]**
  > **CLOSED (Code, 2026-08-21) — PRs [#1248](https://github.com/CrayJThiemsert/vero-lite/pull/1248)
  > (the seam) + [#1250](https://github.com/CrayJThiemsert/vero-lite/pull/1250) (the
  > remaining clause).** The seam is `cases.py::_fire_governed_run_for_acceptance`,
  > invoked from `accept_quote` AFTER `_refresh_case_events`, keyed
  > `entity_ids=[case_id, quote_id]` with `dedup_window_seconds: 3153600000`
  > (bucket 0 across 1970..2069 — asserted, not assumed). Tests:
  > `tests/api/test_case_acceptance_fires_governed_run_scenario.py` — the count clauses
  > and both SD-2(b) directions in #1248, the sub-ceiling clause in #1250. Probes,
  > one per assertion, every mutation on production code: `entity_ids=[case_id]`
  > reddens (ii); keying on the per-call `accepted_id` reddens (i); removing
  > `reshape`'s `where: {verdict: breach}` reddens the sub-ceiling clause. 🔴 **The
  > sub-ceiling negative carries a positive control** — "not in the proposals" is
  > vacuously true of an EMPTY list, so the breaching demo case must be found in the
  > same list first. 🔴 **A SECOND composition failure, beyond G-14 and unreachable
  > by any key design:** SD-P4's `_procedure_in_flight` selects on `procedure_id` and
  > status alone, so the published profile's parked seed made every acceptance a
  > silent `SKIPPED_IN_FLIGHT`, and with no seed a visitor's second acceptance was
  > skipped by their own first parked run. `fire_event` gained
  > `skip_if_in_flight: bool = True`; the default is unchanged and already pinned by
  > `test_skip_if_in_flight`. Full record in #1248's body.
- [x] **AC-3 — the binding scenario test: real producer into real consumer (CLAUDE.md
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
  > **CLOSED (Code, 2026-08-21) — PRs [#1250](https://github.com/CrayJThiemsert/vero-lite/pull/1250)
  > + the outcome-surface follow-up.** `test_the_full_walk_both_gates_the_link_row_and_the_case_surface`
  > drives `POST /api/cases` -> `/quotes` -> `/accepted-quote` into the real seam and
  > resolves BOTH gates through `POST /runs/{id}/gate/resolve` as keyed
  > `appr-fleet-manager-wirat` (G-12: the first resolve parks the run again at
  > `fulfill`; only the second completes it). The module contains **no**
  > `POST /procedures/{id}/run` — the clause separating it from
  > `test_visitor_case_to_monitor_scenario.py`.
  > 🔴 **RULING (Cray, typed, s244) — the "case list / evidence surfaces showing the
  > outcome" clause resolves to the `RepairCaseRunLink` row + the repair-spend
  > export, option (a).** The clause as written pointed at two surfaces that
  > deliberately carry no verdict: the case row stops at the accepted quote, and the
  > evidence pack is verdict-free BY DESIGN ("as FACTS — deliberately not a verdict")
  > because the sourcing threshold can move and a frozen verdict would rot into a
  > confident wrong answer. Rejected: (b) adding a decision field to the case surface
  > — real work, its own PLAN, not a Step-4 addendum; (c) re-scoping the clause —
  > declined in favour of measuring what the system genuinely shows.
  > **Measured, not interpreted:** the structured export ties case -> run -> outcome
  > -> approver, then the REAL CSV endpoint is parsed and this repair is found by
  > plate carrying ผู้อนุมัติ. Two probes, because the halves fail independently —
  > forcing `_approver_of` to `None` reddens the derivation; blanking only the
  > rendered cell reddens the file while the structured read stays green.
  > ⚠️ The row count is deliberately NOT asserted: the gate is a fleet-wide scan
  > (G-6) and this walk approves every proposal at it, so other cases are
  > legitimately decided too — SD-4(a) as ruled. An "exactly one row" assertion was
  > written, measured FALSE, and replaced; it was a claim about the population, not
  > about this outcome being shown.
- [x] **AC-4 — no reachable intake path mints a dead-end run [SD-1 RULED (b), s242 —
  pass read re-fixed against the ruling; the shape-(a) read is retired. SD-5 RULED
  (b), s243 — the ruled mechanism supplies exactly this G-9 actor shape: the
  `event_trigger` descriptor's `owning_person_id` is recorded as the SoD requester
  (`spec.py:168-177`); the pass read below stands unchanged].** The
  invariant: every run a visitor-reachable path can fire has a gate the declared
  approvers can actually resolve. Pass read: every fired run's SoD requester is the
  declared owning person holding `requester` (the service-principal fire, G-9 shape);
  its `run_started` audit names `actor_kind: "service"` (the scheduled path's
  precedent, `procedures.yaml:73-74`); and a resolve by `appr-fleet-manager-wirat`
  succeeds. Non-vacuity probe: force the seam's owning person to `None` in a scratch
  copy and fire → assert the resolve attempt 403s with `UNRESOLVED_PRINCIPAL` (G-7)
  — witnessing the dead-end the invariant excludes, in the direction (approvable →
  unapprovable) it guards. **[offline/DB]**
  > **CLOSED (Code, 2026-08-21) — PR [#1250](https://github.com/CrayJThiemsert/vero-lite/pull/1250).**
  > `test_a_visitor_fired_run_is_never_a_dead_end` asserts three facts SEPARATELY,
  > because they fail independently: `step_principals["intake"] == req-mechanic-tom`
  > (the declared owning person recorded as the SoD requester at fire time, the G-9
  > shape SD-5(b) supplies); the `run_started` audit naming `actor_kind: "service"`
  > with the SP-5 `on_behalf_of.owning_person_id` lineage; and a resolve by
  > `appr-fleet-manager-wirat` actually succeeding. The amount is ฿12,000 — over
  > every truck's ฿5,001 ceiling so it reaches the gate, and inside วิรัช's
  > ฿5,001-30,000 rung (Q9), which he holds cumulatively while NOT holding
  > `เจ้าของกิจการ`; the ฿62,000 case the other tests use would have routed past him.
  > Non-vacuity: the AC's own specified probe — removing
  > `event_trigger.owning_person_id` — reddens the requester assertion, witnessing
  > G-7's dead end in the approvable -> unapprovable direction.
- [x] **AC-5 — the demo copy claims exactly what the ruled shape delivers [SD-3
  RULED (a), s243 — pass read re-fixed, the (b) example clause retired; SD-1 RULED
  (b), s242 — its clause below is now fixed].** The sentences
  PLAN-0110 Step 6 re-scoped (`deploy/published/
  oct-fleet-maintenance/card-copy.md:26-27` TH / `:58-59` EN, per `done/0110:174-180`)
  are re-instated with the **full promise** — under SD-3(a) the published surface
  serves the whole walk (open → quote → accept → watch the run in Tab H), so the
  re-instated copy may make it. Pass read:
  each re-instated claim maps to a green AC-3 assertion; no sentence promises a surface
  the allowlist does not serve; and — fixed by SD-1(b) — no sentence implies the run
  record names the visitor: per-visitor attribution language is confined to the case
  rows (`opened_by`/`accepted_by`) unless the ADR-0035 amendment recorded in SD-1's
  ruling lands first. Non-vacuity: this AC's reads are RED today by
  construction — the current copy deliberately does *not* make the promise
  (PLAN-0110 AC-10 re-scoped it), so any re-instatement flips them. **[offline/no-DB]**
  (grep-based) plus **[published]** eyes-on at Step 7.
- [x] **AC-6 — the RoPA rider: intake's write-side effects are described where the
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
- [x] **AC-7 — the reset and the population bound survive contact [rider 3].**
  (i) A new reset-coexistence scenario: with one visitor-fired run parked and one of
  its link rows written, `reset_demo_runs` deletes only demo-scoped artifacts; the
  visitor run, its step results, and its **non-demo** link rows **survive**, while its
  **demo-scoped** link rows are deleted; `read_demo_state`
  still reads `PRISTINE` after re-boot (G-11).
  _[Superseded s249 by PLAN-0113 — see §Post-archival amendment below]_
  _[**NARROWED (Cray, typed, s246, 2026-08-22)** — the clause previously read "and its
  link rows **survive**" without qualification, which was **measured FALSE** three
  independent ways before the narrowing was proposed: the scenario test (a run fired
  from the visitor's OWN case wrote three link rows, keyed on the visitor's case AND
  two others including `case-fleet-operate-demo`); the live reset (six link rows
  deleted for two demo runs — the excess written by visitor-fired runs); and the live
  gate (*"3 candidates reached this gate"*). Cause: fleet's `intake` is a **fleet-wide
  scan**, so every visitor-fired run's gate also decides the seeded demo case and
  `on_resolved` writes one link row **per decided case**, which the reset then reaches
  by `case_id`. **The deletion is correct, not a defect** — the reset erases and
  re-seeds that case, so a surviving link would point at a different case reusing the
  id. Only the sentence was wrong; no code changed with the ruling.]_ Non-vacuity probe: widen the reset's
  run-id scoping to all fleet runs in a scratch copy → the survival assertion reddens
  (visitor run gone). (ii) G4's population-bound paragraph and the AC-4/AC-5 framing
  in `done/0110` are rewritten **via an additive `§Post-archival amendment`** (the
  PLAN-0100/0102 convention) executing the tripwire's own instruction
  (`done/0110:92-99` — "rewrite this paragraph then; never delete the tripwire"),
  stating the new bound ("exactly two runs bearing the fixed demo ids among N visitor
  runs") **in the SD-6(b) shape as ruled (s243): the Monitor's `GET /runs` carries a
  bounded newest-N default, the two demo runs asserted within bound (AC-8)** — and
  citing this PLAN. The ruled history above it is not touched. Pass read:
  the amendment section exists, the tripwire text survives verbatim, and
  `test_fleet_demo_reset_scenario.py`'s id-scoped assertions are cited as the code
  half. **[offline/DB]** for (i); doc-read for (ii).
  - ✅ **(ii) BUILT and its pass read MET (s245).** `done/0110` carries the additive
    `## Post-archival amendment — 2026-08-22 (session 245)`; the tripwire sentence and
    its "never delete the tripwire" instruction both survive verbatim (checked with
    whitespace normalised — the sentence wraps, and a single-line literal reports a
    false 0); the ruled history above is unedited; all three code-half modules are
    cited by name and exist on disk. `VERDICT=AC7II_VERIFIED`, 18 criteria.
  - ✅ **(i) CLOSED s246, after Cray ratified the narrowing its own measurement
    forced.** The criterion was written asserting that a visitor-fired run's link rows
    survive a reset; that was measured false and the clause is now narrowed in place
    above, with the ruling stamped beside it. The build never changed — it asserted the
    measured bound from the day it was written. The build is complete:
    `tests/api/test_fleet_demo_reset_coexistence_scenario.py`, 4 tests, with **three**
    non-vacuity probes (one per assertion, each mutating the production
    `demo_run_reset.py`, each restored byte-identically and sha256-verified, each
    shown to redden THAT assertion) — `VERDICT=AC7I_NONVACUITY_PROVEN`. What does not
    hold is *"its link rows **survive**"*. Measured: fleet's `intake` is a
    **fleet-wide scan**, so a visitor-fired run's `approve` gate also decides the
    seeded demo case, and `on_resolved` writes **one link row per decided case** —
    a run fired from a visitor's own case wrote three, keyed on
    `['case-<visitor>', 'case-demo-truck03-gearbox', 'case-fleet-operate-demo']`.
    The reset clears link rows on **both** keys, so **every** visitor-fired run loses
    its `case-fleet-operate-demo` link row, whatever case its visitor accepted on.
    **That deletion is correct, not a defect** — the reset erases and re-seeds that
    case, so a surviving link would point at a different case reusing the id.
    **The measured bound, which the tests assert:** the visitor's run survives
    field-for-field, its step results survive, its **non-demo** link rows survive, and
    its **demo-scoped** link rows do not. ✅ **RATIFIED (Cray, typed, s246,
    2026-08-22)** — the clause is narrowed in place above and AC-7 is ticked. Nothing
    in the build changed with the answer; only the wording did. Recorded in
    `done/0110`'s amendment too, so the finding is not carried only here.
- [x] **AC-8 — the reopened cap/filtering question is answered, not dodged [SD-6
  RULED (b), s243 — pass read fixed as ruled; the (a)-unbounded branch is retired].**
  `GET /runs` — unbounded today (G-15) — gains a bounded newest-N default with the
  client filter unchanged; pass read = a test seeds N+1 runs and reads N back, plus
  the two demo runs always present within bound; non-vacuity = lift the bound in
  scratch → the count assertion reddens. **[offline/DB]**
  - ✅ **CLOSED s245.** `settings.runs_list_default_limit` (default **200**, env
    `RUNS_LIST_DEFAULT_LIMIT`) bounds `list_runs`; the client filter is untouched.
    `tests/api/test_runs_list_bounded_scenario.py`, 4 tests: seed N+1 → read N back
    **and prove they are the NEWEST N** (a length-only assertion passes just as
    happily on the oldest page); both demo runs within bound against the **real** boot
    seed — they are the oldest rows on a fresh system and so exactly what a newest-N
    bound drops first; and a guard on the shipped default itself (≥ 50), which no
    other test reads. Two non-vacuity probes on the production router —
    `VERDICT=AC8_NONVACUITY_PROVEN`; N-5 additionally holds the bounded-list assertion
    GREEN while reddening the badge, proving the two are independent.
  - 🔴 **A build choice SD-6(b) did not specify, recorded rather than left implicit:
    `waiting_human_count` is NOT bounded.** It is counted over the whole population
    with its own `select(count())`, never over the returned page. It is the "waiting
    on me" badge Tab H paints (`operate_seed.py`'s docstring names it), and a badge
    that shrank with the page would under-report decisions still pending — a governed
    action nobody is told about. The list is a view; the count is a fact about the
    system. Cray may overrule; the probe N-5 pins the current behaviour either way.
- [x] **AC-9 — full gates + the ingress guard moves only as ruled [SD-3 RULED (a),
  s243 — the (b)/no-ingress-change/byte-identical branch is retired].** `uv run --extra dev
  pytest tests/ -q 2>&1`, `uv run mypy services/ 2>&1`, bare `ruff check . 2>&1` — all
  green (offline gate matches CI scope). `tests/deploy/test_published_profiles.py`:
  the `^/api/cases/[^/]+/accepted-quote$` row is added to the expected table
  (`:114`, case rows `:137-140`) **in the same PR with its written basis** (the
  file's P12 convention, `done/0110:748-751`), and that same PR corrects the two
  G-13 prose sites (the Step 5 obligation). `POST /procedures/{id}/run` stays
  excluded under **every** ruling — any diff touching its exclusion or comments
  (`config.yml:110-112`, `:199-204`) fails this AC. **[offline/DB]**
  - ✅ **CLOSED s246.** Offline gate at CI scope: `pytest tests/` **4267 passed / 8
    skipped**, bare `ruff check .` clean, `ruff format --check .` 654 files,
    `mypy --strict services/ verticals/` clean over 201. The ingress row and its
    written basis landed with the four G-13 prose corrections in one PR
    ([#1255](https://github.com/CrayJThiemsert/vero-lite/pull/1255)).
    🔴 **The exclusion invariant was checked on the LIVE host, not only in the repo:**
    reading `cloudflared/config.yml` as the deployed system holds it — 21 ingress rows,
    with a positive control proving the reader had the real file rather than an error
    string — `^/api/cases/[^/]+/accepted-quote$` is present and **`POST
    /procedures/{id}/run` is still absent**.
  - **Live evidence (never the gate), under Cray's typed per-phase go:** the published
    system was redeployed to `ee41b55` and a full visitor walk was driven through
    Cloudflare Access. Non-cheapest accept → 422 with the reason box scoped to that
    quote; reason submitted → `governed_repair_approval@cbc5677f9fdef75a` fired with
    `trigger: event`; Tab H moved 2 → 3 runs and its badge 1 → 2; the gate reasoned on
    *"Spend 62000.0 THB"* — the visitor's own amount; SoD refused the requester and the
    DOA ladder resolved to `appr-owner`, who approved; the run parked again at
    `fulfill`; and the demo still read **`PRISTINE`** beside it. Full record with the
    rollback point:
    `docs/logs/2026-08-22-s246-plan0112-step7-fleet-deploy-and-live-walk.md`.

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

**EXECUTED (Code, 2026-08-21) — PR #1246, merged `f52dbdc`, as its own PR as
required.** What landed: the fail-closed guard at `runs.py:391-398` (before spec
loading and any DB write), `tests/api/test_run_endpoint_principal_guard.py`
(refusal + positive control), the sibling-test re-arrangement in
`test_runs_endpoints.py` (dead `runs_no_auth` fixture removed), and
`test_case_event_path_scenario.py` keyed as `req-mechanic-tom`. The two-probe
non-vacuity record (presence AND placement, each witnessed RED), the measured
blast radius, and the full gate (4222 passed / 8 skipped, +2 exactly) are in
AC-1's closing stamp — which also carries the ⚠️ probe-battery finding for the
steps ahead. Ordering held: no firing path existed when this merged
(§Verification item 2, first half discharged).

### Step 2: Cray rules SD-1 … SD-7; pass reads re-fixed
No build past Step 1 until the SDs below are ruled. Contingent ACs (2, 4, 5, 8) are
re-fixed against the ruled options in this file, with the ruling stamped per SD
(the PLAN-0110/0111 convention), before Step 3 begins.
**Discharged s243:** all seven SDs are RULED and stamped in place (SD-1 s242;
SD-3 s243; SD-2/SD-4/SD-5/SD-6/SD-7 s243), and the contingent pass reads are
re-fixed in the same edits — the gate on Steps 3+ is lifted (§Verification item 4).

### Step 3: Build the firing seam (AC-2) — SD-1(b) s242; SD-2(b) + SD-5(b) s243
**EXECUTED (Code, 2026-08-21) — PR #1248, merged `8cc365f`.** The declared trigger
flipped to `event` with the `event_trigger` descriptor authored on procurement's
template (`event_kind: repair_quote_accepted`, `owning_person_id: req-mechanic-tom`
— G-8 makes it forced, not chosen), the stale `# L-1` comment corrected in the same
edit, and the accept seam hooked after `_refresh_case_events` with the G-14 key.
🔴 **The build carried a constraint this Step did not know about:** SD-P4's
in-flight guard defeats SD-2(b) on a gated procedure, so `fire_event` gained
`skip_if_in_flight` (default unchanged). 🔴 **Ordering is load-bearing and fails
silently:** firing before the projection refresh yields a run that fires, parks and
gates — about another truck's case. Evidence in AC-2's stamp.
The mechanism as ruled — the event bridge. In
`verticals/fleet_maintenance/procedures.yaml`: flip `governed_repair_approval` to
`trigger: event`; author the `event_trigger` descriptor on procurement's live
template (`verticals/procurement/procedures.yaml:861-868` — the SD-5 stamp;
`owning_person_id` = the standing `requester`-role person per SD-1(b)); choose
`dedup_window_seconds` **deliberately wide** per G-14 (this event is human-driven,
not a polled detection — the bucket must be effectively constant so the key reduces
to `(vertical, event_kind, case_id, quote_id)`); and **correct the stale `# L-1`
comment at `procedures.yaml:144` in the same edit** (the SD-5 stamp). Hook the
governable moment (`cases.py:715`, after `_refresh_case_events`) to invoke the
bridge — a new invocation seam under any option (G-9: today only `actions.py:177-186`
calls it) — with `entity_ids = [case_id, quote_id]` per G-14, never `accepted_id`.
Executor resolution goes through `registry.get_procedure_executors` (G-10) — test
fixtures must register fleet's factory first. Failure posture (the PLAN's carried
requirement, not part of Cray's pick): fail-soft on the case write, loud in the log
+ trace — the accept row must never be lost to a firing error (precedent:
procurement's operate seed, `main.py:507-515`, the citation correction recorded in
the SD-2 stamp).

### Step 4: The scenario test + dead-end guard (AC-3, AC-4)
**EXECUTED (Code, 2026-08-21) — PR #1250, plus the AC-3 outcome-surface follow-up.**
⚠️ **Deviation, recorded rather than glossed:** this Step says the scenario "lands
with the seam in the same PR". It did not — #1248 shipped the seam with the AC-2
count clauses, and #1250 followed with the sub-ceiling clause, both gates, the link
row and AC-4. The ordering requirement that WAS honoured is the one that matters
(no firing path existed before AC-1 closed); splitting these two cost nothing but a
CI round, and #1248 was already large. AC-3 and AC-4 carry the evidence.
The §8-binding scenario lands with the seam in the same PR, plus the AC-4 invariant
tests. Non-vacuity probes witnessed RED from scratch copies before the green is
claimed (probes restore from the scratchpad, never from git).

### Step 5: The published surface (AC-5, AC-6) — SD-3 RULED (a), s243
The `^/api/cases/[^/]+/accepted-quote$` ingress row + the Tab I accept control + the
`test_published_profiles.py` expected-table change with written basis + copy
re-instatement, one PR. **The same PR corrects the two G-13 prose sites**
(`operate_seed.py:478-486`, `test_operate_seed_spend_scenario.py:224-228`): the
gate-reachability clause ("no visitor-created case can reach the gate") is fixed as
no longer true; the ฿-report clause is preserved as still-true (`/closeout` stays
excluded, and the ฿ column comes from a close-out); and the seed's necessity is
restated — split its reason sentence, never remove the seed. The RoPA rider (AC-6)
lands here.

**EXECUTED (Code, 2026-08-22, s245) — AC-5 and AC-6 CLOSED.** The ingress row landed
with its written basis and the `:173-175` exclusion comment was corrected to say which
door moved and which did not; the expected table gained the row under the P12
convention; Tab I gained the ตกลงใบนี้ control (`view-case.js`, `views.css`, `?v=`
bumped on both); the card copy re-instated the full promise in TH and EN; and the RoPA
gained §3.3.

🔴 **MEASURED CORRECTION — G-13's prose-site set is FOUR, not two.** G-13 named two
sites; a sweep before editing (`git grep` over `ingress allowlist`, `ungoverned`,
`unreachable on the published`, `Neither is`) found two more, both **module-level
docstrings**, invisible for exactly G-13's own stated reason — neither *calls* the
endpoint, each *asserts it is unreachable*:

1. 🆕 `verticals/fleet_maintenance/operate_seed.py:11-21` — the MODULE docstring:
   *"AC-8's second clause … is UNREACHABLE on the published profile"*, *"no visitor can
   start a run"*, *"the visitor's case therefore sits OPEN and ungoverned"*, *"Until
   that lands … the card copy says so."* Goes false **because of Step 5** — the ingress
   row is precisely what makes a published visitor able to fire — which is why Steps 3
   and 4 correctly did not touch it.
2. `operate_seed.py:478-486` — G-13 site (1), as named.
3. 🆕 `tests/api/test_operate_seed_spend_scenario.py:12-16` — the MODULE docstring,
   carrying the same *"neither `/closeout` nor `/accepted-quote`"* basis as site (2).
4. `test_operate_seed_spend_scenario.py:224-228` — G-13 site (2), as named.

All four corrected under G-13's own split, which held at every one: the
**gate-reachability** half is FALSE and retired; the **฿-report** half is TRUE and kept;
`seed_settled_history_case` stays, and stays the only writer of the ฿ column on this
surface. Retirements are marked with the repo's `superseded by new info` convention
rather than deleted, so the reasoning lineage survives.

⚠️ **The probe that verified this failed its own first criterion, and the INSTRUMENT was
what was wrong** (CLAUDE.md §8). A bare `grep -c` for each retired clause cannot
distinguish *"X is true"* from *"it used to read X, and X is now false"*, so it scored a
correctly-retired site as a failure — and, worse, silently scored **0** for site (1),
whose clause wraps across a line break. The repaired probe scans whole-file text and
classifies each match as `asserting` vs `quoted-inside-a-retirement`, reporting the two
separately and never summed. Verdict `PE_NEGATIVE_PASSES`: 3 matches, 3 quoted, 0
asserting. The criterion was not relaxed.

**Verified in the browser, and a three-way UX review run on the result.** The walk was
driven end to end on the published fleet profile — no persona → 401; signed in as ต้อม;
a non-cheapest accept → 422 with the reason box scoped to that quote; reason submitted →
+1 run, `trigger: event`, `waiting_human`; the cheapest accept → no reason demanded, +1
run (SD-2(b) live). That found three defects the lexical guards cannot see (a stale
refusal surviving a case re-selection, a success toast promising approval for a
sub-ceiling acceptance, and FastAPI's list-shaped validation `detail` rendering as
`[object Object]`), all fixed here.

A subsequent UX review (interaction order · visual hierarchy · Thai microcopy) found
more. 🔴 **Cray ruled (typed, s245): fix the factually-FALSE strings in this PR, chip the
rest.** Two qualified, and both are the same defect class this PLAN exists to fix, so
neither could be deferred: the success toast named **`หน้าติดตามงาน`**, a tab that does
not exist — measured in the browser, all six published tab labels are English
(*Operational Map · Ask · Procedures · **Monitor** · Open a Case · Month-End KPI*) — and
`card-copy.md` carried the same false name; and the auth refusal said **`เลือกตัวตน`**
where the picker calls itself `เลือกบทบาทเพื่อดำเนินการ`, on another tab, with no
location given. Both corrected.

Deferred to tracked chips **with their measurements attached**, never silently dropped:
the accept button is **4.59×** smaller in area than the routine add-quote button (7.31×
at desktop); `--accent` sits on `.pack-agreed`, the one element that is *not* pressable,
against `theme.css`'s own stated contract; `--fg` and `--panel` are used in `views.css`
and **defined nowhere** (verified at runtime); accept results render far from the button
that produced them; any pack message **wipes a half-typed quote** (measured live, and it
contradicts `view-case.js`'s own header comment); the English 422 shown to a Thai
operator; plus four defects that predate Step 5 entirely.

**Two things Step 5 deliberately did NOT touch, each with its reason:**
- **The in-app Tab I persistence banner** (`view-case.js`, PLAN-0106 / ADR-0037 D2.4).
  Still TRUE after this change — it promises that case *text and photos* are erased
  within 90 days, and the run rows the accept now writes hold no visitor text (measured
  by `test_visitor_case_to_monitor_scenario.py`'s sentinel + key allowlist). Its wording
  is **Cray-reviewed in PLAN-0106 SD-1** and the RoPA's own §6.1 puts it out of this
  document's scope, so re-wording it is a ruling, not a build step.
- **`docs/plans/0111-*.md` F14**, which cites `test_published_profiles.py:141-143` by
  line number — those numbers moved when the row landed. `/closeout`'s exclusion, which
  is what F14 actually claims, is unchanged and still true. Surfaced, not silently
  edited: PLAN-0111 is another PLAN's ruled content.

### Step 6: Population-bound follow-through (AC-7, AC-8) — SD-6(b) + SD-7(a)+(c), s243

**EXECUTED (Code, 2026-08-22, s246) — AC-8 CLOSED; AC-7(ii) met; AC-7(i) built and
proven but left UNTICKED on a wording question.** Three pieces shipped and each was
witnessed RED before being trusted: the coexistence scenario
(`tests/api/test_fleet_demo_reset_coexistence_scenario.py`, 4 tests, 3 probes,
`VERDICT=AC7I_NONVACUITY_PROVEN`); the `done/0110` additive post-archival amendment
(`VERDICT=AC7II_VERIFIED`, 18 criteria); and the bounded newest-N default on
`GET /runs` (`settings.runs_list_default_limit`, 4 tests, 2 probes,
`VERDICT=AC8_NONVACUITY_PROVEN`). Gate: full `pytest tests/` **4267 passed / 8
skipped** (4259 baseline + the 8 added), bare `ruff check .` clean, `ruff format
--check .` 654 files, `mypy --strict services/ verticals/` clean over 201.

🔴 **The one finding that outgrew its criterion.** AC-7(i) asserts a visitor-fired
run's *"link rows survive"* a reset. Measured, they do not — fleet's `intake` is a
fleet-wide scan, so every visitor-fired run's gate also decides the seeded demo case,
and the reset reaches that link row by `case_id`. The deletion is correct; the AC's
wording is not. The measured bound is recorded at AC-7 above and in `done/0110`'s
amendment, and the criterion stays unticked until Cray rules on the narrowing.

**SD-7 needed no build, as ruled:** visitor runs are retained (a) and an operator
cancels stale parked ones through the existing `cancel_run_endpoint` (c). **No sweep
ships**, and none was written — recorded here so a later reader does not mistake the
absence for an omission.

Now unconditional: the reset-coexistence scenario; the `done/0110` post-archival
amendment (its new bound stated in the SD-6(b) shape — AC-7(ii)); the bounded
newest-N default on `GET /runs` (AC-8); and the ruled visitor-run disposition —
retain (a), an operator cancels stale parked runs manually through the existing
`cancel_run_endpoint` (c), which requires an authenticated human and cancels only
`waiting_human` runs (the SD-7 stamp). No sweep ships.

### Step 7: Full gates + live evidence (AC-9)

**EXECUTED (Code, 2026-08-22, s246) — AC-9 CLOSED.** Offline gates first, then the live
walk under Cray's typed go. 🔴 **The pre-flight reads changed the shape of the deploy
and are why the go was asked TWICE:** the host checkout was a week stale at `205ba4b`,
so the accepted-quote ingress row **had never reached production** — Step 5's promise
was unreachable there — and the demo read `CONSUMED`, routing the sequence through
`DEMO-RESET.md`'s reset-before-boot ordering. Cray's advance go predated both facts, so
Phase D was re-asked with them on the table and re-granted.

The deploy carried its own evidence at every step: six file hashes identical between
image and working tree; `:prev` tagged to the exact baseline id as the rollback point;
image id identical across machines; `config --quiet` at zero bytes; only `app`
recreated, then only `cloudflared`; postgres untouched at `Up 3 days`. Full record:
`docs/logs/2026-08-22-s246-plan0112-step7-fleet-deploy-and-live-walk.md`.

🔴 **Production data corroborated AC-7(i)'s finding twice.** The reset deleted **six**
link rows for **two** demo runs — the excess written by visitor-fired runs against demo
case ids — and the live gate then reported *"3 candidates reached this gate"*. Both say
the same thing the coexistence test measured offline: one gate resolution writes one
link row per decided case, so a visitor's demo-scoped links cannot survive a reset.

Offline gates first (the gate). Then, under an explicit typed Cray go (§8 host-state;
every fleet redeploy is by-hand per PLAN-0110 G11): one live walk of the visitor flow
on the published system — open, quote, accept (per SD-3's ruling), watch the run
appear in Tab H, resolve both gates as personas, verify the link row and the reset
coexistence. Evidence, never the gate.

## Surfaced Decisions

> Per the commission: options laid out neutrally, grounded in measurements;
> recommendations are labelled **recommendation** and rule nothing. Cray rules each.

### SD-1 — who is the accountable requester for a visitor-fired run? (the commissioned decision)

**RULED (Cray, typed, s242, 2026-08-21): (b)** — the S1/S2 headless service principal
with a declared owning person as the SoD requester; the recommendation was taken.
Cray's stated reasoning, two halves: **(1)** someone who can get through to Tab I
already holds some level of authorization to use the system; **(2)** we can use the
email name they logged in with to track who opened the case.

**The measured state of each half, recorded with the ruling (re-verified on disk,
s242):**

- **Half 1 is consistent with what the app already tells its users:** the published
  D6 notice states "Access is gated by Cloudflare, which processes your email
  address" (`services/api/static/assets/app.js:170`). One caveat travels with it:
  the tunnel config in this repo carries no Access configuration (Access policies
  are dashboard-side, outside the repo), and `app.js`'s own comment calls the vendor
  gate page "capability this repo cannot verify" (`app.js:154-156`).
- **Half 2 does not hold at the app layer today — a measured fact, not a doubt:**
  `Person` has only `person_id`/`name`/`roles` — no email column
  (`services/db/person.py:14-16`); the only occurrence of "email" anywhere under
  `services/` is the D6 disclosure sentence itself (`app.js:160`, `:170`) — a
  sentence, not a datum; `open_case` sets `opened_by = auth.person_id or
  (req.opened_by or "").strip() or _UNATTRIBUTED` (`cases.py:206`) — a person_id,
  else a **client-supplied string**, else unattributed; the browser credential is an
  operator API key whose display identity is "what the operator typed" —
  self-asserted (`services/api/static/assets/auth.js:13-15`); and **zero code under
  `services/` reads any `Cf-Access-*` header** (0 grep hits; every hit in the repo
  is in ADRs and handoffs). **Plainly, for the later reader: under (b) as ruled, a
  visitor-fired run's requester is the declared role-holder, and the visitor's own
  identity survives only in the case rows' `opened_by`/`accepted_by` — which, for an
  unkeyed caller, is a client-supplied string no one authenticated.**

**Dependency recorded, per Cray's directed sequence (record this ruling first, then
amend ADR-0035):** Cray wants the per-visitor attribution and has directed that we
get it. *[Corrected s243, per Cray's typed same-round ruling (recorded in SD-3's
stamp); the ADR-0035 s242 amendment-pass note cites these very lines as the
sentence to fix. This note originally named the mechanism as the full phase-2
recipe — "an IdP behind Access, with `Cf-Access-Jwt-Assertion` validated in a
FastAPI dependency" — which the amendment does NOT ratify.]* The mechanism is the
**capture half only**, which ADR-0035's s242 amendment ratifies — in the ADR's own
words, app code "is permitted solely to READ the gate's verdict for provenance,
never to perform gating itself"; "reading the identity the edge asserts (the
`Cf-Access-Authenticated-User-Email` / `Cf-Access-Jwt-Assertion` material Access
injects) to stamp provenance on a record = **permitted**; performing or
supplementing the gate — any `Depends(...)` that rejects, any 401/403 the app
issues from that material, any per-visitor key lifecycle — = **still forbidden**"
(the L1 s242 annotation); "what is ratified here is capture, not validation", and
the s172 **validating** FastAPI dependency "remains pilot-era (D8, as amended
there)" (the amendment-pass note). The **validating** recipe may **not** land in
this PLAN: ADR-0035 (Accepted, s200) places that recipe in the pilot era, "out of
L1's phase-1 posture," named "so it is neither forgotten nor smuggled in early," and
reserves the per-route decision for "the pilot's own governance artifact — it may
not ride in on demo precedent." An identity-capture AC would have been exactly that
smuggling before the s242 amendment drew the capture-not-validation line; a
**validating** dependency still would be. CLAUDE.md §1 makes the Accepted ADR
binding. **Therefore SD-1(b) ships
without per-visitor attribution unless and until an ADR-0035 amendment ratifies the
phase-2 identity capture for the published demo surface.** *(That amendment has
since landed, s242 — capture, not validation, is ratified; the identity-capture
AC, when written, "must sit inside" that line, per the amendment-pass note.)*
Noted in passing and
deliberately unresolved here, because the amendment is Cray's to make: ADR-0035's
own pilot-era criterion — "a pilot's users are known principals, not anonymous
visitors" — is the substance of Cray's half 1, i.e. the ground such an amendment
would stand on.

The options below are **retained deliberately** (the PLAN-0111 convention): a future
reader must see what was rejected and why.

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

**RULED (Cray, typed, s243, 2026-08-21): (b)** — re-fire on every projection-material
change (re-accept at a new amount → a new run). **This is NOT the option the PLAN
recommended: the recommendation below was (a), once-per-case, and it was not taken.**
Cray typed the pick only — no reasoning was given, and none is recorded here.
(Contrast SD-1, whose stamp records Cray's typed "two halves" because Cray typed it;
everything below this ruling line is the PLAN's record, not Cray's.)

**The measured state recorded with the ruling (Code, s243, on this branch @
`4913a80` — each re-checkable):**

- **The ruled option and SD-5(b) do not compose on the bridge's stock dedup key —
  G-14.** The accepted amount is not in `event_key`, so a re-accept at a new amount
  within one dedup window would be deduped away — silently defeating (b) exactly as
  ruled. The build must key on the accepted quote's identity
  (`entity_ids = [case_id, quote_id]`), never on `accepted_id`, and must author
  `dedup_window_seconds` deliberately wide; the full mechanism, both traps, and the
  citations are G-14. Step 3 and AC-2 carry the constraint.
- _[Superseded s249 by PLAN-0113 — see §Post-archival amendment below]_
- **AC-2's sub-ceiling pass read was FALSE in the demo environment and is corrected
  in this edit.** The `reshape` step consumes only the breach subset
  (`input: {from: judge, where: {verdict: breach}}`,
  `verticals/fleet_maintenance/procedures.yaml:190-193`), so a non-breaching row
  never reaches the doa_tier gate — but intake is a fleet-wide population scan (G-6)
  and the seeded demo pair stays OPEN with breaching accepted quotes (G-12), so
  **every** visitor-fired run gates, sub-ceiling or not. The old clause "a
  sub-ceiling acceptance fires and completes with no gate" holds only in a fleet
  where no other truck breaches — never in the shipped demo. AC-2's pass read is
  re-fixed accordingly (a direct SD-4(a) consequence).
- **Citation correction (requirement kept, attribution fixed).** Option (a) below
  cites the fail-soft posture as "the boot seed's posture, `main.py:508-511`"; that
  block sits inside `if vertical == "procurement":` (`services/api/main.py:507-515`)
  — it is **procurement's** operate seed, not fleet's. A valid fail-soft precedent,
  imprecisely attributed. The requirement itself — the accept write must never be
  lost to a firing error — stands, and Step 3 carries it (the PLAN's requirement,
  not part of Cray's pick).

The options below are **retained deliberately** (the PLAN-0111 convention): a future
reader must see what was rejected — including the recommendation that was not taken.

Measured (G-4): case-open cannot fire anything real; the governable moment is
quote-acceptance. Remaining choices: **(a)** fire on accept only, once per case
(deterministic id; a re-accept re-fires only if the prior run for that case-event is
absent), fail-soft on the case write (loud log + trace; the accept must not be lost to
a firing error — the boot seed's posture, `main.py:508-511` *[attribution corrected
s243: procurement's operate seed, `main.py:507-515` — see the stamp block above]*);
**(b)** re-fire on every
projection-material change (re-accept at a new amount → a new run; honest but noisy —
each re-fire adds a parked run someone must resolve or cancel); **(c)** fire-on-open
as literally commissioned — measured to govern nothing (G-4) and recorded here so the
reversal's option-name is not silently redefined: delivering *the promise* requires
the accept seam. **Recommendation:** (a). **Why Cray:** (a) vs (b) trades audit
completeness against Monitor noise — a demo-narrative call, and the option-name
correction ((c)→accept-seam) should be ratified explicitly since Cray's commission
used SD-E's wording.

### SD-3 — the second excluded door: how a published visitor reaches the governable moment

**RULED (Cray, typed, s243, 2026-08-21): (a)** — admit `POST
/api/cases/{id}/accepted-quote` to the published allowlist AND ship the Tab I accept
interaction. **Cray typed the pick only — no reasoning was given, and none is
recorded here.** (Contrast SD-1, whose stamp records Cray's typed "two halves"
reasoning because Cray typed it; SD-3 has no such text — everything below this
ruling line is the PLAN's record, not Cray's.) In the same turn Cray ruled that the
incorrect `Cf-Access` sentence in SD-1's dependency note is fixed **in this same
round** rather than deferred to the identity-capture AC PR — done, stamped `s243`
in that note. The PLAN's own recorded rationale for why (a) satisfies the
commission is the **Recommendation** paragraph retained below, unchanged — drafter
reasoning, never Cray's.

**The measured state recorded with the ruling (Code, s243, on this branch @
`b4ccd04` — each re-checkable):**

- **Correction to retained option (b)'s own text — do not inherit its false
  clause.** (b) asserts the firing seam "is real on the **dev console** and for any
  keyed flow that reaches accept". The dev-console half is **measured FALSE**: a
  grep for `accepted-quote|acceptedQuote|accepted_quote` over
  `services/api/static/` returns **zero hits**, with a positive control on the same
  tree (the identical grep for `photos` hits
  `services/api/static/assets/view-case.js:107`). The UI's complete case-route
  surface is `view-case.js:71, 92, 107, 201, 224` — list, create, `/photos`,
  `/evidence`, `/quotes` — exactly the four admitted rows, and **no accept call in
  any view**. So under (b) the governable moment would have been reachable only by
  an API client, a test, or the seed writing ORM rows directly — not by anyone
  using any shipped UI on any surface, published or local.
- **Correction narrowing (a)'s cost.** This SD frames (a) as reversing "a named
  default-deny row". True, but `accepted-quote` is **not** on `_UNIVERSALLY_DENIED`
  (`tests/deploy/test_published_profiles.py:150-161` — ten routes: `/warm`,
  `/sleep`, the three `/intake/*`, the three `/procedures/draft/*`,
  `/demo/hero/event`, `/insights/query`). It is a per-system omission under
  default-deny, not the cross-system floor that "cannot be lowered by adding a
  directory" (`:147-149`). The ruling class stays Cray's; the invariant it touches
  is one system's expected table (`:114`, case rows `:137-140`), not the shared
  floor. `POST /procedures/{id}/run` is likewise not on that floor — it stays
  excluded by fleet's own written basis (`config.yml:199-204`), and AC-9 guards it.
- **The blast radius this SD under-counted (now G-13).** SD-3 named only the
  set-equality guard (`test_published_profiles.py:589-594`). Two further tracked
  sites carry the exclusion as load-bearing prose — each *asserts the endpoint is
  unreachable*, so neither surfaces in a call-graph review: G-13. Under (a) the
  gate-reachability clause there becomes FALSE and is corrected in the same PR
  (Step 5); the ฿-report clause stays TRUE and **`seed_settled_history_case`
  remains necessary** — see G-13 for the precise split.
- **The exposure (a) opens, which this SD did not name — the cost accepted with
  the ruling.** `accept_quote` (`cases.py:639-716`) refuses a non-lowest acceptance
  without a reason with **422** (`:690-697`) — by design, because the audit
  question is "why did you not take the cheapest one" (`:654-656`). Attribution is
  `accepted_by = auth.person_id or (req.accepted_by or "").strip() or
  _UNATTRIBUTED` (`:704`). So under (a) on the published profile, an
  **unauthenticated visitor authors the audit answer to that question, recorded as
  `unattributed`**. This is the same `_UNATTRIBUTED` posture SD-1 already governs
  for `opened_by` — but this datum is a governance justification (the reason the
  DOA ladder's audit trail keeps), not an intake field.

The options below are **retained deliberately** (the PLAN-0111 convention): a future
reader must see what was rejected and why. Option (b) carries the correction above,
marked inline where its false clause sits.

New finding (G-5): `POST /api/cases/{id}/accepted-quote` is deliberately off the
published allowlist, and Tab I ships no accept control — the promise currently fails
before any firing seam is reached. **(a)** Admit the route + ship the Tab I accept
interaction: full promise for published visitors; costs an ingress-allowlist change
(ADR-0035-shaped, guard table changes with written basis, `done/0110:748-751`
precedent) and puts a spend-accepting write on the public surface (bounded by the
same app-auth posture as the other admitted case writes — `accepted_by` falls back to
`_UNATTRIBUTED` at `cases.py:704`, the same intake-attribution question SD-1 governs).
**(b)** Keep it excluded: the firing seam still ships and is real on the dev console
*[measured FALSE, s243 — no shipped UI on any surface drives accept; see the
correction block above]* and for any keyed flow that reaches accept; the published
copy scopes the promise to
"your case enters the queue; the governed round you watch is driven from the console"
— an honest partial delivery, close to what PLAN-0110's re-scope already says.
**Recommendation:** (a), because the commission is "delivered rather than re-scoped"
and (b) re-scopes; but (a) is precisely a published-exposure ruling this PLAN may not
make. **Why Cray:** it reverses a named default-deny row — the decision class
PLAN-0100/0103/ADR-0035 reserved for typed rulings.

### SD-4 — the population-scan gate: whose cases does a visitor-fired run propose?

_[Superseded s249 by PLAN-0113 — see §Post-archival amendment below]_

**RULED (Cray, typed, s243, 2026-08-21): (a)** — accept the multi-case gate. Cray
typed the pick only — no reasoning was given, and none is recorded here; everything
below this ruling line is the PLAN's record, not Cray's.

**The measured state recorded with the ruling (Code, s243, on this branch @
`4913a80`):**

- **The accepted cost is stronger than the option text below states.**
  `GateResolveRequest.decisions: dict[str, Literal["approve", "reject"]]`
  (`services/api/models/runs.py:190-200`) is described in the model itself as
  "action_id -> approve | reject; EVERY proposal at the gate needs an explicit
  decision (no silent default)". So the approver is not merely **able** to decide
  the visitor's proposal independently — on every visitor-fired round they are
  **compelled** to explicitly decide the demo pair's re-proposals too. Option (a)'s
  "the approver decides per proposal" understates this; the sharpened cost is
  recorded here as accepted with the ruling.

The options below are **retained deliberately** (the PLAN-0111 convention): a future
reader must see what was rejected and why.

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

**RULED (Cray, typed, s243, 2026-08-21): (b)** — declared event trigger through the
shipped bridge. Cray typed the pick only — no reasoning was given, and none is
recorded here; everything below this ruling line is the PLAN's record, not Cray's.

**The measured state recorded with the ruling (Code, s243, on this branch @
`4913a80` — each re-checkable):**

- **(b) has a live on-disk template; it is not an invention.** Procurement's
  `emergency_sourcing_round` ships `trigger: event` with
  `event_trigger: {event_kind: emergency_source, owning_person_id: req-planner}` on
  a doa_tier + SoD procedure (`verticals/procurement/procedures.yaml:861-868`) — the
  same archetype as fleet's `governed_repair_approval`. The `EventTrigger` model is
  `services/engine/procedures/spec.py:144-186`: `event_kind` unique per vertical,
  cross-ref validated at load; `owning_person_id` = the SP-5 person recorded as the
  SoD requester; `dedup_window_seconds` default 3600, `gt=0`.
- **Flipping the declared trigger does NOT break manual firing — a de-risk the
  option text below did not state.** `_RUNNABLE_TRIGGERS = frozenset({Trigger.MANUAL,
  Trigger.SCHEDULE, Trigger.EVENT})` (`services/engine/procedures/
  orchestrator.py:149`); `validate_runnable` checks only membership in that allowlist
  (`:169-174`); and `run_procedure_endpoint` never reads the procedure's **declared**
  trigger (`services/api/routers/runs.py:370-419` — `_trigger_of` at `:239-242`
  reads the *trigger_context*, i.e. how this particular run was fired). The manual
  console/demo door survives (b) intact.
- **The cost the option text names is smaller than stated: the `# L-1` comment
  already misdescribes its own file.** `verticals/fleet_maintenance/
  procedures.yaml:144` reads `trigger: manual  # L-1: only manual runs in Phase 1
  (the PLAN-0019 precedent)`. L-1 is a genuine PLAN-0019 **LOCKED** scope decision
  (`docs/plans/done/0019-core-procedure-baseline.md:52`, `:65`), but its substance
  ("Phase-1 = `manual` trigger ONLY") has already been lifted twice: the **same
  file** ships `trigger: schedule` at `:496` (annotated Cray-ratified, typed, s163,
  at `:498`), and `event` is runnable per ADR-0029 / PLAN-0056. So (b) corrects a
  stale comment rather than reversing a live lock. **Step 3 must update that
  comment as part of the build.**
- **The composition constraint with SD-2(b) is G-14:** the bridge's stock key must
  carry the accepted quote's identity, or the dedup silently defeats SD-2(b). Step 3
  and AC-2 carry it.

The options below are **retained deliberately** (the PLAN-0111 convention): a future
reader must see what was rejected and why.

**(a)** Imperative: the accept path calls `run_procedure_persisted` directly with the
ruled actor shape — smallest diff, hand-rolled idempotency, wiring lives in the router.
**(b)** Declared: give `governed_repair_approval` an `event_trigger` and fire through
the shipped bridge — deterministic event-keyed run id (idempotency by construction,
ADR-0029 SD-2), owning-person shape built in (G-9), and the vertical's behaviour stays
*declared* (the spine's own thesis, CLAUDE.md §3); costs: the YAML's `trigger: manual`
comment (`procedures.yaml:144`, "L-1: only manual runs in Phase 1") changes meaning as
a declared decision, and the bridge needs a new invocation seam from the accept path
either way (G-9 — today only `actions.py` calls it, behind `event_bridge_enabled`).
**Recommendation:** (b) if SD-1 = (b) (the shapes compose; the idempotency is free
*[qualified s243: free only on the stock key — SD-2(b) requires the quote's identity
in `entity_ids`; G-14]*);
(a) if SD-1 = (a) (the bridge's service-principal actor contradicts firing as the
persona). **SD-1 is now RULED (b) (s242), so the condition holds: the live
recommendation is (b) — the bridge's service-principal + owning-person actor is
exactly the ruled SD-1 shape. SD-5 itself remained unruled when this was written
*[ruled (b) s243 — the stamp above]*.** **Why Cray:** with SD-1
it fixes which precedent (manual-door vs S1/S2-headless) this surface extends — an
architecture-lineage call.

### SD-6 — the dissolved population bound: cap and server-side filtering

**RULED (Cray, typed, s243, 2026-08-21): (b)** — a bounded newest-N default on
`GET /runs`. Cray typed the pick only — no reasoning was given, and none is recorded
here; everything below this ruling line is the PLAN's record, not Cray's.

**The measured state recorded with the ruling (Code, s243, on this branch @
`4913a80`):** the premise holds — `list_runs` (`services/api/routers/runs.py:273-330`)
issues `select(PipelineRun).order_by(PipelineRun.started_at.desc())` with **no
`.limit()`** (`:295-299`); the endpoint is unbounded today, returning every run ever
on each Tab H load (G-15).

The options below are **retained deliberately** (the PLAN-0111 convention): a future
reader must see what was rejected and why.

The two `done/0110:375-383` Out-of-Scope items reopen the moment a visitor can mint
runs (G4 tripwire trigger (ii), pre-armed). **(a)** Accept unbounded at pilot scale:
each run costs a visitor a full open→quote→accept walk, so growth is slow;
rewrite the tripwire's condition in the AC-7 amendment; ship nothing. **(b)** A
bounded newest-N default on `GET /runs` (client filter unchanged, demo runs asserted
within bound) — the minimal cap. **(c)** Server-side status filtering + pagination —
the complete answer, priced as overbuild before any measured need. **Recommendation:**
(b). **Why Cray:** G4 records the cap as Cray's own reopened question by name.

### SD-7 — visitor-run lifecycle: who owns the runs that now accumulate?

**RULED (Cray, typed, s243, 2026-08-21): (a)+(c)** — retain visitor runs; an
operator cancels stale parked ones manually via the existing endpoint. Cray typed
the pick only — no reasoning was given, and none is recorded here; everything below
this ruling line is the PLAN's record, not Cray's.

**The measured state recorded with the ruling (Code, s243, on this branch @
`4913a80`):** (c)'s mechanism is live and scoped exactly where it is needed —
`cancel_run_endpoint` (`services/api/routers/runs.py:538-560`) requires an
authenticated human (403 otherwise, mirroring the resolve guard, `:553-560`), and v1
cancels **only** a `waiting_human` run — any other state is a 409. Visitor-fired
runs park at `waiting_human` (G-12), so (c) applies precisely to them and to
nothing else.

The options below are **retained deliberately** (the PLAN-0111 convention): a future
reader must see what was rejected and why.

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

### The ruled posture, read together (the PLAN's reading — not Cray's)

SD-2(b) accepts Monitor noise as the price of audit completeness: every material
change to a governed spend leaves its own run. SD-6(b) bounds what the Monitor
*displays*, not what exists — the noise is capped at the read side. And SD-7(a)+(c)
assigns the residue to an operator: parked runs that have served their purpose are
cancelled by hand through the existing governed endpoint, never swept. The three
rulings compose — a later reader should not take (b)-on-SD-2 for an oversight that
SD-6/SD-7 then had to mop up.

## Verification

1. **Offline (the gate):** the AC-9 full gates plus, per AC, its own named test —
   each contingent pass read re-fixed at Step 2 before execution, each non-vacuity
   probe SEEN red from a scratch copy (restored from the scratchpad, never from git)
   before its green is claimed. DB-backed tests run from the main checkout against the
   dev Postgres (5442).
2. **Ordering is part of the pass:** AC-1's PR merges before any PR containing a firing
   seam; a PR that lands both in one diff fails review by this line.
   _[First half discharged 2026-08-21: AC-1's PR #1246 merged `f52dbdc` with no
   firing seam yet in existence. The line stays live — it continues to bind
   every future firing-seam PR (Steps 3+).]_
3. **Live (evidence, not the gate):** Step 7 under an explicit typed Cray go — §8
   host-state rules; every fleet redeploy is the by-hand path (PLAN-0110 G11).
4. **Rulings — all seven SDs are RULED; the Step-2 gate is DISCHARGED (s243).**
   SD-1 is **RULED (b)** and stamped in place (Cray, typed, s242 — with Cray's typed
   "two halves" reasoning, the measured state of its premises, and the ADR-0035
   amendment dependency recorded in the same stamp); AC-4 was re-fixed and
   AC-2/AC-5's contingency brackets narrowed in that edit. SD-3 is **RULED (a)**
   (Cray, typed, s243 — a pick with no typed reasoning, recorded as such; the
   measured-state corrections and G-13 recorded with the stamp, AC-5/AC-9 re-fixed
   and Step 5 made unconditional in the same edit, and the SD-1 dependency note's
   `Cf-Access` sentence corrected per Cray's same-turn ruling). SD-2 **(b)**, SD-4
   **(a)**, SD-5 **(b)**, SD-6 **(b)** and SD-7 **(a)+(c)** are **RULED** and
   stamped in place (Cray, typed, s243, 2026-08-21 — picks only: no reasoning was
   typed for any of the five and none is recorded; **SD-2's ruling is NOT the
   option this PLAN recommended** — its stamp says so plainly). In that same edit:
   G-14/G-15 added to §Grounded measurements, AC-2 re-fixed against SD-2(b)+SD-5(b)
   with its sub-ceiling clause corrected, AC-4 annotated with the SD-5(b) actor
   shape, AC-7(ii)'s bound restated in the SD-6(b) shape, AC-8's (a)-branch
   retired, and Steps 3/6 made unconditional. This PLAN stays `Draft`; every ruling
   is stamped in place per SD (`RULED (Cray, typed, date, session): …`) with the
   contingent ACs re-fixed in the same edit (drafter dispatch — `docs/plans/` stays
   G2-gated for Code).

## Post-archival amendment — 2026-08-25 (session 252): SD-4 is REVERSED, and the two clauses that rested on it are superseded

**Why this section exists.** Three sites above carry an inline
`_[Superseded s249 by PLAN-0113 …]_` pointer — SD-4's ruling, AC-7(i)'s NARROWED clause,
and AC-2's sub-ceiling re-fix. All three rest on one fact that is no longer true: fleet's
`intake` was a **fleet-wide population scan**. It is not any more. Written **additively**
per the OQ-1 ruling (Cray, typed, s249): the ruled history above is untouched, every
original word stands, and the pointer is one inserted line beside it.

**What changed, and where.** PLAN-0113 Step 3 (`ca6133e`, PR #1279) authored
`scope_by: {field: case_id, from: trigger.entity_ids}` + `when_absent: sweep` on fleet's
`intake`. An event-fired run now reads only its firing case's rows.

### SD-4 — the reversal, classified

**RULED (Cray, typed, s249, 2026-08-23): re-scope to option (b)** — the option this PLAN
recorded as rejected. Cray's stated reason, verbatim: *"เพราะมันเป็นทางเลือกที่ดู make
sense ที่สุด มันควรมีให้เลือกเฉพาะของตัวเอง ไม่ใช่แสดงมาให้เลือกทั้งกอง"*

🔴 **Classified `superseded by new info` — NOT `was an error`.** (a) was correct in its
context: (b) genuinely WAS outside this PLAN's scope, and the sharpened cost recorded with
the original ruling — that `GateResolveRequest.decisions` *compels* a decision on every
proposal, so an approver re-decides the demo pair on every visitor round — is precisely
the cost the reversal removes. The option (b) text above stands verbatim; it was re-read
and acted on, not rewritten.

### AC-7(i)'s NARROWED clause — the justification is gone; the CONCLUSION survives

The narrowing's reasoning was "every visitor-fired run's gate also decides the seeded demo
case, so its demo-scoped link rows are deleted". Under scoping a visitor's run decides
**its own case alone** and writes **one** link row, so it no longer writes a demo-scoped
one at all.

**The deletion rule itself is unchanged and was re-verified, not assumed** (s252): the
reset still clears link rows on BOTH keys, and its rationale was never the population — it
is **id reuse**. What moved is only *where the both-key deletion is witnessed*: `run_id` on
the seeded runs' own rows (the boot seeder writes three, one keyed on a demo case), and
`case_id` on the one remaining path that puts a demo case on a NON-demo run — a visitor who
accepts ON the demo case. PLAN-0113 AC-5 executed that re-homing.

### AC-2's sub-ceiling re-fix — superseded, and its replacement was MEASURED WRONG TOO

The clause above reads that "**every** visitor-fired run gates, sub-ceiling or not",
because the seeded demo pair always breached. Under scoping that is false.

🔴 **But PLAN-0113 AC-3's predicted replacement — "a sub-ceiling acceptance fires a run
that completes with no gate" — is ALSO false, and is corrected here rather than swapped
in.** Measured s252: `_suspends` (`services/engine/procedures/orchestrator.py:632-644`) is
purely structural — a `gated` action suspends on its KIND, never on whether its input set
holds anything. So a sub-ceiling acceptance fires, `judge` bands it `ok`, `reshape` drops
it, and the run **parks at `approve` with an EMPTY proposal list**; `/gate/resolve` then
answers 409 `has no proposed actions to resolve`. Only `/cancel` exits it today — which
records *abandonment* for a case that was checked and cleared.

**The measured truth, for a future reader:** a sub-ceiling acceptance fires a run that
parks at an empty gate. Not "gates like the others" (this PLAN's reading), and not
"completes with no gate" (PLAN-0113 AC-3's reading). Both were wrong; the third is
measured, asserted by
`tests/api/test_case_acceptance_fires_governed_run_scenario.py::test_an_empty_gate_cannot_be_resolved_so_the_run_is_a_dead_end`,
and is the origin of **PLAN-0113 SD-3**, **RULED (b)** (Cray, typed, s252): such a run must
reach `completed`. **PLAN-0114** carries the build.

**Owning PLAN:** `docs/plans/0113-scope-event-fired-run-to-its-firing-case.md` (§SD-3,
§AC-3, §AC-5, Step 7). Follow-on:
`docs/plans/0114-empty-gate-continuation-acknowledge-and-complete.md`.
