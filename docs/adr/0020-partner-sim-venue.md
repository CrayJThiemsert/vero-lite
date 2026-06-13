# ADR-0020: Synthetic Design-Partner Simulation Venue (partner-sim)

**Status:** Accepted
**Date:** 2026-06-13
**Deciders:** Jirachai Thiemsert (founder)
**Related:** ADR-009 (tier topology — partner-sim sits **outside** these tiers), ADR-012 (venue-via-ADR *guarded-trial* pattern this ADR mirrors), ADR-013 (advisory-drafter framing; "only Code commits" reinforced), ADR-005 (energy = primary / supply chain = secondary partner type), ADR-011 (earmarked audit framework — partner-sim's R3 means its output does **not** trip ADR-011's "first real partner data" gate), PLAN-0005 §8.1 (deferred-foundational ladder — triggers unchanged), PLAN-0022 (M-2=b calibration-first precedent — ground truth must not be authored by the system under test), seed instruments `docs/research/private/2026-06-13-partnersim-seed-r1clean.md` (R1-clean partner-sim input — D2/R1) + `docs/research/private/2026-06-13-first-dataset-requirements.md` (partner-facing one-pager, not pasted to partner-sim) + `docs/research/private/2026-06-13-pdpa-review-checklist.md`, authoring dispatch `.claude/handoffs/session-57/2026-06-13-0853-code-partnersim-cowork-dispatch.md`, errata dispatch `.claude/handoffs/session-57/2026-06-13-1009-code-r1cleanseed-cowork-dispatch.md`

> **Ratified — 2026-06-13 (Accepted).** Cray ratified in-session ("เอาตาม
> Cowork ทุกข้อ"): **Proposed → Accepted**, accepting **all four** venue SD
> recommendations (SD-1..SD-4) verbatim **and** dispatch-SD-1 (trim the real
> one-pager). The four SD adjudications are folded into D2/D3/D4 below and
> recorded in the "Ratified 2026-06-13" record (formerly "Surfaced for Cray").
> **No R1/R2/R3 substance changed at ratification** — the 2026-06-13 errata
> already settled those; this step only resolves the four open SDs. Cowork
> authored the fold (ADR-009 D1, retained as advisory per ADR-013); Code
> reviews + commits and runs the STATUS T3 reconcile (ADR-009 D2 / ADR-013 D2).
>
> **Drafting history (pre-ratification).** Shipped **Proposed** on an in-session
> go to *build the package* (2026-06-13, "ดำเนินการ (a) ได้ เพราะเราเห็นด้วย");
> ratification to Accepted was held as a separate step (now done, per the note
> above).
>
> **Amendment — 2026-06-13 (pre-ratification; status still Proposed).** An R2
> verification pass before ratification found a self-contradiction. R1 said
> partner-sim is never given our action vocabulary, yet the document the run
> procedure pasted every run — the **partner-facing first-dataset one-pager**
> (`2026-06-13-first-dataset-requirements.md`) — carries our 3-band verdict
> taxonomy *and* action vocabulary, so R1 was defeated **at the paste step**
> (normal procedure, not an oversight), and Consequences/Positive actually
> *relied* on that leak. Three coupled fixes applied here (status unchanged —
> Cray ratifies the corrected draft): **(1)** R1 now requires a **dedicated
> R1-clean seed** (`2026-06-13-partnersim-seed-r1clean.md`) as the only
> first-dataset document cleared for the paste, and states that "no repo mount"
> insulates against repo reads but not against a leaky paste; **(2)**
> Consequences/Positive no longer claims the seed pre-bakes the verdict bands —
> Code maps them on receive; **(3)** R-PS1 records the named breach vector
> (one-pager-instead-of-seed paste). Authored by Cowork per ADR-009 D1; Code
> reviews + commits.

## Context

The audit-framework prep batch (`auditprep`, session 57) produced two
partner-facing instruments — a first-dataset requirements one-pager and a
PDPA review checklist (vero-lite = processor). They are ready, but a **real**
design-partner conversation is weeks out. The intake + mapping + PDPA pipeline
those instruments feed is therefore untested against anything but our own
clean fixtures (the Build-Vertical narratives, session 54), and the first time
it would meet messy reality is the **highest-stakes** moment — first real
partner data. That is the worst time to discover a gap.

Cray's proposal: a **synthetic design partner** — a specialist Cowork project
that role-plays a senior operations decision-maker at a Thai operator and
produces a realistically messy "partner profile package." We feed it the
first-dataset one-pager + PDPA checklist + a business-type brief, and it
answers as a real counterpart would — including refusals, IT debt, legacy
systems, and budget politics. We then rehearse intake, mapping, and the PDPA
RoPA against that material before the real conversation.

### The trap this design must avoid

If the system under test also authors its own ground truth, the test is
circular. PLAN-0022 (M-2=b, calibration-first) settled the project's position
on exactly this: watch-tier ground truth was **pinned from the run
distribution**, never authored by the grader. The same discipline applies
here. If partner-sim is given our ontology, engine internals, or the
benchmark's canonical/acceptable action keys, it will "helpfully" produce
material that already matches our schema — and the schema-mismatch discovery
that is the **entire point** of the rehearsal can no longer emerge. The
insulation (R1 below) is the design.

A second trap is provenance. Synthetic material that leaks unlabeled into a
benchmark, REPORT, or the ADR-011 audit-framework trigger context would
corrupt a real measurement or prematurely trip a real-data gate. R3 below is
the reason this decision lives at ADR level rather than in a skill or note
(Lesson #24 — a binding rule must live where the enforcer looks; here the
enforcers are the SYNTHETIC banner and Code-on-receive).

## Decision

partner-sim is adopted as a **guarded trial** (mirroring the ADR-012 venue
pattern): scoped to one business type for run 1, with pre-declared
regression/exit triggers (D4).

### D1 — Venue status: a specialist simulation project, OUTSIDE the governance tiers

partner-sim is **not** a new collaboration tier and does **not** sit inside
the ADR-009/012/013 topology. It produces **research/fixture data only**:

- It never authors governance artifacts (no ADRs, PLANs, dispatches).
- It never commits and never instructs another tier (ADR-009 D2 / ADR-013 D2
  unchanged; it has no git path and no repo mount — see the system
  instruction).
- Its output enters the repo **exclusively through Code receive**: Code
  validates, re-stamps timestamps (K-1), applies R2 review, and lands the
  package under `docs/research/private/`. partner-sim adds **no new repo
  write scope**.

It is, in effect, a Tier-0-shaped *content source* that the project treats as
an untrusted external party by construction — which is the point.

### D2 — The three anti-circularity rules (BINDING)

- **R1 — feed questions, not schema; and the inputs are themselves
  R1-screened.** partner-sim's inputs are a **dedicated R1-clean seed**
  (`docs/research/private/2026-06-13-partnersim-seed-r1clean.md`), the PDPA
  checklist, and a business-type brief (D3). It is **never** given our ontology
  YAML, `services/**` engine internals, benchmark expectations, or the
  canonical/acceptable/forbidden action vocabulary. **The seed pasted to
  partner-sim is NOT the partner-facing first-dataset one-pager**
  (`docs/research/private/2026-06-13-first-dataset-requirements.md`): that
  one-pager carries our verdict taxonomy and action vocabulary for the *real*
  partner conversation, and pasting it would hand partner-sim the very schema
  R1 withholds. Schema mismatch must be free to emerge — that mismatch is the
  discovery value (same trap-class as M-2 pinning circularity, PLAN-0022).
  Enforced **structurally and procedurally**: the project has **no repo mount**
  (it can read only what Cray pastes), which insulates against repo *reads* —
  but it does **not** insulate against a leaky *paste*. The R1-clean seed is
  the procedural half of the control: the only first-dataset document cleared
  for the partner-sim paste.
- **R2 — forced messiness.** The persona must produce realistically flawed
  material: missing values, unit inconsistencies, hand-maintained
  spreadsheets, legacy-system constraints, "ต้องไปถามทีม IT ก่อน"
  non-answers, and **at least 3 unsolicited inconvenient facts per round**
  (N = 3, ratified 2026-06-13 per SD-1). Clean, schema-shaped output is a
  trial failure (R-PS3), not a success — we already have clean fixtures.
- **R3 — SYNTHETIC provenance.** Every artifact carries a SYNTHETIC banner
  (verbatim text in the system instruction). partner-sim output **never
  satisfies any "first real partner data" trigger** — PLAN-0005 §8.1 ladder
  and the ADR-011 audit-framework gate are unchanged — and **never enters a
  REPORT / benchmark / governance context unlabeled**. This rule is the
  reason the ADR exists; it is binding and lives at ADR level, not in a
  skill or note.

### D3 — I/O protocol

- **Input:** a business type plus parameters — **size / region /
  digital-maturity** (vocabulary ratified 2026-06-13 per SD-3:
  `size ∈ {small <50 assets, mid 50–500, large >500}`;
  `region ∈ {th-central, th-regional, multi-site-sea}`;
  `digital_maturity ∈ {paper-first, spreadsheet-first, mixed-legacy, modern-stack}`)
  — together with the **R1-clean seed**
  (`2026-06-13-partnersim-seed-r1clean.md`, **not** the partner-facing
  one-pager — R1) and the PDPA checklist, all pasted by Cray at run start.
  **Run-1 default (ratified per SD-3): energy / mid / th-regional /
  mixed-legacy** (`mixed-legacy` maximizes the R2 messiness we want to
  exercise).
- **Output:** a **partner profile package** returned as a standard
  **completion handoff** — `actor: cowork`, `batch: partnersim-<type>`,
  `phase: closeout`, `suffix: completion` — using the **existing** validator
  and schema. **No enum changes** are required (`Actor` already includes
  `cowork`; the completion shape reuses the auditprep precedent of
  `phase: closeout` + `suffix: completion`). The package **must include a
  "what we refused to share" section** (ratified-required 2026-06-13 per
  SD-4): modeling refusal — IT-security policy, data-egress rules, "legal
  hasn't cleared this" — is exactly the PDPA-processor-boundary / DPA-scope
  friction the intake pipeline must handle, and it pressure-tests the
  DSR/lineage assumptions when a field is withheld (PDPA checklist §5/§3).
  partner-sim has no repo mount and cannot write to disk, so it **emits the
  handoff as text**; Cray relays it; Code re-stamps the `created`/filename
  timestamp on receive (K-1) and lands the package.

### D4 — Lifecycle (guarded trial) + regression/exit triggers

First run is scoped as an experiment on **energy operator** (ADR-005 primary
partner type). **Topology ratified 2026-06-13 (per SD-2): one project per
business type** — a fresh project per type so the energy run cannot leak into
a later supply-chain run (context bleed = R-PS4); projects are cheap (seeds
are pasted fresh each run regardless). With only energy scoped for run 1, this
first bites at the second business type. **Review after run 1 before any
second business type.** Pre-declared triggers (any one re-opens this decision —
mirrors ADR-012 D5):

- **R-PS1 — circularity leak.** Output mirrors our schema/action vocabulary,
  implying R1 was breached by an input paste; the intake test becomes
  non-informative. **Known breach vector (named 2026-06-13):** pasting the
  partner-facing first-dataset one-pager instead of the R1-clean seed — the
  one-pager carries our verdict taxonomy and action vocabulary. If output
  mirrors our schema, **screen the pasted inputs first**: confirm the R1-clean
  seed (not the one-pager) was the document pasted at run start.
- **R-PS2 — provenance leak.** A SYNTHETIC artifact appears unlabeled in a
  benchmark / REPORT / ADR-011 trigger context (R3 breach).
- **R-PS3 — insufficient messiness.** Output is too clean to exercise the
  mapping/PDPA path; partner-sim degenerates into a clean-fixture generator
  we already have (Build-Vertical narratives).
- **R-PS4 — context bleed** (SD-2 ratified one-project-per-type pre-empts this
  by construction; retained as a guard against a project being reused across
  types). A later business-type run inherits the prior run's specifics,
  collapsing run-to-run independence.

If a trigger fires, the de-scope target is **strict one-project-per-type
enforcement** (if R-PS4 — already the ratified baseline per SD-2) or
retirement to a one-off fixture generator (if R-PS3) — not expansion.

## Ratified 2026-06-13 (per Cray — all four SDs accepted per Cowork rec)

Cray ratified all four venue SDs verbatim ("เอาตาม Cowork ทุกข้อ"); each is
folded into the binding decision noted and recorded here for provenance.

- **SD-1 — N unsolicited inconvenient facts per round = 3** (folded into
  D2/R2). Three guarantees coverage of the project's three friction surfaces
  (people / data / process) and matches the "rule of three" already used as
  a discovery threshold; fewer than three risks a single, easily-dismissed
  fact; many more per round buries the signal in noise. **Ratified N = 3.**
- **SD-2 — one project per business type** (folded into D4). Context bleed
  between runs is a real circularity risk (R-PS4); a fresh project guarantees
  the energy run cannot leak into a later supply-chain run, and projects are
  cheap (seeds are pasted fresh each run regardless). With only energy scoped
  for run 1, this first bites at the second type. **Ratified one-per-type.**
- **SD-3 — parameter vocabulary for the business-type brief** (folded into D3).
  *Ratified enums:* `size ∈ {small <50 assets, mid 50–500, large >500}`;
  `region ∈ {th-central, th-regional, multi-site-sea}`;
  `digital_maturity ∈ {paper-first, spreadsheet-first, mixed-legacy, modern-stack}`.
  *Ratified run-1 default:* energy / mid / th-regional / mixed-legacy
  (most realistic for the primary partner type; `mixed-legacy` maximizes the
  R2 messiness we want to exercise). **Ratified.**
- **SD-4 — include a "what we refused to share" section: yes** (folded into D3
  output, ratified-required). A real partner refuses things — IT-security
  policy, data-egress rules, "legal hasn't cleared this." Modeling refusal is
  exactly the PDPA-processor-boundary and DPA-scope friction the intake
  pipeline must handle, and it pressure-tests our DSR/lineage assumptions when
  a field is withheld (PDPA checklist §5/§3). **Ratified yes.**

**dispatch-SD-1 (separate series) — trim the real partner-facing one-pager:**
ratified; done in this batch. The `…-first-dataset-requirements.md` sector
callout's forbidden-action `หมายเหตุระบบ` (reroute/expedite-ต้องห้าม +
benchmark structure) is removed and the legitimate near-limit-rationale ask is
retained; the R1-clean seed (`…-partnersim-seed-r1clean.md`) is untouched.

## Consequences

### Positive

- Rehearses the intake / mapping / PDPA path **weeks before** a real partner,
  surfacing schema mismatch early and cheaply rather than at first-real-data.
- Produces realistic operational fixtures spanning **problem / near-problem /
  normal situations as the partner describes them** — **but SYNTHETIC**, so
  they inform without being scored as real. **Code maps them to our internal
  verdict bands on receive**; that mapping is itself part of the rehearsal
  value and is **not** pre-baked into the seed (R1 — the R1-clean seed never
  hands partner-sim our verdict taxonomy or any "ground truth").
- Builds the partner-trust narrative (RoPA-lite, residency story, refusal
  handling) as concrete artifacts before the meeting.

### Negative

- Synthetic data can only encode the messiness we have already imagined; it
  will miss real-world surprises (blind-spot risk — partial mitigation: R2's
  forced inconvenient facts deliberately push beyond the obvious).
- R3 provenance discipline is a standing burden: one unlabeled leak corrupts a
  benchmark or trips a real-data gate.
- Adds a Cowork-shaped surface to keep mode-disciplined, even though it sits
  outside the tiers.

### Neutral

- **No schema/enum change**, no new repo write scope, ADR-011 + PLAN-0005
  §8.1 ladder unchanged. The first-real-partner triggers stay exactly where
  they are; partner-sim is explicitly upstream of them (R3).

### Required follow-on commits (TODOs for Code — separate commits)

This ADR is a draft; Cowork has no commit authority (ADR-009 D2 / ADR-013 D2)
and cannot write `docs/conventions/**`. None of these edits are made here:

1. **T1 — Commit this ADR** to `docs/adr/0020-partner-sim-venue.md` at status
   **Proposed**.
2. **T2 — Relocate + commit the system instruction.** Cowork staged the
   instruction body at
   `docs/research/private/2026-06-13-partnersim-project-instructions-draft.md`
   (writable) because `docs/conventions/**` is outside Cowork write scope —
   **see the scope flag in the companion completion handoff §Flag.** Code
   moves it to `docs/conventions/partnersim_project_instructions.md`
   (Code-amends-conventions per ADR-009 D2) and commits. Sync target =
   the new Cowork project's "project instructions" field (same
   canonical-in-repo / paste-to-UI model as `{chat,cowork}_tab_instructions.md`).
3. **T3 — Ratification (status flip + SD fold APPLIED 2026-06-13 by Cowork in
   this revision):** ADR flipped Proposed → **Accepted**; SD-1..SD-4 folded
   into D2/D3/D4; the "Surfaced for Cray" section converted to the dated
   "Ratified 2026-06-13" record. **Remaining for Code:** record the topology
   addition in `docs/STATUS.md` (Recent Decisions + In-Flight Discussions —
   this venue is a guarded trial like ADR-012), reconcile the instruction
   file's SD-finalization language to "ratified", and commit. Cowork has no
   STATUS / commit authority (ADR-009 D2 / ADR-013 D2).
4. **T4 — ADR number:** **0020** verified free at HEAD `2331ffb` (0000–0019
   exist incl. `0014-WITHDRAWN`; `0011` stays earmarked for the audit
   framework; `0019` is newest). No renumber needed.

## Alternatives Considered

### Alternative A: Standalone synthetic-partner project, insulated by R1 (CHOSEN)

- **Pros:** maximal author≠ground-truth independence (R1, enforced by
  no-repo-mount); reuses the existing handoff/receive path; no new write
  scope; reversible (guarded trial).
- **Cons:** synthetic ≠ real (blind-spot risk); standing R3 provenance
  burden.
- **Why chosen:** it is the only option that rehearses the pipeline now
  *without* collapsing the independence the M-2=b precedent requires.

### Alternative B: Generate the fixtures directly in Cowork Tier-0 research

- **Pros:** simpler; no new venue.
- **Cons:** the tier that knows our schema would author the "partner" data →
  the exact M-2 circularity trap (PLAN-0022); schema mismatch could never
  surface.
- **Why rejected:** defeats the discovery purpose.

### Alternative C: Wait for the real partner

- **Pros:** real data, no synthetic blind spots.
- **Cons:** weeks of idle pipeline; the intake/PDPA path goes untested until
  first real data — the highest-stakes, worst-possible moment to find a gap.
- **Why rejected:** partner-sim *informs* the real conversation, it does not
  replace it (R3) — so waiting buys nothing the real run still gives later.

### Alternative D: One shared multi-type project

- Captured as **SD-2** (context-bleed risk R-PS4), not a separate top-level
  alternative; Cray adjudicates.

## References

- **ADR-009** (`docs/adr/0009-cowork-tier1-tier-topology.md`) — tier
  topology partner-sim sits outside; D2 commit boundary
- **ADR-012** (`docs/adr/0012-cowork-second-freeform-tier.md`) — venue-via-ADR
  guarded-trial pattern (D5 regression triggers) mirrored here
- **ADR-013** (`docs/adr/0013-autonomy-axis-relocation.md`) — advisory-drafter
  framing; D2 deterministic "only Code commits"
- **ADR-005** (`docs/adr/0005-strategic-pivot-to-oct.md`) — energy primary /
  supply chain secondary
- **ADR-011** (earmarked, audit framework) — partner-sim output does **not**
  trip its first-real-data trigger (R3)
- **PLAN-0005 §8.1** — deferred-foundational ladder; audit-framework trigger =
  *first design-partner data / PDPA review* (real, not synthetic)
- **PLAN-0022** (`docs/plans/done/0022-tiered-decision-routing.md`) — M-2=b
  calibration-first: ground truth must not be authored by the system under test
- **Seed instruments:**
  `docs/research/private/2026-06-13-partnersim-seed-r1clean.md` (the
  **R1-clean partner-sim input** — D2/R1; the only first-dataset document
  cleared for the partner-sim paste),
  `docs/research/private/2026-06-13-first-dataset-requirements.md` (the
  partner-facing one-pager — **NOT** pasted to partner-sim),
  `docs/research/private/2026-06-13-pdpa-review-checklist.md`
- **Lesson #24** (`docs/lessons/0024-rules-must-live-where-the-enforcer-looks.md`)
  — why R3 lives at ADR level
- **Build-Vertical narratives** (session 54) — LLM-generated operational
  fixture precedent; the clean-fixture baseline R-PS3 guards against
  regressing to
- **CLAUDE.md** §8 (PDPA / residency / assistive-only)
- **Authoring dispatch:**
  `.claude/handoffs/session-57/2026-06-13-0853-code-partnersim-cowork-dispatch.md`
- **Errata dispatch (R1-clean seed + this pre-ratification fix):**
  `.claude/handoffs/session-57/2026-06-13-1009-code-r1cleanseed-cowork-dispatch.md`
- **R1-clean seed (partner-sim input):**
  `docs/research/private/2026-06-13-partnersim-seed-r1clean.md`

## Implementation Notes

Drafted by Cowork in Tier-1 governance-authoring mode (ADR-009 D1, retained as
advisory per ADR-013). No commit authority (ADR-009 D2 / ADR-013 D2); Code
reviews and commits this draft plus the system instruction and T-follow-ons.
Per K-1, `validate_handoff.py` was not run on the companion completion handoff;
that handoff records the mental-validation substitute and flags the gap.

**Author≠reviewer note (ADR-012 D4.3 applied):** the substance of this venue
was deliberated in the preceding Cowork consultation round with Cray (the
in-session go). Per D4.3 this self-deliberation is disclosed: the
independent-tier deliberation check was not exercised; **Code's review is the
remaining independent check.**

**Provenance (R3 self-application):** this ADR is *about* synthetic data but is
itself a real governance artifact — it carries no SYNTHETIC banner because it
is not partner-sim output. Only material emitted *by the partner-sim project*
carries the banner.

AI-assisted per project convention (noted in commit body, never as
Co-Authored-By, per CLAUDE.md §7).
