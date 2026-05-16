# Runbook: Code-tab transcript handoff (raw context → Chat/Cowork)

**Status:** Active (added Session 11, 2026-05-16)
**Audience:** Tier 2 (Code tab) operators
**Tooling:** `tools/handoffs/render_transcript.py` (stdlib-only, no deps)
**Related:** `docs/runbooks/claude-code-chat-handoff.md` (curated handoff
mechanism), Lesson #4 (WSL `bash -c` variable expansion), Lesson #5 §4
(handoff files gitignored by design)

---

## 1. Why this exists

Claude Code persists every session — assistant text, extended thinking,
tool calls, tool results — as an append-only JSONL file:

```
<host>/.claude/projects/<encoded-cwd>/<session-id>.jsonl
```

On this machine (Windows host + WSL2), from inside WSL that path is:

```
/mnt/c/Users/crayj/.claude/projects/--wsl-localhost-ubuntu-24-04-home-crayj-work-vero-lite/<session-id>.jsonl
```

`<encoded-cwd>` = the working-dir path with every non-alphanumeric
character replaced by `-`, lower-cased (see
`render_transcript.encode_project_path`). Large tool outputs spill to a
sibling `…/<session-id>/tool-results/<id>.txt`; the JSONL keeps a
`<persisted-output>` marker with the absolute path + a 2 KB preview.

The curated closeout handoff (per `claude-code-chat-handoff.md`) is still
the primary mechanism. This runbook covers the **complementary** case:
when the Code tab judges that the *full raw reply context* (including the
normally-collapsed process steps) should go to Chat or Cowork for
follow-up analysis — without manual expand-and-drag in the UI.

## 2. The added workflow step

When the Code tab decides a reply (or a span of work) should be handed to
Chat/Cowork for continuation:

1. Render the transcript to a handoff file:

   ```bash
   wsl -d ubuntu-24.04 -- bash -c 'cd /home/crayj/work/vero-lite && \
     .venv/bin/python tools/handoffs/render_transcript.py \
       /mnt/c/Users/crayj/.claude/projects/--wsl-localhost-ubuntu-24-04-home-crayj-work-vero-lite/<session-id>.jsonl \
       --out .claude/handoffs/session-NN/<YYYY-MM-DD>-<HHMM>-code-<topic>-transcript.md'
   ```

   **Finding the current session id (optional helper):**

   ```bash
   wsl -d ubuntu-24.04 -- bash -c \
     'ls -t /mnt/c/Users/crayj/.claude/projects/--wsl-localhost-ubuntu-24-04-home-crayj-work-vero-lite/*.jsonl | head -1'
   ```

   Newest `.jsonl` mtime = current Code-tab session. Useful when the
   session id was not captured at session start.

   - Pass the **explicit `.jsonl` path** (most robust across the
     WSL/Windows split). `--project-dir … --latest` also works.
   - Use `--last N` when only the final N turns matter; `--no-thinking`
     / `--no-tools` to trim; `--resolve-spill` to inline spill files.
   - Lesson #4: invoke with **literal paths, no `$var`** inside
     `wsl … bash -c '…'`.

2. The output filename follows the locked handoff convention
   (`code-` actor prefix; `transcript` is an extensible suffix beyond
   the core enum — see restart-bridge §4 / PLAN-004 Phase A). It lands
   under `.claude/handoffs/` which is **gitignored by design**
   (Lesson #5 §4) — it is a session-scoped working note, not a
   committed artifact.

3. **Always state the export path in the reply.** The tool prints
   `[render_transcript] exported -> <abspath>` to stderr; the Code tab
   reply must also include a line telling Cray exactly where the file
   is, so it can be picked up for Chat/Cowork without hunting. This is a
   standing convention, not optional.

## 3. What the rendered Markdown contains

- Preamble: session id, source path, generation time (UTC), record-type
  counts, rendered-turn count, active filters.
- One `## <role> · <timestamp> · <branch>` section per user/assistant
  turn (sidechain turns are marked `· sidechain`).
- `text`, `[thinking]`, `[tool_use]` (name + JSON input), and
  `[tool_result]` (with `(error)` flag) blocks, fenced for readability.
- Metadata-noise records (`queue-operation`, `attachment`, `ai-title`,
  `last-prompt`) are dropped.

## 4. Boundaries

- This is a **Tier 2 operational** convention, **binding via CLAUDE.md
  §11 "Transcript Handoff"** (promoted Session 11, commit `dd65d9b`).
  Runbook = procedural authority; CLAUDE.md §11 = constitutional trigger
  + invariant. The constitutional cycle followed Lesson #5 §1
  (Chat ratification post-hoc via the Cray-direct codification path —
  see Lesson #5 §2 sub-rule).
- The script never mutates the source JSONL and has no third-party deps.
- Quality gate: `tools/handoffs/render_transcript.py` +
  `tests/test_render_transcript.py` are ruff-clean, ruff-formatted, and
  mypy-strict clean per CLAUDE.md §8 (mypy pre-commit hook is scoped to
  `^services/`, so run mypy manually on `tools/` changes).
