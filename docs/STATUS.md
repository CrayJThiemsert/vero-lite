---
last_updated: 2026-08-21T04:42:58+07:00
session: 241
current_batch: "s241 (2 days) — FIVE PRs (#1229, #1231–#1234), 0 open. Two new pre-commit guards, #18 retired-claims and #19 AC-consistency, both of which caught real defects; PLAN-0107/0108 doc-debts corrected."
current_actor: code
blocked_on: "Nothing blocks repo work; main green, 0 open PRs. PLAN-0107 AC-9 is BLOCKED on a Cray ruling (three options on the PLAN); PLAN-0109's three ruled-content defects need a drafter round before its Step 5."
next_action: "Cray's pick — PLAN-0111 Step 1 (+Step 6 paired; #1, S, six SDs ruled); PLAN-0107 AC-10 (#2, S, fully offline, scope nl-01…nl-11); the ฿ realized-vs-projected join (M); or rule AC-9's re-scope."
head_commit: 6a2e34c
recent_commits: [6a2e34c, ccbd04a, 2e52ac4, 4ae6728, 34c498b, 5cdbf68, 44a0ec9, 8fd3848, e22d824, d912891]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 241, 2026-08-20→21 (head_commit `8fd3848` → `6a2e34c`) — FIVE PRs
> MERGED ([#1229](https://github.com/CrayJThiemsert/vero-lite/pull/1229),
> [#1231](https://github.com/CrayJThiemsert/vero-lite/pull/1231)–#1234), 0 open:
> it opened as *"rank the next work"* and became a MECHANISM change.**
>
> 🔴 **The grounded fan-out found the backlog was RETRIEVAL debt, not technical
> debt** — eight measured facts `git grep` could not find, because they lived
> only in a gitignored handoff and would have died with it. So the work became
> two guards that make such debt findable: `tools/check_retired_claims.py`
> (hook #18) and `tools/check_ac_consistency.py` (#19); the row below states
> the limits each one declares about itself.
>
> 🔴 **Both caught real defects before they could merge — neither was built from
> a hypothetical.** The retired-claim guard **blocked its own first commit**,
> exposing a real design flaw: a file exempted from *declaring* could not exempt
> *its own examples* either (fixed with `Marker.local_only`). It then flagged
> **this file** — STATUS's own narrative quoted a dead claim. The AC-ledger
> guard's first run named PLAN-0108's live duplicate label, and a second nobody
> knew about in `docs/plans/done/0042-at2-managerial-build.md`.
>
> 🔴 **The tempting wrong fix, recorded because it will recur:** narrowing the
> retired text until STATUS's quote stopped matching would have silenced the
> guard — **that is editing the artifact to satisfy the instrument.** A marker
> went beside the quote instead, so on a surface an agent reads every session a
> dead claim carries a label saying so — *"`ms-s1-max` has no WSL DNS entry"*.
> <!-- retired: "`ms-s1-max` has no WSL DNS entry" -->
>
> ⚠️ **One honest failure, recorded not dropped: findings were reported from a
> subagent that never returned.** Four of five grounding agents came back; the
> fifth failed silently and its notice arrived much later. **Two rows of the
> ranking's claim-vs-code table were written with no source** and were RETRACTED
> on measurement (a `/runs` docstring citation, a scenario-marker census) —
> items ranked #8 and below only, not the #1/#2 picks. The memory rule *"verify
> a subagent delivered"* existed and was not applied.
>
> ✅ **The documentation debts then landed** — #1232 PLAN-0107's five, #1233
> PLAN-0108's duplicate label; the rows below own them. Gate on `6a2e34c`: **4206 passed / 8 skipped**, `ruff` + format clean
> over 647, `mypy --strict` clean over 201 files; every PR `sha=MATCH` across
> local HEAD, PR head and the run's own `head_sha`.

> **Session 240, 2026-08-19 (head_commit `dbb3e58` → `8fd3848`) — THREE PRs
> MERGED (#1225–#1227), 0 open. PLAN-0107 AC-11 CLOSED, `DEPLOY.md` gained a
> pre-ship check, and PLAN-0111 was drafted with all six of its SDs ruled in the
> same session.**
>
> 🔴 **The organising finding: three losses of correct work, two of them mine
> this session — each caught by a discipline, none by re-reading a summary.**
>
> 🔴 **(1) A `git merge` reported success and silently reverted a merged PR.** It
> first died with `Unable to write index` although the two sides touched disjoint
> files; `git status` then read *"All conflicts fixed but you are still merging"*
> with **no `index.lock` on disk**. Concluding it produced a merge commit whose
> tree **dropped #1225's entire `DEPLOY.md` change** — while `git merge-base
> --is-ancestor origin/main HEAD` answered **YES**. **Ancestry is not content.**
> Caught by grepping the merged tree for a string only the incoming side
> introduces; recovered by `git reset --hard` to my own commit and re-merging,
> which reported the expected `53 insertions(+)`.
>
> 🔴 **(2) The first non-vacuity probe proved the wrong thing.** The scenario's
> `assert status_code == 422` sat *before* the month-end read, so disarming the
> guard reddened **that** line and returned — the money assertion, the claim the
> module exists to make, never executed. Reordered so the ฿ assertions fire
> first; the RED now reads `assert Decimal('-15000.00') == Decimal('20000.00')`,
> the export holding one row carrying the credit note's document date.
>
> ⚠️ **(3) Two ACs in the first-pushed PLAN-0111 draft named test files that do
> not exist** — corrected to grep-verified paths. Separately, swapping a stale
> line citation for a symbol produced a *wrong symbol* (`get_case` for
> `get_closeout`) until the enclosing function was grepped rather than assumed.
>
> ✅ **PLAN-0107 AC-11 CLOSED — negative money refused at the close-out producer**
> (#1226), plus a four-test scenario module. 🔴 **Why a refusal and not `sum()`:**
> `repair_case_closeout` is append-only with **latest-wins** — `latest_closeout`
> returns one row per case and both consumers read it, so a credit note keyed
> there does not join the invoice, it **REPLACES** it. Measured: month-end moves
> `20,000.00` → `-15,000.00` with every row still looking perfectly filled in.
> Admitting the negative is the **silent** option, not the lenient one. 🔴 **It
> closes an asymmetry rather than adding a rule** — the quote side already refused
> negative money on the same reasoning
> (`tests/api/test_cases_endpoint.py::test_a_negative_quote_is_refused`, *"Not a
> discount — a typo or a credit note"*); the close-out was the outlier, and it is
> the end that feeds the month-end figure. A credit note is internally
> **coherent** (`-14,018.69 + -981.31 = -15,000.00`), so it passes the existing
> totals check — the sign check is its own door, and the scenario pins that
> discriminator. The refusal is **INTERIM**, says so in the handler docstring, and
> names its lift condition: only with a schema holding invoice and credit as two
> coexisting facts.
>
> ✅ **`DEPLOY.md` §2a Pre-ship** (#1225) — build locally, then compare a
> `sha256sum` taken **inside the freshly built image** against the working tree,
> before the host is touched at all.
>
> ✅ **PLAN-0111 drafted and all six SDs RULED** (Cray, typed 2026-08-19, #1227);
> `Status: Draft` — the SDs were ratified, not the PLAN. **SD-E: multiple partial
> credits may coexist** (ทยอยลด; over-credit refused 422), **which forces SD-A to
> (b), a separate `repair_case_credit_note` table** — latest-per-kind would re-arm
> the replacement trap one level down. SD-B (b) one composite reader · SD-C (b)
> two lines matching real documents · SD-D (a) credit inherits the case's `RC-`
> number · SD-F (a) KPI counts repairs, not documents. Newly load-bearing from
> those rulings, each verified against code: the new table must join retention's
> `_FK_CHILD_MODELS`; 🔴 **`load_monthly_export`'s ungoverned branch enumerates
> cases only from `RepairCaseCloseout.entered_at`, so a credit-only month would
> emit no row at all** and must union a second source; and 🔴 **AV-2 stopped being
> hypothetical** — a table FK'd to the close-out with no `case_id` column is
> invisible to both retention walks, prohibited without a guard extension
> witnessed RED first. ⚠️ **AV-1 is the one thing this repo cannot answer** — what
> Express/accounting reconciles a ใบลดหนี้ against; SD-C is provisional on it, and
> the PLAN requires confirming it before Step 4, not before merge.
>
> **Gates: 4174 passed / 8 skipped** (4170 baseline + 4), `mypy --strict services/
> verticals/` clean over **201** files, bare `ruff check .` + `ruff format
> --check .` clean over **643**. Three non-vacuity probes witnessed RED: the
> `DEPLOY.md` operator-path guard naming `DEPLOY.md:111` · the guard-disarm
> reddening the ฿ assertion · the `< 0` → `<= 0` tightening reddening **only** the
> zero-VAT positive control — disjoint sets, which is what makes the control a
> control. **No host-state action this session; MS-S1 was not touched.**
>
> ⚠️ **CARRIED FORWARD from s239's `next_action` — recorded here because the
> frontmatter cap cannot hold them and nothing else in this file does; none was
> touched this session, none is resolved:** (i) the **font-size decision still
> gates re-measuring every geometry number in the beat-4 mockup**; (ii) the
> **run-list backlog badge on the host is still unmeasured** (a host-state read,
> so it needs its own typed §8 go); (iii) the **three Advisory-proposal
> candidates are still unnamed**, so the gate panel still reads as unfinished.

_[Current-Focus rotation ledger. The sessions-233–234 and 235/236 blocks rotated
to `docs/status-archive/2026-h1d-current-focus.md` at earlier reconciles; the
**sessions-237–238 and session-239** blocks rotated there this reconcile —
**one session below the four-session window, deliberately**, because the s241
Active-TODO corrections had to land without growing this file (SD-1 in the s241
reconcile report). Rotated with them: s237's video-rulings carried risk, since
DISCHARGED s239 to `docs/strategy/public/intro-video-production-rulings.md`, and
s239's headline — eight PRs, two host-state deploys, and *"a summary that is
ACCURATE about what it cites still shrinks"*; s239's two host records survive
tracked at `docs/logs/2026-08-18-s239-*` and `docs/logs/2026-08-19-s239-*`.]_

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
| 2026-08-21 | **s241 — FIVE PRs (#1229, #1231–#1234): the backlog measured as RETRIEVAL debt, not technical debt, so the session shipped two pre-commit guards.** 🔴 **Both caught real defects before merge** — the retired-claim guard blocked its own first commit and flagged STATUS's own narrative; the AC-ledger guard found PLAN-0108's live duplicate label plus one in `done/0042`. 🔴 **The wrong fix was to narrow the retired text until the quote stopped matching** — editing the artifact to satisfy the instrument. ⚠️ **Findings were reported from a subagent that never returned; two unsourced rows RETRACTED.** | `6a2e34c` / [#1234](https://github.com/CrayJThiemsert/vero-lite/pull/1234) / `docs/conventions/retired-claims.md` |
| 2026-08-19 | **s240 — THREE PRs (#1225–#1227); PLAN-0107 AC-11 CLOSED and PLAN-0111 drafted with all six SDs ruled (Cray, typed).** 🔴 **A `git merge` reported success and silently reverted #1225** — `merge-base --is-ancestor` answered YES while the merged tree had dropped the change; **ancestry is not content**. 🔴 **A non-vacuity probe proved the wrong thing** — the `422` assert sat before the money read, so the claim the module exists to make never executed. 🔴 **Latest-wins means a credit note REPLACES the invoice** (`20,000.00` → `-15,000.00`), so admitting it is the silent option; the refusal closes the quote side's asymmetry and is INTERIM by docstring. **SD-E forces SD-A to a separate `repair_case_credit_note` table.** | `8fd3848` / [#1226](https://github.com/CrayJThiemsert/vero-lite/pull/1226) / [#1227](https://github.com/CrayJThiemsert/vero-lite/pull/1227) / `docs/plans/0111-*.md` |
| 2026-08-19 | **s239 — EIGHT PRs (#1216–#1223) and TWO host-state deploys under separately typed gos.** 🔴 **An ACCURATE summary still shrinks:** the video rulings were seven, not four — one typed two days earlier and recorded inline rather than in the table, carrying a live tripwire. Rehomed tracked, each row stamped with its source position. 🔴 **s238's correct forward-slash fix silently disarmed the path guard** for the ten commands it corrected, and the module's own `checked >= 5` floor stayed satisfied by the READMEs — a count floor cannot see a document category go dark. Now 26 paths checked, 0 broken. 🔴 **The shared `deploy.py` cannot deploy this system** and §3 handed it over without saying so; `DEPLOY.md` created, and its FIRST use found its own gap (`<last-deployed-sha>` comes from the HOST checkout, not the image's build sha). ✅ Tab F opens the origin narrative with six passages mapped to six steps, `reshape` deliberately unmapped. ✅ R8 ruled: drop the ฿15,000 contrast. ✅ Brand mark live — and **not legible at 28 px**, recorded rather than discovered later. | `dbb3e58` / [#1218](https://github.com/CrayJThiemsert/vero-lite/pull/1218) / [#1221](https://github.com/CrayJThiemsert/vero-lite/pull/1221) / `deploy/published/oct-fleet-maintenance/DEPLOY.md` / `docs/strategy/public/intro-video-production-rulings.md` |
| 2026-08-18 | **s238 — PLAN-0110 BUILT and DEPLOYED; COMPLETE 7/7, ARCHIVED.** Tab A run markers + a three-mode filter + a deploy-time demo reset. 🔴 **The gate's three proposals ALL name a `case_id`; two resolve to no row** — reading the truck off the event instead of the case table stamps nothing forever, green. ✅ Live: `CONSUMED` → `PRISTINE`, subjects landed, #1209's fix finally live, audit rows 9 → 17. 🔴 **The deploy found `DEMO-RESET.md`'s bootstrap gap** — the tool ships in the image it must run before. | `32854ab` / [#1213](https://github.com/CrayJThiemsert/vero-lite/pull/1213) / [#1214](https://github.com/CrayJThiemsert/vero-lite/pull/1214) / `docs/logs/2026-08-18-plan0110-*.md` |
| 2026-08-18 | **s237 — the video pivot: measuring the LIVE demo REFUTED beat 4.** Tab G is not on the published profile **by ruling**; the storyboard was verified on a dev profile. Cray ruled (A) shoot published; Tab H replaces three shots with ONE frame, no scrolling. 🔴 **A real fleet defect found on live** — a settled repair in the visitor's approval queue, root cause in TWO layers (the terminal step is itself gated, so one resume is not enough). PLAN-0109 + PLAN-0110 drafted, all five SDs ruled. ⚠️ **Video rulings live only in a gitignored handoff.** | `b906193` / [#1208](https://github.com/CrayJThiemsert/vero-lite/pull/1208)–[#1212](https://github.com/CrayJThiemsert/vero-lite/pull/1212) / `docs/conventions/local-first-published-parity.md` |
| 2026-08-18 | **s236 — PR-B's carve-out rehome COMPLETE (61,736 → 48,852 B, under R1's soft target) and PLAN-0107 Phase A CLOSED 6/6.** CI gained four oracles: JS syntax, asset bijection, per-vertical lifespan boot, widened mypy + two adopted hooks (**+74 s, no new dependency**). 🔴 **AC-3's own claim was MEASURED FALSE for the DEFAULT vertical** — the boot smoke misses a malformed spec on `energy`. 🔴 **Eleven inherited claims checked, EIGHT wrong.** | `de3295a` / [#1204](https://github.com/CrayJThiemsert/vero-lite/pull/1204) / `docs/plans/0107-*.md` |
| 2026-08-17 | **s235 — ADR-0038 RATIFIED (5 classes binding, 4 SDs ruled); `CLAUDE.md` BOUND with four new rules; 8 PRs (#1193–#1200).** 🔴 **The organising law:** a defect is visible only when an INSTRUMENT reads the artifact, the DATA reaches the failing state, and someone ARMED it as a gate. 🔴 **A live `main` defect fixed** (`deploy.py`'s dead compose path). ✅ §8's scenario rule is genuinely obeyed: 17 files, 0 violations. | `218a521` / [#1197](https://github.com/CrayJThiemsert/vero-lite/pull/1197) / [#1200](https://github.com/CrayJThiemsert/vero-lite/pull/1200) / `docs/adr/0038-*.md` |
| 2026-08-16 | **s234 — Step 10 EXECUTED under Cray's typed §8 go: fleet is LIVE as published system #3;** PLAN-0103 **11/11** and PLAN-0106 **7/7**, both COMPLETE, ARCHIVED. 🔴 **Cray drove the live surface and found Tab I clipping 305px of itself — a defect 4,113 green tests could not see, because CI has no JS runtime.** Fixed, guarded, REDEPLOYED under a second typed go. Pre-flight omissions, two false doc claims and every redeploy reading are in the log. | `027986e` / [#1190](https://github.com/CrayJThiemsert/vero-lite/pull/1190) / `docs/logs/2026-08-16-plan0103-step10-fleet-bring-up.md` |
| 2026-08-16 | **s233 — SEVEN PRs MERGED (#1180–#1187); AC-11's RoPA WRITTEN and ADOPTED, closing fleet's last gate.** Cray ruled **seven** times; every ruling is stamped on the RoPA itself. 🔴 **ADR-0037 OQ-3 had been RULED while its recorded Recommendation was still the OVERRULED option**, and three downstream artifacts inherited it. ⚠️ **The RoPA's authorship DEPARTS from D2.1**, disclosed on the artifact; **SD-1 is UNRULED and D2.1 as written still governs.** _[Label corrected s241: ADR-0037 has **no** SD-1 — the unruled item is its **D2.1 authorship fork**, `0037:229-249`.]_ | `3b9a084` / [#1184](https://github.com/CrayJThiemsert/vero-lite/pull/1184) / `docs/compliance/ropa-fleet-cases.md` |
| 2026-08-15 | **s232 — ELEVEN PRs MERGED (#1170–#1179); the "fleet blocks on ONE artifact" framing was REFUTED — 14 gates walked, TWO owned by nobody.** Six typed rulings folded. ✅ **PLAN-0106 then RULED, BUILT and MERGED — D2.4 DISCHARGED** — and Cloudflare + host secrets closed. 🔴 **Fleet's gate list is now ONE item, AC-11's RoPA.** | `5425822` / [#1178](https://github.com/CrayJThiemsert/vero-lite/pull/1178) / [#1179](https://github.com/CrayJThiemsert/vero-lite/pull/1179) / `docs/plans/done/0106-*.md` / `docs/logs/2026-08-15-fleet-cloudflare-*.md` |

_[The oldest row (s231) rotated to `docs/status-archive/2026-h1-status.md` this reconcile, holding the table at ten.]_

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

- [ ] **🆕 The four s235 audit findings ADR-0038 did NOT absorb — REHOMED s235 out of a gitignored handoff into `docs/logs/2026-08-17-s235-audit-findings-outside-adr-0038.md`.** The **retrieval-reliability ranking** · **"pruning never reclaims storage"** (so never argue a rotation on disk grounds) · **`docker build` in CI, rated YES and owned by no PLAN** · **the 11-class vacuity taxonomy**. 🔴 **One live obligation in there: ADR-0038's three-strike counter has NO OWNER** — three items sit at two firings and no artifact records a count. PLAN-0108 is the natural owner and does not claim it. _[s241, two labels. `was an error (naming only)`: **"ADR-0037 SD-1" does not exist** — the genuinely-unruled item is the **D2.1 authorship fork** (`0037:229-249`), still open. `superseded by new info`: the counter has DRIFTED — the s235 log names **three** items at two firings while **ADR-0038's own D4 names only TWO** (`0038:441-447` W-1/W-2); `#0042` was added by the s235 audit and D4 was never amended.]_
- [ ] **🆕 PLAN-0111 — the fleet close-out record that can hold a credit note (ใบลดหนี้): `Draft`, and all six SDs RULED in the same session** (Cray, typed 2026-08-19, [#1227](https://github.com/CrayJThiemsert/vero-lite/pull/1227)). **Cray ratified the SDs, not the PLAN; nothing gates execution.** 🔴 **SD-E (partial credits may coexist; over-credit refused 422) FORCES SD-A to (b), a separate `repair_case_credit_note` table** — a latest-per-kind row would re-arm the replacement trap one level down. ⚠️ **AV-1 is owed before Step 4, not before merge:** what Express/accounting reconciles a ใบลดหนี้ against is the one thing this repo cannot answer, and SD-C is provisional on it. The three code-verified obligations the rulings created (`_FK_CHILD_MODELS`, the `load_monthly_export` union, the AV-2 prohibition) are in the s240 Current Focus block above and in the PLAN. **Read the PLAN, never a restatement:** `docs/plans/0111-fleet-closeout-credit-note-record.md`.
- [ ] **PLAN-0107 — oracle-coverage hardening: `Draft`, 15 ACs. ✅ Phase A CLOSED 6/6 s236 ([#1204](https://github.com/CrayJThiemsert/vero-lite/pull/1204)); ✅ Phase B's AC-7 + AC-8 CLOSED s236 (#1206 `7a37c6d`, #1207 `5aedaf2`) and ✅ AC-11 CLOSED s240 ([#1226](https://github.com/CrayJThiemsert/vero-lite/pull/1226)). Tally **9/6**. Remaining: Phase B's AC-9 (BLOCKED on a Cray ruling) + AC-10, and Phase C — nothing else gates them.** CI now runs four oracles it lacked (**measured +74 s, no new dependency**). ⚠️ **Read each AC and its `Reviewer amendment` blocks as authoritative; the §Steps prose is narrative — three measured divergences in Phase A alone.** _[s241 — every defect this row named is now FIXED OR RECORDED IN THE PLAN ([#1232](https://github.com/CrayJThiemsert/vero-lite/pull/1232)): AC-11's checkbox ticked, AC-10's scope corrected to **nl-01…nl-11 (eleven)**, the expired 2-case-seed argument dropped in both places, three drifted citations re-anchored by symbol, and 🔴 **AC-9's Step-7 probe recorded UNRUNNABLE in a `Reviewer amendment` — three defects, three options laid out neutrally, BLOCKED pending a Cray ruling.** The PLAN carries the detail; do not restate it here.]_ **Read the PLAN, never a restatement:** `docs/plans/0107-oracle-coverage-hardening.md` (§Phase A closing evidence · §Acceptance Criteria · §AC-9's Reviewer amendment).
- [ ] **🆕 PLAN-0107's citation population is only PARTIALLY verified — recorded here because nothing else carries it.** The s241 sweep was exhaustive for **`verticals/fleet_maintenance/operate_seed.py` only** (three drifted cites re-anchored by symbol); asked directly, the drafter stated plainly it did **not** systematically check the rest, and named the at-risk set: AC-8's before-state cites into `tests/api/conftest.py`, the Phase A cites into `.github/workflows/ci.yml` (#1204 added ~5 steps to that file), and a tail into files no closed AC touched. 🔴 **The framing matters more than the count: most are BEFORE-STATE cites — historical by design, "wrong" only the way an archive is wrong** — so the likely treatment is **labelling them before-state, not re-anchoring them**, which makes this an **AC-authoring convention question (PLAN-0108's subject)**, not a repair job. **Recommendation on record; NOT ruled.**
- [ ] **🆕 PLAN-0108 — AC-authoring + pre-close convention hardening: `Draft`, UNRATIFIED.** The weak-oracle half of the same audit. 🔴 **Still gated, unchanged: SD-1 is NOT ruled — ROUTED to Cowork (`0108:209`; until it returns and is ratified, §8 as written governs); three of six ACs close only on Cray's PR-merge judge read; Step 1 is G2-gated for Code (`0108:240-242`).** _[s241: the two ACs both labelled `AC-5` are CORRECTED ([#1233](https://github.com/CrayJThiemsert/vero-lite/pull/1233)) — the `[evidence]` retro-classification AC is now **AC-6**; the `[check]` staleness-guard AC keeps **AC-5** because ADR-0038's OQ-5 attaches to it. ⚠️ **UNDECIDED, and live only here until ruled — the labels now read `[1, 5, 2, 3, 4, 6]`: unique but NOT ascending.** The AC-5 block is authored adjacent to AC-1's `measure` section and STATUS anchors it by line, so ordering them means physically moving the block — layout against a live citation, **Cray's call**; hook #19 checks collisions, not ordering, so nothing forces it.]_ Owns ADR-0038's **OQ-5** — the staleness-guard obligation attaches to the PLAN template, not to a build task. **Read the PLAN, never a restatement:** `docs/plans/0108-ac-authoring-and-preclose-convention-hardening.md`.
- [ ] **🆕 The two s241 pre-commit guards — BOTH ARE FLOORS, NOT CEILINGS; their limits are recorded here so neither is read as stronger than it is.** `tools/check_retired_claims.py` (hook #18; convention `docs/conventions/retired-claims.md`) — a claim declared retired must not survive anywhere live; it **cannot catch a reworded stale copy** (exact text only) and **cannot know a claim SHOULD have been retired**, so declaring stays a human act. `tools/check_ac_consistency.py` (hook #19) — no duplicate AC labels in an active PLAN, and a closure STATUS claims must be ticked in the PLAN; it **cannot read a phase-level claim** (*"Phase A CLOSED 6/6"* names no AC — three such claims exist), covers **active** PLANs only for duplicates, and cannot know whether an AC *should* be closed. ⚠️ Recorded so it is not rediscovered: `docs/plans/done/0042-at2-managerial-build.md` carries a duplicate `AC-13`, **deliberately out of scope** as frozen history.
- [ ] **🆕 PLAN-0109 (Ask over repair cases) carries THREE factual defects in its RULED content — measured s241, all zero-tracked-hits. Fix all three BEFORE Step 5; they are `docs/plans/` writes, so G2-gated for Code and owed to a drafter dispatch.** 🔴 **(i) AC-11 would write a FALSE sentence into the compliance record by deleting a TRUE one.** It orders the *"does not reach case text"* sentences deleted from `services/db/repair_case_retention.py:7-9` and `docs/compliance/ropa-change-statement-fleet.md:124-125` and replaced with a claim that case `description` / quote `vendor` / accepted-quote `reason` reach the `/query` translate + phrase prompts **and the D6 prompt log**. Measured: `services/engine/llm/prompt_log.py:26` `FIELDS` is a **CLOSED** 7-key set asserted at `:113`, and `services/api/routers/query.py:59` passes `text=request.question` only — so case text reaches the **phrase prompt only** (`nl_query.py:1220-1221`), **not** the translate prompt (schema-only, `:382-398`) and **not** the on-disk log. The deleted sentences stay TRUE after PLAN-0109 ships, and AC-11's grep pass read (*zero occurrences*) **cannot fail** — it is satisfied by deleting a truth. 🔴 **(ii) `tenant_id` is missing from the exclusion enumeration and reddens AC-3 on the first run** — a live column on all three ruled types via `TenantKeyMixin` (`services/db/tenant.py:71`), and it may **NOT** be moved into the YAML (`tests/services/engine/test_tenant_key_not_in_nl_query.py:70` reddens instead). **(iii)** minor: **AC-3(iii) contradicts AC-10 on `seq`** — neither `RepairCase` nor `RepairCaseQuote` has a `seq` column, so a flat exclusion entry is stale for two of three types. **Read the PLAN, never a restatement:** `docs/plans/0109-*.md`.
- [x] **PLAN-0106 — fleet's own in-app case-persistence disclosure (ADR-0037 D2.4): COMPLETE 7/7, marked Complete by Cray (typed) and ARCHIVED s234.** AC-7's ordering clause closed on fleet's Step-10 go record, which cites this PLAN by number. **No live residual.** **Read the archived PLAN, never a restatement:** `docs/plans/done/0106-fleet-case-persistence-disclosure.md` (§Closure evidence · §Surfaced decisions).
- [ ] **TWO unruled silent drops in the NL engine's aggregate paths — REHOMED s235 to the code.** (i) the **`started_week` filter is ignored entirely** (found s228) and (ii) **`group_by` never reaches `AggregateResult`**, so *"average duration per procedure"* validates, executes and silently returns **one ungrouped number** (found s232). Both live at `_aggregate_duration` / `_aggregate_benefit`; ⚠️ **the count path DOES pass `groups`**, so (ii) is a two-site gap in an otherwise-correct design, not a missing feature. **No test covers either.** **Read the docstring, never a restatement:** `services/engine/run_query.py::_aggregate_duration`. **Same two dispositions each, NEITHER ruled: (a) refuse, or (b) make it work.**
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
