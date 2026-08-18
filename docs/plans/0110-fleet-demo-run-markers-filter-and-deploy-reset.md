# PLAN-0110: Fleet Demo Lifecycle — Tab A Run Markers, Three-Mode Filter, Deploy-Time Reset

**Status:** Draft
**Owner:** Claude Code
**Created:** 2026-08-18
**Related ADRs:** ADR-0032 (demo→pilot wedge — the published fleet demo IS the wedge artifact), ADR-0035 (published-surface decisions), ADR-0025 (the `request → approve → fulfill` spine shape), ADR-016 (run records + audit chain)
**Related PLANs:** PLAN-0084 (map↔monitor run linkage — SD-C/SD-D rulings this PLAN inherits), PLAN-0103 (published fleet profile), PLAN-0105 (case retention — the deletion-ordering precedent and the SD-4 link-row ruling this PLAN diverges from, explicitly), PLAN-0107 (backlog-case seeds, untouched)

> Drafted by the in-harness `plan-drafter` subagent (ADR-013 D1 phased authority) from
> Code's session-237 dispatch + fact-pack; amended same-session per Cray's (ข) ruling
> (fold in SD-E — the visitor-case→run gap, G10) from Code's follow-up dispatch, all
> new anchors re-verified on disk. Independent review: Cray at PR merge.
> Baseline: `main` @ `808bfc0`. PLAN-0109 (open PR, Ask ontology) is **not** a
> dependency of this PLAN and must not become one.

## Goal

Fleet's published demo (`oct-fleet-maintenance`) has two lifecycle defects, both
measured live on 2026-08-18: **Tab A renders zero governed-run markers** (both fleet
runs return `subject: null` from `GET /runs`, so the double-gate at
`services/api/static/assets/view-map.js:92-97` skips them), and **the central
refused-then-granted approve beat is consumable exactly once per deployment**
(`services/api/main.py:307` skips the seed whenever the run row exists, in any state —
so the first visitor who plays the beat consumes it for every visitor after them).
This PLAN ships three pieces in one deploy: (1) backfill the demo runs' `subject`
**after** `intake` has resolved the truck — delivering, for fleet, exactly what
PLAN-0084 SD-D intended ("map ingest filters on `subject` presence"; fleet never
received the stamp, this is not a new feature); (2) a three-mode Tab A run-marker
filter — **in-flight (default, unchanged per PLAN-0084 SD-C) / completed / all**;
(3) a deploy-time reset that returns the demo to its pristine two-run state — one run
parked at the `approve` gate (`waiting_human`), one completed through both gates —
which is precisely what a fresh boot already produces since PR #1209 (`90a8f67`), so
the reset's job is to **make the seed able to rebuild**, not to invent a new end state.
Per Cray's 2026-08-18 (ข) ruling this PLAN additionally surfaces — as SD-E, without
pre-deciding it — the measured gap that **a visitor's own case can never enter a
governed run on the published profile** (G10), because the chosen answer changes
G4's population bound and therefore the filter-cap and reset-scoping ground the
other pieces stand on.

## Ground — measured facts this PLAN stands on

All anchors re-verified on disk at drafting time (2026-08-18). Cite these; do not
re-derive.

**G1 — Tab A's double gate.** `view-map.js:92-97` (`computeRunFlags`) requires
`subject.object_type` + `subject.primary_key` + `RUN_INFLIGHT[r.status]`;
`view-map.js:19` pins `RUN_INFLIGHT = { waiting_human: 1, running: 1 }` (PLAN-0084
SD-C). Live-measured: `GET /runs` on the published fleet system returns both runs
with `subject: null` → zero markers regardless of status.

**G2 — the null is deliberate, and its reasoning is time-scoped.**
`verticals/fleet_maintenance/operate_seed.py:164-169` (the `trigger_context` NOTE):
fleet's breaching truck is chosen by the declared query **during** the run, so it is
not knowable at trigger time and inventing it would assert an asset the run had not
yet picked. Correct at trigger time — and silent about **after** `intake` has run,
which is where this PLAN acts. (Both demo cases are on `truck-02` —
`operate_seed.py:417-420`; the ontology object is `Truck`, pk `truck_id` —
`verticals/fleet_maintenance/ontology/fleet_maintenance_v0.yaml:33-34`.)

**G3 — the prior rulings inherited, not reopened.** PLAN-0084 SD-C (RATIFIED, Cray,
2026-07-20 s155): distinct in-flight marker, lights `waiting_human` + `running`,
"never terminal states" — the marker is demo-stage vocabulary Cray narrates live.
→ **The filter's default stays in-flight-only**; the completed/all modes are Cray's
own 2026-08-18 typed direction and are opt-in views layered on top — recorded here as
an explicit extension of SD-C's "never", scoped to non-default modes only.
PLAN-0084 SD-D: v1 ships map ingest filtering on `subject` presence; a run without a
subject simply carries no marker. Fleet never got the stamp — piece 1 delivers SD-D's
intent for fleet.

**G4 — why the "all" mode needs no cap (Cray's explicit question).**
`deploy/published/oct-fleet-maintenance/cloudflared/config.yml` is an anchored-regex
allowlist; `POST /procedures/{id}/run` is deliberately excluded (`:12-15` explains the
anchoring exists so an unanchored pattern cannot admit it "without anyone deciding
to"; `:111-112` and `:202` name the route). **A visitor cannot create a run**; runs
come from the boot seed only, so the population is structurally bounded at 2. The
bound is a *consequence of the allowlist* — **tripwire: if that route is ever
admitted, the cap question reopens** and this paragraph is the place that says so.
**⚠️ Contingency (added under Cray's 2026-08-18 (ข) ruling):** this bound holds
today and under SD-E option (d) only. SD-E options (a), (b) and (c) each give
visitor activity a way to produce runs, which **dissolves the bound** — the "all"
mode regains an unbounded axis and the reset's "exactly two runs" pristine claim
becomes "exactly two *demo* runs among N visitor runs". The per-candidate pricing
lives in SD-E; this paragraph must be rewritten, not deleted, when SD-E is ratified
to a build option.

**G5 — the consumable-once defect, precisely.** `services/api/main.py:307`:
`if await load_run(session, DEMO_RUN_ID) is not None: return` — the seed skips on row
*existence*, in any state. `^/runs/[^/]+/gate/resolve$` **is** allowlisted
(`config.yml:142`) and personas ship with keys: a visitor resolving the gate is the
*designed* interaction (`deploy/published/oct-fleet-maintenance/card-copy.md` — the
refused-then-granted beat). Two-gate nuance (measured, `operate_seed.py:518-525`):
`governed_repair_approval` is `request → approve → fulfill` with a **gated terminal
step**, so resolving `approve` parks the run again at `fulfill`, still
`waiting_human`; resolving `fulfill` completes it. `/cancel` (`config.yml:148`,
endpoint `services/api/routers/runs.py:538`) is a second consumption route. All three
consumed shapes — parked-at-fulfill, completed, cancelled — leave the beat unplayable
for the next visitor, and the seed never re-arms.

**G6 — Cray's piece-3 ruling, translated honestly.** Cray (typed, 2026-08-18): on a
new deploy, clear the runs left behind by visitor play and restore exactly two example
runs — one `WAITING_HUMAN`, one `COMPLETED`. Against G4 there are **no surplus runs to
prune** — visitors cannot create runs. The operation is a **reset of the two seeded
runs to their pristine states**, not a sweep. This PLAN implements no prune, and the
target state is what a fresh boot already produces post-PR #1209: `run-fleet-operate-
demo` parked at `approve` (`waiting_human`), `run-fleet-demo-history` completed
through both gates.

**G7 — deletion mechanics + the rebuild constraint.**
`services/engine/procedures/runs.py:85` (`pipeline_runs`), `:123` (`step_results`),
`:133` (`run_id` FK → `pipeline_runs.run_id`, **no `ondelete`**): children delete
before the parent, and the loud FK failure on a bare parent delete is a safety
property (PLAN-0105 SD-1 kept it deliberately). No run-delete path exists today —
only `cancel_run` (`services/engine/procedures/persistence.py:491`, a status change).
Precedent to copy: `services/db/repair_case_retention.py` (`FK_CHILD_DELETION_ORDER`,
`delete_case` — files-first, explicit child-to-child ordering; PLAN-0105 already paid
for an ordering defect here). **Rebuild constraint (measured):**
`seed_settled_history_case` is idempotent **on the case id**
(`operate_seed.py:410`), its round only proposes OPEN cases, and the history case is
CLOSED at the end (`:400-406`, `:592-594`) — so a run-only delete leaves a closed case
standing and the seed can never rebuild the history run through the real path. The
reset must delete deep enough that the existing seeds rebuild everything through the
same code path a virgin boot uses.

**G8 — the audit chain is NOT at risk, and nobody should re-litigate it.**
`services/db/audit_log.py:97`: `run_id` is `Text, nullable=True`, **no ForeignKey**.
`verify_chain` (`:213-234`) walks the tenant's rows ordered by `audit_id` recomputing
`row_hash` + `prev_hash` linkage — **it never reads runs**. Deleting a run leaves the
chain intact and leaves the audit record of that run standing. Demo talking point,
one sentence: *the demo resets; the audit log remembers.*

**G9 — anchor correction to the dispatch fact-pack.** `PipelineRunStatus` lives at
`services/engine/procedures/runs.py:44-52` (five statuses: `running`,
`waiting_human`, `completed`, `failed`, `cancelled`) — the dispatch's `:78` anchor is
`StepResultStatus.RESOLVED_PROVISIONAL`, a *step* status that never appears in
`GET /runs`' run `status` field. SD-B enumerates the run enum only.

**G10 — a visitor's case can never enter a governed run on the published profile
(measured 2026-08-18; the gap SD-E surfaces).** Four facts, each re-verified on disk:

1. **Case intake fires no run.** `POST /api/cases` (`services/api/routers/cases.py:
   183-219`, `open_case`) writes a `RepairCase` row, commits, returns — no procedure
   is fired. The repo's own visitor scenario proves it by construction:
   `tests/api/test_visitor_case_to_monitor_scenario.py:371` fires the run as an
   **explicit separate step** (`await client_with_db.post(f"/procedures/{_HERO}/run",
   …)`) — a line that would not exist if opening a case created one.
2. **The firing route is tunnel-excluded by design** (G4): the config's own comment
   (`config.yml:111-112`) says the anchor keeps out `POST /procedures/{id}/run`,
   "which would let an **anonymous** visitor start a governed run."
3. **The seeded gate cannot adopt a later case.** Gate proposals are frozen in the
   parked step's persisted artifact at suspend time — `resolve_gated_step` decisions
   are keyed to the artifact's `output_set` (`operate_seed.py:555-558`;
   `routers/runs.py` `_proposals(suspended)` reads the same artifact) — so a case
   opened after boot can never reach the already-parked gate. The only way a
   visitor's case gets governed is a **new** run.
4. → The visitor's case sits `OPEN` and ungoverned forever. **PLAN-0103 AC-8
   clause 2** — "the visitor still gets to watch their *own* case enter the loop",
   quoted verbatim in `operate_seed.py:7-9` — is **unreachable on the published
   profile** (it was authored against the dev console, where the route is
   reachable). **Narrative-surface measurement (refines the dispatch):** the
   card-copy's "First 90 seconds" section (`card-copy.md:36-42` TH / `:69-75` EN)
   rides the *seeded* run and IS reachable; the sentence that overpromises is in
   "What you'll see" — TH `:26-27` ("ใบเสนอราคาซ่อมที่เกินเพดาน ฿5,000
   จะวิ่งเข้าสายอนุมัติเอง …") and EN `:58-59` ("A repair quote above the ฿5,000
   ceiling routes itself into the approval chain") — true of the system, false of
   anything the visitor does with their own case on this surface.

**The security shape, verified rather than assumed:**

5. `run_procedure_endpoint` (`routers/runs.py:370-419`) resolves
   `auth: AuthContext` and sets `trigger_context["triggered_by"] = auth.person_id`
   server-owned (`:391`), passing `principal=auth.person` (`:405`).
   `api_auth_enabled` defaults `True` (`services/api/config.py:71-78`; its
   description names the "PLAN-0047 run/gate-resolve endpoints"), and fleet's
   `published.env:85` sets `API_AUTH_ENABLED=true`. Personas ship keys to the
   browser by design (PLAN-0103 Step 6; `published.env:88` documents the
   `UI_DEMO_PERSONA_KEYS` machine-side secret). → A keyed persona's request is
   **not anonymous**, and the app layer refuses an unkeyed one. **Whether the
   tunnel exclusion is therefore belt-and-braces or is load-bearing for a reason
   its comment does not state is an open question SD-E asks — this PLAN does not
   answer it by assumption.**
6. **🔴 Verified asymmetry between the two doors.** `resolve_gate_endpoint` carries
   an explicit fail-closed refusal — `if auth.person_id is None: raise
   HTTPException(403, …)` (`routers/runs.py:444-451`, ADR-016 S2 RF-1,
   "INDEPENDENT of the authn toggle"). `run_procedure_endpoint`'s complete body
   (`:370-419`) carries **no such check**: with `api_auth_enabled=false` the run
   route would execute with a `None` principal (`triggered_by=None`,
   `principal=None`) while gate-resolve would still refuse. Confirmed by reading
   the full function, not a slice. Any SD-E option that admits the route to the
   allowlist must close this asymmetry **in the same change** — a weaker door must
   not ship beside a stronger one.

## Acceptance Criteria

Each AC names its artifact by path, its command, and a pass/fail read fixed before
the run. DB-backed tests require the dev Postgres (Docker Desktop, port 5442) and the
disposable test DB — one pytest per checkout; Windows worktrees skip DB tests.

- [ ] **AC-1 — subject lands through the real seed→`/runs` path.**
  Artifact: `tests/api/test_fleet_demo_reset_scenario.py` (new; drives the real
  lifespan seed functions + the real FastAPI client).
  Command: `uv run --extra dev pytest tests/api/test_fleet_demo_reset_scenario.py -q 2>&1`.
  Pass: after seeding, `GET /runs` (real client, real response model — never a
  hand-built dict) shows both fleet demo run rows with
  `subject == {"object_type": "Truck", "primary_key": <truck_id>}` where
  `<truck_id>` is derived *in the test* from the case row the run's own approve-step
  proposal names (independently recomputed, not copied from the seed's constant), and
  — positive control — that pk is present in the adapter's `Truck` objects (the
  condition under which Tab A has a node to attach the marker to). Fail: any `null`
  subject, any shape mismatch vs `_subject_of`'s checks
  (`services/api/routers/runs.py:160-169`), or pk absent from the adapter rows.
  Non-vacuity probe (Step 1): with the stamp call removed in a scratch copy, this
  exact assertion reddens (`subject` is `null` — today's measured state).

- [ ] **AC-2 — the filter default is untouched (REJECT-IF-grade).**
  Artifact: `tests/api/test_map_run_filter_contract.py` (new; reads the shipped
  `services/api/static/assets/view-map.js` — the artifact, never its own constant;
  precedent: `tests/api/test_css_class_contract.py`).
  Command: `uv run --extra dev pytest tests/api/test_map_run_filter_contract.py -q 2>&1`.
  Pass: the default mode literal is the in-flight mode AND the in-flight bucket is
  exactly `{waiting_human, running}` (PLAN-0084 SD-C, unchanged). Fail: any other
  default or any widened in-flight set.
  Non-vacuity probe (Step 2): flip the default to `all` in a scratch copy → this
  assertion reddens.

- [ ] **AC-3 — bucket membership is exactly SD-B's ratified sets.**
  Artifact + command: same as AC-2.
  Pass: `completed` bucket == `{completed}`; `all` == all five `PipelineRunStatus`
  values (G9); `failed` + `cancelled` appear in **no** mode except `all`. The test
  enumerates the five statuses from the Python enum (import, not a copied list) so a
  future sixth status reddens the guard instead of silently landing in no bucket.
  Fail: any drift between the JS buckets and the enum.

- [ ] **AC-4 — the reset restores the pristine pair through the real seed path
  (the mandatory scenario test).**
  Artifact: `tests/api/test_fleet_demo_reset_scenario.py`.
  Command: as AC-1.
  Pass, for each consumed shape driven through the **real endpoints** (persona-
  authenticated `POST /runs/{id}/gate/resolve` for `approve`, then `fulfill` →
  completed; and separately `POST /runs/{id}/cancel` → cancelled; plus the
  approve-only shape parked at `fulfill` — all three of G5): running the reset entry
  point (the same function the boot path calls) followed by the same lifespan seed
  functions yields, via `GET /runs`, **exactly two** fleet demo runs —
  `run-fleet-operate-demo` at `waiting_human` **suspended at the `approve` step with
  an undecided proposal set** (status alone is insufficient: a run parked at
  `fulfill` is also `waiting_human` — G5), and `run-fleet-demo-history` at
  `completed` — both carrying the AC-1 subject. Fail: wrong count, wrong statuses,
  wrong suspended step, or a missing subject.
  Non-vacuity probe (Step 5): skip the reset call in a scratch copy of the test →
  the pristine read reddens (the consumed state persists — today's measured defect).

- [ ] **AC-5 — the reset is scoped to the fixed demo ids and can touch nothing else.**
  Artifact + command: as AC-1.
  Pass: a decoy non-demo `pipeline_runs` row (distinct run id, same vertical) and a
  visitor-opened repair case seeded before the reset both survive the reset
  byte-identically (re-read and field-compared). Positive control for the read
  itself: the same comparison detects a deliberate mutation of the decoy in a control
  branch. Fail: any decoy/visitor-row change.
  Non-vacuity probe (Step 3): widen the reset's id set to include the decoy id in a
  scratch copy → this assertion reddens.

- [ ] **AC-6 — FK-completeness guard on the run deleter.**
  Artifact: `tests/services/db/test_demo_run_reset_fk_guard.py` (new; copies the
  PLAN-0105 AC-5 pattern).
  Command: `uv run --extra dev pytest tests/services/db/test_demo_run_reset_fk_guard.py -q 2>&1`.
  Pass: the deleter's declared child-table order == the set of tables whose live
  SQLAlchemy metadata declares an FK referencing `pipeline_runs` (today:
  `step_results`, `runs.py:133`) — the guard reads live metadata, never its own
  constant. Fail: any FK-bearing table missing from the declared order (a future
  child added without updating the deleter reddens this, not production).
  Non-vacuity probe (Step 3): remove `step_results` from the declared order in a
  scratch copy → guard reddens.

- [ ] **AC-7 — the audit chain survives the reset, and the checker is proven able
  to redden.**
  Artifact + command: as AC-1.
  Pass: across consume→reset→re-seed, the tenant's `audit_log` row count never
  decreases and `verify_chain` returns `[]`; positive control — in a sacrificial
  control branch, an in-place mutation of one audit row makes `verify_chain` report
  a break (the absence claim "no breaks" is backed by a demonstrated detection).
  Fail: any decrease, any break on the honest path, or a silent positive control.

- [ ] **AC-8 — the reset fails closed.**
  Artifact + command: as AC-1.
  Pass: with the flag unset/false (default), the boot path performs **zero**
  deletions on a consumed state (rows re-read identical — positive control: the same
  harness with the flag true does reset, so the "nothing happened" read is proven
  able to detect "something happened"); with the flag true but
  `settings.oct_vertical != "fleet_maintenance"`, likewise zero deletions. Fail: any
  deletion on either guard path.

- [ ] **AC-9 — cache-bust for the shipped JS.**
  Artifact: `tests/api/test_map_run_filter_contract.py` (same file as AC-2).
  Command: as AC-2.
  Pass: `index.html`'s `?v=` counter for `view-map.js` is bumped relative to the
  baseline value recorded in the test (per-file counter — differing numbers across
  files are normal). Fail: unbumped.

- [ ] **AC-10 — narrative promise matches the published surface (contingent on
  SD-E = (d); replaced by the ratified option's own ACs otherwise).**
  Artifacts: `deploy/published/oct-fleet-maintenance/card-copy.md` +
  `verticals/fleet_maintenance/operate_seed.py` (module docstring).
  Command: Grep tool (not WSL `rg` — it is absent there) over both files.
  Pass, all four reads: (1) the TH fragment `จะวิ่งเข้าสายอนุมัติเอง` → **0**
  matches in `card-copy.md`; (2) the EN fragment `routes itself into the approval
  chain` → **0** matches; (3) positive control proving the reader reads the real
  file — the stable headings `สิ่งที่จะได้เห็น` and `What you'll see` → exactly
  **1** match each (the copy guard `tests/deploy/` asserts headings, never words,
  so this edit reddens no existing guard and needs its own read); (4) the
  `operate_seed.py:7-9` clause "watch their *own* case enter the loop" is either
  removed or explicitly scoped to the dev console, with a pointer to this PLAN's
  SD-E. Fail: any overpromise fragment still present, or a positive control
  returning 0 (blind reader).
  Non-vacuity: reads (1)-(2) are RED on the unedited file today (1 match each —
  measured at drafting), so the pass state is witnessed to flip.

## Out of Scope

- ❌ **Any engine/orchestrator change** — no generic subject-stamping in
  `run_procedure_persisted` (SD-A alt (b)); PLAN-0084 twice kept the engine
  untouched and this PLAN keeps that line.
- ❌ **Server-side `/runs` status filtering** — the filter is a client-side view over
  the payload the endpoint already returns (population bounded at 2, G4).
- ❌ **A cap on the "all" mode** — unnecessary today *because* the allowlist excludes
  `POST /procedures/{id}/run` (G4). Reopen tripwire recorded there.
- ❌ **Pruning visitor-opened Tab I cases or prompt logs** — PLAN-0105's retention
  owns those; the reset never touches a visitor row (AC-5).
- ❌ **Deleting audit rows — never** (G8; REJECT-IF 5).
- ❌ **The event-bridge path** — `entity_ids` stamping and PLAN-0084 SD-D (d) stand
  untouched; `_resolve_subject`'s event branch is not modified.
- ❌ **Other verticals' seeds/demos** and the portal / other published profiles.
- ❌ **PLAN-0107 backlog-case seeds** — read-only closed cases, not consumed by
  visitor play; their idempotency guards are untouched.
- ❌ **Marker styling redesign beyond the SD-B modes** — the in-flight marker's
  visual language (PLAN-0084 SD-C) is unchanged.
- ❌ **Building the visitor-case→run path** (SD-E options (a)/(b)/(c)) — surfaced
  and priced in SD-E, recommended as a follow-on scope; it enters this PLAN only if
  Cray ratifies it in (precedent: PLAN-0084 SD-D, where Cray ratified wider than
  the defer recommendation — this SD is written so that pull-in is clean). If that
  happens, G4, AC-4/AC-5's population reads, and the "all"-mode cap line all change
  together, per SD-E's interaction pricing — never piecemeal.

## Steps

### Step 1: Backfill `subject` on the two demo runs (SD-A — drafted per recommendation (a), contingent on Cray)

In `verticals/fleet_maintenance/operate_seed.py`, after `_run_repair_round`'s
`run_procedure_persisted` returns (`:154-172` — the shared path both seeds use, on
purpose), derive the truck **from the run's own persisted artifact** — approve-step
`output_set` proposal → `case_id` → `RepairCase.truck_id` — and stamp
`trigger_context["subject"] = {"object_type": "Truck", "primary_key": <truck_id>}`,
persisting via a **new dict assignment** (SQLAlchemy does not track in-place JSONB
mutation; `PipelineRun.version` bumps via `version_id_col`, `runs.py:111-117`).
Fail-soft: artifact names zero or an ambiguous truck → skip the stamp, no marker
(PLAN-0084 SD-D's filtering behaviour, no error). Never stamp from the seed's own
constants — the stamp must be unable to assert an asset the run did not pick, which
is what keeps faith with the `:164-169` NOTE. Update that NOTE to record the
two-phase reasoning (unknowable at trigger time; known and stamped after `intake`).
- Non-vacuity probe: restore a pre-stamp copy from the scratchpad (never from git)
  and run AC-1 — the `subject` assertion must be SEEN red (`subject: null`, the
  measured live state) before the green counts.
- Output that changes: the `subject` field of both fleet rows in the real
  `GET /runs` payload — `null` → `{"object_type": "Truck", "primary_key": …}`.

### Step 2: Three-mode filter on Tab A (SD-B — drafted per recommendation, contingent on Cray)

In `services/api/static/assets/view-map.js`: introduce a mode state
(`inflight` default / `completed` / `all`), a small header control on Tab A, and
parameterize `computeRunFlags` by the mode's status bucket; keep `RUN_INFLIGHT`
(`:19`) as the default bucket **unchanged**. Marker treatment per bucket per SD-B.
Bump `index.html`'s `?v=` for `view-map.js` (per-file counter). Ship AC-2/AC-3/AC-9's
contract test in the same step.
- Non-vacuity probe: flip the default-mode literal in a scratch copy → AC-2 reddens;
  move `cancelled` into the completed bucket in a scratch copy → AC-3 reddens.
- Output that changes: the set of runs `computeRunFlags` admits per mode — under
  `completed`, the history run (status `completed`, subject present post-Step 1)
  gains a marker that the default mode never shows.

### Step 3: The demo-run deleter — first run-delete path in the repo (SD-D — drafted per recommendation, contingent on Cray)

New module `services/db/demo_run_reset.py` (executor may co-locate differently;
keep it demo-named, not generic): deletes, for **exactly** the fixed ids imported
from `operate_seed` (`DEMO_RUN_ID`, `DEMO_HISTORY_RUN_ID`, `DEMO_CASE_ID`,
`DEMO_HISTORY_CASE_ID` — constants, never parameters), in one transaction:
1. `step_results` for the two run ids (FK `runs.py:133`, no `ondelete` — children
   first; the loud FK failure stays as the backstop, G7);
2. `repair_case_run_link` rows for the two run/case ids (SD-D — a deliberate,
   surfaced divergence from PLAN-0105 SD-4's RETAIN; see SD-D);
3. the two `pipeline_runs` rows;
4. the two demo cases via the existing `delete_case`
   (`services/db/repair_case_retention.py` — files-first, `FK_CHILD_DELETION_ORDER`;
   reuse, do not re-implement the ordering PLAN-0105 already paid for);
5. **never** an `audit_log` row (G8).
Declare the run-child deletion order as module data and ship AC-6's live-metadata
completeness guard beside it.
- Non-vacuity probes: AC-5's widening probe (add the decoy id → scoping assertion
  reddens); AC-6's order-drop probe (remove `step_results` → guard reddens).
- Output that changes: post-reset row counts for the fixed ids (2→0 runs, N→0
  step_results/link rows, 2→0 demo cases) while the decoy/visitor rows' re-read
  stays byte-identical.

### Step 4: Boot wiring + the fail-closed flag (SD-C — drafted per recommendation (a), contingent on Cray)

Add a `Settings` field (`services/api/config.py`, `class Settings` at `:45`;
`oct_vertical` precedent at `:228`): `demo_reset_on_boot: bool = False` (env
`DEMO_RESET_ON_BOOT`; env names are uppercase). In `services/api/main.py`'s fleet
seed block, **before** the `:307` skip: if flag AND
`settings.oct_vertical == "fleet_maintenance"`, run the Step 3 reset (one
transaction; on any error, roll back — prior state stands, existing seeds then skip:
degraded, never half-deleted) and log loudly. The existing seeds
(`seed_settled_history_case`, `seed_case_list_history`,
`seed_repair_gate_waiting_human_run`) then find a virgin surface and rebuild the
pristine pair through the exact path a fresh boot uses — no new end state is
invented (G6). Set `DEMO_RESET_ON_BOOT=1` in
`deploy/published/oct-fleet-maintenance/published.env` only; no other env file, no
compose default.
- Execution-time confirms (bounded): `seed_demo_repair_case`'s idempotency guard
  key (expected: case id, mirroring `:410` — confirm before relying on rebuild);
  whether any guard test asserts `published.env`'s contents.
- Non-vacuity probe: AC-8 both ways — flag false → consumed state persists
  unchanged; flag true in the same harness → it does not (the positive control).
- Output that changes: the boot log gains the reset line, and only under
  flag+vertical do the Step 3 counts change.

### Step 5: The scenario test — real producer into real consumer (binding, CLAUDE.md §8)

`tests/api/test_fleet_demo_reset_scenario.py`: boot-seed via the real lifespan
functions → consume the beat via the **real endpoints** in each of G5's three shapes
(persona-authenticated resolve of `approve` then `fulfill`; approve-only parked at
`fulfill`; `/cancel`) → reset via the boot entry point → re-seed → assert AC-1,
AC-4, AC-5, AC-7, AC-8 against the real `GET /runs` / `GET /runs/{id}` payloads.
No mocked seam on either side: the seed that produces, the endpoints that consume,
the reset that restores are all the shipped code paths.
- Record (not hide) the measured reset side-effects in the test's docstring: each
  rebuild consumes one `allocate_repair_order_no` allocation (the report's RO number
  advances per deploy — gap-free by construction, `operate_seed.py:571-577`) and
  appends one seed-round of audit rows (append-only; G8).
- Non-vacuity probe: AC-4's skip-the-reset probe — the consumed state must be SEEN
  to persist before the restore green counts.

### Step 6: Narrative correction (contingent on SD-E = (d); superseded by the ratified option otherwise)

Correct exactly the sentences G10(4) names: `card-copy.md:26-27` (TH) and `:58-59`
(EN) — replace the "routes itself into the approval chain" claim with copy scoped to
what the published surface actually delivers (the seeded case's governed round + the
refused-then-granted beat; replacement wording is Cray's, per the card-copy file's
own "copy quality has no oracle" note) — and re-scope the `operate_seed.py:7-9`
docstring clause so PLAN-0103 AC-8 clause 2 is no longer cited as satisfied on the
published profile (it is not — G10(4)). Ship AC-10's reads in the same change.
- Non-vacuity probe: AC-10's absence greps are RED on the unedited files (measured
  at drafting) and the heading positive controls stay at exactly 1 — the flip is
  witnessed, and a blind reader cannot pass.
- Output that changes: the grep match counts AC-10 fixes (1→0 for each overpromise
  fragment; 1→1 for each positive control).

### Step 7: Deploy + live verification (host-state — Cray go required)

Redeploy the published fleet system with the new image + env. Live checks (evidence,
not the gate — the offline oracle is the gate, CLAUDE.md §8): `GET /runs` shows two
runs with subjects; Tab A default view shows one in-flight marker on `truck-02`'s
node; switching modes shows the completed run; play the beat, redeploy, confirm the
queue is pristine again. Any MS-S1 / host action gets explicit Cray go first.

## Surfaced decisions

Recommendations are drafted into the Steps above but are **contingent on Cray's
ratification**; record ratified picks here per PLAN-0084's convention.

### SD-A — where the `subject` backfill happens

**Question:** who writes the run's `subject` once `intake` has picked the truck?
**Recommendation — (a) seed-local post-round stamp** (Step 1): in `_run_repair_round`
after persistence, derived from the run's own approve-step artifact, fail-soft on
zero/ambiguous. Blast radius: the fleet seed only — the read side
(`_subject_of`, `routers/runs.py:154-169`) and the map key
(`view-map.js:95`, `object_type + '|' + primary_key`) consume it with **zero new
code**, and the shape matches `_subject_of`'s exact checks (non-empty strings for
both members).
**⚠️ Prior-ruling proximity, named rather than assumed away:** PLAN-0084 SD-D
**rejected** its option (c) — "vertical-side post-fire mutation of the persisted
`trigger_context`… overwrites an engine-owned provenance stamp from outside the
engine, an integrity smell." That rejection governed the **engine-stamped
event-bridge** context. Here the `trigger_context` is *authored by this same seed*
(`source: "operate-demo-seed"`, `operate_seed.py:161-170`) and the added key records
the run's **own persisted resolution** — the author annotating its own record from
the run's output, not an outsider rewriting engine provenance. Whether that
distinction holds is exactly the adjudication Cray owns.
**Alternatives:** (b) engine-generic orchestrator stamp from a declared step output —
touches every vertical, needs a `procedures.yaml` declaration surface, and crosses
the engine line PLAN-0084 twice declined to cross; a scope of its own. (c) read-side
projection — extend `_resolve_subject` to fall back to step artifacts: changes
`/runs` semantics for **every** vertical and forces `list_runs` into per-run child
loads it deliberately avoids today.
**Why Cray:** (a) sits next to a ratified rejection whose boundary must be ruled, not
inferred; and which surface carries the demo's map story is a wedge-artifact call
(ADR-0032 D1).

### SD-B — what "completed" means in the filter

**Question:** `PipelineRunStatus` (G9) has five values; `RUN_INFLIGHT` names two.
Which land where, and does "all" literally mean all?
**Recommendation:** in-flight = `{waiting_human, running}` — **the default,
unchanged** (PLAN-0084 SD-C; REJECT-IF 1). completed = `{completed}` **exactly**.
`failed` + `cancelled` land in **neither named mode** and appear only under "all",
which literally means all five. Marker treatment: in-flight keeps the SD-C marker;
completed gets a visually distinct "settled" marker; `failed`/`cancelled` under
"all" get a third, muted treatment — never the settled look (a cancelled run must
not read as finished work).
**Ruling hygiene:** SD-C-0084 said terminal states *never* light the marker. That
governed the single unconditional marker that existed then. Cray's 2026-08-18 typed
direction — the three-mode filter itself — extends it with opt-in views; this SD
records the extension explicitly so the "never" is narrowed in writing, for
non-default modes only, rather than silently.
**Alternatives:** completed = all terminal states (flattens "gave up" into "done" —
rejected in recommendation); hiding `failed`/`cancelled` even from "all" (an "all"
that lies about its name).
**Why Cray:** bucket membership and the three marker treatments are demo-stage
vocabulary Cray narrates live — SD-C-0084's own why-Cray, unchanged.

### SD-C — where the reset runs, and its blast radius

**Question:** boot-time, deploy-script step, or operator command? This is the
highest-risk piece: a misfiring reset would wipe a run mid-visitor-session.
**Recommendation — (a) boot-time in the fleet seed block, triple-guarded,
fail-closed** (Step 4): `DEMO_RESET_ON_BOOT` (default **false**; set only in
`published.env`) AND `oct_vertical == "fleet_maintenance"` AND fixed-id constants —
any guard unmet → zero deletions; one transaction → an error mid-reset rolls back to
prior state (never half-deleted). Dev, CI, local, and every non-fleet deployment can
never fire it (AC-8).
**Named failure mode, accepted rather than hidden:** with (a), a container
*crash-restart* — not only a deploy — also resets, so a visitor mid-beat at that
moment loses the half-played run and finds a pristine demo. Against the measured
alternative (the beat permanently consumed, G5), re-arming is the better failure for
a demo whose promise is "the approve beat is always available." If Cray weighs the
mid-session wipe heavier, option (b) is the fallback.
**Alternatives:** (b) deploy-script one-shot (resets only on explicit deploy;
restarts never reset — but adds an out-of-app execution surface with DB credentials,
and a forgettable manual step is exactly the shape of the current defect); (c)
operator CLI (same objection, more manual).
**Why Cray:** the restart-wipe vs permanent-consumption trade-off is a
demo-operations judgment about the live surface Cray runs in front of people.

### SD-D — delete-and-reseed under fixed ids, and what "pristine" covers

**Question:** delete the fixed ids and re-seed, or re-seed under new ids? And how
deep is "pristine"?
**Recommendation — delete deep under the SAME fixed ids** (Step 3): runs + their
`step_results` + the demo-scoped `repair_case_run_link` rows + the two demo cases
(via `delete_case`), then let the untouched seeds rebuild through the virgin-boot
path. Reasons, in order of force: (1) G7's rebuild constraint — the history seed is
idempotent on the **case** id and its round only proposes OPEN cases, so anything
shallower than case deletion leaves a state the seed cannot rebuild through the real
path; (2) fixed ids keep the population at exactly 2 forever, matching Cray's ruling
and preserving G4's no-cap answer — new ids per boot would accumulate and reopen it;
(3) id reuse is also **why the link rows must go**: a prior deployment's visitor
decisions would otherwise attach to the rebuilt case as decisions nobody made in
this deployment, polluting the month-end report's audit answers.
**⚠️ Surfaced divergence from a ratified ruling:** PLAN-0105 SD-4 ruled RETAIN for
`repair_case_run_link` rows on case deletion. That ruling governed the **retention
sweep**, where a deleted case id never returns and the orphan lands in a measured
silent-degrade mode. The reset **reuses** ids, which is precisely the condition
under which RETAIN stops being safe. This PLAN retains SD-4 for retention and
diverges **only** for the demo-scoped reset — a divergence from a ratified ruling is
Cray's to grant, which is half of this SD's reason to exist.
**Never deleted:** `audit_log` rows (G8; REJECT-IF 5) — the chain stays intact and
every visitor decision remains on the record across resets.
**"Pristine" boundary:** the two demo runs, their step results, their link rows, the
two demo cases and children — nothing else. Visitor Tab I cases, PLAN-0107 backlog
cases, prompt logs: untouched (AC-5).
**Recorded side-effects (measured, not hidden):** each reset advances the repair-
order counter by one allocation and appends one seed-round of audit rows — honest
allocation and honest audit, worth one line in the demo narration, never suppressed.
**Alternatives:** new ids per boot (accumulation; violates "exactly two"; reopens
the cap); run-only deletion (cannot rebuild — G7; rejected as measured-infeasible,
not as taste).
**Why Cray:** it operationalizes Cray's own typed ruling *and* diverges from
PLAN-0105 SD-4 in a named sub-case.

### SD-E — how a visitor's case reaches a governed run on the published profile (added per Cray's 2026-08-18 (ข) ruling)

**Question:** G10 measures that a visitor's case sits `OPEN` and ungoverned forever
on the published surface — PLAN-0103 AC-8 clause 2 and the card-copy's "routes
itself" sentence are unreachable there. How does the demo keep (or honestly
re-scope) that promise?

**Candidates, each with blast radius and security posture:**

- **(a) Admit `POST /procedures/{id}/run` to the tunnel allowlist**, relying on
  app-level auth (G10(5): the route server-owns `triggered_by` and authn is on for
  this system). **Mandatory riders, not optional:** (i) close the G10(6) asymmetry
  first — an explicit `auth.person_id is None → 403` on `run_procedure_endpoint`,
  mirroring `:444-451`, independent of the toggle — the route must fail closed
  before it is exposed; (ii) correct the `config.yml:111-112` and `:202` comments in
  the same PR — the allowlist must never contradict its own written basis; (iii) the
  new ingress row reddens `tests/deploy/test_published_profiles.py`'s set-equality
  guard, whose expected table changes in the same PR, as a decision with its own
  written basis (the file's P12 convention). Blast radius: **reverses a deliberate
  exclusion** (an ADR-0035-shaped surface decision); keyed personas can then fire
  unlimited runs → the population bound dissolves (G4 contingency) — the "all" cap
  question reopens AND visitor-fired runs accumulate across deploys with no
  lifecycle owner, resurrecting, for visitor runs only, exactly the prune question
  G6 dissolved for seeded ones. Cheapest to build; most expensive in reopened
  ground. **Open question this option must ASK, not assume (REJECT-IF 11):**
  whether the tunnel exclusion is belt-and-braces over app auth or load-bearing for
  an unstated reason — Cray (with the ADR-0035 context) answers that; this PLAN
  does not.
- **(b) Server-side firing on case creation** — `open_case`
  (`cases.py:183-219`) fires the run for the case it just wrote. No new tunnel
  surface (the strongest posture: the exclusion and its comment stand untouched);
  the run is a new run, which is the only shape that works anyway (G10(3) — the
  parked seeded gate cannot adopt a later case). Costs, priced honestly:
  `POST /api/cases` changes meaning and cost (case intake becomes coupled to
  procedure execution — latency, failure coupling, and the RoPA/AC-11 description
  of what Tab I writes may need a line); and **the principal question is real** —
  a persona-keyed case can fire as that authenticated requester, but `open_case`
  also accepts unauthenticated intake (`:206` falls back to `_UNATTRIBUTED`), so
  an anonymous case either fires with no accountable requester (unacceptable —
  the G10(6) hole by another door) or fires nothing (fail-closed; the promise
  holds for keyed personas only — say so in the copy). The S1 scheduler precedent
  (service-principal actor, ADR-016 S2) is the alternative actor shape, with its
  own owning-person requirement. Population bound dissolves here too — one run
  per visitor case — but rate-coupled to case creation rather than to a bare
  endpoint.
- **(c) A periodic or boot-time sweep** — fire runs for OPEN ungoverned cases.
  No new surface, but the latency between the visitor's action and the governance
  they were promised to *watch* likely defeats the beat entirely (a boot-time
  sweep governs the case only after a redeploy the visitor never sees; a periodic
  one is minutes of "nothing happened" in a 90-second demo). Same population
  dissolution as (b), plus a background actor with the same principal question.
- **(d) Accept and re-scope the promise** — build nothing; correct exactly the
  sentences G10(4) names (`card-copy.md:26-27` TH, `:58-59` EN, and the
  `operate_seed.py:7-9` AC-8-clause-2 citation). The demo then says: *your case
  lands in the same case list and evidence surfaces the governed runs use; the
  governed approval you play is the seeded round* — the refused-then-granted beat,
  the audit-chain verify, and Tab I intake all remain exactly as shipped. The
  honest null option: G4's bound, the no-cap answer, and the reset's two-run world
  all stay true verbatim.

**Recommendation:** **(d) in this PLAN** (Step 6 + AC-10), and record **(b) as the
strongest build candidate** for a follow-on PLAN if Cray wants the promise
delivered rather than re-scoped — (b) keeps the tunnel exclusion and its written
basis intact, fires the only run shape that works (G10(3)), and confines the new
authority question to a surface this repo already governs (requester principal on
a fired run). (a) is cheaper only if the reopened surface decision, the asymmetry
fix, and the visitor-run lifecycle are all priced in — at which point it is not
cheaper. This PLAN's three pieces ship value now under (d) without waiting on that
adjudication.

**Interaction with SD-C/SD-D and G4 (stated per candidate, not in aggregate):**
under **(d)** — no change; G4 holds verbatim; the reset's fixed-id scoping is
complete because demo runs are the only runs. Under **(a)/(b)/(c)** — the two-run
bound dissolves: the "all" filter mode regains an unbounded axis (a cap or
pagination decision reopens — G4's tripwire fires); the reset's fixed-id scoping
(AC-5) still correctly *protects* visitor runs from deletion, but "restore the
pristine pair" no longer describes the whole population, and visitor-run lifecycle
(retention? cancel-only? sweep?) becomes a decision someone must own — in the
follow-on PLAN, not silently here. AC-4's "exactly two fleet demo runs" read would
be re-scoped to "exactly two runs bearing the fixed demo ids" with the decoy
assertions carrying the rest.

**Why Cray:** this trades demo completeness against **who may start a governed
run** on a public surface — a published-exposure decision of exactly the kind
ADR-0035/PLAN-0103 reserved for explicit rulings, and (a) would reverse one of
those rulings by name.

## Verification

1. **Offline (the gate):** `uv run --extra dev pytest tests/api/test_fleet_demo_reset_scenario.py tests/api/test_map_run_filter_contract.py tests/services/db/test_demo_run_reset_fk_guard.py -q 2>&1` — all green **after** each AC's named non-vacuity probe has been SEEN red in a scratch copy (probes restore from the scratchpad, never from git). Full suite + `mypy services/` + bare `ruff check .` per the offline-gate-matches-CI rule. DB-backed tests need the dev Postgres (port 5442); run from the main checkout, not a Windows worktree.
2. **Pass/fail reads were fixed above, per AC — the run confirms them, never rewrites them.** A green whose assertion was not witnessed red on its own mutation is not evidence (CLAUDE.md §8).
3. **Live (evidence, not the gate; host-state → explicit Cray go):** Step 7's checks on the published system — two subjects in `/runs`, one default marker, mode switching, and the play-then-redeploy pristine cycle.
4. Merge order: this PLAN's ADR-less mechanics ride existing rulings (PLAN-0084 SD-C/SD-D, Cray's 2026-08-18 typed directions); the five SDs above must carry ratified stamps before the implementing PR closes them out. SD-E in particular gates Step 6 + AC-10 (its (d) recommendation) and, if ratified to a build option instead, rewrites G4's contingency paragraph and the AC-4/AC-5 population reads together — never piecemeal.
