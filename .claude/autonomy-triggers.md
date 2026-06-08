# Autonomy Triggers Registry

> **Status:** Phase 2 of PLAN-0008 — *classifier + loop-detect LIVE* as of
> 2026-05-24 (Wave 1 PR #11 + Wave-2-partial PR #12 + Step 5 PR #13 + Wave 2
> completion this PR). The Sonnet pause/proceed classifier
> (`.claude/hooks/_sonnet_classifier.py`, pin `claude-sonnet-4-6`) is wired
> into the `Stop` hook (`stop_continuation.py`) and reads this file
> verbatim per ADR-013 D4 + PLAN-0008 §"Step 6".
>
> **Authoritative source for autonomy decisions.** The `Stop` (and, in
> later phases, `PreToolUse`) prompts read this file verbatim. Edit
> here — **never inline the list into `settings.json` prompts** (rejected
> alternative per ADR-013 D4 — drift risk between the two hook prompts).
>
> **What is *deterministic* vs *classifier-mediated*.** Three rows below
> are enforced deterministically by Phase-1 hooks; they are listed here
> for the classifier's belt-and-suspenders awareness but the hook is the
> hard guarantee. The Phase-2 loop-detect (L1–L4) and classifier-mediated
> governance rows (G1, G2, C1, C2) became live in PLAN-0008 Wave 1 + Step
> 5 + Wave 2:
>
> - `git commit / push / merge` from non-Code session — enforced by
>   `.claude/hooks/pretooluse_git_deny.py` (CLAUDE_TIER env marker; G5).
> - `Write|Edit` to `.claude/handoffs/**` with bad frontmatter — enforced
>   by `.claude/hooks/posttooluse_validate_handoff.py` (H1).
> - `Write|Edit` to `docs/research/` outside `private/` — enforced by
>   `.claude/hooks/pretooluse_research_path_deny.py` (C4).
>
> Rows G3, G4, C3 remain **classifier-mediated** via the Sonnet pause/
> proceed dispatch on `Stop` events; no deterministic hook covers them
> (intentional — they require judgment the classifier supplies).

## Always-pause triggers

When ANY of the rows below matches an agent's intended next action, the
agent MUST pause, Telegram-ping Cray (via the Notification hook, once
the matching event type fires) or surface via handoff, and wait.

### Governance boundaries — from ADR-013 / direction-b §5

| # | Trigger | Phase 1 enforcement | Phase 2 + 3 enforcement |
|---|---------|---------------------|---------------------|
| G1 | Mutate any ADR with `Status: Accepted` | Advisory (agent judgment) | **Live** — `_sonnet_classifier.py` (Sonnet @ `Stop` via `stop_continuation.py`; **also @ `PreToolUse`** via `pretooluse_classifier_dispatch.py` per PLAN-0009 Step 5c-2) |
| G2 | Consume / earmark an ADR or PLAN number | Advisory | **Live** — `_sonnet_classifier.py` (Stop + **PreToolUse** per Step 5c-2) |
| G3 | Read / touch `docs/strategy/private/**` | Advisory + gitignored at FS layer | **Live** — `_sonnet_classifier.py` (Stop only — no Pre-tool signature) |
| G4 | Scope override past ratified tier boundaries (Tier 0/1/1b/2 per ADR-009) | Advisory | **Live** — `_sonnet_classifier.py` (Stop only) |
| G5 | `git commit` / `git push` / `git merge` | **Deterministic** (`pretooluse_git_deny.py`, ADR-009 D2 / ADR-013 D2) | Deterministic + classifier mirror (composed identity gate per PLAN-0009 Step 5a) |

### Config / dependency / wording boundaries — from Chat additions

| # | Trigger | Phase 1 enforcement | Phase 2 enforcement |
|---|---------|---------------------|---------------------|
| C1 | Model pin / version bump (ADR-001 Amendment 1 precedent) | Advisory | **Live** — `_sonnet_classifier.py` |
| C2 | New external dependency added to `pyproject.toml`, `package.json`, or any lockfile | Advisory | **Live** — `_sonnet_classifier.py` (verified live 2026-05-24 conservatism probe) |
| C3 | Public ↔ private wording boundary crossing in `docs/strategy/{public,private}/**` | Advisory | **Live** — `_sonnet_classifier.py` |
| C4 | `Write` / `Edit` under `docs/research/` outside `docs/research/private/**` (Cowork research landing-zone rule, `cowork_tab_instructions.md` line 192 + `.gitignore` lines 49-51) | **Deterministic** (`pretooluse_research_path_deny.py`; N=2 incident pattern — Lesson #5 §10.5 + 2026-05-23 `chat_harness_extension_points_analyzed.md` → ADR-013 D2 precedent applied) | Deterministic + classifier mirror |

### Handoff hygiene — from PLAN-004 / Lesson #7 / direction-b §8

| # | Trigger | Phase 1 enforcement | Phase 2 enforcement |
|---|---------|---------------------|---------------------|
| H1 | `Write` / `Edit` to `.claude/handoffs/**` produces frontmatter that fails `validate_handoff.py` | **Deterministic** (`posttooluse_validate_handoff.py`) | Deterministic |

### Loop-detect (Cray E.4) — **LIVE in Phase 2** (Wave 1 + Wave-2-partial)

Stateful loop-detection is live via the `.claude/state/loop-counter.json`
file (gitignored), the PreToolUse gate
(`pretooluse_loop_detect.py`), the PostToolUse writer
(`posttooluse_progress_observer.py`), and the `Stop`-hook L1
turn-boundary reset (`stop_continuation.py`). Base threshold ≥ 6 attempts
per `(loop_type, target)`; on trigger the Telegram payload contract is
`{loop_type, target, last_6_actions}` per ADR-013 / Cray E.4.

**L1 path-class threshold (Cray E.4 refinement, 2026-06-08).** L1 (file
edits) uses a path-class threshold via `_loop_counter.l1_threshold_for`:
**6 for code paths** (the `edit → test → fail → edit` thrash the guard
targets) and **15 for prose / doc paths** (`*.md` anywhere or under
`docs/`). Multi-section governance authoring (PLAN / ADR / STATUS / lessons
/ handoffs) legitimately makes many small sequential edits to ONE file in a
turn — that is the work, not a loop — and has no test/build feedback loop to
drive a directionless one; L2/L3/L4 cover the code feedback loop more
directly. The doc bar is raised but **finite**, so a genuinely stuck doc
loop still trips. Cray-approved self-modification (per-diff) on 2026-06-08.

| # | Trigger (same `(tool, target)` ≥ 6 attempts in one session) | Phase 1 | Phase 2 |
|---|--------------------------------------------------------------|---------|---------|
| L1 | Same file edited ≥ threshold times in one turn — **path-class threshold** (6 code / 15 prose-doc; see note above) | Manual observation only | **Live** — `pretooluse_loop_detect.py` (gate, `l1_threshold_for`) + `posttooluse_progress_observer.py` (writer + **subagent-completion reset**) + `stop_continuation.py` (turn-boundary reset) |
| L2 | Same test fails ≥ 6 times consecutively | Manual | **Live** — `posttooluse_progress_observer.py` (inline Telegram fire on trigger) |
| L3 | Same error signature ≥ 6 times | Manual | **Live** — `posttooluse_progress_observer.py` (inline fire; auto-reset deferred — see PLAN-0008 §Step 8) |
| L4 | Same Bash command pattern fails ≥ 6 times | Manual | **Live** — `pretooluse_loop_detect.py` (gate) + `posttooluse_progress_observer.py` (writer) |

**Payload contract (Phase 2):** when a loop trigger fires, the Telegram
ping carries `{loop_type, target, last_6_actions}`. State storage:
`.claude/state/loop-counter.json` (gitignored — see `.gitignore`).
**L1 reset on observable progress** happens at any of: (a) a `Stop`
turn boundary where the target was NOT touched that turn
(`stop_continuation.reset_untouched_l1`); (b) a successful `git commit`
of the file (`posttooluse_progress_observer._apply_commit_reset`); or
(c) a subagent (`Agent`/`Task`) tool completing — its edits reset the
turn's touched-file L1 counters so a drafter subagent's edits do not
pre-spend the main agent's budget (`_handle_agent_completion`). L2 resets
on a passing nodeid; L4 on a successful command. Loop-type taxonomy above
is Cowork-scoped; Code refines in Phase 2.

## Auto-handoff triggers (Phase 3 — LIVE per PLAN-0009 Step 5c-1)

When ANY of the rows below matches the agent's recent activity at a
`Stop` event, the Sonnet classifier returns `decision: dispatch`
(instead of `pause`). The `Stop` hook (`stop_continuation.py`) then
emits a `block` directive whose `reason` is a formatted instruction
that the main Code agent reads on its next turn, spawning the named
subagent via the `Agent` tool per PLAN-0009 Step 4 §1 R4 routing +
§5 budget reminder template.

The classifier itself does **not** spawn the subagent; only the main
agent can invoke `Agent`. The hook is the courier of the instruction,
not the actor. This preserves the ADR-009 D2 / ADR-013 D2 boundary:
all spawn decisions remain inside the main Code agent's turn loop,
where the composed G5 check (`pretooluse_git_deny.py`) gates them.

| # | Trigger | Subagent | Artifact kind |
|---|---------|----------|---------------|
| D1 | Cray ratifies a decision (in-conversation, no in-flight ADR draft) that warrants a new ADR | plan-drafter | adr |
| D2 | A multi-step plan needs to be drafted before execution (scope agreed, steps not yet structured) | plan-drafter | plan |

**Override clause (binding for the main agent):** if the agent's
judgment differs from the classifier (the dispatch was misrouted, the
work is not actually governance-drafting, or no D-row actually fits),
the agent does **not** spawn — instead, surface the misroute in a
short reply so Cray can review the trigger. Spurious dispatches are
worse than spurious pauses (they consume a subagent spawn).

**Conservative bias (classifier policy):** when in doubt between PAUSE
and DISPATCH, the classifier chooses PAUSE — same conservatism that
informs the proceed-vs-pause boundary. Spurious-pause-over-spurious-
dispatch is the design preference (PLAN-0009 Step 5c §Design).

**Chain-cap interaction:** a `dispatch` outcome counts toward the
stop-chain depth the same as a `proceed` (the dispatch is semantically
a continuation + instruction). At cap-hit, the Telegram alert fires
and the chain resets, same as the proceed-path cap behavior.

**Why these are not always-pause rows.** The G/C/H/L rows above are
always-pause because they cross hard governance/safety boundaries that
require Cray's judgment. The D-rows are *bounded structured drafting
tasks* whose output (a PR-ready uncommitted draft) Cray reviews at PR
merge time — moving the drafting work to a subagent does not skip Cray
review, it just removes the Cray-paste relay step (resolves PLAN-0008
OQ-D in-harness arm; cross-tab arm remains blocked by K-1/K-2 per
ADR-013 OQ-1).

## How the classifier reads this file (LIVE in Phase 2)

- The `Stop` hook (`stop_continuation.py`) reads this file path verbatim
  and dispatches the Sonnet classifier (`_sonnet_classifier.py`, pin
  `claude-sonnet-4-6`) to scan the agent's pending next action against
  the rows above. Match → pause + Telegram via the Notification flow;
  no match → proceed (block-stop returns the agent to the loop).
  Verified live 2026-05-24 conservatism probe (4/4 trigger scenarios
  paused with correct `matched_rows` G1/G2/C2 + 1/1 routine work
  proceeded). The classifier fails **closed** (pause + Telegram) on
  any unreachable / malformed-output path — 7 fail-paths covered.
- **Stop-side dispatch decisions (PLAN-0009 Step 5c-1, LIVE):** the
  Sonnet classifier now returns one of three decisions —
  `proceed` / `pause` / `dispatch`. The `dispatch` decision is paired
  with a `dispatch: {subagent, artifact_kind, task_summary}`
  sub-object that the `Stop` hook formats into a continuation
  instruction. Allowed `subagent` value today: `plan-drafter` only;
  allowed `artifact_kind` values: `adr` / `plan`. Schema violations in
  the dispatch metadata fail-closed to `pause` per the conservative
  policy. See the Auto-handoff triggers section above for the D-rows.
- **PreToolUse classifier dispatch (PLAN-0009 Step 5c-2, LIVE):**
  `.claude/hooks/pretooluse_classifier_dispatch.py` invokes the same
  classifier from the `PreToolUse` hook for `Write|Edit` events whose
  signature matches G1 (Edit on existing ADR/PLAN with
  `Status: Accepted`) or G2 (Write of a fresh
  `docs/(adr|plans)/NNNN-*.md`). A cheap deterministic pre-filter
  detects the signature before the API call so the classifier only
  fires on candidates. Decision mapping: `proceed` → allow (classifier
  overruled the pre-filter, legitimate context); `pause` → `deny`
  with citation; `dispatch` → `deny` with a spawn-redirect reason
  pointing at `plan-drafter` (the Pre-arm equivalent of the Stop-arm
  continuation instruction). Bypass-immune (PreToolUse `deny` fires
  regardless of `permissionMode` per ADR-013 D2 precedent). The
  on-disk file read defeats in-payload spoofing (the hook reads the
  real file, not the `tool_input`).
- Updates to this file **must** stay machine-readable: leading `#`/`|`
  table rows, no embedded HTML, no inline-code list-items inside table
  cells. The classifier reads it as plain text — content edits propagate
  on the next invocation without a hook change.

## Change protocol

1. Cowork drafts the new row (Tier 0 + Tier 1 + Tier-1b authoring per
   ADR-009 D1).
2. Code commits (ADR-009 D2).
3. Bump the row count in PLAN-0008+ if a Phase-2 classifier prompt
   change is required.
4. Cross-link from the originating ADR / lesson so future readers can
   trace WHY the row exists.

---

*Last updated: 2026-06-08 (Session 45 — L1 path-class threshold refinement: `l1_threshold_for` (6 code / 15 prose-doc) + subagent-completion L1 reset (`_handle_agent_completion`), after L1 false-fired on multi-section governance authoring; Cray-approved per-diff self-modification. See `docs/lessons/0021-l1-loop-detect-subagent-and-doc-threshold.md`. Previous: 2026-05-26 (Session 13 — PLAN-0009 Step 5c-2: PreToolUse classifier dispatch LIVE via `pretooluse_classifier_dispatch.py`; G1/G2 enforcement rows expanded with PreToolUse arm citation; "How the classifier reads this file" §flipped from "deferred to 5c-2" to "LIVE in 5c-2". Same-session: Step 5c-1 added **Auto-handoff triggers** section with D1/D2 rows + extended "How the classifier reads this file" §with the 3rd decision value `dispatch`. Previous: 2026-05-24 (Session 10 — PLAN-0008 Step 6 / Wave 2 completion: status banner flipped to Phase-2 LIVE; G1/G2/G3/G4 + C1/C2/C3 marked **Live** via `_sonnet_classifier.py`; L1–L4 marked **Live** via loop-detect + observer + Stop reset; "How the classifier reads this file" §flipped from spec → live with conservatism-probe evidence. Earlier: row C4 added 2026-05-24 — deterministic enforcement of Cowork research landing-zone rule after N=2 incident pattern; mirrors ADR-013 D2 precedent).*
