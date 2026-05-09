# Lesson 0002: Claude Code in Desktop + WSL Ownership Trap

**Captured:** 2026-05-08 (extracted from Session 8 Phase B, four rounds of git troubleshooting)
**Context:** First-time adoption of Claude Code in Desktop (Code tab) for vero-lite, with the repo living in WSL2 Ubuntu 24.04
**Severity:** High — every git operation in a Code tab session fails until this is resolved; trivially fixed once understood

---

## Summary

When Claude Code in Desktop opens a vero-lite worktree, the Code tab's Bash tool calls Git for Windows (`/mingw64/bin/git`) against a WSL UNC path. Git for Windows applies its `safe.directory` ownership check, which fails because the WSL filesystem reports a UID Git for Windows does not recognize as the current user. The result is a `fatal: detected dubious ownership` error on every git command — `git status`, `git log`, even `git rev-parse --git-dir`.

The fix is one config line. The trap is non-obvious because the error message *does* suggest a fix, but the suggested exact-path fix doesn't survive the next worktree session (each gets a new random subdirectory name), and several plausible-looking parent-directory or wildcard variants also fail to match.

A second-order trap follows from the same architecture: the fix is environment-scoped, not host-scoped. Adding `safe.directory '*'` from Code tab Bash writes to the Windows-side gitconfig (`%USERPROFILE%\.gitconfig`); WSL native terminals read a different file (`~/.gitconfig` inside WSL), and the worktree itself is registered with a UNC gitdir path that WSL git cannot resolve at all. See "Misdiagnosis" below.

---

## Trap: `dubious ownership` on every git command in a Code tab worktree

### Symptom

```
$ git status
fatal: detected dubious ownership in repository at '//wsl.localhost/ubuntu-24.04/home/crayj/work/vero-lite/.claude/worktrees/sad-northcutt-6a48ff'
To add an exception for this directory, call:

	git config --global --add safe.directory '%(prefix)///wsl.localhost/ubuntu-24.04/home/crayj/work/vero-lite/.claude/worktrees/sad-northcutt-6a48ff'
```

Same error from `git log`, `git branch --show-current`, `git rev-parse --show-toplevel`, `git worktree list`, etc. Even `git config --global --list` works (it doesn't need a repo) — but the moment a command tries to discover or open the repository, it fails.

The path Git complains about is the **exact worktree subdirectory**, not the main repo, not the `.claude/worktrees/` parent.

### Root cause (three layers)

This is a three-layer interaction, and missing any layer makes the diagnosis confusing:

1. **Claude Code in Desktop creates a worktree per session.** Each Code tab session lives at `.claude/worktrees/<random-name>/` with its own dedicated branch. Each new session gets a new random name (e.g., `sad-northcutt-6a48ff`, `eager-fermat-1c92f3`). The Bash tool's CWD is set to that worktree path.

2. **WSL filesystem ownership is foreign to Git for Windows.** WSL files are owned by the Linux user (UID 1000, in this case `crayj`). Windows does not have a concept of UID 1000; Git for Windows sees the file owner as "not the current Windows user" and applies the `safe.directory` ownership check defensively (it's the same check that protects against malicious repos in shared download directories).

3. **`safe.directory` matches the literal repository root, with no recursion and no glob support.** Adding the parent (`.../vero-lite`) does not cover children. Adding `.../worktrees` does not cover subdirectories. Adding `.../worktrees/*` is treated as a literal string ending in `*`, not a glob. Only an exact match — or the special wildcard `*` (alone) — works.

These three together mean: **every new Code tab session lands in a path that Git for Windows has never seen before, and the `safe.directory` config can never enumerate them in advance unless `*` is used.**

### Misconceptions debunked (all encountered during Session 8 troubleshooting)

| Misconception | Why it's wrong |
|---------------|---------------|
| "Adding the main repo to `safe.directory` should cover worktrees too." | Worktrees are separate repositories from Git's perspective — each has its own `.git` file pointing to a gitdir under `<main>/.git/worktrees/<name>/`. The ownership check runs at the worktree's own root, not the main repo's. |
| "`.../worktrees/*` is a glob and will match all sessions." | `safe.directory` does not support glob expansion. It does literal-string comparison except for the special single-character value `*`. Session 8 added `.../worktrees/*` as a literal, and it had no effect — the next session still failed. |
| "Adding the path with `Ubuntu-24.04` (capital U) is fine because Windows is case-insensitive." | Git's `safe.directory` comparison is byte-exact, even on Windows. The error message shows the exact path Git is checking; if your config entry differs in case, it does not match. The actual UNC Claude Code uses is lowercase `ubuntu-24.04`. |
| "There is one global gitconfig per user." | On a Windows + WSL hybrid setup there are two: Git for Windows reads `%USERPROFILE%\.gitconfig` (visible to Code tab Bash, PowerShell, Git Bash); Linux git reads `~/.gitconfig` inside the WSL distro. They do not sync. A `safe.directory '*'` added in one is invisible from the other. The "global" in `git config --global` means "user-level instead of repo-level", not "host-level". |
| "If the worktree works from Code tab, it also works from WSL native after fixing safe.directory." | No. Worktrees created from Code tab register their `gitdir` pointer as a UNC path (`//wsl.localhost/ubuntu-24.04/...`), which WSL native git cannot resolve — it parses the leading `//` per POSIX rules and lands on a non-existent `/wsl.localhost/...` path. `git worktree list` from WSL marks such worktrees `prunable`, and any git command inside them returns `fatal: not a git repository`. The fix is not config; the worktree is bound to the environment that created it. |

### Fix

Run on the Windows host PowerShell (not inside the Code tab Bash tool — this modifies the global config that Git for Windows reads):

```powershell
git config --global --add safe.directory '*'
```

Verify:

```powershell
git config --global --get-all safe.directory
# Output should include a line that is just: *
```

Then re-open or refresh the Code tab session. The dubious-ownership errors stop immediately.

### Trade-offs: why `*` and not an exact path

Three options were considered during Session 8 Phase B Round 4:

| Option | Coverage | Maintenance | Security trade-off | Verdict |
|--------|----------|-------------|--------------------|---------|
| Exact path of current worktree | Just this session | Re-add for every new session | Tightest | Doesn't scale; rejected |
| `.../worktrees/*` (intended as glob) | Nothing — literal match only | None (does nothing) | N/A | Doesn't work; rejected |
| `*` (universal wildcard) | All repos on the host | None | Disables `safe.directory` check entirely on this host | Adopted |

The security reasoning for `*`: `safe.directory` exists to prevent a malicious git repo dropped into a shared path (e.g., a colleague's download directory) from running arbitrary code via `core.fsmonitor` or hook configurations. On a single-user developer machine where the user controls all paths under `~/`, `D:/`, and the WSL home, the practical risk is near-zero. The cost of `*` is one fewer tripwire on a path that was already trusted.

A scoped wildcard would be better in principle, but Git does not support it. Until Git for Windows adds glob support to `safe.directory`, `*` is the only option that survives Code tab worktree turnover without manual intervention.

### Anti-fixes (do NOT use)

- **`git config --global --unset-all safe.directory '<regex>'`** — `--unset-all` does accept a value-pattern (regex) argument, but PowerShell quoting around regex characters (`.`, `/`, `*`) is fragile and can silently match more entries than intended. If the pre-existing config contains entries for other projects (e.g., the founder's `casaos.local` and `aaas-pov` paths), an over-broad regex deletes them. If cleanup is needed, **manually edit `%USERPROFILE%\.gitconfig`** with notepad — it is a small text file and the safety margin is worth more than the keystrokes saved.
- **`sudo chown -R $(whoami):$(whoami) <worktree>` inside WSL** — Tempting, but wrong target. The ownership Git for Windows sees is governed by the WSL→Windows UID mapping, not by the WSL filesystem's chown. Re-running chown changes nothing from Git for Windows' perspective.
- **Running `chown` from Windows on the WSL files** — Likely to corrupt WSL's view of file ownership and is not how WSL2 expects to be managed. Don't.
- **Disabling the entire WSL2 distro's UID translation** — Yes, technically possible. No, do not do this. Massive blast radius for a config-line problem.

### Misdiagnosis: when WSL native sees the Code-tab worktree

A separate failure mode looks like the dubious-ownership trap but is not. Symptom, observed at Session 9 start while running diagnostic checks from a WSL native terminal:

```
$ git config --global --get-all safe.directory
(empty)

$ cd ~/work/vero-lite/.claude/worktrees/sad-northcutt-6a48ff
$ git status -s
fatal: not a git repository: //wsl.localhost/ubuntu-24.04/home/crayj/work/vero-lite/.git/worktrees/sad-northcutt-6a48ff

$ git worktree list
/home/crayj/work/vero-lite                                         df3df9a [main]
//wsl.localhost/ubuntu-24.04/home/crayj/work/vero-lite/.claude/...  df3df9a [...] prunable
```

**Three things look wrong, but only one is real:**

1. **`safe.directory` is empty** — looks like config loss. Reality: the `*` was added from Code tab Bash, which wrote to `%USERPROFILE%\.gitconfig` on Windows. The WSL `~/.gitconfig` was never touched. Confirmed by file mtimes (Windows-side: 2026-05-08 18:43 = Phase B Round 4; WSL-side: 2026-05-06 = untouched).
2. **`fatal: not a git repository`** — looks like the dubious-ownership trap returning. Reality: the worktree's `gitdir` file contains `//wsl.localhost/ubuntu-24.04/...`, which Linux git cannot resolve. This is not a permission error; it is a path error.
3. **Worktree marked `prunable`** — looks like git decided the worktree is dead. Reality: from WSL git's point of view, the path *is* dead (it cannot follow the UNC). From Code tab Bash, the same worktree is fully functional.

**Diagnostic rule:** Before adding `safe.directory` to any gitconfig, check which environment created the worktree. If it was created from Code tab, use it from Code tab. The `safe.directory '*'` entry on the Windows side is sufficient and complete; nothing needs to change on the WSL side.

**If cross-environment access is genuinely required** (e.g., a CI script in WSL needs to read a Code-tab-created worktree), the options are:

- `git worktree repair <path>` — re-registers the gitdir with a path the current environment can resolve. Run from the environment that needs access.
- Recreate the worktree from the desired environment: `git worktree remove` from where it was created, then `git worktree add` from where it will be used.
- Accept the asymmetry and use `wsl.exe -d <distro> -- bash -c '<git command>'` from Windows, or its inverse, to defer git operations to the right environment.

The Session 9 incident resolved without any state change: the diagnostic was wrong, the worktree was healthy, and Phase G proceeded from Code tab as originally planned.

### Prevention

Add `safe.directory '*'` once per developer machine, immediately after installing Git for Windows or adopting Claude Code in Desktop. Document this step in the project runbook (`docs/runbooks/claude-code-setup.md` § 2) and in any onboarding checklist. New developer machines should hit this exactly once.

If `safe.directory '*'` is not acceptable for security policy reasons (e.g., shared CI runner machines), the alternative is to run Claude Code from inside WSL natively (Linux-side `git` does not apply this check) — but that gives up the Code tab's Windows-native UI integration.

---

## Related

- `docs/runbooks/claude-code-setup.md` § 2 (Prerequisites) and § 8.1 (Limitations)
- `docs/lessons/0001-precommit-environment.md` Trap 2, Trap 7 — same conceptual category (Windows ↔ WSL ownership friction), different layer
- Pre-existing `safe.directory` entries in the founder's `~/.gitconfig` for `casaos.local` and `D:/aaas-pov` — historical evidence that this trap recurs across projects, not just vero-lite
- Session 8 Phase B transcript (4 rounds of troubleshooting) — for the discovery sequence
