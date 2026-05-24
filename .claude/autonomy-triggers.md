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

| # | Trigger | Phase 1 enforcement | Phase 2 enforcement |
|---|---------|---------------------|---------------------|
| G1 | Mutate any ADR with `Status: Accepted` | Advisory (agent judgment) | **Live** — `_sonnet_classifier.py` (Sonnet @ `Stop` via `stop_continuation.py`) |
| G2 | Consume / earmark an ADR or PLAN number | Advisory | **Live** — `_sonnet_classifier.py` |
| G3 | Read / touch `docs/strategy/private/**` | Advisory + gitignored at FS layer | **Live** — `_sonnet_classifier.py` |
| G4 | Scope override past ratified tier boundaries (Tier 0/1/1b/2 per ADR-009) | Advisory | **Live** — `_sonnet_classifier.py` |
| G5 | `git commit` / `git push` / `git merge` | **Deterministic** (`pretooluse_git_deny.py`, ADR-009 D2 / ADR-013 D2) | Deterministic + classifier mirror |

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
turn-boundary reset (`stop_continuation.py`). Threshold ≥ 6 attempts
per `(loop_type, target)`; on trigger the Telegram payload contract is
`{loop_type, target, last_6_actions}` per ADR-013 / Cray E.4.

| # | Trigger (same `(tool, target)` ≥ 6 attempts in one session) | Phase 1 | Phase 2 |
|---|--------------------------------------------------------------|---------|---------|
| L1 | Same file edited ≥ 6 times in one turn | Manual observation only | **Live** — `pretooluse_loop_detect.py` (gate) + `posttooluse_progress_observer.py` (writer) + `stop_continuation.py` (turn-boundary reset) |
| L2 | Same test fails ≥ 6 times consecutively | Manual | **Live** — `posttooluse_progress_observer.py` (inline Telegram fire on trigger) |
| L3 | Same error signature ≥ 6 times | Manual | **Live** — `posttooluse_progress_observer.py` (inline fire; auto-reset deferred — see PLAN-0008 §Step 8) |
| L4 | Same Bash command pattern fails ≥ 6 times | Manual | **Live** — `pretooluse_loop_detect.py` (gate) + `posttooluse_progress_observer.py` (writer) |

**Payload contract (Phase 2):** when a loop trigger fires, the Telegram
ping carries `{loop_type, target, last_6_actions}`. State storage:
`.claude/state/loop-counter.json` (gitignored — see `.gitignore`).
Reset on observable progress (test passes; target untouched the next
turn). Loop-type taxonomy above is Cowork-scoped; Code refines in
Phase 2.

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
- The `PreToolUse` classifier dispatch (for non-G5 rows that can be
  classified pre-tool, e.g., G1 ADR mutation via `Edit`) is **deferred
  to PLAN-0009+** (subagent topology); Phase 2 ships the `Stop`-side
  dispatch only.
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

*Last updated: 2026-05-24 (Session 10 — PLAN-0008 Step 6 / Wave 2 completion: status banner flipped to Phase-2 LIVE; G1/G2/G3/G4 + C1/C2/C3 marked **Live** via `_sonnet_classifier.py`; L1–L4 marked **Live** via loop-detect + observer + Stop reset; "How the classifier reads this file" §flipped from spec → live with conservatism-probe evidence. Previous: row C4 added 2026-05-24 — deterministic enforcement of Cowork research landing-zone rule after N=2 incident pattern; mirrors ADR-013 D2 precedent).*
