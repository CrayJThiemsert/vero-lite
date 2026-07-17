---
last_updated: 2026-07-17T23:30:00+07:00
session: 146
current_batch: "s146 — PLAN-0080 shipped end to end: #794 feat(ui) deterministic trace-kind attribution + 23-kind registry + AST tripwire; #795 docs(conventions) canonical ui.md. Colour=mechanism, glyph=actor."
current_actor: code
blocked_on: "Nothing blocking. main=8737b0a; 0 open PRs. PLAN-0080 COMPLETE. Loop-dispatcher DISABLED; MS-S1 idle/COLD (zero calls); dev Postgres UP."
next_action: "plan-drafter authors PLAN-0081 — building_materials governed-credit HERO, Cray COMMISSIONED s146 (SD-1=N=3 + ADR-0025 D7 re-eval in-PLAN; SD-2=ride measured_value). G2-gated; PLAN-0079 stays armed."
head_commit: 8737b0a
recent_commits: [8737b0a, 6a2a42d, 6249f52, cdc238d, ce0f0a1, 61d072f, f00e4c7, d43f4a8, d63d1b7, bb369ed]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 146, 2026-07-17 (head_commit `6249f52` → `8737b0a`) — PLAN-0080
> shipped end to end in two PRs: trace-attribution legibility + the canonical
> `docs/conventions/ui.md`.** The reasoning-trace badge had stopped telling the
> truth: a substring sniff (`kind.includes('rule')`) left **14 of 16
> procedure-engine kinds** on an unattributed neutral badge, and
> `scored_rule_selected` / `rule_gate_evaluated` matched `'rule'` and borrowed
> the recommender's `rule_check` colour. **(1) #794 (`6a2a42d`, `feat(ui)`) —
> deterministic attribution + an anti-rot tripwire.** ONE shared
> kind→{label,cls,actor} registry (`services/api/static/assets/trace-kinds.js`,
> `window.OCT_TRACE_KINDS`, **23 kinds**) is read by BOTH the browser and a CI
> tripwire. L-4 (Cray-ratified) split the signal onto **two axes, two channels**:
> colour = mechanism (existing `theme.css` semantics — the demo look is
> UNCHANGED), a small glyph = actor (`{human,llm,engine}` via `data-actor`).
> Unmapped kinds degrade VISIBLY — raw token, dashed `.badge.unmapped`, NO
> glyph, `data-actor="unknown"`. The AST tripwire
> (`tests/api/test_trace_kind_labels.py`) scans `services/engine` + `verticals`
> and asserts SET-EQUALITY, proven non-vacuous by 3 RED mutations. SD-1(c) (keep
> `ReasoningStep.kind: str`) + SD-2(iii) (0013 prompt annotated, not rewritten)
> Cray-ratified. **(2) #795 (`8737b0a`, `docs(conventions)`) — the canonical UI
> convention.** New `docs/conventions/ui.md` (11 items per AC-6, each with a live
> `file:line` anchor: tokens, the `window.OCT` contract, the trace-kind channel,
> the `html:`-only security rule, no-build-step + `?v=` cache-bust,
> ontology-driven principle, control-tower tone, provenance classes, the 0013
> relation, a `Step.kind`-vs-trace-`kind` glossary). AC-7: the 0013 design prompt
> got a one-line header annotation (body untouched); `code-style.md` gained a
> "UI work → ui.md" pointer. Canonical, not derived (ADR-0017 D5) + outside
> G1/G2 gate scope → Code authored it directly. **The reusable lesson (F-4):** a
> live preview probe against a REAL completed governed run REFUTED the PLAN's
> offline-draft claim "the engine is the only emitter" — `verticals/` seed
> executors emit `query`, unmapped, on the governed spine in 9/9 runs → added as
> kind #23, the tripwire's scan root widened to `verticals/`, the leaking
> definition-side `StepKind` token labelled (NOT fixed). Two more offline-draft
> errors caught by the same grounding: AC-3's regex would have absorbed non-trace
> `kind=` kwargs (`ControlRef`, `EconomicImpact`) → became an AST scan; AC-5's
> grep read was impossible as written (view-story has 5 `kind` vocabularies) →
> scoped to the TRACE block. Full offline suite **2860 passed / 7 skipped** re-run
> on BOTH merge commits. Post-merge: main=`8737b0a`; 0 open PRs; loop-dispatcher
> DISABLED; MS-S1 idle/COLD — zero calls this session. Commits: `6a2a42d` (#794,
> Subject A) → `8737b0a` (HEAD, #795 merge, Subject B).

> **Sessions 144 + 145, 2026-07-17 (head_commit `d8db032` → `ce0f0a1`) — the
> R4 arc: a ratified rule that had NO MECHANISM, closed end to end in one
> session (#789 → #791 → #792), plus two PRs from a CONCURRENT session (#788,
> #790).** R4 (`docs/runbooks/memory-architecture.md` §"R4 — Archive, don't
> drop") sets two numbers — archives stay under a **256 KB cap**; over **~192
> KB** start a continuation — and **nothing enforced either**: R4's own
> responsibility-matrix guard column read `—` where R1 and R7 both read `fail`.
> It had rotted to a **3x breach**. **(1) #789 (`f444cd1` → merge `b369fa6`) —
> the guard.** `tools/check_archive_size.py`: warns over the 192 KB trigger,
> **fails over the 256 KB cap**; a `files:`-scoped pre-commit hook (deliberately
> NOT `always_run` — a byte cap can only be breached by writing the file it
> caps); 8 contract tests; the R4 matrix row `—` → `fail >256 KB`. Landed GREEN
> **by design**: the hook does not fire on a commit touching no archive, and CI
> does not run pre-commit at all. **(2) #791 (`96ef1c4` + `d43f4a8` → merge
> `f00e4c7`) — the split the guard FORCED.** `2026-h1-status.md` was **592,577 B
> = 3.01x the trigger, 2.26x the cap**, growing ~7.5 KB per reconcile → split
> into the **c/d/e/f chain** per Cray's ratified naming rule (**letters ascend
> with time; the base holds the RECENT window; older spills into the next
> letter**) — `-b` is NOT the spill target (it holds OLDER content, so spilling
> newer sections in would break the chronology the letters encode). **Five
> files, not four:** a 4-way split forces one file to ~97% of the trigger, and
> the excuse "it's frozen so tight is fine" was **falsified BY THIS SESSION**
> (the s144 reconcile appended an archivist's note to a supposedly frozen row).
> Also lands **`test_live_archives_are_within_cap`** — the BINDING half; it
> could NOT land in #789 (RED at 2.26x), and **that ordering was the point**: a
> guard whose live assertion is RED cannot merge into a protected main. **(3)
> #792 (`61d072f` → merge `ce0f0a1`) — the current-focus split + THE RULE
> RECORDED AS CANON.** `2026-h1-current-focus.md` was 258,346 B (1.31x trigger,
> ~3,798 B under the cap) and **still receiving appends** (last s132) → split to
> `b`/`c` + base. **The more important half: Cray's naming rule was living only
> in commit messages and file headers — canonically invisible, which is EXACTLY
> how R4 got a guard column of `—` in the first place.** Now in the runbook,
> with the corollary and the hard-won warning: **which file holds a block is not
> stable information — grep the directory, never cite a continuation by name
> from outside the archive** (this session broke three of its own pointers that
> way). **Result: every archive is now under the ~192 KB TRIGGER (not merely the
> cap) and the guard is SILENT for the first time.** Rotation archive:
> `h1b`/`c`/`d`/`e`/`f` (94K–162K) → `2026-h1-status.md` base **22,185 B**;
> current-focus: `h1b-cf` 164,875 / `h1c-cf` 81,045 → base **18,161 B**. Both
> bases carry ~174 KB of headroom ≈ 23 reconciles. **Proofs, stated honestly:**
> #791 proved **exact list equality** of 27 sections; #792 proved **multiset
> equality** of 30 blockquote blocks (blocks deliberately reordered ACROSS
> files; order WITHIN each file untouched) — **different proofs, and the PR says
> so**. Both re-run against HEAD **AFTER pre-commit**, which CHANGED the answer:
> the end-of-file-fixer stripped one trailing newline per continuation, so the
> honest claim is *"equal except N trailing newlines, all stripped-equal"*,
> **NOT byte-identical**. **Two structural facts found by grounding, RECORDED
> rather than quietly fixed:** (i) `current-focus` has **zero `## ` sections**
> (it is blockquote blocks) — reusing the sibling's parser would have found 0
> sections and "split" nothing **while reporting success**; (ii) its header
> claimed "Session 46 and earlier" but later deep-rotates had appended sessions
> 116–128 to its bottom — **one file carrying two orderings**. Also: the
> `session 25` block is **162,822 B, atomic** — `h1b-cf` is large **by
> necessity, not by packing choice**. **Concurrent-session PRs — NOT session
> 144's work:** **#788 (`694e8d7`) — PLAN-0080 filed by session 145**, `Status:
> **Draft** (pending Cray ratification)`: **SD-1 and SD-2 are UNRATIFIED —
> merging the document did NOT ratify its decisions, and it must NOT be
> executed**; ⚠ **`docs/conventions/ui.md` does NOT exist** — the PR title names
> it because the PLAN *proposes* it, not because it shipped. **#790 (`ba12e1b` →
> merge `bb369ed`) — session 145's STATUS frontmatter-only bump**, merged by
> session 144 **on Cray's explicit instruction** to clear the STATUS lane; it
> existed *because of* #789 — its own title says "full reconcile blocked by the
> R4 guard", the forcing function biting a sibling session within hours, which
> is what turned the split from hygiene into **unblocking work**. Suite **2855
> passed / 7 skipped** — re-run BY CODE on the merge commit `ce0f0a1` itself,
> since CI is PR-only and never tests the merge commit. Post-merge:
> main=`ce0f0a1`; 0 open PRs; loop-dispatcher DISABLED; MS-S1 idle/COLD (zero
> calls); dev Postgres UP. Commits: `694e8d7` (#788, session 145) → `f444cd1` →
> `b369fa6` (#789) → `ba12e1b` → `bb369ed` (#790) → `96ef1c4` + `d43f4a8` →
> `f00e4c7` (#791) → `61d072f` → `ce0f0a1` (HEAD, #792 merge).

> **Session 144, 2026-07-17 (head_commit `6ee2aa8` → `d8db032`) — PLAN-0078
> Step 7 CLOSEOUT (#786, docs-only): the transform seed-migration arc CLOSED at
> **12/12 ACs** and ARCHIVED → `docs/plans/done/0078-transform-seed-migration.md`.**
> **The headline is that the closeout was FAR smaller than the s143 handoff
> predicted — and why.** **(1) Four of the six open ACs were ALREADY SATISFIED
> on disk** (AC-7/AC-8/AC-9/AC-12) — unticked BOOKKEEPING, not open work. The
> s143 handoff warned "do NOT tick them from the PR-3/PR-4 landed claim —
> verify against code"; that warning was right to DEMAND the verification, and
> the verification came back GREEN. Each tick now cites its satisfying test by
> file:line, every anchor resolved on a fresh read. **AC-9 was re-verified
> INDEPENDENTLY** rather than inherited from PR-4's R2 claim: `_spend` /
> `_severity` hash identically at `173d869^` and HEAD. **(2) AC-6 was the ONE
> genuine hole — and NOT the hole the PLAN described.** The PLAN predicted
> "Phase 2 adds transforms, so the non-participant set shrinks and must be
> re-swept". **FALSE on disk:** PR-3/PR-4 added transforms only to procedures
> that ALREADY carried a Phase-1 `enrich`, so the set never moved. Classified
> **`superseded by new info`, NOT `was an error`** (CLAUDE.md §6) — the
> prediction was reasonable and may yet come true, so it is now pinned as
> **DATA** (`test_derivation_pin.py:326`) rather than re-argued in prose. **The
> REAL hole:** energy + aquaculture — the two verticals AC-6 names FIRST — had
> **no step-level `transform`-absence assertion anywhere**;
> `test_transform_grammar.py:308` proved it only on a SYNTHETIC procedure, the
> two parity sweeps covered only non-participant procedures INSIDE the migrated
> verticals, and `test_derivation_pin.py:263` asserts the TOP-LEVEL key set
> only. **(3) Both new tests proven non-vacuous EMPIRICALLY, not by
> inspection:** temporarily declaring a transform in energy's yaml turned the
> census RED; temporarily deleting the only-when-supplied branch from
> `governance_pin.py` turned the sweep RED for supply_chain + procurement. Both
> probes REVERTED. The second probe is exactly **why the census must exist
> ALONGSIDE the sweep**: with the projection broken, energy/aquaculture still
> PASSED — a vertical with no transforms satisfies the IFF's negative arm
> regardless. **(4) Stale citations refreshed** against `governance_pin.py`
> post-PR-5 (137 lines): AC-5's `:96-98`→`:98-99`; AC-6's `:59-63`→`:58-68`,
> and `:122-125` **DROPPED** (the `derivation_hash` fold-in PR-5 retired; `:121`
> is now the `steps` list). **(5) Deliberately NOT closed:** **OQ-3 stays open**
> (the ADR-0031 D4.4 row annotation = a drafter-authored G1 Accepted-body edit;
> its own text says non-blocking) · **PLAN-0076 does NOT archive** — T1 /
> F-FACTORY stays open, its AC-6 guard stays ARMED · **no artifact records F-PIN
> closed** (L-4). **Order honored:** `Status:` flipped Proposed→COMPLETE in the
> SAME pass as the body edits (never flip-then-edit — the G1 lift is per-diff);
> the `git mv` to `done/` landed AFTER the sweep + ticks, per Step 7's own order
> and the s143 refusal precedent. Suite **2845 passed / 7 skipped** (was 2840/7
> at `6ee2aa8`) — re-run BY CODE on the merge commit `d8db032` itself, since CI
> is PR-only and never tests the merge commit. Post-merge: main=`d8db032`; 0
> open PRs; loop-dispatcher DISABLED; MS-S1 idle/COLD (zero calls this session);
> dev Postgres UP. Commits: `49ff275` (the sweep + ticks + `git mv`) → `2340de3`
> → `d8db032` (HEAD, #786 merge).

> **Session 143, 2026-07-17 (head_commit `303fd48` → `6eea264`) — PLAN-0078
> PR-5 SHIPPED (#784, `refactor`), the FINAL PR of the transform
> seed-migration: the PLAN-0075 AC-13 `derivation_hash` RETIRED end-to-end,
> the F-PIN marker rewritten, PLAN-0076 Step T2 CLOSED — plus two docs-only
> siblings reconciled in the same pass (#783 the R7 citation guard; #782
> Lesson #0031, merged back in s142 but never reconciled).** **Why PR-5 was a
> DELETION PR — that IS the point:** AC-13 hashed supply_chain's
> severity-ladder CONSTANTS into every run's governance snapshot via a
> per-vertical registry hook, for exactly ONE reason — the derivation lived in
> vertical CODE, where a snapshot of the DECLARATION could not reach it. PR-3
> declared the ladder; PR-4 declared the ฿ spend; **the reason vanished, so
> the workaround went.** The per-step `transform` key now pins the governing
> datum directly. Retired across 8 files: the provider, its registration, the
> registry seam (type + `_VerticalEntry` field + register/pull), the
> `governance_pin` parameter on both entry points, and the pass-through kwarg
> — **AC-10 grep-clean, 0 hits outside `docs/`**. **Both guarantees the
> retired suite bought are re-homed at FULL strength:** the replacements drive
> `assert_governance_pin` to an ACTUAL raise (not an `h1 != h2` hash compare),
> including the unbounded top band (the AC-13 drafter finding, preserved in
> declared form). **Two Cray s143 ratifications, both OVERRIDING a drafter
> recommendation:** (1) AC-11's "assert `derivation_hash` is None" is
> UNRENDERABLE alongside AC-10's grep-clean — asserting a hook returns None
> requires the hook to EXIST; Cray ruled: rewrite the marker with NO reference
> to the retired name. (2) `_DOSE_LADDER` / `_TOP_SEVERITY` /
> `SeverityDerivation` / `derive_excursion_severity` are KEPT as a test-only
> reference (the PLAN contemplated retiring them) — their docstrings now say
> so plainly, and the yaml bands are asserted independently + hand-written, so
> the two copies cannot drift together. **The session's reusable finding — the
> `goal-evaluator` subagent caught TWO real defects the author missed:** (i)
> the first draft deleted the "key is present" assertion WITHOUT adding its
> inverse, leaving supply_chain's config-hash change SILENTLY ABSORBED —
> exactly what AC-5/AC-10 forbid; fixed by an exact-snapshot-key-set
> assertion, strictly STRONGER than absence-of-one-name. (ii) a PR-3 forward
> reference ("PR-5 reshapes this module to retire the constants") that PR-5
> itself FALSIFIED via Cray's keep ruling (`70d25a5`). **Honest residual:
> F-PIN is NOT closed** (PLAN-0078 L-4) — only T2's remainder fold-in closed;
> **PLAN-0076 does NOT archive** — T1 (F-FACTORY) stays open, its AC-6
> guard-test stays ARMED. **The two siblings:** **#783** (`3bf99bc`) —
> rotation policy **R7** is now BINDING
> ([`memory-architecture.md`](runbooks/memory-architecture.md)): **never cite
> `docs/STATUS.md` by line number** — cite the tracked artifact, or STATUS by
> SECTION NAME. Rule → tripwire → cleanup, IN THAT ORDER: an `always_run`
> `status-citation-guard` hook (17 tests) + the 10 rotted sites cleaned;
> RED→GREEN proven on the real repo (10 → 0). **#782** (`bc42136`, merged
> s142, reconciled HERE) — Lesson #0031 + the `fan-out-dispatch` skill:
> **split parallel work on the WRITE-SET, not the idea** — the post-mortem of
> three s142 chip sessions whose write-sets collided, costing 3 hand-resolved
> merge commits. **Verification:** full
> offline suite **2840 passed / 7 skipped**, re-run by Code on the merge
> commit `6eea264` ITSELF (CI is PR-only — the merge commit is never
> CI-tested); delta accounted exactly: 2823 (PR-5 branch) + 17 (#783's new
> module); ruff + `ruff format` + mypy clean; R7 guard green;
> deterministic-offline throughout — zero MS-S1 calls, no host-state action.
> Commits: `9cd64d5` → `84f261f` → `bc42136`
> (#782 merge) → `abd41d4` → `3bf99bc` (#783 merge) → `732fc0a` (PR-5 retire)
> → `6e6ec7a` (PLAN-0076 T2) → `70d25a5` (PR-3 forward-ref fix) → `6eea264`
> (HEAD, #784 merge).

> _Rotation note (session-146 reconcile, 2026-07-17, `docs(status):`):
> frontmatter → `head_commit 8737b0a` (the #795 merge, the SHA this reconcile
> makes current). A new **session-146** block was PREPENDED for PLAN-0080
> (#794 deterministic trace-kind attribution + AST tripwire; #795 canonical
> `docs/conventions/ui.md`), so the OLDEST — the **session-142** block (the
> three R2 carve-out TODOs discharged, #780/#778/#779) — rotated OUT (4-session
> window, now s146 + s145/144 + s144 + s143) to the rotation-archive BASE
> `docs/status-archive/2026-h1-status.md`. Recent Decisions gained ONE row
> (PLAN-0080) and so rotated its OLDEST — the **s138** `#767` row (2026-07-16,
> the AT-2 `N=1` misinformation-KILL) — to the same base (10-row window). The
> **s142 RD row's `Full narrative:` pointer was re-pointed** from "the
> Session-142 CF block above" to the archive directory (the block it names is no
> longer in-file — a rotation rots that pointer exactly like a split does, s144
> §3). Prior rotation notes (through the session-145 reconcile) are consolidated
> here (R4). Per the STATUS.md Rotation Policy (R1/R2/R4)._

> _Older content rotates out of this file per the **STATUS.md Rotation Policy (R1-R7)** in [`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md) (Lesson #23): Current Focus keeps the 4 newest sessions (<=8 blocks); Recent Decisions keeps the last 10 rows. Rotated blocks/rows live in [`docs/status-archive/`](status-archive/) and git history (Tier 3). Layout — **two separate chains, both with letters ascending with time and the base holding the recent window**: the rotation archive `2026-h1b` → `c` → `d` → `e` → `f` → `2026-h1-status.md`, and the Current-Focus-only `2026-h1b` → `c` → `2026-h1-current-focus.md`. Rotations append to the two bases. **Grep the directory, not a filename** — the chain is one corpus and which file holds a given block is an artifact of where the ~192 KB R4 bar happened to fall. _[Chain created 2026-07-17 (s144): the single `2026-h1-status.md` had reached 592,577 B, 2.3x R4's cap, and the new guard (#789) forced the split.]_

## Prior focus (archived)

PLAN-003 Phase 1 (ontology engine + 5 emitters), PLAN-0005 Phase 2
(OCT engine runtime layer), PLAN-0006 (LLM reasoning hook),
PLAN-0007 Phase 1 (harness autonomy layer — deterministic floor),
and **PLAN-0008 Phase 2 (harness autonomy layer — probabilistic /
classifier-mediated engine on top of Phase 1)** are all **merged and
moved to `docs/plans/done/`**. The Cowork-as-Tier-1 trial that ran as
the test-bed across the earlier batches **concluded** — ratified
permanently by **ADR-009** (Cowork = merged Tier 0 + Tier 1 workspace;
commits stay Code-exclusive). PLAN-004 Phase A (handoff frontmatter
schema + tooling) also landed; Phase B/C remain deferred (backlog).
Full detail lives in `docs/plans/done/`, the Recent Decisions table
below, and git history.

## Recent Decisions (last 10)

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-17 | **s146 — PLAN-0080 shipped end to end (#794 `feat(ui)` + #795 `docs(conventions)`): the reasoning-trace badge's substring sniff (`kind.includes('rule')`, mis-attributing 14/16 engine kinds) → ONE shared kind→{label,cls,actor} registry (`trace-kinds.js`, 23 kinds) read by BOTH the browser and an AST set-equality tripwire; colour=mechanism (theme.css UNCHANGED) + glyph=actor, unmapped kinds degrade visibly. + canonical `docs/conventions/ui.md` (11 anchored items).** **F-4:** a live probe refuted the offline "engine-only emitter" claim — `verticals/` seed executors emit `query` unmapped 9/9 → kind #23, scan root widened. Suite **2860/7** on BOTH merge commits. Full narrative: the Session-146 CF block above | `8737b0a` (#795 merge) / `6a2a42d` (#794) / `services/api/static/assets/trace-kinds.js` + `tests/api/test_trace_kind_labels.py` + `docs/conventions/ui.md` |
| 2026-07-17 | **s144 — the R4 arc CLOSED end to end (#789 guard → #791 + #792 splits): a ratified rule that had NO mechanism now has one, and every archive sits under the ~192 KB TRIGGER — not merely the cap — for the first time.** R4's own responsibility-matrix guard column read `—` where R1/R7 read `fail`; the rotation archive had rotted to **592,577 B = 2.26x the cap**. #789 shipped `tools/check_archive_size.py` (warn >192 KB, **fail >256 KB**, `files:`-scoped hook) GREEN **by design**; the BINDING live assertion (`test_live_archives_are_within_cap`) could only land in #791 **after** the split — a guard whose live assertion is RED cannot merge into a protected main. **Five-file c/d/e/f chain, not four** (a 4-way split lands one file at ~97% of the trigger). #792 split current-focus AND **recorded Cray's naming rule as CANON** — letters ascend with time, the base holds the recent window; **grep the archive dir, never cite a continuation by name**. Proofs DIFFER and say so: #791 = exact list equality (27 sections), #792 = multiset equality (30 blocks, deliberately reordered across files); both re-run AFTER pre-commit → *"equal except N trailing newlines, all stripped-equal"*, **NOT byte-identical**. Suite **2855/7** re-run on the merge commit itself. _[Concurrent session 145: #788 PLAN-0080 `Status: Draft` — SD-1/SD-2 UNRATIFIED, must NOT be executed, and `docs/conventions/ui.md` does NOT exist · #790 frontmatter-only bump, merged on Cray's instruction.]_ Full narrative: the Sessions-144+145 CF block above | `ce0f0a1` (HEAD, #792 merge) / `f00e4c7` (#791) / `b369fa6` (#789) / `694e8d7` (#788) / `tools/check_archive_size.py` + `.pre-commit-config.yaml` + `docs/runbooks/memory-architecture.md` (R4 matrix row `—` → `fail >256 KB` + the naming rule) + `docs/status-archive/**` (the c/d/e/f + b/c-cf chains) |
| 2026-07-17 | **s144 — PLAN-0078 COMPLETE at 12/12 ACs → `docs/plans/done/0078-transform-seed-migration.md` (#786, docs-only): a FAR smaller closeout than the s143 handoff predicted — 4 of the 6 open ACs (AC-7/8/9/12) were ALREADY SATISFIED on disk (unticked bookkeeping; each tick now cites its test by file:line, and AC-9 was re-verified INDEPENDENTLY rather than inherited from PR-4's R2 claim).** **AC-6 was the ONE genuine hole — and NOT the hole the PLAN described:** the predicted "Phase 2 shrinks the non-participant set" was FALSE on disk (PR-3/PR-4 only touched procedures already carrying a Phase-1 `enrich`) → classified **`superseded by new info`, NOT `was an error`** (CLAUDE.md §6) and pinned as DATA; the REAL hole was energy + aquaculture carrying no step-level `transform`-absence assertion anywhere. Both new tests proven non-vacuous **EMPIRICALLY** (probes reverted). **OQ-3 stays open; PLAN-0076 does NOT archive; F-PIN NOT closed** (L-4). Suite **2845/7** re-run on the merge commit itself. Full narrative: the Session-144 CF block above | `d8db032` (HEAD, #786 merge) / `49ff275` (sweep + ticks + `git mv`) / `docs/plans/done/0078-transform-seed-migration.md` (COMPLETE, archived) + `tests/**` (`test_derivation_pin.py:326` prediction pin + the energy/aquaculture transform census) |
| 2026-07-17 | **s143 — PLAN-0078 Phase 2 PR-5 COMPLETE (#784, `refactor`), the FINAL PR of the transform seed-migration: the PLAN-0075 AC-13 `derivation_hash` RETIRED end-to-end (AC-10 grep-clean, 0 hits outside `docs/`), the F-PIN marker rewritten (AC-11), PLAN-0076 Step T2 CLOSED.** A DELETION PR by design: AC-13 hashed supply_chain's ladder CONSTANTS into the pin only because the derivation lived in vertical CODE — PR-3/PR-4 declared it, so the reason vanished and the workaround went. Both retired guarantees re-homed at FULL strength (an ACTUAL `assert_governance_pin` raise, not an `h1 != h2` compare). 2 Cray ratifications OVERRODE the drafter (unrenderable AC-11 assert; KEEP the constants test-only). **F-PIN NOT closed; PLAN-0076 does NOT archive** (T1 open, AC-6 armed). Suite **2840/7** re-run on the merge commit itself. _[Siblings reconciled same pass: #783 R7 citation guard · #782 Lesson #0031.]_ Full narrative: the Session-143 CF block above | `6eea264` (HEAD, #784 merge) / `70d25a5` (PR-3 forward-ref fix) / `6e6ec7a` (PLAN-0076 T2) / `732fc0a` (the retirement) / `verticals/supply_chain/**` + `services/engine/procedures/**` (registry seam + `governance_pin` param retired across 8 files) + `tests/**` (exact-snapshot-key-set assertion) + `docs/plans/0078-*.md` (PR-5 COMPLETE) + `docs/plans/0076-*.md` (T2 CLOSED) |
| 2026-07-17 | **s143 — rotation policy **R7** is BINDING (#783, `chore`): never cite `docs/STATUS.md` by LINE NUMBER — cite the tracked artifact, or STATUS by SECTION NAME; a tripwire + an `always_run` pre-commit hook enforce it repo-wide (10 rotted sites cleaned, RED→GREEN 10 → 0).** _[Sibling #782 (`bc42136`, s142, reconciled s143): Lesson #0031 + the `fan-out-dispatch` skill — split parallel work on the WRITE-SET, not the idea.]_ Full narrative: the Session-143 CF block above | `3bf99bc` (#783 merge) / `abd41d4` (R7 + guard + cleanup) / `bc42136` (#782 merge) / `docs/runbooks/memory-architecture.md` (R7) + `tools/check_status_citations.py` + `docs/lessons/0031-*.md` + `.claude/skills/fan-out-dispatch/` |
| 2026-07-17 | **s142 — the THREE R2 carve-out TODOs DISCHARGED (#780/#778/#779, docs-only): each fact REHOMED into a tracked home FIRST, THEN trimmed** — Rock 4's evidence-asymmetry finding → ADR-0025 · the `sequence`-column deferral → the ordering-guard docstring (deferral STANDS) · the s74 demo-card SD-3 → the PLAN-0035 `done/` post-archival amendment (+ ADR-0030's `STATUS.md:<line>` citations re-pointed). Runbook R2 now records **"until it is rehomed" is a real exit**, and that an ADR citing `STATUS.md:<line>` is a **defect**. Suite **2822/7**. Full narrative: the Session-142 CF block (rotated to `docs/status-archive/` at the s146 reconcile — grep the archive dir, not one file) | `303fd48` (HEAD, #779) / `37ab124` (#778) / `12e69aa` (#780) / `docs/adr/0025-*.md:23-29` + `docs/plans/done/0035-*.md:576` + `tests/services/db/test_load_run_ordering_guard.py` + `docs/runbooks/memory-architecture.md` (R2) |
| 2026-07-17 | **s141 — PLAN-0078 Phase 2 PR-4 COMPLETE (#775, `feat`, oracle-first): the marquee ฿ spend re-sequenced off the `_scored_rule` stamp into a declared `derive_spend` transform, per the ratified SD-8=(a) ONE DERIVATION HOME.** Cray-ratified in-session refinement: stamp `selected_qty` (not `selected_unit_price` only) so `_quantity` stays the ONE resolution home. Suite **2822 passed / 7 skipped**; deterministic-offline. **PLAN-0078 stays `Status: Proposed`**; **PR-5 is NOT blocked by PR-4**. Full narrative: the Session-141 CF block (rotated to `docs/status-archive/` at the s145 reconcile — grep the archive dir, not one file) | `09714ea` (HEAD, #775 merge) / `88e6e11` (PR-4 flip) / `fc17d02` (PR-4 oracle) / `verticals/{procurement,supply_chain}/**` (declared `derive_spend` transform) + `services/engine/procedures/governance_step.py` (`_scored_rule` factor stamps) + `tests/**` (`test_amount_transform_parity.py`) + `docs/plans/0078-*.md` (Proposed; PR-4 COMPLETE) |
| 2026-07-16 | **s140 — artifact 3/4 (#773, docs-only): `CLAUDE.md` §2 retitled "Current Focus" → "Direction & Current Focus" + a two-pointer signpost — standing direction = ADR-0032, current state = STATUS, "state never overrides direction" (§1).** The strategic-continuity program is now **COMPLETE 4/4** (#770 ADR · #771 PLAN-0079 · #773 §2 · #772 STATUS pointer). Scope CUT at Cray's ratification: the planned sanitized strategy doc DROPPED (a no-precedence restatement of a canonical is itself a drift surface, §1 / ADR-0017 D6). Suite **2810 passed / 7 skipped**. Full narrative: the Session-140 CF block above | `0523d88` (HEAD, #773 merge) / `038efd0` (§2 pointer) / `CLAUDE.md` §2 + `docs/adr/0032-*.md` |
| 2026-07-16 | **s140 — the 4-artifact STRATEGIC-CONTINUITY program CLOSED (3 PRs; docs + one guard test, ZERO behaviour change): ADR-0032 Accepted (#770) — the demo→pilot wedge + 3-shape roadmap + a BINDING pilot gate + the PINNED AT-2 fact record (N=2, re-arms at N=3) · PLAN-0079 `Status: Tracking` (#771) — the governed-credit HERO homed with its honest cost, builds NOTHING · the s138 reconcile unblocked (#769) · this AC-4 pointer.** Cause: the s137 arc lived only in auto-memories + gitignored docs, so a parallel session planned BLIND. Suite **2809 passed / 7 skipped**. _[Artifact 3 landed as #773 — see the row above.]_ Full narrative: the Session-140 CF block above | `8ca772b` (HEAD, #769) / `754a894` (#771) / `ad40aef` (PLAN-0079) / `4a5cfb7` (#770) / `5b53bbe` (ADR-0032) / `docs/adr/0032-*.md` + `docs/plans/0079-*.md` + `tests/services/engine/procedures/test_governed_credit_hero_tracking_guard.py` |
| 2026-07-16 | **s138 — PLAN-0078 Phase 2 PR-3 COMPLETE (#768, `feat`, oracle-first): cold-chain excursion SEVERITY re-sequenced off the `ColdChainAssessExecutor` stamp into a declared `enrich` transform (ADR-0031 D3 row-1) — `_DOSE_LADDER` becomes a governed datum IN THE PIN, the move that makes retiring `derivation_hash` honest in PR-5.** Proved the ratified SD-6 two-tier bar; SD-7 slimmed the executor to its fail-closed guard; OQ-5 ratified (a) materialize. **Honest interim redundancy stays in code until PR-5 — F-PIN stays OPEN.** Suite **2808 passed / 7 skipped**. **PLAN-0078 stays `Status: Proposed`**. Full narrative: the Session-138 CF block (`docs/status-archive/2026-h1f-status.md` — moved there by the s144 R4 split; grep the archive dir, not one file) | `9a5eecf` (HEAD, #768 merge) / `e6fb07a` (PR-3 flip) / `8214a32` (PR-3 oracle) / `verticals/supply_chain/**` (declared `enrich` severity transform + slimmed `ColdChainAssessExecutor` guard) + `tests/**` (`test_severity_transform_parity.py` + 2 re-homed PLAN-0074/PR-2 tests) + `docs/plans/0078-*.md` (Proposed; PR-3 COMPLETE) |

## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13; guarded trial (parallel to ADR-012) — verdict **continue-with-adjustments**. Run 1 (energy, s93) + Run 2 (supply-chain, s94) both COMPLETE, S-checks all PASS against pre-committed oracles, no R-PS trigger fired; C-1..C-3 CONFIRMED → **no open partner-sim debt**. ADR-011 audit stays gated on a REAL partner conversation (R3: SYNTHETIC provenance INFORMS but never TRIGGERS it). Full record: `docs/adr/0020-*.md` + the gitignored run packages `docs/research/private/2026-07-02-partnersim-run{1,2}-*.md`. _(Full prior narrative — the ~8 schema-mismatch findings, both run details, cross-run synthesis — archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **Procurement vertical — GO + SHIPPED (PLAN-0036 Fastenal, Stage 1):** 4th vertical greenlit (s75); PLAN-0036 drafted + merged Draft (#412, `7a7c036`; SD-1…SD-5 confirm-all). Demo target = Fastenal Thailand (auto-parts / EEC); **hero** = asset-failure → governed emergency sourcing, **calm-path** = low-stock reorder. Stage 1 = a PLAN-only pure-config plugin on the ADR-016 engine (zero `services/` core edit; CQ-1 / ADR-0023). **Pitch** = asset-ontology-triggered governed sourcing (native ontology ADR-008 + engine ADR-016), NOT the commoditized "governed"/"cross-vertical" claims. Full record: `docs/plans/0036-*.md` + the s72 de-risk dossier `docs/research/private/2026-06-22-procurement-*.md` (5 files: spec-expressiveness, GTM, asset-aware incumbent scan, AI-sourcing teardown, platform-incumbent deepdive). _(Full prior narrative archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [ ] **PLAN-0079 (`Status: Tracking`, filed #771, s140) — the `building_materials` governed-credit HERO, homed WITH ITS HONEST COST; nothing is built, nothing is scheduled.** **The honest cost:** the hero is **AT-2 signature #3** → re-arms `test_at2_signature_retrigger.py` → **CI goes RED** → it **OBLIGATES the ADR-0025 D7 re-evaluation**; per **ADR-0032 D6 this is NEVER a "cheap follow-on"**. **Doing nothing is a real option** — the shipped Tier-1 Mirror is a supported, tested end-state and no test or commitment forces the hero; only **Cray commissioning it (Step T1)** promotes it. Full detail: `docs/plans/0079-building-materials-governed-credit-hero-tracking.md` — honest cost `:89-98`, the 3-part spine `:116-125`, the 3 open SDs `:246-260`. **Guard:** AC-2 presence guard-test `tests/services/engine/procedures/test_governed_credit_hero_tracking_guard.py` (CI RED on a premature archive-to-`done/` or a pruned STATUS pointer). *(#771; ADR-0032 = #770; the s137 mirror = #765.)*
- [ ] **PLAN-0075 follow-ons — homed by PLAN-0076 (`Status: Tracking`, filed #752, s133): T1, the ADR-0031 D3 gate-plugin seam (F-FACTORY), is now the ONLY open deferral — Step T2's F-PIN remainder CLOSED s143 (#784, PLAN-0078 PR-5).** _[T2 closed ≠ F-PIN closed: **F-PIN itself stays OPEN** (`docs/plans/done/0078-transform-seed-migration.md` L-4 — PLAN-0078 closed s144 COMPLETE at 12/12 and archived, but **no artifact records F-PIN closed**) — only T2's remainder fold-in closed, so **PLAN-0076 does NOT archive** and its guard stays ARMED.]_ A guardrail against the ADR-0031 OQ-4 deferral-rot precedent (s133 4-specialist panel); PLAN-0075 itself is **COMPLETE — all 13 ACs — and CLOSED → `docs/plans/done/0075-*.md`**. Full detail: `docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` — F-FACTORY `:61-127`. **Guard:** PLAN-0076's AC-6 presence guard-test (`tests/services/engine/procedures/test_at2_followon_tracking_guard.py`) turns the build RED on a premature archive-to-`done/` or a pruned STATUS pointer ("location≠tripwire; failing tests are the real anti-rot"). *(PLAN-0075 = #749/#751 → `done/`; PLAN-0076 = #752, `Status: Tracking`; T2 closed by #784.)*
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2) — open ONLY for the O-2 residue; every other leg is DONE + archived.** **Closed:** Q3 ontology data-binding (PLAN-0046) · the Q4 generic query executor (PLAN-0048) · the Q4 join/projection grammar (ADR-016 Q4 amendment #659 + PLAN-0061) · the per-vertical seed migration (PLAN-0062) · the per-entity `threshold_field` band arc (PLAN-0066/0067/0068/0070) · **Box-4 BUILT (PLAN-0071, AC-5 GREEN at N=4) + SURFACED IN THE HERO UI (PLAN-0073)** — all → `docs/plans/done/`. **The one OPEN residue:** procurement's `intake` is declared-expressible ✔ under shadow parity, but **production execution stays the co-existing `_SeedQuery` ✖ for derived fields** — `docs/plans/done/0062-per-vertical-seed-migration.md:348`, the SD-C co-exist decision `:54-60`, `:291-295`. **Now homed by the transform arc:** **PLAN-0077** (transform grammar, COMPLETE → `done/0077-*.md`) + **PLAN-0078** (**COMPLETE at 12/12 ACs, CLOSED s144 #786 → `done/0078-*.md`** — the Step-7 closeout swept AC-5/AC-6 and archived it; do NOT re-open) — the fold-in is named at `docs/plans/0076-*.md:170-174`, what stays seed-side at `docs/plans/done/0078-transform-seed-migration.md:150-155`. *(s84 strategy discussion; the Box-4 leg is DONE — the residue is the O-2 data-binding leg only.)*
- [ ] **Bounded/incremental chain verification (PLAN-0063 SD-4 follow-up, s118).** `GET /audit/verify` walks the WHOLE chain O(n) on demand — accepted at pilot scale, documented in the endpoint docstring (`services/api/routers/audit.py:13-16`). Future work = a checkpointed head / verify-since-anchor design; anchor storage ≈ external anchoring — **do not build without re-reading the tripwire: `docs/plans/done/0063-audit-chain-verification-surface.md:564` + `services/api/routers/audit.py:19`.** _[Corrected s141: this item used to say "ADR-011 tripwire territory" — **ADR-011 does not exist** (`docs/adr/` jumps 0010 → 0012; it is an earmark only); the tripwire text lives at the two anchors above.]_ *(s118; #688/#690)*
- [ ] **procurement ontology ↔ CSV column drift (PLAN-0062 close-out follow-up, s117).** The procurement ontology declares `PurchaseOrder.part_no` / `Quotation.price` / `OperationalEvent.equipment_id` while the real CSVs emit `part_id` / `price_thb` / `asset_id`; the load gate checks DECLARED properties while the executor merges RUNTIME keys. Data/ontology evolution — explicitly **out of PLAN-0062's scope**. Full detail: `docs/plans/done/0062-per-vertical-seed-migration.md:521-522` (near-verbatim) + `:540-541`. *(s117; PLAN-0062 PR4 #682)*
- [ ] **DEFERRED: a monotonic `sequence` column on `step_results` — the ROOT fix for `load_run`'s wall-clock ordering.** Needs a DB migration → its own PLAN (PLAN-0062-independent); none drafted. `ORDER BY created_at` is **unchanged by design**, so **the deferral STANDS**; both surviving orderings are **DISPLAY-ONLY**, so not urgent. Full detail — ROOT-vs-guard, why it is tolerable, the static AST guard holding the line: the module docstring of `tests/services/db/test_load_run_ordering_guard.py`, pointed to from both code sites. *(rehomed s142; s117; #678/#680/#684)*
- [ ] **Standard partner-intake form (template candidate — Cray observation, s93 partner-sim run-1).** Generalize the 6-ask structure into a stakeholder-facing standard intake form per vertical, so partners can prepare narrative context for vero-lite to generate workflow pipelines more accurately. **Looks DONE — Cray to confirm/close:** `docs/conventions/partner-intake-form.md` EXISTS and self-describes as "Canonical, tracked" (`:8`), carrying the per-vertical deferral at `:25-27`. *(s93; ADR-0020 run-1)*
- [ ] **Rock 4 — s84 deep research DELIVERED → O-sequence locked.** Cray locked **O-1 → O-3 → O-2 → O-4**. **O-1** (Box-4 ฿ pitch) **DONE** · **O-3 = ADR-0025 Accepted** · **O-4 = PARK** (agent-interop; `docs/adr/0032-*.md:169` D4 — option-only, un-park = a counterparty's *written* pull). **Remaining: O-2 only** (economic-impact facet + Q3 data-binding = Rock 3). Full detail: `docs/adr/0025-at2-managerial-layer.md:19` (O-sequence + Box-3 fit) + `:23-29` (the **evidence-asymmetry** finding — bullish ROI all vendor-authored, independent mostly skeptical — rehomed s142). *(s84 Cray ask)*
- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten. **Full table (all six rows + their triggers + where each lands): `docs/plans/done/0005-oct-engine-runtime-layer.md:390` §8.1** — which itself instructs this STATUS entry to be a pointer. *(per Cray note 2026-05-21)*
- [ ] **Demo card UX — "trust shape", NO operator confidence badge (s74 design, Cray-approved).** The operator card shows **what / grounded-why / approve gate** + a "show full reasoning trace" toggle; **no confidence badge** (`confidence_signal` is engine-internal QA, trace-only), and the **(B) first-class `verification` field is NOT needed** — SD-3 settles at (a). Full record + rationale + the reconsider-trigger: **`docs/plans/done/0035-governed-action-verify-reshape-build.md:576`** — the s142 post-archival amendment ANSWERING SD-3's Phase-2 question; `ADR-0030` cites it. *(Trigger: the next demo / UI round.)*
- [ ] **PLAN-004 Phase C — OPTIONAL POLISH (forward-declared; "may never land"):** HTML/markdown handoff dashboard under `docs/` + references-graph (mermaid dispatch chains) + `render_transcript.py` unified session export (PLAN-0004 §"Phase C"). *(Phase A + B both COMPLETE — session 35; the prior TODO's validator **warning-swallow bug was FIXED #312**, s58. Minor never-formally-scoped sub-ideas — README/`_rename-map` walk-exclusion, Cat G `references_*` autofix, OQ-2 effective-vs-authored `status:` dashboard flag — fold in only if Phase C lands. Reconciled 2026-06-16 s65 audit.)*
- [ ] **ORM-emitter per-vertical layout (B1-DP-1 follow-up; Cray-deferred s67).** When a **2nd vertical needs its own ORM** (the Rule-of-Three trigger), decide the per-vertical layout: extend `_ORM_COMMITTED_DEST` to per-vertical committed modules **vs** un-ignore a per-vertical `generated/orm.py` + re-export. Premature to design now (one ORM today — energy's, at the committed `services/db/models.py`). Full detail: **`services/engine/code_generator.py:738-742`** (the deferral comment) + **`docs/plans/done/0031-orm-emitter.md:219-222`**. *(Cray-deferred 2026-06-18)*
- [ ] **Custom Postgres image with extensions (pgvector / AGE / pg_trgm) — needs a fresh ADR number + a PLAN; neither drafted.** *[Corrected s141: **PLAN-002 does not exist** ("NOT yet drafted", `docs/plans/done/0005-oct-engine-runtime-layer.md:14`), and the old "≥ ADR-014" floor is **moot** — ADRs now run to 0032 and `0014-WITHDRAWN.md` exists.]* Context: **`docs/adr/0013-autonomy-axis-relocation.md:285-289`** (the floor-bump note) + **`docs/plans/done/0005-*.md:403`** (trigger: semantic + graph features).
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (low priority)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)

## Next Steps

1. **PLAN-0005 §8.1 revisit register** — remaining deferred-foundational simplifications at their batch boundaries (audit framework → ADR-011+, mapping layer, ORM emitter, base-Postgres → PLAN-002 (≥ADR-014), registry discovery).
2. **Partner-trial readiness gaps** — `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` awaits a dedicated Cray discussion.
3. **Deferred (backlog)** — PLAN-004 Phase C only (optional polish: handoff dashboard / references-graph / unified export — Phase B complete s35, warning-swallow fixed #312); PLAN-002 custom Postgres image (≥ADR-014).
4. **Ongoing** — Continue exercising the file-based handoff mechanism (Chat ↔ Code ↔ Cowork) across batches.

## Update Workflow

This file is updated when:
- A commit changes project state significantly
- A new ADR/PLAN is minted or completed
- Active priorities shift
- A batch closes (sync `last_updated` + `current_batch` + `head_commit` + `recent_commits` frontmatter)
- A session closes (sync all frontmatter fields; archive batch history if needed)

**Update mechanism (locked per STATUS staleness batch 2026-05-18, Hybrid A+B short-term, C long-term):**

- **Per closeout (Option A + Q1(b) discipline):** Closeout drafter includes the line "STATUS.md updated: yes / no / N/A" in their closeout. If `yes`, the closeout's commit batch should include a dedicated `docs(status): …` housekeeping commit (Q3(b/c) pattern) bumping at minimum the `last_updated` and `head_commit` frontmatter fields.
- **Per batch boundary (Option B full body):** Full body refresh (Current Focus + Recent Decisions + Active TODOs + Next Steps) at batch close, alongside the frontmatter bump.
- **Per session boundary:** Full body + frontmatter sync; consider archive of prior session's batch history.
- **Future (Option C, PLAN-004 Phase A):** Validator will flag stale STATUS.md by comparing **frontmatter `last_updated` field** against newest closeout's `created` timestamp (NOT file mtime — mtime is defeated by side-effect commits, e.g. `c85a595` 2026-05-16 normalization sweep that touched STATUS.md body without bumping `last_updated`).

**Q4 `head_commit` semantics (codified 2026-05-18, locked Cray ratification of midflight `2026-05-18-1049` §4 + closeout `2026-05-18-1202` §6.2):**

- `head_commit` = short SHA of the newest **substantive** commit on
  `origin/main` that STATUS.md content reflects.
- **Excluded from `head_commit`:** `docs(status): …` housekeeping
  commits. These commits encode no new repo state — they ARE the
  STATUS.md freshness marker. Including them in `head_commit` creates
  a self-defeat where every housekeeping commit makes STATUS.md appear
  "fresh" to Q4 detection regardless of substantive backlog.
- **Substantive (included in `head_commit`):** everything else —
  `docs(lessons):`, `docs(adr):`, `docs(runbook):`, `feat:`, `fix:`,
  `chore:` (when changing meaningful state), `refactor:`, `test:`, etc.
  Any commit type that changes durable repo content updates
  `head_commit` at the next STATUS.md edit.
- **Reader recipe (returning after a pause):**

  ```bash
  # Newest substantive commit on origin/main (the value head_commit should hold)
  git log -1 --format=%h --invert-grep --grep='^docs(status):' origin/main

  # Compare to STATUS.md head_commit field
  grep -E '^head_commit:' docs/STATUS.md
  ```

  If the two differ → STATUS.md content is stale relative to substantive
  repo state. If they match → STATUS.md is fresh.

- **Writer rule (at each STATUS.md update):** Set `head_commit` to the
  output of `git log -1 --format=%h --invert-grep --grep='^docs(status):' origin/main`
  *after* the substantive commits of the current batch land but *before*
  any `docs(status):` housekeeping commit (or, if the STATUS.md edit
  itself is in a substantive commit like `docs(lessons):`, set
  `head_commit` to that substantive commit's own SHA — which becomes
  knowable only post-commit, so the writer typically updates
  `head_commit` to the *most-recent prior substantive commit* and lets
  the next batch's first edit catch up).
- **Two failure modes this rule closes:**
  1. **mtime trap** (closeout `2026-05-18-1202` §2): side-effect commits
     that touch STATUS.md body without bumping `last_updated` (e.g.
     `c85a595` 2026-05-16 normalization sweep) leave the file mtime-fresh
     but semantically stale. A SHA in `head_commit` cannot drift this way.
  2. **Housekeeping self-defeat** (closeout `2026-05-18-1202` §6.2 +
     midflight `2026-05-18-1049` §4): if `head_commit` = own SHA, every
     `docs(status):` commit makes Q4 say "fresh" regardless of
     substantive backlog. Excluding `^docs(status):` from the comparison
     baseline closes this loophole.

Manually edited until Option C lands.
