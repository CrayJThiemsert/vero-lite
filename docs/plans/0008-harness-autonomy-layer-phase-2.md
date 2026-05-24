# PLAN-0008: Harness Autonomy Layer — Phase 2 Execution

**Status:** Draft
**Owner:** Claude Code (Tier 2 — autonomy primitives are Code-exclusive per ADR-013 D1)
**Created:** 2026-05-24
**Related ADRs:** ADR-013 (autonomy axis relocation — **gates this plan**; Phase 2 executes ADR-013 D4 + Cray E.4), ADR-009 (D2 "only Code commits" preserved by carrying the G5 hook through unchanged), ADR-006 (core vs vertical infrastructure — autonomy = core)
**Related PLANs:** PLAN-0007 (Phase 1, MERGED `b2ea9b8` 2026-05-23; this plan builds on its `.claude/` scaffolding and the `.claude/autonomy-triggers.md` registry)

> **Sequencing gate.** Code executes this plan only after:
>
> 1. Phase 1 is merged on `main` (✓ as of 2026-05-23, [PR #6](https://github.com/CrayJThiemsert/vero-lite/pull/6) `b2ea9b8`) with all three ACs verified live (AC-1 AFK ping, AC-2 16-case bypass-immune commit-deny, AC-3 handoff-validator blocking).
> 2. The C4 research-path hook is merged (✓ as of 2026-05-24, [PR #7](https://github.com/CrayJThiemsert/vero-lite/pull/7) `da4f91d`) — demonstrates the deterministic-hook pattern works as a unit and validates the Windows-UNC path-normalization idiom Phase 2 reuses for L1 file-target matching.
> 3. This PLAN's `Status` flips Draft → Ready for execution after Cray ratification of the Notes/OQs §.

## Goal

Layer the **probabilistic / classifier-mediated autonomy engine** on top
of Phase 1's deterministic hooks. Phase 2 ships three coupled pieces, all
inside `.claude/`:

1. **`Stop` continuation loop** — the "are we done? if not, keep going"
   guard (ADR-013 D4). Uses `stop_hook_active` to prevent recursive
   re-entry and `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` (default 8) as a chain
   fail-safe. Lets Code self-continue past `Stop` events without a Cray
   "go" when the next action is clearly-best per the registry.

2. **Sonnet pause/proceed classifier** — Sonnet-backed (Cray E.5)
   prompt-hook on `Stop` and selected `PreToolUse` events that reads
   `.claude/autonomy-triggers.md` verbatim and decides `pause` (→ Telegram
   ping via the Phase 1 Notification bridge) vs `proceed`. Phase 1 shipped
   the registry rows G1–G5 / C1–C4 / H1 / L1–L4 and flagged the
   non-deterministic ones "Phase 2 enforcement"; Phase 2 ships the engine
   that reads them.

3. **Stateful loop-detection (L1–L4)** — `.claude/state/loop-counter.json`
   (gitignored) with the `(tool, target)` ≥ 6 counting + reset-on-progress
   semantics that the L1–L4 registry rows describe. On count = 6 the
   `Notification` flow fires with payload `{loop_type, target,
   last_6_actions}` (ADR-013 / Cray E.4).

Phase 2 keeps Phase 1's deterministic guarantees intact: **G5
(`pretooluse_git_deny.py`) + H1 (`posttooluse_validate_handoff.py`) + C4
(`pretooluse_research_path_deny.py`) remain load-bearing fail-safes** and
are not replaced by classifier judgment (ADR-013 D2 rationale). The
classifier is **belt** above the deterministic **suspenders**, never a
substitute.

## Acceptance Criteria

> Four criteria. AC-1 / AC-2 / AC-3 cover the new Phase 2 surface; AC-4
> guards against Phase 1 regression.

- [ ] **AC-1 — `Stop` continuation loop self-continues on clearly-best
  paths.** In a Code session running a multi-step task, when the model
  emits a `Stop` event with an obvious next action (e.g., "tests pass,
  commit"; "ruff clean, run mypy"), the `Stop` hook proceeds without a
  Cray paste. Verified by observing ≥ 3 consecutive auto-continuations on
  a real PLAN-execution-style flow. The `stop_hook_active` guard prevents
  recursive re-entry; the `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP=8` env caps
  the chain. **No false-positive auto-continue past a registry-matched
  pause condition** (cross-check with AC-2 cases).

- [ ] **AC-2 — Classifier pauses on registry matches, does not
  false-positive on routine work.** Test cases must demonstrate the
  classifier pauses when the agent's next action matches a registry row,
  in particular:
  - **G1** — about to `Edit` an Accepted ADR → pause + Telegram
  - **G2** — about to consume an ADR/PLAN number (filename creation under
    `docs/{adr,plans}/NNNN-*`) → pause + Telegram
  - **C1** — about to bump a model pin in `pyproject.toml` or
    `docker-compose.yml` → pause + Telegram
  - **C2** — about to add an external dep (new entry in `pyproject.toml`
    `dependencies` or a lockfile change) → pause + Telegram

  And **does not** false-positive on routine work (running tests, reading
  files, normal code edits outside the registry surface). ≥ 8 test cases
  green (4 true-positive + 4 true-negative).

- [ ] **AC-3 — Loop-detection fires on L1–L4 patterns and resets on
  progress.** A synthetic test harness drives each L1–L4 pattern past 6
  attempts and confirms:
  - `.claude/state/loop-counter.json` records the `(loop_type, target,
    count)` correctly
  - At `count = 6`, a Telegram ping with `{loop_type, target,
    last_6_actions}` fires (payload contract per ADR-013 / Cray E.4)
  - Reset semantics work: a test pass (L2) zeros the L2 counter for that
    nodeid; the target-untouched-next-turn signal (L1) zeros the L1
    counter; clean exit (L4) zeros the L4 counter for that command pattern
  - State file survives across hook invocations within a session (atomic
    JSON write via tmpfile + `os.replace`)

- [ ] **AC-4 — Phase 1 guarantees regression-free.** Re-run all Phase 1
  + C4 acceptance checks after Phase 2 lands:
  - Phase 1 AC-1 (AFK ping live)
  - Phase 1 AC-2 (16-case bypass-immune commit-deny matrix, including
    `bash -c`, backtick chains, `git -C`, env-prefix spoof, `&&` chains)
  - Phase 1 AC-3 (handoff-validator blocks bad frontmatter)
  - C4 (`pretooluse_research_path_deny.py` allows `private/` + `strategy/`,
    blocks bare `research/` + public/ + arbitrary subdirs)

  **All four must remain green.** A Phase 2 hook that disturbs Phase 1
  guarantees is a hard fail, regardless of new-feature progress.

## Out of Scope

> Everything below is deferred to **PLAN-0009+**. Listed so the Phase-2
> boundary is explicit.

- ❌ **Phase 3 — subagent topology.** Read-only Explore subagent for
  research, Plan subagent for ADR/PLAN drafting, main agent edits/commits
  (ADR-013 D1 phased). Carry to PLAN-0009.

- ❌ **Phase 4 — MCP `vero-bridge` cross-surface transport + plugin
  bundle.** Build only after subagents prove out. Carry to PLAN-0010.

- ❌ **Auto-handoff Code → Cowork/Chat without a Cray paste.** Depends on
  `Stop` + a machine-parseable handoff-outcome contract; Phase 2 ships the
  `Stop` hook's `proceed` arm but **not** the "pause + auto-draft a
  Cowork dispatch" arm. Carry to PLAN-0009 alongside the subagent
  topology, where the Plan subagent is the right author for the
  auto-drafted dispatch.

- ❌ **Stop-hook lesson auto-draft into `docs/lessons/_drafts/`.** A
  "when classifier pauses, draft a lesson stub" affordance; needs a
  lesson-template + auto-draft policy. Carry to PLAN-0009.

- ❌ **Cross-session loop-counter persistence.**
  `.claude/state/loop-counter.json` is **per-session** (resets at session
  start). Cross-session retention would require a session-ID design and
  a retention/expiry policy; out of Phase 2 scope.

- ❌ **Classifier-enforcement of rows already covered by other layers.**
  G3 (`docs/strategy/private/**`) is covered by `.gitignore` at the FS
  layer; C4 (research-path) is covered by the deterministic
  `pretooluse_research_path_deny.py` (Phase 1). These rows stay as
  classifier belt-and-suspenders mirrors; no separate Phase 2 enforcement
  is added on top.

- ❌ **Replacing Phase 1 deterministic hooks with classifier decisions.**
  G5 git-deny + H1 handoff-validator + C4 research-path-deny remain
  deterministic per ADR-013 D2 rationale ("the most safety-critical
  rule[s] must be deterministic"). Phase 2 adds, never substitutes.

- ❌ **Hard cost gate on classifier calls.** Phase 2 captures cost
  telemetry informationally; no per-session token/cost cap is enforced.
  A future plan can add one if Sonnet costs balloon.

## Steps

### Step 1 — `.claude/state/` design + loop-counter schema

Design the state directory layout and the loop-counter JSON shape before
any code lands.

- Create `.claude/state/` (gitignored — add a top-level `.claude/state/`
  entry to `.gitignore`, alongside the existing `.claude/handoffs/`
  pattern from Phase 1).
- Define `.claude/state/loop-counter.json` schema:

  ```json
  {
    "session_id": "<source per OQ-A>",
    "started_at": "ISO-8601",
    "counters": {
      "<loop_type>:<target_normalized>": {
        "count": 3,
        "last_6_actions": [
          {"ts": "ISO-8601", "tool": "Edit", "target": "...", "result": "..."}
        ],
        "last_updated": "ISO-8601"
      }
    }
  }
  ```

- **Target normalization** (reuse the C4 hook's idiom for path handling
  — proven in 20-test pass on Windows-UNC):
  - File paths → forward-slash + project-relative (backslash → slash
    before `pathlib`; strip `\\wsl.localhost\...` prefix to project root)
  - Test IDs → pytest `nodeid` (`tests/path/test_x.py::test_y`)
  - Error signatures → first non-volatile line of the traceback (strip
    timestamps, addresses, temp paths)
  - Bash command patterns → tokenized form with `<arg>` placeholders
    (e.g., `pytest <path>` collapses `pytest tests/foo.py` and `pytest
    tests/bar.py` into the same pattern when desired; configurable per
    L4 row)

- **Atomic write semantics:** write to
  `.claude/state/loop-counter.json.tmp`, then `os.replace()` to the
  canonical name. Hook re-reads before each write to tolerate concurrent
  invocations.

- **Reset triggers (observability-driven, not time-based):**
  - L1 reset: target file untouched on the next turn-boundary marker
  - L2 reset: same test `nodeid` passes
  - L3 reset: error signature absent from the next 2 tool outputs
  - L4 reset: command pattern returns exit 0

- The counter file carries enough state to make reset decisions locally;
  no out-of-band store needed.

### Step 2 — `PreToolUse` loop-detection hook

`.claude/hooks/pretooluse_loop_detect.py` — runs **alongside** the
existing Phase 1 `PreToolUse` hooks (`pretooluse_git_deny.py`,
`pretooluse_research_path_deny.py`). Hook order is additive; the new
hook does not reorder or wrap the deterministic ones.

- **Matcher:** all tools (`*`); body fast-exits unless `(tool, target)`
  matches an L1–L4 pattern.
- **Behavior:**
  - Read `.claude/state/loop-counter.json`; compute the counter for the
    matched `(loop_type, target_normalized)` key.
  - If `count < 6`: emit no decision (allow the tool call to proceed);
    the counter increment for **this** attempt is written by the
    `PostToolUse` observer (Step 3) so the count reflects actual
    invocations, not attempts.
  - If `count ≥ 6`: invoke `tools/notify/telegram.sh` with the
    `{loop_type, target, last_6_actions}` payload, then emit a `deny`
    decision with a `message` asking Cray to intervene.
- **L1** (file edited ≥ 6 times): match `Write|Edit` + same normalized
  `file_path`.
- **L4** (bash command pattern fails ≥ 6 times): match `Bash` + tokenized
  command + counter-was-incremented-by-non-zero-exit (the exit-code signal
  lives in `PostToolUse`; Step 2 only reads the counter).
- **L2 / L3:** require `PostToolUse` test-result / error-signature
  observation (Step 3) to feed the counter; Step 2 only reads.

### Step 3 — `PostToolUse` progress observer

`.claude/hooks/posttooluse_progress_observer.py` — observes tool outputs
to feed the loop-counter and trigger resets. Runs **alongside** the
existing Phase 1 `posttooluse_validate_handoff.py` (no reorder).

- **Matcher:** `Bash|Write|Edit` (the tools whose outcomes signal
  progress or regress).
- **For `Bash`:**
  - Parse exit code; if 0 and command pattern matches an active L4
    counter → reset that counter.
  - If `pytest` output present, extract pass/fail counts + failing
    nodeids; reset L2 counter for passing nodeids, increment for failing.
  - If a Python traceback present, hash the first non-volatile line for
    L3.
- **For `Write|Edit`:**
  - Increment the L1 counter for the normalized `file_path`.
  - Record `file_path` as last-touched-this-turn (turn-boundary marker
    for the next-turn L1 reset signal).
- **Atomic write** (Step 1 semantics).
- **Never blocks.** This hook is observation-only; the `PreToolUse` hook
  (Step 2) is the gate.

### Step 4 — `Stop` continuation loop

`.claude/hooks/stop_continuation.py` — the "are we done?" guard
(ADR-013 D4). Greenfield; Phase 1 did not ship any `Stop` hook.

- **Matcher:** `Stop` event.
- **Behavior:**
  1. **`stop_hook_active` re-entry guard.** If the harness flag
     `stop_hook_active` is true (already inside a stop-hook chain) →
     emit **no block** (let the stop fire). Prevents recursive re-entry
     per Anthropic stop-hook docs.
  2. **Chain-depth cap.** Read `.claude/state/stop-chain.json` (session-
     scoped, atomic write per Step 1 semantics); compare against
     `$CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` (default 8). If at cap → see
     **OQ-E** for the cap-policy decision (recommendation: pause +
     Telegram "cap reached", not silent release).
  3. **Classifier dispatch.** Otherwise, invoke the Sonnet classifier
     (Step 5) with the registry + the agent's last action as context.
     Classifier returns `{decision: "proceed" | "pause", reason: "..."}`.
  4. **On `proceed`:** emit a `block` decision with a `reason` field
     that points the agent to its next action (per Anthropic stop-hook
     docs: a `block` from the stop hook returns the agent to the loop).
     Increment chain depth.
  5. **On `pause`:** emit no block; the stop fires normally; invoke the
     `Notification` flow → Telegram ping with the classifier's `reason`.
- **Resets chain depth** on a clean `pause` or terminal stop.
- This is the only Phase 2 hook that interacts with the Notification
  flow (which itself is Phase 1's `tools/notify/telegram.sh`).

### Step 5 — Sonnet pause/proceed classifier

`.claude/hooks/sonnet_classifier.py` — the prompt-hook helper that backs
Step 4's `Stop` dispatch and the non-deterministic `PreToolUse` rows
(G1, G2, C1, C2 — see AC-2).

- **Invocation:** command-type hook (no agent/prompt hook — Phase 1
  determinism rule from PLAN-0007 §1 carries through). Shells out to
  either:
  - the `claude` CLI with `--model claude-sonnet-4-6 --output-format
    json --max-tokens 1024 ...`, or
  - the Anthropic SDK directly (preferred for deterministic structured
    output via `format` constraint)
- **System prompt:** reads `.claude/autonomy-triggers.md` verbatim +
  instructs the model to return JSON matching the output contract.
  Registry path is referenced (not inlined) so registry edits are picked
  up without a hook change (ADR-013 D4 DRY rationale).
- **Output contract:** JSON
  `{"decision": "proceed" | "pause", "matched_rows": ["G1", "L3", ...],
  "reason": "..."}`. `matched_rows` enum = registry row IDs.
- **Model pin:** `claude-sonnet-4-6` (per CLAUDE.md "default to latest
  Sonnet"; see OQ-B). Pin lives in `.claude/settings.json` so a future
  bump is a single-line PR.
- **Token budget:** 1024 output cap (decision + short reason); 2048 input
  cap (registry is ~100 lines + action context).
- **Failure modes (fail-closed, never silently proceed):**
  - Sonnet unreachable / API error → **pause + Telegram** with
    "classifier unavailable, falling back to manual gate"
  - Malformed JSON output → retry once with stricter `format` constraint;
    second failure → fail-closed (pause + Telegram)
- **Cost rationale:** Cray E.5 picked Sonnet over Haiku for accuracy;
  the hook fires only on `Stop` events + the selected `PreToolUse` rows
  (G1, G2, C1, C2), not on every tool call. Rough budget: 20–50 calls
  per long session × ~500 tokens context = ~10–20k tokens/session.
  Acceptable; see OQ-F if a deterministic pre-filter becomes necessary.
- **Auth:** reads `$ANTHROPIC_API_KEY` from the env (set via `WSLENV`
  like the Telegram token in Phase 1). **No committed credentials**
  (CLAUDE.md §8).

### Step 6 — Wire into `.claude/settings.json` + extend `autonomy-triggers.md`

- **Register Steps 2–4 hooks** in `.claude/settings.json` (Phase 1 file
  already exists from `b2ea9b8`). Step 5 is a helper invoked by Step 4
  + the PreToolUse classifier dispatch, not a top-level hook entry.
- **Update `.claude/autonomy-triggers.md`:**
  - **L1–L4 rows:** flip "Phase 1 = Manual observation only" →
    "Phase 2 = Enforced via `pretooluse_loop_detect.py` +
    `posttooluse_progress_observer.py`".
  - **G1, G2, C1, C2 rows:** flip "Phase 2 enforcement = Classifier
    pause" status from theoretical to live (referenced from
    `sonnet_classifier.py` via `stop_continuation.py`).
  - **"How the classifier reads this file" §spec:** flip from
    "Phase 2 spec, not Phase 1" to **live**.
  - Bump the date footer.
- **Update `.gitignore`** to add `.claude/state/`.

### Step 7 — Tests

Mirror PLAN-0007's testing density (Phase 1 added 28 unit tests + 20
for C4 = 48 total in `tests/claude_hooks/`).

- **`tests/claude_hooks/test_loop_detect.py`** — synthetic counter
  increment + reset for each L1–L4 pattern (~12 tests)
- **`tests/claude_hooks/test_progress_observer.py`** — parse pytest
  output, traceback hash, bash exit + tokenization (~8 tests)
- **`tests/claude_hooks/test_stop_continuation.py`** — chain-depth cap
  + `stop_hook_active` re-entry guard + proceed/pause routing + cap-hit
  policy (~10 tests)
- **`tests/claude_hooks/test_sonnet_classifier.py`** — JSON contract
  + fail-closed paths + malformed-output retry; **Sonnet call is
  mocked** in CI. Optional live-API smoke tests gated by
  `RUN_LIVE_SONNET_TESTS=1` env, skipped in CI (~10 tests + 2 skipped
  live)
- **`tests/claude_hooks/test_state_atomicity.py`** — concurrent-write
  tolerance + tmpfile + `os.replace()` semantics (~4 tests)
- **`tests/claude_hooks/test_phase1_regression.py`** — re-run the
  Phase 1 + C4 acceptance harnesses to satisfy AC-4 (cross-reference
  existing tests, not duplicated)
- **Target totals:** `pytest` ~260 pass / 5 skip (Phase 1 left it at
  216 / 5).
- **Gate parity with Phase 1:** `ruff` + `mypy --strict` +
  `detect-secrets` all clean; mypy hook covers `.claude/hooks/**`
  (verify; extend the pre-commit `files` glob if needed).

### Step 8 — Live verification (AC harness)

Beyond unit tests, run the live verification matrix:

- **AC-1 live:** Drive a real PLAN-execution-style flow (e.g., a small
  `ruff fix` → `mypy` → commit loop), observe ≥ 3 auto-continuations,
  confirm Telegram is silent on the auto-continues.
- **AC-2 live:** Walk through the 4 true-positive + 4 true-negative
  cases manually, observe `pause + ping` vs `proceed`.
- **AC-3 live:** Drive each L1–L4 pattern past 6 attempts (synthetic
  loop or a real failing test), observe Telegram ping with the
  structured payload.
- **AC-4 regression:** Re-run the Phase 1 bypass-immunity matrix (16
  cases) + handoff-validator (good + bad frontmatter) + C4
  research-path-deny (private vs public/bare).
- Capture screenshots + payload bodies in a closeout handoff
  (`.claude/handoffs/session-NN/YYYY-MM-DD-NNNN-code-plan0008-phase2-closeout.md`).

## Verification

Maps 1:1 to AC-1 through AC-4 above. Repo-health gate:

- `.claude/settings.json` valid JSON; hooks fire only on intended
  matchers (no notification spam, no spurious blocks on routine tool
  use).
- `.claude/state/loop-counter.json` and `.claude/state/stop-chain.json`
  never tracked — verify with
  `git check-ignore .claude/state/loop-counter.json` returning a hit.
- No secret in tracked files (`detect-secrets`); `$ANTHROPIC_API_KEY`
  and `$TELEGRAM_*` env-var-only, never in `.claude/settings.json`.
- Phase 1 deterministic guarantees (G5 / H1 / C4) verified post-merge
  of Phase 2 (AC-4).
- **Cost telemetry:** capture a baseline of classifier-call count +
  token usage per session over a 3-session sample (informational; no
  hard cost gate in Phase 2 per Out-of-Scope).

## Notes / surfaces for Cray

> Drafting surfaces that Cray adjudicates before / at Code-commit time.
> None of these are drafting blockers; Code can begin Step 1 immediately
> on Cray ratification and surface the resolved decision in the closeout.

- **OQ-A — Session-ID source for `.claude/state/`.** The Phase 1
  `CLAUDE_TIER=code` env marker identifies *tier*, not session.
  Loop-counter + stop-chain state need a session scope. Options:
  (a) `$CLAUDE_SESSION_ID` if the harness exposes one (Code to verify
  at execution time);
  (b) PID of the launching shell;
  (c) per-session `.claude/state/<UUID>/` directory minted on first
  hook invocation.
  **Recommendation:** (a) → (c) fallback. Code analyzes + decides at
  execution; record in closeout. *Drafting blocker?* No.

- **OQ-B — Sonnet model pin.** Step 5 pins `claude-sonnet-4-6`.
  CLAUDE.md says "default to the latest and most capable Claude
  models." If a newer Sonnet (4.7+) is GA at merge time, bump in the
  same PR. Cray confirms the pin at commit-review time.

- **OQ-C — Classifier-output schema vs registry drift.** The
  registry's row IDs (G1–G5, C1–C4, H1, L1–L4) are the natural enum for
  `matched_rows`. Step 5 specifies this; if the registry grows new
  rows *during* Phase 2 execution, the classifier prompt must be
  regenerated. Mitigation: the registry path is referenced (not
  inlined), so adding rows is a registry-only edit. Note in commit body.

- **OQ-D — Auto-handoff Code → Cowork/Chat is deliberately deferred.**
  Phase 2 ships the `Stop` `proceed` arm but not the
  "pause + auto-draft a Cowork dispatch" arm — so on every classifier
  `pause`, Cray still pastes the resulting handoff. Reasonable for
  Phase 2; the subagent topology in PLAN-0009 is the right place for
  the Plan subagent to auto-draft. **Flag if Cray wants it brought
  into Phase 2.**

- **OQ-E — `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` policy on hit.** Step 4
  alternatives at cap:
  - **(a) silent release** — proceed normally, let the stop fire (the
    agent simply stops mid-flow)
  - **(b) pause + Telegram with `"cap reached"`** — explicit signal to
    Cray
  **Recommendation: (b).** Silent release is a footgun; the agent
  stops with no explanation, and Cray has to reconstruct why. Cray
  confirms.

- **OQ-F — Deterministic pre-filter for the classifier.** Step 5's
  cost rationale assumes the classifier fires on every `Stop` event.
  If session-cost monitoring (the §Verification telemetry) shows the
  per-session cost climbing past acceptable bounds, the fallback is to
  add a deterministic pre-filter (e.g., only invoke the classifier if
  the next action touches `docs/adr/**`, `docs/plans/**`,
  `pyproject.toml`, lockfiles, or a registry-flagged path). **Not
  Phase 2 scope**, but flagged here so the telemetry has a destination.

- **OQ-G — Mock vs live classifier in CI.** Step 7 mocks Sonnet in CI.
  An end-to-end test that calls the live API and asserts JSON-contract
  shape would give higher confidence but introduces an API dependency
  in CI. **Recommendation: keep CI mocked; provide an opt-in live
  smoke test via `RUN_LIVE_SONNET_TESTS=1` env** that Cray runs locally
  before merge.

- **No CLAUDE.md edit required.** ADR-013 already amended §6 for the
  autonomy-axis relocation; PLAN-0008 implements ADR-013 without
  changing constitutional language. The Lesson #5 §1 restart-bridge
  sequence does **not** apply to this plan.

- **No new ADR required.** Phase 2 executes ADR-013 D4 (already
  Accepted). The cap-policy decision (OQ-E) is implementation policy,
  not architecture; lives in PLAN-0008 + the closeout, not a new ADR.

- **STATUS bumps at execution close** (`docs(status):` housekeeping
  commit per Q3 pattern): Current Focus + Recent Decisions row + Active
  TODOs flip + Next Steps (Phase 3 / PLAN-0009 subagent topology).
