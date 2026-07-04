# Partner intake form (v3) — first-dataset requirements for a real design partner

> **What this is.** The questionnaire we put to a **real** design partner to get
> first-dataset input that is **mapping-ready** — i.e. that drops into the
> canonical ontology/engine with minimal reverse-engineering. v2 was derived from
> the **partner-sim run-1 mapping rehearsal**; **v3 adds 11 questions** surfaced by
> the **two** partner-sim mapping rehearsals (run-1 §5 items 1–7 + run-2 §6 items
> 8–11). **Canonical, tracked.** (Distinct from two gitignored siblings: the v1
> partner-facing one-pager and the R1-clean *partner-sim* seed, both under
> `docs/research/private/`.)
>
> **What changed v2 → v3.** Eleven additions, each tagged **`[v3]`** and folded into
> the section it extends (B / C / F / G / H), each traceable to its rehearsal source
> as **`V1`–`V11`**. Nothing from v2 was removed. The additions exist because *messiness*
> only surfaced in the two rehearsals (identity you can't stand behind, renumbered IDs,
> per-source clock drift, corrections applied only in operators' heads, vendor-cloud
> auto-uploads, shareable proxies for withheld fields). See the `[v3] additions` block
> at the end of each affected section.
>
> **Design principle.** Elicit the partner's operation in *their own* terms but
> in a **structured shape** (per-parameter / per-asset-type / per-action) that we
> can map. We do **not** impose our taxonomy on them; we ask for theirs in slots
> we can absorb.
>
> **Applicability tags.** `[generic]` = vertical-agnostic ask · `[energy]` =
> energy-specific phrasing/example. Energy-first; generalize only after a
> 2nd/3rd real vertical (Rule of Three — do not over-abstract now).
>
> **Provenance note (read before borrowing examples).** The two rehearsal runs this
> v3 draws from are **SYNTHETIC-labeled** (ADR-0020 R3). The *questions* are real
> engineering inputs (a questionnaire is not data), so v3 needs no synthetic banner —
> but any **example value** below is **generic / illustrative**, never presented as a
> real partner fact.

---

## A. People & authority `[generic]`

1. **Org + authority matrix** — roles, and **who may approve which action, with
   the real limit** (e.g. "[energy] shift supervisor may reset a recloser once on
   a non-anchor feeder ≤ X MVA; anything touching an anchor customer needs the
   duty manager"). Include the escalation trigger per row.
2. **Current approval workflows** — 2–3 real examples as they run *today*
   (paper / chat app / email / legacy screen), including the friction (who's
   slow, what gets skipped off-hours, what's back-filled).
3. **A named data owner** — one person who can answer data questions without
   convening a committee. If none exists, say so (it's a finding).

## B. Asset & site taxonomy `[generic]`

4. **Enumerate your asset types** in your own words (e.g. [energy] feeder /
   transformer / recloser / RMU / switching-station) — we extend our model to
   yours, we do **not** ask you to fit ours.
5. **Enumerate your site/location types.**
6. **ID stability** — are asset/site IDs ever **reused** (e.g. after a rebuild)?
   Since when? Is there an install/commission or **valid-from date** that
   disambiguates an ID over time?

**`[v3]` additions to Section B:**

- **`V2` `[v3]` ID-stability *history*** — beyond "are IDs reused": have asset/site
  codes ever been **renumbered** wholesale (e.g. [energy] a transformer-ID renumber in
  a past year; a device-fleet renumber)? **Since when, and where does the old→new
  mapping live** — a spreadsheet, a printed map, or only in one person's head? (Reused
  *and* renumbered IDs both break time-series joins unless we get the mapping. Source:
  run-1 §5 #2 / F1.)

## C. Per-parameter reading spec `[generic]` — *the core of v2 (and still v3)*

> The single most important section. For **each** reading your team monitors,
> give us one row. (The v1 form asked for "thresholds" generically; the rehearsal
> showed real operators run several parameters, each two-tier, each with its own
> action — see mapping-analysis headline #1.)

| reading (your name) | unit (explicit) | "watch" threshold (start paying attention) | "act" threshold (you take action) | direction (high-bad / low-bad) | the action you take | who approves it |
|---|---|---|---|---|---|---|
| _[energy] e.g. feeder load_ | _MVA_ | _6.4_ | _7.6_ | _high-bad_ | _loadshed / isolate_ | _duty manager_ |
| _[energy] e.g. oil temp_ | _°C_ | _96_ | _104_ | _high-bad_ | _dispatch + consider loadshed_ | _duty manager_ |
| _[energy] e.g. voltage_ | _kV_ | _20.6 (under)_ | _…_ | _low-bad_ | _…_ | _…_ |

7. Fill one row per parameter. **Units must be explicit** — and flag if any
   legacy export column carries **mixed units** (e.g. some rows Amps, some MVA)
   or **raw/uncalibrated** values (e.g. raw ADC counts vs °C).

**`[v3]` additions to Section C:**

- **`V4` `[v3]` Band shape — seasonal / conditional thresholds + tier count** — do any
  of your watch/act thresholds **vary by season or operating condition** (e.g. a summer
  vs winter limit)? **How many escalation tiers** does each parameter have (just
  watch/act, or more)? (v2's table assumes two fixed tiers; real operators volunteered
  seasonal bands and extra tiers. Source: run-1 §5 #4 / F5. Tier count also touches
  Section E.)
- **`V10` `[v3]` Undocumented corrections** — **what numbers does your team mentally
  adjust before acting?** (e.g. [generic] "probe X reads +0.4 high", "room 3 runs −1.2").
  These silent corrections live in operators' heads; **the mapping layer must know them,
  or it will mis-read your raw values.** (Source: run-2 §6 #10. Pairs with Q7's
  raw/uncalibrated flag.)
- **`V11` `[v3]` Band SHAPE probes** — does any rule have **a time component**
  (sustained-for-X, within-X-hours)? **a two-sided range** (bad if too high *and* if too
  low)? or **a threshold that differs by customer contract**? (Completes the band-shape
  survey run-1 #4 started; these shapes don't fit a single watch/act pair and need
  explicit capture. Source: run-2 §6 #11.)

## D. Actions & their meaning `[generic]`

8. **List every action your team takes** in response, each with: a **one-line
   meaning** (e.g. [energy] "restart" = *reset the auto-recloser*, not power-cycle
   an asset), and the **approval limit/scope**. (We bind your action vocabulary
   deliberately; do not assume a word means what a vendor assumes — mapping
   headline #2.)

## E. Status / severity encoding `[generic]`

9. **Do you have a status or severity field, or is the judgment carried in
   free-text?** Give us your **status vocabulary** (e.g. [energy] ปกติ / เฝ้าระวัง /
   เกินพิกัด) **and the numeric rule behind each word** (which reading + threshold
   makes it "เฝ้าระวัง"). This is what lets us reproduce your call, not guess it.
   *(v3 note: if your bands have extra escalation tiers — see `V4` in Section C —
   list a status word for each tier.)*

## F. The data itself — a time window with edge cases `[generic]`

10. A **continuous period** (not a snapshot) of real events spanning **normal /
    near-limit / over-limit**, *including* real defects: missing values, unit
    drift, duplicates, out-of-order or back-filled timestamps. Don't clean it.
11. **Timestamp reliability** — how are timestamps recorded (device clock /
    manual / back-filled)? Any known **drift or outage periods** (e.g. [energy]
    NTP drift) where ordering can't be trusted? (Audit lineage depends on this.)
12. **Completeness** — are any event types **systematically under-recorded**
    (e.g. fixed quietly off-system to avoid an SLA penalty record)? We need to
    know the log isn't assumed complete.

**`[v3]` additions to Section F:**

- **`V3` `[v3]` Clock discipline *per source*** — for **each** feeding system: **what
  timezone**? Any **known drift** (and roughly how much per month)? **Who, if anyone,
  resets device clocks** — and how often? Are any timestamps **unlabeled** (no TZ
  offset) or in a **non-Gregorian calendar** (e.g. [energy] พ.ศ. / Buddhist-era years)?
  (v2's Q11 asked "reliability" broadly; the rehearsals showed clock behavior differs
  *per source* — per-station TZ splits, minutes/month drift, ambiguous DD/MM — so we
  must ask per system, not once. Source: run-1 §5 #3 / F4.)

## G. Volumes & cadence `[generic]`

13. Asset count; events/day (and seasonal swing); how data leaves your systems
    (**batch export vs stream**); any system that **can't export** at all
    (screenshot / re-key only).

**`[v3]` additions to Section G:**

- **`V5` `[v3]` Export reliability** — does the export job ever **fail or silently drop
  rows**? When there's a gap, is it **back-filled** — and critically, **is the back-fill
  marked as such**, or is it indistinguishable from real-time data once it lands? (An
  unmarked back-fill corrupts audit lineage silently. Source: run-1 §5 #5 / F6. Pairs
  with F12 completeness.)

## H. Privacy, identity & delivery `[generic]`

14. **Field classification** — tag every field **PII** (e.g. operator name,
    shift roster, driver location) / **business-confidential** (customers,
    pricing, protection settings) / **plain**.
15. **Free-text & embedded PII** — which fields are **free-text**, and may
    contain names/customers inside the text (these need log-by-reference, and
    drive a data-subject-rights/lineage challenge).
16. **Actor identity** — where is "**who did what**" recorded? One system, or
    several **unlinked** places (paper / shift log / chat / email)? (Feeds the
    audit framework — ADR-011.)
17. **Delivery terms** — under a **DPA** (purpose, dev/test only, no re-share,
    delete at trial end); first cut **pseudonymized** (stable token per person,
    JOINs + distributions preserved); full-fidelity only at on-site deploy.

**`[v3]` additions to Section H:**

- **`V1` `[v3]` Identity *reliability*, not just existence** — beyond Q16's "where is
  who-did-what recorded": **which identity records can you actually stand behind, per
  shift / per channel?** (Rehearsals surfaced shared logins, "borrowed" chat-app
  identities, and retro-approvals — an ID can *exist* and still not be trustworthy as
  the actor. Source: run-1 §5 #1 / F2. Feeds ADR-0026 "identity unavailable" handling.)
- **`V6` `[v3]` Degraded-mode alternates for refusals** — **for each field you can't
  share, what's the closest shareable proxy?** (e.g. [energy] no GPS → a facility
  geofence or schematic-topology mode; no customer map → feeder-level impact only.)
  Degraded-mode design per refused field is the **norm**, not the exception — so we ask
  for proxies up front. (Source: run-1 §5 #6 / F11.)
- **`V7` `[v3]` Pseudonymization capability** — **can your side pseudonymize before
  export?** We ask rather than assume; **if not, we can offer our tool to run on your
  side.** (Source: run-1 §5 #7 / F8-WI-8c. Extends Q17's pseudonymized-first-cut term.)
- **`V8` `[v3]` Source ownership map** — for **each** system feeding this data: **who
  owns it, and can you legally share it?** (JV boards, third-party shipping/field agents,
  and vendor-hosted systems all change the legal answer — ownership ≠ the operator by
  default. Source: run-2 §6 #8.)
- **`V9` `[v3]` Sub-processor / vendor-cloud inventory** — **which of your systems
  auto-upload to a vendor's cloud, and where does that data physically land?** (A feeding
  system quietly syncing to an offshore vendor cloud is a cross-border-transfer + residency
  surprise we must catch before ingest. Source: run-2 §6 #9. Ties to the residency posture —
  see the Wave-3 GTM ammo pack "compute never leaves".)

---

## How this maps onward (for us, not the partner)

- **C/D/E** → the multi-parameter procedure + the `classify_verdict` bands + the
  `RecommendedAction.action_type` vocabulary (extends `verticals/<v>/`).
  - **`V4` / `V11` (band shape)** → band-expressiveness requirements (seasonal /
    duration-qualified / two-sided / context-scoped) → the generalized procedure schema
    (Stage-2→3 thread).
  - **`V10` (undocumented corrections)** → the mapping layer's calibration/bias
    registry (per-source scale + offset, preserve raw + corrected lineage).
- **B (ID reuse)** → `Asset.install_date` / a valid-from disambiguator.
  - **`V2` (ID-stability history)** → era-scoped surrogate keys + a mapping-elicitation
    onboarding task (the old→new mapping is an artifact we must capture, not assume).
- **F/H** → the mapping layer's raw→canonical **lineage**; **H14–H16** →
  ADR-011 audit framework §Context (approval-chain enforcement, log-by-reference,
  actor unification).
  - **`V3` (per-source clock)** → per-source time config + uncertainty windows +
    sort-by-timestamp-not-file-order.
  - **`V5` (export reliability)** → versioned/bitemporal-lite ingest + a marked-backfill
    flag on the canonical event.
  - **`V1` (identity reliability)** → ADR-0026 "identity unavailable" resolution class +
    role-level-audit pre-clearance mode.
  - **`V6` (degraded-mode proxies)** → per-refused-field product/UI degraded modes
    (schematic topology; feeder-level impact) — a demo-card trigger.
  - **`V7`–`V9` (pseudonymization / ownership / vendor-cloud)** → DPA template musts
    (ingest-source pinning, deletion scope, sub-processor disclosure) → the GTM DPA pack.

## Provenance & status

Derived from **two synthetic runs** (ADR-0020 R3 — inform, do not trip the first-real-data
trigger): run-1 (energy) contributed v2 + additions `V1`–`V7`; run-2 (cold-chain)
contributed additions `V8`–`V11`. The run-2 rehearsal's own work item **G10** routes its
§6 items into this standard form. **v3 supersedes v2 for *real* partner use**; expect a
**v4** after the first real partner conversation (it will surface gaps neither sim did).
Evidence + full mapping tables:
`docs/research/private/2026-07-02-partnersim-run1-rehearsal-intake-mapping-pdpa.md` (§5) and
`docs/research/private/2026-07-03-partnersim-run2-rehearsal-intake-mapping-pdpa.md` (§6).

_Sync note: this is a canonical repo instrument; if it is ever pasted into a
partner-facing doc or a Claude project, the repo copy wins (CLAUDE.md §4)._
