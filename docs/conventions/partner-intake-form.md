# Partner intake form (v2) — first-dataset requirements for a real design partner

> **What this is.** The questionnaire we put to a **real** design partner to get
> first-dataset input that is **mapping-ready** — i.e. that drops into the
> canonical ontology/engine with minimal reverse-engineering. v2 is derived from
> the **partner-sim run-1 mapping rehearsal**
> (`docs/strategy/public/partner-sim-run1-mapping-analysis.md`): every section
> below exists because the rehearsal showed the v1 one-pager left a real mapping
> gap. **Canonical, tracked.** (Distinct from two gitignored siblings: the v1
> partner-facing one-pager and the R1-clean *partner-sim* seed, both under
> `docs/research/private/`.)
>
> **Design principle.** Elicit the partner's operation in *their own* terms but
> in a **structured shape** (per-parameter / per-asset-type / per-action) that we
> can map. We do **not** impose our taxonomy on them; we ask for theirs in slots
> we can absorb.
>
> **Applicability tags.** `[generic]` = vertical-agnostic ask · `[energy]` =
> energy-specific phrasing/example. Energy-first; generalize only after a
> 2nd/3rd real vertical (Rule of Three — do not over-abstract now).

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

## C. Per-parameter reading spec `[generic]` — *the core of v2*

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

## G. Volumes & cadence `[generic]`

13. Asset count; events/day (and seasonal swing); how data leaves your systems
    (**batch export vs stream**); any system that **can't export** at all
    (screenshot / re-key only).

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

---

## How this maps onward (for us, not the partner)

- **C/D/E** → the multi-parameter procedure + the `classify_verdict` bands + the
  `RecommendedAction.action_type` vocabulary (extends `verticals/<v>/`).
- **B (ID reuse)** → `Asset.install_date` / a valid-from disambiguator.
- **F/H** → the mapping layer's raw→canonical **lineage**; **H14–H16** →
  ADR-011 audit framework §Context (approval-chain enforcement, log-by-reference,
  actor unification).

## Provenance & status

Derived from one **synthetic** run (ADR-0020 R3 — informs, does not trip the
first-real-data trigger). v2 supersedes the v1 one-pager for *real* partner use;
expect a v3 after the first real conversation (it will surface gaps the sim
didn't). Evidence + full mapping table:
`docs/strategy/public/partner-sim-run1-mapping-analysis.md`.

_Sync note: this is a canonical repo instrument; if it is ever pasted into a
partner-facing doc or a Claude project, the repo copy wins (CLAUDE.md §4)._
