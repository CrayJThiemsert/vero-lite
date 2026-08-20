# Retired claims — declaring what a correction killed

> **Canonical.** Enforced by `tools/check_retired_claims.py` (pre-commit).
> Placement rationale: `CLAUDE.md` §4 — a canonical standard you look up
> deliberately lives in `docs/conventions/`; the *binding* half is the guard,
> which runs whether or not anyone reads this file.

## The problem this exists for

This repo is good at recording corrections and bad at **propagating** them. Two
measured cases in one file, both found by a human, both late:

| Corrected | Where the stale copy survived | For how long |
|---|---|---|
| *"`ms-s1-max` has no WSL DNS entry"* — s171 | `warm.sh:11`, a sibling script | **2 months** |
| the host-state gate's home — s174 | the **same file's** footer, 165 lines down | **3 sessions** |

<!-- retired: "`ms-s1-max` has no WSL DNS entry" -->
<!-- The table above quotes that dead claim to name the incident. This marker is
     an ILLUSTRATION, not a declaration: files listed in the guard's
     `_OWN_MACHINERY` exempt their own examples and retire nothing repo-wide. -->


The second is the instructive one: a correction landed at the top of the file
and the bottom of that same file kept contradicting it. Both reads were
"documented". Only one was true.

The cost is not tidiness. `services/api/config.py` defaults `ollama_host` to
`http://ms-s1-max:11434`; while the false *"does not resolve"* stood, that live
default read as inert-by-default, and a test that reached it ran `gpt-oss:20b`
twice with no `CLAUDE.md` §8 go.

**A correction that is not propagated reads as settled, while the stale copy
stays the one an operator follows.** Nothing could catch that mechanically,
because a correction records *the new answer* and the repo kept no account of
*the retired one*.

## The rule

**When you correct a claim, declare the claim you killed.** One line, adjacent
to the correction, in whatever comment syntax the file uses:

```markdown
⚠️ **Corrected 2026-07-24 (session 171).** This section used to assert that
`ms-s1-max` has *no WSL DNS entry*. Measured, it resolves fine.

<!-- retired: "`ms-s1-max` has no WSL DNS entry" -->
```

```python
# retired: "the recommender path is pinned to gemma4:26b"
```

The guard then fails any commit where that text appears anywhere live except
beside a marker declaring it.

### Choosing the text

- **Retire the wording a copy would repeat verbatim**, not your paraphrase of
  it. Matching is exact and line-bounded: a claim spanning two lines is not
  matched, and `*no WSL DNS entry*` does not match `no WSL DNS entry`.
- **Minimum 20 characters.** Shorter is *refused*, not ignored — the guard
  fails rather than silently matching unrelated prose.
- **Distinctive beats short.** If retiring a phrase would flag legitimate
  sentences elsewhere, retire a longer span that only the stale copy carries.

### Quoting a dead claim on a live surface

The commonest case, and it is **not** an exception — it is the rule doing its
job. A reconcile, a lesson or a PR narrative often repeats the retired wording
to explain what was fixed. `docs/STATUS.md` did exactly this the same day the
guard landed, and the guard flagged it.

The fix is **not** to narrow the retired text until the quote stops matching —
that is editing the artifact to satisfy the instrument. Put a marker beside the
quote instead:

```markdown
> `warm.sh:11`'s *"`ms-s1-max` has no WSL DNS entry"* was never propagated.
> <!-- retired: "`ms-s1-max` has no WSL DNS entry" -->
```

That silences the guard *and* buys the property worth having: on the surface an
agent reads every session, a dead claim now carries a label saying so, right
where it appears.

### Where it applies

- **Searched and able to declare:** every tracked `.md` `.py` `.sh` `.yaml`
  `.yml` `.js` `.toml` `.txt` file.
- **Neither searched nor able to declare:** `docs/status-archive/` and
  `docs/plans/done/`. Archives preserve superseded text *on purpose*; flagging
  them would make every rotation a violation.
- **Searched but cannot declare:** this file, the guard, and the guard's test —
  they show the syntax, so their examples are illustrations. They are still
  checked for real stale copies like anything else.
- **Out of scope entirely:** gitignored working notes (`.claude/handoffs/`),
  excluded by construction via `git ls-files` rather than by an exclude list.

## What this does NOT do

Stated so the guard is not read as stronger than it is:

- It cannot catch a stale copy that was **reworded**. It is a floor.
- It cannot know a claim *should* have been retired. Declaring is a human act;
  the guard only enforces that a declared claim stays dead.
- It is not a substitute for reading the file you are editing.

## Backfill

Existing correction blocks are not required to carry a marker retroactively.
Add one when you next touch the correction, or when a stale copy is found —
that is the moment the marker earns its keep. New corrections carry one from the
start.

## References

- `tools/check_retired_claims.py` — the guard, its scope limits, and the two
  incidents in its module docstring.
- `tests/tools/test_check_retired_claims.py` — including the same-file distant
  survivor case, the half a cross-file-only guard would miss.
- `CLAUDE.md` §4 — the knowledge-placement rule this convention instantiates:
  name the rule's consumer, then check the home is in that consumer's input.
