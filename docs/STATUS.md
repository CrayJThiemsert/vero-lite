---
last_updated: 2026-08-03T12:41:00+07:00
session: 202
current_batch: "s202 — seven PRs merged (#1013–#1018, #1020): G1/G2 now deterministic, ADR-0035 D2 amendments complete, ADR-0032 Context re-ground, PLAN-0100 drafted, nav-bar overflow fixed for the dev profile, CLAUDE.md §3 names the runtime procedure spine."
current_actor: code
blocked_on: "Nothing blocks Code. PLAN-0100 execution is gated on Cray ruling SD-1..SD-5."
next_action: "Cray rules PLAN-0100's SD-1..SD-5 (SD-1 = published DB posture, load-bearing) before execution starts. Undrafted: the ADR-0035 D7 tenant-key PLAN — no ordering mandated between the two."
head_commit: 40d65d9
recent_commits: [40d65d9, ff0fcb2, ef2c898, 54dfc7d, 4b9c77f, 1e3275c, 8bdefe3, 0c48531, 0856fd4, d7d0f5c]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 202, 2026-08-03 (head_commit `6a3f2d7` → `40d65d9`) — seven PRs merged
> (#1013–#1018, #1020); this reconcile is the one still open. The theme: a
> governance gate stops asking a non-deterministic oracle, and ADR-0035's
> follow-on work opens.**
>
> **#1013 / #1016 — G1/G2 are now DETERMINISTIC.**
> `.claude/hooks/pretooluse_governance_gate_deny.py` reads the target's own
> `**Status:**` line instead of asking the local-LLM classifier, which was
> **measured** non-deterministic: the same input at `temperature 0` returned both
> `proceed` and `pause`, self-consistency **0/4**, blank output **3/12**. #1016 then
> unwired the classifier's now-redundant G1/G2 PreToolUse arm
> (`pretooluse_classifier_dispatch.py`) from `settings.json` — it was also **broader
> than its own spec**, pausing Accepted PLANs, which neither the registry's G1 row
> nor `CLAUDE.md` §6 ever claimed (both say ADR). `plan-drafter` stays exempt; the
> main agent gets no override. Three tests pin the new topology.
>
> **#1014 — ADR-0035 D2's four pointer amendments now all EXIST** (ADR-002 ×3,
> ADR-0003 ×1), plus **nine currency notes** re-dating ADR-0035's own present-tense
> claims about the MS-S1 Cloudflare Tunnel — which Cray confirms is **not running**.
> 117 insertions, **0 deletions**: pure appends, no prior text rewritten.
>
> **#1015 — ADR-0032's Context snapshot RE-GROUND (third pass), discharging the s197
> debt.** "six synthetic verticals" → six verticals of which five are synthetic and
> `fleet_maintenance` is the design partner's real Phase-1 pilot.
>
> **#1017 — PLAN-0100 drafted** (`Status: Draft`, 12 ACs, 6 phases): the ADR-0035
> exposure PLAN. Per **Cray's s202 ruling** it absorbs the UI work D5(2) implies,
> because ADR-0035's "Env only — no code" is contradicted by its own D5(2).
> **SD-1..SD-5 are unruled and execution does not start without them** — SD-1
> (published DB posture: DB-less vs synthetic Postgres) is load-bearing: it decides
> which tabs the public sees, and every allowlist row hangs off it.
>
> **#1018 — the OCT nav-bar overflow is FIXED for the dev profile.** `theme.css`'s
> responsive ladder was written for a **five**-tab header while `app.js` registers
> **ten**; measured natural width **2253 px**, so the inactive-label collapse moves
> `max-width:1360px` → `2299px`. Verified **0 overflow** at
> 1280/1366/1440/1680/1920/2400. Two tripwires, both probe-proven RED. The
> published-profile half stays open as PLAN-0100 AC-3.
>
> **#1020 — `CLAUDE.md` §3 rewritten: the runtime procedure spine is named as the
> primitive.** §3 called the ontology + code generator "the moat" and never
> mentioned `procedures.yaml` being interpreted at load; it now leads with
> ADR-0032 D6's `monitor→decide→approve→act` identity. Codegen is **rescoped, not
> denied** — only `energy`/`core` emit committed code. Cowork drafted (§6
> convention) and returned **four corrections to Code's fact-pack**, all confirmed
> before applying. `docs/conventions/glossary.md` carried the same stale framing
> and was corrected with it. **The "SME wording in §1" half is struck** — see the
> Active TODO; it has no referent.
>
> CI `gate` pass ×6. Offline at the last PR: `ruff` clean over `services/` +
> `tests/`, `mypy --strict` clean over 130 files, suite **3411 passed / 370
> skipped**; `tests/handoffs/` **762 / 2** at #1016. **Honest gap:** the 370 skips
> are the Postgres-down shape (dev DB not up on **5442**), so the offline gate did
> **not** match CI scope — CI is the check that did. Four of the six PRs are
> docs-only. Three dispatch fact-packs were refuted by the drafter and corrected
> before use (unmerged-branch reads, a stale date, a wrong route attribution) —
> each was Code's error, not the drafter's.

> **Session 199, 2026-08-01 (head_commit `2ed45b9` → `6a3f2d7`) — one PR merged
> (#1008), 0 open. PLAN-0099 COMPLETE and ARCHIVED: the wall-clock root fix, all
> six steps landing as a single six-commit stack.** The at-acceptance lowest quote
> is now stored at write time with a `recorded`/`reconstructed` provenance marker,
> both cross-row wall-clock comparisons are **deleted** rather than patched, and
> five latest-wins picks are re-keyed on a DB-assigned `seq`. All ten ACs closed.
>
> **AC-9's gate ran with its pass/fail read fixed before the run:** 3730 passed /
> 8 skipped / 0 failed; the eight skips are all host-state or live opt-ins and none
> is a node an AC names. That last clause was proven **positively** — the named
> nodes were re-run alone (38 passed, 0 skipped) rather than inferred from their
> absence among the skips, because a correct total can hide a wrong skip: one node
> starting to skip while another stops leaves the count at 8 either way. `ruff`
> clean over 586, `mypy --strict services/` clean over 130, five offline guards
> exit 0, CI `gate` pass, merge-commit `git diff` = **0 bytes**, and the full suite
> re-run on the merge commit (3730/8/0) since CI here is PR-only.
>
> **Cray ratified all four veto-open calls as-is** (typed): the stored figure stays
> NOT NULL, `seq` keeps UNIQUE on all five tables, the export row keeps figure +
> boolean + basis together, and `compute_accepted_the_cheapest` stays shared. Only
> the last carried an action — a docstring that claimed three callers where two
> reach it directly. Grounding the other three surfaced a coupling the veto list
> did not show: `cases.py` narrows `bool | None` to `bool` on the stated grounds
> that both operands are NOT NULL **columns**, so relaxing the DB constraint would
> silently change what the endpoint reports, not merely loosen a schema rule.
>
> **Separately — the MS-S1 hosting ADR's trigger FIRED.** Cray named two of
> PLAN-0095 OQ-1's four conditions directly (expose the demo beyond the LAN; test
> MS-S1 call performance over the internet, to inform scaling). The row had been
> sitting in In-Flight Discussions, not Active TODOs — it was **4 of 5** of the
> items s183 grouped as trigger-gated that were Active TODOs, and the odd one out.
> Its wording ("a LIVE candidate … still not drafted") also read as actionable
> while the handoff record said do-not-touch, and the reconciling fact — the
> trigger, and that it had not fired — lived only in a gitignored handoff and an
> archived PLAN's OQ block. Moved to an Active TODO with the trigger stated inline,
> following the OQ-4 row's precedent. Cray's initial lean is **B1** (app public,
> MS-S1 stays on LAN), veto open pending the ADR's own analysis. **The generalised
> rule is `docs/lessons/0034-deliberate-gate-outside-the-scanned-surface.md`** — a
> decision NOT to act needs the same recording discipline as an action, and its
> home is the list where someone would look for it if they thought it was missing.

> **Session 197, 2026-07-31 (head_commit `1dbd972` → `687705d`) — one PR merged
> (#1006), 0 open. PLAN-0098 COMPLETE and ARCHIVED in the same PR: View G's fleet
> branch shipped, all nine ACs closed. Theme, again: the donor's reuse contract was
> MEASURED, not re-read.**
>
> **PLAN-0098's own §D-D was wrong about the donor.** It asserted the joiner
> `governanceMoment` binds only `doa_tier` / `sod` / `governed_decision`, "all of which
> fleet produces". It also binds `po_id`, `declared_tier_id`, `is_off_avl_override`
> (`view-hero.js:42,46,49`), none of which fleet's audit emits — verbatim reuse would
> have rendered `undefined — display only` in the DOA card in front of an audience. A
> fleet joiner was written instead; SoD + join cards ARE reused verbatim, and
> `test_the_fleet_branch_reads_no_procurement_only_field` pins the correction.
>
> **Zero new CSS classes** — `EconomicImpact.baseline/governed` map onto the existing
> `hero-ledger` idiom, so `hero.css` is untouched, #999's class contract needed no
> allowlist edit, and the `?v=` bump covered exactly one asset (`c36` → `c47`).
> **AC-4 / AC-6 closed by EMPTY `git diff`** (`services/engine/`,
> `services/api/models/demo.py`, the donor's own suite) — evidence, not prose. **Five
> non-vacuity probes**, each an observable behaviour change, each RED against its
> NAMED test, each restored from a `/tmp` copy and byte-diff verified: a smuggled
> money literal, a dispatch that stops matching, a reverted cache token, a
> procurement-only field creeping back, a hidden assumptions strip.
>
> **Preview review is evidence, never a gate — and it found a real defect.** Runtime
> DOM probe on `OCT_VERTICAL=fleet_maintenance`: `undefined`=0, `NaN`=0, `hero-*`
> overflow=0, assumptions strip `hidden:false` / 144px / 6 lines, `hero-toggle`
> count=0 (**SD-2 confirmed in the DOM**, stronger than the lexical test). It also
> caught the authored `three_quote` rule rendering 143 chars of prose right-aligned
> in a 54px kv cell against a 19px row — moved to its own full-width line (`bfd789c`).
> **Found but NOT fixed (not this PLAN's):** the page overflows horizontally,
> `scrollWidth 1825` vs `clientWidth 1382`; all 24 overflowing elements are in the
> global nav bar, zero `hero-*`. Pre-existing header behaviour, tracked separately.
>
> **Cray typed four calls** in a "platform vs dev shop" discussion held BEFORE the work
> was picked; all four are carried as Active TODOs / `next_action`: (1) **measure the
> assembly-cost axis BEFORE an ADR argues it** — tripwire first, ADR on the number; (2)
> **no buyer-model mismatch** — the partners are mid-size regulated operators already,
> so `CLAUDE.md` §1's "SME" wording is loose phrasing to correct, not a strategy change;
> (3) **ADR-0032 D2's pilot gate = SATISFIED** (the fleet Phase-1 flow is a real pilot),
> so its Context snapshot must be **re-grounded**, unlocking shape-2 work — OWED, not
> done, G1-gated → `plan-drafter`; (4) **finish the fleet block** (PLAN-0098 ✅, then
> PLAN-0099 Steps 1–6) before the primitives block — insights found along the way may
> strengthen it.
>
> Suite **3700 → 3709** / 8 skipped — skip count unmoved, all 8 host-state/live
> opt-ins. `ruff` clean over 583; `mypy --strict` clean over 130; R1/R4/R7/R8 +
> registration guard exit 0. CI `gate` pass 5m56s on `bfd789c`; `git diff bfd789c
> HEAD` = 0 bytes; full suite re-run on the merge commit = **3709 / 8**.

> **Session 196, 2026-07-31 (head_commit `5382052` → `4846d5e`) — one PR merged
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
> mid-flight. Full detail: `docs/plans/done/0099-wall-clock-root-fix-store-at-write-and-sequence.md`.

> **Session 196, 2026-07-31 — SECOND workstream, same session (head_commit `a8912e0` →
> `5382052`): four PRs merged (#999–#1002). s196 ran TWO concurrent workstreams; this
> block and the one above are deliberately separate — one merged block would breach the
> 4,096 B per-block cap. Theme: two vocabulary guards pinned by measurement, then
> PLAN-0098 ratified and its backend built.**
>
> **#999 (`399fbe0`) — the CSS-class guard widened from 1 asset to all 15** (found by
> glob): 883 defined / 873 applied / **33 undefined** → a two-category allowlist under
> set equality in both directions — 4 JS lookup hooks (permanent, correct); 29 no-rule,
> of which 3 sit on inline-styled elements (semantic markers, NOT debt) and 3 are state
> toggles on a view root nothing reacts to (the likeliest real defects). Four scanner
> defects each got a permanent test — worst two: `classList.toggle(token, force)`'s
> boolean second arg read as a class name, and `api.js`'s whole `s-*` vocabulary
> invisible because it only RETURNS status names, applying no class.
>
> **#1000 (`f931b8b`) — `EconomicImpact.kind`'s documented vocabulary pinned to what
> producers emit** (five kinds now, set equality both directions vs producers found by
> glob). #994 (s195) had added `overpay_avoided` while the Field description — the one
> place a reader learns the vocabulary, shipped in the OpenAPI schema — still listed
> four. Deliberately kept OUT of PLAN-0098 so AC-6 ("zero engine build") stays absolute.
>
> **#1001 (`4bb9494`) — PLAN-0098 ratified** (fleet View G, `Status: Draft`): a mirror
> of `verticals/procurement/hero_demo/` by FUNCTION, not by shape. Cray typed SD-1 (a)
> unregistered verticals fall back to the procurement hero; SD-2 the assumptions strip
> is always-visible; **SD-3 = (c), differing from the draft's (a)** — lead with the
> measured ฿48,000, the partner's fraud origin story rides as narrative copy only,
> never a rendered figure; AC-9 added as that ruling's oracle. The drafter's AC-6
> carve-out was withdrawn at Code's R2.
>
> **#1002 (`5382052`) — PLAN-0098 Steps 1–4: fleet's View G backend + its vertical
> seam.** New `FleetHeroImpact` (measured `quoted_repair_thb` vs modelled `impact` —
> REQUIRED, validator-rejects empty `assumptions`);
> `verticals/fleet_maintenance/hero_demo/` (3 files) runs the real engine over the
> spec-loaded ladder — ฿48,000 → เจ้าของกิจการ, ฿15,000 → ผจก.เดินรถ, plus the
> fleet-only `three_quote` rule-gate card; a lazy `_HERO_BUILDERS` seam in `demo.py`
> on `settings.oct_vertical` (**ADR-0031 D4 corollary 1 FIRED at N=2**).
> `HeroImpactLedger` untouched (ADR-0030 D2) — `/impact` unions at the decorator.
> AC-1/2/3/4/5/6/8 closed — **AC-6 + AC-4 verified by empty `git diff`, not
> asserted**; Steps 5 (frontend) + AC-7/AC-9 remain. Two deviations recorded, not
> absorbed: Step 2's "run the real `compute_three_quote`" is impossible (events carry
> no vendor counts) — the stamped basis is READ per `sourcing.py:79-82`, still
> satisfying AC-2; and AC-2's set-equality parity cannot hold (2 bands vs 3 rungs) —
> implemented as the stronger per-side derivation from the loaded spec.
>
> **Suite 3676 → 3700 / 8 skipped throughout** — same skip count, nothing silently
> disabled; ruff + format + `mypy --strict services/` + `alembic check` clean; guards
> exit 0; CI `gate` pass, merge-commit `git diff` = 0 bytes, and the full suite re-run
> on every merge commit. **16 non-vacuity probes**, each RED against its NAMED test,
> restored from `/tmp` and diff-verified; **two probes were themselves defective and
> read GREEN** before correction — caught only because each is bound to the one test
> it must redden. The 3 new `hero_demo/` files are named in
> `_POST_SCAFFOLD_DONOR_FILES` with a prose reason (fleet is the scaffolder's golden
> donor; a governed hero is bespoke per partner, ADR-0032 D1.2); the exclusion proven
> surgical — a stray `.py` in the donor still reddens the test.

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
| 2026-08-03 | **s202 — G1/G2 made DETERMINISTIC (#1013/#1016); ADR-0035 D2's amendments COMPLETE (#1014); ADR-0032 Context re-ground (#1015); PLAN-0100 drafted (#1017); nav-bar overflow fixed (#1018).** The classifier was *measured* non-deterministic at `temperature 0` (self-consistency 0/4, 3/12 blank), so the gate now reads the target's `**Status:**` line and the classifier's G1/G2 arm is unwired. **Cray typed: PLAN-0100 absorbs the UI work D5(2) implies.** SD-1..SD-5 unruled → execution gated | `ef2c898` (head_commit) / [#1018](https://github.com/CrayJThiemsert/vero-lite/pull/1018) / `docs/adr/0035-hosting-and-exposure-model.md` / `docs/plans/0100-exposure-published-demo-surface.md` |
| 2026-08-01 | **s199 — PLAN-0099 COMPLETE (10/10 ACs) and ARCHIVED; the MS-S1 hosting ADR's trigger FIRED.** Six-commit stack merged as one PR: stored at-acceptance figure + provenance, both wall-clock comparisons deleted, five picks re-keyed on `seq`, the ordering guard widened to `services/`. AC-9 proven positively (named nodes re-run alone, 38/0) rather than inferred from the skip total. **Cray ratified all four veto-open calls as-is.** Separately, Cray's stated intent to show the demo over the internet fired two of OQ-1's four conditions; row moved In-Flight → Active TODO, initial lean **B1** | `6a3f2d7` (head_commit) / [#1008](https://github.com/CrayJThiemsert/vero-lite/pull/1008) / `docs/plans/done/0099-wall-clock-root-fix-store-at-write-and-sequence.md` |
| 2026-07-31 | **s197 — PLAN-0098 COMPLETE + ARCHIVED (#1006): View G's fleet branch, all nine ACs.** The donor joiner also binds `po_id`/`declared_tier_id`/`is_off_avl_override`, which fleet never emits (§D-D claimed otherwise) — a fleet joiner was written; SoD + join cards reused. Zero new CSS; AC-4/AC-6 by empty `git diff`; 5 probes RED. **Cray typed 4 calls**: measure assembly-cost first; no buyer-model mismatch; **ADR-0032 D2 pilot gate = SATISFIED** (Context re-ground OWED); fleet before primitives. Suite → **3709** | `687705d` (head_commit) / `docs/plans/done/0098-fleet-view-g-hero-demo-mirror.md` |
| 2026-07-31 | **s196, 2nd workstream (#999–#1002) — PLAN-0098 ratified + Steps 1–4 built; CSS-class guard → all 15 assets; `EconomicImpact.kind` → 5 kinds.** **Cray typed SD-1 (a), SD-2 always-visible, SD-3 = (c), differing from the draft's (a)**: lead with the measured ฿48,000 — the fraud origin story is narrative copy only, never a rendered figure (AC-9 = its oracle). Backend runs the real engine over the spec-loaded ladder via `_HERO_BUILDERS` (ADR-0031 D4 corollary 1 FIRED at N=2). Suite → **3700** | `5382052` / `4bb9494` / `docs/plans/done/0098-fleet-view-g-hero-demo-mirror.md` |
| 2026-07-31 | **s196 — PLAN-0099 drafted + merged (#1003): the wall-clock root fix.** An intermittent quote-history flake was **measured**, not inferred — the dev clock steps back 20x/300 s (every step ≥400 ms) against a 90–166 ms window ⇒ ~0.9%/run; the Postgres-`now()` hypothesis was **refuted by construction**. **`<=` → `<` rejected on evidence.** Two worse sites found (the DOA gate via `latest_accepted_quote`; the month-end export). **All 5 SDs Cray-ratified** — store-at-write, backfill marked **reconstructed**, three riders on migration `0023`. No production code changed | `4846d5e` (head_commit) / `docs/plans/done/0099-wall-clock-root-fix-store-at-write-and-sequence.md` |
| 2026-07-31 | **s195 — fleet's Box-4 ฿ facet, a REAL PM-confirm race, PLAN-0097 COMPLETE (#994–#997).** **Cray typed** fleet's **event-anchored** ฿30,000 basis + the conservative **15%** recovery fraction. #995 fixed an **unlocked** read-then-write that let two deciders both get a 200 while one overwrote the other (`FOR UPDATE`, no migration). #996/#997 shipped the warn-path trail and archived the PLAN — **SD-2 = yes**, **SD-3 = dedup**. Suite → **3676** | `a8912e0` (#997, head_commit) / `8381c92` (#994) / `fa53911` (#995) / `docs/plans/done/0097-goal-gate-warn-path-trail.md` |
| 2026-07-30 | **s194 — two rotted-pointer repairs + Cray's STATUS-size ruling (#990, #991).** #990 fixed ADR-0025's archive pointer (wrong by whole FILE since the s144 re-charter; now cited by section heading, no line numbers). #991 drafted PLAN-0097 — the goal gate's silent warn path is an **implementation gap against ADR-0018 D5/V2-D1**, not ratified design. **Cray typed: SD-1 = (a), D5 controls (SD-2/SD-3 stay OPEN)**; **STATUS size = tighten the per-block cap + cut duplicates** | `b25cc98` (head_commit) / `c2584c8` (#990) / `docs/plans/done/0097-goal-gate-warn-path-trail.md` / runbook §R2 |
| 2026-07-30 | **s193 — PLAN-0096 Step 8 item 5 COMPLETE (#982–#986): the month-end export end to end, with a KPI that can fail.** Row set = governed ∪ escaped money (a naive export reports 100% by construction). **Cray typed (ค)** traceable = governed AND documented; **(ก)** persist `three_quote_basis` (alembic `0022`). Two defects found by ORACLES, not review. Suite 3607 → **3646** | `367c15b` (#987 merge, head_commit) / `367a08e` (#986) / `ed09502` (#982) / `docs/plans/done/0096-fleet-flow-completion-phase1.md` |
| 2026-07-30 | **s192 — PLAN-0096 Step 8 item 3 COMPLETE (#979): the case → run link, proven on BOTH gate drivers.** The hook read `output_set`, so a rejected case was invisible (fix: `decided_entries()` reads `decisions`); `_outcome` let the run state outrank a refusal. **Cray typed: a refusal is checked FIRST.** Five non-vacuity probes, all RED as predicted. Suite → **3604** | `5dd8ce6` (#979, head_commit) / `docs/plans/done/0096-fleet-flow-completion-phase1.md` §Step 8 |
| 2026-07-30 | **s191 — a REAL repair case now reaches the governed gate (#975–#977).** The accepted quote (ใบที่ตกลง, alembic `0019`) gives the DoA ladder a ฿ figure existing BEFORE the work and tracing to recorded evidence; Cray typed the required FK + reason-only-when-not-cheapest. The case → event path wires it in with **zero engine and zero adapter-`__init__` diff**. One probe came back GREEN — a vacuous oracle a fail-soft handler was hiding. Suite → **3597** | `99b752f` (#977, head_commit) / `d3f2919` (#976) / `d781683` (#975) / `docs/plans/done/0096-fleet-flow-completion-phase1.md` §Step 8 |

## In-Flight Discussions

- **PLAN-0096 — COMPLETE 12/12 and ARCHIVED (s193).** The fleet design partner's Phase-1 flow, shipped end to end across s186→s193 — real governance numbers, case capture from minute 1, the quote evidence pack, the sourcing signal that retired a fail-open default, the E-2 ratification window, the PM import, the outbound-only-and-DISARMED LINE OA surface, the 8-step task chain, and the month-end Express export. **Four residual risks outlive the PLAN and are why this entry is not simply deleted — all four are recorded in the archived PLAN, which is where the detail now lives:** RR-1 (per-baht approver→case attribution is INFERENCE, not data — `GovernedDecision` carries no timestamp and no per-entity key; sound while one human resolves a whole gate, silently wrong the day two approvers share a resolution); RR-3 (concurrency-race was the weakest coverage row for AC-4/AC-9/AC-10 — **both named gaps CLOSED s195 by #995**: the PM-confirm race turned out to be a REAL defect, now `FOR UPDATE`, and `allocate_repair_order_no` got the test its docstring implied, which corrected the constraint that docstring named); ศูนย์ต้นทุน ships EMPTY (partner granularity still unanswered — also an open Active TODO below); and `latest_per` still collapsing two open cases on one truck (item 4, **Cray typed (ค) defer**) — the older case never reaches the gate, so if it is paid it reports as *ungoverned*, which a reader of the number cannot distinguish from a governance failure. Full record: `docs/plans/done/0096-fleet-flow-completion-phase1.md` (§Verification preamble + §Acceptance Criteria for RR-1 / RR-3 / ศูนย์ต้นทุน; §Step 8 for `latest_per`); the AC-12 sign-off is in `.claude/handoffs/session-193/` (gitignored).
- **PLAN-0095 — COMPLETE 7/7 and ARCHIVED (s177, #927/#928).** The scaffold-era `Dockerfile` builds and boots the DB-less synthetic OCT demo: `/health` 200 in ~2 s, all six verticals discovered, `uid=999(vero)`, `HEALTHCHECK` healthy, and `alembic current` → `0012 (head)` from inside the image. **OQ-1, the hosting model — the last thing open from it — is now CLOSED**, answered by **ADR-0035** (Accepted s200; its D2 pointer amendments completed s202, #1014); the exposure work it opened lives in PLAN-0100, not here. Full record: `docs/plans/done/0095-docker-image-boot.md`. _[Corrected s182, `was an error`: this entry still described the PLAN as Draft with "Steps 1–5 UNEXECUTED … the image does not boot today" and cited the pre-archive path — refuted by the s177 row in Recent Decisions above and by the archived PLAN's own `Status: Complete`.]_
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

- [x] **MS-S1 hosting/exposure ADR — DISCHARGED. ADR-0035 Accepted s200; its D2 pointer amendments COMPLETE s202 (#1014).** PLAN-0095's OQ-1 is answered: one domain on MS-S1, a subdomain per system, published through an edge-gated, outbound-only tunnel — the ADR-002 + ADR-0003 successor those ADRs deferred twice as an unnumbered `ADR-NN`, whose pointers now exist (ADR-002 ×3, ADR-0003 ×1). **Read the ADR, never a restatement here** — including its **nine currency notes**, which re-date its present-tense Cloudflare-Tunnel claims: the tunnel is **not running today**. `docs/adr/0035-hosting-and-exposure-model.md`.

- [ ] **PLAN-0100 — the ADR-0035 exposure PLAN. DRAFTED s202 (#1017): `Status: Draft`, 12 ACs, 6 phases. EXECUTION IS GATED on Cray ruling SD-1..SD-5.** **SD-1 is load-bearing** — the published deployment's DB posture, (a) DB-less vs (b) synthetic Postgres — because it decides which tabs the published profile registers and every allowlist row hangs off it; the rest cannot be finalized around an unruled SD-1. Per **Cray's s202 ruling** the PLAN absorbs the UI work D5(2) implies, since ADR-0035's "Env only — no code" is contradicted by its own D5(2). It also carries the **published-profile half of the nav-bar work as AC-3**. `docs/plans/0100-exposure-published-demo-surface.md`.
- [ ] **The tenant-key PLAN (ADR-0035 D7 (i)–(vii)) — UNDRAFTED.** ADR-0035 mandates **no ordering** between this and PLAN-0100, so neither blocks the other and this one is startable independently. Route: `plan-drafter` (G2 — Code may not author a new PLAN), Code R2s and commits. `docs/adr/0035-hosting-and-exposure-model.md` §D7.

- [x] **ADR-0032's Context snapshot RE-GROUNDED — DONE s202 (#1015), third pass.** "six synthetic verticals" → six verticals of which five are synthetic and `fleet_maintenance` is the design partner's real Phase-1 pilot. Discharges the OWED debt created when Cray ruled **D2's pilot gate SATISFIED** at s197. `docs/adr/0032-strategic-frame-demo-to-pilot-wedge-and-3-shape-roadmap.md`.
- [ ] **Assembly-cost axis — MEASURE it before an ADR argues it (Cray typed s197); nothing built, no PLAN drafted.** Build the tripwire that puts a number on assembly cost first, *then* draft the ADR on top of that number — the ordering is the ruling. **The series measured so far is banked HERE because it is banked NOWHERE ELSE in the repo — no test, no doc, no PLAN holds it:** churn per vertical went **1:1.8 → 1:6 → 1:1.1**, i.e. **spiky, not falling**, which is the shape any ADR on this axis has to argue against. Left unbanked it survives only in session memory and dies at the next context reset; a tripwire that recomputes it is what makes it evidence rather than a recollection.
- [ ] **`CLAUDE.md` §3 names the code generator as the moat; measurement (s197) says the load-bearing primitive is the runtime-interpreted `procedures.yaml`.** `_ORM_COMMITTED_DEST` (`services/engine/code_generator.py:871`) carries only `energy` + `core`; the other five verticals' generated ORMs land on gitignored paths with **zero source importers**, and the generator's own docstring calls them "a gitignored reference artifact". One constitutional edit, §3 only: Cowork drafts the text, Code applies. _[Corrected s202, `was an error` — **this row's batched-in "§1's 'SME' wording" half HAS NO REFERENT and is struck**: the string `SME` has never existed in `CLAUDE.md` (`git log -S "SME" -- CLAUDE.md` returns **zero** commits), and §1 in fact reads "2 **enterprise** design partners". The s197 Current Focus block records the same mistaken premise; both rows are corrected once, here. **Cray's actual s197 point is untouched and needs no edit** — the partners are mid-size regulated operators, which is what §1 already says. Scope is therefore §3 alone.]_
- [x] **The OCT console's global nav bar overflowed its own viewport — FIXED for the dev profile s202 (#1018).** Root cause was **not** the header's content but its ladder: `theme.css`'s responsive breakpoints were written for a **five**-tab header while `app.js` registers **ten**. Measured natural width **2253 px**, so the inactive-label collapse threshold moves `max-width:1360px` → `2299px`; verified **0 overflow** at 1280/1366/1440/1680/1920/2400. Two Python geometry tripwires, both probe-proven RED (`docs/conventions/ui.md`: no build step, so a UI tripwire must be a Python test; a new class needs a rule or `tests/api/test_css_class_contract.py` goes RED under set-equality). **The published-profile half remains OPEN as PLAN-0100 AC-3.**
- [ ] **Seam-scoped mutation-testing CI — a PLAN candidate, NOT built.** Surfaced s188 as the one CHECKABLE variant the scenario-test hook rejection does not cover; **rehomed here s191** when its parent `[x]` row was pruned, because STATUS was its only home. A CI job that requires the scenario suite to REDDEN under a seam mutation: ritual compliance cannot fake it, since an empty or stubbed scenario suite stays green under mutation — exactly what a file-existence hook would miss. Rationale: `CLAUDE.md` §8's scenario-test bullet.
- [ ] **PLAN-0096 partner round-2 — ANSWERED s189; five of seven closed, one non-blocking follow-up open.** A1 → Step 6 built (#965); A3 → `pm_due` built (#968); **A4 + A7 confirmed values already shipped** (flat ฿5,000 ceiling, `"30001"` inclusive floors); A5 **parked** — no real Wialon export exists yet. **A2 is answered and consumed by Step 8** (no longer a gate). **Open, NON-blocking: cost-center (ศูนย์ต้นทุน) granularity — per truck or per company?** Ship the column, fill the rule when it lands. A6 is answered but is a Step 9 *runbook* item. Detail: `docs/plans/done/0096-fleet-flow-completion-phase1.md`.
- [ ] **The AT-2 extraction — only the F-FACTORY half remains, owned by PLAN-0076 T1.** The criterion-vocabulary half SHIPPED as PLAN-0087 (COMPLETE 8/8, ARCHIVED — #840/#841); ADR-0025 D7's generator deferral was CANCELLED at N=4 (Cray-ratified, typed); SD-1 = (a) keeps the procedure-aware `ExecutorFactory` half with PLAN-0076 T1, guard `test_at2_extraction_obligation_is_owned` ARMED. Full detail: `docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` + `docs/plans/0076-*.md` §A.
- [ ] **PLAN-0075 follow-ons — homed by PLAN-0076 (`Status: Tracking`, #752, s133).** T1 (ADR-0031 D3 gate-plugin seam, F-FACTORY) is PARTIALLY discharged — the criterion-vocabulary half shipped as PLAN-0087; the procedure-aware-`ExecutorFactory` half stays OPEN here. T2's F-PIN remainder CLOSED s143 (#784), but **F-PIN itself stays OPEN**, so PLAN-0076 does NOT archive and its AC-6 presence guard stays ARMED. Full detail: `docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` §A.
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2) — open ONLY for the O-2 residue.** Every other leg is DONE + archived (PLAN-0046/0048/0061/0062/0066–0068/0070/0071/0073 → `done/`). **The one OPEN residue:** procurement's `intake` migrated only **PARTIALLY** — the derived fields ALREADY moved to declared `transform` ✔ (PLAN-0078 PR-1 #762, AC-2 ticked), so what is left is **only the cardinality-changing `candidate_quotes` nest**, which is explicitly Out-of-Scope there. *[Corrected s175 by the #921 grounding sweep, `was an error`: this entry said production execution stays `_SeedQuery` "for derived fields" — it does not; the derived fields are migrated and the reshape is the sole residue.]* Full detail: `docs/plans/done/0062-per-vertical-seed-migration.md` §SD-C (the co-exist decision + its STOP-and-surface tripwire) + `done/0078-*.md` §L-3 and its Out-of-Scope, where the residue is walled in.
- [ ] **Bounded/incremental chain verification (PLAN-0063 SD-4 follow-up, s118).** `GET /audit/verify` walks the WHOLE chain O(n) on demand — accepted at pilot scale. Future work = a checkpointed head / verify-since-anchor design; anchor storage ≈ external anchoring — **do not build without re-reading the tripwire** in `docs/plans/done/0063-audit-chain-verification-surface.md` + the `services/api/routers/audit.py` module docstring (SD-4). _[Note: the docstring's "ADR-011 boundary" is an EARMARK — `docs/adr/` jumps 0010 → 0012.]_ *(#688/#690)*
- [x] ~~DEFERRED: a monotonic `sequence` column on `step_results` — the ROOT fix for `load_run`'s wall-clock ordering.~~ → **DISCHARGED by PLAN-0099 (s198).** Migration `0023` adds a DB-assigned `seq` to `step_results` and to the four latest-wins evidence tables; `load_run` is re-keyed `(seq, step_result_id)`. Widened beyond the original deferral: the at-acceptance figure is stored at write time with a `recorded`/`reconstructed` provenance marker (SD-1 + SD-2), the `latest_accepted_quote` pick feeding the DOA gate is `seq`-keyed, and closeout / justification / the export's run-link pick came with it (SD-3 a/b/c). **The un-defer trigger did NOT literally fire** — both orderings it enumerated are still display-only. What failed was the safety-margin ARGUMENT: that enumeration was subsystem- and vocabulary-scoped, and wall-clock dependence was later built on correctness paths it never anticipated (the evidence-pack sites, PLAN-0096 Step 8 / migration `0019`, 2026-07-30). Classified `superseded by new info`, not `was an error`. Measured at the fix boundary: the guard's original three-name vocabulary finds exactly the 2 sites its docstring named; the nine-name vocabulary finds 12. `/runs` + `view-map.js` `CAP = 5`: **knowingly left** on the wall clock, display-only, recorded as a decision in PLAN-0099 §Coverage. Full detail: `docs/plans/done/0099-wall-clock-root-fix-store-at-write-and-sequence.md`.
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
