---
last_updated: 2026-08-12T22:02:51+07:00
session: 225
current_batch: "s225 — PLAN-0103 Step 6 SHIPPED and nine of eleven ACs closed (#1136–#1141); verifying an inherited 'closed in substance' claim found AC-7 and AC-6 FALSE — both fixed, not ticked over."
current_actor: code
blocked_on: "NOTHING blocks repo work. AC-11's RoPA (Cray's, as data controller) gates fleet's bring-up, the last Step 10; AC-10 clause 2 requires a typed §8 go per bring-up."
next_action: "PLAN-0103 has NO Code-executable remainder — AC-11 (Cray authors the RoPA) → fleet's typed §8 go → Step 10 bring-up → AC-10. Code's next work comes from Active TODOs, not this PLAN."
head_commit: b229fcd
recent_commits: [b229fcd, 8f68ee8, 0c1be0f, f936e55, a58f303, ae39f56, 445d18a, 45d0107, c9b519d, 376e8fc]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 225, 2026-08-12 (head_commit `853d827` → `b229fcd`) — six PRs
> merged (#1136–#1141), 0 open. #1136–#1138 are session 224's tail and are
> recorded here, because the block below was written by #1135 and stops
> there. Theme: an inherited "these ACs are closed in substance" claim was
> VERIFIED rather than relayed, and two of them were false.**
>
> ✅ **PLAN-0103 Step 6 SHIPPED (#1138)** — fleet's three-persona picker plus
> SD-8(iii)'s narrative copy where Tab G's Act card would be. 15 files,
> **+1062**, tests **4007 → 4025**. **#1139** then closed six ACs in the PLAN
> (**AC-1..AC-5, AC-7**), recorded Step 6's execution, and carried three
> corrections.
>
> 🔴 **Verifying the inherited claim is what found the two falsehoods.**
> **AC-7's own text described an approval the engine refuses** — wrong from
> the moment it was written, not drifted into. **AC-6 was not closed at all:
> the guard its text names had never existed.** Both were **fixed rather than
> ticked over** — **#1140** shipped AC-6's missing guard (tests **4025 →
> 4028**; `.gitignore` also gained `.claude/launch.json`) and **#1141** ticked
> AC-6, closed **as code**.
>
> ✅ **Nine of eleven ACs are now closed.** Open: **AC-10** (the per-bring-up
> obligation — fleet's bring-up has not happened and needs its own typed §8
> go) and **AC-11** (the RoPA, Cray's artifact as data controller). AC-11
> gates fleet's bring-up, which gates AC-10, and `Status:` is still `Draft`.
> ⚠️ **Nothing remaining in this PLAN is Code-executable.**
>
> ✅ **The session-224 tail.** **#1136** reconciled s224 and corrected
> procurement's `cloudflared/config.yml` header, which still repeated SD-8's
> false premise. **#1137** tracked the RoPA change statement at
> `docs/compliance/ropa-change-statement-fleet.md` — so **AC-11 now names its
> path** — and added **Lesson #0041**.
>
> 🔴 **Three of STATUS's OWN standing claims were measured false and are
> corrected IN PLACE, not annotated beside the wrong sentence.** (1) *"Code
> cannot edit `docs/plans/` (G2)"* — **false**: G2 fires only on a numbered
> artifact that does **not yet exist** (creating one consumes a number), and
> G1 is scoped to `docs/adr/` with `Status: Accepted`, never `docs/plans/`.
> What actually routes an existing PLAN to the drafter is the **ADR-009 D1
> convention** plus the advisory Stop classifier — practice unchanged, stated
> reason wrong. (2) PLAN-0100 D-4's *"four seams in one file"* — an
> **undercount**: eight or more, and the decisive omitted seam is the **system
> prompt**, which forbids the very combination the work exists to enable.
> (3) The stream-3 (primitives) *"ZERO ratified ACs/Steps"* — false as worded:
> PLAN-0076 has six ACs and four Steps; the true claim is *zero that direct a
> build*.
>
> 🆕 **Two Active TODOs added, each on its MEASURED basis** — the ฿
> realized-vs-projected join (⚠️ the circulating *"~40 lines by reusing
> `benefit_rollup`"* framing was **checked and is wrong**) and the demo-key
> rotation cadence (Cray's, posture not code). Read the rows below.

> **Session 224, 2026-08-12 (head_commit `b4cb860` → `853d827`) — one PR
> merged (#1135), 0 open. Theme: a governance slot's own factual premise had
> been wrong for three sessions, and RUNNING THE SURFACE is what found it.**
>
> ✅ **RULED (Cray, typed, s224): PLAN-0103 SD-8 = option (iii)** — Tab G's Act
> card is replaced with **narrative copy** on a personaless published system,
> and **Step 6 builds it**. The cost is accepted unsoftened: **copy with no
> oracle — no test reddens if the copy is wrong.**
>
> 🔴 **The slot's premise was FALSE, and measurement is what found it.** SD-8
> asked whether Tab G's Act card "should render at all" on a personaless
> system. Measured against a **local reproduction** of procurement's own
> committed `published.env` (`UI_PROFILE=published`, `UI_PUBLISHED_VIEWS=G,F`,
> no `API_KEYS`): the card **does not render on any published profile** — zero
> `input` elements of any type on Tab G and Tab F, "Act — the human DOA gate"
> absent from the DOM, rendered tabs `G`,`F` only. ⚠️ **A reproduction, never a
> live-system reading** — the domain is deliberately absent from this repo
> (ADR-0035 D1(3)) and the live surface sits behind Access.
>
> **The mechanism is upstream of personas.** The card renders only in event
> mode (`view-hero.js:655`) and `mount()` defaults to manual (`:662`), while
> the one control that reaches event mode is suppressed on every published
> profile (`:604-614`, `if (!published)`) because event mode fires
> `POST /demo/hero/event` — the unauthenticated DB write D5(2) excludes.
> **PLAN-0100 Step 3 did that BEFORE SD-8 was authored**, which is why the
> classification is **`was an error`, not `superseded by new info`**. It stood
> through s222 and s223 because nobody ran the surface and looked.
>
> **Four statements corrected INLINE, each marked**, on this PLAN's own
> #1128→#1129 precedent: the "visitor sees a login form" claim; the slot's
> premise; option (i)'s rationale (it describes a dead end that cannot occur —
> its *outcome* was coherent, its *reasoning* was not); and option (ii)'s
> quoted price of "a new published-profile UI branch", already paid by
> PLAN-0100 for an unrelated reason. The s222 Live-input paragraph was
> **corrected rather than struck** — it carries a separate typed ruling (keep
> `API_KEYS` provisioned) plus true edge facts; only its "option (i)"
> characterisation was wrong.
>
> 🆕 **One implementation note added under Step 6 — rides SD-4 RULED (b), no
> new slot.** `view-monitor.js` contains **zero** `isPublished()` references,
> so its `authBar()` login form — free-text identity + password-type key input
> (`view-monitor.js:425-463`) — renders **unconditionally** whenever Tab H
> mounts. **Fleet is the only system publishing H**, so this is invisible today
> and **becomes visible at fleet's bring-up**. SD-4(b) already rules that
> surface is the published-profile-only persona picker; the published branch
> that would make "published-profile-only" true **does not exist yet**.
>
> **Gates on the tip:** 4007 passed / 8 skipped, ruff + `ruff format` +
> `mypy --strict services/` clean, CI green on the same SHA. ⚠️ Riding in the
> reconcile PR and **not** in `853d827`: `oct-procurement/cloudflared/config.yml`'s
> header, which still described SD-8 as open and repeated the same false
> login-form claim, is corrected there.

> **Session 223, 2026-08-12 (head_commit `bd43d67` → `b4cb860`) — two PRs
> merged (#1132, #1133), 0 open. STATUS had fallen EIGHT PRs behind
> (#1126–#1133); #1127–#1131 are session 222's tail and are recorded in the
> next block, not here. Theme: the MS-S1 secrets exposure session 222 left
> open is CLOSED and PROVEN.**
>
> ✅ **The exposure is CLOSED (#1132).** Run as a ladder under **two typed §8
> gos**: rung A dropped `Authenticated Users`; rung C also dropped
> `BUILTIN\Users` and granted the signed-in account's SID `(OI)(CI)(RX)`.
> Final ACL on the directory and all **8** paths under it: that account
> `(RX)` + `BUILTIN\Administrators (F)` + `NT AUTHORITY\SYSTEM (F)`. The
> bring-up §8 remedy that s222 **measured** to break Docker Desktop's bind
> mount is replaced with the working form, together with the **filtered-token**
> mechanism that explains why the old Administrators-only tightening failed.
> Record, never a restatement:
> `docs/logs/2026-08-12-ms-s1-secrets-acl-tightening.md`.
>
> 🔴 **The canary discipline is the transferable part — and it is why s222's
> breakage stayed invisible.** Each rung was verified by a **force-recreate,
> never a restart**: a running container already holds the file handle, so a
> restart cannot see a broken ACL. A rung was believed only on a **changed
> container id** plus `Registered tunnel connection` in the connector log.
> Canaries were **procurement-only**; `oct-energy`'s connector was recreated
> **exactly once**, deliberately, as the terminal end-to-end proof, and
> **`oct-energy-app` was never recreated** (Up 40 h throughout). The verifier
> was seen **RED before GREEN** (`authenticated_users_aces` 4 → 0) with a
> positive anchor, so an ssh failure fails **closed**. Gates: **4007 passed /
> 8 skipped**.
>
> ✅ **#1133 — the leftover `icacls /save` backup relocated** into the
> tightened directory rather than deleted (Cray, typed). 🔴 **A same-volume
> move keeps the OLD ACL** — measured, and now in the runbook; an unmeasured
> "a copy inherits" claim was **scoped back to what was actually measured**.
>
> 🔴 **The one Cray ruling this record exists to carry — J4's per-action
> reading.** "Run the full `tests/` before pushing" stays **BINDING**, but is
> evaluated against **the commit(s) being pushed at evaluation time**; earlier
> uncovered pushes are **residual gaps, not a standing FAIL** — a criterion no
> future work can turn green is defective, not strict. ⚠️ **This ruling lived
> in a gitignored `goal.json` that has since been DELETED. STATUS and the s223
> handoff are now its only homes — do NOT trim it on a later reconcile without
> rehoming it first (R2 carve-out).**
>
> ⚠️ **Unchanged by this session.** **SD-8 is still NOT RULED** and gates Step
> 6. **AC-11's RoPA** (Cray's, as data controller) gates **fleet's** bring-up,
> the last Step 10. **AC-10 stays deliberately NOT ticked** — three typed §8
> gos are on record, fleet's is outstanding.

> **Session 222 cont., 2026-08-11 (head_commit `3a11e87` → `bd43d67`) — five
> PRs merged (#1127–#1131) after the #1126 reconcile, 0 open. The block below
> was written by #1126 and stops at #1125; this one carries the rest. Theme:
> PLAN-0103 Step 10 EXECUTED — procurement is live as published system #2 —
> and three corrections that each REFUTED a claim rather than filling a gap.**
>
> ✅ **AC-8 and AC-9 are TICKED (#1127)**, PLAN-0103 **Step 1 recorded**, and
> **ADR-0037 D2.7 DISCHARGED**. 🔴 **F4's stated premise was corrected BY
> MEASUREMENT** — refuted, not merely filled in — and **ADR-0035 OQ-4's dead
> trigger retired**.
>
> 🔴 **ADR-0036's claim that the apex domain "appears nowhere in this repo"
> was FALSE (#1128), and #1129 moved that correction INLINE** so a reader who
> stops at the false clause is stopped **by** it. ⚠️ **ADR-0035 OQ-6 is
> SURFACED and OPEN:** does D1(3)'s broad documentary clause govern **evidence
> documents**? Three options stated neutrally, **none recommended** — Cray's
> call. **RULED (Cray, typed): correct the ADR, do NOT edit the archived
> PLAN.**
>
> ✅ **Step 10 EXECUTED — procurement is LIVE as published system #2
> (#1130)**, under a typed §8 go, with 5 runbook corrections riding along.
> Execution record:
> `docs/logs/2026-08-11-plan0103-step10-procurement-bring-up.md`. 🔴 Its first
> head **failed CI on the AC-5 shadow-registry guard — on a docs-only PR**,
> the guard firing on exactly the class of file nobody expects to trip it.
> **RULED (Cray, typed): keep `API_KEYS` on procurement** despite it having no
> consumer, so it is ready if Step 6 admits `/whoami`.
>
> ✅ **s222's four unhomed findings are REHOMED (#1131)** — a new **Lesson
> #0040**, a **session-222 addendum to Lesson #0029**, and two runbook
> entries.

> **Session 222, 2026-08-11 (head_commit `e938cf6` → `3a11e87`) — five PRs
> merged, 0 open, across two sessions: #1121/#1122/#1123 are session 221's tail
> (STATUS stopped at `d71b2ed`, written mid-session) and #1124/#1125 are s222's.
> Theme: PLAN-0103's two open ACs both close in substance, and ADR-0037 D2.7
> stops being a code read and becomes a measurement.**
>
> ✅ **AC-8 clause 2 CLOSES (#1124).**
> `tests/api/test_visitor_case_to_monitor_scenario.py` (3 tests) drives a Tab-I
> case into `GET /runs`, the read Tab H actually makes. ⚠️ Step 7's seed (#1122)
> makes H non-empty *before any visitor arrives*, so a presence check would pass
> **with the case removed entirely** — every assertion is a **delta** against a
> post-seed baseline, tied to the visitor's own `case_id`.
>
> ✅ **ADR-0037 D2.7 MEASURED, not read** — s221 read 2 of 14 `append_audit`
> sites; #1124 asserts over **every `audit_log` row the run produces**, on both
> the ordinary and the waiver→ratify paths. **Result: no visitor-typed case text
> in the chain; `case_id` recoverable.** Two oracles (a positively-controlled
> bracketing sentinel; a structural payload-key allowlist) and why each: the
> module docstring, not a restatement. ⚠️ **One finding D4 must price:**
> `WaiverInvocation.justification` and the ratification `note` **are** human free
> text in the hash-chained log **by design** — a named internal principal's, not
> the visitor's, so possibly its own RoPA line.
>
> 🔴 **#1125 retracted a false claim in #1124's own comment** — that a
> **middle-slice** leak (dropping both bracketed ends, keeping the Thai between)
> "is no longer a leak of the visitor's text". False: it lands in an
> already-allowed key, invisible to **both** oracles. **RULED (Cray, typed,
> s222): that residual risk is ACCEPTED**; **revisit if an audit payload gains a
> field that legitimately holds a SLICE of operator-entered text.**
>
> ✅ **Session 221's tail, unrecorded until now.** **#1121 delivered Step 8b**,
> the portal-side assembly request — gitignored handoff + tracked summary
> `docs/logs/2026-08-10-plan0103-step8b-portal-assembly-request.md`; with Step
> 8a's card files in place, **AC-9's evidence is complete**. ⚠️ It is **parked,
> not sent**, and **the landing page itself has been built by nobody**. **#1122
> shipped Step 7** (`operate_seed.py` + `main.py` wiring + tests), discharging
> the s221 no-op hazard — the seed gate now branches on `fleet_maintenance`; it
> did **not** close AC-8. **#1123** made `render-handoff` report live goal state.
>
> 🔴 **Cray rulings this record exists to carry.** (1) **No portal REPO will be
> created** — PLAN-0103 **Step 1's** answer, unrecorded through three sessions.
> ⚠️ In full, because the shorthand has been misread once as "no portal": the
> portal/landing surface **still exists**, with DNS, Access policies and the
> landing surface configured in the **Cloudflare dashboard**, each system on its
> own `oct-<vertical-id>` subdomain label. **ADR-0036 D2's two-artifact price
> per system is unchanged** — dashboard config rather than repo files. (2) **Step
> 7 before Step 6**, with **SD-8 ruled before Step 6 is built**; Step 7 shipped,
> so the live half is SD-8. (3) D2.7's residual risk **ACCEPTED**, above.
>
> ⚠️ **What this does NOT close.** **AC-8 and AC-9 are closed in SUBSTANCE; the
> PLAN's checkboxes are NOT ticked** — the tick is owed to a `plan-drafter`
> dispatch. _[Corrected s225, `was an error`: this read "Code cannot write
> `docs/plans/` (G2)". **G2 does not gate an existing PLAN** — it fires only on
> a numbered artifact that does not yet exist. The routing rule is the ADR-009
> D1 convention; the full correction is in the PLAN-0103 Active TODO.]_
> **ADR-0037 D4 is UNBLOCKED, not
> decided.** **SD-8 is still NOT RULED** and gates Step 6. Two live obligations
> stand unchanged: **AC-11's RoPA** (Cray's, as controller, before fleet's
> bring-up) and **a typed §8 go per bring-up** (AC-10 clause 2).

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
| 2026-08-12 | **s225 — PLAN-0103 Step 6 SHIPPED (#1138) and nine of eleven ACs CLOSED (#1139, #1141); tests 4007 → 4028.** 🔴 **Verifying an inherited "closed in substance" claim rather than relaying it found two ACs FALSE:** AC-7's own text described an approval the engine refuses (wrong when written), and AC-6 was never closed — the guard its text names had never existed (#1140 built it). **Both fixed, not ticked over.** ⚠️ **AC-10 + AC-11 stay OPEN and nothing left in the PLAN is Code-executable.** Three of STATUS's own claims corrected in place: the G2 scope, D-4's seam count, stream-3's wording | `b229fcd` (head_commit) / [#1138](https://github.com/CrayJThiemsert/vero-lite/pull/1138) / [#1139](https://github.com/CrayJThiemsert/vero-lite/pull/1139) / [#1140](https://github.com/CrayJThiemsert/vero-lite/pull/1140) / [#1141](https://github.com/CrayJThiemsert/vero-lite/pull/1141) / `docs/plans/0103-portal-landing-and-per-system-published-profiles.md` |
| 2026-08-12 | **s224 — RULED (Cray, typed): PLAN-0103 SD-8 = (iii)** — narrative copy in the Act card's place, **Step 6 builds it**; accepted cost: copy with no oracle. 🔴 **The slot's own premise was MEASURED FALSE:** on a *local reproduction* of procurement's committed `published.env`, the Act card renders on **no** published profile (zero inputs on G/F) — suppressed by PLAN-0100 Step 3 *before* SD-8 was authored, so `was an error`, not `superseded by new info`. Four statements corrected inline. 🆕 `view-monitor.js` has zero `isPublished()`, so Tab H's login form renders unconditionally — invisible until **fleet's** bring-up | `853d827` (head_commit) / [#1135](https://github.com/CrayJThiemsert/vero-lite/pull/1135) / `docs/plans/0103-portal-landing-and-per-system-published-profiles.md` §SD-8 |
| 2026-08-12 | **s223 — the MS-S1 secrets-ACL exposure is CLOSED and PROVEN (#1132, #1133), under two typed §8 gos.** **RULED (Cray, typed): tighten as a ladder A → C** (A drops `Authenticated Users`; C also drops `BUILTIN\Users`, granting the signed-in account's SID `(OI)(CI)(RX)`), **canary procurement only**, **recreate `oct-energy` for real** rather than infer from a read-only probe, and **MOVE the leftover `icacls /save` backup into the tightened directory**, not delete it. 🔴 A same-volume move keeps the **OLD** ACL — measured. Each rung believed only on a **force-recreate** (a restart holds the old handle — which is why s222's breakage stayed invisible) + a changed container id + `Registered tunnel connection`; verifier seen RED→GREEN. Gates 4007 / 8 skipped | `b4cb860` (head_commit) / [#1132](https://github.com/CrayJThiemsert/vero-lite/pull/1132) / [#1133](https://github.com/CrayJThiemsert/vero-lite/pull/1133) / `docs/logs/2026-08-12-ms-s1-secrets-acl-tightening.md` |
| 2026-08-12 | 🔴 **s223 — RULED (Cray, typed): J4 ("run the full `tests/` before pushing") stays BINDING, but is evaluated PER ACTION — against the commit(s) being pushed at evaluation time; earlier uncovered pushes are residual gaps, not a standing FAIL.** Rationale: a criterion no future work can turn green is defective, not strict. ⚠️ **R2 CARVE-OUT — do NOT trim this row without rehoming it first:** the ruling lived in a gitignored `goal.json` that has since been DELETED, so this row, the s223 Current Focus block and the s223 handoff are its only homes | s223 Current Focus block / the s223 handoff (gitignored) |
| 2026-08-11 | **s222 cont. — PLAN-0103 Step 10 EXECUTED: procurement is LIVE as published system #2 (#1130, under a typed §8 go); AC-8 + AC-9 TICKED, Step 1 recorded, ADR-0037 D2.7 discharged, F4's premise corrected BY MEASUREMENT and ADR-0035 OQ-4's dead trigger retired (#1127); s222's four unhomed findings REHOMED — Lesson #0040, a Lesson #0029 addendum, two runbook entries (#1131).** 🔴 ADR-0036's "the apex domain appears nowhere in this repo" was FALSE — corrected, then moved INLINE (#1128, #1129). ⚠️ **ADR-0035 OQ-6 is OPEN** (does D1(3)'s documentary clause govern evidence documents? three options, none recommended). **RULED: correct the ADR, do not edit the archived PLAN; keep `API_KEYS` on procurement** | `bd43d67` / [#1127](https://github.com/CrayJThiemsert/vero-lite/pull/1127) / [#1130](https://github.com/CrayJThiemsert/vero-lite/pull/1130) / [#1131](https://github.com/CrayJThiemsert/vero-lite/pull/1131) / `docs/logs/2026-08-11-plan0103-step10-procurement-bring-up.md` |
| 2026-08-11 | **s222 — PLAN-0103 AC-8 clause 2 CLOSED in substance and ADR-0037 D2.7 MEASURED (#1124): no visitor-typed case text in the audit chain, `case_id` recoverable, asserted over EVERY `audit_log` row on both the ordinary and the waiver→ratify paths, via a positively-controlled bracketing sentinel + a structural payload-key allowlist.** ⚠️ `WaiverInvocation.justification` and the ratify `note` ARE human free text by design — possibly its own RoPA line. 🔴 #1125 retracted a false claim (a middle-slice leak IS invisible to both oracles) and records **RULED (Cray, typed, s222): that residual risk is ACCEPTED**, revisit condition stated in place. ⚠️ **D4 is UNBLOCKED, NOT decided**; the AC checkbox is NOT ticked — owed to a `plan-drafter` dispatch _(corrected s225: **not** G2, which fires only on a numbered artifact that does not yet exist)_ | `3a11e87` (head_commit) / [#1124](https://github.com/CrayJThiemsert/vero-lite/pull/1124) / [#1125](https://github.com/CrayJThiemsert/vero-lite/pull/1125) / `tests/api/test_visitor_case_to_monitor_scenario.py` |
| 2026-08-10 | **s221 cont. — PLAN-0103 Steps 7 and 8b SHIPPED (#1122, #1121), so AC-8's first clause and AC-9's evidence are complete; #1123 made `render-handoff` report live goal state.** 🔴 **RULED (Cray, typed): NO portal REPO will be created** — Step 1's answer, unrecorded through three sessions. ⚠️ The portal/landing surface **still EXISTS**: DNS, Access policies and the landing surface are configured in the **Cloudflare dashboard**, one `oct-<vertical-id>` subdomain label per system; **ADR-0036 D2's two-artifact price is unchanged** — dashboard config, not repo files. The Step 8b request is **parked, not sent**, and the landing page is built by nobody. Also ruled: **Step 7 before Step 6**, and SD-8 ruled before Step 6 is built | [#1121](https://github.com/CrayJThiemsert/vero-lite/pull/1121) / [#1122](https://github.com/CrayJThiemsert/vero-lite/pull/1122) / [#1123](https://github.com/CrayJThiemsert/vero-lite/pull/1123) / `docs/logs/2026-08-10-plan0103-step8b-portal-assembly-request.md` |
| 2026-08-10 | **s221 — energy's LIVE system MIGRATED and PLAN-0103 Step 9 headroom MEASURED (one typed Cray §8 go); Step 8a SHIPPED (#1119) so AC-3 CLOSES, and the self-citation TODO DISCHARGED (#1118).** The demo now runs as compose project `oct-energy` on `oct-energy_vero_oct`; `vero-published` is gone from the host in every form. The prompt log was verified **byte-identical on both sides** (per-file checksums) and the app proven able to **write** it as its non-root user — refuting the s215 silent-`OSError` mode, not assuming it absent. 🔴 **#1119 repaired a compose build context that could NOT build** — `context: ../..` was one directory short of the repo root, and `docker compose config --quiet` validates schema, not context, so "all three composes validate" had been reported while none could build. ⚠️ **Step 9 is MEASURED; AC-10 is NOT closed** (clause 2 = an explicit go per bring-up) and **ADR-0036 OQ-2 stays OPEN** — capacity was never its constraint. ⚠️ **AC-9 is NOT closed**: Step 8b still owed. Read the log, never a restatement | `e938cf6` (head_commit) / [#1119](https://github.com/CrayJThiemsert/vero-lite/pull/1119) / [#1118](https://github.com/CrayJThiemsert/vero-lite/pull/1118) / `docs/logs/2026-08-10-oct-energy-migration-phase2-and-step9-headroom.md` |
| 2026-08-10 | **s220 cont. — PLAN-0103 Steps 4b + 5 COMPLETE (#1116): fleet's profile + allowlist landed, so all three per-system profiles now exist.** `oct-fleet-maintenance` publishes `A,C,F,H,I,J` default **A** — the only system with BOTH personas (LOCKED-5) and a database (LOCKED-1/ADR-0037): postgres on its own network + volume, **no `ports:`**, both credentials required host-env pass-throughs. **21 allowlist rows, each re-admission on its own written basis** (I/J's DB-less basis dissolves; Tab H's five were never a storage question). Fleet's landing tab needed the DOA ฿5,000 ceiling as its recommender threshold, not energy's 90.0. 🔴 **AC-3 is NOT closed — the card copy exists for no system** (Step 8a). Evidence: 3971 → 3994 (+23), 9 probes, all three composes `docker compose config --quiet` exit 0 | `f78068e` (head_commit) / [#1116](https://github.com/CrayJThiemsert/vero-lite/pull/1116) / `docs/plans/0103-portal-landing-and-per-system-published-profiles.md` |
| 2026-08-10 | **s220 — PLAN-0103 Steps 4b + 5 SHIPPED (#1114): procurement has a published profile of its own (`G,F`, default `G`, **no personas** per SD-3/SD-4, DB-less), and per-system isolation became a GUARDED property** — compose project `name:` == the profile **directory** (guard-asserted), the fixed network `name:` **dropped** so compose scopes it per project, and 45 new tests assert no committed file outside a profile names two `oct-*` labels. Energy renamed `vero-published` → `oct-energy`. **AC-4 + AC-5 CLOSED.** 🔴 **The rename does NOT follow the LIVE stack** (measured `running(2)`, host checkout at `00ddca0`) — a data migration is owed before energy's next redeploy; see the Active TODO, not this row | `0acc4af` (head_commit) / [#1114](https://github.com/CrayJThiemsert/vero-lite/pull/1114) / `docs/plans/0103-portal-landing-and-per-system-published-profiles.md` |

## In-Flight Discussions

- **OPEN QUESTION for Cray — does a skill's registry table *bind*? (raised by s210's closing notice, recorded here s209 cont.; Code's observation, NOT a ruling and NOT a defect.)** The notice asserted that the four-work-stream registry table in `.claude/skills/stream-status/SKILL.md` (#1062) is **canonical**, and that a carrier-artifact change must update it **in the same PR**. The registry as *reference* is unobjectionable; the **same-PR obligation** is the part that would have to live in `CLAUDE.md` or an ADR to bind — `CLAUDE.md` §1 places `.claude/skills/` at **Tier 2.6, derived, carrying no independent precedence (ADR-0017 D6)**, and §4 draws the bright line that *"a binding rule never moves into a skill (a skill that fails to trigger would silently drop it)"*. Cray's call: promote the obligation into a canonical, or keep the table advisory.
- **PLAN-0096 — COMPLETE 12/12 and ARCHIVED (s193); FOUR RESIDUAL RISKS OUTLIVE IT** (which is why this entry is a pointer and not a deletion): **RR-1** (per-baht approver→case attribution is INFERENCE, not data — silently wrong the day two approvers share a gate resolution), **RR-3** (concurrency-race coverage — both named gaps CLOSED s195 by #995), **ศูนย์ต้นทุน ships EMPTY** (partner granularity unanswered — also an open Active TODO below), and **`latest_per`** still collapsing two open cases on one truck (**Cray typed (ค) defer** — the older case reports as *ungoverned*, indistinguishable from a governance failure). Read the archived PLAN, not a restatement: `docs/plans/done/0096-fleet-flow-completion-phase1.md` (§Verification preamble + §Acceptance Criteria for RR-1 / RR-3 / ศูนย์ต้นทุน; §Step 8 for `latest_per`).
- **COMPLETE-and-ARCHIVED, no live remainder here — read the archived PLAN, never a restatement:** **PLAN-0095** (Docker image boot, s177 — its OQ-1 hosting model CLOSED by ADR-0035) · **PLAN-0094** (L1 loop-detect restructure, s183 — its OQ-4 is ANSWERED; see the PLAN-0102 row in Active TODOs) · **PLAN-0093** (LLM-arm degrade disclosure, s172 — **no follow-on owed**) · **PLAN-0091** (narrative→vertical scaffolder, s168 — two named follow-ons, **neither scheduled**, both greenfield/human-call) · **PLAN-0088** (cross-run read substrate + the four run-insight readers, s171 — **three AC-WORDING debts, none a code defect**) · **PLAN-0036 + PLAN-0037** (Fastenal procurement vertical Stage 1 + the Stage-2 facet retrofit, s76 — `Status: Done`; demo target = Fastenal Thailand, **pitch = asset-ontology-triggered governed sourcing**, NOT the commoditized "governed"/"cross-vertical" claims). Each record is in `docs/plans/done/`; the s168→s193 retrospectives these bullets used to carry are rotated to `docs/status-archive/`.
- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13; verdict **continue-with-adjustments**. Runs 1 (energy, s93) + 2 (supply-chain, s94) both COMPLETE, all S-checks PASS against pre-committed oracles, no R-PS trigger fired; C-1..C-3 CONFIRMED → **no open partner-sim debt**. ADR-011's audit stays gated on a REAL partner conversation (R3: SYNTHETIC provenance INFORMS but never TRIGGERS it). Full record: `docs/adr/0020-*.md` + the gitignored run packages under `docs/research/private/`.
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm — **not yet drafted**, and it needs a fresh ADR number. _[The old "≥ ADR-014" floor recorded here was **moot** — see the Active TODO below, corrected s141: ADRs now run past 0032 and `0014-WITHDRAWN.md` exists. Kept as one pointer rather than two divergent copies.]_
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **The autonomy fork — Stop-hook misfires: CLOSED s167.** Resolved by **option A′** (Cray, typed) and shipped the same session — the `dispatch` verdict is a **suggestion, not an order** (#870/#871). Final ledger: **14 misfires / 0 valid fires**. **The whole argument is settled history in `docs/plans/done/0092-stop-hook-dispatch-arm-demotion-to-suggestion.md` — do not restate it here.** Live remainder: only **option (e)** (flip the classifier backend from local Ollama `gpt-oss:20b` to Sonnet), **deferred**, its API-key/org fail-closed probe unrun.

## Active TODOs

- [ ] **PLAN-0103 — vero-lite's side of the multi-vertical portal. DRAFTED s218 (#1101), `Status: Draft`; Steps 2, 3, 4a, 4b, 5, 7, 8a and 8b are SHIPPED.** _[Corrected s221: this row opened "nothing built" from s218 and stayed that way for three sessions while its own body listed six shipped Steps — a header that contradicted its own contents.]_ ADR-0036's D6 follow-on: per-system published profiles + the landing/framing **content spec**. 10 Steps, 10 ACs, **7 SD slots**. ✅ **ALL EIGHT SLOTS RULED s218 (#1104)** — read them in the PLAN's §Surfaced decisions, each stamped `RULED (Cray, typed, s218)`. ✅ **ADR-0037 RATIFIED s218 (#1107), so nothing gates execution any more** — the whole PLAN is startable. 🔴 **One live obligation instead of a gate: AC-11 — the RoPA must cover fleet's posture BEFORE fleet's bring-up, and it is Cray's artifact as controller (the PLAN gates on it, cannot author it).** The Step-4 map that used to separate gated from ungated now reads as bring-up ORDER, not permission. Step 4 carries a **gate map** naming exactly what proceeds regardless — procurement's entire half, Steps 2–3, energy's move, Step 8's content, Step 9's measurement. It is written "read this before stalling anything" because a bare "ADR-gated" label reads as stop-everything: s206 lost a session to that misreading of PLAN-0100's headline when six items carried no gate. ⚠️ One caveat the map itself carries (Code R2): the **persona-picker UI is not gated but fleet is its only consumer**, so it is orphaned work if ADR-0037 ratifies otherwise than proposed — build it in parallel, never first. **Read the PLAN, never a restatement:** `docs/plans/0103-portal-landing-and-per-system-published-profiles.md` (§The hard boundary · §Surfaced decisions). ⚠️ Two things a future reader must not re-derive: the **hard boundary** — ADR-0036 D1 + ADR-0035 D4/L5 make the `portal.` landing surface, ingress map, Access policies and domain **portal-repo property**, so this PLAN builds no landing page here and ships a spec instead; and `isPublished()` has **ELEVEN consumers across eight files**, so any step touching published-ness must walk all of them (`tools/excision_scope.py` + the `excision-scope` skill). _[Corrected s219 by executing Step 2, `was an error`: the census is **9 call sites**, not 11 — the 11 counted an `app.js` `PUBLISHED_EXCLUDED_VIEWS.indexOf` line, which is not an `isPublished()` site, and AC-2's own list enumerates 10 with the definition among them. Exactly **one** was tab-set; the other eight gate on the published *profile* for allowlist reasons. `tools/excision_scope.py` also does **not** apply to a JavaScript target — it is Python AST analysis, so walk-both-ways went by hand.]_ ✅ **Steps 2 + 3 SHIPPED s219 (#1109, #1111)** — the constant is gone, replaced by a boot-validated per-system declared view set, and `_FALLBACK_VERTICAL` is closed (a heroless vertical now 404s instead of being served procurement's hero). **AC-1 and AC-2 are both CLOSED** — AC-2's first clause by #1109, its second (the branch audit) by #1111. _[Step 3's own text named the wrong audit targets — the third doc-vs-code mismatch in this PLAN: `view-flow.js` is Tab D and was published all along, and `view-monitor.js` has no `isPublished()` at all. Corrected scope + the measured property are in #1111's body.]_ ✅ **Step 4a SHIPPED s219 (#1113); Steps 4b + 5 HALF SHIPPED s220 (#1114)** — energy moved to `deploy/published/oct-energy/`, procurement's own profile authored at `deploy/published/oct-procurement/` (published set `G,F`, default `G`, **no personas** per SD-3/SD-4, DB-less), and per-system isolation is now guarded by `tests/deploy/test_published_profiles.py` (45 tests). **AC-4 and AC-5 are both CLOSED** as guarded properties a third profile inherits automatically. ✅ **Steps 4b + 5 COMPLETE s220 (#1116)** — `deploy/published/oct-fleet-maintenance/` authored (published set `A,C,F,H,I,J`, default `A`, **both personas** per LOCKED-5, **with** the LOCKED-1/ADR-0037 Postgres: own network + volume, no `ports:`, both credentials required host-env pass-throughs), plus a **21-row allowlist in which every re-admission carries its own written basis** — I/J's DB-less exclusion *dissolves* for a DB-granted system, while Tab H's five routes were excluded by default-deny + SD-1's C-3, which is not a storage fact, so each is admitted on its own merits. The guard module now collects **68** tests (was 45); two new guards (ADR-0037-granted-only DB, asserted both directions; credential env values must be required pass-throughs). ✅ **Step 8a SHIPPED s221 (#1119) — AC-3 is now CLOSED.** It required **five** committed artifacts per profile — `{docker-compose.yml, published.env, cloudflared/config.yml, README, card copy}` — and the fifth, `card-copy.md`, now exists in all three profiles, bilingual TH/EN, structurally guard-asserted. 🔴 **The same PR repaired a compose build context that could not build:** `context: ../..` from `deploy/published/<system>/` reaches `deploy/`, one directory short of the repo root, and all three profiles inherited it from Step 4a's move — while `docker compose config --quiet` returned 0 over all three, because it validates the **schema**, not whether the context resolves. Now `../../..`, guarded. ✅ **Step 9 MEASURED s221** under Cray's typed §8 go — **AC-10's first clause is discharged; AC-10 is NOT closed**, its second clause (every bring-up carries its own explicit §8 go) stands — and ⚠️ **ADR-0036 OQ-2 remains OPEN**: container capacity was never its constraint. 🔴 **AC-9 is NOT closed** — its second clause, the portal-side assembly request (Step 8b), is still owed and is a Step 10 input. ✅ **Steps 7 + 8b SHIPPED s221-tail (#1122, #1121); AC-8 clause 2 CLOSED s222 (#1124) and AC-9's evidence complete — both in SUBSTANCE only** (see AC bookkeeping). The s221 "no-op that reads like a fix" hazard is **discharged**: the `main.py` seed gate now branches on `fleet_maintenance`. Detail is in the s222 Current Focus block and the artifacts, not restated here. 🔴 **Step 1 ANSWERED (Cray, typed): no portal REPO will be created** — ⚠️ in full, because the shorthand has been misread as "no portal": the portal/landing surface **still exists**, with DNS, Access policies and the landing surface configured in the **Cloudflare dashboard**, each system on its own `oct-<vertical-id>` subdomain label; **ADR-0036 D2's two-artifact price per system is unchanged** — dashboard config rather than repo files. ⚠️ The Step 8b request is **parked, not sent**, and **the landing page itself has been built by nobody**. ✅ **Step 6 SHIPPED s225 (#1138)** — fleet's three-persona picker plus SD-8(iii)'s narrative copy where Tab G's Act card would be (15 files, +1062; tests 4007 → 4025), built on the s224 ruling. _[Corrected s225: this clause read "**Remaining: Step 6**" and carried two facts for a build that has since happened — and one of them, "`view-monitor.js` has **zero** `isPublished()`", is no longer true: it now has exactly **one**, the picker branch, so the published branch SD-4(b) presumed **exists**.]_ **Remaining: Step 10's last bring-up** — ✅ **procurement went LIVE s222-tail (#1130)** under a typed §8 go, so only **fleet** remains, gated on AC-11's RoPA (Cray's to author) **plus its own typed §8 go** (AC-10 clause 2). ✅ **Both obligations Steps 4b/5 left owed are DISCHARGED s221** — energy's live-system migration ran, and the stale self-citations were corrected by #1118; see the two rows immediately below. ⚠️ **AC bookkeeping:** **AC-8 and AC-9 are TICKED on disk** (`[x]`, #1127) — the `plan-drafter` dispatch this row used to owe has LANDED. _[Corrected s223, `was an error`: the row still read "the PLAN's checkboxes read `[ ]` for all eleven ACs" and "the tick is owed to a `plan-drafter` dispatch" after #1127 had discharged both; caught by checking the PLAN's own checkboxes rather than this record.]_ ✅ **s225 — AC-1 through AC-9 are now CLOSED** (#1139 closed AC-1..AC-5 and AC-7 and recorded Step 6's execution; #1141 ticked AC-6 once #1140 had built the guard its text names). **Only AC-10 and AC-11 remain `[ ]`**, and `Status:` is still `Draft`. 🔴 **Two of that batch were VERIFIED rather than relayed, and both were FALSE:** AC-7's own text described an approval the engine refuses — wrong from the moment it was written, not drifted into — and **AC-6 was not closed at all, the guard its text names never having existed**. Both were **fixed rather than ticked over**. ⚠️ **Nothing remaining in this PLAN is Code-executable:** AC-11 (Cray authors the RoPA, now homed at `docs/compliance/ropa-change-statement-fleet.md` per #1137) → fleet's typed §8 go → Step 10's bring-up → AC-10. _[Corrected s225, `was an error`: this sentence read "The other nine ACs remain `[ ]`, and Code cannot edit `docs/plans/` (G2 gate), so every further tick is a `plan-drafter` dispatch." **Both halves were false.** G2 does **not** gate an existing PLAN — it fires only when a numbered artifact does **not yet exist**, because creating one consumes a number; G1 is scoped to `docs/adr/` with `Status: Accepted` and never touches `docs/plans/`. Routing `docs/plans/` through the drafter is still right — by the **ADR-009 D1 convention** plus the advisory Stop classifier, a convention rather than a gate.]_
- [ ] **The ฿ realized-vs-projected join — RECORDED ON ITS MEASURED BASIS, because the version circulating in session notes is PARTLY FALSE and it was ranked #1 next work on the strength of the false part.** ✅ **True:** the realized side already carries `total_thb` and `run_id` on the **same** `ExportRow` (`services/db/repair_spend_export.py`, linked via `RepairCaseRunLink`), so **no migration is needed**. 🔴 **False as circulated:** that `benefit_rollup` in `services/db/run_analytics.py` "already extracts `net_benefit_thb` by `run_id`". It does **not** — it aggregates by currency × procedure × facet-kind × day and touches `run_id` only inside a `count(distinct …)`, so it yields **no per-run figure at all**. **Therefore the join needs a NEW per-run aggregation, not a reuse of `benefit_rollup`'s output**; the `GROUP BY run_id` pattern to copy is the per-run SUM inner subquery in that same module. The work may still be small — but the circulating **"~40 lines by reusing `benefit_rollup`" framing was CHECKED and is WRONG**, so re-price it before scheduling rather than inheriting the estimate. Lands on **Tab J**, which fleet publishes.
- [ ] **Demo-key rotation cadence — CRAY'S, posture not code.** Fleet's README documents how to **generate** a persona key pair but says nothing about **when to rotate**. Measured s225: `git grep -i -e rotate -e rotation` under `deploy/published/oct-fleet-maintenance/` returns **zero** matches. The keys are served to the browser by ruling, so they are **public the moment fleet is reachable** — which makes the cadence a real posture question rather than a nicety. No code change is implied; the answer is Cray's.
- [ ] **Ungated items rehomed s219 out of the `next_action` frontmatter — they survived ONLY there, and R3 caps that field to one short line.** (1) ✅ **PLAN-0103 Step 9's MS-S1 headroom is MEASURED s221** (`docs/logs/2026-08-10-oct-energy-migration-phase2-and-step9-headroom.md`) — RAM and CPU do not constrain a second or third published system, and AC-10's first clause is discharged. ⚠️ **ADR-0036 OQ-2 does NOT follow from it and remains OPEN:** the aggregate in-flight LLM posture is a different question — the constraint on a second *assisted* system is the resident model and concurrent in-flight calls, not container footprint — and one term in the projection (Postgres idle) is declared unmeasured rather than folded silently into the total. (2) **The public one-pager — never drafted.** (3) **ADR-0037 D4's FINAL ruling is still Cray's — now UNBLOCKED, still UNDECIDED.** It was deferred until D2.7 measured whether visitor case text reaches the audit chain; **s222 MEASURED it (#1124): it does not, on both the ordinary and the waiver→ratify paths, and `case_id` stays recoverable** — so the precondition is discharged and the ruling is not. ⚠️ One input D4 must price that the measurement surfaced: `WaiverInvocation.justification` and the ratification `note` **are** human free text in the hash-chained log by design — a named internal principal's, not the visitor's — which may need its own RoPA line. ⚠️ And the one hole the oracles do not close, **ACCEPTED (Cray, typed, s222)**: a middle-slice carrier is invisible to both; revisit if an audit payload gains a field legitimately holding a SLICE of operator-entered text. (This is the durable home; the Recent Decisions row rotates.) (4) **Edge cache-purge needs a Cloudflare API token = a new secret + host-state**, which is why the purge step in the PLAN-0100 row below is not simply "add a step". _(The remainder of that field — D-4 option (a)'s seam count in `nl_query.py` (⚠️ **eight or more**, not the "four seams" this line used to say; corrected s225 in the PLAN-0100 row, which holds the measurement), versioned font URLs, the unpinned `OLLAMA_KEEP_ALIVE` — is already homed in the PLAN-0100 row and is not duplicated here.)_
- [ ] **PLAN-0100's residuals outlive the PLAN** (COMPLETE 13/13 and ARCHIVED s216; the demo is LIVE, REDEPLOYABLE and DRIVEN). **Read the archived PLAN, never a restatement:** `docs/plans/done/0100-exposure-published-demo-surface.md` (§"Step 11 closure verdict"; §"Defects the live run found" for D-1..D-5, incl. the *transient* D-5 Safe-Browsing flag on the Access login callback, cause UNDETERMINED; §Instrument failures). _[s222: the completion narrative is dropped per R2's ratified Active-TODO rule — `[x]` items older than the session window go, git history + the archived PLAN hold them. Only the live residuals stay.]_ **Live, and recorded ONLY here:** (1) **D-4 RULED s217 (Cray, typed): option (a), teach the engine — nothing built, no PLAN drafted, still the largest ungated Code item.** ⚠️ Its price was corrected (`was an error`): every prior record framed (a) as "teach the translator `group_by`", implying open-ended prompt work, but `group_by` already works for `max`/`min`/`avg`/`sum` — what is unrepresentable is **`count` WITH `group_by`** (`_AGGREGATE_OPS` excludes it in `services/engine/nl_query.py`, and the validator rejects the pair outright). 🔴 **That corrected price was ITSELF an undercount — "four seams in one file" is wrong (`was an error`, s225).** Measured in the same module: `group_by` is touched at **eight or more** sites, and the decisive one the old count omitted is the **system prompt**, which instructs the model *"If you set aggregate_property or group_by, operation must be max/min/avg/sum (never list/count)"* — **so relaxing the validator alone changes nothing, because the model is told never to emit the combination.** The rest: a second prompt site, the property check, aggregate collection, group labelling, `_infer_group_by`, and the rewrite seam. ⚠️ Add that `benchmarks/nl_query_feasibility/gold.yaml` and the A/B fixtures may need **re-recording on MS-S1** — a §8 host-state go. **Re-price before scheduling; "≈ one PR + tests" rested on the four-seam count.** (2) **No cache-purge step or versioned font URLs** in the redeploy runbook — nothing in the pipeline purges the edge and `?v=cNN` does not reach fonts; a purge needs a Cloudflare API token = a new secret + host-state. (3) **`published.env` pins no `OLLAMA_KEEP_ALIVE`**, so the published surface silently inherits the code default of 30m.
- [ ] **Assembly-cost axis — MEASURE it before an ADR argues it (Cray typed s197); nothing built, no PLAN drafted.** Build the tripwire that puts a number on assembly cost first, *then* draft the ADR on top of that number — the ordering is the ruling. **The series measured so far is banked HERE because it is banked NOWHERE ELSE in the repo — no test, no doc, no PLAN holds it:** churn per vertical went **1:1.8 → 1:6 → 1:1.1**, i.e. **spiky, not falling**, which is the shape any ADR on this axis has to argue against. Left unbanked it survives only in session memory and dies at the next context reset; a tripwire that recomputes it is what makes it evidence rather than a recollection.
- [ ] **Seam-scoped mutation-testing CI — a PLAN candidate, NOT built.** Surfaced s188 as the one CHECKABLE variant the scenario-test hook rejection does not cover; **rehomed here s191** when its parent `[x]` row was pruned, because STATUS was its only home. A CI job that requires the scenario suite to REDDEN under a seam mutation: ritual compliance cannot fake it, since an empty or stubbed scenario suite stays green under mutation — exactly what a file-existence hook would miss. Rationale: `CLAUDE.md` §8's scenario-test bullet.
- [ ] **PLAN-0096 partner round-2 — ANSWERED s189; five of seven closed, one non-blocking follow-up open.** A1 → Step 6 built (#965); A3 → `pm_due` built (#968); **A4 + A7 confirmed values already shipped** (flat ฿5,000 ceiling, `"30001"` inclusive floors); A5 **parked** — no real Wialon export exists yet. **A2 is answered and consumed by Step 8** (no longer a gate). **Open, NON-blocking: cost-center (ศูนย์ต้นทุน) granularity — per truck or per company?** Ship the column, fill the rule when it lands. A6 is answered but is a Step 9 *runbook* item. Detail: `docs/plans/done/0096-fleet-flow-completion-phase1.md`.
- [ ] **The AT-2 extraction — only the F-FACTORY half remains, owned by PLAN-0076 T1.** The criterion-vocabulary half SHIPPED as PLAN-0087 (COMPLETE 8/8, ARCHIVED — #840/#841); ADR-0025 D7's generator deferral was CANCELLED at N=4 (Cray-ratified, typed); SD-1 = (a) keeps the procedure-aware `ExecutorFactory` half with PLAN-0076 T1, guard `test_at2_extraction_obligation_is_owned` ARMED. Full detail: `docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` + `docs/plans/0076-*.md` §A.
- [ ] **PLAN-0075 follow-ons — homed by PLAN-0076 (`Status: Tracking`, #752, s133).** T1 (ADR-0031 D3 gate-plugin seam, F-FACTORY) is PARTIALLY discharged — the criterion-vocabulary half shipped as PLAN-0087; the procedure-aware-`ExecutorFactory` half stays OPEN here. T2's F-PIN remainder CLOSED s143 (#784), but **F-PIN itself stays OPEN**, so PLAN-0076 does NOT archive and its AC-6 presence guard stays ARMED. Full detail: `docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` §A. _[s225 — the stream-3 (primitives) shorthand **"ZERO ratified ACs/Steps"** is **false as worded** and is corrected here, which is the only place in STATUS that describes this PLAN's shape: it carries **six ACs (AC-1..AC-6) and four Steps (T0–T3)**. They are stub-level and none directs a build — T0 is explicitly "the only work this PLAN itself does" — so the accurate claim is **zero ratified ACs/Steps THAT DIRECT A BUILD**. The substance is unchanged: nothing here is Code-executable.]_
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2) — open ONLY for the O-2 residue.** Every other leg is DONE + archived (PLAN-0046/0048/0061/0062/0066–0068/0070/0071/0073 → `done/`). **The one OPEN residue:** procurement's `intake` migrated only **PARTIALLY** — the derived fields ALREADY moved to declared `transform` ✔ (PLAN-0078 PR-1 #762, AC-2 ticked), so what is left is **only the cardinality-changing `candidate_quotes` nest**, which is explicitly Out-of-Scope there. *[Corrected s175 by the #921 grounding sweep, `was an error`: this entry said production execution stays `_SeedQuery` "for derived fields" — it does not; the derived fields are migrated and the reshape is the sole residue.]* Full detail: `docs/plans/done/0062-per-vertical-seed-migration.md` §SD-C (the co-exist decision + its STOP-and-surface tripwire) + `done/0078-*.md` §L-3 and its Out-of-Scope, where the residue is walled in.
- [ ] **Bounded/incremental chain verification (PLAN-0063 SD-4 follow-up, s118).** `GET /audit/verify` walks the WHOLE chain O(n) on demand — accepted at pilot scale. Future work = a checkpointed head / verify-since-anchor design; anchor storage ≈ external anchoring — **do not build without re-reading the tripwire** in `docs/plans/done/0063-audit-chain-verification-surface.md` + the `services/api/routers/audit.py` module docstring (SD-4). _[Note: the docstring's "ADR-011 boundary" is an EARMARK — `docs/adr/` jumps 0010 → 0012.]_ *(#688/#690)*
- [ ] **Rock 4 — s84 deep research DELIVERED → O-sequence locked.** Cray locked **O-1 → O-3 → O-2 → O-4**. **O-1** (Box-4 ฿ pitch) **DONE** · **O-3 = ADR-0025 Accepted** · **O-4 = PARK** (agent-interop; `docs/adr/0032-*.md` D4 — option-only, un-park = a counterparty's *written* pull). **Remaining: O-2 only** (economic-impact facet + Q3 data-binding = Rock 3). Full detail: `docs/adr/0025-at2-managerial-layer.md` (O-sequence + Box-3 fit + the **evidence-asymmetry** finding rehomed s142). *(s84 Cray ask)*
- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten. **Full table (all six rows + their triggers + where each lands): `docs/plans/done/0005-oct-engine-runtime-layer.md` §8.1** — which itself instructs this STATUS entry to be a pointer. *(per Cray note 2026-05-21)*
- [ ] **PLAN-004 Phase C — OPTIONAL POLISH (forward-declared; "may never land"):** HTML/markdown handoff dashboard under `docs/` + references-graph (mermaid dispatch chains) + `render_transcript.py` unified session export (PLAN-0004 §"Phase C"). *(Phase A + B both COMPLETE — session 35; the prior TODO's validator **warning-swallow bug was FIXED #312**, s58. Minor never-formally-scoped sub-ideas — README/`_rename-map` walk-exclusion, Cat G `references_*` autofix, OQ-2 effective-vs-authored `status:` dashboard flag — fold in only if Phase C lands. Reconciled 2026-06-16 s65 audit.)*
- [ ] **Custom Postgres image with extensions (pgvector / AGE / pg_trgm) — needs a fresh ADR number + a PLAN; neither drafted.** *[Corrected s141: **PLAN-002 does not exist** ("NOT yet drafted", `docs/plans/done/0005-oct-engine-runtime-layer.md`), and the old "≥ ADR-014" floor is **moot** — ADRs now run to 0032 and `0014-WITHDRAWN.md` exists.]* Context: **`docs/adr/0013-autonomy-axis-relocation.md`** (the floor-bump note) + **`docs/plans/done/0005-*.md`** (trigger: semantic + graph features).
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] **CLAUDE.md follow-up extraction pass (s181 option b): new Cowork dispatch; target < 20 KB (~18 KB / ~225–235 line floor).** Candidates (Cowork fresh-eyes, s181 completion §6): §11 ¶3 restates the §6 E2 rule → one-line pointer; §10 skills-row annotation duplicates §4's Tier-2.6 row (in-file ADR-0017 D6 drift); §10 docs/logs row's PLAN-004 parenthetical; §9 halves; §3 folds into §1. Materials: `.claude/handoffs/session-181/` (gitignored). **PARKED s183 by Cray — the dispatch stays UNSENT until two things are settled, and s183 grounded both.** (1) **The unit of `< 20 KB` is load-bearing and unpinned:** `CLAUDE.md` measures **21,524 B / 261 lines**, so the target needs **1,044 B** cut against 20 KiB but **1,524 B** against decimal 20,000 — Cray was asked and declined to rule for now. (2) **The five named candidates cannot reach either target:** measured at **~930–1,000 B** combined, and the row's own "~225–235 line floor" needs **26–36 lines** removed where the five move **~7** (candidates 1–3 are in-line trims that shorten bytes without deleting lines). The genuinely large blocks — `CLAUDE.md:112` (~1,100 B), `:153` (~700 B), `:73` (~800 B) — are **not on the list**. Sending this dispatch as written would repeat the s181 failure of a target that is arithmetically unreachable in scope. ~~Batch the two standing CLAUDE.md defects into whatever dispatch eventually goes out~~ — **DISCHARGED s188**: both rows below are closed, batched into the s188 three-edit Cowork round-trip. _[s188 — **the arithmetic moved AGAINST the target and the row must not be read at its old numbers.** `CLAUDE.md` is now **22,424 B** (+900 B: the §8 scenario-test rule +569, the §6 gate-claim correction +261, the §7 link resolution +70), so the cut needed is **1,944 B** against 20 KiB or **2,424 B** against decimal 20,000 — roughly **double** what this row was written against, while the five named candidates still measure only ~930–1,000 B. Note also that `:112`, one of the three "genuinely large blocks" this row says are **not** on the candidate list, is now ~260 B larger. The growth is Cray-ratified binding-rule substance, not padding — which is the point: **the target and the constitution are pulling in opposite directions, and that is the decision this row is actually parked on**, not the unit question alone.]_
- [ ] **PLAN-0102's two residues outlive the PLAN** (retire L1 loop-detect — COMPLETE 11/11 and ARCHIVED s217, #1096; L1 is gone from all four hooks, L2/L3/L4 intact and asserted so). **Read the archived PLAN, never a restatement:** `docs/plans/done/0102-retire-l1-loop-detect.md` (§Context for the measurement + the s180 "0 denies" correction to a **≥ 56** floor; §Governance; §"Corrections found by executing this PLAN"). _[s222: completion narrative dropped per R2's ratified Active-TODO rule; residues kept per its carve-out.]_ **Both non-gating and recorded ONLY here:** (1) **`observe()` is now callerless and was deliberately kept** — deleting it turns `_record`'s `bump` into a constant and pulls a refactor into the function every surviving L2/L3/L4 increment flows through; revisit only if that module is reworked anyway. (2) The **forwards-call-graph gap** behind all three PLAN defects is a *method* fix owed to the next excision PLAN, not a code fix — no artifact carries it yet.
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
