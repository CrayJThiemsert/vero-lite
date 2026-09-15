# Lesson #0064 — mute the reader that misreads, not the one that detects

**Session:** 300 (2026-09-15), measured; re-witnessed session 301 the same day, before this
lesson was written · **PRs:** none carried the fix — it is host configuration, applied by Cray
· **Status:** advisory (§1 precedence — promote to ADR if it must bind). The command-line
half of the same boundary is [Lesson #0007 §1.3](0007-harness-exit-code-artifact.md).

---

## The measurement

Two gits read one file and disagreed. The session-start snapshot — Windows git, run by
Claude Desktop — showed ` M tools/notify/line.sh` and ` M tools/notify/telegram.sh`. WSL git
said the tree was clean. On disk both files were `755`; the index held `100755`. Earlier
sessions had met the same drift as a symptom ([#0053](0053-two-sessions-agreeing-through-one-instrument-is-one-measurement.md),
[#0057](0057-a-perfect-correlation-is-not-a-cause-ask-when-it-changed.md)) and filed it as the
known UNC hazard, without tracing which reader was wrong.

What crosses the Windows↔WSL boundary, each row witnessed in a throwaway repo under WSL
`/tmp` (removed afterwards) or read-only on vero-lite:

| Act | Reading |
|---|---|
| Windows git reads a `100755` file through the `\\wsl.localhost\` mount | ` M`; `git diff --summary` → `mode change 100755 => 100644`. It cannot see the exec bit. |
| Windows `git add` on that file, content unchanged | index **`100644`** while disk stays `755` — the misread is *written*. With the fix below in effect, the same `add` left `100755`. |
| Claude Code's **Edit tool** rewrites a `755` file through the mount | disk **`644`**, LF kept, 0 CR bytes. **Control:** an append from inside WSL left its file at `755`. |
| WSL `git add` after that Edit | stages **`100644`** — a real mode change now enters the commit. |
| `git init`, from either side | writes a **local** `core.filemode = true`. |
| Windows `core.autocrlf` | `true` at **system and global** scope. In a repo with no `.gitattributes`, `git add` warns `LF will be replaced by CRLF`. vero-lite's `* text=auto eol=lf` / `*.sh text eol=lf` neutralise it. |

## Three fixes, and which reader each one mutes

| Fix | Scope | What it mutes | Verdict |
|---|---|---|---|
| `core.fileMode false` in the repo's `.git/config` | one clone | **both** gits — including WSL git, the only reader that sees modes | **Rejected.** See below. |
| `core.fileMode false` in the Windows **global** gitconfig (or an `includeIf` there) | one machine | **nothing** | **Dead.** Local beats global, and every `git init` writes local `true`. Measured s300: still ` M`, effective value `local true`. |
| Windows **user** env vars `GIT_CONFIG_COUNT=1`, `GIT_CONFIG_KEY_0=core.fileMode`, `GIT_CONFIG_VALUE_0=false` | one machine | **only Windows git** | **Adopted** s300 (Cray; host config). |

**Why the env vars win.** Git reads `GIT_CONFIG_COUNT`/`KEY_n`/`VALUE_n` as *command* scope,
which beats local. `WSLENV` does not forward them, so a git started inside WSL never sees them
and keeps `local true`. Verified after the Desktop restart (s301):

| Reader | `git config --show-scope --get core.fileMode` | `git status --short` |
|---|---|---|
| Windows git, Bash tool | `command	false` | empty |
| same, with the three vars stripped by `env -u` (**control**) | — | ` M line.sh`, ` M telegram.sh` |
| WSL git | `local	true` (`printenv GIT_CONFIG_COUNT` → rc 1) | empty |

**Why the repo-local setting was rejected** even though it makes the symptom vanish:

- **It blinds the detector.** At s256 this repo *did* carry `core.fileMode = false`
  (`docs/logs/2026-08-26-s256-fleet-deploy-plan0113-plus-0114.md:77`). That session a probe
  driver copied a temp file's `0600` onto every file it mutated, and `git status` was one of
  four checks that could not see it (`docs/status-archive/2026-h1i-status.md:515`).
- **It is per clone.** Every fresh checkout silently lacks it.
- **It does not stay put.** A `git init` run with an inherited `GIT_DIR` re-initialises the
  target and rewrites its `core.filemode`. Witnessed: `false` → a plain `git init` elsewhere
  (**control**) `false` → a `git init` in another directory with `GIT_DIR=<target>` `true`.
  The repo read `false` at s256 and `true` at s300 with no config history in between. Session
  295's exported-`GIT_DIR` pytest run executed fixture `git init`s against the real gitdir;
  the damage recorded afterwards names `core.worktree`, `user.name` and `user.email`
  (`git-workflow` skill), not `core.filemode`. That run is the likely flip — **inferred, not
  isolated**.

## The general point

When two instruments read one artifact and disagree, repair the one that misreads, at a
scope that actually wins for it. A fix that ends the disagreement by blinding **both**
readers removes the symptom and the detector together, and the next real defect is invisible
— as the s256 `0600` bug was.

A fix at a scope that **loses** is worse than none, because it *looks* applied: the line is in
the file, `git config --global --get` returns it, and nothing changes. Read the effective
value with `git config --show-scope --get <key>`, never the value you wrote.

This is the repair half of [Lesson #0056](0056-suspect-the-instrument-before-the-artifact.md):
that lesson says suspect the instrument first; this one says, once it is convicted, mute it
alone.

## What no git setting prevents

The Edit tool's `755 → 644` rewrite happens on disk, below git. So:

- **Run scripts through their interpreter** — `bash x.sh`, `python x.py` — never `./x.sh`.
  This is already the convention: of the **48** tracked files that start with `#!`, **2** are
  `100755` (`tools/notify/line.sh`, `tools/notify/telegram.sh`) and **46** are `100644`. Every
  programmatic caller of `telegram.sh` goes through `bash` — the six hooks via
  `_wsl_bridge.bash_argv`, `tools/loop/`, `tools/probe_battery/_lock.py` and the
  `ms-s1-ollama` detached runner. `line.sh` has no programmatic caller; its own usage comment
  shows the direct form, which is the one invocation an Edit from Windows can break.
- **After editing a `100755` file from Windows,** run `chmod +x` inside WSL and confirm
  `git ls-files -s <path>` shows `100755` before committing. Functionally harmless either way
  (both run via `bash`), but otherwise the PR carries an unintended mode change.
- **A `check-shebang-scripts-are-executable` pre-commit hook is not drop-in.** It would red
  46 of the 48 files. Count the variety before proposing a guard (`CLAUDE.md` §8).

## Host setup and undo

Once per Windows machine (runbook: `docs/runbooks/claude-code-setup.md` § 2), in PowerShell —
three separate commands, since Windows PowerShell 5.1 rejects `&&`:

```powershell
setx GIT_CONFIG_COUNT 1
setx GIT_CONFIG_KEY_0 core.fileMode
setx GIT_CONFIG_VALUE_0 false
```

Then **quit Claude Desktop from the tray and reopen it** — Desktop caches its environment at
launch ([Lesson #0013](0013-claude-desktop-process-env-cache-secret-rotation.md)). Verify from
a new Windows shell: `git config --show-scope --get core.fileMode` prints `command	false`.

Undo: `Remove-ItemProperty -Path HKCU:\Environment -Name GIT_CONFIG_COUNT, GIT_CONFIG_KEY_0, GIT_CONFIG_VALUE_0`,
then restart Desktop.

## Related

- [Lesson #0002](0002-claude-code-desktop-wsl-ownership.md) — the same boundary at the
  ownership layer (`safe.directory`); also the reason "global" in `git config --global` means
  one of **two** user configs on this machine.
- [Lesson #0007 §1.3](0007-harness-exit-code-artifact.md) — the command-line side: `wsl -e`
  inverts the escaping rule, PowerShell 5.1 drops embedded quotes, `wsl bash <file>` has no
  login `PATH`.
- [Lesson #0056](0056-suspect-the-instrument-before-the-artifact.md) — convict the instrument
  before the artifact.

AI-assisted (Claude Code) per project convention.
