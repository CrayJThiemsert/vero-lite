---
name: git-workflow
description: vero-lite git/commit/PR mechanics — how to write commit messages (file + `git commit -F`, never inline backtick heredoc), submit PR/issue/release bodies (`--body-file`, never `--body "$(cat …)"`), commit+push hygiene, recover a corrupted PR body, and commit from a Windows-created (UNC-gitdir) worktree where plain `wsl bash -lc "git …"` fails outright. Use whenever committing, pushing, or creating/editing a PR, issue, or release — and whenever a commit fails with `fatal: not a git repository: //wsl.localhost/...` or `` `pre-commit` not found ``. Encodes Lessons #4/#10/#11.
---

# Git workflow mechanics (vero-lite)

The **binding rules** live in `CLAUDE.md` §7 (conventional-commit format, branch
protection, all-commits-to-`main`-via-PR, canonical author, AI-assistance note).
This skill holds the **how-to + rationale + recovery** that you only need while
actually doing git/PR work.

## Commit messages — write to a file, then `git commit -F`

Never pass a multi-line / backtick / `$var` / code-block message inline.

- **Preferred:** Write tool against the WSL UNC path
  `\\wsl.localhost\Ubuntu-24.04\tmp\commit-message.txt`, then
  `git commit -F /tmp/commit-message.txt`.
- **Avoid:** `wsl bash -c "cat <<'EOF' … EOF"` heredocs when the message
  contains backticks, `$var`, or fenced code blocks.

*Why:* heredoc/inline expansion silently mangles backticks and `$` (Lesson #4).

## PR / issue / release bodies — `--body-file`, never `--body "$(cat …)"`

- Use `gh pr create --body-file PATH` (and the equivalent `--body-file` /
  `--notes-file` flags on `gh issue create`, `gh release create`,
  `gh pr edit`, `gh pr comment`).
- **Never** `gh pr create --body "$(cat PATH)"`.

*Why:* backticks inside the double-quoted shell arg trigger command substitution
and silently corrupt the submitted markdown body (Lesson #11).

**Recovery for an already-corrupted PR body:**
`gh api --method PATCH /repos/<owner>/<repo>/pulls/<N> -F body=@PATH`

**`gh pr edit` caveat (this repo):** `gh pr edit` aborts on a GraphQL
`projectCards` deprecation. For base/title/body changes use
`gh api --method PATCH /repos/<owner>/<repo>/pulls/<N> -f base=… -F body=@PATH`.

## Commit + push hygiene

- **Non-`main` branch target:** `git commit -F … && git push -u origin <branch>`
  chained is fine.
- **Landing on `main` via PR:** never chain commit with a push to `main` —
  commit on a branch first, then PR-flow.

*Why:* a chained command denied as a whole creates rework; auto-mode's classifier
guards direct push to the default branch unconditionally (Lesson #10).

## Toolchain note — which git, and from where

**Default: run git via `wsl bash -lc`.** The Bash tool's default
Git-for-Windows ships a stale CA bundle, so anything touching the network
(`push`, `fetch`) dies there. (See the project memory on the WSL git toolchain.)

⚠️ **That default assumes a WSL-native gitdir, and is wrong in a
Windows-created worktree** — see the next section before committing from one.

## Committing from a Windows-created worktree

A worktree created from the Code tab registers its `gitdir` as a UNC path
(`//wsl.localhost/ubuntu-24.04/...`). Both obvious routes then fail:

| Route | Failure |
|---|---|
| `wsl bash -lc "git commit …"` | `fatal: not a git repository: //wsl.localhost/...` — POSIX git collapses the leading `//` (Lesson #2 / #3 family A2) |
| Windows git (Bash tool default) | the hook fires — `hooksPath` resolves — then aborts `` `pre-commit` not found ``: `pre-commit`/`uv` are not on Windows' PATH |

**Fix — point WSL git at the *same* hooks via a POSIX-resolvable path:**

```bash
export GIT_DIR=/home/crayj/work/vero-lite/.git/worktrees/<name>
export GIT_WORK_TREE=/home/crayj/work/vero-lite/.claude/worktrees/<name>
git -c core.hooksPath=/home/crayj/work/vero-lite/.git/hooks commit -F /tmp/msg.txt
```

- ✅ **This is not a `--no-verify` bypass.** Hooks run normally —
  `detect-secrets` and the repo guards all fire. `--no-verify` stays forbidden
  (CLAUDE.md §8); this recipe exists so you never need it.
- **`gh` needs `GIT_DIR` exported too.**
- **Push through WSL** — Windows git dies on the network leg (stale CA bundle).

**If it aborts with `` Unable to create '…/index.lock': File exists ``** inside
pre-commit's `git write-tree`: **verify `HEAD` first — the commit did not
land — then simply retry.** Measured session 230: identical command, first
attempt aborted, second committed with every hook green. **Never delete the
lock file** to "fix" it; confirm via `git log` that no commit happened and let
the retry take a fresh lock.

⚠️ **Do not reach for Lesson #3's fallbacks here.** Its trap A3 has the *same*
`pre-commit not found` symptom but a different cause (a stale POSIX-path hook
vs a Windows-layout venv) and a different fix (inline `PATH=`). And its Branch-4
fallback `cd`s to `/home/crayj/work/vero-lite` — **the main checkout, not your
worktree** — so it commits the wrong tree if you are in one. Worse, that
checkout is often held by a concurrent session with uncommitted work.

*Measured session 229 (2026-08-14) committing PRs #1153/#1154 from
`.claude/worktrees/`; re-confirmed session 230.*

## References

- `CLAUDE.md` §7 (binding rules), §8 (`--no-verify` prohibition)
- Lessons #4 (commit-message backtick mangling), #10 (classifier blocks direct
  push to `main`), #11 (`gh pr` body-file backtick trap)
- Lessons #2 / #3 (UNC-gitdir binding + worktree lifecycle traps) — the cause
  behind the Windows-created-worktree section, and the two look-alike fixes it
  warns you off
