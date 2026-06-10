---
last_updated: 2026-06-10T09:16:01+07:00
session: 51
current_batch: 'Session 51 — ADR-0018 "Axis-B Verification Loop" Accepted (SD-1 = narrowed Write, #242); ADR-0017 OQ-B resolved earlier (#239/#240). Full narrative in Current Focus.'
current_actor: code
blocked_on: 'Nothing gates shipped work. No open PRs (all merged).'
next_action: 'T2 — Cowork drafts PLAN-0021 (Axis-B build) per ADR-009 D1, then Code commits + builds. Dispatch ready (gitignored), awaiting Cray relay. Follow-up — STATUS rotation policy (this cleanup) to Cowork lesson/convention + status-scribe hardening.'
head_commit: 1be60f7
recent_commits: [1be60f7, 129c3a5, 5f8073c, 3d3ade2, f5f28f8, 1f355cb, c512cf9, f13af35]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 51 (current) — ADR-0018 "Axis-B Verification Loop" is RATIFIED
> Accepted (#242, head_commit `1be60f7`, `docs(adr):`); the deferred Axis-B
> verification-loop track is no longer deferred — it is now Accepted and
> entering its build phase.** ADR-0018 opens harness-review **track 2** (the
> evaluator loop) on top of the already-at-frontier Axis-A governance layer:
> a `/goal` Stop-hook gate + a `goal-evaluator` subagent that judges whether a
> run actually achieved its declared goal. **Decisions:** D1 hybrid
> deterministic-check + LLM-judge; D2 a `.claude/state/goal.json` run-goal
> artifact; D3 a **4th subagent sibling that REFUTES rather than blesses**
> (the structural guard against reasoning-blindness); D4 a `_goal_gate.py`
> living inside `stop_continuation.py`, **FAIL-OPEN** (a broken/absent
> evaluator never blocks Stop); D5 a session-Stop **warn-only v1**; D6 the
> structural reasoning-blindness rationale; D7 formalize + augment the manual
> AC ritual. **SD-1 resolved = narrowed Write** — the evaluator's `Write` is
> hook-narrowed to `goal.json` only (the same author-bounded pattern that
> governs `plan-drafter` and `status-scribe`). **Lineage:** PR #241 added the
> ADR `Proposed` (`5f8073c`) → **#242 ratified it Proposed→Accepted (Cray,
> session 51)** and carries this **T4** STATUS reconcile (the ADR §"Required
> follow-on" T4 task: record ADR-0018 in Recent Decisions + clear the
> Current-Focus Axis-B "deferred" earmark). head_commit = `1be60f7` (the
> ratification `docs(adr):` commit = the newest *substantive* commit per
> `lint_status`; this `docs(status):` reconcile does NOT count). **NEXT = T2:**
> Code dispatches the Axis-B **build PLAN** to Cowork (ADR-009 D1) — covering
> `_goal_gate.py` + the `stop_continuation.py` insertion, the `goal.json`
> schema + tests, the `/goal` command, the `goal-evaluator` agent + the SD-1
> write-deny hook, Telegram wiring, and a verification-rigor case-coverage
> matrix; after draft + Cray ratify → T3 (autonomy-triggers **V-row**) →
> build. **OQ-8** (plugin packaging, MS-S1 local evaluator, blocking-mode
> promotion, PR-merge gating, auto-declared goals) and **VX-1..3** stay
> non-binding / verify-at-execution — none blocks T2. This session also
> earlier resolved ADR-0017 OQ-B (#239/#240), already recorded below.
> AI-assisted (Claude Code, session 51); no `Co-Authored-By` per CLAUDE.md §7.
>
> **Session 51 (earlier) — ADR-0017 OQ-B is RESOLVED; the skills-as-memory-tier
> arc's last open thread is CLOSED (#239, head_commit `c512cf9`,
> `docs(adr):`).** OQ-B (skill-loader tie-break on a same-bare-name collision)
> was the one "delegated to Code" empirical item left after the arc body landed
> in session 49 (#234/#236/#237/#238). Empirical finding, restart-confirmed at a
> clean session-51 startup (~99% confidence): on a same-name collision the
> **GLOBAL/user skill (`C:\Users\crayj\.claude\skills\`) WINS over the project
> skill** (`<repo>/.claude/skills/`) — the OPPOSITE of ADR-0017 D7's
> "project-local context wins" premise; the WSL `~/.claude/skills/` path is not
> scanned, and plugin skills are namespaced (so they don't collide). Recorded
> three ways: (1) ADR-0017 gains a **"D7 Errata (2026-06-10)"** subsection +
> OQ-B flipped Open→RESOLVED (errata applied with Cray's explicit per-diff
> approval through the G1 Accepted-ADR gate); (2) new
> `docs/lessons/0022-skill-loader-precedence.md`; (3) a fill of the
> `docs/runbooks/memory-architecture.md` §"Skill Conventions" OQ-B placeholder.
> The D7 **authority rule** (global/plugin skills must not encode
> project-binding rules) is UNCHANGED and *reinforced* — only the loader
> tie-break mechanics and an incidental `eli-cray` example (it's a command, not
> a global skill) were corrected. The throwaway probe artifacts (host state on
> three skill roots) were cleaned up after merge — working tree restored to
> clean. AI-assisted (Claude Code, session 51); probe ran with Cray's approval;
> no `Co-Authored-By` per CLAUDE.md §7. Two ADR-0017 OQs remain, both
> non-blocking: **OQ-A** (migration backlog — non-binding future-PR candidates)
> and **OQ-C** (revisit the tier definition only if harness-as-plugin packaging
> is pursued). No governance thread is currently blocked or in-flight.
>
> **Session 49 — ADR-0017 "Skills as a memory tier" is ACCEPTED; the
> skills-as-memory-tier governance arc is COMPLETE (#236 + #237, head_commit
> `8b18b3a`, `docs(constitution):`).** Two PRs landed since the #235 reconcile,
> so this single reconcile advances head_commit past BOTH (it was stale at
> `471bcb5`). #236 (`docs(adr):`, `7bf9d38`) added ADR-0017 `Proposed` —
> Cowork-drafted, Code-reviewed via the ADR-009 D3 receive sequence; #237
> (`docs(constitution):`, `8b18b3a`) ratified it (status flipped
> Proposed→Accepted) and applied the alignment. head_commit = `8b18b3a` (the
> newest *substantive* commit per `lint_status`; `8b18b3a` is
> `docs(constitution):` = substantive → it sets head_commit; the #236/#237
> merge commits `c04787b`/`7bf9d38`'s merge and the `docs(status):` reconciles
> are lint-excluded). This block is **T6** (STATUS reconcile) of the ADR-0017
> follow-on plan.
>
> **The arc, end to end.** PR #234 added the `.claude/skills/` **mechanism**
> (two on-demand skills + CLAUDE.md slimming) → #236 added the **ADR** (the
> governance rationale + decisions) → #237 applied the **alignment** (T1–T5).
> The skills-as-memory-tier arc is now governance-complete.
>
> **What #237 aligned (T1–T5).**
> - `.claude/skills/` is now **Tier 2.6** in the memory model (`CLAUDE.md` §4 +
>   the memory-architecture runbook) — git-tracked, auto-loaded by description
>   match.
> - The **D5 knowledge-placement decision rule** — binding rule→`CLAUDE.md`;
>   durable learning→`docs/lessons/`; canonical reference→`conventions`/
>   `runbooks`; task-triggered how-to→a **Skill** — and the **D7
>   skill-authoring conventions** are codified in the runbook (compact form +
>   a pointer from §4).
> - `CLAUDE.md` §1 gained the **D6** line (derived artifacts 2.5 + 2.6 carry no
>   independent precedence; canonical wins on conflict); the §10 skills row now
>   cites ADR-0017.
>
> **T6 housekeeping (this reconcile).** ADR-0017 (Accepted) recorded in Recent
> Decisions; the §50/§57 "next: draft ADR-017" earmark is **cleared** (the ADR
> now exists and is Accepted); the PR #234 skills follow-up is marked
> **governance-complete**.
>
> **Next.** The arc is closed. Open threads: (1) **OQ-B** — skill loader
> tie-break (same-named project vs global vs plugin skill) is delegated to Code
> but needs Cray approval for a probe touching global `~/.claude/skills/` (host
> state); (2) the deferred **Axis-B verification-loop** track (evaluator
> subagent + `/goal` Stop-hook gate) from the harness-engineering review. A
> **restart-bridge handoff is due this session** because #237 edited
> constitutional `CLAUDE.md` (Lesson #5 §1).
>
> **Session 49 (#234 — predecessor in this same arc) — CLAUDE.md slimmed: git +
> Code-ops procedures extracted to on-demand project skills (#234, `471bcb5`,
> `docs(constitution):`).** One
> `docs(constitution)` PR landed this turn (`docs(constitution): slim CLAUDE.md —
> extract git + Code-ops procedures to on-demand skills`), Cray-reviewed + merged
> via merge commit `d556421` (#234). This block = the session-49 #234 reconcile
> (head_commit `471bcb5` — the newest substantive commit per `lint_status`;
> `docs(constitution):` IS substantive, so it sets head_commit; the #234 merge
> commit `d556421` is lint-excluded).
>
> **What shipped.** The always-loaded constitution shrank `206→193 lines /
> 2050→1908 words` by extracting git mechanics + the Tier-2 Code-ops procedure
> into TWO new on-demand project skills under `.claude/skills/` —
> **`git-workflow`** and **`code-operational-policy`** — with **all binding rules
> retained in `CLAUDE.md`** (only the step-by-step procedure moved). This
> establishes `.claude/skills/` as the project's on-demand procedure layer,
> adopting Anthropic's Agent-Skills pattern: a bloated always-on `CLAUDE.md`
> causes rules to be ignored, so procedure belongs in on-demand skills that load
> only when relevant.
>
> **Genesis (the two-axis harness-engineering review, 2026-06-09).** A review of
> vero-lite against Anthropic's public harness guidance reached a two-axis
> verdict: **Axis A (governance / safety)** = vero-lite is at the frontier — its
> deterministic-hooks + Sonnet-classifier hybrid independently mirrors Anthropic
> *auto mode*, and `chain-cap=8` matches Claude Code's own default; **Axis B
> (task-completion / verification — the evaluator loop)** = thin, deferred as a
> separate, higher-leverage track. PR #234 is the **low-risk FIRST move** Cray
> chose off that review (Skills adoption + CLAUDE.md slimming).
>
> **Follow-up already DISPATCHED to Cowork.** Cowork is to draft an ADR (next free
> number, likely **ADR-017**) titled **"Skills as a memory tier"** — handoff
> (gitignored) at `.claude/handoffs/session-49/2026-06-09-2140-code-skills-memory-tier-adr-dispatch.md`.
> Code commits the resulting `Proposed` ADR per ADR-009 D2. The dispatch carries
> 8 OQs to resolve: tier placement, `for_llm/` overlap, the canonical-vs-derived
> rule, authoring ownership, the knowledge-placement decision rule, the precedence
> ladder, conventions, and the migration backlog.
>
> **Next.** Cowork drafts ADR-017 "Skills as a memory tier" → Code commits
> `Proposed` → Cray ratifies. Separately/optionally: begin the Axis-B
> verification-loop prototype (an evaluator subagent + a `/goal` Stop-hook gate).
>
> **Session 49 (earlier) — PLAN-0020 Phase 1 (OFFLINE) is COMPLETE + merged
> (#232, `8324cba`, `feat(engine):`): two complementary, INDEPENDENT product-code
> changes addressing the session-48 PLAN-0019 Part B aquaculture over-naming
> finding.** One `feat(engine)` PR landed this turn (`feat(engine): deterministic
> affected_entities override + aqua precision prompt nudge (PLAN-0020 Phase 1)`),
> Cray-reviewed + merged via merge commit `f46f29c` (#232). This block = the
> session-49 #232 reconcile (head_commit `8324cba` — the newest substantive
> commit per `lint_status`; the #232 merge commit `f46f29c` is lint-excluded).
>
> **The two changes (both product code, independent).**
> - **fix #2 — deterministic `affected_entities` override (PRODUCT path).**
>   `services/engine/procedures/action_step.py` `_compose_action` now sources
>   `affected_entities` from the single loop `event` entity (a new
>   `_loop_entity_ref`), NOT the model's guess — mirroring the existing
>   `step.handler` override. This closes the envelope's over-naming metadata/UX
>   leak; the ADR-007 D2 `RecommendedAction` envelope CLASS is **unchanged** (one
>   field is now sourced deterministically).
> - **aqua prompt nudge (the benchmark β lever).** `services/engine/llm/prompt.py`
>   `build_reasoning_messages` / `build_structuring_messages` now instruct the
>   model to (a) name ONLY the breaching entity, (b) put the action verb in the
>   title. Vertical-agnostic wording (energy/supply already pass these checks → no
>   regression expected).
>
> **The key finding this session — why the two changes DON'T overlap.** The
> benchmark grades the **RAW `LlmJudgment`** (`harness.evaluate_item` bypasses
> `_compose_action` entirely), so **fix #2 is INVISIBLE to the benchmark β/α
> score** — it is validated instead by a dedicated **offline unit test**
> (`test_affected_entities_is_loop_entity_not_llm_overnaming`: an over-naming
> judgment → asserts the composed envelope names only the single loop entity,
> Lesson #7 §3 behavioural). The **prompt nudge** is what moves β — to be measured
> later in a **GATED host-state delta re-run** (NOT run this session).
>
> **The entity-key fork, RESOLVED.** `_loop_entity_ref` assumes the faithful
> ontology-projected event keys `object_type` + `primary_key`, with defensive
> `.get(..., fallback)` mirroring `recommender._rule_recommend` (degrades to
> `event_id`/`"unknown"` on a stub event, **never raises**). The procedure-path
> event shape is not yet standardised — this was surfaced for **merge-review per
> a two-way-door call** (reversible, offline, no production consumer today since
> Tier-2 real-data is parked); **Cray confirmed NO Tier-2 event-key contract in
> mind**, so the defensive getter STANDS. The HEDGE is documented in the
> `_loop_entity_ref` docstring + the commit body + the PR body.
>
> **Verification.** `ruff` + `mypy --strict` (services) green; `pytest` **71**
> (action_step + prompt + DB procedure + benchmark) + **104** (llm + eval
> golden-trace + recommender) green → confirms the reactive Pipeline-v0 path + the
> eval golden traces do NOT regress from the shared `prompt.py` edit.
>
> **PLAN-0020 stays status Draft.** SD-1 (widen supply-α `valid_handlers`
> `[hold]`→`[hold, inspect]`; needs Cray re-ratify BEFORE any dataset/grader edit)
> + SD-2 (8 s-bar review) remain **pending Cray ratification**; Code did NOT touch
> the grader/dataset this session.
>
> **Next — remaining Part B, Cray sequences (host-state — ASK before warming/
> running MS-S1).** ONE batched campaign: **B-3 baselines** (text-to-SQL + RAG,
> REPORTED not gated — the heaviest remaining sub-step + the conviction artifact)
> + **PLAN-0020 latency levers** + the **aqua prompt-nudge delta re-run** (re-run
> aqua β with the Step-1 nudge; confirm energy/supply did not regress). Cray must
> ratify SD-1 + SD-2 BEFORE the relevant gated step; Code does NOT touch the
> grader/dataset until SD-1 is ratified. THEN **B-5** report finalize + **B-6**
> ring-fence wrap (closes Part B). Sequencing = **Cray's call.** Standing backlog
> beyond Part B unchanged: Task (C) Tier-2 real-data path (gate on a design
> partner, not engineering readiness), PLAN-0010 loop handlers (soak-gated),
> `status_digest` v2, PLAN-004 Phase C.
>
> **Session 48 — PLAN-0019 Part B hardened re-run is COMPLETE (#228,
> `ec073a4`, `feat(benchmark):`): the hardened benchmark now DISCRIMINATES as
> designed, on live `gpt-oss:20b` (MS-S1, Cray-approved host-state run).** One
> `feat(benchmark)` PR landed this turn (`feat(benchmark): hardened re-run
> results + --dump-json verify tooling (PLAN-0019 B)`), Cray-reviewed + merged
> via merge commit `838f0ab`. This block = the session-48 #228 reconcile
> (head_commit `ec073a4` — the newest substantive commit per `lint_status`; the
> #228 merge commit `838f0ab` is lint-excluded). Touched only `benchmarks/`
> (REPORT.md, harness.py, run_benchmark.py) — **no product code.**
>
> **Verify, don't infer (the session-46 lesson, operationalized).** Added
> `--dump-json` to the runner — per-item JSONL emitting verdicts + per-check
> details + the raw `LlmJudgment` (`harness.py` `ItemResult` now carries the raw
> judgment) — so **every score was VERIFIED against real model output, not
> inferred.** `REPORT.md` gains a "Results — HARDENED run (2026-06-09)" section;
> the pre-hardening baseline is retained for comparison. Raw evidence dump kept
> as a gitignored working note under `.claude/benchmark-results/`.
>
> **Hardened results (2026-06-09 run; 198 items / 240 LLM calls / 0
> StructuredOutputError).**
> - **β headline (SD-B1 ≥ 85%):** aquaculture 60.0% (24/40), energy 97.5%
>   (39/40), supply_chain 100% (40/40) → **overall 85.8% (103/120) — CLEARS
>   ≥85%** (a companion warm run read 89.2% → honest β ~86–89%). β fell from a
>   pre-hardening 100% to ~86–89% — the hard scenarios gave the headline real
>   discriminating power, exactly as PR2 intended.
> - **α handler-probe (own lane, NOT the headline):** aquaculture 77.5%
>   (31/40), energy 100% (40/40), supply_chain 32.5% (13/40) → overall 70.0%
>   (84/120).
> - **deterministic sanity:** 100% (198/198).
> - **latency (B-δ):** p95 22.64 s, mean 15.02 s (240 calls) → OVER the 8 s bar
>   (~2.8×) — the same ring-fenced finding (NOT a build failure, NOT a bar move,
>   NOT an ADR-016 reopen).
>
> **Verified failure modes (from the `--dump-json` capture — the discriminating
> signal).**
> - **aquaculture β=60% — two REAL model weaknesses:** 11× `forbidden_primary_keys`
>   (under multi-entity input the model frames a "DO Monitoring Summary" and
>   over-names SAFE decoy sibling ponds — e.g. `aqua-h01` names breached
>   `pond-A101` AND safe `pond-A102`/`pond-A103`) + 7× `action_keywords`
>   (assessment framing omits the aerate/oxygenate verb). Energy & supply_chain
>   show NO over-naming — energy's `forbidden_primary_keys` passed on every hard
>   item, so it handles multi-entity input markedly better (a real cross-vertical
>   signal).
> - **supply_chain α=32.5% is a BENIGN divergence, not a model error:** the model
>   picks `inspect` (a defensible cold-chain action; 21/28 easy, 6/12 hard) where
>   the dataset pins single `hold`, and crucially NEVER the dangerous near-misses
>   `expedite`/`reroute`. β stays 100% (action_keywords admits
>   inspect/hold/quarantine/divert). **Finding → tuning PLAN:** the α
>   `valid_handlers` for supply_chain is plausibly too narrow (arguably
>   `[hold, inspect]`) — a tuning-PLAN question, NOT a grader change (methodology
>   ratified). aquaculture's α misses are likewise mostly the benign
>   `increase_water_exchange`.
>
> **Bottom line.** Part B's empirical core is now closed end-to-end: the
> hardened benchmark **discriminates** (β ~86–89%, driven by aquaculture's hard
> scenarios surfacing real entity-precision + action-verb weaknesses), the α
> probe surfaces a real but **benign** handler divergence, sanity stays 100%,
> and latency is the known over-bar B-δ finding. All below-bar reads are logged
> findings → the follow-up tuning PLAN under the B-6 ring-fence; none moves a bar
> or reopens ADR-016.
>
> **Next — remaining Part B, Cray sequences.** **(1) Latency tuning PLAN** from
> the B-δ finding (p95 22.6 s > 8 s) — OFFLINE, authored via `plan-drafter`;
> levers: trim the `think=True` call-1 pass / batching / a faster-arch small
> model not yet on MS-S1 / revisit the 8 s bar; **incorporate the supply-α
> `valid_handlers`-too-narrow observation** as a candidate methodology tweak.
> **Must NOT reopen ADR-016's primitive shape (ring-fence).** **(2) B-3
> baselines** — raw text-to-SQL + a RAG baseline on the same questions
> (REPORTED, not gated; acceptance = a comparison run + measures recorded) — the
> heaviest remaining sub-step; hits MS-S1 (host-state). **(3) B-5 report
> finalize + B-6 ring-fence wrap.** Standing backlog beyond Part B unchanged:
> Task (C) Tier-2 real-data path (heavy-spend → Cray green-lights), PLAN-0010
> loop handlers (soak-gated), `status_digest` v2, PLAN-004 Phase C. Sequencing
> remains **Cray's call**.
>
> **Session 47 — PLAN-0019 Part B hardening is COMPLETE (PR1 #224 +
> PR2 #226): the benchmark now has the real action vocabulary, the β/α grading
> split, AND the hard multi-entity / near-miss scenarios + precision checks.
> PR2 (#226, `e76977d`, `test(benchmark):`) makes the β headline
> discriminating.** This is the SECOND PR of session 47 (PR1 = #224 below). One
> `test(benchmark)` PR landed this turn (`test(benchmark): hard scenarios +
> β-headline precision checks (PLAN-0019 B PR2)`), Cray-reviewed + merged via
> merge commit `6efb28c`. Cray-ratified design (2026-06-09): the entity-precision
> check is **`forbidden_primary_keys`**, and the hard items **augment** the
> dataset (the easy items stay as a floor baseline). Sequencing decided ELI-CTO:
> **build PR2 first, THEN one comprehensive hardened re-run** (not
> re-run-now-then-again) — higher information yield per host-state window, no
> misleading intermediate ~100%, respects anti-moving-target.
>
> **What PR2 hardens (why the β headline now discriminates).** PR2 gives the
> β headline real discriminating power on the two fields the model genuinely
> OWNS in the procedure path — entity-ID and action class:
> - **Multi-entity decoys (entity-ID):** `Scenario` gains `distractors` (1–3
>   SAFE sibling readings, mostly in the watch band so they read as borderline),
>   injected into the event as `other_readings`; the model must name the breach
>   AND NOT the decoys → the β-headline scoring checks `affected_primary_key`
>   (right entity) + the new `forbidden_primary_keys` (no decoy named). A loader
>   guard asserts every decoy is genuinely non-breaching and that
>   `forbidden_primary_keys` exactly equals the scenario's distractor set.
> - **Near-miss action (action-class):** a plausible-but-wrong action the model
>   must avoid recommending — aquaculture `feed` (feeding during an O₂ crash),
>   energy `monitor`/`schedule` (deferring an acute over-temp), supply_chain
>   `expedite`/`reroute` (keeping a possibly-spoiled load moving) → the checks
>   `action_keywords` (right verb present) + the new `forbidden_keywords` (decoy
>   verb absent from the proposal TITLE; the body may legitimately rule it out).
> - **Dataset:** +12 HARD breach items per vertical (ids `*-h01..h12`), each a
>   clear breach among the safe sibling decoys + a domain near-miss. The easy
>   items are kept as the floor baseline. **54 → 66 items/vertical; 84 → 120
>   graded breach items.**
>
> `grader.py` / `harness.py` / `schema.py` thread the precision checks + the
> distractor injection; `REPORT.md` documents the hard scenarios + precision
> checks and keeps the prior filled numbers as the PRE-HARDENING baseline. PR2
> touched only `benchmarks/` + `tests/benchmark/` — **no product code**.
>
> **Verification:** ruff check + ruff format clean; `mypy --strict` (benchmarks)
> clean; full suite **1347 passed / 2 skipped** (was 1340/2; +7 benchmark
> tests). This block = the session-47 #226 reconcile (head_commit `e76977d` —
> the newest substantive commit per `lint_status`; the #226 merge commit
> `6efb28c` is lint-excluded).
>
> **Next — a comprehensive hardened re-run on live `gpt-oss:20b` on MS-S1.**
> The hardened re-run on `gpt-oss:20b` on MS-S1 (192.168.1.133:11434) is **a
> host-state change — ASK Cray before warming/running.** One comprehensive run
> fills the β headline on the hard scenarios + the α handler-selection probe on
> the real menu (per the agreed PR2→single-re-run ordering); warm-first,
> serialized for a clean p95. Then **author a latency tuning PLAN** from the
> B-δ finding (trim the `think` pass / batching / a faster-arch small model /
> revisit the 8 s bar) — **must NOT reopen ADR-016's primitive shape
> (ring-fence)**; **B-3 baselines** (text-to-SQL + RAG, REPORTED not gated —
> the heaviest remaining sub-step); then **B-5** report finalize + **B-6**
> ring-fence wrap. Sequencing remains **Cray's call**.
>
> **Prior context (session 47 earlier — #224, `00d7a24`, `feat(benchmark):`):
> PLAN-0019 Part B hardening PR1 of 2 is COMPLETE — the real ontology
> action-handler vocabulary ((C) product-complete) + a β-headline / α-probe
> grading split, driven by a handler-determinism finding.** This was the FIRST
> PR of session 47, executing the remaining PLAN-0019 Part B work that session
> 46's handoff left for Cray to sequence. One `feat(benchmark)` PR landed
> (`feat(benchmark): action_type handler vocabulary + β/α grading split
> (PLAN-0019 B)`), Cray-reviewed + merged via merge commit `0dfd03a`. Cray
> ratified the design this session: **scope (C) product-complete**, **grading
> β + α**, **2 PRs (handlers first, then harder scenarios)**.
>
> **The handler-determinism finding (why β/α).** While scoping the hardening,
> Code found that vero-lite has TWO action paths with different handler
> semantics: the **reactive** Pipeline-v0 (`recommender._compose_llm_record`)
> USES the model's `suggested_handler` guess and `execute()` runs it; the
> **procedure** orchestrator (ADR-016, `action_step._compose_action`) OVERRIDES
> the guess with the author's deterministic, allowlist-bounded `step.handler`.
> The benchmark grades the raw `LlmJudgment`, but PLAN-0019 validates the
> **procedure** path, which discards the handler guess — so grading
> handler-selection as the *headline* would measure a field the procedure
> product overrides (and brush ADR-016). Resolution, Cray-ratified 2026-06-09:
> **β headline** = the fields the model owns in the procedure path = entity
> (`affected_primary_key`) + action class (`action_keywords`); **α probe** =
> handler-selection (`suggested_handler` vs the correct ontology `action_type`),
> reported on its OWN lane as a reactive-path / future-autonomy signal, NOT
> folded into the headline. `payload_contains` stays advisory.
>
> **Product ((C) product-complete).**
> `verticals/{aquaculture,energy,supply_chain}/handlers.py` now register the
> ontology `RecommendedAction.action_type` vocabulary as distinctly-named
> **no-op stubs** alongside `echo` (aquaculture
> `start_emergency_aerator`/`dispatch_technician`/`increase_water_exchange`/`escalate`;
> energy `restart`/`isolate`/`dispatch_technician`/`escalate`; supply_chain
> `reroute`/`expedite`/`hold`/`inspect`/`escalate`) — so the LLM
> `suggested_handler` enum is now a real 4–5-option menu (real I/O still lands
> with the design partner). Each procedure's breach action step now fixes
> `step.handler` to the correct `action_type` (aquaculture
> `aerate`→`start_emergency_aerator`, energy `restart_breaches`→`restart`,
> supply_chain `hold_breaches`→`hold`), **autonomy stays `gated`** (the human
> go/no-go is unchanged), and each agent's `allowed.action_handlers` allowlist
> was updated; aquaculture `summary` stays `echo` (a no-op artifact). So the OCT
> product now proposes/executes real-named gated actions instead of `echo`.
>
> **Benchmark.** `grader.py` `FieldCheck` gained a `probe` lane +
> `GradeResult.probe_passed`; `harness.py` `Summary`/`ItemResult` thread the α
> metric; `run_benchmark.py` prints it. Dataset `valid_handlers
> [echo]→[correct action_type]` across all 84 breach items. The
> dataset-consistency guard now requires ≥1 β-headline scoring field; a new
> offline test asserts every α-probe handler is registered for its vertical.
> `REPORT.md` documents the finding + the β/α lanes and **relabels the prior
> filled numbers as the PRE-HARDENING baseline** (echo-only,
> valid_handler-in-headline) — a hardened re-run is pending. `pyproject.toml`
> adds `allowed-confusables = ["α","β"]` for the project's Greek step/metric
> notation. `tests/services/db/test_procedure_headline.py` binds its gate spy to
> `start_emergency_aerator` (the gated step's new handler).
>
> **Verification:** ruff check + ruff format clean; `mypy --strict`
> (services/verticals/benchmarks) clean; full suite **1340 passed / 2 skipped**
> (was 1336/2; +4 net benchmark tests). This block was the session-47 #224
> reconcile (its substantive commit was `00d7a24`; the #224 merge commit
> `0dfd03a` is lint-excluded). Superseded as the head by #226 above.
>
> **Next — remaining Part B, β+α direction chosen, Cray to sequence.** **PR2 —
> harder scenarios** (multi-entity sets, distractors, near-miss actions) +
> **grader precision** (decoy-entity absence / forbidden-keyword checks) to give
> the **β headline** real discriminating power → then a **hardened re-run** on
> live `gpt-oss:20b` on MS-S1 (fills the β headline on the harder scenarios +
> the α handler-selection probe on the real menu — a host-state change, **ASK
> Cray before warming/running**). **Author a latency tuning PLAN** from the B-δ
> finding (trim the `think` pass / batching / a faster-arch small model / revisit
> the 8 s bar) — **must NOT reopen ADR-016's primitive shape (ring-fence)**.
> **B-3 baselines** — text-to-SQL + RAG comparison on the same questions
> (REPORTED, not gated) — the heaviest remaining sub-step. Then **B-5** report
> finalize + **B-6** ring-fence wrap. All via `test/*` (or `feat/*` where product
> code) PR(s). Sequencing remains **Cray's call**.
>
> _Older Current Focus blocks (Session 46 and earlier) were rotated out of this file on 2026-06-10 (session 51) to keep the always-read STATUS small — see [`docs/status-archive/2026-h1-current-focus.md`](status-archive/2026-h1-current-focus.md) and git history. Rotation policy is pending (Cowork lesson/convention — this session's follow-up)._

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

## Recent Decisions (last 5)

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-06-10 | **ADR-0018 "Axis-B Verification Loop" ACCEPTED (Cray-ratified, session 51) — opens harness-review track 2 (the evaluator loop) on top of the at-frontier Axis-A governance layer.** A `/goal` Stop-hook gate + a `goal-evaluator` subagent that judges whether a run achieved its declared goal. **Decisions:** D1 hybrid deterministic-check + LLM-judge; D2 a `.claude/state/goal.json` run-goal artifact; D3 a 4th subagent sibling that **REFUTES not blesses** (structural guard against reasoning-blindness); D4 `_goal_gate.py` inside `stop_continuation.py`, **FAIL-OPEN** (broken/absent evaluator never blocks Stop); D5 session-Stop **warn-only v1**; D6 structural reasoning-blindness rationale; D7 formalize + augment the manual AC ritual. **SD-1 resolved = narrowed Write** (the evaluator's Write is hook-narrowed to `goal.json` only — same author-bounded pattern as `plan-drafter`/`status-scribe`). **Lineage:** #241 (`5f8073c`, `docs(adr):`) added ADR-0018 `Proposed` → **#242 (`1be60f7`, `docs(adr):`, head_commit) ratified it Proposed→Accepted** + carries the T4 STATUS reconcile (record ADR-0018 here + clear the Current-Focus Axis-B "deferred" earmark). **NEXT = T2:** Code dispatches the Axis-B build PLAN to Cowork (ADR-009 D1) → T3 (autonomy-triggers V-row) → build. OQ-8 (plugin packaging, MS-S1 local evaluator, blocking-mode promotion, PR-merge gating, auto-declared goals) + VX-1..3 stay non-binding / verify-at-execution | `1be60f7` (#241 + #242) / `docs/adr/0018-axis-b-verification-loop.md` |
| 2026-06-09 | **ADR-0017 "Skills as a memory tier" ACCEPTED — the skills-as-memory-tier governance arc is COMPLETE** — #236 (`docs(adr):`, `7bf9d38`) added ADR-0017 `Proposed` (Cowork-drafted, Code-reviewed via the ADR-009 D3 receive sequence); #237 (`docs(constitution):`, `8b18b3a`, head_commit) ratified it (Proposed→Accepted) + applied the alignment (T1–T5). `.claude/skills/` is now **Tier 2.6** in the memory model (`CLAUDE.md` §4 + the memory-architecture runbook), git-tracked + auto-loaded by description match; the **D5 knowledge-placement decision rule** (binding→CLAUDE.md; durable learning→lessons; canonical reference→conventions/runbooks; task-triggered how-to→a Skill) + **D7 skill-authoring conventions** codified in the runbook; §1 gained the **D6** derived-precedence line (2.5+2.6 carry no independent precedence; canonical wins); §10 skills row cites ADR-0017. **Arc lineage:** PR #234 (`471bcb5`) added the `.claude/skills/` *mechanism* → #236 the *ADR* → #237 the *alignment*. This (T6) reconcile records the Accepted ADR, clears the §50/§57 "draft ADR-017" earmark, and marks the PR #234 skills follow-up governance-complete. Open threads: **OQ-B** skill-loader tie-break (delegated to Code; Cray-gated probe of global `~/.claude/skills/` host state) + the deferred **Axis-B verification-loop** track. Restart-bridge handoff due (#237 edited constitutional `CLAUDE.md`, Lesson #5 §1) | `8b18b3a` (#236 + #237) / `docs/adr/0017-skills-as-a-memory-tier.md` + `CLAUDE.md` §1/§4/§10 + `docs/runbooks/memory-architecture.md` |
| 2026-05-25 | **PLAN-0009 (Phase 3 — subagent topology) RATIFIED + Ready for execution + COMMITTED** — Cowork drafted under interim ADR-009 D1 phasing; Cray adjudicated all 4 OQs (OQ-1…OQ-4) 2026-05-25 (WebFetch for Explore; no new ADR — execute ADR-013 D1; subagent identity folds with ADR-013 OQ-3 in Step 1; PLAN status vocabulary). Cowork → Code dispatch handoff at `.claude/handoffs/session-10/2026-05-25-1240-cowork-plan0009-review-dispatch.md` `validate_handoff.py` clean (K-1 / ADR-009 D3 substitute — 9 required fields, actor=cowork / phase=dispatch / status=READY / suffix=dispatch, ISO-8601 +07:00, filename matches `_FILENAME_RE`). Code fact-pack / R2 review clean across 9 citations (0009 next free; ADR-013 D1/OQ-1/OQ-3 quoted verbatim; PLAN-0008 4 carry-overs accurate; PLAN template structure intact; Cray verification-rigor directive present in Step 6 + Verification). Status flipped Draft → Ready for execution in commit `d10073e` on `feat/plan0009-subagent-topology` (single-doc, worktree-OFF per CLAUDE.md §11). **2 reconciliation findings folded** into Current Focus: (1) `.claude/` readability — K-2 is write-block NOT read-block (research-note §6); OQ-D load-bearing forcing fact remains K-1 (Cowork can't run `validate_handoff.py`), substantive deferral stands. (2) Working-tree divergence — git worktree sees neither uncommitted new files nor gitignored paths (research-note §6.1, reproduced live this session); not K-1/K-2 but checkout-resolution mismatch; design implication for Phase 3.5 if approved. **CLAUDE_TIER / session-identity unification** confirmed correctly folded in PLAN-0009 Step 1 (one mechanism, 3 identity cases: main Code may commit, Plan/Explore subagent must NOT, scheduled Local Code session may [Phase 3.5 HELD]). **Phase 3 execution gated on PR merge. HOLD Phase 3.5** (research-note §7.5 local scheduled-task poller option SURFACED, not decided) | `d10073e` / `docs/plans/0009-subagent-topology.md` + `.claude/handoffs/session-10/2026-05-25-1240-cowork-plan0009-review-dispatch.md` |
| 2026-05-25 | **PLAN-0008 AC-1 CORROBORATED via Auto mode bonus run + layer orthogonality CONFIRMED in production** — A second AC-1 live verification run (2026-05-25 00:30–00:32) using **Mode = Auto** in a fresh worktree session: task `"สร้าง docs/CHANGELOG.md สรุป Phase 2 PRs #9-#17, commit บน branch ใหม่, ไม่ต้อง push"`, single Cray paste, no further input. Result: **≥ 4 auto-continues, 0 permission prompts (Auto mode skipped them all), 0 Telegram pings, terminal pause at commit done** (followed explicit "ไม่ต้อง push" instruction — no over-step). Commit `6dc808c` on branch `chore/phase2-changelog` (unpushed per instruction). **Layer orthogonality confirmed**: Mode (PreToolUse harness layer) ↔ PLAN-0008 (Stop classifier layer) operate independently — Auto mode eliminates per-tool prompts without changing Stop-continuation decisions. **Minor finding for PLAN-0009 carry-over**: `_loop_counter._normalize_file_path()` strips main-repo prefix but does not collapse worktree path suffix (L1 counter key showed `.claude/worktrees/busy-bose-eedc8f/docs/CHANGELOG.md` instead of `docs/CHANGELOG.md`). Non-blocking; per-session isolation works correctly. Both AC-1 evidence runs documented in Current Focus comparison table. Cost: ~$0.004 (4 classifier calls × ~$0.001) | PR #20 amendment / `docs/STATUS.md` |
| 2026-05-25 | **PLAN-0008 AC-1 VERIFIED — Phase 2 fully audited** — Cray ran the live AC-1 task in a fresh Code session (task: *"ตรวจ ruff + mypy ทั้ง project, แก้ warning ถ้ามี, commit"*, single Cray paste, no further input). Agent self-continued **≥ 5 consecutive turns** without Cray paste (initial scan → file inspection → plan → branch creation → 5 file fixes → re-verify → tests → commit), then paused at the `git push` boundary asking permission — classifier correctly identified push as state change outside worktree per `feedback_state_change_outside_worktree.md` memory pattern. **0 Telegram pings** (no `cap_reached`, no L1–L4 false-positives). `stop-chain.json` `depth: 0` at end (consistent with terminal pause resetting chain). Side effect: the session surfaced 21 project-wide mypy errors in `tools/` + `tests/` (outside the pre-commit gate scope) and shipped a cleanup commit `8fef3a5` — PR #18 follows separately. Confirms classifier conservatism bias (spurious pauses > spurious proceeds, per OQ-B) works in production. Phase 2 all 4 ACs now VERIFIED; entry conditions for PLAN-0009 (Phase 3 — subagent topology) met | PR #19 amendment / `docs/STATUS.md` + closeout handoff §1 |
| 2026-05-25 | **PLAN-0008 Phase 2 COMPLETE — Step 8 closeout MERGED** — PR #17 → `main` (`79fe373`), single `feat(claude)` commit `b3657d5` + merge. AC matrix at merge time: AC-2/AC-3/AC-4 VERIFIED; AC-1 deferred to live Cray-supervised observation (subsequent AC-1 row above closes this). Step 8 deliverables: +2 E2E tests (test_l3_traceback_inline_fires_on_threshold + test_l2_resets_on_pass_for_same_nodeid; 387 → 389 pass / 6 skip); closeout handoff at `.claude/handoffs/session-10/2026-05-25-0130-code-plan0008-phase2-closeout.md` (gitignored local working note per CLAUDE.md §11); `git mv docs/plans/0008-...md docs/plans/done/`; STATUS final bump. Phase 3 (subagent topology, ADR-013 D1 phased) entry conditions met. **Reflexive H1 hook fire on the closeout handoff frontmatter** (`phase: completion` initially invalid; corrected to `phase: closeout` per enum) — N=3 production-validation events through this session (L1 in PR #15, L1-attempt in PR #16, H1 in this PR) prove the deterministic + classifier-mediated layer is reachable from real agent activity | `79fe373` (PR #17) / `docs/plans/done/0008-harness-autonomy-layer-phase-2.md` |
| 2026-05-25 | **PLAN-0008 Step 7 (Phase 2 integration tests + mypy hook coverage extension) MERGED** — PR #16 → `main` (`9100e65`), single `test(claude)` commit `d870d76` + merge. New `tests/handoffs/test_phase2_integration.py` with 15 E2E scenarios driving real subprocess invocations of all 3 wired Phase 2 hooks against a local mock HTTP Sonnet server (ephemeral 127.0.0.1 port via `socketserver.TCPServer` + threading daemon; `$CLAUDE_SONNET_API_URL` override; no live network). Coverage: Stop↔classifier wiring (proceed→block, pause→no-block, fail-closed, re-entry guard — mock receives 0 requests = negative proof); chain-cap fail-safe + cap_reached Telegram; observer→state→PreToolUse deny on L1+L4 + Cray-E.4 payload assertion; L4 reset on success; L2 inline Telegram on pytest-fail threshold; L1 turn-boundary survive vs reset; chain depth progression. Pre-commit `mypy` glob extended `^(services\|verticals)/` → `^(services\|verticals\|\.claude/hooks)/` (closes Step 1 follow-on; all 9 hooks pass `--strict`). 372 → 387 pass / 6 skip (+15). Per-test isolation via `tmp_path` for state + classifier fallback path + telegram capture + chain file. AC-3 demonstrated E2E for the first time | `9100e65` (PR #16) / `tests/handoffs/test_phase2_integration.py` |
| 2026-05-25 | **Cross-env Anthropic key file setup completed (Step 5b follow-up)** — Code copied WSL `~/.claude/.anthropic_api_key` to Windows `C:\Users\crayj\.claude\.anthropic_api_key` with NTFS ACL tightened to `crayj` user only (SYSTEM + Administrators removed — strictly tighter than chmod 600). Both `Path.home() / ".claude" / ".anthropic_api_key"` resolution paths verified: WSL Python finds at `/home/crayj/.claude/...`, Windows Python finds at `C:\Users\crayj\.claude\...`. Hook firing path (Windows-spawned hooks) and pytest path (WSL-spawned via Bash tool) both unblocked for live Sonnet operations | `C:\Users\crayj\.claude\.anthropic_api_key` (NTFS user-only) |
| 2026-05-24 | **PLAN-0008 Step 5b (Sonnet classifier config-file fallback) MERGED — defeats Claude Desktop ANTHROPIC_API_KEY strip** — PR #15 → `main` (`3d4f98b`), single `fix(claude)` commit `472a91e` + merge. Diagnosed during Step 6 post-merge env-propagation verification: Claude Desktop on Windows launches `claude.exe` with `ANTHROPIC_API_KEY=""` (intentional OAuth/billing isolation); WSLENV cannot defeat even after full computer restart. Step 5 live proof passed only because Cray ran pytest from a terminal launched outside Desktop. Fix: `_sonnet_classifier.py::_resolve_api_key()` chain → env → `~/.claude/.anthropic_api_key` (chmod 600 POSIX, override via `$CLAUDE_ANTHROPIC_KEY_FILE`) → fail-closed. +10 unit tests (372 pass / 6 skip; also fixed `test_stop_continuation.py` fixture to defang via file path too). `.gitignore` extended. PLAN-0008 §Step 5 + STATUS amended. Auto-memory `project_claude_desktop_strips_anthropic_api_key.md` captured. **Live-verified inside Claude Code session**: empty env → file fallback → real Sonnet 3.04s round-trip → `proceed` decision (proof complete). **Bonus event**: my own L1 loop-detect hook (Step 2) fired on me during the 6 pragma-fix Edits — Cray ratified Bash sed workaround; hook works as designed | `3d4f98b` (PR #15) / `.claude/hooks/_sonnet_classifier.py` |
| 2026-05-24 | **PLAN-0008 Step 6 (Wave 2 completion — autonomy-triggers row flips + PLAN closeout) MERGED** — PR #14 → `main` (`626ab23`), single `docs(claude)` commit `aa64d19` + merge. Docs-only flip of `.claude/autonomy-triggers.md` row labels from placeholder / "Phase 2 spec" wording to **LIVE** with concrete hook attribution: G1/G2/G3/G4/C1/C2/C3 → `_sonnet_classifier.py`; L1–L4 → 3-hook attribution (gate + writer + reset); status banner + "How the classifier reads this file" §flipped to LIVE with conservatism-probe evidence; footer date bumped. PLAN-0008 §Step 6 amendment box rewritten as "Step 6 closeout" with PR #11/#12/#13 lineage. `.claude/settings.json` `_comment` corrected (stub removal happened in PR #13). 362 pass / 6 skip baseline preserved (docs-only; ruff/mypy no scope). Closeout: this STATUS row | `626ab23` (PR #14) / `.claude/autonomy-triggers.md` |
| 2026-05-24 | **PLAN-0008 Step 5 (Sonnet classifier + stub swap) MERGED + live conservatism proof + WSLENV permanent fix + session handoff to new Code** — PR #13 → `main` (`3407ae6`), single `feat(claude)` commit `ceebc1a` + merge. New `.claude/hooks/_sonnet_classifier.py` (~225 lines, stdlib urllib + 7 fail-closed paths + retry + markdown-fence extractor; pin `claude-sonnet-4-6` per OQ-B). Stop hook stub replaced via lazy-import `_classify()` wrapper with double-fallback. 17 mocked tests + 1 live opt-in (362 pass / 6 skip). **LIVE conservatism proof (Cray 2026-05-24):** bare Stop = proceed; G1/G2/C2 triggered scenarios = pause with correct row IDs; routine work = proceed. Total ~$0.005 cost. **WSLENV permanently extended** with `ANTHROPIC_API_KEY/u` so future sessions inherit the key without workaround. **Session-10 ↔ next-session handoff** at `.claude/handoffs/session-10/2026-05-24-2030-code-step5-merged-step6-kickoff.md` — Cray-directed to preserve context-window headroom + double-test WSLENV propagation from clean process tree. Closeout: this STATUS row | `3407ae6` (PR #13) / `.claude/hooks/_sonnet_classifier.py` |
| 2026-05-24 | **PLAN-0008 Step 4 (Stop hook + L1 turn-boundary reset, expanded scope) MERGED** — PR #12 → `main` (`b09bf39`), single `feat(claude)` commit `010ae1b` + merge. 5-piece bundle: stop_continuation.py (Stop hook with re-entry guard + L1 turn-boundary reset + chain depth + cap-hit policy + classifier stub) + _loop_counter.py amendment (turn_touched field + 3 helpers) + observer amendment (records turn_touched on Write/Edit) + early Wave-2-partial settings.json wire for Stop + 26 new tests. **🔴 L1 reset gap CLOSED** per Cray-ratified scope expansion (AskUserQuestion "Expanded (Recommended)"): Stop hook reads turn_touched and resets L1 counters whose targets were NOT touched this turn, implementing PLAN §Step 1's "untouched on next turn-boundary marker" semantic. Classifier inside Stop hook is stubbed (pause-by-default) until Step 5 lands real Sonnet helper. 346 pass / 5 skip (was 320 / 5; +26: 18 stop + 7 turn_touched + 1 observer). Closeout: this STATUS row | `b09bf39` (PR #12) / `.claude/hooks/stop_continuation.py` |
| 2026-05-24 | **PLAN-0008 Step 3 (PostToolUse progress observer + Wave 1 wire + PLAN amendment) MERGED + Step 4 prioritization for L1 reset gap** — PR #11 → `main` (`632a22c`), single `feat(claude)` commit `1c2a7b6` + merge. Wave 1 hooks live in `.claude/settings.json` (L1/L4 gate via Step 2 + L2/L3 inline Telegram via Step 3 + L4 increment-on-failure / reset-on-success). PLAN-0008 §Step 3 + §Step 6 amended with Wave 1/2 split rationale. **ELI-CTO review surfaced 🔴 L1 reset gap** (counter grows unbounded within session until Step 4 turn-boundary reset lands; Cray's STATUS.md iterative workflow at risk of false-positive deny — already 4 of 6 edits used pre-merge). Cray prioritized Step 4 with proper turn-boundary reset impl (not just Stop-hook stub). 31 new tests (pytest 320 / 5 skip). Closeout: this STATUS row | `632a22c` (PR #11) / `.claude/hooks/posttooluse_progress_observer.py` |
| 2026-05-24 | **PLAN-0008 Step 2 (PreToolUse loop-detect hook) MERGED + Wave 1/2 settings.json activation decision (Option C) RECORDED** — PR #10 → `main` (`9494f93`), single `feat(claude)` commit `ad2c047` + merge. New `.claude/hooks/pretooluse_loop_detect.py` (~185 lines) reads Step 1 state, gates L1 (Write/Edit ≥ 6 same file) + L4 (Bash ≥ 6 same tokenized command), fires Cray-E.4 Telegram payload + deny on trigger. L2/L3 explicitly NOT enforced at PreToolUse (2 lock-in tests; routed to Step 3 inline firing). Env-var overrides spoof-immune. 24 new tests with Telegram-stub fixture capturing real payload (pytest 289 / 5 skip). **Wave 1/2 decision (Cray-adjudicated 2026-05-24, Option C):** Step 3 PR wires Step 2 + Step 3 hooks together in `.claude/settings.json`; Step 6 PR wires Step 4 + Step 5 hooks. Rationale: L1/L4 standalone deployable + early smoke catches integration bugs + matches Phase 1 phased pattern. PLAN-0008 §Step 3 + §Step 6 will be amended in the Step 3 commit per documentation option (3). Closeout: this STATUS row | `9494f93` (PR #10) / `.claude/hooks/pretooluse_loop_detect.py` |
| 2026-05-24 | **PLAN-0008 Step 1 (loop-counter state module) MERGED** — PR #9 → `main` (`2b303a0`), single `feat(claude)` commit `e20a6f3` + merge. New `.claude/hooks/_loop_counter.py` (~340 lines, stdlib-only) ships the schema + atomic I/O + 4 normalization helpers (file path / pytest nodeid / error signature / bash command) + session-ID resolution per **OQ-A** + counter ops with `last_6_actions` ring buffer per Cray E.4 payload contract. Step 2 (PreToolUse loop-detect hook) READS this module's state; Step 3 (PostToolUse progress observer) WRITES it. 49 new tests (`tests/handoffs/test_loop_counter_state.py`) incl concurrent-write race; pytest 265 pass / 5 skip (was 216 / 5); ruff + mypy --strict + detect-secrets clean. Closeout: this STATUS row | `2b303a0` (PR #9) / `.claude/hooks/_loop_counter.py` |
| 2026-05-24 | **PLAN-0008 (Phase 2 harness autonomy layer) DRAFTED + MERGED** — PR #8 → `main` (`ec5e2ae`), 3 commits (`b53763d` draft + `5a34ab0` OQ resolutions + merge). Phase 2 layers probabilistic / classifier-mediated engine on top of Phase 1 deterministic hooks: `Stop` continuation loop (`stop_hook_active` + `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP=8`) + Sonnet pause/proceed classifier (fail-closed, pin `claude-sonnet-4-6`, reads `.claude/autonomy-triggers.md` verbatim) + stateful loop-detection L1–L4 via `.claude/state/loop-counter.json` (gitignored; payload `{loop_type, target, last_6_actions}` per Cray E.4). 4 ACs incl **AC-4 Phase 1 regression-free** (16-case bypass-immune commit-deny + handoff-validator + C4 stay green). All 7 OQs adjudicated by Cray (A/B/C/E/F/G approve Code recommendations; **D auto-handoff Code→Cowork DEFERRED to PLAN-0009** — K-1/K-2 forcing fact blocks Cowork read-side so auto-draft does not reduce the human-relay bottleneck ADR-013 §Context targets; Plan subagent = right author per ADR-013 D1; surface bloat = step-sized design comparable to classifier). Status: Ready for execution. Step 1 (`.claude/state/` design + loop-counter schema) next on `feat/plan0008-step1-state-design`. Cowork-drafted under interim ADR-009 D1 (ADR-013 D1 phasing); Code committed per ADR-009 D2 | `ec5e2ae` (PR #8) / `docs/plans/0008-harness-autonomy-layer-phase-2.md` |
| 2026-05-24 | **Research-path enforcement (C4 hook) MERGED** — PR #7 → `main` (`da4f91d`). New `.claude/hooks/pretooluse_research_path_deny.py` blocks `Write`/`Edit` under `docs/research/` outside `docs/research/private/**`. Third deterministic Phase-1 row in `.claude/autonomy-triggers.md` (C4, alongside G5 git-deny + H1 handoff-validator). Trigger = N=2 violations of the documented rule (`cowork_tab_instructions.md` line 192 + `.gitignore` lines 49-51) in 8 days: Lesson #5 §10.5 (2026-05-15, `docs/strategy/public/` drop) + 2026-05-23 (`chat_harness_extension_points_analyzed.md`, detected during PLAN-0007 post-merge cleanup). Applies ADR-013 D2 precedent (documented-rule violation twice → promote to deterministic hook). 20 new tests (216 pass / 5 skip total, +20 from baseline); Windows-UNC path-normalization robust to host (backslash→forward-slash before pathlib). Closeout: this STATUS row | `da4f91d` (PR #7) / `.claude/hooks/pretooluse_research_path_deny.py` |
| 2026-05-23 | **PLAN-0007 Phase 1 (Harness autonomy layer) MERGED** — PR #6 → `main` (`b2ea9b8`), 9 commits (6 Phase A + 3 Phase B). All three ACs green incl live: AC-2 bypass-immune commit boundary verified across 16 test cases (inline `CLAUDE_TIER=code` env-spoof attempt, `bash -c`, backtick chains, `git -C path`, env prefix, `&&` chains — all denied; legitimate Code-tier commit allowed); AC-1 AFK Telegram ping verified end-to-end by Cray after token rotation + `WSLENV` setup; AC-3 handoff frontmatter auto-validator blocks on hard errors. OQ-3 resolved by Code: env marker `CLAUDE_TIER=code` (rejected file marker spoofable by `touch && commit`, cwd heuristic too coarse, settings-scope has no per-session distinction). `.claude/autonomy-triggers.md` registry shipped with G1–G5 / C1–C3 / H1 active and L1–L4 loop-detect rows flagged "Phase 2 enforcement". Plan moved to `docs/plans/done/`. Phase 2–4 (Stop continuation loop + Sonnet classifier + stateful loop-detection + subagent topology + MCP bus) → PLAN-0008+ | `b2ea9b8` (PR #6) / `docs/plans/done/0007-harness-autonomy-layer-phase-1.md` |
| 2026-05-23 | **ADR-013 (Autonomy axis relocation, Direction B) ACCEPTED + PLAN-0007 committed + T3–T6 follow-ons landed** — Cray ratified Direction B in free-form and adjudicated E.1–E.5 + OQ-1/2/3 (OQ-3 PreToolUse session-identity mechanism delegated to Code). ADR-013 D1 amends ADR-009 D1 (execution-automation axis relocates to Code + subagents; Cowork retained as advisory governance drafter per OQ-1); D2 preserves + reinforces "only Code commits" via deterministic PreToolUse deny hook (bypass-immune); D3 extends ADR-012 (free-form venues retained); D4 classifier=Sonnet + registry `.claude/autonomy-triggers.md`; D5 Telegram `@vero_tg_bot` env-var token. Branch `feat/plan0007-harness-autonomy-phase1` carries 5 governance commits (`770adf5` ADR-013, `c00dc98` PLAN-0007, `c45526b` CLAUDE.md §6 T3, `e64a4d2` tier instructions T4, `8eebe09` ADR-009/012 pointers T5). CLAUDE.md edit (T3) is constitutional — restart-bridge applies (Lesson #5 §1). Cowork-drafted, Code-committed per ADR-009 D2 | `8eebe09` / `docs/adr/0013-autonomy-axis-relocation.md` + `docs/plans/0007-harness-autonomy-layer-phase-1.md` |
| 2026-05-22 | **PLAN-0006 (LLM reasoning-hook) MERGED** — PR #5 merged to `main` (`68053fe`): `recommend()` is now LLM-backed (`gpt-oss:20b`, two-call Pattern B, deterministic rule fail-safe retained), new `services/engine/llm/` package + eval harness; ADR-001 Amendment 1 rode the same PR. Code-reviewed, no blockers; 173 passed / 0 skipped, coverage 94.56%. Post-merge: worktree + branch cleaned up | `68053fe` (PR #5) |
| 2026-05-22 | **ADR-001 Amendment 1 — `gpt-oss:20b` recommender-path pin (PLAN-0006 TODO-A)** — amends ADR-001's Primary-multimodal row for the OCT recommender path only: `gpt-oss:20b` + Ollama 0.24.0 supersedes `gemma4:26b`. Two independent grounds — `gemma4:26b` cannot complete the recommender's real nested-schema structuring call (>600s timeout vs gpt-oss 41s), and the still-live Ollama #15260 `think`/`format` interaction. gemma4's vision/multimodal role + `qwen2.5-coder:32b` untouched; cloud-fallback posture unchanged. Cowork-drafted (ADR-009 D1), Code-reviewed + committed onto the PLAN-0006 branch (Cray's routing call); live digest `17052f91a42e` captured | `30d2c8e` / `docs/adr/0001-llm-model-baseline.md` |
| 2026-05-22 | **PLAN-0006 (LLM reasoning-hook execution) EXECUTED — the brain swap** — `recommend()` is now LLM-backed (two-call Pattern B on `gpt-oss:20b`, fail-safe to the retained rule path). New `services/engine/llm/` package (client/prompt/structured/trace) + eval harness. CHECKPOINT-0 pinned `gpt-oss:20b` on Ollama 0.24.0 (#15260 still live for Qwen3.x). SC-1 resolved (reduced `LlmJudgment` sub-schema; ADR-007 D2 envelope unchanged). A Step-7 live capture surfaced + fixed a `suggested_handler` defect. 8 commits on `feat/plan0006-llm-reasoning-hook` (unmerged); 168 passed / 5 skipped, coverage 94.56%. TODO-A (ADR-001 amendment for the pin) pending Cray | `4f13b50`..`2fe1056` |
| 2026-05-22 | **PLAN-0006 (LLM reasoning-hook execution) drafted + committed** — the execution plan for the ADR-010 brain swap; Cowork-authored (Tier 1), Code R2-reviewed (fact-pack verified vs the live repo). Cray adjudicated SD-1..SD-5: async `recommend()` + retry 3, two-call Pattern B trace, gpt-oss-20b primary (provisional, Step-0-gated), raw structured-output (no new dep), seam-only hosted fallback. Next = Phase-1 kickoff dispatch | `d3a781e` / `docs/plans/0006-llm-reasoning-hook-execution.md` |
| 2026-05-22 | **C-2 Suffix-enum divergence RESOLVED — option α (expand the enum)** — Cray adjudicated α: `tools/handoffs/_schema.py:Suffix` gains `dispatch`/`completion`/`consultation`; PLAN-004 D4 + `handoff-frontmatter-schema.md` register them; 2 regression tests. Closes the schema ↔ `cowork_tab_instructions.md` divergence. `discussion` deliberately excluded (ADR-012 carries it via `phase:`). | `db9c5ed` |
| 2026-05-22 | **ADR-012 (Cowork second free-form tier) ACCEPTED** — amends ADR-009 D5: Cowork gains a second free-form role (Tier-1b — repo-grounded discussion / thinking-partner / informal code review) alongside Chat, which is **retained** (D5 extended, not revoked). D2 routing: Chat = repo-blind blue-sky, Cowork = repo-grounded. Adopted by Cray as a guarded trial (option α), regression triggers R-FF1..R-FF4 as exit criteria; commit authority stays Code-exclusive. T1 ADR + T2-T6 follow-on amendments (cowork/chat instructions, ADR-009 D5 pointer, CLAUDE.md §6, this STATUS row) committed by Code | `7916b39` / `docs/adr/0012-cowork-second-freeform-tier.md` |
| 2026-05-22 | **ADR-010 (LLM reasoning-hook surface) ACCEPTED** — five decisions fixing how an LLM replaces the rule recommender: D1 local-LLM-default + Claude-API consent-gated fallback (Cray-ratified), D2 schema-constrained output + retry, D3 hybrid reasoning trace, D4 approval gate = guardrail, D5 `recommend()` LLM-backed under the same signature; ADR-007 D2 envelope unchanged. Drafted by Cowork from two Tier-0 briefs; next = PLAN-0006 | `48fe240` / `docs/adr/0010-llm-reasoning-hook-surface.md` |
| 2026-05-21 | **mypy pre-commit gate extended to `verticals/`** — the hook now covers `^(services\|verticals)/`, not just `services/`; closes the flagged coverage gap (verified `pre-commit run mypy --all-files`) | `9dd1470` |
| 2026-05-21 | **PLAN-0005 Phase 2 — OCT Engine Runtime Layer MERGED** (PR #4, 13 commits) — DataAdapter Protocol + RecommendedAction envelope + vertical registry + rule-based recommender/approval gate + energy synthetic adapter + persistence (real `postgres:16-alpine`, SQLAlchemy 2.0 async + Alembic) + three-layer API wiring + end-to-end action loop; 109 tests, coverage 95.34%; six §8 OQs honoured; DDL/ORM parity test (C-1/R6) green; PLAN-003 + PLAN-0005 moved to `done/` | `c646bab` (PR #4) / `docs/plans/done/0005-oct-engine-runtime-layer.md` |
| 2026-05-21 | **ADR-009 ACCEPTED + 7-commit atomic PR #3 MERGED (`08117d5`)** — Cowork becomes Tier-0+1 merged workspace (dispatch/ADR/PLAN authoring), Chat narrows to free-form discussion only (D5 b), commit authority stays Code-exclusive (D2), K-1/K-2 workflow codified durably (Lesson #8). Hypothesis from parent discussion (2026-05-20-1235) supported by round 1 + round 2 trials (PASS / PASS). Commits 7c5c728 (ADR-009) → 601cdd4 (ADR-007 pointer T7) → 6759949 (cowork_tab T3) → dd9fe76 (chat_tab T4) → b6bf400 (Lesson #8 T6) → af6f858 (CLAUDE.md §6 T2) → e9f499b (STATUS T5). **Cray TODO:** re-paste cowork/chat tier instructions into Claude Desktop UI (repo canonical, UI sync target per CLAUDE.md §4) | `08117d5` / `docs/adr/0009-cowork-tier1-tier-topology.md` |
| 2026-05-20 | **PLAN-003 Phase 1 merged** (PR #2) — `services/engine/` package + 5 emitters + `verticals/energy/ontology/energy_v0.yaml` (ADR-008 D2 grammar; 6 object_types + 7 link_types) + L1 commit-time gate + `vero-lite` entry-point; 24 engine tests; coverage 94.06%; ADR-008 D2 binding per dispatch R-K1; PLAN-003 §8.6 list-of-dicts illustration is REJECTED at L1 (schema-fidelity guarantee) | `30619b8` |
| 2026-05-20 | PLAN-003 Phase 1 kickoff dispatch authored by Cowork-as-Tier-1 (trial test-bed); Code R2 pre-execution PASS; mid-execution C4=0 (no Lesson #6 firings during commits 1-7); trial-protocol §7.3 adjudication queued for Cray | `.claude/handoffs/session-10/2026-05-20-1530-cowork-plan003-phase1-kickoff-dispatch.md` |
| 2026-05-20 | PLAN-003 plan doc landed — `docs/plans/0003-ontology-engine.md` (427 lines); Phase 1 only (5 emitters: Pydantic+SQL+JSON Schema+MCP+TS-light); Typer CLI + ruamel.yaml parser + jsonschema; Alert↔OperationalEvent via explicit join object type (ADR-008 D4 stays; `many_to_many` deferred); coverage ≥70% aspirational (R-8); 3 J-class surfaces logged in dispatch closeout | `a7c68a2` |
| 2026-05-20 | PLAN-004 Phase A Batch 2 COMPLETE — Step 2a (20 files) + 2b.1 (12 renames + ref-graph, 5-ratification surface→re-dispatch chain) + 2b.2 (post-recovery, single-pass). Handoff-class schema-FAIL = `{}` | `ad81e7e` (2b.2 anchor), `098f8cd` (2b.1), `7f5035f` (2a) |
| 2026-05-20 | Strategic pivot — Option-1: pause PLAN-004 Phase B/C, prioritize PLAN-003 (Ontology Engine = the moat) | Cray decision 2026-05-20 |
| 2026-05-20 | Chat dispatch tooling/schema pre-verification protocol codified (operational layer; durable Lesson #8 mint deferred post-Phase-A per Q3=A) | `be38bce` `docs/conventions/chat_tab_instructions.md` |
| 2026-05-19 | PLAN-004 v2 Phase A Batch 1 landed | Schema doc + tools/handoffs/{_schema,validate_handoff,handoff_status}.py + ≥14 tests + runbook cross-link + CLAUDE.md §10 widening (docs/ → docs/ + tools/, Option B per Code midflight) | `9afde79` |
| 2026-05-17 | §11 Transcript Handoff ratified — Lesson #5 §2 "Cray-direct constitutional codification path" sub-rule + runbook §4 refresh + runbook §2 helper | `8d570b4` |
| 2026-05-16 | CLAUDE.md §11 "Transcript Handoff" constitutional subsection promoted — first instance of Cray-direct codification path (Lesson #5 §2 sub-rule) | `dd65d9b` |
| 2026-05-16 | Transcript tooling + runbook landed — `tools/handoffs/render_transcript.py` (stdlib-only, mypy-strict) + tests + `docs/runbooks/transcript-handoff.md` | `98e5591` |
| 2026-05-16 | Lesson-numbering offset sweep — `Lesson #12/#13/#14` → `#2/#3/#4` across repo (full normalization) | `c85a595` |
| 2026-05-16 | Lesson #5 audit baseline applied — `docs/lessons/0005-tier-system-audit-2026-05-15.md` (10 findings, tier-system audit); in-repo references normalized | `8274a66` |
| 2026-05-15 | Governance mini-batch — CLAUDE.md §1 precedence + §6 4-tier table + §11 Tier 2 ops; `docs/conventions/{chat,cowork}_tab_instructions.md` canonicalized | `ac3baf3` |
| 2026-05-13 | ADR-007 (OCT engine contracts) + ADR-008 (YAML ontology specification) — both Accepted | `docs/adr/0007-oct-engine-contracts.md`, `docs/adr/0008-yaml-ontology-specification.md` |
| 2026-05-13 | Cowork Tier 0 first deliverable — Palantir Foundry ontology reference brief (validates ADR-008's 4-tier model; cited from ADR-008 §Context as influencing reference) | `docs/research/private/2026-05-13-palantir-ontology-reference.md` |
| 2026-05-11 | ADR-006 — Vertical Plugin Architecture (D1–D4 + 5 core patterns; template-first multi-vertical) | `docs/adr/0006-vertical-plugin-architecture.md` |
| 2026-05-11 | ADR-005 — Strategic Pivot from SMB vet clinic to Operational Control Tower (vet clinic parked as Phase 2) | `docs/adr/0005-strategic-pivot-to-oct.md` |
| 2026-05-10 | ADR-004 closed — GitHub noreply alias as canonical author email (provisional) | `docs/adr/0004-canonical-author-email.md` |
| 2026-05-10 | Worktree mode policy codified in CLAUDE.md §6 (per Lesson #3) | `CLAUDE.md` §6 |
| 2026-05-10 | Handoff rotation policy codified in runbook | `docs/runbooks/claude-code-chat-handoff.md` |

## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [x] **ADR-007** — OCT engine contracts (DataAdapter, RecommendedAction, three-layer wiring) *(Session 10 Batch 3)*
- [x] **ADR-008** — YAML ontology specification (5 base types, JSON Schema validation) *(Session 10 Batch 3)*
- [x] **`.gitignore` extension** — add `docs/research/private/` (Cowork closeout flag #1) *(Session 10 Batch 3-prep)*
- [x] **PLAN-0005 Phase 2 — OCT Engine Runtime Layer** — DataAdapter Protocol + RecommendedAction envelope + vertical registry + rule-based recommender/approval gate + energy synthetic adapter + persistence (postgres:16-alpine, SQLAlchemy/Alembic) + three-layer API wiring + e2e action loop; merged PR #4 (`c646bab`) *(Session 10, 2026-05-21)*
- [x] **ADR-010 — LLM reasoning-hook surface** — D1 inference backend Cray-ratified (local LLM default + Claude API consent-gated fallback); D2–D5 recommended; ADR-007 D2 envelope unchanged *(Session 10, 2026-05-22; commit `48fe240`)*
- [x] **PLAN-0006 — LLM reasoning-hook execution** — EXECUTED. Steps 0-8 of the Phase-1 kickoff dispatch done on `feat/plan0006-llm-reasoning-hook` (8 commits `4f13b50`..`2fe1056`, **unmerged**); CHECKPOINT-0 pinned `gpt-oss:20b` / Ollama 0.24.0; new `services/engine/llm/` package + eval harness; `ruff` + `mypy --strict` clean, 168 passed / 5 skipped, coverage 94.56%. Closeout: `.claude/handoffs/session-10/2026-05-22-2355-code-plan0006-kickoff-dispatch-closeout.md`. *(Session 10, 2026-05-22)*
- [x] **PLAN-0008 Step 5 — Sonnet classifier helper + stub swap (MERGED) + LIVE conservatism proof** — PR #13 → `main` (`3407ae6`); 4-piece bundle: new `_sonnet_classifier.py` (~225 lines stdlib urllib + Anthropic Messages API + 7 fail-closed paths + retry + markdown-fence extractor; pin `claude-sonnet-4-6` per OQ-B) + `stop_continuation.py` stub-swap via lazy-import `_classify()` wrapper + 17 mocked tests + opt-in live via `RUN_LIVE_SONNET_TESTS=1` (OQ-G). 362 pass / 6 skip; ruff + mypy --strict + detect-secrets clean. **LIVE verification:** bare Stop = proceed; G1/G2/C2 = pause with correct row IDs; routine work = proceed. Cost ~$0.005. WSLENV permanently extended with `ANTHROPIC_API_KEY/u`. **Step 6 next (Wave 2 completion):** autonomy-triggers row flips + closeout note — on NEW Code session via handoff `.claude/handoffs/session-10/2026-05-24-2030-code-step5-merged-step6-kickoff.md`. *(Session 10, 2026-05-24)*
- [x] **PLAN-0008 Step 4 — Stop hook + L1 turn-boundary reset, expanded scope (MERGED)** — PR #12 → `main` (`b09bf39`); 5-piece bundle: stop_continuation.py (Stop hook + L1 reset + chain cap + classifier stub) + _loop_counter.py turn_touched primitives + observer amendment + early Wave-2-partial settings.json wire + 26 new tests. **🔴 L1 reset gap CLOSED.** Classifier stub returns pause-by-default; Step 5 swap is single function replacement. 346 pass / 5 skip; ruff + mypy --strict + detect-secrets clean. **Step 5 next:** `_sonnet_classifier.py` (stdlib urllib + Anthropic Messages API + fail-closed pause) on `feat/plan0008-step5-sonnet-classifier`. *(Session 10, 2026-05-24)*
- [x] **PLAN-0008 Step 3 — PostToolUse progress observer + Wave 1 wire + PLAN amendment (MERGED)** — PR #11 → `main` (`632a22c`); bundle of writer hook (`posttooluse_progress_observer.py`, ~260 lines, `_apply_l2`/`_apply_l3`/`_apply_l4` helpers) + Wave 1 `.claude/settings.json` wire (Phase 1 + Step 2/3 hooks live) + PLAN-0008 §Step 3 + §Step 6 amendment boxes. L2/L3 inline Telegram fire on trigger; L1/L4 let Step 2 gate. Defensive Bash exit-code detection. 31 new tests; pytest 320 pass / 5 skip; ruff + mypy --strict + detect-secrets clean. **ELI-CTO surfaced 🔴 L1 reset gap (real op risk).** **Step 4 next (Cray-prioritized):** stop_continuation.py + L1/L3 turn-boundary reset + early Wave-2-partial Stop-hook wire — scope expansion under Cray surface. *(Session 10, 2026-05-24)*
- [x] **PLAN-0008 Step 2 — PreToolUse loop-detect hook (MERGED)** — PR #10 → `main` (`9494f93`); new `.claude/hooks/pretooluse_loop_detect.py` reads Step 1 state + gates L1/L4 ≥ 6 + fires Cray-E.4 Telegram payload + deny. Env-var overrides spoof-immune. L2/L3 explicitly deferred to Step 3 inline firing (2 lock-in tests). 24 new tests with Telegram-stub fixture; pytest 289 pass / 5 skip; ruff + mypy --strict + detect-secrets clean. **Wave 1/2 settings.json activation decision (Cray 2026-05-24, Option C):** Step 3 PR wires Step 2+3 hooks; Step 6 PR wires Step 4+5. **Step 3 next:** posttooluse_progress_observer.py + Wave 1 wire + PLAN amendment in one commit on `feat/plan0008-step3-posttooluse-progress-observer`. *(Session 10, 2026-05-24)*
- [x] **PLAN-0008 Step 1 — loop-counter state module (MERGED)** — PR #9 → `main` (`2b303a0`); new `.claude/hooks/_loop_counter.py` ships stdlib-only schema + atomic I/O + 4 normalization helpers (L1–L4) + session-ID resolution per OQ-A + counter ops with `last_6_actions` ring buffer. 49 new tests; pytest 265 pass / 5 skip; ruff + mypy --strict + detect-secrets clean. **Step 2 next:** `.claude/hooks/pretooluse_loop_detect.py` on `feat/plan0008-step2-pretooluse-loop-detect`. *(Session 10, 2026-05-24)*
- [x] **PLAN-0008 — Harness autonomy layer Phase 2 (DRAFT MERGED)** — PR #8 → `main` (`ec5e2ae`), 3 commits (`b53763d` draft + `5a34ab0` OQ resolutions + merge). Phase 2 scope: `Stop` continuation loop + Sonnet pause/proceed classifier reading `.claude/autonomy-triggers.md` verbatim + stateful loop-detection L1–L4 via `.claude/state/loop-counter.json`. 4 ACs incl AC-4 Phase 1 regression-free. All 7 OQs (A–G) adjudicated by Cray 2026-05-24 (Code recommendations approved; **OQ-D auto-handoff DEFERRED to PLAN-0009** per K-1/K-2 forcing fact + Plan subagent role + surface bloat). Status: Ready for execution. **Step 1 next:** `.claude/state/` design + `loop-counter.json` schema + `.gitignore` extension + atomic-write tests on `feat/plan0008-step1-state-design`. *(Session 10, 2026-05-24)*
- [x] **Research-path enforcement (C4 hook)** — MERGED. PR #7 → `main` (`da4f91d`); new `.claude/hooks/pretooluse_research_path_deny.py` deterministically blocks `Write`/`Edit` under `docs/research/` outside `docs/research/private/**`. Registered as C4 in `.claude/autonomy-triggers.md` next to G5 + H1. Trigger = N=2 documented-rule violations (Lesson #5 §10.5 + 2026-05-23 `chat_harness_extension_points_analyzed.md`) applying ADR-013 D2 precedent. 20 new tests; pytest 216 / 5 skip. *(Session 10, 2026-05-24)*
- [x] **PLAN-0007 — Harness autonomy layer Phase 1** — MERGED. PR #6 → `main` (`b2ea9b8`), 9 commits (6 Phase A governance: `770adf5` ADR-013 Accepted, `c00dc98` PLAN-0007, `c45526b` CLAUDE.md §6 T3, `e64a4d2` tier instructions T4, `8eebe09` ADR-009/012 pointers T5, `c048117` STATUS T6; 3 Phase B execution: `28fac01` telegram.sh, `711971c` settings + hooks + tests, `7c6ae65` autonomy-triggers registry). All ACs green incl live (AC-2: 16/16 bypass-immune tests; AC-1: live Telegram smoke verified by Cray; AC-3: handoff frontmatter auto-validator). OQ-3 resolved (CLAUDE_TIER=code env marker). Plan moved to `docs/plans/done/`. Closeout: `.claude/handoffs/session-10/2026-05-23-1606-code-plan0007-phaseB-closeout.md`. *(Session 10, 2026-05-23)*
- [x] **TODO-A — ADR-001 amendment (PLAN-0006 follow-on)** — DONE. ADR-001 Amendment 1 pins `gpt-oss:20b` + Ollama 0.24.0 for the recommender path (superseding `gemma4:26b` for that path only; gemma4's multimodal role + `qwen2.5-coder:32b` untouched). Cowork-drafted (ADR-009 D1); Code reviewed against the PLAN-0006 fact-pack + committed (ADR-009 D2) with the live `gpt-oss:20b` digest captured; rides the PLAN-0006 branch / PR #5 per Cray's routing call. *(PLAN-0006 kickoff dispatch §7 TODO-A; commit `30d2c8e`)*
- [x] **Suffix-enum vs cowork-instruction divergence** (PLAN-0005 §4 C-2) — RESOLVED via option α (expand the enum): `tools/handoffs/_schema.py:Suffix` gained `dispatch`/`completion`/`consultation`; PLAN-004 D4 + `handoff-frontmatter-schema.md` registered them; 2 regression tests in `test_schema.py`. `discussion` deliberately not added (ADR-012 carries it via `phase: discussion`). *(surfaced 2026-05-21; Cray adjudicated α 2026-05-22; `db9c5ed`)*
- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten (full table: PLAN-0005 §8.1): rule-based recommender → **ADR-010 ACCEPTED (2026-05-22) → PLAN-0006 next** (LLM reasoning hook); minimal approval gate → **ADR-011+** (audit framework — trigger: first design-partner data / PDPA review); no mapping layer → **dbt/SQLMesh** (trigger: first non-synthetic source); hand-authored ORM → **"ORM emitter"** Rule-of-Three candidate (trigger: 3rd vertical / DDL↔ORM parity-test drift); base Postgres only → **PLAN-002** (pgvector/AGE — trigger: semantic + graph features); explicit registry → **ADR-006 D3 L2** (trigger: vertical #2/#3 or `new-vertical` generator). *(per Cray note 2026-05-21)*
- [ ] **Phase-enum amendment** — add `consultation` (or equivalent Q&A-round value) to canonical Phase enum (Q15 of `2026-05-20-0245-code-plan003-pre-draft-consultation-reply.md`); requires touching `tools/handoffs/_schema.py` + `docs/conventions/handoff-frontmatter-schema.md` + validator tests; PLAN-004 Phase B adjacent. *(Deferred per R-9, 2026-05-20)*
- [ ] **Cleanup stale `ontology/README.md`** — 2026-05-05 PLAN-001 artifact; ontology directory canon now lives at `verticals/<name>/ontology/<name>_v0.yaml` per ADR-006 D1 / ADR-008 D5; superseded by PLAN-003. *(Deferred per R-9 cohort, 2026-05-20)*
- [ ] **PLAN-004 Phase B/C — DEFERRED (backlog, post-PLAN-003):** validator-scope exclusion (`README.md` / `_rename-map.md`, manifest §4.2/§6.1) + Cat G `references_*` autofix + Phase C handoff dashboard + OQ-2 systemic candidate (effective-vs-authored `status:` / archival flag so dead handoffs don't surface as actionable in the dashboard) + **validator warning-swallow bug** — `tools/handoffs/_schema.py` `_build()` (lines ~302–306) returns `Frontmatter` and discards its local `errors` list when no hard error exists, so `_check_unknown()` WARNING-severity findings (e.g. unknown field `brief-number`) are unreachable on otherwise-valid files; fix to surface warnings + add a regression test *(found 2026-05-22 dog-fooding the 4 Cowork LLM-hook handoffs; Cray routed → Phase B)*
- [ ] **ADR-NN (TBD, ≥ ADR-014) + PLAN-002** — Custom Postgres image with extensions (ADR-011 earmarked for the audit framework, ADR-012 taken, ADR-013 taken by autonomy axis relocation; floor bumped from ≥0013 to ≥0014 on 2026-05-23 per ADR-013 T6)
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (low priority)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)
- [x] Filesystem cleanup: `.claude/worktrees/sad-northcutt-6a48ff/` removed *(Session 10, 2026-05-21)*
- [x] **ADR-006** — Vertical Plugin Architecture *(Session 10 Batch 2)*
- [x] **ADR-005** — Strategic Pivot to OCT (vet clinic parked Phase 2) *(Session 10 Batch 2)*
- [x] **Directory scaffolds** — `verticals/{_template, energy, supply_chain, vet_clinic}/` + `docs/strategy/{public, private}/` *(Session 10 Batch 2)*
- [x] **Parked-note pass** — 6 vet-mentioning docs annotated *(Session 10 Batch 2)*
- [x] **ADR-004** — Canonical author email (GitHub noreply, provisional) *(Session 10)*
- [x] **Worktree mode policy** — codified in CLAUDE.md §6 *(Session 10)*
- [x] **Handoff rotation policy** — codified in runbook *(Session 10)*
- [x] **Phase G** — commit + PR + merge + cleanup *(Session 9)*
- [x] **Lesson #2 amendment** — Misdiagnosis section *(Session 9)*
- [x] **Lesson #3** — Code Tab worktree lifecycle traps *(Session 9)*
- [x] **File-based handoff mechanism** — `.claude/handoffs/` live *(Session 9)*
- [x] **Setup Claude Code on Windows** *(Session 8)*
- [x] **Cowork Project setup** *(Session 8)*
- [x] **PLAN-001** — Starter pack scaffold *(Session 4)*
- [x] **ADR-003** — Service port strategy *(Session 4)*
- [x] **Memory architecture implementation** *(Session 5)*
- [x] Lesson cleanup batch — Lesson #3 amendment + Lesson #5 §2/§3 amendment + Lesson #6 new *(done `96bf51b`, 2026-05-18)*
- [x] **PLAN-004 Phase A** — Batch 1 (schema + tools) + Batch 2 (2a: 20 files / 2b.1: 12 renames + ref-graph / 2b.2: post-recovery) complete *(Session 10, 2026-05-19/20; anchor `ad81e7e`)*
- [x] **PLAN-003 Phase 1** — Ontology engine + 5 emitters + `energy_v0.yaml` + L1 commit-time gate *(Session 10, 2026-05-20; merge `30619b8`, PR #2)*
- [x] Adopt Q1(b) closeout-template line "STATUS.md updated: yes/no/N/A" — adopted (closeouts carry the line)
- [x] Adopt Q3(b/c) dedicated `docs(status): …` housekeeping commit at batch close — adopted (`894a1e5` first instance; this 2b.2 close repeats)

## Next Steps

1. **PLAN-0008 Phase 2 — Step 6 execution (Wave 2 completion) — IN NEW CODE SESSION.** Step 5 (Sonnet classifier + stub swap) merged (PR #13 `3407ae6`) with live conservatism proof PASSED. **Step 6** per PLAN §Step 6: (a) flip the L1–L4 row entries in `.claude/autonomy-triggers.md` from "Phase 2 enforcement" placeholders to "Enforced via [hook name]" (matches the now-live Wave 1 + Wave-2-partial topology); (b) flip the G1/G2/C1/C2 + H1 row entries similarly where Wave 2 enforcement is now live; (c) confirm `.gitignore` carries `.claude/state/` (already done in Phase 1; verify); (d) update the registry footer line referencing classifier liveness; (e) PLAN-0008 §Step 6 closeout note marking Wave 2 complete. Branch: `feat/plan0008-step6-wave2-completion`. **NEW SESSION first action:** verify permanent WSLENV propagation — `wsl bash -lc '[ -n "$ANTHROPIC_API_KEY" ] && echo SET || echo UNSET'` should report SET (was UNSET in current session before today's setx). Then read handoff `.claude/handoffs/session-10/2026-05-24-2030-code-step5-merged-step6-kickoff.md`. Then Steps 7-8 (broader integration tests + live AC verification).
2. **PLAN-0008 Step 5 — MERGED.** [PR #13](https://github.com/CrayJThiemsert/vero-lite/pull/13) merged to `main` (`3407ae6`); `_sonnet_classifier.py` live; stub swapped; conservatism validated.
3. **PLAN-0008 Step 4 — MERGED.** [PR #12](https://github.com/CrayJThiemsert/vero-lite/pull/12) merged to `main` (`b09bf39`); Stop hook + L1 reset live; classifier stubbed.
4. **PLAN-0008 Step 3 — MERGED.** [PR #11](https://github.com/CrayJThiemsert/vero-lite/pull/11) merged to `main` (`632a22c`); writer hook + Wave 1 wire live; PLAN-0008 amended with Wave 1/2 split.
5. **PLAN-0008 Step 2 — MERGED.** [PR #10](https://github.com/CrayJThiemsert/vero-lite/pull/10) merged to `main` (`9494f93`); `pretooluse_loop_detect.py` gate live.
6. **PLAN-0008 Step 1 — MERGED.** [PR #9](https://github.com/CrayJThiemsert/vero-lite/pull/9) merged to `main` (`2b303a0`); `_loop_counter.py` state primitives live.
7. **PLAN-0008 — DRAFTED + MERGED.** [PR #8](https://github.com/CrayJThiemsert/vero-lite/pull/8) merged to `main` (`ec5e2ae`); plan lives at `docs/plans/0008-harness-autonomy-layer-phase-2.md` (will move to `done/` after Step 8 closeout).
8. **PLAN-0007 — MERGED + closed.** [PR #6](https://github.com/CrayJThiemsert/vero-lite/pull/6) merged to `main` (`b2ea9b8`); plan archived at `docs/plans/done/0007-harness-autonomy-layer-phase-1.md`.
9. **PLAN-0006 — MERGED + closed.** [PR #5](https://github.com/CrayJThiemsert/vero-lite/pull/5) merged to `main` (`68053fe`); plan archived at `docs/plans/done/0006-llm-reasoning-hook-execution.md`.
10. **PLAN-0005 §8.1 revisit register** — remaining deferred-foundational simplifications at their batch boundaries (audit framework → ADR-011+, mapping layer, ORM emitter, base-Postgres → PLAN-002 (≥ADR-014), registry discovery).
11. **Partner-trial readiness gaps** — `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` awaits a dedicated Cray discussion.
12. **Deferred (backlog)** — PLAN-004 Phase B (validator-scope exclusion; Cat G `references_*` autofix; validator warning-swallow bug) + Phase C (handoff dashboard); PLAN-002 custom Postgres image (≥ADR-014).
13. **Ongoing** — Continue exercising the file-based handoff mechanism (Chat ↔ Code ↔ Cowork) across batches.

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
