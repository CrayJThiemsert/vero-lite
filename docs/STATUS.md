---
last_updated: 2026-08-19T10:45:00+07:00
session: 239
current_batch: "s239 — EIGHT PRs (#1216-#1223), 0 open, and TWO host-state deploys to MS-S1 under separately typed gos. The video rulings rehomed tracked (seven, not four). Tab F opens the origin narrative with six passages mapped to six steps. DEPLOY.md created for this system and corrected on its first real use. The brand mark is live."
current_actor: code
blocked_on: "NOTHING blocks repo work; main is green, 0 open PRs. ADR-0037 SD-1 stays Cray's — unruled across EIGHT sessions. ADR-0038's three-strike counter still has NO owner."
next_action: "Cray's pick: name the three Advisory-proposal candidates so the gate panel stops reading as unfinished (small, unblocks the video); measure the run-list backlog badge on the host now that DEPLOY.md makes host reads routine; PLAN-0109 execution (Ask over repair cases); or PLAN-0107 Phase B. The font-size decision gates re-measuring every geometry number in the beat-4 mockup."
head_commit: dbb3e58
recent_commits: [dbb3e58, b1701b4, 71e7723, 54fb7a6, d665c3e, 907a842, ca10604, e08bb73, c01dd2a, 75690ec]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 239, 2026-08-18→19 (head_commit `32854ab` → `dbb3e58`) — EIGHT PRs
> MERGED (#1216–#1223), 0 open, and TWO host-state deploys to MS-S1 under two
> separately typed §8 gos.**
>
> 🔴 **The organising finding, and it is not about any one artifact: a summary
> that is ACCURATE about what it cites still shrinks.** s237's handoff cited the
> storyboard's ruling table (four rulings) and was correct; s238 inherited that
> and was correct; the actual count was **seven**, because one was typed two days
> earlier and recorded INLINE in the beat it governs rather than in the table —
> and it is the one with a live tripwire (*"a number enters beat 2.5 or 4"*).
> Going to the ORIGINATING artifact rather than the latest summary is what
> recovered it. Everything now lives in `docs/strategy/public/intro-video-production-rulings.md`,
> tracked, each row carrying its **date and source position** for exactly this
> reason. Before #1216, `git grep` over the repo returned **ZERO** hits for the
> CTA ruling, `barely say`, `verify-chain` and `founder on camera`.
>
> 🔴 **A correct fix silently disarmed the guard that was watching it — measured,
> and the more transferable half of the session.** s238 rightly corrected every
> documented host path to forward slashes, because a backslash is stripped by the
> ssh→PowerShell chain and fails as a missing file. `test_every_documented_operator_path_resolves`
> accepted a drive letter only before a **backslash**, so that correction moved
> ten `docker compose -f C:/…` commands OUT of its reach and the guard matched
> **zero** of them. ⚠️ **The module's own anti-vacuity floor (`checked >= 5`)
> stayed satisfied by the READMEs the whole time** — a count floor cannot see a
> category of document going dark. Widened to every profile `*.md` and the regex
> fixed: **26 paths checked, 0 broken**, eight of them previously unreachable and
> three (`DEMO-RESET.md`) unchecked since the day they were written.
>
> 🔴 **The shared deploy script cannot deploy this system, and the runbook handed
> it over without saying so.** Plan mode — which touches nothing, verified in the
> code rather than taken from the docstring — printed `oct-energy` in every
> literal. `--execute` would have built and shipped the wrong profile's image and
> recreated a container on a system nobody meant to touch. The fact was already
> recorded in three places, none of them where §3 sends a reader: a **routing**
> gap, not a knowledge gap. Fixed at the point of handover (#1220), and the
> missing procedure now exists — `deploy/published/oct-fleet-maintenance/DEPLOY.md`
> (#1221), the procedure tier this system never had. Its **first real use found
> its own gap**: §2 said to diff `<last-deployed-sha>..HEAD` without saying the
> sha comes from the HOST's checkout, which is not the image's build sha — here
> `205ba4b3` vs `907a842`. Corrected in the same PR as the deploy record (#1223).
>
> ✅ **Tab F now opens the raw customer story its procedure was formalised from**
> (#1218), with six passages numbered against `governed_repair_approval`'s six
> steps and the legend built from the procedure's **live** steps. `reshape` is
> deliberately left unmapped and the legend says so — it is platform machinery,
> not a rule the business stated, and forcing a sentence onto it would make the
> panel's claim false in the one place a careful viewer checks. Needs no
> infrastructure: `^/assets/.+$` is already allowlisted, `connect-src 'self'`
> already admits the fetch, Tab F is already published under SD-3. It had to live
> under `services/` because the Dockerfile COPYs that and **pointedly not `docs/`**.
>
> ✅ **R8 RULED (Cray, typed): drop the ฿15,000 contrast from beat 4** (#1217).
> Measured this session and recorded by no prior artifact: the remap trades a
> **demonstration** for a **declaration** — no published tab renders the second,
> cheaper repair routing to the fleet manager. Option (b), asserting it over Tab
> A's rings, was rejected as dishonest and the measurement made it worse than it
> looked — Tab A shows **three** anomalies, not the two `published.env` documents,
> and two of the three exceed the band floor.
>
> ✅ **The header brand mark is the Cray.J logo** (#1222), deployed and confirmed
> by Cray on the live surface. Recorded rather than discovered later: it is **not
> legible at 28 px** — the artwork paints at 7% of source scale, so the wordmark
> inside it renders about 16×4.6 px. Cray chose that form knowingly from three
> options; the fix is cropping the artwork to the bunny and needs no code change.
>
> **Both deploys were do-no-harm verified against a baseline captured BEFORE the
> first action**: this system's `cloudflared` and `postgres` kept their container
> ids and uptimes both times — the tunnel never re-registered, `pgdata` was never
> at risk — and both sibling systems' four containers were untouched. The demo
> read `DEMO-STATE: PRISTINE` before and after each, so **`--execute` appears
> nowhere in what was executed** and no row was deleted. Image id **IDENTICAL on
> both machines** each time, which is the guarantee — "a rebuild produced the same
> id" is not, since buildkit's provenance attestation makes an id identify a build
> rather than its content.
>
> ⚠️ **The half neither deploy could close: the render through Cloudflare Access.**
> It needs an interactive PIN no automated step can satisfy. Cray closed it both
> times by opening the live system, and both records say so — recorded as **Cray's
> observation, not this process's measurement**, because blurring that would make
> the next deploy's "verified" weaker than it reads.
>
> **Gates: 4170 passed / 8 skipped**, `mypy --strict services/ verticals/` clean
> over 201 files, bare `ruff check .` + `ruff format --check .` clean over 642.
> Twenty-two non-vacuity probes across the session, each restored from a `/tmp`
> copy and each seen RED with a message naming what broke. Host records:
> `docs/logs/2026-08-18-s239-fleet-origin-narrative-deploy.md` and
> `docs/logs/2026-08-19-s239-brand-mark-deploy.md`.

_[The sessions-233–234 block rotated to `docs/status-archive/2026-h1d-current-focus.md`
this reconcile, keeping the window at four sessions.]_

> **Sessions 237–238, 2026-08-18 (head_commit `de3295a` → `32854ab`) — SEVEN PRs
> MERGED (#1208–#1214), 0 open. PLAN-0110 drafted, ruled, built and DEPLOYED in
> one arc; s237 was never separately reconciled, so this block carries both.**
>
> 🔴 **s237's method, and it is the transferable part: measuring the LIVE demo
> refuted the intro video's central beat.** Beat 4's three shots film **Tab G**,
> which the published profile does not serve — excluded **by ruling** (SD-3 s218 +
> ADR-0032 D1.2), while the storyboard was verified on a local dev profile where
> all ten tabs render. Cray ruled (A): shoot on the published profile. Measuring
> the replacement found **Tab H carries the whole beat in ONE frame, no scrolling**
> (`docH == viewport == 737`), against Tab G's two halves 797 px apart.
>
> 🔴 **A real fleet defect, found on the LIVE system, with a NON-obvious second
> layer** (#1209). Tab H showed a **settled** repair — invoice keyed, case CLOSED —
> sitting in the visitor's approval queue. Root cause: `seed_settled_history_case`
> resolved the gate without resuming; **and one resume is not enough**, because
> `governed_repair_approval`'s TERMINAL step is itself `autonomy: gated`, so
> resuming once parks the run again at `fulfill`, still `waiting_human`. **The
> money was never wrong**, which is why no offline oracle noticed — the defect
> lived in a run's status field, on a screen counting RUNS while every assertion
> counted CASES. An instrument existed and was aimed one field to the left.
>
> ✅ **PLAN-0110 COMPLETE 7/7 and ARCHIVED** — Tab A run markers, a three-mode run
> filter, and a deploy-time demo reset ([#1213](https://github.com/CrayJThiemsert/vero-lite/pull/1213) code,
> [#1214](https://github.com/CrayJThiemsert/vero-lite/pull/1214) evidence).
> 🔴 **The measurement that reversed the obvious design:** the parked gate carries
> **three** proposals and **all three name a `case_id`** — two exist only in the
> fixture and resolve to no row. Reading `truck_id` off the ingested event (the
> shorter path) yields three trucks, trips the ambiguity guard, and stamps
> **nothing, forever**, with every test green. The `repair_case` lookup is the
> discriminator, not a formality.
>
> ⚠️ **TWO divergences from PLAN-0110's own wording, named in its Status block
> rather than left in a diff:** Step 3's *"one transaction"* is incompatible with
> reusing `delete_case` (which owns its commit + rollback by PLAN-0105 contract);
> and Step 4's runbook location **reddened the ADR-0036 D2 label guard**, so the
> operator procedure ships in the profile directory instead.
>
> ✅ **Step 7 DEPLOYED to MS-S1 under a typed §8 go.** `DEMO-STATE: CONSUMED` →
> `PRISTINE`; both demo runs gained a `subject` (`NULL` before, so Tab A could key
> no marker); `run-fleet-demo-history` went `waiting_human` → **`completed`**, so
> #1209's fix is finally live. Audit rows **9 → 17, never decreased**. Only `app`
> recreated; postgres + cloudflared kept their container ids.
> 🔴 **The deploy found a gap in a file merged hours earlier:** `DEMO-RESET.md`
> prescribes reset-then-`up -d`, but **the tool ships inside the image it must run
> before** — impossible on a bootstrap deploy. It fails safely (no token = failed
> check, by that file's own rule); §2a now documents the four-step form.
> Full record: `docs/logs/2026-08-18-plan0110-fleet-demo-reset-deploy.md`.
>
> 🔴 **CARRIED RISK — s237's video rulings exist ONLY in a gitignored handoff**
> (`.claude/handoffs/session-237/…-CLOSE-…`): Cray's option-(A) ruling, the CTA
> decision (*no demo URL on screen*, or viewers hit the Access wall), and the
> beat-4 Tab G→H remap. `git grep` finds none of it. Needs a tracked home before
> the clip is shot.

> **Session 236, 2026-08-17→18 (head_commit `218a521` → `de3295a`) — FOUR PRs
> MERGED (#1201–#1204), 0 open. The session that paid s235's STATUS debt in full
> and then built the first four oracles PLAN-0107 asks for.**
>
> ✅ **STATUS is reconciled and PR-B is COMPLETE — 61,736 → 48,852 B, under R1's
> 49,152 B soft target for the first time in this chain**, headroom 3,800 →
> **16,684 B**. The rehome, not the trim, is what paid: every carve-out fact moved
> to **the artifact whose reader needs it**, then the row collapsed to a pointer
> (PLAN-0100's residuals → its own §Post-archival amendment, 2,202 → 480 B). Six
> facts came out of a **gitignored** handoff into
> `docs/logs/2026-08-17-s235-audit-findings-outside-adr-0038.md`; nine rows out of
> STATUS into code, tests, a benchmark module and `docs/logs/`. **Read those, never
> a restatement.**
>
> ✅ **PLAN-0107 Phase A CLOSED 6/6** (#1204) — CI gained four oracles it did not
> have: `node --check` over every shipped JS asset · an asset↔reference
> **bijection** (chosen over a floor constant: a `≥ 20` floor over 21 files has one
> file of headroom and its misfire remedy is editing the number) · a **per-vertical
> lifespan boot smoke** · `mypy --strict verticals/` plus the two pre-commit hooks
> that had only ever run on a developer's laptop. **Measured bill: `gate` 7m53s →
> 9m7s ≈ +74 s, no new dependency.** Verified at **step level**, not job level — a
> green job cannot distinguish a step that passed from one that was skipped.
>
> 🔴 **AC-3's own central claim was MEASURED FALSE in the configuration CI runs.**
> The AC said the smoke makes §3's fail-loud contract CI-visible; corrupting each
> spec in turn, it is **CAUGHT** for fleet_maintenance, building_materials,
> supply_chain and procurement and **MISSED for `energy`** — the **default**
> vertical, and the one spec-shipping factory that never calls `load_procedures`.
> Booting only the default would have been green and blind to exactly what CI runs.
> Fixed by booting once per spec-shipping vertical; **the `energy` residual stays
> OPEN** in `tools/ci/boot_smoke.py`'s docstring.
>
> 🔴 **CI caught what no local probe structurally could.** Phase A's first run died
> on `ModuleNotFoundError: No module named 'services'` — the runtime venv is
> `--no-install-project` by design, and `python <file>` puts the *script's*
> directory on `sys.path` where `python -c` put the CWD. **Every local run used the
> dev venv, which has the project installed, so the failing state was unreachable
> there.** A ② *reach* failure inside the PLAN that exists to close ② failures.
> Fixed by **building** that condition locally and reproducing the error, not by
> reasoning about it.
>
> 🔴 **ELEVEN inherited claims were checked and EIGHT were wrong** — including two
> live falsehoods in STATUS itself (`deploy.py`'s "broken" compose path, fixed a day
> earlier; *"AC-11's RoPA is still Cray's"*, adopted at s233), a guard cited at the
> wrong file, and a scenario census stale in both figures (13/63 → **14/69**, the
> third drift of that number). **The base rate is high enough that checking an
> inherited claim is not optional.**
>
> **Gates, every PR: `pytest tests/` 4115 → 4123 passed / 8 skipped**, `mypy
> --strict services/ verticals/` clean over **200** files, ruff + format clean over
> 634, CI `gate` pass.

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

this reconcile, keeping the window at four sessions.]_

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
| 2026-08-19 | **s239 — EIGHT PRs (#1216–#1223) and TWO host-state deploys under separately typed gos.** 🔴 **An ACCURATE summary still shrinks:** the video rulings were seven, not four — one typed two days earlier and recorded inline rather than in the table, carrying a live tripwire. Rehomed tracked, each row stamped with its source position. 🔴 **s238's correct forward-slash fix silently disarmed the path guard** for the ten commands it corrected, and the module's own `checked >= 5` floor stayed satisfied by the READMEs — a count floor cannot see a document category go dark. Now 26 paths checked, 0 broken. 🔴 **The shared `deploy.py` cannot deploy this system** and §3 handed it over without saying so; `DEPLOY.md` created, and its FIRST use found its own gap (`<last-deployed-sha>` comes from the HOST checkout, not the image's build sha). ✅ Tab F opens the origin narrative with six passages mapped to six steps, `reshape` deliberately unmapped. ✅ R8 ruled: drop the ฿15,000 contrast. ✅ Brand mark live — and **not legible at 28 px**, recorded rather than discovered later. | `dbb3e58` / [#1218](https://github.com/CrayJThiemsert/vero-lite/pull/1218) / [#1221](https://github.com/CrayJThiemsert/vero-lite/pull/1221) / `deploy/published/oct-fleet-maintenance/DEPLOY.md` / `docs/strategy/public/intro-video-production-rulings.md` |
| 2026-08-18 | **s238 — PLAN-0110 BUILT and DEPLOYED; COMPLETE 7/7, ARCHIVED.** Tab A run markers + a three-mode filter + a deploy-time demo reset. 🔴 **The gate's three proposals ALL name a `case_id`; two resolve to no row** — reading the truck off the event instead of the case table stamps nothing forever, green. ✅ Live: `CONSUMED` → `PRISTINE`, subjects landed, #1209's fix finally live, audit rows 9 → 17. 🔴 **The deploy found `DEMO-RESET.md`'s bootstrap gap** — the tool ships in the image it must run before. | `32854ab` / [#1213](https://github.com/CrayJThiemsert/vero-lite/pull/1213) / [#1214](https://github.com/CrayJThiemsert/vero-lite/pull/1214) / `docs/logs/2026-08-18-plan0110-*.md` |
| 2026-08-18 | **s237 — the video pivot: measuring the LIVE demo REFUTED beat 4.** Tab G is not on the published profile **by ruling**; the storyboard was verified on a dev profile. Cray ruled (A) shoot published; Tab H replaces three shots with ONE frame, no scrolling. 🔴 **A real fleet defect found on live** — a settled repair in the visitor's approval queue, root cause in TWO layers (the terminal step is itself gated, so one resume is not enough). PLAN-0109 + PLAN-0110 drafted, all five SDs ruled. ⚠️ **Video rulings live only in a gitignored handoff.** | `b906193` / [#1208](https://github.com/CrayJThiemsert/vero-lite/pull/1208)–[#1212](https://github.com/CrayJThiemsert/vero-lite/pull/1212) / `docs/conventions/local-first-published-parity.md` |
| 2026-08-18 | **s236 — PR-B's carve-out rehome COMPLETE (61,736 → 48,852 B, under R1's soft target) and PLAN-0107 Phase A CLOSED 6/6.** CI gained four oracles: JS syntax, asset bijection, per-vertical lifespan boot, widened mypy + two adopted hooks (**+74 s, no new dependency**). 🔴 **AC-3's own claim was MEASURED FALSE for the DEFAULT vertical** — the boot smoke misses a malformed spec on `energy`. 🔴 **Eleven inherited claims checked, EIGHT wrong.** | `de3295a` / [#1204](https://github.com/CrayJThiemsert/vero-lite/pull/1204) / `docs/plans/0107-*.md` |
| 2026-08-17 | **s235 — ADR-0038 RATIFIED (5 classes binding, 4 SDs ruled); `CLAUDE.md` BOUND with four new rules; 8 PRs (#1193–#1200).** 🔴 **The organising law:** a defect is visible only when an INSTRUMENT reads the artifact, the DATA reaches the failing state, and someone ARMED it as a gate. 🔴 **A live `main` defect fixed** (`deploy.py`'s dead compose path). ✅ §8's scenario rule is genuinely obeyed: 17 files, 0 violations. | `218a521` / [#1197](https://github.com/CrayJThiemsert/vero-lite/pull/1197) / [#1200](https://github.com/CrayJThiemsert/vero-lite/pull/1200) / `docs/adr/0038-*.md` |
| 2026-08-16 | **s234 — Step 10 EXECUTED under Cray's typed §8 go: fleet is LIVE as published system #3;** PLAN-0103 **11/11** and PLAN-0106 **7/7**, both COMPLETE, ARCHIVED. 🔴 **Cray drove the live surface and found Tab I clipping 305px of itself — a defect 4,113 green tests could not see, because CI has no JS runtime.** Fixed, guarded, REDEPLOYED under a second typed go. Pre-flight omissions, two false doc claims and every redeploy reading are in the log. | `027986e` / [#1190](https://github.com/CrayJThiemsert/vero-lite/pull/1190) / `docs/logs/2026-08-16-plan0103-step10-fleet-bring-up.md` |
| 2026-08-16 | **s233 — SEVEN PRs MERGED (#1180–#1187); AC-11's RoPA WRITTEN and ADOPTED, closing fleet's last gate.** Cray ruled **seven** times; every ruling is stamped on the RoPA itself. 🔴 **ADR-0037 OQ-3 had been RULED while its recorded Recommendation was still the OVERRULED option**, and three downstream artifacts inherited it. ⚠️ **The RoPA's authorship DEPARTS from D2.1**, disclosed on the artifact; **SD-1 is UNRULED and D2.1 as written still governs.** | `3b9a084` / [#1184](https://github.com/CrayJThiemsert/vero-lite/pull/1184) / `docs/compliance/ropa-fleet-cases.md` |
| 2026-08-15 | **s232 — ELEVEN PRs MERGED (#1170–#1179); the "fleet blocks on ONE artifact" framing was REFUTED — 14 gates walked, TWO owned by nobody.** Six typed rulings folded. ✅ **PLAN-0106 then RULED, BUILT and MERGED — D2.4 DISCHARGED** — and Cloudflare + host secrets closed. 🔴 **Fleet's gate list is now ONE item, AC-11's RoPA.** | `5425822` / [#1178](https://github.com/CrayJThiemsert/vero-lite/pull/1178) / [#1179](https://github.com/CrayJThiemsert/vero-lite/pull/1179) / `docs/plans/done/0106-*.md` / `docs/logs/2026-08-15-fleet-cloudflare-*.md` |
| 2026-08-14 | **s231 — PLAN-0105 drafted, its four SD slots RULED (Cray, typed), built and CLOSED 11/11 in one session: fleet's visitor cases, their six FK children and their upload dirs delete 90 days after `opened_at`.** 🔴 **The declared order deleted `repair_case_quote` BEFORE its composite-FK child** — `ForeignKeyViolation` on every accepted-quote case, swallowed by the fail-soft and **retried forever** with unit tests green; **AC-5 checks membership, not order**. Caught by the Step-6 scenario. | `b2fe45e` / [#1167](https://github.com/CrayJThiemsert/vero-lite/pull/1167) / `docs/plans/done/0105-*.md` |
| 2026-08-14 | **s229 — R8's PLAN-reference guard was blind to glob refs (`NNNN-*.md`, the form registries use) since s183; #1153 closes it.** The one live dead pointer had been dead since s216 and was **never reported once** — including by the commit that fixed the stream-2 row beside it. Resolves globs through the **same MOVED-not-MISSING predicate**; `Path.glob` would descend into `done/` and fail **OPEN**. | `ee968e5` (head_commit) / [#1153](https://github.com/CrayJThiemsert/vero-lite/pull/1153) / `docs/runbooks/memory-architecture.md` §R8 |

_[The oldest row (s228) rotated to `docs/status-archive/2026-h1-status.md` this reconcile, holding the table at ten.]_

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
- [ ] **PLAN-0107 — oracle-coverage hardening: `Draft`, 15 ACs. ✅ PHASE A CLOSED 6/6 s236 ([#1204](https://github.com/CrayJThiemsert/vero-lite/pull/1204)); Phases B and C remain, and NOTHING gates them.** CI now runs four oracles it lacked — `node --check`, the asset↔reference bijection, a **per-vertical** lifespan boot smoke, `mypy --strict verticals/` and the two adopted pre-commit hooks (**measured +74 s, no new dependency**). ⚠️ **Executing Phase B/C: read each AC and its `Reviewer amendment` blocks as authoritative and treat the §Steps prose as narrative — three measured divergences in Phase A alone** (a retired `≥ 20` floor, a superseded asset count, `uvx` vs `uv run --no-sync`). 🔴 **Phase B is the load-bearing prerequisite:** with today's 2-case live seed nothing overflows, so any browser stage built before it is green-and-vacuous on day one. **Read the PLAN, never a restatement:** `docs/plans/0107-oracle-coverage-hardening.md` (§Phase A closing evidence · §Acceptance Criteria).
- [ ] **🆕 PLAN-0108 — AC-authoring + pre-close convention hardening: `Draft`, UNRATIFIED.** The weak-oracle half of the same audit; its only blocker was ADR-0038, **which has landed**, so nothing gates it either. Owns ADR-0038's **OQ-5** — the staleness-guard obligation attaches to the PLAN template, not to a build task. **Read the PLAN, never a restatement:** `docs/plans/0108-ac-authoring-and-preclose-convention-hardening.md`.
- [x] **PLAN-0106 — fleet's own in-app case-persistence disclosure (ADR-0037 D2.4): COMPLETE 7/7, marked Complete by Cray (typed) and ARCHIVED s234.** AC-7's ordering clause closed on fleet's Step-10 go record, which cites this PLAN by number. **No live residual.** **Read the archived PLAN, never a restatement:** `docs/plans/done/0106-fleet-case-persistence-disclosure.md` (§Closure evidence · §Surfaced decisions).
- [ ] **TWO unruled silent drops in the NL engine's aggregate paths — REHOMED s235 to the code.** (i) the **`started_week` filter is ignored entirely** (found s228) and (ii) **`group_by` never reaches `AggregateResult`**, so *"average duration per procedure"* validates, executes and silently returns **one ungrouped number** (found s232). Both live at `_aggregate_duration` / `_aggregate_benefit`; ⚠️ **the count path DOES pass `groups`**, so (ii) is a two-site gap in an otherwise-correct design, not a missing feature. **No test covers either.** **Read the docstring, never a restatement:** `services/engine/run_query.py::_aggregate_duration`. **Same two dispositions each, NEITHER ruled: (a) refuse, or (b) make it work.**
- [x] **`deploy.py`'s dead compose path — FIXED s235 ([#1193](https://github.com/CrayJThiemsert/vero-lite/pull/1193)).** Found s232 and live on `main` for three commits; Phase 1 would have died on the next `--execute`. The path is now the module constant `_LOCAL_COMPOSE`, guarded by a test that walks the module's own path constants, so a future straggler reddens by construction. **Read the code and the guard, never a restatement:** `deploy/published/deploy.py` · `tests/deploy/test_deploy.py`. ⚠️ **That guard's first draft masked its own oracle** — homed in [`docs/lessons/0043-*.md`](lessons/0043-a-probes-red-must-name-what-broke.md), now binding via `CLAUDE.md` §8's witnessed-RED rule.
- [ ] **`nl-03`'s `SQL_EXPECT` is UNDER-SPECIFIED — RULED (Cray, typed, s226): RECORD it, do NOT change the token. REHOMED s235 to the module that defines it.** Its list holds two ids where `gold.yaml` lists three. 🔴 **A different defect class from the nl-02/nl-05 tokens Step 1 repaired:** `score_sql` matches a SUBSET, so the oracle is **WEAKER than it should be, not WRONG**. Adding the token would make the benchmark STRICTER and **break comparability with earlier runs** — a measurement decision, not a typo fix. **Read the note, never a restatement:** `benchmarks/nl_query_feasibility/text_to_sql.py` (above `SQL_EXPECT`).
- [x] **PLAN-0103 — vero-lite's side of the multi-vertical portal: COMPLETE 11/11, ARCHIVED s234;** all three published systems are live. **Read the archived PLAN and the closeout record, never a restatement:** `docs/plans/done/0103-portal-landing-and-per-system-published-profiles.md` · `docs/logs/2026-08-16-plan0103-step10-fleet-bring-up.md`. **Two live residuals outlive the PLAN and are recorded here because nothing else carries them:** (1) ⚠️ **Requester identification for the DSR path is genuinely undesigned** — `repair_case.opened_by` has no FK, so a request matches rows only by content. (2) ⚠️ **Step 9's headroom projection under-models by ~3–6× per app container** — it measures containers at boot; a fourth system must be projected against steady-state figures.
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
