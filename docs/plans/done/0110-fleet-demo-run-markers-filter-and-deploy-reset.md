# PLAN-0110: Fleet Demo Lifecycle — Tab A Run Markers, Three-Mode Filter, Deploy-Time Reset

**Status:** Complete (2026-08-18, session 238) — Steps 1–6 shipped in
[#1213](https://github.com/CrayJThiemsert/vero-lite/pull/1213) (`main` @ `20669ae`);
Step 7 deployed and verified on MS-S1 under a typed §8 go, recorded in
[`docs/logs/2026-08-18-plan0110-fleet-demo-reset-deploy.md`](../../logs/2026-08-18-plan0110-fleet-demo-reset-deploy.md).
⚠️ Two divergences from this PLAN's wording are recorded in #1213 and in the shipped
code: Step 3's "one transaction" (incompatible with reusing `delete_case`, which owns
its own commit) and Step 4's runbook location (writing it there reddened the ADR-0036 D2
label guard, so the procedure ships in the profile directory instead).
**Owner:** Claude Code (execution). **All five SDs RULED** (Cray, typed, 2026-08-18
s237) — SD-A (a), SD-B as recommended, **SD-C = deploy-script step, AGAINST the
drafter recommendation** (see SD-C for why and what it buys/costs), SD-D as
recommended, SD-E (d) with (b) the named follow-on build.
**Created:** 2026-08-18
**Related ADRs:** ADR-0032 (demo→pilot wedge — the published fleet demo IS the wedge artifact), ADR-0035 (published-surface decisions), ADR-0025 (the `request → approve → fulfill` spine shape), ADR-016 (run records + audit chain)
**Related PLANs:** PLAN-0084 (map↔monitor run linkage — SD-C/SD-D rulings this PLAN inherits), PLAN-0103 (published fleet profile), PLAN-0105 (case retention — the deletion-ordering precedent and the SD-4 link-row ruling this PLAN diverges from, explicitly), PLAN-0107 (backlog-case seeds, untouched)

> Drafted by the in-harness `plan-drafter` subagent (ADR-013 D1 phased authority) from
> Code's session-237 dispatch + fact-pack; amended same-session per Cray's (ข) ruling
> (fold in SD-E — the visitor-case→run gap, G10), then again when Cray ruled all five
> SDs (typed, 2026-08-18 s237) — rulings folded in place, with SD-C ruled against the
> drafter recommendation and its consequences priced in SD-C/G11. All new anchors
> re-verified on disk at each amendment. Independent review: Cray at PR merge.
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
The PLAN also carries the measured gap that **a visitor's own case can never enter a
governed run on the published profile** (G10): Cray ruled SD-E = (d) — this PLAN
re-scopes the narrative promise (Step 6, AC-10, now active work), and **(b)
server-side firing is the named follow-on build**. That ruling keeps G4's two-run
bound as current fact, so the filter-cap and reset-scoping ground the other pieces
stand on holds. The reset runs as a **deploy-script step, not at boot** (SD-C, ruled
against the drafter recommendation — trade priced in SD-C and G11).

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
**Contingency RESOLVED (SD-E RULED (d), Cray, typed, 2026-08-18 s237): the two-run
bound HOLDS as current fact.** The reopen tripwire is retained, deliberately, with
two triggers: (i) if `POST /procedures/{id}/run` is ever admitted to the allowlist,
or (ii) when SD-E's named follow-on build (b) — server-side firing on case creation
— lands. Either dissolves the bound: the "all" mode regains an unbounded axis and
"exactly two runs" becomes "exactly two *demo* runs among N visitor runs" (the
per-candidate pricing stays recorded in SD-E for that day). Rewrite this paragraph
then; never delete the tripwire.

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

**G11 — "add it to the deploy script" is not a neutral instruction (measured; the
SD-C ruling's binding constraint).** `deploy/published/deploy.py` serves
**`oct-energy` only**, by typed decision (Cray, s219 — recorded in the module's own
header at `deploy.py:65-83`): `_HOST_COMPOSE` and `_LOCAL_COMPOSE` are hardwired to
`deploy/published/oct-energy/docker-compose.yml` (`:89`, `:102`), the
parameterize-vs-copy decision is **explicitly deferred** ("designing a `--system`
interface against a second deployment that has never run" is named as the
speculative-generality failure), and `tests/deploy/test_deploy.py:44-47` **pins**
the script to energy's compose file "so a second system cannot quietly start riding
these energy-shaped literals." Fleet was brought up and redeployed by a **different,
manual path** (`docs/logs/2026-08-16-plan0103-step10-fleet-bring-up.md`): its
compose declares `build:` with **no** `image:`, so the image must be `docker save`
→ `ssh … docker load`-shipped (the deploy host cannot build — measured, `:65-77` of
that log), and the same log's addendum records fleet's first redeploy as a by-hand
sequence — including the boot line `run 'run-fleet-operate-demo' already present —
skip`, which is this PLAN's G5 defect surviving a redeploy on the live system. Two
further measured constraints on any fleet deploy step: remote commands land in
**PowerShell** (no quotes/`$`/braces; **forward slashes** — a backslashed path is
silently stripped to a relative one, the log's Correction 1), and every fleet
redeploy is a §8 host-state action under an explicit typed go. Consequence: the
reset step must **not** attach to `deploy.py` in this PLAN — that would force the
s219-deferred parameterization decision as a side effect and widen a deliberate
test pin. Step 4 states what it attaches to instead.

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
  point (the same function the Step 4 operator step invokes at deploy time) followed
  by the same lifespan seed functions yields, via `GET /runs`, **exactly two** fleet
  demo runs —
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

- [ ] **AC-8 — the reset fails closed (SD-C RULED: deploy-step shape).**
  Artifact + command: as AC-1.
  Pass, three reads: (1) **plan mode is the default** — invoking the entry point
  without its explicit execute flag performs **zero** deletions on a consumed state
  (rows re-read identical; positive control: the same harness *with* the execute
  flag does reset, so the "nothing happened" read is proven able to detect
  "something happened"); (2) with the execute flag but
  `settings.oct_vertical != "fleet_maintenance"`, the entry point **refuses** with
  zero deletions; (3) **nothing at boot invokes it** — a grep read asserting
  `services/api/main.py` contains no reference to the reset module (absence claim;
  positive control: the same grep over `tests/` finds the scenario test's own
  import, proving the reader can find a present reference). Fail: any deletion on
  (1)/(2), or a boot-path reference on (3).

- [ ] **AC-11 — the degraded state is observable without deploying (SD-C
  consequence: a manual reset needs a visible precondition).**
  Artifact: `services/db/demo_run_reset.py` (plan-mode output) +
  `tests/api/test_fleet_demo_reset_scenario.py`.
  Command: as AC-1.
  Pass: the entry point's **plan mode prints a verdict token** — the literal
  `DEMO-STATE: PRISTINE` when the two fixed runs match the pristine read (one
  `waiting_human` suspended at `approve`, one `completed`), and the literal
  `DEMO-STATE: CONSUMED` otherwise — asserted in both states through the real seed
  + consume paths (an echoed exit code is corruptible; the token is the read).
  Fail: missing/wrong token in either state.
  Non-vacuity: the CONSUMED assertion runs after a real gate-resolve — the same
  mutation AC-4 already drives — so the token is witnessed to flip.

- [ ] **AC-9 — cache-bust for the shipped JS.**
  Artifact: `tests/api/test_map_run_filter_contract.py` (same file as AC-2).
  Command: as AC-2.
  Pass: `index.html`'s `?v=` counter for `view-map.js` is bumped relative to the
  baseline value recorded in the test (per-file counter — differing numbers across
  files are normal). Fail: unbumped.

- [ ] **AC-10 — narrative promise matches the published surface (SD-E RULED (d) —
  ACTIVE work, not contingent, not optional).**
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
- ❌ **Building the visitor-case→run path — SD-E RULED (d):** (a) and (c) are not
  planned; **(b) server-side firing is the NAMED follow-on build** (Cray, typed,
  2026-08-18 s237), carrying with it the RoPA/AC-11 description line, the
  anonymous-intake principal question (`cases.py:206` `_UNATTRIBUTED`), and — per
  G4's retained tripwire — the joint rewrite of G4, AC-4/AC-5's population reads,
  and the "all"-mode cap line, never piecemeal.
- ❌ **Parameterizing `deploy/published/deploy.py` across systems** — the s219-typed
  deferral stands (G11); this PLAN's reset step deliberately does not attach to that
  script, so the deferred `--system` decision is not forced here and
  `tests/deploy/test_deploy.py`'s energy pin does not widen.

## Steps

### Step 1: Backfill `subject` on the two demo runs (SD-A RULED (a) — Cray, typed, 2026-08-18 s237)

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

### Step 2: Three-mode filter on Tab A (SD-B RULED as recommended — Cray, typed, 2026-08-18 s237)

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

### Step 3: The demo-run deleter — first run-delete path in the repo (SD-D RULED as recommended — Cray, typed, 2026-08-18 s237)

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

### Step 4: The deploy-step entry point + runbook wiring (SD-C RULED: deploy-script step, NOT boot-time — Cray, typed, 2026-08-18 s237)

**No boot wiring, no `Settings` flag, no `published.env` change** — the boot-time
design was the drafter's recommendation and Cray ruled against it (SD-C states the
trade). What ships instead, resolving G11's constraint explicitly:

**Attachment (the G11 question, answered):** the reset does **not** attach to
`deploy.py` (energy-hardwired by typed s219 decision, test-pinned — G11). It is an
**operator entry point on the reset module itself**, baked into the app image:
`services/db/demo_run_reset.py` gains a `__main__` guard (argparse), invoked inside
the running fleet app container —
`ssh <host> docker compose -f C:/projects/vero-lite/deploy/published/oct-fleet-maintenance/docker-compose.yml -p oct-fleet-maintenance exec -T app python -m services.db.demo_run_reset [--execute]`
— plain words only (PowerShell-safe: no quotes, no `$`, no braces; **forward
slashes** per the bring-up log's Correction 1), the container's own `DATABASE_URL`
and `OCT_VERTICAL` (so it aims at the right database by construction and the
vertical guard reads the deployed system's own setting), and no new credential
surface anywhere. The documented sequence lives in
`docs/runbooks/published-demo-redeploy.md` (SD-C consequence 2).

**Safety pattern, copied from `deploy.py`'s own (`deploy.py:36-41`):** the default
invocation is a **plan** — it deletes nothing and prints the AC-11 verdict token
(`DEMO-STATE: PRISTINE` / `DEMO-STATE: CONSUMED`), which doubles as the SD-C
consequence-1 observable check *and* as the not-silently-a-no-op guard (no token ⇒
the module did not run — the `python -m` silent-no-op hazard is detectable by
construction). Deletion requires an explicit `--execute`. Guards retained in full
(they matter MORE in an operator-invoked step, where a hand-typed invocation can aim
at the wrong target): fixed-id constants imported from `operate_seed`, the
`oct_vertical == "fleet_maintenance"` refusal, one transaction (an error rolls back
— prior state stands, never half-deleted).

**🔴 Ordering within the redeploy is load-bearing.** The seeds rebuild only in the
app's boot lifespan. The runbook step is therefore: **reset with `--execute` first
(against the still-running old container), then `up -d`** — the recreate boots the
new image, the seeds find a virgin surface and rebuild the pristine pair through the
exact path a virgin boot uses (G6). If a redeploy does not recreate the app (image
id unchanged), the runbook names the explicit follow-up: `… compose restart app`.
A reset run *after* the app has booted, with no restart, leaves the demo EMPTY until
the next boot — the runbook states this as the failure the ordering exists to
prevent.

- Execution-time confirms (bounded): `seed_demo_repair_case`'s idempotency guard
  key (expected: case id, mirroring `:410` — confirm before relying on rebuild);
  the `compose exec -T` plain-word argv surviving the ssh→PowerShell chain (a Step 7
  live confirm, under the §8 go).
- Non-vacuity probe: AC-8 all three reads — plan-default deletes nothing (positive
  control: `--execute` does); wrong vertical refuses; no boot-path reference exists
  (positive control: the scenario test's own import is found).
- Output that changes: only under `--execute` + fleet vertical do the Step 3 counts
  change; plan mode changes nothing and prints the token.

### Step 5: The scenario test — real producer into real consumer (binding, CLAUDE.md §8)

`tests/api/test_fleet_demo_reset_scenario.py`: boot-seed via the real lifespan
functions → consume the beat via the **real endpoints** in each of G5's three shapes
(persona-authenticated resolve of `approve` then `fulfill`; approve-only parked at
`fulfill`; `/cancel`) → reset via the operator entry point (the same function
Step 4's deploy step invokes, both plan and `--execute` modes) → re-seed → assert
AC-1, AC-4, AC-5, AC-7, AC-8 and AC-11's verdict tokens against the real
`GET /runs` / `GET /runs/{id}` payloads and the entry point's printed output.
No mocked seam on either side: the seed that produces, the endpoints that consume,
the reset that restores are all the shipped code paths.
- Record (not hide) the measured reset side-effects in the test's docstring: each
  rebuild consumes one `allocate_repair_order_no` allocation (the report's RO number
  advances per deploy — gap-free by construction, `operate_seed.py:571-577`) and
  appends one seed-round of audit rows (append-only; G8).
- Non-vacuity probe: AC-4's skip-the-reset probe — the consumed state must be SEEN
  to persist before the restore green counts.

### Step 6: Narrative correction (SD-E RULED (d) — ACTIVE work; Cray, typed, 2026-08-18 s237)

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

Redeploy the published fleet system with the new image, following the runbook's
updated fleet sequence (Step 4): plan-mode state read → reset `--execute` → ship +
`up -d` (the manual fleet path per G11 — `deploy.py` is not used for fleet). Live
checks (evidence, not the gate — the offline oracle is the gate, CLAUDE.md §8):
plan mode prints `DEMO-STATE:` and the token flips across the cycle; `GET /runs`
shows two runs with subjects; Tab A default view shows one in-flight marker on
`truck-02`'s node; switching modes shows the completed run; play the beat, run the
reset + redeploy, confirm the queue is pristine again; `GET /audit/verify` still
reports intact with a row count that never decreased. Any MS-S1 / host action gets
explicit Cray go first, per invocation.

## Surfaced decisions

**All five SDs RULED (Cray, typed, 2026-08-18 s237)** — stamps recorded per SD
below, per PLAN-0084's convention. Four rulings follow the drafter recommendation;
**SD-C does not** — it is stamped with what the ruling buys and costs, both
directions, because a ruling against the drafter must be priced, not just recorded.
The original recommendations are retained under each SD for the reasoning lineage
(CLAUDE.md §6: superseded-by-ruling, not erased).

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
**RULED (Cray, typed, 2026-08-18 s237): (a) as recommended** — seed-local
post-round stamp. The PLAN-0084 SD-D(c) boundary question is thereby settled for
the seed-authored case: the author annotating its own record from the run's
persisted output is inside the line. PLAN change: none — Step 1 already implements
this shape.

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
**RULED (Cray, typed, 2026-08-18 s237): as recommended** — completed means
`{completed}` exactly; `failed`/`cancelled` appear only under "all"; the default
stays in-flight-only. PLAN change: none — Step 2 / AC-2 / AC-3 already encode this.

### SD-C — where the reset runs, and its blast radius

**Question:** boot-time, deploy-script step, or operator command? This is the
highest-risk piece: a misfiring reset would wipe a run mid-visitor-session.
**Drafter recommendation (SUPERSEDED by the ruling below — retained for lineage) —
(a) boot-time in the fleet seed block, triple-guarded, fail-closed:**
`DEMO_RESET_ON_BOOT` (default **false**; set only in
`published.env`) AND `oct_vertical == "fleet_maintenance"` AND fixed-id constants —
any guard unmet → zero deletions; one transaction → an error mid-reset rolls back to
prior state (never half-deleted). Dev, CI, local, and every non-fleet deployment can
never fire it (AC-8).
**Named failure mode of (a), accepted rather than hidden in the draft:** a
container *crash-restart* — not only a deploy — also resets, so a visitor mid-beat
at that moment loses the half-played run and finds a pristine demo.
**Alternatives as drafted:** (b) deploy-script one-shot (resets only on explicit
deploy; restarts never reset — but adds an out-of-app execution surface with DB
credentials, and a forgettable manual step is exactly the shape of the current
defect); (c) operator CLI (same objection, more manual).
**Why Cray:** the restart-wipe vs permanent-consumption trade-off is a
demo-operations judgment about the live surface Cray runs in front of people.

**RULED (Cray, typed, 2026-08-18 s237): the DEPLOY-SCRIPT step — AGAINST the
drafter recommendation (a).** Recorded with the trade priced both directions:

- **What the ruling buys (why Cray chose it):** the accepted failure the draft
  named **cannot happen** — a crash-restart can never wipe a visitor's mid-session
  run, because the reset fires only when an operator deploys. Deletion on a public
  system happens only under a human's explicit, §8-gated action.
- **What it costs, stated as a consequence, not buried:** the demo stays in
  whatever state a visitor left it **until the next deploy**. A beat consumed on
  day 1 with the next deploy three weeks out means three degraded weeks — and
  nothing self-heals or surfaces it. Boot-time would have re-armed on every
  restart; a deploy step does not. Two mitigations ship in this PLAN, neither a
  monitoring system: **(1) the degraded state is observable without deploying** —
  the entry point's plan mode prints `DEMO-STATE: PRISTINE|CONSUMED` (AC-11), a
  zero-risk read an operator (or a runbook check) can run any day; **(2) the reset
  is discoverable at deploy time** — `docs/runbooks/published-demo-redeploy.md`
  gains the fleet reset step (Step 4), so the operation does not live only in this
  PLAN. An operation nobody can tell is needed will not be run; these two lines
  are the cheapest honest answer to that.
- **The drafter's original objection to this option — an out-of-app credential
  surface — is dissolved by the Step 4 attachment shape:** the entry point runs
  *inside* the app container via `compose exec`, on the container's own
  `DATABASE_URL`/`OCT_VERTICAL`, so no credential leaves the deployed system.
  The "forgettable manual step" objection is mitigated (not erased) by the runbook
  line + the observable check; the residual — an operator who never deploys never
  resets — is exactly the priced cost above.
- **Guards retained in full** (fixed-id constants, vertical refusal, one
  transaction, plan-by-default + explicit `--execute`): they matter MORE in an
  operator-invoked step, where a hand-typed invocation can aim at the wrong
  target (AC-5, AC-8).
- **Attachment (G11 — the binding constraint the follow-up dispatch flagged as
  REJECT-IF: "add it to the deploy script" must not be written unresolved):**
  `deploy.py` is `oct-energy`-only by typed s219 decision, test-pinned
  (`tests/deploy/test_deploy.py:44-47`), with the `--system` parameterization
  explicitly deferred; fleet deploys by a documented manual sequence (G11).
  **Resolved: the reset attaches to the reset module itself** (an in-image
  `__main__` entry point invoked via `compose exec`), documented as a step in the
  fleet section of the redeploy runbook — NOT a `deploy.py` change (which would
  force the deferred parameterization and widen a deliberate test pin), NOT a
  runbook-only prose sequence (a hand-typed SQL sequence would carry none of the
  guards). If the s219-deferred parameterization is ever taken up, folding this
  step into a per-system deploy script is a natural rider — for that PLAN, not
  this one.

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
**RULED (Cray, typed, 2026-08-18 s237): as recommended** — delete deep (runs +
`step_results` + demo-scoped link rows + the demo cases), never audit rows; the
PLAN-0105 SD-4 divergence is granted for the id-reuse sub-case only, and the note
above stays as its record. PLAN change: none — Step 3 already implements this.

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
**RULED (Cray, typed, 2026-08-18 s237): (d) as recommended** — re-scope the
promise in this PLAN (Step 6 + AC-10, active work), with **(b) server-side firing
the NAMED follow-on build** (its RoPA line, anonymous-intake principal question,
and the G4/AC-4/AC-5 joint rewrite all recorded above for that PLAN). G4's bound
holds as current fact; the tripwire stays.

## Verification

1. **Offline (the gate):** `uv run --extra dev pytest tests/api/test_fleet_demo_reset_scenario.py tests/api/test_map_run_filter_contract.py tests/services/db/test_demo_run_reset_fk_guard.py -q 2>&1` — all green **after** each AC's named non-vacuity probe has been SEEN red in a scratch copy (probes restore from the scratchpad, never from git). Full suite + `mypy services/` + bare `ruff check .` per the offline-gate-matches-CI rule. DB-backed tests need the dev Postgres (port 5442); run from the main checkout, not a Windows worktree.
2. **Pass/fail reads were fixed above, per AC — the run confirms them, never rewrites them.** A green whose assertion was not witnessed red on its own mutation is not evidence (CLAUDE.md §8).
3. **Live (evidence, not the gate; host-state → explicit Cray go):** Step 7's checks on the published system — two subjects in `/runs`, one default marker, mode switching, and the play-then-redeploy pristine cycle.
4. Rulings: **all five SDs are RULED** (Cray, typed, 2026-08-18 s237) and stamped in place — SD-A (a), SD-B as recommended, **SD-C = deploy-script step, against the drafter recommendation** (chosen to make the crash-restart mid-session wipe impossible; its cost — a consumed demo stays degraded until the next deploy — is priced in SD-C with the AC-11 observable check and the runbook line as the mitigations), SD-D as recommended, SD-E (d) with (b) the named follow-on. The implementing PR executes the ruled shapes; no SD remains open.

## Post-archival amendment — 2026-08-22 (session 245): G4's tripwire FIRED, and the bound it held is now a measured one

**Why this section exists.** G4 above records the run population as structurally
bounded at two, and carries its own instruction for the day that stops being true:
*"Rewrite this paragraph then; never delete the tripwire."* This is that rewrite,
written **additively** — the ruled history above is not edited and the tripwire text
stays exactly where it stood, because a tripwire that vanishes when it fires cannot
tell the next reader that it ever did.

**Which trigger fired, and in what shape.** G4 named two: (i) `POST /procedures/{id}/run`
being admitted to the allowlist, or (ii) SD-E's named follow-on build (b), server-side
firing **on case creation**. Trigger (i) did **not** fire and must not — that route is
still excluded, under every ruling, on every path. Trigger (ii) fired in a **reversed**
form: Cray reversed SD-E at session 242 so that **quote acceptance**, not case creation,
is the governable moment, and PLAN-0112 Step 3 shipped that seam.
`POST /api/cases/{id}/accepted-quote` joined the published allowlist at PLAN-0112 Step 5
and mints a governed run through the event bridge. A visitor can now create runs, so the
bound this paragraph rested on is gone as a *structural consequence* and has to be
replaced by a *mechanism*.

**The new bound, in the SD-6(b) shape as ruled (Cray, typed, s243).** "Exactly two runs"
becomes **"exactly two runs bearing the fixed demo ids among N visitor runs"**, and the
axis G4 left open is closed by a cap rather than by an assumption: the Monitor's
`GET /runs` carries a **bounded newest-N default** (`settings.runs_list_default_limit`,
shipped default 200), with the client filter unchanged and **both demo runs asserted
within bound**. PLAN-0112 AC-8 owns that pass read;
`tests/api/test_runs_list_bounded_scenario.py` is the code half — including the
demo-runs-within-bound assertion driven through the REAL boot seed, because the demo runs
are the OLDEST rows on a fresh system and therefore exactly what a newest-N bound drops
first.

**One thing the cap deliberately does NOT bound.** `waiting_human_count` — the "waiting
on me" badge Tab H paints — is counted over the whole population, never over the returned
page. A badge that shrank with the page would under-report decisions that are genuinely
still pending, and a governed action nobody is told about is the one failure this surface
exists to prevent. The list is a view; the count is a fact about the system. Both halves
carry their own non-vacuity probe.

**The AC-4/AC-5 framing above is narrowed the same way.** Where those criteria read as
though every run on the system is a demo run, the correct reading after this amendment is
*every run bearing a fixed demo id*. Visitor-fired runs coexist with the demo and stay out
of the reset's reach by run-id scoping — measured in
`tests/api/test_fleet_demo_reset_coexistence_scenario.py` (PLAN-0112 AC-7(i)).

🔴 **That module also recorded a bound AC-7(i)'s own wording missed, and it belongs
here.** Because fleet's `intake` step is a **fleet-wide scan** rather than a lookup of the
accepted case, a visitor-fired run's `approve` gate also decides the seeded demo case, and
the `on_resolved` hook writes one link row per decided case. Measured: a run fired from a
visitor's own case wrote link rows keyed on `['case-<visitor>', 'case-demo-truck03-gearbox',
'case-fleet-operate-demo']`. The reset clears link rows on **both** keys — `run_id` in the
demo ids **or** `case_id` in them — so **every** visitor-fired run loses its
`case-fleet-operate-demo` link row to a reset, whatever case its visitor accepted on. That
is correct rather than defective: the reset erases and re-seeds that case, so a surviving
link would point at a different case reusing the id. The surviving bound is therefore:
the visitor's **run** survives, its **step results** survive, its **non-demo link rows**
survive, and its **demo-scoped link rows do not**.

**Still true and unchanged:** the run-side deletion is id-scoped to `DEMO_RUN_IDS`; the
audit chain is never touched, so an approval stays provable after its link row goes; and
`read_demo_state` reads `PRISTINE` after a reset and one re-boot even with a visitor's run
parked alongside.

**Owning PLAN:** `docs/plans/0112-visitor-case-to-governed-run-tab-i-to-tab-h.md`
(§SD-6, §SD-7, §AC-7, §AC-8).
