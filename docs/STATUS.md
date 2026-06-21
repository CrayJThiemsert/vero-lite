---
last_updated: 2026-06-22T01:36:38+07:00
session: 72
current_batch: 'session-72 — PLAN-0034 (G2 drafting-friction root-fix) FULLY COMPLETE — Step-5 prong-2 scope annotation merged (#399, `.claude/autonomy-triggers.md`) + PLAN flipped Ready→Complete + `git mv` to done/ (`72f0deb`). Optional live gold re-score deferred (Cray-gated host-state, NOT an acceptance gate). Next = A1.'
current_actor: code
blocked_on: 'Nothing blocks Code — the PLAN-0034 close PR (`72f0deb`) is in flight (Cray reviews + merges, hook-adjacent; Code does not self-merge), no Code dependency.'
next_action: 'A1 (ADR-0022 member (b) verify+reshape — a PLAN, not a new ADR; G2-gated → Cowork-dispatch; A2 residual = the 5 correct-action "assessment-prose" cases). Optional Cray-gated live gold re-score (host-state, prong-1 behavioral proof — NOT an acceptance gate). Standing backlog: PLAN-0005 §8.1 revisit register; Phase D (#3b next-vertical refresh, light Cowork).'
head_commit: 72f0deb
recent_commits: [72f0deb, 0f56d24, 5daa0e0, fde6713, 1917a6e, 9092db5, c69b6e2, 3dcecaa, 5705b8a, 71ace01]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 72 (current; head_commit `72f0deb`) — **PLAN-0034 (G2
> drafting-friction root-fix) FULLY COMPLETE.** The two-prong fix that has
> dogged sessions 63/66/67/68 is now closed end-to-end. **Step-5 prong-2 scope
> annotation (#399, annotation `5daa0e0` / merge `0f56d24`):** the
> `.claude/autonomy-triggers.md` registry annotation (SD-3 = (a), PLAN-only —
> **no ADR amendment**) was **Cowork-drafted** (ADR-009 D1, via the K-1/K-2
> scratchpad workflow). When a Stop-hook surfaced a "proceed with editing"
> auto-dispatch, **Code declined the Code-direct override** and Cray confirmed
> the **Cowork-drafts convention route** — Cowork authored the full file, Code
> applied the edits and cross-checked them **byte-identical** to Cowork's
> output, then committed (D2). **PLAN-0034 → Complete + archived (`72f0deb`):**
> Code flipped **Status: Ready for execution → Complete** and
> `git mv docs/plans/0034-*.md → docs/plans/done/` (the close PR is in flight —
> Cray reviews + merges; Code does not self-merge). The prong-2 *code* itself
> shipped earlier in #397 (s71); this session only lands the registry
> annotation + the lifecycle close. **Residual (non-blocking):** the optional
> **live gold re-score** (prong-1 behavioral proof) stays **Cray-gated
> host-state — NOT an acceptance gate** (the offline gate is the sole
> acceptance condition; it was green at #397). **Group-A sequencing:** A2 ✅ →
> **G2 (PLAN-0034) ✅ FULLY COMPLETE** → **A1** (ADR-0022 member (b)
> verify+reshape — a PLAN, **not** a new ADR; G2-gated → Cowork-dispatch;
> A2's residual = the 5 correct-action "assessment-prose" cases) is next. AI-assisted
> (Claude Code, session 72); no `Co-Authored-By` per CLAUDE.md §7.

> **Session 71 (current; head_commit `c69b6e2`) — Group-A: **G2 root-fix
> PLAN-0034 RATIFIED + core-IMPLEMENTED** (#396/#397).** PLAN-0034 (G2
> drafting-friction root-fix) went **Draft → ratified → core-implemented** this
> session. **Ratification (#396, `5705b8a`, merge `3dcecaa`):** Cray ratified all
> four surfaced decisions = option **(a)**. **SD-1** (prong-2 mechanism) was gated
> on a **Code Step-3 spike** run offline this session, which empirically confirmed
> (Q1) project-level PreToolUse hooks **DO** fire inside a subagent context (so the
> deadlock is real, prong 2 is needed) and (Q2) the PreToolUse payload carries
> **both `agent_id` and `agent_type` reliably** in this Claude Code version (the
> official hooks docs omit them — the live harness provides them, vindicating
> `done/0009` §1). So **SD-1 = (a)** exempt `agent_type == "plan-drafter"` reusing
> G5's `_is_subagent_call`/`agent_id` pattern (this **SUPERSEDED** the pre-spike
> (c) narrow-to-main-agent lean); **SD-2 = (a)** hybrid guards; **SD-3 = (a)**
> PLAN-only + a `.claude/autonomy-triggers.md` annotation (no ADR amendment);
> **SD-4 = (a)** keep G5 / PR-review / "only Code commits" untouched. Cowork folded
> the ratification + spike into the PLAN (ADR-009 D1); Code R2-reviewed + committed
> (ADR-009 D2); the PLAN flipped to **Status: Ready for execution**.
> **Implementation (#397, `c69b6e2`, merge `9092db5`):** the offline, deterministic
> core. **Self-modification of the autonomy hooks — Cray-approved per-diff
> in-session; opened as a PR and NOT self-merged (Cray merged it)** — that
> PR-review boundary is the **SD-4 checkpoint**. **Prong 2:**
> `pretooluse_classifier_dispatch.py` exempts the `plan-drafter` subagent
> (short-circuit before `_classify()`; main-agent writes have no `agent_id` so G2
> is preserved; `main()` carries a justified `# noqa: C901`). **Prong 1:** three
> DISPATCH over-fire negative guards in `_sonnet_classifier._build_system_prompt`
> (non-`docs/(adr|plans)/NNNN` target / already-routed / existing-lifecycle-flip; a
> genuine `Status: Accepted` ADR mutation still pauses — **G1 unchanged**). Gold: 6
> `expected: pause` negatives added to `benchmarks/stop_classifier/gold.yaml` (the
> s67 ratify-flip, the s68 CLAUDE.md mis-type, and the 3 live s71 Stop-hook
> over-fires). Tests: prong-2 deterministic AC-7 tests. **Offline gates green:**
> 137 targeted + 730 handoffs/benchmark tests pass, ruff + ruff-format +
> mypy --strict clean, gold parses. **Offline-only (no host-state); the live gold
> re-score (prong-1's true behavioral proof) stays Cray-gated host-state — NOT
> run.** The session also **exercised the very over-fire** prong-1 fixes: the
> Stop-hook over-fired ~4× around PLAN-0034 (dispatch after Cowork chosen /
> re-dispatch / "new ADR while unratified" / "draft final PLAN-0034" while already
> routed) — Code declined each per the override clause; these are now gold
> negatives. **PLAN-0034 stays Status: Ready for execution** (NOT Complete, NOT
> `git mv`'d) — two tails remain: (a) the **Cowork** `.claude/autonomy-triggers.md`
> registry annotation (Step 5 / SD-3 PLAN-only; Cowork drafts, Code commits) → then
> PLAN → Complete + `done/`; (b) the optional Cray-gated **live gold re-score**.
> **Group-A sequencing:** A2 ✅ → **G2 (PLAN-0034) ratified + core-implemented**
> (Step-5 tail remains) → **A1** (verify+reshape = ADR-0022 member (b); a PLAN, not
> a new ADR) is next. AI-assisted (Claude Code, session 71); no `Co-Authored-By`
> per CLAUDE.md §7.

> **Session 71 — Group-A: **A2 CLOSED** + **G2
> root-fix PLAN-0034 committed as DRAFT** (#394); earlier this batch PLAN-0033
> Phase C **COMPLETE** (C1+C2 MERGED #387, s70) + **Step-6 closeout**.** Phase C
> ships the **full 7-scene story-mode arc** on the proven C0 spine, merged to main
> (#387, merge `d7ae465`, **session 70**): **C1** — scene **1 Hook**, scene **2
> Govern-with-fail-safe-self-catch**, scene **4 live-intake dual-path**, scene **5
> Before/After** — plus **C2** — scene **6 Breadth**, scene **7 Appendix**.
> **Architecture:** a **SCENES registry + generic shell** with a **two-tier Motion
> scope** (shell-level + per-scene) enforcing the **AC-13 teardown contract**; the
> additive `view-story.js` **overlay** (SD-C — coexists with Views A–E, never
> replaces) on **synthetic Tier-1 mirror data** (ADR-0015 D1), **no new backend**,
> **offline/no-CDN**. On-screen copy **localised to English**; **offline IBM Plex
> fonts vendored** (#388); a **`?v=` static-asset cache-bust** added (the
> stale-asset trap). **Two scenes iterated live (Cray review):** scene **6** → a
> **swap-in-place** (one engine shape, the data swaps) + **"Compare all" matrix**
> hybrid with a **per-vertical real-YAML toggle**; scene **7** → an **SVG fan-flow**
> (the runtime pipeline + the **YAML→6-artifacts fan-out**) with **marching-dash
> animation** + **click-to-detail** cards + the **golden moat takeaway**.
> **Step-6 closeout (this batch, s71):** per-AC verification **AC-1…AC-14 = 14/14
> PASS** via the **preview workflow** (a11y/DOM probes + behavioral eval;
> `preview_screenshot` environmentally unavailable here). Highlights: **AC-13**
> teardown leak probe `OCT.Motion.activeCount().total === 0` after open→cycle all 7
> scenes→close; **AC-3** moat beat (LLM low-confidence → deterministic rule
> fail-safe reroute → **still** passes the human approve gate + records audit
> `WO-AQ-7731 · audit#a3f1`); **AC-8** scene-5 "**0 of 40**" figure confirmed
> defensible against `benchmarks/procedure_baseline/REPORT.md` §B-3; **AC-9/AC-12**
> honesty+offline greps clean (no `[search-synthesis]`/Palantir/dbt stat in copy,
> no CDN, fonts vendored). A **demo-operator runbook section** added to
> `docs/runbooks/run-oct-demo.md` (pre-warm MS-S1 → confirm `resident` → press S;
> the `?v=` bump convention); **PLAN-0033 `git mv` → `docs/plans/done/`** (Code's
> lane, ADR-009 D2). **Follow-up (s71):** scene 4 "Go live" now makes a **REAL
> MS-S1 extraction call** (shipped #390, merge `04efb8d`) — races
> `O.Intake.extract` against a **35s** hard timeout, falling back to the cached
> draft on timeout/degraded/error (live-smoked: real extract ~19.5s, warm
> `gpt-oss:20b`); this **completes the AC-7 true-live path** (was a scripted
> dummy). The readiness pill still does a real safe `GET /llm/status` read
> (PLAN-0018, never warms). **Group-A progression (this batch, s71):** with
> **A2 CLOSED** (committed reproducible re-grade harness #392 + the §B-3 residual
> decomposition #392/`2463229` + a STATUS reconcile #393), Code built the **G2
> drafting-friction root-fix Cowork dispatch**, and **PLAN-0034 (G2
> drafting-friction root-fix) is now committed as a `Draft`** (#394, merge
> `fda2557`) — **Cowork-drafted** (ADR-009 D1) off the s71 Code→Cowork dispatch,
> **Code R2-reviewed + committed** (ADR-009 D2). PLAN-0034 **drafts a two-prong
> fix and IMPLEMENTS NOTHING** (Out of Scope): **prong 1** tightens the
> **Stop-side** classifier (`_sonnet_classifier._build_system_prompt` +
> `.claude/autonomy-triggers.md` D-rows + `benchmarks/stop_classifier/gold.yaml`)
> against spurious dispatch/pause (CLAUDE.md-target / already-dispatched /
> existing-lifecycle-edit over-fires); **prong 2** exempts the **`plan-drafter`**
> subagent's **uncommitted draft-write** from the project-level **G2 PreToolUse
> gate** (`pretooluse_classifier_dispatch.py`), with **G5 commit-block + PR review
> preserving oversight**. Code R2 verified Cowork's **3 framing corrections**
> against HEAD (over-fires are Stop-side not the PreToolUse pre-filter;
> `run_eval.py` is manual/not-CI; the H2 boundary-inversion caveat is
> direction-specific) and applied **one R2 correction at commit** (fact-2's
> "PLANs never use Status: Accepted" was false — `done/0026` uses it). **Status:
> Draft — awaiting Cray ratification (SD-1..SD-4); nothing blocks Code** (the
> PLAN implements nothing; ratification is Cray's, the Step-3 spike is DEFERRED
> to a fresh session by a context-pressure call). AI-assisted (Claude Code,
> session 71); no `Co-Authored-By` per CLAUDE.md §7.

> **Session 69 (head_commit `0a32e67`) — PLAN-0033 Phase C **C0 VERTICAL
> SLICE** SHIPPED (#385): the aquaculture story-mode.** A new
> `services/api/static/assets/view-story.js` **additive overlay** (SD-C — it
> *coexists* with Views A–E and **never replaces** the console) lands the proven
> story-mode spine, alongside **`motion.js`** (a **driver-agnostic** Motion seam
> that enforces the lifecycle **teardown contract**) + `story.css`, wired into
> `index.html` / `app.js`. C0 delivers the three load-bearing structures: a
> **horizontal branching-DAG** overview (**5 node states + 3 edge types**,
> hand-placed SVG), a **two-axis layout** (all task details **left** / DAG +
> transport **right**), and the **scene-6 control surface** (Proposed→Approved→
> Executed kanban + a reasoning-trace **why-toggle** reusing the existing
> rule/llm/query colour legend). **The moat beat works (AC-3, ADR-010 IN-4):** an
> LLM-compose error **reroutes (amber) to the deterministic rule fail-safe**,
> which **still** passes the human **approve-gate** + **records audit** — the
> governance layer is the demo, not raw accuracy. **GSAP DEFERRED to C1/C2**
> (this **corrects** the s68 next_action that bundled "vendor GSAP locally" into
> C0-1): GSAP's 2026 public-repo licence check + local vendoring are gated, and
> because the Motion seam is **driver-agnostic**, C0 ships on the
> **zero-dependency WAAPI/rAF driver** (offline, no-CDN, the reduced-motion
> floor); GSAP — or an MIT lib like Motion One — drops in behind the same
> `Motion.useDriver` interface for C1/C2 scroll-driven beats after the one-time
> licence check, **with no scene-code change** (Cray's call, s69). **Verify:**
> phase AC-2/3/4/5/6/9/10/11/12/13/14 all confirmed via the **preview workflow**
> (accessibility snapshot + behavioral eval); the deterministic **/goal** gate
> (files exist / `index.html` wired / **no new CDN**) passes; **teardown leaks 0
> timers/tweens/listeners** across repeated open/close cycles. **Caveat:**
> `preview_screenshot` is **environmentally unavailable** in this WSL/FastAPI
> preview (it times out even on the plain console — not a page defect), so
> verification was snapshot + behavioral eval, which the workflow endorses for
> structure/content. **Scope:** Tier-1 mirror, **synthetic data only**
> (ADR-0015 D1); **no new backend**. **NEXT = C1** (full arc scenes) on the
> proven C0 spine, then **C2** (breadth + Ask + appendix) — Code execution, not
> Cowork-drafting. AI-assisted (Claude Code, session 69); no `Co-Authored-By` per
> CLAUDE.md §7.

> **Session 67 (head_commit `558ec29`) — PHASE B COMPLETE: B2 REGISTRY
> AUTO-DISCOVERY SHIPPED (#373); Group B foundation DONE.** A vertical under
> `verticals/<ns>/` exposing the conventional `register_<ns>_*` entry functions is
> now **discovered + registered at startup via import-scan**
> (`services/engine/discovery.py` / `discover_and_register()`, ADR-0023 D1 — the
> ADR-006 D3 **L1→L2** plugin-maturity move) — **no hand edit to `main.py`**.
> Additive (the explicit register API unchanged), idempotent (skips
> already-registered), failure-isolated (a broken vertical is skipped + logged),
> reset-resettable (PLAN-0005 R5). The hand-wired `_VERTICAL_REGISTRARS` map **and**
> the scaffold's `main.py` code-mod are **removed** — the "onboarding edits core"
> fragility is closed. **Verify:** new `test_discovery.py` (register-all /
> idempotent / failure-isolation / reset) + `test_scaffold` + `test_intake_routes`
> rewired (no main.py code-mod); **full suite 1615 passed, 22 skipped**; `ruff` +
> `mypy --strict` clean; offline. `feat(engine)` (#373 / `c0a4be9`); PLAN-0032
> `git mv`'d to `done/`. **Phase A + B (the engine backlog) are DONE** — ADR-0022 /
> ADR-0023 Accepted; PLAN-0028/0029/0030/0031/0032 shipped + archived. The moat is
> built: ontology → 6 generated artifacts (incl. the auto-generated ORM) →
> auto-registering plugins → 3 OCT features + governed entity resolution. **NEXT:**
> Phase C (UI rework, Cray-directed) + Phase D (#3b vertical refresh, light Cowork)
> per the roadmap handoff. AI-assisted (Claude Code, session 67); no
> `Co-Authored-By` per CLAUDE.md §7.

> **Session 67 (head_commit `7a59814`) — PHASE B: B1 ORM EMITTER SHIPPED
> (#370).** The SQLAlchemy ORM is now **generated from the ontology** — a 6th
> `emit_orm` in `code_generator.py` writes the energy ORM to the **committed**
> `services/db/models.py`, so DDL↔ORM parity (`test_schema_parity`) holds **by
> construction** instead of by hand-edit discipline (the PLAN-0005 §8.1 ORM-emitter
> Rule-of-Three trigger fired). **B1-DP-1 resolved Option B (Cray):** the ORM is a
> **runtime dependency** (services/db + alembic import it), so it generates to the
> committed central `models.py` via `_ORM_COMMITTED_DEST` — **not** a gitignored
> `verticals/<ns>/generated/` artifact; the re-export-from-gitignored approach (the
> originally-picked (a)) would break fresh checkouts — **caught at build +
> re-decided**. **SD-D:** the emitter does the ORM model only; Alembic stays
> separate. **Verify:** new `test_orm_emitter.py` + `test_schema_parity` green
> against the generated ORM; **full suite 1612 passed, 22 skipped**; `ruff` +
> `mypy --strict` clean; offline. `feat(engine)` (#370 / `73e85f3`); PLAN-0031
> `git mv`'d to `done/`. **Deferred (Cray):** the per-vertical ORM layout is a
> Rule-of-Three follow-up (trigger: vertical #2 needs an ORM) — Active TODO.
> **NEXT:** the ADR-0023 ratification-flip (dispatch `…1534…` → Cowork flips; Cray
> ratified SD-A=new-ADR + SD-C=import-scan) → unblocks **B2** (PLAN-0032)
> implementation. AI-assisted (Claude Code, session 67); no `Co-Authored-By` per
> CLAUDE.md §7.

> **Session 67 (head_commit `0593bc8`) — PHASE B KICKOFF: Group B
> foundation governance committed (ADR-0023 + PLAN-0031/0032).** Cray **triggered
> Group B** (Rule-of-Three met on energy/supply_chain/aquaculture; ADR-006 D4) and
> ruled **B2 needs an ADR-006-area touch**. Cowork authored 3 drafts; **Code
> reviewed (R2-verified the anchors — `main.py:40-42` map, `registry.py:51-52` dup
> guard, `test_intake_routes.py:256` assertion) + committed**: **ADR-0023**
> (registry auto-discovery = the ADR-006 D3 **L1→L2** plugin-maturity move;
> **Proposed**, #367 `a9488b6`) · **PLAN-0031** (B1 ORM emitter — a 6th `emit_orm`
> so `test_schema_parity` holds by construction; **no ADR gate**) · **PLAN-0032**
> (B2 registry auto-discovery via import-scan; **gated on ADR-0023 Accepted**) —
> both #368 `0593bc8`. Cowork resolved **SD-A=new-ADR · SD-B=split ·
> SD-C=import-scan · SD-D=ORM-only** + surfaced **B1-DP-1** (ORM output location).
> **AWAITING Cray:** ratify ADR-0023 (Proposed→Accepted, SD-A/SD-C) + confirm
> SD-B/SD-D/B1-DP-1 → then Cowork flips ADR-0023 (G1-trap for Code) → Code
> implements **B1 now** + **B2 after the ADR**, offline-only. AI-assisted (Claude
> Code, session 67); no `Co-Authored-By` per CLAUDE.md §7.

> **Session 67 (head_commit `0b56fdf`) — PHASE A COMPLETE: ADR-0022
> ratified + PLAN-0030 member (a) SHIPPED (#365).** Governed **entity resolution**
> now lands on the LLM recommend path (ADR-0022 D2 member (a), the universality
> lever): `recommend()` resolves each model-emitted `EntityRef.primary_key` against
> the vertical's **declared object universe** via the registered
> `DataAdapter.fetch_objects` (**1-b**); a resolving PK keeps the **canonical**
> declared key, a non-resolving PK **falls back to the deterministic event subject
> anchor** (`recommender.py:265`) + a `ReasoningStep(kind="entity_resolution")`
> records the outcome — the governed record **never certifies a model-invented
> identity** (PDPA-forward). **SD-1 = trace-only** (ADR-007 D2 envelope untouched) +
> **SD-2 = shared `event_subject_ref()`** (the LLM-path fall-back and the
> deterministic `:265` path converge, can't drift) — both **Cray-adjudicated**
> 2026-06-18. **D-6 honoured** (fresh product-side key normalizer; no `benchmarks/`
> cross-import, AST-asserted); member (b) verify+reshape **forward-declared**; the
> deterministic fail-safe `:265` **not regressed**. **Verify:** new
> `test_entity_resolution.py` (full contract — resolving/fall-back/never-invent/
> mixed/unknown-type/error→fail-safe/SD-2/D-6); **full suite 1608 passed, 22
> skipped**; `ruff` + `mypy --strict` clean; **offline-only** (no host-state).
> `feat(engine)` (#365, merge `0b56fdf` / `2068e1f`); PLAN-0030 `git mv`'d to
> `done/`. **NEXT = Phase B** (Group B foundation: ORM emitter + registry
> discovery) per the roadmap handoff. AI-assisted (Claude Code, session 67); no
> `Co-Authored-By` per CLAUDE.md §7.

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
| 2026-06-22 | **PLAN-0034 (G2 drafting-friction root-fix) FULLY COMPLETE (session 72)** — Step-5 prong-2 scope annotation Cowork-drafted (ADR-009 D1, K-1/K-2 scratchpad; Code declined the Stop-hook Code-direct override, applied byte-identical edits) + merged #399 (`0f56d24`/`5daa0e0`) into `.claude/autonomy-triggers.md`; PLAN flipped Ready→Complete + `git mv` to `done/` (`72f0deb`). SD-3 = (a) PLAN-only, **no ADR amendment**. Optional live gold re-score (prong-1 behavioral proof) remains Cray-gated host-state — **NOT** an acceptance gate (offline gate, green at #397, is the sole acceptance condition). Group-A: A2 ✅ → G2 ✅ → A1 next | `0f56d24`/`5daa0e0` (#399) + `72f0deb` / `.claude/autonomy-triggers.md` + `docs/plans/done/0034-*.md` |
| 2026-06-21 | **PLAN-0034 (G2 drafting-friction root-fix) RATIFIED + core-IMPLEMENTED (#396/#397, session 71)** — Cray ratified all four SDs = option (a) (#396 `5705b8a`, merge `3dcecaa`). SD-1 (prong-2 mechanism) gated on a Code Step-3 spike run offline this session: it confirmed (Q1) project PreToolUse hooks DO fire inside a subagent context (deadlock real, prong 2 needed) and (Q2) the payload carries BOTH `agent_id` and `agent_type` reliably (docs omit them; the live harness provides them — vindicates `done/0009` §1) → SD-1 = (a) exempt `agent_type=="plan-drafter"` reusing G5's `_is_subagent_call`/`agent_id` (SUPERSEDED the pre-spike (c) lean); SD-2 = (a) hybrid guards; SD-3 = (a) PLAN-only + `.claude/autonomy-triggers.md` annotation (no ADR amendment); SD-4 = (a) keep G5/PR-review/"only Code commits" untouched. Cowork folded ratify+spike into the PLAN (D1), Code R2-reviewed + committed (D2) → PLAN Status: Ready for execution. **Impl (#397 `c69b6e2`, merge `9092db5`):** offline deterministic core; self-modification of the autonomy hooks Cray-approved per-diff, opened as a PR + NOT self-merged (Cray merged — the SD-4 checkpoint). Prong 2: `pretooluse_classifier_dispatch.py` exempts the `plan-drafter` subagent (short-circuit before `_classify()`; main-agent writes have no `agent_id` so G2 preserved; `# noqa: C901` justified). Prong 1: three DISPATCH over-fire guards in `_sonnet_classifier._build_system_prompt` (non-`docs/(adr\|plans)/NNNN` / already-routed / existing-lifecycle-flip; genuine `Status: Accepted` ADR mutation still pauses — G1 unchanged) + 6 `expected: pause` gold negatives. Gates green: 137 targeted + 730 handoffs/benchmark pass, ruff/ruff-format/mypy --strict clean, gold parses. Offline-only; live gold re-score (prong-1 behavioral proof) stays Cray-gated host-state — NOT run. **PLAN-0034 stays Ready for execution (NOT Complete, NOT `done/`);** tails = Cowork `.claude/autonomy-triggers.md` annotation (Step 5) + optional live re-score | `c69b6e2`/`9092db5` (#396/#397) / `pretooluse_classifier_dispatch.py` + `.claude/hooks/_sonnet_classifier.py` + `benchmarks/stop_classifier/gold.yaml` + `docs/plans/0034-*.md` |
| 2026-06-21 | **PLAN-0034 (G2 drafting-friction root-fix) committed as DRAFT — Cowork-drafted, Code R2-reviewed (#394 merge `fda2557`, session 71)** — Cowork-authored (ADR-009 D1) off the s71 Code→Cowork dispatch, Code R2-reviewed + committed (ADR-009 D2). DRAFTS a two-prong fix and IMPLEMENTS NOTHING (Out of Scope): prong 1 = tighten the Stop-side classifier (`_sonnet_classifier._build_system_prompt` + `.claude/autonomy-triggers.md` + `benchmarks/stop_classifier/gold.yaml`) vs spurious dispatch/pause; prong 2 = exempt the `plan-drafter` uncommitted draft-write from the project G2 PreToolUse gate (`pretooluse_classifier_dispatch.py`), G5 commit-block + PR review preserving oversight. Code R2 verified Cowork's 3 framing corrections vs HEAD + applied 1 R2 correction at commit (the "PLANs never use Status: Accepted" fact was false — `done/0026` uses it). **Status: Draft — awaiting Cray ratification (SD-1..SD-4); the Step-3 spike DEFERRED to a fresh session.** Same batch (s71) also CLOSED A2 (committed re-grade harness #392 + §B-3 residual decomposition `2463229` + reconcile #393) | `fda2557` (#394) / `docs/plans/0034-*.md` |
| 2026-06-20 | **PLAN-0033 Phase C COMPLETE — full 7-scene story-mode arc MERGED + Step-6 closeout (#387 merge `d7ae465`, session 70; closeout session 71)** — C1 (scene 1 Hook / 2 Govern-with-fail-safe-self-catch / 4 live-intake dual-path / 5 Before-After) + C2 (scene 6 Breadth / 7 Appendix) on a SCENES registry + generic shell with a two-tier Motion scope (shell + per-scene) enforcing the AC-13 teardown contract; additive `view-story.js` overlay (SD-C, coexists with Views A–E), synthetic Tier-1 mirror (ADR-0015 D1), no new backend, offline/no-CDN. On-screen copy localised to English; offline IBM Plex fonts vendored (#388); `?v=` static-asset cache-bust added. Two scenes iterated live (Cray review): scene 6 → swap-in-place + "Compare all" matrix hybrid (per-vertical real-YAML toggle); scene 7 → SVG fan-flow (runtime pipeline + YAML→6-artifacts fan-out) + marching-dash animation + click-to-detail + golden moat takeaway. **Step-6 closeout (s71):** per-AC AC-1…AC-14 = 14/14 PASS via the preview workflow (a11y/DOM probes + behavioral eval; `preview_screenshot` env-unavailable) — AC-13 teardown `OCT.Motion.activeCount().total === 0` after cycling all 7 scenes; AC-3 moat beat (LLM low-conf → rule fail-safe reroute → still passes approve gate + audit `WO-AQ-7731 · audit#a3f1`); AC-8 scene-5 "0 of 40" defensible vs REPORT §B-3; AC-9/AC-12 honesty+offline greps clean. Demo-operator runbook section added to `docs/runbooks/run-oct-demo.md`; PLAN-0033 `git mv` → `done/`. Honesty note preserved: scene 4 "Go live" is a SCRIPTED dummy (hard-timeout → cached fallback, no real MS-S1 extract; Cray-approved deferral) — the readiness pill does a real safe `GET /llm/status` (PLAN-0018, never warms) | `d7ae465` (#387, #388) / `services/api/static/assets/view-story.js` + `docs/runbooks/run-oct-demo.md` + `docs/plans/done/0033-phase-c-demo-ui.md` |
| 2026-06-19 | **PLAN-0033 Phase C C0 vertical slice SHIPPED — aquaculture story-mode (#385, feat `a9079e5` / merge `0a32e67`, session 69)** — the additive `view-story.js` overlay (SD-C; coexists with Views A–E, never replaces) + `motion.js` (driver-agnostic Motion seam enforcing the lifecycle-teardown contract) + `story.css`, wired into `index.html`/`app.js`. Delivers the branching-DAG overview (5 node states + 3 edge types, hand-placed SVG), the two-axis layout (all task details left / DAG + transport right), and the scene-6 control surface (Proposed→Approved→Executed kanban + reasoning-trace why-toggle reusing the rule/llm/query colour legend). Moat beat (AC-3, ADR-010 IN-4) works: an LLM-compose error reroutes (amber) to the deterministic rule fail-safe, which still passes the human approve-gate + records audit. **GSAP DEFERRED to C1/C2** (Cray's call, s69 — corrects the s68 next_action): the seam is driver-agnostic so C0 ships on the zero-dependency WAAPI/rAF driver (offline, no-CDN, reduced-motion floor); GSAP/Motion One drops in behind `Motion.useDriver` later after the one-time licence check, no scene-code change. AC-2/3/4/5/6/9/10/11/12/13/14 verified via the preview workflow (a11y snapshot + behavioral eval); deterministic /goal gate (files exist / wired / no new CDN) passes; teardown leaks 0 timers/tweens/listeners. Caveat: `preview_screenshot` environmentally unavailable in this WSL/FastAPI preview (times out on the plain console too — not a page defect). Scope: Tier-1 mirror, synthetic only (ADR-0015 D1); no new backend. NEXT = C1 (full arc scenes) then C2 (breadth+Ask+appendix) | `0a32e67` (#385, feat `a9079e5`) / `services/api/static/assets/view-story.js` + `motion.js` + `story.css` + `docs/plans/0033-*.md` |
| 2026-06-17 | **Session 67 Phase 1 — PLAN-0028 + PLAN-0029 ratify-flipped Proposed→Accepted + archived to `done/` (#357, `1cda40f`)** — Cray ratified both PLANs in-session 2026-06-17; Cowork applied the status-flip + ratification record (ADR-009 D1, G1-clean on Desktop), Code committed per ADR-009 D2 (#357, merge `1cda40f` / flip `3d5e2af`). A formal flip of **already-complete, already-Cray-approved** work (PLAN-0028 B-γ cross-vertical extension; PLAN-0029 entity-key whitespace calibration), not new work — closes the PLAN-0028/0029 governance loop; both moats' source PLANs now archived. R2-verified (spot SHAs + the #357 diff = status + ratification only). One harness note: a Stop-hook D2 auto-dispatch misrouted (tried to spawn `plan-drafter` to "draft a plan to flip" existing complete PLANs); Code declined per the override clause — reinforces the parked G2-drafting-friction root-fix (now an Active TODO) | `1cda40f` (#357, flip `3d5e2af`) / `docs/plans/done/0028-*.md` + `docs/plans/done/0029-*.md` |
| 2026-06-16 | **B-γ EXECUTED END-TO-END — PLAN-0027 Steps 2–5 SHIPPED; PLAN-0019 Step B-γ / AC B-3 = DONE (#339–#342, `0aee4eb`, session 64)** — the three-arm comparison on the energy breach subset, run to completion. Offline arms (#339 `e41806a`/`a394342`, Steps 2–3): arm (b) raw text-to-SQL + arm (c) lean RAG + comparison harness, behind a mock-ChatClient offline gate (D-6 guard intact). ONE Cray-approved scored host-state run (`gpt-oss:20b` @ MS-S1, 40 energy breach items, warm-first; every score VERIFIED from `--dump-json` via the Read tool, reports-not-gates per B-3/B-6), then the B-3 REPORT landed (#342 `0aee4eb`/`01370e5`, Step 5). **Results:** arm (a) governed stack 97.5–100% entity+action (REUSED, D-2, not re-run; p95 ~30s); arm (b) raw text-to-SQL 100% entity-ID (40/40, correct `WHERE measured_value >= 90`) but structurally cannot propose an action (D-3; p95 10.2s); arm (c) lean RAG 97.5% entity+action (39/40; action 100%; p95 3.2s); 0 errors / 0 invalid SQL; the lone arm-c miss (`energy-h05`) is a real naive-RAG output-fidelity miss (`E113` not `asset-E113`), VERIFIED not a grading artifact. **Load-bearing finding:** raw entity+action accuracy does NOT separate the governed stack from lean RAG (c ties a at 97.5%) → relocates the moat claim off "raw NL→action accuracy" onto the governance layer (§3.4 verify+reshape / deterministic disposition / handler allowlist / audit that arm c structurally lacks); verify+reshape captured as a forward-pointer (future ADR-016 area), OUT OF SCOPE per D-6. Supporting: #340 (`099d55b`/`17863ef`, `test(handoffs):`) chip-session fix isolating `CLAUDE_GOAL_PATH` in `stub_env` so a live `goal.json` can't leak into Phase-2 Stop-hook tests (test-only +6; 575 passed/2 skipped); #341 (`cf645f7`/`7d8a716`, `fix(benchmarks):`) pre-run arm-c case-normalize calibration, ratified BEFORE the scored run per B-6 (recovers a correctly-named entity, never invents one). Concurrent-session recovery handled (shared WSL checkout: local↔origin divergence + transient `.git/index.lock` after #339; diagnosed read-only, nothing lost, synced cleanly). **PLAN-0027 complete; PLAN-0019 Step B-γ / AC B-3 = DONE** | `0aee4eb` (#339/#340/#341/#342) / `benchmarks/procedure_baseline/` REPORT `## B-3` + `docs/plans/0027-*.md` |
| 2026-06-16 | **PLAN-0027 (B-γ comparison methodology pre-registration) LANDED + Cray-ratified §3–§4 (#337, `ab0174a`/`e70daa9`/`fb91777`, session 63)** — completes PLAN-0019 Step B-γ / AC B-3 **Step 1** (pre-registration); status now **Ready for execution**. Pre-registers the three-arm comparison on the energy breach subset: (a) governed-procedure stack (reuse REPORT numbers, no re-run), (b) raw text-to-SQL, (c) lean-but-real RAG — **reports-not-gates** (B-3/B-6) with a **D-6 contamination guard** (arm c stays a clean naive RAG baseline, no verify/reshape/governance layer). Governance (G2-routed): `plan-drafter` authored → G2 blocks Code/subagent PLAN writes → Cowork materialized (ungated) → Code committed (#337, ADR-009 D1/D2) → Cray ratified §3–§4 resolving SD-1..SD-4 per drafter recs, plus a **joint SD-1↔SD-2 fairness binding** (Cowork advisory): under the locked lexical retriever the corpus + question template must share vocabulary + cover every breach item's `action_keywords` lemma, else arm (c) misses = retrieval artifacts not paradigm limits. Side-thread (no artifact): G2-vs-drafting friction discussed; Cray PARKED the root-fix (exempt plan-drafter uncommitted-draft write from G2) as a future harness-improvement batch | `ab0174a` (#337, content `e70daa9`/`fb91777`) / `docs/plans/0027-*.md` |
| 2026-06-16 | **PLAN-0026 AC-9 optional live MS-S1 re-verify RAN + PASSED (#332, `dc65425`/`c16778d`, session 62)** — Cray-authorized host-state run closing the last PLAN-0026 open item; offline oracle stays the CI gate, AC-9 is verification-not-gate (Lesson #15). 12-Q NL-query harness vs `gpt-oss:20b` @ MS-S1 (`run_benchmark.py --warm`), offline oracle 65 passed immediately prior. **Result: 11/12 correct (was 10/12 in AC-8) · anti-hallucination 12/12 HELD · p50 15.5s / p95 39.0s.** Headline (AC-1 live): nl-08 + nl-11 both flipped correct on the deterministic structured lens (`result_count 7`, max `96.5 °C`, top `Battery Bank A` from the execute-stage `AggregateResult`, not phrase prose) — model emits `operation:max` not `list` and invents no `resolve` placeholder. Two honest notes: (1) lone miss = nl-01 (not an AC-9 target) — known simple-list filter-omission nondeterminism, zero fabrication, out of PLAN-0026 scope, offline gold green → not a Phase-A regression; (2) this run hit the right result via the model's own `unit=celsius` filter (`measured_kind:null`) so the coherence seam had nothing to rewrite — the seam is the safety net proven by the offline oracle (AC-7), both routes yield the identical grounded result. **Verdict: AC-9 PASS.** Recorded as a RESULTS.md addendum; `--dump-json` evidence gitignored at `.claude/benchmark-results/2026-06-16-nl-query-ac9.jsonl`. PLAN-0026 now fully closed incl. the optional live re-verify | `c16778d` (#332, content `dc65425`) / `benchmarks/nl_query_feasibility/RESULTS.md` |
| 2026-06-15 | **PLAN-0026 COMPLETE — ADR-0021 (metric-kind typed ontology semantics) AUTHORED→ACCEPTED then Phase A (`measured_kind`) SHIPPED; PLAN archived to `done/` (#327–#330, `b53e631`, session 61)** — closes PLAN-0026 end-to-end (the principled fix Phase B could only approximate). Cray decisions: Gate-1 = **T2** (NL-query is the moat wedge), Gate-2/SD-2 = **Path B** (kind↔unit binding in the ontology → a new ADR); cross-check confirmed **(b) over (c)** ((c) over-scope now per Rule of Three + ADR-008 D3, and (b) reuses entirely into (c)). **ADR-0021 ("classify, don't synthesize"):** Cowork-authored (ADR-009 D1) → Code committed Proposed (#327, `a102b9d`) → Cray ratified Accepted (#328, `4423a22`); construct **(b)** QUDT-style quantity-kind ⟂ unit typed pair (`quantity_bindings`) over (a) per-enum-value map and (c) composite; (c) is a **triggered successor** (ADR-016 procedure engine + ≥3 verticals); amends ADR-008 D3. **Phase A (steps 6–7, #329 `37f62a7`; `bcbb62d`+`7f72181`):** step 6 — `measured_kind` enum (temperature|frequency) + object-level `quantity_bindings` on OperationalEvent, admitted by `ontology_schema.json` + parsed into `ontology_meta`, synthetic data tagged (7/2/2), emitted across all 5 artifacts, D6 L2 validator check, ORM + Alembic `0003` column (DB↔DDL parity via `test_schema_parity`); step 7 — `StructuredQuery.measured_kind` (translate LLM **classifies** the kind, the coherence seam **synthesizes** the precise `unit` from the binding, **superseding** Phase B dominant-unit per IN-1; no kind → dominant fallback, classified-but-absent → clarify, never fabricate). Distinguishes "highest frequency" from "highest temperature". Suite 1535/22; ruff+ruff-format+mypy clean; 12/12 anti-hallucination preserved; offline oracle re-pointed to a classified `measured_kind`; 6 new tests (4 engine + 2 validator). PLAN-0026 → `done/` (#330, `0a1427e`/`b53e631`). No gated NL-query work remains | `b53e631` (#327/#328/#329/#330) / `docs/adr/0021-metric-kind-typed-ontology-semantics.md` + `services/engine/nl_query.py` + `docs/plans/done/0026-nl-query-aggregate-metric-semantics.md` |

## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13 (ratified `4d1347b`, #302; committed Proposed `e25281d`, #297 + instruction `e387a63`, #298 + R1 errata `655344d`, #300) — guarded trial under observation (parallel to ADR-012). A specialist Cowork project role-plays a Thai operator and emits a "partner profile package" to rehearse the intake+PDPA pipeline before a real partner; venue OUTSIDE the governance tiers (no commits / no repo mount / enters via Code receive). Three BINDING anti-circularity rules R1/R2/R3 (R3 SYNTHETIC provenance → never trips PLAN-0005 §8.1 / ADR-011 first-real-data trigger). All four venue SDs + dispatch-SD-1 ratified per Cowork rec (SD-1 N=3; SD-2 one-project-per-business-type; SD-3 size/region/maturity enums w/ energy·mid·th-regional·mixed-legacy default; SD-4 "what we refused to share" now required). D4 guarded-trial mirrors ADR-012 D5; regression triggers R-PS1..R-PS4 are the exit criteria; run 1 = energy operator (ADR-005 primary). **Now live-able: Cray launches run-1 (paste the R1-clean seed NOT the one-pager); ADR-011 audit framework stays gated on a partner conversation — the synthetic run INFORMS but never TRIGGERS it.**
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten (full table: PLAN-0005 §8.1): rule-based recommender → **ADR-010 ACCEPTED (2026-05-22) → PLAN-0006 next** (LLM reasoning hook); minimal approval gate → **ADR-011+** (audit framework — trigger: first design-partner data / PDPA review); no mapping layer → **dbt/SQLMesh** (trigger: first non-synthetic source); hand-authored ORM → **"ORM emitter"** Rule-of-Three candidate (trigger: 3rd vertical / DDL↔ORM parity-test drift); base Postgres only → **PLAN-002** (pgvector/AGE — trigger: semantic + graph features); explicit registry → **ADR-006 D3 L2** (trigger: vertical #2/#3 or `new-vertical` generator). *(per Cray note 2026-05-21)*
- [ ] **PLAN-004 Phase C — OPTIONAL POLISH (forward-declared; "may never land"):** HTML/markdown handoff dashboard under `docs/` + references-graph (mermaid dispatch chains) + `render_transcript.py` unified session export (PLAN-0004 §"Phase C"). *(Phase A + B both COMPLETE — session 35; the prior TODO's validator **warning-swallow bug was FIXED #312**, s58. Minor never-formally-scoped sub-ideas — README/`_rename-map` walk-exclusion, Cat G `references_*` autofix, OQ-2 effective-vs-authored `status:` dashboard flag — fold in only if Phase C lands. Reconciled 2026-06-16 s65 audit.)*
- [ ] **A1 — verify+reshape governance demo (B-γ moat successor).** The heaviest moat-proof: prove the moat IS governance — verify an LLM step's output for semantic consistency + reshape to the next step's contract (what arm (c) structurally lacks; ADR-016 area; the B-3 REPORT forward-points to it). **Scope together with the Phase-2 governed-entity-resolution ADR** — one ADR-016-area construct, not two overlapping ADRs. **UPDATE (s71):** that consolidation is DONE — **ADR-0022 (Accepted) D3-α already houses verify+reshape as member (b)**, so A1 = a PLAN to build member (b) (like PLAN-0030 built member (a)), at most an ADR-0022 amendment if a member-(b) design fork surfaces — NOT a new ADR. A2's residual decomposition (s71) shows the concrete A1 target: the 5 correct-action "assessment-prose" cases (verify the proposal states the action, reshape from the resolved handler). Sequenced AFTER the G2 root-fix (Cray, s71). *(folded from §7 handoff, s67)*
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
