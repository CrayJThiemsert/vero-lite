# PLAN-0055: S1 Procedure `schedule`-Trigger Scheduler — Build

**Status:** Ready for execution
**Owner:** Code (executes; Surfaced Decisions SD-P1..SD-P6 ratified as-recommended by Cray 2026-07-07)
**Created:** 2026-07-07
**Related ADRs:** ADR-0028 (S1 scheduler architecture — Accepted, SD-1/2/3 ratified), ADR-016 (governed procedure engine — D7 Phase-3 `schedule`, OQ-2 §1192-1195), PLAN-0053 (S2 service-principal actor model — `done/`), ADR-0024 (skeleton LOADS-but-not-RUNS)

> **Author≠reviewer (ADR-012 D4.3 / ADR-013 OQ-1).** Drafted by the in-harness
> `plan-drafter` subagent under ADR-013 D1 phased authority; outline originator =
> Code (via the dispatch); independent reviewer = Cray at PR merge (Code R2 first).
> Separation: **INTACT**. The six Surfaced Decisions below are ratification-gated —
> Code must not silently pick a default.

## Goal

Implement the ratified ADR-0028 S1 architecture: fire non-`manual`
`PipelineRun`s on a clock via a **separate, long-lived worker/daemon** (SD-1)
using **`croniter`** (SD-2, a new parse-only production dependency) and a
**direct in-process `run_procedure_persisted(...)` call** (SD-3) that passes a
typed `ServicePrincipal` as the run's actor. Lift the `manual`-only chokepoint so
`schedule`-triggered procedures become runnable while retaining **every other**
governance check, and correct the two stale texts that pre-judge the rejected
PLAN-0010 reuse. S1 is a **pure client** of the already-shipped S2 actor plumbing
(PLAN-0053 Phase B) — it rebuilds none of it.

## Acceptance Criteria

Offline/deterministic unless flagged. No MS-S1 / host-state dependence in any AC
(CLAUDE.md §8) — the scheduler is a clock, not a model caller.

- [ ] **AC-1** `validate_runnable` admits a `schedule`-trigger procedure (does not
  raise `ProcedureError` on `Trigger.SCHEDULE`); a `manual` procedure still runs;
  an unknown/other trigger still raises. Unit-tested offline.
- [ ] **AC-2** Every *other* governance check is unchanged for `schedule`:
  `validate_governance_complete` (skeleton-reject, ADR-0024), autonomy-ceiling,
  handler allowlist, linear-input — each proven still-enforced for a `schedule`
  procedure by a targeted failing-case test.
- [ ] **AC-3** The stale in-code comment at `orchestrator.py:149` is corrected (no
  longer says "deferred PLAN-0010 reuse, L-1"); ADR-016 OQ-2 at
  `0016-...:1192-1195` is corrected to point at ADR-0028's separate-scheduler
  decision (not "Deferred to PLAN-0019 dispatch").
- [ ] **AC-4** A scheduled run binds a declared `ServicePrincipal` as its actor:
  the `run_started` audit row carries `actor_kind:"service"` +
  `actor_service_principal_id` + the `on_behalf_of` lineage (persistence.py path).
  Asserted via a persisted (test-DB) run, not in-memory.
- [ ] **AC-5** A scheduled run reaching a `gated` step **parks at
  `waiting_human`** (does not auto-approve) — `GateApproverError`/RF-3 posture
  inherited verbatim. Asserted offline.
- [ ] **AC-6** A pure, unit-testable **"fire due schedules"** function computes the
  due set from the schedule-state table + a supplied `now` (injected clock, no
  wall-clock read), calls the invocation path once per due schedule, and updates
  `last_fired`/`next_fire`. Deterministic — no daemon, no sleep.
- [ ] **AC-7** Schedule-state persistence + **restart recovery**: after a simulated
  restart the daemon recovers its schedule set and does **not** double-fire a
  schedule already fired for the same `scheduled_for` (idempotent per fire-slot).
- [ ] **AC-8** A missed round emits an observable `schedule_missed`/`schedule_skipped`
  audit row (ADR-0028 D4) per the ratified missed-run policy (SD-P2).
- [ ] **AC-9** `trigger_context` on a scheduled run is stamped with
  `{trigger, schedule/cron, scheduled_for, fired_at, actor:<service-principal-id>}`
  (SD-P6) and is readable off the persisted run.
- [ ] **AC-10** `croniter` is added to `pyproject.toml` (SD-2) and `uv sync
  --extra dev` resolves cleanly; a cron-expression parse test passes offline.
- [ ] **AC-11** The daemon has a defined entrypoint, run loop, graceful shutdown
  (SIGTERM → finish/park in-flight, no torn writes), and structured logging;
  a start→one-tick→shutdown smoke exits 0. *(Loop timing may need a short live
  run; keep it bounded + injected-clock where possible.)*

## Out of Scope

- ❌ **v2 login / `GET /whoami` / interactive human-operator auth** — S1 uses a
  declared `ServicePrincipal`, not a logged-in human (SP-6 keeps auth material in
  `auth.py`, separate from the actor identity). The HTTP invocation path
  (Alternative 2) is explicitly deferred.
- ❌ **Multi-operator RBAC / per-operator scheduling permissions** — one declared
  service principal per schedule; no operator-facing schedule-management UI/API.
- ❌ **`event`/Alert-triggered runs** (Phase-0 path) and any non-`schedule`
  non-`manual` trigger — S1 lifts the block for `schedule` **only**.
- ❌ **Rebuilding any S2 actor plumbing** — `service_principal` params,
  `run_started` service-actor audit, `GateApproverError`, the
  `service_principals` registry / `Agent.service_principal_ids` are consumed as-is.
- ❌ **`celery`-beat** — `celery` is a dep but as a task-queue; ADR-0028 chose a
  separate `croniter` daemon, not celery-beat.

## Surfaced Decisions — RATIFIED 2026-07-07 (Cray, all six as-recommended)

ADR-0028 §157-173 flagged these as Neutral/deferred to this PLAN. Each had
multiple defensible answers; **Cray ratified SD-P1..SD-P6 all as-recommended on
2026-07-07** (ADR-009 D1) — the recommendations below are now the load-bearing
build contract, no longer contingent.

- **SD-P1 — Cron/timezone semantics.** *Rec:* evaluate schedules in
  `Asia/Bangkok`; store the **IANA tz string per schedule** (not a global const) so
  a non-TH vertical works. *Alt:* UTC-only (simpler, wrong for a TH operator);
  global tz const (breaks multi-vertical). *Cray call:* sets a customer-facing
  semantic + a schema field shape.
- **SD-P2 — Missed-run policy after downtime.** *Rec:* **skip-with-audit** — do
  not backfill; emit `schedule_missed` (AC-8). *Alt:* backfill-all (storm on
  restart); backfill-latest-only. *Cray call:* at-least/at-most-once tradeoff has
  business-visible consequences.
- **SD-P3 — Overlap policy.** *Rec:* **skip-if-in-flight** when a prior run of the
  same `procedure_id` is `running`/`waiting_human` (a run legitimately parks for
  days at a gate). *Alt:* allow-concurrent; queue-behind. *Cray call:* interacts
  with the long-lived-park reality of gated steps.
- **SD-P4 — Delivery guarantee.** *Rec:* **at-most-once** effective, tied to
  SD-P2 skip + SD-P3 skip; rely on write-ahead durability + `gated` `action` steps
  so a rare double-fire is a duplicate *proposal*, not a duplicate side-effect
  (noisy, not dangerous — ADR-0028 §167-169). *Cray call:* the guarantee is a
  composite of P2+P3, worth stating explicitly.
- **SD-P5 — Schedule-state table + restart recovery.** *Rec:* a **small dedicated
  table** (persisted schedules + `last_fired` + `next_fire`) over deriving from run
  history. *Alt:* derive from `PipelineRun` history (fragile, races). *Cray call:*
  a new persisted surface + migration; recovery correctness (AC-7) depends on it.
- **SD-P6 — `trigger_context` observability.** *Rec:* stamp
  `{trigger, schedule/cron, scheduled_for, fired_at, actor:<service-principal>}`
  on every scheduled run (AC-9). *Cray call:* fixes the audit shape a future
  monitor/UI reads.

**Cross-cutting design note (not a blocker) — gate-resolve + vertical choice.** A
scheduled run that reaches a `gated` step **parks for a human** (RF-3; the service
actor cannot approve, by construction, AC-5). The human-approver path needs a real
**authored `Person`** in the vertical — the RF-1 guard checks the `Person` OBJECT,
not `person_id`. **Energy authors no principals by design (OQ-6); procurement
does.** Any S1 demo that exercises a gated scheduled run must therefore target a
**principal-bearing vertical (procurement)**; an energy demo can show fire→auto
steps but will 409 at a gated resolve. Call this out in the demo step, not as a
code defect.

## Steps

Phased: **Phase A** is offline-testable and lands the trigger-lift + state + the
pure fire function without any long-lived process. **Phase B** adds the net-new
daemon operational surface (SD-1). Each step is a small PR (CLAUDE.md §7).

### Phase A — trigger-lift + schedule state + pure fire function

**Step 1 — Lift the `manual`-only block + correct both stale texts.** Edit
`validate_runnable` (`orchestrator.py:146-150`) to admit `Trigger.SCHEDULE` while
keeping `validate_governance_complete` + ceiling + handler + linear-input intact
(AC-1, AC-2). Correct the `:149` comment (AC-3, in-code) and, in the **same PR**,
correct ADR-016 OQ-2 `:1192-1195` to cite ADR-0028's separate-scheduler decision.
*(Note: editing an Accepted ADR is G1-gated — needs per-diff Cray approval; the
in-harness plan-drafter/Code path for the OQ-2 correction should expect the gate.)*

**Step 2 — Schedule descriptor + schedule-state table (SD-P1, SD-P5).** Add a
typed schedule descriptor on `Procedure` under `extra="forbid"` (cron expr + IANA
tz per SD-P1) and a small schedule-state table (Alembic migration) holding
persisted schedules + `last_fired` + `next_fire`. Unit tests for the descriptor +
migration round-trip.

**Step 3 — Add `croniter` + a pure next-fire calculator (SD-2).** Add `croniter`
to `pyproject.toml`; wrap it in a thin `next_fire(cron, tz, after)` helper.
Offline parse + next-fire tests, including a TH-tz case (AC-10).

**Step 4 — The pure "fire due schedules" function (SD-P2, SD-P3, SD-P4, SD-P6).**
Given `(schedule_set, now)` with an **injected clock**, compute the due set, apply
skip-if-in-flight (SD-P3) + skip-with-audit for missed (SD-P2), call
`run_procedure_persisted(..., service_principal=<declared SP>)` once per due
schedule (SD-3), stamp `trigger_context` (SD-P6), and update `last_fired`/
`next_fire`. Fully unit-testable, no daemon (AC-6). Persisted-run assertions cover
the service-actor audit (AC-4) and the gated-park posture (AC-5).

### Phase B — long-lived daemon + ops posture (SD-1)

**Step 5 — Daemon scaffold (SD-1).** Net-new operational surface: a deployment
entrypoint, a run loop that periodically calls the Step-4 fire function, graceful
SIGTERM shutdown (finish/park in-flight; no torn writes), and structured logging
(AC-11). No new scheduling logic — the daemon only drives the pure function.

**Step 6 — Restart recovery + no-double-fire (SD-P5).** On startup the daemon
recovers its schedule set from the state table and, using the per-fire-slot
idempotency key (`scheduled_for`), does not re-fire a slot already fired across a
restart (AC-7). Simulated-restart test.

**Step 7 — Missed-round LOUDness + ops wiring (ADR-0028 D4).** Emit the
`schedule_missed`/`schedule_skipped` audit row on every expected-but-absent fire
and wire the existing Telegram bridge so the *absence* of a run is detectable
(AC-8). Document the run/deploy posture (how the daemon starts, logs, is monitored).

**Step 8 (optional, gated on SD-P* ratification) — procurement demo.** A scripted
`schedule`→fire→auto-steps→park-at-gate demo on the **procurement** vertical
(principal-bearing, so the gated resolve has an authored `Person`; energy would
409 — see the cross-cutting note). Read-only-ish, demo-only, not a build gate.

## Verification

- Phase A is fully offline: `pytest` proves AC-1..AC-6, AC-9, AC-10 with an
  injected clock + the test DB (`TEST_DATABASE_URL`, disposable per project memory).
- Phase B: AC-7 via a simulated restart; AC-8 via the audit-row assertion; AC-11
  via a bounded start→tick→SIGTERM smoke.
- No AC depends on MS-S1 or a live model (the scheduler is a clock). Any live
  daemon smoke is **evidence, not the gate** (CLAUDE.md §8); get explicit Cray go
  before a host-state run.
- Gate: full suite green (not a named subset — per s104 CI lesson, include
  `tests/api/`), ruff + mypy clean, `uv sync --extra dev` resolves with `croniter`.
