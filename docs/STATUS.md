---
last_updated: 2026-08-09T21:30:00+07:00
session: 218
current_batch: "s218 — six PRs (#1099-#1104), 0 open. ADR-0036 RATIFIED; PLAN-0103 drafted, amended and ALL EIGHT slots ruled by Cray; ADR-0037 spawned Proposed by the SD-1 ruling, which overruled both the drafter and Code."
current_actor: code
blocked_on: "Nothing is BLOCKED and nothing is owed by Cray except ADR-0037's ratification, which gates ONLY fleet's half of PLAN-0103. Procurement's entire half plus Steps 2-3, energy's move, Step 8's content and Step 9's measurement all proceed while ADR-0037 is in flight — see PLAN-0103 Step 4's gate map, written so a bare 'ADR-gated' label does not stall work that carries no gate."
next_action: "Two independent tracks, neither waiting on the other. (1) Cray ratifies ADR-0037 (Proposed) — it carries its own Cray slots (D1 grant criterion, D3 bound-don't-amend, D4 the audit-chain erasure answer, which is ruled AFTER D2.7 measures whether visitor text reaches the chain). Ratifying unblocks fleet's DB half. (2) Code executes PLAN-0103's UNGATED work now: Step 2 (kill PUBLISHED_EXCLUDED_VIEWS for a server-declared per-system view set, walking all 11 isPublished() consumers), Step 3's branch audit, then procurement's profile + allowlist (Steps 4-5, DB-less so ungated) — procurement is first in bring-up order per SD-2(b). Still ungated elsewhere: BUILD D-4 option (a) (four seams in nl_query.py, nothing built); the public one-pager; versioned font URLs + pin OLLAMA_KEEP_ALIVE. Edge cache-purge needs a Cloudflare API token = new secret + host-state; MS-S1 headroom is PLAN-0103 Step 9 and is UNMEASURED."
head_commit: 368b813
recent_commits: [368b813, 3d194c4, 9160f4f, 866e09f, 52832bc, a2e2d0e, 289a003, 03c3d45, e5e4f09, 84ac98c]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 218, 2026-08-09→10 (head_commit `36e5735` → `9160f4f`) — six PRs
> merged (#1099–#1104), 0 open. Theme: ADR-0036 ratified, its follow-on PLAN
> drafted, amended and fully ruled, and a second ADR spawned — the whole
> ratify→plan→rule cycle inside one session.**
>
> **What Cray ratified (typed, in-context).** ADR-0036 as drafted: **D1** scope
> ruling (a) — this enters vero-lite as an ADR extending ADR-0035 L9/D4, portal-repo
> files stay out; **D2** *a deployed vertical instance IS a system*, with the
> `oct-<vertical-id>` subdomain-label convention (`_`→`-`), labels only, no apex
> domain anywhere in this repo; **D5** vero-lite owns every vertical-system's
> {allowlist + env} profile, N near-identical allowlists accepted at N ≤ 3 under the
> Rule of Three with per-instance guards as the mitigation; **OQ-1** adopted —
> retire the bare `oct.` label rather than keep it as an alias. LOCKED-1/2/3 were
> already typed 2026-08-06 and were not re-asked. ADR-0035 D1–D4 untouched
> (LOCKED-4): D2's drift check shows system N+1 still costs the portal exactly the
> two artifacts the restated acceptance shape allows, so the **D4 reopening trigger
> does not fire**.
>
> **The two edits are one commit by construction.** ADR-0036 sat in
> `test_the_non_accepted_adrs_are_exactly_the_expected_set` because it was IN
> FLIGHT, not because it was exempt. Flipping without removing the entry reddens
> that assertion; removing without flipping reddens it from the other side. Edit
> **order** also matters and was observed — the test edit landed **first**, because
> flipping `Status` puts the ADR behind the G1 gate and blocks every later edit to
> it (sessions 67 / 110 / 126). The docstring is rewritten to state that as a
> general rule with this ratification as its worked precedent.
>
> **Verified behaviourally, not just green:** `gate.evaluate(ADR-0036)` → **DENY**
> (was allow), beside two live controls — `0014-WITHDRAWN` → allow, `0035` → DENY.
> Without them the DENY is equally consistent with "the gate denies everything".
>
> **Then the whole cycle ran to the end in one session.** PLAN-0103 drafted,
> amended, and **all eight slots RULED by Cray** (#1101/#1103/#1104). 🔴 **SD-1
> overruled both the drafter and Code's R2 concurrence** — both read ADR-0036 D5's
> "PLAN's to finalize" grant as sufficient; Cray ruled a new ADR is required, and
> was right: a DB on a public system changes what personal data it holds and what
> erasure can be promised — legal consequence, outliving the PLAN, needing
> attribution. **Two reviewers agreeing was not independent evidence**; both had
> priced the cost of *having* an ADR and neither the cost of *not*. **ADR-0037**
> (`Proposed`) is the result and the home for two previously-unrecorded findings
> (D6's scope, the audit-chain erasure boundary). All of it — the rulings, the
> eleven-consumer census, the second-assisted-system premise change, the gate map
> — is in the artifacts; read those, not a restatement:
> `docs/adr/0037-*.md` and `docs/plans/0103-*.md` §Surfaced decisions.
>
> **The suite caught the new ADR the same day the rule was written.** Adding
> ADR-0037 `Proposed` reddened `test_the_non_accepted_adrs_are_exactly_the_expected_set`
> — the same test edited that morning, whose rewritten docstring already
> prescribed the fix ("the entry and its Status line move together, in both
> directions"). Morning exercised removal; evening, addition. It caught it only
> because it enumerates `docs/adr/` on disk rather than a hardcoded census.

> **Session 217, 2026-08-08 (head_commit `f987888` → `36e5735`) — two PRs merged
> (#1095, #1096), 0 open. Theme: PLAN-0102 is COMPLETE 11/11 and ARCHIVED — the
> L1 loop-detect guard is RETIRED, and executing the PLAN found three defects in
> the PLAN itself that share one root cause.**
>
> **Why L1 went.** It keyed on the same **file**; ADR-013 E.4 ratified "the same
> **problem**", which is what L2/L3/L4 key on — so the retirement narrows the
> implementation *toward* the Accepted ADR. Across L1's entire live history:
> **zero true positives**, against **≥ 56 denies over 4,201 Write/Edit ops**
> pre-AC-7 (~1.33 % of every edit hard-walled) and 0 denies / 0 organic warns
> over 1,369 ops after. **No ADR amendment** — E.4 never named L1 and
> `0013:333-336` delegated stateful loop-detection to PLANs, so L1 had zero ADR
> backing and an amendment would have *created* the ratification it never had.
> Also eliminated: the three harness registrations that existed only for L1 —
> the PreToolUse `Write|Edit` one spawned a Python process on **every single
> edit** to compute what is now a guaranteed no-op.
>
> **The evidence discipline is the transferable part.** L1 had not fired
> organically since AC-7, so a test that merely observes silence passes
> *identically* before and after the excision. Every absence is therefore paired
> with a live control in the same run: L1 deny **YES→NO** beside L4 deny
> **YES→YES**; L1 warn **YES→NO** beside the shell-hygiene advisory
> **YES→YES**. Both AC-11 probes reintroduced their exact defect and went RED.
>
> 🔴 **Three PLAN defects, one root cause — worth carrying to the next excision
> PLAN.** s206's R2 walked the call graph **backwards** from `LoopType.FILE_EDIT`
> and found the name-less sites; **nobody walked it forwards** from the functions
> being deleted, so every callee reachable only from an L1 entry point stayed
> invisible. Step 4 said to KEEP two imports whose only callers it deletes (and
> never mentioned a third); Step 3 named `_apply_commit_reset` but not the four
> symbols it exclusively owned; Step 5 omitted three constants. ⚠️ **AC-9 would
> not have caught the worst of them** — ruff flags a dead *import* but not a dead
> *private function*, so `_state_path()` would have shipped dead past a green
> gate. **Also a live-behaviour fix:** the deny message named three reset paths,
> all of them L1 paths deleted by this PLAN, on a message only L4 now reaches.
>
> **Also (#1095): D-4's direction RULED (a) by Cray — on a corrected premise.**
> Every prior record framed the fork as "teach the translator `group_by`", which
> is not the problem: `group_by` already works for `max`/`min`/`avg`/`sum`. What
> is unrepresentable is `count` **with** `group_by` — `_AGGREGATE_OPS` excludes
> `count` — so option (a) is four seams in one file, not the scope-uncertain
> prompt work the fork was priced against. ⚠️ **ADR-0036 is newly load-bearing:**
> it designs a "pick which vertical" portal, which *is* a landing surface, so it
> is an ordering prerequisite of the landing/framing layer. Nothing recorded that.

> **Session 216, 2026-08-08 (head_commit `94fac66` → `f987888`) — four PRs merged
> (#1090–#1093), 0 open. Theme: PLAN-0100 is COMPLETE 13/13 and ARCHIVED — the
> exposure PLAN closed after its last three ACs fell in one session, each to a
> DIFFERENT kind of move.**
>
> **Three ACs, three kinds of move — the distinction is the transferable part, and
> flattening it to "three ACs closed" loses the whole lesson.** **AC-6(c) closed by
> arithmetic over evidence already in hand** (#1090): case 1 was re-scored against the
> D-3 fix — **no new run** — its only two misses having been the `.woff2`
> content-types, fixed and live-verified in s215 on a `cf-cache-status: MISS`. The same
> PR corrected AC-6's stale "case 4" citation for the rate cap (under v2 numbering the
> rate cap is **case 6**; case 4 is arm posture) and recorded the carve-out as
> discharged through the Step-11 deferral branch. **AC-11 closed by a fresh live
> measurement** (#1091). **AC-12 closed by VERIFYING rather than drafting** (#1093),
> after which PLAN-0100 went `Draft` → `Complete` and was `git mv`-ed to
> `docs/plans/done/`.
>
> **`T_edge` = 125 s, and why s215 could not get it.** s215 failed five times. Four
> were ordinary instrument faults, already logged. The fifth was subtler: the
> instrument *worked*, but it stalled the upstream with `qwen3.6:35b` — a model big
> enough to cold-load — and it cold-loaded **and answered** in 54 s. **A slow upstream
> is not a stalled one**; vero-lite replied before the edge could cut in. s216 replaced
> *slow* with *never answers*: a socket that `bind`s and `listen`s but **never calls
> `accept()`**, verified from **inside the app container** (connect in 0.013 s, then
> `TimeoutError`, zero bytes). Two runs positive-control each other — a 120 s window
> yielded only `T_edge > 120 s`, recorded **INSUFFICIENT-EVIDENCE, not a pass**, and it
> missed by **five seconds**; a 600 s window returned **HTTP 524 at 125.19 s**.
> ⚠️ **Cloudflare documents 100 s; the measured value is 125 s** — the path is a
> `cloudflared` Tunnel, not a proxied origin, so a run that had trusted the published
> number would have concluded the cut-off was unreachable.
>
> **Cray's ruling is what produced that number.** Offered the `≥ 54 s` bound as
> discharging P4(i), Cray typed that **a bound is not the number the clause asks
> for**. Had Code accepted the bound on its own judgement it would have been rewriting
> an AC to fit the evidence available, and neither the 125 s nor the Tunnel-vs-docs
> finding would exist.
>
> **AC-12 is the reusable one.** The next move *looked* like a `plan-drafter` dispatch
> — Code cannot author ADRs. Verifying the fact-pack first showed all three
> "unrouted" ADR-0035 amendments had **already landed on 2026-08-06 in `06e2b84`**;
> only the tick was missing. Same shape as #1089's unmet "Record which was used".
> **A doc saying "not done" is a claim to grep, not evidence.**
>
> 🟡 **D-5 — a TRANSIENT Safe Browsing phishing flag** on the Access login callback,
> found while fetching a fresh cookie and lifted within ~30 min. **No security posture
> was involved:** the unauthenticated control stayed **302** on five paths across two
> runs, including under a browser UA. Four candidate causes were ruled out **by
> measurement** — a host-wide block (`/health` clean in the same Chrome), a path-prefix
> block (bare callback clean, the omnibox `Dangerous` chip gone, no bypass clicked), a
> flag inherited from a previous domain owner (RDAP: `registration` == `last changed`
> == 2025-12-15), and a neighbour on the zone (only `oct-energy` resolves). **The cause
> is UNDETERMINED and is recorded as such** — Google Search Console is the only source
> that would report why, and only if it recurs.
>
> **Also:** the `ms-s1-admin` skill gained the **stripped-`"` trap** (#1092) —
> PowerShell strips double quotes when handing argv to a native exe — plus a comparison
> table of all three traps in that family. **Five residual items outlive PLAN-0100**;
> they are carried as a pointer in Active TODOs and none of them gates anything.

> **Session 215, 2026-08-08 (head_commit `a5ae3cd` → `94fac66`) — four PRs merged
> (#1084–#1087), 0 open. Theme: PLAN-0100 Step 11 — the Cray-gated live run against
> the published demo — was executed end to end; it found four defects, three of which
> were fixed, redeployed and re-verified live in the same session.**
>
> **The run.** Driven through the ratified Cloudflare Access gate with a cookie from a
> real one-time-PIN login (the s214 route), under Cray's typed §8 go, with the
> unauthenticated control re-run alongside (302/302/302). **Cases 0, 2, 3, 4, 6, 8
> CLOSE.** **Case 1 closes 19/21 on its own read** — the two misses were the font
> content-types, and two further failures were probes the runner added, not rows the
> case asks for. **Case 5 FAILED, was fixed, and re-verified PASS.** **P5 PASS**;
> **P4(ii) PASS** twice independently; **P4(i)'s exact `T_edge` is UNMEASURED** —
> recorded as INSUFFICIENT-EVIDENCE with a measured lower bound (`T_edge ≥ 54 s`)
> that excludes the clause's own FAIL condition of `< 40 s`.
>
> 🔴 **Four defects, none catchable offline.** **D-1 — 90+ published `POST /query`
> wrote ZERO prompt-log rows.** The image never created the volume mount point, so
> Docker made it root-owned while the runtime is uid 999; `prompt_log.record` swallows
> `OSError` **by design**, so it failed silently and ADR-0035 D6's whole regime (RoPA,
> 90-day retention, the purge command, the DSR path) described a file that did not
> exist. **D-2** — the prompt log named a model that never ran
> (`ollama_default_model` / `gemma4:26b` recorded while the engine ran
> `recommender_model` / `gpt-oss:20b`). **D-3** — bundled `.woff2` fonts served as
> `text/plain`: the slim image ships no `/etc/mime.types` and Python's built-in table
> has no `.woff2`. **D-4**, narrowed after a second measurement: **only** the
> `group_by` verified_query fails — `count` aggregation works, and the second query's
> empty result is the **correct** answer (the dataset holds no `feeder` asset). Left
> open, direction undecided. **Also:** the demo pinned no `keep_alive`, so the first
> visitor after an idle spell waited the full 25 s timeout and got a degraded,
> ungrounded answer; fixed by sending the existing `ollama_keep_alive` on every chat
> call.
>
> **The finding worth carrying forward:** `deploy.py`'s seven green checks prove the
> **container** runs the new image; they do **not** prove a **visitor** receives it.
> D-3 read as still-broken after redeploy because Cloudflare was serving a
> `text/plain` copy cached while the defect was live (`cf-cache-status: HIT`,
> `max-age=14400`), closed by a manual **Purge Everything** (Cray). Nothing in the
> pipeline purges the edge, and the repo's `?v=cNN` convention does not reach fonts
> (referenced from inside CSS with no version parameter). A purge step or versioned
> font URLs belongs in the redeploy runbook — **not done**.
>
> **Twelve instrument faults** were caught and are listed in the PLAN record. The two
> most consequential: the probe matrix first scored **0/43 against a completely
> healthy demo**, because Cloudflare's Browser Integrity Check rejects a
> `Python-urllib` User-Agent *before* Access is consulted; and a `/query` oracle
> passed on the string *"I couldn't translate that question into a query over the
> operational data."* Common root: **checking a proxy for the thing rather than the
> thing.** **No AC was ticked — PLAN-0100 stays `Draft` at 10 of 13.** _[STATUS's
> frontmatter had stalled at `1384278`; s214 in fact closed at `a5ae3cd`, so the
> commits between them are s214's later merges, reconciled here rather than
> restated.]_

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
| 2026-08-10 | **s218 cont. — ALL EIGHT PLAN-0103 slots RULED (Cray, typed), and SD-1 spawned ADR-0037 `Proposed` (#1104).** 🔴 **SD-1 OVERRULED both the drafter and Code's R2 concurrence** — two reviewers agreeing was not independent evidence; both priced the cost of *having* an ADR and neither the cost of *not*. **ADR-0037** is the result and the home for two findings previously recorded nowhere (D6's LLM-route scope; the audit-chain erasure boundary, marked UNVERIFIED and made a pre-bring-up measurement, not asserted). ⚠️ It gates **fleet's half only** — Step 4's gate map names what proceeds regardless. Rulings read in the PLAN's §Surfaced decisions | `9160f4f` (head_commit) / [#1104](https://github.com/CrayJThiemsert/vero-lite/pull/1104) / `docs/adr/0037-published-system-data-persistence-posture.md` |
| 2026-08-09 | **s218 — PLAN-0103 DRAFTED `Draft` (#1101): vero-lite's side of the multi-vertical portal, ADR-0036's D6 follow-on.** 10 Steps, 11 ACs, 7 SD slots; five Cray LOCKED calls. Built around the hard boundary — **zero portal-repo files, no landing page here**; card copy is one-system-per-file with **no roster** (AC-5 guards it). 🔴 Two findings reshaped it and are worth not re-deriving: **`isPublished()` has ELEVEN consumers across eight files**, so the constant is *eliminated* rather than a third profile added; and **fleet publishing Tab C makes a SECOND assisted system** on one Ollama, contradicting the premise ADR-0036 D5 wrote its aggregate posture on | `f2731be` (head_commit) / [#1101](https://github.com/CrayJThiemsert/vero-lite/pull/1101) / `docs/plans/0103-portal-landing-and-per-system-published-profiles.md` |
| 2026-08-09 | **s218 — ADR-0036 RATIFIED (Cray, typed): a deployed vertical instance IS a system (#1099).** Accepted as drafted (D1 scope (a), D2 + the `oct-<vertical-id>` label convention, D5 profile ownership, OQ-1 retire the bare `oct.` label); ADR-0035 D1–D4 untouched, D4's reopening trigger does not fire. ⚠️ **The ratifying edit must also remove the ADR from the gate's set-equality assertion in the SAME commit** — an in-flight marker, not an exemption; both directions of that rule were exercised within a day (ADR-0037 re-added it). Verified behaviourally with two controls, not just green | `1a6e29b` (head_commit) / [#1099](https://github.com/CrayJThiemsert/vero-lite/pull/1099) / `docs/adr/0036-vertical-as-system-multi-vertical-demo-portal.md` |
| 2026-08-08 | **s217 — PLAN-0102 COMPLETE 11/11 and ARCHIVED (#1096): the L1 loop-detect guard is RETIRED**, executing Cray's typed s205 ruling. Evidence: **zero true positives across its whole live history** against **≥ 56 denies / 4,201 ops** (~1.33 % of every edit hard-walled). No ADR amendment — L1 had zero ADR backing, so one would have CREATED the ratification it never had. 🔴 **Three PLAN defects found by executing it, one root cause worth carrying:** the scope review walked the call graph BACKWARDS from the marker and never FORWARDS from the functions being deleted — ⚠️ and **ruff flags a dead import but NOT a dead private function**, so an AC reading "ruff clean" passes over dead code | `36e5735` (head_commit) / [#1096](https://github.com/CrayJThiemsert/vero-lite/pull/1096) / `docs/plans/done/0102-retire-l1-loop-detect.md` |
| 2026-08-08 | **s217 — D-4's direction RULED (Cray, typed): option (a), teach the engine (#1095)** — and the ruling changed price because the fork had been posed on a wrong premise (`was an error`). `group_by` already works for `max`/`min`/`avg`/`sum`; what is unrepresentable is **`count` WITH `group_by`** (`_AGGREGATE_OPS` excludes `count`), so (a) is **four seams in one file**, not open-ended prompt work. **Nothing built** — still the largest ungated Code item | `c2e3278` ([#1095](https://github.com/CrayJThiemsert/vero-lite/pull/1095)) / `services/engine/nl_query.py` / `docs/adr/0036-vertical-as-system-multi-vertical-demo-portal.md` |
| 2026-08-08 | **s216 — PLAN-0100 COMPLETE 13/13 and ARCHIVED (#1090–#1093).** Its last three ACs fell to three DIFFERENT kinds of move (re-scoring evidence in hand · measuring · verifying a claim already true) — the distinction is the transferable part. **`T_edge` = 125 s (HTTP 524)**, measured against a socket that `listen`s but never `accept`s, because **a slow upstream is not a stalled one** (a 54 s stall *answered*); ⚠️ **Cloudflare documents 100 s** — Tunnel ≠ proxied origin. Cray typed that **a bound is not the number the clause asks for** | `f987888` (head_commit) / [#1091](https://github.com/CrayJThiemsert/vero-lite/pull/1091) / [#1093](https://github.com/CrayJThiemsert/vero-lite/pull/1093) / `docs/plans/done/0100-exposure-published-demo-surface.md` |
| 2026-08-08 | **s215 — PLAN-0100 Step 11 RAN live against the published demo (#1084–#1087): cases 0, 2, 3, 4, 6, 8 CLOSE; case 5 FAILED → fixed → re-verified PASS; case 1 19/21.** Four defects, **none catchable offline** — the headline one: **90+ published `POST /query` wrote ZERO prompt-log rows** (root-owned mount vs uid 999; `record` swallows `OSError` **by design**, so ADR-0035 D6's whole regime described a file that did not exist). ⚠️ **The edge cache masked the redeploy** — `deploy.py` proves the container, not the visitor | `94fac66` (head_commit) / [#1086](https://github.com/CrayJThiemsert/vero-lite/pull/1086) / [#1087](https://github.com/CrayJThiemsert/vero-lite/pull/1087) / `docs/plans/done/0100-exposure-published-demo-surface.md` |
| 2026-08-08 | **s214 — the published demo has a REPEATABLE deploy procedure, and it RAN under Cray's typed §8 go (#1073–#1078).** Script + runbook + 18 guard/scenario tests; it asserts an **effect** (the container's `.Image` == the id just loaded), not a step count. **3977 green over a script whose first remote command failed on the host**: the deploy host's ssh shell is **PowerShell**, so every `--format={{…}}` died — **and the guard written one PR earlier went GREEN over it**, its hazard set having come from what was imagined, not measured | `1384278` (head_commit) / [#1076](https://github.com/CrayJThiemsert/vero-lite/pull/1076) / `deploy/published/deploy.py` / `docs/runbooks/published-demo-redeploy.md` |
| 2026-08-07 | **s213 — the published OCT demo is LIVE behind Cloudflare Access (#1069–#1072); PLAN-0100 Step 11 is now BLOCKED on an unruled composition question.** `python-multipart` was a RUNTIME dep absent from the shipped image, which **could not boot for eleven days while 3943 tests stayed green**; the fix adds a CI step that rebuilds the image's dependency set and imports the entry module. ⚠️ Access returns **302 on every path**, so exact-status cases cannot hold through the gate | `fe1d018` ([#1072](https://github.com/CrayJThiemsert/vero-lite/pull/1072)) / `6e6563a` ([#1071](https://github.com/CrayJThiemsert/vero-lite/pull/1071)) / `docs/plans/done/0100-exposure-published-demo-surface.md` |
| 2026-08-06 | **s212 — PLAN-0100 Step 9 RAN as its own sanctioned OFFLINE FALLBACK (#1067): cases 2 + 7 PASS, cases 0/1/3–6/8 NOT COVERED → inherited by Step 11.** No `cloudflared` binary, no credentials, and case 0 gates the rest. **Non-vacuity DEMONSTRATED** — anchors stripped on a `/tmp` copy flipped the excluded `/insights/query` to `http://app:8000`. ⚠️ A `tunnel ingress validate` flag order that exits **0 while validating nothing** was among three committed defects fixed | `4a88f37` ([#1067](https://github.com/CrayJThiemsert/vero-lite/pull/1067)) / `docs/plans/done/0100-exposure-published-demo-surface.md` |

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

- [ ] **PLAN-0103 — vero-lite's side of the multi-vertical portal. DRAFTED s218 (#1101), `Status: Draft`, nothing built.** ADR-0036's D6 follow-on: per-system published profiles + the landing/framing **content spec**. 10 Steps, 10 ACs, **7 SD slots**. ✅ **ALL EIGHT SLOTS RULED s218 (#1104)** — read them in the PLAN's §Surfaced decisions, each stamped `RULED (Cray, typed, s218)`. 🔒 **What still gates: ADR-0037's ratification, and it gates FLEET'S HALF ONLY.** Step 4 carries a **gate map** naming exactly what proceeds regardless — procurement's entire half, Steps 2–3, energy's move, Step 8's content, Step 9's measurement. It is written "read this before stalling anything" because a bare "ADR-gated" label reads as stop-everything: s206 lost a session to that misreading of PLAN-0100's headline when six items carried no gate. ⚠️ One caveat the map itself carries (Code R2): the **persona-picker UI is not gated but fleet is its only consumer**, so it is orphaned work if ADR-0037 ratifies otherwise than proposed — build it in parallel, never first. **Read the PLAN, never a restatement:** `docs/plans/0103-portal-landing-and-per-system-published-profiles.md` (§The hard boundary · §Surfaced decisions). ⚠️ Two things a future reader must not re-derive: the **hard boundary** — ADR-0036 D1 + ADR-0035 D4/L5 make the `portal.` landing surface, ingress map, Access policies and domain **portal-repo property**, so this PLAN builds no landing page here and ships a spec instead; and `isPublished()` has **ELEVEN consumers across eight files**, so any step touching published-ness must walk all of them (`tools/excision_scope.py` + the `excision-scope` skill).
- [x] **PLAN-0100 — the ADR-0035 exposure PLAN. COMPLETE 13/13 and ARCHIVED (s216).** The demo is LIVE, REDEPLOYABLE and DRIVEN. Step 11 ran end to end through the ratified Cloudflare Access gate under Cray's typed §8 go, and every pass/fail read is discharged. Closed in s216: **AC-6(c)** by re-scoring case 1 against the D-3 fix (its only two misses were the `.woff2` content-types, fixed and live-verified on a `cf-cache-status: MISS` — proven to reach a *visitor*, not merely the container); **AC-11** by measuring **`T_edge` = 125 s (HTTP 524)** after s215 could only bound it, Cray having ruled that a bound is not the number the clause asks for; **AC-12** by *verifying* rather than dispatching — its three "unrouted" ADR-0035 amendments had already landed on 2026-08-06 in `06e2b84` and only the tick was missing. **Read the archived PLAN, never a restatement:** `docs/plans/done/0100-exposure-published-demo-surface.md` (§"Step 11 closure verdict" for the closeout; §"Defects the live run found" for D-1..D-5; §Instrument failures for the twelve faults). **Five residual items OUTLIVE it, which is why this is a pointer and not a deletion:** **D-4**'s direction — **RULED s217 (Cray, typed): option (a), teach the engine.** _[⚠️ The fork was posed on a wrong premise and the correction is what changed its price — classify `was an error`, not superseded. Every prior record (this row, the s215 Current Focus above, the archived PLAN, the s216 handoff) framed (a) as "teach the translator `group_by`", implying open-ended LLM-prompt work. **`group_by` already works** — for `max`/`min`/`avg`/`sum`. What is structurally unrepresentable is `count` **with** `group_by`: `_AGGREGATE_OPS = {max, min, avg, sum}` (`services/engine/nl_query.py:75`) excludes `count`, and `services/engine/nl_query.py:536` rejects the combination outright, so energy's second verified_query — "How many active assets are hosted at each site?" (`verticals/energy/ontology/energy_v0.yaml:26-27`) — has no `StructuredQuery` that can carry it and burns the retry budget to `QueryTranslationError`. So (a) is **four seams in one file** (`:536` relax · `_compute_aggregate`/`_collect_numeric` `:770-810` · `_AGG_LABEL`/`_phrase_aggregate` `:1050-1067` · `_infer_group_by` `:907`) ≈ one PR + tests — not the scope-uncertain prompt work the fork was priced against. Grounded s217 by an Explore fan-out against the code; **no PLAN drafted, nothing built.**]_ · a **cache-purge step or versioned font URLs** in the redeploy runbook — nothing in the pipeline purges the edge, and the `?v=cNN` convention does not reach fonts · **D-5**, a *transient* Safe Browsing phishing flag on the Access login callback (lifted within ~30 min, no security posture involved, cause UNDETERMINED — Google Search Console is the only source that reports why, if it recurs) · **ADR-0036** — **RATIFIED s218 (#1099), DISCHARGED.** _[Its ordering role, found s217, is now history rather than a warning: ADR-0036 designs an "open the demo and pick which vertical" portal, which **is** a landing surface, so it was an ordering prerequisite of the landing/framing layer and the marketing carrier's §8 — which gates that `plan-drafter` dispatch only on PLAN-0100 closing — never knew about the collision. Both gates are now open. **OQ-1 adopted** (retire the bare `oct.` label); **OQ-2/OQ-3 remain open and are not blockers** — OQ-2 (the aggregate in-flight LLM posture across N systems) is pinned by the follow-on PLAN, OQ-3 (when `fleet_maintenance` becomes system #3) is Cray's trigger, not a schedule.]_ **What is now live instead: the landing/framing-layer PLAN itself (next free number 0103), G2-gated ⇒ `plan-drafter` dispatch**, its scope fixed by ADR-0036 D6. _[Also grounded s217: the published surface today has **no** landing page, intro copy or CTA at all — it boots straight into Tab A, and the published profile drops tabs `['E','G','H','I','J']` (`services/api/static/assets/app.js:68`); `.ask-welcome` is Tab C's empty state, not a landing surface.]_ · **`published.env` pins no `OLLAMA_KEEP_ALIVE`**, so the published surface silently inherits the code default of 30m.
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
- [x] **PLAN-0102 — retire L1 loop-detect. COMPLETE 11/11 and ARCHIVED (s217, #1096).** L1 is gone from all four hooks, the shared state layer, and the three harness registrations that existed only for it. L2/L3/L4 are intact and asserted so. **Read the archived PLAN, never a restatement:** `docs/plans/done/0102-retire-l1-loop-detect.md` (§Context for the measurement + the s180 "0 denies" correction to a **≥ 56** floor; §Governance for why no ADR amendment; §"Corrections found by executing this PLAN" for the three defects + the `observe()` scope decision). **Two residues outlive it, both non-gating and recorded ONLY here:** (1) **`observe()` is now callerless and was deliberately kept** — deleting it would turn `_record`'s `bump` into a constant and pull a refactor into the function every surviving L2/L3/L4 increment flows through; revisit only if that module is being reworked anyway. (2) The **forwards-call-graph gap** that produced all three PLAN defects is a *method* fix owed to the next excision PLAN, not a code fix — no artifact carries it yet.
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
