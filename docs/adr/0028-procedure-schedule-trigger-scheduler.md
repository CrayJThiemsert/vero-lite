# ADR-0028: Procedure `schedule`-Trigger Scheduler (S1)

**Status:** Proposed
**Date:** 2026-07-06
**Deciders:** Cray (ratifies), Code (R2 + commit), plan-drafter (drafts under ADR-013 D1)
**Related:** ADR-016 (governed procedure engine — D7 Phase 3 `schedule` trigger, S2-before-S1 sequencing, OQ-2 `schedule` reuse §1192-1195), PLAN-0052 (ADR-016 Phase-3 monitor — Surfaced-Decision S1, §237-291), PLAN-0053 (S2 service-principal actor model, Phase B — `done/`), ADR-0024 (skeleton LOADS-but-not-RUNS), PLAN-0010 (harness two-poller autonomy loop — the *category-mismatch* alternative, rejected)

## Context

The moat is **governed generative procedures**. The engine today is
**event-reactive** (every `PipelineRun` is fired by a human `manual` trigger);
S1 moves it toward **event-driven** by firing non-`manual` runs on a clock, with
a typed, non-null, non-repudiable **service** actor — never a human.

**The chokepoint.** `validate_runnable` hard-blocks every non-`manual` trigger:
`services/engine/procedures/orchestrator.py:146-150` raises `ProcedureError`,
carrying a **stale in-code comment** `"schedule is a deferred PLAN-0010 reuse,
L-1"`. ADR-016 OQ-2 (`0016-governed-procedure-engine.md:1192-1195`) frames the
same open question — whether `schedule` reuses PLAN-0010's harness machinery or
introduces a purpose-built scheduler. Both the comment and OQ-2 pre-judge a
coupling this ADR **rejects**; the follow-on build must correct both texts (a
future reader must not re-derive the already-rejected PLAN-0010 reuse).

**Enabling precondition — S2 before S1 (satisfied).** A scheduled run has no
human actor. Built before the actor model, S1 would resolve
`actor_person_id = None` on the exact runs it creates — a PDPA accountability gap
(ADR-016 §796-805). PLAN-0053 Phase B shipped the typed service-principal actor
model in session 104; the ordering constraint (a *hard* ordering, not a sibling
surface — PLAN-0052 §233-235) is now met, so S1 is unblocked.

**Actor plumbing S1 CONSUMES, does not rebuild (Code R2-verified on disk).** S1
is a **pure client** of shipped S2 infrastructure:
- `service_principal: ServicePrincipal | None` param on `run_procedure`
  (`orchestrator.py:521-531`), `run_procedure_persisted` (`persistence.py:89-100`),
  and `resume_run` (`persistence.py:259-269`).
- `run_started` audit records `actor_kind:"service"` +
  `actor_service_principal_id` + the `on_behalf_of` lineage (who fired **and** who
  owns/scheduled) — `persistence.py:131-160`.
- `GateApproverError` library guard (`action_step.py:492-503`): a `gated` step
  with no identified human approver fails **closed** — a service actor cannot
  approve a gate **by construction** (RF-3, `principal` typed `Person | None`).
- Audit column `actor_service_principal_id` (alembic 0010) + omit-when-None row
  hash; the vertical `service_principals` registry + `Agent.service_principal_ids`
  (`spec.py`, #594) — all shipped.

This ADR decides the scheduler's **architecture**. A follow-on build-PLAN specs
the build; the consumed actor plumbing above is **out of the decision surface**.

## Decision

**S1 is a separate, purpose-built procedure scheduler** — NOT a reuse of
PLAN-0010's two-poller harness-autonomy machinery (PLAN-0010 is a harness
producer/consumer loop for Cowork↔Code work exchange over a filesystem inbox, a
**category mismatch** for domain `PipelineRun` scheduling; PLAN-0052 §240-244,
ratified Cray s101). The scheduler:

1. **Lifts the `manual`-only block** in `validate_runnable` to admit `schedule`
   (retaining every other governance check — `validate_governance_complete`,
   autonomy-ceiling, handler allowlist, linear-input — unchanged), and the build
   **corrects both** the stale in-code comment (`orchestrator.py:149`) **and**
   ADR-016 OQ-2 (`0016-...:1192-1195`).
2. **Binds every scheduled run to a declared `ServicePrincipal`** named by the
   `schedule` trigger + its owning person (the `on_behalf_of` lineage), invoked
   through the existing `service_principal=` param — so the `run_started` audit
   row is a non-null service actor by construction (SP-4/SP-5).
3. **Elevates no autonomy (RF-2).** A scheduled run that reaches a `gated` step
   **parks at `waiting_human`** exactly as a manual run does; the service actor
   cannot approve it (`GateApproverError`, RF-3). S1 changes only *who fired* a
   run, never *who approves* it. It reuses the existing `auto`/`gated` +
   `autonomy_ceiling` model verbatim.
4. **Makes a missed round LOUD, not silent** — emits an observable signal (an
   audit `schedule_missed`/`schedule_skipped` row + the existing Telegram bridge)
   on every expected-but-absent fire, so the *absence* of a run is detectable.

**Three first-order architecture questions** — the process model (SD-1), the
schedule-parser dependency (SD-2), and the invocation path (SD-3) — are
**surfaced for Cray** (see Surfaced Decisions); recommendations below are
load-bearing in this draft but contingent on ratification. Second-order
build-PLAN concerns (cron/timezone, missed-run, overlap, delivery semantics,
schedule-state persistence, observability) are **flagged, not fully decided**
here (see Consequences → Neutral).

## Surfaced Decisions

Each SD has multiple defensible answers; the Code recommendation is load-bearing
in the Decision/Alternatives above but is **contingent on Cray's ratification**.

- **SD-1 — Process model.** In-process `asyncio` task inside the FastAPI app vs a
  separate long-lived worker/daemon vs external cron hitting an HTTP endpoint.
  *Code recommendation:* a **separate worker/daemon** — a request-scoped FastAPI
  app has no natural clock-driven lifecycle; an in-process task dies with the
  request/reload cycle. *Alternatives:* in-process `asyncio` (simplest, weakest
  liveness); external cron (ties to SD-3). *Why Cray's call:* no long-lived
  scaffold exists on disk — this sets the deployment/ops posture for the first
  clock-driven component in the codebase; multiple defensible answers.

- **SD-2 — Schedule-parser dependency.** `croniter` vs `APScheduler` vs a
  hand-rolled interval; none on disk. *Code recommendation:* **`croniter`** — a
  thin, parse-only dependency that leaves the scheduling loop under our control
  (pairs with SD-1). *Alternatives:* `APScheduler` (bundles a scheduler runtime —
  overlaps and partially pre-decides SD-1); hand-roll (no dependency, but
  reimplements cron edge cases). *Why Cray's call:* a new production dependency,
  and it partially pre-decides SD-1 (APScheduler brings its own process model).

- **SD-3 — Invocation path.** Direct in-process `run_procedure_persisted` call vs
  HTTP `POST /procedures/{id}/run`. *Code recommendation:* a **direct in-process
  call** — the HTTP `get_current_principal` seam assumes a human caller; a direct
  call keeps the service actor typed end-to-end. *Alternatives:* HTTP (a viable
  interim per Alternative 2, but needs scheduler auth material via `auth.py`,
  SP-6). *Why Cray's call:* entangled with SD-1 and with the SP-6 auth-transport
  boundary; the HTTP path's human-caller assumption is a real friction point.

## Consequences

### Positive
- Engine moves event-reactive → event-driven without weakening any governance
  invariant (the gate posture is inherited, not re-derived).
- Every scheduled run is non-repudiable: a typed service actor + owning-person
  lineage on the audit trail (PDPA gap closed by construction).
- Clean layering: S1 is a thin client of S2; no service-identity logic leaks into
  the scheduler.

### Negative
- Introduces the first long-lived, clock-driven component in a codebase that is
  FastAPI request-scoped today (no worker/daemon scaffold exists) — new
  operational surface (restart recovery, liveness) regardless of SD-1's outcome.
- A new scheduler dependency (SD-2) or a hand-rolled parser adds maintenance
  surface.

### Neutral
- **Deferred to the build-PLAN (flagged, not decided here):**
  - **Cron-vs-interval expressiveness** — a typed schedule descriptor on
    `Procedure` under `extra="forbid"`.
  - **Timezone** — evaluate in `Asia/Bangkok`, store the IANA tz name (TH has no
    DST, but a non-TH vertical needs it).
  - **Missed-run / catch-up** — recommend **skip-with-audit**.
  - **Overlapping-run prevention** — recommend **skip-if-in-flight** when a prior
    run of the same `procedure_id` is `running`/`waiting_human` (a run
    legitimately parks for days).
  - **At-most/at-least-once** — the engine is write-ahead durable + `action`
    steps are `gated`, so a double-fire yields a duplicate *proposal*, not a
    duplicate side-effect (noisy, not dangerous).
  - **Schedule-state persistence + restart recovery** — recommend a small
    dedicated table over deriving from run history.
  - **Observability** — stamp `trigger_context` with
    `{trigger, schedule/cron, scheduled_for, fired_at, actor:<service-principal>}`.

## Alternatives Considered

### Alternative 1: Reuse PLAN-0010's two-poller harness-autonomy machinery
- Pros: no new component; machinery already exists.
- Cons: **category mismatch** — PLAN-0010 is a harness Cowork↔Code work-exchange
  loop (heartbeat-class messages over a filesystem inbox), not a domain trigger
  for `PipelineRun`s; conflating them couples operational procedure scheduling to
  the harness autonomy loop's lifecycle.
- Why rejected: PLAN-0052 §240-244; ratified Cray s101 as-recommended.

### Alternative 2: External cron calling `POST /procedures/{id}/run`
- Pros: no in-process scheduler; standard ops tooling; a viable **interim**.
- Cons: the HTTP `get_current_principal` seam assumes a **human** caller — the
  invocation-path choice is entangled with SD-3 and with how the scheduler
  authenticates (SP-6: auth material lives in `auth.py`, kept separate from the
  declared `ServicePrincipal` identity). Still needs the full S2 actor model.
- Why not adopted as the primary: surfaced as SD-3 (interim-vs-durable), not
  silently chosen.

## References
- `services/engine/procedures/orchestrator.py:146-150` (the block + stale comment), `:521-531`
- `services/engine/procedures/persistence.py:89-100`, `:131-160`, `:259-269`
- `services/engine/procedures/action_step.py:492-503` (GateApproverError, RF-3)
- `docs/adr/0016-governed-procedure-engine.md` §796-914 (S2-before-S1), §1192-1195 (OQ-2)
- `docs/plans/0052-adr016-phase3-oct-monitor.md` §237-291 (S1 review, ratified rec)
- PLAN-0053 (`done/`) — SP-4/SP-5/SP-6, RF-1..3 (the shipped actor model)
