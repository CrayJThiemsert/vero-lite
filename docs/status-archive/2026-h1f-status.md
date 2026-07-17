# STATUS.md rotation archive — 2026 H1 (continuation)

> **Period covered:** 2026-07-13 (session-123) → 2026-07-16 (session-140)
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

## Rotated this reconcile (session-123, 2026-07-13 — PLAN-0068 aquaculture per-species DO floors close-out)

### Current Focus block removed — session 119 [rotated 2026-07-13, session-123 reconcile — normal rotation under the 4-session CF window]

> **Session 119, 2026-07-11 (head_commit `869a56d` → `06e5f39`) — PLAN-0065
> (calm-path reorder runnability) drafted → ratified → built → closed in ONE
> session-119 day; procurement `low_stock_reorder_round` is now runnable
> end-to-end.** #699 Ready (`plan-drafter`-authored) → #700 build → #701
> Complete → `done/`. **The fix (SD-2, shipped Q4 grammar, ZERO engine-code
> change):** the `read_stock` step gained a `project: {fields: {stock_qty:
> measured_value}}` rename-projection so the shipped `EvaluateStepExecutor` can
> band the registry-registered adapter's `Part` rows — before this the
> production factory chain CRASHED at `judge_stock` (raw `Part` rows carry
> `stock_qty`, the judge reads `measured_value`; PLAN-0064 fact-9 DISCHARGED).
> **Three new tests prove runnability at three depths:** the production-factory
> chain (`test_calm_path_production_runnability`, red-verified against the
> unedited YAML); the manual-run HTTP endpoint (`test_calm_path_run_endpoint` —
> `POST /procedures/{id}/run` parks at the reorder gate, identity
> server-resolved); and a NEW scheduled sibling
> `scheduled_low_stock_reorder_round` on the PLAN-0055 scheduler (fires
> headless, parks at reorder). **SD-5(b) — Cray-ratified AGAINST the drafter's
> recommendation:** the scheduled sibling carries `owning_person_id:
> req-planner` for accountability parity; the divergent path was verified
> ACCEPTED at execution (no validator couples `owning_person_id` to SoD, and
> this AT-3 path has no SoD — so it is the run principal, not an SoD requester).
> **Honest frame:** both the manual-run and scheduled paths park at ONE human
> go/no-go — nothing auto-approves (RF-1/RF-3). **SD-3 (per-part reorder-point
> band) DEFERRED** — it trips the L-4 tripwire (the shipped judge takes a single
> scalar threshold, not a per-entity field reference) → its own
> ADR-016-amendment PLAN (Active TODO). **Build-discovered coupling
> (disclosed):** the projection renamed `stock_qty→measured_value`, so the
> PLAN-0064 shadow-parity assertion (`read_stock` == raw adapter rows) was
> updated deliberately (routing unchanged, output projected). **Evidence bar:**
> #700 CI `gate` green; local full suite WITH Postgres **2516 passed / 7
> skipped** (baseline 2512/7 + 4 new); ruff + ruff-format + `mypy --strict
> services/` clean; no MS-S1 / host-state action. `docs/plans/` is EMPTY again
> (every plan in `done/`).

### Recent Decisions row removed — 2026-07-10 (PLAN-0062 COMPLETE, sessions 116–117) [rotated 2026-07-13, session-123 reconcile — normal rotation under the 10-row RD window]

| 2026-07-10 | **PLAN-0062 (Q4 Phase-3 per-vertical seed migration, parity-guarded, SD-C) — COMPLETE, all 9 ACs → `done/` (sessions 116–117; #671/#672/#673/#675/#676/#682)** — **#671 Ready** (`docs/plans/0062-*.md`): plan-drafter-authored, Code R2-verified facts 3/5/7, **SD-1..SD-6 Cray-ratified as-rec** (AskUserQuestion). **#672 PR1 (parity core, s116):** energy `read_readings` → the DECLARED latest-per-group grammar (`reads:[OperationalEvent]` + `where:{event_type:reading}` + `project:{latest_per:event_emitted_by_asset, order_by:occurred_at}`) + the shared `assert_read_step_parity` harness (grammar == an INDEPENDENT hand-coded SD-5 reference, ZERO tolerance) + SD-5-edge fixtures + a 4-vertical load-gate pin; suite 2458/7. **#673 PR1b (s117):** `EnvBandEvaluateExecutor` (binds `OCT_RECOMMEND_THRESHOLD`/`_DIRECTION` onto a band-less step, delegates to the SHIPPED `EvaluateStepExecutor`) + deterministic `advisory_stub.py` + `register_energy_procedure_executors` + `main.py` per-vertical registrar table → energy `read_readings` now **execution-bound ✔ on the production HTTP path**. **#675 PR2 (s117):** supply_chain `read_temps` over `event_concerns_shipment` + `verticals/supply_chain/procedures_factory.py`; parity harness went vertical-parameterised (SD-3); reused PR1b's `EnvBandEvaluateExecutor` + `advisory_stub_factory` UNCHANGED (same `env_band` judge, only the threshold differs — 8 °C cold-chain vs energy's 90 °C); OQ-2 settled against the data (`where:{event_type:reading}` load-bearing); suite 2473/7. **#676 PR3 (s117):** aquaculture `read_do` over `event_emitted_by_pond` + `verticals/aquaculture/procedures_factory.py` (the `main.py` registrar table's 4th/final entry); binds the shipped `EvaluateStepExecutor` UNWRAPPED (judge is `in_file_band` typed `threshold 4.0/below/watch_margin 1.0`; a test asserts `EnvBandEvaluateExecutor` is ABSENT — the `env` half of the ADR-016 D2-A3 split). All THREE OCT query steps now execution-bound ✔; procurement `intake` is declared-expressible ✔ (shadow parity, PR4) but production execution stays the co-existing `_SeedQuery` (✖ for the derived fields); `read_stock` deferred/labelled/reason-corrected. ADR-016 D2-A4 honored (env band selected by the FACTORY). **PR4 (#682, `bd8e586` → merge `359555b`):** AC-6 intake shadow-parity over the REAL `FastenalCsvAdapter` (declared join half == `_intake_seed`'s fields, derived fields ABSENT; four `PurchaseOrder`∩`Quotation` column collisions renamed to keep each quote's supplier); AC-7 `read_stock` deferral KEPT, its "no substrate" reason CORRECTED to per-`StepKind` executor routing (ERRATUM 2, Cray-ratified, pinned by an executable invariant test) → PLAN-0062 **COMPLETE (all 9 ACs)**, both errata (ERRATUM 1 = AC-5 "shipped executors" vs PR1b's `EnvBandEvaluateExecutor`; ERRATUM 2) recorded in the Close-out, `git mv`→`done/`; suite **2496/7 on the merge commit**. Both errata DISCLOSED, not silently reinterpreted. Un-gated Code build (PLAN-0062 §6); offline (SD-6), MS-S1 untouched. Full narrative: the Session-117 CF block above | `359555b` (#682 PR4 merge) / `bd8e586` (#682 feat) / `a711927` (#676 PR3 merge) / `c17500a` (#676 feat) / `624b731` (#675 PR2 merge) / `b9c5ebd` (#675 feat) / `ea08e54` (#673 merge) / `f41da9c` (#673 feat) / `8641cb3` (#672 merge) / `d9e4bd2` (#672 feat) / `66beb17` (#671 merge) / `833676e` (#671 Ready) / `services/engine/procedures/{env_band_step.py,advisory_stub.py}` + `verticals/{energy,supply_chain,aquaculture}/procedures_factory.py` + `services/api/main.py` + `tests/services/engine/procedures/test_seed_migration_parity.py` + `tests/verticals/procurement/test_intake_shadow_parity.py` + `docs/plans/done/0062-per-vertical-seed-migration.md` |

### Current Focus block removed — session 120 [rotated 2026-07-13, session-124 reconcile — normal rotation under the 4-session CF window]

> **Session 120, 2026-07-12 (head_commit `06e5f39` → `3682d79`) —
> `threshold_field` per-entity band shipped END-TO-END in ONE session-120 day:
> ADR-016 amendment → PLAN-0066 Ready → build.** #703 amendment → #704 Ready →
> #705 build; procurement `judge_stock` now bands each `Part` against its OWN
> `reorder_point` (not one blanket scalar), and the LIVE demo shows the per-part
> flip a single threshold misses. **#703 — ADR-016 amendment (2026-07-11),
> Accepted:** per-entity `threshold_field` on evaluate steps, **same-row v1**
> (TF-1..TF-4, OQ-1..OQ-4); discharges the deferral of PLAN-0065 SD-3. **#704 —
> PLAN-0066 Ready** (SDs ratified a/a/a/b; SD-4=(b) adds a flip seed part so the
> LIVE demo exhibits the per-part win). **#705 — build:** `threshold_field`
> grammar (`spec.py` at-most-one validator) + the per-entity band executor
> (`evaluate_step.py`, SD-1a `_entity_number`) + the TF-3 load gate
> (`orchestrator.py` trace-to-reads, c1–c4) + the governance pin (`draft.py`) +
> the procurement migration (both `judge_stock` → `threshold_field:
> reorder_point`) + the SD-4(b) flip seed part `part-vbelt-03`.
> **Build-discovered coupling (disclosed):** `draft.py::derive_governance_todo`'s
> band obligation is now threshold_field-OR-threshold. **THREE
> draft≠review≠verify catches, one per stage:** R2 caught + fixed the ADR's TF-1
> exactly-one → at-most-one defect BEFORE ratification (#703); the `plan-drafter`
> added the SD-4 flip seed for demo seed-parity (#704); the build surfaced +
> fixed the `draft.py` governance coupling (#705). **Evidence bar:** full suite
> **2536 passed / 7 skipped** WITH Postgres (baseline 2516/7); ruff + `mypy
> --strict` clean; no MS-S1 / host-state action. PLAN-0066 is being closed to
> `done/` in a sibling `docs(plans)` PR.

### Recent Decisions row removed — 2026-07-10 (flaky-DB-test isolation #678/#679/#680, session 117) [rotated 2026-07-13, session-124 reconcile — normal rotation under the 10-row RD window]

| 2026-07-10 | **Flaky-DB-test isolation track — one intermittent `test_procedure_headline` failure = TWO unrelated bugs, one PRODUCTION (session 117, a CONCURRENT Code track; #678/#679/#680)** — **#678 (a) production correctness:** WSL2 `datetime.now(UTC)` is NON-MONOTONIC (2 backward steps / 20 s, −555 ms worst); `load_run` orders step results by that wall-clock `created_at` and `resume_run`/`GET /runs/{id}` read `step_results[-1]` as the suspended step → a run straddling the jump resumed from an already-COMPLETED step (re-ran a decided gate, dup side effects, stuck `waiting_human`; or "undecided proposals"); ~1 process in 20. Fixed by selecting the suspended step by **STATUS** (`suspended_step_result()`); gate/resolve never affected (looks up by caller `step_id`). **(b) test isolation (deterministic):** `Base.metadata` is import-populated → a `tests/services/db`-only process never registered `action_identity`, so `drop_all` left it for the next `alembic upgrade head` (`DuplicateTableError`); the full suite hid it. Fixed with `alembic/env.py`-mirroring registration imports + `DROP SCHEMA public CASCADE` per test. **#679:** that reset made concurrent sibling-worktree `pytest` wipe each other → test DB scoped per checkout (`vero_lite_test_<8-hex repo root>`), explicit `TEST_DATABASE_URL` still wins so CI is unaffected; control experiment (shared DB → both fail; scoped → both pass). **#680:** the "exactly one unresumed step" invariant was documented but unenforced → two such rows now raise; `get_run` answers **409** not an unhandled 500; + the HTTP-surface regression test #678 left owing. Suite 2473/7 → **2488/7**, verified on the merge commit (CI here is PR-only); ruff+format+mypy clean; offline, MS-S1 untouched, dev DB unchanged. Carry-overs → Active TODOs. | `9a12087` (#680 merge) / `7afff6a` / `8b617b0` (#679 merge) / `4f018bf` / `47a58ed` (#678 merge) / `a4593c8` / `b4b042c` / `services/engine/procedures/persistence.py` + `services/api/routers/runs.py` + `tests/db_support.py` |

### Current Focus block removed — Session 121 (per-entity FK-parent threshold_field v2 / supply_chain temp_ceiling, #707-#710) [rotated 2026-07-13, session-125 reconcile — 4-session CF window]

> **Session 121, 2026-07-12 (head_commit `71d0fc8` → `670117c`) — per-entity
> FK-parent `threshold_field` (ADR-016 "per-entity bands v2") shipped
> END-TO-END in ONE session-121 day: amendment → PLAN → 2-PR build → close.**
> A `threshold_field` may now name a column on a JOINED FK-parent of the traced
> query step, and supply_chain's cold-chain `judge` bands each shipment's latest
> reading against its OWN per-cargo `temp_ceiling` instead of one blanket env
> ceiling. #707 amendment → #708 Ready → #709 PR1 (engine) → #710 PR2
> (vertical). **#707 — ADR-016 amendment (2026-07-12), Accepted:**
> FK-parent-column `threshold_field` (per-entity bands v2), FKP-1..FKP-4,
> SD-1..SD-5 ratified (SD-4 = supply_chain-only build); Code R2 caught +
> corrected the dispatch's "executor deferred Phase C" premise (it had shipped,
> PLAN-0061 #666); discharges TF-2(i). **#708 — PLAN-0067 Ready:** SD-1 = (b)
> TWO PRs (a Cray divergence isolating the DB-migration / first-join-consumer
> rollback), SD-2 = (b) demo-visible seed flip, SD-3 rendered ceilings, SD-4 =
> (a) keep the env-band wrapper + guard, SD-5 = (a). **#709 — PR1 (engine):**
> the FKP-2 gate widening (`_validate_threshold_field_bindings` domain reads[0]
> → base + joined FK-parent, in `orchestrator.py`) + a draft-discovered
> `env_band_step.py` delegate-guard fix (a migrated `threshold_field` judge
> delegates untouched — no clobbered direction, no false `band_source: env`) +
> a stale-docstring fix + `spec.py` reword; 6 new engine tests. **#710 — PR2
> (vertical):** `Shipment.temp_ceiling` + per-cargo seeds (8/12/-15/6) + a
> frozen warming reading (SD-2b) + `read_temps` as the FIRST shipped `join:`
> consumer + the `judge` env_band → threshold_field migration; RED-verified
> flip — the frozen shipment warms to −11.8 °C → `ok` under a blanket 8 °C
> ceiling but `breach` under its own −15 °C ceiling (hold set 1 → 2).
> **Build-discovered correction:** NO Alembic migration — supply_chain has no
> committed ORM/DB table (energy-only), so `temp_ceiling` is in-memory only
> (Cray-ratified Option A). **THREE draft≠review≠verify catches, one per role:**
> Code R2 (stale-docstring premise) / `plan-drafter` (env_band guard coupling) /
> build (AC-3 no-shipment-table). **Evidence bar:** full suite **2544 passed / 7
> skipped** WITH Postgres (baseline 2536 + engine 6 + vertical 2); ruff + `mypy
> --strict` clean; CI `gate` green on every PR; no MS-S1 / host-state — pure
> offline. PLAN-0067 is being closed to `done/` in a sibling `docs(plans)` PR.

### Recent Decisions row removed — 2026-07-10 (TESTS half of #678 wall-clock invariant, #684, session 117) [rotated 2026-07-13, session-125 reconcile — 10-row RD window]

| 2026-07-10 | **Residual flaky-suite fix — the TESTS half of #678's wall-clock invariant (session 117; #684, `fix(test)`)** — a ~1-in-3 full-suite flake on `main` (two procurement DB tests), NO code cause (#683 docs-only), green in isolation. SAME non-monotonic WSL2 `datetime.now(UTC)` as #678 on the OTHER side of the seam: `load_run` still `ORDER BY created_at`; #678 migrated only the PRODUCTION consumers to `suspended_step_result()`, leaving SIX TEST sites on `step_results[-1]` → under a backward step `[-1]` names the wrong (completed) step. Fixed by intent: 4 demo sites → `suspended_step_result()`, 2 latent → select by `step_id` (a status-assert would be circular), + 2 order-asserting sites now compare `sorted(...)` (a round-trip preserves a step SET, not an order). Cover: a non-vacuous AST guard (`test_load_run_ordering_guard.py`, reports EXACTLY the six pre-fix sites) + a deterministic clock-inversion pin. NO production code changed; `pytest -q` 5x pre-merge + 3x on the merge commit (CI PR-only) = eight consecutive greens, 2499/7 (was 2496 + 3 new); ruff clean, offline, MS-S1 untouched. | `22242e4` (#684 merge) / `0a9542a` (#684 fix) / `tests/services/db/test_load_run_ordering_guard.py` + `tests/services/db/{test_event_procurement_demo.py,test_scheduled_procurement_demo.py}` + `tests/services/engine/procedures/{test_procedure_persistence.py,test_write_ahead.py}` |

### Current Focus block removed — session 122 (Axis-B v2 enforcing ADR-0018 #713 + PLAN-0068 Ready #712) [rotated 2026-07-13, session-126 reconcile — 4-session CF window]

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

### Recent Decisions row removed — 2026-07-11 (PLAN-0063 audit-chain verification surface COMPLETE, #687-#690, session 118) [rotated 2026-07-13, session-126 reconcile — 10-row RD window]

| 2026-07-11 | **PLAN-0063 audit-chain verification surface COMPLETE (all 8 ACs) → `done/` — trust dossier object ③'s first product surface (session 118; #687/#688/#689/#690)** — #687 Ready (`plan-drafter`-authored, SD-1..6 Cray-ratified as-rec); #688 PR1 `GET /audit/verify` → typed `ChainVerificationReport`, `verify_chain()`'s (PLAN-0047 Step 5) FIRST production caller, SD-2(d) split visibility (verdict open / verbatim break detail credentialed via the new `get_optional_principal`; OQ-1 = `/audit/verify`); #689 PR2 on-demand monitor "Verify chain" panel (off the poll timers); #690 close-out with TWO DISCLOSED DEFERRALS (local merge-commit full-suite + Step-5 render check — dev Postgres down, §8 Cray go pending, erratum-if-fail). `services/db/audit_log.py` + `alembic/` byte-unchanged (AC-8 pins). Suite **2506/8** via the required CI `gate`. Full narrative: the Session-118 CF block above | `7e87d76` (#690 merge) / `576a201` (#690 close) / `360007a` (#689 merge) / `ceee552` (#689 feat) / `9d02686` (#688 merge) / `b41e3f5` (#688 feat) / `ec2250e` (#687 merge) / `e2c65f0` (#687 Ready) / `services/api/routers/audit.py` + `services/api/models/audit.py` + `services/api/auth.py` (`get_optional_principal`) + `tests/api/test_audit_verify.py` + `services/api/static/assets/view-monitor.js` + `docs/plans/done/0063-audit-chain-verification-surface.md` |

### Current Focus block removed — session 123 (PLAN-0068 aquaculture per-species DO floors, #715/#716) [rotated 2026-07-14, session-127 reconcile — 4-session CF window]

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

### Recent Decisions row removed — 2026-07-11 (s118 CONTINUATION — PLAN-0063 deferrals discharged + PLAN-0064 Ready, #692/#693) [rotated 2026-07-14, session-127 reconcile — 10-row RD window]

| 2026-07-11 | **s118 CONTINUATION — PLAN-0063 deferrals DISCHARGED (`confirmed — prior intact`, no erratum) / #692 PLAN-0064 Ready / #693 hygiene / orphan DB dropped (session 118 cont.)** — Step-5 render check PASSED its pre-committed strings over the REAL dev-DB audit chain (36 rows, breaks []; DOM-asserted + screenshot) + local full suite WITH Postgres **2507/7** (supersedes the 2391/123 degraded run); `vero_lite_test_69fa7362` DROPPED (Cray §8; all 16 checkout-path hash forms re-verified, only the live `bb36873b` remains); **PLAN-0064** (per-step QUERY router for procurement) `plan-drafter`-authored, Code R2 accept, **SD-0..SD-5 Cray-ratified as-rec**, reopens PLAN-0062 AC-7 per ERRATUM 2; PLAN-0004 + PLAN-0012 → `done/` (PLAN-0010 deliberately NOT closed — close-vs-park = Cray decision pending after the s118 ELI-CRAY brief). Full narrative: the Session-118 CF block above | `2694253` (#693 merge) / `e8cba64` (#693 docs) / `f494013` (#692 merge) / `b7e6e40` (#692 Ready) / `docs/plans/0064-per-step-query-router-procurement.md` + `docs/plans/done/{0004,0012}-*.md` |

### Current Focus block removed — Session 124 (Axis-B goal gate GRADUATED v1→v2 per-goal enforcement, PLAN-0069 #721/#722) [rotated 2026-07-14, session-128 reconcile — 4-block CF window]

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

### Recent Decisions row removed — 2026-07-11 (s118 CONTINUATION 2 — PLAN-0010 CLOSED + PLAN-0064 per-step query router #695/#696/#697) [rotated 2026-07-14, session-128 reconcile — 10-row RD window]

| 2026-07-11 | **s118 CONTINUATION 2 — PLAN-0010 CLOSED "shipped + intentionally disabled" (#695) / PLAN-0064 per-step query router BUILT (#696) + CLOSED all 8 ACs → `done/` (#697); draft→R2→SD-ratify→build→close in ONE session-118 day** — #695: Cray-ratified (AskUserQuestion) after the ELI-CRAY brief; AC-1/AC-3/AC-5 ticked (tests/loop/ + the 427-message production run), AC-2/AC-4/AC-6 HONESTLY unticked (operational close over the s76 drift hazard — they become revival-PLAN requirements). #696: `QueryStepRouter` (declaration-presence, SD-1) routes the production procurement factory per step — declared `read_stock` → the SHIPPED `QueryStepExecutor` over the registry-registered `ProcurementSyntheticAdapter` (SD-5); undeclared `intake` → `_SeedQuery` byte-identically; ERRATUM-2 tripwire rewritten in place (SD-4); SD-0 zero engine change; **PLAN-0062 AC-7's deferral DISCHARGED by reference**; `low_stock_reorder_round` end-to-end still NOT production-runnable (fact 9 → Active TODO). Suite **2512/7** local WITH Postgres. Full narrative: the Session-118 CF block above | `869a56d` (#697 merge) / `9a0eb7d` / `fdd6a9b` (#696 merge) / `75ed717` / `0b784f7` (#695 merge) / `3bdef0d` / `services/engine/procedures/query_router.py` + `verticals/procurement/hero_demo/run.py` + `verticals/procurement/procedures.yaml` + `tests/verticals/procurement/test_intake_shadow_parity.py` + `docs/plans/done/0064-per-step-query-router-procurement.md` + `docs/plans/done/0010-phase3-5-scheduled-task-autonomy-loop.md` |

### Current Focus block removed — Session 125 (event-bridge FULL-LOOP live smoke + energy 4th OCT vertical, over-current FK-parent band) [rotated 2026-07-14, session-129 reconcile — 4-session CF window]

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

### Recent Decisions row removed — 2026-07-11 (s119 — PLAN-0065 calm-path reorder runnability BUILT + CLOSED #700/#701) [rotated 2026-07-14, session-129 reconcile — 10-row RD window]

| 2026-07-11 | **s119 — PLAN-0065 calm-path reorder runnability BUILT (#700) + CLOSED → `done/` (#701); procurement `low_stock_reorder_round` now runnable END-TO-END; drafted→ratified→built→closed in ONE session-119 day (#699 Ready, `plan-drafter`-authored)** — **SD-2 fix (shipped Q4 grammar, ZERO engine-code change):** `read_stock` gained a `project: {fields: {stock_qty: measured_value}}` rename-projection so the shipped `EvaluateStepExecutor` bands the registry-registered adapter's `Part` rows — the production factory chain used to CRASH at `judge_stock` (raw `Part` rows carry `stock_qty`, the judge reads `measured_value`); **PLAN-0064 fact-9 DISCHARGED**. Three new tests prove runnability at three depths: production-factory chain (`test_calm_path_production_runnability`, red-verified vs the unedited YAML), manual-run HTTP (`test_calm_path_run_endpoint` — `POST /procedures/{id}/run` parks at the reorder gate, identity server-resolved), and a NEW scheduled sibling `scheduled_low_stock_reorder_round` on the PLAN-0055 scheduler (fires headless, parks at reorder). **SD-5(b) Cray-ratified AGAINST the drafter's rec:** the scheduled sibling carries `owning_person_id: req-planner` (verified ACCEPTED at execution — no validator couples it to SoD, this AT-3 path has no SoD, so it is the run principal not an SoD requester). Both paths park at ONE human go/no-go (RF-1/RF-3). **SD-3 (per-part reorder-point band) DEFERRED** — trips the L-4 tripwire (the shipped judge takes a single scalar threshold, not a per-entity field reference) → own ADR-016-amendment PLAN. PLAN-0064 shadow-parity assertion updated for the projection (routing unchanged, output projected — disclosed). Suite **2516/7** local WITH Postgres (2512/7 + 4 new); no host-state action; `docs/plans/` EMPTY again. Full narrative: the Session-119 CF block above | `06e5f39` (HEAD, #701 close-out merge) / `22a89fd` / `75696c5` / `eaf8b03` / `bfa8a36` / `5ab424a` (the six s119 commits — #699 Ready / #700 build / #701 close; merge↔content pairing inferred from order) / `verticals/procurement/procedures.yaml` (`read_stock` `project` + `scheduled_low_stock_reorder_round`) + `tests/verticals/procurement/` (`test_calm_path_production_runnability`, `test_calm_path_run_endpoint`) + `docs/plans/done/0065-*.md` |

### Current Focus block removed — 2026-07-13 (s126 — ADR-0030 Accepted: Box-4 economic-impact ฿ facet) [rotated 2026-07-14, session-130 reconcile — 4-session CF window]

> **Session 126, 2026-07-13 (head_commit `b19dce4` → `a9dbb6f`) — ADR-0030
> Accepted: the Box-4 economic-impact (฿) facet — typed, ADVISORY,
> trace-carried — DISCHARGING the ADR-016 self-cancelling Box-4 deferral now
> that N≥3 is MET (4 shipped verticals). ONE PR (#728, `docs(adr)`); doc-only
> governance-text batch — NO code/tests shipped; the BUILD is a follow-on
> PLAN.** **D1 (SD-1):** ฿ is carried as an advisory `economic_impact`
> `ReasoningStep` in `reasoning_trace` (`detail` = a producer-validated
> `EconomicImpact` model) — ZERO change to the ADR-007 D2 "verbatim" envelope
> (`services/engine/actions.py:11`); mirrors the PLAN-0035/ADR-0022
> advisory-trace precedent + the s74 trace-only trust-shape discipline. **D3
> (SD-3):** ONE common cross-vertical shape (`baseline` vs `governed` exposure
> → `net_benefit`) for ROI comparability; per-vertical `kind` = avoided_outage
> (energy) / expedite_tradeoff (procurement) / spoilage_avoided (supply_chain)
> / mortality_avoided (aquaculture). **D4 (SD-4) — disclosed `was an error`
> (CLAUDE.md §6):** the ADR-016-promised "enforceable self-cancelling N≥3
> marker" test was NEVER built — a claim-vs-code gap caught by session-126
> MANUAL grounding (the re-open was NOT triggered mechanically); enforcement
> moves forward as a ≥3-vertical build-completion AC in the follow-on PLAN.
> **D5/D6/D7:** ฿ is always provisional/advisory, never auto-authoritative
> (§8); contract-only ADR (the build is a fast-follow PLAN gated on Accepted);
> a fresh ADR-0030 referencing ADR-016 (discharged) + ADR-007 (envelope).
> **draft≠review≠verify:** `plan-drafter` authored → Code R2 (load-bearing
> citations verified vs disk, incl. independently confirming NO economic/N≥3
> marker exists in `tests/`) → Cray ratified ALL SD-1..SD-7 as-recommended
> (s126, via AskUserQuestion) → Code committed (#728). CI `gate` pass 2m35s;
> doc-only so ruff/mypy/format skipped (no files to check). Minor artifact:
> the in-body ratification note was G1-gate-blocked once Status flipped to
> Accepted (deterministic) — the ratification is recorded in the ADR's
> Deciders line + the commit/PR instead. Commit: `a9dbb6f` (#728 merge).

### Recent Decisions row removed — 2026-07-12 (s120 — threshold_field per-entity band shipped END-TO-END) [rotated 2026-07-14, session-130 reconcile — 10-row RD window]

| 2026-07-12 | **s120 — `threshold_field` per-entity band shipped END-TO-END (ADR-016 amendment → PLAN-0066 Ready → build) in ONE session-120 day; procurement `judge_stock` now bands each `Part` vs its OWN `reorder_point` (#703/#704/#705)** — **#703 ADR-016 amendment (Accepted 2026-07-11):** per-entity `threshold_field` on evaluate steps, **same-row v1** (TF-1..TF-4, OQ-1..OQ-4), discharging PLAN-0065 SD-3's deferral; **Code R2 caught + fixed the TF-1 exactly-one → at-most-one defect BEFORE ratification.** **#704 PLAN-0066 Ready** (SDs ratified a/a/a/b — SD-4=(b) added a flip seed part so the LIVE demo shows the per-part win a blanket threshold misses). **#705 build:** `threshold_field` grammar (`spec.py` at-most-one validator) + per-entity band executor (`evaluate_step.py`, SD-1a `_entity_number`) + TF-3 load gate (`orchestrator.py` trace-to-reads, c1–c4) + governance pin (`draft.py`) + procurement migration (both `judge_stock` → `threshold_field: reorder_point`) + SD-4(b) flip seed part `part-vbelt-03`; **build-discovered coupling fixed** — `draft.py::derive_governance_todo`'s band obligation is now threshold_field-OR-threshold. THREE draft≠review≠verify catches, one per stage (R2's exactly-one→at-most-one #703 / the drafter's SD-4 seed-parity #704 / the build's `draft.py` governance coupling #705). Suite **2536/7** WITH Postgres (baseline 2516/7); ruff + `mypy --strict` clean; no host-state action; PLAN-0066 closing to `done/` in a sibling `docs(plans)` PR. Full narrative: the Session-120 CF block above | `3682d79` (HEAD, #705 build merge) / `3047386` / `57e5e08` / `40ce172` (the three #705 build commits) / `525c028` (#704 PLAN-0066 Ready merge) / `f1b7157` (#704 Ready) / `1c9a9af` (#703 ADR merge) / `758610e` (#703 amendment) / `services/engine/procedures/{spec.py,evaluate_step.py,orchestrator.py,draft.py}` + `verticals/procurement/procedures.yaml` (`judge_stock` `threshold_field: reorder_point`) + `verticals/procurement/**` (SD-4(b) flip seed `part-vbelt-03`) + `docs/adr/0016-governed-procedure-engine.md` (per-entity `threshold_field` amendment) + `docs/plans/0066-*.md` |


### Recent Decisions row removed — 2026-07-12 (s121 — per-entity FK-parent threshold_field shipped END-TO-END) [rotated 2026-07-15, session-131 reconcile — 10-row RD window]

| 2026-07-12 | **s121 — per-entity FK-parent `threshold_field` (ADR-016 "per-entity bands v2") shipped END-TO-END (amendment → PLAN-0067 Ready → PR1 engine → PR2 vertical) in ONE session-121 day; supply_chain cold-chain `judge` now bands each shipment vs its OWN per-cargo `temp_ceiling` instead of one blanket env ceiling (#707/#708/#709/#710)** — **#707 ADR-016 amendment (Accepted 2026-07-12):** FK-parent-column `threshold_field` (a `threshold_field` may name a column on a JOINED FK-parent of the traced query step; FKP-1..FKP-4, SD-1..SD-5, SD-4 = supply_chain-only build), discharging TF-2(i); **Code R2 caught + corrected the dispatch's "executor deferred Phase C" premise** (it had shipped in PLAN-0061 #666). **#708 PLAN-0067 Ready:** SD-1 = (b) TWO PRs (a Cray divergence isolating the DB-migration / first-join-consumer rollback), SD-2 = (b) demo-visible seed flip, SD-3 rendered ceilings, SD-4 = (a) keep env-band wrapper + guard, SD-5 = (a). **#709 PR1 (engine):** FKP-2 gate widening (`_validate_threshold_field_bindings` domain reads[0] → base + joined FK-parent, in `orchestrator.py`) + a draft-discovered `env_band_step.py` delegate-guard fix (a migrated `threshold_field` judge delegates untouched — no clobbered direction, no false `band_source: env`) + a stale-docstring fix + `spec.py` reword; 6 new engine tests. **#710 PR2 (vertical):** `Shipment.temp_ceiling` + per-cargo seeds (8/12/-15/6) + a frozen warming reading (SD-2b) + `read_temps` as the FIRST shipped `join:` consumer + the `judge` env_band → threshold_field migration; **RED-verified flip** — the frozen shipment warms to −11.8 °C → `ok` under a blanket 8 °C ceiling but `breach` under its own −15 °C ceiling (hold set 1 → 2). **Build-discovered correction:** NO Alembic migration — supply_chain has no committed ORM/DB table (energy-only), so `temp_ceiling` is in-memory only (Cray-ratified Option A). THREE draft≠review≠verify catches, one per role (Code R2 stale-docstring premise / `plan-drafter` env_band guard coupling / build AC-3 no-shipment-table). Suite **2544/7** WITH Postgres (baseline 2536 + engine 6 + vertical 2); ruff + `mypy --strict` clean; CI `gate` green on every PR; no MS-S1 / host-state — pure offline; PLAN-0067 closing to `done/` in a sibling `docs(plans)` PR. Full narrative: the Session-121 CF block above | `670117c` (HEAD, #710 PR2 vertical merge) / `0b6be2a` / `83cbb39` / `a24971c` / `4c05ecd` / `e3debdd` (the s121 #708 Ready / #709 PR1 engine / #710 PR2 vertical + PLAN-0067 close commits — merge↔content pairing inferred from order) / `1c296a4` (#707 ADR-016 amendment merge) / `7e54a34` (#707 amendment) / `services/engine/procedures/{orchestrator.py,env_band_step.py,spec.py}` + `verticals/supply_chain/{ontology/supply_chain_v0.yaml (`Shipment.temp_ceiling`),procedures.yaml (`read_temps` `join:` + `judge` env_band→`threshold_field`),data_adapter/synthetic.py (per-cargo seeds 8/12/-15/6 + frozen warming reading)}` (+ regenerated `generated/**`) + `docs/adr/0016-governed-procedure-engine.md` (per-entity FK-parent `threshold_field` amendment) + `docs/plans/done/0067-*.md` |

*Rotated 2026-07-15 (session-132 reconcile) — Recent Decisions row, session 122:*

| 2026-07-13 | **s122 — Axis-B verify loop GRADUATED to enforcing (ADR-0018 V2, Accepted 2026-07-13, #713) + next build queued (PLAN-0068 Ready — aquaculture per-species DO floors, #712); governance-text batch, NO code shipped** — **#713 ADR-0018 V2 Amendment:** graduates the Axis-B verification loop from v1 (warn-only, D5) to **v2 (enforcing)**, discharging the D5 warn-only deferral + OQ-8 "Blocking-mode promotion", and formalizes **unintentional drift vs deliberate redirect** (a divergence WITH a typed Cray sign-off = redirect/passes, WITHOUT = drift/flagged-or-blocked). SD-0..SD-4 ratified as-rec: SD-0 in-place amendment to ADR-0018 (ADR-0016 discipline — extends not reverses, D1-D7 unchanged) / SD-1 per-goal `enforce` flag (default warn) / SD-2 typed sign-off in an append-only `amendments[]` log + evaluator-detected, deterministically-consequenced divergence / SD-3 goal-gate graduation ONLY (sibling hooks out-of-scope) / SD-4 missing-evidence-under-enforce = pause `blocked-pending-human`, never a silent pass. **draft≠review≠verify:** `plan-drafter` authored → Code R2 (re-verified D5/OQ-8 + `work_fingerprint()` at `_goal_gate.py:152`; confirmed 2 build hazards — `_goal_state.py` DROPS unknown fields on rewrite [v2 fields must be dataclass fields], `VALID_STATUSES` lacks `blocked-pending-human`) → Cray ratified. Grounded by a 2026-07-13 design brief (research through 13 Jul + repo inventory, a private Artifact, NOT a repo file). **The v2 gate/schema BUILD is a follow-on PLAN** (ADR-013 D1). **#712 PLAN-0068 Ready:** the `next-work-analyst`-ranked #1 pick, `plan-drafter`-authored + Code-R2'd + Cray-ratified (SD-0..SD-5; **SD-4 = (b) TWO PRs, a Cray divergence** from the drafter's 1-PR rec) — migrates aquaculture's `morning_pond_health_round` judge from a blanket 4.0 mg/L DO floor to per-species floors via `Pond.do_floor` + a `read_do` FK-parent join (3rd OCT vertical on the per-entity band substrate → **Rule-of-Three MET**, zero engine change, rides ADR-016 FKP-1); Status = Ready, BUILD (PR1 substrate+RED / PR2 migration+tests) NOT started. No MS-S1 / host-state — pure governance-doc batch; suite unchanged. Full narrative: the Session-122 CF block above | `2e2007c` (HEAD, #713 ADR-0018 V2 merge) / `f67b713` (intervening branch-sync merge, inferred from order) / `d40d2f6` (#713 ADR-0018 V2 amendment) / `2c3a05d` (#712 PLAN-0068 Ready merge) / `c443bfd` (#712 PLAN-0068 Ready) / `docs/adr/0018-*.md` (V2 enforcing amendment) + `docs/plans/0068-*.md` (aquaculture per-species DO floors, Ready) |


### Current Focus block removed — session 129 (PLAN-0073 Box-4 economic_impact facet in the hero-demo UI) [rotated 2026-07-15, session-133 reconcile — 4-session CF window]

> **Session 129, 2026-07-14 (head_commit `88e6984` → `f250593`) — PLAN-0073
> (the Box-4 `economic_impact` facet surfaced in the Palantir-lite hero-demo
> UI) shipped END-TO-END + CLOSED → `done/` in ONE session-129 day (#737 Ready
> → #738 build): the hero demo's beat-4 (฿) now ALSO carries the typed Box-4
> `EconomicImpact` facet with audit-grade provenance — previously beat-4
> rendered ONLY the demo `HeroImpactLedger`.** NO ADR change (ADR-0030 D2
> ledger + facet coexist; ADR-007 D2 envelope byte-untouched — the facet stays
> trace-carried). `plan-drafter` authored PLAN-0073, Code R2, Cray ratified
> **SD-1(a)/SD-2(b)/SD-3** via AskUserQuestion (all as-recommended), then built
> + closed the same session. **#737 (`cc8516e`, `docs(plans)`) — PLAN-0073
> Ready.** **#738 (`f250593`, `feat`) — THE build.** **SD-1(a) fire-for-real:**
> `_intake_seed` now carries `event_type` (from the failure event it already
> fetches at `run.py:208`) so the Box-4 producer fires INSIDE the governed run.
> **Build-discovered (the PLAN's OQ-1, resolved empirically via the AC-2 RED
> test):** the hero `source` step is `GovernanceActionExecutor._scored_rule`,
> which REPLACES the base action envelopes (to thread the selected spend
> forward for `doa_tier`) — so it now LIFTS the advisory `economic_impact`
> trace step onto the persisted step trace, otherwise the facet was computed
> then DISCARDED. Generalizes to any governed scored_rule action with a
> registered producer; advisory + never-raise (ADR-0030 D5). **SD-2(b):** `GET
> /demo/hero/impact` gains an additive optional `economic_impact` field; the
> producer reuses `build_hero_impact_ledger` so the ฿ figures EQUAL the
> ledger's (no drift); ledger fields byte-identical. **SD-3 frontend:**
> `view-hero.js` renders a provenance strip UNDER the unchanged ledger card — a
> `kind` chip, an always-visible `PROVISIONAL` badge (s74 trust-shape), and a
> "show provenance" toggle revealing `assumptions[]` + `basis_refs`; `hero.css`
> (c35) + `view-hero.js` (c36) `?v=` bumped. **Build-discovered (disclosed):**
> the pre-commit mypy hook caught a `list[Mapping]` vs `list[dict[str,Any]]`
> type error the first manual `mypy` never ran (the `&&` chain stopped at a
> `ruff format --check` failure) — fixed with `cast` + annotation.
> **draft≠review≠verify:** `plan-drafter` PLAN (#737) → Code R2 (anchors
> re-verified on disk; SD-1a "one line" confirmed) → Cray SD-1(a)/SD-2(b)/SD-3
> → Code build. **Evidence:** 3 new AC tests GREEN (AC-1 endpoint carries the
> facet `net_benefit`==ledger + 4 `basis_refs`; AC-2 producer fires on the real
> hero seed + the persisted governed-run source trace carries the
> `economic_impact` step; AC-2/AC-3 the existing ledger tests pass UNMODIFIED);
> AC-4 preview (oct-demo-procurement) renders the strip + working toggle, no
> console errors; full suite **2599 passed / 7 skipped** WITH Postgres —
> verified on BOTH the PR head AND the merge commit `f250593` (CI PR-only, so
> the merge-commit re-run is the real gate); ruff + `ruff format --check` +
> `mypy --strict services/` clean. 0 open PRs after the close; tree clean (2
> pre-existing untracked KEEP: `.claude/benchmark-results/`,
> `.claude/launch.json`); MS-S1 idle; dev Postgres UP; loop-dispatcher DISABLED.
> PLAN-0073 `git mv`→`done/` this session; `docs/plans/` empty again. Commits:
> `cc8516e` (#737 PLAN-0073 Ready) → `f250593` (#738 feat build + close).

> _Rotation note (session-132 reconcile, 2026-07-15, `docs(status):`):
> frontmatter bumped to `head_commit 098b0d9` (session 132); a new s132
> Current-Focus block was PREPENDED for the GOVERNANCE batch (PLAN-0075
> Proposed #746 + the ADR-0026 D4 amendment closing the F1 AT-2
> authority-enforcement gap). With s132 prepended, Current Focus held 5
> sessions (s132 + s131 + s130 + s129 + s128), so the OLDEST — the whole
> **session-128** block (PLAN-0072: the Palantir-lite hero demo's beat-3 "run
> it" step now genuinely resolving the parked DOA gate through the production
> `POST /runs/{id}/gate/resolve`, #734/#735) — was rotated OUT to keep the
> 4-session window (now s132 + s131 + s130 + s129). Recent Decisions rotated
> its OLDEST row (2026-07-13 **s122** — the Axis-B verify loop GRADUATED to
> enforcing [ADR-0018 V2 Accepted #713] + PLAN-0068 Ready) to keep the 10-row
> window. Both were emitted verbatim in the reconcile reply for the caller to
> append to `docs/status-archive/2026-h1-status.md` (Bash-side). Prior rotation
> notes (through the session-131 reconcile) are consolidated into this one
> (R4). Per the STATUS.md Rotation Policy (R1/R2/R4)._

> _Older content rotates out of this file per the **STATUS.md Rotation Policy (R1-R6)** in [`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md) (Lesson #23): Current Focus keeps the 4 newest sessions (<=8 blocks); Recent Decisions keeps the last 10 rows. Rotated blocks/rows live in [`docs/status-archive/`](status-archive/) (sessions <=46: `2026-h1-current-focus.md`; 2026-06-10 onward: `2026-h1-status.md`) and git history (Tier 3)._

### Recent Decisions row removed — 2026-07-13 (s123 — PLAN-0068 aquaculture per-species DO floors) [rotated 2026-07-15, session-133 reconcile — 10-row RD window]

| 2026-07-13 | **s123 — PLAN-0068 (aquaculture per-species DO floors) shipped END-TO-END + CLOSED → `done/` in ONE session-123 day; aquaculture's `morning_pond_health_round` judge now bands each pond's latest reading vs its OWN per-species `do_floor` (joined by the migrated `read_do` FK-parent join) instead of one blanket 4.0 mg/L floor — the 3rd OCT vertical on the per-entity FK-parent band substrate → Rule-of-Three MET (ADR-006), zero engine change (#715/#716)** — TWO PRs (SD-4 = (b), a Cray divergence isolating the DB-migration/first-join-consumer rollback). **#715 PR1 (substrate+RED):** `Pond.do_floor` + per-species seeds (whiteleg 4.0/4.0, tiger_prawn 4.5, tilapia 3.0) + the SD-3 flip seed (event-reading-12, pond-11 @ 4.2 mg/L, 01:55) + a RED-verify vs the unedited YAML. **#716 PR2 (migration+tests):** the `read_do` FK-parent join (`reads:[OperationalEvent, Pond]` + `join:{with:Pond, link:event_emitted_by_pond}`) + the `site_id`→`pond_site_id` declared-collision rename + `judge` `threshold:4.0`→`threshold_field:do_floor` (keeping authored `direction:below` + `watch_margin:1.0` — the FIRST shipped `threshold_field`+`watch_margin` 3-band consumer) + a Step-5 coupled-test audit (8 test files). **Zero engine change** (`git diff main -- services/` empty; rides ADR-016 FKP-1). Demo-visible flip (SD-3/AC-7): pond-11 (tiger_prawn) warms to 4.2 mg/L → `watch` under a blanket 4.0 but `breach` under its own 4.5 floor (aerate set {pond-07} → {pond-07, pond-11}); AC-7/SD-5 pins the SAME 3.4 mg/L reading = breach in a whiteleg pond (floor 4.0) but watch in a tilapia pond (floor 3.0). **draft≠review≠verify:** PR2 RESUMED an interrupted prior-session WIP (`acfcd57`, "migration done, 7 coupled tests pending"); `next-work-analyst` CAUGHT STATUS saying "BUILD NOT started" while the code showed PR1 merged + PR2 WIP — a `superseded by new info` staleness (build landed after the s122 reconcile); the 7 pending coupled-test breaks were ALL PLAN-0068 Step-5 pre-disclosed (fixture adapters not serving Pond → inner join empties / fake read_do rows lacking `do_floor` → per-entity judge fails closed FKP-3 / `threshold==4.0` asserts → `None`+`threshold_field`), no engine bug. Suite **2549/7** WITH Postgres (verified on merge commit `b55ff43`, CI PR-only); ruff + `ruff format --check` + `mypy --strict services/` clean; CI `gate` green on both PRs; no MS-S1 / host-state — pure offline. Disclosed [corrected s124 — `was an error`]: the read-only Procedures viewer (View F, `view-procedures.js`) — NOT the payload — doesn't surface `threshold_field` (a pre-existing FRONTEND s121 supply_chain display gap; the payload always carried it), out of PLAN-0068's zero-engine scope; RESOLVED s124 (#718). PLAN-0068 `git mv`→`done/`. Full narrative: the Session-123 CF block above | `b55ff43` (HEAD, #716 PR2 merge) / `befec8e` (PR2 coupled-test fixes) / `acfcd57` (PR2 WIP migration) / `d4cb9b3` (#715 PR1 merge) / `ec4fe6f` (#715 PR1 substrate) / `verticals/aquaculture/{ontology/aquaculture_v0.yaml (`Pond.do_floor`), procedures.yaml (`read_do` `join:` + `judge` `threshold_field:do_floor`), data_adapter/synthetic.py (per-species do_floor seeds + SD-3 flip reading)}` (+ regenerated `generated/**`) + `docs/plans/done/0068-*.md` |

### Recent Decisions row removed — 2026-07-13 (s124 — Axis-B verify-loop goal gate graduated to enforcement + PLAN-0069 closed) [rotated 2026-07-15, session-133 close-out reconcile — 10-row RD window]

| 2026-07-13 | **s124 — Axis-B verify-loop goal gate GRADUATED warn-only v1 → per-goal opt-in ENFORCEMENT; PLAN-0069 shipped END-TO-END (2 PRs) + CLOSED → `done/` in one session-124 day (ADR-0018 V2 Accepted #713; #721/#722, `feat`); session opener #718 `fix` surfaced `threshold_field` in the read-only Procedures viewer (View F) facet — display-only, RESOLVING the s123 frontend display gap** — every v2 consequence gated behind `if goal.enforce`, so `enforce:false` is byte-for-byte warn-only v1 (AC-3, all pre-existing goal tests UNMODIFIED); all 10 ACs met. **#721 PR1 (`_goal_state.py`):** `schema_version`→2, new `blocked-pending-human` status, first-class `enforce` bool + `amendments[]` on the Goal dataclass (closes both build hazards — unknown-field-drop + VALID_STATUSES rejection), new Amendment dataclass, SD-D `amendments_seen` on Evaluation. **#722 PR2 (`_goal_gate.py` + `/goal` + goal-evaluator):** warn→enforce ladder at the three v1 return-None sites (one bounded block → park at `blocked-pending-human`, never twice for the same state), V2-D4 unanswered-dispatch park (never released / silent-pass), SD-D drift/redirect pure function (positional `amendments_seen`, clock-free — WSL wall clock non-monotonic), `goal.md` + goal-evaluator V2-D2 anchor-divergence (refute-not-bless UNCHANGED). Cray ratified SD-A..SD-D via AskUserQuestion, all four as-rec (SD-A=2 PRs / SD-B=PR2 / SD-C=no migration / SD-D=positional). draft≠review≠verify: `plan-drafter` PLAN → Code R2 (grounded citations verified) → Cray SDs → Code build. Suite **2570/7** WITH Postgres (on merge commit `960e988`, CI PR-only); ruff + `ruff format` + `mypy --strict` clean; CI `gate` green (#721 2m37s / #722 2m46s); no MS-S1 / host-state — pure offline. PLAN-0069 `git mv`→`done/`. Full narrative: the Session-124 CF block above | `960e988` (#722 PR2 merge) / `17ca489` (#721 PR1 merge) / `.claude/hooks/{_goal_state.py,_goal_gate.py}` + the `/goal` command + the `goal-evaluator` subagent doc + `docs/plans/done/0069-*.md` |

### Current Focus block removed — session 130 (ADR-0031 core-lifecycle architecture + plan-drafter rigor hardening) [rotated 2026-07-15, session-135 reconcile — 4-session CF window]

> **Session 130, 2026-07-14 (head_commit `f250593` → `192dc52`) —
> FOUNDATION/GOVERNANCE session: NO code feature shipped; two docs/config PRs
> that harden the drafter's rigor and name vero-lite's core-lifecycle
> architecture.** **(1) #740 (`eea875f`, `chore(drafter)`) — plan-drafter rigor
> hardening (Lesson #0030 + a feedback memory).** The `plan-drafter` is
> deliberately bounded (it TRUSTS its dispatch fact-pack), so a stale NEGATIVE
> claim fed as a given ("OQ-8 unbuilt") nearly drove a WRONG ADR decision. Fix:
> (a) Lesson #0030 + a feedback memory — verify the fact-pack BEFORE dispatching
> the drafter, ESPECIALLY negative / precondition claims (**the newest accepted
> ADR wins on FACTS** — an older ADR's OQ may already be resolved by a later
> ADR); (b) `.claude/agents/plan-drafter.md` operating-discipline **point 8** (a
> drafter-side backstop: cite-or-flag negative claims + a targeted supersession
> grep). Root cause = Code dispatch hygiene, NOT a drafter defect. **(2) #741
> (`192dc52`, `docs(adr)`) — ADR-0031 "core lifecycle architecture"
> (Accepted).** Names vero-lite's two extensibility idioms (runtime registries
> vs closed typed governed enums = the moat spine) and ratifies the principle
> **"closed governed core + ONE typed, policy-carrying seam per core"** as the
> answer to multi-vertical scale WITHOUT dissolving the moat. Builds NO seam —
> it PRE-DESIGNS each core's seam for when its N≥2 trigger fires (the **fractal
> Rule-of-Three**), with greppable moat tripwires. Seam map (D3): transform
> StepKind · TriggerDriver/ECA · governance-gate plugin + decision-as-data ·
> executor auto-discovery fold-in · audit transition taxonomy.
> **draft≠review≠verify:** `plan-drafter` authored ADR-0031 → Code R2 → Cray
> ratified OQ-1..4 as-recommended via AskUserQuestion. **First run under the
> #740 hardening — the drafter CAUGHT OQ-4:** ADR-0025 D7's AT-2-generator CI
> marker was NEVER built (only the principal-identity mirror exists) — armed as
> an AC of the future gate-seam / Path-2 PLAN. **Direction (Cray s130):** the
> hero must GENERATE the governance (AT-2: `doa_tier` / SoD), not compose around
> it — sequenced as **Path 2** (hand-author a 2nd AT-2 signature on a DIFFERENT
> vertical pressing a DIFFERENT seam → reach N≥2 → THEN build the AT-2 generator
> per ADR-0025 D7); the **reframe**: OQ-8 (the typed AT-2 sub-model) is ALREADY
> BUILT by ADR-0025, so AT-2 generation is an S–M build on shipped spec, not a
> mega-program. **Grounded by** the private research doc
> `docs/research/private/2026-07-14-work-lifecycle-cores.md` (the 7-core spine +
> seam map that grounds ADR-0031; gitignored). Doc/config-only — no `services/`
> change, no tests, deterministic-offline (no MS-S1 / host-state). 0 open PRs
> after; tree clean (2 pre-existing untracked KEEP: `.claude/benchmark-results/`,
> `.claude/launch.json`); MS-S1 idle; dev Postgres UP; loop-dispatcher DISABLED.
> Open remediations: OQ-4 (arm the ADR-0025 D7 AT-2 marker — Path-2 AC) + OQ-2
> (executor auto-discovery fold-in — small chore, N≥4, anytime). Commits:
> `eea875f` (#740 drafter hardening) → `192dc52` (#741 ADR-0031 Accepted).

### Recent Decisions row removed — 2026-07-13 (s125 — event-bridge full-loop live smoke PASS + energy over-current 4th OCT vertical) [rotated 2026-07-15, session-135 reconcile — 10-row RD window]

| 2026-07-13 | **s125 — (1) event-bridge FULL-LOOP live smoke PASS (#724, EVIDENCE per §8) + (2) energy shipped as the 4th OCT vertical on the per-entity FK-parent band substrate (over-CURRENT, PLAN-0070 #725 Ready + #726 feat BUILT + CLOSED→`done/`)** — **#724 (`22365f2`, `docs(logs)`):** the deferred PLAN-0056 AC-12 / PLAN-0057 host-state smoke — on real MS-S1 (`gpt-oss:20b`) the reactive recommender picked `emergency_source` for the procurement CNC line-down event AND propagated through the production fire path (`recommend`→`build_event_resolver`→`fire_event`) into a PERSISTED `event_emergency_sourcing_round` run parked at the DOA `approve` gate (฿288k → `appr-pm`, `svc-buyer` on-behalf `req-planner`); closes the one remaining live seam (s114/115 proved the recommender-level pick). Disposable test DB; `event_bridge_enabled` default False (ship-dark), no prod code changed. **#725 (`9571abb`, `docs(plans)`) PLAN-0070 Ready** (`plan-drafter`-authored, Code R2 PASS all 7 citations, Cray SD-1..SD-6 via AskUserQuestion). **#726 (`b19dce4`, `feat`) BUILT+CLOSED one PR (SD-1):** re-themes energy's `substation_health_sweep` from over-TEMPERATURE → over-CURRENT — `read_readings` gains the FK-parent `join:` (`event_emitted_by_asset`) + `where {measured_kind: current}` + `site_id→asset_site_id` rename; the `judge` migrates `env_band` → `threshold_field: rated_current_a` + `direction: above` (each feeder banded vs its OWN `Asset.rated_current_a`). Demo flip: Feeder Meter A @ 84 A = `ok` under blanket env 90 but `breach` at 105% of its OWN 80 A rating → parks `waiting_human`; inverter (61 A) stays under its 722 A rating. **Energy's judge was the LAST shipped `env_band` consumer — retires here** (the `EnvBandEvaluateExecutor` engine path stays test-covered). NO new ADR / ontology / regen / Alembic (rides Accepted ADR-016 FKP amendment, its pre-recorded energy follow-on); whole change = `synthetic.py` + `procedures.yaml` + tests. Zero functional `services/` change (AC-8; only an SD-5 docstring hunk). Build-discovered coupling (disclosed correction to AC-8): 2 new current readings grew energy events 11→13 → NL-query `gold.yaml` nl-02/03/05 updated to match the data; no prod code. draft≠review≠verify: `plan-drafter` PLAN → Code R2 → Cray SD-1..SD-6 → build. All 9 ACs; suite **2572/7** WITH Postgres (on merge commit `b19dce4`, CI PR-only); ruff + `ruff format` + `mypy --strict` clean; BUILD deterministic-offline (live smoke = #724). Honesty: demo-breadth (Rule-of-Three MET at N=3 by PLAN-0068), not moat-critical. PLAN-0070 `git mv`→`done/`. Full narrative: the Session-125 CF block above | `b19dce4` (HEAD, #726 feat merge) / `9571abb` (#725 PLAN-0070 Ready) / `22365f2` (#724 live-smoke log) / `verticals/energy/{data_adapter/synthetic.py, procedures.yaml}` + `tests/**` + `docs/logs/2026-07-13-event-bridge-full-loop-live-smoke.md` + `docs/plans/done/0070-*.md` |

### Current Focus block removed — 2026-07-15 (s131 — PLAN-0074 2nd AT-2 signature shipped + CLOSED, N=2) [rotated 2026-07-16, session-136 reconcile — 4-session CF window]

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

### Recent Decisions row removed — 2026-07-13 (s126 — ADR-0030 Accepted, Box-4 economic-impact facet) [rotated 2026-07-16, session-136 reconcile — 10-row RD window]

| 2026-07-13 | **s126 — ADR-0030 Accepted (#728): the Box-4 economic-impact ฿ facet — typed, ADVISORY, trace-carried (`economic_impact` `ReasoningStep`, producer-validated `EconomicImpact` detail; ZERO ADR-007 D2 envelope change) — DISCHARGING the ADR-016 self-cancelling N≥3 Box-4 deferral (N=4)** — ONE cross-vertical shape (`baseline` vs `governed` exposure → `net_benefit`) + per-vertical `kind` (avoided_outage / expedite_tradeoff / spoilage_avoided / mortality_avoided). Disclosed `was an error` (§6): the promised N≥3 marker test was NEVER built → enforcement = a ≥3-vertical build-completion AC in the follow-on BUILD PLAN. Doc-only, contract-only batch (no code/tests). `plan-drafter` → Code R2 → Cray SD-1..SD-7 as-rec. Full narrative: the Session-126 CF block above | `a9dbb6f` (HEAD, #728 `docs(adr)` merge) / `docs/adr/0030-*.md` |

## Rotated this reconcile (session-137, 2026-07-16 — building_materials 5th vertical Tier-1 Mirror + the `GET /procedures` spec-less fix, #765)

### Current-Focus block — Session 132 (head_commit `098b0d9`) [rotated 2026-07-16, session-137 reconcile — 4-session CF window]

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

### Recent Decisions row removed — 2026-07-14 (s127 — PLAN-0071 Box-4 economic-impact ฿ facet shipped across all 4 OCT verticals) [rotated 2026-07-16, session-137 reconcile — 10-row RD window]

| 2026-07-14 | **s127 — PLAN-0071 (the Box-4 economic-impact ฿ facet) shipped END-TO-END across all 4 OCT verticals (2 PRs) + CLOSED → `done/`; the reactive AND governed recommenders now append an ADVISORY, trace-carried `economic_impact` `ReasoningStep` (baseline vs governed exposure → net ฿ benefit) — DISCHARGING the ADR-016 self-cancelling Box-4 N≥3 deferral with an OWNED marker (AC-5 GREEN at N=4); ADR-007 D2 envelope byte-verbatim (#731/#732)** — **#731 PR1 (`81c7070`, `feat`) engine core:** new `services/engine/economic_impact.py` (`EconomicExposure`/`EconomicImpact` + a NEVER-RAISE `build_economic_steps` helper) wired at BOTH `RecommendedAction` sites (`recommender._compose_llm_record` reactive + `action_step._compose_action` governed), appended LAST, never on `_rule_recommend`; AC-5 marker landed RED (`xfail(strict=True)`); conftest autouse clears the producer registry; envelope (`services/engine/actions.py`) byte-untouched. **#732 PR2 (`b11ea40`, `feat`) THE close:** four per-vertical ฿ producers (`verticals/<ns>/economic_impact.py`) — energy `avoided_outage` ฿405k / supply_chain `spoilage_avoided` ฿2.12M / aquaculture `mortality_avoided` ฿247k (assumptions-first per SD-B/SD-G, every ฿ input a named `assumptions[]` entry, NO ontology/regen/migration); procurement `expedite_tradeoff` from the committed-CSV demo ledger (`hero_demo/ledger.py` byte-untouched, `basis_refs` cite CSV columns, gated on the emergency-failure trigger — OQ-C calm-path → `None`, hero-PO exemplar stands in for per-event PO anchor, deferred v2); `discovery._register_vertical` gained a GUARDED optional producer import (`ModuleNotFoundError.name` checked). AC-5 GREEN at N=4; AC-9 GREEN (real energy producer → one `economic_impact` step, net ฿405,000); coupled-test audit = every pin PINNED-UNMODIFIED. draft≠review≠verify: `plan-drafter` PLAN → Code R2 → Cray SD-A..SD-G → build. Suite **2591 passed / 7 skipped / 0 xfailed** WITH Postgres (verified on BOTH PR head + merge commit `b11ea40`, CI PR-only); ruff + `ruff format --check` + `mypy --strict services/` clean; deterministic-offline (no MS-S1 / host-state); 0 open PRs. PLAN-0071 `git mv`→`done/`. Full narrative: the Session-127 CF block above | `b11ea40` (HEAD, #732 PR2 merge) / `81c7070` (#731 PR1 engine core) / `services/engine/economic_impact.py` + `services/engine/{recommender.py, procedures/action_step.py, discovery.py}` + `verticals/{energy,supply_chain,aquaculture,procurement}/economic_impact.py` + `tests/**` (AC-5 ≥3-vertical marker + AC-9) + `docs/plans/done/0071-*.md` |

## Rotated this reconcile (session-138, 2026-07-16 — PLAN-0078 PR-3 severity re-sequencing + AT-2 N=1 misinformation-kill, #768/#767)

### Current-Focus block — Session 133 (close-out: PLAN-0075 COMPLETE + AC-13 + PLAN-0076 filed) [rotated 2026-07-16, session-138 reconcile — 4-session CF window]

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


### Current-Focus block — Session 133 (core: PLAN-0075 AT-2 authority enforcement at the run gate) [rotated 2026-07-16, session-138 reconcile — 4-session CF window]

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


### Recent Decisions row removed — 2026-07-14 (s129 — PLAN-0073 Box-4 economic_impact facet in the hero-demo UI) [rotated 2026-07-16, session-138 reconcile — 10-row RD window]

| 2026-07-14 | **s129 — PLAN-0073 (the Box-4 `economic_impact` facet surfaced in the Palantir-lite hero-demo UI) shipped END-TO-END + CLOSED → `done/` in ONE session-129 day (#737 Ready → #738 build); beat-4 (฿) now ALSO carries the typed Box-4 `EconomicImpact` facet with audit-grade provenance UNDER the unchanged demo ledger; NO ADR change (ADR-0030 D2 ledger+facet coexist; ADR-007 D2 envelope byte-untouched — facet stays trace-carried)** — Cray ratified SD-1(a)/SD-2(b)/SD-3 via AskUserQuestion (all as-rec). **SD-1(a) fire-for-real:** `_intake_seed` carries `event_type` (from the failure event at `run.py:208`) so the Box-4 producer fires INSIDE the governed run; build-discovered (OQ-1, via the AC-2 RED test) the hero `source` step is `GovernanceActionExecutor._scored_rule` which REPLACES the base action envelopes (threading the selected spend for `doa_tier`) → it now LIFTS the advisory `economic_impact` trace step onto the persisted step trace (else computed-then-discarded); advisory + never-raise (ADR-0030 D5). **SD-2(b):** `GET /demo/hero/impact` gains an additive optional `economic_impact` field; the producer reuses `build_hero_impact_ledger` so the ฿ figures EQUAL the ledger's (no drift, ledger byte-identical). **SD-3:** `view-hero.js` provenance strip under the unchanged ledger card — `kind` chip + always-visible `PROVISIONAL` badge (s74 trust-shape) + "show provenance" toggle → `assumptions[]` + `basis_refs`; `hero.css` c35 / `view-hero.js` c36 `?v=` bumps. Build-discovered (disclosed): pre-commit mypy caught a `list[Mapping]` vs `list[dict[str,Any]]` the first manual `mypy` skipped (the `&&` chain stopped at `ruff format --check`) → fixed with `cast` + annotation. draft≠review≠verify: `plan-drafter` PLAN → Code R2 (anchors re-verified on disk) → Cray SD-1(a)/SD-2(b)/SD-3 → build. 3 new AC tests GREEN (AC-1 endpoint facet `net_benefit`==ledger + 4 `basis_refs`; AC-2 producer fires on the real hero seed + persisted governed-run source trace carries the `economic_impact` step; AC-2/AC-3 existing ledger tests UNMODIFIED); AC-4 preview renders the strip + toggle, no console errors; suite **2599/7** WITH Postgres (verified on BOTH PR head + merge commit `f250593`, CI PR-only); ruff + `ruff format --check` + `mypy --strict services/` clean; deterministic-offline (no MS-S1 / host-state); 0 open PRs. PLAN-0073 `git mv`→`done/`. Full narrative: the Session-129 CF block above | `f250593` (HEAD, #738 feat merge) / `cc8516e` (#737 PLAN-0073 Ready) / `verticals/procurement/hero_demo/**` (`_intake_seed` `event_type` + `economic_impact` endpoint field + producer) + `GovernanceActionExecutor._scored_rule` (lifts the advisory step onto the persisted trace) + the oct-demo-procurement frontend (`view-hero.js` provenance strip, `?v=` bumps) + `tests/**` (3 AC tests) + `docs/plans/done/0073-*.md` |

### Recent Decisions row removed — 2026-07-14 (s128 — PLAN-0072 hero-demo beat-3 real DOA gate resolve) [rotated 2026-07-16, session-138 reconcile — 10-row RD window]

| 2026-07-14 | **s128 — PLAN-0072 (the Palantir-lite hero demo's beat-3 "run it" step) shipped END-TO-END + CLOSED → `done/` in ONE session-128 day (#734 Ready → #735 build); the hero demo's beat-3 now GENUINELY resolves the parked DOA gate through the REAL production `POST /runs/{id}/gate/resolve`, rendering the persisted truth — replacing a FAKE front-end badge; NO engine change** — Cray picked D3 (next-work-analyst-ranked); `plan-drafter` PLAN → Code R2 → Cray SD-A(b)/SD-B(b)/SD-C(a)/SD-D(a) via AskUserQuestion → build. **Backend:** event opener additively exposes the parked `run_id` on its `hero` dict; generation-aware replay (SD-C, clock-free COUNT of decided runs bumps `detected_at` +1h past the 3600 s dedup bucket → a FRESH parked run); SD-A(b) drives the PRODUCTION resolve route with `api_auth_enabled` + a real authenticated `appr-pm` Person (RF-1 end-to-end), NO new endpoint. **Frontend** `renderActPanel` reworked: SD-D(a) inline login (authenticate THEN sign), SD-B(b) Approve AND Reject, renders the persisted `GateResolveResponse` (approve → COMPLETED + SoD tie; reject = continue+record → COMPLETED, NOT a rejected terminal); `api.js` Hero.runDetail/resolve; `?v=` bumps. **Build-discovered prod bug (disclosed AC-6 correction):** the SoD-403 path `asdict`'d a frozenset `SoDViolation.constraint_steps` → un-serializable → Starlette 500 MASKED the 403 (procurement = first frozenset SoD verdict on this HTTP path); fixed in `services/api/routers/runs.py` (frozenset → sorted list), security posture INTACT — SoD fails CLOSED before serialize (run stays parked, `gate_refused` audit), only the response CODE was wrong. OQ-4 resolved (reject test → downstream tolerates empty executed-effect set). draft≠review≠verify: `plan-drafter` PLAN → Code R2 → Cray SD-A..SD-D → build. 5 new AC tests GREEN; suite **2596/7** WITH Postgres (on BOTH PR head + merge commit `88e6984`, CI PR-only); ruff + `ruff format --check` + `mypy --strict services/` clean; deterministic-offline (no MS-S1 / host-state; Postgres for DB-backed ACs only); 0 open PRs. PLAN-0072 `git mv`→`done/`. Full narrative: the Session-128 CF block above | `88e6984` (HEAD, #735 feat merge) / `85f90ed` (#734 PLAN-0072 Ready) / `services/api/routers/runs.py` (SoD-403 JSON-sanitize) + `verticals/procurement/hero_demo/**` (`run_id` expose + generation-aware replay) + the oct-demo-procurement frontend (`renderActPanel`, `api.js` Hero.runDetail/resolve, `?v=` bumps) + `tests/**` (5 AC tests) + `docs/plans/done/0072-*.md` |

## Rotated this reconcile (session-140, 2026-07-16 — the 4-artifact strategic-continuity program: ADR-0032 Accepted + PLAN-0079 Tracking + the STATUS pointer, #770/#771/#769)

### Current-Focus block — Session 135 (close-out: PLAN-0077 transform-grammar build COMPLETE across 5 PRs) [rotated 2026-07-16, session-140 reconcile — 4-session CF window]

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

> _Rotation note (session-138 reconcile, 2026-07-16, `docs(status):`):
> frontmatter → `head_commit 9a5eecf` (session 138); a new **session-138** block
> was PREPENDED for PLAN-0078 PR-3 (cold-chain severity re-sequencing, #768) +
> the AT-2 `N=1` misinformation-kill / PLAN-0078 doc-drift reconcile (#767), so
> the two OLDEST — BOTH **session-133** blocks (the "close-out" AC-13 /
> PLAN-0076-filed block AND the "core" AT-2 run-gate-enforcement block, #749 /
> #751 / #752) — rotated OUT (4-session window, now s138 + s137 + s136 + s135)
> to `docs/status-archive/2026-h1-status.md`. Recent Decisions gained the s138
> #768 (PR-3) + #767 (misinformation-kill) rows and rotated its two OLDEST
> (**s129**, 2026-07-14 — PLAN-0073 Box-4 `economic_impact` facet, #737/#738; +
> **s128**, 2026-07-14 — PLAN-0072 hero-demo beat-3 "run it", #734/#735) to the
> same archive (10-row window). Prior rotation notes (through the session-137
> reconcile) are consolidated here (R4). Per the STATUS.md Rotation Policy
> (R1/R2/R4)._

> _Older content rotates out of this file per the **STATUS.md Rotation Policy (R1-R6)** in [`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md) (Lesson #23): Current Focus keeps the 4 newest sessions (<=8 blocks); Recent Decisions keeps the last 10 rows. Rotated blocks/rows live in [`docs/status-archive/`](status-archive/) (sessions <=46: `2026-h1-current-focus.md`; 2026-06-10 onward: `2026-h1-status.md`) and git history (Tier 3)._

### Recent Decisions row removed — 2026-07-14 (s130 — plan-drafter rigor hardening + ADR-0031 core-lifecycle architecture Accepted) [rotated 2026-07-16, session-140 reconcile — 10-row RD window]

| 2026-07-14 | **s130 — FOUNDATION/GOVERNANCE session (NO feature; 2 docs/config PRs): plan-drafter rigor hardening (#740) + ADR-0031 "core lifecycle architecture" Accepted (#741)** — **#740 (`eea875f`, `chore(drafter)`):** a stale NEGATIVE fact-pack claim ("OQ-8 unbuilt") nearly drove a WRONG ADR decision → Lesson #0030 + a feedback memory (verify the fact-pack, ESPECIALLY negative / precondition claims, BEFORE dispatching the drafter — **the newest accepted ADR wins on FACTS**) + `.claude/agents/plan-drafter.md` operating-discipline **point 8** (a drafter-side backstop: cite-or-flag negative claims + a targeted supersession grep); root cause = Code dispatch hygiene, NOT a drafter defect. **#741 (`192dc52`, `docs(adr)`) — ADR-0031 Accepted:** names vero-lite's two extensibility idioms (runtime registries vs closed typed governed enums = the moat spine) + ratifies **"closed governed core + ONE typed, policy-carrying seam per core"** as multi-vertical scale WITHOUT dissolving the moat; builds NO seam — PRE-DESIGNS each core's seam for its N≥2 trigger (the fractal Rule-of-Three) with greppable moat tripwires; seam map D3 (transform StepKind · TriggerDriver/ECA · governance-gate plugin + decision-as-data · executor auto-discovery fold-in · audit transition taxonomy). draft≠review≠verify: `plan-drafter` authored → Code R2 → Cray OQ-1..4 as-rec (AskUserQuestion). **FIRST run under the #740 hardening CAUGHT OQ-4** (ADR-0025 D7's AT-2-generator CI marker was NEVER built, only the principal-identity mirror exists → armed as a Path-2 AC). Direction (Cray s130): the hero must GENERATE the governance (AT-2) not compose around it → **Path 2** (hand-author a 2nd AT-2 signature on a different vertical/seam → N≥2 → THEN the AT-2 generator, ADR-0025 D7; reframe: OQ-8's typed AT-2 sub-model is ALREADY BUILT by ADR-0025). Doc/config-only — no `services/` / tests, deterministic-offline (no MS-S1 / host-state); 0 open PRs. Full narrative: the Session-130 CF block above | `192dc52` (HEAD, #741 ADR-0031 Accepted) / `eea875f` (#740 drafter hardening) / `docs/adr/0031-core-lifecycle-architecture.md` + `.claude/agents/plan-drafter.md` (point-8 backstop) + `docs/lessons/0030-verify-fact-pack-before-drafter-newest-adr-resolves-oq.md` + `docs/research/private/2026-07-14-work-lifecycle-cores.md` (grounding, gitignored) |

## Rotated this reconcile (session-140 artifact-3 reconcile, 2026-07-16 — the CLAUDE.md §2 direction pointer landed, closing the 4-artifact strategic-continuity program 4/4, #773)

### Recent Decisions row removed — 2026-07-15 (s131 — PLAN-0074, the 2nd AT-2 signature: supply_chain cold-chain disposition + SeverityLadder, N=2) [rotated 2026-07-16, session-140 artifact-3 reconcile — 10-row RD window]

| 2026-07-15 | **s131 — PLAN-0074 (the 2nd AT-2 governed-procedure signature) shipped END-TO-END + CLOSED → `done/` in ONE session-131 day (#744, `feat`); reaches N=2 → de-risks the deferred AT-2 GENERATOR (ADR-0025 D7 / Rule-of-Three) via a supply_chain cold-chain excursion DISPOSITION whose authority is NON-MONEY — a `severity_tier` gate + `SeverityLadder` typed content (the 4th AT-2 gate kind; `DoaLadder` is money-typed by construction and cannot represent it)** — Steps 1-6 (spec / obligation gate / run path [resolver + dispatch + run-pin] / procedure+factory / two self-cancelling markers / red-team oracle + the AC-16 load-time `gate_kind`↔content correspondence check), then a **3-independent-reviewer adversarial harvest** (governance / correctness / test-honesty lenses) fixed **10 confirmed defects** (highlights: the facet-less "smuggled gate" — AC-16 closed only the CONTRADICTION half, not the dangerous OMISSION half, so a facet-less `governance_content` owed no SoD yet still gated at run; Infinity/NaN fail-DANGEROUS severity routing; a float-rounding crash on a real sub-0.005 °C breach; a KeyError that killed API startup; a degenerate lane set → dead-code criticality amplifier). Corrected the PLAN's own sketch: `SourcePolicy` is NOT extended (the run executor keys provenance on the member itself, so a 3rd member would invert a vertical's provenance). draft≠review≠verify: `plan-drafter` PLAN → Code R2 → Cray SD-1 (SeverityLadder) → build → 3-reviewer harvest → 10 fixes. Full offline suite **2674 passed / 7 skipped**; `mypy --strict` + ruff clean; deterministic-offline (no MS-S1 / host-state); 0 open PRs. **Follow-on F1** (Cray-ratified, spawn_task `task_053edc92`, separate session): the AT-2 authority ladder (`doa_tier` + `severity_tier`) RESOLVES/AUDITS which tier should act but the gate never ENFORCES the acting approver holds that role (a lower tier can resolve a higher-tier gate) — pre-existing AT-2-wide, touches the procurement hero, needs an ADR. PLAN-0074 `git mv`→`done/`. Full narrative: the Session-131 CF block above | `ff84d9a` (HEAD, #744 merge) / `34c09d6`·`bbe994f`·`d9ffa08` (Steps 1-3) / `7b38db6` (#743 PLAN-0074 Proposed) / `services/**` (severity_tier resolver + dispatch + run-pin · `SeverityLadder` · obligation gate · AC-16 correspondence check) + `verticals/supply_chain/**` (cold-chain disposition procedure + factory) + `tests/**` (red-team oracle + self-cancelling markers) + `docs/plans/done/0074-*.md` |

### Current Focus block removed — Session 136, 2026-07-16 (PLAN-0078 Phase 1 COMPLETE — the intake seed-migration pair #762/#763, oracle-first) [rotated 2026-07-17, session-141 PR-4 reconcile — 4-session CF window]

> **Session 136, 2026-07-16 (head_commit `7cbe08a` → `45d6b82`) — PLAN-0078
> Phase 1 COMPLETE (the intake seed-migration pair, oracle-first, SD-1=(B)
> arc): the intake enrichment migrated off the hand-coded seeds into declared
> `enrich` TRANSFORM steps (ADR-0031 D3 row-1 grammar), across two `feat` PRs
> atop a Step-1 uniform-factory landing.** **Step 1** (`d8707ca`, zero behavior
> change) — a shared `TransformStepExecutor` registered uniformly in all 4
> production factories. **PR-1 #762** (`173d869`, `feat(procurement)`) —
> procurement intake enrichment → a declared `enrich` transform (`criticality`
> copy + `unit` default + `compliance` map) across ALL 3 intake-bearing
> procedures (manual hero + scheduled + event). **PR-2 #763** (`45d6b82`, HEAD,
> `feat(supply_chain)`) — supply_chain disposition intake → an `enrich`
> transform (`excursion_magnitude_c` sub-derive + duration/budget defaults + GDP
> `compliance` map; `assess.input.from` re-pointed intake→enrich). **Each PR is
> oracle-first (L-2):** a hand-coded FROZEN parity reference proven green
> PRE-flip, then byte-equal POST-flip (or it does not land) — the enriched row +
> every governed verdict byte-identical (procurement ฿288,000 / ผจก.จัดซื้อ /
> appr-pm; supply_chain severity CRITICAL / ผอ.ฝ่ายคุณภาพ / appr-qdir); AC-4
> fail-closed + AC-5/AC-6 pin coverage per vertical. **Honest residual (NOT
> overclaimed):** the marquee severity/amount STAMPS stay code-side,
> `derivation_hash` in service, **F-PIN stays OPEN** — those are **Phase 2**
> (SD-1=(B): PR-3 severity re-sequencing + PR-4 amount re-sequencing + PR-5
> `derivation_hash` retirement + F-PIN marker rewrite + PLAN-0076 T2 closure,
> each SD-6 two-tier parity-guarded). **draft≠review≠verify:** Step 1 + both
> flips = Code authored + verified (oracle-first harnesses); PLAN-0078 =
> `plan-drafter` authored → Code R2 → Cray ratified all 8 SDs (s135); each phase
> PR = fresh Cray AskUserQuestion sign-off before merge; this reconcile =
> `status-scribe` → Code R2. Full offline suite **2802 passed / 7 skipped**;
> `mypy --strict` + ruff clean; deterministic-offline (no MS-S1 / host-state).
> Post-merge: main=`45d6b82`; 0 open PRs; loop-dispatcher DISABLED; MS-S1 idle;
> dev Postgres UP. Commits: `d8707ca` (Step 1 uniform factory) → `173d869`
> (#762 PR-1 procurement) → `45d6b82` (#763 PR-2 supply_chain, HEAD).

### Recent Decisions row removed — 2026-07-15 (s132 — PLAN-0075 Proposed #746 + the ADR-0026 D4 amendment, closing the F1 AT-2 authority-enforcement gap) [rotated 2026-07-17, session-141 PR-4 reconcile — 10-row RD window]

| 2026-07-15 | **s132 — GOVERNANCE / PLANNING batch (NO code; 2 docs PRs): PLAN-0075 Proposed (#746) + the ADR-0026 D4 amendment, closing the F1 AT-2 authority-enforcement gap** — an AT-2 authority ladder (`DoaLadder` / `SeverityLadder`) RESOLVES + AUDITS which tier/approver a spend or severity should route to, but the run gate never ENFORCED that the acting approver HOLDS that resolved tier role (a lower-tier approver could resolve a top-tier gate; the persisted audit even NAMED a non-actor); scope = the whole AT-2 axis (`doa_tier` on both procurement surfaces + `severity_tier` on supply_chain). **PLAN-0075 Proposed** (awaiting implementation scheduling): a pure `tier_authority` run-check ADDITIVELY beside `check_principal_sod` + gate-time actor-named audit + an F3 load-time gated-autonomy check + **AC-13** supply_chain derivation-provenance fold-in. **ADR-0026 D4 gains a 4th fail-closed condition** (Accepted, in-place, additive): the acting approver must hold the ladder-resolved tier role, or a declared-authority step with no persisted verdict fails closed. Ratified SDs: **SD-1** = exact-match + **rank-as-authored-data** (no engine `RoleId` rank primitive; cumulative roles in YAML) / **SD-2** = read persisted verdicts, satisfy EVERY verdict / **SD-4** = amend ADR-0026 D4 / **SD-6** = gate-time actor-named audit tie (OQ-5 shape preserved); + a derivation residual-risk caveat. **3-specialist SD-3/SD-5 review** (architect / security / governance-audit): **SD-3 = keep NARROW, confirmed** (orthogonal to the ADR-0031 D3 gate-plugin seam; the architect's binding condition = durably track the seam follow-on); **SD-5 = adjudicated SPLIT** (Cray) — FOLD IN supply_chain derivation-provenance NOW (AC-13, PROVENANCE-ONLY: hashes `_DOSE_LADDER` + `_TOP_SEVERITY` into the run pin = mid-flight tamper-evidence, NOT a new-run guarantee, **F-PIN NOT closed**), DEFER procurement's ฿ derivation to a follow-on bound to ADR-0031 D3 row-1. Three honesty corrections to the just-committed ADR/PLAN (a D4 over-claim; a wrong "cheap mitigation" note; the "different axis" framing → threat-tier). #747 = an interim Active-TODO tracker for the two Out-of-Scope follow-ons (F-PIN remainder + the ADR-0031 D3 seam) so they don't rot. draft≠review≠verify: `plan-drafter` authored → Code R2 (3 corrections) → Cray SD-1..SD-6 + the SD-5 split → 3-specialist review. Doc-only, deterministic-offline (no MS-S1 / host-state); 0 open PRs; PLAN-0075 stays Proposed in `docs/plans/`. Full narrative: the Session-132 CF block above | `098b0d9` (HEAD, #747 guardrail Active-TODO tracker) / `60ad2e3` (ADR-0026 D4 amendment) / `5598c02` (#746 PLAN-0075 Proposed + ratifications) / `docs/plans/0075-*.md` (Proposed) + `docs/adr/0026-*.md` (D4 4th fail-closed condition) |

### R2 terseness pass — 10 Recent Decisions rows trimmed to pointers [rotated 2026-07-17, session-141; originals below verbatim]

> The rows were trimmed to the R2 rule (*"pointers, not narratives: <= ~600 chars"*). Their full narratives also live in the Session-NNN Current Focus blocks (in STATUS for s137/s138/s140/s141; in this archive for s133/s135/s136). Originals preserved here per R4 (move, never drop).

| 2026-07-17 | **s141 — PLAN-0078 Phase 2 PR-4 COMPLETE (#775, `feat`, oracle-first): the marquee ฿ spend re-sequenced off the `_scored_rule` stamp into a declared `derive_spend` transform, per the ratified SD-8=(a) ONE DERIVATION HOME** — `_scored_rule` stops multiplying and stamps the two FACTORS; the transform multiplies them after all 4 shipped scored_rule steps (procurement ×3 + supply_chain `assess`). Oracle-first (L-2): `fc17d02` froze `test_amount_transform_parity.py` (12 tests, cross-vertical) GREEN pre-flip → `88e6e11` flipped, the SAME oracle green UNCHANGED; **non-vacuous by construction** (post-flip nothing stamps `amount` → a transform that failed to run would `KeyError`), anchored on the row the AUTHORITY GATE reads so it holds in either world. **A ratified-SD refinement, Cray-ratified in-session:** SD-8(a)'s "stamp `selected_unit_price` only — qty already rides the entity" was REFUTED by grounding — `_quantity` (`governance_step.py:128`) resolves `qty`→`quantity`→`1`, a fallback the grammar's `default` op cannot express (`spec.py:520-521`), so a bare-`qty` re-read is **fail-DANGEROUS not fail-closed** (silent ×1 on a `quantity`-only row → lower amount → LOWER doa_tier → under-approval; inert today); Cray ratified **stamp `selected_qty`** so `_quantity` stays the ONE resolution home and divergence is unrepresentable. **AC-9 proven by AST source-segment extraction + SHA256** (not by diff-absence — PR-4 edits `_scored_rule` in that same file); SD-6(ii) licensed the audit-form change. Also closed a PLAN-0075 AC-8 debt (the last plain-executor-bypass test) + a PR-3 docstring honesty gap. Suite **2822 passed / 7 skipped**; ruff clean; deterministic-offline. **PLAN-0078 stays `Status: Proposed`**; **PR-5 is NOT blocked by PR-4** (its dep was PR-3, landed). Full narrative: the Session-141 CF block above | `09714ea` (HEAD, #775 merge) / `88e6e11` (PR-4 flip) / `fc17d02` (PR-4 oracle) / `verticals/{procurement,supply_chain}/**` (declared `derive_spend` transform) + `services/engine/procedures/governance_step.py` (`_scored_rule` factor stamps) + `tests/**` (`test_amount_transform_parity.py`) + `docs/plans/0078-*.md` (Proposed; PR-4 COMPLETE) |
| 2026-07-16 | **s140 — artifact 3/4 (#773, docs-only): `CLAUDE.md` §2 retitled "Current Focus" → "Direction & Current Focus" + a two-pointer signpost — standing direction = ADR-0032, current state = STATUS, "state never overrides direction" (§1).** The strategic-continuity program is now **COMPLETE 4/4** (#770 ADR · #771 PLAN-0079 · #773 §2 · #772 STATUS pointer) — the direction now lives in 3 places that cannot silently vanish (the ADR read every session start · the STATUS TODO, guard-test RED if pruned · CLAUDE.md §2). Scope CUT at Cray's ratification: the planned sanitized strategy doc DROPPED (ADR-0032's own §"Public-repo boundary" already carries the public frame + path-only private refs; OQ-2 had already resolved "not yet" — restating a canonical without precedence is itself a drift surface, §1 / ADR-0017 D6). Cowork drafted the §2 text → Code R2 + applied (ADR-009 D1/D2). Suite **2810 passed / 7 skipped**. Full narrative: the Session-140 CF block above | `0523d88` (HEAD, #773 merge) / `038efd0` (§2 pointer) / `CLAUDE.md` §2 + `docs/adr/0032-*.md` |
| 2026-07-16 | **s140 — the 4-artifact STRATEGIC-CONTINUITY program CLOSED (3 PRs; docs + one guard test, ZERO behaviour change): ADR-0032 Accepted (#770) — the demo→pilot wedge + 3-shape roadmap + a BINDING pilot gate + the PINNED AT-2 fact record (N=2, marker re-arms at N=3) · PLAN-0079 `Status: Tracking` (#771) — the `building_materials` governed-credit HERO homed with its honest cost (AT-2 signature #3 → CI RED → obligates the ADR-0025 D7 re-eval; ADR-0032 D6: never a "cheap follow-on"), builds NOTHING · the s138 reconcile unblocked (#769, branch-update) · this AC-4 pointer** — the s137 arc lived only in auto-memories + gitignored private docs, so a parallel session planned BLIND and the HERO sat in NO backlog. draft≠review≠verify: `plan-drafter` → Code R2 → Cray ratified + merged; STATUS = `status-scribe` → Code R2. Suite **2809 passed / 7 skipped**; deterministic-offline. _[Artifact 3 landed as #773 — the §2 pointer only, the strategy doc CUT; see the row above.]_ Full narrative: the Session-140 CF block above | `8ca772b` (HEAD, #769) / `754a894` (#771) / `ad40aef` (PLAN-0079) / `4a5cfb7` (#770) / `5b53bbe` (ADR-0032) / `docs/adr/0032-*.md` + `docs/plans/0079-*.md` + `tests/services/engine/procedures/test_governed_credit_hero_tracking_guard.py` |
| 2026-07-16 | **s138 — PLAN-0078 Phase 2 PR-3 COMPLETE (#768, `feat`, oracle-first): cold-chain excursion SEVERITY re-sequenced off the `ColdChainAssessExecutor` stamp into a declared `enrich` transform (ADR-0031 D3 row-1) — `_DOSE_LADDER` becomes a governed datum IN THE PIN, the move that makes retiring `derivation_hash` honest in PR-5** — oracle-first (L-2): `8214a32` froze `test_severity_transform_parity.py` GREEN against the executor-stamped world (4 passed/1 skipped), then `e6fb07a` flipped + the SAME oracle stayed green unchanged (5 passed), proving the ratified **SD-6 two-tier bar**: (i) output-row byte parity (excursion_severity="critical" + criticality="1" + every Phase-1 field); (ii) semantic run-record equivalence (scored lane-licensed-destruction/63000.000 THB, GDP gate, severity_tier critical→ผอ.ฝ่ายคุณภาพ/appr-qdir, run status); (iii) VALUE-level provenance completeness (the ratified OQ-5 — dose_ch/ratio materialized so the record answers "why CRITICAL?" without re-running the pinned spec). **SD-7** = `ColdChainAssessExecutor` SLIMMED to its fail-closed scalar guard; **OQ-6** = EXTEND the enrich step (executor's call, PLAN-0078:801 — a separate step breaks the PLAN-0074 structural test at test_cold_chain_disposition.py:178); **AC-9 (L-6)** = `governance_step.py` absent from the diff (`_severity`/`_spend` byte-untouched). **Honest interim redundancy: `_DOSE_LADDER` / `derive_excursion_severity` / the derivation_hash provider stay in code until PR-5 — F-PIN stays OPEN, nothing records it closed.** draft≠review≠verify: Code authored + verified oracle-first (2 build findings recorded honestly: an AC-12 test passing vacuously → rewritten; severity_derivation row-stamped too → the flip removes both); Cray ratified OQ-5 + merged. Full offline suite **2808 passed / 7 skipped** (2803→2808 = +5 the new parity module, zero regressions); ruff + `ruff format` + `mypy --strict` clean; deterministic-offline (no MS-S1 / host-state). **PLAN-0078 stays `Status: Proposed`** (never flip-then-edit); PR-4 amount re-seq next. Full narrative: the Session-138 CF block above | `9a5eecf` (HEAD, #768 merge) / `e6fb07a` (PR-3 flip) / `8214a32` (PR-3 oracle) / `verticals/supply_chain/**` (declared `enrich` severity transform + slimmed `ColdChainAssessExecutor` guard) + `tests/**` (`test_severity_transform_parity.py` + 2 re-homed PLAN-0074/PR-2 tests) + `docs/plans/0078-*.md` (Proposed; PR-3 COMPLETE) |
| 2026-07-16 | **s138 — the AT-2 `N=1` misinformation-KILL + PLAN-0078 doc-drift reconcile (#767, docs-only, NO behavior change): s137's planned building_materials `doa_tier` as "the 2nd money signature (N=2) advancing AT-2" was a FALSE premise — corrected at the source** — grounded (next-work-analyst + 4 Explore agents, Code-reverified on disk): ADR-0025 D7 counts AT-2-class procedures with NO per-`gate_kind` partition → **N has been 2 since s131** (supply_chain severity_tier, PLAN-0074); the D7 re-trigger already FIRED + was ANSWERED (generator stays deferred, D2 types stay instance-scoped); the marker `test_at2_signature_retrigger.py:81` re-arms at **N=3** → a building_materials doa_tier would be signature #3, turning CI RED + OBLIGATING the AT-2 extraction, NOT "advancing toward" it. Root cause = stale code comments at `spec.py:822`/`:1046`/`:1092` ("AT-2 is N=1 … PROVISIONAL-UNTIL-N>=2", never updated by PLAN-0074 — the 2nd Lesson #0030 instance, this time a code comment the drafter point-8 backstop does NOT cover) + a `main.py:133` docstring; all corrected from the marker's OWN docstring (quoted, not inferred). Same PR reconciled PLAN-0078 doc-drift: 4 "Phase 2 gated on SD-6 ratification" body sections (all SD-1..SD-8 ratified 2026-07-15), Phase-1 AC-1..AC-4 ticked (AC-5/AC-6 NOT — their re-sequenced leg is Phase 2), drifted scored_rule anchors re-verified (procurement :196/543/878, supply_chain :264/:281), and **OQ-5 recorded RATIFIED by Cray 2026-07-16 via AskUserQuestion: (a) materialize**. draft≠review≠verify: Code authored + verified (every load-bearing claim Code-reverified on disk, caught 2 subagent errors); the finding came from next-work-analyst grounding; Cray ratified OQ-5. Deterministic-offline. **Flagged for follow-up:** `spec.py:816-820` "no principal/role-rank model exists yet" is suspect post-PLAN-0075 (a possible missed 580b9e8 truth-pass site). Full narrative: the Session-138 CF block above | `c9e5186` (#767 merge) / `120521e` (docs(procedures) comment/docstring truth-pass) / `9b19f19` (docs(plans) PLAN-0078 drift reconcile + OQ-5) / `services/**` (`spec.py` :822/:1046/:1092 + `main.py:133` corrected) + `docs/plans/0078-*.md` (Phase-1 ACs ticked, OQ-5 RATIFIED) |
| 2026-07-16 | **s137 — the 5th vertical `building_materials` scaffolded as a Tier-1 Mirror (ADR-0015 D2) for governed customer CREDIT (#765, `feat`), from a hand-authored GUESSED OCT-shaped ontology; + the latent `GET /procedures` 500 it exposed + fixed** — **the reshape is the point:** the monitored Asset is a COMMERCIAL entity (`CustomerAccount` + its own per-entity `credit_limit_thb` band), Site = a sales `Branch` (the ADR-008 "may extend" precedent procurement already uses) → the engine governs a **commercial** decision, not only a physical asset; strategically believed the intended **2nd `doa_tier` (money) signature** target advancing the AT-2 Rule-of-Three — but that lands with the HERO, not this mirror _[SUPERSEDED s138/#767: FALSE — AT-2 is N=2 since s131, marker re-arms at N=3, so this would be signature #3; the stale `spec.py:822` N=1 comment is corrected]_. **The bug (the real find):** `GET /procedures` looped `registry.verticals()` calling `load_procedures` UNCONDITIONALLY → `FileNotFoundError` 500 on the first discovered vertical shipping no `procedures.yaml`; `new-vertical` scaffolds exactly that (mirror tier: ontology + adapter + handlers, no spec) + ADR-0023 import-scan discovery registers it regardless → **the whole read surface died for EVERY other vertical the moment a mirror was scaffolded** (the 4 shipped verticals each hand-authored a spec, so none hit it). Fix = an EXPLICIT `procedures_path().exists()` skip (deliberately NOT a swallowed `FileNotFoundError` — a malformed spec still raises) + a self-cancelling guard that fires if building_materials ever gains a spec. **Scope honesty (NOT overclaimed): Tier-1 Mirror ONLY — no `procedures.yaml`, no governed-credit hero** (the 3-part spine — a deterministic exposure band + a hard KYC/overdue-AR `rule_gate` + `doa_tier`+SoD+audit — is the FOLLOW-ON and is what makes the governance real rather than a bare approval form; handler = the scaffold's `echo` stub, synthetic data = a demo draft, every ฿ a marked GUESS). PLAN-0078 Phase 2 UNTOUCHED (separate track). draft≠review≠verify: Code authored + verified (the ontology guess, the fix, the guard); Cray ratified the vertical choice + the fix approach + the merge; STATUS = `status-scribe` → Code R2. Full offline suite **2803 passed / 7 skipped** (2802→2803 = the new guard); ruff + `ruff format --check` + `mypy --strict services/` clean; live-verified end-to-end on the DETERMINISTIC rule path (map branch + the 250k→550k breach timeline; the trace `550000 >= 500000, crossed=true` + the human-approval gate) — no MS-S1 call, no host-state. Full narrative: the Session-137 CF block above | `c52c1ed` (HEAD, #765 merge) / `1d523a3` (scaffold + fix) / `verticals/building_materials/**` (guessed OCT ontology + adapter + `echo` handlers, no spec) + `services/api/**` (`GET /procedures` exists-skip) + `tests/**` (`test_procedures_skips_discovered_vertical_without_a_spec`) |
| 2026-07-16 | **s136 — PLAN-0078 Phase 1 COMPLETE (the intake seed-migration pair, oracle-first, SD-1=(B) arc; 2 `feat` PRs #762/#763 atop a Step-1 uniform-factory landing `d8707ca`): the intake enrichment migrated off the hand-coded seeds into declared `enrich` TRANSFORM steps (ADR-0031 D3 row-1 grammar)** — **PR-1 #762** procurement intake (`criticality` copy + `unit` default + `compliance` map, all 3 intake-bearing procedures) + **PR-2 #763** supply_chain disposition intake (`excursion_magnitude_c` sub-derive + duration/budget defaults + GDP `compliance` map; `assess.input.from` re-pointed intake→enrich). Each PR oracle-first (L-2): a FROZEN parity reference green PRE-flip → byte-equal POST-flip (enriched row + every governed verdict byte-identical: procurement ฿288,000/ผจก.จัดซื้อ/appr-pm; supply_chain CRITICAL/ผอ.ฝ่ายคุณภาพ/appr-qdir); AC-4 fail-closed + AC-5/AC-6 pin coverage per vertical. **Honest residual: the marquee severity/amount STAMPS stay code-side, `derivation_hash` in service, F-PIN stays OPEN** — Phase 2 (SD-1=(B): PR-3 severity + PR-4 amount re-sequencing + PR-5 derivation_hash retirement + F-PIN marker rewrite + PLAN-0076 T2 closure, each SD-6 two-tier parity-guarded). draft≠review≠verify: Step 1 + both flips = Code authored+verified (oracle-first); PLAN-0078 = `plan-drafter` → Code R2 → Cray ratified all 8 SDs (s135); each PR = fresh Cray AskUserQuestion sign-off; STATUS = `status-scribe` → Code R2. Full offline suite **2802 passed / 7 skipped**; `mypy --strict` + ruff clean; deterministic-offline (no MS-S1 / host-state). Full narrative: the Session-136 CF block above | `45d6b82` (HEAD, #763 PR-2 supply_chain) / `173d869` (#762 PR-1 procurement) / `d8707ca` (Step 1 uniform factory) / `verticals/{procurement,supply_chain}/**` (declared `enrich` transform seeds) + `tests/**` (oracle-first parity harnesses + AC-4/5/6) + `docs/plans/0078-*.md` (Phase 1 COMPLETE, Phase 2 open) |
| 2026-07-15 | **s135 close-out — PLAN-0077 "transform-grammar build" COMPLETE (5 PRs #754→#758: Proposed → Phase A → B → C → #758 L-8 landing); renders ADR-0031 D3 row-1 + ADR-016 Q4 OQ-3, NO new ADR (arc spans s134-135)** — the typed anti-eval `derive` transform grammar shipped, load-gated + execution-bound for the shipped op-set (`StepKind.TRANSFORM` + `transform_step.py`; a value-parity oracle reproduces `derive_excursion_severity` + `scored_rule`'s `amount = unit_price × qty` value-identically WITHOUT touching the hardened stamp path, SD-1; 93 AC tests). **Honest residual: the two verticals' seeds stay execution-bound ✖; the marquee stamps stay code-side (SD-1); `derivation_hash` in service; F-PIN stays OPEN** — flipping those = the separate SD-4 parity-guarded seed-migration PLAN (+ the PLAN-0076 Step T2 F-PIN fold-in). draft≠review≠verify: Phase A/B/C = Code authored+verified; PLAN-0077 + the L-8 Accepted-body edit = `plan-drafter` → Code R2 + committed; STATUS = `status-scribe` → Code R2. Full narrative: the Session-135 CF block above | `ece270a` (HEAD, #758 L-8 landing) / `8808902` (#757 C) / `d94a10d` (#756 B) / `e93e9d0` (#755 A) / `3e6ee4d` (#754 Proposed) / `services/engine/procedures/transform_step.py` + `docs/plans/done/0077-*.md` |
| 2026-07-15 | **s133 close-out — PLAN-0075 COMPLETE (all 13 ACs) + CLOSED → `done/`; AC-13 derivation provenance shipped (#751, `feat`); PLAN-0076 filed as the STANDING follow-on TRACKER (#752, `Status: Tracking`)** — **AC-13** hashes supply_chain `_DOSE_LADDER` + `_TOP_SEVERITY` into the run governance pin via a per-vertical `registry.derivation_hash` hook (optional `derivation_hash` threaded through the 5 pin call sites); **PROVENANCE-ONLY** (mid-flight tamper-evidence + which-derivation-governed-this-run — **F-PIN stays OPEN**); 9 offline tests. PLAN-0075 (core AC-1..AC-12 #749 + AC-13 #751) `git mv`→`done/`. **PLAN-0076** (Cray-ratified s133 4-specialist SD-1 panel) homes the 2 PLAN-0075 deferrals (F-PIN remainder + ADR-0031 D3 gate-plugin / F-FACTORY seam) with an **AC-6 presence guard-test** (`test_at2_followon_tracking_guard.py`, RED on a premature archive-to-`done/` or a pruned STATUS pointer — "location≠tripwire; failing tests are the real anti-rot"). Merge order: #752 (`4a682ab`) then branch-updated #751 (`fac77c7`), both gate-verified. draft≠review≠verify: AC-13 = Code authored+verified; PLAN-0076 = `plan-drafter` → Code R2 → Cray ratified the panel; STATUS = `status-scribe` → Code R2. Full narrative: the Session-133 close-out CF block above | `fac77c7` (HEAD, #751 merge) / `4a682ab` (#752) / `0520fb2` (AC-13 feat) / `docs/plans/done/0075-*.md` + `docs/plans/0076-*.md` + `tests/services/engine/procedures/test_at2_followon_tracking_guard.py` |
| 2026-07-15 | **s133 — PLAN-0075 core: AT-2 AUTHORITY ENFORCEMENT AT THE RUN GATE shipped (12/13 ACs, #749, `feat`); closes the s131-surfaced F1 exploit (`task_053edc92`)** — the AT-2 ladder (`doa_tier` / `severity_tier`) RESOLVED/AUDITED which tier should approve but no run path ENFORCED the acting approver HELD that role (a junior `appr-buyer`, ฿0-50k, could resolve the procurement hero's ฿288k / ฿2M gate; the audit even NAMED a non-actor). **Fix:** a pure `tier_authority.check_tier_authority` runs at `resolve_gated_step` AFTER the SoD check (ADDITIVE, SoD primary) and BLOCKS unless the approver holds EVERY persisted verdict's ladder-resolved tier role — verified at the LIVE DB gate (junior refused, senior approves-down governed). Plus an F3 load check (authority step must be GATED — AC-5), gate-time audit reconciliation naming who ACTED (SD-6a / AC-6), the AC-7 truth pass (7 over-claim sites corrected, grep zero), the blessing test re-harnessed (AC-8). **Two Cray-ratified divergences:** (1) CUMULATIVE roles in the shipped YAML OVERRIDE PLAN-0075's Correction 1 (Cray "senior approves downward", Policy B); (2) NATIVE-TIER routing (`native_approver`, Code-surfaced) keeps the audit routing on the tier's OWN approver (enforcement cumulative, routing native). ADR-0026 D4's 4th fail-closed condition already merged (#746, AC-12). draft≠review≠verify: `plan-drafter` authored (Proposed, s132) → Code built + R2 → Cray ratified the 2 divergences. Full offline suite **2692 passed / 7 skipped**; 251 DB+API tests pass; `mypy --strict` clean; live DB gate = evidence. **PLAN-0075 stays OPEN** (12/13 ACs); AC-13 (derivation provenance, `task_cbf139fe`) is the deferred follow-up = hash supply_chain `_DOSE_LADDER` + `_TOP_SEVERITY` into the run pin (5 sites, vertical-hook; PROVENANCE-ONLY, F-PIN NOT closed), then close → `done/`; F-PIN remainder + ADR-0031 D3 seam stay the #747 Active-TODO. Full narrative: the Session-133 CF block above | `76f42cc` (HEAD, #749 merge) / `580b9e8`…`9e3d421` (7 core build commits) / `services/**` (`tier_authority.check_tier_authority` + `resolve_gated_step` wiring + F3 load check + gate-time audit reconciliation) + `verticals/{procurement,supply_chain}/**` (cumulative-role YAML + `native_approver`) + `tests/**` (AC-5/6/7/8 + live DB gate) + `docs/plans/0075-*.md` (OPEN, 12/13 ACs) |

### R2 terseness pass — Active TODOs trimmed to pointers [rotated 2026-07-17, session-141; originals below verbatim]

> Cray ratified extending the R2 pointer rule to Active TODOs (session 141), with a carve-out: an item whose substance has NO tracked home is NOT trimmed. Each item below was verified as a duplicate of a tracked artifact before trimming. Left untouched by that carve-out: the s74 demo-card UX decision (SOLE HOME), Rock 4 (its evidence-asymmetry finding survives only in gitignored research), and the monotonic `sequence` column (4 deferral facts have no other home).

- [ ] **PLAN-0079 (`Status: Tracking`, filed #771, drafted s139 / merged s140) — the `building_materials` governed-credit HERO, homed WITH ITS HONEST COST; nothing is built, nothing is scheduled.** The 3-part spine (a deterministic exposure band + a hard KYC/overdue-AR `rule_gate` + `doa_tier`+SoD+audit) is what would make the s137 Tier-1 Mirror's governance REAL rather than a bare approval form. **The honest cost — stated without softening:** the hero is the **2nd *money* `doa_tier` signature** and therefore **AT-2 signature #3** → it **re-arms `test_at2_signature_retrigger.py`** → **CI goes RED** → it **OBLIGATES the ADR-0025 D7 re-evaluation**. Per **ADR-0032 D6 this is NEVER a config-cost item / a "cheap follow-on"** — that exact framing is what PR #767 had to KILL (the stale `spec.py` "AT-2 N=1" comments; N has been 2 since s131, the marker re-arms at N=3, and ADR-0032 now pins that fact record). It is equally **NOT "blocked"**, and **doing nothing is a real option**: the shipped `building_materials` Tier-1 Mirror is a **supported, tested end-state**, and **no test, no marker, and no commitment forces the hero** — only **Cray commissioning it (PLAN-0079 Step T1)** promotes it. **3 open SDs = Cray adjudications:** **SD-1** T1 ordering vs PLAN-0076 T1 · **SD-2** the exposure source (the drafter recommends an adapter-maintained `current_exposure_thb` balance field) · **SD-3** this STATUS pointer's timing — **RESOLVED by this PR**. **Guard:** PLAN-0079's AC-2 presence guard-test (`tests/services/engine/procedures/test_governed_credit_hero_tracking_guard.py`) turns CI **RED** on a premature archive-to-`done/` **or** a pruned STATUS pointer ("location≠tripwire; failing tests are the real anti-rot"). *(PLAN-0079 = #771, `Status: Tracking`; ADR-0032 = #770 — the strategic frame + the pinned AT-2 fact record; the s137 mirror = #765.)*
- [ ] **PLAN-0075 follow-ons — now homed by PLAN-0076 (`Status: Tracking`, filed #752, s133): the F-PIN remainder + the ADR-0031 D3 gate-plugin seam (guardrail against the ADR-0031 OQ-4 deferral-rot precedent — s133 4-specialist panel).** PLAN-0075 (the F1 AT-2 authority-enforcement gap: an AT-2 ladder RESOLVES/AUDITS the required tier but the run gate never ENFORCES that the acting approver holds that tier role — a lower tier could resolve a higher-tier gate; the persisted audit even named a non-actor) is now **COMPLETE — all 13 ACs (core AC-1..AC-12 #749 + AC-13 derivation provenance #751) — and CLOSED → `docs/plans/done/0075-*.md`** (with the **ADR-0026 D4(iv) amendment**: tier-authority enforced at `resolve_gated_step`, additive beside `check_principal_sod`; cumulative senior roles authored in YAML per Cray's Policy-B override; gate-time actor-named audit tie per SD-6). Two Out-of-Scope items — now tracked by **PLAN-0076**, no longer by PLAN-0075 — that must **NOT** rot: **(1) F-PIN remainder** — supply_chain's severity derivation (`_DOSE_LADDER` + `_TOP_SEVERITY`, `cold_chain_assess.py:71-77`) is provenance-hashed by PLAN-0075 AC-13 via a per-vertical `registry.derivation_hash` hook (**PROVENANCE-ONLY**: mid-flight tamper-evidence + which-derivation-governed-this-run; **NOT** a new-run guarantee — **F-PIN is NOT closed**), but procurement's imperative ฿ derivation (`unit_price × qty`) is still un-pinned; proper fix = **declare-the-derivation-as-data (ADR-0031 D3 row-1)** → the existing `governance_content` pin covers it for free, NOT a hand-rolled code hash. **(2) The ADR-0031 D3 gate-plugin seam (F-FACTORY)** — trigger has fired (PLAN-0074 = the 2nd AT-2 signature, D4.1 satisfied); folds in procedure-scoped `sod_steps` via a procedure-aware `ExecutorFactory` + the OQ-4 CI-marker check. **PLAN-0076** is the STANDING Tracking stub that homes both; its **AC-6 presence guard-test** (`test_at2_followon_tracking_guard.py`) turns the build RED on a premature archive-to-`done/` or a pruned STATUS pointer (the panel's "location≠tripwire; failing tests are the real anti-rot" finding — the architect's binding SD-3 condition, now enforced not just tracked). *(PLAN-0075 = #749/#751 → `done/`; PLAN-0076 = #752, `Status: Tracking`; ADR-0026 amendment `60ad2e3`; s133 4-specialist SD-1 panel.)*
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2; Q3 ADR Accepted + BUILD COMPLETE s93 — open only for the residues).** (1) **Q3 ontology data-binding — DONE end-to-end:** the ADR-016 D2+D3 amendment (Accepted s93, #505) is now **BUILT + CLOSED** (PLAN-0046 → `done/`; #511 feat `878b517` / #512 close `eb63692`, s93 cont. 2026-07-02): `StepInput.reads: list[str]` + `Agent.allowed.object_types` + the `validate_read_bindings` **LOAD-time consistency/scoping gate** (`reads ∈ ontology ∩ allowlist`, SD-1 Option A) wired at both production pre-flight sites; `reads` H-governed via `STEP_GOVERNANCE_FIELDS` + the `lift_to_step` draft-strip hardening; 12 new tests, offline suite 2066 passed / 5 skipped. v1 = a typed read contract + load-gate, **NOT** runtime-enforced parity — the declared==dispatched teeth for the read side then **SHIPPED as PLAN-0048** (the "Q4 generic run-consume query executor", `docs/plans/done/0048-q4-generic-query-executor.md`, s96, #533–#539; all 15 ACs, Complete 2026-07-04): an engine-owned deterministic `QueryStepExecutor` (`services/engine/procedures/query_step.py`) giving *plain declared reads* the **declared ✔ · load-gated ✔ · execution-bound ✔** frame + a typed auditable refusal (no silent `[]`). **The remaining Q4 residue** (the ADR + grammar build now DONE — only the migration PLAN remains): the four shipped verticals are NOT yet on the generic executor — their query steps encode projections/joins the spec could not yet declare (PLAN-0048 fact-pack 8 / LOCKED-9: hand-written seeds stay **execution-bound ✖** until migrated). The join/projection-grammar ADR is now **Accepted** (ADR-016 Q4 amendment, #659) + the grammar is **BUILT + CLOSED** (PLAN-0061, #664–#668) — a declaring step is execution-bound ✔ for the 2 v1 shapes; only **(b) the per-vertical production-factory + seed-migration PLAN** (Phase 3 = **PLAN-0062, COMPLETE — all 5 PRs, all 9 ACs → `done/`** — PR1 #672 parity core + PR1b #673 env-band executor/energy factory + PR2 #675 supply_chain + PR3 #676 aquaculture + PR4 #682 procurement shadow-parity/close-out) is DONE, having migrated the four verticals' hand-written seeds onto the grammar (all THREE OCT query steps — energy `read_readings`, supply_chain `read_temps`, aquaculture `read_do` — now execution-bound ✔ on the production HTTP path; procurement `intake` is declared-expressible ✔ under shadow parity but production execution stays the co-existing `_SeedQuery` ✖ for derived fields; `read_stock` deferred/labelled/reason-corrected — ERRATUM 2). (2) **Box 4 (Profit Formula) — BUILT + CLOSED (PLAN-0071, s127, #731/#732) + SURFACED IN THE HERO UI (PLAN-0073, s129, #737/#738); the Box-4 economic-impact ฿ facet is now COMPLETE across all 4 verticals AND surfaced in the Palantir-lite hero-demo UI (beat-4 ฿ carries the typed EconomicImpact facet + a provenance strip under the unchanged demo ledger).** N≥3 is MET (4 shipped verticals); ADR-0030 (Accepted s126, #728) TYPED and PLAN-0071 SHIPPED the economic-impact facet — advisory + trace-carried: an `economic_impact` `ReasoningStep` in `reasoning_trace` (`detail` = a producer-validated `EconomicImpact` model; ZERO ADR-007 D2 envelope change), ONE cross-vertical shape (`baseline` vs `governed` exposure → `net_benefit`) + per-vertical `kind` (avoided_outage / expedite_tradeoff / spoilage_avoided / mortality_avoided). Disclosed `was an error` (CLAUDE.md §6): the ADR-016-promised enforceable self-cancelling N≥3 marker test was NEVER built (a claim-vs-code gap caught by s126 manual grounding, NOT a mechanical trigger) — enforcement SHIPPED as the OWNED ≥3-vertical build-completion marker (AC-5, GREEN at N=4 in PLAN-0071: the `EconomicImpact` model + `economic_impact` emission at both `RecommendedAction` sites + four per-vertical ฿ producers). *(s84 strategy discussion + the 3-layer / ontology-binding diagram; Q3 ADR Accepted s93 #505; Q3 build complete + PLAN-0046 closed s93 cont. #511/#512; **Q4 executor SHIPPED = PLAN-0048 closed s96 #533–#539** [reconciled 2026-07-08]; **Q4 join-grammar ADR Accepted #659 + grammar built PLAN-0061 #664–#668** [reconciled 2026-07-09 s116] — **Phase-3 PLAN-0062 COMPLETE** [PR1 #672 + PR1b #673 + PR2 #675 + PR3 #676 + PR4 #682 → `done/`, reconciled 2026-07-10 s117]; **the per-entity `threshold_field` band arc (ADR-016 amendment) — FK-parent Rule-of-Three MET s123:** procurement same-row [PLAN-0066, s120] / supply_chain FK-parent [PLAN-0067, s121] / aquaculture FK-parent [**PLAN-0068** — `read_do`/`do_floor` now execution-bound + per-entity-banded, #715/#716, s123] / energy over-current FK-parent [**PLAN-0070** — `read_readings`/`rated_current_a`, judge env_band→threshold_field, the LAST shipped env_band consumer retired, #726, s125] all shipped → `done/` [reconciled 2026-07-13; energy s125]; the band-shape Rule-of-Three was already MET at N=3 s123 so energy is breadth-not-gate; **Box-4 facet DESIGNED — ADR-0030 Accepted s126 #728 [reconciled 2026-07-13]; Box-4 BUILT + CLOSED — PLAN-0071 #731/#732, AC-5 GREEN N=4 [reconciled 2026-07-14 s127]; Box-4 SURFACED IN THE HERO UI — PLAN-0073 #737/#738 [reconciled 2026-07-14 s129]**; the Box-4 economic-impact ฿ arc is now COMPLETE across all 4 verticals AND surfaced in the hero UI — this TODO's Box-4 leg is DONE, the residue is the Q4 procurement `intake` `_SeedQuery` derived-field co-existence (the O-2 open leg) + the O-2 data-binding trail above)*
- [ ] **Bounded/incremental chain verification (PLAN-0063 SD-4 follow-up, s118).** `GET /audit/verify` walks the WHOLE chain O(n) on demand — accepted at pilot scale and documented in the endpoint docstring. Future work = a checkpointed head / verify-since-anchor design; anchor storage ≈ external anchoring = **ADR-011 tripwire territory — do not build without re-reading the tripwire**. *(s118; #688/#690)*- [ ] **procurement ontology ↔ CSV column drift (PLAN-0062 close-out follow-up, s117).** The procurement ontology declares `PurchaseOrder.part_no` / `Quotation.price` / `OperationalEvent.equipment_id` while the real CSVs emit `part_id` / `price_thb` / `asset_id`; the load gate checks DECLARED properties while the executor merges RUNTIME keys (the AC-6 shadow-parity test renames four `PurchaseOrder`∩`Quotation` collisions to keep each quote's own supplier). Data/ontology evolution — explicitly **out of PLAN-0062's scope**. *(s117; PLAN-0062 PR4 #682)*
- [ ] **Standard partner-intake form (template candidate — Cray observation, s93 partner-sim run-1).** Generalize the 6-ask structure (+ the TWP package's §1–§10 answer shape as a SYNTHETIC-bannered worked example) into a stakeholder-facing standard intake form per vertical, so partners can prepare narrative context for vero-lite to generate workflow pipelines more accurately. Template lineage = the partner-facing ONE-PAGER (full taxonomy allowed for real partners), NOT the R1-clean variant (partner-sim-only screen). Pairs with the partner-trial-readiness discussion + ADR-016 Phase 2 intake. *(s93; ADR-0020 run-1)*

### R2 terseness pass (part 2) — 3 more Active TODOs trimmed to pointers [rotated 2026-07-17, session-141; originals below verbatim]

> The three the L1 loop-guard stopped the scribe from finishing in part 1. Same ratified rule + carve-out; each verified as a duplicate of a tracked artifact first. Two carried stale facts, corrected at the trim: **PLAN-002 never existed** ('NOT yet drafted', `docs/plans/done/0005-*.md:14`) and the **'>= ADR-014' floor is moot** (ADRs now run to 0032; `0014-WITHDRAWN.md` exists).

- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten (full table: PLAN-0005 §8.1): rule-based recommender → **ADR-010 ACCEPTED (2026-05-22) → PLAN-0006 next** (LLM reasoning hook); minimal approval gate → **ADR-011+** (audit framework — trigger: first design-partner data / PDPA review); no mapping layer → **dbt/SQLMesh** (trigger: first non-synthetic source); hand-authored ORM → **"ORM emitter"** Rule-of-Three candidate (trigger: 3rd vertical / DDL↔ORM parity-test drift); base Postgres only → **PLAN-002** (pgvector/AGE — trigger: semantic + graph features); explicit registry → **ADR-006 D3 L2** (trigger: vertical #2/#3 or `new-vertical` generator). *(per Cray note 2026-05-21)*
- [ ] **ORM-emitter per-vertical layout (B1-DP-1 follow-up; Cray-deferred s67).** B1 (PLAN-0031, #370) ships the ORM emitter writing energy's ORM to the **committed** `services/db/models.py` (via `code_generator._ORM_COMMITTED_DEST`) — the gitignored `verticals/<ns>/generated/` cannot host a runtime dependency. When a **2nd vertical needs its own ORM** (the Rule-of-Three trigger), decide the per-vertical layout: extend `_ORM_COMMITTED_DEST` to per-vertical committed modules **vs** un-ignore a per-vertical `generated/orm.py` (gitignore negation) + re-export. Premature to design now (one ORM today). *(Cray-deferred 2026-06-18)*
- [ ] **ADR-NN (TBD, ≥ ADR-014) + PLAN-002** — Custom Postgres image with extensions (ADR-011 earmarked for the audit framework, ADR-012 taken, ADR-013 taken by autonomy axis relocation; floor bumped from ≥0013 to ≥0014 on 2026-05-23 per ADR-013 T6)

### R2 terseness pass (part 3) — the Rock 4 TODO, trimmed only AFTER its finding was rehomed [rotated 2026-07-17, session-142; original below verbatim]

> Rock 4 was one of the **three items s141's R2 pass left byte-untouched under the ratified carve-out** ("an item whose facts live *nowhere else in git* — or only in **gitignored** `docs/research/private/` … — is **not a duplicate**, and is **left at full length until it is rehomed**"). Its central finding — **the evidence asymmetry** — survived only in the gitignored research note; the archive at `:1460` preserves only the METHOD (~48 sources, vendor-vs-independent tagged), **not** the finding.
>
> **The carve-out is DISCHARGED here, not waived.** The finding was **first** rehomed into `docs/adr/0025-at2-managerial-layer.md:23-29` — a public-repo-safe statement of the asymmetry **plus** the 3-tag provenance taxonomy that is the sharp part of it (`[VENDOR-CLAIM]` / `[VENDOR-COMMISSIONED]` / `[INDEPENDENT]`; the middle tag is the trap — an "independent author" is **not** independent evidence when the funding is the vendor's and the "customer" is a modeled composite), with the private research cited **by path only** per the ADR-0032 public-repo boundary. ADR-0025 is **Accepted**, so an Accepted-body edit is **G1-gated for Code**: `plan-drafter` authored it → Code R2'd (verifying the fact-pack on disk **first** — the drafter trusts it 100%) → Cray ratified the `session 142` provenance stamp via AskUserQuestion. **Only then** was this TODO trimmed. ADR-0025 was the right home because it already records the **same s84 research** and the **same O-sequence** at `:19`, and is the ADR that acted on that research.
>
> **Also dropped at the trim:** the `[[reference_rock4_4box_palantir_demo_research]]` token — a **dangling** reference to a private Tier-0 auto-memory that resolved **nowhere** in the repo (a repo-wide grep hit only this STATUS line itself). Replaced by the tracked ADR-0025 anchor, which now genuinely holds the content the token was gesturing at.

- [ ] **Rock 4 — Cowork deep research DELIVERED → O-sequence locked, O-1 done, O-3 Accepted (s84).** The 4-box + Palantir + agentic research landed (`docs/research/private/2026-06-28-rock4-4box-palantir-agentic-research.md`; ~48 sources, vendor-vs-independent tagged, adversarially balanced; central finding = the evidence asymmetry [bullish ROI all vendor, independent mostly skeptical]) → Cray **locked O-1 → O-3 → O-2 → O-4**. **O-1 (Box-4 ฿ pitch artifact) DONE** (conservative ฿ + impact-ledger mock; `docs/strategy/private/2026-06-28-box4-roi-spine-impact-ledger-pitch.md`). **O-3 = ADR-0025 Accepted** (see Rock 2). **Remaining:** **O-2** (economic-impact facet + Q3 ontology data-binding = Rock 3, after N≥3) · **O-4** (agent-interop North-Star, vision only). [[reference_rock4_4box_palantir_demo_research]]. *(s84 Cray ask)*

### R2 terseness pass (part 4) — the monotonic `sequence`-column deferral, rehomed then trimmed [rotated 2026-07-17, session-142; original below verbatim]

> _[Renumbered part 3 → part 4 at merge (s142): PR #780 (Rock 4) landed first and took "part 3". This section's content is unchanged — the collision was two parallel s142 sessions discharging different carve-out items under the same numbering, not a disagreement.]_
>
> The **third of the three s141 carve-out items**, now released from the carve-out. At s141 this item was left byte-untouched because four of its facts lived **nowhere else in git** — the ROOT-fix framing, the needs-a-migration/own-PLAN sizing, the "unchanged by design → the deferral STANDS" verdict, and the DISPLAY-ONLY tolerability argument. The guard test's docstring carried the HAZARD (mechanism, #678 history, scope/limits) but never the words `sequence`, `migration`, or "own PLAN": it explained what it guards, not why the root fix was deferred.
>
> Session 142 **rehomed all four facts first** — into `tests/services/db/test_load_run_ordering_guard.py`'s module docstring (the natural home: a reader hitting the guard is exactly who needs to know the root fix was deferred and why) — plus a one-line pointer back to the guard at each of the two wall-clock code sites (`services/engine/procedures/persistence.py` `suspended_step_result`, `services/api/routers/runs.py` `list_runs`). **Only then** was the STATUS item trimmed to a pointer, per the R2 carve-out's own precondition ("trimmed **only after** verifying its substance has a tracked home").
>
> One stale fact corrected at the rehome: the original's `services/api/routers/runs.py:200` line-ref had rotted — the `order_by(PipelineRun.started_at.desc())` now sits at `:205`. The rehomed text anchors to the **expression** rather than a line number, so it cannot rot the same way again. Ordering behaviour is **unchanged** — this was a docstring/comment-only pass; the deferral explicitly stands.

- [ ] **DEFERRED: a monotonic `sequence` column on `step_results` (s117 flaky-DB track carry-over; needs a migration → own PLAN).** #678 fixed the resume/GET-run path to read the suspended step by STATUS, but two wall-clock orderings remain — `load_run` (`services/engine/procedures/persistence.py`) + the run-list `order_by(PipelineRun.started_at)` in `services/api/routers/runs.py:200` — both **DISPLAY-ONLY** now, so not urgent. **#684 closed the TESTS half of the same invariant** — six positional `step_results[-1]` reads that misread `load_run`'s wall-clock order — and a static AST guard (`tests/services/db/test_load_run_ordering_guard.py`) now prevents that class of regression; but `load_run`'s wall-clock `ORDER BY created_at` is **unchanged by design**, so **the deferral STANDS**: a monotonic per-run sequence column would remove the hazard at its ROOT rather than guard against it. It needs a DB migration, so it deserves its own PLAN (PLAN-0062-independent). *(s117; #678/#680/#684)*

### Rehome — the s74 demo-card carve-out RELEASED, then trimmed [rotated 2026-07-17, session-142; original below verbatim]

> The s141 R2 pass left this item **byte-untouched** under the ratified carve-out: its substance had **no tracked home** — `ADR-0030` cited **STATUS itself** (`STATUS.md:262`) as the authority for the decision in six places, and `PLAN-0035` still recorded the question as **OPEN** (SD-3: "Phase-2 reconsiders a first-class field"; Step 11: "Reconsider the first-class `verification` field"). The decision that ANSWERS that open question therefore lived nowhere in git except this volatile TODO.
>
> **s142 released the carve-out in the order the rule requires — rehome → re-point the citers → verify → trim:**
> 1. **Rehomed** into `docs/plans/done/0035-governed-action-verify-reshape-build.md:576` — a dated **post-archival amendment** at **SD-3**, the very question this decision answers (§"Surfaced decisions (SD-N)"), with pointers at Step 11 (`:445`) and the header SD-box (`:23`). Precedent for amending an archived PLAN: `414e564` / `done/0008-*.md:593-618` (dated, labelled, original preserved, verdict unchanged).
> 2. **Re-pointed all six `ADR-0030` citations** (D1 rationale, D5, Alternative 1, OQ-3, References) off `docs/STATUS.md:262` onto that amendment — an Accepted-ADR body edit, so authored by `plan-drafter`, Code R2-reviewed. The `docs/STATUS.md:256` **Rock-3** references were deliberately left alone (Rock-3 is a live concern with no tracked home yet — Cray scoped it out).
> 3. **Only then** trimmed the TODO to a ~600-char pointer per R2.
>
> Two defects motivated the re-point, both recorded in the runbook's R2 corollary: an ADR citing volatile Tier-1 state **inverts §1** (STATUS is state, never a rule), and any `STATUS.md:<line>` anchor **rots by construction** — this one was written at `:262` and had already drifted to `:319`.

- [ ] **Demo card UX — "trust shape", NO operator confidence badge (s74 design, Cray-approved).** For the next demo round's operator recommendation card: show **what / grounded-why / approve gate** + a **"show full reasoning trace" toggle** that reveals the engine-view (where the floor-vs-judge agreement lives, labelled *audit/QA — not the operator*; reuses the scene-6 why-toggle pattern). **No operator-facing confidence badge** — the floor-vs-judge `confidence_signal` (PLAN-0035 Phase 2) is an **engine-internal QA/audit signal kept trace-only (SD-3 option A)**; surfacing it as a badge mis-reads as "the action might be wrong" (it is **not** — member (b) is advisory, never changes the action). The **(B) first-class `verification` envelope field is NOT needed for the operator UI** — reconsider **only** if a future internal audit/QA dashboard wants confidence as a first-class field (trace stays sufficient otherwise). Settled via a show_widget design review (s74; Cray: "ตรงใจ ตอบโจทย์"). The reframe: users want *what was decided · is it right · why* — answered by the action + grounding (real entity, allow-listed handler, deterministic detection, human approve) + the reasoning trace, **not** a self-reported confidence number. *(Trigger: the next demo / UI round; pairs with any (B) reconsideration.)*
