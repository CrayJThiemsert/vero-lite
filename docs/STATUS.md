---
last_updated: 2026-08-17T21:10:00+07:00
session: 235
current_batch: "s235 — s234's Tab I clip generalised into law: a five-specialist audit, ADR-0038 RATIFIED (5 classes binding, 4 SDs ruled), CLAUDE.md +4 rules, PLAN-0107/0108 drafted. EIGHT PRs, #1193–#1200."
current_actor: code
blocked_on: "NOTHING blocks repo work; main is green and carries no known defect. ADR-0037 SD-1 (the D2.1 authorship fork) stays Cray's — unruled across four sessions; until ruled, D2.1 as written governs."
next_action: "Ratify PLAN-0107, then execute Phase A (zero-new-dependency work). Cray's: ADR-0037 SD-1. Code-side: PR-B's carve-out rehome — 11 rows, enumerated s235."
head_commit: 218a521
recent_commits: [218a521, 989e40a, f6cf8d3, f452e8a, 3b34b13, 6642fe7, b2327b0, c43cb3b, 364f055, f576af2]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 235, 2026-08-17 (head_commit `027986e` → `218a521`) — EIGHT PRs
> MERGED (#1193–#1200), 0 open. s234's Tab I clip was asked to generalise beyond
> UI, and it did: a five-specialist audit turned one 305px defect into a measured
> failure-class census, ADR-0038 made five classes BINDING, and `CLAUDE.md`
> gained FOUR new rules — in one session.**
>
> 🔴 **The organising law the whole session turns on:** an oracle sees a defect
> only when three independent conditions hold — **① an INSTRUMENT can read the
> artifact · ② the test DATA can reach the failing state · ③ someone ARMED it as
> a gate rather than as evidence.** The weakness is **not** UI-specific and is
> **not** a missing test; it was failing silently across two of the three
> Phase-1 OCT features.
>
> ✅ **ADR-0038 RATIFIED** (#1195, #1197) — the three-strike promotion rule for
> advisory lessons, the census, D2's per-class enforcement forms, D5's demotion
> path. **All four surfaced decisions RULED** (Cray, typed); its OQ-5 resolved to
> the PLAN template rather than a build task (#1198). **Read the ADR, never a
> restatement:** `docs/adr/0038-advisory-lesson-promotion-three-strike-rule.md`.
>
> ✅ **`CLAUDE.md` BOUND — four new rules, +314 words / +1,852 B, zero new
> sections** (#1200): a load-bearing green is not evidence until its assertion is
> **witnessed RED** in the direction it claims · an **expected-value set is not
> an oracle of the system** until the system's own output is scored against it ·
> an **inherited premise a decision rests on is a claim, not context** · **name
> the rule's consumer, then check the home is in that consumer's input.** Per the
> file's own convention the amendment record is the commit message
> (`git log --follow -- CLAUDE.md`) and is not restated here.
>
> 🔴 **A live defect on `main` was fixed** (#1193) — `deploy.py` built against
> `deploy/published/docker-compose.yml`, deleted three commits earlier; Phase 1
> would have died on the next `--execute`. Path promoted to a module constant
> plus a guard that walks the module's own path constants. ⚠️ **That guard's
> first draft masked its own oracle** — the probe reddened on a pinned literal
> and the filesystem stat never ran. **Seeing RED is not enough; read the RED.**
>
> ✅ **The control group that shaped the whole response:** `CLAUDE.md` §8's
> scenario-test rule is **GENUINELY OBEYED — all 17 scenario/e2e files, zero
> violations**, recorded per §6 as `confirmed — prior intact`, not a defect. This
> repo obeys a binding *mechanical* rule almost perfectly and fails on *advisory*
> ones — the asymmetry ADR-0038 rests on.
>
> ✅ **Branch protection verified LIVE, not from memory:** `strict: true`,
> `contexts: ["gate"]`, `enforce_admins: true`. With `strict` plus a bare
> `actions/checkout@v4` on `pull_request`, **the graded tree IS the tree that
> lands** — so `on: push: main` is NOT worth adding, and a specialist proposal to
> add it was retired on this evidence.
>
> **PLAN-0107 + PLAN-0108 drafted and split by ORACLE STRENGTH** (#1194, #1199)
> on Cray's typed S1 ruling; both `Draft`, unratified. **Gates, eight times:**
> `pytest tests/` **4115 passed / 8 skipped**, `mypy --strict services/` clean
> over 136, ruff + format clean over 631, CI `gate` **pass** every time.

> **Sessions 233–234, 2026-08-15→16 (head_commit `5425822` → `027986e`) — TWELVE
> PRs merged (#1180–#1191), 0 open. Fleet's last gate closed, fleet WENT LIVE, a
> human drove it, and it broke in a way CI structurally cannot see.
> `oct-fleet-maintenance` is published system #3 and is now serving the FIXED
> build; PLAN-0103 is COMPLETE 11/11 and PLAN-0106 COMPLETE 7/7, both ARCHIVED.**
>
> ✅ **AC-11's RoPA was written and ADOPTED** (`docs/compliance/ropa-fleet-cases.md`,
> #1184) — the artifact the whole chain waited on. 🔴 **Its authorship DEPARTS
> from ADR-0037 D2.1, disclosed ON the artifact:** Code drafted at Cray's request,
> Cray ruled every promise slot and adopted. **SD-1 stays unruled; until it is,
> D2.1 as written governs.**
>
> 🔴 **s233's load-bearing work was VERIFICATION, not construction — seven
> inherited claims were checked and REFUTED**, including ADR-0037's OQ-3, which
> had been *ruled* 2026-08-14 while its recorded Recommendation was still the
> **OVERRULED** option. Three downstream artifacts inherited it and it nearly
> sent the RoPA into the wrong file. _[Closed #1185. The general rule — a ruled
> OQ closes in the same change that records the ruling — is proposed as SD-2 and
> is UNRULED.]_
>
> ✅ **Tab J shows real money — ฿33,705, not a structural ฿0** (#1187), with an
> honest empty state. ⚠️ Seeding onto the demo's flagship truck **displaced** its
> ฿48,000 axle breach (the query projects the latest event **per truck**) —
> silent demo damage caught only by the full suite.
>
> ✅ **s234 executed Step 10 under Cray's typed §8 go**, and the pre-flight found
> **two steps every prose summary of that sequence had omitted** — the image was
> not on the host (`build:` with no `image:`, so `up -d` would build on the deploy
> host and fail there), and the host checkout was deliberately **not** pulled
> (the `deploy/` diff across those eight commits is empty).
>
> 🔴 **The keyed `/whoami` control was recorded as a DIFFERENTIAL** — keyless
> 401, correct key 200, **wrong key 401**. The third reading is what makes the
> second mean anything: a `200` alone is equally explained by "auth is off".
>
> 🔴 **Two documentation claims were MEASURED FALSE and corrected in the same
> PR** — the backslashed Windows path stripped through `ssh`→PowerShell, and
> *"302 proves a **working** origin"*. **Both now live in the runbooks they
> misled.** ⚠️ **Step 9's headroom projection is exceeded (≈1.33 GiB vs ≈0.95)
> because it models containers at boot** — the PLAN-0103 Active TODO owns that
> residual.
>
> Do-no-harm held on both host actions, against baselines captured **before** the
> first one: `oct-energy-app` and `oct-procurement-app` never restarted.
>
> 🔴 **Then Cray drove the live surface through Access, and that is the session's
> lesson.** It closed the scope limit Code had recorded (all six tabs render;
> Tab J shows **฿33,705** live) **and found a defect 4,113 green tests could
> not** — Tab I's root stood **919px inside a 614px `overflow: hidden` view**, so
> **305px was unreachable** with no scrollbar and no error. Fixed by copying
> Tab J's contract (#1190), guarded by a stylesheet-reading test, shipped live
> under a second typed §8 go. **CI has no JS runtime — that is the gap, not a
> missing test; own Active TODO.**
>
> ✅ **Redeploy, measured:** the new image id **differs**, **only `app` was
> recreated** so the tunnel never re-registered, both seeds' idempotency proven on
> real data, and the audit chain's `head_hash` came back **byte-identical** —
> which proves nothing was written, a claim `intact: true` alone cannot make.
> ⚠️ `index.html` is served `cache-control: no-store`, which **narrows**
> PLAN-0100's "nothing purges the edge" residual without closing it (fonts stand).
>
> **Gates: 4114 passed / 8 skipped**, `mypy --strict services/` clean over 136
> files, ruff + format clean over 631. Full record — bring-up **and** redeploy
> addendum: `docs/logs/2026-08-16-plan0103-step10-fleet-bring-up.md`.

> **Session 232, 2026-08-15 (head_commit `b2fe45e` → `5425822`) — ELEVEN PRs
> MERGED (#1170–#1179), 0 open. A next-work ranking became a fleet bring-up
> push: grounding REFUTED the inherited "blocked on ONE artifact" framing and
> found three more gates. Cray ruled six times and five gates closed — then the
> session continued past its own close and shut three MORE, leaving fleet on
> exactly one.** _[Reconciled s233 — s232 closed before #1178/#1179.]_
>
> 🔴 **Prose has no consumer, proven twice** — PLAN-0105's archived text claimed
> a `delete_case` factoring **that did not exist** (EXTRACTED, not re-worded,
> #1171), and fleet's Operate seed shipped s221 while **two of the three
> artifacts describing it still said it was unbuilt**; ruff, mypy and 4093 tests
> stayed silent eleven sessions (#1170, #1173). _[Both in their TODO rows.]_
>
> ⚠️ **`GET /api/cases` is unauthenticated and unfiltered** and `^/api/cases$` is
> on fleet's allowlist — cloudflared matches PATH, not METHOD. **RULED INTENDED**
> (Cray, typed). 🔴 **Record the PREMISE, not the word:** legitimate **because the
> data is synthetic**. Recipients fact: `ropa-change-statement-fleet.md` §4(c).
> ⚠️ **This measurement also forced SD-1's visibility clause WIDER than its
> draft** — the exposure is not surface-bound.
>
> ⚠️ **An empty database is invisible until a visitor hits it.** `/health` never
> touches Postgres and `cloudflared` gates only on `service_healthy` — the tunnel
> OPENS on a system whose visitor case path fails on the first write. RULED
> **operator step + make the skip LEGIBLE** (#1176). ✅ **Also RULED (#1174,
> #1175):** ADR-0037 **D4/OQ-2 = (a)** · recorder free text = **(i)** · ⚠️ OQ-1
> had been ruled since s231 while the ADR still read OPEN. ✅ **`deploy.py` does
> NOT block the bring-up** — it is the REDEPLOY tool.
>
> 🔴 **ADR-0037 D2.4 was an obligation with NO OWNER for three sessions** — the
> ADR said mechanics belong to the owning PLAN and none took it; no STATUS row,
> no test, no checklist held it, and it surfaced only by walking D2's obligations
> one at a time. ✅ **Owned by PLAN-0106 (#1174), then RULED in full, BUILT and
> MERGED the same session (#1178, #1179) — D2.4 is DISCHARGED.** 11 tests;
> **4107 passed / 8 skipped**. **Read the PLAN's §Surfaced decisions, never a
> restatement.**
>
> 🔴 **A guard that scans COMMITTED files is blind to a NEW file, and the blind
> spot sits where confidence peaks** — #1179 went RED in CI but **not locally**.
> Its sibling: **the visual pass found what eleven green tests could not** (no
> CSS; legible but not recognisable *as* a notice). Both, plus the guard family
> and the practice, are recorded in
> [`docs/lessons/0044-*.md`](lessons/0044-a-committed-file-guard-is-blind-to-the-new-file.md)
> — **read it, never a restatement.**
>
> ✅ **Fleet's two Cloudflare artifacts and four host secrets are DONE and
> PROVEN** — ⚠️ the **differential PIN test** is the only check that proves the
> policy *discriminates*; a wide-open policy returns the same `302` and shows the
> same screen. **ADR-0036 D2's price is paid for fleet.** 🔴 **Read the evidence,
> never a restatement — and note it is RECONSTRUCTED, not captured live:**
> [`docs/logs/2026-08-15-fleet-cloudflare-artifacts-and-secrets-staging.md`](logs/2026-08-15-fleet-cloudflare-artifacts-and-secrets-staging.md)
> (written s233 — the bring-up log that will normally own AC-10's evidence cannot
> exist until the bring-up does, and until then it lived only in a **gitignored**
> handoff).
>
> ⚠️ **The gate list is now ONE item, not five. PLAN-0103 AC-11's RoPA is the
> only one left, and only Cray can write it.** Fleet's typed §8 go was given
> **verbally but cannot yet be validly RECORDED** — AC-11 requires the record to
> cite the RoPA **by path**. **Requester identification for the DSR path remains
> genuinely undesigned:** `repair_case.opened_by` has no foreign key and personas
> add no visitor identity, so a request matches rows **only by content**.

> **Session 231, 2026-08-14 (head_commit `9072760` → `b2fe45e`) — eight PRs
> MERGED (#1159–#1167), 0 open. vero-lite gained its FIRST row-retention
> control, and PLAN-0105 went from undrafted to COMPLETE 11/11 and ARCHIVED in
> one session.**
>
> ✅ **What ships:** fleet's visitor-opened repair cases, their six FK children
> and their upload directories are deleted **90 days after `opened_at`** by an
> in-app task — the sweep (`services/db/repair_case_retention.py`), the task
> (`services/api/case_retention_task.py`, wired into `lifespan` with **zero
> added branches**), the eighth-table completeness guard (AC-5), fleet's
> `CASE_RETENTION_ENABLED=true` profile flag with a both-directions deploy
> guard, and the scenario test (AC-10). **Read the archived PLAN, never a
> restatement:** `docs/plans/done/0105-fleet-case-retention-in-app-deletion.md`.
>
> 🔴 **The one finding a future reader must NOT re-derive — classified `was an
> error`.** `repair_case_accepted_quote` holds a **composite FK to
> `repair_case_quote`**, and Step 1's declared deletion order deleted the quote
> **FIRST** — so the sweep raised `ForeignKeyViolation` on every case that had
> ever accepted a quote, was caught by its own fail-soft, and **retried
> forever**. **Retention would silently never have completed on real data while
> every unit test stayed green.** ⚠️ **Neither existing guard could see it:**
> Step 1's unit test inserted a task event and no quote pack, and **AC-5 checks
> membership, not order**. Only the Step-6 scenario, on the first realistic
> case, failed. Fixed by one measured swap (**exactly one** child-to-child edge
> exists) and guarded by
> `test_the_declared_order_respects_every_child_to_child_dependency`.
>
> ✅ **Four SD slots RULED (Cray, typed, 2026-08-14) and folded in:** SD-1 **(b)**
> ordered app-level child deletes + the AC-5 guard (no migration; the loud
> fail-closed DELETE posture preserved) · SD-2 **(a)** files first, then rows ·
> SD-3 **no status exemption** — MEASURED: no code path closes a case, so an
> OPEN exemption would exempt **every** row — **and** the chain's dangling
> `case_id` pointer stated as intended design · SD-4 **(a)**
> `repair_case_run_link` rows deliberately RETAINED.
>
> ⚠️ **What `Complete` does NOT mean.** **PLAN-0103 AC-11's RoPA is still
> Cray's** (it now has a shipped control to describe), the **DSR-on-request path
> for case rows is still undefined**, and **fleet's bring-up still needs its own
> typed §8 go**.
>
> **Also landed:** #1159 corrected the RoPA's deployment-status line and two §7
> controls `owed` → `built` (`docs/compliance/ropa-published-demo.md`) —
> factual only, no controller judgment touched.

_[The session-229 block rotated to `docs/status-archive/2026-h1d-current-focus.md`
this reconcile, keeping the window at four.]_

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
| 2026-08-17 | **s235 — ADR-0038 RATIFIED (5 classes binding, 4 SDs ruled); `CLAUDE.md` BOUND with four new rules; 8 PRs (#1193–#1200).** 🔴 **The organising law:** a defect is visible only when an INSTRUMENT reads the artifact, the DATA reaches the failing state, and someone ARMED it as a gate. 🔴 **A live `main` defect fixed** (`deploy.py`'s dead compose path). ✅ §8's scenario rule is genuinely obeyed: 17 files, 0 violations. | `218a521` / [#1197](https://github.com/CrayJThiemsert/vero-lite/pull/1197) / [#1200](https://github.com/CrayJThiemsert/vero-lite/pull/1200) / `docs/adr/0038-*.md` |
| 2026-08-16 | **s234 — Step 10 EXECUTED under Cray's typed §8 go: fleet is LIVE as published system #3;** PLAN-0103 **11/11** and PLAN-0106 **7/7**, both COMPLETE, ARCHIVED. 🔴 **Cray drove the live surface and found Tab I clipping 305px of itself — a defect 4,113 green tests could not see, because CI has no JS runtime.** Fixed, guarded, REDEPLOYED under a second typed go. Pre-flight omissions, two false doc claims and every redeploy reading are in the log. | `027986e` / [#1190](https://github.com/CrayJThiemsert/vero-lite/pull/1190) / `docs/logs/2026-08-16-plan0103-step10-fleet-bring-up.md` |
| 2026-08-16 | **s233 — SEVEN PRs MERGED (#1180–#1187); AC-11's RoPA WRITTEN and ADOPTED, closing fleet's last gate.** Cray ruled **seven** times; every ruling is stamped on the RoPA itself. 🔴 **ADR-0037 OQ-3 had been RULED while its recorded Recommendation was still the OVERRULED option**, and three downstream artifacts inherited it. ⚠️ **The RoPA's authorship DEPARTS from D2.1**, disclosed on the artifact; **SD-1 is UNRULED and D2.1 as written still governs.** | `3b9a084` / [#1184](https://github.com/CrayJThiemsert/vero-lite/pull/1184) / `docs/compliance/ropa-fleet-cases.md` |
| 2026-08-15 | **s232 — ELEVEN PRs MERGED (#1170–#1179); the "fleet blocks on ONE artifact" framing was REFUTED — 14 gates walked, TWO owned by nobody.** Six typed rulings folded. ✅ **PLAN-0106 then RULED, BUILT and MERGED — D2.4 DISCHARGED** — and Cloudflare + host secrets closed. 🔴 **Fleet's gate list is now ONE item, AC-11's RoPA.** | `5425822` / [#1178](https://github.com/CrayJThiemsert/vero-lite/pull/1178) / [#1179](https://github.com/CrayJThiemsert/vero-lite/pull/1179) / `docs/plans/done/0106-*.md` / `docs/logs/2026-08-15-fleet-cloudflare-*.md` |
| 2026-08-14 | **s231 — PLAN-0105 drafted, its four SD slots RULED (Cray, typed), built and CLOSED 11/11 in one session: fleet's visitor cases, their six FK children and their upload dirs delete 90 days after `opened_at`.** 🔴 **The declared order deleted `repair_case_quote` BEFORE its composite-FK child** — `ForeignKeyViolation` on every case that had accepted a quote, swallowed by the fail-soft and **retried forever** with unit tests green; **AC-5 checks membership, not order**. Caught by the Step-6 scenario. | `b2fe45e` / [#1166](https://github.com/CrayJThiemsert/vero-lite/pull/1166) / [#1167](https://github.com/CrayJThiemsert/vero-lite/pull/1167) / `docs/plans/done/0105-*.md` |
| 2026-08-14 | **s229 — R8's PLAN-reference guard was blind to glob refs (`NNNN-*.md`, the form registries use) since s183; #1153 closes it.** The one live dead pointer had been dead since s216 and was **never reported once** — including by the commit that fixed the stream-2 row beside it. Resolves globs through the **same MOVED-not-MISSING predicate**; `Path.glob` would descend into `done/` and fail **OPEN**. | `ee968e5` (head_commit) / [#1153](https://github.com/CrayJThiemsert/vero-lite/pull/1153) / `docs/runbooks/memory-architecture.md` §R8 |
| 2026-08-13 | **s228 — PLAN-0104 Step 7 EXECUTED under a typed §8 go; AC-7 CLOSED, PLAN COMPLETE 8/8 and ARCHIVED.** 🔴 **The fresh 12/13 RETIRES the prior figure as non-comparable — it does NOT beat it** (prompt changed in #1149; gold grew 12 → 13), and the obvious citation is a trap: that file's arm-comparison `11/12` is **text-to-SQL**, not engine-A's. nl-06's miss was re-run, failed again, investigated — **not a regression; the victim moved**. | `ad2804d` (head_commit) / [#1151](https://github.com/CrayJThiemsert/vero-lite/pull/1151) / `benchmarks/nl_query_feasibility/RESULTS.md` §Addendum |
| 2026-08-13 | **s227 — PLAN-0104 Steps 2+3+4 as ONE PR (#1148) and Steps 5+6 (#1149); Steps 1–6 COMPLETE.** 🔴 **AC-5 is a hard merge dependency, not a preference:** no commit may exist where `count`+`group_by` validates while `_count` still collapses groups — that state answers with a **silently wrong** number, worse than the refusal it replaces. | `75243b0` / [#1148](https://github.com/CrayJThiemsert/vero-lite/pull/1148) / [#1149](https://github.com/CrayJThiemsert/vero-lite/pull/1149) / `docs/plans/done/0104-*.md` |
| 2026-08-13 | **s226 — PLAN-0104 DRAFTED, its three SD slots RULED (Cray, typed), Step 1 SHIPPED.** 🔴 The `count`+`group_by` refusal had **three independent enforcers**, so no single edit changed behaviour and the circulating *"≈ one PR + tests"* price was wrong. 🔴 The gold guard was **VACUOUS** — it restated the numbers instead of reading `SQL_EXPECT`, so two wrong tokens scored `wrong` every run, silently. | `fa8a61c` / [#1144](https://github.com/CrayJThiemsert/vero-lite/pull/1144) / [#1145](https://github.com/CrayJThiemsert/vero-lite/pull/1145) / `docs/plans/done/0104-*.md` |
| 2026-08-12 | **s225 — PLAN-0103 Step 6 SHIPPED and nine of eleven ACs CLOSED.** 🔴 **Verifying an inherited "closed in substance" claim rather than relaying it found two ACs FALSE** — AC-7's text described an approval the engine refuses; AC-6's named guard had never existed. **Both fixed, not ticked over.** ⚠️ AC-10 + AC-11 stay OPEN. | `b229fcd` / [#1139](https://github.com/CrayJThiemsert/vero-lite/pull/1139) / [#1140](https://github.com/CrayJThiemsert/vero-lite/pull/1140) / [#1141](https://github.com/CrayJThiemsert/vero-lite/pull/1141) / `docs/plans/done/0103-*.md` |

_[The session-224 row rotated to `docs/status-archive/2026-h1-status.md` this
reconcile, holding the table at ten.]_

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

- [ ] **🆕 The four s235 audit findings ADR-0038 did NOT absorb — REHOMED s235 out of a gitignored handoff into `docs/logs/2026-08-17-s235-audit-findings-outside-adr-0038.md`.** The **retrieval-reliability ranking** · **"pruning never reclaims storage"** (so never argue a rotation on disk grounds) · **`docker build` in CI, rated YES and owned by no PLAN** · **the 11-class vacuity taxonomy**. 🔴 **One live obligation in there: ADR-0038's three-strike counter has NO OWNER** — three items sit at two firings and no artifact records a count. PLAN-0108 is the natural owner and does not claim it.
- [ ] **🆕 PLAN-0107 — oracle-coverage hardening: `Draft`, UNRATIFIED, 15 ACs; NOTHING gates it.** The strong-oracle half of s235's five-specialist audit (PLAN-0108 holds the weak-oracle convention half — the split is Cray's typed S1 ruling). **Phase A is all zero-new-dependency work:** `node --check`, the asset-manifest bijection, a real `TestClient` lifespan boot, the executor-registrar map, `mypy --strict verticals/` (**measured already clean over 64 files — zero remediation**), the two CI-orphaned pre-commit hooks. AC-14 retires the inert `?v=` guard, **no separate ratification** (Cray, typed). **Read the PLAN, never a restatement:** `docs/plans/0107-oracle-coverage-hardening.md`.
- [ ] **🆕 PLAN-0108 — AC-authoring + pre-close convention hardening: `Draft`, UNRATIFIED.** The weak-oracle half of the same audit; its only blocker was ADR-0038, **which has landed**, so nothing gates it either. Owns ADR-0038's **OQ-5** — the staleness-guard obligation attaches to the PLAN template, not to a build task. **Read the PLAN, never a restatement:** `docs/plans/0108-ac-authoring-and-preclose-convention-hardening.md`.
- [x] **PLAN-0106 — fleet's own in-app case-persistence disclosure (ADR-0037 D2.4): COMPLETE 7/7, marked Complete by Cray (typed) and ARCHIVED s234.** AC-7's ordering clause closed on fleet's Step-10 go record, which cites this PLAN by number. **No live residual.** **Read the archived PLAN, never a restatement:** `docs/plans/done/0106-fleet-case-persistence-disclosure.md` (§Closure evidence · §Surfaced decisions).
- [x] **PLAN-0105 — fleet's 90-day in-app case retention: COMPLETE 11/11, ARCHIVED s231.** **Read the archived PLAN, never a restatement:** `docs/plans/done/0105-fleet-case-retention-in-app-deletion.md` (§Surfaced decisions SD-1..SD-4; the child-to-child FK ordering defect and its guard). ⚠️ **Live remainder — the DSR-on-request path stays undefined, requester identification in particular**; `delete_case()` is the mechanism half only. _[s235: the "AC-11's RoPA is still Cray's" clause is DROPPED as **stale, `was an error` by the time it was last edited** — the RoPA was written and ADOPTED s233 (#1184).]_
- [x] **PLAN-0104 — `count` WITH `group_by`: COMPLETE 8/8, ARCHIVED s228; discharges PLAN-0100 D-4.** **Read the archived PLAN and the evidence, never a restatement:** `docs/plans/done/0104-nl-query-count-with-group-by.md` · `benchmarks/nl_query_feasibility/RESULTS.md` §Addendum — which holds the "12/13 does NOT beat 11/12, that figure is RETIRED as non-comparable" correction. ⚠️ **One live residual, recorded ONLY here:** the Step 7 dumps under `.claude/benchmark-results/` are **untracked and NOT gitignored** — no copy in history, nothing stopping an accidental commit.
- [x] **`_count`'s week silent-drop — CLOSED s228, RULED (a), SHIPPED [#1156](https://github.com/CrayJThiemsert/vero-lite/pull/1156).** The guard and its named set `_WEEK_ROLLUP_BLIND_TO` live in `services/engine/run_query.py` — **read the code, never a restatement.** ⚠️ **Live remainder: (b) — make the filter work — is still the better ANSWER and stays unscheduled**; no gold case asks for it today, and because the set is named, (b) SHRINKS it rather than deleting the guard.
- [ ] **TWO unruled silent drops in the NL engine's aggregate paths — REHOMED s235 to the code.** (i) the **`started_week` filter is ignored entirely** (found s228) and (ii) **`group_by` never reaches `AggregateResult`**, so *"average duration per procedure"* validates, executes and silently returns **one ungrouped number** (found s232). Both live at `_aggregate_duration` / `_aggregate_benefit`; ⚠️ **the count path DOES pass `groups`**, so (ii) is a two-site gap in an otherwise-correct design, not a missing feature. **No test covers either.** **Read the docstring, never a restatement:** `services/engine/run_query.py::_aggregate_duration`. **Same two dispositions each, NEITHER ruled: (a) refuse, or (b) make it work.**
- [x] **`deploy.py`'s dead compose path — FIXED s235 ([#1193](https://github.com/CrayJThiemsert/vero-lite/pull/1193)).** Found s232 and live on `main` for three commits; Phase 1 would have died on the next `--execute`. The path is now the module constant `_LOCAL_COMPOSE`, guarded by a test that walks the module's own path constants, so a future straggler reddens by construction. **Read the code and the guard, never a restatement:** `deploy/published/deploy.py` · `tests/deploy/test_deploy.py`. ⚠️ **That guard's first draft masked its own oracle** — homed in [`docs/lessons/0043-*.md`](lessons/0043-a-probes-red-must-name-what-broke.md), now binding via `CLAUDE.md` §8's witnessed-RED rule.
- [ ] **`nl-03`'s `SQL_EXPECT` is UNDER-SPECIFIED — RULED (Cray, typed, s226): RECORD it, do NOT change the token. REHOMED s235 to the module that defines it.** Its list holds two ids where `gold.yaml` lists three. 🔴 **A different defect class from the nl-02/nl-05 tokens Step 1 repaired:** `score_sql` matches a SUBSET, so the oracle is **WEAKER than it should be, not WRONG**. Adding the token would make the benchmark STRICTER and **break comparability with earlier runs** — a measurement decision, not a typo fix. **Read the note, never a restatement:** `benchmarks/nl_query_feasibility/text_to_sql.py` (above `SQL_EXPECT`).
- [x] **PLAN-0103 — vero-lite's side of the multi-vertical portal: COMPLETE 11/11, ARCHIVED s234;** all three published systems are live. **Read the archived PLAN and the closeout record, never a restatement:** `docs/plans/done/0103-portal-landing-and-per-system-published-profiles.md` · `docs/logs/2026-08-16-plan0103-step10-fleet-bring-up.md`. **Two live residuals outlive the PLAN and are recorded here because nothing else carries them:** (1) ⚠️ **Requester identification for the DSR path is genuinely undesigned** — `repair_case.opened_by` has no FK, so a request matches rows only by content. (2) ⚠️ **Step 9's headroom projection under-models by ~3–6× per app container** — it measures containers at boot; a fourth system must be projected against steady-state figures.
- [x] **Fleet's Operate-tab seed flag — CLOSED s232 ([#1170](https://github.com/CrayJThiemsert/vero-lite/pull/1170)):** `OCT_DEMO_SEED_OPERATE` flipped `false`→`true`; the flag lives in `deploy/published/oct-fleet-maintenance/published.env`. 🔴 **The durable shape, recorded ONLY here — three artifacts described one fact and only `main.py`'s was right, because it was edited alongside the code; prose has no consumer, and ruff, mypy and 4093 tests stayed silent eleven sessions.**
- [ ] **The apex domain leaks in ONE archived file — UNRULED, not urgent; REHOMED s235 to the guard that would have to widen.** 🔴 **RE-PRICED s232 — "widen the guard" is NOT a one-file flip:** widening the scan to `docs/plans/` reddens **FOUR** files, so the option is a flip **plus three deliberate allowlist additions**. ⚠️ **The guard's path was recorded WRONG and is corrected s235** — it is `tests/deploy/test_published_compose.py::test_no_unknown_domain_appears_in_the_deploy_docs`, not `test_published_profiles.py`. **Read its docstring, never a restatement. Reference the carrier BY PATH only — the domain is not named.**
- [ ] **The ฿ realized-vs-projected join — REHOMED s235 to `services/db/run_analytics.py::benefit_rollup`,** which is the primitive the circulating framing wrongly claimed could be reused. 🔴 **It cannot** — it yields no per-run figure at all, so the join needs a NEW per-run aggregation; copy `run_duration_totals`. ✅ **No migration needed.** ⚠️ Re-priced **~150–250 lines across 6–7 files, ONE PR** — the *"~40 lines"* figure was checked and is WRONG. Three TEST-PINNED constraints live in that docstring. **Read it, never a restatement.** Lands on Tab J, which fleet publishes.
- [ ] **Demo-key rotation cadence — CRAY'S, posture not code.** Fleet's README documents how to **generate** a persona key pair but says nothing about **when to rotate**. Measured s225: `git grep -i -e rotate -e rotation` under `deploy/published/oct-fleet-maintenance/` returns **zero** matches. The keys are served to the browser by ruling, so they are **public the moment fleet is reachable** — which makes the cadence a real posture question rather than a nicety. No code change is implied; the answer is Cray's.
- [ ] **ADR-0036 OQ-2 — the aggregate in-flight LLM posture — remains OPEN.** ✅ PLAN-0103 Step 9's MS-S1 headroom is MEASURED s221 (`docs/logs/2026-08-10-oct-energy-migration-phase2-and-step9-headroom.md`): RAM and CPU do not constrain a second or third published system. ⚠️ **OQ-2 does NOT follow from it** — the constraint on a second *assisted* system is the resident model and concurrent in-flight calls, not container footprint, and one term (Postgres idle) is declared unmeasured rather than folded silently into the total. **Read the ADR's own OQ-2, never a restatement.** _[s235: this row's other three sub-items are DISCHARGED — the edge cache-purge cost is now in PLAN-0100's §Post-archival amendment, ADR-0037 D4/OQ-2 closed s232, and the one-pager has its own row.]_
- [ ] **Three measured, unscheduled items — REHOMED s235 to `docs/logs/2026-08-17-s235-unscheduled-measured-items.md`.** (1) **The public one-pager v2** — DESIGN-READY, a WRITE job; destination RULED (Cray, typed, s226) = gitignored `docs/strategy/private/`. (2) **The assembly-cost axis** — Cray's s197 ruling is an ORDERING (measure, then ADR); the banked series **1:1.8 → 1:6 → 1:1.1** is spiky, not falling, and 🔴 **its METHOD is recorded nowhere**, so a tripwire built today emits an incomparable number. (3) **Seam-scoped mutation-testing CI** — still unscopeable: **2 pytest markers, no `scenario` marker**, and CI runs bare `pytest -q`, so §8's binding scenario rule is **mechanically unenforced**. ✅ XS prerequisite (marker + filename normalise) has **ZERO** rename blast radius. **Read the log, never a restatement.**
- [ ] **Landing-layer PLAN — CLOSED s226 as SUPERSEDED. NOT work to do; this row exists so nobody schedules it again.** PLAN-0103 Step 8 consumed the repo-side half (AC-9 ticked), and ADR-0036 D1/D2 place the landing surface, ingress map and Access policies **outside this repo** — a vero-lite file enumerating published systems is guard-rejected as a *shadow ingress map* (`tests/deploy/test_published_profiles.py`). Cray ruled s221 (typed): **no portal repo.** 🔴 **The remainder is CRAY'S DASHBOARD WORK — nothing for Code, no dispatch owed.** _[Trimmed s233 per R2 s141; measurement narrative in `docs/status-archive/`.]_
- [ ] **PLAN-0100's residuals outlive the PLAN** (COMPLETE 13/13, ARCHIVED s216; the demo is LIVE, REDEPLOYABLE and DRIVEN). ✅ **REHOMED s235 under the R2 carve-out** — all three residuals (**D-4 fully discharged** by PLAN-0104 · **no cache-purge step and no versioned font URLs**, a purge needing a new secret + host-state · **no `OLLAMA_KEEP_ALIVE` pin**, so all three profiles inherit the 30m code default) now live in the PLAN's own **§Post-archival amendment**, each re-verified at source rather than copied. **Read it, never a restatement:** `docs/plans/done/0100-exposure-published-demo-surface.md` (§Post-archival amendment · §"Step 11 closure verdict" · §"Defects the live run found" for D-1..D-5).
- [ ] **CI has NO JS RUNTIME — s234 measured the cost; NARROWED s235, NOT closed.** Tab I clipped **305px** of itself on the **live** system while **4,113 tests were green**; a human found it. **No oracle here can see a clip.** ⚠️ **PLAN-0107 AC-1 adds `node --check`, a SYNTAX gate — a clip is a LAYOUT fact, so AC-1 narrows this row and does not close it.** 🔴 **The guard shipped with the fix does not close it either, and says so in its own docstring** — `test_case_wrap_declares_the_scroll_contract` reads the stylesheet, so it catches a deletion and **cannot catch a re-clip by other means**. An oracle gap, not a missing test. Closing it is a JS-runtime-in-CI project — nothing drafted. Evidence: `docs/logs/2026-08-16-plan0103-step10-fleet-bring-up.md` §Addendum.
- [ ] **PLAN-0096 partner round-2 — ANSWERED s189; nothing blocking remains.** **Open, NON-blocking: cost-center (ศูนย์ต้นทุน) granularity — per truck or per company?** Ship the column, fill the rule when it lands. (A5 stays **parked** — no real Wialon export exists yet.) _[s226: the per-answer ledger A1–A7 is ROTATED to `docs/status-archive/2026-h1-status.md`; `docs/plans/done/0096-fleet-flow-completion-phase1.md` holds the detail.]_
- [ ] **The AT-2 extraction — only the F-FACTORY half remains, owned by PLAN-0076 T1.** The criterion-vocabulary half SHIPPED as PLAN-0087 (ARCHIVED, #840/#841); SD-1 = (a) keeps the procedure-aware `ExecutorFactory` half with PLAN-0076 T1, guard `test_at2_extraction_obligation_is_owned` ARMED. Full detail: `docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` + `docs/plans/0076-*.md` §A.
- [ ] **PLAN-0075 follow-ons — homed by PLAN-0076 (`Status: Tracking`, #752).** T1's criterion-vocabulary half shipped as PLAN-0087; the procedure-aware-`ExecutorFactory` half (F-FACTORY) stays OPEN, and T2's F-PIN remainder closed s143 (#784) while **F-PIN itself stays OPEN** — so PLAN-0076 does **not** archive and its AC-6 presence guard stays ARMED. **Read the PLAN, never a restatement:** `docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` §A. ⚠️ Its six ACs and four Steps are **stub-level — none directs a build**, so nothing here is Code-executable. _[Trimmed s233 per R2 s141.]_
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2), open ONLY for the O-2 residue.** Every other leg is DONE and archived. The residue: procurement's `intake` migrated only PARTIALLY — the derived fields already moved to declared `transform` (PLAN-0078 PR-1 #762, AC-2 ticked), leaving **only the cardinality-changing `candidate_quotes` nest**, explicitly Out-of-Scope there. **Read the archived PLANs, never a restatement:** `docs/plans/done/0062-per-vertical-seed-migration.md` §SD-C (the co-exist decision + its STOP-and-surface tripwire) · `done/0078-*.md` §L-3. _[Trimmed s233 per R2 s141.]_
- [ ] **Bounded/incremental chain verification (PLAN-0063 SD-4 follow-up, s118).** `GET /audit/verify` walks the WHOLE chain O(n) on demand — accepted at pilot scale. Future work = a checkpointed head / verify-since-anchor design; anchor storage ≈ external anchoring — **do not build without re-reading the tripwire** in `docs/plans/done/0063-audit-chain-verification-surface.md` + the `services/api/routers/audit.py` module docstring (SD-4). *(#688/#690)*
- [ ] **Rock 4 — s84 deep research DELIVERED → O-sequence locked.** Cray locked **O-1 → O-3 → O-2 → O-4**. **O-1** (Box-4 ฿ pitch) **DONE** · **O-3 = ADR-0025 Accepted** · **O-4 = PARK** (agent-interop; `docs/adr/0032-*.md` D4 — option-only, un-park = a counterparty's *written* pull). **Remaining: O-2 only** (economic-impact facet + Q3 data-binding = Rock 3). Full detail: `docs/adr/0025-at2-managerial-layer.md` (O-sequence + Box-3 fit + the **evidence-asymmetry** finding rehomed s142). *(s84 Cray ask)*
- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten. **Full table (all six rows + their triggers + where each lands): `docs/plans/done/0005-oct-engine-runtime-layer.md` §8.1** — which itself instructs this STATUS entry to be a pointer. *(per Cray note 2026-05-21)*
- [ ] **PLAN-004 Phase C — OPTIONAL POLISH (forward-declared; "may never land"):** HTML/markdown handoff dashboard under `docs/` + references-graph (mermaid dispatch chains) + `render_transcript.py` unified session export (PLAN-0004 §"Phase C"). *(Phase A + B both COMPLETE — session 35; the prior TODO's validator **warning-swallow bug was FIXED #312**, s58.)* _[s226: the three never-formally-scoped sub-ideas are ROTATED to `docs/status-archive/2026-h1-status.md` — fold them in only if Phase C ever lands.]_
- [ ] **Custom Postgres image with extensions (pgvector / AGE / pg_trgm) — MEASURED DORMANT s226. Recommendation on record: NO ACTION.** Grepping `services/` for `pgvector|pg_trgm|trgm|Apache AGE|embedding|CREATE EXTENSION` returns **exactly one hit, and it is a false positive** — the English word "embedding" in a prose comment at `services/engine/llm/prompt.py:43`. **Nothing in the codebase needs these extensions**, and the documented trigger ("semantic query / graph features prioritised") points the **opposite** way from where the work actually went: NL query took the **relational-aggregation** route (PLAN-0104). ⚠️ **The price has RISEN since this row was written:** ADR-0037 grants fleet its **own** Postgres in the published deployment, so swapping the base image is **no longer a one-line compose edit** — it touches **three published profiles and their 68-test guard suite**. **Revisit only when a consumer feature defines which extensions are actually needed**; still needs a fresh ADR number + a PLAN, neither drafted. *[Corrected s141: **PLAN-002 does not exist** and the old "≥ ADR-014" floor is **moot** — ADRs now run past 0032 and `0014-WITHDRAWN.md` exists.]* Context: `docs/adr/0013-autonomy-axis-relocation.md` + `docs/plans/done/0005-*.md`.
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [ ] **CLAUDE.md follow-up extraction pass (s181 option b): new Cowork dispatch; target < 20 KB. PARKED s183 by Cray — the dispatch stays UNSENT until two things are settled, and s183/s188 grounded both.** (1) **The unit of `< 20 KB` is load-bearing and unpinned** (KiB vs decimal); Cray was asked and declined to rule for now. (2) **The named candidates cannot reach either target:** at `CLAUDE.md`'s s188 size of **22,424 B** the cut needed is **1,944 B** (20 KiB) / **2,424 B** (decimal), where the five candidates measure **~930–1,000 B** combined and the genuinely large blocks are **not on the list**. Sending it as written would repeat the s181 failure of an arithmetically unreachable target. 🔴 **The real parked decision: the target and the constitution are pulling in opposite directions** — the growth is Cray-ratified binding-rule substance, not padding. Materials: `.claude/handoffs/session-181/` (gitignored). _[s226: the per-candidate enumeration and the full s183/s188 byte arithmetic are ROTATED to `docs/status-archive/2026-h1-status.md`.]_
- [ ] **PLAN-0102's two residues outlive the PLAN** (retire L1 loop-detect — COMPLETE 11/11, ARCHIVED s217, #1096; L1 gone from all four hooks, L2/L3/L4 intact and asserted so). ✅ **REHOMED s235 under the R2 carve-out** — the **callerless `observe()`** (kept deliberately; deleting it pulls a refactor into every surviving L2/L3/L4 increment) and the **forwards-call-graph method debt** (a linter cannot close it — `ruff` flags a dead import, never a dead private function) now live in the PLAN's own **§Post-archival amendment**, both re-verified at source. **Read it, never a restatement:** `docs/plans/done/0102-retire-l1-loop-detect.md`.
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
