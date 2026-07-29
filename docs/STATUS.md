---
last_updated: 2026-07-29T19:30:00+07:00
session: 189
current_batch: "s189 — PLAN-0096 Steps 6 (#965) + pm_due (#968) shipped on the partner's round-2 answers → Steps 1-7 and 9 COMPLETE (8 of 10); unplanned ORM/alembic registration guard + lockstep test (#966, #967)."
current_actor: code
blocked_on: "Nothing blocks the build — PLAN-0096 Step 8 is unblocked (A2 answered). One NON-blocking follow-up: cost-center granularity (per truck or per company?) — ship the column, fill the rule when it lands."
next_action: "PLAN-0096 Step 8 (month-end Express-shaped export + KPI), then Step 10 (AC-12 confidence sign-off)."
head_commit: 13aa2f0
recent_commits: [13aa2f0, b1630f2, 430cf39, 221f9e7, e54cbe8, 2809e0d, 26e61b3, d0f31a7, 736ae84, 98744bd]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

> **Session 189, 2026-07-29 (head_commit `be7d386` → `13aa2f0`) — the session
> the fleet partner's round-2 answers landed and PLAN-0096 stopped being
> blocked. Four PRs merged (#965–#968), 0 open: **Steps 1–7 and 9 COMPLETE (8
> of 10)**. **Five of the seven questions are closed:** A1 built Step 6, A3
> built `pm_due`, and **A4 + A7 confirmed values that had already shipped** — a
> flat ฿5,000 ceiling for every truck initially, so the authored `5001` default
> stands and the per-truck "stretch values" sub-task is **eliminated, not
> deferred** (those values do not exist yet); and 99% whole-baht quoting,
> ฿30,000 exactly = no comparison / ฿30,001+ = comparison required, confirming
> the shipped `"30001"` inclusive floors and closing the satang de-minimis
> intake note. **A2 is answered, so Step 8 is unblocked rather than blocked** —
> the only question with build left. A5 is **parked** (no real Wialon export
> exists yet, and the partner wants an admin-mapped remembered column mapping,
> so the Step 9 importer stays fixed-column); A6 is a Step 9 *runbook* item,
> not code. **Nothing blocks the build.**
>
> **Step 6 (#965) — the partner's chain, not ours.** A1 superseded the PLAN's
> guessed four-item checklist: the real chain is **8 steps, 4 mandatory + 4
> conditional**, each carrying its **own** "ถ้าค้างเกิน" threshold rather than
> one shared timeout — two of them context-dependent (แจ้งอู่ 30 min on a
> breakdown / 1 day on PM; รออะไหล่ 2 days general / 5 days major part), and
> เริ่มซ่อม anchored to parts-complete ("1 วันหลังของครบ"). Shipped as a
> fleet-side **authored config** (`verticals/fleet_maintenance/task_chain.py`);
> the partner's suggested partner-editable template system was **declined for
> Phase 1** per ADR-006's Rule of Three. Storage is an **append-only**
> `repair_case_task_event` trail plus `repair_case.work_type` (alembic
> **0016**), so AC-7's "actor + timestamp per flip" is the storage model rather
> than logging bolted onto mutable state; that one `work_type` field serves
> both these context SLAs and Step 8's ประเภทงาน export column. Plus the
> staleness sweep into the existing `task_chain_stale` LINE event and
> `POST|GET /api/cases/{case_id}/tasks`, whose GET takes an optional `as_of`
> that Step 8's period-close export needs.
>
> **The anchor rule — Cray typed it, of three options weighed.** A step with
> prerequisites starts its clock when the prerequisites **this case actually
> has** are settled; counting from the item's own activation would have nudged
> เมย์ about starting a repair from day two of an *authorised* five-day
> major-part wait — against a partner whose own stated failure mode is
> *"ผมไม่อยากให้ทุกอย่างเด้งเข้ากลุ่มเดียว เดี๋ยวคนปิดแจ้งเตือนหมด"*, with exactly
> one outbound channel to spend.
>
> **`pm_due` (#968) — a sixth LINE event, admitted on evidence.** A3 supplied
> the two things `LineEvent`'s closed-set docstring demanded before a sixth
> member could exist — a named producer and a named recipient rule — so Cray
> amended AC-8 from five events to six. The recipient is a **group** (กลุ่มช่าง),
> not a person, by the partner's choice, and it is **one message per round**
> listing the due plates, not one push per truck. The producer reads the due
> set off the **persisted `judge_service_due` verdicts of the run that just
> fired** — never re-deriving "due" from odometers, because a second
> implementation of that comparison could disagree with the one the governed
> run acted on and the message would name a different set than the screen the
> human approves. Keyed to a run id, so a truck is announced once per round.
> The scheduler daemon holds no vertical knowledge by design, so it gained an
> **injected `on_fired` hook**, and `services/engine/cli.py` resolves the fleet
> producer as that hook — the same hand-wired shape as the executor factories.
>
> **The unplanned thread (#966 + #967) — the session's most transferable
> finding.** #965's CI failed at 54 s on the `alembic check` lockstep guard:
> `alembic/env.py` never imported the new ORM module, so `Base.metadata` did
> not know the table existed and autogenerate wanted to **DROP** it. **3528
> passing tests could not see it** — `create_all` knows only what the
> *importing test module* pulled in, and nothing offline traverses `env.py`.
> #966 built an offline AST-based guard for that class. Then Cray asked whether
> `alembic check` really needs a live DB, or whether we could run it and see
> what was hiding. **Probing instead of reasoning did three things:** it
> **refuted the premise** of Code's earlier answer (no *dev* DB needed — the
> disposable per-checkout test DB works, measured at **1.75 s** total); it
> found a **live drift**, since #965's own fix had patched `env.py` only and
> left `tests/db_support.py` — the second registration site, whose comment says
> "keep in lockstep with alembic/env.py" — missing the same module; and closing
> that revealed the **pre-existing guard had been defeated by co-drift**,
> because `test_db_hermeticity.py`'s hand-maintained `_HEAD_TABLES` was missing
> the same table, so two wrong lists agreed and the test stayed green. **The
> rule that came out of it: a comparison means something only when at most ONE
> side is hand-maintained.** The widened guard derives the model set from
> source via AST; `_HEAD_TABLES` stays hand-written **on purpose** (deriving it
> would compare metadata to itself). The `alembic check` half
> shipped as a **test, not a hook** (Cray typed it) — a hook's `upgrade head`
> would collide with a concurrent pytest's `DROP SCHEMA public CASCADE`, and
> running the suite in the background while editing is normal here.
>
> **State at close:** `main` `13aa2f0`, 0 open PRs. Suite **3502 → 3552**; ruff
> check + format clean over **552** files; `mypy --strict services/` clean over
> **123**; `alembic check` + the registration guard clean; CI `gate` PASS and
> merge-commit equality **0 bytes** on all four PRs. **Six non-vacuity
> mutations**, each restored from `/tmp` and diff-verified byte-identical; two
> load-bearing — a router writing `"PENDING"` for `"pending"`, a pure seam bug,
> left **all 17 rule-suite cases GREEN** and reddened 5 of 8 scenario cases;
> emptying the CLI's `_FIRED_HOOKS`, an unwired seam, left the **scenario suite
> fully green** and reddened only the hook suite. One proves the producer is
> right, the other proves anything calls it — which is why §8 wants both. **Dev
> DB migrated 0015 → 0016 on Cray's explicit go.** MS-S1 never touched; LINE
> still disarmed. **R2 rotation applied** — the s184→s185 Current-Focus block
> and the s177 PLAN-0095 Recent-Decisions row rotate to `docs/status-archive/`.

> **Session 186→187, 2026-07-28/29 (head_commit `760ceed` → `728da00`) — the
> arc where PLAN-0096 stopped being a document. Ten PRs merged (#951–#961),
> 0 open: **Steps 1–5, 7 and 9 COMPLETE (6 of 10)**. The fleet vertical now
> carries the design partner's real governance numbers, captures cases from
> minute 1 into Postgres, holds a quote evidence pack, **enforces its sourcing
> rule instead of decorating it**, can record a roadside decision provisionally
> and chase the signature afterwards, imports the partner's PM history as
> measured-then-confirmed data, and owns one outbound notify surface — built
> DISARMED. But the session's most important output is not a feature: **a
> plausible one-line bug left all 24 LINE unit tests GREEN and reddened only
> the scenario suite** — and on that measurement Cray set a new standing work
> standard.**
>
> **(s186 — Steps 1–4, and Step 5 split in half on purpose.)** Step 1 replaced
> the PLAN-0086 simulated customer's ladder with the partner's own (floors
> `"0"`/`"5001"`/`"30001"`, per-truck ceiling 5001) and built the AC-2
> cross-vertical hash tripwire. Step 2 added `repair_case` + alembic 0013 + a
> mobile-first View I. Step 3 added the quote evidence pack — two tables and a
> facts-only read model that states no verdict. **Step 4 is the load-bearing
> one:** it KILLED the fail-open `default: {compliance: {three_quote: true}}`
> reshape, which had been passing every repair whether or not anyone compared
> a price. Cray ratified three things mid-session (the `repair_case` table over
> a ⊕ PLAN line; `distinct_vendor_count` over the PLAN's `quote_count` —
> because three quotes from one garage is not "สามเจ้า"; and a dev-DB
> migration). Step 5 was then split deliberately: part 1 landed the schema, the
> `RESOLVED_PROVISIONAL` status and the pure `ratification_state`, because
> **authoring the fleet window before a driver existed would itself have been
> the PLAN-0094 AC-1 defect class** ADR-0034 D3 exists to prevent.
>
> **(s187 — Step 5 part 2, and one ADR that contradicted itself.)** The
> provisional branch, `ratify_gated_step`, the resume advance, and the fleet's
> `ratification_window_days: 7`. The design's load-bearing choice is an
> **absence**: no `governed_decision` tie is emitted at provisional time,
> because the attested authority answered a phone rather than acting in-system,
> and a tie naming them would be a lie the audit model cannot catch (PLAN-0075
> SD-6(a)). The tie appears at ratification, naming whoever actually signs; a
> refusal emits none at all. **The contradiction found by building it:**
> ADR-0034 **D3(3)** writes the ratify precondition as `status ==
> RESOLVED_PROVISIONAL`, while **D3(6)** requires ratification to stay possible
> on an advanced run — and `resume_run` marks every advanced step `complete`.
> In the fleet hero the step after the gate is *itself* gated, so the run
> always moves past `approve` within minutes while the window is seven days;
> read literally, D3(3) makes the owner's signature **impossible in exactly the
> flow the window exists for**. Cray was shown all four options and typed the
> **state-based precondition** — the obligation (`pending`|`overdue`), not the
> step status — which is a strict superset of D3(3) and preserves its stated
> intent (idempotency BY STATE) verbatim. **The ADR text was amended to match in
> s188 (#962, `eae0f82`) — and it was not the "one word" s187 predicted.** Code
> R2 on that amendment found a SECOND divergence of the same class: D3(3) *and*
> D3(4) both stated the `RESOLVED_PROVISIONAL → RESOLVED` transition
> **unconditionally**, while the shipped flip is conditional on the step still
> being parked there — a step the run has advanced past stays `complete`,
> because walking it back would re-enter `_UNRESUMED_STATUSES` and make a
> finished step look like the one the run is suspended at
> (`action_step.py:1165-1172`). Both halves are the same defect: **the shipped
> mechanism is obligation/audit-based where the ADR text described a
> status-based model.**
>
> **(s187 tail — Steps 9 and 7.)** Step 9 (#959) landed PM data import on the
> shape **Cray typed**: a `pm_import_row` table (**alembic 0015**) *plus* a
> confirmed-PM **ontology overlay**, chosen over a per-process cache and over a
> table with no overlay — the rejected third option would have made **AC-10
> vacuous**, since unconfirmed rows would not touch the ontology and neither
> would confirmed ones. The parser is pure and fail-closed whole-file /
> reject-per-row; four API routes and an onboarding runbook ride with it; the
> fleet's last-service `GUESS` stamps are retired. Cray gave an **explicit go**
> to migrate the dev DB to 0015, and it was verified **against the live schema,
> not `alembic current`** — a probe read `information_schema` and confirmed 15
> columns, `seq` as `bigint … IDENTITY(ALWAYS)`, both indexes + the PK + the
> unique constraint, 0 rows. *(`alembic current` reports which migration RAN,
> never what it produced.)* Step 7 (#960) built the **LINE Official Account
> notify seam**: five AC-8 events, recipients addressed as **ROLES not ids**,
> per-(event, recipient) cooldowns, `tools/notify/line.sh`, an `.env.example`
> block — **outbound only, and DISARMED by design**
> (`LINE_NOTIFY_ENABLED=false`, no token, no recipients), so no test and no dev
> session can reach a real recipient.
>
> **(s187 — the measurement that changed the work standard.)** A non-vacuity
> probe measured that a plausible one-line bug — normalising the LINE recipient
> role key (`role.replace(".", "")`) — leaves **all 24 mock-fed LINE unit tests
> GREEN** while silently ensuring the `ผจก.เดินรถ` role never receives an
> approval request for its entire ฿5,001–30,000 DOA rung. **Only the scenario
> suite reddened.** Root cause: every LINE unit case feeds a `_DETAIL` dict the
> test author wrote, so **the suite agrees with itself by construction** — it
> proves the contract the author IMAGINED, not the one the system produces. On
> that measurement **Cray set a new standing work standard (typed, not
> inferred): a passing unit test proves the SEAM works, never that the system
> does its job — every build also needs a scenario test driving the REAL
> producer into the REAL consumer on realistic simulated data, and skipping it
> is not allowed.** #961 is that correction landing: **8 scenario cases** on
> realistic data, producers wired to consumers. The standard is ADVISORY until
> it reaches `CLAUDE.md` §8 — a Cowork round-trip, logged below.
>
> **Two anti-patterns, each worth a sentence because each cost real time.**
> **"Assert absence by making the test double EXPLODE" does not survive a
> blanket `except`:** the AC-11 case ("a disarmed channel makes no outbound
> call") used a raising transport, and removing the arm gate entirely left it
> GREEN — `_push`'s `except Exception`, correct on its own terms, swallowed the
> `AssertionError`. Rewritten to **RECORD each call and assert the record is
> empty**; nothing can swallow that. And **editing a vertical's
> `data_adapter/__init__.py` retracts a MEASUREMENT** —
> `test_row_4_adapter_is_structurally_equal_to_the_donor` carries PLAN-0086
> AC-7's claim that the hand-written adapter equals scaffolder output, so the
> PM overlay was hung on the object SOURCE
> (`synthetic.OBJECT_SOURCES["Truck"]`) rather than weakening that test.
> Future vertical-specific seams go there too.
>
> **State at close:** `main` `728da00`, 0 open PRs. Full offline gate re-run on
> **every merge commit** (CI here is PR-only, so a merge commit is otherwise
> never tested): **3502 passed / 8 skipped** (s185 baseline 3343 → 3438 at
> #958 → **3470** Step 9 → **3494** Step 7 → **3502** scenarios), `mypy
> services/ verticals/` clean over **175** files, ruff + format clean, R7/R8
> exit 0, and `git diff <branch> <merge>` **0 bytes** on all three tail merges
> (`f7f85ef`↔`1de7b80`, `00b40b2`↔`bc7c8a9`, `a042ce1`↔`728da00`). **AC-2 and
> AC-6 stayed green through every schema touch** — only the fleet's own
> governance hash moved, which is the intended and only effect.
> Non-vacuity discipline held throughout: **eleven probes in session 187
> alone** (the s187 close report's own count — the figure this block carried
> before the tail reconcile counted only through #958), each shown RED before
> its oracle was believed, restored from `/tmp` copies (never `git checkout`)
> and `diff`-verified clean afterwards — including the one that proves Cray's
> precondition ruling is guarded by a single discriminating test, the one
> that flipped `quote_gate` from `failed` back to `complete` when the fail-open
> default was restored, demonstrating the hole Step 4 closed, and the role-key
> probe above. Three real
> defects were found **by running the work**: a JSONB-null-vs-SQL-NULL trap
> that would have silently broken Step 8's export, a response model dropping
> fields the router stored, and an un-gitignored photo-upload directory on a
> PUBLIC repo. `.claude/state/goal.json` **CLEARED this session** — the file
> does not exist, so no stale goal is armed. **MS-S1 was never touched;
> everything was deterministic-offline.** **R2 rotation applied at the
> mid-session reconcile** — the s183 + s182 Current-Focus blocks and the s176
> Recent-Decisions row rotate to `docs/status-archive/`; both archive files
> remain under R4's ~192 KB bar. *(This tail reconcile extends the s186→s187
> block and row in place rather than appending new ones, so it rotates
> nothing.)*

> _Older content rotates out of this file per the **STATUS.md Rotation Policy (R1-R8)** in [`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md) (Lesson #23): Current Focus keeps the 4 newest sessions (<=8 blocks); Recent Decisions keeps the last 10 rows. Rotated blocks/rows live in [`docs/status-archive/`](status-archive/) and git history (Tier 3). Layout — **two separate chains, both with letters ascending with time and the base holding the recent window**: the rotation archive `2026-h1b` → `c` → `d` → `e` → `f` → `2026-h1-status.md`, and the Current-Focus-only `2026-h1b` → `c` → `2026-h1-current-focus.md`. Rotations append to the two bases. **Grep the directory, not a filename** — the chain is one corpus and which file holds a given block is an artifact of where the ~192 KB R4 bar happened to fall. _[Chain created 2026-07-17 (s144): the single `2026-h1-status.md` had reached 592,577 B, 2.3x R4's cap, and the new guard (#789) forced the split.]_

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
| 2026-07-29 | **s189 — PLAN-0096 Steps 1–7 and 9 COMPLETE (8 of 10), #965–#968.** Partner round-2 answers closed 5 of 7. Step 6 = the partner's real 8-step chain (4 mandatory + 4 conditional, per-item staleness, append-only trail, alembic 0016); `pm_due` = a sixth LINE event, group recipient, one message per round, read off persisted `judge_service_due` verdicts. Cray typed the prerequisite-anchored clock + the AC-8 bump. Unplanned (#966/#967): an ORM↔alembic registration guard + `alembic check` lockstep test — **a comparison means something only when at most ONE side is hand-maintained**. Suite 3502 → **3552** | `13aa2f0` (#968 merge, head_commit) / `430cf39` (#967) / `e54cbe8` (#966) / `26e61b3` (#965) / `docs/plans/0096-fleet-flow-completion-phase1.md` |
| 2026-07-29 | **s186→s187 — PLAN-0096 Steps 1–5, 7 and 9 COMPLETE (#951–#961).** Real partner ladder + AC-2 hash tripwire; `repair_case` capture (alembic 0013) + View I; quote evidence pack (0014); **the fail-open `three_quote: true` default KILLED** so the sourcing gate enforces instead of decorating; E-2 deferred ratification built — provisional resolve with the `governed_decision` tie WITHHELD until someone actually signs; PM import measured-then-confirmed (0015 + ontology overlay), retiring the last-service `GUESS` stamps; the LINE OA notify seam, **outbound-only and DISARMED by design**. Cray ratified six things: the `repair_case` table over a ⊕ PLAN line; `distinct_vendor_count` over `quote_count`; the **state-based ratify precondition**, on a **self-contradiction between ADR-0034 D3(3) and D3(6)**; **PM storage = table + ontology overlay** (a table with no overlay would have made AC-10 vacuous); the dev-DB migration to 0015 (verified against the live schema, not `alembic current`); and — on a probe showing that a one-line role-key normalisation leaves **all 24 LINE unit tests GREEN** while only the scenario suite reddens — **a new standing work standard: every build also needs a scenario test driving the REAL producer into the REAL consumer on realistic data; skipping it is not allowed** (#961 = that correction, 8 cases). Suite 3343 → **3502**. **s188 then closed the ADR debt (#962):** ADR-0034 D3 amended so its text matches the shipped mechanism, Status staying `Accepted` — and Code R2 found a **second divergence of the same class** while reviewing it (D3(3) *and* D3(4) stated the status transition unconditionally; the shipped flip is conditional on the step still being parked at `RESOLVED_PROVISIONAL`). Drafted in-harness by the **`plan-drafter` subagent on Cray's typed routing pick**, not a Cowork round-trip — which is itself live evidence that `CLAUDE.md:112`'s claim that editing an Accepted ADR is PreToolUse-gated *for `plan-drafter`* is wrong. **s188 then spent that evidence: a three-edit Cowork round-trip made Cray's scenario-test standard BINDING in `CLAUDE.md` §8, corrected the `:112` gate claim, and retired the `docs/conventions/git.md` extraction by DROP** — Cowork drafted the text, Code re-counted the "24" and the PR pointers before letting them become constitutional text, and applied it (21,524 → 22,424 B; three CLAUDE.md TODOs closed, two of them open since s176) | `eae0f82` (#962 merge, head_commit) / `728da00` (#961 merge) / `docs/plans/0096-fleet-flow-completion-phase1.md` / `docs/adr/0034-governed-exception-family.md` §D3 + §"D3 Amendment (2026-07-29)" |
| 2026-07-28 | **s184→s185 — ADR-0034 "governed exception family" ACCEPTED (#948) + PLAN-0096 "fleet flow completion Phase 1, Lean KPI-first" merged as Draft (#949).** Partner-driven: 18/18 discovery answers → three mechanisms (escalate-never-skip waiver / evidence-alternative E-3 / deferred-ratification primitive E-2+E-4); SoD + compliance stay NON-waivable. Cray resolved OQ-1/OQ-2/OQ-3 per the in-file recommendations and approved the ladder boundary encoding. R2 re-verified all engine cites at `7b84fa2`; all 8 dispatch rejection criteria run adversarially, none fired. Implementation NOT started — awaits Cray's explicit go | `760ceed` (#949 merge, head_commit) / `24c3b45` (#948 merge) / `docs/adr/0034-governed-exception-family.md` / `docs/plans/0096-fleet-flow-completion-phase1.md` |
| 2026-07-28 | **s183 — PLAN-0094 ARCHIVED (Cray released the soak), and the goal-gate `evaluations: 0` finding DIAGNOSED: the gate is not broken, its warn path is unobservable.** Cray reported **no anomalies** on the live loop since Step 4 (s180) — the one thing no session can self-serve — discharging the §Step 6 gate on the `git mv`; **OQ-4 re-homed to an Active TODO in the same change**, never buried in `done/`. The `evaluations: 0` diagnosis rests on four fresh measurements: `save_goal()` writes with `sort_keys=True` while the on-disk key order is **not** alphabetical ⇒ **it never wrote the file**; an offline replay of `run_goal_gate({})` against a `CLAUDE_GOAL_PATH` **copy** dispatched and wrote (`evaluations 0 → 1`) ⇒ **the mechanism works today**; C1–C4 run in **32 s** against the harness's **180 s** kill ⇒ **timeout refuted**; and `_goal_gate.py:440-446` shows `_failing_consequence` under `enforce: false` pinging Telegram and returning `None` with **no `record_evaluation` / `save_goal`**, which *any* failing check reaches (`:491-494`) — and s182's 18-mutation sweep made C1 red by construction on every mutated Stop. **The behaviour is ratified ("v1 — the stop fires"), so changing it is an ADR-0018 question, not a patch** — recommendation logged, not applied. Plus **five stale STATUS sites** corrected (`live-check (ii)` "still unrun" — including a `next_action` that directed a re-run of already-passed work) and the PLAN-0036 pre-archive pointer | `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md` §Step 6 + §OQ-4 / `.claude/hooks/_goal_gate.py:440-446,491-494` / `.claude/hooks/stop_continuation.py:600` |
| 2026-07-28 | **s182 — PLAN-0094 Step 6 executed, AC-10 CLOSED (#943): all 11 ACs closed or withdrawn, on a FULL FRESH 18/18 non-vacuity sweep** — Cray typed the full re-sweep rather than citing the recorded s177/s180 runs. 11 PLAN-named mutations + **7 derived** for the ACs that name none; **`missing_red` EMPTY for all 18**; sibling L2/L3/L4 invariance held. Applied by a harness script, not the Edit tool (the mutated files are the session's own live hooks). **M-A's blast radius is 8 L1 rows, not the 3 first predicted** — the session's prediction was too narrow; the PLAN's L2/L4-stay-green claim is `confirmed — prior intact`. AC-4 also reddens AC-11(i) — a FEATURE. Two stale-doc defects fixed. **The `git mv` to `done/` stays Cray-gated** (live-loop soak + live-check (ii)); OQ-4 OPEN | `1d0649f` (#943 merge, head_commit) / `6726b69` / `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md` §Step 6 |
| 2026-07-28 | **s181 — CLAUDE.md full slim (#941): the 11.1 KB footer changelog RETIRED to git history; 277 → 261 lines / 33,014 → 21,524 B (−35.2%).** NEW convention: a constitutional edit bumps the footer date only — the edit's commit message is the full record; `git log --follow -- CLAUDE.md` = amendment history. Coverage verified BEFORE the cut (20 commit bodies ≥ their footer entries; companion artifacts on disk). No binding rule's substance changed (9 hunks, all §6 + footer). The <200-line LOCKED target unreachable (outside-§6 = 194 lines) → Cray ruled (b): target <20 KB + follow-up extraction pass queued | `85efe52` (#941 merge, head_commit) / `8ffd290` / `CLAUDE.md` + `.claude/handoffs/session-181/` |
| 2026-07-28 | **s180 — PLAN-0094 Step 4 COMPLETE (#937/#938/#939): L1 counts NON-PROGRESS, not touches. AC-7, AC-8(i)/(iii), AC-11 closed.** L1 increments only on a re-applied `old_string` (`repeat xN`) or a return to content already held this turn (`osc xN`); forward edits record `result == ""`; `clear_turn_scoped()` wired into the turn boundary. **All three L1 warns ever recorded would not fire under the new unit.** s179's BLOCKING `tool_response` probe was **answered without being run** (84 recorded `Edit` results: no `content` key, `originalFile` null in 78/84, `structuredPatch` = a diff not a state) — the PLAN's on-disk hash stands, no restart spent. **AC-11: `T` = the DENY bar in BOTH Telegram bodies** (Cray's ruling on a self-contradicting spec). **OQ-4 OPENED — should L1 exist at all?** Baseline over all 113 transcripts: **0 denies, 3 warns, 0 true positives**. **Pre-committed: re-measure after ~20 sessions; TPs still 0 with ≥1 FP → dispatch Cowork to draft the ADR-013 amendment retiring L1.** Suite 3318 → **3327** | `767d520` (#939 merge, head_commit) / `2b9cb6f` / `053410a` (#938) / `0a85b21` (#937) / `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md` §D4 + §OQ-4 |
| 2026-07-27 | **s179 — PLAN-0094 Step 4 RE-SCOPED on its own probe's refutation (#933); OQ-3 opened + RESOLVED same session.** Measured twice, one session apart: **a failed `Edit` invokes NO hook** — not `PostToolUseFailure`, not `PostToolUse`. **D4(a) withdrawn**, taking **AC-1(ii) / AC-6 / AC-8(ii)** with it (AC-6 withdrawn, not weakened) and with them Step 4's only Cray-gated `settings.json` surface; the s169-class thrash stays **uncountable**. OQ-3 → (b), four rulings: **R1** a self-contained COUNT, not a sha1 pointer (evidence ring 6 vs doc trip bar 15); **R2** `dict[str,int]`; **R3** `result == ""` on forward edits; **R4** → new **AC-11** (Telegram `count: N/T` + formatter mirror-invariance) | `b3c20dd` / `bde43d6` (#933) / `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md` §D4 + §OQ-3 |
| 2026-07-27 | **s179 — `main` was RED for three hours and PR-only CI structurally could not see it (#934): the tests EXPIRED, they did not regress.** `_seed_ack` hardcoded a `last_updated`; `load_counter`'s `prune_stale_entries` drops entries past `COUNTER_MAX_AGE_HOURS` (6 h) — green at merge, red hours later. `git diff 25239f3 490f09e` was **EMPTY**: same tree, opposite verdict. Proved with zero code edits (`CLAUDE_LOOP_COUNTER_MAX_AGE_HOURS=100000`). Fix stamps from `_now_iso()` + adds `test_seed_ack_is_stamped_live`, a guard that **tests the FIXTURE** so a future re-hardcode fails at the cause. Suite 3317 → **3318** | `35851f2` (#934) / `bc7be51` (head_commit) / `a5dacb0` (#935, OPEN — Step 4 state layer) |
| 2026-07-27 | **s177 — PLAN-0094 Step 5 BUILT (#930): `awaiting_ack`, the L1 exit an agent cannot fake. AC-9 closed.** When L1 denies, all three documented exits can be shut at once — sticky turn boundary, a commit needing a tree the gated file itself blocks, a subagent reset scoped to the subagent's own edits — which is why **2 of 5 recorded incidents ended in a Cray-authorised shell escape**. The deny branch now arms the marker (that gate becomes a **narrow state writer**) and the Stop hook clears it **only where the stop actually fires** (cap / contentless demotion / dispatch suggestion / pause), never on `proceed`, a goal-gate directive, or re-entry. Also **overrides the sticky rule** for armed targets → two-turn recovery becomes one. **Landed ahead of Step 4 deliberately** (Step 4 is gated on a Cray per-diff `settings.json` approval; no step depends on a later one) — surfaced, not assumed. Key finding the RED-first run forced: a negative row went RED because the turn-boundary reset rewrites the whole document, so **additive-and-tolerant was necessary but not sufficient — additive-and-SERIALIZED is the requirement**. 11 rows, **8 RED-first**; the 3 negative rows proven by named mutations (scratchpad restore, never `git checkout`). Thresholds byte-unchanged. **Live demo, unplanned:** the L1 warn fired on `stop_continuation.py` *while it was being fixed* — 6 distinct forward edits, zero retries = exactly the false-positive class Step 4 exists to kill. Plus **#931**: Cray enabled Docker Desktop's WSL integration (Code declined to flip it itself and said why — `RestartPolicy=no` meant an unasked-for downtime; the prediction held exactly), runbook §1a converts to bash with the build **re-verified from WSL**. Suite 3306 → **3317** | `da0b50b` (#931 merge, head_commit) / `387bef0` / `2736acf` (#930 merge) / `c076f7a` / `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md` §D5 |
## In-Flight Discussions

- **PLAN-0096 — ACTIVE, Steps 1–7 and 9 of 10 COMPLETE (s186→s189, #951–#968); stays `Status: Draft` until Complete.** The fleet design partner's Phase-1 flow: real governance numbers, case capture from minute 1, the quote evidence pack, the computed sourcing signal that retired a fail-open default, the E-2 ratification window, the measured-then-confirmed PM import (alembic 0015 + ontology overlay), the **outbound-only and DISARMED** LINE OA surface (six events since s189), and the partner's real 8-step task chain with per-item staleness (alembic 0016). **Remaining: Step 8** (month-end Express-shaped export — the KPI payoff, and the consumer that made the s186 JSONB `none_as_null` fix load-bearing; **A2 is answered, so it is unblocked**) and **Step 10** (AC-12 confidence sign-off). Two things ride into them rather than being re-derived: the pure `ratification_state()` the export and the reminder must both read, and `repair_case.work_type`, which Step 6 added and Step 8's ประเภทงาน column consumes. Full record: `docs/plans/0096-fleet-flow-completion-phase1.md`.
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

- [x] **The scenario-test standard is now BINDING — CLOSED s188. It is a bullet in `CLAUDE.md` §8 "Code Quality", drafted by Cowork and applied by Code.** Cray's standard, in his own frame: **a passing unit test proves the SEAM works, never that the system does its job — every build also needs a scenario test driving the REAL producer into the REAL consumer on realistic simulated data, and skipping it is not allowed.** The measurement that forced it: normalising the LINE recipient role key (`role.replace(".", "")`) — a plausible one-line bug — left **all 24 mock-fed LINE unit tests GREEN** while silently ensuring the `ผจก.เดินรถ` role never received an approval request for its entire ฿5,001–30,000 DOA rung; **only the scenario suite reddened**, because every unit case feeds a `_DETAIL` dict the test author wrote and so agrees with itself by construction. It had lived only in the agent's private Auto Memory — **recall-based, and it can miss** — which is why it needed a constitutional home. **A hook was deliberately NOT recommended and is not built:** a hook could only check that a scenario FILE exists, which invites ritual compliance and **would not have caught the role-key bug** — the file existed and the suite passed. The shipped bullet answers that structurally instead: it **names the non-satisfiers** ("a test that stubs either side of the seam under test, or a scenario file that drives nothing, does not satisfy this rule") and carries the failure mode inside the rule, so the lazy reading is visibly a violation rather than merely unsupported. **The "24" and the PR pointers in that constitutional text were re-counted by Code before merge, not taken on the drafter's word** — `tests/services/notify/test_line_notify.py` collects exactly 24. *(Cowork surfaced one CHECKABLE variant the hook rejection does not cover, routed as a future PLAN candidate, NOT built: a seam-scoped mutation-testing CI job that requires the scenario suite to redden — ritual compliance cannot fake it, because an empty or stubbed scenario suite stays green under mutation.)*
- [ ] **PLAN-0096 partner round-2 — ANSWERED s189; five of seven closed, one non-blocking follow-up open.** A1 → Step 6 built (#965); A3 → `pm_due` built (#968); **A4 + A7 confirmed values already shipped** (flat ฿5,000 ceiling, `"30001"` inclusive floors); A5 **parked** — no real Wialon export exists yet. **A2 is answered and consumed by Step 8** (no longer a gate). **Open, NON-blocking: cost-center (ศูนย์ต้นทุน) granularity — per truck or per company?** Ship the column, fill the rule when it lands. A6 is answered but is a Step 9 *runbook* item. Detail: `docs/plans/0096-fleet-flow-completion-phase1.md`.
- [x] **ADR-0034's text now matches the shipped mechanism — CLOSED s188 (#962, `eae0f82`); the debt was bigger than s187 estimated.** The divergence, as found s187 by building it: D3(3) wrote `ratify_gated_step`'s precondition as `status == RESOLVED_PROVISIONAL` while D3(6) requires ratification to stay possible on an advanced run — and `resume_run` marks every advanced step `complete` (`services/engine/procedures/persistence.py`) with the fleet hero's post-gate step itself gated, so the run always moves past `approve` within minutes against a seven-day window. **Read literally, D3(3) made the owner's signature impossible in exactly the flow the window exists for.** Cray typed the **state-based precondition** (the obligation, `pending`|`overdue`) — a strict superset preserving D3(3)'s stated intent, idempotency BY STATE, verbatim. **s187 scoped the fix as "one word"; it was two clauses.** Code R2 on the amendment found a **second divergence of the same class**: D3(3) *and* D3(4) both stated the `RESOLVED_PROVISIONAL → RESOLVED` transition unconditionally, while the shipped flip is conditional on the step still being parked there (`action_step.py:1165-1172`; a step the run has advanced past stays `complete`, because walking it back would re-enter `_UNRESUMED_STATUSES`). Both halves are the same defect — **the shipped mechanism is obligation/audit-based where the ADR text described a status-based model** — so both landed as one amendment entry, Status staying `Accepted`. **Route taken: the in-harness `plan-drafter`, on Cray's typed routing pick — NOT Cowork.** That is the live measurement behind the `CLAUDE.md:112` row below: editing an Accepted ADR is *not* PreToolUse-gated for `plan-drafter`, and this session proved it by doing it. Form: header `**Amendment log:**` pointer per ADR-0022 + an in-place `### D3 Amendment (2026-07-29)` section per ADR-0016.
- [ ] **The AT-2 extraction — only the F-FACTORY half remains, owned by PLAN-0076 T1.** The criterion-vocabulary half SHIPPED as PLAN-0087 (COMPLETE 8/8, ARCHIVED — #840/#841); ADR-0025 D7's generator deferral was CANCELLED at N=4 (Cray-ratified, typed); SD-1 = (a) keeps the procedure-aware `ExecutorFactory` half with PLAN-0076 T1, guard `test_at2_extraction_obligation_is_owned` ARMED. Full detail: `docs/plans/done/0087-gate-seam-declared-criterion-vocabulary.md` + `docs/plans/0076-*.md` §A.
- [ ] **PLAN-0075 follow-ons — homed by PLAN-0076 (`Status: Tracking`, #752, s133).** T1 (ADR-0031 D3 gate-plugin seam, F-FACTORY) is PARTIALLY discharged — the criterion-vocabulary half shipped as PLAN-0087; the procedure-aware-`ExecutorFactory` half stays OPEN here. T2's F-PIN remainder CLOSED s143 (#784), but **F-PIN itself stays OPEN**, so PLAN-0076 does NOT archive and its AC-6 presence guard stays ARMED. Full detail: `docs/plans/0076-at2-followon-tracking-gate-seam-and-derivation-pin.md` §A.
- [ ] **Rock 3 — Box-4 economics + the procedure→ontology data-binding gap (O-2) — open ONLY for the O-2 residue.** Every other leg is DONE + archived (PLAN-0046/0048/0061/0062/0066–0068/0070/0071/0073 → `done/`). **The one OPEN residue:** procurement's `intake` migrated only **PARTIALLY** — the derived fields ALREADY moved to declared `transform` ✔ (PLAN-0078 PR-1 #762, AC-2 ticked), so what is left is **only the cardinality-changing `candidate_quotes` nest**, which is explicitly Out-of-Scope there. *[Corrected s175 by the #921 grounding sweep, `was an error`: this entry said production execution stays `_SeedQuery` "for derived fields" — it does not; the derived fields are migrated and the reshape is the sole residue.]* Full detail: `docs/plans/done/0062-per-vertical-seed-migration.md` §SD-C (the co-exist decision + its STOP-and-surface tripwire) + `done/0078-*.md` §L-3 and its Out-of-Scope, where the residue is walled in.
- [ ] **Bounded/incremental chain verification (PLAN-0063 SD-4 follow-up, s118).** `GET /audit/verify` walks the WHOLE chain O(n) on demand — accepted at pilot scale. Future work = a checkpointed head / verify-since-anchor design; anchor storage ≈ external anchoring — **do not build without re-reading the tripwire** in `docs/plans/done/0063-audit-chain-verification-surface.md` + the `services/api/routers/audit.py` module docstring (SD-4). _[Note: the docstring's "ADR-011 boundary" is an EARMARK — `docs/adr/` jumps 0010 → 0012.]_ *(#688/#690)*
- [ ] **DEFERRED: a monotonic `sequence` column on `step_results` — the ROOT fix for `load_run`'s wall-clock ordering.** Needs a DB migration → its own PLAN; none drafted, the deferral STANDS, both surviving orderings DISPLAY-ONLY. Full detail (ROOT-vs-guard, the AST guard, the un-defer trigger): the docstring of `tests/services/db/test_load_run_ordering_guard.py`. _[s169: the un-defer trigger got its FIRST real-case reading and did NOT fire — SD-8 = (a) ELIMINATE. This PLAN now also owns newest-first `/runs` pagination; `view-map.js` (a `CAP = 5` truncating consumer) is a second dependant.]_
- [ ] **Rock 4 — s84 deep research DELIVERED → O-sequence locked.** Cray locked **O-1 → O-3 → O-2 → O-4**. **O-1** (Box-4 ฿ pitch) **DONE** · **O-3 = ADR-0025 Accepted** · **O-4 = PARK** (agent-interop; `docs/adr/0032-*.md` D4 — option-only, un-park = a counterparty's *written* pull). **Remaining: O-2 only** (economic-impact facet + Q3 data-binding = Rock 3). Full detail: `docs/adr/0025-at2-managerial-layer.md` (O-sequence + Box-3 fit + the **evidence-asymmetry** finding rehomed s142). *(s84 Cray ask)*
- [ ] **PLAN-0005 deferred-foundational revisit register** — six Phase 2 "simple thing first" simplifications are production-foundational and must be picked back up at the right batch boundary, not silently forgotten. **Full table (all six rows + their triggers + where each lands): `docs/plans/done/0005-oct-engine-runtime-layer.md` §8.1** — which itself instructs this STATUS entry to be a pointer. *(per Cray note 2026-05-21)*
- [x] **Demo card UX — "trust shape" — BUILT; closed s175 with at most one residue.** *[Closed by the #921 grounding sweep: this sat open as a design-to-build TODO long after it shipped.]* The s74 design (Cray-approved) is live on **both** operator surfaces — what / grounded-why / approve gate + a "show full reasoning trace" toggle (`story.css` `.gc-card.trace-open .gc-trace`), and **no confidence badge**: `confidence_signal` stays engine-internal QA/trace-only, pinned by anti-regression comments citing the PLAN-0035 §SD-3 amendment in `story.css`, `view-story.js` and `view-monitor.js` (the latter at `advisoryBlock`: "grounded REASONS, never a score … no confidence number renders on any operator surface"). SD-3 settled at (a) — the first-class `verification` field is NOT needed. **Residue:** at most one toggle on the monitor step card. Full record + rationale + the reconsider-trigger: the §SD-3 post-archival amendment in `docs/plans/done/0035-governed-action-verify-reshape-build.md`; `ADR-0030` cites it. *(Trigger for the residue: the next demo / UI round.)*
- [ ] **PLAN-004 Phase C — OPTIONAL POLISH (forward-declared; "may never land"):** HTML/markdown handoff dashboard under `docs/` + references-graph (mermaid dispatch chains) + `render_transcript.py` unified session export (PLAN-0004 §"Phase C"). *(Phase A + B both COMPLETE — session 35; the prior TODO's validator **warning-swallow bug was FIXED #312**, s58. Minor never-formally-scoped sub-ideas — README/`_rename-map` walk-exclusion, Cat G `references_*` autofix, OQ-2 effective-vs-authored `status:` dashboard flag — fold in only if Phase C lands. Reconciled 2026-06-16 s65 audit.)*
- [ ] **Custom Postgres image with extensions (pgvector / AGE / pg_trgm) — needs a fresh ADR number + a PLAN; neither drafted.** *[Corrected s141: **PLAN-002 does not exist** ("NOT yet drafted", `docs/plans/done/0005-oct-engine-runtime-layer.md`), and the old "≥ ADR-014" floor is **moot** — ADRs now run to 0032 and `0014-WITHDRAWN.md` exists.]* Context: **`docs/adr/0013-autonomy-axis-relocation.md`** (the floor-bump note) + **`docs/plans/done/0005-*.md`** (trigger: semantic + graph features).
- [ ] Set up self-hosted GitHub Actions runner on MS-S1 MAX
- [x] **`docs/conventions/git.md` — CLOSED s188, resolved-by-DROP: the file will not be extracted, and the dead links to it are gone.** *[De-duplicated s175: this TODO existed twice — here and as an In-Flight "Convention extraction" bullet; the In-Flight copy is dropped, this row is the single home.]* The extraction's substance is effectively discharged by the **`git-workflow` skill** (`.claude/skills/git-workflow/`, Tier 2.6), so the file may never need to exist. What DOES need fixing: **`CLAUDE.md:160` holds a dead relative link** *(shifted from `:176` by the s181 slim; re-verified on disk s181)* to the non-existent `docs/conventions/git.md` ("Future canonical: …"). Either extract the file or drop the link — and **either way it is a Cowork round-trip**, since Code may not author `CLAUDE.md` (ADR-009 D1; the s175 #923 exception was scoped to §8 only). **Cowork called the fork DROP and argued it (s188):** it read `.claude/skills/git-workflow/SKILL.md` and found **nothing** `git.md` would carry that the skill does not — commit-message file+`-F`, `--body-file`, corrupted-PR-body recovery, the `gh pr edit` caveat, push hygiene, the WSL toolchain note, and the Lessons #4/#10/#11 pointers are all already there. The tier-model objection ("2.6 is *derived*, so it needs a canonical") does not survive §4's routing rule: ADR-0017 D5 sends a task-triggered procedure to a Skill **directly**, so the canonical chain is complete without `git.md` — binding rules in §7, durable learnings in the Lessons, procedure in the skill. Extracting it would have bought a third copy of the same content wearing a canonical costume: a standing sync burden and drift surface, for zero unique content. **Both dead pointers removed** — `CLAUDE.md` §7 (which now names the skill as the standing procedural home and *explicitly negates* the extraction, so no future reader re-derives this TODO from an unexplained absence) and `.claude/skills/git-workflow/SKILL.md` §References, which was the last one standing.
- [x] **`CLAUDE.md` §6's gate-route claim — CLOSED s188 after surviving open since s176 (and surviving the s181 slim verbatim).** §6 "Mechanical overlay" says a new PLAN/ADR is PreToolUse-gated for Code **and the in-harness `plan-drafter`**. Measured: `.claude/hooks/pretooluse_classifier_dispatch.py:301-311` **exempts the `plan-drafter` subagent from the G2 classifier gate by design** (PLAN-0034 prong 2, SD-1(a)) — it short-circuits *before* the classifier, so it does not even depend on MS-S1 being warm. The main Code agent carries no `agent_id` and **is** still gated, so **G2's substance is preserved**; only the sentence is wrong. _[Sharpened s183 — the correction is **"gated by a different hook"**, NOT "ungated": `pretooluse_plan_subagent_write_deny.py` is an **allowlist** that affirmatively **permits** `docs/adr/*.md` + `docs/plans/*.md` for this subagent and denies everything else fail-closed. So `plan-drafter` is precisely the one actor for whom writing a new PLAN/ADR is *allowed by design*. Whoever drafts the CLAUDE.md fix should say that, not merely delete the clause.]_ **[s188 — the evidence is no longer a code-reading: it is a live execution.** On Cray's typed routing pick, s188 sent the ADR-0034 amendment — an edit to an **Accepted** ADR, precisely the case `:112` names as gated for `plan-drafter` — to the in-harness `plan-drafter`, and **the write succeeded** (verified on disk; shipped as #962/`eae0f82`). Had it been denied, `:112` would have been right. It was not.**]** **The shipped sentence keeps the s183 shape**: `plan-drafter` is stated as exempt from **the G2 classifier** specifically and **"instead gated by its own fail-closed write-allowlist"** — the "ungated" reading is not producible from it — and it carries the *why* (PLAN-0034 prong 2: the one actor for whom those writes are allowed) so the next reader reconstructs allowlist-instead-of-classifier as a deliberate topology rather than suspecting a gap. "PreToolUse-gated **for Code**" preserves G2's substance and keeps the §6 routing table consistent with no change to it. **No claim is made about G1 vs `plan-drafter` in either direction** — that was never measured. Drafted by Cowork, applied by Code: Code may not author `CLAUDE.md` (ADR-009 D1; the s175 #923 exception was scoped to §8 only), and neither may `plan-drafter` — its H2 allowlist covers `docs/{adr,plans}/` only, which is the very asymmetry this row was about.
- [ ] **CLAUDE.md follow-up extraction pass (s181 option b): new Cowork dispatch; target < 20 KB (~18 KB / ~225–235 line floor).** Candidates (Cowork fresh-eyes, s181 completion §6): §11 ¶3 restates the §6 E2 rule → one-line pointer; §10 skills-row annotation duplicates §4's Tier-2.6 row (in-file ADR-0017 D6 drift); §10 docs/logs row's PLAN-004 parenthetical; §9 halves; §3 folds into §1. Materials: `.claude/handoffs/session-181/` (gitignored). **PARKED s183 by Cray — the dispatch stays UNSENT until two things are settled, and s183 grounded both.** (1) **The unit of `< 20 KB` is load-bearing and unpinned:** `CLAUDE.md` measures **21,524 B / 261 lines**, so the target needs **1,044 B** cut against 20 KiB but **1,524 B** against decimal 20,000 — Cray was asked and declined to rule for now. (2) **The five named candidates cannot reach either target:** measured at **~930–1,000 B** combined, and the row's own "~225–235 line floor" needs **26–36 lines** removed where the five move **~7** (candidates 1–3 are in-line trims that shorten bytes without deleting lines). The genuinely large blocks — `CLAUDE.md:112` (~1,100 B), `:153` (~700 B), `:73` (~800 B) — are **not on the list**. Sending this dispatch as written would repeat the s181 failure of a target that is arithmetically unreachable in scope. ~~Batch the two standing CLAUDE.md defects into whatever dispatch eventually goes out~~ — **DISCHARGED s188**: both rows below are closed, batched into the s188 three-edit Cowork round-trip. _[s188 — **the arithmetic moved AGAINST the target and the row must not be read at its old numbers.** `CLAUDE.md` is now **22,424 B** (+900 B: the §8 scenario-test rule +569, the §6 gate-claim correction +261, the §7 link resolution +70), so the cut needed is **1,944 B** against 20 KiB or **2,424 B** against decimal 20,000 — roughly **double** what this row was written against, while the five named candidates still measure only ~930–1,000 B. Note also that `:112`, one of the three "genuinely large blocks" this row says are **not** on the candidate list, is now ~260 B larger. The growth is Cray-ratified binding-rule substance, not padding — which is the point: **the target and the constitution are pulling in opposite directions, and that is the decision this row is actually parked on**, not the unit question alone.]_
- [ ] **OQ-4 — should L1 loop-detect exist at all? OPEN with a DATED, pre-committed criterion. RE-HOMED here s183 from PLAN-0094, which archived.** This row exists because the PLAN's own §Step 6 forbade carrying a live dated commitment into `done/`. **The criterion, unchanged:** re-measure after **~20 sessions** of the post-AC-7 guard (AC-7 closed s180) → **due ≈ s200**; if **true positives are still 0 and there is ≥ 1 false positive**, dispatch Cowork to draft an **ADR-013 amendment retiring L1**, noting that L2/L3/L4 already carry row E.4 more faithfully — they key on "the same *problem*" while L1 keys only on "the same *file*". **Baseline already banked (s180, all 113 transcripts 2026-06-27 → 07-27): 0 denies, 3 warns, 0 true positives**, and the guard cannot catch the s169 incident that motivated it. **Measurement method matters:** grep transcripts for `L1 warn on` **and both** deny wordings — searching only the current wording under-counts. Full reasoning: `docs/plans/done/0094-loop-detect-non-progress-and-reset-paths.md` §OQ-4. *(Not due yet — premature re-measure burns the pre-commitment on an under-powered sample.)*
- [ ] **The goal gate's warn path records NOTHING — diagnosed s183, NOT fixed. Cray's call whether this becomes a PLAN.** Under `enforce: false` (the default posture) a failing `check` routes to `_failing_consequence`, which pings Telegram and returns `None` with **no `record_evaluation` and no `save_goal`** (`.claude/hooks/_goal_gate.py:440-446`); *any* failing check reaches it (`:491-494`), and `_goal_gate.py` carries **no logging at all**. So the gate's most frequently travelled branch — a red check mid-work — is its **only** branch that leaves no in-repo trail, and its sole signal leaves the machine and no-ops silently if `tools/notify/telegram.sh` is absent. **The mechanism is NOT broken** (offline replay of `run_goal_gate({})` against a `CLAUDE_GOAL_PATH` copy dispatched and wrote, `evaluations 0 → 1`), and **the behaviour is ratified** — `:437-439` calls it "v1 — the stop fires" and `stop_continuation.py:600` documents the fall-through — so **changing it is an ADR-0018 question routed through Cowork, not a Code patch**. **Recommendation:** worth a small PLAN *if* the Axis-B loop is meant to be auditable after the fact; the cheapest shape is a trail entry on the warn path (no consequence change), which is still a recorded-state change and therefore still gated. **Evidence, if this is picked up:** the s182 `goal.json` sat `status: active` / `evaluations: 0` all session, and the decisive forensic is that `save_goal()` serializes with `sort_keys=True` while the on-disk key order was never alphabetical — it had never written the file. *(Related: the evidence artifact — the s182 `goal.json` with `evaluations: []` under `enforce: false` — was in `/tmp`, which does not survive a reboot, so s186 **archived it** to `.claude/handoffs/session-186/evidence/goal-s182-openq2-evidence.json`. Cray's ruling is still owed.)* _[Corrected s187, `was an error`: this line claimed `.claude/state/goal.json` "still holds the COMPLETED s182 PLAN-0094 goal". It did not — s186 overwrote it with the PLAN-0096 Step-1 goal, so the file this pointed at as preserved evidence had been gone for a session. The live goal file was cleared at s187 once Step 5 closed; the evidence lives at the archived path above.]_
- [ ] **STATUS rotation-window slack (runbook R2) — OPEN, Cray's call; untouched s180.** The 4-session / 8-block Current Focus window and the file's byte ceiling now bind at the same time: this reconcile rotated the s175 block out to make room and wrote the s180 block to a byte budget rather than to what the session warranted. Widen the window, tighten the per-block cap, or accept the trade — a Cray decision. Policy home: the R1–R8 rotation policy in `docs/runbooks/memory-architecture.md` (Lesson #23).
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
