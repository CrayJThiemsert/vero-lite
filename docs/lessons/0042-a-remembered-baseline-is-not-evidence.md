# Lesson #0042 — A remembered baseline is not evidence: an environmental-RED floor drifts, so attribute by cause and let the count fall out

**Date:** 2026-08-14 (session 230)
**Class:** advisory (verification hygiene / environment baselines)
**Trigger:** Rehoming four unhomed operational mechanics from the session-229
closeout. One of them was the claim *"the Windows-worktree environmental-RED
baseline is 7, not 6."* Checking how 6 became 7 turned out to be the durable
part; the number itself is the perishable part.

## The lesson

Some test failures are **environmental** — they fail for a property of *where*
you ran them, not of the code. In a Windows-created worktree, `pytest tests/`
has a non-zero RED floor for this reason. The natural way to carry that
knowledge forward is a **count**: *"expect 6 REDs, an unexplained 7th is real."*

**That count is a decaying artifact, and it decays silently.** It changes
whenever a new test happens to touch the environment-sensitive surface — which
is an ordinary, blameless event that nobody involved would flag as
baseline-affecting. Nothing announces the drift. The stale count simply keeps
being repeated, and the first genuinely new failure gets absorbed into it.

**So do not carry the number. Carry the causes.** The cause list is stable and
explanatory; the count is a derived, perishable summary of it. Attribute every
RED to a named cause, and let the total fall out of that attribution. A RED you
cannot attribute is signal — *regardless of whether the total matches what you
expected.*

The count-first habit fails in the direction that hurts: it can only ever tell
you *"the number matches, carry on."*

## 1. What actually happened, and what it was not

Session 207 (2026-08-05) ran the suite in a Windows worktree and recorded:

> `pytest tests/` **3471 passed, 6 failed** — exactly the known Windows-worktree
> false-RED set (5 `tests/handoffs/` + `test_check_plan_archive_refs`), **no 7th**.

Session 229 (2026-08-14) measured **7**.

It is tempting to file the 6 as stale and move on. That flattening is exactly
what CLAUDE.md §6 forbids, and the evidence disposes of it cleanly:

```
git log --diff-filter=A -- tests/deploy/test_published_profiles.py
→ 20a6326  2026-08-10  feat(deploy): author procurement's published profile …
```

The 7th failure —
`tests/deploy/test_published_profiles.py::test_ac5_no_file_outside_a_profile_lists_two_system_labels`
— **did not exist when session 207 measured**. It landed five days later, and it
fails from a cause already on the list (git enumeration under a UNC gitdir).

**Classification: `superseded by new info` — NOT `was an error`.** Session 207's
6 was correct, correctly measured, and correctly enumerated when written. Its
explicit *"no 7th"* was true at the time. The reasoning lineage is intact and
worth keeping: a later measurement of 7 does not retroactively convict the 6.

The distinction is not bookkeeping etiquette. "Was an error" prompts you to go
looking for the mistake in how session 207 measured — and there is none to find.
"Superseded" points at the real mechanism: **the floor moves**.

## 2. Why the count-first framing hid it

The two enumerations look different but describe the same files:

| Session | Enumeration as written | Total |
|---|---|---|
| 207 | 5 × `tests/handoffs/` + 1 × `test_check_plan_archive_refs` | 6 |
| 229 | 2 × UNC-gitdir enumeration + 4 × PreToolUse absolute-path shape + 1 × `goal.json` leak | 7 |

Session 229 regrouped the same five `tests/handoffs/` failures into *4 +
1* (the `goal.json` leak has a genuinely different cause from the four
path-shape ones) and added the new deploy test to the UNC-gitdir group. So the
one real change — a new test — is buried inside a table where **every** number
appears to have changed. Had either session recorded *causes* as primary, the
delta would have read as "same causes, one new member," which is a
non-event, instead of "6 vs 7," which looks like a contradiction demanding
someone be wrong.

## 3. The current cause list (the durable part)

Measured session 230 in `.claude/worktrees/`, at `71b8f6b`, via a bare
`uv run --extra dev pytest tests/`:

```
7 failed, 4045 passed, 9 skipped, 2 warnings in 574.94s
```

| Cause | Count | Tests |
|---|---|---|
| **git enumeration under a UNC gitdir** — WSL git cannot resolve the worktree's gitdir, so repo-wide file enumeration returns nothing | 2 | `tests/tools/test_check_plan_archive_refs.py::test_the_real_repo_is_clean`<br>`tests/deploy/test_published_profiles.py::test_ac5_no_file_outside_a_profile_lists_two_system_labels` |
| **PreToolUse absolute-path shape** — the hook's path matching assumes a POSIX repo root; a UNC root changes the shape | 4 | `tests/handoffs/test_pretooluse_goal_evaluator_write_deny.py::test_write_goal_json_absolute_posix_allowed`<br>`tests/handoffs/test_pretooluse_plan_subagent_write_deny.py::test_absolute_repo_path_adr_allowed`<br>`tests/handoffs/test_pretooluse_research_path_deny.py::test_absolute_repo_path_denied`<br>`tests/handoffs/test_pretooluse_status_scribe_write_deny.py::test_absolute_repo_path_status_allowed` |
| **live `goal.json` leaks into the test** — the hook test does not isolate `CLAUDE_GOAL_PATH`, so a real session goal changes the outcome | 1 | `tests/handoffs/test_stop_continuation.py::test_fail_open_e2e_unanswered_dispatch_releases` |

This table will go out of date the same way 6 did. **That is expected and is not
a defect in the table.** What must survive is the three causes and the habit of
attributing to them.

## 4. What to do instead

- **Attribute, then count.** For each RED, name which cause it belongs to. An
  unattributable RED is real — even if the total is the number you expected.
  A total that matches is not a pass; it is a coincidence you have not checked.
- **Re-measure; never quote a count from memory or from a handoff.** Nothing
  emits an event when a new test joins the environment-sensitive surface.
- **For a true CI-scope gate, use a WSL-native checkout, where the expected
  count is 0.** A zero-based gate cannot drift; a 7-based gate is a
  standing invitation to absorb a real failure. Use the worktree for isolation,
  not for gating.
- **When a baseline moves, classify it** (CLAUDE.md §6): `superseded by new
  info` vs `was an error`. Check whether the delta is explained by something
  that *landed after* the earlier measurement before concluding anyone erred.

## 5. Getting a WSL-native gate when you are stuck in a worktree

The advice above is circular if you are already *in* a Windows worktree. You do
not have to move the work — clone into WSL-native space and run the gate there:

```bash
git clone --no-hardlinks /home/crayj/work/vero-lite /tmp/guardverify
cd /tmp/guardverify && git checkout <base-sha>
cp <your changed files> /tmp/guardverify/<same paths>
git add -A          # the enumeration guards read `git ls-files`
<worktree>/.venv/bin/python -m pytest tests/ -q
```

Notes from doing this (session 230):

- **`git clone` from a local path only reads the source.** It is safe even when
  the main checkout is on another branch with a concurrent session's
  uncommitted work — which was the case here.
- **`git add -A` is load-bearing, not tidiness.** The two enumeration guards
  read `git ls-files`; an unstaged new file is invisible to them, and the guard
  passes *vacuously* over a set that does not contain your change.
- **The clone has no `.env`** (gitignored, so not cloned), so DB-backed tests
  **skip** rather than run: 399 of them here. The clone run is therefore not a
  superset of the worktree run — the two are **complementary**. Check the
  arithmetic closes (`4045 + 9 + 7 = 4061 = 3662 + 399`) before claiming
  everything was covered.
- Reusing the worktree's `.venv/bin/python` avoids building a second
  environment, and avoids `uv` mutating a venv from the wrong context
  (Lesson #3 §A3).

## Related

- **Lesson #3** (`0003-code-tab-worktree-lifecycle-traps.md`) — the worktree
  environment these REDs come from; §A2 for the UNC-gitdir cause
- **Lesson #2** — UNC gitdir binding, the root mechanism
- **Lesson #0029** (`verify-full-suite-not-subset`) — the sibling failure: there,
  the *scope* of the gate was wrong; here, the *reference point* is
- **Lesson #0007** (`harness-exit-code-artifact`) — why the suite's own summary
  line, not an echoed exit code, is the trustworthy verdict. During this
  session's measurement the appended `PYTEST_RC` read `0` on a 7-failure run
- **CLAUDE.md** §6 ("Verification is hygiene, not a verdict" — the
  `superseded by new info` vs `was an error` classification), §8 (Code Quality)
- **`code-operational-policy` skill** — Worktree mode; points here
