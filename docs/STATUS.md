---
last_updated: 2026-06-14T09:28:25+07:00
session: 58
current_batch: 'session-58 backlog quick-wins (Code-solo) — stop-classifier gold cases #2/#3 (#311) + handoff-validator warning-swallow fix (#312)'
current_actor: code
blocked_on: 'Nothing blocks Code (quick-wins shipped). Open-for-Cray: strategic sequencing fork (partner-trial roadmap vs B-γ baselines); auditprep SD-4/SD-5/OQ-A + ADR-011 (gated on a real partner) are in the CF coda / In-Flight.'
next_action: 'Teed up for Cray: sequence the partner-trial roadmap fork (NL-query vs real-data) vs the B-γ benchmark baselines — which order yields higher quality. Held: PLAN-002, partner-trial gaps, auditprep SD-4/SD-5/OQ-A, ADR-011 (real-partner gated).'
head_commit: 9595d3e
recent_commits: [6f46277, 9595d3e, 48a2da0, f2ee579, c818695, afea6b3, 8f9a36d, d4fe7fc, effad05, b37bb1b]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 58 (second batch, current; head_commit `9595d3e`) — TWO BACKLOG
> QUICK-WINS (Code-solo, #311 + #312), cleared after the audit-framework arc
> closed.** A genuinely separate small batch (harness tooling, not the partner
> arc): two long-standing backlog items shipped back-to-back. **(1)
> stop-classifier gold cases #311 (`f2ee579`, `test(stop-classifier):`):**
> added 3 "dispatch discriminator" cases to `benchmarks/stop_classifier/gold.yaml`
> (20→23) pinning the surfaced-vs-ratified distinction the local classifier got
> WRONG in session 57 (it OVER-FIRED `plan-drafter` dispatches on ADR/PLAN
> *mentions* while the formality choice was a PENDING Cray decision — 2 instances)
> and RIGHT in session 58 (once Cray RATIFIED PLAN formality, the dispatch was
> correct). Two `pause` negatives + one `dispatch` positive; safety-weighted
> scoring makes a spurious dispatch a HARD FAIL. Offline test
> (`tests/benchmark/test_stop_classifier_gold.py`) green (4 passed); the live
> re-score (warm MS-S1) is a host-state eval — **pending Cray's go**; RESULTS.md
> got an addendum noting the recorded 2026-06-12 run predates the 3 cases (no
> model numbers fabricated). **(2) handoff-validator warning-swallow bug FIXED
> #312 (`9595d3e`, `fix(handoffs):`; PLAN-004 Phase B backlog):**
> `tools/handoffs/_schema.py::_build()` returned the typed `Frontmatter` on the
> otherwise-valid path and discarded its local `errors` list, so
> `_check_unknown()` WARNING findings (e.g. unknown field `brief-number`) were
> unreachable on any file without a hard error — contradicting `validate_file`'s
> own docstring. Fix: `Frontmatter` gains a `warnings` field; `_build()` fills
> it on the success path; `validate_file()` surfaces it; the `validate_handoff.py`
> CLI now prints the warning; precommit unchanged (still gates/prints only
> `is_error()`). Regression tests strengthened (the OLD test passed on the bug)
> + text-API + clean-file guards; `tests/handoffs/` 573 passed / 2 skipped;
> ruff + mypy clean. **Next:** quick-wins #2/#3 done → a strategic discussion is
> teed up for Cray — sequence the partner-trial roadmap fork (NL-query-first vs
> real-data-first) vs the B-γ benchmark baselines (do the fork first and feed
> B-γ, or B-γ first to inform the fork). Other backlog held: B-γ, PLAN-002
> (≥ADR-021), partner-trial gaps + audit-framework SD-4/SD-5/OQ-A + ADR-011
> (gated on a real partner).
> *Rotation note:* a new Session-58 (second batch) CF block was added (separate
> subject — harness tooling, not the partner arc), taking the count to 9 > the
> 8-block soft cap; per R2 the oldest CF block (session 56 fourth batch,
> stop-classifier calibration arc, #278/#279/#280) rotated to
> `docs/status-archive/2026-h1-status.md` this reconcile (R2/R4), keeping the
> count at 8.
> AI-assisted (Claude Code, session 58); no `Co-Authored-By` per CLAUDE.md §7.
>
> **Session 57 (fifth batch, current; head_commit `e09af9b`) — AUDIT-FRAMEWORK PREP arc:
> partner-sim venue ADR-0020 committed Proposed (#297, `e25281d`,
> `docs(adr):`) + its project system instruction LANDED (#298,
> `e387a63`, `docs(conventions):`; merge `e10f589`), then a
> pre-ratification R1 errata + instruction align (#300,
> `655344d`, `docs(adr):`; merge `b466802`), then RATIFIED
> Proposed→Accepted (#302, head_commit `4d1347b`, `docs(adr):`;
> merge `d8c7c11`) — the venue is now ACCEPTED and live-able.**
> Two sub-batches both done this session.
> **(1) auditprep:** Cowork drafted two seed instruments (first-dataset
> requirements one-pager + PDPA review checklist); Code receive-verified
> (validator clean, re-stamped); both gitignored under
> `docs/research/private/`, NOT committed. Open for Cray: SD-4
> residency-guarantee scope, SD-5 erasure vs append-only, OQ-A Thai
> PDPA lawyer review. **(2) partnersim (this reconcile):** Cray-approved
> synthetic-design-partner idea → Cowork drafted ADR-0020 + the project
> instruction; Code R2-reviewed + committed both. **ADR-0020 (#297,
> `e25281d`, Proposed):** a specialist Cowork project that role-plays a
> Thai operator and emits a "partner profile package" so the
> intake+PDPA pipeline is rehearsed weeks before a real partner. D1 =
> venue OUTSIDE the governance tiers (research/fixture data only; no
> commits; no repo mount; enters via Code receive). D2 = three BINDING
> anti-circularity rules: R1 feed-questions-not-schema (no repo mount =
> structural insulation; same M-2=b/PLAN-0022 trap-class), R2 forced
> messiness, R3 SYNTHETIC provenance (output never trips PLAN-0005 §8.1
> / ADR-011 first-real-data trigger; lives at ADR level per Lesson #24).
> D3 reuses the existing completion-handoff schema (NO enum change). D4
> = guarded-trial (mirrors ADR-012 D5) + R-PS1..R-PS4 regression
> triggers; run 1 = energy operator (ADR-005 primary). SD-1..SD-4 =
> recommendations only (N=3; project-per-type; size/region/maturity
> enums w/ energy·mid·th-regional·mixed-legacy default; include "what
> we refused to share"). Author≠reviewer (ADR-012 D4.3): self-deliberated
> in the Cowork consultation round, Code review = remaining independent
> check. **Project instruction (#298, `e387a63`):** landed at
> `docs/conventions/partnersim_project_instructions.md` (ADR-0020 T2;
> Cowork staged it under `research/private` because `conventions` is
> outside Cowork write scope — Code relocated + committed per ADR-009
> D2). Self-contained paste-ready instruction (no repo mount); sync
> target = the Claude "partner-sim" project field; self-documents
> Proposed status; SD defaults finalize at ratification. **Governance
> threads:** ADR-0020 awaits Cray ratification Proposed→Accepted +
> SD-1..SD-4 adjudication before the project goes live (ADR-0020 T3:
> flip Accepted + fold SDs + STATUS record). ADR-011 (audit framework)
> STILL gated on a partner conversation — partner-sim's R3 means the
> synthetic run INFORMS but never TRIGGERS it. **Two spurious
> AUTO-HANDOFF DISPATCHES this session** (PLAN-0009 Step 5c, same class):
> the classifier read ADR mentions ("ADR-011", then "ADR-0020") in
> consultation/summary replies as live drafting needs and ordered
> plan-drafter spawns — both overridden per the override clause (the
> ADR-0020 one fired AFTER that exact draft was already Cray-routed to
> Cowork); strong stop-classifier gold-case candidates (quick-win
> backlog). **K-2 anomaly (carried, unresolved):** this Cowork session
> could Write `.claude/handoffs/` directly (block did not fire) while
> the outputs scratchpad was unreachable — inverted vs Lesson #8; needs
> a stability check across sessions before any workflow-doc change.
> **(coda — pre-ratification R1 errata, #300, `655344d`):** Cray asked
> "anything to worry about before ratifying ADR-0020?" and Code's R2
> verification pass found a VERIFIED R1 self-contradiction — the
> partner-facing first-dataset one-pager (which the run procedure
> pasted EVERY run) carried our 3-band verdict taxonomy
> (breach/watch/ok) AND action vocabulary, including the M-2=b
> reroute/expedite watch design built this session, so R1
> ("never feed our schema") was defeated AT THE PASTE STEP and
> Consequences/Positive actually relied on the leak. Fix (#300,
> dispatched to Cowork, Code R2-reviewed + committed; ADR-0020 stays
> PROPOSED): (a) ADR-0020 errata — R1 now requires a dedicated
> R1-clean seed (`docs/research/private/2026-06-13-partnersim-seed-r1clean.md`,
> gitignored) as the ONLY first-dataset doc cleared for the paste;
> D3/References repoint; Consequences reworded (Code maps to verdict
> bands on receive, not pre-baked); R-PS1 records the named breach
> vector; dated amendment note. (b) The committed instruction file
> (#298) still told Cray to paste "the one-pager" in 3 places — Code
> aligned §2/§3/§4.2 to the R1-clean seed (Code-amends-conventions,
> ADR-009 D2), else the leak persists in practice. Receive: completion
> handoff validator-clean + re-stamped (1055→1123, K-1); the D1 seed
> AC-1 grep-clean (zero forbidden tokens EN+TH) + content R2 (six asks
> intact, redaction faithful, engine-internal "Why" abstraction
> stands); D1 gitignored, NOT committed. *Don't-trust-piped-exit-codes
> catch:* the AC-1 grep first returned a contradictory signal (EXIT=0
> "hits found" yet zero lines from the WSL wrapper) — Code did NOT sign
> off on the ambiguous result, re-ran cleanly → "NO MATCHES" confirmed
> the seed is clean. Open for Cray (added by this errata): dispatch-SD-1
> (trim the real one-pager's internal note); ratification now folds
> SD-1..SD-4 + dispatch-SD-1, and run-1 uses the R1-clean seed, NOT the
> one-pager.
> **(coda — RATIFIED Accepted, #302, `4d1347b`):** Cray ratified
> in-session ("เอาตาม Cowork ทุกข้อ") — ADR-0020 flipped
> Proposed→Accepted (Cowork-authored fold per ADR-009 D1, Code
> R2-reviewed + committed). All four venue SDs + dispatch-SD-1
> accepted per Cowork rec: SD-1 N=3 (→D2/R2); SD-2
> one-project-per-business-type (→D4; R-PS4 reframed as a guard);
> SD-3 size/region/maturity enums + run-1 default
> energy·mid·th-regional·mixed-legacy (→D3 input); SD-4 "what we
> refused to share" ratified-required (→D3 output). R1/R2/R3
> substance unchanged (the #300 errata already settled those). Code
> also reconciled the instruction file (6 ratification-pending
> markers Proposed/finalized-at-ratification → ratified;
> Code-amends-conventions, ADR-009 D2, same PR #302). dispatch-SD-1
> (gitignored, not committed): the real one-pager's sector-callout
> forbidden-action note (reroute/expedite-ต้องห้าม + benchmark
> structure) trimmed; near-limit-rationale ask retained; R1-clean
> seed untouched (R2-verified). Receive: completion handoff
> (`2026-06-13-1215-cowork-adr0020-ratify-completion.md`)
> validator-clean + re-stamped (K-1); **K-2 did NOT fire (3rd data
> point — Cowork could write `.claude/` directly again).** Venue
> status now ACCEPTED guarded-trial under observation (R-PS1..R-PS4
> exit criteria); the live action is now Cray's (create the Claude
> partner-sim project, paste the R1-clean seed + PDPA checklist +
> business-type brief, launch energy run-1).
> **(coda — partner-sim RUN-1 RECEIVED + operation runbook, #304,
> head_commit `6e8c603`):** partner-sim run-1 (energy/NPD) was
> received — **R2 PASS** (rich R1 mismatch / R2 messiness / SD-4 +
> 5 SD-1 facts), completion handoff re-stamped, landed gitignored
> at `docs/research/private/`; D4 regression triggers R-PS1..R-PS4
> all CLEAR (no real-data trigger; output is SYNTHETIC per R3). The
> operating method was then captured as a tracked runbook
> `docs/runbooks/partner-sim-operation.md` (#304, `docs(runbook):`;
> the sim's outputs stay synthetic + gitignored). Next: step-1
> mapping-layer rehearsal against the run-1 package (derive the real
> intake form), then step-2 PDPA RoPA-lite.
> **(coda — partner-sim STEP-1 mapping rehearsal SHIPPED, #306,
> head_commit `e09af9b`):** step-1 (lightweight, energy-first, both
> deliverables tracked per Cray's scoping) landed — a mapping rehearsal
> of the run-1 package against the canonical energy model produced two
> tracked artifacts: the real-partner intake form v2
> (`docs/conventions/partner-intake-form.md`) + the mapping-gap analysis
> (`docs/strategy/public/partner-sim-run1-mapping-analysis.md`).
> 5 headline gaps drove intake form v2: per-parameter reading spec (the
> core fix — our single-parameter-procedure vs NPD's multi-parameter
> operation), action-meaning, status-vocab→numeric-rule,
> asset-taxonomy enumeration, identity/lineage (the last feeding
> ADR-011). SYNTHETIC provenance unchanged — the run-1 package INFORMS
> these but does NOT trigger ADR-011 / PLAN-0005 §8.1 first-real-data.
> The C4 hook routed the analysis to `docs/strategy/public/` because
> `docs/research/` writes are private-only. Next: step-2 (PDPA RoPA-lite)
> — Cray will discuss the approach after reviewing step-1 results.
> **(coda — PLAN-0023 PDPA RoPA-lite STEP-2 SHIPPED, session 58, #308/#309,
> head_commit `afea6b3`):** step-2 of the audit-framework-prep arc landed —
> two tracked deliverables: a reusable RoPA-lite **template**
> (`docs/conventions/partner-ropa-lite.md`, canonical) + an **NPD synthetic
> example** (`docs/strategy/public/partner-sim-run1-ropa-example.md`,
> SYNTHETIC). Each RoPA slot is annotated with a data-quality/lineage hook;
> the example carries a DSR/lineage→ADR-011 design-driver section mapping
> 4 gaps→implications (PII-in-free-text → log-by-reference; scattered actor
> identity → actor unification; PK reuse + NTP drift → lineage/valid-from +
> ordering; under-recording → completeness-not-assumed). **Governance chain
> (clean author≠reviewer):** Cray ratified PLAN formality (3 decisions —
> template+example scope / PLAN / DSR-lineage-as-ADR-011-driver angle); Code
> wrote a self-contained drafting brief → the in-harness `plan-drafter`
> subagent authored PLAN-0023 (ADR-013 D1) → Code committed it (#308,
> ADR-009 D2) → Cray reviewed at merge → Code executed the two deliverables
> directly (Code-direct, same as step-1) (#309); PLAN archived to `done/`.
> SD-1 surfaced + kept: AC-6 (post-merge STATUS reconcile) retained as an
> in-PLAN acceptance criterion (drafter rec; Cray did not flip). **Stop-hook
> AUTO-HANDOFF DISPATCH fired for the PLAN-0023 drafting and was LEGIT this
> time** (contrast the 4 spurious dispatches in session 57): it fired only
> AFTER Cray ratified PLAN formality via the decision prompt, so the drafting
> need was real — a positive gold-case counterpoint to session 57's
> premature-dispatch-on-a-surfaced-decision cases. Carried open (unchanged):
> SD-4 residency scope, SD-5 erasure vs append-only, OQ-A Thai PDPA lawyer
> review; **ADR-011 still gated on a real partner** — the synthetic run
> INFORMS/feeds it (ADR-0020 R3) but never triggers PLAN-0005 §8.1. Next:
> audit-framework-prep arc now idle pending a real partner conversation (the
> ADR-011 gate); backlog quick-wins available (stop-classifier gold cases,
> incl. this session's legit-vs-spurious dispatch contrast).
> *Rotation note:* the oldest CF block (session 56 third batch,
> carrier-death hardening, #275/#276) rotated to
> `docs/status-archive/2026-h1-status.md` this reconcile (R2/R4).
> No CF block rotated this reconcile — step-2 added as a coda on this
> (fifth-batch AUDIT-FRAMEWORK PREP) arc, keeping the count flat at 8.
> AI-assisted (Claude Code, session 58); no `Co-Authored-By` per CLAUDE.md §7.
>
> **Session 57 (fourth batch) — B-6 hyphen normalization
> SHIPPED (#295; head_commit `2331ffb`, `fix(benchmark):`; merge
> `7374f52`) + post-#282 test-hermeticity gap FIXED en route (#294;
> `5330dfb`, `fix(tests):`) — the session's last open adjudication
> is CLOSED.** Cray ratified B-6 in-session ("เริ่มทำ B-6 ต่อได้เลย").
> `grader.py` gains `normalize_primary_key()`: the Unicode
> hyphen/dash family (U+2010–U+2014, U+2212) folds to ASCII `-` on
> BOTH sides of the two primary-KEY comparisons
> (`affected_primary_key` + `forbidden_primary_keys`); free-text
> matching deliberately untouched (no evidence of need). 3 new tests:
> the energy-007 gold case, a real-mismatch guard, and a U+2011-decoy
> precision guard. REPORT.md Calibration log gains a dated addendum
> (same measurement-correctness class as the 2026-06-08 items; no bar
> moves; published tables stay as-run per anti-moving-target).
> VERIFIED by offline dump replay against the stored 2026-06-12
> scored-run records: β re-grades 118/120 → 119/120 with EXACTLY one
> flip (energy-007 False→True, zero collateral); aqua-028 (real model
> miss) still fails. *En-route discovery (#294):* the B-6 full-suite
> regression check hit 17 timeouts in
> `tests/handoffs/test_stop_continuation.py` — post-#282 the
> subprocess fixtures' defang-by-no-key only neuters the SONNET path;
> the new local-Ollama default needs no key, so the
> `stub_env`/`subprocess_env` tests were silently making REAL MS-S1
> network calls (green only while `gpt-oss:20b` was warm; cold
> tonight → 17 cold-load timeouts). `test_phase2_integration.py`
> already carried the pin from #282 — the other two fixture copies
> were missed. Fix: pin `CLAUDE_CLASSIFIER_BACKEND=sonnet` in both;
> proof: the 3 files 90 passed in 11s with the model COLD; full-suite
> runs no longer fire ~17 live generations at MS-S1 (serialize-rule
> hygiene). Full suite on merged main: 1481 passed / 22 skipped in
> 33.58s (was ~5 min while the suite was live-calling; 1478 baseline
> + 3 new grader tests = 1481, accounts clean). *Rotation note:* the
> oldest CF block (session 56 second batch, first watch-lane
> calibration run, #273) + the oldest RD row (PLAN-0022 ratification,
> #261) rotated to `docs/status-archive/2026-h1-status.md` this
> reconcile (R2/R4).
> **NEXT:** session 57 has no remaining open adjudications; next
> session picks up from STATUS/handoff (held: nemotron MXFP4
> warm-cycle, bridge-resilience option B, ADR-0018 OQ-8 backlog).
> AI-assisted (Claude Code, session 57); no `Co-Authored-By` per CLAUDE.md §7.
>
> **Session 57 (third batch) — unit-side completion PING +
> no-Monitor rule SHIPPED (#290; `feat(skills):` `3c25d94`; merge
> `6a47d89`) + deferred header line LANDED (#292; head_commit
> `f1cf3b4`, `chore(skills):`; merge `f2184f6`).** Coda to the scored run's watcher
> death: Cray asked why the WSL issue recurred after the systemd
> switch — answer: systemd protected the *workload*, but the
> notify-back channel (harness Monitor = `wsl.exe` carrier) stayed
> WSL-bound; it false-alarmed once and died silently during the scored
> run. Fix: `_run_detached_body.sh` now sends a best-effort unit-side
> Telegram ping (`tools/notify/telegram.sh`; a subshell sources the
> gitignored `.env` since the systemd user env lacks `TELEGRAM_*`)
> immediately AFTER writing the `.done` sentinel — the sentinel stays
> the authoritative signal; outcome recorded as `[wrap] PING
> ok|failed|skipped`; a ping failure can never touch the sentinel or
> rc. SKILL.md codifies the rule: never arm a harness Monitor/watcher
> on the sentinel — completion truth = sentinel + the ETA rule.
> Verified: `bash -n` clean; the ping block (verbatim copy) smoked
> inside a real `systemd --user` unit → `[wrap] PING ok` (HTTP 200,
> delivered to the project Telegram). Classifier first-flight log (now
> 3 events): the auto-mode classifier allowed the body + SKILL.md
> edits but DENIED a cosmetic one-line header-comment edit in
> `run_detached.sh` (self-modification gate — "diagnostic question ≠
> authorization"); deferred pending explicit per-diff Cray approval
> (cosmetic only: the `.wrap` artifact description didn't yet mention
> the PING markers). *Coda (#292):* that deferred header line landed
> via `f1cf3b4` (`chore(skills):`; merge `f2184f6`) after Cray's
> explicit per-diff approval — the retry passed (the documented
> per-diff override path); the classifier-denied edit thread is
> CLOSED. *Rotation note:* the oldest CF block (session 56,
> PLAN-0022 Phase 3 + closeout, #270/#271) rotated to
> `docs/status-archive/2026-h1-status.md` this reconcile (R2/R4).
> **NEXT:** B-6 hyphen-normalization grader adjudication (3 data
> points) awaits explicit Cray ratification before any grader edit. No
> open PRs; no run in flight.
> AI-assisted (Claude Code, session 57); no `Co-Authored-By` per CLAUDE.md §7.
>
> **Session 57 (second batch) — first SCORED watch-lane run
> RECORDED (#288; head_commit `4c46a92`, `docs(benchmark):`; merge
> `adb1bc5`) — watch lane 97.4% (38/39); the M-2=b arc is COMPLETE.**
> Cray gave the go; the run executed in ~67 min via `run_detached.sh`
> (its first production full run): `gpt-oss:20b` on MS-S1, all 198
> items, `reasoning_mode=full`, 318 LLM calls, 0 errors; the sentinel
> `0 2026-06-12T21:25:22+07:00` was written as designed. The
> harness-side watcher Monitor died silently (lost-notification class)
> and also fired one false alarm earlier (a single-read empty
> `systemctl --user is-active` → declared dead while the unit was
> active); completion truth was recovered via the content-based test
> (sentinel + `DUMP: wrote 198` + empty pgrep). All numbers
> dump-VERIFIED (39/39 `watch_graded:true`). **Watch lane (first
> scored):** aquaculture 100% (13/13 canonical
> `start_emergency_aerator`); energy 100% (13/13 canonical `restart`);
> supply_chain 92.3% (12/13: inspect 6 canonical / hold 6 acceptable /
> reroute 1 forbidden). The single FAIL = supply-040 — "Proceed — no
> breach detected" + `reroute` at confidence 1.0 on a 7.8 °C in-spec
> reading → scored forbidden via the declared `forbidden_keywords` =
> the lane discriminating exactly as designed (1/13 this run vs 3/13
> in calibration — intermittent but real). **Companion lanes:** β
> 98.3% (118/120) — the misses are the SAME two known items: aqua-028
> hedger + energy-007 U+2011 hyphen (THIRD occurrence across runs —
> strengthens the pending B-6 hyphen-normalization adjudication); α
> 100%; deterministic 100%. **Latency:** SD-2 p95 30.18s → nominally
> OVER by 0.18s; recorded with two readings, no bar moved (B-6): (1)
> within the documented ±10s straddle band (31.80 → 28.73 → 30.18
> across full-mode runs); (2) run-unique contamination — the
> session-57 local Stop classifier shares MS-S1 and generated during
> the measured window; clean-verdict option = rerun quiesced or with
> `CLAUDE_CLASSIFIER_BACKEND=sonnet`. **Local-classifier first-flight
> tally** (for the closeout): 2 false-continue Stop verdicts this
> session (one "completion-consistency"-shaped, one blocking turn-end
> while a background monitor was armed) — annoying, never dangerous.
> **NEXT:** the B-6 hyphen-normalization grader adjudication (now 3
> data points) awaits explicit Cray ratification before any grader
> edit. No open PRs; no run in flight.
> AI-assisted (Claude Code, session 57); no `Co-Authored-By` per CLAUDE.md §7.
>
> **Session 57 — watch-lane GROUND TRUTH PINNED on all 39
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
| 2026-06-14 | **Two backlog quick-wins SHIPPED (Code-solo, #311 + #312, `9595d3e`, session 58)** — cleared after the audit-framework arc closed; a separate small harness-tooling batch. **#311** (`f2ee579`, `test(stop-classifier):`): 3 "dispatch discriminator" gold cases added to `benchmarks/stop_classifier/gold.yaml` (20→23) pinning the surfaced-vs-ratified distinction the local classifier got wrong in s57 (over-fired `plan-drafter` on ADR/PLAN mentions while formality was a PENDING Cray decision — 2 cases) and right in s58 (post-ratification dispatch correct); 2 `pause` negatives + 1 `dispatch` positive, safety-weighted (spurious dispatch = HARD FAIL); offline test green (4 passed); live re-score pending Cray go; RESULTS.md addendum (recorded 2026-06-12 run predates the cases). **#312** (`9595d3e`, `fix(handoffs):`, PLAN-004 Phase B): handoff-validator warning-swallow bug fixed — `_schema.py::_build()` discarded its `errors` list on the otherwise-valid path so `_check_unknown()` WARNINGs were unreachable; `Frontmatter` gains `warnings`, `validate_file()` surfaces it, CLI prints it (precommit unchanged); regression tests strengthened; `tests/handoffs/` 573 passed / 2 skipped; ruff + mypy clean | `9595d3e` (#311/#312) / `benchmarks/stop_classifier/gold.yaml` + `tools/handoffs/_schema.py` |
| 2026-06-14 | **PLAN-0023 (PDPA RoPA-lite, step-2 of audit-framework-prep) SHIPPED (#308 PLAN + #309 deliverables, `afea6b3`, session 58)** — two tracked deliverables: reusable RoPA-lite template (`docs/conventions/partner-ropa-lite.md`, canonical) + NPD synthetic example (`docs/strategy/public/partner-sim-run1-ropa-example.md`, SYNTHETIC), each RoPA slot annotated with a data-quality/lineage hook; example's DSR/lineage→ADR-011 section maps 4 gaps→implications (PII-in-free-text→log-by-reference; scattered actor identity→actor unification; PK reuse + NTP drift→lineage/valid-from + ordering; under-recording→completeness-not-assumed). Governance: Cray ratified PLAN formality (3 decisions) → `plan-drafter` subagent authored PLAN-0023 (ADR-013 D1) → Code committed (#308, ADR-009 D2) → Code executed deliverables Code-direct (#309); PLAN archived to `done/`. SD-1 kept (AC-6 in-PLAN). ADR-011 still gated on a real partner — synthetic run INFORMS but never triggers PLAN-0005 §8.1 (ADR-0020 R3). Carried open: SD-4/SD-5/OQ-A | `afea6b3` (#308/#309) / `docs/conventions/partner-ropa-lite.md` + `docs/strategy/public/partner-sim-run1-ropa-example.md` |
| 2026-06-13 | **ADR-0020 (partner-sim venue) RATIFIED Proposed→Accepted (#302, `4d1347b`, session 57)** — Cray ratified in-session ("เอาตาม Cowork ทุกข้อ"); all four venue SDs + dispatch-SD-1 accepted per Cowork rec (Cowork-authored fold per ADR-009 D1, Code R2-reviewed + committed). SD-1 N=3 (→D2/R2); SD-2 one-project-per-business-type (→D4; R-PS4 reframed as a guard); SD-3 size/region/maturity enums + run-1 default energy·mid·th-regional·mixed-legacy (→D3 input); SD-4 "what we refused to share" ratified-required (→D3 output). R1/R2/R3 substance unchanged (#300 errata settled those). Instruction file reconciled same PR (6 ratification-pending markers → ratified; Code-amends-conventions, ADR-009 D2). dispatch-SD-1 (gitignored): one-pager sector-callout forbidden-action note trimmed, R1-clean seed untouched. Venue now ACCEPTED guarded-trial (R-PS1..R-PS4) — live action is Cray's (launch energy run-1) | `4d1347b` (#302) / `docs/adr/0020-partner-sim-venue.md` + `docs/conventions/partnersim_project_instructions.md` |
| 2026-06-13 | **ADR-0020 (synthetic design-partner simulation venue, partner-sim) committed Proposed (#297, `e25281d`, session 57) + project system instruction landed (#298, `e387a63`)** — a specialist Cowork project that role-plays a Thai operator + emits a "partner profile package" so the intake+PDPA pipeline is rehearsed before a real partner. D1 venue OUTSIDE governance tiers (no commits / no repo mount / enters via Code receive); D2 three BINDING anti-circularity rules (R1 feed-questions-not-schema, R2 forced messiness, R3 SYNTHETIC provenance — never trips PLAN-0005 §8.1 / ADR-011 first-real-data trigger); D3 reuses completion-handoff schema (no enum change); D4 guarded-trial (mirrors ADR-012 D5) + R-PS1..R-PS4. SD-1..SD-4 recommendations only. **Awaits Cray ratification (Proposed→Accepted + SD-1..SD-4) before the project goes live (ADR-0020 T3).** Author≠reviewer (ADR-012 D4.3): Cowork authored, Code R2-reviewed + committed both | `e25281d` (#297) + `e387a63` (#298) / `docs/adr/0020-partner-sim-venue.md` + `docs/conventions/partnersim_project_instructions.md` |
| 2026-06-12 | **B-6 hyphen-normalization grader change RATIFIED + SHIPPED (#295, `2331ffb`, session 57)** — Cray ratified in-session; `grader.py` `normalize_primary_key()` folds the Unicode hyphen/dash family (U+2010–U+2014, U+2212) → ASCII `-` on both sides of the two primary-KEY comparisons only; free-text untouched. Offline dump replay vs the 2026-06-12 scored run: β 118/120 → 119/120, EXACTLY one flip (energy-007, zero collateral); aqua-028 still fails. Same measurement-correctness class as the 2026-06-08 items; no bar moves; REPORT.md dated addendum | `2331ffb` (#295) / `benchmarks/procedure_baseline/grader.py` |
| 2026-06-12 | **First SCORED watch-lane run RECORDED — watch 97.4% (38/39); M-2=b arc COMPLETE (#288, `4c46a92`, session 57)** — `gpt-oss:20b`/MS-S1, 198 items, 318 calls, 0 errors, dump-VERIFIED (39/39 `watch_graded:true`); first production `run_detached.sh` run (sentinel as designed; watcher Monitor died silently + one false alarm — truth via content-based test). Aqua + energy 13/13; supply 12/13 — sole FAIL supply-040 (reroute @1.0 on an in-spec 7.8 °C) = `forbidden_keywords` discriminating as designed. β 98.3% (same two known misses; energy-007 U+2011 now ×3 → strengthens B-6). SD-2 p95 30.18s = +0.18s nominal, within the ±10s straddle band + classifier-contaminated; no bar moves (B-6) | `4c46a92` (#288) / `benchmarks/procedure_baseline/REPORT.md` |
| 2026-06-12 | **Watch-lane ground truth PINNED — all 39 watch items (#286, `1bd6328`, session 57)** — Cray adjudicated the M-2=b pinning from the #273 calibration distribution: aqua canonical `start_emergency_aerator` + acceptable `[dispatch_technician, increase_water_exchange, escalate]`; energy canonical `restart` + acceptable `[dispatch_technician, escalate]` (`isolate` excluded → 'other'); supply_chain canonical `inspect` + acceptable `[hold, escalate]` + `forbidden_keywords [expedite, reroute]` declared (3/13 observed reroutes → forbidden). Dataset-only; the watch lane auto-flips unscored→scored; first SCORED run gated on a separate Cray go | `1bd6328` (#286) / `benchmarks/procedure_baseline/dataset/` |
| 2026-06-12 | **Lessons #24 + #25 RECORDED (#284, `4b0e306`, session 56)** — Cray-approved coda to the classifier calibration arc. **#24:** rules must live where the enforcer looks — a binding rule placed only in prose is invisible to a machine enforcer reading a different surface (C5 registry-gap finding generalized; adds an enforcement dimension to the ADR-0017 D5 placement rule). **#25:** an LLM judge's `{verdict, reason}` needs verdict-by-observable definitions + an explicit cross-field agreement contract, pinned by a prompt contract test + gold case (generalizes to the ADR-0018 goal-evaluator) | `4b0e306` (#284) / `docs/lessons/0024-rules-must-live-where-the-enforcer-looks.md` + `docs/lessons/0025-llm-judge-verdict-must-bind-to-its-own-reasoning.md` |
| 2026-06-12 | **Stop classifier SWITCHED to local `gpt-oss:20b` (#282, `3375778`, session 56)** — Cray picked **(b)** on the calibration evidence (8–30s latency acceptable). Default backend = MS-S1 Ollama (format-constrained `/api/chat`, temp 0, keep_alive 10m, 75s timeout; no API key / no WSL bridge); Anthropic API retained as rollback via `CLAUDE_CLASSIFIER_BACKEND=sonnet`. Fail-closed pause + legacy reason strings byte-identical; legacy suite pinned to sonnet + 4 new ollama-backend tests (571 passed / 2 skipped; mypy --strict clean); LIVE-verified from the prod hook runtime: 7.9s → pause | `3375778` (#282) / `.claude/hooks/_sonnet_classifier.py` |
| 2026-06-12 | **Stop-classifier calibration arc SHIPPED (#278 + #279 + #280, `246ee0a`, session 56)** — #278 completion-consistency rule (PROCEED needs concrete remaining work; decision↔reason agreement; contract-test-pinned). #279 20-case safety-weighted eval harness (full prod-prompt fidelity; gold incl. Thai); MS-S1 sweep 4×20 (80 dump-verified): `gpt-oss:20b` 19/20, recall 100%, p95 21.6s vs sonnet(prod) 17+2/20, recall 75%, p95 3.5s; nemotron-4b safety-DQ. #280 HEADLINE = registry gap not model gap → registry row C5 (host-state gate), re-verified live; transport pick (local vs API Sonnet) = Cray's | `246ee0a` (#278–#280) / `benchmarks/stop_classifier/RESULTS.md` |

## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13 (ratified `4d1347b`, #302; committed Proposed `e25281d`, #297 + instruction `e387a63`, #298 + R1 errata `655344d`, #300) — guarded trial under observation (parallel to ADR-012). A specialist Cowork project role-plays a Thai operator and emits a "partner profile package" to rehearse the intake+PDPA pipeline before a real partner; venue OUTSIDE the governance tiers (no commits / no repo mount / enters via Code receive). Three BINDING anti-circularity rules R1/R2/R3 (R3 SYNTHETIC provenance → never trips PLAN-0005 §8.1 / ADR-011 first-real-data trigger). All four venue SDs + dispatch-SD-1 ratified per Cowork rec (SD-1 N=3; SD-2 one-project-per-business-type; SD-3 size/region/maturity enums w/ energy·mid·th-regional·mixed-legacy default; SD-4 "what we refused to share" now required). D4 guarded-trial mirrors ADR-012 D5; regression triggers R-PS1..R-PS4 are the exit criteria; run 1 = energy operator (ADR-005 primary). **Now live-able: Cray launches run-1 (paste the R1-clean seed NOT the one-pager); ADR-011 audit framework stays gated on a partner conversation — the synthetic run INFORMS but never TRIGGERS it.**
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
