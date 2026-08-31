# Lesson #0053 — two sessions agreeing through one instrument is one measurement

**Session:** 265-266 (2026-08-31) · **Measured on:** one config line, two
independent closeout handoffs, six symptoms, one wrong root cause ·
**Status:** advisory (§1 precedence — promote to ADR if it must bind)

## The claim

Two parallel Code sessions independently investigated the same repo-wide `git`
weirdness. They worked in different trees, took different measurements, and
**converged on the same diagnosis**:

> *"The index stat cache is unrefreshable on this UNC mount. One mechanism,
> several faces. Expect it in every tree and every session. It is caused by no
> session."*

Both handoffs recorded that conclusion with measurements attached — 33-of-35
stat-dirty-only in one tree, a byte-identical `D` entry in the other,
`update-index --refresh` exiting 1 in both. Both explicitly warned the next
session not to invert it. It read as strongly corroborated.

**It was wrong.** The cause was one line in the shared `.git/config`:

```
[core]
	worktree = /home/crayj/work/vero-lite/.claude/worktrees/brave-mirzakhani-025e55
```

Every `git` command run from the main checkout used the main `.git` for HEAD and
index, and **a different session's worktree for the files**. Nothing was phantom.
Nothing was a filesystem artifact. `git` reported the truth about a comparison
nobody meant to make.

**The corroboration carried no information, because both sessions were reading
through the redirected config.** Two observers sharing one broken instrument
produce one measurement, stated twice — and the second statement feels like
confirmation precisely because it agrees.

## What happened — six symptoms, one line

| Symptom, as recorded | What it actually was |
|---|---|
| `D gold_fleet.yaml` while the file sat byte-correct on disk | the *other* tree has no such file |
| `tools/notify/*.sh` mode `100755`→`100644` | the *other* tree's files, written from Windows, exec bit stripped |
| `update-index --refresh` says `needs update`, never sticks | it was stat-ing the *other* tree |
| 33 of 35 entries "stat-dirty only" | HEAD-vs-other-tree diff, honestly reported |
| `git merge` / `git checkout` abort: *"local changes would be overwritten"* | git correctly protecting the *other* tree's files |
| `git checkout -- <paths>` returns **rc=0** and no file appears | it wrote them — into the *other* tree |

The last row is the one that broke the story open. A tool reporting success while
its effect is absent is not a filesystem being flaky; it is a tool pointed
somewhere else.

Two hypotheses were tested and refuted first, both cheap and both wrong:
`skip-worktree` / `assume-unchanged` flags (all 1183 index entries were `H`) and
sparse-checkout (`core.sparseCheckout` unset, no sparse file). Refuting them is
what forced the question *"where is git actually writing?"*

## The test

**When a command reports success and the effect is absent, ask where the tool is
pointing before you ask whether the substrate is broken.** For git that is one
command, and it is nearly free:

```bash
cd <repo> && pwd && git rev-parse --show-toplevel
```

Two different answers = every subsequent `git status`, `diff`, `checkout` and
`add` in that shell is about a tree you are not looking at. This session ran that
comparison only after ~15 measurements had been spent building an elaborate
theory of the mount.

The general form, one level up:

1. **Count instruments, not observers.** Before treating agreement as
   corroboration, ask what each observer *ran*. Two sessions, two trees, two
   handoffs — and one `git` reading one config. Independent observers sharing an
   instrument give you `n=1`.
2. **A diagnosis that explains every symptom is not thereby correct.** The stat-cache
   theory explained all six rows above. So did the real cause. Explanatory
   completeness discriminates nothing when two hypotheses both have it — only a
   prediction they *disagree* on does. Here: *"does `git` write where I am
   standing?"*
3. **Prefer a discriminator that reads the tool's own state over one that reads
   its output.** `show-toplevel` asks git what it thinks it is doing. `git status`
   asks git what it found — and a mis-aimed tool answers that one fluently.

### 🔴 The prescribed discriminator was not read-only

Both handoffs prescribed a two-step test — `git update-index --refresh`, then a
content diff — and both called step 1 a *"cheap test"*. It is not: on a path whose
difference is a **mode** difference, `--refresh` **writes the new mode into the
index**. Running it on two files here flipped them from ` M` (unstaged) to `M `
(staged) — a mode change `100755`→`100644` staged for commit, from a command
invoked purely to look. Recovered with `git update-index --chmod=+x`, verified by
`git diff --cached HEAD` returning zero lines.

If a diagnostic is going to be recommended as safe to run freely, its
write-behaviour is part of the recommendation.

### The audit that does not go through the broken instrument

`git status` could not be trusted, so the tree was verified by hashing every
tracked file and comparing against the index — no stat cache, no worktree
resolution in the comparison:

```bash
git ls-files > paths.txt
git hash-object --stdin-paths < paths.txt > disk.txt
# join against `git ls-files -s`, compare blob hashes
```

It found **more** than `git status` ever showed: 6 stale files (including two
that had never appeared in any status output) and 1 tracked file missing from
disk entirely — `docs/plans/0117-*.md`, the artifact the next phase of work was
built on, which `git pull` had reported creating.

## What this does NOT say

- It does not say the two handoffs were careless. Every individual measurement in
  them is reproducible and was correct; only the **inference from agreement** was
  unearned.
- It does not say cross-session cross-checking is low value — it has caught real
  errors here repeatedly. It says agreement is evidence about the *observation*,
  and evidence about the *cause* only when the instruments differ.
- It does not generalise to "suspect config first". Config was the answer once.
  The transferable move is the `show-toplevel` check, which is cheap enough not to
  need a suspicion to justify it.

## Where this fires

- **the `show-toplevel` check** → `.claude/skills/git-workflow/` (loads whenever
  committing, pushing, merging, or diagnosing a git command that behaved oddly)
- **the instrument-vs-subject test** already lives in
  `.claude/skills/code-operational-policy/` (Lesson #0046); this session is the
  case where the *instrument* was shared by the two parties comparing notes.

## References

- Lesson #0045 — a probe that shares fate with its subject cannot fail. Same
  shape, one layer out: here the two *reviewers* shared fate with the instrument.
- Lesson #0038 — shared guard preprocessing converges and misattributes.
- Lesson #0046 — when a check and a claim disagree, go to the artifact. This
  session is the case where both parties went to the artifact and still missed,
  because they went through the same lens.
- Lesson #0048 — repeat sampling establishes a rate, not a cause.
- `CLAUDE.md` §8 "Command Output Is Evidence — Do Not Corrupt It" — the same
  family, for shell plumbing rather than tool aim.
