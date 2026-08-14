# ADR-0037: Data-persistence posture of a published vertical-system — DB-less by default, per-system grant with attached compliance obligations (extends ADR-0036 D5; bounds ADR-0035 D6 by precedence, explicitly)

**Status:** Accepted — ratified by Cray 2026-08-10 (session 218)
**Date:** 2026-08-10 (the routing ruling and the substantive rulings it executes
were typed by Cray in session 218)
**Deciders:** Jirachai Thiemsert (Cray) — ruling originator and ratifier.
**Ratified as drafted:** D1 = **(a) story-required** (the strict grant test;
DB-less stays a bound, not a preference) · D3 = **bound, don't amend** (ADR-0035's
file stays untouched; the one premise at `0035:588-590` is superseded in scope for
granted systems by this ADR's precedence) · D4 = the **direction** only —
**(a) text-by-reference as the target**, (c) permitted as an explicit interim if
the D2.7 measurement forces it, **never (b) as an end state**. ⚠️ **D4's final
ruling is deliberately NOT closed here:** it is Cray's to make *after* D2.7
measures whether visitor case text reaches the audit chain, because the ruling
sets what the controller can promise a data subject and cannot be made before the
measurement exists. OQ-1..OQ-3 remain open and block nothing.
**Related:** ADR-0036 (vertical-as-system; D5 per-system profiles — **extended**,
not re-decided), ADR-0035 (hosting/exposure; D6 prompt-log regime — file
**untouched**; one premise **bounded by precedence**, stated explicitly in D3
below; D7 tenancy — applied), PLAN-0103 (SD-1 is the slot this ADR answers;
AC-11 is this ADR's D2.1 obligation, first instance), PLAN-0100 (SD-1(a) DB-less
ruling — inherited as the default; C-3 storage facts), ADR-011 (log-by-reference
direction, cited by the RoPA's own lineage hook), CLAUDE.md §1 (precedence),
§8 (ADR-before-implementation; secrets; host-state gate).

> **Drafting provenance (ADR-012 D4.3 / ADR-013 D1).** Drafted by the in-harness
> `plan-drafter` subagent from a Code-authored dispatch recording Cray's typed
> session-218 rulings. **Attribution, honestly:** on PLAN-0103 SD-1 the drafter
> recommended "no separate ADR owed" and Code concurred; **Cray overruled both
> and ruled that a new ADR is required.** This document is that ruling executed
> — the routing question is settled and is not re-argued here. Every `file:line`
> fact was verified on disk across sessions 218 and this one. Independent
> review: Code (R2) at PR; ratification: Cray (this ADR is `Proposed` until
> then). Author≠reviewer separation: **INTACT**. Uncommitted draft — Code
> commits per ADR-009 D2.

> **Amendment pass 2026-08-11 (drafted in-harness by `plan-drafter` from a
> Code dispatch; `Status:` unchanged — this amendment records a measurement
> and rules nothing).** The D2.7 measurement this ADR commissioned now
> **exists**: `tests/api/test_visitor_case_to_monitor_scenario.py` (merged via
> PRs #1124/#1125), DB-backed against real Postgres, both decision paths,
> asserted over every `audit_log` row a run produces. Three sites below,
> inline at each: **(i)** D2.7 carries its discharge note; **(ii)** F4's
> structural-difference conclusion is corrected in a note under the fact
> table — labelled `superseded by new info`, with the label argued in place;
> **(iii)** D4 and OQ-2 are **unblocked and deliberately NOT ruled** — the D4
> note states what the measurement implies for each option as input for
> Cray's ruling, which this amendment does not make. Author≠reviewer
> separation: **INTACT** (drafter authored; Code R2 + Cray review at PR).

> **Amendment pass 2026-08-14, session 232 (drafted in-harness by
> `plan-drafter` from a Code dispatch; `Status:` unchanged — this pass stamps
> three typed Cray rulings at their sites and closes the open questions they
> answer; it re-argues nothing and rewrites nothing).** The rulings, recorded
> inline where each belongs: **(i)** D4 = **(a) text-by-reference** — RULED
> (stamp under D4's amendment note), together with the companion ruling the
> amendment note called for: the **recorder's free text gets its own RoPA
> line, stated plainly as non-erasable** (option (i)); OQ-2 closes against
> that stamp. **(ii)** D2.4 = **(ก)** — fleet gets its **own** in-app
> disclosure, owned by **PLAN-0106**; never a widening of ADR-0035 D6's
> banner (D3 stands). **(iii)** OQ-1 closes **retroactively**: its 90-day
> ruling landed as PLAN-0105 LOCKED-1 and shipped, but this file's text was
> never amended to say so — the note at OQ-1 closes that drift and points at
> where the ruling actually lives. D2.3 additionally carries a status note
> (what ruling (a) makes true on disk; what is still owed and whose it is).
> Every pre-existing recommendation and amendment note is preserved verbatim
> as the auditable record of *why* the rulings read the way they do.
> Author≠reviewer separation: **INTACT** (drafter authored; Code R2 + Cray
> review at PR).

## Context

### The question, and why it is an ADR

PLAN-0103's LOCKED-1 (Cray, typed, s218) gives the fleet_maintenance published
system a Postgres inside its own compose project while energy and procurement
stay DB-less. Its SD-1 asked what *authorizes* a per-system DB posture. **Cray
ruled (typed, s218): a new ADR is required before per-system DB posture is
legitimate** — offered both routes, Cray picked the ADR over an ADR-0036 D5
amendment or a PLAN finalization clause. Settled; recorded; executed here.

The reasoning this ADR carries forward — why the ADR route is right: giving a
**public** system a database does not merely change compose topology. It changes
**what personal data the system holds and what can be promised about erasing
it**. That is a decision with legal consequence that outlives PLAN-0103, binds
every future vertical-system, and must be attributable to a decider and a date —
which is precisely what an ADR is for, and what a PLAN's finalization clause is
not: a PLAN shapes files and closes; an ADR carries a durable,
precedence-bearing obligation.

### The measured fact base (verified on disk, s218 + drafting session)

| # | Fact | Grounding |
|---|---|---|
| F1 | **The demo's compliance record describes a DB-less system.** `docs/compliance/ropa-published-demo.md` (~9.2 KB, Cray's voice as data controller): `postgres` / `database` — **zero** mentions. Its entire personal-data story is the prompt log: a **closed** stored set, explicitly not storing IP / headers / gate identity, 90-day rolling retention, 30-day DSR | `ropa:64-66,67-70,100` |
| F2 | **Fleet's grant creates what F1 does not cover.** Tab I ("Open a Case") is a visitor-writable surface; under LOCKED-1 its free text persists to fleet's own Postgres — a **new processing activity, in a new storage location, with its own retention question and its own DSR surface**. The RoPA's erasure path is content search *over the prompt log* and never reaches a case row | `ropa:145-147`; PLAN-0103 SD-1 consequence clause |
| F3 | **ADR-0035 D6 is LLM-route-scoped and cannot absorb F2.** D6 defines what is stored *"per request to a published LLM route"* (`0035:593-595`); its premise — the only PII surface of the demo is what visitors type, landing in the prompt log (`0035:588-590`) — is **stale as stated** the day a granted system publishes a visitor-writable non-LLM surface. Before this ADR, that staleness had no home | `0035:586-629` |
| F4 | **The audit chain bounds what erasure can be promised.** The RoPA can promise prompt-log erasure precisely because that log has no hash links and nothing downstream reads it (`ropa:112-115`). A case that drives a governed run enters the **tamper-evident audit chain** — so the case-text DSR answer is *structurally different*, not merely differently located. ⚠️ Whether visitor-typed text is **copied into** chain records on fleet's case→run path is **unverified** — treated as a required measurement (D2.7), never asserted either way | `ropa:112-115`; D4 below |
| F5 | **The RoPA template needs no change.** `partner-ropa-lite.md` is per-dataset by construction — a new dataset takes a new populated instance or a new section of the demo instance; a structuring call, not a template change | `docs/conventions/partner-ropa-lite.md:3-5` |
| F6 | **Personas add no visitor identity.** The three demo personas (LOCKED-5) are synthetic shared `person_id`s; the gate email stays vendor-side. This **narrows** the new surface to the case free text — it does not eliminate the question | PLAN-0103 SD-1 clause; `verticals/fleet_maintenance/procedures.yaml:102-111` |
| F7 | **Fleet's story is the one that requires persistence.** The runs surface is Postgres-served — PLAN-0100's C-3 struck the runs rows for the DB-less posture (`0100:896-899,921-928`), and the waiting-run seed writes through `async_session` (`services/api/main.py:334-357`). Energy's and procurement's published stories require none of it (procurement's ruled set is `G,F` — the SD-3/SD-4 joint ruling) | PLAN-0100 C-3; PLAN-0103 SD-3 |

> **F4 — corrected by measurement, 2026-08-11 (`superseded by new info`; see
> the amendment-pass note above).** F4's flag was honest — the copying
> question was declared unverified and routed to D2.7 — but its headline
> conclusion ran ahead of that flag, and the measurement refutes it. Measured
> over **every** `audit_log` row a run produces, on both the
> ordinary-approval and the emergency waiver→ratify paths
> (`tests/api/test_visitor_case_to_monitor_scenario.py`): visitor-typed case
> text does **not** reach the tamper-evident chain on either path. Because
> the chain never held the text, **erasing case text breaks no hash — the
> case-text DSR answer is the *same shape* as the prompt log's, not
> structurally different.** What the chain does hold, and cannot un-hold, is
> narrower and different in kind: the opaque `case_id` (`gate_decision`'s
> `decisions` map is keyed by action ids of the form
> `action-event-case-{case_id}`), plus — **by design, not by leak** —
> internal-principal free text on the emergency path
> (`WaiverInvocation.justification`, stored in the chain per its own
> docstring so the obligation and its stated reason cannot drift apart, and
> the ratification `note`, both beside `recorded_by` — a named internal
> principal writing about their own act). F4's opening clause survives: a
> case that drives a governed run does enter the chain — **by name, never by
> text**. Label, argued: `superseded by new info`, not `was an error` — F4
> declared its operative premise unverified and itself commissioned the
> instrument (D2.7) that resolved it; this note is that instrument reporting
> back, not a defect carried unfixed. The measurement's own blind spot — a
> middle-slice carrier inside an already-allowed payload key — is named in
> the test module rather than argued away, and **Cray ruled the residual risk
> ACCEPTED (typed, s222)** with a written revisit condition recorded there.

## Decision

Four decisions. D1 is the posture rule; D2 attaches the obligations; D3 states
this ADR's relationship to ADR-0035 D6 explicitly; D4 surfaces the sharpest
question with a direction rather than resolving it by assertion.

### D1 — DB-less is the default; persistence is a per-system grant made on the record

Every published vertical-system's persistence posture is **declared** in its
committed per-system profile (the ADR-0036 D5 artifact), and the default posture
is **DB-less** — PLAN-0100 SD-1(a)'s bound, inherited as the rule rather than
re-derived per system.

A database is a **grant**: an exception made on the record, in an ADR-visible
place, that **names the visitor-writable datasets it creates** (for fleet:
case free text; the run corpus).

**Decision slot for Cray — strict vs permissive grant test:**

- **(a — recommended) Story-required:** a published system is granted
  persistence only when its *published story requires it*, and the grant
  enumerates the datasets. Grounding: F7 — fleet's approve loop (Tabs H/I/J) is
  storage-backed and is the wedge's core demo moment; energy's and
  procurement's stories need nothing persisted. This keeps the default public
  surface at the RoPA-described minimum and makes every grant carry its own
  justification.
- **(b) Stated-grounds:** any per-system grant is legitimate if declared with
  reasons — more permissive, cheaper for future systems, but it converts the
  DB-less default from a bound into a preference.

First instances under either reading, restated from typed rulings (not
re-decided here): **energy DB-less** (PLAN-0100 SD-1(a), untouched),
**procurement DB-less** (LOCKED-1; SD-3/SD-4 joint ruling (ii)), **fleet
granted** (LOCKED-1, option C).

### D2 — The obligations that attach to a grant, all binding before the system is reachable

The grant and the obligations are one package; a granted system that skips any
of these is out of posture. The obligations bind **the operator and the
artifacts**, not visitors:

1. **RoPA coverage first.** The new processing activity — dataset, storage
   location, retention, DSR path — is recorded in a Cray-authored RoPA
   instance **before** the system's bring-up. 🔴 **The RoPA is the
   controller's artifact: this ADR states the obligation; Cray writes the
   record; no PLAN or drafter authors its text.** PLAN-0103 AC-11 is this
   obligation's first instance. Structuring (new section vs sibling instance)
   is Cray's call — the template itself needs no change (F5).
2. **A named retention number per visitor-writable dataset** (OQ-1).
3. **A stated DSR path per dataset** — for case-linked data, per D4's ruling
   (OQ-2).
   _[Status note, 2026-08-14 — D4 is RULED (a) (Cray, typed, s232; stamp at
   D4). What (a) makes true on disk: the case-text DSR answer is the **same
   shape** as the prompt log's — the text lives in an erasable Postgres row
   outside the chain, and the per-case deletion unit exists
   (`services/db/repair_case_retention.py::delete_case`, s232), so erasure
   is a mechanism, not an intention. What is still owed, and whose: **(1)**
   the RoPA's **stated** path is Cray's to write (D2.1's authorship
   boundary — no PLAN or drafter authors it); **(2)** requester
   identification remains genuinely **undesigned** — `repair_case.opened_by`
   is a `person_id`-shaped string with no FK
   (`services/db/repair_case.py:66-70`) and the personas add no visitor
   identity (F6) — so a DSR request can be matched to case rows only by
   content, and the stated path must say so plainly; **(3)** the recorder's
   free text takes **its own RoPA line, stated plainly as non-erasable** —
   ruling (i), recorded at D4's stamp.]_
4. **In-app disclosure on the granted system**: the published UI must disclose
   that typed case text is persisted, and for how long — the same load-bearing
   in-app capture principle ADR-0035 D6 established for the prompt-log notice
   (`0035:619-629`), applied to the new dataset. Wording is Cray-reviewed
   against ADR-0032 D5's vocabulary rules; mechanics belong to the owning PLAN.
   _[RULED (ก) — Cray, typed, 2026-08-14, s232: fleet gets its **own**
   in-app disclosure, owned by **PLAN-0106**
   (`docs/plans/0106-fleet-case-persistence-disclosure.md`) — **not** a
   widening of the existing D6 prompt-log banner, whose shared text stays
   untouched (D3's refusal stands; the banner's regime remains exactly the
   prompt-log one it says it is). Wording remains Cray-reviewed against
   ADR-0032 D5 per this obligation's own text; PLAN-0106 carries the
   mechanics, the candidate wording as a surfaced decision, and the guard +
   scenario tests. Binding before fleet is reachable — this obligation
   gates fleet's bring-up beside PLAN-0103 AC-11's RoPA (the D2 header's
   "all binding before the system is reachable").]_
5. **Isolation:** the DB service lives inside that system's own compose
   project, on that system's own Docker network, reachable by no other system —
   an application of ADR-0035's acceptance shape and ADR-0036 D5's binding
   isolation note (cited, not re-decided). No database is ever shared between
   published systems.
6. **Tenancy:** every persisted row carries the deployment's `TENANT_ID`
   (ADR-0035 D7 — applied, not re-decided).
7. **Pre-bring-up measurement (feeds D4):** whether visitor-typed case text
   propagates into audit-chain records on the case→run path is **measured on
   the real code**, and the result recorded in the bring-up go package. F4
   marks this unverified; a grant may not go live on an assumption in either
   direction.
   _[Discharged 2026-08-11 — measured, not read:
   `tests/api/test_visitor_case_to_monitor_scenario.py` (PRs #1124/#1125),
   DB-backed against real Postgres, asserted over EVERY `audit_log` row a run
   produces on BOTH the ordinary-approval and the emergency waiver→ratify
   paths. Result: visitor-typed case text does NOT reach the chain on either
   path; the `case_id` IS in the chain and cannot be erased (the
   `gate_decision` `decisions` map is keyed by `action-event-case-{case_id}`
   action ids); internal-principal free text is in the chain BY DESIGN
   (`WaiverInvocation.justification` + the ratification `note`, beside
   `recorded_by`). Oracle: bracketing sentinels asserted absent from every
   payload — positively controlled present in the ingested event — plus a
   structural allowlist of top-level payload keys per audit action; the named
   middle-slice blind spot is ACCEPTED (Cray, typed, s222) with a written
   revisit condition in the module. The test is a permanent guard, so the
   "recorded in the bring-up go package" clause now points at a standing
   tripwire, not a one-off number.]_

### D3 — Relationship to ADR-0035 D6: bounded by precedence, not widened, and said out loud

**This ADR does not edit ADR-0035 or ADR-0036 — both are Accepted and stay
untouched.** What it does, explicitly so no reader discovers a silent conflict:

- **D6 is not widened.** It remains exactly the prompt-log regime it says it is
  (`0035:586`): LLM-route free text, closed set, 90-day rotation, its notice.
  Widening D6 to cover arbitrary persisted datasets would blur the one closed,
  set-equality-tested store (`ropa:67-70`) that makes its promises checkable.
- **One premise is bounded by this ADR's precedence** (CLAUDE.md §1 — newest
  Accepted ADR wins, once ratified): the sentence *"the only PII surface of the
  demo is what visitors type"* (`0035:588-590`, where that typing lands in the
  prompt log) remains true for **DB-less systems** and is **superseded in
  scope for granted systems**, whose PII surfaces are enumerated by their D1
  grant and RoPA record instead. This is a stated supersession of one premise's
  scope, argued here — not an amendment to ADR-0035's file, and not a change to
  any D6 number or mechanism.
- **Decision slot for Cray:** ratify this bounding posture, or direct a formal
  ADR-0035 amendment instead (rejected as Alternative 2 — recommendation:
  bound, don't amend).

Against ADR-0036: this ADR **extends D5** by adding the persistence dimension
to the per-system profile grant. Vertical-as-system, the label convention, and
profile ownership are ADR-0036's and are cited, not restated.

### D4 — The audit-chain / erasure question: surfaced with a direction, ruled after the D2.7 measurement

The structural conflict (F4): the demo RoPA promises erasure of the prompt log
*because* nothing downstream reads it and it carries no hash links
(`ropa:112-115`); the audit chain is tamper-evident and cannot promise the
same. Visitor case text that reaches the chain would inherit the chain's
non-erasability.

Options, to be ruled by Cray **after** D2.7's measurement says which world we
are in:

- **(a — recommended target) Text-by-reference:** the chain holds the case
  **id**; the erasable case row (Postgres, outside the chain) holds the text;
  erasing the row leaves a dangling-by-design reference and an intact chain.
  This is the direction the RoPA's own lineage hook already points to for
  operational data (ADR-011's log-by-reference work, `ropa:154-157`). If the
  measurement shows text already stays out of the chain, (a) is true today and
  gets a **guard test** so it stays true.
- **(b) Accept text-in-chain, disclose the limit:** record in the RoPA and the
  D2.4 disclosure that case text inside the audit chain cannot be erased, only
  aged out of scope. Honest, but it makes the demo promise weaker than the
  prompt log's.
- **(c) Demo-term mitigation while (a) is built:** synthetic-only notice +
  bounded retention as the interim posture, if the measurement shows text
  currently enters the chain and (a) needs real work.

Recommendation: **(a)** as the target posture; **(c)** as the explicit interim
only if the measurement forces it; never (b) as an end state. *Why Cray:* the
ruling sets what the controller can promise a data subject — it is Cray's
promise to make, and it cannot be made before the measurement exists.

> **Measurement in hand (2026-08-11): D4 is UNBLOCKED — and deliberately
> still not ruled; the header's reservation stands and the ruling is
> Cray's.** What D2.7's result (its discharge note in D2) implies for each
> option, stated as input only: **(a)** — the measured world is the one (a)'s
> own text anticipated ("if the measurement shows text already stays out of
> the chain, (a) is true today and gets a guard test so it stays true"): text
> stays out on both paths, and the guard test (a) asks for **already
> exists** — the sentinel + allowlist assertions are a standing tripwire, not
> a one-off reading. **(b)** — the limit it would disclose is narrower than
> F4 feared: not visitor text, but the un-erasable `case_id` plus the
> internal-principal waiver/ratification free text — the latter is personal
> data about a **named internal person** (`recorded_by` sits beside it) and
> needs its own RoPA line under any D4 ruling. **(c)** — its trigger ("the
> measurement shows text currently enters the chain") did **not** fire; there
> is nothing for an interim posture to bridge.

> **RULED (a) — Cray, typed, 2026-08-14, session 232.** The header's
> deliberate reservation is discharged, in the direction recommended:
> **text-by-reference** is the posture. The chain holds the case **id**; the
> erasable case row (fleet's Postgres, outside the chain) holds the text;
> erasing the row leaves a dangling-by-design reference and an intact chain.
> The recommendation and the amendment note above are preserved verbatim as
> the record of why. What already satisfies (a) on disk, so nothing new is
> owed for the posture itself: the D2.7 guard
> (`tests/api/test_visitor_case_to_monitor_scenario.py` — bracketing
> sentinels + the per-action payload-key allowlist) is the standing tripwire
> that keeps text out of the chain, and the per-case deletion unit exists —
> `delete_case(session, case_id, *, photo_root)` in
> `services/db/repair_case_retention.py` (extracted s232; rolls back its own
> partial work and re-raises; deliberately does not refresh the projection).
>
> **Ruled with it (Cray, typed, same session) — the recorder's free text,
> option (i):** the internal-principal free text that is in the chain **by
> design** (`WaiverInvocation.justification` and the ratification `note`,
> typed by a **named internal principal** — `recorded_by` sits beside it)
> gets **its own RoPA line, stated plainly as non-erasable**. This
> discharges the amendment note's clause above ("needs its own RoPA line
> under any D4 ruling"): it is personal data about a different data-subject
> class from the visitor, and its line states the chain's non-erasability
> plainly rather than sheltering behind the case row's erasability. Per
> D2.1's authorship boundary the line's **text** is Cray's, as controller —
> this ruling fixes what the line must say plainly, not its wording. The
> ruling is an input to D2.3's stated-DSR-path obligation and is
> cross-referenced there.

## Consequences

### Positive

- The demo's legal posture becomes **attributable**: which public systems hold
  personal data, on whose decision, under which obligations — one document, one
  decider, one date. Future vertical-systems inherit a rule, not archaeology.
- The DB-less default keeps the minimum public surface the RoPA already
  describes; every enlargement is visible and justified (D1).
- Fleet's grant (LOCKED-1) becomes legitimate **and bounded** — the seven D2
  obligations arrive with it, not after it.

### Negative (the honest costs)

- **The ADR gate adds latency to fleet's half** of PLAN-0103 — this ADR merges
  before fleet's implementation PR (CLAUDE.md §8). Bounded deliberately:
  procurement is DB-less and first in bring-up order (SD-2(b)), so
  **procurement's entire half proceeds while this ADR is in flight** —
  PLAN-0103 Step 4's gate map states it so no executor stalls.
- A one-person controller now maintains a second dataset's compliance record
  (D2.1–D2.3) — real recurring cost, named.
- D2.7 is new pre-bring-up work: a measurement that did not previously exist on
  any checklist.

### Neutral

- Energy's and procurement's postures are untouched restatements of typed
  rulings. ADR-0035's and ADR-0036's files are untouched; the one scope
  supersession is explicit (D3).
- The portal-repo boundary is unaffected: nothing here creates or names a
  portal file, and no system roster appears — postures are declared
  per-system, in that system's own profile.

## Open Questions

- **OQ-1 — retention number for visitor-typed case data (Cray):**
  recommendation **90 days**, aligned with D6's prompt-log number — one number
  for the whole demo surface is one number a visitor-facing disclosure and a
  one-person DSR practice can actually honor. Alternative: shorter (cases are
  demo ephemera), at the cost of a second number to explain everywhere.
  _[Closed 2026-08-14 — ruled **90 days**, but not here and not on this
  file's timeline: the ruling landed as **PLAN-0105 LOCKED-1** (Cray, typed)
  and is SHIPPED — `services/db/repair_case_retention.py`
  (`CASE_RETENTION_DAYS = 90`) + `services/api/case_retention_task.py`,
  armed fleet-only via `CASE_RETENTION_ENABLED=true` in
  `deploy/published/oct-fleet-maintenance/published.env`. One caution the
  pointer must carry: the match with D6's 90 is an **independent
  coincidence**, not an inheritance — LOCKED-1 says so and the code guards
  it (`tests/services/db/test_case_retention.py::
  test_ac9_the_module_does_not_inherit_the_prompt_log_regime` reddens if the
  retention module imports anything named `prompt_log`). This note exists
  because the ruling had existed since PLAN-0105 while this OQ's text still
  read open — a drift caught and closed s232; the reasoning is not restated
  here, it lives with the ruling.]_
- **OQ-2 — the case-data DSR answer (Cray, after D2.7's measurement):** D4's
  slot — recommendation (a) text-by-reference as target; (c) only as measured
  necessity; (b) never as end state.
  _[Unblocked 2026-08-11: the D2.7 measurement exists (discharge note at
  D2.7; per-option implications at D4's amendment note). The ruling remains
  Cray's and is not made here.]_
  _[Closed 2026-08-14 — RULED **(a) text-by-reference** (Cray, typed, s232).
  The stamp, what already satisfies it on disk, and the companion
  recorder-free-text ruling (option (i) — its own RoPA line, plainly
  non-erasable) all live at D4's ruling block; D2.3's status note states
  what remains owed on the stated-path side.]_
- **OQ-3 — RoPA structuring (Cray, as controller):** new section in the demo
  instance vs a sibling per-dataset instance (F5: the template supports either;
  no template change). Recommendation: a new section in the existing instance —
  one demo, one document, easier to keep whole — but this is the controller's
  file and the controller's call.

## Alternatives Considered

### Alternative 1: Authorize the posture from PLAN-0103's finalization clause (no new ADR)
- Pros: zero governance latency; the shape-finalization authority in ADR-0036
  D5 (`0036:214-217`) plausibly covers compose topology.
- Cons: it treats a database as topology. What a public system persists is a
  personal-data and erasure-promise question with consequence that outlives the
  PLAN and binds future systems — a PLAN's clause cannot carry a durable,
  precedence-bearing obligation, and closes with the PLAN.
- Why rejected: **Cray ruled it (typed, s218), overruling the drafter's and
  Code's shared recommendation.** Settled — recorded here for attribution, not
  re-argued; the reasoning above is why the ruling is right.

### Alternative 2: Widen ADR-0035 D6 (formal amendment) to cover all visitor data
- Pros: one regime document for everything visitors type.
- Cons: D6's strength is its closure — one store, a set-equality-tested field
  list (`ropa:67-70`), one retention number, promises that are checkable
  because the set is closed. Widening it to open-ended per-system datasets
  dissolves exactly that; and ADR-0035 is Accepted and G1-locked, making the
  edit route heavier than the bound-by-precedence route for no added clarity.
- Why rejected: D3 bounds one premise explicitly instead; D6 stays coherent.

### Alternative 3: A shared / portal-level database serving multiple systems
- Pros: one DB to operate.
- Cons: violates per-system isolation outright — ADR-0035's acceptance shape
  and ADR-0036 D5's network note exist to prevent exactly this blast radius;
  one system's compromise or migration would touch every system's data; tenancy
  and DSR scoping blur.
- Why rejected: forbidden by the Accepted arrangement this ADR extends (D2.5).

### Alternative 4: Prohibit databases on published systems entirely
- Pros: the RoPA as written stays true forever; smallest possible surface.
- Cons: forecloses fleet's story — the refused-then-granted approve loop is the
  wedge's core demo moment and is storage-backed (F7). LOCKED-1 (Cray, typed)
  already chose otherwise.
- Why rejected: the default (D1) preserves this alternative's virtue for every
  system that does not need more; the grant mechanism prices the exception.

## References

- `docs/compliance/ropa-published-demo.md` — `:64-70` (stored set + not-stored
  list) · `:100` (retention) · `:112-115` (audit-chain erasure boundary) ·
  `:145-147` (prompt-log-scoped DSR search) · `:154-157` (ADR-011 pointer)
- ADR-0035 `docs/adr/0035-hosting-and-exposure-model.md` — D6 `:586-629` (the
  prompt-log regime; premise `:588-590`; per-LLM-route definition `:593-595`;
  notice `:619-629`) · D7 (tenancy)
- ADR-0036 `docs/adr/0036-vertical-as-system-multi-vertical-demo-portal.md` —
  D5 (per-system profiles; finalization clause `:214-217`; isolation note)
- PLAN-0103 `docs/plans/0103-portal-landing-and-per-system-published-profiles.md`
  — SD-1 (the slot + consequence clause), AC-11 (D2.1's first instance), Step 4
  gate map
- PLAN-0100 `docs/plans/done/0100-exposure-published-demo-surface.md` — SD-1(a)
  ruling `:1895-1932` · C-3 `:896-899,921-928`
- `docs/conventions/partner-ropa-lite.md:3-5` · `services/api/main.py:334-357`
  · `verticals/fleet_maintenance/procedures.yaml:102-111` · ADR-011 · CLAUDE.md
  §1, §8
- `tests/api/test_visitor_case_to_monitor_scenario.py` — the D2.7 measurement
  and its standing guard (amendment pass 2026-08-11; PRs #1124/#1125;
  blind-spot acceptance Cray-typed s222, recorded in the module)

**Ratification ask (Cray):** D1's grant test ((a) story-required vs (b)
stated-grounds), the D2 obligation ladder, D3's bound-don't-amend posture, and
OQ-1/OQ-3's recommendations now; OQ-2 after D2.7's measurement. The routing
ruling that created this ADR is already typed and is not re-asked.
