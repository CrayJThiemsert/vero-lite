# Execution Plans

This directory holds execution plans for vero-lite work.

## Workflow

1. New work needed → write a PLAN in `docs/plans/NNNN-name.md` (use [`0000-template.md`](0000-template.md))
2. Plan must include: **Goal**, **Acceptance Criteria**, **Out of Scope**, **Steps**, **Verification**
3. Status transitions: `Draft` → `Ready for execution` → `In progress` → `Complete`
4. Claude Code executes plan in feature branch, referencing the plan + relevant ADRs in commit messages
5. After completion, `git mv docs/plans/NNNN-*.md docs/plans/done/`

## Layout

```
docs/plans/
├── 0000-template.md             # template (do not modify in-place)
├── PLAN-NNNN-<name>.md          # active plans
└── done/                        # completed plans (move here after execution)
```

## Why plans?

Detailed plans **before** implementation = 3–10x token savings in Claude Code sessions. Each session needs:

- A clear plan
- ADR references
- Acceptance criteria
- Out-of-scope items, explicit

See [`CLAUDE.md`](../../CLAUDE.md) for the full project constitution.
