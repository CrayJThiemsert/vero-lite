# Runbook: Claude Code ↔ Claude Chat File-Based Handoff

**Adopted:** Session 9 (2026-05-09) after multiple Phase G fidelity-loss incidents
**Audience:** Anyone collaborating with both Claude Code (Desktop, Code tab) and Claude Chat (claude.ai) on vero-lite
**Goal:** Eliminate copy-paste fidelity loss for long structured outputs

---

## 1. Why this exists

Three observed failure modes during Sessions 8–9:

1. **Tool output ≠ chat reply.** When Code tab runs a command, the output appears in the user's terminal pane but is **not visible to Chat** unless the user copy-pastes it. Code tab agents have wrongly assumed otherwise.
2. **Long outputs truncate.** Notification streams cut off at message-size limits; full hook output for a 10-hook pre-commit run never reaches Chat intact.
3. **Copy-paste rendering drift.** Markdown auto-linkification, code-fence handling, and hidden whitespace cause `str_replace`-style operations to fail silently when content round-trips through chat clients.

Files under `.claude/handoffs/` solve all three: the file is the artifact, both sides read it directly, no transcription happens.

## 2. When to write a file vs. reply inline

| Situation | Choice |
|-----------|--------|
| One-sentence answer, simple ack | Inline reply |
| Decision waiting on user (≤3 short options) | Inline reply |
| Phase report (commands + output + interpretation) | **File** |
| Tool output > 30 lines | **File** |
| State snapshot intended for the next session | **File** |
| Code review of a file already in the repo | Inline reply (refer to file path + line) |

**Rule of thumb:** if a Chat reviewer would benefit from word-search or scrolling, write a file.

## 3. Location and naming

```
.claude/handoffs/
├── .gitignore           # tracked: default-ignore + exceptions
├── README.md            # tracked: pointer to this runbook
└── session-NN/
    └── YYYY-MM-DD-HHMM-task-slug.md
```

- `session-NN` matches `docs/STATUS.md` `session:` field.
- Timestamp is the file's creation time in local TZ (Asia/Bangkok).
- Slug is short kebab-case noun phrase: `phase1-diagnostic`, `lesson-14-draft`, `commit-fail-investigation`.
- One file per logical handoff; do not append to closed files.

## 4. Template

### Status enum

| Value | Meaning |
|-------|---------|
| `complete` | All work in this handoff is done; no recipient action needed |
| `partial` | Some sub-tasks done, more remain in same phase |
| `blocked` | Cannot proceed without recipient decision or external action |
| `needs-decision` | Decision points are listed in "Open questions"; recipient picks |

### Body template

```markdown
---
from: claude-code
to: claude-chat
session: 9
phase: G.B.1
status: blocked
created: 2026-05-09T18:00:00+07:00
title: Phase G B.1 — commit fail at ref lock permission denied
---

# {Title}

## Summary
> 1–3 sentences. Lead with outcome.

## Context
What was attempted, what was approved. Reference prior phase/file/commit.

## Commands run
\`\`\`bash
# verbatim
\`\`\`

## Output
\`\`\`
# verbatim, redirect-captured when notification truncation risk exists
\`\`\`

## Interpretation
Code tab's reading. Distinguish facts (from output) vs inferences.

## Open questions for recipient
1. ... (omit if status=complete with no pending decision)

## State at time of writing
- Git: branch, HEAD short hash
- Files pending: M/A/?? counts
- ≤6 lines total
```

## 5. Lifecycle

1. **Write** — Code tab uses `Write` tool to create the file at the canonical path.
2. **Notify** — Code tab's chat reply mentions the path (`.claude/handoffs/session-09/...`) so Chat knows to read it.
3. **Read** — Chat (or future Code tab session) opens via the `view` tool / file read.
4. **Respond** — Chat replies inline OR writes a counter-handoff (`from: claude-chat`).
5. **Close** — When the handoff's `status` reaches `complete`, no further edits. Future references cite the file by path + commit (if archived).
6. **Cleanup** — End-of-session, prefer **rotation** (see §6) over deletion. The dir is gitignored either way, so retention has no repo cost.

## 6. Handoff rotation policy

To prevent `.claude/handoffs/` from accumulating indefinitely in the active working area while preserving the historical record, handoffs are organised by session and archived at session boundaries.

### Directory structure

```
.claude/handoffs/
├── .gitignore               # tracked: default-ignore + exceptions
├── README.md                # tracked: pointer to this runbook
├── session-NN/              # current session (active, gitignored)
│   └── YYYY-MM-DD-HHMM-<title>.md
└── archive/
    ├── session-NN-1/        # closed sessions (preserved, gitignored)
    └── session-NN-2/
```

### Rotation procedure

At the start of each new session (Step 1 of session execution):

1. Move the previous session's directory into `archive/`:
   ```bash
   mv .claude/handoffs/session-NN .claude/handoffs/archive/session-NN
   ```
2. Create the new session directory:
   ```bash
   mkdir -p .claude/handoffs/session-$((NN+1))
   ```
3. No commit needed — entire `.claude/handoffs/` tree (apart from `.gitignore` and `README.md`) is gitignored.

Use plain `mv`, not `git mv` — the contents are not tracked.

### Rationale

- **Bounded active scope** — each session sees only its own handoffs in the working area, reducing context noise.
- **Historical preservation** — `archive/` retains all prior handoffs for cross-session reference and audit.
- **Zero git footprint** — gitignored throughout, no commit overhead per rotation.
- **Symmetric for Code and Chat** — both sides follow the same convention, avoiding drift.

### When to deviate

If a handoff in `session-NN` is referenced heavily across sessions (e.g., becomes a recurring runbook reference), promote it to a proper location under `docs/` and remove from handoffs entirely. Cross-session value belongs in tracked docs, not in gitignored working notes.

## 7. Cross-references

- `CLAUDE.md` § 6 (Working Patterns) — Conversation Hygiene rule (Code tab vs Chat roles). **Proposed amendment:** add a sentence to the "Rule" line: *"For long structured outputs, write to `.claude/handoffs/` instead of copy-pasting — see `docs/runbooks/claude-code-chat-handoff.md`."*
- `docs/runbooks/claude-code-setup.md` § 4 (Daily Workflow) — describes the two-tool decision; this runbook complements with the file-based bridge.
- `docs/lessons/0001-precommit-environment.md` Trap 6 — copy-paste fidelity failure (the original symptom this runbook addresses).

## 8. Anti-patterns

- ❌ Writing handoffs inside an active worktree (`.claude/worktrees/<name>/.claude/handoffs/`). They get lost on worktree removal. **Always main repo path.**
- ❌ Committing handoff files (other than `README.md`/`.gitignore`). They are session-scoped working notes, not historical record.
- ❌ Appending to a closed (`status: complete`) file. Write a new one and reference the old.
- ❌ Skipping the front-matter. The metadata is what makes the file machine-discoverable.
