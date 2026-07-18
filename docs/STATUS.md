---
last_updated: 2026-07-19T02:50:45+07:00
session: 150
current_batch: "s149 — PLAN-0082 shared-ontology mechanism BUILT (ADR-0033 Accepted #803; Steps 2-4 #804-808). s150 — PLAN-0082 COMPLETE + archived (Steps 5-7 #809-811) + PLAN-0081 fold #812."
current_actor: code
blocked_on: "Nothing blocking. main=043da3c; 0 open PRs. PLAN-0082 COMPLETE + archived; PLAN-0081 UNBLOCKED (Step 9 = building_materials on shared Person). Loop-dispatcher DISABLED; MS-S1 idle/COLD."
next_action: "PLAN-0081 UNBLOCKED: Step 9 = land building_materials on the shared core.Person, then the governed-credit HERO build. OQ-2 (person-table population) deferred. Detail: the Sessions 149+150 CF block."
head_commit: 043da3c
recent_commits: [043da3c, 5eb6998, e059303, 58f661b, c94d089, 5a8af05, 92f0019, 11303c6, a5ec99b, 5e45eb6]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Sessions 149 + 150, 2026-07-19 (head_commit `0b67f76` → `043da3c`) —
> PLAN-0082 (the shared-ontology mechanism + `Person` promotion) BUILT
> end-to-end, then COMPLETE + archived, across both sessions (#801–812), with
> PLAN-0081 folded — and governance behaviour UNCHANGED throughout.** **The moat
> piece:** a shared `core` ontology home + an `imports:` grammar with cross-doc
> `core.<Type>` resolution + a `set`/`closed` type-system extension across all
> emitters + a shared `Person` (type + committed ORM + `person` table + Alembic
> migration) reconciled down to exactly ONE definition. **(s149 — build half,
> #801–808).** Filed PLAN-0082 `Status: Draft` (#801) + folded the SD-round
> (#802 — SD-F/G/H/I/K + OQ-1); **ADR-0033 Accepted (#803, `6dd6464`)** — the
> shared-ontology ADR + ADR-0008/0026 pointer notes, OQ-1=(a) JSONB. Steps 2–4:
> **#804** `ontology/core_v0.yaml` + the reserved `core` namespace + set/closed
> L1/L2; **#805** the Pydantic emitter (set→`frozenset` / closed→`extra=forbid`);
> **#806** the `imports:` grammar + qualified cross-doc `core.<Type>` resolution
> (no KeyError); **#807** set→JSONB across the SQL/ORM/JSON-Schema/TS emitters;
> **#808 (`5e45eb6`)** the committed shared Person ORM `services/db/person.py` +
> the `person` table + Alembic `0012` — RAN GREEN on dev Postgres. Additive
> throughout — zero shipped-behaviour change. **(s150 — reconciliation half,
> #809–812).** **Step 5 (#809)** reconciled the spec-layer `Person` onto the
> committed generated `core.Person` (SD-H=(a) = delete + re-export; Cray s150
> design = a1): the committed-dest mechanism was extended to the Pydantic emitter
> (`_PYDANTIC_COMMITTED_DEST["core"] → services/engine/procedures/person_model.py`),
> parallel to the committed ORM; the AC-4 one-`Person` grep guard was proven
> non-vacuous empirically. **A CI-scope miss caught + fixed:** the offline gate
> ran only the 3 changed files + engine/db tests, but CI runs `mypy services/`
> STRICT tree-wide — `--no-implicit-reexport` flagged 12 consumers of the plain
> re-export → fixed with the redundant-alias idiom (`import Person as Person`);
> lesson recorded (the offline gate must match CI scope). **Step 6 (#810)**
> migrated procurement + supply_chain onto the shared type (AC-5) + transformed
> the OQ-6 marker (AC-6). **Grounding collapsed the handoff's "LARGE dual-roster"
> work to SMALL:** AC-5's TYPE-unification was ALREADY satisfied by Step 5's
> re-export (every roster parses into the one shared `spec.Person`;
> `auth.py`/factory/`run.py` already read the shared seam — nothing to
> re-point). **AC-5 RE-SCOPE (Cray s150):** the "retire one of procurement's dual
> roster sources" clause was a MISREAD — `procedures.yaml` (the Thai SoD roster)
> and `person.csv` via `load_fastenal_principals` (the Fastenal LIVE-run demo
> roster) are DISTINCT demos, not redundant copies; retiring either deletes a
> demo (violates AC-5's own "verdicts may not change" bar). Neither retired,
> documented; classified **`superseded by new info`** (CLAUDE.md §6). The marker
> became a shared-type invariant (no re-arm at N=4), non-vacuity proven. **Step 7
> (#811, `e059303`)** — PLAN-0082 COMPLETE: all 7 ACs ticked against fresh
> on-disk evidence + a Closeout Verification block, `git mv` →
> `docs/plans/done/0082-*.md`. **PLAN-0081 fold (#812)** — SD-J=SPLIT resolved +
> executed: Step 9 shrunk to the `building_materials` residue, AC-7 re-pointed to
> PLAN-0082 AC-6, AC-12/13/14/15 → PLAN-0082 AC-1/2/3/4, OQ-1 → ADR-0033;
> **PLAN-0081 stays `Status: Draft`.** **Verification:** full offline suite
> **2888 passed / 7 skipped**, re-run on EACH merge commit; every existing
> SoD/tier/gate-resolve assertion UNMODIFIED. **OQ-2 (the `person`-table
> population story) stays OPEN + explicitly deferred** (the table ships empty,
> runtime roster-fed). **PLAN-0081 is UNBLOCKED** (Step 9 = land
> building_materials on the shared `Person`); the hero build stays uncommissioned
> beyond PLAN-0079's tracking stub. Post-merge: main=`043da3c`; 0 open PRs;
> loop-dispatcher DISABLED; MS-S1 idle/COLD (zero calls all session); dev
> Postgres UP (localhost:5442). Commits: `5e45eb6` (#808 merge, s149 tip) →
> `92f0019` (#809) → `c94d089` (#810) → `e059303` (#811) → `043da3c` (HEAD,
> #812 merge).

> **Sessions 147 + 148, 2026-07-18 (head_commit `8737b0a` → `0b67f76`) —
> PLAN-0081 opened + reshaped (s147, #797+#798) and PLAN-0080 CLOSED OUT +
> archived (s148, #799); all three PRs `docs(plans)`, ZERO code/behaviour
> change.** **(s147) The PLAN-0081 arc — the `building_materials`
> governed-credit HERO. #797 (`e03e56f`)** filed PLAN-0081 as `Status: Draft`
> — the BUILD plan Cray COMMISSIONED via PLAN-0079 Step T1 (SD-1 = trip AT-2
> signature **N=3** in-PLAN, do NOT wait for PLAN-0076 T1; SD-2 = ride the
> existing `measured_value` exposure field). SD-A/B/C/D resolved (Cray, s146).
> **#798 (`46a6ec2` → merge `fa4f6c6`)** folded in Cray's **SD-E=(b-ii)** +
> ratified **SD-J=SPLIT** (both via AskUserQuestion). SD-E=(b-ii) = promote
> `Person` to an ADR-0008 ontology `object_type` at a NEW shared/core ontology
> home. **The grounded crux:** the shipped codegen model is strictly
> per-vertical — NO shared/cross-vertical ontology home exists — so b-ii
> **INVENTS** the mechanism, it does not reuse one. **SD-J=SPLIT** = b-ii
> becomes its OWN new PLAN (+ a preceding ADR-0008 grammar amendment as its
> gate); PLAN-0081 Step 9 shrinks to the migration onto the shared `Person`
> that new PLAN ships. New AC-12/13/14/15 + surfaced sub-forks SD-F…SD-J +
> expanded OQ-1. **PLAN-0081 stays `Status: Draft` — no code shipped.**
> **(s148) The PLAN-0080 closeout — #799 (`81f307b` → merge `0b67f76`).**
> PLAN-0080 (trace-attribution legibility + the canonical
> `docs/conventions/ui.md`) had shipped end-to-end in s146 (#794 `feat(ui)` +
> #795 `docs(conventions)`) but its Status header still read "Draft (pending
> Cray ratification)" with all **9 ACs unticked**, and it was never archived.
> This closeout flipped Status → **Complete**, re-verified ALL 9 ACs against
> `main` on a FRESH disk read (each with `file:line` evidence), ticked them,
> and `git mv`'d it to `docs/plans/done/`. **AC-5 ticked as-scoped (Finding
> F-4):** the `TRACE` entries fed to `O.reasoningTrace` are normalized to
> canonical kinds; the surviving `kind:` tokens in PROP cards / KIND_BADGE /
> the pipeline DAG are separate local vocabularies the AC carved out. Findings
> **F-1/F-2/F-3 + OQ-1 stay recorded, NOT closed**. No code/behaviour change;
> SD-1(c)/SD-2(iii) were Cray-ratified in s146. Post-merge: main=`0b67f76`;
> 0 open PRs; loop-dispatcher DISABLED; MS-S1 idle/COLD — zero calls this
> session (docs-only). Commits: `e03e56f` (#797) → `46a6ec2` → `fa4f6c6`
> (#798 merge) → `81f307b` (#799 closeout) → `0b67f76` (HEAD, #799 merge).

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

> _Rotation note (session-150 reconcile, 2026-07-19, `docs(status):`):
> frontmatter → `head_commit 043da3c` (the #812 merge, the SHA this reconcile
> makes current; `docs(plans)` counts substantive per the Q4 rule). A combined
> **Sessions 149 + 150** block was PREPENDED (s149 PLAN-0082 shared-ontology
> mechanism BUILT behind ADR-0033, #803–808; s150 PLAN-0082 COMPLETE + archived
> #809–811 + PLAN-0081 fold #812), so the OLDEST — the **session-144** block
> (PLAN-0078 Step 7 CLOSEOUT #786, the transform seed-migration ARCHIVED at
> 12/12 ACs) — rotated OUT (4-session window, now s149/150 + s147/148 + s146 +
> s145/144) to the rotation-archive BASE `docs/status-archive/2026-h1-status.md`.
> Recent Decisions gained TWO rows (s149 PLAN-0082 mechanism BUILT #803–808;
> s150 PLAN-0082 COMPLETE + archived / PLAN-0081 fold #809–812) and so rotated
> its TWO OLDEST — the **s141** PLAN-0078 PR-4 row (#775) and the **s140**
> strategic-continuity artifact-3/4 row (#773) — to the same base (10-row
> window). Prior rotation notes (through the session-148 reconcile) are
> consolidated here (R4). Per the STATUS.md Rotation Policy (R1/R2/R4)._

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
| 2026-07-19 | **s150 — PLAN-0082 COMPLETE + archived (Steps 5-7, #809-811) + PLAN-0081 fold (#812): the reconciliation half of the shared-ontology arc — spec-layer `Person` reconciled to ONE generated `core.Person` (#809, SD-H=(a) + `_PYDANTIC_COMMITTED_DEST`), procurement+supply_chain migrated + OQ-6 marker transformed (#810), PLAN closed out at 7/7 ACs + archived (#811); PLAN-0081 folded (SD-J=SPLIT resolved, Step 9 shrunk).** AC-5 dual-roster "retire one" RE-SCOPED (misread — distinct demos, neither retired). CI-scope lesson (mypy strict re-export). OQ-2 deferred. Full narrative: the Sessions 149+150 CF block above | `043da3c` (HEAD, #812) / `e059303` (#811) / `docs/plans/done/0082-*.md` |
| 2026-07-18 | **s149 — PLAN-0082 shared-ontology mechanism BUILT (Steps 2-4 behind ADR-0033, #803-808): ADR-0033 Accepted (shared `core` home + `imports:` grammar + set/closed types + shared Person committed-ORM contract); `core_v0.yaml` + set/closed L1/L2 (#804), Pydantic emitter (#805), imports/cross-doc resolution (#806), set→JSONB emitters (#807), committed Person ORM + `person` table + Alembic 0012 migration ran green (#808).** Additive — zero shipped-behaviour change. Full narrative: the Sessions 149+150 CF block above | `5e45eb6` (#808) / `6dd6464` (#803) / `ontology/core_v0.yaml` + `services/db/person.py` + `alembic/versions/0012_person_table.py` |
| 2026-07-18 | **s148 — PLAN-0080 COMPLETE + archived (#799, `docs(plans)`): the trace-attribution + `ui.md` PLAN (shipped end-to-end s146 via #794/#795) closed out — Status → Complete, all 9 ACs re-verified against `main` on a fresh disk read (each with file:line evidence) + ticked, `git mv` → `docs/plans/done/`.** AC-5 ticked as-scoped (**F-4**: only the `TRACE` entries fed to `O.reasoningTrace` are canonical-normalized; PROP-card / KIND_BADGE / DAG `kind:` tokens are separate local vocabularies the AC carved out). Findings **F-1/F-2/F-3 + OQ-1 stay recorded, NOT closed**; no code/behaviour change. Full narrative: the Sessions-147+148 CF block above | `0b67f76` (HEAD, #799 merge) / `81f307b` (closeout) / `docs/plans/done/0080-*.md` (COMPLETE, archived) |
| 2026-07-18 | **s147 — PLAN-0081 arc (#797 Draft + #798 SD-E=(b-ii) fold / SD-J=SPLIT ratified, both `docs(plans)`): #797 filed the `building_materials` governed-credit HERO BUILD plan as `Status: Draft` (Cray COMMISSIONED via PLAN-0079 T1 — SD-1=trip AT-2 N=3 in-PLAN, SD-2=ride `measured_value`).** #798 folded Cray's **SD-E=(b-ii)** (promote `Person` to a NEW shared/core ADR-0008 `object_type` — the shipped codegen is strictly per-vertical, so b-ii INVENTS the mechanism) + ratified **SD-J=SPLIT** (b-ii → its OWN new PLAN + a preceding ADR-0008 grammar amendment as gate; PLAN-0081 Step 9 shrinks to the migration). New AC-12/13/14/15 + SD-F…SD-J + expanded OQ-1; **PLAN-0081 stays Draft — no code shipped.** Full narrative: the Sessions-147+148 CF block above | `fa4f6c6` (#798 merge) / `46a6ec2` (SD-E fold) / `e03e56f` (#797 Draft) / `docs/plans/0081-*.md` (Draft) |
| 2026-07-17 | **s146 — PLAN-0080 shipped end to end (#794 `feat(ui)` + #795 `docs(conventions)`): the reasoning-trace badge's substring sniff (`kind.includes('rule')`, mis-attributing 14/16 engine kinds) → ONE shared kind→{label,cls,actor} registry (`trace-kinds.js`, 23 kinds) read by BOTH the browser and an AST set-equality tripwire; colour=mechanism (theme.css UNCHANGED) + glyph=actor, unmapped kinds degrade visibly. + canonical `docs/conventions/ui.md` (11 anchored items).** **F-4:** a live probe refuted the offline "engine-only emitter" claim — `verticals/` seed executors emit `query` unmapped 9/9 → kind #23, scan root widened. Suite **2860/7** on BOTH merge commits. Full narrative: the Session-146 CF block above | `8737b0a` (#795 merge) / `6a2a42d` (#794) / `services/api/static/assets/trace-kinds.js` + `tests/api/test_trace_kind_labels.py` + `docs/conventions/ui.md` |
| 2026-07-17 | **s144 — the R4 arc CLOSED end to end (#789 guard → #791 + #792 splits): a ratified rule that had NO mechanism now has one, and every archive sits under the ~192 KB TRIGGER — not merely the cap — for the first time.** R4's own responsibility-matrix guard column read `—` where R1/R7 read `fail`; the rotation archive had rotted to **592,577 B = 2.26x the cap**. #789 shipped `tools/check_archive_size.py` (warn >192 KB, **fail >256 KB**, `files:`-scoped hook) GREEN **by design**; the BINDING live assertion (`test_live_archives_are_within_cap`) could only land in #791 **after** the split — a guard whose live assertion is RED cannot merge into a protected main. **Five-file c/d/e/f chain, not four** (a 4-way split lands one file at ~97% of the trigger). #792 split current-focus AND **recorded Cray's naming rule as CANON** — letters ascend with time, the base holds the recent window; **grep the archive dir, never cite a continuation by name**. Proofs DIFFER and say so: #791 = exact list equality (27 sections), #792 = multiset equality (30 blocks, deliberately reordered across files); both re-run AFTER pre-commit → *"equal except N trailing newlines, all stripped-equal"*, **NOT byte-identical**. Suite **2855/7** re-run on the merge commit itself. _[Concurrent session 145: #788 PLAN-0080 `Status: Draft` — SD-1/SD-2 UNRATIFIED, must NOT be executed, and `docs/conventions/ui.md` does NOT exist · #790 frontmatter-only bump, merged on Cray's instruction.]_ Full narrative: the Sessions-144+145 CF block above | `ce0f0a1` (HEAD, #792 merge) / `f00e4c7` (#791) / `b369fa6` (#789) / `694e8d7` (#788) / `tools/check_archive_size.py` + `.pre-commit-config.yaml` + `docs/runbooks/memory-architecture.md` (R4 matrix row `—` → `fail >256 KB` + the naming rule) + `docs/status-archive/**` (the c/d/e/f + b/c-cf chains) |
| 2026-07-17 | **s144 — PLAN-0078 COMPLETE at 12/12 ACs → `docs/plans/done/0078-transform-seed-migration.md` (#786, docs-only): a FAR smaller closeout than the s143 handoff predicted — 4 of the 6 open ACs (AC-7/8/9/12) were ALREADY SATISFIED on disk (unticked bookkeeping; each tick now cites its test by file:line, and AC-9 was re-verified INDEPENDENTLY rather than inherited from PR-4's R2 claim).** **AC-6 was the ONE genuine hole — and NOT the hole the PLAN described:** the predicted "Phase 2 shrinks the non-participant set" was FALSE on disk (PR-3/PR-4 only touched procedures already carrying a Phase-1 `enrich`) → classified **`superseded by new info`, NOT `was an error`** (CLAUDE.md §6) and pinned as DATA; the REAL hole was energy + aquaculture carrying no step-level `transform`-absence assertion anywhere. Both new tests proven non-vacuous **EMPIRICALLY** (probes reverted). **OQ-3 stays open; PLAN-0076 does NOT archive; F-PIN NOT closed** (L-4). Suite **2845/7** re-run on the merge commit itself. Full narrative: the Session-144 CF block above | `d8db032` (HEAD, #786 merge) / `49ff275` (sweep + ticks + `git mv`) / `docs/plans/done/0078-transform-seed-migration.md` (COMPLETE, archived) + `tests/**` (`test_derivation_pin.py:326` prediction pin + the energy/aquaculture transform census) |
| 2026-07-17 | **s143 — PLAN-0078 Phase 2 PR-5 COMPLETE (#784, `refactor`), the FINAL PR of the transform seed-migration: the PLAN-0075 AC-13 `derivation_hash` RETIRED end-to-end (AC-10 grep-clean, 0 hits outside `docs/`), the F-PIN marker rewritten (AC-11), PLAN-0076 Step T2 CLOSED.** A DELETION PR by design: AC-13 hashed supply_chain's ladder CONSTANTS into the pin only because the derivation lived in vertical CODE — PR-3/PR-4 declared it, so the reason vanished and the workaround went. Both retired guarantees re-homed at FULL strength (an ACTUAL `assert_governance_pin` raise, not an `h1 != h2` compare). 2 Cray ratifications OVERRODE the drafter (unrenderable AC-11 assert; KEEP the constants test-only). **F-PIN NOT closed; PLAN-0076 does NOT archive** (T1 open, AC-6 armed). Suite **2840/7** re-run on the merge commit itself. _[Siblings reconciled same pass: #783 R7 citation guard · #782 Lesson #0031.]_ Full narrative: the Session-143 CF block above | `6eea264` (HEAD, #784 merge) / `70d25a5` (PR-3 forward-ref fix) / `6e6ec7a` (PLAN-0076 T2) / `732fc0a` (the retirement) / `verticals/supply_chain/**` + `services/engine/procedures/**` (registry seam + `governance_pin` param retired across 8 files) + `tests/**` (exact-snapshot-key-set assertion) + `docs/plans/0078-*.md` (PR-5 COMPLETE) + `docs/plans/0076-*.md` (T2 CLOSED) |
| 2026-07-17 | **s143 — rotation policy **R7** is BINDING (#783, `chore`): never cite `docs/STATUS.md` by LINE NUMBER — cite the tracked artifact, or STATUS by SECTION NAME; a tripwire + an `always_run` pre-commit hook enforce it repo-wide (10 rotted sites cleaned, RED→GREEN 10 → 0).** _[Sibling #782 (`bc42136`, s142, reconciled s143): Lesson #0031 + the `fan-out-dispatch` skill — split parallel work on the WRITE-SET, not the idea.]_ Full narrative: the Session-143 CF block above | `3bf99bc` (#783 merge) / `abd41d4` (R7 + guard + cleanup) / `bc42136` (#782 merge) / `docs/runbooks/memory-architecture.md` (R7) + `tools/check_status_citations.py` + `docs/lessons/0031-*.md` + `.claude/skills/fan-out-dispatch/` |
| 2026-07-17 | **s142 — the THREE R2 carve-out TODOs DISCHARGED (#780/#778/#779, docs-only): each fact REHOMED into a tracked home FIRST, THEN trimmed** — Rock 4's evidence-asymmetry finding → ADR-0025 · the `sequence`-column deferral → the ordering-guard docstring (deferral STANDS) · the s74 demo-card SD-3 → the PLAN-0035 `done/` post-archival amendment (+ ADR-0030's `STATUS.md:<line>` citations re-pointed). Runbook R2 now records **"until it is rehomed" is a real exit**, and that an ADR citing `STATUS.md:<line>` is a **defect**. Suite **2822/7**. Full narrative: the Session-142 CF block (rotated to `docs/status-archive/` at the s146 reconcile — grep the archive dir, not one file) | `303fd48` (HEAD, #779) / `37ab124` (#778) / `12e69aa` (#780) / `docs/adr/0025-*.md:23-29` + `docs/plans/done/0035-*.md:576` + `tests/services/db/test_load_run_ordering_guard.py` + `docs/runbooks/memory-architecture.md` (R2) |

## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13; guarded trial (parallel to ADR-012) — verdict **continue-with-adjustments**. Run 1 (energy, s93) + Run 2 (supply-chain, s94) both COMPLETE, S-checks all PASS against pre-committed oracles, no R-PS trigger fired; C-1..C-3 CONFIRMED → **no open partner-sim debt**. ADR-011 audit stays gated on a REAL partner conversation (R3: SYNTHETIC provenance INFORMS but never TRIGGERS it). Full record: `docs/adr/0020-*.md` + the gitignored run packages `docs/research/private/2026-07-02-partnersim-run{1,2}-*.md`. _(Full prior narrative — the ~8 schema-mismatch findings, both run details, cross-run synthesis — archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **Procurement vertical — GO + SHIPPED (PLAN-0036 Fastenal, Stage 1):** 4th vertical greenlit (s75); PLAN-0036 drafted + merged Draft (#412, `7a7c036`; SD-1…SD-5 confirm-all). Demo target = Fastenal Thailand (auto-parts / EEC); **hero** = asset-failure → governed emergency sourcing, **calm-path** = low-stock reorder. Stage 1 = a PLAN-only pure-config plugin on the ADR-016 engine (zero `services/` core edit; CQ-1 / ADR-0023). **Pitch** = asset-ontology-triggered governed sourcing (native ontology ADR-008 + engine ADR-016), NOT the commoditized "governed"/"cross-vertical" claims. Full record: `docs/plans/0036-*.md` + the s72 de-risk dossier `docs/research/private/2026-06-22-procurement-*.md` (5 files: spec-expressiveness, GTM, asset-aware incumbent scan, AI-sourcing teardown, platform-incumbent deepdive). _(Full prior narrative archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [ ] **PLAN-0079 (`Status: Tracking`, filed #771, s140) — the `building_materials` governed-credit HERO, homed WITH ITS HONEST COST.** **[s147 — COMMISSIONED (Cray, Step T1, s146): PLAN-0081 (`Status: Draft`, #797 filed + #798 SD-E=(b-ii) fold / SD-J=SPLIT ratified) is now the BUILD plan carrying this hero; PLAN-0079's tracking stub + its AC-2 guard STAY armed until the hero ships.]** **The honest cost:** the hero is **AT-2 signature #3** → re-arms `test_at2_signature_retrigger.py` → **CI goes RED** → it **OBLIGATES the ADR-0025 D7 re-evaluation**; per **ADR-0032 D6 this is NEVER a "cheap follow-on"**. **Doing nothing is a real option** — the shipped Tier-1 Mirror is a supported, tested end-state and no test or commitment forces the hero; only **Cray commissioning it (Step T1)** promotes it. Full detail: `docs/plans/0079-building-materials-governed-credit-hero-tracking.md` — honest cost `:89-98`, the 3-part spine `:116-125`, the 3 open SDs `:246-260`. **Guard:** AC-2 presence guard-test `tests/services/engine/procedures/test_governed_credit_hero_tracking_guard.py` (CI RED on a premature archive-to-`done/` or a pruned STATUS pointer). *(#771; ADR-0032 = #770; the s137 mirror = #765.)*
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
