# Autonomy Triggers Registry

> **Status:** Phase 1 of PLAN-0007 — *file + content shipped*. The Sonnet
> pause/proceed classifier that consumes this registry is **Phase 2**
> (PLAN-0008+); see [ADR-013](../docs/adr/0013-autonomy-axis-relocation.md)
> D4 + PLAN-0007 §"Step 6".
>
> **Authoritative source for autonomy decisions.** When the classifier is
> live, the `Stop` and `PreToolUse` prompts read this file verbatim. Edit
> here — **never inline the list into `settings.json` prompts** (rejected
> alternative per ADR-013 D4 — drift risk between the two hook prompts).
>
> **What is *deterministic* vs *classifier-mediated*.** Two rows below are
> already enforced deterministically by Phase-1 hooks; they are listed
> here for the classifier's belt-and-suspenders awareness but the hook is
> the hard guarantee:
>
> - `git commit / push / merge` from non-Code session — enforced by
>   `.claude/hooks/pretooluse_git_deny.py` (CLAUDE_TIER env marker).
> - `Write|Edit` to `.claude/handoffs/**` with bad frontmatter — enforced
>   by `.claude/hooks/posttooluse_validate_handoff.py`.
> - `Write|Edit` to `docs/research/` outside `private/` — enforced by
>   `.claude/hooks/pretooluse_research_path_deny.py` (row C4 below).
>
> Everything else on this list is **advisory / always-pause** in Phase 1
> (agent judgment), becoming classifier-enforced in Phase 2.

## Always-pause triggers

When ANY of the rows below matches an agent's intended next action, the
agent MUST pause, Telegram-ping Cray (via the Notification hook, once
the matching event type fires) or surface via handoff, and wait.

### Governance boundaries — from ADR-013 / direction-b §5

| # | Trigger | Phase 1 enforcement | Phase 2 enforcement |
|---|---------|---------------------|---------------------|
| G1 | Mutate any ADR with `Status: Accepted` | Advisory (agent judgment) | Classifier pause |
| G2 | Consume / earmark an ADR or PLAN number | Advisory | Classifier pause |
| G3 | Read / touch `docs/strategy/private/**` | Advisory + gitignored at FS layer | Classifier pause |
| G4 | Scope override past ratified tier boundaries (Tier 0/1/1b/2 per ADR-009) | Advisory | Classifier pause |
| G5 | `git commit` / `git push` / `git merge` | **Deterministic** (`pretooluse_git_deny.py`, ADR-009 D2 / ADR-013 D2) | Deterministic + classifier mirror |

### Config / dependency / wording boundaries — from Chat additions

| # | Trigger | Phase 1 enforcement | Phase 2 enforcement |
|---|---------|---------------------|---------------------|
| C1 | Model pin / version bump (ADR-001 Amendment 1 precedent) | Advisory | Classifier pause |
| C2 | New external dependency added to `pyproject.toml`, `package.json`, or any lockfile | Advisory | Classifier pause |
| C3 | Public ↔ private wording boundary crossing in `docs/strategy/{public,private}/**` | Advisory | Classifier pause |
| C4 | `Write` / `Edit` under `docs/research/` outside `docs/research/private/**` (Cowork research landing-zone rule, `cowork_tab_instructions.md` line 192 + `.gitignore` lines 49-51) | **Deterministic** (`pretooluse_research_path_deny.py`; N=2 incident pattern — Lesson #5 §10.5 + 2026-05-23 `chat_harness_extension_points_analyzed.md` → ADR-013 D2 precedent applied) | Deterministic + classifier mirror |

### Handoff hygiene — from PLAN-004 / Lesson #7 / direction-b §8

| # | Trigger | Phase 1 enforcement | Phase 2 enforcement |
|---|---------|---------------------|---------------------|
| H1 | `Write` / `Edit` to `.claude/handoffs/**` produces frontmatter that fails `validate_handoff.py` | **Deterministic** (`posttooluse_validate_handoff.py`) | Deterministic |

### Loop-detect (Cray E.4) — **Phase 2 enforcement** (registered in Phase 1)

Stateful loop-detection requires the `.claude/state/` design (loop-counter
file, reset-on-progress semantics) + the Phase-2 `Stop`/`PreToolUse`
classifier. Phase 1 ships the registry rows only.

| # | Trigger (same `(tool, target)` ≥ 6 attempts in one session) | Phase 1 | Phase 2 |
|---|--------------------------------------------------------------|---------|---------|
| L1 | Same file edited ≥ 6 times in one turn | Manual observation only | Enforced via `.claude/state/loop-counter.json` |
| L2 | Same test fails ≥ 6 times consecutively | Manual | Enforced |
| L3 | Same error signature ≥ 6 times | Manual | Enforced |
| L4 | Same Bash command pattern fails ≥ 6 times | Manual | Enforced |

**Payload contract (Phase 2):** when a loop trigger fires, the Telegram
ping carries `{loop_type, target, last_6_actions}`. State storage:
`.claude/state/loop-counter.json` (gitignored — see `.gitignore`).
Reset on observable progress (test passes; target untouched the next
turn). Loop-type taxonomy above is Cowork-scoped; Code refines in
Phase 2.

## How the classifier reads this file (Phase 2 spec, not Phase 1)

- The `Stop` hook prompt template references this file path verbatim
  and instructs the Sonnet classifier to scan the agent's pending next
  action against the rows above. Match → pause; no match → proceed.
- The `PreToolUse` hook (beyond the deterministic `pretooluse_git_deny.py`)
  inspects the candidate tool call against the same registry for non-G5
  rows that can be classified pre-tool (e.g., G1 ADR mutation via
  `Edit`).
- Updates to this file **must** stay machine-readable: leading `#`/`|`
  table rows, no embedded HTML, no inline-code list-items inside table
  cells.

## Change protocol

1. Cowork drafts the new row (Tier 0 + Tier 1 + Tier-1b authoring per
   ADR-009 D1).
2. Code commits (ADR-009 D2).
3. Bump the row count in PLAN-0008+ if a Phase-2 classifier prompt
   change is required.
4. Cross-link from the originating ADR / lesson so future readers can
   trace WHY the row exists.

---

*Last updated: 2026-05-24 (Session 10 — row C4 added: deterministic enforcement of Cowork research landing-zone rule after N=2 incident pattern; mirrors ADR-013 D2 precedent).*
