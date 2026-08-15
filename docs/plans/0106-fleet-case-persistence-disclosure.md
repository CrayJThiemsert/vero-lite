# PLAN-0106: Fleet's own in-app case-persistence disclosure (ADR-0037 D2.4, ruled ก)

**Status:** Draft
**Owner:** both — Cray rules SD-1..SD-3 and reviews wording; Claude Code implements
**Created:** 2026-08-14 (session 232)
**Related ADRs:** ADR-0037 (D2.4 — the obligation this PLAN discharges; D4
ruled (a); D3 — why the D6 banner cannot carry it), ADR-0035 (D6 — the banner
this PLAN must **not** edit), ADR-0032 (D5 — the vocabulary rules the wording
is reviewed against), ADR-0036 (D5 — per-system profiles)

> **Drafting provenance (ADR-012 D4.3 / ADR-013 D1).** Drafted by the
> in-harness `plan-drafter` subagent from a Code dispatch recording Cray's
> typed session-232 ruling: **ADR-0037 D2.4 = (ก) — fleet gets its own
> in-app disclosure, owned by this PLAN** (stamped in ADR-0037's 2026-08-14
> amendment pass). The ruling is restated here, never re-argued. Every
> `file:line` fact below was verified on disk in the drafting session.
> Author≠reviewer separation: **INTACT** (drafter authored; Code review +
> Cray ratification at PR). Uncommitted draft — Code commits per ADR-009 D2.

## Goal

Give the **published fleet_maintenance system** its own in-app disclosure that
what a visitor types into the case-intake surface (Tab I — case free text and
photo uploads) **persists to this system's database, for 90 days, and is read
by more than the operator** — discharging ADR-0037 D2.4 under Cray's typed
(ก) ruling, as a **separate element from the ADR-0035 D6 prompt-log banner**,
with the wording Cray-reviewed against ADR-0032 D5's vocabulary rules, pinned
by an element-level guard test in the repo's established shape, and proven by
a scenario test that drives the real server configuration into the real
served surface. This PLAN is a **precondition of fleet's bring-up** (ADR-0037
D2: obligations bind before the system is reachable), beside PLAN-0103
AC-11's RoPA gate.

## Ruled context (LOCKED — restated from typed rulings; not re-arguable here)

- **ADR-0037 D2.4 = (ก)** (Cray, typed, 2026-08-14, s232): fleet gets its
  **own** in-app disclosure, owned by this PLAN — **not** a widening of the
  existing D6 prompt-log banner. Stamp: ADR-0037, D2.4's inline note.
- **ADR-0037 D4 = (a) text-by-reference** (same session): the chain holds the
  case **id**; the erasable case row holds the text. This bounds what the
  disclosure may promise: case text is deletable (and is deleted), while the
  opaque case id persists in the audit chain. Stamp: ADR-0037 D4's ruling
  block.
- **Retention = 90 days, shipped** (PLAN-0105 LOCKED-1):
  `services/db/repair_case_retention.py` (`CASE_RETENTION_DAYS = 90`) +
  `services/api/case_retention_task.py`, armed fleet-only via
  `CASE_RETENTION_ENABLED=true` in
  `deploy/published/oct-fleet-maintenance/published.env:182`. The disclosure
  states a number a shipped control already enforces — not an intention.

## 🔴 Binding constraint: the D6 banner's shared text is NOT the vehicle

**This obligation must not be discharged by editing the D6 banner's shared
text** (`services/api/static/assets/app.js:164-173`). Three measured reasons,
each verified on disk this session — they are this PLAN's justification and
its hard boundary:

1. **ADR-0037 D3 explicitly refuses to widen D6.** "It remains exactly the
   prompt-log regime it says it is" — D6's strength is its closure (one
   store, a set-equality-tested field list, one retention number), and
   widening it to arbitrary persisted datasets dissolves exactly what makes
   its promises checkable. The (ก) ruling reaffirms this posture.
2. **The two 90s are an independent coincidence the codebase actively
   guards.** Case retention's 90 days is PLAN-0105 LOCKED-1's own ruling,
   not an inheritance from the prompt log's 90 —
   `tests/services/db/test_case_retention.py::test_ac9_the_module_does_not_inherit_the_prompt_log_regime`
   (`:327-347`) reads the retention module's real import table and **reddens
   if it imports anything named `prompt_log`**. A merged banner would fuse in
   prose the very numbers the code keeps independent: the day either number
   moves, a shared sentence becomes false on one surface or the other.
3. **"read only by the operator" is factually false for fleet's case
   text.** The D6 banner's sentence ("What you type is retained for 90 days
   and read only by the operator") is true for the prompt log everywhere —
   and false for case text on fleet:
   `verticals/fleet_maintenance/case_events.py:53-63` leads the emitted
   event's `description` with the visitor's own case text (`:98-103`), the
   case projection overlays that event onto the demo stream
   (`verticals/fleet_maintenance/case_projection.py:122-156`), and fleet
   publishes Tab H — the monitor list — to anonymous visitors
   (`UI_PUBLISHED_VIEWS=A,C,F,H,I,J`,
   `deploy/published/oct-fleet-maintenance/published.env:37`; PLAN-0103 AC-8
   asserts a visitor-opened case appears in H's list). **Other visitors read
   it.** Correcting this by editing the shared sentence would break it on
   the DB-less systems where it is true; correcting it fleet-side is SD-3.

   _[Reviewer addition, Code, s232 — a **shorter and harder** path to the same
   conclusion, verified on disk while reviewing this draft. The chain above goes
   through the UI; it does not have to. `GET /api/cases` is `list_cases`
   (`services/api/routers/cases.py:248-278`) — it takes **`session` only, with no
   `Depends(get_current_principal)`**, applies **no tenant or owner filter**, and
   returns `_to_response(c)` for every row, which carries
   `description=case.description` (`:117-127`). `^/api/cases$` is on fleet's
   ingress allowlist (`deploy/published/oct-fleet-maintenance/cloudflared/config.yml`),
   and cloudflared matches **path, not method**, so the same entry that admits
   Tab I's `POST` admits this `GET`. **Any anonymous caller on fleet's published
   surface can list every visitor's typed free text with one unauthenticated
   request** — no persona key, no UI, no Tab H.
   Kept alongside the UI chain rather than replacing it: the two fail
   independently, so a future change that scopes the list endpoint does not
   silently make reason 3 vacuous.
   ✅ **RULED (Cray, typed, 2026-08-14, s232): the exposure is INTENDED** —
   *"ตั้งใจ — demo สังเคราะห์ ทุกอย่างเห็นได้"*. The unauthenticated, unfiltered
   list is the published demo's deliberate posture on synthetic data, **not** a
   defect, and this PLAN neither narrows it nor owes a fix for it. Recorded here
   so it is not reopened: a future reader finding an unauthenticated list of
   visitor free text is looking at a ruled posture, and the thing to check is
   that the data is still synthetic — **that** is the premise the ruling rests
   on, and it is what would make the ruling stale if it ever changed.

   🔴 **What the ruling does NOT settle, and hands to SD-1:** the disclosure must
   still be *true*, and the draft's truth table prices this exposure as *"appears
   on the Monitor timeline"* — **narrower than the measured reality**, which is
   not surface-bound at all. Ruling the exposure intended makes the breadth
   legitimate; it does not make a narrower sentence about it accurate. Whether
   the wording names that breadth stays Cray's call in SD-1.]_

## Acceptance Criteria

- [ ] **AC-1 — the disclosure exists as its own element on fleet's published
  surface.** A case-persistence disclosure renders on the published fleet
  system, as a **separate element** from the D6 banner (its own node / its
  own asset location per SD-2's ruling), **non-dismissable** (the same
  load-bearing in-app capture principle D6 established — a close button
  turns a required disclosure into an optional one). Evidence: the asset
  diff + the AC-2 guard test, which fails if the element is absent.
- [ ] **AC-2 — every obligation element is pinned individually, against the
  real asset.** A guard test in the `tests/api/test_ui_profile.py`
  `_D6_NOTICE_ELEMENTS` shape (`:60-68`): a **new** obligation→substring
  mapping (never appended to `_D6_NOTICE_ELEMENTS`), asserted per-element
  against the **parsed JS asset on disk** (via
  `tests/api/js_source.strip_js_comments`, the established parser) — a
  guard that read its own constant would agree with itself by construction.
  The obligation set it pins (substrings fixed only after SD-1's wording
  ruling, each pinning **the words a reword would take**, per that module's
  own s208 R2 caution): (1) what is stored — case text **and photos**;
  (2) where — this system's database; (3) for how long — deleted after
  90 days; (4) who reads it — **other visitors on the public monitor
  timeline**, not only the operator; (5) the synthetic-demo restatement at
  the point of capture. Falsifiable: dropping any one element, or rewording
  away its operative words, reddens that element's assertion by name.
- [ ] **AC-3 — the D6 banner's shared text is byte-identical.** The
  implementation makes **zero** edits to the D6 notice strings
  (`app.js:164-173`): all seven `_D6_NOTICE_ELEMENTS` pins stay green, and
  the PR diff shows no change inside the D6 notice block. (The pins alone
  cannot catch an *addition* inside the block, so the diff is named
  evidence, not decoration.)
- [ ] **AC-4 — the disclosure is absent where it would be false.** On the
  dev profile, and on a published system that does not grant case
  persistence (procurement's ruled tab set is `G,F` — no Tab I, no
  database), the disclosure does **not** render — energy and procurement
  are DB-less, and telling their visitors "your case is stored for 90
  days" would be false. Evidence: asymmetry assertions in the AC-5
  scenario test (both directions asserted, presence and absence).
- [ ] **AC-5 — scenario test (CLAUDE.md §8 — binding, never skipped).** A
  test that drives the **real producer into the real consumer on realistic
  data**: boot the real FastAPI app configured as the published fleet
  system — profile/vertical/tab values **parsed from the committed
  `deploy/published/oct-fleet-maintenance/published.env`** (the realistic
  data; it reddens if the committed pins drift), not retyped constants —
  then `GET /` and `GET /meta` and assert the really-served document
  carries the published profile before first paint, the served asset chain
  carries the disclosure gated on exactly the state the server declared,
  and the same drive under procurement's committed values and under the
  dev default yields absence (AC-4). Real index rewrite, real static
  assets, no stub on either side of the config→served-surface seam. (The
  browser's JS execution itself has no CI oracle in this repo; the
  served-bytes + gate-condition shape is the established D6/AC-8 bar, and
  Step 4 adds the one-time visual check.)
- [ ] **AC-6 — cache-bust bumped on every touched asset.** Each asset file
  the implementation touches gets its `?v=cNN` bumped in
  `services/api/static/index.html` (`:51-73`) — the counter is
  **per-file**, not a build number (currently e.g. `app.js?v=c49`,
  `view-case.js?v=c44`); differing numbers across files are normal.
  Evidence: the index.html diff touching exactly the edited assets.
- [ ] **AC-7 — the ordering holds.** This PLAN is merged to `main` (wording
  Cray-ruled, tests green) **before** fleet's Step-10 bring-up go, and that
  go record cites this PLAN by number alongside AC-11's RoPA. Evidence: the
  PLAN-0103 Step-10 fleet go record (authored there, not here — the
  bring-up itself is out of scope below; this AC binds only the sequence).

## Out of Scope

- ❌ **Any RoPA text, and any file under `docs/compliance/`.** The RoPA is
  the controller's artifact (ADR-0037 D2.1: "Cray writes the record; no PLAN
  or drafter authors its text"). That includes the recorder-free-text RoPA
  line ruled at ADR-0037 D4 (option (i)) — this PLAN's disclosure is the
  **visitor-facing** surface only.
- ❌ **The DSR path itself.** The stated path is RoPA content (Cray's); the
  deletion mechanics already shipped in PLAN-0105. Nothing here designs
  requester identification (genuinely undesigned — ADR-0037 D2.3's status
  note).
- ❌ **Fleet's bring-up.** PLAN-0103 Step 10: its own typed go, gated on
  AC-10/AC-11 there plus this PLAN's AC-7 ordering.
- ❌ **Any edit to the D6 banner's text, `_D6_NOTICE_ELEMENTS`, or the
  ADR-0035 D6 regime.** AC-3 is the tripwire; SD-3 surfaces the one
  question that borders this line, and even its recommended answer stays
  outside the shared string.
- ❌ **Portal-side copy / card files** (PLAN-0103 AC-9's surface).

## Ordering — a precondition of fleet's bring-up

ADR-0037 D2's obligations are "all binding **before the system is
reachable**", and D2.4 is one of them: fleet's Step-10 go (PLAN-0103) is
gated on **both** AC-11's Cray-authored RoPA **and** this PLAN's disclosure
being live in the profile fleet will boot with. The two gates are parallel
work — the RoPA (Cray's authorship) and this PLAN (Code's implementation)
proceed independently — with **one coupling point**: SD-1's wording ruling,
where Cray reviews that the in-app disclosure and the RoPA's description of
the same processing activity do not contradict each other. Neither artifact
waits for the other to *start*; the bring-up waits for both to *finish*.

## Steps

### Step 0: Cray rules SD-1..SD-3

The three surfaced decisions below. Wording (SD-1) is reviewed against
ADR-0032 D5's vocabulary rules (plain operational language; no capability
over-claim). Nothing in Steps 1–4 is committed before Step 0 — the guard
test's substrings pin the **ruled** wording, so implementing first would pin
words Cray has not approved.

### Step 1: Implement the disclosure per the rulings

In the asset(s) SD-2's ruling selects (Tab-I-scoped → `view-case.js`;
persistent → a fleet-only element in `app.js` **beside, never inside** the
D6 notice block; both → both). Gating reads **server-declared state, never
browser guesses** — the D6 precedent (`app.js:164`): published profile, and
this-system-grants-persistence. Implementation freedom, flagged not ruled: a
mechanically honest gate is "the system publishes the case-writing surface"
(Tab I in the server-declared view set), which is true exactly where the
disclosure is true and never names a vertical in the browser.

### Step 2: The element-pinned guard test (AC-2, AC-3)

New mapping (e.g. `_FLEET_CASE_NOTICE_ELEMENTS`), one substring per
obligation element from the ruled wording, asserted against the parsed
asset — obligation-keyed so a failure names *what went missing*. Thai
substrings are fine and expected (fleet's surface is Thai-first; the repo
pins Thai strings elsewhere). Confirm all existing `_D6_NOTICE_ELEMENTS`
pins stay green untouched.

### Step 3: The scenario test (AC-4, AC-5)

As specified in AC-5: committed-env-driven, both presence and absence
directions, real server → really-served surface, no stubs.

### Step 4: Cache-bust, visual check, closeout

Bump `?v=cNN` per touched file (AC-6). One manual visual pass on the
published-profile rendering (geometry/overlap — the repo's standing
verify-via-preview practice) recorded in the PR body. Then: STATUS update;
this file stays `Draft` until Cray marks it Complete, and archival to
`docs/plans/done/` is the usual Code-side `git mv` at closeout.

## Surfaced decisions

### SD-1 — the exact user-facing wording — ✅ RULED in part (Cray, typed, 2026-08-15, s232)

> **RULING — the visibility clause: BROADEN it.** The drafted candidate said the
> text *"appears on the Monitor timeline"*. That is **narrower than the measured
> exposure** and was corrected before the ruling: `GET /api/cases` is
> unauthenticated, unfiltered, and returns every row's `description`, so the
> exposure is **not surface-bound at all** and a visitor who simply avoids the
> Monitor tab would draw a false conclusion from the original phrasing.
>
> Ruled wording for that clause:
>
> **TH** — ข้อความและรูปถ่ายที่กรอกในใบแจ้งซ่อมจะถูกบันทึกในฐานข้อมูลของระบบนี้
> และถูกลบภายใน 90 วัน — ข้อความในใบแจ้งซ่อม **ผู้เข้าชมทุกคนของระบบนี้อ่านได้
> ไม่ใช่เฉพาะผู้ดูแลระบบ**
>
> **EN** — Case text and photos you enter are stored in this system's database
> and deleted within 90 days. Case text **can be read by anyone who can reach
> this system — not only the operator.**
>
> ⚠️ Note the second-order benefit the ruling takes: the broadened sentence is
> also **shorter and needs no product vocabulary** — a visitor does not have to
> know what "the Monitor timeline" is for it to be true and actionable.
>
> **RULED on sub-question (2): do NOT mention the case id's chain residue** in
> the visitor-facing notice. It is an opaque UUID that means nothing to a
> visitor, and the residue's home is the **RoPA's** register — where PLAN-0105
> SD-3 already states the dangling pointer as intended design.

> **RULED on sub-question (1) (Cray, typed, 2026-08-15, s232): YES — restate the
> synthetic-demo line at the point of capture.** Tab I's notice carries its own
> "demo data is synthetic — do not enter real personal data" lead rather than
> relying on the persistent banner's copy of it.
>
> ⚠️ **This deliberately accepts a duplicated sentence on one screen.** The
> duplication is the cost of the point-of-capture principle ADR-0035 D6
> established: the banner may be scrolled out of view or banner-blind by minute
> 1, and Tab I is the riskiest input on the whole published surface. A reader who
> later finds the repetition untidy is looking at a **ruled trade-off**, not an
> oversight.
>
> 🔴 **Consequence for AC-2's guard:** the synthetic lead will appear in **two**
> elements. The guard must therefore assert the fleet element's own substrings
> **scoped to that element**, never by searching the whole document — a
> document-wide search would pass on the D6 banner alone and go vacuous the day
> the fleet element is dropped.

✅ **SD-1 is now fully ruled. Step 0 is discharged; implementation is unblocked.**

---

*The material below is preserved verbatim as the auditable record of why the
ruling reads the way it does. It is NOT re-arguable.*

**Not settled here.** The candidates below exist so the ruling has something
concrete to strike at; every clause states what it asserts and why it is
true on disk today. Thai first (fleet's surface is Thai-first), English
mirror.

Candidate (TH):

> **ข้อมูลสาธิตเป็นข้อมูลสังเคราะห์ — กรุณาอย่ากรอกข้อมูลส่วนบุคคลจริง**
> ข้อความและรูปถ่ายที่กรอกในใบแจ้งซ่อมจะถูกบันทึกในฐานข้อมูลของระบบนี้
> และถูกลบภายใน 90 วัน ข้อความในใบแจ้งซ่อมจะแสดงบนไทม์ไลน์ของหน้า
> Monitor ซึ่งผู้เข้าชมรายอื่นมองเห็นได้ — ไม่ใช่เฉพาะผู้ดูแลระบบ

Candidate (EN):

> **Demo data is synthetic — please do not enter real personal data.**
> Case text and photos you enter are stored in this system's database and
> deleted within 90 days. Case text appears on the Monitor timeline, where
> other visitors can read it — not only the operator.

Per-clause truth grounding:

| Clause | Asserts | True because |
|---|---|---|
| "stored in this system's database" (text + photos) | Tab I's POST persists a `repair_case` row; photos as metadata + files | `services/db/repair_case.py:57-77` (row; `photos` JSONB, bytes on disk under `photo_root/<case_id>/` — `repair_case_retention.py:138-152`) |
| "deleted within 90 days" | a shipped sweep, not a policy intention | `CASE_RETENTION_DAYS = 90` (`repair_case_retention.py:62`); sweep + `delete_case` (row, FK children, upload dir); armed on this profile (`published.env:182`) |
| "appears on the Monitor timeline … other visitors" | the visitor's text is republished to Tab H, which is public on fleet | `case_events.py:60,98-103` (description leads the emitted event) → `case_projection.py:122-156` (overlay) → Tab H in `UI_PUBLISHED_VIEWS` (`published.env:37`); PLAN-0103 AC-8 |
| synthetic restatement | repeats D6's lead at the point of capture | ADR-0035 D6's element, restated — see the sub-question below |

Sub-questions inside SD-1, also Cray's: **(1)** restate the synthetic-demo
line at the point of capture (recommended — it is the riskiest input on the
whole demo surface and the D6 banner may be scrolled away or banner-blind by
minute 1) or rely on the D6 banner alone; **(2)** whether the visitor-facing
text should mention the case **id** remaining in the audit chain after
deletion (recommendation: **no** — the id is an opaque reference and the
chain residue is the RoPA's register, not a visitor-notice's; but what the
controller discloses where is Cray's call). *Why Cray:* D2.4 makes the
wording Cray-reviewed by construction, and the disclosure is the
controller's promise to a data subject — ADR-0032 D5 vocabulary compliance
(plain, no over-claim) is a review criterion, not a drafter's self-grade.

### SD-2 — placement — ✅ RULED (Cray, typed, 2026-08-15, s232)

> **RULING: BOTH, asymmetrically — the recommendation as drafted.** The
> **Tab-I point-of-capture notice is the load-bearing disclosure**, plus **one
> fleet-only persistent line beside (never inside) the D6 banner**.
>
> The asymmetry is the substance, not a hedge: the person who **types** must be
> told at the moment of typing, and the person who **reads** — a visitor who
> never opens Tab I — must be told where their expectations are set. One surface
> cannot reach both.
>
> ⚠️ **"beside, never inside"** is load-bearing and pairs with SD-3(ก): the D6
> banner's shared string is not edited, so the fleet line must be its own
> element. AC-1 and the D6-byte-identical tripwire both key on that.

*Recommendation as drafted, preserved verbatim:*

**Recommendation: both, asymmetrically** — the **Tab-I point-of-capture
notice is the load-bearing disclosure** (D6's own principle: the in-app
notice at the moment of the act is what the repo can verify;
`view-case.js` is the minute-1 surface where typing happens), **plus one
fleet-only persistent line** rendered beside (never inside) the D6 banner,
because case text is *read* on Tabs H/J by visitors who never open Tab I,
and the persistent region is where the reading visitor's expectations get
set. Alternatives: Tab-I-only (cheapest honest option; leaves the
persistent region's "read only by the operator" uncorrected next to a
public timeline that contradicts it) and persistent-only (covers readers,
but the typist may act on Tab I with the banner scrolled out of
attention — the point-of-capture principle argues against). *Why Cray:*
this sets where the controller's promise is made and is inseparable from
SD-3's repair choice; the options have different honesty surfaces, not
different costs.

### SD-3 — the D6 banner's false clause — ✅ RULED (Cray, typed, 2026-08-15, s232)

> **RULING: (a) — correct by SCOPING in the new fleet-only element.** The shared
> D6 string is **not edited**. The fleet disclosure states plainly that case text
> is readable by anyone reaching the system (SD-1's ruled clause), so the
> combined surface reads: *prompt-log text → operator-only (D6 banner) · case
> text → readable by any visitor (fleet notice)*.
>
> **What this ruling accepts, stated plainly rather than left implicit:** the D6
> sentence *"what you type is … read only by the operator"* stays on fleet's
> screen, and on its own it remains misleading about case text. The ruling holds
> that an **adjacent, explicitly scoped** correction is enough — the two notices
> do not contradict once each names what it governs. ⚠️ If a future reader finds
> them contradictory **in practice** (a real visitor misreading them), that is
> new information and reopens this slot; it is not a re-argument of it.
>
> Option (b) — amending ADR-0035's D6 text — was rejected as recommended: the
> sentence is TRUE on the DB-less systems and true of the prompt log everywhere,
> and editing a shared string to fix one profile reopens exactly what ADR-0037 D3
> refused, at a governance cost this discharge does not need.

*Options as drafted, preserved verbatim:*

The clause is **factually false for case text on fleet** (measured — reason
3 above) regardless of how D2.4 is discharged. Options: **(a — recommended)
correct-by-scoping in the new fleet-only element**: the fleet disclosure
explicitly says case text is visible to other visitors, so the combined
surface reads "prompt-log text: operator-only (D6 banner) · case text:
public timeline (fleet notice)" — the shared sentence stays true for what
it governs (the prompt log, on every system), and no D6 string changes;
**(b)** formally amend the D6 banner text — rejected-by-recommendation:
the sentence is true on the DB-less systems and for the prompt log
everywhere; editing shared text to fix one profile re-opens exactly what
ADR-0037 D3 refused, and ADR-0035 is Accepted (G1-locked); **(c)** leave
it and let the new disclosure carry the correction implicitly — cheapest,
but two adjacent notices that flatly disagree without scoping words teach a
careful reader to trust neither. *Why Cray:* whether an adjacent scoped
correction suffices, or the shared clause's ambiguity ("what you type"
reads surface-unscoped) demands a heavier fix, is a controller-honesty
judgment about Cray's own promise — with (b) carrying governance cost only
Cray can authorize.

## Verification

- Full offline gate green (`ruff` / `mypy services/` / full `tests/`,
  CI-scope), including the new guard + scenario tests reddening under
  mutation: temporarily removing one disclosure element must redden AC-2's
  pin **by name**; temporarily rendering the disclosure unconditionally
  must redden AC-4's absence direction. (Non-vacuity probe, not a committed
  test.)
- `_D6_NOTICE_ELEMENTS` untouched and green; PR diff clean of the D6 block
  (AC-3's two-part evidence).
- The PR body records the Step-4 visual check and names this PLAN and
  ADR-0037 D2.4.
- Closeout (separate from this PLAN's merge): fleet's Step-10 go record
  cites this PLAN (AC-7) — verified when that go happens, in PLAN-0103's
  execution log.
