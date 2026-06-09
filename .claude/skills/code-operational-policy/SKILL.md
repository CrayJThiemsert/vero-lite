---
name: code-operational-policy
description: Tier 2 (Code) tactical operating policy for vero-lite — when to turn git worktree mode ON vs OFF, and how to render a transcript handoff to Chat/Cowork. Use when deciding worktree isolation for a task, or when handing a reply/work span off to another tier. Other tiers do not need this.
---

# Tier 2 (Code) operational policy

Tactical policy specific to Tier 2 (Code) execution. This is procedure, not a
constitutional rule — it loads on demand. The constitutional pointer lives in
`CLAUDE.md` §11.

## Worktree mode

Default policy per Lesson #3:

| Scenario | Worktree | Rationale |
|----------|----------|-----------|
| Single-task work (ADR draft, doc edit, single commit) | **OFF** | Avoid Family B traps (sandbox ownership cascade); zero isolation benefit |
| Parallel work (multiple branches in flight, risky refactor) | **ON** | Isolation worth the lifecycle cost; apply Lesson #3 prevention checklist |
| Buildable code that should fail-isolated in CI | **ON** | PR boundary clarity; explicit pre-flight required |

Apply the [Lesson #3 prevention checklist](../../../docs/lessons/0003-code-tab-worktree-lifecycle-traps.md#prevention-checklist)
before any worktree-on session.

## Transcript handoff

When the Code tab judges that a reply or span of work should be handed to Chat
or Cowork for follow-up, render the full raw transcript via
`tools/handoffs/render_transcript.py` into `.claude/handoffs/session-NN/`
(gitignored working note) and **always state the export file path in the reply**.

Procedure + options: [`docs/runbooks/transcript-handoff.md`](../../../docs/runbooks/transcript-handoff.md).

## References

- `CLAUDE.md` §11 (constitutional pointer)
- Lesson #3 (worktree lifecycle traps + prevention checklist)
- `docs/runbooks/transcript-handoff.md`
