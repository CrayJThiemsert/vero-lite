# Lesson 0003: Code Tab Worktree Lifecycle on WSL — End-to-End Traps

**Captured:** 2026-05-09 (extracted from Session 9 Phase G — single PR took ~90 minutes due to 7 distinct traps)
**Context:** First end-to-end commit + push + merge cycle using Claude Code in Desktop (Code tab) with vero-lite repo on WSL2
**Severity:** High — every step from `git add` through `gh pr merge` to worktree cleanup hit a different blocker; without this lesson, Session 10 would re-discover the same traps

---

## Summary

A single docs-only PR (3 files, +400/-14 lines) was expected to take 5–10 minutes. It took 90 minutes because the Code-tab-on-WSL setup has **seven distinct traps** distributed across the worktree lifecycle. The traps are not random — they cluster into three root-cause families, each with a unified fix pattern.

This lesson documents the families, the lifecycle stages where each surfaces, and the diagnostic decision tree for distinguishing them. It does not duplicate Lesson #12's coverage of the entry-point dubious-ownership trap; instead, it covers everything that can go wrong **after** you successfully open a worktree.

---

## How this differs from Lesson #12

| Lesson | Scope | Lifecycle stage |
|--------|-------|-----------------|
| **Lesson #12** | Entry point: dubious-ownership trap, 2-store gitconfig misdiagnosis, UNC worktree binding | Opening / accessing the worktree |
| **Lesson #13** (this) | Post-entry lifecycle: commit, push, PR merge, cleanup | Everything after the worktree is open |

Lesson #12 answers: *"Why does `git status` fail in my Code tab worktree?"* Lesson #13 answers: *"My Code tab worktree opens fine — why does my entire commit-push-merge cycle keep breaking?"*

The two are complementary. Trap families A1 and A2 below are documented in Lesson #12; this lesson references them for completeness but does not re-derive them.

---

## The three trap families

| Family | Theme | Traps in this lesson |
|--------|-------|---------------------|
| **A. Environment asymmetry** | Windows ↔ WSL have different `$HOME`, gitconfig, git binary, path conventions | A1, A2, A3 |
| **B. Sandbox ownership cascade** | Claude Desktop sandbox runs as `root` → every file/dir it creates is `root`-owned, blocking subsequent git operations from the Code tab Bash (Windows user privs) | B1, B2, B3 |
| **C. PR merge bookkeeping** | `gh pr merge` does post-merge git work in the **current CWD's worktree** — fails when target branch is held by another worktree | C1 |

All seven traps surfaced sequentially in Session 9 Phase G. The reasoning chain that connects them is in §6 "Worked example".

---

## Trap Family A — Environment asymmetry

### A1: Two-store gitconfig (Windows + WSL)

**Symptom:** Config set via `git config --global --add safe.directory '*'` from PowerShell or Code tab Bash appears to "vanish" when checked from a WSL native terminal.

**Root cause:** On Windows + WSL hybrid, `git config --global` writes to whichever gitconfig the **current shell** sees:
- Code tab Bash, PowerShell, Git Bash → `/c/Users/crayj/.gitconfig` (1.3 KB in this repo)
- WSL native terminal → `/home/crayj/.gitconfig` (273 B in this repo)

These are **separate files** that do not synchronise. The word "global" in `--global` means "user-level instead of repo-level", not "host-level".

**Already documented in Lesson #12 Misdiagnosis section + Misconceptions table row "There is one global gitconfig per user."** This entry is here for completeness — see Lesson #12 for the full treatment, file mtimes evidence, and worked diagnostic.

### A2: UNC worktree gitdir binding

**Symptom:** A worktree created from Code tab is reported `prunable` by WSL native `git worktree list`, and any `git` command inside it returns `fatal: not a git repository`.

**Root cause:** Worktrees created from Code tab register their internal `gitdir` pointer using a UNC path (`//wsl.localhost/ubuntu-24.04/...`). Linux git cannot resolve this — POSIX path parsing collapses the leading `//` and lands on a non-existent `/wsl.localhost/...`.

**Already documented in Lesson #12 Misdiagnosis section.** See Lesson #12 for the worked diagnostic, the three-things-look-wrong-but-only-one-is-real framing, and the cross-environment access options (`git worktree repair` etc.).

### A3: Stale pre-commit hook with hard-coded POSIX paths

**Symptom:** `git commit` fails with:
```
`pre-commit` not found.  Did you forget to activate your virtualenv?
```
even though `uv run pre-commit run --all-files` passes minutes earlier in the same session.

**Root cause:** Pre-commit installs a hook script at `.git/hooks/pre-commit` (which, for a worktree, lives in the **main repo's** `.git/hooks/` because of the commondir share — see Family B2 below). The hook script template hard-codes `INSTALL_PYTHON` to a POSIX path:

```bash
INSTALL_PYTHON=/home/crayj/work/vero-lite/.venv/bin/python3
```

If the hook was installed from a WSL native terminal in a previous session (when a Linux-layout `.venv/bin/` existed), the path is baked in. When a later session runs from Code tab — which created a Windows-layout venv at `.venv/Scripts/pre-commit.exe` — the hook script's `[ -x "$INSTALL_PYTHON" ]` test fails. It then falls back to `command -v pre-commit`, which is also not in PATH (uv keeps tools project-local — see Lesson #1 Trap 11). The hook prints the misleading "did you forget to activate your virtualenv?" error and exits 1.

`uv run pre-commit run --all-files` works because `uv run` injects `.venv/Scripts/` into PATH before executing — bypassing the hook script entirely.

**Fix (one-shot, scoped):**
```bash
PATH="$PWD/.venv/Scripts:$PATH" git commit -F /tmp/commit-message.txt
```

**Why not `uv run pre-commit install` to regenerate the hook?**
The hook lives in the **main repo's** `.git/hooks/`. Re-installing from Code tab would write a Windows-path `INSTALL_PYTHON` — which then breaks `git commit` from WSL native on the main repo. The inline PATH fix is one-shot and affects only the current commit, leaving the main repo's hook untouched.

**Anti-fix:** ❌ `git commit --no-verify` — bypasses pre-commit entirely. CLAUDE.md §8 forbids this. The fix above runs hooks normally; only the hook-shell PATH is overridden.

**Discovered:** Session 9 Phase G B.1 (commit hash 694f2cf attempt 2). The earlier `uv run pre-commit run --all-files` in Phase F.2.5 succeeded and gave false confidence that hooks were "ready" — manual `uv run` and hook-triggered execution take different code paths.

---

## Trap Family B — Sandbox ownership cascade

### B1: Index lock denied (worktree gitdir)

**Symptom:**
```
$ git add docs/STATUS.md
fatal: Unable to create '//wsl.localhost/.../.git/worktrees/<name>/index.lock': Permission denied
```

**Root cause:** Claude Desktop sandbox runs as `root` (Lesson #1 Trap 2). All files and directories it creates inside the worktree's gitdir (`<main-repo>/.git/worktrees/<name>/`) are `root:root`. Code tab Bash invokes Git for Windows under the Windows user's privileges (not `root`), so it cannot write `index.lock` into a `root`-owned directory.

The asymmetry is sharp: Edit/Write tool (sandbox = `root`) can modify existing root-owned files; Bash tool (Windows user) cannot create new files in root-owned dirs. So earlier file edits succeed silently, then `git add` fails surprisingly.

**Fix (scoped):**
```bash
wsl.exe -d ubuntu-24.04 -u root -- bash -c '
  chown -R crayj:crayj /home/crayj/work/vero-lite/.claude/worktrees/<name>
  chown -R crayj:crayj /home/crayj/work/vero-lite/.git/worktrees/<name>
'
```

This is the same `chown` pattern from Lesson #1 Trap 7, applied to **two** locations: the worktree's working tree AND its private gitdir under the main repo.

### B2: Refs and objects denied (main repo's `.git/`)

**Symptom (after fixing B1):**
```
$ git commit -F /tmp/msg.txt
fatal: cannot lock ref 'HEAD': Unable to create
  '//wsl.localhost/.../.git/refs/heads/claude/<name>.lock': Permission denied
```

**Root cause:** Worktrees **share their refs and objects with the main repo** via the commondir mechanism. The branch ref for a Code-tab-created worktree lives at `<main-repo>/.git/refs/heads/claude/<name>` — not inside the worktree's own gitdir. So `chown` on the worktree alone (B1's fix) covers the index but leaves the refs untouched.

Diagnostic from Session 9:

```
root-owned dirs: 5
  /home/crayj/work/vero-lite/.git/logs/refs/heads/claude
  /home/crayj/work/vero-lite/.git/objects/ce
  /home/crayj/work/vero-lite/.git/objects/f3
  /home/crayj/work/vero-lite/.git/refs/heads/claude       ← BLOCKER
  /home/crayj/work/vero-lite/.git/worktrees

root-owned files: 8
  /home/crayj/work/vero-lite/.git/logs/refs/heads/claude/<name>
  /home/crayj/work/vero-lite/.git/index
  /home/crayj/work/vero-lite/.git/objects/ce/...
  /home/crayj/work/vero-lite/.git/objects/00/...
  /home/crayj/work/vero-lite/.git/objects/f3/...
  /home/crayj/work/vero-lite/.git/config
  /home/crayj/work/vero-lite/.git/refs/heads/claude/<name>  ← BLOCKER
  /home/crayj/work/vero-lite/.git/FETCH_HEAD
```

The cascade reveals in **stages**: index → refs → objects. Targeted `chown` would require fixing each as it surfaces (whack-a-mole). A sweep handles them all in one pass.

**Fix (sweep):**
```bash
wsl.exe -d ubuntu-24.04 -u root -- bash -c '
  chown -R crayj:crayj /home/crayj/work/vero-lite/.git
'
```

**Verification (strict gate, 0/0 expected):**
```bash
wsl.exe -d ubuntu-24.04 -- bash -c '
  echo "dirs:";  find /home/crayj/work/vero-lite/.git -user root -type d 2>/dev/null | wc -l
  echo "files:"; find /home/crayj/work/vero-lite/.git -user root -type f 2>/dev/null | wc -l
'
```

**Why this is safe:** scope is `.git/` only — does not touch working tree, system, or other repos. Single-user dev box, fully reversible. Same family as Lesson #1 Trap 7.

### B3: Worktree filesystem leftover after first chown

**Symptom (post-merge cleanup):**
```
$ git worktree remove .claude/worktrees/<name> --force
error: failed to delete '...': Permission denied
remove exit: 255
```

**Root cause:** Even after B1 + B2 chown sweeps, the sandbox can re-create root-owned files inside the worktree **between the chown and the cleanup** — typically `.venv/` regenerations, hook installs, or Edit tool writes to new subdirs. Chown is a **point-in-time fix**, not a permanent one.

The `git` registration still removes cleanly (worktree is unregistered from `git worktree list`), but the filesystem directory persists.

**Acceptable resolution:** skip filesystem cleanup. Git registration clean = "we're done" from git's perspective. The directory is cosmetic clutter, not a blocker.

**Manual cleanup (later, when convenient):**
```bash
wsl.exe -u root -- rm -rf /home/crayj/work/vero-lite/.claude/worktrees/<name>
```

**Anti-fix:** ❌ Do NOT `chown` then retry `git worktree remove`. The cycle repeats. Either accept the leftover or use `wsl -u root -- rm -rf` directly.

**Anti-anti-fix:** ❌ Do NOT add `.venv/` to `.gitignore` exceptions or alter sandbox UID. Both have wider blast radius than the cosmetic problem warrants.

---

## Trap Family C — PR merge bookkeeping

### C1: `gh pr merge` fails when target branch held by another worktree

**Symptom:**
```
$ gh pr merge 1 --merge --delete-branch
failed to run git: fatal: 'main' is already used by worktree at '/home/crayj/work/vero-lite'
exit: 1
```

But — and this is the trap — **the PR is actually merged on GitHub.** Verify before assuming failure:

```bash
$ gh pr view 1 --json number,state,mergeCommit
{"number":1,"state":"MERGED","mergeCommit":{"oid":"e69e31a..."}}
```

**Root cause:** `gh pr merge --delete-branch` performs three steps:
1. Call GitHub merge API (succeeds — server-side merge)
2. `git checkout <target-branch>` in the **current CWD's worktree** (intended to leave the user on the merged branch)
3. Call GitHub branch-delete API

If step 2 fails (target branch is held by another worktree per git's "one branch, one worktree" rule), step 3 is skipped. `gh` returns exit 1, but the merge already happened — only the branch-delete is missing.

**Fix:**
```bash
git push origin --delete <branch-name>
```

A standard git command, no dependency on `gh` post-merge bookkeeping. Works from any worktree (push doesn't require checkout).

**Prevention:** From Code tab worktree, anticipate this. Don't run `gh pr merge` from a worktree whose target branch is checked out elsewhere — or accept that you'll do a manual `git push --delete` afterwards.

**Discovered:** Session 9 Phase G B.4. The error message is technically accurate but misleading without context — looks like the merge failed when actually only cleanup did.

---

## The unified fix pattern

For all three families, the operational pattern is:

1. **Diagnose before fixing** — `find . -user root -type {f,d}` is your friend
2. **Sweep, don't whack-a-mole** — chown the parent directory recursively rather than fix one path at a time
3. **Inline overrides for one-shots** — `PATH=...` for hooks, `git push --delete` for cleanup; do not modify durable state for transient problems
4. **Accept cosmetic leftover** — git registration cleanliness > filesystem cleanliness when they conflict

Specific commands (memorise this card):

| Stage | Trap | Fix |
|-------|------|-----|
| Pre-commit | A3 | `PATH="$PWD/.venv/Scripts:$PATH" git commit ...` |
| `git add`/`commit` | B1, B2 | `wsl -u root -- chown -R crayj:crayj /home/crayj/work/vero-lite/.git` |
| `gh pr merge` exit 1 | C1 | Verify PR state with `gh pr view --json`; if MERGED, just `git push origin --delete <branch>` |
| `git worktree remove` permission denied | B3 | Skip; cleanup later with `wsl -u root -- rm -rf <path>` |

---

## Worked example — Phase G timeline (Session 9)

A single docs-only PR (`docs(runbooks): add Claude Code in Desktop setup runbook + Lesson #12`) took 90 minutes due to encountering all 7 traps sequentially.

The full timeline — including diagnostic outputs, decision points, and chat-side review — is preserved at:

> `.claude/handoffs/session-09/2026-05-09-1100-phase1-diagnostic.md`
> (Phase 1 root-cause discovery)

Brief sequence:

1. **Phase G start** — Cray attempts `git status` from WSL native → A1 + A2 trap surfaces (already knew about A1 from Lesson #12, but A2's persistence-loss illusion required Phase 1 diagnostic to disambiguate)
2. **Phase G B.1 first attempt** — `git add` fails with B1 (`index.lock` denied) → chown worktree gitdir → fix
3. **Phase G B.1 second attempt** — `git commit` fails with A3 (stale POSIX hook) → inline PATH override → fix
4. **Phase G B.1 third attempt** — `git commit` fails with B2 (ref lock denied) → C3 sweep `.git/` → fix → commit `694f2cf`
5. **Phase G B.2** — push succeeds first try (no traps in pure push)
6. **Phase G B.3** — PR creates fine; `gh pr view` interactive needs `read:project` scope (minor, `--json` workaround)
7. **Phase G B.4** — `gh pr merge` exit 1 with C1 trap → verify merged on GitHub → `git push --delete` for cleanup
8. **Phase G B.5** — `git worktree remove` permission denied with B3 → accept leftover, registration is clean

Total: 8 phase steps, 7 distinct traps, 4 chown operations, 1 inline-PATH override, 1 manual branch delete, 1 cosmetic leftover accepted.

---

## Diagnostic decision tree

When a Code tab git operation fails:

```
git command fails
│
├── Symptom contains "Permission denied" + path under .git/ or .claude/worktrees/
│   └── Family B (ownership cascade)
│       ├── Fix: chown -R the parent (worktree gitdir, .git/, or .claude/)
│       └── Verify: find ... -user root | wc -l → 0
│
├── Symptom contains "fatal: not a git repository" or "prunable"
│   └── Family A2 (UNC binding) — see Lesson #12
│       └── Fix: don't use this worktree from this environment
│
├── Symptom contains "pre-commit not found" / "did you forget your virtualenv"
│   └── Family A3 (stale hook)
│       └── Fix: inline PATH override for one-shot
│
├── Symptom is "gh pr merge" exit 1 with worktree mention
│   └── Family C1 (merge bookkeeping)
│       └── Verify: gh pr view --json → check state=MERGED
│       └── Fix: git push origin --delete <branch>
│
└── Symptom is missing safe.directory after a "successful" config add
    └── Family A1 (2-store gitconfig) — see Lesson #12
        └── Fix: identify which gitconfig you're in; check both
```

---

## Anti-patterns (do NOT use)

- ❌ **`git commit --no-verify`** — bypasses pre-commit. CLAUDE.md §8 forbids. Real fix is the inline PATH override (A3).
- ❌ **`rm -rf` to clean up worktree leftover** — destructive, masks ownership root cause. Use `wsl -u root -- rm -rf` only after `git worktree remove` succeeded.
- ❌ **`uv run pre-commit install` from Code tab to "fix" hook PATH** — overwrites main repo's hook with a Windows path, breaking WSL native git.
- ❌ **Retry-without-diagnose on permission errors** — hides which layer is root-owned. Use `find -user root` to see scope.
- ❌ **Targeted chown on `index.lock` only** — works for B1 but misses B2's refs/objects. Sweep the parent.
- ❌ **Disabling sandbox or WSL UID translation** — massive blast radius for a config-line problem.

---

## Prevention checklist

For Session 10+ first-time-in-worktree work:

- [ ] **Pre-flight ownership scan:** `find /home/crayj/work/vero-lite/.git /home/crayj/work/vero-lite/.claude -user root | wc -l` — if not 0, pre-emptively `chown -R` the offending parent
- [ ] **Pre-flight hook portability check:** `head -10 /home/crayj/work/vero-lite/.git/hooks/pre-commit` — if `INSTALL_PYTHON` points to `.venv/bin/` (POSIX) but you're in Code tab, plan for inline PATH on commit
- [ ] **Pre-flight gitconfig sanity:** `git config --global --get-all safe.directory | grep -E '^\*$'` — if no `*`, add it (in the right environment)
- [ ] **Use heredoc + `git commit -F`** for any non-trivial commit message (Lesson #1 Trap 10)
- [ ] **For `gh pr merge`:** be in the main worktree's CWD before running, OR plan for manual `git push --delete` afterwards
- [ ] **Capture long outputs to `/tmp/*.log`** instead of relying on terminal stream — avoids notification truncation (this lesson's Worked Example would not exist without log files)

---

## Related

- **Lesson #12** (`0002-claude-code-desktop-wsl-ownership.md`) — entry-point traps (dubious-ownership, 2-store gitconfig, UNC binding); this lesson covers the post-entry lifecycle
- **Lesson #1** (`0001-precommit-environment.md`) Trap 2, Trap 7 — root chown pattern (same conceptual family, different layer)
- **Lesson #1** Trap 9 — `${PIPESTATUS[0]}`; encountered again in Session 9 when echo-after-command swallowed git commit's exit code
- **Lesson #1** Trap 10 — heredoc + `git commit -F`; used successfully throughout Phase G
- **Lesson #1** Trap 11 — `uv run` for project-local tools; the root mechanism behind A3 hook failure
- **Runbook** `claude-code-setup.md` — first-time setup including `safe.directory '*'` precondition
- **Runbook** `claude-code-chat-handoff.md` — the file-based handoff mechanism this lesson references for worked-example detail
- **CLAUDE.md** §6 (Working Patterns), §8 (Constraints — `--no-verify` prohibition)
