# ADR-0029: Procedure `event`/Alert-Trigger Bridge

**Status:** Accepted
**Date:** 2026-07-07
**Ratified:** 2026-07-07 — Cray ratified all four surfaced decisions as-recommended: SD-1 = (b) FEED INTO (event maps to and fires a governed `PipelineRun`; the Procedure engine is the single governed action surface), SD-2 = deterministic event-keyed `run_id` `<procedure_id>@<event_key>` (write-ahead PK-idempotency, mirroring PLAN-0055 Step 6), SD-3 = declarative `event_kind`→`procedure_id` mapping authored in the vertical spec, SD-4 = in-process fire at detection for v1 (enqueue/worker deferred).
**Deciders:** Cray (ratifies), Code (R2 + commit), plan-drafter (drafts under ADR-013 D1)
**Related:** ADR-0028 (`schedule`-trigger scheduler — the shape + the scheduler precedent this mirrors; S1 lifted the block for `schedule` ONLY), ADR-016 (governed procedure engine — Phase-4+ "streaming / event-driven triggers" DEFERRED `0016-...:1103,:1139`; S1-after-S2 sequencing; `event`/Alert = the Phase-0 recommender path `:1197`), ADR-0025 (AT-2 managerial layer — the `doa_tier`⟹SoD governance an event-fired run must honor, D5), PLAN-0053 (S2 ServicePrincipal actor model, Phase B — `done/`), PLAN-0055 (S1 scheduler build — the SP-5 on-behalf-of + write-ahead PK-idempotency patterns this mirrors — `done/`), ADR-010 / PLAN-0006 (the recommender whose detection the bridge consumes)

## Context

The moat is the **asset-event trigger**: an OCT anomaly is detected → a **governed
Procedure run fires automatically**, with a typed non-human service actor and the
full audit / SoD posture — never a human hand-crank. `docs/STATUS.md:132` names this
"defensibility on **axis (a) asset-event trigger**", and the procurement hero-demo's
opening line ("a critical asset fails → *automatically* fire the governed
emergency-sourcing procedure") is exactly this bridge. Today the engine is
**event-reactive**: every runnable `PipelineRun` is fired by `manual` (human) or, since
ADR-0028, by `schedule` (a clock). This ADR adds the **third trigger kind** — `event`
(an anomaly / `Alert`) — moving the engine from clock-driven toward truly
**condition-driven**.

**The chokepoint (the trivial part).** `Trigger` admits only `MANUAL` + `SCHEDULE`
(`services/engine/procedures/spec.py:77-82`), and `_RUNNABLE_TRIGGERS =
frozenset({Trigger.MANUAL, Trigger.SCHEDULE})`
(`services/engine/procedures/orchestrator.py:136-141`) is an explicit allowlist whose
docstring **already names** "a promoted `event`/Alert path" as the intended future
addition that "stays blocked until it is deliberately added here". `validate_runnable`
raises `ProcedureError` for any trigger outside the set
(`orchestrator.py:155-160`). Lifting the block is **~2 lines**: add `EVENT` to the enum
and to `_RUNNABLE_TRIGGERS`. This is *not* where the design work lives.

**The real design work — NO bridge exists (Code-verified on disk this session).** The
recommender and the Procedure engine are deliberately **PARALLEL**, with **no wiring
between them**. `services/engine/recommender.py` emits an `ActionRecord | None` from
`recommend(event, vertical)` (`:189`) and carries its **own** lightweight governance
gate — `approve` / `reject` / `execute` (`:321-355`) — that dispatches side-effects via
`registry.get_handler(...)` (`:351`). That surface is consumed at
`services/api/routers/actions.py:59-66` into an **in-memory** `_action_store`. A grep of
`recommender.py` for `run_procedure` / `run_procedure_persisted` / `PipelineRun` /
`Procedure` / `services.engine.procedures` returns **zero matches** — the recommender
knows nothing about the governed engine. So the two live, defensible **governance
models** coexist with no reconciliation:

| | recommender `ActionRecord` path | Procedure engine `PipelineRun` |
|---|---|---|
| gate | propose→approve→execute (in-memory `_action_store`) | SoD + `gated`/`auto` steps + `autonomy_ceiling` |
| actor | `AuditMetadata(actor="engine")` | typed non-null `ServicePrincipal` + SP-5 on-behalf-of |
| durability | in-memory store | write-ahead persisted run + audit rows |
| dispatch | `registry.get_handler` | governed step executors under `validate_runnable` |

Reconciling these two is **SD-1**, the central decision of this ADR.

**Enabling precondition — satisfied TODAY.** An event-fired run, like a scheduled one,
has **no human actor**. Both preconditions are now shipped: the typed
`ServicePrincipal` actor model (PLAN-0053 / ADR-016 S2, session 104) *and* the
`schedule` scheduler that first exercised it end-to-end (ADR-0028 / PLAN-0055). The
event bridge therefore sits **strictly downstream** of both and is **unblocked now** —
it introduces no new actor primitive; it is a **pure client** of shipped plumbing.

**Actor + detection plumbing this ADR CONSUMES, does not rebuild (Code-verified).**

- `run_procedure(..., *, trigger_context=..., service_principal=...)` entry
  (`orchestrator.py:535-541`) threads the service actor + trigger context into
  `RunContext` (`:584-591`); `RunContext.service_principal: ServicePrincipal | None`
  (`orchestrator.py:110`).
- `ServicePrincipal(BaseModel)` (`spec.py:723`) — a first-class **non-human** actor,
  `extra="forbid"`, **no `roles` field** so it can never enter the SoD comparison set
  (RF-3); never an approver (SP-1).
- The scheduler's actor-resolution pattern to **mirror**: `scheduler_wiring.py` —
  `build_resolver` (`:164`) returns a `resolve(state)` closure (`:177`) →
  `_resolve_service_principal` (`:127`, uses `agent.service_principal_ids[0]`) +
  `_resolve_owning_person` (`:146`, the SP-5 on-behalf-of human) → packs a
  `ScheduledRun` (`:181-192`). The event path builds the **analogous** resolver
  (event → run-request), not a new one.
- `Schedule.owning_person_id` (the SP-5 on-behalf-of model PLAN-0055 Step 8 added so a
  `doa_tier`⟹SoD procedure has a **distinct** DOA approver — ADR-0025 D5): the event
  path faces the **same** headless-actor-vs-SoD problem and **reuses** this model.
- `GateApproverError` (RF-3): a `gated` step with no identified human approver fails
  **closed** — a service actor cannot approve a gate by construction.
- The recommender's **detection** — `recommend(event, vertical)` +
  `_is_recommendation_trigger` (`recommender.py:189,201`) — stays; only what happens to
  an *actionable* detection changes (SD-1).

This ADR decides the bridge's **architecture**. A follow-on build-PLAN specs the build
(exactly as ADR-0028 decided architecture and PLAN-0055 built it); the consumed
plumbing above is **out of the decision surface**.

## Decision

The engine gains `event` as its **third runnable trigger**, and — per the ratified
SD-1=(b) below — the recommender's **detection is
FED INTO the governed Procedure engine**: the recommender keeps detecting an actionable
condition, but an actionable event now **maps to and fires a governed `PipelineRun`**
rather than being executed through the lightweight `ActionRecord` gate. The bridge:

1. **Lifts the `manual`/`schedule`-only block** to admit `event` — adds `EVENT` to the
   `Trigger` enum (`spec.py:77-82`) and to `_RUNNABLE_TRIGGERS`
   (`orchestrator.py:136-141`), retaining **every** other governance check
   (`validate_governance_complete`, the autonomy-ceiling check, the handler allowlist,
   linear-input) unchanged. The build **corrects the stale docstring** that names the
   `event`/Alert path as merely "future" (a future reader must not re-derive it as still
   blocked).
2. **Binds every event-fired run to a declared `ServicePrincipal`** (the non-human
   trigger actor, SP-4) *and* — when the target procedure carries SoD — an
   **owning-person** (SP-5 on-behalf-of), resolved through an event resolver that
   **mirrors** `scheduler_wiring.build_resolver`. The run is invoked through the
   existing `service_principal=` / `trigger_context=` params, so the `run_started` audit
   row is a non-null service actor **by construction**. No actor logic is rebuilt.
3. **Elevates no autonomy.** An event-fired run is governed **identically** to a
   `manual` / `schedule` run: it reaches a `gated` step and **parks at `waiting_human`**;
   the service actor **cannot** approve it (`GateApproverError`, RF-3); the same
   `auto`/`gated` + `autonomy_ceiling` model applies verbatim. The bridge changes only
   *who fired* a run and *what detected the condition* — never *who approves* it. An
   automatic trigger is **not** a licence for automatic action.
4. **Makes a dropped or failed event fire LOUD, not silent** — mirroring ADR-0028 D4's
   missed-round loudness. An actionable event that maps to a procedure but fails to fire
   (mapping miss, resolver error, idempotency-collision-then-crash) emits an observable
   audit signal (an `event_fire_missed` / `event_fire_failed` row + the existing
   Telegram bridge), so the **absence** of an expected run is detectable. A detection
   that silently never became a run is the failure mode this guards.

**Four first-order architecture questions** — the two-governance reconciliation (SD-1),
event dedup / idempotency (SD-2), the event→procedure mapping surface (SD-3), and the
invocation process model (SD-4) — were surfaced for Cray and are now **RATIFIED**
(2026-07-07, all four as-recommended; see the header `Ratified:` line). The Code
recommendations in the Surfaced Decisions section are the **settled** decisions,
load-bearing in the framing above.

Second-order build-PLAN concerns (event-key hashing details, mapping-schema field
shapes, backpressure tuning, observability payload) remain **flagged, not decided** here
(see Consequences → Neutral).

## Surfaced Decisions

Each SD had multiple defensible answers. **Cray ratified all four as-recommended
(2026-07-07);** the recommendations below are the **settled** decisions, load-bearing in
the Decision above.

- **SD-1 — the two-governance-models reconciliation (THE central decision).** The
  recommender's `ActionRecord` propose→approve→execute gate and the Procedure engine's
  full governed run (SoD, `gated` steps, autonomy ceiling, audited service actor) are
  two live governance models with no bridge. Does an event fire (a) **REPLACE** the
  `ActionRecord` path by firing a `PipelineRun` directly, (b) **FEED INTO** the Procedure
  engine — the recommender's *detection* stays, but an actionable event now maps to and
  fires a governed Procedure run, or (c) run **BOTH** in parallel behind a flag?
  - *Code recommendation (ratified):* **(b) FEED INTO.** The recommender's detection —
    LLM judgment + deterministic rule fallback + governed entity resolution (ADR-0022) —
    is a shipped, valuable signal and the OCT surface already renders its reasoning
    trace; keep it. But the `ActionRecord` `execute` gate is **lightweight and in-memory**
    (`_action_store`, no SoD, no audited service actor, no autonomy ceiling, no
    write-ahead durability), whereas the Procedure engine is the **audited, SoD-governed,
    non-repudiable** one — and the hero demo wants the **governed** run. So the
    recommender keeps detecting; an actionable event **maps to and fires a governed
    `PipelineRun`**, making the Procedure engine the **single governed action surface**.
  - *Alternatives:* (a) REPLACE discards the recommender's detection / reasoning-trace
    surface that OCT already renders — too destructive. (c) BOTH doubles the
    action-and-audit surface and invites drift (which path is authoritative for the same
    detected condition?), and complicates the "one governed action surface" story.
  - *Why this is Cray's call:* it decides whether the recommender's `ActionRecord`
    `execute` path is **deprecated-in-favour-of / coexists-with / replaced-by** the
    Procedure engine — a moat-shaping, cross-surface decision touching both the OCT
    recommender **product** surface and the governance **story**. Multiple defensible
    answers; strategic, not a Code judgment call.

- **SD-2 — event dedup / idempotency.** An event stream can re-detect the same anomaly
  and re-fire; how is a duplicate governed run prevented?
  - *Code recommendation (ratified):* a **deterministic event-keyed `run_id`** —
    mirroring the schedule `<schedule_id>@<scheduled_for>` **write-ahead PK-idempotency**
    from PLAN-0055 Step 6, where the state table's per-fire-slot key makes a
    restart-double-fire a no-op. For events the analogue is `<procedure_id>@<event_key>`,
    where `event_key` is a stable hash over the event's identity + detection window; a
    re-detected event resolves to the **same `run_id`** and the write-ahead insert is a
    no-op. This reuses durability we already have (no new dedup infra) and is consistent
    with the schedule precedent.
  - *Alternatives:* a **time-window debounce** (simpler, but the window is arbitrary and
    can *drop* a genuinely-distinct re-occurrence inside the window); an **explicit dedup
    table** (durable, but more infra than the write-ahead PK gives for free).
  - *Why this is Cray's call:* the `event_key` definition is **semantic** — what makes
    two detections "the same anomaly"? A false-merge suppresses a real second incident; a
    false-split double-fires a governed action. That is a domain-judgment fork, not a
    mechanical one.

- **SD-3 — event→procedure mapping.** How does a detected `OperationalEvent` /
  `ActionRecord` select the target `Procedure` id + `Agent` + `ServicePrincipal` +
  owning-person?
  - *Code recommendation (ratified):* a **declarative mapping authored in the vertical
    spec** — e.g. an `event_kind` / anomaly-kind → `procedure_id` table (with the agent /
    service-principal / owning-person then resolved through the same
    `scheduler_wiring`-style lookup), **mirroring how `schedule` lives on the
    `Procedure`**. This keeps the trigger binding **human-authored** (ADR-0024 H-only),
    versionable per vertical in YAML, and validated at load — so a new vertical wires a
    trigger by editing spec, not code.
  - *Alternatives:* a **code-side registry** (harder to author per-vertical, escapes the
    YAML review surface); a **rule inside the recommender** (couples detection to
    dispatch and spreads governance config into the detector — the exact parallelism this
    ADR is trying to bridge, not entrench).
  - *Why this is Cray's call:* it sets **where the event→action binding is authored** —
    spec YAML (human-authored, versioned, per-vertical) vs code — a moat-authoring-surface
    decision that determines whether onboarding a vertical's trigger is a config edit or a
    code change.

- **SD-4 — invocation process model.** ADR-0028 SD-1 chose a **separate long-lived
  daemon** for `schedule` because a clock has no natural request lifecycle. `event` is
  **different**: the recommender already runs in-process (the `_populate_store` loop over
  `adapter.stream_events`, `actions.py:59-66`), so a natural trigger point **already
  exists** — the daemon question does **not** recur identically. The real fork is: fire
  the governed run **in-process synchronously** at detection, vs **enqueue** the fire to
  a worker.
  - *Code recommendation (ratified):* **in-process fire at detection for v1** — reuse the
    existing recommender loop (no new scaffold; the opposite of ADR-0028's daemon,
    precisely because the trigger point already exists). The run engine is already async
    and write-ahead durable, and a `gated` run parks quickly at `waiting_human` rather
    than blocking; name the **enqueue / worker** path as the deferred scale-out seam for
    high event volume.
  - *Alternatives:* **enqueue to a worker** now (decouples detection throughput from run
    execution — a long or parked run can't stall the stream — but adds the first
    queue/worker scaffold in the codebase, echoing ADR-0028's daemon-scaffold cost).
  - *Why this is Cray's call:* it is a latency-vs-simplicity ops posture for the first
    event-driven fire path, **entangled with SD-1** (if SD-1=(b), the fire happens where
    the recommender already runs), and it decides whether a queue/worker scaffold lands
    **now** or is deferred.

## Consequences

### Positive
- Engine moves clock-driven → **condition-driven** (the moat's axis-(a) asset-event
  trigger) without weakening any governance invariant — the gate posture is **inherited**
  from the Procedure engine, not re-derived in the recommender.
- The procurement hero-demo's automatic opening line ("asset fails → governed
  emergency-sourcing fires") becomes buildable **today** — the bridge is strictly
  downstream of the shipped ServicePrincipal (PLAN-0053) + scheduler (PLAN-0055).
- Under SD-1=(b), there is **one governed action surface**: every automatic action —
  clock or event — runs through the audited, SoD-governed, non-repudiable Procedure
  engine, and the two-parallel-governance-models seam is closed rather than duplicated.
- Clean layering: the bridge is a thin **client** of S2 + the scheduler pattern; no
  service-identity or SoD logic leaks into the recommender.

### Negative
- Couples two subsystems that are deliberately parallel today (SD-1) — a real
  reconciliation decision with product-surface reach (the OCT recommender's `execute`
  path may be deprecated), not a mechanical wiring change.
- A new **dedup/idempotency semantic** (SD-2): a wrong `event_key` either suppresses a
  real second incident (false-merge) or double-fires a governed action (false-split).
- SD-4's enqueue alternative would introduce the first queue/worker scaffold; even the
  recommended in-process path couples detection throughput to run start under load.

### Neutral (deferred to the build-PLAN — flagged, not decided here)
- **Event-key hashing** — the exact identity + detection-window inputs to
  `<procedure_id>@<event_key>` (SD-2's mechanics).
- **Mapping-schema shape** — the `event_kind`→`procedure_id` field(s) on the spec, under
  `extra="forbid"`, and its load-time cross-ref validation (SD-3's mechanics).
- **Backpressure / overlap** — reuse the schedule **skip-if-in-flight** posture
  (PLAN-0055) when a prior run of the same `procedure_id` is `running` / `waiting_human`.
- **Observability** — stamp `trigger_context` with
  `{trigger:"event", event_key, event_kind, detected_at, fired_at,
  actor:<service-principal>, on_behalf_of:<owning-person>}`.

## Deferred / Out of Scope
- **Streaming / real-time transport infra** — a durable event bus / push transport
  remains ADR-016 **Phase 4+** deferred (`0016-...:1103,:1139`); this ADR bridges the
  **already-detected** event (the recommender's existing `stream_events` consumption),
  not a new ingestion transport.
- **The anomaly detector's ML / detection quality** — SD-1 consumes `recommend(...)`
  as-is; improving detection accuracy is out of scope.
- **The actual build** — trigger-lift, resolver, mapping, dedup, and fire path are
  specced + built by a **follow-on S-PLAN** (the ADR-0028 → PLAN-0055 pattern).
- **Multi-operator RBAC** — cross-operator authorization of who may author an
  event→procedure mapping is out of scope.

## Alternatives Considered

### Alternative 1: Fire the recommender's `ActionRecord` `execute` path directly (SD-1 option a)
- Pros: least new wiring; the recommender already dispatches via `registry.get_handler`.
- Cons: the `ActionRecord` gate is lightweight + in-memory (no SoD, no audited service
  actor, no autonomy ceiling, no write-ahead durability); it is **not** the governed
  surface a hero demo needs, and it entrenches the parallelism instead of bridging it.
- Why not adopted as the primary: surfaced as **SD-1**, not silently chosen.

### Alternative 2: Run both governance models in parallel behind a flag (SD-1 option c)
- Pros: no path is removed; incremental.
- Cons: two authoritative action surfaces for the same detected condition invites drift
  and doubles the audit surface; undermines the "one governed action surface" story.
- Why not adopted as the primary: surfaced as **SD-1**.

### Alternative 3: A separate event daemon (mirror ADR-0028 SD-1)
- Pros: symmetric with the `schedule` scheduler's process model.
- Cons: **category difference** — `schedule` needed a *new* clock-driven component with
  no natural lifecycle; `event` already has an in-process trigger point (the recommender
  loop), so a new daemon is not required for correctness.
- Why not adopted as the primary: surfaced as **SD-4** (in-process vs enqueue), where the
  daemon question is reframed for the event case rather than copied.

## References
- `services/engine/procedures/spec.py:77-82` (`Trigger` enum — MANUAL + SCHEDULE only), `:723` (`ServicePrincipal`)
- `services/engine/procedures/orchestrator.py:136-141` (`_RUNNABLE_TRIGGERS` allowlist + the "promoted `event`/Alert path" docstring), `:155-160` (the block), `:110` (`RunContext.service_principal`), `:535-541`/`:584-591` (`run_procedure` service-actor threading)
- `services/engine/procedures/scheduler_wiring.py:127` (`_resolve_service_principal`), `:146` (`_resolve_owning_person`, SP-5), `:164`/`:177`/`:181-192` (`build_resolver` → `resolve` → `ScheduledRun`)
- `services/engine/recommender.py:189` (`recommend` → `ActionRecord | None`), `:201` (`_is_recommendation_trigger`), `:321-355` (parallel `approve`/`reject`/`execute` gate), `:351` (`registry.get_handler` dispatch)
- `services/api/routers/actions.py:59-66` (the `_action_store` consumption)
- `docs/adr/0028-procedure-schedule-trigger-scheduler.md` (shape + scheduler precedent; D4 loudness; SD-1 daemon)
- `docs/adr/0016-governed-procedure-engine.md:1103,:1139` (Phase-4+ event-driven-trigger deferral), `:1197` (`event`/Alert = the Phase-0 path)
- `docs/adr/0025-at2-managerial-layer.md` D5 (`doa_tier`⟹SoD the event run must honor)
- `docs/plans/done/0053-adr016-s2-service-principal-build.md` (ServicePrincipal actor model), `docs/plans/done/0055-s1-schedule-trigger-scheduler-build.md` (Step 6 write-ahead idempotency, Step 8 SP-5 on-behalf-of)
- `docs/STATUS.md:132` (asset-event trigger = defensibility axis (a))
