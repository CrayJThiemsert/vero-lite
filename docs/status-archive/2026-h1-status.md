# STATUS.md rotation archive — 2026 H1 (recent window, base file)

> **Period covered:** 2026-07-17 (session-142) → onward (the RECENT window)
> **Sibling chain (letters ascend with time; the base file holds the RECENT window):** [`2026-h1b-status.md`](2026-h1b-status.md) (2026-05-10 → 2026-06-09) → [`2026-h1c-status.md`](2026-h1c-status.md) → [`2026-h1d-status.md`](2026-h1d-status.md) → [`2026-h1e-status.md`](2026-h1e-status.md) → [`2026-h1f-status.md`](2026-h1f-status.md) → [`2026-h1-status.md`](2026-h1-status.md) (base, newest — rotations append HERE). The separate `2026-h1-current-focus.md` (sessions ≤46, ratified as-is) is a Current-Focus-only artifact predating this chain.


Rotated out of `docs/STATUS.md` per the **STATUS.md Rotation Policy**
(`docs/runbooks/memory-architecture.md`, Lesson #23). Tier-3: **grep + windowed reads
only, never a whole-file Read.**

**Split lineage.** At session 80 the combined `2026-h1-status.md` first crossed R4's
~192 KB bar and was split into a recent-window file and its `-b` sibling. The recent
window then grew back to **592,577 B — 3.01x the split trigger and 2.26x the 256 KB
cap** — because R4 had no mechanism: its responsibility-matrix guard column read `—`
where R1 and R7 read `fail`. Session 144 added that mechanism
(`tools/check_archive_size.py`, #789) and this file is one of the four it forced.
**No content lost:** every section is preserved verbatim and exactly once across the
chain, verified by exact list equality at split time, not by a byte-sum estimate.

**Structural note (honest).** R4 describes an archive as TWO sections — rotated
Current Focus blocks and rotated Recent Decisions rows, *newest at top*. That is not
the shape on disk: the file drifted into **one section per reconcile, appended at the
bottom** (27 of them by session 144), and the old preamble's own "Period covered" had
gone stale years of sessions ago. This split preserves the drifted shape rather than
silently rewriting history to match the spec — reconciling R4's text with the real
convention is separate work, deliberately not done here.

---

## Rotated this reconcile (session-142, 2026-07-17 — the three R2 carve-out TODOs discharged, rehome-then-trim, #780/#778/#779)

### Current-Focus block — Session 137 (the `building_materials` 5th vertical Tier-1 Mirror + the `GET /procedures` spec-less fix, #765) [rotated 2026-07-17, session-142 reconcile — 4-session CF window]

> **Session 137, 2026-07-16 (head_commit `45d6b82` → `c52c1ed`) — the 5th
> vertical `building_materials` SCAFFOLDED as a Tier-1 Mirror (ADR-0015 D2)
> for governed customer CREDIT at a mid-market distributor (#765, `feat`),
> from a hand-authored GUESSED OCT-shaped ontology via `vero-lite
> new-vertical`; plus the latent `GET /procedures` 500 the scaffold exposed
> + fixes.** **The reshape is the point:** the monitored **Asset is a
> COMMERCIAL entity** — `CustomerAccount` with its own per-entity
> `credit_limit_thb` band — and **Site is a sales `Branch`** (the ADR-008
> "may extend" precedent procurement already uses), demonstrating the engine
> governs a **commercial** decision, not only a physical asset.
> Strategically this was believed to be the intended **2nd `doa_tier` (money)
> signature** target, advancing the AT-2 Rule-of-Three; but that lands with the
> HERO, not this mirror. _[SUPERSEDED s138/#767: the "N=1 → toward N=2" framing
> was FALSE — AT-2 is N=2 since s131 (PLAN-0074) and the marker re-arms at N=3,
> so a building_materials `doa_tier` would be signature #3 (CI RED, obligates
> the AT-2 extraction), not a step toward N=2; the stale `spec.py:822` comment
> is corrected. Belief-at-the-time kept for lineage per §6.]_ **The bug is the real find:** `GET /procedures` looped
> `registry.verticals()` and called `load_procedures` UNCONDITIONALLY →
> `FileNotFoundError` (500) on the first discovered vertical shipping no
> `procedures.yaml`. `new-vertical` scaffolds exactly that (mirror tier:
> ontology + adapter + handlers, no spec) and ADR-0023 import-scan discovery
> registers it regardless → **the whole read surface died for every OTHER
> vertical the moment a mirror was scaffolded**; the 4 shipped verticals
> never hit it because each hand-authored a spec. **Fix** = an EXPLICIT
> `procedures_path().exists()` skip (deliberately NOT a swallowed
> `FileNotFoundError` — a malformed spec still raises) + a self-cancelling
> regression guard (`test_procedures_skips_discovered_vertical_without_a_spec`)
> that fires if building_materials ever gains a spec. **Scope honesty (NOT
> overclaimed):** Tier-1 Mirror ONLY — **no `procedures.yaml`, no
> governed-credit hero**. The 3-part spine (a deterministic exposure band +
> a hard `rule_gate` for KYC/overdue-AR + `doa_tier` + SoD + audit) is the
> FOLLOW-ON and is what makes the governance real rather than a bare
> approval form; handler = the scaffold's `echo` stub; synthetic data = a
> demo draft; every ฿ value is a marked GUESS; `verticals/*/generated/`
> stays gitignored. **draft≠review≠verify:** Code authored + verified (the
> ontology guess, the fix, the guard); the offline gate + the live mirror
> are the evidence; Cray ratified the vertical choice + the fix approach +
> the merge; this reconcile = `status-scribe` → Code R2. Full offline suite
> **2803 passed / 7 skipped** (2802→2803 = the new guard); ruff + `ruff
> format --check` + `mypy --strict services/` clean. **Live-verified
> end-to-end on the DETERMINISTIC rule path** (the map renders the branch +
> the 250k→550k breach timeline; the anomaly view renders the reasoning
> trace `550000 >= 500000, crossed=true` + the "requires human approval"
> gate) — **no MS-S1 call, no host-state**. **PLAN-0078 Phase 2 is UNTOUCHED
> and still pending** (a separate track — not conflated here). Post-merge:
> main=`c52c1ed`; 0 open PRs; gate PASS (2m48s) + the merge tree verified
> byte-identical to the gate-tested tip `1d523a3` (the CI-is-PR-only hazard
> neutralised); loop-dispatcher DISABLED; MS-S1 idle; dev Postgres UP.
> Commits: `1d523a3` (the scaffold + the `GET /procedures` fix) → `c52c1ed`
> (HEAD, #765 merge).

### Recent Decisions row removed — 2026-07-15 (s133 core — PLAN-0075 AT-2 authority enforcement at the run gate, #749) [rotated 2026-07-17, session-142 reconcile — 10-row RD window]

| 2026-07-15 | **s133 — PLAN-0075 core: AT-2 AUTHORITY ENFORCEMENT AT THE RUN GATE shipped (12/13 ACs, #749, `feat`); closes the s131-surfaced F1 exploit (`task_053edc92`)** — the AT-2 ladder RESOLVED/AUDITED which tier should approve but no run path ENFORCED that the acting approver HELD that role (a junior could resolve the ฿288k/฿2M gate). Fix = `tier_authority.check_tier_authority` at `resolve_gated_step`, additive beside SoD — verified at the LIVE DB gate. **Two Cray-ratified divergences:** cumulative senior roles in YAML (Policy B, overriding Correction 1) + NATIVE-TIER audit routing. Suite **2692 passed / 7 skipped**. Full narrative: the Session-133 CF block (`docs/status-archive/2026-h1-status.md`) | `76f42cc` (HEAD, #749 merge) / `580b9e8`…`9e3d421` (7 core build commits) / `services/**` (`tier_authority.check_tier_authority` + `resolve_gated_step` wiring + F3 load check + gate-time audit reconciliation) + `verticals/{procurement,supply_chain}/**` (cumulative-role YAML + `native_approver`) + `tests/**` (AC-5/6/7/8 + live DB gate) + `docs/plans/0075-*.md` (OPEN, 12/13 ACs) |

### Current Focus block removed — Session 138, 2026-07-16 (PLAN-0078 Phase 2 PR-3 — severity re-sequenced into a declared `enrich` transform, #768; + the AT-2 misinformation-KILL / PLAN-0078 doc-drift reconcile, #767) [rotated 2026-07-17, session-143 reconcile — 4-session CF window]

> **Session 138, 2026-07-16 (head_commit `c52c1ed` → `9a5eecf`) — PLAN-0078
> Phase 2, PR-3 shipped: cold-chain excursion SEVERITY re-sequenced off the
> `ColdChainAssessExecutor` stamp into a declared `enrich` transform (#768,
> `feat`, oracle-first); plus a docs-only AT-2 misinformation-KILL + PLAN-0078
> doc-drift reconcile (#767).** **PR-3 (the marquee, #768):** the non-money
> authority the `severity_tier` gate routes on now derives in a governed
> `enrich` transform (ADR-0031 D3 row-1) — `_DOSE_LADDER` becomes a governed
> datum IN THE PIN instead of a code constant, the move that makes retiring
> `derivation_hash` honest in PR-5. **Oracle-first (L-2):** `8214a32` froze
> `test_severity_transform_parity.py` GREEN against the executor-stamped world
> (4 passed/1 skipped), then `e6fb07a` flipped and the SAME oracle stayed green
> unchanged (5 passed) — proving the ratified **SD-6 two-tier bar**: (i)
> output-row byte parity (excursion_severity="critical" + criticality="1" +
> every Phase-1 field); (ii) semantic run-record equivalence (scored
> lane-licensed-destruction / 63000.000 THB, GDP gate, severity_tier
> critical→ผอ.ฝ่ายคุณภาพ/appr-qdir, run status); (iii) VALUE-level provenance
> completeness (the ratified **OQ-5** — dose_ch/ratio materialized so the record
> answers "why CRITICAL?" WITHOUT re-running the pinned spec). **SD-7** =
> `ColdChainAssessExecutor` SLIMMED to its fail-closed scalar guard (the grammar
> can't express positivity; a negative ratio bands fail-DANGEROUS). **OQ-6** =
> EXTEND the enrich step (executor's call — a separate step would break the
> PLAN-0074 structural test in `test_cold_chain_disposition.py`).
> **AC-9 (L-6):** `governance_step.py` absent from the diff entirely
> (`_severity`/`_spend` byte-untouched). **Honest interim redundancy
> (disclosed):** `_DOSE_LADDER` / `derive_excursion_severity` / the
> derivation_hash provider stay in code until PR-5 — **F-PIN stays OPEN, nothing
> records it closed**. **The #767 companion (docs-only, NO behavior change):**
> s137 planned a building_materials `doa_tier` as "the 2nd money signature
> (N=2) advancing AT-2" — a FALSE premise. Grounded (next-work-analyst + 4
> Explore agents, Code-reverified on disk): ADR-0025 D7 counts AT-2-class
> procedures with NO per-`gate_kind` partition → **N has been 2 since s131**
> (supply_chain severity_tier, PLAN-0074); the D7 re-trigger already FIRED + was
> ANSWERED (generator stays deferred, D2 types stay instance-scoped); the marker
> `test_at2_signature_retrigger.py` re-arms at **N=3** — so a
> building_materials doa_tier would be signature #3, turning CI RED + OBLIGATING
> the AT-2 extraction, NOT "advancing toward" it. Root cause = stale code
> comments in `spec.py` (the 2nd Lesson #0030 instance, this time a code comment
> the drafter point-8 backstop does NOT cover) + a `main.py` docstring; all
> corrected from the marker's OWN docstring (quoted, not inferred). Same PR
> reconciled PLAN-0078 doc-drift (4 "Phase 2 gated on SD-6" body sections — all
> SD-1..SD-8 ratified 2026-07-15; Phase-1 AC-1..AC-4 ticked, AC-5/AC-6
> deliberately NOT; scored_rule anchors re-verified) and recorded **OQ-5
> RATIFIED by Cray 2026-07-16 via AskUserQuestion: (a) materialize**.
> **draft≠review≠verify:** Code authored + verified both PRs (oracle-first for
> #768; every #767 claim Code-reverified on disk, catching 2 subagent errors);
> the finding came from next-work-analyst grounding; Cray ratified OQ-5 +
> merged. Full offline suite **2808 passed / 7 skipped** (2803→2808 = +5 the new
> parity module, zero regressions); ruff + `ruff format` + `mypy --strict`
> clean; deterministic-offline (no MS-S1 / host-state). **Flagged (NOT
> touched):** `spec.py`'s "no principal/role-rank model exists yet" comment is
> suspect post-PLAN-0075 (a possible missed 580b9e8 truth-pass site).
> Post-merge: main=`9a5eecf`; 0 open PRs; **PLAN-0078 stays `Status:
> Proposed`** (never flip-then-edit; PR-4 amount re-seq next); loop-dispatcher
> DISABLED; MS-S1 idle; dev Postgres UP. Commits: `120521e` (#767 docs) →
> `c9e5186` (#767 merge) → `8214a32` (PR-3 oracle) → `e6fb07a` (PR-3 flip) →
> `9a5eecf` (HEAD, #768 merge).

### Recent Decisions row removed — 2026-07-15 (s135 close-out — PLAN-0077 transform-grammar build COMPLETE, #754→#758) [rotated 2026-07-17, session-143 reconcile — 10-row RD window]

| 2026-07-15 | **s135 close-out — PLAN-0077 "transform-grammar build" COMPLETE (5 PRs #754→#758: Proposed → Phase A → B → C → #758 L-8 landing); renders ADR-0031 D3 row-1 + ADR-016 Q4 OQ-3, NO new ADR (arc spans s134-135)** — the typed anti-eval `derive` transform grammar shipped, load-gated + execution-bound for the shipped op-set (93 AC tests). **Honest residual: the two verticals' seeds stay execution-bound ✖; the marquee stamps stay code-side (SD-1); `derivation_hash` in service; F-PIN stays OPEN** — flipping those = the separate seed-migration PLAN. Full narrative: the Session-135 CF block (`docs/status-archive/2026-h1-status.md`) | `ece270a` (HEAD, #758 L-8 landing) / `8808902` (#757 C) / `d94a10d` (#756 B) / `e93e9d0` (#755 A) / `3e6ee4d` (#754 Proposed) / `services/engine/procedures/transform_step.py` + `docs/plans/done/0077-*.md` |

### Recent Decisions row removed — 2026-07-15 (s133 close-out — PLAN-0075 COMPLETE + PLAN-0076 filed as the standing tracker, #751/#752) [rotated 2026-07-17, session-143 reconcile — 10-row RD window]

| 2026-07-15 | **s133 close-out — PLAN-0075 COMPLETE (all 13 ACs) + CLOSED → `done/`; AC-13 derivation provenance shipped (#751, `feat`); PLAN-0076 filed as the STANDING follow-on TRACKER (#752, `Status: Tracking`)** — AC-13 hashes supply_chain's severity derivation into the run governance pin via a per-vertical `registry.derivation_hash` hook; **PROVENANCE-ONLY** (mid-flight tamper-evidence — **F-PIN stays OPEN**). PLAN-0076 homes the 2 PLAN-0075 deferrals (F-PIN remainder + the ADR-0031 D3 / F-FACTORY seam) behind an AC-6 presence guard-test ("location≠tripwire; failing tests are the real anti-rot"). Full narrative: the Session-133 close-out CF block (`docs/status-archive/2026-h1-status.md`) | `fac77c7` (HEAD, #751 merge) / `4a682ab` (#752) / `0520fb2` (AC-13 feat) / `docs/plans/done/0075-*.md` + `docs/plans/0076-*.md` + `tests/services/engine/procedures/test_at2_followon_tracking_guard.py` |

> **Lineage note (added at the s143 reconcile).** The s133 row above records
> AC-13's ARRIVAL; the s143 Recent-Decisions row records its RETIREMENT
> (PLAN-0078 PR-5, `#784`) — the reasoning lineage is intact across this
> archive boundary. AC-13 was not an error: it was the right call for the world
> it shipped into, where the derivation lived in code and the pin could not
> reach it. PLAN-0078 changed that world, and the workaround retired with the
> reason for it.

## Rotated this reconcile (session-144, 2026-07-17 — the PLAN-0078 Step-7 closeout, 12/12 ACs → `done/`, #786)

### Current Focus block removed — Session 140, 2026-07-16 (the 4-artifact strategic-continuity program COMPLETE 4/4 — ADR-0032 + PLAN-0079 + the CLAUDE.md §2 pointer + the STATUS pointer, #770/#771/#773/#772) [rotated 2026-07-17, session-144 reconcile — 4-session CF window]

> **Session 140, 2026-07-16 (head_commit `9a5eecf` → `0523d88`) — the
> 4-artifact STRATEGIC-CONTINUITY program COMPLETE 4/4 (docs + one guard test
> only, ZERO code behaviour change): #770 ADR-0032 Accepted · #771 PLAN-0079
> `Status: Tracking` · #773 the CLAUDE.md §2 direction pointer · #772 the
> STATUS pointer (PLAN-0079 AC-4); #769 unblocked the lane.** **Why the
> program exists:** the s137
> strategic arc lived ONLY in private auto-memories + gitignored
> `docs/research/private/` — so a parallel session planned BLIND against it,
> and the `building_materials` governed-credit HERO sat in **NO backlog at
> all**; the program moves the frame into tracked, greppable artifacts.
> **(1) #770 → ADR-0032 Accepted** (`5b53bbe`, merge `4a5cfb7`; drafted s139):
> **D1** the demo→pilot wedge (guess-then-react, zero data at first contact, an
> offline arm, a 1-KPI charter) · **D2** the 3-shape roadmap + a **BINDING
> pilot gate** (a shape-2/shape-3 PLAN must cite a live pilot or record Cray's
> explicit in-session override) · **D3** shape-2 = governed self-improvement,
> NOT autonomous · **D4** shape-3 = PARK + the moat rule · **D5** positioning
> ("governed = AI-ready today"; NEVER "AGI-ready" to an ops buyer) · **D6**
> qualify by SHAPE not domain + the AT-2 **cost class** split. It also **pins
> the AT-2 fact record** (N=2; D7 fired at N=2; the re-eval was performed; the
> marker re-arms at N=3) — which is what makes the s138-killed stale-count
> error class hard to REINTRODUCE. **(2) #771 → PLAN-0079 `Status: Tracking`**
> (`ad40aef`, merge `754a894`; drafted s139) — homes the `building_materials`
> governed-credit HERO **with its honest cost**; builds and schedules NOTHING.
> Ships its AC-2 half-(i) presence guard-test
> (`test_governed_credit_hero_tracking_guard.py`). **(3) #773 → the CLAUDE.md
> §2 pointer** (`038efd0`, merge `0523d88` = HEAD) — §2 retitled "Current
> Focus" → **"Direction & Current Focus"** and given a two-pointer signpost:
> **standing direction = ADR-0032** (the D1 demo→pilot wedge · the D2-D4
> 3-shape roadmap + its BINDING pilot gate · the D5-D6 positioning + fit-filter
> discipline, plus a "read it before planning anything strategic" activity
> gate) alongside **current state = `docs/STATUS.md`**, with an explicit
> **"state never overrides direction — §1 precedence"** note. **Scope was CUT
> at Cray's ratification:** the originally-planned "sanitized strategy doc" was
> DROPPED once Code surfaced that ADR-0032's own §"Public-repo boundary"
> already carries the public frame + path-only private refs, and that
> **ADR-0032 OQ-2 had already RESOLVED "not yet"** on any derived doc
> ("Rule-of-Three applies to docs too") — a no-precedence restatement of a
> canonical is itself a drift surface (§1 / ADR-0017 D6), the exact error class
> this program exists to kill. **Artifact 3 = the §2 pointer ONLY.** **(4)
> #772** = the PLAN-0079 **AC-4** Active-TODO pointer + its armed guard (its
> SD-3 timing question, resolved by shipping it). **Enabler → #769, the s138
> STATUS reconcile** (`437369e`, merge `8ca772b`) — a PARALLEL session's PR,
> BEHIND `main`; Code updated its branch via the GitHub API (`PUT
> /pulls/769/update-branch`), the gate re-ran green on the up-to-date tip
> `8e798db`, then it merged — **which unblocked STATUS**, and is the only
> reason artifact 4 could land.
> **draft≠review≠verify:** ADR-0032 + PLAN-0079 = `plan-drafter` authored →
> Code R2 → Cray ratified + merged; the §2 text = **Cowork authored** (ADR-009
> D1) → Code R2 + applied + committed (D2) — neither drafting agent may write
> `CLAUDE.md` (Cowork tier-forbidden, `plan-drafter` hook-denied), so "Cowork
> drafts the text, Code applies" is the only coherent reading; Code's R2 KEPT
> the D-number parentheticals against Cowork's drift flag (a stable Accepted
> ADR's structural labels ≠ a world-tracking COUNT like the #767 "N=1" comment;
> mapping re-verified against `0032:93-202`) and cleared the retitle by grep
> (zero referents); this reconcile = `status-scribe` → Code R2. Full offline
> suite **2810 passed / 7 skipped**; docs + one guard test only — no
> `services/` change, deterministic-offline (no MS-S1 / host-state). **The
> direction now lives in THREE places that cannot silently vanish:** the ADR
> (read at every session start), the STATUS Active-TODO pointer (guard-test RED
> if pruned), and `CLAUDE.md` §2. Post-merge: main=`0523d88`; 0 open PRs;
> loop-dispatcher DISABLED; MS-S1 idle (up but COLD — zero calls this session);
> dev Postgres UP. Commits: `5b53bbe` (#770 ADR-0032) → `4a5cfb7` (#770 merge)
> → `ad40aef` (#771 PLAN-0079) → `754a894` (#771 merge) → `437369e` (#769 s138
> reconcile) → `8ca772b` (#769 merge) → `1ad9d88` (#772 reconcile) → `f450042`
> (#772 merge) → `038efd0` (#773 CLAUDE.md §2) → `0523d88` (HEAD, #773 merge).

### Recent Decisions row removed — 2026-07-16 (s136 — PLAN-0078 Phase 1 COMPLETE, the intake seed-migration pair, #762/#763) [rotated 2026-07-17, session-144 reconcile — 10-row RD window]

> **Archivist's note (session-144).** The row below cites
> `docs/plans/0078-*.md` in its reference column. That PLAN moved to
> `docs/plans/done/0078-transform-seed-migration.md` in the very reconcile that
> rotated this row (session 144, #786). The citation is preserved **verbatim as
> removed**: an archive is a historical record, and the path was accurate when
> written. The lineage is intact across the boundary — this row records Phase 1
> ARRIVING with the honest residual ("the marquee severity/amount STAMPS stay
> code-side, `derivation_hash` in service, F-PIN stays OPEN — that is Phase 2"),
> and the s144 Current Focus block records the arc CLOSING at 12/12 ACs. Every
> residual this row names was discharged by PR-3/PR-4/PR-5 except **F-PIN,
> which remains OPEN by construction** (PLAN-0078 L-4) — no artifact anywhere
> records it closed, and PLAN-0076 stays un-archived on its T1 for the same
> reason.

| 2026-07-16 | **s136 — PLAN-0078 Phase 1 COMPLETE (the intake seed-migration pair, oracle-first, SD-1=(B) arc; 2 `feat` PRs #762/#763 atop a Step-1 uniform-factory landing `d8707ca`): the intake enrichment migrated off the hand-coded seeds into declared `enrich` TRANSFORM steps (ADR-0031 D3 row-1 grammar)** — PR-1 #762 procurement intake + PR-2 #763 supply_chain disposition intake, each oracle-first with a FROZEN parity reference green PRE-flip → byte-equal POST-flip. **Honest residual: the marquee severity/amount STAMPS stay code-side, `derivation_hash` in service, F-PIN stays OPEN** — that is Phase 2. Suite **2802 passed / 7 skipped**. Full narrative: the Session-136 CF block (`docs/status-archive/2026-h1-status.md`) | `45d6b82` (HEAD, #763 PR-2 supply_chain) / `173d869` (#762 PR-1 procurement) / `d8707ca` (Step 1 uniform factory) / `verticals/{procurement,supply_chain}/**` (declared `enrich` transform seeds) + `tests/**` (oracle-first parity harnesses + AC-4/5/6) + `docs/plans/0078-*.md` (Phase 1 COMPLETE, Phase 2 open) |

## Rotated this reconcile (session-145, 2026-07-17 — the full-body reconcile of the `d8db032` → `ce0f0a1` window: the R4 arc closed end to end, #789/#791/#792)

### Current Focus block removed — Session 141, 2026-07-17 (PLAN-0078 Phase 2 PR-4 — the marquee ฿ spend migrated to a declared transform, #775) [rotated 2026-07-17, session-145 reconcile — 4-session CF window]

> **Session 141, 2026-07-17 (head_commit `0523d88` → `88e6e11`) — PLAN-0078
> Phase 2 PR-4 COMPLETE (#775, `feat`, oracle-first): the marquee ฿ spend
> migrates from an execution-bound stamp ✖ to a declared `transform` ✔ per the
> ratified SD-8 = (a) ONE DERIVATION HOME — `_scored_rule` stops multiplying
> and stamps the two FACTORS; a declared `derive_spend` transform multiplies
> them after ALL FOUR shipped scored_rule steps (procurement ×3 + supply_chain
> `assess`).** **Oracle-first (L-2), two commits:** `fc17d02` froze
> `test_amount_transform_parity.py` (12 tests, cross-vertical) GREEN against
> the stamped world → `88e6e11` flipped and the SAME oracle stayed green
> **UNCHANGED**. **Non-vacuous by construction:** post-flip nothing stamps
> `amount`, so a transform that failed to run would `KeyError`. Frozen:
> procurement `96000 × 3 = "288000"` → the [50k,500k) tier → ผจก.จัดซื้อ →
> `appr-pm`; supply_chain `150.00 × 420.0 = "63000.000"` (Decimal PRESERVES
> scale 2+1→3 — the BYTE form is pinned, not the value); anchored on the row
> the AUTHORITY GATE reads (procurement `compliance`, supply_chain `gdp_gate`)
> — downstream of BOTH amount homes, so it holds in either world. **A
> ratified-SD refinement, Cray-ratified in-session:** SD-8(a) specified
> stamping `selected_unit_price` ONLY ("qty already rides the entity") — that
> was REFUTED by grounding: `_quantity` (`governance_step.py:128`) resolves
> `qty` → `quantity` → `1`, a fallback the grammar's `default` op CANNOT
> express (its `value` is a literal, `spec.py:520-521`), so a transform
> re-reading a bare `qty` would silently multiply by 1 on a `quantity`-only
> row → lower amount → LOWER doa_tier → under-approval: **fail-DANGEROUS, not
> fail-closed** (inert today; both verticals carry `qty`). Cray ratified
> **stamp `selected_qty`** over `default: {target: qty, value: 1}` — the
> transform multiplies what `_quantity` already resolved, so divergence is
> unrepresentable and `_quantity` stays the ONE resolution home. **AC-9 proven,
> not asserted:** `_spend` / `_severity` / `EXCURSION_SEVERITY_FIELD` /
> `_quantity` / `_candidate_quotes` / `_event_criticality` are BYTE-IDENTICAL
> to main — by AST source-segment extraction + SHA256, because PR-3's proof
> (the file absent from the diff) is unavailable to PR-4, which edits
> `_scored_rule` in that same file. **SD-6(ii)** licensed the audit-form change
> (the projection carries the two factors + `currency` top-level — they rode
> inside the retired `amount` map — in place of the product; verdicts
> identical). **Honest scope creep (2 files the PLAN's 8-12 estimate missed):**
> `test_procurement_vertical.py` + `test_procurement_sod_gate.py` seed no
> `candidate_quotes` and stub `source`, so the real scored_rule never ran and
> nothing consumed the ฿ — unavoidable under SD-8(a) (a declared step under
> `source` makes any harness that stubs `source` away incoherent). **A
> PLAN-0075 debt closed in passing:**
> `test_procurement_requester_cannot_self_approve` was the ONE test AC-8 left
> on the plain-executor bypass (its 2 siblings were migrated, their docstrings
> say so) — re-harnessed onto `seed_operate_waiting_human_run`, dead cluster
> removed. Plus a **PR-3 honesty gap** on the step PR-4 touches: supply_chain
> `assess` still claimed it "derives the excursion severity" — `enrich` has
> owned it since PR-3. draft≠review≠verify: Code authored + verified
> (oracle-first); Cray ratified the `selected_qty` refinement + merged; this
> reconcile = `status-scribe` → Code R2. Full offline suite **2822 passed / 7
> skipped** (2810 + the oracle's 12); ruff check + format clean; merge-tree
> parity verified (`git diff 88e6e11 09714ea` empty); deterministic-offline (no
> MS-S1 / host-state / DB). **PLAN-0078 stays `Status: Proposed`** (never
> flip-then-edit). **PR-5 is NOT blocked by PR-4** — its dependency was PR-3,
> which landed: `derivation_hash` retirement + F-PIN marker rewrite +
> PLAN-0076 T2 close. Post-merge: main=`09714ea`; 0 open PRs; loop-dispatcher
> DISABLED; MS-S1 idle; dev Postgres UP. Commits: `fc17d02` (oracle) →
> `88e6e11` (flip) → `09714ea` (#775 merge, HEAD).

### Recent Decisions row removed — 2026-07-16 (s137 — the 5th vertical `building_materials` scaffolded as a Tier-1 Mirror + the `GET /procedures` spec-less 500 fix, #765) [rotated 2026-07-17, session-145 reconcile — 10-row RD window]

> **Archivist's note (session-145 reconcile).** The row below ends
> `Full narrative: the Session-137 CF block above`. That pointer was already
> **stale in place before this rotation**: the s137 CF block was itself rotated
> out at the session-142 reconcile, so "above" stopped resolving then, and the
> s144 R4 split subsequently moved the block into this chain. The row is
> preserved **verbatim as removed** — R4 is move-never-rewrite, and the text was
> accurate when it was written. To find the block: **grep
> `docs/status-archive/`, not a filename** — which file holds it is an artifact
> of where the ~192 KB bar fell (the naming rule + this exact caveat are now
> canon in `docs/runbooks/memory-architecture.md` §R4, recorded by #792). This
> is the second archivist's note in this archive for the same cause; the rule
> exists so there need not be a third.

| 2026-07-16 | **s137 — the 5th vertical `building_materials` scaffolded as a Tier-1 Mirror (ADR-0015 D2) for governed customer CREDIT (#765, `feat`), from a hand-authored GUESSED OCT-shaped ontology; + the latent `GET /procedures` 500 it exposed + fixed** — the reshape is the point: the monitored Asset is a COMMERCIAL entity, so the engine governs a **commercial** decision, not only a physical asset _[the "2nd `doa_tier` signature" framing SUPERSEDED s138/#767: AT-2 is N=2 since s131, so this would be signature #3]_. **The bug (the real find):** `GET /procedures` called `load_procedures` UNCONDITIONALLY → a scaffolded mirror with no `procedures.yaml` 500'd the read surface for EVERY vertical; fix = an explicit `procedures_path().exists()` skip + a self-cancelling guard. **Scope honesty: Tier-1 Mirror ONLY — no spec, no governed-credit hero.** Suite **2803 passed / 7 skipped**. Full narrative: the Session-137 CF block above | `c52c1ed` (HEAD, #765 merge) / `1d523a3` (scaffold + fix) / `verticals/building_materials/**` (guessed OCT ontology + adapter + `echo` handlers, no spec) + `services/api/**` (`GET /procedures` exists-skip) + `tests/**` (`test_procedures_skips_discovered_vertical_without_a_spec`) |


## Rotated this reconcile (session-146, 2026-07-17 — PLAN-0080 shipped end to end, #794 trace attribution + #795 ui.md)

### Current-Focus block — Session 142 (the three R2 carve-out TODOs discharged, rehome-then-trim, #780/#778/#779) [rotated 2026-07-17, session-146 reconcile — 4-session CF window]

> **Session 142, 2026-07-17 (head_commit `88e6e11` → `303fd48`) — the THREE
> R2 carve-out TODOs DISCHARGED in one program (#780 + #778 + #779, docs-only,
> ZERO behaviour change): each fact REHOMED into a tracked home FIRST, THEN the
> TODO trimmed to a pointer.** s141's terseness pass ratified the carve-out —
> _"an item whose facts live nowhere else in git … is left at full length until
> it is rehomed"_ — and left **three** items byte-untouched under it. **The
> order is the safety property:** trimming first would have DELETED the fact
> from the repository, which R4 forbids. **The lesson worth recording: the three
> homes are deliberately DIFFERENT IN KIND — rehome into the artifact whose
> READER needs the fact, not whichever doc is nearest.**
> **(1) #780 (`12e69aa`) — Rock 4's evidence-asymmetry finding →
> `docs/adr/0025-at2-managerial-layer.md:23-29`:** the bullish ROI numbers for
> this product category are almost all **vendor-authored**; the independent
> evidence is **mostly skeptical** — the single most decision-relevant
> conclusion of the ~48-source s84 research, and it bears on **how vero-lite
> pitches ROI to a design partner**. It existed in git in exactly ONE place (the
> STATUS TODO); elsewhere only in **gitignored** `docs/research/private/`. The
> 3-tag provenance taxonomy is preserved (`[VENDOR-CLAIM]` /
> `[VENDOR-COMMISSIONED]` / `[INDEPENDENT]` — the middle tag is the trap: an
> "independent author" is NOT independent evidence when the funding is the
> vendor's and the "customer" is a modeled composite). Public-repo boundary held
> per the ADR-0032 precedent: strategic frame only, private research cited **by
> path only**. Framed as the evidence base explaining why the house's
> conservative, customer-calibrated ROI posture is correct — **NOT a new
> decision** (Status/Date/Ratified/Related untouched; no D1-D8 / LOCKED / OQ
> touched). ADR-0025 is **Accepted** → the body edit was **G1-gated** →
> `plan-drafter` authored, Code R2'd. Same PR **dropped** the dangling
> `[[reference_rock4_4box_palantir_demo_research]]` token (a repo-wide grep hit
> only the STATUS line itself — it pointed at a private Tier-0 auto-memory,
> resolving nowhere for any reader) for the tracked ADR-0025 anchor.
> **(2) #778 (`37ab124`) — the monotonic `sequence`-column deferral → the module
> docstring of `tests/services/db/test_load_run_ordering_guard.py`** (+ a pointer
> at each of the two wall-clock code sites,
> `services/engine/procedures/persistence.py` `suspended_step_result` and
> `services/api/routers/runs.py` `list_runs`). Four facts had no other home (the
> ROOT-fix framing, the needs-a-migration/own-PLAN sizing, the "unchanged by
> design → the deferral STANDS" verdict, the DISPLAY-ONLY tolerability
> argument). **Ordering behaviour unchanged — docstring/comment-only; the
> deferral explicitly STANDS.**
> **(3) #779 (`303fd48`) — the s74 demo-card decision →
> `docs/plans/done/0035-governed-action-verify-reshape-build.md:576`**, a dated
> **post-archival amendment** at **SD-3** (the very question that PLAN had left
> open), plus **re-pointing ADR-0030's six `STATUS.md:262` citations** at that
> amendment. **The durable corollary, now in the runbook: an ADR citing
> `STATUS.md:<line>` is a DEFECT, not a citation** — it inverts §1 (STATUS is
> state, never a rule) AND rots by construction (that ref was written at `:262`
> and had drifted to `:319`). **`docs/runbooks/memory-architecture.md` R2
> updated** (across #780 + #779): the carve-out clause now records that **"until
> it is rehomed" is a REAL EXIT — the carve-out defers a trim, it does not grant
> permanent tenure**, with the ordering rule **rehome → re-point the citers →
> verify → trim**, all three s142 discharges as worked examples, and the
> `STATUS.md:<line>` corollary. **Why the PRs interleave:** #778 and #779 were
> opened ~7h earlier by **parallel s142 sessions** working the same program
> unaware of each other; #780 merged first and **broke both** (archive-tail + a
> near-duplicate runbook clause). Code resolved both by **merging main in** (no
> force-push, no rewriting another session's history): #778's archive section
> renumbered **part 3 → part 4** (content untouched), and the two near-duplicate
> runbook bullets **consolidated into one** carrying all three worked examples
> rather than stating one rule twice. **draft≠review≠verify:** `plan-drafter`
> authored the G1-gated ADR-0025 edit; Code R2'd + verified + merged; this
> reconcile = `status-scribe` → Code R2. Full offline suite **2822 passed / 7
> skipped** on `303fd48` (the merge commit itself, not just the PR); `mypy
> --strict` not re-run (docs-only work). **Active TODOs left byte-untouched** —
> all three items are already correctly trimmed to pointers on `main`.
> Post-merge: main=`303fd48`; 0 open PRs; loop-dispatcher DISABLED; MS-S1
> idle/COLD — zero calls this session. Commits: `12e69aa` (#780, the ADR-0025
> rehome) → `37ab124` (#778 merge) → `303fd48` (HEAD, #779 merge).

### Recent-Decisions row — s138 #767 (the AT-2 `N=1` misinformation-KILL + PLAN-0078 doc-drift reconcile) [rotated 2026-07-17, session-146 reconcile — 10-row window]

| 2026-07-16 | **s138 — the AT-2 `N=1` misinformation-KILL + PLAN-0078 doc-drift reconcile (#767, docs-only, NO behavior change): s137's planned building_materials `doa_tier` as "the 2nd money signature (N=2) advancing AT-2" was a FALSE premise — corrected at the source.** ADR-0025 D7 counts with no per-`gate_kind` partition → **N has been 2 since s131**; the marker re-arms at **N=3**, so the hero would be signature #3 → CI RED + OBLIGATING the AT-2 extraction, NOT "advancing toward" it. Root cause = stale `spec.py`/`main.py` comments, all corrected. Same PR reconciled PLAN-0078 doc-drift + recorded OQ-5 RATIFIED (a). Full narrative: the Session-138 CF block (`docs/status-archive/2026-h1f-status.md` — moved there by the s144 R4 split; grep the archive dir, not one file) | `c9e5186` (#767 merge) / `120521e` (docs(procedures) comment/docstring truth-pass) / `9b19f19` (docs(plans) PLAN-0078 drift reconcile + OQ-5) / `services/**` (`spec.py` :822/:1046/:1092 + `main.py:133` corrected) + `docs/plans/0078-*.md` (Phase-1 ACs ticked, OQ-5 RATIFIED) |

### Current Focus block — Session 143 (PLAN-0078 PR-5 #784, the final transform-seed-migration PR) [rotated 2026-07-18, session-148 reconcile — 4-newest-sessions window]

> **Session 143, 2026-07-17 (head_commit `303fd48` → `6eea264`) — PLAN-0078
> PR-5 SHIPPED (#784, `refactor`), the FINAL PR of the transform
> seed-migration: the PLAN-0075 AC-13 `derivation_hash` RETIRED end-to-end,
> the F-PIN marker rewritten, PLAN-0076 Step T2 CLOSED — plus two docs-only
> siblings reconciled in the same pass (#783 the R7 citation guard; #782
> Lesson #0031, merged back in s142 but never reconciled).** **Why PR-5 was a
> DELETION PR — that IS the point:** AC-13 hashed supply_chain's
> severity-ladder CONSTANTS into every run's governance snapshot via a
> per-vertical registry hook, for exactly ONE reason — the derivation lived in
> vertical CODE, where a snapshot of the DECLARATION could not reach it. PR-3
> declared the ladder; PR-4 declared the ฿ spend; **the reason vanished, so
> the workaround went.** The per-step `transform` key now pins the governing
> datum directly. Retired across 8 files: the provider, its registration, the
> registry seam (type + `_VerticalEntry` field + register/pull), the
> `governance_pin` parameter on both entry points, and the pass-through kwarg
> — **AC-10 grep-clean, 0 hits outside `docs/`**. **Both guarantees the
> retired suite bought are re-homed at FULL strength:** the replacements drive
> `assert_governance_pin` to an ACTUAL raise (not an `h1 != h2` hash compare),
> including the unbounded top band (the AC-13 drafter finding, preserved in
> declared form). **Two Cray s143 ratifications, both OVERRIDING a drafter
> recommendation:** (1) AC-11's "assert `derivation_hash` is None" is
> UNRENDERABLE alongside AC-10's grep-clean — asserting a hook returns None
> requires the hook to EXIST; Cray ruled: rewrite the marker with NO reference
> to the retired name. (2) `_DOSE_LADDER` / `_TOP_SEVERITY` /
> `SeverityDerivation` / `derive_excursion_severity` are KEPT as a test-only
> reference (the PLAN contemplated retiring them) — their docstrings now say
> so plainly, and the yaml bands are asserted independently + hand-written, so
> the two copies cannot drift together. **The session's reusable finding — the
> `goal-evaluator` subagent caught TWO real defects the author missed:** (i)
> the first draft deleted the "key is present" assertion WITHOUT adding its
> inverse, leaving supply_chain's config-hash change SILENTLY ABSORBED —
> exactly what AC-5/AC-10 forbid; fixed by an exact-snapshot-key-set
> assertion, strictly STRONGER than absence-of-one-name. (ii) a PR-3 forward
> reference ("PR-5 reshapes this module to retire the constants") that PR-5
> itself FALSIFIED via Cray's keep ruling (`70d25a5`). **Honest residual:
> F-PIN is NOT closed** (PLAN-0078 L-4) — only T2's remainder fold-in closed;
> **PLAN-0076 does NOT archive** — T1 (F-FACTORY) stays open, its AC-6
> guard-test stays ARMED. **The two siblings:** **#783** (`3bf99bc`) —
> rotation policy **R7** is now BINDING
> ([`memory-architecture.md`](runbooks/memory-architecture.md)): **never cite
> `docs/STATUS.md` by line number** — cite the tracked artifact, or STATUS by
> SECTION NAME. Rule → tripwire → cleanup, IN THAT ORDER: an `always_run`
> `status-citation-guard` hook (17 tests) + the 10 rotted sites cleaned;
> RED→GREEN proven on the real repo (10 → 0). **#782** (`bc42136`, merged
> s142, reconciled HERE) — Lesson #0031 + the `fan-out-dispatch` skill:
> **split parallel work on the WRITE-SET, not the idea** — the post-mortem of
> three s142 chip sessions whose write-sets collided, costing 3 hand-resolved
> merge commits. **Verification:** full
> offline suite **2840 passed / 7 skipped**, re-run by Code on the merge
> commit `6eea264` ITSELF (CI is PR-only — the merge commit is never
> CI-tested); delta accounted exactly: 2823 (PR-5 branch) + 17 (#783's new
> module); ruff + `ruff format` + mypy clean; R7 guard green;
> deterministic-offline throughout — zero MS-S1 calls, no host-state action.
> Commits: `9cd64d5` → `84f261f` → `bc42136`
> (#782 merge) → `abd41d4` → `3bf99bc` (#783 merge) → `732fc0a` (PR-5 retire)
> → `6e6ec7a` (PLAN-0076 T2) → `70d25a5` (PR-3 forward-ref fix) → `6eea264`
> (HEAD, #784 merge).

### Recent-Decisions rows — s140 strategic-continuity program (#769/#770/#771) + s138 PLAN-0078 PR-3 (#768) [rotated 2026-07-18, session-148 reconcile — 10-row window]

| 2026-07-16 | **s140 — the 4-artifact STRATEGIC-CONTINUITY program CLOSED (3 PRs; docs + one guard test, ZERO behaviour change): ADR-0032 Accepted (#770) — the demo→pilot wedge + 3-shape roadmap + a BINDING pilot gate + the PINNED AT-2 fact record (N=2, re-arms at N=3) · PLAN-0079 `Status: Tracking` (#771) — the governed-credit HERO homed with its honest cost, builds NOTHING · the s138 reconcile unblocked (#769) · this AC-4 pointer.** Cause: the s137 arc lived only in auto-memories + gitignored docs, so a parallel session planned BLIND. Suite **2809 passed / 7 skipped**. _[Artifact 3 landed as #773 — see the row above.]_ Full narrative: the Session-140 CF block above | `8ca772b` (HEAD, #769) / `754a894` (#771) / `ad40aef` (PLAN-0079) / `4a5cfb7` (#770) / `5b53bbe` (ADR-0032) / `docs/adr/0032-*.md` + `docs/plans/0079-*.md` + `tests/services/engine/procedures/test_governed_credit_hero_tracking_guard.py` |
| 2026-07-16 | **s138 — PLAN-0078 Phase 2 PR-3 COMPLETE (#768, `feat`, oracle-first): cold-chain excursion SEVERITY re-sequenced off the `ColdChainAssessExecutor` stamp into a declared `enrich` transform (ADR-0031 D3 row-1) — `_DOSE_LADDER` becomes a governed datum IN THE PIN, the move that makes retiring `derivation_hash` honest in PR-5.** Proved the ratified SD-6 two-tier bar; SD-7 slimmed the executor to its fail-closed guard; OQ-5 ratified (a) materialize. **Honest interim redundancy stays in code until PR-5 — F-PIN stays OPEN.** Suite **2808 passed / 7 skipped**. **PLAN-0078 stays `Status: Proposed`**. Full narrative: the Session-138 CF block (`docs/status-archive/2026-h1f-status.md` — moved there by the s144 R4 split; grep the archive dir, not one file) | `9a5eecf` (HEAD, #768 merge) / `e6fb07a` (PR-3 flip) / `8214a32` (PR-3 oracle) / `verticals/supply_chain/**` (declared `enrich` severity transform + slimmed `ColdChainAssessExecutor` guard) + `tests/**` (`test_severity_transform_parity.py` + 2 re-homed PLAN-0074/PR-2 tests) + `docs/plans/0078-*.md` (Proposed; PR-3 COMPLETE) |

## Rotated this reconcile (session-150, 2026-07-19 — PLAN-0082 shared-ontology arc COMPLETE + archived, PLAN-0081 folded, #809-812)

### Current-Focus block — Session 144 (PLAN-0078 Step 7 CLOSEOUT, 12/12 ACs → `done/`, #786) [rotated 2026-07-19, session-150 reconcile — 4-newest-sessions CF window]

> **Session 144, 2026-07-17 (head_commit `6ee2aa8` → `d8db032`) — PLAN-0078
> Step 7 CLOSEOUT (#786, docs-only): the transform seed-migration arc CLOSED at
> **12/12 ACs** and ARCHIVED → `docs/plans/done/0078-transform-seed-migration.md`.**
> **The headline is that the closeout was FAR smaller than the s143 handoff
> predicted — and why.** **(1) Four of the six open ACs were ALREADY SATISFIED
> on disk** (AC-7/AC-8/AC-9/AC-12) — unticked BOOKKEEPING, not open work. The
> s143 handoff warned "do NOT tick them from the PR-3/PR-4 landed claim —
> verify against code"; that warning was right to DEMAND the verification, and
> the verification came back GREEN. Each tick now cites its satisfying test by
> file:line, every anchor resolved on a fresh read. **AC-9 was re-verified
> INDEPENDENTLY** rather than inherited from PR-4's R2 claim: `_spend` /
> `_severity` hash identically at `173d869^` and HEAD. **(2) AC-6 was the ONE
> genuine hole — and NOT the hole the PLAN described.** The PLAN predicted
> "Phase 2 adds transforms, so the non-participant set shrinks and must be
> re-swept". **FALSE on disk:** PR-3/PR-4 added transforms only to procedures
> that ALREADY carried a Phase-1 `enrich`, so the set never moved. Classified
> **`superseded by new info`, NOT `was an error`** (CLAUDE.md §6) — the
> prediction was reasonable and may yet come true, so it is now pinned as
> **DATA** (`test_derivation_pin.py:326`) rather than re-argued in prose. **The
> REAL hole:** energy + aquaculture — the two verticals AC-6 names FIRST — had
> **no step-level `transform`-absence assertion anywhere**;
> `test_transform_grammar.py:308` proved it only on a SYNTHETIC procedure, the
> two parity sweeps covered only non-participant procedures INSIDE the migrated
> verticals, and `test_derivation_pin.py:263` asserts the TOP-LEVEL key set
> only. **(3) Both new tests proven non-vacuous EMPIRICALLY, not by
> inspection:** temporarily declaring a transform in energy's yaml turned the
> census RED; temporarily deleting the only-when-supplied branch from
> `governance_pin.py` turned the sweep RED for supply_chain + procurement. Both
> probes REVERTED. The second probe is exactly **why the census must exist
> ALONGSIDE the sweep**: with the projection broken, energy/aquaculture still
> PASSED — a vertical with no transforms satisfies the IFF's negative arm
> regardless. **(4) Stale citations refreshed** against `governance_pin.py`
> post-PR-5 (137 lines): AC-5's `:96-98`→`:98-99`; AC-6's `:59-63`→`:58-68`,
> and `:122-125` **DROPPED** (the `derivation_hash` fold-in PR-5 retired; `:121`
> is now the `steps` list). **(5) Deliberately NOT closed:** **OQ-3 stays open**
> (the ADR-0031 D4.4 row annotation = a drafter-authored G1 Accepted-body edit;
> its own text says non-blocking) · **PLAN-0076 does NOT archive** — T1 /
> F-FACTORY stays open, its AC-6 guard stays ARMED · **no artifact records F-PIN
> closed** (L-4). **Order honored:** `Status:` flipped Proposed→COMPLETE in the
> SAME pass as the body edits (never flip-then-edit — the G1 lift is per-diff);
> the `git mv` to `done/` landed AFTER the sweep + ticks, per Step 7's own order
> and the s143 refusal precedent. Suite **2845 passed / 7 skipped** (was 2840/7
> at `6ee2aa8`) — re-run BY CODE on the merge commit `d8db032` itself, since CI
> is PR-only and never tests the merge commit. Post-merge: main=`d8db032`; 0
> open PRs; loop-dispatcher DISABLED; MS-S1 idle/COLD (zero calls this session);
> dev Postgres UP. Commits: `49ff275` (the sweep + ticks + `git mv`) → `2340de3`
> → `d8db032` (HEAD, #786 merge).

### Recent-Decisions rows — s141 PLAN-0078 PR-4 (#775) + s140 artifact-3/4 (#773) [rotated 2026-07-19, session-150 reconcile — 10-row window]

| 2026-07-17 | **s141 — PLAN-0078 Phase 2 PR-4 COMPLETE (#775, `feat`, oracle-first): the marquee ฿ spend re-sequenced off the `_scored_rule` stamp into a declared `derive_spend` transform, per the ratified SD-8=(a) ONE DERIVATION HOME.** Cray-ratified in-session refinement: stamp `selected_qty` (not `selected_unit_price` only) so `_quantity` stays the ONE resolution home. Suite **2822 passed / 7 skipped**; deterministic-offline. **PLAN-0078 stays `Status: Proposed`**; **PR-5 is NOT blocked by PR-4**. Full narrative: the Session-141 CF block (rotated to `docs/status-archive/` at the s145 reconcile — grep the archive dir, not one file) | `09714ea` (HEAD, #775 merge) / `88e6e11` (PR-4 flip) / `fc17d02` (PR-4 oracle) / `verticals/{procurement,supply_chain}/**` (declared `derive_spend` transform) + `services/engine/procedures/governance_step.py` (`_scored_rule` factor stamps) + `tests/**` (`test_amount_transform_parity.py`) + `docs/plans/0078-*.md` (Proposed; PR-4 COMPLETE) |
| 2026-07-16 | **s140 — artifact 3/4 (#773, docs-only): `CLAUDE.md` §2 retitled "Current Focus" → "Direction & Current Focus" + a two-pointer signpost — standing direction = ADR-0032, current state = STATUS, "state never overrides direction" (§1).** The strategic-continuity program is now **COMPLETE 4/4** (#770 ADR · #771 PLAN-0079 · #773 §2 · #772 STATUS pointer). Scope CUT at Cray's ratification: the planned sanitized strategy doc DROPPED (a no-precedence restatement of a canonical is itself a drift surface, §1 / ADR-0017 D6). Suite **2810 passed / 7 skipped**. Full narrative: the Session-140 CF block above | `0523d88` (HEAD, #773 merge) / `038efd0` (§2 pointer) / `CLAUDE.md` §2 + `docs/adr/0032-*.md` |

## Rotated this reconcile (session-151, 2026-07-19 — PLAN-0081 building_materials governed-credit hero BUILT, the 3rd AT-2 signature, #814)

### Current-Focus block — Sessions 144 + 145 (the R4 archive-guard arc + splits #788–792) [rotated 2026-07-19, session-151 reconcile — 4-newest-sessions CF window]

> **Sessions 144 + 145, 2026-07-17 (head_commit `d8db032` → `ce0f0a1`) — the
> R4 arc: a ratified rule that had NO MECHANISM, closed end to end in one
> session (#789 → #791 → #792), plus two PRs from a CONCURRENT session (#788,
> #790).** R4 (`docs/runbooks/memory-architecture.md` §"R4 — Archive, don't
> drop") sets two numbers — archives stay under a **256 KB cap**; over **~192
> KB** start a continuation — and **nothing enforced either**: R4's own
> responsibility-matrix guard column read `—` where R1 and R7 both read `fail`.
> It had rotted to a **3x breach**. **(1) #789 (`f444cd1` → merge `b369fa6`) —
> the guard.** `tools/check_archive_size.py`: warns over the 192 KB trigger,
> **fails over the 256 KB cap**; a `files:`-scoped pre-commit hook (deliberately
> NOT `always_run` — a byte cap can only be breached by writing the file it
> caps); 8 contract tests; the R4 matrix row `—` → `fail >256 KB`. Landed GREEN
> **by design**: the hook does not fire on a commit touching no archive, and CI
> does not run pre-commit at all. **(2) #791 (`96ef1c4` + `d43f4a8` → merge
> `f00e4c7`) — the split the guard FORCED.** `2026-h1-status.md` was **592,577 B
> = 3.01x the trigger, 2.26x the cap**, growing ~7.5 KB per reconcile → split
> into the **c/d/e/f chain** per Cray's ratified naming rule (**letters ascend
> with time; the base holds the RECENT window; older spills into the next
> letter**) — `-b` is NOT the spill target (it holds OLDER content, so spilling
> newer sections in would break the chronology the letters encode). **Five
> files, not four:** a 4-way split forces one file to ~97% of the trigger, and
> the excuse "it's frozen so tight is fine" was **falsified BY THIS SESSION**
> (the s144 reconcile appended an archivist's note to a supposedly frozen row).
> Also lands **`test_live_archives_are_within_cap`** — the BINDING half; it
> could NOT land in #789 (RED at 2.26x), and **that ordering was the point**: a
> guard whose live assertion is RED cannot merge into a protected main. **(3)
> #792 (`61d072f` → merge `ce0f0a1`) — the current-focus split + THE RULE
> RECORDED AS CANON.** `2026-h1-current-focus.md` was 258,346 B (1.31x trigger,
> ~3,798 B under the cap) and **still receiving appends** (last s132) → split to
> `b`/`c` + base. **The more important half: Cray's naming rule was living only
> in commit messages and file headers — canonically invisible, which is EXACTLY
> how R4 got a guard column of `—` in the first place.** Now in the runbook,
> with the corollary and the hard-won warning: **which file holds a block is not
> stable information — grep the directory, never cite a continuation by name
> from outside the archive** (this session broke three of its own pointers that
> way). **Result: every archive is now under the ~192 KB TRIGGER (not merely the
> cap) and the guard is SILENT for the first time.** Rotation archive:
> `h1b`/`c`/`d`/`e`/`f` (94K–162K) → `2026-h1-status.md` base **22,185 B**;
> current-focus: `h1b-cf` 164,875 / `h1c-cf` 81,045 → base **18,161 B**. Both
> bases carry ~174 KB of headroom ≈ 23 reconciles. **Proofs, stated honestly:**
> #791 proved **exact list equality** of 27 sections; #792 proved **multiset
> equality** of 30 blockquote blocks (blocks deliberately reordered ACROSS
> files; order WITHIN each file untouched) — **different proofs, and the PR says
> so**. Both re-run against HEAD **AFTER pre-commit**, which CHANGED the answer:
> the end-of-file-fixer stripped one trailing newline per continuation, so the
> honest claim is *"equal except N trailing newlines, all stripped-equal"*,
> **NOT byte-identical**. **Two structural facts found by grounding, RECORDED
> rather than quietly fixed:** (i) `current-focus` has **zero `## ` sections**
> (it is blockquote blocks) — reusing the sibling's parser would have found 0
> sections and "split" nothing **while reporting success**; (ii) its header
> claimed "Session 46 and earlier" but later deep-rotates had appended sessions
> 116–128 to its bottom — **one file carrying two orderings**. Also: the
> `session 25` block is **162,822 B, atomic** — `h1b-cf` is large **by
> necessity, not by packing choice**. **Concurrent-session PRs — NOT session
> 144's work:** **#788 (`694e8d7`) — PLAN-0080 filed by session 145**, `Status:
> **Draft** (pending Cray ratification)`: **SD-1 and SD-2 are UNRATIFIED —
> merging the document did NOT ratify its decisions, and it must NOT be
> executed**; ⚠ **`docs/conventions/ui.md` does NOT exist** — the PR title names
> it because the PLAN *proposes* it, not because it shipped. **#790 (`ba12e1b` →
> merge `bb369ed`) — session 145's STATUS frontmatter-only bump**, merged by
> session 144 **on Cray's explicit instruction** to clear the STATUS lane; it
> existed *because of* #789 — its own title says "full reconcile blocked by the
> R4 guard", the forcing function biting a sibling session within hours, which
> is what turned the split from hygiene into **unblocking work**. Suite **2855
> passed / 7 skipped** — re-run BY CODE on the merge commit `ce0f0a1` itself,
> since CI is PR-only and never tests the merge commit. Post-merge:
> main=`ce0f0a1`; 0 open PRs; loop-dispatcher DISABLED; MS-S1 idle/COLD (zero
> calls); dev Postgres UP. Commits: `694e8d7` (#788, session 145) → `f444cd1` →
> `b369fa6` (#789) → `ba12e1b` → `bb369ed` (#790) → `96ef1c4` + `d43f4a8` →
> `f00e4c7` (#791) → `61d072f` → `ce0f0a1` (HEAD, #792 merge).

### Recent-Decisions row — s142 (the THREE R2 carve-out TODOs DISCHARGED, #780/#778/#779) [rotated 2026-07-19, session-151 reconcile — 10-row window]

| 2026-07-17 | **s142 — the THREE R2 carve-out TODOs DISCHARGED (#780/#778/#779, docs-only): each fact REHOMED into a tracked home FIRST, THEN trimmed** — Rock 4's evidence-asymmetry finding → ADR-0025 · the `sequence`-column deferral → the ordering-guard docstring (deferral STANDS) · the s74 demo-card SD-3 → the PLAN-0035 `done/` post-archival amendment (+ ADR-0030's `STATUS.md:<line>` citations re-pointed). Runbook R2 now records **"until it is rehomed" is a real exit**, and that an ADR citing `STATUS.md:<line>` is a **defect**. Suite **2822/7**. Full narrative: the Session-142 CF block (rotated to `docs/status-archive/` at the s146 reconcile — grep the archive dir, not one file) | `303fd48` (HEAD, #779) / `37ab124` (#778) / `12e69aa` (#780) / `docs/adr/0025-*.md:23-29` + `docs/plans/done/0035-*.md:576` + `tests/services/db/test_load_run_ordering_guard.py` + `docs/runbooks/memory-architecture.md` (R2) |

## Rotated this reconcile (session-152, 2026-07-19 — PLAN-0083 c1 procurement adapter canonical mapping CLOSED, #818/#819)

### Current Focus block — Session 146 (PLAN-0080 trace-attribution legibility + the canonical `docs/conventions/ui.md`, #794/#795) [rotated 2026-07-19, session-152 reconcile — 4-newest-sessions CF window]

> **Session 146, 2026-07-17 (head_commit `6249f52` → `8737b0a`) — PLAN-0080
> shipped end to end in two PRs: trace-attribution legibility + the canonical
> `docs/conventions/ui.md`.** The reasoning-trace badge had stopped telling the
> truth: a substring sniff (`kind.includes('rule')`) left **14 of 16
> procedure-engine kinds** on an unattributed neutral badge, and
> `scored_rule_selected` / `rule_gate_evaluated` matched `'rule'` and borrowed
> the recommender's `rule_check` colour. **(1) #794 (`6a2a42d`, `feat(ui)`) —
> deterministic attribution + an anti-rot tripwire.** ONE shared
> kind→{label,cls,actor} registry (`services/api/static/assets/trace-kinds.js`,
> `window.OCT_TRACE_KINDS`, **23 kinds**) is read by BOTH the browser and a CI
> tripwire. L-4 (Cray-ratified) split the signal onto **two axes, two channels**:
> colour = mechanism (existing `theme.css` semantics — the demo look is
> UNCHANGED), a small glyph = actor (`{human,llm,engine}` via `data-actor`).
> Unmapped kinds degrade VISIBLY — raw token, dashed `.badge.unmapped`, NO
> glyph, `data-actor="unknown"`. The AST tripwire
> (`tests/api/test_trace_kind_labels.py`) scans `services/engine` + `verticals`
> and asserts SET-EQUALITY, proven non-vacuous by 3 RED mutations. SD-1(c) (keep
> `ReasoningStep.kind: str`) + SD-2(iii) (0013 prompt annotated, not rewritten)
> Cray-ratified. **(2) #795 (`8737b0a`, `docs(conventions)`) — the canonical UI
> convention.** New `docs/conventions/ui.md` (11 items per AC-6, each with a live
> `file:line` anchor: tokens, the `window.OCT` contract, the trace-kind channel,
> the `html:`-only security rule, no-build-step + `?v=` cache-bust,
> ontology-driven principle, control-tower tone, provenance classes, the 0013
> relation, a `Step.kind`-vs-trace-`kind` glossary). AC-7: the 0013 design prompt
> got a one-line header annotation (body untouched); `code-style.md` gained a
> "UI work → ui.md" pointer. Canonical, not derived (ADR-0017 D5) + outside
> G1/G2 gate scope → Code authored it directly. **The reusable lesson (F-4):** a
> live preview probe against a REAL completed governed run REFUTED the PLAN's
> offline-draft claim "the engine is the only emitter" — `verticals/` seed
> executors emit `query`, unmapped, on the governed spine in 9/9 runs → added as
> kind #23, the tripwire's scan root widened to `verticals/`, the leaking
> definition-side `StepKind` token labelled (NOT fixed). Two more offline-draft
> errors caught by the same grounding: AC-3's regex would have absorbed non-trace
> `kind=` kwargs (`ControlRef`, `EconomicImpact`) → became an AST scan; AC-5's
> grep read was impossible as written (view-story has 5 `kind` vocabularies) →
> scoped to the TRACE block. Full offline suite **2860 passed / 7 skipped** re-run
> on BOTH merge commits. Post-merge: main=`8737b0a`; 0 open PRs; loop-dispatcher
> DISABLED; MS-S1 idle/COLD — zero calls this session. Commits: `6a2a42d` (#794,
> Subject A) → `8737b0a` (HEAD, #795 merge, Subject B).

### Recent Decisions row — s143 R7 (never cite `docs/STATUS.md` by line number, #783) [rotated 2026-07-19, session-152 reconcile — 10-row window]

| 2026-07-17 | **s143 — rotation policy **R7** is BINDING (#783, `chore`): never cite `docs/STATUS.md` by LINE NUMBER — cite the tracked artifact, or STATUS by SECTION NAME; a tripwire + an `always_run` pre-commit hook enforce it repo-wide (10 rotted sites cleaned, RED→GREEN 10 → 0).** _[Sibling #782 (`bc42136`, s142, reconciled s143): Lesson #0031 + the `fan-out-dispatch` skill — split parallel work on the WRITE-SET, not the idea.]_ Full narrative: the Session-143 CF block above | `3bf99bc` (#783 merge) / `abd41d4` (R7 + guard + cleanup) / `bc42136` (#782 merge) / `docs/runbooks/memory-architecture.md` (R7) + `tools/check_status_citations.py` + `docs/lessons/0031-*.md` + `.claude/skills/fan-out-dispatch/` |

### Current Focus block — Sessions 147 + 148 (PLAN-0081 opened + reshaped #797/#798; PLAN-0080 CLOSED OUT + archived #799) [rotated 2026-07-20, session-155 reconcile — 4-newest-sessions CF window]

> **Sessions 147 + 148, 2026-07-18 (head_commit `8737b0a` → `0b67f76`) —
> PLAN-0081 opened + reshaped (s147, #797+#798) and PLAN-0080 CLOSED OUT +
> archived (s148, #799); all three PRs `docs(plans)`, ZERO code/behaviour
> change.** **(s147) The PLAN-0081 arc — the `building_materials`
> governed-credit HERO. #797 (`e03e56f`)** filed PLAN-0081 as `Status: Draft`
> — the BUILD plan Cray COMMISSIONED via PLAN-0079 Step T1 (SD-1 = trip AT-2
> signature **N=3** in-PLAN, do NOT wait for PLAN-0076 T1; SD-2 = ride the
> existing `measured_value` exposure field). SD-A/B/C/D resolved (Cray, s146).
> **#798 (`46a6ec2` → merge `fa4f6c6`)** folded in Cray's **SD-E=(b-ii)** +
> ratified **SD-J=SPLIT** (both via AskUserQuestion). SD-E=(b-ii) = promote
> `Person` to an ADR-0008 ontology `object_type` at a NEW shared/core ontology
> home. **The grounded crux:** the shipped codegen model is strictly
> per-vertical — NO shared/cross-vertical ontology home exists — so b-ii
> **INVENTS** the mechanism, it does not reuse one. **SD-J=SPLIT** = b-ii
> becomes its OWN new PLAN (+ a preceding ADR-0008 grammar amendment as its
> gate); PLAN-0081 Step 9 shrinks to the migration onto the shared `Person`
> that new PLAN ships. New AC-12/13/14/15 + surfaced sub-forks SD-F…SD-J +
> expanded OQ-1. **PLAN-0081 stays `Status: Draft` — no code shipped.**
> **(s148) The PLAN-0080 closeout — #799 (`81f307b` → merge `0b67f76`).**
> PLAN-0080 (trace-attribution legibility + the canonical
> `docs/conventions/ui.md`) had shipped end-to-end in s146 (#794 `feat(ui)` +
> #795 `docs(conventions)`) but its Status header still read "Draft (pending
> Cray ratification)" with all **9 ACs unticked**, and it was never archived.
> This closeout flipped Status → **Complete**, re-verified ALL 9 ACs against
> `main` on a FRESH disk read (each with `file:line` evidence), ticked them,
> and `git mv`'d it to `docs/plans/done/`. **AC-5 ticked as-scoped (Finding
> F-4):** the `TRACE` entries fed to `O.reasoningTrace` are normalized to
> canonical kinds; the surviving `kind:` tokens in PROP cards / KIND_BADGE /
> the pipeline DAG are separate local vocabularies the AC carved out. Findings
> **F-1/F-2/F-3 + OQ-1 stay recorded, NOT closed**. No code/behaviour change;
> SD-1(c)/SD-2(iii) were Cray-ratified in s146. Post-merge: main=`0b67f76`;
> 0 open PRs; loop-dispatcher DISABLED; MS-S1 idle/COLD — zero calls this
> session (docs-only). Commits: `e03e56f` (#797) → `46a6ec2` → `fa4f6c6`
> (#798 merge) → `81f307b` (#799 closeout) → `0b67f76` (HEAD, #799 merge).

### Recent Decisions row — s143 PLAN-0078 Phase 2 PR-5 (the `derivation_hash` retirement, #784) [rotated 2026-07-20, session-155 reconcile — 10-row window]

| 2026-07-17 | **s143 — PLAN-0078 Phase 2 PR-5 COMPLETE (#784, `refactor`), the FINAL PR of the transform seed-migration: the PLAN-0075 AC-13 `derivation_hash` RETIRED end-to-end (AC-10 grep-clean, 0 hits outside `docs/`), the F-PIN marker rewritten (AC-11), PLAN-0076 Step T2 CLOSED.** A DELETION PR by design: AC-13 hashed supply_chain's ladder CONSTANTS into the pin only because the derivation lived in vertical CODE — PR-3/PR-4 declared it, so the reason vanished and the workaround went. Both retired guarantees re-homed at FULL strength (an ACTUAL `assert_governance_pin` raise, not an `h1 != h2` compare). 2 Cray ratifications OVERRODE the drafter (unrenderable AC-11 assert; KEEP the constants test-only). **F-PIN NOT closed; PLAN-0076 does NOT archive** (T1 open, AC-6 armed). Suite **2840/7** re-run on the merge commit itself. _[Siblings reconciled same pass: #783 R7 citation guard · #782 Lesson #0031.]_ Full narrative: the Session-143 CF block above | `6eea264` (HEAD, #784 merge) / `70d25a5` (PR-3 forward-ref fix) / `6e6ec7a` (PLAN-0076 T2) / `732fc0a` (the retirement) / `verticals/supply_chain/**` + `services/engine/procedures/**` (registry seam + `governance_pin` param retired across 8 files) + `tests/**` (exact-snapshot-key-set assertion) + `docs/plans/0078-*.md` (PR-5 COMPLETE) + `docs/plans/0076-*.md` (T2 CLOSED) |

### Recent Decisions row — s144 PLAN-0078 closeout at 12/12 ACs (#786) [rotated 2026-07-20, session-155 evening reconcile — 10-row window]

| 2026-07-17 | **s144 — PLAN-0078 COMPLETE at 12/12 ACs → `docs/plans/done/0078-transform-seed-migration.md` (#786, docs-only): a FAR smaller closeout than the s143 handoff predicted — 4 of the 6 open ACs (AC-7/8/9/12) were ALREADY SATISFIED on disk (unticked bookkeeping; each tick now cites its test by file:line, and AC-9 was re-verified INDEPENDENTLY rather than inherited from PR-4's R2 claim).** **AC-6 was the ONE genuine hole — and NOT the hole the PLAN described:** the predicted "Phase 2 shrinks the non-participant set" was FALSE on disk (PR-3/PR-4 only touched procedures already carrying a Phase-1 `enrich`) → classified **`superseded by new info`, NOT `was an error`** (CLAUDE.md §6) and pinned as DATA; the REAL hole was energy + aquaculture carrying no step-level `transform`-absence assertion anywhere. Both new tests proven non-vacuous **EMPIRICALLY** (probes reverted). **OQ-3 stays open; PLAN-0076 does NOT archive; F-PIN NOT closed** (L-4). Suite **2845/7** re-run on the merge commit itself. Full narrative: the Session-144 CF block above | `d8db032` (HEAD, #786 merge) / `49ff275` (sweep + ticks + `git mv`) / `docs/plans/done/0078-transform-seed-migration.md` (COMPLETE, archived) + `tests/**` (`test_derivation_pin.py:326` prediction pin + the energy/aquaculture transform census) |

### Recent Decisions row — s146 PLAN-0080 trace-attribution registry shipped (#794 #795) [rotated 2026-07-21, session-156 reconcile — 10-row window]

| 2026-07-17 | **s146 — PLAN-0080 shipped end to end (#794 `feat(ui)` + #795 `docs(conventions)`): the reasoning-trace badge's substring sniff (`kind.includes('rule')`, mis-attributing 14/16 engine kinds) → ONE shared kind→{label,cls,actor} registry (`trace-kinds.js`, 23 kinds) read by BOTH the browser and an AST set-equality tripwire; colour=mechanism (theme.css UNCHANGED) + glyph=actor, unmapped kinds degrade visibly. + canonical `docs/conventions/ui.md` (11 anchored items).** **F-4:** a live probe refuted the offline "engine-only emitter" claim — `verticals/` seed executors emit `query` unmapped 9/9 → kind #23, scan root widened. Suite **2860/7** on BOTH merge commits. Full narrative: the Session-146 CF block above | `8737b0a` (#795 merge) / `6a2a42d` (#794) / `services/api/static/assets/trace-kinds.js` + `tests/api/test_trace_kind_labels.py` + `docs/conventions/ui.md` |

### Recent Decisions row — s144 R4 archive-size guard arc closed (#789 #791 #792) [rotated 2026-07-21, session-156 reconcile — 10-row window]

| 2026-07-17 | **s144 — the R4 arc CLOSED end to end (#789 guard → #791 + #792 splits): a ratified rule that had NO mechanism now has one, and every archive sits under the ~192 KB TRIGGER — not merely the cap — for the first time.** R4's own responsibility-matrix guard column read `—` where R1/R7 read `fail`; the rotation archive had rotted to **592,577 B = 2.26x the cap**. #789 shipped `tools/check_archive_size.py` (warn >192 KB, **fail >256 KB**, `files:`-scoped hook) GREEN **by design**; the BINDING live assertion (`test_live_archives_are_within_cap`) could only land in #791 **after** the split — a guard whose live assertion is RED cannot merge into a protected main. **Five-file c/d/e/f chain, not four** (a 4-way split lands one file at ~97% of the trigger). #792 split current-focus AND **recorded Cray's naming rule as CANON** — letters ascend with time, the base holds the recent window; **grep the archive dir, never cite a continuation by name**. Proofs DIFFER and say so: #791 = exact list equality (27 sections), #792 = multiset equality (30 blocks, deliberately reordered across files); both re-run AFTER pre-commit → *"equal except N trailing newlines, all stripped-equal"*, **NOT byte-identical**. Suite **2855/7** re-run on the merge commit itself. _[Concurrent session 145: #788 PLAN-0080 `Status: Draft` — SD-1/SD-2 UNRATIFIED, must NOT be executed, and `docs/conventions/ui.md` does NOT exist · #790 frontmatter-only bump, merged on Cray's instruction.]_ Full narrative: the Sessions-144+145 CF block above | `ce0f0a1` (HEAD, #792 merge) / `f00e4c7` (#791) / `b369fa6` (#789) / `694e8d7` (#788) / `tools/check_archive_size.py` + `.pre-commit-config.yaml` + `docs/runbooks/memory-architecture.md` (R4 matrix row `—` → `fail >256 KB` + the naming rule) + `docs/status-archive/**` (the c/d/e/f + b/c-cf chains) |

### Recent Decisions row — s147 PLAN-0081 arc (#797 Draft + #798 SD-E fold / SD-J SPLIT) [rotated 2026-07-21, session-157 reconcile — 10-row window]

| 2026-07-18 | **s147 — PLAN-0081 arc (#797 Draft + #798 SD-E=(b-ii) fold / SD-J=SPLIT ratified, both `docs(plans)`): #797 filed the `building_materials` governed-credit HERO BUILD plan as `Status: Draft` (Cray COMMISSIONED via PLAN-0079 T1 — SD-1=trip AT-2 N=3 in-PLAN, SD-2=ride `measured_value`).** #798 folded Cray's **SD-E=(b-ii)** (promote `Person` to a NEW shared/core ADR-0008 `object_type` — the shipped codegen is strictly per-vertical, so b-ii INVENTS the mechanism) + ratified **SD-J=SPLIT** (b-ii → its OWN new PLAN + a preceding ADR-0008 grammar amendment as gate; PLAN-0081 Step 9 shrinks to the migration). New AC-12/13/14/15 + SD-F…SD-J + expanded OQ-1; **PLAN-0081 stays Draft — no code shipped.** Full narrative: the Sessions-147+148 CF block above | `fa4f6c6` (#798 merge) / `46a6ec2` (SD-E fold) / `e03e56f` (#797 Draft) / `docs/plans/0081-*.md` (Draft) |

### Rotation note — session-155 EVENING reconcile [rotated 2026-07-21, session-157 reconcile — 2-note window]

> _Rotation note (session-155 EVENING reconcile, 2026-07-20, `docs(status):`):
> the SAME session 155 continued past the morning reconcile and shipped the
> PLAN-0084 arc (#825 → #826 → #827), so the existing **Sessions 153 + 154 +
> 155** block was EXTENDED IN PLACE (head_commit range now `a53c6ed` →
> `25b31e2`, the #827 `feat(demo)` merge, the newest SUBSTANTIVE commit — Q4
> recipe) — NO new CF block, NO CF rotation (4-session window unchanged:
> s153/154/155 + s152 + s151 + s149/150). Recent Decisions gained ONE row (the
> late-s155 PLAN-0084 arc) and so rotated its ONE OLDEST — the **s144**
> PLAN-0078 closeout row (#786) — to the rotation-archive BASE
> `docs/status-archive/2026-h1-status.md`. [Morning reconcile, consolidated:
> the combined s153/154/155 block's PREPEND rotated OUT the **Sessions 147 +
> 148** CF block and the **s143** PLAN-0078 Phase-2 PR-5 row (#784), both to
> the same base.] Prior rotation notes (through the s155 morning reconcile)
> are consolidated here (R4). Per the STATUS.md Rotation Policy (R1/R2/R4)._

| 2026-07-18 | **s148 — PLAN-0080 COMPLETE + archived (#799, `docs(plans)`): the trace-attribution + `ui.md` PLAN (shipped end-to-end s146 via #794/#795) closed out — Status → Complete, all 9 ACs re-verified against `main` on a fresh disk read (each with file:line evidence) + ticked, `git mv` → `docs/plans/done/`.** AC-5 ticked as-scoped (**F-4**: only the `TRACE` entries fed to `O.reasoningTrace` are canonical-normalized; PROP-card / KIND_BADGE / DAG `kind:` tokens are separate local vocabularies the AC carved out). Findings **F-1/F-2/F-3 + OQ-1 stay recorded, NOT closed**; no code/behaviour change. Full narrative: the Sessions-147+148 CF block above | `0b67f76` (HEAD, #799 merge) / `81f307b` (closeout) / `docs/plans/done/0080-*.md` (COMPLETE, archived) |

> _Rotation note (session-156 reconcile, 2026-07-21, `docs(status):`): added the
> **Session 156** CF block (the AI-Transition View-1 / Rung-1 arc) and rotated
> the OLDEST CF block — **Sessions 149 + 150** (PLAN-0082 shared-ontology, #801–
> 812) — to the Current-Focus rotation base
> `docs/status-archive/2026-h1-current-focus.md`. Recent Decisions gained TWO
> rows (the PLAN-0085 Rung-1 arc + the rehearsal/closeout/AI-Transition-frame)
> and rotated its TWO OLDEST — the **s146** PLAN-0080 row (#794/#795) and the
> **s144** R4-arc row (#792) — to the rotation base
> `docs/status-archive/2026-h1-status.md`. Window after this reconcile: CF = 4
> blocks (s156 + s153/154/155 + s152 + s151); RD = 10 rows. Prior rotation notes
> (through the s155 evening reconcile) are consolidated in the rotation archive
> (R4). Per the STATUS.md Rotation Policy (R1/R2/R4)._

| 2026-07-18 | **s149 — PLAN-0082 shared-ontology mechanism BUILT (Steps 2-4 behind ADR-0033, #803-808): ADR-0033 Accepted (shared `core` home + `imports:` grammar + set/closed types + shared Person committed-ORM contract); `core_v0.yaml` + set/closed L1/L2 (#804), Pydantic emitter (#805), imports/cross-doc resolution (#806), set→JSONB emitters (#807), committed Person ORM + `person` table + Alembic 0012 migration ran green (#808).** Additive — zero shipped-behaviour change. Full narrative: the Sessions 149+150 CF block above | `5e45eb6` (#808) / `6dd6464` (#803) / `ontology/core_v0.yaml` + `services/db/person.py` + `alembic/versions/0012_person_table.py` |

> _Rotation note (session-157 reconcile, 2026-07-21, `docs(status):`): added the
> **Session 157** CF block (PLAN-0086 — the timed manual scaffold of vertical #6
> `fleet_maintenance`, #838) and rotated the OLDEST CF block — **Session 151**
> (PLAN-0081 `building_materials` governed-credit hero, #814) — to the
> Current-Focus rotation base `docs/status-archive/2026-h1-current-focus.md`.
> Recent Decisions gained ONE row (the PLAN-0086 / ADR-0025-D7-cancellation arc)
> and rotated its ONE OLDEST — the **s147** PLAN-0081 arc row (#797/#798) — to
> the rotation base `docs/status-archive/2026-h1-status.md`. The **session-155
> EVENING** rotation note was itself rotated to the same base (R4
> consolidation). Window after this reconcile: CF = 4 blocks (s157 + s156 +
> s153/154/155 + s152); RD = 10 rows. Per the STATUS.md Rotation Policy
> (R1/R2/R4)._

| 2026-07-19 | **s150 — PLAN-0082 COMPLETE + archived (Steps 5-7, #809-811) + PLAN-0081 fold (#812): the reconciliation half of the shared-ontology arc — spec-layer `Person` reconciled to ONE generated `core.Person` (#809, SD-H=(a) + `_PYDANTIC_COMMITTED_DEST`), procurement+supply_chain migrated + OQ-6 marker transformed (#810), PLAN closed out at 7/7 ACs + archived (#811); PLAN-0081 folded (SD-J=SPLIT resolved, Step 9 shrunk).** AC-5 dual-roster "retire one" RE-SCOPED (misread — distinct demos, neither retired). CI-scope lesson (mypy strict re-export). OQ-2 deferred. Full narrative: the Sessions 149+150 CF block above | `043da3c` (HEAD, #812) / `e059303` (#811) / `docs/plans/done/0082-*.md` |

---

## Rotated this reconcile (session-163, 2026-07-22 — the s162 fleet AT-3 calm-path reconcile PLUS the R2 pointer-rule trim of Recent Decisions + Active TODOs)

Two passes in one PR: the reconcile rotated the usual window (one RD row, two rotation notes) and retired one Active TODO as discharged; the trim then compressed the surviving RD rows and the over-length Active TODOs to the R2 ~600-char pointer form. Every pre-trim original is preserved below verbatim — the trim is a compression in STATUS, never a deletion from the repository.

### Recent-Decisions row rotated out of the 10-row window — s151 / PLAN-0081 (#814) [rotated 2026-07-22, session-163 reconcile]

| 2026-07-19 | **s151 — PLAN-0081 BUILT end to end (#814, `feat(building_materials)`): the `building_materials` governed-credit HERO — the 3rd AT-2 signature (`building_materials.governed_credit_release`), Cray-commissioned this session. An exposure breach above the account's own `credit_limit_thb` routes the full governed AT-2 spine (per-entity band → `rule_gate` KYC/overdue-AR/blacklist → `doa_tier` approval + SoD); the ฿550,000 breach routes mid-ladder.** The 3rd signature REUSES the money `doa_tier` ladder UNCHANGED (no new gate kind / authority quantity) — only `ComplianceCriterion += {kyc, overdue_ar, blacklist}` grows; engine diff bounded to that additive `spec.py` block (the `Person` promotion was PLAN-0082's, already on main). **ADR-0025 D7 re-eval PERFORMED at N=3** (Cray-ratified: generator stays deferred, marker re-arms N=4). Closeout: PLAN-0079 tracking stub RETIRED (Step T3) + guard test DELETED; PLAN-0076 T1 gate-seam trigger recorded MET (seam PLAN un-opened); PLAN-0081 archived at 15/15 ACs. Suite **2896/7** re-run on the merge commit `9422c40`; mypy strict + ruff clean. Full narrative: the Session-151 CF block above | `9422c40` (HEAD, #814 merge) / `a46bef8` (build) / `docs/plans/done/0081-*.md` (archived, 15/15) + `tests/verticals/building_materials/test_governed_credit_hero.py` |

### Rotation notes rotated (R4 consolidation) — the session-160 and session-159 notes [rotated 2026-07-22, session-163 reconcile]

> _Rotation note (session-160 reconcile, 2026-07-22, `docs(status):`): added
> the **Session 160** CF block (the four-PR arc — #843 the Cray-reserved-step
> classifier rule, recorded LATE / #844 the Stop-hook contentless-reason FLOOR /
> #845 the AT-2 `N=4` correction + the new `step_id`-scope guard / #846 the two
> Accepted-ADR body corrections) and rotated the OLDEST CF block — **Session
> 156** (the morning map-label UI fix #829, the long-carried demo rehearsal
> PERFORMED + the PLAN-0084 closeout #830, and the PLAN-0085 advisory-gate arc
> filed → ratified → built → closed, #831-#834) — to the Current-Focus rotation
> base `docs/status-archive/2026-h1-current-focus.md`. Rotating it is what **R2
> requires**, not a headroom judgement: the 4 most-recent sessions are now
> 160 / 159 / 158 / 157, so the s156 block fell **outside** the window. Recent
> Decisions gained ONE row (the s160 four-PR arc) and rotated its ONE OLDEST —
> the **s149** PLAN-0082 shared-ontology-mechanism row (#803-#808) — to the
> rotation base `docs/status-archive/2026-h1-status.md`. Window after this
> reconcile: **CF = 3 blocks covering the 4 newest sessions** (s160 + s158/159 +
> s157 — well under the 8-block cap); RD = 10 rows. **STATUS: 51,045 B → 56,272
> B** (caller-measured, not estimated), against the 64 KB R1 ceiling — the net
> growth is a four-PR block replacing a smaller one; the Active-TODO trim
> (~4.66 KB, all four oversized items verified to have a tracked home) is the
> standing headroom lever if the soft 48 KB target is wanted back. Per the
> STATUS.md Rotation Policy (R1/R2/R4)._
>
> _Rotation note (session-159 reconcile, 2026-07-21, `docs(status):`): added
> the **Sessions 158 + 159** CF block (PLAN-0087 BUILT #840 → CLOSED + archived
> #841) and rotated the OLDEST CF block — **Session 152** (PLAN-0083, the
> procurement ontology↔CSV column drift closed at the `FastenalCsvAdapter`
> seam, #818/#819) — to the Current-Focus rotation base
> `docs/status-archive/2026-h1-current-focus.md`. Recent Decisions gained ONE
> row (the PLAN-0087 build+closeout arc) and rotated its ONE OLDEST — the
> **s148** PLAN-0080 closeout row (#799) — to the rotation base
> `docs/status-archive/2026-h1-status.md`. The **session-156** rotation note was
> itself rotated to the same base (R4 consolidation). **Amended later the same
> session (the R1 headroom follow-up, `docs(status):`): the `Sessions 153 + 154 +
> 155` CF block (~12.8 KB) was ALSO rotated** to the Current-Focus base. This was
> not a judgement call about headroom — it is what **R2 already required**:
> the canonical rule keeps *"blocks from the **4 most-recent sessions**, capped at
> 8 blocks (blocks ≠ sessions)"* (`docs/runbooks/memory-architecture.md` R2), and
> the 4 most-recent sessions are 159 / 158 / 157 / 156, so the s153-155 block was
> already **outside** the window when this reconcile ran. The first pass held it
> back on a "keep 4 CF **blocks**" reading of the file's own practice; the runbook
> is canonical and wins (CLAUDE.md §1). Window after the amendment: **CF = 3
> blocks covering the 4 newest sessions** (s158/159 + s157 + s156 — well under the
> 8-block cap); RD = 10 rows. **STATUS: 63,159 B → 50,390 B**, against the 64 KB
> R1 ceiling. Per the STATUS.md Rotation Policy (R1/R2/R4)._

### Active TODO RETIRED AS DISCHARGED — "AT-2 stale N=2 / N=3 signature counts" [retired 2026-07-22, session-163 reconcile]

**Retirement basis — the item was FALSE, not merely stale.** Session 160 (#845 / #846) had already corrected all three artifacts it names, verified on disk this session: `services/engine/procedures/spec.py` states N=4 (its surviving N=2/N=3 tokens are correctly-framed historical narrative of the firing arc); `docs/adr/0025-at2-managerial-layer.md` carries a dated 2026-07-22 OUTCOME amendment whose "N >= 2" decision text is deliberately preserved rather than rewritten (the G1-safe pattern); `docs/adr/0032-strategic-frame-demo-to-pilot-wedge-and-3-shape-roadmap.md` is re-grounded to N=4. This is a retirement, not a trim.

- [ ] **AT-2 stale `N=2` / `N=3` signature counts — doc drift across three artifacts (surfaced s155).** _[s157 UPDATE: the deferral is now **CANCELLED**, so the drift is doubly stale — fold the corrections into the G1-gated edits the extraction PLAN will carry rather than fixing them piecemeal.]_ _[s158 UPDATE — **STILL OPEN, and the fold-in did NOT happen**: PLAN-0087's only Accepted-ADR edit was the ADR-0031 **D3 row-3** update its own AC-7 obligated (D4.4), scoped to a single table row. **ADR-0025 D7 and ADR-0032 still carry the stale counts**, and `spec.py`'s comments moved but were not audited for N-counts. So this item is unchanged in substance: it now needs its own small `plan-drafter` dispatch rather than a ride-along. Same reasoning as before — nothing turns RED on it, but every stale count is a wrong premise for the next AT-2 scoping call.]_ _[s159 CONFIRMED: PLAN-0087 **closed out + archived at 8/8 without carrying the fold-in**, so the ride-along option is now GONE — the item is confirmed to need its own small `plan-drafter` dispatch.]_ The pre-s157 live value was **`N=3`, with the ADR-0025 D7 generator marker RE-ARMING at `N=4`** (Cray-ratified at the s151 PLAN-0081 re-eval). Stale counts survive in: **(1)** `services/engine/procedures/spec.py` comments — **ungated, fix freely**; **(2) ADR-0025 D7** and **(3) ADR-0032** — both **G1-gated Accepted-body edits**, so they route via `plan-drafter`, never a direct Code write. Only `tests/services/engine/procedures/test_at2_signature_retrigger.py` carries the correct `_RETRIGGER_N = 4`, so the *test* is the source of truth and nothing turns RED on the prose drift. _[Irony worth preserving: **ADR-0032's own Positive-consequences section claims it makes exactly this stale-N-count error class harder to reintroduce** — and it now carries that very drift.]_ *(s155; blocks nothing, but every stale count is a wrong premise for the next AT-2 scoping call.)*

### Pre-trim originals — the 9 Recent-Decisions rows compressed to the R2 pointer rule [trimmed 2026-07-22, session-163]

Trim basis: the Decision cell only; the Date column and the entire Reference column survive byte-untouched in STATUS, because R2's own wording ("full detail lives in the referenced ADR/PLAN/PR, which every row already links") makes the link the thing the rule preserves. One carve-out HIT was retained verbatim in STATUS and NOT compressed: the s156 model-economy ratification, whose only home is a private Tier-0 auto-memory.

| 2026-07-22 | **s161 — PLAN-0088 filed Draft (#848, `docs(plans)`): the cross-run read substrate + run-insight readers. Grounding: the repo records everything PER-RUN but aggregates NOTHING across runs (the only SQL aggregate in `services/` is the audit-chain count; `GET /runs` materializes every run in Python). Two Cray-ratified TYPED forks are the PLAN's LOCKED constraints — L1: "Group A" (NL-over-runs, ฿ ROI, bottleneck/cycle-time, audit-readiness) is NOT Shape 2 and does NOT trip the ADR-0032 D2 pilot gate, and the separation is proven by a STATIC guard (AC-11), not prose; L2: build Group A + PROVE the substrate expresses Group B (4 executable query-shape tests, AC-10) but do NOT build Group B — it stays pilot-gated.** Wall-clock ordering hazard PINNED not inherited (order-insensitive aggregates, coarse buckets, an AC-3 AST tripwire) — the sequence-column PLAN stays UNOPENED; cross-currency sums made UNREPRESENTABLE (group key includes `currency`, no total field). Docs-only, CI gate PASS SHA-verified. Full narrative: the Session-161 CF block above | `e6bb8c8` (#848 merge, head_commit of record) / `0dce906` (build) / `docs/plans/0088-cross-run-read-substrate-and-run-insight-readers.md` (Draft) |
| 2026-07-22 | **s160 — four PRs hardening the Stop hook and the AT-2 doc record. #844 the CONTENTLESS-REASON FLOOR (a `proceed` reason naming no action is demoted to pause — the COMPLEMENTARY shape to #843, which landed s159 unrecorded); #845 AT-2 corrected to N=4 + a new cross-procedure `step_id`-scope guard; #846 (`plan-drafter`, G1) ADR-0032 re-grounded + a dated ADR-0025 D7 OUTCOME amendment, its "N ≥ 2" decision text deliberately NOT rewritten.** Two premises now pinned in code, not prose: `_RETRIGGER_N` is retired and guards nothing, and PLAN-0087's "zero live `step_id` collisions" is wrong (the OVER-MARK is what is zero) — both carried by the guard docstrings cited right. Tripwire B NOT built (mechanism refuted). Merge-commit gate `0c9cdeb`: **2977/7** + mypy strict 98 files, against a pass/fail read fixed BEFORE the run. Full narrative: the Session-160 CF block above | `0c9cdeb` (#846 merge, head_commit of record) / `d7bbb8b` (#845) / `c42abe4` (#844) / `0090161` (#843) / `tests/services/engine/procedures/test_sod_step_id_scope_guard.py` + `tests/services/engine/procedures/test_at2_signature_retrigger.py` + `docs/adr/0025-at2-managerial-layer.md` (D7 amendment) |
| 2026-07-21 | **s158 + s159 — PLAN-0087 BUILT (#840) then CLOSED at 8/8 ACs + archived (#841 `docs(plans)`): the ADR-0031 D3 gate seam's CRITERION-VOCABULARY half — `ComplianceCriterion` RETIRED from engine code; a vertical DECLARES its own `rule_gate` vocabulary in `procedures.yaml` (`VerticalProcedures.compliance_criteria`, pattern-typed + membership-validated at load), so a new AT-2 vertical ships its gate with ZERO engine diff — PROVEN by AC-1's fixture-criterion pair (loads + gates from outside `services/`; the undeclared twin refused), not prose.** Behaviour-preserving — no pinned governance hash moved. **Cray-ratified SD-1 = (a) (typed): the procedure-aware `ExecutorFactory` half is OUT of scope and stays owned by PLAN-0076 T1 → PLAN-0076 does NOT archive, its AC-6 guard stays ARMED, no re-homing.** ADR-0031 D3 row 3 updated per D4.4. Closeout gate on `main=c6eec65`: **2954/7** (169.91s) + mypy strict 98 files, matching the build. Full narrative: the Sessions 158+159 CF block above | `c6eec65` (#840 merge) / `e55f2b8` (head_commit of record, #841) / `services/engine/procedures/spec.py` + `tests/services/engine/procedures/test_declared_criterion_vocabulary.py` + `docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` (COMPLETE, 8/8) |
| 2026-07-21 | **s157 — PLAN-0086 COMPLETE (#838 `feat(verticals)`): the narrative→pipeline scaffolder run as a TIMED MANUAL baseline — a dirtied customer monologue → a live, governed, human-gated pipeline on the 6th vertical `fleet_maintenance` in 27m39s hands-on (wall 43m17s − 6m51s answer-waits − 8m48s escalation). AC-7 caveat, BINDING and never to be dropped: Code drafted the pre-dirtied narrative → LOWER BOUND on blind intake, operator knows this codebase.** AT-2 `governed_repair_approval` = the 4th signature; first vertical with the PLAN-0085 gate advisory ON by default; additive `ComplianceCriterion += three_quote`. **ADR-0025 D7 AT-2-generator deferral CANCELLED at N=4 (Cray-ratified, typed — 4th consecutive vertical forcing an engine-level criterion extension); the `_RETRIGGER_N` guard RETIRED + REPLACED by `test_at2_extraction_obligation_is_owned` (PLAN-0076 T1 = standing owner). The extraction PLAN is UNOPENED — G2-gated → `plan-drafter`.** 2 of 4 customer rules un-encodable (quote-comparison ฿ threshold has no home on a `rule_gate` criterion; `EmergencyWaiver` lacks cap/ratification fields) — surfaced in the vertical README's "stated but NOT enforced" table. Suite **2943/7**; mypy strict 98 files; ruff clean; live `run-b9c0804b52f0` parks `waiting_human` at `approve`. Full narrative: the Session-157 CF block above | `79358c6` (HEAD, #838 merge) / `a2ef45e` (build) / `verticals/fleet_maintenance/` + `tests/services/engine/procedures/test_at2_signature_retrigger.py` (guard replacement) + `docs/plans/0086-fleet-vertical-timed-manual-scaffold.md` (closeout pending) |
| 2026-07-21 | **s156 — PLAN-0085 "Advisory Gate Recommendation (AI-Transition Rung 1)" filed → 5 SDs Cray-ratified → BUILT → closed, ONE day (#831 Draft `docs(plans)` / #832 SDs `docs(plans)` / #833 `feat(engine)` / #834 closeout `docs(plans)`): an advisory recommendation with grounded reasons at procurement's `doa_tier` approval gate — SHOWN, NEVER routes (the ADR-0019:50-57 fence, now CI-pinned: byte-identical approve audit advisory on/off/exploding-builder).** All 5 SDs = the draft rec (AskUserQuestion): SD-1(b) emit INSIDE the gate propose path (ZERO hash change), SD-2(b) stub-first deterministic arm + opt-in live MS-S1 seam, SD-3 all three procedures, SD-4 gate-panel advisory block, SD-5 new trace kind `advisory_recommendation` (actor `llm`). New `gate_advisory.py` (never-raise, ADR-0030 D5) wired via `GovernanceActionExecutor` + procurement `_executors`; Monitor gate-panel block, NO score (the L-C/#823 trust shape). Suite **2927/7**; mypy/ruff clean; live-verified 8101. Unplanned value (Cray): the advisory doubles as an ONBOARDING aid → recorded as a signal for the View-2 reshape. Full narrative: the Session-156 CF block above | `2f46fc9` (#833 BUILT, head_commit of record) / `63009c3` (#834 closeout, main HEAD) / `8809776` (#831) / `d679036` (#832) / `services/engine/procedures/gate_advisory.py` + `docs/plans/done/0085-*.md` (archived, 8/8) + `docs/runbooks/run-oct-demo.md` §3e |
| 2026-07-21 | **s156 — the demo rehearsal (carried s153→155) PERFORMED + PASSED (Cray, Beats 1-5 on 8101 incl. the new PLAN-0084 map→monitor opening beat, ratified "ok"), which GATED the PLAN-0084 closeout (#830 `docs(plans)`, 9/9 ACs + archived to `done/`); + a morning map-label UI fix (#829 `fix(ui)`, `view-map.js ?v=c39`, plate moved BELOW the node, 0 overlaps live).** Cray then opened the two-view **AI-Transition** frame — (1) an LLM at the approval gate, (2) a narrative→pipeline scaffolder — and ratified the SEQUENCE: capture a discussion note → build View-1 (Rung 1 = PLAN-0085) → reshape View-2 against Rung-1's result → build View-2; umbrella thesis = governance human in/on-the-loop → first-stage AI automation (gitignored note, binds nothing). A model-economy policy ratified (private memory, not a repo change): Fable for complex planning/research, Opus 4.8 + Extra for execution/coding-to-plan. Full narrative: the Session-156 CF block above | `ad39774` (#830) / `19f5caa` (#829) / `docs/plans/done/0084-*.md` (archived, 9/9) + `.claude/handoffs/session-156/2026-07-21-0851-*-ai-transition-two-views.md` |
| 2026-07-20 | **s155 (late) — PLAN-0084 shipped end-to-end in one arc (#825 `docs(plans)` filed Draft → #826 `docs(plans)` all 5 SDs Cray-resolved [SD-B all-four-rotatable + SD-D both-entry-points, both WIDER than rec] → #827 `feat(demo)` BUILT): map↔monitor run linkage (runs stamp `trigger_context["subject"]`; fail-soft `subject` on RunSummaryView/RunDetailView; the map ingests `/runs` direct-fetch [never the mock-fallback O.API path], dashed amber in-flight ring, node-panel "Governed runs · in flight" + "Open in Monitor →" via `ViewMonitor.focusRun`/`oct:goto`) + opt-in seed rotation (`--asset`/`--rotate`, asset-keyed failure pick, all 4 non-hero assets).** **Headline = SD-F, Cray-ratified mid-build — the PLAN's grounding `was an error`: the registered procurement adapter was scaffold-era synthetic (`equip-*`) while every hero surface narrates Fastenal (`AST-*`) — split-brain demo; `register_procurement_adapter` now registers the `FastenalCsvAdapter`** (plant.csv geo anchor + part.csv stock fields; synthetic semantics preserved EXACTLY incl. the PLAN-0066 AC-6 flip case; 4 test repins — the PLAN-0083 canonical-coverage tripwire caught the new keys, WORKING AS DESIGNED). Live 8101 verification: strip LIVE, zero console errors, AC-4 full click-through + AC-9 event-run lights the map + AC-5 no-fallback + AC-7 tier rotation + AC-2 legacy fail-soft. Suite **2922/7** (2915 + 7 new); mypy strict 142 files; ruff clean. PLAN-0084 stays Draft, ACs deliberately UNTICKED — closeout after Cray's rehearsal passes. Full narrative: the Sessions 153+154+155 CF block above | `25b31e2` (HEAD, #827 merge) / `45fcba1` + `64119b9` (build) / `e5f3ede` (#826 merge) / `628bfa1` (#825 merge) / `docs/plans/0084-map-monitor-run-linkage-and-seed-rotation.md` (Draft, 6/6 SDs resolved) + `verticals/procurement/data_adapter/__init__.py:99` + `docs/runbooks/run-oct-demo.md` §3d |
| 2026-07-20 | **s153-155 — #822 `docs(runbook)` staged the config-pin fail-closed refusal as a deliberate demo beat (run-oct-demo.md §3c, Beat 06, PLAN-0047 Step 6); s154 ZERO commits (Cerebras-KB strategy read: predict+warn = existing Shape-1 IF deterministic, artifact-KB = D3 Shape-2 pilot-gated, org-wide ingestion CUT, reframe = "governed retrieval over the decision record"); #823 `fix(ui)` REMOVED the operator confidence badge from BOTH cards — story scene-2 (hardcoded 86%) and View-B `decisionCard()` (LIVE `rec.confidence`, the load-bearing one) — executing the ratified s74 trust shape.** Trace/fault-mode/DAG confidence KEPT by design. Static assets only; suite **2915/7** re-run on the merge commit `4edfa3f`; live 8101 check `LIVE` with a `confidence: 0.86` fixture. **4 claim-vs-code corrections:** naive-RAG comparison ALREADY run (PLAN-0027 — lean RAG TIES governed on accuracy at 3-15x lower latency) · "actions router fully governed" is overstated · the determinism line is ADR-0019:50-57 + ADR-010 IN-3, NOT ADR-0031 · a 4th AT-2 signature is UNBUILDABLE (no vertical has the substrate). Full narrative: the Sessions 153+154+155 CF block above | `4edfa3f` (HEAD, #823 merge) / `ffb251b` + `f09cc99` (badge removal) / `d8057fb` (#822 merge) / `b45f5c4` (#821 merge) / `docs/runbooks/run-oct-demo.md` §3c + `services/api/static/assets/view-anomaly.js` + `view-story.js` |
| 2026-07-19 | **s152 — PLAN-0083 (fix c1) BUILT + verified + archived (#818 `feat`, #819 `docs(plans)`): the procurement ontology↔CSV column drift CLOSED at the `FastenalCsvAdapter` seam — `_COLUMN_RENAMES` on the `fetch_objects` path maps raw Fastenal CSV → canonical ontology names (type key `Asset`→`Equipment` [SD-1] + 5 columns [`part_id`→`part_no`, `price_thb`→`price`, `asset_id`→`equipment_id`, `site`→`site_id`, `lead_time_days`→`lead_time`] + `PurchaseOrder.asset_id`→`equipment_id` [SD-4a]; ฿-columns DEFERRED raw [SD-4b]), so every consumer sees ONE canonical vocabulary.** Rides under ADR-016's LOCKED "mapping absorbs source diversity" boundary — zero-core-edit (no ADR / ontology YAML / regen / `services/` engine edit; ADR-0023), diff = adapter + vertical + tests only. A `test_fastenal_adapter_canonical_coverage.py` tripwire pins per-type set-equality + required-props + rename-target validity + the SD-4b ฿-defer, non-vacuous EMPIRICALLY (dropped a rename → RED → reverted); R2 added the under-scoped `governance_audit.py:177/179`. Suite **2915/7** (2896 + 19); mypy strict + ruff clean; CI gate PASS on #818. Full narrative: the Session-152 CF block above | `a53c6ed` (#818 merge) / `a211651` (build) / `5140ee3` (HEAD, #819 merge) / `docs/plans/done/0083-*.md` (archived) + `tests/verticals/procurement/test_fastenal_adapter_canonical_coverage.py` |

### Pre-trim originals — the 6 Active TODO items compressed to the R2 pointer rule [trimmed 2026-07-22, session-163]

Each was trimmed only after its tracked home was verified on disk (the R2 carve-out): PLAN-0087 + PLAN-0076 §A, PLAN-0076, PLAN-0062/0077/0078, the `tests/services/db/test_load_run_ordering_guard.py` module docstring, PLAN-0063 + the `services/api/routers/audit.py` SD-4 docstring, and the PLAN-0035 §SD-3 post-archival amendment.

- [ ] **The AT-2 extraction — PLAN-0087 is COMPLETE, 8/8 ACs, and ARCHIVED to `docs/plans/done/` (s159, #841); the CRITERION-VOCABULARY half SHIPPED (s158, #840) and only the F-FACTORY half remains, owned by PLAN-0076 T1.** ADR-0025 D7's generator deferral was **CANCELLED at N=4** (Cray-ratified, typed, 2026-07-21) after `fleet_maintenance` became the 4th consecutive vertical to force an engine-level `ComplianceCriterion` extension. **PLAN-0087** (`docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` — `plan-drafter`-authored, Code R2 + commits; closed out s159 with Status `Draft` → **COMPLETE** [never `Accepted` — that status G1-gates a PLAN's own closeout], all 8 ACs re-read against **fresh on-disk evidence**, plus a **Closeout** section recording the evidence read and what was deliberately left undone) discharges the vocabulary half: `ComplianceCriterion` is **retired from engine code**, each vertical **declares** its own `rule_gate` vocabulary in its `procedures.yaml` (`VerticalProcedures.compliance_criteria`, pattern-typed + membership-validated at load), and **a new AT-2 vertical ships its gate with ZERO engine diff** — proven by AC-1's proof pair (a fixture criterion existing nowhere in `services/` loads + gates, with a static guard keeping it that way), not asserted. Behaviour-preserving: **no pinned governance hash moved** (the declaration block is outside the pin surface — the `principals` precedent). Cray ratified the scope split **SD-1 = (a)** (typed, s158): **the procedure-aware `ExecutorFactory` half is NOT in PLAN-0087** and stays owned by **PLAN-0076 Step T1**, triggers armed — its evidence is an *inert* audit display-flag over-mark with zero live `step_id` collisions, versus the vocabulary half's 4-engine-edits-in-4-verticals. `test_at2_extraction_obligation_is_owned` still turns RED if PLAN-0076 is archived or loses the `N=4` record; **no guard re-homing occurred, deliberately** (re-homing is required only when PLAN-0076 archives, and T1 is only partially discharged). _[s159 closeout also left OPEN, deliberately: `scored_rule._KNOWN_CRITERIA` was NOT opened — zero extension pressure to date and its shape is `derive`-grammar-like, not vocabulary-like.]_ *(s157 #838 → s158 PR #840 → s159 closeout PR #841)*
- [ ] **PLAN-0075 follow-ons — homed by PLAN-0076 (`Status: Tracking`, filed #752, s133): T1, the ADR-0031 D3 gate-plugin seam (F-FACTORY), is now **PARTIALLY discharged** — its criterion-vocabulary half shipped as PLAN-0087 (s158, PR #840; PLAN-0087 itself COMPLETE + archived s159, #841), its procedure-aware-`ExecutorFactory` half stays OPEN and owned here — **PLAN-0076 itself stays in active `docs/plans/`, its AC-6 guard ARMED, no re-homing**; Step T2's F-PIN remainder CLOSED s143 (#784, PLAN-0078 PR-5).** _[T2 closed ≠ F-PIN closed: **F-PIN itself stays OPEN** (`docs/plans/done/0078-transform-seed-migration.md` L-4 — PLAN-0078 closed s144 COMPLETE at 12/12 and archived, but **no artifact records F-PIN closed**) — only T2's remainder fold-in closed, so **PLAN-0076 does NOT archive** and its guard stays ARMED.]_ A guardrail against the ADR-0031 OQ-4 deferral-rot precedent (s133 4-specialist panel); PLAN-0075 itself is **COMPLETE — all 13 ACs — and CLOSED → `docs/plans/done/0075-*.md`**. Full detail: `docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` — F-FACTORY `:61-127`. **Guard:** PLAN-0076's AC-6 presence guard-test (`tests/services/engine/procedures/test_at2_followon_tracking_guard.py`) turns the build RED on a premature archive-to-`done/` or a pruned STATUS pointer ("location≠tripwire; failing tests are the real anti-rot"). *(PLAN-0075 = #749/#751 → `done/`; PLAN-0076 = #752, `Status: Tracking`; T2 closed by #784.)*
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2) — open ONLY for the O-2 residue; every other leg is DONE + archived.** **Closed:** Q3 ontology data-binding (PLAN-0046) · the Q4 generic query executor (PLAN-0048) · the Q4 join/projection grammar (ADR-016 Q4 amendment #659 + PLAN-0061) · the per-vertical seed migration (PLAN-0062) · the per-entity `threshold_field` band arc (PLAN-0066/0067/0068/0070) · **Box-4 BUILT (PLAN-0071, AC-5 GREEN at N=4) + SURFACED IN THE HERO UI (PLAN-0073)** — all → `docs/plans/done/`. **The one OPEN residue:** procurement's `intake` is declared-expressible ✔ under shadow parity, but **production execution stays the co-existing `_SeedQuery` ✖ for derived fields** — `docs/plans/done/0062-per-vertical-seed-migration.md:348`, the SD-C co-exist decision `:54-60`, `:291-295`. **Now homed by the transform arc:** **PLAN-0077** (transform grammar, COMPLETE → `done/0077-*.md`) + **PLAN-0078** (**COMPLETE at 12/12 ACs, CLOSED s144 #786 → `done/0078-*.md`** — the Step-7 closeout swept AC-5/AC-6 and archived it; do NOT re-open) — the fold-in is named at `docs/plans/0076-*.md:170-174`, what stays seed-side at `docs/plans/done/0078-transform-seed-migration.md:150-155`. *(s84 strategy discussion; the Box-4 leg is DONE — the residue is the O-2 data-binding leg only.)*
- [ ] **Bounded/incremental chain verification (PLAN-0063 SD-4 follow-up, s118).** `GET /audit/verify` walks the WHOLE chain O(n) on demand — accepted at pilot scale, documented in the endpoint docstring (`services/api/routers/audit.py:13-16`). Future work = a checkpointed head / verify-since-anchor design; anchor storage ≈ external anchoring — **do not build without re-reading the tripwire: `docs/plans/done/0063-audit-chain-verification-surface.md:564` + `services/api/routers/audit.py:19`.** _[Corrected s141: this item used to say "ADR-011 tripwire territory" — **ADR-011 does not exist** (`docs/adr/` jumps 0010 → 0012; it is an earmark only); the tripwire text lives at the two anchors above.]_ *(s118; #688/#690)*
- [ ] **DEFERRED: a monotonic `sequence` column on `step_results` — the ROOT fix for `load_run`'s wall-clock ordering.** Needs a DB migration → its own PLAN (PLAN-0062-independent); none drafted. `ORDER BY created_at` is **unchanged by design**, so **the deferral STANDS**; both surviving orderings are **DISPLAY-ONLY**, so not urgent. Full detail — ROOT-vs-guard, why it is tolerable, the static AST guard holding the line: the module docstring of `tests/services/db/test_load_run_ordering_guard.py`, pointed to from both code sites. _[s161 UPDATE — **the deferral STANDS and this PLAN is still UNOPENED**: **PLAN-0088** (#848) is the first PLAN to read runs *in aggregate*, and it was written DELIBERATELY not to depend on either ordering — order-insensitive aggregates only, day-or-coarser buckets, no cross-row wall-clock arithmetic, plus its own AC-3 AST tripwire forbidding `ORDER BY` on raw wall-clock columns. The un-defer trigger is unchanged and now has a named watch-point: the pinned doctrine (`test_load_run_ordering_guard.py:29-49`) says *"if a correctness path ever starts depending on either ordering, the sequence-column PLAN stops being optional"* — so any Group-B / ordering-sensitive read proposed on top of the substrate re-opens this item FIRST.]_ *(rehomed s142; s117; #678/#680/#684)*
- [ ] **Demo card UX — "trust shape", NO operator confidence badge (s74 design, Cray-approved).** The operator card shows **what / grounded-why / approve gate** + a "show full reasoning trace" toggle; **no confidence badge** (`confidence_signal` is engine-internal QA, trace-only), and the **(B) first-class `verification` field is NOT needed** — SD-3 settles at (a). Full record + rationale + the reconsider-trigger: **`docs/plans/done/0035-governed-action-verify-reshape-build.md:576`** — the s142 post-archival amendment ANSWERING SD-3's Phase-2 question; `ADR-0030` cites it. *(Trigger: the next demo / UI round.)*

---

## Rotated this reconcile (session-163 second arc, 2026-07-22 — the PLAN-0090 pass)

### Recent-Decisions row rotated out of the 10-row window — s152 / PLAN-0083 (#818, #819) [rotated 2026-07-22, session-163 second-arc reconcile]

| 2026-07-19 | **s152 — PLAN-0083 (fix c1) BUILT + verified + archived (#818 `feat`, #819 `docs(plans)`): the procurement ontology↔CSV column drift CLOSED at the `FastenalCsvAdapter` seam — `_COLUMN_RENAMES` on the `fetch_objects` path maps raw Fastenal CSV → canonical ontology names, so every consumer sees ONE canonical vocabulary.** Zero-core-edit under ADR-016's LOCKED "mapping absorbs source diversity" boundary (ADR-0023); a `test_fastenal_adapter_canonical_coverage.py` tripwire pins per-type set-equality, non-vacuous EMPIRICALLY. Full narrative: the Session-152 CF block, rotated to `docs/status-archive/2026-h1-current-focus.md` | `a53c6ed` (#818 merge) / `a211651` (build) / `5140ee3` (HEAD, #819 merge) / `docs/plans/done/0083-*.md` (archived) + `tests/verticals/procurement/test_fastenal_adapter_canonical_coverage.py` |

### Rotation note rotated (R4 consolidation) — the session-161 note [rotated 2026-07-22, session-163 second-arc reconcile]

> _Rotation note (session-161 reconcile, 2026-07-22, `docs(status):`): added the
> **Session 161** CF block (PLAN-0088 filed Draft, #848 — the cross-run read
> substrate + run-insight readers; the L1/L2 forks Cray-ratified by typed
> selection) and rotated the OLDEST CF block — **Session 157** (PLAN-0086, the
> timed manual scaffold of the 6th vertical `fleet_maintenance` #838 + the
> ADR-0025 D7 AT-2-generator deferral CANCELLED at N=4) — to the Current-Focus
> rotation base `docs/status-archive/2026-h1-current-focus.md`. Rotating it is
> what **R2 requires**, not a headroom judgement: the 4 most-recent sessions are
> now 161 / 160 / 159 / 158, so the s157 block fell **outside** the window.
> Recent Decisions gained ONE row (the s161 PLAN-0088 arc) and rotated its ONE
> OLDEST — the **s150** row (PLAN-0082 Steps 5-7 + the PLAN-0081 fold,
> #809-#812) — to the rotation base `docs/status-archive/2026-h1-status.md`. The
> **session-157** rotation note was itself rotated to the same base (R4
> consolidation): the trail had been carrying **three** notes rather than two
> because the s160 reconcile deliberately left it — that dispatch scoped exactly
> one CF block + one RD row, and silently dropping an un-instructed block was the
> exact failure mode that session existed to fix — so this pass instructs it
> explicitly. Because this pass also ADDS a note, the trail stays at **three**
> (s161 + s160 + s159): converging to two needs a SECOND note rotated, which was
> not instructed here. Nothing is violated — the runbook sets no note-count rule
> (grep-verified this session); "two" is the file's own habit, not R2.
> Window after this reconcile: **CF = 3
> blocks covering the 4 newest sessions** (s161 + s160 + s158/159 — well under
> the 8-block cap); RD = 10 rows. **STATUS: 56,272 B → 59,697 B**
> (caller-measured, not estimated), against the 64 KB R1 ceiling — the standing
> headroom levers remain the Active-TODO trim (~4.66 KB) and the oversized RD
> rows (~1,200-1,600 chars each against the ~600 target), both R4-gated on
> appending the full originals to the archive first. Per the STATUS.md Rotation
> Policy (R1/R2/R4)._

<!-- rotated 2026-07-22, session-164 reconcile -->

> _Rotation note (session-163 reconcile, 2026-07-22, `docs(status):`): added
> the **Session 162** CF block (the four-PR arc — #850 the
> `PROCEDURE_ARCHETYPES` re-key and #851 PLAN-0089 filed, both merged during
> s161 and recorded LATE; #852 the AT-3 calm path BUILT; #853 the closeout,
> merged at the s163 open) and rotated **NO CF block**: Current Focus now holds
> **4 blocks covering sessions 162 / 161 / 160 / 159** (s158+159 share one
> block) — exactly the 4-most-recent-sessions window and well under the 8-block
> cap, so R2 requires no CF rotation this pass. Recent Decisions gained ONE row
> (the s162 PLAN-0089 arc, written as a ≤600-char pointer from birth) and
> rotated its ONE OLDEST — the **s151** PLAN-0081 governed-credit-HERO row
> (#814) — to the rotation base `docs/status-archive/2026-h1-status.md`. The
> rotation-note trail was carrying **three** (s161 + s160 + s159); this pass
> rotates **two out** (the s159 and s160 notes, to the same base) and adds one,
> so 3 − 2 + 1 = **2**, restoring the file's own habit (the runbook sets no
> note-count rule). One Active TODO was **RETIRED as discharged, not trimmed**:
> the "AT-2 stale `N=2` / `N=3` signature counts — doc drift across three
> artifacts" item is **FALSE as of session 160** — all three named artifacts
> were verified correct on disk (`services/engine/procedures/spec.py` states
> **N=4**, its surviving N=2/N=3 tokens being correctly-framed historical
> narrative of the firing arc; `docs/adr/0025-at2-managerial-layer.md` carries a
> dated 2026-07-22 **outcome amendment**, its "N ≥ 2" decision text deliberately
> PRESERVED rather than drift; `docs/adr/0032-*.md` is re-grounded to N=4) —
> discharged by **#845 / #846 (s160)**. Its full original text was emitted
> verbatim to the caller for the archive (R4).
> **PASS 2, same session and same PR — the R2 pointer-rule TRIM.** The 9 older
> Recent-Decisions rows (the s162 row was written to the rule at birth) and the
> 6 over-length Active TODOs were compressed to ≤ ~600-char pointers. **Counts
> are UNCHANGED — RD stays 10 rows, Active TODOs stay 13 items:** this is
> compression, not deletion, and every pre-trim original was appended to
> `docs/status-archive/2026-h1-status.md` BEFORE the trim landed (R4). Each item
> was trimmed **only after its tracked home was verified on disk** (PLAN-0087 +
> PLAN-0076 §A, PLAN-0076, PLAN-0062/0077/0078, the
> `tests/services/db/test_load_run_ordering_guard.py` module docstring,
> PLAN-0063 + the `services/api/routers/audit.py` SD-4 docstring, and the
> PLAN-0035 §SD-3 post-archival amendment). The ~600 budget is measured on the
> **Decision cell**, never the Reference column — R2's own wording ("full detail
> lives in the referenced ADR/PLAN/PR, which every row already links") makes the
> link the thing the rule preserves, so it cannot be what the budget consumes.
> **One carve-out HIT, retained verbatim at full length:** the s156
> model-economy ratification lives only in a private Tier-0 auto-memory, so it is
> not a duplicate and stays at full length until rehomed. **STATUS across both
> passes: 59,697 B → 61,616 B (reconcile) → 53,758 B (trim)** — caller-measured,
> not estimated — against the 64 KB R1 ceiling. Still above the 48 KB soft
> target, which the next reconcile inherits as its standing lever. Per the
> STATUS.md Rotation Policy (R1/R2/R4)._

| 2026-07-20 | **s153-155 — #822 `docs(runbook)` staged the config-pin fail-closed refusal as a deliberate demo beat (run-oct-demo.md §3c, Beat 06); s154 ZERO commits (Cerebras-KB strategy read: artifact-KB = D3 Shape-2, pilot-gated; reframe = "governed retrieval over the decision record"); #823 `fix(ui)` REMOVED the operator confidence badge from BOTH cards, executing the ratified s74 trust shape.** Trace/fault-mode/DAG confidence KEPT by design; 4 claim-vs-code corrections recorded. Full narrative: the Sessions 153+154+155 CF block, rotated to `docs/status-archive/2026-h1-current-focus.md` | `4edfa3f` (HEAD, #823 merge) / `ffb251b` + `f09cc99` (badge removal) / `d8057fb` (#822 merge) / `b45f5c4` (#821 merge) / `docs/runbooks/run-oct-demo.md` §3c + `services/api/static/assets/view-anomaly.js` + `view-story.js` |

## Rotated this reconcile (session-166, 2026-07-23 — the dispatch-quality + Lesson #0032 closeout, #866)

### Recent Decisions row removed — 2026-07-20 (s155 late — PLAN-0084 map↔monitor run linkage + seed rotation, #825/#826/#827) [rotated 2026-07-23, session-166 reconcile — 10-row RD window]

| 2026-07-20 | **s155 (late) — PLAN-0084 shipped end-to-end in one arc (#825 filed Draft → #826 all 5 SDs Cray-resolved → #827 `feat(demo)` BUILT): map↔monitor run linkage (runs stamp `trigger_context["subject"]`; the map direct-fetches `/runs`; node-panel "Open in Monitor →") + opt-in seed rotation (`--asset`/`--rotate`).** Headline = SD-F, Cray-ratified mid-build — the PLAN's grounding `was an error`: `register_procurement_adapter` now registers the `FastenalCsvAdapter` (split-brain demo closed). Live-verified on 8101. Full narrative: the Sessions 153+154+155 CF block, rotated to `docs/status-archive/2026-h1-current-focus.md` | `25b31e2` (HEAD, #827 merge) / `45fcba1` + `64119b9` (build) / `e5f3ede` (#826 merge) / `628bfa1` (#825 merge) / `docs/plans/0084-map-monitor-run-linkage-and-seed-rotation.md` (Draft, 6/6 SDs resolved) + `verticals/procurement/data_adapter/__init__.py:99` + `docs/runbooks/run-oct-demo.md` §3d |

## Rotated this reconcile (session-167, 2026-07-23 — the autonomy fork RESOLVED, A′ demotes the dispatch arm, #870/#871)

### Recent Decisions rows removed — both 2026-07-21 (s156: PLAN-0085 advisory gate recommendation; the demo rehearsal + AI-Transition frame) [rotated 2026-07-23, session-167 reconcile — 10-row RD window; two rows out because two went in: PLAN-0092 and the PLAN-0091 SD-5 promotion]

| 2026-07-21 | **s156 — PLAN-0085 "Advisory Gate Recommendation (AI-Transition Rung 1)" filed → 5 SDs Cray-ratified → BUILT → closed in ONE day (#831/#832 `docs(plans)`, #833 `feat(engine)`, #834 closeout): an advisory recommendation with grounded reasons at procurement's `doa_tier` approval gate — SHOWN, NEVER routes (the ADR-0019 determinism fence, now CI-pinned).** All 5 SDs = the draft rec; new `gate_advisory.py` (never-raise, ADR-0030 D5); Monitor gate-panel block, NO score (the #823 trust shape). Full narrative: the Session-156 CF block, rotated to `docs/status-archive/2026-h1-current-focus.md` | `2f46fc9` (#833 BUILT, head_commit of record) / `63009c3` (#834 closeout, main HEAD) / `8809776` (#831) / `d679036` (#832) / `services/engine/procedures/gate_advisory.py` + `docs/plans/done/0085-*.md` (archived, 8/8) + `docs/runbooks/run-oct-demo.md` §3e |
| 2026-07-21 | **s156 — the demo rehearsal (carried s153→155) PERFORMED + PASSED (Cray, Beats 1-5 on 8101), which GATED the PLAN-0084 closeout (#830 `docs(plans)`, 9/9 ACs + archived); + a map-label UI fix (#829 `fix(ui)`).** Cray then opened the two-view **AI-Transition** frame (LLM at the approval gate; narrative→pipeline scaffolder) and ratified the SEQUENCE: View-1 (Rung 1 = PLAN-0085) → reshape View-2 → build View-2. A model-economy policy ratified (private memory, not a repo change): Fable for complex planning/research, Opus 4.8 + Extra for execution/coding-to-plan. Full narrative: the Session-156 CF block, rotated to `docs/status-archive/2026-h1-current-focus.md` | `ad39774` (#830) / `19f5caa` (#829) / `docs/plans/done/0084-*.md` (archived, 9/9) + `.claude/handoffs/session-156/2026-07-21-0851-*-ai-transition-two-views.md` |

### In-Flight entries removed — the PLAN-0091 SD-5 entry (superseded by its new Recent Decisions row) and the autonomy-fork misfire ledger (settled argument; the fork closed s167 and the full case is preserved in `docs/plans/0092-stop-hook-dispatch-arm-demotion-to-suggestion.md`) [rotated 2026-07-23, session-167 reconcile]

- **PLAN-0091 SD-5 — AT-2 template placement: RESOLVED (a), Cray typed 2026-07-23 (s166; surfaced in #865, ratified in #869).** Step 4's design note promised the S1 classify surface would not grow and the API abstain guard would stay as-is; that is structurally false **if the template registers in the shared `REGISTRY`** (`generator/pipeline.py:225` builds the classify catalog from `REGISTRY.values()`; `:253`/`:258` route by label through the same dict; the `_archetype_disagreement` guard at `:188-202` only rejects an AT-2 gate when the model actually emits one in `step_gates` — its contract at `:186-187` says an empty step list is not a disagreement, so it is a second layer, not a guarantee). **RATIFIED (a) — the AT-2 template is owned by `services/engine/scaffolder/` and NEVER enters `REGISTRY`**, which makes the original promise true by construction: the classify path is byte-unchanged and ADR-0024 D7's abstain routing stays literally true. **SD-1 = (c) "no ADR" therefore stands undisturbed, Step 4 is UNBLOCKED, and all five SDs are closed — nothing in PLAN-0091 awaits a decision.** `test_archetype_templates.py:37` (`set(REGISTRY) == set(AT1_FAMILY)`) never fires; **any need to edit it means the SD-5 tripwire is firing** — STOP and re-open SD-5 rather than registering centrally. Full record: `docs/plans/0091-*.md` §SD-5. *(Owed at the next reconcile: promote this to a Recent Decisions row, which needs an R2 rotation of the oldest RD row into `docs/status-archive/2026-h1-status.md`.)*
- **The autonomy fork — Stop-hook misfires (running ledger, opened s165).** The Stop hook keeps dispatching work nobody ordered. **Tally: 3× s71 · 3× s163 · 3× s164 · 3× s165 · 2× s166 (both arcs, one each) = 14** — every one declined by Code via the trigger's own override clause, so the operational cost to date is wasted tokens, not wrong work. **s165's third fire was a NEW shape** — not a re-dispatch of in-flight work, but a wrong **artifact kind** (a new PLAN proposed for a short `CLAUDE.md` edit) sent to a **closed route** (`plan-drafter`, which is hook-denied on `CLAUDE.md`); each new shape would need its own prompt rule, which is why option (a) cannot keep up. **Root cause, grounded s165:** the #844 contentless-reason floor lives on the **proceed** arm only; the recurring misfires come down the **dispatch** arm, which never calls it — so the floor is unreachable, not out-argued. #843's prompt paragraph is likewise proceed-scoped and keyed to approval/merge vocabulary, which a spawn dispatch does not use. **Decisive against option (a) "write another prompt rule":** the rule for this exact failure mode (*already routed → PAUSE, never a second dispatch*) has been in the classifier prompt since PLAN-0034 (2026-06-21) and has failed in four separate sessions; s165's two fires were (1) ordering a `plan-drafter` spawn for a PLAN step already committed and (2) ordering a background watch already running. **Two grounding claims REFUTED s165:** option (b)'s "lexical rule collides with committed pins" — the pins constrain the *floor*, not the *hook*, so a second predicate threads cleanly; and option (c)'s "needs an input the hook does not have" — the Stop payload already carries `transcript_path`, and PLAN-0011's reader already renders tool-use blocks, so an in-flight spawn is visible. **Option (e), newly named:** the classifier backend defaults to local Ollama `gpt-oss:20b`, so every failure to date is that model's; flipping to Sonnet is config-only — but **not free**: the Sonnet path has a known API-key/org failure mode that fails G1/G2 closed, so it needs a probe before it is treated as a fallback. **Nothing depends on this fork** — it blocks no PLAN. "FLOOR, not a specificity judge" is **unratified** (code comments + a test docstring + STATUS only; zero ADR/PLAN backing), so changing it needs no ADR. **s166's fire was another NEW shape:** the D2 governance-drafting classifier fired on a conversation that was ANALYZING dispatch/PLAN mechanics — mention-as-intent (dense PLAN/dispatch/template vocabulary, zero drafting intent; Cray had typed "แค่คุยต่อ ยังไม่ทำ" the turn before) — ordering a `plan-drafter` spawn nobody asked for; declined via the trigger's own override clause. **The PLAN-0091 arc's fire (14th, same session, a THIRD new shape and the sharpest evidence yet) — it ordered a `plan-drafter` spawn to "Draft Plan 0091 steps", instructing the caller to enumerate `docs/plans/` and pass down "the next free NNNN".** But PLAN-0091 **already exists** (`Status: Draft`), and had been patched and merged as #865 minutes earlier — so obeying would have created a **duplicate PLAN under a fresh number** for work already on `main`. It also mis-scoped the route: editing an existing non-`Accepted` PLAN is **ungated for Code** (G2 fires on Write-of-a-new-file, G1 on `Status: Accepted`), so no drafter was needed at all. Same mention-as-intent root as the 13th (a session densely discussing PLAN steps and dispatch mechanics), but the failure is now on the **artifact-identity** axis — the classifier cannot tell "the PLAN exists and was just edited" from "a PLAN needs drafting". **Cumulative shape count: re-dispatch of in-flight work · wrong artifact kind to a closed route · mention-as-intent · non-existent-artifact assumption.** Four distinct shapes in three sessions is the case against option (a) restated empirically: a prompt rule per shape is a losing race.

### Recent Decisions row removed — 2026-07-21 (s157 — PLAN-0086 COMPLETE, the timed manual scaffold baseline, #838) [rotated 2026-07-23, session-168 reconcile — 10-row RD window]

| 2026-07-21 | **s157 — PLAN-0086 COMPLETE (#838 `feat(verticals)`): the narrative→pipeline scaffolder run as a TIMED MANUAL baseline — a dirtied customer monologue → a live, governed, human-gated pipeline on the 6th vertical `fleet_maintenance` in 27m39s hands-on. AC-7 caveat, BINDING: a LOWER BOUND (Code drafted the pre-dirtied narrative).** ADR-0025 D7's AT-2-generator deferral CANCELLED at N=4 (Cray-ratified, typed); `_RETRIGGER_N` RETIRED, replaced by `test_at2_extraction_obligation_is_owned` (PLAN-0076 T1 owns). Full narrative: the Session-157 CF block, rotated to `docs/status-archive/2026-h1-current-focus.md` | `79358c6` (HEAD, #838 merge) / `a2ef45e` (build) / `verticals/fleet_maintenance/` + `tests/services/engine/procedures/test_at2_signature_retrigger.py` (guard replacement) + `docs/plans/0086-fleet-vertical-timed-manual-scaffold.md` (closeout pending) |

### Recent Decisions row removed — 2026-07-21 (s158 + s159 — PLAN-0087 gate-seam declared criterion vocabulary, #840/#841) [rotated 2026-07-23, session-168 reconcile — 10-row RD window]

| 2026-07-21 | **s158 + s159 — PLAN-0087 BUILT (#840) then CLOSED at 8/8 ACs + archived (#841 `docs(plans)`): the ADR-0031 D3 gate seam's CRITERION-VOCABULARY half — `ComplianceCriterion` RETIRED from engine code, a vertical DECLARES its own `rule_gate` vocabulary in `procedures.yaml`, so a new AT-2 vertical ships its gate with ZERO engine diff (PROVEN by AC-1's fixture-criterion pair, not prose).** Behaviour-preserving — no pinned governance hash moved. Cray-ratified SD-1 = (a) (typed): the procedure-aware `ExecutorFactory` half stays owned by PLAN-0076 T1, its AC-6 guard ARMED. Full narrative: the Sessions 158+159 CF block above | `c6eec65` (#840 merge) / `e55f2b8` (head_commit of record, #841) / `services/engine/procedures/spec.py` + `tests/services/engine/procedures/test_declared_criterion_vocabulary.py` + `docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` (COMPLETE, 8/8) |

### Recent Decisions row removed — 2026-07-22 (s162 — PLAN-0089 fleet AT-3 calm path filed→built→archived, #850–#853) [rotated 2026-07-24, session-170 reconcile — 10-row RD window]

| 2026-07-22 | **s162 — PLAN-0089 filed (#851) → BUILT (#852) → COMPLETE 6/6 + archived (#853): `fleet_maintenance.pm_service_round`, the AT-3 calm path, as a measured "extend an existing vertical" experiment — ~14 min hands-on, ZERO engine diff PROVEN (`git diff df1982a..a8d679d -- services/engine/` EMPTY).** M-6 BINDING: a lower bound, never summed with PLAN-0086's 27m39s. + #850 `fix(api)` re-keyed `PROCEDURE_ARCHETYPES` on `(vertical, procedure_id)`. AT-3 GENERALIZED to "a measure vs a per-entity threshold"; N stays 4. Gate on `a8d679d`: 2978/8/5. Full narrative: the Session-162 CF block above | `1b942f5` (#853 merge, head_commit of record) / `a8d679d` (#852 build) / `df1982a` (#851) / `514dc1f` (#850) / `docs/plans/done/0089-fleet-calm-path-extend-an-existing-vertical.md` (COMPLETE, 6/6) |

## Rotated this reconcile (session-171, 2026-07-24 -- the R2 pointer-rule enforcement pass: Recent Decisions, In-Flight Discussions and Active TODOs trimmed to pointers in STATUS; the full pre-trim text is preserved here)

### Recent Decisions + In-Flight Discussions + Active TODOs -- full pre-trim text, as they stood on `main` `45785a7` [rotated 2026-07-24, session-171]

_Not a window rotation: the R2 rolling window was untouched (Current Focus keeps its 4 sessions). What moved here is the narrative BODY of rows that R2 requires to be pointers (<= ~600 chars) and had grown to 4.3x that. Every row below still exists in `docs/STATUS.md`, compressed to a pointer; this is the long form._

## Recent Decisions (last 10)

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-24 | **s170 — PLAN-0088 Step 4 BUILT (#895): reader A4, audit-readiness at `GET /insights/audit-readiness` (AC-7) — status/gate/refusal counts + the public chain verdict via the shipped `verify_chain` seam; no SQL of its own (L3), zero LLM, split visibility STRUCTURAL (`extra="forbid"`, no field could carry a break string). Headline: a MUTATION PROBE caught an oracle that could not fail — deleting the approver `FILTER` reddened ONLY the SQL-shape assertion, both exact-value oracles stayed GREEN, because the CORPUS (every resolved gate carried an approver), not the assertions, was the defect. Corpus gap `i % 15 == 6` fixed it → the same mutation now reddens THREE oracles. Suite 3150 → **3159**. Then, after the close, **SD-9 surfaced (#897) and RULED (a2) by Cray (#898)**: S5's declared A1 properties are unservable by the shipped substrate, **no primitive accepts a parameter at all**, and AC-10's B1–B4 are equally unserved — so the "substrate is complete" premise Steps 2–4 ran on was never true. Ruling extends the substrate in `run_analytics.py` **only** and eliminates `agent_id` + `trigger` from v1; **Step 4.5** created, Step 5 un-gated. Precedent: the invariant is **S1 + AC-11**, not a frozen primitive inventory. **Step 4.5 then BUILT (#900)** — `run_status_rollup` / `week_rollup` / `run_duration_totals`, the last with the per-run SUM as an **inner subquery** so only the aggregate escapes (returning inner rows = O(runs) = the listing shape SD-8 struck). Probed one-per-primitive; each reddened exactly its own exact-value oracle while **statement-capture stayed GREEN — it pins query SHAPE, not value correctness**. Suite 3159 → **3163**. **Then Step 5 BUILT (#902): AC-8 + AC-9** — `POST /insights/query` + `run_query.py`, which **reuses `nl_query`'s validator** so S5's "preserved by construction" is literally true; `agent_id`/`trigger` absent per SD-9 (a2); `list` rejected as a *correctable* validation error (SD-8); **an empty result short-circuits without invoking the phrase stage** (describing zero matches is how a fabricated figure gets in). Suite → **3178**. **AC-9b (live MS-S1 smoke) remains OPEN — host-state.** Full narrative: the Session-170 CF block above | `5d02538` (#902 merge, head_commit of record) / `5a7c232` (Step-5 build) / `0195cdf` (#900 merge) / `9f31732` (Step-4.5 build) / `46f0ba1` (#898, the SD-9 ruling) + `a46bec4` / `776afee` + `27f5af0` (#897, SD-9 surfaced) / `7150c07` (#895 merge) / `a0d2939` + `501b169` (Step-4 build) / `09b90bc` + `06b54cb` (#894, −596 B net) / `docs/plans/0088-…md` §SD-9 + `services/db/run_analytics.py` |
| 2026-07-24 | **s169 — PLAN-0088's design layer ADJUDICATED: the re-draft (#888) surfaced a four-item JOINTLY-UNSATISFIABLE knot; Cray ratified SD-1…SD-8 in ONE typed pass (#889) — SD-8 = (a) ELIMINATE.** `list_runs_page` + AC-12 STRUCK: the substrate ships aggregate primitives only, `GET /runs` untouched, listing pagination sequenced into the future monotonic-`sequence`-column PLAN. First real-case reading of that deferral's un-defer trigger — and it **DECLINES to fire it** (the aggregate readers are order-insensitive). AC-12 kept as a **tombstone** so AC-1…AC-13 numbering stays stable (live count 13). Second correction, `was an error`: AC-12 undercounted `/runs` consumers — `view-map.js` fetches `/runs` bare and TRUNCATES via a `CAP = 5` slice under a newest-first assumption, so an order change HIDES the newest runs. Step 0 DISCHARGED → build-ready (Status stays `Draft`). Full narrative: the Session-169 CF block above | `dd16267` (#889 merge) / `4ef7b5d` (the rulings) / `8d1be34` (#888 merge) / `3a16238` (the re-draft) / `docs/plans/0088-cross-run-read-substrate-and-run-insight-readers.md` §Surfaced decisions |
| 2026-07-24 | **s169 — PLAN-0088 Steps 1–3 BUILT (#890, #891, #893): the cross-run read substrate (AC-1/2/3/11) + reader A2, the ฿ ROI rollup at `GET /insights/impact` (AC-4/5) + reader A3, the flow report at `GET /insights/flow` (AC-6).** Seven read-only async primitives (caller-owned `AsyncSession`, mirroring `audit_log.py`); a seeded 250-run × 6-step corpus with a plain-Python oracle independent of the SQL under test; two AST guards with guard-fires-on-what-it-forbids tests. Step 2 **EXTENDED** `benefit_rollup` (L3: readers write no SQL); `ImpactReport` has **no cross-currency total field and must never gain one** (S7). Step 3 added `waiting_dwell_stats`: SAME-ROW `waiting_human` dwell clamped via `GREATEST(span, 0)` + a surfaced `negative_clock_spans` counter, zero LLM — plus the AC-6 "dwell" caveat (start → suspension; flagged for Cray, see In-Flight). Suite 3109 → **3150** (+17/+17/+7), re-run on the merge commit; non-vacuity probed (`/tmp` restore + `cmp -s`); MS-S1 never contacted. Full narrative: the Session-169 CF block above | `9e26195` (#893 merge, head_commit of record) / `0d11da4` (#893 build) / `8393af8` (#891 merge) / `0be589e` (#891 build) / `b1e12d1` (#890 merge) / `c209bd9` + `2fba64b` (#890 builds) / `services/db/run_analytics.py` + `services/api/models/insights.py` + `services/api/routers/insights.py` + `tests/support/run_corpus_factory.py` |
| 2026-07-23 | **s168 — PLAN-0091 COMPLETE 10/10 + ARCHIVED (#883–#885): closing it exposed that the emitted package could not LOAD and `vero-lite scaffold` wrote NOTHING — both invisible to a green suite (a suite addressed at the library cannot see a dead entry point). Suite 3083 → 3109; honesty correction: s167's "8/10" was 7/10.** Full narrative: the archived PLAN | `c2b92c5` (#886 merge, head_commit of record) / `5865d19` (#885 AC-10) / `4994801` (#884 CLI wiring) / `844eb6d` (#883 AC-7 a/b/c) / `c47232f` (#882) / `b8f011d` (#881) / `docs/plans/done/0091-narrative-to-vertical-scaffolder-tool.md` (COMPLETE, 10/10) + `services/engine/scaffolder/**` + `services/engine/cli.py` |
| 2026-07-23 | **s168 — PLAN-0092 closed 6/6 + archived (#881); the `AT2_ONLY_KINDS` drift fixed with an anti-drift tripwire (#882); SD-D settled — the classifier prompt reworded to a ROUTING SUGGESTION, decision value + reply schema pinned UNCHANGED (#886).** Full narrative: the archived PLAN | `c2b92c5` (#886 merge) / `c47232f` (#882 merge) / `b8f011d` (#881 merge) / `.claude/hooks/_sonnet_classifier.py` + `tests/handoffs/test_sonnet_classifier.py` + `tests/services/engine/procedures/test_archetype_templates.py` + `docs/plans/done/0092-stop-hook-dispatch-arm-demotion-to-suggestion.md` (COMPLETE, 6/6) |
| 2026-07-23 | **s167 — the autonomy fork RESOLVED + SHIPPED in one session: option A′ (Cray, typed) DEMOTES the Stop-hook `dispatch` verdict from an ORDER to a SUGGESTION (#870 filed, #871 built).** No directive on `dispatch`: pause semantics + stop-chain RESET, routing sent as one `stop_dispatch_suggestion` ping. `_sonnet_classifier.py` byte-unchanged; V1 goal-gate + PreToolUse arms untouched. No ADR amendment — the arm had zero ADR backing, so the PLAN IS the governance record. Ledger: 14 misfires / 0 valid fires. **The argument is settled history in the archived PLAN — do not restate it here** | `7c86752` (#871 merge, head_commit of record) / `0870266` + re-sync `6afaf9c` (build) / `822a7e8` (#870) / `.claude/hooks/stop_continuation.py` + `tests/handoffs/test_stop_continuation.py` + `docs/plans/done/0092-stop-hook-dispatch-arm-demotion-to-suggestion.md` _[path fixed s170: archived to `done/` at s168]_ |
| 2026-07-23 | **s166 — PLAN-0091 SD-5 RATIFIED (a), Cray typed (#869): the AT-2 template is owned by `services/engine/scaffolder/` and NEVER enters the shared `REGISTRY`** — Step 4's design promise true by construction; the classify path stays byte-unchanged and ADR-0024 D7's abstain routing stays literally true. All five SDs closed. Tripwire: `test_archetype_templates.py:37` (`set(REGISTRY) == set(AT1_FAMILY)`) must never need editing — if it does, STOP and re-open SD-5 rather than registering centrally | `097d180` (#869 merge) / `9eb7c90` + `1413383` / `docs/plans/done/0091-narrative-to-vertical-scaffolder-tool.md` §SD-5 + `tests/services/engine/procedures/test_archetype_templates.py:37` _[path fixed s170]_ |
| 2026-07-23 | **s166 — dispatch-quality discipline shipped (#866, docs-only): the `code-operational-policy` skill gains the 3 dispatch blocks (Frontier/anti-anchoring · oracle-scoped accelerator · REJECT-if) + the M1–M4 follow-up vocabulary + the pre-close counterexample step; Lesson #0032 files the why.** Deliberately NOT built: any hook/detector for M3/M4 (judgment-shaped) — adoption is Rule-of-Three on recorded catches | `b8566a6` (#866 merge, head_commit of record) / `0a1cbe4` + `9200552` / `.claude/skills/code-operational-policy/SKILL.md` + `docs/lessons/0032-ambition-scales-with-oracle-exploration-gated-not-planned.md` |
| 2026-07-22 | **s164 — PLAN-0091 filed Draft (#859): the narrative→vertical scaffolder (`vero-lite scaffold`), 10 ACs / 8 Steps, create-shape only — BUILD-BLOCKED until Cray adjudicated Step 0.** A 4-agent Explore fan-out REFUTED two claims: the scaffolder is **brownfield-with-a-ratified-half** (ADR-0024 pins the generation contract; PLAN-0040 shipped narrative→procedure), and **PLAN-0088 had 12 defects, not 6** — its own **AC-3 ⊗ AC-12 trilemma** blocked it, not the pilot gate. Both since resolved (s168 / s169) | `f758509` (#859 merge, head_commit of record) / `74a49c2` / `docs/plans/done/0091-narrative-to-vertical-scaffolder-tool.md` _[path fixed s170]_ |
| 2026-07-22 | **s163 — PLAN-0090 filed (#855) → BUILT (#856) → COMPLETE 7/7 + archived (#857): `fleet_maintenance.scheduled_pm_service_round`, the AT-3 SCHEDULED calm path — 16m13s hands-on, steps BYTE-IDENTICAL to the manual path (PROVEN by a dumped-model test).** MS-6 BINDING: a LOWER BOUND, never summed with PLAN-0086's 27m39s or PLAN-0089's ~14 min. A DISTINCT `procedure_id`, never a trigger flip. + the L3 CLI fix: the unwired daemon CRASHED at startup (not "409s at resolve"); a set-equality tripwire now mirrors `main.py`. Gate on `a3ef955`: 2994/7. Full narrative: the Session-163 CF block above | `1ce3546` (#857 merge, head_commit of record) / `a3ef955` (#856 build) / `20f2585` (#855) / `2d34d80` (#854 reconcile + trim) / `docs/plans/done/0090-fleet-scheduled-calm-path.md` (COMPLETE, 7/7) |

## In-Flight Discussions

- **PLAN-0091 — COMPLETE 10/10 and ARCHIVED (s168).** Full record: `docs/plans/done/0091-narrative-to-vertical-scaffolder-tool.md`. **Two follow-ons it named, neither scheduled:** the **extend shapes** (calm-path + scheduled-variant scaffolding) are **greenfield, not an extension** — s169 re-confirmed the shipped emitters refuse an existing vertical *by construction* (`services/engine/cli.py` + the scaffolder's `wire.py`), and create-only is Cray-ratified SD-2, so this needs a fresh seam spec, not effort; and the census-narrative comment in `tests/api/test_procedures_endpoint.py` is the one counted site the disposer REPORTS rather than rewrites (`residual_counted_prose`) — a human call, left visible on purpose.
- **PLAN-0088 — RATIFIED and BUILDING: Steps 1–4 shipped (#890/#891/#893/#895); Steps 5–6 open.** SD-1…SD-8 are Cray-ratified (#889); **SD-8 = (a) ELIMINATE** struck `list_runs_page` + AC-12, so the substrate stays aggregate-only, `GET /runs` is untouched, and listing pagination moves to the future monotonic-`sequence`-column PLAN. Group A remains ungated by ADR-0032 D2 (proven by the AC-11 static guard, not prose); Group B stays pilot-gated (L2). **Step 4 SHIPPED (#895)** — reader A4 at `GET /insights/audit-readiness` (AC-7): `EXISTS`-shaped gate counts carrying the approver half, status + refusal counts, and the public chain verdict via the shipped `verify_chain` seam, read-only with split visibility structurally preserved. Remaining: **Step 5 (AC-8/9/9b — AC-9b is host-state: explicit Cray go required; and see (3) below, its scope is not yet settled)**, then Step 6 (AC-10/AC-13). **Four open questions, flagged for Cray and deliberately NOT self-edited.** (1) **AC-2's wording is wrong about where the gate approver lives.** AC-2 says the factory seeds "gate resolutions with `step_principals` approver halves", but every write to `run.step_principals` (`orchestrator.py`, `persistence.py`) writes the **REQUESTER** half; the approver is recorded by `resolve_gated_step` in three other places — the step `reasoning_trace` (`gate_principal_recorded.principal_id`), `StepResult.audit["governed_decision"].principal_id`, and the `audit_log` `gate_decision` row. The factory seeds it the way the engine actually records it, and Step 4's `approver_recorded` reads the TRACE and names that source explicitly so the confusion cannot return quietly. Steps 1–4 unaffected; it matters for **AC-10's B2**, which must join those three sources. Classified `was an error` in the AC wording. (2) **AC-6's "dwell"** is an AC-wording imprecision, not a code defect — the S4-sanctioned SAME-ROW span measures **start → suspension** for a run whose last write was its suspension, not elapsed-since-suspension; stated at `services/db/run_analytics.py:177-186` + `services/api/models/insights.py:93-102` (detail: the s169 CF block). (3) **NEW (s170) — S5 contradicts itself, so Step 5's scope is unsettled.** S5 says the A1 executor "adds no SQL of its own", but the numeric properties S5 itself declares — `duration_ms_total` (per **run**) and `started_week` — have **no shipped primitive**: `duration_stats` is per-**step** and `period_rollup` is per-**day**. Step 5 therefore needs 1–2 NEW substrate primitives, contrary to the "substrate is done, readers add no SQL" framing Steps 2–4 have been operating under. Cray's call: amend S5's wording · add a Step 1.5 · or narrow A1's declared properties. (4) **NEW (s170) — Step 6 needs the Step-1 corpus factory REOPENED.** B2 (per-tier approval outcome) cannot be written against what is seeded: the factory has **never seeded a reject**, hardcodes a single tier `"t1"`, and gives every run an identical `trigger_context` (so B4 has no trigger diversity to measure); refusals are keyed by kind only, not kind × procedure (B3). B2 also needs the hardest query in the PLAN — two-to-three correlated JSONB laterals on the same `StepResult` row, where the current hardest (`benefit_rollup`) joins one.
- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13; guarded trial (parallel to ADR-012) — verdict **continue-with-adjustments**. Run 1 (energy, s93) + Run 2 (supply-chain, s94) both COMPLETE, S-checks all PASS against pre-committed oracles, no R-PS trigger fired; C-1..C-3 CONFIRMED → **no open partner-sim debt**. ADR-011 audit stays gated on a REAL partner conversation (R3: SYNTHETIC provenance INFORMS but never TRIGGERS it). Full record: `docs/adr/0020-*.md` + the gitignored run packages `docs/research/private/2026-07-02-partnersim-run{1,2}-*.md`. _(Full prior narrative — the ~8 schema-mismatch findings, both run details, cross-run synthesis — archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **Procurement vertical — GO + SHIPPED (PLAN-0036 Fastenal, Stage 1):** 4th vertical greenlit (s75); PLAN-0036 drafted + merged Draft (#412, `7a7c036`; SD-1…SD-5 confirm-all). Demo target = Fastenal Thailand (auto-parts / EEC); **hero** = asset-failure → governed emergency sourcing, **calm-path** = low-stock reorder. Stage 1 = a PLAN-only pure-config plugin on the ADR-016 engine (zero `services/` core edit; CQ-1 / ADR-0023). **Pitch** = asset-ontology-triggered governed sourcing (native ontology ADR-008 + engine ADR-016), NOT the commoditized "governed"/"cross-vertical" claims. Full record: `docs/plans/0036-*.md` + the s72 de-risk dossier `docs/research/private/2026-06-22-procurement-*.md` (5 files: spec-expressiveness, GTM, asset-aware incumbent scan, AI-sourcing teardown, platform-incumbent deepdive). _(Full prior narrative archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).
- **The autonomy fork — Stop-hook misfires: CLOSED s167, no longer an open question.** RESOLVED by **option A′** (Cray, typed) and SHIPPED the same session — the `dispatch` verdict is a **suggestion, not an order** (#870 filed, #871 built). Final ledger: **14 recorded misfires across 5 sessions against 0 recorded valid dispatch-arm fires** in ~2 months live; four shapes in two families (knowledge · judgment). **The whole argument — the shapes, the families, the rejected options, the scope locks, the honest caveat that an unrecorded valid fire cannot be fully ruled out — is settled history preserved in `docs/plans/done/0092-stop-hook-dispatch-arm-demotion-to-suggestion.md`; do not restate it here.** _[path fixed s170: archived to `done/` at s168 — the entry still cited the active-plans path.]_ _[Corrected s169: this entry still listed **SD-D** as PARKED — it was **CLOSED s168 (#886)**, the classifier prompt reworded to a routing suggestion with two contract tests.]_ Live remainder: only **option (e)** (flip the classifier backend from local Ollama `gpt-oss:20b` to Sonnet), **deferred**, its API-key/org fail-closed probe unrun. Full narrative: the Session-167 CF block above.

## Active TODOs

- [ ] **The AT-2 extraction — only the F-FACTORY half remains, owned by PLAN-0076 T1.** The criterion-vocabulary half SHIPPED as PLAN-0087 — COMPLETE 8/8, ARCHIVED (s158 #840, s159 #841). ADR-0025 D7's generator deferral was CANCELLED at N=4 (Cray-ratified, typed). Cray-ratified SD-1 = (a): the procedure-aware `ExecutorFactory` half stays with PLAN-0076 T1, guard `test_at2_extraction_obligation_is_owned` ARMED. Full detail incl. the Closeout and the deliberately-unopened `scored_rule._KNOWN_CRITERIA`: `docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` + `docs/plans/0076-*.md` §A.
- [ ] **PLAN-0075 follow-ons — homed by PLAN-0076 (`Status: Tracking`, #752, s133).** T1 (ADR-0031 D3 gate-plugin seam, F-FACTORY) is PARTIALLY discharged: the criterion-vocabulary half shipped as PLAN-0087 (#840/#841); the procedure-aware-`ExecutorFactory` half stays OPEN and owned here. T2's F-PIN remainder CLOSED s143 (#784) — but **F-PIN itself stays OPEN**, so PLAN-0076 does NOT archive and its AC-6 presence guard (`test_at2_followon_tracking_guard.py`) stays ARMED. PLAN-0075 is COMPLETE (13/13) → `docs/plans/done/0075-*.md`. Full detail: `docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` §A.
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2) — open ONLY for the O-2 residue.** Every other leg is DONE + archived (PLAN-0046/0048/0061/0062/0066/0067/0068/0070/0071/0073 → `docs/plans/done/`). **The one OPEN residue:** procurement's `intake` is declared-expressible under shadow parity, but production execution stays the co-existing `_SeedQuery` for derived fields. Full detail: `docs/plans/done/0062-per-vertical-seed-migration.md` (SD-C — the co-exist decision + its STOP-and-surface tripwire) + the transform arc `done/0077-*.md`/`done/0078-*.md` (both COMPLETE), where the residue is homed and walled in **`done/0078-*.md` §L-3 + its Out-of-Scope**. _[Corrected s167, classified `was an error`: this entry previously said the fold-in "is named in `docs/plans/0076-*.md`". It is **not** — PLAN-0076 has **zero** hits for `_SeedQuery` / `candidate_quotes` / nest / reshape / shadow-parity / O-2 and tracks only F-FACTORY (SoD-scoping) + F-PIN (derivation-pin). Verified by scoped grep.]_
- [ ] **Bounded/incremental chain verification (PLAN-0063 SD-4 follow-up, s118).** `GET /audit/verify` walks the WHOLE chain O(n) on demand — accepted at pilot scale. Future work = a checkpointed head / verify-since-anchor design; anchor storage ≈ external anchoring — **do not build without re-reading the tripwire** in `docs/plans/done/0063-audit-chain-verification-surface.md` + the `services/api/routers/audit.py` module docstring (SD-4). _[Note: the docstring's "ADR-011 boundary" is an EARMARK — `docs/adr/` jumps 0010 → 0012.]_ *(#688/#690)*
- [ ] **DEFERRED: a monotonic `sequence` column on `step_results` — the ROOT fix for `load_run`'s wall-clock ordering.** Needs a DB migration → its own PLAN; none drafted, the deferral STANDS, and both surviving orderings are DISPLAY-ONLY. Full detail (ROOT-vs-guard, why it is tolerable, the AST guard, the un-defer trigger): the module docstring of `tests/services/db/test_load_run_ordering_guard.py`. _[s169: the un-defer trigger got its FIRST real-case reading and **did not fire** — Cray's SD-8 = (a) ELIMINATE removed PLAN-0088's paginated listing rather than un-defer the key, so the shipped substrate is aggregate-only and order-insensitive (AC-3 AST tripwire holds). **This PLAN now also owns newest-first `/runs` listing pagination**, and `view-map.js` (a `CAP = 5` truncating consumer) is a second dependant to respect when it opens.]_
- [ ] **Rock 4 — s84 deep research DELIVERED → O-sequence locked.** Cray locked **O-1 → O-3 → O-2 → O-4**. **O-1** (Box-4 ฿ pitch) **DONE** · **O-3 = ADR-0025 Accepted** · **O-4 = PARK** (agent-interop; `docs/adr/0032-*.md:169` D4 — option-only, un-park = a counterparty's *written* pull). **Remaining: O-2 only** (economic-impact facet + Q3 data-binding = Rock 3). Full detail: `docs/adr/0025-at2-managerial-layer.md:19` (O-sequence + Box-3 fit) + `:23-29` (the **evidence-asymmetry** finding — bullish ROI all vendor-authored, independent mostly skeptical — rehomed s142). *(s84 Cray ask)*
- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten. **Full table (all six rows + their triggers + where each lands): `docs/plans/done/0005-oct-engine-runtime-layer.md:390` §8.1** — which itself instructs this STATUS entry to be a pointer. *(per Cray note 2026-05-21)*
- [ ] **Demo card UX — "trust shape", NO operator confidence badge (s74 design, Cray-approved).** The operator card shows what / grounded-why / approve gate + a "show full reasoning trace" toggle; no confidence badge (`confidence_signal` is engine-internal QA, trace-only), and SD-3 settles at (a) — the first-class `verification` field is NOT needed. Full record + rationale + the reconsider-trigger: the §SD-3 post-archival amendment in `docs/plans/done/0035-governed-action-verify-reshape-build.md`; `ADR-0030` cites it. *(Trigger: the next demo / UI round.)*
- [ ] **PLAN-004 Phase C — OPTIONAL POLISH (forward-declared; "may never land"):** HTML/markdown handoff dashboard under `docs/` + references-graph (mermaid dispatch chains) + `render_transcript.py` unified session export (PLAN-0004 §"Phase C"). *(Phase A + B both COMPLETE — session 35; the prior TODO's validator **warning-swallow bug was FIXED #312**, s58. Minor never-formally-scoped sub-ideas — README/`_rename-map` walk-exclusion, Cat G `references_*` autofix, OQ-2 effective-vs-authored `status:` dashboard flag — fold in only if Phase C lands. Reconciled 2026-06-16 s65 audit.)*
- [ ] **Custom Postgres image with extensions (pgvector / AGE / pg_trgm) — needs a fresh ADR number + a PLAN; neither drafted.** *[Corrected s141: **PLAN-002 does not exist** ("NOT yet drafted", `docs/plans/done/0005-oct-engine-runtime-layer.md:14`), and the old "≥ ADR-014" floor is **moot** — ADRs now run to 0032 and `0014-WITHDRAWN.md` exists.]* Context: **`docs/adr/0013-autonomy-axis-relocation.md:285-289`** (the floor-bump note) + **`docs/plans/done/0005-*.md:403`** (trigger: semantic + graph features).
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (low priority)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)

## Rotated this reconcile (session-173, 2026-07-25 — the loop-detect guard pass, #912/#914)

Recent Decisions rows rotated because **R2 caps the table at the last 10**: the session-172 (PLAN-0093 COMPLETE) and session-173 (loop-detect guard) rows were prepended, so these two session-166 rows fell outside the window.

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-23 | **s166 — PLAN-0091 SD-5 RATIFIED (a), Cray typed (#869): the AT-2 template is owned by `services/engine/scaffolder/` and NEVER enters the shared `REGISTRY`** — the classify path stays byte-unchanged and ADR-0024 D7's abstain routing stays literally true. All five SDs closed. Tripwire: the `set(REGISTRY) == set(AT1_FAMILY)` assertion must never need editing — if it does, STOP and re-open SD-5 | `097d180` (#869) / `docs/plans/done/0091-narrative-to-vertical-scaffolder-tool.md` §SD-5 + `tests/services/engine/procedures/test_archetype_templates.py` |
| 2026-07-23 | **s166 — dispatch-quality discipline shipped (#866, docs-only): the `code-operational-policy` skill gains the 3 dispatch blocks (Frontier/anti-anchoring · oracle-scoped accelerator · REJECT-if) + the M1–M4 follow-up vocabulary + the pre-close counterexample step.** Deliberately NOT built: any hook/detector for M3/M4 — adoption is Rule-of-Three on recorded catches | `b8566a6` (#866) / `docs/lessons/0032-ambition-scales-with-oracle-exploration-gated-not-planned.md` |
| 2026-07-23 | **s167 — the autonomy fork RESOLVED + SHIPPED in one session: option A′ (Cray, typed) DEMOTES the Stop-hook `dispatch` verdict from an ORDER to a SUGGESTION (#870 filed, #871 built).** Ledger: 14 misfires / 0 valid fires. No ADR amendment — the arm had zero ADR backing, so the PLAN **is** the governance record. **The argument is settled history in the archived PLAN — do not restate it** | `7c86752` (#871 merge, head_commit of record) / `822a7e8` (#870) / `docs/plans/done/0092-stop-hook-dispatch-arm-demotion-to-suggestion.md` |
| 2026-07-23 | **s168 — PLAN-0092 closed 6/6 + archived (#881); the `AT2_ONLY_KINDS` drift fixed with an anti-drift tripwire (#882); SD-D settled — the classifier prompt reworded to a ROUTING SUGGESTION, decision value + reply schema pinned UNCHANGED (#886)** | `c2b92c5` (#886) / `c47232f` (#882) / `b8f011d` (#881) / `docs/plans/done/0092-stop-hook-dispatch-arm-demotion-to-suggestion.md` (COMPLETE 6/6) |
| 2026-07-24 | **s169 — PLAN-0088 Steps 1–3 BUILT (#890/#891/#893): the cross-run read substrate (AC-1/2/3/11) + reader A2 (`GET /insights/impact`, AC-4/5) + reader A3 (`GET /insights/flow`, AC-6).** Seven read-only async primitives, a seeded 250-run corpus with a plain-Python oracle independent of the SQL under test, two AST guards. `ImpactReport` carries **no** cross-currency total and must never gain one (S7). Suite 3109 → **3150**. Detail: the s169 CF block above | `9e26195` (#893) / `8393af8` (#891) / `b1e12d1` (#890) / `services/db/run_analytics.py` |
| 2026-07-24 | **s169 — PLAN-0088's design layer ADJUDICATED: SD-1…SD-8 ratified in ONE typed pass (#889); SD-8 = (a) ELIMINATE struck `list_runs_page` + AC-12**, so the substrate ships aggregate-only, `GET /runs` is untouched, and listing pagination moves to the future monotonic-`sequence`-column PLAN. AC-12 kept as a tombstone so AC numbering stays stable (live count 13). Step 0 DISCHARGED → build-ready. Detail: the s169 CF block above | `dd16267` (#889) / `8d1be34` (#888) / `docs/plans/done/0088-cross-run-read-substrate-and-run-insight-readers.md` §Surfaced decisions |

---

## Rotated this reconcile (session-179, 2026-07-27 — PLAN-0094 Step 4 re-scoped on its own probe (#933) + the expired-test fix that unblocked main (#934))

The session-174 Current Focus block rotated out under the R2 four-session window, and two session-171/170 Recent Decisions rows fell outside the 10-row cap. **Archival note:** the s174 block's closing sentence — "**AC-1 (ii)** (`PostToolUseFailure` registration) at Step 4" — was **falsified in session 179**; AC-1(ii) is now WITHDRAWN because the event does not fire in this harness build. The block is preserved verbatim as the historical record; the correction lives in the s179 Current Focus block and the In-Flight PLAN-0094 bullet.

### Current Focus block — session 174

> **Session 174, 2026-07-25 (head_commit `6fb89b8` → `a3a9c66`) — the session
> MS-S1 stopped being an inference appliance and became an administrable host,
> and the constitution's gated surface was widened to match. Three PRs merged
> (#916, #917, #918), 0 open. The headline is not "three PRs landed" — it is that
> a second channel onto the LLM box changed what §8's host-state gate has to
> cover, and §8's one concrete illustration was pointing at a port.**
>
> **(#916 — the channel, and the §4 three-layer split.)** ADR-002 opened TCP
> 11434 and nothing else, so box-level state on MS-S1 was undiagnosable without
> walking to the machine. Cray opened a second **LAN-only** channel — OpenSSH on
> TCP 22, firewall scoped `Domain, Private`, the same scoping as the Ollama rule
> (it had been `Private`-only, so the box was never publicly exposed). Verified
> with `ssh -o BatchMode=yes` → `REMOTE_OK` / `CRAY-MS-S1-MAX`; **BatchMode
> forbids interactive fallback, so that proves publickey auth rather than a
> silent password prompt** — a distinction a plain `ssh` smoke cannot make. The
> knowledge then split three ways per the CLAUDE.md §4 placement rule, and **that
> split is the reusable part**: the **binding rule** stays in `CLAUDE.md` §8, the
> **setup + four traps + recovery** in `docs/runbooks/ms-s1-ssh-access.md`
> (Tier 2), and the **task-triggered operating procedure** in a new
> `.claude/skills/ms-s1-admin/` (Tier 2.6). Neither derived artifact carries the
> rule — the §4 bright line, since a skill that fails to trigger would silently
> drop it.
> **(the trap worth carrying.)** A `$` inside `wsl bash -lc "ssh ms-s1 '...'"`
> passes through **two** bash layers and is expanded away **with no error** —
> `Write-Output "got:[$PSVersionTable]"` returned `got:[]`, a silent empty rather
> than a failure. Escaping survives exactly one layer. The documented answer —
> write a `.ps1` and pipe it via `powershell -NoProfile -Command -` on stdin, so
> no shell ever parses the payload — was verified end-to-end. That same probe
> measured `Elevated=True`: an OpenSSH session for an administrator carries a
> **full, un-UAC-filtered admin token**. Also a drift fix: `ms-s1-ollama` pointed
> the binding rule at "the active PLAN / handoff (e.g. PLAN-0020)", which session
> 62 had already moved into `CLAUDE.md` §8 and which is now archived. Classified
> per §6 as **`superseded by new info`, not `was an error`**.
>
> **(#918 — §8 rescoped, net +1 line.)** The rule's **substance did not change**:
> "any change to global / host configuration outside the worktree" already gated
> SSH-borne changes. What failed was the **illustration** — MS-S1 was exemplified
> as `192.168.1.133:11434`, a *port*, which post-SSH reads as a scope boundary
> rather than an example, leaving the one concrete anchor a hurried reader takes
> away as the narrower half of the truth. Three drafting calls: (1) the literal
> address is **dropped entirely**, not merely the port — §5 Hardware already
> carries it, and a second copy is the ADR-0017 D6 drift class this edit exists to
> undo; (2) the verb is **"altering"**, not "any action over SSH" — gating
> *access* rather than *change* would over-gate read-only diagnostics, a
> substantive tightening outside the dispatch's remit; (3) an **elevation warning
> was considered and declined** — it changes no behaviour (§8 already forbids the
> action without a go, unconditionally) and §8 states no other rule's rationale;
> the hazard rides on the adjective **"administrative"**. **Honest caveat,
> ratified knowingly:** this is a hair wider than pure re-illustration — "host
> *configuration*" arguably did not cover writing an arbitrary file on MS-S1;
> "the gated surface is the whole host" does. Routing: **Cowork drafted the text**
> (ADR-009 D1 — Code may not author `CLAUDE.md`, and `plan-drafter` is
> hook-denied) and corrected Code's reasoning on the elevation fork; **Code R2'd,
> ruled on two returned flags (both rejected), surfaced the widening, applied and
> committed** (D2); Cray ratified the exact wording.
>
> **(#917 — PLAN-0094 Steps 1+2: the reset that was never wired.)** AC-1 + AC-2,
> plus AC-3 in part. The subagent-completion L1 reset shipped 2026-06-08 with a
> handler, green tests and **no event registration that could ever invoke it** —
> dead for seven weeks while three documents advertised it live; s172 followed
> that advice and lost most of a session. **Two independent defects, both fixed.**
> *Route:* a new `SubagentStop` entry, matcher `*`, invoking the observer;
> `main()` now branches on `hook_event_name` **before** `tool_name`; the dead
> `("Task","Agent")` branch deleted. *Scope:* the reset clears the completing
> agent's **own** recorded edits (new additive `subagent_touched:
> {agent_id: [targets]}` state), not `turn_touched` — restoring the documented
> turn-scoped form would have created a **self-unlock path**, letting the main
> agent launder its budget through any zero-edit spawn. Cray ratified that
> divergence from Lesson #0021 §3 **as a decision**. Class-killer: a new
> `tests/handoffs/test_settings_hook_wiring.py` parses `settings.json` **as data**
> and fails on a registration removal alone — it pins the defect class, not the
> instance.
> **(evidence.)** RED-first on every new assertion except one, which was **proved
> non-vacuous by mutation** (reverting to turn-scoped semantics reddens it plus
> three siblings; the file was restored from a `/tmp` copy, byte-identical, never
> `git checkout`). Suite **3244 → 3252 passed / 8 skipped** — the exact +8
> predicted before the run. `mypy` clean (110 files), `ruff` clean (501 files),
> both run in the **main tree**. Thresholds `6` / `15` **byte-unchanged**. Two ACs
> deliberately close later, Cray-approved: **AC-1 (ii)** (`PostToolUseFailure`
> registration) at Step 4, and **AC-3's third surface** (the deny-message anchor in
> `pretooluse_loop_detect.py`) at Step 3, per D2's do-not-edit-twice instruction.
> **Steps 3–6 remain unbuilt and are gated on Step 1 soaking on Cray's live loop.**

### Recent Decisions rows — rotated under the 10-row cap

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-24 | **s171 — PLAN-0088 Step 6 BUILT (#905): the four Group-B primitives + the AC-10 carrier proof, under SD-9 (a2)'s precedent so no new SD was needed.** Reopening the corpus found FOUR shapes it wrote that the engine never does (the AC-2 class), and B3's refusal kind was a BIJECTION of procedure — its oracle could not have failed. Mutation probe 4/4 as predicted. Suite 3178 -> **3189**. Plus **#904**, the STATUS rotate A+C: 61,748 -> 48,920 B, window untouched | `08304a0` (#905 merge, head_commit of record) / `023f24a` / `a3716db` / `d863078` + `96fbdcc` (#904) |
| 2026-07-24 | **s170 — PLAN-0088 Steps 4 / 4.5 / 5 BUILT (#895/#900/#902); SD-9 RULED (a2) by Cray (#898, surfaced #897).** Readers A4 (audit-readiness, AC-7) + A1 (NL query over runs, AC-8/AC-9), three new primitives; SD-9 settles that the substrate grows in `run_analytics.py` **only** and strikes `agent_id` + `trigger` from v1. Suite 3150 → **3178**. **AC-9b (live MS-S1) OPEN — host-state.** | `5d02538` (#902 merge, head_commit of record) / `46f0ba1` (#898) / `7150c07` (#895) / `docs/plans/done/0088-cross-run-read-substrate-and-run-insight-readers.md` §SD-9 |

## Rotated this reconcile (session-180, 2026-07-28 — PLAN-0094 Step 4 COMPLETE: the unit changed from touches to non-progress (#937), two measured PLAN corrections + OQ-4 opened (#938), AC-11's count line + mirror-invariance (#939))

### Current Focus block — session 175

> **Session 175, 2026-07-26 (head_commit `a3a9c66` → `04c94e4`) — the session
> the harness stopped letting a failed command look like a success. Four PRs
> merged (#920–#923), 0 open. Two of them are the same defect class at two
> layers: a guard that fires but says nothing legible (#920), and a shell that
> reports `0` for a command that failed (#923).**
>
> **(#923 — a masked command failure is now impossible to believe silently.)**
> Cray caught that a `| tail -6` hid a traceback, swallowed an exit code, and a
> FAILED script was reported successful. Probing found **three** hazards, and
> the reported one was the smallest. (1) A bare `$` inside `wsl bash -lc`
> expands **one shell layer early** — `$?` reads `0` for a failed command and
> `$(pwd)` resolves *before* a preceding `cd`; escaped `\$?` returns the true
> `1`, but only with a single-quoted outer arg. (2) Unmerged **stderr
> OVERWRITES stdout** byte-for-byte — one stderr line erased all 8 stdout
> lines, 3/3 runs — previously unrecorded anywhere in the repo. (3) A pipe into
> `head`/`tail` reports the **truncator's** status, and the inverse `| head`
> under `pipefail` yields 141 SIGPIPE. Three changes per the §4 routing rule:
> Lesson #0007's mechanism **CORRECTED and reclassified `was an error`** (the
> harness does not "fail to propagate exit codes"; a two-character escape
> recovers `$?`, and the over-generalization cost two months of stderr-parsing
> workarounds), a binding **CLAUDE.md §8** rule, and a `_shell_hygiene_warning`
> **PostToolUse advisory** — deliberately not a PreToolUse deny, because the
> harm is not running the command but *believing* its output, which is knowable
> only after it runs. It attaches to a hook already registered for Bash, so
> `.claude/settings.json` stays untouched. Hazard 2 is deliberately NOT
> enforced: whether a command emits stderr is not knowable from its text, so a
> check would either miss most cases or warn on every call. The advisory caught
> a real bug in the author's own command on its first live use.
>
> **(#922 — PLAN-0094 Step 3: L1 warns first, denies on the second trip.
> Closes AC-3 (final surface), AC-4, AC-5.)** L1's path-class threshold becomes
> the **WARN** bar (observer ping + agent-visible advisory, edit ALLOWED); the
> gate denies only at threshold + `L1_GRACE_BUDGET` (3, Cray-ratified OQ-1) =
> **9 code / 18 doc**. **L4 is untouched** at a flat 6. An additive
> `CounterEntry.warned_at` dedupes the warn. `.claude/settings.json` NOT
> touched. **One deliberate deviation from the Step 3 spec, pinned by a test:**
> the deny message does NOT name the P3 stop-ack, because P3 ships at Step 5
> and advertising an unbuilt exit would recreate the exact defect AC-3 closes.
> Non-vacuity by 3 mutations, each RED count predicted before the run and
> matched. The AC-3 grep oracle caught the author quoting the banned anchor
> phrase in a docstring; the warn then fired live on the author's own 6th edit
> mid-implementation.
>
> **(#920 — every vertical's ACTION client factory pinned offline.)**
> `ActionStepExecutor.client_factory` defaults to a **LIVE** `OllamaClient`
> against MS-S1, so dropping one kwarg from any vertical factory is a silent
> CLAUDE.md §8 host-state change. A parametrized guard now asserts at
> **REGISTRATION**, across all six procedure-shipping verticals, that the
> factory is not the live default and does not produce an `OllamaClient`.
> **The measurement corrected the draft's own premise:** it claimed five
> verticals were unguarded, but mutation-testing each showed the existing suite
> DOES catch it (aquaculture 3 / building_materials 1 / energy 2 /
> fleet_maintenance 6 / supply_chain 7 failures). The real defect is therefore
> not absence but **shape** — the signal is opaque (`BaseExceptionGroup:
> unhandled errors in a TaskGroup`), incidental (only where a vertical happens
> to own an e2e ACTION test), and pytest-only (the production registrations in
> `main.py` / `cli.py` run under neither). The assertion is "not the live
> default", never "is <a specific stub>": procurement injects its own
> same-named PO-shaped stub.
>
> **(#921 — four stale cross-references, found by a five-agent grounding
> sweep.)** Repo claims verified against code, not against each other.
> `query_step.py` still asserted the PLAN-0048 SD-3 "deprecate-in-place, never
> migrated" stance that **PLAN-0062 SD-C overturned**, leaving two engine
> docstrings in live contradiction; `supply_chain/procedures_factory.py` cited
> `hero_demo/run.py:278` (actual `:298`); PLAN-0076's Code-anchors block named
> four symbols PLAN-0078 PR-5 retired (now grep-clean); PLAN-0094 gained a
> line-citation drift table + AC state. All four classified **`superseded by
> new info`**, not `was an error`.
>
> **Governance, recorded so it does not read as precedent.** ADR-009 D1
> reserves `CLAUDE.md` authorship to Cowork; Cray granted Code a **one-off,
> explicitly scoped** exception for the #923 §8 edit — reason given: the
> problem is important, the context was already warm, and the evidence was in
> Code's hands. Cray ratified; it is recorded in the CLAUDE.md footer and the
> PR. **Normal routing is unchanged.** Separately, **Cray settled the
> demo-target fork: the LIVE-API shape ("แบบ B"), not static-only** — which was
> gating both Candidate C (the Docker image) and the future MS-S1 hosting ADR,
> and makes **Candidate C the long pole** rather than an optional alternative.
> And **PLAN-0094 Step 1's soak reported no anomalies** on Cray's live loop,
> which released Step 3.
>
> **Three deferred corrections applied to this file** (found by the #921 sweep,
> held back for this reconcile): the **Demo-card UX TODO is
> closed-with-residue** — the s74 trust shape ships on both the story and
> monitor surfaces with anti-regression comments citing the PLAN-0035 §SD-3
> amendment (`story.css`, `view-story.js`, `view-monitor.js`), residue at most
> one toggle on the monitor step card; **Rock-3 / O-2's wording is corrected**
> — the derived fields ALREADY migrated to declared `transform` ✔ (PLAN-0078
> PR-1 #762, AC-2 ticked), so the residue is ONLY the cardinality-changing
> `candidate_quotes` nest; and the **duplicated `git.md` extraction TODO** is
> de-duplicated to one row, noting its substance is effectively discharged by
> the `git-workflow` skill and that **`CLAUDE.md:176` holds a DEAD link** to a
> non-existent `docs/conventions/git.md` — a **Cowork** round-trip, since the
> #923 exception was scoped to §8 only.
>
> **State at close:** `main` `04c94e4`, suite **3296 passed / 8 skipped**,
> `mypy services/` clean (110 files), ruff + ruff-format clean (501 files) —
> all run in the main tree. 0 open PRs; tree clean but for the two standing
> KEEP untracked paths (`.claude/benchmark-results/`, `.claude/launch.json`).

> _Older content rotates out of this file per the **STATUS.md Rotation Policy (R1-R7)** in [`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md) (Lesson #23): Current Focus keeps the 4 newest sessions (<=8 blocks); Recent Decisions keeps the last 10 rows. Rotated blocks/rows live in [`docs/status-archive/`](status-archive/) and git history (Tier 3). Layout — **two separate chains, both with letters ascending with time and the base holding the recent window**: the rotation archive `2026-h1b` → `c` → `d` → `e` → `f` → `2026-h1-status.md`, and the Current-Focus-only `2026-h1b` → `c` → `2026-h1-current-focus.md`. Rotations append to the two bases. **Grep the directory, not a filename** — the chain is one corpus and which file holds a given block is an artifact of where the ~192 KB R4 bar happened to fall. _[Chain created 2026-07-17 (s144): the single `2026-h1-status.md` had reached 592,577 B, 2.3x R4's cap, and the new guard (#789) forced the split.]_

### Recent Decisions rows — rotated under the 10-row cap

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-25 | **s171 — PLAN-0088 COMPLETE, 13 live ACs, archived to `done/` (#908).** AC-9b BUILT + PASSED (#907): live translate/phrase stages wired (reusing `nl_query`); one MS-S1 `gpt-oss:20b` smoke → grounded count 120 = the seeded corpus. A test premised on an unwired seam RAN the model twice unasked → a socket-level `_no_outbound_network` guard now makes an off-box call impossible. Suite 3189 → **3203/8** | `ca39841` (#908 merge, head_commit) / `c21c0aa` + `e443696` (#907) / `docs/plans/done/0088-*.md` |

## Rotated this reconcile (session-181, 2026-07-28 — CLAUDE.md full slim landed (#941): footer changelog retired to git history, §6 compressed)

### Current Focus block — rotated under the R2 four-session window

> **Session 176, 2026-07-27 (head_commit `04c94e4` → `77fa734`) — the session
> that went looking for a routing answer and found the fact-pack was wrong.
> One PR merged (#925, docs-only), 0 open. PLAN-0095 lands as **Draft** — a
> plan to make the scaffold-era `Dockerfile` build and boot the synthetic OCT
> demo with **no database**. Nothing was built: no Dockerfile change, no test,
> no compose edit, Steps 1–5 unexecuted. The image does **not** boot today.**
>
> **(the grounding sweep is the durable half.)** The session opened as a
> routing question — which of 15 candidate work-items to dispatch. Four Explore
> agents verified all 15 against code and **five premises carried in from the
> s175 handoff were wrong**. The load-bearing one: the first-order Docker boot
> failure is a plain Python import — `importlib.import_module(_VERTICALS_PACKAGE)`
> at `services/engine/discovery.py:45`, uncaught as the **first line** of
> `lifespan()` (`services/api/main.py:166`) — **not** the CWD-relative
> `Path("verticals")` read at `ontology_meta.py:154`, which is real but
> second-order. Dispatching the drafter on the original fact-pack would have
> fixed the second-order problem and left the image still unbootable. Also
> corrected: "8 distinct defects" overstated independence (it is **two** broken
> `COPY` statements, each with two symptoms, plus hygiene gaps), and a **ninth**
> defect nobody had counted — `pyproject.toml:7` declares `readme = "README.md"`,
> never COPY'd, so `uv sync` fails a **second** time even after the
> package-tree fix.
>
> **(a stale gate-route claim in the constitution.)** `CLAUDE.md` §6 says a new
> PLAN/ADR is PreToolUse-gated for Code **and the in-harness `plan-drafter`**.
> Measured: `pretooluse_classifier_dispatch.py:301-311` **exempts the
> `plan-drafter` subagent from the G2 classifier gate by design** (PLAN-0034
> prong 2, SD-1(a)), short-circuiting *before* the classifier — so it does not
> depend on MS-S1 being warm. The main Code agent carries no `agent_id` and is
> still gated, so **G2 is preserved**; only the sentence is wrong. Recorded as a
> **finding needing a Cowork round-trip** (Code may not author `CLAUDE.md`),
> alongside the already-tracked `CLAUDE.md:176` dead-link TODO — **not fixed**.
>
> **(Cray's ruling reframed the PLAN, it did not just pick options.)** The frame
> Cray set: the artifact must be shaped so it grows into production **without a
> rewrite**, under two hosting models (the customer uses an instance we host; we
> stand up a server at the customer's site) — *"ready for development toward
> production," not "build production now."* **SD-1 = both** — the standalone
> image is the artifact, compose is a thin consumer proving it composes with a
> real Postgres (the "no current consumer" premise died under the production
> frame). **SD-2 = include `alembic/` + document** — the over-promise concern is
> answered by documentation, not omission; "one image, different commands"; a
> separate migration image is the *riskier* shape (version skew). **SD-3 = all
> four hygiene items IN.** SD-1 and SD-2 **overturned the drafter's own
> recommendations** and are recorded in-PLAN as **`superseded by new info`**,
> not `was an error`, with the original analysis preserved as the decision
> record.
>
> **(two R2 rounds — and the drafter caught an error in the reviewer's
> correction.)** R2 round 1 widened the oracle's AST scan to the verticals tree;
> the drafter showed a literal `verticals` glob would **break AC-3** — the
> anti-tautology invariant the same review insisted on (the oracle module must
> not contain the string at all) — so the correction could not be implemented
> naively, and it proposed a derived scan set instead. R2 round 2 corrected
> *that* rule: "top-level packages excluding the test tree" is **three**
> directories, not the two claimed — `benchmarks/`, `services/`, `tests/`,
> `verticals/` all carry `__init__.py` — so the behaviour-identity held **by
> luck, not by construction**, and `benchmarks/` is never COPY'd into the image,
> making it a latent **false-RED** surface. Replaced with a **transitive closure
> seeded from the app root**: code that never enters the image cannot fail
> inside it, so it must not constrain the image.
>
> **(the oracle design is the PLAN's real content.)** A test that hardcodes the
> expected COPY list re-encodes the Dockerfile and passes tautologically
> forever. Instead **O-1 derives** the required root set from an AST scan and
> asserts the Dockerfile covers it, with a greppable anti-tautology invariant
> (AC-3) and a mutation (M-C) that adds a runtime-resolved root with no
> Dockerfile edit and **must go RED**. O-4/O-5/O-6 carry **binding
> derivation-status labels** — a presence check presented as derived is an R2
> reject; `USER` is honestly labelled a presence check because no code source of
> truth exists. **AC-6 is invariant: no acceptance criterion needs a Docker
> daemon** (O-6 parses YAML with `ruamel.yaml`, verified a main dependency at
> `pyproject.toml:23`); every daemon action sits in the optional Cray-gated
> evidence step.
>
> **(the hosting question is surfaced, not drafted.)** *"Customer uses our
> server"* touches **ADR-002's LAN trust model** —
> `docs/adr/0002-network-topology.md:76` and `:86` — which defers its own
> successor **twice** as an unnumbered `ADR-NN`. PLAN-0095 states it can land
> with that open, because nothing in the image or the compose service selects
> *where* the image runs. This is now a **live candidate needing its own ADR**.
>
> **(one execution trap recorded for whoever builds this.)** The compose
> sketch's `vero:vero` in-network URL trips the `detect-secrets` pre-commit hook
> as Basic Auth Credentials and needs an inline `# pragma: allowlist secret` —
> in the **real `docker-compose.yml` at Step 3**, not only in the PLAN sketch.
> It is a pattern match, not a leak (`vero:vero` is the already-tracked dev
> placeholder at `docker-compose.yml:6-7` and `services/api/config.py:39`).
> Never `--no-verify` (CLAUDE.md §8).
>
> **State at close:** `main` `77fa734`, 0 open PRs; tree clean but for the two
> standing KEEP untracked paths (`.claude/benchmark-results/`,
> `.claude/launch.json`). CI `gate` PASSED on `2fb8709` in 3m38s and was
> **SHA-verified** against the PR head before merge. **No suite re-run was owed
> or performed** — the merge is docs-only (one file, 702 insertions, zero code).
> **MS-S1 was not contacted; no model warmed or run.** PLAN-0094 Steps 4–6 are
> untouched and still carry their prior blockers.

### Recent Decisions rows — rotated under the 10-row cap

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-25 | **s172 — PLAN-0093 COMPLETE 8/8, archived to `done/` (#913): the LLM-arm degrade disclosure, no silent arm swap.** Four steps — disclose which arm phrased an NL answer, make the rule fail-safe say it is a fail-safe, project the authoring arm over HTTP (incl. the insights run-corpus path), and fix `LLM_RETRY_BUDGET` being **inert on the governed path**. Its L1 deadlock on `services/engine/nl_query.py` — where the documented subagent-reset escape was run verbatim and did **not** clear the counter — became the s173 brief and the empirical half of that finding | `9786c63` (#913 merge) / `55d2007` (#911) / `30285bc` (#910) / `docs/plans/done/0093-llm-arm-degrade-disclosure.md` |


---

_Rotated out of `docs/STATUS.md` on 2026-07-28 (session 182), per the R1–R7 rotation policy._

| 2026-07-25 | **s173 — the L1 loop-detect guard: its unit of measurement was wrong and one documented escape was never wired.** #912 bounds the loop-counter state lifetime (age-out 6 h + a session boundary read from the hook payload, which `resolve_session_id` never consulted). #914 lands **PLAN-0094** (Draft) + **Lesson #0033**. Probed live: `PostToolUse` fires only on success, so L1 could not see a failed edit at all — 6 good edits score 6, 6 retries of one broken anchor score 0, so **no threshold separates them** and PLAN-0094 changes none. `_handle_agent_completion` is **dead code** (no `PostToolUse` Task/Agent matcher); the registry row L1, Lesson #0021 §3 and the deny message all still call it live. Cray ratified **OQ-1 `G=3`, OQ-2 full fresh budget, SD-2 subagent-scoped reset** (a decision, not a diff approval — it changes a recorded lesson) | `6fb89b8` (#914 merge, head_commit) / `3383697` + `2d09002` (#912) / `docs/plans/0094-loop-detect-non-progress-and-reset-paths.md` + `docs/lessons/0033-raising-the-threshold-is-not-fixing-the-unit.md` |

<!-- Recent-Decisions row rotated out of docs/STATUS.md by the s183 reconcile (R2) -->
| 2026-07-25 | **s174 — MS-S1 stopped being an inference appliance, and CLAUDE.md §8's gated surface was widened to match.** #916 opens OpenSSH on TCP 22, LAN-only (`Domain, Private`), verified with `BatchMode=yes` — which proves publickey auth, not a silent password prompt; the knowledge splits per §4 — rule in §8, how-to in the runbook, procedure in a new `ms-s1-admin` skill. #918 rescopes §8, net +1 line: substance unchanged, its `…:11434` *illustration* was reading as a scope boundary (Cowork drafted → Code R2'd + committed → Cray ratified). #917 lands PLAN-0094 Steps 1+2 — the `SubagentStop` L1 reset, scoped to the completing agent's OWN edits (turn-scoped would be a self-unlock path; Cray ratified the divergence from Lesson #0021 §3); suite 3244 → **3252** | `a3a9c66` (#918 merge, head_commit) / `2cda070` (#917) / `c9050b9` (#916) / `docs/runbooks/ms-s1-ssh-access.md` + `docs/plans/0094-loop-detect-non-progress-and-reset-paths.md` |

<!-- Current Focus blocks rotated out of docs/STATUS.md by the s185 reconcile (R2) -->
> **Session 181, 2026-07-28 (head_commit `767d520` → `85efe52`) — the session
> the constitution got a third lighter and no rule changed. One PR merged
> (#941), 0 open. CLAUDE.md full slim: the **11.1 KB footer changelog — ONE
> physical line, 33.6% of the file — retired to git history** under a NEW
> convention; §6 compressed; **277 → 261 lines / 33,014 → 21,524 B
> (−35.2%)** — ~2.8k tokens returned to every session.**
>
> **(the trigger was behavioral; the diagnosis was measured.)** Cray observed
> inconsistent instruction-following. A 2026-07-28 research pass against the
> official guidance (target < 200 lines; "bloated CLAUDE.md files cause
> Claude to ignore your actual instructions"; ❌-exclude "information that
> changes frequently") identified the footer as the anomaly — one physical
> line of 11,104 B, exactly the frequently-changing class the guidance
> excludes.
>
> **(the safety condition ran BEFORE the cut.)** Cray attached a coverage
> verification as a precondition: every footer entry diffed against its
> edit's full commit message (20 commits to scaffold) — every commit body ≥
> the footer entry, and every companion artifact (Lessons
> #0007/#0010/#0011/#0026/#0027, ADR-009/012/013/0017/0018/0032, the ms-s1
> runbook + skills) exists on disk. The footer was a strict summary layer
> over git history; retiring it loses nothing. The NEW convention: a
> constitutional edit bumps the footer date ONLY — the edit's commit message
> is the full record, and `git log --follow -- CLAUDE.md` is the amendment
> history.
>
> **(routing + R2 — five flags, five rulings.)** Cowork drafted (ADR-009 D1,
> cloud session, K-2 delivery); Code R2'd with a one-for-one E2
> six-commitment checklist, a binding-rule substance diff, and arithmetic
> verification, then ruled the returned flags: **α ACCEPT** (Decision + Plan
> Flows merged into one "Governance Artifact Flow"; 8/8 facts verified),
> **β ACCEPT** (the ADR-013 T4 sentence dropped — canonical in ADR-013),
> **γ ACCEPT** (the D2 hook-fact stated once), **δ APPLIED** (Lesson #0027
> linkified), **ε KEEP** (the tier table is the single in-file ADR-009 D1/D2
> statement). Cray ratified the wording + the rulings via AskUserQuestion.
> **No binding rule's substance changed** — verified hunk-by-hunk: 9 hunks,
> all inside the §6 span + the footer.
>
> **(the LOCKED target was unreachable — and the drafter said so.)** Cowork
> flagged per stop-and-flag, and Code verified the arithmetic: the
> < 200-line LOCKED target cannot be met in LOCKED scope — outside-§6 alone
> is 194 lines. Cray ruled option **(b)**: the target restates as **< 20 KB**
> (now 21.5 KB) and a follow-up extraction pass is queued (new Active TODO).
>
> **State at close:** `main` `85efe52`, 0 open PRs. Gate: pytest **3327
> passed / 8 skipped**, mypy clean (110 files), ruff clean on the tracked
> tree, CI `gate` PASS. Restart-bridge filed:
> `.claude/handoffs/session-181/2026-07-28-1027-code-session181-restart-bridge.md`
> — running sessions hold the pre-edit CLAUDE.md until Claude Desktop
> restarts. The two standing CLAUDE.md defect TODOs both SURVIVED the slim
> (re-verified on disk this reconcile): the dead `docs/conventions/git.md`
> link shifted `:176` → `:160`, the stale plan-drafter gate claim now sits
> at `CLAUDE.md:112` — line refs updated in their Active TODO rows.

> **Session 180, 2026-07-28 (head_commit `bc7be51` → `767d520`) — the session
> L1 stopped counting touches and started counting non-progress, and the
> question of whether L1 should exist at all got a measured baseline. Three PRs
> merged (#937, #938, #939), **0 open**. **PLAN-0094 Step 4 COMPLETE** (AC-7,
> AC-8(i)/(iii), AC-11); **OQ-4 opened** with a pre-committed retirement
> criterion; suite 3318 → **3327**. Only Step 6 (closeout, AC-10) remains.**
>
> **(#937 — the unit changed.)** `_handle_write_or_edit` used to increment on
> every Write/Edit, so six distinct forward edits of one file were
> indistinguishable from six retries of one broken change. It now increments
> only on **(b)** a re-applied `old_string` (`repeat xN`) or **(c)** the file
> returning to content it already held this turn (`osc xN`); a distinct forward
> edit is recorded via `observe()` with `result == ""`. `clear_turn_scoped()` is
> wired into the turn boundary. The measurement that makes this real: **all
> three L1 warns ever recorded would not fire under the new unit.**
>
> **(The s179 BLOCKING item was settled WITHOUT the probe it had staged.)**
> s179 closed planning to register a payload-dump hook and **restart the
> session** to learn whether `Edit`'s `tool_response` could supply a hermetic
> digest for (c). Answered instead from **84 recorded `Edit` results** in
> existing transcripts: an `Edit` result carries **no `content` key at all**,
> `originalFile` was null in **78 of 84**, and `structuredPatch` holds 1–2
> hunks — a diff, not a state. Nothing reconstructs the post-edit file, so the
> PLAN's on-disk hash stood unchanged. **The probe was never run; no restart was
> spent.** Corroboration for reading transcripts as a proxy for live payloads:
> the `Write` keyset measured this way matches the `Write` hook payload measured
> live in s179, key for key.
>
> **(#938 — two PLAN corrections, both measured, not inferred.)** The recorded
> result is ASCII `repeat xN`, not `repeat×N` — **seven sites** carried the
> multiplication sign **including AC-8's assertion text**, which is a
> pre-committed pass/fail read, so a test written to the PLAN as it stood could
> not have linted clean (ruff `RUF001`, measured directly). And (c)'s on-disk
> digest is now **grounded rather than defaulted**.
>
> **(OQ-4 — Cray asked whether L1 should exist at all.)** Baseline measured
> across **all 113 session transcripts, 2026-06-27 → 2026-07-27: 0 denies, 3
> warns, 0 true positives.** Two readings recorded: all three warns landed on
> exactly the *old* deny bar, so without P2's grace budget they would have been
> three hard walls during the month's most concentrated build work — the
> false-positive rate is **not flat, it climbs with how much work concentrates
> on single files**; and the guard **cannot catch the s169 incident that
> motivated it**. Not retired on the spot because the *marginal* cost of
> finishing was below the cost of retiring (an ADR-013 amendment plus deleting
> the test surface, against AC-7 on top of a state layer already merged), and a
> deleted detector cannot be measured. **Pre-committed criterion: re-measure
> after ~20 sessions; if true positives are still 0 and there is ≥1 false
> positive, dispatch Cowork to draft the ADR-013 amendment retiring L1** —
> L2/L3/L4 already carry E.4 more faithfully, since E.4 says "the same
> *problem*" while L1 keys only on "the same *file*".
>
> **(#939 — AC-11, and a spec that contradicted itself.)** (i) asked the deny
> body for "the threshold actually applied" (T+G) while (ii) asked the warn body
> for "the same line" (fires at T). **Cray ruled for the deny bar in both**: the
> warn body reads `count: 6/9`, "six of the nine that wall". The observer reads
> its denominator through `l1_deny_threshold_for` — the same function the gate
> applies — which exists precisely so the two bars cannot drift across two hook
> processes.
>
> **Non-vacuity swept twice, 9 named mutations**, each restored from a `/tmp`
> copy, never `git checkout`. The two carrying the most weight: **M-A**
> (whole-feature revert) reddens all three Step-4 rows while **L2 and L4 stay
> green**, proving the blast radius is L1; and **N-D** rewords a shared line
> *unrelated to the count* and reddens **only** the mirror row, proving the
> mirror-invariance assertion stands on its own rather than re-testing the count
> line from a third angle. **Every merge commit was checked, not assumed** —
> `git diff <CI-verified-head> HEAD` was **0 bytes** all three times, closing the
> PR-only-CI hazard by evidence.
>
> **State at close:** `main` `767d520`, suite **3327 passed / 8 skipped** (+9),
> `tests/handoffs/` **710 passed** re-run on the merge commit. 0 open PRs.
> `.claude/state/goal.json` **CLEARED this session** — it had been armed with
> the COMPLETED PLAN-0095 goal since s177, five sessions, and was carried
> unactioned in three prior blocks. Owed and unrun: the PLAN §Verification
> live-check (ii) — one deliberate warn-crossing on a scratch file, to confirm
> the advisory reaches the agent's context — and a Cray-confirmed live-loop
> soak, both gating Step 6.

<!-- Recent-Decisions row rotated out of docs/STATUS.md by the s185 reconcile (R2) -->
| 2026-07-26 | **s175 — the harness stopped letting a failed command look like a success.** #923: Lesson #0007's mechanism CORRECTED and reclassified `was an error` (a bare `$` expands one shell layer early; `$?` is not unreadable) + a binding CLAUDE.md §8 rule + a `_shell_hygiene_warning` PostToolUse advisory. #922: PLAN-0094 **Step 3** — warn at T, deny at T+G (9 code / 18 doc), L4 flat 6; AC-3/4/5 closed. #920 pins all six verticals' ACTION factory offline at REGISTRATION; #921 fixes four stale cross-refs. **Cray: demo target = the LIVE-API shape** → Candidate C is the long pole. ADR-009 D1 one-off Code-authors-§8 exception — **not precedent**. Suite 3252 → **3296** | `04c94e4` (#923 merge, head_commit) / `3b3b666` (#922) / `59c81a6` (#921) / `65c6953` (#920) / `docs/lessons/0007-harness-exit-code-artifact.md` |
