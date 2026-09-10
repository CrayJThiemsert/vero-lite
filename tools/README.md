# `tools/` — the catalogue

**Read this before you hand-roll a script.** Every entry below already exists, and most
of them exist *because* a session hand-rolled the same thing and got it wrong in a way
that was measured. Session 253 rebuilt a probe-battery driver from scratch and re-made
four defect classes an earlier session had already retired — while publishing `13/13`.
Session 261 wrote a CI wait four times in one hour and got four different wrong answers.

PLAN-0115 named the failure that this file exists to close:

> The MUST tier ships a capability; the ALSO tier ships the reason anyone would reach for
> it. **Shipping the tool while cutting the pointer yields a tool nobody knows to use.**

**20 entries: 12 top-level scripts + 8 packages.** They fall into three groups by *who
invokes them* — and only the first group is yours to remember.

---

## 1. Reach for these deliberately — nothing fires them for you

This is the group that a wrong tool choice actually costs you. Nine of the guards in §2
run themselves; these eleven do not.

| Tool | What it answers | The measured failure it replaces |
|------|-----------------|----------------------------------|
| **`probe_battery/`** | "Did my mutations redden the assertions I predicted?" — the witnessed-RED discipline `CLAUDE.md` §8 makes binding. Has its own [`README.md`](probe_battery/README.md). | Before it, **every session rebuilt the driver in `/tmp`**; s253 measured a fresh one re-making four already-fixed defect classes at once. 🔴 **Never hand-roll this.** |
| **`probe_coverage.py`** | "What did I never probe?" — reports which of a test module's claims no probe ever reddened. | s251: a battery printed PASS while **12 of 33 items had never been reddened**, two of them load-bearing (lesson #0047). |
| **`tally.py`** | Breaks a record file down by a field **and proves the breakdown accounts for every record**. `--expect` refuses when the value set differs from the one you pre-declared. | s288 tallied one table from two different instruments (`grep -c -i timeout` vs the actual field); the buckets summed to **139 against 140 lines** and nothing in the reading said so. |
| **`excision_scope.py`** | The blast radius of deleting a set of symbols — walks the call graph **forwards**, to callees only the doomed code reaches. | PLAN-0102's review walked the graph *backwards* only, and missed exclusively-owned callees **three separate times**. `ruff` cannot close this: it flags a dead import, never a dead private function. |
| **`hook_copies_audit.py`** | Which copy of the Stop-arm hooks each worktree is running (sha256 per worktree). **Read-only by ruling** (SD-6, Cray typed s280) — it lists, it never prunes. | A hook change on `main` does not reach a worktree checked out before it. Enumerates by **filesystem, not `git worktree list`** — the porcelain reported **6 where 19 exist**, all marked prunable, because their gitdirs are UNC paths git cannot resolve from WSL. |
| **`ci/wait_for_ci.py`** | "Did CI pass at THIS sha" — without ever inferring a pass from silence. | s261's four hand-rolled attempts: "no checks registered yet" read as settled-green; a redirect placed outside the `wsl bash -lc` argument; an exit code asserted from memory; and a `$(...)` inside an `until` that expanded a layer early and **could not terminate**. 🔴 A `PreToolUse` hook now denies the hand-rolled shape. |
| **`golden_trace/`** | Produces the golden-trace corpus by running the **real engine**, so the fixtures are comparable to the system. | Before it the corpus had **no producer at all** — hand-placed JSON, and five harness tests validating each file *against itself*. |
| **`handoffs/render_transcript.py`** | Renders a session JSONL transcript to flat Markdown, for handing a complete transcript to another tab. | The Code tab collapses tool/process blocks by default. |
| **`handoffs/handoff_status.py`** | Dashboard over `.claude/handoffs/session-NN/` — counts by phase/status/actor, chains, open `NEEDS_INPUT`, parse failures. | — |
| **`handoffs/validate_handoff.py`** | Validates handoff frontmatter against the PLAN-004 schema, by hand (`--all` walks every session). | ⚠️ **Frontmatter shape only.** It never reads the body, and the three `references_*` lists are passed through unvalidated — a fabricated SHA validates clean. |
| **`probes/vero_bridge_probe.py`** | A minimal MCP stdio server used to answer bridge questions empirically (PLAN-0012 OQ-B / OQ-T3). | — |

### Three names that sound alike and are unrelated

- **`probe_battery/`** — the *driver*: runs mutations, reports what each witnessed.
- **`probe_coverage.py`** — the *coverage report*: what no probe ever touched.
- **`probes/`** — an MCP *liveness probe* for the bridge. Nothing to do with either.

---

## 2. These fire on their own — listed so you don't rebuild one

Nine `pre-commit` hooks invoke `tools/` scripts. You do not need to remember them; you
need to not re-implement them.

| Hook id | Script | Enforces |
|---------|--------|----------|
| `handoff-frontmatter` | `handoffs/precommit_handoffs.py` | Handoff frontmatter shape + refreshes `INDEX.md` (latest session dir only) |
| `status-size-guard` | `check_status_size.py` | `docs/STATUS.md` byte ceiling (rotation policy R1) |
| `archive-size-guard` | `check_archive_size.py` | `docs/status-archive/*.md` byte ceiling (R4) |
| `status-citation-guard` | `check_status_citations.py` | No tracked artifact cites `docs/STATUS.md` by line number (R7) |
| `plan-archive-ref-guard` | `check_plan_archive_refs.py` | No tracked artifact cites a PLAN by its pre-archive path (R8) |
| `alembic-model-registration` | `check_alembic_model_registration.py` | Every ORM module is imported by **both** metadata registration sites |
| `retired-claim-guard` | `check_retired_claims.py` | A claim declared `retired:` does not survive anywhere live |
| `ac-consistency-guard` | `check_ac_consistency.py` | An AC's ledger agrees with itself (STATUS `CLOSED` ⇔ PLAN checkbox) |
| `battery-definition-lint` | `check_battery_definitions.py` | Every probe battery can still **address** what it declares |

⚠️ **What this group does NOT do.** Every one of these verifies a *lexical shape* — a
regex, a byte count, a path's resolvability, a checkbox's state — or a *pairwise
agreement between two artifacts*. None opens a cited target and asks whether the sentence
about it is true. `check_ac_consistency.py` says so in its own docstring:

> Neither check knows whether an AC *should* be closed. They compare two statements of
> the same fact; **a wrong fact stated consistently passes.**

---

## 3. Infrastructure — runs as a service, a CI step, or a hook

Not something you invoke while working.

| Entry | Role |
|-------|------|
| `vero_bridge/` | stdio-MCP transport between Code (server) and the Chat / Cowork tabs; carries the audit log, the repo-read sandbox, `lint_status`, and the dispatch queue |
| `loop/` | The PLAN-0010 scheduled-task autonomy loop — inbox poller, message schema, status digest |
| `notify/` | `notify/telegram.sh`, `notify/line.sh` — env-var-driven push, called by the notification hooks |
| `ci/boot_smoke.py` | Boots the app's **lifespan** in CI, not just its import (an image that could not import shipped for ten days while every test stayed green) |
| `ci/cache_bust_diff_check.py` | Fails CI when a changed static asset ships behind an unchanged `?v=` token |

---

## Type-checking this directory

`tools/` is a **PEP 420 namespace package** — no `__init__.py`, and neither have
`tools/handoffs/` nor `tools/ci/`. So the obvious command does not work:

```bash
mypy --strict tools/          # ✗ Source file found twice under different module names
```

With no package base to anchor to, mypy maps the same file to two module names and
refuses to check anything. Check `tools/` like this instead:

```bash
MYPYPATH=.:.claude/hooks mypy --strict --explicit-package-bases tools/
```

On a clean tracked tree that is `Success: no issues found in 47 source files`.

**`.claude/hooks` is on that path deliberately, not defensively.** `tools/goal_template.py`
imports the Stop gate's own schema (`_goal_state`) from there on purpose — so a rendered goal
is parsed by exactly the code that will read it — and bootstraps the directory onto
`sys.path` itself. Drop it from `MYPYPATH` and you get `Cannot find implementation or library
stub for module named "_goal_state"`: **a red on a tree that is clean.** Anything else under
`tools/` that reaches into `.claude/hooks/` will land in the same place.

⚠️ **CI type-checks neither `tools/` nor `tests/`.** A green gate says nothing about this
directory — run the command by hand, and quote the numbers.

⚠️ If you see an error in `tools/probes/`, check `git check-ignore` before fixing it —
`.gitignore` excludes that directory, so it appears only in checkouts where someone left a
copy lying around, and it is not part of the tracked tree.

### What actually triggers it

One rule, and it is neither "you named too many files" nor "some subpackage has an
`__init__.py`": **the same file enters one build under two different module names.** Two
ingredients have to meet.

1. For a file named on the command line, mypy derives a module name by walking **up** while
   `__init__.py` exists. `tools/handoffs/_schema.py` → `_schema` (its directory has none);
   `tools/vero_bridge/_handoff_validate.py` → `vero_bridge._handoff_validate` (its directory
   has one, `tools/` does not).
2. Any absolute `tools.…` import **anywhere in that build** pulls the same file in again
   under its `tools.`-rooted name.

Meet both and mypy refuses to pick. `__init__.py` only decides *which* root step 1 lands on;
the number of files you name is irrelevant. Measured on this tree:

| Invocation | rc | reported pair |
|---|---|---|
| `tools/handoffs/_schema.py` | 0 | — nothing imports it into this build |
| `tools/handoffs/validate_handoff.py tools/handoffs/handoff_status.py` | 0 | — neither is imported by the other |
| `tools/vero_bridge/_handoff_validate.py` **alone** | 2 | `"vero_bridge"` vs `"tools.vero_bridge"` |
| `tools/golden_trace/producer.py` **alone** | 2 | `"golden_trace.producer"` vs `"tools.golden_trace.producer"` |
| `tools/handoffs/validate_handoff.py tools/handoffs/_schema.py` | 2 | `"_schema"` vs `"tools.handoffs._schema"` |
| `tools/` | 2 | `"golden_trace.producer"` vs `"tools.golden_trace.producer"` |

Rows 3 and 4 are **single files named alone** — which is why "it takes two files" is wrong.

**Read the reported pair, not the exit code.** Three passes over this paragraph argued from
`rc` while the error text was printing the discriminating value the whole time — the pair is
what tells you *which* file is doubled, and it is frequently **the package's `__init__.py`,
not the file you named** (rows 3 and 6 report `vero_bridge` and `golden_trace.producer`, not
the module under test). §8's "a verification report prints the values it measured" applies to
reading someone else's report too.

### Which files can be spot-checked alone — run it, don't predict it

There is no cheap predicate, and the failed attempt to build one is worth keeping. Keying it on
the **package** — grep `tools/<pkg>/__init__.py` for absolute self-imports, `0` means safe — is
false, and false in the dangerous direction: it answers *safe* for files that collide. One
package contains both kinds:

| named alone | `tools.loop` imports in **that file** | rc |
|---|---|---|
| `tools/loop/_schema.py` | 0 | 0 |
| `tools/loop/__init__.py` | 0 | 0 |
| `tools/loop/dispatcher.py` | 2 | **2** — `"loop"` / `"tools.loop"` |
| `tools/loop/_status_digest.py` | 1 | **2** — `"loop"` / `"tools.loop"` |

`loop/__init__.py` has zero absolute self-imports — the exact input the predicate keyed on — and
`dispatcher.py` under it still collides, because it reaches `tools.loop` through **its own**
import graph. Spot-checkability is a property of the named file's transitive imports, not of the
package it sits in; evaluating that cheaply is most of what mypy already does. So run the
directory command and read its answer rather than predicting one.

The general rule above is unchanged and still holds — the same file under two names. What broke
was narrowing *"any absolute `tools.…` import **anywhere in that build**"* to *"an import in the
package's `__init__.py`"*, because that was greppable. Four shortcuts have now been tried on this
paragraph — "it takes two files", "it's the `__init__.py` subpackages", "it needs another named
file's import", and "grep the package's `__init__.py`". Every one was cheaper than the general
rule, and every one was wrong.

Importing **into** a package is harmless — `tools/check_battery_definitions.py` alone is
**rc=0** despite importing `tools.probe_battery._lint`, because the subpackage enters under one
name only. The hazard is being named **from inside** a package, not importing one.

⚠️ **So an explicit-file run is not a gate, in both directions.** It can be green while
checking one file out of a tree that cannot be checked whole (rows 1–2), and it can be red
for a reason that has nothing to do with the code you are working on (rows 3–4). Only the
`--explicit-package-bases` directory form above answers a question about `tools/`.

Row 5 is worth knowing because **this PR created it**: now that `validate_handoff.py` imports
`tools.handoffs._schema`, naming both files together collides where before it exited 0 —
measured against the pre-fix tree. Nothing regressed (the gate is the directory form, and it
is green), but if you spot-check those two files together, that rc=2 is the import fix
working, not a fault.

### Import a sibling by its absolute package path, never by bare name

A module that does `sys.path.insert(0, <its own directory>)` and then `from _schema import
...` runs fine and is invisible to `ruff`, but is **unresolvable to mypy**: three
`_schema.py` files exist (`handoffs/`, `loop/`, `vero_bridge/`) and a top-level `_schema`
maps onto none of them.

The cost is larger than the one error it prints. An unresolved import makes the whole
module `Any`, so every value it returns raises a **second, misleading error at the call
site** — a `no-any-return` against a return type that was correct all along. Fixing the
import cleared both; loosening the return type would have buried the real cause (§8:
suspect the instrument, and repair by *deriving* the right expectation).

Use the bootstrap idiom from `absent.py` / `tally.py` / `handoffs/validate_handoff.py`:

```python
if __package__ in (None, ""):   # path-script invocation, not `-m`
    sys.path.insert(0, str(Path(__file__).resolve().parents[N]))   # N = depth to repo root

from tools.<pkg>.<mod> import ...
```

Do **not** add `# noqa: E402` to the import below the guard **in this shape**. `ruff` does
not raise E402 when every `sys.path` mutation sits *inside* the `if`, so `RUF100` flags the
suppression as unused and the noqa costs a lint cycle while buying nothing.

**The shape is what decides, so check yours rather than copying either answer.** Add one
*unconditional* top-level statement before the imports and E402 does fire, and then the noqa
is required — `tools/goal_template.py` is exactly that case: its guard is followed by a bare
`sys.path.insert(...)` at module level, it carries `# noqa: E402` on both imports, and
removing them reddens lines 87 and 98. Two files in this directory, opposite answers, same
linter.

The `__package__` guard is what keeps **both** invocation forms working — and both are
load-bearing: `python tools/handoffs/validate_handoff.py` is the form the
`handoff-frontmatter` pre-commit hook uses, while `python -m tools.handoffs.validate_handoff`
is the form a test or another tool uses. A fix that only serves one of them breaks the other
silently.

## Adding a tool

Ship the pointer with the capability, or you have shipped neither. A new entry belongs
in this file **and**, if a session must reach for it deliberately (§1), as one terse row
in `CLAUDE.md` §10 — the only surface that is read every session.
