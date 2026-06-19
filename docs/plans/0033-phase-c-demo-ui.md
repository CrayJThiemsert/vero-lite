# PLAN-0033: Phase C — Pain-First Animated Demo + Branching Pipeline Overview + New-Vertical Intake

**Status:** Draft (uncommitted — Cowork-drafted per ADR-009 D1; Code commits per ADR-009 D2)
**Owner:** Claude Code (Tier 2 executes) — Cowork drafted (ADR-009 D1)
**Created:** 2026-06-19
**Related ADRs:** ADR-0015 (two-tier vertical onboarding — this is the **Tier-1 "Mirror demo"** face; D5 live co-creation), ADR-010 (LLM reasoning hook; **IN-4 deterministic rule fail-safe** — the honesty anchor for the branching DAG), ADR-0022 (governed entity resolution — `entity_resolution` trace step), ADR-008 (YAML ontology contract), ADR-006 (vertical plugin architecture; D4 Rule of Three), ADR-009 D1/D2 (Cowork drafts / Code commits), ADR-012 D4.3 (author≠reviewer disclosure), ADR-013 (phased advisory relocation — interim authoring applies)
**Related PLANs:** **done/0013** (OCT stakeholder demo shell this lands in), **done/0016** (new-vertical scaffold engine — Tier-1 mirror generator), **done/0017** (live co-creation intake face — `intake-view.js` / View E), **done/0018** (demo-shell MS-S1 status + warm/sleep — `llm-control.js`), **done/0031** (ORM emitter), **done/0032** (registry auto-discovery — a new vertical auto-registers, no core edit)

> **Drafting provenance.** Cowork-drafted (uncommitted) under ADR-009 D1; Code
> reviews + commits via PR (ADR-009 D2; CLAUDE.md §6/§7). Cray **locked** the design
> set across session 68 (arc G pain-first, F1–F3, two-axis layout, branching taxonomy,
> SD-1/2/3, Tier-1 mirror scope — final "lock + go" 2026-06-19); those are **encoded
> here, not re-litigated** (dispatch §0). The four SURFACED items in §10 are the only
> open calls and are flagged for **Cray adjudication**.
>
> **Author≠reviewer disclosure (ADR-012 D4.3) — READ.** The Palantir "Data→Decision"
> research note that feeds scene 6 (`docs/research/private/2026-06-19-palantir-data-decision-control-surface.md`)
> **and** its SD-1/SD-2/SD-3 recommendations were **also Cowork-authored**, and this
> PLAN was drafted by the same tier. The independent-deliberation check was therefore
> **not exercised** on the scene-6 control-surface design — it is one informed
> perspective carried forward, not a second-sourced call. **Code's R2 review + Cray's
> ratification remain the live independent checks.**

---

## Goal

Rework the OCT demo front-end into a **pain-first, narration-paced story** that makes
vero-lite's real moat — *every decision is gated, traced, and reversible* — **visible**
to a non-expert buyer, and lands the new-vertical "Mirror demo" live-intake moment
(ADR-0015 D5). The centrepiece is a **branching DAG pipeline overview** (not a linear
stepper) whose **error → deterministic-fail-safe reroute** dramatizes governance as the
product, plus a **two-axis layout** (all task details visible at once on the left, the
animated branching overview + transport controls on the right) and a **persistent
"during" + actionable "after" control surface** for the anomaly→approve→execute loop.
Scope is **Tier-1 mirror only** — synthetic data, no real-data / no PDPA path (ADR-0015
D1; Tier-2 is a separate gated engagement). The build is **front-end-time-bounded**
(4–8 focused weeks, solo dev) and therefore **phased vertical-slice-first** to de-risk
the animation technique before the full six-scene arc.

## Acceptance Criteria

- [ ] **AC-1 — Arc order = G, pain-first.** The story opens on the buyer's own pain in
      their vertical (scene 1 "Hook"), not on mechanism/ontology. The ontology/engine
      explainer is an **optional appendix**, reachable but never scene 1 (dispatch §1).
- [ ] **AC-2 — Branching DAG overview (not a linear stepper).** The pipeline overview
      renders as a DAG with **hand-placed SVG nodes** (no graph-layout lib) supporting
      **>1 path** and node states `pending / active (pulse) / done (green ✓) / error
      (red ✕) / skipped (dim)**, and **edge types: taken** (solid + green flow + a token
      dot travels the edge), **alt path** (dashed + dimmed), **fail-safe reroute** (amber
      flow). (dispatch §2a.)
- [ ] **AC-3 — The error → fail-safe branch is shown and is the moat beat.** An
      LLM-path error / low-confidence step **reroutes to the deterministic rule
      fail-safe branch**, which **still passes the human approve gate + records audit**
      → "error ก็ยัง governed + reversible." This branch maps to **real engine
      structure** (ADR-010 IN-4 rule fail-safe), not invented fan-out (AC-9).
- [ ] **AC-4 — Two-axis layout.** **Left column:** ALL tasks' details shown
      **simultaneously** (per task: name + status chip + detail rows); the **active task
      highlights + blinks**; clicking a task/node jumps focus. **Right column:** the
      branching overview + transport controls (**▶ play / ⏭ step / ↺**). (dispatch §2b.)
- [ ] **AC-5 — Scene-6 control surface = persistent "during" + actionable "after."**
      The control rail is **present but quiet** beside the scene-3 pipeline animation
      (during); the run emits **exactly one** proposal into a **Proposed** lane at the
      end; the operator **approves → Approved → executes → Executed**, the card animating
      across lanes (View Transitions where supported, GSAP otherwise). **No literal
      mid-flow intervention** (SD-2; we don't have it). 2–3 of the SD-1 patterns are
      adopted: lifecycle/kanban lanes + persistent action-inbox rail + reasoning-trace
      "why" toggle with a **rule / query / LLM colour legend**.
- [ ] **AC-6 — Reasoning trace is the centrepiece and is honest.** The "why" panel
      reuses the existing reasoning-trace render and its **kind colour legend**
      (`view-flow.js` `kindClass` → rule/llm/ontology|query; `view-anomaly.js`
      `O.reasoningTrace`). No distributed-trace span-waterfall or token telemetry we
      don't have (SD-3 honesty guard).
- [ ] **AC-7 — Live intake = dual-path, fail-safe.** Scene 4 reuses `intake-view.js`
      (View E) and frames as "**ร่าง skeleton ของ operation คุณ มาปรับด้วยกัน**" (NOT
      "builds your whole business from a sentence"): a **cached-default path that *looks*
      live** + a pre-warmed **true-live "go live" button**, with a **hard timeout +
      scripted fallback that reads as deliberate**. MS-S1 is pre-warmed and a readiness
      indicator is shown, **reusing PLAN-0018's `GET /llm/status` + warm/sleep**
      (`llm-control.js`), building none of it new.
- [ ] **AC-8 — Scene-5 = ONE honest, sourced number tied to money/biomass.** Before/
      After shows a **single bounded figure**, framed as "**grounding closes the gap raw
      LLMs open**" (robustness), **not** accuracy supremacy; **no "100%" ceiling**.
      Aligns with the project's own B-γ / A2 finding (raw accuracy does **not** separate
      the governed stack from lean RAG → the moat is governance). The exact figure +
      source is SD-D and must be **defensible before it lands** (this is a public repo).
- [ ] **AC-9 — Honesty guard (SD-3) holds end-to-end.** Branches map only to real
      engine structure — (i) LLM-compose vs deterministic rule fail-safe (ADR-010 IN-4),
      (ii) approve / hold / reject, (iii) multiple candidate actions **only if** the
      engine really emits them. **No** Palantir release-promotion-style fan-out is
      invented. No Palantir quote tagged `[search-synthesis]` in the research note is
      asserted as fact anywhere in shipped copy (dispatch §4).
- [ ] **AC-10 — Reduced-motion + static fallback.** `prefers-reduced-motion` is
      honoured end-to-end; the whole story degrades to a **static, readable
      click-through** where state = **colour + icon + label**, never motion-only.
- [ ] **AC-11 — Narration-paced, click/keyboard driven.** Step advance binds to
      click/keyboard (not timer-only) so live Q&A doesn't desync the animation;
      deliberate per-step delays (~0.9–1.25 s) when auto-playing. Keyboard nav coexists
      with the existing `app.js` view hotkeys.
- [ ] **AC-12 — Offline / no-CDN.** Every animation library is **vendored locally**
      through the existing offline-bundler seam (`index.html` `__bundler_thumbnail`
      template + ordered `<script>` tags); **no CDN reference** is introduced
      (CLAUDE.md §8 public-repo posture; offline-first).
- [ ] **AC-13 — Lifecycle teardown contract.** Every scene implements an
      **enter→build / leave→kill** contract (GSAP timelines + View Transitions +
      listeners torn down on scene leave) with **no leaked timers/tweens/handlers**
      across repeated scene cycling — defined and test/observed **before** scene content
      is coded.
- [ ] **AC-14 — Coexists with the functional console.** Story-mode does **not** replace
      the working OCT console (Views A–E); it is an additive surface (SD-C) that can be
      entered and exited, leaving the console intact.

## Out of Scope

- ❌ **Tier-2 / real-data / PDPA path** — synthetic mirror data only (ADR-0015 D1;
      Tier-2 is a separate gated engagement). No real `DataAdapter`, no mapping layer,
      no data-residency/PDPA UX here.
- ❌ **3D / WebGPU / Spline / Three.js** scene work.
- ❌ **Rive (v1)** — deferred to a future v2 (asset-pipeline cost; expert-panel call).
- ❌ **Graph-layout library** (dagre / elk / cytoscape) — demo pipelines are
      known/curated → hand-placed SVG nodes; defer auto-layout.
- ❌ **Native CSS Scroll-Driven Animations as the spine** — Chromium-only in 2026; use
      **GSAP ScrollTrigger** instead (expert-panel tech-reality call).
- ❌ **New backend routes** — scene 4 reuses PLAN-0018's `GET /llm/status` + warm/sleep;
      scene 6 reuses `GET /recommendations` → approve → execute. No net-new API.
- ❌ **Auto-execute / multi-agent / autonomy-without-the-gate** — contradicts the
      single-step human-gated engine and the moat (SD-3).
- ❌ **Distributed-trace span waterfall + token-usage telemetry** — borrow only the
      colour-by-kind legend (SD-3).
- ❌ **CDN-loaded libraries** — vendor locally (AC-12).

## Phasing (REQUIRED — front-end time is the real cost)

Front-end time is the dominant cost (expert estimate **4–8 focused weeks, not 1–2**,
solo dev). De-risk the animation technique on a **vertical slice** before building the
full arc.

| Phase | Scope | De-risk purpose |
|---|---|---|
| **C0 — vertical slice (de-risk first)** | Story-mode shell + scene router + the **lifecycle teardown contract** (AC-13) + **ONE vertical's** (SD-B = aquaculture) **branching DAG pipeline** (scene 3) **with the scene-6 control surface on it** (AC-2/3/4/5/6), end-to-end, **with the reduced-motion static fallback from day 1** (AC-10). | Proves the GSAP spine + branching DAG + kanban lanes + teardown + reduced-motion before any breadth is built. If the technique doesn't carry, it's caught here cheaply. |
| **C1 — full arc** | Layer scenes **1 (Hook)**, **2 (จับได้ + คุณคุม — governance-as-offense + the 🌟 fail-safe self-catch beat)**, **4 (live intake, dual-path)**, **5 (Before/After, one honest number)**. | Completes arc G on the proven slice. |
| **C2 — breadth** | Scene **6 กว้าง + Ask** (snap to other verticals + NL query via `view-ask.js`); the **optional ontology/engine appendix**. | Breadth + the "and what's *your* operation?" hook last, on a hardened spine. |

## The demo arc G (6 scenes, pain-first)

1. **Hook (NEW)** — cold-open on the buyer's OWN pain in THEIR vertical ("ตี 2 พอนด์คุณ
   DO ร่วง"). Lead with their problem, not our mechanism.
2. **จับได้ + คุณคุม (BUILT — `view-anomaly.js`, rework)** — detect → suggest →
   **approve**, on-prem; governance as **offense** ("ไม่มีอะไรทำงานก่อนคุณเซ็น · ทุก
   action log"). Carries the 🌟 **fail-safe self-catch** beat (LLM error / low-confidence
   → deterministic rule path, still gated).
3. **มันทำงานยังไง (EXTEND `view-flow.js`)** — the pipeline animated, **ONE vertical**
   (the original ×3 triple-repeat was a flagged weakness — show it once).
4. **Live intake (BUILT — `intake-view.js`, rework)** — **dual-path**; frame as "ร่าง
   skeleton ของ operation คุณ".
5. **Before / After (NEW)** — **ONE honest, sourced number tied to money/biomass**;
   robustness framing ("grounding closes the gap raw LLMs open"), no "100%" ceiling.
6. **กว้าง + Ask (BUILT — `view-ask.js`)** — snap to other verticals + NL query.

**Appendix (optional opener):** the ontology/engine explainer — demoted from scene 1
(the word "ontology" lost the AI-naive buyer in review); shown only to audiences that
want the "how".

## Steps

### Step 1 — Story-mode shell + scene router (Phase C0)
Stand up the story surface per SD-C (recommended: a new `view-story.js` overlay that
**coexists** with the `app.js` A–E router rather than replacing it — AC-14). Wire scene
navigation (▶ play / ⏭ step / ↺) bound to click/keyboard (AC-11), and the
**enter→build / leave→kill lifecycle contract** as the first thing built (AC-13). Vendor
the chosen animation lib(s) through the offline-bundler seam and add the ordered
`<script>` include(s) to `index.html` (AC-12).

### Step 2 — Branching DAG overview component (Phase C0)
Hand-placed SVG node graph with the 5 node states + 3 edge taxonomies (AC-2), GSAP
orchestrating pulse/flow/token-dot. Implement the **error → fail-safe reroute** path
(AC-3) wired to the real engine's LLM-compose-vs-rule-fail-safe structure (ADR-010
IN-4). Static reduced-motion rendering of every state from day 1 (AC-10).

### Step 3 — Two-axis layout + scene-6 control surface on ONE vertical (Phase C0)
Left = all-tasks-at-once detail column with active-task blink; right = the DAG overview
+ controls (AC-4). Re-house the existing scene-6 components into the persistent
during + after surface: `decisionCard()` + `O.reasoningTrace()` + approve→execute +
`receiptBlock()` (`view-anomaly.js`) and the `Ingest→Condition→Process→Result` flow
(`view-flow.js`) into a **persistent rail + kanban lanes** (Proposed → Approved →
Executed) — ~80% re-housing + ~20% one new pattern (lanes), per the research grounding
map. Adopt 2–3 SD-1 patterns; reuse the rule/llm/query colour legend (AC-5/AC-6).

### Step 4 — Full arc scenes 1/2/4/5 (Phase C1)
Build the Hook (1), rework จับได้+คุณคุม with the fail-safe self-catch beat (2), rework
live intake as dual-path with hard-timeout + pre-warm readiness reusing PLAN-0018 (4),
and Before/After with the one honest number (5). Honour the domain-credibility beats:
**predictive** framing (catch the DO trend at 4.8↓ *before* the 4.0 line, not a
cartoon crash→snap-back), a **sensor-confidence / cross-check** beat, and an
**alarm-fatigue + escalation-when-asleep** story (time-bounded deterministic fallback),
with **$/biomass** attached; cold-chain → a named excursion rule + clock.

### Step 5 — Breadth: other verticals + Ask + appendix (Phase C2)
Snap to other verticals and the NL-query closer (`view-ask.js`); add the optional
ontology/engine appendix. A new vertical auto-registers via PLAN-0032 discovery (no core
edit), so breadth is data, not code.

### Step 6 — Verification + docs + closeout
Per-AC verification (§Verification), runbook update for the demo operator (pre-warm →
confirm `resident` → run story), STATUS update, and `git mv` to `done/` on completion
(Code's lane, ADR-009 D2).

## Technical contract (non-negotiable)

- **Animation lifecycle teardown (AC-13):** every scene exposes `build()` / `teardown()`;
  on scene leave, **all** GSAP timelines are killed, View-Transition callbacks detached,
  and event listeners removed — proven by cycling scenes repeatedly with no leaked
  timers/tweens/handlers. Define this contract **before** coding scene content.
- **Single animation spine:** GSAP is the one orchestration spine (GSAP ScrollTrigger
  for any scroll-driven beats); **View Transitions API = a 1-line enhancement only**
  (kanban-lane reparent), never load-bearing; **verify the GSAP 2026 license** before
  vendoring.
- **Vendored-lib manifest (AC-12):** list every vendored lib + version + the
  offline-bundler include order in `index.html`; **no CDN**. Confirm the offline-bundler
  entrypoint (the `__bundler_thumbnail` seam) handles the new assets.
- **Reduced-motion + static fallback (AC-10):** state encoded as colour + icon + label;
  full static click-through under `prefers-reduced-motion`.
- **Click / keyboard nav (AC-11):** step advance is click/keyboard-driven; coexists with
  `app.js` view hotkeys (which ignore typing into inputs/textareas).
- **No new backend:** reuse `GET /llm/status` + warm/sleep (PLAN-0018) and
  `GET /recommendations` → approve → execute. Net-new code is front-end only.

## Risks / threats

| Risk | Mitigation |
|---|---|
| **Live-demo failure** (MS-S1 cold / slow / unreachable mid-pitch) | Dual-path: cached-default that looks live + pre-warmed true-live button; **hard timeout + scripted fallback that reads as deliberate**; readiness indicator via PLAN-0018 `GET /llm/status` (AC-7). |
| **Solo-dev time** (4–8 wks, not 1–2) | Vertical-slice-first phasing (C0) de-risks the technique before breadth; each phase is independently demoable. |
| **Honesty — numbers** | Scene-5 = ONE sourced bounded figure, robustness framing, no 100% (AC-8); figure + source gated by SD-D before it ships in a public repo. |
| **Honesty — Palantir claims** | Adopt the *grammar* (lanes / inbox / trace legend), not the fiction; **no `[search-synthesis]`-tagged Palantir quote asserted as fact** (AC-9; research-note §4 caveat). No invented release-promotion fan-out (SD-3). |
| **Browser support** | GSAP spine (broad support) over Chromium-only Scroll-Driven; View Transitions strictly a progressive 1-line enhancement; reduced-motion path is the universal floor. |
| **Animation memory leaks** across repeated demo runs | Lifecycle teardown contract defined first + verified by scene-cycling (AC-13). |
| **Over-promise of "builds your whole business from a sentence"** | Reframe scene 4 as "ร่าง skeleton … มาปรับด้วยกัน" with the mandatory human review/edit step (ADR-0015 D5 hard requirement). |

## SURFACED decisions — Cowork recommends, **Cray adjudicates** (do not downgrade)

### SD-A — Scene count: keep 6, or fold? → **Recommend keep 6, with scenes 1+2 tightly coupled** *(Cray adjudicates)*
**Recommend:** keep all six as distinct beats, but stage **1 (Hook) → 2 (จับได้+คุณคุม)
as one continuous movement** (pain → "we caught it, and you stay in command") rather than
merging them into a single scene. Reasoning: the Hook's job (their pain) and scene 2's
job (governance-as-offense + the fail-safe self-catch) are different *claims*; merging
them dilutes the governance beat that is the moat. Folding **2+6** is worse — scene 6 is
breadth/Ask, a different intent. The vertical-slice phasing means the count costs little
(C0 builds one pipeline regardless). **Alternative if time slips:** ship C0+C1 (scenes
1–5) and treat scene 6 breadth as a fast-follow — the arc still closes on the honest
number.

### SD-B — Which vertical for the de-risk slice? → **Recommend aquaculture** *(Cray adjudicates)*
**Recommend aquaculture:** it is the prototyped vertical, the ADR-0015 D4 ratified
showcase pick, and the DO-crash story is the most visceral pain (biomass death at 2 a.m.)
— the strongest Hook. It also exercises the recommender **below**-threshold direction
(ADR-0015 OQ-3 `OCT_RECOMMEND_DIRECTION`), the more demanding path. **Counter-argument
acknowledged:** energy is ADR-005's primary partner type and the B-γ "load-bearing"
baseline; if the *first live audience* is the energy/supply-chain network, the slice
should be energy instead (ADR-0015 D4 "audience-dependent alternate"). Decision should
follow the **first audience**, not the prototype.

### SD-C — Where does "story-mode" live? → **Recommend a new `view-story.js` overlay (don't replace the console)** *(Cray adjudicates)*
**Recommend (overlay):** add `view-story.js` as an additive story surface that the
`app.js` router can enter/exit, **coexisting** with the functional Views A–E rather than
extending the A–E tab router to host scenes. Reasoning: the working console is the
credibility substrate (real approve→execute, real `GET /recommendations`); story-mode is
a *presentation lens over the same engine*, and an overlay keeps the two concerns
separable (AC-14) and the teardown contract clean. Extending `app.js` routing would
entangle scene lifecycle with view lifecycle. **Build cost:** one new view module + the
ordered `<script>` include, mirroring the existing `view-*.js` pattern.

### SD-D — How is scene-5's "one honest number" sourced? → **Recommend the project's own B-γ / A2 finding as the spine; treat the external stat as supporting-only and verify before ship** *(Cray adjudicates)*
**Recommend:** anchor scene 5 on **vero-lite's own measured result** — the B-γ / A2
finding that, on an equal rubric, the governed stack **ties or exceeds** lean RAG on all
three verticals while raw text-to-SQL **swings** by vertical (e.g. aquaculture breach →
0 rows) — framed as "**grounding closes the gap raw LLMs open; the governed stack is
*robust*, not just accurate**" (sources: `benchmarks/procedure_baseline/REPORT.md` §B-3 +
the A2 equal-rubric addendum; both in-repo, defensible). The **dbt-Labs "86% → 6%"
external statistic** named in the dispatch is attractive but is **not yet
source-verified by the drafter** — recommend it only as a **supporting** citation, and
**only after** Code/Cray confirm the exact figure + primary source (this PLAN is
repo-tracked → eventually public; an unverified external stat is a credibility risk, the
same class as the Palantir `[search-synthesis]` caveat). **Do not put a raw-LLM
"accuracy %" head-to-head on screen** — it invites the accuracy-supremacy framing the
project explicitly rejected (AC-8).

## Verification

- **AC-1/AC-11:** scripted click/keyboard walkthrough — arc opens on the Hook; steps
  advance on input, not a timer; auto-play uses the ~0.9–1.25 s delays.
- **AC-2/AC-3/AC-9:** render every node state + edge type; trigger the error path and
  confirm the **fail-safe reroute still hits approve-gate + audit**; audit the branch
  set against the engine (ADR-010 IN-4) — no invented fan-out, no `[search-synthesis]`
  Palantir quote in copy.
- **AC-4/AC-5/AC-6:** left column shows all task details with active-blink; the run emits
  one proposal → lanes Proposed→Approved→Executed; the "why" toggle + rule/llm/query
  colour legend render.
- **AC-7:** live walkthrough — cached-default looks live; true-live button pre-warms;
  forced MS-S1 timeout falls back to the scripted path cleanly; readiness indicator
  reflects `GET /llm/status`.
- **AC-8/SD-D:** scene 5 shows exactly one bounded figure with an in-repo-defensible
  source; no "100%"; no raw-accuracy head-to-head.
- **AC-10:** with `prefers-reduced-motion` set, the entire story is a static, readable
  click-through (state = colour+icon+label).
- **AC-12:** grep the shipped `static/` for any CDN URL → none; libs load from vendored
  assets via the offline bundler.
- **AC-13:** cycle every scene N times; assert no leaked GSAP timelines / View-Transition
  callbacks / listeners (instrument count before/after).
- **AC-14:** enter and exit story-mode; Views A–E remain functional.

## Author≠reviewer disclosure (ADR-012 D4.3)

The scene-6 control-surface design (kanban lanes / action-inbox rail / reasoning-trace
legend / during-vs-after sequencing) originates in a **Cowork-authored** research note
and **Cowork-authored** SD-1/2/3 recommendations, and this PLAN was drafted by the same
tier. The drafter≠deliberator separation is therefore **not** intact for that portion —
it is one perspective, not independently second-sourced. **Code's R2 review and Cray's
ratification are the remaining independent checks.** All other locked design inputs
(arc G, F1–F3, layout, branching taxonomy) originate from Cray's session-68 decisions +
the expert-panel review, carried via Code's dispatch — for those, Cowork is the
distiller, not the originator.

## References

- **Dispatch (this task):** `.claude/handoffs/session-68/2026-06-19-1709-code-cowork-plan0033-phasec-ui-dispatch.md`
- **Feeding research (Cowork, gitignored):** `docs/research/private/2026-06-19-palantir-data-decision-control-surface.md`
  (§4 + all Gotham + the two `blog.palantir.com` claims are `[search-synthesis]` — see
  AC-9 / SD-D honesty caveat); predecessor architecture note
  `docs/research/private/2026-06-07-palantir-5-concerns-pipeline-design.md`.
- **Onboarding governance:** ADR-0015 (`docs/adr/0015-vertical-onboarding-two-tier-pitch.md`),
  PLAN done/0016 (scaffold engine), done/0017 (`intake-view.js`), done/0018 (`llm-control.js`).
- **Engine reality (verified live 2026-06-19, HEAD `41d0372`):**
  - Router + cross-view events + keyboard nav: `services/api/static/assets/app.js`
    (VIEWS A–E `:9-15`, `go()` `:109-117`, `oct:goto`/`oct:navobj` `:141-160`, hotkeys `:155-159`).
  - Linear pipeline + kind colour legend: `services/api/static/assets/view-flow.js`
    (stages `:157-162`, `kindClass` `:189-195`, approve→execute `:172-186`).
  - Decision card + status enum + reasoning trace + receipt:
    `services/api/static/assets/view-anomaly.js` (`decisionCard` `:29-87`,
    `renderActions` `:89-116`, status enum proposed/approved/executed/rejected `:176-181`).
  - Intake (View E) `intake-view.js`; NL query (View C) `view-ask.js`.
  - MS-S1 status/warm/sleep affordance: `services/api/static/assets/llm-control.js`
    (mounted `app.js:44-45`); PLAN-0018 `GET /llm/status`.
  - Offline bundler + ordered scripts: `services/api/static/index.html`
    (`__bundler_thumbnail` `:15-27`, script order `:30-39`).
- **Moat / honesty anchors:** ADR-010 IN-4 (rule fail-safe), ADR-0022 (governed entity
  resolution); B-γ / A2 finding — `benchmarks/procedure_baseline/REPORT.md` §B-3 + the
  A2 equal-rubric addendum (STATUS Recent Decisions, commit `e032512`).
- **Governance:** ADR-009 D1/D2 (Cowork drafts / Code commits), ADR-012 D4.3
  (author≠reviewer), ADR-013 (phased advisory relocation); CLAUDE.md §6 (Plan Flow /
  routing), §7 (commit/PR), §8 (public-repo / no-secrets / offline posture).

---

*Drafter numbering check (Cowork, 2026-06-19): `docs/plans/` active =
0004/0010/0012/0019/0027; `docs/plans/done/` tops at **0032** → **0033 free** (matches
the dispatch's confirmed `target_number = 0033`). No `docs/plans/0033-*` exists at HEAD
`41d0372`. Uncommitted draft per ADR-009 D1; Code commits via a `feat`/`docs` PR
(ADR-009 D2; CLAUDE.md §7). AI-assisted (Cowork); no `Co-Authored-By` per CLAUDE.md §7.*
