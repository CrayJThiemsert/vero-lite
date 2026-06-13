# Runbook — operating the partner-sim synthetic design-partner venue

> **What this is.** The operating procedure for **partner-sim** (ADR-0020): a
> standalone Claude **Cowork** project that role-plays a Thai operator and
> produces a realistically messy "partner profile package", so we can rehearse
> the first-dataset intake + mapping + PDPA pipeline **weeks before** a real
> partner conversation. This runbook is the canonical how-to; it is **tracked**
> (the *method* is legitimate repo knowledge). The sim's **outputs** are
> SYNTHETIC and gitignored (never committed — ADR-0020 R3).
>
> **Current scope (2026-06-13).** Runs as a **separate Claude Desktop Cowork
> project** ("partner-sim"), OUTSIDE the vero-lite repo and OUTSIDE the
> governance tiers (ADR-0020 D1). It is **not** the everyday Cowork tab — a
> fresh, repo-blind project is load-bearing (see R1 below). The methodology is
> expected to evolve (§7 future improvements); this runbook is the baseline to
> iterate from.

## 0. The three binding rules (ADR-0020 D2 — never relax)

- **R1 — feed questions, not schema.** partner-sim is **never** given our
  ontology / engine / benchmark / action vocabulary. Its inputs are R1-screened
  documents only. Schema mismatch is the **discovery value** — do NOT normalize
  it away. (Same trap-class as PLAN-0022 M-2=b: ground truth must not be
  authored by the system under test.)
- **R2 — forced messiness.** The package must carry realistic flaws (missing
  values, unit drift, duplicates, legacy constraints, ≥ N=3 unsolicited
  inconvenient facts). Clean, schema-shaped output is a **failure** (R-PS3).
- **R3 — SYNTHETIC provenance.** Every package carries the SYNTHETIC banner;
  output **never** trips the "first real partner data" trigger (PLAN-0005 §8.1 /
  ADR-011 gate) and **never** enters a benchmark / REPORT / governance context
  unlabeled.

## 1. One-time setup (Cray)

1. **Create a new Claude Desktop Cowork project** named `partner-sim`. It MUST be
   a fresh project — not the existing Cowork tab (which has repo grounding and
   would leak our schema = R1 breach).
2. **Paste the system instruction** into the project's *Project instructions*
   field: copy `docs/conventions/partnersim_project_instructions.md` **from the
   `# partner-sim — Cowork project instructions` heading to the end** (skip the
   top `>` sync-header block, lines 1–7 — that is repo bookkeeping, not for the
   persona). The SYNTHETIC banner block is inside that range and is mandatory.
3. **Do NOT attach the vero-lite repo as Context** (the folder picker lists
   `\\wsl.localhost\…\vero-lite` — selecting it hands partner-sim the whole
   ontology/schema = catastrophic R1 breach).
4. **Disconnect any repo-reading MCP** from this project (e.g. vero-bridge's
   `read_repo_path`). The persona correctly refuses such tools, but the
   capability should not exist (defense in depth — capability-layer R1).
5. **(optional) isolated folder.** A Windows folder (e.g. `D:\ai_projects\
   partner-sim\`) works with no WSL involved, but it must contain **ONLY** the
   cleared inputs (the R1-clean seed + the PDPA checklist) — **never** the
   one-pager, the repo, or any ontology/ADR. Note: the canonical design is
   **paste, not mount** — the persona will (correctly) refuse to read a folder
   because hard-constraint #1 is "read only what Cray pastes". So the folder is
   only a convenient *source to copy-paste from*, not a Context mount.

## 2. Per-run procedure

### 2a. Prepare the three inputs (all R1-screened)

| input | source | note |
|---|---|---|
| **R1-clean seed** | `docs/research/private/2026-06-13-partnersim-seed-r1clean.md` | **NOT** the partner-facing one-pager — the one-pager leaks our taxonomy/action vocabulary (ADR-0020 R1; the 2026-06-13 errata) |
| **PDPA checklist** | `docs/research/private/2026-06-13-pdpa-review-checklist.md` | classification feeds the persona's controller stance |
| **business-type brief** | typed at run start | the ratified SD-3 vocabulary; run-1 default = `energy / mid / th-regional / mixed-legacy` + the session number for the handoff `NN` |

### 2b. Run

Paste the seed, then the PDPA checklist, then the business-brief into the
partner-sim chat (paste — do not rely on a folder mount). The persona produces
**one** partner profile package as **text**, opening with the SYNTHETIC banner
and a handoff frontmatter block (`from: partnersim-<type>`, `actor: cowork`,
`phase: closeout`, `suffix: completion`).

### 2c. Relay + receive (Cray relays → Code receives)

Cray copies the package text back to Code. **Code's D3 receive sequence:**

1. **R2-review** the package quality (§3 criteria). Do **not** normalize the
   schema mismatch — it is the product (R1).
2. **Re-stamp `created`** (K-1: the persona cannot read a clock, so its
   timestamp is an estimate — replace with the real receive time).
3. **Land it gitignored** under `docs/research/private/<date>-partnersim-<type>-
   sessionNN-package.md`. Add `received_by` + `r2_verdict` frontmatter lines.
4. **Verify it is NOT tracked**: `git check-ignore <path>` returns the path AND
   it is absent from `git status --porcelain`. The package is SYNTHETIC — it is
   **never committed**.
5. **D4 run review** (§4): check the four regression triggers.

## 3. R2 review criteria — what makes a good package

A package PASSES if all are present (else flag the gap — possibly a regression
trigger):

- **R1 mismatch is rich** — the package describes the operation in the
  *partner's own* field names / units / categories and does **not** match our
  schema (no canonical action vocabulary, ad-hoc thresholds, their own status
  words). If it looks pre-shaped to our model → **R-PS1**.
- **R2 messiness is present** — missing values, unit drift, duplicates,
  out-of-order timestamps, legacy gaps. If too clean → **R-PS3**.
- **SD-4 refusals** — an explicit "what we refused to share" list with reasons.
- **SD-1 inconvenient facts** — at least N=3 unsolicited, flagged facts.
- **SYNTHETIC banner** verbatim at the top.

## 4. D4 run review — the four regression triggers (ADR-0020)

After every run, confirm none fired:

- **R-PS1** circularity leak — output mirrors our schema (→ first screen the
  pasted inputs: was the R1-clean seed pasted, not the one-pager?).
- **R-PS2** provenance leak — a SYNTHETIC artifact appears unlabeled in a
  benchmark / REPORT / ADR-011 context.
- **R-PS3** insufficient messiness — too clean to exercise the pipeline.
- **R-PS4** context bleed — only if one project runs multiple types (SD-2
  ratified one-project-per-type pre-empts this).

If a trigger fires, **de-scope** (strict one-project-per-type / retire to a
one-off fixture generator) — never expand.

## 5. Operational gotchas (learned on run-1, 2026-06-13)

- **Paste, don't mount.** The persona refusing to read a folder / refusing the
  bridge's `read_repo_path` is **R1 working correctly**, not a bug. Resolve by
  pasting the cleared inputs (the persona's own recommended path).
- **Byte-copy the package via PowerShell, not multi-line `wsl bash`.** Landing
  the package (`D:\…` → the WSL repo) through a multi-line `wsl bash -lc '…'`
  with Thai text + em-dash + shell variables gets **mangled by the 3-shell layer**
  (PowerShell/git-bash → wsl → bash): `cp` reported a misleading `EXIT=0` while
  the file never landed (Glob caught it). Reliable path:
  `Copy-Item -LiteralPath <D:\src> -Destination <\\wsl.localhost\…\dst>`, then
  re-stamp the `created` line with the **Edit tool** (not shell sed).
- **Verify gitignore by content, not piped exit codes.** `git check-ignore <path>`
  (prints the path on match) + a tracked-status count — a `grep -c` returning 0
  exits 1, which is *expected*, not an error. Don't trust a bare piped `$?`.
- **`/mnt/d` is lazy-mounted** in WSL — a cold `test -f /mnt/d/…` can falsely
  report missing; `ls /mnt/` warms it. (PowerShell sidesteps this entirely.)

## 6. Worked example — run-1 (energy / NPD, 2026-06-13)

- Business-brief: `energy / mid / th-regional / mixed-legacy`, session 58.
- Output: `docs/research/private/2026-06-13-partnersim-energy-session58-package.md`
  (gitignored) — synthetic "นครพิงค์ พาวเวอร์ ดิสทริบิวชั่น (NPD)", COO persona.
- **R2 verdict: PASS.** Rich R1 mismatch (their units `load_mva`/`oil_c`/`v_kv`
  with drift to Amps/raw-ADC/V; Thai status words not breach/watch/ok;
  **explicitly no standard action/severity field**; ad-hoc thresholds 6.4/7.6
  MVA, oil 96/104 — not our 8.0/90.0 pins). Full R2 messiness (dup, out-of-order
  ts, missing value, raw-ADC, TX-ID reuse). SD-4 refusal table + 5 SD-1
  inconvenient facts (ID reuse, ~40% oil estimated, OMS no-export + vendor
  defunct, NTP drift 7 min in 2024, SLA-driven under-reporting).
- **D4 review: all four triggers clear** — the venue achieved its goal.
- **High-value yield (for ADR-011 audit framework):** a real authority matrix
  (makes `approval_chain` enforceable), actor-identity scattered across 4
  unlinked places, PII embedded in free-text notes (DSR/lineage challenge),
  back-filled + NTP-drifted timestamps, systematic under-reporting.

## 7. Future improvements (intent captured — to develop further)

Cray intends to evolve the sim methodology for ongoing use. Candidate
directions (not yet decided — capture, don't build):

- **Refine the seed/brief** from what the mapping rehearsal (next step) shows we
  actually need — the seed should ask for exactly what produces usable input.
- **Reduce manual relay friction** — the Cray-relay → Code-receive loop is
  manual; if runs become frequent, the Code-receive half (validate + re-stamp +
  R2 + land) is a natural **Skill** candidate.
- **Parameterize personas** beyond SD-3 (sector depth, adversarial difficulty,
  maturity).
- **Tighten capability-layer R1** — ensure the project ships with zero
  repo-reading tools by construction, not by persona discipline.

## 8. References

- **ADR-0020** (`docs/adr/0020-partner-sim-venue.md`) — the venue decision
  (Accepted 2026-06-13): D1 outside-tiers, D2 R1/R2/R3 binding, D3 I/O protocol,
  D4 guarded-trial + R-PS1..R-PS4, SD-1..SD-4 ratified.
- **System instruction** — `docs/conventions/partnersim_project_instructions.md`
  (the paste source; sync target = the Claude project field).
- **Seeds** — `docs/research/private/2026-06-13-partnersim-seed-r1clean.md`
  (R1-clean input) + `…-pdpa-review-checklist.md` (both gitignored).
- **ADR-005** — energy = primary partner type / supply chain = secondary.
- **PLAN-0022** (`docs/plans/done/0022-tiered-decision-routing.md`) — the M-2=b
  calibration-first precedent the R1 anti-circularity design mirrors.
- **ADR-011** (earmarked) — audit framework; partner-sim output **informs** its
  §Context but **never trips** its first-real-data trigger (R3).
