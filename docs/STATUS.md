---
last_updated: 2026-07-13T18:40:46+07:00
session: 125
current_batch: "s125: asset-event trigger proved LIVE full-loop (#724, EVIDENCE) + energy = 4th OCT vertical on the per-entity FK-parent band substrate (over-CURRENT, PLAN-0070 #726 feat + closed→done/); 2572/7."
current_actor: code
blocked_on: "Nothing blocking. main=b19dce4; PLAN-0070 (energy over-current) shipped + closed → done/; 0 open PRs; tree clean; MS-S1 idle."
next_action: "Backlog only (each its own future ADR/PLAN): monotonic step_results sequence column (needs migration); procurement ontology↔CSV drift (cosmetic). [energy rated_current_a — DONE via PLAN-0070 s125.]"
head_commit: b19dce4
recent_commits: [b19dce4, 9571abb, 22365f2, 36cb2f9, 960e988, 17ca489, 0d1077d, 65ff5c3, 4a4c444, c5651f6]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 125, 2026-07-13 (head_commit `960e988` → `b19dce4`) — (1) the
> moat's asset-event trigger PROVED LIVE end-to-end, then (2) energy shipped as
> the 4th OCT vertical on the per-entity FK-parent band substrate.** Three PRs.
> **#724 (`22365f2`, `docs(logs)`) — event-bridge FULL-LOOP live smoke: PASS
> (EVIDENCE, not a gate — CLAUDE.md §8).** The deferred host-state smoke from
> PLAN-0056 AC-12 / PLAN-0057: on real MS-S1 (`gpt-oss:20b`) the reactive
> recommender picked `suggested_handler == emergency_source` for the procurement
> CNC line-down event AND that pick propagated through the production fire path
> (`recommend` → `build_event_resolver` → `fire_event`) into a PERSISTED
> `event_emergency_sourcing_round` run parked at the DOA `approve` gate (฿288k →
> `appr-pm`, service actor `svc-buyer` on-behalf `req-planner`). Sessions
> 114/115 proved the recommender-level pick; this closes the one remaining live
> seam (propagation + persistence). Ran against a disposable test DB (never the
> demo DB); `event_bridge_enabled` stays default False (ship-dark) — no
> production code changed. Log:
> `docs/logs/2026-07-13-event-bridge-full-loop-live-smoke.md`. **#725
> (`9571abb`, `docs(plans)`) — PLAN-0070 Ready** (`plan-drafter`-authored, Code
> R2 PASS on all 7 load-bearing citations, Cray-ratified SD-1..SD-6 via
> AskUserQuestion). **#726 (`b19dce4`, `feat`) — PLAN-0070 BUILT + CLOSED →
> `done/` in one PR (SD-1):** re-themes energy's single procedure
> `substation_health_sweep` from over-TEMPERATURE to over-CURRENT (feeder
> overload) — `read_readings` gains the FK-parent `join:` via
> `event_emitted_by_asset` + a narrowing `where {measured_kind: current}` + the
> declared `site_id → asset_site_id` collision rename; the `judge` migrates
> `env_band` (blanket OCT_RECOMMEND_THRESHOLD) → `threshold_field:
> rated_current_a` + `direction: above`, so each feeder's latest ampere reading
> bands against its OWN `Asset.rated_current_a`. **Energy = the 4th OCT vertical
> on the per-entity FK-parent band substrate** (procurement s120 / supply_chain
> s121 / aquaculture s123 / energy s125). Rides the Accepted ADR-016 FKP
> amendment (its pre-recorded energy follow-on) — NO new ADR, NO ontology edit,
> NO regen, NO Alembic migration; the whole change is `synthetic.py` seeds +
> `procedures.yaml` + tests. **Demo-visible flip (RED→GREEN vs the unedited YAML
> first):** Feeder Meter A at 84 A is `ok` under the blanket env 90 band but
> `breach` at 105% of its OWN 80 A rating → parks `waiting_human` at the gated
> restart; the inverter (61 A) stays under its 722 A rating. **Energy's judge
> was the LAST shipped `env_band` consumer — it retires here** (no shipped YAML
> authors `env_band`; the `EnvBandEvaluateExecutor` engine path stays
> test-covered). **Zero functional `services/` change** (AC-8 — the only
> `services/` diff is an SD-5 docstring hunk). **Build-discovered coupling
> (disclosed correction to AC-8):** the 2 new current readings grew energy
> synthetic events 11→13 (one new warn), rippling into the NL-query feasibility
> benchmark gold set — `gold.yaml` nl-02 (total 11→13), nl-03
> (`measured_value>80` is unit-agnostic → the 84 A reading joins, 2→3), nl-05
> (warn 1→2) updated to match the data; no production code touched.
> **draft≠review≠verify:** `plan-drafter` PLAN → Code R2 (grounded citations) →
> Cray SD-1..SD-6 → Code build. All 9 ACs met; full suite **2572 passed / 7
> skipped** WITH Postgres (verified on merge commit `b19dce4`, CI PR-only); ruff
> + `ruff format` + `mypy --strict` clean; the BUILD is deterministic-offline
> (no MS-S1 / host-state — the live smoke is #724). Honesty framing:
> demo-breadth (the Rule-of-Three for the band shape was already MET at N=3 by
> PLAN-0068), not moat-critical. Commits: `22365f2` (#724 live-smoke log) →
> `9571abb` (#725 PLAN-0070 Ready) → `b19dce4` (#726 feat build + close).
> PLAN-0070 `git mv`→`done/` this batch; `docs/plans/` empty again.

> **Session 124, 2026-07-13 (head_commit `b55ff43` → `960e988`) — the Axis-B
> verify-loop goal gate GRADUATED from warn-only v1 to per-goal opt-in
> ENFORCEMENT: PLAN-0069 shipped END-TO-END (two PRs) + CLOSED → `done/` in one
> session-124 day (ADR-0018 V2 Accepted #713; #721/#722, `feat`).** Session
> opener (folded in, #718 `fix`): surfaced `threshold_field` in the read-only
> Procedures viewer (View F) decision facet — display-only, ZERO engine change
> — correcting a s123 `was an error` (the `/procedures` payload always carried
> it; the gap was FRONTEND-only in `view-procedures.js`), so the `/procedures`
> threshold_field display gap is now **RESOLVED**. **The major deliverable —
> Axis-B v2:** the Stop-hook goal gate now enforces per-goal opt-in, with every
> v2 consequence gated behind `if goal.enforce`, so `enforce:false` is
> byte-for-byte warn-only v1 (AC-3 — every pre-existing goal test passed
> UNMODIFIED); all 10 ACs met. Two PRs per SD-A: **#721 PR1 (v2 schema,
> `.claude/hooks/_goal_state.py`):** `schema_version`→2, a new
> `blocked-pending-human` status, a first-class `enforce` bool + `amendments[]`
> on the Goal dataclass (closing both build hazards — unknown-field-drop +
> VALID_STATUSES rejection), a new Amendment dataclass, and SD-D
> `amendments_seen` on Evaluation. **#722 PR2 (enforce ladder,
> `.claude/hooks/_goal_gate.py` + `/goal` + goal-evaluator):** the warn→enforce
> ladder at the three v1 return-None sites (one bounded block → park at
> `blocked-pending-human`, never twice for the same state), the V2-D4
> unanswered-dispatch park (never released / silent-pass), the SD-D
> drift/redirect pure function (positional `amendments_seen`, clock-free — the
> WSL wall clock is non-monotonic), `goal.md` documenting the enforce flag +
> amend-ratification + blocked-pending-human handling, and the goal-evaluator's
> V2-D2 anchor-divergence assessment (refute-not-bless posture UNCHANGED).
> **Cray ratified SD-A..SD-D via AskUserQuestion, all four as-recommended**
> (SD-A = 2 PRs / SD-B = same-PR/PR2 / SD-C = no migration / SD-D = positional
> `amendments_seen`). **draft≠review≠verify:** `plan-drafter` PLAN → Code R2
> (grounded citations verified) → Cray-ratified SDs → Code build. **Evidence
> bar:** full suite **2570 passed / 7 skipped** WITH Postgres (verified on the
> PR2 merge commit `960e988`, CI PR-only); `ruff` + `ruff format` + `mypy
> --strict` clean; CI `gate` green on #721 (2m37s) + #722 (2m46s);
> deterministic-offline — no MS-S1 / host-state. PLAN-0069 `git mv`→`done/`
> this batch. Commit: `960e988` (#722 PR2; the PLAN-0069 close rides the same
> closeout PR as housekeeping — head_commit stays the feat merge per Q4).

> **Session 123, 2026-07-13 (head_commit `2e2007c` → `b55ff43`) — PLAN-0068
> (aquaculture per-species DO floors) shipped END-TO-END and CLOSED → `done/`
> in ONE session-123 day; aquaculture's `morning_pond_health_round` judge now
> bands each pond's latest reading vs its OWN per-species `do_floor` (joined
> onto the reading by the migrated `read_do` FK-parent join) instead of one
> blanket 4.0 mg/L floor — the 3rd OCT vertical on the per-entity FK-parent
> band substrate (procurement same-row s120, supply_chain FK-parent s121), so
> Rule-of-Three MET for the FK-parent shape (ADR-006).** Two PRs (SD-4 = (b),
> a Cray divergence isolating the DB-migration / first-join-consumer rollback).
> **#715 PR1 (substrate + RED):** `Pond.do_floor` + per-species seeds (whiteleg
> 4.0/4.0, tiger_prawn 4.5, tilapia 3.0) + the SD-3 flip seed (event-reading-12,
> pond-11 @ 4.2 mg/L, 01:55) + a RED-verify against the unedited YAML.
> **#716 PR2 (migration + tests):** the `read_do` FK-parent join
> (`reads:[OperationalEvent, Pond]` + `join:{with:Pond,
> link:event_emitted_by_pond}`) + the `site_id`→`pond_site_id` declared-collision
> rename + the `judge` `threshold:4.0` → `threshold_field:do_floor` migration
> (keeping the authored `direction:below` + `watch_margin:1.0` — the FIRST
> shipped `threshold_field` + `watch_margin` 3-band consumer) + a Step-5
> coupled-test audit across 8 test files. **Zero engine change** — rides the
> Accepted ADR-016 FK-parent `threshold_field` amendment (FKP-1); `git diff main
> -- services/` is empty. **The demo-visible flip (SD-3 / AC-7):** pond-11
> (tiger_prawn) warms to 4.2 mg/L — a `watch` under a blanket 4.0 floor but a
> `breach` under its own 4.5 floor; the aerate breach set grows {pond-07} →
> {pond-07, pond-11}. AC-7 / SD-5 also pins that the SAME 3.4 mg/L reading is a
> breach in a whiteleg pond (floor 4.0) but only a watch in a tilapia pond
> (floor 3.0). **draft≠review≠verify:** the PR2 build RESUMED an interrupted
> prior-session WIP (`acfcd57`, "migration done, 7 coupled tests pending"); the
> `next-work-analyst` this session CAUGHT that STATUS said "BUILD NOT started"
> while the code showed PR1 merged + PR2 WIP — a `superseded by new info`
> staleness (the build landed after the s122 reconcile). The 7 pending
> coupled-test breaks were ALL the ones PLAN-0068 Step 5 pre-disclosed (fixture
> adapters not serving Pond → the migrated inner join empties; fake `read_do`
> rows lacking `do_floor` → the per-entity judge fails closed FKP-3;
> `threshold==4.0` assertions → `None` + `threshold_field`) — no engine bug.
> **Evidence bar:** full suite **2549 passed / 7 skipped** WITH Postgres
> (verified on the merge commit `b55ff43`, since CI is PR-only) + CI `gate`
> green on both PRs; ruff + `ruff format --check` + `mypy --strict services/`
> clean; no MS-S1 / host-state — pure offline. **Disclosed [corrected s124 —
> `was an error`]:** the read-only Procedures **viewer** (View F,
> `view-procedures.js`) — NOT the payload — does not surface `threshold_field`
> (a pre-existing FRONTEND display gap from s121's supply_chain migration; the
> `/procedures` payload always carried it, the Step model serializes it) — out
> of PLAN-0068's zero-engine scope; **RESOLVED s124 (#718).** Commits: `acfcd57` (PR2 WIP
> migration) → `befec8e` (PR2 coupled-test fixes) → merge `b55ff43` (#716 PR2);
> `ec4fe6f` (#715 PR1 substrate) → merge `d4cb9b3`. PLAN-0068 `git mv`'d to
> `done/` this same batch; `docs/plans/` is empty again.

> **Session 122, 2026-07-13 (head_commit `670117c` → `2e2007c`) — TWO
> governance-track PRs landed: the Axis-B verify loop GRADUATED to ENFORCING
> (ADR-0018 V2, #713) + the next build queued (PLAN-0068 Ready — aquaculture
> per-species DO floors, #712). NO engine/vertical code shipped this batch —
> both are governance text; the BUILDs are follow-on.** **#713 — ADR-0018 V2
> Amendment (Accepted 2026-07-13):** graduates the Axis-B verification loop
> from v1 (warn-only, D5) to **v2 (enforcing)**, discharging the D5 warn-only
> deferral + OQ-8 "Blocking-mode promotion", and formalizes **unintentional
> drift vs deliberate redirect** — a divergence WITH a typed Cray sign-off =
> redirect (passes), WITHOUT = drift (flagged/blocked). SD-0..SD-4 ratified
> as-recommended: SD-0 in-place amendment to ADR-0018 (extends, does NOT
> reverse — ADR-0016 discipline; D1-D7 unchanged); SD-1 per-goal `enforce`
> flag (default warn); SD-2 ratification = typed sign-off in an append-only
> `amendments[]` log, divergence evaluator-detected +
> deterministically-consequenced; SD-3 goal-gate graduation ONLY (sibling
> hooks out-of-scope); SD-4 missing-evidence-under-enforce = pause
> `blocked-pending-human`, never a silent pass. **draft≠review≠verify:**
> `plan-drafter` authored → Code R2 (re-verified the D5/OQ-8 text +
> `work_fingerprint()` at `_goal_gate.py:152`; confirmed 2 build hazards —
> `_goal_state.py` DROPS unknown fields on rewrite so the v2 fields must be
> dataclass fields, and `VALID_STATUSES` lacks `blocked-pending-human`) → Cray
> ratified. Grounded by a 2026-07-13 design brief (research through 13 Jul +
> repo inventory, published as a private Artifact, NOT a repo file). **The v2
> gate/schema BUILD is a follow-on PLAN** (ADR-013 D1). **#712 — PLAN-0068
> Ready (aquaculture per-species DO floors):** the `next-work-analyst`-ranked
> #1 pick, `plan-drafter`-authored + Code-R2'd + Cray-ratified (SD-0..SD-5;
> **SD-4 = (b) TWO PRs, a Cray divergence** from the drafter's 1-PR rec).
> Migrates aquaculture's `morning_pond_health_round` judge from a blanket
> 4.0 mg/L DO floor to per-species floors via `Pond.do_floor` + a `read_do`
> FK-parent join — the 3rd OCT vertical on the per-entity band substrate
> (**Rule-of-Three MET**), zero engine change (rides ADR-016 FKP-1). **Status
> = Ready; the BUILD (PR1 substrate + RED / PR2 migration + tests) is NOT
> started.** Commits: `d40d2f6` (#713 ADR-0018 V2 amendment) → merge `2e2007c`;
> `c443bfd` (#712 PLAN-0068 Ready) → merge `2c3a05d`. No MS-S1 / host-state —
> pure governance-doc batch; test suite unchanged (no code shipped).

> _Rotation note (session-125 reconcile, 2026-07-13, `docs(status):`):
> frontmatter bumped to `head_commit b19dce4` (session 125); a new s125
> Current-Focus block was PREPENDED. **NORMAL reconcile** (no size pressure —
> comfortably under the R1 ceiling): with s125 prepended, Current Focus held 5
> sessions (s125 + s124 + s123 + s122 + s121), so the OLDEST — the whole
> **session-121** block (per-entity FK-parent `threshold_field` / ADR-016
> "per-entity bands v2" shipped, supply_chain cold-chain `temp_ceiling`,
> #707/#708/#709/#710) — was rotated OUT to keep the 4-session window (now s125
> + s124 + s123 + s122). Recent Decisions rotated its OLDEST row (2026-07-10
> residual flaky-suite / TESTS-half wall-clock fix, #684) to keep the 10-row
> window. Both were emitted verbatim in the reconcile reply for the caller to
> append to `docs/status-archive/2026-h1-status.md` (Bash-side). **Backlog
> discharge:** the long-standing "energy `rated_current_a` FK-parent adoption"
> item is now DONE via PLAN-0070 (#726) — energy joins as the 4th OCT vertical
> on the per-entity FK-parent band substrate. Prior rotation notes (through the
> session-124 reconcile) are consolidated into this one (R4). Per the STATUS.md
> Rotation Policy (R1/R2/R4)._

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
| 2026-07-13 | **s125 — (1) event-bridge FULL-LOOP live smoke PASS (#724, EVIDENCE per §8) + (2) energy shipped as the 4th OCT vertical on the per-entity FK-parent band substrate (over-CURRENT, PLAN-0070 #725 Ready + #726 feat BUILT + CLOSED→`done/`)** — **#724 (`22365f2`, `docs(logs)`):** the deferred PLAN-0056 AC-12 / PLAN-0057 host-state smoke — on real MS-S1 (`gpt-oss:20b`) the reactive recommender picked `emergency_source` for the procurement CNC line-down event AND propagated through the production fire path (`recommend`→`build_event_resolver`→`fire_event`) into a PERSISTED `event_emergency_sourcing_round` run parked at the DOA `approve` gate (฿288k → `appr-pm`, `svc-buyer` on-behalf `req-planner`); closes the one remaining live seam (s114/115 proved the recommender-level pick). Disposable test DB; `event_bridge_enabled` default False (ship-dark), no prod code changed. **#725 (`9571abb`, `docs(plans)`) PLAN-0070 Ready** (`plan-drafter`-authored, Code R2 PASS all 7 citations, Cray SD-1..SD-6 via AskUserQuestion). **#726 (`b19dce4`, `feat`) BUILT+CLOSED one PR (SD-1):** re-themes energy's `substation_health_sweep` from over-TEMPERATURE → over-CURRENT — `read_readings` gains the FK-parent `join:` (`event_emitted_by_asset`) + `where {measured_kind: current}` + `site_id→asset_site_id` rename; the `judge` migrates `env_band` → `threshold_field: rated_current_a` + `direction: above` (each feeder banded vs its OWN `Asset.rated_current_a`). Demo flip: Feeder Meter A @ 84 A = `ok` under blanket env 90 but `breach` at 105% of its OWN 80 A rating → parks `waiting_human`; inverter (61 A) stays under its 722 A rating. **Energy's judge was the LAST shipped `env_band` consumer — retires here** (the `EnvBandEvaluateExecutor` engine path stays test-covered). NO new ADR / ontology / regen / Alembic (rides Accepted ADR-016 FKP amendment, its pre-recorded energy follow-on); whole change = `synthetic.py` + `procedures.yaml` + tests. Zero functional `services/` change (AC-8; only an SD-5 docstring hunk). Build-discovered coupling (disclosed correction to AC-8): 2 new current readings grew energy events 11→13 → NL-query `gold.yaml` nl-02/03/05 updated to match the data; no prod code. draft≠review≠verify: `plan-drafter` PLAN → Code R2 → Cray SD-1..SD-6 → build. All 9 ACs; suite **2572/7** WITH Postgres (on merge commit `b19dce4`, CI PR-only); ruff + `ruff format` + `mypy --strict` clean; BUILD deterministic-offline (live smoke = #724). Honesty: demo-breadth (Rule-of-Three MET at N=3 by PLAN-0068), not moat-critical. PLAN-0070 `git mv`→`done/`. Full narrative: the Session-125 CF block above | `b19dce4` (HEAD, #726 feat merge) / `9571abb` (#725 PLAN-0070 Ready) / `22365f2` (#724 live-smoke log) / `verticals/energy/{data_adapter/synthetic.py (over-current seeds + FK-parent event), procedures.yaml (`read_readings` `join:`/`where`/`project` + `judge` `threshold_field: rated_current_a`)}` + `tests/**` (energy over-current + `gold.yaml` nl-02/03/05) + `docs/logs/2026-07-13-event-bridge-full-loop-live-smoke.md` + `docs/plans/done/0070-*.md` |
| 2026-07-13 | **s124 — Axis-B verify-loop goal gate GRADUATED warn-only v1 → per-goal opt-in ENFORCEMENT; PLAN-0069 shipped END-TO-END (2 PRs) + CLOSED → `done/` in one session-124 day (ADR-0018 V2 Accepted #713; #721/#722, `feat`); session opener #718 `fix` surfaced `threshold_field` in the read-only Procedures viewer (View F) facet — display-only, RESOLVING the s123 frontend display gap** — every v2 consequence gated behind `if goal.enforce`, so `enforce:false` is byte-for-byte warn-only v1 (AC-3, all pre-existing goal tests UNMODIFIED); all 10 ACs met. **#721 PR1 (`_goal_state.py`):** `schema_version`→2, new `blocked-pending-human` status, first-class `enforce` bool + `amendments[]` on the Goal dataclass (closes both build hazards — unknown-field-drop + VALID_STATUSES rejection), new Amendment dataclass, SD-D `amendments_seen` on Evaluation. **#722 PR2 (`_goal_gate.py` + `/goal` + goal-evaluator):** warn→enforce ladder at the three v1 return-None sites (one bounded block → park at `blocked-pending-human`, never twice for the same state), V2-D4 unanswered-dispatch park (never released / silent-pass), SD-D drift/redirect pure function (positional `amendments_seen`, clock-free — WSL wall clock non-monotonic), `goal.md` + goal-evaluator V2-D2 anchor-divergence (refute-not-bless UNCHANGED). Cray ratified SD-A..SD-D via AskUserQuestion, all four as-rec (SD-A=2 PRs / SD-B=PR2 / SD-C=no migration / SD-D=positional). draft≠review≠verify: `plan-drafter` PLAN → Code R2 (grounded citations verified) → Cray SDs → Code build. Suite **2570/7** WITH Postgres (on merge commit `960e988`, CI PR-only); ruff + `ruff format` + `mypy --strict` clean; CI `gate` green (#721 2m37s / #722 2m46s); no MS-S1 / host-state — pure offline. PLAN-0069 `git mv`→`done/`. Full narrative: the Session-124 CF block above | `960e988` (#722 PR2 merge) / `17ca489` (#721 PR1 merge) / `.claude/hooks/{_goal_state.py,_goal_gate.py}` + the `/goal` command + the `goal-evaluator` subagent doc + `docs/plans/done/0069-*.md` |
| 2026-07-13 | **s123 — PLAN-0068 (aquaculture per-species DO floors) shipped END-TO-END + CLOSED → `done/` in ONE session-123 day; aquaculture's `morning_pond_health_round` judge now bands each pond's latest reading vs its OWN per-species `do_floor` (joined by the migrated `read_do` FK-parent join) instead of one blanket 4.0 mg/L floor — the 3rd OCT vertical on the per-entity FK-parent band substrate → Rule-of-Three MET (ADR-006), zero engine change (#715/#716)** — TWO PRs (SD-4 = (b), a Cray divergence isolating the DB-migration/first-join-consumer rollback). **#715 PR1 (substrate+RED):** `Pond.do_floor` + per-species seeds (whiteleg 4.0/4.0, tiger_prawn 4.5, tilapia 3.0) + the SD-3 flip seed (event-reading-12, pond-11 @ 4.2 mg/L, 01:55) + a RED-verify vs the unedited YAML. **#716 PR2 (migration+tests):** the `read_do` FK-parent join (`reads:[OperationalEvent, Pond]` + `join:{with:Pond, link:event_emitted_by_pond}`) + the `site_id`→`pond_site_id` declared-collision rename + `judge` `threshold:4.0`→`threshold_field:do_floor` (keeping authored `direction:below` + `watch_margin:1.0` — the FIRST shipped `threshold_field`+`watch_margin` 3-band consumer) + a Step-5 coupled-test audit (8 test files). **Zero engine change** (`git diff main -- services/` empty; rides ADR-016 FKP-1). Demo-visible flip (SD-3/AC-7): pond-11 (tiger_prawn) warms to 4.2 mg/L → `watch` under a blanket 4.0 but `breach` under its own 4.5 floor (aerate set {pond-07} → {pond-07, pond-11}); AC-7/SD-5 pins the SAME 3.4 mg/L reading = breach in a whiteleg pond (floor 4.0) but watch in a tilapia pond (floor 3.0). **draft≠review≠verify:** PR2 RESUMED an interrupted prior-session WIP (`acfcd57`, "migration done, 7 coupled tests pending"); `next-work-analyst` CAUGHT STATUS saying "BUILD NOT started" while the code showed PR1 merged + PR2 WIP — a `superseded by new info` staleness (build landed after the s122 reconcile); the 7 pending coupled-test breaks were ALL PLAN-0068 Step-5 pre-disclosed (fixture adapters not serving Pond → inner join empties / fake read_do rows lacking `do_floor` → per-entity judge fails closed FKP-3 / `threshold==4.0` asserts → `None`+`threshold_field`), no engine bug. Suite **2549/7** WITH Postgres (verified on merge commit `b55ff43`, CI PR-only); ruff + `ruff format --check` + `mypy --strict services/` clean; CI `gate` green on both PRs; no MS-S1 / host-state — pure offline. Disclosed [corrected s124 — `was an error`]: the read-only Procedures viewer (View F, `view-procedures.js`) — NOT the payload — doesn't surface `threshold_field` (a pre-existing FRONTEND s121 supply_chain display gap; the payload always carried it), out of PLAN-0068's zero-engine scope; RESOLVED s124 (#718). PLAN-0068 `git mv`→`done/`. Full narrative: the Session-123 CF block above | `b55ff43` (HEAD, #716 PR2 merge) / `befec8e` (PR2 coupled-test fixes) / `acfcd57` (PR2 WIP migration) / `d4cb9b3` (#715 PR1 merge) / `ec4fe6f` (#715 PR1 substrate) / `verticals/aquaculture/{ontology/aquaculture_v0.yaml (`Pond.do_floor`), procedures.yaml (`read_do` `join:` + `judge` `threshold_field:do_floor`), data_adapter/synthetic.py (per-species do_floor seeds + SD-3 flip reading)}` (+ regenerated `generated/**`) + `docs/plans/done/0068-*.md` |
| 2026-07-13 | **s122 — Axis-B verify loop GRADUATED to enforcing (ADR-0018 V2, Accepted 2026-07-13, #713) + next build queued (PLAN-0068 Ready — aquaculture per-species DO floors, #712); governance-text batch, NO code shipped** — **#713 ADR-0018 V2 Amendment:** graduates the Axis-B verification loop from v1 (warn-only, D5) to **v2 (enforcing)**, discharging the D5 warn-only deferral + OQ-8 "Blocking-mode promotion", and formalizes **unintentional drift vs deliberate redirect** (a divergence WITH a typed Cray sign-off = redirect/passes, WITHOUT = drift/flagged-or-blocked). SD-0..SD-4 ratified as-rec: SD-0 in-place amendment to ADR-0018 (ADR-0016 discipline — extends not reverses, D1-D7 unchanged) / SD-1 per-goal `enforce` flag (default warn) / SD-2 typed sign-off in an append-only `amendments[]` log + evaluator-detected, deterministically-consequenced divergence / SD-3 goal-gate graduation ONLY (sibling hooks out-of-scope) / SD-4 missing-evidence-under-enforce = pause `blocked-pending-human`, never a silent pass. **draft≠review≠verify:** `plan-drafter` authored → Code R2 (re-verified D5/OQ-8 + `work_fingerprint()` at `_goal_gate.py:152`; confirmed 2 build hazards — `_goal_state.py` DROPS unknown fields on rewrite [v2 fields must be dataclass fields], `VALID_STATUSES` lacks `blocked-pending-human`) → Cray ratified. Grounded by a 2026-07-13 design brief (research through 13 Jul + repo inventory, a private Artifact, NOT a repo file). **The v2 gate/schema BUILD is a follow-on PLAN** (ADR-013 D1). **#712 PLAN-0068 Ready:** the `next-work-analyst`-ranked #1 pick, `plan-drafter`-authored + Code-R2'd + Cray-ratified (SD-0..SD-5; **SD-4 = (b) TWO PRs, a Cray divergence** from the drafter's 1-PR rec) — migrates aquaculture's `morning_pond_health_round` judge from a blanket 4.0 mg/L DO floor to per-species floors via `Pond.do_floor` + a `read_do` FK-parent join (3rd OCT vertical on the per-entity band substrate → **Rule-of-Three MET**, zero engine change, rides ADR-016 FKP-1); Status = Ready, BUILD (PR1 substrate+RED / PR2 migration+tests) NOT started. No MS-S1 / host-state — pure governance-doc batch; suite unchanged. Full narrative: the Session-122 CF block above | `2e2007c` (HEAD, #713 ADR-0018 V2 merge) / `f67b713` (intervening branch-sync merge, inferred from order) / `d40d2f6` (#713 ADR-0018 V2 amendment) / `2c3a05d` (#712 PLAN-0068 Ready merge) / `c443bfd` (#712 PLAN-0068 Ready) / `docs/adr/0018-*.md` (V2 enforcing amendment) + `docs/plans/0068-*.md` (aquaculture per-species DO floors, Ready) |
| 2026-07-12 | **s121 — per-entity FK-parent `threshold_field` (ADR-016 "per-entity bands v2") shipped END-TO-END (amendment → PLAN-0067 Ready → PR1 engine → PR2 vertical) in ONE session-121 day; supply_chain cold-chain `judge` now bands each shipment vs its OWN per-cargo `temp_ceiling` instead of one blanket env ceiling (#707/#708/#709/#710)** — **#707 ADR-016 amendment (Accepted 2026-07-12):** FK-parent-column `threshold_field` (a `threshold_field` may name a column on a JOINED FK-parent of the traced query step; FKP-1..FKP-4, SD-1..SD-5, SD-4 = supply_chain-only build), discharging TF-2(i); **Code R2 caught + corrected the dispatch's "executor deferred Phase C" premise** (it had shipped in PLAN-0061 #666). **#708 PLAN-0067 Ready:** SD-1 = (b) TWO PRs (a Cray divergence isolating the DB-migration / first-join-consumer rollback), SD-2 = (b) demo-visible seed flip, SD-3 rendered ceilings, SD-4 = (a) keep env-band wrapper + guard, SD-5 = (a). **#709 PR1 (engine):** FKP-2 gate widening (`_validate_threshold_field_bindings` domain reads[0] → base + joined FK-parent, in `orchestrator.py`) + a draft-discovered `env_band_step.py` delegate-guard fix (a migrated `threshold_field` judge delegates untouched — no clobbered direction, no false `band_source: env`) + a stale-docstring fix + `spec.py` reword; 6 new engine tests. **#710 PR2 (vertical):** `Shipment.temp_ceiling` + per-cargo seeds (8/12/-15/6) + a frozen warming reading (SD-2b) + `read_temps` as the FIRST shipped `join:` consumer + the `judge` env_band → threshold_field migration; **RED-verified flip** — the frozen shipment warms to −11.8 °C → `ok` under a blanket 8 °C ceiling but `breach` under its own −15 °C ceiling (hold set 1 → 2). **Build-discovered correction:** NO Alembic migration — supply_chain has no committed ORM/DB table (energy-only), so `temp_ceiling` is in-memory only (Cray-ratified Option A). THREE draft≠review≠verify catches, one per role (Code R2 stale-docstring premise / `plan-drafter` env_band guard coupling / build AC-3 no-shipment-table). Suite **2544/7** WITH Postgres (baseline 2536 + engine 6 + vertical 2); ruff + `mypy --strict` clean; CI `gate` green on every PR; no MS-S1 / host-state — pure offline; PLAN-0067 closing to `done/` in a sibling `docs(plans)` PR. Full narrative: the Session-121 CF block above | `670117c` (HEAD, #710 PR2 vertical merge) / `0b6be2a` / `83cbb39` / `a24971c` / `4c05ecd` / `e3debdd` (the s121 #708 Ready / #709 PR1 engine / #710 PR2 vertical + PLAN-0067 close commits — merge↔content pairing inferred from order) / `1c296a4` (#707 ADR-016 amendment merge) / `7e54a34` (#707 amendment) / `services/engine/procedures/{orchestrator.py,env_band_step.py,spec.py}` + `verticals/supply_chain/{ontology/supply_chain_v0.yaml (`Shipment.temp_ceiling`),procedures.yaml (`read_temps` `join:` + `judge` env_band→`threshold_field`),data_adapter/synthetic.py (per-cargo seeds 8/12/-15/6 + frozen warming reading)}` (+ regenerated `generated/**`) + `docs/adr/0016-governed-procedure-engine.md` (per-entity FK-parent `threshold_field` amendment) + `docs/plans/done/0067-*.md` |
| 2026-07-12 | **s120 — `threshold_field` per-entity band shipped END-TO-END (ADR-016 amendment → PLAN-0066 Ready → build) in ONE session-120 day; procurement `judge_stock` now bands each `Part` vs its OWN `reorder_point` (#703/#704/#705)** — **#703 ADR-016 amendment (Accepted 2026-07-11):** per-entity `threshold_field` on evaluate steps, **same-row v1** (TF-1..TF-4, OQ-1..OQ-4), discharging PLAN-0065 SD-3's deferral; **Code R2 caught + fixed the TF-1 exactly-one → at-most-one defect BEFORE ratification.** **#704 PLAN-0066 Ready** (SDs ratified a/a/a/b — SD-4=(b) added a flip seed part so the LIVE demo shows the per-part win a blanket threshold misses). **#705 build:** `threshold_field` grammar (`spec.py` at-most-one validator) + per-entity band executor (`evaluate_step.py`, SD-1a `_entity_number`) + TF-3 load gate (`orchestrator.py` trace-to-reads, c1–c4) + governance pin (`draft.py`) + procurement migration (both `judge_stock` → `threshold_field: reorder_point`) + SD-4(b) flip seed part `part-vbelt-03`; **build-discovered coupling fixed** — `draft.py::derive_governance_todo`'s band obligation is now threshold_field-OR-threshold. THREE draft≠review≠verify catches, one per stage (R2's exactly-one→at-most-one #703 / the drafter's SD-4 seed-parity #704 / the build's `draft.py` governance coupling #705). Suite **2536/7** WITH Postgres (baseline 2516/7); ruff + `mypy --strict` clean; no host-state action; PLAN-0066 closing to `done/` in a sibling `docs(plans)` PR. Full narrative: the Session-120 CF block above | `3682d79` (HEAD, #705 build merge) / `3047386` / `57e5e08` / `40ce172` (the three #705 build commits) / `525c028` (#704 PLAN-0066 Ready merge) / `f1b7157` (#704 Ready) / `1c9a9af` (#703 ADR merge) / `758610e` (#703 amendment) / `services/engine/procedures/{spec.py,evaluate_step.py,orchestrator.py,draft.py}` + `verticals/procurement/procedures.yaml` (`judge_stock` `threshold_field: reorder_point`) + `verticals/procurement/**` (SD-4(b) flip seed `part-vbelt-03`) + `docs/adr/0016-governed-procedure-engine.md` (per-entity `threshold_field` amendment) + `docs/plans/0066-*.md` |
| 2026-07-11 | **s119 — PLAN-0065 calm-path reorder runnability BUILT (#700) + CLOSED → `done/` (#701); procurement `low_stock_reorder_round` now runnable END-TO-END; drafted→ratified→built→closed in ONE session-119 day (#699 Ready, `plan-drafter`-authored)** — **SD-2 fix (shipped Q4 grammar, ZERO engine-code change):** `read_stock` gained a `project: {fields: {stock_qty: measured_value}}` rename-projection so the shipped `EvaluateStepExecutor` bands the registry-registered adapter's `Part` rows — the production factory chain used to CRASH at `judge_stock` (raw `Part` rows carry `stock_qty`, the judge reads `measured_value`); **PLAN-0064 fact-9 DISCHARGED**. Three new tests prove runnability at three depths: production-factory chain (`test_calm_path_production_runnability`, red-verified vs the unedited YAML), manual-run HTTP (`test_calm_path_run_endpoint` — `POST /procedures/{id}/run` parks at the reorder gate, identity server-resolved), and a NEW scheduled sibling `scheduled_low_stock_reorder_round` on the PLAN-0055 scheduler (fires headless, parks at reorder). **SD-5(b) Cray-ratified AGAINST the drafter's rec:** the scheduled sibling carries `owning_person_id: req-planner` (verified ACCEPTED at execution — no validator couples it to SoD, this AT-3 path has no SoD, so it is the run principal not an SoD requester). Both paths park at ONE human go/no-go (RF-1/RF-3). **SD-3 (per-part reorder-point band) DEFERRED** — trips the L-4 tripwire (the shipped judge takes a single scalar threshold, not a per-entity field reference) → own ADR-016-amendment PLAN. PLAN-0064 shadow-parity assertion updated for the projection (routing unchanged, output projected — disclosed). Suite **2516/7** local WITH Postgres (2512/7 + 4 new); no host-state action; `docs/plans/` EMPTY again. Full narrative: the Session-119 CF block above | `06e5f39` (HEAD, #701 close-out merge) / `22a89fd` / `75696c5` / `eaf8b03` / `bfa8a36` / `5ab424a` (the six s119 commits — #699 Ready / #700 build / #701 close; merge↔content pairing inferred from order) / `verticals/procurement/procedures.yaml` (`read_stock` `project` + `scheduled_low_stock_reorder_round`) + `tests/verticals/procurement/` (`test_calm_path_production_runnability`, `test_calm_path_run_endpoint`) + `docs/plans/done/0065-*.md` |
| 2026-07-11 | **s118 CONTINUATION 2 — PLAN-0010 CLOSED "shipped + intentionally disabled" (#695) / PLAN-0064 per-step query router BUILT (#696) + CLOSED all 8 ACs → `done/` (#697); draft→R2→SD-ratify→build→close in ONE session-118 day** — #695: Cray-ratified (AskUserQuestion) after the ELI-CRAY brief; AC-1/AC-3/AC-5 ticked (tests/loop/ + the 427-message production run), AC-2/AC-4/AC-6 HONESTLY unticked (operational close over the s76 drift hazard — they become revival-PLAN requirements). #696: `QueryStepRouter` (declaration-presence, SD-1) routes the production procurement factory per step — declared `read_stock` → the SHIPPED `QueryStepExecutor` over the registry-registered `ProcurementSyntheticAdapter` (SD-5); undeclared `intake` → `_SeedQuery` byte-identically; ERRATUM-2 tripwire rewritten in place (SD-4); SD-0 zero engine change; **PLAN-0062 AC-7's deferral DISCHARGED by reference**; `low_stock_reorder_round` end-to-end still NOT production-runnable (fact 9 → Active TODO). Suite **2512/7** local WITH Postgres. Full narrative: the Session-118 CF block above | `869a56d` (#697 merge) / `9a0eb7d` / `fdd6a9b` (#696 merge) / `75ed717` / `0b784f7` (#695 merge) / `3bdef0d` / `services/engine/procedures/query_router.py` + `verticals/procurement/hero_demo/run.py` + `verticals/procurement/procedures.yaml` + `tests/verticals/procurement/test_intake_shadow_parity.py` + `docs/plans/done/0064-per-step-query-router-procurement.md` + `docs/plans/done/0010-phase3-5-scheduled-task-autonomy-loop.md` |
| 2026-07-11 | **s118 CONTINUATION — PLAN-0063 deferrals DISCHARGED (`confirmed — prior intact`, no erratum) / #692 PLAN-0064 Ready / #693 hygiene / orphan DB dropped (session 118 cont.)** — Step-5 render check PASSED its pre-committed strings over the REAL dev-DB audit chain (36 rows, breaks []; DOM-asserted + screenshot) + local full suite WITH Postgres **2507/7** (supersedes the 2391/123 degraded run); `vero_lite_test_69fa7362` DROPPED (Cray §8; all 16 checkout-path hash forms re-verified, only the live `bb36873b` remains); **PLAN-0064** (per-step QUERY router for procurement) `plan-drafter`-authored, Code R2 accept, **SD-0..SD-5 Cray-ratified as-rec**, reopens PLAN-0062 AC-7 per ERRATUM 2; PLAN-0004 + PLAN-0012 → `done/` (PLAN-0010 deliberately NOT closed — close-vs-park = Cray decision pending after the s118 ELI-CRAY brief). Full narrative: the Session-118 CF block above | `2694253` (#693 merge) / `e8cba64` (#693 docs) / `f494013` (#692 merge) / `b7e6e40` (#692 Ready) / `docs/plans/0064-per-step-query-router-procurement.md` + `docs/plans/done/{0004,0012}-*.md` |
| 2026-07-11 | **PLAN-0063 audit-chain verification surface COMPLETE (all 8 ACs) → `done/` — trust dossier object ③'s first product surface (session 118; #687/#688/#689/#690)** — #687 Ready (`plan-drafter`-authored, SD-1..6 Cray-ratified as-rec); #688 PR1 `GET /audit/verify` → typed `ChainVerificationReport`, `verify_chain()`'s (PLAN-0047 Step 5) FIRST production caller, SD-2(d) split visibility (verdict open / verbatim break detail credentialed via the new `get_optional_principal`; OQ-1 = `/audit/verify`); #689 PR2 on-demand monitor "Verify chain" panel (off the poll timers); #690 close-out with TWO DISCLOSED DEFERRALS (local merge-commit full-suite + Step-5 render check — dev Postgres down, §8 Cray go pending, erratum-if-fail). `services/db/audit_log.py` + `alembic/` byte-unchanged (AC-8 pins). Suite **2506/8** via the required CI `gate`. Full narrative: the Session-118 CF block above | `7e87d76` (#690 merge) / `576a201` (#690 close) / `360007a` (#689 merge) / `ceee552` (#689 feat) / `9d02686` (#688 merge) / `b41e3f5` (#688 feat) / `ec2250e` (#687 merge) / `e2c65f0` (#687 Ready) / `services/api/routers/audit.py` + `services/api/models/audit.py` + `services/api/auth.py` (`get_optional_principal`) + `tests/api/test_audit_verify.py` + `services/api/static/assets/view-monitor.js` + `docs/plans/done/0063-audit-chain-verification-surface.md` |
## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13; guarded trial (parallel to ADR-012) — verdict **continue-with-adjustments**. Run 1 (energy, s93) + Run 2 (supply-chain, s94) both COMPLETE, S-checks all PASS against pre-committed oracles, no R-PS trigger fired; C-1..C-3 CONFIRMED → **no open partner-sim debt**. ADR-011 audit stays gated on a REAL partner conversation (R3: SYNTHETIC provenance INFORMS but never TRIGGERS it). Full record: `docs/adr/0020-*.md` + the gitignored run packages `docs/research/private/2026-07-02-partnersim-run{1,2}-*.md`. _(Full prior narrative — the ~8 schema-mismatch findings, both run details, cross-run synthesis — archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **Procurement vertical — GO + SHIPPED (PLAN-0036 Fastenal, Stage 1):** 4th vertical greenlit (s75); PLAN-0036 drafted + merged Draft (#412, `7a7c036`; SD-1…SD-5 confirm-all). Demo target = Fastenal Thailand (auto-parts / EEC); **hero** = asset-failure → governed emergency sourcing, **calm-path** = low-stock reorder. Stage 1 = a PLAN-only pure-config plugin on the ADR-016 engine (zero `services/` core edit; CQ-1 / ADR-0023). **Pitch** = asset-ontology-triggered governed sourcing (native ontology ADR-008 + engine ADR-016), NOT the commoditized "governed"/"cross-vertical" claims. Full record: `docs/plans/0036-*.md` + the s72 de-risk dossier `docs/research/private/2026-06-22-procurement-*.md` (5 files: spec-expressiveness, GTM, asset-aware incumbent scan, AI-sourcing teardown, platform-incumbent deepdive). _(Full prior narrative archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2; Q3 ADR Accepted + BUILD COMPLETE s93 — open only for the residues).** (1) **Q3 ontology data-binding — DONE end-to-end:** the ADR-016 D2+D3 amendment (Accepted s93, #505) is now **BUILT + CLOSED** (PLAN-0046 → `done/`; #511 feat `878b517` / #512 close `eb63692`, s93 cont. 2026-07-02): `StepInput.reads: list[str]` + `Agent.allowed.object_types` + the `validate_read_bindings` **LOAD-time consistency/scoping gate** (`reads ∈ ontology ∩ allowlist`, SD-1 Option A) wired at both production pre-flight sites; `reads` H-governed via `STEP_GOVERNANCE_FIELDS` + the `lift_to_step` draft-strip hardening; 12 new tests, offline suite 2066 passed / 5 skipped. v1 = a typed read contract + load-gate, **NOT** runtime-enforced parity — the declared==dispatched teeth for the read side then **SHIPPED as PLAN-0048** (the "Q4 generic run-consume query executor", `docs/plans/done/0048-q4-generic-query-executor.md`, s96, #533–#539; all 15 ACs, Complete 2026-07-04): an engine-owned deterministic `QueryStepExecutor` (`services/engine/procedures/query_step.py`) giving *plain declared reads* the **declared ✔ · load-gated ✔ · execution-bound ✔** frame + a typed auditable refusal (no silent `[]`). **The remaining Q4 residue** (the ADR + grammar build now DONE — only the migration PLAN remains): the four shipped verticals are NOT yet on the generic executor — their query steps encode projections/joins the spec could not yet declare (PLAN-0048 fact-pack 8 / LOCKED-9: hand-written seeds stay **execution-bound ✖** until migrated). The join/projection-grammar ADR is now **Accepted** (ADR-016 Q4 amendment, #659) + the grammar is **BUILT + CLOSED** (PLAN-0061, #664–#668) — a declaring step is execution-bound ✔ for the 2 v1 shapes; only **(b) the per-vertical production-factory + seed-migration PLAN** (Phase 3 = **PLAN-0062, COMPLETE — all 5 PRs, all 9 ACs → `done/`** — PR1 #672 parity core + PR1b #673 env-band executor/energy factory + PR2 #675 supply_chain + PR3 #676 aquaculture + PR4 #682 procurement shadow-parity/close-out) is DONE, having migrated the four verticals' hand-written seeds onto the grammar (all THREE OCT query steps — energy `read_readings`, supply_chain `read_temps`, aquaculture `read_do` — now execution-bound ✔ on the production HTTP path; procurement `intake` is declared-expressible ✔ under shadow parity but production execution stays the co-existing `_SeedQuery` ✖ for derived fields; `read_stock` deferred/labelled/reason-corrected — ERRATUM 2). (2) **Box 4 (Profit Formula) — STILL DEFERRED (N≥3, unchanged).** The reasoning trace is operational, not economic — tie each action to ฿ impact (avoided outage / margin / ROI). Prepare by capturing the economic dimension as prose when hand-authoring verticals + proving the ฿ framing in the demo; type an economic-impact facet only after **N≥3** verticals triangulate it (the ADR-016 Q3 amendment left it a self-cancelling N≥3 marker). *(s84 strategy discussion + the 3-layer / ontology-binding diagram; Q3 ADR Accepted s93 #505; Q3 build complete + PLAN-0046 closed s93 cont. #511/#512; **Q4 executor SHIPPED = PLAN-0048 closed s96 #533–#539** [reconciled 2026-07-08]; **Q4 join-grammar ADR Accepted #659 + grammar built PLAN-0061 #664–#668** [reconciled 2026-07-09 s116] — **Phase-3 PLAN-0062 COMPLETE** [PR1 #672 + PR1b #673 + PR2 #675 + PR3 #676 + PR4 #682 → `done/`, reconciled 2026-07-10 s117]; **the per-entity `threshold_field` band arc (ADR-016 amendment) — FK-parent Rule-of-Three MET s123:** procurement same-row [PLAN-0066, s120] / supply_chain FK-parent [PLAN-0067, s121] / aquaculture FK-parent [**PLAN-0068** — `read_do`/`do_floor` now execution-bound + per-entity-banded, #715/#716, s123] / energy over-current FK-parent [**PLAN-0070** — `read_readings`/`rated_current_a`, judge env_band→threshold_field, the LAST shipped env_band consumer retired, #726, s125] all shipped → `done/` [reconciled 2026-07-13; energy s125]; the band-shape Rule-of-Three was already MET at N=3 s123 so energy is breadth-not-gate; TODO stays open ONLY for the Box-4 facet)*
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
