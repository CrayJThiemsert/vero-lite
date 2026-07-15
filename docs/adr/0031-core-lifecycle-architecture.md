# ADR-0031: Core lifecycle architecture — closed governed core + one typed seam per core

**Status:** Accepted
**Date:** 2026-07-14
**Ratified:** 2026-07-14 (session 130) by Jirachai Thiemsert (Cray), **per the recommendations** — **OQ-1..OQ-4 all resolved as-recommended** (via AskUserQuestion). Code R2 independently verified OQ-4 (the ADR-0025 D7 AT-2-generator CI marker is confirmed ABSENT on disk — only the principal-identity mirror `test_principal_identity_retrigger.py` exists).
**Deciders:** Jirachai Thiemsert (founder)
**Related:** ADR-006 (vertical plugin architecture — D3 maturity ladder, D4 Rule of Three), ADR-016 (governed procedure engine + amendments), ADR-0023 (registry auto-discovery / plugin maturity), ADR-0025 (AT-2 managerial layer — D7 re-trigger), ADR-0028 (schedule trigger), ADR-0029 (event-trigger bridge), ADR-0030 (economic-impact facet), ADR-011 (audit framework, deferred)

> **Drafting provenance (ADR-012 D4.3 / ADR-013 OQ-1).** Authored by the
> in-harness `plan-drafter` subagent under ADR-013 D1 phased authority
> (dispatch originated by Code, session 130 direction by Cray). Independent
> review: Code (R2) at PR, ratification: Cray. Author≠reviewer separation:
> **INTACT**. Uncommitted draft — Code commits per ADR-009 D2.

## Context

vero-lite's governed-procedure engine now spans four instrumented verticals
(energy, supply_chain, aquaculture, procurement) plus the procurement hero
demo. The engine has grown five distinguishable **cores**, each with its own
lifecycle: steps (ADR-016 D2), triggers (ADR-0028/0029), governance gates
(ADR-0025), run execution (PLAN-0047+), and audit (PLAN-0047 Step 5 minimal
slice; framework deferred to ADR-011).

Cray's session-130 direction — *"ปูพื้นให้กว้างที่สุด"* (lay the widest possible
foundation) — asks for the architectural groundwork that makes expansion to
arbitrary verticals efficient **without** dissolving the governance moat.
Two forces are in tension:

1. **The moat is governed correctness.** Typed, closed, deterministic,
   auditable decision spines — the reason a governed engine beats a generic
   workflow tool. Opening these to arbitrary plugin code would dissolve
   exactly the thing being sold ("governed ≠ generated").
2. **Vertical N must stay cheap** (ADR-006). Every hardcoded extension point
   makes onboarding a new vertical a core-engine engineering event instead of
   an authoring event.

Today the codebase already resolves this tension — but **implicitly**, with
two coexisting extensibility idioms that no ADR has ever named side by side.
Because they are unnamed, every new capability re-litigates "open registry or
closed enum?" from scratch, and each answer risks eroding one side (a
speculative plugin seam) or the other (a hand-edit hardcode). This ADR names
the idioms, states the principle they instantiate, and pre-designs — without
building — the seam each core will get when its trigger fires.

**This is a foundation/meta-architecture ADR. It builds NO seam.** Each seam
in D3 waits for its own N≥2 trigger and its own PLAN.

## Decision

### D1 — Name the two extensibility idioms vero-lite already has

**Idiom A — runtime registries (the data/handler axis — open, already
multi-vertical).** A per-process `VerticalRegistry` maps a vertical to its
`DataAdapter`, named action `Handler`s (+ descriptions), and a per-run
`ExecutorFactory` (`services/engine/registry.py:26-46`). Registration is
reached two ways: explicit calls (PLAN-0005 OQ-6) and the ADR-0023 L2
import-scan auto-discovery (`services/engine/discovery.py:37-73`), which
invokes each vertical's conventional `register_<ns>_adapter` /
`register_<ns>_handlers` entry functions plus the optional
`register_<ns>_economic_impact` producer (`discovery.py:76-92`; the producer
registry itself lives in `services/engine/economic_impact.py`, ADR-0030).
This axis carries **vertical-owned content** — data, handlers, ฿ producers —
and is deliberately open.

**Idiom B — closed typed governed enums (the governed-correctness spine —
deliberately hardcoded).** The decision spine is closed, typed, and
enumerated from observed need only:

- `StepKind` = {query, evaluate, action, human_task}
  (`services/engine/procedures/spec.py:54-60`)
- `Trigger` = {manual, schedule, event} (`spec.py:77-85`; each non-manual
  trigger's firing mechanism is built by its own PLAN — docstring, ibid.)
- `GateKind` = exactly the six observed decision kinds (`spec.py:200-211` —
  "no speculative future kinds, Rule-of-Three"; growth path = ADR-016 OQ-A1
  additive extension)
- `AT2Governance` = the discriminated typed-content union
  (`spec.py:703`; ADR-0025 D2 — a leaked variant is one test, not four)

Neither idiom is an accident, and neither is a defect to "fix" with the
other. Idiom A scales verticals; Idiom B **is the moat**.

### D2 — The principle: closed governed core + ONE typed, policy-carrying seam per core

vero-lite's answer to multi-vertical scale is:

> Each engine core stays a **closed, typed, governed grammar**. When real
> pressure (N≥2) demands extension, the core gains exactly **one**
> pre-designed seam — and that seam is **typed and auditable**
> (declaration-as-data), never arbitrary code.

- **NOT full-plugin.** An open "bring your own step/gate/trigger code" seam
  dissolves the governance moat: arbitrary code is not statically checkable,
  not audit-explainable, not authorable-as-data.
- **NOT full-closed.** Refusing all seams makes vertical N a core-engineering
  event and contradicts the ADR-006 vision.

**Cross-system convergence this generalizes** (prior art fed via dispatch):

- **AWS Step Functions** — a closed set of 8 state types; all extensibility
  funnels through one seam (the Task state's Resource ARN).
- **Netflix/Orkes Conductor** — closed operators + system tasks; exactly one
  open worker kind (`SIMPLE`). Note: `SIMPLE` is an *arbitrary-code* seam —
  right for a throughput orchestrator, **off-brand for a governed engine**;
  vero-lite's seams must stay declaration-as-data.
- **BPMN** — a closed task-type taxonomy; the service-task + connector is the
  typed extension seam; start events are a closed typed taxonomy.

**In-repo precedents already applying the principle** (this ADR generalizes
what these decided locally):

- ADR-0029 SD-3: the event→procedure binding is **authored in the vertical
  spec, not a code registry** — declaration-as-data chosen over a code seam.
- ADR-016 Q4 amendment (2026-07-09): multi-read queries got a **bounded,
  declared join/projection grammar**, explicitly *not* arbitrary SQL.
- ADR-0025 D2/D3: AT-2 content is a typed discriminated union with the
  bypass **unrepresentable** — governance content as data, not hooks.

**Moat tripwires** (greppable; any future PLAN proposing one of these is
contradicting this ADR and must supersede it explicitly):

1. An `eval`/exec or arbitrary-expression field in any authored spec.
2. An open worker-style StepKind (a Conductor-`SIMPLE` analog).
3. Untyped/free-form content registered onto the governed spine (gates,
   step kinds, triggers).
4. Flipping a closed governed enum to accept free strings.

### D3 — The seam map: current state → pre-designed seam → N≥2 trigger

The map is a **pre-designed response, not a build list**. Each row ships only
via its own future PLAN, when its own trigger fires (D4).

| Core | Today (verified 2026-07-14) | Pre-designed seam | N≥2 trigger |
|------|------|------|------|
| **Steps / StepKinds** | Closed enum (`spec.py:54-61`) + per-vertical executor registry — the enum now **includes `transform`** (`spec.py:61`; re-verified 2026-07-15). The typed declarative transform grammar is built + load-gated: `TransformSpec` + the anti-eval `derive` expression tree (`spec.py:414-511,688`), the shared `validate_transform_spec` load/compile predicate (`spec.py:662`), `TransformStepExecutor` (`services/engine/procedures/transform_step.py:197`). The two trigger cases — procurement `_SeedQuery` (`verticals/procurement/hero_demo/run.py:134`), supply_chain `_DispositionSeed` (`verticals/supply_chain/procedures_factory.py:93`) — remain execution-bound seed-side; their migration is the separate parity-guarded migration PLAN (PLAN-0077 SD-4), not PLAN-0077 | **Shipped — see PLAN-0077** (Phases A–C: schema + governance + load gate, compile + execute, fixtures + parity — all on `main`). Shipped v1 op-set: `derive` — a whitelisted **closed expression tree** (arithmetic {add, sub, mul, div, min, max} + compare {le, lt, ge, gt, eq} over `field`/`const` leaves; a bare field leaf = the typed copy; depth-bounded; arbitrary eval **unrepresentable by construction** — tripwire 1 honored); `map_value` — threshold-ladder banding (inclusive ceilings + mandatory unbounded top band); `default`; `rename`; `coerce` (`string \| decimal`). DEFERRED at zero concrete instances (PLAN-0077 L-7, Rule-of-Three): `unit_convert`, `extract`, `normalize`, `derive(concat)`, discrete key→value `map_value`, cardinality-changing nest/aggregate. The shipped set is a deliberate SUBSET of the pre-designed list — the exact op-set was delegated to the transform PLAN (OQ-1); subset-with-honest-deferral is in-authority (D4.2; "the map is a default, not a cage") | **Fired and shipped:** case 1 = procurement `_SeedQuery`, case 2 = supply_chain `_DispositionSeed` — both on disk; the seam shipped via PLAN-0077 |
| **Trigger / Intake** | Closed enum (`spec.py:77-85`) lifts in ~2 lines, but each trigger's **firing machinery is bespoke**: schedule = `scheduler.py` + `scheduler_daemon.py` + `scheduler_wiring.py` (ADR-0028); event = `event_bridge.py` (ADR-0029); manual = the API run path. No shared driver protocol exists (repo-wide grep: no `TriggerDriver`) | A **`TriggerDriver` protocol/registry** normalizing every trigger to ECA (`event + condition → run`), with the BPMN typed-start-event taxonomy as the closed kind-space: {manual, timer/cron, message/event, signal, data-ready/conditional, webhook, sub-procedure}. Note: human-task completion is **not** a trigger kind — it is a state change a data-trigger observes | A real **4th** trigger kind (webhook / message-queue / data-ready) demanded by a vertical |
| **Governance gate** | Adding a gate shape touches ≥4 coordination points: the `GateKind` member (`spec.py:200-211`), the typed content model + `AT2Governance` union arm (`spec.py:703`), a resolver module (`doa_tier.py` / `scored_rule.py` / `rule_gate.py`), and the wiring in `governance_step.py` + `derive_governance_todo` (`draft.py:271`) | A **governance-gate plugin unit**: content-model + resolver + obligation-contributor registered as ONE typed unit; plus **decision-as-data** — the DOA/scored-rule content is already DMN-shaped, so the decision table becomes a versioned, auditable artifact separate from control flow | The 2nd AT-2 signature (Path 2), per ADR-0025 D7's N≥2 re-trigger — the 4-edit pain bites exactly then. ⚠ D7's promised CI count-assertion was **not found** in `tests/` (only a mirror of the pattern, `test_principal_identity_retrigger.py:3,51`) — see OQ-4 |
| **Run / Execution** | Executor factories are registered but **NOT auto-discovered**: `_register_vertical` (`discovery.py:62-73`) wires `data_adapter` + `handlers` + optional `economic_impact` but never `register_<ns>_procedure_executors` — so a vertical 409s on live resolve/run until hand-wired at `main.py` | **Small seam:** fold `register_<ns>_procedure_executors` into `_register_vertical` as a fourth conventional entry function (completing the ADR-0023 L2 move; ADR-0023 L3 entry-points remain the far seam) | **Already N≥4** — every vertical needs it. Trigger has fired; timing is OQ-2 |
| **Audit** | Audited-event set is a free-text `action` string (`services/db/audit_log.py:78` — `Mapped[str]`, Text); no typed transition taxonomy | A **typed governance-transition taxonomy** (closed enum of audited transitions, additive growth like `GateKind`) | Low priority — deferred **with the ADR-011 audit framework** (retention/export/anchoring, gated on real partner data) |

### D4 — The fractal Rule-of-Three discipline

ADR-006 D4 ("concrete-first or nothing") applies **per core**, not just to
the vertical template: a seam is extracted only after **N≥2 concrete
instances press it** (two instances triangulate a shape; the third confirms
the abstraction — the same discipline that gates the AT-2 generator in
ADR-0025 D7 gates every seam above). Corollaries:

1. **The seam map is not a roadmap.** No PLAN may cite this ADR alone as
   justification to build a seam; it must also show its trigger fired.
2. **Each seam gets its own PLAN** with its own acceptance criteria; this ADR
   only pins the *shape* the PLAN must conform to (typed,
   declaration-as-data, one seam per core, moat tripwires honored).
3. **Enforceable triggers must be owned.** Where a trigger is promised as a
   CI marker, the PLAN that arms it must name the owning test + AC (Lesson:
   an unowned marker silently never gets built — ADR-016's N≥3 marker and,
   apparently, ADR-0025 D7's count-assertion; OQ-4).
4. When a seam lands, its PLAN **updates the D3 row** (current state moves,
   the seam column becomes "shipped — see PLAN-NNNN"). A stale map is worse
   than no map.

## Consequences

### Positive
- Future expansion is principled and cheap to *decide*: a new capability maps
  to a core, reads its row, checks its trigger — no re-litigating
  open-vs-closed each time.
- Both erosion modes are guarded: speculative plugin seams (moat dissolution)
  and hand-edit hardcodes (vertical-N cost) now contradict a named,
  ratified principle with greppable tripwires.
- The two idioms get a shared vocabulary; ADR-0029 SD-3 / ADR-016 Q4 /
  ADR-0025 D2 are revealed as one pattern, not three local choices.
- Pre-designed seams mean the eventual PLANs start from a ratified shape
  instead of a blank page.

### Negative
- Discipline cost: the map must be maintained (D4.4) or it rots into
  misinformation.
- A pre-designed seam can anchor prematurely: if the N≥2 instances press a
  *different* shape than pre-designed, the PLAN must feel free to deviate
  (the map is a default, not a cage) — deviation = amend this ADR's row.
- One more meta-ADR future sessions must read before touching a core.

### Neutral
- Zero code changes now. ADR-016's grammar, ADR-0025's union, ADR-0028/0029's
  trigger machinery all stand exactly as ratified.
- The AT-2 generator decision (ADR-0024 D7 / ADR-0025 D7) is untouched — the
  gate-seam row *reuses* its trigger, it does not modify it.

## Alternatives Considered

### Alternative 1: Full-plugin architecture (open seams everywhere now)
- Pros: maximal flexibility; vertical N never blocks on core.
- Cons: dissolves the governance moat — arbitrary code in steps/gates is not
  statically checkable, not audit-explainable, not authorable-as-data;
  contradicts ADR-016's "no speculative future kinds" and ADR-0025 D3's
  unrepresentable-bypass discipline.
- Why rejected: the moat IS the closed typed spine. Conductor's `SIMPLE`
  worker is the cautionary analog — right for Netflix, off-brand here.

### Alternative 2: Full-closed (no seams, extend every core by hand forever)
- Pros: zero speculative design; maximal short-term rigor.
- Cons: every new vertical shape becomes a core-engineering event (the gate
  4-edit pain, the executor hand-wiring 409s); contradicts ADR-006's
  cheap-vertical-N vision and the L2/L3 maturity ladder.
- Why rejected: it does not scale to "arbitrary verticals", which is the
  s130 direction this ADR exists to serve.

### Alternative 3: Build the seams now (this ADR as a build list)
- Pros: one coordinated construction pass; no trigger bookkeeping.
- Cons: violates ADR-006 D4 per-core (most seams are at N=1 or N=0);
  premature abstraction = wrong abstraction (the exact reason ADR-0024 D7
  deferred the AT-2 generator).
- Why rejected: Rule of Three is non-negotiable (ADR-006: "concrete-first or
  nothing").

### Alternative 4: Per-core ADR amendments instead of one meta-ADR
- Pros: each decision lives next to its core's ADR (016/0025/0028…).
- Cons: the principle is *cross-core* — scattering it re-creates the current
  state (three local choices, no named pattern); amendment sprawl on ADR-016
  is already heavy.
- Why rejected: the value here is the single seam-map + shared vocabulary;
  per-core PLANs will still amend their own ADRs when seams ship (SD-3 /
  OQ-3 records the relationship).

## Open Questions

All four resolved at ratification (Cray, session 130, via AskUserQuestion —
all as-recommended). Original recommendation text preserved for the
reasoning lineage; the RESOLVED line is the binding outcome.

- **OQ-1 (= SD-1).** Is the `transform` `derive`-op expression-grammar
  boundary fixed by THIS ADR or by the transform PLAN? **Recommendation:**
  this ADR binds only the *constraint* (whitelisted
  arithmetic/concat/compare; never arbitrary eval — tripwire 1); the exact
  op-set and grammar surface belong to the transform PLAN, designed against
  the two concrete cases.
  **RESOLVED (Cray, s130):** as recommended — this ADR binds only the
  `derive` *constraint* (whitelisted arithmetic/concat/compare; never eval —
  tripwire 1); the exact op-set + grammar surface belongs to the transform
  PLAN, designed against the two concrete cases.
- **OQ-2 (= SD-2).** The executor auto-discovery fold-in is already N≥4 —
  exempt it from "wait for trigger" and do it as near-term cleanup, or batch
  it with the next vertical onboarding? **Recommendation:** exempt — the
  trigger has already fired; a small standalone PLAN/chore is low-risk
  anytime. Cray's call because it schedules work and changes live-wiring
  behavior (removes a known 409 class).
  **RESOLVED (Cray, s130):** as recommended — the fold-in is exempt from
  wait-for-trigger (already N≥4); ship it as a small standalone chore PLAN,
  timing flexible (may bundle with Path 2).
- **OQ-3 (= SD-3).** Relationship to ADR-016: supersede, amend, or extend?
  **Recommendation:** extend — mirror ADR-0025's "extends, does not
  supersede" stance. ADR-016 remains authoritative for the Step grammar;
  this ADR governs the cross-core principle. No annotation edit to ADR-016
  now (it is Accepted; a cosmetic cross-ref is not worth the G1 route).
  **RESOLVED (Cray, s130):** as recommended — this ADR **extends** ADR-016
  (does not supersede or amend); ADR-016 stays authoritative for the Step
  grammar; NO annotation edit to ADR-016's body.
- **OQ-4.** ADR-0025 D7 promised an enforceable CI assertion counting
  AT-2-class procedures; a repo-wide grep (2026-07-14) found no such marker
  in `tests/` — only `test_principal_identity_retrigger.py` *mirroring* the
  pattern for a different deferral. The gate-seam trigger (D3 row 3) leans
  on D7. **Recommendation:** verify + arm the marker (naming the owning test
  + AC) either as a tiny standalone chore or as AC-1 of the future gate-seam
  PLAN — per D4.3.
  **RESOLVED (Cray, s130):** confirmed on disk (Code R2 independent
  verification) that ADR-0025 D7's AT-2-generator CI count-assertion was
  never built. Arm it as an acceptance criterion of the future gate-seam /
  Path-2 PLAN — the PLAN that adds the 2nd AT-2 signature owns the marker,
  naming its test + AC (D4.3). Recorded as a known-open remediation, not
  blocking this ADR.

## References

- ADR-006 — vertical plugin architecture (D3 L1/L2/L3 ladder; D4 Rule of Three)
- ADR-016 — governed procedure engine (D2 grammar; OQ-A1 additive enum growth; Q4 join-grammar amendment, esp. :1094-1097 "downstream transform step")
- ADR-0023 — registry auto-discovery (L2 import-scan; L3 entry-points as future seam)
- ADR-0025 — AT-2 managerial layer (D2 typed union; D7 N≥2 re-trigger)
- ADR-0028 / ADR-0029 — schedule + event triggers (per-PLAN bespoke firing)
- ADR-0030 — economic-impact facet (opt-in producer registration, `discovery.py:76-92`)
- Code anchors (verified 2026-07-14): `services/engine/procedures/spec.py:54-60,77-85,200-211,703`; `services/engine/registry.py:26-46`; `services/engine/discovery.py:37-92`; `services/db/audit_log.py:78`; `verticals/procurement/hero_demo/run.py:133-159`; `services/engine/procedures/{scheduler,scheduler_daemon,scheduler_wiring,event_bridge}.py`; `services/engine/procedures/draft.py:271`
- Prior art (via dispatch): AWS Step Functions state taxonomy; Netflix/Orkes Conductor operator/system/`SIMPLE` task model; BPMN task-type + start-event taxonomies; DMN decision-as-data separation
