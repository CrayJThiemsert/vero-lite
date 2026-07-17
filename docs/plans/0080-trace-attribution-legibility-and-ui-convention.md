# PLAN-0080: trace-attribution legibility (deterministic kind→label map) + `docs/conventions/ui.md`

**Status:** Draft (pending Cray ratification)
**Owner:** Claude Code (executor) · `plan-drafter` (author) · Cray (ratifier)
**Created:** 2026-07-17
**Related ADRs:** ADR-0007 (OCT engine contracts — the `ReasoningStep`/`AuditMetadata` pins), ADR-0017 (D5 knowledge routing, D6 derived-artifact precedence), ADR-0026 (D6 governed-decision audit tie), ADR-0032 (D1(3) offline arm, D4 agent-interop PARK, D5 attribution trust anchor, OQ-2 doc Rule-of-Three)

> **Drafting provenance (ADR-012 D4.3 disclosure).** Authored by the in-harness
> `plan-drafter` subagent (ADR-013 D1 phased authority) from a Code-verified
> dispatch, 2026-07-17 (session 143). Outline originator: Code (from Cray's
> Palantir DevCon 6 transcript analysis + Cray's AskUserQuestion ratification of
> the two work items). Independent review: Code (R2) + Cray (ratification at PR
> merge). Separation: **INTACT** — author (plan-drafter) ≠ reviewer (Code/Cray).
> Every `file:line` fact below marked "re-verified" was read on disk by the
> drafter on 2026-07-17; facts marked "dispatch-verified" are taken from Code's
> grounding pass and re-checked at execution (Step 0).
>
> **Rev 2 (2026-07-17, same session).** Folds in Code's R2 confirmation (the
> tripwire scan is safe against the `Step.kind` StrEnum — see Substrate) and
> Cray's AskUserQuestion ratification of the badge **colour-axis split**
> (colour = mechanism, glyph = actor — L-4). SD-1/SD-2 remain unratified and
> go to Cray at the PR.

## Origin

Cray attached a Palantir DevCon 6 transcript ("Design Patterns for Human-Agent
Collaboration") and asked how it applies to vero-lite. Code's grounded verdict:
of the talk's four sections (agent-vs-human attribution; agent workflow
integrated where users work; enriched non-plain-text responses; anti-"AI slop"
via a shared component library + a `design.md` + agent skills), vero-lite
already satisfies three — View C's grounding receipt is stronger than the
talk's example, `.claude/skills/` is their "agent skills", and `theme.css` is
the anti-slop token file already. The two *real* gaps are:

1. **Attribution legibility** — the trace badge channel that tells a reader
   *who/what produced this step* is substring-sniffed and silently dead for
   most procedure-engine steps (Subject A).
2. **No canonical UI convention doc** — the design opinion lives in a one-shot
   generation prompt marked "not governance" (Subject B).

Cray ratified both work items via AskUserQuestion (2026-07-17, session 143) as
**one PLAN, two subjects**, and explicitly ratified that an LLM-narrated
advisory layer stays an **Open Question, not built now** (see Open Questions).

## Goal

Make the reasoning-trace attribution channel **deterministic and honest** — a
pure kind→plain-English-label lookup shared by every trace render, with
unmapped kinds degrading visibly and a CI tripwire that fails when an
engine-emitted kind lacks a label. The **actor axis** (human / LLM /
deterministic machine — the "who/what" this Goal promises) is carried by a
**small glyph on the badge**, while the **colour channel retains the existing
`theme.css` mechanism/severity semantics** (L-4) — two axes, two channels,
each legible at a glance. And consolidate the existing, scattered UI
conventions (design tokens, component contract, security rule, no-build-step,
cache-bust, ontology-driven principle, control-tower tone) into one canonical,
agent-readable `docs/conventions/ui.md`. No LLM, no network, no new runtime
dependency anywhere in this PLAN (ADR-0032 D1(3)); the label channel stays
reproducible because attribution is the trust anchor (ADR-0032 D5,
`docs/adr/0032-...md:193` — "the AI decided" is not an answer an auditor
accepts).

## Substrate facts

All re-verified on disk by the drafter 2026-07-17 unless marked otherwise.
Items marked **[correction]** amend the dispatch fact-pack and are binding over
it.

### The contract

- `ReasoningStep` — `services/engine/actions.py:20-24`: `step_id: str`,
  `kind: str`, `summary: str`, `detail: dict|None`. `kind` is a **bare `str`**;
  ADR-0007 pins this verbatim in its Accepted body
  (`docs/adr/0007-oct-engine-contracts.md:86-91`) with
  `'ontology_query' | 'llm_inference' | 'rule_check'` as *examples only*
  (`:88`).
- `AuditMetadata` — `actions.py:70-82`: `actor: str`, `actor_kind: str`
  (docstring: *"Initial scope; expanded in future audit-framework ADR"*,
  mirrored at ADR-0007:98). ADR-0007:100 enumerates **3** `actor_kind` values
  (`'engine','llm','human'`); the runtime audit stream also emits a 4th,
  `"service"`, into the `run_started` audit payload
  (`services/engine/procedures/persistence.py:132-141`, PLAN-0053 AC-9/10).
  **[precision]** the `"service"` value lands in an audit-payload dict, not an
  `AuditMetadata` instance — see Finding F-1.
- `ReasoningStep` carries **no actor field**; attribution is
  per-RecommendedAction (`AuditMetadata`), not per-step.
- The audit *framework* (retention, export, anchoring, PDPA surface) is
  **deferred to ADR-011, gated on real partner data**
  (`services/db/audit_log.py:17-18`).

### Two trace vocabularies, one renderer

- Typed `ReasoningStep` instances flow on the recommender/LLM path
  (`services/engine/recommender.py`, `services/engine/llm/trace.py`,
  `entity_resolution.py`, `economic_impact.py`, `action_verification.py`).
- The procedure engine writes **raw dicts** into `StepResult.reasoning_trace`
  JSONB (`services/engine/procedures/runs.py:109`). Nothing validates them
  against `ReasoningStep`. **[correction — load-bearing for SD-1]** the raw
  dicts are not merely untyped-`kind` — they carry **extra top-level keys**
  outside the `ReasoningStep` shape entirely: `principal_id`
  (`action_step.py:672`), `action_id` (`action_step.py:718`), `counts`
  (`evaluate_step.py:130`). `view-monitor.js:321-322` *depends* on the
  top-level `principal_id`. Typing `kind` alone would not unify the
  vocabularies.
- Existing dev-DB rows already hold the raw-dict shape — a tightened validator
  on read would fail closed on historical runs (same hazard class as the AC-13
  `governance_pin` "only-when-supplied" precedent).
- **Hash safety (dispatch asked; verified):** the governance/config hash
  (`services/engine/procedures/governance_pin.py:126-131`) is computed over the
  procedure **definition** snapshot; the `"kind"` it hashes at
  `governance_pin.py:71` is `Step.kind` — the *step-definition enum*, a
  different field that merely shares the name. `reasoning_trace` never appears
  in the hash module. Label/render changes are hash-safe; runtime trace `kind`
  values do not feed any config or governance hash. (The name collision between
  definition-side `Step.kind` and trace-entry `kind` is itself worth one line
  in `ui.md`'s glossary so nobody conflates them.)

### The verified `kind` inventory — 22 kinds, not the dispatch's 9 **[correction]**

Raw-dict emissions (procedure engine → `StepResult.reasoning_trace` JSONB):

| # | kind | emitter |
|---|------|---------|
| 1 | `transform_provenance` | `services/engine/procedures/transform_step.py:246` |
| 2 | `read_passthrough` | `services/engine/procedures/query_step.py:415` |
| 3 | `read_provenance` | `query_step.py:440`, `:477` |
| 4 | `join_pipeline` | `query_step.py:492`, `:546`, `:570`, `:637` |
| 5 | `verdict_computed` | `services/engine/procedures/evaluate_step.py:130` |
| 6 | `action_rejected` | `services/engine/procedures/action_step.py:264` |
| 7 | `action_executed` | `action_step.py:323`, `:717` |
| 8 | `action_proposed` | `action_step.py:332` |
| 9 | `tier_authority` | `action_step.py:448` |
| 10 | `gate_principal_recorded` | `action_step.py:671` |
| 11 | `read_refused` | `services/engine/procedures/orchestrator.py:786` |
| 12 | `error` | `orchestrator.py:792` |
| 13 | `doa_tier_resolved` | `services/engine/procedures/governance_step.py:210` |
| 14 | `severity_tier_resolved` | `governance_step.py:260` |
| 15 | `scored_rule_selected` | `governance_step.py:353` |
| 16 | `rule_gate_evaluated` | `governance_step.py:432` |

Typed `ReasoningStep` emissions (recommender/LLM path):

| # | kind | emitter |
|---|------|---------|
| 17 | `entity_resolution` | `services/engine/entity_resolution.py:158` |
| 18 | `economic_impact` | `services/engine/economic_impact.py:155` |
| 19 | `rule_check` | `services/engine/recommender.py:305`, `:317`; `services/engine/llm/trace.py:115` |
| 20 | `action_verification` | `services/engine/action_verification.py:129` |
| 21 | `ontology_query` | `llm/trace.py:81` |
| 22 | `llm_inference` | `llm/trace.py:91` |

The dispatch listed 9 and omitted 10 real kinds (`join_pipeline`,
`action_rejected`, `action_proposed`, `tier_authority`, `read_refused`,
`doa_tier_resolved`, `severity_tier_resolved`, `scored_rule_selected`,
`rule_gate_evaluated`, `action_verification`) — exactly the silent-rot failure
mode the tripwire (AC-3) exists to kill. No kind emissions exist under
`services/api/*.py` (grep verified — the engine is the only emitter).

**R2 confirmation (Code, 2026-07-17):** the AC-3 scan patterns were
independently tested against the definition-side name collision —
`StepKind` is a `StrEnum` written `QUERY = "query"` (`spec.py:54-61`), not
`kind="query"`, so **both scan patterns return 0 hits in `spec.py`**; counts:
21 raw-dict-form + 16 kwarg-form = 37 emission sites across
`services/engine/`, deduping to exactly the 22 kinds above. Logged
`confirmed — prior intact` (CLAUDE.md §6).

### The defect, stated precisely **[correction — sniff is dishonest in BOTH directions]**

- `kindClass(kind)` decides the badge colour by **substring sniff**
  (`services/api/static/assets/components.js:145-151`): `'rule'`→`s-warn`,
  `'llm'|'infer'`→`s-info`, `'ontology'|'query'`→`s-ok`, else `s-neutral`.
  Duplicated **byte-identically** at `view-flow.js:189-195`.
- `components.js:164` renders **`s.kind` verbatim** as the badge text;
  `:171` renders `s.summary` beneath.
- Fall-through census against the verified inventory: **14 of 16** raw-dict
  kinds fall to `s-neutral` (the actor colour channel is dead in View H), and
  the other **2 match by accident** — `scored_rule_selected` and
  `rule_gate_evaluated` contain `'rule'` and render `s-warn` as if they were
  the recommender's `rule_check`. The dispatch's "every procedure-engine kind
  falls to neutral" is therefore *slightly wrong in the direction that makes
  the defect worse*: the sniff produces both false-neutrals **and**
  false-positive colour matches.
- The typed path is not clean either **[correction]**: `entity_resolution`,
  `economic_impact`, and `action_verification` (all added after the original
  three) also fall to `s-neutral`. Only the original 3 example kinds colour
  correctly — later additions rotted silently on both paths.
- Render call-sites (grep-verified): `O.reasoningTrace` — `view-monitor.js:344`
  (View H, the governed spine), `view-anomaly.js:78` (View B),
  `view-story.js:302`, `:592` (scripted story). `view-flow.js` renders its own
  trace UI via the duplicated local `kindClass` at `:132`, `:134`.
- **[new fact the dispatch missed]** `view-story.js:71-81` feeds
  `O.reasoningTrace` **synthetic kinds `query` / `rule` / `llm`** that only
  colour correctly *because of* the substring sniff. An explicit map breaks
  them unless they are normalized (Step 3) or aliased.

### What is NOT broken (do not re-litigate)

- View H **does** show the human approver: `view-monitor.js:316-326` extracts
  `gate_principal_recorded.principal_id`; `:335-341` renders the
  `data-testid="step-approver"` chip whose tooltip states it is the
  server-resolved person_id, not the cosmetic typed identity.
- Trace `summary` strings are already plain English and deterministic:
  `action_step.py:673-676` ("gate resolved by principal 'p-001' — the
  approving human recorded…"), `action_step.py:719-721` ("human-approved;
  executed handler 'X'"). **Only the badge token is raw.** This PLAN does not
  claim the trace prose is unreadable.

### Styling / conventions substrate (Subject B inputs)

- `theme.css` `:root` token vocabulary at
  `services/api/static/assets/theme.css:50-93`: surfaces, lines, text ramp,
  accent, semantic status (`--ok/--info/--warn/--crit/--neutral` +
  `-bg`/`-line`), type (IBM Plex, vendored under `assets/fonts/` —
  dispatch-verified), radii, shadow.
- `components.js` is the de-facto component library; public contract exported
  on `window.OCT` at `components.js:214-218`: `h, clear, icon, badge, typeTag,
  entityChip, fmtValue, fmtTimestamp, detailRows, reasoningTrace, kvDump,
  loadingState, errorState`. Ontology-aware (vocabulary from `GET /meta`).
- Security convention in-code at `components.js:15-19`: `html:` is the ONLY
  innerHTML sink; never pass untrusted/LLM text (backed by the strict CSP at
  `services/api/main.py:68-94` — dispatch-verified).
- Provenance-class precedent: `view-procedures.js:23-25` tags fields
  `authoritative-typed` / `advisory-prose` / `llm-assist`.
- No build step: "To change the UI, edit `services/api/static/` directly …
  there is no separate build step"
  (`docs/design/0013-oct-ui-provenance.md:64-65` — dispatch-verified). No
  `package.json`, no bundler, no JS/CSS linter, no frontend test runner
  (dispatch-verified; consistent with the IIFE/`window.OCT` module style read
  on disk) → **the AC-3 tripwire must be a Python test**.
- `?v=` cache-bust convention: `docs/runbooks/run-oct-demo.md:700-705` (§6c).
- `docs/conventions/` today has **no `ui*.md`** (directory enumerated;
  14 files, none UI). `code-style.md` is Python-only (dispatch-verified).
- `docs/design/0013-oct-demo-claude-design-prompt.md:3` — "Status: Draft
  (Code-authored working note — not governance)". Carries the real design
  opinion (control-tower tone; ontology-driven make-or-break principle at
  `:14-18`) but is a one-shot generation prompt, never maintained.

## LOCKED (Cray-ratified 2026-07-17 — rendered faithfully; do NOT re-litigate)

- **L-1** One PLAN, two subjects: (A) deterministic trace-attribution
  legibility; (B) `docs/conventions/ui.md`.
- **L-2** The LLM-narrated advisory layer is an **Open Question, not built
  now** (see Open Questions — reasoning lineage recorded, nothing scheduled).
- **L-3** `ui.md` proceeds now as a **canonical** convention (ADR-0017 D5
  routing: a reference you look up deliberately → `docs/conventions/`), not a
  derived doc — so ADR-0032 OQ-2's "Rule of Three applies to docs too" is not
  violated, but the tension is stated honestly: OQ-2's spirit wants a second
  real consumer before a new doc. The honest accounting: the 0013 prompt is
  consumer #1 (it *is* the un-homed convention), agent-driven UI work under
  ADR-0032 D1's per-partner guessed hero guarantees consumer #2+, and Cray
  ratified proceeding in-session on 2026-07-17. If R2 review finds this
  accounting unconvincing, the escalation path is Cray, not silent scope-drop.
- **L-4 — badge colour-axis split (Cray-ratified at R2, AskUserQuestion
  2026-07-17 session 143): colour = mechanism, glyph = actor.** The colour
  channel keeps the existing `theme.css` semantics
  (`--ok/--info/--warn/--crit/--neutral`) — the demo's current look does
  **not** shift (load-bearing: View B is on the ADR-0032 D1 wedge path). A
  separate small glyph on the badge carries the actor axis (human / LLM /
  deterministic machine), reusing the in-repo stroke icon set
  (`components.js:37-58`) — no icon dependency. **The `s-human` class
  originally drafted in Step 1 is dropped** — an actor-coloured class is
  exactly what this decision replaces; `theme.css` gains only
  `.badge.unmapped`. Do not re-litigate.

## Surfaced Decisions

### SD-1 — Typing `ReasoningStep.kind` (Cray must ratify; the PLAN executes option (c) unless Cray picks otherwise)

**Question.** Should `ReasoningStep.kind` become a typed vocabulary
(enum/Literal), now that a canonical kind inventory exists?

**Why this is a Cray decision, not a Code judgment call.** ADR-0007 pins
`kind: str` verbatim in its Accepted body (`0007:86-91`). Changing it — or
building code that contradicts it — touches an Accepted ADR's contract, which
is above Code's pay grade (§1 precedence; the G1 gate exists for exactly this).

**Options and real costs:**

- **(a) Amend ADR-0007.** An Accepted-body edit — G1 does *not* lift with
  in-context approval; route = plan-drafter-authored amendment ratified in one
  pass. Cost: contract churn on a heavily-referenced ADR; and typing `kind`
  alone is **not sufficient** — the raw-dict vocabulary carries extra top-level
  keys (`principal_id`, `action_id`, `counts` — see Substrate) that are not
  `ReasoningStep`-shaped at all, so an honest amendment must decide the whole
  two-vocabulary question, not just the field type.
- **(b) New superseding trace/attribution-contract ADR.** Cleaner scope than
  (a), but the same two-vocabulary problem, plus it plants a flag in territory
  `actions.py:71` / ADR-0007:98 explicitly reserve for the **future
  audit-framework ADR (ADR-011)**, which `audit_log.py:17-18` gates on real
  partner data — and ADR-0032 D2 gates the roadmap on one real pilot.
- **(c) Keep `kind: str`; the vocabulary lives in the label map + the CI
  tripwire only (no runtime validation).** Zero migration risk (historical
  JSONB rows keep reading), zero ADR churn, and the tripwire still delivers
  the anti-rot property this PLAN needs. Cost: the vocabulary is enforced at
  CI-time, not runtime — a dynamically-constructed kind (none exist today; all
  22 are literals) would evade it until rendered.

**Migration hazard (either typed option):** existing `StepResult.reasoning_trace`
JSONB rows hold the raw-dict shape; a tightened validator on the read path
fails closed on historical runs (AC-13 only-when-supplied precedent class).
**Hash note (verified):** trace `kind` feeds no config/governance hash
(`governance_pin.py` hashes definition-side `Step.kind` only) — so the hazard
is the read path, not resume-fail-closed.

**Recommendation: (c) now**, with the typed contract explicitly deferred to
the ADR-011 audit-framework moment (where actor/attribution schema belongs per
ADR-0007:98's own reservation). The label map becomes the de-facto vocabulary
registry the future ADR can promote.

### SD-2 — `docs/design/0013-oct-demo-claude-design-prompt.md`'s relation to `ui.md` (recommendation stated; Cray ratifies with the PLAN)

**Question.** Once `ui.md` is canonical, what is the 0013 prompt?

**Options:** (i) mark it *derived* — wrong: ADR-0017 D6 "derived" means
corrected-against-canonical forever, inverting reality (the prompt is the
*source* of the tone, and it is a one-shot input artifact, not a living doc);
(ii) mark it *superseded* — overshoots: its generation-provenance value (how
the UI was actually produced, PLAN-0013 Steps 3–5) is not superseded by a
convention doc; (iii) **leave it as a dated historical record + a one-line
header annotation** pointing at `ui.md` as the living home of the tone/design
opinion — no body rewrite, nothing silently orphaned.

**Recommendation: (iii).** Cheap, honest, reversible.

## Acceptance Criteria

Each AC states its pre-committed pass/fail read. "Preview probe" = a
`preview_eval` DOM assertion against the running demo (fixed-port launch per
`.claude/launch.json`; `?v=` bumped first per §6c) — execution-time evidence,
not CI.

- [ ] **AC-1 — one map, one source.** A single kind→label map exists as one
  static-asset source of truth; both `components.js` and `view-flow.js` consume
  it; the duplicated substring sniff is gone.
  **Read:** `Grep kindClass services/api/static/assets/` → 0 definition sites
  remain (helper renamed) or exactly 1 shared site; `Grep "includes('rule')"
  services/api/static/assets/` → 0 matches.
- [ ] **AC-2 — mapped kinds render plain English + the actor glyph; raw token
  preserved.** The badge for a mapped kind shows the label (e.g.
  `gate_principal_recorded` → "Human resolved the gate") **and carries the
  actor glyph per L-4** (colour stays mechanism-semantic); the raw kind token
  remains inspectable (title tooltip or detail row) — an auditor can always
  recover the exact engine token.
  **Read:** preview probe on a View H run trace: the
  `gate_principal_recorded` step's badge `textContent` equals the map's label,
  its `title` (or a sibling mono element) contains the literal string
  `gate_principal_recorded`, AND `badge.dataset.actor === 'human'` with an
  SVG glyph child present. Same probe on View B for `llm_inference` → label +
  `s-info` class retained + `data-actor === 'llm'` + glyph present.
- [ ] **AC-3 — the anti-rot tripwire.** A Python test (proposed:
  `tests/api/test_trace_kind_labels.py`) scans `services/engine/**/*.py` for
  literal kind emissions (both the raw-dict `"kind": "..."` and the typed
  `kind="..."` forms), and asserts **set equality** between the scanned
  vocabulary and the map's keys (plus an explicit, initially-empty alias
  allowlist). Covers both trace vocabularies by construction. A scan-health
  assertion (≥ 20 kinds found) prevents a regex refactor from passing
  vacuously (the `|| echo` false-pass class). The test **also asserts every
  map entry carries an `actor` value from the closed set
  `{"human","llm","engine"}`** — a new kind cannot be added with a label but
  no attribution (L-4's facet is tripwired, not hoped-for).
  **Read:** test green on the branch; then three one-off RED mutations, run
  locally and documented in the PR body: (1) delete one map entry → RED;
  (2) add a fake `"kind": "zz_new_kind"` emitter line in a scratch engine file
  → RED; (3) set one entry's `actor` to an out-of-set value (e.g. `"robot"`)
  → RED. All reverted before merge.
- [ ] **AC-4 — unknown kinds degrade visibly and honestly.** An unmapped kind
  renders its raw token verbatim in a dedicated *unmapped* style (dashed
  outline + tooltip "unmapped trace kind — raw engine token") that is visually
  distinct from every `s-*` semantic class — never silently `s-neutral`
  (neutral must mean "deliberately labelled neutral", not "fell through").
  **An unmapped kind renders NO actor glyph and `data-actor="unknown"`** — an
  unknown kind has no known actor, and defaulting to a machine glyph would
  assert an attribution we do not have (the exact dishonesty class this PLAN
  exists to kill).
  **Read:** preview probe injecting
  `O.reasoningTrace([{kind:'zz_unmapped_probe', summary:'x'}])` into a scratch
  container: badge `classList` contains the unmapped class and none of
  `s-ok/s-info/s-warn/s-crit/s-neutral`; badge text === `zz_unmapped_probe`;
  `badge.dataset.actor === 'unknown'`; zero SVG glyph children on the badge.
- [ ] **AC-5 — view-story normalized.** `view-story.js`'s synthetic trace
  kinds (`query`/`rule`/`llm`, `:71-81`) are normalized to canonical kinds
  (`ontology_query`/`rule_check`/`llm_inference`) so the story view renders
  mapped labels, and the map stays exactly the engine vocabulary (no demo
  aliases).
  **Read:** `Grep "kind: 'query'|kind: 'rule'|kind: 'llm'"
  services/api/static/assets/view-story.js` → 0; preview probe on the story
  view trace: zero unmapped badges. (The `:400-405` pipeline-diagram `kind`
  fields are a *different, local* vocabulary not fed to `reasoningTrace` —
  out of AC-5's blast radius; touch them only if trivially safe.)
- [ ] **AC-6 — `docs/conventions/ui.md` exists and is canonical.** It covers,
  with `file:line` anchors: (1) purpose + canonical status + the L-3 OQ-2
  accounting; (2) the `theme.css:50-93` token vocabulary + semantic status
  classes; (3) the `window.OCT` component contract (`components.js:214-218`)
  with the "use it, don't re-invent it" rule; (4) the trace-kind label map + the L-4
  channel split (colour = mechanism, glyph = actor) + the unmapped convention
  (Subject A's output, now convention); (5) the
  `html:`-only-innerHTML security rule (`components.js:15-19`) + CSP pointer;
  (6) the no-build-step rule + the `?v=` cache-bust rule (runbook §6c);
  (7) the ontology-driven principle (render from `GET /meta`, zero UI-code
  change per vertical); (8) the control-tower tone (dense, glanceable, calm
  under load, trustworthy — not playful); (9) the provenance-class labelling
  precedent (`view-procedures.js:23-25`); (10) SD-2's relation statement for
  the 0013 prompt; (11) a one-line glossary note disambiguating definition-side
  `Step.kind` (hashed) from trace-entry `kind` (not hashed).
  **Read:** an 11-item checklist pass over the merged file — each item present
  with its anchor; `docs/conventions/` is not gate-blocked (G1/G2 scope =
  `docs/adr/` + `docs/plans/` only), so Code writes it directly.
- [ ] **AC-7 — 0013 prompt annotated, not rewritten (SD-2 (iii)).** One-line
  header annotation pointing at `ui.md`; no body change.
  **Read:** diff shows exactly the header line(s) added; body untouched.
- [ ] **AC-8 — no live-model or network dependency introduced (ADR-0032
  D1(3), `0032:110`).** The map is a static asset; no new fetches beyond the
  existing static/`/meta` surface; nothing in this PLAN touches MS-S1.
  **Read:** `Grep "fetch(" ` over changed asset files → no new non-static
  endpoints vs `main` (diff review in R2).
- [ ] **AC-9 — cache-bust honoured.** The shared `?v=` token in
  `services/api/static/index.html` is bumped in the same PR that changes
  assets (runbook `:700-705`).
  **Read:** PR diff contains the token bump.

## Out of Scope

- ❌ **Typing `actor_kind` / promoting it to an `audit_log` column.** It lives
  inside `payload` JSONB (`action_step.py:700`, `persistence.py:137-141`) and
  is unqueryable — a real limitation, deliberately untouched: ADR-0007:98
  reserves actor schema for the future audit-framework ADR; `audit_log.py:17-18`
  defers that framework pending real partner data; ADR-0032 D2 gates the
  roadmap on one real pilot. Building it here would claim a deferred ADR's
  territory.
- ❌ **Any LLM-generated label or narration** (L-2; Open Questions).
- ❌ **Extracting a shared component-library abstraction.** ADR-006 D4 Rule of
  Three: there is ONE app, not the 10–20 the talk addresses; `components.js`
  is already ontology-aware.
- ❌ **Multi-agent / orchestrator node-graph visualisation** from the talk.
  ADR-0032 D4 (`0032:169-186`) PARKs governed agent-interop; building its UI
  would contradict the ADR.
- ❌ **Integrating the Ask view into the main workflow** (the talk's mistake
  #2). ADR-0032 D1(3) (`0032:110`) requires the demo run the deterministic
  offline arm; Ask depends on MS-S1 live and is off the wedge path.
- ❌ **Fixing `aggregate`/`outcome` being dropped at
  `services/api/routers/query.py:19-29`** (collapsing `clarify` into
  `no_data`) — recorded as Finding F-2 for a separate PLAN; not fixed in
  passing.
- ❌ **Fixing the ADR-0007 3-vs-4 `actor_kind` drift.** Recorded as Finding
  F-1; an Accepted ADR is never silently corrected.
- ❌ **Runtime validation of `StepResult.reasoning_trace` dicts** — SD-1
  territory; option (c) explicitly defers it.

## Steps

### Step 0 — re-verify the substrate (cheap, pre-committed)

Re-run the kind-inventory greps (`"kind": "..."` and `kind="..."` over
`services/engine/`) and confirm the 22-kind table above is still exact; re-read
`components.js:145-151` / `view-flow.js:189-195` / `view-story.js:71-81`.
Confirm the two dispatch-verified facts an AC touches: the CSP block
(`main.py:68-94`) and the no-build-step statement
(`0013-oct-ui-provenance.md:64-65`). Any drift → update the map + table in the
same PR, not silently.
**Pass/fail read:** the scanned set matches the table (or the PR documents the
delta).

### Step 1 — the map asset + shared helper (Subject A core)

Create `services/api/static/assets/trace-kinds.js` defining
`window.OCT_TRACE_KINDS` as a **strict-JSON object literal between two
delimiter comments** (`/* TRACE_KINDS_JSON_BEGIN */ … /* TRACE_KINDS_JSON_END
*/`), so the Python tripwire extracts and `json.loads` it — one source of
truth readable by both the browser (no build step, no async fetch: plain
`<script>` before `components.js`) and CI. Each entry:
`{"label": <plain English>, "cls": <badge class>, "actor":
"human"|"llm"|"engine"}` — the `actor` facet drives the glyph channel (L-4)
and is machine-readable by construction (resolves former OQ-2). Draft
label/class/actor table (label wording and mechanism-colour picks refinable at
R2 **without** re-ratification; the binding parts are: full coverage, a
correct closed-set `actor` on every entry, and L-4's channel split — colour
stays within existing `theme.css` semantics, actor never rides the colour
channel):

| kind | label (draft) | cls (mechanism, draft) | actor |
|------|---------------|------------------------|-------|
| `gate_principal_recorded` | Human resolved the gate | `s-warn` (governance gate) | `human` |
| `action_executed` | Human-approved — action executed | `s-ok` (executed effect) | `human` |
| `action_rejected` | Human rejected the action | `s-neutral` (disposition) | `human` |
| `action_proposed` | Action proposed — awaiting human | `s-neutral` | `engine` |
| `llm_inference` | LLM inference | `s-info` | `llm` |
| `ontology_query` | Ontology query (deterministic) | `s-ok` | `engine` |
| `read_provenance` | Read from ontology (deterministic) | `s-ok` | `engine` |
| `read_passthrough` | Read — passthrough (deterministic) | `s-ok` | `engine` |
| `join_pipeline` | Join pipeline (deterministic) | `s-ok` | `engine` |
| `entity_resolution` | Entity resolution (deterministic) | `s-ok` | `engine` |
| `rule_check` | Rule check (deterministic) | `s-warn` | `engine` |
| `rule_gate_evaluated` | Rule gate evaluated (deterministic) | `s-warn` | `engine` |
| `scored_rule_selected` | Scored rule selected (deterministic) | `s-warn` | `engine` |
| `tier_authority` | Authority-tier check (deterministic) | `s-warn` | `engine` |
| `doa_tier_resolved` | DOA tier resolved (deterministic) | `s-warn` | `engine` |
| `severity_tier_resolved` | Severity tier resolved (deterministic) | `s-warn` | `engine` |
| `verdict_computed` | Verdict computed (deterministic) | `s-warn` | `engine` |
| `transform_provenance` | Deterministic transform | `s-neutral` | `engine` |
| `economic_impact` | Economic-impact estimate (deterministic) | `s-neutral` | `engine` |
| `action_verification` | Action verification (deterministic) | `s-warn` | `engine` |
| `read_refused` | Read refused (governance) | `s-crit` | `engine` |
| `error` | Step error | `s-crit` | `engine` |

View B's wedge-path badges keep their exact current colours
(`llm_inference`→`s-info`, `rule_check`→`s-warn`, `ontology_query`→`s-ok`) —
L-4's "demo look does not shift" holds for the dominant path.

Add to `components.js` a shared `traceKind(kind)` helper returning
`{label, cls, actor, unmapped}` (exported on `window.OCT`); rewire
`reasoningTrace` (`:159`, `:164`) to render the label with the raw token in
`title`, plus the **actor glyph** and a **`data-actor` attribute** on the
badge (the probe-able channel — `icon()` silently falls back to `dot` for an
unknown name, `components.js:63`, so the SVG itself is not testable); delete
`kindClass` from both files and rewire `view-flow.js:132,134` to the shared
helper. Glyphs: reuse the in-repo stroke set (`components.js:37-58`, no
person glyph exists today) — candidates: human = `check` (consistent with the
existing approver chip, `view-monitor.js:340`) *or* one new in-repo `person`
path added to `ICONS` (an in-repo SVG string, not an icon dependency); llm =
`spark`; engine = `cpu`. Exact picks are executor's call; the binding
requirements are: the three actor glyphs are mutually distinct, and an
**unmapped kind renders NO actor glyph** (AC-4). `theme.css` gains **only**
the `.badge.unmapped` style (dashed outline) — no `s-human`, per L-4.
**Pass/fail read:** AC-1, AC-2, AC-4 probes.

### Step 2 — the tripwire test

`tests/api/test_trace_kind_labels.py`: regex-scan `services/engine/**/*.py`
for both literal emission forms; extract the JSON block from `trace-kinds.js`;
assert set equality (modulo the explicit empty allowlist) + the ≥20 scan-health
floor + every entry's `actor` in the closed set (AC-3). R2 pre-confirmed the
scan is collision-safe against the `StepKind` StrEnum (`spec.py:54-61` — 0
hits; see Substrate). Note in the test docstring: docstring mentions of `kind="..."` (e.g.
`llm/trace.py:5-11`) are harmlessly caught — they name real kinds; a
dynamically-built kind would evade the scan (accepted residual under SD-1(c)).
**Pass/fail read:** AC-3, including the two documented RED mutations.

### Step 3 — normalize view-story's synthetic kinds

Replace `query`/`rule`/`llm` at `view-story.js:71-81` with
`ontology_query`/`rule_check`/`llm_inference`. Check the scripted copy still
reads correctly with the new labels (story tone is demo-facing).
**Pass/fail read:** AC-5.

### Step 4 — author `docs/conventions/ui.md` (Subject B)

Write the 11-item convention doc per AC-6, lifting the tone verbatim-where-good
from the 0013 prompt and citing live anchors. Include the trace-kind map's
*convention* (the map file is the registry; adding an engine kind requires
adding a label — the tripwire enforces it) so future agents learn the rule
where they look for UI rules. Add a one-line cross-pointer from
`docs/conventions/code-style.md` ("UI work → `ui.md`") — code-style is
Python-only today, so the pointer prevents the obvious miss.
**Pass/fail read:** AC-6 checklist.

### Step 5 — annotate the 0013 prompt (SD-2 (iii)) + cache-bust + verification pass

Header-annotate `docs/design/0013-oct-demo-claude-design-prompt.md`; bump
`?v=`; run the preview probes (AC-2/AC-4/AC-5) against a launched demo config;
run the full test suite.
**Pass/fail read:** AC-7, AC-9 + the probe transcript in the PR body.

### Step 6 — PR(s) + findings surfaced

Recommended split: **PR-A** (Steps 0–3, 5: code + test + probes) and **PR-B**
(Step 4 + the 0013 annotation: docs-only) — independently revertable, per §7
PR flow. Either PR body flags Findings F-1/F-2 to Cray explicitly (recorded,
not fixed).

## Findings (recorded, NOT fixed here)

- **F-1 — ADR-0007 `actor_kind` drift.** ADR-0007:100 enumerates 3 values;
  the runtime audit stream also emits `"service"`
  (`persistence.py:132-141`, PLAN-0053) — into an audit-payload dict, not an
  `AuditMetadata` instance (the model itself is instantiated only with
  `engine`/`llm`; `human` appears in gate-decision payloads,
  `action_step.py:700`). Also noted: code `AuditMetadata` carries
  `governed_decision` (`actions.py:77-82`, ADR-0026 D6) beyond the 0007 pin —
  documented extension, listed for completeness. Route: the ADR-011
  audit-framework moment, or an ADR-0007 amendment batch if SD-1(a) is chosen.
- **F-2 — `services/api/routers/query.py:19-29` drops `aggregate`/`outcome`**
  (collapses `clarify` into `no_data`) — Code-reported during grounding
  (2026-07-17); **not re-verified by this draft**; suspected real bug; needs
  its own PLAN (NL-query surface couples the benchmark gold set — see the
  energy-events/gold coupling memory).
- **F-3 — fact-pack erosion class.** The dispatch's 9-kind list vs the
  verified 22 (and the "all neutral" claim vs the 2 accidental `'rule'`
  matches) is itself an instance of the rot AC-3 kills: prose inventories of
  code vocabularies go stale silently. The tripwire, not better prose, is the
  fix (same lesson as the `spec.py` stale-count incident).

## Open Questions

- **OQ-1 — an LLM-narrated `advisory-prose` layer (Cray-ratified OQ; nothing
  scheduled).** Cray's proposal: MS-S1 with a dynamic system instruction +
  context-aware prompt producing short human-readable narration, raw fallback
  when MS-S1 is unreachable. Code's counter, which Cray accepted: (a) it
  inverts ADR-0032 D1(3) — the offline arm means the partner meeting would
  always render the fallback, so the polish exists only in rehearsal; (b) an
  attribution label asserting "an LLM did this" that is *itself* LLM-generated
  is non-reproducible and undercuts ADR-0032 D5's claim that an auditor can
  rely on it; (c) CLAUDE.md §8 gates MS-S1 host-state runs, and session 99's
  reason-then-structure A/B measured NULL lift and kept the baseline. The
  surviving idea worth keeping: narration may belong **above** the trace — a
  run-level "why did this need the CONTROLLER to sign?" summary for a
  non-technical reader — rather than on the attribution channel; the talk's
  actual insight was "help the analyst understand quickly *rather than*
  exposing the full LLM reasoning". `view-procedures.js:23-25`'s
  `advisory-prose` class is the precedent for where such prose would sit.
  Revisit when pilot fuel exists (ADR-0032 D2) — likely alongside ADR-011.
- **OQ-2 — should the label map eventually feed a machine-readable actor
  facet** (each entry gaining `"actor": "human"|"engine"|"llm"`) for a future
  audit dashboard?
  **RESOLVED (2026-07-17, at R2 — by Cray's L-4 colour-axis ratification, not
  by drift).** Raised as an OQ in rev 1 (drafter deliberately excluded the
  facet as SD-1/ADR-011 territory); Cray's ratified glyph channel *requires*
  the facet (the glyph must be driven by data, not by another substring
  sniff), so it moved into the map schema now — each entry carries
  `actor ∈ {"human","llm","engine"}`, tripwired by AC-3. The rev-1 `s-human`
  class this OQ referenced was dropped by the same ratification. The *future
  audit-dashboard* use of the facet remains ADR-011 territory — only the
  render-side facet landed here.

## Verification

1. `uv run pytest tests/api/test_trace_kind_labels.py` green + the two
   documented RED mutations (AC-3).
2. Full suite green on the branch (per-checkout DB rules; Docker Postgres up).
3. Preview probes per AC-2/AC-4/AC-5 against a launched demo (fixed port,
   `?v=` bumped) — probe transcript pasted into PR-A's body.
4. Grep reads per AC-1/AC-5/AC-8.
5. AC-6 11-item checklist against the merged `ui.md`; AC-7 diff read.
6. R2 (Code) reviews this PLAN against the substrate before executing —
   especially the 22-kind table (Step 0 re-verifies it on execution day).

## Size estimate

**S/M.** Subject A: one focused session (map + rewire + test + probes);
Subject B: one docs session. Two small PRs. No migration, no schema change,
no host-state action anywhere.
