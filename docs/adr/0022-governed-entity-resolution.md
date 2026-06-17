# ADR-0022: Governed entity resolution — resolve a model-emitted entity reference against the declared object universe before the governed record trusts it

**Status:** Proposed
**Date:** 2026-06-17
**Deciders:** Jirachai Thiemsert (founder) — ratifies the construct AND resolves the §"Design fork" options below
**Related:** ADR-0021 (metric-kind typed semantics — the "classify, don't synthesize" lineage this extends, and the draft→Cray-picks-the-construct ratification flow this mirrors), ADR-016 (governed procedure engine — the governed action/procedure area this enhancement lands in; it carries **no** verify/reshape clause today — see Context), ADR-007 (OCT engine contracts — D2 `RecommendedAction` envelope + `EntityRef`, generalized not broken), ADR-010 (LLM reasoning-hook surface — D5 LLM-backed `recommend()`, IN-4 deterministic fail-safe), ADR-011 (earmarked audit framework — interplay flagged for the reject/flag fork branch, not pulled in), PLAN-0027 (the **D-6 contamination guard** — the binding boundary in the §"Design fork"), PLAN-0028 / PLAN-0029 (the B-γ extension whose `## Findings` routed this universality investment OUT to "a future ADR + PLAN-0030"; the verify+reshape §3.4 forward-pointer), `benchmarks/procedure_baseline/REPORT.md` §B-3 (the verify+reshape future-enhancement forward-pointer), CLAUDE.md §1 (semantic layer = the moat), §8 (PDPA-forward; ADRs Accepted before implementation), ADR-009 D1/D2 (Cowork drafts, Code commits), ADR-012 D4.3 (author≠reviewer disclosure), ADR-013 (phased autonomy relocation; Cowork = advisory governance drafter)

> **Authoring disclosure (ADR-012 D4.3).** Drafted (uncommitted) by Cowork
> (Tier-1, ADR-009 D1) from Code's session-67 dispatch
> (`.claude/handoffs/session-67/2026-06-17-1555-code-dispatch-adr0022-governed-entity-resolution.md`).
> The construct framing, the gap evidence, the one-construct scoping, and the
> design-fork axes were **originated in Code's dispatch**, not in a Cowork
> free-form deliberation — so this is not an ADR-012 D4.3 self-deliberation case
> (no Cowork opinion is being silently promoted). The drafter is Cowork; the
> **independent reviewer is Cray at ratification + Code at PR review**. Separation
> drafter↔reviewer is **intact**. Code re-verified the cited code lines against
> the live repo this session (R2); Cowork re-verified the cross-file forward-pointers
> (PLAN-0028 §3.4 / D-6, REPORT §B-3, session-66 closeout §7-A1) against the live
> repo before asserting them.

> **Design-first — the fork is OPEN.** This ADR fixes the **construct + framing
> only**. The §"Design fork" axes are drafted as **un-decided options**; Cray
> resolves them at ratification (Proposed → Accepted), exactly as ADR-0021
> confirmed construct (b) at its ratification. **No implementation, no build
> steps** — a separate Cowork-routed **PLAN-0030** builds the ratified construct
> AFTER ratification (CLAUDE.md §6 Decision/Plan Flow; CLAUDE.md §8 ADR-Accepted-before-impl).

## Context

### Where entity identity comes from today — the gap (live-code evidence)

vero-lite's governed action layer produces a `RecommendedAction` envelope
(ADR-007 D2) for an `OperationalEvent` that trips a deterministic trigger, via
two paths in `services/engine/recommender.py`:

| Path | Builds `affected_entities` from | Universality status |
|---|---|---|
| **LLM path** — `_compose_llm_record` (`recommender.py:139-166`) | `affected_entities=judgment.affected_entities` (**`:160`**) — the LLM judgment **verbatim** | **The gap.** Entity identity is copied from model output with **no resolution** against the declared object universe. |
| **Deterministic fail-safe** — `_rule_recommend` (`:205-271`) | `affected_entities=[EntityRef(object_type=entity_type, primary_key=subject_id)]` (**`:265`**) — grounded in the **actual triggering event's** `subject_id` | **Already universal-correct.** Identity comes from the event the engine itself detected, not from model prose. |

The docstring at `recommender.py:144-149` states the harness owns `id`,
`vertical`, `created_at`, `requires_approval`, `audit_metadata`, and the
reasoning trace — but **entity identity is taken from the LLM judgment verbatim**.
Nothing resolves the model-emitted `primary_key` against the vertical's declared
object instances. The data structure offers no backstop either:
`EntityRef(object_type: str, primary_key: str, title: str | None)` is a plain
Pydantic model with **no validation** (`services/engine/actions.py:27-30`) — the
model can emit **any string** as `primary_key`, and the governed
`RecommendedAction.affected_entities` (`actions.py:52`) will certify it.

The two paths diverge precisely on the property that matters: the deterministic
path (`:265`) **grounds the entity in the event that actually fired**; the LLM
path (`:160`) **trusts the model's named identity**. This ADR's construct fixes
the **LLM path only** — the deterministic fail-safe (ADR-010 IN-4 / PLAN-0006
§6.6) is already correct and must not be regressed or re-opened.

*(For the record: the PLAN-0029 grader whitespace/`normalize_primary_key` fold
was benchmark **measurement hygiene**, not this product gap. This is the real
universality investment that PLAN-0029's `## Findings → follow-up` routed OUT to
"a future ADR + PLAN-0030".)*

### Why this is THE universality lever

A new vertical declares its object instances in the ontology (ADR-008). The
governed layer should **resolve a model-named entity against that declared
universe** — normalize the reference, match a known instance, and
reject/flag/fall-back on a non-match — rather than trust model prose or format.
This generalises across verticals and is exactly what makes the governed stack
robust where raw text-to-SQL (the B-γ comparison's arm b) is brittle: the
aquaculture 0% swing is semantic-distance evidence for the moat. It is the **same
"classify, don't synthesize" move ADR-0021 made for measurement *kind*, now
applied to entity *identity*** — the model classifies/selects against a declared
set; the governed record never certifies an identity the model invented.

### One governance family — entity resolution AND verify+reshape

Per the session-66 closeout handoff (§7-A1: A1 is "the heaviest moat-proof —
*proves* the moat IS governance: verify an LLM step's output for semantic
consistency + reshape it to the next step's contract"; and §"scope #3a together
with Group A's A1"), **#3a (entity resolution)** and **Group-A A1 (verify +
reshape)** are the **same governance family**: both validate / reshape an
LLM-emitted output before the governed envelope trusts it. They should be designed
as **one construct, not two overlapping ADR-016-area ADRs**.

Note the forward-pointer's current home: **ADR-016 itself does not yet contain a
verify/reshape clause** (grep-confirmed against the live ADR). The verify+reshape
pointer lives in the B-γ artifacts — `docs/plans/done/0028-...` §3.4 (the
"§3.4 forward-pointer (verify+reshape) … OUT OF SCOPE here") and
`benchmarks/procedure_baseline/REPORT.md` §B-3 (the procedure engine "can
(i) **verify** an LLM step's output for semantic consistency … and (ii)
**reshape** … recorded as a forward-pointer for a future PLAN/ADR"). **This ADR
is where that pointer lands.**

## Decision

> **Read this section as a frame, not a finished mechanism.** D1–D3 fix the
> construct and its boundary; the **§"Design fork"** below is deliberately left
> **open** for Cray to resolve at ratification. PLAN-0030 builds only what
> ratification selects.

### D1: The construct — *govern the LLM's emitted output against a declared contract before the governed record trusts it*

The governed action layer **resolves / verifies a model-emitted output against a
declared contract** before the governed `RecommendedAction` (or, later, a
procedure-step artifact) trusts it. Identity, like measurement kind before it
(ADR-0021), is **classified against a declared set, not synthesized by the
model**. This is a single coherent governance discipline that extends the
governed-engine area of ADR-016.

### D2: The construct has two members (one ADR, not two)

- **(a) Entity resolution** *(the immediate, PLAN-0030-buildable slice — the
  universality lever).* Resolve the LLM-emitted `EntityRef.primary_key` against
  the vertical's declared object universe before `_compose_llm_record`
  (`recommender.py:160`) trusts it: **normalize → match a known instance →
  reject/flag/fall-back on a non-match**.
- **(b) Verify + reshape** *(the A1 "heaviest moat-proof").* Verify an LLM step's
  output for semantic consistency against that step's requirement, and reshape it
  to the next step's contract — the governance capability arm (c) (naive RAG)
  structurally lacks. This is the verify+reshape §3.4 / §B-3 forward-pointer,
  here given an ADR home as the **second member of the same construct**.

(a) is a specific instance of (b): entity resolution **verifies** the emitted
identity against a declared contract (the object universe) and **reshapes** an
unresolved reference into a governed fall-back. Designing them as one construct
keeps the governance discipline coherent and avoids two overlapping ADR-016-area
ADRs.

### D3: Framing choice — surface, do not pre-pick (Cray decides at ratification)

Two ways to formalise D1/D2, surfaced rather than silently chosen:

| Option | Shape | Trade-off |
|---|---|---|
| **D3-α (recommended)** | **One** governance construct covering both facets; (a) and (b) are two members of a single "govern emitted output against a declared contract" discipline. | One coherent citation anchor; matches the "same governance family" framing (session-66 §7); slightly broader scope to ratify at once. |
| **D3-β** | A **base** construct establishing the discipline, with **(a) as its first instance** and **(b) named as a forward-declared second instance** (built later). | Narrower thing to ratify now; but risks the same two-ADR fragmentation this dispatch set out to avoid if (b) later spawns its own ADR. |

**Cowork recommends D3-α** (a single coherent governance construct) unless the
fork analysis below argues otherwise — but this is **Cray's call at ratification**.

## Design fork (OPEN — Cray resolves at ratification; mirrors ADR-0021(b))

These axes are drafted as **un-decided options**. PLAN-0030 builds the branch
Cray selects. Fork axis 3 is the exception — it is a **binding boundary**, not an
open choice.

### Fork 1 — Where does the "known universe" come from at recommend-time?

| Branch | Source of truth | Coupling / latency / staleness |
|---|---|---|
| **1-a** | The **triggering event's candidate entities** (the entities surfaced by the event that fired the recommender). | Lowest coupling; no extra read; universe is only as complete as the event payload — may miss valid entities the model legitimately names from broader context. |
| **1-b** | A **DB / ontology-object lookup** against the canonical object table (the full declared object universe). | Most complete + authoritative; adds a read at recommend-time (latency); needs a freshness/staleness story for the object table. |
| **1-c** | The **deterministic trigger's already-identified subject** (`subject_id` — the `recommender.py:265` anchor) as ground truth. | Zero extra coupling; reuses the path already proven universal-correct; **narrowest** — collapses the LLM's potentially multi-entity judgment to the single triggering subject. |

*(Each has a distinct coupling + latency + staleness profile — Cray weighs
completeness against recommend-time cost. The branches are not mutually exclusive
in principle, e.g. 1-c as the fall-back anchor under 1-b's lookup; PLAN-0030
specifies the exact composition once Cray picks the primary.)*

### Fork 2 — What happens on a non-resolving model PK?

| Branch | Behaviour | Audit implication |
|---|---|---|
| **2-a** | **Drop** the unresolved entity from `affected_entities`. | Loses information silently — note it in the trace. |
| **2-b** | **Flag** it low-confidence (keep it, marked unresolved). | Touches the audit trail (a flagged-unresolved marker). |
| **2-c** | **Fall back** to the deterministic subject (`subject_id`, the `:265` ground truth). | Cleanest grounding; converges the LLM path toward the already-correct deterministic path on failure. |
| **2-d** | **Reject** pending human review (suspend at the approval gate). | Heaviest; touches the audit trail + the approval gate. |

**Audit interplay (flag, do not pull in).** A reject-or-flag branch (2-b / 2-d)
touches the audit trail — note the interplay with the **earmarked audit-framework
ADR (ADR-011)** and `AuditMetadata` (`services/engine/actions.py:33`, "expanded in
future audit-framework ADR"). This ADR **flags** that interplay; it does not
design the audit framework.

**PDPA-forward invariant (CLAUDE.md §8) — applies to ALL branches:** the governed
record must **never silently fabricate identity**. Whatever branch is chosen, an
unresolved model PK must not be certified as a real entity without a trace of the
resolution outcome.

### Fork 3 — Boundary (BINDING, not open): governed-product path ONLY

The resolution lives in the **governed-product path ONLY**. It must **NOT** leak
into the **arm-(c) naive-RAG baseline** — this is the PLAN-0027 **D-6 contamination
guard** (re-asserted in PLAN-0028: "Arm (c) stays a CLEAN naive RAG baseline — NO
verify/reshape/governance/ontology layer bleeds in"). If the resolution
contaminates arm (c), the B-γ comparison stops being honest. **State this as an
explicit non-goal in the build.** This is a guardrail, not a choice — it binds
whatever Cray selects for forks 1 and 2.

## Constraints / guardrails (encode in PLAN-0030)

- **Design-first, no build.** This ADR is framing + fork only. **No code, no
  implementation steps.** PLAN-0030 builds it AFTER Cray ratifies the construct
  and resolves the fork (CLAUDE.md §6 Decision Flow; §8 ADR-Accepted-before-impl;
  inherited anti-moving-target spirit).
- **Deterministic path is already correct** (`recommender.py:265`). The construct
  fixes the **LLM path** (`:160`) only — do not regress or re-open the fail-safe
  (ADR-010 IN-4 / PLAN-0006 §6.6).
- **Classify, don't synthesize** (ADR-0021 lineage). Resolve/match against a
  declared set; never let the model invent an identity the governed record then
  certifies.
- **Reports-not-gates is NOT in play here.** That discipline is the B-γ benchmark's
  (B-3/B-6). This is a **product-layer governance** ADR — keep it from entangling
  with the B-γ baseline (the Fork-3 / D-6 boundary).
- **No PLAN-0030 content, no vertical-#3 here.** PLAN-0030 is a separate
  post-ratification Cowork dispatch; vertical-#3 (Rule-of-Three) research is its
  own separate Cray-directed Cowork dispatch. This ADR is scoped to the construct
  + fork only.

## Consequences

### Positive

- **The universality lever is captured as governance.** Resolving model-named
  identity against the declared object universe generalises across verticals
  (Rule of Three, ADR-006) and is the differentiator where raw text-to-SQL is
  brittle — the CLAUDE.md §1 moat thesis applied to entity identity.
- **Anti-hallucination compounds rather than being traded away.** The model
  classifies/selects against a declared set; code composes the governed identity;
  an unresolved reference routes to a defined outcome instead of silently
  certifying an invented entity.
- **"Classify, don't synthesize" is reused, not re-invented.** ADR-0021 proved the
  principle for measurement kind; this extends the *same* discipline to identity,
  and (via member (b)) forward-declares it for general verify+reshape.
- **One coherent governance construct** (under D3-α) instead of two overlapping
  ADR-016-area ADRs — a single citation anchor for the family.

### Negative

- **A new governance construct + (eventually) resolution machinery is required**
  in the LLM path — a real, if bounded, cost deferred to PLAN-0030. The fork-1
  branch chosen determines the coupling/latency cost (a DB lookup under 1-b adds a
  recommend-time read).
- **Audit-trail interplay is opened but not closed** here. The 2-b/2-d branches
  touch ADR-011's earmarked surface; this ADR flags it rather than resolving it,
  leaving a forward dependency.
- **Scope decision deferred to ratification.** Cray must resolve D3 (framing) and
  forks 1–2 before PLAN-0030 can build — the ADR intentionally does not pre-decide.

### Neutral

- **The deterministic fail-safe is untouched** (`recommender.py:265`); the
  construct only upgrades the LLM path. The `EntityRef` / `RecommendedAction`
  envelope (ADR-007 D2) shapes are not broken by this framing — whether resolution
  adds a field (e.g. a resolution-outcome marker) is a PLAN-0030 implementation
  detail, flagged not fixed.
- **Design-first** means no behavioural change ships from this ADR — only the
  decision + the build mandate for PLAN-0030.

## Alternatives Considered

### Alternative 1: Two separate ADRs (entity resolution; verify+reshape)

- **Pros:** each ADR is narrower; entity-resolution can ratify without the broader
  verify+reshape framing.
- **Cons:** the two are the **same governance family** (session-66 §7-A1) — both
  validate/reshape an LLM-emitted output against a declared contract; two ADRs
  would overlap and fragment the citation anchor.
- **Why not chosen:** the dispatch's explicit instruction is "one ADR-016-area
  construct, not two overlapping ADRs." Recorded as the rejected split (D3-α is the
  positive form).

### Alternative 2: Status quo — keep trusting the LLM `primary_key` verbatim

- **Pros:** zero work; the deterministic fail-safe already covers the non-LLM path.
- **Cons:** this **is the gap** (`recommender.py:160`) — the governed record
  certifies a model-invented identity with no backstop; brittle across verticals;
  contradicts the §1 moat thesis and "classify, don't synthesize."
- **Why rejected:** it is the very problem this ADR exists to govern.

### Alternative 3: Validate the `EntityRef` *shape* only (Pydantic constraints), no universe resolution

- **Pros:** smallest change; a regex/format constraint on `primary_key` in
  `actions.py:27-30`.
- **Cons:** a well-formed but **non-existent** PK still passes; shape validation
  does not resolve identity against the declared universe — it catches typos, not
  fabrication.
- **Why rejected:** insufficient — the universality lever is *resolution against
  the declared object set*, not format validation. (A shape constraint may still be
  a minor PLAN-0030 belt-and-suspenders, but it is not the construct.)

### Alternative 4: Always collapse the LLM path to the deterministic subject (`:265`)

- **Pros:** trivially universal-correct (reuses the proven path); no lookup.
- **Cons:** discards the LLM's potentially richer multi-entity judgment in every
  case — over-narrows to the single triggering subject even when the model
  legitimately names additional valid entities.
- **Why not chosen as the construct:** this is fork branch **1-c / 2-c**, viable as
  *a* selected branch but too blunt to mandate as *the* construct. Recorded so the
  "just always use `subject_id`" option is on the record as a fork branch, not the
  whole decision.

## References

- **The gap (live code, re-verified this session):**
  `services/engine/recommender.py:139-166` (`_compose_llm_record`; `:160` the
  trusted line), `:169-202` (`recommend` + the IN-4 fail-safe), `:205-271`
  (`_rule_recommend`; `:265` the deterministic grounded path);
  `services/engine/actions.py:27-30` (`EntityRef`, no validation), `:42-63`
  (`RecommendedAction`; `affected_entities` at `:52`), `:33` (`AuditMetadata`,
  "expanded in future audit-framework ADR").
- **The construct lineage:**
  `docs/adr/0021-metric-kind-typed-ontology-semantics.md` (D3 "classify, don't
  synthesize"; the draft→Cray-picks-the-construct ratification flow mirrored here);
  `docs/adr/0016-governed-procedure-engine.md` (the governed-engine area this
  extends — carries no verify/reshape clause today).
- **The verify+reshape (A1) forward-pointer:**
  `docs/plans/done/0028-bgamma-extension-aquaculture-supply-chain.md` §3.4 (the
  "verify+reshape … OUT OF SCOPE here" forward-pointer) + the **D-6 contamination
  guard** (inherited from PLAN-0027); `benchmarks/procedure_baseline/REPORT.md`
  §B-3 (the procedure engine "can (i) verify … and (ii) reshape …" future-enhancement
  forward-pointer); the session-66 closeout handoff §7-A1 + §"scope #3a together
  with Group A's A1".
- **The source of this construct:** the session-66 closeout handoff §4 + §7-A1;
  PLAN-0029 `## Findings → follow-up`
  (`docs/plans/done/0029-entity-key-whitespace-calibration-and-regrade.md`); Code's
  session-67 dispatch
  (`.claude/handoffs/session-67/2026-06-17-1555-code-dispatch-adr0022-governed-entity-resolution.md`).
- **Governance:** `docs/adr/0000-template.md`; CLAUDE.md §1 (semantic layer = the
  moat), §6 (Decision/Plan Flow), §8 (PDPA-forward; ADRs Accepted before
  implementation); ADR-009 D1/D2 (Cowork drafts, Code commits); ADR-012 D4.3
  (author≠reviewer disclosure); ADR-013 (phased autonomy relocation — Cowork =
  advisory governance drafter).
- **Audit interplay (flagged, not pulled in):** ADR-011 (earmarked audit
  framework); `services/engine/actions.py:33` `AuditMetadata`.

## Implementation Notes

- **Number:** `0022` confirmed free at authoring (highest used = ADR-0021;
  ADR-0014 is WITHDRAWN; no `0022` file exists — Glob of `docs/adr/` confirms).
  Code confirms the number at commit.
- **Routing + ratification flow (mirror ADR-0021 exactly):**
  1. **Cowork** authors this draft (Proposed) — framing + the §"Design fork" as
     open options + guardrails + the author≠reviewer disclosure. *(done)*
  2. **Code** commits it **Proposed** via a `docs(adr):` chore PR (ADR-009 D2; the
     "Cowork drafts ungated, Code commits" path).
  3. **Cray** ratifies **Proposed → Accepted**, resolving D3 (framing) + forks 1–2
     (the construct branch). Cowork authored, so **Cray is the independent
     reviewer** — the independent-deliberation check (ADR-012 D4.3).
  4. **Then** a separate Cowork dispatch authors **PLAN-0030** to build the
     ratified construct (the entity-resolution slice (a) first).
- **Governance gate:** PLAN-0030's implementation PR is gated on this ADR being
  **Accepted before** the PR (CLAUDE.md §8).
- Drafted by Cowork (Tier-1, ADR-009 D1); uncommitted. Code reviews + commits via a
  `docs(adr):` chore PR (ADR-009 D2). AI-assisted (Claude); no `Co-Authored-By` per
  CLAUDE.md §7.
