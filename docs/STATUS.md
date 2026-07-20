---
last_updated: 2026-07-20T16:32:23+07:00
session: 155
current_batch: "s153-155 — #822 demo-beat runbook §3c (config-pin fail-closed as Beat 06); s154 Cerebras-KB strategy read (no commits, 4 verdicts confirmed vs the real article); s155 #823 fix(ui) operator confidence badge REMOVED from both cards (story scene-2 + View-B live rec.confidence)."
current_actor: code
blocked_on: "Nothing blocking. main=4edfa3f; 0 open PRs. loop-dispatcher DISABLED; MS-S1 idle/COLD (zero calls across s153/154/155)."
next_action: "Rehearse the demo on 8101 (staged run fresh, dated today); then Cray's call among: predict-beat minimal increment (advisory-only free, routing-affecting reopens ADR-0019), read-path governance on /query (15 ungoverned endpoints; real cost = a Cray design call on read events entering the globally-serialized O(n) audit chain), the PLAN-0076 T1 gate-seam PLAN (trigger MET since s151), and the AT-2 stale-N doc-drift cleanup."
head_commit: 4edfa3f
recent_commits: [4edfa3f, ffb251b, f09cc99, d8057fb, b1d7f5a, b45f5c4, 90a2afb, 0248ec1, 1b0184e, 0e0d12f]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Sessions 153 + 154 + 155, 2026-07-20 (head_commit `a53c6ed` → `4edfa3f`) —
> the demo-beat runbook staged (#822), a strategy read that CUT the tempting
> part (s154, zero commits), and the operator confidence badge REMOVED from
> both cards that carried it (#823).** **(s153) Two docs PRs, no code.** **#821
> (`0248ec1` → merge `b45f5c4`, `docs(status)`)** was a housekeeping prune:
> the "Standard partner-intake form" Active TODO CLOSED (the deliverable
> exists and is canonical at `docs/conventions/partner-intake-form.md:8`; its
> per-vertical generalization is deferred to Rule of Three **BY DESIGN, not
> incomplete**), plus the stale `ADR-011+` / `PLAN-002 (>=ADR-014)` pointers
> dropped from Next Steps 1 and 3 — Next Steps had been **contradicting Active
> TODOs two sections up** (both were already corrected at s141). It
> deliberately did NOT bump session/head_commit/recent_commits (pure prune, Q4
> semantics), which is why s152 stayed the last real reconcile. **#822
> (`90a2afb` → merge `d8057fb`, `docs(runbook)`)** is the SUBSTANTIVE one and
> had never been reflected in STATUS until now: `docs/runbooks/run-oct-demo.md`
> §3c stages the **config-pin fail-closed refusal as a deliberate demo beat
> (Beat 06)** per PLAN-0047 Step 6 — the refusal is the product, so it gets
> rehearsed, not hidden. Both PRs sat blocked mid-session on a GitHub-Actions
> outage and landed when CI recovered (~09:34 +07).
> **(s154) ZERO repo commits — strategic analysis only.** Cray brought the
> Cerebras enterprise-knowledge-base article and asked whether vero-lite should
> adopt that approach to grow beyond governance into org-wide monitoring +
> prediction + warning-with-alternatives. Code read **ADR-0032 first** (the §2
> mandated pre-strategic read), then ran 4 read-only specialists in parallel,
> all grounded `file:line` against code. Verdicts: (1) predict+warn+alternatives
> is **NOT a new direction** — it is OCT feature 3 / Shape-1, passing the D6 fit
> filter IF prediction stays **deterministic**; (2) a KB over vero-lite's OWN
> governed artifacts is **D3 Shape-2 fuel verbatim** → pilot-gated by OQ-1; (3)
> org-wide Slack/wiki ingestion is the only genuinely new part **and the part to
> CUT** (fails D6 ~0/4, hits the named refused archetype, DPO-veto surface); (4)
> the surviving reframe = **"governed retrieval over the decision record — an
> answer an auditor accepts"**. The live blog URL 500'd everywhere, so Cray
> saved the page manually and Code re-verified the digest-based analysis against
> the real article: **all 4 verdicts `confirmed — prior intact`**, deltas were
> refinements only. Highest-value delta: the blog gives its authn/authz/audit
> layer ONE bullet and zero design detail — **retrieval quality is the published
> commodity; governance OF retrieval is the uncovered lane.** Artifacts are
> gitignored under `docs/research/private/cerebras/`.
> **(s155, this session) `next-work-analyst` + the badge removal (#823,
> `fix(ui)`).** A full 4-agent Explore fan-out ranked post-rehearsal work; Cray
> commissioned item #1. **#823 (`f09cc99` + `ffb251b` → merge `4edfa3f`) removed
> the operator-facing confidence badge from BOTH cards that carried it**,
> executing the already-ratified demo-card trust shape
> (`docs/plans/done/0035-governed-action-verify-reshape-build.md:591-602`,
> Cray-approved s74, re-recorded s142, cited by ADR-0030: "No operator-facing
> confidence badge"). `f09cc99` removed the hardcoded "Confidence 86%" + meter
> from the story-mode scene-2 governed-action card and the same number from the
> proposal-card meta; **`ffb251b` removed the same badge from the View-B
> "Anomaly & Decision" card, where it was driven by a LIVE `rec.confidence` —
> the more load-bearing instance**, since that file is the operator
> recommendation card the decision actually names. **KEPT by design:** confidence
> inside the reasoning trace (trace-only is the point), the fault-mode `AI 0.41
> ↓ → rule fail-safe` badge (it narrates the reroute MECHANISM, not a self-graded
> score), and the DAG task-detail row (engine-view). `.dc-metarow` collapsed from
> a 2-column grid to 1 so the handler fills the row rather than stranding a dead
> half; orphaned `.gc-conf-top` / `.dc-conf-top` / `.dc-conf-val` rules removed;
> comments at every site cite the decision so the badge is not reintroduced.
> Files: `view-story.js`, `view-anomaly.js`, `story.css`, `views.css`,
> `index.html` (cache tokens bumped) — **static assets only**, no engine/API/
> contract change, ADR-007 D2 envelope untouched. **Verification:** full offline
> suite **2915 passed / 7 skipped** on each commit AND re-run on the merge commit
> `4edfa3f` (CI is PR-only, so the merge commit is otherwise never tested); mypy
> clean (97 files); ruff clean; CI `gate` PASS on #823. Live browser check on
> port 8101 with the connection strip reading **`LIVE`** (not `degraded`): the
> View-B card rendered through the real `decisionCard()` path with a fixture
> deliberately carrying `confidence: 0.86` — proving the badge is gone **even
> when the signal IS present**; `.dc-handler` measured 414/414 px against its row.
> **Four claim-vs-code corrections surfaced by the grounding pass (the session's
> durable finding):** **(a)** the s154 research note recommended running a
> naive-RAG comparison "before building anything", but **PLAN-0027 ALREADY ran
> it** (scored 2026-06-16, `benchmarks/procedure_baseline/REPORT.md:697-771`) and
> the answer is that arm (c) lean RAG **TIES** arm (a) governed on entity+action
> accuracy (97.5% vs 97.5–100%) at **3–15x lower latency** — the moat claim was
> already relocated OFF raw accuracy ONTO the governance layer; **(b)** "the
> actions router is fully governed" is an **overstatement** — `append_audit` is
> called once in a failure-alert helper, approve/execute never call it, and that
> router's own GET endpoints are as ungoverned as `/query`; **(c)** the
> "ADR-0031 tripwire" cited for a learned forecaster is the **wrong ADR** —
> ADR-0031's tripwires are eval/open-StepKind/untyped/enum-widening, while the
> real determinism line is **ADR-0019:50-57 + ADR-010 IN-3**, and a deterministic
> trend projection sits on the **PERMITTED** side so long as it stays advisory;
> **(d)** a 4th AT-2 signature is currently **unbuildable** — no vertical has the
> substrate (energy + aquaculture are AT-1/AT-1b with no principals, no SoD, zero
> money/authority ontology fields; vet_clinic is a parked README) — and ADR-0032
> D1/D6 argues against scoping one absent a named partner. **Also flagged for the
> demo:** the UI **silently serves MOCK data on any backend error**
> (`services/api/static/assets/api.js:37-39` routes any non-ok/non-JSON response
> to `fallback()`), so a rehearsal can pass entirely against fake data — **the
> only tell is the connection strip.** Post-merge: main=`4edfa3f`; 0 open PRs;
> loop-dispatcher DISABLED; MS-S1 idle/COLD (zero calls across all three
> sessions). Commits: `0248ec1` (#821) → `b45f5c4` (#821 merge) → `90a2afb`
> (#822) → `b1d7f5a` → `d8057fb` (#822 merge) → `f09cc99` → `ffb251b` (#823) →
> `4edfa3f` (HEAD, #823 merge).

> **Session 152, 2026-07-19 (head_commit `9422c40` → `a53c6ed`) — PLAN-0083
> (fix option c1) BUILT + verified + archived: the procurement ontology↔CSV
> column drift is CLOSED at the adapter seam (#818).** The `FastenalCsvAdapter`
> now translates raw Fastenal CSV columns → canonical ontology names via
> `_COLUMN_RENAMES` on the `fetch_objects` path — the type key
> `Asset`→`Equipment` (SD-1) plus columns `part_id`→`part_no`,
> `price_thb`→`price`, `asset_id`→`equipment_id`, `site`→`site_id`,
> `lead_time_days`→`lead_time`, and `PurchaseOrder.asset_id`→`equipment_id`
> (SD-4a); the ฿-columns (`total_thb`/`min_thb`/`max_thb`) are DEFERRED raw
> (SD-4b). So every consumer now sees ONE canonical vocabulary (the ontology's),
> closing the bring-your-own-data seam. **Rides under ADR-016's LOCKED boundary**
> ("the mapping layer absorbs source diversity; connectors-in-the-procedure OUT")
> — **no new ADR, no ontology YAML edit, no generated regen, no `services/`
> engine edit** (ADR-0023 zero-core-edit; diff = adapter + vertical + tests only).
> A new coverage tripwire (`test_fastenal_adapter_canonical_coverage.py`) pins
> per-type set-equality + required-props + rename-target ontology validity + the
> type-key + the SD-4b ฿-defer, proven non-vacuous EMPIRICALLY (dropped a rename
> → RED → reverted). Cray COMMISSIONED C3 this session via `next-work-analyst`
> (which ranked the drift item), then ratified (c1) + SD-1..SD-4 via
> AskUserQuestion. **R2 caught** that the PLAN under-scoped
> `governance_audit.py:177/179` (reads the renamed PO columns off the adapter) —
> added, within AC-5 scope. **Verification:** full offline suite **2915 passed /
> 7 skipped** (baseline 2896 + 19 tripwire); `mypy --strict services/ verticals/`
> clean (142 files); ruff clean; CI gate PASS on #818. Deterministic-offline;
> MS-S1 never called; dev Postgres UP (localhost:5442). Post-merge: main=`5140ee3`;
> 0 open PRs; loop-dispatcher DISABLED. Also **#816** pruned the stale ORM-emitter
> Active-TODO (resolved by PLAN-0082 Step 4). Commits: `a211651` (#818 build) →
> `a53c6ed` (#818 merge) → `8b76da2` (#819 closeout) → `5140ee3` (HEAD, #819
> merge).

> **Session 151, 2026-07-19 (head_commit `043da3c` → `9422c40`) — PLAN-0081
> BUILT end to end: the `building_materials` governed-credit HERO — the **3rd
> AT-2 signature** (`building_materials.governed_credit_release`) — then
> PLAN-0079's tracking stub RETIRED (Step T3) + PLAN-0081 archived; governance
> behaviour UNCHANGED (#814).** Cray COMMISSIONED the hero this session
> (AskUserQuestion, after next-work-analyst ranked it #1); PLAN-0079 Step T1 was
> already fired (s146), so this session paid the BUILD. **The hero:** an
> exposure breach ABOVE the account's own `credit_limit_thb` routes the full
> governed AT-2 spine — per-entity band → `rule_gate` (KYC / overdue-AR /
> blacklist) → `doa_tier` human approval + SoD (sales requests, credit-control
> approves); steps intake → judge → reshape → credit_gate → approve → fulfill;
> the ฿550,000 shipped breach routes mid-ladder (`ผจก.ควบคุมเครดิต`), demoing
> tiering not just the top. **The 3rd signature REUSES, it does not re-invent:**
> the money `doa_tier` ladder is reused UNCHANGED (no new gate kind, no new
> authority quantity) — only the criterion vocabulary grows (`ComplianceCriterion
> += {kyc, overdue_ar, blacklist}`). **The ADR-0025 D7 re-evaluation was
> PERFORMED at N=3** (verdict Cray-ratified: the generator stays deferred,
> `test_at2_signature_retrigger.py` re-arms at N=4). **Engine diff bounded** to
> the additive `ComplianceCriterion` block (`spec.py`) — the `Person` promotion
> was PLAN-0082's dependency (already on main), so this PR carried NO engine
> `Person` edit; principals parse into the shared `core.Person` and the
> one-`Person` guard holds. **Coordination:** the endpoint pin bumped 9 → 10
> procedures + the spec-less guard re-pointed to a fixture vertical
> (building_materials is no longer spec-less); the archetype catalog + map gained
> the 3rd AT-2 signature; new AC tests
> `tests/verticals/building_materials/test_governed_credit_hero.py`
> (AC-1/2/4/5/9 — the in-memory run reaches the `doa_tier` gate, `waiting_human`).
> **Closeout (AC-10):** PLAN-0079 tracking stub RETIRED (Step T3) → `done/`, its
> guard test `test_governed_credit_hero_tracking_guard.py` DELETED, the STATUS
> Active-TODO pointer retired; **PLAN-0076 T1's gate-seam trigger recorded MET**
> (its own process owns the seam PLAN — not opened here); PLAN-0081 archived →
> `done/` at 15/15 ACs + a Closeout Verification block. **Honest flag:**
> `DoaLadder` REQUIRES an `emergency_waiver` (ADR-0025 D3) and
> `RelaxableConstraint` is a closed enum AC-3 forbids extending, so the
> procurement-shaped waiver is reused (GUESS-marked, not exercised on the happy
> path). **Verification:** full offline suite **2896 passed / 7 skipped** (re-run
> on the merge commit `9422c40`); `mypy --strict services/ verticals/` clean;
> ruff clean; CI `gate` PASS — deterministic-offline, MS-S1 never called, no
> host-state. Post-merge: main=`9422c40`; 0 open PRs; loop-dispatcher DISABLED.
> Commits: `a46bef8` (#814) → `9422c40` (HEAD, #814 merge).

> **Sessions 149 + 150, 2026-07-19 (head_commit `0b67f76` → `043da3c`) —
> PLAN-0082 (the shared-ontology mechanism + `Person` promotion) BUILT
> end-to-end, then COMPLETE + archived, across both sessions (#801–812), with
> PLAN-0081 folded — and governance behaviour UNCHANGED throughout.** **The moat
> piece:** a shared `core` ontology home + an `imports:` grammar with cross-doc
> `core.<Type>` resolution + a `set`/`closed` type-system extension across all
> emitters + a shared `Person` (type + committed ORM + `person` table + Alembic
> migration) reconciled down to exactly ONE definition. **(s149 — build half,
> #801–808).** Filed PLAN-0082 `Status: Draft` (#801) + folded the SD-round
> (#802 — SD-F/G/H/I/K + OQ-1); **ADR-0033 Accepted (#803, `6dd6464`)** — the
> shared-ontology ADR + ADR-0008/0026 pointer notes, OQ-1=(a) JSONB. Steps 2–4:
> **#804** `ontology/core_v0.yaml` + the reserved `core` namespace + set/closed
> L1/L2; **#805** the Pydantic emitter (set→`frozenset` / closed→`extra=forbid`);
> **#806** the `imports:` grammar + qualified cross-doc `core.<Type>` resolution
> (no KeyError); **#807** set→JSONB across the SQL/ORM/JSON-Schema/TS emitters;
> **#808 (`5e45eb6`)** the committed shared Person ORM `services/db/person.py` +
> the `person` table + Alembic `0012` — RAN GREEN on dev Postgres. Additive
> throughout — zero shipped-behaviour change. **(s150 — reconciliation half,
> #809–812).** **Step 5 (#809)** reconciled the spec-layer `Person` onto the
> committed generated `core.Person` (SD-H=(a) = delete + re-export; Cray s150
> design = a1): the committed-dest mechanism was extended to the Pydantic emitter
> (`_PYDANTIC_COMMITTED_DEST["core"] → services/engine/procedures/person_model.py`),
> parallel to the committed ORM; the AC-4 one-`Person` grep guard was proven
> non-vacuous empirically. **A CI-scope miss caught + fixed:** the offline gate
> ran only the 3 changed files + engine/db tests, but CI runs `mypy services/`
> STRICT tree-wide — `--no-implicit-reexport` flagged 12 consumers of the plain
> re-export → fixed with the redundant-alias idiom (`import Person as Person`);
> lesson recorded (the offline gate must match CI scope). **Step 6 (#810)**
> migrated procurement + supply_chain onto the shared type (AC-5) + transformed
> the OQ-6 marker (AC-6). **Grounding collapsed the handoff's "LARGE dual-roster"
> work to SMALL:** AC-5's TYPE-unification was ALREADY satisfied by Step 5's
> re-export (every roster parses into the one shared `spec.Person`;
> `auth.py`/factory/`run.py` already read the shared seam — nothing to
> re-point). **AC-5 RE-SCOPE (Cray s150):** the "retire one of procurement's dual
> roster sources" clause was a MISREAD — `procedures.yaml` (the Thai SoD roster)
> and `person.csv` via `load_fastenal_principals` (the Fastenal LIVE-run demo
> roster) are DISTINCT demos, not redundant copies; retiring either deletes a
> demo (violates AC-5's own "verdicts may not change" bar). Neither retired,
> documented; classified **`superseded by new info`** (CLAUDE.md §6). The marker
> became a shared-type invariant (no re-arm at N=4), non-vacuity proven. **Step 7
> (#811, `e059303`)** — PLAN-0082 COMPLETE: all 7 ACs ticked against fresh
> on-disk evidence + a Closeout Verification block, `git mv` →
> `docs/plans/done/0082-*.md`. **PLAN-0081 fold (#812)** — SD-J=SPLIT resolved +
> executed: Step 9 shrunk to the `building_materials` residue, AC-7 re-pointed to
> PLAN-0082 AC-6, AC-12/13/14/15 → PLAN-0082 AC-1/2/3/4, OQ-1 → ADR-0033;
> **PLAN-0081 stays `Status: Draft`.** **Verification:** full offline suite
> **2888 passed / 7 skipped**, re-run on EACH merge commit; every existing
> SoD/tier/gate-resolve assertion UNMODIFIED. **OQ-2 (the `person`-table
> population story) stays OPEN + explicitly deferred** (the table ships empty,
> runtime roster-fed). **PLAN-0081 is UNBLOCKED** (Step 9 = land
> building_materials on the shared `Person`); the hero build stays uncommissioned
> beyond PLAN-0079's tracking stub. Post-merge: main=`043da3c`; 0 open PRs;
> loop-dispatcher DISABLED; MS-S1 idle/COLD (zero calls all session); dev
> Postgres UP (localhost:5442). Commits: `5e45eb6` (#808 merge, s149 tip) →
> `92f0019` (#809) → `c94d089` (#810) → `e059303` (#811) → `043da3c` (HEAD,
> #812 merge).

> _Rotation note (session-155 reconcile, 2026-07-20, `docs(status):`):
> **STATUS was THREE sessions behind** — #821 bumped only `last_updated` (a
> pure TODO prune, correctly excluded per Q4 semantics), so s152 was the last
> real reconcile. Frontmatter → `head_commit 4edfa3f` (the #823 `fix(ui)` merge,
> the newest SUBSTANTIVE commit — Q4 recipe `git log -1 --invert-grep
> --grep='^docs(status):'`). ONE COMBINED **Sessions 153 + 154 + 155** block was
> PREPENDED (house style, cf. "Sessions 147 + 148" / "149 + 150"): #822's demo-
> beat runbook §3c had never been reflected in STATUS, s154 shipped zero commits
> (Cerebras-KB strategy read), s155 shipped #823. So the OLDEST — the **Sessions
> 147 + 148** block (PLAN-0081 opened + reshaped #797/#798; PLAN-0080 closed out
> + archived #799) — rotated OUT (4-session window, now s153/154/155 + s152 +
> s151 + s149/150) to the rotation-archive BASE
> `docs/status-archive/2026-h1-status.md`. Recent Decisions gained ONE row
> (s153-155 batch) and so rotated its ONE OLDEST — the **s143** PLAN-0078 Phase-2
> PR-5 row (#784) — to the same base (10-row window). Prior rotation notes
> (through the session-152 reconcile) are consolidated here (R4). Per the
> STATUS.md Rotation Policy (R1/R2/R4)._

> _Older content rotates out of this file per the **STATUS.md Rotation Policy (R1-R7)** in [`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md) (Lesson #23): Current Focus keeps the 4 newest sessions (<=8 blocks); Recent Decisions keeps the last 10 rows. Rotated blocks/rows live in [`docs/status-archive/`](status-archive/) and git history (Tier 3). Layout — **two separate chains, both with letters ascending with time and the base holding the recent window**: the rotation archive `2026-h1b` → `c` → `d` → `e` → `f` → `2026-h1-status.md`, and the Current-Focus-only `2026-h1b` → `c` → `2026-h1-current-focus.md`. Rotations append to the two bases. **Grep the directory, not a filename** — the chain is one corpus and which file holds a given block is an artifact of where the ~192 KB R4 bar happened to fall. _[Chain created 2026-07-17 (s144): the single `2026-h1-status.md` had reached 592,577 B, 2.3x R4's cap, and the new guard (#789) forced the split.]_

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
| 2026-07-20 | **s153-155 — #822 `docs(runbook)` staged the config-pin fail-closed refusal as a deliberate demo beat (run-oct-demo.md §3c, Beat 06, PLAN-0047 Step 6); s154 ZERO commits (Cerebras-KB strategy read: predict+warn = existing Shape-1 IF deterministic, artifact-KB = D3 Shape-2 pilot-gated, org-wide ingestion CUT, reframe = "governed retrieval over the decision record"); #823 `fix(ui)` REMOVED the operator confidence badge from BOTH cards — story scene-2 (hardcoded 86%) and View-B `decisionCard()` (LIVE `rec.confidence`, the load-bearing one) — executing the ratified s74 trust shape.** Trace/fault-mode/DAG confidence KEPT by design. Static assets only; suite **2915/7** re-run on the merge commit `4edfa3f`; live 8101 check `LIVE` with a `confidence: 0.86` fixture. **4 claim-vs-code corrections:** naive-RAG comparison ALREADY run (PLAN-0027 — lean RAG TIES governed on accuracy at 3-15x lower latency) · "actions router fully governed" is overstated · the determinism line is ADR-0019:50-57 + ADR-010 IN-3, NOT ADR-0031 · a 4th AT-2 signature is UNBUILDABLE (no vertical has the substrate). Full narrative: the Sessions 153+154+155 CF block above | `4edfa3f` (HEAD, #823 merge) / `ffb251b` + `f09cc99` (badge removal) / `d8057fb` (#822 merge) / `b45f5c4` (#821 merge) / `docs/runbooks/run-oct-demo.md` §3c + `services/api/static/assets/view-anomaly.js` + `view-story.js` |
| 2026-07-19 | **s152 — PLAN-0083 (fix c1) BUILT + verified + archived (#818 `feat`, #819 `docs(plans)`): the procurement ontology↔CSV column drift CLOSED at the `FastenalCsvAdapter` seam — `_COLUMN_RENAMES` on the `fetch_objects` path maps raw Fastenal CSV → canonical ontology names (type key `Asset`→`Equipment` [SD-1] + 5 columns [`part_id`→`part_no`, `price_thb`→`price`, `asset_id`→`equipment_id`, `site`→`site_id`, `lead_time_days`→`lead_time`] + `PurchaseOrder.asset_id`→`equipment_id` [SD-4a]; ฿-columns DEFERRED raw [SD-4b]), so every consumer sees ONE canonical vocabulary.** Rides under ADR-016's LOCKED "mapping absorbs source diversity" boundary — zero-core-edit (no ADR / ontology YAML / regen / `services/` engine edit; ADR-0023), diff = adapter + vertical + tests only. A `test_fastenal_adapter_canonical_coverage.py` tripwire pins per-type set-equality + required-props + rename-target validity + the SD-4b ฿-defer, non-vacuous EMPIRICALLY (dropped a rename → RED → reverted); R2 added the under-scoped `governance_audit.py:177/179`. Suite **2915/7** (2896 + 19); mypy strict + ruff clean; CI gate PASS on #818. Full narrative: the Session-152 CF block above | `a53c6ed` (#818 merge) / `a211651` (build) / `5140ee3` (HEAD, #819 merge) / `docs/plans/done/0083-*.md` (archived) + `tests/verticals/procurement/test_fastenal_adapter_canonical_coverage.py` |
| 2026-07-19 | **s151 — PLAN-0081 BUILT end to end (#814, `feat(building_materials)`): the `building_materials` governed-credit HERO — the 3rd AT-2 signature (`building_materials.governed_credit_release`), Cray-commissioned this session. An exposure breach above the account's own `credit_limit_thb` routes the full governed AT-2 spine (per-entity band → `rule_gate` KYC/overdue-AR/blacklist → `doa_tier` approval + SoD); the ฿550,000 breach routes mid-ladder.** The 3rd signature REUSES the money `doa_tier` ladder UNCHANGED (no new gate kind / authority quantity) — only `ComplianceCriterion += {kyc, overdue_ar, blacklist}` grows; engine diff bounded to that additive `spec.py` block (the `Person` promotion was PLAN-0082's, already on main). **ADR-0025 D7 re-eval PERFORMED at N=3** (Cray-ratified: generator stays deferred, marker re-arms N=4). Closeout: PLAN-0079 tracking stub RETIRED (Step T3) + guard test DELETED; PLAN-0076 T1 gate-seam trigger recorded MET (seam PLAN un-opened); PLAN-0081 archived at 15/15 ACs. Suite **2896/7** re-run on the merge commit `9422c40`; mypy strict + ruff clean. Full narrative: the Session-151 CF block above | `9422c40` (HEAD, #814 merge) / `a46bef8` (build) / `docs/plans/done/0081-*.md` (archived, 15/15) + `tests/verticals/building_materials/test_governed_credit_hero.py` |
| 2026-07-19 | **s150 — PLAN-0082 COMPLETE + archived (Steps 5-7, #809-811) + PLAN-0081 fold (#812): the reconciliation half of the shared-ontology arc — spec-layer `Person` reconciled to ONE generated `core.Person` (#809, SD-H=(a) + `_PYDANTIC_COMMITTED_DEST`), procurement+supply_chain migrated + OQ-6 marker transformed (#810), PLAN closed out at 7/7 ACs + archived (#811); PLAN-0081 folded (SD-J=SPLIT resolved, Step 9 shrunk).** AC-5 dual-roster "retire one" RE-SCOPED (misread — distinct demos, neither retired). CI-scope lesson (mypy strict re-export). OQ-2 deferred. Full narrative: the Sessions 149+150 CF block above | `043da3c` (HEAD, #812) / `e059303` (#811) / `docs/plans/done/0082-*.md` |
| 2026-07-18 | **s149 — PLAN-0082 shared-ontology mechanism BUILT (Steps 2-4 behind ADR-0033, #803-808): ADR-0033 Accepted (shared `core` home + `imports:` grammar + set/closed types + shared Person committed-ORM contract); `core_v0.yaml` + set/closed L1/L2 (#804), Pydantic emitter (#805), imports/cross-doc resolution (#806), set→JSONB emitters (#807), committed Person ORM + `person` table + Alembic 0012 migration ran green (#808).** Additive — zero shipped-behaviour change. Full narrative: the Sessions 149+150 CF block above | `5e45eb6` (#808) / `6dd6464` (#803) / `ontology/core_v0.yaml` + `services/db/person.py` + `alembic/versions/0012_person_table.py` |
| 2026-07-18 | **s148 — PLAN-0080 COMPLETE + archived (#799, `docs(plans)`): the trace-attribution + `ui.md` PLAN (shipped end-to-end s146 via #794/#795) closed out — Status → Complete, all 9 ACs re-verified against `main` on a fresh disk read (each with file:line evidence) + ticked, `git mv` → `docs/plans/done/`.** AC-5 ticked as-scoped (**F-4**: only the `TRACE` entries fed to `O.reasoningTrace` are canonical-normalized; PROP-card / KIND_BADGE / DAG `kind:` tokens are separate local vocabularies the AC carved out). Findings **F-1/F-2/F-3 + OQ-1 stay recorded, NOT closed**; no code/behaviour change. Full narrative: the Sessions-147+148 CF block above | `0b67f76` (HEAD, #799 merge) / `81f307b` (closeout) / `docs/plans/done/0080-*.md` (COMPLETE, archived) |
| 2026-07-18 | **s147 — PLAN-0081 arc (#797 Draft + #798 SD-E=(b-ii) fold / SD-J=SPLIT ratified, both `docs(plans)`): #797 filed the `building_materials` governed-credit HERO BUILD plan as `Status: Draft` (Cray COMMISSIONED via PLAN-0079 T1 — SD-1=trip AT-2 N=3 in-PLAN, SD-2=ride `measured_value`).** #798 folded Cray's **SD-E=(b-ii)** (promote `Person` to a NEW shared/core ADR-0008 `object_type` — the shipped codegen is strictly per-vertical, so b-ii INVENTS the mechanism) + ratified **SD-J=SPLIT** (b-ii → its OWN new PLAN + a preceding ADR-0008 grammar amendment as gate; PLAN-0081 Step 9 shrinks to the migration). New AC-12/13/14/15 + SD-F…SD-J + expanded OQ-1; **PLAN-0081 stays Draft — no code shipped.** Full narrative: the Sessions-147+148 CF block above | `fa4f6c6` (#798 merge) / `46a6ec2` (SD-E fold) / `e03e56f` (#797 Draft) / `docs/plans/0081-*.md` (Draft) |
| 2026-07-17 | **s146 — PLAN-0080 shipped end to end (#794 `feat(ui)` + #795 `docs(conventions)`): the reasoning-trace badge's substring sniff (`kind.includes('rule')`, mis-attributing 14/16 engine kinds) → ONE shared kind→{label,cls,actor} registry (`trace-kinds.js`, 23 kinds) read by BOTH the browser and an AST set-equality tripwire; colour=mechanism (theme.css UNCHANGED) + glyph=actor, unmapped kinds degrade visibly. + canonical `docs/conventions/ui.md` (11 anchored items).** **F-4:** a live probe refuted the offline "engine-only emitter" claim — `verticals/` seed executors emit `query` unmapped 9/9 → kind #23, scan root widened. Suite **2860/7** on BOTH merge commits. Full narrative: the Session-146 CF block above | `8737b0a` (#795 merge) / `6a2a42d` (#794) / `services/api/static/assets/trace-kinds.js` + `tests/api/test_trace_kind_labels.py` + `docs/conventions/ui.md` |
| 2026-07-17 | **s144 — the R4 arc CLOSED end to end (#789 guard → #791 + #792 splits): a ratified rule that had NO mechanism now has one, and every archive sits under the ~192 KB TRIGGER — not merely the cap — for the first time.** R4's own responsibility-matrix guard column read `—` where R1/R7 read `fail`; the rotation archive had rotted to **592,577 B = 2.26x the cap**. #789 shipped `tools/check_archive_size.py` (warn >192 KB, **fail >256 KB**, `files:`-scoped hook) GREEN **by design**; the BINDING live assertion (`test_live_archives_are_within_cap`) could only land in #791 **after** the split — a guard whose live assertion is RED cannot merge into a protected main. **Five-file c/d/e/f chain, not four** (a 4-way split lands one file at ~97% of the trigger). #792 split current-focus AND **recorded Cray's naming rule as CANON** — letters ascend with time, the base holds the recent window; **grep the archive dir, never cite a continuation by name**. Proofs DIFFER and say so: #791 = exact list equality (27 sections), #792 = multiset equality (30 blocks, deliberately reordered across files); both re-run AFTER pre-commit → *"equal except N trailing newlines, all stripped-equal"*, **NOT byte-identical**. Suite **2855/7** re-run on the merge commit itself. _[Concurrent session 145: #788 PLAN-0080 `Status: Draft` — SD-1/SD-2 UNRATIFIED, must NOT be executed, and `docs/conventions/ui.md` does NOT exist · #790 frontmatter-only bump, merged on Cray's instruction.]_ Full narrative: the Sessions-144+145 CF block above | `ce0f0a1` (HEAD, #792 merge) / `f00e4c7` (#791) / `b369fa6` (#789) / `694e8d7` (#788) / `tools/check_archive_size.py` + `.pre-commit-config.yaml` + `docs/runbooks/memory-architecture.md` (R4 matrix row `—` → `fail >256 KB` + the naming rule) + `docs/status-archive/**` (the c/d/e/f + b/c-cf chains) |
| 2026-07-17 | **s144 — PLAN-0078 COMPLETE at 12/12 ACs → `docs/plans/done/0078-transform-seed-migration.md` (#786, docs-only): a FAR smaller closeout than the s143 handoff predicted — 4 of the 6 open ACs (AC-7/8/9/12) were ALREADY SATISFIED on disk (unticked bookkeeping; each tick now cites its test by file:line, and AC-9 was re-verified INDEPENDENTLY rather than inherited from PR-4's R2 claim).** **AC-6 was the ONE genuine hole — and NOT the hole the PLAN described:** the predicted "Phase 2 shrinks the non-participant set" was FALSE on disk (PR-3/PR-4 only touched procedures already carrying a Phase-1 `enrich`) → classified **`superseded by new info`, NOT `was an error`** (CLAUDE.md §6) and pinned as DATA; the REAL hole was energy + aquaculture carrying no step-level `transform`-absence assertion anywhere. Both new tests proven non-vacuous **EMPIRICALLY** (probes reverted). **OQ-3 stays open; PLAN-0076 does NOT archive; F-PIN NOT closed** (L-4). Suite **2845/7** re-run on the merge commit itself. Full narrative: the Session-144 CF block above | `d8db032` (HEAD, #786 merge) / `49ff275` (sweep + ticks + `git mv`) / `docs/plans/done/0078-transform-seed-migration.md` (COMPLETE, archived) + `tests/**` (`test_derivation_pin.py:326` prediction pin + the energy/aquaculture transform census) |

## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13; guarded trial (parallel to ADR-012) — verdict **continue-with-adjustments**. Run 1 (energy, s93) + Run 2 (supply-chain, s94) both COMPLETE, S-checks all PASS against pre-committed oracles, no R-PS trigger fired; C-1..C-3 CONFIRMED → **no open partner-sim debt**. ADR-011 audit stays gated on a REAL partner conversation (R3: SYNTHETIC provenance INFORMS but never TRIGGERS it). Full record: `docs/adr/0020-*.md` + the gitignored run packages `docs/research/private/2026-07-02-partnersim-run{1,2}-*.md`. _(Full prior narrative — the ~8 schema-mismatch findings, both run details, cross-run synthesis — archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **Procurement vertical — GO + SHIPPED (PLAN-0036 Fastenal, Stage 1):** 4th vertical greenlit (s75); PLAN-0036 drafted + merged Draft (#412, `7a7c036`; SD-1…SD-5 confirm-all). Demo target = Fastenal Thailand (auto-parts / EEC); **hero** = asset-failure → governed emergency sourcing, **calm-path** = low-stock reorder. Stage 1 = a PLAN-only pure-config plugin on the ADR-016 engine (zero `services/` core edit; CQ-1 / ADR-0023). **Pitch** = asset-ontology-triggered governed sourcing (native ontology ADR-008 + engine ADR-016), NOT the commoditized "governed"/"cross-vertical" claims. Full record: `docs/plans/0036-*.md` + the s72 de-risk dossier `docs/research/private/2026-06-22-procurement-*.md` (5 files: spec-expressiveness, GTM, asset-aware incumbent scan, AI-sourcing teardown, platform-incumbent deepdive). _(Full prior narrative archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [ ] **AT-2 stale `N=2` / `N=3` signature counts — doc drift across three artifacts (surfaced s155).** The live value is **`N=3`, with the ADR-0025 D7 generator marker RE-ARMING at `N=4`** (Cray-ratified at the s151 PLAN-0081 re-eval). Stale counts survive in: **(1)** `services/engine/procedures/spec.py` comments — **ungated, fix freely**; **(2) ADR-0025 D7** and **(3) ADR-0032** — both **G1-gated Accepted-body edits**, so they route via `plan-drafter`, never a direct Code write. Only `tests/services/engine/procedures/test_at2_signature_retrigger.py` carries the correct `_RETRIGGER_N = 4`, so the *test* is the source of truth and nothing turns RED on the prose drift. _[Irony worth preserving: **ADR-0032's own Positive-consequences section claims it makes exactly this stale-N-count error class harder to reintroduce** — and it now carries that very drift.]_ *(s155; blocks nothing, but every stale count is a wrong premise for the next AT-2 scoping call.)*
- [ ] **PLAN-0075 follow-ons — homed by PLAN-0076 (`Status: Tracking`, filed #752, s133): T1, the ADR-0031 D3 gate-plugin seam (F-FACTORY), is now the ONLY open deferral — Step T2's F-PIN remainder CLOSED s143 (#784, PLAN-0078 PR-5).** _[T2 closed ≠ F-PIN closed: **F-PIN itself stays OPEN** (`docs/plans/done/0078-transform-seed-migration.md` L-4 — PLAN-0078 closed s144 COMPLETE at 12/12 and archived, but **no artifact records F-PIN closed**) — only T2's remainder fold-in closed, so **PLAN-0076 does NOT archive** and its guard stays ARMED.]_ A guardrail against the ADR-0031 OQ-4 deferral-rot precedent (s133 4-specialist panel); PLAN-0075 itself is **COMPLETE — all 13 ACs — and CLOSED → `docs/plans/done/0075-*.md`**. Full detail: `docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` — F-FACTORY `:61-127`. **Guard:** PLAN-0076's AC-6 presence guard-test (`tests/services/engine/procedures/test_at2_followon_tracking_guard.py`) turns the build RED on a premature archive-to-`done/` or a pruned STATUS pointer ("location≠tripwire; failing tests are the real anti-rot"). *(PLAN-0075 = #749/#751 → `done/`; PLAN-0076 = #752, `Status: Tracking`; T2 closed by #784.)*
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2) — open ONLY for the O-2 residue; every other leg is DONE + archived.** **Closed:** Q3 ontology data-binding (PLAN-0046) · the Q4 generic query executor (PLAN-0048) · the Q4 join/projection grammar (ADR-016 Q4 amendment #659 + PLAN-0061) · the per-vertical seed migration (PLAN-0062) · the per-entity `threshold_field` band arc (PLAN-0066/0067/0068/0070) · **Box-4 BUILT (PLAN-0071, AC-5 GREEN at N=4) + SURFACED IN THE HERO UI (PLAN-0073)** — all → `docs/plans/done/`. **The one OPEN residue:** procurement's `intake` is declared-expressible ✔ under shadow parity, but **production execution stays the co-existing `_SeedQuery` ✖ for derived fields** — `docs/plans/done/0062-per-vertical-seed-migration.md:348`, the SD-C co-exist decision `:54-60`, `:291-295`. **Now homed by the transform arc:** **PLAN-0077** (transform grammar, COMPLETE → `done/0077-*.md`) + **PLAN-0078** (**COMPLETE at 12/12 ACs, CLOSED s144 #786 → `done/0078-*.md`** — the Step-7 closeout swept AC-5/AC-6 and archived it; do NOT re-open) — the fold-in is named at `docs/plans/0076-*.md:170-174`, what stays seed-side at `docs/plans/done/0078-transform-seed-migration.md:150-155`. *(s84 strategy discussion; the Box-4 leg is DONE — the residue is the O-2 data-binding leg only.)*
- [ ] **Bounded/incremental chain verification (PLAN-0063 SD-4 follow-up, s118).** `GET /audit/verify` walks the WHOLE chain O(n) on demand — accepted at pilot scale, documented in the endpoint docstring (`services/api/routers/audit.py:13-16`). Future work = a checkpointed head / verify-since-anchor design; anchor storage ≈ external anchoring — **do not build without re-reading the tripwire: `docs/plans/done/0063-audit-chain-verification-surface.md:564` + `services/api/routers/audit.py:19`.** _[Corrected s141: this item used to say "ADR-011 tripwire territory" — **ADR-011 does not exist** (`docs/adr/` jumps 0010 → 0012; it is an earmark only); the tripwire text lives at the two anchors above.]_ *(s118; #688/#690)*
- [ ] **DEFERRED: a monotonic `sequence` column on `step_results` — the ROOT fix for `load_run`'s wall-clock ordering.** Needs a DB migration → its own PLAN (PLAN-0062-independent); none drafted. `ORDER BY created_at` is **unchanged by design**, so **the deferral STANDS**; both surviving orderings are **DISPLAY-ONLY**, so not urgent. Full detail — ROOT-vs-guard, why it is tolerable, the static AST guard holding the line: the module docstring of `tests/services/db/test_load_run_ordering_guard.py`, pointed to from both code sites. *(rehomed s142; s117; #678/#680/#684)*
- [ ] **Rock 4 — s84 deep research DELIVERED → O-sequence locked.** Cray locked **O-1 → O-3 → O-2 → O-4**. **O-1** (Box-4 ฿ pitch) **DONE** · **O-3 = ADR-0025 Accepted** · **O-4 = PARK** (agent-interop; `docs/adr/0032-*.md:169` D4 — option-only, un-park = a counterparty's *written* pull). **Remaining: O-2 only** (economic-impact facet + Q3 data-binding = Rock 3). Full detail: `docs/adr/0025-at2-managerial-layer.md:19` (O-sequence + Box-3 fit) + `:23-29` (the **evidence-asymmetry** finding — bullish ROI all vendor-authored, independent mostly skeptical — rehomed s142). *(s84 Cray ask)*
- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten. **Full table (all six rows + their triggers + where each lands): `docs/plans/done/0005-oct-engine-runtime-layer.md:390` §8.1** — which itself instructs this STATUS entry to be a pointer. *(per Cray note 2026-05-21)*
- [ ] **Demo card UX — "trust shape", NO operator confidence badge (s74 design, Cray-approved).** The operator card shows **what / grounded-why / approve gate** + a "show full reasoning trace" toggle; **no confidence badge** (`confidence_signal` is engine-internal QA, trace-only), and the **(B) first-class `verification` field is NOT needed** — SD-3 settles at (a). Full record + rationale + the reconsider-trigger: **`docs/plans/done/0035-governed-action-verify-reshape-build.md:576`** — the s142 post-archival amendment ANSWERING SD-3's Phase-2 question; `ADR-0030` cites it. *(Trigger: the next demo / UI round.)*
- [ ] **PLAN-004 Phase C — OPTIONAL POLISH (forward-declared; "may never land"):** HTML/markdown handoff dashboard under `docs/` + references-graph (mermaid dispatch chains) + `render_transcript.py` unified session export (PLAN-0004 §"Phase C"). *(Phase A + B both COMPLETE — session 35; the prior TODO's validator **warning-swallow bug was FIXED #312**, s58. Minor never-formally-scoped sub-ideas — README/`_rename-map` walk-exclusion, Cat G `references_*` autofix, OQ-2 effective-vs-authored `status:` dashboard flag — fold in only if Phase C lands. Reconciled 2026-06-16 s65 audit.)*
- [ ] **Custom Postgres image with extensions (pgvector / AGE / pg_trgm) — needs a fresh ADR number + a PLAN; neither drafted.** *[Corrected s141: **PLAN-002 does not exist** ("NOT yet drafted", `docs/plans/done/0005-oct-engine-runtime-layer.md:14`), and the old "≥ ADR-014" floor is **moot** — ADRs now run to 0032 and `0014-WITHDRAWN.md` exists.]* Context: **`docs/adr/0013-autonomy-axis-relocation.md:285-289`** (the floor-bump note) + **`docs/plans/done/0005-*.md:403`** (trigger: semantic + graph features).
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (low priority)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)

## Next Steps

1. **PLAN-0005 §8.1 revisit register** — remaining deferred-foundational simplifications at their batch boundaries (audit framework, mapping layer, ORM emitter, base-Postgres → the custom-Postgres image, registry discovery). _[Corrected s153: dropped the stale "→ ADR-011+" and "→ PLAN-002 (≥ADR-014)" pointers — **ADR-011 does not exist** (earmark only, per the Active TODO above) and **PLAN-002 was never drafted** with its ADR floor moot; each item's corrected status lives in Active TODOs.]_
2. **Partner-trial readiness gaps** — `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` awaits a dedicated Cray discussion.
3. **Deferred (backlog)** — PLAN-004 Phase C only (optional polish: handoff dashboard / references-graph / unified export — Phase B complete s35, warning-swallow fixed #312); the custom Postgres image (needs a fresh ADR number + a PLAN — neither drafted; see the Active TODO for the corrected framing).
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
