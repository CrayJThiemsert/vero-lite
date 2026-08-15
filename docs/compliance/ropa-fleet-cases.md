# RoPA-lite instance — fleet's visitor-opened repair cases

> ✅ **ADOPTED by Cray (controller), typed, 2026-08-15 (s233)**, together with
> five rulings that fixed every promise this record makes — §6's 30-day figure,
> the audit-chain disclosure, §7's backup and database-access posture, and §8's
> three sub-promises. Each is stamped in place below.
>
> 🔴 **Authorship, stated plainly rather than left silent.** ADR-0037 **D2.1**
> reserves this record's text to Cray as controller (*"no PLAN or drafter authors
> its text"*). The first draft was written by **Code (Tier 2) at Cray's explicit
> request** — a deliberate departure from D2.1. Cray then ruled every promise
> slot and adopted the result, so the controller owns what this record says; but
> **the departure stands on the artifact, not on anyone's memory**, and
> **ADR-0037 D2.1 still needs an amendment or an explicitly recorded waiver** to
> match how this file was actually produced. Until that lands, a reader comparing
> D2.1 to this file is looking at a real inconsistency, not a misreading.
>
> Facts verified on disk at `11c2f0d`; promises are Cray's, stamped where they
> are made.
>
> **What this is.** A second populated instance of
> [`docs/conventions/partner-ropa-lite.md`](../conventions/partner-ropa-lite.md),
> a **sibling** to [`ropa-published-demo.md`](ropa-published-demo.md), covering
> **one dataset**: what visitors type and upload into fleet's repair-case surface.
> Required by ADR-0037 D2.1; satisfies PLAN-0103 **AC-11**.
>
> **Why a sibling and not an extension** — ✅ RULED (Cray, typed, 2026-08-14):
> the coverage takes its **own per-dataset instance**. Recorded at
> `ropa-published-demo.md:29-33`. ⚠️ ADR-0037`:409`, PLAN-0103`:546` and
> `ropa-change-statement-fleet.md:14` still describe the structuring call as
> **open** — they are stale against that ruling and should be corrected.
>
> Not legal advice and not a full legal RoPA — an engineering-readiness record,
> the same standing the template claims. A Thai PDPA lawyer reviews before any
> real partner signature; this instance covers a **synthetic** demo and no
> partner data.
>
> ⚠️ **Roles are INVERTED relative to the template**, exactly as in the sibling:
> there is no partner, so **vero-lite is the controller** and **Cloudflare is a
> named recipient/processor**.

**Status:** ✅ **Adopted** (Cray, typed, 2026-08-15). The system it describes is
**NOT live**; that is the point of adopting it now. ADR-0037 D2's obligations
bind **before** the system is reachable, so this record precedes exposure rather
than documenting it after the fact.

🔴 **Systems are deliberately not enumerated by label in this file.** ADR-0036 D2
places the cross-system map outside this repo, and a committed vero-lite file
naming two or more system labels is a shadow ingress map — guard-enforced by
`tests/deploy/test_published_profiles.py::test_ac5_no_file_outside_a_profile_lists_two_system_labels`.
Do not "helpfully" add them back.

---

## 1. Controller / processor / contact

- **Controller:** vero-lite — Jirachai Thiemsert, sole operator. No DPO exists,
  and that absence is **recorded as a finding**: the one-person controller is
  also the person who fields every request, so §8 must be workable by one person
  on an ordinary day.
- **Recipient / processor:** **Cloudflare** — the access gate processes **visitor
  email addresses**, and all traffic transits the vendor edge (ADR-0035 D3/D6).
- 🔴 **Additional recipients: every visitor who can reach this system.** See §4 —
  this is the slot where this dataset departs hardest from its sibling.
- **Sub-processors:** none beyond the above.
- **Authority / egress gating:** Cray alone; any command touching the serving box
  is a host-state action requiring explicit go (CLAUDE.md §8).

## 2. Purpose(s) of processing

- **The single purpose:** demonstrating the governed repair-approval flow
  end-to-end — a visitor opens a case so the demo can show a real record moving
  through authority, sourcing-hygiene and approval gates.
- Purpose-limited. **No** secondary use: no marketing profiling, no model
  training, no enrichment, no sale, no onward re-share.

> **Lineage hook.** The purpose requires the case row to be *readable* — a case
> nobody can see demonstrates nothing. That is what makes §4's exposure
> purposeful rather than accidental, and it is also why §4 cannot be narrowed
> without changing what the demo is.

## 3. Categories of data subjects + personal data

- **Data subjects:** demo visitors, and **any third party a visitor names inside
  typed free text or shows in an uploaded photo**. The second class is the hard
  one and cannot be enumerated in advance.
- **Personal data categories** — verified against `services/db/repair_case.py`:

| Field | Class | Where |
|---|---|---|
| Case free text (`description`) | **PII-capable** — free text may carry embedded PII regardless of what the notice asks. ⚠️ **Optional by design**: the truck pick is the only required input | this system's Postgres, `repair_case.description` |
| Uploaded photos / quotes — **file bytes** | **PII-capable** — an image may show a person, a plate, a document | **on disk**, under `photo_root/<case_id>/` |
| Photo metadata (id, filename, content type, size, stored path, upload time) | plain — operational metadata | `repair_case.photos`, JSONB |
| `truck_id`, `opened_at`, `status`, `work_type` | plain — operational metadata | `repair_case` |
| `opened_by` | 🔴 **NOT a subject identifier** — see below | `repair_case.opened_by` |
| Visitor email address | **PII** | **Cloudflare only** — the access gate. Never copied into our database |

🔴 **`opened_by` does not identify anyone, and must not be read as if it did.**
Measured at `11c2f0d`: `services/api/routers/cases.py:206` resolves it to the
server-side principal whenever authn is on (fleet ships `API_AUTH_ENABLED=true`),
that principal is `sha256(bearer key) → person_id` (`services/api/auth.py:79`),
and the keys are the **publicly served demo personas** mapping to the three
authored principals in `verticals/fleet_maintenance/procedures.yaml:103-109`.
**Every visitor writes one of three shared values.** It records *which demo role
was clicked*, not who clicked it. It carries **no foreign key**.

- **Explicitly NOT stored by us:** IP address, request headers, any gate identity.
  The vendor edge keeps its own access-log metadata under its own retention.

> **Lineage hook.** Two storage locations, not one — a row **and** files on disk.
> Any erasure claim that walks only the database is incomplete, which is why §6
> names the file path explicitly and why the shipped sweep deletes **files
> first**.

## 4. Categories of recipients

- **Cloudflare** — gate emails + edge transit.
- 🔴 **Every visitor who can reach this system.** Case free text is republished
  to the public monitor surface, **and** `GET /api/cases` returns every row's
  `description` **unauthenticated and unfiltered**
  (`services/api/routers/cases.py:248-278`); that path is on the system's ingress
  allowlist, and the gate matches **path, not method**. So the exposure is **not
  surface-bound** — it does not depend on a visitor opening any particular tab.
- ✅ **RULED INTENDED** (Cray, typed, s232): this is the published demo's
  deliberate posture **because the data is synthetic**.
  🔴 **Record the premise, not the word.** What would make this entry stale is
  **the data ceasing to be synthetic**, not anyone revisiting the word
  "intended".
- **No onward re-share** beyond the above.

> **Lineage hook.** This is the slot where this dataset is *unlike* its sibling:
> the prompt log has one reader, this dataset has every visitor. An in-app
> disclosure therefore cannot say "read only by the operator" here — which is
> precisely why ADR-0037 D2.4 required a **separate** notice (PLAN-0106) rather
> than a widening of the shared banner.

## 5. Cross-border / residency posture

- **At rest:** the Postgres database **and** the uploaded photo bytes live on the
  serving host (Thailand). Never committed to the repository.
- **Inference:** on-box; the demo's LLM routes never call an external model API.
- **Transit + gate:** Cloudflare's global edge — a **cross-border transit and
  processing path**, named here rather than assumed away.

> **Lineage hook.** Unchanged in kind from the sibling; changed in scope, because
> "at rest" now covers a database and a directory of files rather than one log.

## 6. Retention / erasure schedule

- **Retention: 90 days from `opened_at`.** Verified: `CASE_RETENTION_DAYS = 90`
  (`services/db/repair_case_retention.py:62`), armed on this profile via
  `CASE_RETENTION_ENABLED=true`.
- **Erasure mechanism — a shipped control, not an intention:**
  1. **Automatic deletion at 90 days** by an in-app task
     (`services/api/case_retention_task.py`, wired into `lifespan`). There is no
     scheduler on the serving host, so retention enforced by cron would be a
     promise rather than a control.
  2. **Scope per case** — `delete_case()` removes the case row, its **six FK
     child tables** in a dependency-correct order, and the case's **upload
     directory**. **Files first, then rows**, so a crash cannot leave metadata
     promising a file that is gone.
  3. **A data-subject deletion request, honored within 30 days** — §8.
     ✅ **RULED (Cray, typed, 2026-08-15): the same 30 days as the sibling.** Not
     inherited automatically — this is a different dataset under a different ADR,
     so the figure was re-decided rather than assumed. It is the *easier*
     commitment of the two: erasing a case is the single call `delete_case()`,
     where the prompt log needs a content search and a line-by-line edit.
- 🔴 **What erasure does NOT remove. Stated rather than left for a reader to
  infer, because a promise of completeness would be false.** ADR-0037 **D4 = (a)
  text-by-reference**: the tamper-evident audit chain holds the **case id**,
  never the case text. Erasing the row erases the visitor's words and leaves an
  **opaque, dangling id** in the chain.
  ✅ **RULED (Cray, typed, 2026-08-15) — disclose it, and disclose both halves of
  why:**
  1. **Why it must remain.** The chain is tamper-evident: entries are hash-linked,
     so removing one would break the evidence that every other governance claim
     in this system rests on. The choice is not "keep the id or delete it" but
     "keep the id or lose the ability to prove any approval happened at all". The
     residue is the price of the audit property, and it is **a deliberate trade,
     not an oversight or a limitation we failed to fix**.
  2. **Why what remains is not personal data.** The id is a random UUID. Once the
     row is erased there is nothing left to join it to — not the text, not the
     photos, and **not `opened_by`**, which never identified anyone (§3: it
     records which of three shared, publicly served demo personas was clicked).
     So the erasure is complete **in substance**: what survives cannot be resolved
     to a person by us or by anyone else.

  Both halves are stated because either alone misleads — (1) alone reads as a
  system defect, and (2) alone reads as an evasion of the question.
- 🔴 **The recorder's own free text is NOT erasable, and takes this line of its
  own** — ✅ RULED (i) (Cray, typed, s232). `WaiverInvocation.justification` and
  the ratification `note` are written by a **named internal principal**, not by
  the visitor, and they live in the audit chain. ⚠️ Must not be blended with the
  visitor-text promise above: one is erasable and the other is not.

> **Lineage hook.** The sibling's §6 lineage hook says the template's
> append-only-vs-erasure question *"does not bite here"* because the prompt log is
> not the audit chain. **That reasoning does not transfer.** This dataset *is*
> adjacent to the chain, and the reason erasure can still be promised is
> narrower and must be stated as such: the chain holds a **reference**, not the
> text.

## 7. Technical + organizational security measures

- **Ingress:** Cloudflare Access — an **email-allowlist** policy with one-time
  PIN, verified to *discriminate* (an allowlisted address received a PIN; a
  non-allowlisted one did not). Evidence:
  [`docs/logs/2026-08-15-fleet-cloudflare-artifacts-and-secrets-staging.md`](../logs/2026-08-15-fleet-cloudflare-artifacts-and-secrets-staging.md).
- **Application authn:** bearer keys stored as **SHA-256 digests only**
  (`services/api/auth.py:79`). ⚠️ The **persona keys are served to the browser by
  ruling** (Cray, typed, s224) — they are demo role-switchers, **not secrets**,
  and §3 records that they therefore confer no visitor identity.
- **Secrets at rest on the serving host:** ACL-restricted, inheritance verified
  across the secrets directory; no broad principals present.
- **Network exposure — verified in the committed compose file, not assumed.**
  **No `ports:` key on any service.** The database is reachable from this
  system's own `app` container and **from nothing else** — not the host, not the
  LAN, not the internet. The per-system bridge network declares no fixed `name:`,
  and `tests/deploy/test_published_profiles.py` asserts that for every profile,
  so the database cannot be put on a shared wire by a later edit either.
  ⚠️ The repo-root **dev** compose *does* publish `5432`; that habit must never be
  copied into a published profile, and the file says so in two places.
- **Database credentials:** a host-environment secret, required with no default.
  Never a committed literal — this repository is public.
- 🔴 **Backups: NONE, and that is deliberate at this stage.** ✅ **RULED (Cray,
  typed, 2026-08-15):** the system is a **demo-pilot** carrying synthetic data
  only, so no backup regime exists. **Recorded as a finding rather than left
  blank** — an absent control that is stated is auditable; an unstated one is
  indistinguishable from an unexamined one. ⚠️ **This entry goes false the moment
  the data stops being synthetic**, which is the same premise §4's ruling rests
  on — the two should be revisited together.
- **Who can reach the database directly:** ✅ **RULED (Cray, typed, 2026-08-15):**
  **only those who can `ssh` to the serving host — which is Cray alone.** There
  is no other access path, because there is no published port (above).

## 8. Data-subject-rights (DSR) mechanism

✅ **Every promise in this section was ruled by Cray (typed, 2026-08-15).**

**Honored within 30 days** — ruled, matching the sibling (§6).

- **Can we locate all of a subject's records? Only by content — and the limit is
  sharper here than in the sibling, for a different reason.**
  - The sibling stores **no subject identifier at all**, by design.
  - This dataset stores a field that *looks* like one and is not:
    **`opened_by` records which of three shared, publicly served demo personas was
    clicked** (§3). Many distinct people collapse onto one value.
  - 🔴 **Therefore a request must never be served by filtering on `opened_by`** —
    doing so would select **every visitor's** cases under that persona. That is
    not an unhelpful path, it is a **wrong** one.
- **How a request is actually served:**
  - **Gate email** — the one identified surface. Removed from the Access
    allowlist, **and a vendor-side deletion request filed with Cloudflare.**
    ✅ **RULED (Cray, typed, 2026-08-15): yes, matching the sibling.** Without it
    the promise would be incomplete by construction — the email address lives at
    Cloudflare, not with us, so erasing our side alone leaves the one genuinely
    identified field untouched.
  - **Case text and photos** — located by **content search** over case rows and
    the upload directory, using whatever the requester can tell us they typed or
    uploaded, then erased with the per-case unit `delete_case()` (§6), which
    removes the row, its FK children and the files together.
- **The honest statement:** if a visitor typed something identifying and cannot
  recall it, **we cannot find it**, because nothing stored links a case to a
  person. Erasure of the whole dataset within 90 days is automatic regardless.
- 🔴 **What cannot be promised — stated rather than omitted. Two separate things,
  and they must never be blended.** ✅ **RULED (Cray, typed, 2026-08-15).**
  1. **The visitor's case text IS erasable**, and erasing it leaves only an
     opaque, unresolvable id in the audit chain — with both halves of the reason
     stated at §6.
  2. **The recorder's own free text is NOT erasable.** `WaiverInvocation.justification`
     and the ratification `note` are written by a **named internal principal** —
     an operator recording why an exception was granted — not by the visitor, and
     they live in the audit chain itself.
     ⚠️ **Blending these two into one sentence would produce a false promise**, in
     whichever direction it leaned: it would either claim erasure covers text it
     does not, or deny erasure of text it does cover. That is why this appears as
     its own numbered item and not as a qualifier on the item above.
- **Every DSR action is noted in §9** — the record is the evidence.

> **Lineage hook.** DSR feasibility here is bounded by an intentional absence of
> identity — the same trade the sibling makes — but with one added hazard the
> sibling does not have: a field that invites a lookup which would be wrong.
> Naming that hazard is the point of this section.

## 9. DSR + purge action log

Append one row per action. Empty is the correct state before exposure.

| Date | Action | Scope | Requester (if DSR) | Vendor request filed | By |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

---

*PLAN-0103 AC-11; obligation per ADR-0037 D2.1. Sibling instance to
`ropa-published-demo.md` per Cray's typed ruling of 2026-08-14. Retention (90
days from `opened_at`) is PLAN-0105's shipped control, restated here, not
re-decided. Engineering inputs and their evidence:
[`ropa-change-statement-fleet.md`](ropa-change-statement-fleet.md) §6 —
⚠️ note that document's §2 is written in an "extend the existing file" frame that
the sibling-instance ruling superseded.*
