# PLAN-0015: Wire the decision loop onto the Operational Timeline (live-time demo)

**Status:** Draft
**Owner:** Claude Code (executor) — design ratified interactively by Cray (session 31)
**Created:** 2026-06-03
**Related ADRs:** ADR-005 (OCT), ADR-006 (vertical plugin), ADR-007 (RecommendedAction + recommend→approve→execute loop), ADR-010 (LLM brain-swap + rule fail-safe)
**Related Plans:** PLAN-0013 (OCT stakeholder demo, done) — this extends the demo's Screen A timeline (#129/#130/#132) + Screen B decision loop.

> **Provenance (ADR-012 D4.3).** Drafted by **Code** from a session-31 interactive
> design conversation with Cray; the decisions D1–D5 below were **Cray-chosen this
> session** (two AskUserQuestion forks: "events use real time anchored to server
> run" + "recovery is the effect of Execute"). Author = Code; the independent
> check is Cray's interactive ratification. Code commits + executes (ADR-009 D2).

## Goal

Make the demo play as a **live incident → human decision → resolution** loop that
is visible end-to-end on the Screen A **Operational Timeline**. Today the timeline
shows the synthetic events at fixed 2026-05-21 timestamps, and Screen B's
Approve/Execute changes nothing in Screen A. After this plan: each `uvicorn` run
anchors the incident to **real time** (the breach is "just now"), and approving →
executing the decision in Screen B **records real click-times**, makes the
breach **resolve** on the map + timeline, and lands a **recovery reading** as the
visible effect of the executed action — so a stakeholder watches the governance
loop close in real time.

## Decisions baked in (Cray-ratified, session 31 — do not re-surface)

| # | Decision |
|---|----------|
| **D1** | **Real-time event anchoring.** On each server run the active vertical's `OperationalEvent` timestamps are shifted so the incident is recent (the **breach ≈ server-start "now"**), preserving the original relative spacing. Anchored once at startup (stable for the session); reset every run. |
| **D2** | **Recovery is the effect of Execute, not pre-baked.** The 58 °C "returning to safe range" reading is **removed from the always-present events**; it is injected **when the action is executed** (occurred_at = real execute-time), so the timeline only resolves after the operator acts. |
| **D3** | **Decision timestamps are server-side + real.** `approve()` / `execute()` record `approved_at` / `executed_at` (UTC now) on the action; `/recommendations` exposes them (+ status). |
| **D4** | **Resolved state on Execute.** On `executed`, the breach marker (timeline) + the map glow/ring go from pulsing-red (active) to **resolved (green / ✓)**, and a decision-status badge (proposed → approved → executed) sits with the breach. Approve alone shows the intermediate "approved" state; **Execute** is what resolves. |
| **D5** | **Determinism is preserved for tests.** Anchoring (D1) is gated behind a setting (`oct_demo_time_anchor`, env `OCT_DEMO_TIME_ANCHOR`, **default off**). Tests run with it off (fixed datetimes, reproducible — the `synthetic.py` "no randomness" contract holds); the demo box runs with it **on**. |

## Acceptance Criteria

- [ ] **AC-anchor** — with `OCT_DEMO_TIME_ANCHOR=true`, a fresh `uvicorn` run serves
      `OperationalEvent.occurred_at` shifted so the breach ≈ the run's start time
      (±1 min), with the original relative spacing preserved; a second run shifts
      again (anchored to the new start). With the flag off, timestamps are the
      fixed 2026-05-21 values (tests unchanged).
- [ ] **AC-decision-time** — after `POST /approve` then `/execute`,
      `/recommendations` returns the action with `status: executed`, a real
      `approved_at`, and a real `executed_at` (both ≈ click time, ordered).
- [ ] **AC-recovery-on-execute** — before execute, `/objects/OperationalEvent`
      contains **no** recovery reading and the breach is unresolved; after execute,
      a recovery reading (safe-range value, occurred_at ≈ execute-time, affected
      asset) is present.
- [ ] **AC-resolved** — after execute, returning to Screen A shows the breach
      marker + the map node as **resolved** (not pulsing red), the
      decision-status badge reads `executed`, and the recovery marker + the
      `approved`/`executed` markers appear at their real times on the rail.
- [ ] **AC-approve-intermediate** — after Approve (no Execute), Screen A shows the
      decision as `approved` (intermediate), the breach **not** yet resolved, no
      recovery reading.
- [ ] **AC-template** — the anchoring + decision-time wiring is ontology/config
      driven (timestamp + severity from `/meta`; the recovery value/asset from the
      `OCT_RECOMMEND_*` policy), so `OCT_VERTICAL=supply_chain` behaves the same
      with zero per-vertical UI code.
- [ ] **AC-tests** — full suite green with the flag off (deterministic); new tests
      cover the anchor shift, the decision timestamps, and the recovery injection.

## Out of Scope

- ❌ Persisting the anchored times or decision history across restarts (each run
      resets — D1/D5).
- ❌ A real recovery-producing handler (the `echo` handler stays; the recovery
      reading is the demo's modeled effect, not a physical control action).
- ❌ Live push/websocket updates while the operator stays on Screen B — Screen A
      reflects the new state on next navigation (mount re-fetches `/recommendations`
      + `/objects`). A live cross-view refresh is a possible fast-follow.
- ❌ Multi-incident / multi-decision timelines — one breach + one decision (the
      current synthetic scenario).

## Steps

### Step 1 — Backend: real-time anchoring (D1, D5)
Add `oct_demo_time_anchor: bool` to settings. In the data-adapter serving path
(generic over the active vertical's `OperationalEvent` timestamp prop), when on:
capture a base = app-startup time once, compute `delta = base − breach_event_time`,
and shift every event's `occurred_at` by `delta`. Off → unchanged. Tests force off.

### Step 2 — Backend: decision timestamps (D3)
Record `approved_at` / `executed_at` (UTC now) on the `ActionRecord` in
`approve()` / `execute()`; surface them on `RecommendationResponse` +
`/recommendations`.

### Step 3 — Backend: recovery as the effect of Execute (D2)
Remove the pre-baked recovery reading from the base events. Give the energy (and
supply_chain) adapter a per-process mutable event list; on `execute()`, append a
recovery `OperationalEvent` (occurred_at = now, safe-range value, affected asset
from the `OCT_RECOMMEND_*` policy). `/objects/OperationalEvent` then includes it.

### Step 4 — Frontend: timeline + map reflect the decision (D4)
The map view reads each recommendation's `status` + `approved_at` / `executed_at`:
add `approved` / `executed` markers at those real times on the rail; show a
decision-status badge with the breach marker; on `executed`, render the breach
marker + the map node as **resolved** (green/✓, stop the red pulse). The recovery
reading (Step 3) appears on the rail naturally once present.

## Verification

- **Live, not mocked (Lesson #15).** Run with `OCT_DEMO_TIME_ANCHOR=true`; capture
  via Claude Preview: (a) breach ≈ start time; (b) before execute — no recovery,
  breach pulsing red; (c) Approve → intermediate `approved`; (d) Execute →
  `executed_at` real, recovery reading present, breach + map node resolved,
  decision markers on the rail.
- **Determinism.** Full suite green with the flag off; new unit tests for the
  anchor shift (flag on/off), the decision timestamps, and the recovery injection.
- **Template proof.** `OCT_VERTICAL=supply_chain` exhibits the same behavior with
  no per-vertical UI change.

---

*Code-drafted from the session-31 interactive design (Cray-ratified D1–D5);
uncommitted Draft until Code commits per ADR-009 D2. Synthetic data only.*
