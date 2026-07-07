# PLAN-0052: ADR-016 Phase-3 OCT monitor (v1 — read-only pipelines list + live run detail)

**Status:** Complete (v1 read-only monitor shipped session 101, PR #577 `febdf7e` — `GET /runs` list + live run-detail + `view-monitor.js`; the Control leg PLAN-0054 extended its `mode:'read'|'operate'` seam. The S5 config-UI leg stays Out-of-Scope/deferred. Archived to `done/` 2026-07-07, session 109 — the Status line was un-reconciled at completion.)
**Owner:** Claude Code (Tier 2 — all commits Code-exclusive per ADR-009 D2 / ADR-013 D2; drafted by the in-harness `plan-drafter` under ADR-013 D1 phased authoring)
**Created:** 2026-07-05
**Related ADRs:** ADR-016 (D7 Phase 3 — this PLAN builds its first increment; D2 `PipelineRun`/`StepResult` record shape the monitor reads; D3/D4 the approve→execute + `waiting_human` suspend/resume seam the Control leg extends; **OQ-2** scheduler = S1 below), ADR-007 (D2 `RecommendedAction` envelope — **unchanged**, L5), ADR-008 (ontology — **unchanged**, L5), ADR-012 (D4.3 author≠reviewer disclosure), ADR-013 (safe/human-gated autonomy posture; D1 phased authoring)
**Related PLANs:** PLAN-0019 (Phase 1 — shipped the `Procedure/Step/PipelineRun/Agent` primitive + persistence the monitor reads), PLAN-0039 (the read-only `GET /procedures` spec-viewer + `view-procedures.js` — the surface this monitor extends), PLAN-0047 (the run + gate-resolve HTTP seam in `services/api/routers/runs.py` — the Control write endpoint already on disk), PLAN-0010 (Ready — the two-poller harness autonomy loop; **not** the procedure scheduler — see S1), PLAN-0005 §8.1 (read-side audit / PDPA — relevant to S2)

> **Drafting provenance / Author≠reviewer disclosure (ADR-012 D4.3).**
> Outline originator = **Cray** (session 101: Option-1 greenlight that the
> artifact is a PLAN, the read-only v1 cut, and the load-bearing **L4**
> "monitor as a genuine Control-leg foundation, not a throwaway demo view"
> direction). Drafter = the in-harness **`plan-drafter`** subagent (ADR-013 D1
> phased authoring). Independent reviewers = a **four-lens specialist +
> stakeholder panel** (session 101 — four read-only `explore-research` review
> lenses advising on quality within the ratified direction; see the
> Surfaced-Decisions provenance paragraph), **Code R2** (which R2-verified the
> panel's load-bearing on-disk claims against fresh evidence before the drafter
> folded them, and commits per ADR-009 D2), and **Cray** at the Ready gate
> (Draft → Ready flips only now that Cray has ratified S1–S5 as-recommended,
> 2026-07-05). The panel is an **added independent-review layer**: it advised,
> the drafter folded, Code verified, Cray ratified — the drafter neither
> commits nor ratifies and no reviewer originated the direction, so separation
> remains **INTACT**.

## Goal

Build the **first, minimal increment of ADR-016 D7 Phase 3** ("OCT as
Command / Control / Monitor center"): a **read-only monitor** over the
**already-persisted** `PipelineRun` / `StepResult` records — (a) a
**pipelines/runs list** view and (b) a **live run-detail** view exposing each
run's status, per-step `status`/`duration_ms`/`artifact`/`reasoning_trace`/`audit`.
v1 is **additive read-views + read API endpoints only**: it invents no
persistence, no scheduler, no credential, no SLA machinery, and does not touch
the ADR-007 envelope, the ADR-008 ontology, or `spec.py` (L5). It is
deliberately architected as a **genuine foundation for the Control leg** (L4):
it reads **real persisted runs** (never mock data) and reuses the existing
approve→execute + `waiting_human` suspend/resume seam so that "approve / reject /
cancel a run **from the monitor UI**" later is an **extension, not a rewrite**.

## Acceptance Criteria

Offline-verifiable unless marked (live/UI).

- [ ] **AC-1 — read API, runs list.** A new `GET /runs` endpoint returns a list
      projection of persisted `PipelineRun` rows (`run_id`, `procedure_id`,
      `agent_id`, `status`, `started_at`, `updated_at`, a **`trigger`
      discriminator + `triggered_by`** projected from
      `PipelineRun.trigger_context`, and a **`step_count` / step-progress**
      summary e.g. "3/5, 1 waiting") for the active vertical. The `trigger` +
      step-progress fields are already-persisted data (a **projection widening,
      not a schema change**) that serves L4 forward-compat + operator
      scannability (S1 scheduler + S4 UX lenses, independently). *Pass/fail:*
      `pytest` a seeded-DB test asserts the shape (incl. `trigger`/`triggered_by`
      + step-progress) + that a seeded `waiting_human` run appears with
      `status == "waiting_human"`. Still read-only.
- [ ] **AC-2 — read API, run detail.** `GET /runs/{run_id}` returns the run plus
      its ordered `StepResult`s, each carrying
      `status`/`duration_ms`/`artifact`/`reasoning_trace`/`audit`. *Pass/fail:* a
      seeded-DB test asserts the per-step trace/audit round-trip and a `404` for
      an unknown `run_id`. Reuses the existing `load_run` (persistence.py) — no
      new query layer.
- [ ] **AC-3 — read-only by construction.** Both endpoints perform **no**
      mutation, **no** LLM call, and issue only `SELECT`s. *Pass/fail:* a test
      asserts the handlers import no writer/executor symbol; a grep for
      `session.merge`/`.commit()`/`resolve_gated_step` in the new handlers returns
      empty.
- [ ] **AC-4 — reads real persisted runs, never mock (L4-i).** The list/detail
      views bind to `GET /runs` (real rows), not to `mock.js`. *Pass/fail:* a
      grep of the new front-end view for `mock`/`MOCK` returns empty; the view's
      only data source is `api.js` → `/runs`.
- [ ] **AC-5 — front-end view mounts (UI).** A new tab (`VIEWS` key `H`, label
      "Monitor") registers in `app.js` and renders the runs list; selecting a run
      opens the detail view with the per-step trace. **Accessibility /
      snapshot-verifiability (S4 frontend-UX lens):** the list rows, step rows,
      and gate panel carry stable `data-testid`s (`run-row-{run_id}`,
      `step-row-{step_id}`, `gate-panel`) + appropriate ARIA roles — required so
      `preview_snapshot` + `preview_eval` can assert row/step counts
      deterministically rather than scraping brittle text. *Verify (UI):*
      `preview_snapshot` + `preview_eval` (no screenshot — see
      `project_preview_screenshot_timeout`); assert a seeded run row + a step-row
      count in the detail pane **by `data-testid`**.
- [ ] **AC-6 — live-updating cut (UI, S4-dependent).** The run-detail view
      reflects a run advancing `running → waiting_human → completed` without a
      manual full reload, at the S4-ratified refresh mechanism (recommendation:
      **poll**). *Verify (UI):* seed a run, advance it via the existing
      gate-resolve endpoint, assert the detail pane updates within one poll.
- [ ] **AC-7 — Control-leg forward-compat proven (L4-ii).** The §Forward-compat
      section names the exact seams a future Control increment plugs into
      (`POST /runs/{id}/gate/resolve` + `resolve_gated_step` +
      `resume_run`, all already on disk) and the run-detail view exposes (read-only
      in v1) the `waiting_human` gate state + its pending proposals, so adding an
      approve/reject control is a UI+wire change, not a data-model change.
      *Pass/fail:* the detail payload includes the gate/proposal fields for a
      `waiting_human` run (asserted in the AC-2 test); no new persistence is added.
- [ ] **AC-8 — zero change to the frozen surfaces (L5).** `git diff` touches
      **none** of: `services/engine/procedures/spec.py`, the ADR-007
      `RecommendedAction` envelope, or any `verticals/*/ontology/*.yaml`.
      *Pass/fail:* a path-scoped `git diff --name-only` excludes all three.
- [ ] **AC-9 — full suite green.** `uv sync --extra dev && pytest` + `ruff` +
      `mypy` clean (CLAUDE.md §8). Backward-compatible: every shipped procedure /
      run path still loads (the monitor is purely additive read).

## Out of Scope

- ❌ **Any new scheduler** — the `schedule` trigger's poller machinery (S1) is
      surfaced, not built.
- ❌ **Any service-credential / non-human-principal model** (S2) — surfaced;
      may deserve an ADR amendment.
- ❌ **SLA-as-governance objects** (S3) — surfaced, not built.
- ❌ **The config-UI leg** of ADR-016 Phase 3 (S5) — deferred; v1 stays
      read-only.
- ❌ **Act-from-UI** (approve/reject/cancel a run **from the monitor**) — v1 is
      **read-only**; the write seam already exists server-side and v1 only
      *exposes it read-only* so the Control increment is additive (L4).
- ❌ **New persistence / migrations** — v1 reads existing `pipeline_runs` /
      `step_results` (L2); no Alembic change.
- ❌ **Changes to `spec.py`, the ADR-007 envelope, the ADR-008 ontology** (L5).
- ❌ **Branch/loop/parallel steps, retry/backoff, event-streaming triggers** —
      ADR-016 Phase-4+ deferral list.

## Forward-compatibility with the Control leg (L4 — mandatory, load-bearing)

The read-only v1 must not paint us into a corner: adding "operate real work from
the monitor" later must be an **extension, not a rewrite**. The seams are
**already on disk** — v1's job is to *expose them read-only*, not to reinvent
them:

1. **The write seam already exists at the API layer.**
   `services/api/routers/runs.py` already ships
   `POST /runs/{run_id}/gate/resolve` (→ `resolve_gated_step` in
   `services/engine/procedures/action_step.py`) and `POST /procedures/{id}/run`.
   The Control increment is a **UI button that calls an endpoint that already
   exists** — not new orchestration. v1 adds only the mirror-image **`GET`**
   endpoints.
2. **The suspend/resume state machine already exists.** ADR-016 D4 +
   `resume_run` / `resolve_gated_step` implement the durable `waiting_human`
   suspend → human-decides → resume continuation. The monitor's run-detail view
   **surfaces `waiting_human` + the pending proposals read-only**; the Control
   increment flips that same panel to interactive by wiring the existing
   resolve endpoint. No new state, no new persistence.
3. **The read projection is the same shape the write path already consumes.**
   `load_run` (persistence.py) and the `StepResultView` model (already in
   `services/api/models/runs.py`) are reused verbatim — the monitor is a *reader*
   over the exact records the executor writes, so a future "approve from here"
   acts on the identical objects it displays.
4. **UI de-risk mirrors the PLAN-0039 precedent.** `view-procedures.js` already
   shipped read-mode with an inert edit-branch that PLAN-0040 flipped on. The
   monitor view is authored the same way: a `mode: 'read' | 'operate'` seam where
   v1 renders read-only and the gate/proposal panel is structurally present but
   inert — the Control increment sets `mode: 'operate'` and reuses the render
   path unchanged.

**Corner-avoidance claim:** because v1 (i) reads real persisted runs, (ii)
reuses the existing `load_run` + `StepResultView` shapes, and (iii) exposes the
`waiting_human` gate + proposals read-only over the *same* records the existing
`resolve` write endpoint acts on, a future Control increment adds **zero** new
persistence and **zero** new orchestration — it wires an existing write endpoint
to an existing display. This is the sales-pitch surface Cray named (s101): a
monitor that *demonstrably* can grow into operating real work.

## Steps

Each step has a pre-committed pass/fail read (Lesson #0026; CLAUDE.md §11).

### Step 1 — Read-side API models + `GET /runs` list endpoint
Add `RunSummaryView` + a `RunsListResponse` to `services/api/models/runs.py`
(reuse the existing `StepResultView`); add `GET /runs` to `runs.py` returning
summaries for the active vertical via a read-only `SELECT` over `pipeline_runs`.
`RunSummaryView` also projects a **`trigger` discriminator + `triggered_by`**
(from the already-persisted `PipelineRun.trigger_context`) and a **`step_count`
/ step-progress** summary — a projection widening over existing data, no schema
change (S1 + S4 lenses). **Pass/fail:** seeded-DB `pytest` returns the seeded run
in the list with correct `status`, `trigger`/`triggered_by`, and step-progress;
handler imports no writer symbol (grep). (AC-1, AC-3)

### Step 2 — `GET /runs/{run_id}` detail endpoint
Add `GET /runs/{run_id}` delegating to the existing `load_run`; project the run
+ ordered `StepResult`s (trace/audit/duration) + the `waiting_human` gate state
and pending proposals **read-only**. **Pass/fail:** seeded-DB test round-trips
per-step trace/audit + `404` on unknown id; a `waiting_human` run exposes the
gate/proposal fields (AC-2, AC-7).

### Step 3 — Monitor front-end view (list + detail)
Add `services/api/static/assets/view-monitor.js` bound to `api.js` → `/runs`
(never `mock.js`); register `VIEWS.H` ("Monitor") in `app.js`; author it with a
`mode: 'read' | 'operate'` seam (operate-branch inert in v1, mirroring
`view-procedures.js`). Emit stable **`data-testid`s** (`run-row-{run_id}`,
`step-row-{step_id}`, `gate-panel`) + ARIA roles so the snapshot/eval assertions
are deterministic (S4 lens; AC-5). **Pass/fail (UI):**
`preview_snapshot`/`preview_eval` selects the seeded run row + step-rows in
detail **by `data-testid`**; grep for `mock` is empty (AC-4, AC-5, AC-7).

### Step 4 — Live-update cut (per S4 ratification)
Implement the S4-ratified refresh (recommendation: **poll** the detail endpoint
on an interval; SSE deferred). **Pass/fail (UI):** seed a run, advance it via the
existing gate-resolve endpoint, assert the detail pane reflects the new status
within one poll (AC-6).

### Step 5 — Frozen-surface + full-suite verification
Confirm the frozen surfaces are untouched and the suite is green.
**Pass/fail:** `git diff --name-only` excludes `spec.py` / ADR-007 envelope /
`verticals/*/ontology/*.yaml`; `uv sync --extra dev && pytest` + `ruff` + `mypy`
clean (AC-8, AC-9).

## Surfaced Decisions / Open Questions (S1–S5 — RATIFIED by Cray, 2026-07-05, session 101, as-recommended)

> **RATIFIED.** Cray ratified S1–S5 exactly as recommended (session 101,
> 2026-07-05) — this is what flips the PLAN Draft → **Ready**. Each
> recommendation below is now the **ratified decision**; the alternatives are
> retained for lineage. The direction is **LOCKED** — the session-101 panel
> review (below) only *improves quality within* that direction and reverses
> nothing.

> **Panel review (session 101).** After ratification, a **four-lens
> specialist + stakeholder panel** advised on quality via four **read-only**
> `explore-research` review lenses — **S1** scheduler/SRE · **S2**
> security-IAM / PDPA-DPO · **S3** SRE / ops-manager · **S4** frontend-UX /
> operator. Each lens sharpened *how* to build within the ratified direction;
> **no direction was reversed**. **Code R2-verified the load-bearing on-disk
> claims** (cited `file:line` below) against fresh evidence before the drafter
> folded them. Enrichments are attributed to their lens inline (e.g. "(S2
> security review)"). The build-facing must-haves each lens raised are folded
> as **"the eventual ADR/build must answer:"** bullets so the Wave-4+ ADR work
> inherits them.
>
> **ADR-routing forward-note (orients Wave-4+ ADR work; do NOT draft those
> ADRs here).** **S2** is an **ADR-016 amendment** (it extends the D2
> Agent/principal grammar + D3, matching the 2026-06-25 facet + 2026-07-01
> read-binding in-place amendment precedent). **S1** is **ADR-worthy** (its own
> ADR or an ADR-016 amendment — the non-human trigger path). **S3-enforcement**
> is **co-ADR-worthy with S2** (the breach-escalation target must be a named
> human). **Sequencing constraint: S2 before S1** — a scheduled run has no human
> actor, so S1 built before S2 would null the audit actor (PDPA gap); the actor
> dependency is a hard ordering, not a sibling surface.

- **S1 — `schedule`-trigger scheduler (ADR-016 OQ-2).** Does the `schedule`
  trigger **reuse PLAN-0010's two-poller machinery** or introduce a **separate
  procedure scheduler**?
  **Recommendation:** a **separate, purpose-built procedure scheduler** — verified
  on disk, PLAN-0010 is a *harness* producer/consumer autonomy loop for
  Cowork↔Code work exchange (heartbeat-class messages over a filesystem inbox),
  **not** a domain trigger for `PipelineRun`s; conflating them would couple
  operational procedure scheduling to the harness autonomy loop's lifecycle.
  **ADR-worthiness:** **YES** — a scheduler defines the non-human trigger path
  and interacts with S2; deserves its own ADR (or an ADR-016 amendment) before
  build. **Not in v1** (read-only).
  *Alternatives:* reuse PLAN-0010 (rejected — category mismatch); external cron
  calling `POST /procedures/{id}/run` (viable interim, still needs S2).
  **Ratified** (Cray s101, as-rec).
  - **Load-bearing (Code R2-verified — S1 scheduler review).** The engine
    **hard-blocks** `schedule` today: `validate_runnable`
    (`orchestrator.py:138-142`) raises `ProcedureError` for any non-`manual`
    trigger, carrying a **stale in-code comment** "schedule is a deferred
    PLAN-0010 reuse, L-1". The S1 ADR/build **must** (a) lift/relax that guard
    and (b) **correct BOTH** that comment **and** the ADR-016 OQ-2 text
    (`0016-governed-procedure-engine.md:954-957`) — else a future reader
    re-derives the already-rejected PLAN-0010 coupling.
  - **HARD dependency (sequencing, not just a sibling surface): S1 cannot be
    built before S2.** A scheduled run has no human actor, so `actor_person_id`
    falls back to null (`persistence.py:132-140`) → a PDPA gap. **S2 before S1**
    is an ordering constraint.
  - **SRE stakeholder must-have — a missed round must be LOUD, not silent.**
    Emit an observable signal (an audit `schedule_missed`/`schedule_skipped`
    row + the existing Telegram bridge) on **every** expected-but-absent fire,
    so the *absence* of a run is itself detectable.
  - **The eventual ADR/build must answer:**
    - **Cron-vs-interval expressiveness** — add a typed schedule descriptor to
      `Procedure` under `extra="forbid"`.
    - **Timezone** — evaluate in **Asia/Bangkok**, store the IANA tz name (TH
      has no DST so ambiguity is moot for the primary partner, but a non-TH
      vertical needs it).
    - **Missed-run / catch-up** — rec **skip-with-audit**.
    - **Overlapping-run prevention** — rec **skip-if-in-flight** when a prior
      run of the same `procedure_id` is `running`/`waiting_human` (sharpest,
      since a run legitimately parks at `waiting_human` for days).
    - **At-most-once semantics** — the engine is write-ahead durable + `action`
      steps are `gated`, so a double-fire yields a duplicate *proposal*, not a
      duplicate side-effect (cheap-but-noisy, not dangerous).
    - **Schedule-state persistence + restart recovery** — rec a small dedicated
      table over deriving from run history.
    - **Invocation path** — in-process `run_procedure_persisted` vs HTTP
      `POST /procedures/{id}/run`; the HTTP path's `get_current_principal`
      assumes a human caller → **this choice is blocked on S2**.
    - **Observability** — stamp `trigger_context` with
      `{trigger, schedule/cron, scheduled_for, fired_at, actor:<service-principal>}`.
    - **Open build-PLAN questions (no on-disk answer today):** cron-parser / new
      dependency choice (croniter / APScheduler vs hand-roll — none on disk);
      the scheduler **process model** — no long-lived worker/daemon scaffold
      exists (the app is FastAPI request-scoped), so in-process asyncio task vs
      separate worker vs external cron is a **first-order ADR question**.

- **S2 — service credential / principal for non-human triggers.** When a
  scheduled / non-human run fires, **who is the actor on the audit trail**
  (`PipelineRun.trigger_context` + per-step `audit`; `run_started` audit
  `actor_person_id`)?
  **Recommendation:** a **typed service-principal** (a first-class non-human
  `Person`-like actor with a stable id + declared scope), recorded in
  `trigger_context` and the audit `actor_person_id`, **never** an empty/`None`
  actor — so every automated write remains attributable under PDPA
  (PLAN-0005 §8.1).
  **ADR-worthiness:** **YES — an ADR-016 AMENDMENT** (not a new ADR): it
  extends the D2 Agent/principal grammar + D3, matching the 2026-06-25 facet +
  2026-07-01 read-binding in-place amendment precedent. It touches the
  audit/PDPA model and the SoD principal machinery (`step_principals`); a
  "non-human but named" actor is a governance primitive, not a config detail.
  **Not in v1.**
  **Ratified** (Cray s101, as-rec).
  - **CRUX (invariant — preserve verbatim; S2 security-IAM review):** a
    service-principal is a **requester/actor ONLY, NEVER an approver**. A
    scheduled trigger changes only *who fired* the run, never *who approves* a
    `gated` write (still a human at `waiting_human`). Letting a service-principal
    satisfy the approver role silently converts `gated`→`auto` and voids ADR-016
    D3 + the fail-safe posture. Grounds (Code R2-verified):
    `resolve_gated_step` / `_enforce_principal_sod` fail-closed
    (`action_step.py:299,408`).
  - **Identity shape.** Bind to the **Agent**, mirror `Person`
    (`spec.py:638-657`) — a distinct actor *kind*, same shape (stable id +
    declared scope, H-governed). Do **NOT** overload `Person` (SoD compares
    `person_id`s — a service id leaking in could collapse a constraint).
  - **Least-privilege via the EXISTING `Agent.allowed.{action_handlers,
    object_types}`** (`spec.py:609-615`) — no new scope primitive; the
    service-principal inherits its Agent's blast radius. **No auth material on
    the identity** (declared identity only in the local/on-prem model; the
    API-key transport in `auth.py` is the *scheduler's* concern, kept separate).
  - **DPO stakeholder.** PDPA accountability requires a non-null,
    non-repudiable, **typed** actor on every consequential write; the audit
    hash-chain already gives integrity — S2's job is to guarantee the actor
    field is always a **resolvable declared identity**.
  - **The eventual ADR/build must answer (folded as invariants M1–M7 + RF-1..3):**
    - **M1** requester-only-never-approver (invariant + test: a service
      `person_id` passed to `resolve_gated_step` fails closed).
    - **M2** never-null actor — replace the `None` fallback at
      `persistence.py:132-140` + a test asserting `actor_person_id is not None`
      for a schedule-triggered run (highest-leverage PDPA fix).
    - **M3** `actor_kind` — extend the existing `actor_kind:"engine"`
      (`action_step.py:292`) with `"service"` vs `"human"` so the audit trail is
      filterable by actor class.
    - **M4** preserve the on-behalf-of chain — `trigger_context` records BOTH
      the service-principal and the owning human, if any.
    - **M5** reuse the existing allowlists (M-least-privilege above).
    - **M6** no auth material on the identity.
    - **M7** H-governed — add the new fields to
      `STEP_/AGENT_GOVERNANCE_FIELDS` per the 2026-07-01 OQ-A precedent.
    - **RF-1 (security invariant — the one that would make Cray reconsider the
      *mechanics*):** gate-resolve must reject a service/`None` principal for a
      `gated` step **regardless of the authn toggle**, because
      `auth.py:71-72` (`api_auth_enabled=false → AuthContext(None,None)`) makes
      a plain (non-SoD) `gated` step's approver check inert — a scheduler
      driving gate-resolve with authn off would **evaporate the human gate**.
    - **RF-2** `auto` scope-creep — restate that `auto` on a write stays a
      deliberate per-step author choice; a service-principal does **NOT** elevate
      any step's autonomy.
    - **RF-3** keep service ids out of the `Person`/SoD comparison set.

- **S3 — SLA-as-governance.** Make SLAs (e.g. "morning round completes by
  08:00") **first-class governance objects** the monitor tracks / surfaces /
  enforces?
  **Recommendation:** **surface, defer the build.** Recommended shape: a typed,
  optional per-`Procedure` SLA descriptor (target completion window + a breach
  disposition) that the monitor *reads and flags* — **display-only first**, with
  *enforcement* (escalation on breach) a later increment. Keeps v1 read-only
  while proving the surface.
  **ADR-worthiness:** **YES** — an SLA that the engine *enforces* is a new
  governance object interacting with the D4 status enum and S2's non-human
  actor; ADR it before enforcement (a display-only SLA badge could be a smaller
  amendment). **S3-enforcement is co-ADR-worthy with S2** (the escalation target
  must be a named human — see the S3↔S2 coupling below).
  **Ratified** (Cray s101, as-rec).
  - **KEY (Code R2-verified — S3 SRE review): elapsed wall-clock is the WRONG
    clock.** A run parked at `waiting_human` for days is NOT breaching → an SLA
    must measure **active engine time, excluding parked intervals**. There is
    **no persisted parked-time accumulator** today (`PipelineRun` has only
    `started_at`/`updated_at`, `StepResult.created_at`; park intervals live
    un-aggregated across `run_started`/`run_resumed` audit rows) — name this as
    the **enforcement-blocker field to add** (an accumulated `waiting_ms`, or an
    aggregation of the suspend/resume audit). Any completion-window enforcement
    built before it **will misfire** on the exact runs D4 was designed to
    support — which is *why* enforcement is correctly deferred, but the
    **descriptor must name a pause-aware clock NOW** so v1's badge and v2's
    enforcement agree.
  - **Ops-manager stakeholder.** A badge must resolve to **"who owns this + the
    next action"** — tie the badge to the `waiting_human` gate's pending
    proposal (already exposed read-only per AC-7). Clock-time SLAs need
    **business-hours / calendar awareness** (an 08:00 round shouldn't breach on
    a closed day) — **no calendar abstraction exists on disk** (net-new if
    scoped).
  - **The eventual ADR/build must answer:**
    - **Three typed SLA target shapes** the descriptor names: (a)
      **completion-window** (clock pauses during `waiting_human` — needs the
      accumulator); (b) **time-to-first-human-action** (the high-value ops
      target — a proposal sitting unapproved); (c) per-step duration (cheap, low
      ops value).
    - **Window definition** — support BOTH a fixed duration from `started_at`
      AND a wall-clock deadline ("by 08:00") → a discriminated
      `deadline_kind: duration | clock_time` (mirror the ADR-016 D2-A3
      `gate_kind` discriminated-shape precedent).
    - **Breach disposition** — **reuse the existing `escalate_to_human` rail**
      (`orchestrator.py:634-651`): an SLA breach is semantically "this run needs
      a human now", so route it through the same divert (land at `waiting_human`
      with a synthetic breach proposal) rather than a parallel notify path.
      Typed enum: `badge_only` (v1) / `notify` / `escalate`.
    - **S3↔S2 coupling** — the escalation target MUST be a human: a breach on a
      service-principal-triggered run escalates to a **named human owner**, not
      the service principal → the descriptor needs an `owner` / `escalate_to`
      human reference (this is what makes S3 + S2 co-ADR-worthy).
    - **Badge** — three states `on_track` / `at_risk` / `breached` (the
      `at_risk` ~>80% band is what makes it a *monitor*, not a post-mortem);
      **suppress** the badge for a run correctly parked at `waiting_human` under
      a *completion-window* SLA (so a legitimately-waiting run doesn't glow red).
    - **Descriptor home** — a typed optional field on `Procedure` under
      `extra="forbid"`, backward-compatible (mirror the facet/reads amendment
      pattern).

- **S4 — v1 UI cut (list-only / list+detail / live).**
  **Recommendation:** **list + detail + poll-based live-update** — the
  minimal-but-demo-valuable cut consistent with L2/L4. List gives the "pipelines"
  overview; detail exposes the per-step trace/audit (the legibility upgrade
  ADR-016 D2 names) and the `waiting_human` gate (the Control-leg hook); **poll**
  (simple, no server push infra) over **SSE** (deferred — more infra, marginal
  demo gain at v1 run volumes). Live-update is what makes it a *monitor*, not a
  static report.
  **ADR-worthiness:** NO — a v1-scoping call, not a durable architecture
  decision.
  **Ratified** (Cray s101, as-rec). *(Interval values below are a UX rec,
  ratified under S4.)*
  - **Poll mechanics (S4 frontend-UX review).** Poll only the OPEN run-detail
    (~3s) and **stop when the run is terminal** (`completed`/`failed`/
    `cancelled`); poll the list at a slower cadence (~10s) or via the existing
    global Refresh (`app.js:51,123-129`); **skip a poll if a fetch is
    in-flight**; **pause on `document.hidden`**.
  - **List IA columns.** status badge · `procedure_id` · `agent_id` · trigger ·
    `started_at` · duration/`updated_at` · step-progress.
  - **Detail IA.** Render the ordered `StepResult`s as a vertical stepper
    **reusing `O.reasoningTrace`** (`components.js:152-178`, exported) — map
    `reasoning_trace`/`audit`/`duration_ms` into its detail slot so it reads as
    an operational **timeline, not a log dump**; the `waiting_human` gate +
    `proposals[]` get a **distinct pinned panel ABOVE the trace**, not buried.
  - **`operate` seam.** The approve/reject/cancel controls live **INSIDE** that
    gate panel — structurally present-but-inert in v1 (mirror the
    `view-procedures.js` inert author-controls precedent, `mode:'read'|'edit'`
    at `view-procedures.js:12-14,33`); flipping `mode:'operate'` adds buttons
    wired to the already-shipped `POST /runs/{id}/gate/resolve`.
  - **Status legibility.** Reuse the semantic classes `s-ok`(completed) /
    `s-warn`(failed) / `s-info`(running) / `s-neutral`(cancelled), and give
    **`waiting_human` its own high-salience treatment** (the actionable status).
    *Caveat (verify before styling):* those classes are currently scoped to
    `.intake-pill` and the base CSS custom-props (`--ok` etc.) live in an
    as-yet-unread base stylesheet — **confirm/extend** before styling a new
    `waiting_human` badge.
  - **States.** Reuse `O.loadingState` / `O.errorState`
    (`components.js:196,202`); add a genuine **empty state** ("No runs yet") —
    do **NOT** route zero-rows through `errorState`.
  - **Operator stakeholder + demo.** Surface a **top-of-list count of
    `waiting_human` runs with age** ("is anything waiting on me right now, and
    for how long?"). The demo landing move: seed a `waiting_human` run and watch
    the detail pane flip `running → waiting_human` live via poll, with the gate
    panel + named proposals surfacing — narrating "same panel, one `mode` flip,
    becomes the approve button that calls an endpoint that **already exists**."

- **S5 — config-UI leg (ADR-016 Phase-3 third leg).**
  **Recommendation:** **defer out of v1** — keep v1 strictly read-only
  (monitor), stay forward-compatible. The config/edit surface already has a
  precedent path (`view-procedures.js` read-mode → PLAN-0040 edit-mode); the
  monitor's `mode: 'read' | 'operate'` seam keeps the door open without building
  it now.
  **ADR-worthiness:** NO — a deferral, not a decision; revisit as its own PLAN.
  **Ratified** (Cray s101, as-rec).

## Verification

- Offline oracle (the gate): AC-1/2/3/7/8/9 are `pytest` + `git diff` +
  `grep` reads, run first and fixed before any live/UI check (CLAUDE.md §8 "the
  offline oracle is the gate").
- UI evidence (AC-5/6): `preview_snapshot` + `preview_eval` geometry/text
  assertions (screenshot avoided — `project_preview_screenshot_timeout`).
- The monitor reads **real seeded persisted runs** end-to-end (list → detail →
  observe a gate-resolve advance the status), proving L4-i (no mock data) and
  L4-ii (the Control seam is exposed read-only over the same records).
