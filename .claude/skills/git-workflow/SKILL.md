---
name: git-workflow
description: vero-lite git/commit/PR mechanics — how to write commit messages (file + `git commit -F`, never inline backtick heredoc), submit PR/issue/release bodies (`--body-file`, never `--body "$(cat …)"`), commit+push hygiene, and recover a corrupted PR body. Use whenever committing, pushing, or creating/editing a PR, issue, or release. Encodes Lessons #4/#10/#11.
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

## Toolchain note

Run git via `wsl bash -lc` — the Bash tool's default Git-for-Windows ships a
stale CA bundle. (See the project memory on the WSL git toolchain.)

## References

- `CLAUDE.md` §7 (binding rules)
- Lessons #4 (commit-message backtick mangling), #10 (classifier blocks direct
  push to `main`), #11 (`gh pr` body-file backtick trap)
- `docs/conventions/git.md` *(future canonical, see STATUS TODO)*
