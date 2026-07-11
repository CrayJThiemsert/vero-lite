# PLAN-0010: Phase 3.5 — Scheduled-Task Autonomy Loop (Two-Poller Primitive Layer)

**Status:** Complete — closed as **"shipped + intentionally disabled"** and filed to
`done/` 2026-07-11 (session 118, Cray-ratified via AskUserQuestion after an ELI-CRAY
brief). The primitive layer shipped in full (`tools/loop/{_schema,dispatcher,
_status_digest}.py` + `loop/inbox/`+`loop/processed/`) and **proved itself in
production: 427 messages processed 2026-05-26 → 2026-06-25**, then Cray disabled the
dispatcher over the s76 drift hazard (the hourly task drifted past scope and committed
onto a live branch). Closing separates "is it built" (yes — evidenced by the run) from
"is it enabled" (an operational decision, reversible any time). **Any revival mints a
fresh PLAN whose subject is the drift guardrails** — not a switch-flip of this one.
AC-1/AC-3/AC-5 ticked against on-disk tests + the production run; AC-2/AC-4/AC-6 left
unticked honestly (see Close-out note).
**Owner:** Claude Code (Tier 2 — the consumer + all commits are Code-exclusive per ADR-009 D2 / ADR-013 D2; Cowork drafts this plan under interim ADR-009 D1 authority)
**Created:** 2026-05-26
**Related ADRs:** ADR-013 (autonomy axis relocation — **gates this plan**; Phase 3.5 is the scheduled-task slice of the ADR-013 D1 execution-automation axis), ADR-009 (D2 "only Code commits" — load-bearing for the Step 3 consumer commit gate; D1 interim authoring + D3 K-1/K-2 workflow context), ADR-012 (D4.3 author≠reviewer disclosure), ADR-006 (core vs vertical — the loop is vertical-agnostic core harness tooling)
**Related PLANs:** PLAN-0007 (Phase 1, MERGED — deterministic hooks G5/H1/C4 + Telegram notification bridge `tools/notify/telegram.sh`, reused in Step 6), PLAN-0008 (Phase 2, in `docs/plans/done/` — `Stop` continuation loop + Sonnet classifier + L1–L4 loop-detect; Step 3 consumer reuses these), PLAN-0009 (Phase 3 subagent topology — Ready for execution; Phase 3.5 **complements, does not replace** it and integrates only at the Step 5 use-case layer)
**Related Lessons:** Lesson #8 (Cowork K-1/K-2 workflow — binds the Step 2 Write-only producer constraint), Lesson #9 (Auto mode model-tier gating — binds the Step 3 Sonnet 4.6+ consumer model floor)

> **Ratification status.** Cowork drafted under ADR-009 D1 interim
> authority; Code R2-reviewed and Cray ratified all three §Surfaced
> decisions (SD-1 = b smoke regression; SD-2 = parallel with PLAN-0009
> Phase 3; SD-3 = Code picks loop root at execution) on 2026-05-26.
> Status flipped Draft → Ready for execution at the same time; commit
> lands on branch `feat/plan0010-phase3-5-scheduled-task-autonomy-loop`
> per ADR-009 D2.

> **Sequencing gate.** Code executes this plan only after:
>
> 1. Phase 3.5 smoke verdict = GO (✓ — Cray-ratified 2026-05-26T10:10
>    +07; commit `5768a62` on main; STATUS Current Focus).
> 2. This PLAN's `Status` flips Draft → Ready for execution after Cray
>    ratifies the §Surfaced decisions section. (✓ — ratified 2026-05-26
>    in the PR that introduces this file.)
> **Close-out note (2026-07-11, session 118).** AC-2 (the deliberately-wrong-clock
> producer test), AC-4 (the formal 4-case identity-matrix test mapping), and AC-6
> (the formal Phase 1+2+smoke regression re-run) were **never formally discharged**
> and are left unticked — this PLAN closes by **operational decision** (the s76
> drift hazard → dispatcher disabled), not by full AC completion. The un-discharged
> ACs become requirements of the fresh guardrails PLAN if the loop is ever revived.
> Companion fix in this PR: `tools/loop/__init__.py`'s stale docstring (it still
> called the dispatcher "(future)" though `dispatcher.py` shipped).

> 3. Cray resolves the Phase 3 ↔ Phase 3.5 sequencing surface (run
>    PLAN-0010 in parallel with PLAN-0009 Phase 3 execution, or strictly
>    serial). (✓ — **parallel**, ratified 2026-05-26 — see §Surfaced
>    decisions SD-2.)

## Goal

Stand up the **scheduled-task autonomy loop**: a two-poller
producer/consumer primitive that lets a **best-effort Cowork producer**
(Write-only, sandbox-constrained) and a **reliable Code Desktop
consumer** (full bash + git) exchange work over a filesystem inbox on the
shared WSL-UNC main checkout, **without a Cray paste in the loop**. The
smoke test (GO, 2026-05-26) proved the primitive mechanics; Phase 3.5
turns the smoke scaffold into a durable, observable, identity-gated loop.

Phase 3.5 is a **primitive layer**: it ships the message schema,
lifecycle, two poller patterns, the commit identity gate, and
observability — **heartbeat-class workloads only**. It deliberately
complements (does **not** replace) the PLAN-0009 Phase 3 subagent
topology; the two land separately and integrate only at the use-case
layer (Step 5). The load-bearing safety property is preserved and
reinforced: **only Code commits**, now enforced by a composed
identity gate (`agent_id`-absent-in-hook-stdin + `CLAUDE_TIER=code`)
that covers all four identity cases (ADR-013 D2 / ADR-009 D2).

## Acceptance Criteria

> Six criteria. AC-1…AC-5 cover the new Phase 3.5 surface; AC-6 guards
> against Phase 1 + Phase 2 + smoke-baseline regression. Per the Cray
> verification-rigor directive (PLAN-0009 §Step 6, binding for all
> unattended autonomy work), each AC's §Verification row carries a
> case-coverage matrix and names uncovered cases as residual risk —
> "we are confident it does what we intend," not "tests pass."

- [x] *(ticked 2026-07-11 s118 close — `tools/loop/_schema.py` + `tests/loop/{test_schema,test_dispatcher,test_loop_roundtrip}.py` cover the lifecycle/idempotency/retention markers; 427 production messages moved inbox→processed exactly once)* **AC-1 — Message schema + lifecycle are defined and enforced.** A
  message has a documented filename pattern (mtime-derived nonce +
  producer-id, **never** an agent-claimed timestamp) and a body schema
  (YAML frontmatter + structured payload). Messages move `inbox/` →
  `processed/` exactly once; re-processing the same message is
  idempotent (no duplicate side effect). A retention/cleanup policy for
  `processed/` is specified and tested.

- [ ] **AC-2 — Cowork producer writes valid messages within its sandbox
  constraints.** The producer uses `Write` only (no `mcp__workspace__bash`
  per K-1; no `.claude/` writes per K-2), emits a filename whose
  collision-resistance does not depend on the producer's (drifting)
  clock, and stamps the body with "claimed time + drift caveat." A run
  with a deliberately wrong claimed clock still produces a
  non-colliding, consumer-parseable message.

- [x] *(ticked 2026-07-11 s118 close — `tools/loop/dispatcher.py` + `tests/loop/test_dispatcher.py` mtime-order/idempotency coverage; one month of reliable production consumption)* **AC-3 — Code consumer processes reliably and is the only
  committer.** The consumer (Sonnet 4.6 + Auto mode per Lesson #9)
  reads the inbox in **mtime order**, processes idempotently, archives
  to `processed/`, and — for any message whose handling includes a
  commit — the commit succeeds **only** under the composed identity gate
  (`agent_id` absent in hook stdin **and** `CLAUDE_TIER=code`). A
  negative test confirms each of the other three identity cases is
  denied at the `pretooluse_git_deny.py` hook layer.

- [ ] **AC-4 — Identity gate covers all four cases deterministically.**
  The composed G5 check resolves the 4-case matrix (main Code
  interactive ✅; main Code scheduled ✅; Plan/Explore subagent ❌;
  Cowork ❌) with a test mapped to every row, and is bypass-immune even
  to `bypassPermissions` (ADR-013 D2). This extends, and must not
  regress, the PLAN-0009 Step 1 / AC-3 subagent-identity design.

- [x] *(ticked 2026-07-11 s118 close — dispatcher carries L1-L4 poison-detect + retention prune + Telegram integration, exercised by `tests/loop/` and the production run)* **AC-5 — The loop is observable and fails loudly.** Consumer
  failure (parse error, processing exception, git-gate denial when a
  commit was expected) fires a Telegram alert via
  `tools/notify/telegram.sh` (PLAN-0007). Logs are retained/rotated per
  the Step 6 policy. A peak-hours scheduling guard is documented and any
  non-heartbeat workload is scheduled off-peak Bangkok daytime.

- [ ] **AC-6 — Phase 1 + Phase 2 + smoke baseline regression-free.**
  Re-run after Phase 3.5 lands: Phase 1 (G5 16-case bypass-immune
  matrix incl. the new scheduled-Code identity case, H1
  handoff-validator, C4 research-path-deny); Phase 2 (`Stop`
  continuation, Sonnet classifier conservatism, L1–L4 loop-detect +
  reset); and the smoke baselines (Code awake-reliability, Cowork
  awake-reliability, sleep-recovery catch-up). **All must remain green**;
  a Phase 3.5 change that disturbs a prior guarantee is a hard fail
  regardless of new-feature progress.

## Out of Scope

> Deferred beyond Phase 3.5. Listed so the boundary is explicit.

- ❌ **Phase 3 subagent topology execution** (PLAN-0009 line). Phase 3.5
  integrates with it at the use-case layer only (Step 5); it does not
  implement or depend on the subagent triad shipping first.
- ❌ **Self-pacing via `update_scheduled_task`** (research §7 stretch
  goal). Defer to a future plan if value is clear.
- ❌ **Cross-session message persistence beyond `inbox/`/`processed/`**
  (would likely need a small DB). Defer.
- ❌ **Replacing the Anthropic scheduled-task primitive with an MCP
  `vero-bridge`.** Kept as a roadmap fallback if the primitive degrades
  during research-preview; not active scope unless Phase 3.5 fails
  post-ship.
- ❌ **Production-scale workloads** (> ~1k tokens/run on the Cowork
  side). Phase 3.5 ships **heartbeat-class only**; scale-up is a future
  plan.
- ❌ **Production-grade UI on top of the loop** (CLI / web dashboard).
  Defer.
- ❌ **Multi-machine coordination.** Phase 3.5 is single-machine and
  machine-awake-required by the Anthropic primitive's design.

## Steps

### Step 1 — Message schema + lifecycle

Define the on-disk contract before any poller is wired.

- **Root + directory layout.** A configurable loop root (e.g.
  `loop/` at repo top, or a `tools/loop/` data dir — Code picks the
  final path at execution) containing `inbox/` and `processed/`. The
  root **must not** be under `.claude/` (K-2 blocks the Cowork producer
  from writing there). Because a Code session running from a git
  *worktree* sees neither uncommitted-new nor gitignored files (STATUS
  reconciliation finding #2), the consumer reads the inbox from the
  **main checkout**, and the inbox path is either git-tracked or
  consumed in-place on the main tree — never relied upon across a
  worktree boundary.
- **Filename pattern.** `<producer-id>-<mtime-nonce>[-<rand>].msg.md`.
  The ordering key is the **filesystem `mtime`**, never the
  agent-claimed timestamp (drift evidence −3h34m … +5h17m across 7
  smoke fires caused filename collisions that made the inbox count of 7
  under-represent ~11 successful fires). The nonce derives from `mtime`
  (or a process-random suffix) so two fires in the same wall-clock
  minute do not overwrite each other.
- **Body schema.** YAML frontmatter (producer-id, claimed-time +
  explicit drift caveat, message-type, schema-version) + a structured
  payload section. Keep it a flat, stdlib-parseable subset (mirror the
  `tools/handoffs/_schema.py` hand-rolled-parser discipline — no new
  heavy deps).
- **Lifecycle + idempotency.** A message is claimed by the consumer,
  processed once, then `mv`'d to `processed/`. Re-running the consumer
  over an already-processed message is a no-op. Specify the
  `processed/` retention + cleanup policy (age-based prune; bounded
  directory size).

### Step 2 — Cowork-side producer pattern (best-effort)

The sandbox-constrained writer. **~85% awake-reliability observed** in
smoke — best-effort by nature, never load-bearing for safety.

- **Write-only enforcement.** `Write` tool only. **No
  `mcp__workspace__bash`** (K-1 UNC refusal), **no git**, **no `.claude/`
  writes** (K-2). The producer is a heartbeat-class workload: no bash, no
  Read of `.claude/<*>` required.
- **Model + cadence.** Haiku 4.5 + Cowork "Act without asking" + Hourly.
  (Cowork's "Act without asking" is its own permission abstraction,
  separate from Code's Permission mode; Haiku is fine here per Lesson #9
  §5 — the Sonnet-classifier floor applies to Claude Code Auto mode, not
  to Cowork.)
- **Time-awareness workaround (binding).** Filename uses the
  mtime-nonce (Step 1); the body's claimed timestamp carries an explicit
  "claimed by agent; authoritative time = file mtime" caveat. Producer
  prompt instructs this explicitly so a drifting clock cannot corrupt
  ordering or cause silent overwrite.
- **Permission-mode safety review.** Confirm the Connectors panel is
  empty by default for the producer task (no unintended tool reach);
  document the exact toggle state so the producer cannot escalate beyond
  Write.

### Step 3 — Code Desktop-side consumer pattern (reliable)

The trustworthy processor. **100% awake-reliability observed** in smoke
(9/9). The only tier with real bash + git on UNC paths.

- **Model + mode.** Sonnet 4.6 + Auto mode — **mandatory** per Lesson #9
  (Auto mode greys out on Haiku 4.5; "Not available for the selected
  model"). Cost ≈ $0.07–0.10/day heartbeat-class, acceptable.
- **Ordering + idempotency.** Read `inbox/` in **mtime order**; process
  each message once; archive to `processed/`.
- **Commit gate (load-bearing).** For any message whose handling
  includes a commit, the commit is allowed **only** under the composed
  identity gate. The smoke confirmed `CLAUDE_TIER=code` propagates into
  the scheduled Code session (stable across 9 runs); combined with the
  PLAN-0009 Step 1a finding that `agent_id` is **absent** for the main
  agent and **present** for subagents, the single G5 check resolves all
  four cases (see AC-4 / Step 4).
- **Failure handling.** Integrate the PLAN-0008 L1–L4 loop-detect so a
  consumer that thrashes on a poison message trips the loop fail-safe
  and pauses + alerts rather than looping unattended.

### Step 4 — Initial use cases (Cray ratified — b ships first)

Candidate first workloads for the loop. Cray ratified **(b) smoke
regression** as the Phase 3.5 first ship on 2026-05-26 (see §Surfaced
decisions SD-1, now resolved); (a)/(c)/(d) remain candidates but
**NOT shipped in Phase 3.5**.

| # | Candidate | Sketch | Class | Phase 3.5 ship |
|---|-----------|--------|-------|----------------|
| a | **Hourly STATUS digest** | Producer summarizes recent `docs/STATUS.md` changes → consumer files a short rollup | heartbeat | deferred |
| **b** | **Smoke regression** ← ratified first | Re-run the scheduled-task smoke once/day; alert if reliability drifts below the smoke baseline | heartbeat | **✓ ships** |
| c | **Governance reminder** | Poke unmerged ADRs/PLANs older than N days (e.g. a draft sitting un-ratified) | heartbeat | deferred |
| d | **Deferred-OQ rotation** | Surface one open question from `docs/plans/done/` per cycle for review | heartbeat | deferred |

Rationale (Cray + Code agreed): (b) directly extends the smoke scaffold
already in place (currently Paused; resumable), exercises the full
producer→consumer→alert path end-to-end, and its output — a reliability
number — is the cheapest signal that the loop itself is healthy before
any higher-value workload rides on it. (a)/(c)/(d) wait until (b) proves
the loop in production over multi-day wall-clock.

### Step 5 — Integration with Phase 3 subagent topology (use-case layer only)

The seam between the two phases. **No dependency until PLAN-0009 lands.**

- Until Phase 3 ships, the consumer is a **monolithic main agent** (no
  subagent spawn).
- After Phase 3 ships, the consumer **may** spawn Plan/Explore subagents
  per message. Subagent identity is already gated by the `agent_id`
  hook-stdin signal (PLAN-0009 Step 1/AC-3) — a spawned subagent is
  denied commit by the same G5 check, so the loop's safety property
  composes cleanly with subagent fan-out.
- Result reduction back to the consumer follows the PLAN-0009 bounded
  result-reduction contract.
- **Off-peak guideline (binding for subagent-spawning workloads).**
  Sonnet × subagent fan-out raises cost and token volume; schedule such
  workloads off-peak Bangkok daytime (~7 AM – 6 PM Bangkok). Heartbeat
  workloads are negligible in any window. See Step 6 for the peak-hours
  source.

### Step 6 — Observability, AC matrix, closeout

Mirror the PLAN-0008 Step 7/8 + PLAN-0009 Step 6 pattern.

- **Notification.** Consumer failure → Telegram via
  `tools/notify/telegram.sh` (PLAN-0007; env-var token per ADR-013 D5,
  never committed). Degrade gracefully if env vars are unset (PLAN-0007
  no-op requirement).
- **Logs.** Define a log path (outside `.claude/` for Cowork
  compatibility; `docs/logs/` thin tracked summaries per CLAUDE.md §10
  for the durable record) + a rotation/retention policy.
- **Peak-hours guard.** Encode the Cowork UI warning verbatim as the
  scheduling rationale: *"This task runs during peak hours (weekdays
  5:00 AM–11:00 AM PT, 7:00 PM–1:00 AM local time) and will consume your
  session usage limits faster."* → Bangkok translation: peak ≈ 7 PM – 2
  AM Bangkok; off-peak ≈ 7 AM – 6 PM Bangkok. Heartbeat-class is fine in
  any window; batch/long-context work is off-peak only.
- **Per-task stagger note.** Both primitives use per-task deterministic
  stagger (Code ≈ +5 min past hour; Cowork ≈ +4 min past hour). Co-
  scheduled tasks plan stagger offsets if coordination is needed.
- **AC matrix + closeout.**
  `.claude/handoffs/session-NN/<YYYY-MM-DD>-<HHMM>-code-plan0010-phase3-5-closeout.md`
  with the case-coverage matrix, residual-risk sign-off, and the
  `git mv docs/plans/0010-*.md docs/plans/done/` archive step.

## Verification

Maps 1:1 to AC-1…AC-6. Per the Cray verification-rigor directive
(binding for all unattended autonomy work), each component ships a
**case-coverage matrix** — happy / boundary-threshold / fail-closed /
adversarial-bypass / concurrency-race — with a test mapped to every row
and any uncovered case named as residual risk. Live verification over
wall-clock days is required **in addition** to unit coverage; sign-off
states confidence explicitly.

Required matrix rows (illustrative, not exhaustive — Step 6 fills the
full grid):

- **Happy:** producer writes → consumer processes → archive → (optional)
  commit under the gate.
- **Boundary:** two fires in the same wall-clock minute (nonce collision
  resistance); inbox empty; `processed/` at retention bound.
- **Fail-closed:** poison/unparseable message → consumer pauses + alerts,
  does not loop (L1–L4); Telegram env vars unset → graceful no-op, not a
  crash.
- **Adversarial / bypass:** commit attempt from each non-Code identity
  case → denied at the hook (incl. `bypassPermissions`); a message
  crafted to look like it carries commit authority cannot obtain it.
- **Concurrency / race:** consumer fires while producer is mid-write
  (partial file) → consumer skips/quarantines rather than processing a
  truncated message; two consumer fires overlapping → idempotent.

**Residual risks to name explicitly in sign-off (smoke data is real but
limited — ~8h awake-time only):**

1. **Multi-day reliability** — smoke covered ~8h awake; sustained
   multi-day awake-reliability (esp. Cowork's ~85%) is unproven at
   longer horizon.
2. **High-volume cost scaling** — smoke was heartbeat-class only; cost
   and "Skipped" rate under peak-hours quota pressure for larger
   workloads are uncharacterized.
3. **Anthropic primitive changes during research-preview** — scheduled
   tasks / Auto mode / Cowork "Act without asking" semantics may shift
   without notice; the loop must degrade safely if they do.
4. **Cowork "Skipped" rate when peak-hours quota is tight** — 2 explicit
   "Skipped" entries in smoke; rate under sustained peak load unknown.

## Surfaced decisions (RATIFIED 2026-05-26 — Cowork rule #8)

> Presented with options + a recommendation; Cray decided.
> All three resolved in the PR that introduces this file.

- **SD-1 — First use case (Step 4). ✅ RATIFIED = (b) smoke regression.**
  Cowork-recommended; Code R2-concurred; Cray-ratified 2026-05-26.
  Extends the smoke scaffold (currently Paused), exercises the full
  producer→consumer→alert path, and the reliability number it produces
  is the cheapest signal that the loop itself is healthy before any
  higher-value workload rides on it. (a)/(c)/(d) deferred beyond
  Phase 3.5 (see Step 4 table).
- **SD-2 — Sequencing vs. PLAN-0009 Phase 3. ✅ RATIFIED = parallel.**
  Cowork-recommended; Code R2-concurred; Cray-ratified 2026-05-26.
  Phase 3.5 execution may proceed in parallel with PLAN-0009 Phase 3
  (Step 1b contract design + onward) — the consumer is monolithic until
  Phase 3 lands (Step 5 has no hard dependency on the subagent triad),
  and the composed identity gate is designed to compose cleanly with
  subagents when they arrive.
- **SD-3 — Loop root path. ✅ RATIFIED = Code picks at execution.**
  Cowork-deferred; Cray-ratified 2026-05-26. Code chooses the final
  path (e.g. `loop/` at repo top vs. `tools/loop/` data dir vs. other)
  when opening Step 1 execution; the K-2 + worktree constraints from
  Step 1 remain binding regardless of the chosen path.

## Implementation Notes

Drafted by Cowork in Tier-1 (governance authoring) mode under the
interim ADR-009 D1 process (the Phase-3 relocation has not fully
executed; the Plan subagent that would otherwise draft this does not
exist yet). Cowork has **no commit authority** (ADR-009 D2); Code
reviews and commits this file on
`feat/plan0010-phase3-5-scheduled-task-autonomy-loop`. AI-assisted per
project convention (noted in commit body, never as Co-Authored-By, per
CLAUDE.md §7).

**Author≠reviewer disclosure (ADR-012 D4.3).** The substance of this
PLAN was **not** self-deliberated in a Cowork Tier-1b free-form session.
It was authored from the Code-authored dispatch
(`.claude/handoffs/session-10/2026-05-26-1020-code-plan0010-cowork-dispatch.md`),
whose outline + smoke findings derive from Code's smoke observation and
Cray's GO ratification. The independent-deliberation separation is
therefore **intact**: the drafter (Cowork) is distinct from the
outline's originator (Code/Cray), and Code's fact-pack / R2 review
(ADR-009 D3 step 6) remains the independent check.

**Schema / fact-pack self-check (K-1 validator gap flagged).** Per K-1,
Cowork cannot run repo tooling (`mcp__workspace__bash` refuses the
WSL-UNC cwd), so no live validator was run. This PLAN is not a
`.claude/handoffs/` artifact, so `validate_handoff.py` frontmatter rules
do not apply; the relevant canonical shape is the PLAN template
(`docs/plans/0000-template.md`), matched field-by-field (Status / Owner
/ Created / Related ADRs / Goal / Acceptance Criteria / Out of Scope /
Steps / Verification). All repo citations were verified against the live
tree via Read/Glob this session:

- **`0010` is the next free PLAN number** — `docs/plans/` glob:
  `0004`/`0009` active + `done/{0003,0005,0006,0007,0008}` + `PLAN-001`
  + templates; **no `0010*` exists**.
- **`tools/notify/telegram.sh` exists** (Step 5/6 + AC-5 citation) —
  confirmed via glob.
- **ADR slots** 0000–0010 + 0012 + 0013 exist; **0011 reserved** — Step
  references to ADR-009 D2, ADR-013 D1/D2/D5, ADR-012 D4.3 all resolve.
- **Lesson #8 / Lesson #9** resolve to
  `docs/lessons/0008-cowork-tier1-k1-k2-workflow.md` and
  `docs/lessons/0009-anthropic-mode-model-tier-gating.md`; the
  Auto-mode-Sonnet-floor and K-1/K-2 constraints are quoted from those
  files, not paraphrased from memory.
- **Smoke findings** (4-case identity table, ±5h drift, ~85% vs 100%
  awake-reliability, peak-hours verbatim warning, per-task stagger) are
  reproduced from `docs/STATUS.md` Current Focus + the Code dispatch's
  inline reproduction (the underlying
  `docs/research/private/phase3.5-smoke/findings.md` is gitignored on
  Cray's machine and not Cowork-readable).

## Non-commit reminder (ADR-009 D2 / ADR-013 D2 — load-bearing)

This is a Cowork draft. **Cowork does not commit** — only Code commits,
and the boundary is enforced deterministically by
`pretooluse_git_deny.py` (bypass-immune even to `bypassPermissions`,
ADR-013 D2). Code applies the file write + commit after review; Cowork
could not run `git` even if instructed.
