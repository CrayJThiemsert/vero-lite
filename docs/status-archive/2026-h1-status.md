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
