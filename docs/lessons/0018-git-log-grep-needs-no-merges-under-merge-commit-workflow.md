# Lesson #18: `git log --grep` filters over a merge-commit PR workflow need `--no-merges`

> **Status:** Codified 2026-05-29 (vero-bridge Step 2b — `lint_status` tool, PR #82). Surfaced while building the `docs/STATUS.md` freshness check, which classifies commits on `main` by their conventional-commit prefix.
> **Severity:** Medium — silent false positives. The query *runs clean* and returns a plausible-looking result; the bug is that the result is wrong (phantom drift) only under this repo's merge-commit workflow. No crash, no error — easy to ship unnoticed.
> **Cross-references:** `tools/vero_bridge/_status_lint.py` (the realized query). [[lesson-0010-classifier-blocks-direct-push-to-main]] (the all-PRs-to-`main`-via-merge-commit workflow this lesson depends on). PR #82 (`lint_status`). Capability inventory §2.6.

## 1. The finding

A freshness/classification query that selects commits on `main` by **conventional-commit prefix** must add `--no-merges`. Example — "is `docs/STATUS.md` stale?" = "are there *substantive* (non-`docs(status):`) commits since the head STATUS reconciled to?":

```bash
# WRONG under a merge-commit PR workflow — counts a docs(status) PR's
# merge commit as substantive drift:
git log <head>..main --invert-grep --grep='^docs(status):' --format=%h

# RIGHT — exclude merge commits so only the real underlying commits are judged:
git log <head>..main --no-merges --invert-grep --grep='^docs(status):' --format=%h
```

Without `--no-merges`, the query reports **phantom drift immediately after a clean reconcile** — i.e. it says "STATUS is stale" right after STATUS was brought current.

## 2. The mechanism

`--grep` / `--invert-grep` match against the **commit message**, not against any structural property. In this repo **every** change lands on `main` via a **merge commit** (`gh pr merge --merge`; see Lesson #10 — no squash, no rebase). So a `docs(status):` reconcile PR produces two commits on `main`:

| Commit | Subject | Matches `^docs(status):`? |
|---|---|---|
| the real one (on the feature branch) | `docs(status): reconcile …` | ✅ yes → excluded by `--invert-grep` |
| the merge commit (on `main`) | `Merge pull request #N from …/docs-status-…` | ❌ **no** → **survives** `--invert-grep` |

So the merge commit — which represents *the very reconcile you just did* — is misread as a substantive (non-`docs(status):`) commit, i.e. phantom drift. `--no-merges` drops all merge commits, leaving only the real underlying commits where the conventional-commit prefix actually lives.

## 3. Generalization

**Any git-log-based tool that filters `main` by commit-message pattern under a merge-commit workflow has this trap.** The merge commit subject is generic (`Merge pull request #N …`) and will not match a category grep, so it always falls on the "other" side of an `--invert-grep` (or gets miscounted by a positive `--grep` that expects the category to appear). Reach for `--no-merges` (or `--first-parent` if you specifically want the merge-commit view) whenever the *content* you care about lives in the non-merge commits.

Empirical confirmation (PR #82, against the real repo): with `--no-merges`, `lint_status` reported drift = exactly the 3 substantive commits of two feature PRs, with both `Merge pull request #80/#81` commits correctly excluded — byte-identical to the raw `git log` cross-check.

## 4. Sibling realization — spec named `origin/main`, reality wanted local `main`

The same tool's capability spec (written ahead of implementation) said to measure freshness against **`origin/main`**. The realized tool uses **local `main`** instead, for real-operation smoothness:

- The bridge server runs in **WSL local to the repo with no guaranteed network**; `origin/main` is a remote-tracking ref that only refreshes on `git fetch` (stale or unqueryable offline).
- Local `main` is refreshed by `gh`'s pull on every PR merge from this machine, and is queryable as a ref regardless of the checked-out branch.
- `HEAD` would be wrong too — Code usually sits on a feature branch, so it would count not-yet-merged WIP as drift.

Two transferable norms:

1. **Capability specs written ahead of implementation name an *idealized* mechanism.** When the realized deployment differs (WSL-local, no network, merge-commit workflow), the tool should diverge for real-operation smoothness, and the inventory entry gets amended **spec → as-built** (with the rationale recorded) rather than the code being forced to match a stale spec.
2. **Make the divergent knob a one-line constant** (`_status_lint.BASELINE_REF = "main"`) so a future policy change (e.g. to `origin/main` once a network/fetch story exists) is a single edit, not a refactor.

## 5. Prevention checklist

Before shipping a `git log` query that classifies commits on `main`:

1. **Does the repo use merge commits?** (Lesson #10: yes — all PRs merge-commit to `main`.) If so, decide explicitly whether merge commits should count. For prefix/category filters the answer is almost always **no → add `--no-merges`.**
2. **Write a test with a real merge commit.** Build a temp git repo, merge a branch with `--no-ff`, and assert the merge commit is handled as intended. (`tests/vero_bridge/test_lint_status.py::test_merge_commit_after_head_does_not_count` is the regression guard.)
3. **Anchor refs against the deployment, not the spec.** Prefer local `main` over `origin/main` for a network-less, locally-rooted server; keep the ref a named constant.
4. **Fail closed.** A git query that errors (bad ref, not a repo) should degrade to a safe default (here: `fresh=False` — "cannot confirm fresh ⇒ treat as needs-attention"), never raise across a tool boundary.
