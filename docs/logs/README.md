# docs/logs/

Thin git-tracked summaries of working-tree events that need audit-trail
visibility but whose operator-grade detail lives outside repo history
(typically in gitignored `.claude/handoffs/` closeouts).

## Purpose

This directory exists because some events:

- Modify the working tree at scale (e.g. retro-migrating handoff
  frontmatter across many gitignored files)
- Produce no direct git artifact (the modified files are themselves
  gitignored)
- BUT still need audit-grade record on `origin/main` for future
  archeology (commit message + dated tracked file)

The pattern is **two-artifact evidence model** (PLAN-004 v2 D6):

1. **Gitignored closeout** — operator-grade detail at
   `.claude/handoffs/session-NN/<date>-<actor>-<topic>-closeout.md`
   (Code's per-file decisions, pre/post validator output, deviations)
2. **Git-tracked summary** — audit-grade thin summary at
   `docs/logs/<date>-<topic>.md` (this directory): event date, total
   file count, validator delta, rename pairs if any, pointer back to
   gitignored closeout

The gitignored closeout is operator working notes; the tracked
summary is the audit record.

## Distinct from

- `docs/lessons/` — durable patterns and learnings; should outlive
  any single event
- `docs/runbooks/` — operational guides for repeatable procedures
- `docs/adr/` — architecture decisions
- `docs/plans/` — multi-batch execution plans

## File naming

`<YYYY-MM-DD>-<topic>.md` where `<topic>` is a short kebab-case
identifier (e.g. `plan004-batch2a-migration`, `lesson-renumber-sweep`).

## Schema

No formal frontmatter schema required (these are tracked docs, not
handoffs). Recommended structure:

```markdown
# <Event title>

**Date:** YYYY-MM-DD
**Event type:** migration / sweep / cleanup / other
**Commit:** `<short-SHA>` (the commit this summary landed in, OR the
substantive commit this summary documents)
**Operator-grade detail:** `.claude/handoffs/session-NN/<...>` (gitignored)

## Summary

(1-3 paragraphs: what happened, scope, scale)

## Key metrics

(validator delta, file count, etc.)

## Reference

(pointer to gitignored closeout + any related ADRs/lessons)
```

## First entry

`docs/logs/2026-05-XX-plan004-batch2a-migration.md` — pending (PLAN-004
Phase A Batch 2 Step 2a migration; lands in Step 2a v2 dispatch).
