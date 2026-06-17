---
plan: PLAN-0028
title: B-γ extension — three-arm procedure comparison for aquaculture + supply_chain (PLAN-0027's natural successor frontier; PLAN-0019 Step B-γ generalised cross-vertical)
status: Accepted
owner: Claude Code
created: 2026-06-17
related_plans:
  - PLAN-0027 (B-γ comparison methodology pre-registration + energy build/run — THIS plan extends it to two more verticals; D-1..D-6 + SD-1..SD-4 + the joint SD-1↔SD-2 fairness binding are INHERITED verbatim, not re-opened)
  - PLAN-0019 (Core Procedure baseline — B-γ / AC B-3 is the parent step; arm (a) per-vertical β headlines are REUSED from its REPORT)
  - PLAN-0020 (latency tuning — the SD-2 ≤ 30 s p95 per-judgment unit + the per-vertical nudged arm-(a) numbers reused for the join)
  - PLAN-0022 (watch-tier lane — the per-vertical breach datasets this plan slices were authored/hardened there)
related_adrs:
  - ADR-016 (governed procedure engine — the stack arm (a) measures; the future verify+reshape layer stays a §3.4 forward-pointer, OUT OF SCOPE here as in PLAN-0027)
  - ADR-001 (LLM model baseline — gpt-oss:20b pin = the scored-run model for arms b + c; NOT qwen3.x)
  - ADR-009 (D1 interim authoring; D2 only-Code-commits)
  - ADR-012 (D4.3 author≠reviewer disclosure)
  - ADR-013 (autonomy-axis relocation — phased; plan-drafter interim authoring)
authored_by: plan-drafter subagent (in-harness; draft body) + Cowork session-65 (OQ-1 external-grade RAG-fairness re-look + materialization; ADR-009 D1 interim authoring under ADR-013 phased relocation — uncommitted draft; Code commits per ADR-009 D2)
---

# PLAN-0028 — B-γ extension to aquaculture + supply_chain

> **Drafting provenance / author≠reviewer disclosure (ADR-012 D4.3).**
> Drafted (uncommitted) by the in-harness `plan-drafter` subagent under ADR-009
> D1 interim authoring per ADR-013's phased relocation. The outline originator
> was **Cray** (founder, this session, via the handoff session-64 §3 item 1
> "PLAN-0019's natural successor frontier"): the scope — extend the executed
> energy three-arm comparison (PLAN-0027 / the B-3 REPORT) to the **aquaculture**
> and **supply_chain** verticals, honouring all of PLAN-0027's locked decisions
> and the joint SD-1↔SD-2 fairness binding, with the **external-grade RAG-fairness
> re-look** surfaced as the headline Open Question for a fresh creative/adversarial
> Cowork perspective. This draft renders and cross-checks that scope against the
> live `benchmarks/procedure_comparison/` harness (confirming it is
> vertical-parameterizable), the existing per-vertical breach datasets, the energy
> corpus pattern, the two target ontologies, and PLAN-0027 §3–§4 + its SD binding,
> and surfaces residual choices as **Open Questions** (§8) rather than silently
> resolving them.
>
> **OQ-1 re-look provenance + author≠reviewer flag (ADR-012 D4.3 — NEW this
> materialization).** The headline OQ-1 (external-grade RAG-fairness re-look) was
> **performed by Cowork (session 65)** at materialization — the fresh
> creative/adversarial perspective the session-64 handoff and the Code dispatch
> explicitly routed here. Cowork's re-look outcome is **folded into §3.2 / §3.5 /
> §4 (AC-3, AC-4) / §8 (OQ-1, OQ-4)** as **pre-registered recommendations**, all
> **bounded to the corpus + prompt levers (D-6 intact)**. Because Cowork both
> **authored the OQ-1 recommendations** and **materialized this draft**, the
> independent-deliberation check on those recommendations was **not** exercised by
> a second author — **the remaining independent check is Cray at ratification**
> (AC-1; the methodology delta is fixed BEFORE any scored run per B-6). The
> `plan-drafter` (draft body) ≠ Cowork (OQ-1 re-look + materialization) ≠ Cray
> (ratification) separation is otherwise INTACT; Cowork holds **no commit
> authority** (Code commits per ADR-009 D2).
>
> This PLAN **does NOT re-open** any ratified PLAN-0027 decision (D-1..D-6, the
> SD-1..SD-4 resolutions, the joint SD-1↔SD-2 binding, the D-6 contamination
> guard, the §3.4 forward-pointer, the reports-not-gates ring-fence). It
> **generalises the same methodology to two more verticals**, inheriting all of
> it verbatim. The one genuinely new governance moment is the **external-grade
> RAG-fairness re-calibration** (OQ-1) — and even that is bounded to the corpus +
> prompt levers (D-6 stays intact).

## 1. Status

**Accepted.** Cray ratified this PLAN 2026-06-17 (session 67). All work is
complete — this is a formal flip of already-executed, already-Cray-approved work,
not a new decision.

### 1.0 Ratification record (Cray, 2026-06-17, session 67)

Cray ratified, in-session:

- **OQ-1 — the external-grade RAG-fairness re-look outcome** (R-OQ1-1..4: corpus
  richness · the retriever near-oracle caveat · the template-neutrality fix · the
  two-sided over+under coverage guard), and the methodology **delta** (the two
  corpora + the three parameterizations incl. the threshold-noun ceiling/floor
  fix) — ratified **before the scored run** per the inherited PLAN-0019 B-6
  anti-moving-target discipline.
- **OQ-2** — the arm(a)≈arm(c) tie **replicates cross-vertical** (canonical
  aquaculture 100% / supply_chain 100%, post-calibration).
- **OQ-3** — the aquaculture join reads against the nudged **100%**, with the
  60→100% hardened→nudged range disclosed in the REPORT.
- **OQ-4** — the three mechanical harness parameterizations (RAG persona · unit
  map · threshold-noun ceiling/floor) confirmed in-scope.
- **OQ-5** — **ONE combined scored sweep** (executed).

**Completion.** All 6 Steps executed; **AC-1..AC-7 met**. The Step 5 scored sweep
ran + was VERIFIED (`gpt-oss:20b` @ MS-S1, 80 breach items, 0 errors / 0 invalid).
Step 6 — the B-3 REPORT cross-vertical extension — shipped (#355, `d48b770` /
`7275a69`). The canonical numbers were folded via PLAN-0029.

### 1.1 INHERITED locked decisions (from PLAN-0027 — recorded, do NOT re-open)

This extension runs **the identical methodology** PLAN-0027 pre-registered and
Cray ratified for energy. The following are inherited **verbatim** and are NOT
re-litigated here:

| ID | Inherited decision (PLAN-0027) | How it applies per-vertical |
|---|---|---|
| **D-1 (common graded sub-task)** | Every arm is graded on "name the affected entity + name the correct action class," reusing `Expected.{affected_primary_key, action_keywords}` + `grade_proposal`. Arm (c) consumes a **`_reduced_expected`** that declares ONLY `affected_primary_key` + `action_keywords` (no `forbidden_*` precision add-ons). | aquaculture action lemmas `[aerat, oxygenat]`; supply_chain `[hold, inspect, quarantine, divert]` (from the existing datasets). **Disclosure caveat — see §3.5 D.** |
| **D-2 (arm a reuse)** | Arm (a) = the existing governed-procedure stack; **REUSE the REPORT numbers, do NOT re-run.** | Per-vertical arm-(a) β headlines **already exist** in the REPORT (see §2 — this is the resolved arm-a question). |
| **D-3 (arm b)** | Arm (b) = raw text-to-SQL; graded entity-ID only; "action-class structurally N/A" IS the finding. | Per-scenario in-memory SQLite already synthesised generically from the `Scenario` (no vertical `synthetic.py` binding). |
| **D-4 (arm c)** | Arm (c) = lean-but-real RAG: small static corpus + deterministic top-k lexical retriever (NO vector store) → freeform answer → grade entity + action. | **One new corpus YAML per vertical** is the only genuinely new authored artifact. |
| **D-6 (contamination guard — BINDING)** | Arm (c) stays a CLEAN naive RAG baseline — NO verify/reshape/governance/ontology layer bleeds in. | Re-asserted per-vertical in code review of Step 2 (arm c imports no `services.engine.procedures` symbol; exactly one LLM call per item). **OQ-1's fairness re-look stays inside this guard — corpus + prompt levers only.** |
| **Joint SD-1↔SD-2 binding (BINDING)** | Under the locked lexical retriever, each corpus must share surface vocabulary with the question template AND cover **every** breach item's `action_keywords` lemma with ≥1 snippet — else an arm-(c) miss is a *retrieval artifact*, not a paradigm limit. | **The load-bearing per-vertical authoring constraint** — see §3.2 + AC-3. **OQ-1 strengthens this to a joint over- AND under-cover guarantee — §3.5 D.** |
| **Reports-not-gates (B-3/B-6)** | A baseline tying or beating arm (a) is a **finding**, not a build failure; no bar moves, ADR-016's shape is never reopened. | Inherited verbatim; restated in the REPORT extension header. |
| **§3.4 forward-pointer (verify+reshape)** | The future verify+reshape procedure-engine enhancement is a forward-pointer, OUT OF SCOPE, NOT added to arm (c). | Inherited; the extension is measurement-only, same as the energy pass. |

## 2. Context — what already exists (the scope-shrinking discoveries)

The dispatch asked to **verify** the claim "the extension is a new corpus per
vertical + the dataset subset, not new harness code," and to **investigate**
whether arm-(a) baselines exist for aquaculture/supply_chain. Both were checked
against the live code + REPORT (Cowork re-verified every file/symbol/number cited
below against the live repo at materialization — Tier-1 fact-pack discipline).
Findings:

**(1) The comparison harness is genuinely vertical-parameterizable — confirmed
(with THREE small mechanical exceptions, not two).** `benchmarks/procedure_comparison/run_comparison.py`
already accepts `--dataset` and `--corpus` flags and threads `dataset.reading_parameter`
generically through both arms (verified: lines 125–126 + 100–101).
`text_to_sql_arm.build_scenario_db` synthesises the in-memory SQLite **from the
self-contained `Scenario`** (breached entity + distractor siblings as rows) — it
does NOT bind any vertical-specific `synthetic.py`, so arm (b) is vertical-agnostic
as-is (verified). `rag_arm` takes the corpus as a parameter. `questions.py`
renders the SD-2 templates from generic `Scenario` fields. **So the dispatch's claim
is ~90% true.** The three spots that are still energy-specific and need a small
parameterization (NOT new arms, NOT new harness logic — surfaced as OQ-4):
  - **(i)** `rag_arm.build_rag_messages` hardcodes the system-prompt string
    **"You are an energy operations assistant."** (verified, `rag_arm.py` line 128)
    — needs a per-vertical persona so the RAG prompt is not energy-flavoured for
    the other two verticals.
  - **(ii)** `questions._UNIT_PHRASE` maps only `{celsius, hz}` (verified,
    `questions.py` line 28). supply_chain uses `celsius` (covered); **aquaculture
    uses `mg/L`** (falls through to the literal "mg/L", which is acceptable but
    should be confirmed, not assumed).
  - **(iii) NEW — surfaced by the OQ-1 re-look (template-neutrality defect).** BOTH
    `render_sql_question` (line 54) and `render_rag_question` (lines 71–72) hardcode
    the threshold **noun "ceiling"** even though the helper `_edge(direction)`
    already flips the *preposition* ("at or above" / "at or below"). For
    aquaculture (`direction=below`, a 4.0 mg/L **floor**) the rendered question
    reads *"…a dissolved_oxygen reading at or below the 4 mg/L **ceiling**…"* and
    *"a breach is a reading at or below the ceiling"* — internally contradictory
    (below a ceiling is the safe side). **This is a third mechanical
    parameterization, and a fairness fix** (see §3.5 C). Energy + supply_chain are
    `direction=above` and keep "ceiling" verbatim, so the energy pass is
    regression-safe.

**(2) Arm-(a) baselines for aquaculture + supply_chain ALREADY EXIST in the REPORT
— the arm-a question is RESOLVED (no per-vertical arm-a re-run needed).**
`benchmarks/procedure_baseline/REPORT.md` carries per-vertical breach β headlines
for all three verticals from Cray-approved host-state runs (verified):
  - **HARDENED run (2026-06-09):** aquaculture **60.0%** (24/40), energy 97.5%,
    supply_chain **100%** (40/40) — the discriminating run.
  - **PLAN-0020 R1 nudged (2026-06-11):** aquaculture **100%** (40/40), energy
    100%, supply_chain **100%** (40/40) — post prompt-nudge.

  So D-2 ("reuse arm (a), do not re-run") is satisfiable for all three verticals
  exactly as it was for energy. **No new arm-(a) host-state run is required.** The
  only nuance to surface (OQ-3): aquaculture's arm-(a) number is a **range**
  (60% hardened → 100% nudged) — the join must state which arm-(a) figure the
  comparison reads against, and acknowledge the nudge dependency, exactly as the
  energy join did (it cited 97.5–100%).

**(3) The per-vertical breach datasets already exist** — `benchmarks/procedure_baseline/dataset/{aquaculture,supply_chain}.yaml`,
each with the **40-item breach subset** (28 boundary-cluster + 12 hard
`*-h01..h12` multi-entity/near-miss items, verified by item-count) the comparison
slices via `comparison.breach_items()`. No new dataset authoring is required; the
breach subset is reused as-is (the same items arm (a) was scored on — keeping the
comparison commensurable with the reused arm-(a) β headline).

**Net scope.** The genuinely new authored artifacts are **two corpus YAMLs**
(`corpus/aquaculture_v0.yaml`, `corpus/supply_chain_v0.yaml`) honouring the joint
SD-1↔SD-2 binding per vertical (with the OQ-1 over-/under-cover design, §3.2/§3.5),
plus **three small harness parameterizations** (the RAG persona string + the unit
map + the threshold-noun ceiling/floor, OQ-4) and **per-vertical unit tests**
mirroring the existing energy offline tests. Everything else (arms, grader,
datasets, runner) is reused. This is materially smaller than the energy first-pass
(which built the arms from scratch).

## 3. Methodology delta (the ONLY things that differ from the energy pass)

PLAN-0027 §3 is inherited verbatim. The deltas, all per-vertical:

### 3.1 Arm (a) join — per-vertical (D-2, reuse)

Read arm (a)'s **breach β headline** for aquaculture + supply_chain from the
REPORT (§2 above), exactly as the energy join read 97.5–100%. State the figure
(and, for aquaculture, the hardened→nudged range — OQ-3) in the per-vertical
comparison table. **No arm-(a) re-run** (D-2).

### 3.2 Arm (c) corpus authoring — the joint SD-1↔SD-2 binding, per vertical (the load-bearing work)

Author one static corpus YAML per vertical, replicating `corpus/energy_v0.yaml`'s
pattern (threshold rule + entity snippet + per-action playbook snippets +
watch-band guidance + false-positive guard), and **honouring the joint SD-1↔SD-2
binding for that vertical**. The energy corpus is **10 snippets**; the fairness
invariant carried into the new corpora is **structural parity (same KINDS of
snippets) + the joint binding**, NOT an identical snippet count (see §3.5 A):

- **aquaculture** (`reading_parameter = dissolved_oxygen`; **breach BELOW** the
  4.0 mg/L floor — note the direction flips vs energy/supply's ABOVE; watch band
  4.0–5.0; ontology `action_type ∈ {start_emergency_aerator, dispatch_technician,
  increase_water_exchange, escalate}` (verified against
  `verticals/aquaculture/ontology/aquaculture_v0.yaml`); breach `action_keywords
  [aerat, oxygenat]`). The corpus MUST cover the `aerat`/`oxygenat` lemma (one
  consolidated emergency-aeration / oxygenation playbook snippet — §3.5 A) and
  share surface vocabulary (entity word "pond", the parameter "dissolved oxygen",
  "below"/"floor"/"crash") with the SD-2 question template. The **below-floor
  crash semantics** is the one substantive domain difference from energy's
  above-ceiling — the threshold + watch + false-positive snippets must encode "low
  DO is the breach," not "high reading."
- **supply_chain** (`reading_parameter = temperature`; **breach ABOVE** the
  8.0 °C cold-chain ceiling; watch band 6.5–8.0; ontology `action_type ∈ {reroute,
  expedite, hold, inspect, escalate}` (verified against
  `verticals/supply_chain/ontology/supply_chain_v0.yaml`); breach `action_keywords
  [hold, inspect, quarantine, divert]` on the boundary items, `[hold, inspect,
  quarantine]` on the hard items — union `{hold, inspect, quarantine, divert}`).
  The corpus MUST cover the `hold`/`inspect`/`quarantine`/`divert` lemmas (one
  consolidated cold-chain-excursion playbook snippet naming them together — §3.5 A,
  robust under k=4) AND — critically — encode the **dangerous near-miss**
  `reroute`/`expedite` as the wrong action (keep a possibly-spoiled load moving),
  mirroring the watch-lane safety signal the REPORT surfaced and at **parity** with
  energy's `isolate`/`escalate` "not the first-line action" disambiguation snippets
  (§3.5 D). Share surface vocabulary (entity word "shipment", "temperature",
  "above"/"ceiling"/"excursion").

> **Joint-binding coverage check (per-vertical, BINDING — AC-3).** For each
> vertical, every breach item's `action_keywords` lemma set MUST be covered by ≥1
> corpus snippet, AND the SD-2 question's content tokens MUST overlap the relevant
> snippet's tokens under the deterministic lexical retriever (k=4) — otherwise an
> arm-(c) miss is a retrieval artifact (externally rebuttable), not a naive-RAG
> limit. **OQ-1 strengthens this with an over-cover guard** — no snippet may name a
> specific dataset entity key (`pond-A01` / `ship-S01`); snippets state RULES /
> playbooks, never per-item answers (§3.5 D + AC-3). This is the exact constraint
> OQ-1's external-grade re-look stress-tested.

### 3.3 Arm (b) — no delta beyond the shared parameterizations

Arm (b) needs **no new arm code**: `build_scenario_db` already synthesises the DB
from the `Scenario`, and `render_sql_question` renders generically. It shares the
OQ-4 parameterizations with arm (c) (the unit-phrase map + the threshold-noun
fix — §2(1)(ii)/(iii)), since both arms consume `questions.py`. The watch-outs:
aquaculture's `mg/L` is not in `_UNIT_PHRASE` (OQ-4(ii)); and aquaculture's
direction word is "at or below" via `_edge("below")` (already handled), so once the
**threshold-noun** is parameterized to "floor" for `direction=below` (OQ-4(iii))
the aquaculture SQL question reads coherently ("…a dissolved oxygen reading at or
below the 4 mg/L floor…").

### 3.4 Inherited guardrails + the §3.4 forward-pointer

Reports-not-gates (B-3/B-6), anti-moving-target (the per-vertical corpora + the
OQ-1 template/parameter calibration are ratified BEFORE the scored run),
host-state discipline (CLAUDE.md §8), and the verify+reshape forward-pointer (OUT
OF SCOPE, NOT added to arm c) are all inherited from PLAN-0027 §3.4–§3.5 verbatim.

### 3.5 OQ-1 external-grade RAG-fairness re-look — pre-registered calibration (Cowork, session 65; within corpus+prompt levers, D-6 intact; pending Cray ratification per AC-1)

The OQ-1 headline question — *is the lean-RAG arm (c) calibrated fairly enough to
stand as an external-grade baseline?* — was re-examined adversarially against the
live harness. Outcome: **four pre-registered recommendations (R-OQ1-1..4)**, all
bounded to the corpus + prompt levers (D-6 forbids adding any verify/governance
layer). Each is a **recommendation Cray ratifies** (AC-1), not a silent choice.

**A. Corpus richness (OQ-1a) → R-OQ1-1.** ~10 snippets per vertical (energy's
size) with **structural parity** as the fairness invariant — the same snippet
KINDS energy uses (threshold rule · entity · breach-action playbook · "why the
canonical action" · watch-band guidance · action-vocab summary · false-positive /
wrong-action guard), **sized to each vertical's action vocabulary**, not pinned to
an identical count. Decisive design choice under the locked retriever: use **ONE
consolidated breach-action playbook snippet** per vertical that names all breach
lemmas together (aquaculture: `aerate`/`aeration`/`oxygenate`; supply_chain:
`hold`/`inspect`/`quarantine`/`divert`) — exactly as energy's `playbook-restart`
names restart/reset/reboot together. **Why it matters under k=4:** the retriever
returns top-4 of ~10; four *separate* supply_chain action snippets could not all
reach top-4 for one breach query, but one consolidated snippet covering the whole
graded action class **reliably ranks top-4** and satisfies the binding robustly.
*Disclose* the per-vertical snippet count + the retrieved fraction in the REPORT.
*Alternative for Cray:* match energy's exact count/shape mechanically (simpler,
but supply_chain's richer 4-lemma vocabulary then risks an under-covered lemma).

**B. Retriever choice (OQ-1b) → R-OQ1-2.** **Keep the locked deterministic lexical
top-k retriever (D-4); do NOT re-open it** — changing it both re-opens a ratified
decision (a Cray call, not a build choice) and breaks cross-vertical comparability
with the already-shipped energy result. Produce the **REPORT caveat**: under the
joint binding the action-relevant snippet is *guaranteed* surface-token-retrievable,
so lexical retrieval behaves as a **near-oracle** for the graded lemmas — a
stronger (vector) retriever could only differ where surface vocabulary diverges,
which the binding minimises. The honest external-grade framing **inverts** the
skeptic's "lexical handicaps RAG" worry: the binding makes retrieval *generous* to
arm (c), so an arm(a)≈arm(c) parity finding is **conservative** for the moat
thesis. Robustness is claimed only for corpora that honour the binding.

**C. Question-template neutrality (OQ-1c) → R-OQ1-3 (REQUIRED fix + a polish).**
The hardcoded threshold-noun "ceiling" (§2(1)(iii)) makes the SD-2 template
**non-neutral across verticals**: it is coherent for the two above-ceiling
verticals but contradictory for aquaculture's below-floor breach. Because arm (a)
is *reused* (it consumes the event via `scenario_to_event`, not these question
templates), a confusing aquaculture question depresses only arms (b)+(c) — which
would **spuriously inflate** the arm(a)–arm(c) gap on aquaculture (a false
moat-relocation signal). **Required fix:** parameterize the threshold-noun by
direction — "ceiling" for `above`, "floor" for `below`. This is *completing* the
template's existing `_edge(direction)` direction-awareness for a direction **the
energy pass never exercised** (energy is `above`); energy + supply_chain questions
stay **byte-identical** (regression-guarded, AC-4). It is a **prompt-lever (SD-2)
fix + a mechanical parameterization**, not a methodology re-open and not a D-6
breach. **Polish (optional):** render `reading_parameter` without the underscore
("dissolved oxygen" not "dissolved_oxygen") for external-grade readability — no
retrieval impact (the `[a-z0-9]+` tokenizer already splits on `_`, so the corpus's
"dissolved"/"oxygen" tokens match either way). *Alternative for Cray:* leave the
template untouched (inherited SD-2) and only **disclose** the wording mismatch in
the REPORT — weaker for an external-grade number a design partner might see.

**D. Per-vertical vocabulary coverage — over AND under (OQ-1d) → R-OQ1-4.** Pin
the joint binding as a **two-sided** guarantee:
  - *Under-cover (existing):* every breach `action_keywords` lemma covered by ≥1
    snippet AND surfaced under the k=4 retriever (per vertical — aquaculture
    `{aerat, oxygenat}`, supply_chain `{hold, inspect, quarantine, divert}`).
  - *Over-cover (NEW):* no snippet may name a dataset entity key or hand the model
    the per-item answer — snippets state the rule/playbook, so arm (c) must still
    (a) pick the breached entity from the stated readings and (b) map the breach
    condition → the action class. Asserted programmatically in AC-3 (no `pond-A`/
    `ship-S` literal in any snippet).
  - *Parity disambiguation of the dangerous near-miss:* energy's corpus
    disambiguates its non-canonical actions (`playbook-isolate` "not the first-line
    recovery"; `playbook-escalate` "not the first recovery action"; `false-positive`
    guard). For **parity** the new corpora include the analogous guard —
    supply_chain: `reroute`/`expedite` is NOT the cold-chain-excursion response;
    aquaculture: non-oxygen interventions (e.g. feeding) do not address a DO crash.
    This mirrors energy's structure (it is *not* over-help — it does not name the
    answer); **omitting it would be the asymmetry that handicaps the new verticals
    relative to energy.** *Disclose* the judgment in the REPORT; *alternative for
    Cray:* a stricter naive baseline that omits all disambiguation snippets
    (handicaps the new verticals vs the energy pass — not recommended).

**Inherited disclosure caveat (NOT an OQ-1 change; surfaced for external-grade
honesty).** Per D-1, arm (c) is graded via `_reduced_expected`, which declares
ONLY `affected_primary_key` + `action_keywords` — it **omits** the `forbidden_*`
precision checks (verified in `rag_arm._reduced_expected` + `grade_proposal`). So
arm (c)'s entity check passes when the right entity is *present among those named*
and is **not** penalised for over-naming a safe decoy — whereas arm (a)'s reused β
headline **was** graded with `forbidden_primary_keys`/`forbidden_keywords`
precision. The arm(a)≈arm(c) parity is therefore on the D-1 common sub-task
(entity-present + action-class), **not** on the full hardened precision key. This
is an **inherited D-1 definition — do NOT re-open it here**; it is flagged so the
REPORT discloses it for external-grade defensibility (a skeptic comparing the two
numbers must know arm (c) was graded on the looser entity criterion). Material for
aquaculture especially, whose hard items carry the most tempting watch-band decoys.

## 4. Acceptance Criteria

- [ ] **AC-1 RAG-fairness re-look + methodology delta ratified.** OQ-1 (the
  external-grade RAG-fairness re-look) — **run by Cowork (§3.5)** — and its outcome
  (R-OQ1-1..4: corpus richness / retriever caveat / template-neutrality fix /
  per-vertical over+under coverage, all within the corpus+prompt levers, D-6
  intact) is folded into the two corpora + the three parameterizations; the
  resulting methodology **delta** is Cray-ratified **before** any scored run
  (inherited B-6 anti-moving-target).
- [ ] **AC-2 Arm (b) green per vertical, NO new arm code.** Arm (b) runs over the
  aquaculture + supply_chain breach subsets **reusing the existing
  `text_to_sql_arm`** (confirm: no vertical-specific code added beyond the shared
  OQ-4 `questions.py` parameterizations), with per-vertical **mock-`ChatClient`
  unit tests** asserting a correct SELECT scores entity-ID PASS, a non-SELECT is
  refused, and "action-class structurally N/A" is recorded — including
  aquaculture's **below-floor** direction (`WHERE measured_value <= threshold`).
- [ ] **AC-3 Arm (c) corpus authored + green per vertical, joint binding HELD
  (over + under).** `corpus/aquaculture_v0.yaml` + `corpus/supply_chain_v0.yaml`
  authored to the energy pattern (structural parity; one consolidated breach-action
  snippet per vertical — §3.5 A); per-vertical **mock-`ChatClient` unit tests**
  assert (a) the retriever is deterministic; (b) **under-cover** — every breach
  item's `action_keywords` lemma is covered by ≥1 snippet AND surfaces under the
  k=4 retriever (the same assertion shape as the energy
  `test_procedure_comparison_rag.py::test_joint_binding_*` /
  `test_retriever_surfaces_an_action_snippet_*`, with the per-vertical lemma sets);
  (c) **over-cover** — no snippet contains a dataset entity-key literal (`pond-A`/
  `ship-S`); (d) grading reuses `grade_proposal`'s fields; (e) the D-6 guard holds
  (no `services.engine.procedures` import; exactly one LLM call per item).
- [ ] **AC-4 Harness parameterized, NOT forked (OQ-4 — THREE parameterizations).**
  The RAG persona string + the unit map + **the threshold-noun (ceiling/floor by
  direction)** are parameterized so the harness drives all three verticals from
  `--dataset` + `--corpus` with no per-vertical branching in arm logic; **the
  energy run is unchanged — regression: the existing energy offline tests still
  pass verbatim, and the rendered energy questions are byte-identical** (energy is
  `direction=above`, so the threshold-noun stays "ceiling").
- [ ] **AC-5 Offline gate green (the cheapest gate — BEFORE any live run).** The
  full **mock** smoke (arms b + c on both new breach subsets with a deterministic
  mock `ChatClient`) runs end-to-end green; `ruff check` clean; `mypy --strict`
  clean on new/changed code; `pytest` unit suite green (read the `N passed`
  summary line, not `$?`). Energy regression green.
- [ ] **AC-6 ONE scored host-state run per vertical (or one combined).** After
  Cray go (CLAUDE.md §8): the scored run(s) on MS-S1 (`gpt-oss:20b`, ADR-001 pin —
  **NOT qwen3.x**), **warm-first**, via `run_detached.sh`, capturing `--dump-json`.
  Arm (a) is **NOT re-run** (REPORT numbers reused, D-2). Minimise live runs
  (OQ-5: two separate runs vs one combined sweep — Cray's call).
- [ ] **AC-7 Verify + REPORT B-3 extension committed.** Every per-arm/per-item
  score VERIFIED from `--dump-json` with the **Read tool** (the session-46
  confirm-don't-infer / Auto-Memory false-negative caveat); the REPORT `## B-3`
  section extended with per-vertical comparison tables (entity-ID / action-class /
  entity+action / latency / failure-mode) + the inherited §3.4 narrative header +
  forward-pointer + reports-not-gates ring-fence + **the OQ-1 disclosures** (the
  retriever near-oracle caveat §3.5 B; the per-vertical corpus size / retrieved
  fraction §3.5 A; the parity-disambiguation judgment §3.5 D; the inherited D-1
  `_reduced_expected` looser-entity-grade caveat §3.5); landed via a dedicated
  `test/*` PR (review-separation, inherited from PLAN-0019).

## 5. Out of Scope (defer)

- ❌ **Building the future verify+reshape procedure-engine enhancement** — the
  §3.4 forward-pointer; a **separate** future PLAN/ADR (ADR-016 area). This
  extension is **measurement-only**, exactly like the energy pass. *(Explicit per
  dispatch: verify+reshape governance enhancement is OUT.)*
- ❌ **Re-running arm (a)** for any vertical — REPORT numbers are reused (D-2);
  per-vertical arm-(a) β headlines already exist (§2).
- ❌ **A vector store / embeddings for arm (c)** — D-4 inherited: deterministic
  lexical top-k only. (OQ-1b keeps it; produces a REPORT caveat, not a swap.)
- ❌ **Any verify / semantic-consistency / output-reshape / governance / ontology
  layer on arm (c)** — D-6 contamination guard (BINDING, inherited). Note: OQ-1's
  fairness re-look stays **within the corpus + prompt levers** — it does NOT
  license adding any such layer.
- ❌ **Changing the D-1 common sub-task / arm (c)'s `_reduced_expected`** — the
  looser-entity-grade asymmetry (§3.5 disclosure caveat) is **inherited and
  disclosed, not fixed** here.
- ❌ **Re-authoring / re-sizing the breach datasets** — the existing 40-item breach
  subsets are reused as-is (§2).
- ❌ **watch / ok subsets** — breach-only (inherited SD-3; matches arm (a)'s β
  headline and keeps the three verticals commensurable).
- ❌ **A vet_clinic arm** — parked (ADR-005); this extension is the two active
  non-energy verticals only.
- ❌ **Re-opening any PLAN-0027 D-1..D-6 / SD-1..SD-4 / the joint binding, or
  ADR-016's primitive shape** — B-6 ring-fence inherited.
- ❌ **Moving any pre-registered bar** — reports-not-gates inherited.

## 6. Steps

1. **Step 1 — OQ-1 re-look (DONE) + §8 adjudication + methodology-delta
   pre-registration → Cray ratify.** The external-grade RAG-fairness re-look is
   **complete** (Cowork, §3.5 — R-OQ1-1..4). Cray adjudicates §8 (OQ-1 outcome +
   OQ-2/3/4/5) and ratifies the methodology delta (the two corpora + the three
   parameterizations incl. the template-neutrality fix) **before any scored run**
   (inherited B-6). *(AC-1.)*
2. **Step 2 — Build offline (corpora + parameterization + tests).** Author
   `corpus/aquaculture_v0.yaml` + `corpus/supply_chain_v0.yaml` honouring the joint
   SD-1↔SD-2 binding (over + under) per vertical (§3.2 + §3.5). Parameterize the
   THREE harness touch-points (RAG persona · unit map · threshold-noun ceiling/floor)
   without forking arm logic. Add per-vertical offline tests mirroring the existing
   energy `tests/benchmark/test_procedure_comparison_*`. Enforce the D-6 guard.
   *(AC-2, AC-3, AC-4.)* Lands via `feat/*` or `test/*` PR(s).
3. **Step 3 — Offline gate (cheapest gate, MUST be green first).** Full mock smoke
   (arms b + c, both new breach subsets, deterministic mock client) green; ruff /
   mypy --strict / pytest clean from their own summary lines; **energy regression
   green (byte-identical energy questions + the energy offline suite verbatim).**
   **No live run before this is green.** *(AC-5.)*
4. **Step 4 — Pin per-vertical run plan + Cray host-state go.** Decide one combined
   sweep vs one run per vertical (OQ-5); confirm warm-first recipe + the
   `--dataset`/`--corpus` invocation per vertical; get the explicit Cray go per
   CLAUDE.md §8.
5. **Step 5 — ONE scored host-state run (per OQ-5).** MS-S1 `gpt-oss:20b`,
   warm-first, `run_detached.sh`, `--dump-json`. Arm (a) not re-run. *(AC-6.)*
6. **Step 6 — Verify + REPORT extension + land.** VERIFY every score from
   `--dump-json` with the **Read tool**; extend the REPORT `## B-3` section with
   the two per-vertical tables + the inherited narrative header + forward-pointer +
   ring-fence + the OQ-1 disclosures (AC-7); land via a dedicated `test/*` PR
   (review-separation). *(AC-7.)*

> **HARD GATE (inherited from PLAN-0019/0027).** No scored host-state run (Step 5)
> before the offline mock gate (Step 3) is green AND the methodology delta (Step 1,
> incl. the OQ-1 re-look outcome) is Cray-ratified. The reports-not-gates ring-fence
> holds throughout.

## 7. Verification

"Done" = all §4 ACs green via Lesson #7 §3 reliable methods: the offline mock smoke
+ ruff/mypy/pytest green from their own summary lines + energy regression green
(Step 3); the OQ-1 re-look + methodology delta Cray-ratified before the run (Step
1); ONE Cray-approved scored run per OQ-5 (Step 5); every reported number VERIFIED
from `--dump-json` via the Read tool (Step 6); the REPORT `## B-3` per-vertical
extension committed via a `test/*` PR. Per ADR-009 D2, **Code** runs verification +
commits; the drafter / Cowork hold no execution or commit authority.

## 8. Open Questions (for Cray — OQ-1 re-look DONE by Cowork; do NOT silently resolve)

> **OQ-1 is COMPLETE — Cowork ran the external-grade RAG-fairness re-look (§3.5).**
> What remains for OQ-1 is **Cray ratification** of its four recommendations as the
> pre-registered methodology delta (AC-1, B-6). OQ-2/3/4/5 remain Cray decisions.

- **OQ-1 — Is the lean-RAG arm (c) calibrated fairly enough to stand as an
  external-grade baseline? → RE-LOOK DONE (Cowork); Cray RATIFIES.** Outcome
  (full reasoning in the session-65 Cowork completion handoff; pre-registered in
  §3.5):
    - **(a) Corpus richness → R-OQ1-1:** ~10 snippets/vertical, structural parity
      as the invariant (not an identical count), one consolidated breach-action
      snippet per vertical (robust under k=4); disclose size + retrieved fraction.
    - **(b) Retriever → R-OQ1-2:** keep the locked lexical top-k (don't re-open
      D-4); add the REPORT near-oracle caveat; the binding makes retrieval generous
      to arm (c), so a parity finding is conservative for the thesis.
    - **(c) Template neutrality → R-OQ1-3 (REQUIRED fix):** parameterize the
      threshold-noun ceiling/floor by direction (a third OQ-4 parameterization, a
      fairness fix for aquaculture's below-floor question); energy/supply
      byte-identical. Optional polish: de-underscore `reading_parameter`.
    - **(d) Coverage → R-OQ1-4:** two-sided binding (under-cover lemmas + over-cover
      guard, no entity-key literal in snippets) + a parity disambiguation snippet
      for the dangerous near-miss (supply_chain reroute/expedite; aquaculture feed).
  *Why still a Cray ratification:* fairness calibration for an external-grade
  baseline carries reputational stakes; Cowork authored both the re-look and this
  materialization, so the independent-deliberation check falls to Cray (ADR-012
  D4.3). *Each recommendation lists its alternative in §3.5 for an informed call.*

- **OQ-2 — Does the moat-relocation thesis need to *replicate* across all three
  verticals to hold, or is one supporting vertical enough? (Cray — framing.)**
  *Recommendation:* treat each vertical's arm(a)≈arm(c) result as **independent
  evidence**; report all three honestly whether or not they agree, and let the
  *pattern* (does the tie replicate?) be the finding — reports-not-gates means a
  vertical where arm (c) *loses* to arm (a) is just as publishable as one where it
  ties. *Alternatives:* pre-declare a "thesis holds iff ≥2/3 verticals tie" rule
  (risks moving-target if a vertical surprises). *Why a Cray decision:* it sets how
  the cross-vertical result is *interpreted* externally — a framing choice that
  should be pinned before the run (B-6) so the read is not tuned post-hoc.

- **OQ-3 — Which arm-(a) figure does the aquaculture join read against? (Cray.)**
  aquaculture arm (a) is a **range**: 60% (hardened, 2026-06-09) → 100% (nudged,
  2026-06-11). *Recommendation:* read against the **nudged 100%** (the shipped
  prompt's behaviour, matching how the energy join cited 97.5–100%) but **state
  the range + the nudge dependency** in the table, exactly as the energy join did.
  *Alternatives:* read against the hardened 60% (most conservative for the thesis —
  arm (c) would then *beat* arm (a) on aquaculture, a stronger moat-relocation
  signal but a less flattering arm-(a) number). *OQ-1 interaction:* the
  template-neutrality fix (R-OQ1-3) lifts arms b+c on aquaculture, not arm (a)
  (reused) — so a fair below-floor question makes any arm(c)-beats-arm(a) read on
  the 60% basis cleaner, not an artifact. *Why a Cray decision:* which arm-(a)
  baseline the comparison reads against is a pre-registration choice that shapes
  the cross-vertical read (B-6).

- **OQ-4 — Confirm the THREE mechanical harness parameterizations are in-scope
  (NOT "new harness code" that breaks the dispatch's premise). (Cray — sanity.)**
  The RAG persona string + the unit map + **the threshold-noun ceiling/floor**
  (§2(1) / §3.5 C) are small parameterizations, not new arms or new grading logic.
  *(The dispatch named two; the OQ-1 re-look surfaced the third — the threshold-noun
  — as a template-neutrality fairness fix.)* *Recommendation:* treat all three as
  **in-scope build touch-ups** under "extend the arms," with the existing energy
  tests + byte-identical energy questions as the regression guard (AC-4). *Why
  surfaced:* the dispatch's premise was "new corpus, not new harness code"; this
  confirms the premise holds to ~90% and names the three exceptions explicitly
  rather than letting them slip in silently.

- **OQ-5 — One combined sweep vs one scored run per vertical? (Cray — host-state.)**
  *Recommendation:* **one combined sweep** (both verticals' breach subsets in a
  single warm MS-S1 window) to minimise live runs per CLAUDE.md §8, unless OQ-1's
  re-look lands the two corpora at different times (then run each as it is ratified).
  *Alternatives:* two separate runs (cleaner per-vertical provenance; two warm
  cycles). *Why a Cray decision:* it is a host-state run-count choice (CLAUDE.md §8
  — minimise live runs; Cray gates the go).

## 9. References

### Extends
- `docs/plans/0027-bgamma-comparison-baselines.md` — the energy pre-registration
  (D-1..D-6, SD-1..SD-4, the joint SD-1↔SD-2 binding, the D-6 contamination guard,
  the §3.4 forward-pointer, reports-not-gates) — **inherited verbatim**.
- `docs/plans/0019-core-procedure-baseline.md` — B-γ / AC B-3 (the parent step);
  Part B B-6 ring-fence + review-separation.

### Reused surfaces (the scope-shrinking facts — re-verified live by Cowork, session 65)
- `benchmarks/procedure_comparison/run_comparison.py` — already `--dataset` /
  `--corpus` parameterized (lines 125–126); threads `dataset.reading_parameter`
  generically (lines 100–101).
- `benchmarks/procedure_comparison/comparison.py` — `breach_items`, `run_arm_b`,
  `run_arm_c`, the summaries, `comparison_records` (vertical-agnostic).
- `benchmarks/procedure_comparison/text_to_sql_arm.py` — `build_scenario_db`
  (synthesises the DB from the `Scenario` — NO vertical `synthetic.py` binding),
  `run_item_b` (vertical-agnostic as built).
- `benchmarks/procedure_comparison/rag_arm.py` — `load_corpus`, `retrieve`
  (deterministic lexical top-k, `DEFAULT_TOP_K = 4`), `run_item_c`,
  `_reduced_expected` (arm (c) drops `forbidden_*` — the §3.5 disclosure caveat);
  **`build_rag_messages` hardcodes the "energy operations assistant" persona, line
  128** (OQ-4(i) parameterization target).
- `benchmarks/procedure_comparison/questions.py` — `render_sql_question` /
  `render_rag_question` (generic over scenario fields); **`_UNIT_PHRASE` maps only
  `{celsius, hz}`, line 28** (OQ-4(ii) — aquaculture `mg/L` falls through); **the
  threshold-noun "ceiling" is hardcoded in both renderers (lines 54, 71–72) despite
  the `_edge(direction)` preposition flip** (OQ-4(iii) / R-OQ1-3 — the
  template-neutrality fix).
- `benchmarks/procedure_comparison/corpus/energy_v0.yaml` — the 10-snippet corpus
  pattern to replicate per vertical (threshold rule + entity + per-action playbook
  + watch + false-positive snippets; the joint-binding header comment; the
  `playbook-restart` consolidated-action precedent for R-OQ1-1).
- `benchmarks/procedure_baseline/dataset/aquaculture.yaml`,
  `benchmarks/procedure_baseline/dataset/supply_chain.yaml` — the existing 40-item
  breach subsets (28 boundary + 12 hard `*-h01..h12`); reused as-is. Lemma sets
  verified: aquaculture `[aerat, oxygenat]`; supply_chain `[hold, inspect,
  quarantine, divert]` (hard items drop `divert`).
- `benchmarks/procedure_baseline/grader.py` — `grade_proposal` (scores only the
  declared `Expected` fields; `affected_primary_key` passes on "present among
  named"), `normalize_primary_key` — the basis of the §3.5 inherited-asymmetry
  disclosure.
- `benchmarks/procedure_baseline/schema.py` — `Scenario` / `Expected` /
  `SiblingReading` (`direction` ∈ {below, above}; the `forbidden_*` precision
  fields arm (c)'s `_reduced_expected` omits).
- `benchmarks/procedure_baseline/REPORT.md` — arm (a) per-vertical β headlines
  (HARDENED 2026-06-09: aqua 60% / energy 97.5% / supply 100%; PLAN-0020 R1 nudged
  2026-06-11: 100% / 100% / 100%) — the D-2 reuse source; the `## B-3` energy
  comparison result (arm (c) 97.5% ties arm (a)) this extension generalises.
- `tests/benchmark/test_procedure_comparison_{rag,text_to_sql,harness}.py` — the
  offline test pattern to mirror per vertical (esp. `test_joint_binding_every_breach_action_lemma_is_covered`
  + `test_retriever_surfaces_an_action_snippet_for_a_breach_question` +
  `test_d6_arm_c_imports_no_procedure_engine_symbol` — the AC-3 assertion shapes).
- `verticals/aquaculture/ontology/aquaculture_v0.yaml` — `RecommendedAction.action_type
  ∈ {start_emergency_aerator, dispatch_technician, increase_water_exchange, escalate}`
  (verified).
- `verticals/supply_chain/ontology/supply_chain_v0.yaml` — `RecommendedAction.action_type
  ∈ {reroute, expedite, hold, inspect, escalate}` (verified).
- `.claude/skills/ms-s1-ollama/run_detached.sh` — the carrier-proof host-state
  launcher (sentinel + `DUMP: wrote N` completion truth).

### Governance
- `CLAUDE.md` §8 (host-state ASK-Cray; minimise live runs; ADRs merged before
  implementation; AI assistive), §6 (Plan Flow), §7 (PR-only to main).
- ADR-009 D1 (interim authoring), D2 (only Code commits); ADR-013 (autonomy-axis
  relocation, phased); ADR-012 D4.3 (author≠reviewer disclosure — see the
  provenance note re: Cowork's OQ-1 self-deliberation); ADR-016 (the verify+reshape
  forward-pointer is an ADR-016-area future PLAN, OUT OF SCOPE); ADR-001
  (`gpt-oss:20b` pin — NOT qwen3.x).

---

*PLAN-0028 — Draft body authored by the `plan-drafter` subagent 2026-06-16;
materialized + OQ-1 external-grade RAG-fairness re-look folded in by Cowork
(session 65, 2026-06-17). Extends PLAN-0027's executed energy three-arm comparison
(B-3 REPORT) to aquaculture + supply_chain, inheriting all of PLAN-0027's locked
decisions + the joint SD-1↔SD-2 fairness binding verbatim. OQ-1 re-look outcome
(R-OQ1-1..4, all within corpus+prompt levers — D-6 intact) pre-registered in §3.5,
pending Cray ratification (AC-1). The arm-(a) baseline question is RESOLVED
(per-vertical β headlines already in the REPORT — no arm-a re-run). Cowork
materializes + Code commits per ADR-009 D2. Reports-not-gates ring-fence inherited.*

*AI-assisted per project convention.*
