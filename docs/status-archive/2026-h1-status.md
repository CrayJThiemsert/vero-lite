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
