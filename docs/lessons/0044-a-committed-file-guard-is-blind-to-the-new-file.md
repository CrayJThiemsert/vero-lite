# Lesson #0044 — a guard that scans COMMITTED files is blind to the new file

**Session:** 232 (2026-08-15) · **Measured on:** PR #1179 · **Status:** advisory
(§1 precedence — promote to ADR if it must bind)

## The claim

A guard that enumerates the repo through **committed** files cannot see a
violation introduced by a file that is **not yet committed**. The local suite
goes green, the author pushes on that green, and CI reddens on the same commit.

## What happened

`test_ac5_no_file_outside_a_profile_lists_two_system_labels` enforces ADR-0036
D2's no-shadow-ingress-map rule. It walks `_committed_text_files()`.

A new scenario test named two system labels — a real violation. The local full
suite reported **4107 passed**. The file was still `??` untracked, so the guard
never scanned it. On commit it entered the committed set, and CI failed on
**exactly the tree that had just passed locally**.

🔴 **The blind spot sits exactly where confidence peaks.** The moment of maximum
belief — full suite green, about to push — is the moment the guard is least able
to see the new file. The only way to see it locally is to commit first and re-run,
which nobody does.

⚠️ **This is structural, not carelessness.** The suite was run in full and it was
honestly green. A "run the tests before pushing" rule does not close this gap.

## Scope — the guard family, not one test

Any guard keyed on the committed file set inherits it. Named in this repo:

| Guard | Enumerates |
|---|---|
| AC-5 shadow-registry (`tests/deploy/test_published_profiles.py`) | `_committed_text_files()` |
| R8 PLAN-reference guard | tracked docs |
| STATUS citation guard | tracked docs |

## The practice

Before pushing a **new tracked file**, stage it first so the guards can see it:

```bash
git add <file> && pytest tests/deploy/test_published_profiles.py -q
```

## The fix pattern: rule, not roster

The tempting repair is to add the file to an exemption list. That makes the test
pass while the violation stands.

The repair taken was to make the test **discover** its counter-example from
`deploy/published/` by the property it actually needs, rather than naming systems
literally. 🔴 **This is a strictly better test, independent of the CI failure:**
a hard-coded counter-example **silently stops testing anything** the day that
system gains the property — a discovered one stays correct for the fourth system
nobody has built yet.

⚠️ **Both of this session's failures of this guard came from CONVENIENCE, not
carelessness** — first a sentence that helpfully listed which systems a runbook
step applied to, then a constant easier to read than a lookup. The rule forbids
the shortcut that looks good, which is much harder to self-catch than sloppiness.

## Sibling finding — an oracle this repo does not have

The same PR's Step 4 visual pass found what **eleven green tests could not**: the
shipped disclosure had **no CSS** and painted as stray text — legible, but not
recognisable *as* a notice, which is the element's whole job.

Every test could ask *"is the text there"*. None could ask *"does it read as a
notice"*, because **this repo has no JS runtime in CI**, so there is no rendering
oracle. 🔴 **ADR-0037 D2.4 obliges the second, not the first** — bytes reaching
the browser is not disclosure. Where an obligation is about what a human
perceives, a human pass is load-bearing, not polish.

## Related

[[0039-a-self-authored-guard-inherits-the-authors-blind-spot]] ·
[[0037-a-scans-blind-spot-is-the-intersection-of-its-axes]] ·
`CLAUDE.md` §8 (scenario tests) · ADR-0036 D2 · ADR-0037 D2.4
