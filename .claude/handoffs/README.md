# `.claude/handoffs/` — Code ↔ Chat handoff files

This directory holds **structured handoff files** exchanged between Claude Code (in Desktop, the Code tab agent) and Claude Chat (claude.ai, the design partner) within a vero-lite session.

The directory is **gitignored by default**. Only this `README.md` and the `.gitignore` are tracked.

## Why files instead of copy-paste?

Long Code-tab tool outputs do not travel cleanly through manual copy-paste:
- Notification streams truncate at message-size limits.
- Code blocks render differently in chat clients vs. terminal.
- Multi-step sessions create N-hop fidelity loss.

Writing a file → having Chat read it via the `view` tool eliminates the copy-paste path entirely.

## Quick rules

| Situation | Use |
|-----------|-----|
| Quick ack, single-line answer | Inline reply |
| Phase report, structured output, file dump | Write a file under `session-NN/` |
| State snapshot for next session pickup | Write a file (also gitignored — survives session boundary on disk) |

## File naming

```
session-NN/<YYYY-MM-DD>-<HHMM>-<task-slug>.md
```

Sortable chronologically; `task-slug` is short kebab-case (e.g. `phase1-diagnostic`, `pre-commit-fail-investigation`).

## Full documentation

See [`docs/runbooks/claude-code-chat-handoff.md`](../../docs/runbooks/claude-code-chat-handoff.md) for the template, lifecycle, and conventions.
