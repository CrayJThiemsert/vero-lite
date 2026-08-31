---
name: git-workflow
description: vero-lite git/commit/PR mechanics — how to write commit messages (file + `git commit -F`, never inline backtick heredoc), submit PR/issue/release bodies (`--body-file`, never `--body "$(cat …)"`), commit+push hygiene, recover a corrupted PR body, and commit from a Windows-created (UNC-gitdir) worktree where plain `wsl bash -lc "git …"` fails outright. Use whenever committing, pushing, merging, or creating/editing a PR, issue, or release — whenever a commit fails with `fatal: not a git repository: //wsl.localhost/...` or `` `pre-commit` not found ``, and whenever about to trust that a `git merge` landed its content (a merge can report success while dropping the incoming change, with `merge-base --is-ancestor` still answering YES). Also use whenever a git command reports success but the file does not change, when `git status` disagrees with what is on disk, or when a checkout/merge aborts on "local changes" you did not make — check first that git is pointed at the tree you are standing in. Encodes Lessons #4/#10/#11/#0053.
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

## Verify a merge by content, not by ancestry

A `git merge` can report success and still hand you a tree that **dropped the
incoming change**. Measured session 240 merging `origin/main` before #1226:

1. The merge first died with `Unable to write index` — although the two sides
   touched **disjoint** files.
2. `git status` then read *"All conflicts fixed but you are still merging"*,
   with **no `index.lock` on disk**.
3. Concluding it produced a merge commit whose tree had silently dropped
   **all** of #1225's `DEPLOY.md` change.
4. `git merge-base --is-ancestor origin/main HEAD` answered **YES** throughout.

**Ancestry is not content.** Reachability says the commit sits in your history;
it never says its lines are in your tree. So check the tree, not the graph —
grep the merged tree for a string only the incoming side introduces:

```bash
git show HEAD:path/to/file | grep -F 'a string only the incoming side adds'
```

**Recovery:** `git reset --hard` to your own pre-merge commit, then re-merge.
The second attempt reported the expected `53 insertions(+)` — a diffstat that
matches the incoming change is the positive signal the first merge never gave.

*Measured session 240 (2026-08-19), #1225 / #1226. Rehomed here session 248
under the R2 carve-out: this was tracked nowhere outside `docs/STATUS.md`.*

## Toolchain note — which git, and from where

**Default: run git via `wsl bash -lc`.** The Bash tool's default
Git-for-Windows ships a stale CA bundle, so anything touching the network
(`push`, `fetch`) dies there. (See the project memory on the WSL git toolchain.)

⚠️ **That default assumes a WSL-native gitdir, and is wrong in a
Windows-created worktree** — see the next section before committing from one.

## First — confirm git is pointed where you are standing

**Run this before diagnosing anything else** whenever a git command reports
success and the effect is absent, `git status` disagrees with the disk, or a
checkout/merge aborts on "local changes" nobody made:

```bash
cd /home/crayj/work/vero-lite && pwd && git rev-parse --show-toplevel
```

**Two different answers means every `status` / `diff` / `checkout` / `add` in
that shell is about a tree you are not looking at.** Measured session 266: a
stray `core.worktree` in the **shared** `.git/config` pointed the main checkout
at another session's worktree. `git checkout -- <paths>` returned `rc=0` and
wrote the files *there*; `git pull` reported `create mode` for a plan file that
never appeared. Six separate symptoms had already been written up across two
handoffs as a UNC stat-cache artifact (Lesson #0053).

Clear it with `git config --unset core.worktree` — but note `.git/config` is
**shared across every worktree**, so it is a repo-level change: get Cray's go
first.

**When `git status` itself is the thing under suspicion, audit by content:**

```bash
git ls-files > /tmp/paths.txt
git hash-object --stdin-paths < /tmp/paths.txt > /tmp/disk.txt
# join against `git ls-files -s` and compare blob hashes
```

That bypasses the stat cache *and* the worktree resolution. In session 266 it
found 6 stale files and 1 tracked file missing from disk that `git status` never
mentioned.

⚠️ **`git update-index --refresh` is NOT a read-only probe.** On a path whose
difference is a **mode** difference it writes the new mode into the index — two
files went from ` M` to `M ` (staged `100755`→`100644`) from a command run purely
to look. Undo with `git update-index --chmod=+x <paths>` and confirm with
`git diff --cached HEAD`.

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

🔴 **Use the environment variables above — never `git config core.worktree …`.**
`.git/config` is shared by the main checkout and every worktree, so setting
`core.worktree` there redirects *everyone's* git at your worktree, silently and
persistently. Measured session 266: it survived the session that set it, and the
next session spent ~15 measurements diagnosing the filesystem before checking
`git rev-parse --show-toplevel` (Lesson #0053). `GIT_WORK_TREE` is scoped to your
shell and cannot leak.

**If it aborts with `` Unable to create '…/index.lock': File exists ``** inside
pre-commit's `git write-tree`: **verify `HEAD` first — the commit did not
land — then simply retry.** Measured session 230: identical command, first
attempt aborted, second committed with every hook green. **Never delete the
lock file** to "fix" it; confirm via `git log` that no commit happened and let
the retry take a fresh lock.

⚠️ **If the retry keeps working but the lock keeps coming back, stop trusting
the recipe above and `ps` before retrying again.** Measured session 245: an
`index.lock` persisted for **four days** because a **SIGSTOP-suspended** git
process still held it — `STAT=T` (corroborated by `WCHAN=do_signal_stop`). A
suspended process is **not running**, so it never releases the lock and never
looks busy, while the retry above took a *fresh* lock and succeeded every single
time — which is exactly what hid the cause for four days. **A recurring lock is
a process problem, not a timing one.** The tell is the `T` state:

```bash
ps -o pid,stat,wchan:20,cmd -C git
```

`STAT=T` is the decisive signal; `WCHAN` corroborates but is not always
populated. Exit 1 with only a header means no git process is alive — then the
plain retry above really is the right move. _[Rehomed here s250 from
`docs/STATUS.md`, where the cause had survived only as state, not procedure —
the reader who needs it is whoever is staring at a stuck lock, and that reader
loads this skill, not the status archive.]_

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
