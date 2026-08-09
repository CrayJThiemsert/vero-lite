# Lesson #0039 — A guard written by the author of the thing it guards inherits that author's blind spot; an enumerated predicate must come from measurement

**Date:** 2026-08-08 (session 214)
**Class:** advisory (guard design / verification)
**Trigger:** `deploy/published/deploy.py` shipped with a green 3977-test suite and
a guard written *specifically* to catch remote-command re-parsing. Its very first
command against the real host failed on re-parsing — and that guard was **green
over the failing command**.
**Cross-references:** [[0024-rules-must-live-where-the-enforcer-looks]] (a rule
outside the enforcer's input is advisory — this is its sharpest case: the rule was
*inside the same file*, three times); [[0037-a-scans-blind-spot-is-the-intersection-of-its-axes]]
(coverage across axes — this is the complement: the predicate *within* one axis);
[[0007-harness-exit-code-artifact]] (the hazard family). PRs
[#1074](https://github.com/CrayJThiemsert/vero-lite/pull/1074)–[#1078](https://github.com/CrayJThiemsert/vero-lite/pull/1078).

## The lesson

**When a guard's predicate is an *enumeration* — a set of characters, a list of
names, a set of forbidden shapes — and its author is also the author of the code
under guard, the enumeration reproduces the author's model of the hazard. It
therefore goes green on exactly the cases the author did not think of, which are
exactly the cases that bite.**

Writing the rule down does not help. Writing a guard does not help *if the guard's
predicate is self-supplied*. What closes it is an **external source for the
predicate** — the system itself, measured.

## 1. The rule was written down three times, and broken three times

Each of these is a comment stating a rule correctly, with the adjacent code
violating it. All three shipped. All three were caught by *running* the thing,
never by reading it.

| # | The comment said | The code did | Fixed in |
|---|---|---|---|
| 1 | `_ssh` docstring: remote commands are "literals with no `$`, **no inner quotes** and no pipes" | shipped `ssh … python -c "import …;print(…('http://…'))"` | [#1075](https://github.com/CrayJThiemsert/vero-lite/pull/1075) |
| 2 | the same docstring, after #1075 hardened it | shipped `--format={{.Id}}` on five remote commands | [#1076](https://github.com/CrayJThiemsert/vero-lite/pull/1076) |
| 3 | `build_and_ship`: "compose interpolates the WHOLE file … **a build fails without it**" | passed no such variable; `compose config` exits 1 | [#1077](https://github.com/CrayJThiemsert/vero-lite/pull/1077) |

The author knew the rule in every case — it is written, in their own words, inches
away. **A comment has no enforcer.** That is the trivial half of the lesson and it
is already covered by Lesson #24. The interesting half is what happened next.

## 2. The guard written to catch #1 was green over #2

#1075 added `test_no_remote_command_carries_anything_a_shell_would_reparse`. It
walks every `ssh` argv recorded in a scenario run and rejects any word containing
a character the far-side shell would re-parse. Its hazard set was:

```python
hazards = set("\"'$;|&`<>()")
```

That set is a good-faith enumeration of shell metacharacters. It has no braces.

One hour later, the first command that reached the deploy host returned:

```
$ ssh ms-s1 docker version --format={{.Server.Version}}
unknown shorthand flag: 'e' in -encodedCommand
```

Five of eight probes failed identically. The host's ssh shell is **PowerShell**
(`ssh <host> 'echo %COMSPEC%'` returns the string unexpanded, so it is not cmd),
and PowerShell reads `{…}` as a script block.

So the guard, written *for this exact failure mode*, was **green over the exact
command that failed** — because `{` and `}` were not in a set the same author
assembled from the same mental model that produced the bug.

## 3. Why the usual remedies do not reach this

- **"Write the rule down."** Done, three times, in the file (§1).
- **"Add a test."** Done — and the test was blind in the author's blind spot (§2).
- **"Have the guard read the real artifact."** This guard *did* read the real
  artifact: it walked the actual recorded argv list, not a constant. Reading the
  artifact fixes *drift*; it does not fix a **predicate** that never described the
  hazard correctly. That distinction is the substance of this lesson.
- **"Widen the set."** Only in hindsight. The point is not that braces should have
  been listed; it is that nothing in the offline world could have told the author
  to list them. `docker`'s own documentation uses `--format={{…}}` everywhere.

## 4. What actually caught it

A read-only reconnaissance phase, run before any mutation, containing a probe
whose *purpose* was to answer a question the author knew they could not answer:

```bash
ssh ms-s1 docker version --format={{.Server.Version}}
```

carried in the redeploy PR's own body as an explicitly **unverified assumption**,
with a pass/fail read fixed before the run and the rule *a failed phase means no
deploy*. Because that rule held, the host was never touched across three rounds of
fixing.

The generalisation: **name the assumption you cannot check offline, then design
the cheapest possible probe whose only job is to check it, and run that before
anything irreversible.** An unverified assumption that is *written down* is worth
far more than one that is merely absent — it becomes a probe.

## 5. Operational form

When writing a guard whose predicate is an enumeration, ask where the enumeration
came from:

| Source of the predicate | Trust |
|---|---|
| Read out of the system under guard (a file, a schema, a live response) | **Sound** — it cannot disagree with reality |
| Derived from a measurement recorded in the repo | **Sound**, with the measurement cited so it can be re-checked |
| Enumerated by the author from experience | **Provisional** — it will be green on the author's blind spot; say so in the docstring and treat the first contact with the real system as the real test |

The third row is not forbidden. It is often the only thing available. What is
forbidden is **reading a green result from a row-three predicate as coverage**.

`test_every_required_compose_variable_has_a_build_placeholder` (#1077) is a
row-one example worth copying: it extracts every `${VAR:?…}` from the committed
compose file rather than listing the variables it knows about, so a new required
variable reddens it. It also needed one correction before it was right — its first
version matched the compose file's *comments*, and the file explains that syntax
in prose while arguing against using it. Even a row-one predicate needs its input
scoped to declarations rather than to everything that looks like one.

## 6. Scope

This is advisory and about **guard design**, not about verification generally. It
does not license shipping guards whose predicates are guesses; it says that when
you must, you record that fact where the next reader sees it, and you do not let a
green run from such a guard stand in for contact with the real system.

Nor does it soften the surrounding disciplines it depends on: the pre-committed
pass/fail read, the refusal to proceed on a failed phase, and non-vacuity probes
restored from `/tmp` rather than `git checkout`. Those are what made three rounds
of self-inflicted defects cost nothing but time.

## 7. The corollary — an instrument's self-report is not evidence about itself (session 217)

Sections 1–6 are about a guard whose **predicate** the author supplied. The same
blind spot has a second face, met three times while executing PLAN-0102: a
**report** the instrument makes about its own work.

**(a) A guard that grepped its own documentation.** A structural guard asserted
that `stop_continuation.py` no longer references any retired identifier, by
searching the source text. It went RED against a **correct** file — the module
docstring *explains the retirement* and therefore names those identifiers. The
predicate ("the name appears anywhere") could not tell a call from a comment, so
it punished the file for documenting itself, and got redder the better the
documentation was. Fixed by walking the **AST**, which sees only real bindings.
Generalisation: *when a guard's subject is code, its input must be the parsed
program, not the file's characters.*

**(b) A rotation script that reported its own tally.** A script pruned
`docs/STATUS.md` and then printed how many rows and blocks remained. Its counting
regexes were double-escaped inside an f-string, so it reported `RD rows now: 24 /
CF blocks now: 0` — both impossible. The rotation itself was correct; only the
self-report was wrong. It was caught because the numbers were *absurd*, which is
luck, not method: a report off by one would have been believed and copied into a
commit message as evidence.

**The operational form.** *A number that will become evidence — quoted in a
commit message, an acceptance criterion, a decision — must be re-derived with a
different instrument than the one that produced the work.* In the case above the
re-derivation was `awk`/`grep` over the written file rather than the script's own
tally; the second numbers are the ones that shipped.

**(c) The tool built to close section 1's gap missed its own headline example.**
`tools/excision_scope.py` was written to enumerate an excision's blast radius. Its
module docstring led with `_state_path` as the motivating case. Its first version
keyed symbols by **bare name across all modules**, so the three `_state_path`
definitions in the hooks tree collapsed into one node; one copy had a live caller,
so the collapsed node read as alive and the tool reported nothing. Its unit
fixtures all passed. What caught it was running the tool against the **real
pre-excision tree** with an oracle taken from history — the symbols the executed
PLAN is on record as having missed. Fixed by qualifying nodes as `module::name`.

That is section 4's remedy applied to a tool rather than a guard: **the external
source for the predicate was the system itself, measured.** A fixture the author
wrote could not have caught it, because the fixture encodes the same model of the
problem that produced the bug.
