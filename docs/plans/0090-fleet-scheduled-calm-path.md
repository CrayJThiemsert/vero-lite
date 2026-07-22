# PLAN-0090: Fleet Scheduled PM Calm Path — the AT-3 Scheduled Variant (`scheduled_pm_service_round`)

**Status:** Draft
_(Never `Accepted`: that status G1-gates a PLAN's own closeout — the PLAN-0087/PLAN-0089 precedent.)_
**Owner:** Claude Code (executes + commits per ADR-009 D2) + Cray (rules SD-1/SD-2 at Step 0)
**Created:** 2026-07-22 (session 163)
**Related ADRs:** ADR-0028 (SP-4 service actor + SD-P1 per-schedule descriptor), ADR-0025 (D5 —
cited for why the SoD/owning-person *requirement* does NOT attach here), ADR-0032 (D1 — the
"nobody pushed a button" demo beat; D5 — the caveat discipline if SD-2 lands yes), ADR-016
(typed spec + facet), ADR-009 D1/D2 (authoring / commit boundary)
**Related PLANs:** PLAN-0089 (the mandate — this PLAN is its named Out-of-Scope follow-on),
PLAN-0065 (the scheduled-AT-3 donor + the SD-5(b) owning-person precedent), PLAN-0055 (the
scheduler machinery + the Step-8 live-daemon smoke mechanics), PLAN-0086 (the measurement model
+ the local-boot-is-not-host-state precedent), PLAN-0087 (declared criterion vocabulary — why
this PLAN never touches an engine enum)

> Drafted by the in-harness `plan-drafter` subagent (ADR-013 D1); outline + verified fact-pack
> originated by Code (session 163), with L1–L3 ratified by Cray (typed AskUserQuestion, s163)
> BEFORE dispatch. Independent review: Code (R2) + Cray at PR merge. Cray rules on SD-1/SD-2 at
> review — each recommendation below is contingent, not chosen.

## Goal

Add **`fleet_maintenance.scheduled_pm_service_round`** — the scheduled variant of the AT-3 PM
calm path PLAN-0089 shipped manually — so the odometer sweep fires itself daily at 06:00
Asia/Bangkok as a declared service actor and still **parks for a human** at the gated
`schedule_service` step (RF-3: a service actor can never act past the gate). This is the
**second AT-3 scheduled instance** (donor: procurement's `scheduled_low_stock_reorder_round`,
PLAN-0065) and the **cadence contrast** to the fleet AT-2 hero: the hero fires on a breakdown
event and climbs a DOA ladder; this fires on a clock and waits at a single human go/no-go.
Under ADR-0032 D1 that is a demo beat ("nobody pushed a button"), not new machinery: the build
is ~95% vertical config plus one deliberately generic engine fix — retiring the
procurement-only hardcode in `services/engine/cli.py` (L3) so the scheduler daemon can fire
any of the six factory-bearing verticals.

## Mandate

PLAN-0089 named this exact follow-on in its Out of Scope
(`docs/plans/done/0089-fleet-calm-path-extend-an-existing-vertical.md:338-340`):

> **The scheduled variant** (SD-1(b)): schedule descriptor, `service_principals` block,
> `agent.service_principal_ids`, the `cli.py:120-131` branch, and the host-state daemon smoke —
> a named follow-on PLAN.

Its SD-1 ratification (`0089:198-202`) recorded the verified extra cost so this PLAN "starts
grounded" — that cost list is re-verified below. One item in the old list is **corrected** by
this PLAN: the daemon smoke is a **local** boot, and under CLAUDE.md §8's actual definition it
is **not** a host-state action (see AC-6 and Hard-rule 4 below — the PLAN-0086 Step 6
precedent, and session 161's recorded over-application error).

## Verified ground (session-163 fact-pack over the s162 arc, re-verified on disk by this draft 2026-07-22; executor re-verifies at execution HEAD)

### The donor — this is instance #2, not a first

`verticals/procurement/procedures.yaml` ships `scheduled_low_stock_reorder_round`
(`:742-812`, PLAN-0065). Its inline comments settle the design questions this PLAN reuses:

- **A DISTINCT `procedure_id`, never a trigger flip** (`:730-733`): `trigger` is a single enum —
  a schedule descriptor is present IFF `trigger == schedule` (spec.py
  `_validate_schedule_descriptor`) — so flipping the manual `pm_service_round` would break its
  manual runs; and SD-P3 skip-if-in-flight keys on `procedure_id`. The manual path **stays**.
- **RF-3** (`:746-748`, `:794-796`): the scheduled run proposes; a HUMAN resolves the go/no-go.
  A service principal has NO roles by type (`:86-92`) and can never satisfy the human gate.
- The schedule-block shape to copy (`:750-755`): `cron` + `timezone` + `owning_person_id`, each
  with a provenance comment.
- `service_principals:` block at `:93-95` (`svc-buyer`); the agent references it at `:45`
  (`service_principal_ids: [svc-buyer]`, cross-ref validated at load — spec.py `_cross_refs`).

### The engine machinery is ALL shipped — zero engine feature work

- `Schedule` model: `services/engine/procedures/spec.py:90-141`. `extra="forbid"`; `cron`
  non-blank here (authoritative parse = croniter); `timezone` default `Asia/Bangkok`, validated
  against the system tz DB at load (a typo'd zone fails LOUDLY at load, `:128-141`);
  `owning_person_id: str | None`.
- **`owning_person_id` is NOT required for AT-3** — the field's own docstring (`spec.py:117-126`):
  `None` = fully headless, valid for a procedure with no SoD requester to resolve; only a
  `doa_tier` procedure requires SoD (ADR-0025 D5). `pm_service_round` and this variant carry
  **no `doa_tier`, no `separation_of_duties`** — the owning person here is accountability
  parity (L2), not a requirement.
- A scheduled fire REQUIRES the agent to declare a service actor:
  `services/engine/procedures/scheduler_wiring.py:127-135` raises `SchedulerWiringError`
  ("…declares no service_principal_ids — a scheduled run needs a service actor (SP-4)").
- `ScheduleState` (natural key `UniqueConstraint(vertical, procedure_id)`),
  `sync_schedule_states`, `build_resolver`, croniter, `scheduler_daemon` — all generic, all
  shipped (PLAN-0055, `docs/plans/done/0055-s1-schedule-trigger-scheduler-build.md`).
- **Pin safety (checked for this PLAN):** the governance pin snapshots ONLY the procedure's own
  governance projection — `procedure_id`, `separation_of_duties`, and per-step
  kind/autonomy/handler/content/reads/join/project/transform
  (`services/engine/procedures/governance_pin.py:58-120`). It contains **no agent, no
  `service_principals`, no `schedule` key** — so adding `service_principal_ids` to the fleet
  agent and adding the new blocks cannot move any existing procedure's hash. AC-5 still guards
  this with the shipped pin suites (belt and suspenders).

### What `fleet_maintenance` is missing (all verified by grep/read)

- `service_principals:` exists in **procurement only** — repo-wide grep over `verticals/*.yaml`
  finds exactly `verticals/procurement/procedures.yaml:45,:91,:93`. Fleet has none.
- Fleet's agent (`verticals/fleet_maintenance/procedures.yaml:36-50`): `autonomy_ceiling: gated`,
  `step_kinds: [query, evaluate, action, transform]`,
  `action_handlers: [escalate, approve_repair_spend, schedule_pm_service]` — and **no
  `service_principal_ids`**.
- Fleet **does** have `principals:` (`:66-75`): `req-mechanic-tom` (roles `[requester]`),
  `appr-fleet-manager-wirat`, `appr-owner` — so the L2 `owning_person_id` cross-ref resolves.
- Fleet's procedures today: `governed_repair_approval` (`:85`, AT-2) and `pm_service_round`
  (`:311`, AT-3, `trigger: manual` at `:320` with the comment "The nightly odometer sweep is a
  named follow-on PLAN" — this PLAN).
- The executor factory `register_fleet_maintenance_procedure_executors`
  (`verticals/fleet_maintenance/procedures_factory.py:74-114`) is StepKind-keyed and
  procedure-agnostic; the scheduled variant reuses the same three step kinds + the already
  registered `schedule_pm_service` handler → **zero factory change, zero handlers.py change,
  zero ontology/adapter/regen work** expected. Any discovered exception is a deviation to
  surface, not absorb.

### The CLI gap — the one engine edit (L3), with a corrected failure mode

`services/engine/cli.py:120-131`: `_register_executor_factory` is literally
`if vertical == "procurement": …register_procurement_procedure_executors()`. Its docstring
(`:121-123`) is **stale** — "Only procurement ships one today; energy has none by design" is
false: **six** verticals ship a factory, and `services/api/main.py:97-146` wires all six in
`_PROCEDURE_EXECUTOR_REGISTRARS` (aquaculture, energy, procurement, supply_chain,
building_materials, fleet_maintenance).

**Correction to the inherited claim** (verified this draft): the dispatch fact-pack said the
daemon "can tick a fleet schedule but the fired run 409s at resolve" — that echoes the stale
docstring, and it is **not** the current behavior. `_run_scheduler` calls
`registry.get_procedure_executors(vertical)` **unguarded** (`cli.py:151`), and the registry
**raises `RegistryError`** when no factory is registered
(`services/engine/registry.py:114-121`). So today
`uv run vero-lite scheduler --vertical fleet_maintenance` **crashes at daemon startup** — it
never ticks at all. Same fix either way (L3); the loud-crash reality makes the generic fix
*more* motivated, and AC-4 asserts the startup now succeeds.

`_run_scheduler` already calls `discover_and_register()` first (`cli.py:148`) — action handlers
are fine; only the procedure-executor factory dispatch is procurement-hardcoded.

### The census + catalog surface (counted prose — 12 → 13)

- Canonical catalog: `docs/conventions/procedure-archetypes.md` — the AT-3 row (`:50`) lists
  three instances today; the §AT-3 instance list is at `:157-186`. **Canonical grows first, the
  mirror follows** (the map's own comment, `services/api/routers/procedures.py:27-49`).
- Mirror: `PROCEDURE_ARCHETYPES` is keyed on **`(vertical, procedure_id)`** with
  `archetype_for()` as the single read point (PR #850;
  `services/api/routers/procedures.py:50-93`). **Hard rule 1: read the file at execution HEAD —
  never copy its shape or line numbers from this prose.** Every `procedures.py` /
  `test_procedures_endpoint.py` citation in this PLAN carries a known expiry.
- Counted prose at twelve, verified today (the executor re-sweeps — PLAN-0089's closeout lesson
  3 found FIVE stale counts where two were tracked; the lesson is **the sweep, not the count**):
  `services/api/routers/procedures.py:31` ("Twelve shipped"), `:81` ("all twelve shipped
  procedures are mapped today"); `tests/api/test_procedures_endpoint.py:30`, `:111`, `:140`
  (prose) and `:146` (`assert total == 12`). The `_EXPECTED` pin (`:40-…`) + the #850
  set-equality tripwire (`:258-276`) go RED the moment the spec ships the new procedure without
  the catalog/mirror/pin updates — by design.
- `services/engine/procedures/prose_lint.py` exists (`:78` carries a number-word pattern) — the
  executor checks whether it already polices these files before hand-sweeping more.

## Hard rules this PLAN encodes (binding on the executor)

1. **`PROCEDURE_ARCHETYPES` is read from the file, never from prose** — PR #850 re-keyed it to
   `(vertical, procedure_id)` and added `archetype_for()` + a set-equality tripwire; any prose
   citation of it (including this PLAN's) has a known expiry.
2. **The counted-prose census moves 12 → 13** — all sites above plus a fresh sweep; PLAN-0089
   needed a separate `docs(api)` prose-sync commit (`610061b`) for exactly this class.
3. **The AT-3 shape is preserved**: no `doa_tier`, no `separation_of_duties`, no
   `compliance_criteria` on the new procedure. The gate advisory stays absent **by
   construction** — `GovernanceActionExecutor.execute` branches on `step.governance_content`
   and delegates to the base executor; the advisory builder runs only inside `_doa_tier`
   (`services/engine/procedures/governance_step.py:183-191`, `:235-238`). No test may expect an
   advisory entry.
4. **The daemon smoke is a LOCAL boot and NOT a host-state action.** CLAUDE.md §8 scopes
   host-state to running a model on MS-S1 or changing host/global config outside the worktree.
   PLAN-0086 Step 6 records the same reading verbatim ("Local demo stack only — no MS-S1, no
   host-state change (§8)"), and session 161 recorded over-applying §8 here as an **error**.
   There is **no explicit-Cray-go gate** on AC-6; it remains *evidence, never a CI gate* (§8's
   offline-oracle rule).
5. **Dev Postgres is on host port `5442`, not 5432** (ADR-003 `POSTGRES_HOST_PORT`); a worktree
   ships no `.env`, so DB tests **silently skip** and a live run 500s with
   `ConnectionRefusedError`. The quantitative tell: **~8 skips = DB connected, ~141 skips =
   not.** Check the skip count before trusting a "green" DB-touching run.
6. **Engine-diff budget (closed set):** `verticals/fleet_maintenance/procedures.yaml` + (only
   if a factory change proves needed, which is not expected) `procedures_factory.py` + the
   `PROCEDURE_ARCHETYPES` pair + the census prose/test updates + the catalog entry + the
   `cli.py` generic fix (L3) + this PLAN's new tests. Anything beyond is a **finding to
   surface** (deviation record + STOP on any engine file outside `cli.py`), never to absorb.

## LOCKED decisions (Cray-ratified, typed AskUserQuestion, 2026-07-22 s163 — do not reopen)

- **L1 — cadence: `cron: "0 6 * * *"`, `timezone: Asia/Bangkok`** (daily 06:00, before day
  shift). Rationale Cray accepted: the odometer moves daily, so a daily sweep matches the
  signal; and it is the cadence contrast to the hero, which fires on an event. (Donor runs
  05:00; the hour difference is deliberate — this is the fleet's morning sweep, not a copy of
  procurement's overnight one.)
- **L2 — `owning_person_id: req-mechanic-tom`** (ต้อม, ช่างใหญ่ — the `requester`-role human, the
  exact analog of procurement's `req-planner`). Follows **PLAN-0065 SD-5(b)**: not required for
  AT-3, carried anyway so the run/audit record names the accountable human behind an unattended
  sweep. It is **NOT** an SoD requester — this path has no SoD; the in-file comment must say so
  (the donor's `:735-741` wording is the model).
- **L3 — fix `cli.py` GENERICALLY inside this PLAN**: replace the `if vertical == "procurement"`
  hardcode with a vertical → registrar mapping covering all **six** factory-bearing verticals,
  mirroring `services/api/main.py:97-146`, and delete the stale docstring sentence. Cray chose
  this over a 4-line fleet-only branch and over splitting it into its own PR.

## Surfaced decisions (SD-N — Cray rules at Step 0; recommendations are contingent, not chosen)

### SD-1 — The service principal's id + display name

**Question:** fleet's first `service_principals:` entry — what id and display name?

**Recommendation:** `svc-fleet-scheduler`, display name in the house style of the vertical's
existing Thai principals and of procurement's donor SP ("Auto Buyer (บอทจัดซื้ออัตโนมัติ — ตัว
trigger รอบกลางคืน)") — e.g. `"Fleet PM Scheduler (บอทรอบตรวจระยะอัตโนมัติ — ตัว trigger
รอบเช้า 06:00)"`. The id names the *function* (scheduling fleet sweeps), stays vertical-scoped,
and leaves room for a future second SP.

**Alternatives:** `svc-fleet-pm` (shorter, but reads as "the PM bot" rather than the trigger
actor); `svc-odometer-sweeper` (cute, but couples the id to one procedure when SP-4 actors are
agent-scoped).

**Why Cray:** naming is an established Cray call in this repo (PLAN-0089 SD-3 pinned
`pm_service_round` over `tire_*`; PLAN-0065 named the donor SP) — the name lands in every
audit record the demo shows.

### SD-2 — Measure this build, or not?

**Question:** PLAN-0089 produced **~14 min hands-on** for "extend an existing vertical" (new
procedure, same vertical). This build varies a **different axis** — trigger (manual → schedule),
not vertical — so a timed run would be a third companion data point ("put an existing governed
path on a clock"). Run it timed?

**Recommendation: yes — but ONLY with the protocol pre-committed before Step 0's clock**,
exactly as PLAN-0089 did (a measurement designed after the fact is not a measurement). The
protocol below (MS-1…MS-6) is written now so ratification activates it unchanged. If Cray
declines, the steps run untimed, AC-7 is struck, and the closeout says so plainly — no
retroactive number.

**Alternatives:** (a) untimed — the build is small and the portfolio already has two numbers;
defensible if the pitch never needs the scheduling-cost claim. (b) timed without a protocol —
rejected outright (violates the PLAN-0086/0089 measurement discipline).

**Why Cray:** whether the pitch needs a third number — and whether a ~15-minute-class
measurement is worth its protocol overhead this cycle — is portfolio judgment (ADR-0032 D5).

## The measurement protocol (pre-committed; ACTIVE iff SD-2 resolves YES — binding via AC-7)

- **MS-1 Claim:** the marginal hands-on cost of putting an existing governed calm path on a
  clock (schedule descriptor + service actor + daemon wiring), given a shipped scheduled donor
  in another vertical. Companion to PLAN-0086's 27m39s (create a vertical) and PLAN-0089's
  ~14 min (extend a vertical). **Three numbers, three claims — never summed.**
- **MS-2 Arm:** manual hand-port from the procurement donor; no generator.
- **MS-3 Clock:** starts when Step 2 (YAML authoring) begins, after the untimed Step-0/Step-1
  pre-flight; stops at the first AC-6 daemon-smoke pass (park read back from Postgres). The L3
  `cli.py` fix is **inside** the clock — it is part of what "putting a vertical on a clock"
  costs today. If the smoke is deferred, the clock stops at AC-3's first green and the closeout
  records the shorter finish line as a comparability caveat.
- **MS-4 Granularity:** checkpoint rows at the Step grain (~4 rows: YAML / catalog+census /
  cli.py+tests / smoke), wall + hands-on split, interruptions logged with reason and deducted.
  Timing artifact gitignored under
  `docs/research/private/2026-07-NN-fleet-scheduled-timing-log.md`; summary lands in this
  PLAN's closeout.
- **MS-5 Intake:** none expected — L1/L2 already fix the schedule facts, and no new customer
  value is authored (the due points shipped with PLAN-0089). Any question that does arise is
  logged and its wait deducted.
- **MS-6 The binding honesty caveat (never quote the number without it):**

  > The measured time is the marginal cost of scheduling an existing governed calm path under
  > **maximally favourable conditions**: the same operator who built the manual path
  > (PLAN-0089) and read the scheduled donor, on a codebase they know deeply, with all
  > scheduler machinery already shipped (PLAN-0055) and the design decisions pre-ratified
  > (L1–L3). It is a **LOWER BOUND**. It does NOT measure scheduler-machinery construction,
  > blind intake, or a fresh operator. **Never present it summed with PLAN-0086's 27m39s or
  > PLAN-0089's ~14 min as one workflow** — they are companions, not addends.

## Acceptance Criteria

All gates are offline (CLAUDE.md §8 — the offline oracle is the gate); AC-6 is live *evidence*,
never a CI gate. Every pass/fail read below is fixed here, before the run.

- [ ] **AC-1 Offline gate + census 12 → 13 (owns the census tripwire):** full suite green at
  execution HEAD with the census updates — catalog entry first
  (`docs/conventions/procedure-archetypes.md` AT-3 row + §AT-3 instance list), then the
  `PROCEDURE_ARCHETYPES` pair `("fleet_maintenance", "scheduled_pm_service_round"): "AT-3"`,
  the `_EXPECTED` fleet entry, `assert total == 12` → `13`, and the counted-prose sweep
  (§ census above — all named sites plus a fresh repo sweep; check `prose_lint.py` coverage
  first). Plus `mypy --strict services/` and `ruff check` / `ruff format --check` at CI scope
  (the whole tree, not the changed subset).
- [ ] **AC-2 Spec loads with the scheduled wiring (offline):** `load_procedures
  ("fleet_maintenance")` green with the new procedure — schedule descriptor present iff
  `trigger: schedule`; `service_principal_ids` ↔ `service_principals` and `owning_person_id` ↔
  `principals` cross-refs resolve; the AT-3 absence properties hold on the new procedure (no
  `doa_tier`, no `separation_of_duties`, no compliance criteria, and its steps are the same
  three-step spine as `pm_service_round`). A negative control: a copy of the spec with
  `trigger: schedule` and **no** `schedule:` block (or a bogus timezone) fails loudly at load.
- [ ] **AC-3 Fired-run park (offline, owns the run-through test):** driving the shipped
  resolver path (`sync_schedule_states` registers the `(fleet_maintenance,
  scheduled_pm_service_round)` `ScheduleState` row; `build_resolver` resolves the SD-1 service
  actor per SP-4), a fired run completes `read_odometer → judge_service_due`, parks
  `waiting_human` at the gated `schedule_service` step with the breach set = exactly the due
  truck(s), records the service actor (`actor_kind: "service"`) and the L2 owning person, and a
  human resolution completes it. Donor patterns: `tests/services/db/test_scheduler_wiring.py`,
  `tests/services/db/test_scheduled_procurement_demo.py` (note both live under
  `tests/services/db/` — Hard rule 5's skip-count tell applies). No advisory entry is expected
  or asserted (Hard rule 3).
- [ ] **AC-4 The generic CLI fix (L3):** `_register_executor_factory` dispatches over all
  **six** factory-bearing verticals via a mapping mirroring `services/api/main.py` (lazy
  imports preserved — the CLI must not import every vertical at startup); the stale docstring
  sentence is gone; and a new **coverage tripwire test** asserts the CLI mapping's vertical set
  `==` `services/api/main.py:_PROCEDURE_EXECUTOR_REGISTRARS`' key set (set-equality, so a 7th
  vertical added to one but not the other goes RED — the structural fix for the
  stale-docstring failure class). Pass read: `uv run vero-lite scheduler --vertical
  fleet_maintenance` reaches "OK: scheduler …" startup output instead of raising
  `RegistryError` (the corrected failure mode above). Implementation detail (dict-in-`cli.py`
  vs a shared module) is the executor's call; the tripwire test is not.
- [ ] **AC-5 Additivity:** the AT-2 hero suite and the PLAN-0089 calm-path suite
  (`tests/verticals/fleet_maintenance/`) green **unmodified**; the shipped pinned-hash /
  governance-pin suites green (expected by construction — the pin has no agent/schedule key,
  `governance_pin.py:58-120` — but guarded anyway; if any existing hash moves, STOP and
  surface, never re-pin silently); `git diff` over the change set touches **no** file of the
  five other verticals, no `services/engine/` file except `cli.py`, and no `services/api/`
  file except `routers/procedures.py`.
- [ ] **AC-6 Local daemon smoke (evidence, not a gate; NOT host-state — Hard rule 4):** on the
  local demo stack (local uvicorn-seeded Postgres at host port 5442), run the scheduler daemon
  for `fleet_maintenance`, confirm the ScheduleState row registers, force a fire per the
  PLAN-0055 Step-8 donor mechanics (backdate the persisted next-fire state — **never** edit the
  L1 cron to force a smoke), and read the persisted run back from Postgres:
  `waiting_human` at `schedule_service`, service actor recorded, verdicts matching the offline
  run. No MS-S1, no Cray gate.
- [ ] **AC-7 The measurement (IFF SD-2 = yes; struck with a note if no):** the run is executed
  under MS-1…MS-6 *as pre-committed above* — clock per MS-3, rows per MS-4 — and the **MS-6
  caveat appears co-located with the number everywhere it is recorded** (closeout, STATUS, any
  pitch note). A protocol deviation is recorded as a deviation, never retro-fitted.

## Out of Scope

- ❌ **A first-class `Tire` object** — parked pending a design-partner per-tyre data source;
  recorded in the vertical's gaps register (`verticals/fleet_maintenance/README.md:70`).
- ❌ **The generator-assisted arm** — belongs to the scaffolder-tool PLAN, which **does not
  exist yet** (an honest forward reference from PLAN-0086's Out of Scope; nothing here blocks
  on it).
- ❌ **Any event-trigger variant** of the PM path; **new trace kinds**; **new UI surfaces**.
- ❌ **Real PM / garage I/O** — `schedule_pm_service` stays a no-op receipt stub.
- ❌ **Retiring or flipping the manual `pm_service_round`** — the distinct-`procedure_id`
  design keeps it runnable (donor rationale, `verticals/procurement/procedures.yaml:730-733`).
- ❌ **The multi-SP schedule-picks-its-actor refinement** noted in
  `scheduler_wiring.py:128-130` — first-declared-SP semantics are kept.
- ❌ **Any engine change beyond the L3 `cli.py` fix** — if the build discovers one is needed,
  STOP and flag (Hard rule 6; it belongs in the deviation record).

## Steps

### Step 0: SD ratification gate (untimed)

Present SD-1 (SP naming) and SD-2 (measure or not) to Cray via AskUserQuestion; record per-SD
stamps inline in this PLAN (the PLAN-0086/0089 pattern). L1–L3 are already LOCKED — restate,
do not re-ask. If SD-2 = yes, pre-create the gitignored timing artifact with the MS-4
checkpoint template before any authoring. No implementation before ratification.

### Step 1: Pre-flight (untimed)

Working tree clean (stash unrelated drafts — pre-smoke hygiene); baseline full-suite state
known at execution HEAD (note the skip count — Hard rule 5); open the known-expiry files and
read current values: `services/api/routers/procedures.py` (map shape + census prose),
`tests/api/test_procedures_endpoint.py` (`_EXPECTED`, `total ==`, tripwire),
`docs/conventions/procedure-archetypes.md` (AT-3 row + instance list), `services/engine/cli.py`,
`services/api/main.py` registrar dict. No authoring.

### Step 2: The vertical YAML (timed if SD-2 = yes — clock starts)

In `verticals/fleet_maintenance/procedures.yaml`:
1. Add the `service_principals:` block (SD-1 id + display name), with the donor's RF-3 comment
   pattern (`verticals/procurement/procedures.yaml:86-95` is the model).
2. Add `service_principal_ids: [<SD-1 id>]` to `fleet_maintenance_agent` with the cross-ref
   comment (donor `:40-45`).
3. Author `scheduled_pm_service_round`: title + goal prose stating the cadence-contrast beat;
   `run_by: fleet_maintenance_agent`; `trigger: schedule`; the L1/L2 block —

   ```yaml
   schedule:
     cron: "0 6 * * *"              # L1 (Cray, s163): daily 06:00 before day shift — the
                                    # odometer moves daily; the cadence contrast to the
                                    # event-fired hero
     timezone: Asia/Bangkok         # SD-P1 per-schedule IANA tz (validated at load)
     owning_person_id: req-mechanic-tom   # L2 (Cray, s163): PLAN-0065 SD-5(b) accountability
                                          # parity — NOT an SoD requester; this AT-3 path
                                          # has no SoD
   ```

   Steps = the `pm_service_round` three-step spine reused verbatim (`read_odometer` →
   `judge_service_due` → `schedule_service`, `terminal: schedule_service`), with the
   distinct-`procedure_id` rationale comment mirrored from the donor (`:730-733`). No
   `doa_tier`, no SoD, no criteria (Hard rule 3).

### Step 3: Catalog + census (timed if SD-2 = yes)

Canonical first: the `procedure-archetypes.md` AT-3 row + §AT-3 instance entry (the 2nd
scheduled AT-3 instance; note it is scheduled-on-a-second-vertical). Then the mirror pair, the
`_EXPECTED` entry, `total == 13`, and the counted-prose sweep (AC-1). Expect the #850 tripwire
to be RED between the spec landing and this step completing — that is it working.

### Step 4: The L3 generic CLI fix + tests (timed if SD-2 = yes)

Replace the `cli.py:128-131` hardcode with the six-vertical mapping (lazy imports inside the
dispatch, mirroring `main.py:97-146`); rewrite the docstring (drop the false sentence; keep the
OQ-6 explicit-registration rationale and the handlers-vs-factory distinction). Add the AC-4
coverage tripwire test + the AC-2/AC-3 test modules (donor patterns per AC-3; place beside the
donors under `tests/services/db/` unless an in-memory seam proves cleaner — executor's call).

### Step 5: Offline gate (timed if SD-2 = yes)

Full suite + `mypy --strict services/` + ruff at CI scope; AC-5 diff-budget check
(`git diff --stat` against the Step-1 baseline, read against Hard rule 6's closed set).

### Step 6: Local daemon smoke (timed if SD-2 = yes — clock stops at first AC-6 pass)

Local demo stack up (Postgres 5442; seed via the demo boot if the DB is fresh); run
`uv run vero-lite scheduler --vertical fleet_maintenance`; verify startup registers the
schedule row (the "N schedule(s) registered" line); force-fire per the PLAN-0055 Step-8
mechanics; read the persisted parked run. No MS-S1, no host-state change (Hard rule 4).

### Step 7: Closeout (untimed)

If SD-2 = yes: timing summary + the MS-6 caveat into this PLAN's closeout; the caveat travels
to STATUS and any pitch note co-located with the number. Either way: AC evidence table read
from **fresh on-disk artifacts at the merge commit** (never from the build session's memory);
PR referencing PLAN-0090 (branch + PR, CLAUDE.md §7); after merge + Cray confirmation,
`git mv docs/plans/0090-*.md docs/plans/done/`.

## Verification

1. AC-2 + AC-3 + AC-6: the sweep fires itself on a clock, as a typed service actor, and still
   parks for a human — the ADR-0032 D1 demo beat, demonstrated on a second vertical with the
   engine unchanged.
2. AC-4: the scheduler daemon is no longer procurement-only — the tripwire keeps the CLI and
   the API lifespan's vertical sets equal forever, which is the structural end of the
   stale-docstring class.
3. AC-5: the addition is purely additive — the hero, the manual calm path, their hashes, and
   five other verticals untouched.
4. AC-1: the census + catalog say thirteen everywhere anything counts them, and the tripwire
   proves the three surfaces (spec / catalog mirror / test pin) agree.
5. AC-7 (if taken): a third honest number exists, arithmetic closed, caveat attached — and it
   never travels summed with its two companions.

---

> **Author≠reviewer disclosure (ADR-012 D4.3):** drafted by the in-harness `plan-drafter`
> subagent from a Code-verified session-163 fact-pack with L1–L3 Cray-LOCKED pre-dispatch;
> independent review by Code (R2) and Cray at PR merge; SD-1/SD-2 ruled by Cray at Step 0.
> Separation intact.
>
> **Drafter's corrections/additions beyond the dispatch (flagged for R2):** (1) the CLI failure
> mode corrected — startup `RegistryError` crash (`cli.py:151` + `registry.py:114-121`), not
> tick-then-409; (2) the governance-pin safety check (`governance_pin.py:58-120` — no
> agent/schedule key, so existing hashes cannot move) grounding AC-5; (3) the AC-4 CLI↔main.py
> set-equality coverage tripwire as the structural fix for the stale-docstring class; (4) the
> donor test modules located (`tests/services/db/test_scheduler_wiring.py`,
> `test_scheduled_procurement_demo.py`) with the DB-skip caveat attached; (5) the
> never-edit-the-cron-to-force-a-smoke rule in AC-6 (live-test trigger-freshness discipline);
> (6) the MS-1…MS-6 protocol pre-committed in-draft so an SD-2 "yes" activates it unchanged;
> (7) `prose_lint.py` flagged for the census sweep.
