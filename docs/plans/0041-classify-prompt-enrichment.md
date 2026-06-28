# PLAN-0041: Classify-prompt enrichment — lift the live AT-1-family match-rate without touching the moat guard

**Status:** Ready for execution
**Owner:** Claude Code (executes); Cowork drafted (ADR-009 D1); Cray ratifies
**Created:** 2026-06-27
**Related ADRs:** ADR-0024 (procedure generator — **D4** `gate_kind` cross-check / **D7** AT-1-family-only + abstain, the moat this PLAN must not move; **D12** tests-are-the-offline-oracle), ADR-0021 (classify-don't-synthesize), ADR-0019 / ADR-010 IN-3 (determinism invariant — confidence never routes)

> **No new ADR.** The moat guard (`_archetype_disagreement` + `_AT2_ONLY_KINDS`)
> is **untouched** — this is a prompt-only lever, so it is PLAN-only. If execution
> surfaces a reason the guard *must* change to hit the metric, **STOP and surface
> it** (that flips to an ADR-gated decision); do not bake a guard relaxation into
> this PLAN.

> **Provenance / author≠reviewer (ADR-012 D4.3).** Originator = the PLAN-0040 AC-B5
> live finding (session 83 closeout) + the s83-recorded STATUS Active TODO. Trigger
> = a Stop-hook "proceed" (the harness) relayed by Code as a draft dispatch
> (`.claude/handoffs/session-84/2026-06-27-1316-code-cowork-plan0041-classify-enrichment-dispatch.md`)
> — **NOT** a Cray ratification; Cray's veto/redirect is open. Drafter = Cowork.
> The §"Open Questions" recommendations were deliberated by **two Code-run
> specialist reviewers** (an LLM-prompt/classification designer + an adversarial
> moat-safety reviewer), independent of the drafter — so the independent-deliberation
> check is exercised; Cray ratification + Code R2-review remain the closing checks.

---

## Goal

Lift the **live classify match-rate** for textbook AT-1-family narratives by
**enriching the classify prompt only**. Today `build_classify_messages` sends a
**title-only catalog** (`- AT-1: anomaly→action`) and states only the *negative*
rule ("NEVER emit `scored_rule`/`rule_gate`/`doa_tier` … abstain instead"). On a
textbook AT-1/AT-3 narrative the live `gpt-oss:20b` is conservative — it mis-tags
the judge step with an AT-2-only `gate_kind`, which the deterministic cross-check
`_archetype_disagreement` **correctly** abstains on (~1-in-3 false-abstain on a
narrative that *should* match). The guard is doing its job; the **prompt** under-
specifies what a band judge is.

The lever gives the model two things it lacks: (a) **per-archetype descriptions**
derived from the canonical catalog (not just the bare title), and (b) a **positive
band-vs-out-of-scope-gate explainer** that teaches the *band case* a band judge
should emit (`in_file_band` / `env_band`), so the model stops reaching for an
AT-2-only kind. The deterministic abstain-gate is **byte-identical**: the prompt
makes the model's *input* to the guard correct more often; it never weakens the
guard.

Acceptance = a **measured lift** on a labelled narrative set **with zero
regression in AT-2-class abstain behaviour** (the moat-safety twin metric), proven
by an offline structural test pair (the gate) plus a Cray-gated before/after live
run on MS-S1 (confirming evidence, not the gate).

The thesis is preserved: classify stays **best-effort convenience**; the
**manual-pick → `/procedures/draft/instantiate`** path remains the DETERMINISTIC
happy path (ADR-0024 D9). This lever makes the convenience path hit more often —
it does **not** make classify load-bearing.

## LOCKED (render faithfully — do NOT re-litigate)

1. **The AT-2 cross-check is UNTOUCHED** (ADR-0024 D4/D7; rendered "LOCKED-7" in
   PLAN-0040). `_archetype_disagreement`, `_gate_class`, `_AT2_ONLY_KINDS =
   frozenset({SCORED_RULE, RULE_GATE, DOA_TIER})`, and `_BAND_KINDS = (ENV_BAND,
   IN_FILE_BAND)` (`services/engine/procedures/generator/pipeline.py:78-79,
   153-182`) stay **byte-identical**. Any AT-2-only kind on any step still hard-
   abstains; a band-class mismatch on a template-named step still abstains.
   Relaxing the guard to lift the hit-rate is OUT — it needs data + a new ADR.
2. **classify-don't-synthesize holds** (ADR-0021). The model still SELECTS from
   the closed `ARCHETYPE_CHOICES` enum (AT-1 family + `abstain`); the enriched
   prompt may not invite it to invent an archetype or a gate_kind. AT-2 is absent
   by construction → an AT-2-class narrative still routes to `abstain`, never a
   down-classified AT-3.
3. **`confidence` NEVER routes** (ADR-010 IN-3 / determinism invariant). The route
   stays a deterministic function of the closed-enum LABEL + the per-step cross-
   check. The enriched prompt may ask for a rationale/confidence (advisory);
   PLAN-0041 introduces **no** confidence threshold.
4. **Governance bar + untrusted-block containment preserved** (ADR-0024 D3 / IN-2).
   The narrative stays inside the labelled untrusted block; `_GOVERNANCE_BAR` +
   `_SECURITY` stay in the trusted system instruction. New catalog prose is
   **trusted internal config** (it describes archetypes, names no operator data)
   so it may live in the system instruction — but it carries **no governance
   values** itself (no numbers / thresholds / handlers / env-var names).
5. **The canonical archetype catalog wins** (CLAUDE.md §4). Any per-archetype
   description is **DERIVED** from `docs/conventions/procedure-archetypes.md`
   (canonical) — never a third hand-authored copy free to drift. (Seam = OQ-A.)
6. **No host-state in the offline gate.** The classify-prompt change is exercised
   offline by **structural** tests (the prompt contains the descriptions + the
   band explainer; the guard module is unchanged). The **hit-rate lift is
   inherently LIVE** → that measurement is **evidence behind a Cray host-state go**
   (CLAUDE.md §8), not the offline gate (split = OQ-D).

## Acceptance Criteria

**Offline gate (the verdict — zero host-state; merges on green):**

- [ ] **AC-1 — guard byte-identical (the moat invariant).** A new introspection
  test asserts `pipeline._AT2_ONLY_KINDS == frozenset({GateKind.SCORED_RULE,
  GateKind.RULE_GATE, GateKind.DOA_TIER})` and `pipeline._BAND_KINDS ==
  (GateKind.ENV_BAND, GateKind.IN_FILE_BAND)`, and that `ARCHETYPE_CHOICES` still
  excludes `"AT-2"`. (This invariant does **not** exist today — verified — and is
  the cheapest backstop; the analog of ADR-0024 D12-layer-1 disjointness.)
- [ ] **AC-2 — guard still abstains on every AT-2-only kind.** Generalize the
  existing single-kind test (`test_at2_only_gate_disagreement_abstains`,
  `tests/services/engine/procedures/test_generator_pipeline.py:298`) so that
  `scored_rule`, `rule_gate`, **and** `doa_tier` on the judge step each still
  return `Abstained(reason="archetype_disagreement")`.
- [ ] **AC-3 — enriched prompt asserted by introspection.** `build_classify_messages`
  output (a) **still contains** the AT-2 prohibition clause ("NEVER emit
  'scored_rule', 'rule_gate', or 'doa_tier'" + "abstain instead") and the
  "scoring / rule / approval-tier (DOA) shape … OUT OF SCOPE … abstain, never
  force-fit" clause; (b) **now contains** each per-archetype description and the
  positive band-vs-out-of-scope explainer; (c) **still contains** `_GOVERNANCE_BAR`
  + `_SECURITY`.
- [ ] **AC-4 — descriptions carry no AT-2 vocabulary (R3 guard).** The new
  per-archetype description strings contain **none** of `scored_rule` /
  `rule_gate` / `doa_tier` (so the enrichment cannot teach the model to *emit* an
  AT-2-only kind on a true AT-1/AT-3 step — a self-defeating new false-abstain).
- [ ] **AC-5 — schema + guard untouched at the type level.** `classification_schema()`
  still pins `archetype_id` to `list(ARCHETYPE_CHOICES)`; no diff to `schemas.py`'s
  `Classification` / `StepGate`, and no diff to the guard functions in `pipeline.py`.
- [ ] **AC-6 — full suite green.** `ruff` + `ruff-format` + `mypy --strict
  services/` clean; `pytest` green (the existing 1801-pass baseline + the new
  tests).

**Live evidence (confirming, NOT the gate — behind an explicit Cray host-state go):**

- [ ] **AC-7 — twin metric on the labelled fixture set (OQ-C).** On the
  `before` (current) vs `after` (enriched) prompt, same model / seed / temperature:
  - **Arm A (lift):** AT-1 + AT-3 textbook match-rate **strictly improves**
    `after > before` on the same fixtures, meeting the pre-committed target
    (recommend **AT-1+AT-3 ≥ 9/11 after**, vs the live-observed ~7/11 before).
    AT-1b fixtures are **measured and reported but NOT gated** (see OQ-E + the
    scope note).
  - **Arm B (zero-regression — HARD gate):** **11/11** genuine AT-2-class
    narratives still `Abstained`. One false-accept fails the whole PLAN regardless
    of lift.
  - Run **N ≥ 3 live repetitions**; report the **worst** run, not the best;
    record, per fixture, **which** guard path abstained (label-abstain vs per-step-
    disagreement) so a silent label→backstop shift is visible.

## Out of Scope

- ❌ **Any change to `_archetype_disagreement` / `_AT2_ONLY_KINDS` / `_BAND_KINDS`
  / the abstain-gate** (ADR-0024 D4/D7 — needs data + an ADR).
- ❌ Introducing a **confidence threshold** in the route (ADR-010 IN-3).
- ❌ **AT-2 generation** of any kind.
- ❌ Making classify the **load-bearing** path (manual-pick stays the deterministic
  happy path, D9).
- ❌ Touching **`build_prose_messages`** — prose step-id divergence is already
  handled by the s83 positional fallback (#459); OQ-E recommends classify-only.
- ❌ Generating the **`goal`** field (never generated; PLAN-0040 OQ-B B2).
- ❌ **Gating** on an AT-1b lift — AT-1b's residual false-abstain is a per-step-
  *guard* property (its extra action slots trip the cross-check live), not a
  prompt property, so a prompt-only lever cannot own it (scope note below).

## Open Questions (options + recommendation; Cray adjudicates — do not silently resolve)

### OQ-A — where the per-archetype description lives (the derivation seam)

| Option | Verdict |
|---|---|
| **(a) add an optional `description` field to `ArchetypeTemplate`**, populated from the canonical catalog prose; `build_classify_messages` reads `(archetype_id, title, description)` from the one registry | **RECOMMENDED** |
| (b) a description map hardcoded in `prompts.py` | reject — a *third* hand-authored copy free to drift (LOCKED-5 violation) |
| (c) parse the canonical `.md` at runtime | reject — a parser + brittle runtime dependency on doc formatting, for three one-liners |

**Recommendation: (a).** The registry already *is* the derived machine form of the
catalog (`template.py` docstring says so); adding `description` keeps the
catalog→template a single derived seam, no parser, no third copy. Concrete shape:

- `template.py` — add to `ArchetypeTemplate` (after `title`): `description: str =
  Field(default="", …)`; populate `AT1` / `AT1B` / `AT3`. `default=""` keeps every
  existing bare-template construction back-compatible.
- `pipeline.py:197` — `catalog = [(t.archetype_id, t.title, t.description) for t in
  REGISTRY.values()]`.
- `prompts.py` — signature `catalog: list[tuple[str, str, str]]`; render
  `f"- {aid}: {title} — {desc}"` (fall back to `f"- {aid}: {title}"` when `desc`
  is empty). Update any test that builds a 2-tuple catalog → 3-tuple.

### OQ-B — the band-vs-out-of-scope-gate explainer wording (the load-bearing content)

This is what actually moves the metric. The system prompt **already** carries the
*prohibition*; the fix is teaching the **positive band case**. **Recommended prose**
(value-free, additive — inserted after the existing prohibition sentence, before
`_GOVERNANCE_BAR`):

> A catalogued (AT-1-family) judge compares ONE signal against a SINGLE
> deterministic band — a threshold or a reorder point — so its gate_kind is a band
> kind: 'in_file_band' when the band is authored in the procedure, 'env_band' when
> it comes from a deployment binding. A step that weighs SEVERAL criteria, computes
> a weighted or ranked score, or routes by an approval/authority tier (DOA) is a
> different, OUT-OF-SCOPE shape — abstain for the whole narrative rather than tag
> such a step with a band kind. When unsure whether a judge is a single band or a
> multi-criteria gate, abstain.

The trailing "When unsure … abstain" is **load-bearing for moat safety** (it
restores abstain as the default under ambiguity — R2 mitigation). The exact final
string is finalized at execution under Code R2; this is the recommended content.

**Recommended per-archetype descriptions** (derived from the canonical catalog
§§AT-1/AT-1b/AT-3, value-free, one line each — each names the *single-band* nature
so the description reinforces OQ-B):

- **AT-1:** read a signal, judge it against one deterministic band, then act on the
  breach set after a human go/no-go
- **AT-1b:** the AT-1 loop plus a second band-routed branch for the borderline
  watch set and an automatic summary receipt
- **AT-3:** read stock levels, judge them against a single reorder-point band, then
  reorder the low set after one human approval

### OQ-C — the false-accept guardrail + acceptance metric (THE crux — moat safety)

The lift must **not** come by making the model now *accept* AT-2-class narratives
(the opposite failure). The acceptance is a **twin metric on one labelled fixture
set, measured in one run** (see AC-7). Recommended fixture set (~26 narratives;
source the AT-2 prose from the catalog's own governance-signature language + the
live `procurement.emergency_sourcing_round`, so they are *genuine* AT-2, not
strawmen):

| Arm | Class | N | Must produce |
|---|---|---|---|
| **A (lift)** | AT-1 textbook | 6 | `ProposedMatch` AT-1 |
| | AT-3 textbook | 5 | `ProposedMatch` AT-3 |
| | AT-1b textbook | 4 | measured + reported, **not gated** (OQ-E) |
| **B (zero-regression, HARD)** | AT-2 weighted-score sourcing | 3 | `Abstained` |
| | AT-2 per-criterion compliance | 3 | `Abstained` |
| | AT-2 tiered-DOA approval | 3 | `Abstained` |
| | AT-2 full hero (7-step) | 2 | `Abstained` |

Include **≥ 2 *borderline* AT-2** (an AT-1-looking anomaly→action that hides a
per-criterion compliance gate or a DOA tier mid-flow) — the realistic down-
classification trap, not a caricature.

**Pre-committed pass/fail read (fix BEFORE any live run):**

```
PASS  iff  (Arm B: 11/11 AT-2-class fixtures ABSTAIN — HARD, zero regression)
      AND  (Arm A: AT-1+AT-3 match-rate strictly improves vs the recorded
            before-prompt baseline, AT-1+AT-3 ≥ 9/11 after)
```

**Honest confidence flag (no silent cap):** the fixture set is **small (~26) and
hand-authored**, and classify is **non-deterministic live**. A single live 11/11
abstain is weak evidence of a *rate*, not proof — hence N ≥ 3 reps, report the
worst, and report Arm A as "X/11 → Y/11 on this fixture set", never as a population
rate.

### OQ-D — offline gate vs live evidence split (the gate vs the proof)

- **Offline GATE (mergeable bar, zero host-state):** AC-1..AC-6 — the guard byte-
  identity + AT-2-abstain behavioural test + the enriched-prompt introspection +
  the descriptions-no-AT2-vocab lint + schema-unchanged + full suite green. Runs
  on the `RecordedChatClient` seam; **no MS-S1 call**. Offline-green is what makes
  the diff mergeable.
- **LIVE EVIDENCE (confirming, not the gate):** AC-7 — the before/after Arm-A
  hit-rate + the Arm-B 11/11 abstain on MS-S1 `gpt-oss:20b` (`192.168.1.133:11434`),
  warmed via the `ms-s1-ollama` skill, **behind an explicit Cray host-state go**
  (CLAUDE.md §8). A red live result blocks the *value claim* (don't merge claiming
  a lift you can't show) but the offline tests are the gate; the live run cannot
  substitute for them. **Recommendation: accept this split** (mirrors PLAN-0040
  OQ-D/OQ-E).

### OQ-E — does the prose call need the same treatment?

**Recommendation: classify-only.** The live finding is on **classify** (S1). The
**prose** call (S5) already tolerates renamed step_ids via the s83 positional
fallback (#459). Keep PLAN-0041 tight; `build_prose_messages` is out of scope.

**Scope note (AT-1b, from the adversarial review):** STATUS records that AT-1b
"reaches the gate only via manual-pick" — its multi-step shape (the extra
`escalate_watch` + `summary` action slots) trips the **per-step cross-check** live,
which is *downstream of the prompt and byte-identical*. A prompt-only lever can
lift AT-1b's *label* match but cannot reach the per-step failure mode AT-1b
actually hits. So AT-1b is **measured + reported but not gated**; any real AT-1b
fix is a **guard change** (re-opens ADR-0024 D4/D7) — explicitly NOT this PLAN.

## Steps

### Step 1 — extend the derivation seam (OQ-A)

Add `description: str = Field(default="", …)` to `ArchetypeTemplate`
(`services/engine/procedures/archetypes/template.py`); populate `AT1` / `AT1B` /
`AT3` with the OQ-B descriptions (derived from the canonical catalog). Widen the
catalog tuple in `classify_narrative` (`pipeline.py:197`) to
`(archetype_id, title, description)`. Inert plumbing — no new logic, no governance
value.

### Step 2 — enrich `build_classify_messages` (OQ-B)

Change the signature to `catalog: list[tuple[str, str, str]]`; render the catalog
line with the description; insert the positive band-vs-out-of-scope explainer
(value-free, additive) after the existing prohibition, before `_GOVERNANCE_BAR`.
Keep the existing prohibition + OUT-OF-SCOPE clauses verbatim. This is the only
behavioural edit surface.

### Step 3 — land the offline structural test pair + invariants (AC-1..AC-5)

In `tests/services/engine/procedures/test_generator_pipeline.py`:
the guard byte-identity test (AC-1); generalize the AT-2-only-abstain test to all
three kinds (AC-2); the enriched-prompt introspection assertions (AC-3); the
descriptions-no-AT2-vocabulary lint (AC-4); the schema-unchanged assertion (AC-5).
Update any 2-tuple catalog in tests → 3-tuple.

### Step 4 — author the labelled fixture set + the pre-committed pass/fail read (OQ-C)

Add the ~26-narrative labelled fixture set (Arm A + Arm B, incl. ≥ 2 borderline
AT-2) and record the pre-committed pass/fail inequality and the recorded `before`
baseline procedure **before** any live run.

### Step 5 — Cray-gated live before/after on MS-S1 (AC-7; host-state)

**ASK Cray** before warming (CLAUDE.md §8). Warm `gpt-oss:20b` via the
`ms-s1-ollama` skill; run before/after on the fixture set, N ≥ 3 reps; record the
worst run + the per-fixture guard-path split. Live = confirming evidence.

### Step 6 — per-step PRs off `main`; Cray merges each (no self-merge)

Offline tests are the gate; each PR references PLAN-0041. The live run is reported
as evidence, not a CI gate.

## Verification

- **Offline (the verdict):** AC-1..AC-6 green — guard byte-identical, AT-2 still
  abstains on all three kinds, enriched prompt asserted by introspection,
  descriptions carry no AT-2 vocabulary, schema unchanged, full suite + ruff +
  mypy clean.
- **Red-team mitigations bound to assertions:**
  - **R1 (a description force-fits an AT-2 narrative into AT-3):** every AT-3/AT-1
    description explicitly contrasts against the multi-criteria/scored/tiered shape;
    the **borderline AT-2** Arm-B fixtures must still abstain.
  - **R2 (the positive band explainer broadly lowers abstain propensity):** the
    explainer ends on "When unsure … abstain"; the Arm-B **11/11 HARD** gate is the
    measurement that the brake still works; watch the label→backstop abstain-path
    shift.
  - **R3 (description prose re-introduces AT-2 vocabulary → a *new* false-abstain):**
    AC-4 asserts the descriptions contain none of `scored_rule`/`rule_gate`/
    `doa_tier`.
- **Live (confirming evidence, Cray-gated):** AC-7 twin metric — Arm B 11/11
  abstain (hard) AND Arm A `after > before` (≥ 9/11), worst of N ≥ 3, per-fixture
  guard-path recorded.

---

*Drafted by Cowork (session 84) — Tier-1 governance authoring (ADR-009 D1; new PLAN
= G2-gated for Code). Uncommitted; Code R2-reviews + commits via a `docs/*` PR
after Cray ratifies (ADR-009 D2). Prompt-only lever, no new ADR — the moat guard
(ADR-0024 D4/D7) is preserved untouched. §"Open Questions" recommendations
deliberated by two Code-run specialist reviewers, independent of the drafter
(ADR-012 D4.3). Trigger = a Stop-hook "proceed" (harness), relayed by Code as a
draft for Cray to review — NOT a Cray ratification; Cray's veto/redirect is open.
AI-assisted; no `Co-Authored-By` per CLAUDE.md §7.*
