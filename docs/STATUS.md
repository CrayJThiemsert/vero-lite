---
last_updated: 2026-06-18T17:02:53+07:00
session: 67
current_batch: 'session-67 Phase B COMPLETE (Group B foundation). ADR-0023 (registry auto-discovery, ADR-006 D3 L1→L2) Accepted (#372); B1 ORM emitter shipped (#370); B2 registry auto-discovery shipped (#373, merge 558ec29 / commit c0a4be9). B2: discover_and_register() import-scans verticals/* + invokes the conventional register_<ns>_* entry functions at startup (services/engine/discovery.py) — additive, idempotent, failure-isolated, reset-resettable; the hand-wired main.py _VERTICAL_REGISTRARS map + the scaffold main.py code-mod are removed (a new vertical is auto-discovered, no core edit). Full suite 1615 passed; ruff + mypy --strict clean; offline. PLAN-0032 git mv to done/. The Phase A + B engine backlog is now DONE — ADR-0022/0023 Accepted; PLAN-0028/0029/0030/0031/0032 all shipped + archived. Per-vertical ORM layout deferred (B1-DP-1, Active TODO).'
current_actor: code
blocked_on: 'Nothing blocks Code — the Phase A + Phase B engine backlog is COMPLETE (ADR-0022/0023 Accepted; PLAN-0028/0029/0030/0031/0032 all shipped + archived). Next is Phase C (UI rework + new-vertical intake) + Phase D (#3b next-vertical refresh), both Cray-directed (UI design discussion happens in Chat/Cowork → a PLAN; #3b is a light Cowork refresh) — see next_action.'
next_action: 'Session-67 — Phase A + B (the engine backlog) DONE. NEXT per the session-67 roadmap handoff (…0938…): Phase C (UI rework + new-vertical intake — reflect the settled engine: pipeline display + receive-context-from-user-to-create-a-vertical; the B1 ORM emitter + B2 discovery seam are the enablers) — PARKED pending a Cray UI-design discussion (Chat/Cowork) → then a PLAN. Phase D (#3b next-vertical refresh via the semantic-distance lens; research at docs/research/private/2026-06-04-vertical3-pick.md) — LIGHT Cowork refresh, parallelable. Deferred: per-vertical ORM layout (B1-DP-1, Active TODO). All Cowork-routed / Cray-gated.'
head_commit: 558ec29
recent_commits: [558ec29, c0a4be9, cdccf83, 1cdd837, 7a59814, 73e85f3, 0593bc8, 2efb9eb, a9488b6, 206a242]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 67 (current; head_commit `558ec29`) — PHASE B COMPLETE: B2 REGISTRY
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

> **Session 67 (head_commit `1493196`) — PHASE A: ADR-0022 RATIFIED
> ACCEPTED (#361) + PLAN-0030 AUTHORED & COMMITTED (#363).** The governed-entity-resolution construct (the universality
> lever PLAN-0029 routed out) flipped **Proposed → Accepted** at Cray's
> ratification (2026-06-18), recording the resolved **design fork**: **F1 = 1-b**
> (DB/ontology-object lookup vs the declared object universe) primary **+ 1-c**
> (deterministic `subject_id`, `recommender.py:265`) fall-back · **F2 = 2-c** (fall
> back to the deterministic subject on a non-resolving model PK) **+ a
> resolution-outcome trace** (PDPA-forward — never silently fabricate identity) ·
> **D3 = α** (one construct housing entity resolution (a) + verify+reshape (b)).
> **Authoring split (ADR-009 D1/D2):** Code landed the mechanical Status flip
> under Cray's **direct in-context instruction**; the **G1 gate then correctly
> blocked Code** from authoring the ADR narrative once `Status:Accepted`, so
> **Cowork (Tier-1) authored the ratification narrative + the residual-tense
> coherence fold**; Code committed (#361, merge `5c51a75` / ratify `a9634e5`).
> Construct + framing **unchanged** from the Proposed draft (#359) — only the
> ratification outcome is recorded. **R2 verify:** the ratified ADR was read back
> on-disk + grep-swept (no present-tense-pending stragglers) before commit.
> **Phase A tail — through PLAN-0030 commit:** Code wrote the Code→Cowork
> **PLAN-0030** dispatch (`…1210…`); Cowork authored it (ADR-009 D1, the
> entity-resolution build / member (a)); Code reviewed + committed the draft (#363,
> `1493196`). **NEXT — Cray adjudicates 2 surfaced decisions** before
> implementation: **SD-1** (resolution marker: trace-only `ReasoningStep` [Cowork
> rec] vs an optional `EntityRef.resolution` field on the shared ADR-007 D2
> envelope) · **SD-2** (shared `_event_subject_ref(event)` helper [Cowork rec] vs
> duplicate — the helper edits the guarded `:265` line, behavior-preserving). Then
> Code implements member (a) on a `feat/*` branch (offline-only; impl-gate
> ADR-0022-Accepted satisfied). Then **Phase B** (Group B foundation: ORM emitter +
> registry discovery) per the session-67 roadmap handoff. AI-assisted (Claude Code,
> session 67); no `Co-Authored-By` per CLAUDE.md §7.

> **Session 67 (head_commit `1cda40f`) — PHASE 1 RATIFY-FLIPS DONE
> (#357): PLAN-0028 + PLAN-0029 → Accepted + archived to `done/`.** The
> governance-closeout half of the universality track: **PLAN-0028** (B-γ
> cross-vertical extension — aquaculture + supply_chain) and **PLAN-0029**
> (entity-key whitespace calibration + offline re-grade) both flipped
> **Proposed (draft) → Accepted** (Cray ratified in-session 2026-06-17) and
> `git mv`'d to `docs/plans/done/`. **Cowork** applied the status-flip +
> ratification record (ADR-009 D1, G1-clean on Desktop); **Code** committed
> per ADR-009 D2 (#357, merge `1cda40f` / flip `3d5e2af`). Both PLANs document
> **already-complete, already-Cray-approved** work — a formal flip, not new
> work — so this is a clean close of the PLAN-0028/0029 governance loop; both
> moats' source PLANs are now archived. **R2 trust-but-verify confirmed:** spot
> SHAs check out (#353 `e5f9774`/`1ada20d`, #355 `d48b770`/`7275a69`) and the
> #357 diff is **status + ratification record only** (no scope/numbers change).
> **One harness note:** a Stop-hook D2 auto-dispatch **misrouted** — it tried to
> spawn `plan-drafter` to "draft a plan to flip 0028/0029," but the task was a
> **status-flip on existing complete PLANs**, not new-plan drafting; Code
> declined per the hook's override clause (reinforces the parked
> G2-drafting-friction root-fix — now a durable Active TODO). **Frontier:**
> Phase 2 kicked off — **ADR-0022 (governed entity resolution) authored by Cowork
> + committed Proposed (#359, `9ce1289`)**, design-first with the §Design fork left
> OPEN (Fork 3 = D-6 guard binding); scoped as one ADR-016-area construct also
> housing Group-A A1 (verify+reshape). **Awaits Cray ratification** (resolves the
> fork) → then a separate Cowork dispatch authors PLAN-0030; vertical-#3 research
> runs in parallel — all **Cowork-routed / Cray-gated**. Nothing blocks Code.
> AI-assisted (Claude Code, session 67); no `Co-Authored-By` per CLAUDE.md §7.

> **Session 66 (current; head_commit `e5f9774`) — PLAN-0028 Step 5 RAN + VERIFIED;
> PLAN-0029 (entity-key whitespace calibration) minted + implemented; canonical B-γ
> numbers locked.** Building on session 65's offline Step 2/3 (#350 — the data-driven
> harness + the aquaculture/supply_chain corpora), this session got the Cray
> host-state go and ran **PLAN-0028 Step 5** — the ONE combined scored sweep
> (`gpt-oss:20b` @ MS-S1, warm-first, 80 breach items = 40 aquaculture + 40
> supply_chain, serialized in one warm window via a `systemd-run --user` unit, ~18
> min, **0 errors / 0 invalid SQL**). Every score traced to a real model verdict via
> the Read tool (session-46 confirm-don't-infer). **Cross-vertical finding
> (Cray-ratified framing):** arm (c) **lean RAG ties arm (a) governed on BOTH new
> verticals** (canonical **100% / 100%** post-calibration), while arm (b) **raw
> text-to-SQL swings 0% (aquaculture) ↔ 100% (supply_chain)** — the swing is
> **evidence FOR the moat, not a bug**: the explanatory variable is **semantic
> distance** between the NL question and the physical schema (supply_chain breach = a
> clean numeric threshold raw SQL nails; aquaculture breach hides meaning in a
> free-text `description` + a named pond subtype raw SQL must guess → 0 rows). arm (c)
> is robust because the corpus carries the mapping ("ontology in prose"); the governed
> stack declares it once. **OQ-2 answered: the arm-c≈arm-a tie REPLICATES.** **The
> single aquaculture arm-c miss (aqua-h06) was a grader MEASUREMENT artifact** — the
> model named the right pond `pond-A116` with a **U+202F NARROW NO-BREAK SPACE**
> separator the hyphen-only `normalize_primary_key` didn't recover. Under Cray's
> **universality** criterion the fix split two ways: **(1) PLAN-0029** (small, offline)
> — extend the B-6 calibration to fold the whitespace-separator family
> ({U+0020,U+00A0,U+2007,U+202F,U+2060} → ASCII `-`, recover-only / never-invent) + an
> **offline re-grade** of the stored dumps (no host-state); **(2) the product
> entity-trust gap** (`recommender._compose_llm_record` trusts model-emitted entity
> PKs verbatim, no resolution against the declared object universe) = the **real
> universality investment**, routed OUT → a future **ADR + PLAN-0030** (design-first).
> PLAN-0029 was **minted #352** — the **G2 boundary blocked both the in-harness
> plan-drafter AND Code** from writing a new PLAN (G2 ≠ G1, no in-context-approval
> release; **Cowork authored on Desktop, Code committed** via a `docs/*` chore PR) —
> then **implemented #353** (`feat(benchmarks)`): the whitespace fold + 4 regression
> tests + the offline re-grade harness (`benchmarks/procedure_comparison/regrade.py`).
> **Re-grade VERIFIED via Read:** **exactly one** flip (aqua-h06) → aquaculture arm-c
> **39/40 → 40/40**; supply_chain unchanged 40/40; arm (b) whitespace-invariant by
> construction (not re-gradable from the dump → carried forward). Gate green: ruff +
> mypy clean, `tests/benchmark` **151 passed** (+4). **Step 6 B-3 REPORT cross-vertical
> extension SHIPPED (#355)** — canonical tables + OQ-1/OQ-3 disclosures +
> threats-to-validity → **PLAN-0028 COMPLETE end-to-end**. **Frontier (next session,
> Cowork-routed; see the session-66 closeout handoff `…1405…`):** the
> PLAN-0028/0029 status-flips + done-moves (Cowork, G1) and the ADR/PLAN-0030 +
> vertical-#3 research (Cowork-routed). Nothing blocks Code. AI-assisted (Claude Code,
> session 66); no `Co-Authored-By` per CLAUDE.md §7.

> **Session 64 (head_commit `0aee4eb`) — B-γ EXECUTED END-TO-END:
> PLAN-0027 Steps 2–5 SHIPPED; PLAN-0019 Step B-γ / AC B-3 = DONE.** This session
> read the session-63 handoff and ran PLAN-0019's last open step (the three-arm
> comparison on the energy breach subset) to completion. **Offline arms (#339
> `e41806a`/`a394342`, Steps 2–3):** arm (b) **raw text-to-SQL** + arm (c)
> **lean RAG** + the comparison harness, all built behind a **mock-ChatClient
> offline gate** (D-6 contamination guard intact — arm c stays a clean naive RAG
> baseline). **ONE Cray-approved scored host-state run** (`gpt-oss:20b` on MS-S1,
> 40 energy breach items, warm-first; **every score VERIFIED from `--dump-json`
> via the Read tool**, reports-not-gates per B-3/B-6), then the **B-3 REPORT**
> landed (#342 `0aee4eb`/`01370e5`, Step 5). **Scored results:** arm (a)
> governed-procedure stack **97.5–100%** entity+action (REUSED from REPORT, D-2 —
> NOT re-run; p95 ~30s/judgment); arm (b) raw text-to-SQL **100% entity-ID** (40/40,
> correct `WHERE measured_value >= 90` threshold join) but **structurally cannot
> propose an action** (D-3; p95 10.2s); arm (c) lean RAG **97.5% entity+action**
> (39/40; action 100%; p95 3.2s). **0 errors / 0 invalid SQL.** The one arm-c miss
> (`energy-h05`) is a real naive-RAG output-fidelity miss (emitted non-canonical
> `E113`, not the ontology key `asset-E113`), VERIFIED — not a grading artifact.
> **The load-bearing finding:** raw entity+action accuracy does **NOT** separate
> the governed stack from lean RAG (arm c ties arm a at 97.5%) → this **relocates
> the moat claim** off "raw NL→action accuracy" and onto the **governance layer**
> (the §3.4 verify+reshape / deterministic disposition / handler allowlist / audit
> narrative arm c structurally lacks). The **verify+reshape enhancement** is
> captured as a forward-pointer (future ADR-016 area), OUT OF SCOPE for B-γ per the
> D-6 contamination guard. **Two supporting PRs:** **#340** (`099d55b`/`17863ef`,
> `test(handoffs):`) — the spun-off chip-session fix isolating `CLAUDE_GOAL_PATH`
> in the `stub_env` fixture so a developer's live `.claude/state/goal.json` can't
> leak into the Phase-2 Stop-hook integration tests (test-only +6 lines; handoffs
> suite 575 passed / 2 skipped; before/after repro: PR head + active goal PASSES,
> main FAILS with goal-gate dispatch); **#341** (`cf645f7`/`7d8a716`,
> `fix(benchmarks):`) — the pre-run measurement-correctness calibration
> (case+hyphen-normalize the arm-c free-text entity match, **ratified BEFORE the
> scored run** per B-6; only recovers a correctly-named entity, never invents one).
> **Concurrent-session recovery handled:** the chip session ran in the SHARED WSL
> checkout; after #339 merged, local-main vs origin diverged + a transient
> `.git/index.lock` appeared — diagnosed read-only (nothing lost: origin/main
> correct, chip work pushed) then synced cleanly (the shared-worktree
> concurrent-branch-switch lesson). **Frontier:** B-γ extension to aquaculture +
> supply_chain (D-5 was energy-first; the natural point to revisit RAG-baseline
> fairness with a fresh creative/adversarial Cowork perspective) + the
> verify+reshape forward-pointer (future PLAN/ADR) — both Cray-routed/gated. Held
> items unchanged (PLAN-002 ≥ADR-014, auditprep + ADR-011 real-partner-gated,
> partner-sim, ADR-0021(c) future-triggered). Nothing blocks Code.
> AI-assisted (Claude Code, session 64); no `Co-Authored-By` per CLAUDE.md §7.

> **Session 63 (head_commit `ab0174a`) — B-γ KICKOFF: PLAN-0027 (B-γ
> COMPARISON METHODOLOGY PRE-REGISTRATION) LANDED + CRAY-RATIFIED §3–§4 (#337).**
> This session opens **B-γ** — PLAN-0019's last open step (AC B-3): the three-arm
> comparison on the **energy breach subset** — (a) the **governed-procedure stack**
> (reuse the existing REPORT numbers, **no re-run**), (b) **raw text-to-SQL**, and
> (c) a **lean-but-real RAG** baseline. Framed **reports-not-gates** (B-3/B-6) with
> a **D-6 contamination guard**: arm (c) stays a clean naive RAG baseline — **no**
> verify/reshape/governance layer bleeds in, so the comparison measures paradigms
> not a stacked deck. **PLAN-0027 completes B-γ Step 1 (pre-registration); status is
> now Ready for execution.** **Governance chain (the G2-routed path):** the
> in-harness `plan-drafter` authored the PLAN body → the **G2 PreToolUse gate blocks
> Code/subagent from writing a new PLAN** → **Cowork materialized** the file
> (ungated) → **Code committed** it (#337 `e70daa9`; ADR-009 D1/D2) → **Cray ratified
> §3–§4** (`fb91777`), resolving **SD-1..SD-4** per the drafter recommendations.
> Added at ratification: a **joint SD-1↔SD-2 fairness binding** (Cowork advisory) —
> under the locked lexical retriever the corpus + question template must **share
> vocabulary** and cover every breach item's `action_keywords` lemma, else arm (c)
> misses are **retrieval artifacts, not paradigm limits** (the binding that keeps the
> naive-RAG arm an honest baseline). **Also this session (no artifact change):**
> discussed the recurring **G2-vs-drafting friction** (the gate that forces the
> plan-drafter → Cowork → Code relay on every new PLAN); Cray **PARKED** the root-fix
> (exempt the plan-drafter's *uncommitted-draft* write from G2) as a **future
> harness-improvement batch**, and a "proceed vs Cowork-dispatch-file" routing
> framework was captured in private memory. **Frontier:** PLAN-0027 is Ready —
> **Step 2 (build arms b + c + the comparison harness offline, mock-ChatClient,
> honoring the joint binding) is ungated**; Step 3 offline gate; Step 4 host-state
> run is Cray-gated (§8). Held items unchanged. Nothing blocks Code.
> AI-assisted (Claude Code, session 63); no `Co-Authored-By` per CLAUDE.md §7.

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
| 2026-06-17 | **Session 67 Phase 1 — PLAN-0028 + PLAN-0029 ratify-flipped Proposed→Accepted + archived to `done/` (#357, `1cda40f`)** — Cray ratified both PLANs in-session 2026-06-17; Cowork applied the status-flip + ratification record (ADR-009 D1, G1-clean on Desktop), Code committed per ADR-009 D2 (#357, merge `1cda40f` / flip `3d5e2af`). A formal flip of **already-complete, already-Cray-approved** work (PLAN-0028 B-γ cross-vertical extension; PLAN-0029 entity-key whitespace calibration), not new work — closes the PLAN-0028/0029 governance loop; both moats' source PLANs now archived. R2-verified (spot SHAs + the #357 diff = status + ratification only). One harness note: a Stop-hook D2 auto-dispatch misrouted (tried to spawn `plan-drafter` to "draft a plan to flip" existing complete PLANs); Code declined per the override clause — reinforces the parked G2-drafting-friction root-fix (now an Active TODO) | `1cda40f` (#357, flip `3d5e2af`) / `docs/plans/done/0028-*.md` + `docs/plans/done/0029-*.md` |
| 2026-06-16 | **B-γ EXECUTED END-TO-END — PLAN-0027 Steps 2–5 SHIPPED; PLAN-0019 Step B-γ / AC B-3 = DONE (#339–#342, `0aee4eb`, session 64)** — the three-arm comparison on the energy breach subset, run to completion. Offline arms (#339 `e41806a`/`a394342`, Steps 2–3): arm (b) raw text-to-SQL + arm (c) lean RAG + comparison harness, behind a mock-ChatClient offline gate (D-6 guard intact). ONE Cray-approved scored host-state run (`gpt-oss:20b` @ MS-S1, 40 energy breach items, warm-first; every score VERIFIED from `--dump-json` via the Read tool, reports-not-gates per B-3/B-6), then the B-3 REPORT landed (#342 `0aee4eb`/`01370e5`, Step 5). **Results:** arm (a) governed stack 97.5–100% entity+action (REUSED, D-2, not re-run; p95 ~30s); arm (b) raw text-to-SQL 100% entity-ID (40/40, correct `WHERE measured_value >= 90`) but structurally cannot propose an action (D-3; p95 10.2s); arm (c) lean RAG 97.5% entity+action (39/40; action 100%; p95 3.2s); 0 errors / 0 invalid SQL; the lone arm-c miss (`energy-h05`) is a real naive-RAG output-fidelity miss (`E113` not `asset-E113`), VERIFIED not a grading artifact. **Load-bearing finding:** raw entity+action accuracy does NOT separate the governed stack from lean RAG (c ties a at 97.5%) → relocates the moat claim off "raw NL→action accuracy" onto the governance layer (§3.4 verify+reshape / deterministic disposition / handler allowlist / audit that arm c structurally lacks); verify+reshape captured as a forward-pointer (future ADR-016 area), OUT OF SCOPE per D-6. Supporting: #340 (`099d55b`/`17863ef`, `test(handoffs):`) chip-session fix isolating `CLAUDE_GOAL_PATH` in `stub_env` so a live `goal.json` can't leak into Phase-2 Stop-hook tests (test-only +6; 575 passed/2 skipped); #341 (`cf645f7`/`7d8a716`, `fix(benchmarks):`) pre-run arm-c case-normalize calibration, ratified BEFORE the scored run per B-6 (recovers a correctly-named entity, never invents one). Concurrent-session recovery handled (shared WSL checkout: local↔origin divergence + transient `.git/index.lock` after #339; diagnosed read-only, nothing lost, synced cleanly). **PLAN-0027 complete; PLAN-0019 Step B-γ / AC B-3 = DONE** | `0aee4eb` (#339/#340/#341/#342) / `benchmarks/procedure_baseline/` REPORT `## B-3` + `docs/plans/0027-*.md` |
| 2026-06-16 | **PLAN-0027 (B-γ comparison methodology pre-registration) LANDED + Cray-ratified §3–§4 (#337, `ab0174a`/`e70daa9`/`fb91777`, session 63)** — completes PLAN-0019 Step B-γ / AC B-3 **Step 1** (pre-registration); status now **Ready for execution**. Pre-registers the three-arm comparison on the energy breach subset: (a) governed-procedure stack (reuse REPORT numbers, no re-run), (b) raw text-to-SQL, (c) lean-but-real RAG — **reports-not-gates** (B-3/B-6) with a **D-6 contamination guard** (arm c stays a clean naive RAG baseline, no verify/reshape/governance layer). Governance (G2-routed): `plan-drafter` authored → G2 blocks Code/subagent PLAN writes → Cowork materialized (ungated) → Code committed (#337, ADR-009 D1/D2) → Cray ratified §3–§4 resolving SD-1..SD-4 per drafter recs, plus a **joint SD-1↔SD-2 fairness binding** (Cowork advisory): under the locked lexical retriever the corpus + question template must share vocabulary + cover every breach item's `action_keywords` lemma, else arm (c) misses = retrieval artifacts not paradigm limits. Side-thread (no artifact): G2-vs-drafting friction discussed; Cray PARKED the root-fix (exempt plan-drafter uncommitted-draft write from G2) as a future harness-improvement batch | `ab0174a` (#337, content `e70daa9`/`fb91777`) / `docs/plans/0027-*.md` |
| 2026-06-16 | **PLAN-0026 AC-9 optional live MS-S1 re-verify RAN + PASSED (#332, `dc65425`/`c16778d`, session 62)** — Cray-authorized host-state run closing the last PLAN-0026 open item; offline oracle stays the CI gate, AC-9 is verification-not-gate (Lesson #15). 12-Q NL-query harness vs `gpt-oss:20b` @ MS-S1 (`run_benchmark.py --warm`), offline oracle 65 passed immediately prior. **Result: 11/12 correct (was 10/12 in AC-8) · anti-hallucination 12/12 HELD · p50 15.5s / p95 39.0s.** Headline (AC-1 live): nl-08 + nl-11 both flipped correct on the deterministic structured lens (`result_count 7`, max `96.5 °C`, top `Battery Bank A` from the execute-stage `AggregateResult`, not phrase prose) — model emits `operation:max` not `list` and invents no `resolve` placeholder. Two honest notes: (1) lone miss = nl-01 (not an AC-9 target) — known simple-list filter-omission nondeterminism, zero fabrication, out of PLAN-0026 scope, offline gold green → not a Phase-A regression; (2) this run hit the right result via the model's own `unit=celsius` filter (`measured_kind:null`) so the coherence seam had nothing to rewrite — the seam is the safety net proven by the offline oracle (AC-7), both routes yield the identical grounded result. **Verdict: AC-9 PASS.** Recorded as a RESULTS.md addendum; `--dump-json` evidence gitignored at `.claude/benchmark-results/2026-06-16-nl-query-ac9.jsonl`. PLAN-0026 now fully closed incl. the optional live re-verify | `c16778d` (#332, content `dc65425`) / `benchmarks/nl_query_feasibility/RESULTS.md` |
| 2026-06-15 | **PLAN-0026 COMPLETE — ADR-0021 (metric-kind typed ontology semantics) AUTHORED→ACCEPTED then Phase A (`measured_kind`) SHIPPED; PLAN archived to `done/` (#327–#330, `b53e631`, session 61)** — closes PLAN-0026 end-to-end (the principled fix Phase B could only approximate). Cray decisions: Gate-1 = **T2** (NL-query is the moat wedge), Gate-2/SD-2 = **Path B** (kind↔unit binding in the ontology → a new ADR); cross-check confirmed **(b) over (c)** ((c) over-scope now per Rule of Three + ADR-008 D3, and (b) reuses entirely into (c)). **ADR-0021 ("classify, don't synthesize"):** Cowork-authored (ADR-009 D1) → Code committed Proposed (#327, `a102b9d`) → Cray ratified Accepted (#328, `4423a22`); construct **(b)** QUDT-style quantity-kind ⟂ unit typed pair (`quantity_bindings`) over (a) per-enum-value map and (c) composite; (c) is a **triggered successor** (ADR-016 procedure engine + ≥3 verticals); amends ADR-008 D3. **Phase A (steps 6–7, #329 `37f62a7`; `bcbb62d`+`7f72181`):** step 6 — `measured_kind` enum (temperature|frequency) + object-level `quantity_bindings` on OperationalEvent, admitted by `ontology_schema.json` + parsed into `ontology_meta`, synthetic data tagged (7/2/2), emitted across all 5 artifacts, D6 L2 validator check, ORM + Alembic `0003` column (DB↔DDL parity via `test_schema_parity`); step 7 — `StructuredQuery.measured_kind` (translate LLM **classifies** the kind, the coherence seam **synthesizes** the precise `unit` from the binding, **superseding** Phase B dominant-unit per IN-1; no kind → dominant fallback, classified-but-absent → clarify, never fabricate). Distinguishes "highest frequency" from "highest temperature". Suite 1535/22; ruff+ruff-format+mypy clean; 12/12 anti-hallucination preserved; offline oracle re-pointed to a classified `measured_kind`; 6 new tests (4 engine + 2 validator). PLAN-0026 → `done/` (#330, `0a1427e`/`b53e631`). No gated NL-query work remains | `b53e631` (#327/#328/#329/#330) / `docs/adr/0021-metric-kind-typed-ontology-semantics.md` + `services/engine/nl_query.py` + `docs/plans/done/0026-nl-query-aggregate-metric-semantics.md` |
| 2026-06-15 | **PLAN-0026 (NL-query aggregate metric-semantics) AUTHORED+RATIFIED+MERGED (#321) then Phase B (deterministic rewrite seam) MERGED (#322, `19eeb21`, session 60)** — closes the filter-omission-on-aggregate-superlative gap PLAN-0024 left open (nl-08/nl-11). Diagnosis (Cray-directed): a 4-model MS-S1 sweep + a 3-variant prompt escalation both NEGATIVE → it's a typed-query-on-untyped-metric data-model problem, not model/prompt (two external LLMs concurred). Phase B = a post-translate rewrite seam in `nl_query.py`: `group_by` inference for "which <entity>" superlatives (AC-2, reshape-only) + a heterogeneous-aggregate coherence rewrite composing the dominant-unit filter in the engine (AC-3, model never re-supplies it = v2-regression-proof) + a clarify-not-silent-no-data guard (AC-4) + `NlAnswer.outcome: Literal["answered","no_data","clarify"]` (SD-1, Cray-approved). Offline oracle feeds the model's known-bad `{filters:[], operation:max, group_by:null}` and asserts the seam → `result_count==7`, value 96.5, top "Battery Bank A" structurally (not phrase-rescued). Suite 1527/22; ruff+mypy clean; anti-hallucination 12/12 preserved (AC-5); one `# noqa: C901` justified on the orchestrator. Governance: Cray "governed-first" → `plan-drafter` G2-denied → Cowork (ungated) authored → Code committed #321 → Cray ratified Proposed→Accepted → Phase B #322. Phase A (`measured_kind` ontology enum, the principled kind-word fix) GATED on the T2-vs-T3 roadmap call + SD-2's ADR; PLAN stays ACTIVE (not `done/`) | `19eeb21` (#321/#322) / `services/engine/nl_query.py` + `docs/plans/0026-nl-query-aggregate-metric-semantics.md` |
| 2026-06-15 | **PLAN-0024 (NL-query T2 engine enrichment) SHIPPED — engine half of the T2 wedge (#316 plan / #317 engine, `f4aa7fe`, session 59)** — `StructuredQuery` gains `max/min/avg/sum` (+ optional `group_by`) computed in the deterministic execute stage + a new `NlAnswer.aggregate` grounding receipt (never the phrase LLM), plus a `NameResolve` cross-type name→id descriptor (resolve-then-filter; `object_type` stays single/enum-constrained, group keys relabelled id→title); translate prompt now requires the implied filter + exact enum grounding. Gold ceiling cases nl-08/09/10/11 moved onto the deterministic structured-result lens (`_aggregate_ok`). Anti-hallucination AC-5 preserved (empty/no-numeric/unresolved short-circuit to no-records). 11 new offline tests; suite 1511/22 (+30); ruff+mypy clean. Governance: Cray scoped engine-only (UI→PLAN-0025, SD-1 deferred) → `plan-drafter` authored PLAN-0024 → ungated Cowork placed the file (G2 denied all in-harness Code writes) → Code committed #316 → merged → Code executed #317; SD-1 done as the recommended pre-step; one L1 loop-detect resolved by a Cray-approved counter reset, no Bash | `f4aa7fe` (#316/#317) / `services/engine/nl_query.py` + `docs/plans/done/0024-nl-query-t2-engine-enrichment.md` |
| 2026-06-14 | **Two backlog quick-wins SHIPPED (Code-solo, #311 + #312, `9595d3e`, session 58)** — cleared after the audit-framework arc closed; a separate small harness-tooling batch. **#311** (`f2ee579`, `test(stop-classifier):`): 3 "dispatch discriminator" gold cases added to `benchmarks/stop_classifier/gold.yaml` (20→23) pinning the surfaced-vs-ratified distinction the local classifier got wrong in s57 (over-fired `plan-drafter` on ADR/PLAN mentions while formality was a PENDING Cray decision — 2 cases) and right in s58 (post-ratification dispatch correct); 2 `pause` negatives + 1 `dispatch` positive, safety-weighted (spurious dispatch = HARD FAIL); offline test green (4 passed); live re-score pending Cray go; RESULTS.md addendum (recorded 2026-06-12 run predates the cases). **#312** (`9595d3e`, `fix(handoffs):`, PLAN-004 Phase B): handoff-validator warning-swallow bug fixed — `_schema.py::_build()` discarded its `errors` list on the otherwise-valid path so `_check_unknown()` WARNINGs were unreachable; `Frontmatter` gains `warnings`, `validate_file()` surfaces it, CLI prints it (precommit unchanged); regression tests strengthened; `tests/handoffs/` 573 passed / 2 skipped; ruff + mypy clean | `9595d3e` (#311/#312) / `benchmarks/stop_classifier/gold.yaml` + `tools/handoffs/_schema.py` |
| 2026-06-14 | **PLAN-0023 (PDPA RoPA-lite, step-2 of audit-framework-prep) SHIPPED (#308 PLAN + #309 deliverables, `afea6b3`, session 58)** — two tracked deliverables: reusable RoPA-lite template (`docs/conventions/partner-ropa-lite.md`, canonical) + NPD synthetic example (`docs/strategy/public/partner-sim-run1-ropa-example.md`, SYNTHETIC), each RoPA slot annotated with a data-quality/lineage hook; example's DSR/lineage→ADR-011 section maps 4 gaps→implications (PII-in-free-text→log-by-reference; scattered actor identity→actor unification; PK reuse + NTP drift→lineage/valid-from + ordering; under-recording→completeness-not-assumed). Governance: Cray ratified PLAN formality (3 decisions) → `plan-drafter` subagent authored PLAN-0023 (ADR-013 D1) → Code committed (#308, ADR-009 D2) → Code executed deliverables Code-direct (#309); PLAN archived to `done/`. SD-1 kept (AC-6 in-PLAN). ADR-011 still gated on a real partner — synthetic run INFORMS but never triggers PLAN-0005 §8.1 (ADR-0020 R3). Carried open: SD-4/SD-5/OQ-A | `afea6b3` (#308/#309) / `docs/conventions/partner-ropa-lite.md` + `docs/strategy/public/partner-sim-run1-ropa-example.md` |
| 2026-06-13 | **ADR-0020 (partner-sim venue) RATIFIED Proposed→Accepted (#302, `4d1347b`, session 57)** — Cray ratified in-session ("เอาตาม Cowork ทุกข้อ"); all four venue SDs + dispatch-SD-1 accepted per Cowork rec (Cowork-authored fold per ADR-009 D1, Code R2-reviewed + committed). SD-1 N=3 (→D2/R2); SD-2 one-project-per-business-type (→D4; R-PS4 reframed as a guard); SD-3 size/region/maturity enums + run-1 default energy·mid·th-regional·mixed-legacy (→D3 input); SD-4 "what we refused to share" ratified-required (→D3 output). R1/R2/R3 substance unchanged (#300 errata settled those). Instruction file reconciled same PR (6 ratification-pending markers → ratified; Code-amends-conventions, ADR-009 D2). dispatch-SD-1 (gitignored): one-pager sector-callout forbidden-action note trimmed, R1-clean seed untouched. Venue now ACCEPTED guarded-trial (R-PS1..R-PS4) — live action is Cray's (launch energy run-1) | `4d1347b` (#302) / `docs/adr/0020-partner-sim-venue.md` + `docs/conventions/partnersim_project_instructions.md` |

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
- [ ] **A1 — verify+reshape governance demo (B-γ moat successor).** The heaviest moat-proof: prove the moat IS governance — verify an LLM step's output for semantic consistency + reshape to the next step's contract (what arm (c) structurally lacks; ADR-016 area; the B-3 REPORT forward-points to it). **Scope together with the Phase-2 governed-entity-resolution ADR** — one ADR-016-area construct, not two overlapping ADRs. *(folded from §7 handoff, s67)*
- [ ] **A2 — equal-rubric arm-(a) re-grade.** Grade arm (a) on arm (c)'s `_reduced_expected` for a true apples-to-apples number (removes the grading asymmetry the B-3 REPORT discloses). Small, **offline, reuses `benchmarks/procedure_comparison/regrade.py`**. *(folded from §7 handoff, s67)*
- [ ] **ORM-emitter per-vertical layout (B1-DP-1 follow-up; Cray-deferred s67).** B1 (PLAN-0031, #370) ships the ORM emitter writing energy's ORM to the **committed** `services/db/models.py` (via `code_generator._ORM_COMMITTED_DEST`) — the gitignored `verticals/<ns>/generated/` cannot host a runtime dependency. When a **2nd vertical needs its own ORM** (the Rule-of-Three trigger), decide the per-vertical layout: extend `_ORM_COMMITTED_DEST` to per-vertical committed modules **vs** un-ignore a per-vertical `generated/orm.py` (gitignore negation) + re-export. Premature to design now (one ORM today). *(Cray-deferred 2026-06-18)*
- [ ] **G2 drafting-friction root-fix (parked s63; hit AGAIN s66 + s67).** Exempt the plan-drafter's *uncommitted-draft* write from the G2 always-pause (the Stop-hook auto-dispatch tells you to spawn plan-drafter, then the PreToolUse arm denies the very write — and it over-fires on non-new-plan tasks like the s67 ratify-flip). Worth a harness-improvement batch. *(folded from §7 handoff, s67)*
- [ ] **Promote the "proceed vs Cowork-dispatch-file" routing standard (un-promoted since s63).** The captured routing framework (solid + just-needs-perspective → proceed/approve; might-have-gaps OR needs-creative-ideas → Cowork dispatch file) → promote from private memory to a `docs/conventions/` standard. *(folded from §7 handoff, s67)*
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
