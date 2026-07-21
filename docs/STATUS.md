---
last_updated: 2026-07-21T15:59:22+07:00
session: 157
current_batch: "s157 — PLAN-0086 COMPLETE (#838): the timed manual scaffold of vertical #6 fleet_maintenance, narrative → governed pipeline in 27m39s hands-on (AC-7 lower-bound caveat); ADR-0025 D7 AT-2-generator deferral CANCELLED at N=4 (Cray-ratified)."
current_actor: code
blocked_on: "Nothing blocking. main=79358c6; 0 open PRs; suite re-run GREEN on the merge commit (2943/7); loop-dispatcher DISABLED; MS-S1 idle/COLD. PLAN-0086 still in docs/plans/ pending its closeout PR."
next_action: "⭐ PLAN-0086 closeout PR (git mv docs/plans/0086-*.md done/), then open the ADR-0025 D7 gate-plugin-seam / criterion-vocabulary extraction PLAN via plan-drafter (PLAN-0076 T1 owns it; new PLAN = G2-gated)."
head_commit: 79358c6
recent_commits: [79358c6, a2ef45e, 219a134, c8e871b, b1dab82, f8f17df, 06e165b, 254b8ca, 63009c3, 92a25cb]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 157, 2026-07-21 (head_commit `2f46fc9` → `79358c6`) — PLAN-0086
> COMPLETE: the AI-Transition **View-2** scaffolder run as a TIMED MANUAL
> baseline — a rambling, deliberately-dirtied customer monologue carried to a
> live, governed, human-gated pipeline on a 6th vertical (`fleet_maintenance`,
> #838), shipped with its measurement pack; and the ADR-0025 D7 AT-2-generator
> deferral CANCELLED at N=4.**
> **(the headline number — it MUST NOT be quoted without its caveat; AC-7 makes
> that binding.)** Narrative → governed pipeline in **27 minutes 39 seconds
> hands-on** (wall 43m17s minus 6m51s of customer-answer waits and 8m48s stopped
> on a governance escalation). **Caveat (AC-7, binding):** Code drafted the
> pre-dirtied narrative, so this is a **LOWER BOUND on true blind intake** —
> Cray's dirtying plus the four-question intake log partially restore validity,
> and it measures an operator with deep prior knowledge of this codebase.
> **(what shipped.)** `verticals/fleet_maintenance/` — an 8-file package
> HAND-WRITTEN from the `building_materials` template (`vero-lite new-vertical`
> was banned by the measurement protocol). Asset=Truck, Site=Depot; AT-2
> `governed_repair_approval`: intake → judge (per-truck repair ceiling) →
> reshape → quote_gate (`rule_gate`) → approve (money `doa_tier` + SoD) →
> fulfill. **First vertical shipping the PLAN-0085 gate advisory ON by default**
> (PLAN-0086 L-B — the parked gate explains itself on day one). Plus 14 tests,
> the 3 mandatory hand-wires, and an additive `ComplianceCriterion +=
> three_quote` engine change.
> **(ADR-0025 D7 — the AT-2-generator deferral is CANCELLED; Cray-ratified,
> typed.)** Shipping fleet fired `test_at2_signature_retrigger` at N=4. Code
> ESCALATED rather than patched — the marker says "re-argue it, do not just
> update this list", and the fix Code judged correct was also the fix that turned
> Code's own red green. Both readings went to Cray: by gate SHAPE fleet teaches
> nothing new (composition and authority quantity identical to
> `building_materials`'), but it is the FOURTH consecutive vertical to require an
> engine-level `ComplianceCriterion` extension — and repeated pressure on shared
> code is what Rule-of-Three actually watches. Cray's rationale: accept the cost
> now for future flexibility. The `len(signatures) < _RETRIGGER_N` guard is
> RETIRED and REPLACED (never deleted) by `test_at2_extraction_obligation_is_owned`
> (same module), which fails if PLAN-0076 — the standing owner via Step T1 — is
> archived or loses its record. **The extraction itself is NOT done — it needs
> its own PLAN, G2-gated, so `plan-drafter` must author it.** That is the most
> important open thread out of this session.
> **(the finding that outlives the number.)** Two of the four customer rules
> could NOT be fully encoded: the quote-comparison ฿ threshold has nowhere to
> live (a `rule_gate` criterion is pass/fail on a supplied signal and carries no
> threshold field, and ADR-0025 D4 forbids the amount in prose), and
> `EmergencyWaiver` has no fields for the emergency cap or the ratification
> window. Both are recorded in the question log and surfaced to readers in the
> vertical README as an explicit "stated but NOT enforced" table — a
> narrative→pipeline tool that silently dropped the un-modellable half would be
> worse than no tool.
> **Verification:** offline gate at execution HEAD **2943 passed / 7 skipped**,
> **re-run GREEN on the merge commit `79358c6` itself** (2943/7 — CI is PR-only,
> so the merge commit is otherwise never tested); baseline re-measured at
> `219a134` before the clock started (2927/7, matching the #833 figure —
> `confirmed — prior intact`); `mypy --strict services/` clean (98 files);
> `ruff check .` + `ruff format --check .` clean at CI scope; CI `gate` PASS on
> #838 (3m7s; 17 files, +1825/−40). **AC-4 by construction** — the diff touches ZERO files under the
> five existing verticals. Live: `run-b9c0804b52f0` parks `waiting_human` at
> `approve` with the advisory persisted (grounded fleet reasons, `model:
> deterministic`, no confidence key in the advisory), corroborated in the Monitor
> gate panel and confirmed by Cray. PLAN-0086 archives to `done/` in the
> follow-on closeout PR. Commits: `a2ef45e` (#838) → `79358c6` (HEAD, #838
> merge).

> **Session 156, 2026-07-21 (head_commit `25b31e2` → `2f46fc9`) — a morning
> map-label UI fix, a long-carried demo rehearsal finally PERFORMED (the
> PLAN-0084 closeout gate), and the AI-Transition View-1 / Rung-1 arc built
> end-to-end in ONE day: PLAN-0085 "Advisory Gate Recommendation" filed (#831)
> → all 5 SDs Cray-ratified (#832) → BUILT (#833) → closed out (#834).**
> **(morning UI fix — #829, `19f5caa`, `fix(ui)`.)** On the Operational Map
> (View A) the site label plate overlapped the rightmost asset satellite node;
> the plate moved BELOW the node (the asset fan is always the upper hemisphere),
> `view-map.js ?v=c39` — live-verified on 8101 (0 overlaps, strip LIVE).
> **(the rehearsal — the closeout gate.)** Cray performed the demo rehearsal
> (Beats 1-5 on 8101, incl. the new PLAN-0084 map→monitor opening beat) —
> carried s153→154→155, finally run, ratified "ok" = PASS. No commit: it IS the
> AC-4/closeout evidence for **#830** (`ad39774`, `docs(plans)`) — PLAN-0084
> closed out, all 9 ACs ticked with dated evidence, archived to `done/` (the
> PLAN was Draft, so Code closed it directly). (The rehearsal-artifact PREP +
> Beat-06 wording was corrected + republished, but that is a gitignored
> claude.ai working note, not a repo commit.) **(the two-view AI-Transition
> frame — Cray-opened after the rehearsal.)** Two views: (1) an LLM at the
> approval gate, (2) a narrative→pipeline scaffolder. Cray ratified a SEQUENCE —
> capture a discussion note → build View-1 (Rung 1) → reshape View-2 against
> Rung-1's result → build View-2 — under the umbrella thesis **AI Transition =
> governance human in/on-the-loop → first-stage AI automation**. Captured in the
> gitignored note
> `.claude/handoffs/session-156/2026-07-21-0851-code-session156-discussion-ai-transition-two-views.md`
> (binds nothing). **(PLAN-0085 — the View-1 / Rung-1 arc, filed → SDs → built →
> closed, one day.)** **#831** (`8809776`, `docs(plans)`) filed PLAN-0085
> "Advisory Gate Recommendation (AI-Transition Rung 1)" `Status: Draft` by
> `plan-drafter` (grounded by 3 Explore fan-outs + Code's OQ-1 read; the drafter
> corrected the dispatch twice, both re-verified at R2). **#832** (`d679036`,
> `docs(plans)`) — Step 0: all 5 SDs Cray-ratified (AskUserQuestion), every pick
> = the draft recommendation — **SD-1(b)** emit INSIDE the `doa_tier` gate
> propose path (ZERO hash change), **SD-2(b)** stub-first deterministic arm +
> opt-in live MS-S1 seam, **SD-3** all three procedures, **SD-4** gate-panel
> advisory block, **SD-5** new trace kind `advisory_recommendation` (actor
> `llm`). **#833 (`2f46fc9`, `feat(engine)`) BUILT:** an advisory recommendation
> with grounded reasons at procurement's `doa_tier` approval gate — **SHOWN,
> never routes** (the ADR-0019:50-57 fence, now CI-pinned: byte-identical
> approve audit advisory-on / off / exploding-builder). New module
> `services/engine/procedures/gate_advisory.py` (never-raise, ADR-0030 D5
> pattern), wired via `GovernanceActionExecutor` + the procurement `_executors`
> default; a Monitor gate-panel block (reasons, spark glyph, arm sublabel, NO
> score — the L-C/#823 trust shape) + the new trace kind + a PLAN-0080 tripwire
> pin. Suite **2927/7**, mypy/ruff clean, live-verified on 8101 (strip LIVE, the
> run parks with the advisory persisted). **#834** (`63009c3`, `docs(plans)`) —
> PLAN-0085 closeout: all 8 ACs ticked, runbook §3e added, archived to `done/`.
> Cray confirmed the live advisory and surfaced an UNPLANNED value — it doubles
> as an **onboarding aid** (a first-time operator reads a plain-language "why
> this is on my desk", reducing panic), recorded as a signal for the View-2
> scaffolder reshape. **A model-economy policy** was ratified (a private memory,
> not a repo change): Fable reserved for complex planning/research, Opus 4.8 +
> Extra for execution/coding-to-plan. Post-merge: main=`63009c3` (head_commit
> pins `2f46fc9`, the #833 build — the last SUBSTANTIVE code commit, mirroring
> the s155 head-of-record convention; #834 is a `docs(plans)` closeout); 0 open
> PRs; loop-dispatcher DISABLED; MS-S1 idle/COLD (the advisory arm is stub-first
> deterministic — zero live calls). Commits (per-PR): `19f5caa` (#829) →
> `ad39774` (#830) → `8809776` (#831) → `d679036` (#832) → `2f46fc9` (#833
> BUILT — head_commit of record) → `63009c3` (#834 closeout, main HEAD);
> `recent_commits` interleaves the five merge commits.

> **Sessions 153 + 154 + 155, 2026-07-20 (head_commit `a53c6ed` → `25b31e2`) —
> the demo-beat runbook staged (#822), a strategy read that CUT the tempting
> part (s154, zero commits), the operator confidence badge REMOVED from
> both cards that carried it (#823), and the late-s155 PLAN-0084 arc: filed
> (#825) → all 5 SDs Cray-resolved (#826) → BUILT end-to-end (#827) —
> map↔monitor run linkage + opt-in seed rotation + the SD-F Fastenal-adapter
> swap.** **(s153) Two docs PRs, no code.** **#821
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
> sessions). Morning commits: `0248ec1` (#821) → `b45f5c4` (#821 merge) →
> `90a2afb` (#822) → `b1d7f5a` → `d8057fb` (#822 merge) → `f09cc99` →
> `ffb251b` (#823) → `4edfa3f` (#823 merge).
> **(s155 late) The PLAN-0084 arc — filed, SD-ratified, and BUILT end-to-end
> in one afternoon/evening (#825 → #826 → #827).** **#825 (`1b2c05c` → merge
> `628bfa1`, `docs(plans)`) filed PLAN-0084** (`Status: Draft`): map↔monitor
> run linkage + opt-in seed rotation — the demo-coherence ask Cray made
> mid-rehearsal; scope Cray-ratified via AskUserQuestion ("Flow + หมุน asset
> เดิม"; server-side object injection REJECTED) + PLAN-first routing. Authored
> by plan-drafter from Code's grounded dispatch; the drafter corrected Code's
> own fact-pack TWICE (RunSummaryView, not "RunListItem"; the event path's
> engine-side `trigger_context` stamp pinning CNC-Line-07, which matches no
> map pk). **#826 (`edf922d` + `f6bb12c` → merge `e5f3ede`, `docs(plans)`)
> resolved ALL FIVE SDs** (Cray, AskUserQuestion): SD-A typed subject on
> list+detail; **SD-B ALL FOUR non-hero assets rotatable (wider than rec** —
> CNC-009 cheap because `link_asset_uses_part` LNK-AUP-003 already binds it
> to the hero part); SD-C a distinct "governed run in flight" marker,
> waiting_human+running; **SD-D execute option (d) IN-PLAN (wider than rec)**
> — both demo entry points light the map, the `_EVENT_ASSET_ID` re-pin
> superseding PLAN-0057 OQ-1; SD-E newest-first cap 5. Step 0 SATISFIED. Two
> commits because the L1 same-file loop-detect interrupted the drafter's
> batch (3 restating edits landed in commit 2 after the counter reset — fully
> disclosed in the PR). **#827 (`45fcba1` + `64119b9` → merge `25b31e2`,
> `feat(demo)`) BUILT PLAN-0084 end-to-end + SD-F.** The build: seed stamps
> `trigger_context["subject"]` from the computed intake seed; `RunSubjectRef`
> + optional `subject` projected fail-soft on RunSummaryView AND
> RunDetailView; the map ingests `/runs` via a Monitor-style direct fetch
> (never the mock-fallback O.API path); assets with in-flight runs get the
> dashed amber ring; the node panel gains "Governed runs · in flight" with
> per-run "Open in Monitor →" buttons; `ViewMonitor.focusRun` + the
> `oct:goto {view:'H', run}` wire; Step 4b re-pin + the entity_ids→subject
> projection through a lazily-cached pk→object_type index (data-driven, no id
> map); rotation via `--asset`/`--rotate` with an ASSET-KEYED failure pick
> (row-order dependency killed); fixtures = one failure event per rotatable
> asset + 3 quotes each for three previously quote-less parts + the CNC-009
> PO (฿78,500 → the 50k–500k band); runbook §3d (rotation flags, the
> live-verified tier→approver table, the beat-1 cue now naming AST-CNC-014,
> the "strip must read LIVE" rule). **SD-F — the headline finding,
> Cray-ratified mid-build: the PLAN's grounding was WRONG (`was an error`,
> recorded in the PLAN)** — the map never rendered the hero CSV: the
> registered procurement adapter was the scaffold-era synthetic set
> (`equip-*`, 4 anonymous assets) while every hero surface narrates Fastenal
> (`AST-*`, 5 named assets) — the demo was already split-brain and the
> subject could light nothing. Cray: **"Fastenal เป็น adapter หลักของ
> procurement ทั้งหมด"** — `register_procurement_adapter` (discovery) now
> registers the `FastenalCsvAdapter`; the swap required the `plant.csv` geo
> anchor (without it the map has no mappable objects), `stock_qty`/
> `reorder_point` on `part.csv` (the calm-path chain runs over the registered
> adapter; synthetic semantics preserved EXACTLY incl. the PLAN-0066 AC-6
> >100 flip case as PRT-BLT-110 150/160), and four test repins (the
> PLAN-0083 canonical-coverage tripwire caught the new Part keys — working
> as designed; calm-path 3→5 rows; scheduled-demo verdicts; shadow-parity
> expected side JSON-sanitized for Decimal). Fastenal serves `[]` for
> unserved types + streams no events → GET /recommendations stays empty,
> matching the observed pre-swap demo; the synthetic adapter stays in-tree
> for direct-module harnesses. **Live verification (port 8101, strip LIVE,
> zero console errors):** AC-4 full click-through (map node → panel → button
> → View H with `run-row-run-s155-linkage` SELECTED); AC-9 (POST
> /demo/hero/event → the event run projects subject {Equipment, AST-CNC-014}
> and lights the map; the panel listed event + seeded runs newest-first);
> AC-5 (/runs forced 500 → map renders fully, zero markers, no mock
> fallback); AC-7 live (ROBOT-21 ฿99k→appr-pm; CONV-05 ฿7.2k→appr-buyer — a
> genuinely different tier; unknown asset lists the 5 rotatable); AC-2
> legacy fail-soft proven with the REAL morning run (subject: null). AC-1:
> full offline suite **2922 passed / 7 skipped**, re-run and CONFIRMED on the
> merge commit `25b31e2` itself (CI is PR-only, so the merge commit is otherwise
> never tested) — baseline 2915 + 7 new tests; mypy strict 142 files; ruff clean.
> **PLAN-0084 status: Draft, all 6 SDs resolved, ACs deliberately UNTICKED —
> closeout (tick + archive) is a named next step after Cray's rehearsal
> passes on the new build.** Post-merge: main=`25b31e2`; 0 open PRs;
> loop-dispatcher DISABLED; MS-S1 idle/COLD (zero calls all day). Late-s155
> commits: `1b2c05c` (#825) → `628bfa1` (#825 merge) → `edf922d` + `f6bb12c`
> (#826) → `e5f3ede` (#826 merge) → `45fcba1` + `64119b9` (#827) →
> `25b31e2` (HEAD, #827 merge).

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
>
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
| 2026-07-21 | **s157 — PLAN-0086 COMPLETE (#838 `feat(verticals)`): the narrative→pipeline scaffolder run as a TIMED MANUAL baseline — a dirtied customer monologue → a live, governed, human-gated pipeline on the 6th vertical `fleet_maintenance` in 27m39s hands-on (wall 43m17s − 6m51s answer-waits − 8m48s escalation). AC-7 caveat, BINDING and never to be dropped: Code drafted the pre-dirtied narrative → LOWER BOUND on blind intake, operator knows this codebase.** AT-2 `governed_repair_approval` = the 4th signature; first vertical with the PLAN-0085 gate advisory ON by default; additive `ComplianceCriterion += three_quote`. **ADR-0025 D7 AT-2-generator deferral CANCELLED at N=4 (Cray-ratified, typed — 4th consecutive vertical forcing an engine-level criterion extension); the `_RETRIGGER_N` guard RETIRED + REPLACED by `test_at2_extraction_obligation_is_owned` (PLAN-0076 T1 = standing owner). The extraction PLAN is UNOPENED — G2-gated → `plan-drafter`.** 2 of 4 customer rules un-encodable (quote-comparison ฿ threshold has no home on a `rule_gate` criterion; `EmergencyWaiver` lacks cap/ratification fields) — surfaced in the vertical README's "stated but NOT enforced" table. Suite **2943/7**; mypy strict 98 files; ruff clean; live `run-b9c0804b52f0` parks `waiting_human` at `approve`. Full narrative: the Session-157 CF block above | `79358c6` (HEAD, #838 merge) / `a2ef45e` (build) / `verticals/fleet_maintenance/` + `tests/services/engine/procedures/test_at2_signature_retrigger.py` (guard replacement) + `docs/plans/0086-fleet-vertical-timed-manual-scaffold.md` (closeout pending) |
| 2026-07-21 | **s156 — PLAN-0085 "Advisory Gate Recommendation (AI-Transition Rung 1)" filed → 5 SDs Cray-ratified → BUILT → closed, ONE day (#831 Draft `docs(plans)` / #832 SDs `docs(plans)` / #833 `feat(engine)` / #834 closeout `docs(plans)`): an advisory recommendation with grounded reasons at procurement's `doa_tier` approval gate — SHOWN, NEVER routes (the ADR-0019:50-57 fence, now CI-pinned: byte-identical approve audit advisory on/off/exploding-builder).** All 5 SDs = the draft rec (AskUserQuestion): SD-1(b) emit INSIDE the gate propose path (ZERO hash change), SD-2(b) stub-first deterministic arm + opt-in live MS-S1 seam, SD-3 all three procedures, SD-4 gate-panel advisory block, SD-5 new trace kind `advisory_recommendation` (actor `llm`). New `gate_advisory.py` (never-raise, ADR-0030 D5) wired via `GovernanceActionExecutor` + procurement `_executors`; Monitor gate-panel block, NO score (the L-C/#823 trust shape). Suite **2927/7**; mypy/ruff clean; live-verified 8101. Unplanned value (Cray): the advisory doubles as an ONBOARDING aid → recorded as a signal for the View-2 reshape. Full narrative: the Session-156 CF block above | `2f46fc9` (#833 BUILT, head_commit of record) / `63009c3` (#834 closeout, main HEAD) / `8809776` (#831) / `d679036` (#832) / `services/engine/procedures/gate_advisory.py` + `docs/plans/done/0085-*.md` (archived, 8/8) + `docs/runbooks/run-oct-demo.md` §3e |
| 2026-07-21 | **s156 — the demo rehearsal (carried s153→155) PERFORMED + PASSED (Cray, Beats 1-5 on 8101 incl. the new PLAN-0084 map→monitor opening beat, ratified "ok"), which GATED the PLAN-0084 closeout (#830 `docs(plans)`, 9/9 ACs + archived to `done/`); + a morning map-label UI fix (#829 `fix(ui)`, `view-map.js ?v=c39`, plate moved BELOW the node, 0 overlaps live).** Cray then opened the two-view **AI-Transition** frame — (1) an LLM at the approval gate, (2) a narrative→pipeline scaffolder — and ratified the SEQUENCE: capture a discussion note → build View-1 (Rung 1 = PLAN-0085) → reshape View-2 against Rung-1's result → build View-2; umbrella thesis = governance human in/on-the-loop → first-stage AI automation (gitignored note, binds nothing). A model-economy policy ratified (private memory, not a repo change): Fable for complex planning/research, Opus 4.8 + Extra for execution/coding-to-plan. Full narrative: the Session-156 CF block above | `ad39774` (#830) / `19f5caa` (#829) / `docs/plans/done/0084-*.md` (archived, 9/9) + `.claude/handoffs/session-156/2026-07-21-0851-*-ai-transition-two-views.md` |
| 2026-07-20 | **s155 (late) — PLAN-0084 shipped end-to-end in one arc (#825 `docs(plans)` filed Draft → #826 `docs(plans)` all 5 SDs Cray-resolved [SD-B all-four-rotatable + SD-D both-entry-points, both WIDER than rec] → #827 `feat(demo)` BUILT): map↔monitor run linkage (runs stamp `trigger_context["subject"]`; fail-soft `subject` on RunSummaryView/RunDetailView; the map ingests `/runs` direct-fetch [never the mock-fallback O.API path], dashed amber in-flight ring, node-panel "Governed runs · in flight" + "Open in Monitor →" via `ViewMonitor.focusRun`/`oct:goto`) + opt-in seed rotation (`--asset`/`--rotate`, asset-keyed failure pick, all 4 non-hero assets).** **Headline = SD-F, Cray-ratified mid-build — the PLAN's grounding `was an error`: the registered procurement adapter was scaffold-era synthetic (`equip-*`) while every hero surface narrates Fastenal (`AST-*`) — split-brain demo; `register_procurement_adapter` now registers the `FastenalCsvAdapter`** (plant.csv geo anchor + part.csv stock fields; synthetic semantics preserved EXACTLY incl. the PLAN-0066 AC-6 flip case; 4 test repins — the PLAN-0083 canonical-coverage tripwire caught the new keys, WORKING AS DESIGNED). Live 8101 verification: strip LIVE, zero console errors, AC-4 full click-through + AC-9 event-run lights the map + AC-5 no-fallback + AC-7 tier rotation + AC-2 legacy fail-soft. Suite **2922/7** (2915 + 7 new); mypy strict 142 files; ruff clean. PLAN-0084 stays Draft, ACs deliberately UNTICKED — closeout after Cray's rehearsal passes. Full narrative: the Sessions 153+154+155 CF block above | `25b31e2` (HEAD, #827 merge) / `45fcba1` + `64119b9` (build) / `e5f3ede` (#826 merge) / `628bfa1` (#825 merge) / `docs/plans/0084-map-monitor-run-linkage-and-seed-rotation.md` (Draft, 6/6 SDs resolved) + `verticals/procurement/data_adapter/__init__.py:99` + `docs/runbooks/run-oct-demo.md` §3d |
| 2026-07-20 | **s153-155 — #822 `docs(runbook)` staged the config-pin fail-closed refusal as a deliberate demo beat (run-oct-demo.md §3c, Beat 06, PLAN-0047 Step 6); s154 ZERO commits (Cerebras-KB strategy read: predict+warn = existing Shape-1 IF deterministic, artifact-KB = D3 Shape-2 pilot-gated, org-wide ingestion CUT, reframe = "governed retrieval over the decision record"); #823 `fix(ui)` REMOVED the operator confidence badge from BOTH cards — story scene-2 (hardcoded 86%) and View-B `decisionCard()` (LIVE `rec.confidence`, the load-bearing one) — executing the ratified s74 trust shape.** Trace/fault-mode/DAG confidence KEPT by design. Static assets only; suite **2915/7** re-run on the merge commit `4edfa3f`; live 8101 check `LIVE` with a `confidence: 0.86` fixture. **4 claim-vs-code corrections:** naive-RAG comparison ALREADY run (PLAN-0027 — lean RAG TIES governed on accuracy at 3-15x lower latency) · "actions router fully governed" is overstated · the determinism line is ADR-0019:50-57 + ADR-010 IN-3, NOT ADR-0031 · a 4th AT-2 signature is UNBUILDABLE (no vertical has the substrate). Full narrative: the Sessions 153+154+155 CF block above | `4edfa3f` (HEAD, #823 merge) / `ffb251b` + `f09cc99` (badge removal) / `d8057fb` (#822 merge) / `b45f5c4` (#821 merge) / `docs/runbooks/run-oct-demo.md` §3c + `services/api/static/assets/view-anomaly.js` + `view-story.js` |
| 2026-07-19 | **s152 — PLAN-0083 (fix c1) BUILT + verified + archived (#818 `feat`, #819 `docs(plans)`): the procurement ontology↔CSV column drift CLOSED at the `FastenalCsvAdapter` seam — `_COLUMN_RENAMES` on the `fetch_objects` path maps raw Fastenal CSV → canonical ontology names (type key `Asset`→`Equipment` [SD-1] + 5 columns [`part_id`→`part_no`, `price_thb`→`price`, `asset_id`→`equipment_id`, `site`→`site_id`, `lead_time_days`→`lead_time`] + `PurchaseOrder.asset_id`→`equipment_id` [SD-4a]; ฿-columns DEFERRED raw [SD-4b]), so every consumer sees ONE canonical vocabulary.** Rides under ADR-016's LOCKED "mapping absorbs source diversity" boundary — zero-core-edit (no ADR / ontology YAML / regen / `services/` engine edit; ADR-0023), diff = adapter + vertical + tests only. A `test_fastenal_adapter_canonical_coverage.py` tripwire pins per-type set-equality + required-props + rename-target validity + the SD-4b ฿-defer, non-vacuous EMPIRICALLY (dropped a rename → RED → reverted); R2 added the under-scoped `governance_audit.py:177/179`. Suite **2915/7** (2896 + 19); mypy strict + ruff clean; CI gate PASS on #818. Full narrative: the Session-152 CF block above | `a53c6ed` (#818 merge) / `a211651` (build) / `5140ee3` (HEAD, #819 merge) / `docs/plans/done/0083-*.md` (archived) + `tests/verticals/procurement/test_fastenal_adapter_canonical_coverage.py` |
| 2026-07-19 | **s151 — PLAN-0081 BUILT end to end (#814, `feat(building_materials)`): the `building_materials` governed-credit HERO — the 3rd AT-2 signature (`building_materials.governed_credit_release`), Cray-commissioned this session. An exposure breach above the account's own `credit_limit_thb` routes the full governed AT-2 spine (per-entity band → `rule_gate` KYC/overdue-AR/blacklist → `doa_tier` approval + SoD); the ฿550,000 breach routes mid-ladder.** The 3rd signature REUSES the money `doa_tier` ladder UNCHANGED (no new gate kind / authority quantity) — only `ComplianceCriterion += {kyc, overdue_ar, blacklist}` grows; engine diff bounded to that additive `spec.py` block (the `Person` promotion was PLAN-0082's, already on main). **ADR-0025 D7 re-eval PERFORMED at N=3** (Cray-ratified: generator stays deferred, marker re-arms N=4). Closeout: PLAN-0079 tracking stub RETIRED (Step T3) + guard test DELETED; PLAN-0076 T1 gate-seam trigger recorded MET (seam PLAN un-opened); PLAN-0081 archived at 15/15 ACs. Suite **2896/7** re-run on the merge commit `9422c40`; mypy strict + ruff clean. Full narrative: the Session-151 CF block above | `9422c40` (HEAD, #814 merge) / `a46bef8` (build) / `docs/plans/done/0081-*.md` (archived, 15/15) + `tests/verticals/building_materials/test_governed_credit_hero.py` |
| 2026-07-19 | **s150 — PLAN-0082 COMPLETE + archived (Steps 5-7, #809-811) + PLAN-0081 fold (#812): the reconciliation half of the shared-ontology arc — spec-layer `Person` reconciled to ONE generated `core.Person` (#809, SD-H=(a) + `_PYDANTIC_COMMITTED_DEST`), procurement+supply_chain migrated + OQ-6 marker transformed (#810), PLAN closed out at 7/7 ACs + archived (#811); PLAN-0081 folded (SD-J=SPLIT resolved, Step 9 shrunk).** AC-5 dual-roster "retire one" RE-SCOPED (misread — distinct demos, neither retired). CI-scope lesson (mypy strict re-export). OQ-2 deferred. Full narrative: the Sessions 149+150 CF block above | `043da3c` (HEAD, #812) / `e059303` (#811) / `docs/plans/done/0082-*.md` |
| 2026-07-18 | **s149 — PLAN-0082 shared-ontology mechanism BUILT (Steps 2-4 behind ADR-0033, #803-808): ADR-0033 Accepted (shared `core` home + `imports:` grammar + set/closed types + shared Person committed-ORM contract); `core_v0.yaml` + set/closed L1/L2 (#804), Pydantic emitter (#805), imports/cross-doc resolution (#806), set→JSONB emitters (#807), committed Person ORM + `person` table + Alembic 0012 migration ran green (#808).** Additive — zero shipped-behaviour change. Full narrative: the Sessions 149+150 CF block above | `5e45eb6` (#808) / `6dd6464` (#803) / `ontology/core_v0.yaml` + `services/db/person.py` + `alembic/versions/0012_person_table.py` |
| 2026-07-18 | **s148 — PLAN-0080 COMPLETE + archived (#799, `docs(plans)`): the trace-attribution + `ui.md` PLAN (shipped end-to-end s146 via #794/#795) closed out — Status → Complete, all 9 ACs re-verified against `main` on a fresh disk read (each with file:line evidence) + ticked, `git mv` → `docs/plans/done/`.** AC-5 ticked as-scoped (**F-4**: only the `TRACE` entries fed to `O.reasoningTrace` are canonical-normalized; PROP-card / KIND_BADGE / DAG `kind:` tokens are separate local vocabularies the AC carved out). Findings **F-1/F-2/F-3 + OQ-1 stay recorded, NOT closed**; no code/behaviour change. Full narrative: the Sessions-147+148 CF block above | `0b67f76` (HEAD, #799 merge) / `81f307b` (closeout) / `docs/plans/done/0080-*.md` (COMPLETE, archived) |

## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13; guarded trial (parallel to ADR-012) — verdict **continue-with-adjustments**. Run 1 (energy, s93) + Run 2 (supply-chain, s94) both COMPLETE, S-checks all PASS against pre-committed oracles, no R-PS trigger fired; C-1..C-3 CONFIRMED → **no open partner-sim debt**. ADR-011 audit stays gated on a REAL partner conversation (R3: SYNTHETIC provenance INFORMS but never TRIGGERS it). Full record: `docs/adr/0020-*.md` + the gitignored run packages `docs/research/private/2026-07-02-partnersim-run{1,2}-*.md`. _(Full prior narrative — the ~8 schema-mismatch findings, both run details, cross-run synthesis — archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **Procurement vertical — GO + SHIPPED (PLAN-0036 Fastenal, Stage 1):** 4th vertical greenlit (s75); PLAN-0036 drafted + merged Draft (#412, `7a7c036`; SD-1…SD-5 confirm-all). Demo target = Fastenal Thailand (auto-parts / EEC); **hero** = asset-failure → governed emergency sourcing, **calm-path** = low-stock reorder. Stage 1 = a PLAN-only pure-config plugin on the ADR-016 engine (zero `services/` core edit; CQ-1 / ADR-0023). **Pitch** = asset-ontology-triggered governed sourcing (native ontology ADR-008 + engine ADR-016), NOT the commoditized "governed"/"cross-vertical" claims. Full record: `docs/plans/0036-*.md` + the s72 de-risk dossier `docs/research/private/2026-06-22-procurement-*.md` (5 files: spec-expressiveness, GTM, asset-aware incumbent scan, AI-sourcing teardown, platform-incumbent deepdive). _(Full prior narrative archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [ ] **⭐ The AT-2 gate-plugin-seam / criterion-vocabulary EXTRACTION PLAN is UNOPENED (s157, the session's most important open thread).** ADR-0025 D7's generator deferral was **CANCELLED at N=4** (Cray-ratified, typed, 2026-07-21) after `fleet_maintenance` became the 4th consecutive vertical to force an engine-level `ComplianceCriterion` extension — but **the extraction itself is NOT done**. A new PLAN is **G2-gated for Code**, so it routes via `plan-drafter` (Code R2 + commits). The obligation is held by **PLAN-0076 Step T1** (`Status: Tracking`) and enforced by `test_at2_extraction_obligation_is_owned` in `tests/services/engine/procedures/test_at2_signature_retrigger.py`, which turns RED if PLAN-0076 is archived or loses the record. *(s157; #838)*
- [ ] **AT-2 stale `N=2` / `N=3` signature counts — doc drift across three artifacts (surfaced s155).** _[s157 UPDATE: the deferral is now **CANCELLED**, so the drift is doubly stale — fold the corrections into the G1-gated edits the extraction PLAN will carry rather than fixing them piecemeal.]_ The pre-s157 live value was **`N=3`, with the ADR-0025 D7 generator marker RE-ARMING at `N=4`** (Cray-ratified at the s151 PLAN-0081 re-eval). Stale counts survive in: **(1)** `services/engine/procedures/spec.py` comments — **ungated, fix freely**; **(2) ADR-0025 D7** and **(3) ADR-0032** — both **G1-gated Accepted-body edits**, so they route via `plan-drafter`, never a direct Code write. Only `tests/services/engine/procedures/test_at2_signature_retrigger.py` carries the correct `_RETRIGGER_N = 4`, so the *test* is the source of truth and nothing turns RED on the prose drift. _[Irony worth preserving: **ADR-0032's own Positive-consequences section claims it makes exactly this stale-N-count error class harder to reintroduce** — and it now carries that very drift.]_ *(s155; blocks nothing, but every stale count is a wrong premise for the next AT-2 scoping call.)*
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
