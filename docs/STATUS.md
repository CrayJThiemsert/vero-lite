---
last_updated: 2026-07-22T11:47:46+07:00
session: 160
current_batch: "s160 — 4 PRs: the Stop-hook contentless-reason FLOOR (#844, complements #843), the AT-2 N=4 doc drift + a new step_id-scope guard (#845), and 2 Accepted-ADR body corrections by plan-drafter (#846)."
current_actor: code
blocked_on: "Nothing blocking. main=0c9cdeb; 0 open PRs; merge-commit gate 2977/7 + mypy strict clean (98 files); loop-dispatcher DISABLED; MS-S1 idle/COLD; dev Postgres UP."
next_action: "Nothing ordered — 3 candidates: (1) Active-TODO trim (~4.66 KB, all trimmable), (2) fleet tire/PM calm path (G2-gated PLAN + 3 SDs), (3) autonomy-triggers row (Cowork). Tripwire B NOT built (refuted)."
head_commit: 0c9cdeb
recent_commits: [0c9cdeb, d7bbb8b, c42abe4, b5272e2, 25110c8, 66b9707, 532d3e4, 0090161, c8f7184, 89990fd]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 160, 2026-07-22 (head_commit `e55f2b8` → `0c9cdeb`) — a four-PR
> hook-hardening + doc-truth session: the Stop-hook classifier gained a
> **contentless-reason FLOOR** (#844) complementing the s159
> Cray-reserved-step rule (#843), the stale **AT-2 `N=4`** count was corrected
> everywhere it had drifted and the real `step_id` invariant pinned by a new
> guard (#845), and two Accepted-ADR bodies were corrected by `plan-drafter`
> (#846).**
> **(#843, `c8f7184` → merge `0090161`, `fix(hooks)` — recorded LATE.)** This
> landed in session 159, but the s159 reconcile never mentioned it (it was
> written before the PR existed; the s159 handoff flags the omission
> explicitly). The Stop-hook classifier prompt now treats **a step reserved for
> Cray as a natural stop, never a PROCEED next action**, pinned by a contract
> test proven non-vacuous by strip → RED → restore.
> **(#844, `532d3e4` → merge `c42abe4`, `fix(hooks)` — the CONTENTLESS-REASON
> FLOOR.)** The hook passes the classifier's `proceed` reason back to the agent
> **verbatim as its continuation instruction**, and the prompt requires that
> reason to NAME the next action — nothing enforced it. Session 160 observed the
> reason `"Continue to the next work step"` on a turn whose only real next step
> was Cray's decision among unratified candidates. **This is the COMPLEMENTARY
> shape to #843, not a regression of it:** #843 forbids *naming* a
> Cray-reserved step; a contentless reason names nothing, so #843's rule has
> nothing to bite on, and its contract test is four substring assertions on the
> prompt (behaviourally blind). New `_reason_is_contentless()` demotes such a
> verdict to pause. The design call that keeps it free of judgement: **a
> contentless reason is worthless even when `proceed` is CORRECT**, because the
> reason IS the instruction. It is a FLOOR, not a specificity judge —
> `_META_REASON_TOKENS` excludes every real action verb (guard-tested), and the
> OTHER s159 directive ("Continue running the test and mypy suite on the merged
> commit") still passes verbatim as the committed calibration pin. A **missing
> `reason` key** now demotes too (the old fallback was the literal
> `"continue"`). Also adds the gold case `pause-long-batch-then-question`:
> `gpt-oss:20b` already answers the existing short-question case correctly
> (19/20), so the live miss is a **fixture FIDELITY gap, not a model gap** —
> real payloads are a large work batch with the question only at the tail of the
> 8-turn / 3072-byte window. **+20 tests.**
> **(#845, `66b9707` + `b5272e2` → merge `d7bbb8b`, `chore` — the stale AT-2
> N-count, plus a new guard.)** AT-2 is **N=4** (`procurement` /
> `supply_chain` / `building_materials` / `fleet_maintenance` declare a
> `rule_gate` vocabulary; `energy` + `aquaculture` do not). Corrected in
> `spec.py` (×3 sites), `docs/conventions/procedure-archetypes.md`, and **the
> test module's own docstring** — the last two were NOT in the original scope:
> the drift was wider than recorded, and PLAN-0086 had shipped
> `fleet_maintenance` **without extending the archetype catalog** (its
> Quick-reference row and Instances list still enumerated three signatures —
> fixed in `b5272e2`, found during #846's R2). **Two corrections worth keeping
> as facts, not prose:** (a) `_RETRIGGER_N` is **retired and guards nothing**
> (its own docstring says so) — the live tripwire is the `_BASELINE_SIGNATURES`
> set-equality assertion, RED on a FIFTH signature; (b) PLAN-0087's "zero live
> `step_id` collisions today" is **wrong** — collisions already exist
> (`procurement` reuses `intake` / `approve` across three procedures); what is
> zero is the **over-mark**. New
> `tests/services/engine/procedures/test_sod_step_id_scope_guard.py` pins the
> real invariant (a step is in the vertical-flat `sod_steps` union **iff** its
> OWN procedure declares it), because `GovernanceStepExecutor.sod_steps` is a
> bare per-vertical `frozenset[str]` with no procedure key and nothing raises on
> an over-mark; it carries a second test so the guard cannot silently become
> vacuous. This hardens the premise **PLAN-0076 Step T1 (F-FACTORY)** defers on.
> **(#846, `25110c8` → merge `0c9cdeb`, `docs(adr)` — two Accepted-ADR body
> corrections, authored by the `plan-drafter` subagent (G1-gated), Code R2.)**
> **ADR-0032**'s "Where vero-lite stands" is a STATE snapshot and had drifted on
> more than N: it still said `building_materials` was a Tier-1 Mirror with **no
> `procedures.yaml`** and an unbuilt hero, counted four verticals, and did not
> know `fleet_maintenance` existed. It now reads six verticals, the
> governed-credit hero BUILT (PLAN-0081), fleet named, the full N=4 arc, and
> **symbolic anchors replacing the rotted line-number ones**. Its
> positive-consequences bullet — which claimed the ADR record makes exactly this
> stale-N-count error class harder to reintroduce, **while itself being stale**
> — was rewritten to say the durable guard is **the test, not the prose** ("the
> tripwire is CI; the ADR is the narrative"). **ADR-0025 D7's decision text was
> deliberately NOT rewritten** ("N ≥ 2" is the faithful 2026-06-28 record;
> editing a decision to match later events destroys the reasoning lineage) — a
> dated **outcome amendment** was appended instead, following the amendment
> precedent already in that ADR. **Attribution corrected by the drafter against
> Code's own dispatch:** **Cray** cancelled the D7 deferral, typed, 2026-07-21
> (s157), at the PLAN-0086 N=4 escalation; PLAN-0087 only **executed** the
> answer.
> **(deliberately NOT built.)** The second s159 tripwire — **tripwire B, the
> PLAN-0076 AC-6 F-PIN arm** — was NOT built: the grounding REFUTED its
> mechanism. The guard checks **file presence, not T1 text**, so it cannot
> self-release; it can only be deleted by hand, and a tripwire against a hand
> deletion buys nothing.
> **Verification:** both new tripwires proven non-vacuous **empirically** —
> backed up to `/tmp`, broken, **RED confirmed**, then restored **from the
> backup, never from git** (the s159 trap: a `git checkout` restore wipes the
> uncommitted edit under test and the run still prints a pass),
> `md5sum`-verified. Merge-commit gate against a pass/fail read fixed **BEFORE**
> the run — expected `2955 + 20 + 2 = 2977`; actual on `0c9cdeb` = **2977 passed
> / 7 skipped** (164.66s) + `mypy --strict services/` clean (98 files) ⇒
> `confirmed — prior intact`. Branch protection is **`strict: true`** —
> discovered while landing the stack (each remaining PR went `BEHIND` after a
> merge and needed a re-sync + a fresh `gate` run); it substantially closes the
> old "CI is PR-only, so the merge commit is never tested" gap. Grounding for
> the whole session came from a **5-agent Explore fan-out over 6 candidates**
> (the `next-work-analyst` skill), which is what surfaced the corrections above.
> Deterministic-offline: **MS-S1 idle/COLD, zero calls**, no host-state change;
> dev Postgres UP; loop-dispatcher DISABLED; **0 open PRs**; working tree clean
> but for the 2 KEEP untracked paths (`.claude/benchmark-results/`,
> `.claude/launch.json`). Commits: `c8f7184` → `0090161` (#843 merge) →
> `532d3e4` → `c42abe4` (#844 merge) → `66b9707` + `b5272e2` → `d7bbb8b` (#845
> merge) → `25110c8` → `0c9cdeb` (#846 merge, head_commit of record). The three
> `Merge remote-tracking branch 'origin/main'` sync commits (`d852ab1`,
> `329bfac`, `39a37d4`) are strict-mode re-sync noise and are excluded from
> `recent_commits`.

> **Sessions 158 + 159, 2026-07-21 (head_commit `79358c6` → `e55f2b8`) —
> PLAN-0087 BUILT (#840) then CLOSED OUT + archived at 8/8 ACs (#841): the
> ADR-0031 D3 gate seam's **criterion-vocabulary half** is SHIPPED —
> `ComplianceCriterion` is RETIRED from engine code and a vertical now
> **declares** its own `rule_gate` vocabulary, so a new AT-2 vertical ships its
> gate with ZERO engine diff.**
> **(what shipped — s158, #840.)** `VerticalProcedures.compliance_criteria:
> list[CriterionId]` (`spec.py`) — pattern-constrained by the `CriterionId`
> type and membership-validated at load by `_validate_compliance_criteria`;
> only the four `rule_gate` verticals were migrated (`energy` + `aquaculture`
> YAMLs are absent from the diff entirely).
> **(the claim is PROVEN, not asserted.)** AC-1's proof pair: a fixture
> criterion `zzz_fixture_only_sourcing_check` that exists NOWHERE under
> `services/` loads through the real `load_procedures_file` and gates through
> the real `evaluate_compliance`, while its undeclared twin is REFUSED at load;
> a repo-grep static guard keeps the id confined to that one test module.
> **Behaviour-preserving:** no pinned governance hash moved — the declaration
> block sits outside the pin surface (the `principals` precedent).
> **(the scope split — Cray-ratified SD-1 = (a), typed.)** This discharges the
> criterion-vocabulary half of **PLAN-0076 Step T1 (F-FACTORY)** only; the
> procedure-aware `ExecutorFactory` half stays OPEN and still owned by
> PLAN-0076, so **PLAN-0076 does NOT archive** and its AC-6 presence guard
> stays ARMED — **no guard re-homing occurred, deliberately**. ADR-0031 D3
> row 3 was updated on landing per D4.4 — exactly one table row, which was
> AC-7's whole obligation.
> **(the closeout — s159, #841.)** `git mv docs/plans/0087-*.md
> docs/plans/done/`, Status `Draft` → **COMPLETE** (never flipped to
> `Accepted` — an `Accepted`-status PLAN is G1-gated for its own closeout), all
> 8 ACs ticked, plus a new **Closeout** section recording (a) the evidence read
> at closeout time and (b) what was deliberately left undone. Every AC was
> re-read against **fresh on-disk evidence** rather than carried over from the
> build session's notes — CLAUDE.md §6 ("Verification is hygiene, not a
> verdict") double-gates `confirmed — prior intact` on the pre-committed
> pass/fail read AND a fresh artifact.
> **(deliberately NOT done, and recorded as such in the PLAN.)** PLAN-0076 is
> **NOT** archived (T1's factory half open; §B item 1 — F-PIN's new-run
> re-routing threat — open by construction), so its guard stays armed.
> `scored_rule._KNOWN_CRITERIA` was NOT opened: zero extension pressure to
> date, and its shape is `derive`-grammar-like, not vocabulary-like. The stale
> `N=2`/`N=3` doc drift in ADR-0025 D7 + ADR-0032 was NOT folded in — s157
> expected it to ride along with PLAN-0087's G1-gated edits, but AC-7 obligated
> that one ADR-0031 row and nothing more; it now needs its own small
> `plan-drafter` dispatch.
> **Verification:** the suite walked **2943/7 → 2951/7 → 2954/7** across the
> build and re-ran GREEN on the merge commit `c6eec65`. Gate re-run at closeout
> on `main = c6eec65`: full suite **2954 passed / 7 skipped** (169.91s) and
> `mypy --strict services/` clean (98 source files) — **matching the build
> session exactly**; the four doc-reading guard tests re-ran green after the
> `git mv` (84 passed). Deterministic-offline: **MS-S1 idle/COLD, zero calls in
> both sessions**, no host-state change, no demo/dev server started; dev
> Postgres `vero-postgres` UP (localhost:5442 — evidenced by only 7 skips).
> `main` protected; **#841 is the only open PR**; loop-dispatcher DISABLED;
> working tree clean but for the 2 KEEP untracked paths
> (`.claude/benchmark-results/`, `.claude/launch.json`). Commits: `d9a0ad1` →
> `16c3622` → `bdd07ed` → `4f9cb7a` → `c6eec65` (HEAD of `main`, #840 merge) →
> `e55f2b8` (#841 closeout, head_commit of record).

> **Session 157, 2026-07-21 (head_commit `2f46fc9` → `79358c6`) — PLAN-0086
> COMPLETE: the AI-Transition **View-2** scaffolder run as a TIMED MANUAL
> baseline — a rambling, deliberately-dirtied customer monologue carried to a
> live, governed, human-gated pipeline on a 6th vertical (`fleet_maintenance`,
> #838), shipped with its measurement pack; and the ADR-0025 D7 AT-2-generator
> deferral CANCELLED at N=4.**
> **(the headline number — it MUST NOT be quoted without its caveat; AC-7 makes
> that binding.)** Narrative → governed pipeline in **27 minutes 39 seconds
> hands-on** (wall 43m17s minus 6m51s of customer-answer waits and 8m48s stopped
> on a governance escalation). **Caveat (AC-7, binding):** Code drafted the
> pre-dirtied narrative, so this is a **LOWER BOUND on true blind intake** —
> Cray's dirtying plus the four-question intake log partially restore validity,
> and it measures an operator with deep prior knowledge of this codebase.
> **(what shipped.)** `verticals/fleet_maintenance/` — an 8-file package
> HAND-WRITTEN from the `building_materials` template (`vero-lite new-vertical`
> was banned by the measurement protocol). Asset=Truck, Site=Depot; AT-2
> `governed_repair_approval`: intake → judge (per-truck repair ceiling) →
> reshape → quote_gate (`rule_gate`) → approve (money `doa_tier` + SoD) →
> fulfill. **First vertical shipping the PLAN-0085 gate advisory ON by default**
> (PLAN-0086 L-B — the parked gate explains itself on day one). Plus 14 tests,
> the 3 mandatory hand-wires, and an additive `ComplianceCriterion +=
> three_quote` engine change.
> **(ADR-0025 D7 — the AT-2-generator deferral is CANCELLED; Cray-ratified,
> typed.)** Shipping fleet fired `test_at2_signature_retrigger` at N=4. Code
> ESCALATED rather than patched — the marker says "re-argue it, do not just
> update this list", and the fix Code judged correct was also the fix that turned
> Code's own red green. Both readings went to Cray: by gate SHAPE fleet teaches
> nothing new (composition and authority quantity identical to
> `building_materials`'), but it is the FOURTH consecutive vertical to require an
> engine-level `ComplianceCriterion` extension — and repeated pressure on shared
> code is what Rule-of-Three actually watches. Cray's rationale: accept the cost
> now for future flexibility. The `len(signatures) < _RETRIGGER_N` guard is
> RETIRED and REPLACED (never deleted) by `test_at2_extraction_obligation_is_owned`
> (same module), which fails if PLAN-0076 — the standing owner via Step T1 — is
> archived or loses its record. **The extraction itself is NOT done — it needs
> its own PLAN, G2-gated, so `plan-drafter` must author it.** That is the most
> important open thread out of this session.
> **(the finding that outlives the number.)** Two of the four customer rules
> could NOT be fully encoded: the quote-comparison ฿ threshold has nowhere to
> live (a `rule_gate` criterion is pass/fail on a supplied signal and carries no
> threshold field, and ADR-0025 D4 forbids the amount in prose), and
> `EmergencyWaiver` has no fields for the emergency cap or the ratification
> window. Both are recorded in the question log and surfaced to readers in the
> vertical README as an explicit "stated but NOT enforced" table — a
> narrative→pipeline tool that silently dropped the un-modellable half would be
> worse than no tool.
> **Verification:** offline gate at execution HEAD **2943 passed / 7 skipped**,
> **re-run GREEN on the merge commit `79358c6` itself** (2943/7 — CI is PR-only,
> so the merge commit is otherwise never tested); baseline re-measured at
> `219a134` before the clock started (2927/7, matching the #833 figure —
> `confirmed — prior intact`); `mypy --strict services/` clean (98 files);
> `ruff check .` + `ruff format --check .` clean at CI scope; CI `gate` PASS on
> #838 (3m7s; 17 files, +1825/−40). **AC-4 by construction** — the diff touches ZERO files under the
> five existing verticals. Live: `run-b9c0804b52f0` parks `waiting_human` at
> `approve` with the advisory persisted (grounded fleet reasons, `model:
> deterministic`, no confidence key in the advisory), corroborated in the Monitor
> gate panel and confirmed by Cray. PLAN-0086 archives to `done/` in the
> follow-on closeout PR. Commits: `a2ef45e` (#838) → `79358c6` (HEAD, #838
> merge).

> _Rotation note (session-160 reconcile, 2026-07-22, `docs(status):`): added
> the **Session 160** CF block (the four-PR arc — #843 the Cray-reserved-step
> classifier rule, recorded LATE / #844 the Stop-hook contentless-reason FLOOR /
> #845 the AT-2 `N=4` correction + the new `step_id`-scope guard / #846 the two
> Accepted-ADR body corrections) and rotated the OLDEST CF block — **Session
> 156** (the morning map-label UI fix #829, the long-carried demo rehearsal
> PERFORMED + the PLAN-0084 closeout #830, and the PLAN-0085 advisory-gate arc
> filed → ratified → built → closed, #831-#834) — to the Current-Focus rotation
> base `docs/status-archive/2026-h1-current-focus.md`. Rotating it is what **R2
> requires**, not a headroom judgement: the 4 most-recent sessions are now
> 160 / 159 / 158 / 157, so the s156 block fell **outside** the window. Recent
> Decisions gained ONE row (the s160 four-PR arc) and rotated its ONE OLDEST —
> the **s149** PLAN-0082 shared-ontology-mechanism row (#803-#808) — to the
> rotation base `docs/status-archive/2026-h1-status.md`. Window after this
> reconcile: **CF = 3 blocks covering the 4 newest sessions** (s160 + s158/159 +
> s157 — well under the 8-block cap); RD = 10 rows. **STATUS: 51,045 B → 56,272
> B** (caller-measured, not estimated), against the 64 KB R1 ceiling — the net
> growth is a four-PR block replacing a smaller one; the Active-TODO trim
> (~4.66 KB, all four oversized items verified to have a tracked home) is the
> standing headroom lever if the soft 48 KB target is wanted back. Per the
> STATUS.md Rotation Policy (R1/R2/R4)._
>
> _Rotation note (session-159 reconcile, 2026-07-21, `docs(status):`): added
> the **Sessions 158 + 159** CF block (PLAN-0087 BUILT #840 → CLOSED + archived
> #841) and rotated the OLDEST CF block — **Session 152** (PLAN-0083, the
> procurement ontology↔CSV column drift closed at the `FastenalCsvAdapter`
> seam, #818/#819) — to the Current-Focus rotation base
> `docs/status-archive/2026-h1-current-focus.md`. Recent Decisions gained ONE
> row (the PLAN-0087 build+closeout arc) and rotated its ONE OLDEST — the
> **s148** PLAN-0080 closeout row (#799) — to the rotation base
> `docs/status-archive/2026-h1-status.md`. The **session-156** rotation note was
> itself rotated to the same base (R4 consolidation). **Amended later the same
> session (the R1 headroom follow-up, `docs(status):`): the `Sessions 153 + 154 +
> 155` CF block (~12.8 KB) was ALSO rotated** to the Current-Focus base. This was
> not a judgement call about headroom — it is what **R2 already required**:
> the canonical rule keeps *"blocks from the **4 most-recent sessions**, capped at
> 8 blocks (blocks ≠ sessions)"* (`docs/runbooks/memory-architecture.md` R2), and
> the 4 most-recent sessions are 159 / 158 / 157 / 156, so the s153-155 block was
> already **outside** the window when this reconcile ran. The first pass held it
> back on a "keep 4 CF **blocks**" reading of the file's own practice; the runbook
> is canonical and wins (CLAUDE.md §1). Window after the amendment: **CF = 3
> blocks covering the 4 newest sessions** (s158/159 + s157 + s156 — well under the
> 8-block cap); RD = 10 rows. **STATUS: 63,159 B → 50,390 B**, against the 64 KB
> R1 ceiling. Per the STATUS.md Rotation Policy (R1/R2/R4)._
>
> _Rotation note (session-157 reconcile, 2026-07-21, `docs(status):`): added the
> **Session 157** CF block (PLAN-0086 — the timed manual scaffold of vertical #6
> `fleet_maintenance`, #838) and rotated the OLDEST CF block — **Session 151**
> (PLAN-0081 `building_materials` governed-credit hero, #814) — to the
> Current-Focus rotation base `docs/status-archive/2026-h1-current-focus.md`.
> Recent Decisions gained ONE row (the PLAN-0086 / ADR-0025-D7-cancellation arc)
> and rotated its ONE OLDEST — the **s147** PLAN-0081 arc row (#797/#798) — to
> the rotation base `docs/status-archive/2026-h1-status.md`. The **session-155
> EVENING** rotation note was itself rotated to the same base (R4
> consolidation). Window after this reconcile: CF = 4 blocks (s157 + s156 +
> s153/154/155 + s152); RD = 10 rows. Per the STATUS.md Rotation Policy
> (R1/R2/R4)._

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
| 2026-07-22 | **s160 — four PRs hardening the Stop hook and the AT-2 doc record. #844 the CONTENTLESS-REASON FLOOR (a `proceed` reason naming no action is demoted to pause — the COMPLEMENTARY shape to #843, which landed s159 unrecorded); #845 AT-2 corrected to N=4 + a new cross-procedure `step_id`-scope guard; #846 (`plan-drafter`, G1) ADR-0032 re-grounded + a dated ADR-0025 D7 OUTCOME amendment, its "N ≥ 2" decision text deliberately NOT rewritten.** Two premises now pinned in code, not prose: `_RETRIGGER_N` is retired and guards nothing, and PLAN-0087's "zero live `step_id` collisions" is wrong (the OVER-MARK is what is zero) — both carried by the guard docstrings cited right. Tripwire B NOT built (mechanism refuted). Merge-commit gate `0c9cdeb`: **2977/7** + mypy strict 98 files, against a pass/fail read fixed BEFORE the run. Full narrative: the Session-160 CF block above | `0c9cdeb` (#846 merge, head_commit of record) / `d7bbb8b` (#845) / `c42abe4` (#844) / `0090161` (#843) / `tests/services/engine/procedures/test_sod_step_id_scope_guard.py` + `tests/services/engine/procedures/test_at2_signature_retrigger.py` + `docs/adr/0025-at2-managerial-layer.md` (D7 amendment) |
| 2026-07-21 | **s158 + s159 — PLAN-0087 BUILT (#840) then CLOSED at 8/8 ACs + archived (#841 `docs(plans)`): the ADR-0031 D3 gate seam's CRITERION-VOCABULARY half — `ComplianceCriterion` RETIRED from engine code; a vertical DECLARES its own `rule_gate` vocabulary in `procedures.yaml` (`VerticalProcedures.compliance_criteria`, pattern-typed + membership-validated at load), so a new AT-2 vertical ships its gate with ZERO engine diff — PROVEN by AC-1's fixture-criterion pair (loads + gates from outside `services/`; the undeclared twin refused), not prose.** Behaviour-preserving — no pinned governance hash moved. **Cray-ratified SD-1 = (a) (typed): the procedure-aware `ExecutorFactory` half is OUT of scope and stays owned by PLAN-0076 T1 → PLAN-0076 does NOT archive, its AC-6 guard stays ARMED, no re-homing.** ADR-0031 D3 row 3 updated per D4.4. Closeout gate on `main=c6eec65`: **2954/7** (169.91s) + mypy strict 98 files, matching the build. Full narrative: the Sessions 158+159 CF block above | `c6eec65` (#840 merge) / `e55f2b8` (head_commit of record, #841) / `services/engine/procedures/spec.py` + `tests/services/engine/procedures/test_declared_criterion_vocabulary.py` + `docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` (COMPLETE, 8/8) |
| 2026-07-21 | **s157 — PLAN-0086 COMPLETE (#838 `feat(verticals)`): the narrative→pipeline scaffolder run as a TIMED MANUAL baseline — a dirtied customer monologue → a live, governed, human-gated pipeline on the 6th vertical `fleet_maintenance` in 27m39s hands-on (wall 43m17s − 6m51s answer-waits − 8m48s escalation). AC-7 caveat, BINDING and never to be dropped: Code drafted the pre-dirtied narrative → LOWER BOUND on blind intake, operator knows this codebase.** AT-2 `governed_repair_approval` = the 4th signature; first vertical with the PLAN-0085 gate advisory ON by default; additive `ComplianceCriterion += three_quote`. **ADR-0025 D7 AT-2-generator deferral CANCELLED at N=4 (Cray-ratified, typed — 4th consecutive vertical forcing an engine-level criterion extension); the `_RETRIGGER_N` guard RETIRED + REPLACED by `test_at2_extraction_obligation_is_owned` (PLAN-0076 T1 = standing owner). The extraction PLAN is UNOPENED — G2-gated → `plan-drafter`.** 2 of 4 customer rules un-encodable (quote-comparison ฿ threshold has no home on a `rule_gate` criterion; `EmergencyWaiver` lacks cap/ratification fields) — surfaced in the vertical README's "stated but NOT enforced" table. Suite **2943/7**; mypy strict 98 files; ruff clean; live `run-b9c0804b52f0` parks `waiting_human` at `approve`. Full narrative: the Session-157 CF block above | `79358c6` (HEAD, #838 merge) / `a2ef45e` (build) / `verticals/fleet_maintenance/` + `tests/services/engine/procedures/test_at2_signature_retrigger.py` (guard replacement) + `docs/plans/0086-fleet-vertical-timed-manual-scaffold.md` (closeout pending) |
| 2026-07-21 | **s156 — PLAN-0085 "Advisory Gate Recommendation (AI-Transition Rung 1)" filed → 5 SDs Cray-ratified → BUILT → closed, ONE day (#831 Draft `docs(plans)` / #832 SDs `docs(plans)` / #833 `feat(engine)` / #834 closeout `docs(plans)`): an advisory recommendation with grounded reasons at procurement's `doa_tier` approval gate — SHOWN, NEVER routes (the ADR-0019:50-57 fence, now CI-pinned: byte-identical approve audit advisory on/off/exploding-builder).** All 5 SDs = the draft rec (AskUserQuestion): SD-1(b) emit INSIDE the gate propose path (ZERO hash change), SD-2(b) stub-first deterministic arm + opt-in live MS-S1 seam, SD-3 all three procedures, SD-4 gate-panel advisory block, SD-5 new trace kind `advisory_recommendation` (actor `llm`). New `gate_advisory.py` (never-raise, ADR-0030 D5) wired via `GovernanceActionExecutor` + procurement `_executors`; Monitor gate-panel block, NO score (the L-C/#823 trust shape). Suite **2927/7**; mypy/ruff clean; live-verified 8101. Unplanned value (Cray): the advisory doubles as an ONBOARDING aid → recorded as a signal for the View-2 reshape. Full narrative: the Session-156 CF block above | `2f46fc9` (#833 BUILT, head_commit of record) / `63009c3` (#834 closeout, main HEAD) / `8809776` (#831) / `d679036` (#832) / `services/engine/procedures/gate_advisory.py` + `docs/plans/done/0085-*.md` (archived, 8/8) + `docs/runbooks/run-oct-demo.md` §3e |
| 2026-07-21 | **s156 — the demo rehearsal (carried s153→155) PERFORMED + PASSED (Cray, Beats 1-5 on 8101 incl. the new PLAN-0084 map→monitor opening beat, ratified "ok"), which GATED the PLAN-0084 closeout (#830 `docs(plans)`, 9/9 ACs + archived to `done/`); + a morning map-label UI fix (#829 `fix(ui)`, `view-map.js ?v=c39`, plate moved BELOW the node, 0 overlaps live).** Cray then opened the two-view **AI-Transition** frame — (1) an LLM at the approval gate, (2) a narrative→pipeline scaffolder — and ratified the SEQUENCE: capture a discussion note → build View-1 (Rung 1 = PLAN-0085) → reshape View-2 against Rung-1's result → build View-2; umbrella thesis = governance human in/on-the-loop → first-stage AI automation (gitignored note, binds nothing). A model-economy policy ratified (private memory, not a repo change): Fable for complex planning/research, Opus 4.8 + Extra for execution/coding-to-plan. Full narrative: the Session-156 CF block above | `ad39774` (#830) / `19f5caa` (#829) / `docs/plans/done/0084-*.md` (archived, 9/9) + `.claude/handoffs/session-156/2026-07-21-0851-*-ai-transition-two-views.md` |
| 2026-07-20 | **s155 (late) — PLAN-0084 shipped end-to-end in one arc (#825 `docs(plans)` filed Draft → #826 `docs(plans)` all 5 SDs Cray-resolved [SD-B all-four-rotatable + SD-D both-entry-points, both WIDER than rec] → #827 `feat(demo)` BUILT): map↔monitor run linkage (runs stamp `trigger_context["subject"]`; fail-soft `subject` on RunSummaryView/RunDetailView; the map ingests `/runs` direct-fetch [never the mock-fallback O.API path], dashed amber in-flight ring, node-panel "Governed runs · in flight" + "Open in Monitor →" via `ViewMonitor.focusRun`/`oct:goto`) + opt-in seed rotation (`--asset`/`--rotate`, asset-keyed failure pick, all 4 non-hero assets).** **Headline = SD-F, Cray-ratified mid-build — the PLAN's grounding `was an error`: the registered procurement adapter was scaffold-era synthetic (`equip-*`) while every hero surface narrates Fastenal (`AST-*`) — split-brain demo; `register_procurement_adapter` now registers the `FastenalCsvAdapter`** (plant.csv geo anchor + part.csv stock fields; synthetic semantics preserved EXACTLY incl. the PLAN-0066 AC-6 flip case; 4 test repins — the PLAN-0083 canonical-coverage tripwire caught the new keys, WORKING AS DESIGNED). Live 8101 verification: strip LIVE, zero console errors, AC-4 full click-through + AC-9 event-run lights the map + AC-5 no-fallback + AC-7 tier rotation + AC-2 legacy fail-soft. Suite **2922/7** (2915 + 7 new); mypy strict 142 files; ruff clean. PLAN-0084 stays Draft, ACs deliberately UNTICKED — closeout after Cray's rehearsal passes. Full narrative: the Sessions 153+154+155 CF block above | `25b31e2` (HEAD, #827 merge) / `45fcba1` + `64119b9` (build) / `e5f3ede` (#826 merge) / `628bfa1` (#825 merge) / `docs/plans/0084-map-monitor-run-linkage-and-seed-rotation.md` (Draft, 6/6 SDs resolved) + `verticals/procurement/data_adapter/__init__.py:99` + `docs/runbooks/run-oct-demo.md` §3d |
| 2026-07-20 | **s153-155 — #822 `docs(runbook)` staged the config-pin fail-closed refusal as a deliberate demo beat (run-oct-demo.md §3c, Beat 06, PLAN-0047 Step 6); s154 ZERO commits (Cerebras-KB strategy read: predict+warn = existing Shape-1 IF deterministic, artifact-KB = D3 Shape-2 pilot-gated, org-wide ingestion CUT, reframe = "governed retrieval over the decision record"); #823 `fix(ui)` REMOVED the operator confidence badge from BOTH cards — story scene-2 (hardcoded 86%) and View-B `decisionCard()` (LIVE `rec.confidence`, the load-bearing one) — executing the ratified s74 trust shape.** Trace/fault-mode/DAG confidence KEPT by design. Static assets only; suite **2915/7** re-run on the merge commit `4edfa3f`; live 8101 check `LIVE` with a `confidence: 0.86` fixture. **4 claim-vs-code corrections:** naive-RAG comparison ALREADY run (PLAN-0027 — lean RAG TIES governed on accuracy at 3-15x lower latency) · "actions router fully governed" is overstated · the determinism line is ADR-0019:50-57 + ADR-010 IN-3, NOT ADR-0031 · a 4th AT-2 signature is UNBUILDABLE (no vertical has the substrate). Full narrative: the Sessions 153+154+155 CF block above | `4edfa3f` (HEAD, #823 merge) / `ffb251b` + `f09cc99` (badge removal) / `d8057fb` (#822 merge) / `b45f5c4` (#821 merge) / `docs/runbooks/run-oct-demo.md` §3c + `services/api/static/assets/view-anomaly.js` + `view-story.js` |
| 2026-07-19 | **s152 — PLAN-0083 (fix c1) BUILT + verified + archived (#818 `feat`, #819 `docs(plans)`): the procurement ontology↔CSV column drift CLOSED at the `FastenalCsvAdapter` seam — `_COLUMN_RENAMES` on the `fetch_objects` path maps raw Fastenal CSV → canonical ontology names (type key `Asset`→`Equipment` [SD-1] + 5 columns [`part_id`→`part_no`, `price_thb`→`price`, `asset_id`→`equipment_id`, `site`→`site_id`, `lead_time_days`→`lead_time`] + `PurchaseOrder.asset_id`→`equipment_id` [SD-4a]; ฿-columns DEFERRED raw [SD-4b]), so every consumer sees ONE canonical vocabulary.** Rides under ADR-016's LOCKED "mapping absorbs source diversity" boundary — zero-core-edit (no ADR / ontology YAML / regen / `services/` engine edit; ADR-0023), diff = adapter + vertical + tests only. A `test_fastenal_adapter_canonical_coverage.py` tripwire pins per-type set-equality + required-props + rename-target validity + the SD-4b ฿-defer, non-vacuous EMPIRICALLY (dropped a rename → RED → reverted); R2 added the under-scoped `governance_audit.py:177/179`. Suite **2915/7** (2896 + 19); mypy strict + ruff clean; CI gate PASS on #818. Full narrative: the Session-152 CF block above | `a53c6ed` (#818 merge) / `a211651` (build) / `5140ee3` (HEAD, #819 merge) / `docs/plans/done/0083-*.md` (archived) + `tests/verticals/procurement/test_fastenal_adapter_canonical_coverage.py` |
| 2026-07-19 | **s151 — PLAN-0081 BUILT end to end (#814, `feat(building_materials)`): the `building_materials` governed-credit HERO — the 3rd AT-2 signature (`building_materials.governed_credit_release`), Cray-commissioned this session. An exposure breach above the account's own `credit_limit_thb` routes the full governed AT-2 spine (per-entity band → `rule_gate` KYC/overdue-AR/blacklist → `doa_tier` approval + SoD); the ฿550,000 breach routes mid-ladder.** The 3rd signature REUSES the money `doa_tier` ladder UNCHANGED (no new gate kind / authority quantity) — only `ComplianceCriterion += {kyc, overdue_ar, blacklist}` grows; engine diff bounded to that additive `spec.py` block (the `Person` promotion was PLAN-0082's, already on main). **ADR-0025 D7 re-eval PERFORMED at N=3** (Cray-ratified: generator stays deferred, marker re-arms N=4). Closeout: PLAN-0079 tracking stub RETIRED (Step T3) + guard test DELETED; PLAN-0076 T1 gate-seam trigger recorded MET (seam PLAN un-opened); PLAN-0081 archived at 15/15 ACs. Suite **2896/7** re-run on the merge commit `9422c40`; mypy strict + ruff clean. Full narrative: the Session-151 CF block above | `9422c40` (HEAD, #814 merge) / `a46bef8` (build) / `docs/plans/done/0081-*.md` (archived, 15/15) + `tests/verticals/building_materials/test_governed_credit_hero.py` |
| 2026-07-19 | **s150 — PLAN-0082 COMPLETE + archived (Steps 5-7, #809-811) + PLAN-0081 fold (#812): the reconciliation half of the shared-ontology arc — spec-layer `Person` reconciled to ONE generated `core.Person` (#809, SD-H=(a) + `_PYDANTIC_COMMITTED_DEST`), procurement+supply_chain migrated + OQ-6 marker transformed (#810), PLAN closed out at 7/7 ACs + archived (#811); PLAN-0081 folded (SD-J=SPLIT resolved, Step 9 shrunk).** AC-5 dual-roster "retire one" RE-SCOPED (misread — distinct demos, neither retired). CI-scope lesson (mypy strict re-export). OQ-2 deferred. Full narrative: the Sessions 149+150 CF block above | `043da3c` (HEAD, #812) / `e059303` (#811) / `docs/plans/done/0082-*.md` |

## In-Flight Discussions

- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13; guarded trial (parallel to ADR-012) — verdict **continue-with-adjustments**. Run 1 (energy, s93) + Run 2 (supply-chain, s94) both COMPLETE, S-checks all PASS against pre-committed oracles, no R-PS trigger fired; C-1..C-3 CONFIRMED → **no open partner-sim debt**. ADR-011 audit stays gated on a REAL partner conversation (R3: SYNTHETIC provenance INFORMS but never TRIGGERS it). Full record: `docs/adr/0020-*.md` + the gitignored run packages `docs/research/private/2026-07-02-partnersim-run{1,2}-*.md`. _(Full prior narrative — the ~8 schema-mismatch findings, both run details, cross-run synthesis — archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **Procurement vertical — GO + SHIPPED (PLAN-0036 Fastenal, Stage 1):** 4th vertical greenlit (s75); PLAN-0036 drafted + merged Draft (#412, `7a7c036`; SD-1…SD-5 confirm-all). Demo target = Fastenal Thailand (auto-parts / EEC); **hero** = asset-failure → governed emergency sourcing, **calm-path** = low-stock reorder. Stage 1 = a PLAN-only pure-config plugin on the ADR-016 engine (zero `services/` core edit; CQ-1 / ADR-0023). **Pitch** = asset-ontology-triggered governed sourcing (native ontology ADR-008 + engine ADR-016), NOT the commoditized "governed"/"cross-vertical" claims. Full record: `docs/plans/0036-*.md` + the s72 de-risk dossier `docs/research/private/2026-06-22-procurement-*.md` (5 files: spec-expressiveness, GTM, asset-aware incumbent scan, AI-sourcing teardown, platform-incumbent deepdive). _(Full prior narrative archived to `docs/status-archive/` at the s117 deep-rotate.)_
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm. Not yet drafted. **Note:** ADR-005 was originally reserved for this decision (PLAN-001 line 9 forward-reference); ADR-005 was reused for the strategic pivot, so the Postgres-image ADR needs a fresh number (**≥ ADR-014** — ADR-011 earmarked for the audit framework, ADR-012 taken by Cowork second free-form tier, ADR-013 taken by autonomy axis relocation; floor bumped 2026-05-23 per ADR-013 §Consequences/Neutral + T6).
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **Convention extraction:** `git.md` and `hardware.md` may still be extracted from CLAUDE.md (low priority).

## Active TODOs

- [ ] **The AT-2 extraction — PLAN-0087 is COMPLETE, 8/8 ACs, and ARCHIVED to `docs/plans/done/` (s159, #841); the CRITERION-VOCABULARY half SHIPPED (s158, #840) and only the F-FACTORY half remains, owned by PLAN-0076 T1.** ADR-0025 D7's generator deferral was **CANCELLED at N=4** (Cray-ratified, typed, 2026-07-21) after `fleet_maintenance` became the 4th consecutive vertical to force an engine-level `ComplianceCriterion` extension. **PLAN-0087** (`docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` — `plan-drafter`-authored, Code R2 + commits; closed out s159 with Status `Draft` → **COMPLETE** [never `Accepted` — that status G1-gates a PLAN's own closeout], all 8 ACs re-read against **fresh on-disk evidence**, plus a **Closeout** section recording the evidence read and what was deliberately left undone) discharges the vocabulary half: `ComplianceCriterion` is **retired from engine code**, each vertical **declares** its own `rule_gate` vocabulary in its `procedures.yaml` (`VerticalProcedures.compliance_criteria`, pattern-typed + membership-validated at load), and **a new AT-2 vertical ships its gate with ZERO engine diff** — proven by AC-1's proof pair (a fixture criterion existing nowhere in `services/` loads + gates, with a static guard keeping it that way), not asserted. Behaviour-preserving: **no pinned governance hash moved** (the declaration block is outside the pin surface — the `principals` precedent). Cray ratified the scope split **SD-1 = (a)** (typed, s158): **the procedure-aware `ExecutorFactory` half is NOT in PLAN-0087** and stays owned by **PLAN-0076 Step T1**, triggers armed — its evidence is an *inert* audit display-flag over-mark with zero live `step_id` collisions, versus the vocabulary half's 4-engine-edits-in-4-verticals. `test_at2_extraction_obligation_is_owned` still turns RED if PLAN-0076 is archived or loses the `N=4` record; **no guard re-homing occurred, deliberately** (re-homing is required only when PLAN-0076 archives, and T1 is only partially discharged). _[s159 closeout also left OPEN, deliberately: `scored_rule._KNOWN_CRITERIA` was NOT opened — zero extension pressure to date and its shape is `derive`-grammar-like, not vocabulary-like.]_ *(s157 #838 → s158 PR #840 → s159 closeout PR #841)*
- [ ] **AT-2 stale `N=2` / `N=3` signature counts — doc drift across three artifacts (surfaced s155).** _[s157 UPDATE: the deferral is now **CANCELLED**, so the drift is doubly stale — fold the corrections into the G1-gated edits the extraction PLAN will carry rather than fixing them piecemeal.]_ _[s158 UPDATE — **STILL OPEN, and the fold-in did NOT happen**: PLAN-0087's only Accepted-ADR edit was the ADR-0031 **D3 row-3** update its own AC-7 obligated (D4.4), scoped to a single table row. **ADR-0025 D7 and ADR-0032 still carry the stale counts**, and `spec.py`'s comments moved but were not audited for N-counts. So this item is unchanged in substance: it now needs its own small `plan-drafter` dispatch rather than a ride-along. Same reasoning as before — nothing turns RED on it, but every stale count is a wrong premise for the next AT-2 scoping call.]_ _[s159 CONFIRMED: PLAN-0087 **closed out + archived at 8/8 without carrying the fold-in**, so the ride-along option is now GONE — the item is confirmed to need its own small `plan-drafter` dispatch.]_ The pre-s157 live value was **`N=3`, with the ADR-0025 D7 generator marker RE-ARMING at `N=4`** (Cray-ratified at the s151 PLAN-0081 re-eval). Stale counts survive in: **(1)** `services/engine/procedures/spec.py` comments — **ungated, fix freely**; **(2) ADR-0025 D7** and **(3) ADR-0032** — both **G1-gated Accepted-body edits**, so they route via `plan-drafter`, never a direct Code write. Only `tests/services/engine/procedures/test_at2_signature_retrigger.py` carries the correct `_RETRIGGER_N = 4`, so the *test* is the source of truth and nothing turns RED on the prose drift. _[Irony worth preserving: **ADR-0032's own Positive-consequences section claims it makes exactly this stale-N-count error class harder to reintroduce** — and it now carries that very drift.]_ *(s155; blocks nothing, but every stale count is a wrong premise for the next AT-2 scoping call.)*
- [ ] **PLAN-0075 follow-ons — homed by PLAN-0076 (`Status: Tracking`, filed #752, s133): T1, the ADR-0031 D3 gate-plugin seam (F-FACTORY), is now **PARTIALLY discharged** — its criterion-vocabulary half shipped as PLAN-0087 (s158, PR #840; PLAN-0087 itself COMPLETE + archived s159, #841), its procedure-aware-`ExecutorFactory` half stays OPEN and owned here — **PLAN-0076 itself stays in active `docs/plans/`, its AC-6 guard ARMED, no re-homing**; Step T2's F-PIN remainder CLOSED s143 (#784, PLAN-0078 PR-5).** _[T2 closed ≠ F-PIN closed: **F-PIN itself stays OPEN** (`docs/plans/done/0078-transform-seed-migration.md` L-4 — PLAN-0078 closed s144 COMPLETE at 12/12 and archived, but **no artifact records F-PIN closed**) — only T2's remainder fold-in closed, so **PLAN-0076 does NOT archive** and its guard stays ARMED.]_ A guardrail against the ADR-0031 OQ-4 deferral-rot precedent (s133 4-specialist panel); PLAN-0075 itself is **COMPLETE — all 13 ACs — and CLOSED → `docs/plans/done/0075-*.md`**. Full detail: `docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` — F-FACTORY `:61-127`. **Guard:** PLAN-0076's AC-6 presence guard-test (`tests/services/engine/procedures/test_at2_followon_tracking_guard.py`) turns the build RED on a premature archive-to-`done/` or a pruned STATUS pointer ("location≠tripwire; failing tests are the real anti-rot"). *(PLAN-0075 = #749/#751 → `done/`; PLAN-0076 = #752, `Status: Tracking`; T2 closed by #784.)*
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2) — open ONLY for the O-2 residue; every other leg is DONE + archived.** **Closed:** Q3 ontology data-binding (PLAN-0046) · the Q4 generic query executor (PLAN-0048) · the Q4 join/projection grammar (ADR-016 Q4 amendment #659 + PLAN-0061) · the per-vertical seed migration (PLAN-0062) · the per-entity `threshold_field` band arc (PLAN-0066/0067/0068/0070) · **Box-4 BUILT (PLAN-0071, AC-5 GREEN at N=4) + SURFACED IN THE HERO UI (PLAN-0073)** — all → `docs/plans/done/`. **The one OPEN residue:** procurement's `intake` is declared-expressible ✔ under shadow parity, but **production execution stays the co-existing `_SeedQuery` ✖ for derived fields** — `docs/plans/done/0062-per-vertical-seed-migration.md:348`, the SD-C co-exist decision `:54-60`, `:291-295`. **Now homed by the transform arc:** **PLAN-0077** (transform grammar, COMPLETE → `done/0077-*.md`) + **PLAN-0078** (**COMPLETE at 12/12 ACs, CLOSED s144 #786 → `done/0078-*.md`** — the Step-7 closeout swept AC-5/AC-6 and archived it; do NOT re-open) — the fold-in is named at `docs/plans/0076-*.md:170-174`, what stays seed-side at `docs/plans/done/0078-transform-seed-migration.md:150-155`. *(s84 strategy discussion; the Box-4 leg is DONE — the residue is the O-2 data-binding leg only.)*
- [ ] **Bounded/incremental chain verification (PLAN-0063 SD-4 follow-up, s118).** `GET /audit/verify` walks the WHOLE chain O(n) on demand — accepted at pilot scale, documented in the endpoint docstring (`services/api/routers/audit.py:13-16`). Future work = a checkpointed head / verify-since-anchor design; anchor storage ≈ external anchoring — **do not build without re-reading the tripwire: `docs/plans/done/0063-audit-chain-verification-surface.md:564` + `services/api/routers/audit.py:19`.** _[Corrected s141: this item used to say "ADR-011 tripwire territory" — **ADR-011 does not exist** (`docs/adr/` jumps 0010 → 0012; it is an earmark only); the tripwire text lives at the two anchors above.]_ *(s118; #688/#690)*
- [ ] **DEFERRED: a monotonic `sequence` column on `step_results` — the ROOT fix for `load_run`'s wall-clock ordering.** Needs a DB migration → its own PLAN (PLAN-0062-independent); none drafted. `ORDER BY created_at` is **unchanged by design**, so **the deferral STANDS**; both surviving orderings are **DISPLAY-ONLY**, so not urgent. Full detail — ROOT-vs-guard, why it is tolerable, the static AST guard holding the line: the module docstring of `tests/services/db/test_load_run_ordering_guard.py`, pointed to from both code sites. *(rehomed s142; s117; #678/#680/#684)*
- [ ] **Rock 4 — s84 deep research DELIVERED → O-sequence locked.** Cray locked **O-1 → O-3 → O-2 → O-4**. **O-1** (Box-4 ฿ pitch) **DONE** · **O-3 = ADR-0025 Accepted** · **O-4 = PARK** (agent-interop; `docs/adr/0032-*.md:169` D4 — option-only, un-park = a counterparty's *written* pull). **Remaining: O-2 only** (economic-impact facet + Q3 data-binding = Rock 3). Full detail: `docs/adr/0025-at2-managerial-layer.md:19` (O-sequence + Box-3 fit) + `:23-29` (the **evidence-asymmetry** finding — bullish ROI all vendor-authored, independent mostly skeptical — rehomed s142). *(s84 Cray ask)*
- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten. **Full table (all six rows + their triggers + where each lands): `docs/plans/done/0005-oct-engine-runtime-layer.md:390` §8.1** — which itself instructs this STATUS entry to be a pointer. *(per Cray note 2026-05-21)*
- [ ] **Demo card UX — "trust shape", NO operator confidence badge (s74 design, Cray-approved).** The operator card shows **what / grounded-why / approve gate** + a "show full reasoning trace" toggle; **no confidence badge** (`confidence_signal` is engine-internal QA, trace-only), and the **(B) first-class `verification` field is NOT needed** — SD-3 settles at (a). Full record + rationale + the reconsider-trigger: **`docs/plans/done/0035-governed-action-verify-reshape-build.md:576`** — the s142 post-archival amendment ANSWERING SD-3's Phase-2 question; `ADR-0030` cites it. *(Trigger: the next demo / UI round.)*
- [ ] **PLAN-004 Phase C — OPTIONAL POLISH (forward-declared; "may never land"):** HTML/markdown handoff dashboard under `docs/` + references-graph (mermaid dispatch chains) + `render_transcript.py` unified session export (PLAN-0004 §"Phase C"). *(Phase A + B both COMPLETE — session 35; the prior TODO's validator **warning-swallow bug was FIXED #312**, s58. Minor never-formally-scoped sub-ideas — README/`_rename-map` walk-exclusion, Cat G `references_*` autofix, OQ-2 effective-vs-authored `status:` dashboard flag — fold in only if Phase C lands. Reconciled 2026-06-16 s65 audit.)*
- [ ] **Custom Postgres image with extensions (pgvector / AGE / pg_trgm) — needs a fresh ADR number + a PLAN; neither drafted.** *[Corrected s141: **PLAN-002 does not exist** ("NOT yet drafted", `docs/plans/done/0005-oct-engine-runtime-layer.md:14`), and the old "≥ ADR-014" floor is **moot** — ADRs now run to 0032 and `0014-WITHDRAWN.md` exists.]* Context: **`docs/adr/0013-autonomy-axis-relocation.md:285-289`** (the floor-bump note) + **`docs/plans/done/0005-*.md:403`** (trigger: semantic + graph features).
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] Extract `docs/conventions/git.md` from CLAUDE.md (low priority)
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)

## Next Steps

1. **PLAN-0005 §8.1 revisit register** — remaining deferred-foundational simplifications at their batch boundaries (audit framework, mapping layer, ORM emitter, base-Postgres → the custom-Postgres image, registry discovery). _[Corrected s153: dropped the stale "→ ADR-011+" and "→ PLAN-002 (≥ADR-014)" pointers — **ADR-011 does not exist** (earmark only, per the Active TODO above) and **PLAN-002 was never drafted** with its ADR floor moot; each item's corrected status lives in Active TODOs.]_
2. **Partner-trial readiness gaps** — `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` awaits a dedicated Cray discussion.
3. **Deferred (backlog)** — PLAN-004 Phase C only (optional polish: handoff dashboard / references-graph / unified export — Phase B complete s35, warning-swallow fixed #312); the custom Postgres image (needs a fresh ADR number + a PLAN — neither drafted; see the Active TODO for the corrected framing).
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
