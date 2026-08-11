---
last_updated: 2026-08-11T17:55:00+07:00
session: 222
current_batch: "s222 — PLAN-0103 AC-8 clause 2 CLOSED in substance and ADR-0037 D2.7 MEASURED (#1124, #1125); five PRs reconciled (#1121–#1125), 0 open."
current_actor: code
blocked_on: "NOTHING blocks repo work. SD-8 gates Step 6. Two LIVE obligations: AC-11's RoPA (Cray's, as controller, before fleet's bring-up) and a typed §8 go per bring-up (AC-10 clause 2)."
next_action: "Cray's pick, not asserted here: rule SD-8 (gates Step 6), or PLAN-0103 Step 10 (procurement first per SD-2); a plan-drafter dispatch is owed to tick AC-8/AC-9."
head_commit: 3a11e87
recent_commits: [3a11e87, 9e2c15f, 1bcef4b, c8052f6, a18f578, 01653c7, 4498f5a, 068593f, 9a3a9c8, 1f32540]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

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
> PLAN's checkboxes are NOT ticked** — Code cannot write `docs/plans/` (G2), so
> the tick is owed to a `plan-drafter` dispatch. **ADR-0037 D4 is UNBLOCKED, not
> decided.** **SD-8 is still NOT RULED** and gates Step 6. Two live obligations
> stand unchanged: **AC-11's RoPA** (Cray's, as controller, before fleet's
> bring-up) and **a typed §8 go per bring-up** (AC-10 clause 2).

> **Session 221, 2026-08-10 (head_commit `f78068e` → `e938cf6`) — two code PRs
> merged (#1119, #1118), 0 open, plus a host-state run that carries no PR of its
> own.** _[s222: session 221 did not end here — #1121, #1122 and #1123 merged
> after this block was written; they are recorded in the s222 block above and
> not restated.]_ **Theme: PLAN-0103 Step 8a landed together with the repair of a build
> context that could not build, and energy's LIVE system finally caught up with
> the rename the repo made two sessions ago.**
>
> ✅ **Step 8a SHIPPED (#1119) — every profile now carries its card copy, so
> AC-3 CLOSES.** `card-copy.md` exists in all three profile directories
> (`oct-energy`, `oct-procurement`, `oct-fleet-maintenance`), bilingual TH/EN,
> asserted **structurally** — section presence, not copy quality, which has no
> oracle — by `test_ac9_the_card_copy_is_bilingual_and_structurally_complete`.
> 🔴 **AC-9 is NOT closed by this:** its second clause is the portal-side
> assembly request (Step 8b), still owed, and itself a Step 10 input.
>
> 🔴 **The same PR repaired a compose build context that could not build — and
> "all three composes validate" had been reported while none of them could.**
> `context: ../..` from `deploy/published/<system>/` reaches `deploy/`, one
> directory short of the repo root; Step 4a moved the file deeper without
> following the relative path, and all three profiles inherited the error.
> `docker compose config --quiet` returned 0 over all three because it validates
> the **schema**, not whether the context resolves — so the check that was
> trusted in the s220 record could not have caught this. Now `../../..` in all
> three, guarded by `test_the_build_context_resolves_to_a_real_dockerfile`.
>
> ✅ **#1118 discharged the PLAN-0103 self-citation TODO** — the four stale
> citations are corrected in the PLAN itself. The fourth item that TODO carried,
> **whether Tab G's "Act — the human DOA gate" card should render at all on a
> personaless system**, is now homed in the PLAN as **SD-8, explicitly NOT
> RULED**, with three neutral options and no step assuming an answer. It stops
> being a STATUS-only item; it is Step 6's question and **Cray's call**.
>
> ✅ **energy's LIVE system migration is COMPLETE and Step 9's headroom is
> MEASURED — both under one typed Cray §8 go.** The demo now runs as compose
> project **`oct-energy`** on network `oct-energy_vero_oct`; project
> `vero-published` no longer exists on the host in any form — containers,
> network or volume. The prompt-log rows were migrated volume→volume and
> verified **byte-identical on both sides** (per-file checksums, not merely
> sizes), and the running app was proven able to **write** to the log as its
> non-root user — **refuting** the s215 silent-`OSError` failure mode rather
> than assuming it absent. The old volume was removed **last**, and the off-host
> backup — which held personal data outside the retention system — was deleted
> only after the edge check passed. **Read the record, never a restatement:
> `docs/logs/2026-08-10-oct-energy-migration-phase2-and-step9-headroom.md`**
> carries every number, the method, the pre-committed pass/fail reads, and the
> two things the run could not prove.
>
> ⚠️ **What the headroom measurement does NOT settle, so it is not read as
> broader than it is.** RAM and CPU do not constrain a second or third published
> system — but the binding constraint on a second *assisted* system was never
> container footprint; it is the resident LLM and the number of concurrent
> in-flight model calls. That is **ADR-0036 OQ-2, and it stays OPEN.** One term
> in the projection — Postgres idle footprint — is **declared unmeasured**
> rather than folded silently into the total. **Step 9 is MEASURED; AC-10 is NOT
> closed** — its first clause is discharged, its second (every bring-up carries
> its own explicit §8 go) stands.
>
> ⚠️ **A hardware correction worth one clause.** MS-S1's 128 GB unified memory
> is deliberately split roughly in half with the GPU, so only about half of it
> is visible to Windows at all. `CLAUDE.md` §5 / ADR-002 record the hardware
> figure, which is **true of the machine and false of what any process can
> allocate** — any projection starting from 128 GB overstates available RAM.
>
> ⚠️ **Honest miss:** downtime overran its planned window, and the overrun was
> an **instrument failure, not migration work** — a display-only
> `docker network ls` wedged inside a remote PowerShell script whose output was
> block-buffered, so the log sat at zero bytes while containers had already been
> removed. Zero bytes was not evidence that nothing had happened. The log file
> carries the diagnosis and what actually finished the run.
>
> **What remains on PLAN-0103:** Steps **6** (persona picker), **7** (fleet's
> Tab-H seed), **8b** (the portal-side assembly request — AC-9's open clause),
> **10** (bring-up — procurement first per SD-2's ruling, fleet gated on AC-11's
> RoPA, which is Cray's to author). ⚠️ **A hazard Step 7 must not walk into:**
> the operate-demo seed gate in `services/api/main.py` sits inside a
> `vertical == "procurement"` branch, so flipping `OCT_DEMO_SEED_OPERATE` alone
> for fleet is a **no-op that reads like a fix**. ⚠️ **AC bookkeeping:** the
> PLAN's checkboxes read `[ ]` for all eleven ACs on disk because Code cannot
> edit `docs/plans/` (G2 gate) — trust this record, not the checkbox tally.

> **Session 220, 2026-08-10 (head_commit `ac93b64` → `f78068e`) — two code PRs
> merged (#1114, #1116), 0 open. Theme: PLAN-0103 Steps 4b + 5 — every
> published system now has a profile of its own, and per-system isolation stops
> being a convention and becomes a guarded property.**
>
> ✅ **Steps 4b and 5 are COMPLETE.** Step 4 authors three profiles and Step 5
> authors two allowlists; procurement's half landed first (#1114) and fleet's
> closed both Steps (#1116). 🔴 **AC-3 is still NOT closed, and not for the
> reason the half-way record gave:** it requires **five** committed artifacts
> per profile — `{docker-compose.yml, published.env, cloudflared/config.yml,
> README, card copy}` — and **the card copy has been written for NO system**.
> That is Step 8a. **AC-4 and AC-5 remain closed** as guarded properties, and
> the third profile now exercises them rather than merely inheriting them.
>
> **Step 4b — procurement's profile.** `deploy/published/oct-procurement/` is
> authored, all four artifacts, **DB-less**. Published set `G,F`, default `G`,
> **no personas** — SD-3 and SD-4 ruled jointly, so the profile answers "which
> views" and "who can act" in one shape rather than two.
>
> **AC-4 resolved the standing instruction energy's compose addressed to this
> PLAN.** The compose project `name:` is now the profile **directory** name —
> asserted equal by a guard, not left to convention — and the fixed network
> `name:` key is **dropped** so compose scopes the network per project instead
> of pinning every system onto one. Energy was renamed `vero-published` →
> `oct-energy` across the project, both containers, the prompt-log volume and
> the derived image tag, with the ripple carried through `deploy.py`,
> `test_deploy.py` and ~19 runbook commands.
>
> **AC-5 closed as a property, not a checklist.** New
> `tests/deploy/test_published_profiles.py` (**45 tests**): no committed file
> outside a profile names two or more `oct-*` labels, and each profile names
> only its own. That is the form that survives a third system being added by
> someone who never read this PLAN.
>
> 🔴 **Step 4a left six broken operator paths behind, and executing 4b is what
> found them** — two in `published-demo-redeploy.md` written as Windows host
> paths, four in `oct-energy/README.md`. All six fixed, plus **a guard that
> reads the runbooks as instructions** rather than as prose, so the next move
> cannot silently orphan a command again. Two comments in
> `oct-energy/cloudflared/config.yml` that **Steps 2 and 3 of this same PLAN
> had falsified** were also corrected — the allowlist **row** was and is
> correct; only the stated reasons were stale. Doc-vs-code drift inside this
> PLAN is now a pattern, not an incident (see the PLAN-0103 self-citation TODO).
>
> 🔴 **The rename does not follow the LIVE system, and that is now an owed
> migration.** Measured on MS-S1 read-only under Cray's typed §8 go:
> `vero-published` is **`running(2)`** — app up 43 h healthy, cloudflared up 2
> days — the `vero-published-prompt-log` volume **holds real data**, and the
> host checkout sits at `00ddca0`, far behind main. Docker does not follow a
> rename, so a plain `up -d` under the new name would raise a **second parallel
> stack** and leave the prompt log stranded. A **§0b STOP CONDITION** was added
> to `published-demo-redeploy.md` and the migration is carried as its own
> Active TODO — offline tests cannot see any of this.
>
> **Evidence:** `tests/` **3926 → 3971 passed** (+45), 8 skipped, 0 failed —
> the arithmetic closes exactly · **eleven non-vacuity probes**, each RED then
> restored green · `ruff` + `ruff format` + `mypy --strict services/` all
> clean. **AC-4 and AC-5 are both CLOSED**; **#1114's body** carries the tables,
> the probes and the open Tab G question.
>
> **Steps 4b + 5 CLOSED — fleet's profile and allowlist (#1116).**
> `deploy/published/oct-fleet-maintenance/` is authored, all four artifacts.
> Published set `A,C,F,H,I,J`, default **A** (SD-3). It is the only published
> system carrying **both personas** (LOCKED-5) **and** a database (LOCKED-1 /
> ADR-0037), so it is the first profile forced to answer questions the other
> two never raised.
>
> **The database is a grant, not a default.** Three services instead of two:
> `postgres:16-alpine` on this system's own network, its own named volume, and
> **no `ports:` key at all** — worth stating because the repo-root dev compose
> *does* publish 5432, so "not published" here is a deliberate departure rather
> than something inherited. Both credentials are **required host-env
> pass-throughs with no default**, in the postgres service *and* inside the
> `DATABASE_URL` the app composes at runtime.
>
> ⚠️ **Energy's recommender defaults would have opened fleet's own landing tab
> on five anomalies.** Fleet lands on Tab A and the five `OCT_RECOMMEND_*`
> values are energy's; fleet's `measured_value` is a repair quote in THB
> (readings 1,800 / 2,400 / 3,200 / 15,000 / 48,000), so energy's threshold of
> 90.0 breaches **all five**. The real boundary is the **฿5,000 DOA ceiling** —
> pinned at 5000.0, exactly two breach and they route to **two different
> tiers**, which is the fixture's stated design intent: the demo shows the
> ladder ROUTING, which a single-breach fixture cannot.
>
> **The allowlist is 21 rows and every re-admission carries its own written
> basis**, because the original exclusions never shared one. Tabs I/J were
> excluded on SD-1(a) **DB-less** grounds — a basis that simply **dissolves**
> for a system ADR-0037 grants a database. Tab H's five routes were excluded by
> default-deny plus SD-1's C-3, which is **not** a storage fact, so `/runs`,
> `/runs/{id}`, `/runs/{id}/gate/resolve`, `/runs/{id}/cancel` and
> `/audit/verify` are each admitted on their own merits. Only routes the UI
> actually drives are admitted, and the export admits the **cover only**,
> keeping the typed s192 ruling in force.
>
> **Two new guards — and the second was widened by a probe that was itself
> mis-aimed.** (i) Only an ADR-0037-granted profile may declare a database,
> asserted in **both** directions. (ii) Every credential-bearing env value must
> be a required pass-through. The non-vacuity probe for (ii) switched the
> credential inside the app's `DATABASE_URL` connection string to a `:-`
> default and the guard stayed **green**: it was reading only
> `postgres.POSTGRES_PASSWORD`. The probe was mis-targeted, and **in failing it
> exposed a real hole in the assertion** — so the guard was widened to cover
> the connection string too.
>
> **Evidence (#1116):** `tests/` **3971 → 3994 passed** (+23), 8 skipped; the
> profile module collects **68** (was 45) — 45+23=68 *and* 3971+23=3994, so the
> arithmetic closes both ways · **nine non-vacuity probes**, each RED then
> restored green · **all three composes validated with `docker compose config
> --quiet` (exit 0)** — schema-valid, not merely YAML-parseable, and that check
> caught a real defect (the app service mixed sequence and mapping form in one
> `environment:` block, which is invalid YAML) · `ruff` + `ruff format` +
> `mypy --strict services/` clean.
>
> **What remains on PLAN-0103:** Steps 6 (persona picker), 7 (fleet's Tab H
> seed), 8 (card copy + portal request), 9 (MS-S1 headroom measurement), 10
> (bring-up). Two are live candidates and the choice between them is Cray's,
> not this record's: **Step 8a card copy closes AC-3 for all three systems at
> once**, while **Step 6's only consumer is fleet**, which now exists.

> **Session 219, 2026-08-10 (head_commit `faf48b6` → `ac93b64`) — two code PRs
> merged (#1109, #1111) plus the #1110 reconcile, 0 open. Theme: PLAN-0103 Steps
> 2 + 3 — published-ness stops being guessed and becomes **declared per system**,
> and the last guess left in the surface now refuses instead.**
>
> **Step 2 (#1109) — the declaration.** `PUBLISHED_EXCLUDED_VIEWS` is gone.
> `config.ALL_VIEW_KEYS` + `ui_published_views` refuse the process **at boot** on
> an unknown key, an empty set or a repeat; `main.py` emits `<meta name="ui-views">`
> from the **same substitution** as the profile tag, so the pair cannot
> half-arrive; `/meta` carries the same set (a test asserts the two carriers agree
> on a **non-default** value); `app.js` maps the keys **in order**, first = landing tab.
>
> **What Cray ruled (typed).** A page that declares no views **refuses to render
> and says so** — never guesses: a calm panel with no internals for the visitor
> plus a short statement of what vero-lite is (the failure page doubles as the one
> honest place to say it), and the precise diagnostic on the operator's console.
> The **empty-set boot refusal** is Code's extension of that reasoning
> (deploy-time terminal, never a visitor's browser) — flagged as inference, not
> ruling, and accepted. Cray also **took** Step 3's *optional* hero hardening.
>
> **Step 3 (#1111) — the last guess closed.** `_FALLBACK_VERTICAL = "procurement"`
> served procurement's hero to any vertical lacking one: correct while exactly one
> system was published, inverted by multi-system, since a hero is **bespoke per
> design partner** (ADR-0032 D1.2) — the failure mode is a Fastenal hero under an
> energy banner, which is why PLAN-0100 had to *edge-exclude* Tab G. Refusal moves
> from the **edge** (an allowlist that must remember to exclude G for every future
> heroless vertical) to the **route**, which knows: a heroless vertical now 404s,
> and the docstring asserting the fallback as current behaviour was fixed.
>
> 🔴 **Closing it exposed a test-integrity defect, not a code one.**
> `tests/api/test_demo_hero_routes.py` asserts **procurement's** hero throughout
> (Fastenal's ledger, `AST-CNC-014`, `SUP-RAPIDMRO`) while booting the default
> `energy` — it reached those numbers *through the fallback*, so it read as "the
> hero routes work on a default boot" while proving "the fallback works". The
> fixture now pins `OCT_VERTICAL=procurement`; **no assertion changed.**
>
> 🔴 **Step 3's own text named the wrong targets — the THIRD doc-vs-code mismatch
> in this PLAN.** `view-flow.js` is Tab **D**, published by energy all along and
> never unreachable; `view-monitor.js` has **no `isPublished()` at all**. Corrected
> scope: `view-hero.js` (G — dead branch today) and `view-monitor/case/export.js`
> (H/I/J — **no branch, which is correct**: fleet has a Postgres and Step 5 puts
> those on fleet's own allowlist). Property: publishing them adds no *unguarded*
> excluded-backend call — measured zero, now tripwired.
>
> **AC-2 is FULLY CLOSED** (first clause #1109, second #1111) and **AC-1 closed in
> #1109** with two documented literal-wording gaps; AC-2's census was wrong in both
> prior records (`was an error`) — **9** call sites, not 11. Record: PLAN-0103 row.
>
> **Evidence, both steps:** ruff + `ruff format` clean · `mypy --strict services/`
> Success (133 files) · `tests/` **3915** then **3926 passed / 8 skipped / 0
> failed** (3906 +10 −1, then +11 — exact arithmetic is the check that nothing
> vanished) · **nine non-vacuity probes RED**, notably Step 3's probe 1, which
> **restored the real fallback** rather than breaking the function, so the 404 test
> discriminates closed-vs-open and not working-vs-crashing · Step 2 also driven
> **live in a browser**. **#1109 / #1111 bodies** carry the tables and the probes.

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
| 2026-08-11 | **s222 — PLAN-0103 AC-8 clause 2 CLOSED in substance and ADR-0037 D2.7 MEASURED (#1124): no visitor-typed case text in the audit chain, `case_id` recoverable, asserted over EVERY `audit_log` row on both the ordinary and the waiver→ratify paths, via a positively-controlled bracketing sentinel + a structural payload-key allowlist.** ⚠️ `WaiverInvocation.justification` and the ratify `note` ARE human free text by design — possibly its own RoPA line. 🔴 #1125 retracted a false claim (a middle-slice leak IS invisible to both oracles) and records **RULED (Cray, typed, s222): that residual risk is ACCEPTED**, revisit condition stated in place. ⚠️ **D4 is UNBLOCKED, NOT decided**; the AC checkbox is NOT ticked (G2) | `3a11e87` (head_commit) / [#1124](https://github.com/CrayJThiemsert/vero-lite/pull/1124) / [#1125](https://github.com/CrayJThiemsert/vero-lite/pull/1125) / `tests/api/test_visitor_case_to_monitor_scenario.py` |
| 2026-08-10 | **s221 cont. — PLAN-0103 Steps 7 and 8b SHIPPED (#1122, #1121), so AC-8's first clause and AC-9's evidence are complete; #1123 made `render-handoff` report live goal state.** 🔴 **RULED (Cray, typed): NO portal REPO will be created** — Step 1's answer, unrecorded through three sessions. ⚠️ The portal/landing surface **still EXISTS**: DNS, Access policies and the landing surface are configured in the **Cloudflare dashboard**, one `oct-<vertical-id>` subdomain label per system; **ADR-0036 D2's two-artifact price is unchanged** — dashboard config, not repo files. The Step 8b request is **parked, not sent**, and the landing page is built by nobody. Also ruled: **Step 7 before Step 6**, and SD-8 ruled before Step 6 is built | [#1121](https://github.com/CrayJThiemsert/vero-lite/pull/1121) / [#1122](https://github.com/CrayJThiemsert/vero-lite/pull/1122) / [#1123](https://github.com/CrayJThiemsert/vero-lite/pull/1123) / `docs/logs/2026-08-10-plan0103-step8b-portal-assembly-request.md` |
| 2026-08-10 | **s221 — energy's LIVE system MIGRATED and PLAN-0103 Step 9 headroom MEASURED (one typed Cray §8 go); Step 8a SHIPPED (#1119) so AC-3 CLOSES, and the self-citation TODO DISCHARGED (#1118).** The demo now runs as compose project `oct-energy` on `oct-energy_vero_oct`; `vero-published` is gone from the host in every form. The prompt log was verified **byte-identical on both sides** (per-file checksums) and the app proven able to **write** it as its non-root user — refuting the s215 silent-`OSError` mode, not assuming it absent. 🔴 **#1119 repaired a compose build context that could NOT build** — `context: ../..` was one directory short of the repo root, and `docker compose config --quiet` validates schema, not context, so "all three composes validate" had been reported while none could build. ⚠️ **Step 9 is MEASURED; AC-10 is NOT closed** (clause 2 = an explicit go per bring-up) and **ADR-0036 OQ-2 stays OPEN** — capacity was never its constraint. ⚠️ **AC-9 is NOT closed**: Step 8b still owed. Read the log, never a restatement | `e938cf6` (head_commit) / [#1119](https://github.com/CrayJThiemsert/vero-lite/pull/1119) / [#1118](https://github.com/CrayJThiemsert/vero-lite/pull/1118) / `docs/logs/2026-08-10-oct-energy-migration-phase2-and-step9-headroom.md` |
| 2026-08-10 | **s220 cont. — PLAN-0103 Steps 4b + 5 COMPLETE (#1116): fleet's profile + allowlist landed, so all three per-system profiles now exist.** `oct-fleet-maintenance` publishes `A,C,F,H,I,J` default **A** — the only system with BOTH personas (LOCKED-5) and a database (LOCKED-1/ADR-0037): postgres on its own network + volume, **no `ports:`**, both credentials required host-env pass-throughs. **21 allowlist rows, each re-admission on its own written basis** (I/J's DB-less basis dissolves; Tab H's five were never a storage question). Fleet's landing tab needed the DOA ฿5,000 ceiling as its recommender threshold, not energy's 90.0. 🔴 **AC-3 is NOT closed — the card copy exists for no system** (Step 8a). Evidence: 3971 → 3994 (+23), 9 probes, all three composes `docker compose config --quiet` exit 0 | `f78068e` (head_commit) / [#1116](https://github.com/CrayJThiemsert/vero-lite/pull/1116) / `docs/plans/0103-portal-landing-and-per-system-published-profiles.md` |
| 2026-08-10 | **s220 — PLAN-0103 Steps 4b + 5 SHIPPED (#1114): procurement has a published profile of its own (`G,F`, default `G`, **no personas** per SD-3/SD-4, DB-less), and per-system isolation became a GUARDED property** — compose project `name:` == the profile **directory** (guard-asserted), the fixed network `name:` **dropped** so compose scopes it per project, and 45 new tests assert no committed file outside a profile names two `oct-*` labels. Energy renamed `vero-published` → `oct-energy`. **AC-4 + AC-5 CLOSED.** 🔴 **The rename does NOT follow the LIVE stack** (measured `running(2)`, host checkout at `00ddca0`) — a data migration is owed before energy's next redeploy; see the Active TODO, not this row | `0acc4af` (head_commit) / [#1114](https://github.com/CrayJThiemsert/vero-lite/pull/1114) / `docs/plans/0103-portal-landing-and-per-system-published-profiles.md` |
| 2026-08-10 | **s219 — PLAN-0103 Steps 2 + 3 SHIPPED (#1109, #1111): `PUBLISHED_EXCLUDED_VIEWS` retired for a boot-validated, server-declared **per-system** view set on two agreeing channels (`<meta name="ui-views">` + `/meta`), and the `_FALLBACK_VERTICAL` hero fallback CLOSED — a heroless vertical now 404s instead of being served Fastenal's hero under another banner.** **Cray ruled (typed):** a page declaring no views **refuses to render and says so**; Cray also **took** the optional hero hardening. 🔴 **AC-2's consumer census was wrong in BOTH prior records** (`was an error`): **9** call sites, not 11. **AC-1 + AC-2 both CLOSED** | `ac93b64` (head_commit) / [#1109](https://github.com/CrayJThiemsert/vero-lite/pull/1109) / [#1111](https://github.com/CrayJThiemsert/vero-lite/pull/1111) / `docs/plans/0103-portal-landing-and-per-system-published-profiles.md` |
| 2026-08-10 | **s218 cont. — ALL EIGHT PLAN-0103 slots RULED (Cray, typed), and SD-1 spawned ADR-0037 `Proposed` (#1104).** 🔴 **SD-1 OVERRULED both the drafter and Code's R2 concurrence** — two reviewers agreeing was not independent evidence; both priced the cost of *having* an ADR and neither the cost of *not*. **ADR-0037** is the result and the home for two findings previously recorded nowhere (D6's LLM-route scope; the audit-chain erasure boundary, marked UNVERIFIED and made a pre-bring-up measurement, not asserted). **RATIFIED the same session (#1107)**: D1 = **(a) story-required** (DB-less stays a bound, not a preference) · D3 = **bound, don't amend** · D4 = **direction only**, its final ruling deliberately deferred until D2.7 measures whether visitor text reaches the chain — a controller promise cannot precede the measurement. ⚠️ **Nothing is blocked now**; the live obligation is AC-11 (the RoPA, Cray's to author) before fleet's bring-up | `9160f4f` (head_commit) / [#1104](https://github.com/CrayJThiemsert/vero-lite/pull/1104) / `docs/adr/0037-published-system-data-persistence-posture.md` |
| 2026-08-09 | **s218 — PLAN-0103 DRAFTED `Draft` (#1101): vero-lite's side of the multi-vertical portal, ADR-0036's D6 follow-on.** 10 Steps, 11 ACs, 7 SD slots; five Cray LOCKED calls. Built around the hard boundary — **zero portal-repo files, no landing page here**; card copy is one-system-per-file with **no roster** (AC-5 guards it). 🔴 Two findings reshaped it and are worth not re-deriving: **`isPublished()` has ELEVEN consumers across eight files**, so the constant is *eliminated* rather than a third profile added; and **fleet publishing Tab C makes a SECOND assisted system** on one Ollama, contradicting the premise ADR-0036 D5 wrote its aggregate posture on | `f2731be` (head_commit) / [#1101](https://github.com/CrayJThiemsert/vero-lite/pull/1101) / `docs/plans/0103-portal-landing-and-per-system-published-profiles.md` |
| 2026-08-09 | **s218 — ADR-0036 RATIFIED (Cray, typed): a deployed vertical instance IS a system (#1099).** Accepted as drafted (D1 scope (a), D2 + the `oct-<vertical-id>` label convention, D5 profile ownership, OQ-1 retire the bare `oct.` label); ADR-0035 D1–D4 untouched, D4's reopening trigger does not fire. ⚠️ **The ratifying edit must also remove the ADR from the gate's set-equality assertion in the SAME commit** — an in-flight marker, not an exemption; both directions of that rule were exercised within a day (ADR-0037 re-added it). Verified behaviourally with two controls, not just green | `1a6e29b` (head_commit) / [#1099](https://github.com/CrayJThiemsert/vero-lite/pull/1099) / `docs/adr/0036-vertical-as-system-multi-vertical-demo-portal.md` |
| 2026-08-08 | **s217 — PLAN-0102 COMPLETE 11/11 and ARCHIVED (#1096): the L1 loop-detect guard is RETIRED**, executing Cray's typed s205 ruling. Evidence: **zero true positives across its whole live history** against **≥ 56 denies / 4,201 ops** (~1.33 % of every edit hard-walled). No ADR amendment — L1 had zero ADR backing, so one would have CREATED the ratification it never had. 🔴 **Three PLAN defects found by executing it, one root cause worth carrying:** the scope review walked the call graph BACKWARDS from the marker and never FORWARDS from the functions being deleted — ⚠️ and **ruff flags a dead import but NOT a dead private function**, so an AC reading "ruff clean" passes over dead code | `36e5735` (head_commit) / [#1096](https://github.com/CrayJThiemsert/vero-lite/pull/1096) / `docs/plans/done/0102-retire-l1-loop-detect.md` |

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

- [ ] **PLAN-0103 — vero-lite's side of the multi-vertical portal. DRAFTED s218 (#1101), `Status: Draft`; Steps 2, 3, 4a, 4b, 5, 7, 8a and 8b are SHIPPED.** _[Corrected s221: this row opened "nothing built" from s218 and stayed that way for three sessions while its own body listed six shipped Steps — a header that contradicted its own contents.]_ ADR-0036's D6 follow-on: per-system published profiles + the landing/framing **content spec**. 10 Steps, 10 ACs, **7 SD slots**. ✅ **ALL EIGHT SLOTS RULED s218 (#1104)** — read them in the PLAN's §Surfaced decisions, each stamped `RULED (Cray, typed, s218)`. ✅ **ADR-0037 RATIFIED s218 (#1107), so nothing gates execution any more** — the whole PLAN is startable. 🔴 **One live obligation instead of a gate: AC-11 — the RoPA must cover fleet's posture BEFORE fleet's bring-up, and it is Cray's artifact as controller (the PLAN gates on it, cannot author it).** The Step-4 map that used to separate gated from ungated now reads as bring-up ORDER, not permission. Step 4 carries a **gate map** naming exactly what proceeds regardless — procurement's entire half, Steps 2–3, energy's move, Step 8's content, Step 9's measurement. It is written "read this before stalling anything" because a bare "ADR-gated" label reads as stop-everything: s206 lost a session to that misreading of PLAN-0100's headline when six items carried no gate. ⚠️ One caveat the map itself carries (Code R2): the **persona-picker UI is not gated but fleet is its only consumer**, so it is orphaned work if ADR-0037 ratifies otherwise than proposed — build it in parallel, never first. **Read the PLAN, never a restatement:** `docs/plans/0103-portal-landing-and-per-system-published-profiles.md` (§The hard boundary · §Surfaced decisions). ⚠️ Two things a future reader must not re-derive: the **hard boundary** — ADR-0036 D1 + ADR-0035 D4/L5 make the `portal.` landing surface, ingress map, Access policies and domain **portal-repo property**, so this PLAN builds no landing page here and ships a spec instead; and `isPublished()` has **ELEVEN consumers across eight files**, so any step touching published-ness must walk all of them (`tools/excision_scope.py` + the `excision-scope` skill). _[Corrected s219 by executing Step 2, `was an error`: the census is **9 call sites**, not 11 — the 11 counted `app.js:72`, a `PUBLISHED_EXCLUDED_VIEWS.indexOf` line and not an `isPublished()` site, and AC-2's own list enumerates 10 with the definition among them. Exactly **one** was tab-set; the other eight gate on the published *profile* for allowlist reasons. `tools/excision_scope.py` also does **not** apply to a JavaScript target — it is Python AST analysis, so walk-both-ways went by hand.]_ ✅ **Steps 2 + 3 SHIPPED s219 (#1109, #1111)** — the constant is gone, replaced by a boot-validated per-system declared view set, and `_FALLBACK_VERTICAL` is closed (a heroless vertical now 404s instead of being served procurement's hero). **AC-1 and AC-2 are both CLOSED** — AC-2's first clause by #1109, its second (the branch audit) by #1111. _[Step 3's own text named the wrong audit targets — the third doc-vs-code mismatch in this PLAN: `view-flow.js` is Tab D and was published all along, and `view-monitor.js` has no `isPublished()` at all. Corrected scope + the measured property are in #1111's body.]_ ✅ **Step 4a SHIPPED s219 (#1113); Steps 4b + 5 HALF SHIPPED s220 (#1114)** — energy moved to `deploy/published/oct-energy/`, procurement's own profile authored at `deploy/published/oct-procurement/` (published set `G,F`, default `G`, **no personas** per SD-3/SD-4, DB-less), and per-system isolation is now guarded by `tests/deploy/test_published_profiles.py` (45 tests). **AC-4 and AC-5 are both CLOSED** as guarded properties a third profile inherits automatically. ✅ **Steps 4b + 5 COMPLETE s220 (#1116)** — `deploy/published/oct-fleet-maintenance/` authored (published set `A,C,F,H,I,J`, default `A`, **both personas** per LOCKED-5, **with** the LOCKED-1/ADR-0037 Postgres: own network + volume, no `ports:`, both credentials required host-env pass-throughs), plus a **21-row allowlist in which every re-admission carries its own written basis** — I/J's DB-less exclusion *dissolves* for a DB-granted system, while Tab H's five routes were excluded by default-deny + SD-1's C-3, which is not a storage fact, so each is admitted on its own merits. The guard module now collects **68** tests (was 45); two new guards (ADR-0037-granted-only DB, asserted both directions; credential env values must be required pass-throughs). ✅ **Step 8a SHIPPED s221 (#1119) — AC-3 is now CLOSED.** It required **five** committed artifacts per profile — `{docker-compose.yml, published.env, cloudflared/config.yml, README, card copy}` — and the fifth, `card-copy.md`, now exists in all three profiles, bilingual TH/EN, structurally guard-asserted. 🔴 **The same PR repaired a compose build context that could not build:** `context: ../..` from `deploy/published/<system>/` reaches `deploy/`, one directory short of the repo root, and all three profiles inherited it from Step 4a's move — while `docker compose config --quiet` returned 0 over all three, because it validates the **schema**, not whether the context resolves. Now `../../..`, guarded. ✅ **Step 9 MEASURED s221** under Cray's typed §8 go — **AC-10's first clause is discharged; AC-10 is NOT closed**, its second clause (every bring-up carries its own explicit §8 go) stands — and ⚠️ **ADR-0036 OQ-2 remains OPEN**: container capacity was never its constraint. 🔴 **AC-9 is NOT closed** — its second clause, the portal-side assembly request (Step 8b), is still owed and is a Step 10 input. ✅ **Steps 7 + 8b SHIPPED s221-tail (#1122, #1121); AC-8 clause 2 CLOSED s222 (#1124) and AC-9's evidence complete — both in SUBSTANCE only** (see AC bookkeeping). The s221 "no-op that reads like a fix" hazard is **discharged**: the `main.py` seed gate now branches on `fleet_maintenance`. Detail is in the s222 Current Focus block and the artifacts, not restated here. 🔴 **Step 1 ANSWERED (Cray, typed): no portal REPO will be created** — ⚠️ in full, because the shorthand has been misread as "no portal": the portal/landing surface **still exists**, with DNS, Access policies and the landing surface configured in the **Cloudflare dashboard**, each system on its own `oct-<vertical-id>` subdomain label; **ADR-0036 D2's two-artifact price per system is unchanged** — dashboard config rather than repo files. ⚠️ The Step 8b request is **parked, not sent**, and **the landing page itself has been built by nobody**. **Remaining: Steps 6** (persona picker — ⚠️ **SD-8 is NOT RULED and Cray ruled it must be ruled before Step 6 is built**) and **10** (bring-up — procurement first per SD-2, fleet gated on AC-11's RoPA, Cray's to author). ✅ **Both obligations Steps 4b/5 left owed are DISCHARGED s221** — energy's live-system migration ran, and the stale self-citations were corrected by #1118; see the two rows immediately below. ⚠️ **AC bookkeeping:** the PLAN's checkboxes read `[ ]` for all eleven ACs on disk because Code cannot edit `docs/plans/` (G2 gate) — trust this record, not the checkbox tally. **AC-8 and AC-9 are closed in SUBSTANCE and NOT ticked**; the tick is owed to a `plan-drafter` dispatch, and until it lands the PLAN must not be read as recording them done.
- [x] ✅ **energy's LIVE system data migration — DONE s221, under Cray's typed §8 go (one go covering both the migration and the Step 9 measurement).** energy now runs on MS-S1 as compose project **`oct-energy`** on network `oct-energy_vero_oct`; project `vero-published` no longer exists on the host in any form — containers, network or volume. **Neither hazard this row was raised for can still fire:** there is no second parallel stack, and the erasure paths in `docs/runbooks/published-demo-operations.md`, which address `-p oct-energy`, now reach the volume that actually holds the prompt log. The rows were migrated volume→volume and verified **byte-identical on both sides** (per-file checksums, not merely sizes), the running app was proven able to **write** the log as its non-root user — refuting the s215 silent-`OSError` mode rather than assuming it absent — and the old volume was removed **last**, with the off-host backup still in hand at that moment; that backup held personal data outside the retention system and was deleted once the edge check passed. **The stop condition at `docs/runbooks/published-demo-redeploy.md` §0b now returns empty.** **Read the record, never a restatement:** `docs/logs/2026-08-10-oct-energy-migration-phase2-and-step9-headroom.md` (§Part 2 for the pre-committed pass/fail reads and results; §"Two things the run could NOT prove" for what is deliberately still open; §"Instrument failure" for the downtime overrun, which was diagnosis time and not migration work).
- [x] ✅ **PLAN-0103's stale self-citations — DISCHARGED s221 by #1118.** All four corrections landed in the PLAN itself (Step 3's wrong audit targets, the moved operate-demo seed-gate citation, AC-4's pre-Step-4a compose path). **The fourth item this row carried is no longer a STATUS-only question:** whether Tab G's "Act — the human DOA gate" card should render at all on a personaless system is now homed **in the PLAN as SD-8, explicitly NOT RULED**, with three neutral options and no step assuming an answer. It is Step 6's question and **Cray's call**. Read it there, never a restatement: `docs/plans/0103-portal-landing-and-per-system-published-profiles.md` §Surfaced decisions (SD-8).
- [ ] **Ungated items rehomed s219 out of the `next_action` frontmatter — they survived ONLY there, and R3 caps that field to one short line.** (1) ✅ **PLAN-0103 Step 9's MS-S1 headroom is MEASURED s221** (`docs/logs/2026-08-10-oct-energy-migration-phase2-and-step9-headroom.md`) — RAM and CPU do not constrain a second or third published system, and AC-10's first clause is discharged. ⚠️ **ADR-0036 OQ-2 does NOT follow from it and remains OPEN:** the aggregate in-flight LLM posture is a different question — the constraint on a second *assisted* system is the resident model and concurrent in-flight calls, not container footprint — and one term in the projection (Postgres idle) is declared unmeasured rather than folded silently into the total. (2) **The public one-pager — never drafted.** (3) **ADR-0037 D4's FINAL ruling is still Cray's — now UNBLOCKED, still UNDECIDED.** It was deferred until D2.7 measured whether visitor case text reaches the audit chain; **s222 MEASURED it (#1124): it does not, on both the ordinary and the waiver→ratify paths, and `case_id` stays recoverable** — so the precondition is discharged and the ruling is not. ⚠️ One input D4 must price that the measurement surfaced: `WaiverInvocation.justification` and the ratification `note` **are** human free text in the hash-chained log by design — a named internal principal's, not the visitor's — which may need its own RoPA line. ⚠️ And the one hole the oracles do not close, **ACCEPTED (Cray, typed, s222)**: a middle-slice carrier is invisible to both; revisit if an audit payload gains a field legitimately holding a SLICE of operator-entered text. (This is the durable home; the Recent Decisions row rotates.) (4) **Edge cache-purge needs a Cloudflare API token = a new secret + host-state**, which is why the purge step in the PLAN-0100 row below is not simply "add a step". _(The remainder of that field — D-4 option (a)'s four seams in `nl_query.py`, versioned font URLs, the unpinned `OLLAMA_KEEP_ALIVE` — is already homed in the PLAN-0100 row and is not duplicated here.)_
- [ ] **PLAN-0100's residuals outlive the PLAN** (COMPLETE 13/13 and ARCHIVED s216; the demo is LIVE, REDEPLOYABLE and DRIVEN). **Read the archived PLAN, never a restatement:** `docs/plans/done/0100-exposure-published-demo-surface.md` (§"Step 11 closure verdict"; §"Defects the live run found" for D-1..D-5, incl. the *transient* D-5 Safe-Browsing flag on the Access login callback, cause UNDETERMINED; §Instrument failures). _[s222: the completion narrative is dropped per R2's ratified Active-TODO rule — `[x]` items older than the session window go, git history + the archived PLAN hold them. Only the live residuals stay.]_ **Live, and recorded ONLY here:** (1) **D-4 RULED s217 (Cray, typed): option (a), teach the engine — nothing built, no PLAN drafted, still the largest ungated Code item.** ⚠️ Its price was corrected (`was an error`): every prior record framed (a) as "teach the translator `group_by`", implying open-ended prompt work, but `group_by` already works for `max`/`min`/`avg`/`sum` — what is unrepresentable is **`count` WITH `group_by`** (`_AGGREGATE_OPS` excludes it, `services/engine/nl_query.py:75`, rejected outright at `:536`), so (a) is **four seams in one file** (`:536` relax · `_compute_aggregate`/`_collect_numeric` `:770-810` · `_AGG_LABEL`/`_phrase_aggregate` `:1050-1067` · `_infer_group_by` `:907`) ≈ one PR + tests. (2) **No cache-purge step or versioned font URLs** in the redeploy runbook — nothing in the pipeline purges the edge and `?v=cNN` does not reach fonts; a purge needs a Cloudflare API token = a new secret + host-state. (3) **`published.env` pins no `OLLAMA_KEEP_ALIVE`**, so the published surface silently inherits the code default of 30m.
- [ ] **Assembly-cost axis — MEASURE it before an ADR argues it (Cray typed s197); nothing built, no PLAN drafted.** Build the tripwire that puts a number on assembly cost first, *then* draft the ADR on top of that number — the ordering is the ruling. **The series measured so far is banked HERE because it is banked NOWHERE ELSE in the repo — no test, no doc, no PLAN holds it:** churn per vertical went **1:1.8 → 1:6 → 1:1.1**, i.e. **spiky, not falling**, which is the shape any ADR on this axis has to argue against. Left unbanked it survives only in session memory and dies at the next context reset; a tripwire that recomputes it is what makes it evidence rather than a recollection.
- [ ] **Seam-scoped mutation-testing CI — a PLAN candidate, NOT built.** Surfaced s188 as the one CHECKABLE variant the scenario-test hook rejection does not cover; **rehomed here s191** when its parent `[x]` row was pruned, because STATUS was its only home. A CI job that requires the scenario suite to REDDEN under a seam mutation: ritual compliance cannot fake it, since an empty or stubbed scenario suite stays green under mutation — exactly what a file-existence hook would miss. Rationale: `CLAUDE.md` §8's scenario-test bullet.
- [ ] **PLAN-0096 partner round-2 — ANSWERED s189; five of seven closed, one non-blocking follow-up open.** A1 → Step 6 built (#965); A3 → `pm_due` built (#968); **A4 + A7 confirmed values already shipped** (flat ฿5,000 ceiling, `"30001"` inclusive floors); A5 **parked** — no real Wialon export exists yet. **A2 is answered and consumed by Step 8** (no longer a gate). **Open, NON-blocking: cost-center (ศูนย์ต้นทุน) granularity — per truck or per company?** Ship the column, fill the rule when it lands. A6 is answered but is a Step 9 *runbook* item. Detail: `docs/plans/done/0096-fleet-flow-completion-phase1.md`.
- [ ] **The AT-2 extraction — only the F-FACTORY half remains, owned by PLAN-0076 T1.** The criterion-vocabulary half SHIPPED as PLAN-0087 (COMPLETE 8/8, ARCHIVED — #840/#841); ADR-0025 D7's generator deferral was CANCELLED at N=4 (Cray-ratified, typed); SD-1 = (a) keeps the procedure-aware `ExecutorFactory` half with PLAN-0076 T1, guard `test_at2_extraction_obligation_is_owned` ARMED. Full detail: `docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` + `docs/plans/0076-*.md` §A.
- [ ] **PLAN-0075 follow-ons — homed by PLAN-0076 (`Status: Tracking`, #752, s133).** T1 (ADR-0031 D3 gate-plugin seam, F-FACTORY) is PARTIALLY discharged — the criterion-vocabulary half shipped as PLAN-0087; the procedure-aware-`ExecutorFactory` half stays OPEN here. T2's F-PIN remainder CLOSED s143 (#784), but **F-PIN itself stays OPEN**, so PLAN-0076 does NOT archive and its AC-6 presence guard stays ARMED. Full detail: `docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` §A.
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
