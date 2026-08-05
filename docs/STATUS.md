---
last_updated: 2026-08-05T21:17:52+07:00
session: 207
current_batch: "s207 — #1049 merged: Cray's five PLAN-0100 SD rulings recorded (AC-13 CLOSED), C-3 folded in, two of the PLAN's own claims retracted by R2. #1046/#1047/#1048 landed in the s206 tail."
current_actor: code
blocked_on: "PLAN-0100 Step 8 is blocked on the D4/L5 ADR-0035 amendment being routed and ratified; Step 9 on Step 8, and Step 9's arm-posture case on OI-1. Steps 3 and 4 are RELEASED."
next_action: "Cray decides three: (1) per-IP threshold (Code raised 2→10 req/10s, flagged), (2) OI-1's options, (3) the D4/L5 amendment — (3) blocks Step 8. Step 4 DONE; Step 3 next, ungated."
head_commit: 5621266
recent_commits: [5621266, ab57814, 36221a8, b045adf, 9e4427c, d865b75, c96c2c8, ee71736, 405e9d6, 0c9348a]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

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

> **Session 205, 2026-08-04 (head_commit `22202f2` → `bcab1f4`) — three PRs merged
> (#1031–#1033), all s205's own work. Theme:
> answering an overdue question corrected two errors in the record it was built on.**
>
> _[Three PARALLEL-session PRs — **#1034, #1035, #1036 — also landed in this window and
> are NOT s205's work**: #1034 from the chip session s205 spawned, #1035 and #1036 from
> one other session. They carry head to `bcab1f4` and alembic head to **`0025`**; their
> authors wrote the record, and **Recent Decisions** below carries all three.]_
>
> **OQ-4 CLOSED — Cray typed RETIRE L1 (2026-08-04); PLAN-0102 is the vehicle (#1031).**
> Re-measured over **130** transcripts keyed on **structural hook-emission paths**, not
> substring, with a **positive control that passed 3/3** — a zero was pre-committed as
> unreportable unless the method first re-found three known-present warns. **True
> positives = 0 in both eras.** Post-AC-7: **0 denies, 0 organic warns** (the lone warn
> was an induced self-test), so the "≥ 1 false positive" arm could not fire: the literal
> criterion is **unfireable by construction** — AC-7 left the guard inert, and a detector
> that never fires cannot produce the false positive its own retirement trigger requires.
>
> **Running it corrected two errors in the record it was built on.** (1) The s180
> baseline's **"0 denies" was wrong — ≥ 56 measured** over 19 days / 4,201 Write-Edit ops
> (**~1.33 %** of all edits hard-walled), and that is a **floor** — 30-day retention had
> already deleted 06-27 → 07-04 of the baseline's own span. Root cause: **three** deny
> wordings existed, not two — lesson 0012 quotes `in this **session**` while every live
> emission says `in this **turn**`, so s180 searched for a string no transcript contains;
> its warn count (3) was right because that string came from the hook source. Classified
> **was an error**, not superseded (§6). (2) The criterion's **prescribed remedy was
> mis-premised**: it called for an ADR-013 amendment, but `0013:90` states trigger E.4 as
> "the same *problem*" and never names L1, and `0013:333-336` delegates stateful
> loop-detection to PLAN-0008+. **L1 has zero ADR backing ⇒ no amendment**; PLAN-0102 is
> the governance record, on the PLAN-0092 precedent. Method + the four traps that nearly
> skewed it: `docs/lessons/0035-negative-measurement-needs-a-positive-control.md`.
>
> **PLAN-0100's fold-in (#1032) makes SD-1..SD-5 askable.** Five empty `Ruling:` slots +
> **AC-13** (the adjudication record) + BLOCKED-ON-SD markers; the H/I/J inconsistency
> reconciled by **dropping Tab H from SD-1's promise** — its backend is **mixed**, not
> DB-posture-contingent; `54dfc7d`'s measurement table folded in **verbatim** (dev half
> discharged, published half open); SD-4 restated **published-profile-only**.
>
> **The archive relocation (#1033) found its own recorded blocker false.** Three misfiled
> s196/s197 Recent-Decisions rows moved `h1g` → base. The Current-Focus chain split the
> move was said to depend on is a **separate corpus**, and the rotation base had ~109 KB
> of headroom throughout — the dependency never existed.

> **Session 204, 2026-08-04 (head_commit `592124b` → `22202f2`) — three PRs merged
> (#1026–#1028), one open (#1029, CI green, awaiting merge). Theme: the ADR-0035 D7
> tenant key lands end to end, and a remedy stated in halves fabricated a green run.**
>
> **PLAN-0101 Steps 2–6 COMPLETE, 12/12 ACs, ARCHIVED (#1028/#1029).** 21 tables carry
> `tenant_id`; all **12** uniques re-scoped (unscoped **0**, anonymous **0**, read from
> the **built SQLAlchemy metadata**, not source text); revision `0024` = 21 tables ×
> three phases + 12 drop/recreates, downgrade proven by *running* it. **Two consequences
> SD-3's riders never named, both found by the work, not by review:** a composite FK
> **must move with its widened target** (Postgres demands an exact match — **335 suite
> errors from one root**), and audit-chain scoping is **four** sites, not the two Cray's
> call named, because `append_audit`'s head lookup is a **correctness requirement** of
> the widened constraint. Closeout: `docs/plans/done/0101-tenant-key-column.md`.
>
> **Four Cray calls reshaped it mid-flight** (attributed in the PLAN): unbind SD-2's
> letter once AC-10's negative guard proved undischargeable; name the real worry — a
> future LLM over ontology data sweeping tenants; a **synthetic second-tenant fixture**
> not a real second customer; **SD-3 rider 3 reversed** to scope the audit reads here.
>
> **That worry got a measured answer that INVERTS the intuition.** The NL-query path never
> writes SQL (**0** raw-SQL execution sites in `services/`) and `_validate_query` checks
> every filter property against the ontology's property list — **the ontology is the
> allowlist of what a model may name**: `tenant_id` **in** makes cross-tenant selection
> *expressible*, **out** keeps it inexpressible (AC-11 asserts it). Nor is the fixture
> convenience — under one tenant the twelve re-scopes are a **100% behavioural no-op**, so
> the second tenant is the positive control for Cray's own ruling.
>
> **Banked:** a planted `server_default`, read against both oracles in one run, turned
> `test_tenant_key_migration.py` **RED** while `alembic check` stayed **GREEN at exit 0**
> — SD-1(b)'s "no `server_default`" is **provably invisible** to the tool that looks like
> it should catch it. **Read-site census: 50** raw `select(` hits over **16** files in
> `services/`, UNCLASSIFIED — not a bug today (one deployment = one DB = one tenant); four
> are now tenant-scoped, the rest owed to a future multi-tenant ADR, AC-12(iii) records them.
>
> **An unplanned harness-hygiene detour (#1026/#1027).** A pytest run reported `EXIT=0`
> with two tests RED. The remedy has **two required halves** — a SINGLE-quoted outer
> argument **and** `\$` for every `$` — compressed to **one half in three places at once**:
> the memory index, the hook advisory, `CLAUDE.md` §8. Code followed it literally, kept
> double quotes, read a **fabricated zero**, and came within one step of an unnecessary
> constitutional amendment; only the pytest summary three lines below contradicted it.
> **§8 and lesson 0007 §1.1 were correct throughout — only the enforcement was half-built.**
> Recorded: *a two-half remedy stated as one half is worse than stating neither* —
> `docs/lessons/0007-harness-exit-code-artifact.md` §6.1.
>
> Final gate: `tests/` **3817 passed / 0 failed / 8 skipped**, `mypy --strict` clean over
> **131** files, `ruff` + `alembic check` clean, CI `gate` 5m41s. **7 non-vacuity probes,
> every RED observed**, restored from `/tmp`, never `git checkout`.

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
| 2026-08-05 | **s207 — Cray ruled all five PLAN-0100 SDs (#1049): AC-13 CLOSED, every BLOCKED-ON-SD marker RELEASED.** SD-1 (a) DB-less · SD-2 exclude the three draft routes · **SD-3 (ii) `cloudflared` — ADR-0035 never names nginx** · SD-4 (a) · SD-5 keep both. ⚠️ The R2 pass found **C-3: four allowed routes need a DB and there is NO global exception handler ⇒ unhandled 500, not degrade** — Approve succeeds, **Execute 500s**. Two of the PLAN's own claims retracted: `GET /recommendations` is **LLM-backed** (⇒ **OI-1**); ~14 `api.js` cites stale by **+7**. **Steps 3/4 free; Step 8 gated on a D4/L5 ADR-0035 amendment** | `5621266` (head_commit) / [#1049](https://github.com/CrayJThiemsert/vero-lite/pull/1049) / `docs/plans/0100-exposure-published-demo-surface.md` |
| 2026-08-05 | **s206 tail — PLAN-0100 Step 10 shipped and two lessons landed (#1046, #1048).** #1046 creates `docs/compliance/` (the RoPA instance, written in Cray's voice as controller) + `docs/runbooks/published-demo-operations.md`. #1048 adds lessons **0036** (the tiebreak pairing) and **0037** (the three-axis blind spot). **#1047** also merged in this window and is **not characterised in this record**. All three landed after STATUS was last written, so the s206 row below does not carry them | `d865b75` ([#1046](https://github.com/CrayJThiemsert/vero-lite/pull/1046)) / `b045adf` ([#1048](https://github.com/CrayJThiemsert/vero-lite/pull/1048)) / `docs/runbooks/published-demo-operations.md` |
| 2026-08-05 | **s206 — PLAN-0102's scope was three gaps short of safe, and one would have BRICKED the harness (#1040).** The `awaiting_ack` subsystem was entirely unscoped while Step 5 deleted one of its dependencies ⇒ `ImportError` at module load that **no `try/except` catches**, taking chain-cap + classifier + auto-handoff with it; Steps 3/5 contradicted each other over `_apply_commit_reset`, whose `AttributeError` is **swallowed** ⇒ L2/L3/L4 stop persisting at exit 0. Root cause for all three: **none of the missed identifiers carries an `L1`/`loop` token**, so a name-keyed census cannot see them. **AC-11** added — ACs 1–10 would have passed over a bricked harness. Separately **#1041** closed the unowned wall-clock intermittent: **one clock sampled twice**, not two clocks; a planted 1-second defect now reddens where the old bracket could not | `e5d163d` ([#1040](https://github.com/CrayJThiemsert/vero-lite/pull/1040)) / `3b9d9c4` ([#1041](https://github.com/CrayJThiemsert/vero-lite/pull/1041)) / `docs/plans/0102-retire-l1-loop-detect.md` |
| 2026-08-05 | **s206 — PLAN-0100's SD-free slice SHIPPED ENTIRE (#1042–#1045); "execution gated on SD-1..SD-5" was shorthand, not the PLAN's rule.** Step 1 census, Step 2 `ui_profile`, Steps 6–7 in-flight cap + prompt log, Step 5 D6 banner — all six SD-free items, none gated. **Cray chose server-injection for the boot seam; the carrier changed `<script>` → `<meta>`** because `_OCT_CSP` pins `script-src 'self'` and an inline script is **silently blocked** ⇒ fallback to the FULL console. ⚠️ The census found **`/whoami` default-denied**, which makes the published demo **unloginable** — the PLAN's keyed-routes argument rested on a route the same section denied. **Only SD-gated steps 3/4/8/9 remain** | `296cc34` (head_commit) / [#1042](https://github.com/CrayJThiemsert/vero-lite/pull/1042) / [#1043](https://github.com/CrayJThiemsert/vero-lite/pull/1043) / [#1044](https://github.com/CrayJThiemsert/vero-lite/pull/1044) / [#1045](https://github.com/CrayJThiemsert/vero-lite/pull/1045) / `docs/plans/0100-exposure-published-demo-surface.md` |
| 2026-08-04 | **#1034 (chip-authored, NOT s205) — `/api/cases` list order is now REPEATABLE, not newest-first.** A `case_id` tiebreak on `opened_at.desc()` ends cross-refresh flicker at the `limit` boundary, but `case_id` is a **random UUID**: it buys **repeatability, NOT newest-first correctness — 50.5 % over 20,000 reps**. True order needs a monotonic `seq`, which PLAN-0099 §Coverage had already weighed here and **KNOWINGLY LEFT (ledger #7)**; **Cray ratified keeping that** — same `uuid4`-tiebreak trap as #1035, opposite right answers (display list ⇒ leave it, correctness path ⇒ `seq`) | `bcab1f4` ([#1034](https://github.com/CrayJThiemsert/vero-lite/pull/1034)) / `services/api/routers/cases.py:272` / `docs/plans/done/0099-wall-clock-root-fix-store-at-write-and-sequence.md` |
| 2026-08-04 | **#1035 (parallel session, NOT s205) — task-chain state re-keyed onto a DB-assigned monotonic `seq`; alembic head is now `0025`.** `chain_state` sorted flips on `at`, a wall-clock stamp, so a backward clock step let the **superseded** flip win; the `event_id` tiebreak never fired because `at` led the sort (and it is a `uuid4` anyway). It feeds `stale_items` → the LINE nudge sweep, so **both directions were live failures**: a finished step nudged forever, a reopened one silently un-chased. PLAN-0099 D2; `(tenant_id, seq)` unique per PLAN-0101 SD-3 | `3b07c16` ([#1035](https://github.com/CrayJThiemsert/vero-lite/pull/1035)) / `verticals/fleet_maintenance/task_chain.py` + `services/api/routers/cases.py:305` / alembic `0025` |
| 2026-08-04 | **#1036 (parallel session, NOT s205) — `0024` could not migrate a POPULATED `audit_log`.** Its backfill `UPDATE` trips `0007`'s `audit_log_no_mutation` **FOR EACH ROW** trigger; CI was green only because every fixture built an **empty** DB where a row trigger never fires — **a test that could not fail, not a flaky one**. Amended (**Cray-ratified** exception to never-edit-a-shipped-revision — nothing later can rescue a migration that blocks the chain) to a transient `ADD COLUMN … NOT NULL DEFAULT` + `DROP DEFAULT`: no `UPDATE`, so append-only never lapses. Dev DB `0022`→`0025`, 136 rows intact | `d86bb1d` (#1036) / `docs/plans/done/0101-tenant-key-column.md` |
| 2026-08-04 | **s205 — OQ-4 ANSWERED: NO; Cray typed RETIRE L1 (#1031).** 130 transcripts, structural hook paths not substring, **positive control 3/3**, true positives **0** in both eras ⇒ the criterion is **unfireable by construction**. Two corrections to the record it was built on: s180's "0 denies" was **wrong — ≥ 56 measured** (a floor; three deny wordings existed, not two), and **ADR-013 never backed L1** ⇒ no amendment, **PLAN-0102** is the vehicle | `74b6a94` (#1031) / `docs/lessons/0035-negative-measurement-needs-a-positive-control.md` |
| 2026-08-04 | **s205 — PLAN-0100 fold-in (#1032) + archive relocation (#1033).** Five empty `Ruling:` slots + **AC-13** + BLOCKED-ON-SD markers make SD-1..SD-5 **askable**; H/I/J reconciled by **dropping Tab H from SD-1's promise** (mixed backend, not DB-posture-contingent); `54dfc7d`'s table folded in verbatim; SD-4 is **published-profile-only**. #1033 moved three misfiled s196/s197 rows `h1g` → base — the recorded blocker was **false** | `27a6961` (head_commit) / `734feae` / `da633a1` / `docs/plans/0100-exposure-published-demo-surface.md` |
| 2026-08-04 | **s204 — PLAN-0101 COMPLETE 12/12 and ARCHIVED (#1028/#1029): the ADR-0035 D7 tenant key, end to end.** 21 tables carry `tenant_id`, all **12** uniques re-scoped (read from built metadata, not source text), revision `0024` with a symmetric downgrade. **Cray typed four calls** — unbind SD-2's letter, a **synthetic second-tenant fixture**, **SD-3 rider 3 reversed** to scope the audit reads. Two consequences the riders never named: a composite FK must move with its widened target (**335 errors, one root**), and audit scoping is **four** sites. Suite **3817 / 0 / 8** | `22202f2` (head_commit) / [#1028](https://github.com/CrayJThiemsert/vero-lite/pull/1028) / `docs/plans/done/0101-tenant-key-column.md` |

## In-Flight Discussions

- **PLAN-0096 — COMPLETE 12/12 and ARCHIVED (s193).** The fleet design partner's Phase-1 flow, shipped end to end across s186→s193 — real governance numbers, case capture from minute 1, the quote evidence pack, the sourcing signal that retired a fail-open default, the E-2 ratification window, the PM import, the outbound-only-and-DISARMED LINE OA surface, the 8-step task chain, and the month-end Express export. **Four residual risks outlive the PLAN and are why this entry is not simply deleted — all four are recorded in the archived PLAN, which is where the detail now lives:** RR-1 (per-baht approver→case attribution is INFERENCE, not data — `GovernedDecision` carries no timestamp and no per-entity key; sound while one human resolves a whole gate, silently wrong the day two approvers share a resolution); RR-3 (concurrency-race was the weakest coverage row for AC-4/AC-9/AC-10 — **both named gaps CLOSED s195 by #995**: the PM-confirm race turned out to be a REAL defect, now `FOR UPDATE`, and `allocate_repair_order_no` got the test its docstring implied, which corrected the constraint that docstring named); ศูนย์ต้นทุน ships EMPTY (partner granularity still unanswered — also an open Active TODO below); and `latest_per` still collapsing two open cases on one truck (item 4, **Cray typed (ค) defer**) — the older case never reaches the gate, so if it is paid it reports as *ungoverned*, which a reader of the number cannot distinguish from a governance failure. Full record: `docs/plans/done/0096-fleet-flow-completion-phase1.md` (§Verification preamble + §Acceptance Criteria for RR-1 / RR-3 / ศูนย์ต้นทุน; §Step 8 for `latest_per`); the AC-12 sign-off is in `.claude/handoffs/session-193/` (gitignored).
- **PLAN-0095 — COMPLETE 7/7 and ARCHIVED (s177, #927/#928).** The scaffold-era `Dockerfile` builds and boots the DB-less synthetic OCT demo: `/health` 200 in ~2 s, all six verticals discovered, `uid=999(vero)`, `HEALTHCHECK` healthy, and `alembic current` → `0012 (head)` from inside the image. **OQ-1, the hosting model — the last thing open from it — is now CLOSED**, answered by **ADR-0035** (Accepted s200; its D2 pointer amendments completed s202, #1014); the exposure work it opened lives in PLAN-0100, not here. Full record: `docs/plans/done/0095-docker-image-boot.md`. _[Corrected s182, `was an error`: this entry still described the PLAN as Draft with "Steps 1–5 UNEXECUTED … the image does not boot today" and cited the pre-archive path — refuted by the s177 row in Recent Decisions above and by the archived PLAN's own `Status: Complete`.]_
- **PLAN-0094 — COMPLETE (all 11 ACs closed or withdrawn) and ARCHIVED (s183).** The L1 loop-detect restructure: count non-progress instead of touches (P1), warn at `T` and deny at `T+G` (P2, `G=3` → 9 code / 18 doc), add an acknowledged-pause exit the agent cannot fake (P3), and wire the `SubagentStop` reset that had **never been live**, scoped per-`agent_id` so a zero-edit spawn cannot launder the main agent's budget (F3c). Built across s174 #917, s175 #922, s177 #930, s180 #937/#939, closed out s182 #943 on a **full fresh 18/18 non-vacuity sweep**. Archived at s183 once **Cray released the live-loop soak** (no anomalies) — the one gate no session could self-serve. **The one thing that did NOT archive with it: `OQ-4` (should L1 exist at all?) was re-homed to an Active TODO below**, per the PLAN's own §Step 6 instruction never to bury it in `done/` — **and is now ANSWERED s205: NO. Cray typed RETIRE; PLAN-0102 is the vehicle. Read that row, not this line.** Full record: `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md`; the anti-pattern behind it: `docs/lessons/0033-raising-the-threshold-is-not-fixing-the-unit.md`.
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

- [x] **MS-S1 hosting/exposure ADR — DISCHARGED. ADR-0035 Accepted s200; its D2 pointer amendments COMPLETE s202 (#1014).** PLAN-0095's OQ-1 is answered, and the ADR-002 / ADR-0003 pointers deferred twice as an unnumbered `ADR-NN` now exist. **Read the ADR, never a restatement here** — including its **nine currency notes**: the Cloudflare Tunnel is **not running today**. `docs/adr/0035-hosting-and-exposure-model.md`.

- [ ] **PLAN-0100 — the ADR-0035 exposure PLAN. DRAFTED s202 (#1017): `Status: Draft`, 12 ACs, 6 phases. EXECUTION IS GATED on Cray ruling SD-1..SD-5.** **SD-1 is load-bearing** — the published deployment's DB posture, (a) DB-less vs (b) synthetic Postgres — because it decides which tabs the published profile registers and every allowlist row hangs off it. Per **Cray's s202 ruling** the PLAN absorbs the UI work D5(2) implies, and it carries the **published-profile half of the nav-bar work as AC-3**. _[s203: Phase 0 Step 1 has **no `Ruling:` slot** — PLAN-0101 carries one under every SD from the start — so Phase 0 must *author* the adjudication record rather than fill it; and its AC-3 measurement table currently lives only in a commit body.]_ _[s204: **SD-4's published half is not answerable as written** — it turns on a published `UI_PROFILE` that exists **only inside this PLAN** (0 occurrences anywhere else in the repo), so the profile must be built, or SD-4 re-scoped, before a ruling on it can mean anything. Fold this in with the s203 findings before the SD round goes to Cray.]_ _[s205: **the fold-in SHIPPED (#1032) and the s203/s204 findings above are DISCHARGED** — the PLAN now carries five empty `Ruling:` slots, **AC-13** (the adjudication record), BLOCKED-ON-SD markers, and `54dfc7d`'s measurement table verbatim; **Tab H was dropped from SD-1's promise** (mixed backend, not DB-posture-contingent). All that remains is Cray filling the five slots.]_ _[s206: **the row's own headline "EXECUTION IS GATED on Cray ruling SD-1..SD-5" was shorthand, and reading it literally cost a session's worth of unblocked work** — the PLAN gates only steps carrying a BLOCKED-ON-SD marker, and **six items carried none**. All six now SHIPPED (#1042–#1045): Step 1's census, Step 2's `ui_profile` + its two delivery seams, Steps 6–7's in-flight cap + prompt log, Step 5's D6 banner, Step 10's RoPA + runbook (**#1046 open — Cray asked to read it before merge**). **What is genuinely gated: Steps 3, 4, 8, 9 only**, and the gate is **all-or-nothing** — ruling one SD unblocks nothing, so the five want one sitting. ⚠️ Two calls surfaced by the build and left for Cray inside merged PRs: **`llm_max_inflight`'s dev default** (shipped **0**/uncapped, read as a published posture like `PROMPT_LOG_ENABLED`; if 1-everywhere was meant it is one line) and **whether published Tab A should render run markers** (`GET /runs` is default-denied, Tab A degrades to zero flags by design — deliberately NOT raised as a sixth SD, since the safe default already ships and a sixth slot would block five ruled steps on a cosmetic one).]_ _[s207: **ALL FIVE SDs RULED (Cray, typed 2026-08-05) — AC-13 CLOSED, every BLOCKED-ON-SD marker RELEASED, and #1046 merged**, so this row's "EXECUTION IS GATED" headline and its `#1046 open` note are both history. SD-1 (a) DB-less · SD-2 exclude the three draft routes · SD-3 (ii) `cloudflared`, **no nginx** · SD-4 (a) · SD-5 keep both. **Steps 3 and 4 are free.** What is gated NOW: **Step 8 on a D4/L5 ADR-0035 amendment** (the ADR assigns the connector + ingress map to the portal repo), Step 9 on Step 8, and Step 9's arm-posture case on **OI-1** (`GET /recommendations` is LLM-backed, neither rate-capped nor prompt-logged). Also live: finding **C-3** — four allowed routes need a DB the ruled posture does not provide, and there is no global exception handler, so they 500. Detail is in the PLAN (#1049).]_ `docs/plans/0100-exposure-published-demo-surface.md`.
- [x] **PLAN-0101 — the ADR-0035 D7 tenant-key column. COMPLETE and ARCHIVED (s204).** Drafted s203 (#1021), Step 1 shipped (#1022), SD-1..SD-3 ruled by Cray (#1025), Steps 2–6 shipped as one PR (#1028 — CI forces them together: an ORM carrying `tenant_id` without revision `0024` reddens on autogenerate drift). All **12** ACs closed; 21 tables carry the key, all 12 unique constraints re-scoped, revision `0024` with a symmetric downgrade. Two consequences the SD-3 riders had not named surfaced during the build and are recorded in the PLAN's closeout: a **composite FK must move with its widened target** (335 suite errors, one root), and the audit-chain scoping is **four** sites rather than the two Cray's call named — `append_audit`'s head lookup is a correctness requirement of the widened constraint, not optional hardening. `docs/plans/done/0101-tenant-key-column.md`.

- [x] **ADR-0032's Context snapshot RE-GROUNDED — DONE s202 (#1015), third pass.** Discharges the OWED debt created when Cray ruled **D2's pilot gate SATISFIED** at s197. `docs/adr/0032-strategic-frame-demo-to-pilot-wedge-and-3-shape-roadmap.md`.
- [ ] **Assembly-cost axis — MEASURE it before an ADR argues it (Cray typed s197); nothing built, no PLAN drafted.** Build the tripwire that puts a number on assembly cost first, *then* draft the ADR on top of that number — the ordering is the ruling. **The series measured so far is banked HERE because it is banked NOWHERE ELSE in the repo — no test, no doc, no PLAN holds it:** churn per vertical went **1:1.8 → 1:6 → 1:1.1**, i.e. **spiky, not falling**, which is the shape any ADR on this axis has to argue against. Left unbanked it survives only in session memory and dies at the next context reset; a tripwire that recomputes it is what makes it evidence rather than a recollection.
- [x] **`CLAUDE.md` §3 named the code generator as the moat — CORRECTED s202 (#1020), Cowork-drafted per §6 convention.** §3 now leads with ADR-0032 D6's `monitor→decide→approve→act` identity and names the runtime procedure spine as the primitive; codegen is **rescoped, not denied** (only `energy` + `core` emit committed code). `docs/conventions/glossary.md` moved with it. _[Corrected s202, `was an error` — the batched-in "§1's 'SME' wording" half **HAS NO REFERENT and is struck**: `SME` has never existed in `CLAUDE.md`, and §1 reads "2 **enterprise** design partners". Cray's actual s197 point needs no edit; scope is §3 alone.]_ _[Flipped `[x]` s203 — #1020 had discharged it in the same session. The same stale "other five" figure had propagated into **three** `code_generator.py` comments, all fixed in #1023: one → "six", the two artifact sites de-numbered because the count is namespace-dependent.]_
- [x] **The OCT console's global nav bar overflowed its own viewport — FIXED for the dev profile s202 (#1018).** Root cause was **not** the header's content but its ladder: `theme.css`'s breakpoints were written for a **five**-tab header while `app.js` registers **ten** — natural width **2253 px**, so the collapse threshold moves `1360px` → `2299px`, verified **0 overflow** at 1280–2400. Two Python geometry tripwires, both probe-proven RED (`docs/conventions/ui.md`: no build step, so a UI tripwire must be a Python test). **The published-profile half remains OPEN as PLAN-0100 AC-3.**
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
- [x] **OQ-4 — does L1 loop-detect earn its keep? ANSWERED s205: NO. Cray typed RETIRE (2026-08-04).** Re-measure over 130 transcripts (2026-07-05 → 08-04), keyed on structural hook-emission paths rather than substring, **positive control 3/3** (re-found the baseline's three warns — a zero was not reportable without it). **True positives = 0 in both eras.** Post-AC-7 window — 8 days, 31 transcripts, **1,369 Write/Edit ops** — **0 denies, 0 organic warns**; the lone warn was an induced self-test (`l1_livecheck.py`), so the "≥ 1 false positive" arm could not fire and the literal criterion proved **unfireable by construction** — AC-7 left the guard inert, and a detector that never fires can never produce the false positive its own retirement trigger requires. ⚠️ **The s180 baseline's "0 denies" was WRONG — ≥ 56 measured** over 19 days / 4,201 edits (**1.33 %** of all edits hard-walled), and that is a **floor** (retention deleted 06-27 → 07-04). Root cause: **three** deny wordings existed, not two — lesson 0012 quotes `in this **session**`, every live emission says `in this **turn**`. Classified **was an error**, not superseded (§6). ⚠️ The prescribed remedy was mis-premised too: **ADR-013 never backed L1** (`0013:90` states E.4 as "the same *problem*"; `0013:333-336` delegates "stateful loop-detection" to PLAN-0008+), so **no ADR amendment** — the vehicle is **PLAN-0102**, on the PLAN-0092 precedent ("zero ADR backing"). E.4 survives via L2/L3/L4, which key on the *problem* not the *file*. Method + the four traps that nearly skewed it: [`docs/lessons/0035-negative-measurement-needs-a-positive-control.md`](docs/lessons/0035-negative-measurement-needs-a-positive-control.md).
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
