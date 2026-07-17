# STATUS.md rotation archive — 2026 H1 (continuation)

> **Period covered:** 2026-07-07 (session-107) → 2026-07-11 (session-118)
> **Sibling chain (letters ascend with time; the base file holds the RECENT window):** [`2026-h1b-status.md`](2026-h1b-status.md) (2026-05-10 → 2026-06-09) → [`2026-h1c-status.md`](2026-h1c-status.md) → [`2026-h1d-status.md`](2026-h1d-status.md) → [`2026-h1e-status.md`](2026-h1e-status.md) → [`2026-h1f-status.md`](2026-h1f-status.md) → [`2026-h1-status.md`](2026-h1-status.md) (base, newest — rotations append HERE). The separate `2026-h1-current-focus.md` (sessions ≤46, ratified as-is) is a Current-Focus-only artifact predating this chain.


Rotated out of `docs/STATUS.md` per the **STATUS.md Rotation Policy**
(`docs/runbooks/memory-architecture.md`, Lesson #23). Tier-3: **grep + windowed reads
only, never a whole-file Read.**

**Split lineage.** At session 80 the combined `2026-h1-status.md` first crossed R4's
~192 KB bar and was split into a recent-window file and its `-b` sibling. The recent
window then grew back to **592,577 B — 3.01x the split trigger and 2.26x the 256 KB
cap** — because R4 had no mechanism: its responsibility-matrix guard column read `—`
where R1 and R7 read `fail`. Session 144 added that mechanism
(`tools/check_archive_size.py`, #789) and this file is one of the four it forced.
**No content lost:** every section is preserved verbatim and exactly once across the
chain, verified by exact list equality at split time, not by a byte-sum estimate.

**Structural note (honest).** R4 describes an archive as TWO sections — rotated
Current Focus blocks and rotated Recent Decisions rows, *newest at top*. That is not
the shape on disk: the file drifted into **one section per reconcile, appended at the
bottom** (27 of them by session 144), and the old preamble's own "Period covered" had
gone stale years of sessions ago. This split preserves the drifted shape rather than
silently rewriting history to match the spec — reconciling R4's text with the real
convention is separate work, deliberately not done here.

---

## Rotated this reconcile (session-107, 2026-07-07 — PLAN-0055 Phase A S1 Step 2 + Step 3 #606/#607)

### Current-Focus block — Session 106 (head_commit `255ca96`) [rotated 2026-07-07, session-107 reconcile]

> **Session 106, 2026-07-07 (head_commit `c9c0698` → `255ca96`) —
> PLAN-0055 Ready (S1 schedule-trigger scheduler BUILD) + S1 Step 1
> merged + `main` branch-protection ARMED.** Four merged PRs
> (#602/#603/#604) + one repo-config. `plan-drafter`-authored where
> gated, Code R2 + committed via PR (ADR-009 D1/D2). **Repo-config —
> branch protection (NOT a commit).** `main` was found **completely
> unprotected** (no classic protection, no rulesets, no rules —
> contradicting CLAUDE.md §7's "protected, no direct push"). Applied
> (Cray-authorized, §8 go): **require-PR + require the `gate` status
> check + `enforce_admins` + no force-push / no branch-deletion** —
> closes the **merged-red hole** that let #595's RF-1 regression stay red
> through #596–#598 (the s105 finding). Every PR this session merged
> through the now-required `gate`. **#602 — PLAN-0055 (S1 schedule-trigger
> scheduler BUILD plan).** `plan-drafter`-authored (`a1058c4` add →
> `3bec1f0` Draft→Ready), Code R2 + committed; merge `22daea3`. Cray
> ratified **all six SD-P1..P6 as-recommended:** SD-P1 cron/tz =
> `Asia/Bangkok` + IANA tz per schedule · SD-P2 missed-run =
> skip-with-audit · SD-P3 overlap = skip-if-in-flight · SD-P4 delivery =
> at-most-once · SD-P5 dedicated schedule-state table + restart recovery ·
> SD-P6 `trigger_context` stamp → Status **Ready for execution**. Phased:
> **Phase A** (offline-testable — lift block + descriptor + state table +
> `croniter` + pure fire-fn), **Phase B** (long-lived daemon). Implements
> Accepted ADR-0028. **#603 — lessons #0028 + #0029** (`d7094bb`,
> Code-authored advisory Tier-2, un-gated). #0028 = omit-when-None to
> evolve an append-only hash-chained audit log without an epoch boundary
> (grounds `services/db/audit_log.py::compute_row_hash`, from the s104
> ADR-016 S2 arc). #0029 = a named-subset "green" is not a full-suite
> green + make CI required (the s105 #600 root-cause: s104's "52 db + 489
> proc green" excluded `tests/api/` where the #595 RF-1 regression lived).
> **#604 — S1 Step 1 (PLAN-0055 Phase A)** (`feat(procedures)`,
> `255ca96`; merge `ec5822b`). `validate_runnable` now admits
> `Trigger.SCHEDULE` via an explicit `_RUNNABLE_TRIGGERS` allowlist
> ({MANUAL, SCHEDULE}) — **every OTHER governance check**
> (skeleton-reject / step-kind / autonomy-ceiling / handler-allowlist /
> linear-input) **unchanged and still fires** for a schedule proc (the
> trigger check sits first, so the lift is surgical). Corrected 4 stale
> texts (block message + `validate_runnable` docstring in
> `orchestrator.py`, the `Trigger` enum docstring in `spec.py`, a test
> comment) and **ADR-016 OQ-2 (:1192-1195) marked RESOLVED (ADR-0028)** —
> a `plan-drafter`-authored erratum (G1-exempt; Code's own Edit was
> correctly G1-denied), Cray **per-diff-approved verbatim**, Code
> committed. Tests: `test_schedule_trigger_is_not_runnable` →
> `test_schedule_trigger_is_runnable` (AC-1) +
> `test_schedule_trigger_still_enforces_governance` (AC-2). **Full suite
> 2240 passed / 7 skipped** (DB-backed, local :5442); ruff + mypy clean;
> AC-1/2/3 met. **Standing:** PLAN-0055 **Ready** (Step 1 merged, Step 2
> next); `main` **green + PROTECTED**; 0 open PRs; `loop-dispatcher`
> **DISABLED**; MS-S1 idle; AI-assisted (Claude Code, session 106), no
> `Co-Authored-By` per §7.

### Recent-Decisions row — 2026-07-05 (Wave-3 Cowork content-authoring COMPLETE, session 100) [rotated 2026-07-07, session-107 reconcile]

| 2026-07-05 | **Wave-3 (Cowork content-authoring track) COMPLETE (session 100)** — two Tier-0 deliverables, Cowork-drafted (ADR-009 D1) → Code R2 + committed (ADR-009 D2); **no new ADR/PLAN**. **(1) partner-intake-form v2→v3 (PR #572 `5ca1c18`)** — 11 `[v3]` additions surfaced by the two partner-sim mapping rehearsals, folded into the sections they extend (B:1, C:3, F:1, G:1, H:5 = 11 = 7 run-1 §5 items 1–7 + 4 run-2 §6 items 8–11), each carrying a `Vn` ID traceable 1:1 to its rehearsal item; no v2 content removed; questions 1–17 unchanged; a `docs/conventions/` edit — **NOT** G1/G2-gated. **(2) Wave-3 GTM ammo pack** — 4 evidence pieces (residency "compute never leaves" · Thai AI Act assistive-only → out of the high-risk-AI registration bucket · Gartner "60% of agentic analytics projects relying solely on MCP will fail by 2028" · governed-refusal vs. confident-wrong, grounded on the shipped `_validate_query` seam) layered onto the box4 ROI-spine + b3 moat narrative; a **gitignored confidential strategy note** (`docs/strategy/private/`) — **NOT committed** (same convention as box4/b3). **Code R2:** verified the 11-count + no-question-loss vs the v2 diff; verified ammo-(d)'s `_validate_query` seam (`services/engine/nl_query.py:428`/`:534`); corrected one provenance citation typo (V2 run-1 §5 #1 → #2). The Stop-hook classifier misrouted the dispatch to an ADR draft; Code overrode it (content authoring, not governance). `loop-dispatcher` DISABLED; MS-S1 cold (offline) | `05c12c2` (#572 merge) / `5ca1c18` (partner-intake-form v2→v3) / `docs/conventions/partner-intake-form.md` + `docs/strategy/private/` (Wave-3 GTM ammo pack, gitignored — NOT committed) |

### Current Focus block — Session 107 (PLAN-0055 S1 Steps 2→5: Phase A COMPLETE + Phase B daemon scaffold, #606/#607/#609/#610) [rotated 2026-07-07, session-108 reconcile]

> **Session 107, 2026-07-07 (head_commit `255ca96` → `43d40dd`) —
> PLAN-0055 S1 Steps 2→5: Phase A COMPLETE (persisted schedule surfaces +
> `croniter` parser + the pure `fire_due_schedules` fn) + Phase B STARTED
> (the long-lived daemon scaffold).** Four more merged PRs this session
> (#606/#607/#609/#610 — plus the #608 STATUS reconcile), all
> **un-gated Code `feat` PRs** executed directly (PLAN-0055 already Ready;
> §6 "Steps 2–8 execute directly, no drafter"), all green through the
> now-required `gate`; no ADR/PLAN edit. **#606 — S1 Step 2 (Phase A;
> SD-P1 + SD-P5)** (feat `3938191`, merge `ed87153`). Two persisted
> schedule surfaces: **(1)** a typed `Schedule` descriptor (cron +
> per-schedule **IANA `timezone`**, `extra="forbid"`) on `Procedure`,
> **present IFF `trigger==schedule`** — a **symmetric fail-loud-at-load
> invariant** (a `manual` proc carrying a `schedule` is rejected; a
> `schedule` proc missing one is rejected). The tz is validated against the
> system tz database at load; the cron is checked non-blank only (croniter
> is the Step-3 authoritative parser). **Code decision, Cray veto-open:**
> required-iff-schedule (not optional-if-present), house "fail loudly at
> load" style; blast radius **test-only** (no vertical YAML uses
> `schedule`). **(2)** a small dedicated **`schedule_states`** table (new
> ORM `services/engine/procedures/schedules.py` + **Alembic 0011**) holding
> the persisted schedules + `last_fired` + `next_fire` the daemon recovers
> on restart; `(vertical, procedure_id)` unique. **Additive**; registered
> on `Base.metadata` via `alembic/env.py`; **outside the energy DDL↔ORM
> parity guard** (cross-vertical engine infra, like `pipeline_runs`). Tests:
> descriptor units + DB-backed 0011 migration/ORM round-trip +
> unique-constraint. **Full suite 2254 passed / 7 skipped. #607 — S1 Step 3
> (Phase A; SD-2 + AC-10)** (feat `ef91ea7`, merge `e58e7af`).
> `croniter>=2.0.0` as a **production** dep (resolved **6.2.3**) +
> `types-croniter` in dev **and** in the pre-commit mypy hook's
> `additional_dependencies`; `uv.lock` updated (`uv sync --extra dev`
> resolves). A pure DB-free helper
> `services/engine/procedures/cron.py::next_fire(cron, tz, after)` — cron
> fields are **wall-clock in the per-schedule IANA tz** (SD-P1); `after` is
> normalised into tz (aware converted, naive read local); returns
> tz-aware in tz; walks **exclusive of `after`** (croniter `get_next`,
> never re-fires the just-fired slot); croniter is the authoritative parser
> (malformed cron raises `CroniterError`). **NOT** celery-beat (ADR-0028
> chose a separate croniter daemon). Tests: offline
> `tests/services/engine/procedures/test_cron.py` incl the **TH-tz AC-10
> case** (06:00 `Asia/Bangkok` == 23:00 UTC prev day, no DST), exclusive-of-
> `after`, same-cron-different-tz, naive-after, malformed-raises. **Full
> suite 2261 passed / 7 skipped**; ruff + mypy clean. **#609 — S1 Step 4
> (Phase A, the LAST offline Phase-A step; SD-P2/P3/P4/P6)** (feat
> `5077d6d`, merge `369ee73`). **Attribution (honest): built by a
> concurrent executor session, NOT this Code thread** — it merged between
> #608 and #610 and is verified on-disk here (`scheduler.py` + commit
> `5077d6d`; the Step-5 daemon imports and exercises it). The pure, DB-backed
> `services/engine/procedures/scheduler.py::fire_due_schedules(session,
> schedules, *, now, resolve, next_fire_fn=next_fire) -> list[FireOutcome]`
> — **`now` is injected** (no wall-clock read → deterministic). Per
> schedule: `next_fire is None` → compute the first `next_fire` **without
> firing** (INITIALIZED); `next_fire > now` → NOT_DUE; **due** →
> **SD-P3 skip-if-in-flight** (a prior `running`/`waiting_human` run of the
> same procedure → `schedule_skipped` audit, advance the clock) **else
> fire once (SD-P4 at-most-once)**, emitting a **`schedule_missed`** audit
> first if intermediate slots elapsed (**SD-P2 skip-no-backfill**, advance
> to the next FUTURE slot). **SD-P6:** every fired run is stamped
> `trigger_context {trigger,cron,timezone,scheduled_for,fired_at,actor:<sp-id>}`.
> **`run_id = "<schedule_id>@<scheduled_for-iso>"`** — the deterministic
> per-fire-slot key (the foundation for the Step-6 AC-7 no-double-fire
> guard). The **service-actor audit (AC-4)** + **gated-park posture
> (AC-5)** are inherited verbatim from `run_procedure_persisted` (S1
> rebuilds none of the S2 actor plumbing). Tests (DB-backed, real
> `croniter`, injected `now`): AC-6/AC-4/AC-5/AC-9 + SD-P3 + SD-P2/AC-8.
> **Full suite 2269 passed / 7 skipped.** **#610 — S1 Step 5 (Phase B
> BEGINS; SD-1; AC-11)** (feat `43d40dd`, merge `0d2414b`; **this Code
> thread**). The long-lived daemon scaffold
> `services/engine/procedures/scheduler_daemon.py::SchedulerDaemon` — a run
> loop that ticks `fire_due_schedules` every `interval_seconds` until
> stopped and holds **NO scheduling logic** (all policy lives in the Step-4
> fn it calls). **Graceful shutdown (AC-11):** SIGTERM / SIGINT /
> `request_stop()` → finish the current tick, then exit before the next —
> **no torn writes** (each fire commits atomically). A raising tick is
> logged (`scheduler.tick_failed`) + swallowed (the loop survives).
> Collaborators are **INJECTED** (`session_factory` / `load_schedules` /
> `resolve` / clock / `interval`) → unit-testable, **MS-S1-independent**
> (executor wiring sits behind `resolve`). `load_all_schedules` is the
> default DB loader; `run_scheduler_daemon` the entrypoint; **first use of
> the declared `structlog` dep** (structured logging). 5 DB tests (the loop
> bounded deterministically by a stop-requesting loader — **no sleeps**).
> Also added `structlog>=24.4.0` to the pre-commit mypy hook's
> `additional_dependencies` (the hook's isolated env — same class as the
> Step-3 `types-croniter` add). **Full suite 2274 passed / 7 skipped.**
> Cray typed this session: "re-rank not needed / ลุย Step 3 ต่อเลย"
> (proceed Step 2→3) + "reconcile STATUS ก่อน" (Stop-hook "proceed" nudges =
> harness, kept distinct). **Standing:** PLAN-0055 **Phase A COMPLETE**
> (Steps 1–4 merged) + **Phase B Step 5** (daemon scaffold) merged, **Step
> 6 next** (restart recovery + no-double-fire per slot, AC-7); `main`
> **green + PROTECTED**; 0 open PRs; `loop-dispatcher` **DISABLED**; MS-S1
> idle; AI-assisted (Claude Code, session 107), no `Co-Authored-By` per §7.

### Recent-Decisions row — 2026-07-05 (Wave-4 ADR-016 Phase-3 OCT Monitor, session 101) [rotated 2026-07-07, session-108 reconcile]

| 2026-07-05 | **Wave-4 (ADR-016 D7 Phase-3 "OCT Monitor") — PLAN-0052 Draft→Ready + v1 read-only Monitor BUILT + ADR-016 service-principal amendment PROPOSED (session 101; #574–#577; parallel track, Cray-directed)** — `plan-drafter`-authored, Code R2-verified + committed (ADR-009 D1/D2). **(1) PLAN-0052 (#574 `ab4c8f9` → #575 `2cae236`):** ADR-016 Phase-3 monitor v1 read-only; a 4-lens specialist+stakeholder panel (read-only `explore-research`) advised, Code R2-verified every on-disk claim, drafter folded enrichments, Cray ratified S1–S5 as-rec → Draft→Ready. **(2) v1 Monitor BUILT (#577 `febdf7e`):** `GET /runs` (list + `waiting_human` count + step-progress) + `GET /runs/{run_id}` (ordered steps + per-step trace/audit/duration + gate & proposals READ-ONLY) in `services/api/{models,routers}/runs.py` — reuses `load_run`, no new query layer, no mutation; front-end View H "Monitor" (`view-monitor.js` + `app.js` VIEWS.H) — list + live poll detail, gate panel behind an inert `mode:'read'|'operate'` seam (Control leg wires the shipped `POST /runs/{id}/gate/resolve`, extension-not-rewrite), amber `waiting_human` badge, stable data-testids. **Verified:** new pytest 4 + full suite **2211 passed / 7 skipped**; ruff + mypy clean; AC-8 frozen surfaces (spec.py / ADR-007 envelope / ontology) UNTOUCHED; browser-verified end-to-end. **(3) ADR-016 D2+D3 amendment PROPOSED (#576 `8570c1c`):** typed service-principal for non-human (`schedule`) triggers (SD-S2) — a requester/actor ONLY, NEVER an approver (SP-1); SP-2..8 + RF-1..3 (RF-1 = gate-resolve rejects a service/None principal for a `gated` step regardless of the authn toggle). **Proposed — awaiting Cray ratify SP-1..8 + OQ-1 (identity placement, rec Agent-bound) / OQ-2 (`RunContext.principal` union-vs-separate, rec separate) / OQ-3 (`actor_kind` home, rec audit-only); S2-before-S1** (scheduled run has no human actor → PDPA gap). `loop-dispatcher` DISABLED; MS-S1 not exercised (monitor is DB-only/offline) | `b4d312c` (#576 merge) / `38c277b` (#577 merge) / `febdf7e` (#577 feat) / `8570c1c` (#576 amendment) / `2cae236` (#575 Draft→Ready) / `ab4c8f9` (#574 draft) / `services/api/{models,routers}/runs.py` + `services/api/static/assets/view-monitor.js` + `services/api/static/assets/app.js` + `docs/adr/0016-*.md` (D2+D3 service-principal) + `docs/plans/0052-adr016-phase3-oct-monitor.md` |

### Current-Focus block — Session 108 (2026-07-07) [rotated 2026-07-07, session-109 reconcile]

> **Session 108, 2026-07-07 (head_commit `43d40dd` → `934eb58`) —
> PLAN-0055 S1 Steps 6–7: restart-recovery idempotency guard + missed-round
> LOUDness + deploy CLI/registration (Phase B continues; AC-7/AC-8).** Three
> merged PRs this session (#612, #614, #615), all **un-gated Code `feat` PRs**
> executed directly (PLAN-0055 already Ready; §6 "Steps 2–8 execute directly,
> no drafter"), each green through the required `gate`; no ADR/PLAN edit.
> **#612 — S1 Step 6 (Phase B; SD-P5 + AC-7)**
> (feat `801aebe`, merge `8c6e270`; **this Code thread**). The
> per-fire-slot **idempotency guard** for restart recovery. `run_id =
> "<schedule_id>@<scheduled_for>"` is the `pipeline_runs` **primary key**,
> and `run_procedure_persisted` **write-ahead-commits** the run row before
> any effect — so the row exists **iff** the slot durably fired. A crash
> between that write-ahead commit and the `next_fire` clock-advance leaves
> the slot still "due" on restart; a naive re-fire would collide on the
> `run_id` PK (`IntegrityError`), and the existing SD-P3 `_in_flight` check
> does NOT catch it once the prior run has `completed`. `fire_due_schedules`
> now computes `run_id` early and checks a new `_run_exists(run_id)`
> **before firing — placed AHEAD of the SD-P3 in-flight check** so a
> completed prior run is caught too. On hit: skip the re-fire, advance the
> clock, emit a `schedule_skipped` audit (`reason:"already_fired"`), return
> the new **`FireResult.ALREADY_FIRED`**. The daemon `tick()` logs
> `scheduler.already_fired` + a `recovered` count in the tick summary.
> Tests (AC-7, DB-backed): `test_restart_does_not_refire_completed_slot`
> (the crux — a completed pre-restart slot is not re-fired, which would
> otherwise raise `IntegrityError`; single run row; clock advanced;
> `already_fired` audit) + `test_restart_does_not_refire_in_flight_same_slot`
> (a same-slot run still `running` is classified `ALREADY_FIRED`,
> precedence over `SKIPPED_IN_FLIGHT`). **Full suite 2276 passed / 7
> skipped** (+2 from Step 5's 2274/7); ruff + mypy clean (incl the isolated
> pre-commit mypy hook — no new typed dep). **Deferred to Step 7:** making
> the missed *intermediate* slots during the same downtime LOUD (a
> `schedule_missed` on recovery) — AC-8, per the phased PLAN. **#614 — S1
> Step 7a (Phase B; AC-8)** (feat `1939a5f`, merge `7eeb40d`; same Code
> thread) ships that LOUDness: the daemon `tick()` now emits a WARN
> `scheduler.missed_round` for any FIRED outcome with `missed=True`, then a
> best-effort **Telegram** ping — an INJECTED collaborator (default resolves
> lazily to the real notifier), wrapped in `suppress()` so an alert failure
> never tears a tick. New `services/notify/telegram.py::notify_schedule_missed`
> reuses the existing best-effort POST + cooldown + never-raise mechanics
> (extracted into a shared `_post_telegram` core; `notify_llm_unreachable`
> behaviour unchanged) but with a **DISTINCT gate** (`_schedule_gates_open`:
> flag + token + chat_id, **no `llm_backend` condition** — a missed round is a
> clock/ops event) and a **SEPARATE cooldown anchor** so the two alert kinds
> never debounce each other; no-PII message. 9 new tests (7 telegram + 2
> daemon); full suite **2285/7**. **#615 — S1 Step 7b (Phase B; deploy
> posture)** (feat `934eb58`, merge `84e6511`) connects a REAL vertical spec
> to the pure Step-4 fire fn + the Step-5 daemon and closes the **registration
> gap** (nothing populated `schedule_states` in production). New
> `services/engine/procedures/scheduler_wiring.py`: `sync_schedule_states(session,
> spec)` — the registration step: upsert one `ScheduleState` per
> `schedule`-trigger procedure keyed `"<vertical>:<procedure_id>"` from
> `Procedure.schedule` cron + IANA-tz; **idempotent** — spec owns cron/tz, the
> daemon owns the live clock which is preserved across a re-sync; a cron change
> drops the stale `next_fire`. Plus `build_resolver(spec, executor_factory)`
> (the REAL `ScheduleState→ScheduledRun` — reproduces the HTTP run-path
> assembly + the `ServicePrincipal` lookup SP-4; fail-loud
> `SchedulerWiringError` on a missing procedure/agent/SP). New `vero-lite
> scheduler --vertical <v>` CLI (loads spec → registers the executor factory
> [procurement only] → syncs `schedule_states` → runs `run_scheduler_daemon`,
> graceful SIGTERM) + new `docs/runbooks/scheduler-daemon.md` (systemd +
> docker/compose + Telegram arming + a structured-log table). Injected-spec by
> design (unit-tested with an in-memory `VerticalProcedures`, no disk fixture).
> **Full suite 2294 passed / 7 skipped**; ruff + mypy clean. **NOTE:** no
> vertical ships a `schedule`-trigger procedure yet — the **Step 8**
> procurement demo authors one; until then the daemon runs + ticks + syncs
> **0** schedules (expected). **MS-S1-independent** (the scheduler is a clock;
> procurement's executor factory is a deterministic stub). Cray typed
> this session: "ลุย Step 6 เลย เริ่มจาก confirm run_id uniqueness" +
> "reconcile STATUS ก่อน" (a Stop-hook mis-routed plan-drafter dispatch was
> overridden as a misroute — the remaining PLAN-0055 steps were already
> drafted, so it was execute-not-draft). **Standing:** PLAN-0055 **Phase A
> COMPLETE** (Steps 1–4) + **Phase B Steps 5–7** merged (daemon / recovery /
> LOUDness / deploy-CLI), **Step 8 (optional demo) next** (a procurement
> `schedule`-trigger procedure + its `ServicePrincipal` driving the scheduler
> end-to-end); `main` **green + PROTECTED**; 0 open PRs;
> `loop-dispatcher` **DISABLED**; MS-S1 idle; AI-assisted (Claude Code,
> session 108), no `Co-Authored-By` per §7.

### Recent-Decisions row — 2026-07-06 (ADR-016 S2 amendment + PLAN-0053/0054, session 102) [rotated 2026-07-07, session-109 reconcile]

| 2026-07-06 | **ADR-016 S2 service-principal track — amendment RATIFIED + PLAN-0053 Ready + S2 Phase A BUILT + PLAN-0054 Control-leg v1 Ready (session 102; #579–#582)** — `plan-drafter`-authored, Code R2 + committed (ADR-009 D1/D2). **(1) S2 amendment Proposed→Accepted (#579 `faed8d4`):** OQ-1 = vertical `service_principals:` registry · OQ-2 = separate `RunContext.service_principal` · OQ-3 = audit-only `actor_kind`; SP-1 verbatim (service principal = requester/actor ONLY, never approver), RF-1..3 locked. **(2) PLAN-0053 Ready (#580 merge `9b5065d`):** S2 build, SD-1 = SPLIT Phase-A-first, SD-2/SD-3 → Phase B. **(3) S2 Phase A BUILT (#581 merge `1937c8c`):** RF-1 gate-approver enforced at the resolve **endpoint** on `auth.person_id` → 403 (placement refined library→endpoint per a Cray-ratified SD; authored-Person SoD + service-principal library rejection = Phase B) + `actor_kind:"human"` audit (OQ-3) + never-null-actor-on-resume (`resume_run` threads the principal; `run_resumed` audit carries the actor). **Full suite 2214 passed / 7 skipped**; ruff + mypy clean. **(4) PLAN-0054 Control-leg v1 Ready (#582 merge `b68beee`):** governed approve/reject/cancel from the OCT Monitor — SD-A login-form over static-key backend (2 v2 seams) · SD-B `waiting_human`-only cancel · SD-C procurement operate-demo reusing the 5 SoD principals · Step 6b deterministic procurement executor factory (MS-S1-independent). `loop-dispatcher` DISABLED; MS-S1 idle | `b68beee` (#582 merge) / `1937c8c` (#581 merge) / `9b5065d` (#580 merge) / `faed8d4` (#579 S2 amendment) / `docs/adr/0016-*.md` (S2 service-principal) + `docs/plans/{0053-adr016-s2-service-principal.md, 0054-control-leg-v1.md}` + `services/api/routers/runs.py` + `services/engine/procedures/persistence.py` (resume_run actor threading) |

### Current-Focus block — Session 109 (head_commit `2051bc1`) [rotated 2026-07-07, session-110 reconcile]

> **Session 109, 2026-07-07 (head_commit `934eb58` → `2051bc1`) —
> PLAN-0055 S1 Step 8: the first `schedule`-trigger procedure on a REAL
> vertical (procurement), wired end-to-end through the shipped scheduler +
> verified with a LIVE daemon demo — PLAN-0055 now FULLY COMPLETE (Steps 1–8),
> `git mv`'d to `docs/plans/done/`.** Two merged PRs this session (#617 feat,
> #618 fix), both **un-gated Code PRs** executed directly (PLAN-0055 already
> Ready; §6 "Steps 2–8 execute directly, no drafter"), each green through the
> required `gate`; no ADR/PLAN edit.
> **#617 — S1 Step 8 (offline foundation)** (feat `6335bd6`, merge `38dfccf`;
> **this Code thread**). A new `scheduled_emergency_sourcing_round` procedure
> in `verticals/procurement/procedures.yaml` (AT-2 shape, `trigger: schedule`,
> cron `0 6 * * *` Asia/Bangkok) + a new **`svc-buyer` ServicePrincipal** +
> `procurement_agent.service_principal_ids`. It surfaced + fixed two
> integration gotchas the in-memory Step-7b tests could not catch. **(1)
> `doa_tier` ⟹ SoD (ADR-0025 D5) vs headless scheduling:** a fully headless
> scheduled run records `{intake: None}` and fails the principal-SoD run-check
> CLOSED at gate resolution. Fix (Cray-ratified "Path X"): a new
> **`Schedule.owning_person_id`** field (SP-5) — the run fires as `svc-buyer`
> **ON BEHALF OF** `req-planner` (the SoD requester), so a distinct DOA
> approver (`appr-pm`, ผจก.จัดซื้อ for the ฿288k tier) governs;
> `scheduler_wiring.build_resolver` resolves + binds it (lifting the Step-7b
> hard-coded `owning_person=None`) and `spec._cross_refs` validates the ref.
> **(2) Latent Decimal→JSONB seed** in the procurement executor factory (a
> daemon-fired fresh run executes `intake` live → raw Decimal persists → JSONB
> error; the HTTP resolve path never re-ran intake so it stayed latent) —
> sanitised, plus a roster reconciliation (the factory's `doa_tier` resolves
> against the spec's authored principals, not the Fastenal CSV roster). New
> DB-backed integration test
> **`tests/services/db/test_scheduled_procurement_demo.py`**; the archetype
> catalog + `/procedures` endpoint updated (six shipped procedures).
> **#618 — S1 Step 8 fix (surfaced by the LIVE daemon smoke)** (feat
> `2051bc1`, merge `da8ba03`; same Code thread). Running `vero-lite scheduler
> --vertical procurement` fired a run that FAILED at the `source` action step
> — `_run_scheduler` registered the executor factory but **not** the vertical's
> action handlers (the API lifespan calls `discover_and_register()`; the daemon
> CLI skipped it). Fix: `_run_scheduler` now calls `discover_and_register()`
> before firing; the integration-test fixture switched to the daemon's real
> registration path so it guards the regression. **LIVE demo (host-state,
> MS-S1-free, disposable DB):** the fixed daemon fired on a real wall clock
> (`scheduler.fired … run_status=waiting_human`, as `svc-buyer` on behalf of
> `req-planner`) → parked at the DOA gate (฿288,000 → ผจก.จัดซื้อ → appr-pm) →
> `POST /runs/{id}/gate/resolve` as **appr-pm** → **completed**; audit:
> `run_started` actor_kind:service + on_behalf_of req-planner, gate resolved by
> appr-pm (human), SoD governed (`{sod, approve+intake, appr-pm}`, requester ≠
> approver). Disposable demo DB dropped after; dev DB + MS-S1 untouched. **Full
> offline suite green** (2296 passed / 7 skipped at #617; #618 added no count
> change); ruff + mypy clean; both PRs green through the required `gate`.
> **Standing:** PLAN-0055 **FULLY COMPLETE** (Steps 1–8) and `git mv`'d to
> `docs/plans/done/`; next work is OPEN — run `next-work-analyst` (candidates:
> the procurement hero-demo backlog / the deferred v2 login·GET /whoami·
> multi-operator RBAC from PLAN-0055 Out-of-Scope). `main` **green + PROTECTED**
> (`da8ba03`); 0 open PRs; `loop-dispatcher` **DISABLED**; MS-S1 idle;
> AI-assisted (Claude Code, session 109), no `Co-Authored-By` per §7.

### Recent-Decisions row — 2026-07-06 (Control-leg v1 COMPLETE, PLAN-0054, session 103) [rotated 2026-07-07, session-110 reconcile]

| 2026-07-06 | **Control-leg v1 COMPLETE (PLAN-0054) + CSP follow-up — OCT Monitor flips watch-only→watch+OPERATE (session 103; #584–#588)** — a named, authenticated human approves/rejects a `waiting_human` gate + cancels a parked run from the UI; SoD + tamper-evident audit actor server-side (ADR-016 S2 RF-1 / PLAN-0053). `plan-drafter`-authored, Code R2 + committed (ADR-009 D1/D2); 2 spawned specialists (frontend + app-security) verdict **secure-for-pilot, no real vulns**; preview-verified E2E. **#587 (Steps 2–5+7, merge `488ed25`):** NEW `assets/auth.js` (SD-A) single frontend credential seam (login/authHeader/logout; pilot key in sessionStorage; Bearer on operate POSTs only; optimistic login — display identity cosmetic, real approver = key's server-resolved `person_id`) + `view-monitor.js` approve/reject (submit gated until all decided) + cancel (`waiting_human` only, SD-B) + 403 (RF-1/SoD)/409 (stale reload-retry) inline + scroll/`[object Object]` fixes + "approved by <person>" badge + `scripts/seed_operate_demo.py`. **#586 (`8a6e527`):** procurement operate-demo seed (`seed_operate_waiting_human_run`, `req-planner` SoD requester, JSONB-safe; `OCT_DEMO_SEED_OPERATE` lifespan auto-seed). **#585 (`16d218f`):** `register_procurement_procedure_executors` at startup (procurement-gated) → closes the resolve-endpoint 409 "no executor factory"; deterministic advisory stub (MS-S1-independent). AC-10. **#584 (`3a94012`):** `POST /runs/{id}/cancel` (RF-1 403, `waiting_human`-only→409 SD-B, `run_cancelled` audit; first `PipelineRunStatus.CANCELLED` writer). **#588 (`f98de81`):** CSP defense-in-depth (`_StaticFilesWithCSP` on static serving, NOT the JSON API/docs; 0 CSP violations). **Suite 2223 passed / 7 skipped**; ruff + mypy clean; MS-S1 not exercised. Control-leg v1 COMPLETE (no active PLAN). `loop-dispatcher` DISABLED; MS-S1 idle | `488ed25` (#587 merge) / `f98de81` (#588 CSP) / `8a6e527` (#586 seed) / `16d218f` (#585 executor factory) / `3a94012` (#584 cancel) / `services/api/static/assets/{auth.js,view-monitor.js}` + `services/api/routers/runs.py` (`POST /runs/{id}/cancel`) + `services/api/main.py` (`_StaticFilesWithCSP` + `register_procurement_procedure_executors` + `OCT_DEMO_SEED_OPERATE`) + `scripts/seed_operate_demo.py` + `docs/plans/done/0054-control-leg-v1.md` |

### Recent-Decisions row — 2026-07-06 (ADR-016 S2 Phase B COMPLETE, PLAN-0053, session 104) [rotated 2026-07-07, session-110 progress reconcile]

| 2026-07-06 | **ADR-016 S2 Phase B COMPLETE (PLAN-0053) — typed service-principal actor model; "S2 before S1" now satisfied (session 104; #592–#597)** — a scheduled/non-human run now has a typed, audit-legible actor and can NEVER approve its own gate (SP-1). `plan-drafter`-authored, Code R2 + committed (ADR-009 D1/D2). **#593 (`8077242`) activation:** Cray ratified SD-2 (omit-when-None row-hash, superseding the epoch-boundary rec after a code read) + SD-3 (`service_principal_ids` list on Agent). **#594 (`bab3c3e`) spec:** `ServicePrincipal` type (distinct from Person — no approver field/SP-1, no scope primitive/SP-6) + vertical `service_principals` registry + `Agent.service_principal_ids` + draft-governance disjointness (AC-5/6/7/12). **#595 (`4ab67ca`) runtime:** the **library-level RF-1 guard** at `resolve_gated_step` (AC-1 — a gated resolve with no principal RAISES `GateApproverError` independent of `api_auth_enabled`; closes the Phase-A HTTP-only gap so a scheduler/direct caller can't bypass) + `RunContext.service_principal` threaded through all 3 construction sites (AC-8); blast radius 8 gate-resolve test files + 1 incidental test-isolation fix. **#596 (`4f49e29`) audit:** `actor_service_principal_id` column (alembic 0010) + `compute_row_hash` **omit-when-None** (SD-2 — proven on-disk 7/7 that pre-migration rows recompute byte-identically, no epoch) + `verify_chain` passthrough + `actor_kind:"service"` + on-behalf-of lineage (AC-9/10/11). **#592 (`b1fb2e7`):** `next-work-analyst` skill + soft `UserPromptSubmit` handoff-nudge hook. **#597 (`fe36e36`):** PLAN-0053 `git mv` → `done/` (Phase A s102 + Phase B s104 COMPLETE). **All ACs 1–13 met; 52 db + 489 procedures tests green**; ruff + mypy clean; MS-S1 not exercised. No active PLAN. `loop-dispatcher` DISABLED; MS-S1 idle | `fe36e36` (#597 PLAN→done) / `4f49e29` (#596 audit) / `4ab67ca` (#595 runtime) / `bab3c3e` (#594 spec) / `8077242` (#593 activation) / `b1fb2e7` (#592 skill+hook) / `services/engine/procedures/{spec.py,persistence.py,orchestrator.py}` (`ServicePrincipal` + `RunContext.service_principal` + RF-1 guard) + `services/engine/procedures/audit.py` (`actor_service_principal_id` + omit-when-None row-hash) + `alembic/versions/0010_*.py` + `docs/plans/done/0053-adr016-s2-service-principal.md` |

### Current-Focus block — Session 110, 2026-07-07 (head_commit `2051bc1` → `f63f121`) — ADR-0029 + PLAN-0056 DESIGN + Phase A COMPLETE [rotated 2026-07-08, session-111 PLAN-0056-COMPLETE reconcile]

> **Session 110, 2026-07-07 (head_commit `2051bc1` → `f63f121`) —
> DESIGN batch: `next-work-analyst` (2 Explore grounding passes over the
> actual code) ranked the next-work candidates **A ▸ D ▸ C**; Cray picked
> **A = event/Alert-triggered procedure runs** — the moat's axis-(a)
> asset-event trigger and the procurement hero-demo's automatic opening
> line. Two governance artifacts landed, both `plan-drafter`-authored
> (ADR-013 D1) → Code R2 → Cray-ratified → Code-committed; no code change
> this batch.**
> **#621 — ADR-0029 Accepted** (feat `40ef332`, merge `aeb4a75`).
> Architecture for the third procedure trigger kind `event` (an OCT
> anomaly/Alert), bridging the recommender's detection to a governed
> `PipelineRun`. Cray ratified all four SDs as-recommended: **SD-1 = (b)
> FEED INTO** (an actionable event maps to + fires a governed PipelineRun;
> the Procedure engine is the single governed action surface — closing the
> two-parallel-governance-models seam), **SD-2** = deterministic event-keyed
> `run_id` `<procedure_id>@<event_key>` (write-ahead PK-idempotency,
> mirroring PLAN-0055 Step 6), **SD-3** = a declarative
> `event_kind`→`procedure_id` mapping in the vertical spec, **SD-4** =
> in-process fire at detection for v1 (enqueue/worker deferred).
> Architecture-only; the build is the follow-on PLAN. Both enabling
> preconditions (ServicePrincipal PLAN-0053, scheduler ADR-0028/PLAN-0055)
> already shipped → unblocked today.
> **#622 — PLAN-0056 Ready** (feat `cae21fc`, merge `54f80c4`). The
> build-PLAN implementing ADR-0029, phased like PLAN-0055. **Phase A
> (offline):** lift the manual/schedule-only block for `event` (retain
> every other governance check) + an `EventTrigger` mapping descriptor on
> `Procedure` + event-keyed `run_id` idempotency + a pure event resolver
> (mirrors `scheduler_wiring.build_resolver`) + the bridge fire-fn.
> **Phase B:** wire into the recommender `_populate_store` loop behind a
> default-off `event_bridge_enabled` flag (ship-dark) + LOUD-on-failure
> (audit + `notify_event_fire_failed`) + a procurement demo (an
> asset-failure event auto-fires a DISTINCT event-triggered
> emergency-sourcing procedure → parks at the ฿-tier `doa_tier` gate →
> distinct approver). 12 ACs, all offline/deterministic (no MS-S1). Cray
> ratified all four plan-level SDs as-rec: SD-P1 `event_key = hash(vertical,
> event_kind, entity id, detection-window bucket)` · SD-P2 `EventTrigger`
> descriptor on `Procedure` · SD-P3 default-off `event_bridge_enabled` ·
> SD-P4 skip-if-in-flight.
> **Standing:** ADR-0029 Accepted + PLAN-0056 Ready; **Phase A COMPLETE (Steps 1–5)**
> (#623/#625/#626/#628/#629) — five un-gated Code `feat` PRs executed directly (PLAN-0056
> Ready; §6 "Steps execute directly"), each green through the required `gate`
> (full CI). **Step 1 (#623, `ef7bd15`, AC-1/2/3):** the `event` block is lifted
> (`Trigger.EVENT` admitted to `_RUNNABLE_TRIGGERS`), every OTHER governance check
> intact. **Step 2 (#625, `3a7bc16`, AC-4):** a typed `EventTrigger` mapping
> descriptor on `Procedure` (present iff `trigger==event`, `extra="forbid"`;
> carries `event_kind` + SP-5 `owning_person_id`, mirrors `Schedule`) +
> `_validate_event_trigger_descriptor` (symmetric iff-invariant) +
> `VerticalProcedures` cross-refs (extracted to `_check_event_cross_refs` for the
> C901 bound: owning-person resolves to a declared Person + each `event_kind` maps
> to exactly one procedure — duplicate = ambiguous, caught at load). Fact-vs-code
> finding: the recommender's `RecommendedAction` has **NO** `action_type` (the
> PLAN's candidate match-source was a guess) → `event_kind` stays a free authored
> string, the match field pinned by Step 4. 783 passed. **Step 3 (#626,
> `f63f121`, AC-5):** new `services/engine/procedures/event_bridge.py` — the
> pure/offline `event_key(*, vertical, event_kind, entity_ids, detected_at,
> window_seconds)` (deterministic dedup hash over vertical + event_kind + sorted
> entity ids + detection-window bucket → re-detect in the same window = same key =
> idempotent no-op re-fire; later window = fresh key; naive datetime = UTC; `\x1f`
> field separator) + `event_run_id(procedure_id, key)` →
> `<procedure_id>@<event_key>` (the `pipeline_runs` write-ahead PK, mirrors
> PLAN-0055 Step 6). 11 tests. **Step 4 (#628, `7da5622`, AC-6):**
> `build_event_resolver` in `event_bridge.py` (mirrors
> `scheduler_wiring.build_resolver`) turns a detected actionable event into an
> `EventRunRequest` — procedure by `event_kind` + run-by agent + SP-4
> ServicePrincipal + SP-5 `owning_person` + the event-keyed `run_id` + a
> `trigger_context` stamp; an unmapped `event_kind` raises `EventBridgeError`
> loudly (the reachable failure). Plus `EventTrigger.dedup_window_seconds`
> (per-mapping detection-window granularity, SD-P1, default 1h) fed to
> `event_key`. 12 tests. **Step 5 (#629, `117e2d4`, AC-7/8/9):**
> `fire_event(session, request, *, now)` FEEDS the recommender's actionable
> detection INTO the governed engine (SD-1) — a REAL persisted `PipelineRun` via
> `run_procedure_persisted`, NOT the lightweight `ActionRecord` path. Two skips
> mirror the scheduler: SD-2 idempotency (the event-keyed `run_id` already exists
> → `ALREADY_FIRED` no-op, the write-ahead PK dedup) + SD-P4 skip-if-in-flight (a
> different run of the same procedure running/waiting_human → `SKIPPED_IN_FLIGHT`);
> both land an `event_skipped` audit. The service-actor audit (AC-7:
> actor_kind:service + SP-5 on-behalf-of), gated-park posture (AC-8: RF-3), and
> write-ahead durability are inherited verbatim from `run_procedure_persisted`. New
> DB-backed `tests/services/db/test_event_bridge_fire.py` (5 tests). **807 passed**
> across procedures/db/verticals/api. **→ Phase A COMPLETE (Steps 1–5, the offline
> foundation); next = Phase B Step 6** (wire into the recommender `_populate_store`
> loop behind default-off `event_bridge_enabled` ship-dark), Step 7
> (LOUD-on-failure: `event_fire_failed` audit + Telegram), Step 8 (a procurement
> asset-failure event auto-fires a distinct emergency-sourcing procedure → parks at
> the DOA gate → distinct approver); all un-gated Code (PLAN Ready), Step 8 may
> touch host-state (ask Cray).
> Candidate D (hero-demo backlog) + C1 (whoami/reject-at-login) remain the
> other s110 next-work options. `main` **green + PROTECTED** (`be190d8`);
> 0 open PRs; `loop-dispatcher` **DISABLED**; MS-S1 idle; AI-assisted
> (Claude Code, session 110), no `Co-Authored-By` per §7. Still-open
> housekeeping (unchanged from s109): older `done/` PLANs carry stale
> Status lines (per-PLAN verify, not a blind sweep); dev DB `vero_lite`
> behind on migrations (needs `alembic upgrade head` before a daemon run —
> host-state, ask Cray).

### Recent-Decisions row — 2026-07-07 (`main` greened — RF-1 library-guard 409 fix, session 105 #600) [rotated 2026-07-08, session-111 PLAN-0056-COMPLETE reconcile]

| 2026-07-07 | **`main` greened — RF-1 library-guard 409 regression fixed (session 105; #600)** — `main` was **CI-red since #595**, merged red through #596–#598 (2 tests in `tests/api/test_runs_endpoints.py`). Root cause: the ADR-016 S2 **RF-1 library guard** (`resolve_gated_step`, #595) fails closed when the resolved `principal` (`Person`) is `None`, and the **energy vertical authors no principals** → an authenticated caller (`person_id="op-somchai"`, `person=None`, the documented Phase-A contract) hit `GateApproverError → 409` on gate-resolve. **Fix (approach (a) — the guard is correct):** the 2 happy-path tests now provision a **real `Person` approver** (monkeypatch `auth._principal_index`, mirroring `test_api_auth.py`); energy production `procedures.yaml` deliberately **not** given a principals block (would arm vertical-wide membership enforcement — the OQ-6 N≥2 boundary). Reproduced the 409 on a fresh DB, then verified **234 passed** (api+db+verticals). `plan-drafter`-authored, Code R2 + committed | `4b7f472` (#600 fix) / `tests/api/test_runs_endpoints.py` (real-Person approver) / `services/engine/procedures/orchestrator.py` (RF-1 guard, #595 context) |

### Current-Focus block — Session 111 (2026-07-08, PLAN-0056 COMPLETE) [rotated 2026-07-08, session-112 PLAN-0057-COMPLETE reconcile]

> **Session 111, 2026-07-08 (head_commit `117e2d4` → `9fbc703`) —
> BUILD batch: PLAN-0056 **Phase B COMPLETE (Steps 6–8)** → the whole PLAN
> is **COMPLETE (all 12 ACs)** and moved to `docs/plans/done/`
> (#631/#632/#633/#634). The `event`/Alert-triggered governed run —
> ADR-0029's moat axis-(a) asset-event trigger + the procurement
> hero-demo's automatic opener — is now wired end-to-end behind a
> default-off ship-dark flag, LOUD-on-failure, with a procurement event
> demo. Three un-gated Code `feat` PRs + one `docs` close, each green
> through the required CI `gate`; MS-S1-independent.**
> **#631 (Step 6, feat `02f2af9`, merge `ab082f5`, AC-11) — recommender
> wiring behind the ship-dark flag.** `_populate_store`
> (`services/api/routers/actions.py`) now FEEDS an actionable recommendation
> INTO the governed engine in-process (ADR-0029 SD-1/SD-4) behind a
> **default-off `event_bridge_enabled`** flag (`services/api/config.py`,
> mirrors `verification_judge_enabled`; SD-P3 ship-dark). Flag-off = ZERO
> behavior change (resolver never loaded, fire branch never reached; the
> `ActionRecord` path intact). The one Step-6 design call resolved:
> `event_kind = RecommendedAction.suggested_handler` — the envelope has NO
> `action_type` (the Phase-A fact-vs-code correction); `entity_ids` =
> affected-entity PKs; `detected_at` = created_at. New `_load_event_bridge`
> + `_fire_event_for_record` helpers. 9 tests (both flag states + mapping
> via the persisted run's `trigger_context` + graceful no-fire paths).
> **#632 (Step 7, feat `1af7928`, merge `42a3a8f`, AC-10, ADR-0028 D4
> mirror) — LOUD-on-failure.** A dropped/failed event fire is now LOUD, not
> a silent drop: an `event_fire_missed` audit (unmapped kind — the reachable
> case) or `event_fire_failed` audit (a kind that maps but errors mid-flight)
> + a best-effort Telegram alert, then `None` so the read path never breaks.
> New `notify_event_fire_failed` + `build_event_fire_failed_message` +
> `_event_fire_gates_open` in `services/notify/telegram.py` with a SEPARATE
> cooldown anchor (mirrors `notify_schedule_missed`; no `llm_backend` gate —
> an ops event; no-PII body). Distinct from `event_skipped` (a healthy
> idempotent/in-flight skip). +9 tests.
> **#633 (Step 8, feat `f5b5c21`, merge `a45b1fa`, AC-12) — procurement
> event demo.** A DISTINCT `event_emergency_sourcing_round` (trigger: event;
> `event_trigger.event_kind: emergency_source`; `owning_person_id:
> req-planner` for SP-5 SoD) in `verticals/procurement/procedures.yaml` —
> same governed beat + `doa_tier` gate + SoD as the manual/scheduled hero,
> NOT a flip (trigger is a single enum). The archetype catalog map + GET
> /procedures gain the 7th procedure (AT-2). DB-backed MS-S1-free
> integration test (`tests/services/db/test_event_procurement_demo.py`): a
> detected asset-failure event → `build_event_resolver` → `fire_event`
> through the SHIPPED procurement executor factory → parks at the DOA gate
> (actor_kind:service, on_behalf_of req-planner) → `appr-pm` distinct
> approver resolves → COMPLETED. The live end-to-end smoke stays deferred
> (host-state, §8); the offline test is the gate.
> **#634 (docs `9fbc703`, merge `65d9039`) — PLAN-0056 COMPLETE, moved to
> `docs/plans/done/`.** All 12 ACs met (Phase A Steps 1–5 s110 + Phase B
> Steps 6–8 s111); Status Ready → Complete.
> **Verification:** full offline suite **2350 passed / 7 skipped**; ruff +
> mypy clean; every PR green through the required CI `gate`;
> MS-S1-independent. `main` **green + PROTECTED** (`65d9039`); 0 open PRs;
> `loop-dispatcher` **DISABLED**; MS-S1 idle; AI-assisted (Claude Code,
> session 111), no `Co-Authored-By` per §7. Still-open housekeeping
> (unchanged from s110): older `done/` PLANs carry stale Status lines
> (per-PLAN verify, not a blind sweep); dev DB `vero_lite` behind on
> migrations (needs `alembic upgrade head` before a daemon/operate run —
> host-state, ask Cray). No active PLAN; next-work candidates carry forward
> (s110 ranking): D = hero-demo backlog, C1 = whoami/reject-at-login —
> re-rank then Cray picks.

### Recent-Decisions row — ADR-0028 ACCEPTED (2026-07-07, session 105) [rotated 2026-07-08, session-112 PLAN-0057-COMPLETE reconcile]

| 2026-07-07 | **ADR-0028 ACCEPTED — procedure `schedule`-trigger scheduler (S1) architecture; "S2 before S1" now satisfied (session 105; #599)** — `plan-drafter`-authored, Code R2 + committed (ADR-009 D1/D2). Drafted Proposed (`5f3eec3`) → **Cray ratified all 3 surfaced decisions 2026-07-07** (`c9c0698`). Ratified S1 architecture: **SD-1 = a separate long-lived worker/daemon** · **SD-2 = `croniter` (thin, parse-only)** · **SD-3 = direct in-process `run_procedure_persisted`**. S1 is a **pure client** of the s104 S2 actor plumbing (PLAN-0053 Phase B). ADR decides **architecture only** — the build is a **follow-on S1 build-PLAN** (not yet drafted) that will lift the `manual`-only trigger block at `orchestrator.py:146-150` + correct ADR-016 OQ-2 §1192-1195. Selection came from the `next-work-analyst` ranking (Cray picked S1, ADR-first). ADR-0028 Accepted + merged; no active PLAN; `main` green; 0 open PRs; `loop-dispatcher` DISABLED; MS-S1 idle | `c9c0698` (ADR-0028 Accepted / ratify) / `5f3eec3` (ADR-0028 Proposed) / `docs/adr/0028-*.md` |

### Current-Focus block — Session 112 (head_commit `5abb1d9`) — PLAN-0057 event hero-opener COMPLETE [rotated 2026-07-08, session-113 reconcile; R1 64 KB ceiling]

> **Session 112, 2026-07-08 (head_commit `9fbc703` → `5abb1d9`) —
> BUILD + CLOSE batch: PLAN-0057 **COMPLETE (all 8 ACs, live-verified)** and
> moved to `docs/plans/done/` (#638/#639/#640/#641). The shipped ADR-0029 /
> PLAN-0056 event bridge is now made VISIBLE in the procurement hero-demo
> surface: a detected asset-failure event (`CNC-Line-07`) auto-fires
> `event_emergency_sourcing_round` via `fire_event` → parks at the `doa_tier`
> DOA gate → a distinct approver (`appr-pm`, SoD vs `req-planner`) → COMPLETED
> → the same governance-moment + ฿ ledger the manual opener draws, plus the
> beat-1 sense cue. Demo composition over shipped plumbing — NO new engine
> capability, NO new ADR, NO contract reshape. SD-1..SD-5 + OQ-1/OQ-2 ratified
> as-recommended (Cray, via AskUserQuestion); the live smoke was Cray-approved
> (host-state §8).**
> **#638 (Step 1 service projection + Step 5 test, merge `0020097`) —**
> `run_hero_event_governance_moment` + `build_event_hero_governance_audit` in
> `verticals/procurement/hero_demo/run.py`, plus the service-layer test
> `tests/services/db/test_event_hero_opener.py`.
> **#639 (Step 2 route + Step 4 client, merge `8aa71c1`) —** a new
> `POST /demo/hero/event` (`services/api/routers/demo.py`; SD-2 = a new POST,
> NOT a param on the read-only GET) + the `view-hero.js` manual↔event toggle +
> sense cue + `api.js` `Hero.event()` + a route smoke.
> **#640 (Step 3 reveal, merge `4524a29`, AC-2) —** the approve→COMPLETED
> reveal (`renderActPanel` in `view-hero.js`; client-side + Replay).
> **#641 (docs `5abb1d9`, merge `d33fff7`) —** `docs(plans): PLAN-0057
> COMPLETE` → `docs/plans/done/`; all 8 ACs met, Status Ready → Complete.
> **Earlier this session — #636 (merge `021efe2`, `docs(status):`)** reconciled
> the STALE Rock-3 Active-TODO: the "Q4 generic run-consume query executor" is
> NOT a future PLAN — it SHIPPED as PLAN-0048 (s96). The real remaining Q4
> residue = a join/projection-grammar ADR + the SD-4 factory PLAN (both undrafted).
> **Standing-fact change:** dev DB migrated `0009 → 0011` (Cray-approved
> `alembic upgrade head`, host-state §8) — the long-standing "dev DB behind on
> migrations" caveat is now **RESOLVED** (do not repeat it next session).
> **Verification:** every PR green through the required CI `gate`; PLAN-0057
> live-verified end-to-end (Cray-approved smoke, host-state §8); offline suite
> MS-S1-independent. `main` **green + PROTECTED** (`d33fff7`); 0 open PRs;
> `loop-dispatcher` **DISABLED**; MS-S1 idle; dev DB at head `0011`; AI-assisted
> (Claude Code, session 112), no `Co-Authored-By` per §7. No active PLAN;
> next-work candidates (s112 re-rank): C1 = whoami/reject-at-login (cheap,
> ratified-design), Q4 residue = join-grammar ADR (greenfield), hero-demo
> dossier backlog (greenfield) — re-rank when Cray picks.

### Recent-Decisions row — 2026-07-07 (PLAN-0055 Ready + main branch-protection ARMED, session 106) [rotated 2026-07-08, session-113 reconcile]

| 2026-07-07 | **PLAN-0055 Ready + `main` branch-protection ARMED (session 106; #602 + repo-config)** — **(1) Repo-config (NOT a commit):** `main` was found **completely unprotected** (no classic protection, no rulesets, no rules — contradicting CLAUDE.md §7). Applied Cray-authorized (§8 go): **require-PR + require the `gate` status check + `enforce_admins` + no force-push / no branch-deletion** — closes the merged-red hole that let #595's RF-1 regression stay red through #596–#598 (s105 finding). Every PR this session merged through the now-required `gate`. **(2) PLAN-0055 (S1 schedule-trigger scheduler BUILD) Ready (#602 merge `22daea3`):** `plan-drafter`-authored (`a1058c4` add → `3bec1f0` Draft→Ready), Code R2 + committed. Cray ratified **all six SD-P1..P6 as-rec:** SD-P1 cron/tz = `Asia/Bangkok` + IANA tz per schedule · SD-P2 skip-missed-with-audit · SD-P3 skip-if-in-flight · SD-P4 at-most-once · SD-P5 dedicated schedule-state table + restart recovery · SD-P6 `trigger_context` stamp → Ready for execution. Phased: Phase A (offline-testable) + Phase B (long-lived daemon). Implements Accepted ADR-0028 | `22daea3` (#602 merge) / `3bec1f0` (Draft→Ready) / `a1058c4` (PLAN add) / `docs/plans/0055-*.md` + GitHub branch-protection on `main` |

### Current-Focus block — Session 113, 2026-07-08 (head_commit `5abb1d9` → `a3b7113`) — PLAN-0058 whoami/reject-at-login COMPLETE [rotated 2026-07-08, session-114 reconcile]

> **Session 113, 2026-07-08 (head_commit `5abb1d9` → `a3b7113`) —
> BUILD + CLOSE batch: PLAN-0058 **COMPLETE (all 5 ACs)** and moved to
> `docs/plans/done/` (#645/#646/#647). A thin **`GET /whoami`** echo over the
> already-shipped fail-closed auth seam (`get_current_principal`) + the frontend
> `login()` probing it, so a **bad key is rejected AT login** instead of only on
> the first operate POST. Executes the ratified **PLAN-0054 SD-A tail** (the
> "who am I" read named as a designed-into-seams sequel) — **NO new ADR, NO new
> auth backend, NO change to the seam's validation logic.** Fully offline /
> deterministic / MS-S1-independent. Origin: s113 `next-work-analyst` re-rank
> (grounded 4-agent fan-out) → Cray picked **C1 (whoami)**, the cheap
> ratified-design front-runner — now SHIPPED.**
> **#645 (`docs(plans):` PLAN-0058 Ready, feat `847a0bb` / merge `1734187`) —**
> `plan-drafter`-authored; Code R2-verified every code citation; **SD-1..SD-4
> ratified as-recommended** (Cray, via AskUserQuestion): SD-1 minimal shape
> `{person_id, display_name, auth_enabled}`, SD-2 fail-closed (reuse
> `Depends(get_current_principal)`), SD-3 include the frontend wiring, SD-4
> deterministic API tests only.
> **#646 (`feat(api):` Steps 1-3, feat `8eaacd1` / merge `fa0a187`) —** Step 1:
> `services/api/models/whoami.py` (`WhoamiResponse`) + `services/api/routers/whoami.py`
> (`GET /whoami`, injects the shared `Depends(get_current_principal)`) + registered
> in `main.py`. Step 2: `tests/api/test_whoami.py`, 6 deterministic cases (200
> valid + display_name resolved / 200 no-principals → null / 401 no-header / 401
> unknown key / 403 unmapped person / dev-escape → 200 person_id null +
> auth_enabled false). Step 3: async `login()` probes `/whoami` (`auth.js`) →
> reject-at-login; `doLogin` made promise-aware (`view-monitor.js`); stale comment
> fixed; `index.html` `?v=` bumped (auth.js c29→c33, view-monitor.js c30→c33).
> **#647 (`docs(plans):` `cd32b02` / merge `a3b7113`) —** PLAN-0058 Status Ready →
> Complete, `git mv` → `docs/plans/done/`; all 5 ACs met.
> **Parallel session (not mine) — #644 (`fb523f3` / merge `3675403`,
> `chore(agents):`)** pinned the `plan-drafter` subagent to fable + xhigh effort
> (harness config, unrelated).
> **Verification:** offline binding bar green — **full suite 2359 passed / 7
> skipped**; ruff + mypy clean; every PR green through the required CI `gate`.
> Preview-verified on `oct-demo-procurement` (`API_AUTH_ENABLED=true`): a bad key
> → inline "unknown API key" with NO session stored (reject-at-login end-to-end);
> a 200 → session stored; no JS console errors. `main` **green + PROTECTED**
> (`a3b7113`); 0 open PRs; `loop-dispatcher` **DISABLED**; MS-S1 idle; dev DB at
> head `0011` (unchanged this session); AI-assisted (Claude Code, session 113), no
> `Co-Authored-By` per §7. No active PLAN; next-work candidates (re-rank when Cray
> picks): KPI panel (hero-demo dossier — cheap demo-composition over the shipped
> `/demo/hero/impact` ledger, greenfield PLAN); Q4 residue (join-grammar ADR +
> SD-4 factory PLAN, greenfield/needs-ADR, heavy); hero-demo dossier backlog.
> Event-bridge live smoke = deferred host-state evidence.

### Recent-Decisions row — 2026-07-07 (Lessons #0028 + #0029, session 106) [rotated 2026-07-08, session-114 reconcile]

| 2026-07-07 | **Lessons #0028 + #0029 landed (session 106; #603)** — Code-authored advisory Tier-2 (un-gated). **#0028** = omit-when-None to evolve an append-only hash-chained audit log without an epoch boundary (grounds `services/db/audit_log.py::compute_row_hash`, from the s104 ADR-016 S2 arc). **#0029** = a named-subset "green" is not a full-suite green + make CI required (the s105 #600 root-cause: s104's "52 db + 489 proc green" excluded `tests/api/` where the #595 RF-1 regression lived) | `d7094bb` (#603) / `docs/lessons/0028-*.md` + `docs/lessons/0029-*.md` |

### Current-Focus block — Session 114, 2026-07-08 (head_commit `a3b7113` → `1de4d14`) — event-bridge live-smoke FINDING + PLAN-0059 KPI panel COMPLETE [rotated 2026-07-09, session-115 reconcile]

> **Session 114, 2026-07-08 (head_commit `a3b7113` → `1de4d14`; merge tip
> `ab02dfd`) — FINDING + BUILD + CLOSE batch, two items in the order Cray
> directed (B → A).**
> **(B) Event-bridge live smoke → FINDING (evidence-only, §8 host-state,
> #649).** The deferred smoke asked whether the REAL MS-S1 recommender
> (`gpt-oss:20b`) chooses `emergency_source` for a procurement
> critical-asset-failure event. It chose **`reorder`** — `actor_kind=llm` (the
> real model engaged, **NOT** the rule fallback), confidence 1.0. Root cause
> (offline trace): the reactive judgment prompt shows the model **bare handler
> NAMES only** — no per-handler descriptions, no when-to-pick guidance,
> `goal=None`; the distinguishing prose lives only in `procedures.yaml` step
> descriptions + the procedure goal, which thread into the GOVERNED path, not
> the reactive prompt. **The governed procedure path and the shipped hero demo
> (deterministic advisory stub) are UNAFFECTED**; the offline gates
> (`test_action_event_bridge.py`, `test_event_procurement_demo.py`) stay the
> binding bar and green. Recorded in
> `docs/logs/2026-07-08-event-bridge-recommender-live-smoke.md` (#649). The
> cross-vertical fix — surface per-handler descriptions in the reactive
> judgment prompt — is a **DEFERRED** next-work candidate (own PLAN, blast
> radius across all verticals, then one controlled live re-validate).
> **(A) PLAN-0059 KPI stat-tile panel COMPLETE (all 5 ACs) → moved to
> `docs/plans/done/` (#650/#651/#652).** The hero demo's three headline
> ฿-impact figures — expedite premium `฿52,500` / avoided downtime `฿8.16M` /
> net benefit `฿8.11M` — now render as **KPI stat-tiles** over the
> already-shipped `GET /demo/hero/impact` ledger, with the baseline→governed
> exposure (`฿9.76M → ฿1.65M`) as a context sublabel on the net-benefit tile;
> the old `kv()` rows are replaced (no duplication); no trend/target
> affordances. **Pure frontend composition — NO new ADR / backend / engine /
> payload change** (the PLAN-0057 "compose over shipped plumbing" pattern,
> render-only). Origin: session-114 `next-work-analyst` re-rank → Cray picked
> **B → A**.
> **#649 (`docs(logs):` `f528f03`) —** the B event-bridge live-smoke finding
> recorded as evidence-only (§8 host-state; no code change).
> **#650 (`docs(plans):` `cffa9d1`) —** PLAN-0059 Ready; `plan-drafter`-authored;
> Code R2-verified every citation + confirmed the `thb`/`thbM` formatters
> produce the pre-committed strings; **SD-1..SD-5 ratified as-recommended**
> (Cray, session 114, AskUserQuestion).
> **#651 (`feat:` `e8a7d93`) —** Steps 1-3; diff confined to
> `services/api/static/**`; full offline suite green under the required CI
> `gate`; preview-verified on the hero view.
> **#652 (`docs(plans):` `1de4d14`) —** PLAN-0059 Status Ready → Complete,
> `git mv` → `docs/plans/done/`; all 5 ACs met.
> **Verification:** offline binding bar green (full offline suite green under
> the required CI `gate`; every PR green); preview-verified on the hero view —
> KPI stat-tiles render the pre-committed ฿ strings, the old `kv()` rows are
> gone, no duplication. `main` **green + PROTECTED** (substantive tip
> `1de4d14`; merge tip `ab02dfd`); 0 open PRs after merge; `loop-dispatcher`
> **DISABLED**; MS-S1 idle (the B smoke ran host-state, Cray-approved §8, then
> released); dev DB at head `0011` (unchanged this session); AI-assisted
> (Claude Code, session 114), no `Co-Authored-By` per §7. No active PLAN;
> next-work candidates: recommender handler-description fix (deferred this
> session; own PLAN, cross-vertical blast radius); Q4 join/projection-grammar
> ADR (heavy moat, needs-ADR); hero-demo dossier backlog; filing-hygiene —
> PLAN-0019/0027 misfiled in active `docs/plans/` (cheap cleanup).

### Recent-Decisions row — 2026-07-07 (PLAN-0055 S1 Step 1 `SCHEDULE` trigger, session 106) [rotated 2026-07-09, session-115 reconcile]

| 2026-07-07 | **S1 Step 1 BUILT (PLAN-0055 Phase A) — `SCHEDULE` trigger admitted to `validate_runnable`, all other governance intact (session 106; #604)** — `feat(procedures)`: `validate_runnable` gains an explicit `_RUNNABLE_TRIGGERS` allowlist ({MANUAL, SCHEDULE}); the trigger check sits first so **every OTHER governance check** (skeleton-reject / step-kind / autonomy-ceiling / handler-allowlist / linear-input) is **unchanged and still fires** for a schedule proc (surgical lift). Corrected 4 stale texts (block message + `validate_runnable` docstring in `orchestrator.py`, the `Trigger` enum docstring in `spec.py`, a test comment) + **ADR-016 OQ-2 (:1192-1195) marked RESOLVED (ADR-0028)** — a `plan-drafter`-authored erratum (G1-exempt; Code's own Edit correctly G1-denied), Cray **per-diff approved verbatim**. AC-1 (`test_schedule_trigger_is_runnable`) + AC-2 (`test_schedule_trigger_still_enforces_governance`). **Full suite 2240 passed / 7 skipped**; ruff + mypy clean | `255ca96` (#604 feat) / `ec5822b` (#604 merge) / `services/engine/procedures/orchestrator.py` (`_RUNNABLE_TRIGGERS`) + `services/engine/procedures/spec.py` (`Trigger` docstring) + `docs/adr/0016-*.md` (OQ-2 RESOLVED) |

### Recent-Decisions row — 2026-07-07 (PLAN-0055 S1 Steps 2–5, session 107) [rotated 2026-07-09, session-115 reconcile (ADR-016 Q4 amendment)]

| 2026-07-07 | **S1 Steps 2–5 BUILT (PLAN-0055) — Phase A COMPLETE + Phase B daemon scaffold (session 107; #606 + #607 + #609 + #610)** — four un-gated Code `feat` PRs executed directly (PLAN-0055 already Ready; §6 "Steps 2–8 execute directly"), all green through the required `gate`. **Step 2 (#606, SD-P1 + SD-P5):** (1) a typed `Schedule` descriptor (cron + per-schedule IANA `timezone`, `extra="forbid"`) on `Procedure`, **present IFF `trigger==schedule`** — a symmetric fail-loud-at-load invariant [**Code decision, Cray veto-open:** required-iff-schedule, house fail-loud style; blast radius test-only]; (2) a dedicated `schedule_states` table (new ORM `schedules.py` + Alembic 0011, `(vertical, procedure_id)` unique, holds `last_fired`/`next_fire` for restart recovery; additive, **outside the energy parity guard**). **2254/7.** **Step 3 (#607, SD-2 + AC-10):** `croniter>=2.0.0` prod dep (6.2.3) + `types-croniter` (dev + mypy hook) + `uv.lock`; a DB-free `cron.py::next_fire(cron, tz, after)` — wall-clock in per-schedule IANA tz (SD-P1), exclusive of `after`, croniter authoritative parser; tests incl the TH-tz AC-10 case (06:00 `Asia/Bangkok` == 23:00 UTC prev day). **2261/7.** **Step 4 (#609, Phase A LAST step, SD-P2/P3/P4/P6; built by a CONCURRENT executor session, verified on-disk here):** the pure DB-free `scheduler.py::fire_due_schedules(session, schedules, *, now, resolve, next_fire_fn)` (injected `now`) — INITIALIZED / NOT_DUE / SD-P3 skip-if-in-flight (`schedule_skipped` audit) / else fire-once (SD-P4) with a `schedule_missed` no-backfill audit (SD-P2) + `trigger_context` stamp (SD-P6); `run_id=<schedule_id>@<scheduled_for>` per-slot key (Step-6 AC-7 foundation); AC-4/AC-5 inherited from `run_procedure_persisted`. **2269/7.** **Step 5 (#610, Phase B BEGINS, SD-1 + AC-11):** the long-lived `scheduler_daemon.py::SchedulerDaemon` run loop (ticks `fire_due_schedules` every `interval_seconds`, NO scheduling logic of its own) with graceful SIGTERM/SIGINT/`request_stop()` shutdown (finish the tick then exit; no torn writes) + tick-error logged & swallowed; INJECTED collaborators (MS-S1-independent); `run_scheduler_daemon` entrypoint; first use of the `structlog` dep. **Full suite 2274 passed / 7 skipped**; ruff + mypy clean. Phase A = trigger-lift[s106] + descriptor + state + parser + fire-fn (4 of 4) | `43d40dd` (#610 Step 5 feat) / `0d2414b` (#610 merge) / `5077d6d` (#609 Step 4 feat) / `369ee73` (#609 merge) / `ef91ea7` (#607 Step 3 feat) / `e58e7af` (#607 merge) / `3938191` (#606 Step 2 feat) / `ed87153` (#606 merge) / `services/engine/procedures/{spec.py (`Schedule` invariant), schedules.py (`schedule_states` ORM), cron.py (`next_fire`), scheduler.py (`fire_due_schedules`), scheduler_daemon.py (`SchedulerDaemon`)}` + `alembic/versions/0011_schedule_states.py` + `alembic/env.py` + `pyproject.toml`/`uv.lock` (`croniter` + `types-croniter` + `structlog`) + `tests/services/engine/procedures/{test_spec.py,test_orchestrator.py,test_cron.py,test_scheduler.py,test_scheduler_daemon.py}` + `tests/services/db/test_schedule_state.py` |

### Recent-Decisions row — 2026-07-07 (PLAN-0055 S1 Steps 6–7, session 108) [rotated 2026-07-09, session-115 3rd-batch reconcile (PLAN-0061 COMPLETE)]

| 2026-07-07 | **S1 Steps 6–7 BUILT (PLAN-0055 Phase B) — restart-recovery idempotency guard + missed-round LOUDness + deploy CLI/registration (session 108; #612 + #614 + #615)** — three un-gated Code `feat` PRs executed directly (PLAN-0055 Ready; §6 "Steps 2–8 execute directly"), each green through the required `gate`. **Step 6 (#612, SD-P5 + AC-7):** `fire_due_schedules` computes the per-slot `run_id=<schedule_id>@<scheduled_for>` (the `pipeline_runs` PK, write-ahead-committed before any effect → the row exists iff the slot durably fired) early and checks a new `_run_exists(run_id)` **AHEAD of the SD-P3 in-flight check** so a `completed` prior run is caught too (not only `running`, which `_in_flight` misses) → skip the re-fire, advance the clock, emit `schedule_skipped {reason:already_fired}`, return the new `FireResult.ALREADY_FIRED`; daemon `tick()` logs `scheduler.already_fired` + a `recovered` count. **2276/7.** **Step 7a (#614, AC-8):** missed-round LOUDness — daemon `tick()` emits a WARN `scheduler.missed_round` for any FIRED `missed=True` + a best-effort Telegram ping (INJECTED notifier, `suppress()`-wrapped so an alert failure never tears a tick); new `notify_schedule_missed` reuses the best-effort POST/cooldown/never-raise core (`_post_telegram` extraction; `notify_llm_unreachable` unchanged) with a **DISTINCT gate** (flag + token + chat_id, **no `llm_backend`** — a missed round is a clock/ops event) + a **SEPARATE cooldown anchor**; no-PII. **2285/7.** **Step 7b (#615):** REAL vertical-spec → fire-fn/daemon wiring + closes the **registration gap** — new `scheduler_wiring.py::sync_schedule_states` (upsert one `ScheduleState` per `schedule`-trigger procedure keyed `<vertical>:<procedure_id>`, **idempotent**; spec owns cron/tz, daemon owns the preserved live clock; a cron change drops stale `next_fire`) + `build_resolver` (REAL `ScheduleState→ScheduledRun`, `ServicePrincipal` lookup SP-4, fail-loud `SchedulerWiringError`) + a `vero-lite scheduler --vertical` CLI + `docs/runbooks/scheduler-daemon.md`. **Full suite 2294/7**; ruff + mypy clean. NOTE: no vertical ships a `schedule`-trigger procedure yet — the Step 8 procurement demo authors one (daemon ticks + syncs 0 until then). MS-S1-independent | `934eb58` (#615 Step 7b feat) / `84e6511` (#615 merge) / `1939a5f` (#614 Step 7a feat) / `7eeb40d` (#614 merge) / `801aebe` (#612 Step 6 feat) / `8c6e270` (#612 merge) / `services/engine/procedures/scheduler.py` (`_run_exists` + `FireResult.ALREADY_FIRED`) + `services/engine/procedures/scheduler_daemon.py` (`already_fired`/`recovered` + `scheduler.missed_round`) + `services/notify/telegram.py` (`notify_schedule_missed` + `_post_telegram`) + `services/engine/procedures/scheduler_wiring.py` (`sync_schedule_states` + `build_resolver`) + `vero-lite scheduler` CLI + `docs/runbooks/scheduler-daemon.md` + `tests/services/db/{test_scheduler.py,test_scheduler_daemon.py,test_scheduler_wiring.py}` + `tests/services/notify/test_telegram.py` |
| 2026-07-07 | **S1 Step 8 BUILT (PLAN-0055) — first `schedule`-trigger procedure on a REAL vertical (procurement) end-to-end + LIVE daemon demo; PLAN-0055 FULLY COMPLETE (Steps 1–8), moved to `docs/plans/done/` (session 109; #617 + #618)** — two un-gated Code PRs executed directly (PLAN-0055 Ready; §6 "Steps 2–8 execute directly"), each green through the required `gate`. **Step 8 offline (#617, feat):** a new `scheduled_emergency_sourcing_round` procedure in `verticals/procurement/procedures.yaml` (AT-2, `trigger: schedule`, cron `0 6 * * *` Asia/Bangkok) + a new **`svc-buyer` ServicePrincipal** + `procurement_agent.service_principal_ids`; surfaced + fixed two integration gotchas the in-memory Step-7b tests missed: (1) `doa_tier`⟹SoD (ADR-0025 D5) collides with headless scheduling (a headless `{intake:None}` fails the principal-SoD run-check CLOSED at gate resolution) → Cray-ratified "Path X" = a new **`Schedule.owning_person_id`** (SP-5): fire as `svc-buyer` **ON BEHALF OF** `req-planner` so a distinct DOA approver (`appr-pm`, ฿288k tier) governs — `build_resolver` resolves + binds it (lifting the Step-7b hard-coded `owning_person=None`), `spec._cross_refs` validates; (2) a **latent Decimal→JSONB** seed in the procurement executor factory (a daemon-fired fresh run re-runs `intake` live so the raw Decimal persists → JSONB error; the HTTP resolve path never re-ran intake so it stayed latent) sanitised + a roster reconciliation (the factory resolves `doa_tier` against the spec's authored principals, not the Fastenal CSV roster). New DB-backed `tests/services/db/test_scheduled_procurement_demo.py`; archetype catalog + `/procedures` = six shipped procedures. **2296/7.** **Step 8 fix (#618, fix; surfaced by the LIVE daemon smoke):** `vero-lite scheduler --vertical procurement` fired but FAILED at the `source` action — `_run_scheduler` registered the executor factory but not the vertical's action handlers → it now calls **`discover_and_register()`** before firing (the API lifespan already did; the daemon CLI had skipped it); the integration fixture switched to the daemon's real registration path to guard the regression. **LIVE demo (host-state, MS-S1-free, disposable DB):** the fixed daemon fired on a real wall clock (as `svc-buyer` on behalf of `req-planner`) → parked at the ฿288k DOA gate (ผจก.จัดซื้อ → appr-pm) → `POST /runs/{id}/gate/resolve` as **appr-pm** → **completed**; audit actor_kind:service + on_behalf_of req-planner + SoD-governed (requester ≠ approver); demo DB dropped, dev DB + MS-S1 untouched. **Full suite green**; ruff + mypy clean. **PLAN-0055 FULLY COMPLETE (Steps 1–8) → `docs/plans/done/`.** MS-S1-independent | `2051bc1` (#618 fix) / `da8ba03` (#618 merge) / `6335bd6` (#617 feat) / `38dfccf` (#617 merge) / `verticals/procurement/procedures.yaml` (`scheduled_emergency_sourcing_round` + `svc-buyer`) + `services/engine/procedures/spec.py` (`Schedule.owning_person_id`) + `services/engine/procedures/scheduler_wiring.py` (`build_resolver` binds owning_person) + `tests/services/db/test_scheduled_procurement_demo.py` + `docs/plans/done/0055-*.md` |


---
## Rotated 2026-07-10 (session-117 DEEP-ROTATE, Cray-ratified)

Removed from  to reclaim byte headroom under the R1 65,536 ceiling (64,258 B -> 52,232 B). Nothing is lost: the full text lives here.

### In-Flight Discussions -- two entries compressed to one-line pointers in STATUS

- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13 (ratified `4d1347b`, #302; committed Proposed `e25281d`, #297 + instruction `e387a63`, #298 + R1 errata `655344d`, #300) — guarded trial under observation (parallel to ADR-012). A specialist Cowork project role-plays a Thai operator and emits a "partner profile package" to rehearse the intake+PDPA pipeline before a real partner; venue OUTSIDE the governance tiers (no commits / no repo mount / enters via Code receive). Three BINDING anti-circularity rules R1/R2/R3 (R3 SYNTHETIC provenance → never trips PLAN-0005 §8.1 / ADR-011 first-real-data trigger). All four venue SDs + dispatch-SD-1 ratified per Cowork rec (SD-1 N=3; SD-2 one-project-per-business-type; SD-3 size/region/maturity enums w/ energy·mid·th-regional·mixed-legacy default; SD-4 "what we refused to share" now required). D4 guarded-trial mirrors ADR-012 D5; regression triggers R-PS1..R-PS4 are the exit criteria; run 1 = energy operator (ADR-005 primary). **RUN 1 (energy / mid / th-regional / mixed-legacy) COMPLETE 2026-07-02 (session 93):** synthetic partner profile package (fictional TWP operator) received via Cray relay + Code-screened **S-1..S-5 ALL PASS** against a **pre-committed** oracle (R1 no schema echo · R2 six unsolicited inconvenient facts + heavy data flaws · R3 SYNTHETIC banner intact · SD-4 refused-to-share present); no R-PS trigger fired. Landed (gitignored, R3): package `docs/research/private/2026-07-02-partnersim-run1-energy-package.md` + oracle/verdicts `...-run1-receive-checklist.md` + completion handoff (session-93). First-pass value: **8 schema-mismatch findings** for the intake/mapping/PDPA path (unstable asset PKs, unresolvable principal identity vs ADR-0026 SoD + the worker-committee PDPA angle, multi-unit columns vs ADR-0021, per-source TZ chaos, action-events-in-status + seasonal thresholds vs in_file_band, mutable history, residency = our on-prem fit, DPA 4–6-wk timeline). **ADR-0020 D4 post-run-1 review DONE 2026-07-02 (s94): verdict continue-with-adjustments (no R-PS trigger fired; C-1..C-3 confirmed; #516 R1-tighten + stripped paste-variant landed; run-2 preconditions recorded — re-paste instruction to UI, fresh project per SD-2, unannotated bulk ask, persona fix). RUN 2 (supply-chain / mid / multi-site-sea / mixed-legacy) COMPLETE 2026-07-02 (s94): fresh project + all 3 D4 adjustments; S-1..S-6 ALL PASS pre-committed (first live R-PS4 screen clean); cross-run signal — identity/PK/clock/bottleneck/batch-only recur in 2/2 verticals (mapping-layer core, not energy quirks); new classes: cross-border-already-in-flight, duration-qualified + per-contract bands, per-device calibration, GPS-as-PII column-drop. C-1..C-3 (new project) carried open. RUN-2 REHEARSAL done 2026-07-03 (s94 cont.): G1–G11 (headline: supply_chain_v0 lacks an equipment entity + measured_kind; 4 new band-gap classes; cross-border DPA musts; GTM templates now customer-demanded); §5 cross-run synthesis = 9 classes recur 2/2 verticals (mapping-layer core; Rule-of-Three holds — no abstraction yet). C-1..C-3 input-state check CONFIRMED 2026-07-03 (Cray Path-1 UI: no repo mount, post-#516 instructions, no past-chats) — run-2 open item CLOSED; the trial has no open partner-sim debt. ADR-011 audit framework stays gated on a REAL partner conversation — the synthetic run INFORMS but never TRIGGERS it (R3).**

- **Procurement vertical — GO + IN MOTION: PLAN-0036 (Fastenal, Stage 1) drafted + merged Draft (#412, `7a7c036`):** **GO** — Cray greenlit the 4th vertical (Procurement) and **PLAN-0036 (Fastenal procurement vertical, Stage 1) is drafted + merged Draft** (#412, head_commit `7a7c036`; Cowork-D1 + Code-R2 + committed D2, session 75). **Cray adjudicated SD-1…SD-5 = confirm-all** (2026-06-24, as-recommended). **Demo target = Fastenal Thailand** — automotive/auto-parts in the EEC; **hero** = asset-failure → governed emergency sourcing, **calm-path** = low-stock reorder. Stage 1 = a **PLAN-only, no-ADR pure-config plugin** on the shipped ADR-016 engine, **zero `services/` core edit** (CQ-1 confirmed, ADR-0023); the **SD-4 catch** = `services/engine/procedures/spec.py` `Step = ConfigDict(extra="forbid")` → Stage-1 facet annotations are **comment-only** (a first-class `facet` field = a Stage-2 ADR-016 amendment). It is the **proving ground** for the ultimate **3-phase generative-procedure platform** (generate / run / monitor); per Rule-of-Three it builds **no generic generator** (hand-author → extract schema Stage 2 → generator Stage 3). **NEXT = a new session flips PLAN-0036 Draft → Ready for execution (SDs confirm-all) then executes Stage 1.** *Supporting de-risk dossier (Cowork, session 72, 2026-06-22, `docs/research/private/`)* — **(1)** `2026-06-22-procurement-spec-expressiveness-probe.md` (procurement is **config-layer**, **0 new core amendments**; only engine pulls are the already-deferred ADR-016 Phase 2 / Phase 4+ items); **(2)** `2026-06-22-procurement-gtm-commercial-validation.md` (wedge = ops-triggered asset-aware procurement; econ buyer = CFO/Controller, champion = ops/procurement mgr; metric = **cycle-time**; ~$40K–150K/yr; 6-wk paid pilot); **(3)** `2026-06-22-procurement-asset-aware-incumbent-scan.md` (de-risk #1 — EAM/CMMS = nearest incumbent on the *trigger* only; white space = the **triple intersection** asset-trigger × governed sourcing × cross-vertical); **(4)** `2026-06-22-ai-sourcing-competitor-teardown.md` (de-risk #2 — Verusen/Keelvar/Fairmarkit/Arkestro/… triple intersection unoccupied; defensibility on **axis (a) asset-event trigger**; watchlist: **Verusen #1**, Fairmarkit, Coupa); **(5)** `2026-06-22-platform-incumbent-deepdive.md` (de-risk #3 — Palantir/Maximo/GE Vernova/SAP = capability-yes / product-no; moat = **packaging × ICP × price** = the **"Palantir-lite"** thesis, ADR-005, **governed ≠ generated**). **Pitch:** lead with asset-ontology-triggered governed sourcing + the native ontology (ADR-008) + engine (ADR-016) combination — **NOT** "governed"/"cross-vertical" (now commoditized claims).

### Active TODOs -- eight COMPLETE + CLOSED items (Tier-3 archeology per CLAUDE.md §4)

- [x] **PLAN-0041 (classify-prompt enrichment lever — Rock 1) — COMPLETE (s87, offline gate #475/#476 + live AC-7 PASS, moat byte-identical).** The prompt-only fix for the s83 AC-B5 ~1-in-3 false-abstain: offline gate (#475 Steps 1-3 + #476 Step 4) + the Cray-gated live before/after on MS-S1 `gpt-oss:20b` (Arm A 8→11/11 all reps; Arm B 11/11 abstain; label_abstain 33/33, step_disagreement 0); the AT-2 cross-check stayed byte-identical, no schema change, no new ADR; the offline gate is the binding bar, live = confirming. PLAN `git mv` → `done/`. *(Cowork-D1 → Code-R2 → Cray-ratified → committed #461; executed Steps 1-5 Code-direct s87)*

- [x] **PLAN-0051 (reason-then-structure A/B — Wave-2(c)) — COMPLETE + CLOSED (s99, #565–#570).** Operationalized July-2026 research finding #2 (reason-then-structure lifts constrained-decoding accuracy 10-30%) as a **3-arm A/B** (`baseline` / `field_order_flip` / `two_pass`) on the two remaining single-pass structured-output call sites — **classify** (`classify_narrative`) + **nl_query** (`_translate`); anomaly recommender out of scope (already two-pass Pattern B). Plumbing (#566/#569, byte-identical `baseline` default) + 2 A/B corpora (classify reuses PLAN-0041's 26-narrative set #567; nl_query 27 hand-authored gold Qs #568) + skip-by-default A/B harness (#570). **Live run (Step 5b, host-state §8, Cray go, N=3 both sites, 2:17:02 on `gpt-oss:20b`): NO measurable lift** — classify baseline at the 11/11 ceiling (flip +0, two_pass −1; Arm-B moat brake held 11/11 every arm/rep); nl_query worst-rep mean 0.978 baseline vs 0.965–0.978 variants (hard-class Δ +0.000). **SD-6 = REJECT both variants, keep `baseline`; NO production default changed; NO new ADR (SD-5).** The research "10-30% lift" did NOT replicate (both paths already strongly prompted; `gpt-oss:20b` extracts structure well) — a **valid null result**; the plumbing + corpora + harness remain reusable scaffolding behind the `baseline`-default `arm` param. Offline AC-1..AC-5 (binding bar) MET; AC-6/AC-7 (live) confirming. Full record `docs/logs/2026-07-05-plan0051-live-ab-results.md`; PLAN → `done/0051-*.md`. *(s99; plan-drafter drafted → Cray ratified SD-1..SD-6 as-rec → Code R2+commit+live-run; `loop-dispatcher` DISABLED; MS-S1 idle)*

- [x] **ADR-0027 R2 build → PLAN-0050 (the semantic-enrichment-fields follow-up) — COMPLETE + CLOSED (s98, #553–#563).** The 4 OPTIONAL constructs (synonyms th/en · sample_values · verified_queries · metric grain/join_path) BUILT end-to-end (8 steps / 8 ACs): L1 `ontology_schema.json` (#555) + Pydantic projection `ontology_meta.py` typed `Synonyms`/`VerifiedQuery` + optional attrs on PropertyMeta/ObjectTypeMeta/QuantityBinding (#556) + L2 `_check_enrichment` validators (#557, SD-C samples ⊆ enum, SD-5 join_path) + D2 backward-compat GATE (#558, byte-identical/git-clean) + energy-v1 (#559) + supply-chain-v1 (#560) backfills + the emitter fix (#562). **Disclosed deviation:** the "shipped R1 emitter consumes it for free" premise was WRONG — the shipped emitter didn't read the fields; surfaced as ADR-0027 erratum #561 → Cray-authorized emitter change #562 (IN-1 escape hatch, gap surfaced not silently patched). PLAN → `done/0050-ontology-semantic-enrichment-build.md` (#563). Backward-compat HARD INVARIANT held; governed≠generated; no Alembic migration; ~+15 tests, CI-green per PR. *(s98; ADR-0027; drafted→ratified→built→closed; plan-drafter drafted → Code R2+commit → Cray ratified; pairs with Rock-3 Box-4 residue below)*

- [x] **Rock 2 / O-3 — AT-2 / managerial layer — ADR-0025 ACCEPTED (#463, s84) + follow-on build PLAN COMPLETE (PLAN-0042, s86).** The Box-3 "Action = contract" layer (DOA/SoD/scored-rule/compliance). **ADR-0025 (Accepted)** decided: type AT-2 content (D2 authoritative discriminated `Step.governance_content` keyed to `gate_kind`, not the facet), bypass structurally unrepresentable (D3), **close the live run-gate AT-2-blindness defect** (D5), **defer the generator** under a CI-enforced N≥2 re-trigger (D7; AT-2 = N=1). **The follow-on build PLAN = PLAN-0042, which shipped + closed in session 86** (`a958e6b` git-mv → `done/`, "#470/#471/#472"): procurement `procedures.yaml` now carries 4 typed `governance_content`/`separation_of_duties` blocks; `draft.py::derive_governance_todo` handles all 3 AT-2 gate kinds. **Superseded** by newer work (this line was a STATUS TODO not reconciled since s84 — classify *not* an error). **Residual Rock-2 remainder:** only the deferred OQ-3 run-executor + the N≥3 Box-4 facet. *(s84 ADR-0025; PLAN-0042 built+closed s86; [[project_vero_ultimate_target_generative_procedures]])*

- [x] **A1 — verify+reshape governance demo (B-γ moat successor) — DONE (s74).** The heaviest moat-proof: prove the moat IS governance — verify an LLM step's output for semantic consistency + reshape to the next step's contract (what arm (c) structurally lacks; ADR-016 area; the B-3 REPORT forward-points to it). **Scope together with the Phase-2 governed-entity-resolution ADR** — one ADR-016-area construct, not two overlapping ADRs. **UPDATE (s71):** that consolidation is DONE — **ADR-0022 (Accepted) D3-α already houses verify+reshape as member (b)**, so A1 = a PLAN to build member (b) (like PLAN-0030 built member (a)), at most an ADR-0022 amendment if a member-(b) design fork surfaces — NOT a new ADR. A2's residual decomposition (s71) shows the concrete A1 target: the 5 correct-action "assessment-prose" cases (verify the proposal states the action, reshape from the resolved handler). Sequenced AFTER the G2 root-fix (Cray, s71). **UPDATE (s73, cont.):** advanced END-TO-END — **SD-1 adjudicated = (c) Hybrid, phased** (Cray); **Phase 1 floor SHIPPED** (#403 `1c34125` — `services/engine/action_verification.py` at the `_compose_llm_record` seam; 1629 passed/22 skipped; AC-5 wrong-handler-not-rescued + D-6 held); the **(c) hybrid governance RATIFIED** (#404 ADR-0022 amendment [member (b) = hybrid, 7 constraints, local-LLM pin, scope = mechanism-only] + PLAN-0035 revision [Phase 1/2 restructure]; #405 `3625ea4` amendment ratified, SD-A1 = (i) inline). **UPDATE (s74) — DONE:** **Phase 2 (the advisory local-LLM-judge, Steps 8–12) SHIPPED** (#407, feat `5c7c175`) on the Phase-1 floor — the advisory judge (never overrides the surfaced action, ②) + deterministic agreement (③) + `verification_mode` degradation disclosure reusing the IN-4 / OllamaUnreachable path (④), gated behind `verification_judge_enabled` default-off (①); tests fake the judge (1639 passed/22 skipped). **PLAN-0035 flipped Draft → Complete + `git mv` to `done/` (`805f5d2`) — both phases of member (b) verify+reshape now shipped, the A1 arc closed end-to-end.** *(folded from §7 handoff, s67; PLAN drafted+merged s73; Phase 1 shipped + (c) ratified s73; Phase 2 shipped + A1 closed s74)*

- [x] **A2 — equal-rubric arm-(a) re-grade — DONE (s71, #392 + `2463229`).** Committed reproducible harness `benchmarks/procedure_comparison/regrade_arm_a.py` reproduces the full §B-3 A2 table (hardened 24→33/39→39/40→40; nudged 40/40/40), all-120 sanity assert green (every recomputed full-key grade matches the stored `proposal_correct`). §B-3 enriched with the handler-verified residual decomposition: the 7 hardened-reduced aquaculture misses = **5 correct-action** (`start_emergency_aerator`, prose framed as an "assessment" omitting the verb → the prose `action_keywords` check misses it) + **2 genuine wrong-action** (`increase_water_exchange`) → true wrong-action **2/40**. Finding: arm (a) ties-or-exceeds arm (c) once the rubric + prompt confounds are removed; the 5 prose-omission cases are the A1 verify+reshape target. *(folded from §7 handoff, s67; closed s71)*

- [x] **G2 drafting-friction root-fix — PLAN-0034 FULLY COMPLETE — DONE (s72).** Step-5 prong-2 scope annotation merged (#399, `.claude/autonomy-triggers.md`; annotation `5daa0e0` / merge `0f56d24`) — Cowork-drafted (ADR-009 D1, K-1/K-2; Code declined the Stop-hook Code-direct override, applied byte-identical edits, committed). PLAN-0034 flipped **Ready for execution → Complete** + `git mv docs/plans/0034-*.md → docs/plans/done/` (`72f0deb`). SD-3 = (a) PLAN-only (no ADR amendment). The only residual is the **optional, non-blocking** Cray-gated live gold re-score (prong-1 behavioral proof, host-state — **NOT** an acceptance gate; the offline gate, green at #397, is the sole acceptance condition). Parked s63; hit AGAIN s66 + s67 + s68; DRAFTED s71 (#394); ratified all four SDs = (a) + core-implemented s71 (#396/#397). *(folded from §7 handoff, s67; s68 instance + classifier prong; drafted s71; ratified+implemented s71; closed s72)*

- [x] **Promote the "proceed vs Cowork-dispatch-file" routing standard — DONE (s68).** Promoted into **CLAUDE.md §6** ("Routing: proceed vs Cowork-dispatch", #376 / commit `1963282`) — **home changed from the tentative `docs/conventions/` to CLAUDE.md per Cray's 2026-06-19 decision** (strong binding). Cowork-drafted (ADR-009 D1), Code R2-reviewed + committed (D2). Private Auto-Memory slimmed to a pointer (SD-C); parked G2 root-fix preserved separately (line above, SD-D). *(folded from §7 handoff, s67; closed s68)*

## Rotated this reconcile (session-117 DB-isolation track, 2026-07-10 — #678/#679/#680)

> Recent Decisions held at the 10-row cap (R2): one row added for this track, the oldest
> rotated out here verbatim.

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-07 | **DESIGN: ADR-0029 Accepted + PLAN-0056 Ready — the `event`/Alert-triggered procedure-run trigger (3rd trigger kind) architected + build-PLANned (session 110; #621 + #622)** — `next-work-analyst` ranked next-work **A▸D▸C**; Cray picked **A = event-triggered runs** (moat axis-(a) asset-event trigger + procurement hero-demo opener). Both `plan-drafter`-authored → Code R2 → Cray-ratified → committed; no code change. **ADR-0029 (#621):** an OCT Alert **FEEDS INTO** + fires a governed `PipelineRun` (SD-1 (b) = Procedure engine as the single governed action surface); SD-2 event-keyed `run_id <procedure_id>@<event_key>` (cf PLAN-0055 S6); SD-3 declarative `event_kind`→`procedure_id`; SD-4 in-process fire v1. Preconditions (ServicePrincipal PLAN-0053, scheduler PLAN-0055) already shipped → unblocked. **PLAN-0056 (#622):** phased like PLAN-0055 — Phase A (offline) lifts the `event` block + adds `EventTrigger` descriptor + event-keyed idempotency + pure resolver + bridge fire-fn; Phase B wires the recommender `_populate_store` loop behind default-off `event_bridge_enabled` (ship-dark) + LOUD-on-failure + a procurement asset-failure→emergency-sourcing demo. 12 ACs offline/deterministic; SD-P1..P4 as-rec. Build = un-gated Code follow-on | `aeb4a75` (#621 ADR merge) / `40ef332` (#621 feat) / `54f80c4` (#622 PLAN merge) / `cae21fc` (#622 feat) / `docs/adr/0029-*.md` + `docs/plans/0056-*.md` |


---
## Rotated 2026-07-10 (session-117 PLAN-0062 close-out reconcile)

Two Active TODOs removed from `docs/STATUS.md`. The first is **discharged** (the AC-5 erratum is recorded in PLAN-0062's Close-out section, PR #682). The second was **declined by Cray** in the flaky-DB-test track: the destructive half was fixed mechanically by #679, the rest lives in Tier-0 memory, and the proposed rule's premise was wrong (cardinality was never the invariant -- single-writer-per-checkout was). Archeology, not deletions.

- [ ] **PLAN-0062 AC-5 erratum — must be recorded in the PR4 close-out (debt, s117).** PLAN-0062 `Out of Scope` says "❌ any grammar/spec/gate/executor change — L-5" + **AC-5** cites the **shipped** evaluate/action executors, but PR1b (#673) adds a NEW `EnvBandEvaluateExecutor` (an engine module), so AC-5's wording is **not literally satisfied**. Cray ratified the engine-module home in s117 — L-5's enumerated surfaces are the grammar stack only (`spec.py` join/project, the load gate, `query_step`'s compile/execute seam), and AC-2's full-procedure run is **unreachable** without a new evaluate executor. Disclosed in the #673 PR body, NOT decided silently. **PR4's close-out must record the AC-5 erratum** (evolution, not a defect — an ADR-016/PLAN-0062-scope clarification). *(s117; PLAN-0062 PR1b #673)*

- [ ] **Home the "one session = one git worktree" convention (s117 flaky-DB track carry-over; Cray to decide skill vs CLAUDE.md).** The #679 per-checkout test-DB scoping fix exists because concurrent `pytest` in sibling worktrees on the same dev Postgres wiped each other's tables; the durable operating guard is the convention "one session = one git worktree". Home it as a Skill (how-to) **vs** a CLAUDE.md binding rule — Cray decides; a constitutional edit is Cowork-drafted by convention (§6). *(s117; #679)*

## Rotated this reconcile (session-117, 2026-07-10 — residual flaky-suite fix #684)

### Recent-Decisions row — 2026-07-07 (PLAN-0056 Phase A COMPLETE, session 110) [rotated 2026-07-10, session-117 #684 reconcile]

| 2026-07-07 | **PLAN-0056 Phase A COMPLETE (Steps 1–5) — the `event` trigger lifted + a typed `EventTrigger` descriptor + event-keyed idempotency + the event resolver + the governed `fire_event` bridge (session 110; #623 + #625 + #626 + #628 + #629)** — five un-gated Code `feat` PRs executed directly (PLAN-0056 Ready; §6 "Steps execute directly"), each green through the required `gate` (full CI). **Step 1 (#623, AC-1/2/3):** `Trigger.EVENT` admitted to `_RUNNABLE_TRIGGERS` — the `event` block lifted, every OTHER governance check intact. **Step 2 (#625, AC-4):** a typed `EventTrigger` mapping descriptor on `Procedure` (present iff `trigger==event`, `extra="forbid"`; carries `event_kind` + SP-5 `owning_person_id`, mirrors `Schedule`) + `_validate_event_trigger_descriptor` (symmetric iff-invariant) + `VerticalProcedures` cross-refs (`_check_event_cross_refs`, C901-extracted: owning-person → a declared Person + each `event_kind` maps to exactly one procedure — duplicate = ambiguous, caught at load). Fact-vs-code: the recommender's `RecommendedAction` has NO `action_type` → `event_kind` stays a free authored string, the match field pinned by Step 4. 783 passed. **Step 3 (#626, AC-5):** new `services/engine/procedures/event_bridge.py` — pure/offline `event_key(...)` (deterministic dedup hash → same window = same key = idempotent no-op re-fire; later window = fresh key; naive dt = UTC; `\x1f` sep) + `event_run_id → <procedure_id>@<event_key>` (the `pipeline_runs` write-ahead PK, mirrors PLAN-0055 S6). 11 tests. **Step 4 (#628, AC-6):** `build_event_resolver` (mirrors `scheduler_wiring.build_resolver`) turns a detected actionable event into an `EventRunRequest` — procedure by `event_kind` + run-by agent + SP-4 ServicePrincipal + SP-5 `owning_person` + the event-keyed `run_id` + a `trigger_context` stamp; an unmapped `event_kind` raises `EventBridgeError` loudly. Plus `EventTrigger.dedup_window_seconds` (per-mapping detection-window granularity, SD-P1, default 1h). 12 tests. **Step 5 (#629, AC-7/8/9):** `fire_event(session, request, *, now)` FEEDS the recommender's actionable detection INTO the governed engine (SD-1) — a REAL persisted `PipelineRun` via `run_procedure_persisted`, NOT the lightweight `ActionRecord` path; two skips mirror the scheduler (SD-2 idempotency → `ALREADY_FIRED` no-op via the write-ahead PK + SD-P4 skip-if-in-flight → `SKIPPED_IN_FLIGHT`, both landing an `event_skipped` audit); the service-actor audit (AC-7: actor_kind:service + SP-5 on-behalf-of), gated-park (AC-8: RF-3) + write-ahead durability inherited verbatim from `run_procedure_persisted`. New DB-backed `tests/services/db/test_event_bridge_fire.py` (5 tests). **807 passed** (procedures/db/verticals/api). **→ Phase A COMPLETE (the offline foundation); next = Phase B (Steps 6–8).** MS-S1-independent | `117e2d4` (#629 Step 5 feat) / `7da5622` (#628 Step 4 feat) / `f63f121` (#626 Step 3 feat) / `3a7bc16` (#625 Step 2 feat) / `ef7bd15` (#623 Step 1 feat) / merge tip `be190d8` / `services/engine/procedures/event_bridge.py` (`event_key` + `event_run_id` + `build_event_resolver` + `fire_event`) + `services/engine/procedures/spec.py` (`EventTrigger` + `dedup_window_seconds` + `_validate_event_trigger_descriptor` + `_check_event_cross_refs`) + `services/engine/procedures/orchestrator.py` (`Trigger.EVENT`) + `tests/services/engine/procedures/{test_spec.py,test_event_bridge.py}` + `tests/services/db/test_event_bridge_fire.py` |

## Rotated this reconcile (session-118, 2026-07-11 — PLAN-0063 audit-chain verification surface close-out)

### Current Focus block — session 115 (join-grammar arc) [rotated 2026-07-11, session-118 PLAN-0063 reconcile]

> **Session 115, 2026-07-09 (head_commit `1de4d14` → `5a264d6`; merge tip
> `66896e8`) — BUILD + LIVE-VALIDATE + CLOSE, the full join-grammar arc: (1)
> PLAN-0060 "reactive judgment handler catalog" shipped end-to-end (all 7
> ACs) → `docs/plans/done/` — the fix for the session-114 event-bridge
> live-smoke FINDING; (2) the Q4 join/projection-grammar ADR-016 amendment
> ACCEPTED (#659); (3) PLAN-0061 (join-grammar build) Ready (#661); (4)
> PLAN-0061 BUILT + CLOSED (all 8 ACs, #664–#668) — Phases 1-2 of the
> join-grammar sequence DONE.**
> Per-PR / per-SD detail for all three sub-batches (#655-#668) lives in the
> Recent-Decisions rows below + the `done/` plans (`0060`, `0061`) + the
> ADR-016 Q4 amendment. Headlines: **PLAN-0060** made the reactive prompt show
> per-handler descriptions (an "Available actions" catalog) so the model picks
> by MEANING; default flipped **ON** after a Cray-gated live A/B PASS (§8;
> OFF to `reorder` / ON to `emergency_source`); GOVERNED path untouched
> (governed ≠ generated). **Q4 amendment (#659):** SD-A HYBRID surface / SD-B
> 2 v1 shapes (equi-join + latest-per-group) / SD-C co-exist + parity migration
> (Phase 3) / SD-D FK + `join_path` → typed; OQ-1..4 ratified. **PLAN-0061
> (#664-#668):** grammar schema (`JoinSpec`/`ProjectSpec`) + H-governance pin +
> load gate + compile/execute (`QueryStepExecutor`, `JOIN_SHAPE_VIOLATION`),
> all offline (SD-6, NO live run), full suite **2452 / 7**. **Honest frame:**
> a DECLARING query step is declared ✔ · load-gated ✔ · execution-bound ✔ for
> the 2 v1 shapes; the 4 shipped verticals keep hand-written seeds
> (execution-bound ✖) until the Phase-3 parity-guarded migration PLAN (SD-C)
> lands — that is NEXT. `main` green + PROTECTED; 0 open PRs; loop-dispatcher
> DISABLED; MS-S1 idle; dev DB unchanged. Also on `main` this window (not this
> work): #663 `render-handoff` skill (`bb459f4`) — a parallel-session PR.

### Recent-Decisions row — 2026-07-08 (PLAN-0056 Phase B COMPLETE, session 111) [rotated 2026-07-11, session-118 PLAN-0063 reconcile]

| 2026-07-08 | **PLAN-0056 Phase B COMPLETE (Steps 6–8) → whole PLAN COMPLETE (all 12 ACs), moved to `docs/plans/done/` — the `event`/Alert-triggered governed run wired end-to-end behind a default-off ship-dark flag + LOUD-on-failure + a procurement event demo (session 111; #631 + #632 + #633 + #634)** — three un-gated Code `feat` PRs + one `docs` close, each green through the required `gate`; MS-S1-independent. **Step 6 (#631, AC-11):** `_populate_store` FEEDS an actionable recommendation INTO the governed engine in-process (ADR-0029 SD-1/SD-4) behind a **default-off `event_bridge_enabled`** flag (mirrors `verification_judge_enabled`, SD-P3); flag-off = ZERO behavior change; `event_kind = RecommendedAction.suggested_handler` (the envelope has NO `action_type`). **Step 7 (#632, AC-10, ADR-0028 D4 mirror):** a dropped/failed fire is LOUD — `event_fire_missed`/`event_fire_failed` audit + best-effort Telegram (`notify_event_fire_failed`, SEPARATE cooldown, no `llm_backend` gate), then `None` so the read path never breaks; distinct from a healthy `event_skipped`. **Step 8 (#633, AC-12):** a DISTINCT `event_emergency_sourcing_round` (trigger:event, `event_kind:emergency_source`, `owning_person_id:req-planner` SP-5 SoD) in procurement — the 7th shipped procedure (AT-2); DB-backed MS-S1-free test fires a detected asset-failure event → `build_event_resolver` → `fire_event` through the SHIPPED executor factory → parks at the DOA gate (actor_kind:service, on_behalf_of req-planner) → `appr-pm` distinct approver → COMPLETED (live smoke deferred, §8). **#634:** PLAN-0056 Ready → Complete → `done/`. **Full offline suite 2350 passed / 7 skipped**; ruff + mypy clean | `9fbc703` (#634 PLAN-COMPLETE move-to-done) / `65d9039` (#634 merge) / `f5b5c21` (#633 Step 8 feat) / `1af7928` (#632 Step 7 feat) / `02f2af9` (#631 Step 6 feat) / `services/api/routers/actions.py` (`_load_event_bridge` + `_fire_event_for_record`) + `services/api/config.py` (`event_bridge_enabled`) + `services/notify/telegram.py` (`notify_event_fire_failed`) + `verticals/procurement/procedures.yaml` (`event_emergency_sourcing_round`) + `tests/services/db/test_event_procurement_demo.py` + `docs/plans/done/0056-*.md` |

## Rotated this reconcile (session-118 continuation, 2026-07-11 — 0063 deferrals discharged / PLAN-0064 Ready / 0004+0012 hygiene)

### Recent-Decisions row — 2026-07-08 (PLAN-0057 COMPLETE, session 112) [rotated 2026-07-11, session-118 continuation reconcile]

| 2026-07-08 | **PLAN-0057 COMPLETE (all 8 ACs, live-verified) → moved to `docs/plans/done/` — the event-triggered hero-demo opener made VISIBLE over shipped ADR-0029 / PLAN-0056 plumbing (session 112; #638/#639/#640/#641)** — demo composition; NO new engine capability / NO new ADR / NO contract reshape. **#638 (Step 1+5):** `run_hero_event_governance_moment` + `build_event_hero_governance_audit` (`verticals/procurement/hero_demo/run.py`) + a service-layer test. **#639 (Step 2+4):** new `POST /demo/hero/event` (SD-2 = a new POST, NOT a param on the read-only GET) + `view-hero.js` manual↔event toggle + sense cue + `api.js` `Hero.event()`. **#640 (Step 3, AC-2):** approve→COMPLETED reveal (`renderActPanel`, client + Replay). **Live smoke Cray-approved (§8):** detected `CNC-Line-07` failure → `fire_event` → `doa_tier` gate → `appr-pm` (SoD vs `req-planner`) → COMPLETED + ฿ ledger. SD-1..SD-5 + OQ-1/OQ-2 ratified as-rec. **#641:** Ready → Complete → `done/`. Dev DB migrated `0009→0011` (Cray-approved §8) — "behind on migrations" caveat RESOLVED | `5abb1d9` (#641 PLAN-COMPLETE) / `d33fff7` (#641 merge) / `4524a29` (#640) / `8aa71c1` (#639) / `0020097` (#638) / `verticals/procurement/hero_demo/run.py` + `services/api/routers/demo.py` + `view-hero.js`/`api.js` + `tests/services/db/test_event_hero_opener.py` + `docs/plans/done/0057-*.md` |

### Active TODO removed as DISCHARGED [2026-07-11, s118 continuation — render check PASS ("chain intact · 36 rows verified" on the real dev-DB chain) + 2507/7 local full suite]

- [ ] **PLAN-0063 deferred verification debt (s118).** The Step-5 render check + a local full-suite re-run on current main; both need the dev Postgres → dockerd start = §8 host-state, Cray go pending; erratum-if-fail. *(s118; #690)*

### Active TODO removed as DISCHARGED [2026-07-11, s118 continuation — orphan DB `vero_lite_test_69fa7362` dropped with Cray §8 go after re-verifying all 16 checkout-path hash forms]

- [ ] **Housekeeping (s117 flaky-DB track): 1 orphaned test DB on the dev Postgres. Branch half CLOSED — the prior count of this TODO was wrong, both halves.** **Branches: DONE (0 remaining).** All five branches of the track are absent from `origin`, the local checkout, and the GitHub API: `fix/hermetic-db-tests`, `chore/isolate-test-db-per-worktree`, `fix/suspended-step-fail-closed` were **already deleted before s117** (the "4 un-deleted" count was stale, never verified), and `fix/load-run-positional-step-reads` + `docs/status-s117-flake-fix` were deleted in s117 after confirming `git merge-base --is-ancestor <b> main` and that neither was checked out in a worktree. **DBs: the three named here never existed.** `vero_lite_test`, `vero_lite_test_shared`, `vero_lite_test_2cee3da7` are **not** on the dev Postgres. Actual state, re-measured against `pg_database`: (a) `vero_lite_test_bb36873b` is the **LIVE** per-checkout test DB of `/home/crayj/work/vero-lite` (`worktree_scoped_test_url`, `tests/db_support.py`) — **DO NOT DROP**; (b) `vero_lite_test_69fa7362` is a genuine **orphan** — it maps to no live worktree in either the POSIX or the UNC path form (`git worktree list` reports the Windows-created worktrees under `//wsl.localhost/…`, but pytest inside one hashes its POSIX path, so both forms must be checked before calling a DB stale). Dropping (b) is a **host-state change outside the worktree → needs explicit Cray go (CLAUDE.md §8)**; it is otherwise inert. Low-priority. *(s117; #678/#679/#680/#684/#685; corrected s117 cont. after machine-verifying every name)*

## Rotated this reconcile (session-118 continuation 2, 2026-07-11 — PLAN-0010 closed + PLAN-0064 built/closed)

### Recent-Decisions row — 2026-07-08 (PLAN-0058 COMPLETE, session 113) [rotated 2026-07-11, session-118 continuation-2 reconcile]

| 2026-07-08 | **PLAN-0058 COMPLETE (all 5 ACs) → moved to `docs/plans/done/` — a thin `GET /whoami` echo over the shipped fail-closed auth seam + a frontend reject-at-login probe (session 113; #645/#646/#647)** — executes the ratified **PLAN-0054 SD-A tail** (the "who am I" read named as a designed-into-seams sequel); **NO new ADR / NO new auth backend / NO change to the seam's validation logic.** Fully offline / deterministic / MS-S1-independent. **#645 (`docs(plans):`, PLAN Ready):** `plan-drafter`-authored, Code R2-verified every code citation; **SD-1..SD-4 ratified as-rec** (Cray, AskUserQuestion) — SD-1 shape `{person_id, display_name, auth_enabled}`, SD-2 fail-closed reuse `Depends(get_current_principal)`, SD-3 include the frontend wiring, SD-4 deterministic API tests. **#646 (`feat(api):`, Steps 1-3):** `services/api/models/whoami.py` (`WhoamiResponse`) + `services/api/routers/whoami.py` (`GET /whoami` injects the shared `Depends(get_current_principal)`) + `main.py` register; `tests/api/test_whoami.py` 6 deterministic cases (200 valid + display_name / 200 no-principals null / 401 no-header / 401 unknown key / 403 unmapped person / dev-escape → auth_enabled false); async `login()` probes `/whoami` (`auth.js`) → reject-at-login, `doLogin` promise-aware (`view-monitor.js`), `?v=` bump. **#647:** Ready → Complete → `done/`. **Full offline suite 2359 passed / 7 skipped**; ruff + mypy clean. **Preview-verified** on `oct-demo-procurement` (`API_AUTH_ENABLED=true`): a bad key → inline "unknown API key", NO session stored (reject-at-login e2e); good key → session stored. Origin: s113 `next-work-analyst` re-rank → Cray picked **C1 (whoami)**, now SHIPPED | `a3b7113` (#647 merge) / `cd32b02` (#647 PLAN-COMPLETE) / `fa0a187` (#646 merge) / `8eaacd1` (#646 feat) / `1734187` (#645 merge) / `847a0bb` (#645 PLAN) / `services/api/routers/whoami.py` + `services/api/models/whoami.py` + `services/api/main.py` + `tests/api/test_whoami.py` + `services/api/static/assets/{auth.js,view-monitor.js}` + `services/api/static/index.html` + `docs/plans/done/0058-*.md` |

### Active TODO removed — DISCHARGED by PLAN-0064 (#696) [rotated 2026-07-11, session-118 continuation-2 reconcile]

- [ ] **A per-step QUERY router for procurement (PLAN-0062 close-out follow-up, s117).** procurement's QUERY executor is the fixed `_SeedQuery`, so a declared `read_stock` would pass the load gate and still receive the intake requisition — the true blocker behind PLAN-0062 AC-7's `read_stock` deferral (ERRATUM 2: the PLAN's "no substrate" reason was wrong — the ontology declares `Part.stock_qty`/`reorder_point` + the registry adapter emits both). A per-`StepKind` executor router would make `read_stock` migratable and **reopen PLAN-0062 AC-7**; pinned by the executable invariant `test_read_stock_is_blocked_by_per_kind_executor_routing_not_by_data` (fails when the router ships → the deferral falls due). *(s117; PLAN-0062 PR4 #682)*

### Active TODO removed — decided + executed (#695) [rotated 2026-07-11, session-118 continuation-2 reconcile]

- [ ] **PLAN-0010 close-vs-park — Cray decision pending** (ELI-CRAY brief delivered s118; plan stays in `docs/plans/` meanwhile). *(s118)*

### Recent Decisions row removed — 2026-07-08 (PLAN-0059) [rotated 2026-07-11, session-119 reconcile — deep rotation under the 64 KB R1 ceiling]

| 2026-07-08 | **PLAN-0059 KPI stat-tile panel COMPLETE (all 5 ACs) → moved to `docs/plans/done/` + the deferred event-bridge live-smoke FINDING recorded (session 114; B→A per Cray's directive; #649/#650/#651/#652)** — **(A, #650/#651/#652):** the hero demo's three headline ฿-impact figures — expedite premium `฿52,500` / avoided downtime `฿8.16M` / net benefit `฿8.11M` — now render as **KPI stat-tiles** over the already-shipped `GET /demo/hero/impact` ledger, with baseline→governed (`฿9.76M → ฿1.65M`) as a net-benefit-tile context sublabel; the old `kv()` rows are replaced (no duplication); no trend/target affordances. **Pure frontend composition — NO new ADR / backend / engine / payload change** (the PLAN-0057 "compose over shipped plumbing" pattern, render-only). `plan-drafter`-authored PLAN; Code R2-verified every citation + confirmed the `thb`/`thbM` formatters produce the pre-committed strings; **SD-1..SD-5 ratified as-rec** (Cray, session 114, AskUserQuestion). #651 diff confined to `services/api/static/**`, full offline suite green under the required CI `gate`, preview-verified on the hero view; #652 Ready → Complete → `done/`. **(B, #649, evidence-only §8 host-state):** the deferred event-bridge live smoke asked whether the REAL MS-S1 recommender (`gpt-oss:20b`) picks `emergency_source` for a procurement critical-asset-failure event — it chose **`reorder`** (`actor_kind=llm`, the real model engaged not the rule fallback, confidence 1.0). Root cause (offline trace): the reactive judgment prompt shows the model **bare handler NAMES only** (no per-handler descriptions / no when-to-pick guidance / `goal=None`); the distinguishing prose lives only in `procedures.yaml` step descriptions + the procedure goal, which thread into the GOVERNED path, not the reactive prompt. **Governed path + shipped hero demo (deterministic advisory stub) UNAFFECTED**; offline gates (`test_action_event_bridge.py`, `test_event_procurement_demo.py`) stay the binding bar + green. Fix (surface per-handler descriptions in the reactive prompt) = a DEFERRED next-work candidate (own PLAN, cross-vertical blast radius, then one controlled live re-validate). Origin: session-114 `next-work-analyst` re-rank → Cray picked **B → A** | `1de4d14` (#652 PLAN-COMPLETE move-to-done) / `ab02dfd` (#652 merge) / `e8a7d93` (#651 feat KPI panel) / `cffa9d1` (#650 PLAN Ready) / `f528f03` (#649 docs(logs) finding) / `services/api/static/**` (hero KPI stat-tiles) + `docs/logs/2026-07-08-event-bridge-recommender-live-smoke.md` + `docs/plans/done/0059-*.md` |

### Recent Decisions row removed — 2026-07-09 (PLAN-0060) [rotated 2026-07-12, session-120 reconcile — normal rotation under the 64 KB R1 ceiling]

| 2026-07-09 | **PLAN-0060 reactive judgment handler catalog COMPLETE (all 7 ACs) → moved to `docs/plans/done/` — surface per-handler descriptions into the REACTIVE recommender judgment prompt so the model picks by MEANING, the fix for the session-114 event-bridge live-smoke FINDING (session 115; #655/#656/#657)** — the reactive judgment prompt now renders an **"Available actions" catalog** (per-handler `description`s) inside the **TRUSTED system instruction** (same trust class as the ADR-016 D5 goal), so the model distinguishes `emergency_source` vs `reorder` instead of bare handler NAMES. Registry gains a keyword-only `description` + `handler_catalog(vertical)`; the 4 handler-registering verticals (procurement / energy / supply_chain / aquaculture; vet_clinic registers none) declare `ACTION_DESCRIPTIONS`; the block reaches **both** Pattern-B calls **and** the PLAN-0020 skip path via `build_structuring_messages`→`build_reasoning_messages`; `generate_judgment` gains `include_handler_catalog` (all 3 reasoning modes); a default-off `handler_catalog_enabled` Settings flag is threaded at the reactive `recommend()` call site. `suggested_handler` enum unchanged; flag-off byte-identical; **GOVERNED path untouched (governed ≠ generated).** **#655 (Steps 1-6, offline binding bar):** full offline suite **2389 passed / 7 skipped**, ruff + mypy clean. **AC-7 live re-validate (host-state MS-S1 `gpt-oss:20b`, Cray-gated §8, evidence-only NOT a gate):** ONE controlled A/B on the s114 CNC line-down event — catalog OFF → `reorder` (reproduces the finding), catalog ON → `emergency_source` (confidence 1.0); same event, the flag the only moved variable, pass/fail pre-committed, each arm fired once. **#656 (SD-4 default flip):** `handler_catalog_enabled` default False→True after the AC-7 PASS (only `recommend()` reads it; `generate_judgment`'s param default stays False → governed path + benchmark harness unaffected; flag-off stays available). **#657:** Ready → Complete → `done/`. Origin: s115 `next-work-analyst` re-rank → Cray picked PLAN-0060 | `f6a2217` (#657 PLAN-COMPLETE move-to-done) / `0c68d58` (#657 merge) / `a81f05a` (#656 default-flip feat) / `468c3c9` (#656 merge) / `4d54683` (#655 Steps 1-6 feat) / `7c8f2e0` (#655 merge) / `services/engine/registry.py` (`description` + `handler_catalog`) + `services/engine/llm/prompt.py` ("Available actions" block in `build_structuring_messages`/`build_reasoning_messages`) + `services/engine/llm/structured.py` (`generate_judgment` `include_handler_catalog`) + `services/engine/recommender.py` (`recommend()` flag threading) + `services/api/config.py` (`handler_catalog_enabled`) + `verticals/{procurement,energy,supply_chain,aquaculture}/handlers.py` (`ACTION_DESCRIPTIONS`) + `docs/logs/2026-07-09-reactive-handler-catalog-live-revalidate.md` + `docs/plans/done/0060-reactive-judgment-handler-catalog.md` |

### Recent Decisions row removed — 2026-07-09 (ADR-016 join/projection DESIGN) [rotated 2026-07-12, session-121 reconcile — normal rotation under the 10-row RD window]

| 2026-07-09 | **DESIGN: ADR-016 join/projection-grammar amendment ACCEPTED (Q4 multi-read) — Phase 1 of the moat join-grammar sequence (session 115; #659)** — renders ADR-016's deferred Q4 (the 2026-07-01 OQ-5 "the multi-read join lands with Q4"; PLAN-0048 walled the grammar off as "an ADR-016 amendment"): query steps will DECLARE multi-read joins + projections as typed, authored, deterministic spec surface (today `StepInput.reads` is names-only + `QueryStepExecutor` refuses `len(reads)>1` typed). **SD-A grammar surface = HYBRID** — ontology `link_types.foreign_key` = the default join (governed, single source of truth) + a typed per-step explicit override for shapes the ontology cannot declare (the procurement `intake`'s positional singleton fusion + custom projections). **SD-B v1 scope = the 2 shipped shapes** (equi-join enrichment + latest-per-group projection; general group-by/aggregation math DEFERRED — stays the walled-off `nl_query` surface). **SD-C = co-exist + parity-guarded seed migration (Phase 3, no force-retire).** **SD-D (entailed by SD-A)** = promote `LinkTypeMeta.foreign_key` into typed form + parse ADR-0027 `join_path` into the same execution-consumable shape (projection layer only; ADR-008 grammar untouched). **OQ-1..4 ratified as-rec** (Cray, AskUserQuestion): extend `StepInput` `join`/`project`; NO repair loop in v1 (D-N2); grammar = join+projection ONLY (arbitrary computation stays downstream/seed → `intake` migrates PARTIALLY under the SD-C parity guard); warn-first override validation. **NO LLM in the read path** (LOCKED-6 / ADR-0024 D3/D6); every joined type still routes through the single `read_bound_violation` bound at BOTH load gate + run dispatch (PLAN-0048 AC-3, extended not forked). `plan-drafter`-authored (in-place amendment per the D2-Amendment precedent), Code R2-verified every cited file:line on disk (corrected a dispatch over-claim — the procurement join is declared as `quote_id→Quotation.quote_id` + transitive `part_no` via `Part`, not a literal `part_id` link). **Sequence:** this amendment → build PLAN (grammar schema + compile/execute extension + SD-D promotion) → Phase-3 per-vertical factory + seed migration. Origin: s115 Cray picked the Q4 join-grammar ADR after PLAN-0060 closed; the Phase-2 build **PLAN-0061 is Ready** (#661, `ad0f543`; SD-1..6 ratified as-rec — lean 2-construct schema, 4 phases, offline-only) | `ad0f543` (#661 PLAN-0061 Ready) / `a38acde` (#659 amendment feat) / `dbf25e2` (#659 merge) / `docs/adr/0016-governed-procedure-engine.md` (§ "Amendment (2026-07-09): join/projection grammar for multi-read query steps (Q4)") |


### Current Focus block removed — session 118 [rotated 2026-07-13, session-122 reconcile — normal rotation under the 4-session CF window]

> **Session 118, 2026-07-11 (head_commit `22242e4` → `2694253`) — PLAN-0063
> audit-chain verification surface (trust dossier object ③, first product
> surface) COMPLETE in one window: drafted + ratified (#687, SD-1..6 as-rec)
> → PR1 `GET /audit/verify` (#688) → PR2 monitor "Verify chain" panel (#689)
> → closed, all 8 ACs → `done/` (#690).** `verify_chain()` (PLAN-0047 Step 5)
> gains its FIRST production caller: **#688** exposes a typed
> `ChainVerificationReport` with SD-2(d) SPLIT VISIBILITY — the verdict is
> open, verbatim break detail is credentialed via the new
> `get_optional_principal` seam in `services/api/auth.py` (OQ-1 =
> `/audit/verify`); **#689** renders it as an ON-DEMAND monitor panel
> (`view-monitor.js?v=c34`, off the poll timers). `services/db/audit_log.py`
> + `alembic/` byte-unchanged (AC-8 pins verified). **Evidence bar:** #690's
> required CI `gate` = **2506 passed / 8 skipped in 93.5 s** (FULL suite
> incl. DB-backed tests via the CI postgres:16-alpine service) on code
> identical to `main=360007a` plus the docs close-out; local on the merge
> commit ruff + ruff-format + mypy --strict clean (the LOCAL pytest degraded
> to 2391/123-skipped — dev Postgres DOWN, dockerd off — recorded as NOT the
> bar). **TWO DISCLOSED DEFERRALS** (in the close-out, not silent): (1) the
> merge-commit LOCAL full-suite re-run and (2) the Step-5 render check —
> both blocked on the dev Postgres; starting dockerd = §8 host-state
> awaiting explicit Cray go; erratum-if-fail when the render check runs.
> SD-4 follow-up (bounded/incremental verification) → Active TODO.
> **CONTINUATION (same session, afternoon batch — `next-work-analyst`
> ranking delivered; Cray picked "Router + hygiene"; every pick/ratification
> below = Cray via AskUserQuestion):** (1) **Both disclosed deferrals
> DISCHARGED — `confirmed — prior intact`, no erratum.** Cray gave the §8
> go; Docker Desktop restarted, `vero-postgres` (volume
> `vero-lite_postgres_data`) up. The Step-5 render check PASSED its
> pre-committed strings: the monitor "Verify chain" panel rendered "chain
> intact · 36 rows verified" over the REAL dev-DB audit chain (36 rows,
> breaks []), DOM-asserted + screenshot; the withheld leg is not reachable
> on this deployment (dev box opts out of authn via `.env`) and stays
> pinned by the AC-6 pytest matrix. Local full suite on main WITH Postgres
> = **2507 passed / 7 skipped** (supersedes the 2391/123 degraded run). (2)
> Orphan test DB `vero_lite_test_69fa7362` DROPPED (Cray-approved §8) after
> fresh re-verification: sha256-hashed ALL 16 existing checkout-path forms
> (main + 7 worktrees × POSIX/UNC) — none maps to `69fa7362`; only the live
> `vero_lite_test_bb36873b` remains → the s117 housekeeping TODO fully
> discharged. (3) **PLAN-0064 "per-step QUERY router for procurement"
> READY (#692)** — `plan-drafter`-authored, Code R2 re-verified every
> load-bearing citation on disk (accept); **SD-0..SD-5 ratified as-rec**:
> SD-0 no ADR-016 amendment (executor supply is "not an engine contract",
> 0016:511-513; the STOP tripwire stands) / SD-1 declaration-presence
> dispatch / SD-2 engine-module home (`query_router.py`) / SD-3
> `read_stock` only / SD-4 tripwire test rewritten in place / SD-5 declared
> reads served by the registry-registered `ProcurementSyntheticAdapter`.
> Reopens PLAN-0062 AC-7 per ERRATUM 2 by its own ACs. (4) **Hygiene
> (#693):** PLAN-0004 (Phases A+B shipped; Phase C optional → backlog) +
> PLAN-0012 (vero-bridge Phase 1 shipped + live; AC-1/AC-2 ticked as
> bookkeeping; Phase 2 stays unminted) filed to `done/`; **PLAN-0010
> deliberately NOT closed** — Cray asked for an ELI-CRAY brief before the
> close-vs-park decision (delivered in-session; decision pending). NEXT:
> build PLAN-0064 (un-gated Code build, one PR).
> **CONTINUATION 2 (same session — PLAN-0064 went draft [`plan-drafter`] →
> Code R2 → Cray SD ratification → build → close in ONE session-118 day):**
> (1) **PLAN-0010 CLOSED "shipped + intentionally disabled" → `done/`
> (#695)** — Cray-ratified after the ELI-CRAY brief (AskUserQuestion);
> AC-1/AC-3/AC-5 ticked against `tests/loop/` + the 427-message production
> run (2026-05-26→06-25); AC-2/AC-4/AC-6 left unticked HONESTLY (closed by
> operational decision over the s76 drift hazard, NOT full AC discharge —
> they become requirements of any revival PLAN); companion chore fixed the
> stale `tools/loop/__init__.py` "(future) dispatcher" docstring. (2)
> **PLAN-0064 BUILT (#696) + CLOSED, all 8 ACs → `done/` (#697)** —
> `QueryStepRouter` (declaration-presence, SD-1) in
> `services/engine/procedures/query_router.py` + 5 unit pins; the
> production procurement factory routes per step: declared `read_stock`
> (`reads: [Part]`, PLAN-0048 single-read) → the SHIPPED
> `QueryStepExecutor` over the REGISTRY-registered
> `ProcurementSyntheticAdapter` (SD-5); undeclared `intake` → the
> co-existing `_SeedQuery` byte-identically (PLAN-0062 SD-C carried).
> ERRATUM-2 tripwire test rewritten IN PLACE per its own contract (SD-4);
> SD-0 honored — zero orchestrator/registry/spec change, the STOP tripwire
> never fired; the L-4 governance-pin consequence disclosed in the PR body.
> Suite **2512/7 local WITH Postgres**. **Honest frame (LOCKED-9 style —
> nothing claims more):** procurement `read_stock` = declared ✔ ·
> load-gated ✔ · **execution-bound ✔ on the production factory path**;
> `intake` unchanged (declared-expressible ✔ per 0062 AC-6, production
> execution = the co-existing seed, derived fields ✖);
> `low_stock_reorder_round` END-TO-END = **still not production-runnable**
> — `judge_stock` reads `measured_value`, raw Part rows don't carry it
> (PLAN-0064 fact 9 → Active TODO); **PLAN-0062 AC-7's deferral is
> DISCHARGED by reference** (no 0062 line edited).

### Recent Decisions row removed — 2026-07-09 (PLAN-0061 join/projection-grammar build) [rotated 2026-07-13, session-122 reconcile — normal rotation under the 10-row RD window]

| 2026-07-09 | **PLAN-0061 join/projection-grammar build COMPLETE (all 8 ACs) → moved to `docs/plans/done/` — the ADR-016 Q4 amendment RENDERED: a query step now DECLARES multi-read equi-join enrichment + latest-per-group projection as typed authored spec — declared ✔ load-gated ✔ execution-bound ✔ for the 2 v1 shapes (session 115; #664/#665/#666/#667/#668)** — the un-gated Code build of the Ready PLAN (§6 "Steps execute directly"); ALL offline/deterministic, NO live run (SD-6 — MS-S1 never touched); every PR green through the required CI `gate`; **full suite 2452 passed / 7 skipped, ruff + mypy clean.** Chain: **#664** the SD-D substrate (`JoinKeyMeta` + ONE shared parser; `foreign_key` no longer dropped at load; `join_path` → typed) → **#665** the SD-1 lean `JoinSpec`/`ProjectSpec` schema + H-governance pin (a mid-flight edit fails CLOSED at resume) + the structural load gate (`validate_read_bindings` `meta=`; WARN-first on/fuse overrides, OQ-4) → **#666** compile + execute (`JOIN_SHAPE_VIOLATION`, OQ-1; `plan_read` `meta=` = ONE decision surface; `QueryStepExecutor` SD-1 pinned pipeline, D-N2 extended; single-read path byte-identical) → **#667** both shapes e2e over the REAL energy + procurement ontologies (SD-3 fixtures, zero vertical-file change; DB-backed JSONB-safety + governance-hash round-trip) → **#668** Ready → Complete → `done/`. The 4 shipped verticals' hand-written seeds stay execution-bound ✖ until the Phase-3 parity-guarded migration PLAN (SD-C). Full narrative: the Session-115 CF block above | `5a264d6` (#668 PLAN-COMPLETE move-to-done) / `66896e8` (#668 merge) / `e04a00b` (#667 Step 4 feat) / `0d738e1` (#666 Step 3 feat) / `93e01d1`+`7fb7497` (#665 Step 2) / `978caca` (#664 Step 1 feat) / `services/engine/ontology_meta.py` (`JoinKeyMeta` + shared parser) + `services/engine/procedures/{spec.py,orchestrator.py,query_step.py}` + `docs/plans/done/0061-join-projection-grammar-build.md` |
