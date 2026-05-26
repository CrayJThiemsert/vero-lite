# Lesson #11: `gh pr` body with backticks — always use `--body-file`, never `--body "$(cat ...)"`

> **Status:** Codified 2026-05-26 (Session 12, PR #29 incident + fix).
> **Source:** Direct observation 2026-05-26 ~14:00 +07 in Session 12.
> `gh pr create --title "..." --body "$(cat /tmp/pr-step2.md)"` shell-expansion path corrupted PR #29's body — every backtick-delimited inline code segment was eaten by bash and re-interpreted as command substitution. The PR was created with the corruption; recovery required a follow-up `gh api --method PATCH` with `-F body=@/tmp/pr-step2.md` (which preserves bytes verbatim).
> **Severity:** Medium (cosmetic + readability damage; no destructive effect, but the corrupted PR body is the durable record reviewers see).
> **Cross-references:** Lesson #4 (sibling — WSL `bash -c` variable-expansion trap; different mechanism, same class of "shell ate your content"). CLAUDE.md §7 (this Lesson extends the commit-message hygiene rule to `gh pr` operations).

## 1. The finding

When using `gh pr create` / `gh pr edit` to submit a PR body that contains markdown inline code (backticks), do **not** use `--body "$(cat FILE)"` — the file content gets re-parsed by bash and backtick segments are interpreted as command substitution. **Always use `--body-file FILE`** (gh's native flag, no shell expansion).

The same applies to any `gh` command that accepts a multi-line content argument: `gh issue create --body-file`, `gh release create --notes-file`, etc.

## 2. The mechanism

Recipe for the failure:

```bash
# THE TRAP — do NOT do this
gh pr create --title "feat: foo" --body "$(cat /tmp/pr-body.md)"
```

What bash does, step by step:

1. **Command substitution:** `$(cat /tmp/pr-body.md)` runs `cat` and substitutes the file contents into the command line.
2. **Inlined content lands inside double quotes:** the substituted file content is now part of the `--body "..."` argument, still surrounded by the outer double quotes.
3. **Double quotes preserve `$` and `` ` ``:** unlike single quotes, double quotes allow further parameter expansion (`$var`) and command substitution (`` `cmd` ``).
4. **Markdown backticks fire as command substitution:** a line like ``- `tools=[Read, Grep]` — frontmatter ratification`` contains a backtick-delimited segment. Bash sees `` `tools=[Read, Grep]` `` and tries to execute it as a shell command:
   - `tools=[Read,` — tries to assign `tools=` to an empty array slot, parses `[Read,` as an argument, sees no closing bracket — error
   - Subsequent backtick segments yield `command not found`, `permission denied` (when the segment starts with a path), etc.
5. **Stripped output sent to gh:** bash silently strips the failing backtick segments and passes the eviscerated string to `gh pr create`. The PR is created with a body that has every backtick-delimited word removed.

The damage is invisible at submission time — `gh pr create` reports the PR URL with no warning. You only notice when you (or a reviewer) opens the PR and sees `- Read-only subagent: , , , ` where the four backtick-delimited values used to be.

## 3. Reproduction

Save a file with backticks:

```bash
cat > /tmp/repro-body.md <<'EOF'
- Field `foo` is required
- Field `bar` is optional
EOF
```

Then run the trap:

```bash
gh pr create --title test --body "$(cat /tmp/repro-body.md)" --dry-run
# observed: --body argument becomes:
#   "- Field  is required\n- Field  is optional"
# (the backtick-quoted `foo` and `bar` are gone)
```

Then the safe form:

```bash
gh pr create --title test --body-file /tmp/repro-body.md --dry-run
# observed: --body-file reads the file directly, bytes preserved.
```

## 4. The fix (one-liner)

Replace every `--body "$(cat FILE)"` with `--body-file FILE`. Same for `--notes-file`, `--body-file` on `gh issue create`, etc. The flag exists on every `gh` subcommand that takes a body argument.

If you must use `--body` (e.g. dynamically constructed content not in a file): pre-quote with `printf '%s' "$content"` into a temp file first, then `--body-file` that temp file. Do not try to escape backticks inline — the gh-native flag is one character longer (`-file`) and skips the entire failure mode.

## 5. Recovery (when the PR was already created corrupted)

PR-#29 recovery path, documented for next time:

```bash
# gh pr edit --body-file FILE also works, but hit a Projects-classic
# deprecation graphql error in session 12. The gh api fallback is
# bulletproof.
gh api --method PATCH /repos/<owner>/<repo>/pulls/<NUMBER> \
  -F body=@/tmp/pr-body.md
```

`-F body=@/path` is the gh CLI convention for "read this file and submit verbatim." Identical effect to `--body-file`, no shell expansion, works against the raw GitHub REST API which is robust to whatever Projects-classic field deprecations the higher-level subcommands trip over.

## 6. Why this matters (cross-cutting)

Same class as Lesson #4 (WSL `bash -c` variable expansion) but a different mechanism. Both share the diagnostic shape: **shell-side content interpretation between you and your destination tool**. The pattern shows up wherever:

- A subprocess argument is constructed via command substitution
- The substituted content is wrapped in double quotes (not single)
- The content contains shell metacharacters (`$`, `` ` ``, `!` in some shells)

For Code-tab work, the recurring instances are:

1. **`git commit -m "$(cat FILE)"`** — already addressed in CLAUDE.md §7 (use `git commit -F FILE`)
2. **`gh pr create --body "$(cat FILE)"`** — *this Lesson*; fix is `--body-file FILE`
3. **`gh issue create --body "$(cat FILE)"`** — same trap, same fix
4. **`gh release create --notes "$(cat FILE)"`** — same trap, fix is `--notes-file FILE`

The general rule: **prefer the tool's native file-input flag over shell command substitution**, every time. The tool reads the file in its own process; bash never sees the content.

## 7. Promotion

CLAUDE.md §7 amendment (this PR): added a sibling bullet to the existing commit-message-hygiene line:

> **PR / issue / release bodies:** Same hygiene as commit messages. Use `gh pr create --body-file PATH` (and the equivalent `--notes-file` / `--body-file` flags on `gh issue create` / `gh release create`), never `--body "$(cat PATH)"`. Backticks in markdown bodies trigger command substitution inside the double-quoted shell arg and silently corrupt the submitted content. See Lesson #11.

## 8. What did NOT work (rejected mitigations)

- **Escape backticks before substitution** — fragile (sed/awk on markdown is brittle; nested escapes get lost). The `--body-file` flag is shorter to type *and* doesn't require any pre-processing.
- **Single quotes around `$(cat ...)`** — single quotes prevent the outer `$(cat ...)` from running at all (the file path becomes a literal string). Doesn't fix the inner-substitution issue even if it ran.
- **`printf '%q' "$content"` to shell-quote** — works but verbose and slow; `--body-file` skips the whole problem.
- **Switch to heredoc piped to stdin** — gh subcommands do read from stdin if `--body -` is passed, but the discipline ("which subcommands? what flag means stdin?") is harder to remember than "always `--body-file`".

## 9. Open questions / future watch

- The Projects-classic deprecation graphql error from `gh pr edit --body-file` (observed in PR #29 recovery) may bite future edits — track whether `gh` ships a fix or if `gh api PATCH` becomes the durable workaround.
- This Lesson does not extend to `gh comment` / `gh pr comment` — those subcommands ARE worth re-checking for the same trap (the `--body-file` flag exists there too per `gh pr comment --help`).
