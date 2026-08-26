# s257 — what the s256 walk actually left on the live fleet system

Three **read-only** probes against the published fleet system, each under its own
typed Cray go recorded before it ran (`DEPLOY.md` §0 — per occasion, per phase).
Nothing was deployed, deleted, restarted, or otherwise changed.

**Why this ran at all.** `docs/STATUS.md` carried an Active TODO saying two synthetic
cases *"were left on the published demo"* and naming `DEMO-RESET.md` as the procedure
for clearing them. The session-256 closeout handoff said the opposite — that the cases
had already been erased and only orphan runs remained. Two records of the same event
disagreed, and both are s256. Only the live system could settle it.

## What was measured

| Claim | Result | Control |
|---|---|---|
| `case-8a25399bd734`, `case-596c0244e638` still present | ❌ **ABSENT, both** | GREEN — the same query found 2 of 2 seeded cases |
| `governed_repair_approval@41bb78353e7c4138` still present | ✅ **PRESENT**, `waiting_human`, parked at step **`approve`** | GREEN — 2 of 2 seeded runs found |
| `governed_repair_approval@d8f5a677b8f73b3b` still present | ✅ **PRESENT**, `completed`, all six steps `complete` | same |
| `repair_case_run_link` rows for either walk case/run | **n=0** by case_id *and* by run_id | GREEN — control found 3 seeded links |
| audit rows for the two runs | **6, intact** | — |
| `audit_log` total | **64** — byte-for-byte the count `/audit/verify` reported during the walk itself | — |

Totals at probe time: `repair_case` 24 · `pipeline_runs` 7 ·
`repair_case_run_link` 12 · `audit_log` 64.

## The three findings that change the record

**1. The residue is the RUNS, not the cases.** The cases are gone; both runs remain,
and `@41bb78353e7c4138` is still `waiting_human` at a real `approve` gate a visitor can
resolve. `STATUS`'s "two synthetic cases were left" was wrong in both halves — the
cases are not there, and what *is* there is not cases.

**2. 🔴 `DEMO-RESET.md` cannot do the job `STATUS` assigned it.**
`services/db/demo_run_reset.py` deletes only where `.in_(DEMO_RUN_IDS)` /
`.in_(DEMO_CASE_IDS)` (`:229`, `:237`, `:305`) — fixed constants naming the *seeded*
pair. Visitor-created ids are not in those tuples, so the procedure would reset the
seeded demo run (touching something nobody meant to touch) and leave the target
untouched. The per-case seam is `delete_case`
(`services/db/repair_case_retention.py:174`, `async def`). The walk log made the same
attribution first and STATUS inherited it; the s256 handoff §6 records the correction,
so that session found it too — but only on an untracked surface.

**3. The missing link rows are correct behaviour, not a contradiction.**
`repair_case_run_link` is ruled **RETAIN** under `delete_case` (`NO_FK_REFERENCERS`,
PLAN-0105 SD-4(a)), so an erasure should *leave* orphan links — yet none exist. Probing
by `run_id` as well as `case_id` settles it: they were **never created**. That table is
"a governance-decision record" (its own comment), and both runs travelled the
`run_continued_no_decision` path — by definition no decision to record. The audit trail
shows it directly: `run_continued_no_decision` at **`approve`** *and* **`fulfill`** on
`@d8f5a677b8f73b3b` — PLAN-0114's two-gate arity, visible in the tamper-evident chain.

## What is NOT established

**How the cases went away.** They existed (both runs fired from them; `run_started` is
in the audit chain at 09:40), they are absent now, and `audit_log` is unchanged at 64
rows — so no audit row witnesses their removal. Absence is measured; the mechanism is
not. Recorded as unexplained rather than reconciled into a story that fits.

## Method note

Probe 1 asked for the runs with `LIKE '41bb7835%'`, reading the walk log's
`@41bb7835…` as a truncation. The real id is `<procedure_id>@<hex>`, so the hex is an
**infix** — the pattern could never match and returned a false `n=0`. It was not
written down, because that negative carried no control of its own while the case
negative beside it did. Probe 2 recovered the true format and probes 2–3 carried a
control for every negative. The rule that caught it is `CLAUDE.md` §8: a zero needs a
positive control that finds a known one.
