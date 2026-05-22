# Handoff Frontmatter Schema

**Status:** Active (PLAN-004 Phase A Batch 1, 2026-05-19)
**Authority:** `docs/plans/0004-handoff-frontmatter-and-dashboard.md` (D1–D5)
**Validator:** `tools/handoffs/validate_handoff.py`
**Reader:** `tools/handoffs/handoff_status.py`

This schema governs the YAML frontmatter block at the top of every
file under `.claude/handoffs/session-NN/`. Handoff files themselves
are gitignored per Lesson #5 §4; this schema doc and its tooling are
git-tracked.

## Required fields

| Field | Type | Notes |
|-------|------|-------|
| `from` | string | originating actor identifier |
| `to` | string | target actor identifier |
| `actor` | enum | `chat` \| `code` \| `cowork` \| `cray` |
| `session` | int | session number |
| `batch` | string | free-form batch identifier |
| `phase` | enum | `kickoff` \| `dispatch` \| `midflight` \| `closeout` \| `handoff` \| `discussion` |
| `status` | enum | `READY` \| `IN_PROGRESS` \| `PAUSED` \| `DONE` \| `NEEDS_INPUT` |
| `created` | ISO8601 datetime with TZ | e.g. `2026-05-19T02:00:00+07:00` |
| `title` | string | human-readable title |

## Optional fields

| Field | Type | Notes |
|-------|------|-------|
| `suffix` | enum | content-type token (see below); required when filename uses non-core suffix |
| `references_predecessor_handoffs` | list[string] | filenames of prior handoffs this continues |
| `references_session_batches_completed` | list[string] | batch descriptors completed by this handoff |
| `references_commits` | list[string] | short SHA references |

Unknown fields → validator warning, not error (forward-compat).

## `actor:` ↔ filename prefix discipline

| `actor:` value | Required filename prefix | Tier |
|----------------|--------------------------|------|
| `chat` | `chat-` | Tier 1 (Claude Chat) |
| `code` | `code-` | Tier 2 (Claude Code) |
| `cowork` | `cowork-` | Tier 0 (Claude Cowork) |
| `cray` | `cray-` | Tier 3 (Cray, direct codification per Lesson #5 §2) |

Validator enforces filename prefix matches `actor:` field.

## `phase:` enum (lifecycle role)

| Phase | Meaning |
|-------|---------|
| `kickoff` | session/batch initialization handoff |
| `dispatch` | Chat → Code (or Chat → Cowork) execute-this batch |
| `midflight` | recipient surfaces issue mid-execution (pause + ask) |
| `closeout` | recipient reports completion + acceptance criteria self-check |
| `handoff` | thread-to-thread state transfer |
| `discussion` | exploratory conversation file (no execute boundary) |

## `suffix:` enum (content-type token)

Core suffixes (locked):

| Suffix | Meaning |
|--------|---------|
| `closeout` | batch closeout report |
| `midflight` | mid-batch pause + surface |
| `kickoff` | session/batch initialization |
| `errata` | correction notice |
| `amendment` | retroactive edit notice |
| `addendum` | post-closeout supplement |

Extensible suffixes (registered, additions require PLAN-004 amendment):

| Suffix | Meaning | First use |
|--------|---------|-----------|
| `transcript` | full raw session transcript (per `docs/runbooks/transcript-handoff.md`) | Session 11, commit `dd65d9b` |
| `sync` | curated cross-tier sync handoff | Session 11, `2026-05-16-2210-code-chat-sync-transcript-tooling.md` |
| `restart-bridge` | constitutional-edit restart handoff (Lesson #5 §1) | Session 11, `2026-05-16-1337-code-session11-restart-bridge.md` |
| `dispatch` | Tier-1 execute / kickoff dispatch to Code (ADR-009 D1) | Session 10, `2026-05-20-1530-cowork-plan003-phase1-kickoff-dispatch.md` |
| `completion` | Tier-1 governance-artifact completion report (ADR / PLAN draft handed to Code) | Session 10, `2026-05-21-1130-cowork-plan0005-runtime-layer-completion.md` |
| `consultation` | pre-draft consultation Q&A round | Session 10, `2026-05-20-0215-chat-plan003-pre-draft-consultation.md` |

`dispatch` / `completion` / `consultation` were registered 2026-05-22
per C-2 resolution α (PLAN-004 D4 amendment). `discussion` is **not** a
suffix — per ADR-012, discussion handoffs use `phase: discussion` and
omit `suffix:`.

`phase:` ↔ `suffix:` distinction:
- `phase:` always present, answers "what stage of the batch?"
- `suffix:` present when content type is non-core, answers "what KIND of artifact?"

Example: Code → Chat sync = `phase: handoff` + `suffix: sync`.

## `status:` enum

| Status | Meaning |
|--------|---------|
| `READY` | dispatch authored, awaiting recipient action |
| `IN_PROGRESS` | recipient actively working |
| `PAUSED` | work halted pending re-dispatch |
| `DONE` | work complete, closeout filed |
| `NEEDS_INPUT` | blocked on Cray decision |

Validator does NOT verify status transitions; the reader infers chains
from file timestamps + `references_predecessor_handoffs`.

## Example frontmatter

```yaml
---
from: claude-chat-session-10-current-thread
to: claude-code-session-13
actor: chat
session: 10
batch: plan004-batch1-tooling
phase: dispatch
status: READY
created: 2026-05-19T02:00:00+07:00
title: PLAN-004 Phase A Batch 1 dispatch v2
references_predecessor_handoffs:
  - 2026-05-19-0049-chat-plan004-batch1-dispatch.md
  - 2026-05-19-0124-code-plan004-batch1-midflight.md
references_commits:
  - b81817b
---
```

## References

- `docs/plans/0004-handoff-frontmatter-and-dashboard.md` (PLAN-004 v2)
- Lesson #5 §2 (Cray-direct codification path)
- Lesson #5 §4 (handoffs gitignored by design)
- Lesson #6 (Code surface → Chat re-dispatch pattern)
- `docs/runbooks/transcript-handoff.md`
- `docs/runbooks/claude-code-chat-handoff.md`
