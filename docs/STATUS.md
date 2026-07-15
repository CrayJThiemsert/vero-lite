---
last_updated: 2026-07-16T00:02:50+07:00
session: 135
current_batch: "s135 — PLAN-0077 transform-grammar COMPLETE (5 PRs #754→#758) + PLAN-0078 (transform seed-migration) FILED Proposed (#760, all 8 SDs ratified: SD-1=(B) full incl. marquee stamps, SD-6 two-tier parity, SD-7 slim executor, SD-8 one-home amount). Build = next session."
current_actor: code
blocked_on: "Nothing blocking. main=7cbe08a; 0 open PRs; PLAN-0077 COMPLETE; PLAN-0078 filed Proposed (build not started). Loop-dispatcher DISABLED; MS-S1 idle; dev Postgres UP."
next_action: "Build PLAN-0078 Phase 1 PR-1 — procurement intake migration (criticality-copy + unit default + compliance map → declared transform; candidate_quotes nest stays seed-side, L-3 partial), oracle-first: land the SD-4 parity harness against the CURRENT seed BEFORE the flip. Then PR-2 supply_chain intake; Phase 2 (stamps, SD-1=(B)) after."
head_commit: 7cbe08a
recent_commits: [7cbe08a, b536c0e, a3c86ca, 56fc08b, 43d7e4e, ece270a, 95efcb9, 8808902, 81a8a0f, d94a10d]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 135 (close-out), 2026-07-15 (head_commit `fac77c7` → `ece270a`) —
> PLAN-0077 "transform-grammar build" COMPLETE across 5 PRs (renders ADR-0031
> D3 row-1 + ADR-016 Q4 OQ-3; NO new ADR; the s134 PAUSE never reconciled
> STATUS, so this fold spans the whole arc).** **#754** (`3e6ee4d`, s134) —
> PLAN-0077 Proposed (`plan-drafter` → Code R2 → Cray SD-1 = A-refined). **#755
> Phase A** (`e93e9d0`, s134) — `StepKind.TRANSFORM` + a typed declarative
> grammar (an anti-eval `derive` expression tree: arbitrary eval UNREPRESENTABLE
> by construction) + H-governance + a load gate; 41 tests. **#756 Phase B**
> (`d94a10d`) — `services/engine/procedures/transform_step.py`: `plan_transform`
> (pure/total compile-or-refuse, shares `validate_transform_spec` with the load
> gate, L-6) + a frozen, IO/LLM-free, exact-Decimal, fail-closed (div /
> non-finite / missing-input per SD-7) `TransformStepExecutor` with
> inclusive-ceiling banding, JSONB-safe output + per-op provenance; 40 tests.
> **#757 Phase C** (`8808902`) — fixtures end-to-end via `run_procedure` /
> `run_procedure_persisted` + the marquee value-parity oracle: a declared
> transform reproduces `derive_excursion_severity`'s severity+ratio and
> `scored_rule`'s `amount = unit_price × qty` value-identically WITHOUT touching
> the hardened stamp path (SD-1); 12 tests. **#758 L-8 landing** (`ece270a`,
> HEAD) — ADR-0031 D3 row-1 "Steps/StepKinds" → "Shipped — see PLAN-0077"
> (`plan-drafter` authored the Accepted-body edit → Code R2 + committed);
> PLAN-0077 `git mv`→`docs/plans/done/0077-*.md` in this same close-out PR.
> **Honest residual (not overclaimed):** the GRAMMAR shipped (declared ✔,
> load-gated ✔, execution-bound ✔ for the shipped op-set), but the two
> verticals' seeds stay **execution-bound ✖** for their derived halves; the
> marquee amount/severity stamps stay code-side by ratified choice (SD-1);
> `derivation_hash` remains in service; **F-PIN stays OPEN**. Flipping those is
> the separate **SD-4 parity-guarded seed-migration PLAN** (not yet filed),
> which also owns the F-PIN fold-in tracked by **PLAN-0076 Step T2**; nothing
> here retires `derivation_hash` or closes F-PIN. **draft≠review≠verify:** Phase
> A/B/C = Code authored + verified (93 AC tests); PLAN-0077 + the L-8 edit =
> `plan-drafter` → Code R2 + committed; this reconcile = `status-scribe` → Code
> R2. Post-merge: main=`ece270a`; 0 open PRs; loop-dispatcher DISABLED; MS-S1
> idle; dev Postgres UP. Commits: `3e6ee4d` (#754) → `e93e9d0` (#755 A) →
> `d94a10d` (#756 B) → `8808902` (#757 C) → `ece270a` (#758 landing, HEAD).

> **Session 133 (close-out), 2026-07-15 (head_commit `76f42cc` → `fac77c7`) —
> PLAN-0075 COMPLETE (all 13 ACs) + CLOSED → `done/`; AC-13 derivation
> provenance shipped (#751, `feat`); PLAN-0076 filed as the standing follow-on
> TRACKER (#752).** With the core (AC-1..AC-12, #749) landed earlier this
> session, **AC-13** folds supply_chain's severity-derivation constants
> (`_DOSE_LADDER` + `_TOP_SEVERITY`) into the run governance pin: a per-vertical
> `registry.derivation_hash` hook threads an optional `derivation_hash` param
> through the 5 pin call sites, so the persisted pin records WHICH derivation
> governed a run (mid-flight tamper-evidence + which-derivation-governed-this-run).
> This is **PROVENANCE-ONLY** — it does **NOT** guarantee a fresh run's
> derivation, so **F-PIN stays OPEN** (SD-5's residual risk, unchanged); 9
> offline tests. **PLAN-0075 is now COMPLETE — all 13 ACs — and Code
> `git mv`→`docs/plans/done/0075-*.md`.** **The two deferrals no longer live on
> PLAN-0075:** they are homed by **PLAN-0076** (`Status: Tracking`, #752) — a
> Cray-ratified (s133 4-specialist SD-1 panel) STANDING tracker for the F-PIN
> remainder + the ADR-0031 D3 gate-plugin seam (F-FACTORY). PLAN-0076 ships an
> **AC-6 presence guard-test** (`test_at2_followon_tracking_guard.py`) that
> turns the build RED on a premature archive-to-`done/` or a pruned STATUS
> pointer — the panel's "location≠tripwire; failing tests are the real
> anti-rot" finding (guards against the ADR-0031 OQ-4 deferral-rot precedent).
> **Merge sequence:** #752 merged first (`4a682ab`), then the AC-13 branch was
> updated onto it (`e726a00` = routine merge-main) and #751 merged (`fac77c7`,
> HEAD); both gate-verified. **draft≠review≠verify:** AC-13 = Code authored +
> verified (9 offline tests); PLAN-0076 = `plan-drafter` authored → Code R2 →
> Cray ratified the 4-specialist panel path; this STATUS reconcile =
> `status-scribe` authored → Code R2. Post-merge: main=`fac77c7`; 0 open PRs;
> PLAN-0075 COMPLETE → `done/`; the two follow-ons trigger-gated under PLAN-0076
> (not scheduled); loop-dispatcher DISABLED; MS-S1 idle. Commits: `0520fb2`
> (AC-13 feat) → `4a682ab` (#752 merge) → `fac77c7` (HEAD, #751 merge).

> **Session 133, 2026-07-15 (head_commit `098b0d9` → `76f42cc`) — PLAN-0075
> CORE: AT-2 AUTHORITY ENFORCEMENT AT THE RUN GATE shipped (12 of 13 ACs,
> #749, `feat`); closes the s131-surfaced F1 exploit (`task_053edc92`).** The
> AT-2 authority ladder (`doa_tier` / `severity_tier`) RESOLVED + AUDITED which
> tier should approve, but NO run path ENFORCED that the acting approver HELD
> that tier role — so in the shipped procurement hero a junior (`appr-buyer`,
> ฿0-50k authority) could resolve a ฿288k / ฿2M gate, and the persisted audit
> even NAMED an authority who never acted. **The fix:** a pure
> `tier_authority.check_tier_authority` now runs at `resolve_gated_step` AFTER
> the SoD check (ADDITIVE — SoD stays primary) and BLOCKS unless the approver
> holds the ladder-resolved tier role of EVERY persisted verdict — verified at
> the LIVE DB gate (junior refused; senior approves-down, governed). **Plus:**
> an **F3** load-time check (an authority step MUST be GATED — AC-5); audit
> reconciliation to gate-time so the tie names who ACTUALLY acted (SD-6a /
> AC-6); the **AC-7 truth pass** (7 over-claim sites corrected, verification
> grep returns zero); and the blessing test re-harnessed (AC-8). **Two
> Cray-ratified divergences from the merged PLAN:** (1) **CUMULATIVE roles**
> authored in the shipped YAML — OVERRIDING PLAN-0075's Correction 1 (Cray:
> "a senior can approve downward", Policy B); (2) **NATIVE-TIER routing**
> (`native_approver`) — a new consequence Code SURFACED + Cray ratified, so the
> audit routing record stays on the tier's OWN approver even under cumulative
> roles (enforcement stays cumulative, routing stays native). **ADR-0026 D4**'s
> 4th fail-closed condition already merged (#746, AC-12).
> **draft≠review≠verify:** `plan-drafter` authored PLAN-0075 (Proposed, s132) →
> Code built + R2 → Cray ratified the two divergences (cumulative-role override
> + native-tier routing). **Evidence:** full offline suite **2692 passed / 7
> skipped**; 251 DB+API tests pass; `mypy --strict` clean; the live DB gate
> confirmed junior-refused / senior-approves-down. **PLAN-0075 stays OPEN in
> `docs/plans/`** — core landed (12/13 ACs); **AC-13 (derivation provenance) is
> the deferred follow-up** (`task_cbf139fe`, Cray-ratified split): hash the
> supply_chain `_DOSE_LADDER` + `_TOP_SEVERITY` into the run governance pin (a
> 5-call-site pin change needing a vertical-hook design — the engine pin can't
> import vertical constants; PROVENANCE-ONLY, **F-PIN stays open regardless**),
> THEN close PLAN-0075 → `done/`. The F-PIN remainder + the ADR-0031 D3
> gate-plugin seam (F-FACTORY) stay the #747 STATUS Active-TODO. Post-merge:
> main=`76f42cc`; 0 open PRs; tree clean (2 pre-existing untracked KEEP:
> `.claude/benchmark-results/`, `.claude/launch.json`); MS-S1 idle; dev Postgres
> UP; loop-dispatcher DISABLED. Commits: `74d8958` → `899d9a1` → `c8a951a` →
> `8011613` → `580b9e8` (the 5 PLAN-0075 core build commits, Steps 2-5 + AC-8) →
> `76f42cc` (HEAD, #749 merge).

> **Session 132, 2026-07-15 (head_commit `ff84d9a` → `098b0d9`) —
> GOVERNANCE / PLANNING batch: NO code shipped; two docs PRs that AUTHOR the
> AT-2 authority-enforcement fix + its ADR backing.** The **F1 gap** that
> s131's `next_action` named (spawn_task `task_053edc92`): an AT-2 authority
> ladder (`DoaLadder` / `SeverityLadder`) RESOLVES + AUDITS which tier/approver
> a spend or severity should route to, but the run gate never ENFORCED that the
> acting approver HOLDS that resolved tier role — a lower-tier approver could
> resolve a top-tier gate, and the persisted audit even NAMED a non-actor.
> Reproduced against code; scope = the whole AT-2 axis (`doa_tier` on BOTH
> procurement surfaces + `severity_tier` on supply_chain). **#746 (`5598c02`,
> `docs(adr+plans)`) — PLAN-0075 Proposed + the ADR-0026 D4 amendment.**
> **PLAN-0075** (Proposed, awaiting implementation scheduling): a pure
> `tier_authority` run-check ADDITIVELY beside `check_principal_sod` +
> gate-time actor-named audit + an **F3** load-time gated-autonomy check +
> **AC-13** supply_chain derivation-provenance fold-in. **ADR-0026 D4 gains a
> 4th fail-closed condition** (Accepted, in-place, additive): the acting
> approver must hold the ladder-resolved tier role, or a declared-authority
> step with no persisted verdict fails closed. Ratified SDs: **SD-1** =
> exact-match + **rank-as-authored-data** (no engine `RoleId` rank primitive;
> cumulative roles in YAML) / **SD-2** = read persisted verdicts, satisfy EVERY
> verdict / **SD-4** = amend ADR-0026 D4 / **SD-6** = gate-time actor-named
> audit tie (OQ-5 shape preserved); + a derivation residual-risk caveat (from
> the specialist review). **3-specialist SD-3/SD-5 review** (architect /
> security / governance-audit): **SD-3 = keep NARROW, confirmed** — the
> security fix is orthogonal to the ADR-0031 D3 gate-plugin seam, with the
> architect's binding condition to durably track the seam follow-on; **SD-5 =
> adjudicated SPLIT** (Cray) — FOLD IN the supply_chain derivation-provenance
> half NOW (**AC-13**, **PROVENANCE-ONLY**: hashes `_DOSE_LADDER` +
> `_TOP_SEVERITY` into the run pin = mid-flight tamper-evidence +
> which-derivation-governed-this-run, **NOT** a new-run guarantee, **F-PIN is
> NOT closed**), DEFER procurement's ฿ derivation to a follow-on bound to
> ADR-0031 D3 row-1 (declare-as-data). Three honesty corrections applied to the
> just-committed ADR/PLAN (a D4 over-claim; a wrong "cheap mitigation" note;
> the "different axis" framing → threat-tier). **#747 (`098b0d9`,
> `docs(status)`) — an interim Active-TODO tracker** for the two Out-of-Scope
> follow-ons (the F-PIN remainder + the ADR-0031 D3 gate-plugin seam) so they
> don't rot (the ADR-0031 OQ-4 deferral-rot precedent). **draft≠review≠verify:**
> `plan-drafter` authored PLAN-0075 + the ADR-0026 amendment → Code R2 (3
> honesty corrections) → Cray ratified SD-1..SD-6 + adjudicated the SD-5 split
> → a 3-specialist SD-3/SD-5 review. Doc-only — no `services/` change, no
> tests, deterministic-offline (no MS-S1 / host-state). **PLAN-0075 stays OPEN
> in `docs/plans/`** (Proposed, NOT closed — the build is the follow-on). 0
> open PRs after; loop-dispatcher DISABLED; MS-S1 idle. Commits: `5598c02`
> (#746 PLAN-0075 Proposed, ADR-0026 D4 amendment `60ad2e3`) → `098b0d9`
> (HEAD, #747 guardrail Active-TODO tracker).

> **Session 131, 2026-07-15 (head_commit `192dc52` → `ff84d9a`) — PLAN-0074
> shipped END-TO-END + CLOSED → `done/` in ONE session-131 day (#744, `feat`):
> the **2nd AT-2 governed-procedure signature**, reaching **N=2** — de-risking
> the deferred AT-2 GENERATOR (ADR-0025 D7 / Rule-of-Three) with a SECOND
> hand-authored exemplar on a DIFFERENT vertical pressing a DIFFERENT seam. The
> signature = a supply_chain **cold-chain excursion DISPOSITION** whose
> authority quantity is **NON-MONEY**: a `severity_tier` gate backed by
> `SeverityLadder` typed content (the **4th AT-2 gate kind**; `DoaLadder` is
> money-typed by construction and cannot represent non-money authority).**
> Steps 1-6: the spec / the obligation gate / the RUN path (resolver + dispatch
> + run-pin) / the procedure + factory / two self-cancelling markers / a
> red-team oracle + the AC-16 load-time `gate_kind`↔content correspondence
> check. **3-independent-reviewer adversarial harvest** (governance /
> correctness / test-honesty lenses) fixed **10 confirmed defects** —
> highlights: the facet-less "smuggled gate" (AC-16 closed only the
> CONTRADICTION half, not the dangerous OMISSION half — a `governance_content`
> with NO facet owed no SoD yet still gated at run); Infinity/NaN
> fail-DANGEROUS severity routing; a float-rounding crash on a real sub-0.005 °C
> breach; a KeyError that killed API startup; a degenerate lane set that made
> the criticality amplifier DEAD CODE. **Corrected the PLAN's own sketch:**
> `SourcePolicy` is NOT extended (the run executor keys provenance on the member
> itself, so a 3rd member would invert a vertical's provenance).
> **draft≠review≠verify:** `plan-drafter` PLAN → Code R2 → Cray SD-1
> (SeverityLadder) → build → the 3-reviewer harvest → 10 fixes. Full offline
> suite **2674 passed / 7 skipped**; `mypy --strict` + ruff clean;
> deterministic-offline throughout (no MS-S1 / host-state). **Follow-on (F1 —
> Cray-ratified, spawn_task `task_053edc92`, separate session):** the AT-2
> authority ladder (`doa_tier` + `severity_tier`) RESOLVES + AUDITS which tier
> approver should act but the gate never ENFORCES that the acting approver HOLDS
> that tier role — a lower-tier approver can resolve a gate routed to a higher
> tier (pre-existing across the AT-2 axis, touches the procurement hero, needs
> an ADR); folded-in siblings: an AT-2 authority step is not required to be
> `autonomy: gated`, the governance-pin doesn't cover the severity-derivation
> ladder, the `sod_steps`/`stamp_steps` vertical-union limitation. 0 open PRs
> after; tree clean (2 pre-existing untracked KEEP: `.claude/benchmark-results/`,
> `.claude/launch.json`); MS-S1 idle; dev Postgres UP; loop-dispatcher DISABLED.
> PLAN-0074 `git mv`→`done/` this session. Commits: `d9ffa08` (Step 1) /
> `bbe994f` (Step 2) / `34c09d6` (Step 3) → Steps 4-6 + the 3-reviewer harvest
> (`1743ead`, `c67312d`, `bf1916b`, `80df9dd`) → `ff84d9a` (#744 merge).

> _Rotation note (session-135 reconcile, 2026-07-15, `docs(status):`):
> frontmatter → `head_commit ece270a` (session 135); a new **session-135** block
> was PREPENDED for the PLAN-0077 transform-grammar arc (#754→#758), so the
> OLDEST — the whole **session-130** block (plan-drafter rigor #740 + ADR-0031
> core-lifecycle Accepted #741) — rotated OUT (4-session window, now s135 + s133
> + s132 + s131) to `docs/status-archive/2026-h1-status.md`. Recent Decisions
> gained the s135 close-out row and rotated its OLDEST (**s125**, 2026-07-13 —
> event-bridge live smoke #724 + energy over-current #725/#726) to the same
> archive (10-row window). Prior rotation notes (through the session-133
> reconcile) are consolidated here (R4). Per the STATUS.md Rotation Policy
> (R1/R2/R4)._

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
| 2026-07-15 | **s135 close-out — PLAN-0077 "transform-grammar build" COMPLETE (5 PRs #754→#758: Proposed → Phase A → B → C → #758 L-8 landing); renders ADR-0031 D3 row-1 + ADR-016 Q4 OQ-3, NO new ADR (arc spans s134-135)** — the typed anti-eval `derive` transform grammar shipped, load-gated + execution-bound for the shipped op-set (`StepKind.TRANSFORM` + `transform_step.py`; a value-parity oracle reproduces `derive_excursion_severity` + `scored_rule`'s `amount = unit_price × qty` value-identically WITHOUT touching the hardened stamp path, SD-1; 93 AC tests). **Honest residual: the two verticals' seeds stay execution-bound ✖; the marquee stamps stay code-side (SD-1); `derivation_hash` in service; F-PIN stays OPEN** — flipping those = the separate SD-4 parity-guarded seed-migration PLAN (+ the PLAN-0076 Step T2 F-PIN fold-in). draft≠review≠verify: Phase A/B/C = Code authored+verified; PLAN-0077 + the L-8 Accepted-body edit = `plan-drafter` → Code R2 + committed; STATUS = `status-scribe` → Code R2. Full narrative: the Session-135 CF block above | `ece270a` (HEAD, #758 L-8 landing) / `8808902` (#757 C) / `d94a10d` (#756 B) / `e93e9d0` (#755 A) / `3e6ee4d` (#754 Proposed) / `services/engine/procedures/transform_step.py` + `docs/plans/done/0077-*.md` |
| 2026-07-15 | **s133 close-out — PLAN-0075 COMPLETE (all 13 ACs) + CLOSED → `done/`; AC-13 derivation provenance shipped (#751, `feat`); PLAN-0076 filed as the STANDING follow-on TRACKER (#752, `Status: Tracking`)** — **AC-13** hashes supply_chain `_DOSE_LADDER` + `_TOP_SEVERITY` into the run governance pin via a per-vertical `registry.derivation_hash` hook (optional `derivation_hash` threaded through the 5 pin call sites); **PROVENANCE-ONLY** (mid-flight tamper-evidence + which-derivation-governed-this-run — **F-PIN stays OPEN**); 9 offline tests. PLAN-0075 (core AC-1..AC-12 #749 + AC-13 #751) `git mv`→`done/`. **PLAN-0076** (Cray-ratified s133 4-specialist SD-1 panel) homes the 2 PLAN-0075 deferrals (F-PIN remainder + ADR-0031 D3 gate-plugin / F-FACTORY seam) with an **AC-6 presence guard-test** (`test_at2_followon_tracking_guard.py`, RED on a premature archive-to-`done/` or a pruned STATUS pointer — "location≠tripwire; failing tests are the real anti-rot"). Merge order: #752 (`4a682ab`) then branch-updated #751 (`fac77c7`), both gate-verified. draft≠review≠verify: AC-13 = Code authored+verified; PLAN-0076 = `plan-drafter` → Code R2 → Cray ratified the panel; STATUS = `status-scribe` → Code R2. Full narrative: the Session-133 close-out CF block above | `fac77c7` (HEAD, #751 merge) / `4a682ab` (#752) / `0520fb2` (AC-13 feat) / `docs/plans/done/0075-*.md` + `docs/plans/0076-*.md` + `tests/services/engine/procedures/test_at2_followon_tracking_guard.py` |
| 2026-07-15 | **s133 — PLAN-0075 core: AT-2 AUTHORITY ENFORCEMENT AT THE RUN GATE shipped (12/13 ACs, #749, `feat`); closes the s131-surfaced F1 exploit (`task_053edc92`)** — the AT-2 ladder (`doa_tier` / `severity_tier`) RESOLVED/AUDITED which tier should approve but no run path ENFORCED the acting approver HELD that role (a junior `appr-buyer`, ฿0-50k, could resolve the procurement hero's ฿288k / ฿2M gate; the audit even NAMED a non-actor). **Fix:** a pure `tier_authority.check_tier_authority` runs at `resolve_gated_step` AFTER the SoD check (ADDITIVE, SoD primary) and BLOCKS unless the approver holds EVERY persisted verdict's ladder-resolved tier role — verified at the LIVE DB gate (junior refused, senior approves-down governed). Plus an F3 load check (authority step must be GATED — AC-5), gate-time audit reconciliation naming who ACTED (SD-6a / AC-6), the AC-7 truth pass (7 over-claim sites corrected, grep zero), the blessing test re-harnessed (AC-8). **Two Cray-ratified divergences:** (1) CUMULATIVE roles in the shipped YAML OVERRIDE PLAN-0075's Correction 1 (Cray "senior approves downward", Policy B); (2) NATIVE-TIER routing (`native_approver`, Code-surfaced) keeps the audit routing on the tier's OWN approver (enforcement cumulative, routing native). ADR-0026 D4's 4th fail-closed condition already merged (#746, AC-12). draft≠review≠verify: `plan-drafter` authored (Proposed, s132) → Code built + R2 → Cray ratified the 2 divergences. Full offline suite **2692 passed / 7 skipped**; 251 DB+API tests pass; `mypy --strict` clean; live DB gate = evidence. **PLAN-0075 stays OPEN** (12/13 ACs); AC-13 (derivation provenance, `task_cbf139fe`) is the deferred follow-up = hash supply_chain `_DOSE_LADDER` + `_TOP_SEVERITY` into the run pin (5 sites, vertical-hook; PROVENANCE-ONLY, F-PIN NOT closed), then close → `done/`; F-PIN remainder + ADR-0031 D3 seam stay the #747 Active-TODO. Full narrative: the Session-133 CF block above | `76f42cc` (HEAD, #749 merge) / `580b9e8`…`9e3d421` (7 core build commits) / `services/**` (`tier_authority.check_tier_authority` + `resolve_gated_step` wiring + F3 load check + gate-time audit reconciliation) + `verticals/{procurement,supply_chain}/**` (cumulative-role YAML + `native_approver`) + `tests/**` (AC-5/6/7/8 + live DB gate) + `docs/plans/0075-*.md` (OPEN, 12/13 ACs) |
| 2026-07-15 | **s132 — GOVERNANCE / PLANNING batch (NO code; 2 docs PRs): PLAN-0075 Proposed (#746) + the ADR-0026 D4 amendment, closing the F1 AT-2 authority-enforcement gap** — an AT-2 authority ladder (`DoaLadder` / `SeverityLadder`) RESOLVES + AUDITS which tier/approver a spend or severity should route to, but the run gate never ENFORCED that the acting approver HOLDS that resolved tier role (a lower-tier approver could resolve a top-tier gate; the persisted audit even NAMED a non-actor); scope = the whole AT-2 axis (`doa_tier` on both procurement surfaces + `severity_tier` on supply_chain). **PLAN-0075 Proposed** (awaiting implementation scheduling): a pure `tier_authority` run-check ADDITIVELY beside `check_principal_sod` + gate-time actor-named audit + an F3 load-time gated-autonomy check + **AC-13** supply_chain derivation-provenance fold-in. **ADR-0026 D4 gains a 4th fail-closed condition** (Accepted, in-place, additive): the acting approver must hold the ladder-resolved tier role, or a declared-authority step with no persisted verdict fails closed. Ratified SDs: **SD-1** = exact-match + **rank-as-authored-data** (no engine `RoleId` rank primitive; cumulative roles in YAML) / **SD-2** = read persisted verdicts, satisfy EVERY verdict / **SD-4** = amend ADR-0026 D4 / **SD-6** = gate-time actor-named audit tie (OQ-5 shape preserved); + a derivation residual-risk caveat. **3-specialist SD-3/SD-5 review** (architect / security / governance-audit): **SD-3 = keep NARROW, confirmed** (orthogonal to the ADR-0031 D3 gate-plugin seam; the architect's binding condition = durably track the seam follow-on); **SD-5 = adjudicated SPLIT** (Cray) — FOLD IN supply_chain derivation-provenance NOW (AC-13, PROVENANCE-ONLY: hashes `_DOSE_LADDER` + `_TOP_SEVERITY` into the run pin = mid-flight tamper-evidence, NOT a new-run guarantee, **F-PIN NOT closed**), DEFER procurement's ฿ derivation to a follow-on bound to ADR-0031 D3 row-1. Three honesty corrections to the just-committed ADR/PLAN (a D4 over-claim; a wrong "cheap mitigation" note; the "different axis" framing → threat-tier). #747 = an interim Active-TODO tracker for the two Out-of-Scope follow-ons (F-PIN remainder + the ADR-0031 D3 seam) so they don't rot. draft≠review≠verify: `plan-drafter` authored → Code R2 (3 corrections) → Cray SD-1..SD-6 + the SD-5 split → 3-specialist review. Doc-only, deterministic-offline (no MS-S1 / host-state); 0 open PRs; PLAN-0075 stays Proposed in `docs/plans/`. Full narrative: the Session-132 CF block above | `098b0d9` (HEAD, #747 guardrail Active-TODO tracker) / `60ad2e3` (ADR-0026 D4 amendment) / `5598c02` (#746 PLAN-0075 Proposed + ratifications) / `docs/plans/0075-*.md` (Proposed) + `docs/adr/0026-*.md` (D4 4th fail-closed condition) |
| 2026-07-15 | **s131 — PLAN-0074 (the 2nd AT-2 governed-procedure signature) shipped END-TO-END + CLOSED → `done/` in ONE session-131 day (#744, `feat`); reaches N=2 → de-risks the deferred AT-2 GENERATOR (ADR-0025 D7 / Rule-of-Three) via a supply_chain cold-chain excursion DISPOSITION whose authority is NON-MONEY — a `severity_tier` gate + `SeverityLadder` typed content (the 4th AT-2 gate kind; `DoaLadder` is money-typed by construction and cannot represent it)** — Steps 1-6 (spec / obligation gate / run path [resolver + dispatch + run-pin] / procedure+factory / two self-cancelling markers / red-team oracle + the AC-16 load-time `gate_kind`↔content correspondence check), then a **3-independent-reviewer adversarial harvest** (governance / correctness / test-honesty lenses) fixed **10 confirmed defects** (highlights: the facet-less "smuggled gate" — AC-16 closed only the CONTRADICTION half, not the dangerous OMISSION half, so a facet-less `governance_content` owed no SoD yet still gated at run; Infinity/NaN fail-DANGEROUS severity routing; a float-rounding crash on a real sub-0.005 °C breach; a KeyError that killed API startup; a degenerate lane set → dead-code criticality amplifier). Corrected the PLAN's own sketch: `SourcePolicy` is NOT extended (the run executor keys provenance on the member itself, so a 3rd member would invert a vertical's provenance). draft≠review≠verify: `plan-drafter` PLAN → Code R2 → Cray SD-1 (SeverityLadder) → build → 3-reviewer harvest → 10 fixes. Full offline suite **2674 passed / 7 skipped**; `mypy --strict` + ruff clean; deterministic-offline (no MS-S1 / host-state); 0 open PRs. **Follow-on F1** (Cray-ratified, spawn_task `task_053edc92`, separate session): the AT-2 authority ladder (`doa_tier` + `severity_tier`) RESOLVES/AUDITS which tier should act but the gate never ENFORCES the acting approver holds that role (a lower tier can resolve a higher-tier gate) — pre-existing AT-2-wide, touches the procurement hero, needs an ADR. PLAN-0074 `git mv`→`done/`. Full narrative: the Session-131 CF block above | `ff84d9a` (HEAD, #744 merge) / `34c09d6`·`bbe994f`·`d9ffa08` (Steps 1-3) / `7b38db6` (#743 PLAN-0074 Proposed) / `services/**` (severity_tier resolver + dispatch + run-pin · `SeverityLadder` · obligation gate · AC-16 correspondence check) + `verticals/supply_chain/**` (cold-chain disposition procedure + factory) + `tests/**` (red-team oracle + self-cancelling markers) + `docs/plans/done/0074-*.md` |
| 2026-07-14 | **s130 — FOUNDATION/GOVERNANCE session (NO feature; 2 docs/config PRs): plan-drafter rigor hardening (#740) + ADR-0031 "core lifecycle architecture" Accepted (#741)** — **#740 (`eea875f`, `chore(drafter)`):** a stale NEGATIVE fact-pack claim ("OQ-8 unbuilt") nearly drove a WRONG ADR decision → Lesson #0030 + a feedback memory (verify the fact-pack, ESPECIALLY negative / precondition claims, BEFORE dispatching the drafter — **the newest accepted ADR wins on FACTS**) + `.claude/agents/plan-drafter.md` operating-discipline **point 8** (a drafter-side backstop: cite-or-flag negative claims + a targeted supersession grep); root cause = Code dispatch hygiene, NOT a drafter defect. **#741 (`192dc52`, `docs(adr)`) — ADR-0031 Accepted:** names vero-lite's two extensibility idioms (runtime registries vs closed typed governed enums = the moat spine) + ratifies **"closed governed core + ONE typed, policy-carrying seam per core"** as multi-vertical scale WITHOUT dissolving the moat; builds NO seam — PRE-DESIGNS each core's seam for its N≥2 trigger (the fractal Rule-of-Three) with greppable moat tripwires; seam map D3 (transform StepKind · TriggerDriver/ECA · governance-gate plugin + decision-as-data · executor auto-discovery fold-in · audit transition taxonomy). draft≠review≠verify: `plan-drafter` authored → Code R2 → Cray OQ-1..4 as-rec (AskUserQuestion). **FIRST run under the #740 hardening CAUGHT OQ-4** (ADR-0025 D7's AT-2-generator CI marker was NEVER built, only the principal-identity mirror exists → armed as a Path-2 AC). Direction (Cray s130): the hero must GENERATE the governance (AT-2) not compose around it → **Path 2** (hand-author a 2nd AT-2 signature on a different vertical/seam → N≥2 → THEN the AT-2 generator, ADR-0025 D7; reframe: OQ-8's typed AT-2 sub-model is ALREADY BUILT by ADR-0025). Doc/config-only — no `services/` / tests, deterministic-offline (no MS-S1 / host-state); 0 open PRs. Full narrative: the Session-130 CF block above | `192dc52` (HEAD, #741 ADR-0031 Accepted) / `eea875f` (#740 drafter hardening) / `docs/adr/0031-core-lifecycle-architecture.md` + `.claude/agents/plan-drafter.md` (point-8 backstop) + `docs/lessons/0030-verify-fact-pack-before-drafter-newest-adr-resolves-oq.md` + `docs/research/private/2026-07-14-work-lifecycle-cores.md` (grounding, gitignored) |
| 2026-07-14 | **s129 — PLAN-0073 (the Box-4 `economic_impact` facet surfaced in the Palantir-lite hero-demo UI) shipped END-TO-END + CLOSED → `done/` in ONE session-129 day (#737 Ready → #738 build); beat-4 (฿) now ALSO carries the typed Box-4 `EconomicImpact` facet with audit-grade provenance UNDER the unchanged demo ledger; NO ADR change (ADR-0030 D2 ledger+facet coexist; ADR-007 D2 envelope byte-untouched — facet stays trace-carried)** — Cray ratified SD-1(a)/SD-2(b)/SD-3 via AskUserQuestion (all as-rec). **SD-1(a) fire-for-real:** `_intake_seed` carries `event_type` (from the failure event at `run.py:208`) so the Box-4 producer fires INSIDE the governed run; build-discovered (OQ-1, via the AC-2 RED test) the hero `source` step is `GovernanceActionExecutor._scored_rule` which REPLACES the base action envelopes (threading the selected spend for `doa_tier`) → it now LIFTS the advisory `economic_impact` trace step onto the persisted step trace (else computed-then-discarded); advisory + never-raise (ADR-0030 D5). **SD-2(b):** `GET /demo/hero/impact` gains an additive optional `economic_impact` field; the producer reuses `build_hero_impact_ledger` so the ฿ figures EQUAL the ledger's (no drift, ledger byte-identical). **SD-3:** `view-hero.js` provenance strip under the unchanged ledger card — `kind` chip + always-visible `PROVISIONAL` badge (s74 trust-shape) + "show provenance" toggle → `assumptions[]` + `basis_refs`; `hero.css` c35 / `view-hero.js` c36 `?v=` bumps. Build-discovered (disclosed): pre-commit mypy caught a `list[Mapping]` vs `list[dict[str,Any]]` the first manual `mypy` skipped (the `&&` chain stopped at `ruff format --check`) → fixed with `cast` + annotation. draft≠review≠verify: `plan-drafter` PLAN → Code R2 (anchors re-verified on disk) → Cray SD-1(a)/SD-2(b)/SD-3 → build. 3 new AC tests GREEN (AC-1 endpoint facet `net_benefit`==ledger + 4 `basis_refs`; AC-2 producer fires on the real hero seed + persisted governed-run source trace carries the `economic_impact` step; AC-2/AC-3 existing ledger tests UNMODIFIED); AC-4 preview renders the strip + toggle, no console errors; suite **2599/7** WITH Postgres (verified on BOTH PR head + merge commit `f250593`, CI PR-only); ruff + `ruff format --check` + `mypy --strict services/` clean; deterministic-offline (no MS-S1 / host-state); 0 open PRs. PLAN-0073 `git mv`→`done/`. Full narrative: the Session-129 CF block above | `f250593` (HEAD, #738 feat merge) / `cc8516e` (#737 PLAN-0073 Ready) / `verticals/procurement/hero_demo/**` (`_intake_seed` `event_type` + `economic_impact` endpoint field + producer) + `GovernanceActionExecutor._scored_rule` (lifts the advisory step onto the persisted trace) + the oct-demo-procurement frontend (`view-hero.js` provenance strip, `?v=` bumps) + `tests/**` (3 AC tests) + `docs/plans/done/0073-*.md` |
| 2026-07-14 | **s128 — PLAN-0072 (the Palantir-lite hero demo's beat-3 "run it" step) shipped END-TO-END + CLOSED → `done/` in ONE session-128 day (#734 Ready → #735 build); the hero demo's beat-3 now GENUINELY resolves the parked DOA gate through the REAL production `POST /runs/{id}/gate/resolve`, rendering the persisted truth — replacing a FAKE front-end badge; NO engine change** — Cray picked D3 (next-work-analyst-ranked); `plan-drafter` PLAN → Code R2 → Cray SD-A(b)/SD-B(b)/SD-C(a)/SD-D(a) via AskUserQuestion → build. **Backend:** event opener additively exposes the parked `run_id` on its `hero` dict; generation-aware replay (SD-C, clock-free COUNT of decided runs bumps `detected_at` +1h past the 3600 s dedup bucket → a FRESH parked run); SD-A(b) drives the PRODUCTION resolve route with `api_auth_enabled` + a real authenticated `appr-pm` Person (RF-1 end-to-end), NO new endpoint. **Frontend** `renderActPanel` reworked: SD-D(a) inline login (authenticate THEN sign), SD-B(b) Approve AND Reject, renders the persisted `GateResolveResponse` (approve → COMPLETED + SoD tie; reject = continue+record → COMPLETED, NOT a rejected terminal); `api.js` Hero.runDetail/resolve; `?v=` bumps. **Build-discovered prod bug (disclosed AC-6 correction):** the SoD-403 path `asdict`'d a frozenset `SoDViolation.constraint_steps` → un-serializable → Starlette 500 MASKED the 403 (procurement = first frozenset SoD verdict on this HTTP path); fixed in `services/api/routers/runs.py` (frozenset → sorted list), security posture INTACT — SoD fails CLOSED before serialize (run stays parked, `gate_refused` audit), only the response CODE was wrong. OQ-4 resolved (reject test → downstream tolerates empty executed-effect set). draft≠review≠verify: `plan-drafter` PLAN → Code R2 → Cray SD-A..SD-D → build. 5 new AC tests GREEN; suite **2596/7** WITH Postgres (on BOTH PR head + merge commit `88e6984`, CI PR-only); ruff + `ruff format --check` + `mypy --strict services/` clean; deterministic-offline (no MS-S1 / host-state; Postgres for DB-backed ACs only); 0 open PRs. PLAN-0072 `git mv`→`done/`. Full narrative: the Session-128 CF block above | `88e6984` (HEAD, #735 feat merge) / `85f90ed` (#734 PLAN-0072 Ready) / `services/api/routers/runs.py` (SoD-403 JSON-sanitize) + `verticals/procurement/hero_demo/**` (`run_id` expose + generation-aware replay) + the oct-demo-procurement frontend (`renderActPanel`, `api.js` Hero.runDetail/resolve, `?v=` bumps) + `tests/**` (5 AC tests) + `docs/plans/done/0072-*.md` |
| 2026-07-14 | **s127 — PLAN-0071 (the Box-4 economic-impact ฿ facet) shipped END-TO-END across all 4 OCT verticals (2 PRs) + CLOSED → `done/`; the reactive AND governed recommenders now append an ADVISORY, trace-carried `economic_impact` `ReasoningStep` (baseline vs governed exposure → net ฿ benefit) — DISCHARGING the ADR-016 self-cancelling Box-4 N≥3 deferral with an OWNED marker (AC-5 GREEN at N=4); ADR-007 D2 envelope byte-verbatim (#731/#732)** — **#731 PR1 (`81c7070`, `feat`) engine core:** new `services/engine/economic_impact.py` (`EconomicExposure`/`EconomicImpact` + a NEVER-RAISE `build_economic_steps` helper) wired at BOTH `RecommendedAction` sites (`recommender._compose_llm_record` reactive + `action_step._compose_action` governed), appended LAST, never on `_rule_recommend`; AC-5 marker landed RED (`xfail(strict=True)`); conftest autouse clears the producer registry; envelope (`services/engine/actions.py`) byte-untouched. **#732 PR2 (`b11ea40`, `feat`) THE close:** four per-vertical ฿ producers (`verticals/<ns>/economic_impact.py`) — energy `avoided_outage` ฿405k / supply_chain `spoilage_avoided` ฿2.12M / aquaculture `mortality_avoided` ฿247k (assumptions-first per SD-B/SD-G, every ฿ input a named `assumptions[]` entry, NO ontology/regen/migration); procurement `expedite_tradeoff` from the committed-CSV demo ledger (`hero_demo/ledger.py` byte-untouched, `basis_refs` cite CSV columns, gated on the emergency-failure trigger — OQ-C calm-path → `None`, hero-PO exemplar stands in for per-event PO anchor, deferred v2); `discovery._register_vertical` gained a GUARDED optional producer import (`ModuleNotFoundError.name` checked). AC-5 GREEN at N=4; AC-9 GREEN (real energy producer → one `economic_impact` step, net ฿405,000); coupled-test audit = every pin PINNED-UNMODIFIED. draft≠review≠verify: `plan-drafter` PLAN → Code R2 → Cray SD-A..SD-G → build. Suite **2591 passed / 7 skipped / 0 xfailed** WITH Postgres (verified on BOTH PR head + merge commit `b11ea40`, CI PR-only); ruff + `ruff format --check` + `mypy --strict services/` clean; deterministic-offline (no MS-S1 / host-state); 0 open PRs. PLAN-0071 `git mv`→`done/`. Full narrative: the Session-127 CF block above | `b11ea40` (HEAD, #732 PR2 merge) / `81c7070` (#731 PR1 engine core) / `services/engine/economic_impact.py` + `services/engine/{recommender.py, procedures/action_step.py, discovery.py}` + `verticals/{energy,supply_chain,aquaculture,procurement}/economic_impact.py` + `tests/**` (AC-5 ≥3-vertical marker + AC-9) + `docs/plans/done/0071-*.md` |
| 2026-07-13 | **s126 — ADR-0030 Accepted (#728): the Box-4 economic-impact ฿ facet — typed, ADVISORY, trace-carried (`economic_impact` `ReasoningStep`, producer-validated `EconomicImpact` detail; ZERO ADR-007 D2 envelope change) — DISCHARGING the ADR-016 self-cancelling N≥3 Box-4 deferral (N=4)** — ONE cross-vertical shape (`baseline` vs `governed` exposure → `net_benefit`) + per-vertical `kind` (avoided_outage / expedite_tradeoff / spoilage_avoided / mortality_avoided). Disclosed `was an error` (§6): the promised N≥3 marker test was NEVER built → enforcement = a ≥3-vertical build-completion AC in the follow-on BUILD PLAN. Doc-only, contract-only batch (no code/tests). `plan-drafter` → Code R2 → Cray SD-1..SD-7 as-rec. Full narrative: the Session-126 CF block above | `a9dbb6f` (HEAD, #728 `docs(adr)` merge) / `docs/adr/0030-*.md` |
## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13; guarded trial (parallel to ADR-012) — verdict **continue-with-adjustments**. Run 1 (energy, s93) + Run 2 (supply-chain, s94) both COMPLETE, S-checks all PASS against pre-committed oracles, no R-PS trigger fired; C-1..C-3 CONFIRMED → **no open partner-sim debt**. ADR-011 audit stays gated on a REAL partner conversation (R3: SYNTHETIC provenance INFORMS but never TRIGGERS it). Full record: `docs/adr/0020-*.md` + the gitignored run packages `docs/research/private/2026-07-02-partnersim-run{1,2}-*.md`. _(Full prior narrative — the ~8 schema-mismatch findings, both run details, cross-run synthesis — archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **Procurement vertical — GO + SHIPPED (PLAN-0036 Fastenal, Stage 1):** 4th vertical greenlit (s75); PLAN-0036 drafted + merged Draft (#412, `7a7c036`; SD-1…SD-5 confirm-all). Demo target = Fastenal Thailand (auto-parts / EEC); **hero** = asset-failure → governed emergency sourcing, **calm-path** = low-stock reorder. Stage 1 = a PLAN-only pure-config plugin on the ADR-016 engine (zero `services/` core edit; CQ-1 / ADR-0023). **Pitch** = asset-ontology-triggered governed sourcing (native ontology ADR-008 + engine ADR-016), NOT the commoditized "governed"/"cross-vertical" claims. Full record: `docs/plans/0036-*.md` + the s72 de-risk dossier `docs/research/private/2026-06-22-procurement-*.md` (5 files: spec-expressiveness, GTM, asset-aware incumbent scan, AI-sourcing teardown, platform-incumbent deepdive). _(Full prior narrative archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [ ] **PLAN-0075 follow-ons — now homed by PLAN-0076 (`Status: Tracking`, filed #752, s133): the F-PIN remainder + the ADR-0031 D3 gate-plugin seam (guardrail against the ADR-0031 OQ-4 deferral-rot precedent — s133 4-specialist panel).** PLAN-0075 (the F1 AT-2 authority-enforcement gap: an AT-2 ladder RESOLVES/AUDITS the required tier but the run gate never ENFORCES that the acting approver holds that tier role — a lower tier could resolve a higher-tier gate; the persisted audit even named a non-actor) is now **COMPLETE — all 13 ACs (core AC-1..AC-12 #749 + AC-13 derivation provenance #751) — and CLOSED → `docs/plans/done/0075-*.md`** (with the **ADR-0026 D4(iv) amendment**: tier-authority enforced at `resolve_gated_step`, additive beside `check_principal_sod`; cumulative senior roles authored in YAML per Cray's Policy-B override; gate-time actor-named audit tie per SD-6). Two Out-of-Scope items — now tracked by **PLAN-0076**, no longer by PLAN-0075 — that must **NOT** rot: **(1) F-PIN remainder** — supply_chain's severity derivation (`_DOSE_LADDER` + `_TOP_SEVERITY`, `cold_chain_assess.py:71-77`) is provenance-hashed by PLAN-0075 AC-13 via a per-vertical `registry.derivation_hash` hook (**PROVENANCE-ONLY**: mid-flight tamper-evidence + which-derivation-governed-this-run; **NOT** a new-run guarantee — **F-PIN is NOT closed**), but procurement's imperative ฿ derivation (`unit_price × qty`) is still un-pinned; proper fix = **declare-the-derivation-as-data (ADR-0031 D3 row-1)** → the existing `governance_content` pin covers it for free, NOT a hand-rolled code hash. **(2) The ADR-0031 D3 gate-plugin seam (F-FACTORY)** — trigger has fired (PLAN-0074 = the 2nd AT-2 signature, D4.1 satisfied); folds in procedure-scoped `sod_steps` via a procedure-aware `ExecutorFactory` + the OQ-4 CI-marker check. **PLAN-0076** is the STANDING Tracking stub that homes both; its **AC-6 presence guard-test** (`test_at2_followon_tracking_guard.py`) turns the build RED on a premature archive-to-`done/` or a pruned STATUS pointer (the panel's "location≠tripwire; failing tests are the real anti-rot" finding — the architect's binding SD-3 condition, now enforced not just tracked). *(PLAN-0075 = #749/#751 → `done/`; PLAN-0076 = #752, `Status: Tracking`; ADR-0026 amendment `60ad2e3`; s133 4-specialist SD-1 panel.)*
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2; Q3 ADR Accepted + BUILD COMPLETE s93 — open only for the residues).** (1) **Q3 ontology data-binding — DONE end-to-end:** the ADR-016 D2+D3 amendment (Accepted s93, #505) is now **BUILT + CLOSED** (PLAN-0046 → `done/`; #511 feat `878b517` / #512 close `eb63692`, s93 cont. 2026-07-02): `StepInput.reads: list[str]` + `Agent.allowed.object_types` + the `validate_read_bindings` **LOAD-time consistency/scoping gate** (`reads ∈ ontology ∩ allowlist`, SD-1 Option A) wired at both production pre-flight sites; `reads` H-governed via `STEP_GOVERNANCE_FIELDS` + the `lift_to_step` draft-strip hardening; 12 new tests, offline suite 2066 passed / 5 skipped. v1 = a typed read contract + load-gate, **NOT** runtime-enforced parity — the declared==dispatched teeth for the read side then **SHIPPED as PLAN-0048** (the "Q4 generic run-consume query executor", `docs/plans/done/0048-q4-generic-query-executor.md`, s96, #533–#539; all 15 ACs, Complete 2026-07-04): an engine-owned deterministic `QueryStepExecutor` (`services/engine/procedures/query_step.py`) giving *plain declared reads* the **declared ✔ · load-gated ✔ · execution-bound ✔** frame + a typed auditable refusal (no silent `[]`). **The remaining Q4 residue** (the ADR + grammar build now DONE — only the migration PLAN remains): the four shipped verticals are NOT yet on the generic executor — their query steps encode projections/joins the spec could not yet declare (PLAN-0048 fact-pack 8 / LOCKED-9: hand-written seeds stay **execution-bound ✖** until migrated). The join/projection-grammar ADR is now **Accepted** (ADR-016 Q4 amendment, #659) + the grammar is **BUILT + CLOSED** (PLAN-0061, #664–#668) — a declaring step is execution-bound ✔ for the 2 v1 shapes; only **(b) the per-vertical production-factory + seed-migration PLAN** (Phase 3 = **PLAN-0062, COMPLETE — all 5 PRs, all 9 ACs → `done/`** — PR1 #672 parity core + PR1b #673 env-band executor/energy factory + PR2 #675 supply_chain + PR3 #676 aquaculture + PR4 #682 procurement shadow-parity/close-out) is DONE, having migrated the four verticals' hand-written seeds onto the grammar (all THREE OCT query steps — energy `read_readings`, supply_chain `read_temps`, aquaculture `read_do` — now execution-bound ✔ on the production HTTP path; procurement `intake` is declared-expressible ✔ under shadow parity but production execution stays the co-existing `_SeedQuery` ✖ for derived fields; `read_stock` deferred/labelled/reason-corrected — ERRATUM 2). (2) **Box 4 (Profit Formula) — BUILT + CLOSED (PLAN-0071, s127, #731/#732) + SURFACED IN THE HERO UI (PLAN-0073, s129, #737/#738); the Box-4 economic-impact ฿ facet is now COMPLETE across all 4 verticals AND surfaced in the Palantir-lite hero-demo UI (beat-4 ฿ carries the typed EconomicImpact facet + a provenance strip under the unchanged demo ledger).** N≥3 is MET (4 shipped verticals); ADR-0030 (Accepted s126, #728) TYPED and PLAN-0071 SHIPPED the economic-impact facet — advisory + trace-carried: an `economic_impact` `ReasoningStep` in `reasoning_trace` (`detail` = a producer-validated `EconomicImpact` model; ZERO ADR-007 D2 envelope change), ONE cross-vertical shape (`baseline` vs `governed` exposure → `net_benefit`) + per-vertical `kind` (avoided_outage / expedite_tradeoff / spoilage_avoided / mortality_avoided). Disclosed `was an error` (CLAUDE.md §6): the ADR-016-promised enforceable self-cancelling N≥3 marker test was NEVER built (a claim-vs-code gap caught by s126 manual grounding, NOT a mechanical trigger) — enforcement SHIPPED as the OWNED ≥3-vertical build-completion marker (AC-5, GREEN at N=4 in PLAN-0071: the `EconomicImpact` model + `economic_impact` emission at both `RecommendedAction` sites + four per-vertical ฿ producers). *(s84 strategy discussion + the 3-layer / ontology-binding diagram; Q3 ADR Accepted s93 #505; Q3 build complete + PLAN-0046 closed s93 cont. #511/#512; **Q4 executor SHIPPED = PLAN-0048 closed s96 #533–#539** [reconciled 2026-07-08]; **Q4 join-grammar ADR Accepted #659 + grammar built PLAN-0061 #664–#668** [reconciled 2026-07-09 s116] — **Phase-3 PLAN-0062 COMPLETE** [PR1 #672 + PR1b #673 + PR2 #675 + PR3 #676 + PR4 #682 → `done/`, reconciled 2026-07-10 s117]; **the per-entity `threshold_field` band arc (ADR-016 amendment) — FK-parent Rule-of-Three MET s123:** procurement same-row [PLAN-0066, s120] / supply_chain FK-parent [PLAN-0067, s121] / aquaculture FK-parent [**PLAN-0068** — `read_do`/`do_floor` now execution-bound + per-entity-banded, #715/#716, s123] / energy over-current FK-parent [**PLAN-0070** — `read_readings`/`rated_current_a`, judge env_band→threshold_field, the LAST shipped env_band consumer retired, #726, s125] all shipped → `done/` [reconciled 2026-07-13; energy s125]; the band-shape Rule-of-Three was already MET at N=3 s123 so energy is breadth-not-gate; **Box-4 facet DESIGNED — ADR-0030 Accepted s126 #728 [reconciled 2026-07-13]; Box-4 BUILT + CLOSED — PLAN-0071 #731/#732, AC-5 GREEN N=4 [reconciled 2026-07-14 s127]; Box-4 SURFACED IN THE HERO UI — PLAN-0073 #737/#738 [reconciled 2026-07-14 s129]**; the Box-4 economic-impact ฿ arc is now COMPLETE across all 4 verticals AND surfaced in the hero UI — this TODO's Box-4 leg is DONE, the residue is the Q4 procurement `intake` `_SeedQuery` derived-field co-existence (the O-2 open leg) + the O-2 data-binding trail above)*
- [ ] **Bounded/incremental chain verification (PLAN-0063 SD-4 follow-up, s118).** `GET /audit/verify` walks the WHOLE chain O(n) on demand — accepted at pilot scale and documented in the endpoint docstring. Future work = a checkpointed head / verify-since-anchor design; anchor storage ≈ external anchoring = **ADR-011 tripwire territory — do not build without re-reading the tripwire**. *(s118; #688/#690)*- [ ] **procurement ontology ↔ CSV column drift (PLAN-0062 close-out follow-up, s117).** The procurement ontology declares `PurchaseOrder.part_no` / `Quotation.price` / `OperationalEvent.equipment_id` while the real CSVs emit `part_id` / `price_thb` / `asset_id`; the load gate checks DECLARED properties while the executor merges RUNTIME keys (the AC-6 shadow-parity test renames four `PurchaseOrder`∩`Quotation` collisions to keep each quote's own supplier). Data/ontology evolution — explicitly **out of PLAN-0062's scope**. *(s117; PLAN-0062 PR4 #682)*
- [ ] **DEFERRED: a monotonic `sequence` column on `step_results` (s117 flaky-DB track carry-over; needs a migration → own PLAN).** #678 fixed the resume/GET-run path to read the suspended step by STATUS, but two wall-clock orderings remain — `load_run` (`services/engine/procedures/persistence.py`) + the run-list `order_by(PipelineRun.started_at)` in `services/api/routers/runs.py:200` — both **DISPLAY-ONLY** now, so not urgent. **#684 closed the TESTS half of the same invariant** — six positional `step_results[-1]` reads that misread `load_run`'s wall-clock order — and a static AST guard (`tests/services/db/test_load_run_ordering_guard.py`) now prevents that class of regression; but `load_run`'s wall-clock `ORDER BY created_at` is **unchanged by design**, so **the deferral STANDS**: a monotonic per-run sequence column would remove the hazard at its ROOT rather than guard against it. It needs a DB migration, so it deserves its own PLAN (PLAN-0062-independent). *(s117; #678/#680/#684)*
- [ ] **Standard partner-intake form (template candidate — Cray observation, s93 partner-sim run-1).** Generalize the 6-ask structure (+ the TWP package's §1–§10 answer shape as a SYNTHETIC-bannered worked example) into a stakeholder-facing standard intake form per vertical, so partners can prepare narrative context for vero-lite to generate workflow pipelines more accurately. Template lineage = the partner-facing ONE-PAGER (full taxonomy allowed for real partners), NOT the R1-clean variant (partner-sim-only screen). Pairs with the partner-trial-readiness discussion + ADR-016 Phase 2 intake. *(s93; ADR-0020 run-1)*
- [ ] **Rock 4 — Cowork deep research DELIVERED → O-sequence locked, O-1 done, O-3 Accepted (s84).** The 4-box + Palantir + agentic research landed (`docs/research/private/2026-06-28-rock4-4box-palantir-agentic-research.md`; ~48 sources, vendor-vs-independent tagged, adversarially balanced; central finding = the evidence asymmetry [bullish ROI all vendor, independent mostly skeptical]) → Cray **locked O-1 → O-3 → O-2 → O-4**. **O-1 (Box-4 ฿ pitch artifact) DONE** (conservative ฿ + impact-ledger mock; `docs/strategy/private/2026-06-28-box4-roi-spine-impact-ledger-pitch.md`). **O-3 = ADR-0025 Accepted** (see Rock 2). **Remaining:** **O-2** (economic-impact facet + Q3 ontology data-binding = Rock 3, after N≥3) · **O-4** (agent-interop North-Star, vision only). [[reference_rock4_4box_palantir_demo_research]]. *(s84 Cray ask)*
- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten (full table: PLAN-0005 §8.1): rule-based recommender → **ADR-010 ACCEPTED (2026-05-22) → PLAN-0006 next** (LLM reasoning hook); minimal approval gate → **ADR-011+** (audit framework — trigger: first design-partner data / PDPA review); no mapping layer → **dbt/SQLMesh** (trigger: first non-synthetic source); hand-authored ORM → **"ORM emitter"** Rule-of-Three candidate (trigger: 3rd vertical / DDL↔ORM parity-test drift); base Postgres only → **PLAN-002** (pgvector/AGE — trigger: semantic + graph features); explicit registry → **ADR-006 D3 L2** (trigger: vertical #2/#3 or `new-vertical` generator). *(per Cray note 2026-05-21)*
- [ ] **Demo card UX — "trust shape", NO operator confidence badge (s74 design, Cray-approved).** For the next demo round's operator recommendation card: show **what / grounded-why / approve gate** + a **"show full reasoning trace" toggle** that reveals the engine-view (where the floor-vs-judge agreement lives, labelled *audit/QA — not the operator*; reuses the scene-6 why-toggle pattern). **No operator-facing confidence badge** — the floor-vs-judge `confidence_signal` (PLAN-0035 Phase 2) is an **engine-internal QA/audit signal kept trace-only (SD-3 option A)**; surfacing it as a badge mis-reads as "the action might be wrong" (it is **not** — member (b) is advisory, never changes the action). The **(B) first-class `verification` envelope field is NOT needed for the operator UI** — reconsider **only** if a future internal audit/QA dashboard wants confidence as a first-class field (trace stays sufficient otherwise). Settled via a show_widget design review (s74; Cray: "ตรงใจ ตอบโจทย์"). The reframe: users want *what was decided · is it right · why* — answered by the action + grounding (real entity, allow-listed handler, deterministic detection, human approve) + the reasoning trace, **not** a self-reported confidence number. *(Trigger: the next demo / UI round; pairs with any (B) reconsideration.)*
- [ ] **PLAN-004 Phase C — OPTIONAL POLISH (forward-declared; "may never land"):** HTML/markdown handoff dashboard under `docs/` + references-graph (mermaid dispatch chains) + `render_transcript.py` unified session export (PLAN-0004 §"Phase C"). *(Phase A + B both COMPLETE — session 35; the prior TODO's validator **warning-swallow bug was FIXED #312**, s58. Minor never-formally-scoped sub-ideas — README/`_rename-map` walk-exclusion, Cat G `references_*` autofix, OQ-2 effective-vs-authored `status:` dashboard flag — fold in only if Phase C lands. Reconciled 2026-06-16 s65 audit.)*
- [ ] **ORM-emitter per-vertical layout (B1-DP-1 follow-up; Cray-deferred s67).** B1 (PLAN-0031, #370) ships the ORM emitter writing energy's ORM to the **committed** `services/db/models.py` (via `code_generator._ORM_COMMITTED_DEST`) — the gitignored `verticals/<ns>/generated/` cannot host a runtime dependency. When a **2nd vertical needs its own ORM** (the Rule-of-Three trigger), decide the per-vertical layout: extend `_ORM_COMMITTED_DEST` to per-vertical committed modules **vs** un-ignore a per-vertical `generated/orm.py` (gitignore negation) + re-export. Premature to design now (one ORM today). *(Cray-deferred 2026-06-18)*
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
