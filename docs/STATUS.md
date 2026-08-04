---
last_updated: 2026-08-05T00:06:40+07:00
session: 205
current_batch: "s205 — three parallel-session PRs merged (#1034 cases-list tiebreak, #1035 seq-keyed chain state + alembic 0025, #1036 0024 audit_log backfill); 0 PRs open; none of the three is s205's work."
current_actor: code
blocked_on: "Nothing blocks Code — 0 PRs open. PLAN-0100 execution is gated on Cray ruling SD-1..SD-5; PLAN-0102's excision is gated on Cray ratifying it."
next_action: "PLAN-0102 (retire L1) awaits Cray ratification; PLAN-0100 awaits Cray filling its five Ruling: slots; the assembly-cost metric still needs a reproducible definition."
head_commit: bcab1f4
recent_commits: [bcab1f4, 0c05dba, c632ba4, e9b6194, 318187f, d86bb1d, 022125d, 51e27b2, 9a8c5b6, 954d4ad]
---

# vero-lite — Project Status

> Volatile project state. Updated frequently.
> For stable rules, see [`CLAUDE.md`](../CLAUDE.md).

---

## Current Focus

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

> **Session 203, 2026-08-04 (head_commit `40d65d9` → `592124b`) — three PRs merged
> (#1021–#1023), 0 open. Theme: the ADR-0035 D7 tenant-key PLAN opens, and all three
> of its SDs are the ADR describing something that does not exist.**
>
> **#1021 — PLAN-0101 drafted** (`Status: Draft`, 9 ACs): AC-1..AC-7 each quote their
> D7 sub-item **verbatim** so none can be silently dropped, plus a binding scenario
> test and an adjudication record. `plan-drafter` authored (G2), Code R2'd. It carries
> a `**Ruling:** _(unruled)_` slot under every SD **from the start** — the thing
> PLAN-0100 omitted, which is why PLAN-0100's Phase 0 must now *author* its record.
>
> **Three SDs surfaced UNRULED; Steps 2–6 are BLOCKED-ON-SD.** **SD-1 (load-bearing) —
> the write-stamp site:** D7(iv) names a "session/repository seam" that **does not
> exist**: `services/db/session.py` is 24 lines of engine + `async_sessionmaker` +
> `get_session()`, and a case-insensitive `tenant` grep across `services/` returned
> **0 matches**, so `settings.tenant_id` did not exist either — D7 states both in the
> present tense. **SD-2, emitting a non-ontology column:** `emit_orm` builds each class
> body as a pure function of the ontology's `properties`, and **three** committed
> guards enforce that purity where D7(i) says "the reproducibility guard", singular.
> **SD-3, which uniques `tenant_id` joins:** D7(vi) names **2**; the census is **12**,
> and the 12th is a column-level `unique=True` in `services/db/pm_import.py` that a
> `UniqueConstraint(` grep cannot see — so that census returns 11 and looks complete.
> Two families are non-mechanical: the six Identity-`seq` sites, and an audit chain.
>
> **#1022 — Step 1, the only SD-free step:** the `tenant_id` setting, a `.env.example`
> entry, a 3-leg guard test over a **discovered** (globbed, not hardcoded) vertical
> census, and the Step-1.4 probe. **The probe CONFIRMED a lead by measurement** on a
> throwaway `vero_lite_probe` DB: baseline clean → a new model column IS detected
> (`add_column`, exit **255**) → a `server_default` on the model but absent in the DB
> is **NOT** (exit **0**). **The `add_column` leg is the positive control** — without
> it, exit 0 cannot be told from a broken invocation. Unblocks SD-1's folded
> `server_default` question; dev + all four test DBs untouched, the probe DB dropped.
>
> **Two non-vacuity probes, restored from `/tmp`:** a `settings` read folded into the
> step snapshot → **12 RED**; a constant `"tenant_scoped": True` → **6 RED on the name
> leg, both value legs GREEN** — which is what shows leg 3 closes a real hole rather
> than restating legs 1–2. **Measured, not asserted:** `test_derivation_pin.py` stayed
> green (15 passed) under *both*, because its tripwire watches only the **top** level.
>
> **#1023 — four stale-claim chores.** `code_generator.py`'s "other five" at **three**
> sites (the s202 handoff listed two): one → "six" (the emitter count is fixed at 7),
> the two artifact sites **de-numbered** rather than renumbered — how many outputs are
> gitignored is **namespace-dependent**, so any fixed number re-stales. Plus
> `glossary.md`'s two parked-vertical rows, a stale `[ ]` TODO flipped, and **OQ-4's
> "(Not due yet)" removed — it is NOW DUE**. **Also corrected:** "ADR-0035 mandates no
> ordering" is **not in the ADR** — it originates in PLAN-0100.
>
> **Cray typed:** start the tenant-key PLAN now, not after PLAN-0100's SD-1 (they are
> independent); guard scope = tenant-shaped **names**, not step-level set-equality;
> started `vero-postgres` (5442) / stopped `smb-dev-postgres`; #1021 merges first.
>
> CI `gate` ×3. Offline at CI scope with Dev Postgres up: **3792 passed / 8 skipped /
> 0 failed**, ruff clean, 448 formatted, `mypy --strict` over 130 files. Collected
> totals reconcile against the DB-down run — **3781 both ways** — so the **370 → 8**
> skip collapse is the database coming up, not a coverage change.

> **Session 202, 2026-08-03 (head_commit `6a3f2d7` → `40d65d9`) — seven PRs merged
> (#1013–#1018, #1020); this reconcile is the one still open. The theme: a
> governance gate stops asking a non-deterministic oracle, and ADR-0035's
> follow-on work opens.**
>
> **#1013 / #1016 — G1/G2 are now DETERMINISTIC.**
> `.claude/hooks/pretooluse_governance_gate_deny.py` reads the target's own
> `**Status:**` line instead of asking the local-LLM classifier, which was
> **measured** non-deterministic: the same input at `temperature 0` returned both
> `proceed` and `pause`, self-consistency **0/4**, blank output **3/12**. #1016 then
> unwired the classifier's now-redundant G1/G2 PreToolUse arm
> (`pretooluse_classifier_dispatch.py`) from `settings.json` — it was also **broader
> than its own spec**, pausing Accepted PLANs, which neither the registry's G1 row
> nor `CLAUDE.md` §6 ever claimed (both say ADR). `plan-drafter` stays exempt; the
> main agent gets no override. Three tests pin the new topology.
>
> **#1014 — ADR-0035 D2's four pointer amendments now all EXIST** (ADR-002 ×3,
> ADR-0003 ×1), plus **nine currency notes** re-dating ADR-0035's own present-tense
> claims about the MS-S1 Cloudflare Tunnel — which Cray confirms is **not running**.
> 117 insertions, **0 deletions**: pure appends, no prior text rewritten.
>
> **#1015 — ADR-0032's Context snapshot RE-GROUND (third pass), discharging the s197
> debt.** "six synthetic verticals" → six verticals of which five are synthetic and
> `fleet_maintenance` is the design partner's real Phase-1 pilot.
>
> **#1017 — PLAN-0100 drafted** (`Status: Draft`, 12 ACs, 6 phases): the ADR-0035
> exposure PLAN. Per **Cray's s202 ruling** it absorbs the UI work D5(2) implies,
> because ADR-0035's "Env only — no code" is contradicted by its own D5(2).
> **SD-1..SD-5 are unruled and execution does not start without them** — SD-1
> (published DB posture: DB-less vs synthetic Postgres) is load-bearing: it decides
> which tabs the public sees, and every allowlist row hangs off it.
>
> **#1018 — the OCT nav-bar overflow is FIXED for the dev profile.** `theme.css`'s
> responsive ladder was written for a **five**-tab header while `app.js` registers
> **ten**; measured natural width **2253 px**, so the inactive-label collapse moves
> `max-width:1360px` → `2299px`. Verified **0 overflow** at
> 1280/1366/1440/1680/1920/2400. Two tripwires, both probe-proven RED. The
> published-profile half stays open as PLAN-0100 AC-3.
>
> **#1020 — `CLAUDE.md` §3 rewritten: the runtime procedure spine is named as the
> primitive.** §3 called the ontology + code generator "the moat" and never
> mentioned `procedures.yaml` being interpreted at load; it now leads with
> ADR-0032 D6's `monitor→decide→approve→act` identity. Codegen is **rescoped, not
> denied** — only `energy`/`core` emit committed code. Cowork drafted (§6
> convention) and returned **four corrections to Code's fact-pack**, all confirmed
> before applying. `docs/conventions/glossary.md` carried the same stale framing
> and was corrected with it. **The "SME wording in §1" half is struck** — see the
> Active TODO; it has no referent.
>
> CI `gate` pass ×6. Offline at the last PR: `ruff` clean over `services/` +
> `tests/`, `mypy --strict` clean over 130 files, suite **3411 passed / 370
> skipped**; `tests/handoffs/` **762 / 2** at #1016. **Honest gap:** the 370 skips
> are the Postgres-down shape (dev DB not up on **5442**), so the offline gate did
> **not** match CI scope — CI is the check that did. Four of the six PRs are
> docs-only. Three dispatch fact-packs were refuted by the drafter and corrected
> before use (unmerged-branch reads, a stale date, a wrong route attribution) —
> each was Code's error, not the drafter's.

> _Older content rotates out of this file per the **STATUS.md Rotation Policy (R1-R8)** in [`docs/runbooks/memory-architecture.md`](runbooks/memory-architecture.md) (Lesson #23): Current Focus keeps the 4 newest sessions (<=8 blocks); Recent Decisions keeps the last 10 rows. Rotated blocks/rows live in [`docs/status-archive/`](status-archive/) and git history (Tier 3). Layout — **two separate chains, both with letters ascending with time and the base holding the recent window**: the rotation archive `2026-h1b` → `c` → `d` → `e` → `f` → `g` → `2026-h1-status.md`, and the Current-Focus-only `2026-h1b` → `c` → `2026-h1-current-focus.md`. Rotations append to the two bases. **Grep the directory, not a filename** — the chain is one corpus and which file holds a given block is an artifact of where the ~192 KB R4 bar happened to fall. _[Chain created 2026-07-17 (s144): the single `2026-h1-status.md` had reached 592,577 B, 2.3x R4's cap, and the new guard (#789) forced the split. `g` added 2026-07-30 (s193): the base had returned to 194,232 B with a ~10.7 KB block due to rotate in, so sessions-142→171 spilled and the base dropped to 46,215 B.]_

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
| 2026-08-04 | **#1034 (chip-authored, NOT s205) — `/api/cases` list order is now REPEATABLE, not newest-first.** A `case_id` tiebreak on `opened_at.desc()` ends cross-refresh flicker at the `limit` boundary, but `case_id` is a **random UUID**: it buys **repeatability, NOT newest-first correctness — 50.5 % over 20,000 reps**. True order needs a monotonic `seq`, which PLAN-0099 §Coverage had already weighed here and **KNOWINGLY LEFT (ledger #7)**; **Cray ratified keeping that** — same `uuid4`-tiebreak trap as #1035, opposite right answers (display list ⇒ leave it, correctness path ⇒ `seq`) | `bcab1f4` ([#1034](https://github.com/CrayJThiemsert/vero-lite/pull/1034)) / `services/api/routers/cases.py:272` / `docs/plans/done/0099-wall-clock-root-fix-store-at-write-and-sequence.md` |
| 2026-08-04 | **#1035 (parallel session, NOT s205) — task-chain state re-keyed onto a DB-assigned monotonic `seq`; alembic head is now `0025`.** `chain_state` sorted flips on `at`, a wall-clock stamp, so a backward clock step let the **superseded** flip win; the `event_id` tiebreak never fired because `at` led the sort (and it is a `uuid4` anyway). It feeds `stale_items` → the LINE nudge sweep, so **both directions were live failures**: a finished step nudged forever, a reopened one silently un-chased. PLAN-0099 D2; `(tenant_id, seq)` unique per PLAN-0101 SD-3 | `3b07c16` ([#1035](https://github.com/CrayJThiemsert/vero-lite/pull/1035)) / `verticals/fleet_maintenance/task_chain.py` + `services/api/routers/cases.py:305` / alembic `0025` |
| 2026-08-04 | **#1036 (parallel session, NOT s205) — `0024` could not migrate a POPULATED `audit_log`.** Its backfill `UPDATE` trips `0007`'s `audit_log_no_mutation` **FOR EACH ROW** trigger; CI was green only because every fixture built an **empty** DB where a row trigger never fires — **a test that could not fail, not a flaky one**. Amended (**Cray-ratified** exception to never-edit-a-shipped-revision — nothing later can rescue a migration that blocks the chain) to a transient `ADD COLUMN … NOT NULL DEFAULT` + `DROP DEFAULT`: no `UPDATE`, so append-only never lapses. Dev DB `0022`→`0025`, 136 rows intact | `d86bb1d` (#1036) / `docs/plans/done/0101-tenant-key-column.md` |
| 2026-08-04 | **s205 — OQ-4 ANSWERED: NO; Cray typed RETIRE L1 (#1031).** 130 transcripts, structural hook paths not substring, **positive control 3/3**, true positives **0** in both eras ⇒ the criterion is **unfireable by construction**. Two corrections to the record it was built on: s180's "0 denies" was **wrong — ≥ 56 measured** (a floor; three deny wordings existed, not two), and **ADR-013 never backed L1** ⇒ no amendment, **PLAN-0102** is the vehicle | `74b6a94` (#1031) / `docs/lessons/0035-negative-measurement-needs-a-positive-control.md` |
| 2026-08-04 | **s205 — PLAN-0100 fold-in (#1032) + archive relocation (#1033).** Five empty `Ruling:` slots + **AC-13** + BLOCKED-ON-SD markers make SD-1..SD-5 **askable**; H/I/J reconciled by **dropping Tab H from SD-1's promise** (mixed backend, not DB-posture-contingent); `54dfc7d`'s table folded in verbatim; SD-4 is **published-profile-only**. #1033 moved three misfiled s196/s197 rows `h1g` → base — the recorded blocker was **false** | `27a6961` (head_commit) / `734feae` / `da633a1` / `docs/plans/0100-exposure-published-demo-surface.md` |
| 2026-08-04 | **s204 — PLAN-0101 COMPLETE 12/12 and ARCHIVED (#1028/#1029): the ADR-0035 D7 tenant key, end to end.** 21 tables carry `tenant_id`, all **12** uniques re-scoped (read from built metadata, not source text), revision `0024` with a symmetric downgrade. **Cray typed four calls** — unbind SD-2's letter, a **synthetic second-tenant fixture**, **SD-3 rider 3 reversed** to scope the audit reads. Two consequences the riders never named: a composite FK must move with its widened target (**335 errors, one root**), and audit scoping is **four** sites. Suite **3817 / 0 / 8** | `22202f2` (head_commit) / [#1028](https://github.com/CrayJThiemsert/vero-lite/pull/1028) / `docs/plans/done/0101-tenant-key-column.md` |
| 2026-08-04 | **s204 — the `bash -c` escaping remedy was stated in HALVES in three places at once (#1026/#1027).** A pytest run read `EXIT=0` with two tests RED: the advisory named `\$`-escaping but not the SINGLE-quoted outer argument, so following it literally kept double quotes and fabricated a zero. The hook advisory gains a **4th predicate** (any `$` inside a double-quoted `bash -c` argument, escaped or not) and `CLAUDE.md` §8 now states **both** halves. **§8 and lesson 0007 §1.1 were correct throughout — only the enforcement was half-built.** | `e549e98` (#1027) / `017cf94` (#1026) / `docs/lessons/0007-harness-exit-code-artifact.md` §6.1 |
| 2026-08-04 | **s203 — PLAN-0101 drafted (#1021), its Step 1 SHIPPED (#1022), four stale claims retired (#1023).** All three SDs are ADR-0035 D7 describing what does not exist: the D7(iv) "session/repository seam" (grep `tenant` in `services/` = **0**), "the reproducibility guard" (there are **three**), D7(vi)'s **2** uniques (census = **12**). Steps 2–6 BLOCKED-ON-SD. A probe CONFIRMED `alembic check` sees a new column but **not** a `server_default`. Suite **3792 / 8** | `592124b` (head_commit) / [#1022](https://github.com/CrayJThiemsert/vero-lite/pull/1022) / `docs/plans/done/0101-tenant-key-column.md` |
| 2026-08-03 | **s202 — G1/G2 made DETERMINISTIC (#1013/#1016); ADR-0035 D2's amendments COMPLETE (#1014); ADR-0032 Context re-ground (#1015); PLAN-0100 drafted (#1017); nav-bar overflow fixed (#1018).** The classifier was *measured* non-deterministic at `temperature 0` (self-consistency 0/4, 3/12 blank), so the gate now reads the target's `**Status:**` line and the classifier's G1/G2 arm is unwired. **Cray typed: PLAN-0100 absorbs the UI work D5(2) implies.** SD-1..SD-5 unruled → execution gated | `ef2c898` (head_commit) / [#1018](https://github.com/CrayJThiemsert/vero-lite/pull/1018) / `docs/adr/0035-hosting-and-exposure-model.md` / `docs/plans/0100-exposure-published-demo-surface.md` |
| 2026-08-01 | **s199 — PLAN-0099 COMPLETE (10/10 ACs) and ARCHIVED; the MS-S1 hosting ADR's trigger FIRED.** Six-commit stack merged as one PR: stored at-acceptance figure + provenance, both wall-clock comparisons deleted, five picks re-keyed on `seq`, the ordering guard widened to `services/`. AC-9 proven positively (named nodes re-run alone, 38/0) rather than inferred from the skip total. **Cray ratified all four veto-open calls as-is.** Separately, Cray's stated intent to show the demo over the internet fired two of OQ-1's four conditions; row moved In-Flight → Active TODO, initial lean **B1** | `6a3f2d7` (head_commit) / [#1008](https://github.com/CrayJThiemsert/vero-lite/pull/1008) / `docs/plans/done/0099-wall-clock-root-fix-store-at-write-and-sequence.md` |

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

- [ ] **PLAN-0100 — the ADR-0035 exposure PLAN. DRAFTED s202 (#1017): `Status: Draft`, 12 ACs, 6 phases. EXECUTION IS GATED on Cray ruling SD-1..SD-5.** **SD-1 is load-bearing** — the published deployment's DB posture, (a) DB-less vs (b) synthetic Postgres — because it decides which tabs the published profile registers and every allowlist row hangs off it. Per **Cray's s202 ruling** the PLAN absorbs the UI work D5(2) implies, and it carries the **published-profile half of the nav-bar work as AC-3**. _[s203: Phase 0 Step 1 has **no `Ruling:` slot** — PLAN-0101 carries one under every SD from the start — so Phase 0 must *author* the adjudication record rather than fill it; and its AC-3 measurement table currently lives only in a commit body.]_ _[s204: **SD-4's published half is not answerable as written** — it turns on a published `UI_PROFILE` that exists **only inside this PLAN** (0 occurrences anywhere else in the repo), so the profile must be built, or SD-4 re-scoped, before a ruling on it can mean anything. Fold this in with the s203 findings before the SD round goes to Cray.]_ _[s205: **the fold-in SHIPPED (#1032) and the s203/s204 findings above are DISCHARGED** — the PLAN now carries five empty `Ruling:` slots, **AC-13** (the adjudication record), BLOCKED-ON-SD markers, and `54dfc7d`'s measurement table verbatim; **Tab H was dropped from SD-1's promise** (mixed backend, not DB-posture-contingent). All that remains is Cray filling the five slots.]_ `docs/plans/0100-exposure-published-demo-surface.md`.
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
