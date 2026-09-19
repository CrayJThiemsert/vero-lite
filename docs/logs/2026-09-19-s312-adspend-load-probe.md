# Can the engine take a case derived from a workshop conversation, unchanged?

**Date:** 2026-09-19 · **Session:** 312 · **Event type:** probe (measurement, no product)
**Author:** Claude Code (Tier 2) · **Tree:** `main` `3afdd1a6`, branch `feat/s312-adspend-vertical-probe`
**Case:** FDE program §4 เคส 1 — เกตปล่อยงบยิงแอด (the ratified first dry-run case)
**Input:** `docs/strategy/private/2026-09-19-dryrun-case1-adspend-conversation.md` §3 (gitignored, synthetic)

---

## The question, and the answer

**Question (Cray, s312):** *"ทดสอบโครงสร้างและเครื่องมือล่าสุดว่าสามารถรองรับเคส 'บทสนทนา' อื่น ๆ ได้มากน้อยแค่ไหน"*

**Answer: it took the whole case with ZERO engine changes.** `git diff --stat services/`
read **0** before the run and **0** after it. Every structural thing the case asked for was
already expressible. All friction was in **authoring form**, none in the case's shape.

Pass/fail fixed **before** anything ran. Stop rule fixed with it: **an engine refusal is the
finding — do not fix the engine.** That rule was never needed; no refusal came from the engine
lacking something.

| # | Read | Result |
|---|---|---|
| **R1** | ontology validator accepts `adspend_v0.yaml` | ✅ `OK: 1 file(s) valid` |
| **R2** | `load_procedures("adspend")` returns without raising | ✅ `ACCEPTED`, 6 steps, `terminal=fulfill` |
| **R3** | engine untouched | ✅ `services_diff=0` and `tests_diff=0`, **before and after** |
| **R4** | the per-entity band is live | ✅ `threshold_field='target_cpa_thb'` `threshold=None` `direction='above'` |
| **R5** | the authority base is a different field from the monitored measure | ✅ `derive target='amount' from field='daily_spend_thb'` |

**Control:** the ontology validator was shown to refuse before its pass was trusted — a doc with
a planted `flooat` type drew 5 errors (Lesson #0056: an uncontrolled instrument fails
*confidently*).

### It went further than the reads asked — the schema applies to a real database

`tests/support/ontology_docs.py::ontology_docs()` enumerates **by rule**
(`verticals/*/ontology/*_v0.yaml`), so it picked the new vertical up off the filesystem with no
registration and while still untracked: **count 7 → 8**. Every rule-driven test then swept it in:

| Suite | Printed measurement |
|---|---|
| `test_generated_ddl_applies.py` (PLAN-0127 AC-5, real Postgres) | **`docs=8 applied=8 failed=0`** — `outcome=ACQUIRED db_tests=1`, so it ran, it did not skip |
| `test_sql_emitter.py` (AC-11 enumeration rule, AC-12 DDL-order twin) | **`docs=8 references=61 forward=0`** — 12 passed |
| `tests/services/engine/ -k 'ontology or emitter or lockstep'` | 148 passed |

So the ad-spend ontology is not merely well-formed: **its generated DDL creates tables in a live
Postgres, with every foreign key declared after its target.** AC-11's enumeration rule absorbed a
seventh vertical without being edited — which is the rule working exactly as PLAN-0127 AC-11
specifies ("a rule, not a roster and not a floor").

⚠️ Read the pass values, not an exit code: one of these runs was piped into `head`, which reports
the truncator's status. The numbers above are the tests' **own printed lines**, and the unpiped
runs independently reported `12 passed` and `1 passed`.

---

## The three refusals — all about authoring FORM, none about the case

This is the finding that matters for live structuring.

| # | What was refused | Message | Whose fault |
|---|---|---|---|
| 1 | `type: boolean` on a property | *"'boolean' is not one of ['string','int','float','**bool**','timestamp','date','enum','json','ref','set']"* | mine — and instructive |
| 2 | a numeral inside the procedure's `goal` prose | *"AT-2 free-text goal smuggles a governance value (numeric: '1') — author it in the typed field, not prose — ADR-0025 D4"* | mine |
| 3 | a numeral inside a **step `description`** | same rule, same message shape | mine |

### Why refusal 1 is evidence FOR the Layer 2 thesis, not against it

`docs/strategy/private/2026-05-14-llm-driven-vertical-creation.md` claims:
*"JSON Schema validates LLM output — invalid emissions caught immediately, re-prompt cheap."*

That is exactly what happened. Writing `boolean` is what a fluent author — human or model —
produces from a conversation. The validator caught it **at the first gate**, named the line and
column, and **printed the legal set**, which is precisely the context a re-prompt needs. The
claim is not proven by this (one instance, and I am not an LLM), but the mechanism it depends on
was exercised and behaved as described.

### 🔴 Why refusals 2 and 3 are the real obstacle on the conversation→YAML path

ADR-0025 D4 refuses a **numeral in any free-text field** — the procedure `goal` and each step
`description` (refusal 3 widened the known scope past `goal` alone). Typed fields are exempt:
the rule gate's own `spec` was accepted carrying `<= 5`.

The rule is right. A number in prose is pinned by nothing; a number in a typed field is.

**But a goal written from a customer's own words is full of numbers.** The source conversation
says *"ห้ามหยุดวันที่ 1-5"* and *"หยุดเซ็ตที่ใช้เงินไม่เกินวันละห้าพัน"* — that is how people
speak. So conversation→YAML is not transcription; it must **move every value out of prose and
into a typed field, and then write prose that does not restate it.** That is the transformation
an LLM drafting from a transcript is most likely to get wrong, because copying the sentence is
the obvious thing to do.

**It fires loudly, which is the good case:** refusal at load, naming the field and the numeral —
never silent acceptance.

---

## What the engine accepted that the case genuinely needed

| The case needs | Accepted as |
|---|---|
| a band **per ad set**, not one shared figure (the workshop's central correction) | `threshold_field: target_cpa_thb`, `threshold=None` |
| an authority ladder routing on **a different field** from the monitored measure | `derive: {target: amount, expr: {field: daily_spend_thb}}` — while `measured_value` stays CPA |
| Thai role names in the ladder | `tiers=[('0','คนยิงแอด'), ('5000','เจ้าของ')]` |
| an unwritten rule with a machine-checkable half | `rule_gate` + a declared `compliance_criteria: [dealer_window]` |
| object + property **synonyms** in the customer's own words | accepted on both (ADR-0027 R2) |

---

## Three readings I did not pre-commit, recorded as found

**F1 — `separation_of_duties=[]` was ACCEPTED alongside a `doa_tier`.**
`verticals/building_materials/procedures.yaml:267` states *"a doa_tier gate REQUIRES it"*. The
**loader does not enforce that.** The spec was authored deliberately without SoD because the
workshop established this workflow has none (the engine proposes; there is no second human), and
it loaded. ⚠️ **Scope of this reading:** `load_procedures` accepted it. Whether a *runtime* SoD
check fires was **not tested** — no run was executed. Do not read this as "SoD is optional".

**F2 — the blank in the form is representable, and one vocabulary does not fit.**
`ratification_window_days=None` was accepted: the workshop found the owner has no ratification
rule (*"บอกในไลน์ก็จบ"*), and the engine can hold exactly that rather than forcing a fabricated
number. Good.
But `emergency_waiver.relaxes` is a **closed sourcing enum** (`three_bid` / `sole_source`). This
case has a real waiver — the media buyer paused an ad set at 02:00 and told the owner next
morning — that relaxes **nothing in that enum**. `three_bid` is authored only because the type
demands a member; it is semantically wrong for advertising. **This is the same limit
building_materials recorded** ("a future ADR-0025 D3 amendment, out of scope here") — so this is
a *second* vertical hitting it, not a new problem.

**F3 — typed fields may carry numerals; prose may not.** The rule gate's `spec` loaded as
`'not (ad_set.dealer_facing and day_of_month(now) <= 5)'`. This is what makes refusals 2/3
tractable: there is always somewhere legal for the number to go.

---

## 🔴 The most important result: governance refused what the mechanism accepted

ADR-0032 D6 warns that an **AT-2-gated** hero (a money `doa_tier`) *"is the next AT-2 signature —
it moves the `_BASELINE_SIGNATURES` census pin, turns CI RED, and obligates the new signature to
be re-argued against the current baseline"*. Measured rather than assumed. **It does.**

Two tests redden with this vertical on disk:

| Test | What it says |
|---|---|
| `test_at2_signature_retrigger.py::test_at2_generator_deferral_retrigger` | *"the AT-2 signature baseline moved … **Re-argue it (do not just update this list).**"* — adspend registers as a **fifth** signature: `('adspend', ('rule_gate','doa_tier'), (('rule_gate',('dealer_window',)), ('doa_tier',('THB',))))` |
| `tests/verticals/test_governance_config_hash_stability.py::test_the_guard_covers_every_non_fleet_vertical_that_has_procedures` | the covered-vertical set gained `adspend` |

**This is the system working, not breaking.** The two layers behaved differently on purpose:

- the **mechanical** layer — ontology → DDL → the procedure spine — absorbed a brand-new,
  conversation-derived case with **zero engine changes** (`services_diff=0`, `docs=8 applied=8
  failed=0`);
- the **governance** layer **refused to let it in quietly.** A new money-gated hero is a governed
  event that must be argued, and the census pin exists to stop exactly this from landing by
  scaffolding.

That is the moat in a measurable form: **config-cheap where it should be, gated where it must
be.** It is also the sharper answer to the question this probe was asked — the engine takes the
case; *shipping* it is a governance decision, not a build one.

### 🔴 Consequence for where these files may live

`ontology_docs()` enumerates from the **filesystem**, so it picked this vertical up **while
untracked** (count 7 → 8, measured). That creates a trap with three doors, not two:

| Option | Cost |
|---|---|
| commit `verticals/adspend/` | CI RED on the two tests above; updating `_BASELINE_SIGNATURES` is a governance act the test forbids doing casually |
| **leave it untracked under `verticals/`** | 🔴 **worst** — local suites sweep it and redden; CI never sees it. A silent local-vs-CI divergence, and the next person to run the suite gets two unexplained failures |
| move it out of `verticals/`, keep it on disk | costs nothing; the probe stays repeatable by copying it back |

The third door is the only one with no downside, so the probe's YAML was moved beside the
fixture it came from. The vertical is **not** committed and **not** left where the enumeration
rule can reach it.

---

## What this probe does NOT establish

- **It was never run.** No seeding, no DB, no `waiting_human`, no resolve. `load_procedures`
  accepting a spec is not the vertical working. FDE phase 2's own criterion has more halves than
  this one.
- **`vero-lite new-vertical` was not invoked** — the cheapest gate answered the question first
  (validate → load), so the scaffold path (synthetic adapter, handlers, registration code-mod)
  is untested here.
- **No LLM was involved.** I authored the YAML by reading the fixture. Whether a *model* can make
  the same conversation→YAML jump is the open question; this probe only shows the **target** is
  reachable and where the tripwires sit.
- **One case.** เคส 4 (คอมเพลน→ชดเชย) exercises a different LLM position (classification on a
  closed enum) and has real SoD; it is not covered by this reading.

---

## Files this probe created

`verticals/adspend/` — `ontology/adspend_v0.yaml`, `procedures.yaml`. **Untracked at the time of
writing**; whether they are committed is Cray's call. They are the only artifact that would let
the probe be repeated or extended, and the fixture they derive from is gitignored.

## Reference

- The conversation fixture (gitignored): `docs/strategy/private/2026-09-19-dryrun-case1-adspend-conversation.md`
- The case's spec row: `docs/strategy/private/2026-08-28-fde-readiness-program.md` §4, เคส 1
- Structural template: `verticals/building_materials/` (the `CustomerAccount` per-entity-band precedent FDE §4 names)
- The rule that refusals 2/3 enforce: ADR-0025 D4
- The synonyms grammar: ADR-0027 R2
