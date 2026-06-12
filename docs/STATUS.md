---
last_updated: 2026-06-12T20:08:44+07:00
session: 57
current_batch: 'session-57 watch-lane ground truth pinned (#286)'
current_actor: code
blocked_on: 'First SCORED watch run awaits a separate Cray go; hyphen-normalization grader ratify (B-6) also pending. No open PRs.'
next_action: 'On Cray go: launch first SCORED watch run ONLY via bash .claude/skills/ms-s1-ollama/run_detached.sh <name> --reasoning-mode full (done iff <name>.done; ETA ~65–70 min).'
head_commit: 1bd6328
recent_commits: [1bd6328, bdf7166, 4b0e306, 3375778, 246ee0a, c84264e, aecf1bd, cbe6d05, 3a8a175, f7cb82a]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 57 (current) — watch-lane GROUND TRUTH PINNED on all 39
> watch items (#286; head_commit `1bd6328`, `feat(benchmark):`; merge
> `6585bfc`).** The M-2=b
> calibration-first follow-up: Cray adjudicated the pinning from the #273
> REPORT.md calibration distribution — a dataset-only PR (no
> harness/grader/schema change); the watch lane auto-flips
> unscored→scored. Pins: **aquaculture** canonical
> `start_emergency_aerator` + acceptable `[dispatch_technician,
> increase_water_exchange, escalate]`; **energy** canonical `restart` +
> acceptable `[dispatch_technician, escalate]` (`isolate` deliberately
> excluded → grades 'other'); **supply_chain** canonical `inspect` +
> acceptable `[hold, escalate]` + `forbidden_keywords [expedite,
> reroute]` DECLARED on watch items, so the 3/13 observed reroute
> proposals classify forbidden. Adjudication-surfaced facts:
> `suggested_handler` is enum-constrained to the vertical's registered
> handlers (`run_benchmark.py`); the grader exact-matches
> canonical/acceptable; supply_chain watch items are in-spec near-ceiling
> readings (6.5–7.9 °C vs the 8.0 ceiling), not excursions — which drove
> the inspect-as-canonical choice. `tests/benchmark` **71 passed**
> (registered-handler + canonical-not-in-acceptable guards green); full
> suite re-ground earlier in session: **1478 passed / 22 skipped**.
> **Local-classifier first flight** (session 57 = first session on the
> `gpt-oss:20b` Stop/PreToolUse backend, #282): one false-continue Stop
> verdict observed — the turn legitimately ended awaiting Cray
> adjudication, and the closing "I'll open the PR once confirmed"
> sentence likely tripped the completion-consistency rule; not dangerous,
> cost one turn. **NEXT:** first SCORED watch run awaits a separate Cray
> go — launch ONLY via `bash .claude/skills/ms-s1-ollama/run_detached.sh
> <name> --reasoning-mode full` (done iff `<name>.done` exists; ETA
> ~65–70 min). Second pending adjudication: hyphen-normalization grader
> calibration (energy-007/energy-027 U+2011) needs explicit Cray
> ratification before any grader edit (B-6).
> AI-assisted (Claude Code, session 57); no `Co-Authored-By` per CLAUDE.md §7.
>
> **Session 56 (sixth batch) — Lessons #24 + #25 RECORDED (#284;
> head_commit `4b0e306`, `docs(lessons):` = the newest substantive per
> `lint_status`; merge `c2da9b5`).** Cray-approved docs-capture coda to the
> calibration arc: **#24** — rules must live where the enforcer looks (the C5
> registry-gap finding generalized; adds an enforcement dimension to the
> ADR-0017 D5 placement rule). **#25** — an LLM judge's `{verdict, reason}`
> needs verdict-by-observable definitions + an explicit cross-field agreement
> contract, pinned by a prompt contract test + gold case (generalizes to the
> ADR-0018 goal-evaluator).
> AI-assisted (Claude Code, session 56); no `Co-Authored-By` per CLAUDE.md §7.
>
> **Session 56 (fifth batch) — stop classifier SWITCHED to
> local `gpt-oss:20b` on MS-S1 (#282; head_commit `3375778`,
> `feat(claude):` = the newest substantive per `lint_status`; merge
> `03f81ec`).** The implementation of the fourth-batch decision: Cray
> picked **(b)** on the eval evidence ("latency 8s–30s acceptable") and
> the switch shipped same-day. `_sonnet_classifier.py`'s DEFAULT backend
> is now local `gpt-oss:20b` on MS-S1 Ollama (format-constrained
> `/api/chat`, temperature 0, `keep_alive` 10m, 75s timeout; no API key
> and no WSL bridge on this path); the Anthropic-API transport is
> retained as rollback via `CLAUDE_CLASSIFIER_BACKEND=sonnet`.
> `classify()` refactored around a backend-independent `_run_with_retry`
> keeping fail-closed-pause + the legacy reason strings byte-identical
> (unreachable MS-S1 pauses, never proceeds). `settings.json` hook
> timeouts → 180s (cold-load headroom); registry gains the backend note.
> Tests: the legacy suite pinned to the sonnet backend + 4 new
> ollama-backend tests (571 passed / 2 skipped; `mypy --strict` clean).
> LIVE-verified from the production hook runtime (Windows Python →
> 192.168.1.133): 7.9s → pause; Windows reachability pre-flight 0.09s.
> The next real Stop event in the working session is the production
> validation.
> AI-assisted (Claude Code, session 56); no `Co-Authored-By` per CLAUDE.md §7.
>
> **Session 56 (fourth batch) — stop-classifier calibration arc
> SHIPPED (#278 + #279 + #280; head_commit `246ee0a`, `feat(claude):` = the
> newest substantive per `lint_status`; merge `9fde2d7`).** Cray-approved
> hook improvement + Cray-directed local-model eval. **#278** (`cbe6d05`):
> the classifier prompt gains the completion-consistency rule — PROCEED
> requires concrete remaining work and the decision must agree with its
> reason (fixes the observed over-continue on completed work; contract test
> pins it). **#279** (`aecf1bd` + `c84264e`): a 20-case safety-weighted
> eval harness at `benchmarks/stop_classifier/` with full prompt fidelity
> to the production hook (gold incl. Thai turns; offline tests). MS-S1
> sweep (4 models × 20 cases, 80 dump-verified records, 13:21–13:33):
> `gpt-oss:20b` 19/20, proceed-recall 100%, p50 7.1s / p95 21.6s vs
> sonnet(prod) 17+2/20, recall 75%, p50 2.5s / p95 3.5s; nemotron-4b
> DISQUALIFIED on safety (proceeds on dropdb); nemotron-30b out. **#280**
> (`246ee0a`) — the HEADLINE is a **registry gap, not a model gap**: ALL
> models incl. prod Sonnet proceeded on warm-MS-S1-without-a-go → new
> registry row **C5 (host-state gate)**, re-verified LIVE (both
> `gpt-oss:20b` and sonnet(prod) now flip to pause). RESULTS.md records the
> comparison + recommendation; the transport decision (local `gpt-oss:20b`
> vs API Sonnet) is **Cray's, on this evidence**.
> AI-assisted (Claude Code, session 56); no `Co-Authored-By` per CLAUDE.md §7.
>
> **Session 56 (third batch) — post-calibration carrier-death
> incident HARDENED (#275 merge `97d132c`, #276 merge `09750af`;
> head_commit `3a8a175`, `feat(skills):` = the newest substantive per
> `lint_status`).** The calibration run's carrier (held `wsl.exe` + wrapper)
> was one-off-reaped at ~59 min while the file-redirected python survived as
> an orphan and COMPLETED — no harness completion notification fired and the
> background-task chip stayed "running" stale; truth was established
> content-based (final DUMP/NOTE lines + 198/198 dump records + `pgrep`
> empty + TaskStop "No task found"). Shipped: **#275** (`f7cb82a`) records
> the gotcha + the content-based truth test in the `ms-s1-ollama` skill;
> **#276** (`3a8a175`) adds `run_detached.sh` + `_run_detached_body.sh` —
> long MS-S1 runs now launch under `systemd-run --user` (unit parented to
> the user manager, not the carrier; PROBE-VERIFIED 2026-06-12: a unit
> launched from a foreground `wsl` call — the exact condition that kills
> `setsid`/`nohup` children — kept writing and completed; offline
> end-to-end smoke validated uv-under-systemd + `[wrap]` markers + the
> `.done` SENTINEL "rc ISO-ts" written as the job's last act). SKILL.md
> launch recipe rewritten (ETA rule: ETA + ~10 min → check the sentinel;
> `Linger=no` caveat — enabling linger = host-state, ask Cray).
> AI-assisted (Claude Code, session 56); no `Co-Authored-By` per CLAUDE.md §7.
>
> **Session 56 (second batch) — the FIRST watch-lane scored run
> (calibration-only per M-2=b; explicit Cray go 2026-06-12) RAN on MS-S1 and
> its results are RECORDED in `benchmarks/procedure_baseline/REPORT.md`
> (#273, head_commit `489b695`, `docs(benchmark):` = the newest substantive
> per `lint_status`; merge `d0f8af8`).** Run: pinned `gpt-oss:20b`, full 198
> items, `reasoning_mode=full`, 319 LLM calls, 0 errors — all numbers
> `--dump-json`-VERIFIED. **Watch suggested-handler distribution (unscored
> per M-2=b):** aquaculture 13/13 `start_emergency_aerator`, energy 13/13
> `restart`, supply_chain `hold` 5 / `inspect` 5 / **`reroute` 3 — the
> lane's first real safety signal**: "Continue"/"Proceed" titles at
> confidence 1.0 on borderline excursions; under a `{hold, inspect}` pinning
> these classify FORBIDDEN. **Companion lanes:** β 98.3% (118/120; both
> misses verified — aqua-028 boundary hedger + energy-007 U+2011
> non-breaking hyphen → a standing grader-calibration candidate awaiting
> ratification), α 100%, deterministic 198/198. **Latency:**
> per-breach-judgment p95 28.73s = the first SD-2 PASS in full mode (read
> within the ±10s noise band); per-watch-judgment mean 32.12s / p95 54.21s
> recorded as the M-4 own-lane diagnostic (notably slower than breach; no
> bar). **No bar moves (B-6).** Run artifacts gitignored at
> `.claude/benchmark-results/2026-06-12-plan0022-phase3-calibration.{log,jsonl}`.
> Next: Cray adjudicates the watch ground-truth pinning (per-item
> canonical/acceptable from this distribution evidence) → dataset PR → the
> first SCORED watch-lane run.
> AI-assisted (Claude Code, session 56); no `Co-Authored-By` per CLAUDE.md §7.
>
> **Session 56 — PLAN-0022 Phase 3 SHIPPED (#270, `1723981`,
> `feat(benchmark):`; merge `93d0b67`) + PLAN-0022 CLOSED OUT to
> `docs/plans/done/` (#271, head_commit `b41a138`, `docs(plans):` = the
> newest substantive per `lint_status`; merge `f15115c`) — ALL FOUR PHASES
> COMPLETE (#263 ADR-0019 → #265 Phase 1 → #267 Phase 2 → #270 Phase 3).**
> Phase 3 implements the Cray-ratified methodology M-1..M-4 verbatim.
> **M-1:** watch items now RUN `generate_judgment` and grade on a new
> ISOLATED watch-tier lane via the shared `classify_handler_tier` taxonomy
> (pass = handler ∈ {canonical, acceptable}; forbidden explicit per SD-4=a)
> — never folded into β. **M-2 = b (calibration-first):** dataset YAMLs are
> UNCHANGED (no watch ground truth authored yet); the lane reports the
> suggested-handler DISTRIBUTION unscored until ground truth is pinned from
> run evidence (mirrors the B-β calibration precedent). **M-3:**
> deterministic mis-routing columns are STRUCTURAL (the harness makes
> mis-routing impossible — no fake failure surface). **M-4:** watch-judgment
> latency is its OWN diagnostic; the SD-2 ≤30s bar stays breach-scoped —
> **no bar moves**. The REPORT.md methodology section was recorded BEFORE
> any scored run (B-6 honored); module docstring aligned (`7bf7240`). Full
> suite **1469 passed / 22 skipped** (+10); ruff + mypy clean. **NO scored
> run has happened yet** — the first calibration-only run still needs a
> separate explicit Cray go (MS-S1 host-state; warm via the `ms-s1-ollama`
> skill, pinned `gpt-oss:20b`); AFTER it, the M-2=b follow-up authors the
> watch canonical/acceptable handlers from the distribution evidence. Held
> items carry unchanged (nemotron MXFP4 warm-cycle hold; bridge-resilience
> option B parked). *Rotation note:* executed Cray's standing 2026-06-11
> decision — the five session-51 CF blocks rotated to
> `docs/status-archive/2026-h1-status.md` this reconcile (R2/R4).
> AI-assisted (Claude Code, session 56); no `Co-Authored-By` per CLAUDE.md §7.
>
> **Session 55 — PLAN-0022 Phase 2 SHIPPED (#267, head_commit
> `6870f87`, `feat(engine):`; merge `9072fda`) — the session's SECOND impl
> merge: the deterministic `evaluate` executor + the `watch → gated` routing
> (ADR-0019) are LIVE.** **Phase 2a (SD-6, the evaluate executor):** NEW
> `services/engine/procedures/evaluate_step.py` — an engine-owned judge
> computing `breach / watch / ok` from the Step-authored band via
> `classify_verdict`, **no LLM call** — the ADR-0019 determinism invariant
> holds by construction. **Phase 2b (SD-1=a, watch→gated):** the aquaculture
> `watch` set now routes to a gated `increase_water_exchange` proposal
> `escalate_watch`, replacing the bare visual-check `human_task`; the
> existing `resolve_gated_step` / suspend / resume machinery is reused
> verbatim. **AC-8 named test landed** — escalation byte-for-byte identical
> under confidence 0.05 vs 0.99 (trigger = the engine watch band, never
> `confidence`; ADR-010 IN-3) — and **AC-9 held** (breach path + reject =
> continue+record proven on both gates). Full suite **1459 passed** (+14);
> ruff + mypy clean. **NEXT = Phase 3, the only remaining phase:** the
> escalation-correctness scoring lane (Step 5 — scores "escalated
> correctly" vs "should have acted" vs "should have stayed silent" on its
> own watch-tier lane), **B-6 ring-fenced: the scoring methodology must be
> Cray-ratified BEFORE any scored benchmark run**. *Methodology RATIFIED
> (Cray, 2026-06-12, in-session):* **M-1** watch items run the LLM judgment,
> graded on a NEW watch-tier lane (pass = handler ∈ {canonical, acceptable};
> forbidden named explicitly per SD-4=a; never folded into β); **M-2 = (b)
> CALIBRATION-FIRST** — watch ground truth is NOT authored yet (no REPORT
> evidence); the first run reports the suggested-handler distribution only
> (no pass/fail pinned), ground truth pinned from that evidence (mirrors the
> B-β calibration precedent); **M-3** deterministic mis-routing is
> structurally impossible in the harness — reported as structural, no fake
> failure surface; **M-4** watch-judgment latency = its own diagnostic, the
> SD-2 ≤30s bar stays breach-scoped — **no bar moves**. A scored run still
> needs a separate Cray go (MS-S1 host-state). Spec + ratification record in
> the session-55→56 kickoff handoff
> (`.claude/handoffs/session-55/2026-06-12-0039-...-phase3-kickoff.md`).
> After Phase 3, PLAN-0022 archives to done/. Held items carry unchanged
> (nemotron MXFP4
> warm-cycle hold; bridge-resilience option B parked). *Rotation note:* per
> Cray (2026-06-11) the five session-51 CF blocks rotate at the NEXT
> reconcile; this pass added no new block (Phase 2 extends this block), so
> they are kept one more pass.
>
> *Earlier this session — Phase 1 SHIPPED (#265, `a68a114`, `feat(engine):`;
> merge `6b1bdd5`): the benchmark grader's α probe TIERED + the `Step`
> band/tiers config surface (Phase 0 = ADR-0019, #263, prior session).*
> **Step 1 (grader tiering, SD-4=a):**
> `Expected.valid_handlers` → `canonical_handler` + `acceptable_handlers`;
> dispositions are now `canonical / acceptable / forbidden-or-other`; all
> datasets migrated. Acceptable sets are grounded in PLAN-0020 REPORT
> evidence — supply_chain `[inspect]`, aquaculture
> `[increase_water_exchange]`, energy none (no recorded benign divergence).
> **Step 3 (config surface, SD-5=a):** the `Step` spec gains optional
> `threshold` / `direction` / `watch_margin` + `tiers`, and the NEW
> engine-owned `classify_verdict` (`services/engine/procedures/verdict.py`)
> is the single shared watch-band definition — `grader.classify_disposition`
> now DELEGATES to it (watch-band math defined once, per the ratified
> § Execution Order); aquaculture `procedures.yaml` carries the worked
> example. Full suite **1445 passed**; **AC-9 byte-for-byte back-compat
> held**. (The Phase-2 items formerly listed as NEXT here shipped later
> this session — superseded by the lead of this block.)
> AI-assisted (Claude Code, session 55); no `Co-Authored-By` per CLAUDE.md §7.
>
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
| 2026-06-12 | **Watch-lane ground truth PINNED — all 39 watch items (#286, `1bd6328`, session 57)** — Cray adjudicated the M-2=b pinning from the #273 calibration distribution: aqua canonical `start_emergency_aerator` + acceptable `[dispatch_technician, increase_water_exchange, escalate]`; energy canonical `restart` + acceptable `[dispatch_technician, escalate]` (`isolate` excluded → 'other'); supply_chain canonical `inspect` + acceptable `[hold, escalate]` + `forbidden_keywords [expedite, reroute]` declared (3/13 observed reroutes → forbidden). Dataset-only; the watch lane auto-flips unscored→scored; first SCORED run gated on a separate Cray go | `1bd6328` (#286) / `benchmarks/procedure_baseline/dataset/` |
| 2026-06-12 | **Lessons #24 + #25 RECORDED (#284, `4b0e306`, session 56)** — Cray-approved coda to the classifier calibration arc. **#24:** rules must live where the enforcer looks — a binding rule placed only in prose is invisible to a machine enforcer reading a different surface (C5 registry-gap finding generalized; adds an enforcement dimension to the ADR-0017 D5 placement rule). **#25:** an LLM judge's `{verdict, reason}` needs verdict-by-observable definitions + an explicit cross-field agreement contract, pinned by a prompt contract test + gold case (generalizes to the ADR-0018 goal-evaluator) | `4b0e306` (#284) / `docs/lessons/0024-rules-must-live-where-the-enforcer-looks.md` + `docs/lessons/0025-llm-judge-verdict-must-bind-to-its-own-reasoning.md` |
| 2026-06-12 | **Stop classifier SWITCHED to local `gpt-oss:20b` (#282, `3375778`, session 56)** — Cray picked **(b)** on the calibration evidence (8–30s latency acceptable). Default backend = MS-S1 Ollama (format-constrained `/api/chat`, temp 0, keep_alive 10m, 75s timeout; no API key / no WSL bridge); Anthropic API retained as rollback via `CLAUDE_CLASSIFIER_BACKEND=sonnet`. Fail-closed pause + legacy reason strings byte-identical; legacy suite pinned to sonnet + 4 new ollama-backend tests (571 passed / 2 skipped; mypy --strict clean); LIVE-verified from the prod hook runtime: 7.9s → pause | `3375778` (#282) / `.claude/hooks/_sonnet_classifier.py` |
| 2026-06-12 | **Stop-classifier calibration arc SHIPPED (#278 + #279 + #280, `246ee0a`, session 56)** — #278 completion-consistency rule (PROCEED needs concrete remaining work; decision↔reason agreement; contract-test-pinned). #279 20-case safety-weighted eval harness (full prod-prompt fidelity; gold incl. Thai); MS-S1 sweep 4×20 (80 dump-verified): `gpt-oss:20b` 19/20, recall 100%, p95 21.6s vs sonnet(prod) 17+2/20, recall 75%, p95 3.5s; nemotron-4b safety-DQ. #280 HEADLINE = registry gap not model gap → registry row C5 (host-state gate), re-verified live; transport pick (local vs API Sonnet) = Cray's | `246ee0a` (#278–#280) / `benchmarks/stop_classifier/RESULTS.md` |
| 2026-06-12 | **Carrier-death incident → ops hardening SHIPPED (#275 + #276, `3a8a175`, session 56)** — the calibration run's carrier (held `wsl.exe` + wrapper) was reaped at ~59 min; the orphaned python completed silently (stale "running" task chip, no completion event; truth established content-based). #275 records the gotcha + content-based truth test in the `ms-s1-ollama` skill; #276 adds `run_detached.sh` — long MS-S1 runs launch under `systemd-run --user` (carrier-proof, PROBE-VERIFIED 2026-06-12; `.done` sentinel "rc ISO-ts"; ETA + ~10 min → check sentinel; `Linger=no` = host-state, ask Cray) | `3a8a175` (#275 + #276) / `.claude/skills/ms-s1-ollama/` |
| 2026-06-12 | **First watch-lane calibration run RECORDED (#273, `489b695`, session 56)** — M-2=b evidence on MS-S1 (`gpt-oss:20b`, 198 items, 319 calls, 0 errors, `--dump-json`-verified). Watch distribution: aqua 13/13 aerator, energy 13/13 restart, supply_chain hold 5 / inspect 5 / **reroute 3 = the lane's first real safety signal** (forbidden under a `{hold, inspect}` pinning). β 98.3% (2 verified misses incl. the U+2011 hyphen grader-calibration candidate), α 100%, deterministic 198/198. Breach p95 28.73s = first SD-2 PASS in full mode (±10s noise band); watch latency = M-4 own diagnostic. No bar moves (B-6) | `489b695` (#273) / `benchmarks/procedure_baseline/REPORT.md` |
| 2026-06-12 | **PLAN-0022 COMPLETE — Phase 3 watch-tier escalation lane SHIPPED (#270, `1723981`, session 56) + plan archived to done/ (#271, `b41a138`)** — implements the Cray-ratified M-1..M-4 methodology (M-2=b calibration-first: watch items run the LLM judgment, unscored distribution reporting until ground truth is pinned from run evidence; M-4 watch latency = own diagnostic, SD-2 bar stays breach-scoped; REPORT methodology recorded BEFORE any scored run). All four phases done (#263/#265/#267/#270). Suite 1469; first calibration run gated on a separate Cray go | `b41a138` (#270 + #271) / `docs/plans/done/0022-tiered-decision-routing.md` + `benchmarks/procedure_baseline/REPORT.md` |
| 2026-06-11 | **ADR-0019 (`watch → gated`-proposal routing) ACCEPTED + merged (#263, `137766c`, session 54)** — PLAN-0022 **Phase 0** governance gate (CLAUDE.md §8; merges before the impl PR). Cray chose **OQ-1 form (b)** = a follow-on ADR over an in-place ADR-016 amendment. Sanctions routing the deterministic `watch` set → a `gated` `action` proposal (LLM proposes → human decides via `resolve_gated_step`); **extends ADR-016 D3** — no primitive / auto-gated / ceiling / allowlist change; trigger = engine verdict, never `confidence` (ADR-010 IN-3). **Authored by Cowork** — the G1/G2 PreToolUse gates correctly blocked Code's *direct* ADR Write/Edit (ADR-009 D1: Cowork authors, Code commits); Code R2-verified verbatim + committed. Includes an ADR-016 forward pointer + the Morning-Pond Step 4 row (`human_task` → gated proposal, SD-1=a). *(A transient classifier-bridge timeout first fail-closed the gate; diagnosed + healthy.)* | `137766c` (#263) / `docs/adr/0019-watch-gated-proposal-routing.md` + `docs/adr/0016-*` |
| 2026-06-11 | **PLAN-0022 (tiered decision routing) RATIFIED Draft → Ready for execution (#261, `46061b7`, session 54)** — Cowork-drafted (ADR-009 D1, #259); Code R2-reviewed, re-verifying the two load-bearing fact-pack catches vs HEAD (**FP-2/SD-6:** no deterministic `evaluate` executor in `services/engine/procedures/` — only `ActionStepExecutor`; a real prerequisite for `watch→gated`; **FP-1/SD-7:** aquaculture `procedures.yaml` routes `watch→human_task`, an *upgrade* target not silence). Cray accepted **SD-1..SD-7 per recommendation** (SD-1=a gated replaces human_task; SD-2=a deterministic watch band only, no ADR-010 reopen; SD-4=a reuse `forbidden_keywords`; SD-5=a fields on the `Step`; SD-6=a evaluate executor in the impl PR) + **S-1 keep ammonia**. Added **§ Execution Order**: Phase 0 ADR-016 D3 amendment first (CLAUDE.md §8) → Phase 1 grader taxonomy ∥ config (define once) → Phase 2 `evaluate` executor → `watch→gated` → Phase 3 escalation scoring. Trigger = engine watch band, never `confidence` (ADR-010 IN-3). Impl = later separate PR. Also received (gitignored research): 3 Build-Vertical narratives + the gpt-oss rubric R1–R6 | `46061b7` (#261) / `docs/plans/0022-tiered-decision-routing.md` |
| 2026-06-11 | **PLAN-0020 (Procedure-path tuning) COMPLETE + archived to done/ (#251–#256, `a6125c1`, session 53)** — the PLAN-0019 B-6 ring-fence follow-up. All `--dump-json`-VERIFIED on `gpt-oss:20b`/MS-S1: the Phase-1 aqua prompt nudge (PR #232, prev. UNMEASURED) worked dramatically — overall β `85.8%→100%`, aqua β `60%→100%`, overall α `70%→100%` (supply α `32.5%→100%`: model now picks `hold` not `inspect`). Latency lever: new `reasoning_mode=skip` (drop call-1 reasoning) cuts p95 `31.80s→21.62s` UNDER the 30s bar at **zero β cost** (`think_off` = dead lever). **SD-1** (widen supply-α) authorized at ratify but **SKIPPED at Step 9** — nudge made the divergence moot (0 `inspect`); anti-moving-target honored, no grader change. Also: per-judgment latency timer (#252), think-trim lever (#253), `ms-s1-ollama` skill (#254, `warm.sh` live-tested), tuning report (#255). Next: future PLAN for tiered handler grading (canonical/acceptable/forbidden — α too coarse); wiring `skip` into product path is an open audit trade-off | `a6125c1` (#251–#256) / `docs/plans/done/0020-procedure-tuning-latency-precision.md` + `benchmarks/procedure_baseline/REPORT.md` |## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten (full table: PLAN-0005 §8.1): rule-based recommender → **ADR-010 ACCEPTED (2026-05-22) → PLAN-0006 next** (LLM reasoning hook); minimal approval gate → **ADR-011+** (audit framework — trigger: first design-partner data / PDPA review); no mapping layer → **dbt/SQLMesh** (trigger: first non-synthetic source); hand-authored ORM → **"ORM emitter"** Rule-of-Three candidate (trigger: 3rd vertical / DDL↔ORM parity-test drift); base Postgres only → **PLAN-002** (pgvector/AGE — trigger: semantic + graph features); explicit registry → **ADR-006 D3 L2** (trigger: vertical #2/#3 or `new-vertical` generator). *(per Cray note 2026-05-21)*
- [ ] **Phase-enum amendment** — add `consultation` (or equivalent Q&A-round value) to canonical Phase enum (Q15 of `2026-05-20-0245-code-plan003-pre-draft-consultation-reply.md`); requires touching `tools/handoffs/_schema.py` + `docs/conventions/handoff-frontmatter-schema.md` + validator tests; PLAN-004 Phase B adjacent. *(Deferred per R-9, 2026-05-20)*
- [ ] **Cleanup stale `ontology/README.md`** — 2026-05-05 PLAN-001 artifact; ontology directory canon now lives at `verticals/<name>/ontology/<name>_v0.yaml` per ADR-006 D1 / ADR-008 D5; superseded by PLAN-003. *(Deferred per R-9 cohort, 2026-05-20)*
- [ ] **PLAN-004 Phase B/C — DEFERRED (backlog, post-PLAN-003):** validator-scope exclusion (`README.md` / `_rename-map.md`, manifest §4.2/§6.1) + Cat G `references_*` autofix + Phase C handoff dashboard + OQ-2 systemic candidate (effective-vs-authored `status:` / archival flag so dead handoffs don't surface as actionable in the dashboard) + **validator warning-swallow bug** — `tools/handoffs/_schema.py` `_build()` (lines ~302–306) returns `Frontmatter` and discards its local `errors` list when no hard error exists, so `_check_unknown()` WARNING-severity findings (e.g. unknown field `brief-number`) are unreachable on otherwise-valid files; fix to surface warnings + add a regression test *(found 2026-05-22 dog-fooding the 4 Cowork LLM-hook handoffs; Cray routed → Phase B)*
- [ ] **ADR-NN (TBD, ≥ ADR-014) + PLAN-002** — Custom Postgres image with extensions (ADR-011 earmarked for the audit framework, ADR-012 taken, ADR-013 taken by autonomy axis relocation; floor bumped from ≥0013 to ≥0014 on 2026-05-23 per ADR-013 T6)
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (low priority)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)

## Next Steps

1. **PLAN-0005 §8.1 revisit register** — remaining deferred-foundational simplifications at their batch boundaries (audit framework → ADR-011+, mapping layer, ORM emitter, base-Postgres → PLAN-002 (≥ADR-014), registry discovery).
2. **Partner-trial readiness gaps** — `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` awaits a dedicated Cray discussion.
3. **Deferred (backlog)** — PLAN-004 Phase B (validator-scope exclusion; Cat G `references_*` autofix; validator warning-swallow bug) + Phase C (handoff dashboard); PLAN-002 custom Postgres image (≥ADR-014).
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
