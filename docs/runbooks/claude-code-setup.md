# Runbook: Claude Code in Desktop — Setup & Daily Use

**Last verified:** Session 8 (2026-05-08), Claude Code in Desktop v1.6608.0
**Audience:** vero-lite contributors using Claude Code through the Claude Desktop app (Code tab)
**Scope:** Windows 11 host + WSL2 Ubuntu 24.04 worktree (the founder's primary dev configuration)

---

## 1. Overview

Claude Code in Desktop is the **Code tab** integrated into the Claude Desktop application. It runs the same agent harness as the standalone Claude Code CLI, but bundled inside the desktop app together with the chat tab and the side-panel features (terminal, diff viewer, side chat).

**Why Code tab over CLI for vero-lite:**

| Concern | CLI | Code tab |
|---------|-----|----------|
| Repo file edits | Direct | Direct (same agent) |
| Visual diff before commit | Terminal-only (`git diff`) | Built-in diff viewer |
| Side chat for "what does this do?" | Separate Chat session | `Ctrl+;` inline |
| Integrated terminal | Separate window | `Ctrl+\`` inline |
| Worktree isolation per session | Manual `git worktree` | Automatic worktree per session |
| Multi-session context bleed | Easy to mix | Each session = isolated worktree |

The CLI remains useful for headless/SSH contexts. For the founder's day-to-day Windows + WSL2 workflow on Cray-Legion5Pro, the Code tab is preferred because it removes the manual paste-between-Chat-and-Code workflow that earlier sessions used.

**What this runbook does NOT cover:**
- Standalone Claude Code CLI installation (different binary, different PATH setup).
- Running on macOS or Linux desktop — the WSL ownership trap (§ 8) is Windows-specific.
- Claude API / SDK usage from inside vero-lite code (separate concern).

---

## 2. Prerequisites

| Component | Minimum | Notes |
|-----------|---------|-------|
| Claude Desktop | v1.6608.0 or later | Code tab + worktree isolation must be present. |
| Subscription | Max plan | Required for Code tab access at time of writing. |
| Git for Windows | 2.45.x or later | The Code tab's Bash tool calls `/mingw64/bin/git`, **not** WSL git. |
| WSL2 | Ubuntu 24.04 (or any) | Repository lives at `~/work/vero-lite` inside WSL. |
| `safe.directory` config | `*` (wildcard) | Resolves the dubious ownership trap — see § 8 and Lesson #2. |
| Windows username | Any | UNC paths use the WSL username, not the Windows one. |

**Critical pre-flight check** (run once on the Windows host PowerShell, not inside the worktree):

```powershell
git config --global --add safe.directory '*'
git config --global --get-all safe.directory   # verify '*' present
```

Without this, every git operation inside the Code tab fails with `fatal: detected dubious ownership in repository at '//wsl.localhost/...'`. The wildcard is the only entry that reliably matches every Claude-generated worktree subdirectory (which uses random session names).

For the trade-off analysis (`*` vs exact path vs scoped wildcard), see Lesson #2 (`docs/lessons/0002-claude-code-desktop-wsl-ownership.md`).

---

## 3. First-Time Setup

### 3.1 Open the Code tab

1. Launch Claude Desktop.
2. Top of the window, switch tab from **Chat** to **Code**.
3. The repo selector appears.

### 3.2 Select the vero-lite repository

The Code tab expects a path. Use the WSL UNC form:

```
\\wsl.localhost\ubuntu-24.04\home\crayj\work\vero-lite
```

Note the lowercase `ubuntu-24.04`. Even though Windows paths are case-insensitive, Git for Windows compares `safe.directory` byte-exactly — `Ubuntu-24.04` (capital U) does **not** match. Stick with whatever case appears in the actual UNC path; the Code tab tends to lowercase it automatically.

When a session opens, the Code tab automatically creates a worktree under:

```
.claude/worktrees/<adjective-surname-hash>/
```

(e.g. `sad-northcutt-6a48ff`). The session works on a dedicated branch `claude/<worktree-name>` so the main repo's `main` branch is never disturbed.

### 3.3 Smoke test

Once the session is open, run a read-only smoke test before any real work:

```bash
pwd
git rev-parse --show-toplevel
git rev-parse --git-dir
git branch --show-current
git log -3 --oneline
```

Expected:
- `pwd` ends in `.claude/worktrees/<session-name>`
- `--show-toplevel` matches `pwd`
- `--git-dir` points to the **main repo's** `.git/worktrees/<session-name>` (worktree gitdir lives in main repo, not the worktree itself)
- Branch is `claude/<session-name>`
- `git log` shows the latest known commit on `main`

If any of these fail with `fatal: detected dubious ownership`, return to § 2 — `safe.directory '*'` is missing or did not apply.

---

## 4. Daily Workflow — Three-Tool Decision Table

vero-lite has three Claude surfaces. Each has a job; mixing them creates the conversation-hygiene problem CLAUDE.md § 6 warns about.

| Tool | Use for | Avoid for | Output |
|------|---------|-----------|--------|
| **Claude Chat** (claude.ai) | Thinking partner; ADR drafts; design discussion; brainstorming options | Direct repo edits; "do this for me" | Markdown drafts, decisions, prompts to feed Code tab |
| **Claude Code in Desktop** (Code tab) | Implementation; running tests; reviewing diffs; commits | Open-ended exploration that takes 30+ messages | Code commits, file edits, test runs |
| **Cowork** (was: planned) | _Skipped — see § 10_ | — | — |

**Rule of thumb:** The boundary between Chat and Code is "intent decided vs. intent forming." If the goal is still being shaped, stay in Chat. Once the prompt is concrete enough to paste verbatim ("create file X with sections Y and Z, then run tests"), move to Code.

**Phase-based prompts** are the durable habit that came out of Session 8: each Code tab interaction is structured as `[Phase X.Y — short label]` with explicit READ-ONLY vs WRITE scope, an objective, an expected report format, and stop conditions. This costs ~50 tokens of prompt overhead and saves several rounds of "wait, were we supposed to commit yet?". See Session 8 transcript for the canonical example.

---

## 5. Useful Features (Code Tab Specifics)

### Multi-session + worktree isolation
Each Code tab session creates its own worktree on its own branch. You can run two sessions in parallel — one for documentation, one for code — without either seeing the other's pending changes. Caveat: the founder's Max plan caps practical parallelism at 2 sessions before token cost gets visibly punishing (see § 6).

### Side chat — `Ctrl+;`
Opens a small side-panel chat against the same model without the Code tab's filesystem tools. Use it for "explain this regex" or "what's the SQL for X?" without burning Code tab context. Side chat answers don't go into Code tab memory, so don't paste long answers back — just take the gist.

### Integrated terminal — `Ctrl+\``
A real WSL terminal, **not** the Code tab's sandboxed Bash tool. Use this for:
- Anything that needs interactive input (e.g., `gh auth login`, `psql` REPL).
- `sudo` commands (the agent's Bash tool runs sandboxed and can't elevate).
- Long-running processes you want to keep open (e.g., `docker compose up`).

The agent **cannot** see the integrated terminal's output. If a command's result matters for the next agent step, run it through the Bash tool, not the integrated terminal.

### Diff viewer
Before any commit, open the diff viewer (button in the bottom-right). Reviewing the diff visually catches:
- Files written with wrong indentation (CRLF vs LF — see Lesson #1 Trap 4).
- Accidental changes to unrelated files.
- Generated files that shouldn't be committed (e.g., `.env`, `__pycache__`).

### PR monitoring (optional)
The Code tab can stream PR status from `gh` if `gh auth status` succeeds inside the Bash tool. Useful for `/babysit-prs`-style workflows but not yet adopted in vero-lite.

---

## 6. Token Economy

Code tab sessions consume tokens roughly 2–4× faster than chat-only sessions because every message includes file reads and tool outputs in context.

**Rules learned from Session 8:**

1. **Close finished sessions.** A session left idle still re-reads CLAUDE.md and STATUS.md on every wake-up. After a logical task completes (commit pushed, PR open), close the tab.
2. **Cap parallelism at 2.** Three or more concurrent worktree sessions tends to blow through the daily quota by mid-afternoon.
3. **Use phase-based prompts.** A 5-line phase header (`READ-ONLY`, scope, expected report) saves ~3–5× the tokens it costs because the agent stops asking "what's the next step?" between actions.
4. **Long context dumps belong in the repo.** If a Chat session produces a 2KB design doc, save it as `docs/plans/NNNN-...md` and reference the path in the Code tab prompt. Never paste the body verbatim — it bloats context permanently.
5. **`/clear` between unrelated tasks.** Switching from "set up X" to "fix bug in Y" is a context boundary; clearing the Code tab session resets the cache. (Worktree isolation handles this for separate sessions, but `/clear` is the lighter option within one session.)

---

## 7. Known Behaviors (Verified Session 8)

These are characteristics of Claude Code in Desktop v1.6608.0 verified during the Phase B → Phase F walkthrough on 2026-05-08. They are not guarantees about future versions but accurately describe current observed behavior.

### 7.1 Rule respect
The agent reads `CLAUDE.md` at session start and applies its rules. Phase B's READ-ONLY constraint was honored across four rounds of git troubleshooting — the agent flagged every state-changing option (e.g., `git config --global --add safe.directory ...`) and asked for approval rather than running it silently.

### 7.2 Permission asking
Before running any command that modifies state outside the worktree (global git config, env vars, system PATH), the agent presents the proposed command + trade-offs and waits for explicit approval. This is documented as a feedback memory on this machine and is now standing guidance — see `feedback_state_change_outside_worktree.md`.

### 7.3 Feedback memory
The agent maintains a separate per-project memory store under `~/.claude/projects/<encoded-path>/memory/` containing user/feedback/project/reference notes. Memory complements but never replaces the repo's `docs/`. Conflicts resolve in favor of the repo (CLAUDE.md § 4).

### 7.4 Citation discipline
When asked to summarize CLAUDE.md, ADR, or STATUS.md content, the agent quotes file + line/section rather than paraphrasing. Phase C verified this: every answer in the comprehension test cited the source line.

### 7.5 Constitution > prompt
When a prompt instruction conflicts with CLAUDE.md (the canonical example: `Co-Authored-By: Claude` is forbidden by § 7), the agent flags the conflict instead of obeying silently. Override requires a new ADR, not an ad-hoc prompt.

---

## 8. Limitations & Gotchas

### 8.1 WSL ownership trap (the big one)
Documented in detail in Lesson #2. Summary: Git for Windows refuses to operate on WSL UNC paths until `safe.directory '*'` (or an exact match for every worktree subdirectory) is set in the global config. Adding the parent directory or a glob like `.../worktrees/*` does **not** work — `safe.directory` is byte-exact match with no recursion and no glob support.

### 8.2 Worktree branch UI bug (cosmetic)
The Code tab's status bar sometimes shows the main branch name (`main`) even though the worktree is on `claude/<session-name>`. `git branch --show-current` always returns the truth; trust the command, not the UI.

### 8.3 Open-in-VSCode bug
Right-click → "Open in VSCode" on a file in the Code tab opens VSCode pointing at the worktree path. VSCode's git integration then sees the worktree as a detached repo and can fail to commit. Workaround: open VSCode pointed at the **main repo path** (`~/work/vero-lite`) and navigate to the worktree directory manually if needed.

### 8.4 Computer-use preview
The Claude Desktop computer-use feature is a preview and is granted at the "read" tier for browsers (read screenshots only, no clicks). For interactive browser work, install the Claude in Chrome extension. None of this is required for vero-lite's current workflow but is worth knowing before assuming "the agent can drive my browser."

### 8.5 Routines / scheduled tasks preview
The schedule MCP (one-shot or recurring agent runs) is preview-grade. Not adopted for vero-lite — too immature for medical-data-handling discipline.

### 8.6 Token consumption
Already noted in § 6. Repeated here because it is the single biggest gotcha for solo founders on Max plan.

### 8.7 Heavy tool inventory at session start
Each Code tab session loads ~80+ MCP tools (computer-use, browser, schedule, etc.) into the deferred tool list. They cost no tokens until invoked, but they do widen the agent's option space. If a session feels distracted by tool variety, prune via `/permissions` or the project's `.claude/settings.json`.

---

## 9. Memory Architecture Integration

vero-lite's memory architecture defines five tiers (CLAUDE.md § 4). The Code tab's per-project memory store is **Tier 0** — private, machine-local, never committed. The repo (Tiers 1–3) remains the single source of truth.

| Tier | Lives | Examples in this session |
|------|-------|--------------------------|
| 0 (private) | `~/.claude/projects/.../memory/` | `feedback_state_change_outside_worktree.md`, `MEMORY.md` |
| 1 (hot, repo) | `CLAUDE.md`, `docs/STATUS.md` | Both updated this session |
| 2 (reference, repo) | `docs/{adr,lessons,runbooks,conventions}/` | This runbook + Lesson #2 added this session |
| 2.5 (derived) | `docs/for_llm/` | Not touched this session |
| 3 (archeology) | `docs/plans/done/`, git history | Will receive Session 8 plan once Task 1 closes |

**Practical rule:** When a fact would be useful to a future Claude Code session on this exact machine, write it to Tier 0. When it would be useful to any contributor (including a future founder reading their own repo six months later), write it to Tier 1 or 2. The runbook you are reading is Tier 2.

---

## 10. Future Considerations

Things deliberately deferred from Session 8 setup, with one-line rationale each:

- **Skills** — Custom skills (project-specific reusable workflows) are powerful but require an investment in skill definition. Defer until vero-lite has 3+ recurring multi-step workflows worth automating (e.g., "draft new ADR", "run full pre-commit + push").
- **Connectors** — MCP connectors to external services (Linear, Slack, etc.) are not relevant for solo-founder phase. Reconsider when first design partner is on board and async coordination becomes real.
- **Routines / scheduled tasks** — Mentioned in § 8.5. Still preview. Defer indefinitely until the medical-data-handling story for unattended agent runs is clearer.
- **Cowork** — Originally on the Session 8 TODO list. Skipped because the Code tab covers the main use case (in-repo agent workflow with isolation). Cowork's collaborative features are a future concern when there is more than one human contributor.
- **Self-hosted GitHub Actions runner on MS-S1 MAX** — Carried over to Session 9+. Independent of Code tab adoption.

---

## Related

- `CLAUDE.md` § 4 — Memory Architecture (Tier 0 = Code tab private memory)
- `CLAUDE.md` § 6 — Working Patterns (Chat vs Code tab roles)
- `CLAUDE.md` § 7 — Git Conventions (commit message format, AI assistance note)
- `docs/lessons/0002-claude-code-desktop-wsl-ownership.md` — Lesson #2 (the safe.directory trap)
- `docs/runbooks/memory-architecture.md` — Cross-tool memory model
- Session 8 transcript (Phase B → Phase F) — canonical example of phase-based prompting
