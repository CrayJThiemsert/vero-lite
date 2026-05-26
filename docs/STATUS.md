---
last_updated: 2026-05-26T11:30:00+07:00
session: 10
current_batch: **PR #24 merged (`b5d2489`) — PLAN-0010 (Phase 3.5 scheduled-task autonomy loop) Ready for execution.** Cowork drafted under interim ADR-009 D1 authority (dispatch 2026-05-26-1020-code-plan0010-cowork-dispatch.md; completion 2026-05-26-1100-cowork-plan0010-draft-completion.md); Code R2-reviewed and Cray ratified all three Cowork-surfaced decisions 2026-05-26: **SD-1 = (b) smoke regression** as first-ship use case; **SD-2 = parallel** with PLAN-0009 Phase 3 (resolves session-10 kickoff §4 sequencing question — Step 1b unblocked to proceed in parallel); **SD-3 = Code picks loop root path** at Step 1 execution. Plan commit `daaa394`, 398 insertions; pre-commit clean (detect-secrets passed); `validate_handoff.py` green on Cowork completion handoff (K-1 trust-but-verify flag closed in-process before commit). Author≠reviewer separation INTACT (ADR-012 D4.3).
current_actor: code
blocked_on: nothing
next_action: Two paths now open in parallel (per ratified SD-2): (1) **PLAN-0010 execution path** — Step 1 (message schema + lifecycle, incl SD-3 loop-root choice); will be a multi-session arc like Phase 2 was. (2) **PLAN-0009 Step 1b path** — subagent topology contract design, informed by Step 1a survey (`docs/research/private/2026-05-25-subagent-primitive-survey.md`, 8/8 high-confidence). Cray picks which to open first next session (or both in parallel sessions). Smoke scheduled tasks remain Paused; safe to resume any time PLAN-0010 Step 6 verification needs live data; cleanup deferred until execution captures findings + Cray approves teardown.
head_commit: b5d2489
recent_commits: [b5d2489, daaa394, 5768a62, 414e564, b71d95a, 04820be, 0fb83fb, 624882d, fddcf2e, 93e5df7]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

**Session 10 — PR #24 merged (`b5d2489`) — PLAN-0010 (Phase 3.5
scheduled-task autonomy loop) Ready for execution; two execution paths
now open in parallel.**

Cowork drafted PLAN-0010 under interim ADR-009 D1 authority (Tier-1
governance authoring, Claude Sonnet 4.6 in Cowork tab — dispatch
`.claude/handoffs/session-10/2026-05-26-1020-code-plan0010-cowork-dispatch.md`;
completion `.claude/handoffs/session-10/2026-05-26-1100-cowork-plan0010-draft-completion.md`).
Code R2-reviewed against the dispatch contract + session-11 kickoff §3
/ §5 caveats; all citations resolve (ADR-009 D1/D2, ADR-013 D1/D2/D5,
ADR-012 D4.3, PLAN-0007/0008/0009, Lesson #8/#9); composed G5 4-case
identity table encoded at AC-4 + Step 3; smoke caveats (filesystem
`mtime` as authoritative fire-time, off-peak Bangkok scheduling guard)
folded into Step 1 + Step 2 + Step 5 + Step 6; Verification ships full
case-coverage matrix (happy / boundary / fail-closed / adversarial /
concurrency) per Cray verification-rigor directive.

**Cray ratified all three Cowork-surfaced decisions 2026-05-26
(in PR #24):**

- **SD-1 = (b) smoke regression** as Phase 3.5 first-ship use case.
  Rationale: directly extends the smoke scaffold (currently Paused;
  resumable), exercises full producer→consumer→alert path, output
  (a reliability number) is the cheapest signal that the loop itself
  is healthy before any higher-value workload rides on it. Candidates
  (a) hourly STATUS digest / (c) governance reminder / (d) deferred-OQ
  rotation all deferred beyond Phase 3.5.
- **SD-2 = parallel** with PLAN-0009 Phase 3 execution. Resolves the
  Phase 3 Step 1b sequencing question carried in session-11 kickoff §4
  — Step 1b (subagent topology contract design) may proceed in parallel
  with PLAN-0010 execution without blocking. The two design spaces
  overlap only at the Step 5 use-case integration layer (deferred
  to "after Phase 3 lands"), so independent progress is safe; identity
  gate composes cleanly with subagents when they arrive.
- **SD-3 = Code picks loop root path** at Step 1 execution (e.g.
  `loop/` at repo top vs `tools/loop/` data dir vs other). K-2 +
  worktree constraints from Step 1 binding regardless.

**Provenance + integrity:**

| Item | Result |
|------|--------|
| PR #24 | https://github.com/CrayJThiemsert/vero-lite/pull/24 — merged via merge commit `b5d2489` |
| Plan commit | `daaa394` — 1 file, 398 insertions; `docs(plans):` Conventional Commits; AI-assistance noted in body (NOT `Co-Authored-By` per CLAUDE.md §7) |
| Pre-commit | detect-secrets passed; ruff/mypy/YAML skipped (no code files in PR) |
| K-1 validator gap | Closed in-process — `validate_handoff.py` green on Cowork completion handoff before commit |
| Author≠reviewer (ADR-012 D4.3) | INTACT — drafter (Cowork) distinct from outline originator (Code dispatch + Cray smoke GO); R2 review = independent check |

**Two execution paths now open in parallel (per ratified SD-2):**

1. **PLAN-0010 execution path** — Step 1 (message schema + lifecycle,
   incl SD-3 loop-root path choice). Will be a multi-session arc like
   Phase 2 was. AC-1…AC-6 + 4 named residual risks all live.
2. **PLAN-0009 Step 1b path** — subagent topology contract design,
   informed by Step 1a survey
   (`docs/research/private/2026-05-25-subagent-primitive-survey.md`,
   8/8 high-confidence answers; key bonus primitives — `isolation`,
   `maxTurns`, `SubagentStart/Stop` hooks, transcript path,
   Plan/Explore name-reservation, result-reduction caveat — all noted
   in session-11 kickoff §5.2 for fold-in).

**Smoke scheduled tasks (Paused):** still safe to resume any time if
PLAN-0010 Step 6 verification needs live data; cleanup deferred until
execution captures findings + Cray approves teardown (per session-11
kickoff §5.4 OQ list).

**Next action:** Cray picks which of the 2 paths to open first next
session (or both in parallel sessions — they don't interfere). Both
are unblocked. No external dependencies in flight.

---

**Prior — Phase 3.5 smoke verdict = GO (early, Cray-ratified
2026-05-26T10:10 +07).** Smoke ran ~18h wall-clock / ~8h awake-time
(observation cut short of nominal 24h plan because all 5 load-bearing
questions answered with high confidence + 2 minor caveats characterized,
per Cray's pragmatic call: "ถ้าเกิด Extra data หลังจากเรา GO ก็น่าจะ
เป็นอะไรที่เราช่วยกันแก้ไขได้").

**Data summary:**

| Side | Runs | Awake-reliability | Notes |
|------|------|-------------------|-------|
| Code Desktop scheduled task (`phase35-smoke-code-reader`, Sonnet 4.6 + Auto) | 8 of 8 expected during ~8h awake | **100%** | Stable `tier=code` across all runs; `bash=ok` all runs; clean ~10h overnight sleep → 1 catch-up run on wake (per Anthropic harness "catch-up latest missed" semantic, live-verified) |
| Cowork scheduled task (`phase35-smoke-cowork-heartbeat`, Haiku 4.5 + Act-without-asking, Write-only) | 11+ successful of 13+ visible attempts (per Cowork history page) | **~85%** | 2 explicit "Skipped" entries (one initial-setup, one sleep-transition); Cowork inbox has 7 files because Cowork agent time-awareness drift causes filename collisions (overwrite), NOT missed fires |

**5 load-bearing questions all ✅:**

1. Primitive mechanics — both sides fire and write expected files
2. `tier=code` env propagates into scheduled Code session (Phase 3.5 G5 commit gate viable; combines cleanly with PLAN-0009 Step 1a Q3 hook-stdin `agent_id` mechanism for unified 4-case identity composition)
3. Cross-task visibility on UNC mount — Code reader sees all Cowork writes
4. Code Desktop bash works on UNC paths (unlike Cowork's broken `mcp__workspace__bash`)
5. Sleep-recovery clean — ~10h overnight machine sleep → wake → both sides resume + 1 catch-up run each (older missed runs silently dropped per research-note caveat #4, confirmed live)

**2 minor caveats encoded for PLAN-0010 design:**

- **Use filesystem `mtime` as authoritative fire-time** — never trust Cowork agent's claimed timestamp. Drift evidence: Cowork's claimed times in inbox filenames vs actual file mtime show errors from -3h 34m (claimed earlier) to +5h 17m (claimed later) across 7 fires. Filename collisions from this drift caused inbox count (7) to under-represent fire count (~11 successful). Filename should include mtime-derived nonce or process-random suffix for collision resistance.
- **Schedule heavy/batch tasks off-peak Bangkok daytime** — NEW finding F10: Cowork scheduled-task detail page surfaces peak-hours warning verbatim "*This task runs during peak hours (weekdays 5:00 AM-11:00 AM PT, 7:00 PM-1:00 AM local time) and will consume your session usage limits faster.*" Translated for Asia/Bangkok: peak ≈ 7 PM – 2 AM Bangkok; off-peak ≈ 7 AM – 6 PM Bangkok. Heartbeat-class workloads (~1k token/run × hourly) negligible in any window; future high-volume Phase 3.5 work (batch operations, long-context tasks) should be scheduled off-peak. Not surfaced in any of 5 Anthropic docs surveyed during Step 1a research spike + 4 docs cross-checked for Step 1 split — UI-only warning. Candidate for `docs/lessons/` promotion if pattern reproduces elsewhere (Code Routines cloud, Mobile, etc.); for now scoped to F10 in findings file + PLAN-0010 design notes.

**Stagger / cadence observations (F-OBSERVED-4):** Both primitives use **per-task deterministic stagger** (not per-fire random delay). Code Desktop = consistent +5min past hour offset across all 8 runs; Cowork = ~+4min past hour offset across visible attempts. PLAN-0010 implication: co-scheduled tasks must plan stagger offsets if coordination needed (or accept near-same-minute fire times).

**Findings durability:** F1–F10 + F-OBSERVED-1..4 fully captured in `docs/research/private/phase3.5-smoke/findings.md` (gitignored, local-durable on Cray's machine). PLAN-0010 drafting references this file as source-of-truth. Smoke scheduled tasks left running post-verdict for extra reliability data points (low cost — Code Sonnet ~$0.07/day, Cowork heartbeat negligible); cleanup deferred until PLAN-0010 captures all needed findings and Cray approves teardown.

**Identity unification across all 4 cases (final design, combining Step 1a Q3 + Phase 3.5 F5):**

| Identity case | `agent_id` in hook stdin | `CLAUDE_TIER` env | G5 verdict |
|---|---|---|---|
| Main Code interactive | absent | `code` | ✅ allow commit |
| **Main Code scheduled (Phase 3.5)** | **absent** | **`code` (verified live)** | **✅ allow commit** |
| Plan/Explore subagent (Phase 3) | PRESENT | (inherited) | ❌ deny commit |
| Cowork (impossible reach) | absent | empty/other | ❌ deny commit |

One combined check, four cases covered — beautifully unified primitive-native design.

**Next action:** Compose Cowork dispatch block for PLAN-0010 drafting per ADR-009 D1 interim phasing (same pattern as PLAN-0009). Phase 3 execution remains HELD pending Cray sequencing decision (parallel-with-PLAN-0010 vs strictly-serial).

**Prior — PLAN-0009 Step 1 split MERGED + Step 1a survey DONE +
Phase 3.5 smoke observation RUNNING.** Three-track day:

1. **PR #22 (PLAN-0009 Phase 3, `fddcf2e`) + PR #23 (Step 1 split,
   `0fb83fb`) MERGED to main.** HEAD `0fb83fb`. PR #23 splits §Step 1
   into Step 1a (research spike, 1–2 hr) + Step 1b (contract design,
   day-scale). Rationale: Code post-merge cross-check of 4 Anthropic
   docs (Cowork Scheduled / Live Artifacts / CC Routines / Desktop
   scheduled tasks) found 3-of-4 had at least one substantive diff vs
   the Cowork research note that informed PLAN-0009 — including
   undocumented `window.cowork.*` JS APIs, stale daily-run-cap numbers,
   and `CLAUDE_TIER` env-var inheritance that was unverified at draft
   time. Verifying live before contract design lock-in matches the
   PLAN-0008 fact-pack-first discipline + Cray's verification-rigor
   directive (PLAN-0009 §Step 6 + Verification).

2. **Step 1a research spike DONE** — background general-purpose subagent
   (8 min, 95k tokens, 17 tool calls — Code's first parallel-agent
   demonstration this project) wrote
   `docs/research/private/2026-05-25-subagent-primitive-survey.md`
   (Tier-0 research note, gitignored) with 8/8 questions high-
   confidence. Verbatim quotes + 5 Anthropic source URLs. Key findings:

   - **Identity signal = `agent_id` + `agent_type` JSON fields in hook
     PreToolUse/PostToolUse stdin** (Q3, load-bearing for AC-3/AC-6).
     **NOT env vars.** G5 `pretooluse_git_deny.py` final design composes
     2 signals into 1 check for 4 identity cases:
     - `agent_id` PRESENT in stdin → subagent invocation → deny commit
     - `agent_id` ABSENT + `CLAUDE_TIER=code` env → main Code
       (interactive OR Phase-3.5 scheduled) → allow commit
     - `agent_id` ABSENT + `CLAUDE_TIER` not `code` → non-Code → deny
       Resolves ADR-013 OQ-3 unification mechanism via documented harness
     primitive (no env-var gymnastics needed).
   - **Tool allowlist enforced at harness layer** (Q1): `tools` /
     `disallowedTools` frontmatter fields gated by harness before
     dispatch. AC-2 negative tests feasible as written.
   - **No native cwd-narrow or write-path-allowlist primitive** (Q2, Q5).
     AC-3's "Plan writes only under `docs/{adr,plans}/`" = new
     `PreToolUse` hook `pretooluse_plan_subagent_write_deny.py`
     extending the C4 `pretooluse_research_path_deny.py` pattern.
     Preferably in Plan subagent's frontmatter `hooks:` field (subagent-
     scoped, auto-cleanup on subagent exit).
   - **Result reduction = "final message verbatim"** (Q4). No hard
     byte/token bound — "bounded summary" output contract must be
     encoded in subagent system prompt. Residual risk: verbose subagent
     leaks final message into main context.
   - **Built-in `Plan` and `Explore` reserve those exact names** (Q6).
     Step 1b custom subagents must pick non-colliding names; recommend
     `plan-drafter` + `explore-research`.
   - **`isolation: worktree`** frontmatter field gives the subagent a
     fresh checkout — conflicts with CLAUDE.md §11 worktree-OFF default
     for single-doc work. Step 1b: omit `isolation` by default for Plan
     (writes to parent cwd; main agent commits).
   - Bonus primitives discovered: `maxTurns` (loop fail-safe),
     `SubagentStart` / `SubagentStop` hook events (clean wire for AC-5
     completion notify), documented subagent transcript path
     (`~/.claude/projects/<project>/<sessionId>/subagents/agent-<id>.jsonl`
     — useful for AC-6 audit trail). All 8 questions answered without
     live verification needed.

3. **Phase 3.5 smoke observation RUNNING** (started 2026-05-25T16:03 →
   +24-48h). Setup complete with 2 Anthropic scheduled tasks (Cowork
   hourly Write-only producer + Code Desktop hourly bash reader/observer;
   both pinned to MAIN checkout via
   `\\wsl.localhost\Ubuntu-24.04\home\crayj\work\vero-lite` UNC path).
   Run 1 answered 4 of 4 load-bearing questions favorably:

   - `tier=code` ✅ — `CLAUDE_TIER` env var propagates into Code Desktop
     scheduled session (load-bearing for OQ-1 ↔ OQ-3 unification + G5
     gate; combines cleanly with Q3 stdin signal above)
   - `bash=ok` ✅ — Code Desktop scheduled task has working bash on UNC
     paths (NOT the broken `mcp__workspace__bash` Cowork uses; different
     sandbox/layer)
   - `inbox=1` + cross-task file visibility ✅ — Code Desktop reader saw
     Cowork's Write-tool output (same UNC mount, both sides)
   - Cowork `Write` tool works on UNC ✅ — K-1 (`mcp__workspace__bash`
     UNC refusal) confirmed live in scheduled-task context but does NOT
     gate Cowork's Write subsystem (separate path-resolution layer)

   9 findings (F1–F9) captured durably in
   `docs/research/private/phase3.5-smoke/findings.md` (gitignored
   working note). F7 (**Auto mode requires Sonnet-tier model** — Mode
   dropdown greys out "Auto" with label "Not available for the selected
   model" when Haiku 4.5 is selected; becomes selectable on Sonnet 4.6)
   is candidate for promotion to `docs/lessons/` (general Anthropic
   Claude Code primitive behavior, not in any doc surveyed). Observation
   continues 24-48h; daily check ~2026-05-26 +07 → GO / NO-GO decision.
   GO opens PLAN-0010 (Phase 3.5 scheduled-task autonomy loop) + Step
   1b contract design + Phase 3 execution. NO-GO pivots to MCP
   `vero-bridge` roadmap (Phase 3 still proceeds; no scheduled-task
   layer).

**Prior — PLAN-0009 (Phase 3 — subagent topology) RATIFIED + Ready
for execution + COMMITTED.** Cowork drafted under interim ADR-009 D1
phasing; Cray adjudicated all 4 OQs (OQ-1…OQ-4) on 2026-05-25 (WebFetch
for Explore; no new ADR — execute ADR-013 D1; subagent identity folds
with ADR-013 OQ-3 in Step 1; PLAN status vocabulary). Code fact-pack /
R2 review clean across 9 citations (0009 next free; ADR-013 D1/OQ-1/OQ-3
quoted verbatim; PLAN-0008 carry-overs accurate; PLAN template structure
intact; Cray verification-rigor directive present); flipped Status Draft
→ Ready for execution; committed `d10073e` on `feat/plan0009-subagent-topology`
(single-doc, worktree-OFF per CLAUDE.md §11). Phase 3 execution gated on
PR merge.

### Cowork → Code dispatch handoff dog-fooded (K-1 / ADR-009 D3 substitute)

`.claude/handoffs/session-10/2026-05-25-1240-cowork-plan0009-review-dispatch.md`
`validate_handoff.py` clean (9 required fields; actor=cowork / phase=dispatch
/ status=READY / suffix=dispatch; ISO-8601 +07:00; filename matches
`_FILENAME_RE`). Cowork could not run the validator (K-1 UNC-bash refusal);
Code ran post-receive — the standing D3 substitute. Gitignored working
note per CLAUDE.md §11 (the `.claude/handoffs/.gitignore` `*` rule).

### Two reconciliation findings folded into project memory

1. **`.claude/` readability vs PLAN-0008 OQ-D (research-note §6).** Cowork
   successfully Read `.claude/autonomy-triggers.md` this session,
   contradicting PLAN-0008 OQ-D's "sandboxes cannot read
   `.claude/handoffs/`" wording. Reconciled: **K-2 is a write block, NOT a
   read block** (Reads are proxied through the Windows Desktop client).
   The load-bearing forcing fact for OQ-D's deferral remains **K-1**
   (Cowork cannot run `validate_handoff.py` or any bash via UNC), which
   is unchanged. OQ-D's substantive deferral stands; only its prose
   mildly conflates the two axes. **No archived-PLAN amendment** —
   surfaced here for project memory + forward-looking guidance ("keep
   any cross-tier inbox outside `.claude/`" still applies, as
   belt-and-suspenders).
2. **Working-tree divergence (research-note §6.1; reproduced live this
   session).** A Code session running from a git worktree sees **neither**
   uncommitted new files in main tree (`docs/plans/0009-subagent-topology.md`
   initial draft) **nor** gitignored paths (`docs/research/private/`). Both
   are present in `~/work/vero-lite` (main checkout). This is **not**
   K-1/K-2 — it is a `git worktree` checkout-resolution mismatch
   (worktrees check out tracked-only files; both uncommitted new files
   and gitignored paths are filtered out by definition). **Design
   implication** for any future producer/consumer loop (relevant to
   Phase 3.5 if approved): inbox must be a tracked path consumed from
   the main tree, OR committed before hand-off. Folds neatly with the
   PLAN-0009 Step 1 worktree-path normalization carry-over.

### CLAUDE_TIER / session-identity unification (PLAN-0009 OQ-1 ↔ ADR-013 OQ-3)

Confirmed correctly folded in PLAN-0009 Step 1. One mechanism must
distinguish **3 identity cases**:

| Identity | G5 commit authority | Tool/path scope |
|---|---|---|
| Main interactive Code agent | ✅ may commit | full main-agent allowlist |
| Plan / Explore subagent | ❌ must NOT commit | Plan: `docs/{adr,plans}/`; Explore: read-only + WebFetch |
| Scheduled Local Code session (Phase 3.5 — HELD) | ✅ may commit (if approved) | same as main agent |

Existing prose mechanism = `CLAUDE_TIER=code` env-var (this commit used
it); ADR-013 D2 promotes it to deterministic via the G5 hook. PLAN-0009
Step 1's design will wire all three identity cases through one
mechanism — the load-bearing deliverable for AC-3 + AC-6.

### Phase 3.5 — SURFACED, HELD

Research-note §7.5 surfaces a "**Phase 3.5: local scheduled-task poller
experiment**" — Cowork Local scheduled task + Code Local Desktop task
over a repo inbox; appears to deliver most of the auto-handoff value at
lower cost/risk than the MCP `vero-bridge` bridge. Operator constraints
(machine-left-on acceptable, 1h cadence acceptable, avoid cloud)
strongly favor this. **HOLD per Cray** — option SURFACED, not decided.
PLAN-0009 Step 6 + Verification verification-rigor directive
(exhaustive case-coverage matrix; "confident it works" not "tests
pass"; mirrors PLAN-0007 G5 16-case precedent) explicitly binds Phase
3.5 if ratified.

### Prior — PLAN-0008 Phase 2 CORROBORATED via 2 independent AC-1 live runs

Phase 2 was already AUDITED + closed (Step 8 + AC-1 verified amendment
PR #19 merged); a follow-on Auto mode run gives a second independent
data point that strengthens AC-1 evidence + adds layer-orthogonality
confirmation:

### AC-1 evidence corpus — 2 independent runs

| Aspect | Run 1 (Accept edits, main repo, 2026-05-25 ~03:00) | **Run 2 (Auto mode, worktree, 2026-05-25 00:30–00:32)** |
|--------|----------------------------------------------------|---------------------------------------------------------|
| Task | "ตรวจ ruff + mypy ทั้ง project, แก้, commit" | **"สร้าง docs/CHANGELOG.md สรุป Phase 2 PRs #9-#17, commit บน branch ใหม่, ไม่ต้อง push"** |
| Cray paste | Single, then unattended | Single, then unattended |
| Auto-continues observed | ≥ 5 | **≥ 4** (Read STATUS → Write CHANGELOG → Write commit-msg → git commit → summary) |
| Per-tool permission prompts | 1 (UNC path file edit) | **0** (Auto mode skipped them all) |
| Telegram pings (cap / L1-4) | 0 | **0** |
| Terminal pause point | `git push` boundary (memory-aware classifier pause) | **commit done — followed explicit "ไม่ต้อง push"** (no over-step) |
| Commit produced | `8fef3a5` (mypy cleanup, side effect) | **`6dc808c` on `chore/phase2-changelog`** (the CHANGELOG) |

### Layer orthogonality CONFIRMED in production

Mode (PreToolUse permission gate, Anthropic harness layer) and PLAN-
0008 (Stop continuation classifier, our layer) operate independently:

- **Switching Mode = Auto eliminates per-tool prompts** (1 → 0) without
  changing Stop-continuation decisions (≥ 5 → ≥ 4 auto-continues both
  satisfy AC-1 spec).
- **PLAN-0008 classifier honors explicit user instructions** ("ไม่ต้อง
  push" → agent stopped at commit, didn't attempt push despite Auto
  mode permitting it).
- **No false-positive triggers in either run** — 0 Telegram pings
  across both = the L1–L4 loop-detect + chain-cap fail-safe correctly
  stayed silent on routine multi-step work.

### Minor finding for PLAN-0009 carry-over

Run 2's L1 counter key showed `.claude/worktrees/busy-bose-eedc8f/docs/CHANGELOG.md`
instead of the cleaner `docs/CHANGELOG.md`. The `_loop_counter._normalize_file_path()`
strips the main repo prefix but does not collapse the worktree path
suffix — works correctly within a worktree session but creates ugly
keys that don't share state across worktrees. Already a non-blocker
(per-session isolation is by design). Carry-over as a small refinement
for PLAN-0009 if the schema is touched anyway.

**Prior — PLAN-0008 Phase 2 FULLY AUDITED (all 4 ACs verified).**
AC-1 was the only PENDING AC after Step 8 merge (`79fe373`); Cray
ran a Cray-supervised live session 2026-05-25 and the autonomy layer
exercised the auto-continue path as designed.

**AC-1 evidence (2026-05-25):**

| Aspect | Observation |
|--------|-------------|
| Task given | `"ตรวจ ruff + mypy ทั้ง project, แก้ warning ถ้ามี, commit"` (Cray pasted once, no further input) |
| Auto-continues observed | **≥ 5 consecutive** (initial scan → file inspection → plan → branch creation → 5 file fixes → re-verify → tests → commit, all without Cray paste between turns) |
| Terminal pause | Agent paused at the `git push` boundary asking Cray for permission ("ต้องการให้ push + เปิด PR ต่อเลยมั้ยครับ?") — classifier correctly identified push as a state change outside the worktree per the existing `feedback_state_change_outside_worktree.md` auto-memory pattern |
| Telegram pings | **0** — no `cap_reached`, no L1–L4 trigger (no false-positives, depth stayed under cap=8) |
| Chain-state at end | `stop-chain.json` `depth: 0` (consistent with the terminal pause resetting chain) |
| Side effect | The session surfaced **21 project-wide mypy errors** in `tools/` + `tests/` (outside the pre-commit gate scope `^(services|verticals|\.claude/hooks)/`) and shipped a cleanup commit `8fef3a5` on branch `chore/mypy-tools-tests-clean` — PR #18 |

**Implications:**
1. **AC-1 VERIFIED.** Phase 2 acceptance criteria all green
   (AC-1/AC-2/AC-3/AC-4).
2. **Classifier conservatism in production: confirmed.** The agent
   paused at `git push` despite this being a routine action *if it
   were inside the worktree*, because the existing feedback memory
   correctly classifies it as "state change outside the worktree".
   Spurious pauses > spurious proceeds — exactly the bias OQ-B
   adjudicated for.
3. **Cost.** A ~5-turn auto-continue session = ~5 Sonnet classifier
   calls ≈ $0.005 (consistent with the Step 5 + Step 5b cost
   baselines). The cost-telemetry pre-filter (OQ-F) remains
   unnecessary in Phase 2.

Closeout handoff `.claude/handoffs/session-10/2026-05-25-0130-code-plan0008-phase2-closeout.md`
§1 (local working note per CLAUDE.md §11) updated to reflect AC-1
VERIFIED. PLAN-0008 already in `docs/plans/done/` per Step 8.

**Prior — PLAN-0008 Phase 2 COMPLETE.** Step 7 MERGED via [PR #16](https://github.com/CrayJThiemsert/vero-lite/pull/16)
(`9100e65`). Step 8 (closeout + AC matrix + PLAN move to `done/`)
IN-FLIGHT on branch `feat/plan0008-step8-closeout`. The 8-step Phase 2
arc (Steps 1, 2, 3, 4, 5, 5b, 6, 7, 8) leaves the harness autonomy
layer fully wired and tested:

- **Probabilistic / classifier-mediated**: `Stop` continuation loop
  + Sonnet pause/proceed classifier + stateful L1–L4 loop-detection
  + cross-env API key fallback (Step 5b)
- **Deterministic floor (Phase 1) preserved**: G5 git-deny, H1
  handoff-validator, C4 research-path-deny — all reachable and
  reflexively exercised every commit in this session
- **Suite end-state**: 216 (Phase 1) → **389 pass / 6 skip** (Phase 2,
  +173 across 5 new test files incl. 17 E2E integration scenarios
  driving real subprocess hook invocations against a local mock HTTP
  Sonnet server)

**AC matrix verification (full detail in closeout handoff):**

| AC | Status | Evidence |
|----|--------|----------|
| AC-1 (Stop self-continues ≥ 3 auto-continuations) | **PENDING live** | Mechanics verified by Step 7 integration tests + chain-depth progression; live observation deferred — requires unattended Cray-supervised session (interactive sessions cannot exercise the auto-continue path) |
| AC-2 (classifier pauses on registry matches, no false-positives on routine) | **VERIFIED 2026-05-24** | Step 5 live conservatism proof 5/5 scenarios (G1/G2/C2 paused with correct `matched_rows` + 1 routine proceed); $0.005 total cost; mocked harness in Step 7 confirms wire integrity |
| AC-3 (L1–L4 fire on trigger + reset on progress) | **VERIFIED 2026-05-25** | Step 7 + Step 8 integration tests cover all 4 patterns + Cray-E.4 Telegram payload assertion; L3 auto-reset deferred per PLAN §Step 4 closeout (multi-tool observation needs schema evolution → PLAN-0009) |
| AC-4 (Phase 1 + C4 deterministic regression-free) | **VERIFIED 2026-05-25** | pytest 389/6 incl. test_pretooluse_git_deny.py (16 bypass-immune cases), test_posttooluse_validate_handoff.py, test_pretooluse_research_path_deny.py (20 cases) all green; in-session production fires (L1-on-self in PR #15 + H1-on-self in this PR's closeout handoff frontmatter) prove the deterministic + classifier-mediated layer is reachable from real agent activity |

**Closeout handoff** at `.claude/handoffs/session-10/2026-05-25-0130-code-plan0008-phase2-closeout.md`
(local working note per CLAUDE.md §11 — `.claude/handoffs/.gitignore`
keeps these out of the repo). Covers all 4 ACs, cost telemetry
baseline, deferred items carry-over (auto-handoff Code→Cowork, L3
auto-reset, PreToolUse classifier dispatch — all to PLAN-0009),
operational findings (Desktop env strip, L1-on-self, cross-env key
file setup), and Phase 3 entry conditions.

**PLAN move:** `docs/plans/0008-...md` → `docs/plans/done/0008-...md`
(`git mv`). Archived alongside PLAN-003 / PLAN-0005 / PLAN-004 / PLAN-0006
/ PLAN-0007.

**Next: PLAN-0009 (Phase 3 — subagent topology, ADR-013 D1 phased
end-state) entry conditions met.** Recommended outline in closeout
§6: subagent contract design → Explore subagent → Plan subagent →
main-agent dispatch protocol → auto-handoff Code→subagent → live
AC. Cowork-drafted under interim ADR-009 D1 phasing per Cray cadence.

**Prior — PLAN-0008 Step 5b MERGED + Step 7 (Phase 2 integration
tests + mypy hook coverage extension) IN-FLIGHT.** Step 5b
(`_sonnet_classifier.py` config-file fallback) merged via [PR #15](https://github.com/CrayJThiemsert/vero-lite/pull/15)
(`3d4f98b`). Cross-env key file setup completed: Code copied
`~/.claude/.anthropic_api_key` to `C:\Users\crayj\.claude\.anthropic_api_key`
with NTFS ACL `crayj:FullControl` only (SYSTEM + Administrators removed
— stricter than chmod 600). Both WSL Python (`/home/crayj/.claude/...`)
and Windows Python (`C:\Users\crayj\.claude\...`) verified to resolve
the key from their respective `Path.home() / ".claude" / ".anthropic_api_key"`.
Hook firing path (Windows-Python) and pytest path (WSL-Python) both
unblocked for live Sonnet calls.

**Step 7 on branch `feat/plan0008-step7-integration-tests`.** Two
deliverables:

1. **`tests/handoffs/test_phase2_integration.py`** (15 E2E scenarios)
   driving real subprocess invocations of `pretooluse_loop_detect.py`
   + `posttooluse_progress_observer.py` + `stop_continuation.py` with
   a local mock HTTP Sonnet server (ephemeral 127.0.0.1 port via
   `socketserver.TCPServer` + threading daemon; `$CLAUDE_SONNET_API_URL`
   override; no live network). Coverage: Stop→proceed→`block` decision
   with reason propagation; Stop→pause→no block + chain reset;
   classifier fail-closed when env+file missing; `stop_hook_active`
   re-entry guard (mock server records zero requests proves
   short-circuit before classifier dispatch); chain-cap fail-safe
   (Telegram `cap_reached` payload + chain reset, classifier
   short-circuited); observer→state→PreToolUse deny on L1 + L4 at
   threshold 6; L4 reset on success; L2 inline Telegram on
   pytest-fail threshold; L1 turn-boundary survive when target in
   `turn_touched` vs reset when not; re-entry guard preserves state;
   chain depth progression proceed→proceed→pause = 0→1→2→0;
   Phase 1 regression test files present (AC-4 scaffold). All 15
   green.
2. **Pre-commit `mypy` glob extended** from `^(services|verticals)/`
   to `^(services|verticals|\.claude/hooks)/` — closes the Step 1
   closeout follow-on. All 9 hook files pass `mypy --strict` cleanly;
   `pre-commit run mypy --all-files` verified.

Suite totals: **372 → 387 pass / 6 skip** (+15 integration). `ruff` +
`mypy --strict` + `detect-secrets` clean. Per-test isolation via
`tmp_path` for state file, classifier fallback path, telegram capture,
chain file — no developer's real `~/.claude/.anthropic_api_key` can
leak the classifier into a live API call.

AC progress: **AC-3 (loop-detection fires + resets) demonstrated
end-to-end** for the first time (previously only per-hook unit cases).
AC-1 happy-path proceed + chain progression demonstrated. AC-2
governance-match harness is ready (canned `pause` + `matched_rows`
mock); formalization of matched_rows→Telegram payload held for **Step
8 live AC**. AC-4 scaffolded via discoverability test; full
bypass-immunity re-run held for Step 8.

**Prior — PLAN-0008 Step 5b (Anthropic API key config-file fallback)
MERGED.** Step 6 (Wave 2 completion —
`autonomy-triggers.md` row flips + PLAN closeout amendment) merged via
[PR #14](https://github.com/CrayJThiemsert/vero-lite/pull/14)
(`626ab23`). Immediately after, env-propagation diagnostic on the new
session surfaced a **Claude Desktop platform behavior**: on Windows
the Desktop wrapper launches `claude.exe` with `ANTHROPIC_API_KEY=""`
(empty, not unset) as deliberate OAuth-subscription / API-key billing
isolation. WSLENV propagation cannot defeat this — User-scope env is
overwritten before the CLI spawn, even after full computer restart.
The Step 5 live conservatism proof (2026-05-24) only passed because
Cray ran the live pytest from a WSL terminal **outside** the Desktop
process tree; any in-session hook invocation of `_sonnet_classifier.py`
would have fail-closed paused on every Stop event due to the empty key.

**Step 5b fix on branch `feat/plan0008-step5b-classifier-config-fallback`.**
`_sonnet_classifier.py::_resolve_api_key()` extended with a chain
fallback: `$ANTHROPIC_API_KEY` (truthy after strip) →
`~/.claude/.anthropic_api_key` (override via
`$CLAUDE_ANTHROPIC_KEY_FILE`; POSIX requires chmod 600; first non-empty
line, whitespace stripped) → fail-closed pause. **+10 unit tests** added
(`test_sonnet_classifier.py` 17 → 27; full suite 362 → 372 pass / 6
skip), all green. autouse `isolated_key_file` fixture prevents tests
from picking up Cray's real key file. `.gitignore` extended with
`.claude/.anthropic_api_key` (belt-and-suspenders; canonical location
is `~/.claude/.anthropic_api_key` outside repo). PLAN-0008 §Step 5
gains the Step 5b amendment box; auto-memory finding saved at
`project_claude_desktop_strips_anthropic_api_key.md` for future
sessions.

**Live verification PASSED inside this Claude Code session
(2026-05-24).** Direct invocation of `sc.classify()` from a Bash tool
call: env `ANTHROPIC_API_KEY=""` (Desktop strip confirmed) →
`_resolve_api_key()` returned `(sk-ant..., file:/home/crayj/.claude/.anthropic_api_key)`
→ real Sonnet round-trip 3.04s → `{decision: "proceed", matched_rows:
[], reason: "..test/verification Stop event with no pending tool
actions.."}`. The same call pre-Step-5b would have returned fail-closed
pause. Proof complete that the fix defeats the Desktop strip.

**Cross-env caveat.** Hooks fire under Windows Python (`Path.home() =
C:\Users\crayj\`); pytest invoked via the Bash tool runs WSL Python
(`Path.home() = /home/crayj/`). Cray must either (a) maintain a copy
of the key file at both paths, (b) symlink one to the other, or (c)
set `$CLAUDE_ANTHROPIC_KEY_FILE` (this var is **not** Desktop-stripped
— verified via `CLAUDE_TIER` + `TELEGRAM_*` propagating intact) to a
single canonical location via WSLENV. Recommendation documented in
the Step 5b PR body.

**Prior — PLAN-0008 Step 6 (Wave 2 completion — autonomy-triggers row
flips) MERGED.** PR #14 landed on `main` as `626ab23` (single `docs(claude)`
commit `aa64d19` + merge commit). Docs-only flip of registry row labels
in `.claude/autonomy-triggers.md` from placeholder / "Phase 2 spec"
wording to **LIVE** with concrete hook attribution: G1/G2/G3/G4 +
C1/C2/C3 → `_sonnet_classifier.py`; L1–L4 → three-hook attribution
(`pretooluse_loop_detect.py` gate + `posttooluse_progress_observer.py`
writer + `stop_continuation.py` reset); "How the classifier reads this
file" §flipped from spec to LIVE with conservatism-probe evidence;
status banner + footer date updated. PLAN-0008 §Step 6 gained the
"Step 6 closeout — Wave 2 completion" amendment with PR #11/#12/#13
lineage. `.claude/settings.json` `_comment` corrected (stub removal
happened in PR #13, not Step 6). 362 pass / 6 skip baseline preserved
(docs-only).

**Prior — PLAN-0008 Step 5 (Sonnet classifier helper + stub swap)
MERGED + LIVE conservatism proof PASSED.** PR #13 landed on `main` as
`3407ae6` (single `feat(claude)` commit `ceebc1a` + merge commit).
4-piece bundle: (1) new `.claude/hooks/_sonnet_classifier.py` (~225
lines) — stdlib urllib + Anthropic Messages API + JSON-in-text +
retry-once + 7 fail-closed pause paths; pin `claude-sonnet-4-6`
(OQ-B); reads `.claude/autonomy-triggers.md` verbatim. Stdlib-only
deviation from PLAN's "SDK preferred" rationalized (avoids C2
chicken-and-egg + matches Phase 1 hooks idiom; retry + markdown-fence
extractor + fail-closed mitigate the structured-output gap). (2)
`stop_continuation.py` amendment — `_classifier_stub()` removed;
`_classify()` wrapper with defensive double-fallback (ImportError +
final catch-all). (3) `tests/handoffs/test_sonnet_classifier.py`
(NEW, 17 cases incl 1 live opt-in via `RUN_LIVE_SONNET_TESTS=1` per
OQ-G). (4) `test_stop_continuation.py` fixture pops
`ANTHROPIC_API_KEY` for determinism. **LIVE verification (Cray
2026-05-24, 20:00–20:25):** opt-in smoke + 4-scenario conservatism
proof passed 5/5 — bare Stop → proceed; G1 (edit Accepted ADR) →
pause with rows `['G1']`; G2 (consume ADR-014) → pause with `['G2']`;
C2 (add `anthropic` dep) → pause with `['C2']`; routine work
(pytest + variable rename) → proceed. Sonnet's plain-English reasons
are informative and accurate. Total live cost ~$0.005. **WSLENV
permanently extended** with `ANTHROPIC_API_KEY/u` via PowerShell
`[Environment]::SetEnvironmentVariable(..., "User")` so fresh Claude
Code sessions inherit the key without manual workaround. `pytest`
362 pass / 6 skip (Step 4 baseline 346/5 → 362/6); `ruff` +
`mypy --strict` + `detect-secrets` clean.

**Session handoff to new Code session.** This session has accumulated
considerable context across Phase 2 Steps 1–5 (PR #8/9/10/11/12/13)
plus the L1/L4 ELI-CTO + Wave 1/2 design + classifier conservatism
validation. Cray-directed handoff to a fresh Code session for **Step
6 (Wave 2 completion)** to preserve context-window headroom and
double as a live verification of the permanent WSLENV propagation
from a clean process tree. Handoff brief:
`.claude/handoffs/session-10/2026-05-24-2030-code-step5-merged-step6-kickoff.md`.

**Prior — PLAN-0008 Step 4 (Stop hook + L1 turn-boundary reset)
MERGED with expanded scope.** PR #12 landed on `main` as `b09bf39`
(single `feat(claude)` commit `010ae1b` + merge commit). 5-piece
bundle per Cray-ratified scope expansion: (1) new
`.claude/hooks/stop_continuation.py` (~200 lines) — Stop hook with
`stop_hook_active` re-entry guard + **L1 turn-boundary reset** (reads
`turn_touched`, resets untouched L1 counters, clears marker) + chain
depth tracking in `.claude/state/stop-chain.json` + cap-hit policy
(OQ-E option b: pause + Telegram `cap_reached` + reset chain) +
classifier dispatch via `_classifier_stub` (pause-by-default until
Step 5 wires real Sonnet helper). (2) `_loop_counter.py` amendment —
`turn_touched: list[str]` field with JSON round-trip + back-compat for
old state files; 3 new helpers (`record_turn_touched`,
`reset_untouched_l1`, `clear_turn_touched`). (3)
`posttooluse_progress_observer.py` amendment — `_handle_write_or_edit`
records turn_touched on every Write/Edit so Stop hook has the touched
signal. (4) `.claude/settings.json` — **early Wave-2-partial wire**
for Stop hook (required for L1 reset to fire; classifier stub keeps
the wire safe to land before Step 5). (5) 26 new tests (18
`test_stop_continuation.py` + 7 `turn_touched` primitives in
`test_loop_counter_state.py` + 1 observer amendment). **🔴 L1 reset
gap CLOSED** — Cray's iterative STATUS-editing workflow no longer at
false-positive risk. `pytest` 346 pass / 5 skip (Step 3 baseline 320
→ 346); `ruff` + `mypy --strict` + `detect-secrets` clean. **Next:
Step 5** — replace `_classifier_stub` with real Sonnet helper
(stdlib urllib + Anthropic Messages API, fail-closed pause).

**Prior — PLAN-0008 Step 3 (PostToolUse progress observer + Wave 1
wire + PLAN amendment) MERGED.** PR #11 landed on `main` as `632a22c`
(single `feat(claude)` commit `1c2a7b6` + merge commit). 4 things
bundled per Option C + documentation option (3): (1) new
`.claude/hooks/posttooluse_progress_observer.py` (~260 lines,
refactored into `_apply_l2`/`_apply_l3`/`_apply_l4` helpers) — the
writer side that feeds the loop-counter from `Bash`/`Write`/`Edit`
outcomes; never blocks; L2/L3 fire Telegram **inline on trigger**
(PreToolUse can't predict nodeid/signature pre-execution) while L1/L4
let Step 2's PreToolUse gate fire on next attempt; defensive Bash
exit-code detection (`interrupted` → explicit `exit_code` →
`is_error` → stderr-with-error-marker → heuristic) so ambiguous
outcomes are no-op (not spurious increment). (2) 31 new tests with
Telegram-stub fixture capturing real Cray-E.4 payload + 2 lock-in
tests for L1/L4 asymmetry. (3) **Wave 1 wire** in
`.claude/settings.json` — registers `pretooluse_loop_detect.py`
alongside `pretooluse_git_deny.py` (Bash) and
`pretooluse_research_path_deny.py` (Write|Edit); registers
`posttooluse_progress_observer.py` alongside
`posttooluse_validate_handoff.py` (Write|Edit) + new PostToolUse Bash
matcher. (4) PLAN-0008 amendment boxes in §Step 3 + §Step 6 codifying
the Wave 1/2 split. `pytest` 320 pass / 5 skip (Step 2 baseline 289 →
320); `ruff` + `mypy --strict` + `detect-secrets` clean.

**L1/L4 asymmetry ELI-CTO + Step 4 prioritization (Cray 2026-05-24).**
During PR #11 review Cray asked for an ELI-CTO breakdown of the L1/L4
asymmetry (Step 3 increments → Step 2 gates on next attempt vs L2/L3
fire inline). Code's analysis: 🟢 the off-by-one + abandoned-loop +
spec-matching are by-design and not problems; 🟡 the L2/L3 vs L1/L4
fire timing is a minor UX inconsistency (deferrable to Step 8); 🔴
**L1 missing reset until Step 4 lands is a real op risk** — Cray's
actual iterative workflow on STATUS.md (already 4 of 6 edits used in
this session before PR #11 merge) would false-positive-deny without
turn-boundary reset. Cray ratified the recommendation: merge PR #11 +
**prioritize Step 4** with proper L1 reset implementation (not just a
Stop-hook stub). Step 4 scope expansion under surface — see
In-Flight Discussions.

**Prior — PLAN-0008 Step 2 (PreToolUse loop-detect hook) MERGED.**
PR #10 landed on `main` as `9494f93` (single `feat(claude)` commit
`ad2c047` + merge commit). New
`.claude/hooks/pretooluse_loop_detect.py` (~185 lines) reads the Step 1
state file and gates on L1 (`Write`/`Edit` with same `file_path` ≥ 6
times) and L4 (`Bash` with same tokenized command ≥ 6 accumulated
non-zero exits from Step 3). On trigger fires `tools/notify/telegram.sh`
with the Cray-E.4 payload contract `{loop_type, target,
last_6_actions}` and emits a `deny` PreToolUse decision asking Cray
to intervene. Env-var overrides (`CLAUDE_LOOP_COUNTER_PATH`,
`CLAUDE_TELEGRAM_SCRIPT`) read from hook process env, not
`tool_input` → spoof-immune. **L2** (test_fail) and **L3**
(error_signature) explicitly NOT enforced at PreToolUse (locked by 2
test cases) — they are inherently post-execution signals and will be
fired by Step 3 inline when their counters trigger. 24 new tests
(`tests/handoffs/test_pretooluse_loop_detect.py`) incl Telegram-stub
fixture that captures the real payload + "deny still fires when
Telegram script missing"; `pytest` 289 pass / 5 skip (Step 1 baseline
265 → 289); `ruff` + `mypy --strict` + `detect-secrets` clean.

**Wave 1/2 settings.json activation decision (Option C — Cray
2026-05-24).** PLAN-0008 §"Step 6" originally said "Register Steps 2–5
hooks in `.claude/settings.json`" as one batch. Code surfaced 3
alternatives during Step 2 PR (#10): A wire per step; B wire all at
Step 6 (PLAN literal); **C phased — Wave 1 wires Step 2 + Step 3
together when Step 3 lands, Wave 2 wires Step 4 + Step 5 at Step 6**.
Cray ratified C. Rationale: (1) L1/L4 loop-detect is standalone
deployable — does not depend on Stop loop + Sonnet classifier;
artificial coupling delays smoke testing. (2) Real Claude Code event
payload (vs test-crafted JSON) may have edge cases unit tests miss;
early smoke catches integration bugs before Step 4–5 development
piles on. (3) Match Phase 1 phased pattern (3 hooks landed
incrementally with smoke each). Cost: 2 `settings.json` edits across
Wave 1 + Wave 2 instead of 1 — minor append/scatter, not load-bearing.
**Step 3 PR will bundle**: writer hook + tests + Wave 1 wire +
PLAN-0008 amendment (note Wave 1/2 split in §Step 3 + §Step 6 — per
documentation option (3) Cray-approved 2026-05-24) — one commit per
the Option C ratification.

**Next: Step 3** — `.claude/hooks/posttooluse_progress_observer.py`
(writer + L2/L3 inline Telegram firing) + Wave 1 wire +
PLAN amendment, on branch `feat/plan0008-step3-posttooluse-progress-observer`.

**Prior — PLAN-0008 Step 1 (loop-counter state module) MERGED.**
PR #9 landed on `main` as `2b303a0` (single `feat(claude)` commit
`e20a6f3` + merge commit). New `.claude/hooks/_loop_counter.py` (~340
lines, stdlib-only) ships the Phase 2 state primitives: `LoopType`
enum (L1–L4 mapping to `.claude/autonomy-triggers.md`),
`LoopCounter`/`CounterEntry`/`ActionRecord` dataclasses with explicit
JSON round-trip, atomic `load_counter`/`save_counter` (tmpfile +
`os.replace`, tolerant of missing/empty/malformed/wrong-root files),
4 normalization helpers (file path reusing C4 hook idiom for
Windows-UNC, pytest nodeid stripping `[param]` suffix, error signature
stripping 6 volatile patterns, bash command tokenization), session-ID
resolution per **OQ-A** (`$CLAUDE_SESSION_ID` → `pid-<PID>` →
`uuid-<UUID>` fallback chain), counter ops (`increment` with
`last_6_actions` ring buffer per Cray E.4 payload contract, `reset`
removes entry, `get_count`, `has_triggered` against
`LOOP_TRIGGER_THRESHOLD=6`). 49 new tests
(`tests/handoffs/test_loop_counter_state.py`) incl concurrent-write
race (writer + reader threads, no partial reads); `pytest` 265 pass /
5 skip (Phase 1+C4 baseline 216 → 265); `ruff` + `mypy --strict` +
`detect-secrets` clean. **Next: Step 2** —
`.claude/hooks/pretooluse_loop_detect.py` (read state, gate on L1/L4
≥6, fire telegram, deny) on branch
`feat/plan0008-step2-pretooluse-loop-detect`.

**Prior — PLAN-0008 (Phase 2 harness autonomy layer) DRAFTED +
MERGED.** PR #8 landed on `main` as `ec5e2ae` (3 commits: draft
`b53763d` + OQ resolutions `5a34ab0` + merge). Phase 2 scope = three
coupled pieces layering the probabilistic / classifier-mediated engine
on top of Phase 1's deterministic hooks: (1) **`Stop` continuation
loop** with `stop_hook_active` re-entry guard +
`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP=8` chain cap; (2) **Sonnet
pause/proceed classifier** reading `.claude/autonomy-triggers.md`
verbatim (fail-closed, model pin `claude-sonnet-4-6`); (3) **stateful
loop-detection L1–L4** via `.claude/state/loop-counter.json`
(gitignored; payload `{loop_type, target, last_6_actions}` per ADR-013
/ Cray E.4). 4 ACs incl **AC-4 Phase 1 regression-free** (16-case
bypass-immune commit-deny + handoff-validator + C4 research-path-deny
all stay green). All 7 OQs (A–G) adjudicated by Cray on 2026-05-24:
A (session-ID = `$CLAUDE_SESSION_ID` → PID → UUID fallback), B
(Sonnet pin), C (registry path-reference, not inline), **D
(auto-handoff DEFERRED to PLAN-0009** — K-1/K-2 forcing fact still
blocks Cowork read-side so auto-draft does not reduce the Cray-paste
relay; Plan subagent = right author per ADR-013 D1; surface bloat),
E (BLOCK_CAP hit → pause + Telegram `"cap reached"`), F (no Phase 2
pre-filter; cost telemetry is the trigger), G (CI mocks Sonnet +
opt-in `RUN_LIVE_SONNET_TESTS=1`). Status: **Ready for execution**.
**Next: Step 1** — `.claude/state/` directory + `loop-counter.json`
schema + `.gitignore` extension + atomic-write tests, on branch
`feat/plan0008-step1-state-design`. Cowork-drafted under interim
ADR-009 D1 (ADR-013 D1 phasing); Code committed per ADR-009 D2.

**Prior — Research-path enforcement (C4 hook) MERGED.** PR #7
landed on `main` as `da4f91d` (single `feat(claude)` commit `21f0f7a`
+ merge commit). Third deterministic Phase-1 row in `.claude/autonomy-triggers.md`
alongside G5 (`pretooluse_git_deny.py`) and H1 (`posttooluse_validate_handoff.py`):
`.claude/hooks/pretooluse_research_path_deny.py` blocks `Write`/`Edit`
under `docs/research/` outside `docs/research/private/**`. Motivation
= N=2 violations of the documented rule (`cowork_tab_instructions.md`
line 192 + `.gitignore` lines 49-51) in 8 days — Lesson #5 §10.5
(2026-05-15 audit baseline, `docs/strategy/public/` drop) +
2026-05-23 `chat_harness_extension_points_analyzed.md` (detected
+ corrected during PLAN-0007 post-merge cleanup). Applies ADR-013 D2
precedent: when documentation alone fails twice, promote to
deterministic hook reinforcement. 20 new unit tests (allow private/
+ strategy/, deny public/ + bare research/ + arbitrary subdirs, path
normalization for Windows UNC both directions, edge cases for non-Write
tools + malformed stdin); `pytest` 216 pass / 5 skip; `ruff` + `mypy`
+ `detect-secrets` clean. Cowork research workflow unchanged for the
happy path (private/ writes allowed); only the off-policy writes are
blocked at the hook layer.

**Prior — Harness autonomy layer (ADR-013 + PLAN-0007) Phase 1
MERGED.** PR #6 landed on `main` as `b2ea9b8` (9 commits: 6 Phase A
governance + 3 Phase B execution). The `.claude/` autonomy layer is
live: deterministic PreToolUse deny on `git commit|push|merge` from
non-Code sessions (CLAUDE_TIER env marker, bypass-immune across 16
test cases incl `bash -c`, backtick, `git -C`, inline env spoof);
Notification hook → `tools/notify/telegram.sh` (env-var-only Telegram
bridge with graceful no-op when unset, live ping verified end-to-end
by Cray); PostToolUse handoff frontmatter auto-validator (Write|Edit
on `.claude/handoffs/**`, blocks on hard error); `.claude/autonomy-triggers.md`
registry (G1–G5 governance, C1–C3 config/dep/wording, H1 handoff,
L1–L4 loop-detect rows flagged "Phase 2 enforcement"). 28 new unit
tests; `pytest` 196 pass / 5 skip; `ruff` + `mypy` + `detect-secrets`
clean.

**OQ-3 resolution (Code-decided, ADR-013).** Session-identity signal =
env var `CLAUDE_TIER=code`, set by Cray on the launching shell.
Bypass-immune against `permission_mode=bypassPermissions` (hook
decisions run regardless of permission_mode) and against inline
command spoofing (hook reads its own process env, not the tool_input
string). Windows-host setup: `setx CLAUDE_TIER code` + `setx WSLENV
CLAUDE_TIER/u:TELEGRAM_BOT_TOKEN/u:TELEGRAM_CHAT_ID/u`. Token rotated
on 2026-05-23 after one-time screenshot leak in chat (Cray-handled
via `@BotFather`).

**Next:** PLAN-0008+ for Phase 2 entry conditions reached
(`Stop` continuation loop + Sonnet pause/proceed classifier reading
`.claude/autonomy-triggers.md` + stateful loop-detection state file +
subagent topology + MCP `vero-bridge` transport). Drafting cadence
per Cray; the deterministic safety pieces (commit deny, handoff
auto-validation) and the AFK channel are now load-bearing — Phase 2
adds the probabilistic / classifier-mediated layer on top.

---

**Prior — PLAN-0006 (LLM reasoning-hook execution) MERGED.** The brain
swap is done: `services/engine/recommender.py::recommend()` is now LLM-backed
(ADR-010 D5) — **merged to `main` via PR #5 (`68053fe`)**, 12 commits incl.
ADR-001 Amendment 1. Steps 0-8 of the Phase-1 kickoff dispatch all landed:
`ruff` + `mypy --strict` clean, **173 passed / 0 skipped** (with live
Postgres), coverage **94.56%** (new `services/engine/llm/` modules 92-100%).

**CHECKPOINT-0 (Step 0 / ADR-010 IN-1)** — verified live on MS-S1 MAX:
Ollama **0.24.0**, pin **`gpt-oss:20b`** (Cray-adjudicated; gpt-oss:20b and
gemma4:26b both honour the `format` schema constraint under every `think`
setting). The Ollama #15260 `think=false`+`format` bug is **still live for
the Qwen3.x family** but absent for gpt-oss:20b + gemma4:26b. Binding rule:
the structuring call omits `think` — never `think=false` with `format`.

New module set (PLAN-0006) — `services/engine/llm/`: `client.py` (async
Ollama wrapper), `prompt.py` (assembly + IN-2 injection containment),
`structured.py` (constrained generation + validate-and-retry + semantic
checks + the SC-1 reduced `LlmJudgment` sub-schema), `trace.py` (hybrid
reasoning trace). `recommender.py` rewired — `async`, with the deterministic
rule body retained as the fail-safe; `config.py` extended; one `await` at
the API call site; an eval harness + golden traces under
`tests/services/engine/eval/`.

**Follow-ons:** **TODO-A is done** — ADR-001 Amendment 1 (`30d2c8e`) pins
`gpt-oss:20b` + Ollama 0.24.0 for the recommender path (superseding
`gemma4:26b` for that path only). TODO-B (config default) is
satisfied — Step 1 added a dedicated `recommender_model` setting. **SC-1**
resolved by Code: constrained generation targets the reduced `LlmJudgment`
sub-schema; the harness composes the full (unchanged) ADR-007 D2 envelope.
A Step-7 live capture surfaced + fixed a `suggested_handler` defect (the
model invented unregistered handlers — now enum-constrained to the registry).

**Prior this session — PLAN-0005 Phase 2 (OCT Engine Runtime Layer) MERGED**
(PR #4, `c646bab`) — the runtime the LLM hook plugs into. **109 passed**,
coverage **95.34%**. Module / endpoint set (PLAN-0005 §11):

- `services/engine/data_adapter.py` — `DataAdapter` Protocol (ADR-007 D1)
- `services/engine/actions.py` — `RecommendedAction` runtime envelope (ADR-007 D2)
- `services/engine/registry.py` — `VerticalRegistry` (OQ-6 explicit registration)
- `services/engine/recommender.py` — rule-based recommender + minimal approval
  gate (`recommend` / `approve` / `reject` / `execute`; OQ-2/OQ-3)
- `verticals/energy/data_adapter/` — `EnergySyntheticAdapter` + synthetic dataset
- `verticals/energy/handlers.py` — energy `echo` action handler
- `services/db/` — async SQLAlchemy ORM (6 energy tables), session, and the
  envelope→entity persistence projection
- `alembic/` — async migration env + first revision (the six energy tables)
- `services/api/` — three-layer wiring: lifespan-registered energy vertical +
  the action-loop router: `GET /objects/{type}`, `GET /recommendations`,
  `POST /recommendations/{id}/approve`, `POST /recommendations/{id}/execute`;
  `/health` preserved

All six §8 Open Questions (Cray-adjudicated 2026-05-21) are honoured. Persistence
(OQ-4) is real `postgres:16-alpine` via SQLAlchemy 2.0 async + Alembic + asyncpg;
the §7.6 tests run against a live DB and the DDL/ORM parity test (C-1/R6) guards
type drift. The §8.1 deferred-foundational revisit register is in Active TODOs.

Tooling note: `ruff` + `mypy` are now pinned in `pyproject.toml` to the
pre-commit gate versions (`9d461f2`) — closes a `.venv`-vs-gate version skew.
The pre-commit `mypy` hook now also covers `^(services|verticals)/`
(`9dd1470`), not just `services/` — closes the flagged coverage gap.

---

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
