---
last_updated: 2026-07-12T23:52:14+07:00
session: 121
current_batch: "s121: FK-parent threshold_field shipped end-to-end (ADR-016 amendment #707 → PLAN-0067 Ready #708 → PR1 engine #709 + PR2 vertical #710); supply_chain cold-chain judge now bands each shipment vs its OWN temp_ceiling; suite 2544/7"
current_actor: code
blocked_on: "Nothing blocking. main=670117c; PLAN-0067 closed to done/ this batch; 0 open PRs; tree clean (pre-existing untracked .claude/ files); MS-S1 idle; dev Postgres UP."
next_action: "No PLAN active after PLAN-0067 closes. Candidates: remaining ADR-016 TF-2 extension — new-column per-class bands for supply_chain/aquaculture (a future ADR-016 amendment; the FK-parent-column case TF-2(i) is now DISCHARGED, shipped supply_chain-only this batch, energy FK-parent adoption still open); procurement ontology↔CSV column drift (needs a design decision); monotonic sequence column on step_results (S–M, no ADR); hero-demo dossier (needs its own ADR); PLAN-0063 SD-4 bounded verification (ADR-011 unwritten, partner-gated)."
head_commit: 670117c
recent_commits: [670117c, 0b6be2a, 83cbb39, a24971c, 4c05ecd, e3debdd, 1c296a4, 7e54a34, 7e04ce8, 101d122]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

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

> **Session 118, 2026-07-11 (head_commit `22242e4` → `2694253`) — PLAN-0063
> audit-chain verification surface (trust dossier object ③, first product
> surface) COMPLETE in one window: drafted + ratified (#687, SD-1..6 as-rec)
> → PR1 `GET /audit/verify` (#688) → PR2 monitor "Verify chain" panel (#689)
> → closed, all 8 ACs → `done/` (#690).** `verify_chain()` (PLAN-0047 Step 5)
> gains its FIRST production caller: **#688** exposes a typed
> `ChainVerificationReport` with SD-2(d) SPLIT VISIBILITY — the verdict is
> open, verbatim break detail is credentialed via the new
> `get_optional_principal` seam in `services/api/auth.py` (OQ-1 =
> `/audit/verify`); **#689** renders it as an ON-DEMAND monitor panel
> (`view-monitor.js?v=c34`, off the poll timers). `services/db/audit_log.py`
> + `alembic/` byte-unchanged (AC-8 pins verified). **Evidence bar:** #690's
> required CI `gate` = **2506 passed / 8 skipped in 93.5 s** (FULL suite
> incl. DB-backed tests via the CI postgres:16-alpine service) on code
> identical to `main=360007a` plus the docs close-out; local on the merge
> commit ruff + ruff-format + mypy --strict clean (the LOCAL pytest degraded
> to 2391/123-skipped — dev Postgres DOWN, dockerd off — recorded as NOT the
> bar). **TWO DISCLOSED DEFERRALS** (in the close-out, not silent): (1) the
> merge-commit LOCAL full-suite re-run and (2) the Step-5 render check —
> both blocked on the dev Postgres; starting dockerd = §8 host-state
> awaiting explicit Cray go; erratum-if-fail when the render check runs.
> SD-4 follow-up (bounded/incremental verification) → Active TODO.
> **CONTINUATION (same session, afternoon batch — `next-work-analyst`
> ranking delivered; Cray picked "Router + hygiene"; every pick/ratification
> below = Cray via AskUserQuestion):** (1) **Both disclosed deferrals
> DISCHARGED — `confirmed — prior intact`, no erratum.** Cray gave the §8
> go; Docker Desktop restarted, `vero-postgres` (volume
> `vero-lite_postgres_data`) up. The Step-5 render check PASSED its
> pre-committed strings: the monitor "Verify chain" panel rendered "chain
> intact · 36 rows verified" over the REAL dev-DB audit chain (36 rows,
> breaks []), DOM-asserted + screenshot; the withheld leg is not reachable
> on this deployment (dev box opts out of authn via `.env`) and stays
> pinned by the AC-6 pytest matrix. Local full suite on main WITH Postgres
> = **2507 passed / 7 skipped** (supersedes the 2391/123 degraded run). (2)
> Orphan test DB `vero_lite_test_69fa7362` DROPPED (Cray-approved §8) after
> fresh re-verification: sha256-hashed ALL 16 existing checkout-path forms
> (main + 7 worktrees × POSIX/UNC) — none maps to `69fa7362`; only the live
> `vero_lite_test_bb36873b` remains → the s117 housekeeping TODO fully
> discharged. (3) **PLAN-0064 "per-step QUERY router for procurement"
> READY (#692)** — `plan-drafter`-authored, Code R2 re-verified every
> load-bearing citation on disk (accept); **SD-0..SD-5 ratified as-rec**:
> SD-0 no ADR-016 amendment (executor supply is "not an engine contract",
> 0016:511-513; the STOP tripwire stands) / SD-1 declaration-presence
> dispatch / SD-2 engine-module home (`query_router.py`) / SD-3
> `read_stock` only / SD-4 tripwire test rewritten in place / SD-5 declared
> reads served by the registry-registered `ProcurementSyntheticAdapter`.
> Reopens PLAN-0062 AC-7 per ERRATUM 2 by its own ACs. (4) **Hygiene
> (#693):** PLAN-0004 (Phases A+B shipped; Phase C optional → backlog) +
> PLAN-0012 (vero-bridge Phase 1 shipped + live; AC-1/AC-2 ticked as
> bookkeeping; Phase 2 stays unminted) filed to `done/`; **PLAN-0010
> deliberately NOT closed** — Cray asked for an ELI-CRAY brief before the
> close-vs-park decision (delivered in-session; decision pending). NEXT:
> build PLAN-0064 (un-gated Code build, one PR).
> **CONTINUATION 2 (same session — PLAN-0064 went draft [`plan-drafter`] →
> Code R2 → Cray SD ratification → build → close in ONE session-118 day):**
> (1) **PLAN-0010 CLOSED "shipped + intentionally disabled" → `done/`
> (#695)** — Cray-ratified after the ELI-CRAY brief (AskUserQuestion);
> AC-1/AC-3/AC-5 ticked against `tests/loop/` + the 427-message production
> run (2026-05-26→06-25); AC-2/AC-4/AC-6 left unticked HONESTLY (closed by
> operational decision over the s76 drift hazard, NOT full AC discharge —
> they become requirements of any revival PLAN); companion chore fixed the
> stale `tools/loop/__init__.py` "(future) dispatcher" docstring. (2)
> **PLAN-0064 BUILT (#696) + CLOSED, all 8 ACs → `done/` (#697)** —
> `QueryStepRouter` (declaration-presence, SD-1) in
> `services/engine/procedures/query_router.py` + 5 unit pins; the
> production procurement factory routes per step: declared `read_stock`
> (`reads: [Part]`, PLAN-0048 single-read) → the SHIPPED
> `QueryStepExecutor` over the REGISTRY-registered
> `ProcurementSyntheticAdapter` (SD-5); undeclared `intake` → the
> co-existing `_SeedQuery` byte-identically (PLAN-0062 SD-C carried).
> ERRATUM-2 tripwire test rewritten IN PLACE per its own contract (SD-4);
> SD-0 honored — zero orchestrator/registry/spec change, the STOP tripwire
> never fired; the L-4 governance-pin consequence disclosed in the PR body.
> Suite **2512/7 local WITH Postgres**. **Honest frame (LOCKED-9 style —
> nothing claims more):** procurement `read_stock` = declared ✔ ·
> load-gated ✔ · **execution-bound ✔ on the production factory path**;
> `intake` unchanged (declared-expressible ✔ per 0062 AC-6, production
> execution = the co-existing seed, derived fields ✖);
> `low_stock_reorder_round` END-TO-END = **still not production-runnable**
> — `judge_stock` reads `measured_value`, raw Part rows don't carry it
> (PLAN-0064 fact 9 → Active TODO); **PLAN-0062 AC-7's deferral is
> DISCHARGED by reference** (no 0062 line edited).

> _Rotation note (session-120 reconcile, 2026-07-12, `docs(status):`):
> frontmatter bumped to `head_commit 3682d79`; a new s120 Current-Focus block
> was PREPENDED. **NORMAL reconcile** (file ~52 KB, comfortably under the 64 KB
> R1 ceiling — no size pressure): Current Focus now holds **s120 + s119 + s118
> (3 sessions, within the 4-session window)** — nothing rotated out of Current
> Focus. Recent Decisions rotated its OLDEST row (2026-07-09 PLAN-0060 reactive
> judgment handler catalog) to keep the 10-row window; that row was emitted
> verbatim in the reconcile reply for the caller to append to
> `docs/status-archive/2026-h1-status.md` (Bash-side). The prior session-119
> DEEP-rotation note (whole session-117 CF + the session-116 hygiene block + the
> 2026-07-08 PLAN-0059 RD row, all archived at the s119 reconcile) is
> consolidated into this one (R4). Per the STATUS.md Rotation Policy (R1/R2/R4)._

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
| 2026-07-12 | **s121 — per-entity FK-parent `threshold_field` (ADR-016 "per-entity bands v2") shipped END-TO-END (amendment → PLAN-0067 Ready → PR1 engine → PR2 vertical) in ONE session-121 day; supply_chain cold-chain `judge` now bands each shipment vs its OWN per-cargo `temp_ceiling` instead of one blanket env ceiling (#707/#708/#709/#710)** — **#707 ADR-016 amendment (Accepted 2026-07-12):** FK-parent-column `threshold_field` (a `threshold_field` may name a column on a JOINED FK-parent of the traced query step; FKP-1..FKP-4, SD-1..SD-5, SD-4 = supply_chain-only build), discharging TF-2(i); **Code R2 caught + corrected the dispatch's "executor deferred Phase C" premise** (it had shipped in PLAN-0061 #666). **#708 PLAN-0067 Ready:** SD-1 = (b) TWO PRs (a Cray divergence isolating the DB-migration / first-join-consumer rollback), SD-2 = (b) demo-visible seed flip, SD-3 rendered ceilings, SD-4 = (a) keep env-band wrapper + guard, SD-5 = (a). **#709 PR1 (engine):** FKP-2 gate widening (`_validate_threshold_field_bindings` domain reads[0] → base + joined FK-parent, in `orchestrator.py`) + a draft-discovered `env_band_step.py` delegate-guard fix (a migrated `threshold_field` judge delegates untouched — no clobbered direction, no false `band_source: env`) + a stale-docstring fix + `spec.py` reword; 6 new engine tests. **#710 PR2 (vertical):** `Shipment.temp_ceiling` + per-cargo seeds (8/12/-15/6) + a frozen warming reading (SD-2b) + `read_temps` as the FIRST shipped `join:` consumer + the `judge` env_band → threshold_field migration; **RED-verified flip** — the frozen shipment warms to −11.8 °C → `ok` under a blanket 8 °C ceiling but `breach` under its own −15 °C ceiling (hold set 1 → 2). **Build-discovered correction:** NO Alembic migration — supply_chain has no committed ORM/DB table (energy-only), so `temp_ceiling` is in-memory only (Cray-ratified Option A). THREE draft≠review≠verify catches, one per role (Code R2 stale-docstring premise / `plan-drafter` env_band guard coupling / build AC-3 no-shipment-table). Suite **2544/7** WITH Postgres (baseline 2536 + engine 6 + vertical 2); ruff + `mypy --strict` clean; CI `gate` green on every PR; no MS-S1 / host-state — pure offline; PLAN-0067 closing to `done/` in a sibling `docs(plans)` PR. Full narrative: the Session-121 CF block above | `670117c` (HEAD, #710 PR2 vertical merge) / `0b6be2a` / `83cbb39` / `a24971c` / `4c05ecd` / `e3debdd` (the s121 #708 Ready / #709 PR1 engine / #710 PR2 vertical + PLAN-0067 close commits — merge↔content pairing inferred from order) / `1c296a4` (#707 ADR-016 amendment merge) / `7e54a34` (#707 amendment) / `services/engine/procedures/{orchestrator.py,env_band_step.py,spec.py}` + `verticals/supply_chain/{ontology/supply_chain_v0.yaml (`Shipment.temp_ceiling`),procedures.yaml (`read_temps` `join:` + `judge` env_band→`threshold_field`),data_adapter/synthetic.py (per-cargo seeds 8/12/-15/6 + frozen warming reading)}` (+ regenerated `generated/**`) + `docs/adr/0016-governed-procedure-engine.md` (per-entity FK-parent `threshold_field` amendment) + `docs/plans/done/0067-*.md` |
| 2026-07-12 | **s120 — `threshold_field` per-entity band shipped END-TO-END (ADR-016 amendment → PLAN-0066 Ready → build) in ONE session-120 day; procurement `judge_stock` now bands each `Part` vs its OWN `reorder_point` (#703/#704/#705)** — **#703 ADR-016 amendment (Accepted 2026-07-11):** per-entity `threshold_field` on evaluate steps, **same-row v1** (TF-1..TF-4, OQ-1..OQ-4), discharging PLAN-0065 SD-3's deferral; **Code R2 caught + fixed the TF-1 exactly-one → at-most-one defect BEFORE ratification.** **#704 PLAN-0066 Ready** (SDs ratified a/a/a/b — SD-4=(b) added a flip seed part so the LIVE demo shows the per-part win a blanket threshold misses). **#705 build:** `threshold_field` grammar (`spec.py` at-most-one validator) + per-entity band executor (`evaluate_step.py`, SD-1a `_entity_number`) + TF-3 load gate (`orchestrator.py` trace-to-reads, c1–c4) + governance pin (`draft.py`) + procurement migration (both `judge_stock` → `threshold_field: reorder_point`) + SD-4(b) flip seed part `part-vbelt-03`; **build-discovered coupling fixed** — `draft.py::derive_governance_todo`'s band obligation is now threshold_field-OR-threshold. THREE draft≠review≠verify catches, one per stage (R2's exactly-one→at-most-one #703 / the drafter's SD-4 seed-parity #704 / the build's `draft.py` governance coupling #705). Suite **2536/7** WITH Postgres (baseline 2516/7); ruff + `mypy --strict` clean; no host-state action; PLAN-0066 closing to `done/` in a sibling `docs(plans)` PR. Full narrative: the Session-120 CF block above | `3682d79` (HEAD, #705 build merge) / `3047386` / `57e5e08` / `40ce172` (the three #705 build commits) / `525c028` (#704 PLAN-0066 Ready merge) / `f1b7157` (#704 Ready) / `1c9a9af` (#703 ADR merge) / `758610e` (#703 amendment) / `services/engine/procedures/{spec.py,evaluate_step.py,orchestrator.py,draft.py}` + `verticals/procurement/procedures.yaml` (`judge_stock` `threshold_field: reorder_point`) + `verticals/procurement/**` (SD-4(b) flip seed `part-vbelt-03`) + `docs/adr/0016-governed-procedure-engine.md` (per-entity `threshold_field` amendment) + `docs/plans/0066-*.md` |
| 2026-07-11 | **s119 — PLAN-0065 calm-path reorder runnability BUILT (#700) + CLOSED → `done/` (#701); procurement `low_stock_reorder_round` now runnable END-TO-END; drafted→ratified→built→closed in ONE session-119 day (#699 Ready, `plan-drafter`-authored)** — **SD-2 fix (shipped Q4 grammar, ZERO engine-code change):** `read_stock` gained a `project: {fields: {stock_qty: measured_value}}` rename-projection so the shipped `EvaluateStepExecutor` bands the registry-registered adapter's `Part` rows — the production factory chain used to CRASH at `judge_stock` (raw `Part` rows carry `stock_qty`, the judge reads `measured_value`); **PLAN-0064 fact-9 DISCHARGED**. Three new tests prove runnability at three depths: production-factory chain (`test_calm_path_production_runnability`, red-verified vs the unedited YAML), manual-run HTTP (`test_calm_path_run_endpoint` — `POST /procedures/{id}/run` parks at the reorder gate, identity server-resolved), and a NEW scheduled sibling `scheduled_low_stock_reorder_round` on the PLAN-0055 scheduler (fires headless, parks at reorder). **SD-5(b) Cray-ratified AGAINST the drafter's rec:** the scheduled sibling carries `owning_person_id: req-planner` (verified ACCEPTED at execution — no validator couples it to SoD, this AT-3 path has no SoD, so it is the run principal not an SoD requester). Both paths park at ONE human go/no-go (RF-1/RF-3). **SD-3 (per-part reorder-point band) DEFERRED** — trips the L-4 tripwire (the shipped judge takes a single scalar threshold, not a per-entity field reference) → own ADR-016-amendment PLAN. PLAN-0064 shadow-parity assertion updated for the projection (routing unchanged, output projected — disclosed). Suite **2516/7** local WITH Postgres (2512/7 + 4 new); no host-state action; `docs/plans/` EMPTY again. Full narrative: the Session-119 CF block above | `06e5f39` (HEAD, #701 close-out merge) / `22a89fd` / `75696c5` / `eaf8b03` / `bfa8a36` / `5ab424a` (the six s119 commits — #699 Ready / #700 build / #701 close; merge↔content pairing inferred from order) / `verticals/procurement/procedures.yaml` (`read_stock` `project` + `scheduled_low_stock_reorder_round`) + `tests/verticals/procurement/` (`test_calm_path_production_runnability`, `test_calm_path_run_endpoint`) + `docs/plans/done/0065-*.md` |
| 2026-07-11 | **s118 CONTINUATION 2 — PLAN-0010 CLOSED "shipped + intentionally disabled" (#695) / PLAN-0064 per-step query router BUILT (#696) + CLOSED all 8 ACs → `done/` (#697); draft→R2→SD-ratify→build→close in ONE session-118 day** — #695: Cray-ratified (AskUserQuestion) after the ELI-CRAY brief; AC-1/AC-3/AC-5 ticked (tests/loop/ + the 427-message production run), AC-2/AC-4/AC-6 HONESTLY unticked (operational close over the s76 drift hazard — they become revival-PLAN requirements). #696: `QueryStepRouter` (declaration-presence, SD-1) routes the production procurement factory per step — declared `read_stock` → the SHIPPED `QueryStepExecutor` over the registry-registered `ProcurementSyntheticAdapter` (SD-5); undeclared `intake` → `_SeedQuery` byte-identically; ERRATUM-2 tripwire rewritten in place (SD-4); SD-0 zero engine change; **PLAN-0062 AC-7's deferral DISCHARGED by reference**; `low_stock_reorder_round` end-to-end still NOT production-runnable (fact 9 → Active TODO). Suite **2512/7** local WITH Postgres. Full narrative: the Session-118 CF block above | `869a56d` (#697 merge) / `9a0eb7d` / `fdd6a9b` (#696 merge) / `75ed717` / `0b784f7` (#695 merge) / `3bdef0d` / `services/engine/procedures/query_router.py` + `verticals/procurement/hero_demo/run.py` + `verticals/procurement/procedures.yaml` + `tests/verticals/procurement/test_intake_shadow_parity.py` + `docs/plans/done/0064-per-step-query-router-procurement.md` + `docs/plans/done/0010-phase3-5-scheduled-task-autonomy-loop.md` |
| 2026-07-11 | **s118 CONTINUATION — PLAN-0063 deferrals DISCHARGED (`confirmed — prior intact`, no erratum) / #692 PLAN-0064 Ready / #693 hygiene / orphan DB dropped (session 118 cont.)** — Step-5 render check PASSED its pre-committed strings over the REAL dev-DB audit chain (36 rows, breaks []; DOM-asserted + screenshot) + local full suite WITH Postgres **2507/7** (supersedes the 2391/123 degraded run); `vero_lite_test_69fa7362` DROPPED (Cray §8; all 16 checkout-path hash forms re-verified, only the live `bb36873b` remains); **PLAN-0064** (per-step QUERY router for procurement) `plan-drafter`-authored, Code R2 accept, **SD-0..SD-5 Cray-ratified as-rec**, reopens PLAN-0062 AC-7 per ERRATUM 2; PLAN-0004 + PLAN-0012 → `done/` (PLAN-0010 deliberately NOT closed — close-vs-park = Cray decision pending after the s118 ELI-CRAY brief). Full narrative: the Session-118 CF block above | `2694253` (#693 merge) / `e8cba64` (#693 docs) / `f494013` (#692 merge) / `b7e6e40` (#692 Ready) / `docs/plans/0064-per-step-query-router-procurement.md` + `docs/plans/done/{0004,0012}-*.md` |
| 2026-07-11 | **PLAN-0063 audit-chain verification surface COMPLETE (all 8 ACs) → `done/` — trust dossier object ③'s first product surface (session 118; #687/#688/#689/#690)** — #687 Ready (`plan-drafter`-authored, SD-1..6 Cray-ratified as-rec); #688 PR1 `GET /audit/verify` → typed `ChainVerificationReport`, `verify_chain()`'s (PLAN-0047 Step 5) FIRST production caller, SD-2(d) split visibility (verdict open / verbatim break detail credentialed via the new `get_optional_principal`; OQ-1 = `/audit/verify`); #689 PR2 on-demand monitor "Verify chain" panel (off the poll timers); #690 close-out with TWO DISCLOSED DEFERRALS (local merge-commit full-suite + Step-5 render check — dev Postgres down, §8 Cray go pending, erratum-if-fail). `services/db/audit_log.py` + `alembic/` byte-unchanged (AC-8 pins). Suite **2506/8** via the required CI `gate`. Full narrative: the Session-118 CF block above | `7e87d76` (#690 merge) / `576a201` (#690 close) / `360007a` (#689 merge) / `ceee552` (#689 feat) / `9d02686` (#688 merge) / `b41e3f5` (#688 feat) / `ec2250e` (#687 merge) / `e2c65f0` (#687 Ready) / `services/api/routers/audit.py` + `services/api/models/audit.py` + `services/api/auth.py` (`get_optional_principal`) + `tests/api/test_audit_verify.py` + `services/api/static/assets/view-monitor.js` + `docs/plans/done/0063-audit-chain-verification-surface.md` |
| 2026-07-10 | **Residual flaky-suite fix — the TESTS half of #678's wall-clock invariant (session 117; #684, `fix(test)`)** — a ~1-in-3 full-suite flake on `main` (two procurement DB tests), NO code cause (#683 docs-only), green in isolation. SAME non-monotonic WSL2 `datetime.now(UTC)` as #678 on the OTHER side of the seam: `load_run` still `ORDER BY created_at`; #678 migrated only the PRODUCTION consumers to `suspended_step_result()`, leaving SIX TEST sites on `step_results[-1]` → under a backward step `[-1]` names the wrong (completed) step. Fixed by intent: 4 demo sites → `suspended_step_result()`, 2 latent → select by `step_id` (a status-assert would be circular), + 2 order-asserting sites now compare `sorted(...)` (a round-trip preserves a step SET, not an order). Cover: a non-vacuous AST guard (`test_load_run_ordering_guard.py`, reports EXACTLY the six pre-fix sites) + a deterministic clock-inversion pin. NO production code changed; `pytest -q` 5x pre-merge + 3x on the merge commit (CI PR-only) = eight consecutive greens, 2499/7 (was 2496 + 3 new); ruff clean, offline, MS-S1 untouched. | `22242e4` (#684 merge) / `0a9542a` (#684 fix) / `tests/services/db/test_load_run_ordering_guard.py` + `tests/services/db/{test_event_procurement_demo.py,test_scheduled_procurement_demo.py}` + `tests/services/engine/procedures/{test_procedure_persistence.py,test_write_ahead.py}` |
| 2026-07-10 | **Flaky-DB-test isolation track — one intermittent `test_procedure_headline` failure = TWO unrelated bugs, one PRODUCTION (session 117, a CONCURRENT Code track; #678/#679/#680)** — **#678 (a) production correctness:** WSL2 `datetime.now(UTC)` is NON-MONOTONIC (2 backward steps / 20 s, −555 ms worst); `load_run` orders step results by that wall-clock `created_at` and `resume_run`/`GET /runs/{id}` read `step_results[-1]` as the suspended step → a run straddling the jump resumed from an already-COMPLETED step (re-ran a decided gate, dup side effects, stuck `waiting_human`; or "undecided proposals"); ~1 process in 20. Fixed by selecting the suspended step by **STATUS** (`suspended_step_result()`); gate/resolve never affected (looks up by caller `step_id`). **(b) test isolation (deterministic):** `Base.metadata` is import-populated → a `tests/services/db`-only process never registered `action_identity`, so `drop_all` left it for the next `alembic upgrade head` (`DuplicateTableError`); the full suite hid it. Fixed with `alembic/env.py`-mirroring registration imports + `DROP SCHEMA public CASCADE` per test. **#679:** that reset made concurrent sibling-worktree `pytest` wipe each other → test DB scoped per checkout (`vero_lite_test_<8-hex repo root>`), explicit `TEST_DATABASE_URL` still wins so CI is unaffected; control experiment (shared DB → both fail; scoped → both pass). **#680:** the "exactly one unresumed step" invariant was documented but unenforced → two such rows now raise; `get_run` answers **409** not an unhandled 500; + the HTTP-surface regression test #678 left owing. Suite 2473/7 → **2488/7**, verified on the merge commit (CI here is PR-only); ruff+format+mypy clean; offline, MS-S1 untouched, dev DB unchanged. Carry-overs → Active TODOs. | `9a12087` (#680 merge) / `7afff6a` / `8b617b0` (#679 merge) / `4f018bf` / `47a58ed` (#678 merge) / `a4593c8` / `b4b042c` / `services/engine/procedures/persistence.py` + `services/api/routers/runs.py` + `tests/db_support.py` |
| 2026-07-10 | **PLAN-0062 (Q4 Phase-3 per-vertical seed migration, parity-guarded, SD-C) — COMPLETE, all 9 ACs → `done/` (sessions 116–117; #671/#672/#673/#675/#676/#682)** — **#671 Ready** (`docs/plans/0062-*.md`): plan-drafter-authored, Code R2-verified facts 3/5/7, **SD-1..SD-6 Cray-ratified as-rec** (AskUserQuestion). **#672 PR1 (parity core, s116):** energy `read_readings` → the DECLARED latest-per-group grammar (`reads:[OperationalEvent]` + `where:{event_type:reading}` + `project:{latest_per:event_emitted_by_asset, order_by:occurred_at}`) + the shared `assert_read_step_parity` harness (grammar == an INDEPENDENT hand-coded SD-5 reference, ZERO tolerance) + SD-5-edge fixtures + a 4-vertical load-gate pin; suite 2458/7. **#673 PR1b (s117):** `EnvBandEvaluateExecutor` (binds `OCT_RECOMMEND_THRESHOLD`/`_DIRECTION` onto a band-less step, delegates to the SHIPPED `EvaluateStepExecutor`) + deterministic `advisory_stub.py` + `register_energy_procedure_executors` + `main.py` per-vertical registrar table → energy `read_readings` now **execution-bound ✔ on the production HTTP path**. **#675 PR2 (s117):** supply_chain `read_temps` over `event_concerns_shipment` + `verticals/supply_chain/procedures_factory.py`; parity harness went vertical-parameterised (SD-3); reused PR1b's `EnvBandEvaluateExecutor` + `advisory_stub_factory` UNCHANGED (same `env_band` judge, only the threshold differs — 8 °C cold-chain vs energy's 90 °C); OQ-2 settled against the data (`where:{event_type:reading}` load-bearing); suite 2473/7. **#676 PR3 (s117):** aquaculture `read_do` over `event_emitted_by_pond` + `verticals/aquaculture/procedures_factory.py` (the `main.py` registrar table's 4th/final entry); binds the shipped `EvaluateStepExecutor` UNWRAPPED (judge is `in_file_band` typed `threshold 4.0/below/watch_margin 1.0`; a test asserts `EnvBandEvaluateExecutor` is ABSENT — the `env` half of the ADR-016 D2-A3 split). All THREE OCT query steps now execution-bound ✔; procurement `intake` is declared-expressible ✔ (shadow parity, PR4) but production execution stays the co-existing `_SeedQuery` (✖ for the derived fields); `read_stock` deferred/labelled/reason-corrected. ADR-016 D2-A4 honored (env band selected by the FACTORY). **PR4 (#682, `bd8e586` → merge `359555b`):** AC-6 intake shadow-parity over the REAL `FastenalCsvAdapter` (declared join half == `_intake_seed`'s fields, derived fields ABSENT; four `PurchaseOrder`∩`Quotation` column collisions renamed to keep each quote's supplier); AC-7 `read_stock` deferral KEPT, its "no substrate" reason CORRECTED to per-`StepKind` executor routing (ERRATUM 2, Cray-ratified, pinned by an executable invariant test) → PLAN-0062 **COMPLETE (all 9 ACs)**, both errata (ERRATUM 1 = AC-5 "shipped executors" vs PR1b's `EnvBandEvaluateExecutor`; ERRATUM 2) recorded in the Close-out, `git mv`→`done/`; suite **2496/7 on the merge commit**. Both errata DISCLOSED, not silently reinterpreted. Un-gated Code build (PLAN-0062 §6); offline (SD-6), MS-S1 untouched. Full narrative: the Session-117 CF block above | `359555b` (#682 PR4 merge) / `bd8e586` (#682 feat) / `a711927` (#676 PR3 merge) / `c17500a` (#676 feat) / `624b731` (#675 PR2 merge) / `b9c5ebd` (#675 feat) / `ea08e54` (#673 merge) / `f41da9c` (#673 feat) / `8641cb3` (#672 merge) / `d9e4bd2` (#672 feat) / `66beb17` (#671 merge) / `833676e` (#671 Ready) / `services/engine/procedures/{env_band_step.py,advisory_stub.py}` + `verticals/{energy,supply_chain,aquaculture}/procedures_factory.py` + `services/api/main.py` + `tests/services/engine/procedures/test_seed_migration_parity.py` + `tests/verticals/procurement/test_intake_shadow_parity.py` + `docs/plans/done/0062-per-vertical-seed-migration.md` |
| 2026-07-09 | **PLAN-0061 join/projection-grammar build COMPLETE (all 8 ACs) → moved to `docs/plans/done/` — the ADR-016 Q4 amendment RENDERED: a query step now DECLARES multi-read equi-join enrichment + latest-per-group projection as typed authored spec — declared ✔ load-gated ✔ execution-bound ✔ for the 2 v1 shapes (session 115; #664/#665/#666/#667/#668)** — the un-gated Code build of the Ready PLAN (§6 "Steps execute directly"); ALL offline/deterministic, NO live run (SD-6 — MS-S1 never touched); every PR green through the required CI `gate`; **full suite 2452 passed / 7 skipped, ruff + mypy clean.** Chain: **#664** the SD-D substrate (`JoinKeyMeta` + ONE shared parser; `foreign_key` no longer dropped at load; `join_path` → typed) → **#665** the SD-1 lean `JoinSpec`/`ProjectSpec` schema + H-governance pin (a mid-flight edit fails CLOSED at resume) + the structural load gate (`validate_read_bindings` `meta=`; WARN-first on/fuse overrides, OQ-4) → **#666** compile + execute (`JOIN_SHAPE_VIOLATION`, OQ-1; `plan_read` `meta=` = ONE decision surface; `QueryStepExecutor` SD-1 pinned pipeline, D-N2 extended; single-read path byte-identical) → **#667** both shapes e2e over the REAL energy + procurement ontologies (SD-3 fixtures, zero vertical-file change; DB-backed JSONB-safety + governance-hash round-trip) → **#668** Ready → Complete → `done/`. The 4 shipped verticals' hand-written seeds stay execution-bound ✖ until the Phase-3 parity-guarded migration PLAN (SD-C). Full narrative: the Session-115 CF block above | `5a264d6` (#668 PLAN-COMPLETE move-to-done) / `66896e8` (#668 merge) / `e04a00b` (#667 Step 4 feat) / `0d738e1` (#666 Step 3 feat) / `93e01d1`+`7fb7497` (#665 Step 2) / `978caca` (#664 Step 1 feat) / `services/engine/ontology_meta.py` (`JoinKeyMeta` + shared parser) + `services/engine/procedures/{spec.py,orchestrator.py,query_step.py}` + `docs/plans/done/0061-join-projection-grammar-build.md` |
## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13; guarded trial (parallel to ADR-012) — verdict **continue-with-adjustments**. Run 1 (energy, s93) + Run 2 (supply-chain, s94) both COMPLETE, S-checks all PASS against pre-committed oracles, no R-PS trigger fired; C-1..C-3 CONFIRMED → **no open partner-sim debt**. ADR-011 audit stays gated on a REAL partner conversation (R3: SYNTHETIC provenance INFORMS but never TRIGGERS it). Full record: `docs/adr/0020-*.md` + the gitignored run packages `docs/research/private/2026-07-02-partnersim-run{1,2}-*.md`. _(Full prior narrative — the ~8 schema-mismatch findings, both run details, cross-run synthesis — archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **Procurement vertical — GO + SHIPPED (PLAN-0036 Fastenal, Stage 1):** 4th vertical greenlit (s75); PLAN-0036 drafted + merged Draft (#412, `7a7c036`; SD-1…SD-5 confirm-all). Demo target = Fastenal Thailand (auto-parts / EEC); **hero** = asset-failure → governed emergency sourcing, **calm-path** = low-stock reorder. Stage 1 = a PLAN-only pure-config plugin on the ADR-016 engine (zero `services/` core edit; CQ-1 / ADR-0023). **Pitch** = asset-ontology-triggered governed sourcing (native ontology ADR-008 + engine ADR-016), NOT the commoditized "governed"/"cross-vertical" claims. Full record: `docs/plans/0036-*.md` + the s72 de-risk dossier `docs/research/private/2026-06-22-procurement-*.md` (5 files: spec-expressiveness, GTM, asset-aware incumbent scan, AI-sourcing teardown, platform-incumbent deepdive). _(Full prior narrative archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2; Q3 ADR Accepted + BUILD COMPLETE s93 — open only for the residues).** (1) **Q3 ontology data-binding — DONE end-to-end:** the ADR-016 D2+D3 amendment (Accepted s93, #505) is now **BUILT + CLOSED** (PLAN-0046 → `done/`; #511 feat `878b517` / #512 close `eb63692`, s93 cont. 2026-07-02): `StepInput.reads: list[str]` + `Agent.allowed.object_types` + the `validate_read_bindings` **LOAD-time consistency/scoping gate** (`reads ∈ ontology ∩ allowlist`, SD-1 Option A) wired at both production pre-flight sites; `reads` H-governed via `STEP_GOVERNANCE_FIELDS` + the `lift_to_step` draft-strip hardening; 12 new tests, offline suite 2066 passed / 5 skipped. v1 = a typed read contract + load-gate, **NOT** runtime-enforced parity — the declared==dispatched teeth for the read side then **SHIPPED as PLAN-0048** (the "Q4 generic run-consume query executor", `docs/plans/done/0048-q4-generic-query-executor.md`, s96, #533–#539; all 15 ACs, Complete 2026-07-04): an engine-owned deterministic `QueryStepExecutor` (`services/engine/procedures/query_step.py`) giving *plain declared reads* the **declared ✔ · load-gated ✔ · execution-bound ✔** frame + a typed auditable refusal (no silent `[]`). **The remaining Q4 residue** (the ADR + grammar build now DONE — only the migration PLAN remains): the four shipped verticals are NOT yet on the generic executor — their query steps encode projections/joins the spec could not yet declare (PLAN-0048 fact-pack 8 / LOCKED-9: hand-written seeds stay **execution-bound ✖** until migrated). The join/projection-grammar ADR is now **Accepted** (ADR-016 Q4 amendment, #659) + the grammar is **BUILT + CLOSED** (PLAN-0061, #664–#668) — a declaring step is execution-bound ✔ for the 2 v1 shapes; only **(b) the per-vertical production-factory + seed-migration PLAN** (Phase 3 = **PLAN-0062, COMPLETE — all 5 PRs, all 9 ACs → `done/`** — PR1 #672 parity core + PR1b #673 env-band executor/energy factory + PR2 #675 supply_chain + PR3 #676 aquaculture + PR4 #682 procurement shadow-parity/close-out) is DONE, having migrated the four verticals' hand-written seeds onto the grammar (all THREE OCT query steps — energy `read_readings`, supply_chain `read_temps`, aquaculture `read_do` — now execution-bound ✔ on the production HTTP path; procurement `intake` is declared-expressible ✔ under shadow parity but production execution stays the co-existing `_SeedQuery` ✖ for derived fields; `read_stock` deferred/labelled/reason-corrected — ERRATUM 2). (2) **Box 4 (Profit Formula) — STILL DEFERRED (N≥3, unchanged).** The reasoning trace is operational, not economic — tie each action to ฿ impact (avoided outage / margin / ROI). Prepare by capturing the economic dimension as prose when hand-authoring verticals + proving the ฿ framing in the demo; type an economic-impact facet only after **N≥3** verticals triangulate it (the ADR-016 Q3 amendment left it a self-cancelling N≥3 marker). *(s84 strategy discussion + the 3-layer / ontology-binding diagram; Q3 ADR Accepted s93 #505; Q3 build complete + PLAN-0046 closed s93 cont. #511/#512; **Q4 executor SHIPPED = PLAN-0048 closed s96 #533–#539** [reconciled 2026-07-08]; **Q4 join-grammar ADR Accepted #659 + grammar built PLAN-0061 #664–#668** [reconciled 2026-07-09 s116] — **Phase-3 PLAN-0062 COMPLETE** [PR1 #672 + PR1b #673 + PR2 #675 + PR3 #676 + PR4 #682 → `done/`, reconciled 2026-07-10 s117]; TODO stays open ONLY for the Box-4 facet)*
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
