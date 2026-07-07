# PLAN-0056: `event`/Alert-Trigger Bridge — Build (implements ADR-0029)

**Status:** Ready for execution
**Owner:** Code (executes; plan-level Surfaced Decisions SD-P1..SD-P4 ratified by Cray 2026-07-07 (all as-recommended))
**Created:** 2026-07-07
**Related ADRs:** ADR-0029 (`event`/Alert-trigger bridge — Accepted, SD-1..SD-4 ratified), ADR-0028 (`schedule` scheduler — the phased-build + LOUD-on-failure precedent this mirrors), ADR-016 (governed procedure engine — Phase-4+ "event-driven triggers" DEFERRED `:1103,:1139`; `event`/Alert = the Phase-0 recommender path `:1197`), ADR-0025 (AT-2 managerial layer — the `doa_tier`⟹SoD gate the event run must honor, D5), PLAN-0053 (S2 ServicePrincipal actor model — `done/`), PLAN-0055 (S1 scheduler build — the SP-5 on-behalf-of + write-ahead PK-idempotency + LOUD-on-failure patterns this mirrors — `done/`)

> **Author≠reviewer (ADR-012 D4.3 / ADR-013 OQ-1).** Drafted by the in-harness
> `plan-drafter` subagent under ADR-013 D1 phased authority; outline originator =
> Code (via the dispatch); independent reviewer = Cray at PR merge (Code R2 first).
> Separation: **INTACT**. The four Surfaced Decisions below are now **ratified** by Cray
> (2026-07-07, all as-recommended — see the Surfaced Decisions section).

## Goal

Implement the ratified ADR-0029 architecture: fire a **governed `PipelineRun`
automatically when the OCT recommender detects an actionable condition** — the moat's
axis-(a) asset-event trigger. Per the four ratified ADR-0029 decisions: an actionable
event **FEEDS INTO** the governed engine (SD-1 = maps to and fires a governed run, **not**
the lightweight `ActionRecord` execute gate); duplicates are suppressed by a
**deterministic event-keyed `run_id` `<procedure_id>@<event_key>`** (SD-2, write-ahead
PK-idempotency mirroring PLAN-0055 Step 6); the event→procedure binding is a
**declarative `event_kind`→`procedure_id` mapping authored in the vertical spec** (SD-3);
and the fire is **in-process at detection for v1** (SD-4, enqueue/worker deferred). Lift
the `manual`/`schedule`-only chokepoint so `event`-triggered procedures become runnable
while retaining **every other** governance check; bind a typed `ServicePrincipal` + SP-5
owning-person by **mirroring** `scheduler_wiring.build_resolver` (never rebuilding S2);
elevate **no** autonomy (a gated step parks at `waiting_human`, RF-3); and make a
dropped/failed fire **LOUD** (audit + Telegram, mirroring ADR-0028 D4). The bridge is a
**pure client** of the shipped S2 actor plumbing (PLAN-0053) and the recommender's
existing detection (ADR-010) — it rebuilds neither.

## Acceptance Criteria

Offline/deterministic unless flagged. No MS-S1 / host-state dependence in any AC
(CLAUDE.md §8) — the bridge exercises the recommender's **deterministic rule path**, not
a live model call.

- [ ] **AC-1** `validate_runnable` admits an `event`-trigger procedure (does not raise
  `ProcedureError` on `Trigger.EVENT`); `manual` and `schedule` procedures still run; an
  unknown/other trigger still raises. Unit-tested offline.
- [ ] **AC-2** Every *other* governance check is unchanged for `event`:
  `validate_governance_complete` (skeleton-reject, ADR-0024), autonomy-ceiling, handler
  allowlist, linear-input — each proven still-enforced for an `event` procedure by a
  targeted failing-case test.
- [ ] **AC-3** The `_RUNNABLE_TRIGGERS` docstring (`orchestrator.py:136-141`) no longer
  describes the `event`/Alert path as merely "future"/blocked; the `Trigger` enum
  docstring (`spec.py:78-79`) names `event` as runnable. In-code text only.
- [ ] **AC-4** A typed `EventTrigger` mapping descriptor on `Procedure` (SD-3; present
  **iff** `trigger == event`, `extra="forbid"`) carries the `event_kind` it responds to +
  its `owning_person_id` (SP-5). Load-time cross-ref validation fails **loudly** on a
  dangling ref (procedure/agent/service-principal/owning-person not in the vertical).
  Unit-tested. *(SD-P2 ratified.)*
- [ ] **AC-5** A deterministic `event_key` + event-keyed `run_id`
  `<procedure_id>@<event_key>`: the same actionable event re-detected yields the **same**
  `run_id`, and the write-ahead insert is a **no-op** (idempotent per event-slot).
  Unit-tested offline. *(SD-P1 ratified.)*
- [ ] **AC-6** A pure, DB-free-testable **event resolver** (mirror
  `scheduler_wiring.build_resolver`) maps an actionable `ActionRecord`/event → a
  run-request: target `Procedure` (via the SD-3 mapping) + `Agent` + `ServicePrincipal`
  (via `service_principal_ids[0]`) + `owning_person` (SP-5). A mapping miss raises
  **loudly** — never a silent drop.
- [ ] **AC-7** An event-fired run binds a declared `ServicePrincipal` as its actor: the
  `run_started` audit row carries `actor_kind:"service"` + `actor_service_principal_id` +
  the `on_behalf_of` lineage. Asserted via a persisted (test-DB) run, not in-memory.
- [ ] **AC-8** An event-fired run reaching a `gated` step **parks at `waiting_human`**
  (does not auto-approve) — `GateApproverError`/RF-3 posture inherited verbatim. Asserted
  offline.
- [ ] **AC-9** An actionable event **maps to and fires a governed `PipelineRun`** via
  `run_procedure_persisted(..., service_principal=, trigger_context=)` (SD-1 FEED-INTO) —
  **not** the `ActionRecord` `execute` path; `trigger_context` is stamped
  `{trigger:"event", event_key, event_kind, detected_at, fired_at,
  actor:<service-principal>, on_behalf_of:<owning-person>}` and is readable off the
  persisted run.
- [ ] **AC-10** A dropped/failed event fire is **LOUD**: an
  `event_fire_missed`/`event_fire_failed` audit row + a best-effort Telegram alert (a
  distinct cooldown gate, mirroring `notify_schedule_missed`). Asserted via the audit-row
  assertion; the Telegram post is best-effort (never raises into the fire path).
- [ ] **AC-11** The bridge is wired into the recommender consumption path
  (`actions.py` `_populate_store`, SD-1/SD-4 in-process) behind a **default-off**
  `event_bridge_enabled` flag (SD-P3, mirroring `verification_judge_enabled`): flag-off =
  **zero** behavior change (the existing `ActionRecord` path is intact); flag-on = the
  governed run fires. Both states integration-tested.
- [ ] **AC-12** A **procurement** demo: an asset-failure `event` auto-fires the
  event-triggered emergency-sourcing procedure → auto steps → **parks at the ฿-tier
  `doa_tier` gate** → a **distinct** authored approver resolves it (SoD satisfied via the
  SP-5 owning-person). DB-backed integration test + a deterministic (MS-S1-free) smoke.

## Out of Scope

- ❌ **Streaming / real-time transport infra** — a durable event bus / push transport
  stays ADR-016 **Phase 4+** deferred (`:1103,:1139`). The bridge consumes the recommender's
  **already-detected** event (its existing `stream_events` consumption), not a new
  ingestion transport.
- ❌ **The enqueue/worker fire path** — SD-4 chose **in-process** for v1; the decoupled
  queue/worker is the named deferred **scale-out seam**, out of scope here.
- ❌ **The anomaly detector's ML / detection quality** — the bridge consumes
  `recommend(...)` as-is; improving detection accuracy is out of scope.
- ❌ **Multi-operator RBAC** — cross-operator authorization of who may author an
  event→procedure mapping is out of scope; one declared mapping per vertical spec.
- ❌ **Rebuilding any S2 actor plumbing or the schedule scheduler** — `service_principal`
  params, the `run_started` service-actor audit, `GateApproverError`, the
  `service_principals` registry / `Agent.service_principal_ids`, and the
  `scheduler_wiring` resolver pattern are consumed / mirrored, not rebuilt.

## Surfaced Decisions — RATIFIED (Cray, 2026-07-07)

ADR-0029 §Consequences→Neutral flagged these as deferred to this build-PLAN. Each had
multiple defensible answers; **Cray ratified SD-P1..SD-P4 all as-recommended on
2026-07-07** (ADR-009 D1) — the recommendations below are now the **settled** build
contract, load-bearing in the Steps, no longer contingent.

- **SD-P1 — `event_key` hashing inputs (the false-merge/false-split fork).**
  **RATIFIED (Cray, 2026-07-07): hash over `(vertical, event_kind, primary affected-entity id(s), detection-window bucket)`.**
  *Rec:* hash
  over `(vertical, event_kind, primary affected-entity id(s), detection-window bucket)`,
  where the window bucket truncates `detected_at` to a per-mapping granularity — so a
  steady-state anomaly re-detected each poll collapses to **one** run, while the same
  anomaly recurring in a later window fires a **fresh** run. *Alt:* (a) hash the full
  event payload (too granular — every reading re-fires); (b) entity-only, no time bucket
  (a resolved-then-recurring anomaly can **never** re-fire). *Cray call:* the false-merge
  (suppress a real second incident) vs false-split (double-fire a governed action)
  tradeoff is a **domain judgment** tied to each anomaly's real recurrence semantics.
- **SD-P2 — mapping-schema field shape (under `extra="forbid"`).**
  **RATIFIED (Cray, 2026-07-07): an `EventTrigger` descriptor on the `Procedure` (present iff `trigger == event`).**
  *Rec:* an
  `EventTrigger` descriptor **on the `Procedure`** (present **iff** `trigger == event`),
  carrying `event_kind` + `owning_person_id`, **mirroring how `Schedule` lives on
  `Procedure`**; the bridge derives the `event_kind`→procedure index by scanning
  procedures with `trigger == event`. *Alt:* a top-level `event_map` table in the vertical
  spec (`event_kind`→`procedure_id`, allows one kind → many procedures); a code-side
  registry (escapes the YAML review surface). *Cray call:* sets the **authoring surface**
  and whether one `event_kind` may fan out to multiple procedures (a table permits N:M; a
  per-procedure descriptor is 1 procedure declaring its own trigger).
- **SD-P3 — ship-dark flag default (off vs on).**
  **RATIFIED (Cray, 2026-07-07): default-off `event_bridge_enabled` (ship-dark).**
  *Rec:* a **default-off**
  `event_bridge_enabled` flag (mirror `verification_judge_enabled`) so the bridge ships
  **dark** and is enabled per-deployment; the existing `ActionRecord` path is untouched
  when off. *Alt:* default-on (bridge live on merge — flips recommender action semantics
  for **every** existing deployment); no flag (all-or-nothing, no safe rollout). *Cray
  call:* a default-on changes the recommender's action behavior for every deployment the
  moment it merges — a **blast-radius / rollout-posture** call.
- **SD-P4 — backpressure / overlap policy.**
  **RATIFIED (Cray, 2026-07-07): reuse skip-if-in-flight when the same `procedure_id` is `running`/`waiting_human`.**
  *Rec:* reuse the schedule
  **skip-if-in-flight** posture (PLAN-0055 SD-P3) — when a prior run of the same
  `procedure_id` is `running`/`waiting_human`, a **new-key** event fire is
  **skipped-with-audit** (a governed run legitimately parks for days at a gate). *Alt:*
  allow-concurrent (a re-detected condition fires a second parallel run — noise on the
  approver's desk); queue-behind. *Cray call:* interacts with the long-lived-park reality
  of gated steps and is **distinct from SD-P1** (SD-P1 dedupes the *same* event-key;
  SD-P4 governs a *different* key hitting an *already-parked* procedure); business-visible.

**Cross-cutting design note (not a blocker) — gate-resolve + vertical choice.** An
event-fired run that reaches a `gated` step **parks for a human** (RF-3; the service actor
cannot approve, by construction, AC-8). The human-approver path needs a real **authored
`Person`** in the vertical — the RF-1 guard checks the `Person` OBJECT, not `person_id`.
**Energy authors no principals by design (OQ-6); procurement does.** Any demo that
exercises a gated event-fired run must therefore target a **principal-bearing vertical
(procurement)**; an energy event demo can show fire→auto steps but will 409 at a gated
resolve. Call this out in the demo step (Step 8), not as a code defect.

## Steps

Phased: **Phase A** is offline-testable and lands the trigger-lift + mapping descriptor +
event-key + resolver + fire function with **no** new long-lived process (SD-4 v1 fires
in-process where the recommender already runs). **Phase B** wires the bridge into the
recommender consumption path behind the ship-dark flag, adds LOUD-on-failure, and lands
the procurement demo. Each step is a small PR (CLAUDE.md §7).

### Phase A — trigger-lift + mapping + event-key + resolver + fire function

**Step 1 — Lift the `event` block + correct the docstrings.** Add `EVENT` to the
`Trigger` enum (`spec.py:77-82`) and to `_RUNNABLE_TRIGGERS` (`orchestrator.py:136-141`),
keeping `validate_governance_complete` + ceiling + handler + linear-input intact (AC-1,
AC-2). Correct the `_RUNNABLE_TRIGGERS` docstring (which currently frames `event`/Alert as
future/blocked) and the `Trigger` enum docstring (AC-3). *(In-code only. ADR-016's
Phase-4 deferral text at `:1103,:1139` MAY optionally be annotated to point at ADR-0029 —
but editing an Accepted ADR is **G1-gated** (needs per-diff Cray approval); treat that
annotation as optional and expect the gate if attempted.)*

**Step 2 — The `EventTrigger` mapping descriptor + load-time validation (SD-3, SD-P2).**
Add the typed mapping descriptor on `Procedure` under `extra="forbid"` (present **iff**
`trigger == event`), carrying `event_kind` + `owning_person_id`, **mirroring `Schedule`**.
Add load-time cross-ref validation: the procedure's agent, its `service_principal_ids[0]`,
and its `owning_person_id` must resolve in the vertical, and a duplicate `event_kind`
mapping fails loudly. Confirm the `event_kind` source against the recommender's
`ActionRecord`/event shape (candidate: `action.action_type`, e.g. `emergency_source`;
pin this in the PR). Unit tests for the descriptor + validator. *(SD-P2 ratified.)*

**Step 3 — The `event_key` + event-keyed `run_id` (SD-2, SD-P1).** Add a deterministic
`event_key(event) -> str` helper hashing the SD-P1 inputs, and compose the run id as
`<procedure_id>@<event_key>`. Prove idempotency: the same actionable event re-detected
yields the **same** `run_id`, so the write-ahead insert is a no-op (AC-5). Offline tests
including a re-detect-collapses-to-one-run case and a distinct-window-fires-fresh case.
*(SD-P1 ratified.)*

**Step 4 — The event resolver (mirror `scheduler_wiring.build_resolver`).** Build the
analogous resolver: an actionable `ActionRecord`/event → a run-request (procedure via the
Step-2 mapping + agent + `ServicePrincipal` via `service_principal_ids[0]` + `owning_person`
via SP-5). Pure, DB-free-testable. A mapping miss / dangling ref raises **loudly** (never
a silent drop) (AC-6). Reuse `_resolve_service_principal` / `_resolve_owning_person`-style
lookups; do not rebuild them.

**Step 5 — The bridge fire function (SD-1, SD-P4).** An actionable `ActionRecord` →
`run_procedure_persisted(..., service_principal=<resolved SP>, trigger_context=<AC-9 stamp>)`
using the Step-3 event-keyed `run_id`; apply **skip-if-in-flight** (SD-P4) when a prior run
of the same `procedure_id` is `running`/`waiting_human`. Deterministic-offline (the
recommender's **rule path**, MS-S1-free). Persisted-run assertions cover the service-actor
audit (AC-7), the gated-park posture (AC-8), and that the fire goes through the **governed
engine, not the `ActionRecord` execute path** (AC-9). *(SD-P4 ratified.)*

### Phase B — recommender wiring (ship-dark) + LOUD-on-failure + procurement demo

**Step 6 — Wire the bridge into the recommender path behind the ship-dark flag (SD-1,
SD-4, SD-P3).** At the `_populate_store` consumption loop (`services/api/routers/actions.py:59-66`),
when `settings.event_bridge_enabled` is on and a `recommend(...)` result is actionable +
maps to an `event` procedure, call the Step-5 fire function **in-process** (SD-4 v1).
Flag **off** (default) = zero behavior change; the existing `ActionRecord` → `_action_store`
path is untouched (AC-11). Add the `event_bridge_enabled` flag to `config.py`
(default-off, mirroring `verification_judge_enabled`). Integration-test both flag states.
*(SD-P3 ratified.)*

**Step 7 — LOUD-on-failure: audit + Telegram (ADR-0028 D4).** Emit an
`event_fire_missed`/`event_fire_failed` audit row on an actionable event that maps but
fails to fire (mapping miss, resolver error, idempotency-collision-then-crash), and wire a
best-effort Telegram alert — add `notify_event_fire_failed` + a `build_*_message` helper
with a **distinct** cooldown gate, mirroring `notify_schedule_missed` /
`build_schedule_missed_message` (reuse the `_post_telegram` core; never raise into the fire
path) (AC-10). Document the ops posture (how the alert is gated + read).

**Step 8 — Procurement demo (mirror PLAN-0055 Step 8).** Author an **event-triggered**
emergency-sourcing procedure in the procurement spec — a **DISTINCT** `procedure_id`
(e.g. `event_emergency_sourcing_round`) with `trigger: event`, an `EventTrigger` mapping to
the asset-failure `event_kind`, and `owning_person_id: <a maintenance planner>` (SP-5, so
the `doa_tier` gate's SoD has a requester distinct from the approver). It reuses the **same
governed beat** as the manual `emergency_sourcing_round` — **not** a flip of that
procedure's trigger (trigger is a single enum; a schedule/event descriptor is present
**iff** the trigger matches — the exact rationale PLAN-0055 used for
`scheduled_emergency_sourcing_round`). An asset-failure `event` auto-fires it → auto steps
→ **parks at the ฿-tier `doa_tier` gate** → a **distinct** authored approver resolves it.
DB-backed integration test + a deterministic (MS-S1-free) smoke (AC-12). Demo-only, not a
build gate.

## Verification

- Phase A is fully offline: `pytest` proves AC-1..AC-9 with the recommender's rule path +
  the test DB (`TEST_DATABASE_URL`, disposable per project memory) for the persisted-run
  assertions (AC-7/AC-8). No injected model.
- Phase B: AC-11 via the two-flag-state integration test; AC-10 via the audit-row
  assertion; AC-12 via the DB-backed procurement demo test + the deterministic smoke.
- **No AC depends on MS-S1 or a live model** — the bridge exercises the deterministic rule
  path (the recommender's LLM path falls back to it; ADR-010 IN-4). Any live end-to-end
  smoke (real detector → real fire) is **evidence, not the gate** (CLAUDE.md §8); get
  explicit Cray go before a host-state run.
- Gate: full suite green (**not** a named subset — per the s104 CI lesson, include
  `tests/api/`), ruff + mypy clean, `uv sync --extra dev` resolves cleanly.

## References
- `services/engine/procedures/spec.py:77-82` (`Trigger` enum), `:85` (`Schedule` — the descriptor pattern SD-3 mirrors), `:723` (`ServicePrincipal`)
- `services/engine/procedures/orchestrator.py:136-141` (`_RUNNABLE_TRIGGERS` + docstring), `:155-160` (the block), `:110` (`RunContext.service_principal`)
- `services/engine/procedures/persistence.py:89-100` (`run_procedure_persisted(..., trigger_context=, service_principal=)`)
- `services/engine/procedures/scheduler_wiring.py:127` (`_resolve_service_principal`, `service_principal_ids[0]`), `:146` (`_resolve_owning_person`, SP-5), `:164` (`build_resolver` — the resolver pattern Step 4 mirrors)
- `services/engine/recommender.py:189` (`recommend` → `ActionRecord | None`), `:201` (`_is_recommendation_trigger`), `:321-355` (the `ActionRecord` gate the bridge FEEDS-INTO past)
- `services/api/routers/actions.py:59-66` (`_populate_store` — the Step-6 wiring point)
- `services/api/config.py:129` (`verification_judge_enabled` — the default-off ship-dark pattern), `:257` (`telegram_notify_enabled`)
- `services/notify/telegram.py:107` (`_post_telegram`), `:172` (`build_schedule_missed_message`), `:185` (`notify_schedule_missed` — the Step-7 mirror)
- `verticals/procurement/procedures.yaml` (`emergency_sourcing_round` + its `doa_tier` gate; `scheduled_emergency_sourcing_round` — the distinct-trigger-variant precedent for Step 8)
- `docs/adr/0029-procedure-event-trigger-bridge.md` (the governing ADR — SD-1..SD-4)
- `docs/plans/done/0055-s1-schedule-trigger-scheduler-build.md` (the phased-build template + Steps 6/7/8 patterns)
- `docs/STATUS.md:132` (asset-event trigger = defensibility axis (a))
