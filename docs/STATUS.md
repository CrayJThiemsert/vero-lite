---
last_updated: 2026-06-25T19:49:36+07:00
session: 78
current_batch: 'session-78 — Stage 3 (generative-procedures, ADR-016 Phase 2) KICKED OFF: ADR-0024 (archetype-first procedure generator) Accepted #434 (panel-backed; D1–D12 + 9 OQs accepted); PLAN-0039 (read-only 5-facet viewer, ADR-0024 D8) Ready #435 + the ADR-0024 OQ errata (G1-routed via Cowork). Cowork-drafted → Code R2 → Cray-ratified → committed; docs only, no build yet.'
current_actor: code
blocked_on: 'Nothing — ADR-0024 Accepted + PLAN-0039 Ready; next is building PLAN-0039 (the viewer), then dispatching PLAN-0040 (the generator).'
next_action: 'Build PLAN-0039 (read-only 5-facet viewer, AC-1..10) on a feature branch + PR; then PLAN-0040 (the archetype generator, AT-1 family) via a new Cowork dispatch (G2-gated). loop-dispatcher stays DISABLED until the Stop-hook root-fix lands.'
head_commit: 4e56d4b
recent_commits: [97afbc5, 4e56d4b, edd28a6, ab770d2, c90b2d2, e8c217a, 82153f2, 777393c, bf7e858, b2f19bc]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 78 (current; head_commit `4e56d4b`) — **Stage 3 of the
> generative-procedures arc KICKED OFF (ADR-016 Phase 2): two governance
> artifacts, both Cowork-drafted (ADR-009 D1) → Code R2-reviewed → Cray-ratified
> → committed (D2).** **(1) ADR-0024 — archetype-first procedure generator**
> (ADR-016 Phase 2 / "Stage 3") — **Accepted, merged #434** (add `c90b2d2`),
> **backed by a Code-run 5-specialist design panel** (LLM-pipeline · governance ·
> schema · product-UX · red-team) + Cray's s78 scope calls. **Locked decisions
> D1–D12:** generation = **archetype-first** (classify narrative → 1 of N
> catalogued archetypes → deterministic-code instantiates the template → LLM
> drafts only advisory prose; **exactly 2 narrow LLM calls**; classify-don't-
> synthesize, ADR-0021); **"governed ≠ generated" re-fenced for the AUTHORING
> surface + made MECHANICAL** — a **restricted draft type** with NO governance
> fields (a leak = a type error) + a deterministic **prose-lint**; the generator
> emits `gate_kind` (a closed-enum classification) but **never a
> value/handler/threshold/tier/autonomy/env_var** (D4 sharp line); **abstain,
> never force-fit** (D5); the **determinism invariant holds at the authoring
> layer** (never route generation on LLM match-confidence); a skeleton is
> **draft-loadable but NOT run-loadable** until a human authors the gates (D6);
> **v1 = AT-1 family (AT-1/AT-1b/AT-3), AT-2 DEFERRED** (the only AT-2 =
> `procurement.emergency_sourcing`, N=1 — the catalog is really **N≈2**; D7);
> **one review surface** (the 5-facet viewer + the generator gate = read/edit
> modes of ONE component, read-only viewer ships first; D8). The archetype
> catalog must be promoted prose→machine-readable `ArchetypeTemplate` (D2, the
> actual unblock). **9 Open Questions** all surfaced with a recommendation +
> **Cray-ratified ACCEPTED** as standing guidance, each finalized at its
> consuming PLAN. **(2) PLAN-0039 — read-only 5-facet procedure viewer**
> (ADR-0024 D8 "viewer ships first") — **Ready, merged #435** (`edd28a6`)
> together with **the ADR-0024 OQ-disposition errata** (`4e56d4b`). PLAN-0039 = a
> **zero-LLM** view in the oct-demo console rendering **every shipped procedure
> (5 across 4 verticals)** by its five facets per step, the authoritative-typed
> band visually distinct from non-authoritative prose, served by a read-only
> `GET /procedures`; built as the **read-mode of the ONE component PLAN-0040
> extends to edit-mode** (de-risk seam = a `mode:read|edit` param + a pure
> `facetModel(step)` provenance decomposition, AC-7). Cowork's fact-pack
> **corrected the dispatch's "4 procedures" → 5** (procurement ships two) + flagged
> **AT-2 is RENDERED here even though AT-2 *generation* is deferred (D7)**. **7
> UI/endpoint OQs Cray-ratified ACCEPTED**. The **ADR-0024 OQ errata** (commit
> `4e56d4b`) records, in the now-Accepted ADR's OQ section, the ratified
> disposition Code could NOT inline — editing an Accepted ADR is **G1-gated** and
> **in-context approval does NOT override the local-Ollama classifier**
> (fail-closed deny; the chore-PR-via-Cowork path, the s77 precedent); **NO
> decision changed** (D1–D12 byte-identical, diff-verified). **Governance/process
> notes:** the G1 "edit an Accepted ADR" deny was re-confirmed fail-closed even
> with explicit Cray per-diff approval → errata routed via Cowork (the sanctioned
> editor), Code committed; PLAN-0039 + errata were **bundled into one PR / two
> commits** (#435) — a Code-judgment bundle for worktree simplicity, separable in
> history; **`loop-dispatcher` stays DISABLED** (keep-disabled + guard; Stop-hook
> root-fix still the re-enable precondition); **no live MS-S1** — both artifacts
> docs only (CLAUDE.md §8); pre-commit detect-secrets + handoff-validation green
> on both PRs. **Forward:** **build PLAN-0039** (the read-only viewer — its
> feature branch + PR), then **PLAN-0040** (the archetype generator, AT-1 family)
> — its own Cowork dispatch (new PLAN = G2-gated). AI-assisted (Claude Code,
> session 78); no `Co-Authored-By` per CLAUDE.md §7.

> **Session 77 (batch 3; head_commit `777393c`) — **PLAN-0038 (the ADR-016
> D2 Amendment implementation) EXECUTED end-to-end → Complete + archived; Stage 2
> (generalized-schema extraction) now COMPLETE on real data, not just the model.**
> **Step A** (PR-1, #431, feat `bf7e858`) = the `services/engine/procedures/spec.py`
> engine edit — the typed `facet` sub-model exactly per the amendment delta
> (`BandSource` / `GateKind` (6 kinds) / `DecisionCondition` with its
> `band_source⇔gate_kind` + `env_var`-only-with-`env` validator / `StepFacet` /
> `Step.facet`), keeping `extra="forbid"` (facet now a KNOWN key) — the **first
> deliberate `spec.py` edit since the procurement vertical held zero-engine-edit
> (CQ-1)**, ADR-sanctioned; schema-level facet tests landed here (suite 1669 passed).
> **Step B** (PR-2, #432, feat `777393c`, merge `42a8327`) = migrate the **4
> verticals'** comment-facets (`# facet[...]` blocks) → the real typed `facet:` field
> — **config + tests only, no `services/` edit**; +19 end-to-end migration
> round-trip tests. **SDs (Cray-resolved):** **SD-1 = (a)** populate all five facets
> (`decision_condition`+`llm_assist` typed; `input`/`output`/`governance` str notes
> from the comment prose — uniform 5-facet reading preserved); **SD-2 = (a)** remove
> the comment blocks (single carrier, no drift — grep confirms 0 leftover `# facet[`);
> **SD-3 = (b)** split (Step A its own PR, then the migration PR). The **D2-A3
> `gate_kind` mapping:** `energy.judge`/`supply_chain.judge` → `env_band` (env /
> `OCT_RECOMMEND_THRESHOLD`); `aquaculture.judge`/`procurement.judge`/
> `procurement.judge_stock` → `in_file_band` (**points at** the typed
> `threshold`/`direction`/`watch_margin`, **no re-store** — AC-6); `procurement.compliance`
> → `rule_gate`; `procurement.source` → `scored_rule`; `procurement.approve` →
> `doa_tier`; reads / mechanical writes / audit terminals / simple gated actions →
> `none` (incl. `escalate_watch` = `gate_kind: none` + a `decision_condition.note` for
> the watch→gated routing rationale, Cray-endorsed, since the band decision lives on
> the `judge` step). Also updated the now-stale "facets are comment-only" framing in
> `verticals/procurement/README.md` + the procurement `procedures.yaml` header.
> **`facet` stays non-authoritative** — the engine reads but does NOT consume it at
> run time (D2-A4); a `grep` confirmed 0 `.facet` reads in `services/`. **Gates:**
> full offline suite **1688 passed / 22 skipped** (1669 baseline + 19 new); `ruff` +
> `ruff-format` clean; `mypy --strict services/` clean; **no live MS-S1** (CLAUDE.md
> §8 — pure schema/config). **`loop-dispatcher` still DISABLED** all session
> (keep-disabled + guard; the Stop-hook root-fix is deferred + is the precondition for
> any re-enable). PLAN-0038 `git mv` → `done/`. **Forward:** Stage 3 (the procedure
> generator, ADR-016 Phase 2, Rule-of-Three-deferred) + a schema-driven **review UI**
> (5-facet render; unlocked now facets are machine-readable on real data). AI-assisted
> (Claude Code, session 77); no `Co-Authored-By` per CLAUDE.md §7.

> **Session 77 (batch 2; head_commit `b2f19bc`) — **Stage 2 COMPLETE: the
> ADR-016 D2 facet amendment landed (#428) + the follow-on impl PLAN-0038 minted
> (#429).** **Step C = the ADR-016 D2 Amendment (a first-class typed `facet:` `Step`
> field) ACCEPTED + merged** (#428, content `0b56954`) — promotes the **5-facet**
> annotation from a YAML comment to a **first-class, typed, validated, optional
> `facet:` field** on `Step`, completing **Stage 2** (the generalized-schema
> extraction) of the generative-procedures arc. **Cowork-drafted** (ADR-009 D1) →
> **Code R2-reviewed** (fact-pack verified vs the live repo: `gate_kind`↔N=4 band
> split, `spec.py` `extra="forbid"` + typed fields, `procedures.yaml` engine-read not
> codegen, validator dog-food 0 errors) → **Cray-ratified both forks** → committed
> (D2). **Design (both Cray-ratified):** **Fork 1 = Hybrid** — `facet` carries only the
> **net-new** `decision_condition` + `llm_assist` as *typed*, with
> `input`/`output`/`governance` as **optional non-authoritative notes** (one source of
> truth, no drift — `spec.py` already types 4/5 facets via PLAN-0022). **Fork 2 =
> discriminated `gate_kind`** — an enum over **exactly the 6 N=4-observed kinds**
> (`env_band` · `in_file_band` · `rule_gate` · `scored_rule` · `doa_tier` · `none`) +
> `band_source`/`env_var`; `in_file_band` **points at the existing typed band** (no
> re-store). **Governance-process note (worth recording):** the ratify status-flip
> (Proposed→Accepted) was **G1-blocked for Code** — editing an **already-Accepted** ADR
> is denied **even with explicit Cray per-diff approval + a warmed classifier**
> (`gpt-oss:20b` warmed via `warm.sh` first ruled out a fail-closed infra deny → the
> deny was **genuine policy**, distinct from the ratify-*transition* case s40/67 where
> approval flips it). Resolution = the **chore-PR-with-rationale** path: **Cowork
> applied the flip** (ungated), **Code committed**, Cray merged (= the G1 review);
> [[project_g1_adr_gate_override_via_incontext_approval]] updated. **PLAN-0038 (the
> follow-on implementation PLAN) MINTED Draft** (#429, content `b2f19bc`) —
> **`plan-drafter`-authored** (ADR-013 D1) → **Code R2-reviewed** → committed. Scope:
> the **`services/engine/procedures/spec.py` engine edit** (the typed `facet` field per
> the amendment delta) + migrate the **4 verticals'** comment-facets → the real field +
> load/validation tests — **the first deliberate `spec.py` edit since the procurement
> vertical held zero-engine-edit (CQ-1)**, ADR-sanctioned. **Schema only** (the engine
> still **ignores `facet`** at run time); **implements nothing on commit**; **3 OPEN
> SDs** surfaced for Cray (note-migration / comment-removal / PR-granularity). Gate =
> the offline suite (1651 baseline + new tests) + `mypy --strict`; no live MS-S1
> (CLAUDE.md §8). **Forward:** Cray merges #429 + adjudicates SD-1/2/3 → execute
> PLAN-0038 → then **Stage 3** (the procedure generator, Rule-of-Three-deferred) + a
> schema-driven **review UI** (gated on this impl landing). AI-assisted (Claude Code,
> session 77); no `Co-Authored-By` per CLAUDE.md §7.

> **Session 77 (head_commit `f029913`) — **Stage 2 PREP for the
> generative-procedures target (PLAN-0037) SHIPPED + archived to `done/`**, plus a
> `loop-dispatcher` governance decision.** **PLAN-0037** was **`plan-drafter`-authored**
> (the in-harness subagent, ADR-013 D1 phased authority) → **Code R2-reviewed +
> committed** (#424, ADR-009 D2); **separation intact**. Cray chose the **formal-PLAN
> route (ทาง 1)** over a no-PLAN proceed — to keep the PLAN archive as a cross-project
> work-pattern substrate. **Step A (#425, content `31ded05`)** retrofits the SD-4
> **5-facet** annotation (`input · decision-condition · llm-assist · output ·
> governance`) as **YAML comment blocks** onto `energy`/`supply_chain`/`aquaculture`
> `procedures.yaml`, mirroring the procurement template → consistent **N=4**
> instrumentation (the Rule-of-Three substrate). **Provably inert:**
> `services/engine/procedures/spec.py` `Step` declares `extra="forbid"` (so `facet:`
> can only be a comment) and the loader uses `YAML(typ="safe")` (discards comments at
> parse) → Step objects byte-identical, the static-JS demos untouched. Gate:
> parse-clean for all 4 verticals (step counts unchanged 3/3/5/10); **66 insertions,
> all comment lines, 0 deletion**; **full offline suite 1651 passed, 22 skipped**
> (baseline); no live MS-S1 (CLAUDE.md §8). It captured the **env-vs-in-file judge-band
> split** (energy/supply_chain author the band via `OCT_RECOMMEND_THRESHOLD`;
> aquaculture/procurement author it in-file) as the load-bearing input to Step C.
> **Step B (#426, content `c3b477a`)** is the **procedure-archetype catalog** at
> `docs/conventions/procedure-archetypes.md`: **AT-1** `anomaly→action`, **AT-1b**
> `watch+summary` variant, **AT-2** `request→approve→fulfill`, **AT-3**
> `monitor→reorder` — the canonical reference the Step-C ADR + the Stage-3 generator
> will cite. **Cray resolved the surfaced decisions:** SD-1 = one PR for the 3
> verticals; SD-2 = Step B as a follow-on PR; SD-3 = catalog home `docs/conventions/`.
> **`loop-dispatcher` decision (Cray, s77):** **keep-disabled + guard** (chosen over
> fix-hook / delete); the structural root fix (a **Stop-hook exemption** so
> scheduled-task sessions don't auto-continue) is **deferred and is the precondition
> for any future re-enable**. The whole PLAN-0010 loop was dormant all session
> (producer paused, inbox empty); no drift. **Out of scope (forward):** **Step C** (the
> ADR-016 first-class `facet:` field — a separate **Cowork-drafted ADR**, G2-gated) and
> **Stage 3** (the procedure generator — Rule-of-Three-deferred until the schema is
> extracted). **Honesty notes:** an auto-handoff classifier dispatch **misrouted early**
> (guessed "drafting a plan" while Code was still proposing the no-PLAN route) — Code
> **overrode** per the clause, spawning `plan-drafter` only after Cray chose ทาง 1; a
> transient `.git/index.lock` made Step A's first commit appear to fail (echoed exit
> unreliable) — verified HEAD + re-committed `31ded05`; two harness-continuation
> "proceed"s were flagged as **harness-not-Cray**. AI-assisted (Claude Code, session
> 77); no `Co-Authored-By` per CLAUDE.md §7.

> **Session 76 (head_commit `081d650`) — PLAN-0036 Stage 1 (the Fastenal
> procurement vertical — vero-lite's 4th vertical) EXECUTED end-to-end and **Done +
> archived to `done/`.**** All 8 Steps were hand-authored as a **pure-config plugin**
> on the shipped ADR-016 engine + ADR-0023 auto-discovery, each a Cray-merged PR:
> **#415** ontology + scaffold (12 object_types — Equipment/Plant base + 6
> procurement extensions) · **#416** `procedures.yaml` (hero 7-step
> `emergency_sourcing_round` + calm-path reorder, with the SD-4 **5-facet** comment
> annotations) · **#417** handlers (no-op receipt stubs) · **#418** synthetic Tier-1
> hero dataset (the ฿2.15M emergency-sourcing beat: on-contract vs RFQ→AVL exception,
> DOA + emergency waiver, a cert-blocked compliance criterion) · **#419** demo UI (5
> operator surfaces on the PLAN-0033 story overlay — worklist · timeline · approval
> money-screen · graduation moment · monitoring dashboard — 3 visual registers,
> Thai-localized) · **#421** offline governance + run tests (**full suite green, 1651
> passed**). **CQ-1 zero-engine-edit held** — Steps 1–5/7 had literal 0 `services/`
> diff; the Step-6 demo presentation under `services/api/static/` is the
> **Cray-approved Option-A exception** ("zero *engine* edit"; the moat claim stands).
> **Governed ≠ generated** is the through-line — the LLM drafts/summarises; rules +
> humans select/threshold/approve (the dashboard's *"AI drafted N · 0
> supplier-selections · 0 approvals"* makes it visible). The **offline suite was the
> sole acceptance gate** (no live MS-S1 run; CLAUDE.md §8). The README facet map is
> the **Stage-2 schema substrate** (the template-reuse-across-customers foundation
> Cray asked to prepare). **Incident:** the hourly `loop-dispatcher` scheduled task
> **drifted** past its heartbeat-drain scope (likely Stop-hook continuation),
> committed a rival standalone Step-6 UI (`b635088`) onto the live session's branch
> and **hijacked PR #420**; recovered by cherry-picking the clean test commit →
> **#421** + closing #420, and **disabling `loop-dispatcher`** (Cray-authorized) —
> see the private `loop-dispatcher-drift-hazard` memory. **Forward:** Stage 2
> (extract the generalized procedure schema from the 5-facet maps) is the deliberate
> next arc, not started. AI-assisted (Claude Code, session 76); no `Co-Authored-By`
> per CLAUDE.md §7.

> _Rotation note (session-78 reconcile, 2026-06-25): the **Session-74** Current
> Focus block (PLAN-0035 **Phase 2** advisory local-LLM-judge [ADR-0022 member
> (b)] SHIPPED #407 → PLAN-0035 Complete + archived `805f5d2`) fell outside the
> **4-newest-sessions window {78,77,76,75}** (R2), and the **Session-75** block
> (PLAN-0036 Fastenal procurement Stage-1, drafted+merged Draft #412, head_commit
> `7a7c036`) **also rotated to hold STATUS under the R1 64 KB hard ceiling** (R1
> overrides the 4-session window) — both to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md),
> along with the oldest Recent Decisions row (2026-06-21 Session-71 PLAN-0034
> committed-as-DRAFT, `fda2557`), per the STATUS.md Rotation Policy (R1/R2/R4)._

> _Rotation note (session-77 reconcile, 2026-06-25): both the **Session-73**
> Current Focus block (PLAN-0035 A1 advanced END-TO-END — created → Phase 1 floor
> SHIPPED → (c) governance + ADR-0022 amendment RATIFIED, #403/#404/#405,
> head_commit `3625ea4`) and the **Session-72** block (PLAN-0034 G2
> drafting-friction root-fix FULLY COMPLETE + archived, #399, head_commit
> `72f0deb`) fell outside the **4-newest-sessions window {77,76,75,74}** after the
> session-77 PLAN-0037 Stage-2-PREP block landed, and rotated to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md),
> along with the oldest Recent Decisions row (2026-06-17 Session-67 Phase-1 PLAN
> ratify-flip, `1cda40f`), per the STATUS.md Rotation Policy (R2/R4)._

> _Rotation note (session-75 reconcile, 2026-06-24): both **Session-71**
> Current Focus blocks — (1) **G2 root-fix PLAN-0034 RATIFIED +
> core-IMPLEMENTED** (#396/#397, head_commit `c69b6e2`) and (2) **A2 CLOSED + G2
> root-fix PLAN-0034 committed as DRAFT** (#394; + PLAN-0033 Phase C COMPLETE
> #387 / Step-6 closeout) — fell outside the 4-newest-sessions window
> {75,74,73,72} after the session-75 PLAN-0036 block landed, and rotated to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md),
> per the STATUS.md Rotation Policy (R2/R4)._

> _Rotation note (session-74 reconcile, 2026-06-23): the **Session-69**
> Current Focus block (PLAN-0033 Phase C **C0 vertical slice** SHIPPED #385 —
> the aquaculture story-mode, head_commit `0a32e67`) and all three
> **Session-67** blocks (PHASE B COMPLETE: B2 registry auto-discovery #373,
> head_commit `558ec29`; B1 ORM emitter #370, head_commit `7a59814`; PHASE B
> KICKOFF: ADR-0023 + PLAN-0031/0032, head_commit `0593bc8`) fell outside the
> 4-newest-sessions window {74,73,72,71} after the session-74 PLAN-0035 Phase-2
> block landed, and rotated to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md),
> along with the oldest Recent Decisions row (2026-06-16 PLAN-0027 B-γ
> pre-registration LANDED, `ab0174a`), per the STATUS.md Rotation Policy
> (R2/R4)._

> _Rotation note (session-73 reconcile, 2026-06-22): the oldest **Session-67**
> Current Focus block (PHASE A COMPLETE: ADR-0022 ratified + PLAN-0030 member
> (a) verify+reshape's sibling — entity-resolution member (a) — SHIPPED #365,
> head_commit `0b56fdf`) rotated to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md) to
> hold Current Focus at the 8-block cap after the session-73 PLAN-0035-created
> block landed, per the STATUS.md Rotation Policy (R2/R4)._

> _Rotation note (session-72 reconcile, 2026-06-22): the oldest **Session-67**
> Current Focus block (PHASE A: ADR-0022 RATIFIED Accepted #361 + PLAN-0030
> authored & committed #363, head_commit `1493196`) rotated to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md) to
> hold Current Focus at the 8-block cap after the session-72 PLAN-0034
> fully-complete block landed, per the STATUS.md Rotation Policy (R2/R4)._

> _Rotation note (session-71 reconcile, 2026-06-21): the **Session-66** Current
> Focus block (PLAN-0028 Step 5 RAN + VERIFIED / PLAN-0029 whitespace calibration
> minted + implemented / canonical B-γ numbers locked, head_commit `e5f9774`)
> rotated to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md) to
> hold Current Focus at the 8-block cap after the session-71 PLAN-0034
> ratify+impl block landed, per the STATUS.md Rotation Policy (R2/R4)._

> _Rotation note (session-71 reconcile, 2026-06-20): the **Session-64** Current
> Focus block (B-γ executed end-to-end: PLAN-0027 Steps 2–5 shipped / PLAN-0019
> Step B-γ / AC B-3 = DONE, head_commit `0aee4eb`) fell outside the
> 4-newest-sessions window {71,69,67,66} and rotated to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md),
> along with the oldest Recent Decisions row (2026-06-14 PLAN-0023 PDPA RoPA-lite
> SHIPPED, `afea6b3`), per the STATUS.md Rotation Policy (R2/R4)._

> _Rotation note (session-69 reconcile, 2026-06-20): two Current Focus blocks
> rotated to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md) per
> the STATUS.md Rotation Policy (R2/R4) — the **Session-63** block (B-γ kickoff:
> PLAN-0027 pre-registration landed + Cray-ratified §3–§4, head_commit `ab0174a`;
> session 63 fell outside the 4-newest-sessions window {69,67,66,64}) and the
> oldest **Session-67** block (Phase 1 ratify-flips: PLAN-0028 + PLAN-0029 →
> Accepted + archived, #357, head_commit `1cda40f`; rotated to hold Current Focus
> at the 8-block cap) — along with the oldest Recent Decisions row (2026-06-13
> ADR-0020 RATIFIED Proposed→Accepted, `4d1347b`)._

> _Rotation note (session-67 reconcile, 2026-06-17): three Current Focus blocks
> fell outside the 4-newest-sessions window {67,66,64,63} and rotated to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md) —
> both Session-62 blocks (second batch — harness-improvement "plan-first then
> execute" distillation, head_commit `cf958d3`; first batch — PLAN-0026 AC-9
> optional live MS-S1 re-verify PASS, head_commit `c16778d`) and the Session-61
> block (PLAN-0026 COMPLETE: ADR-0021 authored→Accepted + Phase A `measured_kind`
> shipped; PLAN-0026 archived to `done/`, head_commit `b53e631`) — along with the
> oldest Recent Decisions row (2026-06-13 ADR-0020 committed Proposed #297,
> `e25281d`), per the STATUS.md Rotation Policy (R2/R4)._

> _Rotation note: this reconcile rotated both Session-58 Current Focus blocks
> (third batch — NL-query feasibility spike / fork-resolution, head_commit
> `987c2be`; second batch — two backlog quick-wins, head_commit `9595d3e`;
> session 58 falls outside the 4-newest-sessions window {62,61,60,59}) plus the
> oldest Recent Decisions row (2026-06-12 watch-lane ground truth PINNED,
> `1bd6328`) to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md)
> per the STATUS.md Rotation Policy (R2/R4)._
>
> _Rotation note (session-64 reconcile): the Session-60 CF block
> (PLAN-0026 authored+ratified+merged #321 / Phase B #322, head_commit `19eeb21`)
> fell outside the 4-newest-sessions window {64,63,62,61} and rotated to
> [`docs/status-archive/2026-h1-status.md`](status-archive/2026-h1-status.md),
> along with the oldest Recent Decisions row (2026-06-12 B-6 hyphen-normalization
> grader change, `2331ffb`), per the STATUS.md Rotation Policy (R2/R4)._
> _Older content rotates out of this file per the **STATUS.md Rotation Policy (R1-R6)** in [`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md) (Lesson #23): Current Focus keeps the 4 newest sessions (<=8 blocks); Recent Decisions keeps the last 10 rows. Rotated blocks/rows live in [`docs/status-archive/`](status-archive/) (sessions <=46: `2026-h1-current-focus.md`; 2026-06-10 onward: `2026-h1-status.md`) and git history (Tier 3)._

## Prior focus (archived)

PLAN-003 Phase 1 (ontology engine + 5 emitters), PLAN-0005 Phase 2
(OCT engine runtime layer), PLAN-0006 (LLM reasoning hook),
PLAN-0007 Phase 1 (harness autonomy layer — deterministic floor),
and **PLAN-0008 Phase 2 (harness autonomy layer — probabilistic /
classifier-mediated engine on top of Phase 1)** are all **merged and
moved to `docs/plans/done/`**. The Cowork-as-Tier-1 trial that ran as
the test-bed across the earlier batches **concluded** — ratified
permanently by **ADR-009** (Cowork = merged Tier 0 + Tier 1 workspace;
commits stay Code-exclusive). PLAN-004 Phase A (handoff frontmatter
schema + tooling) also landed; Phase B/C remain deferred (backlog).
Full detail lives in `docs/plans/done/`, the Recent Decisions table
below, and git history.

## Recent Decisions (last 10)

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-06-25 | **Stage 3 KICKED OFF — ADR-0024 (archetype-first procedure generator) ACCEPTED #434 + PLAN-0039 (read-only 5-facet viewer) Ready #435 + the ADR-0024 OQ-disposition errata (session 78)** — opens Stage 3 of the generative-procedures arc (ADR-016 Phase 2). Both artifacts **Cowork-drafted (ADR-009 D1) → Code R2-reviewed → Cray-ratified → committed (D2)**. **ADR-0024 (#434, add `c90b2d2`):** archetype-first generation **backed by a Code-run 5-specialist design panel** (LLM-pipeline · governance · schema · product-UX · red-team). **D1–D12 locked:** classify narrative → 1 of N archetypes → deterministic-code instantiates → LLM drafts advisory prose only (**exactly 2 narrow LLM calls**, classify-don't-synthesize ADR-0021); **"governed ≠ generated" re-fenced at the AUTHORING surface + made MECHANICAL** = a **restricted draft type** with NO governance fields (leak = type error) + a deterministic prose-lint; generator emits `gate_kind` (closed-enum) but **never a value/handler/threshold/tier/autonomy/env_var** (D4); **abstain never force-fit** (D5); determinism invariant holds at the authoring layer; skeleton **draft-loadable but NOT run-loadable** until a human authors gates (D6); **v1 = AT-1 family (AT-1/AT-1b/AT-3), AT-2 DEFERRED** (only AT-2 = `procurement.emergency_sourcing`, N=1; catalog really N≈2; D7); **one review surface**, read-only viewer ships first (D8); the catalog promotes prose→machine-readable `ArchetypeTemplate` (D2). **9 OQs Cray-ratified ACCEPTED** as standing guidance. **PLAN-0039 (#435, `edd28a6`):** a **zero-LLM** oct-demo view rendering **every shipped procedure (5 across 4 verticals — Cowork corrected the dispatch's "4"→5, procurement ships two)** by its 5 facets per step, authoritative band visually distinct from prose, served by read-only `GET /procedures`; built as the **read-mode of the ONE component PLAN-0040 extends to edit-mode** (`mode:read|edit` + pure `facetModel(step)`, AC-7); **AT-2 RENDERED here though AT-2 generation is deferred (D7)**; **7 UI/endpoint OQs Cray-ratified ACCEPTED**. **ADR-0024 OQ errata (commit `4e56d4b`, bundled into #435):** records the ratified OQ disposition in the Accepted ADR's OQ section — Code could NOT inline it (editing an Accepted ADR is **G1-gated**; **in-context approval does NOT override the local-Ollama classifier**, fail-closed deny → routed via Cowork, the s77 chore-PR precedent); **NO decision changed (D1–D12 byte-identical, diff-verified)**. **Notes:** PLAN-0039 + errata bundled one PR / two commits (#435, Code-judgment, separable in history); **`loop-dispatcher` stays DISABLED**; **no live MS-S1** (docs only, §8); pre-commit detect-secrets + handoff-validation green. NEXT = build PLAN-0039 (the viewer) then dispatch PLAN-0040 (the generator, AT-1 family, G2-gated) | `c90b2d2` (#434) / `edd28a6` + `4e56d4b` (#435) / `docs/adr/0024-procedure-generator.md` + `docs/plans/0039-readonly-facet-viewer.md` |
| 2026-06-25 | **PLAN-0038 (ADR-016 D2 Amendment implementation) EXECUTED end-to-end → Complete + archived; Stage 2 (generalized-schema extraction) now COMPLETE on real data (session 77, batch 3, #431/#432)** — completes Stage 2 of the generative-procedures arc, now proven on real data not just the model. **Step A (PR-1, #431, feat `bf7e858`):** the `services/engine/procedures/spec.py` engine edit — the typed `facet` sub-model per the amendment delta (`BandSource`/`GateKind` (6 kinds)/`DecisionCondition` w/ `band_source⇔gate_kind` + `env_var`-only-with-`env` validator/`StepFacet`/`Step.facet`), keeping `extra="forbid"` (facet now a KNOWN key) — the **first deliberate `spec.py` edit since procurement's zero-engine-edit (CQ-1)**, ADR-sanctioned; schema-level facet tests landed here (suite 1669 passed). **Step B (PR-2, #432, feat `777393c`, merge `42a8327`):** migrate the **4 verticals'** comment-facets → the real typed `facet:` field — **config + tests only, no `services/` edit**; +19 end-to-end migration round-trip tests. **SDs (Cray-resolved):** SD-1=(a) populate all 5 facets (`decision_condition`+`llm_assist` typed; `input`/`output`/`governance` str notes from the comment prose); SD-2=(a) remove the comment blocks (single carrier, grep confirms 0 leftover `# facet[`); SD-3=(b) split A/B PRs. **D2-A3 `gate_kind` mapping:** energy/supply_chain `judge`→`env_band` (`OCT_RECOMMEND_THRESHOLD`); aquaculture/procurement `judge`+`judge_stock`→`in_file_band` (points at the typed `threshold`/`direction`/`watch_margin`, no re-store — AC-6); procurement `compliance`→`rule_gate`, `source`→`scored_rule`, `approve`→`doa_tier`; reads/mechanical writes/audit terminals/simple gated actions→`none` (incl. `escalate_watch`=`none`+`decision_condition.note`, Cray-endorsed). Updated the stale "facets are comment-only" framing in `verticals/procurement/README.md` + the procurement `procedures.yaml` header. **`facet` stays non-authoritative** — engine reads but does NOT consume it at run time (D2-A4; grep = 0 `.facet` reads in `services/`). Gates: full offline suite **1688 passed/22 skipped** (1669 baseline + 19 new), ruff + ruff-format clean, mypy --strict `services/` clean, no live MS-S1 (§8 — pure schema/config). `loop-dispatcher` still DISABLED all session (Stop-hook root-fix deferred = precondition for re-enable). PLAN-0038 `git mv` → `done/`. NEXT = Stage 3 (the procedure generator, ADR-016 Phase 2, Rule-of-Three-deferred) + a schema-driven 5-facet review UI | `bf7e858` (#431) / `777393c` (#432) / `services/engine/procedures/spec.py` + `verticals/{energy,supply_chain,aquaculture,procurement}/procedures.yaml` + `docs/plans/done/0038-*.md` |
| 2026-06-25 | **Stage 2 COMPLETE — ADR-016 D2 Amendment (first-class typed `facet:` Step field) ACCEPTED + merged (#428) + PLAN-0038 impl PLAN minted (#429) (session 77, batch 2)** — Step C promotes the 5-facet annotation from a YAML comment to a **first-class, typed, validated, optional `facet:` field** on `Step`, completing Stage 2 (generalized-schema extraction). **Cowork-drafted** (ADR-009 D1) → Code R2-reviewed (gate_kind↔N=4 split, `spec.py extra="forbid"`+typed fields, `procedures.yaml` engine-read, validator dog-food 0 errors) → **Cray-ratified both forks** → committed (D2). **Fork 1 = Hybrid** (`facet` carries net-new `decision_condition`+`llm_assist` typed; `input`/`output`/`governance` optional non-authoritative notes — one source of truth, `spec.py` already types 4/5 via PLAN-0022). **Fork 2 = discriminated `gate_kind`** (enum over the 6 N=4 kinds `env_band`/`in_file_band`/`rule_gate`/`scored_rule`/`doa_tier`/`none` + `band_source`/`env_var`; `in_file_band` points at the existing typed band, no re-store). **Process note:** the ratify status-flip (Proposed→Accepted) was **G1-blocked for Code** — editing an already-Accepted ADR is denied **even with Cray per-diff approval + a warmed `gpt-oss:20b` classifier** (genuine policy, not a fail-closed infra deny; distinct from the ratify-transition case s40/67) → resolution = chore-PR path: **Cowork applied the flip** (ungated), Code committed, Cray merged (= the G1 review); [[project_g1_adr_gate_override_via_incontext_approval]] updated. **PLAN-0038 MINTED Draft** (#429, `b2f19bc`) — **`plan-drafter`-authored** (ADR-013 D1) → Code R2-reviewed → committed. Scope: the `services/engine/procedures/spec.py` engine edit (typed `facet` per the delta) + migrate the 4 verticals' comment-facets → the real field + load/validation tests — the **first deliberate `spec.py` edit since procurement's zero-engine-edit (CQ-1)**, ADR-sanctioned. **Schema only** (engine still ignores `facet` at run time); **implements nothing on commit**; **3 OPEN SDs** (note-migration / comment-removal / PR-granularity). Gate = offline suite (1651 baseline + new tests) + `mypy --strict`; no live MS-S1. NEXT = Cray merges #429 + adjudicates SD-1/2/3 → execute PLAN-0038 → Stage 3 generator + review UI | `0b56954` (#428) / `b2f19bc` (#429) / `docs/adr/0016-governed-procedure-engine.md` + `docs/plans/0038-*.md` |
| 2026-06-25 | **PLAN-0037 / Stage 2 PREP COMPLETE — 5-facet retrofit (→N=4) + procedure-archetype catalog SHIPPED + PLAN archived (session 77, #424/#425/#426)** — Stage 2 PREP for the generative-procedures target. PLAN-0037 was **`plan-drafter`-authored** (the in-harness subagent, ADR-013 D1 phased authority) → Code R2-reviewed + committed (#424, ADR-009 D2; separation intact); Cray chose the formal-PLAN route (ทาง 1). **Step A (#425, content `31ded05`):** retrofit the SD-4 5-facet annotation (`input · decision-condition · llm-assist · output · governance`) as **YAML comment blocks** onto `energy`/`supply_chain`/`aquaculture` `procedures.yaml` → consistent **N=4** instrumentation (Rule-of-Three substrate). **Provably inert:** `services/engine/procedures/spec.py` `Step` declares `extra="forbid"` (so `facet:` can only be a comment) + the loader uses `YAML(typ="safe")` (discards comments) → Step objects byte-identical, static-JS demos untouched; gate parse-clean all 4 verticals (steps unchanged 3/3/5/10), **66 insertions all-comment / 0 deletion**, **full offline suite 1651 passed/22 skipped** (baseline), no live MS-S1 (§8). Captured the env-vs-in-file judge-band split (energy/supply_chain via `OCT_RECOMMEND_THRESHOLD`; aquaculture/procurement in-file) as the Step-C input. **Step B (#426, content `c3b477a`):** the procedure-archetype catalog at `docs/conventions/procedure-archetypes.md` (AT-1 `anomaly→action`, AT-1b `watch+summary`, AT-2 `request→approve→fulfill`, AT-3 `monitor→reorder`) — the canonical reference the Step-C ADR + Stage-3 generator cite. SD-1=one PR for the 3 verticals / SD-2=Step B follow-on PR / SD-3=catalog home `docs/conventions/` (all Cray-resolved). **`loop-dispatcher` (Cray s77) = keep-disabled + guard** (over fix-hook / delete); the Stop-hook root-fix (scheduled-task auto-continue exemption) is deferred + is the precondition for any re-enable. **Out of scope (forward):** Step C (ADR-016 first-class `facet:` field = a separate **Cowork-drafted ADR**, G2-gated) + Stage 3 (the procedure generator, Rule-of-Three-deferred). PLAN-0037 `git mv` → `done/` | `f029913` (#424/#425/#426) / `verticals/{energy,supply_chain,aquaculture}/procedures.yaml` + `docs/conventions/procedure-archetypes.md` + `docs/plans/done/0037-*.md` |
| 2026-06-24 | **PLAN-0036 (Fastenal procurement vertical, Stage 1) drafted + merged DRAFT; Cray adjudicated SD-1…SD-5 = confirm-all (session 75, #412)** — Cowork-drafted (ADR-009 D1) from Code's s75 dispatch, Code R2-reviewed + committed (D2), merged as `Draft` (`7a7c036`). Stage 1 = hand-author vero-lite's **4th vertical (Procurement)** instantiated on automotive/auto-parts in the **EEC** (the **Fastenal Thailand** pitch target), as a **PLAN-only, no-ADR pure-config plugin** on the shipped ADR-016 engine with **zero `services/` core edit** (CQ-1 confirmed, ADR-0023). Hero = asset-failure → governed emergency sourcing; calm-path = low-stock reorder. **Cray confirmed all five SDs as-recommended** (2026-06-24). Load-bearing **SD-4 catch:** `services/engine/procedures/spec.py` `Step = ConfigDict(extra="forbid")` → Stage-1 facet annotations are **comment-only** (a first-class `facet` field = a Stage-2 ADR-016 amendment). The **proving ground** for the ultimate 3-phase generative-procedure platform (generate/run/monitor); per Rule-of-Three builds **no generic generator** (hand-author → extract schema Stage 2 → generator Stage 3). **Implements nothing on commit** (every AC `[impl]`). NEXT = a new session flips Draft → Ready for execution then executes Stage 1 | `7a7c036` (#412) / `docs/plans/0036-fastenal-procurement-vertical.md` |
| 2026-06-23 | **PLAN-0035 Phase 2 (advisory local-LLM-judge, ADR-0022 member (b)) SHIPPED + PLAN-0035 fully COMPLETE (session 74, #407)** — an **advisory** local-LLM-judge layered on the Phase-1 deterministic floor (`services/engine/action_verification.py`): semantically cross-checks *does the proposal prose express the corrective action the structured handler names?*, adding confidence + agreement + a `"hybrid"` `verification_mode` trace (`judge_action_expression()` + `augment_with_advisory_judge()` + `ActionJudgeVerdict`/`JudgeResult` + `VERIFICATION_MODE_HYBRID`; the Phase-1 floor `verify_action_expression` unchanged). The 4 locked constraints (ADR-0022 amendment A2) all honored: ① offline gate — tests fake the judge, the live judge gated behind a new `verification_judge_enabled` setting (**default off** — live = host-state, CLAUDE.md §8); ② advisory — the judge NEVER overrides the surfaced action (the deterministic floor decides), pinned by `test_judge_disagreement_never_overrides_the_floor_action`; ③ deterministic compare — floor(D) vs judge(L) agreement in code, no 3rd LLM; ④ disclosed degradation — judge unavailable → `verification_mode "(a)-only"` in the trace, reusing the IN-4 / `OllamaUnreachableError` seam + `notify_llm_unreachable` (no new fail-safe, IN-4 not regressed). `augment_with_advisory_judge` never raises into `recommend()` (only the floor propagates to the IN-4 fail-safe, AC-7). **SD-3 / Step 11 — the first-class `verification` envelope field DEFERRED (trace-only)**, mirroring member (a)'s deferred `EntityRef.resolution` field; ADR-007 D2 envelope untouched (Code's rec → proceed-to-PR). Gate: ruff + ruff-format clean, `mypy --strict` clean (`services/`), **full suite 1639 passed/22 skipped** (was 1629; +10 offline judge-faked tests); AC-5 wrong-handler-not-rescued + D-6 boundary hold. Routing: impl (`feat/*` + PR) gated on the ADR-0022 amendment (RATIFIED #405) — NOT G2-gated; Code built + self-merged (#407, Cray-authorized). **PLAN-0035 flipped Draft → Complete + `git mv` to `done/` (`805f5d2`)** — both phases of member (b) verify+reshape now shipped, the Group-A A1 arc closed end-to-end | `5c7c175` (#407) + `805f5d2` / `services/engine/action_verification.py` + `docs/plans/done/0035-governed-action-verify-reshape-build.md` |
| 2026-06-23 | **PLAN-0035 (A1 = ADR-0022 member (b) verify+reshape) advanced END-TO-END — SD-1 = (c) Hybrid phased; Phase 1 floor SHIPPED; (c) governance + amendment RATIFIED (session 73 cont., #403/#404/#405)** — **SD-1 adjudicated by Cray = (c) Hybrid, phased** (deterministic floor + advisory local-LLM-judge; constraint ② advisory-only, ③ deterministic compare), superseding the Cowork (a)-lean. **Phase 1 = deterministic verify+reshape floor SHIPPED** (#403, feat `1c34125`): new `services/engine/action_verification.py` at the `recommender._compose_llm_record` seam, reshaping the 5 §B-3 "assessment-prose" cases (`aqua-007/014/028/h03/h06`); the 2 genuine wrong-action cases (`aqua-017/h05`) stay wrong (AC-5 — wrong handler NOT rescued); D-6 offline guard held; **1629 passed/22 skipped**, ruff + mypy --strict clean, offline. **The (c) governance landed** (#404): an **ADR-0022 amendment** (member (b) verify = hybrid; 7 constraints incl. the local-LLM pin + D-6; scope = member-(b) mechanism only, F1/F2/F3 + D3-α untouched) + a **PLAN-0035 revision** (SD-1…SD-5 stamped, Goal/Steps restructured Phase 1/Phase 2, path-fix `structured.py`→`llm/structured.py`). **The amendment was RATIFIED** (#405, `3625ea4`; SD-A1 = (i) inline, Cray-selected). **Phase 2 (advisory local-LLM-judge, Steps 8–12) now UNBLOCKED + NEXT** — NOT marked done. Operational detour (no artifact): the G1/G2 classifier backend is local Ollama (MS-S1 `gpt-oss:20b`) since 2026-06-12, G1 is always-pause for Code (warm-confirmed → Accepted-ADR edits route to Cowork), and a keep-alive cron (every 3h) was installed to keep `gpt-oss:20b` warm | `3625ea4` (#405) / `1c34125` (#403) / `47e154b`+`17f5d6e` (#404) / `services/engine/action_verification.py` + `docs/adr/0022-*.md` + `docs/plans/0035-*.md` |
| 2026-06-22 | **PLAN-0035 (Group-A A1 = ADR-0022 member (b) verify+reshape build) CREATED + merged DRAFT (session 73)** — Cowork-drafted (ADR-009 D1) via the s72 `0223` dispatch (the proven Cowork-dispatch route, NOT the now-unblocked in-harness `plan-drafter` — Cray's call); Code independent-reviewed (faithful to LOCKED facts; spot-checked the `recommender.py:202` `_compose_llm_record` seam — Cowork had caught the post-member-(a) #365 line-number shift and re-verified) + committed `4eb2539` (#401, Cray-merged, D2). A **build PLAN, not a new ADR** (ADR-0022 Accepted, D3-α houses member (b); mirrors PLAN-0030 = member (a)). Scope = recommend-time LLM-path verify+reshape for the **5 §B-3 "assessment-prose" cases** (`aqua-007/014/028/h03/h06`, correct `suggested_handler`, prose omits the verb); the **2 genuine wrong-action cases** (`aqua-017/h05`) stay wrong (AC-5 anti-regression). **Implements nothing on commit** (every AC `[impl]`); **5 SDs surfaced** for Cray (SD-1 verify mechanism … SD-5 moat-framing guard) — SD-1 is the load-bearing gate. A1 TODO updated (PLAN drafted+merged Draft; NOT done) | `4eb2539` (#401) / `docs/plans/0035-*.md` |
| 2026-06-22 | **PLAN-0034 (G2 drafting-friction root-fix) FULLY COMPLETE (session 72)** — Step-5 prong-2 scope annotation Cowork-drafted (ADR-009 D1, K-1/K-2 scratchpad; Code declined the Stop-hook Code-direct override, applied byte-identical edits) + merged #399 (`0f56d24`/`5daa0e0`) into `.claude/autonomy-triggers.md`; PLAN flipped Ready→Complete + `git mv` to `done/` (`72f0deb`). SD-3 = (a) PLAN-only, **no ADR amendment**. Optional live gold re-score (prong-1 behavioral proof) remains Cray-gated host-state — **NOT** an acceptance gate (offline gate, green at #397, is the sole acceptance condition). Group-A: A2 ✅ → G2 ✅ → A1 next | `0f56d24`/`5daa0e0` (#399) + `72f0deb` / `.claude/autonomy-triggers.md` + `docs/plans/done/0034-*.md` |
| 2026-06-21 | **PLAN-0034 (G2 drafting-friction root-fix) RATIFIED + core-IMPLEMENTED (#396/#397, session 71)** — Cray ratified all four SDs = option (a) (#396 `5705b8a`, merge `3dcecaa`). SD-1 (prong-2 mechanism) gated on a Code Step-3 spike run offline this session: it confirmed (Q1) project PreToolUse hooks DO fire inside a subagent context (deadlock real, prong 2 needed) and (Q2) the payload carries BOTH `agent_id` and `agent_type` reliably (docs omit them; the live harness provides them — vindicates `done/0009` §1) → SD-1 = (a) exempt `agent_type=="plan-drafter"` reusing G5's `_is_subagent_call`/`agent_id` (SUPERSEDED the pre-spike (c) lean); SD-2 = (a) hybrid guards; SD-3 = (a) PLAN-only + `.claude/autonomy-triggers.md` annotation (no ADR amendment); SD-4 = (a) keep G5/PR-review/"only Code commits" untouched. Cowork folded ratify+spike into the PLAN (D1), Code R2-reviewed + committed (D2) → PLAN Status: Ready for execution. **Impl (#397 `c69b6e2`, merge `9092db5`):** offline deterministic core; self-modification of the autonomy hooks Cray-approved per-diff, opened as a PR + NOT self-merged (Cray merged — the SD-4 checkpoint). Prong 2: `pretooluse_classifier_dispatch.py` exempts the `plan-drafter` subagent (short-circuit before `_classify()`; main-agent writes have no `agent_id` so G2 preserved; `# noqa: C901` justified). Prong 1: three DISPATCH over-fire guards in `_sonnet_classifier._build_system_prompt` (non-`docs/(adr\|plans)/NNNN` / already-routed / existing-lifecycle-flip; genuine `Status: Accepted` ADR mutation still pauses — G1 unchanged) + 6 `expected: pause` gold negatives. Gates green: 137 targeted + 730 handoffs/benchmark pass, ruff/ruff-format/mypy --strict clean, gold parses. Offline-only; live gold re-score (prong-1 behavioral proof) stays Cray-gated host-state — NOT run. **PLAN-0034 stays Ready for execution (NOT Complete, NOT `done/`);** tails = Cowork `.claude/autonomy-triggers.md` annotation (Step 5) + optional live re-score | `c69b6e2`/`9092db5` (#396/#397) / `pretooluse_classifier_dispatch.py` + `.claude/hooks/_sonnet_classifier.py` + `benchmarks/stop_classifier/gold.yaml` + `docs/plans/0034-*.md` |

## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13 (ratified `4d1347b`, #302; committed Proposed `e25281d`, #297 + instruction `e387a63`, #298 + R1 errata `655344d`, #300) — guarded trial under observation (parallel to ADR-012). A specialist Cowork project role-plays a Thai operator and emits a "partner profile package" to rehearse the intake+PDPA pipeline before a real partner; venue OUTSIDE the governance tiers (no commits / no repo mount / enters via Code receive). Three BINDING anti-circularity rules R1/R2/R3 (R3 SYNTHETIC provenance → never trips PLAN-0005 §8.1 / ADR-011 first-real-data trigger). All four venue SDs + dispatch-SD-1 ratified per Cowork rec (SD-1 N=3; SD-2 one-project-per-business-type; SD-3 size/region/maturity enums w/ energy·mid·th-regional·mixed-legacy default; SD-4 "what we refused to share" now required). D4 guarded-trial mirrors ADR-012 D5; regression triggers R-PS1..R-PS4 are the exit criteria; run 1 = energy operator (ADR-005 primary). **Now live-able: Cray launches run-1 (paste the R1-clean seed NOT the one-pager); ADR-011 audit framework stays gated on a partner conversation — the synthetic run INFORMS but never TRIGGERS it.**
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **Procurement vertical — GO + IN MOTION: PLAN-0036 (Fastenal, Stage 1) drafted + merged Draft (#412, `7a7c036`):** **GO** — Cray greenlit the 4th vertical (Procurement) and **PLAN-0036 (Fastenal procurement vertical, Stage 1) is drafted + merged Draft** (#412, head_commit `7a7c036`; Cowork-D1 + Code-R2 + committed D2, session 75). **Cray adjudicated SD-1…SD-5 = confirm-all** (2026-06-24, as-recommended). **Demo target = Fastenal Thailand** — automotive/auto-parts in the EEC; **hero** = asset-failure → governed emergency sourcing, **calm-path** = low-stock reorder. Stage 1 = a **PLAN-only, no-ADR pure-config plugin** on the shipped ADR-016 engine, **zero `services/` core edit** (CQ-1 confirmed, ADR-0023); the **SD-4 catch** = `services/engine/procedures/spec.py` `Step = ConfigDict(extra="forbid")` → Stage-1 facet annotations are **comment-only** (a first-class `facet` field = a Stage-2 ADR-016 amendment). It is the **proving ground** for the ultimate **3-phase generative-procedure platform** (generate / run / monitor); per Rule-of-Three it builds **no generic generator** (hand-author → extract schema Stage 2 → generator Stage 3). **NEXT = a new session flips PLAN-0036 Draft → Ready for execution (SDs confirm-all) then executes Stage 1.** *Supporting de-risk dossier (Cowork, session 72, 2026-06-22, `docs/research/private/`)* — **(1)** `2026-06-22-procurement-spec-expressiveness-probe.md` (procurement is **config-layer**, **0 new core amendments**; only engine pulls are the already-deferred ADR-016 Phase 2 / Phase 4+ items); **(2)** `2026-06-22-procurement-gtm-commercial-validation.md` (wedge = ops-triggered asset-aware procurement; econ buyer = CFO/Controller, champion = ops/procurement mgr; metric = **cycle-time**; ~$40K–150K/yr; 6-wk paid pilot); **(3)** `2026-06-22-procurement-asset-aware-incumbent-scan.md` (de-risk #1 — EAM/CMMS = nearest incumbent on the *trigger* only; white space = the **triple intersection** asset-trigger × governed sourcing × cross-vertical); **(4)** `2026-06-22-ai-sourcing-competitor-teardown.md` (de-risk #2 — Verusen/Keelvar/Fairmarkit/Arkestro/… triple intersection unoccupied; defensibility on **axis (a) asset-event trigger**; watchlist: **Verusen #1**, Fairmarkit, Coupa); **(5)** `2026-06-22-platform-incumbent-deepdive.md` (de-risk #3 — Palantir/Maximo/GE Vernova/SAP = capability-yes / product-no; moat = **packaging × ICP × price** = the **"Palantir-lite"** thesis, ADR-005, **governed ≠ generated**). **Pitch:** lead with asset-ontology-triggered governed sourcing + the native ontology (ADR-008) + engine (ADR-016) combination — **NOT** "governed"/"cross-vertical" (now commoditized claims).
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten (full table: PLAN-0005 §8.1): rule-based recommender → **ADR-010 ACCEPTED (2026-05-22) → PLAN-0006 next** (LLM reasoning hook); minimal approval gate → **ADR-011+** (audit framework — trigger: first design-partner data / PDPA review); no mapping layer → **dbt/SQLMesh** (trigger: first non-synthetic source); hand-authored ORM → **"ORM emitter"** Rule-of-Three candidate (trigger: 3rd vertical / DDL↔ORM parity-test drift); base Postgres only → **PLAN-002** (pgvector/AGE — trigger: semantic + graph features); explicit registry → **ADR-006 D3 L2** (trigger: vertical #2/#3 or `new-vertical` generator). *(per Cray note 2026-05-21)*
- [ ] **Demo card UX — "trust shape", NO operator confidence badge (s74 design, Cray-approved).** For the next demo round's operator recommendation card: show **what / grounded-why / approve gate** + a **"show full reasoning trace" toggle** that reveals the engine-view (where the floor-vs-judge agreement lives, labelled *audit/QA — not the operator*; reuses the scene-6 why-toggle pattern). **No operator-facing confidence badge** — the floor-vs-judge `confidence_signal` (PLAN-0035 Phase 2) is an **engine-internal QA/audit signal kept trace-only (SD-3 option A)**; surfacing it as a badge mis-reads as "the action might be wrong" (it is **not** — member (b) is advisory, never changes the action). The **(B) first-class `verification` envelope field is NOT needed for the operator UI** — reconsider **only** if a future internal audit/QA dashboard wants confidence as a first-class field (trace stays sufficient otherwise). Settled via a show_widget design review (s74; Cray: "ตรงใจ ตอบโจทย์"). The reframe: users want *what was decided · is it right · why* — answered by the action + grounding (real entity, allow-listed handler, deterministic detection, human approve) + the reasoning trace, **not** a self-reported confidence number. *(Trigger: the next demo / UI round; pairs with any (B) reconsideration.)*
- [ ] **PLAN-004 Phase C — OPTIONAL POLISH (forward-declared; "may never land"):** HTML/markdown handoff dashboard under `docs/` + references-graph (mermaid dispatch chains) + `render_transcript.py` unified session export (PLAN-0004 §"Phase C"). *(Phase A + B both COMPLETE — session 35; the prior TODO's validator **warning-swallow bug was FIXED #312**, s58. Minor never-formally-scoped sub-ideas — README/`_rename-map` walk-exclusion, Cat G `references_*` autofix, OQ-2 effective-vs-authored `status:` dashboard flag — fold in only if Phase C lands. Reconciled 2026-06-16 s65 audit.)*
- [x] **A1 — verify+reshape governance demo (B-γ moat successor) — DONE (s74).** The heaviest moat-proof: prove the moat IS governance — verify an LLM step's output for semantic consistency + reshape to the next step's contract (what arm (c) structurally lacks; ADR-016 area; the B-3 REPORT forward-points to it). **Scope together with the Phase-2 governed-entity-resolution ADR** — one ADR-016-area construct, not two overlapping ADRs. **UPDATE (s71):** that consolidation is DONE — **ADR-0022 (Accepted) D3-α already houses verify+reshape as member (b)**, so A1 = a PLAN to build member (b) (like PLAN-0030 built member (a)), at most an ADR-0022 amendment if a member-(b) design fork surfaces — NOT a new ADR. A2's residual decomposition (s71) shows the concrete A1 target: the 5 correct-action "assessment-prose" cases (verify the proposal states the action, reshape from the resolved handler). Sequenced AFTER the G2 root-fix (Cray, s71). **UPDATE (s73, cont.):** advanced END-TO-END — **SD-1 adjudicated = (c) Hybrid, phased** (Cray); **Phase 1 floor SHIPPED** (#403 `1c34125` — `services/engine/action_verification.py` at the `_compose_llm_record` seam; 1629 passed/22 skipped; AC-5 wrong-handler-not-rescued + D-6 held); the **(c) hybrid governance RATIFIED** (#404 ADR-0022 amendment [member (b) = hybrid, 7 constraints, local-LLM pin, scope = mechanism-only] + PLAN-0035 revision [Phase 1/2 restructure]; #405 `3625ea4` amendment ratified, SD-A1 = (i) inline). **UPDATE (s74) — DONE:** **Phase 2 (the advisory local-LLM-judge, Steps 8–12) SHIPPED** (#407, feat `5c7c175`) on the Phase-1 floor — the advisory judge (never overrides the surfaced action, ②) + deterministic agreement (③) + `verification_mode` degradation disclosure reusing the IN-4 / OllamaUnreachable path (④), gated behind `verification_judge_enabled` default-off (①); tests fake the judge (1639 passed/22 skipped). **PLAN-0035 flipped Draft → Complete + `git mv` to `done/` (`805f5d2`) — both phases of member (b) verify+reshape now shipped, the A1 arc closed end-to-end.** *(folded from §7 handoff, s67; PLAN drafted+merged s73; Phase 1 shipped + (c) ratified s73; Phase 2 shipped + A1 closed s74)*
- [x] **A2 — equal-rubric arm-(a) re-grade — DONE (s71, #392 + `2463229`).** Committed reproducible harness `benchmarks/procedure_comparison/regrade_arm_a.py` reproduces the full §B-3 A2 table (hardened 24→33/39→39/40→40; nudged 40/40/40), all-120 sanity assert green (every recomputed full-key grade matches the stored `proposal_correct`). §B-3 enriched with the handler-verified residual decomposition: the 7 hardened-reduced aquaculture misses = **5 correct-action** (`start_emergency_aerator`, prose framed as an "assessment" omitting the verb → the prose `action_keywords` check misses it) + **2 genuine wrong-action** (`increase_water_exchange`) → true wrong-action **2/40**. Finding: arm (a) ties-or-exceeds arm (c) once the rubric + prompt confounds are removed; the 5 prose-omission cases are the A1 verify+reshape target. *(folded from §7 handoff, s67; closed s71)*
- [ ] **ORM-emitter per-vertical layout (B1-DP-1 follow-up; Cray-deferred s67).** B1 (PLAN-0031, #370) ships the ORM emitter writing energy's ORM to the **committed** `services/db/models.py` (via `code_generator._ORM_COMMITTED_DEST`) — the gitignored `verticals/<ns>/generated/` cannot host a runtime dependency. When a **2nd vertical needs its own ORM** (the Rule-of-Three trigger), decide the per-vertical layout: extend `_ORM_COMMITTED_DEST` to per-vertical committed modules **vs** un-ignore a per-vertical `generated/orm.py` (gitignore negation) + re-export. Premature to design now (one ORM today). *(Cray-deferred 2026-06-18)*
- [x] **G2 drafting-friction root-fix — PLAN-0034 FULLY COMPLETE — DONE (s72).** Step-5 prong-2 scope annotation merged (#399, `.claude/autonomy-triggers.md`; annotation `5daa0e0` / merge `0f56d24`) — Cowork-drafted (ADR-009 D1, K-1/K-2; Code declined the Stop-hook Code-direct override, applied byte-identical edits, committed). PLAN-0034 flipped **Ready for execution → Complete** + `git mv docs/plans/0034-*.md → docs/plans/done/` (`72f0deb`). SD-3 = (a) PLAN-only (no ADR amendment). The only residual is the **optional, non-blocking** Cray-gated live gold re-score (prong-1 behavioral proof, host-state — **NOT** an acceptance gate; the offline gate, green at #397, is the sole acceptance condition). Parked s63; hit AGAIN s66 + s67 + s68; DRAFTED s71 (#394); ratified all four SDs = (a) + core-implemented s71 (#396/#397). *(folded from §7 handoff, s67; s68 instance + classifier prong; drafted s71; ratified+implemented s71; closed s72)*
- [x] **Promote the "proceed vs Cowork-dispatch-file" routing standard — DONE (s68).** Promoted into **CLAUDE.md §6** ("Routing: proceed vs Cowork-dispatch", #376 / commit `1963282`) — **home changed from the tentative `docs/conventions/` to CLAUDE.md per Cray's 2026-06-19 decision** (strong binding). Cowork-drafted (ADR-009 D1), Code R2-reviewed + committed (D2). Private Auto-Memory slimmed to a pointer (SD-C); parked G2 root-fix preserved separately (line above, SD-D). *(folded from §7 handoff, s67; closed s68)*
- [ ] **ADR-NN (TBD, ≥ ADR-014) + PLAN-002** — Custom Postgres image with extensions (ADR-011 earmarked for the audit framework, ADR-012 taken, ADR-013 taken by autonomy axis relocation; floor bumped from ≥0013 to ≥0014 on 2026-05-23 per ADR-013 T6)
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (low priority)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)

## Next Steps

1. **PLAN-0005 §8.1 revisit register** — remaining deferred-foundational simplifications at their batch boundaries (audit framework → ADR-011+, mapping layer, ORM emitter, base-Postgres → PLAN-002 (≥ADR-014), registry discovery).
2. **Partner-trial readiness gaps** — `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` awaits a dedicated Cray discussion.
3. **Deferred (backlog)** — PLAN-004 Phase C only (optional polish: handoff dashboard / references-graph / unified export — Phase B complete s35, warning-swallow fixed #312); PLAN-002 custom Postgres image (≥ADR-014).
4. **Ongoing** — Continue exercising the file-based handoff mechanism (Chat ↔ Code ↔ Cowork) across batches.

## Update Workflow

This file is updated when:
- A commit changes project state significantly
- A new ADR/PLAN is minted or completed
- Active priorities shift
- A batch closes (sync `last_updated` + `current_batch` + `head_commit` + `recent_commits` frontmatter)
- A session closes (sync all frontmatter fields; archive batch history if needed)

**Update mechanism (locked per STATUS staleness batch 2026-05-18, Hybrid A+B short-term, C long-term):**

- **Per closeout (Option A + Q1(b) discipline):** Closeout drafter includes the line "STATUS.md updated: yes / no / N/A" in their closeout. If `yes`, the closeout's commit batch should include a dedicated `docs(status): …` housekeeping commit (Q3(b/c) pattern) bumping at minimum the `last_updated` and `head_commit` frontmatter fields.
- **Per batch boundary (Option B full body):** Full body refresh (Current Focus + Recent Decisions + Active TODOs + Next Steps) at batch close, alongside the frontmatter bump.
- **Per session boundary:** Full body + frontmatter sync; consider archive of prior session's batch history.
- **Future (Option C, PLAN-004 Phase A):** Validator will flag stale STATUS.md by comparing **frontmatter `last_updated` field** against newest closeout's `created` timestamp (NOT file mtime — mtime is defeated by side-effect commits, e.g. `c85a595` 2026-05-16 normalization sweep that touched STATUS.md body without bumping `last_updated`).

**Q4 `head_commit` semantics (codified 2026-05-18, locked Cray ratification of midflight `2026-05-18-1049` §4 + closeout `2026-05-18-1202` §6.2):**

- `head_commit` = short SHA of the newest **substantive** commit on
  `origin/main` that STATUS.md content reflects.
- **Excluded from `head_commit`:** `docs(status): …` housekeeping
  commits. These commits encode no new repo state — they ARE the
  STATUS.md freshness marker. Including them in `head_commit` creates
  a self-defeat where every housekeeping commit makes STATUS.md appear
  "fresh" to Q4 detection regardless of substantive backlog.
- **Substantive (included in `head_commit`):** everything else —
  `docs(lessons):`, `docs(adr):`, `docs(runbook):`, `feat:`, `fix:`,
  `chore:` (when changing meaningful state), `refactor:`, `test:`, etc.
  Any commit type that changes durable repo content updates
  `head_commit` at the next STATUS.md edit.
- **Reader recipe (returning after a pause):**

  ```bash
  # Newest substantive commit on origin/main (the value head_commit should hold)
  git log -1 --format=%h --invert-grep --grep='^docs(status):' origin/main

  # Compare to STATUS.md head_commit field
  grep -E '^head_commit:' docs/STATUS.md
  ```

  If the two differ → STATUS.md content is stale relative to substantive
  repo state. If they match → STATUS.md is fresh.

- **Writer rule (at each STATUS.md update):** Set `head_commit` to the
  output of `git log -1 --format=%h --invert-grep --grep='^docs(status):' origin/main`
  *after* the substantive commits of the current batch land but *before*
  any `docs(status):` housekeeping commit (or, if the STATUS.md edit
  itself is in a substantive commit like `docs(lessons):`, set
  `head_commit` to that substantive commit's own SHA — which becomes
  knowable only post-commit, so the writer typically updates
  `head_commit` to the *most-recent prior substantive commit* and lets
  the next batch's first edit catch up).
- **Two failure modes this rule closes:**
  1. **mtime trap** (closeout `2026-05-18-1202` §2): side-effect commits
     that touch STATUS.md body without bumping `last_updated` (e.g.
     `c85a595` 2026-05-16 normalization sweep) leave the file mtime-fresh
     but semantically stale. A SHA in `head_commit` cannot drift this way.
  2. **Housekeeping self-defeat** (closeout `2026-05-18-1202` §6.2 +
     midflight `2026-05-18-1049` §4): if `head_commit` = own SHA, every
     `docs(status):` commit makes Q4 say "fresh" regardless of
     substantive backlog. Excluding `^docs(status):` from the comparison
     baseline closes this loophole.

Manually edited until Option C lands.
