# PLAN-0052: ADR-016 Phase-3 OCT monitor (v1 — read-only pipelines list + live run detail)

**Status:** Draft
**Owner:** Claude Code (Tier 2 — all commits Code-exclusive per ADR-009 D2 / ADR-013 D2; drafted by the in-harness `plan-drafter` under ADR-013 D1 phased authoring)
**Created:** 2026-07-05
**Related ADRs:** ADR-016 (D7 Phase 3 — this PLAN builds its first increment; D2 `PipelineRun`/`StepResult` record shape the monitor reads; D3/D4 the approve→execute + `waiting_human` suspend/resume seam the Control leg extends; **OQ-2** scheduler = S1 below), ADR-007 (D2 `RecommendedAction` envelope — **unchanged**, L5), ADR-008 (ontology — **unchanged**, L5), ADR-012 (D4.3 author≠reviewer disclosure), ADR-013 (safe/human-gated autonomy posture; D1 phased authoring)
**Related PLANs:** PLAN-0019 (Phase 1 — shipped the `Procedure/Step/PipelineRun/Agent` primitive + persistence the monitor reads), PLAN-0039 (the read-only `GET /procedures` spec-viewer + `view-procedures.js` — the surface this monitor extends), PLAN-0047 (the run + gate-resolve HTTP seam in `services/api/routers/runs.py` — the Control write endpoint already on disk), PLAN-0010 (Ready — the two-poller harness autonomy loop; **not** the procedure scheduler — see S1), PLAN-0005 §8.1 (read-side audit / PDPA — relevant to S2)

> **Drafting provenance / Author≠reviewer disclosure (ADR-012 D4.3).**
> Outline originator = **Cray** (session 101: Option-1 greenlight that the
> artifact is a PLAN, the read-only v1 cut, and the load-bearing **L4**
> "monitor as a genuine Control-leg foundation, not a throwaway demo view"
> direction). Drafter = the in-harness **`plan-drafter`** subagent (ADR-013 D1
> phased authoring). Independent reviewer = **Code R2** at commit + **Cray** at
> the Ready gate (Draft → Ready flips only after Cray ratifies S1–S5). The
> drafter neither commits nor ratifies — separation is **INTACT**.

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
      `agent_id`, `status`, `started_at`, `updated_at`, step count) for the
      active vertical. *Pass/fail:* `pytest` a seeded-DB test asserts the shape +
      that a seeded `waiting_human` run appears with `status == "waiting_human"`.
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
      opens the detail view with the per-step trace. *Verify (UI):*
      `preview_snapshot` + `preview_eval` (no screenshot — see
      `project_preview_screenshot_timeout`); assert a seeded run row + a step-row
      count in the detail pane.
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
**Pass/fail:** seeded-DB `pytest` returns the seeded run in the list with correct
`status`; handler imports no writer symbol (grep). (AC-1, AC-3)

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
`view-procedures.js`). **Pass/fail (UI):** `preview_snapshot`/`preview_eval`
shows the seeded run row + step-rows in detail; grep for `mock` is empty (AC-4,
AC-5, AC-7).

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

## Surfaced Decisions / Open Questions (S1–S5 — Cray ratifies at Ready; do NOT silently resolve)

> Draft → Ready flips **only** after Cray ratifies these. Recommendations are
> load-bearing in the draft body but explicitly contingent on ratification.

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

- **S2 — service credential / principal for non-human triggers.** When a
  scheduled / non-human run fires, **who is the actor on the audit trail**
  (`PipelineRun.trigger_context` + per-step `audit`; `run_started` audit
  `actor_person_id`)?
  **Recommendation:** a **typed service-principal** (a first-class non-human
  `Person`-like actor with a stable id + declared scope), recorded in
  `trigger_context` and the audit `actor_person_id`, **never** an empty/`None`
  actor — so every automated write remains attributable under PDPA
  (PLAN-0005 §8.1).
  **ADR-worthiness:** **YES — likely an ADR amendment** (this is the one Cray
  flagged): it touches the audit/PDPA model and the SoD principal machinery
  (`step_principals`), and a "non-human but named" actor is a governance
  primitive, not a config detail. **Not in v1.**

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
  amendment).

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

- **S5 — config-UI leg (ADR-016 Phase-3 third leg).**
  **Recommendation:** **defer out of v1** — keep v1 strictly read-only
  (monitor), stay forward-compatible. The config/edit surface already has a
  precedent path (`view-procedures.js` read-mode → PLAN-0040 edit-mode); the
  monitor's `mode: 'read' | 'operate'` seam keeps the door open without building
  it now.
  **ADR-worthiness:** NO — a deferral, not a decision; revisit as its own PLAN.

## Verification

- Offline oracle (the gate): AC-1/2/3/7/8/9 are `pytest` + `git diff` +
  `grep` reads, run first and fixed before any live/UI check (CLAUDE.md §8 "the
  offline oracle is the gate").
- UI evidence (AC-5/6): `preview_snapshot` + `preview_eval` geometry/text
  assertions (screenshot avoided — `project_preview_screenshot_timeout`).
- The monitor reads **real seeded persisted runs** end-to-end (list → detail →
  observe a gate-resolve advance the status), proving L4-i (no mock data) and
  L4-ii (the Control seam is exposed read-only over the same records).
