# ADR-0019: `watch` → `gated`-proposal routing path (amends ADR-016 D3)

**Status:** Accepted *(Cray-ratified 2026-06-11)*
**Amends:** ADR-016 D3 — **extends** it (adds one sanctioned routing path); does **not** reverse, supersede, or renumber it. ADR-016 carries a forward pointer to this ADR.
**Consuming plan:** PLAN-0022 "tiered decision routing" (Ready) — § Execution Order **Phase 0**. This ADR is the **CLAUDE.md §8 governance gate** the PLAN-0022 implementation PR references and must merge before it.
**Provenance:** Drafted by Cowork (Tier-1, ADR-009 D1) off the Code-authored session-54 dispatch; **Code R2-reviewed + commits** (ADR-009 D2); **Cray ratified** — choosing OQ-1 form **(b)**, a first-class follow-on ADR rather than an in-place ADR-016 amendment.

---

## Context

PLAN-0022 (Ready for execution) renders Cray's two-axis reframe — *(design-time)
is the threshold clearly measurable × (runtime) is the data clear or ambiguous* —
into a tiered decision surface. Its load-bearing engine change routes the
deterministic **`watch`** (ambiguous-data) band to a human-escalation **proposal**
instead of leaving it a bare "go look."

Today — ADR-016 D3 plus the "Morning Pond Health Round" worked example — the
`watch` set routes to a bare **`human_task`**: a human is told to inspect, with
**no machine recommendation attached**. The autonomy primitives for "ambiguous →
human decides" already exist (a `gated` `action` *proposes* → D4 suspends the run
at `waiting_human` → `resolve_gated_step` applies the human's approve/reject) but
are wired only for the **breach** set. This ADR sanctions extending that same,
already-decided machinery to the `watch` band.

## Decision

**What this adds (one sanctioned routing path).** A `watch`-band (ambiguous-data)
object set MAY route to a **`gated` `action` proposal** — an LLM-backed `action`
step proposes a `RecommendedAction` (the ADR-007 D2 envelope, **unchanged**), the
run suspends at `waiting_human` (D4), and a human approves/rejects via the existing
gate — as a **sanctioned alternative** to routing the `watch` set to a bare
`human_task`. This is an extension of D3's *routing options*, not a change to the
autonomy primitive: the human still reviews the consequential write itself (a
`gated` `action`), exactly as for the `breach` set.

**Reuses existing machinery only — nothing new is introduced.** The path is built
entirely from primitives already decided in ADR-016:

- the existing **`gated` autonomy value** on an `action` step (D3) — the human reviews the consequential write;
- **D4's durable/resumable suspend** at `status = waiting_human` (asynchronous; hours-to-days OK);
- the existing **per-proposal approve→execute / reject** resolution on the gated step.

Explicitly, this ADR introduces **no new step `kind`**, **no new lifecycle
primitive or `PipelineRun.status` value**, and **no change** to the `auto`/`gated`
model, the `Agent.autonomy_ceiling`, or the `allowed` (step-kind + action-handler)
allowlist. A `watch`-routed `action` proposal is bounded by the **same** ceiling +
handler allowlist as any other `action` step — blast radius is unchanged.

**Determinism invariant (load-bearing).** The routing trigger is the
**engine-computed deterministic verdict** (`breach` / `watch` / `ok`) — a function
of authored thresholds over observed data — and **never** the LLM's `confidence`
or any model-derived "I'm unsure" signal. This binds **ADR-010 IN-3** (confidence
is *advisory*; surfaced to the reviewer, never gates automation) into the routing
layer: a model signal MAY be **shown** to the human at `waiting_human`, but it MUST
NOT decide whether a set escalates. Any future change that let a model signal route
the `watch` band is an **ADR-010 reopen** and must be surfaced as an explicit
decision, never made silently. (The deterministic `evaluate` executor that
*computes* the verdict is an **implementation prerequisite** — PLAN-0022 SD-6 —
**not** an ADR decision; this ADR asserts only that the verdict is engine-computed
and deterministic.)

**Updated worked example (Step 4).** In ADR-016's "Morning Pond Health Round",
Step 4 (the `watch` set) is amended from a bare `human_task` to a **`gated`
`action` proposal**: for the `watch` subset, an LLM-backed `action` step proposes a
`RecommendedAction` (a precautionary handler the author allowlists) → the run
suspends at `waiting_human` → the technician approves/rejects against a **concrete
machine recommendation**, rather than being told only "go look." Per **PLAN-0022
SD-1=a** (Cray-ratified 2026-06-11) the gated proposal **replaces** the
`human_task` for v1; **augment** — propose *and* still queue a visual-check
`human_task` — remains a per-procedure authoring option.

**Scope fence — what this ADR is NOT.** It is **not** a change to the D2 primitive
(the `Procedure / Step / PipelineRun / Agent` shape is untouched); **not** a new
autonomy level (the axis stays `auto` | `gated`); **not** an ADR-010 reopen
(ADR-010 stays untouched while the trigger is deterministic — see the invariant
above). It adds a *routing option*, nothing more. If implementation finds itself
needing to change the `auto`/`gated` model, the primitive, or the handler
allowlist, that **exceeds** this ADR and requires its own Cray decision.

## Consequences

**Positive.** The ambiguous (`watch`) band becomes actionable — a concrete LLM
recommendation a human ratifies — instead of a bare task or silence; the safety
posture is unchanged (still a human-gated write); the moat's auditability holds
(the escalation trigger is deterministic and engine-owned).

**Neutral / cost.** Requires the deterministic `evaluate` executor (PLAN-0022 SD-6)
as an implementation prerequisite; per-procedure authoring gains an optional
escalation-handler choice (PLAN-0022 Step 3 config surface).

**Guarded.** The determinism invariant is the load-bearing constraint: a future
change that lets `confidence` route is an ADR-010 reopen, to be made explicitly.

## Cross-references

- **PLAN-0022** (the consuming plan) — Step 2 `watch → gated` routing, Step 4 ADR
  touch-points, SD-1=a / SD-6, § Execution Order Phase 0.
- **ADR-016** — D3 (the autonomy model this extends), D4 (the durable/resumable
  `waiting_human` suspend this reuses), and the "Morning Pond Health Round" worked
  example.
- **ADR-010** — IN-3 (confidence advisory, never gates — the determinism invariant).

## Author≠reviewer disclosure (ADR-012 D4.3)

Authored by Cowork (Tier-1 governance-authoring) directly from the Code-authored
session-54 dispatch; its substance (the `watch → gated` path) was deliberated
upstream in PLAN-0022, which Cowork also drafted — so the independent-deliberation
check is **not** exercised within Cowork. The independent checks were **Code's R2
review** (re-verified the D3 + worked-example text and the determinism invariant
against HEAD `a6125c1`; confirmed the amendment stays an extension — no auto/gated,
primitive, ceiling, or allowlist change) and **Cray's ratification** (form OQ-1=b;
Status → Accepted). Drafter/ratifier separation intact — Cowork holds no commit
authority (ADR-009 D2).

---

*Follow-on ADR to ADR-016 (OQ-1 form b). AI-assisted per CLAUDE.md §8 — noted in
the commit body, never as `Co-Authored-By` (§7).*
