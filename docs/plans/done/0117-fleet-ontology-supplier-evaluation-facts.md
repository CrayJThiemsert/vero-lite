# PLAN-0117: Fleet ontology carries supplier-evaluation facts — the Ask-surface unlock; a prerequisite for the rationale bar, not its unlock

**Status:** Complete
**Owner:** Claude Code — **execution-unblocked, no open SDs.** Cray ruled every SD (typed, 2026-08-31, session 265): SD-1=(c), SD-2=SPLIT (fleet side here; core promotion deferred to its own ADR+PLAN), SD-3 IN-set ruled, SD-4=(a), SD-5=(a), and — later the same session — **SD-3a RULED: declare all four remaining donor properties now, bare + rich `description`, NO synonyms** (see the SD-3a ruling block; it overturns this draft's earlier OUT disposition for those four, lineage preserved). In the s265 correction pass, **SD-6 RULED (a): the ontology's effect on the two MS-S1 models is measured on the NL / Ask surface (`benchmarks/nl_query_feasibility/`), not on `procedure_baseline`** (see SD-6 + the Correction record). **s275 addendum (2026-09-03):** the implementation landed and merged at s265-266 (PRs #1329-#1340; `61b0edc`, `42f3843` — per the s275 dispatch, not re-derivable by this drafter); the nine AC boxes stay **unticked** pending the re-witness; **SD-8 RULED (a) later in s275 (Cray, typed, 2026-09-03): the landed `:127` text assertion runs as a 16th probe** — the re-witness is now **16** (15 in-battery + AC-1(a) by hand), superseding Cray's own typed 15 of s274 (`superseded by new info`, not `was an error`: 15 was correct for the scope known then; SD-8 surfaced a claim that scope had not accounted for, and Cray widened it — see the SD-8 block). **No open SDs.**
**Created:** 2026-08-31 · **Revised:** 2026-08-31 ×3 (same session family, s265 — first pass: rulings + two specialist investigations; second pass: SD-3a ruling closed + propagated; third pass: **correction** — Code's offline measurement F17 showed the ontology never reaches the procedure agent's prompt, so the theory of change is corrected from "rationale-bar unlock" to "Ask-surface unlock + rationale-bar prerequisite"; SD-6 ruled) · **2026-09-03 (s275) — closeout-precondition pass:** eight surgical corrections to the ACs/Steps (C1-C8) so each witnessed-RED probe states something that can actually fire, applied **before** the ruled 15-probe re-witness runs; no checkbox ticked, Status unchanged — see the s275 correction record · **2026-09-03 (s275, fifth touch — surgical):** SD-8 ruled (a) and propagated (15 → 16 probes; 72 → 71 expected exemptions), Code's measured s275 results recorded where the PLAN states expected outcomes; no checkbox ticked, Status unchanged
**Related ADRs:** ADR-006 (Rule of Three — bore on SD-2's *original* reasoning; superseded as the operative ground by the SPLIT ruling), ADR-008 (ontology schema + D1 "may extend" license; D4 many_to_many deferral), ADR-0032 (D1 demo→pilot correction-surface discipline — bears on SD-1), ADR-0033 (**D6 boundary — the deferred core promotion must formally reopen it**; see the Out-of-Scope deferred-core record), ADR-0034 (D4 evidence-alternative — the per-case sole-source record that makes a vendor-level `single_source_flag` a double-statement risk; originally the OUT reason in SD-3, now the **noted residual concern** under the SD-3a ruling)
**Related PLANs:** PLAN-0109 (Draft, unexecuted — **edits the same YAML file**; see the Coordination section), PLAN-0111 (verified **zero overlap** — Coordination §5 / F14), `done/0036` (the procurement donor), the later grader PLAN this one feeds (unnumbered; named in Out of Scope — this PLAN is a prerequisite for its rationale lane, **not** its unlock: that lane also needs the goal edit (SD-4, that PLAN) and the still-unscoped event/goal carrier, F17), the deferred core-promotion ADR+PLAN (unnumbered; the Out-of-Scope block below is its durable record until they exist)

> **Drafting provenance (ADR-012 D4.3).** Authored by the in-harness `plan-drafter`
> subagent from a Code-tab dispatch (session-264 follow-on fact-pack, verified by the
> dispatcher and re-verified on disk by this draft, 2026-08-31). **Revised the same day
> (s265) by the same subagent** to record Cray's typed rulings on SD-1..SD-5 and fold in
> two specialist investigations (DSL expressibility; the core-promotion bill) — every
> specialist claim re-verified on disk by this revision except the two explicitly marked
> "measured by Code, s265" (a DB row count and prompt byte sizes, F12/F13). **Revised a
> second time the same day (s265, same subagent)** to close SD-3a per Cray's typed
> ruling and propagate it; the ruling's structural grounds (description dropped at load
> by design, schema legality of a property `description`, the honest-no-records path)
> re-verified on disk by this second revision — only the byte figures remain "measured
> by Code, s265". **Revised a third time (s265, same subagent) — a correction pass:**
> Code's offline measurement (F17: the ontology does not reach the procedure agent's
> prompt; positive-controlled) narrows the theory of change, and Cray's typed SD-6
> ruling fixes the measurement surface. Every F17 grep count, the positive control, the
> prompt-builder signatures, the orchestrator near-miss, and the six-vertical `reads:`
> staleness evidence were re-verified on disk by this revision before citing.
> **Revised a fourth time (2026-09-03, s275, same subagent) — a closeout-precondition
> pass:** eight AC/Step corrections (C1-C8) from the s274 four-specialist audit and
> Cray's typed 15-probe re-witness ruling. Every `file:line` this pass cites — the two
> landed test modules, the seed rows, `ci.yml`, `conftest.py`, `pyproject.toml`, the
> probe-battery driver and README, `nl_query.py`'s no-data text — was re-read on disk
> by this revision; the figures it could not re-derive without a shell (the 86-claim
> denominator, the commit hashes, the generated-artifact timestamps) are marked
> "measured by Code, s275". **Touched a fifth time (2026-09-03, s275, same subagent) —
> surgical:** SD-8's ruling recorded and propagated (15 → 16 probes; 72 → 71 expected
> exemptions), and Code's measured s275 results (the 14-probe battery, AC-1(a), AC-7,
> AC-8 step 3, the AC-3(a) cross-green) recorded where the PLAN states expected
> outcomes — figures per the s275 follow-on dispatch, marked "measured by Code, s275";
> the ruling's anchors (`nl_query.py:1103`, `test_vendor_facts_scenario.py:120-129`,
> `test_ontology_data_contract.py:164,234`, `conftest.py:190`) re-read on disk by this
> touch. Outline originator: Code (s275 dispatch).
> Independent review: Cray at PR merge. Code commits via PR
> (CLAUDE.md §7); the drafter does not commit.

---

## Goal

Extend the `fleet_maintenance` ontology — and the synthetic seed that makes its
declarations answerable — to carry **supplier-evaluation facts**: the vendor-standing
and service-history facts the ratified rationale bar named as missing. The bar is
role-naming alone **because** "is this the right supplier, does their delivery history
support accepting this quote, how does it compare with the alternatives — rest on facts
the ontology does not yet carry" (`benchmarks/procedure_baseline/grader.py:83-91`;
`benchmarks/model_compare/RESULTS-1.6.md:706-718` §13;
`docs/lessons/0052-a-criterion-may-only-demand-what-the-run-supplies.md:69-74`). That
framing is right that the facts have no home — and this PLAN builds the home. What it
does **not** do is put those facts in front of the procedure model, because the
ontology is not on that model's prompt path at all (**F17, measured s265 with a
positive control**). Stated plainly, in three parts:

- **What this PLAN DOES unlock, and it is real: the NL / Ask surface (Tab C).**
  `_describe_ontology` genuinely feeds the translate prompt there (F13), and the seed
  serves the values — a visitor asking "which garage has the most comebacks?" becomes
  answerable, on a live, visitor-facing surface of the published demo. This is where
  the ontology's effect on the MS-S1 models will be measured (**SD-6, RULED**:
  `benchmarks/nl_query_feasibility/`).
- **What it does NOT unlock on its own: the `procedure_baseline` rationale lane.**
  The procedure agent's prompt is built from exactly four inputs — a static role
  string, the `procedures.yaml` goal, the handler catalog, and the event (F17) — and
  a declared ontology property routes into none of them. Adding properties alone
  moves **nothing** in that lane.
- **The missing second half, named as unscoped work:** for supplier facts to reach
  the procedure model, something must carry them into the **event** (the adapter's
  event builders, `verticals/fleet_maintenance/data_adapter/synthetic.py:175,198`) or
  into the **goal** text (`procedures.yaml` — SD-4 deliberately parked goal edits
  with the later grader PLAN). **Nobody has scoped that carrier.** It is not this
  PLAN's job; its absence is recorded in Out of Scope so it is visible here, not
  discovered later.

The rationale-lane statement per RESULTS §13 ("each supplier-evaluation fact that
enters the ontology **and the goal** makes a stricter rule answerable") therefore
needs all its halves read literally: the goal/dataset/grader half rides together in
the later PLAN (SD-4, **RULED (a)**), the value-carrier is unscoped, and this PLAN
supplies the declaration + Ask-surface half. This PLAN is still worth executing
exactly as ruled: `Vendor` property declaration is a **prerequisite for anything
supplier-shaped on either surface** — no carrier, goal edit, or grader move can
reference a fact that has no declared home. It demands nothing of any model.

Shape, per the s265 rulings: **SD-1=(c)** — the values ship as DEMO-SEED,
provenance-marked **AUTHORED**, with the measured-projection route recorded in YAML
comments as the promotion path (the house rule: a backfilled/authored value carries its
provenance). **SD-2=SPLIT** — this PLAN is the **fleet-side extension only**; the core
promotion is **deferred, not rejected**, to its own ADR+PLAN, with its durable record in
the Out-of-Scope deferred-core block below. **SD-3+SD-3a — the declaration is
two-banded:** the 5 narrative-grounded facts carry Thai synonyms and seed values (the
"answerable" band above); the donor's 4 remaining compliance properties (`tax_id`,
`cert_status`, `sanctions_flag`, `single_source_flag`) are declared **bare + rich
`description`, NO synonyms, NO seed values** — prompt-visible by name so the
Ask/translate LLM can use them the moment a value exists (Cray's requirement (c);
the procedure model sees no ontology property either way, F17), while an unpopulated
one routes honestly to the no-records answer (F15) rather than a fabrication.

## Correction record (s265, third pass) — believed, measured, stands

⚠️ **Corrected 2026-08-31 (s265).** Recorded in the house idiom for a corrected
claim: what was believed, what was measured, what now stands.

- **Believed (this PLAN's own earlier title + Goal):** that this PLAN was "the
  rationale-bar unlock, supply side" — i.e. that declaring the supplier facts in the
  ontology was **the** unlock for raising the `procedure_baseline` rationale bar,
  inheriting `grader.py:83-91`'s "an **ontology** move before it is a grader move"
  and Lesson 0052's "the ontology work is now the **named unlock**" at face value.
- **Measured (Code, s265, offline, positive-controlled — F17):** the ontology never
  reaches the procedure agent's prompt. `build_reasoning_messages` →
  `build_system_instruction(vertical: str, goal, catalog)` builds it from a static
  role string, the goal, the handler catalog, and the event — the vertical parameter
  is a `str` name, never `OntologyMeta`. `grep -c ontology` = 0 on both prompt-path
  modules while the **same grep returns 18 on `nl_query.py`** (the control that makes
  the zeros evidence rather than a broken grep). Declaring a property routes it into
  neither the event nor the goal — the only two channels that reach that model.
- **Stands:** (i) the sources' literal claims are still true — the facts had no home,
  and RESULTS §13's own wording already named "the ontology **and the goal**"; (ii)
  what died is the *reading* that declaration alone puts facts in front of the
  procedure model; (iii) this PLAN's unlock is the **NL / Ask surface**, where the
  ontology genuinely feeds the prompt, and that is where the effect is measured
  (SD-6); (iv) the rationale lane additionally needs the goal edit (SD-4, later PLAN)
  **and** an unscoped value-carrier into the event or goal (Out of Scope); (v) every
  AC of this PLAN stands unweakened — **this correction narrows a claim, not a
  criterion** — and the work is still worth executing: no surface can use a fact
  that has no declared home. A post-F17 reading note on SD-3a: "the LLM must be able
  to use them" in Cray's requirement (c) is satisfied on the **Ask/translate model**
  — the mechanism the ruling itself cites is `_describe_ontology` — not on the
  procedure model, which sees no ontology property until the carrier exists.

**Retired-claim handling (`docs/conventions/retired-claims.md`, checked — judged NOT
to emit a marker from this PLAN; stated explicitly, not silently picked):** (1) the
verbatim source wordings are **not dead claims** — `grader.py:83-91` truly states the
facts "rest on facts the ontology does not yet carry", and RESULTS §13 names both
halves — so retiring their text would kill true sentences; what died is a *reading*,
whose only verbatim home was this PLAN's own pre-amendment title/Goal, rewritten in
place on the unmerged PR branch — no live stale copy survives for a marker to guard;
(2) a marker matching `grader.py`'s or Lesson 0052's live wording would fail the
guard against those files and force cross-file edits this correction pass must not
make (the grader is this PLAN's own first Out-of-Scope bullet). One candidate stale
copy IS named for later propagation per the convention's backfill rule: Lesson
0052:71-72 ("the ontology work is now the named unlock") is now half-true — true for
the Ask surface, incomplete for the rationale lane — and should gain its
qualification (with a retire marker if reworded) whenever that lesson or the later
grader PLAN next touches it. Likewise `orchestrator.py:569`'s stale "every shipped
procedure is reads-absent" docstring (F17) — noted, not fixed here.

## Correction record (s275, closeout-precondition pass) — eight corrections, each classified

⚠️ **Corrected 2026-09-03 (s275).** The implementation landed and merged at s265-266
(`61b0edc`, `42f3843`; PRs #1329-#1340 — hashes per the s275 dispatch, not
re-derivable by this drafter; `61b0edc` since **confirmed by Code, s275** as the YAML-edit
commit — `feat(fleet): Vendor carries the supplier-evaluation facts (PLAN-0117 Step 2)`,
105 insertions to `fleet_maintenance_v0.yaml` — so C7's reconstruction command cites
the right SHA) and nobody returned to tick the boxes. A four-specialist
audit (s274) found that several witnessed-RED probes, re-run **as the ACs state
them**, cannot fire or cannot fail. Cray ruled a **full 15-probe re-witness** (typed,
s274) — **widened to 16 by SD-8, ruled (a) later in s275** (`superseded by new info`; both
counts are Cray's own typed rulings — see the SD-8 block). This pass makes each AC state something that can actually be witnessed,
**before** any probe runs — it ticks nothing and weakens nothing. Every correction is
either **`was an error`** (the text was wrong when written) or **`superseded by new
info`** (the text was right; the landed code moved the ground under it) — handled
distinctly, never flattened to "stale" (CLAUDE.md §6). Each row's marker also sits
inline at the corrected text, so the table is the index, not the only record.

| # | Where | Class | What was wrong (measured s275) | What now stands |
|---|---|---|---|---|
| C1 | AC-4, dormant case | `was an error` | Pass read said "grounded-but-empty"; the landed test asserts `ans.grounded is False` (`test_vendor_facts_scenario.py:122`) and its docstring (`:105-110`) already records the divergence | Pass read = the six landed assertions (`:120-123`, `:127`, `:129`); the **operative** requirement — honest no-records, never a fabricated fact — is unchanged; only the `grounded` parenthetical was wrong |
| C2 | AC-3 probe (a) | `was an error` | "Blank the **sole** carrying row" — no synonym-band property has a sole carrier (`synthetic.py:356-395`: `standing` ×3, the other four ×2); one blanked row leaves another carrying → driver reports `GREEN` (README `:102`) | One multi-line `old` spanning **both** carriers of `avg_turnaround_days` (`:368-379`); values set to `None`, keys **not** deleted (keeps the `_HISTORY_FACTS` positive control at `:234` green — `:164` lists that property) |
| C3 | AC-4 dormant probe | `was an error` | `expect_claim` pointed at the text assert `:127`; the run dies first at `:121` (`result_count == 0`) → `MISFIRE` (README `:99`) | `expect_claim` = `:121`; `:127` is a separate claim needing its own probe — **SD-8, ruled (a) s275: it runs as the 16th, `AC-4-dormant-no-records-TEXT` (Step 5)**; ⚠️ AC-3a(b) seeds `false`, this seeds `true` — not mergeable |
| C4 | AC-1(c) | `was an error` | Read said `≥ 5`; the landed test asserts **equality** (`test_ontology_data_contract.py:352`) — `≥` would pass on a stray sixth stamp the test rejects | `== 5`; latent, non-blocking: `_raw_vendor_yaml_lines()` (`:326-327`) reads the **whole file**, so a stamp on `Truck` reddens it for a non-`Vendor` reason (flagged, not fixed) |
| C5 | AC-8 | `was an error` | Commands lacked `--no-sync` (a bare `uv run` uninstalls the dev tools mid-run, `ci.yml:52-54`); `pytest tests/` disarms the AC-12 DB floor (`conftest.py:181,192` compares args to `["tests"]`); four offline CI steps absent | Seven CI-faithful commands (`ci.yml:56,59,74,91,100,113,137`) with `--no-sync`, bare `pytest -q`, `CI=1`; `--strict` and the two alembic steps explicitly checked and **not** added (redundant / DB-bound) |
| C6 | AC-7 positive control | `was an error` | `grep "standing" generated/schema.json` already hits **today with no codegen run** (count 1, measured s275; the gitignored artifact from s265 persists) — the control was vacuous | Delete-first: `rm -rf` the gitignored dir → grep **must fail** → codegen → grep passes; pattern quoted `'"standing"'` (bare `standing` ⊂ `outstanding`) |
| C7 | AC-1(b) baseline RED; AC-6 | `superseded by new info` | Sound against an unexecuted PLAN; post-landing the baseline command returns all 12 names (GREEN), and AC-6 compares the tree with itself — no test asserts a type **count** (`len(...object_types\|link_types)` over `tests/` = 0 matches) | Both marked **un-re-witnessable at closeout**, reason inline; the only genuine AC-1(b) re-witness is `git show 61b0edc~1:…` piped into the loader — out of scope unless Cray rules otherwise; nothing deleted, no substitute invented |
| C8 | Step 5 enumeration | `was an error` | Listed 13 probes; dropped AC-1(c1)/(c2), which AC-1 itself defines as "two mutations, two assertions" | **15** = 14 in-battery + AC-1(a) outside the driver (its subject is a pre-commit hook, not a pytest node); equals Cray's ruled 15; the `:127` probe would be a **16th** — raised as SD-8, not absorbed. **See SD-8, ruled (a) s275: the 16th runs — 16 = 15 in-battery + AC-1(a)**; this row's 14-in-battery was right for the ruled 15 and is `superseded by new info`, not re-classified |

**Known gaps, deliberately unprobed at this closeout** (recorded here so the
coverage report's exemptions are written from a list, not improvised at run time).
**SD-8's ruling (a), s275, resolved one of the two claim-level gaps this pass
registered and not the other:** the `:127` text assertion — formerly a provisional
exemption naming SD-8 (Step 5) — is now **probed** (the 16th) and is no longer a gap;
AC-2's `:203`/`:204` (first bullet) remain named-by-AC-2 and unprobed — the ruling did
not touch them:

- **AC-2's two provenance-exclusion asserts** — `test_ontology_data_contract.py:203`
  `assert "AUTHORED / DEMO SEED" not in described` and `:204`
  `assert "PROMOTION PATH" not in described` — are named by AC-2's own pass read but
  carry **no probe**. They need **written exemptions** in the battery (README `:79`:
  `stable_key` → the reason no probe can reach it) — or probes, if Code finds an
  isolating mutation (injecting a stamp phrase into one rendered `synonyms` list is
  the obvious candidate; not scoped here, and not silently chosen).
- **The coverage denominator is the whole module, not the probe count.** Measured
  by Code, s275, via `python -m tools.probe_battery keys` (`__main__.py:139`):
  `test_ontology_data_contract.py` = **32** claims, `test_vendor_facts_scenario.py` =
  **17**, `test_golden_e2e.py` = **37** — **86** in total. Every claim neither
  credited by a `WITNESSED` probe nor exempted with a written reason is a GAP, and
  any GAP makes `passed` false (`_battery.py:570`: `complete and not overlaps and
  all(r.passed …)`) → `PROBE-BATTERY: FAIL`. Arithmetic, under SD-8 ruled (a):
  86 − **15** in-battery credits = **71 exemption lines** — the pre-ruling figure was
  72 = 86 − 14, correct for the ruled 15 (`superseded by new info`), and was **measured**
  by Code s275 at the 14-probe stage: `claims: 86 · witnessed RED: 14 · exempted: 72 ·
  GAPS: 0 · stale ids: 0`, `PROBE-BATTERY: PASS`, `PROBE-COVERAGE: COMPLETE`. AC-1(a)
  is **outside** the 86 (no `Claim` — C8), so the count is 86 = 15 + 71, not 86 − 16 =
  70: a 70 would subtract a probe from a denominator it is not in; the 16-probe run's
  printed `exempted:` value is the reading to trust, and this line is corrected by
  deriving, never by relaxing, if they disagree (CLAUDE.md §8); the dispatch's "~50-70"
  estimate is therefore a floor, not the figure. Do **not** narrow `claim_sources`
  to shrink the denominator — `tools/probe_coverage.py:25-30` names that move as
  "the moment to have someone else check"; and the AC-5 probe's node lives in
  `test_golden_e2e.py`, so that module is in the denominator by construction.
- **Verification §5 demands the coverage report in the PR body, but no AC requires
  it** — an unhomed requirement. The report is **stdout only**: `_battery.py:577`
  prints it, `BatteryResult.report` is returned, nothing is written to disk — so the
  run must be captured with `2>&1` into a file or the report is unrecoverable. Step 5
  now names the capture. It stays homed in Step 5 + Verification §5 rather than
  gaining a tenth AC (a Code judgment, stated: the report is *evidence for* the nine
  ACs, not a criterion of its own).
- **The DB floor's second gate** (found while verifying C5; stricter, not a
  relaxation): `db_floor_verdict` also returns `None` unless `os.environ.get("CI")`
  is set (`conftest.py:190,209`). A local AC-8 run arms the floor only as
  `CI=1 uv run --no-sync pytest -q` — recorded so a green local run is not mistaken
  for a floor-armed one. **Confirmed by Code, s275**, against `conftest.py:190`
  (`if not ci: return None`) — the full-suite command in AC-8 (7) carries `CI=1`.

## Baseline facts (verified on disk 2026-08-31 by this draft — cite, don't re-derive; re-confirm line numbers on the execution branch, the base moves)

- **F1.** The unlock framing is recorded in three places and is not re-argued here:
  `grader.py:73-96` (`role_vocabulary` — "a model is only ever measured against
  vocabulary its **own prompt handed it**"; the cap on strictness), RESULTS-1.6 §13
  (`:706-718` — "an **ontology** move before it is a grader move"; requiring the amount
  scored 0/14 vs ~3/14, "unmeasurable, not undesirable"), and
  `benchmarks/procedure_baseline/rationale_regrade.py:123-131` ("As supplier-evaluation
  facts enter the ontology and the goal, each …"). ⚠️ **Scope corrected s265 (F17 +
  the Correction record):** these three correctly record the demand-side cap; the
  supply they call for is two-channel (declared home + a carrier into the goal/event),
  and this PLAN builds only the first channel.
- **F2.** Fleet's object types today (`verticals/fleet_maintenance/ontology/fleet_maintenance_v0.yaml:32-282`):
  Truck, Vendor, Depot, OperationalEvent, Alert, RecommendedAction, AlertEventLink —
  **no supplier-evaluation facts anywhere**. `Vendor` (`:105-151`) carries exactly
  `vendor_id`, `name`, `accounting_code`, and its own description (`:120-127`) settles
  the free-text seam: `RepairCaseQuote.vendor` et al. "stay free text on purpose"; the
  registry resolves typed names by exact trimmed case-insensitive match, never fuzzily.
- **F3.** The donor: `verticals/procurement/ontology/procurement_v0.yaml:201-327`
  ships `Supplier` (`avl_status`, `tax_id`, `cert_status`, `sanctions_flag`,
  `single_source_flag`), `Quotation` (`price`, `currency`, `lead_time`, `warranty`,
  `on_contract`), `PurchaseOrder`, `ComplianceRule`, `ApprovalTier` (built by
  `done/0036`). **This is a port with a filter, not an invention** — SD-3 + SD-3a are
  the filter (two-banded since the SD-3a ruling: synonym-carrying vs bare-dormant).
  Donor types for the dormant four, verified at `:216-225` by this revision: `tax_id`
  string; `cert_status` enum `[valid, expired, none]`; `sanctions_flag` bool;
  `single_source_flag` bool.
- **F4.** The run's prompt supply chain (`services/engine/llm/prompt.py:133-156`):
  system = vertical + **goal** + catalog; the event reaches only the untrusted block.
  The ontology is among **none** of these inputs — measured, with a positive control,
  as F17.
  Fleet's goal (`verticals/fleet_maintenance/procedures.yaml:133-143`) currently
  instructs: the sourcing gate "is applied DOWNSTREAM by the engine and not by you …
  never withhold a routing decision on quote counts." Any future goal wording that asks
  the model to weigh vendor history must be written **against** that sentence, not past
  it — SD-4.
- **F5.** The sourcing gate (`verticals/fleet_maintenance/sourcing.py:1-60`) is pure,
  deterministic, count-based, and downstream — the caller supplies counts; nothing
  surfaces vendor facts to the LLM as named facts. Its fraud provenance (`:33-36`,
  "adopted after being defrauded on parts") is the narrative ground for a vendor
  `standing` fact (SD-3).
- **F6.** The evidence-table seam: real quote rows live in a **hand-written** ORM
  outside the ontology layer — `services/db/repair_case_evidence.py:73-122`
  (`RepairCaseQuote`: `vendor` free text `:106`, `amount_thb` Numeric `:108`). Fleet
  has **no committed generated code**: `_ORM_COMMITTED_DEST` = {energy, core},
  `_PYDANTIC_COMMITTED_DEST` = {core} (`services/engine/code_generator.py:900-914`);
  `generate_all` (`:917-939`) falls back to gitignored
  `verticals/fleet_maintenance/generated/` for fleet. **A YAML edit needs no
  migration** — confirmed under the SD-1 ruling (c): option (b)'s projection half
  enters this PLAN only as comments, never as code.
- **F7.** The golden guard (dispatch constraint: named here):
  `tests/services/engine/scaffolder/test_golden_e2e.py:341-349` asserts the donor's
  **object-type set** and **link-type set** against the scaffolder's emission, with a
  hand-maintained exemption `_DONOR_EXTENSION_OBJECTS = {"Vendor"}` (`:318-324`) whose
  comment warns: past "a couple of entries", build an extension slot instead.
  Consequences, verified in the assertion text: (i) **property** extension of the
  already-exempt `Vendor` is invisible to this oracle by construction (`Vendor` is
  subtracted before comparison, `:343`); (ii) a **new object type** reddens it and
  grows the exemption; (iii) a **new link type** reddens it with **no exemption slot at
  all** (`:349` is bare set equality). This prices SD-3's shape options.
- **F8.** The contract guard: `tests/verticals/fleet_maintenance/test_ontology_data_contract.py`
  is generic and two-directional — every `required` property present in every row
  (`:44-55`), no row carries an undeclared property (`:58-67`) — and its own docstring
  (`:8-11`) names the gap this PLAN must close for **non-required** properties:
  "declare a property … forget the value in `synthetic.py`, and NOTHING goes red" while
  `/meta` advertises it. `:120-134` proves Thai synonyms reach `_describe_ontology` —
  "the line between 'in the ontology in principle' and 'answerable'".
- **F9.** The seed: `verticals/fleet_maintenance/data_adapter/synthetic.py:328-364`
  (`vendor_records` — three garages, one deliberately uncoded so the AC-9 KPI stays
  non-vacuous; `OBJECT_SOURCES` `:367-371`). The uncoded-row honesty pattern is the
  template for the new facts' "no history yet" row (Step 3).
- **F10. 🔴 Grounded negative (dispatch constraint 3, answered):**
  `tools/check_ontology_orm_lockstep.py` does **not exist on disk** (verified by direct
  read, 2026-08-31). It is **PLAN-0109's deliverable** (its AC-3 / Step 2; its F9
  records the same grounded negative). Either way it cannot bite here: the guard
  compares YAML↔ORM per a declared type↔table mapping, and `Vendor` is a synthetic
  type with no ORM table — outside the mapping under both PLANs.
- **F11.** The benchmark's fleet ground truth
  (`benchmarks/procedure_baseline/dataset/fleet_maintenance.yaml:1-56`) authors its
  scenarios to stay faithful to real ontology-projected events (B-β calibration,
  `harness.py:61`). It carries no vendor facts today; mirroring new facts into it is
  the later PLAN's move (Out of Scope).
- **F12.** (measured by Code, s265 — a DB measurement this draft cannot re-derive
  offline; re-confirmable at execution) The month-end export currently contains
  **exactly one row** (`case-fleet-demo-history`). SD-1 option (b)'s "a history of
  n=1 cases is noise wearing a number" is therefore **measured, not asserted** — the
  evidentiary ground for ruling (c) over (b)-now.
- **F13.** Prompt-cost facts (fed SD-3a; now the ruling's evidentiary ground).
  Structural halves, verified on disk by this revision (and re-verified by the second
  s265 revision — the base moves): `_describe_ontology`
  (`services/engine/nl_query.py:382-398`) renders **every declared property with no
  value check**, and `PropertyMeta` (`services/engine/ontology_meta.py:268-285`)
  carries no visibility/queryable flag — so "auto-skip when unpopulated" **does not
  exist today**; `services/engine/ontology_schema.json` sets
  `additionalProperties: false` at every level, so a documentation-only YAML parking
  key is inexpressible. **The description half (decisive for SD-3a):** a property-level
  `description` IS schema-legal (`ontology_schema.json:79`), but `_property_meta`
  (`ontology_meta.py:268-285`) drops it at load — `PropertyMeta` carries only
  `name, type, required, enum, target, synonyms, sample_values` — and
  `_property_aliases`'s docstring (`nl_query.py:363-371`) records this as
  **deliberate design**: "``description`` is deliberately NOT rendered … content aimed
  at a human reader of the YAML, not at the model." A rich `description` therefore
  costs **ZERO prompt bytes**, by design. **Synonyms are the expensive part, not
  declaration**: the existing `name` property's synonym list alone is ~90 B against
  ~17-26 B for a bare name+type line (measured by Code, s265). Sizes (measured by
  Code, s265; re-derivable at execution from `len(_describe_ontology(meta).encode())`):
  the fleet schema block is **1,945 B** across 7 object types; the `Vendor` line is
  339 B; the 5 ruled-IN properties add **+145 B (7.5%)**; the 4 dormant ones add
  **+107 B (5.5%)** — roughly 30 tokens per translate call (whether that figure
  already includes `cert_status`'s rendered enum values is re-derivable at execution;
  no AC pins a byte number).
- **F14.** PLAN-0111 (`docs/plans/0111-fleet-closeout-credit-note-record.md`) touches
  **neither** `fleet_maintenance_v0.yaml` **nor** `ontology/` — grep for both terms
  returned zero matches (verified by this revision, 2026-08-31). The earlier
  "asserted-not-verified" residual note about 0111 is **CLOSED** (see Coordination §5).
- **F15.** The honest-no-records path (verified on disk by the second s265 revision —
  the mechanism the SD-3a ruling's requirement (b) rides on): an empty match
  short-circuits to `_no_data_nlanswer` (`services/engine/nl_query.py:1369-1371` →
  `:1280-1283`, "no record matched, so no fact is invented"); a resolve miss takes the
  same path (`:1354-1358`). A declared-but-unpopulated property filtered on therefore
  yields a grounded-but-empty answer through **existing** machinery — partial
  population needs **no new mechanism**.
- **F16. ⚠️ Asserted-not-verified — UNMEASURED.** The answer-quality effect of the
  wider translate vocabulary (9 new property names in every translate call, 4 of them
  valueless): a model may attempt queries that return empty more often. This is
  **unmeasured**; measuring it needs a live MS-S1 run under a typed CLAUDE.md §8 go.
  Recommendation (Code, s265, adopted by this draft): fold that measurement into the
  later grader PLAN's MS-S1 run — which re-baselines the lane anyway (SD-4 ruling) —
  rather than paying for a separate host-state round. Until then, every claim that
  the dormant band is behaviourally free rests on the offline F15 mechanism only.
  ⚠️ **Recommendation superseded by the SD-6 ruling (s265, kept as lineage):** the
  ruled surface for measuring the ontology's effect on the MS-S1 models is route (a),
  `benchmarks/nl_query_feasibility/` — F16's vocabulary-width question rides THAT run
  (it is a translate-surface effect, so route (a) is also where it is observable),
  still under its own typed CLAUDE.md §8 go.
- **F17. 🔴 Measured (Code, s265, offline, positive-controlled; every count and
  anchor re-verified on disk by this revision — re-verify again before citing, the
  base moves): the ontology does NOT reach the procedure agent's LLM prompt.** The
  prompt on that path is built by `build_reasoning_messages` →
  `build_system_instruction(vertical: str, goal, catalog)`
  (`services/engine/llm/prompt.py:72-138`) from exactly four inputs: (1) a static
  `role` string keyed on the vertical **name** — a `str`, never `OntologyMeta`; (2)
  `goal` — the procedure's directive from `procedures.yaml`; (3) `catalog` —
  `registry.handler_catalog` (handler names + descriptions); (4) the `event` dict,
  rendered by `format_event` (`:122`) into the untrusted block. Evidence:
  `grep -c ontology` → `services/engine/llm/prompt.py` = **0** (0 even
  case-insensitive), `services/engine/llm/structured.py` = **0** (the single
  case-insensitive hit is the capitalized English word inside a static
  `Field(description=...)` at `structured.py:101` — schema prose, not a meta feed),
  `services/engine/procedures/action_step.py` = **1**, and that hit is a docstring
  phrase ("ontology-projected keys", `:234`), not a prompt feed. **Positive control
  (what makes the zeros evidence rather than a broken grep):** the same
  `grep -c ontology` on `services/engine/nl_query.py` returns **18** — the NL path
  genuinely consumes the ontology via `load_ontology_meta` → `_describe_ontology`.
  Near-miss, classified: `services/engine/procedures/orchestrator.py`'s
  `validate_read_bindings_for_vertical` (`:562-577`) DOES call `load_ontology_meta`
  (`:574`) — a **validation gate**, not a prompt feed; loading is not prompting.
  ⚠️ That function's docstring claim "every shipped procedure is reads-absent"
  (`:569`) is **STALE** — all six verticals declare `reads:` in their
  `procedures.yaml` (10 occurrences across 6 files; fleet: 3) — noted here because
  it could mislead a reader re-tracing this measurement; fixing that file is out of
  scope. **Consequence:** the only channels into the procedure model are the
  **event** (built by `operational_events` / `_fixture_events`,
  `verticals/fleet_maintenance/data_adapter/synthetic.py:175,198`) and the **goal**
  text — declaring an ontology property routes it into neither.

## Coordination with PLAN-0109 (required — the two PLANs edit the same file)

`docs/plans/0109-fleet-repair-cases-queryable-from-ask.md` Step 1 (`:338-355`) edits
`fleet_maintenance_v0.yaml` — it **adds three new object types** (SD-B **RULED**:
`RepairCase`, `RepairCaseQuote`, `RepairCaseAcceptedQuote`, `/meta` 7 → 10), grows
`_DONOR_EXTENSION_OBJECTS`, and builds the lockstep guard (F10). PLAN-0109 is Draft,
unexecuted, and execution-unblocked (all its blocking SDs ruled).

**Partition (this PLAN's contract, under the ruled SD-3 shape — property-only
extension of the existing `Vendor` block):**

1. **Disjoint file regions.** 0109 appends new type blocks; 0117 edits **inside the
   existing `Vendor` block only** (`:105-151`). A textual merge is clean in either
   landing order.
2. **Disjoint guard surfaces.** 0117 does not touch `_DONOR_EXTENSION_OBJECTS`
   (AC-5 asserts a zero diff); `Vendor` is outside the lockstep guard's mapping (F10);
   0109's AC-1(b) asserts the exact **type-name** list, which property edits cannot
   move; 0117's AC-1(b) asserts the exact **Vendor property** list, which 0109 does
   not touch.
3. **Scope fence.** SD-3 + SD-3a as ruled include **no quote-level facts** — both
   bands are vendor-level; the SD-3a ruling named only the four vendor-level
   properties, and quote-level `warranty` / `on_contract` were **not** in Cray's
   ruling (they stay OUT as a partition boundary, not a cost call — see Out of
   Scope). Standing fence, kept: if any later amendment ever adds a quote-level fact
   (e.g. a per-quote `warranty`), it lands as an amendment to PLAN-0109's
   RepairCaseQuote declaration (whose PII/lockstep/ROPA machinery already governs
   that block), **never** in this PLAN. 0117 stays off the `RepairCase*` blocks
   entirely.
4. **Sequencing (SD-5 — RULED (a), Cray, typed, 2026-08-31, s265): no forced order.**
   Whichever PLAN lands second rebases and re-runs
   `tests/verticals/fleet_maintenance/` + the scaffolder suite before its PR. 0117's
   counts are asserted **relative to the branch baseline** (AC-6), never pinned to
   7-vs-10, precisely so either order stays green. In practice 0109 likely lands
   first (it is fully ruled); nothing here waits for it.
5. **PLAN-0111 is not a party.** Verified by this revision (F14): it names neither
   `fleet_maintenance_v0.yaml` nor `ontology/` — zero grep matches — so no
   coordination contract with 0111 is needed, and the earlier residual gap about it
   is closed.

## Acceptance Criteria

Commands run from the repo root via WSL under CLAUDE.md §8 evidence rules (`2>&1`,
no `head`/`tail` pipes, verdicts read from files). Two ruled bands (both typed, Cray,
2026-08-31, s265): **the synonym-carrying set** (SD-3) = `standing`, `is_contracted`,
`repairs_completed_count`, `comeback_count`, `avg_turnaround_days` — Thai synonyms +
seed values + AUTHORED stamps; **the dormant set** (SD-3a) = `tax_id`, `cert_status`,
`sanctions_flag`, `single_source_flag` — bare declaration + rich `description`,
**no `synonyms` block, no seed values**. Where an AC says "the ruled IN-set" it means
the synonym-carrying five; the dormant four have their own contract (AC-3a). Every
witnessed-RED probe below runs through the shipped driver `tools/probe_battery/`
(CLAUDE.md §8 — never a from-scratch script), one mutation per assertion, restore
from the scratchpad copy. ⚠️ **s275:** the implementation is merged; the boxes below
stay **unticked** until Code witnesses each probe under the corrected wording (the
s275 correction record, C1-C8) — a box ticked against the pre-s275 prose would tick
a criterion the system does not satisfy (C1) or a probe that cannot fire (C2/C3/C6).
Every `uv run` below is read as `uv run --no-sync` (C5's ground, `ci.yml:52-54`: a
bare `uv run` re-syncs without the dev extra and strips pytest mid-run — it fails
loudly, not falsely green, so the pre-existing commands are not rewritten one by one).

- [x] **AC-1 — the YAML declares BOTH ruled bands on `Vendor`, schema-valid.**
  Artifact: `verticals/fleet_maintenance/ontology/fleet_maintenance_v0.yaml`.
  Command (a): `uv run --no-sync pre-commit run check-jsonschema --all-files 2>&1`
  → exit 0 (this also witnesses that a property-level `description` is schema-legal,
  `ontology_schema.json:79` — the SD-3a mechanism). Command (b):
  `uv run python -c "from services.engine.ontology_meta import load_ontology_meta; m=load_ontology_meta('fleet_maintenance'); print(sorted(p.name for o in m.object_types if o.name=='Vendor' for p in o.properties))"`
  → pass read fixed pre-run: exactly the 3 baseline names (F2) plus the
  synonym-carrying five plus the dormant four:
  `['accounting_code', 'avg_turnaround_days', 'cert_status', 'comeback_count', 'is_contracted', 'name', 'repairs_completed_count', 'sanctions_flag', 'single_source_flag', 'standing', 'tax_id', 'vendor_id']`
  (pinned as `_RULED_VENDOR_PROPERTIES`, `test_ontology_data_contract.py:310-323`).
  ⚠️ **s275 C7 (`superseded by new info`):** the "witnessed baseline RED" Step 1
  attached to this command is **un-re-witnessable post-landing** — see Step 1; the
  removal probe (b) below is this AC's witness at closeout.
  Command (c) — **the SD-1(c) comment contract** (two assertions):
  `grep -c "AUTHORED / DEMO SEED" verticals/fleet_maintenance/ontology/fleet_maintenance_v0.yaml 2>&1`
  → **exactly 5** — `== 5`, not `≥ 5`. ⚠️ **s275 C4 (`was an error`):** the pre-s275
  read said `≥ 5`; the landed test asserts **equality**
  (`test_ontology_data_contract.py:352`, `len(stamped) == len(_SYNONYM_BAND)`), so an
  `≥` read would have passed on a stray sixth stamp that the test rejects. (One stamp
  per synonym-carrying property — today at YAML `:170,181,190,202,212`; the dormant
  four carry **no** AUTHORED stamp — nothing is authored for them, their `description`
  is their contract, AC-3a(c)), and
  `grep -n "PROMOTION PATH" verticals/fleet_maintenance/ontology/fleet_maintenance_v0.yaml 2>&1`
  → exactly one block (today `:153`), naming the SD-1(b) measured-projection route.
  **Latent, non-blocking (s275 C4 — flagged, NOT fixed in this PLAN):** the test's
  reader `_raw_vendor_yaml_lines()` (`:326-327`) does
  `_YAML_PATH.read_text().splitlines()` — the **whole YAML file**, not the `Vendor`
  block — so an `AUTHORED / DEMO SEED` stamp added to `Truck` (or any other object)
  would redden this test for a reason unrelated to `Vendor`.
  **Witnessed RED (one probe per assertion):** (a) a scratch undeclared key inside a
  Vendor property block → the hook exits non-zero naming the file
  (`additionalProperties: false`, per 0109 F12) — **measured (Code, s275, by hand
  outside the driver): baseline exit 0 → mutated exit 1, the failure naming
  `fleet_maintenance_v0.yaml` → restored exit 0, mutation gone, porcelain 0**; (b) remove exactly **one** declared
  property from the YAML — **pick a dormant one** (e.g. `tax_id`), so the five's
  synonyms are genuinely untouched and AC-2 stays green under this mutation (the
  cross-green that isolates the probe; the second s265 revision repaired this probe —
  removing a synonym-carrying property would have reddened AC-2 as well, voiding the
  isolation the original text claimed); (c1) strip one property's AUTHORED stamp → the count becomes 4 ≠ 5
  (`:352` reddens) while the PROMOTION PATH grep stays green; (c2) delete the
  PROMOTION PATH comment line → that grep exits non-zero (`:364` reddens) while the
  stamp count stays **exactly 5** (`:352` green) — two mutations, two assertions, each
  with the other's green as isolation. ⚠️ **s275 C8:** (c1) and (c2) are two of the
  ruled probes (15 at s274; 16 after SD-8, ruled (a) s275) — the pre-s275 Step 5
  enumeration dropped them; see Step 5.
- [x] **AC-2 — the facts are Thai-addressable in the translate prompt.**
  Artifact: a new test in `tests/verticals/fleet_maintenance/test_ontology_data_contract.py`
  (the `:120-134` pattern) asserting `_describe_ontology(meta)` contains one designated
  Thai synonym **per synonym-carrying property** (the five — e.g. `ประวัติงานซ่อม`,
  `อู่คู่สัญญา`; the dormant four are synonym-free **by ruling**, guarded by AC-3a's
  cost guard) and still excludes provenance prose.
  Command: `uv run pytest tests/verticals/fleet_maintenance/test_ontology_data_contract.py -x 2>&1`.
  **Witnessed RED:** delete only the `synonyms` block of one ruled property → this test
  reddens on that synonym while AC-1(b) stays green (the property remains declared) —
  one mutation, one assertion, other-assertion-green.
- [x] **AC-3 — the seed carries values for the synonym-carrying five (closing F8's named gap for non-required properties).**
  Artifact: `verticals/fleet_maintenance/data_adapter/synthetic.py` (`vendor_records`)
  + a new presence test in `test_ontology_data_contract.py`: for **each**
  synonym-carrying property, at least one vendor row carries a non-null value (the
  positive control — the dormant four are **excluded by ruling**: unpopulated is
  their contracted state, asserted by AC-3a(b)),
  **and** at least one vendor omits the history facts (the F9 honesty pattern — a
  garage genuinely can have no history yet; keeps any future completeness KPI
  non-vacuous). The existing generic direction-2 guard (`:58-67`) covers undeclared
  keys.
  Command: same module, same pytest command as AC-2.
  **Witnessed RED (two assertions, two probes):** (a) ⚠️ **s275 C2 (`was an error`)
  — the pre-s275 wording "blank the sole carrying row's value" cannot redden: no
  synonym-band property has a sole carrier.** Measured in `vendor_records()`
  (`synthetic.py:356-395`): `standing` is carried by all three rows (`:365,376,395`);
  `is_contracted`, `repairs_completed_count`, `comeback_count` and
  `avg_turnaround_days` by two each (`vendor-01` `:364-368`, `vendor-02` `:375-379`;
  `vendor-03` omits the history facts by design — the F9 honesty row). Blank one row
  and the other still carries, the presence assertion
  (`test_ontology_data_contract.py:218`) stays green, and the driver reports `GREEN`
  — "the mutation reached disk and nothing reddened — the guard may be vacuous"
  (README `:102`) — a probe failure, not a pass. **Corrected probe:** one multi-line
  `old` string spanning **all carriers of one property**, so a single mutation removes
  that property's values from the whole seed. Recommended property:
  `avg_turnaround_days` — the smallest span (two carriers, `:368-379`) and, unlike
  `standing` / `is_contracted`, not referenced by `test_vendor_facts_scenario.py`'s
  pinned expectations (`EXPECTED_APPROVED_IDS`, `EXPECTED_CONTRACTED_ID`, `:44-46`),
  so the mutation stays isolated to the assertion it probes. Mutation shape: set both
  values to `None` — do **not** delete the keys — because the presence test reads
  `r.get(prop) is not None` (`:216`) while the honesty test's positive control reads
  key membership (`history <= set(r)`, `:233-234`) and `_HISTORY_FACTS` includes
  `avg_turnaround_days` (`:164`): `None`-ing reddens only `:218`; deleting would also
  redden `:234` and void the isolation. **Measured (Code, s275) — the cross-green
  checked by hand, because the driver runs ONE node per probe and cannot report it:**
  under the `None`-ing mutation the declared node reddened (exit 1) and the exempted
  honesty claim at `:234` stayed **GREEN** (exit 0); restored to 0 porcelain lines.
  That witnessed green is what makes `:234`'s exemption text ("live and green") true
  rather than assumed; Code re-confirmed the `:164` 3-tuple and `:234`'s
  `history <= set(r)` against the file before writing the probe. Write `old`
  **after** the final `ruff format` pass (README `:108-131`). → the presence test reddens naming `avg_turnaround_days`
  (YAML untouched → AC-1/AC-2 stay green); (b) add a scratch key `x_scratch` to one
  vendor row → the **existing** `test_no_row_carries_a_property_the_ontology_never_declared`
  reddens — witnessing that the pre-existing guard, not a new copy of it, patrols
  direction 2.
- [x] **AC-3a — the dormant band contract (SD-3a): declared, prompt-visible,
  synonym-free, unpopulated, description-carrying.** Artifact: a new dormant-band
  test in `test_ontology_data_contract.py` (it may read the raw YAML — descriptions
  are dropped at load, F13, so loaded meta cannot check assertion (c)). Command:
  `uv run pytest tests/verticals/fleet_maintenance/test_ontology_data_contract.py -x 2>&1`.
  Five assertions, each with its own probe:
  (a) **prompt-visible** — `_describe_ontology(meta)` contains each of the four names
  (Cray's requirement (c): the LLM can use a dormant property the moment a value
  exists, with zero code change). Probe: remove one dormant property from the YAML →
  this assertion reddens naming it while (d) on the remaining three stays green.
  (b) **unpopulated** — no `vendor_records()` row carries any of the four keys
  (dormant = no authored value; also what makes the SD-3a residual concern inert in
  this PLAN — an unpopulated flag cannot disagree with the per-case record). Probe:
  add `sanctions_flag: false` to one seed row → this assertion reddens naming the
  row, YAML untouched so (a)/(c)/(d) stay green — and the existing
  undeclared-key guard also stays green (the key IS declared now), witnessing that
  THIS guard, not that one, patrols dormancy.
  (c1) **description present** — every one of the four carries a non-empty raw-YAML
  `description` explaining declared-but-unpopulated and why. Probe: blank `tax_id`'s
  description → reddens while (c2) stays green.
  (c2) **the residual-concern mitigation** — `single_source_flag`'s description
  names `RepairCaseJustification` as the authoritative record. Probe: strip that
  token from the description → reddens while (c1) stays green (the description is
  still non-empty).
  (d) **the cost guard (dispatch-mandated)** — each of the four has
  `synonyms is None` in loaded `PropertyMeta` (equivalently: its rendered line
  carries no `; aka`), so nobody silently adds the ~90 B-per-list synonym cost
  (F13); synonyms for these four arrive only via a deliberate later YAML edit when
  the narrative brings the Thai term. Probe: add a `synonyms: {th: [...]}` block to
  one of the four → this assertion reddens while (a) stays green (the property
  still renders) — the isolation that proves the redden is about synonyms, not
  declaration.
- [x] **AC-4 — scenario test (CLAUDE.md §8, binding): a supplier-evaluation question is
  answerable end-to-end offline.** Artifact:
  `tests/verticals/fleet_maintenance/test_vendor_facts_scenario.py`. Real producer →
  real consumer: the registered fleet synthetic adapter through
  `answer_question(question, "fleet_maintenance", client=<transport stub>)` — translate
  → execute → phrase all real, only the LLM *transport* canned (`TranslateOnlyStub`,
  the PLAN-0104 precedent) — asking a question over a ruled property (e.g. count of
  vendors with `standing == approved`, and a lookup of the contracted garage).
  Pass read fixed pre-run: `grounded is True`; the count equals the seed's authored
  figure; the lookup's source ids are the seed's `vendor_id`s (rows flowed, not a
  fixture constant). **Plus the dormant case (SD-3a requirement (b), riding F15's
  existing machinery):** a question filtering on a dormant property (e.g. vendors
  with `sanctions_flag == true`) terminates in the honest no-records answer
  (`_no_data_nlanswer`, `nl_query.py:1369-1371` → `:1280`; text composed at `:1103`)
  — never a fabricated fact. ⚠️ **s275 C1 (`was an error`): the pre-s275 prose
  called this outcome "grounded-but-empty"; the engine returns `grounded=False`.**
  Measured: the landed test asserts `ans.grounded is False`
  (`test_vendor_facts_scenario.py:122`), and its docstring (`:105-110`) already
  records the divergence — "the engine actually returns `grounded=False` with
  `result_count=0` via the no-data path … only the AC's parenthetical description of
  `grounded` does not [hold]". **Pass read for the dormant case, restated as the six
  assertions the landed test makes:** `ans.query is not None` (`:120` — the green
  control: translate produced a query); `ans.result_count == 0` (`:121`);
  `ans.grounded is False` (`:122`); `set(ans.source_object_ids) == set()` (`:123`);
  the deterministic text `"No Vendor records match that query." in ans.answer`
  (`:127` — the positive control separating the real no-data path from a crashed
  run, which also yields an empty count and id set); and no seeded garage name in
  the answer (`:129`). The **operative** requirement — an honest no-records answer,
  never a fabricated fact — holds unchanged; only the `grounded` parenthetical was
  wrong, and ticking this AC against the old prose would tick a criterion the system
  does not satisfy. (Where the word came from, kept as lineage: F15 and
  `_no_data_nlanswer`'s own docstring at `:1281`, "A grounded-but-empty answer", use
  "grounded" colloquially — no invented fact — not as the `NlAnswer.grounded` field.)
  Makes **no claim** any live model emits the translation — that is
  MS-S1 territory and out of scope (the vocabulary-width effect on live translate
  quality is explicitly UNMEASURED, F16).
  Command: `uv run pytest tests/verticals/fleet_maintenance/test_vendor_facts_scenario.py -x 2>&1`.
  **Witnessed RED / named changing output:** flip one seed row's `standing` → the
  asserted count changes by exactly 1 (`:76` reddens; `:75` `grounded is True` stays
  green) — the probe's mutation reaches the code and names the output it changes.
  **Dormant-case probe (its own mutation):** author `sanctions_flag: true` onto one
  seed row → the no-records assertion reddens (the answer now carries a record) —
  proving the case exercises the live no-data path, not a constant; AC-3a(b) reddens
  on the same mutation in ITS run, which is exactly the two-guard agreement expected,
  not a confound. ⚠️ **s275 C3 (`was an error`): this probe's `expect_claim` must be
  `:121` (`assert ans.result_count == 0`), NOT the text assert at `:127`.** Measured:
  seeding `sanctions_flag: true` makes `result_count == 1`; pytest stops at the
  **first** failed assert, so the run dies at `:121` and never reaches `:127` —
  declared against `:127`, the driver returns `MISFIRE` ("an assertion failed, but
  not the declared one", README `:99`). Consequently `:127` is a **separate claim** in
  the coverage denominator and, under CLAUDE.md §8's one-mutation-one-assertion rule,
  needs **its own probe** under a mutation that keeps `:121` green — a candidate is
  the no-data template at `nl_query.py:1103`
  (`f"No {query.object_type} records match that query."`), which leaves the count at
  0 and the id set empty while reddening `:127` alone. Whether that probe runs (a
  **16th**, exceeding the ruled 15) or `:127` is exempted with a written reason was
  **SD-8 — RULED (a) (Cray, typed, 2026-09-03, s275): it runs as the 16th**,
  `AC-4-dormant-no-records-TEXT` — subject `nl_query.py:1103`, node `:96`,
  `expect_claim` `:127`; the reworded string leaves `result_count` 0, `grounded`
  False and the id list empty (`:120-123` stay green) and carries no vendor name
  (`:129` stays green) — `:127` is the only assertion that reddens (Step 5). ⚠️ **Not mergeable with AC-3a(b)'s
  probe, though they look it:** AC-3a(b) seeds `sanctions_flag: false` — its
  assertion is key-membership (`test_ontology_data_contract.py:258`, `p in r`); this
  probe seeds `sanctions_flag: true` — its assertion is the `== "true"` filter's
  result count. Seeding `false` here would leave the filter empty and this probe
  `GREEN`.
- [x] **AC-5 — the golden oracle stays green with ZERO exemption growth.**
  Artifacts: `tests/services/engine/scaffolder/test_golden_e2e.py` — **unmodified**.
  Command (a): `uv run pytest tests/services/engine/scaffolder/ -x 2>&1` → green.
  Command (b): `git diff --stat tests/services/engine/scaffolder/ 2>&1` → empty (the
  F7 tripwire: this PLAN adds no object types and no link types, so the exemption must
  not move).
  **Witnessed RED (proving the oracle is alive, not merely un-tripped):** add a scratch
  object type `ScratchObject` to the fleet YAML → the set-equality assertion (`:348`)
  reddens naming it; restore from scratchpad. This is the probe for the surface this
  PLAN promises not to touch.
- [x] **AC-6 — the rest of the vertical is untouched, relative to the branch baseline.**
  Command: `uv run pytest tests/verticals/fleet_maintenance/ 2>&1` → green with zero
  modified assertions in pre-existing tests; object-type count and link-type count
  equal the branch baseline captured in Step 1 (7/7 links pre-0109, 10/7 post-0109 —
  asserted relative, per Coordination §4).
  **Witnessed RED:** covered by AC-5's scratch-object probe (the count read moves on
  the same mutation); no second mutation needed for the same surface. ⚠️ **s275 C7
  (`superseded by new info`) — un-re-witnessable at closeout; ticking this AC is an
  honest statement about a tautological green, not a claimed witness.** Sound when
  written against an unexecuted PLAN with a branch baseline still to capture; after
  landing, "the baseline" and "the tree" are the same tree, so the count read
  compares the tree with itself. Worse, measured s275: **no test asserts the
  object-type or link-type count at all** (`grep -E 'len\([^)]*(object_types|link_types)\)' tests/`
  → 0 matches; `test_golden_e2e.py:348-349` asserts **set** equality against the
  donor YAML — that is AC-5's oracle, not a count), and the AC-5 `ScratchObject`
  mutation leaves the whole fleet suite green — every fleet contract test iterates
  `synthetic.OBJECT_SOURCES` (`test_ontology_data_contract.py:53,65`) and looks
  declared types up by name, so a type declared in YAML but never served enters no
  loop. The count clause is a manual eyeball wearing an AC's clothes: there is no
  pytest assertion for a `Claim.stable_key` to address, so the battery cannot carry
  it (the s274 audit reports `BatteryDefinitionError` — `_battery.py:74` — on the
  attempt; asserted by the audit, not re-traced by this pass). **Not deleted and no
  substitute probe invented:** the pass read that remains honest is "fleet suite
  green, zero modified assertions in pre-existing tests"; the count clause is
  recorded as tautological post-landing and is not what a tick of this box claims.
- [x] **AC-7 — codegen produces zero committed drift, with a positive control.**
  Command: run fleet codegen via the console script (`uv run vero-lite …` — never
  `python -m`), then `git status --porcelain 2>&1` written to a file → **empty** (F6:
  fleet's outputs are gitignored). **Positive control (an absence claim needs one —
  CLAUDE.md §8), restated delete-first — ⚠️ s275 C6 (`was an error`): the pre-s275
  control was itself vacuous.** Measured s275 with codegen **not** run this session:
  `grep '"standing"' verticals/fleet_maintenance/generated/schema.json` already hits
  (count 1). The directory holds seven artifacts from the s265 run
  (`context_pack.md`, `mcp_tools.json`, `models.py`, `orm.py`, `schema.json`,
  `schema.sql`, `types.ts` — dated Aug 31 18:20 per Code's listing, s275), and because
  it is gitignored by construction (`code_generator.py:900-914` — `_ORM_COMMITTED_DEST`
  = {energy, core}, `_PYDANTIC_COMMITTED_DEST` = {core}) a stale artifact simply
  persists. A control that passes before the thing it controls for has happened
  proves nothing about the regen. **Corrected sequence — three reads, each value
  printed, never a bare PASS:** (1) `rm -rf verticals/fleet_maintenance/generated/`
  — free and reversible: the tree is gitignored and fully regenerable; (2)
  `grep -n '"standing"' verticals/fleet_maintenance/generated/schema.json 2>&1` →
  **must FAIL** (no such file) — this is the real control: it proves the instrument
  can report absence; (3) run codegen, then the same grep → **present**, proving the
  regen ran and expressed the new facts. Pattern **quoted** — `'"standing"'` — because
  bare `standing` is a substring of `outstanding` and would match prose. An empty
  porcelain from a codegen that did nothing would otherwise pass vacuously.
  **Measured (Code, s275, delete-first as corrected):** the stale-artifact grep
  returned **1** with codegen never run (C6's vacuous pass, reproduced); after
  `rm -rf`, the control grep exited **2** — it can report absence;
  `uv run --no-sync vero-lite generate fleet_maintenance` exit 0, 7 artifacts; the
  quoted `"standing"` grep then hit, and `tax_id`, `cert_status`, `sanctions_flag`,
  `single_source_flag`, `avg_turnaround_days` were each present in the regenerated
  `schema.json`; `git status --porcelain -- verticals/` = **0** lines, `-- tests/` =
  **0**.
- [x] **AC-8 — full offline gate at CI scope.** ⚠️ **s275 C5 (`was an error`): the
  pre-s275 command list — `uv run ruff check .`, `uv run mypy services/ verticals/`,
  `uv run pytest tests/` — was NOT at CI scope.** Measured against
  `.github/workflows/ci.yml`: (i) **every** CI step runs `uv run --no-sync`, and the
  comment at `ci.yml:52-54` says why — a bare `uv run` re-syncs **without** the dev
  extra and uninstalls pytest/ruff/mypy mid-job; the old list dropped `--no-sync`
  from all three commands while AC-1(a) in this same PLAN had it right; (ii) CI's
  test step is bare `uv run --no-sync pytest -q` (`ci.yml:137`), and the old
  `pytest tests/` **disarmed the AC-12 DB-collapse floor**: `tests/conftest.py:181`
  pins `_FULL_SUITE_ARGS = ["tests"]` and `:192` compares
  `list(args) != _FULL_SUITE_ARGS` — the string `"tests/"` is not `"tests"`, so
  `db_floor_verdict` returned `None` and the floor never fired; bare `pytest -q`
  matches because `pyproject.toml:111` sets `testpaths = ["tests"]`; (iii) four
  further offline-runnable CI gates were absent. **Commands (CI-faithful; from the
  repo root, on the checkout that owns the test DB; each `2>&1` to a file with the
  exit code echoed — CLAUDE.md §8):**
  1. `uv run --no-sync ruff check . 2>&1` (`ci.yml:56`)
  2. `uv run --no-sync ruff format --check . 2>&1` (`:59`)
  3. `node --check` over every `services/api/static/assets/*.js`, floored at
     non-empty exactly as `ci.yml:74-83` does (`shopt -s nullglob`; error if the glob
     matched nothing — a vacuous-pass guard, not decoration).
     **Measured (Code, s275) — closed with a *controlled* instrument, not an install:**
     `node` is absent from this WSL, but `node.exe` v22.16.0 already exists on the
     Windows side and reads the repo over its UNC path, so the host-state change was
     **zero** (Cray had approved an install under CLAUDE.md §8; none was needed).
     Three controls preceded the real reading: a deliberately broken file → exit 1; a
     valid file → exit 0; **a non-existent path → exit 1** — the control that proves a
     resolve failure is not silently read as a pass. Real run: **21 assets enumerated
     from disk, 0 failed**, matching the 21 `ci.yml` measured.
  4. `uv run --no-sync python tools/ci/cache_bust_diff_check.py 2>&1` (`:91`; the
     check compares the PR's two revisions — CI checks out depth 2 — so run it on
     the branch with its parent present)
  5. `uv run --no-sync mypy services/ verticals/ 2>&1` (`:100`)
  6. `uv run --no-sync pre-commit run detect-secrets --all-files 2>&1` (`:113`)
  7. `CI=1 uv run --no-sync pytest -q 2>&1` (`:137`) — bare, no path argument, so
     `session.config.args == ["tests"]`; `CI=1` because the floor's other gate is
     `os.environ.get("CI")` (`conftest.py:190,209`) — without it a local run is green
     with the floor **disarmed** (a drafter addition beyond the dispatch's stated
     fix; stricter, recorded so a local green is not mistaken for a floor-armed one)
  (`ci.yml:116`'s `check-jsonschema` step is AC-1(a)'s own command — run once,
  credited to both.) Pass read: all seven green — partial-scope greens do not close
  this AC. **Two things deliberately NOT "fixed" — checked s275, recorded so no later
  reader reopens them:** CI runs `mypy --strict services/ verticals/` (`:100`) and
  command 5 omits `--strict` — **not a defect**: `pyproject.toml:94` sets
  `strict = true` under `[tool.mypy]` (`:92`), so the CLI flag is redundant; and CI's
  `alembic upgrade head` (`:121`) + `alembic check` (`:131`) need a live database and
  are correctly **out of scope** for an AC that is explicitly the *offline* gate.

## Closeout evidence (s275, 2026-09-03) — what each tick above rests on

Every figure here was **printed by a command run this session** on base `52d4432`
with a clean tree. A prior handoff's "14 of 14" is deliberately **not** cited: Cray
ruled a full re-witness (typed, s274) precisely because s266's per-probe verdicts do
not survive, and none of them are reused below.

### The battery — 16 probes, `PROBE-BATTERY: PASS`

`python -m tools.probe_battery run` printed
`claims: 86 · witnessed RED: 15 · exempted: 71 · GAPS: 0 · stale ids: 0`,
`PROBE-COVERAGE: COMPLETE`, `PROBE-BATTERY: PASS`. All fifteen in-battery probes
returned **`WITNESSED`** — no `GREEN`, no `MISFIRE`, no `CRASHED`, no
`SETUP/COLLECT-ERROR`, no crash-credit. Tree before and after the run differed only
by this PLAN file; `probe_battery status` reported `no unrestored runs`.

| probe | AC | claim it reddened |
|---|---|---|
| `AC-1b-declared-set` | AC-1(b) | `sorted(p.name …) == _RULED_VENDOR_PROPERTIES` (`:338`) |
| `AC-1c1-authored-stamp` | AC-1(c1) | `len(stamped) == len(_SYNONYM_BAND)` (`:352`) |
| `AC-1c2-promotion-path` | AC-1(c2) | `len(marked) == 1` (`:364`) |
| `AC-2-thai-synonym` | AC-2 | `not missing` (`:200`) |
| `AC-3a-presence` | AC-3(a) | `not unsupplied` (`:218`) |
| `AC-3b-undeclared-key` | AC-3(b) | `not undeclared` (`:71`) |
| `AC-3a-a-prompt-visible` | AC-3a(a) | `not absent` (`:245`) |
| `AC-3a-b-unpopulated` | AC-3a(b) | `not seeded` (`:259`) |
| `AC-3a-c1-description-present` | AC-3a(c1) | `not blank` (`:274`) |
| `AC-3a-c2-residual-mitigation` | AC-3a(c2) | `"RepairCaseJustification" in description` (`:287`) |
| `AC-3a-d-synonym-cost-guard` | AC-3a(d) | `not carrying` (`:303`) |
| `AC-4-main-count-moves` | AC-4 | `ans.result_count == len(EXPECTED_APPROVED_IDS)` (`:76`) |
| `AC-4-dormant-no-records` | AC-4 dormant | `ans.result_count == 0` (`:121`) |
| `AC-5-golden-oracle-alive` | AC-5 | `set(emitted["object_types"]) == donor_core` (`:348`) |
| `AC-4-dormant-no-records-TEXT` | AC-4 `:127` | `"No Vendor records match that query." in ans.answer` (`:127`) — the 16th, SD-8 (a) |

**AC-1(a), the sixteenth, ran by hand** — its subject is a pre-commit hook, not a
pytest node, so `tools/probe_battery/` has no `Claim` handle on it and it sits outside
the 86. Measured: baseline exit **0** → with a scratch undeclared key inside a `Vendor`
property block exit **1**, the failure naming `fleet_maintenance_v0.yaml` → restored
exit **0**, the scratch key gone (grep count 0), porcelain 0.

### Three probe definitions were repaired before the run, and the repairs were load-bearing

Each had been predicted to fail by the s274 audit; each was then observed to behave
exactly as predicted, so these are measurements rather than precautions.

- **AC-3(a)** as written could not redden — no synonym-carrying property has a sole
  carrier. Corrected to span both carriers of `avg_turnaround_days`, and on review
  corrected again to set them to `None` rather than delete the keys: `_HISTORY_FACTS`
  (`:164`) is a 3-tuple including this property and the honesty control at `:234` is
  `history <= set(r)`, so a deletion would have reddened a claim this battery **exempts
  as "live and green"** — the exemption would have asserted something false.
  **The isolation was then checked by hand**, because the driver runs one node per probe
  and cannot check it: under the mutation the declared node exited **1** and `:234`
  exited **0**, restoring to 0 porcelain lines.
- **AC-4's dormant probe** declared `:127`; seeding the flag makes `result_count` 1 and
  the run dies at `:121`, so the driver would have returned `MISFIRE`. Declared at `:121`.
- **AC-1(b)'s `old`** initially spanned only part of the `tax_id` block, leaving orphaned
  description continuation lines; the first run returned `SETUP/COLLECT-ERROR` on a
  `ruamel` `ScannerError`, not a witness. Corrected to span the whole block.

### AC-7 — the delete-first control, and what it exposed

The AC's original control was **itself vacuous**: with codegen never run this session,
`grep -c '"standing"' verticals/fleet_maintenance/generated/schema.json` already returned
**1**, because the directory is gitignored by construction and still held artifacts dated
Aug 31 18:20. Reproduced, then corrected. Measured: `rm -rf` the directory → the control
grep exits **2** (it *can* report absence — that is the reading the old control never
took) → `uv run --no-sync vero-lite generate fleet_maintenance` exits **0**, 7 artifacts →
the quoted `"standing"` grep hits, and `tax_id`, `cert_status`, `sanctions_flag`,
`single_source_flag`, `avg_turnaround_days` are each present in the regenerated
`schema.json` → `git status --porcelain -- verticals/` = **0** lines, `-- tests/` = **0**.

### AC-8 — at true CI scope

| command | exit |
|---|---|
| `uv run --no-sync ruff check .` (bare) | 0 |
| `uv run --no-sync ruff format --check .` | 0 |
| `node --check` over 21 JS assets | 0 — **21 checked, 0 failed** |
| `uv run --no-sync python tools/ci/cache_bust_diff_check.py` | 0 |
| `uv run --no-sync pre-commit run detect-secrets --all-files` | 0 |
| `uv run --no-sync pre-commit run check-jsonschema --all-files` | 0 |
| `uv run --no-sync mypy --strict services/ verticals/` | 0 |
| `CI=1 uv run --no-sync pytest -q` | **0** — `4801 passed, 8 skipped, 2 warnings in 721.38s` |

**`node` is absent from this WSL**, but `node.exe` v22.16.0 already existed on the Windows
side and reads the repo over its UNC path, so the host-state change was **zero** (an install
was approved and turned out to be unnecessary). The instrument was controlled before its
first real reading: a file with a real syntax error → exit 1; a valid file → exit 0; and
**a path that does not exist → exit 1**, which is what rules out a resolve failure being
read as 21 clean parses of nothing.

🔴 **An earlier full-suite reading is VOID and is recorded rather than deleted.** It
reported `4 failed, 4793 passed, 8 skipped, 5 errors`. Every one was DB schema contention:
`DROP SCHEMA public CASCADE` deadlocked between two processes in one database, then
`relation "repair_case" / "step_results" / "pipeline_runs" does not exist` followed from a
schema dropped under a live session. The second session was **the Axis-B goal gate's own
`pytest` criterion**, which fires at every Stop — a gate that corrupts the run it is
watching. The criterion was retired and the suite re-run alone; the clean run above is the
one AC-8 is ticked on.

**The DB-collapse floor genuinely armed** — "no floor message" alone cannot distinguish
*armed and cleared* from *never armed*, which is the exact distinction the C5 correction is
about, so it was controlled. Driving `db_floor_verdict` with the real run's `(ci, args)`:
`executed=0` → **message**; `executed=399` (floor is 400) → **message**; `executed=400` →
silent; `ci=None` → silent; `args=["tests/"]` → silent. The last two reproduce, by
measurement, the two C5 defects.

### Two ACs are ticked as un-re-witnessable, not as witnessed

**AC-1(b)'s "witnessed baseline RED"** and **AC-6** cannot fail if run today (C7). Their
inline records state the reason. AC-1(b)'s *probe* is separate and was witnessed above;
only its Step-1 baseline is un-re-witnessable, and the one command that would genuinely
reconstruct it — `git show 61b0edc~1:…` piped into the loader — is recorded and out of
scope. `61b0edc` was confirmed this session as the YAML-edit commit
(`feat(fleet): Vendor carries the supplier-evaluation facts (PLAN-0117 Step 2)`,
105 insertions).

### One correction to this session's own record

The 16th probe's note originally said the replacement text left `:129` "green as well".
It does not: `:129` sits **after** `:127`, the run stops at the first failed assert, so
`:129` was **never reached** and its state is unknown. `was an error`, raised by the
`goal-evaluator`. Only `:120`–`:123` are witnessed green, and they are witnessed precisely
because the failure site is `:127`. The printed battery report keeps the original wording —
it is the authentic artifact of that run and is not rewritten after the fact.

### Registered gap, deliberately not closed

AC-2's two provenance-exclusion asserts (`:203`, `:204`) are named by AC-2's own pass read
and carry no probe; they hold written exemptions. SD-8 resolved the `:127` gap and did not
touch these two.


## Out of Scope

- ❌ **The grader move.** `benchmarks/procedure_baseline/grader.py`, the rationale
  lane, `rationale_regrade.py`, and any change to `carries_content` or the ratified
  role-naming bar (Cray, typed 2026-08-31). Raising the demand side is a **later,
  separate PLAN** — this PLAN gives the facts a declared home and makes them
  answerable on the Ask surface; rationale-lane expressibility additionally needs the
  goal edit (SD-4, that PLAN) **and** the unscoped carrier (next bullet, F17).
- ❌ **The procedure-side carrier — unscoped by ANYONE; named so its absence is
  visible here, not discovered later (F17).** For supplier facts to reach the
  procedure model at all, something must carry values into the **event** (the
  adapter's event builders, `synthetic.py:175,198`) or into the **goal** text
  (`procedures.yaml` — goal edits parked with the grader PLAN by SD-4's ruling).
  No PLAN owns that carrier today. It is not this PLAN's job to build or scope it —
  but whoever scopes the later grader PLAN must scope the carrier with it, or the
  rationale lane stays unmovable regardless of grader edits.
- ❌ **`procedures.yaml` goal text** (SD-4 — **RULED (a)**, Cray, typed, 2026-08-31,
  s265) — the goal is the vocabulary source `role_vocabulary` caps the lane by
  (F1/F4); it moves **with** the grader PLAN so supply and demand land in one
  reviewable diff, its "never withhold a routing decision on quote counts" sentence
  gets rewritten against, not past (F4), and **the re-baseline happens once, there**.
- ❌ **The benchmark dataset** (`dataset/fleet_maintenance.yaml`, F11) — mirroring the
  new facts into scenarios is the demand-side lockstep, same later PLAN.
- ❌ **MS-S1 / any live model run** — host-state, typed Cray go required (CLAUDE.md
  §8). This PLAN is deterministic-offline end to end. Where the eventual live
  measurements go, per the s265 rulings: **the ontology's effect on the two MS-S1
  models is measured on route (a), the NL / Ask surface
  (`benchmarks/nl_query_feasibility/`) — SD-6, RULED** — and F16's UNMEASURED
  vocabulary-width effect (does the wider translate vocabulary, 4 valueless names
  included, raise the empty-result rate?) rides that same route-(a) run.
  Re-measuring the 0/14 vs ~3/14 rationale-lane figures stays with the grader PLAN
  under its own go — and is **deferred until the procedure-side carrier is scoped**
  (previous bullet): before the carrier exists, a procedure-side run would measure a
  channel that does not exist (F17).
- ❌ **NOT swept in by the SD-3a ruling** (stated so nothing rides in silently —
  Cray's ruling named exactly four properties, all vendor-level): quote-level
  `warranty` / `on_contract` stay OUT — they are PLAN-0109's block, a **partition
  boundary** (Coordination §3), not a cost call; and `last_engaged_at` stays OUT —
  derivable, hold until a consumer asks (SD-3's original reason, untouched by the
  ruling). Reopening either takes a fresh typed ruling, not this PLAN.
- ❌ **Synonyms for the dormant four** — deliberately absent under the SD-3a ruling
  (the ~90 B-per-list cost, F13, is the expensive half); they arrive as a later
  cheap YAML edit if and when the narrative actually uses the Thai term, and
  AC-3a(d)'s cost guard makes any earlier addition redden a test.
- ❌ **New object types or link types** — settled by the SD-3 ruling (property-only
  extension; the `VendorServiceRecord` alternative is dead): a new object grows
  `_DONOR_EXTENSION_OBJECTS` against its own tripwire, and a new link reddens the
  golden oracle with **no** exemption slot (F7). Only a fresh typed ruling reopens
  this line.
- ❌ **DB backing, migrations, or projecting `repair_case_*` rows into Vendor facts**
  — SD-1's ruling (c) takes only the **comment** half of option (b): the projection is
  *named* as the promotion path, never built here. No alembic touch; fleet has no
  committed ORM (F6); the free-text `vendor`→registry join and its honesty rules stay
  exactly as `Vendor`'s description states them (F2).
- ❌ **Anything in PLAN-0109's scope** — the `RepairCase*` declarations, the lockstep
  guard, the session-owning adapter, the ROPA/retention corrections (Coordination §3's
  fence).
- ❌ **Promotion of a shared counterparty shape into `ontology/` core — DEFERRED,
  NOT REJECTED** (SD-2 ruling: **SPLIT** — Cray, typed, 2026-08-31, s265). The core
  promotion goes to its **own ADR + PLAN** (both unnumbered today); until they exist,
  **this block is the deferral's durable, tracked home** — a deferred item whose only
  record is a closed conversation rots, and that is the failure mode this block
  exists to prevent. The companion STATUS row is proposed below. Findings from the
  two s265 specialist investigations, **each re-verified on disk by this revision
  (2026-08-31) except where marked**:
  1. **The ontology DSL has no inheritance/subtype/mixin construct at all.**
     `services/engine/ontology_schema.json`: the `property.type` enum is closed
     (`string,int,float,bool,timestamp,date,enum,json,ref,set`, `:76`), every `$def`
     sets `additionalProperties: false`, and no `extends`/`parent`/`abstract` keyword
     exists at any level (whole-file read). The only cross-object levers are `ref`
     (qualifiable `<namespace>.<Type>` per ADR-0033 D2, `:87-91`) and `link_types`
     (no `many_to_many` — deferred per ADR-008 D4, `:158-159`). **A
     superclass/subtype design is not expressible; composition-by-reference is the
     only option.**
  2. **`Person` is NOT a subtyping precedent.** Its promotion was ratified as
     **delete + re-export** (ADR-0033 Alt-4, `docs/adr/0033-shared-ontology-mechanism.md:421-422`
     — "delete + re-export pins the single-source-of-truth end state") — possible
     precisely because the per-vertical Persons had **zero vertical-specific
     fields**. `Supplier`/`Vendor` diverge on real fields — the opposite case.
  3. **ADR-0033 D6 explicitly forecloses a silent second shared type**
     (`0033-shared-ontology-mechanism.md:294-300`): "No second shared object_type is
     authored; … the decision to use it is not pre-granted." The same boundary names
     the reopening route ("re-opens under this grammar with its own concrete
     pressure") — **the deferred work must formally reopen D6, which is why it needs
     an ADR, not just a PLAN.**
  4. **External prior art converges on composition, not inheritance** (s265
     specialist finding; not derivable from this repo): schema.org's `Organization`
     deliberately has **no** `Supplier` subtype — supplier-ness is relational, via
     `seller`/`provider`; Fowler's Party/Role pattern splits stable identity from
     contextual role.
  5. **Recommended future shape (contingent on the future ADR):** `core.Counterparty`
     holding ONLY `counterparty_id` + `name` — the two fields verified identical in
     both live shapes — with each vertical keeping its own fields plus a `ref` to it:
     **HAS-A, never IS-A**. Both vertical docs would then need `imports: [core]`,
     which **no real vertical declares today** (grep across
     `verticals/*/ontology/*.yaml`: zero matches; only a synthetic in-memory test
     fixture exercises the construct).
  6. **The bill, measured:** `_ORM_COMMITTED_DEST` = `{energy, core}` and
     `_PYDANTIC_COMMITTED_DEST` = `{core}` (`services/engine/code_generator.py:900-914`),
     so a core edit changes **two committed, git-tracked files**
     (`services/db/person.py`, `services/engine/procedures/person_model.py`) **plus a
     new alembic migration** (precedent: `alembic/versions/0012_person_table.py`).
     `alembic check` runs in CI (`.github/workflows/ci.yml:118-131`) and locally via
     `tests/services/db/test_migration_orm_lockstep.py`, and reddens without one.
  7. 🔴 **The structural blocker — the single biggest reason the split is correct:**
     `_ORM_COMMITTED_DEST` routes by **namespace → one file**, and `emit_orm` takes a
     whole doc + one output path (`code_generator.py:936-938`). Core's SECOND object
     type therefore either lands inside the Person-named files, or
     `code_generator.py` must gain per-object-type routing — **a generator-mechanism
     change, not a data change** — and bundling that with this PLAN's 5-property YAML
     edit would confound two variables.
  8. **Three tooling gaps the deferred PLAN must also close:** (i) the
     `check-jsonschema` pre-commit glob is `^verticals/.*/ontology/.*\.yaml$`
     (`.pre-commit-config.yaml:55`) and **does not match `ontology/core_v0.yaml`**;
     (ii) there is **no `vero-lite generate core`** — `services/engine/cli.py:29`
     hardcodes `verticals/{vertical}/ontology/{vertical}_v0.yaml`; (iii)
     `docs/runbooks/ontology-migration-autogenerate.md:11-13` is **STALE** — it names
     energy as "the only entry in `_ORM_COMMITTED_DEST`", which
     `code_generator.py:900-903` now contradicts (core is the second entry).
  9. **Guard note:** adding a new CORE object type does **not** redden
     `test_golden_e2e.py` (it reads fleet's own donor YAML) — but **removing `Vendor`
     from fleet's YAML WOULD**: the dead-weight-exemption assert
     `_DONOR_EXTENSION_OBJECTS <= set(donor["object_types"])`
     (`tests/services/engine/scaffolder/test_golden_e2e.py:344-347`). **The future
     core work must not delete `Vendor`.**

  **Proposed `docs/STATUS.md` Active-TODO row** (Code lands this separately, verbatim
  or trimmed to the block cap — it is proposed here so the deferral has a scanned,
  tracked tripwire, not just this PLAN):

  > - [ ] **🆕 CRAY'S CALL — core `Counterparty` promotion: DEFERRED by the SD-2
  >   SPLIT (s265); needs its own ADR (formally reopening ADR-0033 D6) + PLAN.** Not
  >   rejected — split off PLAN-0117 so a generator-mechanism change never rides a
  >   5-property YAML edit. 🔴 Structural blocker: `_ORM_COMMITTED_DEST` routes
  >   namespace→ONE file and `emit_orm` takes one output path
  >   (`code_generator.py:900-914,936-938`) — a second core object type needs
  >   per-object-type routing first. Bill: 2 committed files + an alembic migration
  >   (CI `alembic check` reddens without it) + 3 tooling gaps (pre-commit glob skips
  >   `ontology/`; no `vero-lite generate core`; stale runbook
  >   `ontology-migration-autogenerate.md:11-13`). ⚠️ The future work must NOT delete
  >   fleet's `Vendor` (`test_golden_e2e.py:344`). Shape lean: `core.Counterparty` =
  >   `counterparty_id`+`name` only, HAS-A via `ref` — the DSL has NO inheritance.
  >   **Read:** PLAN-0117 § Out of Scope (deferred-core record).
- ❌ **`services/db/evidence_pack.py` / month-end export changes** — exact-match
  vendor resolution and the AC-9 KPI are untouched.

## Steps

**All SD gates are lifted — no open SDs** (Cray's typed rulings, 2026-08-31, s265;
SD-3a ruled later the same session; SD-6 ruled in the correction pass — it changes
**no step** in this PLAN, only where the later live measurement runs). Step 2
declares **both bands**: the
synonym-carrying five (SD-3) and the dormant four (SD-3a — bare + `description`, no
synonyms, no seed values). The earlier preamble text ("under every option the four
stay undeclared in this PLAN") described the pre-ruling option space and is
superseded by the ruling, which chose an outcome none of the three recorded options
named — see the SD-3a block for the lineage. All work on one `feat/*` branch; one
PR.

### Step 1 — Baseline capture + coordination check

Record on the branch: the current Vendor property list (AC-1(b)'s command at baseline
— this run is AC-1(b)'s witnessed baseline RED for the new names), the object/link
type counts (AC-6's relative baseline), and whether PLAN-0109 has landed (Coordination
§4 — if it has, re-verify F2/F7 line anchors before editing). Confirm `git status` in
the first tool batch per standing hygiene.

⚠️ **s275 C7 (`superseded by new info`) — the "witnessed baseline RED" above is
un-re-witnessable at closeout.** Sound when written: this step ran before the YAML
edit, so the 12-name pass read was genuinely RED. The YAML edit landed 2026-08-31
(`61b0edc`, per the s275 dispatch); running AC-1(b)'s stated command today returns all
12 names → **GREEN**, not RED. The **only** command that would genuinely re-witness the
baseline is a reconstruction —
`git show 61b0edc~1:verticals/fleet_maintenance/ontology/fleet_maintenance_v0.yaml`
written to a scratch path and fed to the loader in place of the tracked file — a
materially different command from the one the AC states, and **out of scope for this
closeout unless Cray rules otherwise**. Ticking AC-1(b) at closeout therefore credits
its **removal probe** (the dormant-property mutation — one of the ruled 15), not this
baseline, which is recorded as an honest tautological green. Nothing deleted, no
substitute invented. The same classification covers AC-6's relative count (see AC-6).

### Step 2 — Author the `Vendor` extension in the YAML (AC-1, AC-2)

Inside the existing `Vendor` block only (Coordination §1): declare the ruled IN-set
under ADR-008 D1's "may extend" license, mirroring the house provenance style —
every value-bearing comment states **AUTHORED / DEMO SEED, not a partner answer**,
names the future intake question that promotes it (the `minor_repair_ceiling_thb`
precedent, F2's guess-and-react discipline: a promoted fact retires its stamp, an
unanswered one keeps it), and Thai-first synonyms per property (`_property_aliases`
rationale). Per **SD-1=(c)**, one comment block inside `Vendor` records the
**PROMOTION PATH**: the measured projection (SD-1 option (b)) — aggregate
`repair_case_quote` / `repair_case_accepted_quote` / closeout rows joined on the
exact-match free-text `vendor` name (F2's rule) — as the route that retires the
AUTHORED stamps once real volume exists (today the export holds one row, F12).
Ruled declarations, band 1 (SD-3, s265): `standing` (enum
`[approved, probation, suspended]`), `is_contracted` (bool — the narrative's
อู่คู่สัญญา, F9), `repairs_completed_count` (int), `comeback_count` (int),
`avg_turnaround_days` (float). All **non-required** — a garage with no history is a
real state (F9's honesty pattern), which is also why AC-3 must exist (F8's gap).

Ruled declarations, band 2 — **the dormant four** (SD-3a, s265): `tax_id` (string),
`cert_status` (enum `[valid, expired, none]` — the donor's values, F3),
`sanctions_flag` (bool), `single_source_flag` (bool). Shape per the ruling: bare
`name` + `type` (+ enum `values` where enum), **no `synonyms` block** (AC-3a(d)'s
cost guard), no seed values, and a **rich `description`** per property — schema-legal
(`ontology_schema.json:79`), dropped at load so it costs zero prompt bytes (F13) —
explaining that the property is declared-but-unpopulated and why (the narrative may
bring some, not necessarily all, of these facts later; declaring now means the
Ask/translate LLM can use a value the day it exists — Cray's requirements (a)-(c),
read per the Correction record's SD-3a note: the procedure model sees no ontology
property either way, F17).
`single_source_flag`'s description additionally carries the residual-concern
mitigation verbatim in substance: the per-case `RepairCaseJustification` (ADR-0034
D4) is the **authoritative** sole-source record; this vendor-level flag is
**advisory, never the basis for a gate decision**, and if it is ever populated its
value must be **derived from the per-case records, never independently authored**
(AC-3a(c2)).

### Step 3 — Extend the seed (AC-3)

`vendor_records()`: DEMO SEED values labelled as such — the contracted garage carries
`is_contracted: true`, `standing: approved`, and a plausible small history; one vendor
carries `standing` but **no history facts** (the "used once, no record yet" row —
mirrors the uncoded-`accounting_code` row's stated purpose). No real vendor data is
invented (F9's public-repo rule for codes applies to history figures identically).
**The dormant four get NO seed values** — unpopulated is their contracted state
(SD-3a; AC-3a(b) asserts it), and an unpopulated question routes to the honest
no-records answer through existing machinery (F15, witnessed by AC-4's dormant case).

### Step 4 — Tests (AC-2, AC-3, AC-3a, AC-4)

Extend `test_ontology_data_contract.py` with the synonym-rendering and per-property
presence tests (generic over the ruled set where practical — F8's "guard for the NEXT
property" spirit) **plus the dormant-band test** (AC-3a: prompt-visible, unpopulated,
description contract, cost guard — the description assertions read the raw YAML, F13).
New `test_vendor_facts_scenario.py` per AC-4's fixed reads, including the dormant
no-records case (`TranslateOnlyStub` precedent:
`tests/services/engine/test_grouped_count_scenario.py`).

### Step 5 — Probe battery (every witnessed RED above)

⚠️ **s275 C8 (`was an error`): the pre-s275 enumeration — "AC-1(a)/(b), AC-2,
AC-3(a)/(b), AC-3a(a)/(b)/(c1)/(c2)/(d), AC-4 (both mutations), AC-5" — counted 13
and silently dropped AC-1(c1) and AC-1(c2), which AC-1 itself defines as "two
mutations, two assertions".** The corrected total was **15**, equal to the count Cray ruled
for the full re-witness (typed, s274) — **and is 16 under SD-8, RULED (a) (Cray, typed,
2026-09-03, s275; verbatim: "(a) 16 probe เลย"): 15 in-battery + AC-1(a) by hand.**
Lineage, kept explicit: 15 was correct for the scope known at s274; SD-8 surfaced a claim
that scope had not accounted for, and Cray widened it — `superseded by new info`, not
`was an error`; 16 was not always the number. C8's 14-in-battery becomes 15 in-battery:

| AC | probes | node / mutation (in-battery unless marked) |
|---|---|---|
| AC-1(a) | 1 | **outside the driver** — its subject is the `check-jsonschema` pre-commit hook, not a pytest node, so `tools/probe_battery/` has no `Claim` to address. Run by hand under the same discipline: scratch key → hook exits non-zero naming the file → restore; evidence file + printed exit code |
| AC-1(b) | 1 | `test_the_vendor_block_declares_exactly_the_ruled_property_set` (`test_ontology_data_contract.py:330`) — remove one dormant property from the YAML |
| AC-1(c1) | 1 | `test_every_authored_value_carries_its_demo_seed_stamp` (`:341`) — strip one stamp → 4 ≠ 5 |
| AC-1(c2) | 1 | `test_the_promotion_path_is_recorded_exactly_once` (`:358`) — delete the PROMOTION PATH line |
| AC-2 | 1 | `test_the_translate_prompt_carries_a_thai_name_for_every_supplier_fact` (`:192`) — delete one `synonyms` block |
| AC-3(a) | 1 | `test_every_supplier_fact_has_at_least_one_carrying_row` (`:207`) — `None` both `avg_turnaround_days` values (C2) |
| AC-3(b) | 1 | the existing `test_no_row_carries_a_property_the_ontology_never_declared` (F8, `:58-67`) — `x_scratch` on one row |
| AC-3a(a)/(b)/(c1)/(c2)/(d) | 5 | `:237`, `:248`, `:262`, `:277`, `:291` — exactly as AC-3a states them |
| AC-4 count | 1 | `test_counting_approved_garages_runs_on_real_rows` (`test_vendor_facts_scenario.py:64`) — flip one `standing`; `expect_claim` `:76` |
| AC-4 dormant | 1 | `test_a_dormant_property_reaches_the_honest_no_records_answer` (`:96`) — seed `sanctions_flag: true`; `expect_claim` **`:121`** (C3) |
| AC-4 dormant TEXT — **the 16th (SD-8, ruled (a) s275)** | 1 | `AC-4-dormant-no-records-TEXT` — subject `services/engine/nl_query.py:1103` (`_no_data_answer`: `return f"No {query.object_type} records match that query."`); node `test_a_dormant_property_reaches_the_honest_no_records_answer` (`:96`); `expect_claim` **`:127`**. Mutation: reword the string in place — `result_count` stays 0, `grounded` stays False, the id list stays empty, so `:120/:121/:122/:123` stay GREEN; the replacement carries no vendor name, so `:129` stays green; `:127` is the only assertion that reddens |
| AC-5 | 1 | `test_golden_e2e.py:348` — `ScratchObject` in the fleet YAML |
| **Total** | **16** | **15 in-battery + 1 outside the driver (AC-1(a))** — was 15 = 14 + 1 under the s274 ruling (C8), widened by SD-8 |

Run the 15 through `tools/probe_battery/` — one claim per probe, `Claim.stable_key`
addressing, scratchpad-backed restore — and AC-1(a) by hand with the same evidence
discipline (CLAUDE.md §8; module README, PLAN-0115). Write every `old` **after** the
final `ruff format` pass (README `:108-131`). If a probe fails its pre-fixed
criterion, repair the instrument — never relax the criterion after seeing the result.

**The 16th — SD-8, RULED (a) (Cray, typed, 2026-09-03, s275):** the landed dormant
test's text assert (`test_vendor_facts_scenario.py:127`) is a separate claim that the
AC-4 dormant probe cannot credit (C3), and it now carries its own probe,
`AC-4-dormant-no-records-TEXT` (table row above). **Why its own probe rather than
riding `:121`:** an empty result set and an empty id list are also what a CRASHED run
produces; the deterministic no-records TEXT is the one thing only the real no-data
path emits (the test's own comment, `:124-126`). Lineage: as drafted pre-ruling, the
15 ran as enumerated with `:127` under a **provisional exemption whose text named
SD-8** — a flagged disposition, never a silent one — and the 14-probe run Code
measured at that stage (`PROBE-BATTERY: PASS`; `claims: 86 · witnessed RED: 14 ·
exempted: 72 · GAPS: 0 · stale ids: 0`; `PROBE-COVERAGE: COMPLETE`; every probe
`WITNESSED`, no GREEN / MISFIRE / CRASHED) stands as the pre-ruling baseline. The
provisional exemption is **retired** — `:127` is credited by its probe, not exempted.
The 16-probe re-run's result is Code's to record from the printed report, not this
draft's.

**Coverage report capture (the unhomed Verification-§5 requirement, homed here):** the
report is **stdout only** (`_battery.py:577`; nothing is written to disk) — capture the
run with `2>&1` into a file under the scratchpad *and* the session handoff directory;
the passed run's report is the PR-body artifact Verification §5 names, and it is
unrecoverable otherwise. Expect **71 written exemptions** (86 claims measured by Code
s275 − **15** in-battery credits under SD-8 ruled (a); the pre-ruling 72 = 86 − 14 is
the figure the 14-probe run printed; AC-1(a) is outside the 86, so not 86 − 16 = 70 —
the s275 record's arithmetic note) — every unexplained GAP
makes the verdict `PROBE-BATTERY: FAIL` (`:570`), and two of the 71 are AC-2's own
provenance-exclusion asserts (`:203-204`; the s275 record's known-gaps note). Do not
narrow `claim_sources` to shrink the denominator (`tools/probe_coverage.py:25-30`).

### Step 6 — Regenerate, gate, close (AC-5, AC-6, AC-7, AC-8)

Run fleet codegen + the AC-7 porcelain/positive-control pair; run the scaffolder suite
and the zero-diff read (AC-5); full vertical suite with the relative counts (AC-6);
the CI-scope offline gate (AC-8). Update `docs/STATUS.md` per session hygiene. PR via
branch per CLAUDE.md §7 (Code commits; Cray merges by default). After merge + Cray
closeout, `git mv` to `docs/plans/done/`.

## Surfaced decisions — RULED (Cray, typed, 2026-08-31, session 265), original recommendation texts preserved for reasoning lineage

Every SD below carries its ruling inline — **including SD-3a, ruled later in the
same session, SD-6, ruled in the s265 correction pass, SD-7 (ruled s270) and SD-8
(ruled s275); nothing remains open.**
Where a ruling's *reasoning* differs from the
original recommendation (SD-2), or the ruling *overturns* recommendations outright
(SD-3a overturns both this draft's OUT disposition for the four and Code's own
"YAML comments only" recommendation), all versions are recorded — this repo keeps
lineage; nothing is deleted.

### SD-1 — RULED (c) — the ontology↔evidence-table seam: what backs the new facts?

The hardest question in this PLAN (dispatch's own framing), not papered over. The real
transactional truth lives in hand-written evidence tables (F6); the new facts describe
vendors *across* cases. Options:

- **(a) Ontology + synthetic seed only — RECOMMENDED.** Declare the properties; values
  are DEMO SEED in `vendor_records()`; no DB, no migration (F6 makes this the
  zero-migration path). Cost, stated: the facts are **authored, not measured** — every
  comment says so (backfilled/authored values are marked, house rule), and the demo
  shows authored history until a partner answer or a projection promotes it.
- **(b) Measured projection.** Compute history from `repair_case_quote` /
  `repair_case_accepted_quote` / closeout rows at serve time, joining on the exact-match
  free-text `vendor` name (F2's rule). Cost: an aggregation seam in an adapter that is
  only now gaining DB access (0109 SD-A), honest handling of unmatched names, **and**
  near-zero real volume today — a "history" of n=1 cases is noise wearing a number.
- **(c) Declare now, name the projection as the promotion path.** (a) today, with the
  (b) design recorded in comments as the intake/measurement route.

Recommendation: **(a) with (c)'s pointer recorded**. Why Cray, not Code: this decides
whether the demo surface shows authored or measured facts — a truthfulness-of-the-demo
call under ADR-0032 D1's correction-surface discipline, and it fixes the evidence story
the later grader PLAN inherits.

**RULING (Cray, typed, 2026-08-31, s265): (c).** Declare the properties with
DEMO-SEED values now, **and** record the measured-projection route (option (b)) in
comments as the promotion path; every authored value carries its **AUTHORED**
provenance stamp (the house backfilled-value rule; enforced by AC-1(c)). This matches
the draft's "(a) with (c)'s pointer" recommendation in substance — the ruling names
(c) as the frame. **New evidence since drafting:** option (b)'s cost is now
**measured, not asserted** — the month-end export holds exactly one row
(`case-fleet-demo-history`; F12, measured by Code s265), so "a history of n=1 is
noise wearing a number" is a fact, not a forecast.

### SD-2 — RULED: SPLIT — duplicate into fleet vs promote to `ontology/` core

Procurement's `Supplier` and fleet's `Vendor` are the same *idea* at N=2 with different
shapes (a bolt supplier carries AVL/sanctions machinery; a garage carries comebacks and
turnaround). Recommendation: **fleet-side extension, no promotion** — Rule of Three
(ADR-006) says extract after 3 working verticals, and the one prior core promotion
(Person, ADR-0033) was forced by a runtime engine consumer that has no analogue here.
Alternative: promote a minimal shared `supplier-evaluation` fragment now. Why Cray:
promotion changes what every 7th vertical inherits — architecture direction, not a
drafting call.

**RULING (Cray, typed, 2026-08-31, s265): SPLIT — and the reasoning CHANGED; both
are recorded.** Sequence, kept for lineage: Cray initially ruled "promote to core";
after two specialist investigations returned (DSL expressibility; the promotion
bill), the ruling became a split:

- **This PLAN executes the fleet-side extension** — the same *action* the original
  recommendation named, **but for a different reason, and the new reason is the
  ruling's substance**. The original ground was "Rule of Three (ADR-006) says wait at
  N=2." That is **no longer the operative reason**. The operative reason: **the core
  promotion is real architecture work with its own bill** — a generator-mechanism
  change (the namespace→one-file routing blocker, Out-of-Scope finding 7), two
  committed files + an alembic migration (finding 6), three tooling gaps (finding 8),
  and a formal reopening of ADR-0033 D6 (finding 3) — **and bundling that with a
  5-property YAML edit would confound two variables** (the
  one-variable-per-change discipline).
- **The core promotion is DEFERRED, NOT REJECTED** — to its own ADR (reopening
  ADR-0033 D6 is an architecture decision, not a PLAN step) plus its own PLAN. Its
  durable, tracked record is the Out-of-Scope deferred-core block + the proposed
  STATUS Active-TODO row there — never only a closed conversation.
- The original recommendation's `Person` point survives **strengthened**: ADR-0033's
  promotion was delete+re-export of a zero-divergence type (Alt-4, `:421-422`) — not
  a subtyping precedent for the field-divergent `Supplier`/`Vendor` pair (Out-of-Scope
  finding 2).

### SD-3 — RULED (the IN-set) — the property IN/OUT set (the port filter)

Each property widens the translate vocabulary and costs prompt tokens in every call
(PLAN-0109 SD-B's pricing) — the set should be the smallest that makes the three
approver questions expressible. Menu, priced:

- **Recommended IN (5):** `standing` (the fraud narrative F5 gives it teeth — the
  small-operator register of `avl_status`); `is_contracted` (narrative-grounded:
  อู่คู่สัญญา is literally the seed's first garage, F9 — "is this the right supplier"
  is partly "is this our contracted garage"); `repairs_completed_count`,
  `comeback_count`, `avg_turnaround_days` (the delivery-history facts an approver
  actually asks).
- **Recommended OUT, with reasons recorded per Lesson 0052's rule (unmeasurable ≠
  forgotten):** `tax_id` / `cert_status` / `sanctions_flag` — corporate-compliance
  machinery the narrative's garages don't carry; dead vocabulary tokens.
  `single_source_flag` — fleet models sole-source **per case** via
  `RepairCaseJustification` (ADR-0034 D4's evidence-alternative); a vendor-level flag
  would double-state it. `on_contract`/`warranty` at quote level — 0109's block,
  Coordination §3's fence. `last_engaged_at` — derivable, hold until a consumer asks.
- **Alternative shape:** a new `VendorServiceRecord` object (one row per engagement) —
  richer, but grows `_DONOR_EXTENSION_OBJECTS` against its own tripwire and needs
  either synthetic engagement rows or SD-1(b)'s projection; priced OUT by F7 unless
  Cray wants the row-level story now.

Why Cray: this set **is** the future bar's vocabulary — it bounds what the later
grader PLAN may ever demand, and the OUT-list is a partner-facing modelling claim
about what a Thai garage is.

**RULING (Cray, typed, 2026-08-31, s265): the 5 recommended IN properties are IN** —
`standing`, `is_contracted`, `repairs_completed_count`, `comeback_count`,
`avg_turnaround_days`. ⚠️ At first ruling, **the disposition of the 4 OUT properties
was NOT ruled** — Cray asked a follow-up question about them, Code measured the
answer, and the question became sub-decision **SD-3a** below. The alternative
`VendorServiceRecord` shape is dead under the ruling (no new object types).

**Resolved later the same session — SD-3a RULED (see its block): all four are
DECLARED, bare + rich `description`, NO synonyms.** The consistent post-ruling
framing of this SD's set is therefore **two bands, one declared set**: the five
above are the **synonym-carrying, narrative-grounded band** (Thai synonyms + seed
values + AUTHORED stamps); the four are **declared-but-dormant, NOT OUT**
(prompt-visible by name, synonym-free, unpopulated). The OUT bullet above stays as
lineage: its cost reasons ("dead vocabulary tokens") were answered by the F13
measurements and overturned; its `single_source_flag` reason was a **correctness**
objection and survives as the **noted residual concern** under the SD-3a ruling.
Still genuinely OUT, untouched by SD-3a: quote-level `on_contract`/`warranty`
(0109's block) and `last_engaged_at` — see the SD-3a not-covered list.

### SD-3a — RULED (declare all four: bare + rich `description`, NO synonyms) — the 4 OUT properties: can they be kept "optional, skipped when there is no data, without costing prompt tokens"?

Cray's question, verbatim in substance. The measured answer (Code, s265; the
structural halves re-verified on disk by this revision — F13): **no such free slot
exists today.** *(The bullets below are the pre-ruling record, kept as lineage —
the RULING block after them supersedes their option framing.)*

- **Sizes (F13):** the whole fleet prompt-schema block is 1,945 B across 7 object
  types; the `Vendor` line is 339 B; the 5 IN properties add **+145 B (7.5%)**; the 4
  OUT ones would add **+107 B (5.5%)**.
- **Structure (F13, verified):** `_describe_ontology`
  (`services/engine/nl_query.py:382-398`) renders **every declared property with no
  value check**, and `PropertyMeta` (`services/engine/ontology_meta.py:268-285`)
  carries no visibility/queryable flag — **"auto-skip when unpopulated" does not
  exist today**. `ontology_schema.json`'s `additionalProperties: false` also
  forecloses parking them in a documentation-only YAML key.
- **Expressible options — all three recorded (pre-ruling; none was chosen as
  written):**
  1. **YAML comments only** — free, zero code, zero tokens, not machine-readable.
     **Code recommended (1)** *(overturned by the ruling — recorded for lineage)*.
  2. **Build a `prompt: false` property flag** — ~4 files + a guard; yields
     "declared but dormant"; saves the 107 B. Hazard, named: a property hidden from
     the prompt is one the LLM **can never query** until the flag is flipped —
     dormant means *invisible*, not *optional*.
  3. **Do not declare them** — the reasons live in this PLAN (this SD-3/SD-3a record
     is the durable home).
- **Considered and advised AGAINST (recorded so it is not re-invented):** a
  data-driven "render only if some row has a value" variant — it puts a DB read on
  every translate call (the hot path) and makes the prompt **data-dependent**, which
  breaks benchmark comparability — the very surface SD-4's ruling protects.
- **Gating (pre-ruling note, superseded):** the original text here said "under every
  option the four stay undeclared in this PLAN" — true of the three options as
  written, but the ruling chose a fourth shape none of them named, and the four now
  **do** enter this PLAN. Why Cray (unchanged): the OUT-list is a partner-facing
  modelling claim (SD-3's original ground), and mechanism-vs-comment was a spend
  call against a measured 107 B saving.

**RULING (Cray, typed, 2026-08-31, s265): DECLARE all four now — `tax_id`,
`cert_status`, `sanctions_flag`, `single_source_flag` — bare `name` + `type` (+ enum
`values` where the type is enum: `cert_status`), a rich `description` per property,
and NO `synonyms` block yet.** This **overturns two recommendations, both preserved
above for lineage**: this draft's SD-3 OUT disposition for these four, and Code's
own option-(1) "YAML comments only" recommendation.

- **What decided it — Cray's requirement, three parts that must hold at once:**
  (a) the narrative may mention these properties in future; (b) it may bring only
  SOME of them, not all four; (c) **the LLM must be able to use them effectively in
  its reasoning once a value exists.** Requirement (c) eliminates every option that
  hides the property from the prompt — both option (1) and option (2)'s
  `prompt: false` flag leave a property that HAS data but cannot be used until a
  human intervenes.
- **What makes declaring cheap (measured, F13; structural halves re-verified on disk
  by this revision):** `description` is absent from `PropertyMeta` entirely —
  dropped at load, by documented design (`nl_query.py:363-371`) — so a rich
  description costs **ZERO prompt bytes**; **`synonyms` is the expensive part**
  (~90 B for the existing `name` property's list alone, vs ~17-26 B for a bare
  name+type line); the four bare cost **+107 B on the 1,945 B block (5.5%)** —
  roughly 30 tokens per translate call.
- **Partial population needs no new mechanism (requirement (b) satisfied):** a
  declared property with no values yields an empty result, which routes to the
  existing honest-no-records path (`_no_data_nlanswer`, F15 — the "never invent"
  discipline), not a fabricated answer. Witnessed offline by AC-4's dormant case.
- **Enforcement in this PLAN:** AC-1(b) (the 12-name list), AC-3a (prompt-visible,
  unpopulated, description contract, and the **cost guard** — a `synonyms` block
  added to any of the four reddens a test), Step 2's band-2 declaration spec.

**🔴 Noted residual concern under the ruling (flagged, NOT re-ruled):** the original
OUT reason for `single_source_flag` was **not** a token argument — it is a
**correctness objection of a different kind from the cost question Cray was
answering**. Fleet models sole-source **per case** via `RepairCaseJustification`
(ADR-0034 D4's evidence-alternative), so a vendor-level flag **double-states** the
same fact at two levels, and the two copies can DISAGREE. Cray ruled all four in,
so all four go in — but this risk is recorded visibly rather than silently
absorbed. **Cheapest mitigation, adopted (free — descriptions cost zero prompt
bytes):** the flag's `description` states that the per-case
`RepairCaseJustification` is the **authoritative** record, that the vendor-level
flag is **advisory — never the basis for a gate decision** — and that if it is ever
populated, its value must be **derived from the per-case records, never
independently authored** (removing the second author removes the disagreement
channel by construction). Enforced textually by AC-3a(c2). **Honest adequacy
judgment:** *sufficient while dormant* — AC-3a(b) keeps the flag unpopulated in
this PLAN, and an unpopulated flag cannot disagree with anything; **not sufficient
on its own once populated** — the description is invisible to the LLM at translate
time (dropped at load, F13) and no guard executes a prose authoring rule, so the
change that first populates this flag MUST bring a machine check (flag ⇔ per-case
justification consistency) or the disagreement channel reopens. That future check
is flagged here for whichever PLAN first authors a value; it is not built now.

**What this ruling does NOT cover (nothing silently swept in — Cray named exactly
four properties, all vendor-level):** quote-level `warranty` / `on_contract` stay
OUT — they are PLAN-0109's block, a **partition boundary** (Coordination §3), not a
cost call; `last_engaged_at` stays OUT — derivable, hold until a consumer asks
(the original reason, untouched). See the Out-of-Scope not-swept-in bullet.

**⚠️ Asserted-not-verified, UNMEASURED (F16):** the answer-quality effect of the
wider translate vocabulary — a model may attempt queries that return empty more
often. Measuring it needs a live MS-S1 run under a typed CLAUDE.md §8 go. The
original recommendation here (fold it into the later grader PLAN's MS-S1 round) is
**superseded by the SD-6 ruling**, kept as lineage: it now rides the ruled route-(a)
run on `benchmarks/nl_query_feasibility/` — the surface where a translate-vocabulary
effect is actually observable.

### SD-4 — RULED (a) — `procedures.yaml` goal text: pre-thread now, or move with the grader?

RESULTS §13 is explicit that answerability needs the ontology **and the goal** (F1);
`role_vocabulary` reads only the goal (F1). Options: **(a) leave the goal untouched in
this PLAN — RECOMMENDED** — the goal edit and the grader edit are one supply-and-demand
pair and should land in one reviewable diff (the same pair-landing spirit as 0109's
declare+guard REJECT-IF), and the current "applied DOWNSTREAM … never withhold on quote
counts" sentence (F4) must be *rewritten against*, which deserves its own PLAN's
attention; **(b)** pre-thread supplier vocabulary now so the later PLAN is grader-only.
Why Cray: the goal is a ratified prompt surface (its trigger ruling was typed, s243)
and the benchmark's measurement surface — editing it re-baselines every banked number.

**RULING (Cray, typed, 2026-08-31, s265): (a).** The goal text stays untouched in
this PLAN; the goal edit pairs with the grader edit in the later PLAN, and **the
re-baseline happens once, there.** As recommended.

### SD-5 — RULED (a) — sequencing vs PLAN-0109

**(a) No forced order — RECOMMENDED** (Coordination §1-§4: disjoint regions, disjoint
guard surfaces, second-lander rebases); **(b)** strict 0109-first (simplest mental
model; 0109 is fully ruled and unblocked anyway). Why Cray: two Draft PLANs claiming
one file is a routing/priority call between sessions, exactly the class Tier-3 owns.

**RULING (Cray, typed, 2026-08-31, s265): (a).** No forced order; disjoint regions;
the second-lander rebases (Coordination §4). As recommended. Additionally, verified
on disk by this revision: **PLAN-0111 touches neither the fleet YAML nor
`ontology/`** (F14, zero grep matches) — the earlier "asserted-not-verified" residual
note about 0111 is **CLOSED**, and 0111 needs no coordination contract
(Coordination §5).

### SD-6 — RULED (a) — where is the ontology's effect on the two MS-S1 models measured?

Arose in the s265 correction pass, not in the original draft: the pre-correction
framing implied the ontology's effect could be read off `procedure_baseline`'s
rationale lane, and F17's measurement showed the ontology is not on that prompt path
— a run there would measure a channel that does not exist. Options:

- **(a) The NL / Ask surface — `benchmarks/nl_query_feasibility/`** (harness,
  `gold.yaml`, `run_benchmark.py` verified on disk by this revision). On this route
  the declared facts genuinely reach the model: `_describe_ontology` feeds the
  translate prompt (F13) and the seed serves the values (AC-3/AC-4).
- **(b) `procedure_baseline`.** Only meaningful after the unscoped event/goal
  carrier exists (Out of Scope, F17) and the SD-4 goal edit lands — before that, any
  delta measured there is noise attributed to a channel that is not connected.

Why Cray: this fixes which banked benchmark lane the ontology work is accountable
to — a measurement-surface ruling of exactly the kind SD-4 protected.

**RULING (Cray, typed, 2026-08-31, s265): (a).** The ontology's effect on the two
MS-S1 models is measured on the NL / Ask surface, route (a) — **because there the
facts genuinely reach the model, so the experiment measures the ontology rather
than measuring a channel that does not exist.** The procedure-side question is
**deferred until the carrier is scoped** — deferred, not ruled. Consequences
recorded: F16's vocabulary-width measurement rides this route-(a) run (the earlier
fold-into-grader-PLAN recommendation is superseded, kept as lineage in F16 and the
SD-3a block); any live run still requires its own typed CLAUDE.md §8 go; nothing in
this PLAN's offline ACs moves.

### SD-7 — RULED (decide from the standing principle) — `fl-21`/`fl-22`: score the answer or the query? (ruled s270)

✅ **RULED: decide it from the lane's principle, blind to these two results.** Cray,
typed, 2026-09-02 (session 270). Applying that ruling closes the question **without a
new criterion**, because the principle already exists and predates the cases.

The question, as STATUS carried it since s265-266: gpt-oss emits `group_by: null` on
`fl-21`/`fl-22` while qwen emits `group_by: vendor_id`; gpt-oss's **prose answer is
right** (the identity came from the phrase step reading records, not from the
aggregate). STATUS flagged the hazard itself — *"deciding it now, with the result
visible, would relax a criterion after seeing the outcome"* — i.e. HARK, the same class
CLAUDE.md §8 forbids when it says never repair by relaxing the criterion that just
failed.

**The standing principle, quoted from where it lives** — `harness.py::score_case`'s
docstring:

> `ceiling=false` → `result_ok`: the executed result (count + id set) equals the
> hand-verified gold — invariant to how the filter was phrased.
> `ceiling=true` → `answer_ok`: the phrased answer carries every expected substring.

**It is uncontaminated, and this is checkable rather than asserted** (`git log -S`):

| commit | date | what |
|---|---|---|
| `ff5bab8` | **2026-06-14** | the `ceiling=false → executed result` principle enters `harness.py` |
| `31b90d9` | 2026-08-31 | `fl-21` is authored |
| `01f2881` | 2026-08-31 | the `fl-21`/`fl-22` result is recorded |

The criterion was fixed **78 days before the case existed** and 78 before any of these
outputs were seen. Nothing about it can have been tuned to them.

**Therefore, mechanically:** `fl-21` and `fl-22` both carry `ceiling: false`, so they
score the **executed result** — `expected_aggregate`, `groups` included — and **not**
the prose answer. `_aggregate_ok` returns `False` on an empty `agg.groups` before it
reaches the `top` comparison, so `group_by: null` is **wrong** on both, right prose
notwithstanding. No gold edit and no scorer edit follow from this ruling; the lane
already behaves as ruled.

🔴 **The residual, stated so it is not mistaken for an oversight.** A model that hands
the operator the correct answer by a route the query shape does not capture scores
`wrong` here **by design** — that is what separating `ceiling` from expressible cases
is *for*. If that capability is later worth crediting, the mechanism is a **separate
`ceiling: true` case** measuring the phrase-step rescue on its own denominator. It is
**not** relaxing `fl-21`/`fl-22`, which would retro-fit a criterion to a known result.

Why Cray, not Code: the question was whether to re-open a scoring criterion after
seeing which model it favours. Only Cray can authorise that, and the ruling was that it
is not re-opened.

### SD-8 — RULED (a) — does the landed `:127` text assertion make the re-witness 16 probes, exceeding the ruled 15? (ruled s275)

Arose in the s275 closeout-precondition pass (C3 + C8); the only open SD in this PLAN
until Cray ruled it later the same session (ruling below; options kept for lineage).
AC-4's dormant case landed as **six** assertions (`test_vendor_facts_scenario.py:120-129`),
and the AC's single "dormant-case probe" (seed `sanctions_flag: true`) can credit only
the first one it reddens — `:121` (`result_count == 0`). The deterministic-text assert
at `:127` (`"No Vendor records match that query." in ans.answer`) is a separate claim
in the coverage denominator; under CLAUDE.md §8's one-mutation-one-assertion rule it
is credited only by its own probe, under a mutation that keeps `:121` green. Such a
mutation exists — the no-data template at `nl_query.py:1103`
(`f"No {query.object_type} records match that query."`): the count stays 0, the id set
stays empty, `:127` alone reddens. Options:

- **(a) Run it as a 16th probe — RECOMMENDED (Code, s275 draft).** Reason: `:127` is
  the positive control the test's own comment (`:124-126`) says separates the real
  no-data path from a crashed run; an exemption would assert "no probe can reach it"
  when one demonstrably can — the exact reason-rot the exemption rule exists to
  stop (`_battery.py:219-221`). Cost: one engine-side mutation (restored by the
  driver) and one report line. It **exceeds the typed 15** — which is precisely why
  it is Cray's call and not this draft's.
- **(b) Exempt `:127` with a written reason** — "credited transitively: the `:121`
  probe shows the no-data path is live; the text is that path's output" — and hold
  the battery at 15. Honest but weaker: it exempts a reachable claim.
- **(c) Re-read "15" as "the PLAN's probes, however many assertions each covers"** —
  rejected by this draft: it re-interprets a typed ruling after the fact.

Why Cray, not Code: Cray typed the number; adding a probe changes the scope of a typed
ruling, and the alternative — an exemption on a reachable claim — is exactly the
coverage-report quality the ruling was protecting. As drafted pre-ruling: the battery
ran at 15 and `:127` carried a *provisional* exemption whose text named SD-8 — a
flagged gap in the report, not a silent one; recommendation (a) was contingent on
Cray's ratification, and the draft was written so either ruling is a one-line battery
change.

**RULING (Cray, typed, 2026-09-03, s275): (a) — verbatim: "(a) 16 probe เลย".** The
`:127` text assertion runs as the **16th probe**, `AC-4-dormant-no-records-TEXT`
(Step 5): subject `services/engine/nl_query.py:1103` (`_no_data_answer`'s
`return f"No {query.object_type} records match that query."`), node
`tests/verticals/fleet_maintenance/test_vendor_facts_scenario.py::test_a_dormant_property_reaches_the_honest_no_records_answer`
(`:96`), `expect_claim` = the `:127` text assertion. The mutation rewords the string
in place, so `result_count` stays 0, `grounded` stays False and the id list stays
empty — `:120/:121/:122/:123` all stay GREEN — and the replacement carries no vendor
name, so `:129` stays green too; `:127` is the only assertion that reddens. **Why it
needed its own probe rather than riding `:121`:** an empty result set and an empty id
list are also what a CRASHED run produces; the deterministic no-records TEXT is the
one thing only the real no-data path emits. **Supersession, recorded as lineage:**
this ruling widens Cray's own typed count of **15** (s274) to **16** —
`superseded by new info`, NOT `was an error`. The 15 was correct for the scope known
at s274; SD-8 surfaced a claim that scope had not accounted for, and Cray widened it.
16 was not always the number, and this PLAN does not read as though it were.
Consequences recorded: Step 5's total is **16 = 15 in-battery + AC-1(a) by hand**
(C8's 14-in-battery becomes 15); the expected exemption count is **71 = 86 − 15**
(AC-1(a) is outside the 86 — the s275 record's arithmetic note); the provisional
exemption on `:127` is retired; the Owner line, C3, C8, AC-1, AC-4, Step 5 and
Verification §3/§5 are updated in place; **no SD remains open**; no checkbox is
ticked and Status is unchanged — the 16-probe re-run's result is Code's to record.

## Verification

1. **Declared and addressable:** AC-1's exact 12-name property list (both bands) —
   its Step-1 baseline RED is un-re-witnessable post-landing (C7); the
   dormant-property removal probe is the witness; schema hook green with its own red
   probe (AC-1(a), run outside the driver — C8); Thai synonyms rendered for the five
   (AC-2) with the synonyms-only mutation; the SD-1(c) comment contract — **exactly
   5** AUTHORED stamps (C4) + exactly one PROMOTION PATH block — present with its
   two removal probes (AC-1(c1)/(c2), both in the ruled set — 15 at s274, 16 after
   SD-8).
2. **Answerable, not just advertised:** every synonym-carrying property has a valued
   seed row (AC-3, closing F8's named gap), and a supplier-evaluation question
   round-trips grounded through the real translate→execute→phrase chain offline
   (AC-4), count moving with the seed.
3. **The dormant band held to its contract (SD-3a):** the four prompt-visible,
   synonym-free (the cost-guard probe: an added `synonyms` block reddens),
   unpopulated in the seed, each carrying its `description` — with the
   `RepairCaseJustification`-authoritative sentence on `single_source_flag`
   (AC-3a's five probes); a dormant-property question terminates in the honest
   no-records answer — `grounded=False`, `result_count=0`, the deterministic text
   (C1) — reddening at `:121` when a value is authored (AC-4's dormant case,
   `expect_claim` `:121` — C3; the `:127` text claim is probed on its own as the
   16th, `AC-4-dormant-no-records-TEXT` — SD-8, ruled (a) s275).
4. **The promised non-events, witnessed:** golden oracle green with a zero exemption
   diff and a live scratch-object red probe (AC-5); fleet suite green with zero
   modified pre-existing assertions (AC-6 — its count clause is tautological
   post-landing, C7, and is not what the tick claims); zero committed codegen drift
   with the **delete-first** positive control — grep fails on the emptied dir, then
   passes after the regen (AC-7, C6).
5. **Gate:** the seven CI-faithful offline commands green (AC-8, C5 — `--no-sync`
   throughout, `CI=1 … pytest -q`); all **16** probes (15 through
   `tools/probe_battery/` + AC-1(a) by hand — C8, widened by SD-8 ruled (a) s275)
   with the coverage report — stdout only, captured `2>&1` — in the PR body, **71**
   written exemptions expected (86 − 15 in-battery; this demand is homed in Step 5,
   not in an AC; recorded as such in the s275 record).
