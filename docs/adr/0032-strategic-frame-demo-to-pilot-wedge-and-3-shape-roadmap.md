# ADR-0032: Strategic frame — the demo→pilot wedge + the 3-shape roadmap

**Status:** Accepted
**Date:** 2026-07-16
**Deciders:** Jirachai Thiemsert (founder). The six decisions below were
Cray-ratified **in substance** in-session (2026-07-16, "เอาครบ 6" — all six,
verbatim scope) after ~5 rounds of 4-specialist panels across sessions
136–137; **OQ-1..OQ-4 were ratified 2026-07-16 via AskUserQuestion — all
as-recommended** (the resolved record is in Open Questions below). Status
flipped to `Accepted` in the same pass that folded the resolutions (house
rule: never flip Status then edit body — G1).
**Related:** ADR-005 (strategic pivot — the precedent that a *strategic*
decision belongs in an ADR), ADR-006 (vertical plugin architecture; D4 Rule
of Three), ADR-0015 (two-tier vertical onboarding — D1's "pre-build in their
shape" leans on it), ADR-0020 (partner-sim guarded trial — partner-facing
method), ADR-0025 (AT-2 managerial layer; D7 deferred generator +
re-trigger — shape 2's capstone), ADR-0030 (Box-4 economic-impact facet —
D1's ฿-charter leans on it), ADR-0031 (core lifecycle architecture — closed
governed core + one typed seam; the moat constant all three shapes inherit),
PLAN-0074 (SD-3 — the performed N=2 re-evaluation), PLAN-0076 (AT-2
follow-on tracking)

> **Drafting provenance (ADR-012 D4.3 / ADR-013 OQ-1).** Authored by the
> in-harness `plan-drafter` subagent under ADR-013 D1 phased authority
> (dispatch originated by Code; strategic substance originated by Cray +
> the session-136/137 specialist panels). Independent review: Code (R2) at
> PR; ratification: Cray. Author≠reviewer separation: **INTACT**.
> Uncommitted draft — Code commits per ADR-009 D2.

## Context

### The problem this ADR closes

Session 137 produced a full strategic direction — the demo→pilot wedge, the
3-shape roadmap, the positioning frame, the workflow fit filter — via ~5
rounds of blind 4-specialist panels, converged and then Cray-ratified in
substance. **None of it was repo-tracked.** It landed only in Tier-0
auto-memories and **gitignored** `docs/{research,strategy}/private/` files.
The consequence was verified on disk the same day: a parallel session (138)
planned its next work with zero visibility of the direction; the frame was
in **no** ADR, **no** PLAN, and **no** STATUS Active TODO (session-137
ADDENDUM handoff §1/§6). Since `CLAUDE.md` §9 reads `docs/adr/` at every
session start, an ADR is the one artifact class that makes a strategic frame
first-class and session-visible. ADR-005 (the vet→OCT pivot) is the standing
precedent that strategy of this magnitude is ADR material.

### Where vero-lite stands (grounded 2026-07-16)

- **Shape 1 is shipped.** The governed `monitor→decide→approve→act` engine
  runs across four fully-instrumented synthetic verticals — electrical grid
  (energy), cold-chain (supply_chain), aquaculture biology, and money
  (procurement + its bespoke governed hero) — plus a fifth **Tier-1 Mirror**
  (ADR-0015 D2), `verticals/building_materials/` (#765): scaffolded guessed
  ontology, `echo` handler stub, **no `procedures.yaml`**, live-verified on
  the deterministic rule path. Its governed-credit hero is **not built** and
  is deliberately **not scheduled by this ADR** (a separate tracking-stub
  PLAN will home it).
- **AT-2 state (fact-critical — a stale version of this cost a PR, #767):**
  AT-2 is **N=2** — procurement (`emergency_sourcing_round` + its
  schedule/event variants = **one** signature, money / `doa_tier`) and
  supply_chain (cold-chain disposition, non-money / `severity_tier`,
  PLAN-0074). The ADR-0025 D7 CI re-trigger **fired at N=2** and the
  re-evaluation was **performed** (PLAN-0074 SD-3 — the generator stays
  deferred; **N≥2 permits genericization, it does not mandate it**). The
  marker **re-arms at N=3**
  (`tests/services/engine/procedures/test_at2_signature_retrigger.py`;
  grounded at `services/engine/procedures/spec.py:822-830` as corrected by
  #767).
- **Partner-facing capability is further along than older gap-docs said:**
  NL-query is built (`services/api/routers/query.py`,
  `services/engine/nl_query.py`) and a real per-vertical CSV adapter exists
  (`verticals/procurement/data_adapter/fastenal_csv.py`). The genuine gap is
  the dbt/SQLMesh auto-canonicalization layer — a funded Phase-2
  deliverable, never a pilot precondition.

### Public-repo boundary

This repository is public. This ADR carries the **strategic/architectural
frame only**. Partner-identifying content, pricing, and GTM operational
detail stay in the gitignored companions, referenced here **by path only**
(established house practice): the strategy synthesis
`docs/strategy/private/2026-07-16-demo-to-pilot-strategy-synthesis.md`, the
partner one-pager
`docs/research/private/2026-07-16-partner-onboarding-wedge-onepager.md`, and
the hero-shaping checklist
`docs/research/private/2026-07-16-hero-shaping-checklist.md`.

## Decision

Six decisions, ratified in substance as a set. D1 is the immediate motion;
D2–D4 the roadmap; D5–D6 the framing discipline that keeps D1 repeatable.

### D1 — The wedge: a sharpened HERO-FIRST ("guess-then-react")

The demo→pilot motion opens by **pre-building a *guessed* governed hero in
the partner's own shape** and asking them only to **correct** it — reacting
is far lower-friction than supplying, and it inverts the #1 enterprise fear
("why hand you our data"). Five binding elements:

1. **Zero partner data at first contact.** The first meeting requires no
   files, no PII, no legal documents — only 30–45 minutes correcting our
   guess (approval chain, authority limits, thresholds, a real incident
   narrative).
2. **Guess in their shape, on the shipped machinery.** The Tier-1 Mirror
   path (ADR-0015 D2, `vero-lite new-vertical` + ontology YAML + regen) is
   config-cheap; a bespoke governed hero mirrors
   `verticals/procurement/hero_demo/`. Zero engine build either way — but
   an AT-2-gated hero carries the D6 cost caveat (it is signature #3, not
   config-cost). Every guessed value is marked "guess — correct me."
3. **Run the deterministic offline arm.** No live-model or network
   dependency in the room — a hiccup cannot collapse the demo (this also
   keeps the demo inside the §8 host-state discipline: no live run needed).
4. **Bind the pilot to a 1-KPI, 6-week charter.** Pre-agreed success
   criteria, one measurable KPI — the economic framing rides the typed ฿
   facet (ADR-0030) with assumptions-first discipline
   (`services/engine/economic_impact.py`), every figure labeled PROVISIONAL.
5. **Enter via an existing executive relationship**, name the synthetic-data
   limit first, keep everything on-prem (trust + PDPA + residency at once).

The panel-unanimous load-bearing risk: a wrong-shaped guess reads as "you
don't understand our business." Mitigation = the hero-shaping checklist
(private companion), with D6's fit filter as its step 0. The data-onboarding
ladder (zero data → static pseudonymized cut → live feed) is the operational
form of this decision; it lives in the private one-pager, not here.

### D2 — The 3-shape roadmap, and the single pilot gate

vero-lite's evolution is three shapes, each governed (human approves,
audited, on-prem, no arbitrary-code escape — the ADR-0031 moat constant that
makes the three compose):

- **Shape 1 — governed workflow** (`monitor→decide→approve→act`): **shipped**
  (see Context). The immediate job is D1.
- **Shape 2 — governed self-improvement** (D3): the moat's second act.
- **Shape 3 — governed agent-interop** (D4): parked.

**All three gate on ONE thing: a real pilot.** Shape 2 needs real run-volume
as fuel (synthetic verticals cannot feed an improvement loop with honest
signal); shape 3 needs a real counterparty. The wedge (D1) is the unlock for
the entire arc. No shape-2 or shape-3 build work is scheduled by this ADR.
**The gate is binding, with a named escape** (OQ-1, ratified): a future
shape-2 or shape-3 PLAN must cite a live pilot, or record Cray's explicit
in-session override in the proposing PLAN itself. It is not a soft
observation.

### D3 — Shape 2 is GOVERNED self-improvement, not autonomous

The naive thesis "self-improving system → recurring vendor need" is
**refuted** (it erodes vendor need and repels audit-driven buyers). The
ratified form:

- The loop **SURFACES** typed improvement proposals from captured feedback —
  the audit hash-chain, reasoning traces, approve/reject decisions (free
  tier-stamped human labels), and the ฿ facet.
- A **human approves each proposal** through the same
  `monitor→decide→approve→act` spine. Every self-change is itself governed
  and audited. No self-applying change exists.
- **Recurring vendor need flows from the LIMITS on self-improvement** — the
  closed typed spine (ADR-0031), the permanent human-approval layer, and
  vendor-built new governed shapes — NOT from autonomy.

Relationship to AT-2: shape 2 is the AT-2 generator **recursed** (input
widened from a founder narrative to the ontology's own feedback stream). It
does **not** reopen the ADR-0025 D7 / PLAN-0074 SD-3 decision — the
generator stays deferred, the marker re-arms at N=3, and this ADR schedules
nothing against it. Shape 2 names the direction that work grows toward once
D2's pilot gate supplies fuel.

### D4 — Shape 3 (governed agent-interop) is PARK

Hold shape 3 as a **cheap option plus one vision-slide line** — do not
build. The seeds already on disk (the MCP emitter, the audit hash-chain)
require no further investment to keep the option alive. The near-term
concrete framing, when it is ever raised, is a **bilateral governed
exchange** with a full audit trail — never a network / "AGI-ready" story
(see D5).

**Moat rule (never cross): read-only + on-prem + governed + human-approved —
never an ungoverned data-sharing escape hatch.** This extends ADR-0031's
tripwire discipline from the engine's internals to the system's data-egress
boundary. The rule is **homed here only** — ADR-0031's body is not amended
(OQ-3, ratified; mirrors ADR-0031 OQ-3's own no-cosmetic-edit stance).

**Un-park trigger:** a real counterparty's *written* pilot-condition pull —
nothing softer. The vision-slide line is placed only AFTER the hero demo
lands (D5).

### D5 — Positioning: "governed = AI-ready today" + the DIY-ceiling

Lead with **"governed = AI-ready today"** and the **commodity-AI
DIY-ceiling**: commodity AI can draft the memo, but it cannot **own** a
governed, authority-gated, tamper-evidently-audited decision — *"the AI
decided" is not an answer an auditor accepts*. That ownership layer (DOA +
SoD + hash-chained audit + reasoning trace, all shipped) is what a buyer
cannot assemble from commodity parts, and it is consistent with the standing
"governed ≠ generated" moat line and the §8 assistive-AI posture.

Never say **"AGI-ready"** or **"self-modifying"** to an operations buyer —
both repel the actual buyer and misstate D3. The vision slide (shapes 2–3)
appears only **after** the hero demo lands.

### D6 — Qualify by SHAPE, not domain

vero-lite is not a general workflow platform; it is a
`monitor→decide→approve→act` engine, and partner qualification runs on a
**4-question fit filter** applied to the *painful workflow*, before any
build:

1. Is there a locatable **asset**?
2. Does it emit a **numeric stream**?
3. Is "anomaly" defined by a **threshold/band**?
4. Is the outcome a **governed approval action** (DOA/SoD)?

**Domain is free; the shape is not.** The four fully-instrumented verticals
span electrical grid / cold-chain / aquaculture biology / money — and the
building_materials mirror extends the reach to a *commercial* asset
(`CustomerAccount` with its own credit band, the ADR-008 "may extend"
precedent) — the shape generalizes across wildly different domains at
config cost.

- **All four YES → proceed.** Mirror ≈ days; a bespoke **non-AT-2** hero
  (AT-1 anomaly→action / AT-3 calm-path) ≈ 1–2 weeks, zero engine build.
  An **AT-2-gated** hero (money `doa_tier` or non-money `severity_tier`) is
  a **different cost class**: it is AT-2 signature **#3** — it trips the
  re-armed marker, turns CI RED, and obligates the ADR-0025 D7
  re-evaluation (see the Context AT-2 paragraph) — never scope it as a
  config-cost item.
- **Any NO → reshape, don't accept.** Non-fitting archetypes — multi-party
  negotiation, scheduling/optimization (a solver is un-declarable-as-data, an
  ADR-0031 tripwire), document/OCR extraction (parked since ADR-005) — get
  the conversation **reshaped to the fitting *slice*** of the partner's
  operation, never adopted whole.
- **Adopting a new workflow archetype** (a new typed core per ADR-0031 /
  ADR-016 OQ-A1 additive growth) requires a **Rule-of-Three signal or a
  paying anchor partner** whose core pain genuinely is that archetype and
  cannot be resliced — and even then, land on the fitting slice first, then
  expand as paid Phase-2 work. The anchor-partner trigger *commissions a
  PLAN*; that PLAN still conforms to ADR-0031's shape constraints (typed,
  declaration-as-data, tripwires honored). This reading is **confirmed as
  intended** (OQ-4, ratified): an anchor partner commissions a *concrete
  additive archetype* (ADR-016 OQ-A1 growth from observed need), not the
  *abstraction/seam extraction* that ADR-0031 D4's N≥2 gates — a future
  archetype PLAN may lean on it.

## Consequences

### Positive

- The strategic frame is repo-tracked and session-visible (CLAUDE.md §9):
  parallel sessions and planning subagents can no longer plan blind to it —
  the exact failure verified in session 138.
- D6 gives every future partner conversation a cheap, binding qualification
  step; wrong-shaped pursuits are refused *by rule*, not by mood.
- D5 removes a demonstrated self-sabotage channel ("AGI-ready" framing) from
  partner-facing material by rule.
- D2's single gate stops speculative shape-2/shape-3 build pressure cold: any
  PLAN proposing such work must show a real pilot (or cite OQ-1's resolution).
- The AT-2 fact record (N=2, fired, performed, re-arms at N=3) is now stated
  in an ADR, making the stale-N-count class of error (the one #767 killed)
  harder to reintroduce.

### Negative (the honest costs)

- **D4 parks a capability whose seeds already exist.** The MCP emitter and
  audit hash-chain are on disk; the option cost is near-zero but the
  opportunity cost is real — a competitor could establish governed-interop
  precedent first, and the written-pull trigger means we are structurally
  *reactive* on shape 3.
- **D6 narrows the addressable market by design.** Named archetypes
  (negotiation, optimization, extraction) are walls even when a prospect
  asks — revenue conversations will be reshaped or declined.
- **D2 concentrates the entire roadmap on one gate.** Shapes 2 and 3 both
  starve until a single wedge motion succeeds; there is no parallel path.
- **D1 carries reputational risk by construction** — a wrong-shaped guess in
  the first meeting damages exactly the relationship it entered through; the
  mitigation is a checklist, not a mechanism.
- **A strategic ADR can rot.** GTM learning moves faster than governance
  artifacts; mitigated by keeping the operational detail (ladder rungs,
  meeting mechanics, sector boxes) in the private companions and pinning only
  the frame here — but the frame itself must be superseded, not silently
  drifted, when learning contradicts it.

### Neutral

- Zero code changes. ADR-0025 D7 / PLAN-0074 SD-3 stand untouched; the
  building_materials Tier-1 Mirror stands as shipped and needs nothing.
- The governed-credit hero remains unscheduled — it is neither claimed as
  built nor put in a backlog by this ADR (its true cost is coupled to the
  N=3 obligation; a separate tracking-stub PLAN homes it).
- The gitignored companions remain canonical for partner-facing operational
  detail; this ADR does not absorb them.

## Alternatives Considered

### Alternative 1: Status quo — auto-memories + gitignored private docs
- Pros: zero governance overhead; already written; free to iterate.
- Cons: invisible to fresh sessions, parallel sessions, and planning
  subagents — a **verified** failure mode (session 138 planned blind);
  auto-memories are private to one machine/agent and carry no precedence.
- Why rejected: it already failed, observably, within one day.

### Alternative 2: STATUS Active TODO / narrative block
- Pros: lightweight; session-visible.
- Cons: STATUS is state, not rules (§1 precedence — it never wins a
  conflict); Current Focus blocks record *what happened*, not standing
  direction; TODOs compress a frame to a one-liner and get archived.
- Why rejected: a multi-year strategic frame homed in the most volatile
  artifact in the repo.

### Alternative 3: A conventions doc (`docs/conventions/`)
- Pros: right home for a *lookup standard*; D6's filter is checklist-shaped.
- Cons: conventions carry lower precedence than ADRs and record standards,
  not decisions; the wedge/roadmap/park calls are decisions with reversal
  costs.
- Why rejected for the frame as a whole; **partially open** for D6's filter
  as a derived operational checklist — surfaced as OQ-2.

### Alternative 4: A PLAN
- Pros: PLANs are the executable-work artifact.
- Cons: no acceptance criteria or steps exist here — this is direction, not
  execution; completed PLANs archive to `done/`, which would bury the frame;
  each future concrete motion (hero PLAN, shape-2 loop PLAN) gets its own
  PLAN citing this ADR.
- Why rejected: wrong artifact shape for standing direction.

## Open Questions

All four resolved at ratification (Cray, 2026-07-16, via AskUserQuestion —
all as-recommended). The original question + recommendation text is
preserved for the reasoning lineage; the RESOLVED line is the binding
outcome.

- **OQ-1 (= SD-1).** Is D2's "all three shapes gate on a real pilot" a
  **binding constraint** (a future shape-2/3 PLAN must cite a live pilot or
  supersede this ADR) or a **strategic observation** (strong default,
  overridable by Cray in-session)? Recommendation: binding-with-named-escape
  — binding, with Cray's explicit in-session override recorded in the
  proposing PLAN; a soft observation would not have stopped the speculative
  pressure this ADR exists to stop.
  **RESOLVED (Cray, 2026-07-16):** as recommended — **binding with a named
  escape**. A future shape-2/shape-3 PLAN must cite a live pilot, or record
  Cray's explicit in-session override in the proposing PLAN itself. Not a
  soft observation. (Folded into D2.)
- **OQ-2 (= SD-2).** Should D6's 4-question fit filter *also* be published as
  a derived checklist in `docs/conventions/` (canonical stays here, per the
  ADR-0017 D6 derived-artifact rule)? Recommendation: not yet — one artifact
  until a second consumer (a real qualification conversation) demands a
  standalone form; Rule-of-Three applies to docs too.
  **RESOLVED (Cray, 2026-07-16):** as recommended — **not yet**. The filter
  stays canonical here only; no derived `docs/conventions/` checklist until
  a second real consumer (an actual qualification conversation) demands a
  standalone form. Rule-of-Three applies to docs too.
- **OQ-3 (= SD-3).** D4's moat rule reads as a *data-egress-boundary* analog
  of ADR-0031's engine-internal tripwires. Should it be (a) recorded only
  here, or (b) added to ADR-0031's greppable tripwire list (an Accepted-body
  edit, G1-routed)? Recommendation: (a) — mirror ADR-0031 OQ-3's own stance
  ("no annotation edit to an Accepted ADR for a cross-ref"); this ADR is
  greppable on its own.
  **RESOLVED (Cray, 2026-07-16):** as recommended — **(a), here only**.
  ADR-0031's body is NOT amended (no Accepted-body edit for a cross-ref).
  (Folded into D4.)
- **OQ-4 (= SD-4).** D6's "paying anchor partner" trigger admits a new
  archetype at N=1, while ADR-0031 D4 gates *seam extraction* at N≥2. The
  reading taken here: consistent — an anchor partner commissions a *concrete
  addition* (ADR-016 OQ-A1 additive growth from observed need), not an
  *abstraction extraction*; ADR-0031's shape constraints still bind the
  PLAN. Cray to confirm this reading is the intended one, since a future
  PLAN will lean on it.
  **RESOLVED (Cray, 2026-07-16):** as recommended — **consistent; the
  reading is confirmed as intended**. A paying anchor partner commissions a
  concrete additive archetype (ADR-016 OQ-A1 additive growth from observed
  need), not the abstraction/seam extraction ADR-0031 D4's N≥2 gates;
  ADR-0031's shape constraints (typed, declaration-as-data, tripwires
  honored) still bind any such PLAN. A future archetype PLAN may lean on
  this reading. (Folded into D6.)

## References

- `docs/strategy/private/2026-07-16-demo-to-pilot-strategy-synthesis.md` —
  the full arc in one page (gitignored; referenced by path per house
  practice); companions:
  `docs/research/private/2026-07-16-partner-onboarding-wedge-onepager.md`,
  `docs/research/private/2026-07-16-hero-shaping-checklist.md`
- Session-137 ADDENDUM handoff (gitignored) — the un-plannability evidence +
  the AT-2 N-count correction record
- Code anchors (verified 2026-07-16): `services/engine/procedures/spec.py:822-830`
  (AT-2 N=2, re-arms at N=3, per #767);
  `tests/services/engine/procedures/test_at2_signature_retrigger.py` (the
  re-armed marker); `verticals/building_materials/` (Tier-1 Mirror, no
  `procedures.yaml`, #765); `verticals/procurement/hero_demo/` (the bespoke
  hero structure); `verticals/procurement/data_adapter/fastenal_csv.py` (the
  real CSV adapter); `services/api/routers/query.py` +
  `services/engine/nl_query.py` (NL-query, built);
  `services/engine/economic_impact.py` (assumptions-first ฿ discipline)
- ADR-005, ADR-006, ADR-0015, ADR-0020, ADR-0025 (D7), ADR-0030, ADR-0031;
  PLAN-0074 (SD-3), PLAN-0076
