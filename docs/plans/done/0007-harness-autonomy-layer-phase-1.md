# PLAN-0007: Harness Autonomy Layer — Phase 1 Execution

**Status:** Draft
**Owner:** Claude Code (Tier 2 — autonomy primitives are Code-exclusive per ADR-013 D1)
**Created:** 2026-05-23
**Related ADRs:** ADR-013 (autonomy axis relocation — **gates this plan**; Phase 1 executes ADR-013 D2/D4/D5), ADR-009 (D2 only-Code-commits — enforced by item #4), ADR-012 (free-form venues retained), ADR-006 (core vs vertical infrastructure)

> **Sequencing gate (dispatch §6 / CLAUDE.md §6 Decision Flow).** Code does
> **not** execute this plan until **both** ADR-013 and this PLAN are
> committed **and** ADR-013 `Status` flips to `Accepted` (Cray ratifies).
> Drafting order was ADR-013 first, then this PLAN.

## Goal

Stand up the **first `.claude/` harness-autonomy layer** for vero-lite —
greenfield, since `.claude/settings.json` and `.claude/hooks/` do not exist
at HEAD 68053fe. Phase 1 delivers the locked items #1–#5 (Cray E.3):
hook-directory scaffold, an env-var-driven Telegram notification bridge, a
`Notification` hook that pings Cray when the agent needs input, a
`PreToolUse deny` hook that makes the ADR-009 D2 "only Code commits"
boundary deterministic, and migration of `validate_handoff.py` into a
`PostToolUse` hook so handoff frontmatter is validated automatically.
Phase 1 deliberately **excludes** the `Stop` continuation loop, the Sonnet
pause/proceed classifier, stateful loop-detection, the subagent topology,
and the MCP bus — those are PLAN-0008+.

## Acceptance Criteria

> Three criteria, locked per dispatch §4.

- [ ] **AC-1 — AFK notification works.** Cray walks away from the desk for
  ~30 min while a Code agent runs a PLAN execution. Cray receives a
  Telegram ping **iff** the agent hits a `permission_prompt` or
  `idle_prompt` event (and not otherwise — no spurious pings on normal
  tool use).
- [ ] **AC-2 — Commit boundary is hook-enforced and bypass-immune.**
  Attempting `git commit` (or `push`/`merge`) from a non-Code session is
  **denied at the hook layer**. Verify the agent cannot bypass it with any
  prompt variant, including a session that has `bypassPermissions` — the
  `PreToolUse deny` decision must beat `bypassPermissions` (ADR-013 D2 /
  direction-b §4.1).
- [ ] **AC-3 — Handoff frontmatter validates automatically.** Every
  handoff file written/edited under `.claude/handoffs/session-NN/`
  triggers `validate_handoff.py` via the `PostToolUse` hook; a FAIL blocks
  the write. The K-1 "Cowork mental-validation" workaround is retired for
  any handoff Code touches (direction-b §8).

## Out of Scope

> Everything below is deferred to **PLAN-0008+**. Listed so the boundary is
> explicit (dispatch §4 out-of-scope).

- ❌ **Phase 2 — `Stop` continuation loop + Sonnet pause/proceed classifier.**
  The "are we done? if not, keep going" loop (ADR-013 D4), the
  8-consecutive-block cap (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`) and
  `stop_hook_active` guard, and the Sonnet classifier reading
  `.claude/autonomy-triggers.md`. Phase 1 ships the registry **file** and
  the deterministic `deny`/`Notification` hooks, but **not** the
  probabilistic proceed/pause engine.
- ❌ **Phase 2 — stateful loop-detection (Cray E.4).** Needs a
  `.claude/state/` design (loop-counter, reset-on-progress semantics);
  scoped in §"Always-pause trigger registry" below but **not built** in
  Phase 1.
- ❌ **Phase 3 — subagent topology** (read-only Explore for research, Plan
  subagent for ADR/PLAN drafting, main agent edits/commits; direction-b §6
  item 3). Gated additionally on ADR-013 OQ-1 (Cowork/Chat authoring
  end-state).
- ❌ **Phase 4 — MCP `vero-bridge` cross-surface transport + plugin
  bundle.** Article guidance + direction-b §4 item 2: build only after
  hooks are proven.
- ❌ **Auto-handoff Code→Cowork/Chat without a Cray paste.** Depends on the
  `Stop` hook + machine-parseable handoff outcome; Phase 2+.
- ❌ **Stop-hook lesson auto-draft** into `docs/lessons/_drafts/`. Phase 2+.

## Steps

### Step 1 — Scaffold `.claude/settings.json` + `.claude/hooks/`

Greenfield (verified absent, direction-b §3). Create the hook config root
and the hooks directory.

- Create `.claude/hooks/` and a minimal `.claude/settings.json` with an
  empty-but-valid `hooks` block, then populate per Steps 3–5.
- Confirm the installed Claude Code version supports the hook fields used
  (note: the `if` field needs v2.1.85+; **agent**-type hooks are
  experimental — Phase 1 uses **command**-type hooks only, no agent or
  prompt hooks, for load-bearing determinism; direction-b §7).
- `.gitignore` review: decide whether `.claude/settings.json` is tracked
  (recommended: tracked, since it is the shareable convention) while
  `.claude/state/` and any token files stay gitignored. **No secret may
  land in a tracked file** (CLAUDE.md §8) — the Telegram token is env-var
  only (Step 2).

### Step 2 — Telegram bridge `tools/notify/telegram.sh`

Env-var-driven shell notifier (ADR-013 D5).

- Reads `$TELEGRAM_BOT_TOKEN` and `$TELEGRAM_CHAT_ID` from the environment;
  **never** hardcodes them. Per Cray E.2 the live values target bot
  `@vero_tg_bot` (ID `8492382723`), chat_id `5247477693` — set in the
  shell env, not committed.
- `curl` + POSIX shell only (no Python dep; mypy-strict N/A to shell).
- **Graceful no-op if either env var is unset** — a dev session without
  the vars must not break (exit 0, log a one-line "telegram: env unset,
  skipping" to stderr).
- Payload contract: accepts `{session, prompt, options[]}` (see Step 3) and
  POSTs a formatted message to the Telegram `sendMessage` API.
- Smoke-test parity: reproduce the Cray E.2 PASS (`curl` → `{"ok":true}`)
  as the script's self-test path.

### Step 3 — `Notification` hook → `telegram.sh`

The AFK ping (ADR-013 D5; AC-1).

- Matchers: `permission_prompt` **and** `idle_prompt` (only these — no
  ping on routine tool use, so AC-1's "and not otherwise" holds).
- Invokes `tools/notify/telegram.sh` with payload
  `{session, prompt, options[]}` extracted from the hook event.
- Command-type hook (not agent/prompt), per Step 1 determinism rule.

### Step 4 — `PreToolUse deny` hook → ADR-009 D2 enforcement

Deterministic commit-boundary (ADR-013 D2; AC-2).

- Matcher: `Bash` tool whose command matches `^git (commit|push|merge)`
  (anchor to the start; account for leading env/`cd` prefixes —
  harden the regex against `git -C ...` and `&&`-chained forms during
  implementation).
- Condition: session identity **!= Code**. **The mechanism for determining
  session identity is delegated to Code** (Cray-adjudicated 2026-05-23,
  ADR-013 OQ-3): Code analyzes and decides among env marker the Code launch
  sets / settings-scope / cwd heuristic / other. This is an execution-phase
  decision, not a drafting blocker.
- Decision: `deny`. **Confirm bypass-immunity** against `bypassPermissions`
  (direction-b §4.1) as part of AC-2.
- This is the load-bearing fail-safe; it must be a deterministic command
  hook, **never** a prompt/classifier (ADR-013 D2 rationale).

### Step 5 — `validate_handoff.py` → `PostToolUse` hook

Auto-validate handoff frontmatter (AC-3; direction-b §8).

- Matcher: `Write|Edit` on paths matching `.claude/handoffs/**`.
- Action: run `tools/handoffs/validate_handoff.py` against the touched
  file; **block on FAIL** (non-zero exit → `PostToolUse` blocking
  decision).
- Migrates the validator from manual-only invocation (Lesson #7 §3.2 /
  Lesson #8 K-1 workaround) into the harness. Retires the K-1
  mental-validation step for Code-touched handoffs.
- **Known interaction (do not regress):** the validator warning-swallow
  bug (STATUS Active TODOs, PLAN-004 Phase B — `_schema.py:_build()` drops
  WARNING-severity findings on otherwise-valid files). The hook should
  treat hard errors as blocking; whether it also surfaces warnings depends
  on the Phase-B fix. Flag, do not silently couple this plan to that fix.

### Step 6 — Always-pause trigger registry `.claude/autonomy-triggers.md`

Create the **canonical, machine-readable** registry (ADR-013 D4). Phase 1
ships the **file + its content**; the Sonnet classifier that *reads* it is
Phase 2 (out of scope). Consolidate the three sources below into one list.
**Proposed location: `.claude/autonomy-triggers.md`** — Cowork's proposal;
Code confirms fit (alternatives: a section in `settings.json`, or a skill).
Cowork's assessment: a standalone `.claude/` markdown file is the right
home — it is DRY (one source the Phase-2 hook prompt references), reviewable
in diffs, and co-located with the harness config; embedding in
`settings.json` would inline the list into both the `Stop` and `PreToolUse`
prompts and drift (ADR-013 D4 rejected alternative).

**Registry contents (consolidated):**

*From Cowork direction-b §5 (governance boundaries):*

- mutate any ADR with `Status: Accepted`
- consume / earmark an ADR or PLAN number
- read / touch `docs/strategy/private/**`
- scope override past ratified tier boundaries
- `git commit` / `git push` (D2 fail-safe — duplicated here as a
  classifier belt-and-suspenders even though Step 4's `deny` hook is the
  deterministic guarantee)

*From Chat additions (config / dependency / wording boundaries):*

- model pin / version bump (ADR-001 Amendment 1 precedent)
- new external dependency (`pyproject.toml`, `package.json`, lockfiles)
- public/private wording boundary crossing
  (`docs/strategy/{public,private}/**`)

*New from Cray E.4 (stateful loop-detection — registry entry now, engine in
Phase 2):*

- **Loop-detect:** same `(tool, target)` ≥ 6 attempts in a single session
  → pause + Telegram with payload `{loop_type, target, last_6_actions}`.
- Loop-types to track (Cowork scoping for Code to refine in Phase 2):
  1. same file edited ≥ 6 times in one turn
  2. same test fails ≥ 6 times consecutively
  3. same error signature ≥ 6 times
  4. same Bash command pattern fails ≥ 6 times
- State storage: `.claude/state/loop-counter.json` (gitignored).
- Reset on observable progress (test passes, or target untouched the next
  turn).

> The stateful loop-detection rows are **registered** in Phase 1 but
> **not enforced** — enforcement needs the `.claude/state/` design + the
> Phase-2 `Stop`/`PreToolUse` classifier. Marked clearly in the registry
> as "Phase 2 enforcement."

## Verification

How we know Phase 1 worked — maps 1:1 to the acceptance criteria, plus a
green-state gate.

- **AC-1 verification:** run a real (or simulated) Code PLAN execution that
  triggers `permission_prompt` and `idle_prompt`; confirm a Telegram
  message arrives for each, and confirm a routine no-prompt tool run
  produces **no** message. Also run `telegram.sh` with env vars unset and
  confirm graceful no-op (exit 0, no crash).
- **AC-2 verification:** from a non-Code session, attempt
  `git commit`/`push`/`merge` and confirm `deny`. Repeat with a
  `bypassPermissions` session and confirm the `deny` still holds. From a
  Code session, confirm a legitimate commit is **allowed** (no false
  positive that would brick Code's own commit authority).
- **AC-3 verification:** write a deliberately invalid handoff (bad enum /
  missing required field) under `.claude/handoffs/session-NN/` and confirm
  the `PostToolUse` hook blocks it; write a valid one and confirm it
  passes. Cross-check against `tools/handoffs/_schema.py` REQUIRED_FIELDS /
  enums.
- **Repo-health gate:** `.claude/settings.json` is valid JSON; the hooks do
  not fire on unrelated tool use (no notification spam, no spurious
  blocks); no secret is committed (`detect-secrets` / CLAUDE.md §8); the
  Telegram token exists only in the environment, never in a tracked file.
- **Recommended:** Code runs the AC-2 bypass-immunity check as the
  highest-priority verification — it is the safety-critical fail-safe and
  the one most expensive to get wrong.

## Notes / surfaces for Cray

- **Session-identity signal (Step 4) — delegated to Code (Cray
  2026-05-23, ADR-013 OQ-3).** The `PreToolUse deny` condition "session !=
  Code" needs a concrete signal in the hook context. Cray asked Code to
  analyze and decide the mechanism (env marker the Code launch sets vs
  settings-scope vs cwd heuristic vs other). Code surfaces its chosen
  approach in the execution closeout; it is not a drafting blocker.
- **`.claude/settings.json` tracked vs gitignored.** Recommendation: track
  it (it is the shareable convention, no secrets inside); keep
  `.claude/state/` and any token material gitignored. Cray confirms at
  commit time.
- **Phase-1 scope honors E.3 exactly** (items #1–#5). The continuation
  loop + classifier (the highest-leverage but highest-risk piece) is
  intentionally held to Phase 2 so the deterministic safety pieces (commit
  `deny`, handoff validation) and the AFK channel land and are proven
  first.
