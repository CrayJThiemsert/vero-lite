---
last_updated: 2026-08-06T13:44:49+07:00
session: 209
current_batch: "s209 — 1 PR: #1060 PLAN-0100 OI-1 ruled + built (on the published profile no visitor-uninitiated LLM call is made; ฿ facet kept). No AC ticked — PLAN-0100 stays 8 of 13."
current_actor: code
blocked_on: "Nothing blocks PLAN-0100 Step 8 — both blockers discharged (#1057 D4/L5; OI-1 ruled s209). Step 8 still owes an UNPINNED OCT_VERTICAL; Step 9 follows Step 8."
next_action: "PLAN-0100 Step 8 — build deploy/published/. Cray owes two reads: the per-IP cap 2→10 req/10s nod (§Pinned values) and AC-12 (still failed by #1057)."
head_commit: 0c067de
recent_commits: [0c067de, 0ffb7f9, 2ab4186, ed3fa55, c0f08b8, d4ac0c1, a8e04c3, 06e2b84, 5f07c6a, 1f97d83]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 209, 2026-08-06 (head_commit `c0f08b8` → `0c067de`) — one PR merged
> (#1060), 0 open. Theme: an LLM call the visitor never asked for was being made on
> the default landing view, and the ruling that stopped it was written as a
> principle rather than as a one-route patch.**
>
> **OI-1 RULED — Cray typed option (b), and #1060 built it.** On the `published` UI
> profile, an LLM call the visitor did not initiate is **no longer made**. The rule
> lives in a new `services/engine/llm/arm_policy.py` — the principle in its
> docstring, one predicate that decides it — and `recommender.recommend(...)` now
> takes `visitor_initiated=False` **keyword-only and fail-closed by default**, so a
> future caller that forgets the flag gets the deterministic arm rather than a
> silent fan-out. Cray's second typed call: **keep the ฿ facet under the pin** —
> `build_economic_steps` is deterministic and never raises, so pinning the *LLM arm*
> need not cost the Box-4 facet anything.
>
> **A third disclosure state, on purpose.** `_disclose_rule_by_design` is new rather
> than a reuse of `_disclose_llm_degrade`: the degrade wording would have made the
> demo announce it is **degraded** while it is in fact working exactly **as
> designed**. The new trace step `arm-pin-disclosure` deliberately reuses the
> CI-pinned `rule_check` kind, so **no UI label and no `?v=` asset cache-bust are
> owed**.
>
> **Verification.** Non-vacuity **DEMONSTRATED** — neutralising the predicate to
> `return False` drove **3 of the 5** new tests RED while both dev controls stayed
> correctly green. Gate at CI scope: `ruff check .` clean on the tracked tree,
> ruff-format clean (609 files), `mypy services/` clean (**133** files, up from
> 132), full `tests/` **3869 passed / 8 skipped / 0 failed** (baseline 3864 / 8 —
> the **+5** is exactly `tests/api/test_published_arm_pin.py`, skip count unchanged).
>
> **No AC was ticked — PLAN-0100 stays 8 of 13.** The ruling *unblocks*; it does not
> close AC-4/5/6. Same PR reconciled the PLAN (OI-1 RULED, the allow-table posture,
> Step 8's now-stale BLOCK released, an AC-12 note, Step 9 Case 4). **Step 8 is now
> fully unblocked** — both blockers discharged (D4/L5 ratified in #1057 on
> 2026-08-05; OI-1 ruled today). **Cray owes one call, not two:** the **per-IP rate
> cap 2 → 10 req/10s** nod (the PLAN's §Pinned values row still reads "needs Cray's
> nod"), plus a read on **AC-12**, whose "this PLAN's diff touches no file under
> `docs/adr/`" clause is still failed by #1057 (#1060 touches no `docs/adr/` file,
> so it does not worsen it). Cray's third typed call was **"merge only, then
> stop"** — Step 8 is deliberately deferred to s210.

> **Session 208, 2026-08-06 (head_commit `5621266` → `c0f08b8`) — three PRs merged
> (#1056–#1058), 0 open. Theme: a fail-soft handler was holding the DB-less boot
> guarantee for the wrong reason, and an AC table read 4 of 13 while its own handoff
> claimed 10.**
>
> **#1056 — every non-procurement boot was raising `UnboundLocalError`, and the test
> suite passed anyway.** `async_session` was imported inside a nested branch of
> `lifespan` but used by the separate `if "fleet_maintenance" in known:` block below,
> so Python bound the name **function-local**: any boot not taking the
> procurement-seed branch — **including the plain `energy` default** — raised at
> **both** call sites. `tests/test_startup_log.py` had been exercising the broken
> path all along and **passing**, because the fail-soft handler absorbed it. So the
> DB-less boot guarantee **was holding for the wrong reason**: a handler swallowing
> a *code bug* rather than an *environment absence*. The fix leaves a deliberate
> open seam — `_is_environment_absent(exc)` is a documented `return True` stub that
> **Cray chose to author personally**; it is behaviour-neutral today and nothing
> else in the repo tracks it.
>
> **#1057 — ADR-0035 D4/L5 amended; PLAN-0100 Step 8's ADR blocker is CLEARED.**
> **Cray's typed ruling, 2026-08-06: reading (a)** — vero-lite's `cloudflared` **is**
> this system's connector in its own compose project; the portal repo owns the
> ingress map *across systems*; each system owns its *own* route allowlist. Reading
> (b) was **rejected** (it voids AC-6(a) and re-opens SD-3). The amendment is framed
> as the ADR **reconciled with itself**: Implementation Note 1 gave connector + map
> to the portal while Note 2 already gave the route allowlist to vero-lite. Two
> drafter-surfaced decisions were **also typed by Cray**: **SD-1** restate D4's
> acceptance shape to count *each system's own* connector (otherwise the ADR's own
> drift trigger fires on the arrangement just ruled), **SD-2** keep the binding
> corollary that **no other system's connector may join this system's network**. The
> same PR renumbered **81 line numbers across 45 PLAN-0100 citations** with a
> self-verifying script (old line content must be byte-identical to new, or abort) —
> **no guard test validates ADR line citations**, so that drift would have rotted
> silently.
>
> **#1058 — PLAN-0100 AC-7/8/9/10 CLOSED: 4 of 13 → 8 of 13, and two of the four came
> back NOT-CLOSEABLE.** The work had shipped in s206 (Steps 5/6/7/10) and the AC
> table was simply never ticked — the s207 handoff claimed "10 of 13 closed" while
> the checkboxes read **4**. Every AC was verified clause-by-clause by independent
> **refuting** reviewers. **AC-7:** two clauses were **unassertable as written** and
> were amended on Cray's typed ruling ("< 5 s" on one coroutine whose completion
> order the event loop does not promise; "the first" is not identifiable), and a
> third was **genuinely unmet and built** — no prompt-log assertion existed anywhere
> under the cap; non-vacuity was shown by mutating the router to log a hardcoded
> `arm="llm"`, which reddened **only** the new assertion. **AC-8** closed **with
> Postgres up on purpose** — its `/insights/query` half is the sole coverage and
> silently **skips** otherwise. **AC-9's** required ADR-0032 D5 wording review **had
> never been performed**: done, **PASS**, and its tripwire hardened (pinning
> `"Cloudflare"` survived a reword that deletes the actual D6 duty). **AC-10** fixed
> a purge command reading `prompts-*.jsonl` against a writer emitting `prompt-` — it
> matched **zero** files and **exited 0**.
>
> **OI-1 got worse, not clearer.** The LLM fan-out fires on **Tab A, the default
> landing view** — not first on Tab B as previously recorded — so the exposure sits
> on the page every visitor lands on; and option **(a)** collides with a **closed**
> prompt-log row schema whose `text` is defined as *the visitor's typed input*,
> which `/recommendations` has none of. Cray owes two calls: **OI-1** (three options
> in the PLAN's §Open items; **(c) conflicts with D6**) and the **per-IP rate cap
> 2 → 10 req/10s** nod. Step 8 also still owes an **unpinned `OCT_VERTICAL`**;
> Step 9 follows Step 8.

> **Session 207, 2026-08-05 (head_commit `296cc34` → `5621266`) — one PR merged
> (#1049), 0 open. Theme: a ratified plan's own recommendation and its own allow
> table had never been checked against each other, and an unreviewed fold-in got
> two of its own claims wrong.**
>
> _[The s206 tail also merged **#1046** (Step 10 — RoPA + the published-demo
> runbook), **#1047** (`0c9348a` — the s206 STATUS reconcile itself, which is why
> the s206 block below stops where it does) and **#1048** (lessons
> **0036**/**0037**); the s206 block below predates all three.]_
>
> **Step 4 COMPLETE, AC-3 CLOSED:** the published profile measured green at all
> five pinned widths — **0 overflow, 0 clipped** — under SD-4's option (a),
> *before* Step 3's removals, i.e. at maximum header width demand. A 600 px
> **non-vacuity probe** drove the instrument red first. ⚠️ The initial probe's
> `querySelector('header')` returned **null** (the element is `class="header"`),
> scanning **zero** nodes and reporting a clean "0 clipped" — the table now carries
> a **nodes-scanned column** so a void row cannot pass as a clean one.
>
> **Cray ruled all five SDs (typed 2026-08-05); AC-13 is CLOSED and every
> BLOCKED-ON-SD marker is RELEASED.** SD-1 = (a) DB-less · SD-2 = exclude all
> three draft routes · SD-4 = (a) measure-to-confirm · SD-5 = keep both. **SD-3
> was restated before it was ruled: ADR-0035 never names nginx** — it says only
> "at vero-lite's edge" and that "rate limiting lives at the edge", which forbids
> rate limiting *inside* `services/` rather than mandating a proxy. Cray ruled
> **(ii): stay with `cloudflared`** (ingress allowlist + catch-all 404, config
> committed) plus the zone's Cloudflare rate-limiting rule — **no nginx service**.
>
> **Finding C-3 — four allow-table rows the ruled DB-less posture cannot serve.**
> Tracing every allow-table handler for a DB session dependency found
> `/recommendations/{id}/execute`, `/runs/{id}`, `/runs/{id}/gate/resolve` and
> `/insights/query`, and there is **no global exception handler anywhere in
> `services/api/`** — so each returns an unhandled **500, not a degrade**.
> Sharpest: the allow table called `execute` the "operator-driven demo beat", so
> **Approve would succeed and Execute would 500** — the Tab B loop dying at its
> last step. The runs pair also fails a second, DB-independent way: justified as
> "Tab G beat 3", but that panel mounts only in event mode (`view-hero.js:641`)
> and event mode is excluded — **zero callers**. This is **C-1 mirrored**: C-1
> was a route *missing* that made a feature undrivable; C-3 is routes *present*
> whose reachability path is excluded. Method note: the drafting census walked
> *UI call sites → routes*; C-3 needed *routes → handler DB dependency*, and
> **neither walk finds the other's defect**.
>
> **An R2 pass with three independent adversarial reviewers discharged the
> author≠reviewer separation the fold-in owed — and it paid for itself.** C-3
> survived **5/5**. But SD-3's ruling drew **six findings**, three of which the
> spec cannot remove: a **blocking D4/L5 ADR debt** (the ADR assigns the connector
> + ingress map to the portal repo, so `0035:421-424`'s drift trigger fires), a
> vendor-branded 429 on Free, and NAT-shared-IP with no burst. And **Step 9's
> pass/fail read scored 4/5 against a completely dead app** — its "non-404" bar
> let a crashed container pass four cases at once — so it was rewritten as **v2**.
>
> **Two of the PLAN's own claims were retracted.** `GET /recommendations` was
> pinned `deterministic` but is **LLM-backed** (`recommender.py:194-195`), so the
> recorded consequence "`/query` is the only published LLM route" was **false**;
> it is tracked now as **OI-1** — the route is neither rate-capped nor
> prompt-logged, and each failure pages Cray via `notify_llm_unreachable`. And
> ~14 `api.js` citations were stale by exactly **+7**: the fold-in corrected three
> instances without recognising the shift was **systematic**.

> **Session 206, 2026-08-05 (head_commit `bcab1f4` → `296cc34`) — six PRs merged
> (#1040–#1045), one open for Cray (#1046). Theme: every defect found this session
> was one that leaves the system LOOKING correct.**
>
> **PLAN-0102 was one ratification away from bricking the harness (#1040).** An R2
> pass found three scope gaps. The sharp one: the acknowledged-pause (`awaiting_ack`)
> subsystem was **entirely unscoped** while Step 5 removed one of its two
> dependencies — `stop_continuation.py:73` would still import a deleted function at
> module load, an `ImportError` **no `try/except` catches**, taking the chain-cap
> fail-safe, the classifier and auto-handoff down with it. Steps 3 and 5 also
> contradicted each other over `_apply_commit_reset`, whose `AttributeError` is
> **swallowed** by the observer's blanket handler — L2/L3/L4 would stop persisting
> while the hook still exits 0. **One root cause for all three: none of the missed
> identifiers carries an `L1` or `loop` token in its name**, so the name-keyed census
> could not see them. New **AC-11** carries two prongs that go RED on exactly these,
> because ACs 1–10 would all have passed over a bricked harness.
>
> **PLAN-0100's "blocked" slice was half unblocked — and all of it shipped.** STATUS
> read *execution gated on SD-1..SD-5*; the PLAN's own text gates only steps marked
> BLOCKED-ON-SD. **Six SD-free items shipped**: the Step-1 census (#1043), `ui_profile`
> + its two delivery seams (#1042), the in-flight cap + prompt log (#1044), the D6
> banner (#1045). **Cray chose server-injection for the boot seam; the carrier had to
> change from `<script>` to `<meta>`** — `_OCT_CSP` pins `script-src 'self'`, so an
> inline script is silently blocked and the profile would fall back to the FULL
> console. Every property the decision was made for survives.
>
> **The census found the published demo unloginable (#1043).** `/whoami` was in
> **neither** allowlist table, so it fell to default-deny — but `auth.js:39` probes it
> to provision the operator key, so approve/execute and gate-resolve would have been
> undrivable *while sitting on the allow table as keyed routes*. The PLAN's own
> keyed-routes paragraph rested on a route the same section denied. Generalises: **an
> allowlist complete for the routes a feature CALLS can be incomplete for the routes
> that make it REACHABLE.**
>
> **The unowned wall-clock intermittent is closed (#1041)** — and the reported framing
> was wrong in a useful way: not two clocks, but **one clock sampled twice** on a
> non-monotonic host. Bracket → equality against a frozen `Clock`; a planted
> **1-second** defect reddens both tests, which the old bracket could not catch at all.
>
> **Two silent failures the gates caught, not review:** `uvicorn.Config` applies a
> **global** logging `dictConfig` (`propagate=False` on `uvicorn.error`), so a test
> stub broke a `caplog` assertion three files away while the line it wanted still
> reached stderr — only the full-suite run saw it. And a CSS custom property that does
> not exist **fails silently**, so the D6 banner's first draft would have rendered in
> an inherited colour with nothing to redden.
>
> Gate at CI scope on every merge, including each merge commit (CI is PR-only and
> never tests those): suite **3826 → 3847**, ruff + `mypy --strict` clean throughout.

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
| 2026-08-06 | **s209 — PLAN-0100 OI-1 RULED (Cray, typed): option (b), as a PRINCIPLE not a one-route patch (#1060).** On the `published` profile an LLM call the visitor did not initiate is **no longer made** — `arm_policy.py` (the principle + one predicate); `recommend(..., visitor_initiated=False)` is **keyword-only, fail-closed**. **฿ facet kept** (`build_economic_steps` is deterministic, never raises). New `_disclose_rule_by_design` — a **third** state, because the degrade wording would claim degraded while working as designed; trace step `arm-pin-disclosure` reuses the CI-pinned `rule_check` kind ⇒ **no UI label, no `?v=` bump**. Non-vacuity 3 of 5 RED. **No AC ticked — still 8 of 13**; Step 8 now fully unblocked | `0c067de` (head_commit) / [#1060](https://github.com/CrayJThiemsert/vero-lite/pull/1060) / `services/engine/llm/arm_policy.py` |
| 2026-08-06 | **s208 — PLAN-0100 AC-7/8/9/10 CLOSED (#1058): 4 of 13 → 8 of 13.** The work shipped in s206; the table was never ticked (the s207 handoff said "10 of 13", the checkboxes read **4**). Independent refuting review returned **two of four NOT-CLOSEABLE**: AC-7 had two **unassertable** clauses (**amended on Cray's typed ruling**) plus a third genuinely unmet and now built — a prompt-log assertion under the cap, non-vacuity proven by a hardcoded `arm="llm"` mutation; **AC-9's ADR-0032 D5 wording review had never been run** (done, PASS). AC-10 fixed a purge glob (`prompts-*` vs `prompt-`) matching **0** files at **exit 0** | `c0f08b8` (head_commit) / [#1058](https://github.com/CrayJThiemsert/vero-lite/pull/1058) / `docs/plans/0100-exposure-published-demo-surface.md` |
| 2026-08-06 | **s208 — ADR-0035 D4/L5 AMENDED (#1057): PLAN-0100 Step 8's ADR blocker is CLEARED.** **Cray typed reading (a)** — vero-lite's `cloudflared` **is** this system's connector in its own compose project; the portal owns the ingress map *across* systems; each system owns its *own* route allowlist. (b) rejected: voids AC-6(a), re-opens SD-3. Two drafter SDs also typed: **SD-1** restate D4's acceptance to count each system's own connector; **SD-2** keep "no other system's connector may join this system's network". Same PR renumbered **81 line numbers / 45 citations** — no guard test covers ADR line cites | `a8e04c3` ([#1057](https://github.com/CrayJThiemsert/vero-lite/pull/1057)) / `docs/adr/0035-hosting-and-exposure-model.md` |
| 2026-08-06 | **s208 — the DB-less boot guarantee was holding for the WRONG REASON (#1056).** `async_session` imported inside a nested `lifespan` branch but used by the `if "fleet_maintenance" in known:` block below ⇒ Python bound it **function-local** ⇒ **every** boot not taking the procurement-seed branch (**including plain `energy`**) raised `UnboundLocalError` at both call sites. `tests/test_startup_log.py` exercised the broken path and **passed** — the fail-soft handler absorbed a *code bug* as if it were an *environment absence*. Deliberate open seam: `_is_environment_absent(exc)` is a documented `return True` stub **Cray chose to author personally** | `5f07c6a` ([#1056](https://github.com/CrayJThiemsert/vero-lite/pull/1056)) / `services/api/main.py` |
| 2026-08-05 | **s207 — Cray ruled all five PLAN-0100 SDs (#1049): AC-13 CLOSED, every BLOCKED-ON-SD marker RELEASED.** SD-1 (a) DB-less · SD-2 exclude the three draft routes · **SD-3 (ii) `cloudflared` — ADR-0035 never names nginx** · SD-4 (a) · SD-5 keep both. ⚠️ The R2 pass found **C-3: four allowed routes need a DB and there is NO global exception handler ⇒ unhandled 500, not degrade** — Approve succeeds, **Execute 500s**. Two of the PLAN's own claims retracted: `GET /recommendations` is **LLM-backed** (⇒ **OI-1**); ~14 `api.js` cites stale by **+7**. **Steps 3/4 free; Step 8 gated on a D4/L5 ADR-0035 amendment** | `5621266` (head_commit) / [#1049](https://github.com/CrayJThiemsert/vero-lite/pull/1049) / `docs/plans/0100-exposure-published-demo-surface.md` |
| 2026-08-05 | **s206 tail — PLAN-0100 Step 10 shipped and two lessons landed (#1046, #1048).** #1046 creates `docs/compliance/` (the RoPA instance, written in Cray's voice as controller) + `docs/runbooks/published-demo-operations.md`. #1048 adds lessons **0036** (the tiebreak pairing) and **0037** (the three-axis blind spot). **#1047** also merged in this window and is **not characterised in this record**. All three landed after STATUS was last written, so the s206 row below does not carry them | `d865b75` ([#1046](https://github.com/CrayJThiemsert/vero-lite/pull/1046)) / `b045adf` ([#1048](https://github.com/CrayJThiemsert/vero-lite/pull/1048)) / `docs/runbooks/published-demo-operations.md` |
| 2026-08-05 | **s206 — PLAN-0102's scope was three gaps short of safe, and one would have BRICKED the harness (#1040).** The `awaiting_ack` subsystem was entirely unscoped while Step 5 deleted one of its dependencies ⇒ `ImportError` at module load that **no `try/except` catches**, taking chain-cap + classifier + auto-handoff with it; Steps 3/5 contradicted each other over `_apply_commit_reset`, whose `AttributeError` is **swallowed** ⇒ L2/L3/L4 stop persisting at exit 0. Root cause for all three: **none of the missed identifiers carries an `L1`/`loop` token**, so a name-keyed census cannot see them. **AC-11** added — ACs 1–10 would have passed over a bricked harness. Separately **#1041** closed the unowned wall-clock intermittent: **one clock sampled twice**, not two clocks; a planted 1-second defect now reddens where the old bracket could not | `e5d163d` ([#1040](https://github.com/CrayJThiemsert/vero-lite/pull/1040)) / `3b9d9c4` ([#1041](https://github.com/CrayJThiemsert/vero-lite/pull/1041)) / `docs/plans/0102-retire-l1-loop-detect.md` |
| 2026-08-05 | **s206 — PLAN-0100's SD-free slice SHIPPED ENTIRE (#1042–#1045); "execution gated on SD-1..SD-5" was shorthand, not the PLAN's rule.** Step 1 census, Step 2 `ui_profile`, Steps 6–7 in-flight cap + prompt log, Step 5 D6 banner — all six SD-free items, none gated. **Cray chose server-injection for the boot seam; the carrier changed `<script>` → `<meta>`** because `_OCT_CSP` pins `script-src 'self'` and an inline script is **silently blocked** ⇒ fallback to the FULL console. ⚠️ The census found **`/whoami` default-denied**, which makes the published demo **unloginable** — the PLAN's keyed-routes argument rested on a route the same section denied. **Only SD-gated steps 3/4/8/9 remain** | `296cc34` (head_commit) / [#1042](https://github.com/CrayJThiemsert/vero-lite/pull/1042) / [#1043](https://github.com/CrayJThiemsert/vero-lite/pull/1043) / [#1044](https://github.com/CrayJThiemsert/vero-lite/pull/1044) / [#1045](https://github.com/CrayJThiemsert/vero-lite/pull/1045) / `docs/plans/0100-exposure-published-demo-surface.md` |
| 2026-08-04 | **#1034 (chip-authored, NOT s205) — `/api/cases` list order is now REPEATABLE, not newest-first.** A `case_id` tiebreak on `opened_at.desc()` ends cross-refresh flicker at the `limit` boundary, but `case_id` is a **random UUID**: it buys **repeatability, NOT newest-first correctness — 50.5 % over 20,000 reps**. True order needs a monotonic `seq`, which PLAN-0099 §Coverage had already weighed here and **KNOWINGLY LEFT (ledger #7)**; **Cray ratified keeping that** — same `uuid4`-tiebreak trap as #1035, opposite right answers (display list ⇒ leave it, correctness path ⇒ `seq`) | `bcab1f4` ([#1034](https://github.com/CrayJThiemsert/vero-lite/pull/1034)) / `services/api/routers/cases.py:272` / `docs/plans/done/0099-wall-clock-root-fix-store-at-write-and-sequence.md` |
| 2026-08-04 | **#1035 (parallel session, NOT s205) — task-chain state re-keyed onto a DB-assigned monotonic `seq`; alembic head is now `0025`.** `chain_state` sorted flips on `at`, a wall-clock stamp, so a backward clock step let the **superseded** flip win; the `event_id` tiebreak never fired because `at` led the sort (and it is a `uuid4` anyway). It feeds `stale_items` → the LINE nudge sweep, so **both directions were live failures**: a finished step nudged forever, a reopened one silently un-chased. PLAN-0099 D2; `(tenant_id, seq)` unique per PLAN-0101 SD-3 | `3b07c16` ([#1035](https://github.com/CrayJThiemsert/vero-lite/pull/1035)) / `verticals/fleet_maintenance/task_chain.py` + `services/api/routers/cases.py:305` / alembic `0025` |

## In-Flight Discussions

- **PLAN-0096 — COMPLETE 12/12 and ARCHIVED (s193); FOUR RESIDUAL RISKS OUTLIVE IT** (which is why this entry is a pointer and not a deletion): **RR-1** (per-baht approver→case attribution is INFERENCE, not data — silently wrong the day two approvers share a gate resolution), **RR-3** (concurrency-race coverage — both named gaps CLOSED s195 by #995), **ศูนย์ต้นทุน ships EMPTY** (partner granularity unanswered — also an open Active TODO below), and **`latest_per`** still collapsing two open cases on one truck (**Cray typed (ค) defer** — the older case reports as *ungoverned*, indistinguishable from a governance failure). Read the archived PLAN, not a restatement: `docs/plans/done/0096-fleet-flow-completion-phase1.md` (§Verification preamble + §Acceptance Criteria for RR-1 / RR-3 / ศูนย์ต้นทุน; §Step 8 for `latest_per`).
- **COMPLETE-and-ARCHIVED, no live remainder here — read the archived PLAN, never a restatement:** **PLAN-0095** (Docker image boot, s177 — its OQ-1 hosting model CLOSED by ADR-0035) · **PLAN-0094** (L1 loop-detect restructure, s183 — its OQ-4 is ANSWERED; see the PLAN-0102 row in Active TODOs) · **PLAN-0093** (LLM-arm degrade disclosure, s172 — **no follow-on owed**) · **PLAN-0091** (narrative→vertical scaffolder, s168 — two named follow-ons, **neither scheduled**, both greenfield/human-call) · **PLAN-0088** (cross-run read substrate + the four run-insight readers, s171 — **three AC-WORDING debts, none a code defect**) · **PLAN-0036 + PLAN-0037** (Fastenal procurement vertical Stage 1 + the Stage-2 facet retrofit, s76 — `Status: Done`; demo target = Fastenal Thailand, **pitch = asset-ontology-triggered governed sourcing**, NOT the commoditized "governed"/"cross-vertical" claims). Each record is in `docs/plans/done/`; the s168→s193 retrospectives these bullets used to carry are rotated to `docs/status-archive/`.
- **ADR-012 guarded trial (Cowork second free-form tier):** Accepted 2026-05-22 (`7916b39`) as a guarded trial — Cowork gains Tier-1b (repo-grounded free-form / thinking-partner / informal code review) alongside Chat (repo-blind blue-sky). Regression triggers R-FF1..R-FF4 are the exit criteria; under observation across the next sessions.
- **ADR-0020 partner-sim guarded trial (synthetic design-partner simulation venue):** Accepted 2026-06-13; verdict **continue-with-adjustments**. Runs 1 (energy, s93) + 2 (supply-chain, s94) both COMPLETE, all S-checks PASS against pre-committed oracles, no R-PS trigger fired; C-1..C-3 CONFIRMED → **no open partner-sim debt**. ADR-011's audit stays gated on a REAL partner conversation (R3: SYNTHETIC provenance INFORMS but never TRIGGERS it). Full record: `docs/adr/0020-*.md` + the gitignored run packages under `docs/research/private/`.
- **Partner-trial-readiness gaps:** `docs/research/private/2026-05-22-partner-trial-readiness-gaps.md` — Cowork's engine→design-partner-trial gap analysis (gap groups A–E; recommended T0–T4 sequence). Informational; awaits a dedicated Cray roadmap discussion. Key fork: NL-query-first ("wow demo on synthetic") vs real-data-first ("show me MY data").
- **PLAN-002 (Database setup):** Custom Postgres image with pgvector + Apache AGE + pg_trgm — **not yet drafted**, and it needs a fresh ADR number. _[The old "≥ ADR-014" floor recorded here was **moot** — see the Active TODO below, corrected s141: ADRs now run past 0032 and `0014-WITHDRAWN.md` exists. Kept as one pointer rather than two divergent copies.]_
- **Hook portability across environments:** Lesson #3 A3 documents the workaround; durable fix deferred (would require hook regeneration policy).
- **The autonomy fork — Stop-hook misfires: CLOSED s167.** Resolved by **option A′** (Cray, typed) and shipped the same session — the `dispatch` verdict is a **suggestion, not an order** (#870/#871). Final ledger: **14 misfires / 0 valid fires**. **The whole argument is settled history in `docs/plans/done/0092-stop-hook-dispatch-arm-demotion-to-suggestion.md` — do not restate it here.** Live remainder: only **option (e)** (flip the classifier backend from local Ollama `gpt-oss:20b` to Sonnet), **deferred**, its API-key/org fail-closed probe unrun.

## Active TODOs

- [ ] **PLAN-0100 — the ADR-0035 exposure PLAN. DRAFTED s202 (#1017): `Status: Draft`, 12 ACs, 6 phases. EXECUTION IS GATED on Cray ruling SD-1..SD-5.** **SD-1 is load-bearing** — the published deployment's DB posture, (a) DB-less vs (b) synthetic Postgres — because it decides which tabs the published profile registers and every allowlist row hangs off it. Per **Cray's s202 ruling** the PLAN absorbs the UI work D5(2) implies, and it carries the **published-profile half of the nav-bar work as AC-3**. _[s203: Phase 0 Step 1 has **no `Ruling:` slot** — PLAN-0101 carries one under every SD from the start — so Phase 0 must *author* the adjudication record rather than fill it; and its AC-3 measurement table currently lives only in a commit body.]_ _[s204: **SD-4's published half is not answerable as written** — it turns on a published `UI_PROFILE` that exists **only inside this PLAN** (0 occurrences anywhere else in the repo), so the profile must be built, or SD-4 re-scoped, before a ruling on it can mean anything. Fold this in with the s203 findings before the SD round goes to Cray.]_ _[s205: **the fold-in SHIPPED (#1032) and the s203/s204 findings above are DISCHARGED** — the PLAN now carries five empty `Ruling:` slots, **AC-13** (the adjudication record), BLOCKED-ON-SD markers, and `54dfc7d`'s measurement table verbatim; **Tab H was dropped from SD-1's promise** (mixed backend, not DB-posture-contingent). All that remains is Cray filling the five slots.]_ _[s206: **the row's own headline "EXECUTION IS GATED on Cray ruling SD-1..SD-5" was shorthand, and reading it literally cost a session's worth of unblocked work** — the PLAN gates only steps carrying a BLOCKED-ON-SD marker, and **six items carried none**. All six now SHIPPED (#1042–#1045): Step 1's census, Step 2's `ui_profile` + its two delivery seams, Steps 6–7's in-flight cap + prompt log, Step 5's D6 banner, Step 10's RoPA + runbook (**#1046 open — Cray asked to read it before merge**). **What is genuinely gated: Steps 3, 4, 8, 9 only**, and the gate is **all-or-nothing** — ruling one SD unblocks nothing, so the five want one sitting. ⚠️ Two calls surfaced by the build and left for Cray inside merged PRs: **`llm_max_inflight`'s dev default** (shipped **0**/uncapped, read as a published posture like `PROMPT_LOG_ENABLED`; if 1-everywhere was meant it is one line) and **whether published Tab A should render run markers** (`GET /runs` is default-denied, Tab A degrades to zero flags by design — deliberately NOT raised as a sixth SD, since the safe default already ships and a sixth slot would block five ruled steps on a cosmetic one).]_ _[s207: **ALL FIVE SDs RULED (Cray, typed 2026-08-05) — AC-13 CLOSED, every BLOCKED-ON-SD marker RELEASED, and #1046 merged**, so this row's "EXECUTION IS GATED" headline and its `#1046 open` note are both history. SD-1 (a) DB-less · SD-2 exclude the three draft routes · SD-3 (ii) `cloudflared`, **no nginx** · SD-4 (a) · SD-5 keep both. **Steps 3 and 4 are free.** What is gated NOW: **Step 8 on a D4/L5 ADR-0035 amendment** (the ADR assigns the connector + ingress map to the portal repo), Step 9 on Step 8, and Step 9's arm-posture case on **OI-1** (`GET /recommendations` is LLM-backed, neither rate-capped nor prompt-logged). Also live: finding **C-3** — four allowed routes need a DB the ruled posture does not provide, and there is no global exception handler, so they 500. Detail is in the PLAN (#1049).]_ _[s208: **the D4/L5 ADR-0035 amendment SHIPPED (#1057, Cray typed reading (a)) — Step 8's ADR blocker is CLEARED**, and **AC-7/8/9/10 CLOSED (#1058): 4 of 13 → 8 of 13** (the s207 handoff's "10 of 13" was never true of the checkboxes; two of the four came back NOT-CLOSEABLE on first read). What Step 8 still owes: an **unpinned `OCT_VERTICAL`** and its own self-declared dependency on **OI-1**; Step 9 follows Step 8. Cray owes **OI-1** (the LLM fan-out fires on **Tab A, the default landing view**; option (a) collides with the closed prompt-log row schema, (c) conflicts with D6) and the **per-IP cap 2→10 req/10s** nod.]_ _[s209: **OI-1 is RULED and BUILT (#1060) — Cray typed option (b), written as a PRINCIPLE, not a one-route patch**, so "Cray owes two" above is history. On the `published` profile an LLM call the visitor did not initiate is no longer made (`services/engine/llm/arm_policy.py`; `recommend(..., visitor_initiated=False)` keyword-only + fail-closed), the **฿ facet is kept** under the pin (`build_economic_steps` is deterministic and never raises), and disclosure goes through a **third** state `_disclose_rule_by_design` rather than the degrade wording. **Step 8 is now FULLY unblocked** — both blockers discharged (#1057 D4/L5 on 2026-08-05, OI-1 today) — but **no AC was ticked: PLAN-0100 remains 8 of 13**, and Step 8's **unpinned `OCT_VERTICAL`** is still owed. Cray's remaining two reads: the **per-IP cap 2→10 req/10s** nod (§Pinned values still reads "needs Cray's nod") and **AC-12**, still failed by #1057 (#1060 touches no `docs/adr/` file, so it does not worsen it). Cray typed **"merge only, then stop"** — Step 8 deferred to s210.]_ `docs/plans/0100-exposure-published-demo-surface.md`.
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
- [ ] **PLAN-0102 — retire L1 loop-detect. OQ-4 ANSWERED s205 (NO; Cray typed RETIRE, 2026-08-04); the PLAN is DRAFTED and UNARCHIVED, so this row tracks execution only.** The measurement, the s180 "0 denies" correction (**≥ 56**, a floor), and the ADR-013-never-backed-L1 finding are all recorded elsewhere — read them, not a restatement: `docs/plans/0102-retire-l1-loop-detect.md` §Context + [`docs/lessons/0035-negative-measurement-needs-a-positive-control.md`](docs/lessons/0035-negative-measurement-needs-a-positive-control.md).
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
