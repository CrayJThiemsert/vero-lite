# Curated context for LLM sessions

This directory holds **curated, hand-picked context** intended for LLM sessions (Claude Chat, Claude Code agents, MCP servers).

## Purpose

When starting a new Claude Chat or Claude Code session, you may want to paste in a focused subset of project context that fits in a single message — too much will dilute attention; too little will lose important nuance. Files in this directory are short, current, and intentionally optimized for being copy-pasted into a new conversation.

## Relationship to canonical docs

`for_llm/` files are **derived snippets** (Tier 2.5), not canonical sources.

| Source | Authority |
|--------|-----------|
| `CLAUDE.md`, `docs/STATUS.md` | **Canonical** — Tier 1, read every session |
| `docs/{adr,lessons,runbooks,conventions}/` | **Canonical** — Tier 2, reference material |
| `docs/for_llm/` | **Derived** — Tier 2.5, curated snippets |

**Rule:** If a `for_llm/` file conflicts with CLAUDE.md or `docs/`, the canonical source wins. Update or regenerate the `for_llm/` snippet to match.

See [`docs/runbooks/memory-architecture.md`](../runbooks/memory-architecture.md) for the full Tier model.

## Conventions

- **One topic per file** — e.g., `architecture-summary.md`, `current-priorities.md`, `glossary.md`.
- **Keep short** — target < 200 lines per file. If longer, split.
- **Reference, don't duplicate** — link to ADRs / plans rather than restate them.
- **Date every file** — every file should have a "_Last updated:_" line at the bottom.
- **Update or remove when stale** — stale curated context is worse than none.
- **Note the source** — every file should reference which canonical(s) it derives from.

## Files

(none yet — this directory is the staging area for future curated context)

---

_Last updated: 2026-05-07_
