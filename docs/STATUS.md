---
last_updated: 2026-07-31T15:24:24+07:00
session: 196
current_batch: "s196 — one PR (#1003): PLAN-0099 drafted + merged, the wall-clock root fix, root-caused by MEASUREMENT (a backward clock step), five SDs all Cray-ratified."
current_actor: code
blocked_on: "Nothing blocks. PLAN-0099 is merged with all five SDs ratified; 0 PRs open."
next_action: "PLAN-0099 Step 1 — write the frozen/stepping-clock forcing tests and capture each RED before touching production code. Note: a concurrent session is mid-build on PLAN-0098 (fleet View G)."
head_commit: 4846d5e
recent_commits: [4846d5e, 8e2b290, 88abb3f, 5382052, f936f00, b142fed, 4bb9494, 76d5e2a, f931b8b, 75a4822]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 196, 2026-07-31 (head_commit `a8912e0` → `4846d5e`) — one PR merged
> (#1003), 0 open. The theme: an intermittent flake root-caused by MEASUREMENT —
> which refuted the leading hypothesis and found two sites worse than the reported
> one.**
>
> **The failure.** `test_accepted_quote_endpoint.py::test_a_cheaper_quote_arriving_later_does_not_rewrite_history`
> failed once in three full-suite runs. **The leading hypothesis was refuted by
> construction:** Postgres `now()` / transaction-start is not involved — there is no
> `server_default` on any timestamp column; both stamps are Python
> `datetime.now(UTC)`, in separate requests and separate transactions. **Measured
> instead:** the dev box's clock steps **backwards 20x per 300 s, every step
> ≥ 400 ms** (worst −592 ms) against a vulnerable window of **90–166 ms** ⇒ **~0.9%
> flake per execution**, matching the observed 1-in-3. Reproduced deterministically
> three ways, incl. a frozen clock through the real HTTP path — which also exposed
> **POST and GET disagreeing about the same case** (`45500.50` vs `39000.00`).
>
> **`<=` → `<` was tried and REJECTED on evidence:** all 63 tests in the 6 touching
> files pass either way (a coverage gap in itself), and the swap fixes only the tie
> that cannot occur in production, does nothing for the inversion that does, and
> breaks the equal-stamp case. **Two further sites, both worse than the reported
> one:** `latest_accepted_quote` feeds the DOA gate via `governed_case_facts`, so a
> backward step reports the **superseded** acceptance (wrong ฿, wrong vendor, the
> operator's stated reason dropped); and `repair_spend_export.py:587`
> sorts-then-overwrites, so the month-end export can show a provisional gate outcome
> instead of its ratification.
>
> **The un-defer trigger did NOT literally fire** — both orderings it enumerates
> remain display-only, as s169 found. What failed is the safety-margin *argument*,
> whose enumeration was scoped by subsystem **and** by column vocabulary: the
> PLAN-0088 guard machinery flags **2** sites repo-wide on its current 3-name
> vocabulary (exactly the pair the docstring named) and **12** once the repair-case
> column names are added. Classified **`superseded by new info`** per `CLAUDE.md`
> §6, not "was an error".
>
> **PLAN-0099 merged (#1003), five SDs all Cray-ratified:** SD-1 store-at-write
> (eliminate the re-derivation); SD-2 backfill marks the value **reconstructed**,
> not recorded (a third option neither drafted alternative offered); SD-3 (a)
> `latest_closeout` (b) `justifications[-1]` (c) `repair_spend_export.py:587` all
> ride migration `0023`; SD-4 retain the positional-read rule, rewritten rationale.
> **No production code changed** — execution starts at Step 1 (forcing tests, RED
> first). Numbered 0099 because a concurrent session claimed 0098 (#1001)
> mid-flight. Full detail: `docs/plans/0099-wall-clock-root-fix-store-at-write-and-sequence.md`.

> **Session 195, 2026-07-31 (head_commit `b25cc98` → `a8912e0`) — four PRs merged
> (#994–#997), 0 open. The theme: a documented claim that measurement refuted, four
> times in four places.**
>
> **#994 — fleet's Box-4 ฿ facet, the last config-shaped half of ADR-0032 D1.** Fifth
> economic producer, first **event-anchored** one: procurement's OQ-C fell back to a hero
> PO (its events carry a criticality score, not a ฿ anchor), but a fleet repair-quote
> event *is* the money (`measured_value`, `unit == "THB"`) — baseline = an uncompared
> price, governed = the same repair after the three-vendor comparison the partner adopted
> after being defrauded on parts. **Cray typed the basis** (event-anchored + the
> partner's own ฿30,000 threshold, over an assumptions-first exemplar and a DB read empty
> at `row_count: 0`) **and the 15% recovery fraction** over a fraud-sized 25%. The
> threshold is **imported from `sourcing.py`**, so producer and gate cannot drift; no ADR
> amendment needed (ADR-0030 D3 leaves `kind` a free `str`). `test_golden_e2e`'s donor
> oracle fired as designed; the exclusion is **surgical**.
>
> **#995 — a REAL production defect, not a hardening.** `decide_pm_import` read a row's
> status then wrote it on an **unlocked** read, so two deciders could both observe
> `proposed`, both pass the 409 guard, and the later commit would overwrite the earlier
> decision — stamping the loser's `decided_by` on a row someone else had ruled on,
> **while both callers got a 200**. The guard's own "idempotent BY STATE" comment was
> true for a *replay*, false for a *race*. Fixed with `FOR UPDATE` on the decide path's
> read only (the review GET must not lock), no migration — Code's call over a version
> column, veto open.
>
> **#996 / #997 — PLAN-0097 built and CLOSED (7/7 ACs, archived).** The warn arm was the
> only terminal outcome in `_goal_gate.py` that wrote nothing; it now records before it
> pings. Load-bearing is what the entry is **invisible to**: `_last_decision_evaluation`
> excludes warn entries from every decision read, or two untested corners change
> behaviour (flake would skip a dispatch; enforce-flip would double-block). **Cray typed
> SD-2 = yes** (first-class `Evaluation.detail`) **and SD-3 = dedup** (marker + same
> non-empty fingerprint; empty always records).
>
> **The theme, four times.** The allocator docstring named the wrong constraint; AC-6
> predicted M6 would redden the ladder tests and it does not, so the enforce fence was an
> **untested** property M6 would have passed silently; the s194 RR-3 estimate was
> over-scoped; and **two of eight mutation probes were themselves defective** — one
> mutated the wrong site (its anchor recurs earlier), the other was a deletion wearing
> another probe's label. Both showed **GREEN as vacuous oracles**. Also measured: a
> two-session DB race test fails by **hanging**, not reddening, unless the parked task is
> unwound in a `finally` and bounded with Postgres `lock_timeout`.
>
> Suite **3656 → 3676** / 8 skipped, re-run per merge commit, `git diff <ci-head> HEAD` =
> 0 bytes ×4. ruff + format clean over 576 files, `mypy --strict services/` clean over
> 130; guard + R1/R4/R7/R8 exit 0; `alembic check` clean, dev DB at `0022`; CI `gate` ×4.
> **21 non-vacuity probes**, each RED against its named test, restored from `/tmp`.

> **Session 194, 2026-07-30 (head_commit `367c15b` → `b25cc98`) — two rotted-pointer
> repairs landed, and Cray ruled the standing STATUS-size TODO.** Two PRs merged
> (#990, #991), 0 open.
>
> **#990 — ADR-0025's archive pointer was wrong by whole FILE, not by offset.** It cited
> a line range in `docs/status-archive/2026-h1-status.md`; that base was **re-chartered**
> at the s144 split as the rolling recent window, so the target had long since migrated
> to a lettered sibling. Repaired by citing `2026-h1c-status.md` **by section heading,
> with no line numbers** — § "Current-Focus block — Session 84 (cont.; head_commit
> `f56a6e8`)" — per the house rule that headings survive an edit and line numbers do not.
> **Pre-existing rot from s144**, whose repair sweep fixed three pointers of this shape
> and missed one; **not** caused by the s193 R4 split, which preserved every heading.
> N=1 — no sibling rot in `docs/adr/`. Drafted by `plan-drafter` (ADR-0025 is Accepted →
> G1-denied to Code), Code R2'd.
>
> **#991 — PLAN-0097 drafted (`Status: Draft`), and the finding is that the standing
> TODO's PREMISE was wrong.** That TODO read the goal gate's silent warn path as
> *ratified behaviour*, which made any fix an ADR-0018 amendment question. It is not:
> **D5** says verbatim *"v1 is warn + annotate … records the verdict trail in the goal
> file"*, and **V2-D1** (ratified 2026-07-13, with the warn path already built)
> re-describes the default tier as *"warn + annotate + Telegram"*. The spec's step 5
> omits the record and the implementation followed the sketch — so the silence is an
> **implementation gap against a ratified Decision, not a ratified design**. **Third
> instance of this class** (ADR-0034 D3(3) vs D3(6) at s186; D3(3)/D3(4) at s188): a
> Decision's prose and its own procedural sketch disagreeing, code following the sketch.
>
> **Cray typed three calls.** (1) **PLAN-0097 SD-1 = (a): D5 controls** — the trail entry
> is licensed by ADR-0018 as it stands, no amendment needed; recorded at the PLAN's SD-1
> and as a discharged gate at Step 0, with Appendix A's contingency amendment retained
> but marked NOT applied / superseded, and `docs/adr/0018-*.md` untouched. **SD-2 and
> SD-3 were NOT ruled and stay OPEN.** (2) **STATUS size = tighten the per-block cap +
> cut duplicated content**, declining both "widen the rotation window" and "accept the
> trade". (3) **Next build ordering #3 → #1** — the fleet demo showability work
> (surfacing the month-end KPI + export in the console UI) goes first.
>
> **Ruling (2) is applied in this same reconcile.** STATUS measured **59,820 B** against
> R1's 49,152 B soft target. Runbook §R2 gained a **per-Current-Focus-block cap of
> ≤ 4,096 B** — the count caps bounded how *many* blocks, never how *large* one may be —
> and its existing "RD rows are pointers, ≤ ~600 chars" rule was measured **unenforced**,
> 8 of 10 rows over, worst 2,660 B. This pass rewrites every RD row to that cap, brings
> each retained block under the new cap, and cuts the PLAN-0096 In-Flight entry to a
> pointer. **The R2 carve-out bound the work**: nothing was trimmed until its substance
> was verified present in a tracked file.

> **Session 193, 2026-07-30 (head_commit `5dd8ce6` → `367c15b`) — the session the
> month-end export went from zero lines to a downloadable file with a KPI that can
> fail.** Six PRs merged (#982–#987), 0 open. PLAN-0096 **Step 8 item 5 COMPLETE**;
> **Step 10's AC-12 evidence written** — four coverage matrices, seven named residual
> risks, a confidence statement, in `.claude/handoffs/session-193/` (gitignored).
>
> **The build, in five PRs.** #982 the reader, whose row set is a UNION: cases with a
> `gate_decision` in the month, filed on the APPROVAL date, **∪** close-outs in the
> month with no governed run at all, filed on `entered_at`. That second source is the
> whole point — a naive export reports 100% traceability *by construction*, because the
> rows it cannot explain are the rows it never selected. #983 the KPI + cover: **Cray
> typed rule (ค)** — a row counts only if it was governed AND fully documented;
> governance-only would score a perfectly-approved repair with no invoice at 100%,
> paperwork-only would score escaped money as traceable the moment a tidy invoice was
> keyed. `vat_thb` and `cost_center` are deliberately NOT required — a garage that is
> not VAT-registered; and requiring the unfilled `cost_center` would pin the KPI at 0%
> forever. #984 **Cray typed (ก)**: persist `three_quote_basis` (alembic `0022`) rather
> than recompute it — recomputing would answer last month's audit question with this
> month's threshold *while looking completely filled in*. #985 the CSV + router, the
> repo's **first** export surface, UTF-8 **with BOM** because Excel on Windows mojibakes
> Thai without one. #986 the E-2 exception report on the cover.
>
> **Two defects were found by ORACLES, not by review — the useful half.** A probe
> mutating `is_fully_traceable` so its governed/outcome guard never fires left the suite
> **GREEN**: the guard was unreachable through `load_monthly_export`, which already
> nulls the approver when there is no decision, so nothing tested it on its own terms;
> four direct predicate tests now do. And the **end-to-end scenario found a real bug** —
> the hero round decides the demo fixture cases alongside the real one, and rejecting
> them produced link rows with no approver, invoice or amounts, landing in the export as
> **฿0 Express entries** an accountant would have to key to record that nothing
> happened. No unit test could have shown it; every fixture built exactly the rows its
> author had in mind. `is_reportable` now states the rule: money exists → always a row
> (a REJECTED case *with* a close-out is the worst case in the report);
> authorised-but-unpaid → a row; neither → not spend.
>
> **28 non-vacuity probes**, each restored from a backup copy and diff-verified. Two did
> not redden and were treated as findings rather than passes: one exposed the untested
> guard above, the other that **a probe whose mutation is a semantic no-op measures
> nothing while reading as a pass**. AC-9's bar is demonstrated on the real path, not
> asserted (archived PLAN, §Acceptance Criteria).
>
> **Also:** #987 corrected a **public-repo** overclaim — README and
> `docs/conventions/tech-stack.md` described pgvector + Apache AGE + pg_trgm as the
> database when `docker-compose.yml` runs stock `postgres:16-alpine`. STATUS had carried
> the corrected framing since s141 and never propagated it to the two files a *reader*
> hits first; two dead pointers fell out of the same pass. Suite **3607 → 3646**; `mypy
> --strict services/` 127 → **130**; dev DB `0021` → **`0022`** on Cray's go against five
> criteria fixed before the run. MS-S1 never touched; LINE still disarmed. **R2/R4
> rotation applied** — s186→187 block + s179 RD row out; the archive base spilled
> sessions-142→171 into the new `2026-h1g-status.md` (numbers in the chain note below).

> _Older content rotates out of this file per the **STATUS.md Rotation Policy (R1-R8)** in [`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md) (Lesson #23): Current Focus keeps the 4 newest sessions (<=8 blocks); Recent Decisions keeps the last 10 rows. Rotated blocks/rows live in [`docs/status-archive/`](status-archive/) and git history (Tier 3). Layout — **two separate chains, both with letters ascending with time and the base holding the recent window**: the rotation archive `2026-h1b` → `c` → `d` → `e` → `f` → `g` → `2026-h1-status.md`, and the Current-Focus-only `2026-h1b` → `c` → `2026-h1-current-focus.md`. Rotations append to the two bases. **Grep the directory, not a filename** — the chain is one corpus and which file holds a given block is an artifact of where the ~192 KB R4 bar happened to fall. _[Chain created 2026-07-17 (s144): the single `2026-h1-status.md` had reached 592,577 B, 2.3x R4's cap, and the new guard (#789) forced the split. `g` added 2026-07-30 (s193): the base had returned to 194,232 B with a ~10.7 KB block due to rotate in, so sessions-142→171 spilled and the base dropped to 46,215 B.]_

## Prior focus (archived)

PLAN-003, PLAN-0005, PLAN-0006, PLAN-0007 and PLAN-0008 are all merged
and archived to `docs/plans/done/`; the Cowork-as-Tier-1 trial concluded
and was ratified permanently by **ADR-009** (Cowork = merged Tier 0 +
Tier 1 workspace; commits stay Code-exclusive). Full detail lives in
`docs/plans/done/`, the Recent Decisions table below, and git history.
_[Corrected s169, `was an error`: this paragraph claimed PLAN-004's
"Phase B/C remain deferred", which both the Next Steps section and the
Active TODO refute — **Phase A + B are COMPLETE (s35)** and only the
optional Phase C polish is deferred. The stale sentence is dropped rather
than restated: the Active TODO owns that status.]_

## Recent Decisions (last 10)

| Date | Decision | Reference |
|------|----------|-----------|
| 2026-07-31 | **s196 — PLAN-0099 drafted + merged (#1003): the wall-clock root fix.** An intermittent quote-history flake was **measured**, not inferred — the dev clock steps back 20x/300 s (every step ≥400 ms) against a 90–166 ms window ⇒ ~0.9%/run; the Postgres-`now()` hypothesis was **refuted by construction**. **`<=` → `<` rejected on evidence.** Two worse sites found (the DOA gate via `latest_accepted_quote`; the month-end export). **All 5 SDs Cray-ratified** — store-at-write, backfill marked **reconstructed**, three riders on migration `0023`. No production code changed | `4846d5e` (head_commit) / `docs/plans/0099-wall-clock-root-fix-store-at-write-and-sequence.md` |
| 2026-07-31 | **s195 — fleet's Box-4 ฿ facet, a REAL PM-confirm race, PLAN-0097 COMPLETE (#994–#997).** **Cray typed** fleet's **event-anchored** ฿30,000 basis + the conservative **15%** recovery fraction. #995 fixed an **unlocked** read-then-write that let two deciders both get a 200 while one overwrote the other (`FOR UPDATE`, no migration). #996/#997 shipped the warn-path trail and archived the PLAN — **SD-2 = yes**, **SD-3 = dedup**. Suite → **3676** | `a8912e0` (#997, head_commit) / `8381c92` (#994) / `fa53911` (#995) / `docs/plans/done/0097-goal-gate-warn-path-trail.md` |
| 2026-07-30 | **s194 — two rotted-pointer repairs + Cray's STATUS-size ruling (#990, #991).** #990 fixed ADR-0025's archive pointer (wrong by whole FILE since the s144 re-charter; now cited by section heading, no line numbers). #991 drafted PLAN-0097 — the goal gate's silent warn path is an **implementation gap against ADR-0018 D5/V2-D1**, not ratified design. **Cray typed: SD-1 = (a), D5 controls (SD-2/SD-3 stay OPEN)**; **STATUS size = tighten the per-block cap + cut duplicates** | `b25cc98` (head_commit) / `c2584c8` (#990) / `docs/plans/done/0097-goal-gate-warn-path-trail.md` / runbook §R2 |
| 2026-07-30 | **s193 — PLAN-0096 Step 8 item 5 COMPLETE (#982–#986): the month-end export end to end, with a KPI that can fail.** Row set = governed ∪ escaped money (a naive export reports 100% by construction). **Cray typed (ค)** traceable = governed AND documented; **(ก)** persist `three_quote_basis` (alembic `0022`). Two defects found by ORACLES, not review. Suite 3607 → **3646** | `367c15b` (#987 merge, head_commit) / `367a08e` (#986) / `ed09502` (#982) / `docs/plans/done/0096-fleet-flow-completion-phase1.md` |
| 2026-07-30 | **s192 — PLAN-0096 Step 8 item 3 COMPLETE (#979): the case → run link, proven on BOTH gate drivers.** The hook read `output_set`, so a rejected case was invisible (fix: `decided_entries()` reads `decisions`); `_outcome` let the run state outrank a refusal. **Cray typed: a refusal is checked FIRST.** Five non-vacuity probes, all RED as predicted. Suite → **3604** | `5dd8ce6` (#979, head_commit) / `docs/plans/done/0096-fleet-flow-completion-phase1.md` §Step 8 |
| 2026-07-30 | **s191 — a REAL repair case now reaches the governed gate (#975–#977).** The accepted quote (ใบที่ตกลง, alembic `0019`) gives the DoA ladder a ฿ figure existing BEFORE the work and tracing to recorded evidence; Cray typed the required FK + reason-only-when-not-cheapest. The case → event path wires it in with **zero engine and zero adapter-`__init__` diff**. One probe came back GREEN — a vacuous oracle a fail-soft handler was hiding. Suite → **3597** | `99b752f` (#977, head_commit) / `d3f2919` (#976) / `d781683` (#975) / `docs/plans/done/0096-fleet-flow-completion-phase1.md` §Step 8 |
| 2026-07-29 | **s189 — PLAN-0096 Steps 1–7 and 9 COMPLETE (8 of 10), #965–#968.** Partner round-2 answers closed 5 of 7 questions. Step 6 = the partner's real 8-step task chain (alembic `0016`); `pm_due` = a sixth LINE event, group recipient, read off persisted `judge_service_due` verdicts. Cray typed the prerequisite-anchored clock + the AC-8 bump. Unplanned (#966/#967): an ORM↔alembic registration guard — **a comparison means something only when at most ONE side is hand-maintained**. Suite → **3552** | `13aa2f0` (#968 merge, head_commit) / `26e61b3` (#965) / `docs/plans/done/0096-fleet-flow-completion-phase1.md` |
| 2026-07-29 | **s186→s187 — PLAN-0096 Steps 1–5, 7 and 9 COMPLETE (#951–#961); s188 closed the ADR debt (#962).** Six Cray ratifications, incl. the state-based ratify precondition on a **self-contradiction between ADR-0034 D3(3) and D3(6)** — and a second divergence of the same class found at s188 R2. Suite → **3502** | `eae0f82` (#962 merge, head_commit) / `728da00` (#961 merge) / `docs/plans/done/0096-fleet-flow-completion-phase1.md` / `docs/adr/0034-governed-exception-family.md` §D3 + §"D3 Amendment (2026-07-29)" |
| 2026-07-28 | **s184→s185 — ADR-0034 "governed exception family" ACCEPTED (#948) + PLAN-0096 "fleet flow completion Phase 1, Lean KPI-first" merged as Draft (#949).** Partner-driven: 18/18 discovery answers → three mechanisms (escalate-never-skip waiver / evidence-alternative E-3 / deferred-ratification E-2+E-4); SoD + compliance stay NON-waivable. Cray resolved OQ-1/OQ-2/OQ-3 per the in-file recommendations. All 8 dispatch rejection criteria run adversarially, none fired | `760ceed` (#949 merge, head_commit) / `24c3b45` (#948) / `docs/adr/0034-governed-exception-family.md` |
| 2026-07-28 | **s183 — PLAN-0094 ARCHIVED (Cray released the live-loop soak), and the goal-gate `evaluations: 0` finding DIAGNOSED: the gate is not broken, its warn path is unobservable.** OQ-4 re-homed to an Active TODO rather than buried in `done/`. _[s194: this row's "the behaviour is ratified" reading was REFUTED — see PLAN-0097.]_ | `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md` §Step 6 + §OQ-4 / `docs/plans/done/0097-goal-gate-warn-path-trail.md` §"The ADR-0018 determination" |

## In-Flight Discussions

- **PLAN-0096 — COMPLETE 12/12 and ARCHIVED (s193).** The fleet design partner's Phase-1 flow, shipped end to end across s186→s193 — real governance numbers, case capture from minute 1, the quote evidence pack, the sourcing signal that retired a fail-open default, the E-2 ratification window, the PM import, the outbound-only-and-DISARMED LINE OA surface, the 8-step task chain, and the month-end Express export. **Four residual risks outlive the PLAN and are why this entry is not simply deleted — all four are recorded in the archived PLAN, which is where the detail now lives:** RR-1 (per-baht approver→case attribution is INFERENCE, not data — `GovernedDecision` carries no timestamp and no per-entity key; sound while one human resolves a whole gate, silently wrong the day two approvers share a resolution); RR-3 (concurrency-race was the weakest coverage row for AC-4/AC-9/AC-10 — **both named gaps CLOSED s195 by #995**: the PM-confirm race turned out to be a REAL defect, now `FOR UPDATE`, and `allocate_repair_order_no` got the test its docstring implied, which corrected the constraint that docstring named); ศูนย์ต้นทุน ships EMPTY (partner granularity still unanswered — also an open Active TODO below); and `latest_per` still collapsing two open cases on one truck (item 4, **Cray typed (ค) defer**) — the older case never reaches the gate, so if it is paid it reports as *ungoverned*, which a reader of the number cannot distinguish from a governance failure. Full record: `docs/plans/done/0096-fleet-flow-completion-phase1.md` (§Verification preamble + §Acceptance Criteria for RR-1 / RR-3 / ศูนย์ต้นทุน; §Step 8 for `latest_per`); the AC-12 sign-off is in `.claude/handoffs/session-193/` (gitignored).
- **PLAN-0095 — COMPLETE 7/7 and ARCHIVED (s177, #927/#928).** The scaffold-era `Dockerfile` builds and boots the DB-less synthetic OCT demo: `/health` 200 in ~2 s, all six verticals discovered, `uid=999(vero)`, `HEALTHCHECK` healthy, and `alembic current` → `0012 (head)` from inside the image. The only thing still open from it is **OQ-1, the hosting model** — already homed in the next bullet, not restated here. Full record: `docs/plans/done/0095-docker-image-boot.md`. _[Corrected s182, `was an error`: this entry still described the PLAN as Draft with "Steps 1–5 UNEXECUTED … the image does not boot today" and cited the pre-archive path — refuted by the s177 row in Recent Decisions above and by the archived PLAN's own `Status: Complete`.]_
- **Hosting model → ADR-002's LAN trust boundary: a LIVE candidate needing its own ADR (surfaced s176, still not drafted; this is where PLAN-0095's OQ-1 lives).** *"Customer uses our server"* touches ADR-002's LAN trust model — `docs/adr/0002-network-topology.md` defers its own successor **twice** as an unnumbered `ADR-NN`: in **§Consequences → Neutral** (the LAN trust assumption is to be re-evaluated when a first design partner deploys to a real site) and in **§Alternatives Considered → Alternative 3** (Tailscale / WireGuard, to be reconsidered when remote development or design-partner site connectivity becomes a need). Nothing in the image or the compose service selects *where* the image runs, so the question only bites when a hosting model is actually chosen. Route: a new ADR via the Cowork/plan-drafter path (G1/G2 — Code may not author it). _[s182: the two line-number citations here were **dropped, not corrected** — one of them had already rotted onto a PDPA bullet, which is the failure mode the rotation policy's R7 rule names. Cite the ADR's section headings; they survive an edit, line numbers do not.]_
- **PLAN-0094 — COMPLETE (all 11 ACs closed or withdrawn) and ARCHIVED (s183).** The L1 loop-detect restructure: count non-progress instead of touches (P1), warn at `T` and deny at `T+G` (P2, `G=3` → 9 code / 18 doc), add an acknowledged-pause exit the agent cannot fake (P3), and wire the `SubagentStop` reset that had **never been live**, scoped per-`agent_id` so a zero-edit spawn cannot launder the main agent's budget (F3c). Built across s174 #917, s175 #922, s177 #930, s180 #937/#939, closed out s182 #943 on a **full fresh 18/18 non-vacuity sweep**. Archived at s183 once **Cray released the live-loop soak** (no anomalies) — the one gate no session could self-serve. **The one thing that did NOT archive with it: `OQ-4` (should L1 exist at all?) is OPEN and dated — re-homed to an Active TODO below**, per the PLAN's own §Step 6 instruction never to bury it in `done/`. Full record: `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md`; the anti-pattern behind it: `docs/lessons/0033-raising-the-threshold-is-not-fixing-the-unit.md`.
- **PLAN-0093 — COMPLETE 8/8 and ARCHIVED (s172, #913).** The LLM-arm degrade disclosure — no silent arm swap: which arm phrased an NL answer is disclosed, the rule fail-safe says it is a fail-safe, the authoring arm is projected over HTTP (including the insights run-corpus path), and `LLM_RETRY_BUDGET` no longer sits inert on the governed path. No follow-on owed. Full record: `docs/plans/done/0093-llm-arm-degrade-disclosure.md`.
- **PLAN-0091 — COMPLETE 10/10 and ARCHIVED (s168).** Two follow-ons it named, **neither scheduled**: the **extend shapes** (calm-path + scheduled-variant scaffolding) are **greenfield, not an extension** — the shipped emitters refuse an existing vertical *by construction* and create-only is Cray-ratified SD-2, so this needs a fresh seam spec, not effort; and the census-narrative comment in `tests/api/test_procedures_endpoint.py` is the one counted site the disposer REPORTS rather than rewrites — a human call, left visible on purpose. Full record: `docs/plans/done/0091-narrative-to-vertical-scaffolder-tool.md`.
- **PLAN-0088 — COMPLETE (13/13 live ACs) and ARCHIVED (s171, #908).** The cross-run read substrate + the four run-insight readers (A2 ฿ ROI, A3 flow, A4 audit-readiness, A1 NL-over-runs) + the Group-B carrier proof. SD-1…SD-9 all Cray-ratified; the substrate stays aggregate-only (SD-8 a) and grows only in `run_analytics.py` (SD-9 a2); Group A ungated, Group B pilot-gated (AC-10 proves the questions expressible, AC-11 that no proposal machinery exists). AC-9b's live MS-S1 smoke PASSED. **Three AC-WORDING debts carried into the archived PLAN, none a code defect** (Cray's to reword if ever): (1) AC-2 names the wrong approver source — the approver is in the trace / `governed_decision` / audit-log, not `step_principals` (the requester half); (2) AC-6's "dwell" is a same-row start→suspension span, stated plainly in the code; (3) SD-9's aside miscalls `trigger` "undefined". Full record: `docs/plans/done/0088-cross-run-read-substrate-and-run-insight-readers.md`.
- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13; verdict **continue-with-adjustments**. Runs 1 (energy, s93) + 2 (supply-chain, s94) both COMPLETE, all S-checks PASS against pre-committed oracles, no R-PS trigger fired; C-1..C-3 CONFIRMED → **no open partner-sim debt**. ADR-011's audit stays gated on a REAL partner conversation (R3: SYNTHETIC provenance INFORMS but never TRIGGERS it). Full record: `docs/adr/0020-*.md` + the gitignored run packages under `docs/research/private/`.
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **Procurement vertical — GO + SHIPPED (PLAN-0036 Fastenal, Stage 1):** 4th vertical greenlit (s75); **PLAN-0036 is `Status: Done` — Stage 1 complete 2026-06-25 (s76), all 8 Steps executed, AC-1…AC-15 satisfied offline — and Stage 2 (the facet retrofit it forward-declared) shipped as PLAN-0037.** Demo target = Fastenal Thailand; **hero** = asset-failure → governed emergency sourcing, **calm-path** = low-stock reorder. Stage 1 = a PLAN-only pure-config plugin on the ADR-016 engine (zero `services/` core edit; CQ-1 / ADR-0023). **Pitch** = asset-ontology-triggered governed sourcing (ADR-008 + ADR-016), NOT the commoditized "governed"/"cross-vertical" claims. Full record: `docs/plans/done/0036-fastenal-procurement-vertical.md` + `done/0037-stage2-facet-retrofit-archetype-catalog.md` + the s72 de-risk dossier under `docs/research/private/`. _[Corrected s183, `was an error`: this entry pointed at the pre-archive path `docs/plans/0036-*.md` and described the PLAN as "merged Draft" long after it reached `done/` with `Status: Done` — the same stale-pointer class the s182 corrections were chasing.]_
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm — **not yet drafted**, and it needs a fresh ADR number. _[The old "≥ ADR-014" floor recorded here was **moot** — see the Active TODO below, corrected s141: ADRs now run past 0032 and `0014-WITHDRAWN.md` exists. Kept as one pointer rather than two divergent copies.]_
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **The autonomy fork — Stop-hook misfires: CLOSED s167.** Resolved by **option A′** (Cray, typed) and shipped the same session — the `dispatch` verdict is a **suggestion, not an order** (#870/#871). Final ledger: **14 misfires / 0 valid fires**. **The whole argument is settled history in `docs/plans/done/0092-stop-hook-dispatch-arm-demotion-to-suggestion.md` — do not restate it here.** Live remainder: only **option (e)** (flip the classifier backend from local Ollama `gpt-oss:20b` to Sonnet), **deferred**, its API-key/org fail-closed probe unrun.

## Active TODOs

- [ ] **Seam-scoped mutation-testing CI — a PLAN candidate, NOT built.** Surfaced s188 as the one CHECKABLE variant the scenario-test hook rejection does not cover; **rehomed here s191** when its parent `[x]` row was pruned, because STATUS was its only home. A CI job that requires the scenario suite to REDDEN under a seam mutation: ritual compliance cannot fake it, since an empty or stubbed scenario suite stays green under mutation — exactly what a file-existence hook would miss. Rationale: `CLAUDE.md` §8's scenario-test bullet.
- [ ] **PLAN-0096 partner round-2 — ANSWERED s189; five of seven closed, one non-blocking follow-up open.** A1 → Step 6 built (#965); A3 → `pm_due` built (#968); **A4 + A7 confirmed values already shipped** (flat ฿5,000 ceiling, `"30001"` inclusive floors); A5 **parked** — no real Wialon export exists yet. **A2 is answered and consumed by Step 8** (no longer a gate). **Open, NON-blocking: cost-center (ศูนย์ต้นทุน) granularity — per truck or per company?** Ship the column, fill the rule when it lands. A6 is answered but is a Step 9 *runbook* item. Detail: `docs/plans/done/0096-fleet-flow-completion-phase1.md`.
- [ ] **The AT-2 extraction — only the F-FACTORY half remains, owned by PLAN-0076 T1.** The criterion-vocabulary half SHIPPED as PLAN-0087 (COMPLETE 8/8, ARCHIVED — #840/#841); ADR-0025 D7's generator deferral was CANCELLED at N=4 (Cray-ratified, typed); SD-1 = (a) keeps the procedure-aware `ExecutorFactory` half with PLAN-0076 T1, guard `test_at2_extraction_obligation_is_owned` ARMED. Full detail: `docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` + `docs/plans/0076-*.md` §A.
- [ ] **PLAN-0075 follow-ons — homed by PLAN-0076 (`Status: Tracking`, #752, s133).** T1 (ADR-0031 D3 gate-plugin seam, F-FACTORY) is PARTIALLY discharged — the criterion-vocabulary half shipped as PLAN-0087; the procedure-aware-`ExecutorFactory` half stays OPEN here. T2's F-PIN remainder CLOSED s143 (#784), but **F-PIN itself stays OPEN**, so PLAN-0076 does NOT archive and its AC-6 presence guard stays ARMED. Full detail: `docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` §A.
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2) — open ONLY for the O-2 residue.** Every other leg is DONE + archived (PLAN-0046/0048/0061/0062/0066–0068/0070/0071/0073 → `done/`). **The one OPEN residue:** procurement's `intake` migrated only **PARTIALLY** — the derived fields ALREADY moved to declared `transform` ✔ (PLAN-0078 PR-1 #762, AC-2 ticked), so what is left is **only the cardinality-changing `candidate_quotes` nest**, which is explicitly Out-of-Scope there. *[Corrected s175 by the #921 grounding sweep, `was an error`: this entry said production execution stays `_SeedQuery` "for derived fields" — it does not; the derived fields are migrated and the reshape is the sole residue.]* Full detail: `docs/plans/done/0062-per-vertical-seed-migration.md` §SD-C (the co-exist decision + its STOP-and-surface tripwire) + `done/0078-*.md` §L-3 and its Out-of-Scope, where the residue is walled in.
- [ ] **Bounded/incremental chain verification (PLAN-0063 SD-4 follow-up, s118).** `GET /audit/verify` walks the WHOLE chain O(n) on demand — accepted at pilot scale. Future work = a checkpointed head / verify-since-anchor design; anchor storage ≈ external anchoring — **do not build without re-reading the tripwire** in `docs/plans/done/0063-audit-chain-verification-surface.md` + the `services/api/routers/audit.py` module docstring (SD-4). _[Note: the docstring's "ADR-011 boundary" is an EARMARK — `docs/adr/` jumps 0010 → 0012.]_ *(#688/#690)*
- [ ] **DEFERRED: a monotonic `sequence` column on `step_results` — the ROOT fix for `load_run`'s wall-clock ordering.** Needs a DB migration → its own PLAN; none drafted, the deferral STANDS, both surviving orderings DISPLAY-ONLY. Full detail (ROOT-vs-guard, the AST guard, the un-defer trigger): the docstring of `tests/services/db/test_load_run_ordering_guard.py`. _[s169: the un-defer trigger got its FIRST real-case reading and did NOT fire — SD-8 = (a) ELIMINATE. This PLAN now also owns newest-first `/runs` pagination; `view-map.js` (a `CAP = 5` truncating consumer) is a second dependant.]_ _[s196: **PLAN-0099 is DRAFTED and MERGED (#1003)** and now owns this fix — root-caused by a MEASURED backward clock step, not by the wall-clock tie this row anticipated. **The deferral text above is left INTACT on purpose:** PLAN-0099 **Step 5** owns rewriting it, gated on Cray ratifying the exact wording. `docs/plans/0099-wall-clock-root-fix-store-at-write-and-sequence.md`.]_
- [ ] **Rock 4 — s84 deep research DELIVERED → O-sequence locked.** Cray locked **O-1 → O-3 → O-2 → O-4**. **O-1** (Box-4 ฿ pitch) **DONE** · **O-3 = ADR-0025 Accepted** · **O-4 = PARK** (agent-interop; `docs/adr/0032-*.md` D4 — option-only, un-park = a counterparty's *written* pull). **Remaining: O-2 only** (economic-impact facet + Q3 data-binding = Rock 3). Full detail: `docs/adr/0025-at2-managerial-layer.md` (O-sequence + Box-3 fit + the **evidence-asymmetry** finding rehomed s142). *(s84 Cray ask)*
- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten. **Full table (all six rows + their triggers + where each lands): `docs/plans/done/0005-oct-engine-runtime-layer.md` §8.1** — which itself instructs this STATUS entry to be a pointer. *(per Cray note 2026-05-21)*
- [ ] **PLAN-004 Phase C — OPTIONAL POLISH (forward-declared; "may never land"):** HTML/markdown handoff dashboard under `docs/` + references-graph (mermaid dispatch chains) + `render_transcript.py` unified session export (PLAN-0004 §"Phase C"). *(Phase A + B both COMPLETE — session 35; the prior TODO's validator **warning-swallow bug was FIXED #312**, s58. Minor never-formally-scoped sub-ideas — README/`_rename-map` walk-exclusion, Cat G `references_*` autofix, OQ-2 effective-vs-authored `status:` dashboard flag — fold in only if Phase C lands. Reconciled 2026-06-16 s65 audit.)*
- [ ] **Custom Postgres image with extensions (pgvector / AGE / pg_trgm) — needs a fresh ADR number + a PLAN; neither drafted.** *[Corrected s141: **PLAN-002 does not exist** ("NOT yet drafted", `docs/plans/done/0005-oct-engine-runtime-layer.md`), and the old "≥ ADR-014" floor is **moot** — ADRs now run to 0032 and `0014-WITHDRAWN.md` exists.]* Context: **`docs/adr/0013-autonomy-axis-relocation.md`** (the floor-bump note) + **`docs/plans/done/0005-*.md`** (trigger: semantic + graph features).
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] **CLAUDE.md follow-up extraction pass (s181 option b): new Cowork dispatch; target < 20 KB (~18 KB / ~225–235 line floor).** Candidates (Cowork fresh-eyes, s181 completion §6): §11 ¶3 restates the §6 E2 rule → one-line pointer; §10 skills-row annotation duplicates §4's Tier-2.6 row (in-file ADR-0017 D6 drift); §10 docs/logs row's PLAN-004 parenthetical; §9 halves; §3 folds into §1. Materials: `.claude/handoffs/session-181/` (gitignored). **PARKED s183 by Cray — the dispatch stays UNSENT until two things are settled, and s183 grounded both.** (1) **The unit of `< 20 KB` is load-bearing and unpinned:** `CLAUDE.md` measures **21,524 B / 261 lines**, so the target needs **1,044 B** cut against 20 KiB but **1,524 B** against decimal 20,000 — Cray was asked and declined to rule for now. (2) **The five named candidates cannot reach either target:** measured at **~930–1,000 B** combined, and the row's own "~225–235 line floor" needs **26–36 lines** removed where the five move **~7** (candidates 1–3 are in-line trims that shorten bytes without deleting lines). The genuinely large blocks — `CLAUDE.md:112` (~1,100 B), `:153` (~700 B), `:73` (~800 B) — are **not on the list**. Sending this dispatch as written would repeat the s181 failure of a target that is arithmetically unreachable in scope. ~~Batch the two standing CLAUDE.md defects into whatever dispatch eventually goes out~~ — **DISCHARGED s188**: both rows below are closed, batched into the s188 three-edit Cowork round-trip. _[s188 — **the arithmetic moved AGAINST the target and the row must not be read at its old numbers.** `CLAUDE.md` is now **22,424 B** (+900 B: the §8 scenario-test rule +569, the §6 gate-claim correction +261, the §7 link resolution +70), so the cut needed is **1,944 B** against 20 KiB or **2,424 B** against decimal 20,000 — roughly **double** what this row was written against, while the five named candidates still measure only ~930–1,000 B. Note also that `:112`, one of the three "genuinely large blocks" this row says are **not** on the candidate list, is now ~260 B larger. The growth is Cray-ratified binding-rule substance, not padding — which is the point: **the target and the constitution are pulling in opposite directions, and that is the decision this row is actually parked on**, not the unit question alone.]_
- [ ] **OQ-4 — should L1 loop-detect exist at all? OPEN with a DATED, pre-committed criterion. RE-HOMED here s183 from PLAN-0094, which archived.** This row exists because the PLAN's own §Step 6 forbade carrying a live dated commitment into `done/`. **The criterion, unchanged:** re-measure after **~20 sessions** of the post-AC-7 guard (AC-7 closed s180) → **due ≈ s200**; if **true positives are still 0 and there is ≥ 1 false positive**, dispatch Cowork to draft an **ADR-013 amendment retiring L1**, noting that L2/L3/L4 already carry row E.4 more faithfully — they key on "the same *problem*" while L1 keys only on "the same *file*". **Baseline already banked (s180, all 113 transcripts 2026-06-27 → 07-27): 0 denies, 3 warns, 0 true positives**, and the guard cannot catch the s169 incident that motivated it. **Measurement method matters:** grep transcripts for `L1 warn on` **and both** deny wordings — searching only the current wording under-counts. Full reasoning: `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md` §OQ-4. *(Not due yet — premature re-measure burns the pre-commitment on an under-powered sample.)*
- [x] **The goal gate's warn path records NOTHING — FIXED s195 (#996); PLAN-0097 COMPLETE, archived.** The warn arm now appends a `_goal_gate:warn` trail entry before it pings, so the gate's most-travelled branch leaves the same durable evidence as every other outcome. **Cray ruled all three SDs:** SD-1 = (a) D5 controls, no ADR amendment (s194); **SD-2 = yes** (first-class `Evaluation.detail`); **SD-3 = dedup** (marker + same non-empty fingerprint; empty always records). The consequence is unchanged and provably so — warn entries are excluded from every decision read, and two previously-untested corners (flake, enforce-flip) now assert it. Full detail incl. the AC-6/M6 prediction that did NOT hold: `docs/plans/done/0097-goal-gate-warn-path-trail.md`.
- [x] **STATUS rotation-window slack (runbook R2) — RULED s194.** Cray typed **tighten the per-block cap + cut duplicated content**, declining both "widen the window" and "accept the trade". Applied the same session: §R2 now carries a **per-Current-Focus-block cap of ≤ 4,096 B**, plus a compliance note that its existing "RD rows are pointers, ≤ ~600 chars" rule was measured **unenforced** (8 of 10 rows over, worst 2,660 B). Policy home: `docs/runbooks/memory-architecture.md` §R2.
- [ ] Extract `docs/conventions/hardware.md` from CLAUDE.md (low priority)

## Next Steps

1. **PLAN-0005 §8.1 revisit register** — remaining deferred-foundational simplifications at their batch boundaries (audit framework, mapping layer, ORM emitter, base-Postgres → the custom-Postgres image, registry discovery). _[Corrected s153: dropped the stale "→ ADR-011+" and "→ PLAN-002 (≥ADR-014)" pointers — **ADR-011 does not exist** (earmark only, per the Active TODO above) and **PLAN-002 was never drafted** with its ADR floor moot; each item's corrected status lives in Active TODOs.]_
2. **Partner-trial readiness gaps** — `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` awaits a dedicated Cray discussion.
3. **Deferred (backlog)** — PLAN-004 Phase C only (optional polish: handoff dashboard / references-graph / unified export — Phase B complete s35, warning-swallow fixed #312); the custom Postgres image (needs a fresh ADR number + a PLAN — neither drafted; see the Active TODO for the corrected framing).
4. **Ongoing** — Continue exercising the file-based handoff mechanism (Chat ↔ Code ↔ Cowork) across batches.

## Update Workflow

**Rehomed 2026-07-24 (session-171).** The update mechanism and the Q4
`head_commit` semantics are *procedure*, not *state*, so they now live in
[`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md)
section "STATUS.md Update Workflow" (ADR-0017 D5 knowledge placement). Moved
verbatim; nothing was rewritten.
