# Lesson 0001: Pre-commit Environment Setup Traps

**Captured:** 2026-05-07 (extracted from Session 4)
**Context:** PLAN-001 Phase E execution (initial scaffold pre-commit run)
**Severity:** High — these traps block commits and silently break tooling

---

## Summary

Setting up pre-commit on a public repo with multiple contributing tools (Claude Desktop, Claude Code, manual WSL) hit 10 distinct traps. Each is documented below with symptom, root cause, and fix.

---

## Trap 1: `uv sync` does not install dev dependencies by default

**Symptom:**
```
$ pre-commit run --all-files
pre-commit: command not found
```

**Root cause:** `uv sync` installs only the default dependency group. Dev tools (pre-commit, ruff, mypy, pytest) live under `[project.optional-dependencies] dev = [...]` and require explicit opt-in.

**Fix:**
```bash
uv sync --extra dev
```

**Prevention:** Document in README and `CLAUDE.md`. Add to onboarding checklist.

---

## Trap 2: Files written by Claude Desktop are root-owned

**Symptom:**
```
$ git add .
error: insufficient permission for adding an object to repository database .git/objects
```
or
```
$ pre-commit run
[detect-secrets] FAILED — cannot read file (permission denied)
```

**Root cause:** Claude Desktop's filesystem tool runs as root inside its sandbox. Files it creates in WSL paths are owned by `root:root`, not `crayj:crayj`.

**Fix pattern:**
```bash
sudo chown $USER:$USER <file-or-dir>
# or for multiple files:
sudo chown -R $USER:$USER docs/ services/
```

**Prevention:** After ANY Claude Desktop file write, run `ls -la` and check ownership before `git add`.

---

## Trap 3: detect-secrets baseline breaks on `git mv`

**Symptom:**
```
$ git mv docs/plans/PLAN-001-foo.md docs/plans/done/
$ pre-commit run detect-secrets
detect-secrets: file path not in baseline → FAIL
```

**Root cause:** `.secrets.baseline` records paths. Renaming/moving files invalidates the baseline.

**Fix:**
```bash
uv run detect-secrets scan --baseline .secrets.baseline
git add .secrets.baseline
```

**Prevention:** Re-scan baseline after every `git mv` operation involving tracked files.

---

## Trap 4: Cross-platform line endings break pre-commit hooks

**Symptom:** Files modified on Windows (CRLF) fail `end-of-file-fixer` and `trailing-whitespace` hooks even when "untouched".

**Root cause:** Mixed CRLF/LF in repo causes pre-commit normalizers to rewrite files on every run.

**Fix:** Add `.gitattributes`:
```
* text=auto eol=lf
*.{cmd,bat,ps1} text eol=crlf
*.{png,jpg,jpeg,gif,ico,pdf,zip,tar,gz} binary
```

Then re-normalize:
```bash
git add --renormalize .
git commit -m "chore: enforce LF line endings via .gitattributes"
```

**Prevention:** Set `.gitattributes` before first commit on any cross-platform repo.

---

## Trap 5: Pre-commit must run inside WSL native, not Git Bash or Claude Desktop

**Symptom:** Hooks pass in Claude Desktop bash tool but fail in native WSL terminal (or vice versa). Path separators, virtualenv resolution, or file permissions diverge.

**Root cause:** Claude Desktop's bash tool is a sandboxed environment with subtle differences from native WSL (PATH, $HOME, file ownership semantics).

**Fix:** Always run pre-commit in **native WSL terminal**:
```bash
# In Windows Terminal / WSL tab, NOT in Claude Desktop bash tool:
cd ~/work/vero-lite
pre-commit run --all-files
```

**Prevention:** Reserve Claude Desktop bash tool for read-only commands and quick checks. All commit-time operations → native WSL.

---

## Trap 6: Markdown auto-linkification in Chat client breaks `str_replace`

**Symptom:** Claude Chat client renders `[text](url)` as a clickable link in the UI. When user copies the rendered text and tries to use it in `str_replace` against the source, the search string doesn't match because the underlying markdown was preserved but display was different.

**Root cause:** UI rendering ≠ source text. Copy-paste from rendered Markdown can drop or transform syntax.

**Fix:** When transferring code/markdown between Chat and Code:
1. Use code blocks (triple backtick) in Chat — preserves raw text
2. Or paste source through `cat <<'EOF'` heredoc to bypass shell interpretation
3. Verify with `git diff` before commit

**Prevention:** Treat Chat output as "display layer". Always round-trip through repo files for execution.

---

## Trap 7: `sudo chown $USER:$USER` is the universal Claude Desktop fix

**Symptom:** Generic "permission denied" errors after Claude Desktop file operations.

**Root cause:** See Trap 2.

**Fix pattern (memorize this):**
```bash
sudo chown -R $USER:$USER <path>
```

Use after:
- Claude Desktop creates files
- Claude Desktop modifies files
- Any unexpected permission error in WSL

**Prevention:** Add to mental shell shortcut list. This is THE most common WSL+Claude Desktop interaction issue.

---

## Trap 8: `git status` block ordering hides untracked vs staged

**Symptom:** Reading `git status` output quickly leads to confusion about which files are staged vs. unstaged vs. untracked.

**Root cause:** `git status` shows three blocks:
1. "Changes to be committed:" (staged)
2. "Changes not staged for commit:" (modified, not staged)
3. "Untracked files:" (new, never added)

Easy to miss block 3 when scrolling fast, especially in long output.

**Fix:** Use porcelain format for scripts:
```bash
git status --short
# Or:
git status --porcelain
```

The two-character status codes (`A `, ` M`, `??`, `MM`) are unambiguous.

**Prevention:** Default to `git status -s` for quick checks. Use full `git status` only when explanatory text helps.

---

## Trap 9: `tee` breaks `$?` exit code — use `${PIPESTATUS[0]}`

**Symptom:**
```bash
$ pre-commit run --all-files | tee /tmp/precommit.log
$ echo $?
0    # ← LIE! pre-commit may have failed
```

**Root cause:** When piping, `$?` reflects the exit code of the LAST command in the pipeline (`tee` here, which almost always succeeds). The actual command's exit code is hidden.

**Fix:** Use `${PIPESTATUS[0]}` (bash) or `${pipestatus[1]}` (zsh):
```bash
pre-commit run --all-files | tee /tmp/precommit.log
echo "Pre-commit exit: ${PIPESTATUS[0]}"
```

Or use `set -o pipefail`:
```bash
set -o pipefail
pre-commit run --all-files | tee /tmp/precommit.log
echo $?  # Now reflects pre-commit's exit code
```

**Prevention:** Always use `set -o pipefail` in scripts. For one-off commands with logging, prefer `${PIPESTATUS[0]}`.

---

## Trap 10: Heredoc + file-based commit messages avoid quote escape hell

**Symptom:** Multi-line commit messages with backticks, quotes, or special chars get mangled when passed via `git commit -m "..."`.

**Root cause:** Shell quote escaping is fragile. Backticks trigger command substitution. Single/double quotes interact unpredictably.

**Fix:** File-based commit messages:
```bash
cat > /tmp/commit-3-message.txt <<'EOF'
docs: implement memory architecture (Tier 0-3 model)

- Slim CLAUDE.md to ~7-8KB constitution
- Add docs/STATUS.md for volatile state
- Add docs/runbooks/memory-architecture.md
- Extract conventions: tech-stack, code-style, glossary
- Document Session 4 lessons in docs/lessons/0001

Scaffolded with AI assistance (Claude Code).
EOF

git commit -F /tmp/commit-3-message.txt
```

Note `<<'EOF'` (single-quoted delimiter) — disables variable expansion and command substitution inside the heredoc.

**Prevention:** For any commit message > 1 line, ALWAYS use heredoc + `git commit -F`.

---

## Quick Reference Card

| Trap | One-line fix |
|------|-------------|
| 1 | `uv sync --extra dev` |
| 2 | `sudo chown -R $USER:$USER <path>` |
| 3 | `uv run detect-secrets scan --baseline .secrets.baseline` |
| 4 | `.gitattributes` with `* text=auto eol=lf` |
| 5 | Run pre-commit in native WSL terminal |
| 6 | Round-trip through repo files, not Chat copy-paste |
| 7 | `sudo chown -R $USER:$USER <path>` (memorize) |
| 8 | `git status -s` for porcelain output |
| 9 | `${PIPESTATUS[0]}` or `set -o pipefail` |
| 10 | `cat > file <<'EOF'` + `git commit -F file` |

---

## Related

- `CLAUDE.md` §6 — Working Patterns
- `CLAUDE.md` §7 — Git Conventions
- `CLAUDE.md` §8 — Constraints (public repo, code quality)
- `docs/runbooks/memory-architecture.md` — Cross-tool sharing model
