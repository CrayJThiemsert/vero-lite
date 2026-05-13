# Lesson 0004: WSL `bash -c` Variable Expansion Trap

**Captured:** 2026-05-13 (codified from Session 10 Batch 2 observations)
**Context:** Three occurrences in Session 10 Batch 2 — file-existence checks, vet-grep loop, cherry-pick loop — each producing silent empty-string substitutions
**Severity:** Medium (causes silent failures; not destructive)
**Related:** Lesson #1 (pre-commit environment), Lesson #13 (worktree lifecycle)

---

## Symptom

Shell variable substitution (`$var`, `"$var"`) inside
`wsl -d ubuntu-24.04 -- bash -c '...'` does NOT expand.

Inside the inner `bash -c '...'` script, variables become empty
strings, producing errors like:
- `cannot access '': No such file or directory`
- `grep: : No such file or directory`
- `fatal: bad revision ''`

---

## Diagnosis

The outer single quotes around the `bash -c '...'` body are consumed by
Windows-side argument parsing (or by the Bash tool's own quote handling)
BEFORE WSL bash sees the body. By the time inner bash runs, the
variables have already been emptied — but inner bash doesn't know that
and proceeds, producing the empty-string substitution errors.

---

## Reproduction (any of these will trigger)

```bash
# Pattern 1: variable assignment + use
wsl -d ubuntu-24.04 -- bash -c '
  FILE=/some/path
  ls -la "$FILE"
'
# → ls: cannot access '': No such file or directory

# Pattern 2: for loop with variable
wsl -d ubuntu-24.04 -- bash -c '
  for h in c5eebdd 00a00f1 ad12067; do
    git cherry-pick "$h"
  done
'
# → fatal: bad revision '' (three times)

# Pattern 3: command substitution + variable
wsl -d ubuntu-24.04 -- bash -c '
  for f in $(ls *.md); do
    grep "$f" something
  done
'
# → grep: : No such file or directory (per file)
```

---

## Workaround (validated 3 times in Session 10)

Use **explicit literal values** instead of shell variables:

```bash
# Instead of for-loop:
wsl -d ubuntu-24.04 -- bash -c 'git cherry-pick c5eebdd'
wsl -d ubuntu-24.04 -- bash -c 'git cherry-pick 00a00f1'
wsl -d ubuntu-24.04 -- bash -c 'git cherry-pick ad12067'

# Or pass values via command-line arguments and use $1, $2, ...:
wsl -d ubuntu-24.04 -- bash -c 'git cherry-pick "$1"' _ c5eebdd
```

The `_` is a positional-arg-0 placeholder; `$1` will receive
`c5eebdd`. This pattern works because positional args traverse the
quote boundary differently from `$var` interpolation.

---

## Prevention checklist

Before writing any `wsl -d ubuntu-24.04 -- bash -c '...'` that uses
variables:

- [ ] Does this command use `$var` or `"$var"` inside the single-quoted
      body? If yes — STOP, restructure
- [ ] Can the value be inlined as a literal? Use that
- [ ] Can the command be split into N separate invocations (one per
      literal value)? Do that
- [ ] If a loop is unavoidable, pass values as positional args
      (`bash -c 'echo "$1"' _ value`)

---

## Why this isn't covered by Lesson #1 or #13

- **Lesson #1** addresses pre-commit hook PATH issues — different layer
  (hook environment), different symptom (hook fails to find tools)
- **Lesson #13** addresses worktree lifecycle traps — different
  problem class (filesystem state vs shell quoting)

This is its own family: **shell-quoting boundary errors in cross-tool
invocations**. Could expand to a Lesson #14 family later if other
shell-quoting issues surface (e.g., PowerShell → WSL, Claude Code Bash
tool → WSL bash, etc.).

---

## Recurrence count this session

3 occurrences in Session 10 Batch 2 alone (each documented in Batch 2
closeout addendum §6). Pattern reliable enough to codify.
