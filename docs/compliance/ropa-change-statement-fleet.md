# RoPA change statement — what fleet's published system adds

> **What this is.** The **change statement** PLAN-0103 owes Cray under **AC-11**
> and SD-1's consequence clause. It tells the controller precisely what changed,
> so the RoPA can be updated in one pass.
>
> 🔴 **It is deliberately NOT RoPA text, and nothing here is drafted to be
> pasted.** The RoPA is authored in Cray's controller voice; AC-11's authorship
> boundary is explicit — *"this PLAN gates on it and supplies the change
> statement; it authors none of the text."* The same author boundary this PLAN
> holds against portal-repo files.
>
> **Target:** [`ropa-published-demo.md`](ropa-published-demo.md) (9 sections), or
> a sibling per-dataset instance — the structuring call is Cray's. The template
> ([`../conventions/partner-ropa-lite.md`](../conventions/partner-ropa-lite.md))
> is per-dataset by construction and needs no change either way.

**Status:** open obligation. AC-11 makes the updated RoPA a **precondition of
fleet's bring-up** (ADR-0037 D2.1) — a Step-10 **stop condition**, not a
follow-up. Fleet's profile is authored and merged (`f78068e`); nothing is
reachable yet.

**Why this file is tracked.** It was authored in session 220 into a session
scratchpad and flagged in s221 and again in s223 as *"still the only copy … treat
it as probably gone."* It survived four sessions by luck. An artifact an
acceptance criterion names as owed does not belong in a directory that
evaporates.

---

## 1. The one-sentence change

The published demo stops being a DB-less system. **Fleet's published system adds
a visitor-writable surface (Tab I) whose free text persists to a Postgres
database** — a new processing activity, in a new storage location, with its own
retention question (**answered s231 and enforced in code** — §3.1) and its own
DSR path (**still open**).

## 2. What the current RoPA says that is now incomplete

Verified against the committed file:

- It describes a **DB-less** system. `postgres` / `database`: **zero** mentions.
- Its entire personal-data story is the **prompt log** (§3), treated as a
  *closed* stored set — explicitly not storing IP, headers, or gate identity.
- Retention is **90-day rolling** (§6); DSR honored within 30 days (§8).
- §8's erasure path is a **content search over the prompt log**. That path
  **never reaches a case row**, so as written it cannot satisfy an erasure
  request covering Tab I text.

🔴 **The sharpest instance, worth quoting to yourself while editing.** §6's own
lineage hook states *why* the file can promise erasure at all:

> *"The template's §6 open question (append-only audit integrity vs erasure)
> **does not bite here**: the prompt log is not the tamper-evident audit chain,
> carries no hash links, and nothing downstream reads it."*

Fleet makes that premise false. The reasoning that licenses the current erasure
promise is the exact thing fleet invalidates — so §6 needs a change of
**argument**, not only a change of **scope**.

None of this becomes false for energy or procurement — both stay DB-less. It
becomes **incomplete** the moment fleet publishes.

## 3. The new processing activity, concretely

| | |
|---|---|
| **Surface** | Tab I ("case intake") — visitor-writable |
| **Personal data** | free text a visitor types describing a fault, plus any photo they upload |
| **Routes** | `POST /api/cases`, `POST /api/cases/{id}/photos`; read back via `GET /api/cases/{id}/evidence` and `.../quotes` |
| **Storage** | fleet's own Postgres (`postgres:16-alpine`), database `vero_lite` |
| **Volume** | `oct-fleet-maintenance-pgdata` — a **named** volume, so rows survive a container replace |
| **Reachability** | fleet's own Docker network only; **no published port**; only fleet's `app` can reach it |
| **Tenant** | `TENANT_ID=demo` — stamped on persisted rows (ADR-0035 D7) |
| **Retention** | ✅ **90 days after `opened_at`** — a shipped control, not an intention. Mechanism in §3.1 |
| **DSR path** | 🔴 **undefined for case rows**; the existing path searches the prompt log |

### 3.1 The retention control, as built — input for §6, not §6's text

_[Added s232. This cell read *"no number exists yet — the gap only the controller
can close"* until PLAN-0105 shipped (s231, PRs #1162–#1167). Classified
`superseded by new info`: it was true when this statement was written at s224 and
was answered by a build, not corrected as a mistake. The number itself is
**Cray's ruling** (PLAN-0105 LOCKED-1, typed 2026-08-14), taken before the build
— what changed here is that it is now enforced.]_

What the controller can now state, and what still has to be decided:

| | |
|---|---|
| **Number** | 90 days, measured from `opened_at` |
| **Enforced by** | an in-app periodic task shipped inside the image (`services/api/case_retention_task.py`), **not** a host scheduler — LOCKED-3, because a policy whose enforcement depends on a scheduler nobody installed is a promise rather than a control, and a host scheduler does not survive a redeploy |
| **Armed where** | fleet's published profile only (`CASE_RETENTION_ENABLED=true`). Default-**OFF** in the engine, so no dev box, CI run or pilot deployment acquires row deletion by inheritance |
| **What is deleted** | the case row, its six FK children, and the case's entire upload directory (photos **and** quote attachments) |
| **Anchor** | `opened_at`, written once at creation and never updated — not file mtime, which a volume remount would silently reset |

🔴 **Two facts §6's *argument* has to carry, not just its scope.** §2 flags that
fleet invalidates the premise licensing the current erasure promise; these are the
two the mechanism itself forces into the open:

1. **`repair_case_run_link` rows are deliberately RETAINED** past the case's
   deletion (PLAN-0105 SD-4, ruled (a)). They carry no visitor free text and are a
   governance-decision record, but the result is a **dangling `case_id` pointer by
   design** — SD-3 states that as intended, not as a defect. A §6 that promises
   unqualified erasure of "everything relating to the case" would be false.
2. **The 90 does not inherit from the prompt log's 90.** ADR-0035 D6's regime is
   defined per LLM request and does not reach case text (§4(a)). The code enforces
   that independence structurally — the module is guarded against importing
   `prompt_log` — so a future change to either number must not be described as
   moving both.

⚠️ **Still open, and unchanged by this build:** the **DSR path** (row above), whose
blocking half is requester identification — personas add no visitor identity
(§4(b)), so *"prove you own case X"* has no in-repo answer today — and §5.3's
recorder free text. Neither is a retention question.

## 4. Two scope facts, so the update stays exact

**(a) ADR-0035 D6 does not reach this.** D6 is the *prompt-log* regime, defined
per request *to a published LLM route*. Case text falls outside it. D6's
premise — that the only PII surface of the demo is what visitors type, and that
such typing lands in the prompt log — goes **stale as stated** the day fleet
publishes Tab I. Whether D6 takes a pointer or an amendment is ADR-level and is
recorded in ADR-0037 D3; the RoPA update does not have to settle it.

**(b) The personas add nothing to this.** LOCKED-5 adds **no visitor identity**
to the audit trail: the three persona `person_id`s are synthetic shared
identities and the Access gate email stays vendor-side. So the new activity is
**the case free text**, not the persona mechanism. Do not widen the entry to
cover personas.

---

## 5. The sharp edge — measured, no longer open

### 5.1 What the s220 statement asked the controller to wait for

The session-220 version of this statement framed the sharp edge as *"a case that
drives a governed run enters the tamper-evident audit chain"*, and said:

> *"Do not settle this from memory — **D2.7's measurement is the input, and it
> has not run.**"*

**It has since run** (session 222,
[#1124](https://github.com/CrayJThiemsert/vero-lite/pull/1124)).
`tests/api/test_visitor_case_to_monitor_scenario.py` asserts over **every**
`audit_log` row a full run produces, on both the ordinary path and the
waiver→ratify path, using two independent oracles (Cray, typed, s222):

1. a **sentinel buried inside the visitor's own typed description**, asserted
   absent from every payload — this survives a leak that truncated or reshaped
   the text, which a whole-string search would not. It is **positively
   controlled**: asserted PRESENT in the ingested event first, so *"absent from
   the chain"* cannot pass in the world where the text never reached the run at
   all;
2. a **structural allowlist of top-level payload keys** per audit action, where
   an unknown action **or** an unknown key fails loudly — catching a *new*
   carrier of text when it is introduced rather than when someone next thinks to
   look.

**Result: visitor-typed case text does NOT reach the chain, and `case_id` stays
recoverable.**

⚠️ Scope caveat from the module's own docstring: it is **DB-backed and SKIPS when
Postgres is unreachable** — *"a skip is never satisfaction."* It runs green in
CI, which provisions Postgres.

### 5.2 What that does to the three shapes

| s220's shape | Status |
|---|---|
| **1. Case text excluded from the chain by reference** (chain holds a pointer, text lives in an erasable row) | ✅ **The measured actual behaviour** — not a target, not a hope. Also ADR-0037 D4's ruled direction |
| 2. Case text **is** in the chain; narrow the promise accordingly | ❌ Refuted by measurement for **visitor** text |
| 3. Tab I takes structured input only (no free text) in v1 | Unnecessary as an interim — it existed only to avoid shape 2 |

**What the RoPA can now say is stronger than a hedge:** the erasable row is the
erasure target, the chain holds a `case_id` reference, and that is evidenced by a
test that fails the day it stops being true.

### 5.3 The input the measurement surfaced — **this still needs the controller's judgement**

The same allowlist that proves the visitor's text is absent proves something
else, which the s220 statement could not have known:

**The *recorder's* free text IS in the chain, by design.** Read off
`_ALLOWED_PAYLOAD_KEYS`:

- `gate_decision` may carry **`justification`** — `WaiverInvocation.justification`,
  a human sentence typed by an internal principal;
- `gate_ratified` may carry **`note`** — the ratification note, likewise.

The test module marks the distinction deliberately, with separate sentinels, so
that *"the recorder's words are in there"* (**true, and intended**) can never be
confused with *"the visitor's words are in there"* (**false on every path
measured**).

**Why this reaches the RoPA.** These are a named internal principal's words, not
a visitor's — a different data-subject class from anything §3 currently
describes, in a structure that by construction cannot be selectively erased. It
plausibly needs **its own line**, and the decision is the controller's:

- treat internal-principal free text in the chain as **out of scope** for a RoPA
  about *what visitors type* (defensible — the dataset boundary is visitor
  input), and say so **explicitly rather than by silence**; **or**
- add a short entry covering it, with the honest non-erasability statement
  attached.

⚠️ **Not a defect.** The waiver justification is *supposed* to be in the durable
record — it is the reason a gate was relaxed. The question is only whether the
RoPA describes it.

### 5.4 The residual hole, already ruled

One gap the two oracles do **not** close: a **middle-slice** carrier — text with
both bracketed ends dropped, landing in an already-allowed key — is invisible to
both. **RULED (Cray, typed, s222): that residual risk is ACCEPTED**, with a
stated revisit condition: *if an audit payload gains a field that legitimately
holds a SLICE of operator-entered text.*

Recorded so the RoPA is written knowing it, not so it is re-litigated.

---

## 6. What the update has to contain to satisfy AC-11

AC-11's evidence is *"the updated RoPA on `main` **and** fleet's Step-10 go
record citing it by path"*. Four things it must cover:

1. the **new processing activity** (visitor-typed case free text + photos);
2. its **storage location** (fleet's Postgres, named in §3);
3. its **retention number** — ✅ supplied as of s231, with the two argument-level
   facts it drags with it: **§3.1**;
4. its **DSR path** — and, per §5, an honest statement of what can and cannot be
   promised where the audit chain is involved. 🔴 **The one item of the four with
   no engineering input to draw on**, and its blocker is identification rather
   than mechanism (§3.1's closing note).

Sections most likely affected: **§3** (categories of personal data), **§6**
(retention/erasure — and per §2, its *argument*, not only its scope), **§8** (DSR
mechanism). §5 (residency) is unchanged — the database is on the same host as
everything else. §4 (recipients) is unchanged. See also §8 below for three
staleness items unrelated to fleet.

## 7. What is NOT owed here

- No change to energy's or procurement's posture — both remain DB-less.
- No change to the prompt-log regime itself.
- No template change.
- Nothing blocking: procurement's bring-up is unaffected entirely, and SD-2 ruled
  the order **procurement first, then fleet**.

## 8. Three stalenesses in the RoPA unrelated to fleet

Found while re-verifying §2 (session 224). **None is an AC-11 obligation and none
blocks fleet** — recorded because the file will be open anyway.

**(a) The Status line is now false.** It reads *"populated, offline. The
deployment it describes does not exist until PLAN-0100 Phase 3/5 land."*
PLAN-0100 is `Status: Complete — 2026-08-08 (session 216)`, all 13 ACs closed,
and **two systems are live** (energy; procurement since s222).

**(b) §7's control table marks as "owed" at least two controls that are built and
guard-asserted.**

| §7 row | State found |
|---|---|
| *"No published `ports:` on any service — **owed** — Step 8"* | **Built, all three profiles** — each compose file carries an explicit no-`ports:` banner, guard-asserted as AC-5's property |
| *"Deny-by-default route allowlist at the edge proxy — **owed** — Step 8"* | **Built** — in the committed `cloudflared/config.yml`, path-based separation of allowed from excluded routes, with explicit deliberate denials |
| *"Per-IP rate cap on LLM routes (10/min, burst 20) — **owed** — Step 8, proxy config"* | ⚠️ **Not verified — do not restate either way.** No rate-limit directive appears in the committed `cloudflared/config.yml`. It may be Cloudflare **dashboard**-side, which ADR-0036 D2 makes the home for ingress/Access configuration. This needs a look at the dashboard, not the repo |

**(c) §7's last row — "Access logging over the prompt log itself: **gap**" — is
unchanged and still honest.** Noted only so it is not mistaken for part of (b).

---

*PLAN-0103 AC-11. Authored session 220, superseded and re-verified session 224,
and moved out of a session scratchpad into the repository at that point. Code
authors no RoPA text by design. Every fact was read from the code, the committed
profiles, or the test artifact — the §5 findings come from
`tests/api/test_visitor_case_to_monitor_scenario.py` itself, not from a narrative
about it. Nothing here is ratified.*

*AI-assisted (Claude Code); no `Co-Authored-By` per CLAUDE.md §7.*
